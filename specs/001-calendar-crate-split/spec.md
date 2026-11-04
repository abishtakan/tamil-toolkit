# Feature Specification: Calendar Crate Split

**Feature Directory**: `specs/001-calendar-crate-split`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "calendar-crate-split. since there are no users of this crates we doesn't mention deprecations."

## Clarifications

### Session 2026-11-05
- Q: How should the new `tamil-calendar` crate be handled in `release-policy.toml`? → A: Excluded from `release-policy.toml` initially, retaining status as an internal/experimental workspace crate until calendar suites are activated.
- Q: How should calendar operations be exposed in high-level language bindings (Python / WASM / Dart)? → A: Organized under dedicated sub-namespaces (e.g. `tamil_toolkit.calendar` in Python, `calendar` object export in WASM/TypeScript, `Calendar` class/namespace in Dart).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dedicated Calendar Engine Discovery & Consumption (Priority: P1)

As a developer building Tamil calendar, almanac, or panchangam applications, I want a dedicated package focused strictly on Tamil calendar systems (solar calculations, Thirukanitham, Vakiya, five limbs, holidays, and observances) without coupling to general number formatting or currency logic, so that I can consume calendar features with minimal compilation overhead and clear API boundaries.

**Why this priority**: Calendar calculations represent a distinct domain with substantial astronomical formulas and tables. Decoupling calendar logic establishes clean modularity in accordance with the project constitution.

**Independent Test**: Can be independently verified by consuming the standalone calendar package directly, executing all solar date conversions, panchangam evaluations, and observance calculations without any reference to numeral modules.

**Acceptance Scenarios**:
1. **Given** a consumer requesting calendar functions (e.g. Gregorian-to-Tamil solar date conversion or panchangam calculation), **When** they import the dedicated calendar module, **Then** all calendar operations execute successfully and return verified astronomical outputs.
2. **Given** a consumer utilizing the calendar module, **When** they inspect the package interfaces, **Then** all calendar-specific structures and operations are exposed cleanly under the calendar namespace.

---

### User Story 2 - Lightweight Numerals Package Focused on Numbers & Currency (Priority: P2)

As a developer requiring Tamil number words, decimal formatting, traditional integer numerals, fractions, or currency formatting (INR/LKR), I want the numerals package to contain only numeric and currency logic, so that my applications do not pull in heavy astronomical ephemeris and calendar tables.

**Why this priority**: Numeral operations are stable, fully verified (35,646 active golden vectors), and widely applicable in UI/localization. Purging experimental calendar code from numerals prevents regressions in stable numeric releases.

**Independent Test**: Can be verified by building and testing the numerals module; it must compile strictly numeric features and retain 100% pass rates across all active numeral golden test suites.

**Acceptance Scenarios**:
1. **Given** a consumer importing the numerals package, **When** they format currency or numbers, **Then** all numeral operations succeed without any calendar dependencies.
2. **Given** the numerals package, **When** checking its exposed exports, **Then** no calendar types or functions are present.

---

### User Story 3 - Unified Multi-Runtime Access via Umbrella Toolkit (Priority: P3)

As a consumer accessing the toolkit through multi-language bindings (Python, WebAssembly, Dart) or developer workbenches, I want the top-level toolkit to provide both numerals and calendar operations through structured sub-namespaces, so that multi-runtime usage is cleanly organized and intuitive.

**Why this priority**: Preserves a structured, modular developer experience in high-level language wrappers and the interactive developer workbench.

**Independent Test**: Can be verified by running the full parity test suite and the interactive workbench, verifying that both numeral and calendar queries are routed and served accurately under their respective namespaces.

**Acceptance Scenarios**:
1. **Given** a query issued to the shared dispatcher for a calendar operation, **When** executed via Python (`tamil_toolkit.calendar`), WASM (`calendar` export), or Dart wrappers, **Then** the request delegates to the new calendar engine and produces identical results.
2. **Given** the developer workbench, **When** inspecting available modules, **Then** calendar and numerals are presented as independent domains with dedicated controls.

---

### Edge Cases

- What happens to calendar test fixtures currently recorded in the golden test manifest?
  - All 17 calendar suites (covering solar arithmetic, Thirukanitham, Vakiya, panchangam, daylight periods, and observances) must be reassigned directly to the new `tamil-calendar` package in the test inventory.
- What happens if an external or historical request asks for calendar operations on the numerals package?
  - Because there are no external consumers of the pre-release calendar API on the numerals package, no deprecation shims or warnings are retained. Requests for calendar functions on the numerals package are cleanly unsupported.
- What happens during release packaging and publishing checks?
  - The `tamil-calendar` crate remains excluded from `release-policy.toml` and does not block or participate in public package publication until its suites are activated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A standalone calendar engine MUST be established as an independent package (`tamil-calendar`) within the repository workspace.
- **FR-002**: All calendar-related logic—including Thirukanitham (Drik), Vakiya (Vakya) solar/civil models, five panchangam limbs, daylight periods, official holidays, and festival observances—MUST reside entirely within the calendar package.
- **FR-003**: All calendar types, structures, and functions MUST be cleanly removed from the numerals package (`tamil-numerals`), leaving it dedicated exclusively to numbers, fractions, decimals, and currencies.
- **FR-004**: No backward-compatibility shims, aliases, or deprecation warnings for calendar symbols MUST be retained in the numerals package.
- **FR-005**: High-level language wrappers (Python, WASM/TypeScript, Dart) MUST expose calendar operations under dedicated sub-namespaces (e.g. `tamil_toolkit.calendar` in Python, `calendar` object in WASM) while sharing the common Rust dispatcher.
- **FR-006**: The new `tamil-calendar` crate MUST remain excluded from `release-policy.toml` as an internal/experimental crate, preserving `tamil-numerals`' existing approved public release status.
- **FR-007**: The golden test manifest MUST assign all calendar suites and vectors directly to the `tamil-calendar` package.
- **FR-008**: The developer workbench MUST present the calendar package as its own distinct domain with corresponding operation panels.

### Key Entities

- **Calendar Package (`tamil-calendar`)**: Standalone engine responsible for Tamil timekeeping, astronomical algorithms, and observance calculations; initially internal/experimental.
- **Numerals Package (`tamil-numerals`)**: Focused, public-approved engine responsible for numeric parsing, formatting, number words, and monetary representations.
- **Shared Dispatcher**: Centralized dispatch interface routing requests across core packages to multi-runtime adapters.
- **Language Binding Sub-namespaces**: Module boundaries in target language runtimes (`tamil_toolkit.calendar`, `calendar` WASM export, etc.).
- **Golden Test Manifest**: Central registry defining test suites, active/planned statuses, and package ownership.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Clean separation of source directories with zero calendar code remaining in the numerals source tree.
- **SC-002**: 100% of existing active numeral golden tests (35,646 vectors) continue to pass without modification.
- **SC-003**: 100% of calendar test suites (all 17 planned suites) are mapped to the new calendar package and execute cleanly in test runs.
- **SC-004**: The numerals package compilation time and binary footprint are measurably reduced by offloading astronomical calculation logic.
- **SC-005**: All quality gates and multi-runtime parity checks execute successfully across Rust, Python, WASM, and Dart.
- **SC-006**: Release policy checks (`just check-release-policy`) pass cleanly without requiring premature publication of `tamil-calendar`.

## Assumptions

- No external production systems or public consumers depend on calendar exports residing inside the numerals package, allowing immediate clean separation without transitional deprecation periods.
- The calendar engine may depend on core primitives (`tamil-core`) and, where necessary for formatted date strings with Tamil digits or traditional numerals, on `tamil-numerals`.
- Calendar status remains bounded/experimental under the project's release policy while numerals remains an approved public crate.
