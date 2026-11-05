# Research & Technical Decisions: Interactive Playground (`playground`)

**Feature**: `005-playground` | **Date**: 2026-11-05

## Summary of Decisions

This document details the architectural investigations, design choices, and technical trade-offs for the `tamil-toolkit` interactive public and developer playground.

---

## 1. Bundler & Application Framework

### Decision
Use **Vite 8** (`8.3.6`) with **React 19** (`19.3.1`) and **TypeScript 7** (`7.0.2`) as a static Single-Page Application (SPA).

### Rationale
- **WebAssembly Compatibility**: Vite provides first-class support for loading `.wasm` binaries via native ESM and `vite-plugin-wasm` / `vite-plugin-top-level-await`, completely bypassing the complex SSR hydration workarounds and Node.js server mocking required by Next.js.
- **Resource Footprint**: The production build produces pure static assets (`dist/`) with an initial gzipped JavaScript footprint well under 180 KB (excluding the compiled WASM module). Next.js carries server runtimes and substantial framework hydration code.
- **Developer Velocity**: Vite's native ES module Hot Module Replacement (HMR) reloads in < 50ms, allowing instantaneous UI tweaks and live feedback when updating Rust WASM bindings in the monorepo workspace.
- **Deployment Simplicity**: The static output can be deployed effortlessly to GitHub Pages, Cloudflare Pages, Vercel, or any static object storage without any backend server cost or management.

### Alternatives Considered
- **Next.js (App Router / SSR)**: Rejected. Next.js excels when applications require dynamic server-side rendering, databases, or API routes. Here, the project constitution mandates 100% client-side privacy with zero server telemetry. Running Next.js solely in `output: 'export'` mode introduces unnecessary build tooling complexity, larger bundle sizes, and brittle WebAssembly packaging compared to Vite.
- **Astro**: Evaluated. Astro is excellent for content-heavy sites with isolated islands, but the playground is an interactive application where nearly every view requires shared reactive state, live input synchronization, and immediate WASM execution.
- **Vanilla TypeScript**: Rejected for the UI layer. While lightweight, managing multi-step reactive UI state, accessible tab panels, dialogs, toasts, and mobile layouts without a component model would lead to high code complexity and slower iteration.

---

## 2. UI Component System & Mobile Touch Ergonomics

### Decision
Use **Tailwind CSS** with **shadcn/ui** patterns (built on unstyled **Radix UI** primitives) and **Lucide React** icons.

### Rationale
- **Zero-Friction Mobile Ergonomics**: Radix UI primitives provide fully accessible (WAI-ARIA compliant) keyboard and touch behaviors. shadcn/ui components are copied directly into the project source tree (`playground/src/components/ui`), allowing complete custom styling and zero third-party component lock-in.
- **One-Tap Actions**:
  - Sticky bottom action bar on mobile viewports (< 768px) housing the primary Copy, Clear, and Swap buttons within thumb reach.
  - Horizontal chip selectors for legacy encoding overrides that do not require opening nested modal menus.
  - Floating toast notifications for non-blocking feedback upon clipboard copy.
- **Styling Efficiency**: Tailwind CSS eliminates runtime CSS overhead and produces an optimized, purged stylesheet (< 25 KB).

### Alternatives Considered
- **Material UI (MUI) / Ant Design**: Rejected due to heavy runtime emotion/CSS-in-JS bundle overhead (> 300 KB) and desktop-centric default ergonomics.
- **Custom Hand-Crafted CSS**: Rejected due to accessibility maintenance burden (managing ARIA focus rings, dialog traps, and touch targets manually).

---

## 3. Real-Time Conversion & Execution Concurrency

### Decision
Implement a **dual-tier execution model**:
1. **Direct Main-Thread Execution** for standard text inputs (< 10 KB), debounced at 50ms.
2. **Dedicated Web Worker** for large batch inputs (> 100 KB) and multi-file conversions.

### Rationale
- Sub-50ms latency: Rust WASM execution for typical paragraphs and numeral formatting takes < 2ms in the browser. Running these directly on the main thread avoids the serialization overhead of worker message passing, delivering true instantaneous real-time typing feedback.
- Thread Safety & 60 FPS UI: When users drop large text files (e.g. 500 KB–5 MB archives) into the converter, delegating execution to `playground.worker.ts` guarantees that typing, scrolling, and tab animations remain buttery smooth without main-thread blocking.

### Alternatives Considered
- **Worker-Only for All Operations**: Rejected for keystroke typing because `postMessage` serialization adds ~5–10ms overhead and asynchronous state coordination for single character inputs.
- **Main-Thread Only**: Rejected because large text buffers (> 1 MB) could cause perceptible UI stuttering during heavy encoding conversion.

---

## 4. Multi-Language Code Snippet Generation

### Decision
Implement a pure, client-side declarative snippet generator template engine for all four supported runtimes:
- **Rust** (direct crate imports from `tamil-*` and `tamil-toolkit`)
- **Python** (`import tamil_toolkit`)
- **TypeScript / JavaScript** (`import { ... } from "tamil-toolkit"`)
- **Dart** (`import 'package:tamil_toolkit/tamil_toolkit.dart'`)

### Rationale
- Provides immediate utility for developers inspecting any operation in the sandbox.
- Snippets reflect the exact inputs, parameters, and flags configured in the active UI, with one-click copy and language switching.

---

## 5. Offline Capabilities & PWA Strategy

### Decision
Integrate **Vite PWA Plugin (`vite-plugin-pwa`)** using standard Service Worker caching (CacheFirst strategy for WASM binary and static assets).

### Rationale
- Once visited, the playground operates completely offline without internet connectivity.
- Complies with Constitution Principle VII (Explicit Guarantees & Rigorous Quality Gates) and guarantees 100% data confidentiality.
