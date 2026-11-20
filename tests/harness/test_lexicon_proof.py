"""Focused small-fixture tests for bounded-memory source payload equality proof."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from tools.lexicon import NAMESPACE, ROOT, data_json, inventory, stage
from tools.lexicon_proof import verify_source_payloads


def _write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def _stage_fixture(tmp_path, files_spec, namespace=None, extra_files=()):
    source = tmp_path / "source"
    inv = tmp_path / "inventory"
    ws = tmp_path / "workspace"
    source.mkdir()
    ws.mkdir()
    for filename, (headers, rows) in files_spec.items():
        _write_csv(source / filename, headers, rows)
    for filename, raw_bytes in extra_files:
        (source / filename).write_bytes(raw_bytes)
    ns_value = str(namespace or NAMESPACE)
    (ws / "dataset.toml").write_text(
        f'schema_version = 1\ntext_codec = "json-string-utf8-v1"\nid_namespace = "{ns_value}"\n',
        encoding="ascii",
    )
    inventory(source, inv)
    stage(inv, ws)
    return source, inv, ws


def _rewrite_assertions(workspace, transform):
    path = workspace / "assertions.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        fieldnames = list(reader.fieldnames or [])
        rows = transform(list(reader))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_verify_source_payloads_passes_across_all_table_kinds_and_cli_payloads_only(tmp_path, monkeypatch):
    nfd_tamil = chr(0x0BA4) + chr(0x0BC6) + chr(0x0BBE)
    literal_bs = "\\" + "u200d"
    controls_text = (
        nfd_tamil
        + chr(0x200C)
        + chr(0x200D)
        + chr(0xFEFF)
        + chr(0x00AD)
        + chr(0x2028)
        + chr(0x2029)
        + chr(0x7F)
        + chr(0x85)
        + "\t\n"
        + literal_bs
        + chr(0x11FC0)
        + chr(0x1F600)
    )
    files_spec = {
        "primary_lemmas.csv": (
            ["word_id", "headword_ta", "part_of_speech"],
            [["10", chr(0x0BA4) + chr(0x0BAE) + chr(0x0BBF) + chr(0x0BB4) + chr(0x0BCD), "noun"]],
        ),
        "unified_master_30col.csv": (
            ["word_id", "headword_ta", "root_word"],
            [["10", controls_text, literal_bs]],
        ),
        "primary_meanings.csv": (
            ["meaning_id", "word_id", "sense_number", "meaning_en"],
            [["100", "10", "1", "Tamil " + controls_text]],
        ),
        "primary_relationships.csv": (
            ["relationship_id", "source_word_id", "target_word_id", "relation_code", "directionality"],
            [["200", "10", "10", "synonym", "symmetric"]],
        ),
        "secondary_dialect_colloquialisms.csv": (
            ["record_id", "headword_ta", "region_dialect", "meaning_en"],
            [["s1", chr(0x0BA4) + chr(0x0BA3) + chr(0x0BCD) + chr(0x0BA3) + chr(0x0BC0), "Jaffna", "water"]],
        ),
    }
    source, _inv, ws = _stage_fixture(tmp_path, files_spec, extra_files=[("dummy.fst", b"\x00\x01\x02")])
    from tools import lexicon_proof

    temporary_directory = lexicon_proof.tempfile.TemporaryDirectory
    owned_temp = []

    def track_temporary_directory(*args, **kwargs):
        directory = temporary_directory(*args, **kwargs)
        owned_temp.append(Path(directory.name))
        return directory

    monkeypatch.setattr(lexicon_proof.tempfile, "TemporaryDirectory", track_temporary_directory)

    report = verify_source_payloads(ws, source)
    assert report["schema_version"] == 1
    assert report["codec"] == "json-string-utf8-v1"
    assert report["source_hashes_verified"] == 6
    assert report["source_records"] == 5
    assert report["master_records"] == 1
    assert report["matching_raw_assertions"] == 5
    assert report["missing_or_duplicate_assertions"] == 0
    assert report["exact_decoded_source_fields_and_scalars"] is True
    assert report["subject_ids_match_immutable_allocations"] is True
    assert report["l2_structural_accepted"] is False
    assert report["l3_pack_eligible"] is False
    assert report["runtime_verified"] is None
    assert owned_temp
    assert all(not path.exists() for path in owned_temp)

    output_path = tmp_path / "payload-proof.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/lexicon_proof.py"),
            "--payloads-only",
            "--workspace",
            str(ws),
            "--source",
            str(source),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    cli_report = json.loads(output_path.read_text(encoding="ascii"))
    assert cli_report == report


def test_verify_source_payloads_supports_custom_dataset_namespace(tmp_path):
    custom_ns = uuid.uuid5(NAMESPACE, "custom-fixture-ns-v1")
    files_spec = {
        "primary_lemmas.csv": (["word_id", "headword_ta"], [["1", chr(0x0B85)]]),
        "primary_meanings.csv": (["meaning_id", "word_id", "meaning_en"], [["2", "1", "a"]]),
    }
    source, _inv, ws = _stage_fixture(tmp_path, files_spec, namespace=custom_ns)

    report = verify_source_payloads(ws, source)
    assert report["source_records"] == 2
    assert report["matching_raw_assertions"] == 2

    # Switching dataset.toml namespace breaks assertion/subject UUID expectations.
    (ws / "dataset.toml").write_text(
        f'schema_version = 1\ntext_codec = "json-string-utf8-v1"\nid_namespace = "{NAMESPACE}"\n',
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="missing=2"):
        verify_source_payloads(ws, source)


def test_verify_source_payloads_rejects_nfd_normalization_and_content_tamper(tmp_path):
    nfd_tamil = chr(0x0BA4) + chr(0x0BC6) + chr(0x0BBE)
    nfc_tamil = chr(0x0BA4) + chr(0x0BCA)
    assert nfd_tamil != nfc_tamil
    files_spec = {
        "primary_lemmas.csv": (["word_id", "headword_ta"], [["1", nfd_tamil]]),
    }
    source, _inv, ws = _stage_fixture(tmp_path, files_spec)

    def normalize_inner(rows):
        for row in rows:
            inner = json.loads(json.loads(row["value_json"]))
            inner["headword_ta"] = nfc_tamil
            row["value_json"] = data_json(data_json(inner))
        return rows

    _rewrite_assertions(ws, normalize_inner)
    with pytest.raises(ValueError, match="content_mismatches=1"):
        verify_source_payloads(ws, source)


def test_verify_source_payloads_rejects_outer_non_string_and_control_tamper(tmp_path):
    literal_bs = "\\" + "u0085"
    files_spec = {
        "primary_lemmas.csv": (["word_id", "headword_ta"], [["1", literal_bs + chr(0x200D)]]),
    }
    source, _inv, ws = _stage_fixture(tmp_path, files_spec)

    # Corrupt literal backslash -> actual C1 scalar inside inner object.
    def tamper_control(rows):
        for row in rows:
            inner = json.loads(json.loads(row["value_json"]))
            inner["headword_ta"] = chr(0x0085) + chr(0x200D)
            row["value_json"] = data_json(data_json(inner))
        return rows

    _rewrite_assertions(ws, tamper_control)
    with pytest.raises(ValueError, match="content_mismatches=1"):
        verify_source_payloads(ws, source)

    # Outer value_json replaced with a JSON object rather than a JSON string literal fails cleanly.
    def unwrap_outer(rows):
        for row in rows:
            row["value_json"] = '{"headword_ta":"x","word_id":"1"}'
        return rows

    _rewrite_assertions(ws, unwrap_outer)
    with pytest.raises(ValueError, match="must decode to JSON string"):
        verify_source_payloads(ws, source)


def test_verify_source_payloads_rejects_missing_duplicate_unexpected_and_wrong_subject(tmp_path):
    files_spec = {
        "primary_lemmas.csv": (
            ["word_id", "headword_ta"],
            [["1", chr(0x0B85)], ["2", chr(0x0B86)]],
        ),
    }
    source, _inv, ws = _stage_fixture(tmp_path, files_spec)
    original_bytes = (ws / "assertions.csv").read_bytes()

    # 1. Wrong subject_id
    def swap_subjects(rows):
        rows[0]["subject_id"], rows[1]["subject_id"] = rows[1]["subject_id"], rows[0]["subject_id"]
        return rows

    _rewrite_assertions(ws, swap_subjects)
    with pytest.raises(ValueError, match="subject_mismatches=2"):
        verify_source_payloads(ws, source)

    # 2. Duplicate assertion row
    (ws / "assertions.csv").write_bytes(original_bytes)
    _rewrite_assertions(ws, lambda rows: rows + [dict(rows[0])])
    with pytest.raises(ValueError, match="duplicates=1"):
        verify_source_payloads(ws, source)

    # 3. Missing assertion row
    (ws / "assertions.csv").write_bytes(original_bytes)
    _rewrite_assertions(ws, lambda rows: rows[:1])
    with pytest.raises(ValueError, match="missing=1"):
        verify_source_payloads(ws, source)

    # 4. Unexpected extra unparsed assertion
    (ws / "assertions.csv").write_bytes(original_bytes)

    def add_unexpected(rows):
        extra = dict(rows[0])
        extra["assertion_id"] = "ast_00000000-0000-5000-8000-000000000099"
        return rows + [extra]

    _rewrite_assertions(ws, add_unexpected)
    with pytest.raises(ValueError, match="unexpected=1"):
        verify_source_payloads(ws, source)
