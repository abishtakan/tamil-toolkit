# Implementation Plan: `tamil-collate` Folded Search & Uyirmei-First Profile

**Branch**: `020-tamil-collate-folded-search` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary
Implement Phase 5 of the architectural roadmap:
1. Versioned `folded_search_key` consuming `tamil-norm` search folding (`fold_for_search` with Mayangoli, Grantha, and Comprehensive profiles) while preserving exact `search_key` backward compatibility.
2. Modern Uyirmei-first school dictionary collation profile (`uyirmei-first-v1`) alongside existing Mei-first `agara-v1`.
3. Multi-runtime exposure in `tamil-toolkit` dispatcher, CLI, Python, and WASM.
4. Golden test vectors in `tests/golden/collate_folded_search.jsonl` and `tests/golden/collate_uyirmei_first.jsonl`.

## Technical Context
- Language/Framework: Rust 2021 (MSRV workspace-pinned), `#![forbid(unsafe_code)]`.
- Workspace Crate: `crates/tamil-collate` (Rank 2), `crates/tamil-toolkit` (Rank 5).
- Dependencies: `tamil-core` (Rank 0), `tamil-norm` (Rank 1).
- Quality Gates: `check-release-policy`, `check-unicode`, `test-rust`, `test-parity`, `agent-pre-stop-gate`.

## Constitution Check
- **Principle I (Rust Single Source of Truth)**: Implemented in `crates/tamil-collate`. Bindings are thin wrappers.
- **Principle II (Inspect by Scalars)**: All test cases escaped (`\u{...}`).
- **Principle III (Golden Vectors & Tri-Runtime Parity)**: Golden suites tested across Rust, Python, and WASM.
- **Principle IV (Separation of Lexical Data and Engine Logic)**: `lexicon/collate_uyirmei_first.toml` compiled via `build.rs`.
- **Principle VII (Rigorous Quality Gates)**: Verified with `just agent-pre-stop-gate`.

## Architecture & Implementation Phases
- **Phase 0 (Research)**: Completed in [research.md](research.md).
- **Phase 1 (Design & Contracts)**: Completed in [data-model.md](data-model.md), [contracts/collation-contracts.md](contracts/collation-contracts.md), [quickstart.md](quickstart.md).
- **Phase 2 (Implementation Execution)**:
  1. Add `lexicon/collate_uyirmei_first.toml`.
  2. Update `crates/tamil-collate/Cargo.toml` to depend on `tamil-norm`.
  3. Update `crates/tamil-collate/build.rs` to generate tables for both profiles.
  4. Update `crates/tamil-collate/src/lib.rs` with `CollationProfile`, `folded_search_key`, and profile-aware functions.
  5. Add golden fixtures for folded search and Uyirmei-first collation.
  6. Expose in `tamil-toolkit` dispatcher and CLI.
  7. Run all validation gates.
