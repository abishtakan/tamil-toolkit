use crate::tables;
use crate::{magnitude, spell, to_words, Currency, DigitStyle, Fraction, GregorianDate, Locale};

pub const MAX_DECIMAL_DIGITS: usize = 256;
pub const MAX_DECIMAL_SCALE: u16 = 256;
const MAX_DECIMAL_BYTES: usize = 1024;
const DECIMAL_RANGE_ERROR: &str = "decimal precision exceeds supported range";
const DECIMAL_SYNTAX_ERROR: &str = "invalid decimal string";

fn exponent_notation(text: &str) -> bool {
    let body = text.strip_prefix(['+', '-']).unwrap_or(text);
    let mut marker = body.match_indices(['e', 'E']);
    let Some((index, _)) = marker.next() else {
        return false;
    };
    if marker.next().is_some() {
        return false;
    }
    let mantissa = &body[..index];
    let exponent = body[index + 1..]
        .strip_prefix(['+', '-'])
        .unwrap_or(&body[index + 1..]);
    let mut points = mantissa.split('.');
    let integer = points.next().unwrap_or_default();
    let fraction = points.next();
    let valid_integer =
        !integer.is_empty() && integer.chars().all(|c| c.is_ascii_digit() || c == ',');
    let valid_fraction =
        fraction.is_none_or(|part| !part.is_empty() && part.chars().all(|c| c.is_ascii_digit()));
    let has_digit = mantissa.chars().any(|c| c.is_ascii_digit());
    has_digit
        && valid_integer
        && valid_fraction
        && points.next().is_none()
        && exponent.chars().all(|c| c.is_ascii_digit())
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactDecimal {
    pub negative: bool,
    pub coefficient: String,
    pub scale: u16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MixedFraction {
    pub negative: bool,
    pub whole: u64,
    pub numerator: u64,
    pub denominator: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum NumericRangeEndpoint {
    Decimal(ExactDecimal),
    Fraction { numerator: i64, denominator: u64 },
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Grouping {
    None,
    Indian,
}

fn grouping(value: &str) -> Result<Grouping, String> {
    match value {
        "none" => Ok(Grouping::None),
        "indian" => Ok(Grouping::Indian),
        _ => Err("unsupported grouping".into()),
    }
}

fn digit_value(c: char) -> Option<(u8, bool)> {
    if c.is_ascii_digit() {
        Some((c as u8 - b'0', false))
    } else if ('\u{0be6}'..='\u{0bef}').contains(&c) {
        Some((c as u32 as u8 - 0xe6, true))
    } else {
        None
    }
}

fn digit_style(value: &str) -> Result<DigitStyle, String> {
    DigitStyle::parse(value)
}

pub fn convert_digits(text: &str, to: &str) -> Result<String, String> {
    let to_tamil = match to {
        "latin" => false,
        "tamil" => true,
        _ => return Err("unsupported digit style".into()),
    };
    Ok(text
        .chars()
        .map(|c| match digit_value(c) {
            Some((digit, true)) if !to_tamil => char::from(b'0' + digit),
            Some((digit, false)) if to_tamil => char::from_u32(0x0be6 + u32::from(digit)).unwrap(),
            _ => c,
        })
        .collect())
}

pub fn validate_exact_decimal(value: &ExactDecimal) -> Result<(), String> {
    if value.scale > MAX_DECIMAL_SCALE || value.coefficient.len() > MAX_DECIMAL_DIGITS {
        return Err(DECIMAL_RANGE_ERROR.into());
    }
    let bytes = value.coefficient.as_bytes();
    if bytes.is_empty()
        || bytes.iter().any(|byte| !byte.is_ascii_digit())
        || (bytes.len() > 1 && bytes[0] == b'0')
        || (value.coefficient == "0" && value.negative)
    {
        return Err("invalid decimal value".into());
    }
    Ok(())
}

fn validate_decimal(value: &ExactDecimal) -> Result<(), String> {
    validate_exact_decimal(value)
}

pub fn parse_decimal(
    text: &str,
    source_digits: &str,
    grouping_option: &str,
    allow_mixed: bool,
) -> Result<ExactDecimal, String> {
    if text.len() > MAX_DECIMAL_BYTES {
        return Err(DECIMAL_RANGE_ERROR.into());
    }
    let lexical_digits = text.chars().filter(|c| digit_value(*c).is_some()).count();
    if lexical_digits > MAX_DECIMAL_DIGITS {
        return Err(DECIMAL_RANGE_ERROR.into());
    }
    let source_tamil = match source_digits {
        "latin" => false,
        "tamil" => true,
        _ => return Err("unsupported digit style".into()),
    };
    let grouping = grouping(grouping_option)?;
    if exponent_notation(text) || ["NaN", "nan", "Infinity", "infinity", "inf", "∞"].contains(&text)
    {
        return Err("unsupported numeric notation".into());
    }
    let (negative, body) = match text.chars().next() {
        Some('-') => (true, &text[1..]),
        Some('+') => (false, &text[1..]),
        _ => (false, text),
    };
    if body.is_empty() {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    let mut pieces = body.split('.');
    let integer_part = pieces.next().unwrap_or_default();
    let fraction_part = pieces.next();
    if pieces.next().is_some() {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    let fraction_part = match fraction_part {
        Some(value) if !value.is_empty() => Some(value),
        Some(_) => return Err(DECIMAL_SYNTAX_ERROR.into()),
        None => None,
    };
    if integer_part.is_empty()
        || integer_part
            .chars()
            .next()
            .is_some_and(|c| digit_value(c).is_none())
        || fraction_part.is_some_and(|part| {
            part.chars()
                .next()
                .is_some_and(|c| digit_value(c).is_none())
        })
    {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    let integer_groups: Vec<&str> = integer_part.split(',').collect();
    if integer_groups.len() > 1
        && (grouping != Grouping::Indian
            || integer_groups.iter().any(|part| part.is_empty())
            || integer_groups
                .last()
                .is_some_and(|part| part.chars().count() != 3)
            || integer_groups.first().is_some_and(|part| {
                let max = if integer_groups.len() == 2 { 3 } else { 2 };
                !(1..=max).contains(&part.chars().count())
            })
            || integer_groups
                .iter()
                .skip(1)
                .take(integer_groups.len().saturating_sub(2))
                .any(|part| part.chars().count() != 2))
    {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    if fraction_part.is_some_and(|part| part.contains(',')) {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    let integer_digits = integer_groups.concat();
    let fractional_digits = fraction_part.unwrap_or_default();
    let mut saw_latin = false;
    let mut saw_tamil = false;
    let mut digits = String::with_capacity(integer_digits.len() + fractional_digits.len());
    for c in integer_digits.chars().chain(fractional_digits.chars()) {
        let Some((digit, tamil)) = digit_value(c) else {
            return Err(DECIMAL_SYNTAX_ERROR.into());
        };
        saw_tamil |= tamil;
        saw_latin |= !tamil;
        if !allow_mixed && tamil != source_tamil {
            return Err(DECIMAL_SYNTAX_ERROR.into());
        }
        digits.push(char::from(b'0' + digit));
    }
    if digits.len() > MAX_DECIMAL_DIGITS
        || fractional_digits.chars().count() > usize::from(MAX_DECIMAL_SCALE)
    {
        return Err(DECIMAL_RANGE_ERROR.into());
    }
    if !allow_mixed && ((source_tamil && saw_latin) || (!source_tamil && saw_tamil)) {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    let canonical = digits.trim_start_matches('0');
    let coefficient = if canonical.is_empty() {
        "0".to_owned()
    } else {
        canonical.to_owned()
    };
    Ok(ExactDecimal {
        negative: negative && coefficient != "0",
        coefficient,
        scale: fractional_digits.chars().count() as u16,
    })
}

fn grouped_integer(digits: &str, grouping: Grouping) -> String {
    if grouping == Grouping::None || digits.len() <= 3 {
        return digits.to_owned();
    }
    let mut groups = Vec::new();
    let mut end = digits.len();
    let last_start = end - 3;
    groups.push(&digits[last_start..end]);
    end = last_start;
    while end > 2 {
        groups.push(&digits[end - 2..end]);
        end -= 2;
    }
    if end > 0 {
        groups.push(&digits[..end]);
    }
    groups.reverse();
    groups.join(",")
}

pub fn format_decimal(
    value: &ExactDecimal,
    digits_option: &str,
    grouping_option: &str,
) -> Result<String, String> {
    validate_decimal(value)?;
    let style = digit_style(digits_option)?;
    let grouping = grouping(grouping_option)?;
    let scale = usize::from(value.scale);
    let padded = if value.coefficient.len() <= scale {
        format!(
            "{}{}",
            "0".repeat(scale + 1 - value.coefficient.len()),
            value.coefficient
        )
    } else {
        value.coefficient.clone()
    };
    let split = padded.len() - scale;
    let integer = grouped_integer(&padded[..split], grouping);
    let body = if scale == 0 {
        integer
    } else {
        format!("{integer}.{}", &padded[split..])
    };
    let signed = format!("{}{body}", if value.negative { "-" } else { "" });
    convert_digits(
        &signed,
        if style == DigitStyle::Tamil {
            "tamil"
        } else {
            "latin"
        },
    )
}

fn decimal_integer_fraction(value: &ExactDecimal) -> Result<(u64, String), String> {
    validate_decimal(value)?;
    let scale = usize::from(value.scale);
    let (integer, fraction) = if scale == 0 {
        (&value.coefficient[..], "".to_owned())
    } else if value.coefficient.len() <= scale {
        (
            "0",
            format!(
                "{}{}",
                "0".repeat(scale - value.coefficient.len()),
                value.coefficient
            ),
        )
    } else {
        (
            &value.coefficient[..value.coefficient.len() - scale],
            value.coefficient[value.coefficient.len() - scale..].to_owned(),
        )
    };
    if integer.len() > 9 {
        return Err("expected an integer in the supported range".into());
    }
    let integer = integer
        .parse::<u64>()
        .map_err(|_| "expected an integer in the supported range")?;
    if integer > crate::MAX_INTEGER as u64 {
        return Err("expected an integer in the supported range".into());
    }
    Ok((integer, fraction))
}

pub fn decimal_to_words(value: &ExactDecimal, locale: Locale) -> Result<String, String> {
    let (integer, fractional) = decimal_integer_fraction(value)?;
    if value.scale == 0 {
        return to_words(
            if value.negative {
                -(integer as i64)
            } else {
                integer as i64
            },
            locale,
        );
    }
    let mut output = if value.negative {
        super::negative_prefix(-1)
    } else {
        String::new()
    };
    output.push_str(&to_words(integer as i64, locale)?);
    output.push(' ');
    output.push_str(crate::formats::DECIMAL_POINT_WORD);
    for digit in fractional.chars() {
        output.push(' ');
        output.push_str(&to_words((digit as u8 - b'0') as i64, locale)?);
    }
    Ok(tamil_core::normalize_nfc(&output))
}

pub fn ordinal_to_words(value: u64, locale: Locale) -> Result<String, String> {
    if value == 0 || value > tables::ORDINAL_MAX {
        return Err("expected a positive integer in the supported range".into());
    }
    let rules = match locale {
        Locale::TN => tables::ORDINAL_TN,
        Locale::SL => tables::ORDINAL_SL,
    };
    let mut output = String::new();
    spell(value, tables::ORDINAL_MAIN, rules, 0, &mut output)?;
    Ok(tamil_core::normalize_nfc(&output))
}

pub fn digit_sequence_to_words(
    text: &str,
    source_digits: &str,
    locale: Locale,
) -> Result<String, String> {
    let tamil = match source_digits {
        "latin" => false,
        "tamil" => true,
        _ => return Err("unsupported digit style".into()),
    };
    let chars: Vec<char> = text.chars().collect();
    if chars.is_empty() {
        return Err("invalid digit sequence".into());
    }
    if chars.len() > MAX_DECIMAL_DIGITS {
        return Err("digit sequence exceeds supported range".into());
    }
    let mut words = Vec::with_capacity(chars.len());
    for c in chars {
        let Some((digit, is_tamil)) = digit_value(c) else {
            return Err("invalid digit sequence".into());
        };
        if is_tamil != tamil {
            return Err("invalid digit sequence".into());
        }
        words.push(to_words(i64::from(digit), locale)?);
    }
    Ok(words.join(" "))
}

pub fn format_traditional_integer(value: i64) -> Result<String, String> {
    let absolute = magnitude(value, tables::TRADITIONAL_MAX as i64)
        .map_err(|_| "expected a traditional Tamil integer in the supported range")?;
    let mut output = if value < 0 {
        tables::TRADITIONAL_NEGATIVE.to_owned()
    } else {
        String::new()
    };
    spell(
        absolute,
        tables::TRADITIONAL_MAIN,
        tables::TRADITIONAL,
        0,
        &mut output,
    )?;
    Ok(output)
}

fn parse_under_thousand(text: &str) -> Option<u64> {
    if text.is_empty() {
        return Some(0);
    }
    let mut total = 0u64;
    let mut current = 0u64;
    for c in text.chars() {
        if ('\u{0be7}'..='\u{0bef}').contains(&c) {
            current = current
                .checked_mul(10)?
                .checked_add(u64::from(c as u32 - 0x0be6))?;
        } else {
            let unit = match c {
                '\u{0bf0}' => 10,
                '\u{0bf1}' => 100,
                _ => return None,
            };
            total = total.checked_add(current.max(1).checked_mul(unit)?)?;
            current = 0;
        }
    }
    total.checked_add(current)
}

fn parse_thousands(text: &str) -> Option<u64> {
    if text.is_empty() {
        return Some(0);
    }
    let mut total = 0u64;
    let mut start = 0usize;
    for (index, c) in text.char_indices() {
        if c == '\u{0bf2}' {
            let chunk = parse_under_thousand(&text[start..index])?.max(1);
            total = total.checked_add(chunk.checked_mul(1000)?)?;
            start = index + c.len_utf8();
        }
    }
    total.checked_add(parse_under_thousand(&text[start..])?)
}

fn parse_traditional_magnitude(text: &str) -> Option<u64> {
    if text.is_empty() {
        return None;
    }
    if text == "\u{0be6}" {
        return Some(0);
    }
    // CLDR's million rule has a coefficient of at least ten before the
    // explicit \u{0bf1}\u{0bf2} (100,000) multiplier. Smaller coefficients belong to the
    // ordinary thousands ruleset and are parsed as coefficient × 1,000.
    if let Some(marker) = text.find("\u{0bf1}\u{0bf2}") {
        let (prefix, suffix_with_marker) = text.split_at(marker);
        let suffix = &suffix_with_marker["\u{0bf1}\u{0bf2}".len()..];
        if let Some(coefficient) = parse_under_thousand(prefix).filter(|value| *value >= 10) {
            return coefficient
                .checked_mul(100_000)?
                .checked_add(parse_thousands(suffix)?);
        }
    }
    parse_thousands(text)
}

pub fn parse_traditional_integer(text: &str) -> Result<i64, String> {
    let (negative, body) = text
        .strip_prefix('−')
        .map_or((false, text), |rest| (true, rest));
    let value = parse_traditional_magnitude(body)
        .filter(|value| *value <= tables::TRADITIONAL_MAX)
        .ok_or("invalid canonical traditional Tamil integer")?;
    let signed = if negative {
        -(value as i64)
    } else {
        value as i64
    };
    if format_traditional_integer(signed)? != text {
        return Err("invalid canonical traditional Tamil integer".into());
    }
    Ok(signed)
}

pub fn symbol_info(text: &str) -> Result<crate::SymbolInfo, String> {
    if text.chars().count() != 1 {
        return Err("unsupported Tamil numeric symbol".into());
    }
    tables::SYMBOLS
        .iter()
        .find(|entry| entry.character == text)
        .copied()
        .ok_or_else(|| "unsupported Tamil numeric symbol".into())
}

pub fn parse_fraction_symbol(text: &str) -> Result<Fraction, String> {
    let (negative, symbol) = text
        .strip_prefix('-')
        .map_or((false, text), |rest| (true, rest));
    if symbol.chars().count() != 1 {
        return Err("expected a traditional Tamil fraction symbol".into());
    }
    let info = symbol_info(symbol).map_err(|_| "expected a traditional Tamil fraction symbol")?;
    if info.kind != "fraction" {
        return Err("expected a traditional Tamil fraction symbol".into());
    }
    let (numerator, denominator) = info
        .rational
        .ok_or("expected a traditional Tamil fraction symbol")?;
    Fraction::new(
        if negative { -numerator } else { numerator },
        denominator as i64,
    )
}

pub fn validate_mixed_fraction(value: &MixedFraction) -> Result<(), String> {
    if value.whole > crate::MAX_INTEGER as u64
        || value.denominator == 0
        || value.numerator >= value.denominator
        || value.denominator > crate::MAX_INTEGER as u64
        || (value.negative && value.whole == 0 && value.numerator == 0)
    {
        return Err("invalid mixed fraction".into());
    }
    Ok(())
}

pub fn format_mixed_fraction(value: &MixedFraction, digits_option: &str) -> Result<String, String> {
    validate_mixed_fraction(value)?;
    let style = digit_style(digits_option)?;
    let (numerator, denominator) = if value.numerator == 0 {
        (0, 1)
    } else {
        let common = gcd(value.numerator, value.denominator);
        (value.numerator / common, value.denominator / common)
    };
    let body = if numerator == 0 {
        value.whole.to_string()
    } else {
        format!("{} {numerator}/{denominator}", value.whole)
    };
    convert_digits(
        &format!("{}{body}", if value.negative { "-" } else { "" }),
        if style == DigitStyle::Tamil {
            "tamil"
        } else {
            "latin"
        },
    )
}

fn parse_canonical_unsigned(text: &str, tamil: bool) -> Result<u64, String> {
    if text.is_empty() {
        return Err("invalid mixed fraction".into());
    }
    let mut ascii = String::new();
    for c in text.chars() {
        let Some((digit, is_tamil)) = digit_value(c) else {
            return Err("invalid mixed fraction".into());
        };
        if is_tamil != tamil {
            return Err("invalid mixed fraction".into());
        }
        ascii.push(char::from(b'0' + digit));
    }
    if ascii.len() > 1 && ascii.starts_with('0') {
        return Err("invalid mixed fraction".into());
    }
    ascii
        .parse::<u64>()
        .map_err(|_| "invalid mixed fraction".into())
}

pub fn parse_mixed_fraction(text: &str, source_digits: &str) -> Result<MixedFraction, String> {
    let tamil = match source_digits {
        "latin" => false,
        "tamil" => true,
        _ => return Err("unsupported digit style".into()),
    };
    let (negative, body) = text
        .strip_prefix('-')
        .map_or((false, text), |rest| (true, rest));
    let result = if let Some((whole, fraction)) = body.split_once(' ') {
        if fraction.contains(' ') {
            return Err("invalid mixed fraction".into());
        }
        let (numerator, denominator) = fraction.split_once('/').ok_or("invalid mixed fraction")?;
        if denominator.contains('/') {
            return Err("invalid mixed fraction".into());
        }
        let whole = parse_canonical_unsigned(whole, tamil)?;
        let numerator = parse_canonical_unsigned(numerator, tamil)?;
        let denominator = parse_canonical_unsigned(denominator, tamil)?;
        if denominator == 0
            || numerator == 0
            || numerator >= denominator
            || gcd(numerator, denominator) != 1
        {
            return Err("invalid mixed fraction".into());
        }
        MixedFraction {
            negative,
            whole,
            numerator,
            denominator,
        }
    } else {
        if body.contains('/') {
            return Err("invalid mixed fraction".into());
        }
        MixedFraction {
            negative,
            whole: parse_canonical_unsigned(body, tamil)?,
            numerator: 0,
            denominator: 1,
        }
    };
    if (result.negative && result.whole == 0 && result.numerator == 0)
        || result.whole > crate::MAX_INTEGER as u64
        || result.denominator > crate::MAX_INTEGER as u64
    {
        return Err("invalid mixed fraction".into());
    }
    Ok(result)
}

pub fn parse_percent(
    text: &str,
    source_digits: &str,
    grouping_option: &str,
) -> Result<ExactDecimal, String> {
    let number = text.strip_suffix('%').ok_or(DECIMAL_SYNTAX_ERROR)?;
    if number.ends_with(' ') || number.starts_with(' ') {
        return Err(DECIMAL_SYNTAX_ERROR.into());
    }
    parse_decimal(number, source_digits, grouping_option, false)
}

pub fn format_percent(
    value: &ExactDecimal,
    digits_option: &str,
    grouping_option: &str,
) -> Result<String, String> {
    Ok(format!(
        "{}%",
        format_decimal(value, digits_option, grouping_option)?
    ))
}

fn multiply_decimal_digits(number: &str, multiplier: u64) -> String {
    if multiplier == 0 || number == "0" {
        return "0".into();
    }
    let mut carry = 0u128;
    let mut output = Vec::with_capacity(number.len() + 20);
    for byte in number.bytes().rev() {
        let product = u128::from(byte - b'0') * u128::from(multiplier) + carry;
        output.push((product % 10) as u8 + b'0');
        carry = product / 10;
    }
    while carry > 0 {
        output.push((carry % 10) as u8 + b'0');
        carry /= 10;
    }
    output.reverse();
    String::from_utf8(output).expect("ASCII digits")
}

fn shift_scale(value: &ExactDecimal, shift: i32) -> Result<ExactDecimal, String> {
    validate_decimal(value)?;
    let mut result = value.clone();
    if shift >= 0 {
        let shift = shift as u16;
        result.scale = result.scale.checked_add(shift).ok_or(DECIMAL_RANGE_ERROR)?;
    } else {
        let places = (-shift) as usize;
        if usize::from(result.scale) >= places {
            result.scale -= places as u16;
        } else {
            let zeros = places - usize::from(result.scale);
            if result.coefficient == "0" {
                result.scale = 0;
            } else {
                if result.coefficient.len() + zeros > MAX_DECIMAL_DIGITS {
                    return Err(DECIMAL_RANGE_ERROR.into());
                }
                result.coefficient.push_str(&"0".repeat(zeros));
                result.scale = 0;
            }
        }
    }
    validate_decimal(&result)?;
    Ok(result)
}

pub fn ratio_to_percent(value: &ExactDecimal) -> Result<ExactDecimal, String> {
    shift_scale(value, -2)
}
pub fn percent_to_ratio(value: &ExactDecimal) -> Result<ExactDecimal, String> {
    shift_scale(value, 2)
}

fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

fn compare_unsigned_digits(left: &str, right: &str) -> std::cmp::Ordering {
    let left = left.trim_start_matches('0');
    let right = right.trim_start_matches('0');
    let left = if left.is_empty() { "0" } else { left };
    let right = if right.is_empty() { "0" } else { right };
    left.len().cmp(&right.len()).then_with(|| left.cmp(right))
}

fn compare_magnitude_decimal(a: &ExactDecimal, b: &ExactDecimal) -> std::cmp::Ordering {
    let scale = a.scale.max(b.scale);
    let mut left = a.coefficient.clone();
    let mut right = b.coefficient.clone();
    left.push_str(&"0".repeat(usize::from(scale - a.scale)));
    right.push_str(&"0".repeat(usize::from(scale - b.scale)));
    compare_unsigned_digits(&left, &right)
}

fn compare_signed_decimal(
    a: &ExactDecimal,
    b: &ExactDecimal,
) -> Result<std::cmp::Ordering, String> {
    validate_decimal(a)?;
    validate_decimal(b)?;
    Ok(match (a.negative, b.negative) {
        (true, false) => std::cmp::Ordering::Less,
        (false, true) => std::cmp::Ordering::Greater,
        (false, false) => compare_magnitude_decimal(a, b),
        (true, true) => compare_magnitude_decimal(b, a),
    })
}

fn compare_decimal_fraction(
    decimal: &ExactDecimal,
    numerator: i64,
    denominator: u64,
) -> Result<std::cmp::Ordering, String> {
    validate_decimal(decimal)?;
    if denominator == 0
        || numerator.unsigned_abs() > crate::MAX_INTEGER as u64
        || denominator > crate::MAX_INTEGER as u64
    {
        return Err("invalid numeric range".into());
    }
    let fraction_negative = numerator < 0;
    if decimal.negative != fraction_negative {
        if decimal.coefficient == "0" {
            return Ok(if fraction_negative {
                std::cmp::Ordering::Greater
            } else {
                std::cmp::Ordering::Less
            });
        }
        return Ok(if decimal.negative {
            std::cmp::Ordering::Less
        } else {
            std::cmp::Ordering::Greater
        });
    }
    let left = multiply_decimal_digits(&decimal.coefficient, denominator);
    let right = format!(
        "{}{}",
        numerator.unsigned_abs(),
        "0".repeat(usize::from(decimal.scale))
    );
    let magnitude = compare_unsigned_digits(&left, &right);
    Ok(if decimal.negative {
        magnitude.reverse()
    } else {
        magnitude
    })
}

fn compare_endpoints(
    a: &NumericRangeEndpoint,
    b: &NumericRangeEndpoint,
) -> Result<std::cmp::Ordering, String> {
    match (a, b) {
        (NumericRangeEndpoint::Decimal(a), NumericRangeEndpoint::Decimal(b)) => {
            compare_signed_decimal(a, b)
        }
        (
            NumericRangeEndpoint::Fraction {
                numerator: an,
                denominator: ad,
            },
            NumericRangeEndpoint::Fraction {
                numerator: bn,
                denominator: bd,
            },
        ) => {
            if *ad == 0
                || *bd == 0
                || an.unsigned_abs() > crate::MAX_INTEGER as u64
                || *ad > crate::MAX_INTEGER as u64
                || bn.unsigned_abs() > crate::MAX_INTEGER as u64
                || *bd > crate::MAX_INTEGER as u64
            {
                return Err("invalid numeric range".into());
            }
            let left = i128::from(*an) * i128::from(*bd);
            let right = i128::from(*bn) * i128::from(*ad);
            Ok(left.cmp(&right))
        }
        (
            NumericRangeEndpoint::Decimal(d),
            NumericRangeEndpoint::Fraction {
                numerator,
                denominator,
            },
        ) => compare_decimal_fraction(d, *numerator, *denominator),
        (
            NumericRangeEndpoint::Fraction {
                numerator,
                denominator,
            },
            NumericRangeEndpoint::Decimal(d),
        ) => Ok(compare_decimal_fraction(d, *numerator, *denominator)?.reverse()),
    }
}

fn render_endpoint(value: &NumericRangeEndpoint, style: DigitStyle) -> Result<String, String> {
    match value {
        NumericRangeEndpoint::Decimal(value) => format_decimal(
            value,
            if style == DigitStyle::Tamil {
                "tamil"
            } else {
                "latin"
            },
            "none",
        ),
        NumericRangeEndpoint::Fraction {
            numerator,
            denominator,
        } => {
            let fraction = Fraction::new(
                *numerator,
                i64::try_from(*denominator).map_err(|_| "invalid numeric range")?,
            )?;
            Ok(crate::format_fraction(fraction, style))
        }
    }
}

pub fn format_numeric_range(
    start: &NumericRangeEndpoint,
    end: &NumericRangeEndpoint,
    start_inclusive: bool,
    end_inclusive: bool,
    separator: &str,
    digits_option: &str,
) -> Result<String, String> {
    validate_numeric_range(start, end, separator)?;
    let style = digit_style(digits_option)?;
    Ok(format!(
        "{}{}{}{}{}",
        if start_inclusive { '[' } else { '(' },
        render_endpoint(start, style)?,
        separator,
        render_endpoint(end, style)?,
        if end_inclusive { ']' } else { ')' }
    ))
}

pub fn validate_numeric_range(
    start: &NumericRangeEndpoint,
    end: &NumericRangeEndpoint,
    separator: &str,
) -> Result<(), String> {
    if separator.is_empty()
        || separator.chars().count() > 8
        || compare_endpoints(start, end).map_err(|_| "invalid numeric range")?
            == std::cmp::Ordering::Greater
    {
        return Err("invalid numeric range".into());
    }
    Ok(())
}

fn decimal_to_minor(value: &ExactDecimal) -> Result<i64, String> {
    validate_decimal(value)?;
    if value.scale > 2 {
        return Err("currency amount has more than two fractional digits".into());
    }
    let mut coefficient = value.coefficient.clone();
    coefficient.push_str(&"0".repeat(2 - usize::from(value.scale)));
    let value = coefficient
        .parse::<u64>()
        .map_err(|_| "currency amount exceeds supported range")?;
    if value > crate::MAX_MINOR as u64 {
        return Err("currency amount exceeds supported range".into());
    }
    let signed = i64::try_from(value).map_err(|_| "currency amount exceeds supported range")?;
    Ok(signed)
}

pub fn validate_currency_decimal(value: &ExactDecimal) -> Result<(), String> {
    decimal_to_minor(value).map(|_| ())
}

pub fn format_currency_decimal(
    value: &ExactDecimal,
    currency: Currency,
    locale: Locale,
) -> Result<String, String> {
    let minor = decimal_to_minor(value)?;
    let minor = if value.negative { -minor } else { minor };
    crate::format_currency(minor, currency, locale)
}

pub fn currency_decimal_to_words(
    value: &ExactDecimal,
    currency: Currency,
    locale: Locale,
) -> Result<String, String> {
    let minor = decimal_to_minor(value)?;
    let minor = if value.negative { -minor } else { minor };
    crate::currency_to_words(minor, currency, locale)
}

fn leap_year(year: i64) -> bool {
    year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
}
fn month_length(year: i64, month: u32) -> u32 {
    if month == 2 && leap_year(year) {
        29
    } else {
        [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month as usize - 1]
    }
}
fn days_before_year(year: i64) -> i64 {
    let y = year - 1;
    365 * y + y / 4 - y / 100 + y / 400
}
pub(crate) fn ordinal_day(date: GregorianDate) -> i64 {
    let mut days = days_before_year(date.year());
    for month in 1..date.month() {
        days += i64::from(month_length(date.year(), month));
    }
    days + i64::from(date.day()) - 1
}
pub(crate) fn date_from_ordinal(mut day: i64) -> Result<GregorianDate, String> {
    let max = days_before_year(10000);
    if day < 0 || day >= max {
        return Err("Gregorian date arithmetic out of range".into());
    }
    let mut lo = 1i64;
    let mut hi = 10000i64;
    while lo + 1 < hi {
        let mid = (lo + hi) / 2;
        if days_before_year(mid) <= day {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    let year = lo;
    day -= days_before_year(year);
    let mut month = 1u32;
    while day >= i64::from(month_length(year, month)) {
        day -= i64::from(month_length(year, month));
        month += 1;
    }
    GregorianDate::new(year, i64::from(month), day + 1)
        .map_err(|_| "Gregorian date arithmetic out of range".into())
}

pub fn validate_gregorian_date(year: i64, month: i64, day: i64) -> Result<bool, String> {
    GregorianDate::new(year, month, day).map(|_| true)
}

pub fn parse_gregorian_date(text: &str) -> Result<GregorianDate, String> {
    if text.len() != 10
        || text.as_bytes().get(4) != Some(&b'-')
        || text.as_bytes().get(7) != Some(&b'-')
        || text
            .bytes()
            .enumerate()
            .any(|(i, b)| i != 4 && i != 7 && !b.is_ascii_digit())
    {
        return Err("invalid Gregorian date".into());
    }
    let year = text[..4]
        .parse::<i64>()
        .map_err(|_| "invalid Gregorian date")?;
    let month = text[5..7]
        .parse::<i64>()
        .map_err(|_| "invalid Gregorian date")?;
    let day = text[8..10]
        .parse::<i64>()
        .map_err(|_| "invalid Gregorian date")?;
    GregorianDate::new(year, month, day)
}

pub fn weekday(date: GregorianDate) -> &'static str {
    const DAYS: [&str; 7] = [
        "sunday",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
    ];
    DAYS[date.weekday()]
}

pub fn add_gregorian_date(
    date: GregorianDate,
    unit: &str,
    amount: i64,
    overflow: &str,
) -> Result<GregorianDate, String> {
    match overflow {
        "reject" | "clamp" => {}
        _ => return Err("unsupported date overflow policy".into()),
    }
    match unit {
        "days" => {
            let target = ordinal_day(date)
                .checked_add(amount)
                .ok_or("Gregorian date arithmetic out of range")?;
            date_from_ordinal(target)
        }
        "months" | "years" => {
            let delta = if unit == "years" {
                amount
                    .checked_mul(12)
                    .ok_or("Gregorian date arithmetic out of range")?
            } else {
                amount
            };
            let index = (date.year() - 1)
                .checked_mul(12)
                .and_then(|n| n.checked_add(i64::from(date.month() - 1)))
                .and_then(|n| n.checked_add(delta))
                .ok_or("Gregorian date arithmetic out of range")?;
            if !(0..(9999 * 12)).contains(&index) {
                return Err("Gregorian date arithmetic out of range".into());
            }
            let year = index / 12 + 1;
            let month = (index % 12 + 1) as u32;
            let last = month_length(year, month);
            let day = if date.day() <= last {
                date.day()
            } else if overflow == "clamp" {
                last
            } else {
                return Err("Gregorian date arithmetic out of range".into());
            };
            GregorianDate::new(year, i64::from(month), i64::from(day))
                .map_err(|_| "Gregorian date arithmetic out of range".into())
        }
        _ => Err("unsupported date unit".into()),
    }
}

pub fn date_difference(start: GregorianDate, end: GregorianDate) -> i64 {
    ordinal_day(end) - ordinal_day(start)
}

pub fn date_interval(
    start: GregorianDate,
    end: GregorianDate,
) -> Result<(String, String, i64), String> {
    let days = date_difference(start, end);
    if days < 0 {
        return Err("invalid date interval".into());
    }
    Ok((iso_date(start), iso_date(end), days + 1))
}

pub fn iso_date(date: GregorianDate) -> String {
    format!("{:04}-{:02}-{:02}", date.year(), date.month(), date.day())
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn exact_decimal_string_roundtrip(raw in prop::collection::vec(0u8..10, 1..=256), scale in 0u16..=256, negative in any::<bool>(), tamil in any::<bool>()) {
            let lexical: String = raw.iter().map(|digit| char::from(b'0' + *digit)).collect();
            let coefficient = lexical.trim_start_matches('0');
            let coefficient = if coefficient.is_empty() { "0" } else { coefficient };
            let negative = negative && coefficient != "0";
            // A required integer zero plus 256 fractional digits exceeds the
            // textual digit cap; all other representable exact values roundtrip.
            let formatted_digits = if coefficient.len() > usize::from(scale) { coefficient.len() } else { usize::from(scale) + 1 };
            prop_assume!(formatted_digits <= MAX_DECIMAL_DIGITS);
            let value = ExactDecimal { negative, coefficient: coefficient.to_owned(), scale };
            let style = if tamil { "tamil" } else { "latin" };
            let formatted = format_decimal(&value, style, "none").unwrap();
            prop_assert_eq!(parse_decimal(&formatted, style, "none", false).unwrap(), value);
        }

        #[test]
        fn root_traditional_integer_roundtrip(value in -99_999_999i64..=99_999_999i64) {
            let formatted = format_traditional_integer(value).unwrap();
            prop_assert_eq!(parse_traditional_integer(&formatted).unwrap(), value);
        }

        #[test]
        fn major_currency_decimal_matches_minor_unit_api(value in -crate::MAX_MINOR..=crate::MAX_MINOR, sl in any::<bool>(), lkr in any::<bool>()) {
            let magnitude = value.unsigned_abs();
            let amount = format!("{}.{:02}", magnitude / 100, magnitude % 100);
            let exact = parse_decimal(&amount, "latin", "none", false).unwrap();
            prop_assert_eq!(decimal_to_minor(&exact).unwrap(), magnitude as i64);
            let signed = if value < 0 && magnitude != 0 { ExactDecimal { negative: true, ..exact.clone() } } else { exact };
            let currency = if lkr { Currency::LKR } else { Currency::INR };
            let locale = if sl { Locale::SL } else { Locale::TN };
            prop_assert_eq!(format_currency_decimal(&signed, currency, locale).unwrap(), crate::format_currency(value, currency, locale).unwrap());
        }

        #[test]
        fn mixed_fraction_canonical_roundtrip(whole in 0u64..=999_999_999, denominator in 1u64..=999_999_999, raw_numerator in 0u64..=999_999_999, negative_input in any::<bool>()) {
            let numerator = raw_numerator % denominator;
            let negative = negative_input && (whole != 0 || numerator != 0);
            let value = MixedFraction { negative, whole, numerator, denominator };
            let formatted = format_mixed_fraction(&value, "latin").unwrap();
            let parsed = parse_mixed_fraction(&formatted, "latin").unwrap();
            let common = if numerator == 0 { denominator } else { gcd(numerator,denominator) };
            prop_assert_eq!(parsed, MixedFraction { negative, whole, numerator: numerator/common, denominator: denominator/common });
        }

        #[test]
        fn ratio_percent_scale_shift_is_reversible(raw in prop::collection::vec(0u8..10, 1..=254), scale in 2u16..=254, negative in any::<bool>()) {
            let lexical: String = raw.iter().map(|digit| char::from(b'0' + *digit)).collect();
            let coefficient = lexical.trim_start_matches('0');
            let coefficient = if coefficient.is_empty() { "0" } else { coefficient };
            let value = ExactDecimal { negative: negative && coefficient != "0", coefficient: coefficient.to_owned(), scale };
            let roundtrip = ratio_to_percent(&percent_to_ratio(&value).unwrap()).unwrap();
            prop_assert_eq!(roundtrip, value);
        }

        #[test]
        fn day_addition_and_difference_are_inverse(ordinal in 0i64..=3_652_058, amount in -366i64..=366) {
            let Some(target_ordinal) = ordinal.checked_add(amount).filter(|value| (0..=3_652_058).contains(value)) else { return Ok(()); };
            let start = date_from_ordinal(ordinal).unwrap();
            let end = date_from_ordinal(target_ordinal).unwrap();
            let calculated = add_gregorian_date(start, "days", amount, "reject").unwrap();
            prop_assert_eq!(calculated, end);
            prop_assert_eq!(date_difference(start,calculated), amount);
        }
    }
}
