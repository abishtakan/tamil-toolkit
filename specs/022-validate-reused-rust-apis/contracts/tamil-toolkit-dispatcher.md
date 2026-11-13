# Contract: `tamil-toolkit` Dispatcher, Operations Inventory & Build Readiness

**Crate**: `tamil-toolkit` (`crates/tamil-toolkit/src/lib.rs`, `src/bin/tamil-toolkit.rs`, `Cargo.toml`)  
**Consumed by**: Rust callers, Python PyO3 (`bindings/python`), JS/WASM (`bindings/js-wasm`), Dart C FFI (`bindings/dart-flutter`), Golden parity runner

## 1. Dispatcher Completeness (`OPERATIONS` <-> `execute`)

- **Invariant**: Every operation string handled by `pub fn execute(request_json: &str)` MUST appear in `pub const OPERATIONS: &[&str]`, and every string in `OPERATIONS` MUST resolve cleanly (no `UnsupportedOperation` on valid input shapes) in `execute()`.
- **Previously missing from `OPERATIONS` (to add and lock with automated Rust test)**:
  1. `are_cognates`
  2. `baseline_maathirai`
  3. `calendar_display_info`
  4. `classify_quantity`
  5. `compare_calendar_profiles`
  6. `format_tamil_date`
  7. `get_cognate`
  8. `get_olippasai`
  9. `thiruvalluvar_year_info`

## 2. Dispatcher Request / Error Semantics

- Request envelope: `{"op": "<op_name>", "input": <json_value>}`.
- Invalid JSON -> `Err(ToolkitError::InvalidArgument(...))`.
- Missing `"op"` or non-string `"op"` -> `Err(ToolkitError::InvalidArgument(...))`.
- Unknown `"op"` -> `Err(ToolkitError::UnsupportedOperation(...))` (checked clearly and consistently).
- Operations accepting `null` / optional object input (relevant for upcoming Feature 021 operations such as `lexicon_packs`) MUST remain dispatchable without breaking existing operations that require `"input"` to be present and typed (`string`, `object`, `array`).
- `fold_for_search` rejects unknown `"profile"` names with `Err(ToolkitError::InvalidArgument("unknown folding profile: ..."))`.

## 3. CLI Error Contract (`tamil-toolkit norm`)

- `norm fold --profile <value> <text>` and `norm fold <text> --profile <value>` parse `<value>` strictly via `FoldingProfile::from_str`.
- Unknown `--profile` returns non-zero exit status with clear error message on stderr.

## 4. Packaging & Dependency Readiness for Feature 021

- `release-policy.toml` + `tools/release_policy.py` allow `tamil-toolkit` (Rank 5) to depend on `tamil-core` and `tamil-norm` in both `[dependencies]` and `[build-dependencies]`.
- `just check-release-policy`, `just check-unicode`, `just test-rust`, `just sync-bindings`, `just test-parity`, `just test-dart`, `just agent-pre-stop-gate` all execute cleanly on the repository.
