# Changelog

## Unreleased

- Pin Thamodaran's 1999 Nannūl critical edition as the first literary Punarchi
  profile's root-text/commentary source; verify the three chapter ranges and
  document provisional Tolkāppiyam comparison areas. Add a page-indexed,
  paraphrased Markdown digest and per-sūtra viewer-page locator for the TVA HTML
  edition text, add a provisional subject ledger for sūtras 151–203, and clarify
  that Project Madurai already provides a searchable Unicode companion e-text.
  Add provisional subject ledgers for sūtras 204–239 and 240–257. Keep
  fixtures inactive pending full scan inventory and linguistic review. Record
  that the earlier CICT 1979 comparison-edition selection was premature. Inspect
  the 1979 Annamalai scan (second edition, August 1979), 2003 Tamilmann edition,
  1982 WTRI Puṇariyal Uraivaḷam, and CICT's 1996 textual-variation volume.
  Document the 1996 volume's explicit limit: it presents collected manuscript
  and print variants but does not establish a single base reading. Note the
  1992 third-edition / CICT 1996 catalog discrepancy for Sundaramurthy's later
  Annamalai edition; its title page remains unverified. Keep 1979 provisional
  and the 1996 volume as a variant apparatus, not sole authority. Add
  discovery-only Project Madurai locators for Tokai Marabu 2 and 3. Add provisional
  TVA HTML root/commentary paraphrases and example citations for Nannūl sūtras
  151–157; keep them inactive pending print and linguistic review.

- Add a bounded LT-TM / IndoWord 16-bit code profile, canonical 332-entry
  mapping projection, reverse encoder, shared dispatcher operations, and 687
  active golden vectors. Record PDF evidence, mapping provenance, and
  compatibility limits. Owner-approved gates passed: Rust, 115 harness tests,
  Python, Node/browser WASM, and Dart.

## 0.1.0-alpha.2 / Python 0.1.0a2 - 2026-11-01

- Add bounded bidirectional Anjal byte conversion with explicit ambiguity errors.

- Add bounded bidirectional TAM byte conversion with monolingual byte handling.

- Add bounded bidirectional TAB byte conversion and shared cross-runtime fixtures.

- Audit TSCII byte assignments, add missing symbols and Grantha forms, and fix repeated HA byte corruption.

- Add strict bounded Unicode to TSCII byte encoding and cross-runtime bindings.

- Add bounded TSCII byte decoding, shared fixtures, and Python, WASM, and Dart adapters.
- Remove stale generated Python extensions before rebuilding bindings.

- Add shared publishing policy checks, reusable source/digest gates, and
  serialized manual uploads for future releases.
- Resolve distribution source once across platforms; run the expensive
  artifact matrix on explicit dispatch.
- Document feature development, release preparation, and durable agent handoff.
- Use numbered workspace pytest temp runs for reliable Windows reruns.

## 0.1.0-alpha.1 / Python 0.1.0a1 - 2026-10-31

- First experimental MIT-licensed release of the Rust modules and umbrella SDK,
  Python native bindings, and Node/browser WASM package.
- Unicode normalization, tailored Ezhuthu segmentation and Mei/Uyir composition.
- Versioned Agara sorting and search keys.
- Bounded TN/SL integer words, exact INR/LKR amounts, fractions, and Gregorian dates.
- Explicit Bamini decoding and strict, round-trip-checked reverse encoding.
- Shared golden corpus with 21,277 cases and seventeen 10,000-case properties.

The module specifications document bounds and linguistic conventions. APIs may
change before stability. Other legacy encodings and the planned grammar,
morphology, dialect, publishing, prosody, and PostgreSQL modules are excluded.
Dart remains a development adapter requiring a host native library.
See [contracts and publication evidence](docs/releases/alpha-1.md).
