# Quickstart Validation Guide: Calendar Crate Split

**Feature**: `specs/001-calendar-crate-split`

This guide details runnable commands to validate the calendar crate split across all workspace layers.

## 1. Prerequisites
- Rust toolchain (1.85+)
- `uv` / Python 3.11+
- `pnpm` / Node 22+

## 2. Validation Scenarios

### Scenario A: Build and Test `tamil-numerals` (Isolated Verification)
Verify that `tamil-numerals` compiles cleanly without `astro` and without calendar modules, and passes all its unit and property tests.
```powershell
cargo test -p tamil-numerals --locked
```
**Expected Outcome**: All 35,646 numeral golden rows and core numeric property tests pass. No calendar code is compiled.

### Scenario B: Build and Test `tamil-calendar` (Standalone Crate Verification)
Verify that the new `tamil-calendar` crate compiles and runs its test suite independently.
```powershell
cargo test -p tamil-calendar --locked
```
**Expected Outcome**: Clean compilation and passing unit tests for Thirukanitham and Vakiya astronomical models.

### Scenario C: Release Policy & Verification Gate
Verify that release policy checks pass and recognize `tamil-calendar` as an unreleased workspace crate while keeping `tamil-numerals` valid.
```powershell
just check-release-policy
```
**Expected Outcome**: Passes with zero policy violations; `tamil-calendar` is preserved as an experimental workspace crate.

### Scenario D: Tri-Runtime Binding & Parity Verification
Rebuild bindings and verify multi-runtime parity through the shared dispatcher:
```powershell
just sync-bindings
just test-parity
```
**Expected Outcome**: Python PyO3 wrapper, Node/browser WASM packages, and Dart bindings build cleanly, with zero regressions on active test suites.

### Scenario E: Workbench Verification
Verify that the developer workbench displays the new `tamil-calendar` package card and its operations:
```powershell
pnpm run check:workbench
pnpm run build:workbench
```
**Expected Outcome**: TypeScript typecheck passes and production Vite build finishes with HTTP 200 and WASM module generation.
