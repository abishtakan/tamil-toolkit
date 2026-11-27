<div align="center">

# tamil-tokenize

**Offline, source-preserving Tamil word and sentence segmentation with exact UTF-8 byte and written-unit offsets, attested abbreviation handling, and opt-in stopword profiles.**

[![crates.io version](https://img.shields.io/crates/v/tamil-tokenize?style=flat-square)](https://crates.io/crates/tamil-tokenize)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-tokenize?style=flat-square&label=downloads)](https://crates.io/crates/tamil-tokenize)
[![docs.rs](https://docs.rs/tamil-tokenize/badge.svg)](https://docs.rs/tamil-tokenize/0.3.0)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Word Tokenization** | Source-preserving UAX #29 tailored word segmentation with zero-based UTF-8 byte and written-unit offsets (`tokenize_words`). |
| **Sentence Segmentation** | Sentence boundaries honoring attested Tamil abbreviations (`திரு.`, `மு.க.`, `பி.ப.`, `மு.ப.`, `எ.கா.`, `ரூ.`) and hard separators (`segment_sentences`). |
| **Stopwords** | Opt-in `none`, `conservative`, and `broad` profiles preserving original token coordinates (`StopwordProfile`). |

Release `0.3.0`. Public APIs follow semantic versioning. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-tokenize@=0.3.0
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-tokenize = "=0.3.0"
```

## Example

```rust
use tamil_tokenize::{segment_sentences, tokenize_words, StopwordProfile};

fn main() {
    let text = "திரு. குமார் வந்தார்.";
    let words = tokenize_words(text, StopwordProfile::None);
    let sentences = segment_sentences(text);
    println!("{} words, {} sentences", words.len(), sentences.len());
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-tokenize/0.3.0)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/tokenize-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Stable release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/v0.3.0.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
