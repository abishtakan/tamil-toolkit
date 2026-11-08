<div align="center">

# tamil-hyphen

### Syllable and Orthographic Boundary Hyphenation & DTP Engine for Tamil Text

**Syllabic hyphenation · Coda binding · Soft-hyphen (`\u{00AD}`) injection · Responsive line wrapping · Hunspell `.dic` pattern generator · LibreOffice extension (`tamil-hyphenation.oxt`)**

[![crates.io version](https://img.shields.io/crates/v/tamil-hyphen?style=flat-square)](https://crates.io/crates/tamil-hyphen)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-hyphen?style=flat-square&label=downloads)](https://crates.io/crates/tamil-hyphen)
[![docs.rs](https://docs.rs/tamil-hyphen/badge.svg)](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Quick Start](#example) · [DTP Integrations](#desktop-publishing-integrations) · [Documentation](#documentation--integrations) · [License](#license)

</div>

---

**tamil-hyphen** provides deterministic, linguistically authentic syllable hyphenation and line-wrapping for the Tamil language. Built to solve the long-standing desktop publishing (DTP) challenge of broken Tamil ligatures, orphaned pulli marks, and illegal word splits in books, newspapers, gazettes, and web typography.

---

## What is Included

| Operation | Linguistic Behavior |
| --- | --- |
| **`hyphenate_word`** | Syllable-based hyphenation with strict Mei/Aytham coda binding and configurable letter margins (`left_min`, `right_min`). Prevents breaking before pure consonants or after vowel markers. |
| **`hyphenation_points`** | Enumerates all valid orthographic syllable boundary positions (`letter_index`, `byte_offset`) within a word. |
| **`hyphenate_text`** | Idempotent soft-hyphen (`\u{00AD}`) injection across full paragraphs, preserving URLs, email addresses, and non-Tamil tokens. |
| **`wrap_text`** | Deterministic, responsive line wrapping to target Tamil visual letter widths without breaking words at invalid phonetic points. |
| **`generate_patterns`** | Synthesizes phonotactically verified Frank Liang / Hunspell hyphenation patterns for publishing systems. |
| **`export_dic_file`** | Exports canonical `hyph_ta_IN.dic` with `LEFTHYPHENMIN 2` and multi-locale support (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, `ta`). |
| **`package_oxt`** | Bundles the dictionary into a one-click LibreOffice / Apache OpenOffice extension (`tamil-hyphenation.oxt`). |

---

## Install

```sh
cargo add tamil-hyphen@=0.1.0-alpha.6
```

Or add the exact dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-hyphen = "=0.1.0-alpha.6"
```

---

## Example

```rust
use tamil_hyphen::{hyphenate_word, hyphenate_text, wrap_text, HyphenationConfig};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Single Word Hyphenation (syllable segmentation with coda attachment)
    let word_res = hyphenate_word("தமிழ்நாடு", None)?;
    println!("Syllables: {:?}", word_res.syllables);
    // Syllables: ["தமிழ்", "நா", "டு"]

    // 2. Full Text Soft-Hyphenation (\u{00AD} injection for web & DTP)
    let paragraph = "தமிழ்நாடு மற்றும் பல்கலைக்கழகம் ஆகிய இரண்டும் செழித்து வளர்கின்றன.";
    let soft_hyphenated = hyphenate_text(paragraph, None)?;
    println!("With soft-hyphens: {soft_hyphenated}");

    // 3. Responsive Column Wrapping without breaking Tamil glyphs
    let wrapped = wrap_text(paragraph, 15, None)?;
    for (i, line) in wrapped.lines.iter().enumerate() {
        println!("Line {}: {}", i + 1, line);
    }

    Ok(())
}
```

---

## Desktop Publishing Integrations

`tamil-hyphen` powers native hyphenation in industry-standard typesetting software:

- 📄 **LibreOffice / OpenOffice**: Direct support via packaged extension `tamil-hyphenation.oxt`. Supports locales `ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, and generic `ta`.
- 🎨 **Adobe InDesign**: Integration guide for importing generated Hunspell `.dic` dictionary files into InDesign's dictionary directory for justified book printing.
- 📰 **Scribus**: Open-source DTP hyphenation dictionary setup.
- 📝 **Microsoft Word & Google Docs**: Strategic roadmap for soft-hyphen macro injection and OOXML `<w:softHyphen/>` rendering.

---

## Documentation & Integrations

- [API reference on docs.rs](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
- [Hyphenation specification](https://github.com/abishtakan/tamil-toolkit/blob/master/specs/009-tamil-hyphen/spec.md)
- [DTP dictionary & extension specification](https://github.com/abishtakan/tamil-toolkit/blob/master/specs/011-tamil-hyphen-dic/spec.md)
- [LibreOffice installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/libreoffice.md)
- [Adobe InDesign installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/indesign.md)
- [Scribus installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/scribus.md)
- [Microsoft Word & Google Docs long-term integration roadmap](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/word-googledocs-roadmap.md)
- [Project overview & roadmap](https://github.com/abishtakan/tamil-toolkit/blob/master/ROADMAP.md)

---

## Author & Maintainer

**Abishtakan Sivachandrathevan** ([@abishtakan](https://github.com/abishtakan))

---

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).

---

## Keywords & Search Queries

`tamil hyphenation`, `tamil line break`, `tamil libreoffice extension`, `tamil indesign hyphenation`, `tamil dtp typesetting`, `hunspell tamil dictionary`, `tamil soft hyphen`, `tamil text wrapping`, `asai hyphenation`.
