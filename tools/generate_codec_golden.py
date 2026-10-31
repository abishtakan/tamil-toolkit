"""Compile offline codec fixtures from pinned source tables and encoder evidence.

No decoder or runtime mapping imports belong in this fixture compiler.
"""

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_core_golden import ROOT, row  # noqa: E402

REFERENCE = ROOT / "tests/reference/codec-v0.1"
OUTPUT = ROOT / "tests/golden/codec_bamini.jsonl"
SOURCE = "MIT upstream Bamini tables/encoder; docs/specs/codec-v0.1.md"


def references():
    metadata = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    for source in metadata["files"]:
        if hashlib.sha256((REFERENCE / source["file"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("codec reference digest mismatch: " + source["file"])
    return tuple(json.loads((REFERENCE / name).read_text(encoding="utf-8")) for name in
                 ("profile.json", "primary-table.json", "secondary-results.json"))


def mappings():
    profile, primary, _ = references()
    candidates = defaultdict(set)
    for unicode, legacy in list(primary["font-keymap"].items()) + list(primary["symbol"].items()):
        for key in legacy if isinstance(legacy, list) else [legacy]:
            candidates[key].add(unicode)
    for extension in profile["extensions"]:
        candidates[extension["legacy"]].add(extension["unicode"])
    unambiguous = {key: next(iter(values)) for key, values in sorted(candidates.items()) if len(values) == 1}
    ambiguous = {key: sorted(values) for key, values in sorted(candidates.items()) if len(values) > 1}
    return profile, unambiguous, ambiguous


def scalar_error(char, position=0, *, ambiguous=False):
    prefix = "ambiguous Bamini sequence" if ambiguous else "unsupported Bamini scalar"
    return f"{prefix} at byte {position}: U+{ord(char):04X}"


def generate():
    profile, table, ambiguous = mappings()
    _, _, evidence = references()
    cases = []

    def add(identifier, inputs, expected, *, error=False, tags=None, dialect="COMMON", region=None):
        cases.append(row("codec_" + identifier, "bamini_to_unicode", inputs, expected,
                         tags or ["bamini_v1"], SOURCE, error=error, dialect=dialect, region=region))

    for index, (legacy, unicode) in enumerate(table.items()):
        for dialect in ("TN", "SL"):
            for policy in ("default", "preserve"):
                inputs = {"text": legacy}
                if policy != "default":
                    inputs["errors"] = policy
                add(f"mapping_{index:03}_{dialect.lower()}_{policy}", inputs, unicode,
                    tags=["complete_mapping", "longest_match"], dialect=dialect)
    for index, entry in enumerate(evidence):
        if entry["kind"] != "word":
            continue
        assert "*" not in entry["encoded"], "reference word contains an ambiguous placeholder"
        for dialect in ("TN", "SL"):
            for policy in ("strict", "preserve"):
                add(f"{entry['id']}_{dialect.lower()}_{policy}", {"text": entry["encoded"], "errors": policy}, entry["text"],
                    tags=["independent_encoder", "word_or_vowel_matrix"], dialect=dialect)
    for code in range(128):
        char = chr(code)
        for dialect in ("TN", "SL"):
            for policy in ("strict", "preserve"):
                error = policy == "strict" and char not in table and char not in profile["passthrough"]
                expected = scalar_error(char, ambiguous=char in ambiguous) if error else table.get(char, char)
                add(f"ascii_{code:03}_{dialect.lower()}_{policy}", {"text": char, "errors": policy}, expected,
                    error=error, tags=["complete_ascii", "error_policy"], dialect=dialect)
    for entry in profile["regional_invariance"]:
        add("inventory_" + entry["region"].lower(), {"text": " ".join(table)}, " ".join(table.values()),
            dialect=entry["dialect"], region=entry["region"], tags=["complete_mapping", "regional_invariance"])
    for key in ambiguous:
        for dialect in ("TN", "SL"):
            add("ambiguous_" + dialect.lower(), {"text": "f" + key}, scalar_error(key, 1, ambiguous=True),
                error=True, dialect=dialect, tags=["ambiguous_placeholder"])
            add("ambiguous_preserve_" + dialect.lower(), {"text": "f" + key, "errors": "preserve"}, table["f"] + key,
                dialect=dialect, tags=["ambiguous_placeholder"])
    # Finite, reviewed concatenation cases; no decoder is implemented here.
    sequences = [["G+", "R+", "T+", "A+"], ["u;", "H", "h;"], ["f;", "\\p"],
                 ["nfs", "Nfh", "nfh", "nf", "Nf", "if"], ["/", ">", ","],
                 ["`{", "\\{", "&"]]
    for index, keys in enumerate(sequences):
        for dialect in ("TN", "SL"):
            add(f"sequence_{index}_{dialect.lower()}", {"text": "".join(keys)}, "".join(table[key] for key in keys),
                dialect=dialect, tags=["concatenation", "no_cascading_replacement"])
    safe = profile["passthrough"]
    controls = ["", safe, "\r\n\t 00123!?-.'\"()", "jkpo; " * 512]
    expected = ["", safe, controls[2], "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd " * 512]
    for index, (value, result) in enumerate(zip(controls, expected, strict=True)):
        for policy in ("strict", "preserve"):
            add(f"control_{index}_{policy}", {"text": value, "errors": policy}, result, tags=["boundary_or_bulk"])
    # Existing Unicode and invisible scalars are explicit unsupported/preserved cases.
    for index, suffix in enumerate([chr(0x1F642), chr(0x00E9), "e" + chr(0x0301), chr(0x0B95),
                                     chr(0x0BC6) + chr(0x0BBE), chr(0x200C), chr(0x200D), chr(0xFEFF)]):
        # Prefix output length differs from its original five-byte legacy spelling.
        value = "jkpo;" + suffix
        first = suffix[0]
        # ASCII 'e' is itself a mapped NA; the following accent is the first unsupported scalar.
        if first == "e":
            prefix, unknown, position = "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd" + table["e"], suffix[1:], 6
        else:
            prefix, unknown, position = "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd", suffix, 5
        add(f"unicode_{index}_strict", {"text": value}, scalar_error(unknown[0], position), error=True, tags=["original_byte_offset"])
        add(f"unicode_{index}_preserve", {"text": value, "errors": "preserve"}, unicodedata.normalize("NFC", prefix + unknown),
            tags=["unicode_preservation", "nfc_output"])
    joiners = [chr(0x200C), chr(0x200D)]
    for index, joiner in enumerate(joiners):
        add(f"joiner_boundary_{index}", {"text": "f" + joiner + "h", "errors": "preserve"}, table["f"] + joiner + "h",
            tags=["no_joiner_removal", "no_match_across_joiner"])
    add("cross_fragment_nfc", {"text": "f" + chr(0x0BC6) + chr(0x0BBE), "errors": "preserve"}, "\u0b95\u0bca",
        tags=["nfc_output"])
    failures = []
    for value in (None, True, 1, [], {}):
        failures.append(({"text": value}, "expected a string input"))
    for value in (None, True, 1, "text", [], {}):
        failures.append((value, "expected a string input"))
    for policy in (None, True, 1, [], {}, "", "ignore", "replace", "STRICT"):
        failures.append(({"text": "f", "errors": policy}, "unsupported codec error policy"))
    failures.append(({"text": None, "errors": "invalid"}, "expected a string input"))
    for index, (inputs, message) in enumerate(failures):
        for dialect in ("TN", "SL"):
            add(f"invalid_{index:02}_{dialect.lower()}", inputs, message, error=True, dialect=dialect, tags=["shared_error"])
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
            raise SystemExit("Codec corpus differs; review independent evidence before regeneration")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
