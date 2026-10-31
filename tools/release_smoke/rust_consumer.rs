use serde_json::Value;
use std::{env, fs};

fn main() {
    let source = fs::read_to_string(env::args().nth(1).expect("golden JSONL path")).unwrap();
    let mut count = 0;
    for line in source.lines() {
        let case: Value = serde_json::from_str(line).unwrap();
        let actual = tamil_toolkit::execute(&case);
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
    println!("Extracted Rust distributions: {count} golden rows passed.");
}
