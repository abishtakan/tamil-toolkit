# Feature Specification: Phase 1 — Tamil Core Phonological & Nucleus Primitives Closeout

**Feature Branch**: `017-tamil-core-primitives`

**Created**: 2026-11-08

**Status**: Complete — implemented and verified across Rust, Python, and WASM (2026-11-08)

**Completion evidence**: All 23 tasks are checked in [tasks.md](tasks.md); validation results and tri-runtime parity are recorded in [the project handoff](../../docs/status.md).

**Input**: User description: "phase 1"

## Clarifications

### Session 2026-11-08

- Q: How should the syllable nucleus segmenter (Olippasai) handle words that begin with an initial pure consonant cluster before the first vowel nucleus (such as 'ஸ்டார்' or 'ப்ரியா')? → A: Attach leading consonants to the following vowel nucleus as an onset cluster (e.g., 'ஸ்டார்' -> 'ஸ்டார்', 'ப்ரியா' -> 'ப்ரி' + 'யா').
- Q: Should the ina_ezhuthu (cognate letter) API accept composite Uyirmei letters (e.g., 'கா' <-> 'ஙா'), or strictly pure consonants and independent vowels? → A: Support both: evaluate pure consonants/vowels directly, and for composite Uyirmei letters, preserve the vowel sign while mapping the base consonant (e.g., 'கா' <-> 'ஙா', 'கி' <-> 'ஙி').

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tamil Letter Quantity & Duration Classification (Priority: P1) 🎯 MVP

A linguistics software developer, language tutor, or grammar engine needs to inspect any Tamil letter (independent vowel, pure consonant, consonant-vowel composite, or special letter) to determine its classical phonological quantity (*Kuril*, *Nedil*, *Mei* / *Otru*, *Aytham*) and its nominal baseline duration (*Maathirai*).

**Why this priority**: Letter quantity is the foundational phonological building block for prosody (*Yaappu*), Sandhi (*Punarchi*), syllabification, and speech synthesis. Without this classification, higher-level grammatical rules cannot determine vowel weight, mora timing, or metrical patterns.

**Independent Test**: Can be fully tested by evaluating individual Tamil characters and composites across the full Unicode Tamil block, confirming that each letter maps to its exact quantity category and canonical mora duration without requiring any external dictionary or higher-level crate.

**Acceptance Scenarios**:

1. **Given** a short vowel (e.g. `அ`, `இ`, `உ`, `எ`, `ஒ`) or a short consonant-vowel composite (e.g. `க`, `கி`, `சு`, `தெ`, `நொ`), **When** quantity classification and duration are queried, **Then** the letter is classified as *Kuril* with a baseline duration of exactly 1.0 mora (*Maathirai*).
2. **Given** a long vowel (e.g. `ஆ`, `ஈ`, `ஊ`, `ஏ`, `ஐ`, `ஓ`, `ஔ`) or a long consonant-vowel composite (e.g. `கா`, `கீ`, `சூ`, `தே`, `கை`, `நோ`, `கௌ`), **When** quantity classification and duration are queried, **Then** the letter is classified as *Nedil* with a baseline duration of exactly 2.0 morae (*Maathirai*).
3. **Given** a pure consonant with pulli (e.g. `க்`, `த்`, `ம்`, `ழ்`), **When** quantity classification and duration are queried, **Then** the letter is classified as *Mei* (*Otru*) with a baseline duration of exactly 0.5 mora (*Maathirai*).
4. **Given** the Aytham character (`ஃ`), **When** quantity classification and duration are queried, **Then** the letter is classified as *Aytham* with a baseline duration of exactly 0.5 mora (*Maathirai*).
5. **Given** a non-Tamil character, punctuation, or whitespace, **When** queried, **Then** it is classified as *Other* or non-quantity with an undefined or zero mora count.

---

### User Story 2 - Homorganic Cognate Letter Mapping (*Ina Ezhuthu*) (Priority: P2)

A computational linguist or grammar engine needs to query classical cognate letter affinities (*Ina Ezhuthu*)—specifically the phonetic harmony between hard stop consonants (*Vallinam*) and their homorganic nasals (*Mellinam*), as well as between short and long vowels.

**Why this priority**: Cognate pairings govern Sandhi assimilation rules (*Punarchi*), allophonic voicing in phonetics, rhyming rules in poetry (*Ethugai* / *Monai*), and spelling error confusion sets (*Mayangoli*).

**Independent Test**: Can be tested independently by querying cognate pairs across all 18 classical consonants and 12 vowels, verifying bidirectional symmetry and grammatical validity against *Tolkappiyam* and *Nannool*.

**Acceptance Scenarios**:

1. **Given** any of the 6 hard stop consonants (*Vallinam*: `க்`, `ச்`, `ட்`, `த்`, `ப்`, `ற்`), **When** its cognate nasal is queried, **Then** the system returns its exact homorganic nasal partner (*Mellinam*: `ங்`, `ஞ்`, `ண்`, `ந்`, `ம்`, `ன்` respectively).
2. **Given** any of the 6 nasal consonants (*Mellinam*), **When** its cognate stop is queried, **Then** the system returns its exact homorganic stop partner (*Vallinam*).
3. **Given** medium consonants (*Idaiyinam*: `ய்`, `ர்`, `ல்`, `வ்`, `ழ்`, `ள்`), **When** checked for nasal/stop cognates, **Then** the system indicates they form a self-contained group without nasal stop partners.
4. **Given** short and long vowels, **When** queried for cognate pairs, **Then** standard pairs are returned (`அ` ↔ `ஆ`, `இ` ↔ `ஈ`, `உ` ↔ `ஊ`, `எ` ↔ `ஏ`, `ஒ` ↔ `ஓ`) and diphthongs map to their classical phonetic partners per *Nannool* (`ஐ` ↔ `இ`, `ஔ` ↔ `உ`).
5. **Given** two letters, **When** testing whether they are cognates, **Then** the system returns true for valid pairs (e.g. `த்` and `ந்`, or `அ` and `ஆ`) and false for non-cognate pairs (e.g. `த்` and `ம்`).

---

### User Story 3 - Orthographic Syllable Nucleus Segmentation (*Olippasai*) (Priority: P2)

A text processing engine, hyphenator, speech synthesizer, or prosody scanner needs to segment Tamil words into natural phonetic sound units (*Olippasai*), each consisting of an orthographic vowel nucleus (independent vowel or consonant-vowel composite) along with any trailing pure consonants or Aytham markers, preserving character span positions.

**Why this priority**: Providing a single, canonical syllable nucleus extractor in the foundational core crate prevents duplicate or conflicting syllabification logic across downstream typography (`tamil-hyphen`), prosody (`tamil-yaappu`), phonetics (`tamil-phonetics`), and search indexing.

**Independent Test**: Can be tested independently by running strings through syllable nucleus segmentation and verifying that each segment accurately identifies its start/end offsets, nucleus letter, and coda letters.

**Acceptance Scenarios**:

1. **Given** a simple word with open syllables (e.g. "தமிழ்"), **When** segmented into syllable nuclei, **Then** the system yields "த" (nucleus "த", no coda) and "மிழ்" (nucleus "மி", coda "ழ்") with exact character boundaries.
2. **Given** a word with internal pure consonants (e.g. "கற்பனை"), **When** segmented, **Then** the pure consonant attaches to the preceding vowel nucleus as a coda, producing "கற்", "ப", "னை".
3. **Given** a word containing the Aytham letter (e.g. "அஃது"), **When** segmented, **Then** the Aytham letter attaches as a coda to the preceding nucleus, producing "அஃ", "து".
4. **Given** a word with atomic Grantha sequences (e.g. `ஸ்ரீலங்கா`, `லக்ஷ்மி`), **When** segmented, **Then** the atomic ligatures remain intact without breaking diacritics or separating marks.
5. **Given** text containing non-Tamil words or mixed punctuation, **When** segmented, **Then** non-Tamil tokens are demarcated without disturbing the boundaries or validity of neighboring Tamil syllable nuclei.

---

### Edge Cases

- **Diphthong Classification**: Vowels `ஐ` (*ai*) and `ஔ` (*au*) are composite in sound but fundamentally categorized as *Nedil* (2 morae) in classical Tamil grammar. Their cognates are `இ` and `உ` respectively.
- **Grantha Letters & Ligatures**: Pure Grantha consonants with pulli (e.g. `ஜ்`, `ஷ்`, `ஸ்`, `ஹ்`) receive 0.5 mora. Grantha vowel composites (e.g. `ஸா`, `ஹி`) follow the vowel length of their diacritic mark. Atomic ligatures (`க்ஷ`, `ஸ்ரீ`) must not be torn apart during segmentation.
- **Isolated Vowel Signs**: Standalone combining vowel signs without a consonant base (e.g. isolated `ா`, `ி`) are malformed and must be classified as non-Tamil / invalid rather than hallucinating a vowel nucleus.
- **Zero-Width Controls**: Zero-Width Joiner (`ZWJ`, `U+200D`) and Zero-Width Non-Joiner (`ZWNJ`, `U+200C`) occurring in text must be preserved within their containing spans without alteration or silent removal.
- **Consecutive Consonants**: Clustered pure consonants (e.g., geminates or clusters like `ர்த்த`) must bind cleanly as coda consonants to the preceding nucleus according to standard phonetic syllabification.
- **Initial Consonant Clusters**: When words begin with pure consonants or Grantha clusters before the first vowel nucleus (e.g. loanwords like 'ஸ்டார்' or 'ப்ரியா'), the initial consonants attach as onset cluster consonants to the first vowel nucleus, preventing orphan pure consonants and maintaining span continuity.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Quantity Classification)**: System MUST provide a function or predicate to classify any Tamil letter into its primary phonological quantity: *Kuril* (short), *Nedil* (long), *Mei* / *Otru* (pure consonant with pulli), *Aytham*, or *Other* (non-Tamil / unclassified).
- **FR-002 (Baseline Mora Measure)**: System MUST return the nominal baseline duration (*Maathirai*) for individual letters: exactly 1.0 mora for *Kuril*, 2.0 morae for *Nedil*, 0.5 mora for *Mei* and *Aytham*, and 0.0 or undefined for non-quantity characters.
- **FR-003 (Predicates for Quantity Queries)**: System MUST provide convenience predicates for direct boolean checks: `is_kuril`, `is_nedil`, `is_mei`, `is_otru` (equivalent to `is_mei`), and `is_aytham`.
- **FR-004 (Homorganic Consonant Cognates)**: System MUST provide bidirectional mapping between the 6 hard stops (*Vallinam*: `க்`, `ச்`, `ட்`, `த்`, `ப்`, `ற்`) and their respective homorganic nasals (*Mellinam*: `ங்`, `ஞ்`, `ண்`, `ந்`, `ம்`, `ன்`). When queried with a composite *Uyirmei* consonant (e.g., `கா`, `கி`), the system MUST preserve the vowel diacritic while mapping the consonant base (e.g., `கா` ↔ `ஙா`, `கி` ↔ `ஙி`).
- **FR-005 (Vowel Cognates)**: System MUST provide cognate mappings for short and long vowels, mapping `அ` ↔ `ஆ`, `இ` ↔ `ஈ`, `உ` ↔ `ஊ`, `எ` ↔ `ஏ`, `ஒ` ↔ `ஓ`, `ஐ` ↔ `இ`, and `ஔ` ↔ `உ`.
- **FR-006 (Cognate Pair Validation)**: System MUST provide a verification function that takes two letters and determines whether they constitute a valid classical *Ina Ezhuthu* pair, supporting both pure consonants/vowels and corresponding *Uyirmei* letters.
- **FR-007 (Phonetic Syllable Nucleus Extraction & Onset Clusters)**: System MUST extract phonetic syllable units (*Olippasai*), grouping each vowel nucleus with its preceding onset consonants (including initial consonant clusters such as 'ஸ்டார்' or 'ப்ரியா') and all contiguous trailing coda consonants or Aytham markers.
- **FR-008 (Span and Boundary Preservation)**: Syllable nucleus extraction MUST return character span offsets (start and end positions) referencing the original text, ensuring zero loss of characters or punctuation.
- **FR-009 (Grantha & Ligature Integrity)**: All phonological classifications and syllable segmentations MUST respect atomic Grantha sequences (such as `க்ஷ` and `ஸ்ரீ`) and prevent splitting of ligatures or diacritics.
- **FR-010 (Separation from Downstream Policies)**: Syllable nucleus extraction in `tamil-core` MUST NOT apply line-breaking margin policies (`left_min`/`right_min`) or contextual prosodic reductions (*Kurriyalugaram*/*Alapedai*); these belong strictly to `tamil-hyphen` and `tamil-yaappu` respectively.
- **FR-011 (Golden Vector Verification)**: All phonological classifications, cognate pairs, and syllable nucleus outputs MUST be covered by auditable test datasets in `tests/golden/` formatted with escaped Unicode sequences.

---

### Key Entities

- **LetterQuantity**: An enumeration of phonological weight categories:
  - `Kuril`: Short vowel or consonant-vowel composite (1 mora).
  - `Nedil`: Long vowel or consonant-vowel composite, including diphthongs (2 morae).
  - `Mei` / `Otru`: Pure consonant terminating in a pulli virama (0.5 mora).
  - `Aytham`: The special Aytham character `ஃ` (0.5 mora).
  - `Other`: Characters outside the Tamil phonological quantity system (e.g. digits, symbols, foreign letters).
- **InaEzhuthu**: A representation of phonetic affinity between paired sounds, encompassing Vallinam-Mellinam homorganic pairs and short-long vowel pairings.
- **Olippasai**: An orthographic syllable unit consisting of:
  - `nucleus`: The central vowel or consonant-vowel composite.
  - `codas`: An ordered list of trailing pure consonants or Aytham markers attached to the nucleus.
  - `span`: The character offset range (start index and end index) in the source text.
  - `text`: The contiguous substring representing the complete syllable sound unit.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (Complete Letter Coverage)**: 100% of all 247 standard Tamil letters (12 vowels, 18 pure consonants, 216 consonant-vowel combinations, 1 Aytham) plus recognized Grantha extensions are classified without failure.
- **SC-002 (Mora Accuracy)**: 100% of standard Tamil letters yield exact classical baseline *Maathirai* measures matching primary grammatical authority.
- **SC-003 (Cognate Pair Coverage)**: All 6 consonant stop-nasal pairs and all 7 vowel cognate pairs are accurately verified in both query directions.
- **SC-004 (Span Identity & Reconstitution)**: Reassembling the segmented *Olippasai* spans across any source text reproduces the original input string byte-for-byte with zero loss of format controls, whitespace, or punctuation.
- **SC-005 (Independent Usability)**: Downstream crates (`tamil-hyphen`, `tamil-yaappu`, `tamil-punarchi`) can consume these primitives directly from `tamil-core` without defining duplicate classification tables.

---

## Assumptions

- **Grammatical Authority**: Phonological definitions and cognate pairings are grounded in classical Tamil grammar (*Tolkappiyam Ezhuthathikaram* and *Nannool Ezhuthathikaram*).
- **Nominal vs. Contextual Duration**: `baseline_maathirai` measures the isolated, unconditioned phonetic duration of a letter. Context-dependent prosodic shortening (e.g., *Kurriyalugaram* shortening to 0.5 mora, or *Alapedai* lengthening to 3 morae) is deferred to `tamil-yaappu` and does not alter the baseline value in `tamil-core`.
- **Typographic Neutrality**: *Olippasai* syllable nucleus extraction reflects pure spoken/sound grouping. Typographic hyphenation constraints (such as minimum line margins `left_min = 3, right_min = 3`) remain the exclusive responsibility of `tamil-hyphen`.
- **Single Crate Scope**: All primitives specified here reside strictly in `crates/tamil-core` (`Rank 0`), requiring zero new dependencies.
