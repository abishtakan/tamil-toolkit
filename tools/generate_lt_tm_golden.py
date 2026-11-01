"""Generate LT-TM mapping fixtures from the canonical declarative table."""

import json
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEXICON = ROOT / "lexicon/lt_tm.toml"
OUTPUT = ROOT / "tests/golden/codec_lt_tm.jsonl"
CONFIG_SHA256 = "32fc21ffe8e2fbffa33d5f3899acfd15ee8a2ab9fc5fd5e931f9e7d4ec3326cd"
MAP_SOURCE = (
    "Azhagi+ Portable LT-TM configuration projection, SHA-256 "
    f"{CONFIG_SHA256}; see docs/specs/codec-lt-tm.md"
)
PDF_SOURCE = (
    "Tamil Virtual Academy 2003 Tamilmann Tolkappiyam PDF, rendered-page check; "
    "see docs/specs/codec-lt-tm.md"
)
CONTRACT_SOURCE = "LT-TM profile input/error contract; see docs/specs/codec-lt-tm.md"


def row(identifier, operation, input_value, expected, source, tags, *, error=False, nfd=False):
    result = {
        "id": identifier,
        "op": operation,
        "input": input_value,
        "expected_error" if error else "expected": expected,
        "dialect": "COMMON",
        "tags": ["lt_tm", *tags],
        "source": source,
    }
    if nfd:
        result["unicode_exceptions"] = [{
            "path": "/input/text",
            "kind": "non_nfc",
            "reason": "Intentional canonical decomposition tests LT-TM encoder NFC normalization.",
        }]
    return json.dumps(result, ensure_ascii=True, separators=(",", ":"))


def generate():
    profile = tomllib.loads(LEXICON.read_text(encoding="utf-8"))
    if profile["profile"] != "lt-tm-indoword-cid-v1":
        raise ValueError("Unexpected LT-TM profile")
    mappings = profile["mappings"]
    if len(mappings) != 332:
        raise ValueError("Expected all 332 LT-TM mappings")

    lines = []
    for mapping in mappings:
        codes = mapping["cids"]
        key = "".join(f"{code:04x}" for code in codes)
        lines.append(row(
            f"codec_lt_tm_decode_{key}",
            "lt_tm_codes_to_unicode",
            {"codes": codes},
            mapping["unicode"], MAP_SOURCE, ["mapping", "decode"],
        ))
        lines.append(row(
            f"codec_lt_tm_encode_{key}",
            "unicode_to_lt_tm_codes",
            {"text": mapping["unicode"]},
            codes, MAP_SOURCE, ["mapping", "encode"],
        ))

    title_codes = [0x0062, 0x006A, 0x0068, 0x0161, 0x0066, 0x0068,
                   0x00A5, 0x00E3, 0x0061, 0x00AB]
    title = "\u0ba4\u0bca\u0bb2\u0bcd\u0b95\u0bbe\u0baa\u0bcd\u0baa\u0bbf\u0baf\u0bae\u0bcd"
    lines.extend([
        row("codec_lt_tm_pdf_title_decode", "lt_tm_codes_to_unicode",
            {"codes": title_codes}, title, PDF_SOURCE, ["pdf", "title"]),
        row("codec_lt_tm_pdf_title_encode", "unicode_to_lt_tm_codes",
            {"text": title}, title_codes, PDF_SOURCE, ["pdf", "roundtrip"]),
        row("codec_lt_tm_text_bjh", "lt_tm_text_to_unicode",
            {"text": "bjh"}, "\u0ba4\u0bca", PDF_SOURCE, ["legacy_text"]),
        row("codec_lt_tm_common_sentence", "lt_tm_text_to_unicode",
            {"text": "tz\u00a1f\u00ab, \u00efJ j\u00c4\u0153 vG\u00a4J."},
            "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd, \u0b87\u0ba4\u0bc1 \u0ba4\u0bae\u0bbf\u0bb4\u0bcd \u0b8e\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1.",
            MAP_SOURCE, ["legacy_text", "phrase"]),
        row("codec_lt_tm_text_high_code", "lt_tm_text_to_unicode",
            {"text": "\u2219"}, "\u0bfa", MAP_SOURCE, ["legacy_text", "high_code"]),
        row("codec_lt_tm_variant_c4", "lt_tm_codes_to_unicode",
            {"codes": [0x00C4]}, "\u0bae\u0bbf", MAP_SOURCE, ["variant"]),
        row("codec_lt_tm_variant_e4", "lt_tm_codes_to_unicode",
            {"codes": [0x00E4]}, "\u0bb2\u0bc0", MAP_SOURCE, ["variant"]),
        row("codec_lt_tm_ksha_i", "unicode_to_lt_tm_codes",
            {"text": "\u0b95\u0bcd\u0bb7\u0bbf"}, [0x00F8], MAP_SOURCE, ["grantha"]),
        row("codec_lt_tm_ascii_fallback", "lt_tm_codes_to_unicode",
            {"codes": [0x0020, 0x0031, 0x002C]}, " 1,", CONTRACT_SOURCE, ["fallback"]),
        row("codec_lt_tm_preserve_unknown", "lt_tm_codes_to_unicode",
            {"codes": [0x2603], "errors": "preserve"}, "\u2603", CONTRACT_SOURCE, ["preserve"]),
        row("codec_lt_tm_decomposed_encode", "unicode_to_lt_tm_codes",
            {"text": unicodedata.normalize("NFD", "\u0ba4\u0bca")},
            [0x0062, 0x006A, 0x0068], CONTRACT_SOURCE, ["nfc"], nfd=True),
        row("codec_lt_tm_legacy_text_encode", "unicode_to_lt_tm_text",
            {"text": "\u0ba4\u0bca"}, "bjh", CONTRACT_SOURCE, ["legacy_text", "encode"]),
        row("codec_lt_tm_unmapped_strict", "lt_tm_codes_to_unicode",
            {"codes": [0x0081]}, "unsupported LT-TM code at offset 0: U+0081",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_lt_tm_invalid_surrogate", "lt_tm_codes_to_unicode",
            {"codes": [0xD800]}, "invalid LT-TM code unit at offset 0: 0xD800",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_lt_tm_unmapped_ascii_letter", "lt_tm_codes_to_unicode",
            {"codes": [0x0062]}, "unsupported LT-TM code at offset 0: U+0062",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_lt_tm_non_bmp_text", "lt_tm_text_to_unicode",
            {"text": "\U0001f642"}, "LT-TM text contains non-BMP scalar at character 0: U+1F642",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_lt_tm_unencodable", "unicode_to_lt_tm_codes",
            {"text": "\U0001f642"}, "unsupported Unicode scalar for LT-TM at NFC byte 0: U+1F642",
            CONTRACT_SOURCE, ["error"], error=True),
        row("codec_lt_tm_missing_codes", "lt_tm_codes_to_unicode",
            {}, "expected LT-TM code array", CONTRACT_SOURCE, ["error"], error=True),
    ])
    for identifier, value in (
        ("string", "not-an-array"),
        ("negative", [-1]),
        ("large", [65536]),
        ("fraction", [1.5]),
        ("boolean", [True]),
    ):
        lines.append(row(
            f"codec_lt_tm_invalid_codes_{identifier}", "lt_tm_codes_to_unicode",
            {"codes": value}, "expected LT-TM code array", CONTRACT_SOURCE, ["error"], error=True,
        ))

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(generate(), encoding="utf-8", newline="\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
