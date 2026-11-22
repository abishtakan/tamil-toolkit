"""Generate deterministic golden vectors for Phase 6 (numerals-v0.4) from frozen ICU references."""

import argparse
import json
import sys
import tomllib
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, row  # noqa: E402
from tools.generate_numerals_golden import REFERENCE, rule_tables  # noqa: E402

OUTPUT = ROOT / "tests/golden/numerals_v04.jsonl"
SOURCE = "CLDR 49 Tamil rules; ICU4J 79.1 frozen output; docs/specs/numerals-v0.4.md"


def format_grouped_33(value: int) -> str:
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    major, minor = divmod(magnitude, 100)
    return f"{sign}{major:,}.{minor:02d}"


def load_v04_data():
    return tomllib.loads((ROOT / "lexicon/numerals-v04.toml").read_text(encoding="utf-8"))


def load_formats_data():
    return tomllib.loads((ROOT / "lexicon/numerals-formats.toml").read_text(encoding="utf-8"))


def render():
    _, negative, _ = rule_tables()
    v04 = load_v04_data()
    formats = load_formats_data()
    division = formats["division"]
    common_fractions = {
        (entry["numerator"], entry["denominator"]): entry["words"]
        for entry in formats["common_fractions"]
    }
    integer_rows = {
        entry["value"]: entry
        for entry in map(json.loads, (REFERENCE / "icu-integers.jsonl").read_text(encoding="utf-8").splitlines())
    }
    money_rows = {
        entry["value"]: entry
        for entry in map(json.loads, (REFERENCE / "icu-money.jsonl").read_text(encoding="utf-8").splitlines())
    }
    cases = []

    def add(identifier, op, value, expected, locale="TN", error=False, tags=None, region=None):
        cases.append(
            row(
                identifier,
                op,
                value,
                expected,
                tags or ["numerals_v04"],
                SOURCE,
                dialect=locale,
                error=error,
                region=region,
            )
        )

    # 1. Diaspora currencies: SGD, MYR, USD, EUR, GBP, CAD
    sample_amounts = [
        0, 1, 5, 50, 99, 100, 101, 1000, 102501, 100000, 100001, 10000000, 10000021, 99999999999,
        -1, -100, -100000, -10000021, -99999999999,
    ]
    for curr in v04["diaspora_currencies"]:
        code = curr["code"]
        for amt in sample_amounts:
            entry = money_rows[amt]
            for locale in ("TN", "SL"):
                inputs = {"amount_minor": amt, "currency": code, "locale": locale}
                formatted = f"{code} {format_grouped_33(amt)}"
                words = (
                    (f"{negative} " if amt < 0 else "")
                    + f"{entry[locale]['major']} {curr['major']} {entry[locale]['minor']} {curr['minor']}"
                )
                tag = f"n{abs(amt)}" if amt < 0 else str(amt)
                add(
                    f"num04_curr_{code.lower()}_{tag}_{locale.lower()}_fmt",
                    "format_currency",
                    inputs,
                    formatted,
                    locale,
                    tags=["numerals_v04", "diaspora_currency"],
                )
                add(
                    f"num04_curr_{code.lower()}_{tag}_{locale.lower()}_words",
                    "currency_to_words",
                    inputs,
                    words,
                    locale,
                    tags=["numerals_v04", "diaspora_currency"],
                )
        # Decimal currency spot-checks
        for dec_text, minor in [("1234.50", 123450), ("-0.05", -5), ("100000.00", 10000000)]:
            entry = money_rows[minor] if minor in money_rows else None
            formatted = f"{code} {format_grouped_33(minor)}"
            add(
                f"num04_curr_dec_{code.lower()}_{abs(minor)}_{'neg' if minor < 0 else 'pos'}",
                "format_currency_decimal",
                {"amount": dec_text, "source_digits": "latin", "currency": code, "locale": "TN"},
                formatted,
                "TN",
                tags=["numerals_v04", "diaspora_currency", "decimal_currency"],
            )
            if entry is not None:
                words = (
                    (f"{negative} " if minor < 0 else "")
                    + f"{entry['TN']['major']} {curr['major']} {entry['TN']['minor']} {curr['minor']}"
                )
                add(
                    f"num04_curr_dec_words_{code.lower()}_{abs(minor)}_{'neg' if minor < 0 else 'pos'}",
                    "currency_decimal_to_words",
                    {"amount": dec_text, "source_digits": "latin", "currency": code, "locale": "TN"},
                    words,
                    "TN",
                    tags=["numerals_v04", "diaspora_currency", "decimal_currency"],
                )

    # 2. Colloquial mixed fraction words
    endings = v04["mixed_fraction_words"]["endings"]
    conjunction = v04["mixed_fraction_words"]["conjunction"]

    def expected_mixed(negative_flag, whole, num, den, locale):
        if num == 0:
            signed = -whole if negative_flag else whole
            return integer_rows[signed][locale]["numbering"]
        prefix = f"{negative} " if negative_flag else ""
        if whole == 0:
            if (num, den) in common_fractions:
                return prefix + common_fractions[(num, den)]
            return f"{prefix}{integer_rows[num][locale]['numbering']} {division} {integer_rows[den][locale]['numbering']}"
        whole_words = integer_rows[whole][locale]["numbering"]
        key = {(1, 4): "quarter", (1, 2): "half", (3, 4): "three_quarters"}.get((num, den))
        if key is not None:
            for rule in endings:
                if whole_words.endswith(rule["strip_suffix"]):
                    stem = whole_words[: -len(rule["strip_suffix"])]
                    return unicodedata.normalize("NFC", prefix + stem + rule[key])
            raise ValueError(f"no mixed fraction ending rule for {whole_words}")
        frac_words = f"{integer_rows[num][locale]['numbering']} {division} {integer_rows[den][locale]['numbering']}"
        return unicodedata.normalize("NFC", f"{prefix}{whole_words} {conjunction} {frac_words}")

    mixed_samples = [
        (False, 0, 0, 1),
        (False, 5, 0, 1),
        (True, 5, 0, 1),
        (False, 0, 1, 4),
        (False, 0, 1, 2),
        (False, 0, 3, 4),
        (True, 0, 1, 2),
        (False, 0, 2, 5),
        (False, 1, 1, 4),
        (False, 1, 1, 2),
        (False, 1, 3, 4),
        (True, 1, 1, 2),
        (False, 2, 1, 4),
        (False, 2, 1, 2),
        (False, 2, 3, 4),
        (False, 3, 1, 2),
        (False, 4, 1, 4),
        (False, 5, 3, 4),
        (False, 9, 1, 2),
        (False, 10, 1, 4),
        (False, 11, 1, 2),
        (False, 12, 3, 4),
        (False, 20, 1, 2),
        (False, 100, 1, 2),
        (False, 900, 1, 2),
        (False, 1000, 1, 4),
        (False, 1000, 1, 2),
        (False, 1000, 3, 4),
        (False, 100000, 1, 2),
        (False, 10000000, 1, 4),
        (False, 10000000, 1, 2),
        (False, 10000000, 3, 4),
        (False, 2, 2, 5),
        (True, 3, 5, 8),
    ]
    for idx, (neg, whole, num, den) in enumerate(mixed_samples):
        for locale in ("TN", "SL"):
            exp = expected_mixed(neg, whole, num, den, locale)
            add(
                f"num04_mixed_{idx:03}_{locale.lower()}",
                "mixed_fraction_to_words",
                {"negative": neg, "whole": whole, "numerator": num, "denominator": den, "locale": locale},
                exp,
                locale,
                tags=["numerals_v04", "mixed_fraction_words"],
            )
    # Default locale check
    add(
        "num04_mixed_default_locale",
        "mixed_fraction_to_words",
        {"negative": False, "whole": 1, "numerator": 1, "denominator": 2},
        expected_mixed(False, 1, 1, 2, "TN"),
        "TN",
        tags=["numerals_v04", "mixed_fraction_words", "default_locale"],
    )
    # Unreduced fraction input reduces just like format_mixed_fraction (1 2/4 -> 1 1/2)
    add(
        "num04_mixed_reduces_fraction",
        "mixed_fraction_to_words",
        {"negative": False, "whole": 1, "numerator": 2, "denominator": 4, "locale": "TN"},
        expected_mixed(False, 1, 1, 2, "TN"),
        "TN",
        tags=["numerals_v04", "mixed_fraction_words"],
    )
    # Mixed fraction errors
    mixed_errors = [
        ({"negative": True, "whole": 0, "numerator": 0, "denominator": 1}, "invalid mixed fraction"),
        ({"negative": False, "whole": 1, "numerator": 2, "denominator": 2}, "invalid mixed fraction"),
        ({"negative": False, "whole": 1, "numerator": 3, "denominator": 2}, "invalid mixed fraction"),
        ({"negative": False, "whole": 1, "numerator": 1, "denominator": 0}, "invalid mixed fraction"),
        ({"negative": False, "whole": 1, "numerator": 1, "denominator": 2, "locale": "XX"}, "unsupported locale"),
        ({"negative": False, "whole": 1, "numerator": 2, "denominator": 2, "locale": "XX"}, "invalid mixed fraction"),
    ]
    for idx, (inp, err) in enumerate(mixed_errors):
        add(
            f"num04_mixed_err_{idx:02}",
            "mixed_fraction_to_words",
            inp,
            err,
            "TN",
            error=True,
            tags=["numerals_v04", "shared_error"],
        )

    # 3. Reverse word-to-number parsing (ITN: words_to_number)
    itn_values = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
        20, 21, 29, 30, 45, 50, 67, 70, 88, 90, 99,
        100, 101, 110, 111, 123, 200, 305, 456, 500, 899, 900, 901, 999,
        1000, 1001, 1025, 1999, 2000, 2001, 2021, 10000, 11000, 19021, 21000, 99999,
        100000, 100001, 100999, 200000, 999999, 1000000, 2100021, 9999999,
        10000000, 10000001, 20000000, 990000000, 999999999,
        -1, -10, -19, -20, -999, -1000, -100000, -10000000, -999999999,
    ]
    for idx, val in enumerate(itn_values):
        entry = integer_rows[val]
        for locale in ("TN", "SL"):
            add(
                f"num04_itn_{idx:03}_{locale.lower()}",
                "words_to_number",
                {"text": entry[locale]["numbering"], "locale": locale},
                val,
                locale,
                tags=["numerals_v04", "itn"],
            )
    # Default locale check for ITN
    add(
        "num04_itn_default_locale",
        "words_to_number",
        {"text": integer_rows[100000]["TN"]["numbering"]},
        100000,
        "TN",
        tags=["numerals_v04", "itn", "default_locale"],
    )
    # Regional coverage probes
    for dialect, region in [
        ("TN", "TN"),
        ("TN", "KONGU"),
        ("TN", "CHENNAI"),
        ("SL", "JAFFNA"),
        ("SL", "BATTICALOA"),
        ("SL", "VANNI"),
        ("SL", "UP_COUNTRY"),
    ]:
        add(
            f"num04_itn_region_{region.lower()}",
            "words_to_number",
            {"text": integer_rows[100001][dialect]["numbering"], "locale": dialect},
            100001,
            dialect,
            region=region,
            tags=["numerals_v04", "itn", "regional_profile"],
        )
    # ITN error cases
    itn_errors = [
        ({"text": ""}, "invalid Tamil number words"),
        ({"text": "   "}, "invalid Tamil number words"),
        ({"text": f" {integer_rows[1]['TN']['numbering']}"}, "invalid Tamil number words"),
        ({"text": f"{integer_rows[1]['TN']['numbering']} "}, "invalid Tamil number words"),
        ({"text": f"{negative} {integer_rows[0]['TN']['numbering']}"}, "invalid Tamil number words"),
        ({"text": integer_rows[100000]["SL"]["numbering"], "locale": "TN"}, "invalid Tamil number words"),
        ({"text": integer_rows[100000]["TN"]["numbering"], "locale": "SL"}, "invalid Tamil number words"),
        ({"text": integer_rows[1]["TN"]["cardinal"], "locale": "TN"}, "invalid Tamil number words"),
        ({"text": f"{integer_rows[5]['TN']['numbering']} {integer_rows[100]['TN']['numbering']}"}, "invalid Tamil number words"),
        ({"text": "123"}, "invalid Tamil number words"),
        ({"text": 123}, "expected a string input"),
        ({}, "expected a string input"),
        ({"text": integer_rows[1]["TN"]["numbering"], "locale": "XX"}, "unsupported locale"),
    ]
    for idx, (inp, err) in enumerate(itn_errors):
        add(
            f"num04_itn_err_{idx:02}",
            "words_to_number",
            inp,
            err,
            "TN",
            error=True,
            tags=["numerals_v04", "itn", "shared_error"],
        )

    return "".join(json.dumps(case, ensure_ascii=True, separators=(",", ":")) + "\n" for case in cases)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("numerals_v04.jsonl differs; regenerate with tools/generate_numerals_v04_golden.py")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
