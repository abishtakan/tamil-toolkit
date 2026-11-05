# Contract: Rust Public API

**Feature**: `specs/003-codec-detection`  
**Target Crates**: `crates/tamil-codec`, `crates/tamil-toolkit`  

---

## 1. `tamil-codec` Interface Contract

```rust
pub const MAX_SAMPLE_BYTES: usize = 4096;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DetectionStatus {
    Detected,
    Uncertain,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EncodingCandidate {
    pub encoding: String,
    pub confidence: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DetectionResult {
    pub status: DetectionStatus,
    pub encoding: Option<String>,
    pub confidence: f64,
    pub reason: Option<String>,
    pub candidates: Vec<EncodingCandidate>,
}

/// Detects legacy Tamil encoding from a raw byte slice (8-bit encodings + UTF-8).
///
/// Invariant: Scans up to `MAX_SAMPLE_BYTES` (4,096 bytes).
/// Deterministic, seek-safe, and non-allocating during scoring.
pub fn detect_encoding(input: &[u8]) -> DetectionResult;

/// Detects 16-bit font CID code units (LT-TM and Vanavil Avvaiyar).
///
/// Invariant: Scans up to `MAX_SAMPLE_BYTES` (4,096 code units).
pub fn detect_encoding_cids(codes: &[u16]) -> DetectionResult;

/// Convenience function that detects the encoding and decodes to NFC Unicode.
///
/// Returns `Ok(String)` if `status == DetectionStatus::Detected`.
/// Returns `Err(String)` describing the uncertainty if `status == DetectionStatus::Uncertain`.
pub fn detect_and_decode(input: &[u8]) -> Result<String, String>;
```

---

## 2. `tamil-toolkit` Umbrella Dispatcher Contract

```rust
// Added to crates/tamil-toolkit/src/lib.rs

pub const OPERATIONS: &[&str] = &[
    // ... existing operations ...
    "detect_encoding",
    "detect_and_decode",
];

// Handles:
// { "op": "detect_encoding", "input": { "bytes": [...] } } OR
// { "op": "detect_encoding", "input": { "text": "..." } } OR
// { "op": "detect_encoding", "input": { "codes": [...] } }
//
// And:
// { "op": "detect_and_decode", "input": { "bytes": [...] } } OR
// { "op": "detect_and_decode", "input": { "text": "..." } }
```
