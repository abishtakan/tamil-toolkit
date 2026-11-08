//! Versioned lossy search-folding profiles for Tamil search and indexing.
#![forbid(unsafe_code)]

use crate::types::FoldingProfile;
use tamil_core::{compose_uyirmei, split_uyirmei, Letters};

const LA_RETROFLEX_MEI: &str = "\u{0BB3}\u{0BCD}"; // ள்
const ZHA_MEI: &str = "\u{0BB4}\u{0BCD}"; // ழ்
const LA_ALVEOLAR_MEI: &str = "\u{0BB2}\u{0BCD}"; // ல்

const NA_RETROFLEX_MEI: &str = "\u{0BA3}\u{0BCD}"; // ண்
const NA_ALVEOLAR_MEI: &str = "\u{0BA9}\u{0BCD}"; // ன்

const RA_HARD_MEI: &str = "\u{0BB1}\u{0BCD}"; // ற்
const RA_MEDIAL_MEI: &str = "\u{0BB0}\u{0BCD}"; // ர்

const SA_MEI: &str = "\u{0BB8}\u{0BCD}"; // ஸ்
const SHA_MEI: &str = "\u{0BB7}\u{0BCD}"; // ஷ்
const JA_MEI: &str = "\u{0B9C}\u{0BCD}"; // ஜ்
const HA_MEI: &str = "\u{0BB9}\u{0BCD}"; // ஹ்
const CHA_MEI: &str = "\u{0B9A}\u{0BCD}"; // ச்
const KA_MEI: &str = "\u{0B95}\u{0BCD}"; // க்

const KSHA_BASE: &str = "\u{0B95}\u{0BCD}\u{0BB7}"; // க்ஷ
const KSHA_MEI: &str = "\u{0B95}\u{0BCD}\u{0BB7}\u{0BCD}"; // க்ஷ்
const SHRI_1: &str = "\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}"; // ஸ்ரீ
const SHRI_2: &str = "\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}"; // ஶ்ரீ

fn fold_mayangoli_letter(letter: &str) -> String {
    // 1. Pure consonants with pulli
    if letter == LA_RETROFLEX_MEI || letter == ZHA_MEI {
        return LA_ALVEOLAR_MEI.to_string(); // ள், ழ் -> ல்
    }
    if letter == NA_RETROFLEX_MEI {
        return NA_ALVEOLAR_MEI.to_string(); // ண் -> ன்
    }
    if letter == RA_HARD_MEI {
        return RA_MEDIAL_MEI.to_string(); // ற் -> ர்
    }

    // 2. Composite Uyirmei letters
    if let Ok(parts) = split_uyirmei(letter) {
        if parts.mei == LA_RETROFLEX_MEI || parts.mei == ZHA_MEI {
            if let Ok(comp) = compose_uyirmei(LA_ALVEOLAR_MEI, &parts.uyir) {
                return comp;
            }
        }
        if parts.mei == NA_RETROFLEX_MEI {
            if let Ok(comp) = compose_uyirmei(NA_ALVEOLAR_MEI, &parts.uyir) {
                return comp;
            }
        }
        if parts.mei == RA_HARD_MEI {
            if let Ok(comp) = compose_uyirmei(RA_MEDIAL_MEI, &parts.uyir) {
                return comp;
            }
        }
    }

    letter.to_string()
}

fn fold_grantha_letter(letter: &str) -> String {
    // 1. Shri -> சீ
    if letter == SHRI_1 || letter == SHRI_2 {
        return "\u{0B9A}\u{0BC0}".to_string();
    }

    // 2. Ksha ligature composites: க்ஷ + diacritic -> ச + diacritic
    if letter == KSHA_MEI {
        return CHA_MEI.to_string(); // க்ஷ் -> ச்
    }
    if letter == KSHA_BASE {
        return "\u{0B9A}".to_string(); // க்ஷ -> ச
    }
    if let Some(rest) = letter.strip_prefix(KSHA_BASE) {
        return format!("\u{0B9A}{rest}"); // e.g. க்ஷா -> சா, க்ஷி -> சி
    }

    // 3. Pure Grantha consonants with pulli
    if letter == SA_MEI || letter == SHA_MEI || letter == JA_MEI {
        return CHA_MEI.to_string(); // ஸ், ஷ், ஜ் -> ச்
    }
    if letter == HA_MEI {
        return KA_MEI.to_string(); // ஹ் -> க்
    }

    // 4. Grantha composite letters
    if let Ok(parts) = split_uyirmei(letter) {
        if parts.mei == SA_MEI || parts.mei == SHA_MEI || parts.mei == JA_MEI {
            if let Ok(comp) = compose_uyirmei(CHA_MEI, &parts.uyir) {
                return comp;
            }
        }
        if parts.mei == HA_MEI {
            if let Ok(comp) = compose_uyirmei(KA_MEI, &parts.uyir) {
                return comp;
            }
        }
    }

    letter.to_string()
}

/// Folds Tamil text for search and index matching according to the chosen profile.
pub fn fold_for_search(text: &str, profile: FoldingProfile) -> String {
    let mut result = String::with_capacity(text.len());

    for letter in Letters::new(text) {
        match profile {
            FoldingProfile::Mayangoli => {
                result.push_str(&fold_mayangoli_letter(letter));
            }
            FoldingProfile::Grantha => {
                result.push_str(&fold_grantha_letter(letter));
            }
            FoldingProfile::Comprehensive => {
                let grantha_folded = fold_grantha_letter(letter);
                let fully_folded = fold_mayangoli_letter(&grantha_folded);
                for c in fully_folded.chars() {
                    result.push(c.to_ascii_lowercase());
                }
            }
        }
    }

    if profile == FoldingProfile::Comprehensive {
        // Collapse whitespace in comprehensive mode
        let mut collapsed = String::with_capacity(result.len());
        let mut in_space = false;
        for c in result.trim().chars() {
            if c.is_whitespace() {
                if !in_space {
                    collapsed.push(' ');
                    in_space = true;
                }
            } else {
                collapsed.push(c);
                in_space = false;
            }
        }
        tamil_core::normalize_nfc(&collapsed)
    } else {
        tamil_core::normalize_nfc(&result)
    }
}
