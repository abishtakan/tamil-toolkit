//! Bharathi Tamil Braille Grade 1 (`U+2800..U+28FF`) encoder and decoder.
//! See `docs/specs/codec-braille.md` for the normative contract.

use crate::ErrorPolicy;
use tamil_core::normalize_nfc;

pub(crate) struct BrailleVowel {
    pub(crate) independent: char,
    pub(crate) dependent: Option<char>,
    pub(crate) cell: char,
}

pub(crate) struct BrailleConsonant {
    pub(crate) unicode: char,
    pub(crate) cell: char,
}

mod tables {
    use super::{BrailleConsonant, BrailleVowel};
    include!(concat!(env!("OUT_DIR"), "/braille_tables.rs"));
}

pub use tables::PROFILE as BRAILLE_PROFILE;

fn find_vowel_by_ind(ch: char) -> Option<char> {
    tables::VOWELS
        .iter()
        .find(|v| v.independent == ch)
        .map(|v| v.cell)
}

fn find_vowel_by_dep(ch: char) -> Option<char> {
    tables::VOWELS
        .iter()
        .find(|v| v.dependent == Some(ch))
        .map(|v| v.cell)
}

fn find_consonant_by_uni(ch: char) -> Option<char> {
    tables::CONSONANTS
        .iter()
        .find(|c| c.unicode == ch)
        .map(|c| c.cell)
}

fn find_vowel_by_cell(cell: char) -> Option<&'static BrailleVowel> {
    tables::VOWELS.iter().find(|v| v.cell == cell)
}

fn find_consonant_by_cell(cell: char) -> Option<char> {
    tables::CONSONANTS
        .iter()
        .find(|c| c.cell == cell)
        .map(|c| c.unicode)
}

/// Encode Tamil Unicode to Grade 1 Bharathi Tamil Braille (`U+2800..U+28FF`).
pub fn unicode_to_braille(text: &str, errors: ErrorPolicy) -> Result<String, String> {
    let normalized = normalize_nfc(text);
    let mut output = String::with_capacity(normalized.len());
    let mut i = 0;
    let bytes = normalized.as_bytes();
    while i < bytes.len() {
        let tail = &normalized[i..];
        if tail.starts_with("\u{0b95}\u{0bcd}\u{0bb7}\u{0bcd}") {
            output.push(tables::PULLI_CELL);
            output.push(tables::KSHA_CELL);
            i += "\u{0b95}\u{0bcd}\u{0bb7}\u{0bcd}".len();
            continue;
        }
        if tail.starts_with(tables::KSHA_UNICODE) {
            output.push(tables::KSHA_CELL);
            i += tables::KSHA_UNICODE.len();
            if let Some(next_ch) = normalized[i..].chars().next() {
                if let Some(vcell) = find_vowel_by_dep(next_ch) {
                    output.push(vcell);
                    i += next_ch.len_utf8();
                }
            }
            continue;
        }
        let ch = tail.chars().next().expect("non-empty tail");
        let ch_len = ch.len_utf8();
        if let Some(ccell) = find_consonant_by_uni(ch) {
            i += ch_len;
            if let Some(next_ch) = normalized[i..].chars().next() {
                if next_ch == '\u{0bcd}' {
                    output.push(tables::PULLI_CELL);
                    output.push(ccell);
                    i += next_ch.len_utf8();
                    continue;
                }
                if let Some(vcell) = find_vowel_by_dep(next_ch) {
                    output.push(ccell);
                    output.push(vcell);
                    i += next_ch.len_utf8();
                    continue;
                }
            }
            output.push(ccell);
        } else if let Some(vcell) = find_vowel_by_ind(ch) {
            output.push(vcell);
            i += ch_len;
        } else if ch == tables::AYTHAM_UNICODE {
            output.push(tables::AYTHAM_CELL);
            i += ch_len;
        } else if ch == ' ' {
            output.push(tables::SPACE_CELL);
            i += ch_len;
        } else if matches!(ch, '\t' | '\r' | '\n') || errors == ErrorPolicy::Preserve {
            output.push(ch);
            i += ch_len;
        } else {
            return Err(format!(
                "unsupported Unicode scalar for Braille at NFC byte {i}: U+{:04X}",
                u32::from(ch)
            ));
        }
    }
    Ok(output)
}

/// Decode Grade 1 Bharathi Tamil Braille (`U+2800..U+28FF`) to NFC Tamil Unicode.
pub fn braille_to_unicode(text: &str, errors: ErrorPolicy) -> Result<String, String> {
    let chars: Vec<char> = text.chars().collect();
    let mut output = String::with_capacity(text.len());
    let mut idx = 0;
    while idx < chars.len() {
        let cell = chars[idx];
        if cell == tables::PULLI_CELL {
            let Some(&next) = chars.get(idx + 1) else {
                if errors == ErrorPolicy::Preserve {
                    output.push(cell);
                    idx += 1;
                    continue;
                }
                return Err(format!("invalid Braille pulli sequence at character {idx}"));
            };
            if next == tables::KSHA_CELL {
                output.push_str(tables::KSHA_UNICODE);
                output.push('\u{0bcd}');
                idx += 2;
            } else if let Some(cons) = find_consonant_by_cell(next) {
                output.push(cons);
                output.push('\u{0bcd}');
                idx += 2;
            } else if errors == ErrorPolicy::Preserve {
                output.push(cell);
                idx += 1;
            } else {
                return Err(format!("invalid Braille pulli sequence at character {idx}"));
            }
        } else if cell == tables::KSHA_CELL {
            output.push_str(tables::KSHA_UNICODE);
            idx += 1;
            if let Some(&next) = chars.get(idx) {
                if let Some(v) = find_vowel_by_cell(next) {
                    if let Some(dep) = v.dependent {
                        output.push(dep);
                        idx += 1;
                    }
                }
            }
        } else if let Some(cons) = find_consonant_by_cell(cell) {
            output.push(cons);
            idx += 1;
            if let Some(&next) = chars.get(idx) {
                if let Some(v) = find_vowel_by_cell(next) {
                    if let Some(dep) = v.dependent {
                        output.push(dep);
                        idx += 1;
                    }
                }
            }
        } else if let Some(v) = find_vowel_by_cell(cell) {
            output.push(v.independent);
            idx += 1;
        } else if cell == tables::AYTHAM_CELL {
            output.push(tables::AYTHAM_UNICODE);
            idx += 1;
        } else if cell == tables::SPACE_CELL || cell == ' ' {
            output.push(' ');
            idx += 1;
        } else if matches!(cell, '\t' | '\r' | '\n') || errors == ErrorPolicy::Preserve {
            output.push(cell);
            idx += 1;
        } else {
            return Err(format!(
                "unsupported Braille scalar at character {idx}: U+{:04X}",
                u32::from(cell)
            ));
        }
    }
    Ok(normalize_nfc(&output))
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_utf8_never_panics_in_braille(text in ".{0,96}") {
            let _ = unicode_to_braille(&text, ErrorPolicy::Strict);
            prop_assert!(unicode_to_braille(&text, ErrorPolicy::Preserve).is_ok());
            let _ = braille_to_unicode(&text, ErrorPolicy::Strict);
            prop_assert!(braille_to_unicode(&text, ErrorPolicy::Preserve).is_ok());
        }
        #[test]
        fn valid_tamil_braille_roundtrips_losslessly(
            parts in prop::collection::vec(0usize..58, 0..24)
        ) {
            let mut tamil = String::new();
            let mut after_consonant = false;
            for p in parts {
                match p {
                    0..=11 if !after_consonant => {
                        tamil.push(tables::VOWELS[p].independent);
                        after_consonant = false;
                    }
                    12 => {
                        tamil.push(tables::AYTHAM_UNICODE);
                        after_consonant = false;
                    }
                    13..=35 => {
                        tamil.push(tables::CONSONANTS[p - 13].unicode);
                        after_consonant = true;
                    }
                    36..=45 => {
                        tamil.push(tables::CONSONANTS[p - 36].unicode);
                        tamil.push('\u{0bcd}');
                        after_consonant = false;
                    }
                    46..=56 => {
                        tamil.push(tables::CONSONANTS[(p - 46) % 23].unicode);
                        if let Some(dep) = tables::VOWELS[(p - 46) + 1].dependent {
                            tamil.push(dep);
                        }
                        after_consonant = false;
                    }
                    _ => {
                        tamil.push(' ');
                        after_consonant = false;
                    }
                }
            }
            let encoded = unicode_to_braille(&tamil, ErrorPolicy::Strict).unwrap();
            let decoded = braille_to_unicode(&encoded, ErrorPolicy::Strict).unwrap();
            prop_assert_eq!(decoded, normalize_nfc(&tamil));
        }
    }
}
