---
description: "Implementation tasks for Tamil word and sentence tokenization"
---

# Tasks — Tamil Word and Sentence Tokenization

**Input** [Feature specification](spec.md), [implementation plan](plan.md), [module contract](../../docs/specs/tokenize-v0.1.md), [research](research.md), [data model](data-model.md), [dispatcher contract](contracts/tokenizer.md), and [validation quickstart](quickstart.md).

Tests are required for this feature. Author the shared golden expectations before the Rust algorithms. A `[P]` marker identifies work that can run alongside the other tasks named in its parallel group once their prerequisites are complete. Keep regional attestation distinct from regional invariance. Phase 9 delivers linguistic source spans and opt-in stopword filtering. Model inference, subword encoders, and model-budget chunking belong to follow-up work.

## Phase 1 — Setup and pinned Unicode references

- [X] T001 [P] Pin the official Unicode 17.0.0 `WordBreakTest.txt` and `SentenceBreakTest.txt` under `tests/reference/unicode-17.0.0/` from the upstream links in [research](research.md). Retain the original input and expected boundary markers and record the SHA-256 values for T003.
- [X] T002 [P] Produce the compact Unicode 17.0.0 property projection in `lexicon/tokenize-unicode-v17.toml` with a deterministic generator in `tools/generate_tokenize_unicode.py`. Use the pinned general category, whitespace, and sentence break data for `L*`, `M*`, `Nd`, `Cf`, `White_Space`, and the required sentence classes. Record the upstream and projection hashes for T003.
- [X] T003 Record sources, hashes, any selection, and license references for T001–T002 in `tests/reference/unicode-17.0.0/sources.json`, reusing `tests/reference/unicode-17.0.0/LICENSE.txt`. Verify the raw test files and regenerate the same property projection from the pinned inputs.

## Phase 2 — Foundation and shared evidence

- [X] T004 Curate attested abbreviation forms and contexts in `lexicon/tokenize-v0.1.toml` against `docs/specs/tokenize-v0.1.md`. For each admitted form, record “Complete NFC form with the recorded periods. Keys are unique after canonical normalization.” Record use class, canonical eligibility, sentence continuation independently of word recognition, spacing, permissible continuation punctuation, region, source locator, and redistribution terms. Check the witnessed morning and afternoon markers and adjacent forms. Freeze each observable next-unit, whitespace, and punctuation predicate before T006–T007.
- [X] T005 Curate the stopword profiles in `lexicon/tokenize-v0.1.toml` from the pinned candidate list. Define `none` as “Empty set. Default when omitted.” Give `conservative` a reviewed subset and `broad` a “Strict superset of `conservative`, with rationale for the additional entries.” Record evidence, rights, and rationale for each unique NFC word, including an independently defensible term with a canonical decomposition.
- [X] T006 Author escaped word and offset goldens in `tests/golden/tokenize_v01.jsonl`. Independently annotate Tamil Nadu and Sri Lankan passages and tag the boundary groups. Cover source slicing, empty and whitespace input, adjacent abbreviations, inflected words, decomposed vowel signs, KSHA and both Shri spellings, joiner-interrupted units, detached marks, CRLF, digits, mixed scripts, and emoji. Include whole-unit whitespace treatment and punctuation or symbols emitted as `other`.
- [X] T007 Add independently annotated sentence goldens to `tests/golden/tokenize_v01.jsonl`. Give each admitted abbreviation positive and negative or boundary cases, covering attested adjacent forms, true endings with quotes or parentheses, decimals, unknown dotted forms, hard breaks, and end of text. Add shared boundary invariance cases labeled for Tamil Nadu, Jaffna, Batticaloa, Vanni, and Up-Country. Pair continuation fixtures with hard boundaries and out-of-predicate examples, asserting baseline fallback for the latter.
- [X] T008 Add stopword and request-validation goldens to `tests/golden/tokenize_v01.jsonl`. Cover omission and explicit `none`, `conservative`, `broad`, canonical equivalence, unsupported strings, null and wrong types, validation precedence, full-word-only matching, retained non-word tokens, unchanged spans, and sentence independence. Use the exact errors in `specs/024-tamil-tokenize/contracts/tokenizer.md`.
- [X] T009 Register both operations and a `planned` reason in `tests/golden/manifest.json`. Verify IDs, evidence, dialect and region fields, and exact exceptions on each affected `/input/text` and `/expected/<index>/text` value in `tests/golden/tokenize_v01.jsonl`. Run `just check-unicode` before engine work and record that the suite is planned.
- [X] T010 Add the substantive private Rank 2 crate in `crates/tamil-tokenize/Cargo.toml` and `crates/tamil-tokenize/src/lib.rs`, including `Cargo.toml` and `Cargo.lock` workspace wiring. In `crates/tamil-tokenize/src/span.rs`, index original `tamil_core::Letters::new` endpoints and define the fields `text`, `start_byte`, `end_byte`, `start_unit`, and `end_unit`. Enforce “Both ranges are nonempty, zero-based and half-open. Both select `text` from the same source. Endpoints are written-unit boundaries.”
- [X] T011 Compile immutable sorted lexical tables and the property projection in `crates/tamil-tokenize/build.rs` and `crates/tamil-tokenize/src/tables.rs`. Validate NFC, canonical uniqueness, supported contexts, source metadata, and profile containment. Use root canonical inputs for private development and support the generated release copies for isolated archive builds.
- [X] T012 Implement shared abbreviation recognition in `crates/tamil-tokenize/src/abbreviation.rs`. Match canonically at original unit boundaries using exact left eligibility, longest eligible form at a start, and attested spacing or adjacency. Expose the matched range and continuation context to the two boundary passes.
- [X] T013 Build a standalone golden loader in `crates/tamil-tokenize/tests/support/mod.rs` and a raw baseline conformance test in `crates/tamil-tokenize/tests/unicode_baseline.rs`. Use the locked full word and sentence boundary iterators against both Unicode 17 test files before applying Tamil tailoring. Reuse the loader for the shared success fixtures in each story.

## Phase 3 — User Story 1 — Locate words in the original text (P1, MVP)

**Goal** — Return word and other token spans that tools can use to highlight exact source text.

**Independent test** — Use the private Rust engine with filtering disabled. Match the word fixtures, including separate adjacent abbreviation boundaries and intact surface inflections, and recover each token using either range.

- [X] T014 [P] [US1] Write `crates/tamil-tokenize/tests/word_golden.rs` against the unfiltered word rows from T006, asserting exact kinds, slices, and original offsets for every returned token.
- [X] T015 [P] [US1] Write the 10,000-case word-span property tests in `crates/tamil-tokenize/tests/word_properties.rs` for ordered non-overlap, exact byte and unit slicing, preservation of format controls, and complete non-whitespace coverage.
- [X] T016 [US1] Implement the unfiltered word pass in `crates/tamil-tokenize/src/words.rs` and expose `tokenize_words(text, StopwordProfile::None)` through `crates/tamil-tokenize/src/lib.rs` for the private MVP. Use full baseline word boundary offsets, add whitespace-run boundaries and both explicit ends of matched abbreviations, collapse abbreviation interiors, and suppress cuts inside written units. Return `[]` for empty and whitespace-only text. Classify using `abbreviation`, `word`, `number`, and `other` in the precedence from the module contract. Run the word fixture and property tests.

## Phase 4 — User Story 2 — Read sentences containing Tamil abbreviations (P2)

**Goal** — Preserve sentences containing attested abbreviations and honor genuine sentence and paragraph endings.

**Independent test** — Use the private Rust sentence API directly. A reviewed honorific followed by its name stays in one sentence, and hard separators, standalone terminators, and end of text produce the annotated spans.

- [X] T017 [P] [US2] Write `crates/tamil-tokenize/tests/sentence_golden.rs` against T007, asserting exact original ranges and a negative or boundary result for each admitted abbreviation.
- [X] T018 [P] [US2] Write the 10,000-case sentence-span properties in `crates/tamil-tokenize/tests/sentence_properties.rs` for exact reconstruction, ordered non-overlap, hard separators, and complete non-whitespace coverage.
- [X] T019 [US2] Implement `segment_sentences` in `crates/tamil-tokenize/src/sentences.rs` and expose it in `crates/tamil-tokenize/src/lib.rs`. Map a baseline break after closing punctuation or trailing space to its triggering period. Preserve hard separators, independent terminators, and EOF. Apply final-period suppression only in reviewed contexts. “Trim outer whole whitespace units. Preserve interior whitespace and closing punctuation assigned to the sentence.” Run the sentence fixture and property tests.

## Phase 5 — User Story 3 — Control which stopwords a search omits (P3)

**Goal** — Offer all three profiles while preserving the text, kind, order, and both source ranges of surviving tokens.

**Independent test** — Run one reviewed passage under all profiles. Verify that the lists differ as specified, only complete canonically equivalent words match, and untouched tokens keep their ranges.

- [X] T020 [P] [US3] Write `crates/tamil-tokenize/tests/stopword_golden.rs` from T008. Compare the three results to the unfiltered sequence, including a broader-list-only term, canonical NFC/NFD matching, unlisted inflections, joiner-bearing variants, retained non-word tokens, and an unsupported profile parse.
- [X] T021 [US3] Extend `StopwordProfile` to all three admitted options and implement NFC equality matching in `crates/tamil-tokenize/src/stopwords.rs`. Wire filtering through `crates/tamil-tokenize/src/words.rs` and `crates/tamil-tokenize/src/lib.rs`. “A filtered word list is a stable subsequence of the unfiltered list.” Apply matching only to `word` tokens and preserve every retained token field. Run all three story suites.

## Phase 6 — Cross-cutting verification and reviewed integration

- [X] T022 Compare default and tailored word and sentence endpoints to the regional annotations in `crates/tamil-tokenize/tests/boundary_evaluation.rs`. Compare matched, missed, and spurious original byte boundaries by case group using a consistent whitespace policy. Verify exact tailored results, no interior written-unit cuts, and source integrity. Record observed costs on long mixed-script and punctuation-heavy text in `docs/specs/tokenize-v0.1.md`. Run `just agent-post-edit` with the private engine and planned vectors.
- [X] T023 Prepare the isolated preactivation checkout described in `specs/024-tamil-tokenize/quickstart.md`. In that checkout, add the provisional `tamil-tokenize` dependency to `crates/tamil-toolkit/Cargo.toml` and refresh `Cargo.lock`. Keep the existing public release scope in `release-policy.toml` until it is reviewed.
- [X] T024 Add both operations, the inventory entries, and the re-export in `crates/tamil-toolkit/src/lib.rs` in the isolated candidate. Validate object, then `text`, then optional `stopword_profile`. Preserve exact contract errors, omission versus explicit null, and existing unknown-field and envelope handling through the shared dispatcher.
- [X] T025 [P] Add Python convenience functions, typed mappings, and export names in `bindings/python/python/tamil_toolkit/__init__.py` and `bindings/python/python/tamil_toolkit/__init__.pyi` through the existing dispatcher.
- [X] T026 [P] Add typed `createApi` functions in `bindings/js-wasm/src/api.ts` and exports through `bindings/js-wasm/src/index.ts` and `bindings/js-wasm/src/web.ts`. Preserve UTF-8 byte and written-unit coordinates and rebuild the declarations. Add direct positive span and unsupported-profile checks for both WASM exports in `bindings/js-wasm/tests/golden.test.ts`.
- [X] T027 [P] Add typed Dart methods and result records in `bindings/dart-flutter/lib/tamil_toolkit.dart` through the existing JSON C ABI. Omit an unspecified profile and preserve the dispatcher errors and original offsets. Add direct positive span and unsupported-profile checks against the host library in `bindings/dart-flutter/test/golden_test.dart`.
- [X] T028 Run the lower-level real Rust, Python, Node/browser-target WASM, and Dart commands in `specs/024-tamil-tokenize/quickstart.md` using `TAMIL_GOLDEN_INCLUDE_PLANNED=tokenize_v01.jsonl` in the isolated candidate. Verify shared rows, typed entry points, and error messages. Record exact planned counts and regional boundary results separately from active parity in `docs/specs/tokenize-v0.1.md`. Run those direct checks separately from dispatcher parity, along with the Python wrapper check.
- [X] T029 Record owner review for fixture activation in `docs/specs/tokenize-v0.1.md` and apply it in `tests/golden/manifest.json` only after approval. Obtain separate release-scope review for the proposed dependency closure and package scope in `release-policy.toml` under `docs/releases/policy.md`.
- [X] T030 Prepare the reviewed package scope in `release-policy.toml`, `crates/tamil-tokenize/Cargo.toml`, `crates/tamil-toolkit/Cargo.toml`, `Cargo.toml`, `Cargo.lock`, and `.github/workflows/publish-crate.yml`. Add canonical release input, notice, license, and README rules in `tools/release_files.py`. Put `tamil-tokenize` before its dependent and run `just sync-release-files` to create distribution copies.
- [X] T031 Run `just agent-pre-stop-gate`, `just test-dart`, and the quickstart wrapper checks in the reviewed integration candidate following `specs/024-tamil-tokenize/quickstart.md`. Confirm all active suites run in the real runtimes and `tools/release_files.py --check` accepts the synchronized data.
- [X] T032 Run `just release-check` for isolated archive consumers and record the package sizes and dependency closure in `docs/specs/tokenize-v0.1.md`. Keep publication under its separate manual release action.
- [X] T033 Record accepted fixture counts, boundaries tested, runtime and archive outcomes, and any remaining limits in `docs/specs/tokenize-v0.1.md`, `docs/status.md`, and `CHANGELOG.md` under Unreleased. Link the shipped inventory in `lexicon/tokenize-v0.1.toml` from the module contract, document each admitted abbreviation and its exact contexts, and identify the shipped `none`, `conservative`, and `broad` membership.

## Dependencies & Execution Order

- T001 and T002 can run together. T003 depends on both. T004–T009 establish the canonical lexical data and all shared golden cases before T010–T012 begin. T013 needs T003, T009, and T010. Complete the foundation before implementing the story APIs.
- **US1** T014 and T015 can run together after T013. T016 depends on them and the shared foundation.
- **US2** T017 and T018 can run together after T013. T019 depends on them and the shared abbreviation matcher. The sentence algorithm is independent of the word and filtering passes. Serialize edits to `crates/tamil-tokenize/src/lib.rs` when stories overlap.
- **US3** T020 depends on T013 and the shared profile fixtures. T021 depends on T020 and on US1's word pass. It can be tested without US2’s output.
- T022 follows all stories. T023–T024 create the isolated candidate, after which T025–T027 can run together in their separate adapter directories. T028 requires the completed candidate. T029–T033 follow in order through fixture approval, release-scope review, canonical gates, and archive evidence.

## Parallel Execution Examples

- **US1** Write T014’s shared-fixture assertions and T015’s original-span properties separately before implementing the word pass in T016.
- **US2** Write T017’s named abbreviation regressions and T018’s generated properties separately before implementing the sentence pass in T019.
- **US3** Once the fixtures and test loader exist, T020 can proceed alongside US2’s tests in separate files. Apply filtering in T021 after the unfiltered word pass is ready.

## Implementation Strategy

1. **MVP** — Finish the foundation and US1. Demonstrate default word tokenization in the private Rust crate with matching byte and written-unit spans.
2. **Incremental delivery** — Add and independently verify US2 sentence boundaries and US3 opt-in stopwords. Collect the baseline and tailored boundary comparison before building the candidate.
3. **Integration** — Prove planned vectors in every real runtime, then record both reviews and run the canonical and archive gates on the approved dependency closure.
