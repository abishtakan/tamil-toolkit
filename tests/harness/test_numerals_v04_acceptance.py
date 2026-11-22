"""Acceptance checks for Phase 6 (numerals-v0.4) golden corpus and declarative tables."""

import json
import tomllib

from tools.generate_numerals_v04_golden import OUTPUT, ROOT, render


def test_numerals_v04_corpus_matches_deterministic_generator():
    content = render()
    assert OUTPUT.read_text(encoding="utf-8") == content
    cases = [json.loads(line) for line in content.splitlines()]
    assert len(cases) == 739
    ops = {case["op"] for case in cases}
    assert ops == {
        "format_currency",
        "currency_to_words",
        "format_currency_decimal",
        "currency_decimal_to_words",
        "mixed_fraction_to_words",
        "words_to_number",
    }
    assert {case["region"] for case in cases if "region" in case} == {
        "TN",
        "KONGU",
        "CHENNAI",
        "JAFFNA",
        "BATTICALOA",
        "VANNI",
        "UP_COUNTRY",
    }


def test_numerals_v04_lexicon_table_contract():
    data = tomllib.loads((ROOT / "lexicon/numerals-v04.toml").read_text(encoding="utf-8"))
    assert data["profile"] == "numerals-v0.4"
    codes = [entry["code"] for entry in data["diaspora_currencies"]]
    assert codes == ["SGD", "MYR", "USD", "EUR", "GBP", "CAD"]
    assert len(data["mixed_fraction_words"]["endings"]) == 3
