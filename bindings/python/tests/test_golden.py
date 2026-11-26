import csv
import json
import os
from pathlib import Path
import pytest
import tamil_toolkit as tamil
import tomllib

from tools.harness import load_vectors, select_vectors, selected_planned_suites, vector_request


_REPO_ROOT = Path(__file__).resolve().parents[3]
_PACK_DIRS = {
    "core": _REPO_ROOT / "lexicon/dictionary",
    "names_taxa": _REPO_ROOT / "lexicon/packs/names_taxa",
    "regional": _REPO_ROOT / "lexicon/packs/regional",
}


def infer_compiled_python_profile() -> str:
    packs = tamil.lexicon_packs()
    if packs == []:
        return "default"
    if len(packs) == 1 and packs[0].get("id") == "core" and packs[0].get("available") is True:
        return "core"
    if (
        len(packs) == 3
        and [pack.get("id") for pack in packs] == ["core", "names_taxa", "regional"]
        and all(pack.get("available") is True for pack in packs)
    ):
        return "full"
    raise AssertionError(f"Unsupported compiled Python lexicon packs: {packs!r}")


def resolve_python_profile() -> str:
    compiled_profile = infer_compiled_python_profile()
    env_profile = os.environ.get("TAMIL_LEXICON_PROFILE")
    if env_profile is not None:
        if env_profile not in ("default", "core", "full"):
            raise AssertionError(
                f"Unsupported TAMIL_LEXICON_PROFILE={env_profile!r} (expected 'default', 'core', or 'full')"
            )
        if env_profile != compiled_profile:
            raise AssertionError(
                f"TAMIL_LEXICON_PROFILE={env_profile!r} does not match compiled Python binding profile {compiled_profile!r}"
            )
        return env_profile
    return compiled_profile


def test_golden():
    profile = resolve_python_profile()
    selection = select_vectors(include_planned=selected_planned_suites(), profile=profile)
    cases = selection.vectors
    assert cases
    if profile == "core":
        assert selection.core_profile_count > 0
        assert selection.excluded_profile_count == 0
    elif profile == "full":
        manifest = json.loads((_REPO_ROOT / "tests/golden/manifest.json").read_text(encoding="utf-8"))
        has_declared_full = any(
            suite.get("status") == "active" and suite.get("required_profile") == "full"
            for suite in manifest.get("suites", [])
        )
        if has_declared_full:
            assert selection.full_profile_count > 0
    for filename, req_profile, row_count in selection.excluded_profile_suites:
        print(
            f"PROFILE_EXCLUDED {filename}: requires profile {req_profile!r} "
            f"(active profile {profile!r}; {row_count} vectors excluded)"
        )
    print(
        f"Python selected {selection.active_count} active golden vectors for profile {profile!r} "
        f"(excluded {selection.excluded_profile_count} active vectors requiring other profiles)."
    )
    for case in cases:
        if "expected_error" in case:
            assert "expected" not in case, case["id"]
            with pytest.raises(ValueError) as failure:
                tamil.execute(vector_request(case))
            assert str(failure.value) == case["expected_error"], case["id"]
        else:
            assert "expected" in case, case["id"]
            assert tamil.execute(vector_request(case)) == case["expected"], case["id"]


def test_tokenizer_convenience_api():
    from tamil_toolkit import segment_sentences, tokenize_words

    rows = (_REPO_ROOT / "tests/golden/tokenize_v01.jsonl").read_text(encoding="utf-8").splitlines()
    fixture = next(row for row in map(json.loads, rows) if row["id"] == "tokenize_decomposed_mixed")
    text = fixture["input"]["text"]
    token = tokenize_words(text)[1]
    assert token["text"] == text.encode()[2:11].decode()
    assert (token["start_byte"], token["end_byte"]) == (2, 11)
    assert (token["start_unit"], token["end_unit"]) == (2, 3)
    first = segment_sentences(text)[0]
    assert first["text"] == text.encode()[first["start_byte"]:first["end_byte"]].decode()
    with pytest.raises(ValueError, match="^unsupported stopword profile$"):
        tokenize_words(text, stopword_profile="unknown")


def test_phonology_and_olippasai_convenience_api():
    assert tamil.classify_quantity("\u0b85") == "kuril"
    assert tamil.classify_quantity("\u0b86") == "nedil"
    assert tamil.baseline_maathirai("\u0b95") == 1.0
    assert tamil.is_kuril("\u0b95\u0bbf")
    assert tamil.is_nedil("\u0b95\u0bbe")
    assert tamil.is_mei("\u0b95\u0bcd")
    assert tamil.is_otru("\u0ba4\u0bcd")
    assert tamil.is_aytham("\u0b83")
    assert tamil.get_cognate("\u0b95\u0bbe") == "\u0b99\u0bbe"
    assert tamil.are_cognates("\u0ba4\u0bcd", "\u0ba8\u0bcd")
    assert not tamil.are_cognates("\u0ba4\u0bcd", "\u0bae\u0bcd")
    syllables = tamil.get_olippasai("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")
    assert len(syllables) == 2
    assert syllables[0]["text"] == "\u0ba4"
    assert syllables[1]["text"] == "\u0bae\u0bbf\u0bb4\u0bcd"


def test_vakyakarana_true_moon_convenience_api():
    result = tamil.vakya_true_moon_from_kali_day(1_844_004)
    assert result["moon_vakya_number"] == 154
    assert result["uncorrected_true_moon"] == {
        "rasi": 4, "degrees": 11, "minutes": 14, "seconds": 1,
    }
    assert result["true_moon"] == {
        "rasi": 4, "degrees": 11, "minutes": 17, "seconds": 32,
    }


def test_official_holiday_schedule_convenience_api():
    tn = tamil.calendar_official_holidays("TN", 2025)
    assert tn["source_sha256"] is None
    assert len(tn["holidays"]) == 24
    assert tn["holidays"][1]["name"] == "Pongal"
    sl = tamil.calendar_official_holidays("SL", 2027)
    assert sl["source_sha256"] == "9071010e6d253e72aee4cdd40057cebc2dfc98e45e713de65ceb9d209cb09eb9"
    assert len(sl["holidays"]) == 25


def test_named_observance_convenience_api():
    result = tamil.calendar_observances(2026, {
        "region": "TN",
        "latitude_microdegrees": 13_087_840,
        "longitude_microdegrees": 80_278_470,
        "elevation_meters": 14,
        "time_zone": "Asia/Kolkata",
    })
    assert result["rule_set_id"] == "thirukanitham-tamil-named-observances-v1"
    assert result["source_compatibility"] == "publisher_equivalence_not_claimed"
    assert "amavasya_tithi_day" in result["supported_event_ids"]
    assert result["events"]


def test_vakyakarana_local_sunrise_convenience_api():
    result = tamil.vakya_reduce_to_local_true_sunrise(
        {"rasi": 4, "degrees": 11, "minutes": 17, "seconds": 32},
        {"degrees": 14, "minutes": 12, "seconds": 0},
        130,
        -266,
        -210,
    )
    assert result["correction_arcseconds"] == -491
    assert result["local_true_position"] == {
        "rasi": 4, "degrees": 11, "minutes": 9, "seconds": 21,
    }


def test_vakyakarana_cara_convenience_api():
    result = tamil.vakya_cara_from_sayana_sun(
        {"rasi": 4, "degrees": 22, "minutes": 30, "seconds": 0}, 30,
    )
    assert result["bhuja"] == {
        "rasi": 1, "degrees": 7, "minutes": 30, "seconds": 0,
    }
    assert result["cara_vinadi_tenths"] == -720


def test_vakyakarana_desantara_convenience_api():
    east = tamil.vakya_desantara_from_yojana_distance(244)
    west = tamil.vakya_desantara_from_yojana_distance(-244)
    assert east["desantara_vinadi_tenths"] == -266
    assert west["desantara_vinadi_tenths"] == 266


def test_vakyakarana_bhujaantara_convenience_api():
    example = tamil.vakya_bhujaantara_from_true_sun(5, 84_513)
    midpoint = tamil.vakya_bhujaantara_from_true_sun(0, 54_000)
    assert example["bhujaantara_vinadi_tenths"] == -210
    assert midpoint["bhujaantara_vinadi_tenths"] == 185


@pytest.mark.parametrize("payload", [
    {"op": "unknown", "input": ""},
    {"op": "get_letters", "input": 1},
    {"op": "split_uyirmei", "input": "\u0b95\u0bcd"},
])
def test_errors_cross_ffi(payload):
    with pytest.raises(ValueError):
        tamil.execute(payload)


def test_collation_convenience_apis():
    cases = {case["id"]: case for case in load_vectors(profile=resolve_python_profile())}
    word_case = cases["collate_words_basic"]
    key_case = cases["collate_key_001"]
    assert tamil.sort_words(word_case["input"]) == word_case["expected"]
    assert tamil.sort_key(key_case["input"]) == key_case["expected"]
    assert tamil.search_key(key_case["input"]) == key_case["expected"]
    assert tamil.compare(key_case["input"], key_case["input"]) == 0


def test_numeral_convenience_apis():
    cases = {case["id"]: case for case in load_vectors(profile=resolve_python_profile())}
    assert tamil.to_words(1025, "SL") == cases["num_014"]["expected"]
    assert tamil.to_words(100000) == cases["number_default_locale"]["expected"]
    for case in cases.values():
        if case["op"] in ("format_currency", "currency_to_words") and "expected" in case:
            assert getattr(tamil, case["op"])(**case["input"]) == case["expected"]
    with pytest.raises(ValueError, match="unsupported currency"):
        tamil.format_currency(1, "ZZZ")


def test_codec_convenience_api():
    cases = {case["id"]: case for case in load_vectors(profile=resolve_python_profile())}
    word = cases["codec_word_000_tn_strict"]
    preserved = cases["codec_joiner_boundary_0"]
    assert tamil.bamini_to_unicode(word["input"]["text"]) == word["expected"]
    assert tamil.bamini_to_unicode(**preserved["input"]) == preserved["expected"]
    with pytest.raises(ValueError, match="ambiguous Bamini sequence"):
        tamil.bamini_to_unicode("*")
    with pytest.raises(ValueError, match="unsupported codec error policy"):
        tamil.bamini_to_unicode("f", "ignore")


def test_encoder_convenience_api():
    cases = {case["id"]: case for case in load_vectors(profile=resolve_python_profile())}
    word = cases["encode_word_000_tn"]
    encoded = tamil.unicode_to_bamini(word["input"]["text"])
    assert encoded == word["expected"]
    assert tamil.bamini_to_unicode(encoded) == tamil.normalize_nfc(word["input"]["text"])
    decomposed = next(case for case in cases.values() if case["id"].startswith("encode_mapping_") and case["id"].endswith("_tn_nfd"))
    assert tamil.unicode_to_bamini(decomposed["input"]["text"]) == decomposed["expected"]
    collision = cases["encode_collision_000_tn"]
    with pytest.raises(ValueError) as failure:
        tamil.unicode_to_bamini(collision["input"]["text"])
    assert str(failure.value) == collision["expected_error"]


def test_tscii_byte_convenience_api():
    assert tamil.tscii_bytes_to_unicode(bytes([0xba, 0xa2, 0xc5, 0xfd])) == "\u0b9a\u0bbf\u0bb5\u0ba9\u0bcd"
    assert tamil.unicode_to_tscii_bytes("\u0b87") == bytes([0xfe])
    with pytest.raises(ValueError, match="unsupported TSCII byte at offset 1: 0xFF"):
        tamil.tscii_bytes_to_unicode([65, 255])


def test_fraction_and_date_convenience_apis():
    for case in load_vectors(profile=resolve_python_profile()):
        if case["op"] in ("format_fraction", "fraction_to_words", "fraction_symbol", "format_date") and "expected" in case:
            assert getattr(tamil, case["op"])(**case["input"]) == case["expected"]
    with pytest.raises(ValueError, match="fraction denominator must not be zero"):
        tamil.format_fraction(1, 0)
    with pytest.raises(ValueError, match="invalid Gregorian date"):
        tamil.format_date(2023, 2, 29)


def test_numerals_v03_typed_convenience_apis():
    cases = load_vectors(include_planned=selected_planned_suites(), profile=resolve_python_profile())
    value = tamil.parse_decimal("12.3400", "latin")
    assert value == {"negative": False, "coefficient": "123400", "scale": 4}
    assert tamil.format_decimal(value) == "12.3400"
    assert tamil.format_decimal(value, digits="tamil") == "௧௨.௩௪௦௦"
    assert tamil.decimal_to_words("12.03", "latin").endswith("\u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd \u0bae\u0bc2\u0ba9\u0bcd\u0bb1\u0bc1")
    assert tamil.ordinal_to_words(21) == next(case["expected"] for case in cases if case["id"] == "n3_ordinal_21_tn")
    assert tamil.digit_sequence_to_words("0071", "latin").startswith("\u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd \u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd")
    assert tamil.format_currency_decimal("123.45", "latin", "LKR") == "LKR 123.45"
    assert tamil.parse_fraction_symbol("-\U00011fd1") == {"numerator": -1, "denominator": 2}
    assert tamil.symbol_info("\U00011fd1")["canonical_alternative"] == 73681
    mixed = tamil.parse_mixed_fraction(tamil.format_mixed_fraction(False, 5, 2, 4), "latin")
    assert mixed == {"negative": False, "whole": 5, "numerator": 1, "denominator": 2}
    assert tamil.mixed_fraction_to_words(False, 1, 1, 2) == "\u0b92\u0ba9\u0bcd\u0bb1\u0bb0\u0bc8"
    assert tamil.words_to_number(tamil.to_words(100001, "SL"), "SL") == 100001
    assert tamil.format_currency(10000021, "SGD") == "SGD 100,000.21"
    traditional = tamil.format_traditional_integer(1234567)
    assert tamil.parse_traditional_integer(traditional) == 1234567
    assert tamil.parse_percent("12.50%", "latin") == {"negative": False, "coefficient": "1250", "scale": 2}
    assert tamil.ratio_to_percent({"negative": False, "coefficient": "125", "scale": 3}) == {"negative": False, "coefficient": "125", "scale": 1}
    assert tamil.format_numeric_range({"type": "fraction", "numerator": 1, "denominator": 4}, {"type": "decimal", "value": {"negative": False, "coefficient": "5", "scale": 0}}, False, True, " to ") == "(1/4 to 5]"
    assert tamil.weekday(2024, 1, 1) == "monday"
    assert tamil.add_gregorian_date(2024, 1, 31, "months", 1, "clamp") == {"year": 2024, "month": 2, "day": 29}
    assert tamil.date_difference({"year": 2024, "month": 2, "day": 28}, {"year": 2024, "month": 3, "day": 1}) == 2
    assert tamil.date_interval("2024-02-28", "2024-03-01")["inclusive_days"] == 3


def test_historical_vakya_solar_convenience_apis():
    year = tamil.vakya_solar_transits(1890)
    assert year["ahargana"] == {"days": 1_851_494, "nadi": 6, "vinadi": 15, "weekday": "Saturday"}
    assert year["transits"][0] == {"rasi": "vrishabha", "day_field": 4, "weekday": "Tuesday", "nadi": 1, "vinadi": 47}
    sun = tamil.vakya_true_sun_from_mesha_elapsed(180, 19, 41)
    assert sun["true_sun"] == {"degrees": 173, "minutes": 28, "seconds": 33}


def test_thirukanitham_typed_convenience_apis():
    context = {
        "region": "TN", "latitude_microdegrees": 13087840,
        "longitude_microdegrees": 80278470, "elevation_meters": 14,
        "time_zone": "Asia/Kolkata",
    }
    profile = tamil.calendar_profile_info()
    assert profile["definition_id"] == tamil.THIRUKANITHAM_DEFINITION
    date = {"year": 2026, "month": 11, "day": 1}
    converted = tamil.gregorian_to_tamil_date(date, context)
    assert converted["tamil_date"] == {
        "solar_year": 2026, "month": 7, "month_name": "Aippasi", "day": 15,
    }
    assert tamil.tamil_to_gregorian_date(converted["tamil_date"], context)["gregorian_date"] == date
    month = tamil.tamil_month_info(2026, 7, context)
    assert month["days"] == 30
    assert month["start_date"] == {"year": 2026, "month": 10, "day": 18}
    year = tamil.tamil_year_info(2025, context)
    assert year["days"] == 365 and len(year["months"]) == 12
    assert year["start_date"] == {"year": 2025, "month": 4, "day": 14}
    assert year["year_cycle"]["cycle_name"] == "Visvavasu"
    assert tamil.tamil_year_cycle_info(2024, context)["cycle_name"] == "Krodhi"
    assert tamil.add_tamil_date(
        {"solar_year": 2025, "month": 1, "day": 1}, "days", 1, context
    )["gregorian_date"] == {"year": 2025, "month": 4, "day": 15}
    instant = tamil.panchangam_at(1793514600, context)
    assert instant["limbs"]["tithi"]["name"] == "Saptami"
    assert instant["vara"] == "Sunday"
    day = tamil.panchangam_day(date, context)
    assert day["sunrise_minute_of_day"] == 362
    assert len(day["transitions"]) == 5
    periods = tamil.calendar_daylight_periods({"year": 2026, "month": 11, "day": 1}, context)
    assert [period["period"] for period in periods["intervals"]] == [
        "yamagandam", "kuligai", "rahukalam",
    ]
    assert periods["intervals"][0]["eighth_part"] == 5


def test_vakya_civil_typed_convenience_apis():
    context = {"reference_station": "ujjain", "time_zone": "Asia/Kolkata"}
    definition = tamil.VAKYA_CIVIL_DEFINITION
    assert tamil.calendar_profile_info(definition)["day_boundary"] == "ujjain_mean_sunrise"
    date = {"year": 1947, "month": 10, "day": 11}
    converted = tamil.gregorian_to_tamil_date(date, context, definition)
    assert converted["tamil_date"] == {
        "solar_year": 1947, "month": 6, "month_name": "Purattasi", "day": 24,
    }
    assert tamil.tamil_to_gregorian_date(converted["tamil_date"], context, definition)["gregorian_date"] == date
    assert tamil.tamil_month_info(1947, 6, context, definition)["days"] == 30
    year = tamil.tamil_year_info(1947, context, definition)
    assert year["days"] == 365 and len(year["months"]) == 12
    assert year["reference_station"] == "ujjain"
    assert year["year_cycle"]["cycle_name"] == "Sarvajit"
    assert tamil.tamil_year_cycle_info(1947, context, definition)["cycle_index"] == 21
    assert tamil.add_tamil_date(
        {"solar_year": 1947, "month": 6, "day": 24}, "days", 1,
        context, definition_id=definition,
    )["gregorian_date"] == {"year": 1947, "month": 10, "day": 12}
    at = tamil.panchangam_at(-701391788, context, definition)
    assert at["limbs"]["tithi"]["name"] == "Dwadashi"
    assert at["reference_station"] == "ujjain"
    day = tamil.panchangam_day(date, context, definition)
    assert day["sunrise_minute_of_day"] == 387
    assert day["sunset_minute_of_day"] is None
    assert day["sunset_status"] == "unavailable_source_bhujaantara_interpolation_unresolved"


def test_thirukanitham_lunar_phase_typed_api_matches_usno_minutes():
    phases = tamil.lunar_phase_events(1736121600, 1738195200)
    assert [event["phase"] for event in phases["events"]] == [
        "first_quarter", "full_moon", "last_quarter", "new_moon",
    ]
    assert [event["utc_minute"] for event in phases["events"]] == [
        {"year": 2025, "month": 1, "day": 6, "hour": 23, "minute": 56},
        {"year": 2025, "month": 1, "day": 13, "hour": 22, "minute": 27},
        {"year": 2025, "month": 1, "day": 21, "hour": 20, "minute": 31},
        {"year": 2025, "month": 1, "day": 29, "hour": 12, "minute": 36},
    ]


def test_tab_byte_convenience_apis():
    assert tamil.tab_bytes_to_unicode(bytes([0xe8, 0xa4])) == "\u0b95\u0bbf"
    assert tamil.unicode_to_tab_bytes("\u0b95\u0bbf") == bytes([0xe8, 0xa4])
    with pytest.raises(ValueError, match="unsupported TAB byte"):
        tamil.tab_bytes_to_unicode([0x98])


def test_tam_byte_convenience_apis():
    assert tamil.tam_bytes_to_unicode(bytes([0x41])) == "\u0b95\u0bbf"
    assert tamil.unicode_to_tam_bytes("\u0b95\u0bbf") == bytes([0x41])
    with pytest.raises(ValueError, match="unsupported Unicode scalar for TAM"):
        tamil.unicode_to_tam_bytes("A")


def test_anjal_byte_convenience_apis():
    assert tamil.anjal_bytes_to_unicode(bytes([0x8d])) == "\u0b95"
    assert tamil.unicode_to_anjal_bytes("\u0b95") == bytes([0x8d])
    with pytest.raises(ValueError, match="ambiguous ANJAL byte"):
        tamil.anjal_bytes_to_unicode([0xe5])


def test_vanavil_convenience_apis():
    assert tamil.vanavil_codes_to_unicode([0x006a, 0x00e4, 0x0153]) == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
    assert tamil.vanavil_text_to_unicode("j\u00e4\u0153") == "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
    assert tamil.unicode_to_vanavil_codes("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd") == [0x006a, 0x00e4, 0x0153]
    assert tamil.unicode_to_vanavil_text("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd") == "j\u00e4\u0153"
    with pytest.raises(ValueError, match="unsupported Unicode scalar for Vanavil"):
        tamil.unicode_to_vanavil_text("\u0bb6\u0bcd\u0bb0\u0bc0")


def test_hyphen_convenience_apis():
    res = tamil.hyphenate_word("தமிழ்நாடு")
    assert res["hyphenated"] == "தமிழ்\u00adநாடு"
    assert tamil.hyphenate_text("வணக்கம் தமிழ்நாடு") == "வணக்\u00adகம் தமிழ்\u00adநாடு"


def test_process_docx_convenience_api(tmp_path):
    import zipfile

    docx_in = tmp_path / "test_in.docx"
    docx_out = tmp_path / "test_out.docx"

    with zipfile.ZipFile(docx_in, "w") as zf:
        zf.writestr("[Content_Types].xml", b"<Types/>")
        zf.writestr(
            "word/document.xml",
            "<w:document><w:body><w:p><w:r><w:t>தமிழ்நாடு</w:t></w:r></w:p></w:body></w:document>".encode("utf-8"),
        )

    stats = tamil.process_docx(str(docx_in), str(docx_out))
    assert stats["parts_updated"] == 1
    assert stats["paragraphs_processed"] == 1
    assert stats["words_hyphenated"] >= 1
    assert stats["soft_hyphens_inserted"] >= 1

    with zipfile.ZipFile(docx_out, "r") as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        assert "தமிழ்\u00adநாடு" in xml



def test_norm_convenience_apis():
    res = tamil.repair_tamil_text("\u0b95\u0bcd\u0bcd")
    assert res["text"] == "\u0b95\u0bcd"
    assert res["diagnostics"]["duplicate_pulli_count"] == 1
    assert res["diagnostics"]["total_repairs"] == 1

    assert tamil.fold_for_search("\u0baa\u0bb4\u0bae\u0bcd", "mayangoli") == "\u0baa\u0bb2\u0bae\u0bcd"
    assert tamil.fold_for_search("\u0bb0\u0bbe\u0b9c\u0bbe", "grantha") == "\u0bb0\u0bbe\u0b9a\u0bbe"


def _read_pack_manifest(pack_id: str) -> dict:
    return tomllib.loads((_PACK_DIRS[pack_id] / "packs.toml").read_text(encoding="utf-8"))


def _first_canonical_written_form(pack_id: str) -> str:
    assertions_csv = _PACK_DIRS[pack_id] / "assertions.csv"
    with assertions_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("subject_kind") == "form":
                parsed = json.loads(row["value_json"])
                if isinstance(parsed, str) and parsed:
                    return parsed
    raise AssertionError(f"No canonical form assertion found in {assertions_csv}")


def _absent_golden_input() -> str:
    path = _REPO_ROOT / "tests/golden/lexicon_lookup.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        if case.get("id") == "lexicon_lookup_not_found_absent_007":
            assert case["expected"]["status"] == "not_found"
            return case["input"]
    raise AssertionError("Missing lexicon_lookup_not_found_absent_007 golden vector")


def _assert_pack_matches_manifest(pack: dict, manifest: dict) -> None:
    assert pack["id"] == manifest["pack_id"]
    assert pack["dataset_version"] == manifest["dataset_version"]
    assert pack["schema_version"] == manifest["schema_version"]
    assert pack["index_format_version"] == manifest["index_format_version"]
    assert pack["manifest_sha256"] == manifest["manifest_sha256"]
    assert pack["available"] is True
    assert pack["coverage"] == manifest["coverage"]


def test_lexicon_profile_and_convenience_api():
    profile = resolve_python_profile()
    select_vectors(include_planned=selected_planned_suites(), profile=profile)
    absent_input = _absent_golden_input()

    if profile == "default":
        assert tamil.lexicon_packs() == []
        with pytest.raises(ValueError, match=r"^lexicon: pack unavailable 'core'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf")
        with pytest.raises(ValueError, match=r"^lexicon: packs must be a nonempty string array$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=[])
        with pytest.raises(ValueError, match=r"^lexicon: unknown pack 'unknown'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=["unknown"])
    elif profile == "core":
        manifest = _read_pack_manifest("core")
        packs = tamil.lexicon_packs()
        assert len(packs) == 1
        core = packs[0]
        _assert_pack_matches_manifest(core, manifest)
        env_sha = os.environ.get("TAMIL_LEXICON_MANIFEST_SHA256")
        if env_sha:
            assert core["manifest_sha256"] == env_sha
        env_ver = os.environ.get("TAMIL_LEXICON_DATASET_VERSION")
        if env_ver:
            assert core["dataset_version"] == env_ver

        matched = tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf")
        assert matched["status"] == "matched"
        assert len(matched["entries"]) == 2
        assert matched["packs"] == [core]
        assert tamil.lexicon_lookup("\u0b85\u0b9f\u0b9f\u0bbe", packs=["core"])["status"] == "matched"
        missing = tamil.lexicon_lookup(absent_input)
        assert missing["status"] == "not_found"
        assert missing["entries"] == []

        with pytest.raises(ValueError, match=r"^lexicon: packs must be a nonempty string array$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=[])
        with pytest.raises(ValueError, match=r"^lexicon: pack unavailable 'regional'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=["regional"])
        with pytest.raises(ValueError, match=r"^lexicon: unknown region 'LK-JAFFNA'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", region="LK-JAFFNA")
        with pytest.raises(ValueError, match=r"^lexicon: unknown register 'written'$"):
            tamil.lexicon_lookup("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8", register="written")
    elif profile == "full":
        packs = tamil.lexicon_packs()
        assert [pack["id"] for pack in packs] == ["core", "names_taxa", "regional"]
        raw_env_manifests = os.environ.get("TAMIL_LEXICON_PACK_MANIFESTS")
        env_manifests = json.loads(raw_env_manifests) if raw_env_manifests else None
        for pack, pack_id in zip(packs, ("core", "names_taxa", "regional")):
            manifest = _read_pack_manifest(pack_id)
            _assert_pack_matches_manifest(pack, manifest)
            if env_manifests is not None:
                expected = env_manifests[pack_id]
                assert pack["dataset_version"] == expected["dataset_version"]
                assert pack["manifest_sha256"] == expected["manifest_sha256"]
        core = packs[0]
        env_sha = os.environ.get("TAMIL_LEXICON_MANIFEST_SHA256")
        if env_sha:
            assert core["manifest_sha256"] == env_sha
        env_ver = os.environ.get("TAMIL_LEXICON_DATASET_VERSION")
        if env_ver:
            assert core["dataset_version"] == env_ver

        matched = tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf")
        assert matched["status"] == "matched"
        assert len(matched["entries"]) == 2
        assert matched["packs"] == [core]
        all_packs = tamil.lexicon_lookup(
            "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=["core", "names_taxa", "regional"]
        )
        assert all_packs["status"] == "matched"
        assert all_packs["packs"] == packs
        for pack_id in ("names_taxa", "regional"):
            sample = _first_canonical_written_form(pack_id)
            pack_match = tamil.lexicon_lookup(sample, packs=[pack_id])
            assert pack_match["status"] == "matched"
            assert pack_match["entries"]
        missing = tamil.lexicon_lookup(absent_input)
        assert missing["status"] == "not_found"
        assert missing["entries"] == []

        with pytest.raises(ValueError, match=r"^lexicon: pack unavailable 'terminology'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=["terminology"])
        with pytest.raises(ValueError, match=r"^lexicon: packs must be a nonempty string array$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=[])
        with pytest.raises(ValueError, match=r"^lexicon: unknown pack 'unknown'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", packs=["unknown"])
        with pytest.raises(ValueError, match=r"^lexicon: unknown region 'LK-JAFFNA'$"):
            tamil.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", region="LK-JAFFNA")
        with pytest.raises(ValueError, match=r"^lexicon: unknown register 'written'$"):
            tamil.lexicon_lookup("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8", register="written")
    else:
        pytest.fail(f"Unsupported TAMIL_LEXICON_PROFILE={profile!r}")


def test_punarchi_convenience_api():
    joined = tamil.punarchi_join(
        "மரம்",
        "ஐ",
        context={"relation": "vetrumai", "subtype": "case_2"},
    )
    assert joined["surface"] == "மரத்தை"

    candidates = tamil.punarchi_split_candidates("கல்லடி")
    assert any(
        (c["first"], c["second"], c["sutra"], c["split_byte"], c["split_unit"])
        == ("கல்", "அடி", 205, 9, 2)
        for c in candidates
    )

    assert len(tamil.punarchi_rules()) == 117

    with pytest.raises(ValueError, match="^unsupported punarchi profile$"):
        tamil.punarchi_rules(profile="tolkappiyam-v1")
