use tamil_core::get_olippasai;

#[test]
fn test_basic_syllables() {
    let text = "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"; // தமிழ்
    let syllables: Vec<_> = get_olippasai(text).collect();

    assert_eq!(syllables.len(), 2);

    assert_eq!(syllables[0].text, "\u{0BA4}"); // த
    assert_eq!(syllables[0].start_byte, 0);
    assert_eq!(syllables[0].end_byte, 3);
    assert_eq!(syllables[0].start_letter_idx, 0);
    assert_eq!(syllables[0].end_letter_idx, 1);
    assert!(!syllables[0].has_coda);
    assert_eq!(syllables[0].coda_count, 0);

    assert_eq!(syllables[1].text, "\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"); // மிழ்
    assert_eq!(syllables[1].start_byte, 3);
    assert_eq!(syllables[1].end_byte, 15);
    assert_eq!(syllables[1].start_letter_idx, 1);
    assert_eq!(syllables[1].end_letter_idx, 3);
    assert!(syllables[1].has_coda);
    assert_eq!(syllables[1].coda_count, 1);
}

#[test]
fn test_syllables_with_internal_coda() {
    let text = "\u{0B95}\u{0BB1}\u{0BCD}\u{0BAA}\u{0BA9}\u{0BC8}"; // கற்பனை
    let syllables: Vec<_> = get_olippasai(text).collect();

    assert_eq!(syllables.len(), 3);
    assert_eq!(syllables[0].text, "\u{0B95}\u{0BB1}\u{0BCD}"); // கற்
    assert_eq!(syllables[0].start_byte, 0);
    assert_eq!(syllables[0].end_byte, 9);
    assert!(syllables[0].has_coda);

    assert_eq!(syllables[1].text, "\u{0BAA}"); // ப
    assert_eq!(syllables[1].start_byte, 9);
    assert_eq!(syllables[1].end_byte, 12);
    assert!(!syllables[1].has_coda);

    assert_eq!(syllables[2].text, "\u{0BA9}\u{0BC8}"); // னை
    assert_eq!(syllables[2].start_byte, 12);
    assert_eq!(syllables[2].end_byte, 18);
    assert!(!syllables[2].has_coda);
}

#[test]
fn test_syllables_with_aytham() {
    let text = "\u{0B85}\u{0B83}\u{0BA4}\u{0BC1}"; // அஃது
    let syllables: Vec<_> = get_olippasai(text).collect();

    assert_eq!(syllables.len(), 2);
    assert_eq!(syllables[0].text, "\u{0B85}\u{0B83}"); // அஃ
    assert!(syllables[0].has_coda);
    assert_eq!(syllables[1].text, "\u{0BA4}\u{0BC1}"); // து
    assert!(!syllables[1].has_coda);
}

#[test]
fn test_loanword_initial_consonant_cluster() {
    // ஸ்டார் (ஸ் + டார்) -> attaches leading ஸ் to டார்
    let text = "\u{0BB8}\u{0BCD}\u{0B9F}\u{0BBE}\u{0BB0}\u{0BCD}";
    let syllables: Vec<_> = get_olippasai(text).collect();

    assert_eq!(syllables.len(), 1);
    assert_eq!(syllables[0].text, text);
    assert_eq!(syllables[0].start_byte, 0);
    assert_eq!(syllables[0].end_byte, 18);
    assert!(syllables[0].has_coda);
}

#[test]
fn test_full_reconstitution() {
    let sample = "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD} \u{0B95}\u{0BB1}\u{0BCD}\u{0BAA}\u{0BA9}\u{0BC8} 123!";
    let syllables: Vec<_> = get_olippasai(sample).collect();
    let reconstituted: String = syllables.iter().map(|s| s.text).collect();
    assert_eq!(reconstituted, sample);
}
