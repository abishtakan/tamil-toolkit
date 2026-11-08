# Data Model: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts

**Feature Branch**: `018-tamil-norm-contracts`  
**Date**: 2026-11-08  
**Prerequisites**: [spec.md](spec.md), [research.md](research.md)

---

## 1. Entities & Data Structures

### 1.1 `RepairOptions`
Configuration parameters passed to `repair_tamil_text`:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct RepairOptions {
    /// Collapse contiguous duplicate viramas/pullis (e.g. `க்்` -> `க்`). Default: true.
    pub collapse_duplicate_pulli: bool,
    /// Reorder visual/legacy left-side kombus placed before consonants (e.g. `ெக` -> `கெ`). Default: true.
    pub reorder_visual_kombu: bool,
    /// Strip soft-hyphens (U+00AD) and non-printable ASCII control characters. Default: true.
    pub strip_soft_hyphens: bool,
    /// Strip Zero-Width Joiner (ZWJ, U+200D) and Zero-Width Non-Joiner (ZWNJ, U+200C). Default: false.
    pub strip_joiners: bool,
}

impl Default for RepairOptions {
    fn default() -> Self {
        Self {
            collapse_duplicate_pulli: true,
            reorder_visual_kombu: true,
            strip_soft_hyphens: true,
            strip_joiners: false,
        }
    }
}
```

### 1.2 `RepairDiagnostics`
Telemetry and count of repairs performed during text normalization:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, serde::Serialize, serde::Deserialize)]
pub struct RepairDiagnostics {
    /// Number of duplicate pulli occurrences collapsed.
    pub duplicate_pulli_count: usize,
    /// Number of visual left kombus reordered to proper consonant-vowel composite positions.
    pub visual_kombu_count: usize,
    /// Number of soft-hyphens, control characters, and (if enabled) joiners stripped.
    pub stripped_control_count: usize,
    /// Grand total of all repairs applied.
    pub total_repairs: usize,
}
```

### 1.3 `RepairResult`
Return value containing repaired text and diagnostic telemetry:

```rust
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
pub struct RepairResult {
    /// The cleaned, normalized Unicode text.
    pub text: String,
    /// Telemetry metrics on repairs performed.
    pub diagnostics: RepairDiagnostics,
}
```

### 1.4 `FoldingProfile`
Lossy search-folding profile selector:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FoldingProfile {
    /// Folds Mayangoli confusion sets: ல/ள/ழ -> ல; ன/ண -> ன; ர/ற -> ர.
    Mayangoli,
    /// Folds Grantha consonants to native equivalents: ஸ/ஷ -> ச; ஜ -> ச; ஹ -> க; க்ஷ -> ச.
    Grantha,
    /// Combines Mayangoli + Grantha folding, lowercases ASCII text, and normalizes whitespace.
    Comprehensive,
}
```

---

## 2. Invariants & Guarantees

1. **Non-Destructive by Default**:
   - `normalize_nfc` and `normalize_nfd` NEVER alter text semantics, strip format controls, or reorder letters.
   - Text repair is only executed when `repair_tamil_text` is explicitly invoked.
2. **Idempotency**:
   - `repair_tamil_text(repair_tamil_text(text, opt).text, opt).diagnostics.total_repairs == 0`.
   - `fold_for_search(fold_for_search(text, profile), profile) == fold_for_search(text, profile)`.
3. **Format Control Security**:
   - `strip_joiners: false` strictly guarantees that `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`) remain untouched.
4. **Rank 0 DAG Boundary**:
   - All internal operations use `tamil_core` and Rust standard library; zero other `tamil-*` dependencies.
