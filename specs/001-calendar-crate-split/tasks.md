# Tasks: Calendar Crate Split

**Feature**: `specs/001-calendar-crate-split`

## Phase 1: Setup (Shared Infrastructure & Workspace Registration)

**Purpose**: Register `tamil-calendar` in the root workspace and scaffold directory layout.

- [X] T001 Create `crates/tamil-calendar/src` directory structure per implementation plan
- [X] T002 Configure workspace membership and dependency declaration for `tamil-calendar` in `Cargo.toml`
- [X] T003 Create `crates/tamil-calendar/Cargo.toml` with `tamil-core`, `tamil-numerals`, and `astro = "=2.0.0"` dependencies

---

## Phase 2: Foundational (Module Migration to `tamil-calendar`)

**Purpose**: Move calendar algorithms and domain modules into `crates/tamil-calendar` and establish `lib.rs`.

**⚠️ CRITICAL**: Foundational tasks must complete before user story verification and dispatcher updates.

- [X] T004 Move `crates/tamil-numerals/src/calendar/display.rs` to `crates/tamil-calendar/src/display.rs`
- [X] T005 Move `crates/tamil-numerals/src/calendar/drik.rs` to `crates/tamil-calendar/src/drik.rs`
- [X] T006 Move `crates/tamil-numerals/src/calendar/holidays.rs` to `crates/tamil-calendar/src/holidays.rs`
- [X] T007 Move `crates/tamil-numerals/src/calendar/observances.rs` to `crates/tamil-calendar/src/observances.rs`
- [X] T008 Move `crates/tamil-numerals/src/calendar/solar_arithmetic.rs` to `crates/tamil-calendar/src/solar_arithmetic.rs`
- [X] T009 Move `crates/tamil-numerals/src/calendar/vakya.rs` to `crates/tamil-calendar/src/vakya.rs`
- [X] T010 Move `crates/tamil-numerals/src/calendar/vakya_civil.rs` to `crates/tamil-calendar/src/vakya_civil.rs`
- [X] T011 Create `crates/tamil-calendar/src/lib.rs` re-exporting all calendar types and functions per contracts
- [X] T012 Create `crates/tamil-calendar/README.md` documenting calendar scope, Vakiya/Thirukanitham models, and experimental status
- [X] T013 Verify standalone compilation of `tamil-calendar` with `cargo check -p tamil-calendar`

**Checkpoint**: Foundation ready — `tamil-calendar` compiles independently as a standalone crate.

---

## Phase 3: User Story 1 - Dedicated Calendar Engine Discovery & Consumption (Priority: P1) 🎯 MVP

**Goal**: Establish `tamil-calendar` as an independently testable engine with its test suites cleanly reassigned.

**Independent Test**: Verify `cargo test -p tamil-calendar --locked` passes and `tests/golden/manifest.json` attributes all 17 calendar suites to `tamil-calendar`.

- [X] T014 [US1] Reassign all 17 planned calendar suites to `tamil-calendar` in `tests/golden/manifest.json`
- [X] T015 [P] [US1] Add unit tests for Thirukanitham date conversion in `crates/tamil-calendar/tests/thirukanitham_tests.rs`
- [X] T016 [P] [US1] Add unit tests for Vakiya transit calculations in `crates/tamil-calendar/tests/vakya_tests.rs`
- [X] T017 [US1] Run `cargo test -p tamil-calendar` to verify standalone calendar functionality

**Checkpoint**: User Story 1 complete — `tamil-calendar` is fully functional and independently verified.

---

## Phase 4: User Story 2 - Lightweight Numerals Package Focused on Numbers & Currency (Priority: P2)

**Goal**: Purge all calendar modules, types, and `astro` dependency from `crates/tamil-numerals` without deprecations.

**Independent Test**: Verify `crates/tamil-numerals/src/calendar` is completely removed, `astro` is removed from `crates/tamil-numerals/Cargo.toml`, and `cargo test -p tamil-numerals` passes all 35,646 active golden vectors.

- [X] T018 [US2] Remove `astro = "=2.0.0"` from `crates/tamil-numerals/Cargo.toml`
- [X] T019 [US2] Remove `calendar` module declaration and re-exports from `crates/tamil-numerals/src/lib.rs`
- [X] T020 [US2] Remove remaining directory `crates/tamil-numerals/src/calendar/`
- [X] T021 [US2] Run `cargo test -p tamil-numerals` to verify 100% pass on all 35,646 active numeral vectors with zero calendar dependencies

**Checkpoint**: User Story 2 complete — `tamil-numerals` is clean, lightweight, and focused purely on numbers and currency.

---

## Phase 5: User Story 3 - Unified Multi-Runtime Access via Umbrella Toolkit (Priority: P3)

**Goal**: Expose `tamil-calendar` through `crates/tamil-toolkit` and language bindings under dedicated sub-namespaces.

**Independent Test**: Verify `just sync-bindings`, `just test-parity`, and workbench check pass with calendar operations routed through `tamil-calendar`.

- [X] T022 [US3] Add `tamil-calendar.workspace = true` to `crates/tamil-toolkit/Cargo.toml`
- [X] T023 [US3] Update `crates/tamil-toolkit/src/lib.rs` to re-export `pub use tamil_calendar as calendar;`
- [X] T024 [US3] Update `crates/tamil-toolkit/src/calendar_features.rs` to import calendar types from `tamil_calendar` instead of `numerals`
- [X] T025 [P] [US3] Update Python binding `bindings/python/Cargo.toml` and expose `tamil_toolkit.calendar` sub-namespace in `bindings/python/src/lib.rs`
- [X] T026 [P] [US3] Update WebAssembly binding `bindings/js-wasm/Cargo.toml` and export `api.calendar` in `bindings/js-wasm/src/api.ts`
- [X] T027 [P] [US3] Update Dart FFI wrapper in `bindings/dart-flutter` to route calendar operations via `TamilCalendar`
- [X] T028 [US3] Update `workbench/main.ts` and `workbench/index.html` to add `tamil-calendar` package card and map its operations

**Checkpoint**: User Story 3 complete — Unified multi-runtime access and workbench support operational.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Verification against project constitution, release policies, and developer documentation.

- [X] T029 Verify `release-policy.toml` cleanly excludes `tamil-calendar` and passes `just check-release-policy`
- [X] T030 [P] Update `docs/specs/bootstrap.md` and `docs/status.md` with the new `tamil-calendar` crate boundary
- [X] T031 [P] Update `CHANGELOG.md` under `## Unreleased` recording the extraction of `tamil-calendar` from `tamil-numerals`
- [X] T032 Run `just sync-release-files` and `just check-release-files` to verify distribution data integrity
- [X] T033 Run `just agent-pre-stop-gate` to verify clippy, Unicode checks, and parity gates across all crates
- [X] T034 Run `pnpm run check:workbench` and `pnpm run build:workbench` to verify workbench builds cleanly

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Can start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; moves files and scaffolds `tamil-calendar`.
- **Phase 3 (User Story 1)**: Depends on Phase 2; verifies `tamil-calendar` independently.
- **Phase 4 (User Story 2)**: Depends on Phase 2; purges calendar code from `tamil-numerals`.
- **Phase 5 (User Story 3)**: Depends on Phase 3 and Phase 4; binds both crates into the top-level facade, multi-runtime wrappers, and workbench.
- **Phase 6 (Polish)**: Depends on Phase 5; runs full workspace quality gates.

### Parallel Opportunities
- In Phase 3: T015 and T016 can be written in parallel.
- In Phase 5: Language binding tasks T025 (Python), T026 (WASM), and T027 (Dart) can be implemented in parallel.
- In Phase 6: Documentation tasks T030 and T031 can be updated in parallel.
