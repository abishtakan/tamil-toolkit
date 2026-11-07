# Feature Specification: Canonical Prosodic & Syllabic Tamil Hyphenation Rules (`canonical-tamil-hyphenation`)

**Feature Branch**: `[015-canonical-tamil-hyphenation]`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "what you found. Also research whether leftmin rightmin which is best 2 or 3. if 3 is best change it to 3."

## Clarifications

### Session 2026-11-08

- Q: Should this feature also update the core Rust crate (`crates/tamil-hyphen`), Python/WASM bindings, and golden test suite (`tests/golden/hyphen.jsonl`) to match the new 5-step Tamil *Asai* + `left_min = 3, right_min = 3` rules alongside the Word Add-in and Playground? (FR-002) → A: Option A — Full parity across `crates/tamil-hyphen`, `tests/golden/hyphen.jsonl`, Python/WASM bindings, Word Add-in, and Playground.
- Q: When a caller or user explicitly configures custom `left_min` and `right_min` values (e.g., in `HyphenConfig` or the Word Add-in taskpane), how should the *Asai* segment merge rules and minimum word length behave? (FR-001) → A: Option A — Dynamic scaling from `(left_min, right_min)` with `3, 3` (`min_word_letters = 6`) as the default.
- Q: Should the specification declare the 5-step Tamil *Asai* hyphenation rules as dialect-invariant across all regional Tamil varieties (`ta-IN` Tamil Nadu and `ta-LK` Sri Lankan / Jaffna / Batticaloa / Diaspora Tamil), or include dialect-specific overrides? → A: Option A — Dialect-invariant across `ta-IN` and `ta-LK`, backed by golden test vectors from both regions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminating Short-Word Breaks & 2-Letter Next-Line Orphans (`left_min = 3, right_min = 3`) (Priority: P1)

A Tamil author, editor, or desktop publisher justifying Tamil paragraphs in Microsoft Word, LibreOffice, or web layouts needs:
1. **Short words ($< 6$ tailored Tamil letters)**—such as `உலகம்` (4), `சமூகம்` (4), `வணிகம்` (4), `திட்டம்` (4), `வரலாறு` (4), `தலைமுறை` (4), `அறிவியல்` (5), `விவசாயம்` (5), and `பாதுகாக்க` (5)—to remain **100% unbroken**.
2. **Bigger words ($\ge 6$ tailored Tamil letters)** to **never strand a 2-letter fragment on the next line** (such as `-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`, `-கோள்`, `-தூர்`, `-துறை`) or leave a 2-letter stub before a break (`பல்-`, `கண்-`, `இன்-`, `மக்-`, `பள்-`).

**Why this priority**:
- When a 2-letter suffix (`-கம்`, `-பம்`, `-றல்`, `-கள்`, `-யம்`) wraps onto the next line, it consists of only 1 vowel + 1 pulli consonant (1.5 *maathirai*), creating a visually jarring 2-letter orphan at the start of the new line while saving only ~1 glyph width on the previous line (since the `-` hyphen itself occupies ~1 glyph width).
- Enforcing **`left_min = 3, right_min = 3`** and a **minimum segment length of 3 tailored letters** across all Tamil *Asai* segments guarantees that every part of a broken word—on the current line, in the middle, and on the next line—is at least 3 tailored letters long.

**Independent Test**: Can be tested across all 53 benchmark words and the 114-word golden corpus by verifying that zero words $< 6$ letters break, and 100% of segments in broken words contain $\ge 3$ tailored Tamil letters.

**Acceptance Scenarios**:

1. **Given** any Tamil word with fewer than 6 tailored Tamil letters (`உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `அறிவியல்`, `விவசாயம்`, `பாதுகாக்க`), **When** hyphenating with default settings (`left_min = 3, right_min = 3`), **Then** the word is returned completely unbroken.
2. **Given** bigger words ending in 2-letter closed syllables (`தொழில்நுட்பம்`, `படைப்பாற்றல்`, `பல்கலைக்கழகம்`, `ஓலைச்சுவடிப்`, `பதிப்புகளைப்`, `செயற்கைக்கோள்`, `பாரம்பரியம்`, `கோயம்புத்தூர்`, `பருத்தித்துறை`), **When** hyphenating with default settings (`left_min = 3, right_min = 3`), **Then** the 2-letter ending merges with the preceding *Asai* so the next line always receives at least 3–4 letters (`தொழில்-நுட்பம்`, `படைப்-பாற்றல்`, `பல்கலைக்-கழகம்`, `ஓலைச்-சுவடிப்`, `பதிப்-புகளைப்`, `செயற்-கைக்கோள்`, `பாரம்-பரியம்`, `கோயம்-புத்தூர்`, `பருத்-தித்துறை`).

---

### User Story 2 - 5-Step Tamil *Asai* (`நேரசை` / `நிரையசை`) + 3-Letter Segment Grouping (Priority: P2)

To ensure bigger words break at natural Tamil syllable boundaries without ever producing 1-letter or 2-letter pieces, the engine partitions words using a deterministic 5-step Tamil *Asai* algorithm:
1. **Participle Stem Binding**: A word-initial 2-letter closed syllable (`CVC`, such as `கண்`, `இன்`, `கன்`) followed by a 1-letter `-உ` or `-இ` (*குற்றியலுகரம்* / *வினையெச்ச இகரம்*, such as `டு`, `றி`, `னி`) binds into a 3-letter stem (`கண்டு-பிடிப்பு`, `இன்றி-யமையாத`, `கன்னி-யாகுமரி`).
2. **Forward *Nirai-asai* Grouping**: Any remaining 1-letter open syllable (having no pulli *Mei* or *Aytham* coda) joins forward with the following syllable (`"குறில் தனித்து அசையாகாது"` $\rightarrow$ `கலைக்`, `கழ`, `திருச்`, `சிராப்`, `ஒருங்`, `கிணைக்`).
3. **Next-Line Tail Merge (`right_min = 3`)**: While the final *Asai* has fewer than 3 tailored letters (`-கம்`, `-பம்`, `-றல்`, `-யம்`, `-கள்`), it merges into the preceding *Asai* (`கழ` + `கம்` $\rightarrow$ `கழகம்`, `நுட்` + `பம்` $\rightarrow$ `நுட்பம்`).
4. **Current-Line Head Merge (`left_min = 3`)**: While the first *Asai* has fewer than 3 tailored letters (`பல்`, `பள்`, `மட்`, `நாக`), it merges into the second *Asai* (`பல்` + `கலைக்` $\rightarrow$ `பல்கலைக்`, `பள்` + `ளிக்` $\rightarrow$ `பள்ளிக்`).
5. **Internal Segment Merge (`min_seg = 3`)**: Any internal *Asai* with fewer than 3 tailored letters merges with its adjacent neighbor (preferring an open neighbor over a closed *Mei* coda) so no 2-letter middle segment ever occurs.

**Why this priority**: Combines classical Tamil *Asai* prosody with strict 3-letter minimum visual weight on every line.

**Independent Test**: Can be tested by verifying that `பல்கலைக்கழகம்` $\rightarrow$ `பல்கலைக்-கழகம்`, `பல்கலைக்கழகங்களில்` $\rightarrow$ `பல்கலைக்-கழகங்-களில்`, `திருச்சிராப்பள்ளி` $\rightarrow$ `திருச்-சிராப்-பள்ளி`, and `ஒருங்கிணைக்கப்பட்ட` $\rightarrow$ `ஒருங்-கிணைக்-கப்பட்ட`.

**Acceptance Scenarios**:

1. **Given** `பல்கலைக்கழகம்` (9 letters) and `பல்கலைக்கழகங்களில்` (12 letters), **When** hyphenated, **Then** they break into $\ge 3$-letter *Asai* segments as **`பல்கலைக்-கழகம்`** and **`பல்கலைக்-கழகங்-களில்`**.
2. **Given** `திருச்சிராப்பள்ளி` (9 letters) and `ஒருங்கிணைக்கப்பட்ட` (11 letters), **When** hyphenated, **Then** they break into $\ge 3$-letter *Asai* segments as **`திருச்-சிராப்-பள்ளி`** and **`ஒருங்-கிணைக்-கப்பட்ட`**.

---

### User Story 3 - Automatic Healing & Cache Invalidation in the Word Add-in (Priority: P3)

A user who previously hyphenated a Word document needs re-running "Hyphenate Document" or "Remove Hyphens" in the Word Add-in to automatically strip all old `<w:softHyphen/>` tags and re-apply the new `left_min = 3, right_min = 3` Tamil *Asai* rules immediately.

**Why this priority**: Ensures existing documents are immediately healed in a single click.

**Independent Test**: Can be tested by passing OOXML containing `<w:t>உல</w:t><w:softHyphen/><w:t>கம்</w:t>` into `hyphenateOoxml()` and verifying that `உலகம்` is merged back into a single unbroken `<w:t>உலகம்</w:t>`.

**Acceptance Scenarios**:

1. **Given** Word OOXML containing previously hyphenated short words (`<w:t>உல</w:t><w:softHyphen/><w:t>கம்</w:t>`), **When** `hyphenateOoxml()` runs, **Then** the `<w:softHyphen/>` inside `உலகம்` is removed and `உலகம்` remains unbroken.

---

### Edge Cases

- **Multi-Consonant Coda Clusters (Geminate & Conjunct Codas)**: Words with 2 consecutive pure consonants with pulli (such as `வாழ்த்துகள்`, `ஆராய்ச்சிகள்`, `துர்ப்பிரயோகம்`) bind all contiguous pulli letters and *Aytham* (`ஃ`) to the preceding vowel nucleus (`வாழ்த்-துகள்`, `ஆராய்ச்-சிகள்`, `துர்ப்-பிரயோகம்`).
- **6-Letter Words Whose *Asai* Segments Cannot Split into $\ge 3 + \ge 3$**: Words like `முன்னேற்றம்` (`முன்` [2] + `னேற்` [2] + `றம்` [2]), `நீதிமன்றம்` (`நீதி` [2] + `மன்` [2] + `றம்` [2]), `செய்தார்கள்` (`செய்` [2] + `தார்` [2] + `கள்` [2]), and `திண்டுக்கல்` (`திண்` [2] + `டுக்` [2] + `கல்` [2]) have three 2-letter *Asais*; merging any 2-letter tail/head leaves a single unbroken 6-letter word (`முன்னேற்றம்`, `நீதிமன்றம்`, `செய்தார்கள்`, `திண்டுக்கல்`) rather than splitting inside an *Asai* or leaving a 2-letter orphan.
- **Atomic Grantha Conjuncts**: Sequences `க்ஷ` (plus any vowel sign or pulli) and `ஸ்ரீ` / `ஶ்ரீ` are treated as a single indivisible tailored letter and syllable onset.
- **Zero-Width Joiners (`ZWJ` / `ZWNJ`)**: Words containing `U+200D` or `U+200C` are never split across a break boundary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (5-Step Tamil *Asai* + Minimum Segment Partitioning)**: The hyphenation engine MUST partition words into raw phonetic nuclei (vowel nucleus + contiguous *Mei* `\u0BCD` / *Aytham* `\u0B83` codas), bind word-initial `CVC + u/i` stems, group 1-letter open nuclei forward into *Nirai-asai* units, and merge any tail (`< right_min`), head (`< left_min`), or internal (`< min(left_min, right_min)`) *Asai* dynamically from the active `(left_min, right_min)` configuration (default `3, 3`, minimum word threshold `left_min + right_min = 6`).
- **FR-002 (Default Margins `left_min = 3, right_min = 3`, `MIN_WORD_LETTERS = 6`, & Cross-Runtime Parity)**: The default leading margin (`left_min`) and trailing margin (`right_min`) MUST be **`3` tailored Tamil letters** across the core Rust crate (`crates/tamil-hyphen`), Python/WASM bindings, golden test suite (`tests/golden/hyphen.jsonl`), Word Add-in, and Playground. Any word with $< 6$ tailored Tamil letters MUST NOT be hyphenated.
- **FR-003 (Zero 2-Letter Next-Line Orphans)**: A hyphenation break MUST NEVER leave fewer than 3 tailored Tamil letters on the next line (`right_min = 3`), eliminating 2-letter next-line orphans (`-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`).
- **FR-004 (Line-Start & Cluster Integrity)**: A hyphenation break MUST NEVER be placed before a pulli (`்`), pure consonant (*Mei*), *Aytham* (`ஃ`), or dependent vowel sign, and MUST NEVER split multi-consonant coda clusters (`வாழ்த்`, `ராய்ச்`), atomic Grantha sequences (`க்ஷ`, `ஸ்ரீ`, `ஶ்ரீ`), or `ZWJ`/`ZWNJ` sequences.
- **FR-005 (Idempotent Healing of Existing Hyphens)**: Before inserting new break points, the engine MUST strip any existing soft hyphens (`U+00AD`), optional hyphens (`U+001F`), zero-width spaces (`U+200B`), and `<w:softHyphen/>` OOXML elements.
- **FR-006 (Pluricentric Dialect Invariance)**: The 5-step Tamil *Asai* hyphenation rules MUST be orthographically invariant across Tamil Nadu (`ta-IN`), Sri Lanka (`ta-LK`, including Jaffna, Batticaloa, Vanni, and Up-Country), and global diaspora Tamil, verified by golden test vectors covering regional toponyms and inflections (e.g., `யாழ்ப்பாணம்` $\rightarrow$ `யாழ்ப்-பாணம்`, `மட்டக்களப்பு` $\rightarrow$ `மட்டக்-களப்பு`, `திருச்சிராப்பள்ளி` $\rightarrow$ `திருச்-சிராப்-பள்ளி`, `கோயம்புத்தூர்` $\rightarrow$ `கோயம்-புத்தூர்`).

### Key Entities

- **Phonetic Syllable (*Olippasai*)**: A single vowel-bearing Tamil letter (*Uyir*, *Uyirmei*, or atomic Grantha onset) together with all immediately following contiguous *Mei* (pulli) and *Aytham* coda letters.
- **Prosodic Hyphenation Segment (*Asai* Segment)**: One or more contiguous phonetic syllables grouped via Tamil *Asai* rules (`நேரசை` / `நிரையசை`) and merged so that every segment contains at least `min_seg_letters = 3` tailored Tamil letters.
- **Short-Word Threshold (`MIN_WORD_LETTERS = 6`)**: Minimum number of tailored Tamil letters required before a word is eligible for hyphenation.
- **Edge Margins (`left_min = 3, right_min = 3`)**: Minimum number of tailored Tamil letters required before the first break point and after the last break point inside a hyphenated ($\ge 6$-letter) word.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: **100% of short Tamil words with $< 6$ tailored letters** (including `உலகம்`, `சமூகம்`, `வணிகம்`, `திட்டம்`, `வரலாறு`, `தலைமுறை`, `அறிவியல்`, `விவசாயம்`, `முடிவுகள்`, `பாதுகாக்க`, `வேண்டியது`, `மரபாகும்`) remain **completely unbroken**.
- **SC-002**: **100% of broken Tamil words ($\ge 6$ tailored letters)** produce **zero 1-letter or 2-letter segments** on the current line, in the middle, or on the next line (eliminating 2-letter next-line orphans like `-கம்`, `-பம்`, `-றல்`, `-றம்`, `-யம்`, `-கள்`, `-கல்`, `-டிப்`), while cleanly breaking compound and polysyllabic words at natural Tamil *Asai* boundaries (`பல்கலைக்-கழகம்`, `பல்கலைக்-கழகங்-களில்`, `தொழில்-நுட்பம்`, `படைப்-பாற்றல்`, `கண்டு-பிடிப்பு`, `இன்றி-யமையாத`, `திருச்-சிராப்-பள்ளி`, `ஒருங்-கிணைக்-கப்பட்ட`).
- **SC-003**: **0 instances** of line-initial pure consonants (*Mei* with pulli), *Aytham* (`ஃ`), or split multi-consonant pulli clusters (`*வாழ்-த்துகள்`) occur across the entire test corpus.

## Assumptions

- Short Tamil words ($< 6$ tailored letters) wrap cleanly onto the next line in justified paragraphs without creating noticeable whitespace rivers.
- For bigger words ($\ge 6$ tailored letters), a 2-letter fragment on the next line (1 Uyirmei + 1 pulli Mei = 1.5 *maathirai*) saves only ~1 glyph width on the current line while creating an awkward 2-letter orphan on the next line; merging any $< 3$-letter *Asai* guarantees every line break carries at least 3 tailored letters of visual and prosodic weight.
