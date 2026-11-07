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
fn test_short_words_remain_unbroken_under_default_3_3() {
    let short_words = [
        "உலகம்",
        "சமூகம்",
        "வணிகம்",
        "திட்டம்",
        "வரலாறு",
        "தலைமுறை",
        "அறிவியல்",
        "விவசாயம்",
        "முடிவுகள்",
        "பாதுகாக்க",
        "வணக்கம்",
        "தமிழ்நாடு",
    ];

    for word in short_words {
        let res = hyphenate_word(word, None).expect("valid hyphenation");
        assert_eq!(
            res.segments,
            vec![word],
            "Short word (<6 letters) '{}' must remain unbroken under default 3/3",
            word
        );
        assert_eq!(res.hyphenated, word);
    }
}

#[test]
fn test_word_hyphenation_asai_and_3_letter_segments() {
    // "பல்கலைக்கழகம்": பல்கலைக்-கழகம்
    let res = hyphenate_word("பல்கலைக்கழகம்", None).expect("valid hyphenation");
    assert_eq!(res.segments, vec!["பல்கலைக்", "கழகம்"]);
    assert_eq!(res.hyphenated, "பல்கலைக்\u{00AD}கழகம்");

    // "பல்கலைக்கழகங்களில்": பல்கலைக்-கழகங்-களில்
    let res_long = hyphenate_word("பல்கலைக்கழகங்களில்", None).expect("valid hyphenation");
    assert_eq!(res_long.segments, vec!["பல்கலைக்", "கழகங்", "களில்"]);

    // "தொழில்நுட்பம்": தொழில்-நுட்பம் (no 2-letter -பம் orphan on next line)
    let res_tech = hyphenate_word("தொழில்நுட்பம்", None).expect("valid hyphenation");
    assert_eq!(res_tech.segments, vec!["தொழில்", "நுட்பம்"]);

    // "படைப்பாற்றல்": படைப்-பாற்றல் (no 2-letter -றல் orphan on next line)
    let res_creativity = hyphenate_word("படைப்பாற்றல்", None).expect("valid hyphenation");
    assert_eq!(res_creativity.segments, vec!["படைப்", "பாற்றல்"]);

    // "கண்டுபிடிப்பு": கண்டு-பிடிப்பு (CVC + u stem binding)
    let res_disc = hyphenate_word("கண்டுபிடிப்பு", None).expect("valid hyphenation");
    assert_eq!(res_disc.segments, vec!["கண்டு", "பிடிப்பு"]);

    // "இன்றியமையாத": இன்றி-யமையாத (CVC + i stem binding)
    let res_ess = hyphenate_word("இன்றியமையாத", None).expect("valid hyphenation");
    assert_eq!(res_ess.segments, vec!["இன்றி", "யமையாத"]);

    // "திருச்சிராப்பள்ளி": திருச்-சிராப்-பள்ளி
    let res_trichy = hyphenate_word("திருச்சிராப்பள்ளி", None).expect("valid hyphenation");
    assert_eq!(res_trichy.segments, vec!["திருச்", "சிராப்", "பள்ளி"]);

    // "ஒருங்கிணைக்கப்பட்ட": ஒருங்-கிணைக்-கப்பட்ட
    let res_integ = hyphenate_word("ஒருங்கிணைக்கப்பட்ட", None).expect("valid hyphenation");
    assert_eq!(res_integ.segments, vec!["ஒருங்", "கிணைக்", "கப்பட்ட"]);
}

#[test]
fn test_never_start_with_mei_or_aytham() {
    let words = ["துர்ப்பிரயோகம்", "வாழ்த்துகள்", "ஆராய்ச்சிகள்", "பல்கலைக்கழகம்"];
    for w in words {
        let res = hyphenate_word(w, None).expect("valid hyphenation");
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
}

#[test]
fn test_margin_enforcement_and_custom_overrides() {
    // "அரசு" has 3 letters: அ, ர, சு.
    // With default left_min=3, right_min=3 (sum=6), it should not break.
    let res = hyphenate_word("அரசு", None).expect("valid");
    assert_eq!(res.segments.len(), 1);
    assert_eq!(res.segments[0], "அரசு");

    // With left_min=1, right_min=1, break is possible between raw phonetic syllables: அ / ர / சு
    let cfg = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 1,
        right_min: 1,
    };
    let res_custom = hyphenate_word("அரசு", Some(&cfg)).expect("valid");
    assert_eq!(res_custom.segments, vec!["அ", "ர", "சு"]);

    // With left_min=3, right_min=2, "தமிழ்நாடு" (5 letters) splits as தமிழ்-நாடு
    let cfg_3_2 = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 3,
        right_min: 2,
    };
    let res_tn = hyphenate_word("தமிழ்நாடு", Some(&cfg_3_2)).expect("valid");
    assert_eq!(res_tn.segments, vec!["தமிழ்", "நாடு"]);
}

#[test]
fn test_idempotent_healing_of_existing_soft_hyphens() {
    // Previously hyphenated short word "உல\u{00AD}கம்" heals to unbroken "உலகம்"
    let healed = hyphenate_word("உல\u{00AD}கம்", None).expect("valid");
    assert_eq!(healed.hyphenated, "உலகம்");
    assert_eq!(healed.segments, vec!["உலகம்"]);
}

#[test]
fn test_configuration_validation_errors() {
    let bad_left = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 0,
        right_min: 3,
    };
    assert!(hyphenation_points("தமிழ்நாடு", Some(&bad_left)).is_err());

    let bad_right = HyphenationConfig {
        delimiter: "-".to_string(),
        left_min: 3,
        right_min: 0,
    };
    assert!(hyphenation_points("தமிழ்நாடு", Some(&bad_right)).is_err());
}
