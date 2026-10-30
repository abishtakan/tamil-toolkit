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
