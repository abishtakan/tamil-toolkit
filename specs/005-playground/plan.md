# Implementation Plan: Interactive Public & Developer Playground (`playground`)

**Branch**: `005-playground` | **Date**: 2026-11-05 | **Spec**: [specs/005-playground/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/005-playground/spec.md)

**Input**: Feature specification from `specs/005-playground/spec.md`

## Summary

Build a high-performance, mobile-first, zero-friction web playground providing everyday public tools (legacy font converter, numeral/currency to Tamil words, calendar/panchangam explorer, text sorter) and developer diagnostic tools (Unicode scalar inspector, raw dispatcher sandbox, multi-language code generator, batch file processor). The application runs 100% client-side via the compiled `tamil-toolkit` WebAssembly engine, guaranteeing complete privacy, zero server dependency, and full offline capability.

## Technical Context

**Language/Version**: TypeScript 7.0+ (`7.0.2`) / Node.js 22+ (WebAssembly runtime powered by Rust MSRV 1.85+)

**Primary Dependencies**: Vite 8 (`8.3.6`), React 19 (`19.3.1`), Tailwind CSS v4 (`4.3.4`), Radix UI primitives (`@radix-ui/react-tabs@1.2.1`, `@radix-ui/react-toast@1.3.1`), Lucide React (`1.69.0`), `vite-plugin-pwa` (`2.0.0`), `vite-plugin-wasm` (`3.6.0`)

**Internal Dependency**: `tamil-toolkit/web` (via monorepo workspace `workspace:*`)

**Storage**: Browser LocalStorage / IndexedDB (for user preference persistence only, no server storage)

**Testing**: Vitest, Playwright (for mobile/desktop visual and interaction end-to-end tests)

**Target Platform**: Modern Web Browsers (Mobile and Desktop, Chrome/Safari/Firefox/Edge, offline PWA)

**Project Type**: Web Application (Static Single Page Application, zero backend)

**Performance Goals**: Sub-30ms conversion latency on standard text; 60 fps smooth typing feedback on mobile; initial bundle < 250 KB gzipped

**Constraints**: 100% client-side execution; zero network requests with user data; full offline operation; minimum 44×44px touch targets; zero-click live conversion

**Scale/Scope**: 4 Public Tools, 4 Developer Tools, 1 shared Web Worker, full mobile and desktop responsiveness

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Plan Conformance | Status |
| :--- | :--- | :--- | :---: |
| **I. Rust Owns Linguistic Behavior** | All core algorithms, collation, and conversions MUST reside in Rust. Adapters MUST NOT duplicate logic. | Playground imports `tamil-toolkit/web` compiled from Rust. The UI layer contains zero custom Tamil linguistic or orthographic logic. | **PASS** |
| **II. Inspect Tamil by Scalars** | No visual layout guessing; codepoints inspected by scalars; invisible controls preserved. | Developer scalar inspector renders exact Unicode hexadecimal escapes (`\u{0B85}`) and flags ZWJ (`\u{200D}`) and ZWNJ (`\u{200C}`). | **PASS** |
| **III. Golden Vectors Precede Implementation** | Behavior defined by sourced golden vectors; tri-runtime parity maintained. | Playground test suites validate conversion behaviors directly against golden fixtures from `tests/golden/`. | **PASS** |
| **IV. Separation of Lexical Data & Logic** | Lexical data kept declarative in TOML/CSV; no hallucinated rules. | All calendar, numeral, and encoding tables remain inside Rust crates; playground consumes compiled tables via WASM. | **PASS** |
| **V. Pluricentric Dialect Scope** | Regional varieties (TN and SL) explicitly declared. | Public tools provide clear region selectors (Tamil Nadu vs. Sri Lanka) for calendar observances and currency conventions. | **PASS** |
| **VI. Platform-Conforming Distribution** | Native package conventions; policy-governed releases. | Playground resides in `playground/`, managed via `pnpm-workspace.yaml`, building to static assets for deployment. | **PASS** |
| **VII. Explicit Guarantees & Quality Gates** | Verified performance, memory guarantees, and strict gates. | 100% client-side privacy verified by zero-network test suite; sub-30ms latency benchmarks; mobile responsive audit. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/005-playground/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Phase 0: Technology, bundler, and UX research
├── data-model.md        # Phase 1: Entity definitions and domain models
├── design-standard.md   # UI/UX design standard, color tokens & mobile ergonomics
├── quickstart.md        # Phase 1: Local development and verification guide
├── contracts/           # Phase 1: Interface and Web Worker contracts
│   └── playground-api-contract.md
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Phase 2: Actionable task list (created by /speckit-tasks)
```

### Source Code Layout

```text
playground/
├── index.html                  # HTML entry point with mobile viewport & theme meta
├── package.json                # Playground workspace package config
├── tsconfig.json               # TypeScript configuration
├── vite.config.ts              # Vite 8 config with WASM and PWA plugins
├── public/                     # Static assets, icons, manifest.json
│   ├── favicon.svg
│   └── pwa-icon-512.png
├── src/
│   ├── main.tsx                # Application bootstrap & React root
│   ├── App.tsx                 # Top-level shell with mobile navigation & bottom bar
│   ├── index.css               # Tailwind CSS imports & theme variables
│   ├── lib/
│   │   ├── engine.ts           # Tamil-toolkit WASM wrapper & lifecycle manager
│   │   ├── utils.ts            # Class name helpers and string formatters
│   │   └── worker-client.ts    # Web Worker RPC client for batch conversions
│   ├── workers/
│   │   └── playground.worker.ts # Background Web Worker for batch tasks
│   ├── components/
│   │   ├── ui/                 # Accessible Radix UI / shadcn component primitives
│   │   │   ├── button.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── toast.tsx
│   │   │   ├── badge.tsx
│   │   │   └── card.tsx
│   │   ├── common/             # Shared ergonomic components
│   │   │   ├── StickyActionBar.tsx  # Mobile thumb-zone (Copy, Clear, Swap)
│   │   │   ├── CopyButton.tsx       # 1-tap copy with toast feedback
│   │   │   └── CodeBlock.tsx        # Syntax-highlighted snippet viewer
│   │   ├── public-tools/       # Public Tools implementations
│   │   │   ├── CodecConverter.tsx   # Real-time legacy font converter
│   │   │   ├── NumeralFormatter.tsx # Number to words and currency
│   │   │   ├── CalendarExplorer.tsx # Tamil calendar and panchangam
│   │   │   └── TextSorter.tsx       # Agara varisai collation tool
│   │   └── developer-tools/    # Developer Tools implementations
│   │       ├── ScalarInspector.tsx  # Unicode codepoints & cluster visualizer
│   │       ├── DispatcherSandbox.tsx# Raw JSON dispatcher console
│   │       ├── CodeGenerator.tsx    # Rust / Python / TS / Dart snippet export
│   │       └── BatchProcessor.tsx   # Multi-file drag-and-drop converter
│   └── tests/
│       ├── codec-converter.test.tsx
│       ├── numeral-formatter.test.tsx
│       └── mobile-ergonomics.test.tsx
```

**Structure Decision**: A dedicated `playground/` workspace package integrated directly into `pnpm-workspace.yaml`. It consumes the compiled `tamil-toolkit` browser WASM bundle through local package linking, guaranteeing exact parity with the published npm package.

## Complexity Tracking

| Dimension | Strategy | Justification |
| :--- | :--- | :--- |
| **No Server Backend** | 100% Client-side WASM | Eliminates server infrastructure, hosting costs, and privacy concerns. Guaranteed zero data retention. |
| **Web Worker Offloading** | Dedicated Worker for > 100 KB inputs | Preserves 60 fps main-thread typing smoothness on budget mobile devices during large document conversions. |
| **Vite over Next.js** | Static Vite SPA | Eliminates SSR complexity and WASM bundling workarounds; cuts build times and bundle sizes in half. |
