# tamil-codec v0.1 plan and acceptance contract

Status: v0.1 engineering acceptance passed locally. Profile: `bamini-v1`.
The [reverse encoder](codec-reverse-v0.1.md) extends this profile separately;
its addition preserves the decoder behavior specified here. Additional bounded
profiles are specified in the [codec roadmap](codec-roadmap.md), including
[LT-TM / IndoWord](codec-lt-tm.md) and [Vanavil Avvaiyar](codec-vanavil.md).

## Plan

1. Pin the MIT-licensed ag-sanjjeev Bamini table and the independently maintained
   Pakeetharan converter, their commits, byte digests, and license notices.
2. Specify the mapping choices, longest-match behavior, unsupported/ambiguous
   input policy, and Unicode preservation. Write independent fixtures first.
3. Compile declarative mappings into a static Rust trie and expose a thin
   `bamini_to_unicode` adapter through the existing shared dispatcher.
4. Verify the entire active corpus across Rust, Python, both WASM targets, and
   host Dart, plus property tests and the repository's mandatory gates.

## Scope and API

`bamini_to_unicode` takes `{text, errors?}` and returns an NFC string. `errors`
defaults to `strict`; the other accepted value is `preserve`. The typed APIs
take `text` and an optional error-policy string. The encoding is selected by
calling this operation; there is no guessing from Latin-looking input.

Input is a Unicode string containing the ASCII character codes of the selected
Bamini font profile. This is not an arbitrary-byte decoder or a Word/PDF font-run
extractor. Callers must select Bamini text runs; ordinary English can contain
exactly the same character codes and will also be converted if supplied.

Match the longest declared key at each input position, advancing once through
the original input. Never run cascading replacements over generated Tamil.
The profile's maximum key length is three ASCII bytes. Canonical normalization
runs on the completed output, including preserved input; no compatibility
folding, transliteration, spelling correction, or joiner removal is performed.

The same mappings apply to TN and SL. Jaffna, Batticaloa, Vanni, Up-Country,
Kongu, and Chennai cases test encoding invariance, not spoken-language support.

## Mapping and ambiguity decisions

The primary table is `fontRespectiveUnicode.bamini` from ag-sanjjeev's pinned
`src/main.js`. It supplies 300 Unicode entries, including comma, and three
aliases for RA + VIRAMA. The secondary source is Pakeetharan's pinned
`convert.js`; its Aytham mapping, ASCII `/` -> U+0B83, is included explicitly.
Both MIT notices are retained with the frozen references.

The primary source maps `*` to five outputs: U+0B99 U+0BC1, U+0B99 U+0BC2,
U+0B9E U+0BC1, U+0B9E U+0BC2, and U+0BB4 U+0BC2. Treat `*` as ambiguous, never
choose one of those outputs. These five forms therefore have no unambiguous
mapping in this profile. Do not describe the source's placeholders as complete
support for every Tamil syllable.

There are 298 unambiguous keys and 296 distinct outputs. Outputs include the
legacy SA-based Shri (U+0BB8 U+0BCD U+0BB0 U+0BC0); no SHA-based Shri spelling
fold is introduced. KSHA can arise from adjacent mapped consonants; no new
ligature mapping is invented. Independent SHA U+0BB6 is not in this legacy table.

For HA+U, SSA+U, and RA+UU, the two sources differ. Keep the primary table's
ASCII keys respectively U+0060 U+007B, U+005C U+007B, and U+0026. Do not add
secondary aliases that would silently reinterpret these sequences.

Longest match resolves overlapping spellings as a declared policy. For example,
`nfs` maps to KA+AU, even though `nf` and `s` are individually meaningful keys.
The encoding is not uniquely reversible for arbitrary concatenated letter
sequences. The reverse operation's strict acceptance rules are specified in
`codec-reverse-v0.1.md`; there is no universal guarantee for arbitrary legacy
aliases. No Bamini font binary or font rights are redistributed.

## Error and preservation policy

The explicit pass-through set is space, tab, CR, LF, ASCII digits, and the
punctuation `!`, quotes, parentheses, hyphen, period, colon, and question mark.
Comma, slash, greater-than, and other mapped ASCII characters retain their
declared Bamini meanings; they are not assumed to be English punctuation.

In strict mode, fail at the first ambiguous key or unmapped scalar. Error
positions count UTF-8 bytes in the original input, consistently across bindings:

- `ambiguous Bamini sequence at byte N: U+002A`
- `unsupported Bamini scalar at byte N: U+XXXX` (uppercase hex, at least four digits)

Preserve mode leaves ambiguous keys and unmapped scalars in place and continues
decoding recognized keys. Its result may contain mixed scripts or remaining
legacy characters. ZWJ/ZWNJ are unsupported in strict mode and retained in
preserve mode, including their original positions relative to surrounding text.
They are never silently removed. NFC can change canonically decomposed text.

Missing/non-string text fails with `expected a string input`. A malformed or
unsupported policy fails with `unsupported codec error policy`. Validate text
before policy; a missing policy alone defaults to strict. Empty text succeeds.

## Acceptance criteria

- Pin and verify upstream bytes, licenses, extracted table, and declared profile.
  Regeneration is offline; expected output never comes from the Rust decoder or
  runtime lexicon. Independent source disagreement is documented, not hidden.
- Test every unambiguous key unchanged in TN and SL, all primary RA aliases,
  every ambiguous candidate, the full source inventory, and vowel-order cases.
- Frozen word/sequence samples use the secondary upstream Unicode encoder where
  both profiles agree. Decoder expectations are the original Unicode strings;
  corpus preparation must reject unsupported/ambiguous or non-round-trippable
  examples rather than weaken expectations.
- Exercise all ASCII scalar inputs, strict/preserve behavior, safe punctuation,
  multi-key text, longest-match collisions, normalization, original UTF-8 error
  offsets, Unicode/emoji, joiners, empty/large input, and malformed API requests.
- The build validates uniqueness, ASCII keys, NFC outputs, explicit ambiguity,
  and pass-through disjointness; all linguistic mappings stay in TOML.
- Three 10,000-case properties verify arbitrary UTF-8 never panics, preserve
  output is NFC without losing joiners, and pass-through content stays exact.
- All shared success/error vectors pass Rust, rebuilt Python, Node/browser-target
  WASM, and host Dart. Typed APIs have direct tests. Existing modules remain
  passing. `just agent-pre-stop-gate` and `just test-dart` pass.

## Sources

- https://github.com/ag-sanjjeev/app-tamil-fonts-unicode-converter/tree/9faf6226e500b0d1ab2e83132e8f227232d4d05d
- https://github.com/Pakeetharan/unicode-bamini-converter/tree/ee08d4360afadebaea4ef373ca1fad42025abb53

Both repositories publish MIT license notices. The frozen source and its
license are in `tests/reference/codec-v0.1`; byte digests and source URLs are in
`sources.json`. The reference JavaScript is development evidence only; the
runtime and all public bindings execute the Rust engine.

Other encodings, automatic detection, binary code-page decoding, and historic
orthography are future milestones.

## Acceptance results

All stated engineering acceptance criteria passed on the local Windows/MSVC
environment. The codec adds **1,920 golden vectors**, including **144 exact
errors**, bringing the shared active corpus to **14,993 vectors** with **424
errors** overall.

Coverage includes 1,192 mapping cases (298 keys, TN/SL, default/preserve), 124
independent word/vowel-matrix cases, 512 individual ASCII cases, seven regional
full-inventory cases, and 85 concatenation, ambiguity, Unicode, bulk, and API
controls. Independent Unicode 17 inventory checks prove that exactly the five
declared ambiguous source forms are absent from the 247 traditional letters.
No invented replacements fill those gaps.

Before implementation, the unchanged Rust runner failed on the missing
`bamini_to_unicode` operation. `just agent-pre-stop-gate` now passes formatting,
Unicode/schema checks, locked workspace checking, clippy with denied warnings,
**15 Rust tests**, doctests, and **57 harness tests**. The three codec properties
run 10,000 cases each; the workspace now has eleven such properties, totaling
**110,000 generated cases** per full gate.

All 14,993 active rows passed real Rust, rebuilt PyO3, Node WASM, browser-target
WASM, and host Dart. Python reported **14,999 tests**, Vitest **14,997 tests**
(each golden row invokes both WASM entry points), and Dart **14,997 tests**.
Direct convenience tests cover default strict mode, preserve mode, ambiguity,
and invalid policy. `just test-dart` also passed analysis without issues.

The original source extraction and all 332 independent encoder outputs were
reproduced structurally exactly using the checked-in reference helper. Offline
fixture regeneration matched under Python 3.14 and 3.13.7. Harness tests enforce
reference digests, the runtime/source mapping agreement, exact coverage, source
disagreements, and retained license notices.

Verification is local; remote CI has not run. Browser-target WASM was loaded in
Node rather than an interactive browser. Dart coverage is for the host shared
library, without mobile packaging. The named profile does not establish
compatibility with every Bamini font variant. The five ambiguous forms,
automatic detection, other encodings, and historic orthography
remain outside this completed milestone. Publication remains disabled.
