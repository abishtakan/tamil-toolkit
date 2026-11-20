use serde_json::{json, Value};
use std::{env, fs};

fn assert_full_or_core_errors(nanri: &str, absent: &str, unavailable_pack: &str) {
    let missing = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": absent}))
        .expect("absent lookup should succeed");
    assert_eq!(missing["status"].as_str(), Some("not_found"));
    assert_eq!(missing["entries"].as_array().map(Vec::len), Some(0));
    assert_eq!(
        tamil_toolkit::execute(
            &json!({"op": "lexicon_lookup", "input": nanri, "packs": [unavailable_pack]})
        ),
        Err(format!("lexicon: pack unavailable '{unavailable_pack}'"))
    );
    assert_eq!(
        tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri, "packs": []})),
        Err("lexicon: packs must be a nonempty string array".to_owned())
    );
    assert_eq!(
        tamil_toolkit::execute(
            &json!({"op": "lexicon_lookup", "input": nanri, "packs": ["unknown"]})
        ),
        Err("lexicon: unknown pack 'unknown'".to_owned())
    );
    assert_eq!(
        tamil_toolkit::execute(
            &json!({"op": "lexicon_lookup", "input": nanri, "region": "LK-JAFFNA"})
        ),
        Err("lexicon: unknown region 'LK-JAFFNA'".to_owned())
    );
    assert_eq!(
        tamil_toolkit::execute(
            &json!({"op": "lexicon_lookup", "input": "\u{0b85}\u{0bb1}\u{0bbf}\u{0b95}\u{0bcd}\u{0b95}\u{0bc8}", "register": "written"})
        ),
        Err("lexicon: unknown register 'written'".to_owned())
    );
}

fn verify_lexicon_profile() {
    let profile = env::var("TAMIL_LEXICON_PROFILE").unwrap_or_else(|_| "default".to_owned());
    let packs = tamil_toolkit::execute(&json!({"op": "lexicon_packs", "input": null}))
        .expect("lexicon_packs should succeed");
    let packs_array = packs
        .as_array()
        .expect("lexicon_packs must return an array");
    let nanri = "\u{0ba8}\u{0ba9}\u{0bcd}\u{0bb1}\u{0bbf}";
    let absent = "\u{0b87}\u{0bb2}\u{0bcd}\u{0bb2}\u{0bbe}\u{0ba4}\u{0b9a}\u{0bca}\u{0bb2}\u{0bcd}";
    match profile.as_str() {
        "default" => {
            assert!(
                packs_array.is_empty(),
                "default zero-payload profile must expose 0 lexicon packs, got {packs_array:?}"
            );
            let err = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri}))
                .expect_err("default zero-payload profile must reject core lookup");
            assert_eq!(err, "lexicon: pack unavailable 'core'");
        }
        "core" => {
            assert_eq!(
                packs_array.len(),
                1,
                "core profile must expose exactly 1 pack, got {packs_array:?}"
            );
            let core = &packs_array[0];
            assert_eq!(core["id"].as_str(), Some("core"));
            assert_eq!(core["available"].as_bool(), Some(true));
            assert_eq!(core["schema_version"].as_u64(), Some(1));
            if let Ok(expected_sha) = env::var("TAMIL_LEXICON_MANIFEST_SHA256") {
                assert_eq!(
                    core["manifest_sha256"].as_str(),
                    Some(expected_sha.as_str()),
                    "core pack manifest_sha256 mismatch"
                );
            }
            if let Ok(expected_ver) = env::var("TAMIL_LEXICON_DATASET_VERSION") {
                assert_eq!(
                    core["dataset_version"].as_str(),
                    Some(expected_ver.as_str()),
                    "core pack dataset_version mismatch"
                );
            }
            let matched = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri}))
                .expect("core lookup should match");
            assert_eq!(matched["status"].as_str(), Some("matched"));
            assert_full_or_core_errors(nanri, absent, "regional");
        }
        "full" => {
            assert_eq!(
                packs_array.len(),
                3,
                "full profile must expose exactly 3 packs, got {packs_array:?}"
            );
            let pack_manifests: Option<Value> = env::var("TAMIL_LEXICON_PACK_MANIFESTS")
                .ok()
                .map(|raw| serde_json::from_str(&raw).expect("valid TAMIL_LEXICON_PACK_MANIFESTS"));
            for (index, pack_id) in ["core", "names_taxa", "regional"].iter().enumerate() {
                let pack = &packs_array[index];
                assert_eq!(pack["id"].as_str(), Some(*pack_id));
                assert_eq!(pack["available"].as_bool(), Some(true));
                assert_eq!(pack["schema_version"].as_u64(), Some(1));
                if let Some(map) = pack_manifests.as_ref() {
                    let expected = &map[*pack_id];
                    assert_eq!(
                        pack["manifest_sha256"].as_str(),
                        expected["manifest_sha256"].as_str()
                    );
                    assert_eq!(
                        pack["dataset_version"].as_str(),
                        expected["dataset_version"].as_str()
                    );
                }
            }
            let core = &packs_array[0];
            if let Ok(expected_sha) = env::var("TAMIL_LEXICON_MANIFEST_SHA256") {
                assert_eq!(
                    core["manifest_sha256"].as_str(),
                    Some(expected_sha.as_str()),
                    "core pack manifest_sha256 mismatch"
                );
            }
            if let Ok(expected_ver) = env::var("TAMIL_LEXICON_DATASET_VERSION") {
                assert_eq!(
                    core["dataset_version"].as_str(),
                    Some(expected_ver.as_str()),
                    "core pack dataset_version mismatch"
                );
            }
            let matched = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri}))
                .expect("full lookup across all packs should match");
            assert_eq!(matched["status"].as_str(), Some("matched"));
            assert_full_or_core_errors(nanri, absent, "terminology");
        }
        other => panic!("Unsupported TAMIL_LEXICON_PROFILE={other:?}"),
    }
}

fn main() {
    let source = fs::read_to_string(env::args().nth(1).expect("golden JSONL path")).unwrap();
    let mut count = 0;
    for line in source.lines() {
        let case: Value = serde_json::from_str(line).unwrap();
        let actual = tamil_toolkit::execute(&vector_request(&case));
        if let Some(expected) = case.get("expected") {
            assert_eq!(&actual.unwrap(), expected, "{}", case["id"]);
        } else {
            assert_eq!(
                actual.unwrap_err(),
                case["expected_error"].as_str().unwrap()
            );
        }
        count += 1;
    }
    assert!(count > 0);
    assert_eq!(tamil_toolkit::numerals::PROFILE, "numerals-v1");
    verify_lexicon_profile();
    println!("Extracted Rust distributions: {count} golden rows passed.");
}

fn vector_request(case: &Value) -> Value {
    if !matches!(
        case["op"].as_str(),
        Some("lexicon_lookup" | "lexicon_packs")
    ) {
        return case.clone();
    }
    let mut request = case.as_object().expect("golden object").clone();
    for key in [
        "id",
        "expected",
        "expected_error",
        "dialect",
        "tags",
        "source",
        "unicode_exceptions",
    ] {
        request.remove(key);
    }
    Value::Object(request)
}
