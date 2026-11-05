use tamil_codec::{
    detect_and_decode, detect_encoding, unicode_to_anjal_bytes, unicode_to_bamini,
    unicode_to_tab_bytes, unicode_to_tam_bytes, unicode_to_tscii_bytes, DetectionStatus,
};

#[test]
fn test_detect_native_utf8() {
    let input = "தமிழ் வாழ்க வளர்க தமிழ் மொழி".as_bytes();
    let res = detect_encoding(input);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("utf-8"));
    assert_eq!(res.confidence, 1.0);
    assert!(res.reason.is_none());

    let decoded = detect_and_decode(input).expect("decoded utf8");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க தமிழ் மொழி");
}

#[test]
fn test_detect_bamini() {
    let bamini_str = unicode_to_bamini("தமிழ் வாழ்க வளர்க").expect("bamini encoded");
    let res = detect_encoding(bamini_str.as_bytes());
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("bamini-v1"));
    assert!(res.confidence >= 0.70);

    let decoded = detect_and_decode(bamini_str.as_bytes()).expect("decoded bamini");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}

#[test]
fn test_detect_tscii() {
    let tscii_bytes = unicode_to_tscii_bytes("தமிழ் வாழ்க வளர்க").expect("tscii encoded");
    let res = detect_encoding(&tscii_bytes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("tscii-1.7-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = detect_and_decode(&tscii_bytes).expect("decoded tscii");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}

#[test]
fn test_detect_tab() {
    let tab_bytes = unicode_to_tab_bytes("தமிழ் வாழ்க வளர்க").expect("tab encoded");
    let res = detect_encoding(&tab_bytes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("tab-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = detect_and_decode(&tab_bytes).expect("decoded tab");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}

#[test]
fn test_detect_tam() {
    let tam_bytes = unicode_to_tam_bytes("தமிழ் வாழ்க வளர்க").expect("tam encoded");
    let res = detect_encoding(&tam_bytes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("tam-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = detect_and_decode(&tam_bytes).expect("decoded tam");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}

#[test]
fn test_detect_anjal() {
    let anjal_bytes = unicode_to_anjal_bytes("தமிழ் வாழ்க வளர்க").expect("anjal encoded");
    let res = detect_encoding(&anjal_bytes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("anjal-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = detect_and_decode(&anjal_bytes).expect("decoded anjal");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}
