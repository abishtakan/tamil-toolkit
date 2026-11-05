use tamil_hyphen::{
    classify_letter, hyphenate_word, hyphenation_points, HyphenationConfig, LetterClass,
};

#[test]
fn test_letter_classification() {
    assert_eq!(classify_letter("அ"), LetterClass::Uyir);
    assert_eq!(classify_letter("ஆ"), LetterClass::Uyir);
    assert_eq!(classify_letter("க"), LetterClass::Uyirmei);
    assert_eq!(classify_letter("கி"), LetterClass::Uyirmei);
    assert_eq!(classify_letter("கை"), LetterClass::Uyirmei);
    assert_eq!(classify_letter("க்"), LetterClass::Mei);
    assert_eq!(classify_letter("த்"), LetterClass::Mei);
    assert_eq!(classify_letter("ஃ"), LetterClass::Aytham);
    assert_eq!(classify_letter("க்ஷ"), LetterClass::AtomicGrantha);
    assert_eq!(classify_letter("ஸ்ரீ"), LetterClass::AtomicGrantha);
}

#[test]
fn test_word_hyphenation_coda_binding() {
    let res = hyphenate_word("தமிழ்நாடு", None).expect("valid hyphenation");
    // "தமிழ்நாடு" has letters: த, மி, ழ், நா, டு
    // Break after ழ் (left=3, right=2)
    assert_eq!(res.segments, vec!["தமிழ்", "நாடு"]);
    assert_eq!(res.hyphenated, "தமிழ்\u{00AD}நாடு");

    // "பல்கலைக்கழகம்": பல் / கலைக் / க / ழ / கம்
    let res2 = hyphenate_word("பல்கலைக்கழகம்", None).expect("valid hyphenation");
    assert_eq!(res2.segments, vec!["பல்", "க", "லைக்", "க", "ழ", "கம்"]);
    assert_eq!(res2.hyphenated, "பல்\u{00AD}க\u{00AD}லைக்\u{00AD}க\u{00AD}ழ\u{00AD}கம்");
    // Verify each break preserves coda and starts with vowel/composite
    for seg in &res2.segments {
        let first_letter = tamil_core::Letters::new(seg).next().unwrap();
        assert_ne!(classify_letter(first_letter), LetterClass::Mei);
    }
}

#[test]
fn test_never_start_with_mei_or_aytham() {
    // Test cluster word "துர்ப்பிரயோகம்"
    let res = hyphenate_word("துர்ப்பிரயோகம்", None).expect("valid hyphenation");
    for seg in &res.segments {
        assert!(
            !seg.starts_with('்') && !seg.starts_with('ஃ'),
            "Segment must never start with a pulli or aytham: {}",
            seg
        );
        let first_letter = tamil_core::Letters::new(seg).next().unwrap();
        let class = classify_letter(first_letter);
        assert_ne!(
            class,
            LetterClass::Mei,
            "Segment must never start with a pure consonant (Mei): {}",
            seg
        );
        assert_ne!(
            class,
            LetterClass::Aytham,
            "Segment must never start with Aytham: {}",
            seg
        );
    }
}

#[test]
fn test_margin_enforcement() {
    // "அரசு" has 3 letters: அ, ர, சு.
    // With left_min=2, right_min=2 (sum=4), it should not break.
    let res = hyphenate_word("அரசு", None).expect("valid");
    assert_eq!(res.segments.len(), 1);
    assert_eq!(res.segments[0], "அரசு");

    // With left_min=1, right_min=1, break is possible between syllables: அ / ர / சு
    let cfg = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 1,
        right_min: 1,
    };
    let res_custom = hyphenate_word("அரசு", Some(&cfg)).expect("valid");
    assert_eq!(res_custom.segments, vec!["அ", "ர", "சு"]);
}

#[test]
fn test_configuration_validation_errors() {
    let bad_left = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 0,
        right_min: 2,
    };
    assert!(hyphenation_points("தமிழ்நாடு", Some(&bad_left)).is_err());

    let bad_right = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 2,
        right_min: 0,
    };
    assert!(hyphenation_points("தமிழ்நாடு", Some(&bad_right)).is_err());
}
