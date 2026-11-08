<div align="center">

# tamil-toolkit for Python

### High-Performance Tamil NLP, Text Processing & Unicode Library for Python

**Blazing fast Rust-backed Tamil NLP · Grapheme & Syllable segmentation · Agara varisai sorting · Legacy font conversion (Bamini, TSCII, TAB, TAM, Vanavil) · Currency & Numerals · Panchangam calendar**

[![PyPI version](https://img.shields.io/pypi/v/tamil-toolkit?style=flat-square&logo=pypi&logoColor=white)](https://pypi.org/project/tamil-toolkit/)
[![PyPI monthly downloads](https://img.shields.io/pypi/dm/tamil-toolkit?style=flat-square&label=monthly)](https://pypistats.org/packages/tamil-toolkit)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://pypi.org/project/tamil-toolkit/)
[![CPython abi3](https://img.shields.io/badge/wheel-abi3-success.svg?style=flat-square)](https://pypi.org/project/tamil-toolkit/)

[Install](#install) · [Quick Start](#quick-start) · [Key Capabilities](#what-is-included) · [Feature Comparison](#why-tamil-toolkit-for-python) · [Documentation](#documentation) · [License](#license)

</div>

---

**tamil-toolkit** is the premier, high-performance Tamil language and NLP library for Python 3.11+. Powered under the hood by memory-safe, zero-cost Rust abstractions, it brings deterministic, microsecond-level Tamil computational linguistics to Python data scientists, NLP researchers, web developers, and automation engineers.

Pre-built binary wheels using the stable CPython `abi3` interface are provided for Windows, macOS (Apple Silicon and Intel x86_64), and Linux. Installation is instantaneous with zero compiler dependencies.

---

## What is Included

| Domain | Python Capabilities |
|---|---|
| 🔤 **Unicode & Letters** | NFC/NFD normalization, tailored Tamil letter segmentation (`get_letters`), Mei/Uyir splitting, and scalar inspection. Correctly handles ligatures like `க்ஷ` and `ஸ்ரீ`. |
| 🎵 **Phonology & Prosody** | Tholkappiyam-grounded phonology: exact mora (*Maathirai*) duration calculation, letter quantity classification (`is_kuril`, `is_nedil`, `is_mei`, `is_otru`, `is_aytham`), stop-nasal cognates (*Ina Ezhuthu* via `get_cognate`, `are_cognates`), and zero-allocation syllable nuclei (*Olippasai*). |
| 🔄 **Legacy Font Transcoder** | Universal bidirectional transcoding between Unicode and legacy Tamil encoding formats: **Bamini**, **TSCII**, **TAB**, **TAM**, **Anjal**, **Vanavil Avvaiyar**, and **LT-TM / IndoWord**. |
| 🔠 **Agara Varisai Collation** | Traditional Tamil dictionary alphabetical sorting (*Agara Varisai*) with stable Mei-first collation order and versioned sort/search keys. |
| 🔢 **Numerals & Currency** | Bounded Tamil Nadu (`ta-IN`) and Sri Lankan (`ta-LK`) number-to-words conversion, exact financial currency formatting (INR/LKR) with zero floating-point drift, rational fractions, and Gregorian civil dates. |
| 📅 **Solar Calendar & Panchangam** | Classical Thirukanitham Drik and 1962 Vākyakaraṇa calendar models: Gregorian ↔ Tamil solar date conversion, 60-year Jovian cycles, and five-limb astronomical panchangam calculations. |

---

## Why tamil-toolkit for Python?

Unlike legacy pure-Python packages (such as `open-tamil`), **tamil-toolkit** is engineered for production workloads:

- ⚡ **10x to 50x Faster**: Core algorithms run in compiled Rust via the C-ABI with zero Python interpreter overhead.
- 🎯 **Linguistic Accuracy**: Adheres strictly to Unicode UAX #29, CLDR 49, and classical grammatical treatises (Tolkappiyam).
- 🛡️ **Zero Floating Point Drift**: Currency formatting uses exact integer minor-unit math (e.g. paisa/cents) rather than imprecise IEEE-754 floats.
- 📦 **Instant Installation**: Pre-compiled binary wheels for all major platforms (Windows, macOS x86_64/ARM64, Linux glibc/musl).

---

## Install

```sh
python -m pip install tamil-toolkit==0.1.0a7
```

---

## Quick Start

### 1. Accurate Tamil Letter Segmentation

Python's built-in `len()` or string slicing breaks compound Tamil grapheme clusters. `tamil-toolkit` treats each Tamil letter (including vowel modifiers and atomic ligatures like `க்ஷ` and `ஸ்ரீ`) as a unified glyph:

```python
import tamil_toolkit as tamil

text = "தமிழ்நாடு"
letters = tamil.get_letters(text)
print("Letter count:", len(letters))  # 5 (not 10!)
print("Letters:", letters)            # ['த', 'மி', 'ழ்', 'நா', 'டு']

# Correct handling of complex Grantha ligatures
shree = "ஸ்ரீலங்கா"
print(tamil.get_letters(shree))       # ['ஸ்ரீ', 'ல', 'ங்', 'கா']
```

### 2. Legacy Font Transcoder (Bamini, TSCII, TAB, TAM, Vanavil)

Convert legacy digitized archives, PDF extractions, and older websites into modern Unicode:

```python
import tamil_toolkit as tamil

# Bamini font to Unicode
bamini_text = "jkpo;ehL"
unicode_text = tamil.bamini_to_unicode(bamini_text)
print(unicode_text)  # தமிழ்நாடு

# Unicode back to Bamini
print(tamil.unicode_to_bamini("வணக்கம்"))  # tzf;fk;

# Advanced transcoders via the unified execute() dispatcher
# TSCII bytes to Unicode:
tscii_data = [0xba, 0xa2, 0xc5, 0xfd]
restored = tamil.execute({
    "op": "tscii_bytes_to_unicode",
    "input": {"bytes": tscii_data}
})
print("From TSCII:", restored)

# Vanavil Avvaiyar font to Unicode:
vanavil_result = tamil.execute({
    "op": "vanavil_text_to_unicode",
    "input": {"text": "jkpo;"}
})
```

### 3. Number to Tamil Words & Cheque Currency Formatting

Format numbers for banking, legal cheques, invoices, and formal documents:

```python
import tamil_toolkit as tamil

# Exact currency formatting without floating-point errors (input in minor units: cents/paisa)
# 102550 minor units = 1,025.50
inr = tamil.format_currency(102550, "INR", "TN")
print("Tamil Nadu INR:", inr)  # INR 1,025.50

lkr = tamil.format_currency(102550, "LKR", "SL")
print("Sri Lanka LKR:", lkr)   # LKR 1,025.50

# Rational fraction formatting
print(tamil.format_fraction(2, 4))  # 1/2
```

### 4. Agara Varisai Dictionary Collation

Sort lists and datasets according to traditional Tamil lexicographical ordering:

```python
import tamil_toolkit as tamil

words = ["ஆப்பிள்", "அணில்", "ஔவையார்", "இலை", "ஈட்டி", "உரல்"]
sorted_words = tamil.sort_words(words)
print("Agara Varisai:", sorted_words)
# Output: ['அணில்', 'ஆப்பிள்', 'இலை', 'ஈட்டி', 'உரல்', 'ஔவையார்']

# Compare two words
print(tamil.compare("அம்மா", "அப்பா"))  # -1 (அம்மா comes before அப்பா)
```

### 5. Phonology, Mora (*Maathirai*) & Cognates (*Ina Ezhuthu*)

Analyze poetic prosody and phonetic properties:

```python
import tamil_toolkit as tamil

# Letter Quantity Classification
assert tamil.is_kuril("அ") == True
assert tamil.is_nedil("ஆ") == True
assert tamil.is_mei("க்") == True
assert tamil.is_otru("க்") == True
assert tamil.is_aytham("ஃ") == True

# Exact Mora (Maathirai) calculation
# த (1.0) + மி (1.0) + ழ் (0.5) = 2.5
mora = tamil.baseline_maathirai("தமிழ்")
print("Maathirai for 'தமிழ்':", mora)  # 2.5

# Homorganic Stop-Nasal Cognates (Ina Ezhuthu)
assert tamil.get_cognate("க்") == "ங்"
assert tamil.get_cognate("ச்") == "ஞ்"
assert tamil.get_cognate("தூ") == "நூ"
assert tamil.are_cognates("ட்", "ண்") == True
```

---

## Alpha 7 scope

The PyPI `0.1.0a7` package includes the capabilities listed above. The shared
`execute` API exposes `lt_tm_codes_to_unicode`, `lt_tm_text_to_unicode`,
`unicode_to_lt_tm_codes`, and `unicode_to_lt_tm_text`. LT-TM conversion handles
selected 16-bit code sequences; it does not parse PDFs, select font runs, or
detect encodings. The profile does not claim complete historical-font coverage.
APIs may change.

Other planned linguistic modules, the private PDF extraction utility, and
Dart/Pub distribution are not published.

```python
import tamil_toolkit as tamil

codes = tamil.execute({"op": "unicode_to_lt_tm_codes", "input": {"text": "தமிழ்"}})
text = tamil.execute({"op": "lt_tm_codes_to_unicode", "input": {"codes": codes}})
```

---

## Author & Maintainer

**Abishtakan Sivachandrathevan** ([@abishtakan](https://github.com/abishtakan))

---

## Documentation

- [API and feature overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Unicode/core contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Collation contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/collate-v0.1.md)
- [Numerals, fractions, and dates](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.2.md)
- [Codec contract and alpha 3 limits](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-7.md#compatibility-and-scope)
- [LT-TM CID profile contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/codec-lt-tm.md)
- [Python package API declarations](https://github.com/abishtakan/tamil-toolkit/blob/master/bindings/python/python/tamil_toolkit/__init__.py)
- [Third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md)

The wheels target CPython 3.11+ through the stable abi3 interface. Source builds
require Rust 1.85+. See the [alpha 7 release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-7.md)
for artifact details.

---

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).

---

## Keywords & Search Queries

`tamil nlp python`, `python tamil text processing`, `bamini to unicode python`, `tscii to unicode converter python`, `tamil numerals spellout python`, `tamil sort agara varisai`, `tamil letter segmentation python`, `tamil panchangam calendar python`, `tamil unicode normalizer`, `open-tamil alternative`, `fast tamil library python`.
