"""Explicit append-only ingestion of supplied source, evidence, review, and pack records."""

from pathlib import Path

from tools.lexicon import LexiconError, safe_output

ALLOWED_INGEST_TABLES = frozenset({
    "sources",
    "evidence",
    "decisions",
    "pack_members",
    "scopes",
    "labels",
    "unicode_exceptions",
    "changes",
    "successors",
})
PACK_IDS = frozenset({"core", "terminology", "names_taxa", "regional"})


def _record_key(table, row, primary_col):
    if table == "evidence":
        return (
            row["assertion_id"],
            row["source_id"],
            row["source_record_id"] or "",
            row["locator_json"],
            row["evidence_role"],
        )
    if table == "successors":
        return (row["retired_id"], row["successor_id"], row["role"])
    if table == "unicode_exceptions":
        return tuple(str(row.get(f)) for f in primary_col if f != "reason_json")
    if table == "pack_members":
        return (row["pack_id"], row["entry_id"])
    if table == "labels":
        return (row["registry_id"], row["registry_version"], row["code"])
    if table == "scopes":
        return (
            row["subject_kind"],
            row["subject_id"],
            row["dimension"],
            row["state"],
            row["label_code"] or "",
        )
    return row[primary_col[0]]


def _read_optional(workspace, name):
    from tools.lexicon_tables import read_rows
    path = workspace / f"{name}.csv"
    return list(read_rows(path)) if path.exists() else []


def _validate_labels(workspace, merged_rows, additions):
    from tools.lexicon_tables import read_rows
    assertions = {r["assertion_id"] for r in read_rows(workspace / "assertions.csv")}
    by_registry = {(r["registry_id"], r["registry_version"], r["code"]): r for r in merged_rows}
    for row in additions:
        ref = row.get("evidence_reference")
        if ref and ref not in assertions:
            raise LexiconError("unknown label evidence assertion reference")
        seen = {(row["registry_id"], row["registry_version"], row["code"])}
        parent = row.get("parent_code")
        cur_cat = row["category"]
        while parent:
            pkey = (row["registry_id"], row["registry_version"], parent)
            if pkey in seen:
                raise LexiconError("cycle in label parent hierarchy")
            prow = by_registry.get(pkey)
            if prow is None:
                raise LexiconError("unknown label parent_code")
            if prow["category"] != cur_cat:
                raise LexiconError("label parent category mismatch")
            seen.add(pkey)
            parent = prow.get("parent_code")


def _validate_scopes(workspace, merged_rows, additions):
    from tools.lexicon_tables import ENTITY_TABLE_FOR_KIND, PRIMARY_ID_COLS, read_rows
    from tools.lexicon_review import claim_revision
    claims = {r["assertion_id"]: r for r in read_rows(workspace / "assertions.csv")}
    decisions = {r["decision_id"]: r for r in read_rows(workspace / "decisions.csv")}
    labels = _read_optional(workspace, "labels")
    labels_by_code = {}
    for lbl in labels:
        labels_by_code.setdefault((lbl["category"], lbl["code"]), []).append(lbl)
    subject_cache = {"assertion": set(claims)}
    by_dim = {}
    for row in merged_rows:
        dim_key = (row["subject_kind"], row["subject_id"], row["dimension"])
        prev_states = by_dim.setdefault(dim_key, set())
        if prev_states and (row["state"] != "attested" or any(s != "attested" for s in prev_states)):
            raise LexiconError("conflicting scope state for subject and dimension")
        prev_states.add(row["state"])
    for row in additions:
        kind, sid = row["subject_kind"], row["subject_id"]
        if kind not in subject_cache:
            tbl = ENTITY_TABLE_FOR_KIND[kind]
            subject_cache[kind] = {r[PRIMARY_ID_COLS[tbl]] for r in _read_optional(workspace, tbl)}
        if sid not in subject_cache[kind]:
            raise LexiconError("unknown scope subject reference")
        aid = row["supporting_assertion_id"]
        claim = claims.get(aid)
        if claim is None:
            raise LexiconError("unknown scope supporting_assertion reference")
        dec = decisions.get(row["decision_id"])
        if dec is None or dec["assertion_id"] != aid or dec["assertion_revision_sha256"] != claim_revision(claim):
            raise LexiconError("invalid or stale scope decision reference")
        if row["state"] == "attested":
            code = row.get("label_code")
            if not code or (row["dimension"], code) not in labels_by_code:
                raise LexiconError("unknown attested scope label_code")


def _validate_pack_members(workspace, merged_rows, additions):
    from tools.lexicon_tables import read_rows
    entries = {r["entry_id"]: r for r in _read_optional(workspace, "entries")}
    identities = {r["entity_id"]: r for r in _read_optional(workspace, "identities")}
    rev_by_entry = {}
    for row in merged_rows:
        pid = row["pack_id"]
        if pid not in PACK_IDS:
            raise LexiconError("unsupported pack_id")
        eid = row["entry_id"]
        entry = entries.get(eid)
        if entry is None:
            raise LexiconError("unknown pack_members entry reference")
        ident = identities.get(eid)
        if ident is not None and (ident.get("kind") != "entry" or ident.get("lifecycle") != "active"):
            raise LexiconError("pack_members entry is inactive or not an entry")
        if row["included_revision"] != entry["revision"]:
            raise LexiconError("pack_members included_revision does not match entry revision")
        prev_rev = rev_by_entry.setdefault(eid, row["included_revision"])
        if prev_rev != row["included_revision"]:
            raise LexiconError("cross-pack entry revision conflict")
    if not additions:
        return


def _validate_unicode_exceptions(workspace, claims, additions):
    from tools.lexicon_review import claim_revision, unicode_findings
    decisions = _read_optional(workspace, "decisions")
    for row in additions:
        claim = claims[row["assertion_id"]]
        if row["claim_revision_sha256"] != claim_revision(claim):
            raise LexiconError("stale unicode exception claim revision")
        issues = unicode_findings(claim, [row], decisions)
        if any(f["issue_code"] in {"invalid_unicode_exception", "unused_unicode_exception"} for f in issues):
            raise LexiconError("unicode exception does not match claim anomaly or valid human decision")


def _validate_history_tables(workspace, table, existing, additions):
    from tools.lexicon_tables import read_rows
    from tools.lexicon_review import validate_history
    identities = _read_optional(workspace, "identities")
    assertions = list(read_rows(workspace / "assertions.csv"))
    decisions = list(read_rows(workspace / "decisions.csv"))
    if table == "changes":
        changes = list(existing.values()) + [r for r in additions if r["change_id"] not in existing]
        successors = _read_optional(workspace, "successors")
    else:
        changes = _read_optional(workspace, "changes")
        seen_pairs = {(r["retired_id"], r["successor_id"]): r["role"] for r in existing.values()}
        for row in additions:
            pair = (row["retired_id"], row["successor_id"])
            if pair in seen_pairs and seen_pairs[pair] != row["role"]:
                raise LexiconError("conflicting successor role for identity pair")
            seen_pairs[pair] = row["role"]
        merged_succ = dict(existing)
        for row in additions:
            merged_succ[(row["retired_id"], row["successor_id"], row["role"])] = row
        successors = list(merged_succ.values())
    findings = validate_history(identities, changes, successors, assertions, decisions)
    if table == "changes":
        relevant = [f for f in findings if f["issue_code"] not in {"merge_cardinality", "split_cardinality"}]
    else:
        batch_retired = {r["retired_id"] for r in additions}
        relevant = [
            f for f in findings
            if f["issue_code"] not in {"merge_cardinality", "split_cardinality"}
            or f["entity_id"] in batch_retired
        ]
    if relevant:
        raise LexiconError("history validation failed: " + "; ".join(f["issue_code"] for f in relevant))


def ingest(workspace, table, incoming):
    from tools.lexicon_tables import ACCEPTED_OUTCOMES, fields, read_rows, write_rows
    from tools.lexicon_review import _current_decisions, claim_revision, eligibility, evidence_hash, unicode_findings

    workspace = safe_output(workspace)
    incoming = Path(incoming).resolve()
    if table not in ALLOWED_INGEST_TABLES:
        raise LexiconError("unsupported ingestion table")
    if incoming.is_relative_to(workspace):
        raise LexiconError("ingestion input must be outside its workspace")
    additions = list(read_rows(incoming, table))
    cols = fields(table)
    destination = workspace / (table + ".csv")
    existing = {_record_key(table, r, cols): r for r in read_rows(destination)} if destination.exists() else {}

    seen_batch = {}
    for row in additions:
        ident = _record_key(table, row, cols)
        if ident in existing and existing[ident] != row:
            raise LexiconError("conflicting existing editorial record")
        if ident in seen_batch and seen_batch[ident] != row:
            raise LexiconError("conflicting records in ingestion batch")
        seen_batch[ident] = row

    claims = {}
    if table in {"evidence", "decisions", "unicode_exceptions"}:
        wanted = {r["assertion_id"] for r in additions}
        claims = {r["assertion_id"]: r for r in read_rows(workspace / "assertions.csv") if r["assertion_id"] in wanted}
        if wanted - claims.keys():
            raise LexiconError("unknown assertion reference")

    if table == "decisions":
        evidence = list(read_rows(workspace / "evidence.csv"))
        sources = list(read_rows(workspace / "sources.csv"))
        merged_decisions = dict(existing)
        for row in additions:
            merged_decisions[_record_key(table, row, cols)] = row
        by_assertion = {}
        for d in merged_decisions.values():
            by_assertion.setdefault(d["assertion_id"], []).append(d)
        for aid, dec_list in by_assertion.items():
            if dec_list and not _current_decisions(dec_list):
                raise LexiconError(f"invalid or cyclic decision history for {aid}")
        for row in additions:
            claim = claims[row["assertion_id"]]
            related = [r for r in evidence if r["assertion_id"] == claim["assertion_id"]]
            if row["assertion_revision_sha256"] != claim_revision(claim) or row["evidence_bundle_sha256"] != evidence_hash(related):
                raise LexiconError("stale claim or evidence revision")
            if row["outcome"] in ACCEPTED_OUTCOMES:
                per_claim = [r for r in existing.values() if r["assertion_id"] == claim["assertion_id"] and r["decision_id"] != row["decision_id"]] + [row]
                result = eligibility(claim, related, sources, per_claim, unicode_findings(claim))
                if not result["eligible"]:
                    raise LexiconError("supplied acceptance fails eligibility: " + ",".join(result["reasons"]))
    elif table == "evidence":
        sources = {r["source_id"] for r in read_rows(workspace / "sources.csv")}
        if any(r["source_id"] not in sources for r in additions):
            raise LexiconError("unknown source reference")
        wanted_records = {r["source_record_id"] for r in additions if r.get("source_record_id")}
        if wanted_records:
            sr_path = workspace / "source_records.csv"
            known_records = (
                {r["record_id"] for r in read_rows(sr_path) if r["record_id"] in wanted_records}
                if sr_path.exists()
                else set()
            )
            if wanted_records - known_records:
                raise LexiconError("unknown source_record reference")
    elif table == "labels":
        merged = dict(existing)
        for row in additions:
            merged[_record_key(table, row, cols)] = row
        _validate_labels(workspace, list(merged.values()), additions)
    elif table == "scopes":
        merged = dict(existing)
        for row in additions:
            merged[_record_key(table, row, cols)] = row
        _validate_scopes(workspace, list(merged.values()), additions)
    elif table == "pack_members":
        merged = dict(existing)
        for row in additions:
            merged[_record_key(table, row, cols)] = row
        _validate_pack_members(workspace, list(merged.values()), additions)
    elif table == "unicode_exceptions":
        _validate_unicode_exceptions(workspace, claims, additions)
    elif table in {"changes", "successors"}:
        _validate_history_tables(workspace, table, existing, additions)

    inserted = 0
    for row in additions:
        identity = _record_key(table, row, cols)
        if identity not in existing:
            inserted += 1
        existing[identity] = row
    write_rows(destination, table, existing.values())
    return {"schema_version": 1, "command": "review-ingest", "table": table, "inserted": inserted, "l3_pack_eligible": False, "runtime_verified": None}
