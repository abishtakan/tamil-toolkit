# Quickstart & Validation Guide: Automatic Legacy Tamil Encoding Detection

**Feature**: `specs/003-codec-detection`  
**Date**: 2026-11-05  

This guide provides end-to-end validation scenarios and commands to verify that `detect_encoding` and `detect_and_decode` function accurately across all supported encodings and runtimes.

---

## 1. Prerequisites & Environment Setup

Ensure the repository dependencies and toolchains are installed:
```powershell
# Verify Rust toolchain
cargo --version

# Verify golden datasets and parity test runner
just --version
```

---

## 2. Validation Scenarios

### Scenario 1: High-Confidence Detection on TSCII 1.7 Buffer
**Input**: Sourced TSCII byte buffer (e.g. `[0xA1, 0xAA, 0xAF]...`).
```rust
use tamil_codec::{detect_encoding, DetectionStatus};

let sample_tscii: &[u8] = &[/* tscii bytes */];
let result = detect_encoding(sample_tscii);

assert_eq!(result.status, DetectionStatus::Detected);
assert_eq!(result.encoding.as_deref(), Some("tscii-1.7-v1"));
assert!(result.confidence >= 0.90);
assert!(result.reason.is_none());
```

---

### Scenario 2: ASCII Typewriter (Bamini) vs English Disambiguation
**Input**: Bamini typewriter string (e.g. `"jkpH"` for தமிழ்) vs plain English text (`"The quick brown fox"`).
```rust
use tamil_codec::{detect_encoding, DetectionStatus};

// Bamini detection
let bamini_bytes = b"jkpH";
let res_bamini = detect_encoding(bamini_bytes);
assert_eq!(res_bamini.status, DetectionStatus::Detected);
assert_eq!(res_bamini.encoding.as_deref(), Some("bamini-v1"));

// English text detection
let english_bytes = b"The quick brown fox jumps over the lazy dog";
let res_english = detect_encoding(english_bytes);
assert_eq!(res_english.status, DetectionStatus::Uncertain);
assert_eq!(res_english.encoding, None);
assert_eq!(res_english.reason.as_deref(), Some("no legacy tamil patterns detected"));
```

---

### Scenario 3: Mixed English and Legacy Tamil Document
**Input**: Mixed document with English headings and TSCII paragraphs.
```rust
use tamil_codec::{detect_encoding, DetectionStatus};

let mut doc = Vec::new();
doc.extend_from_slice(b"Chapter 1: History of Tamil Literature\n\n");
doc.extend_from_slice(&[/* tscii paragraphs with 0x80..0xFF bytes */]);

let result = detect_encoding(&doc);
assert_eq!(result.status, DetectionStatus::Detected);
assert_eq!(result.encoding.as_deref(), Some("tscii-1.7-v1"));
```

---

### Scenario 4: CID Font Code Units (16-bit LT-TM and Vanavil)
**Input**: 16-bit glyph unit slices (`&[u16]`).
```rust
use tamil_codec::{detect_encoding_cids, DetectionStatus};

let lt_tm_codes: &[u16] = &[/* LT-TM glyph indices */];
let result = detect_encoding_cids(lt_tm_codes);
assert_eq!(result.status, DetectionStatus::Detected);
assert_eq!(result.encoding.as_deref(), Some("lt-tm-cid-v1"));
```

---

### Scenario 5: End-to-End `detect_and_decode`
**Input**: Legacy buffer without prior encoding knowledge.
```rust
use tamil_codec::detect_and_decode;

let tscii_sample = &[/* tscii bytes for தமிழ் */];
let unicode_text = detect_and_decode(tscii_sample).expect("successful decode");
assert_eq!(unicode_text, "தமிழ்");

// Empty input returns error
let err = detect_and_decode(b"").unwrap_err();
assert_eq!(err, "empty input");
```

---

## 3. Automated Test Execution

Run the complete suite of Rust tests, golden parity suites, and quality gates:

```powershell
# 1. Run unit tests in tamil-codec
cargo test -p tamil-codec

# 2. Run golden vectors across multi-runtime dispatcher
cargo test -p tamil-toolkit --test codec_detection

# 3. Synchronize bindings & verify tri-runtime parity
just sync-bindings
just test-parity

# 4. Execute pre-stop quality gate
just agent-pre-stop-gate
```
