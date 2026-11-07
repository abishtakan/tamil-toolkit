# Phase 0 Research: Crate Dependency DAG, Capability Boundaries & Difficulty-Tiered Roadmap (`016`)

**Date**: 2026-11-08  
**Feature**: [spec.md](spec.md)  
**Research Provenance**:
1. Codebase & Dependency Audit (`gemini-3.8-flash` subagent)
2. Tamil Computational Linguistics & NLP Domain Analysis (`gemini-3.8-flash` subagent)
3. Architectural Review & DAG Co-Design (`gpt-6.1-sol` with `xhigh` reasoning effort)

---

## 1. Decision Log

### Decision 1: Acyclic Crate Dependency DAG (`Rank 0` through `Rank 6`) & Automated Gate Enforcement
- **Decision**: Assign every existing and planned crate/extension an integer topological rank (`Rank 0` through `Rank 6`) and enforce `Rank(dependency) < Rank(dependent)` across `[dependencies]`, `[build-dependencies]`, and `[dev-dependencies]` in `tools/release_policy.py` (`just check-release-policy`).
- **Rationale**:
  - Guarantees zero circular dependencies across compile-time, build-time, and test-time graphs.
  - Prevents lower-rank crates (`Rank 0`–`Rank 4`) from pulling in the umbrella crate (`tamil-toolkit`, `Rank 5`) in `[dev-dependencies]`, keeping crate unit tests fast and isolated while placing cross-crate integration tests in `crates/tamil-toolkit/tests/`.
- **Alternatives Considered**:
  - *Allowing `[dev-dependencies]` cycles*: Rejected because Cargo struggles with feature unification across dev-dependency cycles during `cargo test --workspace` and `cargo package` verification.
  - *Manual code-review enforcement only*: Rejected during `$speckit-clarify` (Q1) in favor of automated enforcement in `tools/release_policy.py`.

---

### Decision 2: Boundary Between `tamil-core` (`Rank 0`), `tamil-yaappu` (`Rank 1`), and `tamil-hyphen` (`Rank 2`)
- **Decision**:
  - **`tamil-core` (`Rank 0`)** owns pure, context-free letter facts (`is_kuril`, `is_nedil`, `is_mei`/`is_otru`, `is_aytham`, nominal `baseline_maathirai`, sourced `ina_ezhuthu` homorganic pairs) and narrow orthographic syllable nucleus (`Olippasai`) segmentation with byte/letter spans.
  - **`tamil-yaappu` (`Rank 1`)** owns classical metrical interpretation (*Yaapparungalakkaarigai* / *Tolkappiyam*): context-dependent *Maathirai* reductions (*Kurriyalugaram*, *Kurriyaligaram*, *Alapedai*, *Aytham*), *Ner*/*Nirai* *Asai* formation, *Seer*, *Thalai*, *Adi*, *Thodai*, and *Paa* meter validation.
  - **`tamil-hyphen` (`Rank 2`)** owns typographic line-breaking policies (`left_min = 3, right_min = 3`, `MIN_WORD_LETTERS = 6`, margin segment merging, Frank Liang `.dic`, LibreOffice `.oxt`, and OpenXML `.docx`).
- **Rationale**:
  - Promoting the complete `tamil-hyphen` algorithm into `tamil-core` as general *Asai* classification would be linguistically incorrect because `tamil-hyphen` merges short boundary syllables to satisfy visual typographic margins (`left_min = 3, right_min = 3`), whereas classical *Yaappu* *Asai* scansion never merges feet based on line-breaking margins.
  - Conversely, extracting the raw phonetic nucleus + coda grouping (`Olippasai`) and *Kuril*/*Nedil* predicates into `tamil-core` eliminates duplicate character-classification tables across `tamil-hyphen`, `tamil-punarchi`, `tamil-phonetics`, and `tamil-yaappu`.
- **Alternatives Considered**:
  - *Making `tamil-yaappu` depend on `tamil-hyphen`*: Rejected because classical prosody is not a sub-domain of desktop publishing hyphenation.
  - *Duplicating `Kuril`/`Nedil` tables inside each crate*: Rejected by Constitution Principle I & IV (Single Source of Truth).

---

### Decision 3: Unidirectional Boundary Between `tamil-punarchi` (`Rank 2`) and `tamil-morph` (`Rank 3`)
- **Decision**:
  - `tamil-punarchi` (`Rank 2`) depends only on `tamil-core` and `tamil-norm`. It implements forward Sandhi synthesis (`join` with explicit *Vetrumai* / *Alvazhi* context) and bounded inverse-rule candidate generation (`split_candidates` returning rule IDs, reconstructed underlying stems, and surface spans).
  - `tamil-morph` (`Rank 3`) depends on `tamil-punarchi`. It uses `tamil-punarchi` transitions to strip/attach inflectional suffixes and validates/ranks `tamil-punarchi` compound split candidates against the morphological stem lexicon.
- **Rationale**:
  - Forward Sandhi synthesis is rule-driven over phonological boundaries and grammatical context, whereas reverse Sandhi splitting produces multiple phonological candidates (e.g., `மரக்கலம்` $\rightarrow$ `மரம் + கலம்`) that require a stem lexicon to prune false positives.
  - Placing candidate generation in `tamil-punarchi` (`Rank 2`) and lexical validation/ranking in `tamil-morph` (`Rank 3`) resolves the apparent mutual dependency without Cargo cycles.
- **Alternatives Considered**:
  - *Merging `tamil-punarchi` and `tamil-morph` into one monolithic crate*: Rejected because Nannool Sandhi synthesis is an independent grammatical primitive used outside full morphological parsing, and both crates already exist as distinct architectural units in the workspace.

---

### Decision 4: Three Distinct Normalization Contracts in `tamil-norm` (`Rank 1`)
- **Decision**: Structure `tamil-norm` around three explicit, non-overlapping contracts:
  1. **Canonical Normalization** (`normalize_nfc`, `normalize_nfd`): Lossless Unicode equivalence (including standard two-part vowel composition `\u{0BC6}\u{0BBE}` $\rightarrow$ `\u{0BCA}`).
  2. **Orthographic Repair** (`repair_tamil_text`): Explicit opt-in healing of malformed sequences (duplicate pullis `\u{0BCD}\u{0BCD}`, visually ordered left-kombu before consonant, optional stripping of `\u{00AD}`/zero-width controls) with structured diagnostic provenance, preserving `ZWJ`/`ZWNJ` by default per Constitution Principle II.
  3. **Search Folding** (`fold_for_search`): Explicit versioned lossy folding (*Mayangoli* `ல/ள/ழ`, `ன/ண`, `ர/ற` and Grantha phonetic folding) restricted strictly to opt-in search/indexing pipelines.
- **Rationale**:
  - Conflating lossy search folding or aggressive control-character stripping with default normalization would corrupt morphological analysis, classical poetry scansion, and persisted `agara-v1` collation keys (`docs/specs/collate-v0.1.md`).
- **Alternatives Considered**:
  - *Mutating `tamil-collate::search_key` in place to apply Mayangoli folding*: Rejected because `docs/specs/collate-v0.1.md` and active golden vectors guarantee exact key behavior; a separate versioned `folded_search_key` profile preserves index backward compatibility.

---

### Decision 5: Crate vs. Module Boundaries for Missing Tamil NLP Capabilities
- **Decision**:
  - **Standalone New Crates (4)** — created just-in-time at their scheduled phase (`FR-006`):
    1. `tamil-translit` (`Rank 2`, Phase 8 / Phase 17): Bidirectional orthographic transliteration (reversible ISO 15919, Madras University Lexicon, ITRANS/HK first; historical scripts Tamil-Brahmi `U+11000`, Grantha `U+11300`, Vatteluttu, Sinhala/Malayalam, and noisy Tanglish IME in Phase 17).
    2. `tamil-tokenize` (`Rank 2`, Phase 9): Surface word/sentence span segmentation, sourced Tamil abbreviation disambiguation (`திரு.`, `பி.ப.`, `மு.க.`), and stopwords.
    3. `tamil-phonetics` (`Rank 2`, Phase 14): Context-sensitive Grapheme-to-Phoneme (G2P) and IPA transcription (allophonic voicing, intervocalic lenition, post-nasal voicing, geminate invariance).
    4. `tamil-spell` (`Rank 4`, Phase 16): *Mayangoli* confusion-set spellchecker and morphology-backed *Valimigum / Valimigaa Idangal* (வல்லினம் மிகும்/மிகா இடங்கள்) grammatical linter.
  - **In-Crate Modules (2)** — added to existing `Rank 1` crates (`FR-007`):
    1. `tamil-codec::braille` (Phase 7): Bharathi Braille / Unicode Braille (`U+2800..U+28FF`) bidirectional conversion.
    2. `tamil-numerals` ITN parser (Phase 6): Reverse formal word-to-number parsing (`"நூற்று இருபத்து மூன்று"` $\rightarrow$ `123`).
- **Rationale**:
  - Keeps `tamil-translit` (orthographic script mapping) cleanly separated from `tamil-phonetics` (acoustic/allophonic IPA pronunciation), while folding Braille into `tamil-codec` and verbal number parsing into `tamil-numerals` to avoid micro-crate proliferation.
- **Alternatives Considered**:
  - *Scaffolding empty `tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, and `tamil-spell` directories immediately*: Rejected in `$speckit-clarify` (Q2) to avoid maintaining empty placeholder crates before their specification phase starts.
