# TSCII byte decoder: bounded profile contract

Status: implemented in the unreleased development tree. The byte decoder is bounded by the
declared mapping inventory and rejects bytes outside it.

## Interface

`tscii_bytes_to_unicode` receives `{"bytes": [0..255, ...]}` and returns NFC
Unicode text. The bytes are actual encoded bytes, not UTF-8 or a font string
that happens to display Windows-1252 glyphs. The typed bindings should expose
native byte-compatible inputs and the dispatcher should enforce integer range.
Malformed input and unsupported bytes produce the errors specified below.

The initial cases cover independent vowels and a consonant whose IANA
glyph names correspond to Unicode Tamil character names. Both `0xAD` (a
deprecated alias) and `0xFE` are included as inputs for the third vowel.
These facts are drawn from the [IANA registration draft](https://data.iana.org/archive/ietf-charsets/pdf00000.pdf)
and [Unicode Tamil names](https://www.unicode.org/charts/PDF/U0B80.pdf).
They are not a complete decoder specification.

The registration draft's notes mention `0xEF` alongside `0xAD` for the third vowel,
while its table places that vowel at `0xFE`. The table and both inspected
implementations support `0xFE`; the discrepancy still needs explicit review
for any future broader profile.

## Decoder contract

The profile uses the TamilUtil TSCII encoder's byte spellings corrected and
supplemented using the [IANA byte audit](codec-tscii-audit.md),
interpreting printable legacy characters through Windows-1252 and C1 controls
as same-valued bytes. The reference's `0x5C 0x88` spelling for U+0B9C U+0BCD
contains a literal backslash in a Java `replace` call; use `0x88` as supported
by the IANA table. Also accept the IANA-deprecated `0xAD` alias for U+0B87.
The map is a bounded profile rather than a guarantee for every legacy font.

At each byte position use the longest declared key. ASCII bytes pass through.
An unsupported byte fails as `unsupported TSCII byte at offset N: 0xXX`, where
N counts original bytes. Malformed request arrays or values outside 0..255 fail
as `expected TSCII byte array`. Empty input succeeds. Normalize decoded output
to NFC; do not guess encodings or remove joiners.

## Acceptance criteria

1. Pin source bytes, license and source version; retain source disagreements.
2. Cover every declared mapping, ASCII, unassigned bytes, malformed input,
   visual-order sequences, aliases, and TN/SL invariant behavior in fixtures.
3. Compile declarative data at build time. Run every active case through Rust,
   Python, Node/browser WASM and host Dart, plus arbitrary byte tests.

Reverse conversion, Windows-1252 font strings and automatic detection need
separate contracts and are outside this draft's initial decoder scope.

All assigned individual bytes in the IANA table now have mappings. This byte
inventory does not by itself establish complete coverage of every valid TSCII
sequence or legacy font variant. Aril was consulted for comparison.
