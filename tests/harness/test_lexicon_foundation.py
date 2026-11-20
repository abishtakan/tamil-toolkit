"""Structural foundation tests for tools.lexicon (Feature 021 T007)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.lexicon import (
    LexiconError,
    atomic_json,
    decode_text,
    encode_text,
    table_rows,
    write_table,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/reference/lexicon/structural"
COMMON_SCHEMA = ROOT / "schemas/lexicon/common.schema.json"


def _load_codec_cases() -> dict:
    return json.loads((FIXTURES / "codec_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", _load_codec_cases()["roundtrip_texts"], ids=lambda c: c["name"])
def test_text_codec_roundtrips_structural_cases(case):
    encoded = encode_text(case["text"])
    assert encoded.isascii()
    assert encoded == case["encoded"]
    assert decode_text(encoded) == case["text"]


@pytest.mark.parametrize("bad_value", [None, 123, ["a"], "\ud800", "\udfff", "prefix\ud800suffix"])
def test_encode_text_rejects_non_strings_and_lone_surrogates(bad_value):
    with pytest.raises(LexiconError):
        encode_text(bad_value)


@pytest.mark.parametrize("case", _load_codec_cases()["invalid_decode_cells"], ids=lambda c: c["name"])
def test_decode_text_rejects_invalid_and_surrogate_cells(case):
    with pytest.raises(LexiconError):
        decode_text(case["cell"])


def test_decode_text_rejects_raw_non_ascii_cells():
    raw_tamil_cell = '"\u0b85\u0bae\u0bcd\u0bae\u0bbe"'
    with pytest.raises(LexiconError):
        decode_text(raw_tamil_cell)


def test_atomic_json_is_deterministic_ascii_lf_and_rejects_source_overlap(tmp_path):
    source_root = tmp_path / "frozen"
    source_root.mkdir()
    sentinel = source_root / "original.csv"
    sentinel.write_text("id\n1\n", encoding="utf-8")

    # Reject destination equal to, inside, or enclosing frozen source_root.
    for bad_target in [source_root, source_root / "out.json", source_root / "sub" / "out.json", tmp_path]:
        with pytest.raises(LexiconError):
            atomic_json(bad_target, {"b": 1, "a": "\u0b85"}, source_root=source_root)
    assert sentinel.read_text(encoding="utf-8") == "id\n1\n"

    out_path = tmp_path / "out" / "report.json"
    atomic_json(out_path, {"z": "\u0b85", "a": 1}, source_root=source_root)
    raw = out_path.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    text = raw.decode("ascii")
    assert text.index('"a"') < text.index('"z"')
    assert json.loads(text) == {"a": 1, "z": "\u0b85"}


def test_write_table_sorts_bytewise_and_preserves_prior_output_on_error(tmp_path):
    source_root = tmp_path / "frozen"
    source_root.mkdir()
    table_path = tmp_path / "out" / "items.csv"

    write_table(
        table_path,
        ["id", "val"],
        [{"id": "b", "val": encode_text("second")}, {"id": "a", "val": encode_text("first")}],
        source_root=source_root,
    )
    rows = list(table_rows(table_path))
    assert [r["id"] for r in rows] == ["a", "b"]
    assert b"\r\n" not in table_path.read_bytes()

    def failing_rows():
        yield {"id": "c", "val": encode_text("partial")}
        raise RuntimeError("generator aborted")

    with pytest.raises(RuntimeError, match="generator aborted"):
        write_table(table_path, ["id", "val"], failing_rows(), source_root=source_root)

    assert [r["id"] for r in table_rows(table_path)] == ["a", "b"]


def test_common_schema_distinguishes_known_empty_from_unknown_and_not_applicable():
    schema = json.loads(COMMON_SCHEMA.read_text(encoding="utf-8"))
    stateful_schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/statefulValue"}
    locator_schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/locator"}

    jsonschema.validate({"value_state": "known", "value_json": ""}, stateful_schema)
    jsonschema.validate({"value_state": "unknown", "value_json": None}, stateful_schema)
    jsonschema.validate({"value_state": "not_applicable", "value_json": None}, stateful_schema)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"value_state": "unknown", "value_json": ""}, stateful_schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"value_state": "not_applicable", "value_json": "NA"}, stateful_schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate("", locator_schema)
def test_inventory_cli_reports_mode_without_granting_acceptance(tmp_path, capsys):
    import json
    from tools.lexicon import main

    source = tmp_path / "source"
    source.mkdir()
    (source / "words.csv").write_text("id,term\n1,example\n", encoding="utf-8")
    assert main(["inventory", "--source", str(source), "--output", str(tmp_path / "inventory")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["command"] == "inventory"
    assert report["mode"] == "intake"
    assert report["csv_records"] == 1
    assert report["l2_structural_accepted"] is False
    assert report["l3_pack_eligible"] is False
    assert report["runtime_verified"] is None

