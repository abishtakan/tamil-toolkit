# Bounded Unicode to TSCII byte encoder

## Contract and acceptance

The unreleased encoder `unicode_to_tscii_bytes` accepts a Unicode string and
returns a byte array. Normalize input to NFC; use longest matching against the
340 distinct Unicode values in `tscii-tamilutil-bounded-v1`. ASCII passes
through. For U+0B87 choose FE: the IANA registration draft labels AD a deprecated
alias, and the pinned TamilUtil encoder uses FE. Reject unsupported scalars
with their NFC UTF-8 byte offset; reject byte sequences that do not decode back
to the complete normalized input. Do not remove joiners or guess an encoding.

Evidence: the pinned [TamilUtil encoder](../../tests/reference/codec-tscii/README.md),
the [IANA draft](https://data.iana.org/archive/ietf-charsets/pdf00000.pdf), and
the [decoder contract](codec-tscii-draft.md), and the [IANA byte audit](codec-tscii-audit.md). The profile is not a claim of
full TSCII or historic font coverage.

Acceptance: fixtures precede the implementation, cover each canonical mapping
for TN and SL, FE alias choice, ASCII, mixed text, invalid inputs, and strict
errors. Rust, Python, WASM and host Dart consume the same fixtures. Successful
encodings round-trip to NFC; arbitrary UTF-8 never panics. Bindings are thin.
Automatic detection and other encodings remain out of scope.
