"""Generate a bounded TAB profile from the pinned TamilUtil reference."""
import argparse
import hashlib
import json
import re
import tomllib
import unicodedata
from collections import defaultdict
from pathlib import Path
from tools.generate_tscii_golden import raw_bytes

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/codec-tscii/TamilUtil.java"
SHA256 = "fbc2e9fc85b83ae9bb617a860629941707711a1de1e23f7233af1bc3178a5753"
SOURCE_LABEL = "TamilUtil 1f659e70; Unicode TAB conversion note UTN 17"


def mappings():
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Pinned TAB source digest mismatch")
    section = data.decode("utf-8").split("private String convertToTab", 1)[1].split("private String convertToTam", 1)[0]
    arrays = []
    for name in ("TamilText", "TamilReplace"):
        body = re.search(r"String " + name + r"\[\]\s*=\s*\{(.*?)\};", section, re.S).group(1)
        arrays.append([json.loads(value) for value in re.findall(r'"(?:[^"\\]|\\.)*"', body)])
    if len(arrays[0]) != 321 or len(arrays[1]) != 321:
        raise ValueError("Unexpected TAB source row count")
    result = {}
    for legacy, unicode_text in zip(*arrays):
        key = raw_bytes(legacy)
        value = unicodedata.normalize("NFC", unicode_text)
        # TamilUtil includes numeral assignments undefined by the TAB note;
        # its last row for C3 is also a digit, conflicting with Tamil KUU.
        if any(0x0be6 <= ord(char) <= 0x0bf2 for char in value):
            continue
        if key[0] < 0x80 or len(key) > 3:
            raise ValueError(f"Unexpected TAB key: {key.hex()}")
        if key in result and result[key] != value:
            raise ValueError(f"Conflicting TAB key: {key.hex()}")
        result[key] = value
    # Standalone signs and punctuation from TAB's published byte inventory.
    supplement = tomllib.loads((ROOT / "lexicon/tab-supplement.toml").read_text(encoding="utf-8"))
    for item in supplement["mappings"]:
        key = bytes.fromhex(item["hex"])
        value = item["unicode"]
        if key in result and result[key] != value:
            raise ValueError(f"TAB standard conflicts at {key.hex()}")
        result[key] = value
    return dict(sorted(result.items()))


def canonical(table):
    reverse = defaultdict(list)
    for key, value in table.items():
        reverse[value].append(key)
    return {value: min(keys, key=lambda key: (len(key), key)) for value, keys in reverse.items()}


def lexicon(table):
    lines = ['profile = "tab-tamilutil-bounded-v1"', 'source = "TamilUtil 1f659e70; Unicode TAB UTN 17"', '']
    for key, value in table.items():
        lines.extend(['[[mappings]]', f'hex = "{key.hex()}"', 'unicode = ' + json.dumps(value, ensure_ascii=True), ''])
    grouped = defaultdict(list)
    for key, value in table.items(): grouped[value].append(key)
    for value, keys in sorted(grouped.items()):
        if len(keys) > 1:
            key = min(keys, key=lambda item: (len(item), item))
            lines.extend(['[[encoding_preferences]]', f'hex = "{key.hex()}"', 'unicode = ' + json.dumps(value, ensure_ascii=True), ''])
    return "\n".join(lines)


def fixtures(table):
    rows = []
    for dialect in ("TN", "SL"):
        for key, value in table.items():
            rows.append(dict(id=f"tab_decode_{dialect.lower()}_{key.hex()}", op="tab_bytes_to_unicode", input={"bytes": list(key)}, expected=value, dialect=dialect, tags=["tab", "mapping"], source=SOURCE_LABEL))
        for value, key in canonical(table).items():
            rows.append(dict(id=f"tab_encode_{dialect.lower()}_{key.hex()}", op="unicode_to_tab_bytes", input={"text": value}, expected=list(key), dialect=dialect, tags=["tab", "mapping"], source=SOURCE_LABEL))
        for name, text in (("ascii", "A 123!"), ("empty", "")):
            rows.append(dict(id=f"tab_decode_{name}_{dialect.lower()}", op="tab_bytes_to_unicode", input={"bytes": list(text.encode("ascii"))}, expected=text, dialect=dialect, tags=["tab", name], source="TAB ASCII compatibility, UTN 17"))
            rows.append(dict(id=f"tab_encode_{name}_{dialect.lower()}", op="unicode_to_tab_bytes", input={"text": text}, expected=list(text.encode("ascii")), dialect=dialect, tags=["tab", name], source="TAB ASCII compatibility, UTN 17"))
    for byte in (0x80, 0x98, 0xa1, 0xad, 0xd0):
        rows.append(dict(id=f"tab_unassigned_{byte:02x}", op="tab_bytes_to_unicode", input={"bytes": [byte]}, expected_error=f"unsupported TAB byte at offset 0: 0x{byte:02X}", dialect="COMMON", tags=["tab", "error"], source="Unicode TAB conversion note UTN 17"))
    for name, value in (("missing", {}), ("negative", {"bytes": [-1]}), ("large", {"bytes": [256]}), ("string", {"bytes": "abc"}), ("bool", {"bytes": [True]})):
        rows.append(dict(id=f"tab_invalid_{name}", op="tab_bytes_to_unicode", input=value, expected_error="expected TAB byte array", dialect="COMMON", tags=["tab", "error"], source="TAB input contract"))
    for name, text, error in (("emoji", "A\U0001f600", "unsupported Unicode scalar for TAB at NFC byte 1: U+1F600"), ("digit", "\u0be7", "unsupported Unicode scalar for TAB at NFC byte 0: U+0BE7")):
        rows.append(dict(id=f"tab_encode_error_{name}", op="unicode_to_tab_bytes", input={"text": text}, expected_error=error, dialect="COMMON", tags=["tab", "error"], source="TAB input contract; UTN 17 excludes Tamil numerals"))
    for dialect in ("TN", "SL"):
        row = dict(id=f"tab_nfd_{dialect.lower()}", op="unicode_to_tab_bytes", input={"text": "".join(map(chr, (0x0b95, 0x0bc6, 0x0bbe)))}, expected=[0xaa, 0xe8, 0xa3], dialect=dialect, tags=["tab", "nfd"], source="Unicode Tamil canonical composition and TAB UTN 17", unicode_exceptions=[{"path": "/input/text", "kind": "non_nfc", "reason": "Intentional decomposition tests canonical normalization."}])
        rows.append(row)
    rows.append(dict(id="tab_invalid_offset", op="tab_bytes_to_unicode", input={"bytes": [65, 128]}, expected_error="unsupported TAB byte at offset 1: 0x80", dialect="COMMON", tags=["tab", "error"], source="TAB strict error contract"))
    return "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("fixtures", "lexicon"))
    args = parser.parse_args()
    table = mappings()
    target = ROOT / ("tests/golden/codec_tab.jsonl" if args.kind == "fixtures" else "lexicon/tab.toml")
    target.write_text(fixtures(table) if args.kind == "fixtures" else lexicon(table), encoding="utf-8", newline="\n")
    print(f"Wrote {target.relative_to(ROOT)}: {len(table)} byte keys, {len(canonical(table))} canonical Unicode values")
