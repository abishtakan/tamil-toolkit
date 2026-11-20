//! Unicode primitives. See docs/specs/bootstrap.md for segmentation tailoring.
#![forbid(unsafe_code)]

use serde::Serialize;
use unicode_normalization::UnicodeNormalization;
use unicode_segmentation::UnicodeSegmentation;

pub mod olippasai;
pub mod phonology;

pub use olippasai::{get_olippasai, Olippasai, OlippasaiIter};
pub use phonology::{
    are_cognates, baseline_maathirai, classify_quantity, get_cognate, is_aytham, is_kuril, is_mei,
    is_nedil, is_otru, LetterQuantity, Maathirai,
};

mod tables {
    include!(concat!(env!("OUT_DIR"), "/core_tables.rs"));
}

/// Canonical NFC normalization. Preserves joiners and never folds Shri spellings.
pub fn normalize_nfc(text: &str) -> String {
    text.nfc().collect()
}

/// Canonical NFD normalization. Preserves non-Tamil text and invisible joiners.
pub fn normalize_nfd(text: &str) -> String {
    text.nfd().collect()
}

/// Allocation-free iteration over borrowed input. Supply NFC text for canonical output.
pub struct Letters<'a> {
    remaining: &'a str,
}

impl<'a> Letters<'a> {
    pub fn new(text: &'a str) -> Self {
        Self { remaining: text }
    }
}

impl<'a> Iterator for Letters<'a> {
    type Item = &'a str;

    fn next(&mut self) -> Option<Self::Item> {
        let first = self.remaining.graphemes(true).next()?;
        let mut end = first.len();
        if let Some(atomic) = tables::ATOMIC_LETTERS
            .iter()
            .find(|s| self.remaining.starts_with(**s))
        {
            // Tailor whole graphemes, preserving all marks/joiners on their boundary.
            end = self
                .remaining
                .graphemes(true)
                .map(str::len)
                .scan(0, |sum, size| {
                    *sum += size;
                    Some(*sum)
                })
                .find(|boundary| *boundary >= atomic.len())
                .expect("atomic boundary");
        }
        let (letter, rest) = self.remaining.split_at(end);
        self.remaining = rest;
        Some(letter)
    }
}

/// Normalize to NFC and return tailored clusters, including non-Tamil clusters.
/// KSHA and both Shri spellings are atomic; malformed text is preserved.
pub fn get_letters(text: &str) -> Vec<String> {
    let normalized = normalize_nfc(text);
    Letters::new(&normalized).map(str::to_owned).collect()
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Uyirmei {
    pub mei: String,
    pub uyir: String,
}

/// Split exactly one NFC-normalized consonant/vowel form into Mei and Uyir.
///
/// Returns an error for pure Mei, independent Uyir, Shri, multiple letters,
/// joiners, and malformed vowel sequences. See the v0.1 golden error contract.
pub fn split_uyirmei(text: &str) -> Result<Uyirmei, String> {
    let normalized = normalize_nfc(text);
    for &(base, _) in tables::CONSONANTS {
        if let Some(sign) = normalized.strip_prefix(base) {
            if let Some(&(uyir, _)) = tables::VOWELS.iter().find(|(_, value)| *value == sign) {
                return Ok(Uyirmei {
                    mei: format!("{base}{}", tables::PULLI),
                    uyir: uyir.to_owned(),
                });
            }
        }
    }
    Err("expected exactly one Uyirmei letter".to_owned())
}

/// Compose one valid Mei and independent Uyir into its NFC vowel form.
///
/// Canonically equivalent inputs are accepted. Invalid letters and extra marks
/// return an error rather than being stripped or repaired.
pub fn compose_uyirmei(mei: &str, uyir: &str) -> Result<String, String> {
    let mei = normalize_nfc(mei);
    let uyir = normalize_nfc(uyir);
    let base = mei
        .strip_suffix(tables::PULLI)
        .filter(|base| tables::CONSONANTS.iter().any(|(c, _)| c == base))
        .ok_or("expected a valid Mei consonant")?;
    let sign = tables::VOWELS
        .iter()
        .find(|(v, _)| *v == uyir)
        .map(|(_, sign)| *sign)
        .ok_or("expected an independent Uyir vowel")?;
    Ok(format!("{base}{sign}"))
}

fn classify(letter: &str) -> &'static str {
    if letter == tables::AYTHAM {
        return "aytham";
    }
    if tables::VOWELS.iter().any(|(v, _)| *v == letter) {
        return "uyir";
    }
    if tables::ATOMIC_LETTERS.contains(&letter)
        && !tables::CONSONANTS.iter().any(|(c, _)| *c == letter)
    {
        return "grantha";
    }
    let base = split_uyirmei(letter).ok().map(|parts| parts.mei);
    let mei = base.as_deref().unwrap_or(letter);
    if let Some(base) = mei.strip_suffix(tables::PULLI) {
        if let Some((_, class)) = tables::CONSONANTS.iter().find(|(c, _)| *c == base) {
            return class;
        }
    }
    "other"
}

#[derive(Debug, Serialize)]
pub struct InspectedLetter {
    pub text: String,
    pub classification: &'static str,
}

#[derive(Debug, Serialize)]
pub struct Inspection {
    pub nfc: String,
    pub nfd: String,
    pub is_nfc: bool,
    pub is_nfd: bool,
    pub ezhuthu_count: usize,
    pub grapheme_count: usize,
    pub letters: Vec<InspectedLetter>,
}

/// Inspect normalization and valid Tamil letter classes without repairing input.
/// `grapheme_count` counts project-tailored clusters, including non-Tamil text;
/// it is not the untailored UAX 29 grapheme count. `ezhuthu_count` excludes `other`.
pub fn inspect_tamil_string(text: &str) -> Inspection {
    let nfc = normalize_nfc(text);
    let nfd = normalize_nfd(text);
    let letters: Vec<_> = Letters::new(&nfc)
        .map(|letter| InspectedLetter {
            text: letter.to_owned(),
            classification: classify(letter),
        })
        .collect();
    Inspection {
        is_nfc: nfc == text,
        is_nfd: nfd == text,
        ezhuthu_count: letters
            .iter()
            .filter(|l| l.classification != "other")
            .count(),
        grapheme_count: letters.len(),
        nfc,
        nfd,
        letters,
    }
}

/// Lightweight text audit matching `inspect_tamil_string` + lexicon intentional-control checks
/// without allocating `nfd` or per-letter `String` vectors.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TextAudit {
    pub is_nfc: bool,
    pub intentional_controls: Vec<(usize, u32)>,
    pub has_other_tamil_cluster: bool,
}

#[inline]
const fn is_intentional_control_cp(cp: u32) -> bool {
    cp < 32
        || (cp >= 0x7F && cp <= 0x9F)
        || matches!(cp, 0x00AD | 0x200C | 0x200D | 0x2028 | 0x2029 | 0xFEFF)
}

#[inline]
const fn is_tamil_block(ch: char) -> bool {
    ch >= '\u{0B80}' && ch <= '\u{0BDF}'
}

/// Inspect normalization, intentional control positions, and `other` Tamil-containing
/// clusters without allocating NFD text or per-letter string slices.
pub fn audit_tamil_text_light(text: &str) -> TextAudit {
    if text.is_ascii() {
        let mut intentional_controls = Vec::new();
        if text.bytes().any(|b| b < 32 || b == 0x7F) {
            for (idx, b) in text.bytes().enumerate() {
                if b < 32 || b == 0x7F {
                    intentional_controls.push((idx, u32::from(b)));
                }
            }
        }
        return TextAudit {
            is_nfc: true,
            intentional_controls,
            has_other_tamil_cluster: false,
        };
    }

    let is_nfc = text.nfc().eq(text.chars());
    let mut intentional_controls = Vec::new();
    for (idx, ch) in text.chars().enumerate() {
        let cp = ch as u32;
        if is_intentional_control_cp(cp) {
            intentional_controls.push((idx, cp));
        }
    }

    let nfc_cow: std::borrow::Cow<'_, str> = if is_nfc {
        std::borrow::Cow::Borrowed(text)
    } else {
        std::borrow::Cow::Owned(normalize_nfc(text))
    };

    let has_other_tamil_cluster = if nfc_cow.chars().any(is_tamil_block) {
        Letters::new(nfc_cow.as_ref())
            .any(|letter| classify(letter) == "other" && letter.chars().any(is_tamil_block))
    } else {
        false
    };

    TextAudit {
        is_nfc,
        intentional_controls,
        has_other_tamil_cluster,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_unicode_preserves_normalized_content(text in ".{0,64}") {
            let borrowed: Vec<_> = Letters::new(&text).collect();
            prop_assert_eq!(borrowed.concat(), text.as_str());
            for letter in borrowed {
                let start = letter.as_ptr() as usize;
                let input_start = text.as_ptr() as usize;
                prop_assert!(start >= input_start && start + letter.len() <= input_start + text.len());
            }
            let nfc = normalize_nfc(&text);
            prop_assert_eq!(get_letters(&text).concat(), nfc.as_str());
            prop_assert_eq!(normalize_nfc(&nfc), nfc.as_str());
            prop_assert_eq!(normalize_nfc(&normalize_nfd(&text)), nfc);
            let _ = split_uyirmei(&text);
            let full = inspect_tamil_string(&text);
            let light = audit_tamil_text_light(&text);
            prop_assert_eq!(light.is_nfc, full.is_nfc);
            let expected_other_tamil = full.letters.iter().any(|l| {
                l.classification == "other" && l.text.chars().any(|c| ('\u{0B80}'..='\u{0BDF}').contains(&c))
            });
            prop_assert_eq!(light.has_other_tamil_cluster, expected_other_tamil);
            let expected_controls: Vec<(usize, u32)> = text
                .chars()
                .enumerate()
                .filter_map(|(i, ch)| {
                    let cp = ch as u32;
                    is_intentional_control_cp(cp).then_some((i, cp))
                })
                .collect();
            prop_assert_eq!(light.intentional_controls, expected_controls);
        }

        #[test]
        fn compose_decompose_roundtrip(c in 0..tables::CONSONANTS.len(), v in 0..tables::VOWELS.len()) {
            let mei = format!("{}{}", tables::CONSONANTS[c].0, tables::PULLI);
            let uyir = tables::VOWELS[v].0;
            let composed = compose_uyirmei(&mei, uyir).unwrap();
            let parts = split_uyirmei(&composed).unwrap();
            prop_assert_eq!(parts.mei, mei);
            prop_assert_eq!(parts.uyir, uyir);
            prop_assert_eq!(get_letters(&composed).len(), 1);
        }
    }

    #[test]
    fn rejects_invalid_letter_boundaries() {
        for text in [
            "",
            "abc",
            "\u{0b95}\u{0bcd}",
            "\u{0b85}",
            "\u{0b95}\u{0b95}",
        ] {
            assert!(split_uyirmei(text).is_err());
        }
        assert!(compose_uyirmei("x", "\u{0b85}").is_err());
        assert!(compose_uyirmei("\u{0b95}\u{0bcd}", "x").is_err());
    }
}
