import pytest
import tamil_toolkit as tamil

from tools.harness import load_vectors, selected_planned_suites


def test_golden():
    cases = load_vectors(include_planned=selected_planned_suites())
    assert cases
    for case in cases:
        if "expected_error" in case:
            assert "expected" not in case, case["id"]
            with pytest.raises(ValueError) as failure:
                tamil.execute(case)
            assert str(failure.value) == case["expected_error"], case["id"]
        else:
            assert "expected" in case, case["id"]
            assert tamil.execute(case) == case["expected"], case["id"]


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
    cases = {case["id"]: case for case in load_vectors()}
    word_case = cases["collate_words_basic"]
    key_case = cases["collate_key_001"]
    assert tamil.sort_words(word_case["input"]) == word_case["expected"]
    assert tamil.sort_key(key_case["input"]) == key_case["expected"]
    assert tamil.search_key(key_case["input"]) == key_case["expected"]
    assert tamil.compare(key_case["input"], key_case["input"]) == 0


def test_numeral_convenience_apis():
    cases = {case["id"]: case for case in load_vectors()}
    assert tamil.to_words(1025, "SL") == cases["num_014"]["expected"]
    assert tamil.to_words(100000) == cases["number_default_locale"]["expected"]
    for case in cases.values():
        if case["op"] in ("format_currency", "currency_to_words") and "expected" in case:
            assert getattr(tamil, case["op"])(**case["input"]) == case["expected"]
    with pytest.raises(ValueError, match="unsupported currency"):
        tamil.format_currency(1, "USD")


def test_codec_convenience_api():
    cases = {case["id"]: case for case in load_vectors()}
    word = cases["codec_word_000_tn_strict"]
    preserved = cases["codec_joiner_boundary_0"]
    assert tamil.bamini_to_unicode(word["input"]["text"]) == word["expected"]
    assert tamil.bamini_to_unicode(**preserved["input"]) == preserved["expected"]
    with pytest.raises(ValueError, match="ambiguous Bamini sequence"):
        tamil.bamini_to_unicode("*")
    with pytest.raises(ValueError, match="unsupported codec error policy"):
        tamil.bamini_to_unicode("f", "ignore")


def test_encoder_convenience_api():
    cases = {case["id"]: case for case in load_vectors()}
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
    for case in load_vectors():
        if case["op"] in ("format_fraction", "fraction_to_words", "fraction_symbol", "format_date") and "expected" in case:
            assert getattr(tamil, case["op"])(**case["input"]) == case["expected"]
    with pytest.raises(ValueError, match="fraction denominator must not be zero"):
        tamil.format_fraction(1, 0)
    with pytest.raises(ValueError, match="invalid Gregorian date"):
        tamil.format_date(2023, 2, 29)


def test_numerals_v03_typed_convenience_apis():
    cases = load_vectors(include_planned=selected_planned_suites())
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

