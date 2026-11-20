use serde_json::{json, Value};
use std::{collections::BTreeSet, env::VarError, fs, path::Path};

fn compiled_lexicon_profile() -> &'static str {
    let available = tamil_toolkit::lexicon_pack::available_packs();
    let has_core = cfg!(feature = "lexicon-core");
    let has_terminology = cfg!(feature = "lexicon-terminology");
    let has_names_taxa = cfg!(feature = "lexicon-names-taxa");
    let has_regional = cfg!(feature = "lexicon-regional");
    if has_terminology {
        panic!("unsupported lexicon-terminology feature enabled in compiled verification profile");
    }
    if has_core && has_names_taxa && has_regional {
        assert_eq!(
            available.len(),
            3,
            "full profile must embed exactly three packs"
        );
        let ids: Vec<&str> = available.iter().map(|pack| pack.id).collect();
        assert_eq!(ids, vec!["core", "names_taxa", "regional"]);
        "full"
    } else if has_core && !has_names_taxa && !has_regional {
        assert_eq!(
            available.len(),
            1,
            "core profile must embed exactly one pack"
        );
        assert_eq!(available[0].id, "core");
        "core"
    } else if !has_core && !has_names_taxa && !has_regional {
        assert!(available.is_empty(), "no approved data feature is enabled");
        "default"
    } else {
        panic!(
            "unsupported partial lexicon feature set: core={has_core} names_taxa={has_names_taxa} regional={has_regional}"
        );
    }
}

fn resolve_effective_lexicon_profile() -> &'static str {
    let compiled = compiled_lexicon_profile();
    match std::env::var("TAMIL_LEXICON_PROFILE") {
        Ok(raw) => {
            assert!(
                matches!(raw.as_str(), "default" | "core" | "full"),
                "Unsupported TAMIL_LEXICON_PROFILE={raw:?} (expected 'default', 'core', or 'full')"
            );
            assert_eq!(
                raw, compiled,
                "TAMIL_LEXICON_PROFILE={raw:?} does not match compiled Rust profile {compiled:?}"
            );
            compiled
        }
        Err(VarError::NotPresent) => compiled,
        Err(err) => panic!("Failed to read TAMIL_LEXICON_PROFILE: {err}"),
    }
}

#[test]
fn all_active_golden_vectors() {
    let profile = resolve_effective_lexicon_profile();
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/golden");
    let manifest: Value =
        serde_json::from_str(&fs::read_to_string(root.join("manifest.json")).unwrap()).unwrap();
    assert_eq!(manifest["version"], 1);
    let mut count = 0;
    let mut planned_review_count = 0;
    let mut core_profile_count = 0;
    let mut full_profile_count = 0;
    let mut has_declared_full = false;
    let mut excluded_profile_count = 0;
    let mut ids = BTreeSet::new();
    let mut files = BTreeSet::new();
    let mut dialects = BTreeSet::new();
    let include_planned = std::env::var("TAMIL_GOLDEN_INCLUDE_PLANNED")
        .unwrap_or_default()
        .split(',')
        .map(str::trim)
        .filter(|name| !name.is_empty())
        .map(str::to_owned)
        .collect::<BTreeSet<_>>();
    for suite in manifest["suites"].as_array().unwrap() {
        let filename = suite["file"].as_str().unwrap();
        assert!(
            files.insert(filename.to_owned()),
            "duplicate suite: {filename}"
        );
        let required_profile = match suite.get("required_profile") {
            None => None,
            Some(Value::String(name)) if matches!(name.as_str(), "default" | "core" | "full") => {
                Some(name.as_str())
            }
            Some(other) => panic!("invalid required_profile in {filename}: {other}"),
        };
        let content = fs::read_to_string(root.join(filename)).unwrap();
        let status = suite["status"].as_str().unwrap();
        assert!(
            ["active", "planned"].contains(&status),
            "unknown suite status"
        );
        if status == "active" && required_profile == Some("full") {
            has_declared_full = true;
        }
        if status == "planned" && include_planned.contains(filename) {
            if let Some(req) = required_profile {
                assert_eq!(
                    req, profile,
                    "planned suite {filename} requires profile '{req}', cannot run under '{profile}'"
                );
            }
        }
        let mut suite_count = 0;
        let mut excluded_suite_rows = 0;
        for (index, line) in content.lines().enumerate() {
            let case: Value = serde_json::from_str(line).unwrap();
            let id = case["id"].as_str().unwrap();
            assert!(ids.insert(id.to_owned()), "duplicate golden id: {id}");
            if status == "planned" && !include_planned.contains(filename) {
                continue;
            }
            if status == "active" && required_profile.is_some_and(|req| req != profile) {
                excluded_suite_rows += 1;
                continue;
            }
            dialects.insert(case["dialect"].as_str().unwrap().to_owned());
            let operation = case["op"].as_str().unwrap();
            assert!(suite["operations"]
                .as_array()
                .unwrap()
                .contains(&Value::from(operation)));
            let actual = tamil_toolkit::execute(&vector_request(&case));
            match (case.get("expected"), case.get("expected_error")) {
                (Some(expected), None) => {
                    let actual = actual
                        .unwrap_or_else(|error| panic!("{filename}:{} ({id}): {error}", index + 1));
                    assert_eq!(&actual, expected, "{filename}:{} ({id})", index + 1);
                }
                (None, Some(Value::String(expected_error))) => {
                    let error = actual.expect_err("expected an error, got a successful output");
                    assert_eq!(&error, expected_error, "{filename}:{} ({id})", index + 1);
                }
                _ => panic!(
                    "{filename}:{} ({id}): require exactly one valid outcome",
                    index + 1
                ),
            }
            if status == "active" {
                count += 1;
                if required_profile == Some("core") {
                    core_profile_count += 1;
                } else if required_profile == Some("full") {
                    full_profile_count += 1;
                }
            } else {
                planned_review_count += 1;
            }
            suite_count += 1;
        }
        if status == "active" {
            if let Some(req) = required_profile.filter(|req| *req != profile) {
                assert!(
                    excluded_suite_rows > 0,
                    "empty excluded active suite {filename}"
                );
                excluded_profile_count += excluded_suite_rows;
                eprintln!(
                    "PROFILE_EXCLUDED {filename}: requires profile '{req}' (active profile '{profile}'; {excluded_suite_rows} vectors excluded)"
                );
            } else {
                assert!(suite_count > 0, "empty active suite");
            }
        } else {
            eprintln!(
                "PLANNED {filename}: {} (executed {suite_count} review-only vectors)",
                suite["reason"]
            );
        }
    }
    let on_disk: BTreeSet<_> = fs::read_dir(&root)
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.extension().is_some_and(|ext| ext == "jsonl"))
        .map(|p| p.file_name().unwrap().to_str().unwrap().to_owned())
        .collect();
    assert_eq!(files, on_disk, "every JSONL suite must be registered");
    assert_eq!(
        dialects,
        BTreeSet::from(["COMMON".to_owned(), "TN".to_owned(), "SL".to_owned()])
    );
    assert!(count > 0, "no active golden vectors");
    if profile == "core" {
        assert!(
            core_profile_count > 0,
            "core profile must execute required_profile='core' active golden vectors"
        );
        assert_eq!(
            excluded_profile_count, 0,
            "core profile unexpectedly excluded {excluded_profile_count} active vectors"
        );
    } else if profile == "full" && has_declared_full {
        assert!(
            full_profile_count > 0,
            "full profile must execute required_profile='full' active golden vectors"
        );
    }
    eprintln!(
        "Rust passed {count} active golden vectors for profile '{profile}' (excluded {excluded_profile_count} active vectors requiring other profiles)"
    );
    if planned_review_count > 0 {
        eprintln!(
            "Rust executed {planned_review_count} explicitly selected planned vectors for pre-activation review; they are not counted as active parity"
        );
    }
}

fn pack_dir_rel(pack_id: &str) -> &'static str {
    match pack_id {
        "core" => "../../lexicon/dictionary",
        "names_taxa" => "../../lexicon/packs/names_taxa",
        "regional" => "../../lexicon/packs/regional",
        other => panic!("unsupported pack id for contract test: {other}"),
    }
}

fn read_pack_manifest_toml(pack_id: &str) -> toml::Value {
    let packs_toml_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join(pack_dir_rel(pack_id))
        .join("packs.toml");
    toml::from_str(&fs::read_to_string(packs_toml_path).unwrap()).unwrap()
}

fn first_canonical_written_form(pack_id: &str) -> String {
    let assertions_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join(pack_dir_rel(pack_id))
        .join("assertions.csv");
    let mut reader = csv::Reader::from_path(&assertions_path).unwrap();
    let headers = reader.headers().unwrap().clone();
    let subject_kind_idx = headers
        .iter()
        .position(|header| header == "subject_kind")
        .expect("assertions.csv missing subject_kind");
    let value_json_idx = headers
        .iter()
        .position(|header| header == "value_json")
        .expect("assertions.csv missing value_json");
    for record in reader.records() {
        let row = record.unwrap();
        if row.get(subject_kind_idx) == Some("form") {
            let value_raw = row.get(value_json_idx).unwrap();
            let parsed: Value = serde_json::from_str(value_raw).unwrap();
            if let Some(text) = parsed.as_str() {
                if !text.is_empty() {
                    return text.to_owned();
                }
            }
        }
    }
    panic!(
        "no canonical form assertion found in {}",
        assertions_path.display()
    );
}

fn absent_golden_input() -> String {
    let path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/golden/lexicon_lookup.jsonl");
    for line in fs::read_to_string(path).unwrap().lines() {
        let case: Value = serde_json::from_str(line).unwrap();
        if case["id"].as_str() == Some("lexicon_lookup_not_found_absent_007") {
            assert_eq!(case["expected"]["status"].as_str(), Some("not_found"));
            return case["input"].as_str().unwrap().to_owned();
        }
    }
    panic!("missing lexicon_lookup_not_found_absent_007 golden vector");
}

fn assert_pack_matches_manifest(pack: &Value, manifest: &toml::Value) {
    assert_eq!(pack["id"].as_str(), manifest["pack_id"].as_str());
    assert_eq!(
        pack["dataset_version"].as_str(),
        manifest["dataset_version"].as_str()
    );
    assert_eq!(
        pack["schema_version"].as_i64(),
        manifest["schema_version"].as_integer()
    );
    assert_eq!(
        pack["index_format_version"].as_i64(),
        manifest["index_format_version"].as_integer()
    );
    assert_eq!(
        pack["manifest_sha256"].as_str(),
        manifest["manifest_sha256"].as_str()
    );
    assert_eq!(pack["available"].as_bool(), Some(true));
}

#[test]
fn lexicon_profile_contract() {
    let profile = resolve_effective_lexicon_profile();
    let packs = tamil_toolkit::execute(&json!({"op": "lexicon_packs", "input": null}))
        .expect("lexicon_packs should succeed");
    let packs_array = packs
        .as_array()
        .expect("lexicon_packs must return an array");
    let nanri = "\u{0ba8}\u{0ba9}\u{0bcd}\u{0bb1}\u{0bbf}";
    let absent_input = absent_golden_input();
    match profile {
        "default" => {
            assert_eq!(tamil_toolkit::lexicon_pack::embedded_payload_bytes(), 0);
            assert!(
                packs_array.is_empty(),
                "default zero-payload profile must expose 0 lexicon packs, got {packs_array:?}"
            );
            assert_eq!(
                tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri})),
                Err("lexicon: pack unavailable 'core'".to_owned())
            );
            assert_eq!(
                tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": nanri, "packs": []})
                ),
                Err("lexicon: packs must be a nonempty string array".to_owned())
            );
            assert_eq!(
                tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": nanri, "packs": ["unknown"]})
                ),
                Err("lexicon: unknown pack 'unknown'".to_owned())
            );
        }
        "core" => {
            assert!(tamil_toolkit::lexicon_pack::embedded_payload_bytes() > 0);
            assert_eq!(packs_array.len(), 1, "core profile must expose 1 pack");
            let manifest = read_pack_manifest_toml("core");
            let core = &packs_array[0];
            assert_pack_matches_manifest(core, &manifest);
            if let Ok(expected_sha) = std::env::var("TAMIL_LEXICON_MANIFEST_SHA256") {
                assert_eq!(
                    core["manifest_sha256"].as_str(),
                    Some(expected_sha.as_str())
                );
            }
            if let Ok(expected_ver) = std::env::var("TAMIL_LEXICON_DATASET_VERSION") {
                assert_eq!(
                    core["dataset_version"].as_str(),
                    Some(expected_ver.as_str())
                );
            }
            let matched = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri}))
                .expect("core lookup should match");
            assert_eq!(matched["status"].as_str(), Some("matched"));
            assert_eq!(matched["entries"].as_array().map(Vec::len), Some(2));
            let missing =
                tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": absent_input}))
                    .expect("missing lookup should succeed");
            assert_eq!(missing["status"].as_str(), Some("not_found"));
            assert_eq!(missing["entries"].as_array().map(Vec::len), Some(0));
            assert_eq!(
                tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": nanri, "packs": ["regional"]})
                ),
                Err("lexicon: pack unavailable 'regional'".to_owned())
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
        "full" => {
            assert!(tamil_toolkit::lexicon_pack::embedded_payload_bytes() > 0);
            assert_eq!(packs_array.len(), 3, "full profile must expose 3 packs");
            let env_manifests: Option<Value> = std::env::var("TAMIL_LEXICON_PACK_MANIFESTS")
                .ok()
                .map(|raw| serde_json::from_str(&raw).expect("valid TAMIL_LEXICON_PACK_MANIFESTS"));
            for (index, pack_id) in ["core", "names_taxa", "regional"].iter().enumerate() {
                let manifest = read_pack_manifest_toml(pack_id);
                let pack = &packs_array[index];
                assert_pack_matches_manifest(pack, &manifest);
                if let Some(map) = env_manifests.as_ref() {
                    let expected = &map[*pack_id];
                    assert_eq!(
                        pack["dataset_version"].as_str(),
                        expected["dataset_version"].as_str()
                    );
                    assert_eq!(
                        pack["manifest_sha256"].as_str(),
                        expected["manifest_sha256"].as_str()
                    );
                }
            }
            let core = &packs_array[0];
            if let Ok(expected_sha) = std::env::var("TAMIL_LEXICON_MANIFEST_SHA256") {
                assert_eq!(
                    core["manifest_sha256"].as_str(),
                    Some(expected_sha.as_str())
                );
            }
            if let Ok(expected_ver) = std::env::var("TAMIL_LEXICON_DATASET_VERSION") {
                assert_eq!(
                    core["dataset_version"].as_str(),
                    Some(expected_ver.as_str())
                );
            }
            let matched = tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": nanri}))
                .expect("full lookup across all packs should match");
            assert_eq!(matched["status"].as_str(), Some("matched"));
            assert_eq!(matched["entries"].as_array().map(Vec::len), Some(2));
            for pack_id in ["names_taxa", "regional"] {
                let sample = first_canonical_written_form(pack_id);
                let pack_match = tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": sample, "packs": [pack_id]}),
                )
                .unwrap_or_else(|err| panic!("full {pack_id} lookup failed: {err}"));
                assert_eq!(pack_match["status"].as_str(), Some("matched"));
                assert!(
                    !pack_match["entries"].as_array().unwrap().is_empty(),
                    "expected non-empty entries for canonical {pack_id} form"
                );
            }
            let missing =
                tamil_toolkit::execute(&json!({"op": "lexicon_lookup", "input": absent_input}))
                    .expect("missing lookup should succeed under full profile");
            assert_eq!(missing["status"].as_str(), Some("not_found"));
            assert_eq!(missing["entries"].as_array().map(Vec::len), Some(0));
            assert_eq!(
                tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": nanri, "packs": ["terminology"]})
                ),
                Err("lexicon: pack unavailable 'terminology'".to_owned())
            );
            assert_eq!(
                tamil_toolkit::execute(
                    &json!({"op": "lexicon_lookup", "input": nanri, "packs": []})
                ),
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
        other => unreachable!("validated profile {other}"),
    }
}

mod feature_022_dispatcher_validation {
    use std::process::Command;

    #[test]
    fn operations_list_includes_all_implemented_ops() {
        let expected_present = [
            "are_cognates",
            "baseline_maathirai",
            "calendar_display_info",
            "classify_quantity",
            "compare_calendar_profiles",
            "format_tamil_date",
            "get_cognate",
            "get_olippasai",
            "thiruvalluvar_year_info",
        ];

        for op in expected_present {
            assert!(
                tamil_toolkit::OPERATIONS.contains(&op),
                "OPERATIONS is missing implemented operation '{op}'"
            );
        }

        // Verify no duplicate entries in OPERATIONS
        let unique: std::collections::BTreeSet<&str> =
            tamil_toolkit::OPERATIONS.iter().copied().collect();
        assert_eq!(
            unique.len(),
            tamil_toolkit::OPERATIONS.len(),
            "OPERATIONS contains duplicate entries"
        );
    }

    #[test]
    fn dispatcher_rejects_invalid_fold_profile_and_unknown_op() {
        let invalid_profile_req = serde_json::json!({
            "op": "fold_for_search",
            "input": {"text": "\u{0baa}\u{0bb4}\u{0bae}\u{0bcd}", "profile": "invalid"}
        });
        assert!(
            tamil_toolkit::execute(&invalid_profile_req).is_err(),
            "expected invalid folding profile error"
        );

        let unknown_op_req = serde_json::json!({"op": "nonexistent_op_xyz", "input": "test"});
        assert!(
            tamil_toolkit::execute(&unknown_op_req).is_err(),
            "expected unsupported operation error"
        );

        let missing_op_req = serde_json::json!({"input": "test"});
        assert!(
            tamil_toolkit::execute(&missing_op_req).is_err(),
            "expected missing op error"
        );
    }

    #[test]
    fn cli_norm_fold_rejects_invalid_profile() {
        let bin = env!("CARGO_BIN_EXE_tamil-toolkit");

        let after_text = Command::new(bin)
            .args(["norm", "fold", "test", "--profile", "invalid"])
            .output()
            .expect("run tamil-toolkit norm fold test --profile invalid");
        assert!(
            !after_text.status.success(),
            "expected non-zero exit for --profile invalid after text, got {:?}",
            after_text.status
        );

        let before_text = Command::new(bin)
            .args(["norm", "fold", "--profile", "invalid", "test"])
            .output()
            .expect("run tamil-toolkit norm fold --profile invalid test");
        assert!(
            !before_text.status.success(),
            "expected non-zero exit for --profile invalid before text, got {:?}",
            before_text.status
        );

        let valid = Command::new(bin)
            .args([
                "norm",
                "fold",
                "--profile",
                "grantha",
                "\u{0bb0}\u{0bbe}\u{0b9c}\u{0bbe}",
            ])
            .output()
            .expect("run tamil-toolkit norm fold --profile grantha");
        assert!(
            valid.status.success(),
            "expected zero exit for valid --profile grantha: stderr={}",
            String::from_utf8_lossy(&valid.stderr)
        );
        assert_eq!(
            String::from_utf8_lossy(&valid.stdout).trim(),
            "\u{0bb0}\u{0bbe}\u{0b9a}\u{0bbe}"
        );
    }
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
