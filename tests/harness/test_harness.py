import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tools.harness import GOLDEN, ROOT, load_vectors, unicode_issues, validate_golden_schema, validate_rows


def oracle_module():
    spec = importlib.util.spec_from_file_location("tamil_oracle", ROOT / "tools/mcp-tamil-oracle/server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed():
    return copy.deepcopy(load_vectors()[0])


def write_row(tmp_path, row):
    path = tmp_path / "fixture.jsonl"
    path.write_text(json.dumps(row, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def test_repository_vectors_are_valid():
    assert load_vectors()
    assert validate_golden_schema("tests/golden/core_graphemes.jsonl")["valid"]


@pytest.mark.parametrize("mutation", [
    lambda row: row.pop("dialect"),
    lambda row: row.update(dialect="XX"),
    lambda row: row.update(input="\ud800"),
    lambda row: row.update(input="x" + chr(0x200C)),
    lambda row: row.update(input=next(c["input"] for c in load_vectors() if c["id"] == "core_008")),
    lambda row: row.update(region="JAFFNA", dialect="TN"),
    lambda row: row.update(unicode_exceptions=[{"path": "/input", "kind": "joiner", "reason": "Unused exception must fail"}]),
])
def test_invalid_fixture_is_rejected(tmp_path, mutation):
    row = seed()
    mutation(row)
    with pytest.raises(ValueError):
        validate_rows(write_row(tmp_path, row))


@pytest.mark.parametrize("key,kind", [
    pytest.param("hidden" + chr(0x200C), "key_joiner", id="zwnj"),
    pytest.param("hidden" + chr(0x200D), "key_joiner", id="zwj"),
    pytest.param(chr(0x0065) + chr(0x0301), "key_non_nfc", id="non-nfc"),
    pytest.param(chr(0xD800), "key_surrogate", id="high-surrogate"),
    pytest.param(chr(0xDFFF), "key_surrogate", id="low-surrogate"),
])
@pytest.mark.parametrize("nested", [False, True], ids=["object", "nested-array"])
def test_invalid_unicode_object_keys_are_rejected(tmp_path, key, kind, nested):
    row = copy.deepcopy(next(case for case in load_vectors() if case["op"] == "inspect_tamil_string"))
    payload = {key: "clean value"}
    row["expected"] = {"outer": [payload]} if nested else payload
    with pytest.raises(ValueError, match=kind):
        validate_rows(write_row(tmp_path, row))


def test_key_diagnostics_escape_json_pointer_tokens():
    key = "slash/tilde~" + chr(0x200C)
    assert unicode_issues({"expected": [{key: "clean"}]}) == {
        ("/expected/0/slash~1tilde~0" + chr(0x200C), "key_joiner"),
    }


def test_unicode_keys_and_value_exceptions_remain_valid(tmp_path):
    normalized = next(case for case in load_vectors() if case["id"] == "core_008")["expected"]
    # Cover non-ASCII keys, astral scalars, and escaped JSON Pointer tokens.
    key = normalized + "/~" + chr(0x1F4BB)
    row = copy.deepcopy(next(case for case in load_vectors() if case["op"] == "inspect_tamil_string"))
    row["expected"] = {key: ["value" + chr(0x200C)]}
    row["unicode_exceptions"] = [{
        "path": "/expected/" + key.replace("~", "~0").replace("/", "~1") + "/0",
        "kind": "joiner",
        "reason": "Intentional value joiner verifies that key checks preserve scoped exceptions.",
    }]
    assert validate_rows(write_row(tmp_path, row)) == [row]


def test_value_exceptions_do_not_cover_object_keys(tmp_path):
    row = copy.deepcopy(next(case for case in load_vectors() if case["id"] == "core_010"))
    row["op"] = "inspect_tamil_string"
    row["expected"] = {"hidden" + chr(0x200C): "clean"}
    row["unicode_exceptions"] = [exception for exception in row["unicode_exceptions"] if exception["path"] == "/input"]
    with pytest.raises(ValueError, match="key_joiner"):
        validate_rows(write_row(tmp_path, row))


def test_duplicate_ids_are_rejected(tmp_path):
    row = seed()
    path = write_row(tmp_path, row)
    with pytest.raises(ValueError, match="duplicate"):
        validate_rows(path, {row["id"]})


def test_oracle_restricts_file_paths():
    with pytest.raises(ValueError):
        validate_golden_schema("Cargo.toml")


def test_oracle_scalar_diff_exposes_composition_and_joiners():
    oracle = oracle_module()
    # Read the intentionally decomposed case from the single fixture source.
    case = next(row for row in load_vectors() if row["id"] == "core_008")
    diff = oracle.diff_tamil_outputs(case["input"], case["expected"])
    assert not diff["equal"] and diff["canonically_equivalent"]
    assert [s["hex"] for s in diff["differences"][0]["expected"]] == ["U+0BC6", "U+0BBE"]
    assert oracle.diff_tamil_outputs("a", "a" + chr(0x200C))["differences"][0]["actual"][0]["hex"] == "U+200C"


def test_source_gate_decodes_rust_escapes(tmp_path):
    spec = importlib.util.spec_from_file_location("unicode_check", ROOT / "tools/mcp-tamil-oracle/check_source_unicode.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "bad.rs"
    for case_id in ("core_008", "core_010"):
        text = next(c["input"] for c in load_vectors() if c["id"] == case_id)
        escaped = "".join(chr(92) + "u{" + format(ord(c), "x") + "}" for c in text)
        path.write_text('const BAD: &str = "' + escaped + '";\n', encoding="utf-8")
        assert module.inspect_source(path)


def test_oracle_inspection_uses_rust():
    oracle = oracle_module()
    case = load_vectors()[0]
    inspected = oracle.inspect_tamil_string(case["input"])
    assert inspected["ezhuthu_count"] == 3
    assert inspected["scalars"][0]["hex"] == "U+0BA4"
    assert [letter["classification"] for letter in inspected["letters"]] == ["vallinam", "mellinam", "idaiyinam"]


def test_manifest_cannot_hide_an_unregistered_suite(tmp_path):
    for path in GOLDEN.iterdir():
        if path.is_file():
            (tmp_path / path.name).write_bytes(path.read_bytes())
    (tmp_path / "forgotten.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="registered"):
        load_vectors(tmp_path)
