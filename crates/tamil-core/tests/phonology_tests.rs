use tamil_core::{
    are_cognates, baseline_maathirai, classify_quantity, get_cognate, is_aytham, is_kuril, is_mei,
    is_nedil, is_otru, LetterQuantity, Maathirai,
};

#[test]
fn test_independent_vowel_quantities() {
    // Short vowels (Kuril) = 1.0 mora
    let short_vowels = ["\u{0B85}", "\u{0B87}", "\u{0B89}", "\u{0B8E}", "\u{0B92}"];
    for v in short_vowels {
        assert_eq!(
            classify_quantity(v),
            LetterQuantity::Kuril,
            "failed for {v}"
        );
        assert_eq!(baseline_maathirai(v), Maathirai::KURIL);
        assert!(is_kuril(v));
        assert!(!is_nedil(v));
        assert!(!is_mei(v));
    }

    // Long vowels (Nedil) = 2.0 morae
    let long_vowels = [
        "\u{0B86}", "\u{0B88}", "\u{0B8A}", "\u{0B8F}", "\u{0B90}", "\u{0B93}", "\u{0B94}",
    ];
    for v in long_vowels {
        assert_eq!(
            classify_quantity(v),
            LetterQuantity::Nedil,
            "failed for {v}"
        );
        assert_eq!(baseline_maathirai(v), Maathirai::NEDIL);
        assert!(is_nedil(v));
        assert!(!is_kuril(v));
    }
}

#[test]
fn test_uyirmei_quantities() {
    // Kuril composites: க, கி, கு, தெ, நொ
    let short_composites = [
        "\u{0B95}",
        "\u{0B95}\u{0BBF}",
        "\u{0B95}\u{0BC1}",
        "\u{0BA4}\u{0BC6}",
        "\u{0BA8}\u{0BCA}",
    ];
    for c in short_composites {
        assert_eq!(
            classify_quantity(c),
            LetterQuantity::Kuril,
            "failed for {c}"
        );
        assert_eq!(baseline_maathirai(c).value(), 1.0);
        assert!(is_kuril(c));
        assert!(!is_nedil(c));
    }

    // Nedil composites: கா, கீ, கூ, தே, கை, நோ, கௌ
    let long_composites = [
        "\u{0B95}\u{0BBE}",
        "\u{0B95}\u{0BC0}",
        "\u{0B95}\u{0BC2}",
        "\u{0BA4}\u{0BC7}",
        "\u{0B95}\u{0BC8}",
        "\u{0BA8}\u{0BCB}",
        "\u{0B95}\u{0BCC}",
    ];
    for c in long_composites {
        assert_eq!(
            classify_quantity(c),
            LetterQuantity::Nedil,
            "failed for {c}"
        );
        assert_eq!(baseline_maathirai(c).value(), 2.0);
        assert!(is_nedil(c));
        assert!(!is_kuril(c));
    }
}

#[test]
fn test_pure_consonant_quantities() {
    let pure_consonants = [
        "\u{0B95}\u{0BCD}", // க்
        "\u{0B99}\u{0BCD}", // ங்
        "\u{0BA4}\u{0BCD}", // த்
        "\u{0BAE}\u{0BCD}", // ம்
        "\u{0BB4}\u{0BCD}", // ழ்
        "\u{0B9C}\u{0BCD}", // ஜ் (Grantha)
        "\u{0BB7}\u{0BCD}", // ஷ் (Grantha)
        "\u{0BB8}\u{0BCD}", // ஸ் (Grantha)
        "\u{0BB9}\u{0BCD}", // ஹ் (Grantha)
    ];
    for m in pure_consonants {
        assert_eq!(classify_quantity(m), LetterQuantity::Mei, "failed for {m}");
        assert_eq!(baseline_maathirai(m), Maathirai::MEI);
        assert_eq!(baseline_maathirai(m).as_fraction(), (1, 2));
        assert!(is_mei(m));
        assert!(is_otru(m));
        assert!(!is_kuril(m));
        assert!(!is_nedil(m));
    }
}

#[test]
fn test_aytham_quantity() {
    let aytham = "\u{0B83}"; // ஃ
    assert_eq!(classify_quantity(aytham), LetterQuantity::Aytham);
    assert_eq!(baseline_maathirai(aytham), Maathirai::AYTHAM);
    assert!(is_aytham(aytham));
    assert!(!is_mei(aytham));
    assert!(!is_kuril(aytham));
}

#[test]
fn test_atomic_grantha_quantities() {
    // Ksha (க்ஷ) without vowel sign = Kuril
    assert_eq!(
        classify_quantity("\u{0B95}\u{0BCD}\u{0BB7}"),
        LetterQuantity::Kuril
    );
    assert_eq!(baseline_maathirai("\u{0B95}\u{0BCD}\u{0BB7}").value(), 1.0);

    // Ksha with long aa (க்ஷா) = Nedil
    assert_eq!(
        classify_quantity("\u{0B95}\u{0BCD}\u{0BB7}\u{0BBE}"),
        LetterQuantity::Nedil
    );

    // Ksha with pulli (க்ஷ்) = Mei
    assert_eq!(
        classify_quantity("\u{0B95}\u{0BCD}\u{0BB7}\u{0BCD}"),
        LetterQuantity::Mei
    );

    // Shri (ஸ்ரீ) = Nedil
    assert_eq!(
        classify_quantity("\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}"),
        LetterQuantity::Nedil
    );
    assert_eq!(
        classify_quantity("\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}"),
        LetterQuantity::Nedil
    );
}

#[test]
fn test_non_tamil_and_other() {
    assert_eq!(classify_quantity("A"), LetterQuantity::Other);
    assert_eq!(baseline_maathirai("A"), Maathirai::ZERO);
    assert_eq!(classify_quantity("1"), LetterQuantity::Other);
    assert_eq!(classify_quantity(" "), LetterQuantity::Other);
}

#[test]
fn test_homorganic_cognate_pairs() {
    // Consonant pairs (Vallinam <-> Mellinam)
    assert_eq!(
        get_cognate("\u{0B95}\u{0BCD}"),
        Some("\u{0B99}\u{0BCD}".to_string())
    ); // க் <-> ங்
    assert_eq!(
        get_cognate("\u{0B99}\u{0BCD}"),
        Some("\u{0B95}\u{0BCD}".to_string())
    );
    assert_eq!(
        get_cognate("\u{0B9A}\u{0BCD}"),
        Some("\u{0B9E}\u{0BCD}".to_string())
    ); // ச் <-> ஞ்
    assert_eq!(
        get_cognate("\u{0B9F}\u{0BCD}"),
        Some("\u{0BA3}\u{0BCD}".to_string())
    ); // ட் <-> ண்
    assert_eq!(
        get_cognate("\u{0BA4}\u{0BCD}"),
        Some("\u{0BA8}\u{0BCD}".to_string())
    ); // த் <-> ந்
    assert_eq!(
        get_cognate("\u{0BAA}\u{0BCD}"),
        Some("\u{0BAE}\u{0BCD}".to_string())
    ); // ப் <-> ம்
    assert_eq!(
        get_cognate("\u{0BB1}\u{0BCD}"),
        Some("\u{0BA9}\u{0BCD}".to_string())
    ); // ற் <-> ன்

    // Vowel pairs
    assert_eq!(get_cognate("\u{0B85}"), Some("\u{0B86}".to_string())); // அ <-> ஆ
    assert_eq!(get_cognate("\u{0B86}"), Some("\u{0B85}".to_string()));
    assert_eq!(get_cognate("\u{0B87}"), Some("\u{0B88}".to_string())); // இ <-> ஈ
    assert_eq!(get_cognate("\u{0B89}"), Some("\u{0B8A}".to_string())); // உ <-> ஊ
    assert_eq!(get_cognate("\u{0B8E}"), Some("\u{0B8F}".to_string())); // எ <-> ஏ
    assert_eq!(get_cognate("\u{0B92}"), Some("\u{0B93}".to_string())); // ஒ <-> ஓ
    assert_eq!(get_cognate("\u{0B90}"), Some("\u{0B87}".to_string())); // ஐ <-> இ
    assert_eq!(get_cognate("\u{0B94}"), Some("\u{0B89}".to_string())); // ஔ <-> உ

    // Composite Uyirmei mapping
    assert_eq!(
        get_cognate("\u{0B95}\u{0BBE}"),
        Some("\u{0B99}\u{0BBE}".to_string())
    ); // கா <-> ஙா
    assert_eq!(
        get_cognate("\u{0B95}\u{0BBF}"),
        Some("\u{0B99}\u{0BBF}".to_string())
    ); // கி <-> ஙி
    assert_eq!(
        get_cognate("\u{0BA4}\u{0BC2}"),
        Some("\u{0BA8}\u{0BC2}".to_string())
    ); // தூ <-> நூ
    assert_eq!(
        get_cognate("\u{0BAA}\u{0BC8}"),
        Some("\u{0BAE}\u{0BC8}".to_string())
    ); // பை <-> மை

    // Negative / Idaiyinam (medium consonants have no nasal partners)
    assert_eq!(get_cognate("\u{0BAF}\u{0BCD}"), None); // ய்
    assert_eq!(get_cognate("\u{0BB0}\u{0BCD}"), None); // ர்

    // are_cognates checks
    assert!(are_cognates("\u{0BA4}\u{0BCD}", "\u{0BA8}\u{0BCD}"));
    assert!(are_cognates("\u{0BA8}\u{0BCD}", "\u{0BA4}\u{0BCD}"));
    assert!(!are_cognates("\u{0BA4}\u{0BCD}", "\u{0BAE}\u{0BCD}"));
    assert!(are_cognates("\u{0B90}", "\u{0B87}"));
    assert!(are_cognates("\u{0B95}\u{0BBE}", "\u{0B99}\u{0BBE}"));
    assert!(!are_cognates("\u{0B95}\u{0BBE}", "\u{0BAE}\u{0BBE}"));
}
