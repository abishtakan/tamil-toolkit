use serde::Serialize;
use unicode_segmentation::UnicodeSegmentation;

use crate::abbreviation;
use crate::span::{Source, SourceSpan};
use crate::tables::{contains, DECIMAL, LETTER};
use crate::StopwordProfile;

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TokenKind {
    Abbreviation,
    Word,
    Number,
    Other,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct Token<'a> {
    #[serde(flatten)]
    pub span: SourceSpan<'a>,
    pub kind: TokenKind,
}

/// Return non-whitespace word, number, abbreviation, and other source spans.
pub fn tokenize_words(text: &str, profile: StopwordProfile) -> Vec<Token<'_>> {
    let source = Source::new(text);
    let mut boundaries =
        source.boundaries(text.split_word_bound_indices().map(|(offset, _)| offset));
    for (i, pair) in source.units.windows(2).enumerate() {
        if pair[0].whitespace != pair[1].whitespace {
            boundaries[i + 1] = true;
        }
    }
    let matches = abbreviation::find(&source);
    for matched in &matches {
        boundaries[matched.start] = true;
        boundaries[matched.start + 1..matched.end].fill(false);
        boundaries[matched.end] = true;
    }
    let mut matches = matches.iter().peekable();
    let mut result = Vec::new();
    let mut start = 0;
    for (end, _) in boundaries
        .iter()
        .enumerate()
        .skip(1)
        .filter(|(_, boundary)| **boundary)
    {
        if !source.units[start].whitespace {
            let span = source.span(start, end);
            let kind = if matches.peek().is_some_and(|m| m.start == start) {
                matches.next();
                TokenKind::Abbreviation
            } else if span.text.chars().any(|scalar| contains(LETTER, scalar)) {
                TokenKind::Word
            } else if span.text.chars().any(|scalar| contains(DECIMAL, scalar)) {
                TokenKind::Number
            } else {
                TokenKind::Other
            };
            if kind != TokenKind::Word || !profile.contains(span.text) {
                result.push(Token { span, kind });
            }
        }
        start = end;
    }
    result
}
