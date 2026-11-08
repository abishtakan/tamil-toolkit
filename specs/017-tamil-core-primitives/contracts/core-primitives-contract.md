# Contract: Tamil Core Phonological & Nucleus Primitives (`017`)

**Feature**: [spec.md](../spec.md)  
**Status**: Normative Contract

---

## 1. Rust Public API (`crates/tamil-core`)

The `crates/tamil-core` crate exposes the following public functions and data types:

```rust
// In crates/tamil-core/src/lib.rs

pub use crate::phonology::{
    LetterQuantity,
    Maathirai,
    classify_quantity,
    baseline_maathirai,
    is_kuril,
    is_nedil,
    is_mei,
    is_otru,
    is_aytham,
    get_cognate,
    are_cognates,
};

pub use crate::olippasai::{
    Olippasai,
    OlippasaiIter,
    get_olippasai,
};
```

### 1.1 Function Signatures & Behaviors

#### Quantity & Mora Predicates
```rust
/// Classifies a tailored Tamil letter or grapheme cluster into its phonological quantity.
/// Respects atomic Grantha sequences (க்ஷ is Kuril, ஸ்ரீ is Nedil).
pub fn classify_quantity(letter: &str) -> LetterQuantity;

/// Returns the nominal baseline duration (Maathirai) for a given letter.
/// 1.0 for Kuril, 2.0 for Nedil, 0.5 for Mei/Aytham, 0.0 for Other.
pub fn baseline_maathirai(letter: &str) -> Maathirai;

/// Returns true if the letter is a short vowel or consonant-vowel composite.
pub fn is_kuril(letter: &str) -> bool;

/// Returns true if the letter is a long vowel, diphthong, or long consonant-vowel composite.
pub fn is_nedil(letter: &str) -> bool;

/// Returns true if the letter is a pure consonant terminating in pulli virama (U+0BCD).
pub fn is_mei(letter: &str) -> bool;

/// Semantic alias for `is_mei(letter)`.
#[inline]
pub fn is_otru(letter: &str) -> bool;

/// Returns true if the letter is the classical Aytham character (U+0B83).
pub fn is_aytham(letter: &str) -> bool;
```

#### Cognate Functions (*Ina Ezhuthu*)
```rust
/// Returns the canonical cognate letter for a given consonant, vowel, or Uyirmei composite.
/// If an Uyirmei letter is supplied (e.g., "கா"), the base consonant is mapped and the vowel diacritic preserved ("ஙா").
/// Returns None if the character has no cognate partner (e.g. Idaiyinam consonants or non-Tamil).
pub fn get_cognate(letter: &str) -> Option<String>;

/// Returns true if letter1 and letter2 form a recognized classical Ina Ezhuthu pair.
pub fn are_cognates(letter1: &str, letter2: &str) -> bool;
```

#### Syllable Nucleus Segmentation (*Olippasai*)
```rust
/// Returns a zero-allocation iterator over natural phonetic syllables (Olippasai) in `text`.
pub fn get_olippasai<'a>(text: &'a str) -> OlippasaiIter<'a>;
```

---

## 2. Dispatcher JSON Contract (`tamil-toolkit`)

The unified dispatcher in `tamil-toolkit` exposes these capabilities under the `core` domain:

### 2.1 Action: `core.classify_letter`
**Request Payload**:
```json
{
  "domain": "core",
  "action": "classify_letter",
  "params": {
    "letter": "க"
  }
}
```

**Response Payload**:
```json
{
  "status": "ok",
  "data": {
    "letter": "க",
    "quantity": "kuril",
    "maathirai": 1.0,
    "is_kuril": true,
    "is_nedil": false,
    "is_mei": false,
    "is_aytham": false
  }
}
```

### 2.2 Action: `core.get_cognate`
**Request Payload**:
```json
{
  "domain": "core",
  "action": "get_cognate",
  "params": {
    "letter": "கா"
  }
}
```

**Response Payload**:
```json
{
  "status": "ok",
  "data": {
    "source": "கா",
    "cognate": "ஙா",
    "has_cognate": true
  }
}
```

### 2.3 Action: `core.segment_olippasai`
**Request Payload**:
```json
{
  "domain": "core",
  "action": "segment_olippasai",
  "params": {
    "text": "தமிழ்"
  }
}
```

**Response Payload**:
```json
{
  "status": "ok",
  "data": {
    "syllables": [
      {
        "text": "த",
        "start_byte": 0,
        "end_byte": 3,
        "start_letter_idx": 0,
        "end_letter_idx": 1,
        "has_coda": false,
        "coda_count": 0
      },
      {
        "text": "மிழ்",
        "start_byte": 3,
        "end_byte": 12,
        "start_letter_idx": 1,
        "end_letter_idx": 3,
        "has_coda": true,
        "coda_count": 1
      }
    ]
  }
}
```

---

## 3. Python, WASM & Dart API Alignment

### Python (`bindings/python`)
```python
from tamil_toolkit import core

assert core.is_kuril("க") is True
assert core.is_nedil("கா") is True
assert core.baseline_maathirai("ஆ") == 2.0
assert core.get_cognate("கா") == "ஙா"
assert core.are_cognates("த்", "ந்") is True

syllables = core.get_olippasai("தமிழ்")
assert len(syllables) == 2
assert syllables[0].text == "த"
assert syllables[1].text == "மிழ்"
```

### TypeScript / WASM (`bindings/js-wasm`)
```typescript
import { isKuril, isNedil, baselineMaathirai, getCognate, areCognates, getOlippasai } from "tamil-toolkit";

console.assert(isKuril("க") === true);
console.assert(baselineMaathirai("ஆ") === 2.0);
console.assert(getCognate("கா") === "ஙா");
console.assert(areCognates("த்", "ந்") === true);

const syllables = getOlippasai("தமிழ்");
console.assert(syllables.length === 2);
```
