mod support;

use serde_json::json;
use tamil_tokenize::{tokenize_words, StopwordProfile};

#[test]
fn unfiltered_word_vectors() {
    for row in support::rows().filter(|row| {
        row["op"] == "tokenize_words"
            && row.get("expected").is_some()
            && row["input"].get("stopword_profile").is_none()
    }) {
        let text = row["input"]["text"].as_str().unwrap();
        assert_eq!(
            json!(tokenize_words(text, StopwordProfile::None)),
            row["expected"],
            "{}",
            row["id"]
        );
    }
}
