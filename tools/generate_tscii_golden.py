"""Generate bounded TSCII fixtures/data from the pinned MIT reference encoder."""

import argparse
import hashlib
import json
import re
import tomllib
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/codec-tscii/TamilUtil.java"
SHA256 = "fbc2e9fc85b83ae9bb617a860629941707711a1de1e23f7233af1bc3178a5753"
SOURCE_LABEL = "TamilUtil TSCII encoder, commit 1f659e70; see tests/reference/codec-tscii"


def raw_bytes(value):
    result = bytearray()
    for character in value:
        try:
            result.extend(character.encode("cp1252"))
        except UnicodeEncodeError:
            code = ord(character)
            if 0x80 <= code <= 0x9f:
                result.append(code)
            else:
                raise
    return bytes(result)


def mappings():
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Pinned TSCII source digest mismatch")
    section = data.decode("utf-8").split("private String convertToTSCII", 1)[1].split("private String convertToAnjal", 1)[0]
    result = {}
    for line in section.splitlines():
        match = re.search(r'\.replace\(("(?:[^"\\]|\\.)*"),\s*("(?:[^"\\]|\\.)*")\)', line)
        if not match:
            continue
        unicode_text, legacy_text = map(json.loads, match.groups())
        key = raw_bytes(legacy_text)
        # The source uses Java String.replace, so its escaped backslash is
        # literal. IANA assigns the following byte directly to this letter.
        if key == bytes([0x5c, 0x88]) and unicode_text == "\u0b9c\u0bcd":
            key = bytes([0x88])
        value = unicodedata.normalize("NFC", unicode_text)
        if not key or key[0] < 0x80 or len(key) > 3:
            raise ValueError(f"Unexpected reference key: {key.hex()}")
        if key in result and result[key] != value:
            raise ValueError(f"Ambiguous reference key: {key.hex()}")
        result[key] = value
    # IANA's draft documents this deprecated alternate byte explicitly.
    result[bytes([0xad])] = "\u0b87"
    supplement = tomllib.loads((ROOT / "lexicon/tscii-iana-supplement.toml").read_text(encoding="utf-8"))
    for key in supplement["remove_hex"]:
        del result[bytes.fromhex(key)]
    for item in supplement["mappings"]:
        key = bytes.fromhex(item["hex"])
        value = unicodedata.normalize("NFC", item["unicode"])
        if key in result and result[key] != value:
            raise ValueError(f"Conflicting audited key: {key.hex()}")
        result[key] = value
    return dict(sorted(result.items()))


def fixtures(table):
    audited = {bytes.fromhex(item["hex"]) for item in tomllib.loads((ROOT / "lexicon/tscii-iana-supplement.toml").read_text(encoding="utf-8"))["mappings"]}
    rows = []
    for dialect in ("TN", "SL"):
        for key, value in table.items():
            rows.append({"id": f"codec_tscii_map_{dialect.lower()}_{key.hex()}", "op": "tscii_bytes_to_unicode",
                         "input": {"bytes": list(key)}, "expected": value, "dialect": dialect,
                         "tags": ["tscii", "mapping"], "source":
                         ("IANA TSCII registration draft and Unicode Tamil chart; see lexicon/tscii-iana-supplement.toml" if key in audited else SOURCE_LABEL + "; IANA registration draft byte assignment" if key in (bytes([0xad]), bytes([0x88])) else SOURCE_LABEL)})
        rows.append({"id": f"codec_tscii_ascii_{dialect.lower()}", "op": "tscii_bytes_to_unicode",
                     "input": {"bytes": list(range(128))}, "expected": "".join(map(chr, range(128))),
                     "dialect": dialect, "tags": ["tscii", "ascii"], "source": "IANA TSCII registration draft, ASCII range"})
        rows.append({"id": f"codec_tscii_word_{dialect.lower()}", "op": "tscii_bytes_to_unicode",
                     "input": {"bytes": [0xba, 0xa2, 0xc5, 0xfd]},
                     "expected": "\u0b9a\u0bbf\u0bb5\u0ba9\u0bcd", "dialect": dialect,
                     "tags": ["tscii", "word"], "source": "TamilUtil encoder; Aril TSCII example"})
        for name, encoded, expected in (("short", [0xa6, 0xb8], "\u0b95\u0bc6"),
                                        ("long", [0xa6, 0xb8, 0xa1], "\u0b95\u0bca")):
            rows.append({"id": f"codec_tscii_longest_{name}_{dialect.lower()}", "op": "tscii_bytes_to_unicode",
                         "input": {"bytes": encoded}, "expected": expected, "dialect": dialect,
                         "tags": ["tscii", "longest_match"], "source": SOURCE_LABEL + "; Unicode NFC"})
    for byte in (0xa0, 0xff):
        rows.append({"id": f"codec_tscii_unassigned_{byte:02x}", "op": "tscii_bytes_to_unicode",
                     "input": {"bytes": [byte]}, "expected_error": f"unsupported TSCII byte at offset 0: 0x{byte:02X}",
                     "dialect": "COMMON", "tags": ["tscii", "error"], "source": "IANA TSCII registration draft, unassigned slots"})
    for suffix, value in (("missing", {}), ("negative", {"bytes": [-1]}), ("large", {"bytes": [256]}),
                          ("string", {"bytes": "abc"}), ("bool", {"bytes": [True]})):
        rows.append({"id": f"codec_tscii_invalid_{suffix}", "op": "tscii_bytes_to_unicode", "input": value,
                     "expected_error": "expected TSCII byte array", "dialect": "COMMON", "tags": ["tscii", "error"],
                     "source": "codec-tscii-draft input contract"})
    rows.append({"id": "codec_tscii_offset", "op": "tscii_bytes_to_unicode", "input": {"bytes": [65, 255]},
                 "expected_error": "unsupported TSCII byte at offset 1: 0xFF", "dialect": "COMMON",
                 "tags": ["tscii", "error"], "source": "codec-tscii-draft error contract"})
    return "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)


def lexicon(table):
    lines = ['profile = "tscii-tamilutil-bounded-v1"', 'source = "TamilUtil 1f659e70; IANA registration draft and audited supplement"', ""]
    for key, value in table.items():
        lines.extend(["[[mappings]]", f'hex = "{key.hex()}"', "unicode = " + json.dumps(value, ensure_ascii=True), ""])
    lines.extend(["[[encoding_preferences]]", 'hex = "fe"', 'unicode = "\\u0b87"', ""])
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("fixtures", "lexicon"))
    args = parser.parse_args()
    table = mappings()
    target = ROOT / ("tests/golden/codec_tscii_bytes.jsonl" if args.kind == "fixtures" else "lexicon/tscii.toml")
    target.write_text(fixtures(table) if args.kind == "fixtures" else lexicon(table), encoding="utf-8", newline="\n")
    print(f"Wrote {target.relative_to(ROOT)} from {len(table)} reference mappings.")
