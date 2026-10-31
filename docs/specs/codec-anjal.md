# Anjal byte conversion contract

The unreleased profile `anjal-tamilutil-bounded-v1` converts explicitly
selected legacy Anjal bytes to Unicode and back. It is not the modern Anjal
keyboard or a universal claim about all Anjal fonts. ASCII bytes pass through;
bytes above 7F are the pinned TamilUtil legacy strings interpreted as Windows-1252
with same-valued C1 controls. Do not infer an encoding from user input.

The source assigns E5, E6, E7 and E8 to two different Tamil outputs each; a
standalone ambiguous byte returns an error at its byte offset. Longer declared
sequences are matched first when unambiguous. The source also uses U+2212 for
one output; that scalar is not representable under this byte interpretation,
so no byte is guessed for it. These facts are stored in declarative data and
covered by strict-error tests. A second inspected implementation, Aril, shares
all 319 distinct TamilUtil mappings and thus is useful for comparison, but is
not independent evidence resolving the conflicts.

Encode NFC Unicode using the shortest unambiguous byte spelling, breaking ties
lexicographically; reject unsupported scalars and reject any sequence that
fails to decode to the normalized input. Decode longest byte matches and return
NFC. Preserve ASCII; reject unrecognized bytes and do not remove joiners.

Acceptance: source bytes and digest are pinned; TN and SL fixtures cover each
unambiguous mapping, canonical encoder choice, source conflicts, malformed
input, offsets, ASCII, NFD and joiners. Run the shared corpus across Rust,
Python, Node/browser WASM and host Dart. Arbitrary byte and Unicode inputs must
not panic; successful encodings must round-trip. The scope is a bounded profile,
not complete legacy font or variant coverage.

Source: pinned TamilUtil Anjal encoder at `tests/reference/codec-tscii/`;
[upstream Android TamilUtil](https://github.com/mayooresan/Android-TamilUtil)
and [Aril](https://github.com/digital-tamil/aril) are implementation references.
