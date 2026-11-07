# Contract: Workspace Crate Dependency DAG & Release Policy Invariants (`016`)

**Date**: 2026-11-08  
**Feature**: [spec.md](../spec.md)  
**Enforced By**: [`tools/release_policy.py`](../../../tools/release_policy.py) (`just check-release-policy`) and [`docs/specs/architecture-roadmap.md`](../../../docs/specs/architecture-roadmap.md)

---

## 1. Canonical Crate Rank Map (`CRATE_RANKS`)

Every `tamil-*` crate, extension, and binding package in the repository is assigned an immutable integer rank in `CRATE_RANKS`:

```python
CRATE_RANKS = {
    # Rank 0: Foundational Orthography & Phonological Primitives
    "tamil-core": 0,

    # Rank 1: Normalization, Codecs (+ Braille), Numerals (+ ITN), Classical Prosody
    "tamil-norm": 1,
    "tamil-codec": 1,
    "tamil-numerals": 1,
    "tamil-yaappu": 1,

    # Rank 2: Contextual Engines, Sandhi, Typography, Transliteration, Phonetics, Tokenization
    "tamil-calendar": 2,
    "tamil-collate": 2,
    "tamil-hyphen": 2,
    "tamil-punarchi": 2,
    "tamil-translit": 2,   # Unscaffolded until Phase 8
    "tamil-phonetics": 2,  # Unscaffolded until Phase 14
    "tamil-tokenize": 2,   # Unscaffolded until Phase 9

    # Rank 3: Morphological Analyzer & Lexicon
    "tamil-morph": 3,

    # Rank 4: High-Level Linguistic Applications & Isolated Database Extension
    "tamil-dialect": 4,
    "tamil-spell": 4,      # Unscaffolded until Phase 16
    "pg_tamil": 4,

    # Rank 5: Unified Facade, Cross-Branch Orchestrator & CLI
    "tamil-toolkit": 5,

    # Rank 6: Multi-Runtime FFI Adapters
    "tamil-python": 6,
    "tamil-wasm": 6,
    "tamil-dart": 6,
}
```

---

## 2. Automated Verification Rules in `tools/release_policy.py`

When `python tools/release_policy.py check` (`just check-release-policy`) executes:

1. **Complete Rank Registration**:
   - Every Cargo manifest under `crates/*/Cargo.toml`, `extensions/*/Cargo.toml`, and `bindings/*/Cargo.toml` (or `bindings/dart-flutter/rust/Cargo.toml`) MUST have its `package.name` registered in `CRATE_RANKS`.
2. **Strict Topological Ordering (`FR-001`)**:
   - For every manifest `M` with `source_rank = CRATE_RANKS[M.package.name]`, inspect all three dependency tables (`dependencies`, `build-dependencies`, `dev-dependencies`) and any target-specific dependency tables:
   - For every dependency `D` where `D` is in `CRATE_RANKS`:
     - Require `CRATE_RANKS[D] < source_rank`.
     - Require `(M.package.name, D)` is in `ALLOWED_INTERNAL_EDGES` (if strict edge whitelisting is enabled) or satisfies the rank inequality.
3. **Unscaffolded Crate Guard (`FR-006`)**:
   - The four existing planned crates (`tamil-punarchi`, `tamil-morph`, `tamil-yaappu`, `tamil-dialect`) are permitted as internal workspace scaffolds (`publish = false`).
   - Unscaffolded future crates (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`) MUST NOT exist as empty `STATUS = "planned"` directories prior to their specification phase.
4. **Public Dependency Closure (`FR-009`)**:
   - Every crate listed in `release-policy.toml` `public_crates` MUST only depend on `tamil-*` crates that are also listed earlier in `public_crates` (with the temporary `tamil-hyphen` exemption removed in Phase 3).
