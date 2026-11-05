# Research & Design Decisions: Automatic Legacy Tamil Encoding Detection (`detect_encoding`)

**Feature**: `specs/003-codec-detection`  
**Date**: 2026-11-05  
**Status**: Completed  

---

## 1. Detection Scoring Engine & Trie Reuse

### Decision
Reuse the existing decoder trie structures (`tables::NODES`, `tscii_tables::NODES`, `tab_tables::NODES`, `tam_tables::NODES`, `anjal_tables::NODES`, `lt_tm_tables::NODES`, and `vanavil_tables::NODES`) already generated in `crates/tamil-codec` to drive candidate scoring, augmented by signature n-gram patterns and invalid byte penalties.

### Rationale
- Existing tries in `tamil-codec` already encode exact valid transition edge tables (`edges: &'static [(u8, usize)]`) for all supported legacy encodings.
- Iterating across a borrowed slice (`&[u8]`) with trie traversal requires zero heap allocation, ensuring deterministic, seek-safe execution.
- Computes valid-transition density:
  $$\text{Score}(E) = \frac{\text{Valid Trie Steps} + \text{Signature Boosts} - \text{Illegal Penalties}}{\text{Evaluated Units}}$$
- Satisfies SC-003 (< 5µs latency budget for 1KB buffers) without introducing any external dependencies.

### Alternatives Considered
- **External Bayesian / ML Classifiers (e.g. `uchardet` or fastText)**: Rejected due to large binary footprints, unpredictable latency, memory allocation overhead, and violation of the self-contained zero-dependency mandate in `tamil-toolkit`.
- **Pure Unigram Byte Frequency Tables**: Rejected because 8-bit encodings like TAB and TAM share many individual byte ranges, leading to ambiguity that only multi-byte ligature transitions (n-grams) can resolve.

---

## 2. Mixed English & Legacy Tamil Handling

### Decision
Implement isolated scoring based on encoding class:
1. **8-bit Encodings (`tscii-1.7-v1`, `tab-v1`, `tam-v1`)**: Standard ASCII (`0x00..0x7F`) bytes are treated as neutral. The scoring engine evaluates confidence strictly on the non-ASCII (`0x80..0xFF`) byte transitions.
2. **ASCII Typewriter Encodings (`bamini-v1`, `anjal-v1`)**: Because these layouts map Tamil glyphs directly onto ASCII alphanumeric keys, plain English words could theoretically overlap with Bamini. The engine scores typewriter encodings by identifying distinctive Tamil consonant-vowel key digraphs (e.g. prefix vowel signs like `n` followed by consonants) and penalizes common English word morphology (e.g. stop words like `the`, `and`, `is`).
3. **Threshold Gate**: If Tamil-distinctive patterns are absent or below a minimum discriminative density (< 4 meaningful units), the result falls back to `status: "uncertain"` with reason `"no legacy tamil patterns detected"`.

### Rationale
- Archival documents, database fields, and web scrapes frequently mix English headers, URLs, and citations with legacy Tamil text.
- Eliminates false positives on pure English text (SC-002: 0% false positive rate) while maintaining high confidence (> 0.85) on real-world bilingual documents.

### Alternatives Considered
- **Token-Level Document Segmentation**: Splitting text into whitespace-delimited tokens and classifying each token separately. Rejected because it requires heap allocations and string tokenization, violating zero-allocation requirements.
- **Strict English Rejection**: Requiring documents to be 100% Tamil. Rejected as impractical for real-world legacy data.

---

## 3. Buffer Sampling & Performance Budget

### Decision
The detection engine automatically inspects up to the first 4,096 bytes (4 KB) for `&[u8]` or 4,096 code units for `&[u16]`. Any data beyond this threshold is ignored during scoring.

### Rationale
- Statistical sample theory demonstrates that 4 KB of text provides overwhelming discriminative power (thousands of character transitions) to classify document encoding with >99% confidence.
- Guarantees upper-bounded execution time regardless of whether the caller passes a 10 KB snippet or a 500 MB database dump, ensuring compliance with SC-003 (< 5µs benchmark target).

### Alternatives Considered
- **Full Buffer Scanning**: Scanning the entirety of unbounded input. Rejected because multi-megabyte files cause unpredictable latency spikes.
- **Configurable Options Struct**: Providing `sample_size: usize`. Kept as an optional internal constant with 4 KB default; exposing a mandatory options struct would overcomplicate the standard high-level API.

---

## 4. Multi-Runtime Dispatcher & String/CID Routing

### Decision
Expose `detect_encoding` and `detect_and_decode` in `crates/tamil-toolkit/src/lib.rs` and across all high-level language bindings (Python, WebAssembly, Dart):
1. **Raw Byte Buffers (`&[u8]`, `bytes`, `Uint8Array`, `Uint8List`)**: Dispatches to 8-bit encoding detection (`bamini-v1`, `tscii-1.7-v1`, `tab-v1`, `tam-v1`, `anjal-v1`, `utf-8`).
2. **Text Strings (`&str`, `str`, `string`, `String`)**:
   - First checks if text contains valid UTF-8 Tamil script (`\u{0B80}..\u{0BFF}`). If so, returns `utf-8` with 1.0 confidence.
   - If text contains Private Use Area (PUA `\u{E000}..\u{F8FF}`) or 16-bit CID units, also runs `detect_encoding_cids` on UTF-16 code units.
   - Concurrently checks 8-bit profiles on the string's UTF-8 bytes.
   - Unifies all candidates in a single ranked `DetectionResult`.
3. **`detect_and_decode` Convenience Helper**: Runs `detect_encoding`; if `status == "detected"`, decodes directly into NFC Unicode; if `status == "uncertain"`, returns a typed `UncertainEncoding` error with the specific failure reason.

### Rationale
- PDF text extractors and document parsers frequently extract legacy font runs as strings (sometimes using PUA codepoints, sometimes using ASCII bytes decoded as Latin-1). A unified dispatcher relieves developers from guessing whether their PDF used 8-bit or 16-bit font hacks.
- Tri-runtime parity is preserved across Rust, Python, and WASM.

### Alternatives Considered
- **Separate CIDs API Only**: Requiring callers to know ahead of time whether a document is CID-encoded. Rejected because end users rarely know the internal PDF font type.
