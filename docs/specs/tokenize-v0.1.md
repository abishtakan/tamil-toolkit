# tamil-tokenize v0.1 contract

Status is active for Phase 9 (`v0.1`, owner-activated on 2026-11-26). The [feature specification](../../specs/024-tamil-tokenize/spec.md) defines user outcomes. This contract defines their observable boundary behavior and the evidence recorded for acceptance.

The outputs are linguistic word and sentence spans. For example, OpenAI’s published `o200k_base` encoder can place `U+0BCD` in its own model token after `U+0BB4` in `0BA4 0BAE 0BBF 0BB4 0BCD`. Phase 9 keeps that final written unit together. Model inference, subword IDs and counting, and budget-aware chunking have their own contracts if pursued. A chunker can compose source spans and measure each assembled chunk with its target encoder. [OpenAI encoder reference](https://github.com/openai/tiktoken)

## Source coordinates

- Input is Unicode text. Each result is a nonempty, contiguous substring with zero-based, half-open UTF-8 byte and written-unit ranges into the entire original input. Written units follow the [core tailoring](bootstrap.md#unicode-operations) on original text, including atomic KSHA and both Shri spellings. Other scripts, punctuation, digits, whitespace clusters, and malformed clusters each occupy their corresponding positions in that same sequence. This coordinate is distinct from a count of valid Tamil letters.
- Both coordinates must land at boundaries of the same complete units. A boundary proposed inside a unit is suppressed. Normalization during lookup never changes the text or coordinates returned to the caller. In particular, the tokenizer preserves decomposed signs, U+200D, and U+200C.
- Tailoring uses the exact atomic sequences defined by the core. For interrupted forms such as `0B95 0BCD 200D 0BB7` or `0B95 0BCD 200C 0BB7`, use the core units for those original scalars and retain the joiner in its original position.
- A whitespace unit consists entirely of Unicode `White_Space` scalars. A unit with a whitespace base and an attached non-whitespace mark remains addressable. Empty and all-whitespace input return empty results.
- For the input `x \u{0B95}\u{0BC6}\u{0BBE}. \u{1F600}`, the decomposed Tamil token has byte range `[2, 11)` and written-unit range `[2, 3)`. The full stop is `[11, 12)` and `[3, 4)`. The emoji is `[13, 17)` and `[5, 6)`. Lookup can compare the Tamil token with `\u{0B95}\u{0BCA}`, and the returned slice still contains `0B95 0BC6 0BBE`.

## Boundary rules

Use the Unicode 17.0 default word and sentence rules as the baseline. The profile tailors those rules for core written units, whitespace handling, and reviewed Tamil abbreviations. Treat the baseline and the tailoring as distinct acceptance cases. [UAX #29 revision 47](https://www.unicode.org/reports/tr29/tr29-47.html)

### Word tokens

Apply the baseline word boundaries with a boundary at both ends of each whitespace run. A matched abbreviation is one token including its periods. Its ends are explicit word-token boundaries, including when the baseline would combine adjoining letters, a dot, and more letters into a single span. This lets the next name or amount have its own token. The final-period sentence rule does not affect the abbreviation token kind. Keep normally written inflected words and written compounds as surface units where the baseline keeps them together.

Omit whitespace runs. In order of precedence, classify each remaining span as an abbreviation, a word if it contains any Unicode letter (`L*`), a decimal-number token if it contains a decimal digit (`Nd`), or other content. Numeric punctuation stays with a number where the baseline permits it. The number kind describes a token and carries no numeric interpretation. Punctuation, symbols, emoji, and standalone marks or format controls are accounted for under other content when they do not belong to a listed token kind.

### Sentences

Keep the start and end of text and the hard boundaries defined by the baseline paragraph separators (`CR`, `LF`, and `Sep`), with `CRLF` treated as a unit. Trim only leading and trailing whole whitespace units from a sentence. Keep interior whitespace and closing punctuation that belongs to the sentence. Discard empty spans and return the final non-whitespace span even without a terminator.

### Tamil abbreviation matching

For both word and sentence boundaries, an admitted abbreviation must match a complete, canonically equivalent form at the start of text or after a scalar that is neither a letter, mark, decimal digit, nor format control. Its span starts and ends at written-unit boundaries. If approved candidates compete at the same start, select the longest eligible form. Admit an unspaced form only with evidence for that form or context.

For sentence boundaries, suppress breaks inside a matched abbreviation. Its final period suppresses a break attributable to that period only in the entry's documented continuation context. A following hard separator, end of text, or independent sentence terminator takes precedence. For an unknown form or an ineligible final-period context, retain the baseline behavior even when the baseline itself suppresses a break. The profile does not infer arbitrary names or sentence intent from undotted words.

The following forms have usage witnesses. Verify the proposed contexts against the exact source scalars before admitting them. A Tamil letter start is an `L*` scalar in `U+0B80..U+0BFF`. A decimal start is an `Nd` scalar. These are tests of the first scalar of the next written unit. Inline space means whole whitespace units containing no hard separator. The table states how many such units may be skipped. Examine punctuation literally. Skip it only when the entry lists it.

Apply the rule when the next text meets the listed predicate, even if a reader could interpret the continuation as the start of a new sentence. When the predicate fails, use the baseline for the final period. For example, pair `0BA4 0BBF 0BB0 0BC1 002E 0020 0B95` with `0BA4 0BBF 0BB0 0BC1 002E 000D 000A 0B95`. The first continues after the honorific when its predicate is admitted. The second keeps the hard boundary. Add an ineligible continuation fixture for each admitted entry and compare its final-period boundary with the baseline.

| Tamil form | Use and proposed final-period continuation context | Primary usage witness |
| --- | --- | --- |
| **திரு.** | Honorific. Tamil letter start after zero or more inline spaces. Admit zero spaces only where attested. | [Tamil Nadu HR&CE department profile](https://hrce.tn.gov.in/hrcehome/hrce_department.php), [Sri Lankan CIABOC institutional history](https://tamil.ciaboc.gov.lk/about) |
| **மு.க.** | Dotted initials. Tamil letter start after zero or more inline spaces. Admit zero spaces only where attested. | [Tamil Nadu HR&CE foreword, 26 April 2022](https://hrce.tn.gov.in/resources/docs/hrcescroll_doc/151/document_1.pdf), [Tamil Nadu cooperation policy note, 2025–26](https://rcs.tn.gov.in/public/uploads/policy/Policy%20Note%202025-26%20Tamil.pdf) |
| **பி.ப.** | Afternoon marker. Decimal start after one or more inline spaces. | [Sri Lankan Department of Agriculture, Tamil TV schedules](https://doa.gov.lk/naicc-services-tv-programs-ta/) |
| **மு.ப.** | Morning marker. Decimal start after one or more inline spaces. | [Sri Lankan Registrar General’s Department, transaction office hours](https://rgd.gov.lk/web/index.php/ta/services/document-land-registration/title/transactions) |
| **எ.கா.** | Example marker. Tamil letter start after at least one inline space. Where attested, allow one literal `)` or `:` between the period and the letter, with zero or more inline spaces on each side of that punctuation. | [Tamil Virtual Academy, Ukaram semester 2, printed page 143](https://www.tamilvu.org/courses/new_courses/level03/sem02/pdf/Ukaram_Sem_2.pdf), [Tamil Virtual Academy writing guide](https://www.tamilvu.org/sites/default/files/notice/Thamizhai_Pizhaiyinri_Ezhuthuvom.pdf) |
| **ரூ.** | Currency marker. Decimal start after zero or more inline spaces. Admit zero spaces only where attested. | [Tamil Nadu Rural Development FAQ, drinking-water connection question 6](https://vptax.tnrd.tn.gov.in/faq/), [Sri Lankan Gazette, 29 September 2023](https://documents.gov.lk/view/gazettes/2023/9/2023-09-29%28I-IIA%29T.pdf) |

Regional labels on sources describe where each form was witnessed. The same rules apply to the same text throughout Tamil Nadu and Sri Lanka. The abbreviation inventory records the form, context, region of attestation, and page or section locator. Cite government and educational publications as usage witnesses. Use independently composed passages for fixtures unless the source explicitly allows redistribution of the quoted material.

## Stopword profiles

- The default profile retains all tokens. The conservative profile removes a small reviewed set of common function words. The broader search profile contains that set plus additional reviewed words whose omission is useful for general search. Its additional entries must be documented so consumers can choose the effect on retrieval.
- The matching unit is a complete word token, compared by NFC equality. Unknown profiles return an explicit error. Filtering returns a subsequence of the unfiltered tokens with identical text, kind, and coordinates. Sentence output is independent of filtering.
- Use the Apache-licensed Lucene 9.8.0 Tamil stopword file as a candidate pool, with its TamilNLP attribution. Verify the exact admitted entries and the redistribution record before adding either named list. Document why each admitted entry belongs in its profile. Candidate list membership alone does not establish regional coverage or suitability for retrieval. [Pinned Lucene list](https://raw.githubusercontent.com/apache/lucene/releases/lucene/9.8.0/lucene/analysis/common/src/resources/org/apache/lucene/analysis/ta/stopwords.txt), [Lucene source attribution](https://lucene.apache.org/core/9_8_0/analysis/common/org/apache/lucene/analysis/ta/TamilAnalyzer.html), [TamilNLP license](https://github.com/AshokR/TamilNLP/blob/master/LICENSE)

## Verification before implementation and acceptance

1. Write escaped golden fixtures with independent expected boundaries and source references before implementing segmentation or filtering. Include positive and negative contexts for each admitted abbreviation, every profile, malformed input types, unknown profiles, and source offset cases for decomposed Tamil, Tamil and Latin digits, detached marks, ZWJ and ZWNJ, KSHA, both Shri forms, mixed scripts, emoji, and hard line separators.
2. Check baseline behavior against pinned Unicode test data and document deliberate tailoring. Verify byte slicing and written-unit slicing independently. Include regional invariance cases labeled for Tamil Nadu, Jaffna, Batticaloa, Vanni, and Up-Country and separate attested abbreviation uses from those invariance cases. [WordBreakTest 17.0.0](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/WordBreakTest.txt), [SentenceBreakTest 17.0.0](https://www.unicode.org/Public/17.0.0/ucd/auxiliary/SentenceBreakTest.txt), [Unicode License V3](https://www.unicode.org/license.txt)
3. Compare the documented default boundaries and the Phase 9 profile against independently annotated regional passages. Report missed and spurious boundaries by case group. Include spaced and adjacent abbreviations where attested, legitimate endings, joiner-interrupted atomic forms, and intact inflected words. Require exact matches for all reviewed fixtures. Report boundary accuracy and source integrity as distinct outcomes.
4. Once fixtures are approved for activation, verify them unchanged through the shared dispatcher and real Rust, Python, Node and browser WASM, and Dart consumers. Follow the [golden-vector lifecycle](bootstrap.md#golden-vector-lifecycle), including suite activation review.

### Private-engine evidence

The [candidate inventory](../../lexicon/tokenize-v0.1.toml) records six abbreviation forms and their spacing, next-unit classes, and source locators. The default `none` profile is empty. `conservative` includes **மற்றும்** and **அல்லது**. `broad` adds **போன்ற**. The table records the pinned upstream digest, Apache-2.0 terms, and TamilNLP attribution.

The planned suite contains 54 vectors. The standalone Rust tests reproduce all success rows, confirm the unsupported string profile error, and pass the 1,944 word and 512 sentence boundary cases in the Unicode 17 reference files. Two properties each ran 10,000 generated inputs. The annotated comparison found 4 missed and 8 spurious baseline word endpoints in the abbreviation group and 20 spurious baseline sentence endpoints in the abbreviation group. The tailored output matched every annotated endpoint. The baseline also produced eight spurious internal abbreviation endpoints in each of the hard-boundary and fallback groups.

On the Windows development host with the optimized test profile, the 143,360-byte mixed-script sample took about 7 ms for words and 6 ms for sentences. The 102,400-byte punctuation-heavy sample took about 7 ms for each. These observations cover the bundled examples and do not establish a time bound for arbitrary Unicode input.

### Preactivation parity

Review all inputs and expected results in the [readable fixture view](../../specs/024-tamil-tokenize/fixture-review.md).

### Activation, release scope, and archive verification (2026-11-26)

- **Owner approvals (T029–T030):** Owner approved activating all 54 fixtures in [`tests/golden/tokenize_v01.jsonl`](../../tests/golden/tokenize_v01.jsonl) (`tests/golden/manifest.json` -> `active`) and adding `tamil-tokenize` (Rank 2, `Apache-2.0`) to the public allowlist in [`release-policy.toml`](../../release-policy.toml) before `tamil-toolkit`, with synchronized distribution copies across all 10 public crates and 3 bindings (`157` verified release files). Registry publishing remains a separate manual release action under `docs/releases/policy.md`.
- **Shipped inventory ([`lexicon/tokenize-v0.1.toml`](../../lexicon/tokenize-v0.1.toml)):**
  - **Admitted abbreviations (6 forms):**
    - **திரு.** (`honorific`, SL witness): Tamil letter start after `min_spaces = 0`, no skipped punctuation.
    - **மு.க.** (`initials`, TN witness): Tamil letter start after `min_spaces = 0`, no skipped punctuation.
    - **பி.ப.** (`afternoon`, SL witness): decimal start after `min_spaces = 1`, no skipped punctuation.
    - **மு.ப.** (`morning`, SL witness): decimal start after `min_spaces = 1`, no skipped punctuation.
    - **எ.கா.** (`example`, TN witness): Tamil letter start after `min_spaces = 1`, optional literal `:` between the period and letter.
    - **ரூ.** (`currency`, TN witness): decimal start after `min_spaces = 0`, no skipped punctuation.
  - **Stopword profiles (Apache Lucene 9.8.0 / TamilNLP, Apache-2.0):**
    - `none`: empty set (default).
    - `conservative`: **மற்றும்**, **அல்லது**.
    - `broad`: **மற்றும்**, **அல்லது**, **போன்ற**.
- **Active parity and gate outcomes (T031):**
  - `just check-unicode`: passed (`40,265` active vectors = `40,211` existing + `54` tokenizer vectors; `157` synced release files verified).
  - `just agent-pre-stop-gate`: `cargo fmt --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `245` Rust workspace/property tests (including 10,000-case tokenizer properties and Unicode 17 baseline suites), `524` harness tests, Rust active parity (`40,265` vectors), Python (`32/32` tests), and Node/browser-target WASM (`40,291/40,291` tests) all passed.
  - `just test-dart` and Python quickstart wrapper check: `40,286/40,286` Dart tests passed with clean `dart analyze`, and the standalone Python wrapper check passed.
- **Isolated archive verification and dependency closure (T032):**
  - Dependency closure of `tamil-tokenize`: runtime `serde`, `tamil-core`, `tamil-norm`, `unicode-segmentation`; build `serde`, `toml`, `unicode-normalization` (zero `unsafe` code, Rank 2 acyclic DAG verified).
  - `default`-profile isolated archives passed across all four runtimes (`40,221` active golden rows each, including all 54 tokenizer vectors; 44 `lexicon-core`-gated dictionary vectors excluded by profile):
    - Rust: `tamil-tokenize-0.1.0.crate` (`29,133` bytes / `28.5 KiB`), `tamil-toolkit-0.1.0.crate` (`99,995` bytes / `97.7 KiB`), and all 8 other public crates extracted and verified in an isolated consumer.
    - Python: `tamil_toolkit-0.1.0.tar.gz` (`32,356,734` bytes) and `tamil_toolkit-0.1.0-cp311-abi3-win_amd64.whl` (`2,000,727` bytes) verified in an isolated venv.
    - npm: `tamil-toolkit-0.1.0.tgz` (`2,974,868` bytes; unpacked `7.8 MB`) verified with strict `tsc --noEmit` and isolated Node + browser-target WASM consumers.
    - Dart: `default` archive verified (`archive_sha256`: `1fa2e0dc6409f349c2a3dc43b58fc23a6649da96d5766a3c7c22601221ac361e`, `40,221` golden rows).
  - Note on `just release-check` `core`/`full` Rust `.crate` steps: because the published crates.io `tamil-toolkit` archive is intentionally slim (`Apache-2.0` only, excluding bulk `CC-BY-SA-4.0` `lexicon/dictionary/**`), the isolated `.crate` consumer cannot compile `lexicon-core`/`lexicon-full` from the `.crate` archive itself; full `core`-profile parity (`40,265` active vectors) is verified from the source checkout via `just agent-pre-stop-gate` and `just test-dart`.
- **Remaining limits:** Model inference, subword token IDs/counting, and model-budget chunking remain out of scope for Phase 9. Unlisted abbreviations fall back to the Unicode 17 sentence-break baseline.
