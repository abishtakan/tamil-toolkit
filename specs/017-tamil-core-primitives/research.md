# Research: Tamil Core Phonological & Nucleus Primitives (`017`)

**Feature**: [spec.md](spec.md)  
**Status**: Complete (All unknowns resolved)

---

## 1. Research Topics & Technical Decisions

### Topic 1: Phonological Quantity Classification & Duration Representation

- **Context**: Need to represent Tamil letter weight (*Kuril*, *Nedil*, *Mei* / *Otru*, *Aytham*) and its canonical duration measure (*Maathirai* / mora).
- **Decision**: 
  1. Define a `LetterQuantity` enum with variants: `Kuril`, `Nedil`, `Mei`, `Aytham`, and `Other`.
  2. Implement `Maathirai` as a rational/exact value struct or constant f32 (`1.0`, `2.0`, `0.5`, `0.0`) with helper methods (`as_fraction() -> (u8, u8)`, `as_f32() -> f32`).
  3. Ground rules in *Tolkappiyam Ezhuthathikaram* (Noorpa 3–4) and *Nannool Ezhuthathikaram* (Sutra 88):
     - Kuril vowels (`அ, இ, உ, எ, ஒ`) and their Uyirmei combinations = 1 mora.
     - Nedil vowels (`ஆ, ஈ, ஊ, ஏ, ஐ, ஓ, ஔ`) and their Uyirmei combinations = 2 morae. Diphthongs `ஐ` and `ஔ` are canonically 2 morae in isolation.
     - Pure consonants (*Mei*) with pulli virama (`U+0BCD`) = 0.5 mora.
     - Aytham (`U+0B83`) = 0.5 mora.
     - Non-Tamil / unclassified characters = 0.0 mora.
- **Rationale**:
  - Providing both enum classification and numeric mora representation satisfies both high-level grammatical classification (e.g. prosody rules checking for `is_kuril`) and numerical timing calculation (e.g. speech synthesis, verse meter sum).
- **Alternatives Considered**:
  - *Float-only*: Floating point numbers alone lose the qualitative linguistic distinction between a Mei (0.5 mora) and an Aytham (0.5 mora).
  - *Integer-only*: Integers cannot represent fractional morae (0.5 for Mei/Aytham) without scaling (e.g. half-mora units). Providing both exact float and rational representations avoids precision issues.

---

### Topic 2: Homorganic Cognate Letter Mapping (*Ina Ezhuthu*)

- **Context**: Classical Tamil grammar groups sounds by phonetic affinity (*Ina Ezhuthu*).
- **Grammatical Sourcing**:
  - *Tolkappiyam Ezhuthathikaram* (Pirappiyal) & *Nannool* (Sutras 75–76):
    - 6 Hard Stops (*Vallinam*) pair with 6 Nasals (*Mellinam*):
      - `க்` $\leftrightarrow$ `ங்` (velar: ககரத்திற்கு ஙகரம் இனம்)
      - `ச்` $\leftrightarrow$ `ஞ்` (palatal: சகரத்திற்கு ஞகரம் இனம்)
      - `ட்` $\leftrightarrow$ `ண்` (retroflex: டகரத்திற்கு ணகரம் இனம்)
      - `த்` $\leftrightarrow$ `ந்` (dental: தகரத்திற்கு நகரத்திற்கு இனம்)
      - `ப்` $\leftrightarrow$ `ம்` (labial: பகரத்திற்கு மகரம் இனம்)
      - `ற்` $\leftrightarrow$ `ன்` (alveolar: றகரத்திற்கு னகரம் இனம்)
    - 6 Medium consonants (*Idaiyinam*: `ய், ர், ல், வ், ழ், ள்`) form their own harmonious group; they do not have nasal cognates.
    - Vowels pair by quantity:
      - `அ` $\leftrightarrow$ `ஆ`
      - `இ` $\leftrightarrow$ `ஈ`
      - `உ` $\leftrightarrow$ `ஊ`
      - `எ` $\leftrightarrow$ `ஏ`
      - `ஒ` $\leftrightarrow$ `ஓ`
      - `ஐ` $\leftrightarrow$ `இ` (Nannool Sutra 76: "ஐகாரத்திற்கு இகரமும்")
      - `ஔ` $\leftrightarrow$ `உ` (Nannool Sutra 76: "ஔகாரத்திற்கு உகரமும் இனமாகும்")
- **Decision**:
  - Implement bidirectional functions:
    - `get_cognate(letter: &str) -> Option<String>`
    - `are_cognates(letter1: &str, letter2: &str) -> bool`
  - Per Clarification Session 2026-11-08: If composite *Uyirmei* letters are provided (e.g., `கா`, `கி`), decompose into base consonant + vowel sign, translate the base consonant to its cognate partner, and recombine with the original vowel sign (`கா` $\rightarrow$ `ஙா`, `கி` $\rightarrow$ `ஙி`).
- **Rationale**:
  - Real-world NLP pipelines (like Sandhi checkers) operate on words in surface Uyirmei form. Decomposing and recomposing seamlessly eliminates repetitive caller-side boilerplate.
- **Alternatives Considered**:
  - *Consonant-only table*: Requires caller to split Uyirmei, handle errors, look up root, and recompose manually. Rejected per user clarification.

---

### Topic 3: Orthographic Syllable Nucleus (*Olippasai*) Segmentation

- **Context**: Extracting natural sound units (syllable nuclei) from running text to serve as the single source of truth across `tamil-hyphen`, `tamil-yaappu`, and `tamil-phonetics`.
- **Phonotactic Syllable Structure**:
  - Standard Tamil syllable shape: `(C*) V (C*)`
    - Onset: Optional consonants (`C*`), including Grantha or loanword onset clusters (e.g. `ஸ்டா`, `ப்ரி`).
    - Nucleus: Essential vowel core `V` (independent Uyir or Uyirmei base).
    - Coda: Zero or more pure consonants (`Mei` with pulli) or Aytham (`ஃ`).
- **Decision**:
  - Syllable extraction algorithm:
    1. Iterate through tailored grapheme clusters (`Letters`).
    2. Group an optional onset sequence + mandatory vowel nucleus.
    3. Consume all immediately following pure consonants (*Mei*) and Aytham characters as codas.
    4. If a word starts with an initial consonant cluster before any vowel (e.g., loanword `ஸ்டார்`), attach the initial consonants to the first vowel nucleus as an onset cluster.
    5. Yield an `Olippasai` struct containing:
       - `text: &'a str` (borrowed zero-allocation slice)
       - `start_byte: usize`, `end_byte: usize`
       - `start_letter_idx: usize`, `end_letter_idx: usize`
       - `has_coda: bool`
       - `coda_count: usize`
- **Rationale**:
  - Zero-allocation iteration over borrowed string slices matches Principle VII of the Constitution.
  - Slicing strictly by Unicode character and byte offsets preserves ZWJ, ZWNJ, spaces, and punctuation byte-for-byte.
- **Alternatives Considered**:
  - *Allocating `Vec<String>` per syllable*: Rejected for hot loop performance; borrowed slices and zero-allocation iterators (`OlippasaiIter<'a>`) provide superior throughput and zero heap pressure.

---

### Topic 4: Grantha Ligature & Formatting Invariance

- **Context**: Handling atomic Grantha ligatures (`க்ஷ` *ksha*, `ஸ்ரீ` / `ஶ்ரீ` *shri*) and format controls (`U+200C` ZWNJ, `U+200D` ZWJ).
- **Decision**:
  - Respect existing `tables::ATOMIC_LETTERS` in `tamil-core`:
    - `க்ஷ` is an atomic letter unit: base quantity is *Kuril* (1 mora); `க்ஷா` is *Nedil* (2 morae); `க்ஷ்` is *Mei* (0.5 mora).
    - `ஸ்ரீ` is an atomic letter unit: base quantity is *Nedil* (2 morae).
  - Format controls (ZWJ, ZWNJ) are preserved inside whatever grapheme cluster / span they inhabit, without altering the phonological classification.
- **Rationale**:
  - Maintains strict compliance with Constitution Principle II ("Inspect Tamil by Scalars, No Visual Guesses").

---

## 2. Summary of Design Constraints

| Component | Architecture Rank | Memory Policy | Concurrency / Thread Safety |
|---|---|---|---|
| `LetterQuantity` | `Rank 0` (`crates/tamil-core`) | `Copy`, zero-allocation | Immutable, `Send + Sync` |
| `InaEzhuthu` | `Rank 0` (`crates/tamil-core`) | Static lookup tables | Immutable, zero allocation |
| `Olippasai` | `Rank 0` (`crates/tamil-core`) | Borrowed slices `&'a str` | Zero-allocation iterator |
| Tri-Runtime Bindings | `Rank 6` (`bindings/*`) | JSON dispatcher & typed FFI | Safe serialization |
