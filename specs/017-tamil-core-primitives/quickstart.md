# Quickstart & Verification Guide: Tamil Core Phonological Primitives (`017`)

**Feature**: [spec.md](spec.md)  
**Contract**: [contracts/core-primitives-contract.md](contracts/core-primitives-contract.md)

---

## 1. Prerequisites

- Rust toolchain (MSRV 1.80+) installed.
- `uv` Python package manager installed.
- Working directory set to repository root: `C:\Users\abish\Documents\dev\tamil-toolkit`.

---

## 2. Fast Verification Commands

### 2.1 Verify Rust Unit Tests
Run the focused unit test suite inside `tamil-core`:
```powershell
cargo test -p tamil-core --lib phonology
cargo test -p tamil-core --lib olippasai
```
**Expected Outcome**: 100% of quantity tests, cognate tests, and syllable nucleus tests pass in < 0.2s.

### 2.2 Verify Golden Parity Vectors
Run the new active golden suite `tests/golden/core_phonology.jsonl`:
```powershell
uv run --locked pytest tests/harness/test_golden_parity.py -k core_phonology
```
**Expected Outcome**: All escaped golden vectors pass identically across Rust, Python, and WASM bindings.

### 2.3 Verify Zero-Allocation & Strict Invariants
Run the standard repository agent gate:
```powershell
just agent-post-edit
```
**Expected Outcome**: Unicode compliance passes (`check-unicode`), formatting is clean, and release manifests are synchronized.

---

## 3. End-to-End Verification Scenarios

### Scenario 1: Letter Quantity & Mora Classification
```rust
use tamil_core::{classify_quantity, baseline_maathirai, is_kuril, is_nedil, is_mei, is_aytham, LetterQuantity};

// Short vowel / uyirmei
assert_eq!(classify_quantity("அ"), LetterQuantity::Kuril);
assert_eq!(baseline_maathirai("க").value(), 1.0);
assert!(is_kuril("கி"));

// Long vowel / uyirmei
assert_eq!(classify_quantity("ஆ"), LetterQuantity::Nedil);
assert_eq!(baseline_maathirai("கா").value(), 2.0);
assert!(is_nedil("கை"));

// Pure consonant / Otru
assert_eq!(classify_quantity("க்"), LetterQuantity::Mei);
assert_eq!(baseline_maathirai("த்").value(), 0.5);
assert!(is_mei("ம்"));

// Aytham
assert_eq!(classify_quantity("ஃ"), LetterQuantity::Aytham);
assert_eq!(baseline_maathirai("ஃ").value(), 0.5);
assert!(is_aytham("ஃ"));

// Grantha atomic sequences
assert_eq!(classify_quantity("க்ஷ"), LetterQuantity::Kuril);
assert_eq!(classify_quantity("ஸ்ரீ"), LetterQuantity::Nedil);
```

### Scenario 2: Homorganic Cognate Pairs (*Ina Ezhuthu*)
```rust
use tamil_core::{get_cognate, are_cognates};

// Consonants
assert_eq!(get_cognate("க்"), Some("ங்".to_string()));
assert_eq!(get_cognate("ங்"), Some("க்".to_string()));
assert!(are_cognates("த்", "ந்"));
assert!(!are_cognates("த்", "ம்"));

// Composite Uyirmei letters
assert_eq!(get_cognate("கா"), Some("ஙா".to_string()));
assert_eq!(get_cognate("கி"), Some("ஙி".to_string()));
assert!(are_cognates("தா", "நா"));

// Vowels
assert_eq!(get_cognate("அ"), Some("ஆ".to_string()));
assert_eq!(get_cognate("ஐ"), Some("இ".to_string()));
assert_eq!(get_cognate("ஔ"), Some("உ".to_string()));
assert!(are_cognates("ஐ", "இ"));
```

### Scenario 3: Syllable Nucleus Segmentation (*Olippasai*)
```rust
use tamil_core::get_olippasai;

// Standard word
let syllables: Vec<_> = get_olippasai("தமிழ்").map(|s| s.text).collect();
assert_eq!(syllables, vec!["த", "மிழ்"]);

// Word with internal codas
let syllables: Vec<_> = get_olippasai("கற்பனை").map(|s| s.text).collect();
assert_eq!(syllables, vec!["கற்", "ப", "னை"]);

// Loanword with initial consonant cluster
let syllables: Vec<_> = get_olippasai("ஸ்டார்").map(|s| s.text).collect();
assert_eq!(syllables, vec!["ஸ்டார்"]);
```
