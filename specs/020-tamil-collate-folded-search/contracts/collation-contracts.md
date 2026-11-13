# Phase 1 Interface Contracts: `tamil-collate`

## 1. Rust Public API (`tamil-collate`)

```rust
pub use tamil_norm::FoldingProfile;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum CollationProfile {
    #[default]
    AgaraV1,
    UyirmeiFirstV1,
}

// Existing backward-compatible functions (default to AgaraV1)
pub fn sort_key(text: &str) -> Vec<u32>;
pub fn search_key(text: &str) -> Vec<u32>;
pub fn compare(left: &str, right: &str) -> Ordering;
pub fn sort_words(words: &[String]) -> Vec<String>;

// New profile-aware functions
pub fn sort_key_with_profile(text: &str, profile: CollationProfile) -> Vec<u32>;
pub fn compare_with_profile(left: &str, right: &str, profile: CollationProfile) -> Ordering;
pub fn sort_words_with_profile(words: &[String], profile: CollationProfile) -> Vec<String>;

// New search folding functions
pub fn folded_search_key(text: &str, profile: FoldingProfile) -> Vec<u32>;
pub fn folded_search_key_with_profile(
    text: &str,
    fold_profile: FoldingProfile,
    collate_profile: CollationProfile,
) -> Vec<u32>;
```

## 2. CLI Contract (`tamil-toolkit collate`)

Subcommands under `tamil-toolkit collate`:
- `sort`: `tamil-toolkit collate sort [--profile agara-v1|uyirmei-first-v1] <words...>`
- `compare`: `tamil-toolkit collate compare [--profile agara-v1|uyirmei-first-v1] <left> <right>`
- `key`: `tamil-toolkit collate key [--profile agara-v1|uyirmei-first-v1] <text>`
- `search-key`: `tamil-toolkit collate search-key [--fold mayangoli|grantha|comprehensive] [--profile agara-v1|uyirmei-first-v1] <text>`

## 3. Dispatcher / Multi-Runtime Contract (`tamil-toolkit`)

Operations dispatched through JSON:
- `collate_folded_search_key`: `{"op": "collate_folded_search_key", "text": "...", "profile": "mayangoli"}` $\rightarrow$ `{"key": [1, ...]}`
- `collate_compare`: expanded to support optional `"profile": "uyirmei-first-v1"`
- `collate_sort_words`: expanded to support optional `"profile": "uyirmei-first-v1"`
