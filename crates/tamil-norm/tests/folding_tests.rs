#![forbid(unsafe_code)]

use tamil_norm::{fold_for_search, FoldingProfile};

#[test]
fn test_mayangoli_lateral_folding() {
    // பழம் (fruit) vs பலம் (strength) vs பளம் -> பலம்
    assert_eq!(fold_for_search("பழம்", FoldingProfile::Mayangoli), "பலம்");
    assert_eq!(fold_for_search("பளம்", FoldingProfile::Mayangoli), "பலம்");
    assert_eq!(fold_for_search("பலம்", FoldingProfile::Mayangoli), "பலம்");

    // வெள்ளம் (flood) vs வெல்லம் (jaggery) -> வெல்லம்
    assert_eq!(fold_for_search("வெள்ளம்", FoldingProfile::Mayangoli), "வெல்லம்");
    assert_eq!(fold_for_search("வெல்லம்", FoldingProfile::Mayangoli), "வெல்லம்");

    // கிளி (parrot) vs கிலி (fear) -> கிலி
    assert_eq!(fold_for_search("கிளி", FoldingProfile::Mayangoli), "கிலி");
}

#[test]
fn test_mayangoli_nasal_folding() {
    // மணம் (fragrance) vs மனம் (mind) -> மனம்
    assert_eq!(fold_for_search("மணம்", FoldingProfile::Mayangoli), "மனம்");
    assert_eq!(fold_for_search("மனம்", FoldingProfile::Mayangoli), "மனம்");

    // கண் (eye) -> கன்
    assert_eq!(fold_for_search("கண்", FoldingProfile::Mayangoli), "கன்");

    // Dental ந is preserved by default
    assert_eq!(
        fold_for_search("நன்றி", FoldingProfile::Mayangoli),
        "நன்ரி" // dental ந kept, hard ற -> medial ர
    );
}

#[test]
fn test_mayangoli_rhotic_folding() {
    // கறி (curry) vs கரி (charcoal) -> கரி
    assert_eq!(fold_for_search("கறி", FoldingProfile::Mayangoli), "கரி");
    assert_eq!(fold_for_search("கரி", FoldingProfile::Mayangoli), "கரி");

    // பறை -> பரை
    assert_eq!(fold_for_search("பறை", FoldingProfile::Mayangoli), "பரை");
}

#[test]
fn test_grantha_folding() {
    // ஸ, ஷ -> ச
    assert_eq!(fold_for_search("சந்தோஷம்", FoldingProfile::Grantha), "சந்தோசம்");
    assert_eq!(fold_for_search("கஷ்டம்", FoldingProfile::Grantha), "கச்டம்");

    // ஜ -> ச
    assert_eq!(fold_for_search("ராஜா", FoldingProfile::Grantha), "ராசா");

    // ஹ -> க
    assert_eq!(fold_for_search("மஹால்", FoldingProfile::Grantha), "மகால்");

    // க்ஷ -> ச (க்ஷ் -> ச்)
    assert_eq!(fold_for_search("லக்ஷ்மி", FoldingProfile::Grantha), "லச்மி");
    assert_eq!(fold_for_search("மோக்ஷம்", FoldingProfile::Grantha), "மோசம்");

    // ஸ்ரீ -> சீ
    assert_eq!(fold_for_search("ஸ்ரீலங்கா", FoldingProfile::Grantha), "சீலங்கா");
}

#[test]
fn test_comprehensive_folding() {
    let input = "  ஸ்ரீ  லக்ஷ்மி   Pazham!  ";
    let folded = fold_for_search(input, FoldingProfile::Comprehensive);
    assert_eq!(folded, "சீ லச்மி pazham!");
}
