# Data Model: Validate Reused Rust APIs & NFC/NFD Normalization

**Feature**: `022-validate-reused-rust-apis`  
**Date**: 2026-11-13

## Entities

### 1. Reused API Validation Record (Contract Inventory)

Represents the verified reuse boundary for each exported Rust API consumed by Feature 021 across `tamil-core`, `tamil-norm`, and `tamil-toolkit`.

| Field | Type / Constraint | Description |
|-------|-------------------|-------------|
| `crate_name` | enum: `tamil-core`, `tamil-norm`, `tamil-toolkit` | Owning workspace crate |
| `symbol` | non-empty identifier (`fn`, `struct`, `const`, `op`) | Rust API symbol or dispatcher operation name |
| `normalization_precondition` | enum: `any_unicode`, `caller_nfc`, `internal_nfc`, `json_payload` | Whether the function normalizes internally or requires normalized input |
| `joiner_behavior` | enum: `preserve_verbatim`, `diagnostic_report`, `structural_delimiter` | Contract for `ZWJ` (`\u{200D}`), `ZWNJ` (`\u{200C}`), `BOM`, `SHY` |
| `error_contract` | structured error or total function | Failure modes (e.g., unknown profile, invalid JSON shape, single-letter fallback) |
| `verified_by` | non-empty list of test / golden paths | Unit test, proptest, golden JSONL ID, and parity runtime evidence |

### 2. Canonical Normalization Vector (`tests/golden/*.jsonl` Schema)

Follows the workspace golden vector schema (`tests/golden/manifest.json` + `tools/mcp-tamil-oracle/check_source_unicode.py`):

| Field | Type / Constraint | Description |
|-------|-------------------|-------------|
| `id` | unique global slug (`norm_canonical_###`) | Stable vector identifier across all JSONL suites |
| `op` | active op in `OPERATIONS` (`normalize_nfc`, `normalize_nfd`, `fold_for_search`, `repair_tamil_text`, `inspect_tamil_string`, `get_letters`, `classify_quantity`, `baseline_maathirai`, `get_cognate`, `are_cognates`, `get_olippasai`) | Dispatcher operation executed identically in Rust, Python, WASM, and Dart |
| `input` | escaped JSON string or object (zero raw non-ASCII in source) | Bounded test input; non-NFC or control inputs must declare `unicode_exceptions` |
| `expected` | escaped JSON output matching dispatcher return type | Expected exact canonical output |
| `dialect` | string (`COMMON` for canonical Unicode ops) | Pluricentric scope marker |
| `tags` | non-empty array of strings | Category tags (`canonical`, `nfc`, `nfd`, `ccc_reorder`, `format_control`, `shri`, `malformed`, `grantha`) |
| `source` | non-empty provenance citation (e.g. Unicode 17.0.0 UAX #15 / UCD 17.0.0 or internal spec) | Authoritative linguistic/Unicode reference |
| `unicode_exceptions` | optional array of `{path, kind, reason}` | Required by `check-unicode` whenever `input` or `expected` intentionally contains non-NFC, control, or non-canonical forms |

## State & Boundary Rules

- `normalize_nfc` and `normalize_nfd` are **total, deterministic, idempotent canonical transforms**:
  - `normalize_nfc(normalize_nfc(s)) == normalize_nfc(s)`
  - `normalize_nfd(normalize_nfd(s)) == normalize_nfd(s)`
  - `normalize_nfc(normalize_nfd(s)) == normalize_nfc(s)`
  - `normalize_nfd(normalize_nfc(s)) == normalize_nfd(s)`
- Format controls (`\u{200C}`, `\u{200D}`, `\u{FEFF}`, `\u{00AD}`) pass through `normalize_nfc` and `normalize_nfd` unchanged; UAX #15 decomposition/composition does not cross a `CCC=0` format control scalar (`\u{0B95}\u{0BC6}\u{200D}\u{0BBE}` must NOT merge `\u{0BC6}` and `\u{0BBE}` across `\u{200D}`).
- `OPERATIONS` in `tamil-toolkit` maintains strict set equality with implemented top-level arms in `execute()` (no missing ops, no unimplemented names).
