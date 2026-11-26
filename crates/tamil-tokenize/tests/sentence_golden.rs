mod support;

use serde_json::json;
use tamil_tokenize::segment_sentences;

#[test]
fn sentence_vectors() {
    for row in support::rows()
        .filter(|row| row["op"] == "segment_sentences" && row.get("expected").is_some())
    {
        let text = row["input"]["text"].as_str().unwrap();
        assert_eq!(
            json!(segment_sentences(text)),
            row["expected"],
            "{}",
            row["id"]
        );
    }
}
