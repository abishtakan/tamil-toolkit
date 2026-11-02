<div align="center">

# tamil-toolkit

**Unified Rust entry point for Tamil text, ordering, bounded exact numerals, civil arithmetic, Thirukanitham and classical Vākyakaraṇa profiles, selected TN observance rules, official annual holiday schedules, and legacy conversion APIs.**

[![crates.io version](https://img.shields.io/crates/v/tamil-toolkit?style=flat-square)](https://crates.io/crates/tamil-toolkit)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-toolkit?style=flat-square&label=downloads)](https://crates.io/crates/tamil-toolkit)
[![docs.rs](https://docs.rs/tamil-toolkit/badge.svg)](https://docs.rs/tamil-toolkit/0.1.0-alpha.5)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Text** | Unicode letter operations, normalization, and inspection. |
| **Ordering and numbers** | Agara sorting, Tamil number words, bounded exact numeric strings and currency amounts, symbol metadata, fractions, and Gregorian civil arithmetic. |
| **Tamil calendar** | Bounded Thirukanitham Drik conversion and panchangam reports, a named Nava Panchangam/Tamil-rule TN subset for solar festivals and Amavasya/Pournami Aparahna selection with sunrise fallback, and selected authority-published TN/SL annual holiday schedules; Vakiya and Sri Lanka observances are unsupported and calendar fixture suites remain planned. |
| **Historical calendar kernels** | Unreleased source-pinned 1962 Vakiya solar and lunar calculations; full Vakiya date/location/five-limb coverage is not implemented. |
| **Legacy conversion** | Bamini plus bounded TSCII, TAB, TAM, Anjal, LT-TM / IndoWord, and Vanavil profiles. |

Experimental alpha `0.1.0-alpha.5`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage. This candidate includes owner-approved numerals v0.3 and experimental, bounded calendar APIs. Calendar acceptance suites remain planned and their selected review runs are separate from active numeral parity. Thirukanitham, Ujjain mean-sunrise Vakiya, named TN observances and annual holiday snapshots have explicit coverage. Arbitrary-location Vakiya daylight, official era reconciliation and Krishna Jayanthi remain deferred. See docs/releases/numerals-calendar-candidate.md for scope and limitations.

## Install

```sh
cargo add tamil-toolkit@=0.1.0-alpha.5
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-toolkit = "=0.1.0-alpha.5"
```

## Example

```rust
use tamil_toolkit::{codec, core, numerals};

fn main() -> Result<(), String> {
    let text = "தமிழ்";
    println!("{}", core::get_letters(text).join(" | "));
    println!("{}", codec::unicode_to_bamini(text)?);
    let codes = codec::unicode_to_lt_tm_codes(text)?;
    println!("{:?} -> {}", codes, codec::lt_tm_codes_to_unicode(&codes, codec::ErrorPolicy::Strict)?);
    let amount = numerals::parse_decimal("123.45", "latin", "none", false)?;
    println!("{}", numerals::format_currency_decimal(&amount, numerals::Currency::LKR, numerals::Locale::SL)?);
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-toolkit/0.1.0-alpha.5)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/README.md#capability-contracts)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-5.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
