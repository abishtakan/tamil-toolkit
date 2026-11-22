# Implementation Plan: Native-Themed Tamil Browser Extension

**Branch**: `023-browser-extension` | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/023-browser-extension/spec.md`

## Summary

Build a privacy-first, 100% offline **Chrome/Edge & Firefox MV3 browser extension** under `integrations/browser-extension/` powered exclusively by the canonical slim Apache-2.0 `tamil-toolkit` Rust/WASM engine. The extension delivers four prioritized user journeys: (1) **Live Inline Tamil Typing** directly inside web page editors via a one-click toolbar toggle / `Alt+Shift+T` shortcut and a focus-aware Shadow DOM floating pill using a hybrid commitment model (word-boundary preview for Phonetic/Anjal; instant per-keystroke conversion for Tamil99/Bamini) plus a canvas-editor scratchpad fallback; (2) **Live Document & Selection Tamil Inspector** reporting true Tamil letter counts (எழுத்து), word counts (சொல்), script-category breakdowns, and Unicode health checks with 1-click in-place repair; (3) **In-Place Legacy Conversion, Repair & Line Sorting** across 7 legacy codecs with an Auto-detect ambiguity guard and joiner preservation; and (4) **Native Host-Browser Theming** (Chrome Refresh 2023 on Chrome/Edge; Firefox Acorn/Proton + `browser.theme` on Firefox), bilingual `தமிழ் / EN` UI, offline TN/SL numerals & active civil date/holidays, and opt-in per-site Tamil font fixing — with zero broad host permissions at install and a compressed package size under 2 MiB.

## Technical Context

**Language/Version**: TypeScript 7 (`^7.0.2`), HTML5, CSS3 (native semantic tokens + Shadow DOM), Node.js 22+ build scripts; canonical linguistic engine in Rust compiled to WebAssembly (`bindings/js-wasm`, Apache-2.0 default profile).

**Primary Dependencies**: `tamil-toolkit` (`workspace:*`, slim default-profile WASM via `wasm-pack`), `vite` (`^8.3.6`), `vite-plugin-wasm` (`^3.6.0`), `@fontsource/noto-sans-tamil`, `@fontsource/noto-sans-tamil-supplement` (bundled `.woff2` subsets only; zero runtime UI framework overhead).

**Storage**: Browser extension local storage (`storage.local`) for user preferences and opt-in per-site permission records; `storage.session` for transient per-tab typing state and single-use right-click selection handoff payloads. Zero external storage or network calls.

**Testing**: `vitest` (`^5.0.5`) executing against real compiled slim WASM (golden vectors for Phase 8 translit, 7 codecs, repair, collation, inspection, numerals, active calendar); Playwright Chromium extension smoke tests for live inline typing, Shadow DOM pill, side panel, and cold-start handoff; `web-ext lint` for Firefox MV3 validation; repo `just check-unicode` gate.

**Target Platform**: Desktop Chrome 116+, Microsoft Edge (Chromium), and Mozilla Firefox 140+ (Manifest V3 dual-target build).

**Project Type**: Dual-target browser extension workspace package (`integrations/browser-extension`) integrated into the root `pnpm` workspace.

**Performance Goals**: < 50 ms end-to-end live typing preview and word/keystroke commit (local IPC to background WASM host < 5 ms); instant side-panel open and inspection; < 25 KiB injected content script.

**Constraints**: 100% offline (zero network requests); zero broad host permissions at install (`activeTab` + opt-in single-origin permissions only); compressed ZIP < 2 MiB per browser; strict CSP (`script-src 'self' 'wasm-unsafe-eval'; object-src 'self'`); preserve `U+200D` / `U+200C` joiners by default; exclude all 13 `planned` calendar ephemeris suites and heavy lexicon packs.

**Scale/Scope**: 4 side-panel tabs (`Inspect`, `Live Type`, `Fix Text`, `Tools`) + compact Settings drawer, 1 Shadow DOM on-page floating pill, 2 browser targets (`dist/chrome`, `dist/firefox`), 3 store distribution artifacts (Chrome ZIP, Firefox ZIP, AMO reproducible source bundle).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification / Design Alignment |
| :--- | :--- | :--- |
| **I. Rust Owns Linguistic Behavior** | PASS | Zero Tamil linguistic logic is duplicated in TypeScript. All transliteration, inspection, legacy detection/conversion, repair, collation, numeral, and active calendar calls route through `bindings/js-wasm` (`createApi`) hosted in the extension background/panel context. |
| **II. Inspect Tamil by Scalars** | PASS | Inspection counts and health diagnostics are computed from scalar-accurate `tamil-core` / `tamil-norm` APIs. `U+200D` (ZWJ) and `U+200C` (ZWNJ) are preserved by default (`strip_joiners: false`). All source files remain clean UTF-8 verified by `just check-unicode`. |
| **III. Golden Vectors Precede Implementation** | PASS | Extension Vitest suites consume real compiled slim WASM and verify active golden vectors for all exposed features; no mocks and zero `planned` calendar ephemeris suites exposed. |
| **IV. Separation of Lexical Data & Engine Logic** | PASS | No lexicon tables or grammar rules are duplicated inside `integrations/browser-extension/`; all tables remain compiled inside the Rust/WASM artifact. |
| **V. Pluricentric Dialect Scope** | PASS | Numerals/currencies (`INR`/`LKR`) and official holidays explicitly support both `TN` and `SL` scopes; Unicode typing, inspection, repair, and collation are dialect-invariant. |
| **VI. Platform-Conforming Distribution & Policy** | PASS | `integrations/browser-extension` is a private workspace integration package (`"private": true`); store ZIPs are built locally for manual reviewed submission and bundle `LICENSE`, `NOTICE`, and font notices without altering `release-policy.toml` crate scope. |
| **VII. Explicit Guarantees & Quality Gates** | PASS | Package size (< 2 MiB), offline guarantee, canvas-editor fallback, and active-only calendar scope are stated honestly; `just check-unicode` and `just check-release-policy` remain green. |

**Post-Phase 1 Re-Check**: PASS — All contracts (`extension-messages.md`), data model entities (`data-model.md`), and research decisions (`research.md`) satisfy Principles I–VII with zero violations.

## Project Structure

### Documentation (this feature)

```text
specs/023-browser-extension/
├── plan.md                         # This file (/speckit-plan output)
├── research.md                     # Phase 0 architectural decisions
├── data-model.md                   # Phase 1 local storage & state entities
├── quickstart.md                   # Phase 1 validation & verification guide
├── contracts/
│   └── extension-messages.md       # Phase 1 IPC, WASM adapter & manifest contracts
├── checklists/
│   └── requirements.md             # Spec quality checklist (16/16 passing)
└── tasks.md                        # Phase 2 output (/speckit-tasks - not created here)
```

### Source Code (repository root)

```text
integrations/
├── shared/
│   └── prepare-slim-wasm.mjs       # Shared Apache-2.0 slim WASM builder extracted from office-word-addin
├── office-word-addin/
│   └── scripts/prepare-wasm.mjs    # Thin wrapper delegating to ../shared/prepare-slim-wasm.mjs
└── browser-extension/
    ├── package.json                # Added to root pnpm-workspace.yaml
    ├── tsconfig.json
    ├── vite.config.ts              # Multi-entry build (background, content, panel, offscreen)
    ├── scripts/
    │   ├── build-manifests.mjs     # Emits dist/chrome/manifest.json & dist/firefox/manifest.json
    │   └── package-zips.mjs        # Builds Chrome ZIP, Firefox ZIP & AMO reproducible source bundle
    ├── src/
    │   ├── engine/
    │   │   ├── tamil-engine.ts     # Lazy slim-WASM loader + typed adapters (translit, inspect, fix, tools)
    │   │   └── inspect.ts          # InspectionSnapshot builder using tamil-core & tamil-norm
    │   ├── shared/
    │   │   ├── browser-api.ts      # Thin Chrome/Firefox MV3 compatibility shim
    │   │   ├── messages.ts         # Discriminated-union IPC message types
    │   │   ├── storage.ts          # Typed UserPreferences, PerSitePermissionRecord & Handoff store
    │   │   ├── i18n.ts             # Bilingual Tamil/English strings & locale auto-detect
    │   │   └── theme/
    │   │       ├── base.css        # Shared semantic layout & component styles
    │   │       ├── chrome-tokens.css   # Chrome Refresh 2023 Light/Dark native tokens
    │   │       └── firefox-tokens.css  # Firefox Acorn/Proton Light/Dark tokens + theme sync
    │   ├── background/
    │   │   ├── index.ts            # Toolbar toggle, Alt+Shift+T, context menus, WASM RPC host, site permissions
    │   │   └── font-fixer.ts       # Per-site opt-in Noto Tamil + Tamil Supplement CSS injection/revocation
    │   ├── offscreen/
    │   │   ├── offscreen.html      # Chrome-only silent clipboard copy host
    │   │   └── offscreen.ts
    │   ├── content/
    │   │   ├── index.ts            # Content script entry, focus tracking, message handler
    │   │   ├── live-typing.ts      # Hybrid inline typing (Phonetic/Anjal word-boundary; Tamil99/Bamini instant)
    │   │   ├── editor-adapter.ts   # Safe input/textarea/contenteditable replacement, sensitive-field guard, canvas detect
    │   │   └── floating-pill.ts    # Focus-aware Shadow DOM floating pill + canvas Quick-Compose scratchpad
    │   ├── panel/
    │   │   ├── panel.html
    │   │   ├── main.ts             # Side Panel / Sidebar shell, native theme init, bilingual toggle, Settings drawer
    │   │   └── tabs/
    │   │       ├── inspect-tab.ts  # Live Document & Selection Inspector + 1-click Repair in place
    │   │       ├── live-tab.ts     # Live typing toggle, per-site Always-on toggle, standalone composer
    │   │       ├── fix-tab.ts      # 7 legacy codecs + Auto ambiguity guard, Repair, Agara/Uyirmei sort
    │   │       └── tools-tab.ts    # TN/SL numerals & INR/LKR currency, active civil date/holidays, font fixer
    │   └── assets/
    │       ├── icons/              # Native-clean extension toolbar icons (16/32/48/128)
    │       └── fonts/              # Subsetted Noto Sans Tamil + Tamil Supplement .woff2 files
    └── tests/
        ├── engine.test.ts          # Vitest against real slim WASM (translit, inspect, codecs, repair, sort, numerals, calendar)
        ├── live-typing.test.ts     # Hybrid commitment, Escape bypass, sensitive-field guard, editor adapter tests
        ├── manifests.test.ts       # Dual-browser MV3 manifest & permission invariants
        └── e2e/
            └── extension.spec.ts   # Playwright Chromium smoke tests (live typing, pill, panel, handoff)
```

**Structure Decision**: Place the browser extension as a sibling integration package at `integrations/browser-extension/` alongside `integrations/office-word-addin/`, extracting only the slim WASM build script into `integrations/shared/prepare-slim-wasm.mjs` so both integrations stay cleanly decoupled while sharing the exact Apache-2.0 WASM pipeline.

## Complexity Tracking

No Constitution Check violations. Zero complexity exceptions required.
