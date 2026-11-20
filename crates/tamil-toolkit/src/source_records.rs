//! Runtime bucket routing and exact lookup over owner-supplied historical source records.
//!
//! This module serves unverified, rights-unresolved owner-supplied records without
//! inferring linguistic acceptance, regional scope, or relicensing terms.

use std::collections::HashSet;

use serde_json::{json, Map, Value};
use sha2::{Digest, Sha256};

/// Bucket and lookup contract schema version.
pub const SCHEMA_VERSION: u64 = 1;

/// Maximum accepted UTF-8 query length in bytes (no silent truncation).
pub const MAX_QUERY_BYTES: usize = 65_536;

/// Maximum accepted pagination offset.
pub const MAX_OFFSET: u64 = 1_000_000;

/// Minimum accepted pagination limit.
pub const MIN_LIMIT: u64 = 1;

/// Maximum accepted pagination limit.
pub const MAX_LIMIT: u64 = 100;

/// Fixed data status reported on every source-record lookup response.
pub const DATA_STATUS: &str = "owner_supplied_unverified";

/// Fixed rights status reported on every source-record lookup response.
pub const RIGHTS_STATUS: &str = "unresolved";

/// Error returned for invalid `query` values.
pub const ERR_INVALID_QUERY: &str = "lexicon source: invalid query";

/// Error returned for invalid bucket payloads, record invariants, or lookup options.
pub const ERR_INVALID_BUCKET_OR_OPTIONS: &str = "lexicon source: invalid bucket or options";

/// Computes the bucket byte index (`0..=255`) from an already NFC-normalized key.
pub fn bucket_index_for_normalized(normalized_key: &str) -> u8 {
    let digest = Sha256::digest(normalized_key.as_bytes());
    digest[0]
}

/// Computes the two-character lowercase hexadecimal bucket ID from an already NFC-normalized key.
pub fn bucket_for_normalized(normalized_key: &str) -> String {
    format!("{:02x}", bucket_index_for_normalized(normalized_key))
}

/// Returns `true` if `bucket` is exactly two lowercase hexadecimal ASCII digits.
pub fn is_valid_bucket_id(bucket: &str) -> bool {
    let bytes = bucket.as_bytes();
    bytes.len() == 2 && bytes.iter().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

/// Returns `true` if `name` is a plain `.csv` filename without path components or control characters.
pub fn is_plain_csv_filename(name: &str) -> bool {
    !name.is_empty()
        && name.len() > 4
        && name.ends_with(".csv")
        && !name.starts_with('.')
        && !name.contains("..")
        && !name.contains(['/', '\\', ':', '\0'])
        && !name.chars().any(char::is_control)
}

fn validate_query(value: &Value) -> Result<&str, String> {
    let query = value.as_str().ok_or_else(|| ERR_INVALID_QUERY.to_owned())?;
    if query.is_empty() || query.len() > MAX_QUERY_BYTES {
        return Err(ERR_INVALID_QUERY.to_owned());
    }
    Ok(query)
}

fn exact_object<'a>(
    value: &'a Value,
    required_keys: &[&str],
) -> Result<&'a Map<String, Value>, String> {
    let obj = value
        .as_object()
        .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
    if obj.len() != required_keys.len() || required_keys.iter().any(|key| !obj.contains_key(*key)) {
        return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
    }
    Ok(obj)
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_source_bucket"`.
///
/// Validates a UTF-8 query string (`1..=65536` bytes), applies canonical NFC
/// normalization without trimming or stripping joiners, and computes the
/// two-hex-digit SHA-256 bucket prefix.
pub fn execute_bucket(input: &Value) -> Result<Value, String> {
    let query = validate_query(input)?;
    let normalized_query = tamil_norm::normalize_nfc(query);
    let bucket = bucket_for_normalized(&normalized_query);
    Ok(json!({
        "query": query,
        "normalized_query": normalized_query,
        "bucket": bucket,
    }))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_source_lookup"`.
///
/// Validates exact request shape, query, pagination bounds, bucket metadata,
/// every record's shape, NFC `lookup_key`, bucket assignment, and `(source_file,
/// source_row)` locator uniqueness before returning any match.
pub fn execute_lookup(input: &Value) -> Result<Value, String> {
    let obj = exact_object(input, &["query", "bucket", "offset", "limit"])?;

    let query = validate_query(&obj["query"])?;
    let normalized_query = tamil_norm::normalize_nfc(query);
    let expected_bucket = bucket_for_normalized(&normalized_query);

    let offset = obj["offset"]
        .as_u64()
        .filter(|&v| v <= MAX_OFFSET)
        .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
    let limit = obj["limit"]
        .as_u64()
        .filter(|&v| (MIN_LIMIT..=MAX_LIMIT).contains(&v))
        .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;

    let bucket_obj = exact_object(&obj["bucket"], &["schema_version", "bucket", "records"])?;
    if bucket_obj["schema_version"].as_u64() != Some(SCHEMA_VERSION) {
        return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
    }
    let bucket_id = bucket_obj["bucket"]
        .as_str()
        .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
    if !is_valid_bucket_id(bucket_id) || bucket_id != expected_bucket {
        return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
    }

    let records = bucket_obj["records"]
        .as_array()
        .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;

    let mut seen_locators: HashSet<(&str, u64)> = HashSet::with_capacity(records.len());
    let mut matches: Vec<(&str, u64, &Value)> = Vec::new();

    for rec_val in records {
        let rec_obj = exact_object(
            rec_val,
            &["source_file", "source_row", "lookup_key", "fields"],
        )?;

        let source_file = rec_obj["source_file"]
            .as_str()
            .filter(|name| is_plain_csv_filename(name))
            .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
        let source_row = rec_obj["source_row"]
            .as_u64()
            .filter(|&row| row >= 1)
            .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;

        if !seen_locators.insert((source_file, source_row)) {
            return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
        }

        let lookup_key = rec_obj["lookup_key"]
            .as_str()
            .filter(|key| !key.is_empty())
            .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
        if tamil_norm::normalize_nfc(lookup_key) != lookup_key {
            return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
        }
        if bucket_for_normalized(lookup_key) != bucket_id {
            return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
        }

        let fields = rec_obj["fields"]
            .as_object()
            .ok_or_else(|| ERR_INVALID_BUCKET_OR_OPTIONS.to_owned())?;
        if fields.values().any(|val| !val.is_string()) {
            return Err(ERR_INVALID_BUCKET_OR_OPTIONS.to_owned());
        }

        if lookup_key == normalized_query {
            matches.push((source_file, source_row, rec_val));
        }
    }

    matches.sort_unstable_by(|a, b| (a.0, a.1).cmp(&(b.0, b.1)));

    let total = matches.len();
    let status = if total > 0 { "matched" } else { "not_found" };
    let start = usize::try_from(offset).unwrap_or(usize::MAX).min(total);
    let end = start.saturating_add(limit as usize).min(total);
    let page: Vec<Value> = matches[start..end]
        .iter()
        .map(|(_, _, val)| (*val).clone())
        .collect();

    Ok(json!({
        "query": query,
        "normalized_query": normalized_query,
        "status": status,
        "data_status": DATA_STATUS,
        "rights_status": RIGHTS_STATUS,
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": page,
    }))
}
