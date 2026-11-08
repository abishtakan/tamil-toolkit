# Tasks: Tamil Normalization, Repair & Search-Folding Contracts (`018`)

**Input**: Design documents from `specs/018-tamil-norm-contracts/`  
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required), [research.md](research.md), [data-model.md](data-model.md), [contracts/norm-contract.md](contracts/norm-contract.md), [quickstart.md](quickstart.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Exact file paths are included in every task description.

---

## Phase 1: Setup (Shared Infrastructure & Test Baselines)

**Purpose**: Establish test vectors and manifest baseline before implementing norm modules.

- [X] T001 Inspect existing `crates/tamil-norm/Cargo.toml` and verify `tamil-core` Rank 0 dependency
- [X] T002 [P] Create initial golden test datasets in `tests/golden/norm_repair.jsonl` and `tests/golden/norm_folding.jsonl` and register them as `"active"` in `tests/golden/manifest.json`

---

## Phase 2: Foundational (Norm & Repair Types)

**Purpose**: Core types, enums, and configuration options required by all user stories.

**⚠️ CRITICAL**: Must complete before User Story phases.

- [X] T003 Define `RepairOptions`, `RepairDiagnostics`, `RepairResult`, and `FoldingProfile` enums/structs with `Serialize` and `Deserialize` derives in `crates/tamil-norm/src/types.rs`
- [X] T004 [P] Re-export `RepairOptions`, `RepairDiagnostics`, `RepairResult`, and `FoldingProfile` in `crates/tamil-norm/src/lib.rs`

**Checkpoint**: Foundational types ready.

---

## Phase 3: User Story 1 - Canonical Unicode Normalization (Priority: P1) 🎯 MVP

**Goal**: Expose standard Unicode 17.0.0 canonical NFC and NFD normalization while strictly preserving format controls (`ZWJ`, `ZWNJ`), whitespace, and non-Tamil text.

**Independent Test**: Execute `cargo test -p tamil-norm --test norm_tests` to verify that precomposed and decomposed Tamil strings normalize canonically without altering joiners.

### Tests for User Story 1

- [X] T005 [P] [US1] Author unit tests for canonical NFC/NFD normalization, decomposed vowel combinations (`U+0BCA`, `U+0BCB`, `U+0BCC`), and joiner preservation in `crates/tamil-norm/tests/norm_tests.rs`
- [X] T006 [P] [US1] Add test cases for canonical NFC/NFD equivalence and format control preservation in `tests/golden/norm_repair.jsonl`

### Implementation for User Story 1

- [X] T007 [US1] Implement re-exports and validation wrappers for `normalize_nfc` and `normalize_nfd` in `crates/tamil-norm/src/lib.rs` guaranteeing `#![forbid(unsafe_code)]` and zero joiner loss

**Checkpoint**: User Story 1 complete and independently testable.

---

## Phase 4: User Story 2 - Opt-in Orthographic Text Repair (Priority: P2)

**Goal**: Repair duplicate viramas, inverted visual left-kombus, and stray soft-hyphens/controls while tracking diagnostic counts.

**Independent Test**: Execute `cargo test -p tamil-norm --test repair_tests` to verify that corruptions are healed and diagnostic counts match expectations.

### Tests for User Story 2

- [X] T008 [P] [US2] Author unit tests for `repair_tamil_text` in `crates/tamil-norm/tests/repair_tests.rs` covering duplicate pullis, visual left kombus (`ெ`, `ே`, `ை`), soft-hyphen stripping, and opt-in joiner stripping
- [X] T009 [P] [US2] Add test vectors for orthographic repair and diagnostic telemetry in `tests/golden/norm_repair.jsonl`

### Implementation for User Story 2

- [X] T010 [US2] Implement duplicate pulli collapsing (`U+0BCD` contiguous sequences) and control/soft-hyphen stripping in `crates/tamil-norm/src/repair.rs`
- [X] T011 [US2] Implement visual left-kombu reordering (mapping misplaced `ெ`, `ே`, `ை` before consonants into proper consonant-vowel combinations and two-part vowels) in `crates/tamil-norm/src/repair.rs`
- [X] T012 [P] [US2] Assemble `repair_tamil_text(text: &str, options: &RepairOptions) -> RepairResult` in `crates/tamil-norm/src/repair.rs` and re-export it in `crates/tamil-norm/src/lib.rs`

**Checkpoint**: User Stories 1 and 2 complete and independently testable.

---

## Phase 5: User Story 3 - Versioned Lossy Search Folding (Priority: P2)

**Goal**: Provide deterministic lossy search folding for Mayangoli confusion sets (`ல/ள/ழ`, `ன/ண`, `ர/ற`) and Grantha consonants (`ஸ/ஷ/ச`, `ஜ/ச`, `ஹ/க`, `க்ஷ/ச`), preserving attached vowel signs.

**Independent Test**: Execute `cargo test -p tamil-norm --test folding_tests` to verify that homophone/confusion pairs produce identical folded strings.

### Tests for User Story 3

- [X] T013 [P] [US3] Author unit tests for `fold_for_search` in `crates/tamil-norm/tests/folding_tests.rs` covering Mayangoli sets, Grantha folding, diacritic preservation, and Comprehensive folding
- [X] T014 [P] [US3] Add test vectors for search-folding profiles in `tests/golden/norm_folding.jsonl`

### Implementation for User Story 3

- [X] T015 [US3] Implement Mayangoli folding (`ல/ள/ழ` -> `ல`, `ன/ண` -> `ன`, `ர/ற` -> `ர`) preserving attached diacritics via `tamil_core::split_uyirmei` / `compose_uyirmei` in `crates/tamil-norm/src/folding.rs`
- [X] T016 [US3] Implement Grantha folding (`ஸ/ஷ` -> `ச`, `ஜ` -> `ச`, `ஹ` -> `க`, `க்ஷ` -> `ச`, `ஸ்ரீ` -> `சீ`) in `crates/tamil-norm/src/folding.rs`
- [X] T017 [P] [US3] Implement `fold_for_search(text: &str, profile: FoldingProfile) -> String` with Comprehensive support (combining Mayangoli + Grantha + ASCII lowercase) in `crates/tamil-norm/src/folding.rs` and re-export in `crates/tamil-norm/src/lib.rs`

**Checkpoint**: All three user stories complete and independently testable.

---

## Phase 6: Multi-Runtime Exposure & Dispatcher Integration

**Goal**: Expose normalization, repair, and folding in the `tamil-toolkit` unified facade and update Python and WASM bindings.

- [X] T018 Wire `norm.repair_text` and `norm.fold_for_search` dispatcher actions in `crates/tamil-toolkit/src/lib.rs`
- [X] T019 [P] Expose `repair_tamil_text`, `fold_for_search`, and their options/types in Python bindings `bindings/python/python/tamil_toolkit/__init__.py` and `__init__.pyi`
- [X] T020 [P] Expose `repairTamilText`, `foldForSearch`, and types in TypeScript/WASM bindings `bindings/js-wasm/src/api.ts`

---

## Phase 7: Polish & Cross-Cutting Verification

**Purpose**: Execute full repository gates, verify multi-runtime parity, and update documentation.

- [X] T021 Run `cargo test -p tamil-norm` and `cargo test -p tamil-toolkit` to verify all Rust tests pass
- [X] T022 Run `uv run --locked pytest bindings/python/tests/test_golden.py` and `pnpm --filter tamil-toolkit test` to verify tri-runtime parity
- [X] T023 [P] Run `just agent-post-edit` and `just agent-pre-stop-gate` to confirm zero formatting drift, clippy cleanliness, and schema conformance
- [X] T024 [P] Update `docs/status.md` and `docs/specs/architecture-roadmap.md` recording Phase 2 closeout progress
