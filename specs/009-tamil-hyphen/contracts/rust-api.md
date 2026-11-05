# Rust API Contract: `tamil-hyphen` and `tamil-toolkit`

## 1. Crate: `tamil-hyphen`

```rust
//! Crate: tamil-hyphen
//! Syllable and orthographic boundary hyphenation.

#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};

/// Configuration controlling hyphenation and line-wrapping behavior.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationConfig {
    /// String delimiter inserted at valid break points. Default: "\u{00AD}" (soft hyphen).
    pub delimiter: String,
    /// Minimum tailored Tamil letters required before the first break. Default: 2.
    pub left_min: usize,
    /// Minimum tailored Tamil letters required after the last break. Default: 2.
    pub right_min: usize,
}

impl Default for HyphenationConfig {
    fn default() -> Self {
        Self {
            delimiter: "\u{00AD}".to_string(),
            left_min: 2,
            right_min: 2,
        }
    }
}

/// A valid break opportunity identified within a normalized word.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationPoint {
    /// Zero-based index in the sequence of tailored letters (Ezhuthu).
    pub letter_index: usize,
    /// Zero-based Unicode scalar offset in the normalized string.
    pub scalar_offset: usize,
    /// Zero-based UTF-8 byte offset in the normalized string.
    pub byte_offset: usize,
}

/// The result of hyphenating a single Tamil word.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationResult {
    /// Input word normalized to NFC.
    pub original: String,
    /// Word with delimiter inserted at each valid break point.
    pub hyphenated: String,
    /// Ordered list of unbroken syllable segments.
    pub segments: Vec<String>,
    /// Metadata for each break point.
    pub points: Vec<HyphenationPoint>,
}

/// The result of wrapping a text paragraph.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WrapResult {
    /// Ordered list of wrapped lines.
    pub lines: Vec<String>,
    /// Number of words split across lines using hyphenation.
    pub broken_words_count: usize,
}

/// Hyphenates a single Tamil word using the specified configuration.
pub fn hyphenate_word(word: &str, config: Option<&HyphenationConfig>) -> Result<HyphenationResult, String>;

/// Inspects valid break opportunities within a single Tamil word.
pub fn hyphenation_points(word: &str, config: Option<&HyphenationConfig>) -> Result<Vec<HyphenationPoint>, String>;

/// Hyphenates arbitrary text, scanning for Tamil word tokens and injecting delimiters.
pub fn hyphenate_text(text: &str, config: Option<&HyphenationConfig>) -> Result<String, String>;

/// Wraps Tamil and mixed-script text to a specified maximum width (in grapheme clusters).
pub fn wrap_text(text: &str, max_width: usize, config: Option<&HyphenationConfig>) -> Result<WrapResult, String>;
```

---

## 2. Umbrella Dispatcher: `tamil-toolkit::execute`

The unified dispatcher in `crates/tamil-toolkit/src/lib.rs` routes operation strings:

### Supported Operations:
1. `"hyphenate_word"`:
   - `input`: `string` (Tamil word)
   - `options`: optional object (`delimiter`, `left_min`, `right_min`)
   - Returns: `HyphenationResult`
2. `"hyphenation_points"`:
   - `input`: `string` (Tamil word)
   - `options`: optional object (`left_min`, `right_min`)
   - Returns: `Vec<HyphenationPoint>`
3. `"hyphenate_text"`:
   - `input`: `string` (Paragraph / full text)
   - `options`: optional object (`delimiter`, `left_min`, `right_min`)
   - Returns: `string` (Hyphenated text)
4. `"wrap_text"`:
   - `input`: `string` (Paragraph / full text)
   - `options`: object requiring `max_width: number`, optional (`delimiter`, `left_min`, `right_min`)
   - Returns: `WrapResult`
