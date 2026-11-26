# Implementation Plan: Tamil Sandhi (`tamil-punarchi` — Complete Nannūl Eḻuttatikāram 117 Sūtras)

**Branch**: `master` (`025-tamil-punarchi`) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification [spec.md](spec.md), 107-sūtra locator digest [docs/specs/punarchi-source-notes.md](../../docs/specs/punarchi-source-notes.md), and exhaustive 117-sūtra primary-source research under [specs/025-tamil-punarchi/research/](research/05-precedence-and-inverse-matrix.md).

## Summary

Implement the Rank 2 Rust crate `crates/tamil-punarchi` (`#![forbid(unsafe_code)]`, depending only on `tamil-core` and `tamil-norm`) providing complete, traceable coverage of all **117 *Nannūl Eḻuttatikāram* sūtras** (**10 mandatory prerequisites**: `93–94`, `102–108`, `136` + **107 Puṇariyal sūtras**: `151–257`) under the named `nannool-v1` profile. Canonical declarative TOML tables under `lexicon/` account for all 117 sūtras across five chapters and five computational tiers and compile at build time via `build.rs` into immutable static tables. A bounded 4-stage compositional pipeline with strict intra-stage sub-ordering (`1A→1B→1C`, `Stage 2` left-to-right multi-segment *Chariyai* fold, `3A→3B→3C→3D`, `Stage 4`) executes forward word joining (`punarchi_join`) with full sūtra traces, two-level grammatical context (`PunarchiContext`), deterministic primary selection plus labeled `alternatives`, and opt-in closed poetic rules. A dictionary-free reverse analyzer (`punarchi_split_candidates`) generates bounded single-boundary two-part split candidates covering all 28 reversible surface patterns (including all 12 `237`-interaction clusters/singletons), dual-pruned by *Nannūl* `102–108` phonotactics and forward-join verification.

## Technical Context

**Language/Version**: Rust 1.95 workspace toolchain (edition 2021, MSRV 1.85); existing Python 3.11+ (PyO3), TypeScript/WASM (Node + browser), and Dart C ABI bindings.
**Primary Dependencies**: `tamil-core` (written units `Letters`, `split_uyirmei`/`compose_uyirmei`, phonological quantity `classify_quantity`), `tamil-norm` (`normalize_nfc`), and workspace `serde` / `toml` / `unicode-normalization` (build-time). Zero runtime external dictionary dependencies; zero `unsafe` code.
**Storage**: Canonical declarative TOML tables (`lexicon/punarchi-nannool-inventory.toml` and `lexicon/punarchi-nannool.toml`) compiled by `crates/tamil-punarchi/build.rs` into static Rust slices in `OUT_DIR`; pinned source URLs & SHA-256 manifest in [tests/reference/punarchi-nannool/sources.json](../../tests/reference/punarchi-nannool/sources.json); escaped golden vectors in `tests/golden/punarchi_nannool.jsonl`.
**Testing**: Build-time schema/inventory completeness checks (all 117 sūtras `93–94, 102–108, 136, 151..=257`), chapter-grouped golden tests (`prereq`, `uyireeru`, `meyyeeru`, `urupu`, `split`), 10,000-case `proptest` round-trip and boundary-integrity suites, preactivation multi-runtime parity (Rust, Python, Node/Browser WASM, Dart), and isolated archive consumer checks.
**Target Platform**: Native Rust, Python `abi3` wheels, Node & Browser WebAssembly (`wasm32-unknown-unknown`), and Dart host C ABI.
**Project Type**: Workspace Rank 2 library crate + unified `tamil-toolkit` dispatcher & multi-language adapter integration.
**Performance Goals**: Zero runtime TOML/file parsing (static compiled tables); single-pass `tamil_core::Letters` indexing per call; bounded 4-stage acyclic forward evaluation and bounded dual-pruned single-boundary reverse candidate generation (`<= 256` UTF-8 bytes surface cap); measure and record observed latencies before release.
**Constraints**: Offline deterministic execution; strict Rank 2 acyclic DAG (depends only on `tamil-core` Rank 0 and `tamil-norm` Rank 1); no dependency on `tamil-lexicon` or dictionary packs; never blend *Nannūl* with *Tolkāppiyam*; preserve non-Tamil and `ZWJ`/`ZWNJ` boundary barriers verbatim as *Iyalbu*; no copying of copyrighted modern commentary prose.
**Scale/Scope**: 117 sūtras (`93–94, 102–108, 136, 151–257`), 3 dispatcher operations (`punarchi_join`, `punarchi_split_candidates`, `punarchi_rules`), 1 initial grammar profile (`nannool-v1`), 4-stage ordered forward pipeline + 28-pattern dual-pruned reverse analyzer.

## Constitution Check

*GATE: Evaluated before Phase 0 research and re-checked post exhaustive R0–R4 primary-source audit.*

| Principle | Pre-Design Gate | Post-Audit Verification |
| --- | --- | --- |
| **I. Rust owns linguistic behavior** | All Sandhi joining, context disambiguation, and reverse candidate generation live in `crates/tamil-punarchi`. | Verified: Python, JS/WASM, and Dart adapters strictly serialize/deserialize `punarchi_join`, `punarchi_split_candidates`, and `punarchi_rules` through `tamil_toolkit::execute` ([contracts/punarchi.md](contracts/punarchi.md)). |
| **II. Inspect Tamil by scalars** | Golden JSONL stays escaped; canonical `lexicon/*.toml` uses uniform readable NFC UTF-8 Tamil with detached marks/controls escaped; never silently strip `ZWJ`/`ZWNJ`. | Verified: `build.rs` validates NFC; `just check-unicode` enforces TOML/JSONL escaping; boundary `ZWJ`/`ZWNJ` triggers verbatim *Iyalbu* passthrough (`FR-008`). |
| **III. Golden vectors precede implementation** | Author sourced escaped vectors in `tests/golden/punarchi_nannool.jsonl` (`planned`) per chapter before algorithms, tagged with verified `viruttiyurai_pno` / `kandigai` witnesses. | Verified: all 117 sūtras have verified witness-tagged examples in `research/00..03*.md`; `punarchi_nannool.jsonl` stays `planned` through preactivation parity and activates only after owner review. |
| **IV. Separate lexical data and engine** | All 117 sūtra metadata, closed-class stems, 17 *Chariyais*, case suffixes, and rules live in `lexicon/*.toml` with pinned provenance; `build.rs` compiles static tables. | Verified: `lexicon/punarchi-nannool-inventory.toml` and `lexicon/punarchi-nannool.toml` contain zero executable code; `tests/reference/punarchi-nannool/sources.json` pins URLs and checksums without copying commentary prose. |
| **V. Pluricentric dialect scope & invariance** | Label `nannool-v1` explicitly as classical literary grammar shared across TN and SL; test regional invariance without claiming modern colloquial coverage. | Verified: cross-check of TVA 1999 *Viruttiyurai* (TN) and Āṟumuka Nāvalar *Kāṇṭikaiyurai* (Jaffna/SL) confirms 100% rule agreement (`COMMON`). |
| **VI. Platform-conforming & policy-governed releases** | `tamil-punarchi` starts private (`publish.workspace = true`), Rank 2 in `tools/release_policy.py`; public allowlist & facade wiring require separate review. | Verified: Isolated preactivation worktree validates multi-runtime parity first; `release-policy.toml`, `tools/release_files.py`, and `publish-crate.yml` update only upon explicit release-scope approval. |
| **VII. Explicit guarantees & quality gates** | Document actual scope limits (meta/metrical `151–156`, usage `239`, Phase 16 syntactic *Valimigum*/*Valimigaa*, no lexical ranking); run 10,000-case properties and full canonical gates. | Verified: [quickstart.md](quickstart.md) enforces standalone properties, `just agent-pre-stop-gate`, `just test-dart`, and isolated `default`-profile archives. |

**Gate Result:** PASS — zero constitution violations or exceptions.

## Project Structure

### Documentation (this feature)

```text
specs/025-tamil-punarchi/
├── spec.md                                     # Feature specification + 5 clarifications (117 sūtras)
├── plan.md                                     # This file
├── research.md                                 # Synthesized architectural decisions
├── data-model.md                               # Declarative TOML schemas & runtime entities
├── quickstart.md                               # End-to-end validation commands
├── contracts/
│   └── punarchi.md                             # Unified dispatcher & multi-language API contract
├── checklists/
│   └── requirements.md                         # Spec quality checklist (16/16 passing)
└── research/
    ├── 00-prerequisites-eluttiyal-padaviyal.md # Sūtras 93–94, 102–108, 136
    ├── 01a-uyireeru-151-177.md                 # Sūtras 151–177
    ├── 01b-uyireeru-178-203.md                 # Sūtras 178–203
    ├── 02-meyyeeru-204-239.md                  # Sūtras 204–239
    ├── 03-urupu-240-257.md                     # Sūtras 240–257
    ├── 04-cross-book-and-edge-cases.md         # Witness diffs, Tolkāppiyam boundary & edge-case traps
    └── 05-precedence-and-inverse-matrix.md     # Formal precedence DAG, pipeline proof & 28-pattern inverse matrix
```

### Source Code & Canonical Data (repository root)

```text
tests/reference/punarchi-nannool/
└── sources.json                         # Pinned URLs, SHA-256 digest & license terms (link-only for TVA)

lexicon/
├── punarchi-nannool-inventory.toml      # Complete 117-sūtra (93–94, 102–108, 136, 151–257) inventory
└── punarchi-nannool.toml                # Closed-class stems, 17 Chariyais, case suffixes & ordered rules

tests/golden/
├── punarchi_nannool.jsonl               # Sourced escaped golden vectors (initially planned)
└── manifest.json                        # Suite status, operations & review reason

tools/
└── generate_punarchi_golden.py          # Programmatic golden-vector compiler & offset/provenance checker

crates/tamil-punarchi/
├── Cargo.toml                           # Rank 2 crate (tamil-core, tamil-norm, serde)
├── build.rs                             # Validates 117/117 inventory & compiles static tables
├── src/
│   ├── lib.rs                           # Public API re-exports (#![forbid(unsafe_code)])
│   ├── tables.rs                        # Included OUT_DIR static tables & lookup helpers
│   ├── context.rs                       # PunarchiProfile, PunarchiChapter, PunarchiContext, validation
│   ├── phonology.rs                     # Sūtra 94 6-class Kurriyalugaram vs Mutriyalugaram, 93, 102–108, 205
│   ├── closed_class.rs                  # Stage 1: Panpuppeyar 136, numerals 188–199, directions 186, pronouns 247, 183–185
│   ├── urupu.rs                         # Stage 2: 17 Chariyais, multi-segment fold, உம் post-position, 240–257 filters
│   ├── uyireeru.rs                      # Stage 3: 163/162/164/165 & blockers (158–203)
│   ├── meyyeeru.rs                      # Stage 3–4: 237 pre-mutation, 209–236 consonant rules, 205, 204 fusion
│   ├── pipeline.rs                      # 4-stage ordered joiner (BoundaryFlags, 3A->3B->3C->3D, dedup & sort)
│   └── split.rs                         # 28-pattern dual-pruned (102–108 + forward-verified) reverse analyzer
└── tests/
    ├── support/mod.rs                   # Standalone golden fixture loader
    ├── inventory_completeness.rs        # Verifies 117/117 sūtra accounting & rule linkage
    ├── prereq_golden.rs                 # Prerequisites (93–94, 102–108, 136) golden assertions
    ├── uyireeru_golden.rs               # Chapter 1 (151–203) golden assertions
    ├── meyyeeru_golden.rs               # Chapter 2 (204–239) golden assertions
    ├── urupu_golden.rs                  # Chapter 3 (240–257) golden assertions
    ├── context_ambiguity_golden.rs      # Context disambiguation, ambiguity alternatives & poetic gating
    ├── split_golden.rs                  # Reverse split, all 12 237-clusters & ambiguity assertions
    └── roundtrip_properties.rs          # 10,000-case proptest round-trip & integrity invariants

# Reviewed Integration Touchpoints (Preactivation Candidate -> Approved Integration)
crates/tamil-toolkit/{Cargo.toml,src/lib.rs}
tools/mcp-tamil-oracle/                  # Verifies oracle forwarding through tamil_toolkit::execute
tools/tasks.py                           # Wires generate_punarchi_golden.py --check into just check-unicode
bindings/python/python/tamil_toolkit/{__init__.py,__init__.pyi}
bindings/python/tests/test_golden.py
bindings/js-wasm/src/{api.ts,index.ts,web.ts}
bindings/js-wasm/tests/golden.test.ts
bindings/dart-flutter/lib/tamil_toolkit.dart
bindings/dart-flutter/test/golden_test.dart
release-policy.toml
tools/release_files.py
.github/workflows/publish-crate.yml
docs/specs/punarchi-nannool-v1.md        # Active module contract & verification record
docs/status.md
CHANGELOG.md
README.md
ROADMAP.md
```

**Structure Decision** — Keep all linguistic logic, phonology classification (Sūtras `93–94`, `102–108` built over `tamil-core`), ordered 4-stage forward pipeline (`BoundaryFlags`, `3A→3B→3C→3D`), and dual-pruned 28-pattern reverse analyzer inside `crates/tamil-punarchi` (Rank 2). Keep all 117 sūtra records, closed-class word sets, *Chariyais*, and rule tables declarative in `lexicon/`. Keep the crate private until chapter-by-chapter verification and preactivation multi-runtime parity complete, then promote via reviewed activation and release-policy updates.

## Phased Delivery Order

1. **Phase 10A — 117-Sūtra Inventory & Foundational Phonology (`93–94, 102–108, 136`):** Author the complete 117-sūtra `lexicon/punarchi-nannool-inventory.toml` (with all 12 verified `edition_note` entries) and schema skeleton `lexicon/punarchi-nannool.toml` using pinned `tests/reference/punarchi-nannool/sources.json`. Implement `build.rs`, `context.rs`, `phonology.rs` (exact Sūtra 94 6-class *Kurriyalugaram* vs *Mutriyalugaram* decision tree, Sūtra 93 *Kurriyaligaram*, Sūtras `102–108` *Mozhi-muthal*/*Mozhi-eetru* validators, Sūtra 205 *Thanikkuril*), Stage 1A *Panpuppeyar* (`136`), and verify `inventory_completeness.rs` + `prereq_golden.rs`.
2. **Phase 10B — Chapter 1 (*Uyirīṟṟup Puṇariyal* `151–203`) & Pipeline Core:** Implement `pipeline.rs` (`BoundaryFlags`, left-to-right folding, `3A→3B→3C→3D` sub-ordering) and populate Chapter 1 declarative rules & closed classes (`158–161`, `162–163`, `164`, `165–167`, `168–178`, `179–185` with `183–185` in Stage 1C, directions `186–187`, numerals `188–199`, `200–203`, opt-in closed poetic rules `163.3/172.1/173/180`) plus witness-backed escaped golden vectors before code. Verify `uyireeru_golden.rs`.
3. **Phase 10C — Chapter 2 (*Meyyīṟṟup Puṇariyal* `204–239`):** Populate Chapter 2 declarative rules & closed classes (`237` in Stage 3B before `209–210`/`227–229` in Stage 3C producing all 12 surface patterns and blocking `*ல்த/*ள்த` per `117`; `204–205`, optional minority `206`, `207–208`, named exceptions `211–218`, `ம்` `219–223`, `ய்/ர்/ழ்` `224–226`, `ல்/ள்` `227–234`, `வ்` `235–236`, `238` delegation) and golden vectors. Verify `meyyeeru_golden.rs`.
4. **Phase 10D — Chapter 3 (*Urupu Puṇariyal* `240–257`) + 28-Pattern Dual-Pruned Reverse Split + Properties:** Populate all 17 *Chariyais*, multi-segment folding (`அற்று+இன்`, `அத்து+இன்+உ`, `வ்+இன்+உ`, `அன்+உ`, `ன்+அ`), `உம்` post-positioning (`245–246`), pronoun/demonstrative/decade rules (`247–251`, `257` `எவ்→எவற்றை`), `252` (`அத்தின் அகரம்` in `3A`), `247.5`/`250.3` anti-gemination, `254`/`242.2` filters, and implement `split.rs` (28-pattern inverse matrix + `102–108` phonotactics + forward-verification pruning). Verify `urupu_golden.rs`, `split_golden.rs`, and 10,000-case `roundtrip_properties.rs`.
5. **Phase 10E — Preactivation Candidate, Owner Review & Integration:** Wire `tamil-toolkit` dispatcher and Python/WASM/Dart adapters in an isolated candidate worktree, verify all planned vectors across all 4 real runtimes, present readable Tamil fixture review for owner approval (activation + release policy), then integrate, sync release files, run `just agent-pre-stop-gate`, `just test-dart`, and isolated `default`-profile archive verification.

## Complexity Tracking

No constitution violations to justify. The 117-sūtra inventory, ordered 4-stage pipeline (`BoundaryFlags` + `3A→3B→3C→3D`), and dual-pruned 28-pattern inverse analyzer directly encode *Nannūl Eḻuttatikāram*'s own verified rule dependencies without introducing extra crates or runtime dependencies.
