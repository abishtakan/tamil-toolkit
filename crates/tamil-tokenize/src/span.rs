use serde::Serialize;

use crate::tables::{contains, HARD, WHITESPACE};

/// The exact text and original, half-open byte and written-unit coordinates.
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SourceSpan<'a> {
    pub text: &'a str,
    pub start_byte: usize,
    pub end_byte: usize,
    pub start_unit: usize,
    pub end_unit: usize,
}

pub(super) struct Source<'a> {
    pub text: &'a str,
    pub units: Vec<Unit<'a>>,
}

pub(super) struct Unit<'a> {
    pub text: &'a str,
    pub start: usize,
    pub whitespace: bool,
    pub hard: bool,
}

impl<'a> Source<'a> {
    pub fn new(text: &'a str) -> Self {
        let mut start = 0;
        let units = tamil_core::Letters::new(text)
            .map(|unit| {
                let entry = Unit {
                    text: unit,
                    start,
                    whitespace: unit.chars().all(|scalar| contains(WHITESPACE, scalar)),
                    hard: unit.chars().any(|scalar| contains(HARD, scalar)),
                };
                start += unit.len();
                entry
            })
            .collect();
        Self { text, units }
    }

    pub fn offset(&self, index: usize) -> usize {
        self.units
            .get(index)
            .map_or(self.text.len(), |unit| unit.start)
    }

    pub fn span(&self, start_unit: usize, end_unit: usize) -> SourceSpan<'a> {
        let start_byte = self.offset(start_unit);
        let end_byte = self.offset(end_unit);
        SourceSpan {
            text: &self.text[start_byte..end_byte],
            start_byte,
            end_byte,
            start_unit,
            end_unit,
        }
    }

    pub fn boundaries(&self, offsets: impl Iterator<Item = usize>) -> Vec<bool> {
        let mut offsets = offsets.peekable();
        (0..=self.units.len())
            .map(|index| {
                let byte = self.offset(index);
                while offsets.peek().is_some_and(|offset| *offset < byte) {
                    offsets.next();
                }
                offsets.peek() == Some(&byte) || index == self.units.len()
            })
            .collect()
    }
}
