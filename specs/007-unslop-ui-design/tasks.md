# Tasks: Unslop UI Design & De-AI-ification

**Branch**: `007-unslop-ui-design` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

## Phase 1: Setup & Design Tokens

**Purpose**: Audit and refine styling tokens and microcopy to purge AI slop conventions.

- [X] T001 Audit and purge all AI marketing superlatives in `playground/src/lib/i18n.ts`, replacing them with authentic domain-specific linguistic copy in Tamil and English.
- [X] T002 [P] Configure hairline borders and tactile transitions in `playground/src/index.css` (banning `transition: all`, defining 120ms targeted transitions).

---

## Phase 2: User Story 1 - Elimination of AI-Slop Layouts & Asymmetric Bento Workbench (Priority: P1) 🎯 MVP

**Goal**: Replace the repetitive uniform 4-card grid and floating gradient marketing hero with an authentic, asymmetric linguistic workbench.

- [X] T003 [US1] Replace the floating gradient marketing box in `playground/src/components/common/OverviewHub.tsx` with a clean, utilitarian workbench status header displaying active engine telemetry.
- [X] T004 [US1] Build the asymmetric Bento workbench in `playground/src/components/common/OverviewHub.tsx` with a prominent Hero slot for the Codec Converter (with direct legacy font chips), side-by-side linguistic cards for Numeral and Calendar, and Agara Varisai collation.
- [X] T005 [US1] Consolidate the developer diagnostics in `playground/src/components/common/OverviewHub.tsx` into a high-density, integrated engineering console tray.

---

## Phase 3: User Story 2 - Purging AI-Slop Micro-Interactions & Hover Gimmicks (Priority: P2)

**Goal**: Remove all bouncy hover transforms (`scale-105`, sliding arrow translations) across all components.

- [X] T006 [P] [US2] Remove `scale-105` and bouncy hover gimmicks from `playground/src/App.tsx`.
- [X] T007 [P] [US2] Remove `scale-105` and sliding arrow transforms from `playground/src/components/common/OverviewHub.tsx`.
- [X] T008 [P] [US2] Verify and enforce crisp 1px hairline transitions and tactile active states (`active:scale-[0.99]`) on interactive buttons and chips across all tool components.

---

## Phase 4: User Story 3 - Visual Polish & Accessibility (Priority: P3)

**Goal**: Enforce strict WCAG AA contrast and verify that all text elements adhere to authentic Tamil materiality.

- [X] T009 [US3] Verify contrast ratios across light and dark modes in `playground/src/index.css` and component cards.
- [X] T010 [P] [US3] Update unit tests in `playground/src/tests/i18n.test.ts` to test and assert the un-slopped linguistic copy strings.

---

## Phase 5: Verification & Quality Gates

**Purpose**: Validate repository and playground build integrity.

- [X] T011 Run `pnpm --filter tamil-toolkit-playground build` to verify clean compilation.
- [X] T012 Run `pnpm --filter tamil-toolkit-playground test` to verify Vitest test suites.
- [X] T013 Verify zero `scale-105` occurrences remain across `playground/src/`.
- [X] T014 Run `just agent-post-edit` for constitution and workspace checks.
