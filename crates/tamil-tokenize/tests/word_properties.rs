#[path = "support/properties.rs"]
mod properties;

use proptest::prelude::*;
use tamil_tokenize::{tokenize_words, StopwordProfile};

proptest! {
    #![proptest_config(ProptestConfig::with_cases(10_000))]
    #[test]
    fn unfiltered_words_preserve_source(text in properties::documents()) {
        properties::verify(&text, tokenize_words(&text, StopwordProfile::None).into_iter().map(|token| token.span))?;
    }
}
