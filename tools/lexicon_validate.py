"""Read-only integration checks for the editorial workspace."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path

from tools.lexicon import LexiconError, ROOT, json_text


_UNPARSED_INTAKE_PROPERTIES = frozenset({"unparsed_source_record", "imported_master_fields"})
_EXCEPTION_INTEGRITY_CODES = frozenset({"invalid_unicode_exception", "unused_unicode_exception"})
_PROJECTION_CORE_TABLES = (
    "entries", "forms", "senses", "texts", "relations",
    "scopes", "labels", "changes", "successors",
    "unicode_exceptions", "pack_members", "decisions",
)
_PROJECTION_SMALL_TABLES = frozenset(_PROJECTION_CORE_TABLES) | frozenset({"record_targets", "snapshots", "sources"})
_PROJECTION_ALL_TABLES = _PROJECTION_SMALL_TABLES | frozenset({"assertions", "evidence", "source_records", "identities"})


def _collect_wanted_ids(tables):
    wanted_assertions = set()
    wanted_entities = set()
    wanted_records = set()

    for row in tables.get("entries", ()):
        if row.get("entry_id"):
            wanted_entities.add(row["entry_id"])
        if row.get("pos_assertion_id"):
            wanted_assertions.add(row["pos_assertion_id"])
    for row in tables.get("forms", ()):
        for col in ("form_id", "entry_id"):
            if row.get(col):
                wanted_entities.add(row[col])
        for col in ("text_assertion_id", "convention_assertion_id"):
            if row.get(col):
                wanted_assertions.add(row[col])
    for row in tables.get("senses", ()):
        for col in ("sense_id", "entry_id", "parent_sense_id"):
            if row.get(col):
                wanted_entities.add(row[col])
    for row in tables.get("texts", ()):
        for col in ("text_id", "owner_id"):
            if row.get(col):
                wanted_entities.add(row[col])
        if row.get("text_assertion_id"):
            wanted_assertions.add(row["text_assertion_id"])
    for row in tables.get("relations", ()):
        for col in ("relation_id", "source_id", "target_id"):
            if row.get(col):
                wanted_entities.add(row[col])
        if row.get("relation_code_assertion_id"):
            wanted_assertions.add(row["relation_code_assertion_id"])
    for row in tables.get("scopes", ()):
        if row.get("supporting_assertion_id"):
            wanted_assertions.add(row["supporting_assertion_id"])
        sid = row.get("subject_id")
        if sid:
            if row.get("subject_kind") == "assertion":
                wanted_assertions.add(sid)
            else:
                wanted_entities.add(sid)
    for row in tables.get("labels", ()):
        if row.get("evidence_reference"):
            wanted_assertions.add(row["evidence_reference"])
    for row in tables.get("changes", ()):
        if row.get("subject_id"):
            wanted_entities.add(row["subject_id"])
        for col in ("old_assertion_id", "new_assertion_id", "evidence_reference"):
            if row.get(col):
                wanted_assertions.add(row[col])
    for row in tables.get("successors", ()):
        for col in ("retired_id", "successor_id"):
            if row.get(col):
                wanted_entities.add(row[col])
    for row in tables.get("unicode_exceptions", ()):
        if row.get("assertion_id"):
            wanted_assertions.add(row["assertion_id"])
    for row in tables.get("decisions", ()):
        if row.get("assertion_id"):
            wanted_assertions.add(row["assertion_id"])
    for row in tables.get("pack_members", ()):
        if row.get("entry_id"):
            wanted_entities.add(row["entry_id"])
    for row in tables.get("record_targets", ()):
        if row.get("entity_id"):
            wanted_entities.add(row["entity_id"])
        if row.get("record_id"):
            wanted_records.add(row["record_id"])
    return wanted_assertions, wanted_entities, wanted_records


def _accepted_claim_ids(decisions):
    from tools.lexicon_review import _current_decisions
    from tools.lexicon_tables import ACCEPTED_OUTCOMES
    by_claim = defaultdict(list)
    for row in decisions:
        by_claim[row.get("assertion_id")].append(row)
    accepted = set()
    for aid, rows in by_claim.items():
        current = _current_decisions(rows)
        if len(current) == 1 and current[0].get("outcome") in ACCEPTED_OUTCOMES:
            accepted.add(aid)
    return accepted


def check_curated_csv(workspace=None, canonical=None):
    """Decode/schema-check editorial tables and strictly inspect canonical claims.

    Quarantined unparsed raw intake envelopes are schema/UTF-8 decoded without
    full native adjudication; projected editorial assertions must have native
    Unicode findings either queued in open findings or waived by exact
    reviewed exceptions, and projected structural/history references must hold.
    Canonical claims retain unconditional strict Unicode checks.
    """
    from tools.lexicon_tables import read_rows
    from tools.lexicon_review import batch_claim_revisions, build_text_audit_cache, claim_revision, unicode_findings
    workspace = Path(workspace or ROOT / "data/curation/tamil-lexicon")
    canonical = Path(canonical or ROOT / "lexicon/dictionary")
    failures, counts = [], {}

    def load_optional(directory: Path, name: str):
        path = directory / f"{name}.csv"
        if not path.exists():
            return []
        try:
            return list(read_rows(path))
        except (LexiconError, OSError, ValueError) as error:
            failures.append(f"{path}: {error}")
            return []

    can_exceptions = load_optional(canonical, "unicode_exceptions")
    can_decisions = load_optional(canonical, "decisions")
    can_exc_by_aid = defaultdict(list)
    for exc in can_exceptions:
        can_exc_by_aid[exc["assertion_id"]].append(exc)

    ws_exceptions = load_optional(workspace, "unicode_exceptions")
    ws_decisions = load_optional(workspace, "decisions")
    ws_accepted = _accepted_claim_ids(ws_decisions)
    ws_exc_by_aid = defaultdict(list)
    for exc in ws_exceptions:
        ws_exc_by_aid[exc["assertion_id"]].append(exc)

    ws_open_findings: set[tuple[str, str]] = set()
    ws_findings_path = workspace / "findings.csv"
    if ws_findings_path.exists():
        try:
            for row in read_rows(ws_findings_path):
                if row.get("status") == "open" and row.get("assertion_id"):
                    ws_open_findings.add((row["assertion_id"], row["issue_code"]))
        except (LexiconError, OSError, ValueError) as error:
            failures.append(f"{ws_findings_path}: {error}")

    seen_can_claims = set()
    seen_ws_claims = set()
    preloaded = {}
    preload_ok = True
    preload_large_ok = False
    wanted_assertions = set()
    wanted_entities = set()
    wanted_records = set()
    decision_ids = set()
    retained_assertions = []
    filtered_evidence = []
    filtered_source_records = []
    filtered_identities = []
    ids_initialized = False

    def _init_wanted_ids():
        nonlocal wanted_assertions, wanted_entities, wanted_records, decision_ids, ids_initialized, preload_large_ok
        if ids_initialized or not preload_ok:
            return
        ids_initialized = True
        preload_large_ok = True
        wanted_assertions, wanted_entities, wanted_records = _collect_wanted_ids(preloaded)
        decision_ids = {r["decision_id"] for r in preloaded.get("decisions", ()) if r.get("decision_id")}

    _deferred_ws_order = {"assertions": 1, "evidence": 2, "source_records": 3, "identities": 4}
    for is_workspace, directory in [(True, workspace), (False, canonical)]:
        dir_paths = sorted(directory.glob("*.csv"))
        if is_workspace:
            scan_paths = sorted(dir_paths, key=lambda p: (_deferred_ws_order.get(p.stem, 0), p.name))
        else:
            scan_paths = dir_paths
        dir_counts = {}
        is_canonical = directory == canonical
        for path in scan_paths:
            count = 0
            stem = path.stem
            if is_workspace and stem in _deferred_ws_order and not ids_initialized:
                _init_wanted_ids()
            collect_small = is_workspace and preload_ok and stem in _PROJECTION_SMALL_TABLES
            small_rows = [] if collect_small else None
            track_assertions = is_workspace and stem == "assertions" and preload_large_ok and bool(wanted_assertions)
            track_evidence = is_workspace and stem == "evidence" and preload_large_ok and bool(wanted_assertions)
            track_records = is_workspace and stem == "source_records" and preload_large_ok and bool(wanted_records)
            track_identities = is_workspace and stem == "identities" and preload_large_ok
            assertion_chunk: list[tuple[int, dict]] = []

            def _flush_assertion_chunk() -> None:
                if not assertion_chunk:
                    return
                rows_only = [r for _, r in assertion_chunk]
                saved_revs = [r.get("claim_revision_sha256") for r in rows_only]
                computed_revs = batch_claim_revisions(rows_only)
                audit_targets = []
                for r in rows_only:
                    aid = r["assertion_id"]
                    if is_canonical or r.get("property_code") not in _UNPARSED_INTAKE_PROPERTIES or aid in ws_accepted:
                        audit_targets.append(r)
                audit_cache = build_text_audit_cache(audit_targets) if audit_targets else {}
                for (row_num, r), saved_rev, rev_sha in zip(assertion_chunk, saved_revs, computed_revs):
                    if rev_sha != saved_rev:
                        failures.append(f"{path.name}:{row_num}: stale claim revision")
                    aid = r["assertion_id"]
                    if is_canonical:
                        seen_can_claims.add(aid)
                        for finding in unicode_findings(r, can_exc_by_aid.get(aid, ()), can_decisions, _audit_cache=audit_cache, _revision=rev_sha):
                            failures.append(f"{path.name}:{row_num}: value_json: {finding['issue_code']}")
                    elif r.get("property_code") not in _UNPARSED_INTAKE_PROPERTIES or aid in ws_accepted:
                        seen_ws_claims.add(aid)
                        for finding in unicode_findings(r, ws_exc_by_aid.get(aid, ()), ws_decisions, _audit_cache=audit_cache, _revision=rev_sha):
                            code = finding["issue_code"]
                            if code in _EXCEPTION_INTEGRITY_CODES or aid in ws_accepted or (aid, code) not in ws_open_findings:
                                failures.append(f"{path.name}:{row_num}: value_json: {code}")
                assertion_chunk.clear()

            try:
                for row in read_rows(path):
                    count += 1
                    if small_rows is not None:
                        small_rows.append(row)
                    if stem == "assertions":
                        aid = row["assertion_id"]
                        assertion_chunk.append((count + 1, row))
                        if len(assertion_chunk) >= 2048:
                            _flush_assertion_chunk()
                        if track_assertions and aid in wanted_assertions:
                            retained_assertions.append(row)
                            sid = row.get("subject_id")
                            if row.get("subject_kind") == "assertion":
                                if sid and sid not in wanted_assertions:
                                    preload_large_ok = False
                                    track_assertions = False
                            elif sid:
                                wanted_entities.add(sid)
                    elif track_evidence:
                        if row["assertion_id"] in wanted_assertions:
                            filtered_evidence.append(row)
                            if row.get("source_record_id"):
                                wanted_records.add(row["source_record_id"])
                    elif track_records:
                        if row["record_id"] in wanted_records:
                            filtered_source_records.append(row)
                    elif track_identities:
                        if (
                            row["entity_id"] in wanted_entities
                            or row.get("lifecycle") != "active"
                            or row.get("identity_decision_id") in decision_ids
                        ):
                            filtered_identities.append(row)
                _flush_assertion_chunk()
                if collect_small:
                    preloaded[stem] = small_rows
                elif track_assertions:
                    preloaded["assertions"] = retained_assertions
                elif track_evidence:
                    preloaded["evidence"] = filtered_evidence
                elif track_records:
                    preloaded["source_records"] = filtered_source_records
                elif track_identities:
                    preloaded["identities"] = filtered_identities
                elif is_workspace and stem == "assertions" and preload_large_ok and not wanted_assertions:
                    preloaded["assertions"] = []
                elif is_workspace and stem == "evidence" and preload_large_ok and not wanted_assertions:
                    preloaded["evidence"] = []
                elif is_workspace and stem == "source_records" and preload_large_ok and not wanted_records:
                    preloaded["source_records"] = []
            except (LexiconError, OSError, ValueError) as error:
                failures.append(f"{path}: {error}")
                if is_workspace and stem in _PROJECTION_ALL_TABLES:
                    preload_ok = False
                    preload_large_ok = False
            dir_counts[path] = count
        for path in dir_paths:
            counts[str(path.relative_to(directory.parent))] = dir_counts[path]
    for row in can_exceptions:
        if row["assertion_id"] not in seen_can_claims:
            failures.append("unicode_exceptions.csv: unused exception assertion")
    for row in ws_exceptions:
        if row["assertion_id"] not in seen_ws_claims:
            failures.append("workspace/unicode_exceptions.csv: unused exception assertion")
    if canonical.is_dir() and any(canonical.iterdir()):
        from tools.lexicon_packs import validate_canonical_dir
        failures.extend(validate_canonical_dir(canonical))
    if workspace.is_dir():
        try:
            proj_preload = preloaded if (preload_ok and (preload_large_ok or not ids_initialized)) else None
            for finding in validate_projection(workspace, _preloaded=proj_preload):
                code = finding.get("code") or finding.get("issue_code") or "projection_error"
                failures.append(f"projection: {code}: {finding.get('reason', '')}")
        except (LexiconError, OSError, ValueError) as error:
            failures.append(f"projection: {error}")
    return {"schema_version": 1, "command": "check-curated-csv", "counts": counts, "findings": sorted(set(failures))}


def validate_projection(workspace, *, _preloaded=None):
    """Validate the selected proposed structure without loading the raw corpus."""
    from tools.lexicon_tables import read_rows, validate_relations
    from tools.lexicon_review import validate_history
    workspace = Path(workspace)
    preload = _preloaded or {}
    tables = {
        name: list(preload[name]) if name in preload else (list(read_rows(workspace / (name + ".csv"))) if (workspace / (name + ".csv")).exists() else [])
        for name in _PROJECTION_CORE_TABLES
    }
    if (workspace / "record_targets.csv").exists():
        tables["record_targets"] = list(preload["record_targets"]) if "record_targets" in preload else list(read_rows(workspace / "record_targets.csv"))
    if (workspace / "snapshots.csv").exists():
        tables["snapshots"] = list(preload["snapshots"]) if "snapshots" in preload else list(read_rows(workspace / "snapshots.csv"))
    tables["sources"] = list(preload["sources"]) if "sources" in preload else (list(read_rows(workspace / "sources.csv")) if (workspace / "sources.csv").exists() else [])

    wanted_assertions, wanted_entities, wanted_records = _collect_wanted_ids(tables)

    assertions_path = workspace / "assertions.csv"
    retained_assertions = []
    if assertions_path.exists() and wanted_assertions:
        if "assertions" in preload:
            retained_assertions = list(preload["assertions"])
        else:
            seen_assertions = set()
            pending_assertions = set(wanted_assertions)
            while pending_assertions:
                newly_wanted = set()
                batch = []
                for row in read_rows(assertions_path):
                    aid = row["assertion_id"]
                    if aid in pending_assertions:
                        batch.append(row)
                        seen_assertions.add(aid)
                        sid = row.get("subject_id")
                        if row.get("subject_kind") == "assertion" and sid and sid not in wanted_assertions:
                            newly_wanted.add(sid)
                retained_assertions.extend(batch)
                wanted_assertions.update(newly_wanted)
                pending_assertions = newly_wanted
    tables["assertions"] = retained_assertions

    for row in retained_assertions:
        if row.get("subject_kind") != "assertion" and row.get("subject_id"):
            wanted_entities.add(row["subject_id"])

    evidence_path = workspace / "evidence.csv"
    if evidence_path.exists() and wanted_assertions:
        if "evidence" in preload:
            tables["evidence"] = list(preload["evidence"])
        else:
            tables["evidence"] = [r for r in read_rows(evidence_path) if r["assertion_id"] in wanted_assertions]
    else:
        tables["evidence"] = []
    for row in tables["evidence"]:
        if row.get("source_record_id"):
            wanted_records.add(row["source_record_id"])

    source_records_path = workspace / "source_records.csv"
    if wanted_records and source_records_path.exists():
        if "source_records" in preload:
            tables["source_records"] = list(preload["source_records"])
        else:
            tables["source_records"] = [
                r for r in read_rows(source_records_path) if r["record_id"] in wanted_records
            ]

    decision_ids = {r["decision_id"] for r in tables["decisions"] if r.get("decision_id")}
    identities_path = workspace / "identities.csv"
    if not identities_path.exists():
        tables["identities"] = []
    elif "identities" in preload:
        tables["identities"] = list(preload["identities"])
    else:
        tables["identities"] = [
            r for r in read_rows(identities_path)
            if r["entity_id"] in wanted_entities
            or r.get("lifecycle") != "active"
            or r.get("identity_decision_id") in decision_ids
        ]
    findings = validate_relations(tables)
    findings.extend(validate_history(tables["identities"], tables["changes"], tables["successors"], tables["assertions"], tables["decisions"]))
    return sorted(findings, key=json_text)
