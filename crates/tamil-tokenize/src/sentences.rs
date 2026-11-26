use unicode_segmentation::UnicodeSegmentation;

use crate::abbreviation;
use crate::span::{Source, SourceSpan};
use crate::tables::{contains, SENTENCE_TAIL, TERMINATOR};

/// Return abbreviation-aware sentence spans with outer whitespace omitted.
pub fn segment_sentences(text: &str) -> Vec<SourceSpan<'_>> {
    let source = Source::new(text);
    let mut boundaries = source.boundaries(
        text.split_sentence_bound_indices()
            .map(|(offset, _)| offset),
    );
    for matched in abbreviation::find(&source) {
        boundaries[matched.start + 1..matched.end].fill(false);
        if matched.continues_sentence(&source) {
            // The baseline may place the break after closing punctuation and spaces.
            let mut tail = matched.end;
            while source.units.get(tail).is_some_and(|unit| {
                !unit.hard
                    && unit.text.chars().all(|scalar| {
                        contains(SENTENCE_TAIL, scalar) && !contains(TERMINATOR, scalar)
                    })
            }) {
                tail += 1;
            }
            boundaries[matched.end..=tail].fill(false);
        }
    }
    for (i, unit) in source.units.iter().enumerate() {
        if unit.hard {
            boundaries[i + 1] = true;
        }
    }
    let mut result = Vec::new();
    let mut start = 0;
    for (end, _) in boundaries
        .iter()
        .enumerate()
        .skip(1)
        .filter(|(_, boundary)| **boundary)
    {
        let segment = &source.units[start..end];
        if let Some(first) = segment.iter().position(|unit| !unit.whitespace) {
            let last = segment.iter().rposition(|unit| !unit.whitespace).unwrap();
            result.push(source.span(start + first, start + last + 1));
        }
        start = end;
    }
    result
}
