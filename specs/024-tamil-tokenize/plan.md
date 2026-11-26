# Implementation Plan — Tamil Word and Sentence Tokenization

**Branch** `master` · **Feature** `024-tamil-tokenize` · **Date** 2026-11-26

**Input** [Feature specification](spec.md) and [module contract](../../docs/specs/tokenize-v0.1.md)

## Summary

Implement a Rank 2 Rust crate that returns original-text word and sentence spans. Tailor the Unicode 17 baseline around the existing Tamil written units and reviewed abbreviations. Compile opt-in stopword profiles from reviewed source data. Verify shared fixtures and a manually annotated Tamil Nadu and Sri Lankan corpus. Expose the operations through the existing dispatcher and bindings. The [research](research.md) records the Unicode probes and the choice to keep model inference, subword encoders, and model-budget chunking outside Phase 9.

## Technical Context

**Language and version** — Rust 1.95 workspace toolchain, edition 2021 and workspace MSRV 1.85. Existing Python 3.11+, TypeScript/WASM, and Dart bindings.

**Primary dependencies** — `tamil-core` for original written units, `tamil-norm` for NFC lookup, and the locked `unicode-segmentation` 1.13.3 for Unicode 17 word and sentence boundaries. Use workspace Serde and TOML for existing data and transport conventions.

**Storage** — Canonical abbreviation and stopword TOML and a compact Unicode property projection in `lexicon/`. Build-time immutable tables. Sources, pinned hashes, license evidence, raw Unicode break tests, and escaped JSONL fixtures follow existing repository layouts.

**Testing** — Unicode baseline conformance, exact annotated boundaries and false-break reporting by case group, standalone Rust fixture and property tests, real runtime parity, and reviewed archive verification. Exercise 10,000 cases per core source-integrity property.

**Target platforms** — Native Rust, PyO3, Node and browser-target WASM, and the Dart host C ABI. The oracle shares the Rust dispatcher.

**Project type** — Workspace library crate plus shared dispatcher integration.

**Performance goals** — Reuse one source unit index per call and bound abbreviation work to candidate forms and local context. Avoid whole-document normalization. Measure runtime and output size on long mixed-script text and punctuation-heavy input. Document observed costs and any dependency limits before publishing guarantees.

**Constraints** — Deterministic offline segmentation, original text and joiner preservation, no model payloads, and no dependence on optional dictionary packs. Follow the approved Rust dependency closure for integration.

**Scale and scope** — Two operations, three filtering profiles, and a small attested abbreviation inventory. Existing `tamil-punarchi` and `tamil-morph` scopes cover later morphological work.

## Constitution Check

| Principle | Before research | After design |
| --- | --- | --- |
| I. Rust owns linguistic behavior | One Rank 2 Rust engine and a shared dispatcher | Typed wrappers only serialize and deserialize the [same contract](contracts/tokenizer.md). |
| II. Inspect by scalars | Original offsets and exact scalar evidence | The data model preserves original UTF-8 and written-unit coordinates and uses explicit fixture exceptions for NFD and joiners. |
| III. Golden vectors precede implementation | Plan sourced fixtures before code | The staged workflow preserves planned status through preactivation verification and records active parity only after owner review. |
| IV. Separate lexical data and engine | Canonical data files carry sources and rights | `build.rs` validates and projects the reviewed entries. Release copies come from the existing sync tooling. |
| V. Pluricentric scope | Tamil Nadu and Sri Lanka share a profile | Corpus annotations distinguish regional usage witnesses from invariance. Coverage includes Jaffna, Batticaloa, Vanni, and Up-Country. |
| VI. Policy-governed releases | Rank 2 is registered and the new engine starts private | Reviewed activation and archive scope precede public facade integration. Publishing remains a separate manual action. |
| VII. Explicit guarantees and quality gates | Require exact slicing, bounded claims, and real runtimes | The quickstart distinguishes baseline probes, planned parity, and final integration and package gates. |

The design passes the constitution check. Fixture, runtime, and release acceptance require the implementation evidence listed in the [quickstart](quickstart.md).

## Project Structure

### Documentation

```text
specs/024-tamil-tokenize/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   └── tokenizer.md
└── quickstart.md
```

### Source and verification paths

```text
crates/tamil-tokenize/                 # New private engine and build-time tables
crates/tamil-toolkit/src/lib.rs        # Reviewed re-export and dispatcher integration
lexicon/tokenize-v0.1.toml             # Canonical abbreviation and stopword data
lexicon/tokenize-unicode-v17.toml      # Compact pinned property projection
tests/reference/unicode-17.0.0/        # Unicode baseline inputs and provenance
tests/golden/tokenize_v01.jsonl        # Shared reviewed cases, initially planned
tests/golden/manifest.json             # Suite status, reason, and operations
bindings/python/python/tamil_toolkit/ # Python wrappers and stubs
bindings/js-wasm/src/                  # Shared API and both entry points
bindings/dart-flutter/lib/             # Existing Dart dispatcher wrapper
tools/release_files.py                 # Generated archive copies and notices
release-policy.toml                    # Separately reviewed archive scope
```

**Structure decision** — The engine owns range calculation and profile behavior. The facade supplies the Rust re-export and dispatcher operations. The adapters retain their existing transports. Canonical data and verification fixtures remain outside runtime code. Archive-only copies are generated when packaging is reviewed.

## Delivery Order

1. **Evidence and fixtures** — Pin the Unicode 17 baseline data and provenance. Curate the proposed abbreviations and stopword groups with source rights and rationale. Create the escaped `tokenize_v01.jsonl` and register it as `planned` with a reason. Annotate words and sentences before engine implementation. Establish the raw baseline and the document-trimming policy used in the per-group error comparison.
2. **Private engine** — Add substantive Rank 2 `tamil-tokenize` code under the inherited private publication defaults. Compile the tables. Use the baseline offset iterators and original core unit boundaries. Apply abbreviation and whitespace tailoring before classification and filtering. Exercise the shared success rows against the engine in standalone Rust tests and check the source-span properties.
3. **Preactivation candidate** — In an isolated integration checkout wire the new dependency, dispatcher, and wrappers. Build real bindings and run the planned suite explicitly with the existing runners. Use their lower-level build and test commands because the standard release-policy gate excludes private dependencies from the public facade. Keep the provisional manifests out of the integration branch. Record planned counts, the regional boundary comparison, and any unresolved language evidence for review.
4. **Reviewed integration** — Obtain owner review for fixture activation and separate approval of release scope. Coordinate the allowlist entry before `tamil-toolkit`, inherited workspace pin, facade, bindings, generated archive files and notices, and explicit publisher inventory. Verify the actual candidate with the canonical gates and the isolated archive consumers before landing. Record acceptance evidence and limits. Registry upload remains a separate reviewed action.

The [data model](data-model.md) and [interface contract](contracts/tokenizer.md) define the design for task generation. There are no constitution exceptions.
