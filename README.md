<div align="center">

# tamil-toolkit

### The High-Performance Tamil NLP, Unicode & Linguistic Toolkit for Rust, Python, and JavaScript/WASM

**Universal Tamil text processing · Grapheme, Word & Sentence segmentation · Agara varisai sorting · Legacy font conversion · Currency & Numerals · Panchangam calendar · DTP Hyphenation**

[![Rust CI][ci-badge]][ci]
[![crates.io version][crates-version]][crates]
[![crates.io total downloads][crates-downloads]][crates]
[![PyPI version][pypi-version]][pypi]
[![PyPI monthly downloads][pypi-downloads]][pypistats]
[![npm version][npm-version]][npm]
[![npm monthly downloads][npm-downloads]][npm]
[![Apache-2.0 license][license-badge]][license]
[![Zero Unsafe](https://img.shields.io/badge/unsafe-zero-success?style=flat-square&logo=rust)](crates/tamil-core)
[![WebAssembly](https://img.shields.io/badge/WASM-100%25%20offline-blueviolet?style=flat-square&logo=webassembly)](bindings/js-wasm)

[Features](#key-features) · [Quick Start](#quick-start) · [Install](#installation) · [Interactive Playground](#interactive-playground) · [Recipes](#common-recipes) · [Performance](#performance--benchmarks) · [Capability Contracts](#capability-contracts) · [Contributing](CONTRIBUTING.md)

</div>

---

**tamil-toolkit** is an all-in-one, memory-safe Tamil linguistic engine written in Rust (`#![forbid(unsafe_code)]`) and compiled to native libraries and WebAssembly for **Rust (crates.io)**, **Python (PyPI abi3 wheels)**, **JavaScript / TypeScript (npm ESM/WASM for Node.js & Browsers)**, **Dart/Flutter**, and **Microsoft Word**.

One canonical Rust core powers every runtime with verified golden-vector parity (**40,550 active vectors** across Rust, Python, Node/Browser WASM, and Dart). Try it immediately in the [live WebAssembly Playground](https://tamil-toolkit-playground.vercel.app/) or read the machine-readable index in [llms.txt](llms.txt).

---

## Key Features

| Capability | What It Delivers |
|---|---|
| 🔤 **Unicode & Segmentation** | Tailored UAX #29 grapheme cluster segmentation treating `க்ஷ` and `ஸ்ரீ` as atomic letters, Mei/Uyirmei decomposition & composition, canonical NFC/NFD normalization preserving ZWJ/ZWNJ joiners, orthographic repair, Mayangoli search folding, and scalar inspection. |
| 🧩 **Word & Sentence Tokenization** | Offline, source-preserving word and sentence spans (`tokenize_words`, `segment_sentences`) with exact zero-based UTF-8 byte & written-unit offsets, attested Tamil abbreviation handling (`திரு.`, `மு.க.`, `பி.ப.`, `மு.ப.`, `எ.கா.`, `ரூ.`), and opt-in stopword profiles (`none`, `conservative`, `broad`). |
| 🎵 **Phonology & Mora Metrics** | Tholkappiyam-grounded phonological analysis: exact mora (*Maathirai*) duration (`KURIL = 1.0`, `NEDIL = 2.0`, `MEI = 0.5`, `AYTHAM = 0.5`), quantity classification (`is_kuril`, `is_nedil`, `is_mei`, `is_aytham`), homorganic cognates (*Ina Ezhuthu*), and borrowed syllable nuclei (*Olippasai*). |
| 🔠 **Agara Varisai Sorting** | Lexicographical Tamil alphabetical collation following traditional Mei-first dictionary order (`agara-v1`) and school Uyirmei-first order (`uyirmei-first-v1`), with versioned sort keys and canonical search keys. |
| 📐 **DTP Syllabic Hyphenation** | Coda-binding syllabic hyphenation (`\u{00AD}`) that never strands a pulli consonant (ஒற்று), responsive line wrapping, Hunspell `.dic` export, LibreOffice `.oxt`, and a [Microsoft Word Add-in](https://tamil-toolkit-word.vercel.app/support.html). |
| ⌨️ **Transliteration & Offline Input** | Lossless bidirectional scholarly romanization (`iso-15919`, `madras-lexicon`, `itrans`, `harvard-kyoto`), bidirectional Tanglish (`phonetic-v1`), deterministic keyboard input (`tamil99`, `anjal-phonetic`, `suratha-bamini`), and phonotactically constrained Mayangoli suggestions (`transliterate_suggest`). |
| 🔀 **Sandhi / Punarchi (`tamil-punarchi`)** | Deterministic *Nannool* (Sutras 151–257) sandhi joining (*Thonral*, *Thirithal*, *Keduthal*, *Iyalbu*) with *Vetrumai*/*Alvazhi* context and sutra-by-sutra derivations, plus dictionary-free inverse split candidate generation. |
| 📖 **Lexicon & Reverse English Search** | Compact `TMLPACK2` `.tlpack` runtime reader (`tamil-lexicon`), exact/prefix/fuzzy/*Mayangoli*-folded FST lookup, reverse English-to-Tamil gloss search (`lexicon_search_english`), atomic domain/register/region facets, and SHA-256-verified pack managers across CLI, Python, JS/WASM, and Dart. |
| 🔢 **Numerals, Currencies & ITN** | Bounded Tamil Nadu (`TN`) and Sri Lanka (`SL`) number-to-words (`-999,999,999..=999,999,999`), exact currency formatting (`INR`, `LKR`, `SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`), colloquial mixed fractions, formal `words_to_number` ITN, traditional numerals (`௰`, `௱`, `௲`), and 72 Unicode Tamil symbols. |
| 🔄 **Legacy Codecs & Bharathi Braille** | Bidirectional conversion between Tamil Unicode and bounded legacy profiles: **Bamini**, **TSCII**, **TAB**, **TAM**, **Anjal**, **Vanavil Avvaiyar**, **LT-TM**, **Senthamil**, **Shree-Tam**, **Softview**, **TBO**, and **Bharathi Tamil Braille Grade 1** (plus client-side PDF text-layer import in the Playground). |
| 📅 **Solar Calendar & Panchangam** | Active civil profiles (60-year Jovian cycle, Thiruvalluvar year, TN/SL official holiday snapshots, Tamil date display) plus experimental bounded **Thirukanitham** (Drik) and 1962 **Vākyakaraṇa** solar-lunar engines and five limbs (*Tithi*, *Nakshatram*, *Yogam*, *Karanam*, *Vāram*). |
| ⚡ **Multi-Package-Manager Parity** | Single Rust engine shipped across `crates.io`, `PyPI`, and `npm` (ESM + WebAssembly), plus Dart FFI, Microsoft Word, and Chrome/Edge/Firefox MV3 extensions. Processes text locally without external API calls. |

---

## Interactive Playground

Try all tools live in your browser at **[tamil-toolkit-playground.vercel.app](https://tamil-toolkit-playground.vercel.app/)** (processes text locally via WebAssembly):

- [Agara Varisai Tamil Sorter](https://tamil-toolkit-playground.vercel.app/tools/agara-varisai-sorter/) — Mei-first & Uyirmei-first alphabetical sorting
- [Tamil Word & Sentence Tokenizer](https://tamil-toolkit-playground.vercel.app/tools/tamil-tokenizer/) — Source-preserving word/sentence spans, attested abbreviations & stopword filtering
- [Tamil99 Keyboard & Transliteration](https://tamil-toolkit-playground.vercel.app/tools/tamil99-keyboard/) — ISO 15919, Madras Lexicon, ITRANS, Harvard-Kyoto, Tanglish, Tamil99, Anjal, Suratha Bamini
- [Tamil Number to Words & Cheque Formatter](https://tamil-toolkit-playground.vercel.app/tools/tamil-number-to-words/) — TN/SL spellout, 8 currencies, ITN, mixed fractions & traditional numerals
- [Tamil Syllabic Hyphenator](https://tamil-toolkit-playground.vercel.app/tools/tamil-hyphenation/) — Coda-binding soft hyphens, `.dic` & LibreOffice `.oxt`
- [Tamil Calendar & Panchangam](https://tamil-toolkit-playground.vercel.app/tools/tamil-panchangam/) — Thirukanitham & Vakya solar dates and five limbs
- [Legacy Tamil Font Converter](https://tamil-toolkit-playground.vercel.app/tools/bamini-to-unicode/) & [Bharathi Tamil Braille Converter](https://tamil-toolkit-playground.vercel.app/tools/tamil-braille-converter/) — Legacy encodings, Braille Grade 1 & client-side PDF text-layer import

```bash
# Run playground locally
pnpm playground:dev
# or using just
just playground-dev
```

---

## Installation

Choose the SDK for your technology stack:

| SDK | Install 0.3.0 | Version | Downloads |
| --- | --- | --- | --- |
| **Rust 1.85+** | `cargo add tamil-toolkit@=0.3.0` | [![crates.io][crates-version]][crates] | [![crates.io total downloads][crates-downloads]][crates] |
| **Python 3.11+** | `python -m pip install tamil-toolkit==0.3.0` | [![PyPI][pypi-version]][pypi] | [![PyPI monthly downloads][pypi-downloads]][pypistats] |
| **Node.js 22+ / browsers** | `npm install tamil-toolkit@latest` | [![npm][npm-version]][npm] | [![npm monthly downloads][npm-downloads]][npm] |

**Release scope:** npm’s `latest` tag points to 0.3.0; see the [release notes](CHANGELOG.md) and [0.3.0 compatibility details](docs/releases/v0.3.0.md#compatibility-and-scope).

Download badges track the umbrella package in each registry: total downloads on crates.io and monthly downloads on PyPI and npm.

All twelve Rust crates are published at `0.3.0`: [`tamil-core`](https://crates.io/crates/tamil-core), [`tamil-norm`](https://crates.io/crates/tamil-norm), [`tamil-collate`](https://crates.io/crates/tamil-collate), [`tamil-numerals`](https://crates.io/crates/tamil-numerals), [`tamil-calendar`](https://crates.io/crates/tamil-calendar), [`tamil-codec`](https://crates.io/crates/tamil-codec), [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen), [`tamil-punarchi`](https://crates.io/crates/tamil-punarchi), [`tamil-translit`](https://crates.io/crates/tamil-translit), [`tamil-tokenize`](https://crates.io/crates/tamil-tokenize), [`tamil-lexicon`](https://crates.io/crates/tamil-lexicon), and [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit).

**Contract boundaries:** Legacy font profiles (Bamini, TSCII, TAB, TAM, Anjal, LT-TM, Vanavil, Senthamil, Shree-Tam, Softview, TBO) and Bharathi Braille use declared bounded profiles; they do not claim complete historical-font coverage. Four civil calendar suites are active while 13 Thirukanitham/Vakya ephemeris and observance suites remain experimental (`planned` pending independent witness review). Planned NLP modules (Phases 11–17: `tamil-morph`, `tamil-yaappu`, `tamil-phonetics`, `tamil-dialect`, `tamil-spell`) and Dart/Pub or PostgreSQL distributions remain outside the public release. See the [LT-TM contract](docs/specs/codec-lt-tm.md), [Vanavil contract](docs/specs/codec-vanavil.md), [tokenizer contract](docs/specs/tokenize-v0.1.md), [punarchi contract](docs/specs/punarchi-v0.1.md), [lexicon contract](docs/specs/lexicon-v0.2.md), [calendar scope](docs/releases/numerals-calendar-candidate.md), and [0.3.0 compatibility details](docs/releases/v0.3.0.md#compatibility-and-scope).

---

## Quick Start

### Python (3.11+)

Pre-built CPython abi3 binary wheels are available for Windows, macOS (Intel & Apple Silicon), and Linux.

```python
import tamil_toolkit as tamil

# 1. Letter Segmentation (handles ligatures like க்ஷ, ஸ்ரீ correctly)
text = "தமிழ்நாடு"
letters = tamil.get_letters(text)
print("Letters:", letters)  # ['த', 'மி', 'ழ்', 'நா', 'டு']

# 2. Legacy Font Conversion (Unicode <-> Bamini, TSCII, TAB, TAM, Vanavil)
bamini = tamil.unicode_to_bamini(text)
print("Bamini:", bamini)  # jkpo;ehL
print("Restored:", tamil.bamini_to_unicode(bamini))  # தமிழ்நாடு

# 3. Currency & Legal Cheque Amount Formatting
amount = tamil.format_currency(102550, "LKR", "SL")
print("Currency:", amount)  # LKR 1,025.50

# 4. Agara Varisai Dictionary Collation
words = ["ஆப்பிள்", "அணில்", "இலை", "ஈட்டி"]
print("Sorted:", tamil.sort_words(words))  # ['அணில்', 'ஆப்பிள்', 'இலை', 'ஈட்டி']

# 5. Phonology: Mora Calculation (Maathirai) & Syllable Nuclei (Olippasai)
mora = tamil.baseline_maathirai("தமிழ்")
print("Total Maathirai:", mora)  # 2.5 (த=1.0 + மி=1.0 + ழ்=0.5)
```

---

### JavaScript & TypeScript (Node.js & Web)

Native ESM and CommonJS support for Node.js 22+, Next.js, Vite, and modern browsers via WebAssembly.

#### Node.js / Server-side:

```typescript
import * as tamil from "tamil-toolkit";

// 1. Text Segmentation & Letter Inspection
const letters = tamil.get_letters("தமிழ்");
console.log(letters); // [ 'த', 'மி', 'ழ்' ]

// 2. Legacy Font Transcoder
const legacy = tamil.unicode_to_bamini("தமிழ்");
console.log(legacy); // "jkpo;"
console.log(tamil.bamini_to_unicode(legacy)); // "தமிழ்"

// 3. Exact Cheque & Currency Formatting
console.log(tamil.format_currency(102550, "INR", "TN")); // "INR 1,025.50"

// 4. Tamil Alphabetical Sorting
const sorted = tamil.sort_words(["கனி", "கவிதை", "அறம்", "ஈகை"]);
console.log(sorted); // [ 'அறம்', 'ஈகை', 'கனி', 'கவிதை' ]
```

#### Browser / Client-side (Zero-latency WebAssembly):

```javascript
import { init, get_letters, unicode_to_bamini } from "tamil-toolkit/web";

// Initialize the WebAssembly module once at application startup
await init();

const letters = get_letters("வணக்கம்");
console.log(letters); // [ 'வ', 'ண', 'க்', 'க', 'ம்' ]
const encoded = unicode_to_bamini("வணக்கம்");
console.log(encoded); // "tzf;fk;"
```

---

### Rust (1.85+)

Direct zero-cost abstractions with zero unsafe code in core modules.

```rust
use tamil_toolkit::{codec, core, numerals, collate};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let word = "தமிழ்";

    // 1. Zero-allocation tailored letter segmentation
    let letters = core::get_letters(word);
    assert_eq!(letters, vec!["த", "மி", "ழ்"]);

    // 2. Phonological Mora (Maathirai) & Cognates (Ina Ezhuthu)
    let mora = core::baseline_maathirai(word);
    assert_eq!(mora.as_fraction(), (5, 2)); // 2.5 mora
    assert!(core::are_cognates("க்", "ங்"));

    // 3. Bidirectional Legacy Font Conversion
    let bamini = codec::unicode_to_bamini(word)?;
    assert_eq!(bamini, "jkpo;");
    let back = codec::bamini_to_unicode(&bamini, codec::ErrorPolicy::Strict)?;
    assert_eq!(back, word);

    // 4. Agara Varisai Dictionary Sorting
    let mut dictionary = vec!["ஆடு", "அம்மா", "இலை"];
    collate::sort_words_slice(&mut dictionary);
    assert_eq!(dictionary, vec!["அம்மா", "ஆடு", "இலை"]);

    // 5. Exact Currency and Bounded Numerals
    let parsed = numerals::parse_decimal("123.45", "latin", "none", false)?;
    let formatted = numerals::format_currency_decimal(&parsed, numerals::Currency::INR, numerals::Locale::TN)?;
    println!("{formatted}");

    Ok(())
}
```

---

## Common Recipes

### 1. Legacy Font Conversion (Batch & File Processing)
Convert legacy news archives, government gazettes, and university documents encoded in Bamini, TSCII, TAB, TAM, Anjal, or Vanavil into modern Unicode:

```python
import tamil_toolkit as tamil

# Bamini font to Unicode
unicode_text = tamil.bamini_to_unicode(bamini_string)

# TSCII byte stream to Unicode
unicode_text = tamil.execute({
    "op": "tscii_bytes_to_unicode",
    "input": {"bytes": [0xba, 0xa2, 0xc5, 0xfd]}
})

# Vanavil Avvaiyar font to Unicode
unicode_from_vanavil = tamil.execute({
    "op": "vanavil_text_to_unicode",
    "input": {"text": vanavil_string}
})
```

### 2. Linguistic Syllable & Meter Analysis (*Olippasai* & *Maathirai*)
Analyze classical Tamil poetry or compute prosodic meter units:

```python
import tamil_toolkit as tamil

# Analyze mora (Maathirai) duration
assert tamil.is_kuril("அ") == True
assert tamil.is_nedil("ஆ") == True
assert tamil.is_otru("க்") == True
assert tamil.baseline_maathirai("பாடல்") == 4.0 # பா(2) + ட(1) + ல்(0.5) + ...

# Homorganic Stop-Nasal Cognates (Ina Ezhuthu)
assert tamil.get_cognate("க்") == "ங்"
assert tamil.get_cognate("சா") == "ஞா"
assert tamil.are_cognates("ட்", "ண்") == True
```

### 3. Syllabic Hyphenation for Desktop Publishing & Web Typography
Ensure high-quality justified Tamil text without ugly line breaks or broken vowel signs:

```rust
use tamil_hyphen::{hyphenate_text, wrap_text};

// Insert invisible soft-hyphens (\u{00AD}) into long text
let text = "பல்கலைக்கழகம் மற்றும் தமிழ்நாடு அரசு";
let soft_hyphenated = hyphenate_text(text, None).unwrap();

// Wrap text to fixed visual Tamil character column widths safely
let wrapped = wrap_text(text, 12, None).unwrap();
for line in wrapped.lines {
    println!("{line}");
}
```

### 4. Source-Preserving Word & Sentence Tokenization
Split Tamil prose into exact UTF-8 byte and written-unit spans without breaking attested abbreviations (`திரு.`, `மு.க.`, `பி.ப.`, `மு.ப.`, `எ.கா.`, `ரூ.`):

```python
import tamil_toolkit as tamil

text = "திரு. குமார் மற்றும் ரூ.100 வந்தது."
words = tamil.tokenize_words(text, stopword_profile="conservative")
sentences = tamil.segment_sentences(text)
```

---

## Performance & Benchmarks

| Feature / Metric | `tamil-toolkit` (Rust/WASM/Python) | Legacy Python (`open-tamil`) | Ad-hoc Regex / JS Scripts |
|---|---|---|---|
| **Runtime Implementation** | Native Rust core + CPython abi3 + WASM | Pure Python (interpreted) | JavaScript / Regex |
| **Grapheme Segmentation Speed** | **< 120 ns** / word (Zero-allocation) | ~2,500 ns / word | Variable, often breaks ligatures |
| **UAX #29 Ligature Precision** | ✅ Full support (`க்ஷ`, `ஸ்ரீ`, Grantha) | ⚠️ Partial / breaks on ligatures | ❌ Missing |
| **Phonological Mora (*Maathirai*)** | ✅ Fractional exact math (`KURIL = 1.0`, `MEI = 0.5`) | ⚠️ Integer approximations | ❌ None |
| **Zero-Allocation Syllable Nucleus** | ✅ `Olippasai` iterator (0 bytes allocated) | ❌ Allocates strings | ❌ None |
| **Legacy Transcoding Coverage** | ✅ 7 codecs (Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM) | ⚠️ 3 codecs (TSCII, Bamini, TAB) | ⚠️ Single codec only |
| **Client-Side Web (Browser / WASM)** | ✅ Native WASM package (100% offline) | ❌ Requires server/Pyodide | ⚠️ Fragile regex rules |
| **Currency & Legal Cheque Spellout** | ✅ Exact decimal (INR & LKR) without float drift | ⚠️ Basic numbers only | ❌ None |
| **Desktop Publishing / Hyphenation** | ✅ Soft-hyphen injection + LibreOffice `.oxt` | ❌ None | ❌ None |
| **Test Verification Suite** | ✅ **40,265 active golden vectors** verified across runtimes | ~200 unit tests | None |

---

## Capability Contracts

Every API in `tamil-toolkit` is governed by a formal capability specification:

| Looking for | Start here |
| --- | --- |
| Unicode letters, composition, and normalization | [Core contract](docs/specs/core-v0.1.md) |
| Agara sorting and search keys | [Collation contract](docs/specs/collate-v0.1.md) |
| Number words, currency, fractions, exact decimal strings, and civil arithmetic | [Numerals v0.1](docs/specs/numerals-v0.1.md) · [fractions and dates v0.2](docs/specs/numerals-v0.2.md) · [exact strings and civil arithmetic v0.3](docs/specs/numerals-v0.3.md) |
| Bounded calendar labels and inter-profile comparison | [Tamil display contract](docs/specs/calendar-tamil-display-v1.md) · [profile comparison contract](docs/specs/calendar-profile-comparison-v1.md) · [Thiruvalluvar convention contract](docs/specs/calendar-thiruvalluvar-year-v1.md) |
| Bounded Thirukanitham date conversion, panchangam, phases, arithmetic, daylight periods and cycle titles | [Profile contract](docs/specs/calendar-thirukanitham-v1.md) · [phase contract](docs/specs/calendar-lunar-phases-v1.md) · [arithmetic contract](docs/specs/calendar-solar-arithmetic-v1.md) · [cycle-title contract](docs/specs/calendar-year-cycle-v1.md) · [daylight-period contract](docs/specs/calendar-daylight-periods-v1.md) · [source research](docs/specs/numerals-calendar-source-research.md) |
| Authority-published holiday schedule snapshots | [Official schedule contract](docs/specs/calendar-official-holidays-v1.md) · [source research](docs/specs/numerals-calendar-source-research.md) |
| Bounded classical Vakiya civil, five-limb, arithmetic profile | [1962 edition contract](docs/specs/calendar-vakya-civil-v1.md) · [solar arithmetic contract](docs/specs/calendar-solar-arithmetic-v1.md) · [completion matrix](docs/specs/numerals-completion-plan.md) |
| Bamini, bounded byte profiles, and LT-TM / Vanavil CID conversion | [Codec contract](docs/specs/codec-v0.1.md) · [LT-TM profile](docs/specs/codec-lt-tm.md) · [Vanavil profile](docs/specs/codec-vanavil.md) · [0.3.0 scope](docs/releases/v0.3.0.md#compatibility-and-scope) |
| Syllable and orthographic boundary hyphenation | [Hyphenation specification](specs/009-tamil-hyphen/spec.md) · [DTP dictionary spec](specs/011-tamil-hyphen-dic/spec.md) · [Word & Google Docs roadmap](docs/integrations/word-googledocs-roadmap.md) |
| Word & sentence tokenization, abbreviations, and stopwords | [Tokenizer contract](docs/specs/tokenize-v0.1.md) · [Phase 9 spec](specs/024-tamil-tokenize/spec.md) |
| Rust API reference | [docs.rs/tamil-toolkit](https://docs.rs/tamil-toolkit/0.3.0/tamil_toolkit/) |
| Python and JavaScript/WASM SDK guides | [Python](bindings/python/README.md) · [JavaScript/WASM](bindings/js-wasm/README.md) |
| Published package list and release record | [Release policy](docs/releases/policy.md#what-can-ship) · [0.3.0](docs/releases/v0.3.0.md) |
| Contributing, development, roadmap, and status | [Contributing](CONTRIBUTING.md) · [development guide](docs/development.md) · [project status](docs/status.md) · [roadmap](ROADMAP.md) |

The repository checks shared golden fixtures through Rust, Python, Node/browser WASM, and a host Dart adapter. No Dart/Pub package is published. The contracts describe bounded supported behavior; they do not claim complete linguistic coverage.

---

## Author & Maintainer

**Abishtakan Sivachandrathevan**
- GitHub: [@abishtakan](https://github.com/abishtakan)
- Project: [tamil-toolkit](https://github.com/abishtakan/tamil-toolkit)

---

## Contributing

Bug reports, documentation improvements, and sourced test cases are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow, [current project status](docs/status.md) for active and deferred work, and [ROADMAP.md](ROADMAP.md) for long-term integration milestones.

## License

Original code is [Apache-2.0 licensed][license] (see [NOTICE](NOTICE) for attribution). Unicode data, encoding maps, and other upstream material retain the terms recorded in [third-party notices](THIRD_PARTY_NOTICES.md).

[ci-badge]: https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=Rust%20CI
[ci]: https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml
[license-badge]: https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square
[license]: LICENSE
[crates-version]: https://img.shields.io/crates/v/tamil-toolkit?style=flat-square&logo=rust&label=crates.io
[crates-downloads]: https://img.shields.io/crates/d/tamil-toolkit?style=flat-square&label=total
[crates]: https://crates.io/crates/tamil-toolkit
[pypi-version]: https://img.shields.io/pypi/v/tamil-toolkit?style=flat-square&logo=pypi&logoColor=white
[pypi-downloads]: https://img.shields.io/pypi/dm/tamil-toolkit?style=flat-square&label=monthly
[pypi]: https://pypi.org/project/tamil-toolkit/
[pypistats]: https://pypistats.org/packages/tamil-toolkit
[npm-version]: https://img.shields.io/npm/v/tamil-toolkit?style=flat-square&logo=npm&label=npm
[npm-downloads]: https://img.shields.io/npm/dm/tamil-toolkit?style=flat-square&label=monthly
[npm]: https://www.npmjs.com/package/tamil-toolkit

The next candidate includes experimental bounded calendar APIs; see the [candidate scope and deferred work](docs/releases/numerals-calendar-candidate.md). Calendar acceptance suites remain planned.
