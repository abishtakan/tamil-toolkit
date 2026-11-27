<div align="center">

# tamil-punarchi

**Sourced Nannool (Sutras 151–257) sandhi joining (Thonral, Thirithal, Keduthal, Iyalbu) and dictionary-free reverse split candidate generation.**

[![crates.io version](https://img.shields.io/crates/v/tamil-punarchi?style=flat-square)](https://crates.io/crates/tamil-punarchi)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-punarchi?style=flat-square&label=downloads)](https://crates.io/crates/tamil-punarchi)
[![docs.rs](https://docs.rs/tamil-punarchi/badge.svg)](https://docs.rs/tamil-punarchi/0.3.0)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Forward Sandhi (`join`)** | Deterministic *Nannool* (Sutras 151–257) joining across *Uyireeru*, *Meyyeeru*, and *Urupu* with *Vetrumai*/*Alvazhi* context and sutra-by-sutra derivation steps. |
| **Inverse Splitting (`split_candidates`)** | Dictionary-free bounded reverse-rule candidate generator returning `(first, second)` pairs, rule IDs, and surface spans. |
| **Rule Inspection (`rules`)** | Queryable sutra inventory and edition notes across *Ezhuttiyal*, *Padaviyal*, *Uyireeru*, *Meyyeeru*, and *Urupu*. |

Release `0.3.0`. Public APIs follow semantic versioning. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-punarchi@=0.3.0
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-punarchi = "=0.3.0"
```

## Example

```rust
use tamil_punarchi::{join, JoinOptions};

fn main() -> Result<(), String> {
    let result = join("மரம்", "அடி", &JoinOptions::default())?;
    println!("{} ({:?})", result.surface, result.transform);
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-punarchi/0.3.0)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/punarchi-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Stable release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/v0.3.0.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
