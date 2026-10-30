use serde_json::Value;
use std::{collections::BTreeSet, fs, path::Path};

#[test]
fn all_active_golden_vectors() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../tests/golden");
    let manifest: Value =
        serde_json::from_str(&fs::read_to_string(root.join("manifest.json")).unwrap()).unwrap();
    assert_eq!(manifest["version"], 1);
    let mut count = 0;
    let mut ids = BTreeSet::new();
    let mut files = BTreeSet::new();
    let mut dialects = BTreeSet::new();
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
            if status == "planned" {
                continue;
            }
            dialects.insert(case["dialect"].as_str().unwrap().to_owned());
            let operation = case["op"].as_str().unwrap();
            assert!(suite["operations"]
                .as_array()
                .unwrap()
                .contains(&Value::from(operation)));
            let actual = tamil_toolkit::execute(&case)
                .unwrap_or_else(|error| panic!("{filename}:{} ({id}): {error}", index + 1));
            assert_eq!(actual, case["expected"], "{filename}:{} ({id})", index + 1);
            count += 1;
            suite_count += 1;
        }
        if status == "active" {
            assert!(suite_count > 0, "empty active suite");
        } else {
            eprintln!("PLANNED {filename}: {}", suite["reason"]);
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
}
