# tamil-collate v0.1 plan and acceptance contract

Status: accepted for the documented v0.1 profile by local verification.
Profile: `agara-v1`; key format version: 1.

## Plan

1. Freeze the CLDR 48 Tamil tailoring and its digest beside the existing Unicode
   17 references. Document the exact Agara profile and fallback decisions.
2. Compile independent golden expectations from the reference inventory and
   declared profile before implementing Rust. Store runtime ordering separately
   in `lexicon/collate.toml` and compile it to static lookup tables with build.rs.
3. Implement comparison, cached-key stable sorting, and sort/search keys in
   `tamil-collate`. Expose only thin wrappers in the umbrella and all bindings.
4. Verify corpus provenance, exhaustive ordering, properties, public convenience
   APIs, cross-runtime success/error parity, and the full gates. Record results.

## Agara profile

The profile orders 325 Tamil elements: the 12 independent vowels, Aytham, then
24 consonant rows, each containing Mei followed by its 12 vowel forms. Native
consonants follow the order in Unicode's traditional Tamil table. The Grantha
extension follows J, SH, SS, S, H, KSHA, after the native rows. This row order is
also explicitly listed in the independent reference profile.

Mei-first ordering follows CLDR's Tamil tailoring, which cites the University
of Madras Tamil Lexicon. The traditional letter inventory/order follows Unicode
17 section 12.6.5 and NamedSequences. This is the project's explicit Agara
profile, not an implementation or conformance claim for the full UCA/ICU rules.

Normalize to NFC before generating keys. Compare lexicographically by these
ordered elements; a prefix sorts before a longer word. Shri is expanded for
collation into its written Mei plus RII, so modern SHA-based and legacy SA-based
spellings remain distinct and occupy their respective consonant rows. Their
normalization, spelling, and source strings are never rewritten into one another.

Other scripts, whitespace, punctuation, emoji, joiners, isolated marks, and
malformed Tamil clusters are preserved. Every unrecognized cluster sorts after
the listed Tamil elements and is encoded by its scalar sequence. Within this
fallback, scalar order is deterministic; it is not a linguistic ordering for
other scripts. No punctuation/case/joiner removal or digit-value folding occurs.
An entire malformed cluster uses fallback, rather than treating a valid prefix
of it as a valid Tamil letter.

Core Unicode behavior has the same profile for TN and SL. Tests label TN,
Jaffna, Batticaloa, Vanni, Up-Country, Kongu, and Chennai. This scope introduces
no unverified regional spelling substitutions or alternate dictionary profiles.

## APIs and keys

- Rust `compare(left, right) -> Ordering`; JSON/bindings `compare` returns -1/0/1
  from input `{left, right}`.
- `sort_words`: accept a string array and return a stable sorted copy. Preserve
  original strings and duplicates, including NFC/NFD spelling on equal keys.
- `sort_key(text)` and `search_key(text)`: return identical numeric arrays.
  Equality provides canonical exact matching and keys support lexicographic
  ordered indexes. Search is by exact normalized letters, not fuzzy/stemmed or
  vowel-insensitive matching. A query letter A does not match AA by prefix.

The key begins with version 1. Each following pair is `[0, one_based_rank]` for
a recognized element, or `[1, scalar]` for a scalar in a fallback cluster. Shri
emits the pairs of its two written elements. Empty input has key `[1]`. Numeric
arrays compare lexicographically, not as JSON strings. Persist the profile/key
version with indexes; never mix keys across future profile versions.

All key integers fit exactly in JavaScript and Dart. Sorting allocates one key
per input and returns original text. Key generation and comparison allocate;
this API makes no zero-allocation or performance-SLA claim.

Wrong scalar types return `expected a string input`. Comparison requires string
`left` and `right` fields. Sorting rejects a non-array with
`expected an array of strings` and rejects non-string members with
`expected a string input`. Existing core errors and behavior remain unchanged.

## Acceptance criteria

- Independent fixtures enumerate all 325 elements with exact sort/search keys,
  compare every adjacent pair in both directions, and sort reversed inventory.
- Every consonant row has a shuffled Mei/vowel sorting fixture. TN/SL and all
  seven core regional labels have full-inventory sorting expectations.
- Fixtures cover native consonant confusables, prefix words, stable duplicates,
  canonical decompositions for all 73 relevant Tamil forms, both Shri spellings,
  KSHA, empty lists/text, mixed scripts, punctuation, digits, emoji, isolated and
  repeated marks, ZWJ/ZWNJ, and malformed clusters.
- All four operations include successful and wrong-type/shape error cases in
  the language-agnostic corpus. Every active row executes through Rust, PyO3,
  Node WASM, browser-target WASM, and the host Dart ABI.
- Runtime tables are declarative and validated at build time. Frozen evidence,
  profile, fixture regeneration, case counts, and table agreement are checked
  offline. Expected output is never obtained from the runtime or oracle.
- 10,000-case properties check lossless canonical key encoding, comparator
  order properties, stable sorting, and preservation of input values.
- Convenience APIs are typed and exercised in Python, both WASM entry points,
  and Dart; bindings contain no linguistic ordering logic.
- `just agent-pre-stop-gate` and `just test-dart` pass with existing core behavior
  preserved. Document exact results and local-verification limitations.

## Sources and exclusions

- https://www.unicode.org/faq/tamil.html
- https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-12/
- https://www.unicode.org/Public/17.0.0/ucd/NamedSequences.txt
- https://raw.githubusercontent.com/unicode-org/cldr/release-48/common/collation/ta.xml

Full UCA weights, secondary/tertiary linguistic strengths, numeric sorting,
case/accent-insensitive search, dictionary lexicons, dialect/morphology folding,
PostgreSQL integration, registry publication, and remote CI execution are outside
this v0.1 contract. No claim of universal agreement among Tamil dictionaries is
made; users receive this named, documented profile.

## Acceptance results

All stated engineering acceptance criteria passed on the local Windows/MSVC
environment. The module adds **3,091 collation vectors**, bringing the active
shared corpus to **5,545 vectors**, including 146 exact-error cases overall.

The collation suite includes 650 exact inventory sort/search-key cases, 1,296
adjacent comparisons in both directions for TN/SL, 650 prefix comparisons, all
24 vowel-family sorts, seven regional full-inventory sorts, 365 canonical-tie
and key cases, Shri/word/fallback controls, and 50 wrong-type/shape errors.

`just agent-pre-stop-gate` passed formatting, Unicode/schema checks, workspace
checking, clippy with denied warnings, nine Rust tests, doctests, and **50 harness
tests**. The three new collation properties run 10,000 cases each; with core's
two properties, the gate executes **50,000 generated property cases**.

All 5,545 golden rows passed through Rust, rebuilt PyO3, Node WASM,
browser-target WASM, and host Dart. Python reported **5,549 tests**, Vitest
**5,547 tests** with each golden case checking both WASM entry points, and Dart
**5,547 tests**. Convenience APIs have explicit tests in every binding.
`just test-dart` also passed static analysis without issues.

Both core and collation fixture compilers regenerated identically offline under
the development Python 3.14 environment and Python 3.13.7, matching the CI Python
version. Reference digests, runtime/reference table agreement, and corpus counts
are enforced in harness tests.

Limits: this verification is local; remote CI has not run. Browser-target WASM
was initialized and executed in Node rather than an interactive browser. Dart
verification covers the host shared library. The profile's scalar fallback and
canonical exact search semantics remain deliberate limits, not full UCA/ICU or
fuzzy linguistic search behavior. Registry publication remains disabled.
