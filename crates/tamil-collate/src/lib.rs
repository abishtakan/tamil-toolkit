//! Traditional Mei-first Agara collation and modern Uyirmei-first school dictionary collation.
//! See docs/specs/collate-v0.1.md.
//! Other scripts and malformed clusters have a deterministic scalar fallback.
#![forbid(unsafe_code)]

use std::cmp::Ordering;
use tamil_core::{normalize_nfc, Letters};

pub use tamil_norm::FoldingProfile;

mod tables {
    include!(concat!(env!("OUT_DIR"), "/collation_tables.rs"));
}

pub use tables::{
    AGARA_PROFILE, EXPANSIONS, KEY_VERSION, LOOKUP, PROFILE, UYIRMEI_FIRST_KEY_VERSION,
    UYIRMEI_FIRST_PROFILE,
};

/// Supported Tamil collation profiles.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum CollationProfile {
    /// Traditional Mei-first Agara collation (CLDR 48 / Madras Tamil Lexicon).
    #[default]
    AgaraV1,
    /// Modern pedagogical school dictionary collation (Uyirmei syllables precede pure consonants).
    UyirmeiFirstV1,
}

impl CollationProfile {
    /// Canonical profile identifier string.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::AgaraV1 => tables::AGARA_PROFILE,
            Self::UyirmeiFirstV1 => tables::UYIRMEI_FIRST_PROFILE,
        }
    }

    /// Key format version for this profile.
    pub fn key_version(&self) -> u32 {
        match self {
            Self::AgaraV1 => tables::AGARA_KEY_VERSION,
            Self::UyirmeiFirstV1 => tables::UYIRMEI_FIRST_KEY_VERSION,
        }
    }
}

impl std::str::FromStr for CollationProfile {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "agara-v1" | "agara" => Ok(Self::AgaraV1),
            "uyirmei-first-v1" | "uyirmei-first" | "school-v1" => Ok(Self::UyirmeiFirstV1),
            other => Err(format!("unknown collation profile: '{other}'")),
        }
    }
}

/// Produce a lossless canonical key for the documented Agara profile.
/// Compare numeric arrays lexicographically; never compare their JSON encodings.
/// Persist the profile/key version with stored indexes. This function allocates.
pub fn sort_key(text: &str) -> Vec<u32> {
    sort_key_with_profile(text, CollationProfile::AgaraV1)
}

/// Produce a lossless canonical key for the requested collation profile.
pub fn sort_key_with_profile(text: &str, profile: CollationProfile) -> Vec<u32> {
    let (lookup, expansions, key_version) = match profile {
        CollationProfile::AgaraV1 => (
            tables::AGARA_LOOKUP,
            tables::AGARA_EXPANSIONS,
            tables::AGARA_KEY_VERSION,
        ),
        CollationProfile::UyirmeiFirstV1 => (
            tables::UYIRMEI_FIRST_LOOKUP,
            tables::UYIRMEI_FIRST_EXPANSIONS,
            tables::UYIRMEI_FIRST_KEY_VERSION,
        ),
    };
    let normalized = normalize_nfc(text);
    let mut key = vec![key_version];
    for cluster in Letters::new(&normalized) {
        if let Ok(index) = lookup.binary_search_by_key(&cluster, |entry| entry.0) {
            key.extend([0, lookup[index].1]);
        } else if let Some((_, weights)) = expansions.iter().find(|(text, _)| *text == cluster) {
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

/// Canonical exact-match/search-index key for the requested collation profile.
pub fn search_key_with_profile(text: &str, profile: CollationProfile) -> Vec<u32> {
    sort_key_with_profile(text, profile)
}

/// Produce a versioned search key normalized under the given lossy search-folding profile.
/// Uses the default Agara-v1 collation profile after folding.
pub fn folded_search_key(text: &str, profile: FoldingProfile) -> Vec<u32> {
    folded_search_key_with_profile(text, profile, CollationProfile::AgaraV1)
}

/// Produce a versioned search key normalized under the given search-folding profile and collation profile.
pub fn folded_search_key_with_profile(
    text: &str,
    fold_profile: FoldingProfile,
    collate_profile: CollationProfile,
) -> Vec<u32> {
    let folded = tamil_norm::fold_for_search(text, fold_profile);
    sort_key_with_profile(&folded, collate_profile)
}

/// Compare using agara-v1. Canonically equivalent spellings compare equal.
pub fn compare(left: &str, right: &str) -> Ordering {
    compare_with_profile(left, right, CollationProfile::AgaraV1)
}

/// Compare using the requested collation profile. Canonically equivalent spellings compare equal.
pub fn compare_with_profile(left: &str, right: &str, profile: CollationProfile) -> Ordering {
    sort_key_with_profile(left, profile).cmp(&sort_key_with_profile(right, profile))
}

/// Return a stable sorted copy, preserving original spellings and duplicates.
/// Each input's key is computed once. Neither input text nor input order mutates.
pub fn sort_words(words: &[String]) -> Vec<String> {
    sort_words_with_profile(words, CollationProfile::AgaraV1)
}

/// Return a stable sorted copy using the requested collation profile.
pub fn sort_words_with_profile(words: &[String], profile: CollationProfile) -> Vec<String> {
    let mut keyed: Vec<_> = words
        .iter()
        .map(|word| (sort_key_with_profile(word, profile), word))
        .collect();
    keyed.sort_by(|left, right| left.0.cmp(&right.0));
    keyed.into_iter().map(|(_, word)| word.clone()).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use tamil_core::normalize_nfd;

    fn decode_key(key: &[u32], profile: CollationProfile) -> String {
        assert_eq!(key[0], profile.key_version());
        assert_eq!(key.len() % 2, 1);
        let lookup = match profile {
            CollationProfile::AgaraV1 => tables::AGARA_LOOKUP,
            CollationProfile::UyirmeiFirstV1 => tables::UYIRMEI_FIRST_LOOKUP,
        };
        key[1..]
            .chunks_exact(2)
            .map(|pair| match pair[0] {
                0 => lookup
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

    #[test]
    fn test_folded_search_key_mayangoli() {
        let key_la = folded_search_key("பழம்", FoldingProfile::Mayangoli);
        let key_la2 = folded_search_key("பலம்", FoldingProfile::Mayangoli);
        let key_la3 = folded_search_key("பளம்", FoldingProfile::Mayangoli);
        assert_eq!(key_la, key_la2);
        assert_eq!(key_la, key_la3);

        let key_na = folded_search_key("மணம்", FoldingProfile::Mayangoli);
        let key_na2 = folded_search_key("மனம்", FoldingProfile::Mayangoli);
        assert_eq!(key_na, key_na2);
    }

    #[test]
    fn test_folded_search_key_grantha() {
        let key_ja = folded_search_key("ஜனம்", FoldingProfile::Grantha);
        let key_ca = folded_search_key("சனம்", FoldingProfile::Grantha);
        assert_eq!(key_ja, key_ca);

        let key_ha = folded_search_key("ஹரி", FoldingProfile::Grantha);
        let key_ka = folded_search_key("கரி", FoldingProfile::Grantha);
        assert_eq!(key_ha, key_ka);
    }

    #[test]
    fn test_uyirmei_first_school_ordering() {
        let word_ka = "கப்பல்".to_string();
        let word_k = "க்ளப்".to_string();

        // Under agara-v1: Mei comes before Uyirmei (க் precedes க)
        assert_eq!(compare(&word_k, &word_ka), Ordering::Less);

        // Under uyirmei-first-v1: Uyirmei comes before Mei (க precedes க்)
        assert_eq!(
            compare_with_profile(&word_ka, &word_k, CollationProfile::UyirmeiFirstV1),
            Ordering::Less
        );

        let sorted = sort_words_with_profile(
            &[word_k.clone(), word_ka.clone()],
            CollationProfile::UyirmeiFirstV1,
        );
        assert_eq!(sorted, vec![word_ka, word_k]);
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]

        #[test]
        fn keys_preserve_canonical_content(text in ".{0,32}") {
            let key = sort_key(&text);
            prop_assert_eq!(decode_key(&key, CollationProfile::AgaraV1), normalize_nfc(&text));
            prop_assert_eq!(&key, &sort_key(&normalize_nfd(&text)));
            prop_assert_eq!(&key, &search_key(&text));

            let key_uyirmei = sort_key_with_profile(&text, CollationProfile::UyirmeiFirstV1);
            prop_assert_eq!(decode_key(&key_uyirmei, CollationProfile::UyirmeiFirstV1), normalize_nfc(&text));
            prop_assert_eq!(&key_uyirmei, &sort_key_with_profile(&normalize_nfd(&text), CollationProfile::UyirmeiFirstV1));
        }

        #[test]
        fn comparator_obeys_order_laws(a in ".{0,16}", b in ".{0,16}", c in ".{0,16}") {
            for profile in [CollationProfile::AgaraV1, CollationProfile::UyirmeiFirstV1] {
                let ab = compare_with_profile(&a, &b, profile);
                prop_assert_eq!(ab, compare_with_profile(&b, &a, profile).reverse());
                if ab != Ordering::Greater && compare_with_profile(&b, &c, profile) != Ordering::Greater {
                    prop_assert_ne!(compare_with_profile(&a, &c, profile), Ordering::Greater);
                }
                prop_assert_eq!(compare_with_profile(&a, &normalize_nfd(&a), profile), Ordering::Equal);
            }
        }
    }
}
