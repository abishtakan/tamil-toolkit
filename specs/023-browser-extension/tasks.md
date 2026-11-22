---
description: "Dependency-ordered task list for Native-Themed Tamil Browser Extension (023-browser-extension)"
---

# Tasks: Native-Themed Tamil Browser Extension

**Input**: Design documents from `/specs/023-browser-extension/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/extension-messages.md`, `quickstart.md`

**Tests**: Real-WASM Vitest suites, dual-browser manifest invariant tests, hybrid live-typing unit tests, and Playwright Chromium extension smoke tests are included to satisfy Constitution Principle III (no mocks) and `quickstart.md`.

**Organization**: Tasks are grouped by user story (`US1`–`US4`) in priority order so each story can be implemented and validated as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) — used only in User Story phases
- Every task includes exact repository-relative file path(s)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extract the shared slim Apache-2.0 WASM builder, register `integrations/browser-extension` in the `pnpm` workspace, and scaffold TypeScript, Vite, and Vitest configuration.

- [X] T001 Extract reusable slim Apache-2.0 default-profile WASM builder accepting `--out-dir` and `--force` into `integrations/shared/prepare-slim-wasm.mjs` and update `integrations/office-word-addin/scripts/prepare-wasm.mjs` to delegate to it
- [X] T002 Register `integrations/browser-extension` in `pnpm-workspace.yaml` and create `integrations/browser-extension/package.json` with scripts (`prepare-wasm`, `build`, `build:chrome`, `build:firefox`, `test`, `package`) and workspace dependency `tamil-toolkit: workspace:*`
- [X] T003 [P] Create TypeScript and Vitest configuration in `integrations/browser-extension/tsconfig.json` and `integrations/browser-extension/vitest.config.ts`
- [X] T004 [P] Create multi-entry Vite build configuration (background, content, panel, offscreen, target-specific theme token selection via `BROWSER_TARGET=chrome|firefox`) in `integrations/browser-extension/vite.config.ts`
- [X] T005 [P] Add clean native-style extension toolbar icons (`16`, `32`, `48`, `128` PNG/SVG) under `integrations/browser-extension/src/assets/icons/` and copy subsetted `Noto Sans Tamil` (400/500/600) + `Noto Sans Tamil Supplement` (`U+11FC0–U+11FFF`) `.woff2` files into `integrations/browser-extension/src/assets/fonts/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared runtime shims, typed storage & IPC contracts, canonical slim-WASM engine host, and dual-browser MV3 manifest generation required before any user story can run.

**⚠️ CRITICAL**: No user story implementation begins until this phase is complete.

- [X] T006 Implement dual-browser MV3 manifest generator emitting `dist/chrome/manifest.json` (`side_panel`, `offscreen`, `background.service_worker`) and `dist/firefox/manifest.json` (`sidebar_action` with `open_at_install: false`, non-persistent `background.scripts`, `browser_specific_settings.gecko` with `strict_min_version: "140.0"` and `data_collection_permissions: { required: ["none"] }`), zero `host_permissions`, `optional_host_permissions`, `commands.toggle-live-typing` (`Alt+Shift+T`), and CSP `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'` in `integrations/browser-extension/scripts/build-manifests.mjs`
- [X] T007 [P] Implement thin Chrome/Firefox compatibility wrapper (action badge, synchronous `sidebarAction.open()` / `sidePanel.open()`, storage, scripting, permissions, commands, contextMenus) in `integrations/browser-extension/src/shared/browser-api.ts`
- [X] T008 [P] Define discriminated-union IPC message contracts (`ENGINE_*`, `OPEN_SIDE_PANEL`, `TOGGLE_LIVE_TYPING`, `TAB_*`, `OFFSCREEN_COPY_TEXT`) matching `contracts/extension-messages.md` in `integrations/browser-extension/src/shared/messages.ts`
- [X] T009 [P] Implement typed local & session storage helpers in `integrations/browser-extension/src/shared/storage.ts` enforcing `UserPreferences` (`uiLang: "ta" | "en"` defaulting to `"ta"` if UI locale starts with `"ta"`, `layout: "phonetic-v1" | "tamil99" | "anjal-phonetic" | "suratha-bamini"` default `"phonetic-v1"`, `lastTab: "inspect" | "live" | "fix" | "tools"` default `"live"`, `numeralLocale: "TN" | "SL"` default `"TN"`, `currency: "INR" | "LKR"` default `"INR"`, `sortProfile: "agara-v1" | "uyirmei-first-v1"` default `"agara-v1"`, `showMicroCounter: boolean` default `true`), `PerSitePermissionRecord` (strictly single-origin `https://<hostname>/*` or `http://<hostname>/*`, reconciled with `permissions.getAll()`), and `SelectionHandoffPayload` (single-use `requestId`, 60-second expiry)
- [X] T010 Implement lazy slim-WASM loader and canonical `tamil-toolkit` API wrapper (`createApi(nativeExecute)`) in `integrations/browser-extension/src/engine/tamil-engine.ts` covering `transliterate`, `detect_encoding`, 7 legacy codecs, `repair_text` (`strip_joiners: false`), `sort_lines`, `decimal_to_words`, `currency_decimal_to_words`, `format_tamil_date`, `calendar_display_info`, and `calendar_official_holidays` (excluding all 13 planned ephemeris suites)
- [X] T011 Implement background coordinator & WASM RPC host skeleton (`ENGINE_*` message dispatcher, startup permission reconciliation, restricted-URL detection) in `integrations/browser-extension/src/background/index.ts`
- [X] T012 [P] Write manifest invariant tests verifying zero install-time `host_permissions`, required permissions split (`sidePanel`/`offscreen` Chrome-only, `sidebar_action`/`gecko.data_collection_permissions` Firefox-only), CSP, and `Alt+Shift+T` command in `integrations/browser-extension/tests/manifests.test.ts`

**Checkpoint**: Foundation ready — slim WASM builds cleanly, manifests validate for Chrome and Firefox, and user story implementation can proceed.

---

## Phase 3: User Story 1 - Live Inline Tamil Typing on Any Web Page (Priority: P1) 🎯 MVP

**Goal**: Deliver one-click (`action.onClicked` / `Alt+Shift+T`) live inline Tamil typing directly inside standard web page editors using a hybrid commitment model (Phonetic & Anjal word-boundary preview + `Esc` English bypass; Tamil99 & Bamini instant per-keystroke conversion), a focus-aware Shadow DOM floating pill, sensitive-field protection, canvas-editor scratchpad fallback, and opt-in per-site "Always on".

**Independent Test**: Open a web page with `<input>`, `<textarea>`, `contenteditable`, and `<input type="password">`, click the toolbar icon or press `Alt+Shift+T`, type in Phonetic/Anjal (word-boundary commit + `Esc` bypass) and Tamil99/Bamini (instant per-keystroke commit), verify Backspace/Undo and pill focus auto-hide, confirm password fields stay untouched, and test canvas-editor scratchpad fallback.

### Tests for User Story 1

- [X] T013 [P] [US1] Write real-WASM transliteration tests covering `"phonetic-v1"`, `"tamil99"`, `"anjal-phonetic"`, and `"suratha-bamini"` active golden vectors in `integrations/browser-extension/tests/engine.test.ts`
- [X] T014 [P] [US1] Write unit tests for hybrid commitment (`word-boundary` vs `instant-keystroke`), `Escape` word bypass, Backspace handling, sensitive-field exclusion (`password`, `email`, `url`, `tel`, `number`, `one-time-code`, `cc-*`), and canvas-editor detection in `integrations/browser-extension/tests/live-typing.test.ts`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement safe editor adapter (`setRangeText` + `InputEvent` for native inputs/textareas, `execCommand("insertText")` with Range fallback for `contenteditable`, sensitive-field guard, and canvas editor detection for Google Docs / Figma) in `integrations/browser-extension/src/content/editor-adapter.ts`
- [X] T016 [US1] Implement hybrid inline typing state machine (`ActiveCompositionSession`: word-boundary preview + Space/Enter/punctuation commit + `Escape` bypass for `phonetic-v1` and `anjal-phonetic`; rolling instant per-keystroke commit for `tamil99` and `suratha-bamini`; RPC calls to background `ENGINE_TRANSLITERATE`) in `integrations/browser-extension/src/content/live-typing.ts`
- [X] T017 [P] [US1] Implement focus-aware Shadow DOM floating pill (~2s confirmation toast on toggle, visible while an editable field is focused, auto-hides on non-editable page content, `தமிழ் ON / EN` toggle, 4-layout switcher, `Inspect` & Side Panel trigger, optional live micro-counter slot, and compact Quick-Compose scratchpad for canvas editors) in `integrations/browser-extension/src/content/floating-pill.ts`
- [X] T018 [US1] Wire content script lifecycle, focus/blur listeners, `TAB_SET_LIVE_STATE` / `TAB_INSERT_TEXT` handlers, and cleanup on deactivate in `integrations/browser-extension/src/content/index.ts`
- [X] T019 [US1] Implement toolbar click (`action.onClicked`) & `Alt+Shift+T` (`commands.onCommand`) live-typing toggle, `த` badge updates, on-demand `scripting.executeScript` injection, restricted-page Side Panel fallback, and opt-in per-site "Always on" (`permissions.request` + `scripting.registerContentScripts`) in `integrations/browser-extension/src/background/index.ts`
- [X] T020 [US1] Implement the **Live Type** side-panel tab (master Live Typing toggle, per-site "Always on for <hostname>" opt-in toggle, 4-layout selector, and standalone/canvas Quick-Compose input with Insert & Copy actions) in `integrations/browser-extension/src/panel/tabs/live-tab.ts`

**Checkpoint**: User Story 1 (MVP) is independently functional and verifiable in Chrome/Edge and Firefox.

---

## Phase 4: User Story 2 - Live Document and Selection Tamil Inspector (Priority: P2)

**Goal**: Provide a live Document & Selection Inspector powered by `tamil-core` / `tamil-norm` showing true Tamil letter count (எழுத்து), word count (சொல்), syllable count, UTF-16 unit comparison, estimated reading time, Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, Unicode health diagnostics, 1-click "Repair in place", and the optional live micro-counter while typing.

**Independent Test**: Type or highlight clean and malformed Tamil text on a web page, open Inspect, verify exact Tamil letter counts (`தமிழ்` = 4 vs 5 UTF-16 units), category counts, and health warnings; click "Repair in place" on an editable field and confirm `U+200D`/`U+200C` preservation; open Inspect with nothing selected/focused and test the 1-click "Inspect visible page" button and standalone paste box.

### Tests for User Story 2

- [X] T021 [P] [US2] Add real-WASM inspection & Unicode health tests (true Tamil letter count, Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, visual left-kombu, duplicate pulli, `U+200D`/`U+200C` preservation, legacy encoding detection, empty/English inputs) to `integrations/browser-extension/tests/engine.test.ts`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `InspectionSnapshot` builder using `tamil-core` letter/syllable/category APIs, `is_nfc`, `repair_text` dry-run diagnostics, and `detect_encoding` in `integrations/browser-extension/src/engine/inspect.ts`
- [X] T023 [US2] Wire `ENGINE_INSPECT` background RPC handler in `integrations/browser-extension/src/background/index.ts` and `TAB_GET_CONTEXT_TEXT` (`mode: "auto" | "visible-page"`) + `TAB_REPLACE_TEXT` handlers in `integrations/browser-extension/src/content/index.ts`
- [X] T024 [US2] Implement the **Inspect** side-panel tab (stat cards for Tamil Letters / Words / UTF-16 Units, reading time, Uyir/Mei/Uyirmei/Aytham/Grantha stacked bar, Health status with 1-click "Repair in place" when editable, 1-click "Inspect visible page" when nothing is selected/focused, and standalone paste/type fallback) in `integrations/browser-extension/src/panel/tabs/inspect-tab.ts`
- [X] T025 [US2] Connect the optional live `எழுத்து · சொல்` micro-counter (debounced `ENGINE_INSPECT` updates governed by `UserPreferences.showMicroCounter`) into `integrations/browser-extension/src/content/floating-pill.ts`

**Checkpoint**: User Stories 1 and 2 both work independently and together seamlessly.

---

## Phase 5: User Story 3 - In-Place Legacy Text Conversion, Repair, and Line Sorting (Priority: P3)

**Goal**: Enable right-click silent repair-and-copy, right-click "Convert to Tamil…" with cold-start selection handoff, in-place "Repair & Replace" / "Convert & Replace" inside editable fields, 7-codec conversion with Auto ambiguity guard, joiner-preserving repair, and traditional *Agara Varisai* / *Uyirmei-first* line sorting.

**Independent Test**: Select legacy Bamini/TSCII text and broken Tamil on both read-only and editable pages; verify silent right-click "Copy repaired Tamil" (no panel jump, joiners preserved), right-click "Convert to Tamil…" cold-start handoff, explicit codec prompt on ambiguous Auto input, in-place replacement in editable fields, and line sorting in both profiles.

### Tests for User Story 3

- [X] T026 [P] [US3] Add real-WASM tests for all 7 legacy codecs (`bamini`, `tscii`, `tab`, `tam`, `anjal`, `vanavil`, `lt_tm`), Auto ambiguity guard, `repair_text` (`strip_joiners: false`), and `agara-v1` / `uyirmei-first-v1` line sorting to `integrations/browser-extension/tests/engine.test.ts`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement Chrome-only offscreen silent plain-text clipboard helper (`OFFSCREEN_COPY_TEXT`) in `integrations/browser-extension/src/offscreen/offscreen.html` and `integrations/browser-extension/src/offscreen/offscreen.ts`
- [X] T028 [US3] Register selection right-click context menus ("Copy repaired Tamil", "Convert to Tamil…", and editable-field in-place repair/replace), cold-start `SelectionHandoffPayload` storage write, synchronous Firefox `sidebarAction.open()` / Chrome `sidePanel.open()`, and `ENGINE_DETECT_AND_CONVERT` / `ENGINE_REPAIR` / `ENGINE_SORT_LINES` RPC handlers in `integrations/browser-extension/src/background/index.ts`
- [X] T029 [US3] Implement the **Fix Text** side-panel tab (3-way switch: Convert legacy with Auto + 7 manual codecs & ambiguity prompt, Repair Tamil with `strip_joiners: false`, Sort lines with `agara-v1` default / `uyirmei-first-v1`; "Replace in page" when `editable: true` + "Copy"; consumes `SelectionHandoffPayload` once) in `integrations/browser-extension/src/panel/tabs/fix-tab.ts`

**Checkpoint**: User Stories 1, 2, and 3 are independently testable and complete.

---

## Phase 6: User Story 4 - Native Host-Browser Appearance, Bilingual Interface, and Compact Everyday Tools (Priority: P4)

**Goal**: Deliver authentic Chrome Refresh 2023 styling on Chrome/Edge and Firefox Acorn/Proton + `browser.theme.getCurrent()` styling on Firefox (Light/Dark auto-sync), full bilingual Tamil/English UI with auto-locale detection, offline TN/SL numerals & INR/LKR currency words, supported TN civil date + official TN/SL holidays, and opt-in per-site Tamil font fixing with Settings revocation.

**Independent Test**: Open the extension in Chrome/Edge and Firefox under Light and Dark themes, toggle `தமிழ் / EN`, convert INR/LKR numbers in TN and SL locales, view today's TN civil date and official TN/SL holidays (including unsupported-year messaging), and toggle "Improve Tamil fonts here" on and off with full style restoration.

### Tests for User Story 4

- [X] T030 [P] [US4] Add real-WASM tests for TN/SL numerals, INR/LKR currency words, active TN civil date formatting, and official TN/SL holidays (including unsupported-year handling) to `integrations/browser-extension/tests/engine.test.ts`

### Implementation for User Story 4

- [X] T031 [P] [US4] Create shared semantic layout & component styles in `integrations/browser-extension/src/shared/theme/base.css`, Chrome Refresh 2023 Light/Dark native tokens in `integrations/browser-extension/src/shared/theme/chrome-tokens.css`, and Firefox Acorn/Proton Light/Dark tokens + runtime `browser.theme.getCurrent()` sync in `integrations/browser-extension/src/shared/theme/firefox-tokens.css`
- [X] T032 [P] [US4] Implement complete bilingual Tamil/English string dictionary and browser-locale auto-detection (`ta` default if Tamil locale, else `en`) in `integrations/browser-extension/src/shared/i18n.ts`
- [X] T033 [P] [US4] Implement opt-in per-site Tamil font fixer (requests single-origin permission, injects `Noto Sans Tamil` + `Noto Sans Tamil Supplement` `U+11FC0–U+11FFF` CSS via `scripting.insertCSS` scoped to `:lang(ta)` reading elements outside editable inputs, removes CSS via `scripting.removeCSS` before revoking origin permission) in `integrations/browser-extension/src/background/font-fixer.ts`
- [X] T034 [US4] Implement the **Tools** side-panel tab (Numbers & INR/LKR currency words with TN/SL toggle; Dates showing today's active TN civil date + TN/SL official holidays with source attribution and unsupported-year notice; "Improve Tamil fonts here" site toggle) in `integrations/browser-extension/src/panel/tabs/tools-tab.ts`
- [X] T035 [US4] Assemble the native-themed Side Panel / Sidebar shell (4-tab navigation `Inspect`, `Live Type`, `Fix Text`, `Tools`, persistent `தமிழ் / EN` toggle, compact Settings drawer listing all opted-in sites with 1-click revoke, micro-counter toggle, and browser-target theme class) in `integrations/browser-extension/src/panel/panel.html` and `integrations/browser-extension/src/panel/main.ts`

**Checkpoint**: All four user stories are complete, bilingual, native-themed, and independently testable.

---

## Phase 7: Polish, Store Packaging & Cross-Cutting Verification

**Purpose**: Store-ready ZIP & reproducible AMO source packaging, Playwright Chromium E2E smoke tests, bundle size verification (< 2 MiB), and repository quality gates.

- [X] T036 Implement store archive builder producing `dist/tamil-toolkit-chrome.zip`, `dist/tamil-toolkit-firefox.zip` (each bundling root `LICENSE`, `NOTICE`, and font notices and asserting compressed size < 2 MiB), and `dist/tamil-toolkit-firefox-source.zip` (reproducible AMO source bundle with Linux rebuild script) in `integrations/browser-extension/scripts/package-zips.mjs`
- [X] T037 [P] Add Playwright Chromium extension smoke test verifying live inline typing, Shadow DOM pill auto-hide, Inspect counts, in-place repair, right-click handoff, and zero network requests in `integrations/browser-extension/tests/e2e/extension.spec.ts`
- [X] T038 Run full verification suite (`pnpm --filter tamil-browser-extension build`, `pnpm --filter tamil-browser-extension test`, `pnpm --filter tamil-browser-extension package`, `just check-unicode`, `just check-release-policy`, `just check-release-files`) and update `docs/status.md` and `CHANGELOG.md` with the browser extension milestone

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS** all user story phases (`US1`–`US4`).
- **Phase 3 (`US1` — P1 MVP)**: Depends on Phase 2 only; no dependencies on other stories.
- **Phase 4 (`US2` — P2)**: Depends on Phase 2; enhances `floating-pill.ts` from `US1` for the optional live micro-counter (T025), while `inspect.ts` and `inspect-tab.ts` can be built independently.
- **Phase 5 (`US3` — P3)**: Depends on Phase 2; completely independent of `US1`/`US2`.
- **Phase 6 (`US4` — P4)**: Depends on Phase 2; integrates all 4 tab modules into `panel/main.ts` (T035).
- **Phase 7 (Polish & Packaging)**: Depends on completion of all desired user stories.

### Parallel Opportunities

- **Setup**: T003, T004, T005 can run in parallel once T001–T002 are underway.
- **Foundational**: T007, T008, T009, and T012 can run in parallel alongside T006 and T010.
- **Within US1**: T013, T014 (tests), T015 (`editor-adapter.ts`), and T017 (`floating-pill.ts`) can run in parallel before wiring T016, T018, T019, T020.
- **Within US2**: T021 (tests) and T022 (`inspect.ts`) run in parallel before T023–T025.
- **Within US3**: T026 (tests) and T027 (`offscreen/*`) run in parallel before T028–T029.
- **Within US4**: T030 (tests), T031 (`theme/*`), T032 (`i18n.ts`), and T033 (`font-fixer.ts`) all run in parallel before T034–T035.

### Parallel Example: User Story 1

```text
Parallel batch 1:
- T013 [P] [US1] Real-WASM transliteration tests (tests/engine.test.ts)
- T014 [P] [US1] Hybrid live-typing unit tests (tests/live-typing.test.ts)
- T015 [P] [US1] Safe editor adapter & sensitive-field guard (src/content/editor-adapter.ts)
- T017 [P] [US1] Focus-aware Shadow DOM floating pill (src/content/floating-pill.ts)

Sequential wiring batch 2:
- T016 [US1] Hybrid typing state machine (src/content/live-typing.ts)
- T018 [US1] Content script entrypoint (src/content/index.ts)
- T019 [US1] Background toggle, badge, restricted fallback & per-site Always-on (src/background/index.ts)
- T020 [US1] Live Type side-panel tab (src/panel/tabs/live-tab.ts)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Complete **Phase 1 (Setup)** + **Phase 2 (Foundational)** → slim WASM builds, dual Chrome/Firefox MV3 manifests pass invariant tests.
2. Complete **Phase 3 (US1 — Live Inline Tamil Typing)** → verify inline typing across Phonetic, Tamil99, Anjal, and Bamini with zero broad install permissions.
3. **STOP & VALIDATE**: Load `dist/chrome` and `dist/firefox` unpacked and test `US1` end-to-end.

### Incremental Delivery
1. Setup + Foundational → Core foundation ready.
2. Add **US1 (P1)** → Live inline typing MVP.
3. Add **US2 (P2)** → Live Document & Selection Tamil Inspector + micro-counter.
4. Add **US3 (P3)** → In-place Legacy Conversion, Repair & Line Sorting + right-click flows.
5. Add **US4 (P4)** → Native Chrome/Firefox theme tokens, bilingual `தமிழ் / EN`, TN/SL tools, and per-site font fixer.
6. Run **Phase 7** → Store ZIPs (< 2 MiB), AMO reproducible source archive, Playwright smoke tests, and repo gates.

---

## Phase 8: Convergence

- [X] T039 Ensure word-boundary keys (`Space`, `Enter`, punctuation) are never dropped when `preventDefault()` fires and `HybridTypingEngine.handleKeyDown` returns `handled: false` in `integrations/browser-extension/src/content/index.ts` per FR-005 / US1/AC1 (partial)
- [X] T040 Add an editable-selection "Repair & Replace in place" right-click context menu item in `integrations/browser-extension/src/background/index.ts` that repairs selected text and applies `TAB_REPLACE_TEXT` directly into the active editable field per FR-013 / US3/AC3 (missing)
- [X] T041 Expand real-WASM tests in `integrations/browser-extension/tests/engine.test.ts` to cover all 7 legacy codecs (`bamini`, `tscii`, `tab`, `tam`, `anjal`, `vanavil`, `lt_tm`), Auto-detect ambiguity guard, and `uyirmei-first-v1` line sorting per FR-011 / T026 / Constitution III (partial)
- [X] T042 Localize all Shadow DOM floating pill labels in `integrations/browser-extension/src/content/floating-pill.ts` and Inspect health diagnostic messages in `integrations/browser-extension/src/panel/tabs/inspect-tab.ts` via `integrations/browser-extension/src/shared/i18n.ts` for both Tamil and English per FR-017 / US4/AC2 (partial)
- [X] T043 Push `TAB_SET_LIVE_STATE` to the active tab whenever `showMicroCounter` or `uiLang` is toggled in `integrations/browser-extension/src/panel/main.ts` so the floating pill updates immediately per FR-010 / US2/AC4 (partial)
- [X] T044 Implement executable built-bundle and Playwright Chromium smoke tests in `integrations/browser-extension/tests/e2e/extension.spec.ts` and wire an `e2e` script in `integrations/browser-extension/package.json` per plan: Testing / T037 (partial)
