"""Synchronize distributable data/license copies; canonical sources stay at root."""

import argparse
from pathlib import Path
import re
try:
    from release_policy import ROOT, load, parse_version
except ModuleNotFoundError:
    from tools.release_policy import ROOT, load, parse_version

POLICY = load()
VERSION = POLICY["version"]
PUBLIC = tuple(POLICY["public_crates"])
RELEASE_RECORD = POLICY["record_name"]
INPUTS = {
    "tamil-core": ("core.toml",),
    "tamil-collate": ("collate.toml",),
    "tamil-numerals": (
        "numerals.toml",
        "numerals-formats.toml",
        "numerals-ordinals.toml",
        "numerals-symbols.toml",
        "numerals-traditional.toml",
        "calendar-vakya-solar.toml",
        "calendar-vakya-moon.toml",
        "calendar-vakya-civil.toml",
        "calendar-thirukanitham.toml",
        "calendar-solar-year-cycle.toml",
        "calendar-tamil-display.toml",
        "calendar-official-holidays.toml",
        "calendar-observances.toml",
    ),
    "tamil-calendar": (
        "calendar-vakya-solar.toml",
        "calendar-vakya-moon.toml",
        "calendar-vakya-civil.toml",
        "calendar-thirukanitham.toml",
        "calendar-solar-year-cycle.toml",
        "calendar-tamil-display.toml",
        "calendar-official-holidays.toml",
        "calendar-observances.toml",
    ),
    "tamil-codec": ("bamini.toml", "tscii.toml", "tab.toml", "tam.toml", "anjal.toml", "lt_tm.toml", "vanavil.toml"),
}
SUMMARIES = {
    "tamil-core": "Tailored UAX #29 letter segmentation, Mei/Uyir splitting, Tholkappiyam phonology (mora/Maathirai, cognates/Ina Ezhuthu), zero-allocation syllable nuclei (Olippasai), and Unicode inspection.",
    "tamil-norm": "NFC and NFD normalization for Tamil and mixed-script text, with joiners preserved.",
    "tamil-collate": "Versioned Mei-first Agara dictionary ordering and canonical sort/search keys.",
    "tamil-numerals": "Bounded TN/SL number words, exact decimal and INR/LKR strings, Unicode 17 symbols, traditional numerals, fractions, Gregorian civil arithmetic, bounded Thirukanitham and classical Vākyakaraṇa calendar profiles, selected TN observance rules, and official annual holiday schedules.",
    "tamil-calendar": "Tamil calendar systems, Thirukanitham, Vakiya, panchangam, and observances.",
    "tamil-codec": "Bamini conversion plus bounded TSCII, TAB, TAM, Anjal, LT-TM / IndoWord, and Vanavil profiles.",
    "tamil-toolkit": "Unified high-performance Rust entry point for Tamil text, Agara ordering, bounded exact numerals, Tholkappiyam phonology, Thirukanitham and classical Vākyakaraṇa profiles, selected TN observance rules, official annual holiday schedules, and legacy conversion APIs.",
}
FEATURE_TABLES = {
    "tamil-core": """| Area | Capabilities |
| --- | --- |
| **Segmentation** | Tailored Tamil grapheme clusters via `get_letters` or the borrowed `Letters` iterator (accurately preserving `க்ஷ` and `ஸ்ரீ`). |
| **Phonology** | Tholkappiyam mora metrics (`Maathirai`, `baseline_maathirai`), letter quantity classification (`is_kuril`, `is_nedil`, `is_mei`, `is_otru`, `is_aytham`), and homorganic cognates (`get_cognate`, `are_cognates`). |
| **Syllable Nuclei** | Zero-allocation orthographic syllable segmentation (`Olippasai`, `OlippasaiIter`) borrowing directly from input string slices. |
| **Normalization** | NFC/NFD canonical normalization and scalar-level inspection. |
| **Ezhuthu** | Mei/Uyir splitting and composition (`split_uyirmei`, `compose_uyirmei`). |""",
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
| **Exact strings** | Bounded decimal parse/format, percentages, mixed fractions, exact numeric ranges, and INR/LKR major-unit amounts without rounding. |
| **Symbols and traditional integers** | Unicode 17 Tamil numeric metadata and canonical CLDR traditional integer parse/format. |
| **Fractions and dates** | Rational fractions plus validated Gregorian parsing, weekday, arithmetic, differences, and intervals. |
| **Tamil calendar** | Bounded Thirukanitham Drik solar-date conversion and five-limb day/instant reports for the declared 2024–2027 TN/SL location ranges; a named Nava Panchangam/Tamil-rule TN subset for Puthandu, Pongal, Bhogi, Mattu Pongal and Amavasya/Pournami Aparahna selection with sunrise fallback; separately sourced annual holiday rows for TN 2025–26 and SL 2026–27. Vakiya and Sri Lanka observances are unsupported, and observance/calendar fixture suites remain planned. |
| **Historical calendar kernels** | Unreleased source-pinned 1962 Vakiya solar and lunar calculations, including a caller-input local-sunrise correction; calendar fixtures remain planned. |""",
    "tamil-calendar": """| Area | Capabilities |
| --- | --- |
| **Tamil calendar** | Bounded Thirukanitham Drik solar-date conversion and five-limb panchangam. |
| **Observances** | Tamil Nadu festival rules and official annual holiday schedules. |
| **Historical kernels** | Classical Vākyakaraṇa solar, lunar, and civil timekeeping algorithms. |""",
    "tamil-codec": """| Area | Capabilities |
| --- | --- |
| **Bamini** | Explicit Unicode conversion using the declared Bamini profile. |
| **Byte profiles** | Bounded TSCII, TAB, TAM, and Anjal conversion. |
| **LT-TM / IndoWord and Vanavil** | Selected 16-bit CID/code conversion in both directions. |
| **Limits** | No PDF parsing, automatic detection, or complete historical-font coverage. |""",
    "tamil-toolkit": """| Area | Capabilities |
| --- | --- |
| **Text & Phonology** | Unicode letter operations, normalization, inspection, Tholkappiyam mora (`Maathirai`), homorganic cognates (`Ina Ezhuthu`), and zero-allocation syllable nuclei (`Olippasai`). |
| **Ordering and numbers** | Agara sorting, Tamil number words, bounded exact numeric strings and currency amounts, symbol metadata, fractions, and Gregorian civil arithmetic. |
| **Tamil calendar** | Bounded Thirukanitham Drik conversion and panchangam reports, a named Nava Panchangam/Tamil-rule TN subset for solar festivals and Amavasya/Pournami Aparahna selection with sunrise fallback, and selected authority-published TN/SL annual holiday schedules; Vakiya and Sri Lanka observances are unsupported and calendar fixture suites remain planned. |
| **Historical calendar kernels** | Unreleased source-pinned 1962 Vakiya solar and lunar calculations; full Vakiya date/location/five-limb coverage is not implemented. |
| **Legacy conversion** | Bamini plus bounded TSCII, TAB, TAM, Anjal, LT-TM / IndoWord, and Vanavil profiles. |""",
}
CONTRACTS = {
    "tamil-core": "docs/specs/core-v0.1.md",
    "tamil-norm": "docs/specs/core-v0.1.md",
    "tamil-collate": "docs/specs/collate-v0.1.md",
    "tamil-numerals": "docs/specs/numerals-v0.3.md",
    "tamil-calendar": "docs/specs/calendar-year-cycle-v1.md",
    "tamil-codec": "docs/specs/codec-lt-tm.md",
    "tamil-toolkit": "README.md#capability-contracts",
}
UNRELEASED_NOTES = {
    name: (
        "This candidate includes owner-approved numerals v0.3 and experimental, bounded calendar APIs. "
        "Calendar acceptance suites remain planned and their selected review runs are separate from active numeral parity. "
        "Thirukanitham, Ujjain mean-sunrise Vakiya, named TN observances and annual holiday snapshots have explicit coverage. "
        "Arbitrary-location Vakiya daylight, official era reconciliation and Krishna Jayanthi remain deferred. "
        "See docs/releases/numerals-calendar-candidate.md for scope and limitations."
    ) for name in ("tamil-numerals", "tamil-toolkit")
}
EXAMPLES = {
    "tamil-core": '''use tamil_core::{are_cognates, baseline_maathirai, get_letters, Letters};

fn main() {
    let text = "தமிழ்";
    println!("{}", get_letters(text).join(" | "));
    assert_eq!(Letters::new(text).count(), 3);
    assert_eq!(baseline_maathirai("த").as_fraction(), (1, 1)); // 1.0 mora (Kuril)
    assert_eq!(baseline_maathirai("ழ்").as_fraction(), (1, 2)); // 0.5 mora (Mei)
    assert!(are_cognates("க்", "ங்"));
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
    "tamil-calendar": '''use tamil_calendar::tamil_year_cycle_info;

fn main() -> Result<(), String> {
    let year = tamil_year_cycle_info(2026, 1)?;
    println!("{}: {}", year.cycle_number, year.tamil);
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
    "tamil-toolkit": '''use tamil_toolkit::{codec, core, numerals};

fn main() -> Result<(), String> {
    let text = "தமிழ்";
    println!("{}", core::get_letters(text).join(" | "));
    println!("{}", codec::unicode_to_bamini(text)?);
    let codes = codec::unicode_to_lt_tm_codes(text)?;
    println!("{:?} -> {}", codes, codec::lt_tm_codes_to_unicode(&codes, codec::ErrorPolicy::Strict)?);
    let amount = numerals::parse_decimal("123.45", "latin", "none", false)?;
    println!("{}", numerals::format_currency_decimal(&amount, numerals::Currency::LKR, numerals::Locale::SL)?);
    Ok(())
}''',
}


def sync_root_readme(text, policy):
    v = policy["version"]
    pv = policy["python_version"]
    tag = policy["npm_tag"]
    rec = policy["record_name"]
    lbl = policy["label"]
    text = re.sub(r'(\| \*\*Rust 1\.85\+\*\* \| `cargo add tamil-toolkit@=)[^`]+(` \|)', rf'\g<1>{v}\g<2>', text)
    text = re.sub(r'(\| \*\*Python 3\.11\+\*\* \| `python -m pip install tamil-toolkit==)[^`]+(` \|)', rf'\g<1>{pv}\g<2>', text)
    text = re.sub(r'(\| \*\*Node\.js 22\+ / browsers\*\* \| `npm install tamil-toolkit@)[^`]+(` \|)', rf'\g<1>{tag}\g<2>', text)
    text = re.sub(r'(\| SDK \| Install )[^\|]+( \| Version \| Downloads \|)', rf'\g<1>{lbl}\g<2>', text)
    text = re.sub(r'(npm[’\']s `)[^`]+(` tag points to )[^;]+(;)', rf'\g<1>{tag}\g<2>{lbl}\g<3>', text)
    text = re.sub(r'(All six Rust crates are published at `)[^`]+(`:)', rf'\g<1>{v}\g<2>', text)
    text = re.sub(r'https://docs\.rs/tamil-toolkit/[^/]+/tamil_toolkit/', f'https://docs.rs/tamil-toolkit/{v}/tamil_toolkit/', text)
    text = re.sub(r'\[[^\]]+ compatibility details\]\(docs/releases/[^)]+\.md#compatibility-and-scope\)',
                  f'[{lbl} compatibility details](docs/releases/{rec}.md#compatibility-and-scope)', text)
    text = re.sub(r'(\| Published package list and release record \| \[Release policy\]\(docs/releases/policy\.md#what-can-ship\) · )\[[^\]]+\]\(docs/releases/[^)]+\.md\)( \|)',
                  rf'\g<1>[{lbl}](docs/releases/{rec}.md)\g<2>', text)
    text = re.sub(r'· \[[^\]]+ scope\]\(docs/releases/[^)]+\.md#compatibility-and-scope\)',
                  f'· [{lbl} scope](docs/releases/{rec}.md#compatibility-and-scope)', text)
    return text


def sync_python_readme(text, policy):
    pv = policy["python_version"]
    rec = policy["record_name"]
    lbl = policy["label"]
    title = lbl.title()
    text = re.sub(r'python -m pip install tamil-toolkit==\S+', f'python -m pip install tamil-toolkit=={pv}', text)
    text = re.sub(r'## (?:Alpha|Beta|Rc|\d+)[^\n]* scope', f'## {title} scope', text)
    text = re.sub(r'(The PyPI `)[^`]+(` package includes)', rf'\g<1>{pv}\g<2>', text)
    text = re.sub(r'https://github\.com/abishtakan/tamil-toolkit/blob/master/docs/releases/[^/)]+\.md#compatibility-and-scope',
                  f'https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/{rec}.md#compatibility-and-scope', text)
    text = re.sub(r'See the \[[^\]]+\]\(https://github\.com/abishtakan/tamil-toolkit/blob/master/docs/releases/[^/)]+\.md\)',
                  f'See the [{lbl} release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/{rec}.md)', text)
    return text


def sync_js_readme(text, policy):
    v = policy["version"]
    tag = policy["npm_tag"]
    rec = policy["record_name"]
    lbl = policy["label"]
    title = lbl.title()
    text = re.sub(r'(Install )[^f]+( from npm[’\']s `)[^`]+(` dist-tag:)', rf'\g<1>{lbl}\g<2>{tag}\g<3>', text)
    text = re.sub(r'npm install tamil-toolkit@\S+', f'npm install tamil-toolkit@{tag}', text)
    text = re.sub(r'(The `)[^`]+(` tag points to `)[^`]+(`;)', rf'\g<1>{tag}\g<2>{v}\g<3>', text)
    text = re.sub(r'## (?:Alpha|Beta|Rc|\d+)[^\n]* scope', f'## {title} scope', text)
    text = re.sub(r'(The npm `)[^`]+(` package includes)', rf'\g<1>{v}\g<2>', text)
    text = re.sub(r'https://github\.com/abishtakan/tamil-toolkit/blob/master/docs/releases/[^/)]+\.md#compatibility-and-scope',
                  f'https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/{rec}.md#compatibility-and-scope', text)
    return text


def notices(root=ROOT):
    text = """# Third-party notices

Original tamil-toolkit code is MIT licensed. The following upstream data and
mapping notices retain their original terms; the project MIT license does not
replace them. Generated lexicon copies are checked against the canonical data.

Unicode 17 and CLDR 49 data: https://www.unicode.org/ and https://cldr.unicode.org/
Bamini mapping sources: https://github.com/ag-sanjjeev/app-tamil-fonts-unicode-converter
and https://github.com/Pakeetharan/unicode-bamini-converter
TSCII mapping source: https://github.com/mayooresan/Android-TamilUtil
LT-TM and Vanavil mapping references: Azhagi+ Portable configurations; source
digests and scope are recorded in docs/specs/codec-lt-tm.md and
docs/specs/codec-vanavil.md. Their bundled terms remain applicable to the
derived mapping tables.
Tamil calendar display labels are extracted as short factual name lists from
Tamil Virtual Academy's educational page; its reuse terms were not stated, so
no license or permission is asserted and no prose or page/table image is copied.
Tamil Gregorian weekday labels are from CLDR 49 under Unicode data terms.
The Latin transliterations of the seven weekday names are from Vidya Mohan and
Rajiv Ranjan, *Basic Tamil* (2024), chapter 6.1, under CC BY-NC 4.0; attribution
and the noncommercial condition remain applicable. No images or surrounding
text from the book are included.
Historical Vakyakarana solar-transit, Bhupadi correction, and Candra-vakya
values are transcribed as mathematical facts from *Vakyakarana with
Sundararaja's Laghuprakashika*, eds. T. S. Kuppanna Sastri and K. V. Sarma,
1962, printed English translation pp. 251-253 and Appendix II pp. 125-134.
No source prose or scan images are included; the publication's redistribution
terms were not established. See docs/specs/calendar-vakya-solar-v1.md and
docs/specs/calendar-vakya-moon-v1.md before redistributing this data.
The Ujjain mean-sunrise civil profile uses the same 1962 source, Bag (2001)
for the Kali epoch's Gregorian equivalence, Pai (2019) as an independent
transit-method cross-check, and IMD station metadata. It does not include
source prose or page images; see docs/specs/calendar-vakya-civil-v1.md. The
1962 source's redistribution terms remain unresolved.
The Thirukanitham Drik profile depends on Rust `astro` 2.0.0 by Saurav
Sachidanand, distributed under the MIT license; its complete upstream license
text is copied below. GeoNames city-point coordinates are attributed to
GeoNames and used under CC BY 4.0. Drik Panchang, IMD, and Nava Panchangam
provide factual date and rule witnesses in planned calendar suites. The named
Nava observance subset records its published Aparahna-then-sunrise selection
rule and factual annual dates; Nava's annual tithi pages use Vakyakarana, so
their match to Thirukanitham is not a publisher-equivalence claim. Reuse terms
for these page tables are not established, and no source page or markup is
copied. Exact sources, locators, coverage, and retained-page digests are in
lexicon/calendar-observances.toml and docs/specs/calendar-observances-v1.md.
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
        ("astro 2.0.0 by Saurav Sachidanand (MIT)", "tests/reference/calendar-thirukanitham-v1/astro-LICENSE.md"),
    ):
        text += f"## {title}\n\n```text\n{(root / source).read_text(encoding='utf-8').strip()}\n```\n\n"
    return text.encode("utf-8")


def expected_files(root=ROOT):
    policy = load(root)
    version = policy["version"]
    public = tuple(policy["public_crates"])
    release_record = policy["record_name"]
    files = {}

    if (root / "LICENSE").is_file():
        license_bytes = (root / "LICENSE").read_bytes()
        destinations = [root / "crates" / name for name in public]
        destinations += [root / "bindings" / name for name in ("python", "js-wasm", "dart-flutter")]
        for destination in destinations:
            files[destination / "LICENSE"] = license_bytes

    if all((root / source).is_file() for source in (
        "tests/reference/unicode-17.0.0/LICENSE.txt",
        "tests/reference/codec-v0.1/LICENSE-ag.txt",
        "tests/reference/codec-v0.1/LICENSE-pakeetharan.txt",
        "tests/reference/codec-tscii/LICENSE.txt",
        "tests/reference/calendar-thirukanitham-v1/astro-LICENSE.md",
    )):
        notice = notices(root)
        files[root / "THIRD_PARTY_NOTICES.md"] = notice
        destinations = [root / "crates" / name for name in public]
        destinations += [root / "bindings" / name for name in ("python", "js-wasm", "dart-flutter")]
        for destination in destinations:
            files[destination / "THIRD_PARTY_NOTICES.md"] = notice

    for name in public:
        label = "Release" if policy["channel"] == "stable" else "Experimental " + policy["channel"]
        stability = ("Public APIs follow semantic versioning." if policy["channel"] == "stable"
                     else "APIs may change before stability.")
        contract_url = f"https://github.com/abishtakan/tamil-toolkit/blob/master/{CONTRACTS[name]}"
        record_title = f"{policy['channel'].title()} release record"
        unreleased_note = UNRELEASED_NOTES.get(name, "")
        if unreleased_note:
            unreleased_note = " " + unreleased_note
        text = f"""<div align="center">

# {name}

**{SUMMARIES[name]}**

[![crates.io version](https://img.shields.io/crates/v/{name}?style=flat-square)](https://crates.io/crates/{name})
[![crates.io downloads](https://img.shields.io/crates/d/{name}?style=flat-square&label=downloads)](https://crates.io/crates/{name})
[![docs.rs](https://docs.rs/{name}/badge.svg)](https://docs.rs/{name}/{version})
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

{FEATURE_TABLES[name]}

{label} `{version}`. {stability} This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.{unreleased_note}

## Install

```sh
cargo add {name}@={version}
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
{name} = \"={version}\"
```

## Example

```rust
{EXAMPLES[name]}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/{name}/{version})
- [Feature contract and examples]({contract_url})
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [{record_title}](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/{release_record}.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
"""
        files[root / "crates" / name / "README.md"] = text.encode("utf-8")

    if (root / "lexicon").is_dir():
        for name, inputs in INPUTS.items():
            for filename in inputs:
                lex_file = root / "lexicon" / filename
                if lex_file.is_file():
                    files[root / "crates" / name / "lexicon" / filename] = lex_file.read_bytes()

    for readme_path, sync_fn in (
        (root / "README.md", sync_root_readme),
        (root / "bindings/python/README.md", sync_python_readme),
        (root / "bindings/js-wasm/README.md", sync_js_readme),
    ):
        if readme_path.is_file():
            content = readme_path.read_text(encoding="utf-8")
            synced = sync_fn(content, policy)
            files[readme_path] = synced.encode("utf-8")

    return files


def sync(root=ROOT, check=False):
    stale = []
    files = expected_files(root)
    for path, expected in files.items():
        if path.is_file() and path.read_bytes() == expected:
            continue
        stale.append(str(path.relative_to(root)))
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if check and stale:
        raise ValueError("Stale release copies; run just sync-release-files: " + ", ".join(stale))
    print(f"Release source copies {'verified' if check else 'synchronized'} ({len(files)} files).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    sync(root=args.root, check=args.check)
