//! Syllable and orthographic boundary hyphenation.
//!
//! Provides deterministic Tamil syllable breakdown (*Akshara* boundary detection),
//! word hyphenation, paragraph soft-hyphenation, and publication-grade line wrapping.
#![forbid(unsafe_code)]

pub mod syllable;
pub mod text;
pub mod types;

pub use syllable::{classify_letter, hyphenate_word, hyphenation_points, LetterClass};
pub use text::{hyphenate_text, tokenize_words, wrap_text, TextToken};
pub use types::{HyphenationConfig, HyphenationPoint, HyphenationResult, WrapResult};
