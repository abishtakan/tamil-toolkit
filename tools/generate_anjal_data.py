"""Generate a strict, bounded Anjal byte profile from pinned TamilUtil data."""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from tools.generate_tscii_golden import raw_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/codec-tscii/TamilUtil.java"
SHA256 = "fbc2e9fc85b83ae9bb617a860629941707711a1de1e23f7233af1bc3178a5753"
SOURCE_LABEL = "TamilUtil Anjal encoder, commit 1f659e70; see codec-anjal.md"


def mappings():
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Pinned Anjal source digest mismatch")
    section = data.decode("utf-8").split("private String convertToAnjal", 1)[1].split("private String convertToTab", 1)[0]
    arrays = []
    for name in ("TamilText", "TamilReplace"):
        body = re.search(r"String " + name + r"\[\]\s*=\s*\{(.*?)\};", section, re.S).group(1)
        arrays.append([json.loads(value) for value in re.findall(r'"(?:[^"\\]|\\.)*"', body)])
    if len(arrays[0]) != 320 or len(arrays[1]) != 320:
        raise ValueError("Unexpected Anjal source row count")
    candidates = defaultdict(set)
    omitted = []
    for legacy, unicode_text in zip(*arrays):
        value = unicodedata.normalize("NFC", unicode_text)
        try:
            key = raw_bytes(legacy)
        except UnicodeEncodeError:
            omitted.append((legacy, value))
            continue
        if not key or key[0] < 0x80 or len(key) > 3:
            raise ValueError(f"Unexpected Anjal key: {key.hex()}")
        candidates[key].add(value)
    if omitted != [(chr(0x2212), chr(0x0ba3) + chr(0x0bc0))]:
        raise ValueError("Unexpected unrepresentable Anjal source glyph")
    ambiguous = {key: sorted(values) for key, values in candidates.items() if len(values) > 1}
    if set(ambiguous) != {bytes([byte]) for byte in (0xe5, 0xe6, 0xe7, 0xe8)}:
        raise ValueError("Unexpected Anjal source conflicts")
    table = {key: next(iter(values)) for key, values in candidates.items() if len(values) == 1}
    return dict(sorted(table.items())), dict(sorted(ambiguous.items()))


def canonical(table):
    reverse = defaultdict(list)
    for key, value in table.items(): reverse[value].append(key)
    return {value: min(keys, key=lambda key: (len(key), key)) for value, keys in reverse.items()}


def lexicon(table, ambiguous):
    lines = ['profile = "anjal-tamilutil-bounded-v1"', 'source = "TamilUtil 1f659e70; Windows-1252/C1 interpretation"', '']
    for key, value in table.items():
        lines.extend(['[[mappings]]', f'hex = "{key.hex()}"', 'unicode = ' + json.dumps(value, ensure_ascii=True), ''])
    for key, values in ambiguous.items():
        lines.extend(['[[ambiguous]]', f'hex = "{key.hex()}"', 'candidates = ' + json.dumps(values, ensure_ascii=True), ''])
    grouped = defaultdict(list)
    for key, value in table.items(): grouped[value].append(key)
    for value, keys in sorted(grouped.items()):
        if len(keys) > 1:
            key = min(keys, key=lambda item: (len(item), item))
            lines.extend(['[[encoding_preferences]]', f'hex = "{key.hex()}"', 'unicode = ' + json.dumps(value, ensure_ascii=True), ''])
    return "\n".join(lines)


def fixtures(table, ambiguous):
    rows = []
    for dialect in ("TN", "SL"):
        for key, value in table.items():
            rows.append(dict(id=f"anjal_decode_{dialect.lower()}_{key.hex()}", op="anjal_bytes_to_unicode", input={"bytes": list(key)}, expected=value, dialect=dialect, tags=["anjal", "mapping"], source=SOURCE_LABEL))
        for value, key in canonical(table).items():
            rows.append(dict(id=f"anjal_encode_{dialect.lower()}_{key.hex()}", op="unicode_to_anjal_bytes", input={"text": value}, expected=list(key), dialect=dialect, tags=["anjal", "mapping"], source=SOURCE_LABEL))
        for byte in (0xe5, 0xe6, 0xe7, 0xe8):
            rows.append(dict(id=f"anjal_ambiguous_{dialect.lower()}_{byte:02x}", op="anjal_bytes_to_unicode", input={"bytes": [byte]}, expected_error=f"ambiguous ANJAL byte at offset 0: 0x{byte:02X}", dialect=dialect, tags=["anjal", "ambiguity"], source=SOURCE_LABEL))
        for name, text in (("ascii", "A 123!"), ("empty", "")):
            rows.append(dict(id=f"anjal_decode_{name}_{dialect.lower()}", op="anjal_bytes_to_unicode", input={"bytes": list(text.encode("ascii"))}, expected=text, dialect=dialect, tags=["anjal", name], source="Anjal byte-profile contract"))
            rows.append(dict(id=f"anjal_encode_{name}_{dialect.lower()}", op="unicode_to_anjal_bytes", input={"text": text}, expected=list(text.encode("ascii")), dialect=dialect, tags=["anjal", name], source="Anjal byte-profile contract"))
    for dialect in ("TN", "SL"):
        rows.append(dict(id=f"anjal_nfd_{dialect.lower()}", op="unicode_to_anjal_bytes", input={"text": "".join(map(chr, (0x0b95, 0x0bc6, 0x0bbe)))}, expected=[0x97, 0x8d, 0x91], dialect=dialect, tags=["anjal", "nfd"], source="Unicode Tamil canonical composition and pinned Anjal reference", unicode_exceptions=[{"path": "/input/text", "kind": "non_nfc", "reason": "Intentional decomposition tests canonical normalization."}]))
    for name, value in (("missing", {}), ("negative", {"bytes": [-1]}), ("large", {"bytes": [256]}), ("string", {"bytes": "abc"}), ("bool", {"bytes": [True]})):
        rows.append(dict(id=f"anjal_invalid_{name}", op="anjal_bytes_to_unicode", input=value, expected_error="expected ANJAL byte array", dialect="COMMON", tags=["anjal", "error"], source="Anjal input contract"))
    for name, text, error in (("emoji", "A\U0001f600", "unsupported Unicode scalar for ANJAL at NFC byte 1: U+1F600"), ("minus_mapping", "\u0ba3\u0bc0", "unsupported Unicode scalar for ANJAL at NFC byte 3: U+0BC0")):
        rows.append(dict(id=f"anjal_encode_error_{name}", op="unicode_to_anjal_bytes", input={"text": text}, expected_error=error, dialect="COMMON", tags=["anjal", "error"], source="Anjal byte-profile contract"))
    rows.append(dict(id="anjal_ambiguous_offset", op="anjal_bytes_to_unicode", input={"bytes": [65, 0xe5]}, expected_error="ambiguous ANJAL byte at offset 1: 0xE5", dialect="COMMON", tags=["anjal", "ambiguity"], source=SOURCE_LABEL))
    rows.append(dict(id="anjal_invalid_offset", op="anjal_bytes_to_unicode", input={"bytes": [65, 0x80]}, expected_error="unsupported ANJAL byte at offset 1: 0x80", dialect="COMMON", tags=["anjal", "error"], source="Anjal byte-profile contract"))
    rows.append(dict(id="anjal_encode_error_joiner", op="unicode_to_anjal_bytes", input={"text": chr(0x200c)}, expected_error="unsupported Unicode scalar for ANJAL at NFC byte 0: U+200C", dialect="COMMON", tags=["anjal", "error"], source="Anjal strict error contract", unicode_exceptions=[{"path": "/input/text", "kind": "joiner", "reason": "Intentional joiner verifies rejection without silent removal."}]))
    return "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("fixtures", "lexicon"))
    args = parser.parse_args()
    table, ambiguous = mappings()
    target = ROOT / ("tests/golden/codec_anjal.jsonl" if args.kind == "fixtures" else "lexicon/anjal.toml")
    target.write_text(fixtures(table, ambiguous) if args.kind == "fixtures" else lexicon(table, ambiguous), encoding="utf-8", newline="\n")
    print(f"Wrote {target.relative_to(ROOT)}: {len(table)} byte keys, {len(canonical(table))} canonical Unicode values, {len(ambiguous)} ambiguous keys")
