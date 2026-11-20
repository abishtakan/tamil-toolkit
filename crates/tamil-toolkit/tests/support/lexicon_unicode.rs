//! Synthetic scalar fixtures only; these records grant no linguistic or source approval.
use serde_json::Value;

pub fn fixture(id: &str) -> Value {
    let row = include_str!("../../../../tests/reference/lexicon/runtime/synthetic_unicode.jsonl")
        .lines()
        .map(|line| serde_json::from_str::<Value>(line).expect("valid synthetic Unicode fixture"))
        .find(|row| row["id"] == id)
        .expect("known synthetic Unicode fixture");
    let scalars: Vec<u32> = row["value"]
        .as_str()
        .unwrap()
        .chars()
        .map(u32::from)
        .collect();
    let expected: Vec<u32> = row["scalars"]
        .as_array()
        .unwrap()
        .iter()
        .map(|cp| u32::try_from(cp.as_u64().unwrap()).unwrap())
        .collect();
    assert_eq!(scalars, expected, "fixture scalar sequence");
    assert!(!row["reason"].as_str().unwrap().is_empty());
    assert_eq!(
        serde_json::from_str::<String>(row["json"].as_str().unwrap()).unwrap(),
        row["value"].as_str().unwrap()
    );
    row
}
