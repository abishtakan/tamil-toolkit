# TAB byte conversion contract

The unreleased profile `tab-tamilutil-bounded-v1` converts TAB bytes and NFC
Unicode. TAB is bilingual: bytes 00–7F are ASCII. Raw high bytes follow the
pinned TamilUtil mapping, with standalone signs and punctuation from the Unicode
TAB conversion note. TamilUtil's added numeral mappings conflict with the note
and are excluded; in particular C3 means U+0B95 U+0BC2, not a Tamil digit, and
98 is undefined. Ambiguity from multiple byte sequences for one Unicode string
is resolved by the shortest sequence, then lexicographically smallest bytes;
the preferences are recorded in the declarative profile.

Decode by longest byte sequence, return NFC, and report unsupported byte offsets.
Encode by longest NFC Unicode sequence and reject unsupported scalars or any
output that does not decode back to the normalized input. Do not discard joiners.
A0 and CA are NBSP aliases; 95, A5, and B7 are bullet aliases. Any unsupported
byte, glyph variation, and Tamil numeral returns an error rather than guessing.

Acceptance: source bytes and digests are pinned, both TN and SL fixtures cover
every declared mapping and reverse preference, ASCII, NFD, invalid values and
unsupported data. Rust, Python, Node/browser WASM and host Dart consume the same
active suite. Fuzz arbitrary UTF-8 and bytes; round-trip every successful encode.
An independent comparison of parseable UTN 17 entries found no conflicting
mapping; six Grantha vowel sequences are handled by composing single-byte
mappings and have independent vectors. This is a bounded profile, not a
completeness claim for TAB or font variants.

Sources: TamilUtil 1f659e70 pinned at `tests/reference/codec-tscii/`; [Unicode
TAB conversion note](https://www.unicode.org/notes/tn17/); [Tamil Nadu government
order](https://www.tamilvu.org/en/node/147000).
