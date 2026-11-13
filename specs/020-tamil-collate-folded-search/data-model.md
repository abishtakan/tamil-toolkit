# Phase 1 Data Model: `tamil-collate` Folded Search & Uyirmei-First Profile

## Entities and Types

### `CollationProfile`
Enumerates supported collation rule sets.
- `AgaraV1`: Traditional Mei-first Agara collation (CLDR 48 / University of Madras Tamil Lexicon).
- `UyirmeiFirstV1`: Modern pedagogical school dictionary collation (Uyirmei syllables precede pure consonants).

### `FoldingProfile` (Re-exported from `tamil_norm::FoldingProfile`)
Enumerates search folding schemes:
- `Mayangoli`: Folds confusion sets (ல/ள/ழ, ன/ண, ர/ற).
- `Grantha`: Folds Grantha consonants to native equivalents.
- `Comprehensive`: Combines Mayangoli + Grantha + case/whitespace normalization.

### Collation Key Structure
A vector of unsigned 32-bit integers (`Vec<u32>`):
- Element 0: Key version header (e.g. `1`).
- Following elements in pairs:
  - `[0, rank]`: Recognized Tamil element in the active profile's ordered alphabet.
  - `[1, scalar]`: Fallback scalar character (non-Tamil, punctuation, symbol, etc.).
- Ordering: Lexicographical comparison across slice slices `&[u32]`.
