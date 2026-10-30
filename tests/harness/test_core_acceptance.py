"""Acceptance checks use independent frozen evidence, not the runtime lexicon."""

import json
import unicodedata

import pytest

from tools.generate_core_golden import GOLDEN, generate, references, render, text
from tools.harness import validate_rows


def test_independent_corpus_is_reproducible_and_complete():
    generated = generate()
    assert {name: len(rows) for name, rows in generated.items()} == {
        "core_alphabet.jsonl": 1237,
        "core_normalization.jsonl": 291,
        "core_boundaries.jsonl": 796,
        "core_errors.jsonl": 96,
    }
    for name, content in render().items():
        assert (GOLDEN / name).read_text(encoding="utf-8") == content, name
    alphabet = generated["core_alphabet.jsonl"]
    assert len([r for r in alphabet if r["id"].startswith("alphabet_split_")]) == 288
    assert len([r for r in alphabet if r["id"].startswith("alphabet_compose_")]) == 288
    inspections = [r for r in alphabet if r["op"] == "inspect_tamil_string"]
    assert len(inspections) == 327
    traditional = [r for r in inspections if "grantha" not in r["tags"]]
    assert len(traditional) == 247
    assert len({r["input"] for r in traditional}) == 247


def test_independent_normalizer_matches_tamil_reference_decompositions():
    _, ucd, _ = references()
    canonical = [(char, mapping) for char, mapping in ucd.values() if mapping]
    assert len(canonical) == 4
    for char, mapping in canonical:
        assert unicodedata.normalize("NFD", char) == text(mapping.split())


@pytest.mark.parametrize("outcomes", [{}, {"expected": [], "expected_error": "bad input"}, {"expected_error": ""}])
def test_golden_schema_requires_exactly_one_valid_outcome(tmp_path, outcomes):
    row = json.loads((GOLDEN / "core_graphemes.jsonl").read_text().splitlines()[0])
    row.pop("expected")
    row.update(outcomes)
    path = tmp_path / "invalid.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_rows(path)


def test_error_vectors_accept_wrong_input_types_but_success_vectors_do_not(tmp_path):
    row = {"id": "schema_error", "op": "get_letters", "input": 1,
           "expected_error": "expected a string input", "dialect": "TN", "tags": ["invalid_input"],
           "source": "docs/specs/core-v0.1.md"}
    path = tmp_path / "negative.jsonl"
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert validate_rows(path) == [row]
    row.pop("expected_error")
    row["expected"] = []
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_rows(path)
