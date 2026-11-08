# Quickstart & Verification Guide: Phase 3 Consolidation

## Prerequisites
- Rust stable toolchain 1.95+
- Python 3.11+
- Node.js 20+

## Verification Commands

### 1. Check Release Policy
Verify that `tamil-hyphen` is in `public_crates` and passes dependency closure and rank invariants:
```bash
python tools/release_policy.py
# Or: just check-release-policy
```

### 2. Verify Active Golden Suite Parity
Verify that `hyphen_syllable.jsonl` runs as an active suite across Rust:
```bash
cargo test --test golden_suite
```

### 3. Verify Word Add-in Contract Tests
Run integration tests for the Office.js Word Add-in:
```bash
node --test tests/integrations/test_word_addin_contract.js
```

### 4. Verify CLI Subcommands
Build and test the expanded CLI:
```bash
cargo run -p tamil-toolkit --bin tamil-toolkit -- core letters "தமிழ்"
cargo run -p tamil-toolkit --bin tamil-toolkit -- norm nfc "தமிழ்"
cargo run -p tamil-toolkit --bin tamil-toolkit -- numerals to-words 2026
cargo run -p tamil-toolkit --bin tamil-toolkit -- hyphen word "பல்கலைக்கழகம்" -l 3 -r 3 -d "-"
```

### 5. Run Full Pre-Stop Gate
```bash
just agent-pre-stop-gate
```
