"""Compile the independent agara-v1 profile; never read runtime ordering tables."""

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, references, row, text  # noqa: E402

REFERENCE = ROOT / "tests/reference/collate-v0.1"
OUTPUT = ROOT / "tests/golden/collate_agara_varisai.jsonl"
SOURCE = "docs/specs/collate-v0.1.md; Unicode 17 traditional Tamil table; CLDR 48 ta.xml"


def inventory():
    metadata = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    if hashlib.sha256((REFERENCE / metadata["file"]).read_bytes()).hexdigest() != metadata["sha256"]:
        raise ValueError("CLDR reference checksum mismatch")
    profile = json.loads((REFERENCE / "profile.json").read_text(encoding="utf-8"))
    core_profile, ucd, named = references()
    labels, letters = [], []
    for vowel in profile["vowels"]:
        labels.append("TAMIL LETTER " + vowel)
        letters.append(ucd[labels[-1]][0])
    labels.append("TAMIL SIGN VISARGA")
    letters.append(ucd[labels[-1]][0])
    for consonant in profile["consonants"]:
        labels.append("TAMIL CONSONANT " + consonant)
        letters.append(named[labels[-1]])
        for vowel in profile["vowels"]:
            label = "TAMIL SYLLABLE " + consonant + vowel
            labels.append(label)
            letters.append(ucd["TAMIL LETTER " + consonant + "A"][0] if vowel == "A" and consonant != "KSS" else named[label])
    assert len(set(letters)) == 325
    return profile, core_profile, labels, letters


def generate():
    profile, core_profile, labels, letters = inventory()
    ranks = {letter: index for index, letter in enumerate(letters, 1)}
    label_to_letter = dict(zip(labels, letters))
    cases = []

    def add(identifier, op, value, expected, *, tags=None, dialect="COMMON", region=None, error=False):
        cases.append(row("collate_" + identifier, op, value, expected, tags or ["agara_v1"], SOURCE,
                         dialect=dialect, region=region, error=error))

    def key_for_elements(elements):
        return [profile["key_version"]] + [part for element in elements for part in (0, ranks[element])]

    for index, letter in enumerate(letters, 1):
        for op, prefix in [("sort_key", "key"), ("search_key", "search")]:
            add(f"{prefix}_{index:03}", op, letter, key_for_elements([letter]), tags=["complete_inventory", "exact_key"])
        add(f"prefix_{index:03}", "compare", {"left": letter, "right": letter + letters[0]}, -1, tags=["prefix_order"])
        add(f"prefix_reverse_{index:03}", "compare", {"left": letter + letters[0], "right": letter}, 1, tags=["prefix_order"])
    for index, (left, right) in enumerate(zip(letters, letters[1:]), 1):
        for dialect in ("TN", "SL"):
            add(f"adjacent_{index:03}_{dialect.lower()}", "compare", {"left": left, "right": right}, -1,
                dialect=dialect, tags=["complete_order"])
            add(f"adjacent_reverse_{index:03}_{dialect.lower()}", "compare", {"left": right, "right": left}, 1,
                dialect=dialect, tags=["complete_order"])
    for regional in core_profile["regional_invariance"]:
        add("inventory_" + regional["region"].lower(), "sort_words", list(reversed(letters)), letters,
            dialect=regional["dialect"], region=regional["region"], tags=["complete_inventory", "regional_invariance"])
    for index, consonant in enumerate(profile["consonants"]):
        family = letters[13 + index * 13:26 + index * 13]
        shuffled = family[::2] + family[1::2]
        add("family_" + consonant.lower(), "sort_words", shuffled, family, tags=["vowel_family"])
    for index, letter in enumerate(letters, 1):
        nfd = unicodedata.normalize("NFD", letter)
        if nfd == letter:
            continue
        add(f"canonical_compare_{index:03}", "compare", {"left": letter, "right": nfd}, 0, tags=["canonical_equivalence"])
        add(f"canonical_reverse_{index:03}", "compare", {"left": nfd, "right": letter}, 0, tags=["canonical_equivalence"])
        add(f"canonical_stable_{index:03}", "sort_words", [nfd, letter, nfd], [nfd, letter, nfd], tags=["stable_sort"])
        for op in ("sort_key", "search_key"):
            add(f"canonical_{op}_{index:03}", op, nfd, key_for_elements([letter]), tags=["canonical_equivalence"])
    shri = []
    for index, expansion in enumerate(profile["shri_expansions"]):
        spelling = text(expansion["codes"])
        elements = [label_to_letter[label] for label in expansion["elements"]]
        shri.append(spelling)
        for op in ("sort_key", "search_key"):
            add(f"shri_{index}_{op}", op, spelling, key_for_elements(elements), tags=["grantha", "written_expansion"])
        add(f"shri_{index}_prefix", "compare", {"left": elements[0], "right": spelling}, -1)
        following = letters[ranks[elements[0]]]
        add(f"shri_{index}_row", "compare", {"left": spelling, "right": following}, -1)
    add("shri_distinct", "compare", {"left": shri[0], "right": shri[1]}, -1, tags=["grantha", "preserve_spelling"])
    words = [text(codes.split()) for codes in [
        "0B95 0BB2 0BCD 0BB5 0BBF", "0B95 0BB2 0BC8", "0B95 0BB2 0BC8 0B95 0BB3 0BCD",
    ]]
    add("words_basic", "sort_words", list(reversed(words)), words, tags=["dictionary_words", "prefix_order"], dialect="TN")
    add("words_basic_sl", "sort_words", list(reversed(words)), words, tags=["dictionary_words", "prefix_order"], dialect="SL", region="JAFFNA")
    add("duplicates", "sort_words", [letters[14], letters[0], letters[14], letters[0]],
        [letters[0], letters[0], letters[14], letters[14]], tags=["stable_sort", "duplicates"])
    add("empty_sort", "sort_words", [], [], tags=["empty"])
    add("empty_compare", "compare", {"left": "", "right": ""}, 0, tags=["empty"])
    add("empty_prefix", "compare", {"left": "", "right": letters[0]}, -1, tags=["empty"])
    for op in ("sort_key", "search_key"):
        add("empty_" + op, op, "", [1], tags=["empty"])
    malformed = [text(codes.split()) for codes in ["0B95 0BBE 0BBE", "0B95 0BCD 200C", "0B95 0BCD 200D", "0BBE", "200C", "200D"]]
    fallback = [" ", "!", "0", "A", "a", chr(0x00E9), chr(0x0BE7), chr(0xE000), chr(0x1F4BB)] + malformed
    for index, value in enumerate(fallback):
        normalized = unicodedata.normalize("NFC", value)
        key = [1] + [part for char in normalized for part in (1, ord(char))]
        for op in ("sort_key", "search_key"):
            add(f"fallback_{index}_{op}", op, value, key, tags=["fallback", "preserve_scalars"])
    # Only fallback samples use scalar sorting in this compiler, as specified;
    # no general-purpose Tamil collation implementation is duplicated here.
    fallback_order = sorted(fallback, key=lambda value: tuple(map(ord, unicodedata.normalize("NFC", value))))
    known = [letters[0], letters[13], letters[14]]
    add("mixed", "sort_words", list(reversed(fallback_order + known)), known + fallback_order, tags=["mixed_script", "fallback"])
    add("scalar_not_utf16", "compare", {"left": chr(0xE000), "right": chr(0x1F4BB)}, -1, tags=["fallback", "scalar_order"])
    negative = []
    for op in ("sort_key", "search_key"):
        negative += [(op, value, "expected a string input") for value in [None, 1, [], {}]]
    negative += [("compare", value, "expected a string input") for value in [
        None, 1, [], {}, {"left": ""}, {"right": ""}, {"left": 1, "right": ""}, {"left": "", "right": []}]]
    negative += [("sort_words", value, "expected an array of strings") for value in [None, 1, {}, "text"]]
    negative += [("sort_words", value, "expected a string input") for value in [[None], [1], [[]], [{}], [letters[0], False]]]
    for index, (op, value, error) in enumerate(negative):
        for dialect in ("TN", "SL"):
            add(f"error_{index}_{dialect.lower()}", op, value, error, dialect=dialect, error=True, tags=["shared_error"])
    return cases


def render():
    return "".join(json.dumps(case, ensure_ascii=True, separators=(",", ":")) + "\n" for case in generate())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Collation corpus differs; review references and regenerate")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
