use crate::{magnitude, negative_prefix, to_words, Locale, MAX_INTEGER};
use tamil_core::normalize_nfc;

enum DateOp {
    Literal(&'static str),
    Day,
    MonthNumber,
    MonthAbbreviated,
    MonthWide,
    Weekday,
    Year,
    YearTwo,
}
mod tables {
    use super::DateOp;
    include!(concat!(env!("OUT_DIR"), "/numeral_format_tables.rs"));
}
pub use tables::FORMAT_PROFILE;
pub const INVALID_DATE: &str = "invalid Gregorian date";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DigitStyle {
    Latin,
    Tamil,
}
impl DigitStyle {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "latin" => Ok(Self::Latin),
            "tamil" => Ok(Self::Tamil),
            _ => Err("unsupported digit style".into()),
        }
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DateStyle {
    Short,
    Medium,
    Long,
    Full,
}
impl DateStyle {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "short" => Ok(Self::Short),
            "medium" => Ok(Self::Medium),
            "long" => Ok(Self::Long),
            "full" => Ok(Self::Full),
            _ => Err("unsupported date style".into()),
        }
    }
    fn index(self) -> usize {
        match self {
            Self::Short => 0,
            Self::Medium => 1,
            Self::Long => 2,
            Self::Full => 3,
        }
    }
}
fn digits(text: &str, style: DigitStyle) -> String {
    if style == DigitStyle::Latin {
        return text.to_owned();
    }
    text.chars()
        .map(|c| {
            if c.is_ascii_digit() {
                tables::TAMIL_DIGITS[c as usize - '0' as usize]
            } else {
                c
            }
        })
        .collect()
}
fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

/// Reduced signed rational with a positive denominator. Components are bounded.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Fraction {
    numerator: i64,
    denominator: u64,
}
impl Fraction {
    pub fn new(numerator: i64, denominator: i64) -> Result<Self, String> {
        let n = magnitude(numerator, MAX_INTEGER)?;
        let d = magnitude(denominator, MAX_INTEGER)?;
        if d == 0 {
            return Err("fraction denominator must not be zero".into());
        }
        let common = gcd(n, d);
        let value = (n / common) as i64;
        Ok(Self {
            numerator: if (numerator < 0) != (denominator < 0) {
                -value
            } else {
                value
            },
            denominator: d / common,
        })
    }
    pub fn numerator(self) -> i64 {
        self.numerator
    }
    pub fn denominator(self) -> u64 {
        self.denominator
    }
}
/// Exact reduced n/d, including /1 for integers. No floating-point arithmetic.
pub fn format_fraction(value: Fraction, style: DigitStyle) -> String {
    digits(&format!("{}/{}", value.numerator, value.denominator), style)
}
/// Common quarter/half names, otherwise an explicit numerator/division/denominator reading.
pub fn fraction_to_words(value: Fraction, locale: Locale) -> Result<String, String> {
    if value.denominator == 1 {
        return to_words(value.numerator, locale);
    }
    let n = value.numerator.unsigned_abs();
    let mut output = negative_prefix(value.numerator);
    if let Some((_, _, name)) = tables::NAMED_FRACTIONS
        .iter()
        .find(|&&(numerator, denominator, _)| numerator == n && denominator == value.denominator)
    {
        output.push_str(name);
    } else {
        output.push_str(&to_words(n as i64, locale)?);
        output.push(' ');
        output.push_str(tables::DIVISION);
        output.push(' ');
        output.push_str(&to_words(value.denominator as i64, locale)?);
    }
    Ok(normalize_nfc(&output))
}
/// The canonical Unicode Tamil fraction symbol, choosing the lower variant codepoint.
pub fn fraction_symbol(value: Fraction) -> Result<String, String> {
    let n = value.numerator.unsigned_abs();
    let (_, _, symbol) = tables::FRACTION_SYMBOLS
        .iter()
        .find(|&&(numerator, denominator, _)| numerator == n && denominator == value.denominator)
        .ok_or("no traditional Tamil symbol for this fraction")?;
    Ok(format!(
        "{}{symbol}",
        if value.numerator < 0 { "-" } else { "" }
    ))
}
fn leap(year: i64) -> bool {
    year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
}
fn month_length(year: i64, month: u32) -> u32 {
    if month == 2 && leap(year) {
        29
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month as usize - 1]
    }
}
/// A validated proleptic Gregorian civil date, years 1..9999 (no time zone).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GregorianDate {
    year: i64,
    month: u32,
    day: u32,
}
impl GregorianDate {
    pub fn new(year: i64, month: i64, day: i64) -> Result<Self, String> {
        if !(1..=9999).contains(&year) || !(1..=12).contains(&month) || !(1..=31).contains(&day) {
            return Err(INVALID_DATE.into());
        }
        if day as u32 > month_length(year, month as u32) {
            return Err(INVALID_DATE.into());
        }
        Ok(Self {
            year,
            month: month as u32,
            day: day as u32,
        })
    }
    pub fn year(self) -> i64 {
        self.year
    }
    pub fn month(self) -> u32 {
        self.month
    }
    pub fn day(self) -> u32 {
        self.day
    }
    fn weekday(self) -> usize {
        let y = self.year - 1;
        let ordinal = (1..self.month)
            .map(|month| i64::from(month_length(self.year, month)))
            .sum::<i64>()
            + i64::from(self.day)
            - 1;
        ((365 * y + y / 4 - y / 100 + y / 400 + ordinal + 1) % 7) as usize
    }
}
/// Format a valid civil date with the pinned CLDR Tamil styles and digit system.
pub fn format_date(
    date: GregorianDate,
    _locale: Locale,
    style: DateStyle,
    digit_style: DigitStyle,
) -> String {
    let mut output = String::new();
    for op in tables::DATE_PATTERNS[style.index()] {
        match op {
            DateOp::Literal(text) => output.push_str(text),
            DateOp::Day => output.push_str(&date.day.to_string()),
            DateOp::MonthNumber => output.push_str(&date.month.to_string()),
            DateOp::MonthAbbreviated => {
                output.push_str(tables::ABBREVIATED_MONTHS[date.month as usize - 1])
            }
            DateOp::MonthWide => output.push_str(tables::MONTHS[date.month as usize - 1]),
            DateOp::Weekday => output.push_str(tables::WEEKDAYS[date.weekday()]),
            DateOp::Year => output.push_str(&date.year.to_string()),
            DateOp::YearTwo => output.push_str(&format!("{:02}", date.year % 100)),
        }
    }
    normalize_nfc(&digits(&output, digit_style))
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    fn latin(text: &str) -> String {
        text.chars()
            .map(|c| {
                tables::TAMIL_DIGITS
                    .iter()
                    .position(|&d| d == c)
                    .map(|index| (b'0' + index as u8) as char)
                    .unwrap_or(c)
            })
            .collect()
    }
    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_fraction_inputs_never_panic(n in any::<i64>(),d in any::<i64>()){
            let result=Fraction::new(n,d);prop_assert_eq!(result.is_ok(),n.unsigned_abs()<=MAX_INTEGER as u64&&d.unsigned_abs()<=MAX_INTEGER as u64&&d!=0);
            if let Ok(value)=result{prop_assert_eq!(value.numerator*d,n*value.denominator as i64);prop_assert_eq!(gcd(value.numerator.unsigned_abs(),value.denominator),1);}
        }
        #[test]
        fn exact_fraction_formats_roundtrip(n in -MAX_INTEGER..=MAX_INTEGER,d in 1_i64..=MAX_INTEGER){
            let value=Fraction::new(n,d).unwrap();let text=format_fraction(value,DigitStyle::Latin);let(a,b)=text.split_once('/').unwrap();
            prop_assert_eq!(Fraction::new(a.parse().unwrap(),b.parse().unwrap()).unwrap(),value);
            prop_assert_eq!(latin(&format_fraction(value,DigitStyle::Tamil)),text);
            for locale in [Locale::TN,Locale::SL]{let words=fraction_to_words(value,locale).unwrap();prop_assert_eq!(&words,&normalize_nfc(&words));}
        }
        #[test]
        fn gregorian_cycle_and_digit_styles_agree(year in 1_i64..=9599,month in 1_i64..=12,day in 1_i64..=31){
            if let Ok(date)=GregorianDate::new(year,month,day){let other=GregorianDate::new(year+400,month,day).unwrap();prop_assert_eq!(date.weekday(),other.weekday());
                for style in [DateStyle::Short,DateStyle::Medium,DateStyle::Long,DateStyle::Full]{let a=format_date(date,Locale::TN,style,DigitStyle::Latin);let b=format_date(date,Locale::SL,style,DigitStyle::Tamil);prop_assert_eq!(latin(&b),a);prop_assert_eq!(&b,&normalize_nfc(&b));}
            }
        }
        #[test]
        fn arbitrary_date_components_never_panic(year in any::<i64>(),month in any::<i64>(),day in any::<i64>()){
            if let Ok(date)=GregorianDate::new(year,month,day){let _=format_date(date,Locale::TN,DateStyle::Full,DigitStyle::Tamil);}
        }
    }
}
