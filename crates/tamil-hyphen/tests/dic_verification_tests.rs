use serde_json::Value;
use std::fs::File;
use std::io::{BufRead, BufReader};
use std::path::Path;
use tamil_hyphen::dic::{generate_patterns, DicExportOptions};
use tamil_hyphen::verify_dic::LiangEvaluator;

#[test]
fn test_verify_all_golden_hyphen_vectors() {
    // 1. Generate phonotactic Frank Liang dictionary
    let options = DicExportOptions {
        left_hyphen_min: 2,
        right_hyphen_min: 2,
    };
    let dict = generate_patterns(&options);
    let evaluator = LiangEvaluator::new(&dict);

    // 2. Open tests/golden/hyphen_syllable.jsonl
    let path = Path::new("../../tests/golden/hyphen_syllable.jsonl");
    let file = match File::open(path) {
        Ok(f) => f,
        Err(_) => File::open("tests/golden/hyphen_syllable.jsonl")
            .expect("Could not locate tests/golden/hyphen_syllable.jsonl"),
    };

    let reader = BufReader::new(file);
    let mut tested_count = 0;

    for line in reader.lines() {
        let line = line.expect("Failed to read line from golden corpus");
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }

        let val: Value = match serde_json::from_str(trimmed) {
            Ok(v) => v,
            Err(_) => continue,
        };

        if val.get("op").and_then(|v| v.as_str()) != Some("hyphenate_word") {
            continue;
        }

        let word = match val.get("input").and_then(|i| i.get("word")).and_then(|w| w.as_str()) {
            Some(w) => w,
            None => continue,
        };

        let id = val.get("id").and_then(|i| i.as_str()).unwrap_or("unknown");
        let left_min = val.get("input").and_then(|i| i.get("left_min")).and_then(|m| m.as_u64()).unwrap_or(2) as usize;

        let (hyphenated, segments) = evaluator.hyphenate_word(word, "-");
        tested_count += 1;

        // Verify fundamental orthographic safety guarantees across all golden words:
        // Rule A: Never sever Grantha ligatures (ksha க்ஷ)
        assert!(
            !hyphenated.contains("க்-ஷ"),
            "[{}] Severed Grantha ligature க்-ஷ in word '{}': got '{}'",
            id,
            word,
            hyphenated
        );

        // Rule B: Never start a line/segment with a naked virama
        for seg in &segments {
            assert!(
                !seg.starts_with('\u{0BCD}'),
                "[{}] Segment '{}' starts with naked virama in word '{}': full '{}'",
                id,
                seg,
                word,
                hyphenated
            );

            // Rule C: Never start a segment with an isolated pure consonant (except valid onset clusters like ஸ்ரீ)
            let chars: Vec<char> = seg.chars().collect();
            if chars.len() >= 2 && chars[1] == '\u{0BCD}' {
                let is_sri = (chars[0] == '\u{0BB8}' || chars[0] == '\u{0BB6}')
                    && chars.len() >= 4
                    && chars[2] == '\u{0BB0}'
                    && chars[3] == '\u{0BC0}';
                let is_ksha = chars[0] == '\u{0B95}'
                    && chars.len() >= 3
                    && chars[2] == '\u{0BB7}'
                    && (chars.len() == 3 || chars[3] != '\u{0BCD}');

                assert!(
                    is_sri || is_ksha,
                    "[{}] Segment '{}' illegally begins with a pure consonant in word '{}'! Full: '{}'",
                    id,
                    seg,
                    word,
                    hyphenated
                );
            }
        }

        // Rule D: Respect left_min = 2 margin (no 1-character prefix breaks)
        if left_min >= 2 {
            assert!(
                !hyphenated.starts_with(|c: char| c != '-' && hyphenated.chars().nth(1) == Some('-')),
                "[{}] Word '{}' has illegal 1-character prefix hyphenation: '{}'",
                id,
                word,
                hyphenated
            );
        }
    }

    assert!(tested_count > 100, "Expected >100 golden vectors, tested {}", tested_count);
    println!("Successfully verified {tested_count} golden test vectors against Liang pattern dictionary!");
}
