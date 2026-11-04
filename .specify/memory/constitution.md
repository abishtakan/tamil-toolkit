<!--
Sync Impact Report
- Version change: 0.0.0 (uninitialized template) -> 1.0.0
- Ratification Date: 2026-10-31
- Last Amended Date: 2026-11-05
- Principles defined:
  1. I. Rust Owns Linguistic Behavior (Single Source of Truth)
  2. II. Inspect Tamil by Scalars (No Visual Guesses)
  3. III. Golden Vectors Precede Implementation (Tri-Runtime Parity)
  4. IV. Separation of Lexical Data and Engine Logic
  5. V. Pluricentric Dialect Scope & Regional Invariance
  6. VI. Platform-Conforming Distribution & Policy-Governed Releases
  7. VII. Explicit Guarantees & Rigorous Quality Gates
- Added sections:
  - Technology Stack & Multi-Runtime Architecture
  - Quality Gates & Verification Workflow
- Governance:
  - Formalized amendment procedure, semantic versioning policy, and compliance review rules.
- Follow-up TODOs: None.
-->

# tamil-toolkit Constitution

## Core Principles

### I. Rust Owns Linguistic Behavior (Single Engine Source of Truth)
All core algorithms, tokenization, orthographic logic, collation, transliteration, and numeric/calendar operations MUST reside in `crates/tamil-*`. Python, TypeScript/WebAssembly, and Dart packages MUST act as thin serialization and FFI wrappers around the compiled Rust engine. No adapter or external tool may implement duplicate or secondary Tamil processing logic; all consumers and test harnesses MUST use the same unified Rust dispatcher.

### II. Inspect Tamil by Scalars (No Visual Guesses)
Character boundaries, grapheme cluster composition, and invisible code points MUST NEVER be inferred from rendered or visually presented text. Inspection MUST be performed using scalar-level tools (such as the `tamil-oracle` MCP tool `inspect_tamil_string` / `inspect_codepoints`) or explicit hexadecimal Unicode escape sequences (`\u{0B85}`). All golden test cases and declarative datasets MUST keep non-ASCII Tamil sequences escaped and auditable. Systems and transformations MUST NEVER silently drop or alter invisible format controls such as Zero-Width Joiner (ZWJ, U+200D) or Zero-Width Non-Joiner (ZWNJ, U+200C).

### III. Golden Vectors Precede Implementation (Test-First & Tri-Runtime Parity)
Every linguistic behavior and feature MUST be defined by sourced test vectors in `tests/golden/<module>.jsonl` before implementing the underlying algorithms. Active golden test cases MUST execute and pass identically without mocks across Rust, Python, and WebAssembly runtimes. Experimental or planned suites MUST remain explicitly categorized as planned and MUST NEVER be counted as passing in release metrics.

### IV. Separation of Lexical Data and Engine Logic
Lexicon databases, affix lists, font encoding tables, and grammatical rules MUST be stored declaratively in `lexicon/*.toml` or CSV format with explicit bibliographic sourcing and licensing documentation. Code generators in `build.rs` compile this declarative data into immutable static tables, tries, or finite-state transducers (FST). No executable logic is permitted in `lexicon/`, and linguistic rules (such as Punarchi transformations) MUST NEVER be hallucinated or approximated without authoritative citation.

### V. Pluricentric Dialect Scope & Regional Invariance
Tamil is a pluricentric language with established regional varieties across Tamil Nadu (TN) and Sri Lanka (SL) (including Jaffna, Batticaloa, Vanni, and Up-Country). Specifications MUST explicitly declare their target dialect scope. Operations that are phonetically or orthographically invariant across regional dialects MUST demonstrate test-backed dialect invariance.

### VI. Platform-Conforming Distribution & Policy-Governed Releases
Distribution packages MUST adhere to the native naming conventions of their respective package registries (`tamil-*` for crates.io and npm; `tamil_*` for PyPI and Dart pub; `pg_tamil` for PostgreSQL extensions). Cargo's workspace version represents the single authoritative release number. Only approved packages and release channels defined in `release-policy.toml` may be published, and publication MUST occur strictly through reviewed, manual release workflows.

### VII. Explicit Guarantees & Rigorous Quality Gates
Performance, memory allocation, and linguistic coverage guarantees MUST be documented accurately and tested continuously. Core iteration over borrowed slices MUST remain zero-allocation, whereas normalization, string transformations, and FFI boundaries allocate as documented. Passing baseline suites MUST NOT be represented as comprehensive linguistic coverage. All automated quality gates (`just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just test-rust`, `just test-parity`, `just agent-pre-stop-gate`) MUST pass completely before integration.

## Technology Stack & Multi-Runtime Architecture

- **Core Engine**: Rust workspace targeting Modern Stable Rust (MSRV strictly maintained across crates in `crates/tamil-*`).
- **Foreign Function Interface (FFI)**:
  - Python bindings via PyO3 (`bindings/python`) with stub generation.
  - WebAssembly bindings via `wasm-bindgen` (`bindings/js-wasm`) targeting both Node.js (CommonJS/ESM) and browser Web environments.
  - Dart bindings via C ABI (`bindings/dart`).
- **Data Compilation**: Build-time compilation of declarative TOML/CSV lexicons into static byte tables and minimal FSTs using `build.rs`.
- **Developer Workbench**: Interactive web environment in `workbench/` powered by Vite, TypeScript, and the browser WASM package for live manual and visual verification.

## Quality Gates & Verification Workflow

1. **Specification & Golden Vectors**: Create or update the module specification (`docs/specs/*.md`) and add sourced golden test cases (`tests/golden/*.jsonl`).
2. **Implementation & Binding Sync**: Implement algorithm in Rust, run `just test-rust`, rebuild bindings (`just sync-bindings`), and verify tri-runtime parity (`just test-parity`).
3. **Data Synchronization**: Synchronize distribution data and license copies from canonical sources via `just sync-release-files`; verify with `just check-release-files`.
4. **Pre-Stop Gate Verification**: Before committing or concluding any implementation task, execute `just agent-pre-stop-gate` (enforcing formatting, clippy, Unicode integrity, schema conformance, and multi-runtime parity).
5. **Context & Handoff Preservation**: Maintain operational status in `docs/status.md` and log public interface modifications in `CHANGELOG.md`.

## Governance

This Constitution supersedes all informal practices and serves as the non-negotiable architectural and linguistic foundation for `tamil-toolkit`.

1. **Compliance Review**: All pull requests, code modifications, and agent executions MUST strictly satisfy the Core Principles and pass all designated Quality Gates.
2. **Amendment Procedure**:
   - Proposed amendments MUST be documented with a detailed rationale and impact analysis.
   - Any modification or removal of an established principle constitutes a MAJOR version bump.
   - Additions of new principles or material expansions of operational guidance constitute a MINOR version bump.
   - Clarifications, non-semantic wording adjustments, and typography corrections constitute a PATCH version bump.
3. **Guidance References**: Runtime agent execution and role delegation MUST consult `AGENTS.md`, `CLAUDE.md`, and `docs/development.md`.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-11-05
