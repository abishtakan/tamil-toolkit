"""Project CLDR 49's bounded Tamil ordinal rules into build-time TOML."""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/reference/numerals-v0.3/ta-rbnf.xml"
OUTPUT = ROOT / "lexicon/numerals-ordinals.toml"
SOURCE_SHA256 = "f826ec4815c3d60d6bb7c9365dc152a9c7a1a1da99b883a0b648e9da451fadc5"
MAX_INTEGER = 999_999_999
RULESETS = ("%%spellout-ordinal-compound", "%spellout-ordinal")


def escaped(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def project() -> str:
    raw = SOURCE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise SystemExit("CLDR 49 Tamil RBNF digest changed")
    rules_text = ET.fromstring(raw).find(
        './/rulesetGrouping[@type="SpelloutRules"]/rbnfRules'
    ).text.strip()
    selected = {name: [] for name in RULESETS}
    current = None
    for line in rules_text.splitlines():
        line = line.strip()
        if line.startswith("%") and line.endswith(":"):
            candidate = line[:-1]
            current = candidate if candidate in selected else None
            continue
        if current is None or not line:
            continue
        base_text, pattern = line.split(":", 1)
        if not base_text.isdigit():
            continue
        base = int(base_text)
        if base > MAX_INTEGER:
            continue
        pattern = pattern.strip().removesuffix(";")
        divisor = 10 ** (len(str(base)) - 1) if base else 1
        selected[current].append((base, divisor, pattern))

    if any(not selected[name] for name in RULESETS):
        raise SystemExit("missing required CLDR Tamil ordinal rules")
    lines = [
        "# CLDR 49 release-49/common/rbnf/ta.xml SpelloutRules; Unicode-3.0.",
        'profile = "numerals-ordinals-v1"',
        f"max_integer = {MAX_INTEGER}",
    ]
    for name in RULESETS:
        lines.extend(["", "[[rulesets]]", f"name = {escaped(name)}"])
        for base, divisor, pattern in selected[name]:
            lines.extend(
                [
                    "",
                    "[[rulesets.rules]]",
                    f"base = {base}",
                    f"divisor = {divisor}",
                    f"pattern = {escaped(pattern)}",
                ]
            )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="verify the canonical projection")
    mode.add_argument("--update", action="store_true", help="write the canonical projection")
    args = parser.parse_args()
    content = project()
    if args.update:
        OUTPUT.write_text(content, encoding="utf-8", newline="\n")
    elif args.check or not args.update:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("ordinal projection differs; inspect CLDR changes or use --update")
    print(f"{OUTPUT.relative_to(ROOT)}: projected {len(RULESETS)} rulesets")
