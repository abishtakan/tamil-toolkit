# Data Model: tamil-hyphen Release Policy, Manifest & WASM Consolidation

## 1. Hyphenation Types (Crate: `tamil-hyphen`)

### `HyphenationConfig`
```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationConfig {
    /// Delimiter inserted at hyphenation points (default: U+00AD soft hyphen)
    pub delimiter: String,
    /// Minimum letters required on the preceding line segment (default: 3)
    pub left_min: usize,
    /// Minimum letters required on the following line segment (default: 3)
    pub right_min: usize,
}
```

### `HyphenationPoint`
```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationPoint {
    /// Byte index in the original string where the break is inserted
    pub byte_offset: usize,
    /// Unicode scalar count offset from start of string
    pub scalar_offset: usize,
    /// Tailored Tamil letter index from start of string
    pub letter_index: usize,
}
```

### `HyphenationResult`
```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HyphenationResult {
    /// Original input word before hyphenation
    pub original: String,
    /// Hyphenated word with delimiter inserted at valid breakpoints
    pub hyphenated: String,
    /// Ordered slice of hyphenated segments
    pub segments: Vec<String>,
    /// Breakpoint details with byte and scalar offsets
    pub points: Vec<HyphenationPoint>,
}
```

### `WrapResult`
```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WrapResult {
    /// Ordered list of wrapped lines
    pub lines: Vec<String>,
    /// Complete text reassembled with newlines
    pub wrapped: String,
}
```

## 2. CLI Command Models (`crates/tamil-toolkit/src/bin/tamil-toolkit.rs`)

### Module Hierarchy
- `core`:
  - `letters <text>` -> JSON array or whitespace-separated list of tailored graphemes
  - `inspect <text>` -> Full JSON object of `Inspection`
  - `split-uyirmei <letter>` -> JSON `{"mei": "...", "uyir": "..."}`
  - `compose-uyirmei <mei> <uyir>` -> Composed string
- `norm`:
  - `nfc <text>` -> NFC string
  - `nfd <text>` -> NFD string
  - `repair <text>` -> Repaired text + diagnostic counts
  - `fold <text> [--profile <name>]` -> Folded search key
- `codec`:
  - `convert <text> --from <enc> --to <enc>` -> Converted string
  - `detect <text>` -> Detected encoding with confidence score
- `collate`:
  - `compare <a> <b>` -> Comparison integer (-1, 0, 1)
  - `key <text> [--profile <name>]` -> Hexadecimal collation key
  - `sort <file>` -> Sorted lines
- `numerals`:
  - `to-words <number>` -> Tamil numeral words
  - `to-numeral <number>` -> Tamil numeral glyphs
  - `parse <words>` -> Decoded integer
- `calendar`:
  - `info [--date YYYY-MM-DD]` -> Tamil date metadata JSON/text
- `hyphen`:
  - `word <word> [--left-min N] [--right-min N] [--delimiter D]` -> Hyphenated word
  - `text <text> [--left-min N] [--right-min N] [--delimiter D]` -> Hyphenated text
  - `wrap <text> --width <N> [options]` -> Wrapped lines
  - `export-dic [options]` -> `.dic` pattern dictionary
  - `package-oxt [options]` -> LibreOffice extension
  - `process-docx [options]` -> Word document processor
