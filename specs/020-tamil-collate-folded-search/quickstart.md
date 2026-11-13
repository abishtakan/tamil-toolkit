# Phase 1 Quickstart: `tamil-collate` Folded Search & Uyirmei-First Profile

## 1. Rust Example

```rust
use tamil_collate::{
    compare_with_profile, folded_search_key, sort_words_with_profile,
    CollationProfile, FoldingProfile,
};

fn main() {
    // 1. Folded search keys for Mayangoli variants
    let key1 = folded_search_key("மணம்", FoldingProfile::Mayangoli);
    let key2 = folded_search_key("மனம்", FoldingProfile::Mayangoli);
    assert_eq!(key1, key2);

    // 2. Uyirmei-First School Dictionary Sorting
    let words = vec![
        "க்ளப்".to_string(),
        "கப்பல்".to_string(),
    ];
    let sorted = sort_words_with_profile(&words, CollationProfile::UyirmeiFirstV1);
    assert_eq!(sorted, vec!["கப்பல்", "க்ளப்"]);
}
```

## 2. CLI Example

```bash
# Folded search key
tamil-toolkit collate search-key --fold mayangoli "மணம்"

# Compare using Uyirmei-First profile
tamil-toolkit collate compare --profile uyirmei-first-v1 "கப்பல்" "க்ளப்"
```
