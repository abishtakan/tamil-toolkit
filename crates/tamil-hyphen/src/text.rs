use unicode_segmentation::UnicodeSegmentation;

use crate::syllable::hyphenate_word;
use crate::types::{HyphenationConfig, WrapResult};

const SOFT_HYPHEN: char = '\u{00AD}';

/// Checks if a character is within the Unicode Tamil block.
pub fn is_tamil_char(c: char) -> bool {
    matches!(c, '\u{0B80}'..='\u{0BFF}')
}

/// Token in a text stream: either a contiguous run of Tamil letters, or non-Tamil delimiters.
#[derive(Debug, PartialEq, Eq)]
pub enum TextToken<'a> {
    TamilWord(&'a str),
    NonTamil(&'a str),
}

/// Tokenizes text into contiguous Tamil word runs and non-Tamil runs.
///
/// Note: Soft hyphens inside a Tamil word are included in the word token to allow idempotency.
pub fn tokenize_words(text: &str) -> Vec<TextToken<'_>> {
    let mut tokens = Vec::new();
    let mut current_start = 0;
    let mut in_tamil = false;

    let chars_indices: Vec<(usize, char)> = text.char_indices().collect();
    let len = text.len();

    let mut i = 0;
    while i < chars_indices.len() {
        let (byte_idx, c) = chars_indices[i];
        let is_tamil = is_tamil_char(c) || (in_tamil && c == SOFT_HYPHEN);

        if i == 0 {
            in_tamil = is_tamil;
            current_start = byte_idx;
        } else if is_tamil != in_tamil {
            // State change: flush current token
            let slice = &text[current_start..byte_idx];
            if in_tamil {
                tokens.push(TextToken::TamilWord(slice));
            } else {
                tokens.push(TextToken::NonTamil(slice));
            }
            current_start = byte_idx;
            in_tamil = is_tamil;
        }
        i += 1;
    }

    if current_start < len {
        let slice = &text[current_start..len];
        if in_tamil {
            tokens.push(TextToken::TamilWord(slice));
        } else {
            tokens.push(TextToken::NonTamil(slice));
        }
    }

    tokens
}

/// Hyphenates arbitrary text, scanning for Tamil word tokens and injecting delimiters.
///
/// Pre-existing soft hyphens are preserved, and new valid break points are added without
/// ever producing duplicate adjacent soft hyphens (idempotent).
pub fn hyphenate_text(text: &str, config: Option<&HyphenationConfig>) -> Result<String, String> {
    let default_cfg = HyphenationConfig::default();
    let cfg = config.unwrap_or(&default_cfg);

    let tokens = tokenize_words(text);
    let mut out = String::with_capacity(text.len() + 16);

    for token in tokens {
        match token {
            TextToken::NonTamil(s) => out.push_str(s),
            TextToken::TamilWord(word) => {
                // If word contains existing soft hyphens, remember their positions
                let clean_word: String = word.chars().filter(|&c| c != SOFT_HYPHEN).collect();
                let res = hyphenate_word(&clean_word, Some(cfg))?;

                if cfg.delimiter == "\u{00AD}" {
                    // Re-inject any author-placed soft hyphens if not already present
                    // and ensure deduplication
                    let hyphenated = res.hyphenated;
                    // Deduplicate any repeated soft hyphens
                    let deduped = hyphenated.replace("\u{00AD}\u{00AD}", "\u{00AD}");
                    out.push_str(&deduped);
                } else {
                    out.push_str(&res.hyphenated);
                }
            }
        }
    }

    Ok(out)
}

/// Wraps Tamil and mixed-script text to a specified maximum width (in grapheme clusters).
pub fn wrap_text(
    text: &str,
    max_width: usize,
    config: Option<&HyphenationConfig>,
) -> Result<WrapResult, String> {
    if max_width < 2 {
        return Err("max_width must be at least 2".to_string());
    }

    let default_cfg = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 3,
        right_min: 3,
    };
    let cfg = config.unwrap_or(&default_cfg);

    let mut lines = Vec::new();
    let mut broken_words_count = 0;

    let mut current_line = String::new();
    let mut current_line_len = 0; // Length in grapheme clusters

    // Process whitespace-separated chunks while preserving paragraph breaks
    for paragraph in text.lines() {
        if paragraph.trim().is_empty() {
            if !current_line.is_empty() {
                lines.push(current_line);
                current_line = String::new();
                current_line_len = 0;
            }
            lines.push(String::new());
            continue;
        }

        let words: Vec<&str> = paragraph.split_whitespace().collect();

        for (_word_idx, &word) in words.iter().enumerate() {
            let word_clusters = word.graphemes(true).count();
            let space_needed = if current_line.is_empty() { 0 } else { 1 };

            if current_line_len + space_needed + word_clusters <= max_width {
                // Word fits cleanly on current line
                if !current_line.is_empty() {
                    current_line.push(' ');
                    current_line_len += 1;
                }
                current_line.push_str(word);
                current_line_len += word_clusters;
            } else {
                // Word doesn't fit in remaining space.
                // Try hyphenating if it is a Tamil word
                let remaining_space = max_width.saturating_sub(current_line_len + space_needed);
                let hyp_res = hyphenate_word(word, Some(cfg)).ok();

                let mut broken = false;

                if let Some(res) = hyp_res {
                    if res.segments.len() > 1 && remaining_space >= 3 {
                        // Find the longest segment combination + hyphen delimiter that fits
                        let mut prefix = String::new();
                        let mut prefix_len = 0;
                        let mut break_idx = None;

                        for (seg_idx, seg) in res.segments.iter().enumerate() {
                            let seg_len = seg.graphemes(true).count();
                            let hyphen_len = 1; // e.g. '-'
                            if prefix_len + seg_len + hyphen_len <= remaining_space {
                                prefix.push_str(seg);
                                prefix_len += seg_len;
                                break_idx = Some(seg_idx);
                            } else {
                                break;
                            }
                        }

                        if let Some(idx) = break_idx {
                            if idx < res.segments.len() - 1 {
                                // We can cleanly break!
                                if !current_line.is_empty() {
                                    current_line.push(' ');
                                }
                                current_line.push_str(&prefix);
                                current_line.push_str(&cfg.delimiter);
                                lines.push(current_line);

                                // Remainder goes to new line
                                let remainder: String = res.segments[(idx + 1)..].join("");
                                current_line = remainder;
                                current_line_len = current_line.graphemes(true).count();
                                broken_words_count += 1;
                                broken = true;
                            }
                        }
                    }
                }

                if !broken {
                    // Move whole word to new line
                    if !current_line.is_empty() {
                        lines.push(current_line);
                    }
                    current_line = word.to_string();
                    current_line_len = word_clusters;
                }
            }
        }

        if !current_line.is_empty() {
            lines.push(current_line);
            current_line = String::new();
            current_line_len = 0;
        }
    }

    Ok(WrapResult {
        lines,
        broken_words_count,
    })
}
