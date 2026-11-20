"""Differential parity, offline registry, roundtrip, and bounded speed checks for lexicon schema validation."""

from __future__ import annotations

from decimal import Decimal
from enum import IntEnum
from pathlib import Path
import time
import urllib.request

import jsonschema_rs
import pytest

from tools.lexicon import LexiconError, ROOT
from tools.lexicon_tables import (
    _check_no_surrogates,
    _format_validation_error,
    _table_registry,
    read_rows,
    validate_row,
    write_rows,
)

ZERO_SHA = "0" * 64
ONE_SHA = "1" * 64
REVIEWED_DIR = ROOT / "data/curation/wiktionary-core-reviewed"


class _SampleIntEnum(IntEnum):
    ONE = 1


class _CustomDict(dict):
    pass


def _valid_rows_by_table() -> dict[str, dict]:
    return {
        "snapshots": {
            "snapshot_id": "snap_1",
            "dataset_id": "ds_1",
            "relative_path": "intake/source.csv",
            "byte_length": 42,
            "sha256": ZERO_SHA,
            "media_type": "text/csv",
            "logical_row_count": 2,
        },
        "sources": {
            "source_id": "src_1",
            "label_json": "Primary Dictionary",
            "publication_json": "University Press",
            "url_json": None,
            "edition_json": "1",
            "locator_json": "p. 1",
            "snapshot_id": "snap_1",
            "retrieval_date_state": "known",
            "retrieval_date_json": "2024-02-29",
            "extraction_method": "csv-intake",
            "extraction_version": "v1",
            "evidence_verification_state": "verified",
            "reuse_basis_json": "CC-BY-SA-4.0",
            "reuse_state": "permitted",
            "attribution_text_json": "Attribution",
            "attribution_reference_json": "NOTICE.md",
        },
        "identities": {
            "entity_id": "ent_1",
            "kind": "entry",
            "allocation_key": "entry:1",
            "lifecycle": "active",
            "identity_decision_id": None,
        },
        "source_records": {
            "record_id": "rec_1",
            "snapshot_id": "snap_1",
            "ordinal": 2,
            "physical_line_start": 2,
            "physical_line_end": 2,
            "legacy_key_json": "L001",
            "raw_row_sha256": ZERO_SHA,
        },
        "dispositions": {
            "record_id": "rec_1",
            "disposition": "mapped",
            "structural_state": "validated",
            "reason_code": "MAPPED_OK",
            "note_json": "mapped cleanly",
            "finding_set_sha256": ZERO_SHA,
            "method": "ingest",
            "method_version": "v1",
        },
        "record_targets": {
            "record_id": "rec_1",
            "entity_id": "ent_1",
            "target_role": "primary_entry",
        },
        "entries": {
            "entry_id": "ent_1",
            "language_id": "tam",
            "variety_id": None,
            "canonical_form_id": "frm_1",
            "pos_assertion_id": "asr_pos",
            "structural_kind": "lexeme",
            "revision": ZERO_SHA,
        },
        "forms": {
            "form_id": "frm_1",
            "entry_id": "ent_1",
            "representation": "written",
            "role": "canonical",
            "text_assertion_id": "asr_hw",
            "convention_assertion_id": None,
        },
        "senses": {
            "sense_id": "sns_1",
            "entry_id": "ent_1",
            "display_order": 1,
            "parent_sense_id": None,
        },
        "texts": {
            "text_id": "txt_1",
            "owner_kind": "sense",
            "owner_id": "sns_1",
            "component": "definition",
            "language_id": "eng",
            "text_assertion_id": "asr_def",
            "paired_translation_id": None,
            "cited_source_locator_json": None,
        },
        "relations": {
            "relation_id": "rel_1",
            "source_kind": "entry",
            "source_id": "ent_1",
            "target_kind": "entry",
            "target_id": "ent_2",
            "relation_code_assertion_id": "asr_rel",
            "directionality": "directed",
            "inverse_relation_id": None,
        },
        "assertions": {
            "assertion_id": "asr_1",
            "subject_kind": "form",
            "subject_id": "frm_1",
            "property_code": "headword",
            "value_state": "known",
            "value_json": "\u0b85\u0bae\u0bcd\u0bae\u0bbe",
            "origin": "verbatim_source",
            "source_fidelity_state": "verified",
            "ambiguity_state": "unambiguous",
            "algorithm_reference": None,
            "convention_reference": None,
            "imported_status_json": None,
            "imported_confidence_json": 1.0,
            "claim_revision_sha256": ZERO_SHA,
        },
        "evidence": {
            "assertion_id": "asr_1",
            "source_id": "src_1",
            "source_record_id": "rec_1",
            "locator_json": "line 2",
            "evidence_role": "supports",
            "extraction_version": "v1",
            "extraction_sha256": ONE_SHA,
        },
        "decisions": {
            "decision_id": "dec_1",
            "assertion_id": "asr_1",
            "assertion_revision_sha256": ZERO_SHA,
            "evidence_bundle_sha256": ONE_SHA,
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "rev_1",
            "method_version": None,
            "decision_date": "2026-11-15",
            "note_json": "",
            "predecessor_decision_id": None,
        },
        "changes": {
            "change_id": "chg_1",
            "subject_id": "ent_1",
            "old_assertion_id": None,
            "new_assertion_id": "asr_1",
            "reason_json": "initial claim",
            "evidence_reference": "src_1",
            "decision_id": "dec_1",
            "inverse_change_id": None,
        },
        "successors": {
            "retired_id": "ent_0",
            "successor_id": "ent_1",
            "role": "merge",
            "identity_decision_id": "dec_1",
        },
        "findings": {
            "finding_id": "fnd_1",
            "record_id": "rec_1",
            "assertion_id": None,
            "issue_code": "joiner_present",
            "severity": "info",
            "scalar_positions": [0, 3],
            "status": "open",
            "resolution_reason_json": None,
        },
        "unicode_exceptions": {
            "assertion_id": "asr_1",
            "claim_revision_sha256": ZERO_SHA,
            "value_sha256": ONE_SHA,
            "kind": "intentional_control",
            "scalar_sequence": [0x0B95, 0x200D, 0x0BCD],
            "scalar_position": 0,
            "reason_json": "reviewed joiner",
            "decision_id": "dec_1",
        },
        "labels": {
            "registry_id": "reg_scope",
            "registry_version": "v1",
            "code": "LK-JAFFNA",
            "category": "region",
            "display_label_json": "Jaffna",
            "definition_json": "Jaffna Tamil variety",
            "evidence_reference": "src_1",
            "parent_code": "LK",
        },
        "scopes": {
            "subject_kind": "entry",
            "subject_id": "ent_1",
            "dimension": "region",
            "state": "attested",
            "label_code": "LK-JAFFNA",
            "supporting_assertion_id": "asr_1",
            "decision_id": "dec_1",
        },
        "pack_members": {
            "pack_id": "core",
            "entry_id": "ent_1",
            "included_revision": ZERO_SHA,
            "relation_inclusion_policy": None,
        },
    }


def _assert_matches_reference(table: str, row: dict) -> None:
    meta = _table_registry()[table]
    expected_valid = meta.validator.is_valid(row)
    if expected_valid:
        validate_row(table, row)
        if _check_no_surrogates(row, table):
            assert meta.fast_validator.is_valid(row) is True
    else:
        expected_msg = f"{table} schema error at {_format_validation_error(meta.validator, row)}"
        with pytest.raises(LexiconError) as exc_info:
            validate_row(table, row)
        assert str(exc_info.value) == expected_msg


def test_differential_valid_rows_all_21_tables():
    registry = _table_registry()
    valid_rows = _valid_rows_by_table()
    assert len(registry) == 21
    assert set(valid_rows) == set(registry)

    for table, row in valid_rows.items():
        meta = registry[table]
        assert isinstance(meta.fast_validator, jsonschema_rs.Draft202012Validator)
        assert meta.validator.is_valid(row) is True
        assert meta.fast_validator.is_valid(row) is True
        validate_row(table, row)


def test_differential_mutations_all_21_tables_and_json_types():
    valid_rows = _valid_rows_by_table()

    # Universal per-table structural mutations: unknown key and missing first required key.
    for table, base in valid_rows.items():
        _assert_matches_reference(table, {**base, "__unexpected_col": "x"})
        first_key = next(iter(base))
        missing = {k: v for k, v in base.items() if k != first_key}
        _assert_matches_reference(table, missing)

    # Targeted type, value, pattern, format, and conditional mutations.
    cases: list[tuple[str, dict]] = [
        # null / bool / int / float / large ints
        ("snapshots", {**valid_rows["snapshots"], "byte_length": -1}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": True}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": False}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": 1.0}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": 1.5}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": 2**63}),
        ("snapshots", {**valid_rows["snapshots"], "byte_length": 10**30}),
        ("snapshots", {**valid_rows["snapshots"], "logical_row_count": 0}),
        ("snapshots", {**valid_rows["snapshots"], "media_type": "application/octet-stream", "logical_row_count": None}),
        ("snapshots", {**valid_rows["snapshots"], "relative_path": "../escape.csv"}),
        ("snapshots", {**valid_rows["snapshots"], "relative_path": "a/b.csv\n"}),
        ("sources", {**valid_rows["sources"], "retrieval_date_state": "unknown", "retrieval_date_json": None}),
        ("sources", {**valid_rows["sources"], "retrieval_date_state": "unknown", "retrieval_date_json": "2024-02-29"}),
        ("sources", {**valid_rows["sources"], "retrieval_date_state": "known", "retrieval_date_json": None}),
        ("sources", {**valid_rows["sources"], "retrieval_date_json": "2025-02-29"}),
        ("identities", {**valid_rows["identities"], "lifecycle": "merged", "identity_decision_id": None}),
        ("identities", {**valid_rows["identities"], "lifecycle": "merged", "identity_decision_id": "dec_1"}),
        ("source_records", {**valid_rows["source_records"], "ordinal": 1}),
        ("source_records", {**valid_rows["source_records"], "legacy_key_json": None}),
        ("source_records", {**valid_rows["source_records"], "legacy_key_json": True}),
        ("source_records", {**valid_rows["source_records"], "legacy_key_json": 10**40}),
        ("source_records", {**valid_rows["source_records"], "legacy_key_json": {"nested": "disallowed"}}),
        ("dispositions", {**valid_rows["dispositions"], "disposition": "invalid"}),
        ("record_targets", {**valid_rows["record_targets"], "target_role": ""}),
        ("entries", {**valid_rows["entries"], "entry_id": ""}),
        ("entries", {**valid_rows["entries"], "entry_id": "1bad"}),
        ("entries", {**valid_rows["entries"], "entry_id": "ent_1\n"}),
        ("entries", {**valid_rows["entries"], "revision": ZERO_SHA + "\n"}),
        ("entries", {**valid_rows["entries"], "revision": "g" * 64}),
        ("forms", {**valid_rows["forms"], "representation": "spoken"}),
        ("senses", {**valid_rows["senses"], "display_order": 0}),
        ("senses", {**valid_rows["senses"], "display_order": 2**64}),
        ("texts", {**valid_rows["texts"], "cited_source_locator_json": ""}),
        ("relations", {**valid_rows["relations"], "directionality": "bidirectional"}),
        # assertions: jsonValue recursive types, propertyNames, conditional known/headword
        ("assertions", {**valid_rows["assertions"], "value_json": None, "value_state": "unknown"}),
        ("assertions", {**valid_rows["assertions"], "value_json": "NA", "value_state": "unknown"}),
        ("assertions", {**valid_rows["assertions"], "value_json": None, "value_state": "known"}),
        ("assertions", {**valid_rows["assertions"], "value_json": ""}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": ""}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": True}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": 10**500}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": -(10**500)}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": 1e308}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": -0.0}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": [1, True, None, "ok", {"a_1": [2.5]}]}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {"1bad": "v"}}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {"a_1\n": "v"}}),
        # evidence
        ("evidence", {**valid_rows["evidence"], "locator_json": ""}),
        # decisions: dates and actor/outcome rules
        ("decisions", {**valid_rows["decisions"], "decision_date": "2024-02-29"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "2025-02-29"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "2026-02-30"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "0000-01-01"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "2026-13-01"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "2026-01-01\n"}),
        ("decisions", {**valid_rows["decisions"], "decision_date": "20260101"}),
        ("decisions", {**valid_rows["decisions"], "outcome": "accepted_human", "actor_type": "automated"}),
        ("decisions", {**valid_rows["decisions"], "outcome": "accepted_auto_source", "actor_type": "automated", "actor_id": None, "method_version": "v1"}),
        ("decisions", {**valid_rows["decisions"], "outcome": "accepted_auto_source", "actor_type": "automated", "actor_id": None, "method_version": None}),
        # changes
        ("changes", {**valid_rows["changes"], "old_assertion_id": None, "new_assertion_id": None}),
        # successors
        ("successors", {**valid_rows["successors"], "role": "delete"}),
        # findings: uniqueItems & conditional
        ("findings", {**valid_rows["findings"], "scalar_positions": [1, 1]}),
        ("findings", {**valid_rows["findings"], "scalar_positions": [1, 1.0]}),
        ("findings", {**valid_rows["findings"], "scalar_positions": [1, True]}),
        ("findings", {**valid_rows["findings"], "record_id": None, "assertion_id": None}),
        ("findings", {**valid_rows["findings"], "status": "resolved", "resolution_reason_json": None}),
        # unicode_exceptions: codepoint range & surrogates excluded by schema
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": []}),
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": [0xD800]}),
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": [0xDFFF]}),
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": [0xD7FF, 0xE000, 0x10FFFF]}),
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": [0x110000]}),
        # labels / scopes / pack_members
        ("labels", {**valid_rows["labels"], "category": "invalid"}),
        ("scopes", {**valid_rows["scopes"], "state": "attested", "label_code": None}),
        ("scopes", {**valid_rows["scopes"], "state": "unrestricted", "label_code": "LK"}),
        ("scopes", {**valid_rows["scopes"], "state": "unknown", "label_code": None, "supporting_assertion_id": None, "decision_id": None}),
        ("pack_members", {**valid_rows["pack_members"], "included_revision": "xyz"}),
    ]

    for table, mutated in cases:
        _assert_matches_reference(table, mutated)


def test_differential_non_json_python_objects_preserve_original_semantics(tmp_path):
    valid_rows = _valid_rows_by_table()

    # Tuple / nested tuple MUST NOT be accepted as JSON array by jsonschema_rs.
    non_json_cases: list[tuple[str, dict]] = [
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": ("a", "b")}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": [("nested",)]}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {"k": (1, 2)}}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {(1,): "v"}}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {1: "non_str_key"}}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": {"s": {1, 2}}}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": object()}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": Decimal("1.5")}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": float("nan")}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": float("inf")}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": float("-inf")}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": _SampleIntEnum.ONE}),
        ("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": _CustomDict(a="ok")}),
        ("findings", {**valid_rows["findings"], "scalar_positions": (0, 3)}),
        ("unicode_exceptions", {**valid_rows["unicode_exceptions"], "scalar_sequence": (0x0BA4,)}),
    ]

    for table, row in non_json_cases:
        assert _check_no_surrogates(row, table) is False
        _assert_matches_reference(table, row)

    # Top-level non-dict or dict subclass / tuple row.
    with pytest.raises(LexiconError):
        validate_row("entries", ("not", "a", "dict"))  # type: ignore[arg-type]

    # write_rows must also reject tuples in value_json instead of converting them to JSON arrays.
    with pytest.raises(LexiconError):
        write_rows(
            tmp_path / "assertions.csv",
            "assertions",
            [{**valid_rows["assertions"], "property_code": "misc", "value_json": ("a", "b")}],
        )


def test_control_and_surrogate_boundaries():
    valid_rows = _valid_rows_by_table()
    # Valid scalar boundaries (BMP non-surrogates, astral, Tamil + audit controls).
    boundary_text = "".join(
        chr(cp)
        for cp in (0xD7FF, 0xE000, 0x10000, 0x10FFFF, 0x0BA4, 0x007F, 0x0085, 0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF)
    ) + "\n"
    row = {**valid_rows["assertions"], "property_code": "misc", "value_json": boundary_text}
    _assert_matches_reference("assertions", row)

    # Lone surrogates at boundaries and nested inside tuple/dict after non-JSON value.
    for cp in (0xD800, 0xDBFF, 0xDC00, 0xDFFF):
        bad = chr(cp)
        for bad_val in (bad, [bad], (bad,), {"k": (1,), "bad": bad}, {bad: "k"}):
            with pytest.raises(LexiconError, match="invalid Unicode scalar: lone surrogate"):
                validate_row("assertions", {**valid_rows["assertions"], "property_code": "misc", "value_json": bad_val})


def test_offline_registry_blocks_unknown_retrieval(monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError("network access is forbidden during schema validation")

    monkeypatch.setattr(urllib.request, "urlopen", forbid_network)
    _table_registry.cache_clear()
    registry = _table_registry()
    assert len(registry) == 21

    # Unknown refs must never fetch from disk or network against our offline registry.
    base = "https://schemas.tamil-toolkit.invalid/lexicon/"
    docs = {}
    import json
    from tools.lexicon_tables import SCHEMA_DIR, _deny_retrieve

    rs_resources = []
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        docs[path.name] = doc
        rs_resources.append((base + path.name, doc))
        if "$id" in doc and ":" in doc["$id"]:
            rs_resources.append((doc["$id"], doc))

    rs_reg = jsonschema_rs.Registry(rs_resources, draft=jsonschema_rs.Draft202012, retriever=_deny_retrieve)
    for bad_ref in (
        "https://example.com/evil.schema.json",
        "http://localhost:9999/schema.json",
        "file:///C:/nonexistent.schema.json",
        "unknown.schema.json#/$defs/x",
    ):
        with pytest.raises(jsonschema_rs.ValidationError, match="Retrieval is disabled"):
            jsonschema_rs.Draft202012Validator(
                {"$ref": bad_ref},
                base_uri=base + "row.schema.json",
                registry=rs_reg,
                offline=True,
                validate_formats=True,
            )
        with pytest.raises((jsonschema_rs.ReferencingError, LexiconError)):
            rs_reg.resolver(base + "row.schema.json").lookup(bad_ref)


def test_existing_reviewed_fixture_roundtrip_and_exact_csv_bytes(tmp_path):
    csv_paths = sorted(REVIEWED_DIR.glob("*.csv"))
    assert len(csv_paths) == 21
    registry = _table_registry()

    for csv_path in csv_paths:
        table = csv_path.stem
        meta = registry[table]
        original_bytes = csv_path.read_bytes()
        decoded_rows = list(read_rows(csv_path))
        for row in decoded_rows:
            assert meta.validator.is_valid(row) is True
            assert meta.fast_validator.is_valid(row) is True

        replay_path = tmp_path / csv_path.name
        write_rows(replay_path, table, decoded_rows, source_root=tmp_path / "frozen")
        assert replay_path.read_bytes() == original_bytes
        assert list(read_rows(replay_path)) == decoded_rows


def test_read_rows_error_message_matches_reference(tmp_path):
    bad_csv = tmp_path / "senses.csv"
    bad_csv.write_text("sense_id,entry_id,display_order,parent_sense_id\nsns_1,ent_1,0,\n", encoding="utf-8", newline="\n")
    meta = _table_registry()["senses"]
    bad_row = {"sense_id": "sns_1", "entry_id": "ent_1", "display_order": 0, "parent_sense_id": None}
    expected = f"senses.csv:2 ({_format_validation_error(meta.validator, bad_row)})"
    with pytest.raises(LexiconError) as exc_info:
        list(read_rows(bad_csv))
    assert str(exc_info.value) == expected


def test_bounded_diagnostic_native_vs_reference_equivalence_and_timing(capsys):
    valid_rows = _valid_rows_by_table()
    meta = _table_registry()["assertions"]
    batch = [
        {
            **valid_rows["assertions"],
            "assertion_id": f"asr_{i}",
            "property_code": "misc",
            "value_json": {"k": i, "txt": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"},
        }
        for i in range(500)
    ]

    t0 = time.perf_counter()
    py_results = [meta.validator.is_valid(row) for row in batch]
    py_elapsed = time.perf_counter() - t0

    t1 = time.perf_counter()
    rs_results = [meta.fast_validator.is_valid(row) for row in batch]
    rs_elapsed = time.perf_counter() - t1

    assert py_results == [True] * len(batch)
    assert rs_results == py_results
    print(f"[diag 500 assertions] python={py_elapsed:.4f}s native={rs_elapsed:.4f}s")
