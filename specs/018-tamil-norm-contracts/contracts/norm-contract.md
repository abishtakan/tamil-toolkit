# API Contract: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts

**Feature Branch**: `018-tamil-norm-contracts`  
**Date**: 2026-11-08  
**Prerequisites**: [spec.md](../spec.md), [data-model.md](../data-model.md)

---

## 1. Rust API (`tamil-norm`)

```rust
// Canonical Unicode normalization (re-exported from core)
pub use tamil_core::{normalize_nfc, normalize_nfd};

// Types
pub use crate::types::{FoldingProfile, RepairDiagnostics, RepairOptions, RepairResult};

// Functions
pub fn repair_tamil_text(text: &str, options: &RepairOptions) -> RepairResult;
pub fn fold_for_search(text: &str, profile: FoldingProfile) -> String;
```

---

## 2. Facade Dispatcher JSON Protocol (`tamil-toolkit`)

### 2.1 Action: `norm.repair_text`
```json
// Request
{
  "action": "norm.repair_text",
  "text": "ெகாக்்",
  "options": {
    "collapse_duplicate_pulli": true,
    "reorder_visual_kombu": true,
    "strip_soft_hyphens": true,
    "strip_joiners": false
  }
}

// Response
{
  "text": "கொக்",
  "diagnostics": {
    "duplicate_pulli_count": 1,
    "visual_kombu_count": 1,
    "stripped_control_count": 0,
    "total_repairs": 2
  }
}
```

### 2.2 Action: `norm.fold_for_search`
```json
// Request
{
  "action": "norm.fold_for_search",
  "text": "பழம் மற்றும் சந்தோஷம்",
  "profile": "comprehensive"
}

// Response
{
  "folded": "பலம் மற்றும் சந்தோசம்"
}
```

---

## 3. Python Bindings (`tamil_toolkit`)

```python
class RepairOptions:
    def __init__(
        self,
        collapse_duplicate_pulli: bool = True,
        reorder_visual_kombu: bool = True,
        strip_soft_hyphens: bool = True,
        strip_joiners: bool = False,
    ) -> None: ...

class RepairDiagnostics:
    duplicate_pulli_count: int
    visual_kombu_count: int
    stripped_control_count: int
    total_repairs: int

class RepairResult:
    text: str
    diagnostics: RepairDiagnostics

class FoldingProfile:
    MAYANGOLI: str
    GRANTHA: str
    COMPREHENSIVE: str

def repair_tamil_text(text: str, options: RepairOptions | None = None) -> RepairResult: ...
def fold_for_search(text: str, profile: str = "comprehensive") -> str: ...
```

---

## 4. TypeScript / WASM API (`tamil-toolkit`)

```typescript
export interface RepairOptions {
  collapse_duplicate_pulli?: boolean;
  reorder_visual_kombu?: boolean;
  strip_soft_hyphens?: boolean;
  strip_joiners?: boolean;
}

export interface RepairDiagnostics {
  duplicate_pulli_count: number;
  visual_kombu_count: number;
  stripped_control_count: number;
  total_repairs: number;
}

export interface RepairResult {
  text: string;
  diagnostics: RepairDiagnostics;
}

export type FoldingProfile = 'mayangoli' | 'grantha' | 'comprehensive';

export interface TamilToolkitApi {
  // Normalization & Repair
  normalizeNfc(text: string): string;
  normalizeNfd(text: string): string;
  repairTamilText(text: string, options?: RepairOptions): RepairResult;
  foldForSearch(text: string, profile?: FoldingProfile): string;
}
```
