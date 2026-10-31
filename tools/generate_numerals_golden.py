"""Prepare/check fixtures from frozen ICU output; no Tamil number engine here."""

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, row  # noqa: E402

REFERENCE = ROOT / "tests/reference/numerals-v0.1"
OUTPUT = ROOT / "tests/golden/numerals_lkr_inr.jsonl"
SOURCE = "CLDR 49 Tamil rules; ICU4J 79.1 frozen output; docs/specs/numerals-v0.1.md"
RULESET_NAMES = ["%%spellout-prefix", "%spellout-numbering", "%%spellout-cardinal-tens-compound",
                 "%%spellout-cardinal-hundreds-compound", "%%spellout-cardinal-crore-compound", "%spellout-cardinal"]


def references(check_outputs=True):
    metadata = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    for source in metadata["files"]:
        if not check_outputs and source["file"].startswith("icu-"):
            continue
        if hashlib.sha256((REFERENCE / source["file"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("numeral reference digest mismatch: " + source["file"])
    profile = json.loads((REFERENCE / "profile.json").read_text(encoding="utf-8"))
    rules = ET.fromstring((REFERENCE / "ta-rbnf.xml").read_bytes()).find('.//rulesetGrouping[@type="SpelloutRules"]/rbnfRules').text.strip()
    return profile, rules


def rule_tables():
    profile, rules = references(False)
    tables = {}
    current = None
    negative = None
    for line in rules.splitlines():
        line = line.strip()
        if line.startswith("%") and line.endswith(":"):
            current = line[:-1]
            if current in RULESET_NAMES:
                tables[current] = []
        elif current in RULESET_NAMES and line:
            value, pattern = line.split(":", 1)
            pattern = pattern.strip().removesuffix(";")
            if value == "-x" and current == "%spellout-numbering":
                negative = pattern.removesuffix(">>").strip()
            if not value.isdigit() or int(value) > profile["max_integer"]:
                continue
            base = int(value)
            divisor = 10 ** (len(str(base)) - 1) if base else 1
            tables[current].append({"base": base, "divisor": divisor, "pattern": pattern})
    assert len(tables) == 6 and negative
    return profile, negative, tables


def integer_values():
    values = set(range(1000)) | set(range(-20, 0))
    for scale in (1000, 100000, 10000000):
        for multiplier in range(1, 100):
            values.update(multiplier * scale + remainder for remainder in (0, 1, 21))
    for boundary in (1000, 2000, 10000, 100000, 200000, 1000000, 10000000, 20000000, 100000000, 999999999):
        for offset in (-2, -1, 0, 1, 2, 10, 11, 19, 20, 25, 99, 100, 101, 999):
            value = boundary + offset
            if 0 <= value <= 999999999:
                values.add(value)
                values.add(-value)
    values.update((1025, 1001, 999999999, -999999999))
    return sorted(values)


def money_values():
    values = set(range(200)) | {-1, -5, -50, -99, -100, -101, -199}
    for major in (9, 10, 11, 19, 20, 21, 99, 100, 101, 999, 1000, 1001, 1025,
                  9999, 10000, 99999, 100000, 100001, 9999999, 10000000, 10000001, 999999999):
        for minor in (0, 1, 21, 99):
            values.add(major * 100 + minor)
            values.add(-(major * 100 + minor))
    return sorted(values)


def render():
    profile, _ = references()
    _, negative, _ = rule_tables()
    integer_rows = [json.loads(line) for line in (REFERENCE / "icu-integers.jsonl").read_text().splitlines()]
    money_rows = [json.loads(line) for line in (REFERENCE / "icu-money.jsonl").read_text().splitlines()]
    assert [entry["value"] for entry in integer_rows] == integer_values()
    assert [entry["value"] for entry in money_rows] == money_values()
    cases = []

    def add(identifier, op, value, expected, locale="TN", error=False, tags=None, region=None):
        cases.append(row(identifier, op, value, expected, tags or ["numerals_v1"], SOURCE,
                         dialect=locale, error=error, region=region))

    for index, entry in enumerate(integer_rows):
        for locale in ("TN", "SL"):
            add(f"number_{index:04}_{locale.lower()}", "to_words", {"value": entry["value"], "locale": locale}, entry[locale]["numbering"], locale)
    for index, entry in enumerate(money_rows):
        for currency in profile["currencies"]:
            for locale in ("TN", "SL"):
                inputs = {"amount_minor": entry["value"], "currency": currency["code"], "locale": locale}
                formatted = currency["code"] + " " + entry["formatted"]
                words = (negative + " " if entry["value"] < 0 else "") + entry[locale]["major"] + " " + currency["major"] + " " + entry[locale]["minor"] + " " + currency["minor"]
                identifier = f"money_{index:04}_{currency['code'].lower()}_{locale.lower()}"
                add(identifier + "_format", "format_currency", inputs, formatted, locale, tags=["exact_minor_units"])
                add(identifier + "_words", "currency_to_words", inputs, words, locale, tags=["currency_labels", "cardinal_form"])
    cache = {entry["value"]: entry for entry in integer_rows}
    # Retain the brief's IDs as reviewed source-backed examples with the new input contract.
    for identifier, value in [("num_001", 1000), ("num_014", 1025)]:
        add(identifier, "to_words", {"value": value, "locale": "SL"}, cache[value]["SL"]["numbering"], "SL", tags=["reviewed_brief_example"])
    add("number_default_locale", "to_words", {"value": 100000}, cache[100000]["TN"]["numbering"])
    add("number_integral_json", "to_words", {"value": 1.0}, cache[1]["TN"]["numbering"])
    add("number_negative_zero", "to_words", {"value": -0.0}, cache[0]["TN"]["numbering"])
    money_cache = {entry["value"]: entry for entry in money_rows}
    for currency in profile["currencies"]:
        for value in (0, -1, 100):
            for integral_float in (False, True):
                entry = money_cache[value]
                inputs = {"amount_minor": float(value) if integral_float else value, "currency": currency["code"]}
                words = (negative + " " if value < 0 else "") + entry["TN"]["major"] + " " + currency["major"] + " " + entry["TN"]["minor"] + " " + currency["minor"]
                identifier = f"money_default_{currency['code'].lower()}_{'minus' if value < 0 else 'plus'}{abs(value)}_{int(integral_float)}"
                add(identifier + "_format", "format_currency", inputs, currency["code"] + " " + entry["formatted"], tags=["default_locale", "integral_json"])
                add(identifier + "_words", "currency_to_words", inputs, words, tags=["default_locale", "integral_json"])
    for dialect, region in [("TN", "TN"), ("TN", "KONGU"), ("TN", "CHENNAI"), ("SL", "JAFFNA"), ("SL", "BATTICALOA"), ("SL", "VANNI"), ("SL", "UP_COUNTRY")]:
        add("number_region_" + region.lower(), "to_words", {"value": 100001, "locale": dialect}, cache[100001][dialect]["numbering"], dialect, region=region, tags=["regional_profile"])
    bad_integer = "expected an integer in the supported range"
    failures = []
    for value in [None, True, "1", 1.25, [], {}, 1000000000, -1000000000]:
        failures.append(("to_words", {"value": value}, bad_integer))
    failures.extend([("to_words", value, bad_integer) for value in [None, 1, [], {}]])
    for op in ("format_currency", "currency_to_words"):
        for value in [None, True, "100", 1.25, [], {}, 100000000000, -100000000000]:
            failures.append((op, {"amount_minor": value, "currency": "INR"}, bad_integer))
        failures.extend([(op, value, bad_integer) for value in [None, 1, [], {}]])
        for currency in [None, "USD", "inr", 1, ""]:
            failures.append((op, {"amount_minor": 100, "currency": currency}, "unsupported currency"))
        failures.append((op, {"amount_minor": 100}, "unsupported currency"))
    for op in ("to_words", "format_currency", "currency_to_words"):
        for locale in [None, "XX", "tn", 1, ""]:
            inputs = {"value": 1, "locale": locale} if op == "to_words" else {"amount_minor": 100, "currency": "INR", "locale": locale}
            failures.append((op, inputs, "unsupported locale"))
    for op in ("format_currency", "currency_to_words"):
        failures.append((op, {"amount_minor": 1.25, "locale": "XX", "currency": "USD"}, bad_integer))
        failures.append((op, {"amount_minor": 100, "locale": "XX", "currency": "USD"}, "unsupported locale"))
    for index, (op, inputs, message) in enumerate(failures):
        for dialect in ("TN", "SL"):
            add(f"number_error_{index:03}_{dialect.lower()}", op, inputs, message, dialect, error=True, tags=["shared_error"])
    return "".join(json.dumps(case, ensure_ascii=True, separators=(",", ":")) + "\n" for case in cases)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Numeral corpus differs; review frozen ICU evidence and regenerate")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
