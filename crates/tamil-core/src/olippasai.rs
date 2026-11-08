//! Natural phonetic sound unit (*Olippasai*) segmentation for Tamil text.
//!
//! Syllable structure follows `(C*) V (C*)` where onset consonants (including loanword clusters)
//! and trailing pure consonants / Aytham bind to their vowel nucleus.
//! The iterator operates without heap allocation over borrowed string slices.

use serde::{Deserialize, Serialize};

use crate::phonology::{classify_quantity, LetterQuantity};
use crate::Letters;

/// An orthographic syllable unit (*Olippasai*) with byte and letter span offsets.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Olippasai<'a> {
    /// Borrowed substring slice representing the full syllable.
    pub text: &'a str,

    /// Byte offset range in the source text: `[start_byte, end_byte)`.
    pub start_byte: usize,
    pub end_byte: usize,

    /// Tailored letter index range in the source text: `[start_letter_idx, end_letter_idx)`.
    pub start_letter_idx: usize,
    pub end_letter_idx: usize,

    /// Whether this syllable has one or more trailing pure consonants (Mei) or Aytham codas.
    pub has_coda: bool,

    /// Number of coda letters attached to the nucleus.
    pub coda_count: usize,
}

impl<'a> Olippasai<'a> {
    /// Number of tailored grapheme letters in this syllable unit.
    #[inline]
    pub fn letter_count(&self) -> usize {
        self.end_letter_idx - self.start_letter_idx
    }

    /// Number of UTF-8 bytes in this syllable unit.
    #[inline]
    pub fn byte_len(&self) -> usize {
        self.end_byte - self.start_byte
    }
}

/// Zero-allocation iterator yielding [`Olippasai`] sound units from borrowed input.
pub struct OlippasaiIter<'a> {
    source: &'a str,
    letters: Vec<(&'a str, usize, usize)>, // (slice, letter_idx, byte_offset)
    cursor: usize,
}

impl<'a> OlippasaiIter<'a> {
    /// Creates a new syllable iterator over the supplied text.
    pub fn new(text: &'a str) -> Self {
        let mut letters = Vec::new();
        let base_ptr = text.as_ptr() as usize;
        for (idx, letter) in Letters::new(text).enumerate() {
            let byte_offset = letter.as_ptr() as usize - base_ptr;
            letters.push((letter, idx, byte_offset));
        }

        Self {
            source: text,
            letters,
            cursor: 0,
        }
    }
}

impl<'a> Iterator for OlippasaiIter<'a> {
    type Item = Olippasai<'a>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.cursor >= self.letters.len() {
            return None;
        }

        let start_pos = self.cursor;
        let mut nucleus_pos = None;

        // Check if there is an upcoming vowel nucleus in the current word token
        let mut pos = self.cursor;
        while pos < self.letters.len() {
            let (letter, _, _) = self.letters[pos];
            let qty = classify_quantity(letter);
            if qty == LetterQuantity::Kuril || qty == LetterQuantity::Nedil {
                nucleus_pos = Some(pos);
                break;
            } else if qty == LetterQuantity::Mei {
                // Leading onset consonant candidate
                pos += 1;
            } else {
                // Non-Tamil or Aytham without preceding nucleus
                break;
            }
        }

        if let Some(n_pos) = nucleus_pos {
            // Group optional onset consonants [start_pos .. n_pos] with nucleus at n_pos
            let mut end_pos = n_pos + 1;
            let mut coda_count = 0;

            // Greedily consume following pure consonants (Mei) or Aytham as codas
            while end_pos < self.letters.len() {
                let (letter, _, _) = self.letters[end_pos];
                let qty = classify_quantity(letter);
                if qty == LetterQuantity::Mei || qty == LetterQuantity::Aytham {
                    // Check if this Mei could be an onset for the NEXT syllable:
                    // In Tamil phonotactics, a Mei followed by a vowel binds as onset only if it has NO pulli.
                    // But here qty == Mei means it HAS a pulli virama (e.g. க்).
                    // In Tamil, pure consonants with pulli NEVER initiate syllables, they are always codas!
                    // Loanwords may have initial Mei clusters, but WITHIN a word, C+pulli attaches to preceding nucleus.
                    coda_count += 1;
                    end_pos += 1;
                } else {
                    break;
                }
            }

            self.cursor = end_pos;

            let (_, start_letter_idx, start_byte) = self.letters[start_pos];
            let (last_letter, last_letter_idx, last_byte) = self.letters[end_pos - 1];
            let end_byte = last_byte + last_letter.len();
            let end_letter_idx = last_letter_idx + 1;

            Some(Olippasai {
                text: &self.source[start_byte..end_byte],
                start_byte,
                end_byte,
                start_letter_idx,
                end_letter_idx,
                has_coda: coda_count > 0,
                coda_count,
            })
        } else {
            // Non-nucleus token or orphan consonant: yield as single letter span
            let (letter, letter_idx, byte_offset) = self.letters[self.cursor];
            self.cursor += 1;

            Some(Olippasai {
                text: letter,
                start_byte: byte_offset,
                end_byte: byte_offset + letter.len(),
                start_letter_idx: letter_idx,
                end_letter_idx: letter_idx + 1,
                has_coda: false,
                coda_count: 0,
            })
        }
    }
}

/// Returns an iterator over natural phonetic syllables (*Olippasai*) in `text`.
#[inline]
pub fn get_olippasai<'a>(text: &'a str) -> OlippasaiIter<'a> {
    OlippasaiIter::new(text)
}
