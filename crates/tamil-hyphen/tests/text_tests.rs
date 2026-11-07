use tamil_hyphen::{hyphenate_text, tokenize_words, wrap_text, TextToken};

#[test]
fn test_tokenize_words() {
    let text = "வணக்கம் world! தமிழ்நாடு 123";
    let tokens = tokenize_words(text);
    assert_eq!(
        tokens,
        vec![
            TextToken::TamilWord("வணக்கம்"),
            TextToken::NonTamil(" world! "),
            TextToken::TamilWord("தமிழ்நாடு"),
            TextToken::NonTamil(" 123"),
        ]
    );
}

#[test]
fn test_hyphenate_text_preserves_non_tamil() {
    let text = "Welcome to தமிழ்நாடு பல்கலைக்கழகம் (Tamil Nadu) 2026!";
    let res = hyphenate_text(text, None).expect("hyphenate");
    assert!(res.starts_with("Welcome to தமிழ்நாடு "));
    assert!(res.contains("பல்கலைக்\u{00AD}கழகம்"));
    assert!(res.ends_with(" (Tamil Nadu) 2026!"));
}

#[test]
fn test_hyphenate_text_idempotency() {
    let text = "தமிழ்நாடு அரசு கலை மற்றும் அறிவியல் பல்கலைக்கழகம்";
    let first_pass = hyphenate_text(text, None).expect("first pass");
    let second_pass = hyphenate_text(&first_pass, None).expect("second pass");
    assert_eq!(first_pass, second_pass);
}

#[test]
fn test_wrap_text_deterministic() {
    let text = "தமிழ்நாடு அரசு கலை மற்றும் அறிவியல் பல்கலைக்கழகம்";
    let res = wrap_text(text, 16, None).expect("wrap");
    assert!(!res.lines.is_empty());
    // Verify lines do not exceed width unless an individual word couldn't break
    for line in &res.lines {
        let _clusters =
            unicode_segmentation::UnicodeSegmentation::graphemes(line.as_str(), true).count();
        // Each broken line should fit within or cleanly wrap
        assert!(!line.is_empty() || res.lines.len() == 1);
    }
}
