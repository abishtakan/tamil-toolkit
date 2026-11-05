use tamil_codec::{
    detect_encoding_cids, lt_tm_codes_to_unicode, unicode_to_lt_tm_codes, unicode_to_vanavil_codes,
    vanavil_codes_to_unicode, DetectionStatus, ErrorPolicy,
};

#[test]
fn test_detect_lt_tm_cids() {
    let lt_codes = unicode_to_lt_tm_codes("தமிழ் வாழ்க வளர்க").expect("encoded lt_tm");
    let res = detect_encoding_cids(&lt_codes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("lt-tm-cid-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = lt_tm_codes_to_unicode(&lt_codes, ErrorPolicy::Strict).expect("decoded lt_tm");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}

#[test]
fn test_detect_vanavil_cids() {
    let codes = unicode_to_vanavil_codes("தமிழ் வாழ்க வளர்க").expect("encoded vanavil");
    let res = detect_encoding_cids(&codes);
    assert_eq!(res.status, DetectionStatus::Detected);
    assert_eq!(res.encoding.as_deref(), Some("vanavil-avvaiyar-cid-v1"));
    assert!(res.confidence >= 0.85);

    let decoded = vanavil_codes_to_unicode(&codes, ErrorPolicy::Strict).expect("decoded vanavil");
    assert_eq!(decoded, "தமிழ் வாழ்க வளர்க");
}
