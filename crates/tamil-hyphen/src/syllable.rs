use tamil_core::{inspect_tamil_string, split_uyirmei, Letters};
use tamil_norm::normalize_nfc;

use crate::types::{HyphenationConfig, HyphenationPoint, HyphenationResult};

const PULLI: &str = "\u{0BCD}";
const AYTHAM: &str = "\u{0B83}";

#[inline]
fn contains_joiner(s: &str) -> bool {
    s.chars().any(|c| matches!(u32::from(c), 0x200c | 0x200d))
}

/// Classification of a tailored Tamil letter for syllable breakdown.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LetterClass {
    /// Independent vowel (அ, ஆ...)
    Uyir,
    /// Consonant + Vowel composite (க, கா, கி, கை, கொ...)
    Uyirmei,
    /// Pure consonant with pulli (க், த், ம்...)
    Mei,
    /// Aytham letter (ஃ)
    Aytham,
    /// Atomic Grantha sequence (e.g. க்ஷ, ஸ்ரீ)
    AtomicGrantha,
    /// Non-Tamil letter, symbol, punctuation, or unclassified
    Other,
}

/// Classifies a tailored Tamil letter into its orthographic syllable role.
pub fn classify_letter(letter: &str) -> LetterClass {
    if letter == AYTHAM {
        return LetterClass::Aytham;
    }
    if letter.ends_with(PULLI) {
        return LetterClass::Mei;
    }
    if letter == "க்ஷ" || letter.starts_with("ஸ்ரீ") || letter.starts_with("\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}") {
        return LetterClass::AtomicGrantha;
    }
    if split_uyirmei(letter).is_ok() {
        return LetterClass::Uyirmei;
    }
    let inspected = inspect_tamil_string(letter);
    if let Some(first) = inspected.letters.first() {
        match first.classification {
            "uyir" => LetterClass::Uyir,
            "vallinam" | "mellinam" | "idayinam" | "grantha" => {
                // If it wasn't split by split_uyirmei and doesn't end with pulli,
                // check if it's an inherent-a consonant like 'க'
                if letter.chars().count() == 1 {
                    LetterClass::Uyirmei
                } else {
                    LetterClass::Other
                }
            }
            _ => LetterClass::Other,
        }
    } else {
        LetterClass::Other
    }
}

/// Returns true if this letter acts as a vowel-bearing syllable nucleus.
pub fn is_syllable_nucleus(class: LetterClass) -> bool {
    matches!(
        class,
        LetterClass::Uyir | LetterClass::Uyirmei | LetterClass::AtomicGrantha
    )
}

/// Computes valid break points within a single NFC-normalized Tamil word.
pub fn hyphenation_points(
    word: &str,
    config: Option<&HyphenationConfig>,
) -> Result<Vec<HyphenationPoint>, String> {
    let default_cfg = HyphenationConfig::default();
    let cfg = config.unwrap_or(&default_cfg);

    if cfg.left_min < 1 {
        return Err("left_min must be at least 1".to_string());
    }
    if cfg.right_min < 1 {
        return Err("right_min must be at least 1".to_string());
    }

    let nfc = normalize_nfc(word);
    let letters: Vec<&str> = Letters::new(&nfc).collect();
    let total_letters = letters.len();

    if total_letters < cfg.left_min + cfg.right_min {
        return Ok(Vec::new());
    }

    let classes: Vec<LetterClass> = letters.iter().map(|l| classify_letter(l)).collect();

    // Track prefix and suffix nucleus counts to ensure vowel presence on both sides
    let mut has_nucleus_before = vec![false; total_letters];
    let mut running_nucleus = false;
    for (i, &class) in classes.iter().enumerate() {
        if is_syllable_nucleus(class) {
            running_nucleus = true;
        }
        has_nucleus_before[i] = running_nucleus;
    }

    let mut has_nucleus_after = vec![false; total_letters];
    running_nucleus = false;
    for (i, &class) in classes.iter().enumerate().rev() {
        if is_syllable_nucleus(class) {
            running_nucleus = true;
        }
        has_nucleus_after[i] = running_nucleus;
    }

    // Precalculate byte and scalar offsets of each letter boundary
    let mut byte_offsets = Vec::with_capacity(total_letters + 1);
    let mut scalar_offsets = Vec::with_capacity(total_letters + 1);
    let mut cur_byte = 0;
    let mut cur_scalar = 0;
    byte_offsets.push(0);
    scalar_offsets.push(0);

    for letter in &letters {
        cur_byte += letter.len();
        cur_scalar += letter.chars().count();
        byte_offsets.push(cur_byte);
        scalar_offsets.push(cur_scalar);
    }

    let mut points = Vec::new();

    // Evaluate each boundary after letter i (between i and i+1)
    for i in 0..(total_letters - 1) {
        let left_count = i + 1;
        let right_count = total_letters - left_count;

        // Margin check
        if left_count < cfg.left_min || right_count < cfg.right_min {
            continue;
        }

        // Nucleus check on both sides
        if !has_nucleus_before[i] || !has_nucleus_after[i + 1] {
            continue;
        }

        let _curr_class = classes[i];
        let next_class = classes[i + 1];

        // RULE 1: Next letter CANNOT be a pure consonant (Mei) or Aytham
        if next_class == LetterClass::Mei || next_class == LetterClass::Aytham {
            continue;
        }

        // RULE 2: Next letter must be an onset: Uyir, Uyirmei, or AtomicGrantha
        if !is_syllable_nucleus(next_class) {
            continue;
        }

        // RULE 3: Joiner check: neither curr letter nor next letter can be adjacent to ZWJ or ZWNJ
        let curr_str = letters[i];
        let next_str = letters[i + 1];
        if contains_joiner(curr_str) || contains_joiner(next_str) {
            continue;
        }

        // Valid break!
        points.push(HyphenationPoint {
            letter_index: left_count,
            scalar_offset: scalar_offsets[left_count],
            byte_offset: byte_offsets[left_count],
        });
    }

    Ok(points)
}

/// Hyphenates a single Tamil word, returning the formatted string and unbroken segments.
pub fn hyphenate_word(
    word: &str,
    config: Option<&HyphenationConfig>,
) -> Result<HyphenationResult, String> {
    let default_cfg = HyphenationConfig::default();
    let cfg = config.unwrap_or(&default_cfg);

    let nfc = normalize_nfc(word);
    let points = hyphenation_points(&nfc, Some(cfg))?;

    if points.is_empty() {
        return Ok(HyphenationResult {
            original: nfc.clone(),
            hyphenated: nfc.clone(),
            segments: vec![nfc],
            points: Vec::new(),
        });
    }

    let mut segments = Vec::with_capacity(points.len() + 1);
    let mut last_byte = 0;

    for pt in &points {
        segments.push(nfc[last_byte..pt.byte_offset].to_string());
        last_byte = pt.byte_offset;
    }
    segments.push(nfc[last_byte..].to_string());

    let hyphenated = segments.join(&cfg.delimiter);

    Ok(HyphenationResult {
        original: nfc,
        hyphenated,
        segments,
        points,
    })
}
