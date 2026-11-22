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
    primary_group: usize,
    secondary_group: usize,
}
pub(crate) struct MixedEndingRule {
    pub strip_suffix: &'static str,
    pub quarter: &'static str,
    pub half: &'static str,
    pub three_quarters: &'static str,
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
    use super::{CurrencyUnits, MixedEndingRule, Op, Operand, Rule, SymbolInfo};
    include!(concat!(env!("OUT_DIR"), "/numeral_tables.rs"));
}
pub use tables::{MAX_INTEGER, MAX_MINOR, PROFILE};
pub const INTEGER_ERROR: &str = "expected an integer in the supported range";

mod numeric;
pub use numeric::{
    add_gregorian_date, convert_digits, currency_decimal_to_words, date_difference,
    date_from_ordinal, date_interval, decimal_to_words, digit_sequence_to_words,
    format_currency_decimal, format_decimal, format_mixed_fraction, format_numeric_range,
    format_percent, format_traditional_integer, iso_date, ordinal_day, ordinal_to_words,
    parse_decimal, parse_fraction_symbol, parse_gregorian_date, parse_mixed_fraction,
    parse_percent, parse_traditional_integer, percent_to_ratio, ratio_to_percent, symbol_info,
    validate_currency_decimal, validate_exact_decimal, validate_gregorian_date,
    validate_mixed_fraction, validate_numeric_range, weekday, ExactDecimal, MixedFraction,
    NumericRangeEndpoint, MAX_DECIMAL_DIGITS, MAX_DECIMAL_SCALE,
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
    SGD,
    MYR,
    USD,
    EUR,
    GBP,
    CAD,
}
impl Currency {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "INR" => Ok(Self::INR),
            "LKR" => Ok(Self::LKR),
            "SGD" => Ok(Self::SGD),
            "MYR" => Ok(Self::MYR),
            "USD" => Ok(Self::USD),
            "EUR" => Ok(Self::EUR),
            "GBP" => Ok(Self::GBP),
            "CAD" => Ok(Self::CAD),
            _ => Err("unsupported currency".into()),
        }
    }
    fn units(self) -> &'static CurrencyUnits {
        &tables::CURRENCIES[match self {
            Self::INR => 0,
            Self::LKR => 1,
            Self::SGD => 2,
            Self::MYR => 3,
            Self::USD => 4,
            Self::EUR => 5,
            Self::GBP => 6,
            Self::CAD => 7,
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

fn grouped(value: u64, primary_group: usize, secondary_group: usize) -> String {
    let digits = value.to_string();
    let mut end = digits.len();
    let mut width = primary_group;
    let mut groups = Vec::new();
    while end > 0 {
        let start = end.saturating_sub(width);
        groups.push(&digits[start..end]);
        end = start;
        width = secondary_group;
    }
    groups.reverse();
    groups.join(",")
}

/// ISO code and currency-grouped Latin digits with exactly two decimal places.
/// Input is exact signed minor units; no rounding.
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
        grouped(
            value / units.factor,
            units.primary_group,
            units.secondary_group
        ),
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

/// Colloquial Tamil mixed-fraction words for 1/4, 1/2, 3/4, or explicit conjunction otherwise.
pub fn mixed_fraction_to_words(value: &MixedFraction, locale: Locale) -> Result<String, String> {
    validate_mixed_fraction(value)?;
    if value.numerator == 0 {
        let signed = if value.negative {
            -(value.whole as i64)
        } else {
            value.whole as i64
        };
        return to_words(signed, locale);
    }
    if value.whole == 0 {
        let signed_num = if value.negative {
            -(value.numerator as i64)
        } else {
            value.numerator as i64
        };
        return fraction_to_words(Fraction::new(signed_num, value.denominator as i64)?, locale);
    }
    let reduced = Fraction::new(value.numerator as i64, value.denominator as i64)?;
    let (num, den) = (reduced.numerator().unsigned_abs(), reduced.denominator());
    let whole_words = to_words(value.whole as i64, locale)?;
    let prefix = if value.negative {
        format!("{} ", tables::NEGATIVE)
    } else {
        String::new()
    };
    let compound = match (num, den) {
        (1, 4) | (1, 2) | (3, 4) => {
            let rule = tables::MIXED_ENDINGS
                .iter()
                .find(|r| whole_words.ends_with(r.strip_suffix))
                .ok_or_else(|| "invalid mixed fraction".to_owned())?;
            let stem = &whole_words[..whole_words.len() - rule.strip_suffix.len()];
            let suffix = match (num, den) {
                (1, 4) => rule.quarter,
                (1, 2) => rule.half,
                _ => rule.three_quarters,
            };
            format!("{prefix}{stem}{suffix}")
        }
        _ => {
            let frac = fraction_to_words(reduced, locale)?;
            format!("{prefix}{whole_words} {} {frac}", tables::MIXED_CONJUNCTION)
        }
    };
    Ok(normalize_nfc(&compound))
}

fn parse_optional_remainder(
    tail: &str,
    nonzero: &[Op],
    zero: &[Op],
    divisor: u64,
    rules: &[&[Rule]],
    depth: usize,
) -> Option<u64> {
    // Check zero branch first
    match zero {
        [] if tail.is_empty() => return Some(0),
        [Op::Literal(zlit)] if tail == *zlit => return Some(0),
        _ => {}
    }
    // Check nonzero branch: [Op::Literal(nz_lit), Op::Substitute(Operand::Remainder, target_set)]
    if let [Op::Literal(nz_lit), Op::Substitute(Operand::Remainder, target_set)] = nonzero {
        if let Some(rem_str) = tail.strip_prefix(nz_lit) {
            if let Some(rem) = parse_ruleset(rem_str, *target_set, rules, depth + 1) {
                if rem > 0 && rem < divisor {
                    return Some(rem);
                }
            }
        }
    }
    None
}

fn parse_ruleset(text: &str, set: usize, rules: &[&[Rule]], depth: usize) -> Option<u64> {
    if depth > 64 || text.is_empty() {
        return None;
    }
    for rule in rules[set].iter().rev() {
        match rule.ops {
            [Op::Literal(lit)] if text == *lit => {
                return Some(rule.base);
            }
            [Op::Literal(lit), Op::Optional(nonzero, zero)] => {
                if let Some(tail) = text.strip_prefix(lit) {
                    if let Some(rem) =
                        parse_optional_remainder(tail, nonzero, zero, rule.divisor, rules, depth)
                    {
                        return rule.base.checked_add(rem);
                    }
                }
            }
            [Op::Substitute(Operand::Quotient, q_set), Op::Literal(lit), Op::Optional(nonzero, zero)] => {
                for (pos, _) in text.match_indices(lit) {
                    let left = &text[..pos];
                    let tail = &text[pos + lit.len()..];
                    if let Some(q) = parse_ruleset(left, *q_set, rules, depth + 1) {
                        let min_q = rule.base / rule.divisor;
                        if q >= min_q && q <= 99 {
                            if let Some(rem) = parse_optional_remainder(
                                tail,
                                nonzero,
                                zero,
                                rule.divisor,
                                rules,
                                depth,
                            ) {
                                if let Some(val) =
                                    q.checked_mul(rule.divisor).and_then(|v| v.checked_add(rem))
                                {
                                    return Some(val);
                                }
                            }
                        }
                    }
                }
            }
            _ => {}
        }
    }
    None
}

/// Exact inverse of `to_words` for CLDR 49 formal Tamil number words (`-MAX_INTEGER..=MAX_INTEGER`).
pub fn words_to_number(text: &str, locale: Locale) -> Result<i64, String> {
    let err = || "invalid Tamil number words".to_owned();
    let normalized = normalize_nfc(text);
    if normalized.is_empty() || normalized.trim() != normalized {
        return Err(err());
    }
    let neg_prefix = format!("{} ", tables::NEGATIVE);
    let (negative, body) = if let Some(rest) = normalized.strip_prefix(&neg_prefix) {
        (true, rest)
    } else {
        (false, normalized.as_str())
    };
    let mag = parse_ruleset(body, tables::NUMBERING, locale.rules(), 0).ok_or_else(err)?;
    if mag > MAX_INTEGER as u64 || (negative && mag == 0) {
        return Err(err());
    }
    let signed = if negative { -(mag as i64) } else { mag as i64 };
    if to_words(signed, locale).ok().as_deref() == Some(normalized.as_str()) {
        Ok(signed)
    } else {
        Err(err())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    const ALL_CURRENCIES: [Currency; 8] = [
        Currency::INR,
        Currency::LKR,
        Currency::SGD,
        Currency::MYR,
        Currency::USD,
        Currency::EUR,
        Currency::GBP,
        Currency::CAD,
    ];

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_signed_inputs_never_panic(value in any::<i64>()) {
            for locale in [Locale::TN, Locale::SL] {
                prop_assert_eq!(to_words(value, locale).is_ok(), value.unsigned_abs() <= MAX_INTEGER as u64);
                for currency in ALL_CURRENCIES {
                    prop_assert_eq!(format_currency(value, currency, locale).is_ok(), value.unsigned_abs() <= MAX_MINOR as u64);
                    prop_assert_eq!(currency_to_words(value, currency, locale).is_ok(), value.unsigned_abs() <= MAX_MINOR as u64);
                }
            }
        }
        #[test]
        fn currency_digits_roundtrip_exactly(value in -MAX_MINOR..=MAX_MINOR, sl in any::<bool>(), curr_idx in 0usize..8) {
            let currency = ALL_CURRENCIES[curr_idx];
            let text = format_currency(value, currency, if sl { Locale::SL } else { Locale::TN }).unwrap();
            let digits: String = text.split_once(' ').unwrap().1.chars().filter(|c| *c != ',' && *c != '.').collect();
            prop_assert_eq!(digits.parse::<i64>().unwrap(), value);
            prop_assert_eq!(text.rsplit_once('.').unwrap().1.len(), 2);
        }
        #[test]
        fn supported_words_are_nfc_and_clean(value in -MAX_INTEGER..=MAX_INTEGER, minor in 0_i64..100, sl in any::<bool>(), curr_idx in 0usize..8) {
            let locale = if sl { Locale::SL } else { Locale::TN };
            let currency = ALL_CURRENCIES[curr_idx];
            for words in [to_words(value, locale).unwrap(), currency_to_words(value * 100 + minor, currency, locale).unwrap()] {
                prop_assert_eq!(&words, &normalize_nfc(&words));
                prop_assert!(!words.is_empty() && words.trim() == words && !words.contains("  "));
                prop_assert!(words.chars().all(|c| !matches!(u32::from(c), 0x200c | 0x200d)), "generated words must not contain joiners");
            }
        }
        #[test]
        fn words_to_number_bijection_roundtrips(value in -MAX_INTEGER..=MAX_INTEGER, sl in any::<bool>()) {
            let locale = if sl { Locale::SL } else { Locale::TN };
            let words = to_words(value, locale).unwrap();
            prop_assert_eq!(words_to_number(&words, locale).unwrap(), value);
        }
        #[test]
        fn mixed_fraction_words_are_nfc_and_clean(whole in 0_u64..=MAX_INTEGER as u64, kind in 0_u8..4, neg in any::<bool>(), sl in any::<bool>()) {
            let locale = if sl { Locale::SL } else { Locale::TN };
            let (numerator, denominator) = match kind {
                0 => (1, 4),
                1 => (1, 2),
                2 => (3, 4),
                _ => (2, 5),
            };
            let mf = MixedFraction { negative: neg, whole, numerator, denominator };
            let words = mixed_fraction_to_words(&mf, locale).unwrap();
            prop_assert_eq!(&words, &normalize_nfc(&words));
            prop_assert!(!words.is_empty() && words.trim() == words && !words.contains("  "));
            prop_assert!(words.chars().all(|c| !matches!(u32::from(c), 0x200c | 0x200d)));
        }
    }
}
