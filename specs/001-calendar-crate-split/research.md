# Research: Calendar Crate Split

**Feature**: `specs/001-calendar-crate-split`

## Decisions & Technical Rationale

### 1. Crate Architecture & Workspace Setup
- **Decision**: Create `crates/tamil-calendar` as a standalone member of the Cargo workspace.
- **Rationale**:
  - `tamil-numerals` is approved and published on crates.io/PyPI/npm with 35,646 active golden vectors. It must not carry unapproved, experimental calendar algorithms.
  - The calendar module incorporates complex astronomical formulas, large ephemeris tables (e.g. `drik.rs` is ~156 KB), and the `astro = "=2.0.0"` dependency.
  - Decoupling calendar logic leaves `tamil-numerals` free of `astro` and astronomical code.
- **Alternatives Considered**:
  - *Keep calendar under `tamil-numerals` behind a feature flag (e.g. `features = ["calendar"]`)*: Rejected because the project constitution principles require clear library boundaries, and release-policy governs entire crates. Feature flags would still bind numeral release versions to calendar readiness.

### 2. Dependency Graph
- **Decision**:
  - `tamil-calendar` depends on `tamil-core` (for scalar/grapheme handling) and `tamil-numerals` (for formatting Tamil calendar dates using Tamil digits/words/fractions where required).
  - `tamil-numerals` drops its `calendar` submodule and its `astro = "=2.0.0"` dependency entirely.
  - `tamil-toolkit` (the unified facade/dispatcher) depends on both `tamil-numerals` and `tamil-calendar`.
- **Alternatives Considered**:
  - *Make `tamil-calendar` completely independent of `tamil-numerals`*: Formatting dates with Tamil numerals or traditional number representations would require duplicated logic or raw numeric representations. Depending on `tamil-numerals` preserves single-source-of-truth invariants.

### 3. Release Policy & Registry Publication
- **Decision**: Exclude `tamil-calendar` from `release-policy.toml` `public_crates` list initially.
- **Rationale**: The user clarified that `tamil-calendar` should remain an internal/experimental crate until its golden suites (225+ vectors across 17 files) are formally activated and pass release review. `tamil-numerals` remains in `public_crates`.
- **Alternatives Considered**:
  - *Add `tamil-calendar` to `public_crates` immediately*: Rejected by user decision; calendar is experimental and suites are planned.

### 4. High-Level Language Bindings (Python, WASM, Dart)
- **Decision**: Group calendar operations under a dedicated sub-namespace in language bindings:
  - Python: `tamil_toolkit.calendar` submodule or namespace object.
  - WebAssembly: `calendar` property on the exported toolkit API object.
  - Dart: `TamilCalendar` class or `calendar` namespace.
- **Rationale**: Keeps language APIs structured and modular without polluting root namespaces, matching the user's explicit preference.

### 5. Developer Workbench Presentation
- **Decision**: Add `tamil-calendar` as an active/experimental package card on the workbench grid. Expose calendar operations (e.g., `gregorian_to_tamil_date`, `tamil_to_gregorian_date`, `panchangam_at`, `calendar_observances`, `compare_calendar_profiles`) in its dedicated operation selector.
- **Rationale**: Maintains the workbench's manual testing utility while accurately reflecting the new crate boundary.
