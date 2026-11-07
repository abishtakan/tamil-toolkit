<div align="center">

# tamil-hyphen

**Syllable and orthographic boundary hyphenation for Tamil text.**

[![crates.io version](https://img.shields.io/crates/v/tamil-hyphen?style=flat-square)](https://crates.io/crates/tamil-hyphen)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-hyphen?style=flat-square&label=downloads)](https://crates.io/crates/tamil-hyphen)
[![docs.rs](https://docs.rs/tamil-hyphen/badge.svg)](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Operation | Behavior |
| --- | --- |
| **`hyphenate_word`** | Syllable-based hyphenation with strict Mei/Aytham coda binding and configurable letter margins. |
| **`hyphenation_points`** | Valid syllable boundary positions (`letter_index`, `byte_offset`) within a word. |
| **`hyphenate_text`** | Soft-hyphen (`\u{00AD}`) injection across full paragraphs, preserving URLs and non-Tamil tokens. |
| **`wrap_text`** | Deterministic line wrapping to target Tamil letter widths without breaking words at invalid points. |
| **`generate_patterns`** | Synthesizes phonotactically verified Frank Liang / Hunspell hyphenation patterns. |
| **`export_dic_file`** | Exports `hyph_ta_IN.dic` with `LEFTHYPHENMIN 2` and multi-locale support (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, `ta`). |
| **`package_oxt`** | Bundles the dictionary into a one-click LibreOffice extension (`tamil-hyphenation.oxt`). |

Experimental alpha `0.1.0-alpha.6`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-hyphen@=0.1.0-alpha.6
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-hyphen = "=0.1.0-alpha.6"
```

## Example

```rust
use tamil_hyphen::{hyphenate_word, hyphenate_text, wrap_text, HyphenationConfig};

fn main() {
    // Word hyphenation
    let word_res = hyphenate_word("தமிழ்நாடு", None).unwrap();
    println!("Syllables: {:?}", word_res.syllables);

    // Text soft-hyphenation (idempotent)
    let text = "தமிழ்நாடு மற்றும் பல்கலைக்கழகம் ஆகிய இரண்டும் செழித்து வளர்கின்றன.";
    let soft_hyphenated = hyphenate_text(text, None).unwrap();
    println!("{soft_hyphenated}");

    // Line wrapping with hyphenation
    let wrapped = wrap_text(text, 15, None).unwrap();
    for line in wrapped.lines {
        println!("{line}");
    }
}
```

## Documentation & Integrations

- [API reference on docs.rs](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
- [Hyphenation specification](https://github.com/abishtakan/tamil-toolkit/blob/master/specs/009-tamil-hyphen/spec.md)
- [DTP dictionary & extension specification](https://github.com/abishtakan/tamil-toolkit/blob/master/specs/011-tamil-hyphen-dic/spec.md)
- [LibreOffice installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/libreoffice.md)
- [Adobe InDesign installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/indesign.md)
- [Scribus installation guide](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/scribus.md)
- [Microsoft Word & Google Docs long-term integration roadmap](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/integrations/word-googledocs-roadmap.md)
- [Project overview & roadmap](https://github.com/abishtakan/tamil-toolkit/blob/master/ROADMAP.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
