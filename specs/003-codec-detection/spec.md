# Feature Specification: Automatic Legacy Tamil Encoding Detection (`detect_encoding`)

**Feature Directory**: `specs/003-codec-detection`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Specification for an automatic legacy Tamil encoding detection engine (`detect_encoding`) in tamil-codec."

## Clarifications

### Session 2026-11-05
- Q: Which legacy encodings must be detectable?
  → A: All 7 profiles supported by `tamil-codec`:
    1. `bamini-v1` (ASCII typewriter layout)
    2. `tscii-1.7-v1` (8-bit standardized encoding)
    3. `tab-v1` (Bilingual 8-bit standard)
    4. `tam-v1` (Monolingual 8-bit standard)
    5. `anjal-v1` (Phonetic byte encoding)
    6. `lt-tm-cid-v1` (16-bit IndoWord / LT-TM CID code units)
    7. `vanavil-avvaiyar-cid-v1` (16-bit Vanavil Avvaiyar CID code units)
- Q: How should ambiguity and short inputs be handled?
  → A: When byte sequences are ambiguous (e.g. pure ASCII English text, or byte combinations shared by multiple font layouts) or the input is shorter than a minimum discriminative threshold (e.g. < 4 meaningful bytes), the engine MUST return `status: "uncertain"` with a candidate list and confidence scores rather than guessing.
- Q: What input formats must be supported?
  → A: Both raw byte buffers (`&[u8]`) for 8-bit encodings (Bamini, TSCII, TAB, TAM, Anjal) and text strings / 16-bit code units (`&[u16]` / `&str`) for CID font runs (LT-TM and Vanavil).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - High-Confidence Detection Across Supported Legacy Encodings (Priority: P1) 🎯 MVP

As an end user or developer processing legacy Tamil documents, websites, or database archives, I want to pass an unlabelled buffer of text or bytes to `detect_encoding` and receive the correct encoding identifier with a high confidence score (> 0.85) so that I can automatically decode the content into standard Unicode without manual inspection.

**Why this priority**: Solves the primary pain point for Tamil archival processing where documents lack charset headers or specify generic headers like `windows-1252` or `ASCII`.

**Independent Test**: Can be independently verified by feeding sample paragraphs from each of the 7 supported encodings into `detect_encoding` and asserting that the top detected profile matches the expected encoding with high confidence.

**Acceptance Scenarios**:
1. **Given** a byte buffer encoded in TSCII 1.7, **When** calling `detect_encoding(bytes)`, **Then** the result returns `{ "encoding": "tscii-1.7-v1", "confidence": >= 0.90, "status": "detected" }`.
2. **Given** an ASCII text stream using Bamini typewriter glyph sequences, **When** calling `detect_encoding(bytes_or_str)`, **Then** the result returns `{ "encoding": "bamini-v1", "confidence": >= 0.90, "status": "detected" }`.
3. **Given** a 16-bit CID stream from a Vanavil Avvaiyar PDF font run, **When** calling `detect_encoding_cids(codes)`, **Then** the result returns `{ "encoding": "vanavil-avvaiyar-cid-v1", "confidence": >= 0.90, "status": "detected" }`.
4. **Given** a 16-bit CID stream from an LT-TM / IndoWord font run, **When** calling `detect_encoding_cids(codes)`, **Then** the result returns `{ "encoding": "lt-tm-cid-v1", "confidence": >= 0.90, "status": "detected" }`.

---

### User Story 2 - Ambiguity Handling & Uncertain Fallback (Priority: P2)

As a robust data pipeline engineer, I want the detection engine to explicitly flag ambiguous, mixed, or insufficiently long inputs as `uncertain` so that my system does not inadvertently corrupt data by applying incorrect decoding transforms.

**Why this priority**: Avoids false positives on plain English text, short labels (1-2 characters), or overlapping code points.

**Independent Test**: Verify that plain ASCII strings (e.g. `"Hello World"`, `"12345"`), short 2-byte inputs, and conflicting byte patterns return `status: "uncertain"` with `encoding: null`.

**Acceptance Scenarios**:
1. **Given** a pure ASCII English sentence containing no distinctive Tamil typewriter patterns, **When** calling `detect_encoding(bytes)`, **Then** the result returns `{ "status": "uncertain", "encoding": null, "candidates": [...] }`.
2. **Given** an input buffer with length < 4 bytes, **When** calling `detect_encoding(bytes)`, **Then** the result returns `{ "status": "uncertain", "reason": "insufficient input length" }`.
3. **Given** an input containing invalid or reserved byte sequences for a candidate profile, **When** evaluating that profile, **Then** its confidence score drops to zero or is eliminated from candidate ranking.

---

### User Story 3 - Multi-Runtime Access via Umbrella Toolkit (Priority: P3)

As a Python, TypeScript, or Flutter developer, I want uniform detection APIs exposed through `tamil-toolkit` so that I can detect encodings in web browsers, backend scripts, and mobile apps.

**Why this priority**: Enables developers in web, mobile, and data science ecosystems to use detection seamlessly without writing custom FFI glue.

**Independent Test**: Execute detection test fixtures across Python (`tamil_toolkit.detect_encoding`), WebAssembly (`api.detectEncoding`), and Dart (`tamilToolkit.detectEncoding`) verifying identical detection outputs.

**Acceptance Scenarios**:
1. **Given** Python `tamil_toolkit.detect_encoding(data)`, **When** passing a bytes or string object, **Then** a Python dictionary matching the standard detection schema is returned.
2. **Given** WebAssembly `api.detectEncoding(data)`, **When** passing a Uint8Array or string, **Then** a typed `DetectionResult` object is returned.
3. **Given** Dart `tamilToolkit.detectEncoding(data)`, **When** passing a Uint8List or String, **Then** a typed Dart `DetectionResult` is returned.

---

### Edge Cases

- What happens when input is already valid UTF-8 Tamil text (e.g. contains `\u{0B80}..\u{0BFF}`)? The engine MUST detect this and report `encoding: "utf-8"` with `confidence: 1.0` so consumers do not double-convert.
- What happens when an input contains mixed English and legacy Tamil text? The detection engine MUST weight distinctive multi-byte n-gram sequences to identify the Tamil encoding embedded within the stream.
- What happens with empty inputs (`b""` or `""`)? It MUST return `status: "uncertain"` with `reason: "empty input"`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `tamil-codec` MUST implement `detect_encoding(input: &[u8]) -> DetectionResult` analyzing byte-level distributions and n-gram signatures for 8-bit encodings (`bamini-v1`, `tscii-1.7-v1`, `tab-v1`, `tam-v1`, `anjal-v1`, `utf-8`).
- **FR-002**: `tamil-codec` MUST implement `detect_encoding_cids(codes: &[u16]) -> DetectionResult` for 16-bit font code units (`lt-tm-cid-v1`, `vanavil-avvaiyar-cid-v1`).
- **FR-003**: The detection algorithm MUST compute normalized confidence scores between `0.0` and `1.0` based on:
  - Valid transition frequency in the encoding's decode trie.
  - Presence of signature n-grams (e.g. vowel sign prefixes or specific ligature sequences unique to that profile).
  - Penalty for illegal or reserved byte positions.
- **FR-004**: If the difference between the top two candidate confidence scores is below `0.15`, or the top confidence is below `0.60`, the engine MUST designate the result as `status: "uncertain"`.
- **FR-005**: All detection operations MUST be deterministic, seek-safe, non-allocating during scoring where feasible, and thread-safe.
- **FR-006**: The dispatcher in `crates/tamil-toolkit/src/lib.rs` MUST expose `detect_encoding` as a standard operation accepting either raw byte arrays or text strings.
- **FR-007**: High-level bindings (Python, WebAssembly, Dart) MUST expose `detect_encoding` with idiomatic parameter types.

### Key Entities

- **DetectionResult**:
  - `status`: `"detected" | "uncertain"`
  - `encoding`: `Option<String>` (e.g. `"bamini-v1"`, `"tscii-1.7-v1"`, or `None` if uncertain)
  - `confidence`: `f64` (normalized 0.0 to 1.0)
  - `candidates`: `Vec<EncodingCandidate>` (list of scored encodings ordered by confidence)
- **EncodingCandidate**:
  - `encoding`: `String`
  - `confidence`: `f64`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Detection accuracy exceeds 98% on test corpuses (> 50 characters) across all 7 supported encodings.
- **SC-002**: False positive rate on plain English text is 0% (always classified as `uncertain` or `utf-8`/ASCII).
- **SC-003**: Detection completes in under 5 microseconds for buffers under 1KB in Rust benchmarks.
- **SC-004**: Golden test suite `codec_detection.jsonl` contains at least 150 diverse test cases covering single words, paragraphs, mixed text, and edge cases, passing 100% across Rust, Python, and WASM.

## Assumptions

- Analysis can be performed on the first 1KB to 4KB of a document with sufficient statistical power to classify the entire stream.
- No new external crates or heavy statistical model dependencies are required; scoring relies on trie valid-path ratios and signature character n-grams compiled into `tamil-codec`.
