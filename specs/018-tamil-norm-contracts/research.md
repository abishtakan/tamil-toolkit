# Research: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts

**Feature Branch**: `018-tamil-norm-contracts`  
**Date**: 2026-11-08  
**Prerequisites**: [spec.md](spec.md)

---

## 1. Unicode Canonical Normalization Standards & Joiner Invariants

### 1.1 NFC and NFD Standards
- **Unicode Standard**: In Unicode 17.0.0 (UAX #15), Tamil syllables with vowel signs `ொ` (`U+0BCA`), `ோ` (`U+0BCB`), and `ௌ` (`U+0BCC`) have canonical decompositions:
  - `ொ` (`U+0BCA`) $\leftrightarrow$ `ெ` (`U+0BC6`) + `ா` (`U+0BBE`)
  - `ோ` (`U+0BCB`) $\leftrightarrow$ `ே` (`U+0BC7`) + `ா` (`U+0BBE`)
  - `ௌ` (`U+0BCC`) $\leftrightarrow$ `ெ` (`U+0BC6`) + `ௗ` (`U+0BD7`, Tamil Length Mark)
  - Independent `ஔ` (`U+0B94`) $\leftrightarrow$ `ஒ` (`U+0B92`) + `ௗ` (`U+0BD7`)
- **Canonical Equivalence**: NFC normalizes decomposed sequences back into single precomposed scalars. NFD decomposes precomposed characters into base consonant and combining diacritics.
- **Format Control Preservation**: The Unicode Standard dictates that Zero-Width Joiner (`ZWJ`, `U+200D`) and Zero-Width Non-Joiner (`ZWNJ`, `U+200C`) are formatting controls and are **never** removed during NFC or NFD normalization. They must be preserved byte-for-byte in canonical operations.

---

## 2. Orthographic Text Repair Engine

### 2.1 Problem Space in Legacy and Web-Scraped Tamil Text
Legacy font encoders (e.g. Bamini, TAB, TAM), OCR tools, and typewriter-style keyboards often emit non-standard or malformed Unicode sequences:
1. **Duplicate Pullis (Viramas)**:
   - Users or faulty IME auto-completions double the pulli: `க்்` (`U+0B95` `U+0BCD` `U+0BCD`).
   - Fix: Collapse contiguous sequences of `U+0BCD` into a single `U+0BCD`.
2. **Visual Left-Kombu Inversion**:
   - In Tamil typewriter keyboards and physical layouts, the left kombu `ெ` (`U+0BC6`), `ே` (`U+0BC7`), or `ை` (`U+0BC8`) is typed *before* the consonant key.
   - If converted naively, the string contains `ெக` (`U+0BC6` `U+0B95`) instead of `கெ` (`U+0B95` `U+0BC6`).
   - If followed by a right-side diacritic (e.g. `ெ` + `க` + `ா`), this represents the two-part vowel `கொ` (`U+0BCA`).
   - Fix: Scan for left kombu diacritics (`U+0BC6`, `U+0BC7`, `U+0BC8`) placed immediately before a base consonant (or Grantha base). Swap them to consonant + vowel sign, and re-normalize to NFC if paired with trailing `ா` or `ௗ`.
3. **Discretionary Soft-Hyphens and Control Characters**:
   - Word processing software and web scrapers introduce soft hyphens (`U+00AD`) or unprintable control codes (`\x00..\x08`, `\x0B..\x0C`, `\x0E..\x1F`).
   - Fix: Strip `U+00AD` and unprintable ASCII control characters. Preserve standard whitespace (`\t`, `\n`, `\r`, `' '`).
4. **Joiner Policy**:
   - Default: Preserve `ZWJ` and `ZWNJ` untouched.
   - Opt-in (`strip_joiners: true`): Strip `ZWJ`/`ZWNJ` when generating clean plain-text strings for indexing.

---

## 3. Lossy Search-Folding Profiles

### 3.1 *Mayangoli* (மயங்கொலி) Confusion Sets
In Tamil phonology, letters with similar points or manners of articulation frequently suffer orthographic confusion:
1. **Laterals / Liquids**:
   - `ல` (`U+0BB2`, alveolar lateral approximant)
   - `ள` (`U+0BB3`, retroflex lateral approximant)
   - `ழ` (`U+0BB4`, retroflex approximant)
   - **Canonical Representative**: `ல` (`U+0BB2`).
2. **Nasals**:
   - `ன` (`U+0BA9`, alveolar nasal)
   - `ண` (`U+0BA3`, retroflex nasal)
   - **Canonical Representative**: `ன` (`U+0BA9`).
   - Note: Dental `ந` (`U+0BA8`) is kept distinct by default as resolved in clarification, because initial/medial `ந` is syntactically distinct in standard Tamil.
3. **Rhotics**:
   - `ர` (`U+0BB0`, alveolar tap)
   - `ற` (`U+0BB1`, alveolar trill)
   - **Canonical Representative**: `ர` (`U+0BB0`).

### 3.2 Grantha to Native Tamil Folding
For phonetic search and simplified indexing, non-native Grantha consonants map to native Tamil stop/affricate equivalents:
- Sibilants: `ஸ` (`U+0BB8`), `ஷ` (`U+0BB7`) $\rightarrow$ `ச` (`U+0B9A`)
- Voiced palatal: `ஜ` (`U+0B9C`) $\rightarrow$ `ச` (`U+0B9A`)
- Fricative: `ஹ` (`U+0BB9`) $\rightarrow$ `க` (`U+0B95`)
- Atomic ligature: `க்ஷ` (`U+0B95` `U+0BCD` `U+0BB7`) $\rightarrow$ `ச` (`U+0B9A`) (per user clarification, e.g. `லக்ஷ்மி` $\rightarrow$ `லசுமி`, `மோக்ஷம்` $\rightarrow$ `மோசம்`)
- Grantha Shri: `ஸ்ரீ` $\rightarrow$ `சீ` (`ச` + `ீ`)

### 3.3 Preserving Attached Diacritics
When a base consonant is folded, its vowel diacritic or pulli virama must remain intact:
- `பழம்` $\rightarrow$ `ப` + (`ழ` $\rightarrow$ `ல`) + `ம்` = `பலம்`
- `கிளி` $\rightarrow$ `க` + `ி` + (`ள` $\rightarrow$ `ல` + `ி`) = `கிலி`
- `வெள்ளம்` $\rightarrow$ `வெ` + (`ள்` $\rightarrow$ `ல்`) + (`ள` $\rightarrow$ `ல`) + `ம்` = `வெல்லம்`
- `பூனை` $\rightarrow$ `பூ` + `னை`, `மாணை` $\rightarrow$ `மா` + (`ணை` $\rightarrow$ `னை`) = `மானை`

---

## 4. Rank 1 Invariant & Zero-Dependency Architectural Boundary

- `tamil-norm` (`Rank 1`) depends **only** on `tamil-core` (`Rank 0`).
- Core primitives used:
  - `tamil_core::Letters` / `get_letters` for tailored cluster iteration.
  - `tamil_core::split_uyirmei` / `tamil_core::compose_uyirmei` for diacritic extraction and re-composition.
  - `tamil_core::normalize_nfc` / `tamil_core::normalize_nfd`.
- Zero dependencies on higher-rank crates (`tamil-collate`, `tamil-hyphen`, `tamil-numerals`, `tamil-calendar`).
