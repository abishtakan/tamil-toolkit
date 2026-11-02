"""Build escaped v0.3 numeric/civil vectors from pinned ICU and exact references."""

import argparse
import hashlib
import json
import sys
import tomllib
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, row  # noqa: E402
from tools.generate_numerals_golden import rule_tables  # noqa: E402

REFERENCE = ROOT / "tests/reference/numerals-v0.3"
OLD_REFERENCE = ROOT / "tests/reference/numerals-v0.1"
OUTPUT = ROOT / "tests/golden/numerals_v03.jsonl"
SOURCE = "CLDR 49 RBNF; Unicode 17.0.0; ICU4J 79.1; Python exact-string/Gregorian oracle; docs/specs/numerals-v0.3.md"


def verify(reference: Path, manifest_name: str = "sources.json") -> dict:
    metadata = json.loads((reference / manifest_name).read_text(encoding="utf-8"))
    for entry in metadata["files"]:
        path = reference / entry["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("numeral reference checksum mismatch: " + entry["file"])
    return metadata


def parse_numeric(text: str) -> tuple[bool, str, int]:
    negative = text.startswith("-")
    text = text.lstrip("+-").replace(",", "")
    if "." in text:
        integer, fraction = text.split(".")
    else:
        integer, fraction = text, ""
    digits = integer + fraction
    digits = digits.translate(str.maketrans("\u0be6\u0be7\u0be8\u0be9\u0bea\u0beb\u0bec\u0bed\u0bee\u0bef", "0123456789"))
    coefficient = digits.lstrip("0") or "0"
    return negative and coefficient != "0", coefficient, len(fraction)


def group_indian(value: str) -> str:
    if len(value) <= 3:
        return value
    groups = [value[-3:]]
    value = value[:-3]
    while value:
        groups.append(value[-2:])
        value = value[:-2]
    return ",".join(reversed(groups))


def format_exact(value: dict, tamil: bool = False, indian: bool = False) -> str:
    coefficient = value["coefficient"]
    scale = value["scale"]
    padded = coefficient.zfill(scale + 1)
    integer, fraction = (padded[:-scale], padded[-scale:]) if scale else (padded, "")
    if indian:
        integer = group_indian(integer)
    result = ("-" if value["negative"] else "") + integer
    if scale:
        result += "." + fraction
    if tamil:
        result = result.translate(str.maketrans("0123456789", "\u0be6\u0be7\u0be8\u0be9\u0bea\u0beb\u0bec\u0bed\u0bee\u0bef"))
    return result


def generate_cases():
    verify(REFERENCE)
    verify(OLD_REFERENCE)
    profile = json.loads((OLD_REFERENCE / "profile.json").read_text(encoding="utf-8"))
    v03_profile = json.loads((REFERENCE / "profile.json").read_text(encoding="utf-8"))
    tamil_data = {}
    for line in (OLD_REFERENCE / "icu-integers.jsonl").read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        tamil_data[entry["value"]] = entry
    ordinal = [json.loads(line) for line in (REFERENCE / "icu-ordinals.jsonl").read_text(encoding="utf-8").splitlines()]
    traditional = [json.loads(line) for line in (REFERENCE / "icu-traditional.jsonl").read_text(encoding="utf-8").splitlines()]
    negative_prefix = rule_tables()[1]
    cases = []

    def add(identifier, op, inputs, expected, *, error=False, dialect="COMMON", tags=None):
        cases.append(row("n3_" + identifier, op, inputs, expected,
                         tags or ["numerals_v03"], SOURCE, error=error, dialect=dialect))

    # CLDR 49 and ICU4J expected outputs are frozen in the local, digest-pinned reference.
    for entry in ordinal:
        value = entry["value"]
        if value == 0:
            continue
        for locale in ("TN", "SL"):
            add(f"ordinal_{value}_{locale.lower()}", "ordinal_to_words", {"value": value, "locale": locale}, entry[locale], dialect=locale, tags=["icu_ordinal_boundary", "ordinal_domain"])
    for entry in traditional:
        value = entry["value"]
        case_value = f"m{-value}" if value < 0 else str(value)
        add(f"traditional_format_{case_value}", "format_traditional_integer", {"value": value}, entry["formatted"], tags=["icu_root_rbnf", "traditional_integer"])
        add(f"traditional_parse_{case_value}", "parse_traditional_integer", {"text": entry["formatted"]}, value, tags=["icu_root_rbnf", "traditional_integer"])

    # Scalar-preserving conversion and exact decimal strings use a small independent string oracle.
    joiner = chr(0x200D)
    add("digits_to_tamil", "convert_digits", {"text": "ID 2026 / \u0be7\u0be8 · " + joiner + "9", "to": "tamil"}, "ID \u0be8\u0be6\u0be8\u0bec / \u0be7\u0be8 · " + joiner + "\u0bef")
    add("digits_to_latin", "convert_digits", {"text": "A\u0be6\u0be7\u0be8/3", "to": "latin"}, "A012/3")
    add("decimal_parse_leading_and_scale", "parse_decimal", {"text": "+00012.3400", "source_digits": "latin"}, {"negative": False, "coefficient": "123400", "scale": 4})
    add("decimal_parse_negative_zero", "parse_decimal", {"text": "-000.00", "source_digits": "latin"}, {"negative": False, "coefficient": "0", "scale": 2})
    add("decimal_parse_tamil", "parse_decimal", {"text": "\u0be6\u0be6\u0be7\u0be8.\u0be9\u0be6", "source_digits": "tamil"}, {"negative": False, "coefficient": "1230", "scale": 2})
    add("decimal_parse_indian", "parse_decimal", {"text": "12,34,567.80", "source_digits": "latin", "grouping": "indian"}, {"negative": False, "coefficient": "123456780", "scale": 2})
    add("decimal_parse_mixed", "parse_decimal", {"text": "1\u0be8.3\u0bea", "source_digits": "latin", "allow_mixed_digits": True}, {"negative": False, "coefficient": "1234", "scale": 2})
    add("decimal_parse_256_digits", "parse_decimal", {"text": "1" + "0" * 255, "source_digits": "latin"}, {"negative": False, "coefficient": "1" + "0" * 255, "scale": 0}, tags=["numerals_v03_precision_boundary"])
    add("decimal_format_preserve", "format_decimal", {"value": {"negative": False, "coefficient": "123400", "scale": 4}}, "12.3400")
    add("decimal_format_grouped_tamil", "format_decimal", {"value": {"negative": False, "coefficient": "123456700", "scale": 2}, "digits": "tamil", "grouping": "indian"}, "\u0be7\u0be8,\u0be9\u0bea,\u0beb\u0bec\u0bed.\u0be6\u0be6")
    add("decimal_format_zero", "format_decimal", {"value": {"negative": False, "coefficient": "0", "scale": 3}}, "0.000")

    for value in (0, 1, 2, 9, 10, 42, 999, 123456789):
        if value not in tamil_data:
            continue
        for locale in ("TN", "SL"):
            entry = tamil_data[value][locale]
            add(f"decimal_words_{value}_{locale.lower()}", "decimal_to_words", {"text": f"{value}.03", "source_digits": "latin", "locale": locale},
                entry["numbering"] + " " + v03_profile["decimal_point_word"] + " " + tamil_data[0][locale]["numbering"] + " " + tamil_data[3][locale]["numbering"], dialect=locale)
    for value in ("1.20", "0.5", "12.03"):
        negative, coefficient, scale = parse_numeric(value)
        integer_text = coefficient[:-scale] if scale and len(coefficient) > scale else "0"
        fraction_text = coefficient[-scale:].zfill(scale) if scale else ""
        integer_value = int(integer_text or "0")
        for locale in ("TN", "SL"):
            integer_words = tamil_data[integer_value][locale]["numbering"]
            frac_words = " ".join(tamil_data[int(digit)][locale]["numbering"] for digit in fraction_text)
            expected = (negative_prefix + " " if negative else "") + integer_words + " " + v03_profile["decimal_point_word"] + " " + frac_words
            add(f"decimal_words_exact_{value.replace('.', '_')}_{locale.lower()}", "decimal_to_words", {"text": value, "source_digits": "latin", "locale": locale}, expected, dialect=locale)

    for text, script in (("0071", "latin"), ("\u0be6\u0be6\u0bed\u0be7", "tamil")):
        chars = text.translate(str.maketrans("\u0be6\u0be7\u0be8\u0be9\u0bea\u0beb\u0bec\u0bed\u0bee\u0bef", "0123456789"))
        for locale in ("TN", "SL"):
            add(f"digit_sequence_{script}_{locale.lower()}", "digit_sequence_to_words", {"text": text, "source_digits": script, "locale": locale},
                " ".join(tamil_data[int(ch)][locale]["numbering"] for ch in chars), dialect=locale)

    # Major-unit currency helpers reuse the frozen ICU cardinals and existing labels.
    for amount in ("0", "1.2", "123.45", "-999999999.99"):
        neg, coefficient, scale = parse_numeric(amount)
        minor_text = coefficient + "0" * (2 - scale)
        minor = int(minor_text)
        major, cents = divmod(minor, 100)
        for currency in profile["currencies"]:
            code = currency["code"]
            for locale in ("TN", "SL"):
                sign = "-" if neg else ""
                formatted = f"{code} {sign}{group_indian(str(major))}.{cents:02d}"
                add(f"money_decimal_format_{amount.replace('-', 'm').replace('.', '_')}_{code.lower()}_{locale.lower()}", "format_currency_decimal",
                    {"amount": amount, "source_digits": "latin", "currency": code, "locale": locale}, formatted, dialect=locale)
                major_words = tamil_data[major][locale]["cardinal"]
                minor_words = tamil_data[cents][locale]["cardinal"]
                words = (negative_prefix + " " if neg else "") + major_words + " " + currency["major"] + " " + minor_words + " " + currency["minor"]
                add(f"money_decimal_words_{amount.replace('-', 'm').replace('.', '_')}_{code.lower()}_{locale.lower()}", "currency_decimal_to_words",
                    {"amount": amount, "source_digits": "latin", "currency": code, "locale": locale}, words, dialect=locale)

    # UnicodeData 17 rational values include every duplicate fraction glyph.
    unicode_lines = [line.split(";") for line in (REFERENCE / "UnicodeData-Tamil.txt").read_text(encoding="utf-8").splitlines()]
    rows = {int(fields[0], 16): fields for fields in unicode_lines}
    frac_values = {}
    for cp in range(0x11FC0, 0x11FD4):
        fields = rows[cp]
        rational = Fraction(fields[8])
        frac_values.setdefault(rational, []).append(cp)
        add(f"fraction_symbol_{cp:04x}", "parse_fraction_symbol", {"text": chr(cp)},
            {"numerator": rational.numerator, "denominator": rational.denominator}, tags=["unicode_17_all_fraction_forms"])
    add("fraction_symbol_negative", "parse_fraction_symbol", {"text": "-" + chr(0x11FD1)}, {"numerator": -1, "denominator": 2})
    add("fraction_symbol_kiizh", "parse_fraction_symbol", {"text": chr(0x11FD4)}, "expected a traditional Tamil fraction symbol", error=True)
    add("fraction_symbol_multiscalar", "parse_fraction_symbol", {"text": chr(0x11FD1) + chr(0x11FD2)}, "expected a traditional Tamil fraction symbol", error=True)

    symbols = []
    wanted = [0x0BD0, *range(0x0BE6,0x0BF3), *range(0x0BF3,0x0BFB), *range(0x11FC0,0x11FF2)]
    for cp in wanted:
        fields = rows.get(cp)
        if fields is None:
            continue
        name = fields[1]
        rational = Fraction(fields[8]) if fields[8] else None
        kind = "symbol"
        if 0x0BE6 <= cp <= 0x0BEF:
            kind = "digit"
        elif cp in (0x0BF0,0x0BF1,0x0BF2):
            kind = "integer_sign"
        elif 0x11FC0 <= cp <= 0x11FD3:
            kind = "fraction"
        elif cp == 0x11FD4:
            kind = "fraction_modifier"
            rational = None
        elif 0x0BF3 <= cp <= 0x0BF5:
            kind = "calendar"
        elif 0x0BF6 <= cp <= 0x0BF8 or cp in (0x11FE8,0x11FE9):
            kind = "clerical"
        elif 0x11FDD <= cp <= 0x11FE0 or cp == 0x0BF9:
            kind = "currency"
        symbols.append({"codepoint":cp,"character":chr(cp),"name":name,"kind":kind,"_rational":rational})
    canonical = {}
    for item in symbols:
        rational = item["_rational"]
        if rational is not None:
            canonical[rational] = min(canonical.get(rational, item["codepoint"]), item["codepoint"])
    for item in symbols:
        rational = item.pop("_rational")
        item.update({"rational":None if rational is None else {"numerator":rational.numerator,"denominator":rational.denominator},
                        "canonical_alternative":canonical.get(rational),
                        "source_version":"Unicode 17.0.0"})
    for item in symbols:
        add(f"symbol_info_{item['codepoint']:05x}", "symbol_info", {"text":item["character"]}, {key:value for key,value in item.items() if key != "character"}, tags=["unicode_17_symbol_subset"])
    add("symbol_info_unknown", "symbol_info", {"text":"A"}, "unsupported Tamil numeric symbol", error=True)

    # Exact mixed forms, percent transformations, ranges and civil-date arithmetic.
    add("mixed_format", "format_mixed_fraction", {"negative":False,"whole":5,"numerator":2,"denominator":4}, "5 1/2")
    add("mixed_format_zero_whole_tamil", "format_mixed_fraction", {"negative":False,"whole":0,"numerator":1,"denominator":4,"digits":"tamil"}, "\u0be6 \u0be7/\u0bea")
    add("mixed_parse_reduced", "parse_mixed_fraction", {"text":"5 1/2","source_digits":"latin"}, {"negative":False,"whole":5,"numerator":1,"denominator":2})
    add("mixed_parse_negative", "parse_mixed_fraction", {"text":"-0 1/4","source_digits":"latin"}, {"negative":True,"whole":0,"numerator":1,"denominator":4})
    add("mixed_format_supported_limit", "format_mixed_fraction", {"negative":False,"whole":999999999,"numerator":1,"denominator":999999999}, "999999999 1/999999999", tags=["numerals_v03_precision_boundary"])
    add("mixed_parse_supported_limit", "parse_mixed_fraction", {"text":"999999999 1/999999999","source_digits":"latin"}, {"negative":False,"whole":999999999,"numerator":1,"denominator":999999999}, tags=["numerals_v03_precision_boundary"])
    add("mixed_reject_unreduced", "parse_mixed_fraction", {"text":"5 2/4","source_digits":"latin"}, "invalid mixed fraction", error=True)
    add("mixed_reject_negative_zero", "parse_mixed_fraction", {"text":"-0","source_digits":"latin"}, "invalid mixed fraction", error=True)
    add("percent_parse", "parse_percent", {"text":"12.50%","source_digits":"latin"}, {"negative":False,"coefficient":"1250","scale":2})
    add("percent_parse_tamil", "parse_percent", {"text":"\u0be7\u0be8.\u0beb\u0be6%","source_digits":"tamil"}, {"negative":False,"coefficient":"1250","scale":2})
    add("percent_format", "format_percent", {"value":{"negative":False,"coefficient":"1250","scale":2}}, "12.50%")
    add("ratio_to_percent", "ratio_to_percent", {"value":{"negative":False,"coefficient":"125","scale":3}}, {"negative":False,"coefficient":"125","scale":1})
    add("percent_to_ratio", "percent_to_ratio", {"value":{"negative":False,"coefficient":"1250","scale":2}}, {"negative":False,"coefficient":"1250","scale":4})
    add("range_decimal_reversed", "format_numeric_range", {"start":{"type":"decimal","value":{"negative":False,"coefficient":"125","scale":2}},"end":{"type":"fraction","numerator":1,"denominator":2},"start_inclusive":True,"end_inclusive":False,"separator":".."}, "invalid numeric range", error=True)
    add("range_mixed", "format_numeric_range", {"start":{"type":"fraction","numerator":1,"denominator":4},"end":{"type":"decimal","value":{"negative":False,"coefficient":"5","scale":0}},"start_inclusive":False,"end_inclusive":True,"separator":" to "}, "(1/4 to 5]")
    add("range_reversed", "format_numeric_range", {"start":{"type":"decimal","value":{"negative":False,"coefficient":"2","scale":0}},"end":{"type":"fraction","numerator":1,"denominator":2},"start_inclusive":True,"end_inclusive":True,"separator":"–"}, "invalid numeric range", error=True)

    # Exact range expectations come from Python Fraction, independent of the Rust comparator.
    def decimal_value(coefficient, scale=0, negative=False):
        return {"negative": negative, "coefficient": coefficient, "scale": scale}

    def endpoint_value(endpoint):
        if endpoint["type"] == "decimal":
            value = endpoint["value"]
            rational = Fraction(int(value["coefficient"]), 10 ** value["scale"])
            return -rational if value["negative"] else rational
        return Fraction(endpoint["numerator"], endpoint["denominator"])

    def endpoint_text(endpoint):
        if endpoint["type"] == "decimal":
            return format_exact(endpoint["value"])
        rational = Fraction(endpoint["numerator"], endpoint["denominator"])
        return f"{rational.numerator}/{rational.denominator}"

    def add_oracle_range(identifier, start, end, start_inclusive=True, end_inclusive=True):
        inputs = {
            "start": start,
            "end": end,
            "start_inclusive": start_inclusive,
            "end_inclusive": end_inclusive,
            "separator": "..",
        }
        if endpoint_value(start) > endpoint_value(end):
            add(identifier, "format_numeric_range", inputs, "invalid numeric range", error=True,
                tags=["independent_fraction_range_oracle", "numerals_v03_regression"])
            return
        expected = (
            ("[" if start_inclusive else "(")
            + endpoint_text(start)
            + ".."
            + endpoint_text(end)
            + ("]" if end_inclusive else ")")
        )
        add(identifier, "format_numeric_range", inputs, expected,
            tags=["independent_fraction_range_oracle", "numerals_v03_regression"])

    zero_scales = (0, 1, 2, 3, 9, 32, 128, 255, 256)
    for scale in zero_scales:
        zero = {"type": "decimal", "value": decimal_value("0", scale)}
        plain_zero = {"type": "decimal", "value": decimal_value("0", 0)}
        add_oracle_range(f"range_zero_equal_scale_{scale}", zero, plain_zero)
        add_oracle_range(f"range_zero_equal_reverse_scale_{scale}", plain_zero, zero)

    zero_fraction = {"type": "fraction", "numerator": 0, "denominator": 1}
    for scale in (0, 1, 2, 9, 256):
        zero = {"type": "decimal", "value": decimal_value("0", scale)}
        add_oracle_range(f"range_zero_fraction_decimal_first_{scale}", zero, zero_fraction)
        add_oracle_range(f"range_zero_fraction_fraction_first_{scale}", zero_fraction, zero)

    add_oracle_range(
        "range_decimal_point_one_vs_zero_fraction",
        {"type": "decimal", "value": decimal_value("1", 1)},
        zero_fraction,
    )
    add_oracle_range(
        "range_zero_vs_decimal_point_one",
        zero_fraction,
        {"type": "decimal", "value": decimal_value("1", 1)},
    )
    add_oracle_range(
        "range_equal_decimal_point_one_fraction",
        {"type": "decimal", "value": decimal_value("1", 1)},
        {"type": "fraction", "numerator": 1, "denominator": 10},
    )
    add_oracle_range(
        "range_equal_fraction_decimal_point_one",
        {"type": "fraction", "numerator": 1, "denominator": 10},
        {"type": "decimal", "value": decimal_value("10", 2)},
    )
    add_oracle_range(
        "range_negative_decimal_fraction",
        {"type": "decimal", "value": decimal_value("1", 2, True)},
        {"type": "fraction", "numerator": -1, "denominator": 200},
    )
    add_oracle_range(
        "range_unequal_near_zero_positive",
        {"type": "decimal", "value": decimal_value("1", 6)},
        {"type": "decimal", "value": decimal_value("2", 6)},
    )
    add_oracle_range(
        "range_unequal_near_zero_negative",
        {"type": "decimal", "value": decimal_value("2", 6, True)},
        {"type": "decimal", "value": decimal_value("1", 6, True)},
    )

    # Exercise every supported decimal magnitude width, both display and parser paths.
    tamil_digit_map = str.maketrans("0123456789", "\u0be6\u0be7\u0be8\u0be9\u0bea\u0beb\u0bec\u0bed\u0bee\u0bef")
    for width in range(1, 257):
        coefficient = "1" * width
        value = decimal_value(coefficient)
        grouped = group_indian(coefficient)
        add(f"group_format_width_{width:03}", "format_decimal",
            {"value": value, "grouping": "indian"}, grouped,
            tags=["indian_grouping_width_1_to_256"])
        add(f"group_parse_width_{width:03}", "parse_decimal",
            {"text": grouped, "source_digits": "latin", "grouping": "indian"}, value,
            tags=["indian_grouping_width_1_to_256", "independent_exact_decimal_oracle"])
    max_coefficient = "9" * 256
    add("decimal_format_256_digits", "format_decimal",
        {"value": decimal_value(max_coefficient, 0), "grouping": "indian"}, group_indian(max_coefficient),
        tags=["numerals_v03_precision_boundary", "independent_exact_decimal_oracle"])
    for width in (1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 64, 255, 256):
        coefficient = "123456789" * (width // 9) + "123456789"[: width % 9]
        coefficient = coefficient or "0"
        grouped = group_indian(coefficient)
        tamil_grouped = grouped.translate(tamil_digit_map)
        value = decimal_value(coefficient)
        add(f"group_tamil_format_width_{width:03}", "format_decimal",
            {"value": value, "digits": "tamil", "grouping": "indian"}, tamil_grouped,
            tags=["tamil_digit_grouping", "independent_exact_decimal_oracle"])
        add(f"group_tamil_parse_width_{width:03}", "parse_decimal",
            {"text": tamil_grouped, "source_digits": "tamil", "grouping": "indian"}, value,
            tags=["tamil_digit_grouping", "independent_exact_decimal_oracle"])
    for malformed in ("1,234,56", "12,345,678", ",123", "1,,234", "1234,567"):
        add(f"group_malformed_{len(cases):05}", "parse_decimal",
            {"text": malformed, "source_digits": "latin", "grouping": "indian"},
            "invalid decimal string", error=True, tags=["indian_grouping_malformed"])
    add("group_malformed_tamil", "parse_decimal",
        {"text": "\u0be7\u0be8,\u0be9\u0bea\u0beb,\u0bec\u0bed", "source_digits": "tamil", "grouping": "indian"},
        "invalid decimal string", error=True, tags=["tamil_digit_grouping", "indian_grouping_malformed"])

    # Percent shifts preserve zero canonically and enforce the same 256-digit/scale limits.
    for scale in (0, 1, 2, 3, 9, 128, 254, 255, 256):
        value = decimal_value("0", scale)
        result_scale = max(scale - 2, 0)
        add(f"ratio_zero_scale_{scale}", "ratio_to_percent", {"value": value},
            decimal_value("0", result_scale), tags=["percent_zero_scale_regression"])
    for scale in (0, 1, 2, 3, 128, 254):
        value = decimal_value("0", scale)
        add(f"percent_zero_scale_{scale}", "percent_to_ratio", {"value": value},
            decimal_value("0", scale + 2), tags=["percent_zero_scale_regression"])
    add("ratio_nonzero_digit_limit", "ratio_to_percent",
        {"value": decimal_value("1" * 256, 0)},
        "decimal precision exceeds supported range", error=True,
        tags=["numerals_v03_precision_boundary"])
    add("percent_scale_limit", "percent_to_ratio",
        {"value": decimal_value("1", 255)},
        "decimal precision exceeds supported range", error=True,
        tags=["numerals_v03_precision_boundary"])
    add("percent_zero_scale_limit", "percent_to_ratio",
        {"value": decimal_value("0", 255)},
        "decimal precision exceeds supported range", error=True,
        tags=["percent_zero_scale_regression", "numerals_v03_precision_boundary"])

    # Bad values must win over display-option errors, as specified for exact formatting.
    precedence = [
        ("format_decimal", {"value": decimal_value("0", 2, True), "digits": "bad", "grouping": "bad"}, "invalid decimal value"),
        ("format_decimal", {"value": decimal_value("01"), "digits": "bad", "grouping": "bad"}, "invalid decimal value"),
        ("format_decimal", {"value": decimal_value("1", 257), "digits": "bad", "grouping": "bad"}, "decimal precision exceeds supported range"),
        ("format_percent", {"value": decimal_value("0", 1, True), "digits": "bad", "grouping": "bad"}, "invalid decimal value"),
        ("format_mixed_fraction", {"negative": False, "whole": 1, "numerator": 2, "denominator": 2, "digits": "bad"}, "invalid mixed fraction"),
        ("format_numeric_range", {"start": {"type": "fraction", "numerator": 2, "denominator": 1}, "end": {"type": "fraction", "numerator": 1, "denominator": 1}, "start_inclusive": True, "end_inclusive": True, "separator": "..", "digits": "bad"}, "invalid numeric range"),
    ]
    for index, (operation, inputs, expected_error) in enumerate(precedence):
        add(f"precedence_domain_{index:02}", operation, inputs, expected_error,
            error=True, tags=["numerals_v03_validation_precedence"])

    civil_cases = [
        ("leap_day", {"year":2024,"month":2,"day":29}, "validate_gregorian_date", True),
        ("weekday_monday", {"year":2024,"month":1,"day":1}, "weekday", "monday"),
        ("weekday_sunday", {"year":2024,"month":1,"day":7}, "weekday", "sunday"),
        ("iso_parse", {"text":"2000-02-29"}, "parse_gregorian_date", {"year":2000,"month":2,"day":29}),
        ("add_days", {"year":2024,"month":2,"day":28,"unit":"days","amount":2}, "add_gregorian_date", {"year":2024,"month":3,"day":1}),
        ("add_month_clamp", {"year":2024,"month":1,"day":31,"unit":"months","amount":1,"overflow":"clamp"}, "add_gregorian_date", {"year":2024,"month":2,"day":29}),
        ("difference_leap", {"start":{"year":2024,"month":2,"day":28},"end":{"year":2024,"month":3,"day":1}}, "date_difference", 2),
        ("interval_inclusive", {"start":"2024-02-28","end":"2024-03-01"}, "date_interval", {"start":"2024-02-28","end":"2024-03-01","inclusive_days":3}),
    ]
    for name, inputs, operation, expected in civil_cases:
        add("civil_" + name, operation, inputs, expected, tags=["gregorian_independent_oracle"])
    date_pairs = [
        ("century_leap_2000", {"year":2000,"month":2,"day":28}, {"year":2000,"month":3,"day":1}),
        ("century_common_1900", {"year":1900,"month":2,"day":28}, {"year":1900,"month":3,"day":1}),
        ("leap_4000", {"year":4000,"month":2,"day":28}, {"year":4000,"month":3,"day":1}),
        ("year_edge_1", {"year":1,"month":1,"day":1}, {"year":1,"month":12,"day":31}),
        ("year_edge_9999", {"year":9999,"month":12,"day":30}, {"year":9999,"month":12,"day":31}),
    ]
    for name, start_parts, end_parts in date_pairs:
        start_date = date(**start_parts)
        end_date = date(**end_parts)
        add(f"civil_difference_{name}", "date_difference",
            {"start": start_parts, "end": end_parts}, (end_date - start_date).days,
            tags=["gregorian_independent_oracle", "date_difference_adversarial"])
        add(f"civil_difference_reverse_{name}", "date_difference",
            {"start": end_parts, "end": start_parts}, (start_date - end_date).days,
            tags=["gregorian_independent_oracle", "date_difference_adversarial"])
    add("civil_invalid_date", "validate_gregorian_date", {"year":1900,"month":2,"day":29}, "invalid Gregorian date", error=True)
    add("civil_date_difference_invalid_year", "date_difference",
        {"start":{"year":0,"month":1,"day":1},"end":{"year":1,"month":1,"day":1}},
        "invalid Gregorian date", error=True, tags=["date_difference_adversarial"])
    add("civil_add_below_domain", "add_gregorian_date",
        {"year":1,"month":1,"day":1,"unit":"days","amount":-1},
        "Gregorian date arithmetic out of range", error=True, tags=["date_arithmetic_domain"])
    add("civil_add_above_domain", "add_gregorian_date",
        {"year":9999,"month":12,"day":31,"unit":"days","amount":1},
        "Gregorian date arithmetic out of range", error=True, tags=["date_arithmetic_domain"])
    add("civil_reject_missing_day", "add_gregorian_date", {"year":2023,"month":1,"day":31,"unit":"months","amount":1}, "Gregorian date arithmetic out of range", error=True)
    add("civil_parse_shape", "parse_gregorian_date", {"text":"2024-2-01"}, "invalid Gregorian date", error=True)
    add("civil_interval_reversed", "date_interval", {"start":"2024-03-02","end":"2024-03-01"}, "invalid date interval", error=True)

    failures = [
        ("parse_decimal", {"text":"1e3","source_digits":"latin"}, "unsupported numeric notation"),
        ("parse_decimal", {"text":"12,34,56","source_digits":"latin","grouping":"indian"}, "invalid decimal string"),
        ("parse_decimal", {"text":"12.3","source_digits":"tamil"}, "invalid decimal string"),
        ("parse_decimal", {"text":"1.2","source_digits":"latin","grouping":"bad"}, "unsupported grouping"),
        ("parse_decimal", {"text":"1.2","source_digits":"bad"}, "unsupported digit style"),
        ("parse_decimal", {"text":"1." ,"source_digits":"latin"}, "invalid decimal string"),
        ("parse_decimal", {"text":"1 2","source_digits":"latin"}, "invalid decimal string"),
        ("parse_decimal", {"text":"1\u0be8","source_digits":"latin"}, "invalid decimal string"),
        ("format_decimal", {"value":{"negative":True,"coefficient":"0","scale":2}}, "invalid decimal value"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"01","scale":0}}, "invalid decimal value"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"1","scale":0},"digits":"bad"}, "unsupported digit style"),
        ("decimal_to_words", {"text":"1000000000","source_digits":"latin"}, "expected an integer in the supported range"),
        ("ordinal_to_words", {"value":0}, "expected a positive integer in the supported range"),
        ("digit_sequence_to_words", {"text":"001x","source_digits":"latin"}, "invalid digit sequence"),
        ("format_currency_decimal", {"amount":"1.000","source_digits":"latin","currency":"INR"}, "currency amount has more than two fractional digits"),
        ("parse_percent", {"text":"1 %","source_digits":"latin"}, "invalid decimal string"),
        ("symbol_info", {"text":"AB"}, "unsupported Tamil numeric symbol"),
        ("format_traditional_integer", {"value":100000000}, "expected a traditional Tamil integer in the supported range"),
        ("parse_traditional_integer", {"text":"\u0be6\u0be6\u0be7"}, "invalid canonical traditional Tamil integer"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":1,"denominator":2},"end":{"type":"fraction","numerator":1,"denominator":2},"start_inclusive":True,"end_inclusive":True,"separator":"","digits":"latin"}, "invalid numeric range"),
        ("parse_decimal", {"text":"1" + "0" * 256,"source_digits":"latin"}, "decimal precision exceeds supported range"),
        ("parse_decimal", {"text":"letters","source_digits":"latin"}, "invalid decimal string"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"1","scale":0,"extra":True}}, "invalid decimal value"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"1","scale":0},"digits":3}, "unsupported digit style"),
        ("format_mixed_fraction", {"negative":False,"whole":1,"numerator":1,"denominator":2,"digits":True}, "unsupported digit style"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":1,"denominator":2},"end":{"type":"fraction","numerator":3,"denominator":2},"start_inclusive":True,"end_inclusive":True,"separator":"..","digits":False}, "unsupported digit style"),
        ("add_gregorian_date", {"year":2024,"month":1,"day":31,"unit":"months","amount":1,"overflow":True}, "unsupported date overflow policy"),
        ("parse_decimal", {"text":" " * 1025,"source_digits":"latin"}, "decimal precision exceeds supported range"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"1","scale":257},"digits":"bad","grouping":"bad"}, "decimal precision exceeds supported range"),
        ("format_decimal", {"value":{"negative":False,"coefficient":"","scale":0},"digits":"bad","grouping":"bad"}, "invalid decimal value"),
        ("format_percent", {"value":{"negative":False,"coefficient":"01","scale":0},"digits":"bad","grouping":"bad"}, "invalid decimal value"),
        ("format_mixed_fraction", {"negative":False,"whole":1,"numerator":1,"denominator":0,"digits":"latin"}, "invalid mixed fraction"),
        ("format_mixed_fraction", {"negative":True,"whole":0,"numerator":0,"denominator":1,"digits":"latin"}, "invalid mixed fraction"),
        ("format_mixed_fraction", {"negative":False,"whole":1000000000,"numerator":0,"denominator":1,"digits":"latin"}, "invalid mixed fraction"),
        ("format_mixed_fraction", {"negative":False,"whole":1,"numerator":1,"denominator":1000000000,"digits":"latin"}, "invalid mixed fraction"),
        ("parse_mixed_fraction", {"text":"01 1/2","source_digits":"latin"}, "invalid mixed fraction"),
        ("parse_mixed_fraction", {"text":"1,000 1/2","source_digits":"latin"}, "invalid mixed fraction"),
        ("parse_mixed_fraction", {"text":"1 1/2  ","source_digits":"latin"}, "invalid mixed fraction"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":0,"denominator":0},"end":{"type":"decimal","value":{"negative":False,"coefficient":"0","scale":0}},"start_inclusive":True,"end_inclusive":True,"separator":".."}, "invalid numeric range"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":1000000000,"denominator":1},"end":{"type":"fraction","numerator":1000000000,"denominator":1},"start_inclusive":True,"end_inclusive":True,"separator":".."}, "invalid numeric range"),
        ("format_numeric_range", {"start":{"type":"decimal","value":{"negative":True,"coefficient":"0","scale":2}},"end":{"type":"decimal","value":{"negative":False,"coefficient":"1","scale":0}},"start_inclusive":True,"end_inclusive":True,"separator":".."}, "invalid numeric range"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":0,"denominator":1},"end":{"type":"fraction","numerator":1,"denominator":1},"start_inclusive":True,"end_inclusive":True,"separator":"123456789"}, "invalid numeric range"),
        ("format_numeric_range", {"start":{"type":"fraction","numerator":0,"denominator":1},"end":{"type":"fraction","numerator":1,"denominator":1},"start_inclusive":"true","end_inclusive":True,"separator":".."}, "invalid numeric range"),
    ]
    for index, (op, inputs, expected) in enumerate(failures):
        add(f"error_{index:03}", op, inputs, expected, error=True, tags=["numerals_v03_validation"])

    return cases


def render():
    return "".join(json.dumps(case, ensure_ascii=True, separators=(",", ":")) + "\n" for case in generate_cases())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Numerals v0.3 corpus differs; review pinned evidence")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
