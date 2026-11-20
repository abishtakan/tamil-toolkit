"""Tests-first suite for T042/T043 offline CLDF 1.3 schema pinning, export, and roundtrip."""

from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import shutil
import socket
import sys
import unicodedata
import urllib.request

import jsonschema
import pycldf
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import lexicon, lexicon_cldf, lexicon_review, lexicon_tables  # noqa: E402

SCHEMA_DIR = ROOT / "schemas" / "lexicon" / "cldf"
SHA_MANIFEST = SCHEMA_DIR / "cldf-1.3.sha256.json"
REPORT_SCHEMA = SCHEMA_DIR / "cldf-export-report.schema.json"

ZWJ = chr(0x200D)
BOM = chr(0xFEFF)


def _ev_sha(evidence_rows: list[dict]) -> str:
    return lexicon_review.evidence_hash(evidence_rows)


def _make_assertion(
    aid: str,
    subject_kind: str,
    subject_id: str,
    property_code: str,
    value,
    *,
    value_state: str = "known",
    origin: str = "verbatim_source",
    fidelity: str = "verified",
    ambiguity: str = "unambiguous",
    convention: str = "unicode-nfc-v1",
    imported_status=None,
    imported_confidence=None,
) -> dict:
    row = {
        "assertion_id": aid,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "property_code": property_code,
        "value_state": value_state,
        "value_json": value,
        "origin": origin,
        "source_fidelity_state": fidelity,
        "ambiguity_state": ambiguity,
        "algorithm_reference": None,
        "convention_reference": convention,
        "imported_status_json": imported_status,
        "imported_confidence_json": imported_confidence,
        "claim_revision_sha256": "",
    }
    row["claim_revision_sha256"] = lexicon_review.claim_revision(row)
    return row


def _make_evidence(
    aid: str,
    source_id: str,
    record_id: str,
    locator: str,
    *,
    role: str = "supports",
) -> dict:
    return {
        "assertion_id": aid,
        "source_id": source_id,
        "source_record_id": record_id,
        "locator_json": locator,
        "evidence_role": role,
        "extraction_version": "cldf-test-1",
        "extraction_sha256": hashlib.sha256(f"{aid}:{source_id}:{record_id}:{locator}".encode("utf-8")).hexdigest(),
    }


def _make_decision(
    did: str,
    assertion: dict,
    ev_rows: list[dict],
    *,
    outcome: str = "accepted_auto_source",
    actor_type: str = "automated",
    actor_id: str | None = None,
    date: str = "2026-11-14",
    note: str = "",
) -> dict:
    matching = [row for row in ev_rows if row["assertion_id"] == assertion["assertion_id"]]
    return {
        "decision_id": did,
        "assertion_id": assertion["assertion_id"],
        "assertion_revision_sha256": assertion["claim_revision_sha256"],
        "evidence_bundle_sha256": _ev_sha(matching),
        "outcome": outcome,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "method_version": "review-v1",
        "decision_date": date,
        "note_json": note,
        "predecessor_decision_id": None,
    }


def _write_canonical_fixture(
    root: pathlib.Path,
    *,
    pack: str = "core",
    eligible: bool = True,
    with_zwj_exception: bool = True,
    empty_pack: bool = False,
) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    notices_dir = root / "notices"
    notices_dir.mkdir(parents=True, exist_ok=True)
    notice_rel = "notices/source-attribution.md"
    notice_bytes = (
        b"# Source Attribution\n\n"
        b"- Synthetic verified source (CC-BY-SA-4.0) for offline CLDF harness tests.\n"
    )
    (root / notice_rel).write_bytes(notice_bytes)
    notice_sha = hashlib.sha256(notice_bytes).hexdigest()

    snap_sha = hashlib.sha256(b"synthetic-snapshot-v1\n").hexdigest()
    rec1_sha = hashlib.sha256(b"rec-1\n").hexdigest()
    rec2_sha = hashlib.sha256(b"rec-2\n").hexdigest()
    rev1_sha = hashlib.sha256(b"ent:ta.001:rev1").hexdigest()
    rev2_sha = hashlib.sha256(b"ent:ta.002:rev1").hexdigest()

    src_id = "src:wikt.2026:1"
    sources = [
        {
            "source_id": src_id,
            "label_json": "Synthetic Wiktionary Entry",
            "publication_json": "Synthetic Tamil Dictionary",
            "url_json": "https://example.org/wikt/1",
            "edition_json": "2026-11-14",
            "locator_json": "line 10",
            "snapshot_id": "snap:wikt.1",
            "retrieval_date_state": "known",
            "retrieval_date_json": "2026-11-14",
            "extraction_method": "csv_parser",
            "extraction_version": "v1",
            "evidence_verification_state": "verified",
            "reuse_basis_json": "CC-BY-SA-4.0",
            "reuse_state": "permitted",
            "attribution_text_json": "Synthetic Contributor Group (CC-BY-SA-4.0)",
            "attribution_reference_json": notice_rel,
        }
    ]

    hw1 = "\u0b85\u0bb1\u0bae\u0bcd"
    hw2 = unicodedata.normalize("NFD", "\u0b95\u0bca\u0bb3\u0bcd") if with_zwj_exception else "\u0b95\u0bca\u0bb3\u0bcd"
    zwj_gloss = f"take{ZWJ}hold" if with_zwj_exception else "take"

    a_form1 = _make_assertion(
        "asrt:form.1",
        "form",
        "frm:ta.001.w",
        "written_form",
        hw1,
        imported_status="imported_ok",
        imported_confidence=0.95,
    )
    a_rom1 = _make_assertion(
        "asrt:form.1.rom",
        "form",
        "frm:ta.001.rom",
        "romanization",
        "aram",
    )
    a_conv1 = _make_assertion(
        "asrt:conv.1",
        "form",
        "frm:ta.001.rom",
        "transliteration_convention",
        "ISO-15919",
    )
    a_pos1 = _make_assertion(
        "asrt:pos.1",
        "entry",
        "ent:ta.001",
        "part_of_speech",
        "noun",
    )
    a_gloss1 = _make_assertion(
        "asrt:txt.1",
        "text",
        "txt:ta.001.s1.gloss",
        "gloss",
        "virtue; moral law",
    )
    a_gloss1_sub = _make_assertion(
        "asrt:txt.1b",
        "text",
        "txt:ta.001.s2.def",
        "definition",
        "righteous conduct",
    )
    a_ex1 = _make_assertion(
        "asrt:txt.ex1",
        "text",
        "txt:ta.001.s1.ex",
        "example",
        "\u0b85\u0bb1\u0bae\u0bcd \u0b9a\u0bc6\u0baf\u0bcd",
    )
    a_tr1 = _make_assertion(
        "asrt:txt.tr1",
        "text",
        "txt:ta.001.s1.tr",
        "translation",
        "Do virtuous deeds.",
    )
    a_form2 = _make_assertion(
        "asrt:form.2",
        "form",
        "frm:ta.002.w",
        "written_form",
        hw2,
        origin="correction" if with_zwj_exception else "verbatim_source",
        convention="unicode-nfd-exception-v1" if with_zwj_exception else "unicode-nfc-v1",
    )
    a_pos2 = _make_assertion(
        "asrt:pos.2",
        "entry",
        "ent:ta.002",
        "part_of_speech",
        None,
        value_state="unknown",
        origin="verbatim_source",
    )
    a_gloss2 = _make_assertion(
        "asrt:txt.2",
        "text",
        "txt:ta.002.s1.gloss",
        "gloss",
        zwj_gloss,
        origin="verbatim_source",
    )
    a_rel = _make_assertion(
        "asrt:rel.1",
        "relation",
        "rel:ta.001.002",
        "relation_code",
        "related_concept",
    )
    a_scope1 = _make_assertion(
        "asrt:scope.1",
        "entry",
        "ent:ta.002",
        "region_scope",
        "jaffna",
    )

    assertions = [
        a_form1,
        a_rom1,
        a_conv1,
        a_pos1,
        a_gloss1,
        a_gloss1_sub,
        a_ex1,
        a_tr1,
        a_form2,
        a_pos2,
        a_gloss2,
        a_rel,
        a_scope1,
    ]

    evidence = [
        _make_evidence(a["assertion_id"], src_id, "rec:001" if idx % 2 == 0 else "rec:002", f"page {idx + 1}; [col]")
        for idx, a in enumerate(assertions)
    ]

    decisions = []
    unicode_exceptions = []
    for idx, a in enumerate(assertions):
        aid = a["assertion_id"]
        if not eligible:
            decisions.append(
                _make_decision(
                    f"dec:{idx}",
                    a,
                    evidence,
                    outcome="pending",
                    actor_type="automated",
                    actor_id=None,
                )
            )
            continue

        if aid in {"asrt:form.2", "asrt:txt.2"} and with_zwj_exception:
            did = f"dec:{idx}"
            decisions.append(
                _make_decision(
                    did,
                    a,
                    evidence,
                    outcome="accepted_human",
                    actor_type="human",
                    actor_id="curator:sa",
                    note="Verified intentional joiner / original NFD citation" + ("\t[ok]" if aid == "asrt:txt.2" else ""),
                )
            )
            if aid == "asrt:form.2":
                unicode_exceptions.append(
                    {
                        "assertion_id": aid,
                        "claim_revision_sha256": a["claim_revision_sha256"],
                        "value_sha256": hashlib.sha256(hw2.encode("utf-8")).hexdigest(),
                        "kind": "non_nfc_original",
                        "scalar_sequence": [ord(c) for c in hw2],
                        "scalar_position": 0,
                        "reason_json": "Historical NFD witness preserved verbatim",
                        "decision_id": did,
                    }
                )
            else:
                unicode_exceptions.append(
                    {
                        "assertion_id": aid,
                        "claim_revision_sha256": a["claim_revision_sha256"],
                        "value_sha256": hashlib.sha256(zwj_gloss.encode("utf-8")).hexdigest(),
                        "kind": "intentional_control",
                        "scalar_sequence": [ord(ZWJ)],
                        "scalar_position": zwj_gloss.index(ZWJ),
                        "reason_json": "Intentional ZWJ control preserved for roundtrip check",
                        "decision_id": did,
                    }
                )
        elif a["value_state"] == "unknown":
            decisions.append(
                _make_decision(
                    f"dec:{idx}",
                    a,
                    evidence,
                    outcome="accepted_human",
                    actor_type="human",
                    actor_id="curator:sa",
                    note="POS unattested in source",
                )
            )
        else:
            decisions.append(
                _make_decision(
                    f"dec:{idx}",
                    a,
                    evidence,
                    outcome="accepted_auto_source",
                    actor_type="automated",
                    actor_id=None,
                )
            )

    identities = [
        {"entity_id": "ent:ta.001", "kind": "entry", "allocation_key": "ta::aram::1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "ent:ta.002", "kind": "entry", "allocation_key": "ta::kol::1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "frm:ta.001.w", "kind": "form", "allocation_key": "frm::1::w", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "frm:ta.001.rom", "kind": "form", "allocation_key": "frm::1::rom", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "frm:ta.002.w", "kind": "form", "allocation_key": "frm::2::w", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "sns:ta.001.1", "kind": "sense", "allocation_key": "sns::1::1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "sns:ta.001.2", "kind": "sense", "allocation_key": "sns::1::2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "sns:ta.002.1", "kind": "sense", "allocation_key": "sns::2::1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "txt:ta.001.s1.gloss", "kind": "text", "allocation_key": "txt::1::s1::g", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "txt:ta.001.s2.def", "kind": "text", "allocation_key": "txt::1::s2::d", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "txt:ta.001.s1.tr", "kind": "text", "allocation_key": "txt::1::s1::tr", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "txt:ta.001.s1.ex", "kind": "text", "allocation_key": "txt::1::s1::ex", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "txt:ta.002.s1.gloss", "kind": "text", "allocation_key": "txt::2::s1::g", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": "rel:ta.001.002", "kind": "relation", "allocation_key": "rel::1::2", "lifecycle": "active", "identity_decision_id": None},
    ]

    tables = {
        "snapshots": [
            {
                "snapshot_id": "snap:wikt.1",
                "dataset_id": "wiktionary-synthetic",
                "relative_path": "wiktionary/synthetic.csv",
                "byte_length": 22,
                "sha256": snap_sha,
                "media_type": "text/csv",
                "logical_row_count": 2,
            }
        ],
        "sources": sources,
        "identities": identities,
        "source_records": [
            {
                "record_id": "rec:001",
                "snapshot_id": "snap:wikt.1",
                "ordinal": 2,
                "physical_line_start": 2,
                "physical_line_end": 2,
                "legacy_key_json": "1",
                "raw_row_sha256": rec1_sha,
            },
            {
                "record_id": "rec:002",
                "snapshot_id": "snap:wikt.1",
                "ordinal": 3,
                "physical_line_start": 3,
                "physical_line_end": 3,
                "legacy_key_json": "2",
                "raw_row_sha256": rec2_sha,
            },
        ],
        "dispositions": [],
        "record_targets": [],
        "entries": [] if empty_pack else [
            {
                "entry_id": "ent:ta.001",
                "language_id": "ta",
                "variety_id": None,
                "canonical_form_id": "frm:ta.001.w",
                "pos_assertion_id": "asrt:pos.1",
                "structural_kind": "lexical_entry",
                "revision": rev1_sha,
            },
            {
                "entry_id": "ent:ta.002",
                "language_id": "ta",
                "variety_id": "ta-LK-jaffna",
                "canonical_form_id": "frm:ta.002.w",
                "pos_assertion_id": "asrt:pos.2",
                "structural_kind": "homograph",
                "revision": rev2_sha,
            },
        ],
        "forms": [] if empty_pack else [
            {
                "form_id": "frm:ta.001.w",
                "entry_id": "ent:ta.001",
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": "asrt:form.1",
                "convention_assertion_id": None,
            },
            {
                "form_id": "frm:ta.001.rom",
                "entry_id": "ent:ta.001",
                "representation": "romanization",
                "role": "variant",
                "text_assertion_id": "asrt:form.1.rom",
                "convention_assertion_id": "asrt:conv.1",
            },
            {
                "form_id": "frm:ta.002.w",
                "entry_id": "ent:ta.002",
                "representation": "written",
                "role": "canonical",
                "text_assertion_id": "asrt:form.2",
                "convention_assertion_id": None,
            },
        ],
        "senses": [] if empty_pack else [
            {
                "sense_id": "sns:ta.001.1",
                "entry_id": "ent:ta.001",
                "display_order": 1,
                "parent_sense_id": None,
            },
            {
                "sense_id": "sns:ta.001.2",
                "entry_id": "ent:ta.001",
                "display_order": 2,
                "parent_sense_id": "sns:ta.001.1",
            },
            {
                "sense_id": "sns:ta.002.1",
                "entry_id": "ent:ta.002",
                "display_order": 1,
                "parent_sense_id": None,
            },
        ],
        "texts": [] if empty_pack else [
            {
                "text_id": "txt:ta.001.s1.gloss",
                "owner_kind": "sense",
                "owner_id": "sns:ta.001.1",
                "component": "gloss",
                "language_id": "en",
                "text_assertion_id": "asrt:txt.1",
                "paired_translation_id": None,
                "cited_source_locator_json": "line 10",
            },
            {
                "text_id": "txt:ta.001.s2.def",
                "owner_kind": "sense",
                "owner_id": "sns:ta.001.2",
                "component": "definition",
                "language_id": "en",
                "text_assertion_id": "asrt:txt.1b",
                "paired_translation_id": None,
                "cited_source_locator_json": "line 11",
            },
            {
                "text_id": "txt:ta.001.s1.tr",
                "owner_kind": "sense",
                "owner_id": "sns:ta.001.1",
                "component": "translation",
                "language_id": "en",
                "text_assertion_id": "asrt:txt.tr1",
                "paired_translation_id": None,
                "cited_source_locator_json": "line 12",
            },
            {
                "text_id": "txt:ta.001.s1.ex",
                "owner_kind": "sense",
                "owner_id": "sns:ta.001.1",
                "component": "example",
                "language_id": "ta",
                "text_assertion_id": "asrt:txt.ex1",
                "paired_translation_id": "txt:ta.001.s1.tr",
                "cited_source_locator_json": "line 12",
            },
            {
                "text_id": "txt:ta.002.s1.gloss",
                "owner_kind": "sense",
                "owner_id": "sns:ta.002.1",
                "component": "gloss",
                "language_id": "en",
                "text_assertion_id": "asrt:txt.2",
                "paired_translation_id": None,
                "cited_source_locator_json": "line 20",
            },
        ],
        "relations": [] if empty_pack else [
            {
                "relation_id": "rel:ta.001.002",
                "source_kind": "sense",
                "source_id": "sns:ta.001.1",
                "target_kind": "entry",
                "target_id": "ent:ta.002",
                "relation_code_assertion_id": "asrt:rel.1",
                "directionality": "undirected",
                "inverse_relation_id": None,
            }
        ],
        "assertions": [] if empty_pack else assertions,
        "evidence": [] if empty_pack else evidence,
        "decisions": [] if empty_pack else decisions,
        "changes": [],
        "successors": [],
        "findings": [],
        "unicode_exceptions": [] if empty_pack else unicode_exceptions,
        "labels": [
            {
                "registry_id": "reg:region",
                "registry_version": "1.0.0",
                "code": "unrestricted",
                "category": "region",
                "display_label_json": "Unrestricted",
                "definition_json": "No regional restriction",
                "evidence_reference": "ref:region:0",
                "parent_code": None,
            },
            {
                "registry_id": "reg:region",
                "registry_version": "1.0.0",
                "code": "jaffna",
                "category": "region",
                "display_label_json": "Jaffna Tamil",
                "definition_json": "Northern Sri Lankan Tamil variety",
                "evidence_reference": "ref:region:1",
                "parent_code": "unrestricted",
            },
            {
                "registry_id": "reg:pos",
                "registry_version": "1.0.0",
                "code": "noun",
                "category": "grammar_system",
                "display_label_json": "Noun",
                "definition_json": "Nominal grammatical category",
                "evidence_reference": "ref:pos:1",
                "parent_code": None,
            },
        ],
        "scopes": [] if empty_pack else [
            {
                "subject_kind": "entry",
                "subject_id": "ent:ta.002",
                "dimension": "region",
                "state": "attested",
                "label_code": "jaffna",
                "supporting_assertion_id": "asrt:scope.1",
                "decision_id": decisions[-1]["decision_id"],
            }
        ],
        "pack_members": [] if empty_pack else [
            {
                "pack_id": pack,
                "entry_id": "ent:ta.001",
                "included_revision": rev1_sha,
                "relation_inclusion_policy": "same_pack_only",
            },
            {
                "pack_id": pack,
                "entry_id": "ent:ta.002",
                "included_revision": rev2_sha,
                "relation_inclusion_policy": "same_pack_only",
            },
        ],
    }

    for tname, rows in tables.items():
        lexicon_tables.write_rows(root / f"{tname}.csv", tname, rows, source_root=lexicon.SOURCE)

    vocab_toml = (
        'schema_version = "lexicon-vocab-v1"\n\n'
        '[registries."reg:region"]\n'
        'version = "1.0.0"\n'
        'codes = ["jaffna"]\n\n'
        '[registries."reg:pos"]\n'
        'version = "1.0.0"\n'
        'codes = ["noun"]\n'
    )
    (root / "vocabularies.toml").write_text(vocab_toml, encoding="utf-8", newline="\n")

    eligible_count = (
        len([
            a for a in assertions
            if a["value_state"] == "known"
            and any(d["assertion_id"] == a["assertion_id"] and d["outcome"] in lexicon_tables.ACCEPTED_OUTCOMES for d in decisions)
        ])
        if not empty_pack
        else 0
    )
    packs_toml = (
        'schema_version = "lexicon-packs-v1"\n'
        'dataset_version = "0.1.0-synthetic"\n'
        f'vocabularies_sha256 = "{hashlib.sha256(vocab_toml.encode("utf-8")).hexdigest()}"\n\n'
        f'[packs.{pack}]\n'
        f'pack_id = "{pack}"\n'
        'dataset_version = "0.1.0-synthetic"\n'
        f'eligible_assertions = {eligible_count}\n'
        f'entry_count = {0 if empty_pack else 2}\n'
        f'attribution_notices = ["{notice_rel}"]\n'
        f'notice_sha256 = {{ "{notice_rel}" = "{notice_sha}" }}\n'
    )
    (root / "packs.toml").write_text(packs_toml, encoding="utf-8", newline="\n")
    return root


def test_t042_pinned_cldf_schemas_and_digests_valid(tmp_path: pathlib.Path) -> None:
    manifest = json.loads(SHA_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["cldf_version"] == "1.3"
    assert manifest["validator_pins"] == {"pycldf": "2.2.0", "csvw": "4.2.0"}
    assert "v1.3/modules/Dictionary-metadata.json" in manifest["files"]
    assert "v1.3/terms.rdf" in manifest["files"]
    assert lexicon_cldf.verify_cldf_schemas() == {
        "cldf_version": "1.3",
        "schema_manifest_sha256": hashlib.sha256(SHA_MANIFEST.read_bytes()).hexdigest(),
        "validator_pins": {"pycldf": "2.2.0", "csvw": "4.2.0"},
        "file_count": len(manifest["files"]),
    }

    # Tampering a local schema copy must fail closed.
    bad_dir = tmp_path / "schemas"
    shutil.copytree(SCHEMA_DIR, bad_dir)
    md = bad_dir / "v1.3" / "modules" / "Dictionary-metadata.json"
    md.write_text(md.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(lexicon.LexiconError) as exc:
        lexicon_cldf.verify_cldf_schemas(bad_dir)
    assert exc.value.code == 2


def test_t043_export_cldf_check_positive_offline_and_roundtrip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    canonical = _write_canonical_fixture(tmp_path / "canonical", pack="core", eligible=True)
    out_a = tmp_path / "cldf_a"
    out_b = tmp_path / "cldf_b"
    report_path = tmp_path / "cldf-report.json"

    def deny_network(*_args, **_kwargs):
        raise RuntimeError("network disabled for offline CLDF validation")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(urllib.request, "urlopen", deny_network)

    report_a = lexicon_cldf.export_cldf(
        canonical=canonical,
        pack="core",
        output=out_a,
        check=True,
        report_output=report_path,
    )
    report_b = lexicon_cldf.export_cldf(
        canonical=canonical,
        pack="core",
        output=out_b,
        check=True,
    )

    assert report_a["l2_structural_accepted"] is False
    assert report_a["l3_pack_eligible"] is True
    assert report_a["runtime_verified"] is None
    assert report_a["cldf_valid"] is True
    assert report_a["roundtrip_ok"] is True
    assert report_a["cldf_version"] == "1.3"
    assert report_a["eligible_assertions"] > 0
    assert report_a["findings"] == []
    assert report_a["export_sha256"] == report_b["export_sha256"]

    schema_obj = json.loads(REPORT_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(instance=json.loads(report_path.read_text(encoding="utf-8")), schema=schema_obj)

    # Byte-for-byte deterministic output across identical runs.
    files_a = {p.relative_to(out_a).as_posix(): p.read_bytes() for p in sorted(out_a.rglob("*")) if p.is_file()}
    files_b = {p.relative_to(out_b).as_posix(): p.read_bytes() for p in sorted(out_b.rglob("*")) if p.is_file()}
    assert files_a == files_b
    for rel, raw in files_a.items():
        assert not raw.startswith(b"\xef\xbb\xbf"), f"Unexpected UTF-8 BOM in {rel}"
        assert b"\r\n" not in raw, f"Unexpected CRLF in {rel}"

    # Verify real pycldf validation offline with pinned local terms.rdf.
    ds = pycldf.Dataset.from_metadata(out_a / "Dictionary-metadata.json")
    assert ds.module == "Dictionary"
    assert ds.validate(ontology_path=SCHEMA_DIR / "v1.3" / "terms.rdf") is True

    # Verify exact preservation of IDs ('.', ':'), ZWJ, NFD, unknown POS, null actor_id, and notices.
    entry_rows = {row["ID"]: row for row in ds["EntryTable"]}
    sense_rows = {row["ID"]: row for row in ds["SenseTable"]}
    assert entry_rows["ent:ta.001"]["Part_Of_Speech"] == "noun"
    assert entry_rows["ent:ta.001"]["POS_Value_State"] == "known"
    assert entry_rows["ent:ta.002"]["Headword"] == unicodedata.normalize("NFD", "\u0b95\u0bca\u0bb3\u0bcd")
    assert entry_rows["ent:ta.002"]["Part_Of_Speech"] is None
    assert entry_rows["ent:ta.002"]["POS_Value_State"] == "unknown"
    assert entry_rows["ent:ta.002"]["Variety_ID"] == "ta-LK-jaffna"
    assert sense_rows["sns:ta.002.1"]["Description"] == f"take{ZWJ}hold"
    assert (out_a / "notices" / "source-attribution.md").read_bytes() == (canonical / "notices" / "source-attribution.md").read_bytes()

    # Re-running onto an unchanged existing output dir is idempotent.
    report_again = lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=out_a, check=True)
    assert report_again["export_sha256"] == report_a["export_sha256"]


def test_t043_rejects_quarantined_and_empty_packs_with_eligibility_failure(tmp_path: pathlib.Path) -> None:
    quarantined = _write_canonical_fixture(tmp_path / "quarantined", pack="core", eligible=False)
    out_q = tmp_path / "out_q"
    rep_q = tmp_path / "rep_q.json"
    code = lexicon_cldf.main(
        ["--canonical", str(quarantined), "--pack", "core", "--output", str(out_q), "--check", "--report-output", str(rep_q)]
    )
    assert code == 1
    assert not out_q.exists()
    rep = json.loads(rep_q.read_text(encoding="utf-8"))
    assert rep["l3_pack_eligible"] is False
    assert any(f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" for f in rep["findings"])

    empty_dir = _write_canonical_fixture(tmp_path / "empty_pack", pack="terminology", empty_pack=True)
    out_e = tmp_path / "out_e"
    rep_e = tmp_path / "rep_e.json"
    code_e = lexicon_cldf.main(
        ["--canonical", str(empty_dir), "--pack", "terminology", "--output", str(out_e), "--check", "--report-output", str(rep_e)]
    )
    assert code_e == 1
    assert not out_e.exists()
    assert json.loads(rep_e.read_text(encoding="utf-8"))["l3_pack_eligible"] is False


def test_t043_safety_overlap_conflict_and_no_imported_approval_transfer(tmp_path: pathlib.Path) -> None:
    canonical = _write_canonical_fixture(tmp_path / "canonical", pack="core", eligible=True)
    out = tmp_path / "out"
    lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=out, check=True)

    # Output overlapping canonical or SOURCE fails with exit 2.
    with pytest.raises(lexicon.LexiconError) as exc_overlap:
        lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=canonical / "cldf", check=True)
    assert exc_overlap.value.code == 2

    with pytest.raises(lexicon.LexiconError) as exc_source:
        lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=lexicon.SOURCE / "cldf_bad", check=True)
    assert exc_source.value.code == 2

    # Conflicting manual edit in existing output must never be silently overwritten.
    (out / "sources.bib").write_text("% manually edited\n", encoding="utf-8")
    with pytest.raises(lexicon.LexiconError) as exc_conflict:
        lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=out, check=True)
    assert exc_conflict.value.code == 2

    # Imported status/confidence cannot bypass missing decision approval.
    tampered_canon = _write_canonical_fixture(tmp_path / "tampered_import", pack="core", eligible=True)
    dec_rows = [r for r in lexicon_tables.read_rows(tampered_canon / "decisions.csv", "decisions") if r["assertion_id"] != "asrt:form.1"]
    lexicon_tables.write_rows(tampered_canon / "decisions.csv", "decisions", dec_rows, source_root=lexicon.SOURCE)
    out_imp = tmp_path / "out_imp"
    rep_imp = tmp_path / "rep_imp.json"
    code = lexicon_cldf.main(
        ["--canonical", str(tampered_canon), "--pack", "core", "--output", str(out_imp), "--check", "--report-output", str(rep_imp)]
    )
    assert code == 1
    assert not out_imp.exists()
    assert json.loads(rep_imp.read_text(encoding="utf-8"))["l3_pack_eligible"] is False


def test_t043_cldf_validation_and_roundtrip_reject_metadata_fk_source_review_and_control_tamper(
    tmp_path: pathlib.Path,
) -> None:
    canonical = _write_canonical_fixture(tmp_path / "canonical", pack="core", eligible=True)
    base_out = tmp_path / "cldf_base"
    lexicon_cldf.export_cldf(canonical=canonical, pack="core", output=base_out, check=True)
    trusted = lexicon_cldf.load_trusted_canonical(canonical, "core")

    # 1. Bad CSVW metadata
    bad_meta = tmp_path / "bad_meta"
    shutil.copytree(base_out, bad_meta)
    meta = json.loads((bad_meta / "Dictionary-metadata.json").read_text(encoding="utf-8"))
    meta["dc:conformsTo"] = "http://cldf.clld.org/v1.0/terms.rdf#Generic"
    (bad_meta / "Dictionary-metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    res_meta = lexicon_cldf.verify_cldf_export(bad_meta, trusted)
    assert res_meta["cldf_valid"] is False

    # 2. Broken FK in senses.csv (nonexistent Entry_ID)
    bad_fk = tmp_path / "bad_fk"
    shutil.copytree(base_out, bad_fk)
    senses_txt = (bad_fk / "senses.csv").read_text(encoding="utf-8").replace("ent:ta.001", "ent:missing.999")
    (bad_fk / "senses.csv").write_text(senses_txt, encoding="utf-8", newline="\n")
    res_fk = lexicon_cldf.verify_cldf_export(bad_fk, trusted)
    assert res_fk["cldf_valid"] is False

    # 3. Missing BibTeX source reference in sources.bib
    bad_bib = tmp_path / "bad_bib"
    shutil.copytree(base_out, bad_bib)
    (bad_bib / "sources.bib").write_text("", encoding="utf-8")
    res_bib = lexicon_cldf.verify_cldf_export(bad_bib, trusted)
    assert res_bib["cldf_valid"] is False

    # 4. Tampered decision in CLDF decisions.csv must be rejected by roundtrip check
    bad_rev = tmp_path / "bad_rev"
    shutil.copytree(base_out, bad_rev)
    dec_csv = (bad_rev / "decisions.csv").read_text(encoding="utf-8").replace("accepted_auto_source", "accepted_human", 1)
    (bad_rev / "decisions.csv").write_text(dec_csv, encoding="utf-8", newline="\n")
    res_rev = lexicon_cldf.verify_cldf_export(bad_rev, trusted)
    assert res_rev["roundtrip_ok"] is False

    # 5. Control / ZWJ tampering in exported CLDF senses.csv and NFD->NFC tampering in entries.csv must be rejected
    bad_ctl = tmp_path / "bad_ctl"
    shutil.copytree(base_out, bad_ctl)
    sns_csv = (bad_ctl / "senses.csv").read_text(encoding="utf-8").replace(f"take{ZWJ}hold", "takehold")
    assert sns_csv != (bad_ctl / "senses.csv").read_text(encoding="utf-8")
    (bad_ctl / "senses.csv").write_text(sns_csv, encoding="utf-8", newline="\n")
    res_ctl = lexicon_cldf.verify_cldf_export(bad_ctl, trusted)
    assert res_ctl["roundtrip_ok"] is False

    bad_nfd = tmp_path / "bad_nfd"
    shutil.copytree(base_out, bad_nfd)
    nfd_str = unicodedata.normalize("NFD", "\u0b95\u0bca\u0bb3\u0bcd")
    ent_csv = (bad_nfd / "entries.csv").read_text(encoding="utf-8").replace(nfd_str, "\u0b95\u0bca\u0bb3\u0bcd")
    assert ent_csv != (bad_nfd / "entries.csv").read_text(encoding="utf-8")
    (bad_nfd / "entries.csv").write_text(ent_csv, encoding="utf-8", newline="\n")
    res_nfd = lexicon_cldf.verify_cldf_export(bad_nfd, trusted)
    assert res_nfd["roundtrip_ok"] is False

    # 6. Tampered notice file must be rejected
    bad_notice = tmp_path / "bad_notice"
    shutil.copytree(base_out, bad_notice)
    (bad_notice / "notices" / "source-attribution.md").write_text("tampered notice\n", encoding="utf-8")
    res_notice = lexicon_cldf.verify_cldf_export(bad_notice, trusted)
    assert res_notice["roundtrip_ok"] is False


def test_t043_canonical_validator_dependency_injection(tmp_path: pathlib.Path) -> None:
    canonical = _write_canonical_fixture(tmp_path / "canonical", pack="core", eligible=True)
    out = tmp_path / "out_hook"

    def rejecting_validator(_canon_dir: pathlib.Path, _pack: str) -> dict:
        return {
            "l2_structural_accepted": True,
            "l3_pack_eligible": False,
            "findings": [
                {
                    "code": "UPSTREAM_PACK_REJECTED",
                    "severity": "error",
                    "entity_id": "core",
                    "field": "pack_members",
                    "reason": "Synthetic pack validator rejected pack eligibility",
                }
            ],
        }

    rep = lexicon_cldf.export_cldf(
        canonical=canonical,
        pack="core",
        output=out,
        check=True,
        canonical_validator=rejecting_validator,
    )
    assert rep["l3_pack_eligible"] is False
    assert not out.exists()
    assert any(f["code"] == "UPSTREAM_PACK_REJECTED" for f in rep["findings"])


def test_t043_cli_exit_codes_and_negative_review_policies(tmp_path: pathlib.Path) -> None:
    # Existing bare directory with no promoted tables must fail closed on eligibility (exit 1), not exit 2.
    bare_dir = tmp_path / "bare_canon"
    bare_dir.mkdir()
    rep_bare = tmp_path / "bare_rep.json"
    out_bare = tmp_path / "out_bare"
    assert lexicon_cldf.main(
        ["--canonical", str(bare_dir), "--pack", "regional", "--output", str(out_bare), "--check", "--report-output", str(rep_bare)]
    ) == 1
    assert any(f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" for f in json.loads(rep_bare.read_text(encoding="utf-8"))["findings"])

    # Invalid pack or missing canonical directory returns exit 2.
    assert lexicon_cldf.main(
        ["--canonical", str(bare_dir), "--pack", "bogus", "--output", str(out_bare), "--check"]
    ) == 2
    assert lexicon_cldf.main(
        ["--canonical", str(tmp_path / "does_not_exist"), "--pack", "core", "--output", str(out_bare), "--check"]
    ) == 2

    # Dropping unicode_exceptions fails canonical eligibility (exit 1).
    no_exc = _write_canonical_fixture(tmp_path / "no_exc", pack="core", eligible=True, with_zwj_exception=True)
    lexicon_tables.write_rows(no_exc / "unicode_exceptions.csv", "unicode_exceptions", [], source_root=lexicon.SOURCE)
    rep_exc = lexicon_cldf.export_cldf(canonical=no_exc, pack="core", output=tmp_path / "out_no_exc", check=True)
    assert rep_exc["l3_pack_eligible"] is False

    # accepted_auto_source on inferred claim must fail eligibility even with valid hashes.
    inferred = _write_canonical_fixture(tmp_path / "inferred", pack="core", eligible=True, with_zwj_exception=False)
    asrt_rows = list(lexicon_tables.read_rows(inferred / "assertions.csv", "assertions"))
    ev_rows = list(lexicon_tables.read_rows(inferred / "evidence.csv", "evidence"))
    dec_rows = list(lexicon_tables.read_rows(inferred / "decisions.csv", "decisions"))
    for a in asrt_rows:
        if a["assertion_id"] == "asrt:form.1":
            a["origin"] = "inferred"
            a["claim_revision_sha256"] = lexicon_review.claim_revision(a)
            for d in dec_rows:
                if d["assertion_id"] == "asrt:form.1":
                    d["assertion_revision_sha256"] = a["claim_revision_sha256"]
                    d["evidence_bundle_sha256"] = _ev_sha([e for e in ev_rows if e["assertion_id"] == "asrt:form.1"])
    lexicon_tables.write_rows(inferred / "assertions.csv", "assertions", asrt_rows, source_root=lexicon.SOURCE)
    lexicon_tables.write_rows(inferred / "decisions.csv", "decisions", dec_rows, source_root=lexicon.SOURCE)
    rep_inf = lexicon_cldf.export_cldf(canonical=inferred, pack="core", output=tmp_path / "out_inf", check=True)
    assert rep_inf["l3_pack_eligible"] is False
    assert any(f["code"] == "INELIGIBLE_ASSERTION" and "human_review_required" in f["reason"] for f in rep_inf["findings"])


def test_t043_preserves_control_notes_and_imported_fields_verbatim(tmp_path: pathlib.Path) -> None:
    canonical = _write_canonical_fixture(tmp_path / "canon_ctrl", pack="names_taxa", eligible=True, with_zwj_exception=True)
    out = tmp_path / "out_ctrl"
    rep = lexicon_cldf.export_cldf(canonical=canonical, pack="names_taxa", output=out, check=True)
    assert rep["l3_pack_eligible"] is True
    assert rep["roundtrip_ok"] is True

    assertions_csv = list(csv.DictReader((out / "assertions.csv").open(encoding="utf-8")))
    a1 = next(r for r in assertions_csv if r["assertion_id"] == "asrt:form.1")
    assert json.loads(a1["imported_status_json"]) == "imported_ok"
    assert json.loads(a1["imported_confidence_json"]) == 0.95

    decisions_csv = list(csv.DictReader((out / "decisions.csv").open(encoding="utf-8")))
    d0 = next(r for r in decisions_csv if r["assertion_id"] == "asrt:form.1")
    assert d0["actor_id"] == ""
    d_zwj = next(r for r in decisions_csv if r["assertion_id"] == "asrt:txt.2")
    assert "\t[ok]" in json.loads(d_zwj["note_json"])


def test_t043_promoted_core_wiktionary_reviewed_cldf_roundtrip(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reviewed_ws = ROOT / "data" / "curation" / "wiktionary-core-reviewed"
    assert reviewed_ws.is_dir(), "Required reviewed Wiktionary workspace is missing"

    from tools import lexicon_packs

    canon_dir = tmp_path / "canon_core"
    cldf_dir = tmp_path / "cldf_core"
    report_path = tmp_path / "core-cldf-report.json"

    lexicon_packs.promote(reviewed_ws, pack="core", output=canon_dir)

    def deny_network(*_args, **_kwargs):
        raise RuntimeError("network disabled for offline CLDF validation")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(urllib.request, "urlopen", deny_network)

    rep = lexicon_cldf.export_cldf(
        canonical=canon_dir,
        pack="core",
        output=cldf_dir,
        check=True,
        report_output=report_path,
    )
    assert rep["l2_structural_accepted"] is False
    assert rep["l3_pack_eligible"] is True
    assert rep["cldf_valid"] is True
    assert rep["roundtrip_ok"] is True
    assert rep["eligible_assertions"] == 31
    assert rep["counts"]["entries"] == 6
    assert rep["counts"]["senses"] == 19
    assert rep["findings"] == []
    assert (cldf_dir / "ATTRIBUTION_AND_TERMS.md").is_file()
    assert (cldf_dir / "ATTRIBUTION_AND_TERMS.md").read_bytes() == (canon_dir / "ATTRIBUTION_AND_TERMS.md").read_bytes()

    ds = pycldf.Dataset.from_metadata(cldf_dir / "Dictionary-metadata.json")
    assert ds.validate(ontology_path=SCHEMA_DIR / "v1.3" / "terms.rdf") is True
    nandri = [r for r in ds["EntryTable"] if r["Headword"] == "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf"]
    assert len(nandri) == 2
    assert len({r["Part_Of_Speech"] for r in nandri}) == 2
    assert {r["Language_ID"] for r in ds["EntryTable"]} == {"tam"}

    # Requesting wrong pack against core canonical fails closed on eligibility.
    rep_wrong = lexicon_cldf.export_cldf(
        canonical=canon_dir,
        pack="terminology",
        output=tmp_path / "cldf_wrong",
        check=True,
    )
    assert rep_wrong["l3_pack_eligible"] is False
    assert any(f["code"] == "NONEMPTY_ELIGIBLE_PACK_REQUIRED" for f in rep_wrong["findings"])
def test_referenced_missing_notice_is_not_silently_omitted(tmp_path):
    from tools.lexicon_cldf import _load_notices

    canonical = tmp_path / "canonical"
    canonical.mkdir()
    notices, findings = _load_notices(canonical, {}, [{"attribution_reference_json": "notices/missing.md"}])
    assert notices == {}
    assert any(f["code"] == "MISSING_NOTICE_FILE" for f in findings)


def test_notice_path_cannot_read_outside_canonical_directory(tmp_path):
    from tools.lexicon_cldf import _load_notices

    canonical = tmp_path / "canonical"
    canonical.mkdir()
    (tmp_path / "private.md").write_text("Do not export this unrelated file.", encoding="utf-8")
    notices, findings = _load_notices(canonical, {"attribution_notices": ["../private.md"]}, [])
    assert notices == {}
    assert any(f["code"] == "INVALID_NOTICE_PATH" for f in findings)


@pytest.mark.xdist_group("real_lexicon_packs")
def test_t043_real_lexicon_dictionary_cldf_export_and_notice_closure(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    real_core_canonical_validation: dict,
) -> None:
    canon_dir = real_core_canonical_validation["canon_dir"]
    assert canon_dir == ROOT / "lexicon" / "dictionary"
    assert canon_dir.is_dir(), "Checked-in lexicon/dictionary canonical pack is missing"
    disallowed = [
        p.relative_to(canon_dir).as_posix()
        for p in canon_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".json", ".txt"}
    ]
    assert disallowed == []

    assert real_core_canonical_validation["findings"] == []
    loaded = real_core_canonical_validation["loaded"]
    assert set(loaded["notices"]) == {
        "notices/ATTRIBUTION_AND_LICENSE.md",
        "notices/CC-BY-SA-4.0.md",
    }
    assert loaded["packs"]["dataset_version"] == "0.1.0+a211334e3659"
    assert (
        loaded["packs"]["manifest_sha256"]
        == "a211334e3659647deb4fc30a1c5c6778f4fa9ef98815ed44674a7d5d7dc05bdf"
    )

    def deny_network(*_args, **_kwargs):
        raise RuntimeError("network disabled for offline CLDF validation")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(urllib.request, "urlopen", deny_network)

    validated_findings = real_core_canonical_validation["findings"]

    def reuse_real_validation(canonical_path: pathlib.Path, pack: str) -> dict:
        assert canonical_path == canon_dir
        assert pack == "core"
        return {
            "l3_pack_eligible": not validated_findings,
            "findings": [
                {
                    "code": "CANONICAL_PACK_INVALID",
                    "entity_id": pack,
                    "field": "canonical",
                    "reason": str(err),
                }
                for err in validated_findings
            ],
        }

    cldf_dir = tmp_path / "lexicon_dictionary_cldf"
    report_path = tmp_path / "lexicon-dictionary-cldf-report.json"
    rep = lexicon_cldf.export_cldf(
        canonical=canon_dir,
        pack="core",
        output=cldf_dir,
        check=True,
        report_output=report_path,
        canonical_validator=reuse_real_validation,
    )
    assert rep["dataset_version"] == "0.1.0+a211334e3659"
    assert rep["l2_structural_accepted"] is False
    assert rep["l3_pack_eligible"] is True
    assert rep["cldf_valid"] is True
    assert rep["roundtrip_ok"] is True
    assert rep["eligible_assertions"] == 50718
    assert rep["counts"]["entries"] == 10343
    assert rep["counts"]["senses"] == 23827
    assert rep["counts"]["notices"] == 3
    assert rep["findings"] == []

    for rel in (
        "ATTRIBUTION_AND_TERMS.md",
        "notices/ATTRIBUTION_AND_LICENSE.md",
        "notices/CC-BY-SA-4.0.md",
    ):
        assert (cldf_dir / rel).is_file()
        assert (cldf_dir / rel).read_bytes() == (canon_dir / rel).read_bytes()


def _build_promoted_workspace_with_relations(ws: pathlib.Path) -> dict[str, object]:
    """Create a complete L3-eligible workspace with both sense->sense and sense->entry relations."""
    from tools import lexicon_packs

    ws.mkdir(parents=True, exist_ok=True)
    snap_id = "snp_rel_test"
    src_id = "src_rel_test"
    rec_1 = "rec_rel_1"
    rec_2 = "rec_rel_2"
    ent_1 = "ent_rel_1"
    ent_2 = "ent_rel_2"
    frm_1 = "frm_rel_1"
    frm_2 = "frm_rel_2"
    sen_1a = "sen_rel_1a"
    sen_1b = "sen_rel_1b"
    sen_2 = "sen_rel_2"
    txt_1a = "txt_rel_1a"
    txt_1b = "txt_rel_1b"
    txt_2 = "txt_rel_2"
    rel_s2s = "rel_sense_to_sense"
    rel_s2e = "rel_sense_to_entry"
    zero_sha = hashlib.sha256(b"cldf-rel-regression").hexdigest()

    (ws / "notices").mkdir(parents=True, exist_ok=True)
    (ws / "notices" / "source-attribution.md").write_text(
        "# Source Attribution\n\nSynthetic verified source for CLDF relation regression.\n",
        encoding="utf-8",
        newline="\n",
    )

    (ws / "vocabularies.toml").write_text(
        'schema_version = 1\n'
        'vocabulary_version = "1"\n'
        'language_ids = ["eng", "tam"]\n'
        'parts_of_speech = ["NOUN"]\n'
        'relation_codes = ["related_to", "synonym"]\n'
        'annotation_properties = []\n'
        'registers = []\n',
        encoding="ascii",
        newline="\n",
    )

    snapshots = [{
        "snapshot_id": snap_id,
        "dataset_id": "synthetic-cldf-rel",
        "relative_path": "primary.csv",
        "byte_length": 64,
        "sha256": zero_sha,
        "media_type": "text/csv",
        "logical_row_count": 2,
    }]
    sources = [{
        "source_id": src_id,
        "label_json": "Synthetic Verified Source",
        "publication_json": "Synthetic Pub",
        "url_json": None,
        "edition_json": None,
        "locator_json": "synthetic:1",
        "snapshot_id": snap_id,
        "retrieval_date_state": "known",
        "retrieval_date_json": "2026-11-15",
        "extraction_method": "synthetic-extractor",
        "extraction_version": "1",
        "evidence_verification_state": "verified",
        "reuse_basis_json": "CC0-1.0 synthetic test fixture",
        "reuse_state": "permitted",
        "attribution_text_json": "Synthetic Test Attribution",
        "attribution_reference_json": "notices/source-attribution.md",
    }]
    source_records = [
        {"record_id": rec_1, "snapshot_id": snap_id, "ordinal": 2, "physical_line_start": 2, "physical_line_end": 2, "legacy_key_json": "1", "raw_row_sha256": zero_sha},
        {"record_id": rec_2, "snapshot_id": snap_id, "ordinal": 3, "physical_line_start": 3, "physical_line_end": 3, "legacy_key_json": "2", "raw_row_sha256": zero_sha},
    ]
    dispositions = [
        {"record_id": rec_1, "disposition": "mapped", "structural_state": "validated", "reason_code": "MAPPED", "note_json": "Synthetic", "finding_set_sha256": hashlib.sha256(b"[]").hexdigest(), "method": "lexicon", "method_version": "1"},
        {"record_id": rec_2, "disposition": "mapped", "structural_state": "validated", "reason_code": "MAPPED", "note_json": "Synthetic", "finding_set_sha256": hashlib.sha256(b"[]").hexdigest(), "method": "lexicon", "method_version": "1"},
    ]
    record_targets = [
        {"record_id": rec_1, "entity_id": ent_1, "target_role": "primary"},
        {"record_id": rec_2, "entity_id": ent_2, "target_role": "primary"},
    ]
    identities = [
        {"entity_id": ent_1, "kind": "entry", "allocation_key": "e1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": ent_2, "kind": "entry", "allocation_key": "e2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_1, "kind": "form", "allocation_key": "f1", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": frm_2, "kind": "form", "allocation_key": "f2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_1a, "kind": "sense", "allocation_key": "s1a", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_1b, "kind": "sense", "allocation_key": "s1b", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": sen_2, "kind": "sense", "allocation_key": "s2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1a, "kind": "text", "allocation_key": "t1a", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_1b, "kind": "text", "allocation_key": "t1b", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": txt_2, "kind": "text", "allocation_key": "t2", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": rel_s2s, "kind": "relation", "allocation_key": "rs2s", "lifecycle": "active", "identity_decision_id": None},
        {"entity_id": rel_s2e, "kind": "relation", "allocation_key": "rs2e", "lifecycle": "active", "identity_decision_id": None},
    ]

    assertions = []
    evidence = []
    decisions = []

    def add_claim(aid: str, skind: str, sid: str, prop: str, val: str, rec: str) -> str:
        row = _make_assertion(aid, skind, sid, prop, val)
        assertions.append(row)
        ev = _make_evidence(aid, src_id, rec, f"loc:{aid}")
        evidence.append(ev)
        decisions.append(
            _make_decision(
                f"dec_{aid}",
                row,
                [ev],
                outcome="accepted_human",
                actor_type="human",
                actor_id="human.reviewer",
            )
        )
        return aid

    ast_hw1 = add_claim("ast_hw1", "form", frm_1, "headword", "\u0b85\u0bb1\u0bae\u0bcd", rec_1)
    ast_hw2 = add_claim("ast_hw2", "form", frm_2, "headword", "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", rec_2)
    ast_pos1 = add_claim("ast_pos1", "entry", ent_1, "part_of_speech", "NOUN", rec_1)
    ast_pos2 = add_claim("ast_pos2", "entry", ent_2, "part_of_speech", "NOUN", rec_2)
    ast_txt1a = add_claim("ast_txt1a", "text", txt_1a, "gloss", "virtue", rec_1)
    ast_txt1b = add_claim("ast_txt1b", "text", txt_1b, "definition", "duty", rec_1)
    ast_txt2 = add_claim("ast_txt2", "text", txt_2, "gloss", "gratitude", rec_2)
    ast_rel_s2s = add_claim("ast_rel_s2s", "relation", rel_s2s, "relation_code", "synonym", rec_1)
    ast_rel_s2e = add_claim("ast_rel_s2e", "relation", rel_s2e, "relation_code", "related_to", rec_1)

    rev1 = hashlib.sha256(b"rev1").hexdigest()
    rev2 = hashlib.sha256(b"rev2").hexdigest()
    entries = [
        {"entry_id": ent_1, "language_id": "tam", "variety_id": None, "canonical_form_id": frm_1, "pos_assertion_id": ast_pos1, "structural_kind": "lexical_entry", "revision": rev1},
        {"entry_id": ent_2, "language_id": "tam", "variety_id": None, "canonical_form_id": frm_2, "pos_assertion_id": ast_pos2, "structural_kind": "lexical_entry", "revision": rev2},
    ]
    forms = [
        {"form_id": frm_1, "entry_id": ent_1, "representation": "written", "role": "canonical", "text_assertion_id": ast_hw1, "convention_assertion_id": None},
        {"form_id": frm_2, "entry_id": ent_2, "representation": "written", "role": "canonical", "text_assertion_id": ast_hw2, "convention_assertion_id": None},
    ]
    senses = [
        {"sense_id": sen_1a, "entry_id": ent_1, "display_order": 1, "parent_sense_id": None},
        {"sense_id": sen_1b, "entry_id": ent_1, "display_order": 2, "parent_sense_id": sen_1a},
        {"sense_id": sen_2, "entry_id": ent_2, "display_order": 1, "parent_sense_id": None},
    ]
    texts = [
        {"text_id": txt_1a, "owner_kind": "sense", "owner_id": sen_1a, "component": "gloss", "language_id": "eng", "text_assertion_id": ast_txt1a, "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_1b, "owner_kind": "sense", "owner_id": sen_1b, "component": "definition", "language_id": "eng", "text_assertion_id": ast_txt1b, "paired_translation_id": None, "cited_source_locator_json": None},
        {"text_id": txt_2, "owner_kind": "sense", "owner_id": sen_2, "component": "gloss", "language_id": "eng", "text_assertion_id": ast_txt2, "paired_translation_id": None, "cited_source_locator_json": None},
    ]
    relations = [
        {"relation_id": rel_s2s, "source_kind": "sense", "source_id": sen_1a, "target_kind": "sense", "target_id": sen_2, "relation_code_assertion_id": ast_rel_s2s, "directionality": "undirected", "inverse_relation_id": None},
        {"relation_id": rel_s2e, "source_kind": "sense", "source_id": sen_1b, "target_kind": "entry", "target_id": ent_2, "relation_code_assertion_id": ast_rel_s2e, "directionality": "directed", "inverse_relation_id": None},
    ]
    pack_members = [
        {"pack_id": "core", "entry_id": ent_1, "included_revision": rev1, "relation_inclusion_policy": "omit_cross_pack"},
        {"pack_id": "core", "entry_id": ent_2, "included_revision": rev2, "relation_inclusion_policy": "omit_cross_pack"},
    ]

    for tbl, rows in (
        ("snapshots", snapshots),
        ("sources", sources),
        ("source_records", source_records),
        ("dispositions", dispositions),
        ("record_targets", record_targets),
        ("identities", identities),
        ("entries", entries),
        ("forms", forms),
        ("senses", senses),
        ("texts", texts),
        ("relations", relations),
        ("assertions", assertions),
        ("evidence", evidence),
        ("decisions", decisions),
        ("findings", []),
        ("labels", []),
        ("scopes", []),
        ("pack_members", pack_members),
    ):
        lexicon_tables.write_rows(ws / f"{tbl}.csv", tbl, rows, source_root=lexicon.SOURCE)

    canon_dir = ws.parent / "canon_with_relations"
    promo = lexicon_packs.promote(ws, pack="core", output=canon_dir)
    assert promo["l3_pack_eligible"] is True
    assert lexicon_packs.validate_canonical_dir(canon_dir) == []
    return {
        "canon_dir": canon_dir,
        "rel_s2s": rel_s2s,
        "rel_s2e": rel_s2e,
        "ast_rel_s2s": ast_rel_s2s,
        "ast_rel_s2e": ast_rel_s2e,
    }


def test_t043_promote_export_cldf_roundtrip_with_sense_to_sense_and_sense_to_entry_relations(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    info = _build_promoted_workspace_with_relations(tmp_path / "ws_rel")
    canon_dir = info["canon_dir"]
    cldf_dir = tmp_path / "cldf_rel"

    def deny_network(*_args, **_kwargs):
        raise RuntimeError("network disabled for offline CLDF validation")

    monkeypatch.setattr(socket, "create_connection", deny_network)
    monkeypatch.setattr(urllib.request, "urlopen", deny_network)

    rep = lexicon_cldf.export_cldf(canonical=canon_dir, pack="core", output=cldf_dir, check=True)
    assert rep["l3_pack_eligible"] is True
    assert rep["cldf_valid"] is True
    assert rep["roundtrip_ok"] is True
    assert rep["findings"] == []

    # Nonzero relation and closure counts must be preserved in both report and exported CLDF files.
    assert rep["counts"]["entries"] == 2
    assert rep["counts"]["senses"] == 3
    assert rep["counts"]["relations"] == 2
    assert rep["counts"]["assertions"] == 9
    assert rep["counts"]["evidence"] == 9
    assert rep["counts"]["decisions"] == 9
    assert rep["counts"]["identities"] == 12

    exported_rels = {r["relation_id"]: r for r in csv.DictReader((cldf_dir / "relations.csv").open(encoding="utf-8"))}
    assert set(exported_rels) == {info["rel_s2s"], info["rel_s2e"]}
    assert exported_rels[info["rel_s2s"]]["source_kind"] == "sense"
    assert exported_rels[info["rel_s2s"]]["target_kind"] == "sense"
    assert exported_rels[info["rel_s2e"]]["source_kind"] == "sense"
    assert exported_rels[info["rel_s2e"]]["target_kind"] == "entry"

    exported_aids = {r["assertion_id"] for r in csv.DictReader((cldf_dir / "assertions.csv").open(encoding="utf-8"))}
    assert {info["ast_rel_s2s"], info["ast_rel_s2e"]} <= exported_aids
    exported_ids = {r["entity_id"] for r in csv.DictReader((cldf_dir / "identities.csv").open(encoding="utf-8"))}
    assert {info["rel_s2s"], info["rel_s2e"]} <= exported_ids

    ds = pycldf.Dataset.from_metadata(cldf_dir / "Dictionary-metadata.json")
    assert ds.validate(ontology_path=SCHEMA_DIR / "v1.3" / "terms.rdf") is True

    # Missing relation row in exported CLDF must fail roundtrip verification.
    trusted = lexicon_cldf.load_trusted_canonical(canon_dir, "core")
    bad_missing = tmp_path / "cldf_missing_rel"
    shutil.copytree(cldf_dir, bad_missing)
    rel_lines = (bad_missing / "relations.csv").read_text(encoding="utf-8").splitlines()
    assert len(rel_lines) == 3
    (bad_missing / "relations.csv").write_text("\n".join(rel_lines[:2]) + "\n", encoding="utf-8", newline="\n")
    res_missing = lexicon_cldf.verify_cldf_export(bad_missing, trusted)
    assert res_missing["roundtrip_ok"] is False
    assert any(f["code"] == "ROUNDTRIP_TABLE_MISMATCH" and f["entity_id"] == "relations" for f in res_missing["findings"])

    # Tampered relation row in exported CLDF must fail roundtrip verification.
    bad_tamper = tmp_path / "cldf_tamper_rel"
    shutil.copytree(cldf_dir, bad_tamper)
    tampered_rel_csv = (bad_tamper / "relations.csv").read_text(encoding="utf-8").replace("directed", "undirected", 1)
    assert tampered_rel_csv != (bad_tamper / "relations.csv").read_text(encoding="utf-8")
    (bad_tamper / "relations.csv").write_text(tampered_rel_csv, encoding="utf-8", newline="\n")
    res_tamper = lexicon_cldf.verify_cldf_export(bad_tamper, trusted)
    assert res_tamper["roundtrip_ok"] is False
    assert any(f["code"] == "ROUNDTRIP_TABLE_MISMATCH" and f["entity_id"] == "relations" for f in res_tamper["findings"])


def test_t043_cldf_rejects_entry_source_relation_and_enforces_sense_to_entry_external_policy(
    tmp_path: pathlib.Path,
) -> None:
    # 1. Entry-sourced relation in canonical fixture must not be silently dropped or accepted.
    bad_entry_src = _write_canonical_fixture(tmp_path / "canon_entry_src", pack="core", eligible=True)
    rel_rows = list(lexicon_tables.read_rows(bad_entry_src / "relations.csv", "relations"))
    rel_rows[0]["source_kind"] = "entry"
    rel_rows[0]["source_id"] = "ent:ta.001"
    lexicon_tables.write_rows(bad_entry_src / "relations.csv", "relations", rel_rows, source_root=lexicon.SOURCE)
    rep_entry_src = lexicon_cldf.export_cldf(canonical=bad_entry_src, pack="core", output=tmp_path / "out_entry_src", check=True)
    assert rep_entry_src["l3_pack_eligible"] is False
    assert any(f["code"] == "UNSUPPORTED_RELATION_SOURCE_KIND" for f in rep_entry_src["findings"])

    # 2. Sense-sourced relation targeting external entry without evidence_only_external must fail via sense->entry ownership policy.
    bad_ext = _write_canonical_fixture(tmp_path / "canon_ext_rel", pack="core", eligible=True)
    ext_rels = list(lexicon_tables.read_rows(bad_ext / "relations.csv", "relations"))
    ext_rels[0]["target_kind"] = "entry"
    ext_rels[0]["target_id"] = "ent:external.999"
    lexicon_tables.write_rows(bad_ext / "relations.csv", "relations", ext_rels, source_root=lexicon.SOURCE)
    rep_ext = lexicon_cldf.export_cldf(canonical=bad_ext, pack="core", output=tmp_path / "out_ext_rel", check=True)
    assert rep_ext["l3_pack_eligible"] is False
    assert any(f["code"] == "RELATION_EXTERNAL_CLOSURE_VIOLATION" for f in rep_ext["findings"])

    # 3. Single-pack canonical dir with dangling/unowned relation endpoints must not silently drop the relation.
    bad_unowned = _write_canonical_fixture(tmp_path / "canon_unowned_rel", pack="core", eligible=True)
    unowned_rels = list(lexicon_tables.read_rows(bad_unowned / "relations.csv", "relations"))
    unowned_rels[0]["source_kind"] = "sense"
    unowned_rels[0]["source_id"] = "sns:external.999"
    unowned_rels[0]["target_kind"] = "entry"
    unowned_rels[0]["target_id"] = "ent:external.999"
    lexicon_tables.write_rows(bad_unowned / "relations.csv", "relations", unowned_rels, source_root=lexicon.SOURCE)
    rep_unowned = lexicon_cldf.export_cldf(canonical=bad_unowned, pack="core", output=tmp_path / "out_unowned_rel", check=True)
    assert rep_unowned["l3_pack_eligible"] is False
    assert rep_unowned["findings"]



