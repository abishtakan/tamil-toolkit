# Tasks: Tamil Core Phonological & Nucleus Primitives (`017`)

**Input**: Design documents from `specs/017-tamil-core-primitives/`  
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required), [research.md](research.md), [data-model.md](data-model.md), [contracts/core-primitives-contract.md](contracts/core-primitives-contract.md), [quickstart.md](quickstart.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Exact file paths are included in every task description.

---

## Phase 1: Setup (Shared Infrastructure & Test Baseline)

**Purpose**: Establish test vectors and manifest baseline before implementing phonology modules.

- [X] T001 Inspect existing tailored letter iteration and table definitions in `crates/tamil-core/src/lib.rs` and `crates/tamil-core/build.rs` to establish module layout
- [X] T002 [P] Create the initial golden test dataset in `tests/golden/core_phonology.jsonl` and register it as `"active"` in `tests/golden/manifest.json`

---

## Phase 2: Foundational (Phonological Types & Mora Primitives)

**Purpose**: Core types and enums required by all user stories.

**⚠️ CRITICAL**: Must complete before User Story phases.

- [X] T003 Define `LetterQuantity` enum (`Kuril`, `Nedil`, `Mei`, `Aytham`, `Other`) and `Maathirai` struct (`KURIL = 1.0`, `NEDIL = 2.0`, `MEI = 0.5`, `AYTHAM = 0.5`, `ZERO = 0.0`) with `as_fraction()` in `crates/tamil-core/src/phonology.rs`
- [X] T004 [P] Re-export `LetterQuantity` and `Maathirai` in `crates/tamil-core/src/lib.rs` with `Serialize` and `Deserialize` derives

**Checkpoint**: Foundational types ready.

---

## Phase 3: User Story 1 - Tamil Letter Quantity & Duration Classification (Priority: P1) 🎯 MVP

**Goal**: Classify any Tamil letter into its primary phonological quantity (*Kuril*, *Nedil*, *Mei*, *Aytham*) and baseline duration (*Maathirai*).

**Independent Test**: Execute `cargo test -p tamil-core --test phonology_tests` to verify that all 247 primary Tamil letters, Grantha pure consonants, and atomic ligatures return exact quantity categories and mora values.

### Tests for User Story 1

- [X] T005 [P] [US1] Author unit tests for letter quantity classification (`is_kuril`, `is_nedil`, `is_mei`, `is_otru`, `is_aytham`, `baseline_maathirai`) and Grantha ligatures in `crates/tamil-core/tests/phonology_tests.rs`
- [X] T006 [P] [US1] Add test cases for all vowel and consonant quantity categories in `tests/golden/core_phonology.jsonl`

### Implementation for User Story 1

- [X] T007 [US1] Implement `classify_quantity(letter: &str) -> LetterQuantity` and `baseline_maathirai(letter: &str) -> Maathirai` in `crates/tamil-core/src/phonology.rs` handling standard vowels, Uyirmei composites, Grantha consonants, and atomic ligatures (`க்ஷ` as Kuril, `ஸ்ரீ` as Nedil)
- [X] T008 [P] [US1] Implement boolean query predicates `is_kuril`, `is_nedil`, `is_mei`, `is_otru`, and `is_aytham` in `crates/tamil-core/src/phonology.rs` and re-export them in `crates/tamil-core/src/lib.rs`

**Checkpoint**: User Story 1 complete and independently testable.

---

## Phase 4: User Story 2 - Homorganic Cognate Letter Mapping (*Ina Ezhuthu*) (Priority: P2)

**Goal**: Query homorganic stop-nasal cognates (*Vallinam* $\leftrightarrow$ *Mellinam*) and short-long vowel pairs per *Tolkappiyam* and *Nannool*, supporting composite *Uyirmei* letters.

**Independent Test**: Execute `cargo test -p tamil-core --test phonology_tests cognate` to verify bidirectional mapping across all 6 consonant pairs, 7 vowel pairs, and composite Uyirmei letters.

### Tests for User Story 2

- [X] T009 [P] [US2] Author unit tests for `get_cognate` and `are_cognates` in `crates/tamil-core/tests/phonology_tests.rs` covering consonants (`க்` ↔ `ங்`), composite Uyirmei (`கா` ↔ `ஙா`), vowels (`அ` ↔ `ஆ`, `ஐ` ↔ `இ`, `ஔ` ↔ `உ`), and non-cognates
- [X] T010 [P] [US2] Add test cases for cognate pairs, composite Uyirmei mapping, and negative non-cognate assertions in `tests/golden/core_phonology.jsonl`

### Implementation for User Story 2

- [X] T011 [US2] Implement static bidirectional cognate mapping tables (`VALLINAM_MELLINAM_PAIRS`, `VOWEL_COGNATE_PAIRS`) and `get_cognate(letter: &str) -> Option<String>` in `crates/tamil-core/src/phonology.rs` with Uyirmei diacritic preservation
- [X] T012 [P] [US2] Implement `are_cognates(letter1: &str, letter2: &str) -> bool` in `crates/tamil-core/src/phonology.rs` and re-export both functions in `crates/tamil-core/src/lib.rs`

**Checkpoint**: User Stories 1 and 2 complete and independently testable.

---

## Phase 5: User Story 3 - Orthographic Syllable Nucleus Segmentation (*Olippasai*) (Priority: P2)

**Goal**: Zero-allocation syllable nucleus iteration grouping vowel nuclei with onset clusters (including loanword initial clusters) and trailing coda consonants/Aytham markers with byte and letter span offsets.

**Independent Test**: Execute `cargo test -p tamil-core --test olippasai_tests` to verify that words are segmented into syllable nuclei with exact byte offsets matching the original input.

### Tests for User Story 3

- [X] T013 [P] [US3] Author unit tests for `OlippasaiIter` and `get_olippasai` in `crates/tamil-core/tests/olippasai_tests.rs` covering open syllables, coda clusters, Aytham, atomic Grantha sequences (`ஸ்ரீலங்கா`), and loanwords with initial consonant clusters (`ஸ்டார்`, `ப்ரியா`)
- [X] T014 [P] [US3] Add test cases for syllable nucleus segmentation and span reconstitution in `tests/golden/core_phonology.jsonl`

### Implementation for User Story 3

- [X] T015 [US3] Implement `Olippasai<'a>` struct and `OlippasaiIter<'a>` zero-allocation iterator in `crates/tamil-core/src/olippasai.rs` using tailored `Letters`, attaching leading consonants to following nuclei, and grouping codas without allocating heap strings
- [X] T016 [P] [US3] Expose `Olippasai`, `OlippasaiIter`, and `get_olippasai(text: &str)` in `crates/tamil-core/src/lib.rs`

**Checkpoint**: All three core user stories complete and independently testable.

---

## Phase 6: Multi-Runtime Exposure & Dispatcher Integration

**Goal**: Expose core phonological and syllable primitives in the `tamil-toolkit` unified facade and update multi-runtime bindings.

- [X] T017 Wire `core.classify_letter`, `core.get_cognate`, and `core.segment_olippasai` actions into `crates/tamil-toolkit/src/dispatcher.rs`
- [X] T018 [P] Expose phonological predicates, cognate lookup, and syllable segmentation in Python bindings `bindings/python/src/lib.rs` and WASM bindings `bindings/js-wasm/src/lib.rs`
- [X] T019 [P] Add tri-runtime golden parity test cases in `tests/harness/test_golden_parity.py` and `bindings/python/tests/test_golden.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify all quality gates, Unicode conformance, and release readiness.

- [X] T020 Run `cargo test -p tamil-core` and `cargo test -p tamil-toolkit` to verify all Rust unit and integration tests pass
- [X] T021 Run `uv run --locked pytest tests/harness/test_golden_parity.py` and verify multi-runtime parity across Rust, Python, and WASM
- [X] T022 [P] Run `just agent-post-edit` and `just agent-pre-stop-gate` to confirm zero formatting drift, clippy cleanliness, and schema conformance
- [X] T023 [P] Update `docs/status.md` and `docs/specs/architecture-roadmap.md` recording Phase 1 closeout progress

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion — blocks User Stories.
- **Phase 3 (User Story 1 - P1 MVP)**: Depends on Phase 2 completion.
- **Phase 4 (User Story 2 - P2)**: Depends on Phase 2 completion; can run in parallel with Phase 3.
- **Phase 5 (User Story 3 - P2)**: Depends on Phase 2 completion; can run in parallel with Phase 3 and Phase 4.
- **Phase 6 (Multi-Runtime Exposure)**: Depends on Phases 3, 4, and 5 completing.
- **Phase 7 (Polish)**: Depends on all user stories and multi-runtime exposure completing.

### User Story Dependencies

- **User Story 1 (P1)**: Independent of US2 and US3.
- **User Story 2 (P2)**: Independent of US1 and US3.
- **User Story 3 (P2)**: Independent of US1 and US2 (uses foundational `Letters` and `LetterQuantity`).

### Parallel Opportunities

- `T001` and `T002` can run in parallel across crate structure and test vectors.
- `T005` (unit tests) and `T006` (golden vectors) can run in parallel before `T007` implementation.
- `T009` (unit tests) and `T010` (golden vectors) can run in parallel before `T011` implementation.
- `T013` (unit tests) and `T014` (golden vectors) can run in parallel before `T015` implementation.
- `T017` (`dispatcher.rs`), `T018` (`bindings/*`), and `T019` (`test_golden_parity.py`) can run in parallel across separate files.
- `T022` (formatting/gates) and `T023` (documentation updates) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete Phase 1 & Phase 2 (`T001`–`T004`).
2. Complete Phase 3 (`T005`–`T008`): Letter quantity classification & mora duration.
3. Validate independently via `cargo test -p tamil-core --test phonology_tests`.

### Incremental Delivery
1. Add User Story 2 (`T009`–`T012`): Homorganic cognate mapping (*Ina Ezhuthu*).
2. Add User Story 3 (`T013`–`T016`): Syllable nucleus segmentation (*Olippasai*).
3. Add Multi-Runtime Exposure (`T017`–`T019`): Dispatcher and FFI bindings.
4. Run Phase 7 validation (`T020`–`T023`): Pre-stop gate and parity checks.
