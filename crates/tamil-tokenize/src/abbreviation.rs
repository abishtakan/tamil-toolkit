use crate::span::Source;
use crate::tables::{
    contains, Abbreviation, Following, ABBREVIATIONS, DECIMAL, FORMAT, LETTER, MARK,
};

pub(super) struct Matched {
    pub start: usize,
    pub end: usize,
    pub entry: &'static Abbreviation,
}

fn word_context(scalar: char) -> bool {
    [LETTER, MARK, DECIMAL, FORMAT]
        .into_iter()
        .any(|table| contains(table, scalar))
}

fn matches_following(entry: &Abbreviation, scalar: char) -> bool {
    match entry.following {
        Following::Tamil => ('\u{0b80}'..='\u{0bff}').contains(&scalar) && contains(LETTER, scalar),
        Following::Decimal => contains(DECIMAL, scalar),
    }
}

pub(super) fn find(source: &Source<'_>) -> Vec<Matched> {
    let mut found = Vec::new();
    let mut start = 0;
    while start < source.units.len() {
        let byte = source.offset(start);
        let mut longest = None;
        if source.units[start]
            .text
            .starts_with(|c| ('\u{0b80}'..='\u{0bff}').contains(&c))
            && !source.text[..byte]
                .chars()
                .next_back()
                .is_some_and(word_context)
        {
            for entry in ABBREVIATIONS {
                for end in start + 1..=source.units.len() {
                    let end_byte = source.offset(end);
                    if end_byte - byte > entry.max_bytes {
                        break;
                    }
                    if !source.text[byte..end_byte].ends_with('.')
                        || tamil_norm::normalize_nfc(&source.text[byte..end_byte]) != entry.form
                    {
                        continue;
                    }
                    let adjacent_ok = source.text[end_byte..].chars().next().is_none_or(|c| {
                        !word_context(c) || (entry.min_spaces == 0 && matches_following(entry, c))
                    });
                    if adjacent_ok && longest.as_ref().is_none_or(|m: &Matched| end > m.end) {
                        longest = Some(Matched { start, end, entry });
                    }
                    break;
                }
            }
        }
        if let Some(matched) = longest {
            start = matched.end;
            found.push(matched);
        } else {
            start += 1;
        }
    }
    found
}

impl Matched {
    pub fn continues_sentence(&self, source: &Source<'_>) -> bool {
        let mut remaining = source.units[self.end..].iter().peekable();
        let mut spaces = 0;
        while remaining
            .next_if(|unit| unit.whitespace && !unit.hard)
            .is_some()
        {
            spaces += 1;
        }
        let punctuation = remaining
            .next_if(|unit| unit.text.len() == 1 && self.entry.punctuation.contains(unit.text))
            .is_some();
        if punctuation {
            while remaining
                .next_if(|unit| unit.whitespace && !unit.hard)
                .is_some()
            {}
        }
        (punctuation || spaces >= self.entry.min_spaces)
            && remaining
                .next()
                .and_then(|unit| unit.text.chars().next())
                .is_some_and(|scalar| matches_following(self.entry, scalar))
    }
}
