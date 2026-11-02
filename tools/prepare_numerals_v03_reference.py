"""Prepare pinned CLDR rules and deterministic input lists for ICU4J 79.1."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "tests/reference/numerals-v0.3"
ICU = ROOT / "target/numerals-reference/icu4j-79.1.jar"
ICU_SHA256 = "28b292e60d0d00c496bae88a15b2615f89f781be13670aeac9dc90f189570e07"
ROOT_SHA256 = "43fcb8dab6f1afa8c59be9eb6be9b6df0da45dc5cc91f6a3710cf2631e01ed2e"
TA_SHA256 = "f826ec4815c3d60d6bb7c9365dc152a9c7a1a1da99b883a0b648e9da451fadc5"


def boundary_values(maximum: int, boundaries: tuple[int, ...]) -> list[int]:
    values = set(range(1000))
    for boundary in boundaries:
        for offset in (-2, -1, 0, 1, 2, 9, 10, 11, 20, 99, 100):
            value = boundary + offset
            if 0 <= value <= maximum:
                values.add(value)
    return sorted(values)


def inputs():
    ordinal = boundary_values(
        999_999_999,
        (1000, 2000, 10_000, 100_000, 200_000, 10_000_000, 20_000_000,
         100_000_000, 999_999_999),
    )
    traditional = set(
        boundary_values(
            99_999_999,
            (1000, 2000, 10_000, 99_999, 100_000, 999_999, 1_000_000,
             1_000_001, 1_234_567, 99_999_999),
        )
    )
    traditional.update(-value for value in tuple(traditional) if value)
    return ordinal, sorted(traditional)


def rules(name: str, group: str) -> str:
    path = REFERENCE / name
    expected = ROOT_SHA256 if name == "root-rbnf.xml" else TA_SHA256
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise SystemExit("pinned CLDR RBNF digest changed: " + name)
    element = ET.fromstring(path.read_bytes())
    value = element.find(f'.//rulesetGrouping[@type="{group}"]/rbnfRules')
    if value is None or not value.text:
        raise SystemExit(f"CLDR RBNF group not found: {name} / {group}")
    return value.text.strip() + "\n"


def prepare():
    if hashlib.sha256(ICU.read_bytes()).hexdigest() != ICU_SHA256:
        raise SystemExit("pinned ICU4J 79.1 jar digest mismatch")
    ordinal, traditional = inputs()
    (REFERENCE / "ordinal-values.txt").write_text(
        "".join(f"{value}\n" for value in ordinal), encoding="ascii", newline="\n"
    )
    (REFERENCE / "traditional-values.txt").write_text(
        "".join(f"{value}\n" for value in traditional), encoding="ascii", newline="\n"
    )
    (REFERENCE / "root-numbering-rules.txt").write_text(
        rules("root-rbnf.xml", "NumberingSystemRules"), encoding="utf-8", newline="\n"
    )
    ta = rules("ta-rbnf.xml", "SpelloutRules")
    (REFERENCE / "ta-spellout-rules-tn.txt").write_text(ta, encoding="utf-8", newline="\n")
    old_profile = json.loads(
        (ROOT / "tests/reference/numerals-v0.1/profile.json").read_text(encoding="utf-8")
    )
    sl = ta.replace(old_profile["sl_lakh_from"], old_profile["sl_lakh_to"])
    (REFERENCE / "ta-spellout-rules-sl.txt").write_text(sl, encoding="utf-8", newline="\n")
    profile = {
        "profile": "numerals-v0.3",
        "cldr_version": "49",
        "unicode_version": "17.0.0",
        "max_decimal_bytes": 1024,
        "max_decimal_digits": 256,
        "max_decimal_scale": 256,
        "max_integer_words": 999_999_999,
        "max_currency_major": "999999999.99",
        "max_traditional_integer": 99_999_999,
        "traditional_zero": "U+0BE6",
        "traditional_negative": "U+2212",
        "ordinal_ruleset": "%spellout-ordinal",
        "traditional_rulesets": ["%tamil", "%%tamil-thousands"],
        "decimal_point_word": "",  # Filled from the pinned CLDR decimal rule below.
        "lakh_stem_from": old_profile["sl_lakh_from"],
        "lakh_stem_to": old_profile["sl_lakh_to"],
    }
    # The decimal marker is a CLDR literal, not a Tamil word inferred here.
    ta_rules = rules("ta-rbnf.xml", "SpelloutRules")
    numbering = ta_rules.split("%spellout-numbering:\n", 1)[1]
    decimal_rule = next(
        line.strip() for line in numbering.splitlines() if line.strip().startswith("x.x:")
    )
    marker = decimal_rule.split("<<", 1)[1].split(">>", 1)[0].strip()
    profile["decimal_point_word"] = marker
    (REFERENCE / "profile.json").write_text(
        json.dumps(profile, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


def reproduce():
    prepare()
    command = [
        "java", "-cp", str(ICU), str(ROOT / "tools/reference/NumeralsV03Reference.java"),
        str(REFERENCE / "root-numbering-rules.txt"),
        str(REFERENCE / "ta-spellout-rules-tn.txt"),
        str(REFERENCE / "ta-spellout-rules-sl.txt"),
        str(REFERENCE / "ordinal-values.txt"),
        str(REFERENCE / "traditional-values.txt"),
        str(REFERENCE / "icu-ordinals.jsonl"),
        str(REFERENCE / "icu-traditional.jsonl"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    write_manifest()


def write_manifest():
    upstream = {
        "root-rbnf.xml": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/rbnf/root.xml",
        "ta-rbnf.xml": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/rbnf/ta.xml",
        "numberingSystems.xml": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/supplemental/numberingSystems.xml",
        "UnicodeData-Tamil.txt": "https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt (Tamil-script projection)",
        "UnicodeData-fractions.txt": "https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt (Tamil digit/fraction projection)",
    }
    entries = []
    for path in sorted(REFERENCE.iterdir()):
        if path.name == "sources.json" or not path.is_file():
            continue
        entries.append(
            {
                "file": path.name,
                "source": upstream.get(path.name, "CLDR/Unicode projection or declared independent test domain"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    metadata = {
        "profile": "numerals-v0.3",
        "files": entries,
        "source_records": [
            {
                "id": "cldr-49-root-rbnf",
                "source": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/rbnf/root.xml",
                "version": "CLDR 49 release-49",
                "sha256": ROOT_SHA256,
                "license": "Unicode License v3; see ../unicode-17.0.0/LICENSE.txt",
                "inspection": "Full pinned XML parsed; NumberingSystemRules / %tamil and %%tamil-thousands projected by this script.",
            },
            {
                "id": "cldr-49-tamil-rbnf",
                "source": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/rbnf/ta.xml",
                "version": "CLDR 49 release-49",
                "sha256": TA_SHA256,
                "license": "Unicode License v3; see ../unicode-17.0.0/LICENSE.txt",
                "inspection": "Full pinned XML parsed; SpelloutRules projected for ordinals, Tamil decimal words, and existing TN/SL spellout profiles.",
            },
            {
                "id": "cldr-49-numbering-systems",
                "source": "https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/supplemental/numberingSystems.xml",
                "version": "CLDR 49 release-49",
                "sha256": "c5b9b208c6fe7bd3ce4e1c6cbb8f3337480aca620c9cf703ef3b6c74d4258c16",
                "license": "Unicode License v3; see ../unicode-17.0.0/LICENSE.txt",
                "inspection": "Pinned XML read for the taml algorithmic-system declaration and its RBNF alias.",
            },
            {
                "id": "unicode-17-ucd",
                "source": "https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt",
                "version": "Unicode 17.0.0 UCD",
                "sha256": "2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c",
                "projected_sha256": {
                    "UnicodeData-Tamil.txt": "79385cd202b825038270bb253b057d83bbaed5a67b776dcfe5cc84684ba9d059",
                    "UnicodeData-fractions.txt": "aaa7132a55eb2e1dbb7afb5afd0849d8f68f4b66be4dae65b6789f38a4a41476",
                },
                "license": "Unicode License v3; see ../unicode-17.0.0/LICENSE.txt",
                "inspection": "Full source digest pinned locally; Tamil block and Tamil Supplement records projected, including numeric values and names. The Kiizh modifier is explicitly not treated as a standalone rational.",
            },
        ],
        "derived_files": {
            "ordinal-values.txt": "Deterministic 0..999,999,999 boundary set, generated by prepare_numerals_v03_reference.py; not a copied upstream table.",
            "traditional-values.txt": "Deterministic signed boundary set inside CLDR root RBNF's 0..99,999,999 domain.",
            "root-numbering-rules.txt": "Exact NumberingSystemRules projection from pinned root-rbnf.xml.",
            "ta-spellout-rules-tn.txt": "Exact bounded SpelloutRules projection from pinned ta-rbnf.xml.",
            "ta-spellout-rules-sl.txt": "Tamil SpelloutRules plus only the already-declared SL lakh-stem substitution from numerals-v0.1/profile.json.",
            "icu-ordinals.jsonl": "ICU4J 79.1 outputs from custom pinned CLDR rule descriptions; oracle jar is test-generation-only and is not linked at runtime.",
            "icu-traditional.jsonl": "ICU4J 79.1 outputs from the pinned root rules; independent Python parser checks canonical round trips.",
        },
        "icu4j": {
            "version": "79.1",
            "url": "https://repo.maven.apache.org/maven2/com/ibm/icu/icu4j/79.1/icu4j-79.1.jar",
            "sha256": ICU_SHA256,
            "license": "Unicode License v3; oracle-only build/test reference, not distributed or linked at runtime.",
        },
        "license": "../unicode-17.0.0/LICENSE.txt (Unicode License v3)",
        "source_note": "Data projections retain Unicode License v3 attribution. ICU4J supplies expected spellout strings only; decimal-string, Gregorian, schema, and error expectations are independently generated by exact Python routines and reviewed literal cases.",
    }
    (REFERENCE / "sources.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reproduce", action="store_true", help="run pinned ICU4J reference")
    args = parser.parse_args()
    (reproduce if args.reproduce else prepare)()
    print("Prepared numerals-v0.3 pinned reference inputs")
