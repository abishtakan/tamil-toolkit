use serde_json::Value;
use std::{collections::BTreeSet, fs, path::Path};

#[test]
fn all_active_golden_vectors() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/golden");
    let manifest: Value =
        serde_json::from_str(&fs::read_to_string(root.join("manifest.json")).unwrap()).unwrap();
    assert_eq!(manifest["version"], 1);
    let mut count = 0;
    let mut planned_review_count = 0;
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
        let content = fs::read_to_string(root.join(filename)).unwrap();
        let status = suite["status"].as_str().unwrap();
        assert!(
            ["active", "planned"].contains(&status),
            "unknown suite status"
        );
        let mut suite_count = 0;
        for (index, line) in content.lines().enumerate() {
            let case: Value = serde_json::from_str(line).unwrap();
            let id = case["id"].as_str().unwrap();
            assert!(ids.insert(id.to_owned()), "duplicate golden id: {id}");
            if status == "planned" && !include_planned.contains(filename) {
                continue;
            }
            dialects.insert(case["dialect"].as_str().unwrap().to_owned());
            let operation = case["op"].as_str().unwrap();
            assert!(suite["operations"]
                .as_array()
                .unwrap()
                .contains(&Value::from(operation)));
            let actual = tamil_toolkit::execute(&case);
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
            } else {
                planned_review_count += 1;
            }
            suite_count += 1;
        }
        if status == "active" {
            assert!(suite_count > 0, "empty active suite");
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
    eprintln!("Rust passed {count} active golden vectors");
    if planned_review_count > 0 {
        eprintln!(
            "Rust executed {planned_review_count} explicitly selected planned vectors for pre-activation review; they are not counted as active parity"
        );
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
