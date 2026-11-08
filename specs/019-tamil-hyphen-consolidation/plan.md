# Implementation Plan: tamil-hyphen Release Policy, Manifest & WASM Consolidation

**Branch**: `019-tamil-hyphen-consolidation` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/019-tamil-hyphen-consolidation/spec.md`

## Summary

Consolidate `tamil-hyphen` with `tamil-core` Phase 1 phonological primitives, activate `hyphen_syllable.jsonl` in `tests/golden/manifest.json`, promote `tamil-hyphen` to `public_crates` in `release-policy.toml`, remove private exemptions in `tools/release_policy.py`, consolidate Playground and Word Add-in onto the unified Rust/WASM engine, and add rich CLI subcommands for all active crates in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`.

## Technical Context

**Language/Version**: Rust 1.95+ (2021 edition), TypeScript 5.5+, Python 3.11+
**Primary Dependencies**: `tamil-core`, `tamil-norm`, `serde`, `serde_json`, `clap`/manual CLI dispatch, `unicode-segmentation`
**Storage**: N/A (declarative golden JSONL and static tables)
**Testing**: `cargo test`, Nextest, Pytest, Vitest, Node test runner
**Target Platform**: Multi-platform (Rust native, WebAssembly browser, Node.js, Office.js)
**Project Type**: Workspace library crates, CLI binary, WebAssembly bindings
**Performance Goals**: Zero-allocation letter inspection/syllable classification where possible; sub-millisecond word hyphenation
**Constraints**: `#![forbid(unsafe_code)]`, strict DAG Rank order (`tamil-hyphen` Rank 2, `tamil-toolkit` Rank 5), 100% tri-runtime parity on all active golden suites

## Constitution Check

- **I. Rust Owns Linguistic Behavior**: PASS. All hyphenation, classification, and conversion logic originates in Rust.
- **II. Inspect Tamil by Scalars**: PASS. All characters inspected by Unicode scalars or `tamil-core` primitives. No raw non-NFC or unescaped non-ASCII in code.
- **III. Golden Vectors Precede Implementation**: PASS. `hyphen_syllable.jsonl` fixtures are active and validated without mocks.
- **IV. Separation of Lexical Data and Engine Logic**: PASS. Pattern dictionaries generated deterministically.
- **V. Pluricentric Dialect Scope**: PASS. Common Tamil rules applied uniformly with dialect neutrality.
- **VI. Policy-Governed Releases**: PASS. `tamil-hyphen` promoted through `release-policy.toml` and verified by `tools/release_policy.py`.
- **VII. Rigorous Quality Gates**: PASS. All gates in `just agent-pre-stop-gate` enforced.

## Project Structure

### Documentation (this feature)

```text
specs/019-tamil-hyphen-consolidation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code Impact

```text
crates/
├── tamil-hyphen/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs
│       └── syllable.rs            # Refactor to consume tamil-core primitives
├── tamil-toolkit/
│   └── src/
│       └── bin/
│           └── tamil-toolkit.rs   # Expanded CLI subcommands
tests/
└── golden/
    └── manifest.json              # Activate hyphen_syllable.jsonl
release-policy.toml                # Add tamil-hyphen to public_crates
tools/
└── release_policy.py              # Remove temporary hyphen exemptions
```

## Structure Decision

Direct edits to `crates/tamil-hyphen/src/syllable.rs`, `tests/golden/manifest.json`, `release-policy.toml`, `tools/release_policy.py`, and `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`.
Integrations verified via `tests/integrations/test_word_addin_contract.js` and playground tests.
