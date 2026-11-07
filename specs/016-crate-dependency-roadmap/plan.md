# Implementation Plan: Crate Dependency DAG, Capability Boundaries & Difficulty-Tiered Roadmap (`016`)

**Branch**: `016-crate-dependency-roadmap` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [`specs/016-crate-dependency-roadmap/spec.md`](spec.md)

## Summary

Establish the authoritative **Crate Dependency Directed Acyclic Graph (`Rank 0` through `Rank 6`)**, **Capability Difficulty Tiers (`Tier 1` through `Tier 5`)**, **Existing Crate Gap Inventory**, **Missing Tamil NLP Capability Boundaries**, and **18-Phase Sequenced Execution Roadmap (`Phase 0` through `Phase 17`)** across `tamil-toolkit`.

Per the clarified specification (`FR-001` through `FR-010`) and user scope boundary (*"This is the documentation and project structure task not an implementation task"*):
1. Author the canonical architecture and roadmap specification in [`docs/specs/architecture-roadmap.md`](../../docs/specs/architecture-roadmap.md) and synchronize root [`ROADMAP.md`](../../ROADMAP.md) and [`docs/status.md`](../../docs/status.md).
2. Encode the `Rank 0`–`Rank 6` crate dependency DAG invariant and unscaffolded-crate guard directly into [`tools/release_policy.py`](../../tools/release_policy.py) (`just check-release-policy`) with unit test coverage in [`tests/harness/test_release_policy.py`](../../tests/harness/test_release_policy.py) so out-of-rank or circular dependencies across `[dependencies]`, `[build-dependencies]`, and `[dev-dependencies]` are automatically rejected.
3. Make zero implementation changes to Rust source files (`crates/*/src/*.rs`), keeping the 4 existing planned crates (`tamil-punarchi`, `tamil-morph`, `tamil-yaappu`, `tamil-dialect`) as internal scaffolds and deferring creation of the 4 newly identified standalone crates (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`) until their respective roadmap phases (`Phase 8`, `Phase 14`, `Phase 9`, `Phase 16`).

## Technical Context

**Language/Version**: Markdown (CommonMark / GitHub Flavored Markdown + Mermaid), Python 3.11+ (`tools/release_policy.py` policy checker), TOML (`Cargo.toml`, `release-policy.toml`)  
**Primary Dependencies**: Python standard library (`tomllib`, `json`, `unittest`, `pathlib`) for `tools/release_policy.py`; zero external dependencies added  
**Storage**: Repository documentation (`docs/specs/architecture-roadmap.md`, `ROADMAP.md`, `docs/status.md`, `specs/016-crate-dependency-roadmap/*`)  
**Testing**: `uv run --locked python tools/release_policy.py check` (`just check-release-policy`), `uv run --locked pytest tests/harness/test_release_policy.py`, `python tools/tasks.py check-unicode`  
**Target Platform**: Cross-platform repository governance & CI/CD (`Linux`, `macOS`, `Windows`)  
**Project Type**: Multi-crate Rust/WASM/Python/Dart/PostgreSQL linguistic toolkit monorepo (Architecture & Roadmap Governance)  
**Performance Goals**: `check-release-policy` executes in $< 200\text{ ms}$ over all workspace manifests  
**Constraints**: Strictly a documentation, project-structure, and policy-governance task — MUST NOT implement new Rust algorithms in `crates/*/src/*.rs` or scaffold empty directories for future `unscaffolded` crates (`FR-006`)  
**Scale/Scope**: Governs 12 existing workspace crates, 1 isolated PostgreSQL extension (`extensions/pg_tamil`), 3 FFI binding crates (`bindings/*`), 4 future standalone NLP crates (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`), 2 in-crate modules (`tamil-codec::braille`, `tamil-numerals` ITN), and 18 sequenced phases (`Phase 0`–`Phase 17`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Pre-Research Gate | Post-Design Gate | Notes |
|---|---|---|---|
| **I. Rust Owns Linguistic Behavior** | **PASS** | **PASS** | Roadmap Phase 3 explicitly schedules consolidating the Playground and Word Add-in JS/TS hyphenation logic onto the shared Rust/WASM engine, and `Rank 5` (`tamil-toolkit`) owns cross-branch orchestration. |
| **II. Inspect Tamil by Scalars** | **PASS** | **PASS** | Phase 2 `tamil-norm` contracts preserve `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`) by default and require explicit opt-in with diagnostic provenance for any control-character stripping. |
| **III. Golden Vectors Precede Implementation** | **PASS** | **PASS** | `FR-010` mandates the 6-step milestone gate (spec $\rightarrow$ escaped golden vectors $\rightarrow$ Rust engine $\rightarrow$ adapters $\rightarrow$ parity $\rightarrow$ suite activation) for all 18 phases. |
| **IV. Separation of Lexical Data and Engine Logic** | **PASS** | **PASS** | All planned crates (`tamil-punarchi`, `tamil-morph`, `tamil-yaappu`, `tamil-dialect`, `tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`) require declarative `lexicon/*.toml` sources with primary-source citations. |
| **V. Pluricentric Dialect Scope & Regional Invariance** | **PASS** | **PASS** | `tamil-dialect` (`Phase 15`), `tamil-numerals` (`Phase 6`), and `tamil-calendar` (`Phase 4`) explicitly distinguish `ta-IN` (TN) and `ta-LK` (Jaffna, Batticaloa, Vanni, Up-Country), plus `ta-SG`/`ta-MY`. |
| **VI. Platform-Conforming Distribution & Policy-Governed Releases** | **PASS** | **PASS** | `FR-001` and `FR-009` enforce the `Rank 0`–`Rank 6` DAG and publication dependency closure directly in `tools/release_policy.py` (`just check-release-policy`). |
| **VII. Explicit Guarantees & Rigorous Quality Gates** | **PASS** | **PASS** | Distinguishes capability status (`unscaffolded`, `planned`, `specified`, `implemented`, `active`, `release-approved`, `published`) so planned suites are never misrepresented as active. |

## Project Structure

### Documentation (this feature)

```text
specs/016-crate-dependency-roadmap/
├── spec.md                                # Normative feature specification (completed & clarified)
├── plan.md                                # This implementation plan
├── research.md                            # Phase 0 research & architectural decisions
├── data-model.md                          # Phase 1 entities, ranks, tiers & boundary contracts
├── quickstart.md                          # Phase 1 verification & validation commands
├── contracts/
│   └── dependency-dag-contract.md         # Canonical CRATE_RANKS & release_policy.py contract
├── checklists/
│   └── requirements.md                    # 14/14 passing specification quality checklist
└── tasks.md                               # Phase 2 output ($speckit-tasks command)
```

### Repository Documentation & Policy Files Touched

```text
C:\Users\abish\Documents\dev\tamil-toolkit\
├── ROADMAP.md                             # Root project roadmap synchronized with Spec 016
├── docs/
│   ├── status.md                          # Project handoff & Spec 016 architecture record
│   └── specs/
│       └── architecture-roadmap.md        # Canonical docs/specs architecture & dependency DAG spec
├── tools/
│   └── release_policy.py                  # Enforces CRATE_RANKS (Rank 0-6 DAG) across all Cargo manifests
└── tests/
    └── harness/
        └── test_release_policy.py         # Unit tests verifying DAG rank enforcement & cycle rejection
```

**Structure Decision**: Because `016-crate-dependency-roadmap` is strictly an architectural documentation and project-structure governance task, deliverables are confined to `specs/016-crate-dependency-roadmap/`, `docs/specs/architecture-roadmap.md`, `ROADMAP.md`, `docs/status.md`, and the automated DAG policy checker in `tools/release_policy.py` (+ `tests/harness/test_release_policy.py`). No `crates/*/src/*.rs` files are modified.

## Complexity Tracking

> No Constitution Check violations exist. All gates pass.
