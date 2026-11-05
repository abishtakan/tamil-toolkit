# Implementation Plan: Unslop UI Design & De-AI-ification

**Branch**: `007-unslop-ui-design` | **Date**: 2026-11-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-unslop-ui-design/spec.md`

## Summary

Purge generic AI-generated design artifacts from the Tamil Toolkit Playground and implement an authentic, asymmetric linguistic workbench based on empirical unslop UI heuristics:
1. Replace repetitive uniform 4-card grids and floating gradient marketing heroes with an authentic asymmetric Bento workbench.
2. Remove all `scale-105` hover distortions and sliding arrow gimmicks in favor of crisp 1px hairline border transitions (120ms) and tactile active states (`active:scale-[0.99]`).
3. Replace generic AI SaaS buzzwords in dictionaries with precise, utilitarian linguistic terminology.
4. Consolidate developer utilities into a high-density diagnostic console.

## Technical Context

**Language/Version**: TypeScript 5.8+, React 19, Vite 8, Tailwind CSS v4
**Primary Dependencies**: React 19, `@tamil-toolkit/wasm`, Lucide React
**Testing**: Vitest (`pnpm --filter tamil-toolkit-playground test`), `tsc -b`
**Target Platform**: Modern Web Browsers (WASM + ES2022)
**Project Type**: Client-Side Web Application
**Performance Goals**: < 120ms transition latency, zero layout shift (CLS = 0)
**Constraints**: 100% client-side execution, WCAG AA contrast (minimum 4.5:1)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Rust Owns Linguistic Behavior**: All UI transformations remain presentation layer; WebAssembly engine calls remain authoritative.
- [x] **Principle II: Inspect Tamil by Scalars**: Unicode scalar inspection and display integrity preserved without distortion.
- [x] **Principle VII: Explicit Guarantees & Rigorous Quality Gates**: `just agent-post-edit` and `pnpm test` must pass cleanly.

## Project Structure

### Documentation (this feature)

```text
specs/007-unslop-ui-design/
├── spec.md               # Feature specification
├── plan.md               # This plan
├── research.md           # Research into AI slop tells & unslop heuristics
├── data-model.md         # Component hierarchy and layout structure
├── quickstart.md         # Visual and automated verification guide
├── contracts/
│   └── unslop-ui-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md              # Actionable tasks
```

### Source Code Impact

```text
playground/
├── src/
│   ├── lib/
│   │   └── i18n.ts                    # Refined copy removing AI marketing buzzwords
│   ├── App.tsx                        # Clean header without scale-105; tactile nav tabs
│   ├── components/
│   │   ├── common/
│   │   │   └── OverviewHub.tsx        # Asymmetric Bento workbench & diagnostic console
│   │   ├── public-tools/
│   │   │   └── *.tsx                  # Removal of scale-105 & bouncy hover physics
│   │   └── developer-tools/
│   │       └── *.tsx                  # Compact, tactile diagnostic layout
│   └── tests/
│       └── i18n.test.ts               # Verification of refined unslop dictionary
```
