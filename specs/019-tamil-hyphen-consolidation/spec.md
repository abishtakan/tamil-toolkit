# Feature Specification: tamil-hyphen Release Policy, Manifest & WASM Consolidation

**Feature Branch**: `019-tamil-hyphen-consolidation`

**Created**: 2026-11-08

**Status**: Completed

**Input**: User description: "phase 3. then do the full speckit lifecycle"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Refactor tamil-hyphen with tamil-core Phonological Primitives (Priority: P1)

As a Tamil typography developer, I want `tamil-hyphen` to leverage the centralized phonological and syllable nucleus primitives from `tamil-core` (`is_kuril`, `is_nedil`, `is_mei`, `is_aytham`, `LetterQuantity`, `baseline_maathirai`, `get_olippasai`), so that syllable breakdown and letter classification are consistent across the entire toolkit workspace while preserving typographic minimum-margin merging rules.

**Why this priority**: Core architectural integrity. Eliminates duplicated classification logic and guarantees that `tamil-hyphen` strictly respects the Rank 0 -> Rank 2 dependency boundary without behavioral regression.

**Independent Test**: Can be tested independently via `cargo test -p tamil-hyphen` and verifying unit tests for `classify_letter`, `hyphenation_points`, and `hyphenate_word`.

**Acceptance Scenarios**:
1. **Given** any Tamil word (e.g. `தமிழ்நாடு`, `பல்கலைக்கழகம்`, `துஷ்பிரயோகம்`), **When** `hyphenate_word` is called, **Then** letter classification and nucleus identification delegate to `tamil-core` primitives and produce identical typographic break points respecting `left_min` and `right_min`.
2. **Given** words containing Grantha onsets (`ஸ்ரீ`, `க்ஷ`) or pure consonants, **When** passed to `classify_letter` and `hyphenation_points`, **Then** onsets and codas bind properly to their respective syllables without dangling pulli markers.

---

### User Story 2 - Manifest Activation & Release Policy Promotion (Priority: P1)

As a release engineer and package consumer, I want `hyphen_syllable.jsonl` marked `active` in `tests/golden/manifest.json` and `tamil-hyphen` promoted to `public_crates` in `release-policy.toml`, with the temporary private exemption in `tools/release_policy.py` eliminated, so that `tamil-hyphen` is officially release-ready.

**Why this priority**: Mandatory Phase 3 exit gate in `docs/specs/architecture-roadmap.md`. Unlocks formal public distribution and multi-runtime parity enforcement for hyphenation.

**Independent Test**: Can be tested independently via `just check-release-policy` and running `cargo test --test golden_suite`.

**Acceptance Scenarios**:
1. **Given** `tests/golden/manifest.json`, **When** inspected by test runners, **Then** `hyphen_syllable.jsonl` has `"status": "active"`.
2. **Given** `release-policy.toml`, **When** `public_crates` is checked, **Then** `tamil-hyphen` is present in topological order preceding `tamil-toolkit`.
3. **Given** `tools/release_policy.py`, **When** `check_public_dependency_closure` and umbrella checks run, **Then** no special-cased exemptions for `tamil-hyphen` exist, and `just check-release-policy` passes cleanly.

---

### User Story 3 - Consolidation of Playground & Word Add-in onto Shared Rust/WASM Engine (Priority: P2)

As a web and Office Add-in developer, I want the Playground and Microsoft Word Add-in to rely strictly on the single shared Rust/WASM engine for Tamil hyphenation and syllable breakdown, eliminating divergent JavaScript reimplementations while maintaining offline client-side execution.

**Why this priority**: Adheres directly to Constitution Principle I (Rust Owns Linguistic Behavior) and Constitution Principle III (Tri-Runtime Parity).

**Independent Test**: Can be tested independently by running `tests/integrations/test_word_addin_contract.js` and Vitest in `playground/`.

**Acceptance Scenarios**:
1. **Given** the Word Add-in runtime, **When** text or OOXML documents are hyphenated, **Then** syllable and hyphenation calculations route through the shared WASM engine or validated engine contracts without divergent logic.
2. **Given** the Playground web application, **When** the hyphenator tool processes text, **Then** all results match the Rust engine outputs.

---

### User Story 4 - CLI Subcommands Expansion for Existing Crates (Priority: P2)

As a command-line user and automator, I want `tamil-toolkit` CLI to provide convenient, intuitive subcommands for existing library crates (`core`, `norm`, `codec`, `collate`, `numerals`, `calendar`, and `hyphen`), so that toolkit capabilities can be directly invoked from terminal workflows and shell scripts.

**Why this priority**: Required milestone deliverable in `docs/specs/architecture-roadmap.md` Phase 3. Transforms the CLI from a hyphen-only tool into a comprehensive workspace CLI.

**Independent Test**: Can be tested independently by running `tamil-toolkit <subcommand>` with sample inputs and verifying standard output and exit codes.

**Acceptance Scenarios**:
1. **Given** CLI command `tamil-toolkit core letters "தமிழ்"`, **When** executed, **Then** it outputs tailored letters.
2. **Given** CLI command `tamil-toolkit norm nfc "..."`, **When** executed, **Then** it normalizes input to NFC.
3. **Given** CLI command `tamil-toolkit numerals to-words 2026`, **When** executed, **Then** it outputs Tamil numeral words.
4. **Given** CLI command `tamil-toolkit calendar info --date 2026-11-08`, **When** executed, **Then** it outputs Tamil date details.
5. **Given** CLI command `tamil-toolkit collate compare "அம்மா" "ஆடு"`, **When** executed, **Then** it outputs alphabetical comparison result.
6. **Given** CLI command `tamil-toolkit codec convert ...`, **When** executed, **Then** it performs the requested encoding conversion.

---

### Edge Cases

- **Boundary Minimum Margins**: When a word has fewer letters than `left_min + right_min`, the hyphenator must return the unhyphenated word with empty points.
- **Embedded Joiners / Hyphens**: Input words containing pre-existing soft hyphens (`\u{00AD}`), word joiners (`\u{2060}`), or zero-width spaces (`\u{200B}`) must have them stripped before calculating boundaries.
- **Grantha and Consonant Clusters**: Clusters like `க்ஷ` or `ஸ்ரீ` must be treated atomically or as valid onsets without generating orphan viramas (`Pulli`).
- **Punctuation and Whitespace in Text**: Hyphenation of full paragraphs/sentences must preserve inter-word spaces, line breaks, and punctuation intact.
- **CLI Argument Validation**: Incomplete CLI arguments or invalid flags must emit helpful error messages and exit with non-zero exit codes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tamil-hyphen` MUST consume `tamil-core` phonological & nucleus primitives (`is_kuril`, `is_nedil`, `is_mei`, `is_aytham`, `LetterQuantity`, `baseline_maathirai`, `get_olippasai`) for letter classification and sound unit segmentation.
- **FR-002**: `tamil-hyphen` MUST maintain typographic minimum-margin segmentation rules (`left_min`, `right_min`, default 3/3) and preserve existing API contracts (`classify_letter`, `hyphenation_points`, `hyphenate_word`, `hyphenate_text`, `wrap_text`, `process_docx_file`).
- **FR-003**: `tests/golden/manifest.json` MUST be updated to mark `hyphen_syllable.jsonl` with `"status": "active"`.
- **FR-004**: `release-policy.toml` MUST be updated to include `"tamil-hyphen"` in `public_crates` in proper topological order.
- **FR-005**: `tools/release_policy.py` MUST be updated to remove private crate exemptions for `tamil-hyphen`, and `just check-release-policy` MUST pass with zero errors.
- **FR-006**: Playground and Word Add-in integrations MUST remain synchronized with the shared Rust/WASM engine contracts.
- **FR-007**: `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` MUST be expanded to provide CLI subcommands for:
  - `core` (`letters`, `inspect`, `split-uyirmei`, `compose-uyirmei`)
  - `norm` (`nfc`, `nfd`, `repair`, `fold`)
  - `codec` (`convert`, `detect`)
  - `collate` (`compare`, `key`, `sort`)
  - `numerals` (`to-words`, `to-numeral`, `parse`)
  - `calendar` (`info`)
  - `hyphen` (`word`, `text`, `wrap`, `export-dic`, `package-oxt`, `process-docx`)

### Key Entities

- **`HyphenationConfig`**: Configuration struct specifying delimiter string, `left_min`, and `right_min`.
- **`HyphenationPoint`**: Struct specifying breakpoint location with `byte_offset`, `scalar_offset`, and `letter_index`.
- **`HyphenationResult`**: Structured outcome with `original`, `hyphenated`, `segments`, and `points`.
- **`WrapResult`**: Paragraph wrapping outcome with wrapped text and individual lines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All active golden vectors in `hyphen_syllable.jsonl` pass across Rust (`golden_suite.rs`), Python, and WASM with 100% parity.
- **SC-002**: `just check-release-policy` passes with zero exemptions for `tamil-hyphen`.
- **SC-003**: Office Word Add-in contract tests pass with 100% success.
- **SC-004**: All 7 CLI command suites (`core`, `norm`, `codec`, `collate`, `numerals`, `calendar`, `hyphen`) run successfully with expected outputs and help docs.
- **SC-005**: Complete repository quality gate `just agent-pre-stop-gate` passes with zero errors and zero warnings.

## Assumptions

- Rust stable toolchain 1.95+ is available in the development environment.
- Node.js and npm are installed and available for integration tests.
- `tamil-core` Phase 1 primitives are fully implemented and verified.
