use tamil_core::{
    classify_quantity, inspect_tamil_string, is_aytham, is_mei, split_uyirmei, LetterQuantity,
    Letters,
};
use tamil_norm::normalize_nfc;

use crate::types::{HyphenationConfig, HyphenationPoint, HyphenationResult};

#[inline]
fn contains_joiner(s: &str) -> bool {
    s.chars().any(|c| matches!(u32::from(c), 0x200c | 0x200d))
}

#[inline]
fn strip_existing_hyphens(s: &str) -> String {
    s.chars()
        .filter(|&c| !matches!(c, '\u{00AD}' | '\u{001F}' | '\u{200B}'))
        .collect()
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

/// Raw phonetic syllable (*Olippasai*) consisting of a vowel nucleus and all contiguous Mei/Aytham codas.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RawSyllable {
    pub start_letter_idx: usize,
    pub end_letter_idx: usize,
    pub text: String,
    pub has_coda: bool,
}

impl RawSyllable {
    #[inline]
    pub fn letter_count(&self) -> usize {
        self.end_letter_idx - self.start_letter_idx
    }
}

/// Prosodic Tamil *Asai* segment formed by the 5-step grouping and minimum-segment merge rules.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AsaiSegment {
    pub start_letter_idx: usize,
    pub end_letter_idx: usize,
    pub has_coda: bool,
}

impl AsaiSegment {
    #[inline]
    pub fn letter_count(&self) -> usize {
        self.end_letter_idx - self.start_letter_idx
    }
}

/// Classifies a tailored Tamil letter into its orthographic syllable role.
pub fn classify_letter(letter: &str) -> LetterClass {
    if is_aytham(letter) {
        return LetterClass::Aytham;
    }
    if is_mei(letter) {
        return LetterClass::Mei;
    }
    if letter == "\u{0B95}\u{0BCD}\u{0BB7}"
        || letter.starts_with("\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}")
        || letter.starts_with("\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}")
    {
        return LetterClass::AtomicGrantha;
    }
    if split_uyirmei(letter).is_ok() {
        return LetterClass::Uyirmei;
    }
    let qty = classify_quantity(letter);
    if qty == LetterQuantity::Kuril || qty == LetterQuantity::Nedil {
        let inspected = inspect_tamil_string(letter);
        if let Some(first) = inspected.letters.first() {
            if first.classification == "uyir" {
                return LetterClass::Uyir;
            }
            if matches!(
                first.classification,
                "vallinam" | "mellinam" | "idayinam" | "grantha"
            ) {
                return LetterClass::Uyirmei;
            }
        }
    }
    let inspected = inspect_tamil_string(letter);
    if let Some(first) = inspected.letters.first() {
        match first.classification {
            "uyir" => LetterClass::Uyir,
            "vallinam" | "mellinam" | "idayinam" | "grantha" => {
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

/// Computes valid break points within a single NFC-normalized Tamil word using the
/// 5-step Tamil *Asai* (`நேரசை` / `நிரையசை`) + minimum segment algorithm.
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

    let cleaned = strip_existing_hyphens(word);
    let nfc = normalize_nfc(&cleaned);
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

    // Step 1: Partition tailored letters into raw phonetic syllables (Olippasai)
    // Each vowel nucleus absorbs all contiguous following Mei (pulli) and Aytham coda letters.
    let mut raw: Vec<RawSyllable> = Vec::new();
    let mut idx = 0;
    while idx < total_letters {
        let start = idx;
        let mut text = String::from(letters[idx]);
        let mut has_coda = matches!(classes[idx], LetterClass::Mei | LetterClass::Aytham);
        idx += 1;

        while idx < total_letters && matches!(classes[idx], LetterClass::Mei | LetterClass::Aytham)
        {
            text.push_str(letters[idx]);
            has_coda = true;
            idx += 1;
        }

        raw.push(RawSyllable {
            start_letter_idx: start,
            end_letter_idx: idx,
            text,
            has_coda,
        });
    }

    let min_seg = cfg.left_min.min(cfg.right_min);
    let mut asais: Vec<AsaiSegment> = Vec::new();

    if min_seg <= 1 {
        // When caller explicitly sets 1-letter minimum margin, preserve raw phonetic syllables
        for r in &raw {
            asais.push(AsaiSegment {
                start_letter_idx: r.start_letter_idx,
                end_letter_idx: r.end_letter_idx,
                has_coda: r.has_coda,
            });
        }
    } else {
        // Step 2: Word-initial Participle Stem Binding (CVC + 1-letter open -u / -i)
        // e.g., கண் + டு -> கண்டு, இன் + றி -> இன்றி, கன் + னி -> கன்னி
        let mut r_idx = 0;
        if raw.len() >= 2 {
            let first = &raw[0];
            let second = &raw[1];
            let ends_with_u_or_i =
                second.text.ends_with('\u{0BC1}') || second.text.ends_with('\u{0BBF}');
            if first.letter_count() == 2
                && first.has_coda
                && second.letter_count() == 1
                && !second.has_coda
                && ends_with_u_or_i
            {
                asais.push(AsaiSegment {
                    start_letter_idx: first.start_letter_idx,
                    end_letter_idx: second.end_letter_idx,
                    has_coda: false,
                });
                r_idx = 2;
            }
        }

        // Step 3: Forward Nirai-asai Grouping ("குறில் தனித்து அசையாகாது")
        // Any remaining 1-letter open syllable joins forward with the following syllable.
        while r_idx < raw.len() {
            let cur = &raw[r_idx];
            if cur.letter_count() == 1 && !cur.has_coda && r_idx + 1 < raw.len() {
                let next = &raw[r_idx + 1];
                asais.push(AsaiSegment {
                    start_letter_idx: cur.start_letter_idx,
                    end_letter_idx: next.end_letter_idx,
                    has_coda: next.has_coda,
                });
                r_idx += 2;
            } else if cur.letter_count() == 1
                && !cur.has_coda
                && r_idx == raw.len() - 1
                && !asais.is_empty()
            {
                let last = asais.last_mut().unwrap();
                last.end_letter_idx = cur.end_letter_idx;
                last.has_coda = cur.has_coda;
                r_idx += 1;
            } else {
                asais.push(AsaiSegment {
                    start_letter_idx: cur.start_letter_idx,
                    end_letter_idx: cur.end_letter_idx,
                    has_coda: cur.has_coda,
                });
                r_idx += 1;
            }
        }

        // Step 4a: Next-Line Tail Merge (< right_min)
        // Eliminates 2-letter next-line orphans (-கம், -பம், -றல், -றம், -யம், -கள், -கல், -டிப்)
        while asais.len() > 1 && asais.last().unwrap().letter_count() < cfg.right_min {
            let tail = asais.pop().unwrap();
            let prev = asais.last_mut().unwrap();
            prev.end_letter_idx = tail.end_letter_idx;
            prev.has_coda = tail.has_coda;
        }

        // Step 4b: Current-Line Head Merge (< left_min)
        // Eliminates 2-letter leading stubs (பல்-, பள்-, மட்-)
        while asais.len() > 1 && asais[0].letter_count() < cfg.left_min {
            let head = asais.remove(0);
            asais[0].start_letter_idx = head.start_letter_idx;
        }

        // Step 4c: Internal Segment Merge (< min_seg)
        let mut s_idx = 1;
        while s_idx + 1 < asais.len() {
            if asais[s_idx].letter_count() < min_seg {
                let prev_has_coda = asais[s_idx - 1].has_coda;
                let cur_has_coda = asais[s_idx].has_coda;
                if !prev_has_coda && cur_has_coda {
                    let cur = asais.remove(s_idx);
                    asais[s_idx - 1].end_letter_idx = cur.end_letter_idx;
                    asais[s_idx - 1].has_coda = cur.has_coda;
                } else {
                    let cur = asais.remove(s_idx);
                    asais[s_idx].start_letter_idx = cur.start_letter_idx;
                }
            } else {
                s_idx += 1;
            }
        }
    }

    // Step 5: Emit valid break points between adjacent Asai segments
    let mut points = Vec::new();
    for segment in asais.iter().take(asais.len().saturating_sub(1)) {
        let left_count = segment.end_letter_idx;
        let right_count = total_letters - left_count;

        if left_count < cfg.left_min || right_count < cfg.right_min {
            continue;
        }

        let i = left_count - 1;
        if !has_nucleus_before[i] || !has_nucleus_after[i + 1] {
            continue;
        }

        let next_class = classes[i + 1];
        if next_class == LetterClass::Mei || next_class == LetterClass::Aytham {
            continue;
        }
        if !is_syllable_nucleus(next_class) {
            continue;
        }

        let curr_str = letters[i];
        let next_str = letters[i + 1];
        if contains_joiner(curr_str) || contains_joiner(next_str) {
            continue;
        }

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

    let cleaned = strip_existing_hyphens(word);
    let nfc = normalize_nfc(&cleaned);
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
