<div align="center">

# tamil-numerals

**Bounded TN/SL number words, exact decimal and INR/LKR strings, Unicode 17 symbols, traditional numerals, fractions, Gregorian civil arithmetic, bounded Thirukanitham and classical Vākyakaraṇa calendar profiles, selected TN observance rules, and official annual holiday schedules.**

[![crates.io version](https://img.shields.io/crates/v/tamil-numerals?style=flat-square)](https://crates.io/crates/tamil-numerals)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-numerals?style=flat-square&label=downloads)](https://crates.io/crates/tamil-numerals)
[![docs.rs](https://docs.rs/tamil-numerals/badge.svg)](https://docs.rs/tamil-numerals/0.1.0-alpha.5)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Number words** | Bounded formal Tamil Nadu and Sri Lankan profiles. |
| **Exact strings** | Bounded decimal parse/format, percentages, mixed fractions, exact numeric ranges, and INR/LKR major-unit amounts without rounding. |
| **Symbols and traditional integers** | Unicode 17 Tamil numeric metadata and canonical CLDR traditional integer parse/format. |
| **Fractions and dates** | Rational fractions plus validated Gregorian parsing, weekday, arithmetic, differences, and intervals. |
| **Tamil calendar** | Bounded Thirukanitham Drik solar-date conversion and five-limb day/instant reports for the declared 2024–2027 TN/SL location ranges; a named Nava Panchangam/Tamil-rule TN subset for Puthandu, Pongal, Bhogi, Mattu Pongal and Amavasya/Pournami Aparahna selection with sunrise fallback; separately sourced annual holiday rows for TN 2025–26 and SL 2026–27. Vakiya and Sri Lanka observances are unsupported, and observance/calendar fixture suites remain planned. |
| **Historical calendar kernels** | Unreleased source-pinned 1962 Vakiya solar and lunar calculations, including a caller-input local-sunrise correction; calendar fixtures remain planned. |

Experimental alpha `0.1.0-alpha.5`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage. This candidate includes owner-approved numerals v0.3 and experimental, bounded calendar APIs. Calendar acceptance suites remain planned and their selected review runs are separate from active numeral parity. Thirukanitham, Ujjain mean-sunrise Vakiya, named TN observances and annual holiday snapshots have explicit coverage. Arbitrary-location Vakiya daylight, official era reconciliation and Krishna Jayanthi remain deferred. See docs/releases/numerals-calendar-candidate.md for scope and limitations.

## Install

```sh
cargo add tamil-numerals@=0.1.0-alpha.5
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-numerals = "=0.1.0-alpha.5"
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

- [API reference on docs.rs](https://docs.rs/tamil-numerals/0.1.0-alpha.5)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.3.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-5.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
