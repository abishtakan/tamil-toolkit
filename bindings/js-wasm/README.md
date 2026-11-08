<div align="center">

# tamil-toolkit for JavaScript & TypeScript

### High-Performance Tamil Text Processing, Unicode & Font Transcoder for Node.js and Browsers

**Zero-dependency WebAssembly · Bamini / TSCII / TAB / TAM / Vanavil font conversion · Grapheme segmentation · Agara varisai sorting · Currency & Numerals · 100% offline & private**

[![npm alpha version](https://img.shields.io/npm/v/tamil-toolkit/alpha?style=flat-square&logo=npm&label=npm%20alpha)](https://www.npmjs.com/package/tamil-toolkit)
[![npm monthly downloads](https://img.shields.io/npm/dm/tamil-toolkit?style=flat-square&label=monthly)](https://www.npmjs.com/package/tamil-toolkit)
[![CI](https://img.shields.io/github/actions/workflow/status/abishtakan/tamil-toolkit/ci.yml?branch=master&style=flat-square&label=CI)](https://github.com/abishtakan/tamil-toolkit/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/github/license/abishtakan/tamil-toolkit?style=flat-square)](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE)
[![TypeScript types](https://img.shields.io/badge/types-included-blue?style=flat-square&logo=typescript)](bindings/js-wasm)
[![WebAssembly](https://img.shields.io/badge/WASM-100%25%20offline-blueviolet?style=flat-square&logo=webassembly)](bindings/js-wasm)

[Install](#install) · [Node Quick Start](#node-quick-start) · [Browser Quick Start](#browser-quick-start) · [Use Cases](#practical-web-recipes) · [Documentation](#documentation) · [License](#license)

</div>

---

**tamil-toolkit** is the premier, high-performance Tamil text and Unicode processing library for JavaScript, TypeScript, Node.js, and modern web browsers. Powered by compiled Rust WebAssembly (WASM), it brings zero-latency, deterministic Tamil computing to frontend web apps, serverless functions, and backend services.

Runs **100% client-side** with zero network tracking, zero external dependencies, and complete offline PWA compatibility.

---

## What is Included

| Domain | Capabilities in JS / TS / WASM |
|---|---|
| 🔤 **Unicode & Letters** | NFC/NFD normalization, tailored Tamil grapheme segmentation (`get_letters`), Mei/Uyir splitting, and scalar inspection. Handles complex ligatures like `க்ஷ` and `ஸ்ரீ`. |
| 🔄 **Legacy Font Transcoder** | Universal bidirectional transcoding between Unicode and legacy Tamil encoding formats: **Bamini**, **TSCII**, **TAB**, **TAM**, **Anjal**, **Vanavil Avvaiyar**, and **LT-TM / IndoWord**. |
| 🔠 **Agara Varisai Collation** | Traditional Tamil dictionary alphabetical sorting with stable Mei-first collation order (`sort_words`, `compare`). |
| 🔢 **Numerals & Currency** | Bounded Tamil Nadu (`ta-IN`) and Sri Lankan (`ta-LK`) number-to-words conversion, exact financial currency formatting (INR/LKR) with zero floating-point drift, and Gregorian civil dates. |
| 🎵 **Phonology & Prosody** | Tholkappiyam-grounded phonology: mora (*Maathirai*) duration calculation, letter quantity classification (`is_kuril`, `is_nedil`, `is_mei`, `is_aytham`), stop-nasal cognates (*Ina Ezhuthu*), and syllable nuclei (*Olippasai*). |
| 📅 **Solar Calendar & Panchangam** | Classical Thirukanitham Drik and 1962 Vākyakaraṇa calendar models: Gregorian ↔ Tamil solar date conversion, 60-year Jovian cycles, and five-limb astronomical panchangam calculations. |

---

## Install

Node.js 22+ is supported. Install alpha 7 from npm’s `alpha` dist-tag:

```sh
npm install tamil-toolkit@alpha
```

Or using pnpm / yarn:

```sh
pnpm add tamil-toolkit@alpha
# or
yarn add tamil-toolkit@alpha
```

The `alpha` tag points to `0.1.0-alpha.7`; npm’s `latest` tag still points to `0.1.0-alpha.1`. The version badge above tracks the `alpha` tag.

---

## Node Quick Start

In Node.js (ESM or TypeScript), the native WebAssembly module initializes automatically on import:

```typescript
import * as tamil from "tamil-toolkit";

// 1. Grapheme Segmentation (handles ligatures accurately)
const text = "தமிழ்நாடு";
const letters = tamil.get_letters(text);
console.log("Letters:", letters); // [ 'த', 'மி', 'ழ்', 'நா', 'டு' ]

// 2. Legacy Font Conversion (Bamini, TSCII, TAB, TAM, Vanavil)
const bamini = tamil.unicode_to_bamini(text);
console.log("Bamini encoded:", bamini); // "jkpo;ehL"
console.log("Back to Unicode:", tamil.bamini_to_unicode(bamini)); // "தமிழ்நாடு"

// 3. Exact Currency & Cheque Formatting (no float errors!)
console.log(tamil.format_currency(102550, "INR", "TN")); // "INR 1,025.50"
console.log(tamil.format_currency(102550, "LKR", "SL")); // "LKR 1,025.50"

// 4. Tamil Alphabetical Sorting (Agara Varisai)
const words = ["ஆப்பிள்", "அணில்", "இலை", "ஈட்டி"];
console.log(tamil.sort_words(words)); // [ 'அணில்', 'ஆப்பிள்', 'இலை', 'ஈட்டி' ]
```

---

## Browser Quick Start

For browser applications (Vite, Next.js, Webpack, Nuxt, or Vanilla JS), use the `/web` entry point and initialize WebAssembly once before calling API methods:

```typescript
import { init, get_letters, unicode_to_bamini, bamini_to_unicode } from "tamil-toolkit/web";

// 1. Initialize WebAssembly module (load and compile WASM)
await init();

// 2. Ready to use!
const letters = get_letters("வணக்கம்");
console.log(letters); // [ 'வ', 'ண', 'க்', 'க', 'ம்' ]

const bamini = unicode_to_bamini("வணக்கம்");
console.log(bamini); // "tzf;fk;"
```

### Next.js & React Example:

```tsx
"use client";

import { useEffect, useState } from "react";
import { init, unicode_to_bamini, bamini_to_unicode } from "tamil-toolkit/web";

export default function TamilConverter() {
  const [ready, setReady] = useState(false);
  const [input, setInput] = useState("தமிழ்");
  const [output, setOutput] = useState("");

  useEffect(() => {
    init().then(() => setReady(true));
  }, []);

  const handleConvert = () => {
    if (ready) {
      setOutput(unicode_to_bamini(input));
    }
  };

  return (
    <div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={handleConvert} disabled={!ready}>Convert to Bamini</button>
      <p>Result: {output}</p>
    </div>
  );
}
```

---

## Practical Web Recipes

### 1. Sorting Tamil Arrays in UI State (Agara Varisai)

Use `compare` directly in standard JavaScript `Array.prototype.sort()`:

```typescript
import { compare } from "tamil-toolkit";

const users = [
  { name: "கவிதா" },
  { name: "அமுதா" },
  { name: "பாரதி" }
];

users.sort((a, b) => compare(a.name, b.name));
// Result: அமுதா, கவிதா, பாரதி
```

### 2. Converting Legacy Files & Clipboard Content

```typescript
import * as tamil from "tamil-toolkit";

// Transcode Bamini clipboard text
function convertClipboard(pastedText: string): string {
  try {
    return tamil.bamini_to_unicode(pastedText);
  } catch (err) {
    console.error("Transcoding error:", err);
    return pastedText;
  }
}
```

---

## Alpha 7 scope

The npm `0.1.0-alpha.7` package includes the capabilities listed above. The
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

---

## Author & Maintainer

**Abishtakan Sivachandrathevan** ([@abishtakan](https://github.com/abishtakan))

---

## Documentation

- [API and feature overview](https://github.com/abishtakan/tamil-toolkit#capability-contracts)
- [JavaScript/WASM API declarations](https://github.com/abishtakan/tamil-toolkit/tree/master/bindings/js-wasm)
- [Unicode/core contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/core-v0.1.md)
- [Collation contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/collate-v0.1.md)
- [Numerals, fractions, and dates](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/numerals-v0.2.md)
- [Codec contract and alpha 3 limits](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/releases/alpha-7.md#compatibility-and-scope)
- [LT-TM CID profile contract](https://github.com/abishtakan/tamil-toolkit/blob/master/docs/specs/codec-lt-tm.md)
- [Third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md)

---

## License

Original code is [MIT licensed](https://github.com/abishtakan/tamil-toolkit/blob/master/LICENSE).
Bundled data and mappings retain their recorded terms in the
[third-party notices](https://github.com/abishtakan/tamil-toolkit/blob/master/THIRD_PARTY_NOTICES.md).

---

## Keywords & Search Queries

`tamil npm`, `tamil unicode javascript`, `bamini to unicode converter npm`, `tscii to unicode javascript`, `tamil font converter web`, `tamil text processing nodejs`, `tamil sort agara varisai js`, `tamil numbers to words npm`, `tamil wasm webassembly`, `offline tamil converter`.
