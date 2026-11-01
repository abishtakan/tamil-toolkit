"""Generate Vanavil Avvaiyar mapping fixtures from the canonical declarative table."""

import json
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEXICON = ROOT / "lexicon/vanavil.toml"
OUTPUT = ROOT / "tests/golden/codec_vanavil.jsonl"
CONFIG_SHA256 = "4948396d50fbbaf251ddfe620ca5d8a0ccdb65b5bef07231065a5d6439754b67"
MAP_SOURCE = (
    "Azhagi+ Portable Vanavil configuration projection, SHA-256 "
    f"{CONFIG_SHA256}; see docs/specs/codec-vanavil.md"
)
FONT_SOURCE = (
    "Vanavilavvai.ttf cmap cross-check, SHA-256 "
    "ba7f814d22dbbf66498b19a52efb62b8412bc52bde0452e624af601d17b709a7; "
    "see docs/specs/codec-vanavil.md"
)
CONTRACT_SOURCE = "Vanavil profile input/error contract; see docs/specs/codec-vanavil.md"


def row(identifier, operation, input_value, expected, source, tags, *, error=False, nfd=False):
    result = {
        "id": identifier,
        "op": operation,
        "input": input_value,
        "expected_error" if error else "expected": expected,
        "dialect": "COMMON",
        "tags": ["vanavil", *tags],
        "source": source,
    }
    if nfd:
        result["unicode_exceptions"] = [{
            "path": "/input/text",
            "kind": "non_nfc",
            "reason": "Intentional canonical decomposition tests Vanavil encoder NFC normalization.",
        }]
    return json.dumps(result, ensure_ascii=True, separators=(",", ":"))


def generate():
    profile = tomllib.loads(LEXICON.read_text(encoding="utf-8"))
    if profile["profile"] != "vanavil-avvaiyar-cid-v1":
        raise ValueError("Unexpected Vanavil profile")
    mappings = profile["mappings"]
    if len(mappings) != 319:
        raise ValueError("Expected all 319 Vanavil mappings")

    lines = []
    for mapping in mappings:
        codes = mapping["cids"]
        key = "".join(f"{code:04x}" for code in codes)
        lines.append(row(
            f"codec_vanavil_decode_{key}",
            "vanavil_codes_to_unicode",
            {"codes": codes},
            mapping["unicode"], MAP_SOURCE, ["mapping", "decode"],
        ))
        lines.append(row(
            f"codec_vanavil_encode_{key}",
            "unicode_to_vanavil_codes",
            {"text": mapping["unicode"]},
            codes, MAP_SOURCE, ["mapping", "encode"],
        ))

    title_codes = [0x0062, 0x006A, 0x0068, 0x0161, 0x0066, 0x0068,
                   0x00A5, 0x00C3, 0x0061, 0x00AB]
    title = "\u0ba4\u0bca\u0bb2\u0bcd\u0b95\u0bbe\u0baa\u0bcd\u0baa\u0bbf\u0baf\u0bae\u0bcd"
    lines.extend([
        row("codec_vanavil_title_decode", "vanavil_codes_to_unicode",
            {"codes": title_codes}, title, FONT_SOURCE, ["word", "title"]),
        row("codec_vanavil_title_encode", "unicode_to_vanavil_codes",
            {"text": title}, title_codes, FONT_SOURCE, ["word", "roundtrip"]),
        row("codec_vanavil_text_bjh", "vanavil_text_to_unicode",
            {"text": "bjh"}, "\u0ba4\u0bca", FONT_SOURCE, ["legacy_text"]),
        row("codec_vanavil_common_sentence", "vanavil_text_to_unicode",
            {"text": "tz\u00a1f\u00ab, \u00cfJ j\u00e4\u0153 vG\u00a4J."},
            "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd, \u0b87\u0ba4\u0bc1 \u0ba4\u0bae\u0bbf\u0bb4\u0bcd \u0b8e\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1.",
            MAP_SOURCE, ["legacy_text", "phrase"]),
        row("codec_vanavil_text_credit_sign", "vanavil_text_to_unicode",
            {"text": "\u00b7"}, "\u0bfa", MAP_SOURCE, ["legacy_text", "symbol"]),
        row("codec_vanavil_variant_c4", "vanavil_codes_to_unicode",
            {"codes": [0x00C4]}, "\u0bb2\u0bc0", MAP_SOURCE, ["variant"]),
        row("codec_vanavil_variant_e4", "vanavil_codes_to_unicode",
            {"codes": [0x00E4]}, "\u0bae\u0bbf", MAP_SOURCE, ["variant"]),
        row("codec_vanavil_ksha_i", "unicode_to_vanavil_codes",
            {"text": "\u0b95\u0bcd\u0bb7\u0bbf"}, [0x00F8], MAP_SOURCE, ["grantha"]),
        row("codec_vanavil_ascii_fallback", "vanavil_codes_to_unicode",
            {"codes": [0x0020, 0x0031, 0x002C]}, " 1,", CONTRACT_SOURCE, ["fallback"]),
        row("codec_vanavil_preserve_unknown", "vanavil_codes_to_unicode",
            {"codes": [0x2603], "errors": "preserve"}, "\u2603", CONTRACT_SOURCE, ["preserve"]),
        row("codec_vanavil_decomposed_encode", "unicode_to_vanavil_codes",
            {"text": unicodedata.normalize("NFD", "\u0ba4\u0bca")},
            [0x0062, 0x006A, 0x0068], CONTRACT_SOURCE, ["nfc"], nfd=True),
        row("codec_vanavil_legacy_text_encode", "unicode_to_vanavil_text",
            {"text": "\u0ba4\u0bca"}, "bjh", CONTRACT_SOURCE, ["legacy_text", "encode"]),
        row("codec_vanavil_unmapped_strict", "vanavil_codes_to_unicode",
            {"codes": [0x0081]}, "unsupported Vanavil code at offset 0: U+0081",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_vanavil_invalid_surrogate", "vanavil_codes_to_unicode",
            {"codes": [0xD800]}, "invalid Vanavil code unit at offset 0: 0xD800",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_vanavil_unmapped_ascii_letter", "vanavil_codes_to_unicode",
            {"codes": [0x0062]}, "unsupported Vanavil code at offset 0: U+0062",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_vanavil_non_bmp_text", "vanavil_text_to_unicode",
            {"text": "\U0001f642"}, "Vanavil text contains non-BMP scalar at character 0: U+1F642",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_vanavil_unencodable", "unicode_to_vanavil_codes",
            {"text": "\U0001f642"}, "unsupported Unicode scalar for Vanavil at NFC byte 0: U+1F642",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_vanavil_missing_codes", "vanavil_codes_to_unicode",
            {}, "expected Vanavil code array", CONTRACT_SOURCE, ["error"], error=True),
    ])
    for identifier, value in (
        ("string", "not-an-array"),
        ("negative", [-1]),
        ("large", [65536]),
        ("fraction", [1.5]),
        ("boolean", [True]),
    ):
        lines.append(row(
            f"codec_vanavil_invalid_codes_{identifier}", "vanavil_codes_to_unicode",
            {"codes": value}, "expected Vanavil code array", CONTRACT_SOURCE, ["error"], error=True,
        ))

    return "\n".join(lines) + "\n"


def build_lexicon():
    lt_tm = tomllib.loads((ROOT / "lexicon/lt_tm.toml").read_text(encoding="utf-8"))

    def to_vanavil_cid(cid):
        if 0x00C0 <= cid <= 0x00CF:
            return cid + 0x20
        if 0x00E0 <= cid <= 0x00EF:
            return cid - 0x20
        if cid == 0x2219:
            return 0x00B7
        return cid

    entries = []
    for mapping in lt_tm["mappings"]:
        if "\u0bb6" in mapping["unicode"]:
            continue
        cids = [to_vanavil_cid(cid) for cid in mapping["cids"]]
        entries.append((cids, mapping["unicode"]))
    entries.sort(key=lambda item: item[0])
    if len(entries) != 319:
        raise ValueError("Expected 319 Vanavil entries")

    lines = [
        'profile = "vanavil-avvaiyar-cid-v1"',
        'source = "Azhagi+ Portable Vanavil mapping configuration, normalized projection; see docs/specs/codec-vanavil.md"',
        'source_url = "https://www.azhagi.com/any-tamil-font.php"',
        f'source_sha256 = "{CONFIG_SHA256}"',
        "max_key_cids = 3",
    ]
    for cids, unicode_text in entries:
        cid_str = ", ".join(f"0x{cid:04X}" for cid in cids)
        uni_str = "".join(f"\\u{ord(ch):04X}" for ch in unicode_text)
        lines.extend(["", "[[mappings]]", f"cids = [{cid_str}]", f'unicode = "{uni_str}"'])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    if not LEXICON.is_file():
        lexicon_text = build_lexicon()
        LEXICON.write_text(lexicon_text, encoding="utf-8", newline="\n")
        (ROOT / "crates/tamil-codec/lexicon/vanavil.toml").write_text(
            lexicon_text, encoding="utf-8", newline="\n"
        )
    OUTPUT.write_text(generate(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
