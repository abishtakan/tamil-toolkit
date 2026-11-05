# Tasks: Additional Interactive Linguistic & Epigraphical Tools

**Feature**: `008-add-playground-tools` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Type definitions, bilingual strings, and shared engine helpers.

- [x] T001 Update bilingual dictionary with tool titles, descriptions, categories, and action labels in `playground/src/lib/i18n.ts`
- [x] T002 [P] Define data interfaces for TraditionalSymbol, AnalyzedSyllable, and NormalizationResult in `playground/src/lib/engine.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Engine dispatcher bindings and workbench navigation integration.

- [x] T003 Implement engine helper functions for symbols, letter decomposition, and normalization via WebAssembly `execute()` in `playground/src/lib/engine.ts`
- [x] T004 [P] Update tool state and selection chips for new public and developer tools in `playground/src/App.tsx`
- [x] T005 [P] Add interactive launch slots and preview cards for the new tools in `playground/src/components/common/OverviewHub.tsx`

---

## Phase 3: User Story 1 - Traditional Tamil Fractions & Epigraphical Symbol Explorer (Priority: P1) 🎯 MVP

**Goal**: Deliver an interactive catalog and converter for traditional Tamil fractions and epigraphical measurement glyphs.

**Independent Test**: Navigate to Public Tools → Fractions & Symbols, select `காணி`, verify glyph `𑿀`, codepoint `U+11FC0`, fraction `1/80`, and copy function.

### Tests for User Story 1
- [x] T006 [P] [US1] Create unit tests for fraction/symbol lookup, decimal conversions, and category filters in `playground/src/tests/symbols-explorer.test.ts`

### Implementation for User Story 1
- [x] T007 [US1] Implement interactive symbol catalog, search filter, and detail inspector in `playground/src/components/public-tools/SymbolsExplorer.tsx`

---

## Phase 4: User Story 2 - Real-Time Tamil Letter & Uyirmei Morphological Decomposer (Priority: P2)

**Goal**: Deliver real-time syllable segmentation and root consonant + vowel deconstruction.

**Independent Test**: Type `தமிழ்நாடு` into the Letter Analyzer; verify 5 syllables segmented with correct base consonant, vowel, and diacritic identification.

### Tests for User Story 2
- [x] T008 [P] [US2] Create unit tests for letter segmentation, uyirmei splitting, and character classification in `playground/src/tests/letter-analyzer.test.ts`

### Implementation for User Story 2
- [x] T009 [US2] Implement real-time syllable decomposition ribbon, letter inspector card, and classification counters in `playground/src/components/developer-tools/LetterAnalyzer.tsx`

---

## Phase 5: User Story 3 - Tamil Unicode Text Normalizer & Anomaly Repair Tool (Priority: P3)

**Goal**: Deliver real-time Unicode text normalization (NFC/NFD) and digital anomaly repair.

**Independent Test**: Paste text with non-standard diacritics or duplicate pulli; verify automatic repair and one-tap copy of canonical text.

### Tests for User Story 3
- [x] T010 [P] [US3] Create unit tests for NFC/NFD normalization and anomaly diagnostics in `playground/src/tests/normalizer-tool.test.ts`

### Implementation for User Story 3
- [x] T011 [US3] Implement dual-pane diff textareas, NFC/NFD selector, and anomaly diagnostic badges in `playground/src/components/developer-tools/NormalizerTool.tsx`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Ergonomics verification, quality gates, and documentation consistency.

- [x] T012 [P] Verify touch target sizes and dark mode contrast tokens for new tool components in `playground/src/tests/mobile-ergonomics.test.ts`
- [x] T013 Execute full verification suite: Vitest tests, production build, and `just agent-post-edit`

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** → **Phase 3 (US1: Fractions/Symbols Explorer)** → **Phase 4 (US2: Letter Analyzer)** → **Phase 5 (US3: Normalizer Tool)** → **Phase 6 (Polish)**.
- Once Foundational (Phase 2) is complete, User Stories 1, 2, and 3 are independently implementable and testable.
