<div align="center">

# tamil-calendar

**Tamil calendar systems, Thirukanitham, Vakiya, panchangam, and observances.**

[![crates.io version](https://img.shields.io/crates/v/tamil-calendar?style=flat-square)](https://crates.io/crates/tamil-calendar)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-calendar?style=flat-square&label=downloads)](https://crates.io/crates/tamil-calendar)
[![docs.rs](https://docs.rs/tamil-calendar/badge.svg)](https://docs.rs/tamil-calendar/0.1.0-alpha.7)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Tamil calendar** | Bounded Thirukanitham Drik solar-date conversion and five-limb panchangam. |
| **Observances** | Tamil Nadu festival rules and official annual holiday schedules. |
| **Historical kernels** | Classical Vākyakaraṇa solar, lunar, and civil timekeeping algorithms. |

Experimental alpha `0.1.0-alpha.7`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-calendar@=0.1.0-alpha.7
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-calendar = "=0.1.0-alpha.7"
```

## Example

```rust
use tamil_calendar::tamil_year_cycle_info;

fn main() -> Result<(), String> {
    let year = tamil_year_cycle_info(2026, 1)?;
    println!("{}: {}", year.cycle_number, year.tamil);
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-calendar/0.1.0-alpha.7)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/calendar-year-cycle-v1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-7.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
