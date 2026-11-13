# Phase 0 Research: `tamil-collate` Folded Search & Uyirmei-First Profile

## Decision 1: Architecture of `folded_search_key`
- **Decision**: `folded_search_key` accepts an input string and a `FoldingProfile` (re-exported or mapped from `tamil_norm::FoldingProfile`: `Mayangoli`, `Grantha`, `Comprehensive`). It runs `tamil_norm::fold_for_search(text, profile)` and then generates the collation key using `tamil_collate::sort_key(&folded)`.
- **Rationale**:
  - `tamil-norm` (`Rank 1`) already implements rigorously tested and verified folding rules for Mayangoli and Grantha in Spec 018.
  - Collation (`Rank 2`) depending on `tamil-norm` preserves the DAG rank invariant: `Rank(norm) = 1 < Rank(collate) = 2`.
  - Re-using `tamil_norm::fold_for_search` guarantees complete parity between text-level search folding and key-level search folding.
- **Alternatives Considered**:
  - Implementing custom folding tables inside `tamil-collate`: Rejected. Violates Constitution Principle I (Rust single source of truth) and code duplication rules.
  - Mutating existing `search_key`: Rejected. FR-005 and architecture-roadmap roadmap explicitly mandate that `search_key` under `agara-v1` must preserve its exact backward-compatible contract and integer output.

## Decision 2: Uyirmei-First Profile Definition & Declarative Sourcing
- **Decision**: Define modern school dictionary ordering in `lexicon/collate_uyirmei_first.toml` with profile name `"uyirmei-first-v1"` and key version `1` (or separate profile tag). In each of the 24 consonant rows, the 12 vowel-consonant syllables ($C + \text{அ}, \dots, C + \text{ஔ}$) precede the pure consonant ($C + \text{pulli}$).
- **Rationale**:
  - In Tamil Nadu textbook curriculum and modern Tamil school dictionaries (e.g. *Tamil Lexicon for Schools*, *Kazhagam Tamil Agarathi*, *Lifco*), students learn letters starting from the Uyirmei syllable $க$ before the consonant-cluster form $க்$.
  - Sourcing this in a declarative TOML file in `lexicon/` adheres to Constitution Principle IV (declarative data compiled at build time).
  - Keeps `agara-v1` tables completely untouched.
- **Alternatives Considered**:
  - Ordering $க்$ at the very end of the alphabet after all consonants: Rejected. Modern school dictionaries order $க்$ immediately after $கௌ$, preserving consonant row grouping.

## Decision 3: API Shape & Non-Breaking Evolution
- **Decision**:
  - Keep `sort_key(text)`, `search_key(text)`, `compare(left, right)`, and `sort_words(words)` using default `agara-v1`.
  - Introduce:
    - `pub enum CollationProfile { AgaraV1, UyirmeiFirstV1 }`
    - `sort_key_with_profile(text: &str, profile: CollationProfile) -> Vec<u32>`
    - `compare_with_profile(left: &str, right: &str, profile: CollationProfile) -> Ordering`
    - `sort_words_with_profile(words: &[String], profile: CollationProfile) -> Vec<String>`
    - `folded_search_key(text: &str, profile: FoldingProfile) -> Vec<u32>`
    - `folded_search_key_with_profile(text: &str, fold_profile: FoldingProfile, collate_profile: CollationProfile) -> Vec<u32>`
- **Rationale**:
  - 100% backward compatibility for all existing callers and tests.
  - Clean, expressive API for new profile selection.
