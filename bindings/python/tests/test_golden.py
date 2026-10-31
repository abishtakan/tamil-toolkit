import pytest
import tamil_toolkit as tamil

from tools.harness import load_vectors


@pytest.mark.parametrize("case", load_vectors(), ids=lambda case: case["id"])
def test_golden(case):
    if "expected_error" in case:
        assert "expected" not in case
        with pytest.raises(ValueError) as failure:
            tamil.execute(case)
        assert str(failure.value) == case["expected_error"]
    else:
        assert "expected" in case
        assert tamil.execute(case) == case["expected"]


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
