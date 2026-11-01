"""Synchronize distributable data/license copies; canonical sources stay at root."""

import argparse
from release_policy import ROOT, load

POLICY = load()
VERSION = POLICY["version"]
PUBLIC = tuple(POLICY["public_crates"])
RELEASE_RECORD = "alpha-" + VERSION.rsplit("alpha.", 1)[1]
INPUTS = {
    "tamil-core": ("core.toml",),
    "tamil-collate": ("collate.toml",),
    "tamil-numerals": ("numerals.toml", "numerals-formats.toml"),
    "tamil-codec": ("bamini.toml", "tscii.toml", "tab.toml", "tam.toml", "anjal.toml", "lt_tm.toml"),
}
SUMMARIES = {
    "tamil-core": "Unicode normalization, tailored Ezhuthu iteration, Mei/Uyir composition and scalar inspection.",
    "tamil-norm": "NFC and NFD normalization for Tamil and mixed-script text, with joiners preserved.",
    "tamil-collate": "Versioned Mei-first Agara dictionary ordering and canonical sort/search keys.",
    "tamil-numerals": "Bounded TN/SL integers, exact INR/LKR amounts, rational fractions and Gregorian date formatting.",
    "tamil-codec": "Bamini conversion plus bounded TSCII, TAB, TAM, Anjal, and LT-TM / IndoWord profiles.",
    "tamil-toolkit": "Unified Rust entry point for published Tamil text, ordering, numerals, and bounded legacy conversion APIs.",
}
FEATURE_TABLES = {
    "tamil-core": """| Area | Capabilities |
| --- | --- |
| **Segmentation** | Tailored Tamil letter clusters via `get_letters` or the borrowed `Letters` iterator. |
| **Normalization** | NFC/NFD normalization and scalar-level inspection. |
| **Ezhuthu** | Mei/Uyir splitting and composition. |""",
    "tamil-norm": """| Operation | Behavior |
| --- | --- |
| **NFC/NFD** | Canonical Unicode normalization for Tamil and mixed-script text. |
| **Preservation** | Non-Tamil text and ZWJ/ZWNJ joiners are retained. |""",
    "tamil-collate": """| Area | Capabilities |
| --- | --- |
| **Ordering** | Stable Mei-first `agara-v1` comparison and sorting. |
| **Keys** | Versioned numeric sort keys and canonical exact-match search keys. |""",
    "tamil-numerals": """| Area | Capabilities |
| --- | --- |
| **Number words** | Bounded formal Tamil Nadu and Sri Lankan profiles. |
| **Money** | Exact INR/LKR minor-unit amounts with no rounding. |
| **Fractions and dates** | Rational fractions and Gregorian civil-date formatting. |""",
    "tamil-codec": """| Area | Capabilities |
| --- | --- |
| **Bamini** | Explicit Unicode conversion using the declared Bamini profile. |
| **Byte profiles** | Bounded TSCII, TAB, TAM, and Anjal conversion. |
| **LT-TM / IndoWord** | Selected 16-bit CID/code conversion in both directions. |
| **Limits** | No PDF parsing, automatic detection, or complete historical-font coverage. |""",
    "tamil-toolkit": """| Area | Capabilities |
| --- | --- |
| **Text** | Unicode letter operations, normalization, and inspection. |
| **Ordering and numbers** | Agara sorting, number words, exact amounts, fractions, and dates. |
| **Legacy conversion** | Bamini plus bounded TSCII, TAB, TAM, Anjal, and LT-TM / IndoWord profiles. |""",
}
CONTRACTS = {
    "tamil-core": "docs/specs/core-v0.1.md",
    "tamil-norm": "docs/specs/core-v0.1.md",
    "tamil-collate": "docs/specs/collate-v0.1.md",
    "tamil-numerals": "docs/specs/numerals-v0.2.md",
    "tamil-codec": "docs/specs/codec-lt-tm.md",
    "tamil-toolkit": "README.md#capability-contracts",
}
EXAMPLES = {
    "tamil-core": '''use tamil_core::{get_letters, Letters};

fn main() {
    let text = "தமிழ்";
    println!("{}", get_letters(text).join(" | "));
    assert_eq!(Letters::new(text).count(), 3);
}''',
    "tamil-norm": '''fn main() {
    let decomposed = tamil_norm::normalize_nfd("தமிழ்");
    let normalized = tamil_norm::normalize_nfc(&decomposed);
    println!("{normalized}");
}''',
    "tamil-collate": '''fn main() {
    let words = vec!["ஆ".to_owned(), "அ".to_owned()];
    let sorted = tamil_collate::sort_words(&words);
    println!("{}", sorted.join(" | "));
}''',
    "tamil-numerals": '''use tamil_numerals::{Currency, Locale};

fn main() -> Result<(), String> {
    let amount = tamil_numerals::format_currency(102_550, Currency::LKR, Locale::SL)?;
    println!("{amount}");
    Ok(())
}''',
    "tamil-codec": '''use tamil_codec::{bamini_to_unicode, lt_tm_codes_to_unicode, unicode_to_bamini, unicode_to_lt_tm_codes, ErrorPolicy};

fn main() -> Result<(), String> {
    let legacy = unicode_to_bamini("தமிழ்")?;
    let text = bamini_to_unicode(&legacy, ErrorPolicy::Strict)?;
    println!("{legacy} -> {text}");

    let codes = unicode_to_lt_tm_codes("தமிழ்")?;
    let decoded = lt_tm_codes_to_unicode(&codes, ErrorPolicy::Strict)?;
    println!("{codes:?} -> {decoded}");
    Ok(())
}''',
    "tamil-toolkit": '''use tamil_toolkit::{codec, core};

fn main() -> Result<(), String> {
    let text = "தமிழ்";
    println!("{}", core::get_letters(text).join(" | "));
    println!("{}", codec::unicode_to_bamini(text)?);
    let codes = codec::unicode_to_lt_tm_codes(text)?;
    println!("{:?} -> {}", codes, codec::lt_tm_codes_to_unicode(&codes, codec::ErrorPolicy::Strict)?);
    Ok(())
}''',
}


def notices():
    text = """# Third-party notices

Original tamil-toolkit code is MIT licensed. The following upstream data and
mapping notices retain their original terms; the project MIT license does not
replace them. Generated lexicon copies are checked against the canonical data.

Unicode 17 and CLDR 49 data: https://www.unicode.org/ and https://cldr.unicode.org/
Bamini mapping sources: https://github.com/ag-sanjjeev/app-tamil-fonts-unicode-converter
and https://github.com/Pakeetharan/unicode-bamini-converter
TSCII mapping source: https://github.com/mayooresan/Android-TamilUtil
LT-TM mapping reference: Azhagi+ Portable configuration; source digest and
scope are recorded in docs/specs/codec-lt-tm.md. Its bundled terms remain
applicable to the derived mapping table.
Exact sources, revisions, digests and profile limits are recorded at:
https://github.com/abishtakan/tamil-toolkit/tree/HEAD/tests/reference
and https://github.com/abishtakan/tamil-toolkit/tree/HEAD/docs/specs

Binary distributions also include THIRD_PARTY_LICENSES.txt, generated from the
locked Rust dependency graph with the complete upstream license texts.

"""
    for title, source in (
        ("Unicode License V3", "tests/reference/unicode-17.0.0/LICENSE.txt"),
        ("ag-sanjjeev Bamini source (MIT)", "tests/reference/codec-v0.1/LICENSE-ag.txt"),
        ("Pakeetharan Balasubramaniam Bamini reference (MIT)", "tests/reference/codec-v0.1/LICENSE-pakeetharan.txt"),
        ("Jay Mayu Android TamilUtil reference (MIT)", "tests/reference/codec-tscii/LICENSE.txt"),
    ):
        text += f"## {title}\n\n```text\n{(ROOT / source).read_text(encoding='utf-8').strip()}\n```\n\n"
    return text.encode("utf-8")


def expected_files():
    notice = notices()
    files = {ROOT / "THIRD_PARTY_NOTICES.md": notice}
    license_bytes = (ROOT / "LICENSE").read_bytes()
    destinations = [ROOT / "crates" / name for name in PUBLIC]
    destinations += [ROOT / "bindings" / name for name in ("python", "js-wasm", "dart-flutter")]
    for destination in destinations:
        files[destination / "LICENSE"] = license_bytes
        files[destination / "THIRD_PARTY_NOTICES.md"] = notice
    for name in PUBLIC:
        label = "Release" if POLICY["channel"] == "stable" else "Experimental " + POLICY["channel"]
        stability = ("Public APIs follow semantic versioning." if POLICY["channel"] == "stable"
                     else "APIs may change before stability.")
        contract_url = f"https://github.com/abishtakan/tamil-toolkit/blob/master/{CONTRACTS[name]}"
        text = f"""<div align="center">

# {name}

**{SUMMARIES[name]}**

[![crates.io version](https://img.shields.io/crates/v/{name}?style=flat-square)](https://crates.io/crates/{name})
[![crates.io downloads](https://img.shields.io/crates/d/{name}?style=flat-square&label=downloads)](https://crates.io/crates/{name})
[![docs.rs](https://docs.rs/{name}/badge.svg)](https://docs.rs/{name}/{VERSION})
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

{FEATURE_TABLES[name]}

{label} `{VERSION}`. {stability} This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add {name}@={VERSION}
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
{name} = \"={VERSION}\"
```

## Example

```rust
{EXAMPLES[name]}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/{name}/{VERSION})
- [Feature contract and examples]({contract_url})
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/{RELEASE_RECORD}.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
"""
        files[ROOT / "crates" / name / "README.md"] = text.encode("utf-8")
    for name, inputs in INPUTS.items():
        for filename in inputs:
            files[ROOT / "crates" / name / "lexicon" / filename] = (ROOT / "lexicon" / filename).read_bytes()
    return files


def sync(check=False):
    stale = []
    for path, expected in expected_files().items():
        if path.is_file() and path.read_bytes() == expected:
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if check and stale:
        raise ValueError("Stale release copies; run just sync-release-files: " + ", ".join(stale))
    print(f"Release source copies {'verified' if check else 'synchronized'} ({len(expected_files())} files).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    sync(parser.parse_args().check)
