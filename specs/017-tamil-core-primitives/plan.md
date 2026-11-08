# Implementation Plan: Phase 1 — Tamil Core Phonological & Nucleus Primitives (`017`)

**Branch**: `017-tamil-core-primitives` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/017-tamil-core-primitives/spec.md`

## Summary

Implement foundational phonological and syllable nucleus primitives in `crates/tamil-core` (`Rank 0`):
1. **Quantity & Duration**: Letter weight enum (`LetterQuantity`: `Kuril`, `Nedil`, `Mei`, `Aytham`, `Other`), duration measurement struct (`Maathirai`: 1.0, 2.0, 0.5, 0.0), and direct predicates (`is_kuril`, `is_nedil`, `is_mei`/`is_otru`, `is_aytham`).
2. **Cognate Harmony (*Ina Ezhuthu*)**: Sourced bidirectional mapping for Vallinam-Mellinam consonant stop-nasal pairs and short-long vowel pairs per *Tolkappiyam* & *Nannool*, supporting composite *Uyirmei* diacritic preservation.
3. **Phonetic Syllable Nucleus (*Olippasai*)**: Zero-allocation iterator grouping vowel nuclei with onset clusters (including loanword initial clusters like `ஸ்டார்`) and trailing coda consonants/Aytham markers with byte and letter span offsets.
4. **Golden Parity**: Author active, escaped test vectors in `tests/golden/core_phonology.jsonl` and wire into `tests/golden/manifest.json`.
5. **Multi-Runtime Exposure**: Expose primitives through `tamil-toolkit` dispatcher and update Python/WASM bindings.

## Technical Context

**Language/Version**: Modern Stable Rust (MSRV 1.80+), Python 3.11–3.14, Node.js 20/22/24 (WASM).

**Primary Dependencies**:
- Core: `unicode-segmentation = "1.12"`, `unicode-normalization = "0.1"`, `serde = { version = "1.0", features = ["derive"] }` (all already present in `tamil-core`). Zero new dependencies.
- Bindings: `pyo3 = "0.22"`, `wasm-bindgen = "0.2"`.

**Storage**: N/A (in-memory algorithms & declarative lookup tables).

**Testing**: `cargo test -p tamil-core`, `uv run pytest tests/harness/`, tri-runtime parity test harness.

**Target Platform**: Multi-platform: Native (Windows, Linux, macOS), WebAssembly (Node.js & browser), Python wheels, Flutter/Dart C ABI.

**Project Type**: Core systems library (`crates/tamil-core`), FFI bindings, and CLI/dispatcher integration.

**Performance Goals**:
- Letter classification & mora lookup: < 10 nanoseconds per letter.
- Syllable nucleus segmentation: Zero-allocation iteration over borrowed string slices (`&'a str`), processing > 50,000 words/sec.

**Constraints**:
- `Rank 0` invariant: Zero internal dependencies on any other `tamil-*` crates.
- `#![forbid(unsafe_code)]` across all Rust source files.
- Absolute preservation of format controls (`ZWJ`, `ZWNJ`), punctuation, and whitespace byte offsets.

**Scale/Scope**:
- 247 primary Tamil characters + recognized Grantha extensions.
- 6 consonant cognate pairs + 7 vowel cognate pairs.
- ~100 active golden vectors in `tests/golden/core_phonology.jsonl`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check Description | Status | Evidence / Compliance |
|---|---|---|---|
| **I. Rust Owns Linguistic Behavior** | Single engine source of truth in `crates/tamil-core`. No duplicate logic in JS/Python. | **PASS** | Implemented strictly in `crates/tamil-core/src/phonology.rs` and `olippasai.rs`. Adapters use FFI / JSON dispatcher. |
| **II. Inspect Tamil by Scalars** | No visual regex guesses; inspect via Unicode scalars and escaped sequences. Format controls preserved. | **PASS** | Built on existing tailored `Letters` iterator and scalar tables; ZWJ/ZWNJ preserved in syllable spans. |
| **III. Golden Vectors Precede Implementation** | Sourced test vectors in `tests/golden/*.jsonl` before algorithm signoff. Tri-runtime parity. | **PASS** | Authoring `tests/golden/core_phonology.jsonl` with escaped Unicode; tested against Rust, Python, WASM. |
| **IV. Separation of Lexical Data and Engine Logic** | Sourced grammatical rules (*Tolkappiyam*, *Nannool*) stored declaratively. | **PASS** | Cognate tables and mora constants defined declaratively with authoritative literature citations. |
| **V. Pluricentric Dialect Scope** | Tamil phonological quantities and cognate pairs are regional-invariant. | **PASS** | Quantity and cognate harmony are invariant across all TN and SL regional dialects. |
| **VI. Platform-Conforming Distribution** | Cargo workspace version authority; policy-governed release. | **PASS** | `tamil-core` is `Rank 0` published crate; zero circular edges or out-of-rank dependencies. |
| **VII. Explicit Guarantees & Quality Gates** | Zero-allocation iteration over borrowed slices; passes `just agent-pre-stop-gate`. | **PASS** | `OlippasaiIter<'a>` yields `Olippasai<'a>` with borrowed `&'a str` and usize indices; zero heap allocation. |

## Project Structure

### Documentation (this feature)

```text
specs/017-tamil-core-primitives/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (resolved design questions & sourcing)
├── data-model.md        # Phase 1 output (entities, fields, invariants)
├── quickstart.md        # Phase 1 output (runnable verification scenarios)
├── contracts/
│   └── core-primitives-contract.md # Phase 1 output (Rust, JSON, adapter APIs)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
crates/tamil-core/
├── src/
│   ├── lib.rs           # Re-exports phonology and olippasai primitives
│   ├── phonology.rs     # LetterQuantity, Maathirai, is_kuril, cognate mapping
│   ├── olippasai.rs     # Zero-allocation syllable nucleus iterator & span types
│   └── tables.rs        # Static phonological lookup tables (if needed)
└── tests/
    ├── phonology_tests.rs
    └── olippasai_tests.rs

crates/tamil-toolkit/
├── src/
│   └── dispatcher.rs    # Core domain actions: core.classify_letter, core.get_cognate, core.segment_olippasai

tests/golden/
├── core_phonology.jsonl # Active escaped golden test vectors
└── manifest.json        # Suite registration ("active")

bindings/
├── python/src/          # Python FFI bindings
└── js-wasm/src/         # WASM bindings
```

**Structure Decision**: Multi-crate workspace. Primitives reside in `crates/tamil-core` (`Rank 0`), exposed via `crates/tamil-toolkit` (`Rank 5`), and wrapped in `bindings/*` (`Rank 6`).

## Complexity Tracking

> Zero constitution violations; no complexity exceptions required.
