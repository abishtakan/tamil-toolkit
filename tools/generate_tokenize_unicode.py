"""Project the Unicode 17 properties used by the Tamil boundary profile."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/reference/unicode-17.0.0"
OUTPUT = ROOT / "lexicon/tokenize-unicode-v17.toml"


def records(filename):
    data = (REFERENCE / filename).read_bytes()
    sources = json.loads((REFERENCE / "sources.json").read_text(encoding="utf-8"))
    source = next(row for row in sources["files"] if row["file"] == filename)
    if hashlib.sha256(data).hexdigest() != source["sha256"]:
        raise ValueError(f"Unicode reference checksum mismatch: {filename}")
    for line in data.decode("utf-8").splitlines():
        value = line.partition("#")[0].strip()
        if value:
            interval, category = map(str.strip, value.split(";"))
            start, _, end = interval.partition("..")
            yield int(start, 16), int(end or start, 16), category


def merged(ranges):
    result = []
    for start, end in sorted(ranges):
        if result and start <= result[-1][1] + 1:
            result[-1][1] = max(end, result[-1][1])
        else:
            result.append([start, end])
    return result


def projection():
    general = list(records("DerivedGeneralCategory.txt"))
    properties = {
        "letter": [(a, b) for a, b, c in general if c.startswith("L")],
        "mark": [(a, b) for a, b, c in general if c.startswith("M")],
        "decimal": [(a, b) for a, b, c in general if c == "Nd"],
        "format": [(a, b) for a, b, c in general if c == "Cf"],
        "whitespace": [(a, b) for a, b, c in records("PropList.txt") if c == "White_Space"],
    }
    sentence = list(records("SentenceBreakProperty.txt"))
    for key, classes in {
        "hard": {"Sep", "CR", "LF"},
        "sentence_tail": {"Close", "Sp", "Extend", "Format"},
        "terminator": {"ATerm", "STerm"},
    }.items():
        properties[key] = [(a, b) for a, b, c in sentence if c in classes]
    lines = ['version = "17.0.0"', '# Generated from Unicode 17.0.0 under Unicode License V3.']
    for name, ranges in properties.items():
        lines.append(f"{name} = [")
        lines.extend(f"  [0x{a:X}, 0x{b:X}]," for a, b in merged(ranges))
        lines.append("]")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    output = projection()
    if parser.parse_args().check:
        if OUTPUT.read_bytes() != output:
            raise SystemExit(f"Stale Unicode property projection: {OUTPUT}")
    else:
        OUTPUT.write_bytes(output)


if __name__ == "__main__":
    main()
