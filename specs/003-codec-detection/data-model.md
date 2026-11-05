# Data Model: Automatic Legacy Tamil Encoding Detection (`detect_encoding`)

**Feature**: `specs/003-codec-detection`  
**Date**: 2026-11-05  
**Status**: Completed  

---

## Entities & Value Objects

### 1. `DetectionResult`
Represents the comprehensive outcome of an encoding detection attempt.

| Field | Type | Description | Required | Notes |
|-------|------|-------------|----------|-------|
| `status` | `DetectionStatus` (`"detected" \| "uncertain"`) | High-level status flag | Yes | Indicates if a confident encoding was determined |
| `encoding` | `Option<String>` | Canonical identifier of detected profile | No | Present (`Some`) if `status == "detected"`, `None` if uncertain |
| `confidence` | `f64` | Normalized confidence score [0.0, 1.0] | Yes | Top candidate's confidence score |
| `reason` | `Option<String>` | Explanation for uncertainty or detection mode | No | Present (`Some`) if `status == "uncertain"` (e.g. `"empty input"`, `"insufficient input length"`, `"low confidence"`, `"conflicting candidates"`) |
| `candidates` | `Vec<EncodingCandidate>` | Scored candidate encodings | Yes | All evaluated profiles sorted in descending order of confidence |

---

### 2. `EncodingCandidate`
Represents an individual encoding evaluated during scoring.

| Field | Type | Description | Required | Notes |
|-------|------|-------------|----------|-------|
| `encoding` | `String` | Canonical profile name | Yes | e.g. `"bamini-v1"`, `"tscii-1.7-v1"`, `"tab-v1"`, `"tam-v1"`, `"anjal-v1"`, `"lt-tm-cid-v1"`, `"vanavil-avvaiyar-cid-v1"`, `"utf-8"` |
| `confidence` | `f64` | Normalized confidence score [0.0, 1.0] | Yes | Computed from trie transitions, signature n-grams, and penalties |

---

### 3. `DetectionStatus` (Enum)

| Variant | String Value | Invariant Rules |
|---------|--------------|-----------------|
| `Detected` | `"detected"` | `encoding.is_some()`, `confidence >= 0.60`, top candidate leads runner-up by $\ge 0.15$, `reason == None` |
| `Uncertain` | `"uncertain"` | `encoding == None`, `reason.is_some()`, top confidence $< 0.60$ OR delta to second candidate $< 0.15$ OR input $< 4$ bytes |

---

## Canonical Encoding Profile Identifiers

The detection engine evaluates and identifies the following canonical profile strings:

| Encoding Identifier | Category | Input Type | Description |
|---------------------|----------|------------|-------------|
| `"bamini-v1"` | 8-bit Typewriter | Bytes / ASCII string | Typewriter layout mapping Tamil glyphs to ASCII keys |
| `"tscii-1.7-v1"` | 8-bit Standard | Bytes | Tamil Standard Code for Information Interchange 1.7 |
| `"tab-v1"` | 8-bit Standard | Bytes | Bilingual Tamil script encoding standard |
| `"tam-v1"` | 8-bit Standard | Bytes | Monolingual Tamil script encoding standard |
| `"anjal-v1"` | 8-bit Phonetic | Bytes | Anjal phonetic byte-level legacy font layout |
| `"lt-tm-cid-v1"` | 16-bit Font CID | Codes / PUA string | IndoWord / LT-TM CID 16-bit font glyph indices |
| `"vanavil-avvaiyar-cid-v1"` | 16-bit Font CID | Codes / PUA string | Vanavil Avvaiyar CID 16-bit font glyph indices |
| `"utf-8"` | Modern Unicode | Bytes / Text string | Standard native Unicode Tamil script (`\u{0B80}..\u{0BFF}`) |

---

## Scoring & Classification Invariants

1. **Deterministic Upper Bound**:
   - The engine evaluates at most the first 4,096 bytes or 4,096 code units (`sample_size = min(input.len(), 4096)`).
2. **Confidence Normalization**:
   - Every confidence score is strictly bounded: $0.0 \le \text{confidence} \le 1.0$.
3. **Candidate Ordering**:
   - `candidates` MUST be sorted strictly in descending order of `confidence`. If scores tie, stable lexicographic order by `encoding` is preserved.
4. **Uncertainty Gate**:
   - If input is empty (`len == 0`) $\implies$ `status: "uncertain"`, `reason: "empty input"`.
   - If input is $< 4$ non-whitespace bytes $\implies$ `status: "uncertain"`, `reason: "insufficient input length"`.
   - If top candidate confidence $< 0.60 \implies$ `status: "uncertain"`, `reason: "low confidence"`.
   - If (top confidence - 2nd confidence) $< 0.15 \implies$ `status: "uncertain"`, `reason: "conflicting candidates"`.
   - Pure English text (no distinctive Tamil n-grams) $\implies$ `status: "uncertain"`, `reason: "no legacy tamil patterns detected"`.
