# Implementation Plan: Calendar Crate Split

**Branch**: `001-calendar-crate-split` | **Date**: 2026-11-05 | **Spec**: [specs/001-calendar-crate-split/spec.md](spec.md)

**Input**: Feature specification from `/specs/001-calendar-crate-split/spec.md`

## Summary

Extract all astronomical and almanac calculations (Thirukanitham Drik, Vakiya, panchangam limbs, daylight periods, official holidays, observances) out of `crates/tamil-numerals` into a dedicated workspace crate `crates/tamil-calendar`. `tamil-numerals` will focus purely on number words, decimals, fractions, and currency. The unified dispatcher (`crates/tamil-toolkit`) and high-level language bindings (Python, WASM, Dart) will expose calendar operations under dedicated sub-namespaces.

## Technical Context

**Language/Version**: Rust 1.85 (MSRV), TypeScript 7.0.2 / Vite 8.3.5, Python 3.11+, Dart 3.x
**Primary Dependencies**: `tamil-core`, `tamil-numerals`, `astro = "=2.0.0"` (moved to `tamil-calendar`), PyO3, `wasm-bindgen`
**Storage**: N/A (declarative TOML / static Rust data)
**Testing**: `cargo test`, `just test-parity`, `just agent-pre-stop-gate`, `pnpm run check:workbench`
**Target Platform**: Native OS (Linux/Windows/macOS), WebAssembly (Node & Browser), Python wheels, Flutter/Dart
**Project Type**: Multi-crate Rust workspace with multi-runtime FFI wrappers
**Performance Goals**: Zero allocation for borrowed iteration; minimal binary footprint for `tamil-numerals`
**Constraints**: Pure scalar inspection (no visual guesses), zero calendar code left in numerals, no deprecation shims
**Scale/Scope**: 1 new crate, 1 modified crate (`tamil-numerals`), 1 modified facade (`tamil-toolkit`), 17 planned test suites reassigned

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Rust Owns Linguistic Behavior**: PASS. The new `crates/tamil-calendar` owns all calendar computation; Python/WASM/Dart are thin serialization wrappers.
- **Principle II: Inspect Tamil by Scalars**: PASS. All Tamil month and day names continue using explicit scalars.
- **Principle III: Golden Vectors Precede Implementation**: PASS. All 17 planned calendar suites are cleanly reassigned to `tamil-calendar` in `tests/golden/manifest.json`.
- **Principle IV: Separation of Lexical Data**: PASS. Calendar display names and holiday tables remain declarative.
- **Principle V: Pluricentric Dialect Scope**: PASS. TN and SL calendar profiles and holidays remain distinct.
- **Principle VI: Platform Naming & Policy**: PASS. `tamil-calendar` is initially excluded from `release-policy.toml`, preserving approved public release gates.
- **Principle VII: Explicit Guarantees & Rigorous Quality Gates**: PASS. All verification gates (`just check-release-policy`, `just test-parity`, `just agent-pre-stop-gate`) must pass.

## Project Structure

### Documentation (this feature)

```text
specs/001-calendar-crate-split/
├── plan.md              # This file
├── research.md          # Phase 0 architectural decisions
├── data-model.md        # Phase 1 domain entities and crate boundaries
├── quickstart.md        # Phase 1 runnable validation scenarios
├── contracts/
│   └── contracts.md     # Phase 1 public API contracts (Rust, Python, WASM, Dart)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code Layout

```text
crates/
├── tamil-core/               # Core Unicode primitives
├── tamil-numerals/           # Numbers, decimals, fractions, LKR/INR currency (calendar removed)
├── tamil-calendar/           # [NEW] Standalone calendar engine
│   ├── Cargo.toml            # Holds astro = "=2.0.0" and workspace dependencies
│   └── src/
│       ├── lib.rs            # Re-exports calendar modules
│       ├── display.rs        # Tamil & Romanized date display formatting
│       ├── drik.rs           # Thirukanitham ephemeris calculations & panchangam
│       ├── holidays.rs       # TN & SL official holiday schedules
│       ├── observances.rs    # Festival & vrata selectors
│       ├── solar_arithmetic.rs # Solar date math & year cycles
│       ├── vakya.rs          # Vakiya astronomical reductions
│       └── vakya_civil.rs    # Vakiya civil calendar profile
├── tamil-toolkit/            # Top-level dispatcher re-exporting calendar and numerals
bindings/
├── python/                   # Exposes tamil_toolkit.calendar
├── js-wasm/                  # Exposes api.calendar
└── dart-flutter/             # Exposes TamilCalendar
workbench/
├── index.html                # Adds tamil-calendar package card
└── main.ts                   # Updates package list and operation mappings
```

## Structure Decision

Split the existing monolithic `crates/tamil-numerals/src/calendar/` hierarchy into its own workspace crate `crates/tamil-calendar`. Update the top-level dispatcher in `crates/tamil-toolkit/src/lib.rs` and `calendar_features.rs` to consume `tamil-calendar` instead of `tamil-numerals::calendar`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New workspace crate (`tamil-calendar`) | Clean separation of concerns between stable numerals and experimental calendar systems | Retaining calendar in `tamil-numerals` couples 156KB+ of astronomical math and `astro` dependency to lightweight number formatting |
