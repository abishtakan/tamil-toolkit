"""Curation table I/O, schema, and semantic validation tests (Feature 021 T008, T019, T021-T024)."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
from pathlib import Path
import urllib.request

import pytest

from tools.lexicon import LexiconError
from tools.lexicon_tables import fields, read_rows, validate_relations, write_rows

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas/lexicon"
ZERO_SHA = "0" * 64


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_tag(tag: str) -> str:
    return hashlib.sha256(tag.encode("utf-8")).hexdigest()


def _assertion(
    assertion_id: str,
    subject_kind: str,
    subject_id: str,
    property_code: str,
    value_json,
    *,
    value_state: str = "known",
    origin: str = "verbatim_source",
    source_fidelity_state: str = "verified",
    ambiguity_state: str = "unambiguous",
    algorithm_reference: str | None = None,
    convention_reference: str | None = None,
    imported_status_json=None,
    imported_confidence_json=None,
    revision_tag: str | None = None,
) -> dict:
    return {
        "assertion_id": assertion_id,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "property_code": property_code,
        "value_state": value_state,
        "value_json": value_json,
        "origin": origin,
        "source_fidelity_state": source_fidelity_state,
        "ambiguity_state": ambiguity_state,
        "algorithm_reference": algorithm_reference,
        "convention_reference": convention_reference,
        "imported_status_json": imported_status_json,
        "imported_confidence_json": imported_confidence_json,
        "claim_revision_sha256": _sha256_tag(revision_tag or f"rev:{assertion_id}"),
    }


def _make_valid_tables() -> dict[str, list[dict]]:
    snap_id = "snap_1"
    src_id = "src_1"
    rec_mapped = "rec_1"
    rec_split = "rec_2"
    rec_quar = "rec_3"
    rec_excl = "rec_4"

    ent_1 = "ent_1"
    ent_2 = "ent_2"
    ent_retired = "ent_0"

    frm_1 = "frm_1"
    frm_1_var = "frm_1v"
    frm_1_ipa = "frm_1i"
    frm_2 = "frm_2"

    sns_1 = "sns_1"
    sns_1_child = "sns_1a"
    sns_2 = "sns_2"

    txt_1_def = "txt_1"
    txt_1_ex = "txt_2"
    txt_1_tr = "txt_3"
    txt_1_unp = "txt_4"
    txt_2_def = "txt_5"

    rel_1 = "rel_1"
    rel_2 = "rel_2"
    rel_sense = "rel_3"

    hw_text = "\u0b85\u0bae\u0bcd\u0bae\u0bbe"
    zwj_text = "\u0b95" + chr(0x200D) + "\u0bcd"

    asr_hw_1 = _assertion("asr_hw_1", "form", frm_1, "headword", hw_text)
    asr_hw_1v = _assertion("asr_hw_1v", "form", frm_1_var, "headword", zwj_text)
    asr_ipa_1 = _assertion("asr_ipa_1", "form", frm_1_ipa, "ipa", "amma:")
    asr_conv_1 = _assertion("asr_conv_1", "form", frm_1_ipa, "convention", "ipa-2026")
    asr_hw_2 = _assertion("asr_hw_2", "form", frm_2, "headword", hw_text)

    asr_pos_1 = _assertion("asr_pos_1", "entry", ent_1, "part_of_speech", "noun")
    asr_pos_2 = _assertion("asr_pos_2", "entry", ent_2, "part_of_speech", "noun")

    asr_txt_1 = _assertion("asr_txt_1", "text", txt_1_def, "definition", "mother")
    asr_txt_2 = _assertion("asr_txt_2", "text", txt_1_ex, "example", "example tamil")
    asr_txt_3 = _assertion("asr_txt_3", "text", txt_1_tr, "translation", "example english")
    asr_txt_4 = _assertion("asr_txt_4", "text", txt_1_unp, "unparsed", "1. raw [uncertain]")
    asr_txt_5 = _assertion("asr_txt_5", "text", txt_2_def, "definition", "homograph sense")

    asr_rel_1 = _assertion("asr_rel_1", "relation", rel_1, "relation_code", "synonym")
    asr_rel_2 = _assertion("asr_rel_2", "relation", rel_2, "relation_code", "synonym")
    asr_rel_3 = _assertion("asr_rel_3", "relation", rel_sense, "relation_code", "see_also")

    asr_scope_1 = _assertion("asr_scope_1", "entry", ent_1, "region_scope", "LK-JAFFNA")
    asr_scope_2 = _assertion(
        "asr_scope_2",
        "entry",
        ent_2,
        "region_scope",
        "unrestricted",
        origin="correction",
        source_fidelity_state="changed",
    )

    dec_hw_1v = {
        "decision_id": "dec_hw_1v",
        "assertion_id": "asr_hw_1v",
        "assertion_revision_sha256": asr_hw_1v["claim_revision_sha256"],
        "evidence_bundle_sha256": _sha256_tag("evb_hw_1v"),
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "rev_1",
        "method_version": None,
        "decision_date": "2026-11-13",
        "note_json": "intentional ZWJ preserved",
        "predecessor_decision_id": None,
    }
    dec_scope_1 = {
        "decision_id": "dec_scope_1",
        "assertion_id": "asr_scope_1",
        "assertion_revision_sha256": asr_scope_1["claim_revision_sha256"],
        "evidence_bundle_sha256": _sha256_tag("evb_scope_1"),
        "outcome": "accepted_auto_source",
        "actor_type": "automated",
        "actor_id": None,
        "method_version": "scope-v1",
        "decision_date": "2026-11-13",
        "note_json": "attested region",
        "predecessor_decision_id": None,
    }
    dec_scope_2 = {
        "decision_id": "dec_scope_2",
        "assertion_id": "asr_scope_2",
        "assertion_revision_sha256": asr_scope_2["claim_revision_sha256"],
        "evidence_bundle_sha256": _sha256_tag("evb_scope_2"),
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "rev_1",
        "method_version": None,
        "decision_date": "2026-11-13",
        "note_json": "affirmatively unrestricted",
        "predecessor_decision_id": None,
    }

    return {
        "snapshots": [
            {
                "snapshot_id": snap_id,
                "dataset_id": "tamil-lexicon-intake",
                "relative_path": "entries.csv",
                "byte_length": 128,
                "sha256": _sha256_tag("snap_1"),
                "media_type": "text/csv",
                "logical_row_count": 5,
            }
        ],
        "sources": [
            {
                "source_id": src_id,
                "label_json": "Synthetic Structural Source",
                "publication_json": None,
                "url_json": None,
                "edition_json": None,
                "locator_json": "entries.csv:row:2",
                "snapshot_id": snap_id,
                "retrieval_date_state": "unknown",
                "retrieval_date_json": None,
                "extraction_method": "structural-test",
                "extraction_version": "1",
                "evidence_verification_state": "verified",
                "reuse_basis_json": "structural-fixture-only",
                "reuse_state": "permitted",
                "attribution_text_json": None,
                "attribution_reference_json": None,
            }
        ],
        "identities": [
            {
                "entity_id": ent_retired,
                "kind": "entry",
                "allocation_key": "legacy:L000",
                "lifecycle": "merged",
                "identity_decision_id": "dec_id_merge",
            },
            {
                "entity_id": ent_1,
                "kind": "entry",
                "allocation_key": "legacy:L001",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": ent_2,
                "kind": "entry",
                "allocation_key": "legacy:L002",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": sns_1,
                "kind": "sense",
                "allocation_key": "legacy:L001:sns1",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": sns_2,
                "kind": "sense",
                "allocation_key": "legacy:L002:sns1",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": sns_1_child,
                "kind": "sense",
                "allocation_key": "legacy:L001:sns1a",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": frm_1,
                "kind": "form",
                "allocation_key": "form:frm_1",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": frm_1_var,
                "kind": "form",
                "allocation_key": "form:frm_1v",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": frm_1_ipa,
                "kind": "form",
                "allocation_key": "form:frm_1i",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": frm_2,
                "kind": "form",
                "allocation_key": "form:frm_2",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": txt_1_def,
                "kind": "text",
                "allocation_key": "text:txt_1",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": txt_1_ex,
                "kind": "text",
                "allocation_key": "text:txt_2",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": txt_1_tr,
                "kind": "text",
                "allocation_key": "text:txt_3",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": txt_1_unp,
                "kind": "text",
                "allocation_key": "text:txt_4",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": txt_2_def,
                "kind": "text",
                "allocation_key": "text:txt_5",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": rel_1,
                "kind": "relation",
                "allocation_key": "rel:rel_1",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": rel_2,
                "kind": "relation",
                "allocation_key": "rel:rel_2",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
            {
                "entity_id": rel_sense,
                "kind": "relation",
                "allocation_key": "rel:rel_3",
                "lifecycle": "active",
                "identity_decision_id": None,
            },
        ],
        "source_records": [
            {
                "record_id": rec_mapped,
                "snapshot_id": snap_id,
                "ordinal": 2,
                "physical_line_start": 2,
                "physical_line_end": 2,
                "legacy_key_json": "L001",
                "raw_row_sha256": _sha256_tag("r1"),
            },
            {
                "record_id": rec_split,
                "snapshot_id": snap_id,
                "ordinal": 3,
                "physical_line_start": 3,
                "physical_line_end": 4,
                "legacy_key_json": "L002",
                "raw_row_sha256": _sha256_tag("r2"),
            },
            {
                "record_id": rec_quar,
                "snapshot_id": snap_id,
                "ordinal": 4,
                "physical_line_start": 5,
                "physical_line_end": 5,
                "legacy_key_json": "L003",
                "raw_row_sha256": _sha256_tag("r3"),
            },
            {
                "record_id": rec_excl,
                "snapshot_id": snap_id,
                "ordinal": 5,
                "physical_line_start": 6,
                "physical_line_end": 6,
                "legacy_key_json": "L004",
                "raw_row_sha256": _sha256_tag("r4"),
            },
        ],
        "dispositions": [
            {
                "record_id": rec_mapped,
                "disposition": "mapped",
                "structural_state": "validated",
                "reason_code": "mapped_primary",
                "note_json": "mapped to ent_1",
                "finding_set_sha256": ZERO_SHA,
                "method": "test-stage",
                "method_version": "1",
            },
            {
                "record_id": rec_split,
                "disposition": "split",
                "structural_state": "validated",
                "reason_code": "split_senses",
                "note_json": "split into two senses",
                "finding_set_sha256": ZERO_SHA,
                "method": "test-stage",
                "method_version": "1",
            },
            {
                "record_id": rec_quar,
                "disposition": "quarantined",
                "structural_state": "validated",
                "reason_code": "unknown_source_terms",
                "note_json": "quarantined pending source",
                "finding_set_sha256": ZERO_SHA,
                "method": "test-stage",
                "method_version": "1",
            },
            {
                "record_id": rec_excl,
                "disposition": "excluded",
                "structural_state": "validated",
                "reason_code": "derived_unreproducible",
                "note_json": "excluded non-source record",
                "finding_set_sha256": ZERO_SHA,
                "method": "test-stage",
                "method_version": "1",
            },
        ],
        "record_targets": [
            {"record_id": rec_mapped, "entity_id": ent_1, "target_role": "primary_entry"},
            {"record_id": rec_split, "entity_id": sns_1, "target_role": "split_sense"},
            {"record_id": rec_split, "entity_id": sns_2, "target_role": "split_sense"},
        ],
        "entries": [
            {
                "entry_id": ent_1,
                "language_id": "tam",
                "variety_id": None,
                "canonical_form_id": frm_1,
                "pos_assertion_id": "asr_pos_1",
                "structural_kind": "lexeme",
                "revision": _sha256_tag("entry_rev_1"),
            },
            {
                "entry_id": ent_2,
                "language_id": "tam",
                "variety_id": "LK-JAFFNA",
                "canonical_form_id": frm_2,
                "pos_assertion_id": "asr_pos_2",
                "structural_kind": "lexeme",
                "revision": _sha256_tag("entry_rev_2"),
            },
        ],
        "forms": [
            {
                "form_id": frm_1,
                "entry_id": ent_1,
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": "asr_hw_1",
                "convention_assertion_id": None,
            },
            {
                "form_id": frm_1_var,
                "entry_id": ent_1,
                "representation": "written",
                "role": "variant",
                "text_assertion_id": "asr_hw_1v",
                "convention_assertion_id": None,
            },
            {
                "form_id": frm_1_ipa,
                "entry_id": ent_1,
                "representation": "ipa",
                "role": "canonical",
                "text_assertion_id": "asr_ipa_1",
                "convention_assertion_id": "asr_conv_1",
            },
            {
                "form_id": frm_2,
                "entry_id": ent_2,
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": "asr_hw_2",
                "convention_assertion_id": None,
            },
        ],
        "senses": [
            {
                "sense_id": sns_1,
                "entry_id": ent_1,
                "display_order": 1,
                "parent_sense_id": None,
            },
            {
                "sense_id": sns_1_child,
                "entry_id": ent_1,
                "display_order": 2,
                "parent_sense_id": sns_1,
            },
            {
                "sense_id": sns_2,
                "entry_id": ent_2,
                "display_order": 1,
                "parent_sense_id": None,
            },
        ],
        "texts": [
            {
                "text_id": txt_1_def,
                "owner_kind": "sense",
                "owner_id": sns_1,
                "component": "definition",
                "language_id": "eng",
                "text_assertion_id": "asr_txt_1",
                "paired_translation_id": None,
                "cited_source_locator_json": None,
            },
            {
                "text_id": txt_1_ex,
                "owner_kind": "sense",
                "owner_id": sns_1,
                "component": "example",
                "language_id": "tam",
                "text_assertion_id": "asr_txt_2",
                "paired_translation_id": txt_1_tr,
                "cited_source_locator_json": "source:line:9",
            },
            {
                "text_id": txt_1_tr,
                "owner_kind": "sense",
                "owner_id": sns_1,
                "component": "translation",
                "language_id": "eng",
                "text_assertion_id": "asr_txt_3",
                "paired_translation_id": None,
                "cited_source_locator_json": None,
            },
            {
                "text_id": txt_1_unp,
                "owner_kind": "entry",
                "owner_id": ent_1,
                "component": "unparsed",
                "language_id": "tam",
                "text_assertion_id": "asr_txt_4",
                "paired_translation_id": None,
                "cited_source_locator_json": None,
            },
            {
                "text_id": txt_2_def,
                "owner_kind": "sense",
                "owner_id": sns_2,
                "component": "definition",
                "language_id": "eng",
                "text_assertion_id": "asr_txt_5",
                "paired_translation_id": None,
                "cited_source_locator_json": None,
            },
        ],
        "relations": [
            {
                "relation_id": rel_1,
                "source_kind": "entry",
                "source_id": ent_1,
                "target_kind": "entry",
                "target_id": ent_2,
                "relation_code_assertion_id": "asr_rel_1",
                "directionality": "undirected",
                "inverse_relation_id": rel_2,
            },
            {
                "relation_id": rel_2,
                "source_kind": "entry",
                "source_id": ent_2,
                "target_kind": "entry",
                "target_id": ent_1,
                "relation_code_assertion_id": "asr_rel_2",
                "directionality": "undirected",
                "inverse_relation_id": rel_1,
            },
            {
                "relation_id": rel_sense,
                "source_kind": "sense",
                "source_id": sns_1,
                "target_kind": "sense",
                "target_id": sns_2,
                "relation_code_assertion_id": "asr_rel_3",
                "directionality": "directed",
                "inverse_relation_id": None,
            },
        ],
        "assertions": [
            asr_hw_1,
            asr_hw_1v,
            asr_ipa_1,
            asr_conv_1,
            asr_hw_2,
            asr_pos_1,
            asr_pos_2,
            asr_txt_1,
            asr_txt_2,
            asr_txt_3,
            asr_txt_4,
            asr_txt_5,
            asr_rel_1,
            asr_rel_2,
            asr_rel_3,
            asr_scope_1,
            asr_scope_2,
        ],
        "evidence": [
            {
                "assertion_id": "asr_scope_1",
                "source_id": src_id,
                "source_record_id": rec_mapped,
                "locator_json": "entries.csv:row:2",
                "evidence_role": "supports",
                "extraction_version": "1",
                "extraction_sha256": _sha256_tag("ext_1"),
            }
        ],
        "decisions": [dec_hw_1v, dec_scope_1, dec_scope_2],
        "successors": [
            {
                "retired_id": ent_retired,
                "successor_id": ent_1,
                "role": "merge",
                "identity_decision_id": "dec_id_merge",
            }
        ],
        "unicode_exceptions": [
            {
                "assertion_id": "asr_hw_1v",
                "claim_revision_sha256": asr_hw_1v["claim_revision_sha256"],
                "value_sha256": _sha256_text(zwj_text),
                "kind": "intentional_control",
                "scalar_sequence": [0x200D],
                "scalar_position": 1,
                "reason_json": "explicit ZWJ control test",
                "decision_id": "dec_hw_1v",
            }
        ],
        "labels": [
            {
                "registry_id": "lexicon-labels",
                "registry_version": "1",
                "code": "LK",
                "category": "region",
                "display_label_json": "Sri Lanka",
                "definition_json": "Sri Lanka geographic region",
                "evidence_reference": "evd_reg_lk",
                "parent_code": None,
            },
            {
                "registry_id": "lexicon-labels",
                "registry_version": "1",
                "code": "LK-JAFFNA",
                "category": "region",
                "display_label_json": "Jaffna",
                "definition_json": "Jaffna region",
                "evidence_reference": "evd_reg_jaffna",
                "parent_code": "LK",
            },
            {
                "registry_id": "lexicon-labels",
                "registry_version": "1",
                "code": "literary",
                "category": "register",
                "display_label_json": "Literary",
                "definition_json": "Literary register",
                "evidence_reference": "evd_reg_lit",
                "parent_code": None,
            },
        ],
        "scopes": [
            {
                "subject_kind": "entry",
                "subject_id": ent_1,
                "dimension": "region",
                "state": "attested",
                "label_code": "LK-JAFFNA",
                "supporting_assertion_id": "asr_scope_1",
                "decision_id": "dec_scope_1",
            },
            {
                "subject_kind": "entry",
                "subject_id": ent_2,
                "dimension": "region",
                "state": "unrestricted",
                "label_code": None,
                "supporting_assertion_id": "asr_scope_2",
                "decision_id": "dec_scope_2",
            },
            {
                "subject_kind": "entry",
                "subject_id": ent_1,
                "dimension": "register",
                "state": "unknown",
                "label_code": None,
                "supporting_assertion_id": None,
                "decision_id": None,
            },
        ],
    }


def _assert_has_finding(findings: list[dict], *, subject_id: str | None = None, code_substr: str | None = None):
    assert findings, "expected at least one finding"
    for item in findings:
        assert set(item.keys()) >= {"code", "severity", "reason", "subject_id"}
        assert isinstance(item["code"], str) and item["code"]
        assert item["severity"] in {"info", "warning", "error"}
        assert isinstance(item["reason"], str) and item["reason"]
        assert isinstance(item["subject_id"], str)
    if subject_id is not None:
        assert any(f["subject_id"] == subject_id for f in findings), f"missing finding for {subject_id}: {findings}"
    if code_substr is not None:
        assert any(code_substr in f["code"] for f in findings), f"missing finding matching {code_substr!r}: {findings}"


def test_fields_matches_schema_property_order_for_all_21_tables():
    expected_tables = {}
    for schema_name in ("intake.schema.json", "lexical.schema.json", "review.schema.json"):
        doc = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
        for table_name, table_def in doc["$defs"].items():
            expected_tables[table_name] = list(table_def["properties"].keys())

    assert len(expected_tables) == 21
    for table_name, expected_cols in expected_tables.items():
        assert fields(table_name) == expected_cols

    # Specifically verify source_records uses schema keys (ordinal, physical_line_*), not inventory keys.
    assert fields("source_records") == [
        "record_id",
        "snapshot_id",
        "ordinal",
        "physical_line_start",
        "physical_line_end",
        "legacy_key_json",
        "raw_row_sha256",
    ]


def test_fields_rejects_unknown_table():
    with pytest.raises(LexiconError):
        fields("nonexistent_table")


def test_write_and_read_rows_roundtrip_all_value_kinds_and_atomic_sort(tmp_path):
    source_root = tmp_path / "frozen"
    source_root.mkdir()
    out_dir = tmp_path / "curation"
    out_dir.mkdir()

    # Include optional null FK, known empty JSON string, backslashes, astral scalar, ZWJ, typed JSON values, and ints.
    astral = chr(0x11FC0)
    zwj = "\u0b95" + chr(0x200D) + "\u0bcd"
    assertions_rows = [
        _assertion(
            "asr_b",
            "entry",
            "ent_1",
            "misc_known_empty",
            "",
            imported_status_json="verified",
            imported_confidence_json=1.0,
        ),
        _assertion(
            "asr_a",
            "form",
            "frm_1",
            "headword",
            f"a\\b\n{zwj} {astral}",
            value_state="known",
            imported_status_json=None,
            imported_confidence_json=None,
        ),
        _assertion(
            "asr_c",
            "entry",
            "ent_1",
            "pronunciation",
            None,
            value_state="unknown",
        ),
    ]
    assertions_path = out_dir / "assertions.csv"
    write_rows(assertions_path, "assertions", assertions_rows, source_root=source_root)

    raw_bytes = assertions_path.read_bytes()
    assert not raw_bytes.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw_bytes
    assert zwj.replace(chr(0x200D), "").split(chr(0x0BCD))[0] in raw_bytes.decode("utf-8")
    assert chr(0x200D).encode("utf-8") not in raw_bytes  # Controls remain visible as escapes.

    # Verify bytewise primary-ID sort and empty FK cells for null optional FKs.
    with assertions_path.open(encoding="utf-8", newline="") as handle:
        raw_csv_rows = list(csv.DictReader(handle, strict=True))
    assert [r["assertion_id"] for r in raw_csv_rows] == ["asr_a", "asr_b", "asr_c"]
    assert raw_csv_rows[0]["algorithm_reference"] == ""
    assert raw_csv_rows[0]["imported_status_json"] == "null"
    assert raw_csv_rows[1]["value_json"] == '""'
    assert raw_csv_rows[2]["value_json"] == "null"

    gen = read_rows(assertions_path)
    assert inspect.isgenerator(gen)
    decoded = list(gen)
    assert [r["assertion_id"] for r in decoded] == ["asr_a", "asr_b", "asr_c"]
    assert decoded[0]["value_json"] == f"a\\b\n{zwj} {astral}"
    assert decoded[1]["value_json"] == ""
    assert decoded[1]["imported_confidence_json"] == 1.0
    assert decoded[2]["value_json"] is None
    assert decoded[0]["algorithm_reference"] is None

    # Test integer and array columns in source_records, snapshots, and findings.
    snap_rows = [
        {
            "snapshot_id": "snap_1",
            "dataset_id": "ds_1",
            "relative_path": "a.csv",
            "byte_length": 10,
            "sha256": ZERO_SHA,
            "media_type": "text/csv",
            "logical_row_count": 2,
        },
        {
            "snapshot_id": "snap_2",
            "dataset_id": "ds_1",
            "relative_path": "b.fst",
            "byte_length": 16,
            "sha256": "1" * 64,
            "media_type": "application/octet-stream",
            "logical_row_count": None,
        },
    ]
    snap_path = out_dir / "snapshots.csv"
    write_rows(snap_path, "snapshots", snap_rows, source_root=source_root)
    assert list(read_rows(snap_path)) == snap_rows

    rec_rows = [
        {
            "record_id": "rec_1",
            "snapshot_id": "snap_1",
            "ordinal": 2,
            "physical_line_start": 2,
            "physical_line_end": 3,
            "legacy_key_json": "L001",
            "raw_row_sha256": ZERO_SHA,
        }
    ]
    rec_path = out_dir / "source_records.csv"
    write_rows(rec_path, "source_records", rec_rows, source_root=source_root)
    assert list(read_rows(rec_path)) == rec_rows

    # Header-only table round-trips to empty list.
    empty_forms = out_dir / "forms.csv"
    write_rows(empty_forms, "forms", [], source_root=source_root)
    assert list(read_rows(empty_forms)) == []

    finding_rows = [
        {
            "finding_id": "fnd_1",
            "record_id": "rec_1",
            "assertion_id": None,
            "issue_code": "joiner_present",
            "severity": "info",
            "scalar_positions": [0, 3],
            "status": "open",
            "resolution_reason_json": None,
        }
    ]
    fnd_path = out_dir / "findings.csv"
    write_rows(fnd_path, "findings", finding_rows, source_root=source_root)
    assert list(read_rows(fnd_path)) == finding_rows


def test_write_rows_rejects_source_overlap_and_preserves_prior_output_on_error(tmp_path):
    source_root = tmp_path / "frozen"
    source_root.mkdir()
    with pytest.raises(LexiconError):
        write_rows(source_root / "entries.csv", "entries", [], source_root=source_root)

    out_path = tmp_path / "entries.csv"
    valid_row = {
        "entry_id": "ent_1",
        "language_id": "tam",
        "variety_id": None,
        "canonical_form_id": None,
        "pos_assertion_id": None,
        "structural_kind": "lexeme",
        "revision": ZERO_SHA,
    }
    write_rows(out_path, "entries", [valid_row], source_root=source_root)

    def bad_rows():
        yield valid_row
        yield {**valid_row, "entry_id": "ent_\ud800"}

    with pytest.raises(LexiconError):
        write_rows(out_path, "entries", bad_rows(), source_root=source_root)
    assert list(read_rows(out_path)) == [valid_row]


def test_read_rows_rejects_bom_crlf_and_wrong_headers(tmp_path):
    valid_path = tmp_path / "senses.csv"
    row = {"sense_id": "sns_1", "entry_id": "ent_1", "display_order": 1, "parent_sense_id": None}
    write_rows(valid_path, "senses", [row])
    valid_bytes = valid_path.read_bytes()

    bom_path = tmp_path / "bom.csv"
    bom_path.write_bytes(b"\xef\xbb\xbf" + valid_bytes)
    with pytest.raises(LexiconError):
        list(read_rows(bom_path, table="senses"))

    crlf_path = tmp_path / "crlf.csv"
    crlf_path.write_bytes(valid_bytes.replace(b"\n", b"\r\n"))
    with pytest.raises(LexiconError):
        list(read_rows(crlf_path, table="senses"))

    wrong_order = tmp_path / "wrong_order.csv"
    wrong_order.write_text("entry_id,sense_id,display_order,parent_sense_id\nent_1,sns_1,1,\n", encoding="utf-8", newline="\n")
    with pytest.raises(LexiconError):
        list(read_rows(wrong_order, table="senses"))

    extra_col = tmp_path / "extra_col.csv"
    extra_col.write_text("sense_id,entry_id,display_order,parent_sense_id,extra\n", encoding="utf-8", newline="\n")
    with pytest.raises(LexiconError):
        list(read_rows(extra_col, table="senses"))

    empty_file = tmp_path / "empty.csv"
    empty_file.write_bytes(b"")
    with pytest.raises(LexiconError):
        list(read_rows(empty_file, table="senses"))


def test_read_rows_accepts_utf8_json_cells_and_rejects_malformed_json_surrogates_and_raw_controls(tmp_path):
    from tools.lexicon import data_json

    header = ",".join(fields("labels")) + "\n"

    def write_csv_row(path: Path, row_cells: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(fields("labels"))
            writer.writerow(row_cells)

    valid_utf8 = tmp_path / "labels.csv"
    label_value = (
        "\u0b85\u0bae\u0bcd\u0bae\u0bbe " + chr(92) + "u0ba4 "
        + chr(0x200D) + " " + chr(0x2028) + " " + chr(0x2029)
        + " " + chr(0x0085) + " \n"
    )
    write_csv_row(
        valid_utf8,
        [
            "reg_1",
            "1",
            "LK",
            "region",
            data_json(label_value),
            '"Sri Lanka"',
            "evd_1",
            "",
        ],
    )
    decoded_utf8 = list(read_rows(valid_utf8))
    assert len(decoded_utf8) == 1
    assert decoded_utf8[0]["display_label_json"] == label_value

    # Malformed JSON cell must be rejected.
    malformed_json = tmp_path / "malformed.csv"
    write_csv_row(malformed_json, ["reg_1", "1", "LK", "region", '"unclosed', '"Sri Lanka"', "evd_1", ""])
    with pytest.raises(LexiconError):
        list(read_rows(malformed_json, table="labels"))

    # Raw unescaped audit controls in JSON cells must be rejected.
    for cp in (0x007F, 0x0085, 0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF):
        raw_ctrl = tmp_path / f"raw_ctrl_{cp:04x}.csv"
        write_csv_row(raw_ctrl, ["reg_1", "1", "LK", "region", f'"a{chr(cp)}b"', '"Sri Lanka"', "evd_1", ""])
        with pytest.raises(LexiconError):
            list(read_rows(raw_ctrl, table="labels"))

    # Lone surrogate encoded inside JSON string cell (constructed dynamically for source-unicode gate).
    lone_surrogate_cell = '"bad\\' + 'ud800"'
    surrogate_path = tmp_path / "surrogate.csv"
    surrogate_path.write_text(
        header + f'reg_1,1,LK,region,{lone_surrogate_cell},"def",evd_1,\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(LexiconError):
        list(read_rows(surrogate_path, table="labels"))

    # Unknown table / unknown inferred stem.
    unknown_path = tmp_path / "unknown_table.csv"
    unknown_path.write_text("a,b\n1,2\n", encoding="utf-8", newline="\n")
    with pytest.raises(LexiconError):
        list(read_rows(unknown_path))
    with pytest.raises(LexiconError):
        list(read_rows(unknown_path, table="unknown_table"))


def test_read_rows_validates_schema_via_local_registry_without_network(tmp_path, monkeypatch):
    def forbid_network(*args, **kwargs):
        raise AssertionError("network access is forbidden during schema validation")

    monkeypatch.setattr(urllib.request, "urlopen", forbid_network)

    # Forbidden coercion of unknown/not_applicable to non-null value_json.
    asr_header = ",".join(fields("assertions")) + "\n"
    bad_unknown = tmp_path / "assertions.csv"
    bad_unknown.write_text(
        asr_header
        + f'asr_1,entry,ent_1,pos,unknown,"NA",verbatim_source,unknown,unknown,,,null,null,{ZERO_SHA}\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(LexiconError):
        list(read_rows(bad_unknown))

    # Forbidden empty headword when value_state is known.
    bad_empty_hw = tmp_path / "empty_hw.csv"
    bad_empty_hw.write_text(
        asr_header
        + f'asr_1,form,frm_1,headword,known,"",verbatim_source,verified,unambiguous,,,null,null,{ZERO_SHA}\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(LexiconError):
        list(read_rows(bad_empty_hw, table="assertions"))

    # Invalid calendar date rejected by local FormatChecker.
    dec_header = ",".join(fields("decisions")) + "\n"
    bad_date = tmp_path / "decisions.csv"
    bad_date.write_text(
        dec_header
        + f'dec_1,asr_1,{ZERO_SHA},{ZERO_SHA},pending,human,rev_1,,2026-02-30,"note",\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(LexiconError):
        list(read_rows(bad_date))

    # Reject NaN in JSON cells and non-canonical integers.
    bad_nan = tmp_path / "bad_nan.csv"
    bad_nan.write_text(
        asr_header
        + f'asr_1,entry,ent_1,conf,known,1.0,verbatim_source,verified,unambiguous,,,null,NaN,{ZERO_SHA}\n',
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(LexiconError):
        list(read_rows(bad_nan, table="assertions"))

    sns_header = ",".join(fields("senses")) + "\n"
    bad_int = tmp_path / "senses.csv"
    bad_int.write_text(sns_header + "sns_1,ent_1,01,\n", encoding="utf-8", newline="\n")
    with pytest.raises(LexiconError):
        list(read_rows(bad_int))


def test_validate_relations_valid_baseline_and_homographs_pass():
    tables = _make_valid_tables()
    assert validate_relations(tables) == []


def test_validate_relations_detects_duplicate_ids_and_dangling_refs():
    tables = _make_valid_tables()
    tables["entries"].append({**tables["entries"][0]})
    _assert_has_finding(validate_relations(tables), subject_id="ent_1", code_substr="duplicate")

    # Cross-table ID collision between entries and senses.
    tables = _make_valid_tables()
    tables["senses"].append({"sense_id": "ent_1", "entry_id": "ent_1", "display_order": 3, "parent_sense_id": None})
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")

    # Dangling references.
    tables = _make_valid_tables()
    tables["forms"][0]["entry_id"] = "ent_missing"
    _assert_has_finding(validate_relations(tables), subject_id="frm_1")

    tables = _make_valid_tables()
    tables["entries"][0]["pos_assertion_id"] = "asr_missing"
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")


def test_validate_relations_enforces_canonical_written_form_cardinality():
    # Zero canonical written forms (only variant remains).
    tables = _make_valid_tables()
    tables["forms"] = [f for f in tables["forms"] if f["form_id"] != "frm_1"]
    tables["entries"][0]["canonical_form_id"] = None
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")

    # Two canonical written forms for one entry.
    tables = _make_valid_tables()
    tables["forms"][1]["role"] = "canonical"
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")

    # canonical_form_id disagrees with the canonical written form.
    tables = _make_valid_tables()
    tables["entries"][0]["canonical_form_id"] = "frm_1v"
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")


def test_validate_relations_enforces_sense_parent_same_entry_and_acyclic():
    # Cross-entry parent sense.
    tables = _make_valid_tables()
    tables["senses"][1]["parent_sense_id"] = "sns_2"
    _assert_has_finding(validate_relations(tables), subject_id="sns_1a")

    # Self-cycle.
    tables = _make_valid_tables()
    tables["senses"][0]["parent_sense_id"] = "sns_1"
    _assert_has_finding(validate_relations(tables), subject_id="sns_1")

    # Multi-hop cycle within same entry.
    tables = _make_valid_tables()
    tables["senses"][0]["parent_sense_id"] = "sns_1a"
    _assert_has_finding(validate_relations(tables))


def test_validate_relations_enforces_text_owner_and_paired_translation():
    # Owner kind/id mismatch (says entry, points to sense ID).
    tables = _make_valid_tables()
    tables["texts"][0]["owner_kind"] = "entry"
    _assert_has_finding(validate_relations(tables), subject_id="txt_1")

    # paired_translation_id pointing to non-translation component.
    tables = _make_valid_tables()
    tables["texts"][1]["paired_translation_id"] = "txt_1"
    _assert_has_finding(validate_relations(tables), subject_id="txt_2")

    # paired_translation_id pointing to translation with a different owner.
    tables = _make_valid_tables()
    tables["texts"][2]["owner_id"] = "sns_2"
    _assert_has_finding(validate_relations(tables), subject_id="txt_2")


def test_validate_relations_enforces_relation_endpoints_and_no_spelling_guessing():
    # Target set to headword spelling instead of unique ID.
    tables = _make_valid_tables()
    tables["relations"][2]["target_kind"] = "entry"
    tables["relations"][2]["target_id"] = "\u0b85\u0bae\u0bcd\u0bae\u0bbe"
    _assert_has_finding(validate_relations(tables), subject_id="rel_3")

    # Endpoint kind/table mismatch (claims sense, gives entry ID).
    tables = _make_valid_tables()
    tables["relations"][2]["target_kind"] = "sense"
    tables["relations"][2]["target_id"] = "ent_2"
    _assert_has_finding(validate_relations(tables), subject_id="rel_3")

    # Incompatible inverse relation endpoints/directionality.
    tables = _make_valid_tables()
    tables["relations"][1]["directionality"] = "directed"
    _assert_has_finding(validate_relations(tables), subject_id="rel_1")

    # Ambiguous target/relation assertion cannot auto-pass.
    tables = _make_valid_tables()
    asr_amb = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_rel_3")
    asr_amb["ambiguity_state"] = "ambiguous"
    tables["decisions"].append(
        {
            "decision_id": "dec_bad_rel_auto",
            "assertion_id": "asr_rel_3",
            "assertion_revision_sha256": asr_amb["claim_revision_sha256"],
            "evidence_bundle_sha256": ZERO_SHA,
            "outcome": "accepted_auto_source",
            "actor_type": "automated",
            "actor_id": None,
            "method_version": "auto-v1",
            "decision_date": "2026-11-13",
            "note_json": "invalid auto on ambiguous",
            "predecessor_decision_id": None,
        }
    )
    _assert_has_finding(validate_relations(tables), subject_id="dec_bad_rel_auto")


def test_validate_relations_enforces_scope_decisions_label_categories_and_no_unknown_coercion():
    # Unrestricted scope without decision or with pending decision fails.
    tables = _make_valid_tables()
    tables["scopes"][1]["decision_id"] = None
    _assert_has_finding(validate_relations(tables), subject_id="ent_2")

    tables = _make_valid_tables()
    tables["decisions"][2]["outcome"] = "pending"
    _assert_has_finding(validate_relations(tables), subject_id="ent_2")

    # Unrestricted scope supported by an unknown-value assertion fails (no coercion of unknown into fact).
    tables = _make_valid_tables()
    asr_s2 = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_scope_2")
    asr_s2["value_state"] = "unknown"
    asr_s2["value_json"] = None
    _assert_has_finding(validate_relations(tables), subject_id="ent_2")

    # Category mismatch: register scope referencing a region label.
    tables = _make_valid_tables()
    tables["scopes"][2]["state"] = "attested"
    tables["scopes"][2]["label_code"] = "LK-JAFFNA"
    tables["scopes"][2]["supporting_assertion_id"] = "asr_scope_1"
    tables["scopes"][2]["decision_id"] = "dec_scope_1"
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")

    # Cyclic label parent_code.
    tables = _make_valid_tables()
    tables["labels"][0]["parent_code"] = "LK-JAFFNA"
    _assert_has_finding(validate_relations(tables))

    # Unknown assertion coerced to non-null value in-memory.
    tables = _make_valid_tables()
    tables["assertions"][2]["value_state"] = "not_applicable"
    tables["assertions"][2]["value_json"] = "NA"
    _assert_has_finding(validate_relations(tables), subject_id="asr_ipa_1")


def test_validate_relations_enforces_record_dispositions_one_to_one_and_cardinality():
    # Missing disposition for a source record.
    tables = _make_valid_tables()
    tables["dispositions"] = tables["dispositions"][1:]
    _assert_has_finding(validate_relations(tables), subject_id="rec_1")

    # Mapped with zero targets.
    tables = _make_valid_tables()
    tables["record_targets"] = [rt for rt in tables["record_targets"] if rt["record_id"] != "rec_1"]
    _assert_has_finding(validate_relations(tables), subject_id="rec_1")

    # Split with fewer than two targets.
    tables = _make_valid_tables()
    tables["record_targets"] = [rt for rt in tables["record_targets"] if not (rt["record_id"] == "rec_2" and rt["entity_id"] == "sns_2")]
    _assert_has_finding(validate_relations(tables), subject_id="rec_2")

    # Quarantined record must have no target mappings.
    tables = _make_valid_tables()
    tables["record_targets"].append({"record_id": "rec_3", "entity_id": "ent_1", "target_role": "bad_quarantine_target"})
    _assert_has_finding(validate_relations(tables), subject_id="rec_3")

    # Excluded record must have no target mappings.
    tables = _make_valid_tables()
    tables["record_targets"].append({"record_id": "rec_4", "entity_id": "ent_1", "target_role": "bad_excluded_target"})
    _assert_has_finding(validate_relations(tables), subject_id="rec_4")


def test_validate_relations_enforces_successor_cycles_and_stale_unicode_exceptions():
    # Multi-hop successor cycle.
    tables = _make_valid_tables()
    tables["identities"][1]["lifecycle"] = "split"
    tables["identities"][1]["identity_decision_id"] = "dec_split"
    tables["successors"].append(
        {
            "retired_id": "ent_1",
            "successor_id": "ent_0",
            "role": "split",
            "identity_decision_id": "dec_split",
        }
    )
    _assert_has_finding(validate_relations(tables))

    # Stale unicode exception after revision change.
    tables = _make_valid_tables()
    tables["unicode_exceptions"][0]["claim_revision_sha256"] = ZERO_SHA
    _assert_has_finding(validate_relations(tables), subject_id="asr_hw_1v")

    # Stale/unused unicode exception after scalar value change.
    tables = _make_valid_tables()
    tables["unicode_exceptions"][0]["value_sha256"] = ZERO_SHA
    _assert_has_finding(validate_relations(tables), subject_id="asr_hw_1v")

    # Unused intentional_control exception pointing at ordinary ASCII scalar.
    tables = _make_valid_tables()
    tables["unicode_exceptions"][0]["scalar_sequence"] = [ord("a")]
    tables["unicode_exceptions"][0]["scalar_position"] = 0
    _assert_has_finding(validate_relations(tables), subject_id="asr_hw_1v")

    # Non-NFC original exception constructed dynamically without triggering source Unicode gate.
    tables = _make_valid_tables()
    non_nfc = chr(0x0B92) + chr(0x0BD7)
    asr_hw1 = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_hw_1")
    asr_hw1["value_json"] = non_nfc
    tables["decisions"].append(
        {
            "decision_id": "dec_non_nfc",
            "assertion_id": "asr_hw_1",
            "assertion_revision_sha256": asr_hw1["claim_revision_sha256"],
            "evidence_bundle_sha256": ZERO_SHA,
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "rev_1",
            "method_version": None,
            "decision_date": "2026-11-13",
            "note_json": "preserve non-NFC original",
            "predecessor_decision_id": None,
        }
    )
    tables["unicode_exceptions"].append(
        {
            "assertion_id": "asr_hw_1",
            "claim_revision_sha256": asr_hw1["claim_revision_sha256"],
            "value_sha256": _sha256_text(non_nfc),
            "kind": "non_nfc_original",
            "scalar_sequence": [0x0B92, 0x0BD7],
            "scalar_position": 0,
            "reason_json": "decomposed vowel original",
            "decision_id": "dec_non_nfc",
        }
    )
    assert validate_relations(tables) == []

    # Mutating non-NFC assertion text invalidates the exception.
    asr_hw1["value_json"] = "\u0b94"
    _assert_has_finding(validate_relations(tables), subject_id="asr_hw_1")


def test_validate_relations_enforces_pack_members_and_changes_consistency():
    tables = _make_valid_tables()
    tables["pack_members"] = [
        {
            "pack_id": "core",
            "entry_id": "ent_1",
            "included_revision": tables["entries"][0]["revision"],
            "relation_inclusion_policy": "omit_cross_pack",
        }
    ]
    assert validate_relations(tables) == []

    tables["pack_members"][0]["included_revision"] = ZERO_SHA
    _assert_has_finding(validate_relations(tables), subject_id="ent_1")

    tables = _make_valid_tables()
    tables["changes"] = [
        {
            "change_id": "chg_1",
            "subject_id": "ent_1",
            "old_assertion_id": "asr_pos_1",
            "new_assertion_id": "asr_pos_1",
            "reason_json": "self change invalid",
            "evidence_reference": "evd_1",
            "decision_id": "dec_scope_1",
            "inverse_change_id": "chg_1",
        }
    ]
    _assert_has_finding(validate_relations(tables), subject_id="chg_1")


def test_validate_projection_complete_reference_closure_and_no_false_disposition_errors(tmp_path):
    from tools.lexicon_review import claim_revision, evidence_hash
    from tools.lexicon_validate import validate_projection

    source_root = tmp_path / "frozen"
    source_root.mkdir()
    ws = tmp_path / "editorial"
    ws.mkdir()

    tables = _make_valid_tables()
    # Add an extra unprojected raw intake source record + disposition + raw assertion (not in projected entries)
    # to ensure validate_projection does not emit false missing_disposition or retain unrelated raw intake rows.
    raw_rec = {
        "record_id": "rec_raw_only",
        "snapshot_id": "snap_1",
        "ordinal": 99,
        "physical_line_start": 99,
        "physical_line_end": 99,
        "legacy_key_json": "L999",
        "raw_row_sha256": _sha256_tag("r999"),
    }
    tables["source_records"].append(raw_rec)
    tables["dispositions"].append(
        {
            "record_id": "rec_raw_only",
            "disposition": "quarantined",
            "structural_state": "validated",
            "reason_code": "SOURCE_AND_REUSE_UNVERIFIED",
            "note_json": "unprojected intake row",
            "finding_set_sha256": ZERO_SHA,
            "method": "test-stage",
            "method_version": "1",
        }
    )
    raw_asr = _assertion("asr_raw_only", "entry", "ent_raw_only", "unparsed_source_record", {"huge": "blob"})
    raw_asr["claim_revision_sha256"] = claim_revision(raw_asr)
    tables["identities"].append(
        {
            "entity_id": "ent_raw_only",
            "kind": "entry",
            "allocation_key": "legacy:L999",
            "lifecycle": "active",
            "identity_decision_id": None,
        }
    )
    tables["assertions"].append(raw_asr)
    tables["evidence"].append(
        {
            "assertion_id": "asr_raw_only",
            "source_id": "src_1",
            "source_record_id": "rec_raw_only",
            "locator_json": "entries.csv:row:99",
            "evidence_role": "transcribes",
            "extraction_version": "1",
            "extraction_sha256": _sha256_tag("ext_raw"),
        }
    )

    # Add a historical assertion referenced only by changes + decisions (not in entries/forms/texts/relations)
    # and a label whose evidence_reference is an assertion_id.
    asr_pos_old = _assertion("asr_pos_1_old", "entry", "ent_1", "part_of_speech", "verb")
    asr_pos_new = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_pos_1")
    asr_pos_new["claim_revision_sha256"] = claim_revision(asr_pos_new)
    asr_pos_old["claim_revision_sha256"] = claim_revision(asr_pos_old)
    tables["assertions"].append(asr_pos_old)

    # Recompute claim_revision_sha256 and decision hashes so validate_history passes cleanly.
    for a in tables["assertions"]:
        a["claim_revision_sha256"] = claim_revision(a)
    for d in tables["decisions"]:
        target = next(a for a in tables["assertions"] if a["assertion_id"] == d["assertion_id"])
        d["assertion_revision_sha256"] = target["claim_revision_sha256"]
        ev_for_d = [e for e in tables["evidence"] if e["assertion_id"] == d["assertion_id"]]
        d["evidence_bundle_sha256"] = evidence_hash(ev_for_d)
    for u in tables["unicode_exceptions"]:
        target = next(a for a in tables["assertions"] if a["assertion_id"] == u["assertion_id"])
        u["claim_revision_sha256"] = target["claim_revision_sha256"]
    # Provide decision dec_id_merge referenced by retired identity ent_0 & successors.
    tables["decisions"].append(
        {
            "decision_id": "dec_id_merge",
            "assertion_id": "asr_pos_1",
            "assertion_revision_sha256": asr_pos_new["claim_revision_sha256"],
            "evidence_bundle_sha256": evidence_hash([]),
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "rev_1",
            "method_version": None,
            "decision_date": "2026-11-13",
            "note_json": "merge decision",
            "predecessor_decision_id": None,
        }
    )
    tables["changes"] = [
        {
            "change_id": "chg_pos_1",
            "subject_id": "ent_1",
            "old_assertion_id": "asr_pos_1_old",
            "new_assertion_id": "asr_pos_1",
            "reason_json": "corrected pos",
            "evidence_reference": "asr_pos_1",
            "decision_id": "dec_id_merge",
            "inverse_change_id": None,
        }
    ]
    tables["labels"].append(
        {
            "registry_id": "imported_categories",
            "registry_version": "1",
            "code": "lbl_pos",
            "category": "grammar_system",
            "display_label_json": "noun",
            "definition_json": "pos label",
            "evidence_reference": "asr_pos_1",
            "parent_code": None,
        }
    )

    for tbl_name, rows in tables.items():
        write_rows(ws / f"{tbl_name}.csv", tbl_name, rows, source_root=source_root)
    for extra in ("pack_members",):
        write_rows(ws / f"{extra}.csv", extra, [], source_root=source_root)

    assert validate_projection(ws) == []

    # Dangling source_record_id on retained evidence must be flagged.
    bad_ev = [
        dict(e, source_record_id="rec_missing") if e["assertion_id"] == "asr_scope_1" else e
        for e in tables["evidence"]
    ]
    write_rows(ws / "evidence.csv", "evidence", bad_ev, source_root=source_root)
    findings = validate_projection(ws)
    assert any(f.get("code") == "dangling_reference" and "rec_missing" in f.get("reason", "") for f in findings)


def test_validate_relations_flags_missing_identities_non_actual_non_nfc_and_accepts_2028_2029_controls():
    from tools.lexicon_review import claim_revision

    # Entity missing from provided identities table must be flagged.
    tables = _make_valid_tables()
    tables["identities"] = [i for i in tables["identities"] if i["entity_id"] != "frm_1"]
    _assert_has_finding(validate_relations(tables), subject_id="frm_1")

    # non_nfc_original exception on an already-NFC string must be rejected via Rust.
    tables = _make_valid_tables()
    nfc_text = "\u0b94"
    asr_hw1 = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_hw_1")
    asr_hw1["value_json"] = nfc_text
    asr_hw1["claim_revision_sha256"] = claim_revision(asr_hw1)
    tables["decisions"].append(
        {
            "decision_id": "dec_fake_non_nfc",
            "assertion_id": "asr_hw_1",
            "assertion_revision_sha256": asr_hw1["claim_revision_sha256"],
            "evidence_bundle_sha256": ZERO_SHA,
            "outcome": "accepted_human",
            "actor_type": "human",
            "actor_id": "rev_1",
            "method_version": None,
            "decision_date": "2026-11-13",
            "note_json": "false non-NFC exception",
            "predecessor_decision_id": None,
        }
    )
    tables["unicode_exceptions"].append(
        {
            "assertion_id": "asr_hw_1",
            "claim_revision_sha256": asr_hw1["claim_revision_sha256"],
            "value_sha256": _sha256_text(nfc_text),
            "kind": "non_nfc_original",
            "scalar_sequence": [0x0B94],
            "scalar_position": 0,
            "reason_json": "falsely claims NFC string is non-NFC",
            "decision_id": "dec_fake_non_nfc",
        }
    )
    _assert_has_finding(validate_relations(tables), subject_id="asr_hw_1", code_substr="unused_unicode_exception")

    # intentional_control supports U+2028 and U+2029 matching data_json audit-control set.
    for cp in (0x2028, 0x2029):
        tables = _make_valid_tables()
        ctrl_text = "a" + chr(cp) + "b"
        asr_hw1 = next(a for a in tables["assertions"] if a["assertion_id"] == "asr_hw_1")
        asr_hw1["value_json"] = ctrl_text
        asr_hw1["claim_revision_sha256"] = claim_revision(asr_hw1)
        tables["decisions"].append(
            {
                "decision_id": "dec_sep_ctrl",
                "assertion_id": "asr_hw_1",
                "assertion_revision_sha256": asr_hw1["claim_revision_sha256"],
                "evidence_bundle_sha256": ZERO_SHA,
                "outcome": "accepted_human",
                "actor_type": "human",
                "actor_id": "rev_1",
                "method_version": None,
                "decision_date": "2026-11-13",
                "note_json": "intentional line/paragraph separator",
                "predecessor_decision_id": None,
            }
        )
        tables["unicode_exceptions"].append(
            {
                "assertion_id": "asr_hw_1",
                "claim_revision_sha256": asr_hw1["claim_revision_sha256"],
                "value_sha256": _sha256_text(ctrl_text),
                "kind": "intentional_control",
                "scalar_sequence": [cp],
                "scalar_position": 1,
                "reason_json": "preserve separator",
                "decision_id": "dec_sep_ctrl",
            }
        )
        assert validate_relations(tables) == []


def test_check_curated_csv_validates_projected_unicode_exceptions_refs_and_skips_unparsed_intake(tmp_path, monkeypatch):
    from tools.lexicon import inventory, native_inspect, stage
    from tools.lexicon_curate import project
    import tools.lexicon_review as review
    from tools.lexicon_validate import check_curated_csv

    source = tmp_path / "source"
    source.mkdir()
    non_nfc = chr(0x0B92) + chr(0x0BD7)
    (source / "primary_lemmas.csv").write_text(
        f"word_id,headword_ta,part_of_speech\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,NOUN\n2,{non_nfc},NOUN\n3,\u0b95\u0bca,VERB\n",
        encoding="utf-8",
    )
    (source / "unified_master_30col.csv").write_text(
        f"word_id,headword_ta,extra\n1,\u0b85\u0bae\u0bcd\u0bae\u0bbe,ok\n2,{non_nfc},raw\n3,\u0b95\u0bca,raw-unprojected\n",
        encoding="utf-8",
    )
    inv, ws = tmp_path / "inventory", tmp_path / "editorial"
    canonical = tmp_path / "canonical"
    canonical.mkdir()
    inventory(source, inv)
    stage(inv, ws)

    src_recs = list(read_rows(ws / "source_records.csv"))
    selected = {r["record_id"] for r in src_recs if r["legacy_key_json"] in {"1", "2"}}
    # Only project primary_lemmas rows 1 and 2 (record 3 & master rows stay unparsed raw intake).
    lemma_snap = next(s["snapshot_id"] for s in read_rows(ws / "snapshots.csv") if s["relative_path"] == "primary_lemmas.csv")
    selected = {r["record_id"] for r in src_recs if r["snapshot_id"] == lemma_snap and r["legacy_key_json"] in {"1", "2"}}
    project(ws, selected, source=source)

    inspected_inputs = []
    real_inspect = native_inspect

    def spy_inspect(text):
        inspected_inputs.append(text)
        return real_inspect(text)

    monkeypatch.setattr(review, "native_inspect", spy_inspect)

    # Valid quarantined projection passes: unparsed raw intake blobs are NOT passed to native_inspect,
    # while projected non_nfc_original on word 2 IS queued in findings.csv.
    ok_res = check_curated_csv(ws, canonical)
    assert ok_res["findings"] == []
    assert not any("raw-unprojected" in item for item in inspected_inputs)

    # Removing the queued open finding for the non-NFC projected claim must fail the gate.
    saved_findings = list(read_rows(ws / "findings.csv"))
    write_rows(
        ws / "findings.csv",
        "findings",
        [f for f in saved_findings if f["issue_code"] != "non_nfc_original"],
        source_root=source,
    )
    missing_q = check_curated_csv(ws, canonical)
    assert missing_q["findings"]

    # Adding an exact unicode_exception + accepted_human decision resolves it cleanly.
    non_nfc_asr = next(a for a in read_rows(ws / "assertions.csv") if a["value_json"] == non_nfc)
    ev_for_non_nfc = [e for e in read_rows(ws / "evidence.csv") if e["assertion_id"] == non_nfc_asr["assertion_id"]]
    dec_row = {
        "decision_id": "dec_ws_non_nfc",
        "assertion_id": non_nfc_asr["assertion_id"],
        "assertion_revision_sha256": non_nfc_asr["claim_revision_sha256"],
        "evidence_bundle_sha256": review.evidence_hash(ev_for_non_nfc),
        "outcome": "accepted_human",
        "actor_type": "human",
        "actor_id": "rev_1",
        "method_version": None,
        "decision_date": "2026-11-14",
        "note_json": "preserve non-NFC",
        "predecessor_decision_id": None,
    }
    exc_row = {
        "assertion_id": non_nfc_asr["assertion_id"],
        "claim_revision_sha256": non_nfc_asr["claim_revision_sha256"],
        "value_sha256": _sha256_text(non_nfc),
        "kind": "non_nfc_original",
        "scalar_sequence": [ord(c) for c in non_nfc],
        "scalar_position": 0,
        "reason_json": "verified original spelling",
        "decision_id": "dec_ws_non_nfc",
    }
    write_rows(ws / "decisions.csv", "decisions", [dec_row], source_root=source)
    write_rows(ws / "unicode_exceptions.csv", "unicode_exceptions", [exc_row], source_root=source)
    assert check_curated_csv(ws, canonical)["findings"] == []

    # Stale exception (wrong value_sha256) must fail.
    write_rows(ws / "unicode_exceptions.csv", "unicode_exceptions", [dict(exc_row, value_sha256=ZERO_SHA)], source_root=source)
    assert check_curated_csv(ws, canonical)["findings"]

    # Restore valid exception, then break a projection reference (dangling pos_assertion_id) -> must fail.
    write_rows(ws / "unicode_exceptions.csv", "unicode_exceptions", [exc_row], source_root=source)
    entries = list(read_rows(ws / "entries.csv"))
    write_rows(ws / "entries.csv", "entries", [dict(entries[0], pos_assertion_id="ast_dangling"), *entries[1:]], source_root=source)
    assert check_curated_csv(ws, canonical)["findings"]


def test_scopes_register_not_applicable_decoded_csv_roundtrip_and_schema_guards(tmp_path):
    """Schema allows state='not_applicable' strictly for register with null label_code."""
    tables = _make_valid_tables()
    na_scope = {
        "subject_kind": "sense",
        "subject_id": "sns_1",
        "dimension": "register",
        "state": "not_applicable",
        "label_code": None,
        "supporting_assertion_id": None,
        "decision_id": None,
    }
    scopes_path = tmp_path / "scopes.csv"
    write_rows(scopes_path, "scopes", [na_scope])
    roundtripped = list(read_rows(scopes_path, "scopes"))
    assert roundtripped == [na_scope]
    tables["scopes"] = roundtripped
    assert validate_relations(tables) == []

    # Non-register dimensions must be rejected by review.schema.json.
    with pytest.raises(LexiconError):
        write_rows(
            tmp_path / "bad_dim_scopes.csv",
            "scopes",
            [dict(na_scope, dimension="region")],
        )

    # Non-null label_code on not_applicable must be rejected by review.schema.json.
    with pytest.raises(LexiconError):
        write_rows(
            tmp_path / "bad_lbl_scopes.csv",
            "scopes",
            [dict(na_scope, label_code="formal")],
        )
