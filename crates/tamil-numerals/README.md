<div align="center">

# tamil-numerals

**Bounded TN/SL integers, exact INR/LKR amounts, rational fractions and Gregorian date formatting.**

[![crates.io version](https://img.shields.io/crates/v/tamil-numerals?style=flat-square)](https://crates.io/crates/tamil-numerals)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-numerals?style=flat-square&label=downloads)](https://crates.io/crates/tamil-numerals)
[![docs.rs](https://docs.rs/tamil-numerals/badge.svg)](https://docs.rs/tamil-numerals/0.1.0-alpha.2)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Number words** | Bounded formal Tamil Nadu and Sri Lankan profiles. |
| **Money** | Exact INR/LKR minor-unit amounts with no rounding. |
| **Fractions and dates** | Rational fractions and Gregorian civil-date formatting. |

Experimental alpha `0.1.0-alpha.2`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-numerals@=0.1.0-alpha.2
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-numerals = "=0.1.0-alpha.2"
```

## Example

```rust
use tamil_numerals::{Currency, Locale};

fn main() -> Result<(), String> {
    let amount = tamil_numerals::format_currency(102_550, Currency::LKR, Locale::SL)?;
    println!("{amount}");
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-numerals/0.1.0-alpha.2)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.2.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha 2 release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md)


## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
