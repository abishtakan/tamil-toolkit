# Data Model: Calendar Crate Split

**Feature**: `specs/001-calendar-crate-split`

## 1. Domain Entities & Package Boundaries

```
[tamil-core] <────────────┐
      ▲                   │
      │                   │
[tamil-numerals]          │
      ▲                   │
      │                   │
[tamil-calendar] ─────────┘
      ▲
      │
[tamil-toolkit] (Unified Dispatcher)
 ├── Python (`tamil_toolkit.calendar`)
 ├── WASM (`tamil_toolkit.calendar`)
 └── Dart (`TamilCalendar`)
```

### Entity: `tamil-calendar` (Crate)
- **Path**: `crates/tamil-calendar`
- **Dependencies**:
  - `tamil-core.workspace = true`
  - `tamil-numerals.workspace = true`
  - `astro = "=2.0.0"`
- **Internal Modules**:
  - `solar_arithmetic`: Day, month, and year cycle calculations, solar date additions.
  - `drik`: Thirukanitham ephemeris calculations, five limbs, sunrise/sunset, daylight intervals, primary lunar phases.
  - `vakya`: Classical Vakiya true Sun, true Moon, Cara, Desantara, and Bhujaantara reductions.
  - `vakya_civil`: Vakiya civil calendar profile, month information, panchangam day/instant.
  - `display`: Tamil and Romanized date display formatting, month names, weekday names.
  - `holidays`: Government holiday schedules (TN & SL).
  - `observances`: Festival and vrata rules (Amavasai, Pournami, Ekadashi, Pradosham, etc.).

### Entity: `tamil-numerals` (Refined Crate)
- **Path**: `crates/tamil-numerals`
- **Dependencies**:
  - `tamil-core.workspace = true`
- **Exposed Modules**:
  - `numeric`: Integers, words, digit sequences, ordinals, decimals, fractions, mixed fractions, traditional integers.
  - `formats`: LKR/INR currencies, standard decimal currency formatting.
- **Removed**:
  - `calendar` submodule and all references to astronomical structures or `astro`.

### Entity: Shared Dispatcher Routing (`tamil-toolkit`)
- **Operations Routed to `tamil-calendar`**:
  - `calendar_profile_info`
  - `gregorian_to_tamil_date`
  - `tamil_to_gregorian_date`
  - `tamil_month_info`
  - `panchangam_at`
  - `panchangam_day`
  - `calendar_observances`
  - `calendar_daylight_periods`
  - `lunar_phase_events`
  - `tamil_year_info`
  - `add_tamil_date`
  - `tamil_year_cycle_info`
  - `calendar_official_holidays`
  - `format_tamil_date`
  - `calendar_display_info`
  - `compare_calendar_profiles`
  - `thiruvalluvar_year_info`
  - `vakya_solar_transits`
  - `vakya_true_sun_from_mesha_elapsed`
  - `vakya_true_moon_from_kali_day`
  - `vakya_reduce_to_local_true_sunrise`
  - `vakya_cara_from_sayana_sun`
  - `vakya_desantara_from_yojana_distance`
  - `vakya_bhujaantara_from_true_sun`

## 2. Test Suite Ownership (Manifest Mapping)

All 17 calendar suites in `tests/golden/manifest.json` are reassigned from `tamil-numerals` to `tamil-calendar`:
- `calendar_thirukanitham.jsonl`
- `calendar_observances.jsonl`
- `calendar_daylight_periods.jsonl`
- `calendar_lunar_phases.jsonl`
- `calendar_solar_arithmetic.jsonl`
- `calendar_vakya_solar.jsonl`
- `calendar_vakya_moon.jsonl`
- `calendar_vakya_civil.jsonl`
- `calendar_vakya_local_sunrise.jsonl`
- `calendar_vakya_cara.jsonl`
- `calendar_vakya_desantara.jsonl`
- `calendar_vakya_bhujaantara.jsonl`
- `calendar_year_cycle.jsonl`
- `calendar_official_holidays.jsonl`
- `calendar_tamil_display.jsonl`
- `calendar_profile_comparison.jsonl`
- `calendar_thiruvalluvar_year.jsonl`
