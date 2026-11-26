#[path = "support/properties.rs"]
mod properties;

use proptest::prelude::*;
use tamil_tokenize::segment_sentences;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(10_000))]
    #[test]
    fn sentences_preserve_source_and_respect_hard_breaks(text in properties::documents()) {
        let spans = segment_sentences(&text);
        for span in &spans {
            prop_assert!(!span.text.contains(['\r', '\n', '\u{0085}', '\u{2028}', '\u{2029}']), "span crosses a hard separator");
        }
        properties::verify(&text, spans)?;
    }
}
