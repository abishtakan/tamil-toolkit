# Tasks: Interactive Public & Developer Playground (`playground`)

**Feature**: `005-playground` | **Date**: 2026-11-05 | **Spec**: [specs/005-playground/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/005-playground/spec.md) | **Plan**: [specs/005-playground/plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/005-playground/plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the `playground` workspace package, configure Vite, React, TypeScript, Tailwind CSS, and shadcn/ui primitives.

- [x] T001 Update workspace configuration in `pnpm-workspace.yaml` to include `playground`
- [x] T002 Initialize `playground/package.json` with dependencies (`react`, `react-dom`, `lucide-react`, `@radix-ui/react-tabs`, `@radix-ui/react-toast`, `@radix-ui/react-dialog`, `tailwindcss`, `vite`, `vite-plugin-pwa`, `tamil-toolkit: "workspace:*"`)
- [x] T003 [P] Configure TypeScript compiler in `playground/tsconfig.json` and `playground/tsconfig.node.json`
- [x] T004 [P] Configure Vite 8 in `playground/vite.config.ts` with WASM support and PWA configuration
- [x] T005 [P] Setup Tailwind CSS v4 and design tokens per `specs/005-playground/design-standard.md` in `playground/src/index.css`
- [x] T006 [P] Create HTML template with mobile viewport, theme-color, and PWA manifest link in `playground/index.html`
- [x] T007 Add playground scripts to root `package.json` and `justfile` (`playground-dev`, `playground-build`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core application shell, WebAssembly engine lifecycle management, and shared mobile-first ergonomic primitives.

**⚠️ CRITICAL**: No user story implementation can begin until the engine lifecycle and base layout are established.

- [x] T008 Implement WebAssembly engine loader and state manager in `playground/src/lib/engine.ts`
- [x] T009 [P] Implement utility functions and class merger in `playground/src/lib/utils.ts`
- [x] T010 [P] Implement accessible UI primitives (`Button`, `Card`, `Tabs`, `Badge`, `Textarea`, `Toast`) styled with terracotta/parchment tokens in `playground/src/components/ui/`
- [x] T011 [P] Implement single-tap clipboard copy component and mobile sticky action bar in `playground/src/components/common/CopyButton.tsx` and `playground/src/components/common/StickyActionBar.tsx`
- [x] T012 [P] Implement bilingual i18n translation dictionary and language context (`தமிழ்` / `English`) in `playground/src/lib/i18n.ts`
- [x] T013 Implement main application shell, header with language toggle, and top/bottom navigation in `playground/src/App.tsx`
- [x] T014 Implement React entry bootstrap and engine initialization in `playground/src/main.tsx`

**Checkpoint**: Foundation ready — the application shell loads, initializes the WASM engine, and renders responsive navigation.

---

## Phase 3: User Story 1 - Public Tools with Zero-Friction Mobile & Real-Time UX (Priority: P1) 🎯 MVP

**Goal**: Deliver everyday end-user tools (Legacy Font Converter, Numeral Formatter, Calendar Explorer, Text Sorter) featuring real-time conversion and zero-friction mobile touch controls.

**Independent Test**: Open `http://localhost:5173` on a mobile viewport (390px), paste Bamini text; verify auto-detection identifies `bamini-v1` and renders converted Unicode in under 30ms without clicking "Convert"; tap Copy to verify toast confirmation; test numeral to words and calendar display.

### Tests for User Story 1
- [x] T015 [P] [US1] Unit test for real-time legacy conversion and auto-detection in `playground/src/tests/codec-converter.test.tsx`
- [x] T016 [P] [US1] Unit test for numeral and currency formatting in `playground/src/tests/numeral-formatter.test.tsx`
- [x] T017 [P] [US1] Unit test for calendar date conversion and panchangam lookup in `playground/src/tests/calendar-explorer.test.tsx`
- [x] T018 [P] [US1] Component test for mobile sticky action bar interactions in `playground/src/tests/mobile-ergonomics.test.tsx`

### Implementation for User Story 1
- [x] T019 [US1] Implement real-time Legacy Font & Encoding Converter component (`Bamini`, `TSCII`, `TAB`, `TAM`, `Anjal`, `Vanavil`, `LT-TM`, auto-detect chip row, swap button) in `playground/src/components/public-tools/CodecConverter.tsx`
- [x] T020 [US1] Implement Numeral & Currency Formatter component (formal words, spoken variants, cheque format, traditional numerals, fractions) in `playground/src/components/public-tools/NumeralFormatter.tsx`
- [x] T021 [US1] Implement Tamil Calendar & Panchangam Explorer component (Gregorian to Tamil solar date, Thiruvalluvar year, 60-year cycle title, nakshatra, tithi, daylight periods, official holidays) in `playground/src/components/public-tools/CalendarExplorer.tsx`
- [x] T022 [US1] Implement Agara Varisai Sorter component (alphabetical collation, duplicate filter, syllable breakdown) in `playground/src/components/public-tools/TextSorter.tsx`
- [x] T023 [US1] Integrate Public Tools into `playground/src/App.tsx` with mobile bottom action bar bindings (Copy, Clear, Swap)

**Checkpoint**: User Story 1 (MVP) is fully functional, responsive, and testable independently.

---

## Phase 4: User Story 2 - Developer Diagnostics & Interactive API Sandbox (Priority: P2)

**Goal**: Deliver interactive diagnostics for engineers, including Unicode scalar inspection, raw JSON dispatcher console, and multi-language code generation.

**Independent Test**: Navigate to the Developer tab, input complex Tamil text (e.g. `தமிழ்` with or without invisible ZWJ/ZWNJ); verify each scalar hex code (`\u{0B85}`) and grapheme boundary is visualised; inspect raw JSON request/response; copy generated Python/Rust/TS/Dart snippets.

### Tests for User Story 2
- [x] T024 [P] [US2] Unit test for Unicode scalar breakdown and invisible control detection in `playground/src/tests/scalar-inspector.test.tsx`
- [x] T025 [P] [US2] Unit test for code snippet generator accuracy in `playground/src/tests/code-generator.test.tsx`

### Implementation for User Story 2
- [x] T026 [US2] Implement Unicode Scalar & Grapheme Inspector component (hex codepoint badges, cluster breakdown, ZWJ/ZWNJ alert badges) in `playground/src/components/developer-tools/ScalarInspector.tsx`
- [x] T027 [US2] Implement Interactive Dispatcher Sandbox component (monaco/textarea JSON editor, preset payload selector, latency display, raw JSON response) in `playground/src/components/developer-tools/DispatcherSandbox.tsx`
- [x] T028 [US2] Implement Multi-Language Code Snippet Generator component (`Rust`, `Python`, `TypeScript`, `Dart` templates for active operations) in `playground/src/components/developer-tools/CodeGenerator.tsx`
- [x] T029 [US2] Integrate Developer Tools into `playground/src/App.tsx` tabs

**Checkpoint**: User Stories 1 and 2 are fully functional and testable independently.

---

## Phase 5: User Story 3 - Client-Side Privacy, Web Worker & Offline Operation (Priority: P3)

**Goal**: Deliver non-blocking batch file processing via Web Worker, offline PWA caching, and verify zero network telemetry.

**Independent Test**: Drop a multi-page legacy text document into the batch converter; verify progress updates without UI stuttering; toggle browser DevTools to offline mode and verify all tools continue operating; verify zero outgoing network requests during all interactions.

### Tests for User Story 3
- [x] T030 [P] [US3] Unit test for Web Worker RPC communication in `playground/src/tests/worker-client.test.ts`
- [x] T031 [P] [US3] End-to-end network assertion verifying zero HTTP requests during conversions in `playground/src/tests/privacy.test.ts`

### Implementation for User Story 3
- [x] T032 [US3] Implement background Web Worker for batch file conversions and dispatcher execution in `playground/src/workers/playground.worker.ts`
- [x] T033 [US3] Implement worker RPC bridge client with progress reporting in `playground/src/lib/worker-client.ts`
- [x] T034 [US3] Implement Batch File Processor component (drag-and-drop file dropzone, encoding selector, download converted file) in `playground/src/components/developer-tools/BatchProcessor.tsx`
- [x] T035 [US3] Configure Progressive Web App manifest and service worker CacheFirst caching in `playground/vite.config.ts` and `playground/src/pwa.ts`
- [x] T036 [US3] Integrate batch processor into Developer Tools and register service worker in `playground/src/main.tsx`

**Checkpoint**: All three user stories are complete, verified client-side, and functional offline.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cross-viewport visual polishing, performance optimization, documentation, and validation.

- [x] T037 [P] Perform responsive layout audit across mobile viewports (360px, 390px, 768px, 1024px) ensuring no clipped text or horizontal overflow in `playground/src/App.tsx`
- [x] T038 [P] Optimize bundle splitting and chunking in `playground/vite.config.ts` to ensure gzipped JS bundle remains < 250 KB
- [x] T039 Execute all 5 validation scenarios defined in `specs/005-playground/quickstart.md`
- [x] T040 Update repository documentation in `README.md` and `docs/development.md` to reference the public playground and development commands

---

## Dependencies & Execution Order

```text
Phase 1: Setup (T001 - T007)
       │
       ▼
Phase 2: Foundational (T008 - T014) ─── [BLOCKS all user stories]
       │
       ├───────────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼
Phase 3: US1 - Public Tools (MVP)   Phase 4: US2 - Dev Diagnostics   Phase 5: US3 - Worker & Offline
(T015 - T023)                       (T024 - T029)                    (T030 - T036)
       │                               │                               │
       └───────────────────────────────┼───────────────────────────────┘
                                       │
                                       ▼
                       Phase 6: Polish & Verification (T037 - T040)
```

### User Story Dependencies
- **Foundational Phase (Phase 2)**: Mandatory prerequisite for US1, US2, and US3.
- **User Story 1 (P1)**: Independent of US2 and US3. Represents the core user-facing MVP.
- **User Story 2 (P2)**: Independent of US1 and US3. Reuses foundational UI components.
- **User Story 3 (P3)**: Depends on foundational engine; connects batch UI to Worker.

### Parallel Opportunities
- In Phase 1: `T003`, `T004`, `T005`, `T006` can run in parallel.
- In Phase 2: `T009`, `T010`, `T011` can run in parallel.
- Once Phase 2 is complete:
  - Developer A can implement US1 (`T019`–`T022`).
  - Developer B can implement US2 (`T026`–`T028`).
  - Developer C can implement US3 (`T032`–`T035`).
- In Phase 6: `T037` and `T038` can run in parallel.

---

## Implementation Strategy: MVP First

1. **Step 1**: Complete **Phase 1 (Setup)** and **Phase 2 (Foundational)**.
2. **Step 2**: Implement **Phase 3 (User Story 1 - Public Tools MVP)**.
3. **Step 3**: Validate MVP independently against Scenario 1 & 2 in `quickstart.md`.
4. **Step 4**: Implement **Phase 4 (User Story 2 - Developer Diagnostics)**.
5. **Step 5**: Implement **Phase 5 (User Story 3 - Batch Worker & Offline PWA)**.
6. **Step 6**: Run **Phase 6 (Polish & Verification)** and complete release audit.
