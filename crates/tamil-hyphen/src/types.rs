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
