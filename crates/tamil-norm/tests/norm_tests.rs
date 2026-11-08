#![forbid(unsafe_code)]

use tamil_norm::{normalize_nfc, normalize_nfd};

#[test]
fn test_canonical_nfc_nfd_equivalence() {
    let precomposed = "\u{0B95}\u{0BCA}";
    let decomposed: String = [0x0B95, 0x0BC6, 0x0BBE]
        .into_iter()
        .filter_map(char::from_u32)
        .collect();

    assert_eq!(normalize_nfc(&decomposed), precomposed);
    assert_eq!(normalize_nfd(precomposed), decomposed);
    assert_eq!(normalize_nfc(precomposed), precomposed);
    assert_eq!(normalize_nfd(&decomposed), decomposed);
}

#[test]
fn test_joiner_preservation() {
    let zwj = char::from_u32(0x200D).unwrap();
    let zwnj = char::from_u32(0x200C).unwrap();
    let with_zwj = format!("தமிழ்{zwj}நாடு");
    let with_zwnj = format!("தமிழ்{zwnj}நாடு");

    assert_eq!(normalize_nfc(&with_zwj), with_zwj);
    assert_eq!(normalize_nfd(&with_zwj), with_zwj);
    assert_eq!(normalize_nfc(&with_zwnj), with_zwnj);
    assert_eq!(normalize_nfd(&with_zwnj), with_zwnj);
}

#[test]
fn test_mixed_scripts_passthrough() {
    let mixed = "Tamil 123 தமிழ்! 🎉";
    assert_eq!(normalize_nfc(mixed), mixed);
    assert_eq!(normalize_nfd(mixed), mixed);
}
