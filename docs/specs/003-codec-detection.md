# Specification: Automatic Legacy Tamil Encoding Detection (`detect_encoding`)

## Overview

The `detect_encoding` feature in `tamil-codec` and `tamil-toolkit` provides automatic, deterministic, zero-dependency identification of legacy Tamil text encodings from raw byte slices or 16-bit CID code unit sequences. It reliably identifies 7 legacy encodings alongside native UTF-8:
- **8-bit byte-stream encodings**: Bamini (`bamini-v1`), TSCII 1.7 (`tscii-1.7-v1`), TAB (`tab-v1`), TAM (`tam-v1`), Anjal (`anjal-v1`), and native UTF-8 (`utf-8`).
- **16-bit CID code unit encodings**: LT-TM (`lt-tm-cid-v1`) and Vanavil Avvaiyar (`vanavil-avvaiyar-cid-v1`).

When detection succeeds with high confidence, `detect_and_decode` transparently converts the input to standardized Unicode NFC Tamil text.

---

## Architectural Principles & Guarantees

1. **Zero External Dependencies**:
   Detection is implemented using static prefix tables, bitmasks, transition matrices, and n-gram frequency lookup arrays compiled directly into the binary.
2. **Bounded Resource Consumption**:
   To prevent denial-of-service on large files, detection inspects a maximum of 4,096 bytes or 16-bit code units (`MAX_INSPECTION_BYTES`).
3. **Strict 0% False Positive Rate on English**:
   Plain ASCII text, English prose, and dictionary words (such as `"the"`, `"and"`, `"this"`) are penalized or treated neutrally, returning `status: "uncertain"` with reason `"insufficient Tamil markers"`.
4. **Short Buffer Rejection**:
   Buffers shorter than 4 bytes or code units cannot establish statistical confidence and return `status: "uncertain"` with reason `"insufficient input length"`. Empty buffers return reason `"empty input"`.
5. **Delta Margin Enforcement**:
   A winning candidate must score confidence $\ge 0.60$ and maintain a separation margin $\ge 0.15$ over the runner-up candidate. If the top two candidates are tied or separated by $< 0.15$, the result is designated `status: "uncertain"` with reason `"ambiguous encoding candidate distribution"`.
6. **Classical Tamil Orthographic Invariants**:
   - Virama (`\u{0BCD}`) must never follow a vowel sign (`\u{0BBE}..\u{0BCC}`) or independent vowel (`\u{0B85}..\u{0B94}`).
   - Tamil numerals (`\u{0BE6}..\u{0BF2}`) attached directly to Tamil consonants indicate font glyph mojibake.
   - Punctuation quotes must not appear inside word tokens sandwiched between Tamil characters.
   - Poetic elongation (Uyiralapedai, where an independent vowel follows a long vowel, e.g. `தூஉம்`) is explicitly recognized as valid Classical Tamil and not penalized.

---

## Profile Disambiguation

- **TAB vs TAM**: TAM possesses compatibility mappings covering decomposed high bytes (`0xA0..0xFF`) used natively by TAB. When a byte buffer contains high-byte decomposed markers without TAM's characteristic precomposed points (`0x41..0x7E`, `0x80..0x9F`), TAM's score is adjusted by factor $0.70$, allowing TAB to win decisively.
- **LT-TM vs Vanavil Avvaiyar**: LT-TM assigns short *i* uyirmei to `0x00C0..=0x00CF` and *lī* to `0x00E4`. Vanavil assigns short *i* uyirmei to `0x00E0..=0x00EF` and *lī* to `0x00C4`. Signature checks on decoded tokens penalize the inverse mapping and disambiguate near-identical CID tables.
- **Unified String Evaluation**: In `tamil-toolkit`, callers can pass raw strings or byte arrays. 16-bit CID profiles are evaluated only when non-ASCII (`> 0x007F`) or PUA code units (`0xE000..=0xF8FF`) are present, ensuring typewriter profiles like Bamini are not misidentified as CIDs.

---

## Public API Contract

### Rust (`crates/tamil-codec`)

```rust
pub enum DetectionStatus {
    Detected,
    Uncertain,
}

pub struct EncodingCandidate {
    pub encoding: String,
    pub confidence: f64,
}

pub struct DetectionResult {
    pub status: DetectionStatus,
    pub encoding: Option<String>,
    pub confidence: f64,
    pub reason: Option<String>,
    pub candidates: Vec<EncodingCandidate>,
}

pub fn detect_encoding(bytes: &[u8]) -> DetectionResult;
pub fn detect_encoding_cids(codes: &[u16]) -> DetectionResult;
pub fn detect_and_decode(bytes: &[u8]) -> Result<String, String>;
```

### Unified Dispatcher (`crates/tamil-toolkit`)

Operations registered in `OPERATIONS`:
- `"detect_encoding"`: accepts `{"bytes": [...]}` or `{"codes": [...]}` or `{"text": "..."}`. Returns `DetectionResult` JSON.
- `"detect_and_decode"`: accepts `{"bytes": [...]}` or `{"codes": [...]}` or `{"text": "..."}`. Returns `{"text": "..."}` or error JSON.

### Multi-Runtime Bindings

- **Python (`tamil_toolkit`)**:
  - `detect_encoding(data: Union[bytes, str, Sequence[int]]) -> Dict[str, Any]`
  - `detect_and_decode(data: Union[bytes, str, Sequence[int]]) -> str`
- **WebAssembly / TypeScript (`tamil-toolkit`)**:
  - `detectEncoding(input: Uint8Array | Uint16Array | number[] | string): DetectionResult`
  - `detectAndDecode(input: Uint8Array | Uint16Array | number[] | string): string`
- **Dart (`tamil_toolkit`)**:
  - `detectEncoding(dynamic input): DetectionResult`
  - `detectAndDecode(dynamic input): String`
