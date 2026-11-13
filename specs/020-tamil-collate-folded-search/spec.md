# Feature Specification: `tamil-collate` Folded Search & Uyirmei-First Profile

**Feature Branch**: `020-tamil-collate-folded-search`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "Phase 5: tamil-collate Folded Search & Uyirmei-First Profile"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Error-Tolerant Search Indexing with Folded Keys (Priority: P1)

Users searching dictionaries, catalogs, or Tamil document collections often miss relevant entries because of common phonological confusions (Mayangoli variants like ல/ள/ழ, ன/ண, ர/ற) or Grantha vs. native consonant spelling differences (e.g., ஸ/ஷ vs. ச, ஜ vs. ச). A search system needs an index key where phonologically equivalent queries map to identical keys without destroying exact-order collation for standard sorting.

**Why this priority**: Search is the primary retrieval operation for users interacting with digital Tamil texts. Providing folded keys enables fuzzy, resilient lookups while preserving canonical collation keys.

**Independent Test**: Can be fully tested by generating folded search keys for pairs of words differing only by Mayangoli or Grantha substitutions (e.g., `பழம்` and `பலம்`) and verifying their keys match, while their standard sort keys remain distinct.

**Acceptance Scenarios**:

1. **Given** two Tamil words differing only by Mayangoli letters (e.g., `மணம்` and `மனம்`), **When** folded search keys are generated under the Mayangoli profile, **Then** both words produce identical keys.
2. **Given** two Tamil words differing only by Grantha vs. native consonants (e.g., `ஜனம்` and `சனம்`), **When** folded search keys are generated under the Grantha profile, **Then** both words produce identical keys.
3. **Given** two distinct Tamil words, **When** standard `search_key` or `sort_key` is requested under `agara-v1`, **Then** the original exact-match keys are preserved without any lossy folding.

---

### User Story 2 - Pedagogical & Modern School Dictionary Sorting (Priority: P2)

Educators, students, and textbook publishers expect alphabetical word lists to follow the modern pedagogical Tamil dictionary order taught in primary schools (Uyirmei-first, where basic syllables க, கா, கி... precede the pure muted consonant க்), whereas classical lexicons and the CLDR tailoring use Mei-first order (க் precedes க). Users need to select between the classical Mei-first Agara order and the modern Uyirmei-first school profile.

**Why this priority**: Tamil textbooks, educational curricula, and general-public school dictionaries follow the Uyirmei-first convention. Supporting this profile allows educational and modern publishing tools to produce culturally expected sort orders.

**Independent Test**: Can be tested by sorting a list of words where some start with pure consonants and others with vowel-consonant syllables (e.g., `கப்பல்`, `காகம்`, `க்ளப்`), verifying `கப்பல்` sorts before `க்ளப்` in Uyirmei-first order, and reverse in Mei-first order.

**Acceptance Scenarios**:

1. **Given** a set of Tamil words containing both pure consonants and initial syllables (e.g., `கப்பல்` and `க்ரௌண்ட்`), **When** sorted under the modern school dictionary profile, **Then** words with initial syllable `க` appear before words with initial consonant cluster `க்`.
2. **Given** the same set of Tamil words, **When** sorted under the default `agara-v1` profile, **Then** words with initial consonant `க்` appear before words with initial syllable `க`.

---

### User Story 3 - Backward Compatibility for Existing Collation Indexes (Priority: P3)

Existing applications relying on stored Agara collation keys require that existing key formats, key versions, and ordering sequences remain 100% identical and unchanged so database indexes and stored ordering columns do not become invalidated or corrupted.

**Why this priority**: Prevents breaking changes across production databases and stored search indexes that have already persisted `agara-v1` keys.

**Independent Test**: Can be tested by comparing generated `sort_key` and `search_key` output against previously verified golden vectors and verifying zero divergence in byte/integer outputs.

**Acceptance Scenarios**:

1. **Given** any existing valid Tamil text from the active golden corpus, **When** `sort_key` or `search_key` is invoked with the default profile, **Then** the exact output array matches the frozen `agara-v1` output.

---

### Edge Cases

- **Mixed Scripts and Non-Tamil Characters**: What happens when text contains English, digits, or punctuation alongside Tamil? The system must deterministically assign ordering tags so that Tamil letters sort consistently before fallback scripts, without crashing or dropping non-Tamil characters.
- **Empty and Whitespace Strings**: How are empty strings and pure whitespace handled? An empty string produces a minimal valid key header, and whitespace characters are handled deterministically in the fallback ordering tier.
- **Combined Mayangoli and Grantha Foldings**: When a query contains both Mayangoli differences and Grantha characters, the comprehensive folded key must handle both simultaneously.
- **NFC/NFD Input Equivalence**: Canonically equivalent Unicode strings (NFC and NFD decomposed forms) must produce identical collation keys across all profiles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a versioned folded search key capability that normalizes phonological variants (Mayangoli confusion pairs: ல/ள/ழ, ன/ண, ர/ற) into shared equivalence classes for search indexing.
- **FR-002**: The system MUST provide Grantha-to-native folding within the folded search key capability (mapping Grantha consonants to native equivalents: ஸ/ஷ $\rightarrow$ ச, ஜ $\rightarrow$ ச, ஹ $\rightarrow$ க, க்ஷ $\rightarrow$ ச).
- **FR-003**: The system MUST support a combined comprehensive folding mode that applies both Mayangoli and Grantha normalization together.
- **FR-004**: The system MUST preserve the exact output, format, and behavior of existing `sort_key` and `search_key` under `agara-v1` without modification or regression.
- **FR-005**: The system MUST introduce a modern Uyirmei-first collation profile where consonant syllables (க, கா, கி, கீ, கு, கூ, கெ, கே, கை, கொ, கோ, கௌ) sort before the corresponding muted consonant (க்).
- **FR-006**: The system MUST allow callers to choose between the default classical Mei-first profile (`agara-v1`) and the modern school dictionary profile (`uyirmei-first-v1`) for string comparison and word list sorting.
- **FR-007**: The system MUST treat canonically decomposed (NFD) and canonically precomposed (NFC) representations of the same text as strictly identical in ordering and key generation across all profiles.
- **FR-008**: The system MUST support stable sorting of word collections, preserving original character casing and input order for duplicate or equivalently-keyed entries.

### Key Entities

- **Collation Profile**: The ordering rule set governing letter priority. Encompasses:
  - `AgaraV1`: Traditional Mei-first ordering based on CLDR / Madras Tamil Lexicon tailoring.
  - `UyirmeiFirstV1`: Modern pedagogical school dictionary ordering where syllabic forms precede pure consonants.
- **Collation Key**: An ordered sequence of integers representing the sort weight of a string, comparable using standard lexicographical array comparison.
- **Folded Search Profile**: The specific normalization scheme applied before key derivation (Mayangoli, Grantha, or Comprehensive).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing `agara-v1` active golden test vectors produce identical sort and search keys with zero regression.
- **SC-002**: Words with Mayangoli spelling variations produce identical folded keys in 100% of test cases under the Mayangoli profile.
- **SC-003**: In school dictionary mode, words starting with simple consonant syllables appear before consonant-cluster words in 100% of tested word pairs.
- **SC-004**: Word list sorting maintains stable ordering across all profiles without modifying original string content or casing.
- **SC-005**: All collation operations achieve 100% behavioral parity across Rust, Python, WebAssembly, and CLI interfaces.

## Assumptions

- Collation operates deterministically in memory without external database or locale dependencies.
- The `agara-v1` profile remains the default profile to protect existing users and stored data.
- Search folding is an opt-in search indexing feature and does not replace exact collation keys used for dictionary sorting.
