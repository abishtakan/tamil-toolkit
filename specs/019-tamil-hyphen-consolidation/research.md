# Research: tamil-hyphen Release Policy, Manifest & WASM Consolidation

## 1. tamil-hyphen Refactoring with tamil-core Phonological Primitives

### Decision
Refactor `crates/tamil-hyphen/src/syllable.rs` to import and utilize `tamil_core` phonological primitives:
- `tamil_core::is_aytham(s)`
- `tamil_core::is_mei(s)`
- `tamil_core::is_kuril(s)`
- `tamil_core::is_nedil(s)`
- `tamil_core::classify_quantity(s)`
- `tamil_core::split_uyirmei(s)`
- `tamil_core::get_olippasai(s)` / `tamil_core::olippasai_nuclei`

### Rationale
- `tamil-core` (Rank 0) was expanded in Phase 1 (`017-tamil-core-primitives`) to provide authoritative phonological classifications and raw sound unit (`Olippasai`) segmentation.
- `tamil-hyphen` (Rank 2) previously had ad-hoc string comparisons for pulli, aytham, and inspecting letters. Delegating to `tamil-core` eliminates code duplication and ensures phonological consistency across the workspace.
- Typographic minimum-margin merging (`left_min`/`right_min`, default 3/3) and paragraph line-wrapping remain in `tamil-hyphen`, respecting FR-002 from `architecture-roadmap.md`.

### Alternatives Considered
- *Leave `tamil-hyphen` with its own private classifiers*: Rejected because it violates Constitution Principle I (Single Source of Truth) and leaves duplicated classification logic unaligned with `tamil-core`.
- *Move hyphenation into `tamil-core`*: Rejected because `tamil-core` is strictly Rank 0 foundation primitives; hyphenation involves typographic layout policies and word wrapping (Rank 2).

---

## 2. Manifest Activation & Release Policy Promotion

### Decision
1. Update `tests/golden/manifest.json`: change `hyphen_syllable.jsonl` from `"status": "planned"` to `"status": "active"`.
2. Update `release-policy.toml`: add `"tamil-hyphen"` to `public_crates` in topological order:
   `["tamil-core", "tamil-norm", "tamil-collate", "tamil-numerals", "tamil-calendar", "tamil-codec", "tamil-hyphen", "tamil-toolkit"]`.
3. In `tools/release_policy.py`: remove the temporary exemptions for `tamil-hyphen` in `check_public_dependency_closure` and `check_umbrella_exports`.

### Rationale
- `hyphen_syllable.jsonl` contains 100+ vetted test vectors for Tamil syllabic hyphenation that already pass in the golden test suite.
- `tamil-hyphen` has complete documentation, specs (`009`, `010`, `011`, `012`, `015`), and passing tests. Promoting it satisfies Phase 3 milestone exit criteria.

---

## 3. Playground & Word Add-in WASM Consolidation

### Decision
- Maintain the unified Rust dispatcher (`tamil_toolkit::execute`) as the primary path for WASM in `playground/src/lib/engine.ts`.
- Ensure fallback pure-JS routines in Playground and Word Add-in (`integrations/office-word-addin/engine.js`) adhere 100% to the active `hyphen_syllable.jsonl` test vectors and `test_word_addin_contract.js`.

### Rationale
- Office.js Word Add-in runs within desktop Office and Word Online sandboxes where WASM loading might fail or need fallback in offline environments. Having the contract test `test_word_addin_contract.js` guarantee exact parity preserves reliability without breaking offline sandboxing.

---

## 4. CLI Subcommand Expansion Architecture

### Decision
Implement a modular CLI dispatcher in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` supporting:
- `tamil-toolkit core <subcommand>`
- `tamil-toolkit norm <subcommand>`
- `tamil-toolkit codec <subcommand>`
- `tamil-toolkit collate <subcommand>`
- `tamil-toolkit numerals <subcommand>`
- `tamil-toolkit calendar <subcommand>`
- `tamil-toolkit hyphen <subcommand>`

### Rationale
- `tamil-toolkit` is Rank 5 facade crate that already depends on all active library crates.
- Exposing intuitive CLI commands gives developers, linguists, and automated pipelines command-line access to all toolkit capabilities without writing custom code.
