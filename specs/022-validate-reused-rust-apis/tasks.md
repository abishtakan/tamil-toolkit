# Tasks: Validate Reused Rust APIs & NFC/NFD Normalization (`tamil-core`, `tamil-norm`, `tamil-toolkit`)

**Input**: Design documents from `/specs/022-validate-reused-rust-apis/`  
**Prerequisites**: [plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/plan.md), [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/spec.md), [research.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/research.md), [data-model.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/data-model.md), [contracts/](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/contracts/)

**Tests**: Required by specification (`SC-001`–`SC-004`) and Project Constitution Principle III (Golden Vectors Precede Implementation).

**Organization**: Organized by user story (`US1`, `US2`, `US3`) with golden vector setup first and cross-runtime parity gates last.

## Phase 1: Setup & Environment Readiness

**Purpose**: Confirm baseline release policy, Unicode tooling, and property-testing dependencies.

- [X] T001 Verify baseline policy and Unicode validator execution cleanly using `.venv\Scripts\python.exe tools\tasks.py check-release-policy` and `.venv\Scripts\python.exe tools\tasks.py check-unicode`
- [X] T002 Inspect and ensure `proptest` dev-dependency is declared for property-based NFC/NFD tests in `crates/tamil-norm/Cargo.toml`

---

## Phase 2: Foundational Golden Vectors (Golden-First Gate)

**Purpose**: Author escaped golden vectors and register them in the manifest before any Rust code changes.

**⚠️ CRITICAL**: Golden vectors must pass `check-unicode` schema and escaping checks before implementation edits begin.

- [X] T003 Create canonical normalization golden vector suite in `tests/golden/norm_canonical.jsonl` covering two-part vowel signs (`\u0bca`, `\u0bcb`, `\u0bcc`, `\u0b94`), CCC mark reordering (`\u0bcd` + `\u0301`), format-control barriers (`\u200c`, `\u200d`, `\ufeff`, `\u00ad`), Shri variants (`\u0bb8\u0bcd\u0bb0\u0bc0` vs `\u0bb6\u0bcd\u0bb0\u0bc0`), malformed double vowels (`\u0ba4\u0bc1\u0bbe`), mixed scripts, `fold_for_search` NFD equivalence, and `repair_tamil_text` NFD equivalence with explicit `unicode_exceptions`
- [X] T004 Register `norm_canonical` as an active suite in `tests/golden/manifest.json` and run `.venv\Scripts\python.exe tools\tasks.py check-unicode` to verify global IDs, schema, and escape rules

**Checkpoint**: Canonical golden vectors exist and pass `check-unicode` across all declared fields.

---

## Phase 3: User Story 1 - Canonical NFC & NFD Normalization Correctness in `tamil-norm` (Priority: P1) 🎯 MVP

**Goal**: Prove `tamil_norm::normalize_nfc`, `tamil_norm::normalize_nfd`, `fold_for_search`, and `repair_tamil_text` behave strictly per Unicode 17.0.0 UAX #15 across NFC, NFD, format controls, CCC reordering, and downstream folding/repair.

**Independent Test**: `cargo test --locked -p tamil-norm` passes all unit tests, `PROPTEST_CASES=10000` property invariants, and full Tamil/Grantha NFD sweeps.

### Tests for User Story 1

- [X] T005 [P] [US1] Add deterministic NFC/NFD edge-case tests (split vowel signs, CCC mark reordering, `ZWJ`/`ZWNJ`/`BOM`/`SHY` barriers, Shri distinctions, malformed sequence non-repair, mixed-script, empty strings) in `crates/tamil-norm/tests/norm_tests.rs`
- [X] T006 [P] [US1] Add `proptest` NFC/NFD invariant suite (`10,000+` generated strings verifying NFC idempotence, NFD idempotence, cross-form round-trips, format-control preservation, and NFC-vs-NFD equality in `fold_for_search` / `repair_tamil_text`) in `crates/tamil-norm/tests/norm_tests.rs`
- [X] T007 [US1] Add 23-consonant (Tamil + Grantha + `\u{0b95}\u{0bcd}\u{0bb7}`) NFC-vs-NFD parity sweep tests in `crates/tamil-norm/tests/folding_tests.rs` and `crates/tamil-norm/tests/repair_tests.rs`, then execute `cargo test --locked -p tamil-norm` with `PROPTEST_CASES=10000`

**Checkpoint**: `tamil-norm` passes comprehensive NFC, NFD, and NFD-input folding/repair tests independently.

---

## Phase 4: User Story 2 - Validate Reused `tamil-core` Primitives & Diagnostics (Priority: P2)

**Goal**: Verify every Feature 021-reused `tamil-core` function has explicit, test-backed contract guarantees including boundary behaviors.

**Independent Test**: `cargo test --locked -p tamil-core` passes all primitive, segmentation, uyirmei, quantity/maathirai, cognate, olippasai, and inspection contract tests.

### Tests for User Story 2

- [X] T008 [P] [US2] Add Feature 021 reuse validation tests covering `get_letters` (NFC normalization) vs `Letters::new` (borrowed non-normalizing), `split_uyirmei`/`compose_uyirmei` round-trips, `classify_quantity` & `baseline_maathirai` single-letter vs multi-letter boundary (`Other` / `0.0`), `get_cognate`, `are_cognates`, and `get_olippasai` in `crates/tamil-core/tests/phonology_tests.rs`
- [X] T009 [P] [US2] Add `inspect_tamil_string` validation tests verifying `is_nfc`, `is_nfd`, `grapheme_count`, `ezhuthu_count`, `ZWJ`/`ZWNJ`/`BOM`/`SHY` preservation, and UAX #29 joiner cluster classification behavior in `crates/tamil-core/tests/phonology_tests.rs`, then execute `cargo test --locked -p tamil-core`

**Checkpoint**: All Feature 021-reused `tamil-core` primitives are contract-verified with passing tests.

---

## Phase 5: User Story 3 - Validate `tamil-toolkit` Dispatcher, CLI & Build Readiness (Priority: P3)

**Goal**: Eliminate `OPERATIONS` vs `execute()` drift, fix silent CLI `--profile` fallback in `norm fold`, and lock dispatcher error/parity contracts.

**Independent Test**: `cargo test --locked -p tamil-toolkit`, `cargo clippy --locked -p tamil-core -p tamil-norm -p tamil-toolkit --all-targets -- -D warnings`, and CLI invalid-profile check pass.

### Tests for User Story 3 (TDD First)

- [X] T010 [P] [US3] Add Rust integration tests asserting exact `OPERATIONS` completeness against `execute()`, JSON error contracts (invalid JSON, missing/unknown `op`, invalid `fold_for_search` profile), and CLI `norm fold --profile invalid` non-zero failure in `crates/tamil-toolkit/tests/golden_suite.rs`

### Implementation & Fixes for User Story 3

- [X] T011 [US3] Update `pub const OPERATIONS` in `crates/tamil-toolkit/src/lib.rs` to include all 9 implemented operations (`are_cognates`, `baseline_maathirai`, `calendar_display_info`, `classify_quantity`, `compare_calendar_profiles`, `format_tamil_date`, `get_cognate`, `get_olippasai`, `thiruvalluvar_year_info`) so `OPERATIONS` and `execute()` match 1:1
- [X] T012 [US3] Fix `norm fold --profile` flag parsing in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` to parse via `FoldingProfile::from_str`, reject unknown profiles with a non-zero exit code, and accept `--profile <value>` cleanly before or after `<TEXT>`
- [X] T013 [US3] Run focused Rust & clippy checks across all three crates (`cargo test --locked -p tamil-core -p tamil-norm -p tamil-toolkit` and `cargo clippy --locked -p tamil-core -p tamil-norm -p tamil-toolkit --all-targets -- -D warnings`)

**Checkpoint**: Dispatcher `OPERATIONS`, CLI `norm fold`, and all three crates pass tests and strict clippy checks.

---

## Phase 6: Polish, Bindings Sync & Multi-Runtime Verification

**Purpose**: Rebuild bindings, verify tri-runtime parity and Dart FFI sequentially, and update project handoff documentation.

- [X] T014 Run `.venv\Scripts\python.exe tools\tasks.py sync-bindings` and `.venv\Scripts\python.exe tools\tasks.py agent-pre-stop-gate` to rebuild PyO3/WASM bindings and verify all active golden vectors across Rust, Python, and WASM
- [X] T015 Run `.venv\Scripts\python.exe tools\tasks.py test-dart` sequentially after `agent-pre-stop-gate` completes to verify C ABI and Dart fixture parity (avoiding concurrent Windows DLL locks)
- [X] T016 [P] Update `CHANGELOG.md` (`[Unreleased]`) and `docs/status.md` documenting Feature 022 validation evidence, `OPERATIONS` completeness fix, CLI `--profile` fix, and readiness for Feature 021 (`021-lexicon-curation`) without modifying any Feature 021 spec/source files
- [X] T017 Run `.venv\Scripts\python.exe tools\tasks.py check-unicode` and verify quickstart checks in `specs/022-validate-reused-rust-apis/quickstart.md` after final documentation edits

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational Golden Vectors)**: Depends on Phase 1 (`T001`–`T002`); BLOCKS parity and multi-runtime validation.
- **Phase 3 (US1 - `tamil-norm`)**: Depends on Phase 2 (`T002`, `T003`, `T004`). `T005` and `T006` can be authored cleanly together before `T007`.
- **Phase 4 (US2 - `tamil-core`)**: Independent of Phase 3 (`crates/tamil-core/tests/phonology_tests.rs`); `T008` and `T009` touch the same file sequentially.
- **Phase 5 (US3 - `tamil-toolkit`)**: `T010` written first (TDD) before `T011` and `T012`; `T011` (`src/lib.rs`) and `T012` (`src/bin/tamil-toolkit.rs`) edit separate files before `T013`.
- **Phase 6 (Polish & Parity)**: Depends on Phases 3, 4, and 5; `T014` MUST finish before `T015` on Windows (`agent-pre-stop-gate` then `test-dart`).

### Parallel Opportunities

- US1 (`crates/tamil-norm/tests/`) and US2 (`crates/tamil-core/tests/`) can be developed in parallel after Phase 2.
- Inside US3, `T011` (`src/lib.rs`) and `T012` (`src/bin/tamil-toolkit.rs`) touch separate source files and can proceed concurrently after `T010`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & Phase 2 (`T001`–`T004`).
2. Complete Phase 3 (`T005`–`T007`) to establish 100% confidence in `tamil-norm` NFC/NFD normalization and NFD-input handling.

### Incremental Delivery

1. Deliver US1 (`tamil-norm` NFC/NFD + NFD-input verification).
2. Deliver US2 (`tamil-core` reused primitive contract tests).
3. Deliver US3 (`tamil-toolkit` `OPERATIONS` sync + CLI `--profile` fix).
4. Execute sequential Windows parity & Dart gates (`T014`–`T017`).
