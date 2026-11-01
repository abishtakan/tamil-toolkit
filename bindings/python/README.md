<div align="center">

# tamil-toolkit for Python

**Rust-backed Tamil text tools for CPython.**

[![PyPI version](https://img.shields.io/pypi/v/tamil-toolkit?style=flat-square)](https://pypi.org/project/tamil-toolkit/)
[![Monthly downloads](https://img.shields.io/pypi/dm/tamil-toolkit?style=flat-square&label=monthly)](https://pypistats.org/packages/tamil-toolkit)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Quick start](#quick-start) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Unicode and letters** | NFC/NFD normalization, tailored Tamil letter operations, and inspection. |
| **Ordering** | Stable Mei-first Agara collation and versioned sort/search keys. |
| **Numbers and dates** | Bounded TN/SL number words, exact INR/LKR amounts, fractions, and Gregorian dates. |
| **Legacy conversion** | Bamini text conversion and bounded TSCII, TAB, TAM, and Anjal byte profiles. |

Python is a thin binding to the shared Rust implementation.

## Install

Python 3.11+ with GIL-enabled CPython is supported. Install the published alpha:

```sh
python -m pip install tamil-toolkit==0.1.0a2
```

## Quick start

```python
import tamil_toolkit as tamil

text = "தமிழ்"
print(" | ".join(tamil.get_letters(text)))  # த | மி | ழ்
print(tamil.unicode_to_bamini(text))  # jkpo;
print(tamil.format_currency(102550, "LKR", "SL"))  # LKR 1,025.50
print(tamil.format_fraction(2, 4))  # 1/2
```

`102550` is an exact amount in minor units. The numeral APIs support bounded
TN/SL profiles and INR/LKR amounts.

## Alpha 2 scope

The published PyPI `0.1.0a2` package includes the capabilities listed above.
Byte conversion uses explicit bounded profiles; it does not guess encodings or
claim complete historical-font coverage. APIs may change.

LT-TM CID conversion is present in current workspace source but is **not** in
the published `0.1.0a2` package. Other planned linguistic modules and Dart/Pub
distribution are not published.

## Documentation

- [API and feature overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [Unicode/core contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Collation contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/collate-v0.1.md)
- [Numerals, fractions, and dates](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.2.md)
- [Codec contract and alpha 2 limits](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md#compatibility-and-scope)
- [LT-TM workspace specification (unreleased)](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/codec-lt-tm.md)
- [Python package API declarations](https://github.com/abishtakan/tamil-toolkit/blob/master/bindings/python/python/tamil_toolkit/__init__.py)
- [Third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md)

The wheels target CPython 3.11+ through the stable abi3 interface. Source builds
require Rust 1.85+. See the [alpha 2 release record](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-2.md)
for artifact details.

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
