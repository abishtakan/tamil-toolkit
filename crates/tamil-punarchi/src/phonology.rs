//! Prerequisite Nannool Ezhuttiyal phonology & phonotactics (Sutras 93-94, 102-108, 205).
//!
//! Built directly over `tamil_core::Letters`, `split_uyirmei`, `compose_uyirmei`,
//! and `classify_quantity` without duplicating Tamil orthographic primitives.

use tamil_core::{
    classify_quantity, is_aytham, is_kuril, is_mei, is_nedil, split_uyirmei, LetterQuantity,
    Letters,
};
use tamil_norm::normalize_nfc;

const ZWNJ_CODE: u32 = 0x200C;
const ZWJ_CODE: u32 = 0x200D;

pub const ALL_VOWELS: &[&str] = &["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ"];

pub const VALLINAM_MEI: &[&str] = &["க்", "ச்", "ட்", "த்", "ப்", "ற்"];
pub const MELLINAM_MEI: &[&str] = &["ங்", "ஞ்", "ண்", "ந்", "ம்", "ன்"];
pub const IDAIYINAM_MEI: &[&str] = &["ய்", "ர்", "ல்", "வ்", "ழ்", "ள்"];
pub const IDAIYINAM_KURRIYAL_MEI: &[&str] = &["ய்", "ர்", "ல்", "ழ்", "ள்"];

pub const NATIVE_MEI: &[&str] = &[
    "க்", "ங்", "ச்", "ஞ்", "ட்", "ண்", "த்", "ந்", "ப்", "ம்", "ய்", "ர்", "ல்", "வ்", "ழ்", "ள்", "ற்", "ன்",
];

/// Sutra 107: 11 pure consonants permitted at word-end (`ஞணநம னயரல வழள`).
pub const LEGAL_EETRU_MEI: &[&str] = &["ஞ்", "ண்", "ந்", "ம்", "ன்", "ய்", "ர்", "ல்", "வ்", "ழ்", "ள்"];

/// Sutra 102 + 106.2: 6 word-initial consonants combining with all 12 vowels.
const UNRESTRICTED_MUTHAL_MEI: &[&str] = &["க்", "ச்", "த்", "ந்", "ப்", "ம்"];

/// Sutra 103: 8 vowels allowed with initial `வ`.
const VA_MUTHAL_VOWELS: &[&str] = &["அ", "ஆ", "இ", "ஈ", "எ", "ஏ", "ஐ", "ஔ"];

/// Sutra 104: 6 vowels allowed with initial `ய`.
const YA_MUTHAL_VOWELS: &[&str] = &["அ", "ஆ", "உ", "ஊ", "ஓ", "ஔ"];

/// Sutra 105: 4 vowels allowed with initial `ஞ`.
const NJA_MUTHAL_VOWELS: &[&str] = &["அ", "ஆ", "எ", "ஒ"];

/// Sutra 106: clitics licensing bound `ஙனம்`.
pub const NGANAM_TRIGGERS: &[&str] = &["அ", "இ", "உ", "யா", "எ"];

/// Six Kurriyalugaram classes vs Mutriyalugaram vs NonU (Nannool Sutra 94).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum UgaramClass {
    NedilThodar,
    AythathThodar,
    UyirThodar,
    Vanthodar,
    Menthodar,
    Idaithodar,
    Mutriyalugaram,
    NonU,
}

impl UgaramClass {
    /// Returns true if the word ends in a half-mora *Kurriyalugaram* (any of the 6 classes).
    #[inline]
    pub fn is_kurriyalugaram(self) -> bool {
        matches!(
            self,
            Self::NedilThodar
                | Self::AythathThodar
                | Self::UyirThodar
                | Self::Vanthodar
                | Self::Menthodar
                | Self::Idaithodar
        )
    }
}

/// Return true if a scalar is ZWJ or ZWNJ.
#[inline]
pub fn is_joiner(ch: char) -> bool {
    matches!(ch as u32, ZWNJ_CODE | ZWJ_CODE)
}

/// Return true if a string slice contains ZWJ or ZWNJ.
#[inline]
pub fn contains_joiner(s: &str) -> bool {
    s.chars().any(is_joiner)
}

/// Return true if `unit` is a standalone independent Tamil vowel (12 vowels).
#[inline]
pub fn is_independent_uyir(unit: &str) -> bool {
    ALL_VOWELS.contains(&unit)
}

/// Return true if `mei` is one of the 18 native Tamil pure consonants.
#[inline]
pub fn is_native_mei(mei: &str) -> bool {
    NATIVE_MEI.contains(&mei)
}

/// Return true if `mei` is one of the 6 Vallinam pure consonants (`க், ச், ட், த், ப், ற்`).
#[inline]
pub fn is_vallinam_mei(mei: &str) -> bool {
    VALLINAM_MEI.contains(&mei)
}

/// Return true if `mei` is one of the 6 Mellinam pure consonants (`ங், ஞ், ண், ந், ம், ன்`).
#[inline]
pub fn is_mellinam_mei(mei: &str) -> bool {
    MELLINAM_MEI.contains(&mei)
}

/// Return true if `mei` is one of the 6 Idaiyinam pure consonants (`ய், ர், ல், வ், ழ், ள்`).
#[inline]
pub fn is_idaiyinam_mei(mei: &str) -> bool {
    IDAIYINAM_MEI.contains(&mei)
}

/// Extract the final vowel of a written unit (standalone vowel or Uyirmei's vowel).
pub fn unit_vowel(unit: &str) -> Option<String> {
    if is_independent_uyir(unit) {
        return Some(unit.to_owned());
    }
    split_uyirmei(unit).ok().map(|parts| parts.uyir)
}

/// Extract the base pure consonant (`Mei` with pulli) of a pure consonant or Uyirmei unit.
pub fn unit_mei(unit: &str) -> Option<String> {
    if is_mei(unit) && is_native_mei(unit) {
        return Some(unit.to_owned());
    }
    split_uyirmei(unit)
        .ok()
        .filter(|parts| is_native_mei(&parts.mei))
        .map(|parts| parts.mei)
}

/// Return true if `unit` is a Vallinam-initial Uyirmei (`க/ச/த/ப`-series; also `ட/ற`).
pub fn is_vallinam_initial_unit(unit: &str) -> bool {
    split_uyirmei(unit)
        .ok()
        .is_some_and(|parts| matches!(parts.mei.as_str(), "க்" | "ச்" | "த்" | "ப்"))
}

/// Return the homorganic Mellinam nasal for a Vallinam stop Mei (`க்->ங்`, `ச்->ஞ்`, `ட்->ண்`, `த்->ந்`, `ப்->ம்`, `ற்->ன்`).
pub fn homorganic_nasal(vallinam_mei: &str) -> Option<&'static str> {
    match vallinam_mei {
        "க்" => Some("ங்"),
        "ச்" => Some("ஞ்"),
        "ட்" => Some("ண்"),
        "த்" => Some("ந்"),
        "ப்" => Some("ம்"),
        "ற்" => Some("ன்"),
        _ => None,
    }
}

/// Exact Nannool Sutra 94 decision tree classifying final `உ` into 6 *Kurriyalugaram* classes vs *Mutriyalugaram* vs `NonU`.
pub fn classify_ugaram(word: &str) -> UgaramClass {
    let nfc = normalize_nfc(word);
    let units: Vec<&str> = Letters::new(&nfc).collect();
    let Some(&last) = units.last() else {
        return UgaramClass::NonU;
    };

    if last == "உ" {
        return UgaramClass::Mutriyalugaram;
    }

    let Ok(last_parts) = split_uyirmei(last) else {
        return UgaramClass::NonU;
    };
    if last_parts.uyir != "உ" {
        return UgaramClass::NonU;
    }
    if !is_vallinam_mei(&last_parts.mei) {
        return UgaramClass::Mutriyalugaram;
    }

    let n = units.len();
    if n < 2 {
        return UgaramClass::Mutriyalugaram;
    }
    // Two-unit short-vowel `C?V_short + C_v u` (`அது`, `பசு`, `புது`, `கடு`, `நடு`) is Mutriyalugaram.
    if n == 2 && is_kuril(units[0]) {
        return UgaramClass::Mutriyalugaram;
    }

    let prev = units[n - 2];
    if is_aytham(prev) {
        return UgaramClass::AythathThodar;
    }
    if is_mei(prev) {
        if is_vallinam_mei(prev) {
            return UgaramClass::Vanthodar;
        }
        if is_mellinam_mei(prev) {
            return UgaramClass::Menthodar;
        }
        if IDAIYINAM_KURRIYAL_MEI.contains(&prev) {
            return UgaramClass::Idaithodar;
        }
        return UgaramClass::Mutriyalugaram;
    }

    // Penultimate is a vowel or Uyirmei.
    if n == 2 && is_nedil(prev) {
        return UgaramClass::NedilThodar;
    }
    if n >= 3 && (is_kuril(prev) || is_nedil(prev)) {
        return UgaramClass::UyirThodar;
    }

    UgaramClass::Mutriyalugaram
}

/// Sutra 93: Returns true if `(first, second)` forms a *Kurriyaligaram* context
/// (either `first` is *Kurriyalugaram* before `ய`-initial `second`, or `second == "மியா"`).
pub fn is_kurriyaligaram_context(first: &str, second: &str) -> bool {
    let second_nfc = normalize_nfc(second);
    if second_nfc == "மியா" {
        return true;
    }
    if !classify_ugaram(first).is_kurriyalugaram() {
        return false;
    }
    let Some(first_unit) = Letters::new(&second_nfc).next() else {
        return false;
    };
    split_uyirmei(first_unit)
        .ok()
        .is_some_and(|parts| parts.mei == "ய்")
}

/// Sutras 102-106: Classical native Tamil word-initial (*Mozhi-muthal*) phonotactic validator.
///
/// `left_context` supplies the preceding word when checking Sutra 106 bound `ஙனம்`.
pub fn is_valid_mozhi_muthal(word: &str, left_context: Option<&str>) -> bool {
    let nfc = normalize_nfc(word);
    let Some(first_unit) = Letters::new(&nfc).next() else {
        return false;
    };

    if is_independent_uyir(first_unit) {
        return true;
    }
    let Ok(parts) = split_uyirmei(first_unit) else {
        return false;
    };
    let mei = parts.mei.as_str();
    let uyir = parts.uyir.as_str();

    if UNRESTRICTED_MUTHAL_MEI.contains(&mei) {
        return true;
    }
    match mei {
        "வ்" => VA_MUTHAL_VOWELS.contains(&uyir),
        "ய்" => YA_MUTHAL_VOWELS.contains(&uyir),
        "ஞ்" => NJA_MUTHAL_VOWELS.contains(&uyir),
        "ங்" => {
            uyir == "அ"
                && nfc == "ஙனம்"
                && left_context.is_some_and(|left| {
                    let left_nfc = normalize_nfc(left);
                    NGANAM_TRIGGERS.contains(&left_nfc.as_str())
                })
        }
        _ => false,
    }
}

/// Sutras 107-108: Classical native Tamil word-final (*Mozhi-eetru*) phonotactic validator.
pub fn is_valid_mozhi_eetru(word: &str) -> bool {
    let nfc = normalize_nfc(word);
    let Some(last_unit) = Letters::new(&nfc).last() else {
        return false;
    };

    if is_independent_uyir(last_unit) {
        return true;
    }
    if is_mei(last_unit) {
        return LEGAL_EETRU_MEI.contains(&last_unit);
    }
    let Ok(parts) = split_uyirmei(last_unit) else {
        return false;
    };
    if !is_native_mei(&parts.mei) {
        return false;
    }
    match parts.uyir.as_str() {
        "எ" => false,
        "ஒ" => parts.mei == "ந்",
        "ஔ" => matches!(parts.mei.as_str(), "க்" | "வ்"),
        _ => true,
    }
}

/// Sutra 205: Returns true if `word` is a short-vowel monosyllable ending in a single native pure consonant (`தனிக்குறில் முன் ஒற்று`).
pub fn is_thanikkuril_otru(word: &str) -> bool {
    let nfc = normalize_nfc(word);
    let units: Vec<&str> = Letters::new(&nfc).collect();
    units.len() == 2 && is_kuril(units[0]) && is_mei(units[1]) && is_native_mei(units[1])
}

/// Detect whether the join boundary between `first` and `second` has a non-Tamil scalar
/// or an explicit `ZWJ`/`ZWNJ` barrier (FR-008: verbatim *Iyalbu* passthrough).
pub fn has_boundary_barrier(first: &str, second: &str) -> bool {
    if first.chars().last().is_some_and(is_joiner) || second.chars().next().is_some_and(is_joiner) {
        return true;
    }

    let first_nfc = normalize_nfc(first);
    let second_nfc = normalize_nfc(second);

    let Some(last_unit) = Letters::new(&first_nfc).last() else {
        return true;
    };
    let Some(first_unit) = Letters::new(&second_nfc).next() else {
        return true;
    };

    if contains_joiner(last_unit) || contains_joiner(first_unit) {
        return true;
    }

    classify_quantity(last_unit) == LetterQuantity::Other
        || classify_quantity(first_unit) == LetterQuantity::Other
}
