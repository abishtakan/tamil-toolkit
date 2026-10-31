# Bootstrap contract

This setup implements only the operations in the active golden suite. It does
not claim to implement general legacy-encoding coverage, sandhi, morphology,
dialect normalization, hyphenation, prosody, or PostgreSQL full-text search.

The unreleased [TSCII decoder](codec-tscii-draft.md) and [encoder](codec-tscii-encode.md) contracts specify the bounded byte profile.

## Unicode operations

- `normalize_nfc` / `normalize_nfd`: Unicode canonical normalization. Preserve
  joiners, whitespace, punctuation, and other scripts; never silently sanitize.
- `get_letters`: normalize to NFC, then return all extended grapheme clusters,
  with project tailoring that treats Sri and KSHA sequences as atomic Tamil
  letters. Preserve non-Tamil clusters. This is a specified Ezhuthu convention,
  not a claim that UAX 29 alone implements all Tamil linguistic segmentation.
- `split_uyirmei`: accept exactly one consonant with an inherent or dependent
  vowel, including the Grantha consonants in `lexicon/core.toml`. Normalize input
  to NFC. Reject a pure Mei, independent vowel, Sri ligature, or multiple letters.
- `compose_uyirmei`: accept exactly a valid Mei and independent Uyir; return NFC.
- `inspect_tamil_string`: preserve original scalars, report normalization and
  per-letter phonetic classes using Rust. Ezhuthu count includes recognized
  Tamil letters only; `grapheme_count` also includes non-Tamil clusters. Invalid
  orthographic sequences are preserved as clusters with class `other`.

`Letters` borrows NFC input and yields borrowed slices without allocation. Public
normalizing functions, JSON adapters, and FFI necessarily allocate. No blanket
zero-allocation claim applies to these APIs.

Core Unicode behavior is region independent. Fixtures label TN, Jaffna,
Batticaloa, Vanni, Up-Country, Kongu, and Chennai explicitly. Future linguistic
features must add sourced TN and SL cases, including relevant regional variation.

## Golden-vector lifecycle

`tests/golden/schema.json` defines each row. `dialect` is mandatory and is one of
`COMMON`, `TN`, or `SL`; `tags` never substitutes for that field. IDs are globally
unique. A row requires exactly one of `expected` or `expected_error`. The latter
asserts an exact Rust error message through each runtime's native exception.
Wrong-type inputs are permitted only in error vectors. `source` records evidence.
JSONL stores Tamil as escapes so codepoints
are reviewable. Required intentional non-NFC/joiner values must have an exact
JSON Pointer, kind, and reason in `unicode_exceptions`. Unused exceptions fail.

Object keys are checked recursively, including inside arrays. Keys must contain
valid Unicode scalars, be NFC, and contain no ZWJ/ZWNJ. Unicode exceptions apply
only to values and cannot waive invalid keys. Key diagnostics identify the
member's escaped JSON Pointer and use `key_non_nfc`, `key_joiner`, or
`key_surrogate` to distinguish a key from its value.

`manifest.json` lists every JSONL suite with status `active` or `planned`.
All runtimes execute every row of every active suite; unknown operations fail.
Planned suites are validated and reported, but never counted as passing tests.
Only the owner reviewing the specification may activate a planned suite. Empty
planned suites deliberately avoid fabricated linguistic facts. The numeral
suite now uses the reviewed CLDR/ICU evidence specified below.

The oracle shares `tamil-toolkit`'s Rust dispatcher. Python implements Unicode
scalar display/diff and schema validation only, not Tamil linguistic algorithms.

The [core v0.1 acceptance plan](core-v0.1.md) defines independent inventory,
normalization, boundary, and shared-error coverage. Its corpus is compiled offline
from pinned Unicode 17 data and separately sourced phonetic groups. Both Shri
spellings are atomic; canonical normalization preserves their distinct scalars.

The [collation v0.1 contract](collate-v0.1.md) adds Mei-first Agara comparison,
stable sorting, and canonical sort/search keys using declarative ordering tables.
Mixed-script fallback and the profile's limits are specified explicitly there.

The [numerals v0.1 contract](numerals-v0.1.md) adds bounded CLDR 49 integer
spellings and exact INR/LKR minor-unit formatting. The declared SL lakh spelling and invariant unit-label template
have explicit sources and limits; no general regional speech support is implied.
The [numeral completion contract](numerals-v0.2.md) adds exact reduced fractions,
traditional symbols, common-name/division readings, and Gregorian date formats
with Latin/Tamil decimal digits. This completes the numeral feature families
within their explicit component and calendar bounds.

The [codec v0.1 contract](codec-v0.1.md) adds explicit-profile Bamini decoding
with a build-time static trie, longest matching, strict/preserve policies, and
NFC output. Ambiguous source placeholders are rejected or explicitly preserved;
no automatic font detection is implied.
The [reverse codec contract](codec-reverse-v0.1.md) adds a strict canonical
Unicode encoder with an enforced NFC round trip. Unsupported input and
non-reversible key combinations fail explicitly.

## Evidence

- [Unicode Tamil FAQ](https://unicode.org/faq/tamil.html)
- [Unicode Tamil script chapter](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-12/)
- [Unicode named sequences](https://www.unicode.org/Public/17.0.0/ucd/NamedSequences.txt)
- [UAX 29](https://www.unicode.org/reports/tr29/)

The golden examples in this bootstrap are engineering fixtures. Expert review
remains necessary for linguistic rules; agents must never invent Nannool rules.
