# Quickstart & Validation Guide: Bilingual Architecture

## Prerequisites
- Node.js 20+
- pnpm 10+
- Repository built and WebAssembly binding ready

## Validation Scenarios

### Scenario 1: Verify TypeScript Key Parity
Run the typecheck build:
```bash
pnpm --filter tamil-toolkit-playground build
```
**Expected Outcome**: Build succeeds in < 1s with zero missing key or type mismatch errors.

### Scenario 2: Verify Elimination of Inline Conditionals
Search for leftover inline conditionals:
```powershell
Get-ChildItem -Path playground/src -Recurse -Filter *.tsx | Select-String -Pattern 'language ==='
```
**Expected Outcome**: Only the toggle button in header and LanguageProvider contain `language` references; zero inline ternaries in tool bodies or component text.

### Scenario 3: Verify Automated Test Suite
Run playground tests:
```bash
pnpm --filter tamil-toolkit-playground test
```
**Expected Outcome**: All tests pass.
