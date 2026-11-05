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
| **Format numbers and dates** | Tamil Nadu and Sri Lankan numeral profiles, integer words, exact INR/LKR amounts, fractions, and Gregorian dates. The unreleased v0.3 source contract also specifies bounded exact decimal strings and civil arithmetic. |
| **Use a bounded Tamil calendar** | The unreleased `thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2` profile converts Gregorian and Tamil solar dates, computes month boundaries, reports five panchangam limbs and civil-day transitions, bounded primary lunar-phase UTC events, calendar-year/month information and date arithmetic, and Rahukalam/Yamagandam/Kuligai daylight intervals. Coverage is 2024–2027 in declared TN/SL location boxes. Additive display APIs provide source-backed Tamil or Romanized labels, explicit digit styles and fixed templates; a comparison API returns both named profiles with contexts and semantic bases intact. The Thiruvalluvar operation is a named TN Thai-1 profile convention for 2025–2027 and does not claim official Gazette-year equivalence. Separately, official annual holiday rows are available for TN 2025–26 and SL 2026–27. Calendar suites remain planned for separate review. |
| **Use the classical Vakiya civil profile** | The unreleased `vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1` profile converts Gregorian/Tamil solar dates, reports all five limbs at instants and Ujjain mean-sunrise days, enumerates source-model years/months, and supports profile-based date arithmetic in the exposed solar-equation range. It uses the unmodified 1962 edition and Ujjain reference station; true local horizon sunrise/sunset and arbitrary-location corrections remain unavailable. Its suite remains planned. |
| **Convert legacy text** | Unicode ↔ Bamini text, bounded TSCII/TAB/TAM/Anjal byte profiles, and bounded LT-TM / IndoWord and Vanavil Avvaiyar 16-bit CID profiles. |

Normalization preserves joiners and non-Tamil text. Encoding conversion uses
explicit profiles; callers choose the source encoding. Unsupported input is
reported according to each profile's contract.

## Installation

Choose the SDK for your application:

| SDK | Install alpha 6 | Version | Downloads |
| --- | --- | --- | --- |
| **Rust 1.85+** | `cargo add tamil-toolkit@=0.1.0-alpha.6` | [![crates.io][crates-version]][crates] | [![crates.io total downloads][crates-downloads]][crates] |
| **Python 3.11+** | `python -m pip install tamil-toolkit==0.1.0a6` | [![PyPI][pypi-version]][pypi] | [![PyPI monthly downloads][pypi-downloads]][pypistats] |
| **Node.js 22+ / browsers** | `npm install tamil-toolkit@alpha` | [![npm alpha][npm-version]][npm] | [![npm monthly downloads][npm-downloads]][npm] |

**Public alpha:** APIs may change. npm’s `alpha` tag points to alpha 6;
`latest` still points to alpha 1. See the [release notes](CHANGELOG.md) and
[alpha 6 compatibility details](docs/releases/alpha-6.md#compatibility-and-scope).

Download badges track the umbrella package in each registry: total downloads
on crates.io and monthly downloads on PyPI and npm.

All six Rust crates are published at `0.1.0-alpha.6`: [`tamil-core`](https://crates.io/crates/tamil-core),
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
[LT-TM contract](docs/specs/codec-lt-tm.md), [Vanavil contract](docs/specs/codec-vanavil.md), and [alpha 6 compatibility details](docs/releases/alpha-6.md#compatibility-and-scope).

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

## Playground

A public playground offering practical, interactive tools powered by the toolkit packages is planned for a future release; planning and ideation will be handled in a later milestone.

## Capability contracts

| Looking for | Start here |
| --- | --- |
| Unicode letters, composition, and normalization | [Core contract](docs/specs/core-v0.1.md) |
| Agara sorting and search keys | [Collation contract](docs/specs/collate-v0.1.md) |
| Number words, currency, fractions, exact decimal strings, and civil arithmetic | [Numerals v0.1](docs/specs/numerals-v0.1.md) · [fractions and dates v0.2](docs/specs/numerals-v0.2.md) · [exact strings and civil arithmetic v0.3](docs/specs/numerals-v0.3.md) |
| Bounded calendar labels and inter-profile comparison | [Tamil display contract](docs/specs/calendar-tamil-display-v1.md) · [profile comparison contract](docs/specs/calendar-profile-comparison-v1.md) · [Thiruvalluvar convention contract](docs/specs/calendar-thiruvalluvar-year-v1.md) |
| Bounded Thirukanitham date conversion, panchangam, phases, arithmetic, daylight periods and cycle titles | [Profile contract](docs/specs/calendar-thirukanitham-v1.md) · [phase contract](docs/specs/calendar-lunar-phases-v1.md) · [arithmetic contract](docs/specs/calendar-solar-arithmetic-v1.md) · [cycle-title contract](docs/specs/calendar-year-cycle-v1.md) · [daylight-period contract](docs/specs/calendar-daylight-periods-v1.md) · [source research](docs/specs/numerals-calendar-source-research.md) |
| Authority-published holiday schedule snapshots | [Official schedule contract](docs/specs/calendar-official-holidays-v1.md) · [source research](docs/specs/numerals-calendar-source-research.md) |
| Bounded classical Vakiya civil, five-limb, arithmetic profile | [1962 edition contract](docs/specs/calendar-vakya-civil-v1.md) · [solar arithmetic contract](docs/specs/calendar-solar-arithmetic-v1.md) · [completion matrix](docs/specs/numerals-completion-plan.md) |
| Bamini, bounded byte profiles, and LT-TM / Vanavil CID conversion | [Codec contract](docs/specs/codec-v0.1.md) · [LT-TM profile](docs/specs/codec-lt-tm.md) · [Vanavil profile](docs/specs/codec-vanavil.md) · [alpha 6 scope](docs/releases/alpha-6.md#compatibility-and-scope) |
| Rust API reference | [docs.rs/tamil-toolkit](https://docs.rs/tamil-toolkit/0.1.0-alpha.6/tamil_toolkit/) |
| Python and JavaScript/WASM SDK guides | [Python](bindings/python/README.md) · [JavaScript/WASM](bindings/js-wasm/README.md) |
| Published package list and release record | [Release policy](docs/releases/policy.md#what-can-ship) · [alpha 6](docs/releases/alpha-6.md) |
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

The next candidate includes experimental bounded calendar APIs; see the
[candidate scope and deferred work](docs/releases/numerals-calendar-candidate.md).
Calendar acceptance suites remain planned.
