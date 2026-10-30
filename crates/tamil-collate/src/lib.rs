//! Traditional Mei-first Agara collation. See docs/specs/collate-v0.1.md.
//! Other scripts and malformed clusters have a deterministic scalar fallback.
#![forbid(unsafe_code)]

use std::cmp::Ordering;
use tamil_core::{normalize_nfc, Letters};

mod tables {
    include!(concat!(env!("OUT_DIR"), "/collation_tables.rs"));
}

pub use tables::{KEY_VERSION, PROFILE};

/// Produce a lossless canonical key for the documented Agara profile.
/// Compare numeric arrays lexicographically; never compare their JSON encodings.
/// Persist the profile/key version with stored indexes. This function allocates.
pub fn sort_key(text: &str) -> Vec<u32> {
    let normalized = normalize_nfc(text);
    let mut key = vec![KEY_VERSION];
    for cluster in Letters::new(&normalized) {
        if let Ok(index) = tables::LOOKUP.binary_search_by_key(&cluster, |entry| entry.0) {
            key.extend([0, tables::LOOKUP[index].1]);
        } else if let Some((_, weights)) =
            tables::EXPANSIONS.iter().find(|(text, _)| *text == cluster)
        {
            for rank in *weights {
                key.extend([0, *rank]);
            }
        } else {
            for scalar in cluster.chars() {
                key.extend([1, scalar as u32]);
            }
        }
    }
    key
}

/// Canonical exact-match/search-index key. No case, vowel, or dialect folding.
pub fn search_key(text: &str) -> Vec<u32> {
    sort_key(text)
}

/// Compare using agara-v1. Canonically equivalent spellings compare equal.
pub fn compare(left: &str, right: &str) -> Ordering {
    sort_key(left).cmp(&sort_key(right))
}

/// Return a stable sorted copy, preserving original spellings and duplicates.
/// Each input's key is computed once. Neither input text nor input order mutates.
pub fn sort_words(words: &[String]) -> Vec<String> {
    let mut keyed: Vec<_> = words.iter().map(|word| (sort_key(word), word)).collect();
    keyed.sort_by(|left, right| left.0.cmp(&right.0));
    keyed.into_iter().map(|(_, word)| word.clone()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use tamil_core::normalize_nfd;

    fn decode_key(key: &[u32]) -> String {
        assert_eq!(key[0], KEY_VERSION);
        assert_eq!(key.len() % 2, 1);
        key[1..]
            .chunks_exact(2)
            .map(|pair| match pair[0] {
                0 => tables::LOOKUP
                    .iter()
                    .find(|(_, rank)| *rank == pair[1])
                    .unwrap()
                    .0
                    .to_owned(),
                1 => char::from_u32(pair[1]).unwrap().to_string(),
                _ => panic!("invalid key tag"),
            })
            .collect()
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn keys_preserve_canonical_content(text in ".{0,32}") {
            let key = sort_key(&text);
            prop_assert_eq!(decode_key(&key), normalize_nfc(&text));
            prop_assert_eq!(&key, &sort_key(&normalize_nfd(&text)));
            prop_assert_eq!(&key, &search_key(&text));
        }

        #[test]
        fn comparator_obeys_order_laws(a in ".{0,16}", b in ".{0,16}", c in ".{0,16}") {
            let ab = compare(&a, &b);
            prop_assert_eq!(ab, compare(&b, &a).reverse());
            if ab != Ordering::Greater && compare(&b, &c) != Ordering::Greater {
                prop_assert_ne!(compare(&a, &c), Ordering::Greater);
            }
            prop_assert_eq!(compare(&a, &normalize_nfd(&a)), Ordering::Equal);
        }

        #[test]
        fn sorting_preserves_values_and_equal_key_order(words in prop::collection::vec(".{0,12}", 0..10)) {
            let sorted = sort_words(&words);
            let mut original_values = words.clone();
            original_values.sort();
            let mut sorted_values = sorted.clone();
            sorted_values.sort();
            prop_assert_eq!(sorted_values, original_values);
            prop_assert!(sorted.windows(2).all(|pair| compare(&pair[0], &pair[1]) != Ordering::Greater));
            for word in &words {
                let original_equal: Vec<_> = words.iter().filter(|other| compare(word, other) == Ordering::Equal).collect();
                let sorted_equal: Vec<_> = sorted.iter().filter(|other| compare(word, other) == Ordering::Equal).collect();
                prop_assert_eq!(original_equal, sorted_equal);
            }
        }
    }
}
