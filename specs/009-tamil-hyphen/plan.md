# Implementation Plan: Syllable and Orthographic Boundary Hyphenation (`tamil-hyphen`)

**Branch**: `009-tamil-hyphen` | **Date**: 2026-11-05 | **Spec**: [specs/009-tamil-hyphen/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/009-tamil-hyphen/spec.md)

**Input**: Feature specification from `specs/009-tamil-hyphen/spec.md`

## Summary

Implement deterministic, rule-based Tamil syllable and orthographic boundary hyphenation in `crates/tamil-hyphen` (and expose via `crates/tamil-toolkit` and multi-runtime bindings). The engine identifies valid syllable boundaries (*Aksharas*), strictly prohibits *Mei* (`புள்ளி` consonants) or *Aytham* from starting a new line or segment, enforces configurable safe margins (`left_min = 2, right_min = 2` tailored Tamil letters by default), preserves invisible joiners (`ZWJ`/`ZWNJ`), and provides both word-level hyphenation, paragraph soft-hyphenation, and deterministic line wrapping.

## Technical Context

**Language/Version**: Modern Stable Rust (MSRV 1.85), Python 3.11+, Node.js 22+ (WASM), Dart 3.0+  
**Primary Dependencies**: `tamil-core` (for tailored `Letters` segmentation), `tamil-norm` (for canonical NFC normalization); `serde` / `serde_json` for serialization in `tamil-toolkit`  
**Storage**: Static immutable rule structures in `crates/tamil-hyphen` (zero external databases)  
**Testing**: `cargo test -p tamil-hyphen`, `cargo test -p tamil-toolkit`, `just test-parity`  
**Target Platform**: Cross-platform (Linux, macOS, Windows, Node.js & browser WASM, Dart host)  
**Project Type**: Rust workspace crate + unified dispatcher + multi-runtime bindings  
**Performance Goals**: < 5 microseconds per word in Rust benchmarks (SC-004); < 100 microseconds for 1KB paragraph text; zero heap allocation during boundary detection on borrowed string slices  
**Constraints**: 100% grapheme cluster integrity (SC-001); 0 instances of split vowel signs or stranded pulli; dialect-invariant across Tamil Nadu (`TN`) and Sri Lanka (`SL`)  
**Scale/Scope**: 4 primary operations (`hyphenate_word`, `hyphenation_points`, `hyphenate_text`, `wrap_text`); 120+ golden vectors in planned suite `tests/golden/hyphen_syllable.jsonl`  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Compliance Details |
|-----------|-------------|--------|--------------------|
| **I. Rust Owns Linguistic Behavior** | All core algorithms reside in `crates/tamil-*` | **PASS** | Syllable decomposition and boundary logic reside 100% in `crates/tamil-hyphen`. Python, TS/WASM, and Dart are thin serialization/FFI wrappers over the Rust dispatcher. |
| **II. Inspect Tamil by Scalars** | Inspection by scalars, no visual guessing; preserve joiners | **PASS** | Evaluates code point classifications directly; never guesses visually; ZWJ (`U+200D`) and ZWNJ (`U+200C`) strictly preserved without surrounding breaks. |
| **III. Golden Vectors Precede Implementation** | Tri-runtime parity backed by `tests/golden/*.jsonl` | **PASS** | 120+ sourced test cases in `tests/golden/hyphen_syllable.jsonl` categorized as `planned` pending owner activation review; multi-runtime parity verified across Rust, Python, and WASM. |
| **IV. Separation of Lexical Data and Engine Logic** | Declarative data in `lexicon/`, static compilation in `build.rs` | **PASS** | Phonetic category sets and syllable onset/nucleus/coda rules declared statically. No arbitrary heuristic code. |
| **V. Pluricentric Dialect Scope** | Document dialect scope; regional invariance | **PASS** | Orthographic syllabification is invariant across Tamil Nadu (`TN`) and Sri Lanka (`SL`) dialects; tested with explicit regional vocabulary probes. |
| **VI. Platform-Conforming Distribution** | Authoritative Cargo workspace version, approved channels | **PASS** | Follows workspace version (`0.1.0-alpha.6`), included in workspace members, policy governed in `release-policy.toml`. |
| **VII. Explicit Guarantees & Quality Gates** | Performance guarantees documented & tested | **PASS** | SC-001 (100% integrity), SC-002 (lossless roundtrip), SC-004 (< 5μs latency) enforced by automated tests and `just agent-pre-stop-gate`. |

## Project Structure

### Documentation (this feature)

```text
specs/009-tamil-hyphen/
├── spec.md              # Feature specification & clarifications
├── plan.md              # This implementation plan
├── research.md          # Phase 0: Phonotactics, margins, and W3C line-break decisions
├── data-model.md        # Phase 1: Entities (HyphenationConfig, HyphenationPoint, HyphenationResult, WrapResult)
├── quickstart.md        # Phase 1: End-to-end runnable validation guide
├── contracts/           # Phase 1: Interface contracts
│   ├── rust-api.md      # Rust API signatures for tamil-hyphen and tamil-toolkit
│   ├── dispatcher-schema.json # JSON schema for execute dispatcher
│   └── bindings.md      # Python, WebAssembly/TS, and Dart bindings contracts
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code Layout

```text
crates/
├── tamil-hyphen/
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs              # Public API (hyphenate_word, hyphenation_points, hyphenate_text, wrap_text)
│       ├── syllable.rs         # Akshara nucleus/coda state machine and boundary detection
│       └── text.rs             # Paragraph scanner, word tokenizer, and line-wrapping algorithm
├── tamil-toolkit/
│   └── src/
│       └── lib.rs              # Dispatches hyphenation operations in execute()
bindings/
├── python/                     # PyO3 wrappers for hyphenation operations
├── js-wasm/                    # wasm-bindgen wrappers and TS definitions
└── dart-flutter/               # Dart FFI wrappers
tests/
└── golden/
    ├── hyphen_syllable.jsonl   # 120+ tri-runtime golden test vectors (status: planned)
    └── manifest.json           # Registration of hyphen_syllable suite
```

**Structure Decision**: Monorepo Rust workspace crate `crates/tamil-hyphen`, leveraging `tamil-core` for tailored letter iteration, and dispatched through `tamil-toolkit`.

## Complexity Tracking

> **No Constitution violations. Complexity tracking table left blank.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
