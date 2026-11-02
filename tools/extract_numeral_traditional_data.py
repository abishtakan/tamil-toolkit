"""Project CLDR 49 root Tamil traditional integer rules to canonical TOML."""

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/numerals-v0.3/root-rbnf.xml"
OUTPUT = ROOT / "lexicon/numerals-traditional.toml"
SOURCE_SHA256 = "43fcb8dab6f1afa8c59be9eb6be9b6df0da45dc5cc91f6a3710cf2631e01ed2e"
MAX_INTEGER = 99_999_999
RULESETS = ("%tamil", "%%tamil-thousands")


def project() -> str:
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise SystemExit("CLDR 49 root RBNF digest changed")
    group = ET.fromstring(raw).find(
        './/rulesetGrouping[@type="NumberingSystemRules"]/rbnfRules'
    )
    if group is None or not group.text:
        raise SystemExit("CLDR root NumberingSystemRules not found")

    selected = {name: [] for name in RULESETS}
    current = None
    for raw_line in group.text.splitlines():
        line = raw_line.strip()
        if line.startswith("%") and line.endswith(":"):
            candidate = line[:-1]
            current = candidate if candidate in selected else None
            continue
        if current is None or not line:
            continue
        base_text, pattern = line.split(":", 1)
        base_parts = base_text.strip().split("/", 1)
        if not all(part.isdigit() for part in base_parts):
            continue
        base = int(base_parts[0])
        if base > MAX_INTEGER:
            continue
        divisor = (
            int(base_parts[1])
            if len(base_parts) == 2
            else (10 ** max(len(str(base)) - 1, 0) if base else 1)
        )
        selected[current].append((base, divisor, pattern.strip().removesuffix(";")))

    if any(not selected[name] for name in RULESETS):
        raise SystemExit("missing required CLDR root Tamil traditional rules")
    lines = [
        "# CLDR 49 release-49/common/rbnf/root.xml, NumberingSystemRules, %tamil and",
        "# %%tamil-thousands, lines 772-795; Unicode-3.0. Build-time data only.",
        'profile = "numerals-traditional-v1"',
        f"max_integer = {MAX_INTEGER}",
        'negative = "\\u2212"',
    ]
    for name in RULESETS:
        lines.extend(["", "[[rulesets]]", f"name = {json.dumps(name)}"])
        for base, divisor, pattern in selected[name]:
            lines.extend(
                [
                    "",
                    "[[rulesets.rules]]",
                    f"base = {base}",
                    f"divisor = {divisor}",
                    f"pattern = {json.dumps(pattern, ensure_ascii=True)}",
                ]
            )
    return "\n".join(lines) + "\n"


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
        raise SystemExit("traditional integer projection differs; inspect CLDR changes or use --update")
    print(f"{OUTPUT.relative_to(ROOT)}: projected {content.count('[[rulesets.rules]]')} rules")
