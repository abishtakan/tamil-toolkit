# Tasks: Interactive Tamil Syllabic Hyphenator & Line Wrapper (`playground-hyphenation`)

**Feature**: `010-playground-hyphenation` | **Date**: 2026-11-05 | **Spec**: [specs/010-playground-hyphenation/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/010-playground-hyphenation/spec.md) | **Plan**: [specs/010-playground-hyphenation/plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/010-playground-hyphenation/plan.md)

---

## Phase 1: Setup & Engine Foundation

- [X] T001 Define `HyphenationConfig`, `HyphenationPoint`, `HyphenationResult`, and `WrapResult` interfaces and helpers in `playground/src/lib/engine.ts`
- [X] T002 Implement WASM dispatch with fallback syllabification in `playground/src/lib/engine.ts`
- [X] T003 Add bilingual dictionary strings (`t.tools.hyphenator`) in `playground/src/lib/i18n.ts` for English and Tamil

---

## Phase 2: Interactive UI Component

- [X] T004 Implement `HyphenatorTool.tsx` with Word Syllable mode (chips, break points table, coda binding alert, margin controls, delimiter selector)
- [X] T005 Implement Paragraph Soft-Hyphen mode in `HyphenatorTool.tsx` with high-visibility toggle and HTML snippet copy
- [X] T006 Implement Responsive Column & Line Wrapping mode in `HyphenatorTool.tsx` with letter slider and side-by-side comparison

---

## Phase 3: Hub & Navigation Integration

- [X] T007 Register `HyphenatorTool` in `playground/src/App.tsx` navigation chips and view switcher
- [X] T008 Add `HyphenatorTool` feature card in `playground/src/components/common/OverviewHub.tsx`
- [X] T009 Update `playground/README.md` to document the new tool under Public Utilities

---

## Phase 4: Verification & Automated Tests

- [X] T010 Create automated test suite in `playground/src/tests/hyphenator-tool.test.ts`
- [X] T011 Run `pnpm --filter tamil-toolkit-playground test` and verify all tests pass
- [X] T012 Run `pnpm --filter tamil-toolkit-playground build` and verify bundle builds cleanly
