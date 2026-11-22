"""Synchronize distributable data/license copies; canonical sources stay at root."""

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tomllib
try:
    from release_policy import ROOT, load, parse_version
except ModuleNotFoundError:
    from tools.release_policy import ROOT, load, parse_version

POLICY = load()
VERSION = POLICY["version"]
PUBLIC = tuple(POLICY["public_crates"])
RELEASE_RECORD = POLICY["record_name"]
DICTIONARY_FILES = (
    "ATTRIBUTION_AND_TERMS.md",
    "assertions.csv",
    "decisions.csv",
    "entries.csv",
    "evidence.csv",
    "forms.csv",
    "identities.csv",
    "labels.csv",
    "notices/ATTRIBUTION_AND_LICENSE.md",
    "notices/CC-BY-SA-4.0.md",
    "pack_members.csv",
    "packs.toml",
    "relations.csv",
    "schema.toml",
    "scopes.csv",
    "senses.csv",
    "sources.csv",
    "texts.csv",
    "unicode_exceptions.csv",
    "vocabularies.toml",
)
DICTIONARY_SCHEMAS = (
    "common.schema.json",
    "intake.schema.json",
    "lexical.schema.json",
    "review.schema.json",
)
DICTIONARY_NOTICE_FILES = (
    "ATTRIBUTION_AND_TERMS.md",
    "notices/ATTRIBUTION_AND_LICENSE.md",
    "notices/CC-BY-SA-4.0.md",
)
DICTIONARY_PACK_PROFILES = {
    "core": {
        "pack_id": "core",
        "spdx": "CC-BY-SA-4.0",
        "source_dir": "lexicon/dictionary",
        "notice_files": tuple(f"lexicon/dictionary/{rel}" for rel in DICTIONARY_NOTICE_FILES),
    },
    "names_taxa": {
        "pack_id": "names_taxa",
        "spdx": "CC-BY-SA-4.0",
        "source_dir": "lexicon/packs/names_taxa",
        "notice_files": tuple(f"lexicon/packs/names_taxa/{rel}" for rel in DICTIONARY_NOTICE_FILES),
    },
    "regional": {
        "pack_id": "regional",
        "spdx": "CC-BY-SA-4.0",
        "source_dir": "lexicon/packs/regional",
        "notice_files": tuple(f"lexicon/packs/regional/{rel}" for rel in DICTIONARY_NOTICE_FILES),
    },
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INPUTS = {
    "tamil-core": ("core.toml",),
    "tamil-collate": ("collate.toml", "collate_uyirmei_first.toml"),
    "tamil-numerals": (
        "numerals.toml",
        "numerals-formats.toml",
        "numerals-ordinals.toml",
        "numerals-symbols.toml",
        "numerals-traditional.toml",
        "numerals-v04.toml",
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
    "tamil-codec": (
        "bamini.toml",
        "tscii.toml",
        "tab.toml",
        "tam.toml",
        "anjal.toml",
        "lt_tm.toml",
        "vanavil.toml",
        "senthamil.toml",
        "shree_tam.toml",
        "softview.toml",
        "tbo.toml",
        "braille.toml",
    ),
    "tamil-translit": ("translit.toml",),
}
SUMMARIES = {
    "tamil-core": "Tailored UAX #29 letter segmentation, Mei/Uyir splitting, Tholkappiyam phonology (mora/Maathirai, cognates/Ina Ezhuthu), zero-allocation syllable nuclei (Olippasai), and Unicode inspection.",
    "tamil-norm": "NFC and NFD normalization for Tamil and mixed-script text, with joiners preserved.",
    "tamil-collate": "Versioned Mei-first Agara dictionary ordering and canonical sort/search keys.",
    "tamil-numerals": "Bounded TN/SL number words, exact decimal and INR/LKR strings, Unicode 17 symbols, traditional numerals, fractions, Gregorian civil arithmetic, bounded Thirukanitham and classical Vākyakaraṇa calendar profiles, selected TN observance rules, and official annual holiday schedules.",
    "tamil-calendar": "Tamil calendar systems, Thirukanitham, Vakiya, panchangam, and observances.",
    "tamil-codec": "Bamini conversion plus bounded TSCII, TAB, TAM, Anjal, LT-TM / IndoWord, and Vanavil profiles.",
    "tamil-hyphen": "Syllable breakdown, prosodic Asai segmentation, soft hyphenation, and publication-grade line wrapping.",
    "tamil-translit": "Lossless Tamil orthographic romanization (ISO 15919, Madras Lexicon, ITRANS, Harvard-Kyoto) and deterministic offline input (Tamil99, Anjal phonetic, Suratha Bamini, Phonetic v1).",
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
    "tamil-hyphen": """| Area | Capabilities |
| --- | --- |
| **Syllable breakdown** | Orthographic syllable and prosodic *Asai* segment partitioning (`hyphenate_word`, `hyphenation_points`). |
| **Text Hyphenation** | Full paragraph soft hyphenation preserving punctuation, whitespace, and non-Tamil runs (`hyphenate_text`). |
| **Line Wrapping** | Publication-grade line wrapping with customizable margins and delimiters (`wrap_text`). |
| **OpenXML & Dictionaries** | Batch OOXML Word document processing (`process_docx_file`), Frank Liang dictionary export (`export_dic_file`), and LibreOffice extension bundling (`package_oxt`). |""",
    "tamil-translit": """| Area | Capabilities |
| --- | --- |
| **Scholarly Romanization** | Lossless bidirectional ISO 15919, Madras Lexicon, ITRANS, and Harvard-Kyoto transliteration (`transliterate`). |
| **Offline Input** | Deterministic Tamil99, Anjal phonetic, Suratha Bamini, and rule-based Phonetic/Tanglish v1 input (`transliterate`). |""",
}
CONTRACTS = {
    "tamil-core": "docs/specs/core-v0.1.md",
    "tamil-norm": "docs/specs/core-v0.1.md",
    "tamil-collate": "docs/specs/collate-v0.1.md",
    "tamil-numerals": "docs/specs/numerals-v0.3.md",
    "tamil-calendar": "docs/specs/calendar-year-cycle-v1.md",
    "tamil-codec": "docs/specs/codec-lt-tm.md",
    "tamil-hyphen": "docs/specs/hyphen-v0.1.md",
    "tamil-translit": "docs/specs/translit-v0.1.md",
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
    "tamil-hyphen": '''use tamil_hyphen::{hyphenate_word, HyphenationConfig};

fn main() -> Result<(), String> {
    let word = "\u0baa\u0bb2\u0bcd\u0b95\u0bb2\u0bc8\u0b95\u0bcd\u0b95\u0bb4\u0b95\u0bae\u0bcd";
    let config = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 3,
        right_min: 3,
    };
    let result = hyphenate_word(word, Some(&config))?;
    println!("{} -> {}", result.original, result.hyphenated);
    Ok(())
}''',
    "tamil-translit": '''use tamil_translit::{transliterate, Direction, Scheme};

fn main() -> Result<(), String> {
    let roman = transliterate("தமிழ்", Scheme::Iso15919, Direction::ToLatin)?;
    let back = transliterate(&roman, Scheme::Iso15919, Direction::ToTamil)?;
    println!("{roman} -> {back}");
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


def _safe_relative_posix(rel: str) -> PurePosixPath:
    """Validate that a manifest-declared relative POSIX path cannot traverse upward."""
    if not isinstance(rel, str) or not rel or "\\" in rel or rel.startswith("/"):
        raise ValueError(f"Unsafe canonical file path: {rel!r}")
    pure = PurePosixPath(rel)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError(f"Unsafe canonical path traversal component: {rel!r}")
    return pure


def _assert_no_symlinks(directory: Path) -> None:
    if directory.is_symlink():
        raise ValueError(f"Symlink directory is not permitted in release tree: {directory}")
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlink is not permitted in release tree: {path}")


def _validate_canonical_with_lexicon_packs(lex_dict: Path) -> None:
    """Run tools.lexicon_packs.validate_canonical_dir when present in this repo."""
    repo_with_tools = Path(__file__).resolve().parents[1]
    if not (repo_with_tools / "tools/lexicon_packs.py").is_file():
        return
    added = False
    repo_str = str(repo_with_tools)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)
        added = True
    try:
        from tools.lexicon_packs import validate_canonical_dir
    finally:
        if added and repo_str in sys.path:
            sys.path.remove(repo_str)
    findings = validate_canonical_dir(lex_dict)
    if findings:
        raise ValueError(
            "Canonical dictionary validation failed: " + "; ".join(findings[:5])
        )


def _validate_single_dictionary_pack(root: Path, pack_id: str, expected_set: set[str]) -> dict:
    """Validate one canonical dictionary pack directory, manifest hashes, notices, and sources."""
    cfg = DICTIONARY_PACK_PROFILES[pack_id]
    source_dir_rel = cfg["source_dir"]
    pack_dir = root / source_dir_rel
    if not pack_dir.is_dir() or pack_dir.is_symlink():
        raise ValueError(f"Missing or invalid canonical dictionary directory: {pack_dir}")
    _assert_no_symlinks(pack_dir)

    actual_files = {
        path.relative_to(pack_dir).as_posix()
        for path in pack_dir.rglob("*")
        if path.is_file()
    }
    missing = sorted(expected_set - actual_files)
    extra = sorted(actual_files - expected_set)
    if missing or extra:
        details = []
        if missing:
            details.append("missing=" + ", ".join(missing))
        if extra:
            details.append("unexpected=" + ", ".join(extra))
        raise ValueError(
            f"Canonical {source_dir_rel} file set mismatch (" + "; ".join(details) + ")"
        )

    packs_path = pack_dir / "packs.toml"
    packs = tomllib.loads(packs_path.read_text(encoding="utf-8"))
    if (
        packs.get("schema_version") != 1
        or packs.get("pack_id") != pack_id
        or packs.get("l3_pack_eligible") is not True
        or packs.get("l2_structural_accepted") is not False
        or not isinstance(packs.get("dataset_version"), str)
        or not packs.get("dataset_version")
    ):
        raise ValueError(f"{source_dir_rel}/packs.toml release eligibility metadata is invalid or not L3 approved")

    manifest_sha = packs.get("manifest_sha256", "")
    if not isinstance(manifest_sha, str) or not _SHA256_RE.fullmatch(manifest_sha):
        raise ValueError(f"{source_dir_rel}/packs.toml has invalid manifest_sha256: {manifest_sha!r}")

    declared_entries = packs.get("files")
    if not isinstance(declared_entries, list):
        raise ValueError(f"{source_dir_rel}/packs.toml must contain [[files]] entries")
    declared_paths = set()
    digest_basis = []
    for entry in sorted(declared_entries, key=lambda item: str(item.get("path", ""))):
        rel = entry.get("path", "")
        _safe_relative_posix(rel)
        if rel not in expected_set or rel == "packs.toml":
            raise ValueError(f"{source_dir_rel}/packs.toml declares unapproved or non-manifest path: {rel!r}")
        if rel in declared_paths:
            raise ValueError(f"{source_dir_rel}/packs.toml duplicates file entry: {rel!r}")
        declared_paths.add(rel)
        data = (pack_dir / rel).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if sha != entry.get("sha256") or len(data) != entry.get("bytes"):
            raise ValueError(f"{source_dir_rel}/packs.toml digest or byte count mismatch for {rel}")
        digest_basis.append({"path": rel, "sha256": sha, "bytes": len(data)})

    if declared_paths != (expected_set - {"packs.toml"}):
        raise ValueError(f"{source_dir_rel}/packs.toml [[files]] does not match curated 19 manifest-tracked files")

    recomputed = hashlib.sha256(
        json.dumps(
            digest_basis,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    if recomputed != manifest_sha:
        raise ValueError(
            f"{source_dir_rel}/packs.toml manifest_sha256 mismatch: expected {manifest_sha}, computed {recomputed}"
        )

    cc_text = (pack_dir / "notices/CC-BY-SA-4.0.md").read_text(encoding="utf-8")
    if (
        "Attribution-ShareAlike 4.0 International" not in cc_text
        or "https://creativecommons.org/licenses/by-sa/4.0/" not in cc_text
    ):
        raise ValueError(f"{source_dir_rel}/notices/CC-BY-SA-4.0.md does not contain full CC-BY-SA-4.0 legal terms")

    attr_text = (pack_dir / "ATTRIBUTION_AND_TERMS.md").read_text(encoding="utf-8")
    local_attr_text = (pack_dir / "notices/ATTRIBUTION_AND_LICENSE.md").read_text(encoding="utf-8")
    if "Wiktionary" not in attr_text or "CC-BY-SA-4.0" not in local_attr_text:
        raise ValueError(f"Canonical dictionary attribution notices are incomplete in {source_dir_rel}")

    with (pack_dir / "sources.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Canonical {source_dir_rel}/sources.csv must not be empty")
    for row in rows:
        if row.get("evidence_verification_state") != "verified" or row.get("reuse_state") != "permitted":
            raise ValueError(f"Unverified or unpermitted source in {source_dir_rel}/sources.csv: {row.get('source_id')}")
        attr_ref = json.loads(row["attribution_reference_json"])
        attr_val = json.loads(row["attribution_text_json"])
        reuse_basis = json.loads(row["reuse_basis_json"])
        if not attr_val or "CC-BY-SA-4.0" not in reuse_basis:
            raise ValueError(f"Incomplete attribution or reuse basis for source {row.get('source_id')}")
        if not str(attr_ref).startswith(("http://", "https://")):
            _safe_relative_posix(attr_ref)
            if attr_ref not in expected_set:
                raise ValueError(f"Missing referenced notice file {attr_ref!r} from {source_dir_rel}/sources.csv")

    _validate_canonical_with_lexicon_packs(pack_dir)
    return packs


def validate_dictionary_sources(root=ROOT, *, profiles=None):
    """Validate curated canonical dictionary files, manifest hashes, notices, and row schemas."""
    schema_dir = root / "schemas/lexicon"
    if not schema_dir.is_dir() or schema_dir.is_symlink():
        raise ValueError(f"Missing or invalid canonical schema directory: {schema_dir}")
    for schema_name in DICTIONARY_SCHEMAS:
        schema_path = schema_dir / schema_name
        if not schema_path.is_file() or schema_path.is_symlink():
            raise ValueError(f"Missing required canonical row schema: {schema_path}")
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid canonical row schema {schema_name}: {exc}") from exc

    expected_set = set(DICTIONARY_FILES)
    target_profiles = _validate_profiles(profiles) if profiles is not None else tuple(DICTIONARY_PACK_PROFILES)
    if not target_profiles:
        target_profiles = tuple(DICTIONARY_PACK_PROFILES)
    validated = {
        pack_id: _validate_single_dictionary_pack(root, pack_id, expected_set)
        for pack_id in target_profiles
    }
    return validated["core"] if "core" in validated else next(iter(validated.values()))


def _validate_profiles(profiles):
    normalized = tuple(dict.fromkeys(profiles))
    unknown = [p for p in normalized if p not in DICTIONARY_PACK_PROFILES]
    if unknown:
        raise ValueError(f"Unknown dictionary pack profile(s): {', '.join(unknown)}")
    return normalized


def artifact_license_spdx(artifact: str, *, profiles=()) -> str:
    """Return the exact SPDX license expression for a packaged artifact profile."""
    normalized = _validate_profiles(profiles)
    if artifact in ("tamil-core", "tamil-norm", "tamil-collate", "tamil-numerals",
                    "tamil-calendar", "tamil-codec", "tamil-hyphen", "tamil-translit"):
        if normalized:
            raise ValueError(f"Lower crate {artifact} cannot enable dictionary pack profiles: {normalized}")
        return "MIT"
    if artifact == "tamil-toolkit":
        return "MIT"
    if artifact == "python-sdist":
        return "MIT AND CC-BY-SA-4.0"
    if artifact in ("python-wheel", "npm", "dart"):
        return "MIT AND CC-BY-SA-4.0" if normalized else "MIT"
    raise ValueError(f"Unknown distribution artifact: {artifact!r}")


def artifact_notice_paths(artifact: str, *, profiles=(), root=ROOT, relative: bool = True):
    """Return canonical notice paths required for the given artifact and dictionary profile."""
    normalized = _validate_profiles(profiles)
    # Validate license rules first (rejects profiles on lower crates and unknown artifacts).
    spdx = artifact_license_spdx(artifact, profiles=normalized)
    rel_paths = ["THIRD_PARTY_NOTICES.md"]
    if "CC-BY-SA-4.0" in spdx:
        default_packs = tuple(DICTIONARY_PACK_PROFILES) if artifact == "python-sdist" else ("core",)
        for profile in normalized or default_packs:
            rel_paths.extend(DICTIONARY_PACK_PROFILES[profile]["notice_files"])
    seen = list(dict.fromkeys(rel_paths))
    if relative:
        return seen
    return [root / path for path in seen]


_NOTICE_REF_LICENSE_FILES = (
    "tests/reference/unicode-17.0.0/LICENSE.txt",
    "tests/reference/codec-v0.1/LICENSE-ag.txt",
    "tests/reference/codec-v0.1/LICENSE-pakeetharan.txt",
    "tests/reference/codec-tscii/LICENSE.txt",
    "tests/reference/calendar-thirukanitham-v1/astro-LICENSE.md",
)


def _render_pack_notice_section(root: Path, profiles) -> str:
    pack_sections = []
    included_packs = []
    for pack_id in _validate_profiles(profiles):
        cfg = DICTIONARY_PACK_PROFILES[pack_id]
        source_dir_rel = cfg["source_dir"]
        packs_path = root / source_dir_rel / "packs.toml"
        attr_notice = root / source_dir_rel / "notices/ATTRIBUTION_AND_LICENSE.md"
        if packs_path.is_file() and attr_notice.is_file():
            packs = tomllib.loads(packs_path.read_text(encoding="utf-8"))
            dataset_version = packs.get("dataset_version", "unknown")
            manifest_sha = packs.get("manifest_sha256", "unknown")
            included_packs.append(pack_id)
            pack_sections.append(
                f"- `{pack_id}` (`{source_dir_rel}/`): dataset `{dataset_version}`, "
                f"manifest SHA-256 `{manifest_sha}`\n"
                f"  - `{source_dir_rel}/ATTRIBUTION_AND_TERMS.md`\n"
                f"  - `{source_dir_rel}/notices/ATTRIBUTION_AND_LICENSE.md`\n"
                f"  - `{source_dir_rel}/notices/CC-BY-SA-4.0.md`"
            )
    if not pack_sections:
        return ""
    pack_names = ", ".join(f"`{pack_id}`" for pack_id in included_packs)
    sections_text = "\n".join(pack_sections)
    return (
        "## Wiktionary Dictionary Data Packs (CC-BY-SA-4.0)\n\n"
        f"The canonical Wiktionary data packs ({pack_names}) and source-archive\n"
        "copies distributed with `tamil-toolkit` are separately licensed under **CC-BY-SA-4.0**\n"
        "(upstream English Wiktionary contributors, dual CC-BY-SA-4.0 / GFDL upstream). The project\n"
        "MIT license continues to cover original Rust/binding code, lower crates, and default\n"
        "zero-data runtime distributions without embedded dictionary data. Complete attribution,\n"
        "revision/history links, section 7 disclaimers, and full CC-BY-SA-4.0 legal text are\n"
        "distributed in:\n\n"
        f"{sections_text}\n\n"
    )


def copy_profile_notices(destination: Path, *, profiles=("core",), root=ROOT):
    """Validate and copy notice files and pack-scoped THIRD_PARTY_NOTICES.md into a release artifact directory."""
    normalized = _validate_profiles(profiles)
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    if normalized:
        validate_dictionary_sources(root, profiles=normalized)
    if all((root / source).is_file() for source in _NOTICE_REF_LICENSE_FILES):
        scoped_notice_bytes = notices(root, profiles=normalized)
    else:
        raw_notice = (root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        prefix = raw_notice.split("## Wiktionary Dictionary Data Packs", 1)[0]
        scoped_notice_bytes = (prefix + _render_pack_notice_section(root, normalized)).encode("utf-8")
    notices_target = dest / "THIRD_PARTY_NOTICES.md"
    notices_target.write_bytes(scoped_notice_bytes)
    written = [notices_target]
    rel_paths = []
    for profile in normalized:
        rel_paths.extend(DICTIONARY_PACK_PROFILES[profile]["notice_files"])
    for rel in dict.fromkeys(rel_paths):
        src = root / rel
        if not src.is_file():
            raise ValueError(f"Missing canonical notice source: {src}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        written.append(target)
    return written


def expected_dictionary_files(root=ROOT):
    """Return the validated mapping of canonical dictionary files and row schemas to crate copies."""
    validate_dictionary_sources(root)
    crate_root = root / "crates/tamil-toolkit"
    mapped = {}
    for cfg in DICTIONARY_PACK_PROFILES.values():
        source_dir_rel = cfg["source_dir"]
        for rel in DICTIONARY_FILES:
            _safe_relative_posix(rel)
            mapped[crate_root / source_dir_rel / rel] = (root / source_dir_rel / rel).read_bytes()
    for schema_name in DICTIONARY_SCHEMAS:
        _safe_relative_posix(schema_name)
        mapped[crate_root / "schemas/lexicon" / schema_name] = (root / "schemas/lexicon" / schema_name).read_bytes()
    return mapped


def notices(root=ROOT, *, profiles=None):
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
    target_profiles = tuple(DICTIONARY_PACK_PROFILES) if profiles is None else _validate_profiles(profiles)
    text += _render_pack_notice_section(root, target_profiles)
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
        license_badge = (
            "[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)]"
            "(https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)"
        )
        license_section = """Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md)."""
        text = f"""<div align="center">

# {name}

**{SUMMARIES[name]}**

[![crates.io version](https://img.shields.io/crates/v/{name}?style=flat-square)](https://crates.io/crates/{name})
[![crates.io downloads](https://img.shields.io/crates/d/{name}?style=flat-square&label=downloads)](https://crates.io/crates/{name})
[![docs.rs](https://docs.rs/{name}/badge.svg)](https://docs.rs/{name}/{version})
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
{license_badge}

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

{license_section}
"""
        files[root / "crates" / name / "README.md"] = text.encode("utf-8")

    if (root / "lexicon").is_dir():
        for name, inputs in INPUTS.items():
            for filename in inputs:
                lex_file = root / "lexicon" / filename
                if lex_file.is_file():
                    files[root / "crates" / name / "lexicon" / filename] = lex_file.read_bytes()
    if (root / "lexicon/dictionary").is_dir():
        files.update(expected_dictionary_files(root))

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


def _managed_directories(root: Path, public_crates):
    managed = [root / "crates" / name / "lexicon" for name in public_crates]
    managed.append(root / "crates/tamil-toolkit/schemas/lexicon")
    return managed


def sync(root=ROOT, check=False):
    policy = load(root)
    stale = []
    extra = []
    files = expected_files(root)
    expected_set = set(files)

    for managed_dir in _managed_directories(root, policy["public_crates"]):
        if not managed_dir.exists() and not managed_dir.is_symlink():
            continue
        if managed_dir.is_symlink():
            rel = str(managed_dir.relative_to(root))
            extra.append(rel)
            if not check:
                managed_dir.unlink()
            continue
        for candidate in sorted(managed_dir.rglob("*"), reverse=True):
            if candidate.is_symlink():
                rel = str(candidate.relative_to(root))
                extra.append(rel)
                if not check:
                    candidate.unlink()
            elif candidate.is_file() and candidate not in expected_set:
                rel = str(candidate.relative_to(root))
                extra.append(rel)
                if not check:
                    candidate.unlink()
            elif candidate.is_dir() and not check and not any(candidate.iterdir()):
                candidate.rmdir()

    if check and extra:
        raise ValueError(
            "Unexpected files in managed release directories; run just sync-release-files: "
            + ", ".join(sorted(extra))
        )

    for path, expected in files.items():
        if path.is_symlink():
            stale.append(str(path.relative_to(root)))
            if not check:
                path.unlink()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(expected)
            continue
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
    parser.add_argument("mode", nargs="?", choices=("sync", "check"), default=None)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    sync(root=args.root, check=bool(args.check or args.mode == "check"))
