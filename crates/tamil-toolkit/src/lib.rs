//! Unified entry point. Planned modules expose no invented algorithms.
#![forbid(unsafe_code)]

pub use tamil_codec as codec;
pub use tamil_collate as collate;
pub use tamil_core as core;
pub use tamil_dialect as dialect;
pub use tamil_hyphen as hyphen;
pub use tamil_morph as morph;
pub use tamil_norm as norm;
pub use tamil_numerals as numerals;
pub use tamil_punarchi as punarchi;
pub use tamil_yaappu as yaappu;

use serde_json::{json, Value};

pub const OPERATIONS: &[&str] = &[
    "get_letters",
    "normalize_nfc",
    "normalize_nfd",
    "split_uyirmei",
    "compose_uyirmei",
    "inspect_tamil_string",
    "compare",
    "sort_words",
    "sort_key",
    "search_key",
    "to_words",
    "format_currency",
    "currency_to_words",
    "bamini_to_unicode",
    "unicode_to_bamini",
    "format_fraction",
    "fraction_to_words",
    "fraction_symbol",
    "format_date",
];

fn string(value: &Value) -> Result<&str, String> {
    value
        .as_str()
        .ok_or_else(|| "expected a string input".to_owned())
}

fn integer(value: &Value, maximum: i64) -> Result<i64, String> {
    // JSON.stringify emits 1 for 1.0, while other serializers keep the .0.
    // Parse whole values identically without floating-point money arithmetic.
    let error = || numerals::INTEGER_ERROR.to_owned();
    let number = value.as_number().ok_or_else(error)?.to_string();
    let parsed = number
        .strip_suffix(".0")
        .unwrap_or(&number)
        .parse::<i64>()
        .map_err(|_| error())?;
    if parsed.unsigned_abs() > maximum as u64 {
        Err(error())
    } else {
        Ok(parsed)
    }
}

fn locale(input: &Value) -> Result<numerals::Locale, String> {
    match input.get("locale") {
        None => Ok(numerals::Locale::TN),
        Some(value) => numerals::Locale::parse(value.as_str().ok_or("unsupported locale")?),
    }
}

fn digit_style(input: &Value) -> Result<numerals::DigitStyle, String> {
    match input.get("digits") {
        None => Ok(numerals::DigitStyle::Latin),
        Some(value) => {
            numerals::DigitStyle::parse(value.as_str().ok_or("unsupported digit style")?)
        }
    }
}

/// Shared dispatcher used by every binding and the oracle CLI.
pub fn execute(request: &Value) -> Result<Value, String> {
    let input = request.get("input").ok_or("missing input")?;
    match request
        .get("op")
        .and_then(Value::as_str)
        .ok_or("missing op")?
    {
        "get_letters" => Ok(json!(core::get_letters(string(input)?))),
        "normalize_nfc" => Ok(json!(norm::normalize_nfc(string(input)?))),
        "normalize_nfd" => Ok(json!(norm::normalize_nfd(string(input)?))),
        "split_uyirmei" => core::split_uyirmei(string(input)?).map(|parts| json!(parts)),
        "compose_uyirmei" => {
            core::compose_uyirmei(string(&input["mei"])?, string(&input["uyir"])?).map(|s| json!(s))
        }
        "inspect_tamil_string" => Ok(json!(core::inspect_tamil_string(string(input)?))),
        "compare" => {
            let order = collate::compare(string(&input["left"])?, string(&input["right"])?);
            Ok(json!(match order {
                std::cmp::Ordering::Less => -1,
                std::cmp::Ordering::Equal => 0,
                std::cmp::Ordering::Greater => 1,
            }))
        }
        "sort_words" => {
            let words = input
                .as_array()
                .ok_or("expected an array of strings")?
                .iter()
                .map(|value| string(value).map(str::to_owned))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(json!(collate::sort_words(&words)))
        }
        "sort_key" => Ok(json!(collate::sort_key(string(input)?))),
        "search_key" => Ok(json!(collate::search_key(string(input)?))),
        "to_words" => {
            let value = integer(&input["value"], numerals::MAX_INTEGER)?;
            numerals::to_words(value, locale(input)?).map(|words| json!(words))
        }
        "format_currency" | "currency_to_words" => {
            let value = integer(&input["amount_minor"], numerals::MAX_MINOR)?;
            let locale = locale(input)?;
            let currency = numerals::Currency::parse(
                input["currency"].as_str().ok_or("unsupported currency")?,
            )?;
            if request["op"] == "format_currency" {
                numerals::format_currency(value, currency, locale).map(|s| json!(s))
            } else {
                numerals::currency_to_words(value, currency, locale).map(|s| json!(s))
            }
        }
        "bamini_to_unicode" => {
            let text = string(&input["text"])?;
            let policy = match input.get("errors") {
                None => codec::ErrorPolicy::Strict,
                Some(value) => codec::ErrorPolicy::parse(
                    value.as_str().ok_or("unsupported codec error policy")?,
                )?,
            };
            codec::bamini_to_unicode(text, policy).map(|text| json!(text))
        }
        "unicode_to_bamini" => {
            codec::unicode_to_bamini(string(&input["text"])?).map(|text| json!(text))
        }
        "format_fraction" | "fraction_to_words" | "fraction_symbol" => {
            let value = numerals::Fraction::new(
                integer(&input["numerator"], numerals::MAX_INTEGER)?,
                integer(&input["denominator"], numerals::MAX_INTEGER)?,
            )?;
            match request["op"].as_str().expect("validated op") {
                "format_fraction" => {
                    Ok(json!(numerals::format_fraction(value, digit_style(input)?)))
                }
                "fraction_to_words" => {
                    numerals::fraction_to_words(value, locale(input)?).map(|text| json!(text))
                }
                _ => numerals::fraction_symbol(value).map(|text| json!(text)),
            }
        }
        "format_date" => {
            let component = |key: &str| {
                integer(&input[key], 9999).map_err(|_| numerals::INVALID_DATE.to_owned())
            };
            let date = numerals::GregorianDate::new(
                component("year")?,
                component("month")?,
                component("day")?,
            )?;
            let locale = locale(input)?;
            let style = match input.get("style") {
                None => numerals::DateStyle::Long,
                Some(value) => {
                    numerals::DateStyle::parse(value.as_str().ok_or("unsupported date style")?)?
                }
            };
            Ok(json!(numerals::format_date(
                date,
                locale,
                style,
                digit_style(input)?
            )))
        }
        op => Err(format!("unsupported operation: {op}")),
    }
}

pub fn execute_json(request: &str) -> Result<String, String> {
    let request = serde_json::from_str(request).map_err(|e| e.to_string())?;
    execute(&request).map(|result| result.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn errors_are_explicit() {
        for request in [
            json!({}),
            json!({"op":"to_words","input":1000}),
            json!({"op":"get_letters","input":1}),
        ] {
            assert!(execute(&request).is_err());
        }
        assert!(execute_json("invalid JSON").is_err());
    }
}
