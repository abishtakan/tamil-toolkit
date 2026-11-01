<div align="center">

# tamil-toolkit

**Tamil text tools for Rust, Python, and JavaScript.**

Unicode letters · Agara ordering · Tamil numerals · Legacy encodings

[![Rust CI][ci-badge]][ci]
[![MIT license][license-badge]][license]
[![GitHub stars][stars-badge]][stars]

[Capabilities](#capability-contracts) · [Quick start](#quick-start) · [Install](#installation) · [Contributing](CONTRIBUTING.md)

</div>

Work with Tamil letters, sort words, format numbers and dates, and convert
selected legacy encodings. A shared Rust implementation powers the native
Python package and the Node.js and browser WASM bindings.

## What’s included

| Task | Capabilities |
| --- | --- |
| **Work with Tamil text** | Tailored letter segmentation, Mei/Uyirmei splitting and composition, NFC/NFD normalization, and Unicode inspection. |
| **Order and match words** | Stable Mei-first Agara sorting, versioned sort keys, and keys for exact normalized matching. |
| **Format numbers and dates** | Tamil Nadu and Sri Lankan numeral profiles, integer words, exact INR/LKR amounts, fractions, and Gregorian dates. |
| **Convert legacy text** | Unicode ↔ Bamini text, bounded TSCII/TAB/TAM/Anjal byte profiles, and bounded LT-TM / IndoWord and Vanavil Avvaiyar 16-bit CID profiles. |

Normalization preserves joiners and non-Tamil text. Encoding conversion uses
explicit profiles; callers choose the source encoding. Unsupported input is
reported according to each profile's contract.

## Installation

Choose the SDK for your application:

| SDK | Install alpha 4 | Version | Downloads |
| --- | --- | --- | --- |
| **Rust 1.85+** | `cargo add tamil-toolkit@=0.1.0-alpha.4` | [![crates.io][crates-version]][crates] | [![crates.io total downloads][crates-downloads]][crates] |
| **Python 3.11+** | `python -m pip install tamil-toolkit==0.1.0a4` | [![PyPI][pypi-version]][pypi] | [![PyPI monthly downloads][pypi-downloads]][pypistats] |
| **Node.js 22+ / browsers** | `npm install tamil-toolkit@alpha` | [![npm alpha][npm-version]][npm] | [![npm monthly downloads][npm-downloads]][npm] |

**Public alpha:** APIs may change. npm’s `alpha` tag points to alpha 4;
`latest` still points to alpha 1. See the [release notes](CHANGELOG.md) and
[alpha 4 compatibility details](docs/releases/alpha-4.md#compatibility-and-scope).

Download badges track the umbrella package in each registry: total downloads
on crates.io and monthly downloads on PyPI and npm.

All six Rust crates are published at `0.1.0-alpha.4`: [`tamil-core`](https://crates.io/crates/tamil-core),
[`tamil-norm`](https://crates.io/crates/tamil-norm),
[`tamil-collate`](https://crates.io/crates/tamil-collate),
[`tamil-numerals`](https://crates.io/crates/tamil-numerals),
[`tamil-codec`](https://crates.io/crates/tamil-codec), and
[`tamil-toolkit`](https://crates.io/crates/tamil-toolkit).

**Alpha boundaries:** Bamini, TSCII, TAB, TAM, Anjal, LT-TM, and Vanavil conversions use
declared bounded profiles. LT-TM and Vanavil handle selected 16-bit CID/code sequences;
they do not parse PDFs or detect fonts automatically. These profiles do not
claim complete historical-font coverage. Other planned linguistic modules
and a Dart/Pub distribution are outside the published alpha. See the
[LT-TM contract](docs/specs/codec-lt-tm.md), [Vanavil contract](docs/specs/codec-vanavil.md), and [alpha 4 compatibility details](docs/releases/alpha-4.md#compatibility-and-scope).

## Quick start

These examples segment `தமிழ்` into three Tamil letters, then encode it as
Bamini. Python and JavaScript also show an exact currency amount: `102550`
minor units is `LKR 1,025.50`.

### Rust

```rust
use tamil_toolkit::{codec, core};

fn main() -> Result<(), String> {
    let text = "தமிழ்";
    println!("{}", core::get_letters(text).join(" | ")); // த | மி | ழ்
    println!("{}", codec::unicode_to_bamini(text)?); // jkpo;
    Ok(())
}
```

### Python

```python
import tamil_toolkit as tamil

text = "தமிழ்"
print(tamil.get_letters(text))  # ['த', 'மி', 'ழ்']
print(tamil.unicode_to_bamini(text))  # jkpo;
print(tamil.format_currency(102550, "LKR", "SL"))  # LKR 1,025.50
```

### JavaScript / TypeScript

```javascript
import * as tamil from "tamil-toolkit";

const text = "தமிழ்";
console.log(tamil.get_letters(text)); // [ 'த', 'மி', 'ழ்' ]
console.log(tamil.unicode_to_bamini(text)); // jkpo;
console.log(tamil.format_currency(102550, "LKR", "SL")); // LKR 1,025.50
```

Browser applications use the [`tamil-toolkit/web` entry point](bindings/js-wasm/README.md)
and must call `await init()` before using the API.

## Try the workbench locally

The workbench lets you try operations interactively and inspect returned text,
JSON, and Unicode scalars. With Rust 1.85+, Python 3.11+, Node 22+, pnpm 11.5+,
`uv`, and `just` installed, run these commands from the repository root:

```sh
just bootstrap
pnpm dev
```

Then open <http://127.0.0.1:5173/>. The [development guide](docs/development.md)
covers verification and contribution workflow.

## Capability contracts

| Looking for | Start here |
| --- | --- |
| Unicode letters, composition, and normalization | [Core contract](docs/specs/core-v0.1.md) |
| Agara sorting and search keys | [Collation contract](docs/specs/collate-v0.1.md) |
| Number words, currency, fractions, and dates | [Numerals contract](docs/specs/numerals-v0.1.md) · [fractions and dates](docs/specs/numerals-v0.2.md) |
| Bamini, bounded byte profiles, and LT-TM / Vanavil CID conversion | [Codec contract](docs/specs/codec-v0.1.md) · [LT-TM profile](docs/specs/codec-lt-tm.md) · [Vanavil profile](docs/specs/codec-vanavil.md) · [alpha 4 scope](docs/releases/alpha-4.md#compatibility-and-scope) |
| Rust API reference | [docs.rs/tamil-toolkit](https://docs.rs/tamil-toolkit/0.1.0-alpha.4/tamil_toolkit/) |
| Python and JavaScript/WASM SDK guides | [Python](bindings/python/README.md) · [JavaScript/WASM](bindings/js-wasm/README.md) |
| Published package list and release record | [Release policy](docs/releases/policy.md#what-can-ship) · [alpha 4](docs/releases/alpha-4.md) |
| Contributing, development, and current status | [Contributing](CONTRIBUTING.md) · [development guide](docs/development.md) · [project status](docs/status.md) |

The repository checks shared golden fixtures through Rust, Python, Node/browser
WASM, and a host Dart adapter. No Dart/Pub package is published. The contracts
describe bounded supported behavior; they do not claim complete linguistic
coverage.

## Contributing

Bug reports, documentation improvements, and sourced test cases are welcome.
Read [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and
[current project status](docs/status.md) for active and deferred work.

## License

Original code is [MIT licensed][license]. Unicode data, encoding maps, and
other upstream material retain the terms recorded in
[third-party notices](THIRD_PARTY_NOTICES.md).

[ci-badge]: https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=Rust%20CI
[ci]: https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml
[license-badge]: https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square
[license]: LICENSE
[stars-badge]: https://img.shields.io/github/stars/abishtakan/tamil-toolkit?style=flat-square
[stars]: https://github.com/abishtakan/tamil-toolkit/stargazers
[crates-version]: https://img.shields.io/crates/v/tamil-toolkit?style=flat-square&logo=rust&label=crates.io
[crates-downloads]: https://img.shields.io/crates/d/tamil-toolkit?style=flat-square&label=total
[crates]: https://crates.io/crates/tamil-toolkit
[pypi-version]: https://img.shields.io/pypi/v/tamil-toolkit?style=flat-square&logo=pypi&logoColor=white
[pypi-downloads]: https://img.shields.io/pypi/dm/tamil-toolkit?style=flat-square&label=monthly
[pypi]: https://pypi.org/project/tamil-toolkit/
[pypistats]: https://pypistats.org/packages/tamil-toolkit
[npm-version]: https://img.shields.io/npm/v/tamil-toolkit/alpha?style=flat-square&logo=npm&label=npm%20alpha
[npm-downloads]: https://img.shields.io/npm/dm/tamil-toolkit?style=flat-square&label=monthly
[npm]: https://www.npmjs.com/package/tamil-toolkit
