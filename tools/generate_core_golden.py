"""Compile independent Unicode references into offline core acceptance fixtures.

This fixture compiler never imports the runtime tables, engine, or bindings.
"""

import argparse
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/reference/unicode-17.0.0"
PROFILE = ROOT / "tests/reference/core-profile.json"
GOLDEN = ROOT / "tests/golden"
UCD_SOURCE = "https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt"
NAMED_SOURCE = "https://www.unicode.org/Public/17.0.0/ucd/NamedSequences.txt"
BOUNDARY_SOURCE = "https://www.unicode.org/Public/17.0.0/ucd/auxiliary/GraphemeBreakTest.txt"
CONTRACT_SOURCE = "docs/specs/core-v0.1.md (explicit API contract)"


def text(hex_values):
    return "".join(chr(int(value, 16)) for value in hex_values)


def references():
    sources = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    assert sources["unicode_version"] == "17.0.0"
    for source in sources["files"]:
        actual = hashlib.sha256((REFERENCE / source["file"]).read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError(f"reference checksum mismatch: {source['file']}")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    ucd = {}
    for line in (REFERENCE / "UnicodeData-Tamil.txt").read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        ucd[fields[1]] = (chr(int(fields[0], 16)), fields[5])
    named = {}
    for line in (REFERENCE / "NamedSequences.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("TAMIL"):
            name, codes = line.split(";")
            named[name] = text(codes.split())
    return profile, ucd, named


def exceptions(value, path=""):
    entries = []
    if isinstance(value, str):
        if not unicodedata.is_normalized("NFC", value):
            entries.append({"path": path, "kind": "non_nfc", "reason": "Intentional canonical decomposition from independent Unicode reference data."})
        if any(chr(code) in value for code in (0x200C, 0x200D)):
            entries.append({"path": path, "kind": "joiner", "reason": "Intentional joiner tests exact preservation and documented cluster boundaries."})
    elif isinstance(value, list):
        for index, item in enumerate(value):
            entries.extend(exceptions(item, f"{path}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            token = key.replace("~", "~0").replace("/", "~1")
            entries.extend(exceptions(item, f"{path}/{token}"))
    return entries


def row(identifier, operation, value, expected, tags, source, *, error=False, dialect="COMMON", region=None):
    outcome = "expected_error" if error else "expected"
    case = {"id": identifier, "op": operation, "input": value, outcome: expected,
            "dialect": dialect, "tags": tags, "source": source}
    if region:
        case["region"] = region
    allowed = exceptions(value, "/input") + exceptions(expected, f"/{outcome}")
    if allowed:
        case["unicode_exceptions"] = allowed
    return case


def inspection(letter, classification):
    return {"nfc": letter, "nfd": unicodedata.normalize("NFD", letter),
            "is_nfc": True, "is_nfd": unicodedata.is_normalized("NFD", letter),
            "ezhuthu_count": 1, "grapheme_count": 1,
            "letters": [{"text": letter, "classification": classification}]}


def inventory(profile, ucd, named):
    classes = {name: group for group, names in profile["native_groups"].items() for name in names}
    classes.update({name: "grantha" for name in profile["grantha_names"]})
    vowels = {name: ucd["TAMIL LETTER " + name][0] for name in profile["uyir_names"]}
    meis = {name.removeprefix("TAMIL CONSONANT "): value for name, value in named.items() if name.startswith("TAMIL CONSONANT ")}
    assert len(vowels) == 12 and len(meis) == 24 and len(classes) == 24
    forms = []
    for consonant, mei in meis.items():
        for vowel, uyir in vowels.items():
            # NamedSequences supplies each expected spelling directly. Only inherent
            # A uses the Unicode character name (or the explicitly named KSHA form).
            if vowel == "A" and consonant != "KSS":
                spelling = ucd["TAMIL LETTER " + consonant + "A"][0]
            else:
                spelling = named["TAMIL SYLLABLE " + consonant + vowel]
            forms.append((consonant, vowel, mei, uyir, spelling, classes[consonant]))
    return classes, vowels, meis, forms


def generate():
    profile, ucd, named = references()
    classes, vowels, meis, forms = inventory(profile, ucd, named)
    alphabet, normalization, boundaries, errors = [], [], [], []
    letters = [(f"uyir_{name.lower()}", value, "uyir") for name, value in vowels.items()]
    letters += [(f"mei_{name.lower()}", value, classes[name]) for name, value in meis.items()]
    letters += [(f"uyirmei_{c.lower()}_{v.lower()}", spelling, group) for c, v, _, _, spelling, group in forms]
    letters += [("aytham", ucd["TAMIL SIGN VISARGA"][0], "aytham"),
                ("shri_modern", named[profile["modern_shri_name"]], "grantha"),
                ("shri_legacy", text(profile["legacy_shri"]), "grantha")]
    assert len(letters) == 327
    source = NAMED_SOURCE + "; " + UCD_SOURCE + "; " + profile["classification_source"]
    for identifier, spelling, group in letters:
        tags = ["complete_inventory", group]
        alphabet.append(row("alphabet_segment_" + identifier, "get_letters", spelling, [spelling], tags, source))
        alphabet.append(row("alphabet_inspect_" + identifier, "inspect_tamil_string", spelling, inspection(spelling, group), tags, source))
    for consonant, vowel, mei, uyir, spelling, group in forms:
        identifier = consonant.lower() + "_" + vowel.lower()
        alphabet.append(row("alphabet_split_" + identifier, "split_uyirmei", spelling, {"mei": mei, "uyir": uyir}, ["complete_matrix", group], source))
        alphabet.append(row("alphabet_compose_" + identifier, "compose_uyirmei", {"mei": mei, "uyir": uyir}, spelling, ["complete_matrix", group], source))
    for regional in profile["regional_invariance"]:
        spelling = "".join(value for _, value, _ in letters)
        alphabet.append(row("alphabet_region_" + regional["region"].lower(), "get_letters", spelling,
                            [value for _, value, _ in letters], ["regional_invariance", "complete_inventory"], source, **regional))
    # Every Tamil canonical decomposition, with each dependent sign on every base.
    normalization_forms = [("uyir_au", vowels["AU"], None)]
    normalization_forms += [(c.lower() + "_" + v.lower(), spelling, {"mei": mei, "uyir": uyir})
                            for c, v, mei, uyir, spelling, _ in forms if v in {"O", "OO", "AU"}]
    assert len(normalization_forms) == 73
    for identifier, spelling, parts in normalization_forms:
        nfd = unicodedata.normalize("NFD", spelling)
        assert nfd != spelling
        for op, value, expected in [("normalize_nfc", nfd, spelling), ("normalize_nfd", spelling, nfd),
                                    ("get_letters", nfd, [spelling])]:
            normalization.append(row("canonical_" + identifier + "_" + op, op, value, expected, ["canonical_decomposition"], UCD_SOURCE))
        if parts:
            normalization.append(row("canonical_" + identifier + "_split", "split_uyirmei", nfd, parts, ["canonical_decomposition"], UCD_SOURCE))
    for line_number, line in enumerate((REFERENCE / "GraphemeBreakTest.txt").read_text(encoding="utf-8").splitlines(), 1):
        sequence = line.split("#")[0].split()
        if not sequence:
            continue
        clusters, cluster = [], ""
        for token in sequence:
            if token == chr(0x00F7):
                if cluster:
                    clusters.append(cluster)
                    cluster = ""
            elif token != chr(0x00D7):
                cluster += chr(int(token, 16))
        assert not cluster
        value = "".join(clusters)
        boundaries.append(row(f"uax29_line_{line_number:04}", "get_letters", value,
                              [unicodedata.normalize("NFC", item) for item in clusters], ["uax29_17"], BOUNDARY_SOURCE + f" line {line_number}"))
    assert len(boundaries) == 766
    # Scalar-written project boundary decisions, independent of runtime output.
    ka, pulli, aa, i = (chr(code) for code in (0x0B95, 0x0BCD, 0x0BBE, 0x0BBF))
    sha, sa, ra, ii, ssa = (chr(code) for code in (0x0BB6, 0x0BB8, 0x0BB0, 0x0BC0, 0x0BB7))
    manual = [("empty", [], []), ("crlf", ["\r", "\n"], ["\r\n"]),
              ("isolated_vowel", [aa], [aa]), ("repeated_vowel", [ka, aa, aa], [ka + aa + aa]),
              ("repeated_pulli", [ka, pulli, pulli], [ka + pulli + pulli]),
              ("incompatible_mark", [ka, chr(0x0301)], [ka + chr(0x0301)]),
              ("adjacent_mei_uyir", [ka, pulli, vowels["A"]], [ka + pulli, vowels["A"]]),
              ("mixed_script", ["A", ka, i, " ", chr(0x1F4BB)], ["A", ka + i, " ", chr(0x1F4BB)]),
              ("tamil_digit", [chr(0x0BE7)], [chr(0x0BE7)]),
              ("tamil_supplement", [chr(0x11FC0)], [chr(0x11FC0)])]
    for code in (0x200C, 0x200D):
        joiner = chr(code)
        for prefix, base, tail in [("ksha", ka, ssa + i), ("shri_modern", sha, ra + ii), ("shri_legacy", sa, ra + ii)]:
            manual.append((f"interrupted_{prefix}_{code:x}", [base, pulli, joiner, tail], [base + pulli + joiner, tail]))
        manual.append((f"joiner_after_letter_{code:x}", [ka, joiner], [ka + joiner]))
        manual.append((f"isolated_joiner_{code:x}", [joiner], [joiner]))
    for identifier, pieces, expected in manual:
        value = "".join(pieces)
        boundaries.append(row("boundary_" + identifier, "get_letters", value, expected, ["project_boundary"], CONTRACT_SOURCE))
        # All manual examples other than the mixed valid-letter controls are invalid
        # or non-Tamil clusters; assert that inspection never counts them as letters.
        if identifier.startswith(("isolated_", "repeated_", "incompatible_", "joiner_after_", "tamil_")):
            result = {"nfc": value, "nfd": unicodedata.normalize("NFD", value), "is_nfc": True,
                      "is_nfd": unicodedata.is_normalized("NFD", value), "ezhuthu_count": 0,
                      "grapheme_count": len(expected), "letters": [{"text": item, "classification": "other"} for item in expected]}
            boundaries.append(row("boundary_inspect_" + identifier, "inspect_tamil_string", value, result, ["invalid_orthography"], CONTRACT_SOURCE))
    split_bad = ["", ka + pulli, vowels["A"], aa, ka + ka, ka + aa + aa, ka + pulli + pulli,
                 ka + chr(0x200C), ka + chr(0x200D), named[profile["modern_shri_name"]], text(profile["legacy_shri"])]
    negative = [("split_uyirmei", value, "expected exactly one Uyirmei letter") for value in split_bad]
    negative += [("compose_uyirmei", pair, "expected a valid Mei consonant") for pair in [
        {"mei": "", "uyir": vowels["A"]}, {"mei": ka, "uyir": vowels["A"]},
        {"mei": ka + pulli + ka + pulli, "uyir": vowels["A"]},
        {"mei": ka + pulli + chr(0x200C), "uyir": vowels["A"]}]]
    negative += [("compose_uyirmei", {"mei": ka + pulli, "uyir": value}, "expected an independent Uyir vowel")
                 for value in ["", aa, vowels["A"] + vowels["I"], vowels["A"] + chr(0x200D)]]
    negative += [("compose_uyirmei", pair, "expected a string input") for pair in [
        {}, {"mei": ka + pulli}, {"uyir": vowels["A"]}, {"mei": 1, "uyir": vowels["A"]}]]
    for op in ["get_letters", "normalize_nfc", "normalize_nfd", "split_uyirmei", "inspect_tamil_string", "compose_uyirmei"]:
        negative += [(op, value, "expected a string input") for value in [None, 1, [], {}]] if op != "compose_uyirmei" else [
            (op, value, "expected a string input") for value in [None, 1, [], "bad"]]
    negative.append(("unknown_core_operation", "", "unsupported operation: unknown_core_operation"))
    for index, (op, value, message) in enumerate(negative, 1):
        for dialect in ("TN", "SL"):
            errors.append(row(f"error_{index:03}_{dialect.lower()}", op, value, message, ["invalid_input", "shared_error"], CONTRACT_SOURCE, error=True, dialect=dialect))
    return {"core_alphabet.jsonl": alphabet, "core_normalization.jsonl": normalization,
            "core_boundaries.jsonl": boundaries, "core_errors.jsonl": errors}


def render():
    return {name: "".join(json.dumps(case, ensure_ascii=True, separators=(",", ":")) + "\n" for case in cases)
            for name, cases in generate().items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare checked-in fixtures without writing")
    args = parser.parse_args()
    for name, content in render().items():
        path = GOLDEN / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Generated corpus differs: {name}; review references and regenerate")
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
        print(f"{name}: {len(content.splitlines())} vectors")


if __name__ == "__main__":
    main()
