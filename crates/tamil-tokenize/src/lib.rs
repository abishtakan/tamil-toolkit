//! Offline, source-preserving Tamil word and sentence boundaries.
#![forbid(unsafe_code)]

mod abbreviation;
mod sentences;
mod span;
mod stopwords;
mod tables;
mod words;

pub use sentences::segment_sentences;
pub use span::SourceSpan;
pub use stopwords::StopwordProfile;
pub use words::{tokenize_words, Token, TokenKind};
