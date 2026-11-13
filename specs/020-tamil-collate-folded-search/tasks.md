# Tasks: `tamil-collate` Folded Search & Uyirmei-First Profile

**Feature Branch**: `020-tamil-collate-folded-search`
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency configuration and build setup

- [X] T001 Update `crates/tamil-collate/Cargo.toml` to add `tamil-norm.workspace = true`
- [X] T002 Verify acyclic dependency graph with `just check-release-policy`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Declarative lexicon data and static table generation

- [X] T003 Create declarative lexicon `lexicon/collate_uyirmei_first.toml` with `uyirmei-first-v1` ordering (325 elements, where consonant syllables precede pure consonants)
- [X] T004 Update `crates/tamil-collate/build.rs` to validate and compile both `agara-v1` and `uyirmei-first-v1` tables into static arrays in `collation_tables.rs`

**Checkpoint**: Foundation ready - both collation profiles compiled into immutable static tables.

---

## Phase 3: User Story 1 - Error-Tolerant Search Indexing with Folded Keys (Priority: P1)

**Goal**: Provide `folded_search_key` normalizing Mayangoli and Grantha variations for fuzzy search indexing while preserving canonical Agara sort keys.

**Independent Test**: Generate folded search keys for pairs differing only in Mayangoli or Grantha letters and verify keys are identical.

- [X] T005 [P] [US1] Create golden test vectors for folded search in `tests/golden/collate_folded_search.jsonl`
- [X] T006 [US1] Define `CollationProfile` enum and re-export `FoldingProfile` in `crates/tamil-collate/src/lib.rs`
- [X] T007 [US1] Implement `folded_search_key(text: &str, profile: FoldingProfile) -> Vec<u32>` and `folded_search_key_with_profile` in `crates/tamil-collate/src/lib.rs`
- [X] T008 [US1] Add unit and property tests for `folded_search_key` in `crates/tamil-collate/src/lib.rs`

**Checkpoint**: User Story 1 functional and tested.

---

## Phase 4: User Story 2 - Pedagogical & Modern School Dictionary Sorting (Priority: P2)

**Goal**: Provide modern Uyirmei-first school dictionary collation profile where syllables precede muted consonants.

**Independent Test**: Sort words where simple syllables precede consonant clusters and verify ordering under `uyirmei-first-v1` climatic rules.

- [X] T009 [P] [US2] Create golden test vectors for Uyirmei-first collation in `tests/golden/collate_uyirmei_first.jsonl`
- [X] T010 [US2] Implement `sort_key_with_profile`, `compare_with_profile`, and `sort_words_with_profile` in `crates/tamil-collate/src/lib.rs`
- [X] T011 [US2] Add unit tests verifying `uyirmei-first-v1` ordering (e.g., `கப்பல்` sorts before `க்ளப்`) in `crates/tamil-collate/src/lib.rs`

**Checkpoint**: User Story 2 functional and tested.

---

## Phase 5: User Story 3 - Backward Compatibility for Existing Collation Indexes (Priority: P3)

**Goal**: Guarantee 100% backward compatibility of existing `sort_key`, `search_key`, `compare`, and `sort_words` functions under `agara-v1`.

**Independent Test**: Verify existing tests and active golden vectors produce identical keys.

- [X] T012 [US3] Verify all existing `sort_key`, `search_key`, `compare`, and `sort_words` tests pass without regression in `crates/tamil-collate/src/lib.rs`
- [X] T013 [US3] Verify `tests/golden/collate_agara_varisai.jsonl` passes with 100% match

**Checkpoint**: Backward compatibility verified.

---

## Phase 6: Multi-Runtime Exposure & CLI

**Purpose**: Expose new capabilities across facade dispatcher, CLI, Python, and WASM

- [X] T014 [P] Expose `folded_search_key` and `CollationProfile` in `crates/tamil-toolkit/src/dispatcher.rs` and facade `crates/tamil-toolkit/src/lib.rs`
- [X] T015 [P] Expose `folded_search_key` and profile parameters in `bindings/python`
- [X] T016 [P] Expose `folded_search_key` and profile parameters in `bindings/js-wasm`
- [X] T017 Update `tamil-toolkit` CLI binary in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` with `collate search-key` and `--profile` flags

---

## Phase 7: Polish & Governance Gates

**Purpose**: Documentation, manifest activation, and repository gates

- [X] T018 Register new golden suites in `tests/golden/manifest.json`
- [X] T019 Update documentation in `docs/specs/collate-v0.1.md` and `README.md`
- [X] T020 Run `just check-release-policy`, `just check-unicode`, `just test-rust`, `just test-parity`, and `just agent-pre-stop-gate`

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** $\rightarrow$ **Phase 2 (Foundational)** $\rightarrow$ **Phase 3 (US1)** $\rightarrow$ **Phase 4 (US2)** $\rightarrow$ **Phase 5 (US3)** $\rightarrow$ **Phase 6 (Multi-Runtime)** $\rightarrow$ **Phase 7 (Gates)**
