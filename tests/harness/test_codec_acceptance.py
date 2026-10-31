import json
import tomllib

from tools.generate_codec_golden import OUTPUT, REFERENCE, ROOT, generate, mappings, references, render
from tools.generate_core_golden import inventory, references as core_references


def test_codec_corpus_matches_independent_evidence():
    cases = generate()
    assert OUTPUT.read_text(encoding="utf-8") == render()
    assert len(cases) == 1920
    assert sum("expected_error" in case for case in cases) == 144
    for dialect in ("TN", "SL"):
        mapping = [case for case in cases if "complete_mapping" in case["tags"] and case["id"].startswith("codec_mapping_") and case["dialect"] == dialect]
        assert len(mapping) == 596  # Each supported key with default and preserve policies.
        ascii_cases = [case for case in cases if "complete_ascii" in case["tags"] and case["dialect"] == dialect]
        assert {ord(case["input"]["text"]) for case in ascii_cases} == set(range(128))
    assert {case["region"] for case in cases if "region" in case} == {
        "TN", "KONGU", "CHENNAI", "JAFFNA", "BATTICALOA", "VANNI", "UP_COUNTRY",
    }


def test_runtime_codec_data_agrees_with_pinned_source_tables():
    profile, table, ambiguous = mappings()
    runtime = tomllib.loads((ROOT / "lexicon/bamini.toml").read_text(encoding="utf-8"))
    for key in ("profile", "max_key_bytes", "passthrough"):
        assert runtime[key] == profile[key]
    assert {entry["legacy"]: entry["unicode"] for entry in runtime["mappings"]} == table
    assert {entry["legacy"]: entry["candidates"] for entry in runtime["ambiguous"]} == ambiguous
    assert len(table) == 298 and len(set(table.values())) == 296
    assert table["/"] == chr(0x0B83)
    assert table[">"] == "," and table[","] == chr(0x0B87)
    assert table["nfs"] == "\u0b95\u0bcc"
    assert table["nf"] + table["s"] != table["nfs"]


def test_source_ambiguity_explains_exact_traditional_inventory_gap():
    _, table, ambiguous = mappings()
    core_profile, ucd, named = core_references()
    classes, vowels, meis, forms = inventory(core_profile, ucd, named)
    traditional = set(vowels.values()) | {chr(0x0B83)}
    traditional.update(mei for name, mei in meis.items() if classes[name] != "grantha")
    traditional.update(spelling for consonant, _, _, _, spelling, _ in forms if classes[consonant] != "grantha")
    assert len(traditional) == 247
    assert set(ambiguous) == {"*"}
    assert len(ambiguous["*"]) == 5
    assert traditional - set(table.values()) == set(ambiguous["*"])


def test_independent_encoder_disagreements_are_explicit_and_licensed():
    _, primary, evidence = references()
    secondary = {entry["text"]: entry["encoded"] for entry in evidence if entry["kind"] == "mapping"}
    assert len(evidence) == 332
    differences = {text for text, legacy in primary["font-keymap"].items()
                   if secondary[text] not in (legacy if isinstance(legacy, list) else [legacy])}
    assert differences == {"\u0bb9\u0bc1", "\u0bb7\u0bc1", "\u0bb0\u0bc2"}
    metadata = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    upstream = [entry for entry in metadata["files"] if "url" in entry]
    assert len(upstream) == 4 and all(entry["license"] == "MIT" for entry in upstream)
    assert all("Permission is hereby granted" in (REFERENCE / name).read_text(encoding="utf-8")
               for name in ("LICENSE-ag.txt", "LICENSE-pakeetharan.txt"))
