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
];

fn string(value: &Value) -> Result<&str, String> {
    value
        .as_str()
        .ok_or_else(|| "expected a string input".to_owned())
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
