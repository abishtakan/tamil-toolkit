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
