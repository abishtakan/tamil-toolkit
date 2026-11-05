use proptest::prelude::*;
use tamil_hyphen::hyphenate_word;

proptest! {
    #![proptest_config(ProptestConfig::with_cases(10_000))]

    #[test]
    fn prop_lossless_roundtrip_reconstruction(s in "\\PC{1,30}") {
        if let Ok(res) = hyphenate_word(&s, None) {
            let reconstructed = res.segments.join("");
            prop_assert_eq!(reconstructed, res.original);
        }
    }
}
