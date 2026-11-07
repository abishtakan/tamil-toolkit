use serde::{Deserialize, Serialize};

/// Configuration controlling hyphenation and line-wrapping behavior.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationConfig {
    /// String delimiter inserted at valid break points. Default: "\u{00AD}" (soft hyphen).
    pub delimiter: String,
    /// Minimum tailored Tamil letters required before the first break. Default: 3.
    pub left_min: usize,
    /// Minimum tailored Tamil letters required after the last break. Default: 3.
    pub right_min: usize,
}

impl Default for HyphenationConfig {
    fn default() -> Self {
        Self {
            delimiter: "\u{00AD}".to_string(),
            left_min: 3,
            right_min: 3,
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

/// An individual Frank Liang hyphenation pattern with interleaved weights.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LiangPattern {
    /// Raw pattern string, e.g. "2க்ஷ2", "2க1"
    pub raw: String,
    /// Clean string without numeric weight digits, e.g. "க்ஷ", "க"
    pub text: String,
    /// Weight numbers around and between characters. Length is text.chars().count() + 1.
    pub weights: Vec<u8>,
}

impl LiangPattern {
    /// Parse a pattern line such as "2க்ஷ2" or "1அ"
    pub fn parse(pattern: &str) -> Option<Self> {
        let trimmed = pattern.trim();
        if trimmed.is_empty() || trimmed.starts_with('%') {
            return None;
        }

        let mut text = String::new();
        let mut weights = Vec::new();
        let mut current_weight = 0u8;

        for ch in trimmed.chars() {
            if let Some(digit) = ch.to_digit(10) {
                current_weight = digit as u8;
            } else {
                weights.push(current_weight);
                current_weight = 0;
                text.push(ch);
            }
        }
        weights.push(current_weight);

        Some(Self {
            raw: trimmed.to_string(),
            text,
            weights,
        })
    }
}

/// Header metadata and parameters for a TeX / Hunspell hyphenation dictionary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DicHeader {
    pub encoding: String,
    pub left_hyphen_min: usize,
    pub right_hyphen_min: usize,
    pub license_notice: String,
}

impl Default for DicHeader {
    fn default() -> Self {
        Self {
            encoding: "UTF-8".to_string(),
            left_hyphen_min: 3,
            right_hyphen_min: 3,
            license_notice: "MIT / LGPL / GPL Tri-license".to_string(),
        }
    }
}

/// A complete TeX / Hunspell hyphenation dictionary.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenDictionary {
    pub header: DicHeader,
    pub patterns: Vec<LiangPattern>,
}

/// Processing statistics for DOCX hyphenation.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct DocxStats {
    /// Number of distinct XML parts inspected and updated (e.g. document.xml, headers, footers).
    pub parts_updated: usize,
    /// Total count of <w:p> paragraph elements traversed.
    pub paragraphs_processed: usize,
    /// Total count of Tamil words detected and evaluated.
    pub words_hyphenated: usize,
    /// Total count of soft hyphens (U+00AD) newly injected.
    pub soft_hyphens_inserted: usize,
}

/// Errors that can occur during DOCX processing.
#[derive(Debug)]
pub enum DocxError {
    Io(std::io::Error),
    Zip(zip::result::ZipError),
    InvalidArchive(String),
    XmlError { part: String, error: String },
}

impl std::fmt::Display for DocxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DocxError::Io(e) => write!(f, "I/O error: {e}"),
            DocxError::Zip(e) => write!(f, "ZIP archive error: {e}"),
            DocxError::InvalidArchive(s) => write!(f, "Invalid OpenXML archive: {s}"),
            DocxError::XmlError { part, error } => write!(f, "Malformed XML in '{part}': {error}"),
        }
    }
}

impl std::error::Error for DocxError {}

impl From<std::io::Error> for DocxError {
    fn from(e: std::io::Error) -> Self {
        DocxError::Io(e)
    }
}

impl From<zip::result::ZipError> for DocxError {
    fn from(e: zip::result::ZipError) -> Self {
        DocxError::Zip(e)
    }
}

