//! Syllable and orthographic boundary hyphenation.
//!
//! Provides deterministic Tamil syllable breakdown (*Akshara* boundary detection),
//! word hyphenation, paragraph soft-hyphenation, and publication-grade line wrapping.
#![forbid(unsafe_code)]

pub mod dic;
pub mod oxt;
pub mod syllable;
pub mod text;
pub mod types;
pub mod verify_dic;

pub use dic::{export_dic_content, export_dic_file, generate_patterns, DicExportOptions};
pub use oxt::package_oxt;
pub use syllable::{classify_letter, hyphenate_word, hyphenation_points, LetterClass};
pub use text::{hyphenate_text, tokenize_words, wrap_text, TextToken};
pub use types::{
    DicHeader, HyphenDictionary, HyphenationConfig, HyphenationPoint, HyphenationResult,
    LiangPattern, WrapResult,
};
pub use verify_dic::LiangEvaluator;
