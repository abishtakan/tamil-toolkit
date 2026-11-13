# Implementation Plan: Validate Reused Rust APIs & NFC/NFD Normalization (`tamil-core`, `tamil-norm`, `tamil-toolkit`)

**Branch**: `022-validate-reused-rust-apis` | **Date**: 2026-11-13 | **Spec**: [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/spec.md)

**Input**: Feature specification from [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/022-validate-reused-rust-apis/spec.md)

## Summary

Validate all Rust primitives and contracts reused by Feature 021 (`021-lexicon-curation`) across `tamil-core`, `tamil-norm`, and `tamil-toolkit`, with explicit emphasis on proving Unicode 17.0.0 NFC/NFD canonical normalization correctness in `tamil-norm`. Where validation uncovered gaps—missing `tamil-norm` crate-level property/NFC/NFD/NFD-folding test depth, missing dedicated canonical golden cases in `tests/golden/norm_canonical.jsonl`, 9 implemented operations omitted from `tamil_toolkit::OPERATIONS`, and silent fallback in `tamil-toolkit norm fold --profile <unknown>`—this feature adds golden vectors first, closes the code/contract gaps in Rust, rebuilds cross-language bindings, and verifies parity across Rust, Python, WASM, and Dart.

## Technical Context

**Language/Version**: Rust (stable workspace toolchain, Edition 2021), Python 3.11+ (`.venv`), TypeScript/WASM, Dart FFI  
**Primary Dependencies**: `tamil-core`, `tamil-norm`, `tamil-toolkit`, `unicode-normalization = "0.1.26"`, `unicode-segmentation = "1.13.3"`, `proptest`, `serde_json`  
**Storage**: File-based escaped golden fixtures in `tests/golden/*.jsonl` registered in `tests/golden/manifest.json`  
**Testing**: `cargo test --locked`, `proptest` (`>= 10,000` cases per NFC/NFD invariant), `pytest` harness (`test-parity`), Dart FFI tests (`test-dart`), `clippy -D warnings`, `tools/tasks.py check-unicode` / `check-release-policy`  
**Target Platform**: Windows host + cross-platform Rust / PyO3 / Node+Browser WASM / C ABI + Dart bindings  
**Project Type**: Multi-crate workspace library + CLI + MCP oracle + multi-language bindings  
**Performance Goals**: Zero regression to borrowed zero-allocation `Letters::new` and linear normalization/folding complexity  
**Constraints**:
- Preserve Feature 021 spec/plan/tasks (`specs/021-lexicon-curation/`) and immutable intake files (`data/sources/tamil-lexicon/`) untouched
- Keep all Tamil strings in golden JSONL, Rust tests, and data files escaped (`\uXXXX` / `\u{XXXX}`) per Unicode gate
- Run `test-parity` / `agent-pre-stop-gate` and `test-dart` strictly sequentially on Windows to avoid DLL locking  
**Scale/Scope**: Validation + targeted bug fixes across `tamil-core`, `tamil-norm`, `tamil-toolkit`, `tests/golden/`, and documentation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1. **Principle I — Rust Owns Linguistic Behavior**: PASS. All normalization, segmentation, repair, folding, and dispatcher validation logic lives strictly in `crates/tamil-core`, `crates/tamil-norm`, and `crates/tamil-toolkit`; Python/WASM/Dart remain thin wrappers calling `execute`.
2. **Principle II — Scalar Inspection & Zero-Guessing**: PASS. All golden cases and Rust tests inspect scalars via `\uXXXX` / `\u{XXXX}` escapes and explicit Unicode exception annotations for intentional NFD inputs; `just check-unicode` verifies every line.
3. **Principle III — Golden Vectors Precede Implementation**: PASS. `tests/golden/norm_canonical.jsonl` and `tests/golden/manifest.json` updates are authored and verified before any Rust fixes (`OPERATIONS` sync, CLI flag parsing, regression/property tests).
4. **Principle IV — Pluricentric Tamil Scope**: PASS. Canonical normalization vectors use `dialect: "COMMON"` (dialect-invariant Unicode layer) while exercising TN/SL/Grantha conjuncts and Shri variants without lossy folding.
5. **Principle V — Separation of Data & Engine**: PASS. No executable code enters `lexicon/`; all test vectors live cleanly under `tests/golden/` and `crates/*/tests/`.
6. **Principle VI — Multi-Runtime Parity & Exact Guarantees**: PASS. Every active golden vector runs unchanged in Rust, Python, WASM, and Dart (`sync-bindings`, `test-parity`, `test-dart`). Contract bounds (`Letters::new` non-normalizing vs `get_letters` NFC, single-letter scope for `classify_quantity`/`baseline_maathirai`, joiner preservation) are explicitly documented rather than overstated.
7. **Principle VII — Packaging & Release Safety**: PASS. `check-release-policy` and `check-release-files` verify crate boundaries without triggering registry publication.

*Post-Phase 1 Re-Check*: All contracts (`contracts/tamil-norm-normalization.md`, `contracts/tamil-core-reuse.md`, `contracts/tamil-toolkit-dispatcher.md`) conform strictly to Principles I–VII.

## Project Structure

### Documentation (this feature)

```text
specs/022-validate-reused-rust-apis/
├── spec.md                              # Feature specification
├── checklists/requirements.md           # Spec quality checklist
├── plan.md                              # This implementation plan
├── research.md                          # Phase 0 empirical findings & decisions
├── data-model.md                        # Validation entities & golden vector schema
├── quickstart.md                        # Runnable verification sequence
├── contracts/
│   ├── tamil-norm-normalization.md      # NFC/NFD & NFD-input repair/fold contract
│   ├── tamil-core-reuse.md              # Feature 021 reused primitives contract
│   └── tamil-toolkit-dispatcher.md      # OPERATIONS <-> execute & CLI contract
└── tasks.md                             # Generated by /speckit-tasks
```

### Source Code & Tests Touched (repository root)

```text
tests/golden/
├── norm_canonical.jsonl                 # NEW: Canonical NFC/NFD, CCC, format-control, Shri, malformed, NFD-folding vectors
└── manifest.json                        # Register norm_canonical suite as active

crates/tamil-norm/
├── Cargo.toml                           # Ensure proptest dev-dependency if needed
└── tests/
    └── norm_tests.rs                    # Expand NFC/NFD unit tests, proptest (>=10k cases), NFD fold/repair sweep

crates/tamil-core/
└── tests/
    └── phonology_tests.rs               # Verify/lock Feature 021 reused primitives & joiner/single-letter edge cases

crates/tamil-toolkit/
├── src/lib.rs                           # Sync OPERATIONS with all execute() arms + verify null/error handling
├── src/bin/tamil-toolkit.rs             # Fix `norm fold --profile <invalid>` silent fallback + flag ordering
└── tests/
    └── golden_suite.rs                  # Add OPERATIONS <-> execute completeness & dispatcher contract tests

docs/
├── status.md                            # Update handoff status
└── ...                                  # CHANGELOG.md under Unreleased if public ops list/CLI behavior updated
```

## Complexity Tracking

No constitution exceptions or structural violations required. All edits stay strictly inside existing workspace crates, golden suites, and documentation.
