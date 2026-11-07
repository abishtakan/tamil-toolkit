# Tasks: Crate Dependency DAG, Capability Boundaries & Difficulty-Tiered Roadmap (`016`)

**Input**: Design documents from `specs/016-crate-dependency-roadmap/`  
**Prerequisites**: [plan.md](plan.md) (required), [spec.md](spec.md) (required), [research.md](research.md), [data-model.md](data-model.md), [contracts/dependency-dag-contract.md](contracts/dependency-dag-contract.md), [quickstart.md](quickstart.md)

**Scope Constraint**: Per the user request and `spec.md`, this feature is strictly an **architecture documentation, project-structure governance, and automated DAG policy task** (zero implementation changes to Rust crate source files `crates/*/src/*.rs`).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`, `[US4]`)
- Exact file paths are included in every task description.

---

## Phase 1: Setup (Shared Governance & Baseline Inspection)

**Purpose**: Verify current workspace manifests, `release-policy.toml`, and `tools/release_policy.py` baseline before adding DAG enforcement and canonical documentation.

- [X] T001 Inspect all workspace and extension `Cargo.toml` manifests (`crates/*/Cargo.toml`, `extensions/pg_tamil/Cargo.toml`, `bindings/python/Cargo.toml`, `bindings/js-wasm/Cargo.toml`, `bindings/dart-flutter/rust/Cargo.toml`) to confirm exact `package.name` values for the `CRATE_RANKS` table in `tools/release_policy.py`
- [X] T002 Create the canonical architecture specification skeleton in `docs/specs/architecture-roadmap.md` linking `specs/016-crate-dependency-roadmap/spec.md` and `ROADMAP.md`

---

## Phase 2: Foundational (Canonical Status Vocabulary & Rank Registry)

**Purpose**: Establish the 7-state `CapabilityStatus` vocabulary (`unscaffolded`, `planned`, `specified`, `implemented`, `active`, `release-approved`, `published`) and the `CRATE_RANKS` (`Rank 0` through `Rank 6`) constant map required by all user stories.

**CRITICAL**: Must complete before User Story phases.

- [X] T003 Define `CRATE_RANKS` (`Rank 0` through `Rank 6` covering all 12 workspace crates, `pg_tamil`, the 3 FFI binding packages, and the 4 future unscaffolded crates `tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`) and `UNSCAFFOLDED_PLANNED_CRATES` in `tools/release_policy.py`
- [X] T004 [P] Document the 7-state `CapabilityStatus` lifecycle vocabulary (`unscaffolded`, `planned`, `specified`, `implemented`, `active`, `release-approved`, `published`) and 6-step milestone acceptance gate (`FR-010`) in `docs/specs/architecture-roadmap.md`

**Checkpoint**: Foundational rank map and status vocabulary ready.

---

## Phase 3: User Story 1 - Enforce Acyclic Prerequisite Ordering Across All Workspace Crates (Priority: P1) 🎯 MVP

**Goal**: Enforce the `Rank 0`–`Rank 6` Directed Acyclic Graph (`Rank(dependency) < Rank(dependent)`) across `[dependencies]`, `[build-dependencies]`, and `[dev-dependencies]` in `tools/release_policy.py` (`just check-release-policy`) and document the exact boundary contracts (`tamil-core` vs. `tamil-yaappu` vs. `tamil-hyphen`, and `tamil-punarchi` vs. `tamil-morph`).

**Independent Test**: Run `uv run --locked pytest tests/harness/test_release_policy.py` and `uv run --locked python tools/release_policy.py check` to verify that every crate/extension manifest is checked against `CRATE_RANKS` and that any out-of-rank or circular dependency across `dependencies`, `build-dependencies`, or `dev-dependencies` fails the gate.

### Tests for User Story 1

- [X] T005 [P] [US1] Add unit tests in `tests/harness/test_release_policy.py` verifying that `release_policy.check()` rejects out-of-rank dependencies (`Rank(dep) >= Rank(source)`) in `[dependencies]`, `[build-dependencies]`, and `[dev-dependencies]` as well as unapproved empty scaffolds for `UNSCAFFOLDED_PLANNED_CRATES`

### Implementation for User Story 1

- [X] T006 [US1] Implement `check_dependency_dag(root)` in `tools/release_policy.py` and invoke it from `check(root)` to enforce `CRATE_RANKS[dep] < CRATE_RANKS[name]` across `dependencies`, `build-dependencies`, `dev-dependencies`, and target-specific dependency tables for all `crates/*/Cargo.toml`, `extensions/pg_tamil/Cargo.toml`, and `bindings/*/Cargo.toml` (`FR-001`, `FR-006`)
- [X] T007 [P] [US1] Author the normative `Rank 0`–`Rank 6` DAG section and boundary contracts (`FR-002` `tamil-core` vs. `tamil-yaappu` vs. `tamil-hyphen` and `FR-003` unidirectional `tamil-punarchi` $\rightarrow$ `tamil-morph` contract with `SandhiSplitCandidate` surface spans vs. reconstructed stems) in `docs/specs/architecture-roadmap.md`

**Checkpoint**: User Story 1 complete — `Rank 0`–`Rank 6` DAG is both normatively specified and automatically enforced by `just check-release-policy`.

---

## Phase 4: User Story 2 - Close Foundational Gaps in Existing Crates Before Upstream Expansion (Priority: P1)

**Goal**: Document the exact Phase 1–7 closeout specifications and prerequisite gates for all gaps discovered inside existing crates (`tamil-core`, `tamil-norm`, `tamil-hyphen`, `tamil-calendar`, `tamil-collate`, `tamil-numerals`, `tamil-codec`, `tamil-toolkit`).

**Independent Test**: Inspect `docs/specs/architecture-roadmap.md` and `ROADMAP.md` to confirm that every existing crate gap (`tamil-core` quantity/cognate/nucleus primitives, `tamil-norm` 3-contract split, `tamil-hyphen` release-policy/manifest/WASM closeout, `tamil-calendar` 13 planned suites, `tamil-collate` `folded_search_key`, `tamil-numerals` ITN/mixed-fractions/currencies, `tamil-codec` legacy fonts + `braille`, and `tamil-toolkit` CLI subcommands) has an explicit phase, prerequisite list, and exit gate.

### Implementation for User Story 2

- [X] T008 [US2] Author the "Foundational Closeout Specifications for Existing Crates (Phases 1–7)" section in `docs/specs/architecture-roadmap.md` covering `tamil-core` (`LetterQuantity`, `InaEzhuthuPair`, `OrthographicNucleus`), `tamil-norm` (`FR-004` 3-contract separation), `tamil-hyphen` (`FR-009` release-policy/manifest closeout & WASM consolidation), `tamil-calendar`, `tamil-collate` (`FR-005`), `tamil-numerals`, and `tamil-codec`
- [X] T009 [P] [US2] Synchronize the existing crate status and Phase 1–7 closeout deliverables in `ROADMAP.md`

**Checkpoint**: User Stories 1 and 2 complete.

---

## Phase 5: User Story 3 - Incorporate Missing Tamil NLP Capabilities with Clean Crate vs. Module Boundaries (Priority: P2)

**Goal**: Specify the domain scope, input/output contracts, and crate-vs-module boundaries for the 4 future standalone NLP crates (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`), the 2 in-crate modules (`tamil-codec::braille`, `tamil-numerals` ITN), and the facade orchestration pattern (`FR-008`).

**Independent Test**: Verify in `docs/specs/architecture-roadmap.md` and `specs/016-crate-dependency-roadmap/spec.md` that each missing capability is assigned its exact owner (`tamil-codec::braille` and `tamil-numerals` ITN in `Rank 1`; `tamil-translit`, `tamil-phonetics`, `tamil-tokenize` in `Rank 2`; `tamil-spell` in `Rank 4`), that no empty directories exist for `unscaffolded` crates (`FR-006`), and that compound-hyphenation margin precedence (`left_min = 3, right_min = 3` governing before morphological compound preference) is explicitly specified (`FR-008`).

### Implementation for User Story 3

- [X] T010 [US3] Author the "Planned & Newly Identified NLP Crates and Module Boundaries" section in `docs/specs/architecture-roadmap.md` covering `tamil-punarchi`, `tamil-morph`, `tamil-yaappu`, `tamil-dialect`, `tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`, `tamil-codec::braille`, `tamil-numerals` ITN, and `FR-008` facade orchestration (`HyphenationBoundaryHint` with `3/3` margin precedence)

**Checkpoint**: User Story 3 complete.

---

## Phase 6: User Story 4 - Execute Features by Difficulty Tier & Sequenced Phase Gates (Priority: P2)

**Goal**: Document the capability-level Difficulty Tiers (`Tier 1: Foundation` through `Tier 5: Ambiguous Synthesis & Validation`) and the 18-phase execution schedule (`Phase 0` through `Phase 17`) with hard prerequisites and independent track rules across `docs/specs/architecture-roadmap.md`, `ROADMAP.md`, and `docs/status.md`.

**Independent Test**: Verify that `docs/specs/architecture-roadmap.md`, `ROADMAP.md`, and `docs/status.md` all present the identical `Tier 1`–`Tier 5` matrix and `Phase 0`–`Phase 17` execution table.

### Implementation for User Story 4

- [X] T011 [US4] Author the "Capability Difficulty Tiers (`Tier 1`–`Tier 5`)" and "Sequenced Execution Roadmap (`Phase 0`–`Phase 17`)" sections in `docs/specs/architecture-roadmap.md`
- [X] T012 [P] [US4] Record the completed Feature `016-crate-dependency-roadmap` architecture and DAG governance summary in `docs/status.md`

**Checkpoint**: All 4 user stories complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Run full verification gates from `quickstart.md` to confirm zero regressions and 100% policy/test pass rate.

- [X] T013 Execute `uv run --locked python tools/release_policy.py check` and `uv run --locked pytest tests/harness/test_release_policy.py` to verify the new `Rank 0`–`Rank 6` DAG enforcement and unit tests pass
- [X] T014 [P] Execute `python tools/tasks.py check-unicode` and `git status` to verify all documentation and policy files adhere to repository formatting and that zero Rust crate source files (`crates/*/src/*.rs`) were modified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 — defines `CRATE_RANKS` and `CapabilityStatus`.
- **Phase 3 (User Story 1 - P1 MVP)**: Depends on Phase 2 — implements automated DAG check in `tools/release_policy.py` and core DAG docs.
- **Phase 4 (User Story 2 - P1)**: Depends on Phase 2 — can run in parallel with Phase 3 on documentation sections.
- **Phase 5 (User Story 3 - P2)**: Depends on Phase 3 & Phase 4.
- **Phase 6 (User Story 4 - P2)**: Depends on Phase 5.
- **Phase 7 (Polish)**: Depends on all User Stories (Phases 3–6) completing.

### Parallel Opportunities

- `T003` (`tools/release_policy.py`) and `T004` (`docs/specs/architecture-roadmap.md`) can run in parallel.
- `T005` (`tests/harness/test_release_policy.py`), `T006` (`tools/release_policy.py`), and `T007` (`docs/specs/architecture-roadmap.md`) can run in parallel across test, tool, and documentation files.
- `T008` (`docs/specs/architecture-roadmap.md`) and `T009` (`ROADMAP.md`) can run in parallel.
- `T011` (`docs/specs/architecture-roadmap.md`) and `T012` (`docs/status.md`) can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Run test authoring and documentation authoring in parallel:
Task T005: "Add unit tests in tests/harness/test_release_policy.py verifying Rank 0-6 DAG enforcement"
Task T007: "Author Rank 0-6 DAG section and boundary contracts in docs/specs/architecture-roadmap.md"
```

---

## Implementation Strategy

### MVP First (User Story 1)
1. Complete Phase 1 & Phase 2 (`T001`–`T004`).
2. Complete Phase 3 (`T005`–`T007`) to enforce the `Rank 0`–`Rank 6` DAG in `tools/release_policy.py` and `tests/harness/test_release_policy.py`.
3. Validate independently via `uv run --locked pytest tests/harness/test_release_policy.py`.

### Incremental Delivery
1. Add User Story 2 (`T008`–`T009`): Existing crate gap closeout specs (`Phase 1`–`Phase 7`).
2. Add User Story 3 (`T010`): Missing NLP crate & module boundary specs (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`, `tamil-codec::braille`, `tamil-numerals` ITN).
3. Add User Story 4 (`T011`–`T012`): `Tier 1`–`Tier 5` difficulty matrix, `Phase 0`–`Phase 17` execution table, and `docs/status.md` handoff update.
4. Run Phase 7 validation (`T013`–`T014`).

## Verification handoff (2026-11-08)

T001-T013 complete. Policy checker passes; 48 focused pytest cases pass, including target tables and direct/workspace package aliases. No Rust source or Cargo manifests changed. T014 remains open: `just check-unicode` rejects existing escaped joiners in `crates/tamil-hyphen/src/dic.rs` (29, 31) and `tests/dic_tests.rs` (21). Both agent gates stop at existing Rust formatting drift in hyphen and CLI files. These baseline failures remain outside this feature's explicit no-Rust-edits scope. `git diff --check` passes. No extension hooks file exists.


## Phase 8: Convergence

Assessment date: 2026-11-08. Scope remains documentation and Python governance; future roadmap algorithms, suite activation and publication are not implementation obligations of Feature 016. Existing tasks and completion markers above are preserved. Findings: 3 partial, 1 contradicts; 1 CRITICAL, 1 HIGH, 2 MEDIUM. Checked 10 FRs, 4 SCs, 10 acceptance scenarios, 3 main plan decisions, 14 existing tasks and 7 constitution principles.

- [X] T015 CRITICAL — Complete the outstanding integration verification per Constitution VII and T014 (partial): preserve Feature 016's no-Rust-edits constraint; after the recorded baseline formatting and escaped-joiner failures are resolved within authorized scope, run `just check-unicode`, `just agent-post-edit` and `just agent-pre-stop-gate`, and record actual outcomes in `docs/status.md` and this task file. Do not weaken checks or mark integration complete while gates fail. Evidence: existing verification handoff records unsuccessful gates.
- [X] T016 HIGH — Strengthen the unscaffolded-crate guard in `tools/release_policy.py` and regression coverage in `tests/harness/test_release_policy.py` per FR-006, T005 and T006 (partial): detect empty future-crate directories even without `Cargo.toml`; reject placeholder-only source without relying on the exact literal `STATUS: &str = "planned"`; preserve the four permitted existing scaffolds and document how beginning a specification phase permits legitimate work. Test all four future crate names, manifest-free empty directories, alternate placeholder formatting and an allowed implementation case. Evidence: manifest-only enumeration at lines 77–85 and literal source check at lines 89–94 omit these cases.
- [X] T017 MEDIUM — Define each lifecycle state's evidence and transition criteria in `docs/specs/architecture-roadmap.md` per T004 and spec section 7's Capability Status Vocabulary (partial): distinguish specification plus sourced vectors, local implementation evidence, manifest activation and real runtime parity, publication allowlist plus archive verification, and immutable release publication evidence. Keep roadmap-only proposals distinct from completed specifications and link the definitions from `ROADMAP.md`. Evidence: the canonical Lifecycle and acceptance section currently lists the seven names without individual definitions.
- [X] T018 MEDIUM — Reconcile the current handoff in `docs/status.md` with release records and actual Feature 016 acceptance status per T012 and plan summary decision 1 (contradicts): the retained current-release paragraph identifies alpha.5 while the roadmap identifies alpha.6; clearly label historical material and cite the authoritative current release record. Report incomplete gates without claiming complete integration; retain the canonical tier/phase links and remaining acceptance criteria. Evidence: Feature 016 handoff followed by the stale current-release paragraph and completion claims.

Dependencies: T016–T018 can be addressed within Feature 016's existing scope; T015 closes verification after corrections and baseline prerequisite resolution. No Rust algorithm, Cargo manifest, public allowlist or suite activation change is authorized by this convergence phase.

### Convergence implementation evidence (2026-11-08)

T016–T018 completed. The future-crate guard now checks directories before manifest enumeration and removes comments, attributes and STATUS declarations when detecting placeholder-only sources. This is a bounded heuristic, not Rust parsing or specification approval. Regression cases cover all four names, manifest-free directories, empty/comment/alternate STATUS sources and legitimate implementation alongside a planned status. Existing scaffold manifests continue to pass.

Validation: `uv run --locked pytest tests/harness/test_release_policy.py -q` passed 72 tests; `just check-release-policy` passed; whitespace checks passed. `just check-unicode` still rejects escaped joiners at hyphen `src/dic.rs:29,31` and `tests/dic_tests.rs:21`. Both `just agent-post-edit` and `just agent-pre-stop-gate` still stop at existing `cargo fmt --all -- --check` differences. Logs: `target/feature016-post-edit.log`, `target/feature016-pre-stop.log`. No Rust source or Cargo manifests were modified. T014/T015 remain unchecked pending resolution of those baseline issues; no checks were weakened and integration is not complete. No extension hooks file is present.

### Baseline repair and final validation (2026-11-08)

The user's follow-up request authorized fixing the reported baseline blockers, extending the earlier no-Rust-edits governance scope only for these repairs. Earlier blocked-state notes above are historical and superseded by this result. Applied workspace Rust formatting, preserved both dictionary joiner patterns and their order through explicit scalar construction, asserted both controls, replaced unused-index loops without algorithm changes, and removed unused example imports/mutability. The release acceptance assertion now matches the existing private hyphen exemption and explicitly rejects public hyphen promotion.

T014/T015 complete: `just agent-post-edit` passed (including Unicode/schema and 61 release-copy checks); the final sequential `just agent-pre-stop-gate` passed formatting, Clippy, Rust tests, 158 harness tests, rebuilt Python/WASM bindings, 35,890 active Rust golden vectors, 28 Python tests and 35,913 WASM checks. `just test-dart` passed analysis and 35,909 checks. Four focused dictionary tests passed. `git diff --check` passed. One overlapping Dart/workspace run hit a Windows DLL lock; Dart completed before the successful final sequential gate. No suite status, public allowlist or Cargo manifest changed. Logs remain under `target/feature016-*.log`.
