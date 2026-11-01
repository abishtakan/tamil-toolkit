<div align="center">

# tamil-codec

**Bamini conversion and bounded TSCII, TAB, TAM and Anjal byte profiles.**

[![crates.io version](https://img.shields.io/crates/v/tamil-codec?style=flat-square)](https://crates.io/crates/tamil-codec)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-codec?style=flat-square&label=downloads)](https://crates.io/crates/tamil-codec)
[![docs.rs](https://docs.rs/tamil-codec/badge.svg)](https://docs.rs/tamil-codec/0.1.0-alpha.2)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Bamini** | Explicit Unicode conversion using the declared Bamini profile. |
| **Byte profiles** | Bounded TSCII, TAB, TAM, and Anjal conversion. |
| **Limits** | No automatic detection or complete historical-font coverage. |

Experimental alpha `0.1.0-alpha.2`. APIs may change before stability. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-codec@=0.1.0-alpha.2
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-codec = "=0.1.0-alpha.2"
```

## Example

```rust
use tamil_codec::{bamini_to_unicode, unicode_to_bamini, ErrorPolicy};

fn main() -> Result<(), String> {
    let legacy = unicode_to_bamini("தமிழ்")?;
    let text = bamini_to_unicode(&legacy, ErrorPolicy::Strict)?;
    println!("{legacy} -> {text}");
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-codec/0.1.0-alpha.2)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md#compatibility-and-scope)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Alpha 2 release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md)


LT-TM CID conversion is present in current workspace source but is **not** included in the published `0.1.0-alpha.2` crate. See the [unreleased workspace specification](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/codec-lt-tm.md).

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
