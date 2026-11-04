# tamil-calendar

Standalone Tamil calendar and almanac engine for the `tamil-toolkit` workspace.

## Scope

`tamil-calendar` implements classical and contemporary Tamil timekeeping, panchangam, and observance algorithms in pure Rust:
- **Thirukanitham (Drik) System**: Apparent geocentric ephemeris calculations, five limbs (*Tithi*, *Vāra*, *Nakshatra*, *Yoga*, *Karaṇa*), sunrise/sunset, daylight intervals (*Rahu kalam*, *Yamagandam*, *Kuligai*), and primary lunar phases.
- **Vakiya (Vakya) System**: Classical Vakiya equations of true Sun, true Moon, Cara, Desantara, and Bhujaantara reductions, anchored to the printed 1962 Vakyakarana edition.
- **Civil Calendar**: Gregorian ↔ Tamil solar date conversions, solar arithmetic, 60-year cycles (*Prabhava* through *Kshaya*), and Thiruvalluvar year calculations.
- **Observances & Holidays**: Official government holiday schedules (Tamil Nadu & Sri Lanka) and verified festival/vrata rule selectors.

## Status

`tamil-calendar` is currently an internal/experimental workspace crate. Public production releases are gated under the project's constitution until remaining astronomical and festival selector contracts are finalized.
