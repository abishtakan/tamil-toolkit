<div align="center">

# tamil-hyphen

**Syllable breakdown, prosodic Asai segmentation, soft hyphenation, and publication-grade line wrapping.**

[![crates.io version](https://img.shields.io/crates/v/tamil-hyphen?style=flat-square)](https://crates.io/crates/tamil-hyphen)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-hyphen?style=flat-square&label=downloads)](https://crates.io/crates/tamil-hyphen)
[![docs.rs](https://docs.rs/tamil-hyphen/badge.svg)](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Syllable breakdown** | Orthographic syllable and prosodic *Asai* segment partitioning (`hyphenate_word`, `hyphenation_points`). |
| **Text Hyphenation** | Full paragraph soft hyphenation preserving punctuation, whitespace, and non-Tamil runs (`hyphenate_text`). |
| **Line Wrapping** | Publication-grade line wrapping with customizable margins and delimiters (`wrap_text`). |
| **OpenXML & Dictionaries** | Batch OOXML Word document processing (`process_docx_file`), Frank Liang dictionary export (`export_dic_file`), and LibreOffice extension bundling (`package_oxt`). |

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
use tamil_hyphen::{hyphenate_word, HyphenationConfig};

fn main() -> Result<(), String> {
    let word = "பல்கலைக்கழகம்";
    let config = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 3,
        right_min: 3,
    };
    let result = hyphenate_word(word, Some(&config))?;
    println!("{} -> {}", result.original, result.hyphenated);
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-hyphen/0.1.0-alpha.6)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/hyphen-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-6.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
