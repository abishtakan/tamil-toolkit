<div align="center">

# tamil-core

**Unicode normalization, tailored Ezhuthu iteration, Mei/Uyir composition and scalar inspection.**

[![crates.io version](https://img.shields.io/crates/v/tamil-core?style=flat-square)](https://crates.io/crates/tamil-core)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-core?style=flat-square&label=downloads)](https://crates.io/crates/tamil-core)
[![docs.rs](https://docs.rs/tamil-core/badge.svg)](https://docs.rs/tamil-core/0.1.0-alpha.2)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Segmentation** | Tailored Tamil letter clusters via `get_letters` or the borrowed `Letters` iterator. |
| **Normalization** | NFC/NFD normalization and scalar-level inspection. |
| **Ezhuthu** | Mei/Uyir splitting and composition. |

Experimental alpha `0.1.0-alpha.2`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-core@=0.1.0-alpha.2
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-core = "=0.1.0-alpha.2"
```

## Example

```rust
use tamil_core::{get_letters, Letters};

fn main() {
    let text = "தமிழ்";
    println!("{}", get_letters(text).join(" | "));
    assert_eq!(Letters::new(text).count(), 3);
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-core/0.1.0-alpha.2)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha 2 release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md)


## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
