use tamil_hyphen::dic::{generate_patterns, DicExportOptions};
use tamil_hyphen::verify_dic::LiangEvaluator;

#[test]
fn test_generate_patterns_contains_header_and_rules() {
    let options = DicExportOptions {
        left_hyphen_min: 2,
        right_hyphen_min: 2,
    };
    let dict = generate_patterns(&options);

    assert_eq!(dict.header.left_hyphen_min, 2);
    assert_eq!(dict.header.right_hyphen_min, 2);
    assert_eq!(dict.header.encoding, "UTF-8");
    assert!(!dict.patterns.is_empty());

    // Check specific critical rules exist
    let patterns_raw: Vec<&str> = dict.patterns.iter().map(|p| p.raw.as_str()).collect();

    // 1. ZWJ protection
    assert!(patterns_raw.iter().any(|p| *p == "2\u{200D}2"));

    // 2. Aytham protection (no break before Aytham)
    assert!(patterns_raw.iter().any(|p| *p == "2\u{0B83}1" || *p == "2\u{0B83}"));

    // 3. Grantha ligature protection (never break inside Ksha க்ஷ)
    assert!(patterns_raw.iter().any(|p| p.contains("க்2ஷ") || p.contains("க\u{0BCD}2ஷ")));

    // 4. Consecutive pure consonant cluster protection (no break between two pure consonants)
    assert!(patterns_raw.iter().any(|p| p.contains("\u{0BCD}2")));
}

#[test]
fn test_liang_evaluator_preserves_grantha_ksha() {
    let options = DicExportOptions::default();
    let dict = generate_patterns(&options);
    let evaluator = LiangEvaluator::new(&dict);

    // தக்ஷிணம் (letters: த, க்ஷ, ி, ண, ம்) -> syllables: தக், ஷி, ணம் or த, க்ஷி, ணம்
    // Under no circumstances should க் and ஷ be separated across lines (க்-ஷ)!
    let (hyphenated, segments) = evaluator.hyphenate_word("தக்ஷிணம்", "-");
    assert!(!hyphenated.contains("தக்-ஷ"), "Severed Grantha ligature க்-ஷ in தக்ஷிணம்: {}", hyphenated);
    for seg in &segments {
        assert!(!seg.ends_with("க்") || !seg.starts_with('ஷ'));
    }
}

#[test]
fn test_liang_evaluator_never_starts_segment_with_pure_consonant() {
    let options = DicExportOptions::default();
    let dict = generate_patterns(&options);
    let evaluator = LiangEvaluator::new(&dict);

    let test_words = [
        "தமிழ்நாடு",
        "பல்கலைக்கழகம்",
        "திருக்குறள்",
        "வணக்கம்",
        "செம்மொழி",
        "அகிலத்திரட்டு",
        "துர்ப்பிரயோகம்",
    ];

    for word in test_words {
        let (hyphenated, segments) = evaluator.hyphenate_word(word, "-");
        for seg in &segments {
            assert!(
                !seg.starts_with('\u{0BCD}'),
                "Segment '{}' in word '{}' starts with naked virama! Full: {}",
                seg, word, hyphenated
            );
            if seg.chars().count() > 1 {
                let second = seg.chars().nth(1).unwrap();
                assert_ne!(
                    second, '\u{0BCD}',
                    "Segment '{}' in word '{}' illegally starts with a pure consonant! Full: {}",
                    seg, word, hyphenated
                );
            }
        }
    }
}

#[test]
fn test_liang_evaluator_respects_margins() {
    let options = DicExportOptions {
        left_hyphen_min: 2,
        right_hyphen_min: 2,
    };
    let dict = generate_patterns(&options);
    let evaluator = LiangEvaluator::new(&dict);

    // "கல்" is 2 letters / 3 chars, cannot break
    let (h1, segs1) = evaluator.hyphenate_word("கல்", "-");
    assert_eq!(h1, "கல்");
    assert_eq!(segs1.len(), 1);

    // "அம்மா" (அ, ம், மா) - 1-letter prefix break (அ-ம்மா) must be forbidden by left_min = 2!
    let (h2, _) = evaluator.hyphenate_word("அம்மா", "-");
    assert!(!h2.starts_with("அ-"), "Forbidden 1-letter prefix break in அம்மா: {}", h2);
}
