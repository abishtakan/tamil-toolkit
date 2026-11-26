use serde_json::Value;

pub fn rows() -> impl Iterator<Item = Value> {
    include_str!("../../../../tests/golden/tokenize_v01.jsonl")
        .lines()
        .map(|line| serde_json::from_str(line).expect("valid planned vector"))
}
