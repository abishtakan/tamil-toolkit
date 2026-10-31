import json
import tomllib
import xml.etree.ElementTree as ET

from tools.generate_numerals_golden import (
    OUTPUT, REFERENCE, ROOT, integer_values, money_values, references, render, rule_tables,
)


def test_numeral_corpus_matches_frozen_independent_icu_output():
    content = render()  # Includes every pinned reference digest and coverage check.
    assert OUTPUT.read_text(encoding="utf-8") == content
    cases = [json.loads(line) for line in content.splitlines()]
    assert len(cases) == 7528
    assert sum("expected_error" in case for case in cases) == 134
    for locale in ("TN", "SL"):
        values = {case["input"]["value"] for case in cases
                  if case["op"] == "to_words" and "expected" in case
                  and case["input"].get("locale") == locale}
        assert set(integer_values()) <= values
    assert set(range(1000)) <= set(integer_values())
    assert set(range(100)) <= set(money_values())
    for locale in ("TN", "SL"):
        for currency in ("INR", "LKR"):
            for op in ("format_currency", "currency_to_words"):
                values = {case["input"]["amount_minor"] for case in cases
                          if case["op"] == op and "expected" in case
                          and case["input"].get("currency") == currency
                          and case["input"].get("locale") == locale}
                assert values == set(money_values())
    assert {case["region"] for case in cases if "region" in case} == {
        "TN", "KONGU", "CHENNAI", "JAFFNA", "BATTICALOA", "VANNI", "UP_COUNTRY",
    }


def test_runtime_numeral_data_agrees_with_frozen_cldr_rules():
    profile, negative, tables = rule_tables()
    runtime = tomllib.loads((ROOT / "lexicon/numerals.toml").read_text(encoding="utf-8"))
    for key in ("profile", "max_integer", "max_minor", "primary_group", "secondary_group",
                "sl_lakh_from", "sl_lakh_to", "currencies"):
        assert runtime[key] == profile[key]
    assert runtime["negative"] == negative
    assert {entry["name"]: entry["rules"] for entry in runtime["rulesets"]} == tables


def test_numeric_facts_and_distinct_standalone_cardinal_forms():
    references()
    facts = json.loads((REFERENCE / "ta-number-facts.json").read_text())
    assert facts["decimal_pattern"] == "#,##,##0.###"
    # ta_LK inherits grouping: it does not supply a different decimalFormats tree.
    assert ET.fromstring((REFERENCE / "ta-LK.xml").read_bytes()).find(".//decimalFormats") is None
    fractions = json.loads((REFERENCE / "currency-fractions.json").read_text())
    assert fractions["currency_fractions"] == [{"iso4217": "DEFAULT", "digits": "2", "rounding": "0"}]
    rows = {entry["value"]: entry for entry in map(json.loads, (REFERENCE / "icu-integers.jsonl").read_text().splitlines())}
    assert rows[1]["TN"]["numbering"] == "\u0b92\u0ba9\u0bcd\u0bb1\u0bc1"
    assert rows[1]["TN"]["cardinal"] == "\u0b92\u0bb0\u0bc1"
    assert rows[11]["TN"]["numbering"] != rows[11]["TN"]["cardinal"]
    assert rows[100000]["TN"]["numbering"] != rows[100000]["SL"]["numbering"]
    assert rows[1025]["SL"]["numbering"] == "\u0b86\u0baf\u0bbf\u0bb0\u0ba4\u0bcd\u0ba4\u0bc1 \u0b87\u0bb0\u0bc1\u0baa\u0ba4\u0bcd\u0ba4\u0bc1 \u0b90\u0ba8\u0bcd\u0ba4\u0bc1"
