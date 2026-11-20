"""Offline CLDF 1.3 Dictionary schema validation, export, and lossless roundtrip."""

from __future__ import annotations

import argparse
from collections import OrderedDict, defaultdict
import csv
import hashlib
import importlib
import inspect
import json
import logging
import os
import pathlib
import shutil
import sys
import tempfile
import tomllib
import types
from typing import Any, Callable

import csvw
import jsonschema
import pycldf

from tools import lexicon, lexicon_review, lexicon_tables

CLDF_VERSION = "1.3"
CLDF_SCHEMA_DIR = lexicon.ROOT / "schemas" / "lexicon" / "cldf"
CLDF_MANIFEST_PATH = CLDF_SCHEMA_DIR / "cldf-1.3.sha256.json"
CLDF_REPORT_SCHEMA_PATH = CLDF_SCHEMA_DIR / "cldf-export-report.schema.json"
CLDF_TERMS_RDF = CLDF_SCHEMA_DIR / "v1.3" / "terms.rdf"

SUPPORTED_PACKS = ("core", "terminology", "names_taxa", "regional")
ID_REGEX = "^[A-Za-z][A-Za-z0-9_.:-]*$"

CANONICAL_TABLES = (
    "entries",
    "forms",
    "senses",
    "texts",
    "relations",
    "sources",
    "assertions",
    "evidence",
    "decisions",
    "changes",
    "successors",
    "identities",
    "findings",
    "unicode_exceptions",
    "labels",
    "scopes",
    "pack_members",
)

CUSTOM_EXTENSION_TABLES = tuple(t for t in CANONICAL_TABLES if t not in {"entries", "senses"})

CLOSED_CSV_FILES = (
    "languages.csv",
    "entries.csv",
    "senses.csv",
    "examples.csv",
    "forms.csv",
    "texts.csv",
    "relations.csv",
    "sources.csv",
    "assertions.csv",
    "evidence.csv",
    "decisions.csv",
    "changes.csv",
    "successors.csv",
    "identities.csv",
    "findings.csv",
    "unicode_exceptions.csv",
    "labels.csv",
    "scopes.csv",
    "pack_members.csv",
    "notices.csv",
)


def _column_specs(table: str) -> dict[str, lexicon_tables.ColumnSpec]:
    return lexicon_tables._table_registry()[table].columns  # noqa: SLF001 - single schema registry owner


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _finding(
    code: str,
    entity_id: str,
    reason: str,
    *,
    field: str = "",
    severity: str = "error",
    scalar_positions: list[int] | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "entity_id": entity_id,
        "field": field,
        "reason": reason,
    }
    if scalar_positions is not None:
        item["scalar_positions"] = list(scalar_positions)
    return item


def verify_cldf_schemas(schema_dir: pathlib.Path | None = None) -> dict[str, Any]:
    """Verify local pinned CLDF 1.3 schemas, validator versions, and digests."""
    base = CLDF_SCHEMA_DIR if schema_dir is None else pathlib.Path(schema_dir)
    manifest_path = base / "cldf-1.3.sha256.json"
    if not manifest_path.is_file():
        raise lexicon.LexiconError(f"Missing pinned CLDF digest manifest: {manifest_path}", code=2)

    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise lexicon.LexiconError(f"Unreadable CLDF digest manifest: {exc}", code=2) from exc

    if manifest.get("cldf_version") != CLDF_VERSION:
        raise lexicon.LexiconError(f"Unsupported pinned CLDF version: {manifest.get('cldf_version')!r}", code=2)

    pins = manifest.get("validator_pins", {})
    if pins.get("pycldf") != pycldf.__version__ or pins.get("csvw") != csvw.__version__:
        raise lexicon.LexiconError(
            "Installed CLDF validator versions do not match pins: "
            f"expected pycldf={pins.get('pycldf')} csvw={pins.get('csvw')}, "
            f"got pycldf={pycldf.__version__} csvw={csvw.__version__}",
            code=2,
        )

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise lexicon.LexiconError("Pinned CLDF digest manifest has no file entries", code=2)

    for rel, meta in sorted(files.items()):
        target = base / rel
        if not target.is_file():
            raise lexicon.LexiconError(f"Missing pinned CLDF schema file: {target}", code=2)
        raw = target.read_bytes()
        if len(raw) != meta.get("bytes") or _sha256_bytes(raw) != meta.get("sha256"):
            raise lexicon.LexiconError(f"Pinned CLDF schema integrity check failed for {rel}", code=2)

    terms_path = base / "v1.3" / "terms.rdf"
    if not terms_path.is_file():
        raise lexicon.LexiconError(f"Missing pinned CLDF ontology terms.rdf: {terms_path}", code=2)

    return {
        "cldf_version": CLDF_VERSION,
        "schema_manifest_sha256": _sha256_bytes(manifest_bytes),
        "validator_pins": {"pycldf": pycldf.__version__, "csvw": csvw.__version__},
        "file_count": len(files),
    }


def _check_non_overlapping(
    canonical: pathlib.Path,
    output: pathlib.Path,
    report_output: pathlib.Path | None,
) -> None:
    lexicon.safe_output(output, source_root=lexicon.SOURCE)
    canon_res = canonical.resolve()
    out_res = output.resolve()
    if out_res == canon_res or canon_res in out_res.parents or out_res in canon_res.parents:
        raise lexicon.LexiconError(f"Output path {out_res} overlaps canonical input {canon_res}", code=2)

    if report_output is not None:
        lexicon.safe_output(report_output, source_root=lexicon.SOURCE)
        rep_res = report_output.resolve()
        if rep_res == canon_res or canon_res in rep_res.parents:
            raise lexicon.LexiconError(f"Report path {rep_res} overlaps canonical input {canon_res}", code=2)
        if rep_res == out_res or out_res in rep_res.parents:
            raise lexicon.LexiconError(f"Report path {rep_res} overlaps CLDF output {out_res}", code=2)


def _table_sort_key(table: str, row: dict[str, Any]) -> tuple:
    if table in lexicon_tables.PRIMARY_ID_COLS:
        col = lexicon_tables.PRIMARY_ID_COLS[table]
        return (str(row.get(col) or ""),)
    return (lexicon.json_text(row),)


def _run_upstream_pack_validator(
    canonical_dir: pathlib.Path,
    pack: str,
    packs_meta: dict[str, Any],
    canonical_validator: Callable[[pathlib.Path, str], dict[str, Any]] | None,
    *,
    preloaded_tables: dict[str, list[dict[str, Any]]] | None = None,
    prevalidated_schema: bool = False,
) -> list[dict[str, Any]]:
    if canonical_validator is not None:
        res = canonical_validator(canonical_dir, pack)
        if not isinstance(res, dict):
            raise lexicon.LexiconError("canonical_validator must return a dict report", code=2)
        findings = list(res.get("findings") or [])
        if res.get("l3_pack_eligible") is False and not findings:
            findings.append(
                _finding(
                    "UPSTREAM_PACK_INELIGIBLE",
                    pack,
                    "Canonical pack validator marked pack ineligible",
                    field="pack",
                )
            )
        return findings

    if (canonical_dir / "schema.toml").is_file() and (canonical_dir / "ATTRIBUTION_AND_TERMS.md").is_file():
        findings: list[dict[str, Any]] = []
        declared_pack = packs_meta.get("pack_id") if isinstance(packs_meta, dict) else None
        if declared_pack and declared_pack != pack:
            findings.append(
                _finding(
                    "NONEMPTY_ELIGIBLE_PACK_REQUIRED",
                    pack,
                    f"Canonical directory promotes pack {declared_pack!r}, not requested {pack!r}",
                    field="pack_id",
                )
            )
        try:
            mod = importlib.import_module("tools.lexicon_packs")
            validate_dir = getattr(mod, "validate_canonical_dir", None)
        except ModuleNotFoundError:
            validate_dir = None
        if callable(validate_dir):
            kwargs: dict[str, Any] = {}
            if preloaded_tables is not None:
                try:
                    sig = inspect.signature(validate_dir)
                    if "preloaded_tables" in sig.parameters:
                        kwargs["preloaded_tables"] = preloaded_tables
                    if "prevalidated_schema" in sig.parameters:
                        kwargs["prevalidated_schema"] = prevalidated_schema
                except (TypeError, ValueError):
                    kwargs = {}
            for err in validate_dir(canonical_dir, **kwargs):
                findings.append(_finding("CANONICAL_PACK_INVALID", pack, str(err), field="canonical"))
        return findings

    return []


def _load_notices(canonical_dir: pathlib.Path, pack_cfg: dict[str, Any], sources: list[dict[str, Any]]) -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    notices: dict[str, bytes] = {}
    findings: list[dict[str, Any]] = []
    declared_hashes = pack_cfg.get("notice_sha256", {}) if isinstance(pack_cfg, dict) else {}
    rel_candidates: set[str] = set()

    if isinstance(pack_cfg, dict):
        for rel in pack_cfg.get("attribution_notices", []) or []:
            rel_candidates.add(str(rel))

    for src in sources:
        ref = src.get("attribution_reference_json")
        if isinstance(ref, str) and (ref.startswith("notices/") or "/" not in ref):
            cand = ref if ref.startswith("notices/") else f"notices/{ref}"
            rel_candidates.add(cand)

    notices_dir = canonical_dir / "notices"
    if notices_dir.is_dir():
        for p in sorted(notices_dir.rglob("*")):
            if p.is_file():
                rel_candidates.add(p.relative_to(canonical_dir).as_posix())
    if (canonical_dir / "ATTRIBUTION_AND_TERMS.md").is_file():
        rel_candidates.add("ATTRIBUTION_AND_TERMS.md")

    for rel in sorted(rel_candidates):
        path = canonical_dir / rel
        if not path.resolve().is_relative_to(canonical_dir.resolve()):
            findings.append(
                _finding("INVALID_NOTICE_PATH", rel, "Notice path escapes canonical directory", field="notices")
            )
            continue
        if not path.is_file():
            findings.append(
                _finding("MISSING_NOTICE_FILE", rel, f"Declared attribution notice missing: {rel}", field="notices")
            )
            continue
        raw = path.read_bytes()
        expected_sha = declared_hashes.get(rel) if isinstance(declared_hashes, dict) else None
        if expected_sha and _sha256_bytes(raw) != expected_sha:
            findings.append(
                _finding("NOTICE_DIGEST_MISMATCH", rel, f"Notice SHA-256 mismatch for {rel}", field="notices")
            )
            continue
        notices[rel] = raw

    return notices, findings


def _pack_closure_tables(raw_tables: dict[str, list[dict[str, Any]]], pack: str) -> dict[str, list[dict[str, Any]]]:
    pack_members = [r for r in raw_tables["pack_members"] if r["pack_id"] == pack]
    if not pack_members:
        return {t: [] for t in CANONICAL_TABLES}

    entry_ids = {r["entry_id"] for r in pack_members}
    entries = [r for r in raw_tables["entries"] if r["entry_id"] in entry_ids]
    forms = [r for r in raw_tables["forms"] if r["entry_id"] in entry_ids]
    senses = [r for r in raw_tables["senses"] if r["entry_id"] in entry_ids]
    sense_ids = {r["sense_id"] for r in senses}
    texts = [r for r in raw_tables["texts"] if r["owner_kind"] == "sense" and r["owner_id"] in sense_ids]
    text_ids = {r["text_id"] for r in texts}
    relations = [r for r in raw_tables["relations"] if r["source_id"] in (entry_ids | sense_ids)]
    relation_ids = {r["relation_id"] for r in relations}
    scopes = [
        r
        for r in raw_tables["scopes"]
        if (r["subject_kind"] == "entry" and r["subject_id"] in entry_ids)
        or (r["subject_kind"] == "sense" and r["subject_id"] in sense_ids)
    ]

    assertion_ids: set[str] = set()
    for e in entries:
        if e.get("pos_assertion_id"):
            assertion_ids.add(e["pos_assertion_id"])
    for f in forms:
        assertion_ids.add(f["text_assertion_id"])
        if f.get("convention_assertion_id"):
            assertion_ids.add(f["convention_assertion_id"])
    for t in texts:
        assertion_ids.add(t["text_assertion_id"])
    for r in relations:
        assertion_ids.add(r["relation_code_assertion_id"])
    for s in scopes:
        if s.get("supporting_assertion_id"):
            assertion_ids.add(s["supporting_assertion_id"])

    assertions = [r for r in raw_tables["assertions"] if r["assertion_id"] in assertion_ids]
    evidence = [r for r in raw_tables["evidence"] if r["assertion_id"] in assertion_ids]
    source_ids = {r["source_id"] for r in evidence}
    sources = [r for r in raw_tables["sources"] if r["source_id"] in source_ids]
    decisions = [r for r in raw_tables["decisions"] if r["assertion_id"] in assertion_ids]
    decision_ids = {r["decision_id"] for r in decisions}
    unicode_exceptions = [r for r in raw_tables["unicode_exceptions"] if r["assertion_id"] in assertion_ids]
    changes = [
        r
        for r in raw_tables["changes"]
        if r["old_assertion_id"] in assertion_ids or r["new_assertion_id"] in assertion_ids
    ]
    all_entity_ids = entry_ids | sense_ids | {f["form_id"] for f in forms} | text_ids | relation_ids
    identities = [r for r in raw_tables["identities"] if r["entity_id"] in all_entity_ids]
    retired_ids = {r["entity_id"] for r in identities}
    successors = [
        r
        for r in raw_tables["successors"]
        if r["retired_id"] in retired_ids or r["successor_id"] in entry_ids or r["identity_decision_id"] in decision_ids
    ]
    findings_rows = [
        r
        for r in raw_tables["findings"]
        if r.get("assertion_id") in assertion_ids
    ]
    label_codes = {r["label_code"] for r in scopes if r.get("label_code")}
    parent_codes = {r["parent_code"] for r in raw_tables["labels"] if r["code"] in label_codes and r.get("parent_code")}
    wanted_codes = label_codes | parent_codes
    labels = [r for r in raw_tables["labels"] if r["code"] in wanted_codes or r["category"] == "grammar_system"]

    out = {
        "entries": entries,
        "forms": forms,
        "senses": senses,
        "texts": texts,
        "relations": relations,
        "sources": sources,
        "assertions": assertions,
        "evidence": evidence,
        "decisions": decisions,
        "changes": changes,
        "successors": successors,
        "identities": identities,
        "findings": findings_rows,
        "unicode_exceptions": unicode_exceptions,
        "labels": labels,
        "scopes": scopes,
        "pack_members": pack_members,
    }
    return {k: sorted(v, key=lambda r: _table_sort_key(k, r)) for k, v in out.items()}


def _validate_unknown_claim_review(
    assertion: dict[str, Any],
    ev_rows: list[dict[str, Any]],
    sources_by_id: dict[str, dict[str, Any]],
    decisions_for_a: list[dict[str, Any]],
    findings_rows: list[dict[str, Any]],
    *,
    _revision: str | None = None,
) -> list[str]:
    reasons: list[str] = []
    expected_rev = lexicon_review.claim_revision(assertion) if _revision is None else _revision
    if assertion.get("claim_revision_sha256") != expected_rev:
        reasons.append("claim_revision_mismatch")
    if assertion.get("value_json") is not None:
        reasons.append("unknown_claim_must_have_null_value")
    if not ev_rows:
        reasons.append("missing_verified_support")
    for ev in ev_rows:
        if ev.get("source_id") not in sources_by_id:
            reasons.append("unverified_source_or_reuse_attribution")
    relevant_terminal = [
        d for d in decisions_for_a
        if not any(other.get("predecessor_decision_id") == d.get("decision_id") for other in decisions_for_a)
    ]
    if len(relevant_terminal) != 1:
        reasons.append("missing_or_conflicting_decision")
    else:
        dec = relevant_terminal[0]
        if dec.get("outcome") not in lexicon_tables.ACCEPTED_OUTCOMES:
            reasons.append("decision_not_accepted")
        if (
            dec.get("assertion_revision_sha256") != assertion.get("claim_revision_sha256")
            or dec.get("evidence_bundle_sha256") != lexicon_review.evidence_hash(ev_rows)
        ):
            reasons.append("stale_decision")
    for f in findings_rows:
        if f.get("assertion_id") == assertion.get("assertion_id") and f.get("severity") == "error" and f.get("status") != "resolved":
            reasons.append("blocking_findings")
    return sorted(set(reasons))


def _evaluate_pack_eligibility(
    tables: dict[str, list[dict[str, Any]]],
    pack: str,
    *,
    prevalidated_schema: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    findings: list[dict[str, Any]] = []
    if not tables["pack_members"] or not tables["entries"]:
        findings.append(
            _finding(
                "NONEMPTY_ELIGIBLE_PACK_REQUIRED",
                pack,
                f"Pack {pack!r} has zero eligible entries/assertions; refusing release/export",
                field="pack_members",
            )
        )
        return findings, 0

    invalid_assertions: set[str] = set()
    invalid_evidence: set[str] = set()
    if not prevalidated_schema:
        for table in CANONICAL_TABLES:
            for row, err_msg in lexicon_tables.validate_rows_batch(table, tables[table], collect_errors=True):
                findings.append(_finding("SCHEMA_ROW_INVALID", str(row), err_msg, field=table))
                if table == "assertions" and isinstance(row, dict) and row.get("assertion_id"):
                    invalid_assertions.add(row["assertion_id"])
                elif table == "evidence" and isinstance(row, dict) and row.get("assertion_id"):
                    invalid_evidence.add(row["assertion_id"])

    for rel_err in lexicon_tables.validate_relations(tables):
        findings.append(
            _finding(
                rel_err.get("code", "RELATION_INVALID"),
                rel_err.get("entity_id", pack),
                rel_err.get("reason", "Invalid canonical relation/reference"),
                field=rel_err.get("field", "relations"),
            )
        )

    for hist_err in lexicon_review.validate_history(
        tables["identities"],
        tables["changes"],
        tables["successors"],
        tables["assertions"],
        tables["decisions"],
    ):
        findings.append(
            _finding(
                hist_err.get("code", "HISTORY_INVALID"),
                hist_err.get("entity_id", pack),
                hist_err.get("reason", "Invalid history state"),
                field=hist_err.get("field", "decisions"),
            )
        )

    entry_ids = {e["entry_id"] for e in tables["entries"]}
    sense_to_entry = {s["sense_id"]: s["entry_id"] for s in tables["senses"]}
    sense_ids = set(sense_to_entry)
    pack_policy = {m["entry_id"]: m["relation_inclusion_policy"] for m in tables["pack_members"]}
    sense_by_entry: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in tables["senses"]:
        sense_by_entry[s["entry_id"]].append(s)
    texts_by_owner: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in tables["texts"]:
        if t["owner_kind"] != "sense":
            findings.append(
                _finding("INVALID_TEXT_OWNER", t["text_id"], f"Text must be sense-owned, got {t['owner_kind']!r}", field="texts")
            )
        if t["component"] == "unparsed":
            findings.append(
                _finding("UNPARSED_COMPONENT_FORBIDDEN", t["text_id"], "Unparsed text cannot enter CLDF export", field="texts")
            )
        texts_by_owner[t["owner_id"]].append(t)

    for e in tables["entries"]:
        if not sense_by_entry.get(e["entry_id"]):
            findings.append(
                _finding("ENTRY_MISSING_SENSE", e["entry_id"], "Entry has no active sense in pack", field="senses")
            )
        for s in sense_by_entry.get(e["entry_id"], []):
            if not any(t["component"] in {"gloss", "definition"} for t in texts_by_owner.get(s["sense_id"], [])):
                findings.append(
                    _finding("SENSE_MISSING_GLOSS_OR_DEFINITION", s["sense_id"], "Sense requires gloss or definition text", field="texts")
                )

    for r in tables["relations"]:
        src_kind = r.get("source_kind")
        tgt_kind = r.get("target_kind")
        src_id = r["source_id"]
        tgt_id = r["target_id"]
        if src_kind != "sense":
            findings.append(
                _finding(
                    "UNSUPPORTED_RELATION_SOURCE_KIND",
                    r["relation_id"],
                    f"Relation {r['relation_id']!r} has unsupported source_kind {src_kind!r}; canonical CLDF packs require sense-sourced relations",
                    field="relations",
                )
            )
        src_in = (src_kind == "sense" and src_id in sense_ids) or (src_kind == "entry" and src_id in entry_ids)
        tgt_in = (tgt_kind == "sense" and tgt_id in sense_ids) or (tgt_kind == "entry" and tgt_id in entry_ids)
        src_entry = sense_to_entry.get(src_id) if src_kind == "sense" else (src_id if src_kind == "entry" and src_id in entry_ids else None)
        tgt_entry = sense_to_entry.get(tgt_id) if tgt_kind == "sense" else (tgt_id if tgt_kind == "entry" and tgt_id in entry_ids else None)
        if not (src_in and tgt_in):
            owner_entry = src_entry if src_in else tgt_entry
            if owner_entry is None or pack_policy.get(owner_entry) != "evidence_only_external":
                missing_endpoint = tgt_id if src_in else src_id
                findings.append(
                    _finding(
                        "RELATION_EXTERNAL_CLOSURE_VIOLATION",
                        r["relation_id"],
                        f"Relation endpoint {missing_endpoint!r} is outside pack {pack!r} without evidence_only_external policy",
                        field="relations",
                    )
                )

    sources_by_id = {s["source_id"]: s for s in tables["sources"]}
    ev_by_aid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in tables["evidence"]:
        ev_by_aid[ev["assertion_id"]].append(ev)
    dec_by_aid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for dec in tables["decisions"]:
        dec_by_aid[dec["assertion_id"]].append(dec)
    exc_by_aid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for exc in tables["unicode_exceptions"]:
        exc_by_aid[exc["assertion_id"]].append(exc)

    pos_unknown_aids = {
        a["assertion_id"]
        for a in tables["assertions"]
        if a["property_code"] == "part_of_speech" and a["value_state"] in {"unknown", "not_applicable"}
    }

    sources_unique = len(sources_by_id) == len(tables["sources"])
    audit_cache = lexicon_review.build_text_audit_cache(tables["assertions"])
    claim_revs = lexicon_review.batch_claim_revisions(tables["assertions"])
    eligible_count = 0
    for a, computed_rev in zip(tables["assertions"], claim_revs):
        aid = a["assertion_id"]
        u_findings = lexicon_review.unicode_findings(
            a,
            exc_by_aid[aid],
            dec_by_aid[aid],
            _audit_cache=audit_cache,
            _revision=computed_rev,
        )
        for uf in u_findings:
            findings.append(
                _finding(
                    uf.get("issue_code", "UNICODE_EXCEPTION_REQUIRED"),
                    aid,
                    uf.get("reason", "Unicode validation failed"),
                    field="value_json",
                    scalar_positions=uf.get("scalar_positions"),
                )
            )

        if aid in pos_unknown_aids:
            unk_reasons = _validate_unknown_claim_review(
                a, ev_by_aid[aid], sources_by_id, dec_by_aid[aid], tables["findings"], _revision=computed_rev
            )
            if unk_reasons:
                findings.append(
                    _finding(
                        "INELIGIBLE_UNKNOWN_POS_CLAIM",
                        aid,
                        "Unknown POS claim lacks valid review/evidence: " + ", ".join(unk_reasons),
                        field="assertions",
                    )
                )
            continue

        elig = lexicon_review.eligibility(
            a,
            ev_by_aid[aid],
            tables["sources"],
            dec_by_aid[aid],
            tables["findings"],
            _revision=computed_rev,
            _assertion_valid=aid not in invalid_assertions,
            _source_index=sources_by_id if sources_unique else None,
            _evidence_valid=True if aid not in invalid_evidence else None,
        )
        if elig["eligible"]:
            eligible_count += 1
        else:
            findings.append(
                _finding(
                    "INELIGIBLE_ASSERTION",
                    aid,
                    "Assertion failed eligibility: " + ", ".join(elig["reasons"]),
                    field="decisions",
                )
            )

    if eligible_count == 0 and not any(f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" for f in findings):
        findings.append(
            _finding(
                "NONEMPTY_ELIGIBLE_PACK_REQUIRED",
                pack,
                f"Pack {pack!r} produced zero eligible assertions",
                field="assertions",
            )
        )
    return findings, eligible_count


def load_trusted_canonical(
    canonical: str | pathlib.Path,
    pack: str,
    *,
    canonical_validator: Callable[[pathlib.Path, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Load, validate, and verify pack closure from trusted canonical input."""
    if pack not in SUPPORTED_PACKS:
        raise lexicon.LexiconError(f"Unsupported pack {pack!r}; expected one of {SUPPORTED_PACKS}", code=2)

    canon_dir = pathlib.Path(canonical)
    if not canon_dir.is_dir():
        raise lexicon.LexiconError(f"Canonical directory does not exist: {canon_dir}", code=2)

    input_digests: dict[str, str] = {}
    for p in sorted(canon_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(canon_dir).as_posix()
            input_digests[rel] = lexicon.digest(p)

    packs_meta: dict[str, Any] = {}
    packs_path = canon_dir / "packs.toml"
    if packs_path.is_file():
        try:
            packs_meta = tomllib.loads(packs_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
            raise lexicon.LexiconError(f"Invalid packs.toml in {canon_dir}: {exc}", code=2) from exc

    vocab_path = canon_dir / "vocabularies.toml"
    if vocab_path.is_file():
        expected_vsha = packs_meta.get("vocabularies_sha256")
        actual_vsha = lexicon.digest(vocab_path)
        if expected_vsha and expected_vsha != actual_vsha:
            raise lexicon.LexiconError("vocabularies.toml SHA-256 does not match packs.toml", code=2)

    raw_tables: dict[str, list[dict[str, Any]]] = {}
    for table in CANONICAL_TABLES:
        csv_path = canon_dir / f"{table}.csv"
        raw_tables[table] = list(lexicon_tables.read_rows(csv_path, table)) if csv_path.is_file() else []

    pack_tables = _pack_closure_tables(raw_tables, pack)
    findings = _run_upstream_pack_validator(
        canon_dir,
        pack,
        packs_meta,
        canonical_validator,
        preloaded_tables=raw_tables,
        prevalidated_schema=True,
    )
    elig_findings, eligible_count = _evaluate_pack_eligibility(pack_tables, pack, prevalidated_schema=True)
    findings.extend(elig_findings)
    pack_member_packs = {m["pack_id"] for m in raw_tables["pack_members"]}
    if pack_tables["pack_members"] and pack_member_packs <= {pack}:
        pack_rel_ids = {r["relation_id"] for r in pack_tables["relations"]}
        for r in raw_tables["relations"]:
            if r["relation_id"] not in pack_rel_ids:
                findings.append(
                    _finding(
                        "RELATION_EXTERNAL_CLOSURE_VIOLATION",
                        r["relation_id"],
                        f"Relation {r['relation_id']!r} in single-pack canonical input is not owned by pack {pack!r} and cannot be silently omitted",
                        field="relations",
                    )
                )

    pack_cfg = (packs_meta.get("packs") or {}).get(pack, {}) if isinstance(packs_meta, dict) else {}
    notices, notice_findings = _load_notices(canon_dir, pack_cfg, pack_tables["sources"])
    findings.extend(notice_findings)

    if isinstance(pack_cfg, dict) and "eligible_assertions" in pack_cfg:
        declared = pack_cfg["eligible_assertions"]
        if isinstance(declared, int) and declared != eligible_count and not any(
            f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" for f in findings
        ):
            findings.append(
                _finding(
                    "PACK_MANIFEST_COUNT_MISMATCH",
                    pack,
                    f"packs.toml declares eligible_assertions={declared} but computed {eligible_count}",
                    field="packs.toml",
                )
            )

    findings.sort(key=lambda item: (item["code"], item["entity_id"], item["field"], item["reason"]))
    dataset_version = (
        pack_cfg.get("dataset_version")
        if isinstance(pack_cfg, dict) and pack_cfg.get("dataset_version")
        else packs_meta.get("dataset_version")
    )

    return {
        "canonical_dir": canon_dir,
        "pack": pack,
        "dataset_version": dataset_version,
        "input_digests": input_digests,
        "tables": pack_tables,
        "notices": notices,
        "eligible_assertions": eligible_count,
        "findings": findings,
        "l2_structural_accepted": bool(packs_meta.get("l2_structural_accepted", False)),
        "l3_pack_eligible": eligible_count > 0 and not findings,
    }


def _build_sources_bib(sources: list[dict[str, Any]]) -> str:
    def _bib_escape(value: Any) -> str:
        text = "" if value is None else str(value)
        return text.replace("{", "\\{").replace("}", "\\}")

    blocks: list[str] = []
    for src in sorted(sources, key=lambda r: r["source_id"]):
        fields = [
            ("title", src.get("label_json")),
            ("booktitle", src.get("publication_json")),
            ("url", src.get("url_json")),
            ("edition", src.get("edition_json")),
            ("copyright", src.get("reuse_basis_json")),
            ("note", f"reuse={src.get('reuse_state')}; attribution={src.get('attribution_text_json')}"),
        ]
        rendered = ",\n".join(
            f"  {key} = {{{_bib_escape(val)}}}" for key, val in fields if val not in (None, "")
        )
        blocks.append(f"@misc{{{src['source_id']},\n{rendered}\n}}")
    return ("\n\n".join(blocks) + "\n") if blocks else ""


def _source_refs_for_assertions(
    assertion_ids: list[str],
    ev_by_aid: dict[str, list[dict[str, Any]]],
) -> str:
    keys: set[str] = set()
    for aid in assertion_ids:
        for ev in ev_by_aid.get(aid, []):
            keys.add(ev["source_id"])
    return ";".join(sorted(keys))


def _col_spec(
    name: str,
    *,
    datatype: Any = "string",
    required: bool = True,
    nullable: bool = False,
    property_url: str | None = None,
    separator: str | None = None,
    extent: str | None = None,
) -> dict[str, Any]:
    col: dict[str, Any] = {"name": name, "datatype": datatype}
    if required and not nullable:
        col["required"] = True
    if nullable:
        col["required"] = False
        col["null"] = ""
    if property_url:
        col["propertyUrl"] = property_url
    if separator is not None:
        col["separator"] = separator
    if extent:
        col["dc:extent"] = extent
    return col


def _id_datatype() -> dict[str, str]:
    return {"base": "string", "format": ID_REGEX}


def _custom_table_schema(table: str, fk_specs: list[tuple[str, str, str]]) -> dict[str, Any]:
    if table == "notices":
        cols = [
            _col_spec("notice_id", datatype=_id_datatype()),
            _col_spec("relative_path"),
            _col_spec("sha256"),
            _col_spec("bytes", datatype="integer"),
        ]
        pk = ["notice_id"]
    else:
        field_names = lexicon_tables.fields(table)
        pk_col = lexicon_tables.PRIMARY_ID_COLS.get(table)
        if table == "evidence":
            pk = ["assertion_id", "source_id", "source_record_id", "evidence_role"]
        elif table == "identities":
            pk = ["entity_id"]
        elif table == "unicode_exceptions":
            pk = ["assertion_id", "kind"]
        elif table == "labels":
            pk = ["registry_id", "code"]
        elif table == "scopes":
            pk = ["subject_kind", "subject_id", "dimension", "state", "label_code", "supporting_assertion_id"]
        elif table == "successors":
            pk = ["retired_id", "successor_id"]
        elif table == "pack_members":
            pk = ["pack_id", "entry_id"]
        else:
            pk = [pk_col]

        cols = []
        col_specs = _column_specs(table)
        for name in field_names:
            spec = col_specs[name]
            dt: Any = "integer" if spec.kind == "int" else (_id_datatype() if name == pk_col else "string")
            cols.append(_col_spec(name, datatype=dt, nullable=spec.nullable))

    schema: dict[str, Any] = {"columns": cols, "primaryKey": pk}
    if fk_specs:
        schema["foreignKeys"] = [
            {
                "columnReference": col_ref,
                "reference": {"resource": target_res, "columnReference": target_col},
            }
            for col_ref, target_res, target_col in fk_specs
        ]
    return schema


def _build_metadata(pack: str, dataset_version: str | None, schema_manifest_sha256: str) -> dict[str, Any]:
    t_base = "http://cldf.clld.org/v1.0/terms.rdf#"
    tables_meta: list[dict[str, Any]] = [
        {
            "url": "languages.csv",
            "dc:conformsTo": f"{t_base}LanguageTable",
            "tableSchema": {
                "columns": [
                    _col_spec("ID", datatype=_id_datatype(), property_url=f"{t_base}id"),
                    _col_spec("Name", property_url=f"{t_base}name"),
                    _col_spec("Glottocode", nullable=True, property_url=f"{t_base}glottocode"),
                    _col_spec("ISO639P3code", nullable=True, property_url=f"{t_base}iso639P3code"),
                    _col_spec("Kind"),
                    _col_spec("Parent_Language_ID", nullable=True),
                ],
                "primaryKey": ["ID"],
            },
        },
        {
            "url": "entries.csv",
            "dc:conformsTo": f"{t_base}EntryTable",
            "tableSchema": {
                "columns": [
                    _col_spec("ID", datatype=_id_datatype(), property_url=f"{t_base}id"),
                    _col_spec("Language_ID", property_url=f"{t_base}languageReference", extent="singlevalued"),
                    _col_spec("Headword", property_url=f"{t_base}headword", extent="singlevalued"),
                    _col_spec("Part_Of_Speech", nullable=True, property_url=f"{t_base}partOfSpeech"),
                    _col_spec("Variety_ID", nullable=True),
                    _col_spec("Canonical_Form_ID"),
                    _col_spec("POS_Assertion_ID", nullable=True),
                    _col_spec("POS_Value_State"),
                    _col_spec("Structural_Kind"),
                    _col_spec("Revision"),
                    _col_spec("Pack_ID"),
                    _col_spec("Source", property_url=f"{t_base}source", separator=";"),
                ],
                "primaryKey": ["ID"],
                "foreignKeys": [
                    {"columnReference": "Language_ID", "reference": {"resource": "languages.csv", "columnReference": "ID"}},
                    {"columnReference": "Variety_ID", "reference": {"resource": "languages.csv", "columnReference": "ID"}},
                    {"columnReference": "Canonical_Form_ID", "reference": {"resource": "forms.csv", "columnReference": "form_id"}},
                    {"columnReference": "POS_Assertion_ID", "reference": {"resource": "assertions.csv", "columnReference": "assertion_id"}},
                ],
            },
        },
        {
            "url": "senses.csv",
            "dc:conformsTo": f"{t_base}SenseTable",
            "tableSchema": {
                "columns": [
                    _col_spec("ID", datatype=_id_datatype(), property_url=f"{t_base}id"),
                    _col_spec("Description", property_url=f"{t_base}description"),
                    _col_spec("Entry_ID", property_url=f"{t_base}entryReference"),
                    _col_spec("Display_Order", datatype="integer"),
                    _col_spec("Parent_Sense_ID", nullable=True),
                    _col_spec("Primary_Text_ID"),
                    _col_spec("Source", property_url=f"{t_base}source", separator=";"),
                ],
                "primaryKey": ["ID"],
                "foreignKeys": [
                    {"columnReference": "Entry_ID", "reference": {"resource": "entries.csv", "columnReference": "ID"}},
                    {"columnReference": "Parent_Sense_ID", "reference": {"resource": "senses.csv", "columnReference": "ID"}},
                    {"columnReference": "Primary_Text_ID", "reference": {"resource": "texts.csv", "columnReference": "text_id"}},
                ],
            },
        },
        {
            "url": "examples.csv",
            "dc:conformsTo": f"{t_base}ExampleTable",
            "tableSchema": {
                "columns": [
                    _col_spec("ID", datatype=_id_datatype(), property_url=f"{t_base}id"),
                    _col_spec("Language_ID", property_url=f"{t_base}languageReference", extent="singlevalued"),
                    _col_spec("Primary_Text", property_url=f"{t_base}primaryText"),
                    _col_spec("Analyzed_Word", nullable=True, property_url=f"{t_base}analyzedWord", separator="\t"),
                    _col_spec("Gloss", nullable=True, property_url=f"{t_base}gloss", separator="\t"),
                    _col_spec("Translated_Text", nullable=True, property_url=f"{t_base}translatedText"),
                    _col_spec("Meta_Language_ID", nullable=True, property_url=f"{t_base}metaLanguageReference"),
                    _col_spec("Sense_ID"),
                    _col_spec("Text_Assertion_ID"),
                    _col_spec("Paired_Translation_ID", nullable=True),
                    _col_spec("Source", property_url=f"{t_base}source", separator=";"),
                ],
                "primaryKey": ["ID"],
                "foreignKeys": [
                    {"columnReference": "Language_ID", "reference": {"resource": "languages.csv", "columnReference": "ID"}},
                    {"columnReference": "Meta_Language_ID", "reference": {"resource": "languages.csv", "columnReference": "ID"}},
                    {"columnReference": "Sense_ID", "reference": {"resource": "senses.csv", "columnReference": "ID"}},
                    {"columnReference": "Text_Assertion_ID", "reference": {"resource": "assertions.csv", "columnReference": "assertion_id"}},
                    {"columnReference": "Paired_Translation_ID", "reference": {"resource": "texts.csv", "columnReference": "text_id"}},
                ],
            },
        },
    ]

    ext_fks: dict[str, list[tuple[str, str, str]]] = {
        "forms": [
            ("entry_id", "entries.csv", "ID"),
            ("text_assertion_id", "assertions.csv", "assertion_id"),
            ("convention_assertion_id", "assertions.csv", "assertion_id"),
        ],
        "texts": [
            ("text_assertion_id", "assertions.csv", "assertion_id"),
            ("paired_translation_id", "texts.csv", "text_id"),
        ],
        "relations": [
            ("relation_code_assertion_id", "assertions.csv", "assertion_id"),
        ],
        "sources": [],
        "assertions": [],
        "evidence": [
            ("assertion_id", "assertions.csv", "assertion_id"),
            ("source_id", "sources.csv", "source_id"),
        ],
        "decisions": [
            ("assertion_id", "assertions.csv", "assertion_id"),
            ("predecessor_decision_id", "decisions.csv", "decision_id"),
        ],
        "changes": [
            ("old_assertion_id", "assertions.csv", "assertion_id"),
            ("new_assertion_id", "assertions.csv", "assertion_id"),
            ("decision_id", "decisions.csv", "decision_id"),
            ("inverse_change_id", "changes.csv", "change_id"),
        ],
        "successors": [
            ("identity_decision_id", "decisions.csv", "decision_id"),
        ],
        "identities": [
            ("identity_decision_id", "decisions.csv", "decision_id"),
        ],
        "findings": [],
        "unicode_exceptions": [
            ("assertion_id", "assertions.csv", "assertion_id"),
            ("decision_id", "decisions.csv", "decision_id"),
        ],
        "labels": [],
        "scopes": [
            ("supporting_assertion_id", "assertions.csv", "assertion_id"),
            ("decision_id", "decisions.csv", "decision_id"),
        ],
        "pack_members": [
            ("entry_id", "entries.csv", "ID"),
        ],
        "notices": [],
    }
    for tname, fk_specs in ext_fks.items():
        tables_meta.append(
            {
                "url": f"{tname}.csv",
                "tableSchema": _custom_table_schema(tname, fk_specs),
            }
        )

    return {
        "@context": ["http://www.w3.org/ns/csvw", {"@language": "en"}],
        "dc:conformsTo": f"{t_base}Dictionary",
        "dc:title": f"Tamil Toolkit Lexicon Pack ({pack})",
        "dc:identifier": f"tamil-toolkit:{pack}:{dataset_version or 'unversioned'}",
        "dc:description": (
            f"cldf_version={CLDF_VERSION};pack={pack};"
            f"schema_manifest_sha256={schema_manifest_sha256}"
        ),
        "dc:source": "sources.bib",
        "dialect": {"commentPrefix": None},
        "tables": tables_meta,
    }


def _write_csv(path: pathlib.Path, headers: list[str], rows: list[list[Any]]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        for row in rows:
            writer.writerow(["" if val is None else val for val in row])


def _encode_ext_cell(table: str, col: str, val: Any) -> str:
    spec = _column_specs(table)[col]
    if spec.kind == "json":
        return lexicon.json_text(val) if spec.is_array else lexicon.data_json(val)
    if val is None:
        return ""
    return str(val)


def _decode_ext_cell(table: str, col: str, raw: Any) -> Any:
    spec = _column_specs(table)[col]
    if spec.kind == "json":
        return json.loads(raw)
    if raw is None or (spec.nullable and raw == ""):
        return None
    if spec.kind == "int":
        return int(raw)
    return raw


def _render_cldf_bundle(
    trusted: dict[str, Any],
    out_dir: pathlib.Path,
    schema_manifest_sha256: str,
) -> None:
    tables = trusted["tables"]
    pack = trusted["pack"]
    assertions_by_id = {a["assertion_id"]: a for a in tables["assertions"]}
    forms_by_id = {f["form_id"]: f for f in tables["forms"]}
    texts_by_id = {t["text_id"]: t for t in tables["texts"]}
    ev_by_aid: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in tables["evidence"]:
        ev_by_aid[ev["assertion_id"]].append(ev)

    lang_rows: dict[str, dict[str, Any]] = {}

    def ensure_lang(lid: str, kind: str = "language", parent: str | None = None) -> None:
        if lid in lang_rows:
            return
        iso = "tam" if lid in {"ta", "tam"} or lid.startswith("ta-") else ("eng" if lid in {"en", "eng"} else None)
        glotto = "tami1289" if lid in {"ta", "tam"} else ("stan1293" if lid in {"en", "eng"} else None)
        name = "Tamil" if lid in {"ta", "tam"} else ("English" if lid in {"en", "eng"} else lid)
        lang_rows[lid] = {
            "ID": lid,
            "Name": name,
            "Glottocode": glotto,
            "ISO639P3code": iso,
            "Kind": kind,
            "Parent_Language_ID": parent,
        }

    for e in tables["entries"]:
        ensure_lang(e["language_id"], kind="language")
        if e.get("variety_id"):
            ensure_lang(e["variety_id"], kind="variety", parent=e["language_id"])
    for t in tables["texts"]:
        ensure_lang(t["language_id"], kind="language")

    languages_out = [
        [
            lang_rows[lid]["ID"],
            lang_rows[lid]["Name"],
            lang_rows[lid]["Glottocode"],
            lang_rows[lid]["ISO639P3code"],
            lang_rows[lid]["Kind"],
            lang_rows[lid]["Parent_Language_ID"],
        ]
        for lid in sorted(lang_rows)
    ]
    _write_csv(
        out_dir / "languages.csv",
        ["ID", "Name", "Glottocode", "ISO639P3code", "Kind", "Parent_Language_ID"],
        languages_out,
    )

    entries_out: list[list[Any]] = []
    for e in tables["entries"]:
        cf = forms_by_id[e["canonical_form_id"]]
        hw = assertions_by_id[cf["text_assertion_id"]]["value_json"]
        pos_aid = e.get("pos_assertion_id")
        if pos_aid:
            pos_asrt = assertions_by_id[pos_aid]
            pos_val = pos_asrt["value_json"] if pos_asrt["value_state"] == "known" else None
            pos_state = pos_asrt["value_state"]
            src_aids = [cf["text_assertion_id"], pos_aid]
        else:
            pos_val = None
            pos_state = "unknown"
            src_aids = [cf["text_assertion_id"]]
        src_refs = _source_refs_for_assertions(src_aids, ev_by_aid)
        entries_out.append([
            e["entry_id"],
            e["language_id"],
            hw,
            pos_val,
            e["variety_id"],
            e["canonical_form_id"],
            pos_aid,
            pos_state,
            e["structural_kind"],
            e["revision"],
            pack,
            src_refs,
        ])
    _write_csv(
        out_dir / "entries.csv",
        [
            "ID", "Language_ID", "Headword", "Part_Of_Speech", "Variety_ID",
            "Canonical_Form_ID", "POS_Assertion_ID", "POS_Value_State",
            "Structural_Kind", "Revision", "Pack_ID", "Source",
        ],
        entries_out,
    )

    texts_by_sense: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in tables["texts"]:
        if t["owner_kind"] == "sense":
            texts_by_sense[t["owner_id"]].append(t)

    senses_out: list[list[Any]] = []
    for s in tables["senses"]:
        candidates = sorted(
            [t for t in texts_by_sense[s["sense_id"]] if t["component"] in {"gloss", "definition"}],
            key=lambda t: (0 if t["component"] == "gloss" else 1, t["text_id"]),
        )
        primary = candidates[0]
        desc = assertions_by_id[primary["text_assertion_id"]]["value_json"]
        src_refs = _source_refs_for_assertions([t["text_assertion_id"] for t in candidates], ev_by_aid)
        senses_out.append([
            s["sense_id"],
            desc,
            s["entry_id"],
            s["display_order"],
            s["parent_sense_id"],
            primary["text_id"],
            src_refs,
        ])
    _write_csv(
        out_dir / "senses.csv",
        ["ID", "Description", "Entry_ID", "Display_Order", "Parent_Sense_ID", "Primary_Text_ID", "Source"],
        senses_out,
    )

    examples_out: list[list[Any]] = []
    for t in sorted([r for r in tables["texts"] if r["component"] == "example"], key=lambda r: r["text_id"]):
        ex_text = assertions_by_id[t["text_assertion_id"]]["value_json"]
        tr_id = t.get("paired_translation_id")
        tr_text = None
        tr_lang = None
        ref_aids = [t["text_assertion_id"]]
        if tr_id and tr_id in texts_by_id:
            tr_row = texts_by_id[tr_id]
            tr_text = assertions_by_id[tr_row["text_assertion_id"]]["value_json"]
            tr_lang = tr_row["language_id"]
            ref_aids.append(tr_row["text_assertion_id"])
        src_refs = _source_refs_for_assertions(ref_aids, ev_by_aid)
        examples_out.append([
            t["text_id"],
            t["language_id"],
            ex_text,
            None,
            None,
            tr_text,
            tr_lang,
            t["owner_id"],
            t["text_assertion_id"],
            tr_id,
            src_refs,
        ])
    _write_csv(
        out_dir / "examples.csv",
        [
            "ID", "Language_ID", "Primary_Text", "Analyzed_Word", "Gloss",
            "Translated_Text", "Meta_Language_ID", "Sense_ID",
            "Text_Assertion_ID", "Paired_Translation_ID", "Source",
        ],
        examples_out,
    )

    for table in CUSTOM_EXTENSION_TABLES:
        cols = lexicon_tables.fields(table)
        rows = [
            [_encode_ext_cell(table, col, row.get(col)) for col in cols]
            for row in tables[table]
        ]
        _write_csv(out_dir / f"{table}.csv", cols, rows)

    notices_rows: list[list[Any]] = []
    for idx, (rel, raw) in enumerate(sorted(trusted["notices"].items()), start=1):
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(raw)
        notices_rows.append([f"notice:{idx}", rel, _sha256_bytes(raw), len(raw)])
    _write_csv(out_dir / "notices.csv", ["notice_id", "relative_path", "sha256", "bytes"], notices_rows)

    (out_dir / "sources.bib").write_text(
        _build_sources_bib(tables["sources"]),
        encoding="utf-8",
        newline="\n",
    )
    metadata = _build_metadata(pack, trusted["dataset_version"], schema_manifest_sha256)
    (out_dir / "Dictionary-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class _LogCollector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.records: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(self.format(record))


def _install_per_call_csvw_cache(tg: csvw.TableGroup, primary_handler: _LogCollector) -> dict[str, list[tuple[Any, int, dict[str, Any]]]]:
    """Memoize verified csvw.Table.iterdicts rows within a single immutable validation call."""
    orig_iterdicts = csvw.Table.iterdicts
    row_cache: dict[str, list[tuple[Any, int, dict[str, Any]]]] = {}

    for idx, tbl in enumerate(tg.tables):
        cache_key = tbl.local_name or pathlib.Path(str(tbl.url)).name or f"__tbl_{idx}"

        def cached_iterdicts(
            self,
            log=None,
            with_metadata=False,
            fname=None,
            _Row=OrderedDict,
            strict=True,
            _cache_key=cache_key,
        ):
            if fname is not None or not strict or _Row is not OrderedDict:
                yield from orig_iterdicts(
                    self, log=log, with_metadata=with_metadata, fname=fname, _Row=_Row, strict=strict
                )
                return
            cached = row_cache.get(_cache_key)
            if cached is not None:
                if with_metadata:
                    yield from cached
                else:
                    for _, _, row in cached:
                        yield row
                return
            records_before = len(primary_handler.records)
            collected: list[tuple[Any, int, dict[str, Any]]] = []
            for item in orig_iterdicts(
                self, log=log, with_metadata=True, fname=None, _Row=OrderedDict, strict=True
            ):
                collected.append(item)
                yield item if with_metadata else item[2]
            if len(primary_handler.records) == records_before:
                row_cache[_cache_key] = collected

        tbl.iterdicts = types.MethodType(cached_iterdicts, tbl)

    return row_cache


def _validate_cldf_offline_impl(
    cldf_dir: pathlib.Path,
    schema_dir: pathlib.Path,
    *,
    collect_decoded: bool = False,
) -> tuple[bool, list[dict[str, Any]], dict[str, list[dict[str, Any]]] | None]:
    findings: list[dict[str, Any]] = []
    md_path = cldf_dir / "Dictionary-metadata.json"
    if not md_path.is_file():
        return False, [_finding("CLDF_METADATA_MISSING", "Dictionary-metadata.json", "Missing CLDF metadata JSON", field="metadata")], None

    try:
        md_obj = json.loads(md_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, [_finding("CLDF_METADATA_INVALID", "Dictionary-metadata.json", f"Invalid JSON: {exc}", field="metadata")], None

    if md_obj.get("dc:conformsTo") != "http://cldf.clld.org/v1.0/terms.rdf#Dictionary":
        findings.append(
            _finding(
                "CLDF_MODULE_INVALID",
                "Dictionary-metadata.json",
                f"Expected Dictionary module, got {md_obj.get('dc:conformsTo')!r}",
                field="dc:conformsTo",
            )
        )

    actual_urls = tuple(t.get("url") for t in md_obj.get("tables", []) if isinstance(t, dict))
    if set(actual_urls) != set(CLOSED_CSV_FILES) or len(actual_urls) != len(CLOSED_CSV_FILES):
        findings.append(
            _finding(
                "CLDF_TABLE_SET_MISMATCH",
                "Dictionary-metadata.json",
                f"Expected closed table set {sorted(CLOSED_CSV_FILES)}, got {sorted(actual_urls)}",
                field="tables",
            )
        )

    handler = _LogCollector()
    logger = logging.getLogger(f"tamil_toolkit.cldf.{id(handler)}")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.WARNING)

    ds_completed = False
    ds = None
    row_cache: dict[str, list[tuple[Any, int, dict[str, Any]]]] | None = None
    try:
        ds = pycldf.Dataset.from_metadata(md_path)
        row_cache = _install_per_call_csvw_cache(ds.tablegroup, handler)
        valid = bool(ds.validate(log=logger, ontology_path=schema_dir / "v1.3" / "terms.rdf"))
        ds_completed = True
    except Exception as exc:  # noqa: BLE001 - pycldf raises ValueError/SchemaError on structural flaws
        findings.append(_finding("PYCLDF_VALIDATION_ERROR", "Dictionary-metadata.json", str(exc), field="pycldf"))
        valid = False

    for msg in handler.records:
        if msg.startswith("Table with composite primary key:"):
            continue
        findings.append(_finding("PYCLDF_VALIDATION_WARNING", "Dictionary-metadata.json", msg, field="pycldf"))

    try:
        bib_keys = set(ds.sources.keys()) if (ds is not None and (valid or (cldf_dir / "sources.bib").is_file())) else set()
        if ds is not None:
            for tbl_name in ("EntryTable", "SenseTable", "ExampleTable"):
                if tbl_name not in ds:
                    continue
                for row in ds[tbl_name]:
                    for raw_ref in row.get("Source") or []:
                        key = str(raw_ref).split("[", 1)[0]
                        if key and key not in bib_keys:
                            findings.append(
                                _finding(
                                    "CLDF_SOURCE_BIB_MISSING",
                                    str(row.get("ID") or tbl_name),
                                    f"Source citation key {key!r} missing from sources.bib",
                                    field="Source",
                                )
                            )
    except Exception as exc:  # noqa: BLE001
        findings.append(_finding("CLDF_BIBTEX_CHECK_ERROR", "sources.bib", str(exc), field="sources.bib"))

    # pycldf.Dataset.validate() already invokes ds.tablegroup.check_referential_integrity()
    # when it completes; only run the standalone CSVW FK pass if pycldf did not succeed cleanly.
    if not (ds_completed and valid):
        try:
            tg = csvw.TableGroup.from_file(md_path)
            if not tg.check_referential_integrity():
                findings.append(_finding("CSVW_FK_VIOLATION", "Dictionary-metadata.json", "CSVW referential integrity check failed", field="foreignKeys"))
        except Exception as exc:  # noqa: BLE001
            findings.append(_finding("CSVW_VALIDATION_ERROR", "Dictionary-metadata.json", str(exc), field="csvw"))

    ok = bool(valid and not findings)
    decoded_tables: dict[str, list[dict[str, Any]]] | None = None
    if collect_decoded and ok and ds is not None:
        decoded_tables = {}
        for tbl in ds.tablegroup.tables:
            tname = tbl.local_name or pathlib.Path(str(tbl.url)).name
            if row_cache is not None and tname in row_cache:
                decoded_tables[tname] = [row for _, _, row in row_cache[tname]]
            else:
                decoded_tables[tname] = list(tbl)
    if row_cache is not None:
        row_cache.clear()
    return ok, findings, decoded_tables


def _validate_cldf_offline(cldf_dir: pathlib.Path, schema_dir: pathlib.Path) -> tuple[bool, list[dict[str, Any]]]:
    ok, findings, _ = _validate_cldf_offline_impl(cldf_dir, schema_dir, collect_decoded=False)
    return ok, findings


def verify_cldf_export(
    cldf_dir: str | pathlib.Path,
    trusted_canonical: dict[str, Any],
    *,
    schema_dir: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Validate exported CLDF 1.3 offline and assert lossless roundtrip vs trusted input."""
    base_schema = CLDF_SCHEMA_DIR if schema_dir is None else pathlib.Path(schema_dir)
    verify_cldf_schemas(base_schema)
    target = pathlib.Path(cldf_dir)

    cldf_valid, cldf_findings, decoded_tables = _validate_cldf_offline_impl(
        target, base_schema, collect_decoded=True
    )
    rt_findings: list[dict[str, Any]] = []

    if cldf_valid:
        try:
            if decoded_tables is None:
                tg = csvw.TableGroup.from_file(target / "Dictionary-metadata.json")
                decoded_tables = {}
                for tbl in tg.tables:
                    decoded_tables[tbl.local_name or pathlib.Path(str(tbl.url)).name] = list(tbl)

            trusted_tables = trusted_canonical["tables"]
            decoded_ext: dict[str, list[dict[str, Any]]] = {
                "entries": [
                    {
                        "entry_id": r["ID"],
                        "language_id": r["Language_ID"],
                        "variety_id": r["Variety_ID"],
                        "canonical_form_id": r["Canonical_Form_ID"],
                        "pos_assertion_id": r["POS_Assertion_ID"],
                        "structural_kind": r["Structural_Kind"],
                        "revision": r["Revision"],
                    }
                    for r in decoded_tables.get("entries.csv", [])
                ],
                "senses": [
                    {
                        "sense_id": r["ID"],
                        "entry_id": r["Entry_ID"],
                        "display_order": r["Display_Order"],
                        "parent_sense_id": r["Parent_Sense_ID"],
                    }
                    for r in decoded_tables.get("senses.csv", [])
                ],
            }
            for table in CUSTOM_EXTENSION_TABLES:
                fname = f"{table}.csv"
                cols = lexicon_tables.fields(table)
                raw_rows = decoded_tables.get(fname, [])
                decoded_ext[table] = [
                    {col: _decode_ext_cell(table, col, row.get(col)) for col in cols}
                    for row in raw_rows
                ]
            for table in CANONICAL_TABLES:
                if decoded_ext[table] != trusted_tables[table]:
                    rt_findings.append(
                        _finding(
                            "ROUNDTRIP_TABLE_MISMATCH",
                            table,
                            f"Decoded CLDF table for {table} differs from trusted canonical table",
                            field=table,
                        )
                    )

            # Re-verify exported review/eligibility on decoded extension rows (never trust labels blindly).
            recheck_findings, _ = _evaluate_pack_eligibility(decoded_ext, trusted_canonical["pack"])
            for rf in recheck_findings:
                rf["code"] = f"ROUNDTRIP_{rf['code']}"
                rt_findings.append(rf)

            # Verify standard CLDF Dictionary tables scalar-for-scalar against trusted assertions.
            assertions_by_id = {a["assertion_id"]: a for a in trusted_tables["assertions"]}
            forms_by_id = {f["form_id"]: f for f in trusted_tables["forms"]}
            texts_by_id = {t["text_id"]: t for t in trusted_tables["texts"]}

            std_entries = {r["ID"]: r for r in decoded_tables["entries.csv"]}
            for e in trusted_tables["entries"]:
                re_row = std_entries.get(e["entry_id"])
                exp_hw = assertions_by_id[forms_by_id[e["canonical_form_id"]]["text_assertion_id"]]["value_json"]
                pos_aid = e.get("pos_assertion_id")
                if pos_aid:
                    pos_a = assertions_by_id[pos_aid]
                    exp_pos = pos_a["value_json"] if pos_a["value_state"] == "known" else None
                    exp_state = pos_a["value_state"]
                else:
                    exp_pos = None
                    exp_state = "unknown"
                if (
                    re_row is None
                    or re_row["Headword"] != exp_hw
                    or re_row["Part_Of_Speech"] != exp_pos
                    or re_row["POS_Value_State"] != exp_state
                    or re_row["Language_ID"] != e["language_id"]
                    or re_row["Variety_ID"] != e["variety_id"]
                    or re_row["Revision"] != e["revision"]
                ):
                    rt_findings.append(
                        _finding(
                            "ROUNDTRIP_ENTRY_MISMATCH",
                            e["entry_id"],
                            "Standard CLDF entries.csv row differs from trusted canonical scalars",
                            field="entries.csv",
                        )
                    )

            std_senses = {r["ID"]: r for r in decoded_tables["senses.csv"]}
            texts_by_sense: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for t in trusted_tables["texts"]:
                if t["owner_kind"] == "sense" and t["component"] in {"gloss", "definition"}:
                    texts_by_sense[t["owner_id"]].append(t)
            for s in trusted_tables["senses"]:
                s_row = std_senses.get(s["sense_id"])
                primary = sorted(
                    texts_by_sense[s["sense_id"]],
                    key=lambda t: (0 if t["component"] == "gloss" else 1, t["text_id"]),
                )[0]
                exp_desc = assertions_by_id[primary["text_assertion_id"]]["value_json"]
                if (
                    s_row is None
                    or s_row["Description"] != exp_desc
                    or s_row["Entry_ID"] != s["entry_id"]
                    or s_row["Display_Order"] != s["display_order"]
                    or s_row["Parent_Sense_ID"] != s["parent_sense_id"]
                ):
                    rt_findings.append(
                        _finding(
                            "ROUNDTRIP_SENSE_MISMATCH",
                            s["sense_id"],
                            "Standard CLDF senses.csv row differs from trusted canonical scalars",
                            field="senses.csv",
                        )
                    )

            std_examples = {r["ID"]: r for r in decoded_tables["examples.csv"]}
            for t in trusted_tables["texts"]:
                if t["component"] != "example":
                    continue
                ex_row = std_examples.get(t["text_id"])
                exp_txt = assertions_by_id[t["text_assertion_id"]]["value_json"]
                tr_id = t.get("paired_translation_id")
                exp_tr = assertions_by_id[texts_by_id[tr_id]["text_assertion_id"]]["value_json"] if tr_id else None
                if ex_row is None or ex_row["Primary_Text"] != exp_txt or ex_row["Translated_Text"] != exp_tr:
                    rt_findings.append(
                        _finding(
                            "ROUNDTRIP_EXAMPLE_MISMATCH",
                            t["text_id"],
                            "Standard CLDF examples.csv row differs from trusted canonical scalars",
                            field="examples.csv",
                        )
                    )

            # Verify exact notice bytes & digests.
            notice_map = {r["relative_path"]: r for r in decoded_tables.get("notices.csv", [])}
            if set(notice_map) != set(trusted_canonical["notices"]):
                rt_findings.append(
                    _finding("ROUNDTRIP_NOTICES_MISMATCH", "notices.csv", "Exported notice inventory differs from trusted input", field="notices")
                )
            for rel, expected_raw in trusted_canonical["notices"].items():
                notice_file = target / rel
                if not notice_file.is_file() or notice_file.read_bytes() != expected_raw:
                    rt_findings.append(
                        _finding("ROUNDTRIP_NOTICE_TAMPERED", rel, f"Exported notice {rel} bytes differ from trusted input", field="notices")
                    )

            bib_sources = pycldf.sources.Sources.from_file(target / "sources.bib")
            if {s["source_id"] for s in trusted_tables["sources"]} != set(bib_sources.keys()):
                rt_findings.append(
                    _finding("ROUNDTRIP_SOURCES_BIB_MISMATCH", "sources.bib", "BibTeX keys do not match trusted pack sources", field="sources.bib")
                )
        except Exception as exc:  # noqa: BLE001
            rt_findings.append(_finding("ROUNDTRIP_DECODE_ERROR", str(target.name), str(exc), field="roundtrip"))

    all_findings = sorted(
        cldf_findings + rt_findings,
        key=lambda item: (item["code"], item["entity_id"], item["field"], item["reason"]),
    )
    return {
        "cldf_valid": cldf_valid,
        "roundtrip_ok": cldf_valid and not rt_findings,
        "findings": all_findings,
    }


def _collect_dir_bytes(directory: pathlib.Path) -> dict[str, bytes]:
    return {
        p.relative_to(directory).as_posix(): p.read_bytes()
        for p in sorted(directory.rglob("*"))
        if p.is_file()
    }


def _bundle_sha256(file_bytes: dict[str, bytes]) -> tuple[str, list[dict[str, Any]]]:
    files_meta: list[dict[str, Any]] = []
    h = hashlib.sha256()
    for rel, raw in sorted(file_bytes.items()):
        fsha = _sha256_bytes(raw)
        files_meta.append({"path": rel, "sha256": fsha, "bytes": len(raw)})
        h.update(f"{rel}:{fsha}\n".encode("utf-8"))
    return h.hexdigest(), files_meta


def _commit_staged_dir(staged: pathlib.Path, output: pathlib.Path) -> tuple[str, list[dict[str, Any]]]:
    staged_bytes = _collect_dir_bytes(staged)
    bundle_sha, files_meta = _bundle_sha256(staged_bytes)

    if output.exists():
        if not output.is_dir():
            raise lexicon.LexiconError(f"Output path exists and is not a directory: {output}", code=2)
        existing_bytes = _collect_dir_bytes(output)
        if existing_bytes == staged_bytes:
            return bundle_sha, files_meta
        if existing_bytes:
            raise lexicon.LexiconError(
                f"Existing CLDF output directory {output} has conflicting contents; refusing silent overwrite",
                code=2,
            )
        output.rmdir()

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staged), str(output))
    return bundle_sha, files_meta


def _validate_report_schema(report: dict[str, Any]) -> None:
    schema = json.loads(CLDF_REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=report, schema=schema)


def export_cldf(
    canonical: str | pathlib.Path,
    pack: str,
    output: str | pathlib.Path,
    *,
    check: bool = True,
    report_output: str | pathlib.Path | None = None,
    canonical_validator: Callable[[pathlib.Path, str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Export an eligible canonical lexicon pack to CLDF 1.3 and validate offline."""
    schema_info = verify_cldf_schemas()
    canon_path = pathlib.Path(canonical)
    out_path = pathlib.Path(output)
    rep_path = pathlib.Path(report_output) if report_output is not None else None

    _check_non_overlapping(canon_path, out_path, rep_path)
    trusted = load_trusted_canonical(canon_path, pack, canonical_validator=canonical_validator)

    counts = {table: len(trusted["tables"][table]) for table in CANONICAL_TABLES}
    counts["notices"] = len(trusted["notices"])

    cldf_valid = False
    roundtrip_ok = False
    export_sha256: str | None = None
    files_meta: list[dict[str, Any]] = []
    findings = list(trusted["findings"])

    if trusted["l3_pack_eligible"]:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix=f".{out_path.name}.cldf-stage-", dir=out_path.parent))
        try:
            _render_cldf_bundle(trusted, tmp_dir, schema_info["schema_manifest_sha256"])
            ver = verify_cldf_export(tmp_dir, trusted)
            cldf_valid = ver["cldf_valid"]
            roundtrip_ok = ver["roundtrip_ok"] if check else cldf_valid
            findings.extend(ver["findings"])
            if cldf_valid and (not check or roundtrip_ok):
                export_sha256, files_meta = _commit_staged_dir(tmp_dir, out_path)
        finally:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir, ignore_errors=True)

    findings.sort(key=lambda item: (item["code"], item["entity_id"], item["field"], item["reason"]))
    report = {
        "schema_version": "lexicon-cldf-report-v1",
        "command": "export-cldf",
        "pack": pack,
        "check": bool(check),
        "cldf_version": schema_info["cldf_version"],
        "validator_pins": schema_info["validator_pins"],
        "schema_manifest_sha256": schema_info["schema_manifest_sha256"],
        "dataset_version": trusted["dataset_version"],
        "l2_structural_accepted": trusted["l2_structural_accepted"],
        "l3_pack_eligible": trusted["l3_pack_eligible"] and not findings,
        "runtime_verified": None,
        "cldf_valid": cldf_valid,
        "roundtrip_ok": roundtrip_ok,
        "eligible_assertions": trusted["eligible_assertions"],
        "counts": counts,
        "input_digests": trusted["input_digests"],
        "export_sha256": export_sha256,
        "files": files_meta,
        "findings": findings,
    }
    _validate_report_schema(report)
    if rep_path is not None:
        lexicon.atomic_json(rep_path, report, source_root=lexicon.SOURCE)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="export-cldf",
        description="Export a validated nonempty canonical Tamil lexicon pack to CLDF 1.3.",
    )
    parser.add_argument("--canonical", required=True, help="Path to promoted canonical pack directory.")
    parser.add_argument("--pack", required=True, help=f"Target pack id ({', '.join(SUPPORTED_PACKS)}).")
    parser.add_argument("--output", required=True, help="Target directory for generated CLDF dataset.")
    parser.add_argument("--check", action="store_true", help="Run full pycldf/CSVW offline validation and lossless roundtrip verification.")
    parser.add_argument("--report-output", help="Optional path to write deterministic JSON report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        report = export_cldf(
            canonical=args.canonical,
            pack=args.pack,
            output=args.output,
            check=bool(args.check),
            report_output=args.report_output,
        )
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except lexicon.LexiconError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.code

    if args.report_output is None:
        print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    if not report["l3_pack_eligible"] or not report["cldf_valid"] or (args.check and not report["roundtrip_ok"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
