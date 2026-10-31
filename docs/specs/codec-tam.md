# TAM byte conversion contract

The unreleased `tam-utn18-bounded-v1` profile converts raw TAM bytes to Unicode
and back. TAM is monolingual: bytes 41–5A and 61–7A represent Tamil glyphs and
symbols, rather than Latin letters. It retains the documented control, digit and
punctuation bytes. Latin letters that cannot be represented are rejected.

TAM builds on the verified TAB profile, adds the monolingual assignments in
`lexicon/tam-supplement.toml`, and allows documented TAB-compatible alternate
sequences where they decode unambiguously. Canonical encoding chooses the
shortest spelling, then the lowest byte sequence; preferences are recorded in
the generated declarative data. The profile includes Tamil signs but rejects
Tamil digits and numerals, which UTN 18 states are not encoded in TAM.

Decode the longest declared byte sequence, preserving only unassigned low-byte
positions that are documented ASCII controls or punctuation. Unsupported bytes
fail with their original offset. Normalize text to NFC before encoding; reject
unsupported scalars and any output whose decode differs from the normalized
input. Do not remove joiners or infer encodings.

Acceptance: sourced TN and SL fixtures cover each mapped spelling and canonical
value, monolingual low bytes, controls, punctuation, aliases, Tamil signs,
invalid inputs, joiners and NFD. Rust, Python, Node/browser WASM and host Dart
consume the same suite. Test arbitrary UTF-8 and byte sequences, and require
all successful encodings to round-trip. Six Grantha forms are represented by
composing mapped bytes and have independent cases. This bounded profile does
not claim full coverage of every font variant.

Sources: [Unicode Technical Note 18](https://www.unicode.org/notes/tn18/), the
[TAB contract](codec-tab.md), and the pinned TamilUtil reference. The UTF-8
source bytes and attribution are retained under `tests/reference/codec-tscii/`.
