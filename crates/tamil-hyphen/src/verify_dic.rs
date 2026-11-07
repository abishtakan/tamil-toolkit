use crate::types::{HyphenDictionary, LiangPattern};
use std::cmp::max;

/// A simulated Frank Liang pattern evaluator for validating .dic files against test words.
#[derive(Debug, Clone)]
pub struct LiangEvaluator {
    pub patterns: Vec<LiangPattern>,
    pub left_min: usize,
    pub right_min: usize,
}

impl LiangEvaluator {
    /// Create a new evaluator from a `HyphenDictionary`.
    pub fn new(dict: &HyphenDictionary) -> Self {
        Self {
            patterns: dict.patterns.clone(),
            left_min: dict.header.left_hyphen_min,
            right_min: dict.header.right_hyphen_min,
        }
    }

    /// Parse raw `.dic` file content directly into an evaluator.
    pub fn from_dic_content(content: &str) -> Self {
        let mut left_min = 2;
        let mut right_min = 2;
        let mut patterns = Vec::new();

        for line in content.lines() {
            let trimmed = line.trim();
            if trimmed.is_empty() || trimmed.starts_with('%') {
                continue;
            }
            if let Some(rest) = trimmed.strip_prefix("LEFTHYPHENMIN") {
                if let Ok(val) = rest.trim().parse::<usize>() {
                    left_min = val;
                }
                continue;
            }
            if let Some(rest) = trimmed.strip_prefix("RIGHTHYPHENMIN") {
                if let Ok(val) = rest.trim().parse::<usize>() {
                    right_min = val;
                }
                continue;
            }
            if trimmed == "UTF-8" || trimmed.starts_with("ISO") {
                continue;
            }

            if let Some(pat) = LiangPattern::parse(trimmed) {
                patterns.push(pat);
            }
        }

        Self {
            patterns,
            left_min,
            right_min,
        }
    }

    /// Evaluate a single Tamil word and return its hyphenation break points (char indices).
    pub fn hyphenate_word(&self, word: &str, delimiter: &str) -> (String, Vec<String>) {
        let chars: Vec<char> = word.chars().collect();
        let char_count = chars.len();

        if char_count < self.left_min + self.right_min {
            return (word.to_string(), vec![word.to_string()]);
        }

        // word_weights has length chars.len() + 1
        let mut weights = vec![0u8; char_count + 1];

        // Match every pattern against every substring in the word
        for pat in &self.patterns {
            let pat_chars: Vec<char> = pat.text.chars().collect();
            let pat_len = pat_chars.len();

            if pat_len == 0 || pat_len > char_count {
                continue;
            }

            for start in 0..=(char_count - pat_len) {
                if chars[start..start + pat_len] == pat_chars[..] {
                    for (offset, &w) in pat.weights.iter().enumerate() {
                        let idx = start + offset;
                        if idx < weights.len() {
                            weights[idx] = max(weights[idx], w);
                        }
                    }
                }
            }
        }

        // Collect break points respecting left_min and right_min
        let mut break_positions = Vec::new();
        for (i, &w) in weights.iter().enumerate() {
            if i >= self.left_min && i <= char_count.saturating_sub(self.right_min) && w % 2 == 1 {
                break_positions.push(i);
            }
        }

        if break_positions.is_empty() {
            return (word.to_string(), vec![word.to_string()]);
        }

        let mut segments = Vec::new();
        let mut last_idx = 0;
        for &bp in &break_positions {
            let seg: String = chars[last_idx..bp].iter().collect();
            if !seg.is_empty() {
                segments.push(seg);
            }
            last_idx = bp;
        }
        let tail: String = chars[last_idx..].iter().collect();
        if !tail.is_empty() {
            segments.push(tail);
        }

        let hyphenated = segments.join(delimiter);
        (hyphenated, segments)
    }
}
