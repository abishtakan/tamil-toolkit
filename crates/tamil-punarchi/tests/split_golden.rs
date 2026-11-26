mod support;

use serde_json::Value;
use tamil_punarchi::{punarchi_split_candidates, PunarchiError, PunarchiProfile};

fn eval_punarchi_split_candidates(input: &Value) -> Result<Value, PunarchiError> {
    let surface = input
        .get("surface")
        .and_then(Value::as_str)
        .ok_or(PunarchiError::ExpectedStringInput)?;
    let profile = match input.get("profile") {
        None => PunarchiProfile::default(),
        Some(v) => PunarchiProfile::parse(v.as_str().ok_or(PunarchiError::ExpectedProfileString)?)?,
    };
    let poetic = match input.get("poetic") {
        None => false,
        Some(v) => v.as_bool().ok_or(PunarchiError::ExpectedPoeticBoolean)?,
    };

    let result = punarchi_split_candidates(surface, profile, poetic)?;
    Ok(serde_json::to_value(&result).expect("serialize Vec<SplitCandidate>"))
}

#[test]
fn golden_split_candidates_vectors() {
    let vectors = support::vectors_by_op("punarchi_split_candidates");
    assert!(
        !vectors.is_empty(),
        "expected punarchi_split_candidates golden vectors"
    );

    let split_vectors: Vec<&Value> = vectors
        .iter()
        .filter(|row| {
            row.get("tags")
                .and_then(Value::as_array)
                .is_some_and(|tags| tags.iter().any(|t| t.as_str() == Some("split")))
        })
        .collect();
    assert!(
        !split_vectors.is_empty(),
        "expected at least one split-tagged punarchi_split_candidates vector"
    );

    for row in &vectors {
        let id = row["id"].as_str().expect("vector id");
        let outcome = eval_punarchi_split_candidates(&row["input"]);

        if let Some(expected_err) = row.get("expected_error").and_then(Value::as_str) {
            let err = outcome.expect_err(&format!("{id}: expected error {expected_err:?}"));
            assert_eq!(err.as_str(), expected_err, "{id}");
        } else {
            let actual = outcome.unwrap_or_else(|err| panic!("{id}: expected success, got {err}"));
            assert_eq!(actual, row["expected"], "{id}");
        }
    }
}
