# Unicode to Bamini: plan and acceptance contract

Status: engineering acceptance passed locally. Uses the existing `bamini-v1` profile; decoder behavior
and its 1,920 existing fixtures remain unchanged.

## Plan and scope

1. Derive canonical encoder spellings from the pinned, licensed primary source,
   using its first preferred alias and the existing Aytham extension. Declare
   the one multiple-alias choice in the lexicon, not in Rust code.
2. Write independent encoder fixtures from the frozen source tables, upstream
   encoder outputs, Unicode normalization facts, and structural key collisions.
3. Compile the Unicode-to-legacy trie at build time. Normalize input to NFC,
   encode with longest matching, then require strict decoding to reproduce the
   normalized input before returning any output.
4. Add thin Python, WASM, and Dart APIs and pass both full repository gates.

`unicode_to_bamini` takes `{text}` and returns an ASCII Bamini string. Typed
APIs take one string argument. Encoding is strict; there is no preserve/replace
option, implicit English conversion, or automatic source-encoding detection.
Empty text succeeds. All successful output satisfies:

`bamini_to_unicode(unicode_to_bamini(text), Strict) == normalize_nfc(text)`

This guarantees accepted Unicode input round-trips canonically. It does not
reproduce arbitrary original Bamini aliases: the three RA+VIRAMA spellings all
encode canonically as `u;`. Unsupported input produces an error, never partial
output or an ambiguous `*` placeholder.

## Mapping decisions

Invert each unique forward mapping. When a Unicode output has multiple legacy
aliases, require a declarative preference: RA+VIRAMA U+0BB0 U+0BCD uses `u;`,
the primary table's first alias. The other two aliases remain decoder inputs.
There are 296 canonical encoder entries, including Unicode comma -> ASCII `>`.
The existing Aytham -> `/`, primary HA+U / SSA+U / RA+UU, and legacy SA-based
Shri choices remain intact. The same pinned sources and MIT notices apply; see
`codec-v0.1.md` and `tests/reference/codec-v0.1/sources.json`.

Use longest Unicode matching so the SA-based Shri sequence becomes `=`.
KSHA forms compose from the existing KA+VIRAMA and SSA mappings. No new letters,
font variants, modern SHA-based Shri folding, or grammar rules are invented.
The five ambiguous source forms still cannot be encoded unambiguously.

ASCII pass-through is exactly the decoder's documented safe set. Other Latin
letters, literal `/`, `>`, `=`, `*`, joiners, and unsupported scalars fail.
Unicode comma has its own mapping. Joiners are rejected rather than removed.
NFC input normalization is canonical only; no compatibility/spelling folding.

## Boundary collisions and errors

Individually valid keys can combine into a different longer decoder key. For
example, KA+E followed by LLA would encode as `nf` + `s`, but `nfs` decodes as
KA+AU. Reject that input rather than return changed text. Suffix forms beginning
with `s` can also leave an invalid trailing vowel marker after longest decoding.
The strict round-trip check covers both changed and invalid decoded output.

Do not insert spaces or invent alternate glyph spellings to avoid collisions.
The encoder is deliberately conservative and does not search for alternate
spellings beyond the documented canonical table.

Errors are exact across runtimes:

- Missing/non-string text: `expected a string input`.
- First unsupported scalar during normalized scanning:
  `unsupported Unicode scalar for Bamini at NFC byte N: U+XXXX` (uppercase hex,
  at least four digits). Offsets refer to the normalized UTF-8 input, not the
  original decomposed input. A known base followed by an unsupported vowel sign
  reports that vowel sign's byte offset.
- If the complete candidate fails strict decoding or changes the normalized
  input: `Bamini encoding is not reversible for this input`.

Unsupported scalar errors precede the final round-trip check. No result is
returned before both stages succeed.

## Acceptance criteria

- Independent vectors cover all 296 canonical entries, their canonically
  decomposed inputs, the RA alias preference, primary/secondary source
  disagreements, and all independently encoded word/matrix samples.
- Structural fixture generation enumerates every canonical-key pair whose join
  crosses into a longer decoder key, without implementing a second decoder.
  All such collisions fail; safe adjacent and space-separated controls pass.
- Cover all ASCII and Tamil-block scalar inputs, all KSHA vowel forms, both
  Shri conventions, unsupported/ambiguous forms, malformed request shapes,
  joiners, NFC-relative error offsets, empty input, and a bulk sample.
- Cover TN/SL and seven regional inventory probes; encoding is region invariant.
- Runtime preferences match the independent primary source. The build rejects
  missing/unused/invalid alias choices and compiles one canonical mapping per
  supported Unicode output. Existing decoder fixtures remain unchanged.
- Two new 10,000-case properties exercise arbitrary UTF-8 without panic and
  supported random letter sequences. Every successful encoding is ASCII and
  decodes exactly to NFC input; canonically equivalent inputs yield identical
  success/error results.
- All active rows pass real Rust, rebuilt PyO3, Node/browser-target WASM, and
  host Dart, with direct typed API tests. `just agent-pre-stop-gate` and
  `just test-dart` pass, while preserving existing workspace edits.

## Acceptance results

The extension adds **1,838 golden vectors**, including **664 exact errors**,
bringing the active shared corpus to **16,831 vectors** and **1,088 errors**.
The existing 1,920 decoder fixtures regenerate unchanged.

Coverage includes all 296 canonical mappings, 67 decomposed mapping variants,
31 independent word/matrix samples, all 115 structural collision pairs and
their space-separated controls, all ASCII and Tamil-block scalars, 13 KSHA
forms, seven regional inventory probes, alias controls, unsupported forms,
normalization-relative errors, malformed requests, and empty/bulk input.
TN/SL cases consume the same independent source facts.

Before implementation, the unchanged Rust golden runner failed on the missing
`unicode_to_bamini` operation. After implementation, `just agent-pre-stop-gate`
passed formatting, Unicode/schema checks, locked workspace checking, clippy
with denied warnings, **17 Rust tests**, doctests, and **60 harness tests**.
Two new 10,000-case properties bring the workspace total to thirteen properties
and **130,000 generated cases** per full gate.

All 16,831 active rows pass real Rust, rebuilt PyO3, Node WASM, browser-target
WASM, and host Dart. Python reported **16,838 tests**; Vitest and Dart each
reported **16,836 tests**. Each Vitest golden row invokes both WASM targets.
Direct API tests exercise canonical output, NFC/decomposed input, strict
round trips, and collision errors. `just test-dart` passed host analysis and
tests, and a final Dart analysis also passed without issues.

Offline fixture regeneration matched under Python 3.14 and 3.13.7. Reference
digests and canonical alias agreement are enforced in the harness.

Verification is local Windows/MSVC; remote CI has not run. Browser-target WASM
was executed in Node rather than an interactive browser. Dart testing covers
the host shared library, without mobile packaging. The strict named profile
still excludes the five ambiguous forms and combinations that fail canonical
round trips; it does not search alternate font spellings. No universal Bamini
font-variant or original-alias preservation guarantee is implied. Other
encodings, detection, and historic orthography remain planned. Publication is
disabled.
