"""Lossless, unapproved editorial projection of explicitly selected records."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tomllib

from tools.lexicon import LexiconError, NAMESPACE, SOURCE, allocate_id, digest, json_text, safe_output, source_rows, native_inspect


def _addition_key(name, row):
    if name == "evidence":
        return (
            row["assertion_id"],
            row["source_id"],
            row["source_record_id"] or "",
            row["locator_json"],
            row["evidence_role"],
        )
    if name == "identities":
        return row["entity_id"]
    if name == "findings":
        return row["finding_id"]
    return row["assertion_id"]


def project(workspace, selected_record_ids, source=SOURCE):
    from tools.lexicon_review import claim_revision, unicode_findings
    from tools.lexicon_tables import read_rows, write_rows

    source = Path(source).resolve()
    workspace = safe_output(workspace, source)
    config_path = workspace / "dataset.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    if config and (config.get("schema_version") != 1 or config.get("text_codec") != "json-string-utf8-v1"):
        raise LexiconError("unsupported dataset schema or codec")
    namespace = config.get("id_namespace", str(NAMESPACE))
    selected = set(selected_record_ids)
    snapshots = {r["relative_path"]: r for r in read_rows(workspace / "snapshots.csv")}
    rows, records = {}, {}
    for name, snapshot in snapshots.items():
        path = source / name
        if digest(path) != snapshot["sha256"]:
            raise LexiconError("source hash mismatch before projection")
        if path.suffix != ".csv":
            continue
        for ordinal, _, _, checksum, values in source_rows(path):
            rec = allocate_id("rec", NAMESPACE, f"{snapshot['sha256']}:{ordinal}:{checksum}")
            if rec in selected:
                rows[rec] = (name, values)
                records[rec] = checksum
    if selected - set(rows):
        raise LexiconError("selection references unknown source records")
    unparsed_ids = {rec: allocate_id("ast", namespace, rec + ":unparsed") for rec in selected}
    original_evidence = {}
    for r in read_rows(workspace / "evidence.csv"):
        srid = r["source_record_id"]
        if srid in selected and r["assertion_id"] == unparsed_ids[srid]:
            if srid not in original_evidence or r["evidence_role"] == "transcribes":
                original_evidence[srid] = r
    tables = {name: [] for name in ["entries", "forms", "senses", "texts", "relations", "scopes", "labels", "changes", "successors", "unicode_exceptions", "pack_members"]}
    additions = {"assertions": [], "evidence": [], "identities": [], "findings": []}
    primary_ids = set()
    label_rows = {}

    def queue(rec, aid, issue, severity="warning", positions=()):
        additions["findings"].append({"finding_id": allocate_id("fnd", namespace, aid + ":" + issue),
            "record_id": rec, "assertion_id": aid, "issue_code": issue, "severity": severity,
            "scalar_positions": list(positions), "status": "open", "resolution_reason_json": None})

    def entity(kind, key):
        prefix = {"entry": "ent", "form": "frm", "sense": "sen", "text": "txt", "relation": "rel"}[kind]
        result = allocate_id(prefix, namespace, key)
        additions["identities"].append({"entity_id": result, "kind": kind, "allocation_key": key, "lifecycle": "active", "identity_decision_id": None})
        return result

    def claim(rec, kind, subject, field, value, empty_unknown=True):
        aid = allocate_id("ast", namespace, f"{rec}:field:{field}")
        assertion = {"assertion_id": aid, "subject_kind": kind, "subject_id": subject, "property_code": field,
            "value_state": "unknown" if empty_unknown and value == "" else "known", "value_json": None if empty_unknown and value == "" else value,
            "origin": "verbatim_source", "source_fidelity_state": "unknown", "ambiguity_state": "unknown",
            "algorithm_reference": None, "convention_reference": None, "imported_status_json": rows[rec][1].get("status"),
            "imported_confidence_json": rows[rec][1].get("confidence"), "claim_revision_sha256": "0" * 64}
        assertion["claim_revision_sha256"] = claim_revision(assertion)
        additions["assertions"].append(assertion)
        category = {"sol_vagai":"grammar_system", "grammatical_subclass":"grammar_system", "verb_class":"grammar_system",
            "domain":"domain", "domain_field":"domain", "register":"register", "region_dialect":"region",
            "period_era":"period", "social_usage":"social_usage"}.get(field)
        if category and value:
            code = allocate_id("lbl", namespace, category + ":" + value)
            label_rows.setdefault(code, {"registry_id":"imported_categories", "registry_version":"1", "code":code,
                "category":category,"display_label_json":value,"definition_json":"Unreviewed imported category; no scope or equivalence inferred.",
                "evidence_reference":aid,"parent_code":None})
        evidence = dict(original_evidence[rec], assertion_id=aid, locator_json=original_evidence[rec]["locator_json"] + ":field=" + field)
        additions["evidence"].append(evidence)
        if field in {"pronunciation_ipa", "root_word", "verb_class", "grammatical_subclass", "sol_vagai", "corpus_frequency_tier", "sandhi_behavior", "matra_count", "grapheme_count"} and value:
            queue(rec, aid, "IMPORTED_ANNOTATION_REQUIRES_REVIEW")
        if isinstance(value, str) and value:
            for finding in unicode_findings(assertion):
                issue = finding.get("issue_code", finding.get("code", "UNICODE_REVIEW"))
                additions["findings"].append({"finding_id": allocate_id("fnd", namespace, aid + ":" + issue + ":" + json_text(finding)),
                    "record_id": rec, "assertion_id": aid, "issue_code": issue, "severity": finding.get("severity", "warning"),
                    "scalar_positions": finding.get("scalar_positions", []), "status": "open", "resolution_reason_json": None})
        return aid

    for rec, (name, row) in sorted(rows.items()):
        if name in {"primary_meanings.csv", "primary_relationships.csv", "unified_master_30col.csv"}:
            continue
        legacy = next(iter(row.values()))
        key = "primary:word:" + legacy if name == "primary_lemmas.csv" else Path(name).stem + ":legacy:" + legacy
        entry = entity("entry", key)
        if name == "primary_lemmas.csv":
            primary_ids.add(legacy)
        field = next((f for f in ["headword_ta", "term_ta", "phrase_ta", "name_ta", "tamil_name", "transliterated_ta"] if f in row), None)
        form_id = None
        if field and row[field]:
            form_id = entity("form", key + ":canonical-written")
            tables["forms"].append({"form_id": form_id, "entry_id": entry, "representation": "written", "role": "canonical",
                "text_assertion_id": claim(rec, "form", form_id, "headword", row[field]), "convention_assertion_id": None})
        pos = claim(rec, "entry", entry, "part_of_speech", row.get("part_of_speech", ""))
        for field in ["transliteration", "pronunciation_ipa"]:
            if row.get(field):
                fid = entity("form", key + ":" + field)
                tables["forms"].append({"form_id": fid, "entry_id": entry, "representation": "ipa" if field == "pronunciation_ipa" else "romanization",
                    "role": "variant", "text_assertion_id": claim(rec, "form", fid, field, row[field]), "convention_assertion_id": None})
        tables["entries"].append({"entry_id": entry, "language_id": "tam", "variety_id": None, "canonical_form_id": form_id,
            "pos_assertion_id": pos, "structural_kind": "proposed_import", "revision": hashlib.sha256(json_text(row).encode()).hexdigest()})
        for dimension in ["region", "register", "domain", "social_usage", "period", "grammar_system"]:
            tables["scopes"].append({"subject_kind": "entry", "subject_id": entry, "dimension": dimension, "state": "unknown",
                "label_code": None, "supporting_assertion_id": None, "decision_id": None})
        for field in ["root_word", "verb_class", "sol_vagai", "grammatical_subclass", "region_dialect", "register", "domain", "domain_field", "period_era", "social_usage", "language_variety"]:
            if field in row:
                claim(rec, "entry", entry, field, row[field])
        # Secondary datasets get a single unsplit source-component group.
        if name.startswith("secondary_"):
            sid = entity("sense", key + ":source-component")
            tables["senses"].append({"sense_id": sid, "entry_id": entry, "display_order": 1, "parent_sense_id": None})
            for field, language in [("meaning_ta", "tam"), ("meaning_en", "eng"), ("english_gloss", "eng"), ("english_term", "eng"), ("definition_ta", "tam"), ("definition_en", "eng")]:
                if row.get(field):
                    tid = entity("text", key + ":" + field)
                    tables["texts"].append({"text_id": tid, "owner_kind": "sense", "owner_id": sid, "component": "unparsed", "language_id": language,
                        "text_assertion_id": claim(rec, "text", tid, field, row[field]), "paired_translation_id": None, "cited_source_locator_json": None})
    for rec, (name, row) in sorted(rows.items()):
        if name == "primary_meanings.csv" and row["word_id"] in primary_ids:
            sid = entity("sense", "primary_meanings:legacy:" + row["meaning_id"])
            entry = allocate_id("ent", namespace, "primary:word:" + row["word_id"])
            order = int(row.get("sense_number", "1")) if row.get("sense_number", "1").isdigit() else 1
            tables["senses"].append({"sense_id": sid, "entry_id": entry, "display_order": max(1, order), "parent_sense_id": None})
            for field, language in [("meaning_ta", "tam"), ("meaning_en", "eng"), ("definition_ta", "tam"), ("definition_en", "eng")]:
                if row.get(field):
                    tid = entity("text", "primary_meanings:legacy:" + row["meaning_id"] + ":" + field)
                    tables["texts"].append({"text_id": tid, "owner_kind": "sense", "owner_id": sid, "component": "unparsed", "language_id": language,
                        "text_assertion_id": claim(rec, "text", tid, field, row[field]), "paired_translation_id": None, "cited_source_locator_json": None})
        elif name == "primary_relationships.csv" and {row["source_word_id"], row["target_word_id"]} <= primary_ids:
            rid = entity("relation", "primary_relationships:legacy:" + row["relationship_id"])
            tables["relations"].append({"relation_id": rid, "source_kind": "entry", "source_id": allocate_id("ent", namespace, "primary:word:" + row["source_word_id"]),
                "target_kind": "entry", "target_id": allocate_id("ent", namespace, "primary:word:" + row["target_word_id"]),
                "relation_code_assertion_id": claim(rec, "relation", rid, "relation_code", row["relation_code"]),
                "directionality": row["directionality"], "inverse_relation_id": None})
        elif name == "unified_master_30col.csv" and row["word_id"] in primary_ids:
            entry = allocate_id("ent", namespace, "primary:word:" + row["word_id"])
            for field in ["root_word", "verb_class", "corpus_frequency_tier", "sandhi_behavior", "matra_count", "grapheme_count", "example_sentence_ta", "etymology_type", "syllable_structure", "phonetic_weight"]:
                if field not in row:
                    continue
                aid = claim(rec, "entry", entry, field, row[field])
                if field == "grapheme_count" and row[field]:
                    try:
                        supplied = int(row[field])
                    except ValueError:
                        queue(rec, aid, "INVALID_IMPORTED_COUNT", "error")
                    else:
                        if supplied != native_inspect(row["headword_ta"])["ezhuthu_count"]:
                            queue(rec, aid, "RUST_COUNT_CONVENTION_DISAGREEMENT")
    tables["labels"] = list(label_rows.values())
    # All input claims remain intact; only explicit selected pending components are added.
    with tempfile.TemporaryDirectory(dir=workspace.parent, prefix=".lexicon-project-") as temporary:
        temporary = Path(temporary)
        for name, additions_rows in additions.items():
            new = {}
            for row in additions_rows:
                identity_key = _addition_key(name, row)
                if identity_key in new and new[identity_key] != row:
                    raise LexiconError("conflicting proposed rows")
                new[identity_key] = row
            def merged(name=name, new=new):
                for old in read_rows(workspace / (name + ".csv")):
                    identity_key = _addition_key(name, old)
                    if identity_key in new:
                        if old != new[identity_key]:
                            raise LexiconError("existing editorial claim conflicts with projection")
                        del new[identity_key]
                    yield old
                yield from new.values()
            write_rows(temporary / (name + ".csv"), name, merged(), source_root=source)
        for name, values in tables.items():
            write_rows(temporary / (name + ".csv"), name, values, source_root=source)
            existing = workspace / (name + ".csv")
            if existing.exists() and digest(existing) != digest(temporary / existing.name) and not (name == "labels" and not any(read_rows(existing))):
                raise LexiconError("existing editorial structure conflicts with projection")
        finding_sets = defaultdict(list)
        for row in read_rows(temporary / "findings.csv"):
            if row["record_id"]:
                finding_sets[row["record_id"]].append(row["finding_id"])
        def dispositions():
            for row in read_rows(workspace / "dispositions.csv"):
                if row["record_id"] in selected:
                    row["finding_set_sha256"] = hashlib.sha256(json_text(sorted(finding_sets[row["record_id"]])).encode("ascii")).hexdigest()
                yield row
        write_rows(temporary / "dispositions.csv", "dispositions", dispositions(), source_root=source)
        for path in temporary.glob("*.csv"):
            os.replace(path, workspace / path.name)
    return {"schema_version": 1, "command": "curate", "selected_records": len(selected), "entries": len(tables["entries"]),
        "senses": len(tables["senses"]), "eligible_assertions": 0, "l2_structural_accepted": False, "l3_pack_eligible": False, "runtime_verified": None}
