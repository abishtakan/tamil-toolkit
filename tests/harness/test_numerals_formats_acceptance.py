import datetime
import tomllib
import xml.etree.ElementTree as ET
from fractions import Fraction

from tools.generate_numerals_formats_golden import OUTPUT,REFERENCE,ROOT,generate,references,render


def test_format_corpus_matches_independent_references():
    cases=generate()
    assert OUTPUT.read_text(encoding="utf-8")==render()
    assert len(cases)==4446 and sum("expected_error" in case for case in cases)==537
    assert {case["op"] for case in cases}=={"format_fraction","fraction_to_words","fraction_symbol","format_date"}
    assert {case["region"] for case in cases if "region" in case}=={"TN","KONGU","CHENNAI","JAFFNA","BATTICALOA","VANNI","UP_COUNTRY"}


def test_format_runtime_tables_agree_with_frozen_sources():
    profile,calendar,_,_,_,symbols=references()
    runtime=tomllib.loads((ROOT/"lexicon/numerals-formats.toml").read_text(encoding="utf-8"))
    assert runtime["profile"]==profile["profile"] and runtime["division"]==profile["division"]
    assert runtime["latin_digits"]==profile["digits"]["latn"]
    assert runtime["tamil_digits"]==profile["digits"]["tamldec"]=="".join(chr(code) for code in range(0x0BE6,0x0BF0))
    assert runtime["common_fractions"]==profile["common_fractions"]
    assert {Fraction(entry["numerator"],entry["denominator"]):entry["symbol"] for entry in runtime["symbols"]}==symbols
    assert calendar["cldr_version"]=="49.0.0.0" and calendar["profiles"]["TN"]==calendar["profiles"]["SL"]
    for key in ("months","abbreviated_months","weekdays"):assert runtime[key]==calendar["profiles"]["TN"][key]
    assert {entry["name"]:entry["pattern"] for entry in runtime["date_styles"]}==calendar["profiles"]["TN"]["patterns"]
    xml=ET.fromstring((REFERENCE/"calendar-ta.xml").read_bytes())
    assert [entry.text for entry in xml.findall('./months/monthContext[@type="format"]/monthWidth[@type="wide"]/month')]==runtime["months"]
    assert ET.fromstring((REFERENCE/"calendar-ta-LK.xml").read_bytes()).find('dateFormats') is None


def test_calendar_oracle_agrees_with_python_gregorian_and_digit_facts():
    profile,calendar,dates,_,_,_=references()
    assert len(dates)==154
    keys={(entry["year"],entry["month"],entry["day"]) for entry in dates}
    assert {(1,1,1),(1582,10,5),(1582,10,14),(2000,2,29),(2024,2,29),(9999,12,31)}<=keys
    assert (1900,2,29) not in keys and (2100,2,29) not in keys
    translation=str.maketrans(profile["digits"]["latn"],profile["digits"]["tamldec"])
    weekdays=set()
    for entry in dates:
        date=datetime.date(entry["year"],entry["month"],entry["day"])
        weekday=calendar["profiles"]["TN"]["weekdays"][(date.weekday()+1)%7];weekdays.add(weekday)
        for locale in ("TN","SL"):
            assert entry[locale]["full"]["latin"].split(',')[0]==weekday
            for style in ("short","medium","long","full"):
                assert entry[locale][style]["latin"].translate(translation)==entry[locale][style]["tamil"]
    assert len(weekdays)==7 and {entry["month"] for entry in dates}==set(range(1,13))


def test_fraction_reference_domain_and_unicode_alternates_are_complete():
    _,_,_,pairs,components,symbols=references()
    assert len(pairs)==328 and len(symbols)==18
    assert (0,-999999999) in map(tuple,pairs)
    assert (999999999,999999998) in map(tuple,pairs)
    assert symbols[Fraction(1,16)]==chr(0x11FC9) and symbols[Fraction(1,2)]==chr(0x11FD1)
    assert len([case for case in generate() if "every_unicode_fraction_form" in case["tags"]])==20
    for n,d in pairs:
        value=Fraction(n,d)
        assert abs(value.numerator) in components and value.denominator in components
