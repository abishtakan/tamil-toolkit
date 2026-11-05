//! Signature patterns, n-grams, and heuristic guards for Tamil encodings.
#![forbid(unsafe_code)]

/// Common English stop words used to penalize typewriter layouts on pure English text.
pub const ENGLISH_WORDS: &[&[u8]] = &[
    b"the", b"and", b"that", b"have", b"for", b"not", b"with", b"you", b"this", b"but", b"his",
    b"from", b"they", b"say", b"her", b"she", b"will", b"one", b"all", b"would", b"there",
    b"their", b"what", b"out", b"about", b"who", b"get", b"which", b"when", b"make", b"can",
    b"like", b"time", b"just", b"him", b"know", b"take", b"people", b"into", b"year", b"your",
    b"good", b"some", b"could", b"them", b"see", b"other", b"than", b"then", b"now", b"look",
    b"only", b"come", b"its", b"over", b"think", b"also", b"back", b"after", b"use", b"two",
    b"how", b"our", b"work", b"first", b"well", b"way", b"even", b"new", b"want", b"because",
    b"any", b"these", b"give", b"day", b"most", b"hello", b"world",
];

/// Checks if an ASCII word matches a common English word.
pub fn is_english_word(token: &[u8]) -> bool {
    let mut lower = [0u8; 16];
    if token.is_empty() || token.len() > 16 {
        return false;
    }
    for (i, &b) in token.iter().enumerate() {
        lower[i] = b.to_ascii_lowercase();
    }
    let slice = &lower[..token.len()];
    ENGLISH_WORDS.contains(&slice)
}

/// Computes the ratio of English words found in ASCII text.
pub fn english_word_density(input: &[u8]) -> f64 {
    let mut words_count = 0usize;
    let mut english_count = 0usize;
    let mut start = None;

    for (i, &b) in input.iter().enumerate() {
        if b.is_ascii_alphabetic() {
            if start.is_none() {
                start = Some(i);
            }
        } else if let Some(s) = start {
            words_count += 1;
            if is_english_word(&input[s..i]) {
                english_count += 1;
            }
            start = None;
        }
    }
    if let Some(s) = start {
        words_count += 1;
        if is_english_word(&input[s..]) {
            english_count += 1;
        }
    }

    if words_count == 0 {
        0.0
    } else {
        english_count as f64 / words_count as f64
    }
}

/// Distinctive Bamini consonants that frequently combine with kombu or vowel signs.
pub const BAMINI_CONSONANTS: &[u8] = b"kcrjgymtldwKpP;h[{";

/// Evaluates presence and density of distinctive Bamini typewriter digraphs.
pub fn bamini_signature_score(input: &[u8]) -> f64 {
    if input.len() < 2 {
        return 0.0;
    }

    let mut matches = 0usize;
    let mut total_pairs = 0usize;

    let mut i = 0;
    while i + 1 < input.len() {
        let b1 = input[i];
        let b2 = input[i + 1];

        // Kombu prefixes: 'n', 'N', 'i' followed by a Tamil consonant
        if (b1 == b'n' || b1 == b'N' || b1 == b'i') && BAMINI_CONSONANTS.contains(&b2) {
            matches += 2;
            i += 2;
            total_pairs += 1;
            continue;
        }

        // Consonant followed by vowel signs: 'h' (ா), 'p' (ி), 'P' (ீ), '[' (ு), '{' (ூ), ';' (்)
        if BAMINI_CONSONANTS.contains(&b1) && matches!(b2, b'h' | b'p' | b'P' | b'[' | b'{' | b';')
        {
            matches += 2;
            i += 2;
            total_pairs += 1;
            continue;
        }

        total_pairs += 1;
        i += 1;
    }

    if total_pairs == 0 {
        0.0
    } else {
        (matches as f64 / (total_pairs * 2) as f64).min(1.0)
    }
}

/// Checks whether a byte slice contains valid UTF-8 Tamil characters (U+0B80..U+0BFF).
pub fn native_utf8_tamil_ratio(input: &[u8]) -> f64 {
    let Ok(s) = std::str::from_utf8(input) else {
        return 0.0;
    };
    let mut total_chars = 0usize;
    let mut tamil_chars = 0usize;
    for c in s.chars() {
        total_chars += 1;
        if ('\u{0B80}'..='\u{0BFF}').contains(&c) {
            tamil_chars += 1;
        }
    }
    if total_chars == 0 {
        0.0
    } else {
        tamil_chars as f64 / total_chars as f64
    }
}

/// Common canonical Tamil roots and words that provide high-confidence boost.
pub const COMMON_TAMIL_WORDS: &[&str] = &[
    "தமிழ்",
    "வாழ்க",
    "வளர்க",
    "நாடு",
    "மற்றும்",
    "என்று",
    "இந்த",
    "ஒரு",
    "அரசு",
    "மொழி",
    "செய்தி",
    "மக்கள்",
    "உலக",
    "கல்வி",
    "பெயர்",
    "நேரம்",
    "மனித",
    "பற்றி",
    "அவர்",
    "இவர்",
    "என்பது",
    "உள்ள",
    "வந்த",
    "செய்த",
    "கொண்டு",
    "போது",
    "கூட",
    "தானே",
    "இல்லை",
    "வேண்டும்",
    "அனைத்து",
    "முதல்",
    "முக்கிய",
    "பதிவு",
    "தகவல்",
    "நன்றி",
    "வணக்கம்",
    "பள்ளி",
    "கல்லூரி",
    "நூல்",
];

/// Common grammatical case markers and inflectional suffixes in Tamil.
pub const COMMON_TAMIL_SUFFIXES: &[&str] =
    &["கள்", "இல்", "க்கு", "உடன்", "ஆக", "வது", "உடைய", "ஆல்", "ஓடு"];

/// Validates orthographic and phonetic naturalness of decoded Tamil Unicode text.
pub fn tamil_orthographic_quality(text: &str) -> f64 {
    let mut total_tamil = 0usize;
    let mut core_consonants = 0usize;
    let mut grantha_consonants = 0usize;
    let mut illegal_sequences = 0usize;

    let chars: Vec<char> = text.chars().collect();
    if chars.is_empty() {
        return 0.0;
    }

    for (i, &c) in chars.iter().enumerate() {
        // Tamil digits (U+0BE6..U+0BF2): cannot be attached immediately to Tamil letters
        if ('\u{0BE6}'..='\u{0BF2}').contains(&c) {
            if i > 0 && ('\u{0B80}'..='\u{0BFF}').contains(&chars[i - 1]) {
                illegal_sequences += 1;
            }
            if i + 1 < chars.len() && ('\u{0B80}'..='\u{0BFF}').contains(&chars[i + 1]) {
                illegal_sequences += 1;
            }
        }

        // Curly quotes or symbols embedded inside words
        if matches!(c, '\u{2018}' | '\u{2019}' | '\u{201C}' | '\u{201D}')
            && i > 0
            && ('\u{0B80}'..='\u{0BFF}').contains(&chars[i - 1])
            && i + 1 < chars.len()
            && ('\u{0B80}'..='\u{0BFF}').contains(&chars[i + 1])
        {
            illegal_sequences += 1;
        }

        if ('\u{0B80}'..='\u{0BFF}').contains(&c) {
            total_tamil += 1;

            // Core Tamil consonants: க, ங, ச, ஞ, ட, ண, த, ந, ப, ம, ய, ர, ல, வ, ழ, ள, ற, ன
            if matches!(
                c,
                '\u{0B95}'
                    | '\u{0B99}'
                    | '\u{0B9A}'
                    | '\u{0B9E}'
                    | '\u{0B9F}'
                    | '\u{0BA3}'
                    | '\u{0BA4}'
                    | '\u{0BA8}'
                    | '\u{0BAA}'
                    | '\u{0BAE}'
                    | '\u{0BAF}'
                    | '\u{0BB0}'
                    | '\u{0BB1}'
                    | '\u{0BB2}'
                    | '\u{0BB3}'
                    | '\u{0BB4}'
                    | '\u{0BB5}'
                    | '\u{0BA9}'
            ) {
                core_consonants += 1;
            }

            // Grantha consonants: ஜ (0B9C), ஷ (0BB7), ஸ (0BB8), ஹ (0BB9)
            if matches!(c, '\u{0B9C}' | '\u{0BB7}' | '\u{0BB8}' | '\u{0BB9}') {
                grantha_consonants += 1;
            }

            // Virama / Pulli: 0x0BCD
            if c == '\u{0BCD}' {
                // Word-initial pulli
                if i == 0 || chars[i - 1].is_whitespace() {
                    illegal_sequences += 1;
                }
                // Pulli preceded by vowel sign or independent vowel
                if i > 0
                    && (('\u{0BBE}'..='\u{0BCC}').contains(&chars[i - 1])
                        || ('\u{0B85}'..='\u{0B94}').contains(&chars[i - 1]))
                {
                    illegal_sequences += 1;
                }
                // Consecutive pullis
                if i + 1 < chars.len() && chars[i + 1] == '\u{0BCD}' {
                    illegal_sequences += 1;
                }
                // Pulli followed by vowel sign
                if i + 1 < chars.len() && ('\u{0BBE}'..='\u{0BCC}').contains(&chars[i + 1]) {
                    illegal_sequences += 1;
                }
            }

            // Consonant followed by independent vowel (e.g. க followed by அ)
            if matches!(c, '\u{0B95}'..='\u{0BB9}')
                && i + 1 < chars.len()
                && ('\u{0B85}'..='\u{0B94}').contains(&chars[i + 1])
            {
                illegal_sequences += 1;
            }

            // Consecutive vowel signs
            if ('\u{0BBE}'..='\u{0BCC}').contains(&c)
                && i + 1 < chars.len()
                && ('\u{0BBE}'..='\u{0BCC}').contains(&chars[i + 1])
            {
                illegal_sequences += 1;
            }
        }
    }

    if total_tamil < 2 || illegal_sequences > 0 {
        return 0.0;
    }

    let all_consonants = core_consonants + grantha_consonants;
    if all_consonants == 0 {
        return 0.0;
    }

    // Heavy penalty for unnatural Grantha explosion
    let grantha_ratio = grantha_consonants as f64 / all_consonants as f64;
    if grantha_ratio > 0.05 {
        let penalty = grantha_ratio * 4.0;
        return (0.95 - penalty).max(0.0);
    }

    // Word and dictionary validation
    let mut score = 0.90;
    if COMMON_TAMIL_WORDS.iter().any(|&w| text.contains(w)) {
        score = 0.98;
    }
    score
}
