# Implementation Plan: Canonical Prosodic & Syllabic Tamil Hyphenation Rules (`015-canonical-tamil-hyphenation`)

**Branch**: `[015-canonical-tamil-hyphenation]` | **Date**: 2026-11-08 | **Spec**: [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/015-canonical-tamil-hyphenation/spec.md)

**Input**: Feature specification from `/specs/015-canonical-tamil-hyphenation/spec.md`

## Summary

Upgrade the Tamil hyphenation engine across `crates/tamil-hyphen`, `tests/golden/hyphen.jsonl`, Python/WASM bindings, `integrations/office-word-addin`, and `playground` to enforce the **5-step Tamil *Asai* (`நேரசை` / `நிரையசை`) + 3-letter minimum segment algorithm (`left_min = 3, right_min = 3, min_word_letters = 6`)**. This eliminates all false breaks on short words ($< 6$ tailored Tamil letters like `உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `அறிவியல்`) and prevents 2-letter orphan suffixes (`-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`) from wrapping onto the next line.

## Technical Context

**Language/Version**: Rust (2021 edition, stable MSRV), TypeScript 5.x (Playground), JavaScript ES2020 (Office Word Add-in), Python 3.11+ (PyO3 bindings)

**Primary Dependencies**: `tamil-core` (tailored Tamil letter segmentation & inspection), `tamil-norm` (Unicode NFC normalization), `serde`, `quick-xml` / `zip` (DOCX processing)

**Storage**: Declarative JSONL golden vectors in `tests/golden/hyphen.jsonl`

**Testing**: `cargo test -p tamil-hyphen`, `just test-rust`, `just test-parity`, Node.js verification for `integrations/office-word-addin/engine.js`

**Target Platform**: Rust native library, Python (`PyO3`), WebAssembly (`wasm-bindgen`), Next.js Playground, and Microsoft Word Desktop/Web Add-in (`Office.js`)

**Project Type**: Multi-runtime linguistic library + web playground + Office Word Add-in

**Performance Goals**: Zero-regression $O(N)$ linear pass per word; $< 50\text{ ms}$ per 1,000-word document in both Rust and JS engines

**Constraints**: Deterministic, dictionary-free rule execution; `#![forbid(unsafe_code)]` in `crates/tamil-hyphen`; preserve `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`); idempotent stripping of pre-existing `\u00AD` / `<w:softHyphen/>`

**Scale/Scope**: Core `crates/tamil-hyphen` module, `tests/golden/hyphen.jsonl` (114+ golden vectors), Python/WASM bindings, `integrations/office-word-addin`, and `playground`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evaluation |
|-----------|--------|------------|
| **I. Rust Owns Linguistic Behavior** | **PASS** | `crates/tamil-hyphen` implements the canonical 5-step Tamil *Asai* algorithm; Python/WASM bindings delegate to Rust; standalone Office Add-in & Playground JS/TS engines mirror the exact 5-step specification. |
| **II. Inspect Tamil by Scalars** | **PASS** | Uses `tamil_core::Letters` and explicit Unicode scalar checks (`\u{0BCD}`, `\u{0B83}`, `\u{200C}`, `\u{200D}`); all golden vectors in `tests/golden/hyphen.jsonl` are Unicode-escaped. |
| **III. Golden Vectors Precede Implementation** | **PASS** | `tests/golden/hyphen.jsonl` defines all expected break points and segments across `ta-IN` and `ta-LK` words and is verified across Rust, Python, and WASM. |
| **IV. Separation of Lexical Data and Engine Logic** | **PASS** | Purely orthographic/prosodic *Asai* state machine with no embedded ad-hoc word lists in code. |
| **V. Pluricentric Dialect Scope & Regional Invariance** | **PASS** | Explicitly declared dialect-invariant (`ta-IN` and `ta-LK`) in `FR-006`, backed by Tamil Nadu and Sri Lankan test vectors (`யாழ்ப்பாணம்`, `மட்டக்களப்பு`, `திருச்சிராப்பள்ளி`, `கோயம்புத்தூர்`). |
| **VI. Platform-Conforming Distribution** | **PASS** | Preserves all crate/package names and `release-policy.toml` rules. |
| **VII. Explicit Guarantees & Rigorous Quality Gates** | **PASS** | All quality gates (`just check-unicode`, `just test-rust`, `just test-parity`) enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/015-canonical-tamil-hyphenation/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── hyphenation-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
crates/tamil-hyphen/
├── src/
│   ├── lib.rs           # Public exports
│   ├── syllable.rs      # 5-step Tamil Asai + minimum segment partitioning
│   ├── types.rs         # HyphenationConfig & DicHeader defaults (left_min = 3, right_min = 3)
│   ├── text.rs          # Paragraph hyphenation & line wrapping
│   ├── dic.rs           # Hunspell/TeX .dic pattern generation
│   └── docx.rs          # OpenXML DOCX soft-hyphen processing
└── tests/               # Crate unit & golden tests

bindings/
├── python/              # PyO3 wrapper defaults (left_min = 3, right_min = 3)
└── js-wasm/             # wasm-bindgen wrapper defaults (left_min = 3, right_min = 3)

integrations/office-word-addin/
├── engine.js            # Standalone JS 5-step Tamil Asai + OOXML healer
├── commands.js          # Ribbon one-click hyphenate (leftMin = 3, rightMin = 3)
├── taskpane.js          # Taskpane UI handler (leftMin = 3, rightMin = 3)
├── index.html           # Taskpane inputs (default value="3")
├── commands.html        # Cache-busted ?v=5 script references
└── manifest.xml         # Add-in manifest v1.5.0.0

playground/
└── src/
    ├── lib/engine.ts    # TypeScript 5-step Tamil Asai engine
    └── components/public-tools/HyphenatorTool.tsx

tests/golden/
└── hyphen.jsonl         # Canonical golden test vectors (Unicode-escaped)

docs/specs/
└── hyphen.md            # Module specification document
```

**Structure Decision**: Multi-target monorepo update spanning `crates/tamil-hyphen`, `bindings/{python,js-wasm}`, `tests/golden/hyphen.jsonl`, `docs/specs/hyphen.md`, `integrations/office-word-addin`, and `playground`.

## Complexity Tracking

No constitution violations — table omitted.
