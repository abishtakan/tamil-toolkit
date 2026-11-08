# Feature Specification: Phase 2 — `tamil-norm` Repair & Search-Folding Contracts

**Feature Branch**: `018-tamil-norm-contracts`

**Created**: 2026-11-08

**Status**: Complete

**Input**: User description: "phase 2"

## Clarifications

### Session 2026-11-08

- Q: Which Mayangoli folding baseline should be used for nasals: fold alveolar 'ன' and retroflex 'ண' only, or include dental 'ந' as well? → A: Fold alveolar 'ன' and retroflex 'ண' only ('ன' ↔ 'ண') into canonical representative 'ன'; keep dental 'ந' distinct in the default Mayangoli profile (support an optional 3-nasal flag in comprehensive profile if requested).
- Q: How should the Grantha ligature 'க்ஷ' be mapped in the Grantha folding profile: fold to hard stop 'க', affricate 'ச', or double 'க்க'/'ச்ச'? → A: Fold 'க்ஷ' to native affricate 'ச' (preserving attached vowel signs, e.g. 'லக்ஷ்மி' → 'லசுமி', 'மோக்ஷம்' → 'மோசம்') to align with sibilant/affricate folding.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Canonical Unicode Normalization (Priority: P1) 🎯 MVP

A developer, parser, or database storage layer needs to ensure all Tamil text is stored and compared in standard, canonical Unicode normalization forms (NFC or NFD), correctly handling independent vowels, dependent combining signs, and atomic Grantha clusters, while preserving joiners, format controls, and mixed-script text.

**Why this priority**: Unicode canonical equivalence is the bedrock of Tamil information processing. Inconsistent NFC/NFD encodings cause search misses, sorting errors, and visual display glitches.

**Independent Test**: Can be fully tested by evaluating decomposed Unicode sequences (e.g. `க` + `ொ` vs `க` + `ெ` + `ா`), independent two-part vowels (`ஔ`), and verifying that `normalize_nfc` and `normalize_nfd` produce deterministic, canonically equivalent Unicode strings matching Unicode 17.0 standard mappings.

**Acceptance Scenarios**:

1. **Given** a string containing decomposed vowel combinations (e.g. `க` `U+0B95` followed by `ெ` `U+0BC6` and `ா` `U+0BBE`), **When** `normalize_nfc` is called, **Then** the composite sequence is normalized into the single canonical precomposed code point `கொ` (`U+0BCA`).
2. **Given** precomposed Tamil letters, **When** `normalize_nfd` is called, **Then** the string is decomposed into canonical base consonants and combining vowel marks without altering text semantics.
3. **Given** a string with format controls such as Zero-Width Joiner (`ZWJ`, `U+200D`) or Zero-Width Non-Joiner (`ZWNJ`, `U+200C`), **When** canonical normalization is called, **Then** format controls are strictly preserved byte-for-byte.
4. **Given** text with mixed English, numerals, emoji, or punctuation, **When** normalized, **Then** non-Tamil characters pass through unchanged without corruption.

---

### User Story 2 - Opt-In Orthographic Text Repair with Diagnostic Counts (Priority: P2)

An application processing legacy documents, optical character recognition (OCR) outputs, voice-transcription transcripts, or web-scraped content needs to repair common orthographic corruptions (such as duplicate pullis, visual left-kombu reordering from typewriter keyboards, and accidental soft-hyphens) while receiving a diagnostic record of all changes made.

**Why this priority**: Corrupted Tamil encodings from legacy font decoders and legacy typists frequently contain misplaced kombus (`ெக` instead of `கெ`) and doubled viramas (`க்்`). Without explicit repair, searches fail and screen readers mispronounce words.

**Independent Test**: Can be tested independently by submitting intentionally malformed inputs with duplicate pullis and inverted kombus, confirming that the output text is valid, correctly rendered Tamil, and that the returned diagnostics accurately reflect the exact number of repairs applied.

**Acceptance Scenarios**:

1. **Given** text containing duplicate pulli marks (e.g. `க்்` or `த்்`), **When** `repair_tamil_text` is executed, **Then** extraneous duplicate viramas are collapsed into a single pulli (`க்`, `த்`) and recorded in the diagnostic breakdown.
2. **Given** text with visual left-kombu ordering (e.g. `ெ` + `க`, `ே` + `க`, or `ை` + `க` where the vowel sign erroneously precedes the base consonant), **When** `repair_tamil_text` is executed, **Then** the sequence is reordered into valid Unicode consonant-vowel composites (`கெ`, `கே`, `கை`).
3. **Given** text containing accidental soft-hyphen characters (`\u{00AD}`) or unprintable ASCII control characters, **When** `repair_tamil_text` is executed, **Then** these characters are stripped while preserving intentional spaces, line breaks, and formatting.
4. **Given** text with `ZWJ` or `ZWNJ`, **When** `repair_tamil_text` is executed with default options, **Then** format controls are retained intact; if the caller sets `strip_joiners: true`, they are stripped and counted in diagnostics.
5. **Given** already clean and well-formed Tamil text, **When** `repair_tamil_text` is executed, **Then** the output is identical to the input and total repair count is zero.

---

### User Story 3 - Versioned Lossy Search-Folding Profiles (Priority: P2)

A search engine, database indexing system, or spellchecker needs to fold phonetically confused or interchangeable letters (*Mayangoli* confusion sets: `ல/ள/ழ`, `ன/ண`, `ர/ற` and Grantha sibilants/fricatives: `ஸ/ஷ/ச`, `ஜ/ச`, `ஹ/க`) into canonical representative letters so that user searches find relevant documents regardless of minor spelling variations.

**Why this priority**: Tamil users frequently confuse Mayangoli consonants due to subtle phonetic proximity, regional dialects, or informal digital typing. Search engines and autocomplete systems require deterministic, versioned folding profiles to maximize search recall without altering stored source documents.

**Independent Test**: Can be tested independently by generating folded search keys for words differing only by Mayangoli letters (e.g. `பழம்` vs `பலம்` vs `பளம்`, or `மணம்` vs `மனம்`), confirming that both map to the exact same folded string while non-confusable letters remain distinct.

**Acceptance Scenarios**:

1. **Given** words containing lateral consonants `ல`, `ள`, or `ழ` (with any vowel diacritic or pulli, e.g. `பழம்`, `பலம்`), **When** folded under the `Mayangoli` profile, **Then** all three consonants fold to the representative canonical letter `ல` while preserving attached vowel signs (`பலம்`).
2. **Given** words containing alveolar `ன` and retroflex `ண` (e.g. `மனம்`, `மணம்`), **When** folded under the `Mayangoli` profile, **Then** both fold to the representative nasal letter `ன` (`மனம்`).
3. **Given** words containing medial rhotic `ர` and alveolar tap `ற` (e.g. `கரி`, `கறி`), **When** folded under the `Mayangoli` profile, **Then** both fold to representative rhotic `ர` (`கரி`).
4. **Given** words with Grantha letters (e.g. `சந்தோஷம்`, `கஷ்டம்`), **When** folded under the `Grantha` profile, **Then** sibilants `ஸ` and `ஷ` fold to native affricate `ச` (`சந்தோசம்`, `கச்டம்`).
5. **Given** mixed-script text or uppercase Latin search terms, **When** folded under the `Comprehensive` profile, **Then** Mayangoli folding, Grantha folding, Latin lowercasing, and whitespace normalization are applied uniformly.

---

### Edge Cases

- **Multiple Adjacent Kombus**: Sequences like `ெெக` or `ேெக` must be safely handled without unbounded recursion or panicking, folding extra signs or repairing to the nearest valid composite.
- **Standalone Combining Signs**: Stray combining vowel marks without a consonant base (e.g. string starting with `ா` or `ி`) must not panic or synthesize hallucinated consonants; they should be left as-is or reported as unattached in repair diagnostics.
- **Three-Part Vowels**: Decomposed representations of `கௌ` (`க` + `ெ` + `ள`) must be preserved or repaired accurately without confusing the trailing `ள` with the independent consonant `ள`.
- **Grantha Sibilant Consonant Clusters**: Clusters like `ஸ்ரீ` (`U+0BB8` `U+0BCD` `U+0BB0` `U+0BC0`) or `க்ஷ` (`U+0B95` `U+0BCD` `U+0BB7`) must fold gracefully without creating illegal intermediate Unicode code points.
- **Preservation of Non-Tamil Scripts**: Numbers, English words, punctuation, emojis, and symbols must pass through normalization and Mayangoli folding completely uncorrupted.
- **Empty & Whitespace-Only Strings**: Must return empty strings or original whitespace with zero diagnostics without allocating unnecessary buffers.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Canonical Normalization Functions)**: `tamil-norm` MUST provide `normalize_nfc(text: &str) -> String` and `normalize_nfd(text: &str) -> String` producing standard Unicode 17.0.0 normalization forms.
- **FR-002 (Preservation of Format Controls in Canonical Forms)**: `normalize_nfc` and `normalize_nfd` MUST strictly preserve `ZWJ` (`U+200D`) and `ZWNJ` (`U+200C`) byte-for-byte.
- **FR-003 (Opt-In Repair Function & Options)**: System MUST provide `repair_tamil_text(text: &str, options: &RepairOptions) -> RepairResult`. `RepairOptions` MUST support toggles for `duplicate_pulli` (default true), `visual_kombu` (default true), `strip_soft_hyphens` (default true), and `strip_joiners` (default false).
- **FR-004 (Duplicate Virama Healing)**: `repair_tamil_text` MUST collapse adjacent duplicate pulli marks (`U+0BCD`) into a single virama and record the count in `RepairDiagnostics.duplicate_pulli_count`.
- **FR-005 (Visual Left-Kombu Reordering)**: `repair_tamil_text` MUST detect when a left-side combining vowel sign (`U+0BC6` `ெ`, `U+0BC7` `ே`, `U+0BC8` `ை`) precedes a Tamil base consonant and reorder the sequence into a canonical consonant-vowel composite, incrementing `RepairDiagnostics.visual_kombu_count`.
- **FR-006 (Control Character & Soft-Hyphen Stripping)**: `repair_tamil_text` MUST strip discretionary soft-hyphens (`U+00AD`) and unprintable control characters, incrementing `RepairDiagnostics.stripped_control_count`.
- **FR-007 (Repair Diagnostic Breakdown)**: `RepairResult` MUST return `text: String`, `total_repairs: usize`, and `diagnostics: RepairDiagnostics` providing granular counts of each repair category applied.
- **FR-008 (Versioned Search-Folding Profiles)**: System MUST provide `fold_for_search(text: &str, profile: FoldingProfile) -> String`. `FoldingProfile` MUST support `Mayangoli`, `Grantha`, and `Comprehensive`.
- **FR-009 (Mayangoli Confusion-Set Folding)**: Under `FoldingProfile::Mayangoli`, system MUST collapse `ல, ள, ழ` into `ல`; `ன, ண` into `ன`; and `ர, ற` into `ர`, while preserving any attached combining vowel signs or pulli marks.
- **FR-010 (Grantha Sibilant & Fricative Folding)**: Under `FoldingProfile::Grantha`, system MUST map Grantha consonants to native equivalents (`ஸ, ஷ` -> `ச`; `ஜ` -> `ச`; `ஹ` -> `க`).
- **FR-011 (Comprehensive Search Folding)**: Under `FoldingProfile::Comprehensive`, system MUST apply both Mayangoli and Grantha folding, lowercase ASCII characters, and collapse consecutive whitespace into single spaces.
- **FR-012 (Rank 1 DAG Invariant)**: `tamil-norm` MUST depend solely on `tamil-core` (`Rank 0`) and standard libraries, introducing zero circular dependencies or higher-rank crate edges.
- **FR-013 (Tri-Runtime & Facade Integration)**: All normalization, repair, and search-folding capabilities MUST be exposed in `crates/tamil-toolkit` dispatcher and wrapped with native type bindings in Python (`tamil_toolkit`) and JavaScript/WASM (`tamil-toolkit`).
- **FR-014 (Active Escaped Golden Vectors)**: Normalization, repair, and folding test cases MUST be covered by active, escaped Unicode vectors in `tests/golden/norm_repair.jsonl` and `tests/golden/norm_folding.jsonl`.

---

### Key Entities

- **RepairOptions**: Configuration struct controlling orthographic repair behaviors:
  - `collapse_duplicate_pulli: bool` (default: true)
  - `reorder_visual_kombu: bool` (default: true)
  - `strip_soft_hyphens: bool` (default: true)
  - `strip_joiners: bool` (default: false)
- **RepairDiagnostics**: Telemetry breakdown of applied repairs:
  - `duplicate_pulli_count: usize`
  - `visual_kombu_count: usize`
  - `stripped_control_count: usize`
  - `total_repairs: usize`
- **RepairResult**: The outcome of text repair containing:
  - `text: String`
  - `diagnostics: RepairDiagnostics`
- **FoldingProfile**: Enumeration of lossy search-folding profiles:
  - `Mayangoli`: Folds lateral, rhotic, and nasal confusion sets.
  - `Grantha`: Folds Grantha sibilants, fricatives, and ligatures to native Tamil consonants.
  - `Comprehensive`: Combines Mayangoli, Grantha, Latin case-folding, and whitespace normalization.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Lossless Canonical Equivalence)**: 100% of valid Unicode Tamil strings round-trip through `normalize_nfc` and `normalize_nfd` without loss of characters, format controls (`ZWJ`, `ZWNJ`), or punctuation.
- **SC-002 (Orthographic Repair Precision)**: 100% of tested duplicate viramas and inverted visual kombus are healed to valid Unicode sequences without corrupting neighboring consonants.
- **SC-003 (Joiner Safety Invariant)**: Zero format controls (`ZWJ`, `ZWNJ`) are stripped unless `strip_joiners: true` is explicitly passed by the caller.
- **SC-004 (Folding Precision & Recall)**: Search queries folded under `Mayangoli` achieve 100% collision identity across defined Mayangoli pairs (`பழம்` == `பலம்`), while non-confusable letters retain distinct identities.
- **SC-005 (Multi-Runtime Parity & Performance)**: All active golden vectors execute identically without mocks across Rust, Python, and WebAssembly runtimes, maintaining < 50 microseconds per kilobyte processing speed for text repair.

---

## Assumptions

- **Canonical Authority**: Canonical normalization strictly follows Unicode 17.0.0 normalization forms (UAX #15).
- **Format Control Policy**: `ZWJ` and `ZWNJ` are valid linguistic modifiers (e.g. used in Grantha ligature control) and are never removed in canonical normalization.
- **Non-Destructive Default**: Text repair is always opt-in; canonical normalization never modifies orthographically malformed but valid Unicode sequences unless repair is explicitly requested.
- **Lossy Search Only**: `fold_for_search` is strictly a one-way transformation intended for search indexes and query matching, never for document storage or display.
