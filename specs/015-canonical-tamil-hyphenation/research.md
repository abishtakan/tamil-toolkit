# Phase 0 Research: Canonical Prosodic & Syllabic Tamil Hyphenation Rules (`015-canonical-tamil-hyphenation`)

## Decision 1: Default Margins (`left_min = 3, right_min = 3`, `MIN_WORD_LETTERS = 6`)

- **Decision**: Change the default leading and trailing hyphenation margins from `left_min = 2, right_min = 2` to **`left_min = 3, right_min = 3`** (requiring a minimum word length of `left_min + right_min = 6` tailored Tamil letters before any word is eligible for hyphenation).
- **Rationale**:
  1. **Short Tamil words ($< 6$ tailored letters)**—such as `உலகம்` (4), `சமூகம்` (4), `வணிகம்` (4), `திட்டம்` (4), `வரலாறு` (4), `தலைமுறை` (4), `அறிவியல்` (5), `விவசாயம்` (5), and `பாதுகாக்க` (5)—wrap cleanly onto the next line in justified paragraphs without creating noticeable whitespace rivers. Under `2/2`, they were split into tiny 2-letter stubs (`உல-கம்`, `திட்-டம்`, `சமூ-கம்`).
  2. **2-letter fragments on the next line look visually unbalanced**: Common Tamil suffixes (`-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`) consist of 1 *Uyirmei* + 1 pulli *Mei* (`1.5` *maathirai*). Replacing a 2-letter suffix with a `-` hyphen on Line 1 saves only ~1 glyph width while stranding a tiny 2-letter orphan at the start of Line 2.
- **Alternatives Considered**:
  - `left_min = 2, right_min = 2` (TeX `hyph-ta.tex` technical minimum): Rejected as default because it over-hyphenates 4-letter and 5-letter stems and leaves 2-letter next-line orphans (`-கம்`, `-பம்`, `-றல்`).
  - `left_min = 2, right_min = 2` with `MIN_WORD_LETTERS = 6`: Rejected because even on $\ge 6$-letter words (`தொழில்நுட்பம்`, `படைப்பாற்றல்`, `பல்கலைக்கழகம்`), it stranded 2-letter suffixes (`-பம்`, `-றல்`, `-கம்`) on the next line.

---

## Decision 2: 5-Step Tamil *Asai* (`நேரசை` / `நிரையசை`) + Minimum Segment Partitioning

- **Decision**: Partition words ($\ge \text{left\_min} + \text{right\_min}$ tailored Tamil letters) using a deterministic 5-step prosodic syllable (*Asai*) algorithm:
  1. **Raw Phonetic Syllable Extraction (*Olippasai*)**: Group each vowel-bearing letter (*Uyir*, *Uyirmei*, or atomic Grantha `க்ஷ` / `ஸ்ரீ` / `ஶ்ரீ`) with all immediately following contiguous pure consonants (*Mei* with pulli `\u0BCD`) and *Aytham* (`\u0B83`).
  2. **Participle Stem Binding**: Bind a word-initial 2-letter closed syllable (`CVC`, e.g., `கண்`, `இன்`, `கன்`) with an immediately following 1-letter open `-உ` or `-இ` (*குற்றியலுகரம்* / *வினையெச்ச இகரம்*, e.g., `டு`, `றி`, `னி`) into a 3-letter stem (`கண்டு-பிடிப்பு`, `இன்றி-யமையாத`, `கன்னி-யாகுமரி`).
  3. **Forward *Nirai-asai* Grouping**: Join any remaining 1-letter open syllable (no pulli *Mei* or *Aytham* coda) forward with the next syllable (`"குறில் தனித்து அசையாகாது"` $\rightarrow$ `கலைக்`, `கழ`, `திருச்`, `சிராப்`, `ஒருங்`, `கிணைக்`).
  4. **Edge & Internal Segment Merging**:
     - **Next-Line Tail Merge**: While the final *Asai* has $< \text{right\_min}$ tailored letters, merge it into the preceding *Asai* (`கழ` + `கம்` $\rightarrow$ `கழகம்`, `நுட்` + `பம்` $\rightarrow$ `நுட்பம்`).
     - **Current-Line Head Merge**: While the first *Asai* has $< \text{left\_min}$ tailored letters, merge it into the second *Asai* (`பல்` + `கலைக்` $\rightarrow$ `பல்கலைக்`, `பள்` + `ளிக்` $\rightarrow$ `பள்ளிக்`).
     - **Internal Segment Merge**: Merge any internal *Asai* shorter than $\min(\text{left\_min}, \text{right\_min})$ with its adjacent neighbor (preferring an open neighbor over a closed *Mei* coda).
  5. **Emit Break Points**: Emit break points between the resulting segments that satisfy `left_count >= left_min`, `right_count >= right_min`, and no `ZWJ`/`ZWNJ` across the boundary.
- **Rationale**: Guarantees that every break occurs at a genuine Tamil *Asai* boundary AND every segment (left, middle, and right) has at least 3 tailored letters under default settings.
- **Alternatives Considered**:
  - Raw letter-window slicing (`left_min = 3, right_min = 3` on ungrouped *Olippasai*): Rejected because it split after 1-letter open syllables (`*பல்க-லைக்கழகம்`, `*தொழில்நுட்-பம்` $\rightarrow$ no break at all on `தொழில்நுட்பம்` or awkward mid-stem splits like `*படைப்பா-ற்றல்`).

---

## Decision 3: Multi-Consonant Coda Clusters & Idempotent OOXML Healing

- **Decision**:
  - Attach **all** contiguous *Mei* (`\u0BCD`) and *Aytham* (`\u0B83`) letters to the preceding vowel nucleus (`while` loop rather than single `if`), keeping `வாழ்த்-துகள்` and `ஆராய்ச்-சிகள்` intact.
  - Strip existing soft hyphens (`\u00AD`, `\u001F`, `\u200B`) and `<w:softHyphen/>` tags before re-evaluating words in both text and OOXML modes.
- **Rationale**: Prevents invalid line-initial pulli consonants (`*வாழ்-த்துகள்`) and heals previously hyphenated Word documents in a single click.
