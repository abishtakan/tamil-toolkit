"""Offline exact-rational/ICU calendar fixtures; never import a runtime engine."""
import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, row  # noqa: E402
from tools.generate_numerals_golden import rule_tables  # noqa: E402

REFERENCE = ROOT / "tests/reference/numerals-v0.2"
OUTPUT = ROOT / "tests/golden/numerals_fractions_dates.jsonl"
SOURCE = "Unicode 17 fractions; ICU4J 79.1/CLDR 49; docs/specs/numerals-v0.2.md"


def references():
    metadata = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    for entry in metadata["files"]:
        if hashlib.sha256((REFERENCE / entry["file"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("numeral format reference checksum mismatch: " + entry["file"])
    def read(name): return json.loads((REFERENCE / name).read_text(encoding="utf-8"))
    profile = read("profile.json")
    calendar = read("calendar-data.json")
    dates = [json.loads(line) for line in (REFERENCE / "icu-dates.jsonl").read_text(encoding="utf-8").splitlines()]
    components = {entry["value"]: entry for entry in map(json.loads, (REFERENCE / "icu-components.jsonl").read_text(encoding="utf-8").splitlines())}
    symbols = {}
    for line in (REFERENCE / "UnicodeData-fractions.txt").read_text().splitlines():
        fields = line.split(";")
        if fields[0].startswith("11F"):
            symbols.setdefault(Fraction(fields[8]), chr(int(fields[0], 16)))
    return profile, calendar, dates, read("fraction-inputs.json"), components, symbols


def generate():
    profile, _, dates, pairs, components, symbols = references()
    _, negative, _ = rule_tables()
    named = {Fraction(entry["numerator"], entry["denominator"]): entry["words"] for entry in profile["common_fractions"]}
    cases = []
    def add(identifier, op, inputs, expected, *, error=False, dialect="COMMON", region=None, tags=None):
        cases.append(row("formats_" + identifier, op, inputs, expected, tags or ["numerals_formats_v1"], SOURCE,
                         error=error, dialect=dialect, region=region))
    def words(value, locale):
        prefix = negative + " " if value < 0 else ""
        value = abs(value)
        if value.denominator == 1: return prefix + components[value.numerator][locale]["numbering"]
        if value in named: return prefix + named[value]
        return prefix + components[value.numerator][locale]["numbering"] + " " + profile["division"] + " " + components[value.denominator][locale]["numbering"]
    digit_map = str.maketrans(profile["digits"]["latn"], profile["digits"]["tamldec"])
    for index, (n, d) in enumerate(pairs):
        value = Fraction(n, d)
        ratio = f"{value.numerator}/{value.denominator}"
        inputs = {"numerator": n, "denominator": d}
        for digits in ("latin", "tamil"):
            add(f"ratio_{index:03}_{digits}", "format_fraction", {**inputs, "digits": digits}, ratio if digits == "latin" else ratio.translate(digit_map))
        for locale in ("TN", "SL"):
            add(f"fraction_words_{index:03}_{locale.lower()}", "fraction_to_words", {**inputs, "locale": locale}, words(value, locale), dialect=locale)
        symbol = symbols.get(abs(value))
        add(f"symbol_{index:03}", "fraction_symbol", inputs, ("-" if value < 0 else "") + symbol if symbol else "no traditional Tamil symbol for this fraction", error=symbol is None)
    for line in (REFERENCE / "UnicodeData-fractions.txt").read_text().splitlines():
        fields = line.split(";")
        if fields[0].startswith("11F"):
            f = Fraction(fields[8])
            add("symbol_source_" + fields[0].lower(), "fraction_symbol", {"numerator": f.numerator, "denominator": f.denominator}, symbols[f], tags=["every_unicode_fraction_form"])
    for index, entry in enumerate(dates):
        for locale in ("TN", "SL"):
            for style in ("short", "medium", "long", "full"):
                for digits in ("latin", "tamil"):
                    inputs = {key: entry[key] for key in ("year", "month", "day")}
                    add(f"date_{index:03}_{locale.lower()}_{style}_{digits}", "format_date", {**inputs, "locale": locale, "style": style, "digits": digits}, entry[locale][style][digits], dialect=locale, tags=["independent_icu_date"])
    leap = next(entry for entry in dates if (entry["year"],entry["month"],entry["day"]) == (2024,2,29))
    add("date_defaults", "format_date", {"year":2024,"month":2,"day":29}, leap["TN"]["long"]["latin"])
    add("date_integral_json", "format_date", {"year":2024.0,"month":2.0,"day":29.0}, leap["TN"]["long"]["latin"])
    add("ratio_defaults", "format_fraction", {"numerator":1.0,"denominator":2.0}, "1/2")
    add("words_defaults", "fraction_to_words", {"numerator":1.0,"denominator":2.0}, named[Fraction(1,2)])
    regions = [("TN","TN"),("TN","KONGU"),("TN","CHENNAI"),("SL","JAFFNA"),("SL","BATTICALOA"),("SL","VANNI"),("SL","UP_COUNTRY")]
    for locale, region in regions:
        add("date_region_" + region.lower(), "format_date", {"year":2024,"month":2,"day":29,"locale":locale,"style":"full"}, leap[locale]["full"]["latin"], dialect=locale, region=region)
        add("fraction_region_" + region.lower(), "fraction_to_words", {"numerator":100000,"denominator":3,"locale":locale}, words(Fraction(100000,3),locale), dialect=locale, region=region)
    failures = []
    fraction_ops = ("format_fraction","fraction_to_words","fraction_symbol")
    integer_error = "expected an integer in the supported range"
    for op in fraction_ops:
        for field in ("numerator","denominator"):
            for value in (None,True,"1",1.25,[],{},1000000000,-1000000000):
                inputs={"numerator":1,"denominator":2}; inputs[field]=value
                failures.append((op,inputs,integer_error))
        for inputs in (None,True,1,[],{}, {"numerator":1},{"denominator":2}): failures.append((op,inputs,integer_error))
        failures.append((op,{"numerator":1,"denominator":0},"fraction denominator must not be zero"))
    for digits in (None,True,1,[],"","tamldec","TAMIL"):
        failures.append(("format_fraction",{"numerator":1,"denominator":2,"digits":digits},"unsupported digit style"))
    for locale in (None,True,1,[],"","XX","tn"):
        failures.append(("fraction_to_words",{"numerator":1,"denominator":2,"locale":locale},"unsupported locale"))
    bad_dates = [(0,1,1),(-1,1,1),(10000,1,1),(2024,0,1),(2024,13,1),(2024,1,0),(2024,1,32)]
    bad_dates += [(y,2,29) for y in (1,100,1900,2100,9999)]
    bad_dates += [(y,m,31) for y in (2023,2024) for m in (4,6,9,11)]
    for y,m,d in bad_dates: failures.append(("format_date",{"year":y,"month":m,"day":d},"invalid Gregorian date"))
    for field in ("year","month","day"):
        for value in (None,True,"1",1.25,[],{}):
            inputs={"year":2024,"month":2,"day":29}; inputs[field]=value
            failures.append(("format_date",inputs,"invalid Gregorian date"))
    for inputs in (None,True,1,[],{}, {"year":2024},{"year":2024,"month":2}): failures.append(("format_date",inputs,"invalid Gregorian date"))
    for field,error in [("locale","unsupported locale"),("style","unsupported date style"),("digits","unsupported digit style")]:
        for value in (None,True,1,[],"","unknown"):
            inputs={"year":2024,"month":2,"day":29}; inputs[field]=value
            failures.append(("format_date",inputs,error))
    failures.extend([
        ("format_date",{"year":2023,"month":2,"day":29,"locale":"XX","style":"x","digits":"x"},"invalid Gregorian date"),
        ("fraction_to_words",{"numerator":1,"denominator":0,"locale":"XX"},"fraction denominator must not be zero"),
        ("format_fraction",{"numerator":1,"denominator":0,"digits":"x"},"fraction denominator must not be zero"),
    ])
    for index,(op,inputs,message) in enumerate(failures):
        for dialect in ("TN","SL"): add(f"error_{index:03}_{dialect.lower()}",op,inputs,message,error=True,dialect=dialect,tags=["shared_error"])
    return cases


def render(): return "".join(json.dumps(case,ensure_ascii=True,separators=(",",":"))+"\n" for case in generate())


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--check",action="store_true");args=parser.parse_args();content=render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8")!=content: raise SystemExit("Numeral format corpus differs; review pinned evidence")
    else: OUTPUT.write_text(content,encoding="utf-8",newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
