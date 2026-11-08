# Quickstart: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts

**Feature Branch**: `018-tamil-norm-contracts`  
**Date**: 2026-11-08  
**Prerequisites**: [spec.md](spec.md), [contracts/norm-contract.md](contracts/norm-contract.md)

---

## 1. Rust Example

```rust
use tamil_norm::{fold_for_search, repair_tamil_text, FoldingProfile, RepairOptions};

fn main() {
    // 1. Orthographic Repair
    let corrupted = "\u{0BC6}\u{0B95}\u{0BBE}\u{0BCD}\u{0BCD}"; // "ெகாக்்" (visual kombu + double pulli)
    let repaired = repair_tamil_text(corrupted, &RepairOptions::default());
    assert_eq!(repaired.text, "கொக்");
    assert_eq!(repaired.diagnostics.duplicate_pulli_count, 1);
    assert_eq!(repaired.diagnostics.visual_kombu_count, 1);
    assert_eq!(repaired.diagnostics.total_repairs, 2);

    // 2. Mayangoli Search Folding
    let query1 = "பழம்";
    let query2 = "பலம்";
    assert_eq!(
        fold_for_search(query1, FoldingProfile::Mayangoli),
        fold_for_search(query2, FoldingProfile::Mayangoli)
    ); // Both yield "பலம்"

    // 3. Grantha Search Folding
    let text = "லக்ஷ்மி சந்தோஷம்";
    let folded = fold_for_search(text, FoldingProfile::Grantha);
    assert_eq!(folded, "லசுமி சந்தோசம்");
}
```

---

## 2. Python Example

```python
import tamil_toolkit as tt

# 1. Orthographic Repair
res = tt.repair_tamil_text("ெகாக்்")
print(res.text)  # "கொக்"
print(res.diagnostics.total_repairs)  # 2

# 2. Mayangoli Search Folding
assert tt.fold_for_search("பழம்", profile="mayangoli") == tt.fold_for_search("பலம்", profile="mayangoli")

# 3. Comprehensive Search Folding
print(tt.fold_for_search("லக்ஷ்மி  Pazham!", profile="comprehensive"))
# "லசுமி பலம்! (lowercase latin and normalized whitespace)"
```

---

## 3. TypeScript / WASM Example

```typescript
import { createApi } from 'tamil-toolkit';

const api = await createApi();

// Repair
const res = api.repairTamilText("ெகாக்்");
console.log(res.text); // "கொக்"
console.log(res.diagnostics.total_repairs); // 2

// Search Folding
const key1 = api.foldForSearch("மணம்", "mayangoli");
const key2 = api.foldForSearch("மனம்", "mayangoli");
console.log(key1 === key2); // true ("மனம்")
```
