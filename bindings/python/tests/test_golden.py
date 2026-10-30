import pytest
import tamil_toolkit as tamil

from tools.harness import load_vectors


@pytest.mark.parametrize("case", load_vectors(), ids=lambda case: case["id"])
def test_golden(case):
    assert tamil.execute(case) == case["expected"]


@pytest.mark.parametrize("payload", [
    {"op": "unknown", "input": ""},
    {"op": "get_letters", "input": 1},
    {"op": "split_uyirmei", "input": "\u0b95\u0bcd"},
])
def test_errors_cross_ffi(payload):
    with pytest.raises(ValueError):
        tamil.execute(payload)
