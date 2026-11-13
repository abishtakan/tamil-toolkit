# Quickstart Validation Guide: Feature 022 (`022-validate-reused-rust-apis`)

**Prerequisites** (Windows PowerShell from repo root `C:\Users\abish\Documents\dev\tamil-toolkit`):
```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
```

## 1. Validate Unicode, Escaping & Release Policy
```powershell
.\.venv\Scripts\python.exe tools\tasks.py check-unicode
.\.venv\Scripts\python.exe tools\tasks.py check-release-policy
```
**Expected**: Both exit `0`; `norm_canonical.jsonl` passes schema/escaping validation with declared `unicode_exceptions` on intentional NFD inputs.

## 2. Validate Rust Unit, Property (10,000+ cases), Integration & Clippy Gates
```powershell
cargo test --locked -p tamil-core -p tamil-norm -p tamil-toolkit
cargo clippy --locked -p tamil-core -p tamil-norm -p tamil-toolkit --all-targets -- -D warnings
```
**Expected**: All `tamil-core`, `tamil-norm` (including NFC/NFD property tests and NFD-input folding/repair tests), and `tamil-toolkit` (`OPERATIONS` completeness + CLI profile validation) tests pass with zero warnings.

## 3. Verify CLI Error Contract
```powershell
cargo run --locked -q -p tamil-toolkit --bin tamil-toolkit -- norm fold test --profile invalid
```
**Expected**: Prints invalid profile diagnostic to stderr and exits non-zero (NOT `0`).

## 4. Rebuild Bindings & Run Full Parity + Dart Gates (Sequentially)
```powershell
.\.venv\Scripts\python.exe tools\tasks.py agent-pre-stop-gate
.\.venv\Scripts\python.exe tools\tasks.py test-dart
```
**Expected**: `agent-pre-stop-gate` rebuilds PyO3 & WASM bindings and passes all active JSONL vectors across Rust, Python, and WASM (`0` failures, `0` skipped active tests); `test-dart` passes C ABI and Dart fixture tests sequentially after PyO3/WASM completes.
