#![allow(dead_code)]

use serde_json::Value;

/// Load all rows from `tests/golden/punarchi_nannool.jsonl`.
pub fn load_punarchi_vectors() -> Vec<Value> {
    let raw = include_str!("../../../../tests/golden/punarchi_nannool.jsonl");
    raw.lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| serde_json::from_str(line).expect("valid punarchi golden vector JSON"))
        .collect()
}

/// Filter punarchi golden vectors by operation name (`punarchi_join`, `punarchi_split_candidates`, `punarchi_rules`).
pub fn vectors_by_op(op: &str) -> Vec<Value> {
    load_punarchi_vectors()
        .into_iter()
        .filter(|row| row.get("op").and_then(Value::as_str) == Some(op))
        .collect()
}

/// Filter punarchi golden vectors by tag (e.g. `"prereq"`, `"uyireeru"`, `"meyyeeru"`, `"urupu"`, `"split"`, `"context"`, `"error"`).
pub fn vectors_by_tag(tag: &str) -> Vec<Value> {
    load_punarchi_vectors()
        .into_iter()
        .filter(|row| {
            row.get("tags")
                .and_then(Value::as_array)
                .is_some_and(|tags| tags.iter().any(|t| t.as_str() == Some(tag)))
        })
        .collect()
}

/// Filter punarchi golden vectors by both operation and tag.
pub fn vectors_by_op_and_tag(op: &str, tag: &str) -> Vec<Value> {
    load_punarchi_vectors()
        .into_iter()
        .filter(|row| {
            row.get("op").and_then(Value::as_str) == Some(op)
                && row
                    .get("tags")
                    .and_then(Value::as_array)
                    .is_some_and(|tags| tags.iter().any(|t| t.as_str() == Some(tag)))
        })
        .collect()
}
