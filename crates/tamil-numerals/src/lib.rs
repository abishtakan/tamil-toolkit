//! Bounded CLDR 49 integer spellout and exact INR/LKR minor-unit rendering.
//! See docs/specs/numerals-v0.1.md for the declared TN/SL lexical profiles.
#![forbid(unsafe_code)]

use tamil_core::normalize_nfc;
mod formats;
pub use formats::{
    format_date, format_fraction, fraction_symbol, fraction_to_words, DateStyle, DigitStyle,
    Fraction, GregorianDate, FORMAT_PROFILE, INVALID_DATE,
};

#[derive(Clone, Copy)]
enum Operand {
    Quotient,
    Remainder,
    Same,
}
enum Op {
    Literal(&'static str),
    Substitute(Operand, usize),
    Optional(&'static [Op], &'static [Op]),
}
struct Rule {
    base: u64,
    divisor: u64,
    ops: &'static [Op],
}
struct CurrencyUnits {
    code: &'static str,
    major: &'static str,
    minor: &'static str,
    factor: u64,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CalendarOfficialHoliday {
    pub date: GregorianDate,
    pub name: &'static str,
    pub categories: &'static [&'static str],
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CalendarOfficialHolidayYearInfo {
    pub jurisdiction: &'static str,
    pub year: i64,
    pub schedule_id: &'static str,
    pub source_id: &'static str,
    pub source: &'static str,
    pub source_url: &'static str,
    pub source_sha256: Option<&'static str>,
    pub reuse_terms_status: &'static str,
    pub scope_note: &'static str,
    pub holidays: Vec<CalendarOfficialHoliday>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SymbolInfo {
    pub codepoint: u32,
    pub character: &'static str,
    pub name: &'static str,
    pub kind: &'static str,
    pub rational: Option<(i64, u64)>,
    pub canonical_alternative: Option<u32>,
    pub source_version: &'static str,
}
mod tables {
    use super::{CurrencyUnits, Op, Operand, Rule, SolarVakya, SymbolInfo};
    include!(concat!(env!("OUT_DIR"), "/numeral_tables.rs"));
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct SolarVakya {
    pub rasi: &'static str,
    pub days: i64,
    pub nadis: i64,
    pub vinadis: i64,
}
mod calendar;
pub use calendar::{
    calendar_display_names, calendar_official_holiday_year, solar_year_cycle_info,
    thirukanitham_add_solar_date, thirukanitham_daylight_periods,
    thirukanitham_gregorian_to_tamil_date, thirukanitham_lunar_phase_events,
    thirukanitham_month_info, thirukanitham_observances, thirukanitham_panchangam_at,
    thirukanitham_panchangam_day, thirukanitham_profile_info, thirukanitham_solar_year_info,
    thirukanitham_tamil_to_gregorian_date, vakya_add_solar_date, vakya_bhujaantara_from_true_sun,
    vakya_cara_from_sayana_sun, vakya_civil_profile_info, vakya_desantara_from_yojana_distance,
    vakya_gregorian_to_tamil_date, vakya_month_info, vakya_panchangam_at, vakya_panchangam_day,
    vakya_reduce_to_local_true_sunrise, vakya_solar_transits, vakya_solar_year_info,
    vakya_tamil_to_gregorian_date, vakya_true_moon_from_kali_day,
    vakya_true_sun_from_mesha_elapsed, Ahargana, CalendarDisplayNames, CalendarSolarDate,
    CalendarSolarDateArithmetic, CalendarSolarMonth, CalendarSolarYearCycleInfo,
    CalendarSolarYearInfo, DmsAngle, RasiDmsAngle, SolarTransit, ThirukanithamContext,
    ThirukanithamDateConversion, ThirukanithamDateReverse, ThirukanithamDaylightInterval,
    ThirukanithamDaylightPeriods, ThirukanithamLimb, ThirukanithamLimbs, ThirukanithamLocalTime,
    ThirukanithamLunarPhaseEvent, ThirukanithamMonthInfo, ThirukanithamObservanceEvent,
    ThirukanithamObservanceSource, ThirukanithamObservances, ThirukanithamPanchangamAt,
    ThirukanithamPanchangamDay, ThirukanithamProfileInfo, ThirukanithamRegionInfo,
    ThirukanithamStationInfo, ThirukanithamTamilDate, ThirukanithamTransition,
    ThirukanithamUtcMinute, VakyaBhujaantara, VakyaCara, VakyaCivilContext,
    VakyaCivilDateConversion, VakyaCivilDateReverse, VakyaCivilLimb, VakyaCivilLimbs,
    VakyaCivilMonthInfo, VakyaCivilPanchangamAt, VakyaCivilPanchangamDay, VakyaCivilProfileInfo,
    VakyaCivilTamilDate, VakyaCivilTime, VakyaCivilTransition, VakyaDesantara,
    VakyaLocalSunriseReduction, VakyaSolarYear, VakyaTrueMoon, VakyaTrueSun,
};
pub use tables::{MAX_INTEGER, MAX_MINOR, PROFILE};
pub const INTEGER_ERROR: &str = "expected an integer in the supported range";

mod numeric;
pub use numeric::{
    add_gregorian_date, convert_digits, currency_decimal_to_words, date_difference, date_interval,
    decimal_to_words, digit_sequence_to_words, format_currency_decimal, format_decimal,
    format_mixed_fraction, format_numeric_range, format_percent, format_traditional_integer,
    iso_date, ordinal_to_words, parse_decimal, parse_fraction_symbol, parse_gregorian_date,
    parse_mixed_fraction, parse_percent, parse_traditional_integer, percent_to_ratio,
    ratio_to_percent, symbol_info, validate_currency_decimal, validate_exact_decimal,
    validate_gregorian_date, validate_mixed_fraction, validate_numeric_range, weekday,
    ExactDecimal, MixedFraction, NumericRangeEndpoint, MAX_DECIMAL_DIGITS, MAX_DECIMAL_SCALE,
};

/// Formal lexical profiles; neither is a regional spoken-language normalizer.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Locale {
    TN,
    SL,
}
impl Locale {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "TN" => Ok(Self::TN),
            "SL" => Ok(Self::SL),
            _ => Err("unsupported locale".into()),
        }
    }
    fn rules(self) -> &'static [&'static [Rule]] {
        match self {
            Self::TN => tables::TN,
            Self::SL => tables::SL,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Currency {
    INR,
    LKR,
}
impl Currency {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "INR" => Ok(Self::INR),
            "LKR" => Ok(Self::LKR),
            _ => Err("unsupported currency".into()),
        }
    }
    fn units(self) -> &'static CurrencyUnits {
        &tables::CURRENCIES[match self {
            Self::INR => 0,
            Self::LKR => 1,
        }]
    }
}

fn magnitude(value: i64, maximum: i64) -> Result<u64, String> {
    let magnitude = value.unsigned_abs();
    if magnitude > maximum as u64 {
        Err(INTEGER_ERROR.into())
    } else {
        Ok(magnitude)
    }
}

fn spell(
    value: u64,
    set: usize,
    rules: &[&[Rule]],
    depth: usize,
    output: &mut String,
) -> Result<(), String> {
    if depth > 64 {
        return Err("invalid numeral rule recursion".into());
    }
    let rule = rules[set]
        .iter()
        .rev()
        .find(|rule| rule.base <= value)
        .ok_or("no matching numeral rule")?;
    render(rule.ops, value, rule.divisor, rules, depth, output)
}

fn render(
    ops: &[Op],
    value: u64,
    divisor: u64,
    rules: &[&[Rule]],
    depth: usize,
    output: &mut String,
) -> Result<(), String> {
    for op in ops {
        match op {
            Op::Literal(text) => output.push_str(text),
            Op::Substitute(operand, set) => {
                let number = match operand {
                    Operand::Quotient => value / divisor,
                    Operand::Remainder => value % divisor,
                    Operand::Same => value,
                };
                spell(number, *set, rules, depth + 1, output)?;
            }
            Op::Optional(nonzero, zero) => render(
                if value % divisor == 0 { zero } else { nonzero },
                value,
                divisor,
                rules,
                depth + 1,
                output,
            )?,
        }
    }
    Ok(())
}

fn negative_prefix(value: i64) -> String {
    if value < 0 {
        format!("{} ", tables::NEGATIVE)
    } else {
        String::new()
    }
}

/// Standalone integer spelling, inclusive range +/- MAX_INTEGER. Allocates.
pub fn to_words(value: i64, locale: Locale) -> Result<String, String> {
    let magnitude = magnitude(value, MAX_INTEGER)?;
    let mut output = negative_prefix(value);
    spell(magnitude, tables::NUMBERING, locale.rules(), 0, &mut output)?;
    Ok(normalize_nfc(&output))
}

fn grouped(value: u64) -> String {
    let digits = value.to_string();
    let mut end = digits.len();
    let mut width = tables::PRIMARY_GROUP;
    let mut groups = Vec::new();
    while end > 0 {
        let start = end.saturating_sub(width);
        groups.push(&digits[start..end]);
        end = start;
        width = tables::SECONDARY_GROUP;
    }
    groups.reverse();
    groups.join(",")
}

/// ISO code and 3-2-grouped Latin digits with exactly two decimal places.
/// Both profiles share grouping. Input is exact signed minor units; no rounding.
pub fn format_currency(
    amount_minor: i64,
    currency: Currency,
    _locale: Locale,
) -> Result<String, String> {
    let value = magnitude(amount_minor, MAX_MINOR)?;
    let units = currency.units();
    let sign = if amount_minor < 0 { "-" } else { "" };
    Ok(format!(
        "{} {sign}{}.{:02}",
        units.code,
        grouped(value / units.factor),
        value % units.factor
    ))
}

/// Noun/cardinal spellings followed by invariant major/minor denomination labels.
/// Both units are always present. This is not a cheque-writing grammar. Allocates.
pub fn currency_to_words(
    amount_minor: i64,
    currency: Currency,
    locale: Locale,
) -> Result<String, String> {
    let value = magnitude(amount_minor, MAX_MINOR)?;
    let units = currency.units();
    let mut output = negative_prefix(amount_minor);
    spell(
        value / units.factor,
        tables::CARDINAL,
        locale.rules(),
        0,
        &mut output,
    )?;
    output.push(' ');
    output.push_str(units.major);
    output.push(' ');
    spell(
        value % units.factor,
        tables::CARDINAL,
        locale.rules(),
        0,
        &mut output,
    )?;
    output.push(' ');
    output.push_str(units.minor);
    Ok(normalize_nfc(&output))
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_signed_inputs_never_panic(value in any::<i64>()) {
            for locale in [Locale::TN, Locale::SL] {
                prop_assert_eq!(to_words(value, locale).is_ok(), value.unsigned_abs() <= MAX_INTEGER as u64);
                for currency in [Currency::INR, Currency::LKR] {
                    prop_assert_eq!(format_currency(value, currency, locale).is_ok(), value.unsigned_abs() <= MAX_MINOR as u64);
                    prop_assert_eq!(currency_to_words(value, currency, locale).is_ok(), value.unsigned_abs() <= MAX_MINOR as u64);
                }
            }
        }
        #[test]
        fn currency_digits_roundtrip_exactly(value in -MAX_MINOR..=MAX_MINOR, sl in any::<bool>(), lkr in any::<bool>()) {
            let currency = if lkr { Currency::LKR } else { Currency::INR };
            let text = format_currency(value, currency, if sl { Locale::SL } else { Locale::TN }).unwrap();
            let digits: String = text.split_once(' ').unwrap().1.chars().filter(|c| *c != ',' && *c != '.').collect();
            prop_assert_eq!(digits.parse::<i64>().unwrap(), value);
            prop_assert_eq!(text.rsplit_once('.').unwrap().1.len(), 2);
        }
        #[test]
        fn supported_words_are_nfc_and_clean(value in -MAX_INTEGER..=MAX_INTEGER, minor in 0_i64..100, sl in any::<bool>(), lkr in any::<bool>()) {
            let locale = if sl { Locale::SL } else { Locale::TN };
            let currency = if lkr { Currency::LKR } else { Currency::INR };
            for words in [to_words(value, locale).unwrap(), currency_to_words(value * 100 + minor, currency, locale).unwrap()] {
                prop_assert_eq!(&words, &normalize_nfc(&words));
                prop_assert!(!words.is_empty() && words.trim() == words && !words.contains("  "));
                prop_assert!(words.chars().all(|c| !matches!(u32::from(c), 0x200c | 0x200d)), "generated words must not contain joiners");
            }
        }
    }
}
