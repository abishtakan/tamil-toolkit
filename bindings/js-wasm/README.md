# tamil-toolkit for TypeScript / WASM

`just sync-bindings` produces Node and browser WASM builds and TypeScript
declarations. Node: `import * as tamil from 'tamil-toolkit'`. Browser:
`import { init, get_letters } from 'tamil-toolkit/web'; await init();`.
The experimental MIT-licensed `0.1.0-alpha.1` is published on npm. Install it
with `npm install tamil-toolkit@alpha`.
These adapters serialize calls into the shared Rust dispatcher. Planned modules
are excluded. APIs may change before stability. Node 22+ is supported; browser
consumers must initialize the WASM module before calling its functions.

```javascript
import { format_fraction, format_currency } from "tamil-toolkit";

console.log(format_fraction(2, 4)); // 1/2
console.log(format_currency(102550, "LKR", "SL")); // LKR 1,025.50
```

The package includes core Unicode/Ezhuthu functions, Agara collation, bounded
TN/SL integer and currency words, fractions, Gregorian dates, and explicit
Bamini conversion. For browser code use the `/web` entry point, `await init()`,
then call the same methods. Hosts must serve the packaged WASM file with the
generated loader; bundlers must support WebAssembly assets and ES modules.
See LICENSE, THIRD_PARTY_NOTICES.md, and bundled dependency license notices.

Both entry points expose `compare`, `sort_words`, `sort_key`, and `search_key`.
Use the comparison result or numeric-array keys for ordering; comparing their
JSON string representation is incorrect. The versioned `agara-v1` profile and
its mixed-script fallback are specified at
https://github.com/abishtakan/tamil-toolkit/tree/HEAD/docs/specs/collate-v0.1.md.

Current development source adds `tscii_bytes_to_unicode(new Uint8Array([0xba, 0xa2, 0xc5, 0xfd]))`; it is not in the published alpha.

The unreleased `unicode_to_tscii_bytes(text)` returns an array of byte values.

Unreleased development source provides `tab_bytes_to_unicode(bytes)` and `unicode_to_tab_bytes(text)`.

Unreleased development source provides `tam_bytes_to_unicode(bytes)` and `unicode_to_tam_bytes(text)`; TAM bytes do not preserve Latin letters.
