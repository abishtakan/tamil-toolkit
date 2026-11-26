mod support;

use serde_json::json;
use tamil_tokenize::{tokenize_words, StopwordProfile};

#[test]
fn stopword_vectors() {
    for row in support::rows().filter(|row| row["op"] == "tokenize_words") {
        if let Some(profile) = row["input"]["stopword_profile"].as_str() {
            if let Some(expected) = row.get("expected") {
                let text = row["input"]["text"].as_str().unwrap();
                assert_eq!(
                    json!(tokenize_words(text, profile.parse().unwrap())),
                    *expected,
                    "{}",
                    row["id"]
                );
            } else if row["id"] == "tokenize_word_profile_unknown" {
                assert_eq!(
                    profile.parse::<StopwordProfile>().unwrap_err(),
                    row["expected_error"]
                );
            }
        }
    }
}
