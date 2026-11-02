"""Project the pinned Unicode 17 Tamil numeric/symbol subset to TOML."""

import hashlib
import argparse
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/numerals-v0.3/UnicodeData-Tamil.txt"
OUTPUT = ROOT / "lexicon/numerals-symbols.toml"
SOURCE_SHA256 = "79385cd202b825038270bb253b057d83bbaed5a67b776dcfe5cc84684ba9d059"
FRACTION_SOURCE = ROOT / "tests/reference/numerals-v0.3/UnicodeData-fractions.txt"
FRACTION_SHA256 = "aaa7132a55eb2e1dbb7afb5afd0849d8f68f4b66be4dae65b6789f38a4a41476"


def quoted(value: str) -> str:
    pieces = ['"']
    for character in value:
        scalar = ord(character)
        if character == '"':
            pieces.append('\\"')
        elif character == "\\":
            pieces.append("\\\\")
        elif 0x20 <= scalar <= 0x7E:
            pieces.append(character)
        elif scalar <= 0xFFFF:
            pieces.append(f"\\u{scalar:04x}")
        else:
            pieces.append(f"\\U{scalar:08x}")
    pieces.append('"')
    return "".join(pieces)


def rows():
    for path, digest in ((SOURCE, SOURCE_SHA256), (FRACTION_SOURCE, FRACTION_SHA256)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise SystemExit("Unicode 17 symbol source digest changed: " + path.name)
    records = {}
    for line in SOURCE.read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        codepoint = int(fields[0], 16)
        name = fields[1]
        include = (
            codepoint == 0x0BD0
            or 0x0BE6 <= codepoint <= 0x0BEF
            or 0x0BF0 <= codepoint <= 0x0BFA
            or 0x11FC0 <= codepoint <= 0x11FF1
        )
        if not include:
            continue
        numeric = fields[8]
        fraction = Fraction(numeric) if numeric else None
        if codepoint == 0x11FD4:
            fraction = None  # Kiizh scales a following fraction; it is not one alone.
        if 0x0BE6 <= codepoint <= 0x0BEF:
            kind = "digit"
        elif 0x0BF0 <= codepoint <= 0x0BF2:
            kind = "integer_sign"
        elif 0x11FC0 <= codepoint <= 0x11FD3:
            kind = "fraction"
        elif codepoint == 0x11FD4:
            kind = "fraction_modifier"
        elif 0x0BF3 <= codepoint <= 0x0BF5:
            kind = "calendar"
        elif 0x0BF6 <= codepoint <= 0x0BF8 or codepoint in (0x11FE8, 0x11FE9):
            kind = "clerical"
        elif codepoint == 0x0BF9 or 0x11FDD <= codepoint <= 0x11FE0:
            kind = "currency"
        else:
            kind = "symbol"
        records[codepoint] = {
            "codepoint": codepoint,
            "name": name,
            "character": chr(codepoint),
            "kind": kind,
            "rational": fraction,
        }

    canonical = {}
    for entry in records.values():
        value = entry["rational"]
        if value is not None:
            canonical[value] = min(canonical.get(value, entry["codepoint"]), entry["codepoint"])
    for entry in records.values():
        value = entry["rational"]
        entry["canonical_alternative"] = canonical.get(value) if value is not None else None
    return [records[key] for key in sorted(records)]


def project():
    content = [
        "# Unicode 17.0.0 UnicodeData Tamil numeric/symbol subset; Unicode-3.0.",
        'profile = "numerals-symbols-v1"',
        'source_version = "Unicode 17.0.0"',
    ]
    entries = rows()
    for item in entries:
        content.extend(
            [
                "",
                "[[symbols]]",
                f"codepoint = {item['codepoint']}",
                f"character = {quoted(item['character'])}",
                f"name = {quoted(item['name'])}",
                f"kind = {quoted(item['kind'])}",
            ]
        )
        value = item["rational"]
        if value is not None:
            content.append(
                f"rational = {{ numerator = {value.numerator}, denominator = {value.denominator} }}"
            )
            content.append(f"canonical_alternative = {item['canonical_alternative']}")
    return "\n".join(content) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify the canonical projection")
    mode.add_argument("--update", action="store_true", help="write the canonical projection")
    args = parser.parse_args()
    content = project()
    if args.update:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    elif not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != content:
        raise SystemExit("Unicode 17 symbol projection differs; inspect source changes or use --update")
    print(f"{OUTPUT.relative_to(ROOT)}: projected {len(rows())} symbols")
