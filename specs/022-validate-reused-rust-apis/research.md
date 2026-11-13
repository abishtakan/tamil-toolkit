# Research Findings: Validate Reused Rust APIs & NFC/NFD Normalization

**Feature**: `022-validate-reused-rust-apis`  
**Date**: 2026-11-13  
**Inputs Evaluated**: `crates/tamil-core`, `crates/tamil-norm`, `crates/tamil-toolkit`, `tests/golden/core_normalization.jsonl`, `tests/golden/norm_*.jsonl`, `Cargo.lock`

## Decisions & Evidence

### 1. Canonical NFC & NFD Normalization in `tamil-norm`

- **Decision**: Keep `tamil_norm::{normalize_nfc, normalize_nfd}` as direct zero-divergent re-exports of `tamil_core::{normalize_nfc, normalize_nfd}` backed by `unicode-normalization` `0.1.26` (`Cargo.lock`), and add crate-level unit/property tests (`>= 10,000` cases) plus dedicated escaped active golden vectors (`tests/golden/norm_canonical.jsonl`) executed across Rust, Python, WASM, and Dart.
- **Rationale**:
  - Empirical cross-checks against Python's `unicodedata` (`16.0.0`) across all two-part Tamil vowel signs (`\u{0BCA}` <-> `\u{0BC6}\u{0BBE}`, `\u{0BCB}` <-> `\u{0BC7}\u{0BBE}`, `\u{0BCC}` <-> `\u{0BC6}\u{0BD7}`, `\u{0B94}` <-> `\u{0B92}\u{0BD7}`), CCC mark reordering (`\u{0BCD}` CCC=9 paired with `\u{0301}` CCC=230), format controls (`\u{200C}`, `\u{200D}`, `\u{FEFF}`, `\u{00AD}`), Shri distinctions (`\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}` vs `\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}`), and malformed double vowels (`\u{0BA4}\u{0BC1}\u{0BBE}`) confirmed exact Unicode canonical behavior.
  - However, `crates/tamil-norm/tests/norm_tests.rs` currently contains only 3 basic tests (`கொ`, one `ZWJ`/`ZWNJ` check, one mixed-script check), `crates/tamil-norm/src/lib.rs` has 0 unit/proptest tests, and `tests/golden/` has no `norm_canonical.jsonl` suite testing `normalize_nfc`/`normalize_nfd` through `tamil-norm`'s own contract (especially CCC reordering, format-control preservation, idempotence, and cross-form round-trips).
- **Alternatives considered**:
  - Custom Tamil composition tables in `tamil-norm`: Rejected because `AGENTS.md` mandates `tamil-core` owns canonical Unicode primitives and `unicode-normalization` handles full Unicode UAX #15 ordering across mixed-script text without duplicating UCD tables.

### 2. NFD Input Consistency in `fold_for_search` and `repair_tamil_text`

- **Decision**: Retain internal NFC normalization/canonical handling inside `tamil-norm`, and lock down NFD-vs-NFC equivalence with exhaustive Tamil/Grantha sweep tests (23 base consonants/conjuncts including `\u{0B95}\u{0BCD}\u{0BB7}` across split vowels `\u{0BCA}`, `\u{0BCB}`, `\u{0BCC}` and profiles `mayangoli`, `grantha`, `comprehensive`) and property tests.
- **Rationale**:
  - Sweeping all 23 Tamil + Grantha (`\u{0B9C}`, `\u{0BB7}`, `\u{0BB8}`, `\u{0BB9}`, `\u{0B95}\u{0BCD}\u{0BB7}`) bases with split vowel signs (`\u{0BC6}\u{0BBE}`, `\u{0BC7}\u{0BBE}`, `\u{0BC6}\u{0BD7}`) and ZWNJ produced `0` mismatches between NFC and NFD inputs for both `fold_for_search` (all 3 profiles) and `repair_tamil_text`.
  - Visual-order kombu inputs (`\u{0BC6}\u{0B95}\u{0BBE}`, `\u{0BC7}\u{0B95}\u{0BBE}`, `\u{0BC6}\u{0B95}\u{0BD7}`, `\u{0BC8}\u{0B95}`) repaired identically to canonical composed vowels with `visual_kombu_count == 1`.
  - Adding dedicated regression + property tests guarantees NFD-input parity cannot regress before Feature 021 runs.
- **Alternatives considered**:
  - Normalizing blindly inside `Letters::new`: Rejected because `Letters::new` is explicitly documented as a zero-allocation borrowed iterator (`AGENTS.md` Principle 7 / `tamil-core` contract).

### 3. Reused `tamil-core` Function Contracts for Feature 021

- **Decision**: Validate and document exact contracts (with regression tests in `crates/tamil-core/tests/` / golden vectors) for every Feature 021 reused API rather than altering established single-letter or zero-allocation semantics:
  - `normalize_nfc`, `normalize_nfd`: canonical UAX #15 conversions.
  - `get_letters`: allocates and normalizes input to NFC before tailored cluster extraction.
  - `Letters::new`: borrowed zero-allocation iterator operating on caller-supplied normalization.
  - `split_uyirmei`, `compose_uyirmei`: round-trip uyirmei decomposition/composition.
  - `classify_quantity`, `baseline_maathirai`: single tailored letter contract (`Other` / `0.0` on multi-letter strings like `\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}`).
  - `get_cognate`, `are_cognates`, `get_olippasai`: consonant cognate & syllabic phonetic class helpers (`None` on multi-letter strings for `get_cognate`).
  - `inspect_tamil_string`: preserves joiners verbatim and reports `nfc`, `nfd`, `is_nfc`, `is_nfd`, `grapheme_count`, `ezhuthu_count`, and per-cluster `letters`; note verified behavior that `ZWJ`/`ZWNJ` extends UAX #29 clusters (`\u{0BB4}\u{0BCD}\u{200C}` classified `"other"`, lowering `ezhuthu_count`), so Feature 021's intake scanner inspects scalar format controls directly in addition to calling `inspect_tamil_string`.
- **Alternatives considered**:
  - Changing `classify_quantity` to split multi-letter strings silently: Rejected because it would break existing `tamil-core` unit/golden contract (`Other` / `0.0` for non-single letters).

### 4. `tamil-toolkit` Dispatcher (`OPERATIONS`) & CLI Validation Fixes

- **Decision**:
  1. Update `pub const OPERATIONS` in `crates/tamil-toolkit/src/lib.rs` to include all 9 implemented operations currently missing from it (`are_cognates`, `baseline_maathirai`, `calendar_display_info`, `classify_quantity`, `compare_calendar_profiles`, `format_tamil_date`, `get_cognate`, `get_olippasai`, `thiruvalluvar_year_info`), bringing `OPERATIONS` and `execute()` arms into exact 1:1 parity, backed by a Rust test asserting bidirectionally that `OPERATIONS` matches `execute()`.
  2. Fix `norm fold --profile <unknown>` in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` to return a non-zero exit error via `FromStr` (`FoldingProfile::from_str`) instead of silently falling back with `.unwrap_or(FoldingProfile::Comprehensive)`, while preserving valid profiles regardless of flag position before or after `<TEXT>` if already supported or rejecting unexpected unknown profile flags cleanly.
- **Rationale**:
  - Probing `crates/tamil-toolkit/src/lib.rs` proved `OPERATIONS` has 90 entries while `execute()` implements 99 unique operations (9 missing from `OPERATIONS`, 0 in `OPERATIONS` missing from `execute()` since the 8 `currency_*`/`tscii_*` ops live in multi-pattern match arms).
  - Running `cargo run --locked -q -p tamil-toolkit --bin tamil-toolkit -- norm fold test --profile invalid` exited `0` silently using `Comprehensive`, and `--profile invalid test` treated `--profile` as `<TEXT>` and printed `--profile` with exit `0`. In contrast, `_native.execute({'op': 'fold_for_search', 'input': {'text': ..., 'profile': 'invalid'}})` already rejects invalid profiles with an error. Aligning CLI behavior prevents silent misconfiguration.
- **Alternatives considered**:
  - Leaving `OPERATIONS` incomplete until Feature 021: Rejected because Feature 021 reuses `tamil-toolkit` dispatcher checks and `test-parity` / discovery should reflect reality cleanly beforehand.

### 5. Verification & Environment Execution Strategy (Windows)

- **Decision**: Follow the exact repo harness workflow:
  - Author/register escaped JSONL golden vectors in `tests/golden/norm_canonical.jsonl` and `tests/golden/manifest.json` before Rust edits.
  - Run `cargo` with `$env:USERPROFILE\.cargo\bin` prepended and `.venv\Scripts\python.exe tools/tasks.py ...` for repo tasks.
  - Run native/PyO3 parity checks (`test-parity` / `agent-pre-stop-gate`) and `test-dart` strictly sequentially to avoid Windows DLL locking (`docs/status.md`).
  - Keep Feature 021 artifacts (`specs/021-lexicon-curation/`) and immutable source files (`data/sources/tamil-lexicon/`) untouched.
