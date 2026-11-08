# Tasks: tamil-hyphen Release Policy, Manifest & WASM Consolidation

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and environment validation

- [x] T001 Verify Rust and Node.js environment dependencies for workspace compilation
- [x] T002 [P] Verify git working directory status and branch alignment in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core prerequisites that must be confirmed before user stories begin

- [x] T003 [P] Verify `tamil-core` Phase 1 phonological primitives in `crates/tamil-core/src/lib.rs`

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Refactor tamil-hyphen with tamil-core Phonological Primitives (Priority: P1) 🎯 MVP

**Goal**: Refactor `tamil-hyphen` letter classification and syllable nucleus breakdown to consume `tamil-core` primitives directly while strictly maintaining typographic minimum-margin merging rules.

**Independent Test**: `cargo test -p tamil-hyphen` passes with 0 failures and 0 regressions.

### Implementation for User Story 1

- [x] T004 [US1] Update `classify_letter` in `crates/tamil-hyphen/src/syllable.rs` to consume `tamil_core` phonological classifiers (`is_aytham`, `is_mei`, `is_kuril`, `is_nedil`, `classify_quantity`, `split_uyirmei`)
- [x] T005 [US1] Refactor syllable breakdown and nucleus identification in `crates/tamil-hyphen/src/syllable.rs` to use `tamil_core` primitives while preserving typographic margin segmentation
- [x] T006 [US1] Run unit tests and property tests via `cargo test -p tamil-hyphen`

**Checkpoint**: User Story 1 complete and independently verified.

---

## Phase 4: User Story 2 - Manifest Activation & Release Policy Promotion (Priority: P1)

**Goal**: Activate `hyphen_syllable.jsonl` in `tests/golden/manifest.json`, promote `tamil-hyphen` to `public_crates` in `release-policy.toml`, and eliminate private crate exemptions in `tools/release_policy.py`.

**Independent Test**: `just check-release-policy` and `cargo test --test golden_suite` pass with 0 errors.

### Implementation for User Story 2

- [x] T007 [US2] Update `tests/golden/manifest.json` to change `hyphen_syllable.jsonl` status from `planned` to `active`
- [x] T008 [US2] Update `release-policy.toml` to add `tamil-hyphen` to `public_crates` in topological order before `tamil-toolkit`
- [x] T009 [US2] Remove temporary `tamil-hyphen` private exemptions from `tools/release_policy.py`
- [x] T010 [US2] Verify release policy conformance via `python tools/release_policy.py`
- [x] T011 [US2] Run golden suite across active vectors via `cargo test --test golden_suite`

**Checkpoint**: User Story 2 complete and verified.

---

## Phase 5: User Story 3 - Consolidation of Playground & Word Add-in onto Shared Rust/WASM Engine (Priority: P2)

**Goal**: Verify and maintain consolidation of Word Add-in and Playground onto the shared Rust/WASM engine contracts.

**Independent Test**: `node --test tests/integrations/test_word_addin_contract.js` and playground Vitest suite pass with 100% success.

### Implementation for User Story 3

- [x] T012 [P] [US3] Verify Word Add-in contract test parity in `tests/integrations/test_word_addin_contract.js`
- [x] T013 [P] [US3] Verify Playground hyphenation integration and Vitest suite in `playground/`

**Checkpoint**: User Story 3 complete and verified.

---

## Phase 6: User Story 4 - CLI Subcommands Expansion for Existing Crates (Priority: P2)

**Goal**: Expand `tamil-toolkit` CLI binary to support subcommands for `core`, `norm`, `codec`, `collate`, `numerals`, `calendar`, and `hyphen`.

**Independent Test**: `cargo run -p tamil-toolkit --bin tamil-toolkit -- <subcommand>` outputs valid results for each crate.

### Implementation for User Story 4

- [x] T014 [US4] Implement `core` subcommands (`letters`, `inspect`, `split-uyirmei`, `compose-uyirmei`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T015 [US4] Implement `norm` subcommands (`nfc`, `nfd`, `repair`, `fold`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T016 [US4] Implement `codec` subcommands (`convert`, `detect`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T017 [US4] Implement `collate` subcommands (`compare`, `key`, `sort`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T018 [US4] Implement `numerals` subcommands (`to-words`, `to-numeral`, `parse`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T019 [US4] Implement `calendar` subcommands (`info`) in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T020 [US4] Implement `hyphen` subcommands (`word`, `text`, `wrap`) alongside existing `export-dic`, `package-oxt`, `process-docx` in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [x] T021 [US4] Test CLI subcommands end-to-end via `cargo run -p tamil-toolkit --bin tamil-toolkit`

**Checkpoint**: User Story 4 complete and verified.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Multi-runtime parity, formatting, and final quality gates

- [x] T022 [P] Rebuild and synchronize WebAssembly and Python bindings via `python tools/sync_bindings.py`
- [x] T023 [P] Verify Unicode scalar integrity across source tree via `python tools/mcp-tamil-oracle/check_source_unicode.py`
- [x] T024 Run complete repository gate via `just agent-pre-stop-gate`

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** -> **Phase 2 (Foundational)** -> **Phase 3 (User Story 1)** -> **Phase 4 (User Story 2)** -> **Phase 5 (User Story 3)** -> **Phase 6 (User Story 4)** -> **Phase 7 (Polish)**
