//! Classical Tamil phonological primitives and letter-quantity metrics.
//!
//! Grounded in classical Tamil grammars (*Tolkappiyam Ezhuthathikaram* & *Nannool Ezhuthathikaram*).
//! All classifications operate on Unicode NFC normalized characters and respect tailored atomic clusters.

use serde::{Deserialize, Serialize};

use crate::{compose_uyirmei, normalize_nfc, split_uyirmei, tables};

/// Classical phonological quantity of a Tamil letter or grapheme cluster.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum LetterQuantity {
    /// Short vowel or consonant-vowel composite (1.0 mora / Maathirai).
    /// Examples: அ, இ, உ, எ, ஒ, க, கி, கு, தெ, நொ.
    Kuril,

    /// Long vowel, diphthong, or long consonant-vowel composite (2.0 morae / Maathirai).
    /// Examples: ஆ, ஈ, ஊ, ஏ, ஐ, ஓ, ஔ, கா, கீ, கூ, தே, கை, நோ, கௌ, ஸ்ரீ.
    Nedil,

    /// Pure consonant with pulli virama (0.5 mora / Maathirai).
    /// Examples: க், ங், ச், ட், த், ப், ற், ம், ய், ர், ல், வ், ழ், ள், ஜ், ஷ், ஸ், ஹ், க்ஷ்.
    Mei,

    /// Aytham character ஃ (0.5 mora / Maathirai).
    Aytham,

    /// Non-Tamil letter, symbol, punctuation, whitespace, or unclassified character (0.0 mora).
    Other,
}

/// Classical temporal measure (*Maathirai* / mora) of an isolated speech sound.
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Maathirai(pub f32);

impl Maathirai {
    /// 1.0 mora for short vowel or consonant-vowel composite.
    pub const KURIL: Self = Self(1.0);
    /// 2.0 morae for long vowel, diphthong, or composite.
    pub const NEDIL: Self = Self(2.0);
    /// 0.5 mora for pure consonant with pulli.
    pub const MEI: Self = Self(0.5);
    /// 0.5 mora for classical Aytham character.
    pub const AYTHAM: Self = Self(0.5);
    /// 0.0 mora for non-Tamil or unclassified characters.
    pub const ZERO: Self = Self(0.0);

    /// Returns the duration as an f32 mora value.
    #[inline]
    pub fn value(&self) -> f32 {
        self.0
    }

    /// Returns the exact fractional duration as (numerator, denominator).
    #[inline]
    pub fn as_fraction(&self) -> (u8, u8) {
        if (self.0 - 0.5).abs() < f32::EPSILON {
            (1, 2)
        } else if (self.0 - 1.0).abs() < f32::EPSILON {
            (1, 1)
        } else if (self.0 - 2.0).abs() < f32::EPSILON {
            (2, 1)
        } else {
            (0, 1)
        }
    }
}

const SHORT_UYIR: &[&str] = &[
    "\u{0B85}", // அ
    "\u{0B87}", // இ
    "\u{0B89}", // உ
    "\u{0B8E}", // எ
    "\u{0B92}", // ஒ
];

const LONG_UYIR: &[&str] = &[
    "\u{0B86}", // ஆ
    "\u{0B88}", // ஈ
    "\u{0B8A}", // ஊ
    "\u{0B8F}", // ஏ
    "\u{0B90}", // ஐ (Nannool Sutra 88: 2 morae)
    "\u{0B93}", // ஓ
    "\u{0B94}", // ஔ (Nannool Sutra 88: 2 morae)
];

const VALLINAM_MELLINAM_PAIRS: &[(&str, &str)] = &[
    ("\u{0B95}\u{0BCD}", "\u{0B99}\u{0BCD}"), // க் <-> ங்
    ("\u{0B9A}\u{0BCD}", "\u{0B9E}\u{0BCD}"), // ச் <-> ஞ்
    ("\u{0B9F}\u{0BCD}", "\u{0BA3}\u{0BCD}"), // ட் <-> ண்
    ("\u{0BA4}\u{0BCD}", "\u{0BA8}\u{0BCD}"), // த் <-> ந்
    ("\u{0BAA}\u{0BCD}", "\u{0BAE}\u{0BCD}"), // ப் <-> ம்
    ("\u{0BB1}\u{0BCD}", "\u{0BA9}\u{0BCD}"), // ற் <-> ன்
];

const VOWEL_COGNATE_PAIRS: &[(&str, &str)] = &[
    ("\u{0B85}", "\u{0B86}"), // அ <-> ஆ
    ("\u{0B87}", "\u{0B88}"), // இ <-> ஈ
    ("\u{0B89}", "\u{0B8A}"), // உ <-> ஊ
    ("\u{0B8E}", "\u{0B8F}"), // எ <-> ஏ
    ("\u{0B92}", "\u{0B93}"), // ஒ <-> ஓ
    ("\u{0B90}", "\u{0B87}"), // ஐ <-> இ (Nannool Sutra 76)
    ("\u{0B94}", "\u{0B89}"), // ஔ <-> உ (Nannool Sutra 76)
];

/// Classifies a tailored Tamil letter or grapheme cluster into its phonological quantity.
pub fn classify_quantity(letter: &str) -> LetterQuantity {
    let normalized = normalize_nfc(letter);

    // Aytham character ஃ
    if normalized == tables::AYTHAM {
        return LetterQuantity::Aytham;
    }

    // Atomic Grantha ligatures
    if normalized == "\u{0B95}\u{0BCD}\u{0BB7}" {
        // க்ஷ with inherent 'a' is Kuril
        return LetterQuantity::Kuril;
    }
    if normalized == "\u{0B95}\u{0BCD}\u{0BB7}\u{0BCD}" {
        // க்ஷ் with pulli is Mei
        return LetterQuantity::Mei;
    }
    if normalized == "\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}"
        || normalized == "\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}"
    {
        // ஸ்ரீ / ஶ்ரீ has long 'ii' vowel sign, so Nedil
        return LetterQuantity::Nedil;
    }

    // Independent vowels (Uyir)
    if SHORT_UYIR.contains(&normalized.as_str()) {
        return LetterQuantity::Kuril;
    }
    if LONG_UYIR.contains(&normalized.as_str()) {
        return LetterQuantity::Nedil;
    }

    // Pure consonants (Mei) with pulli
    if let Some(base) = normalized.strip_suffix(tables::PULLI) {
        if tables::CONSONANTS.iter().any(|(c, _)| *c == base) || base == "\u{0B95}\u{0BCD}\u{0BB7}"
        {
            return LetterQuantity::Mei;
        }
    }

    // Uyirmei composites (Consonant + Vowel)
    if let Ok(parts) = split_uyirmei(&normalized) {
        if SHORT_UYIR.contains(&parts.uyir.as_str()) {
            return LetterQuantity::Kuril;
        }
        if LONG_UYIR.contains(&parts.uyir.as_str()) {
            return LetterQuantity::Nedil;
        }
    }

    // Extended check for Ksha + vowel sign composites (e.g. க்ஷா, க்ஷி)
    if let Some(sign) = normalized.strip_prefix("\u{0B95}\u{0BCD}\u{0BB7}") {
        if let Some(&(uyir, _)) = tables::VOWELS.iter().find(|(_, s)| *s == sign) {
            if SHORT_UYIR.contains(&uyir) {
                return LetterQuantity::Kuril;
            }
            if LONG_UYIR.contains(&uyir) {
                return LetterQuantity::Nedil;
            }
        }
    }

    LetterQuantity::Other
}

/// Returns the nominal baseline duration (*Maathirai*) for a given letter.
#[inline]
pub fn baseline_maathirai(letter: &str) -> Maathirai {
    match classify_quantity(letter) {
        LetterQuantity::Kuril => Maathirai::KURIL,
        LetterQuantity::Nedil => Maathirai::NEDIL,
        LetterQuantity::Mei => Maathirai::MEI,
        LetterQuantity::Aytham => Maathirai::AYTHAM,
        LetterQuantity::Other => Maathirai::ZERO,
    }
}

/// Returns true if the letter is a short vowel or short consonant-vowel composite.
#[inline]
pub fn is_kuril(letter: &str) -> bool {
    classify_quantity(letter) == LetterQuantity::Kuril
}

/// Returns true if the letter is a long vowel, diphthong, or long consonant-vowel composite.
#[inline]
pub fn is_nedil(letter: &str) -> bool {
    classify_quantity(letter) == LetterQuantity::Nedil
}

/// Returns true if the letter is a pure consonant terminating in pulli virama (U+0BCD).
#[inline]
pub fn is_mei(letter: &str) -> bool {
    classify_quantity(letter) == LetterQuantity::Mei
}

/// Semantic alias for `is_mei(letter)`.
#[inline]
pub fn is_otru(letter: &str) -> bool {
    is_mei(letter)
}

/// Returns true if the letter is the classical Aytham character (U+0B83).
#[inline]
pub fn is_aytham(letter: &str) -> bool {
    classify_quantity(letter) == LetterQuantity::Aytham
}

/// Returns the canonical cognate letter (*Ina Ezhuthu*) for a given consonant, vowel, or Uyirmei composite.
///
/// Sourced from *Tolkappiyam* (Pirappiyal) and *Nannool* (Sutras 75–76):
/// - Vallinam hard stops pair with Mellinam nasals: க் ↔ ங், ச் ↔ ஞ், ட் ↔ ண், த் ↔ ந், ப் ↔ ம், ற் ↔ ன்.
/// - Short and long vowels pair: அ ↔ ஆ, இ ↔ ஈ, உ ↔ ஊ, எ ↔ ஏ, ஒ ↔ ஓ.
/// - Diphthongs pair: ஐ ↔ இ, ஔ ↔ உ.
/// - Composite Uyirmei letters map their base consonant while preserving the vowel sign: e.g., கா ↔ ஙா, கி ↔ ஙி.
/// - Idaiyinam medium consonants have no nasal partners, returning `None`.
pub fn get_cognate(letter: &str) -> Option<String> {
    let normalized = normalize_nfc(letter);

    // 1. Consonant pure Mei stop <-> nasal
    for &(stop, nasal) in VALLINAM_MELLINAM_PAIRS {
        if normalized == stop {
            return Some(nasal.to_string());
        }
        if normalized == nasal {
            return Some(stop.to_string());
        }
    }

    // 2. Vowel cognate pairs
    for &(short_v, long_v) in VOWEL_COGNATE_PAIRS {
        if normalized == short_v {
            return Some(long_v.to_string());
        }
        if normalized == long_v {
            return Some(short_v.to_string());
        }
    }

    // 3. Composite Uyirmei letters (preserve vowel sign while mapping base consonant)
    if let Ok(parts) = split_uyirmei(&normalized) {
        if let Some(cognate_mei) = get_cognate(&parts.mei) {
            if let Ok(composed) = compose_uyirmei(&cognate_mei, &parts.uyir) {
                return Some(composed);
            }
        }
    }

    None
}

/// Returns true if letter1 and letter2 form a recognized classical *Ina Ezhuthu* pair.
pub fn are_cognates(letter1: &str, letter2: &str) -> bool {
    let normalized1 = normalize_nfc(letter1);
    let normalized2 = normalize_nfc(letter2);

    if normalized1.is_empty() || normalized2.is_empty() {
        return false;
    }

    if let Some(target) = get_cognate(&normalized1) {
        if target == normalized2 {
            return true;
        }
    }

    if let Some(target) = get_cognate(&normalized2) {
        if target == normalized1 {
            return true;
        }
    }

    false
}
