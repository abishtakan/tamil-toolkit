"""Independent encoder fixtures from frozen tables, source output, and key prefixes.

This compiler neither calls the Rust encoder/decoder nor implements a decoder.
"""

import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.generate_codec_golden import ROOT, mappings, references  # noqa: E402
from tools.generate_core_golden import row  # noqa: E402

OUTPUT = ROOT / "tests/golden/codec_unicode_to_bamini.jsonl"
SOURCE = "Pinned Bamini primary/secondary sources; docs/specs/codec-reverse-v0.1.md"
COLLISION_ERROR = "Bamini encoding is not reversible for this input"


def canonical_mappings():
    profile, primary, evidence = references()
    _, decoded, _ = mappings()
    canonical = {}
    for text, spelling in list(primary["font-keymap"].items()) + list(primary["symbol"].items()):
        preferred = spelling[0] if isinstance(spelling, list) else spelling
        if decoded.get(preferred) == text:
            canonical[text] = preferred
    for entry in profile["extensions"]:
        canonical[entry["unicode"]] = entry["legacy"]
    return profile, dict(sorted(canonical.items())), evidence


def boundary_collisions():
    _, canonical, _ = canonical_mappings()
    _, decoded, _ = mappings()
    pairs = set()
    # Structural prefix relations only: the next canonical key completes a longer
    # decoder key across the boundary. This is not a conversion implementation.
    for left, first_key in canonical.items():
        for longer in decoded:
            if len(longer) <= len(first_key) or not longer.startswith(first_key):
                continue
            suffix = longer[len(first_key):]
            for right, next_key in canonical.items():
                if next_key.startswith(suffix):
                    pairs.add((left, right))
    return sorted(pairs)


def scalar_error(char, position=0):
    return f"unsupported Unicode scalar for Bamini at NFC byte {position}: U+{ord(char):04X}"


def generate():
    profile, canonical, evidence = canonical_mappings()
    _, _, ambiguous = mappings()
    cases = []

    def add(identifier, inputs, expected, *, error=False, tags=None, dialect="COMMON", region=None):
        cases.append(row("encode_" + identifier, "unicode_to_bamini", inputs, expected,
                         tags or ["canonical_bamini"], SOURCE, error=error, dialect=dialect, region=region))

    for index, (text, encoded) in enumerate(canonical.items()):
        variants = [("nfc", text)]
        nfd = unicodedata.normalize("NFD", text)
        if nfd != text:
            variants.append(("nfd", nfd))
        for dialect in ("TN", "SL"):
            for name, value in variants:
                add(f"mapping_{index:03}_{dialect.lower()}_{name}", {"text": value}, encoded,
                    dialect=dialect, tags=["complete_canonical_mapping", "canonical_equivalence"])
    for entry in evidence:
        if entry["kind"] == "word":
            for dialect in ("TN", "SL"):
                add(f"{entry['id']}_{dialect.lower()}", {"text": entry["text"]}, entry["encoded"],
                    dialect=dialect, tags=["independent_encoder"])
    for index, (left, right) in enumerate(boundary_collisions()):
        for dialect in ("TN", "SL"):
            add(f"collision_{index:03}_{dialect.lower()}", {"text": left + right}, COLLISION_ERROR,
                error=True, dialect=dialect, tags=["all_boundary_collisions"])
            add(f"separated_{index:03}_{dialect.lower()}", {"text": left + " " + right}, canonical[left] + " " + canonical[right],
                dialect=dialect, tags=["safe_boundary"])
    for prefix, codes in [("ascii", range(128)), ("tamil", range(0x0B80, 0x0C00))]:
        for code in codes:
            char = chr(code)
            expected = canonical.get(char, char if char in profile["passthrough"] else None)
            for dialect in ("TN", "SL"):
                add(f"{prefix}_{code:04x}_{dialect.lower()}", {"text": char}, expected if expected is not None else scalar_error(char),
                    error=expected is None, dialect=dialect, tags=["complete_scalar_block"])
    for index, text in enumerate(ambiguous["*"]):
        for dialect in ("TN", "SL"):
            add(f"unsupported_form_{index}_{dialect.lower()}", {"text": text}, scalar_error(text[1], 3),
                error=True, dialect=dialect, tags=["no_ambiguous_placeholder"])
    for entry in profile["regional_invariance"]:
        add("inventory_" + entry["region"].lower(), {"text": " ".join(canonical)}, " ".join(canonical.values()),
            dialect=entry["dialect"], region=entry["region"], tags=["regional_invariance", "complete_canonical_mapping"])
    mei = chr(0x0B95) + chr(0x0BCD)
    ssa = chr(0x0BB7)
    for index, suffix in enumerate([chr(0x0BCD), "", *(chr(code) for code in (0x0BBE, 0x0BBF, 0x0BC0, 0x0BC1, 0x0BC2, 0x0BC6, 0x0BC7, 0x0BC8, 0x0BCA, 0x0BCB, 0x0BCC))]):
        for dialect in ("TN", "SL"):
            add(f"ksha_{index:02}_{dialect.lower()}", {"text": mei + ssa + suffix}, canonical[mei] + canonical[ssa + suffix],
                dialect=dialect, tags=["compositional_ksha"])
    for index, code in enumerate((0x200C, 0x200D, 0x1F642, 0x0BB6, 0xFEFF)):
        # NFC reduces the prefix from 9 UTF-8 bytes to 6 before reporting offsets.
        prefix = chr(0x0B95) + chr(0x0BC6) + chr(0x0BBE)
        add(f"offset_{index}", {"text": prefix + chr(code)}, scalar_error(chr(code), 6), error=True,
            tags=["nfc_byte_offset", "no_silent_removal"])
    add("modern_shri", {"text": "\u0bb6\u0bcd\u0bb0\u0bc0"}, scalar_error(chr(0x0BB6)), error=True,
        tags=["no_spelling_fold"])
    add("latin_nfd", {"text": "e" + chr(0x0301)}, scalar_error(chr(0x00E9)), error=True,
        tags=["nfc_before_error"])
    for index, text in enumerate(["", profile["passthrough"], "\r\n00123!?", "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd " * 512]):
        expected = "jkpo; " * 512 if index == 3 else text
        add(f"control_{index}", {"text": text}, expected, tags=["empty_passthrough_or_bulk"])
    # Known alias sequences canonicalize to the primary source's first alias.
    add("ra_alias_preference", {"text": "\u0bb0\u0bcd\u0bb0\u0bcd\u0bb0\u0bcd"}, "u;u;u;", tags=["canonical_alias"])
    # If unsupported input and a prior collision coexist, scalar validation wins.
    left, right = boundary_collisions()[0]
    value = left + right + chr(0x1F642)
    add("error_precedence", {"text": value}, scalar_error(chr(0x1F642), len(unicodedata.normalize("NFC", left + right).encode("utf-8"))),
        error=True, tags=["error_precedence"])
    failures = [{"text": value} for value in (None, True, 1, [], {})]
    failures += [None, True, 1, "text", [], {}]
    for index, value in enumerate(failures):
        for dialect in ("TN", "SL"):
            add(f"invalid_{index:02}_{dialect.lower()}", value, "expected a string input", error=True,
                dialect=dialect, tags=["shared_error"])
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
            raise SystemExit("Reverse corpus differs; review independent evidence before regeneration")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
