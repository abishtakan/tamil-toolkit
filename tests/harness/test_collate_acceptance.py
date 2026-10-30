import tomllib
from pathlib import Path

from tools.generate_collate_golden import OUTPUT, REFERENCE, generate, inventory, render


def test_collation_corpus_matches_independent_profile():
    cases = generate()
    assert len(cases) == 3091
    assert OUTPUT.read_text(encoding="utf-8") == render()
    assert len([case for case in cases if case["id"].startswith("collate_key_")]) == 325
    assert len([case for case in cases if case["id"].startswith("collate_adjacent_")]) == 1296
    assert len([case for case in cases if case["id"].startswith("collate_family_")]) == 24
    assert len([case for case in cases if case["id"].startswith("collate_canonical_stable_")]) == 73
    assert len([case for case in cases if "expected_error" in case]) == 50


def test_runtime_order_agrees_with_independent_reference():
    profile, _, labels, letters = inventory()
    runtime = tomllib.loads((Path(__file__).resolve().parents[2] / "lexicon/collate.toml").read_text(encoding="utf-8"))
    assert runtime["profile"] == profile["profile"]
    assert runtime["key_version"] == profile["key_version"]
    assert runtime["order"] == letters
    for actual, expected in zip(runtime["expansions"], profile["shri_expansions"], strict=True):
        assert actual["text"] == "".join(chr(int(code, 16)) for code in expected["codes"])
        assert actual["elements"] == [letters[labels.index(label)] for label in expected["elements"]]


def test_cldr_evidence_explicitly_places_mei_before_each_base():
    _, _, labels, letters = inventory()
    rules = (REFERENCE / "ta.xml").read_text(encoding="utf-8")
    for label, mei in zip(labels, letters):
        if label.startswith("TAMIL CONSONANT "):
            assert "&[before 1]" + mei[:-1] + "<" + mei in rules
