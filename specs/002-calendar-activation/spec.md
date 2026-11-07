# Feature Specification: Calendar Suite Activation

**Feature Directory**: `specs/002-calendar-activation`

**Created**: 2026-11-05

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "Specification for reviewing, validating, and activating the planned golden test suites in tamil-calendar."

## Clarifications

### Session 2026-11-05
- Q: What order should calendar suites be reviewed and activated in?
  → A: Three distinct priority phases:
    1. **Priority 1 (MVP)**: 4 tabular, metadata, and display suites (`calendar_year_cycle`, `calendar_thiruvalluvar_year`, `calendar_official_holidays`, `calendar_tamil_display`). These rely on stable chronological and statutory tables and already pass all vectors.
    2. **Priority 2**: 10 astronomical, ephemeris, and solar/lunar transit suites (`calendar_solar_arithmetic`, `calendar_lunar_phases`, `calendar_daylight_periods`, `calendar_vakya_solar`, `calendar_vakya_moon`, `calendar_vakya_civil`, `calendar_vakya_local_sunrise`, `calendar_vakya_cara`, `calendar_vakya_desantara`, `calendar_vakya_bhujaantara`).
    3. **Priority 3**: Observance selectors and multi-profile comparative analysis (`calendar_observances`, `calendar_thirukanitham`, `calendar_profile_comparison`), formalizing community variations and date attribution bounds.
- Q: How does suite activation affect `release-policy.toml`?
  → A: Suite activation is a prerequisite for moving `tamil-calendar` from experimental to public release. The crate remains internal during P1 and P2 activation; once all suites are active and reviewed, a separate release policy gate will be submitted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Activate Tabular, Civil Display, & Statutory Calendar Suites (Priority: P1) 🎯 MVP

As an application developer using `tamil-toolkit`, I want access to verified, active golden test suites for 60-year cycle titles, the official Thiruvalluvar era, public holiday calendars, and Tamil date display formatting so that I can rely on certified cross-runtime parity for common civil calendar features without waiting for the full ephemeris verification.

**Why this priority**: These 4 suites cover 100% of standard Tamil civil calendar UI needs (date formatting, year names, gazetted holidays). The underlying logic is already fully implemented, deterministic, and passes in Rust, Python, and WASM.

**Independent Test**: Can be independently verified by switching status from `planned` to `active` in `tests/golden/manifest.json` for:
- `calendar_year_cycle.jsonl`
- `calendar_thiruvalluvar_year.jsonl`
- `calendar_official_holidays.jsonl`
- `calendar_tamil_display.jsonl`
and confirming `just test-parity` passes with all vectors active.

**Acceptance Scenarios**:
1. **Given** a query for Tamil 60-year cyclic names (`tamil_year_cycle_info`), **When** executed across Rust, Python, WASM, and Dart, **Then** all 1889/1941 historical cyclic anchors return identical Roman and Tamil titles.
2. **Given** a valid solar date, **When** calculating Thiruvalluvar year via `thiruvalluvar_year_info`, **Then** the TN Thai-1 convention resolves consistently across all runtimes.
3. **Given** a gazetted holiday query for Tamil Nadu or Sri Lanka (`calendar_official_holidays`), **When** querying 2025–2027, **Then** exactly gazetted public holiday records are returned.
4. **Given** `format_tamil_date` and `calendar_display_info`, **When** formatting dates in Tamil or Latin digits, **Then** localized month, day, and weekday strings match golden outputs.

---

### User Story 2 - Activate Ephemeris, Astronomical Transit, & Vakiya Suites (Priority: P2)

As an astronomical or astrological software author, I want verified, active golden test suites for solar month ingresses, lunar phases, day/night eighth divisions, and classical Vakiya planetary/lunar motions so that I can perform exact ephemeris calculations with verified mathematical reproducibility.

**Why this priority**: Validates the core astronomical models (Drik/Thirukanitham and classical Vakiya Laghuprakashika 1962). These require careful boundary checks around mean vs. true sunrise, Cara corrections, and Desantara conversions.

**Independent Test**: Can be tested by activating the 10 ephemeris suites and executing `just test-parity` across all runtimes.

**Acceptance Scenarios**:
1. **Given** solar transit and ingress requests (`calendar_solar_arithmetic`), **When** calculating monthly transitions for supported Gregorian years, **Then** transit times match Drik/Vakiya definitions to the exact second.
2. **Given** primary lunar phase queries (`calendar_lunar_phases`), **When** requesting new moon, full moon, or quarter phases, **Then** geocentric minutes match independent USNO checkpoints.
3. **Given** classical Vakiya calculations (`calendar_vakya_*`), **When** evaluating Candra-vakya, solar transits, Cara, or Desantara, **Then** outputs match the 1962 primary worked anchors.

---

### User Story 3 - Activate Observance Selectors & Multi-Profile Comparisons (Priority: P3)

As a temple administrator or panchangam publisher, I want verified observance rules for solar/tithi festivals, Ekadashi, Pradosham, and comparative profiling between Thirukanitham and Vakiya traditions so that festival dates are attributed accurately to specific community lineages without unsupported claims of universal equivalence.

**Why this priority**: Observances involve religious traditions and regional variation (e.g. Udyog Smarta vs. Sri Vaishnava Ekadashi, Dharmasindhu vs. Nava Pradosham). These require explicit metadata attribution and source boundary validation.

**Independent Test**: Can be verified by running `calendar_observances.jsonl`, `calendar_thirukanitham.jsonl`, and `calendar_profile_comparison.jsonl` against all runtimes and verifying that source-specific variant tags and date disagreements are preserved.

**Acceptance Scenarios**:
1. **Given** an observance query for Tamil Nadu festivals (`calendar_observances`), **When** evaluating Ekadashi or Pradosham, **Then** the active rule sets (Nava, Dharmasindhu, Udyog) resolve according to their specific boundary conditions.
2. **Given** a profile comparison query (`compare_calendar_profiles`), **When** contrasting Thirukanitham and Vakiya at a given instant or date, **Then** discrepancies in tithi, nakshatra, and solar day are reported factually without accuracy ranking.

---

### Edge Cases

- How does the system handle years outside the supported astronomical domain (e.g. < 2023 or > 2027 for Thirukanitham)? It MUST return explicit `outside supported calendar coverage` errors.
- How does the system handle negative solar years or non-integer year inputs? It MUST return explicit invalid calendar input errors.
- How does the system treat unquantified ritual thresholds (e.g. Dharmasindhu 3-muhurta worship duration)? It MUST reject or withhold unsupported selectors rather than fabricate approximation heuristics.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `manifest.json` MUST update the `status` of all reviewed calendar suites from `planned` to `active` in staged batches matching P1, P2, and P3.
- **FR-002**: All active calendar golden vectors MUST execute and pass identically in Rust (`golden_suite.rs`), Python (`test_golden.py`), and WebAssembly/Node (`golden.test.ts`).
- **FR-003**: The dispatcher in `crates/tamil-toolkit/src/lib.rs` and `calendar_features.rs` MUST enforce safe JSON integer limits (`MAX_SAFE_CALENDAR_JSON_INTEGER = 9_007_199_254_740_991`) on all calendar inputs and outputs.
- **FR-004**: Calendar suite activations MUST preserve source provenance tags (`source_id`, `source_sha256`, `sources`) for every golden vector.
- **FR-005**: `tools/mcp-tamil-oracle/check_source_unicode.py` MUST validate all newly activated calendar vectors without Unicode errors or missing escapes.
- **FR-006** *(Superseded)*: The developer workbench MUST execute all activated calendar operations directly against live WebAssembly binaries. *(Superseded: developer workbench removed completely).*

### Key Entities

- **Golden Suite Manifest (`tests/golden/manifest.json`)**: Authoritative inventory recording status (`active` vs `planned`), operation mapping, and review reasons for each test file.
- **Calendar Definition**: Unique identifier selecting astronomical models (e.g. `thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2` or `vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1`).
- **Observance Rule Set**: Named collection of festival selection logic bounded to specific sources (e.g. `thirukanitham-tamil-named-observances-v1`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of P1 tabular/metadata calendar vectors (over 80 vectors) transition to active status and pass in Rust, Python, and WASM.
- **SC-002**: Zero regressions in existing active suites (35,646 active numeral/core/collate/codec vectors remain 100% passing).
- **SC-003**: `just test-parity` passes with zero runtime divergences across all active suites.
- **SC-004**: `tools/release_policy.py check` and `tools/tasks.py check-unicode` pass cleanly upon suite activation.

## Assumptions

- The underlying astronomical algorithms in `crates/tamil-calendar` remain stable and require no breaking changes to vector contracts.
- P1 tabular suites can be activated immediately without waiting for P2/P3 review resolution.
