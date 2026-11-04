# Interface Contracts: Calendar Crate Split

**Feature**: `specs/001-calendar-crate-split`

## 1. Rust Crate Contract: `tamil-calendar`

### Package Definition (`crates/tamil-calendar/Cargo.toml`)
```toml
[package]
name = "tamil-calendar"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
publish = false
license.workspace = true
repository.workspace = true
readme = "README.md"
description = "Tamil calendar systems, Thirukanitham, Vakiya, panchangam, and observances"

[dependencies]
tamil-core.workspace = true
tamil-numerals.workspace = true
astro = "=2.0.0"

[dev-dependencies]
proptest.workspace = true
serde_json.workspace = true

[lints]
workspace = true
```

### Root Exports (`crates/tamil-calendar/src/lib.rs`)
Exposes all calendar models, date conversions, panchangam limbs, and observance rules previously residing under `tamil_numerals::calendar`:
- Solar Arithmetic: `thirukanitham_add_solar_date`, `vakya_add_solar_date`, `solar_year_cycle_info`, `CalendarSolarDate`, `CalendarSolarMonth`.
- Thirukanitham (Drik): `thirukanitham_panchangam_at`, `thirukanitham_panchangam_day`, `thirukanitham_gregorian_to_tamil_date`, `thirukanitham_tamil_to_gregorian_date`, `thirukanitham_month_info`, `thirukanitham_daylight_periods`, `thirukanitham_lunar_phase_events`.
- Vakiya: `vakya_solar_transits`, `vakya_true_sun_from_mesha_elapsed`, `vakya_true_moon_from_kali_day`, `vakya_cara_from_sayana_sun`, `vakya_desantara_from_yojana_distance`, `vakya_bhujaantara_from_true_sun`, `vakya_reduce_to_local_true_sunrise`.
- Vakiya Civil: `vakya_gregorian_to_tamil_date`, `vakya_tamil_to_gregorian_date`, `vakya_month_info`, `vakya_panchangam_at`, `vakya_panchangam_day`.
- Observances & Holidays: `thirukanitham_observances`, `calendar_official_holiday_year`.
- Display: `calendar_display_names`, `CalendarDisplayNames`.

## 2. Refined Rust Crate Contract: `tamil-numerals`

### Package Definition (`crates/tamil-numerals/Cargo.toml`)
- Removes `astro = "=2.0.0"`.
- Removes `src/calendar/` directory and `calendar` module export.
- Remains focused strictly on `numeric.rs` and `formats.rs`.

## 3. Top-Level Facade (`tamil-toolkit`) Contract

### Rust Module Re-export
```rust
pub use tamil_calendar as calendar;
pub use tamil_codec as codec;
pub use tamil_collate as collate;
pub use tamil_core as core;
pub use tamil_norm as norm;
pub use tamil_numerals as numerals;
```

### Python Binding Contract
```python
import tamil_toolkit

# Numerals remain under root / numerals module:
words = tamil_toolkit.numerals.to_words(123)

# Calendar operations are housed in the dedicated calendar namespace:
tamil_date = tamil_toolkit.calendar.gregorian_to_tamil_date(
    definition_id="thirukanitham-v1",
    year=2026, month=11, day=5,
    context={"station": "chennai"}
)
```

### TypeScript / WebAssembly Contract
```typescript
import { createApi } from "tamil-toolkit";

const api = createApi();

// Numerals API:
const words = api.numerals.toWords(123);

// Calendar API sub-namespace:
const date = api.calendar.gregorianToTamilDate({
  definitionId: "thirukanitham-v1",
  year: 2026, month: 11, day: 5,
  context: { station: "chennai" }
});
```

### Dart Contract
```dart
import 'package:tamil_toolkit/tamil_toolkit.dart';

// Standalone Calendar API:
final date = TamilCalendar.gregorianToTamilDate(
  definitionId: 'thirukanitham-v1',
  year: 2026, month: 11, day: 5,
  context: {'station': 'chennai'},
);
```
