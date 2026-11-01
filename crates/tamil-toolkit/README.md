<div align="center">

# tamil-toolkit

**Unified Rust entry point for published Tamil text, ordering, numerals, and bounded legacy conversion APIs.**

[![crates.io version](https://img.shields.io/crates/v/tamil-toolkit?style=flat-square)](https://crates.io/crates/tamil-toolkit)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-toolkit?style=flat-square&label=downloads)](https://crates.io/crates/tamil-toolkit)
[![docs.rs](https://docs.rs/tamil-toolkit/badge.svg)](https://docs.rs/tamil-toolkit/0.1.0-alpha.3)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Text** | Unicode letter operations, normalization, and inspection. |
| **Ordering and numbers** | Agara sorting, number words, exact amounts, fractions, and dates. |
| **Legacy conversion** | Bamini plus bounded TSCII, TAB, TAM, Anjal, LT-TM / IndoWord, and Vanavil profiles. |

Experimental alpha `0.1.0-alpha.3`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-toolkit@=0.1.0-alpha.3
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-toolkit = "=0.1.0-alpha.3"
```

## Example

```rust
use tamil_toolkit::{codec, core};

fn main() -> Result<(), String> {
    let text = "தமிழ்";
    println!("{}", core::get_letters(text).join(" | "));
    println!("{}", codec::unicode_to_bamini(text)?);
    let codes = codec::unicode_to_lt_tm_codes(text)?;
    println!("{:?} -> {}", codes, codec::lt_tm_codes_to_unicode(&codes, codec::ErrorPolicy::Strict)?);
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-toolkit/0.1.0-alpha.3)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/README.md#capability-contracts)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-3.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
