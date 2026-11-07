# Phase 1 Data Model: Canonical Prosodic & Syllabic Tamil Hyphenation Rules (`015-canonical-tamil-hyphenation`)

## Entities

### 1. `LetterClass` (Orthographic Role of a Tailored Tamil Letter)

| Variant | Description | Examples |
|---------|-------------|----------|
| `Uyir` | Independent Tamil vowel (`U+0B85`–`U+0B94`) | `அ`, `ஆ`, `இ`, `ஈ`, `உ` |
| `Uyirmei` | Consonant + vowel composite (inherent `அ` or dependent vowel sign `U+0BBE`–`U+0BCC`) | `க`, `கா`, `கி`, `கை`, `கொ`, `கௌ` |
| `Mei` | Pure consonant with pulli (`U+0BCD`) | `க்`, `த்`, `ம்`, `ழ்`, `ன்` |
| `Aytham` | Tamil Aytham (`U+0B83`) | `ஃ` |
| `AtomicGrantha` | Indivisible Grantha conjunct onset (`க்ஷ` + vowel/pulli, `ஸ்ரீ`, `ஶ்ரீ`) | `க்ஷ`, `க்ஷி`, `ஸ்ரீ`, `ஶ்ரீ` |
| `Other` | Non-Tamil character, digit, symbol, or punctuation | `1`, `-`, `a` |

---

### 2. `RawSyllable` (*Olippasai* — Phonetic Syllable Unit)

| Field | Type | Validation / Invariant |
|-------|------|------------------------|
| `letters` | `Vec<&str>` / `string[]` | 1 vowel-bearing onset (`Uyir`, `Uyirmei`, or `AtomicGrantha`) followed by $0..N$ contiguous `Mei` (`\u0BCD`) or `Aytham` (`\u0B83`) coda letters. |
| `start_letter_idx` | `usize` | 0-based index of the first tailored letter in the word. |
| `end_letter_idx` | `usize` | Exclusive index of the last tailored letter (`start_letter_idx + letters.len()`). |
| `has_coda` | `bool` | `true` iff the final letter in `letters` is `Mei` or `Aytham` (closed syllable). |

---

### 3. `AsaiSegment` (Prosodic Hyphenation Segment)

| Field | Type | Validation / Invariant |
|-------|------|------------------------|
| `letters` | `Vec<&str>` / `string[]` | Contiguous tailored Tamil letters formed by grouping `RawSyllable` units via the 5-step *Asai* algorithm. |
| `start_letter_idx` | `usize` | 0-based tailored letter start index. |
| `end_letter_idx` | `usize` | Exclusive tailored letter end index. |
| `letter_count` | `usize` | `end_letter_idx - start_letter_idx`. Must satisfy: first segment $\ge \text{left\_min}$, last segment $\ge \text{right\_min}$, internal segments $\ge \min(\text{left\_min}, \text{right\_min})$. |

---

### 4. `HyphenationConfig`

| Field | Type | Default | Validation Rule |
|-------|------|---------|-----------------|
| `delimiter` | `String` | `"\u{00AD}"` (Soft Hyphen) | Non-empty delimiter string inserted at break points. |
| `left_min` | `usize` | `3` | Must be $\ge 1$. Controls minimum tailored Tamil letters in the first segment. |
| `right_min` | `usize` | `3` | Must be $\ge 1$. Controls minimum tailored Tamil letters in the final (next-line) segment. |

---

### 5. `HyphenationPoint` & `HyphenationResult`

| Entity | Fields | Invariants |
|--------|--------|------------|
| `HyphenationPoint` | `letter_index: usize`, `scalar_offset: usize`, `byte_offset: usize` | Strictly increasing offsets within the NFC-normalized, pre-cleaned word. |
| `HyphenationResult` | `original: String`, `hyphenated: String`, `segments: Vec<String>`, `points: Vec<HyphenationPoint>` | `segments.join(&config.delimiter) == hyphenated` and `segments.concat() == original`. |
