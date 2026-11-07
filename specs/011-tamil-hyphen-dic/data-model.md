# Data Model: Hyphenation Dictionary & LibreOffice Extension

**Feature**: `011-tamil-hyphen-dic`
**Date**: 2026-11-06
**Status**: Completed

## 1. Core Entities & Types

### 1.1 `LiangPattern`
Represents an individual Frank Liang hyphenation pattern consisting of characters interleaved with numeric weights (`0`-`9`).

| Field | Type | Description |
|---|---|---|
| `raw_pattern` | `String` | Original pattern string, e.g. `"2க்ஷ2"`, `"2க1"`, `"1அ"` |
| `text` | `String` | Extracted characters without weight digits |
| `weights` | `Vec<u8>` | Sequence of numeric weights between/around characters |

**Validation Rules**:
- Encoding MUST be valid UTF-8.
- Digits MUST be ASCII numbers `0`-`9`.
- Pattern length (excluding digits) MUST be >= 1 character.

---

### 1.2 `DicHeader`
Represents the configuration and license preamble of a `.dic` file.

| Field | Type | Default | Description |
|---|---|---|---|
| `encoding` | `String` | `"UTF-8"` | Character encoding of the dictionary |
| `left_hyphen_min` | `usize` | `2` | Minimum scalar characters before first break |
| `right_hyphen_min` | `usize` | `2` | Minimum scalar characters after last break |
| `license_notice` | `String` | MIT / LGPL / GPL | Upstream-compatible tri-license header |

---

### 1.3 `HyphenDictionary`
Represents the complete generated TeX / Hunspell pattern dictionary.

| Field | Type | Description |
|---|---|---|
| `header` | `DicHeader` | Dictionary header and metadata |
| `patterns` | `Vec<LiangPattern>` | Alphabetically sorted list of distinct patterns |

**State Transitions**:
1. `Empty` -> `PhonotacticGeneration` -> `Synthesized`
2. `Synthesized` -> `ValidationAgainstGolden` -> `Verified`
3. `Verified` -> `Serialization` -> `hyph_ta_IN.dic` (file output)

---

### 1.4 `OxtPackage`
Represents the packaging manifest and metadata for the LibreOffice extension.

| Field | Type | Description |
|---|---|---|
| `identifier` | `String` | `"org.tamiltoolkit.hyphenation"` |
| `version` | `String` | autorated from toolkit version (e.g. `"0.1.0"`) |
| `display_name_en` | `String` | `"Tamil Syllabic Hyphenation Dictionary"` |
| `display_name_ta` | `String` | `"தமிழ் அசைசார் சொல் பிரிப்பான்"` |
| `supported_locales` | `Vec<String>` | `["ta-IN", "ta-LK", "ta-SG", "ta-MY", "ta"]` |
| `dictionary_filename` | `String` | `"hyph_ta_IN.dic"` |

---

### 1.5 `BenchmarkComparison`
Represents the automated comparative metrics between legacy SMC patterns and new generated patterns.

| Metric | Type | Description |
|---|---|---|
| `total_words_tested` | `usize` | Total words in verification corpus |
| `legacy_illegal_breaks` | `usize` | Number of broken diacritics / illegal coda splits in legacy |
| `new_illegal_breaks` | `usize` | Target: strictly `0` |
| `fixed_defect_examples` | `Vec<DefectDiff>` | Specific word diffs highlighting solved failure modes |
