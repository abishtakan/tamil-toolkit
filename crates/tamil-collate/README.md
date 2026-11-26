<div align="center">

# tamil-collate

**Versioned Mei-first Agara dictionary ordering and canonical sort/search keys.**

[![crates.io version](https://img.shields.io/crates/v/tamil-collate?style=flat-square)](https://crates.io/crates/tamil-collate)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-collate?style=flat-square&label=downloads)](https://crates.io/crates/tamil-collate)
[![docs.rs](https://docs.rs/tamil-collate/badge.svg)](https://docs.rs/tamil-collate/0.2.0)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Ordering** | Stable Mei-first `agara-v1` comparison and sorting. |
| **Keys** | Versioned numeric sort keys and canonical exact-match search keys. |

Release `0.2.0`. Public APIs follow semantic versioning. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-collate@=0.2.0
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-collate = "=0.2.0"
```

## Example

```rust
fn main() {
    let words = vec!["ஆ".to_owned(), "அ".to_owned()];
    let sorted = tamil_collate::sort_words(&words);
    println!("{}", sorted.join(" | "));
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-collate/0.2.0)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/collate-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Stable release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/v0.2.0.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
