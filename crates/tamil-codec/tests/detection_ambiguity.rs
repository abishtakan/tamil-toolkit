use tamil_codec::{detect_and_decode, detect_encoding, detect_encoding_cids, DetectionStatus};

#[test]
fn test_empty_buffer_returns_uncertain() {
    let res = detect_encoding(b"");
    assert_eq!(res.status, DetectionStatus::Uncertain);
    assert_eq!(res.encoding, None);
    assert_eq!(res.reason.as_deref(), Some("empty input"));

    let err = detect_and_decode(b"").unwrap_err();
    assert!(err.contains("empty input"));
}

#[test]
fn test_short_buffer_returns_uncertain() {
    let res = detect_encoding(b"abc");
    assert_eq!(res.status, DetectionStatus::Uncertain);
    assert_eq!(res.encoding, None);
    assert_eq!(res.reason.as_deref(), Some("insufficient input length"));

    let err = detect_and_decode(b"abc").unwrap_err();
    assert!(err.contains("insufficient input length"));
}

#[test]
fn test_plain_english_returns_uncertain() {
    let english = b"Hello world! This is a standard English paragraph that does not contain Tamil.";
    let res = detect_encoding(english);
    assert_eq!(res.status, DetectionStatus::Uncertain);
    assert_eq!(res.encoding, None);
    assert!(
        res.reason.as_deref() == Some("no legacy tamil patterns detected")
            || res.reason.as_deref() == Some("low confidence")
    );

    let err = detect_and_decode(english).unwrap_err();
    assert!(err.contains("uncertain"));
}

#[test]
fn test_empty_and_short_cids_return_uncertain() {
    let empty_res = detect_encoding_cids(&[]);
    assert_eq!(empty_res.status, DetectionStatus::Uncertain);
    assert_eq!(empty_res.encoding, None);
    assert_eq!(empty_res.reason.as_deref(), Some("empty input"));

    let short_res = detect_encoding_cids(&[0x0041, 0x0042]);
    assert_eq!(short_res.status, DetectionStatus::Uncertain);
    assert_eq!(short_res.encoding, None);
    assert_eq!(
        short_res.reason.as_deref(),
        Some("insufficient input length")
    );
}
