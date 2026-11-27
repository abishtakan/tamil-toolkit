<div align="center">

# tamil-lexicon

**Pure-Rust, zero-unsafe TMLPACK1/TMLPACK2 binary lexicon reader, pack registry, FST prefix/fuzzy/stem search, Mayangoli folding, reverse English gloss index, and lexical relations engine.**

[![crates.io version](https://img.shields.io/crates/v/tamil-lexicon?style=flat-square)](https://crates.io/crates/tamil-lexicon)
[![crates.io downloads](https://img.shields.io/crates/d/tamil-lexicon?style=flat-square&label=downloads)](https://crates.io/crates/tamil-lexicon)
[![docs.rs](https://docs.rs/tamil-lexicon/badge.svg)](https://docs.rs/tamil-lexicon/0.3.0)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![Apache-2.0 license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Example](#example) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Binary Packs (`TMLPACK2`)** | Deterministic SHA-256-verified block-compressed `.tlpack` reader/builder (`CompactPack`, `PackRegistry`) with zero embedded dictionary bytes and `#![forbid(unsafe_code)]`. |
| **Search & Lookup** | O(key) exact/prefix FST lookup (`define`, `prefix_search`), *Mayangoli*-folded search, reverse English-to-Tamil gloss search (`search_english`), bounded Damerau-Levenshtein `fuzzy_search`, and `longest_prefix_matches` for stem/morphology splitting. |
| **Facets & Relations** | Atomic domain/region/register filtering, precomputed facet counts (`LexiconStoreStats`), cursor pagination, and indexed symmetric relations (`SYNONYM`, `ANTONYM`, `RELATED`, `HYPERNYM`). |

Release `0.3.0`. Public APIs follow semantic versioning. This package provides bounded APIs and does not
attempt complete Tamil linguistic coverage.

## Install

```sh
cargo add tamil-lexicon@=0.3.0
```

Or add the exact alpha dependency to `Cargo.toml`:

```toml
[dependencies]
tamil-lexicon = "=0.3.0"
```

## Example

```rust
use tamil_lexicon::{LexiconProfile, LexiconSearchOptions, LexiconStore, PackRegistry};

fn main() -> Result<(), String> {
    let mut registry = PackRegistry::new();
    registry.load_auto(LexiconProfile::Open)?;
    let hits = registry.search_english("gratitude", &LexiconSearchOptions::default())?;
    println!("{} matches", hits.hits.len());
    Ok(())
}
```

## Documentation

- [API reference on docs.rs](https://docs.rs/tamil-lexicon/0.3.0)
- [Feature contract and examples](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/lexicon-v0.2.md)
- [Project overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Stable release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/v0.3.0.md)

## License

Original code is [Apache-2.0 licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE) (see [NOTICE](https://github.com/abishtakan/tamil-toolkit/blob/master/NOTICE) for attribution).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
Contributions are welcome; see the [contributor guide](https://github.com/abishtakan/tamil-toolkit/blob/master/CONTRIBUTING.md).
