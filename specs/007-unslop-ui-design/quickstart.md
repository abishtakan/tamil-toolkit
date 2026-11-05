# Quickstart & Visual Verification Guide: Unslop UI Design

## Automated Checks

### 1. Zero Scale-105 & Banned Gimmick Check
Verify no `scale-105` or bouncy hover transforms exist in the codebase:
```powershell
Get-ChildItem -Path playground/src -Recurse -Filter *.tsx | Select-String -Pattern 'scale-105'
```
**Expected Outcome**: 0 occurrences found.

### 2. TypeScript Compilation Check
```bash
pnpm --filter tamil-toolkit-playground build
```
**Expected Outcome**: Build succeeds with zero errors in ~500ms.

### 3. Automated Test Suite
```bash
pnpm --filter tamil-toolkit-playground test
```
**Expected Outcome**: All 10 test suites pass.

## Visual Inspection Scenarios

1. **Home Workbench View**:
   - Verify the top bar presents a clean engine status strip rather than a giant floating gradient marketing box.
   - Verify tools are arranged in an asymmetric Bento workbench (Codec Converter as hero, Numeral & Calendar as structured cards, Developer Tools as a compact diagnostic console).
2. **Tactile Hover & Focus Verification**:
   - Hover over cards: observe subtle 1px border color change and tonal surface shift; confirm no bouncy scale-up.
   - Click card: observe crisp tactile press (`active:scale-[0.99]`).
   - Tab through with keyboard: observe high-visibility focus outline rings.
