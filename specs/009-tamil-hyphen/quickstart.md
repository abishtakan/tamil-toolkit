# Quickstart: Validating `tamil-hyphen`

This guide explains how to validate the Tamil syllable hyphenation capabilities across Rust, multi-runtime bindings, and the test harness.

---

## 1. Prerequisites

- Rust 1.85+ (`cargo`)
- `just` task runner
- Node.js 22+ & `pnpm` (for WebAssembly testing)
- Python 3.11+ (for Python binding testing)

---

## 2. Running Rust Unit & Integration Tests

Run focused unit tests in `crates/tamil-hyphen`:

```bash
cargo test -p tamil-hyphen
```

Expected output:
- Akshara segmentation tests pass.
- Invariant tests (no *Mei* leading a line or segment) pass.
- Letter margin tests (`left_min=2`, `right_min=2`) pass.
- Idempotency tests pass (`hyphenate_text(hyphenate_text(s)) == hyphenate_text(s)`).
- Round-trip tests pass (`segments.join("") == original`).

---

## 3. Validating Planned Golden Vectors

Execute the golden vector suite across all runtimes by setting the review override:

```bash
# In PowerShell:
$env:TAMIL_GOLDEN_INCLUDE_PLANNED = "hyphen_syllable.jsonl"

# Run Rust golden tests:
cargo test -p tamil-toolkit --test golden_tests

# Run Python golden tests:
pytest bindings/python

# Run WebAssembly tests:
pnpm --dir bindings/js-wasm test
```

---

## 4. Quick API Demonstration

### Rust
```rust
use tamil_hyphen::{hyphenate_word, wrap_text, HyphenationConfig};

fn main() {
    let result = hyphenate_word("தமிழ்நாடு", None).unwrap();
    println!("Hyphenated: {}", result.hyphenated); // "தமிழ்\u{00AD}நாடு"
    println!("Segments: {:?}", result.segments);   // ["தமிழ்", "நாடு"]

    let wrapped = wrap_text("தமிழ்நாடு அரசு கலை மற்றும் அறிவியல் பல்கலைக்கழகம்", 16, None).unwrap();
    for line in wrapped.lines {
        println!("{}", line);
    }
}
```

### Python
```python
import tamil_toolkit as tamil

res = tamil.hyphenate_word("பல்கலைக்கழகம்")
print(res["segments"])  # ['பல்', 'கலைக்', 'கழகம்']
```

### JavaScript / TypeScript (Node or Browser WASM)
```javascript
import * as tamil from "tamil-toolkit";

const res = tamil.hyphenateWord("பல்கலைக்கழகம்");
console.log(res.segments); // [ 'பல்', 'கலைக்', 'கழகம்' ]
```
