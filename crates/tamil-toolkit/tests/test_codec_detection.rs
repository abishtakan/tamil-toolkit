use serde_json::json;
use tamil_toolkit::{codec, execute};

#[test]
fn test_dispatcher_detect_encoding_bytes() {
    let tscii_bytes = codec::unicode_to_tscii_bytes("தமிழ் வாழ்க வளர்க").expect("tscii encoded");
    let req = json!({
        "op": "detect_encoding",
        "input": {
            "bytes": tscii_bytes
        }
    });
    let res = execute(&req).expect("executed detect_encoding");
    assert_eq!(res["status"], "detected");
    assert_eq!(res["encoding"], "tscii-1.7-v1");
    assert!(res["confidence"].as_f64().unwrap() >= 0.85);
}

#[test]
fn test_dispatcher_detect_encoding_codes() {
    let lt_codes = codec::unicode_to_lt_tm_codes("தமிழ் வாழ்க வளர்க").expect("lt_tm encoded");
    let req = json!({
        "op": "detect_encoding",
        "input": {
            "codes": lt_codes
        }
    });
    let res = execute(&req).expect("executed detect_encoding");
    assert_eq!(res["status"], "detected");
    assert_eq!(res["encoding"], "lt-tm-cid-v1");
    assert!(res["confidence"].as_f64().unwrap() >= 0.85);
}

#[test]
fn test_dispatcher_detect_encoding_text() {
    // 1. Native UTF-8
    let req_utf8 = json!({
        "op": "detect_encoding",
        "input": {
            "text": "தமிழ் வாழ்க வளர்க"
        }
    });
    let res_utf8 = execute(&req_utf8).expect("executed detect_encoding utf8");
    assert_eq!(res_utf8["status"], "detected");
    assert_eq!(res_utf8["encoding"], "utf-8");
    assert_eq!(res_utf8["confidence"], 1.0);

    // 2. Bamini text
    let bamini_str = codec::unicode_to_bamini("தமிழ் வாழ்க வளர்க").expect("bamini encoded");
    let req_bamini = json!({
        "op": "detect_encoding",
        "input": {
            "text": bamini_str
        }
    });
    let res_bamini = execute(&req_bamini).expect("executed detect_encoding bamini");
    assert_eq!(res_bamini["status"], "detected");
    assert_eq!(res_bamini["encoding"], "bamini-v1");
    assert!(res_bamini["confidence"].as_f64().unwrap() >= 0.70);
}

#[test]
fn test_dispatcher_detect_and_decode() {
    // Bytes decode
    let tscii_bytes = codec::unicode_to_tscii_bytes("தமிழ் வாழ்க வளர்க").expect("tscii encoded");
    let req_bytes = json!({
        "op": "detect_and_decode",
        "input": {
            "bytes": tscii_bytes
        }
    });
    let res_bytes = execute(&req_bytes).expect("executed detect_and_decode bytes");
    assert_eq!(res_bytes, "தமிழ் வாழ்க வளர்க");

    // Text decode (Bamini)
    let bamini_str = codec::unicode_to_bamini("தமிழ் வாழ்க வளர்க").expect("bamini encoded");
    let req_text = json!({
        "op": "detect_and_decode",
        "input": {
            "text": bamini_str
        }
    });
    let res_text = execute(&req_text).expect("executed detect_and_decode text");
    assert_eq!(res_text, "தமிழ் வாழ்க வளர்க");

    // Uncertain error
    let req_uncertain = json!({
        "op": "detect_and_decode",
        "input": {
            "text": "Hello world"
        }
    });
    let err = execute(&req_uncertain).unwrap_err();
    assert!(err.contains("uncertain encoding"));
}
