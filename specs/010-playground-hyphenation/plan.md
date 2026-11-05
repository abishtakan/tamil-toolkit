# Implementation Plan: Interactive Tamil Syllabic Hyphenator & Line Wrapper (`playground-hyphenation`)

**Feature**: `010-playground-hyphenation` | **Date**: 2026-11-05 | **Spec**: [specs/010-playground-hyphenation/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/010-playground-hyphenation/spec.md)

---

## 1. Technical Context & Integration Surface

The Tamil Toolkit Playground is a React 19 + TypeScript + Vite + Tailwind CSS web application running 100% client-side with WebAssembly (`tamil-toolkit/web`).

This feature adds a new interactive Public Tool:
- **Component**: `playground/src/components/public-tools/HyphenatorTool.tsx`
- **Engine Layer**: `playground/src/lib/engine.ts` (WASM integration + offline fallback)
- **Localization**: `playground/src/lib/i18n.ts` (Tamil & English strings)
- **Hub Navigation**: `playground/src/App.tsx` & `playground/src/components/common/OverviewHub.tsx`
- **Unit & Integration Tests**: `playground/src/tests/hyphenator-tool.test.ts`

---

## 2. Architecture & Data Flow

```
[User Input: Word / Text / Width Slider]
                  │
                  ▼
   [HyphenatorTool.tsx React Component]
                  │
                  ▼
        [engine.ts Helper API]
          │                │
          │ (WASM Ready)   │ (Fallback / Offline)
          ▼                ▼
   [tamil-toolkit/web]  [Local JS Syllabifier]
   (tt.execute dispatch)
          │                │
          └───────┬────────┘
                  ▼
    [HyphenationResult / WrapResult]
                  │
                  ▼
[Render Syllable Chips, Breakpoints, Soft-Hyphens, Responsive Column]
```

---

## 3. Implementation Phases

### Phase 1: Engine & Localization Foundation
- Add `HyphenationConfig`, `HyphenationPoint`, `HyphenationResult`, `WrapResult` to `playground/src/lib/engine.ts`.
- Expose `hyphenateWord`, `getHyphenationPoints`, `hyphenateText`, and `wrapText` with WASM dispatch and pure TS fallback.
- Add complete bilingual dictionaries in `playground/src/lib/i18n.ts` for English and Tamil.

### Phase 2: Interactive UI Component (`HyphenatorTool.tsx`)
- Build the 3-tab layout:
  1. **Word Syllables**: Syllable badge ribbon, coda binding alert, break points table, margin sliders, delimiter dropdown.
  2. **Paragraph Soft-Hyphens**: Input textarea, soft-hyphen injection, show/hide invisible marks toggle, HTML copy button.
  3. **Line Wrapping Simulator**: Column width slider (letters), side-by-side comparison (Standard vs Syllabic Wrap).

### Phase 3: Hub & Navigation Integration
- Add `HyphenatorTool` to `playground/src/App.tsx` tool chips and view switcher.
- Add tool card to `playground/src/components/common/OverviewHub.tsx` under Public Utilities.
- Update `playground/README.md` and root `README.md`.

### Phase 4: Verification & Automated Tests
- Create `playground/src/tests/hyphenator-tool.test.ts`.
- Run `pnpm --filter tamil-toolkit-playground test`.
- Run `pnpm --filter tamil-toolkit-playground build`.
