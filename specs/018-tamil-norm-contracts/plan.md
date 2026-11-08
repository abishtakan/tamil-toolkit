# Implementation Plan: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts (`018`)

**Branch**: `018-tamil-norm-contracts` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-tamil-norm-contracts/spec.md`

## Summary

Expand `crates/tamil-norm` (`Rank 1`) from a minimal 2-line facade into three distinct, robust normalization contracts:
1. **Canonical Normalization**: Lossless `normalize_nfc` and `normalize_nfd`, with strict preservation of `ZWJ` and `ZWNJ`.
2. **Opt-in Orthographic Repair**: `repair_tamil_text` with `RepairOptions` and granular `RepairDiagnostics` (healing duplicate pullis, reordering visual left-kombus, and stripping soft-hyphens/controls).
3. **Versioned Lossy Search Folding**: `fold_for_search` with versioned `FoldingProfile` enum (`Mayangoli`, `Grantha`, `Comprehensive`) preserving diacritics.
4. **Golden Test Suites**: Author active, escaped test vectors in `tests/golden/norm_repair.jsonl` and `tests/golden/norm_folding.jsonl` with manifest registration.
5. **Multi-Runtime Exposure**: Expose in `tamil-toolkit` dispatcher, Python stubs/PyO3 bindings, and TypeScript/WASM bindings.

## Technical Context

**Language/Version**: Modern Stable Rust (MSRV 1.80+), Python 3.11–3.14, Node.js 20/22/24 (WASM).

**Primary Dependencies**:
- Core: `tamil-core` (`Rank 0`), `serde = { version = "1.0", features = ["derive"] }`. Zero additional external crate dependencies.
- Bindings: `pyo3 = "0.22"`, `wasm-bindgen = "0.2"`.

**Testing**: `cargo test -p tamil-norm`, `cargo test -p tamil-toolkit`, tri-runtime golden parity test runner.

**Target Platform**: Native Rust, WebAssembly, Python, Dart C ABI.

**Performance Goals**:
- Canonical normalization: Pass-through latency.
- Orthographic repair: < 50 µs / KB.
- Search folding: < 30 µs / KB.

**Constraints**:
- `Rank 1` invariant: Depends ONLY on `tamil-core` (`Rank 0`).
- `#![forbid(unsafe_code)]` across all Rust modules.
- Preserves `ZWJ`/`ZWNJ` by default unless explicitly configured.

## Constitution Check

| Principle | Check Description | Status | Evidence / Compliance |
|---|---|---|---|
| **I. Rust Owns Linguistic Behavior** | Single engine source of truth in `crates/tamil-norm`. No duplicate logic in JS/Python. | **PASS** | Implemented strictly in `crates/tamil-norm/src/repair.rs` and `folding.rs`. Adapters call Rust engine. |
| **II. Inspect Tamil by Scalars** | No visual regex guesses; inspect via Unicode scalars and escaped sequences. Format controls preserved. | **PASS** | Uses tailored letters and scalar inspection; format controls (`ZWJ`, `ZWNJ`) preserved by default. |
| **III. Golden Vectors Precede Implementation** | Sourced test vectors in `tests/golden/*.jsonl` before algorithm signoff. Tri-runtime parity. | **PASS** | Adding `norm_repair.jsonl` and `norm_folding.jsonl` to active manifest with escaped Unicode. |
| **IV. Separation of Lexical Data and Engine Logic** | Sourced confusion sets and Grantha mappings stored declaratively. | **PASS** | Mayangoli mappings and Grantha fold tables defined statically with documented linguistic rationale. |
| **V. Pluricentric Dialect Scope** | Tamil normalization and folding are regional-invariant. | **PASS** | Both TN and SL orthographies share the same Mayangoli pairs and Unicode canonical rules. |
| **VI. Platform-Conforming Distribution** | Cargo workspace version authority; policy-governed release. | **PASS** | `tamil-norm` is `Rank 1` published crate; zero circular edges or out-of-rank dependencies. |
| **VII. Explicit Guarantees & Quality Gates** | Preserves joiners; zero formatting drift; passes `agent-pre-stop-gate`. | **PASS** | Passes all workspace gates. |

## Project Structure

### Documentation (this feature)

```text
specs/018-tamil-norm-contracts/
├── plan.md              # Implementation plan
├── research.md          # Research findings & Unicode standards
├── data-model.md        # Types and invariants
├── quickstart.md        # Runnable verification scenarios
├── contracts/
│   └── norm-contract.md # API contracts across Rust, JSON, Python, TS
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code

```text
crates/tamil-norm/
├── src/
│   ├── lib.rs           # Re-exports contracts, types, and functions
│   ├── types.rs         # RepairOptions, RepairDiagnostics, RepairResult, FoldingProfile
│   ├── repair.rs        # repair_tamil_text engine
│   └── folding.rs       # fold_for_search engine
└── tests/
    ├── repair_tests.rs  # Unit tests for text repair
    └── folding_tests.rs # Unit tests for search folding

crates/tamil-toolkit/
└── src/
    └── lib.rs           # Dispatcher actions: norm.repair_text, norm.fold_for_search

tests/golden/
├── norm_repair.jsonl    # Escaped test vectors for text repair
├── norm_folding.jsonl   # Escaped test vectors for search folding
└── manifest.json        # Suite registration ("active")

bindings/
├── python/              # Python bindings & stubs
└── js-wasm/             # TypeScript & WASM bindings
```
