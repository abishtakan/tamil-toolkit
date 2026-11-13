# Feature Specification: Validate Reused Rust APIs & NFC/NFD Normalization (`tamil-core`, `tamil-norm`, `tamil-toolkit`)

**Feature Branch**: `022-validate-reused-rust-apis`  
**Created**: 2026-11-13  
**Status**: Draft  
**Input**: User description: "Validate the Rust functions we'll reuse across tamil-core, tamil-norm, and tamil-toolkit before implementing Feature 021, and make sure tamil-norm is correctly performing NFC and NFD normalizations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical NFC & NFD Normalization Correctness in `tamil-norm` (Priority: P1)

As a maintainer preparing for Feature 021 lexicon curation, I need `tamil_norm::normalize_nfc` and `tamil_norm::normalize_nfd` (along with downstream `tamil-norm` functions consuming NFC/NFD inputs) to strictly satisfy Unicode 17.0.0 canonical equivalence, format-control preservation, and non-destructive guarantees across Rust, Python, WASM, and Dart.

**Why this priority**: Feature 021 normalizes, keys, indexes, and repairs tens of thousands of lexicon entries using `tamil-norm`; any subtle NFC/NFD defect, silent character loss, or NFD-input handling mismatch in `tamil-norm` would corrupt generated static tables and search indexes.

**Independent Test**: Run `tamil-norm` unit/property tests and active canonical normalization golden vectors across Rust, Python, WASM, and Dart covering Tamil split vowel signs, combining mark reordering, joiners/format controls, Shri variants, non-NFC malformed inputs, mixed scripts, and NFD inputs passed into `repair_tamil_text` and `fold_for_search`.

**Acceptance Scenarios**:

1. **Given** canonically decomposed Tamil sequences (two-part vowel signs `\u{0BC6}\u{0BBE}`, `\u{0BC7}\u{0BBE}`, `\u{0BC6}\u{0BD7}` with consonants/conjuncts, and `\u{0B92}\u{0BD7}`), **When** processed with `normalize_nfc` and `normalize_nfd`, **Then** `normalize_nfc` produces the composed scalar form (`\u{0BCA}`, `\u{0BCB}`, `\u{0BCC}`, `\u{0B94}`) and `normalize_nfd` produces the decomposed base + combining parts in canonical order, with both functions satisfying idempotence and cross-form round-trip invariance (`nfc(nfd(x)) == nfc(x)`, `nfd(nfc(x)) == nfd(x)`).
2. **Given** strings containing invisible format controls (`ZWJ` `\u{200D}`, `ZWNJ` `\u{200C}`, `BOM` `\u{FEFF}`, `SHY` `\u{00AD}`), Shri variants (`ஸ்ரீ` vs `ஶ்ரீ`), or orthographically malformed sequences (e.g., repeated vowel signs such as `\u{0BA4}\u{0BC1}\u{0BBE}`), **When** normalized via `normalize_nfc` or `normalize_nfd`, **Then** format controls are preserved verbatim without silent stripping, `ஸ்ரீ` and `ஶ்ரீ` remain distinct, and malformed sequences are not repaired or folded.
3. **Given** canonically equivalent NFC and NFD forms of Tamil and Grantha words (including `க்ஷொ` / `க்ஷோ` / `க்ஷௌ` and mixed-script text), **When** passed to `fold_for_search` or `repair_tamil_text`, **Then** `fold_for_search` yields identical folded outputs for canonically equivalent NFC and NFD inputs and `repair_tamil_text` produces consistent repair diagnostics without corrupting valid decomposed forms.

---

### User Story 2 - Validate Reused `tamil-core` Primitives & Diagnostics (Priority: P2)

As an engineer implementing Feature 021's build-time compiler, inspection pipelines, and syllable/quantity utilities, I need every `tamil-core` function planned for reuse to have verified contracts, documented boundary behaviors, and explicit regression coverage.

**Why this priority**: Feature 021 relies on `tamil-core` for Unicode normalization, letter segmentation, uyirmei splitting/composition, string inspection, phonetic/quantity classification, and cognate matching; unverified assumptions about multi-letter inputs, NFD inputs, or joiner clustering could cause subtle bugs during lexicon compilation.

**Independent Test**: Run `tamil-core` unit/property and integration suites plus cross-runtime parity checks verifying `normalize_nfc`, `normalize_nfd`, `get_letters`, `Letters`, `split_uyirmei`, `compose_uyirmei`, `inspect_tamil_string`, `classify_quantity`, `baseline_maathirai`, `get_cognate`, `are_cognates`, and `get_olippasai`.

**Acceptance Scenarios**:

1. **Given** single-letter and multi-letter strings (including NFD sequences, Grantha conjuncts, and `ZWJ`/`ZWNJ` joiners), **When** processed with `get_letters`, `Letters::new`, `split_uyirmei`, and `compose_uyirmei`, **Then** `get_letters` returns NFC-normalized tailored clusters while zero-allocation `Letters::new` operates strictly on caller-provided normalization, and `split_uyirmei`/`compose_uyirmei` round-trip accurately across valid Tamil/Grantha combinations.
2. **Given** strings containing `ZWJ`, `ZWNJ`, non-Tamil scripts, or unexpected controls, **When** inspected via `inspect_tamil_string`, **Then** the inspection accurately exposes scalar/control presence without silently removing joiners, and any cluster-classification or scalar-offset constraints needed by Feature 021 are explicitly tested and verified.
3. **Given** single tailored letters vs multi-letter words, **When** passed to `classify_quantity` and `baseline_maathirai`, **Then** single letters return accurate prosodic quantity and baseline maathirai values while multi-letter inputs follow the documented single-letter boundary contract (`Other` / `0.0`).

---

### User Story 3 - Validate `tamil-toolkit` Dispatcher, CLI & Build-Time Reuse Readiness (Priority: P3)

As an integrator wiring Feature 021 operations into `tamil-toolkit`, CLI subcommands, and cross-language bindings, I need the unified `tamil-toolkit` dispatcher, CLI argument handling, build configuration, and FFI bindings to accurately expose all implemented operations and enforce consistent error contracts across Rust, Python, WASM, and Dart.

**Why this priority**: Feature 021 exposes new operations through `tamil-toolkit::execute` (`OPERATIONS`), build-time `lexicon/` compilation (`build.rs`), and multi-language bindings; existing drift between `OPERATIONS`, implemented match arms, CLI flags, or error validation would block parity checks or mask invalid inputs.

**Independent Test**: Verify `OPERATIONS` alignment against `execute()`, test invalid arguments / missing inputs / unknown CLI flags / unknown operations, confirm `tamil-toolkit` build/packaging policy compliance, and run the full tri-runtime parity and Dart C ABI test suites.

**Acceptance Scenarios**:

1. **Given** the complete set of operations implemented in `tamil_toolkit::execute`, **When** inspected against `tamil_toolkit::OPERATIONS` and binding surfaces, **Then** every implemented operation is listed in `OPERATIONS` and responds deterministically across Rust, Python, WASM, and Dart with consistent structured errors for unsupported ops or malformed payloads.
2. **Given** invalid CLI inputs such as an unrecognized `norm fold --profile <unknown>` value, **When** invoked via the `tamil-toolkit` CLI binary, **Then** the CLI rejects the invalid profile with a non-zero exit status rather than silently falling back to a default profile.
3. **Given** all updated golden vectors and binding rebuilds, **When** running the repository quality gates (`check-unicode`, `check-release-policy`, `test-parity`, `test-dart`), **Then** every active vector passes identically across Rust, Python, WASM, and Dart with zero skipped checks or stale distribution files.

### Edge Cases

- Empty strings `""`, pure ASCII strings, and whitespace-only strings across `normalize_nfc`, `normalize_nfd`, `fold_for_search`, `repair_tamil_text`, `get_letters`, and `inspect_tamil_string`.
- Split vowel signs (`\u{0BCA}`, `\u{0BCB}`, `\u{0BCC}`, `\u{0B94}`) both pre-composed and decomposed (`\u{0BC6}\u{0BBE}`, `\u{0BC7}\u{0BBE}`, `\u{0BC6}\u{0BD7}`, `\u{0B92}\u{0BD7}`) combined with base Tamil consonants, Grantha consonants (`ஜ`, `ஷ`, `ஸ`, `ஹ`), and `க்ஷ` conjuncts.
- Multiple combining marks requiring Unicode CCC reordering (e.g., Tamil virama `\u{0BCD}` CCC=9 paired with non-zero CCC diacritics such as `\u{0301}` CCC=230 or `\u{0323}` CCC=220).
- Format controls (`ZWJ` `\u{200D}`, `ZWNJ` `\u{200C}`, `BOM` `\u{FEFF}`, `SHY` `\u{00AD}`) adjacent to consonants, virama, or split vowel signs, ensuring `normalize_nfc`/`normalize_nfd` never drop them and documenting/verifying `inspect_tamil_string` reporting behavior.
- Orthographically anomalous double vowel signs (e.g., `\u{0BA4}\u{0BC1}\u{0BBE}` from Tamil Lexicon intake Entry 4848) verifying `normalize_nfc`/`normalize_nfd` do not coerce them.
- Dispatcher requests with missing/null `input` keys vs non-string `input` payloads vs unknown `op` names.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tamil_norm::normalize_nfc` and `tamil_norm::normalize_nfd` MUST pass comprehensive canonical composition and decomposition validation aligned with Unicode 17.0.0 UAX #15, including all Tamil two-part vowel signs (`\u{0BCA}`, `\u{0BCB}`, `\u{0BCC}`, `\u{0B94}`), multi-mark CCC reordering, idempotence, and cross-form round-trips (`nfc(nfd(s)) == nfc(s)`, `nfd(nfc(s)) == nfd(s)`).
- **FR-002**: `tamil_norm::normalize_nfc` and `tamil_norm::normalize_nfd` MUST preserve invisible format controls (`ZWJ`, `ZWNJ`, `BOM`, `SHY`), non-Tamil text, and Shri spelling distinctions (`ஸ்ரீ` vs `ஶ்ரீ`), and MUST NOT perform silent orthographic repair on malformed sequences.
- **FR-003**: Downstream `tamil-norm` entry points (`fold_for_search`, `repair_tamil_text`) MUST produce consistent canonical results regardless of whether valid input text is supplied in NFC or NFD form (e.g., decomposed Grantha conjuncts with split vowels such as `\u{0B95}\u{0BCD}\u{0BB7}\u{0BC6}\u{0BBE}`).
- **FR-004**: Canonical normalization golden vectors MUST exist as dedicated escaped JSONL fixture cases registered in `tests/golden/manifest.json` and run actively across Rust, Python, WASM, and Dart, accompanied by `tamil-norm` property tests covering random NFC/NFD/mixed/format-control inputs.
- **FR-005**: All Feature 021-reused `tamil-core` functions (`normalize_nfc`, `normalize_nfd`, `get_letters`, `Letters`, `split_uyirmei`, `compose_uyirmei`, `inspect_tamil_string`, `classify_quantity`, `baseline_maathirai`, `get_cognate`, `are_cognates`, `get_olippasai`) MUST have validated contract tests covering edge cases (empty inputs, NFD vs NFC segmentation, Grantha conjuncts, format controls/joiner impact on cluster counts, and single-letter boundary behavior for quantity/maathirai).
- **FR-006**: `tamil_toolkit::OPERATIONS` MUST match every operation implemented in `tamil_toolkit::execute()`, without omitting active operations or listing unimplemented stubs.
- **FR-007**: `tamil-toolkit` dispatcher and CLI MUST validate inputs cleanly (rejecting unknown `fold` `--profile` values with explicit non-zero errors and maintaining consistent JSON error semantics for unsupported operations and invalid payloads).
- **FR-008**: All reused crate boundaries and build readiness for Feature 021 (`tamil-core`, `tamil-norm`, `tamil-toolkit` crate dependencies and release-policy compliance) MUST be verified without breaking or altering Feature 021 specification files or immutable source intake files.
- **FR-009**: All changes MUST pass repository gates sequentially on the host environment (`just check-unicode`, `just check-release-policy`, `just test-rust`, `just test-parity`, `just test-dart`, `just agent-pre-stop-gate`) after rebuilding Python, WASM, and C/Dart bindings.

### Key Entities

- **Validation Matrix**: Mapping from each reused API in `tamil-core`, `tamil-norm`, and `tamil-toolkit` to its verified contract guarantees, known preconditions/limits (e.g., single-letter scope or non-normalizing `Letters::new`), and executable test evidence.
- **Canonical Normalization Fixture Set**: Escaped JSONL golden cases (`tests/golden/norm_canonical.jsonl` or equivalent active suite) and property-based invariants verifying `normalize_nfc`, `normalize_nfd`, and NFD-input resilience in `tamil-norm`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `tamil-norm` executes at least 10,000 property-test cases each for NFC and NFD normalization invariants plus dedicated escaped golden vectors covering 100% of Tamil two-part vowel signs, Shri variants, joiners/format controls, CCC reordering, malformed double vowels, and NFD inputs to `fold_for_search`/`repair_tamil_text`, with zero failures.
- **SC-002**: 100% of operations handled by `tamil_toolkit::execute()` appear in `tamil_toolkit::OPERATIONS` and return matching results/errors across Rust, Python, WASM, and Dart parity runs.
- **SC-003**: Every reused `tamil-core`, `tamil-norm`, and `tamil-toolkit` function required by Feature 021 has documented, test-backed contract verification in `specs/022-validate-reused-rust-apis/contracts/` with zero unresolved correctness blockers.
- **SC-004**: Full verification suite (`check-unicode`, `check-release-policy`, `test-rust`, `sync-bindings`, `test-parity`, `test-dart`, `agent-pre-stop-gate`) exits cleanly with zero failures and zero skipped active tests after final edits.

## Assumptions

- Feature `021-lexicon-curation` (`specs/021-lexicon-curation/`) remains the target consumer of these validated Rust APIs and MUST NOT be overwritten or regressed during Feature 022 execution.
- `unicode-normalization` `0.1.26` (currently locked in `Cargo.lock`) implements Unicode 17.0.0 NFC/NFD algorithms; Feature 022 validates this empirically across Tamil and mixed-script edge cases rather than reimplementing Unicode tables manually.
- Pre-existing single-letter contracts for `classify_quantity`/`baseline_maathirai` and non-normalizing zero-allocation `Letters::new` are preserved unless a genuine correctness bug is discovered; Feature 021 callers normalize inputs first via `normalize_nfc` / `get_letters`.
- `.specify/feature.json` will track `specs/022-validate-reused-rust-apis` during the Feature 022 SpecKit lifecycle and be documented cleanly in `docs/status.md` upon completion so work can resume seamlessly on Feature 021.
