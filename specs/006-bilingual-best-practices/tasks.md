# Tasks: Bilingual Architecture & Internationalization Best Practices

**Branch**: `006-bilingual-best-practices` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

## Phase 1: Setup (Foundational Schema & Context)

**Purpose**: Expand the centralized translation schema and context provider to support exhaustive keys and URL synchronization.

- [X] T001 [P] Expand `Translations` interface in `playground/src/lib/i18n.ts` with comprehensive keys for `hub`, `nav`, and all tool-specific headers, actions, inputs, outputs, error states, and tags.
- [X] T002 Implement full `ta` and `en` dictionary objects matching `Translations` contract in `playground/src/lib/i18n.ts`.
- [X] T003 Upgrade `LanguageProvider` in `playground/src/lib/i18n.ts` to implement 4-tier language resolution: URL query `?lang=`, `localStorage`, `navigator.language`, and default `ta`.
- [X] T004 Implement seamless URL synchronization via `window.history.replaceState` in `LanguageProvider` when `setLanguage` is called in `playground/src/lib/i18n.ts`.

---

## Phase 2: User Story 1 - Centralized Translation Catalog & Zero Inline Logic (Priority: P1) 🎯 MVP

**Goal**: Eliminate all inline `language === "en" ? ... : ...` expressions from all playground components, routing 100% of text through `t`.

- [X] T005 [P] [US1] Refactor `playground/src/components/common/OverviewHub.tsx` to replace all inline conditionals with `t.hub.*` and `t.actions.*`.
- [X] T006 [P] [US1] Refactor `playground/src/components/public-tools/CodecConverter.tsx` to replace all inline conditionals with `t.tools.codec.*` and `t.actions.*`.
- [X] T007 [P] [US1] Refactor `playground/src/components/public-tools/NumeralFormatter.tsx` to replace all inline conditionals with `t.tools.numeral.*` and `t.actions.*`.
- [X] T008 [P] [US1] Refactor `playground/src/components/public-tools/CalendarExplorer.tsx` to replace all inline conditionals with `t.tools.calendar.*` and `t.actions.*`.
- [X] T009 [P] [US1] Refactor `playground/src/components/public-tools/TextSorter.tsx` to replace all inline conditionals with `t.tools.sorter.*` and `t.actions.*`.
- [X] T010 [P] [US1] Refactor `playground/src/components/developer-tools/DispatcherSandbox.tsx` to replace all inline conditionals with `t.tools.dispatcher.*` and `t.actions.*`.
- [X] T011 [P] [US1] Refactor `playground/src/components/developer-tools/CodeGenerator.tsx` to replace all inline conditionals with `t.tools.codegen.*` and `t.actions.*`.
- [X] T012 [P] [US1] Refactor `playground/src/components/developer-tools/BatchProcessor.tsx` to replace all inline conditionals with `t.tools.batch.*` and `t.actions.*`.
- [X] T013 [P] [US1] Refactor `playground/src/components/developer-tools/ScalarInspector.tsx` to replace all inline conditionals with `t.tools.scalar.*` and `t.actions.*`.
- [X] T014 [US1] Refactor `playground/src/App.tsx` header, language toggle button, and footer to consume `t.nav.*` and `t.siteTitle`.

**Checkpoint**: Zero inline ternaries exist across presentation components.

---

## Phase 3: User Story 2 & 3 - Shareable URL & Accessibility (Priority: P2 & P3)

**Goal**: Validate URL query param synchronization and ensure accessibility through dynamic `document.documentElement.lang` and `document.title`.

- [X] T015 [US2] Ensure initial mount listens to URL query changes or popstate events in `playground/src/lib/i18n.ts`.
- [X] T016 [US3] Add dynamic `document.title` synchronization in `LanguageProvider` (`playground/src/lib/i18n.ts`) reflecting the active localized site title.
- [X] T017 [P] [US2] Write unit tests in `playground/src/tests/i18n.test.ts` verifying dictionary key parity, URL parameter reading, and language toggle persistence.

---

## Phase 4: Polish & Quality Gates

**Purpose**: Verify repository integrity, type safety, and test coverage.

- [X] T018 Run `pnpm --filter tamil-toolkit-playground build` to verify clean TypeScript compilation and bundle generation.
- [X] T019 Run `pnpm --filter tamil-toolkit-playground test` to verify all playground unit and component tests pass.
- [X] T020 Run `just agent-post-edit` or repository pre-stop verification gates.
