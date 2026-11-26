<div align="center">

# tamil-norm

**NFC and NFD normalization for Tamil and mixed-script text, with joiners preserved.**

[![crates.io version](https://img.shields.io/crates/v/tamil-norm?style=flat-square)](https://crates.io/crates/tamil-norm)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-norm?style=flat-square&label=downloads)](https://crates.io/crates/tamil-norm)
[![docs.rs](https://docs.rs/tamil-norm/badge.svg)](https://docs.rs/tamil-norm/0.2.0)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Operation | Behavior |
| --- | --- |
| **NFC/NFD** | Canonical Unicode normalization for Tamil and mixed-script text. |
| **Preservation** | Non-Tamil text and ZWJ/ZWNJ joiners are retained. |

Release `0.2.0`. Public APIs follow semantic versioning. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-norm@=0.2.0
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-norm = "=0.2.0"
```

## Example

```rust
fn main() {
    let decomposed = tamil_norm::normalize_nfd("தமிழ்");
    let normalized = tamil_norm::normalize_nfc(&decomposed);
    println!("{normalized}");
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-norm/0.2.0)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Stable release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/v0.2.0.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
