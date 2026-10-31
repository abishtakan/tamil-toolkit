import tomllib
import unicodedata

from tools.generate_codec_reverse_golden import (
    OUTPUT, ROOT, boundary_collisions, canonical_mappings, generate, render,
)
from tools.generate_codec_golden import mappings, references


def test_encoder_corpus_matches_independent_evidence():
    cases = generate()
    assert OUTPUT.read_text(encoding="utf-8") == render()
    assert len(cases) == 1838
    assert sum("expected_error" in case for case in cases) == 664
    _, canonical, _ = canonical_mappings()
    for dialect in ("TN", "SL"):
        entries = [case for case in cases if case["id"].startswith("encode_mapping_") and case["dialect"] == dialect]
        assert {case["input"]["text"] for case in entries if case["id"].endswith("_nfc")} == set(canonical)
        assert {case["input"]["text"] for case in entries if case["id"].endswith("_nfd")} == {
            unicodedata.normalize("NFD", text) for text in canonical if unicodedata.normalize("NFD", text) != text
        }
    assert {case["region"] for case in cases if "region" in case} == {
        "TN", "KONGU", "CHENNAI", "JAFFNA", "BATTICALOA", "VANNI", "UP_COUNTRY",
    }
    for case in cases:
        if "expected" in case:
            assert case["expected"].isascii() and "*" not in case["expected"]


def test_all_source_key_boundary_collisions_are_explicit():
    cases = generate()
    collisions = boundary_collisions()
    assert len(collisions) == 115
    assert len({left for left, _ in collisions}) == 23
    assert len({right for _, right in collisions}) == 5
    for dialect in ("TN", "SL"):
        assert len([case for case in cases if "all_boundary_collisions" in case["tags"] and case["dialect"] == dialect]) == 115
        assert len([case for case in cases if "safe_boundary" in case["tags"] and case["dialect"] == dialect]) == 115
    assert ("\u0b95\u0bc6", "\u0bb3") in collisions
    assert ("\u0b92", "\u0bb3\u0bbe") in collisions


def test_runtime_alias_preference_matches_independent_primary_source():
    _, canonical, _ = canonical_mappings()
    _, primary, _ = references()
    _, forward, _ = mappings()
    runtime = tomllib.loads((ROOT / "lexicon/bamini.toml").read_text(encoding="utf-8"))
    assert runtime["encoding_preferences"] == [{"unicode": "\u0bb0\u0bcd", "legacy": "u;"}]
    assert primary["font-keymap"]["\u0bb0\u0bcd"][0] == "u;"
    assert len(canonical) == 296
    assert all(forward[legacy] == text for text, legacy in canonical.items())
    assert canonical["\u0bb0\u0bcd"] == "u;"
    assert canonical["\u0bb8\u0bcd\u0bb0\u0bc0"] == "="
