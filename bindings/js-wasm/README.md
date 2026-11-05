<div align="center">

# tamil-toolkit for JavaScript and TypeScript

**Rust-backed Tamil text tools for Node.js and browsers.**

[![npm alpha version](https://img.shields.io/npm/v/tamil-toolkit/alpha?style=flat-square&label=npm%20alpha)](https://www.npmjs.com/package/tamil-toolkit)
[![Monthly downloads](https://img.shields.io/npm/dm/tamil-toolkit?style=flat-square&label=monthly)](https://www.npmjs.com/package/tamil-toolkit)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)

[Install](#install) · [Node quick start](#node-quick-start) · [Documentation](#documentation)

</div>

## What’s included

| Area | Capabilities |
| --- | --- |
| **Unicode and letters** | NFC/NFD normalization, tailored Tamil letter operations, and inspection. |
| **Ordering** | Stable Mei-first Agara collation and versioned sort/search keys. |
| **Numbers and dates** | Bounded TN/SL number words, exact INR/LKR amounts, fractions, and Gregorian dates. |
| **Tamil calendar** | Unreleased bounded Thirukanitham Gregorian/solar conversion and five-limb panchangam reports for declared TN/SL coordinates in 2024–2027. Its custom profile does not claim every publisher's Drik output; calendar fixtures remain planned. |
| **Legacy conversion** | Bamini text conversion, bounded TSCII/TAB/TAM/Anjal byte profiles, and LT-TM / IndoWord 16-bit CID conversion. |

TypeScript and WASM are thin bindings to the shared Rust implementation.

## Install

Node.js 22+ is supported. Install alpha 6 from npm’s `alpha` dist-tag:

```sh
npm install tamil-toolkit@alpha
```

The `alpha` tag points to `0.1.0-alpha.6`; npm’s `latest` tag still points to
`0.1.0-alpha.1`. The version badge above tracks the `alpha` tag.

## Node quick start

```javascript
import * as tamil from "tamil-toolkit";

const text = "தமிழ்";
console.log(tamil.get_letters(text).join(" | ")); // த | மி | ழ்
console.log(tamil.unicode_to_bamini(text)); // jkpo;
console.log(tamil.format_currency(102550, "LKR", "SL")); // LKR 1,025.50
```

## Browser quick start

Use the `/web` entry point and initialize WebAssembly before calling the API:

```javascript
import { init, get_letters } from "tamil-toolkit/web";

await init();
console.log(get_letters("தமிழ்").join(" | "));
```

The host page or bundler must serve the packaged WASM asset as an ES module
asset. The Node entry point initializes its native WASM module automatically.

## Alpha 6 scope

The npm `0.1.0-alpha.6` package includes the capabilities listed above. The
shared `execute` API exposes `lt_tm_codes_to_unicode`, `lt_tm_text_to_unicode`,
`unicode_to_lt_tm_codes`, and `unicode_to_lt_tm_text`. LT-TM conversion handles
selected 16-bit code sequences; it does not parse PDFs, select font runs, or
detect encodings. The profile does not claim complete historical-font coverage.
APIs may change.

Other planned linguistic modules, the private PDF extraction utility, and
Dart/Pub distribution are not published.

```javascript
import * as tamil from "tamil-toolkit";

const codes = tamil.execute({ op: "unicode_to_lt_tm_codes", input: { text: "தமிழ்" } });
const text = tamil.execute({ op: "lt_tm_codes_to_unicode", input: { codes } });
```

## Documentation

- [API and feature overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [JavaScript/WASM API declarations](https://github.com/abishtakan/tamil-toolkit/tree/master/bindings/js-wasm)
- [Unicode/core contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Collation contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/collate-v0.1.md)
- [Numerals, fractions, and dates](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.2.md)
- [Codec contract and alpha 3 limits](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-6.md#compatibility-and-scope)
- [LT-TM CID profile contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/codec-lt-tm.md)
- [Third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md)

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).
