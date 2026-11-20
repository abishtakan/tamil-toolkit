"""Deterministic intake bookkeeping; no linguistic or source approval."""

from __future__ import annotations

from contextlib import ExitStack
import hashlib
import heapq
import itertools
import json
import os
from pathlib import Path
import tempfile
import tomllib

from tools.lexicon import (
    LexiconError, NAMESPACE, ROOT, SOURCE, _checked_files_with_digests, allocate_id,
    atomic_json, digest, json_text, data_json, native_batch_canonical_json_sha256,
    native_batch_data_json, safe_output, source_rows, table_rows,
)


def _stage_claim_revision(
    assertion_id: str,
    subject_kind: str,
    subject_id: str,
    property_code: str,
    value_json: str,
    status_val,
    conf_val,
) -> str:
    payload = (
        '{"algorithm_reference":null,"ambiguity_state":"unknown","assertion_id":'
        + json_text(assertion_id)
        + ',"convention_reference":null,"imported_confidence_json":'
        + ("null" if conf_val is None else json_text(conf_val))
        + ',"imported_status_json":'
        + ("null" if status_val is None else json_text(status_val))
        + ',"origin":"verbatim_source","property_code":'
        + json_text(property_code)
        + ',"source_fidelity_state":"unknown","subject_id":'
        + json_text(subject_id)
        + ',"subject_kind":'
        + json_text(subject_kind)
        + ',"value_json":'
        + json_text(value_json)
        + ',"value_state":"known"}'
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def stage(inventory_path, workspace):
    from tools.lexicon_tables import TableRowWriter, fields, write_rows

    inventory_path, workspace = Path(inventory_path).resolve(), safe_output(workspace)
    manifest = json.loads((inventory_path / "manifest.json").read_text(encoding="utf-8"))
    source = Path(manifest["source_root"])
    workspace = safe_output(workspace, source)
    if workspace == inventory_path or workspace.is_relative_to(inventory_path) or inventory_path.is_relative_to(workspace):
        raise LexiconError("workspace overlaps inventory")
    _, paths, verified = _checked_files_with_digests(source)
    expected = {item["file"]: item for item in manifest["files"]}
    if set(expected) != {path.name for path in paths}:
        raise LexiconError("inventory source file set mismatch")
    for path in paths:
        item = expected[path.name]
        size, checksum = verified[path.name] if path.name in verified else (path.stat().st_size, digest(path))
        if (checksum != item["sha256"] or size != item["bytes"]
                or item["snapshot_id"] != allocate_id("snap", NAMESPACE, item["sha256"])):
            raise LexiconError("inventory source hash mismatch")
    config_path = workspace / "dataset.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    if config and (config.get("schema_version") != 1 or config.get("text_codec") != "json-string-utf8-v1"):
        raise LexiconError("unsupported dataset schema or codec")
    namespace = config.get("id_namespace", str(NAMESPACE))
    if namespace == str(NAMESPACE):
        namespace = NAMESPACE
    dataset_id = config.get("dataset_id", "tamil-lexicon-intake")
    workspace.parent.mkdir(parents=True, exist_ok=True)
    names = ["snapshots", "sources", "identities", "source_records", "dispositions", "record_targets", "assertions", "evidence", "decisions", "findings"]
    existing = {}
    if (workspace / "identities.csv").exists():
        from tools.lexicon_tables import read_rows
        for row in read_rows(workspace / "identities.csv"):
            prefix = {"entry": "ent", "form": "frm", "sense": "sen", "text": "txt", "relation": "rel"}.get(row["kind"], row["kind"])
            key = (prefix, row["allocation_key"])
            if key in existing or row["entity_id"] != allocate_id(prefix, namespace, row["allocation_key"]):
                raise LexiconError("identity allocation conflict")
            existing[key] = row
    with tempfile.TemporaryDirectory(dir=workspace.parent, prefix=".lexicon-stage-") as temporary:
        temporary = Path(temporary)
        with ExitStack() as stack:
            writers = {
                name: stack.enter_context(TableRowWriter(temporary / (name + ".csv"), name, source_root=source))
                for name in names
            }
            emit_identities = writers["identities"].write_row
            emit_sources = writers["sources"].write_row
            emit_snapshots = writers["snapshots"].write_row
            emit_records = writers["source_records"].write_row
            emit_assertions = writers["assertions"].write_row
            emit_evidence = writers["evidence"].write_row
            emit_dispositions = writers["dispositions"].write_row

            allocated, leads, primary = {}, {}, set()
            kind_names = {"ent": "entry", "sen": "sense", "rel": "relation"}
            empty_finding_sha = hashlib.sha256(b"[]").hexdigest()

            def identity(kind, key):
                pair = (kind, key)
                entity_id = allocated.get(pair)
                if entity_id is None:
                    entity_id = allocate_id(kind, namespace, key)
                    allocated[pair] = entity_id
                    row = existing.get(
                        pair,
                        {
                            "entity_id": entity_id,
                            "kind": kind_names[kind],
                            "allocation_key": key,
                            "lifecycle": "active",
                            "identity_decision_id": None,
                        },
                    )
                    emit_identities(row)
                return entity_id

            def lead(label, snapshot):
                key = (label, snapshot)
                sid = leads.get(key)
                if sid is None:
                    sid = allocate_id("src", namespace, json_text(key))
                    leads[key] = sid
                    emit_sources({
                        "source_id": sid, "label_json": label, "publication_json": None, "url_json": None,
                        "edition_json": None, "locator_json": None, "snapshot_id": snapshot,
                        "retrieval_date_state": "unknown", "retrieval_date_json": None,
                        "extraction_method": "owner_reported_python", "extraction_version": "unknown",
                        "evidence_verification_state": "unknown", "reuse_basis_json": None, "reuse_state": "unknown",
                        "attribution_text_json": None, "attribution_reference_json": None,
                    })
                return sid

            # Primary first, master later: its legacy keys resolve to these identities.
            paths.sort(key=lambda path: (path.name == "unified_master_30col.csv", path.name))
            for path in paths:
                meta = expected[path.name]
                snapshot, checksum = meta["snapshot_id"], meta["sha256"]
                is_csv = path.suffix == ".csv"
                emit_snapshots({
                    "snapshot_id": snapshot, "dataset_id": dataset_id, "relative_path": path.name,
                    "byte_length": meta["bytes"], "sha256": checksum,
                    "media_type": "text/csv" if is_csv else "application/octet-stream",
                    "logical_row_count": meta["rows"] + 1 if is_csv else None,
                })
                source_id = lead("unrecovered:" + path.stem, snapshot)
                if not is_csv:
                    continue
                seen = set()
                actual_count = 0
                is_primary_lemmas = path.name == "primary_lemmas.csv"
                is_master_table = path.name == "unified_master_30col.csv"
                is_primary_or_master = is_primary_lemmas or is_master_table
                prop_code = "imported_master_fields" if path.name.startswith("unified_master") else "unparsed_source_record"
                if not is_primary_or_master:
                    file_kind = (
                        "sen" if path.name == "primary_meanings.csv"
                        else "rel" if path.name == "primary_relationships.csv"
                        else "ent"
                    )
                    key_prefix = path.stem + ":legacy:"
                else:
                    file_kind = "ent"
                    key_prefix = "primary:word:"
                subject_kind_name = kind_names[file_kind]

                _STAGE_BATCH = 4096
                rec_buf = []
                row_buf = []
                meta_buf = []

                def _flush_stage_batch():
                    if not meta_buf:
                        return
                    vjson_list = native_batch_data_json(row_buf)
                    rev_inputs = []
                    ast_buf = []
                    ev_buf = []
                    disp_buf = []
                    for (rec, ordinal, row_hash, subject, aid, status_val, conf_val), vjson in zip(meta_buf, vjson_list):
                        rev_inputs.append({
                            "algorithm_reference": None,
                            "ambiguity_state": "unknown",
                            "assertion_id": aid,
                            "convention_reference": None,
                            "imported_confidence_json": conf_val,
                            "imported_status_json": status_val,
                            "origin": "verbatim_source",
                            "property_code": prop_code,
                            "source_fidelity_state": "unknown",
                            "subject_id": subject,
                            "subject_kind": subject_kind_name,
                            "value_json": vjson,
                            "value_state": "known",
                        })
                        ast_buf.append({
                            "assertion_id": aid,
                            "subject_kind": subject_kind_name,
                            "subject_id": subject,
                            "property_code": prop_code,
                            "value_state": "known",
                            "value_json": vjson,
                            "origin": "verbatim_source",
                            "source_fidelity_state": "unknown",
                            "ambiguity_state": "unknown",
                            "algorithm_reference": None,
                            "convention_reference": None,
                            "imported_status_json": status_val,
                            "imported_confidence_json": conf_val,
                            "claim_revision_sha256": "",
                        })
                        ev_buf.append({
                            "assertion_id": aid, "source_id": source_id, "source_record_id": rec,
                            "locator_json": f"{snapshot}:record={ordinal}", "evidence_role": "transcribes",
                            "extraction_version": "lexicon-host-v1", "extraction_sha256": row_hash,
                        })
                        disp_buf.append({
                            "record_id": rec, "disposition": "quarantined", "structural_state": "validated",
                            "reason_code": "SOURCE_AND_REUSE_UNVERIFIED",
                            "note_json": "Unparsed imported claims retained; no approved mapping.",
                            "finding_set_sha256": empty_finding_sha, "method": "lexicon-host", "method_version": "1",
                        })
                    for assertion_row, rev_sha in zip(ast_buf, native_batch_canonical_json_sha256(rev_inputs)):
                        assertion_row["claim_revision_sha256"] = rev_sha
                    writers["source_records"].write_rows_batch(rec_buf)
                    writers["assertions"].write_rows_batch(ast_buf)
                    writers["evidence"].write_rows_batch(ev_buf)
                    writers["dispositions"].write_rows_batch(disp_buf)
                    rec_buf.clear()
                    row_buf.clear()
                    meta_buf.clear()

                for ordinal, start, end, row_hash, row in source_rows(path):
                    actual_count += 1
                    legacy = next(iter(row.values()))
                    if not legacy or legacy in seen:
                        raise LexiconError(f"missing or conflicting legacy key: {path.name}:{ordinal}")
                    seen.add(legacy)
                    rec = allocate_id("rec", NAMESPACE, f"{checksum}:{ordinal}:{row_hash}")
                    rec_buf.append({
                        "record_id": rec, "snapshot_id": snapshot, "ordinal": ordinal,
                        "physical_line_start": start, "physical_line_end": end,
                        "legacy_key_json": legacy, "raw_row_sha256": row_hash,
                    })
                    if is_primary_lemmas:
                        primary.add(legacy)
                    elif is_master_table and legacy not in primary:
                        raise LexiconError("master entry lacks primary identity")
                    subject = identity(file_kind, key_prefix + legacy)
                    # A raw component is explicitly unparsed. Preserve every column,
                    # especially additional master annotations, without asserting truth.
                    aid = allocate_id("ast", namespace, rec + ":unparsed")
                    status_val = row.get("status")
                    conf_val = row.get("confidence")
                    row_buf.append(row)
                    meta_buf.append((rec, ordinal, row_hash, subject, aid, status_val, conf_val))
                    if "source_code" in row and row["source_code"]:
                        lead(row["source_code"], snapshot)
                    if "literary_source" in row and row["literary_source"]:
                        lead(row["literary_source"], snapshot)
                    if len(meta_buf) >= _STAGE_BATCH:
                        _flush_stage_batch()
                _flush_stage_batch()
                if actual_count != meta["rows"]:
                    raise LexiconError("inventory source row count mismatch")
            for key, row in existing.items():
                if key not in allocated:
                    emit_identities(row)
            counts = {name: writer.count for name, writer in writers.items()}
            for writer in writers.values():
                writer.finish()
        report = {"schema_version": 1, "command": "stage", "mode": "intake", "dataset_version": config.get("dataset_version", "1"),
            "input_sha256": digest(inventory_path / "manifest.json"), "counts": counts,
            "file_dispositions": [{"snapshot_id": item["snapshot_id"], "disposition": "quarantined", "reason_code": "UNREPRODUCIBLE_DERIVED_ARTIFACT"}
                for item in manifest["files"] if not item["file"].endswith(".csv")],
            "l2_structural_accepted": False, "l3_pack_eligible": False, "runtime_verified": None,
            "eligible_assertions": 0, "findings": []}
        atomic_json(temporary / "stage-report.json", report, source)
        # Preserve append-only editorial additions. Same-ID claim changes are
        # conflicts, while explicitly edited source/disposition metadata stays
        # owned by the editorial workflow rather than being reset by reimport.
        from tools.lexicon_tables import read_rows
        for name in names:
            destination = workspace / (name + ".csv")
            generated = temporary / destination.name
            if not destination.exists() or digest(destination) == digest(generated):
                continue
            first = fields(name)[0]
            def merged(name=name, destination=destination, generated=generated, first=first):
                def tagged(path, old):
                    for row in read_rows(path, name):
                        key = (row[first],)
                        if name == "evidence":
                            key += (row["source_id"], row["source_record_id"] or "", data_json(row["locator_json"]), row["evidence_role"])
                        elif name == "record_targets":
                            key += (row["entity_id"], row["target_role"])
                        yield key, old, row
                for _, group in itertools.groupby(heapq.merge(tagged(destination, True), tagged(generated, False), key=lambda r: r[0]), key=lambda r: r[0]):
                    values = list(group)
                    if len(values) > 2 or len(values) == 2 and values[0][1] == values[1][1]:
                        raise LexiconError("duplicate editorial identity")
                    prior = next((v[2] for v in values if v[1]), None)
                    fresh = next((v[2] for v in values if not v[1]), None)
                    if prior is not None and fresh is not None and prior != fresh and name not in {"sources", "dispositions", "identities"}:
                        raise LexiconError(f"existing editorial content conflicts: {name}")
                    yield prior if prior is not None else fresh
            replacement = temporary / (name + ".merged.csv")
            write_rows(replacement, name, merged(), source_root=source)
            os.replace(replacement, generated)
        # Inputs have all been checked before replacing any destination.
        workspace.mkdir(exist_ok=True)
        for path in list(temporary.glob("*.csv")) + [temporary / "stage-report.json"]:
            if not (workspace / path.name).exists() or digest(path) != digest(workspace / path.name):
                os.replace(path, workspace / path.name)
        return report
