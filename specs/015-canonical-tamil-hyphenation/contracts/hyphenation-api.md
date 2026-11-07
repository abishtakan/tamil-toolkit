# Interface Contracts: Canonical Prosodic & Syllabic Tamil Hyphenation (`015-canonical-tamil-hyphenation`)

## 1. Rust Core Contract (`crates/tamil-hyphen`)

```rust
/// Default configuration: delimiter = "\u{00AD}", left_min = 3, right_min = 3
impl Default for HyphenationConfig {
    fn default() -> Self {
        Self {
            delimiter: "\u{00AD}".to_string(),
            left_min: 3,
            right_min: 3,
        }
    }
}

/// Default dictionary header: left_hyphen_min = 3, right_hyphen_min = 3
impl Default for DicHeader {
    fn default() -> Self {
        Self {
            encoding: "UTF-8".to_string(),
            left_hyphen_min: 3,
            right_hyphen_min: 3,
            license_notice: "MIT / LGPL / GPL Tri-license".to_string(),
        }
    }
}

/// Computes valid break points using the 5-step Tamil Asai + minimum segment algorithm.
pub fn hyphenation_points(
    word: &str,
    config: Option<&HyphenationConfig>,
) -> Result<Vec<HyphenationPoint>, String>;

/// Hyphenates a single Tamil word (stripping any pre-existing U+00AD / U+001F / U+200B first).
pub fn hyphenate_word(
    word: &str,
    config: Option<&HyphenationConfig>,
) -> Result<HyphenationResult, String>;
```

---

## 2. Python & WebAssembly FFI Contracts (`bindings/python`, `bindings/js-wasm`)

- **Python (`tamil_toolkit.hyphenate_word` / `tamil_toolkit.hyphenation_points`)**:
  - Default `left_min: int = 3`, `right_min: int = 3`, `delimiter: str = "\u00ad"`.
  - Returns identical `HyphenationResult` / `list[HyphenationPoint]` as Rust.
- **WebAssembly (`@tamil-toolkit/wasm` / `bindings/js-wasm`)**:
  - `hyphenate_word(word, delimiter = "\u00AD", left_min = 3, right_min = 3)`
  - `hyphenation_points(word, left_min = 3, right_min = 3)`

---

## 3. Office Word Add-in & Playground Contract (`integrations/office-word-addin/engine.js`, `playground/src/lib/engine.ts`)

```ts
export function getRawSyllables(word: string): string[];
export function getTamilSyllables(
  word: string,
  leftMin?: number,  // default: 3
  rightMin?: number, // default: 3
): string[];
export function hyphenateWord(
  word: string,
  leftMin?: number,        // default: 3
  rightMin?: number,       // default: 3
  delimiter?: string,      // default: "\u00AD"
  minWordLetters?: number, // default: Math.max(leftMin + rightMin, 2)
): string;
export function hyphenateOoxml(
  ooxml: string,
  leftMin?: number,        // default: 3
  rightMin?: number,       // default: 3
): { ooxml: string; stats: { wordsHyphenated: number; softHyphensInserted: number } };
```
