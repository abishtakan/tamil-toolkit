"""Generate deterministic Phase 8 golden vectors (tests/golden/translit_v01.jsonl)."""

import argparse
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tests/golden/translit_v01.jsonl"
SOURCE = "Phase 8 tamil-translit v0.1 contract; docs/specs/translit-v0.1.md"


def row(identifier, op, inp, expected, tags, *, error=False):
    obj = {
        "id": identifier,
        "op": op,
        "input": inp,
        "expected_error" if error else "expected": expected,
        "dialect": "COMMON",
        "tags": ["translit", *tags],
        "source": SOURCE,
    }
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


def render() -> str:
    data = tomllib.loads((ROOT / "lexicon/translit.toml").read_text(encoding="utf-8"))
    lines = []

    # 1. Scholarly bidirectional tests for all 4 schemes
    scholarly = [
        ("iso-15919", "iso_15919"),
        ("madras-lexicon", "madras_lexicon"),
        ("itrans", "itrans"),
        ("harvard-kyoto", "harvard_kyoto"),
    ]
    for scheme_id, field in scholarly:
        slug = scheme_id.replace("-", "_")
        # All 12 vowels
        for idx, v in enumerate(data["vowels"]):
            ta, lat = v["independent"], v[field]
            lines.append(row(f"tr_{slug}_v{idx:02}_to_lat", "transliterate", {"text": ta, "scheme": scheme_id, "direction": "to_latin"}, lat, [slug, "vowel"]))
            lines.append(row(f"tr_{slug}_v{idx:02}_to_ta", "transliterate", {"text": lat, "scheme": scheme_id, "direction": "to_tamil"}, ta, [slug, "vowel"]))
        # Aytham
        ay_ta, ay_lat = data["aytham"], data["aytham_tokens"][field]
        lines.append(row(f"tr_{slug}_aytham_to_lat", "transliterate", {"text": ay_ta, "scheme": scheme_id, "direction": "to_latin"}, ay_lat, [slug, "aytham"]))
        lines.append(row(f"tr_{slug}_aytham_to_ta", "transliterate", {"text": ay_lat, "scheme": scheme_id, "direction": "to_tamil"}, ay_ta, [slug, "aytham"]))
        # All 23 consonants (inherent a + mei)
        for idx, c in enumerate(data["consonants"]):
            ta, lat = c["tamil"], c[field]
            lines.append(row(f"tr_{slug}_c{idx:02}_to_lat", "transliterate", {"text": ta, "scheme": scheme_id, "direction": "to_latin"}, lat + "a", [slug, "consonant"]))
            lines.append(row(f"tr_{slug}_c{idx:02}_to_ta", "transliterate", {"text": lat + "a", "scheme": scheme_id, "direction": "to_tamil"}, ta, [slug, "consonant"]))
            ta_m = ta + "\u0BCD"
            lines.append(row(f"tr_{slug}_m{idx:02}_to_lat", "transliterate", {"text": ta_m, "scheme": scheme_id, "direction": "to_latin"}, lat, [slug, "mei"]))
            lines.append(row(f"tr_{slug}_m{idx:02}_to_ta", "transliterate", {"text": lat, "scheme": scheme_id, "direction": "to_tamil"}, ta_m, [slug, "mei"]))

    # Phrase checks for scholarly schemes
    phrase_cases = [
        ("iso_tamil", "iso-15919", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "tami\u1E3B"),
        ("iso_vanakkam", "iso-15919", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD", "va\u1E47akkam"),
        ("iso_kural", "iso-15919", "\u0BA4\u0BBF\u0BB0\u0BC1\u0B95\u0BCD\u0B95\u0BC1\u0BB1\u0BB3\u0BCD", "tirukku\u1E5Fa\u1E37"),
        ("mtl_tamil", "madras-lexicon", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "tami\u1E3B"),
        ("mtl_aytham", "madras-lexicon", "\u0B8E\u0B83\u0B95\u0BC1", "e\u1E25ku"),
        ("itrans_tamil", "itrans", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "tamizh"),
        ("itrans_vanakkam", "itrans", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD", "vaNakkam"),
        ("hk_tamil", "harvard-kyoto", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "tamiZ"),
        ("hk_vanakkam", "harvard-kyoto", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD", "vaNakkam"),
    ]
    for tag, scheme_id, ta, lat in phrase_cases:
        lines.append(row(f"tr_phrase_{tag}_to_lat", "transliterate", {"text": ta, "scheme": scheme_id, "direction": "to_latin"}, lat, ["phrase"]))
        lines.append(row(f"tr_phrase_{tag}_to_ta", "transliterate", {"text": lat, "scheme": scheme_id, "direction": "to_tamil"}, ta, ["phrase"]))

    # 2. Tamil99 keyboard layout (stateful: vowel signs, pulli, gemination, homorganic nasal+stop)
    t99_cases = [
        ("tamil", "lks/f", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD"),
        ("vanakkam", "vphhkf", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"),
        ("amma", "akkq", "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
        ("nangai", ";bhgr", "\u0BA8\u0B99\u0BCD\u0B95\u0BC6\u0B90" if False else "\u0BA8\u0B99\u0BCD\u0B95\u0BC6\u0B90"),
        ("kaka_explicit_a", "hah", "\u0B95\u0B95"),
        ("homorganic_nt", ";l", "\u0BA8\u0BCD\u0BA4"),
        ("homorganic_ng", "bh", "\u0B99\u0BCD\u0B95"),
        ("homorganic_mp", "kj", "\u0BAE\u0BCD\u0BAA"),
        ("sri_ksha", "Y T", "\u0BB8\u0BCD\u0BB0\u0BC0 \u0B95\u0BCD\u0BB7"),
    ]
    # Remove unused placeholder and keep clean verified Tamil99 words
    t99_cases = [
        ("tamil", "lks/f", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD"),
        ("vanakkam", "vphhkf", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"),
        ("amma", "akkq", "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
        ("kaka_explicit_a", "hah", "\u0B95\u0B95"),
        ("homorganic_nt", ";l", "\u0BA8\u0BCD\u0BA4"),
        ("homorganic_ng", "bh", "\u0B99\u0BCD\u0B95"),
        ("homorganic_mp", "kj", "\u0BAE\u0BCD\u0BAA"),
        ("homorganic_nr", "iu", "\u0BA9\u0BCD\u0BB1"),
        ("sri_ksha", "Y T", "\u0BB8\u0BCD\u0BB0\u0BC0 \u0B95\u0BCD\u0BB7"),
    ]
    for tag, keys, expected in t99_cases:
        lines.append(row(f"tr_t99_{tag}", "transliterate", {"text": keys, "scheme": "tamil99", "direction": "to_tamil"}, expected, ["tamil99"]))

    # 3. Anjal phonetic input
    anjal_cases = [
        ("tamil", "thamizh", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD"),
        ("vanakkam", "vaNakkam", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"),
        ("nandri", "nanRi", "\u0BA8\u0BA9\u0BCD\u0BB1\u0BBF"),
        ("chennai", "chennai", "\u0B9A\u0BC6\u0BA9\u0BCD\u0BA9\u0BC8"),
        ("amma", "ammaa", "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
        ("thanga", "thanga", "\u0BA4\u0B99\u0BCD\u0B95"),
    ]
    for tag, keys, expected in anjal_cases:
        lines.append(row(f"tr_anjal_{tag}", "transliterate", {"text": keys, "scheme": "anjal-phonetic", "direction": "to_tamil"}, expected, ["anjal_phonetic"]))

    # 4. Suratha Bamini live keystroke input
    bamini_cases = [
        ("tamil", "jkpo;", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD"),
        ("ko_kombu", "nfh", "\u0B95\u0BCA"),
        ("koo_kombu", "Nfh", "\u0B95\u0BCB"),
        ("kai_kombu", "if", "\u0B95\u0BC8"),
        ("kau_kombu", "nfs", "\u0B95\u0BCC"),
        ("amma", "mk;kh", "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
    ]
    for tag, keys, expected in bamini_cases:
        lines.append(row(f"tr_suratha_{tag}", "transliterate", {"text": keys, "scheme": "suratha-bamini", "direction": "to_tamil"}, expected, ["suratha_bamini"]))

    # 5. Phonetic / Tanglish v1 (to_tamil + readable to_latin)
    phonetic_cases = [
        ("tamizh", "thamizh", "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD"),
        ("vanakkam", "vaNakkam", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"),
        ("chennai", "chennai", "\u0B9A\u0BC6\u0BA9\u0BCD\u0BA9\u0BC8"),
        ("namaskaram", "namaskaaram", "\u0BA8\u0BAE\u0BB8\u0BCD\u0B95\u0BBE\u0BB0\u0BAE\u0BCD"),
    ]
    for tag, keys, expected in phonetic_cases:
        lines.append(row(f"tr_phonetic_{tag}_to_ta", "transliterate", {"text": keys, "scheme": "phonetic-v1", "direction": "to_tamil"}, expected, ["phonetic_v1"]))
    lines.append(row("tr_phonetic_tamil_to_lat", "transliterate", {"text": "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "scheme": "phonetic-v1", "direction": "to_latin"}, "thamizh", ["phonetic_v1"]))

    # 6. Error contracts
    errors = [
        ("bad_scheme", {"text": "a", "scheme": "unknown", "direction": "to_tamil"}, "unsupported transliteration scheme"),
        ("bad_dir", {"text": "a", "scheme": "iso-15919", "direction": "sideways"}, "unsupported transliteration direction"),
        ("t99_reverse", {"text": "\u0BA4", "scheme": "tamil99", "direction": "to_latin"}, "reverse transliteration is not supported for keyboard layout"),
        ("anjal_reverse", {"text": "\u0BA4", "scheme": "anjal-phonetic", "direction": "to_latin"}, "reverse transliteration is not supported for keyboard layout"),
        ("suratha_reverse", {"text": "\u0BA4", "scheme": "suratha-bamini", "direction": "to_latin"}, "reverse transliteration is not supported for keyboard layout"),
        ("missing_text", {"scheme": "iso-15919", "direction": "to_tamil"}, "expected a string input"),
    ]
    for tag, inp, err in errors:
        lines.append(row(f"tr_err_{tag}", "transliterate", inp, err, ["error"], error=True))

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("translit_v01.jsonl differs; regenerate with tools/generate_translit_golden.py")
    else:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    print(f"{OUTPUT.name}: {len(content.splitlines())} vectors")
