# Implementation Plan: Calendar Golden Suite Activation (Phase 1)

**Branch**: `002-calendar-activation` | **Date**: 2026-11-05 | **Spec**: [specs/002-calendar-activation/spec.md](spec.md)

**Input**: Feature specification from `/specs/002-calendar-activation/spec.md`

## Summary

Activate and validate the stable tabular, metadata, and civil display calendar golden test suites (`calendar_official_holidays.jsonl`, `calendar_tamil_display.jsonl`, `calendar_thiruvalluvar_year.jsonl`) alongside the already-active `calendar_year_cycle.jsonl`. Verify cross-runtime parity across Rust, Python, WebAssembly, and Dart. Ensure Unicode schema compliance and update documentation and manifest records.

## Technical Context

**Language/Version**: Rust 1.85 (MSRV), TypeScript / Vite, Python 3.11+, Dart 3.x
**Primary Dependencies**: `tamil-core`, `tamil-calendar`, `tamil-toolkit`
**Testing**: `cargo test`, `just test-parity`, `just check-unicode`, `just agent-pre-stop-gate`
**Target Platform**: Native OS (Rust, Python, Dart), WebAssembly (Node & Browser)
**Constraints**: Zero regression across all active golden suites; strict schema validation; exact multi-runtime parity.

## Constitution Check

- **Principle I: Rust Owns Linguistic Behavior**: PASS. All operations run through `crates/tamil-calendar` and the unified dispatcher in `crates/tamil-toolkit`.
- **Principle II: Inspect Tamil by Scalars**: PASS. Display formatting and calendar labels strictly use verified Unicode scalars.
- **Principle III: Golden Vectors Precede Implementation**: PASS. Golden vectors are already established in `tests/golden/*.jsonl`.
- **Principle IV: Separation of Lexical Data**: PASS. Tabular data and display names remain strictly isolated from computation logic.
- **Principle V: Pluricentric Dialect Scope**: PASS. Official holiday schedules for TN (Tamil Nadu) and SL (Sri Lanka) are preserved distinctly with dialect tags.
- **Principle VI: Platform Naming & Policy**: PASS. Release policy status is maintained according to crate release gating rules.
- **Principle VII: Rigorous Quality Gates**: PASS. All tests across Rust, Python, WASM, and Dart must pass without discrepancies.

## Implementation Steps

1. **Phase 1: Manifest & Vector Updates**
   - In `tests/golden/manifest.json`, transition:
     - `calendar_official_holidays.jsonl` to `"status": "active"`
     - `calendar_tamil_display.jsonl` to `"status": "active"`
     - `calendar_thiruvalluvar_year.jsonl` to `"status": "active"`
   - In the corresponding `.jsonl` files, remove `"planned"` from the vector `tags` array.

2. **Phase 2: Validation & Parity Verification**
   - Run `just check-unicode` to ensure schema conformance and absence of joiners/normalization issues.
   - Run Rust tests (`cargo test --test golden_suite`).
   - Run Python golden tests (`pytest tests/harness/test_golden.py`).
   - Run WASM golden tests (`pnpm --filter tamil-toolkit-wasm test`).
   - Run `just test-parity` for full cross-runtime parity.

3. **Phase 3: Documentation & Status Updates**
   - Update `docs/status.md` and `docs/specs/002-calendar-activation.md` reflecting the activation of Phase 1 civil calendar suites.
