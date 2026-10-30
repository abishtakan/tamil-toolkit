# tamil-core v0.1 acceptance plan

Status: accepted for the v0.1 Unicode-primitives contract by local verification.
Publication and expert endorsement of a complete linguistic SDK are separate
milestones. Acceptance evidence and environment limits are recorded below.

## Scope and order

1. Freeze independent Unicode 17.0.0 reference data, its source URLs, SHA-256
   digests, and redistribution license. Compile expected JSONL from those facts,
   never from `lexicon/core.toml`, Rust output, the oracle, or bindings.
2. Cover the complete supported letter inventory and canonical decompositions.
   Add explicit boundary and error cases before changing implementation.
3. Extend the existing fixture schema and every runner to accept exactly one
   of `expected` or `expected_error`. Errors compare the Rust error message;
   Python/JavaScript/Dart retain their native exception types.
4. Fix behavior exposed by these cases at its owning Rust/data layer. Keep FFI
   adapters thin and preserve spelling, joiners, whitespace, and other scripts.
5. Run the full repository gate and host Dart verification. Record exact counts,
   passing commands, remaining limitations, and the scope being accepted.

## Measurable acceptance criteria

- The 247 traditional letters (12 Uyir, 18 Mei, 216 Uyirmei, one Aytham) each
  have independent segmentation and classification expectations.
- All 24 supported consonant bases (18 native, five single-codepoint Grantha,
  and KSHA) have all 12 vowel forms tested independently for segmentation,
  classification, composition, and decomposition: 288 combinations, including
  the 216 native Uyirmei. All 24 pure Mei are tested too.
- Both Shri spellings (`0BB6 0BCD 0BB0 0BC0` and
  `0BB8 0BCD 0BB0 0BC0`) count as one atomic Grantha letter. Neither spelling
  is rewritten into the other: they are not canonically equivalent Unicode.
- Every Tamil canonical decomposition from UnicodeData is tested in NFC and
  NFD, including independent AU and dependent O/OO/AU on each supported base.
  Decomposed inputs also exercise segmentation and Uyirmei splitting.
- The frozen Unicode 17 grapheme-boundary cases run through the normalizing API
  with expected clusters normalized independently. Any project tailoring that
  differs from default UAX 29 must be explicit and tested separately.
- Targeted cases cover empty input, CRLF, punctuation, emoji, mixed scripts,
  isolated/repeated marks, ZWJ/ZWNJ preservation, interrupted ligatures, and
  adjacent Tamil letters. Invalid orthography is preserved; it is not silently
  repaired or counted as a valid Tamil letter.
- Shared negative vectors cover empty/Mei/Uyir/multiple-letter splitting,
  malformed vowel combinations, joiners in composition/decomposition, invalid
  Mei/Uyir pairs, missing pair fields, wrong JSON types, and unknown operations.
  Success where an error is expected, a wrong message, or an unexpected error
  fails in every runner. Exactly one expected outcome is required by schema.
- The inventory is tested for regional invariance with explicit TN, Jaffna,
  Batticaloa, Vanni, Up-Country, Kongu, and Chennai fixtures. Core Unicode
  behavior has no locale-specific vocabulary or spelling substitution.
- Checked-in fixture regeneration is deterministic and works offline. Coverage
  and reference digests are verified automatically; dropped cases cannot pass
  merely because every remaining case succeeds.
- Both existing core properties still run 10,000 cases. `Letters` continues to
  return borrowed slices, and its preservation contract is checked. Allocating
  normalization/FFI APIs are documented without zero-allocation claims.
- `just agent-pre-stop-gate` and `just test-dart` pass with every active fixture
  executed in Rust, Python, Node WASM, browser-target WASM, and host Dart. No
  mocks, skipped runtimes, weakened expectations, or new planned core suites.

## Public contract decisions

The existing six operations remain the API. `get_letters` and inspection use
NFC text and the documented Ezhuthu tailoring; they preserve non-Tamil clusters.
`split_uyirmei` accepts one valid consonant/vowel form. `compose_uyirmei` accepts
one valid Mei and independent Uyir. Error strings already returned by Rust are
the baseline for this milestone; introducing a new public error-code API is out
of scope.

Inspection distinguishes the tailored cluster count from the number of valid
Tamil letters. Unexpected marks/joiners remain in the returned text and make an
affected cluster `other`; they are not discarded to increase the count.

## Independent evidence

- [Unicode 17 Tamil chapter, sections 12.6.1-12.6.5](https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-12/)
- [Unicode 17 named character sequences](https://www.unicode.org/Public/17.0.0/ucd/NamedSequences.txt)
- [Unicode 17 character/decomposition data](https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt)
- [UAX 29 revision 47, Unicode 17](https://www.unicode.org/reports/tr29/tr29-47.html)
- [Unicode 17 grapheme-boundary tests](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/GraphemeBreakTest.txt)

Unicode evidence establishes encoded letters, named sequences, normalization,
and boundary rules. Native consonant grouping is independently checked against
[Tamil Virtual Academy's Advanced Ebook, printed page 26](https://www.tamilvu.org/coresite/download/Advance_Ebook.pdf)
and [its online consonant lesson](https://www.tamilvu.org/courses/degree/c021/c0211/html/c0211331.htm).
This work does not claim to validate regional pronunciation,
phonology, historical orthography, grammar, prosody, or dictionary collation.

## Explicit non-goals

No collation, numerals, codecs, Punarchi, morphology, dialect conversion,
hyphenation, prosody, PostgreSQL work, registry publication, performance SLA,
lossy sanitization, or new user-facing API is included. Unicode supplementary
Tamil symbols remain preserved non-letter clusters for this milestone.

## Acceptance results

All stated engineering acceptance criteria passed on the local Windows/MSVC
environment. The active corpus contains **2,454 vectors**:

- 34 original bootstrap cases;
- 1,237 alphabet/matrix/regional cases, including segmentation and inspection
  for all 327 supported spellings (247 traditional plus 80 extended spellings),
  composition and splitting for all 288 vowel forms, and seven regional probes;
- 291 canonical-normalization cases;
- 796 boundary/inspection cases, including all 766 frozen UAX 29 test rows;
- 96 exact-error cases, covering TN and SL.

`just agent-pre-stop-gate` passed formatting, Unicode/schema validation,
workspace checking, clippy with denied warnings, six Rust tests (including both
10,000-case properties), doctests, and **47 harness tests**. The harness checks
reference digests, corpus regeneration, exact coverage, and outcome schema.

The same 2,454 rows passed through Rust, the rebuilt PyO3 extension, Node WASM,
browser-target WASM, and host Dart. Python reported 2,457 tests including three
additional adapter checks. Vitest reported 2,455 tests, each golden case checking
both WASM targets, plus one adapter check. `just test-dart` passed analysis and
2,455 tests including one additional ABI/error check.

`tools/generate_core_golden.py --check` produced identical fixtures under Python
3.13.7 (Unicode data 15.1) and the development Python 3.14 environment. Reference
hashes verify the frozen Unicode 17 evidence independently; `.gitattributes`
prevents checkout newline conversion from changing those bytes.

The newly reproduced modern-Shri failure was corrected by adding the SHA-based
sequence to `lexicon/core.toml`. No spelling fold or alternate binding algorithm
was introduced. Rust's existing composition and normalization behavior satisfied
the independent matrix and shared negative cases.

Limits: remote Ubuntu/Windows CI has not been executed as part of this local
verification. Browser-target WASM was initialized and executed in Node, not in
an interactive browser. Dart verification covers the host library, not mobile
cross-compilation. These results accept the documented v0.1 scope; they do not
claim publication readiness, broader linguistic correctness, or a performance SLA.
