<div align="center">

# tamil-translit

**Lossless Tamil orthographic romanization (ISO 15919, Madras Lexicon, ITRANS, Harvard-Kyoto) and deterministic offline input (Tamil99, Anjal phonetic, Suratha Bamini, Phonetic v1).**

[![crates.io version](https://img.shields.io/crates/v/tamil-translit?style=flat-square)](https://crates.io/crates/tamil-translit)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-translit?style=flat-square&label=downloads)](https://crates.io/crates/tamil-translit)
[![docs.rs](https://docs.rs/tamil-translit/badge.svg)](https://docs.rs/tamil-translit/0.1.0-alpha.10)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Scholarly Romanization** | Lossless bidirectional ISO 15919, Madras Lexicon, ITRANS, and Harvard-Kyoto transliteration (`transliterate`). |
| **Offline Input** | Deterministic Tamil99, Anjal phonetic, Suratha Bamini, and rule-based Phonetic/Tanglish v1 input (`transliterate`). |

Experimental alpha `0.1.0-alpha.10`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-translit@=0.1.0-alpha.10
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-translit = "=0.1.0-alpha.10"
```

## Example

```rust
use tamil_translit::{transliterate, Direction, Scheme};

fn main() -> Result<(), String> {
    let roman = transliterate("தமிழ்", Scheme::Iso15919, Direction::ToLatin)?;
    let back = transliterate(&roman, Scheme::Iso15919, Direction::ToTamil)?;
    println!("{roman} -> {back}");
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-translit/0.1.0-alpha.10)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/translit-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-10.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
