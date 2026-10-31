"""Generate the bounded TAM profile from TAB data and cited TAM assignments."""
import argparse
import json
import tomllib
from collections import defaultdict
from pathlib import Path
from tools import generate_tab_data as tab

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "Unicode TAM conversion note UTN 18; TamilUtil TAB reference 1f659e70"


def mappings():
    result = tab.mappings()
    supplement = tomllib.loads((ROOT / "lexicon/tam-supplement.toml").read_text(encoding="utf-8"))
    for item in supplement["mappings"]:
        key = bytes.fromhex(item["hex"])
        value = item["unicode"]
        if key in result and result[key] != value:
            raise ValueError(f"TAM mapping conflict at {key.hex()}")
        result[key] = value
    return dict(sorted(result.items()))


def canonical(table):
    reverse = defaultdict(list)
    for key, value in table.items(): reverse[value].append(key)
    return {value: min(keys, key=lambda key: (len(key), key)) for value, keys in reverse.items()}


def lexicon(table):
    lines = ['profile = "tam-utn18-bounded-v1"', 'source = "Unicode TAM UTN 18; TamilUtil TAB reference 1f659e70"', '']
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
            rows.append(dict(id=f"tam_decode_{dialect.lower()}_{key.hex()}", op="tam_bytes_to_unicode", input={"bytes": list(key)}, expected=value, dialect=dialect, tags=["tam", "mapping"], source=SOURCE))
        for value, key in canonical(table).items():
            rows.append(dict(id=f"tam_encode_{dialect.lower()}_{key.hex()}", op="unicode_to_tam_bytes", input={"text": value}, expected=list(key), dialect=dialect, tags=["tam", "mapping"], source=SOURCE))
        for name, text in (("punctuation", " 123!?[]"), ("empty", "")):
            rows.append(dict(id=f"tam_decode_{name}_{dialect.lower()}", op="tam_bytes_to_unicode", input={"bytes": list(text.encode("ascii"))}, expected=text, dialect=dialect, tags=["tam", name], source="TAM byte inventory UTN 18"))
            rows.append(dict(id=f"tam_encode_{name}_{dialect.lower()}", op="unicode_to_tam_bytes", input={"text": text}, expected=list(text.encode("ascii")), dialect=dialect, tags=["tam", name], source="TAM byte inventory UTN 18"))
        rows.append(dict(id=f"tam_nfd_{dialect.lower()}", op="unicode_to_tam_bytes", input={"text": "".join(map(chr, (0x0b95, 0x0bc6, 0x0bbe)))}, expected=[0xaa, 0xe8, 0xa3], dialect=dialect, tags=["tam", "nfd"], source="Unicode Tamil canonical composition and TAM UTN 18", unicode_exceptions=[{"path": "/input/text", "kind": "non_nfc", "reason": "Intentional decomposition tests canonical normalization."}]))
    for byte in (0x80, 0x81, 0x8d, 0x8e, 0x8f, 0x90, 0x9d, 0x9e):
        rows.append(dict(id=f"tam_unassigned_{byte:02x}", op="tam_bytes_to_unicode", input={"bytes": [byte]}, expected_error=f"unsupported TAM byte at offset 0: 0x{byte:02X}", dialect="COMMON", tags=["tam", "error"], source="Unicode TAM conversion note UTN 18"))
    for name, value in (("missing", {}), ("negative", {"bytes": [-1]}), ("large", {"bytes": [256]}), ("string", {"bytes": "abc"}), ("bool", {"bytes": [True]})):
        rows.append(dict(id=f"tam_invalid_{name}", op="tam_bytes_to_unicode", input=value, expected_error="expected TAM byte array", dialect="COMMON", tags=["tam", "error"], source="TAM input contract"))
    for name, text, error in (("emoji", " \U0001f600", "unsupported Unicode scalar for TAM at NFC byte 1: U+1F600"), ("latin_upper", "A", "unsupported Unicode scalar for TAM at NFC byte 0: U+0041"), ("latin_lower", "s", "unsupported Unicode scalar for TAM at NFC byte 0: U+0073"), ("digit", "\u0be7", "unsupported Unicode scalar for TAM at NFC byte 0: U+0BE7")):
        rows.append(dict(id=f"tam_encode_error_{name}", op="unicode_to_tam_bytes", input={"text": text}, expected_error=error, dialect="COMMON", tags=["tam", "error"], source="TAM byte inventory and UTN 18 numeral exclusion"))
    rows.append(dict(id="tam_encode_error_joiner", op="unicode_to_tam_bytes", input={"text": chr(0x200c)}, expected_error="unsupported Unicode scalar for TAM at NFC byte 0: U+200C", dialect="COMMON", tags=["tam", "error"], source="TAM strict error contract", unicode_exceptions=[{"path": "/input/text", "kind": "joiner", "reason": "Intentional joiner verifies rejection without silent removal."}]))
    rows.append(dict(id="tam_invalid_offset", op="tam_bytes_to_unicode", input={"bytes": [32, 128]}, expected_error="unsupported TAM byte at offset 1: 0x80", dialect="COMMON", tags=["tam", "error"], source="TAM strict error contract"))
    return "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=("fixtures", "lexicon"))
    args = parser.parse_args()
    table = mappings()
    target = ROOT / ("tests/golden/codec_tam.jsonl" if args.kind == "fixtures" else "lexicon/tam.toml")
    target.write_text(fixtures(table) if args.kind == "fixtures" else lexicon(table), encoding="utf-8", newline="\n")
    print(f"Wrote {target.relative_to(ROOT)}: {len(table)} byte keys, {len(canonical(table))} canonical Unicode values")
