# Feature Specification: Syllable and Orthographic Boundary Hyphenation (`tamil-hyphen`)

**Feature Branch**: `009-tamil-hyphen`

**Created**: 2026-11-05

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "tamil-hyphen"

## Clarifications

### Session 2026-11-05

- Q: When wrapping, what happens to a word longer than the line width that has no valid break point (long Latin word, URL, or a Tamil word where every break violates `left_min`/`right_min`)? → A: Non-Tamil tokens and URLs are outside hyphenation scope and handled by host/browser default wrapping; for Tamil words without valid break points, keep the word intact without forcing an invalid orthographic break.
- Q: When a Tamil word already contains author-placed soft hyphens (U+00AD), what should paragraph hyphenation do? → A: Keep the author's soft hyphens and also add automatic breaks at any other valid points, never producing duplicate adjacent soft hyphens.
- Q: Should the hyphenation test suite be active (counted as passing) immediately or planned until owner review? → A: Planned: rules and vectors ship, but the suite stays excluded from active counts until the owner reviews and approves activation.
- Q: May a break be placed directly before or after a ZWJ/ZWNJ inside a Tamil word? → A: No; never break immediately before or after a joiner, and the letter sequence around it stays together.
- Q: Which characters form a hyphenatable Tamil word during paragraph scanning? → A: Only a contiguous run of Tamil letters (including Grantha letters, vowel signs, pulli, aytham); Tamil digits, Tamil symbols, punctuation, apostrophes, explicit hyphens, and non-Tamil text end the word and are never hyphenated.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Orthographic & Syllabic Word Hyphenation (Priority: P1) 🎯 MVP

As a digital publisher, typographer, e-book reader developer, or web application author working with Tamil text, I want to identify valid syllable-level hyphenation break points within Tamil words and optionally insert soft hyphens (`U+00AD`) or visible markers, so that multi-column layouts, narrow mobile screens, and justified paragraphs can wrap long Tamil words cleanly without splitting grapheme clusters, stranding pure consonants (*Mei* / pulli letters), or breaking grammatical ligatures.

**Why this priority**: Tamil words—especially agglutinative forms and compound nouns—frequently exceed narrow column widths in newspapers, mobile UIs, and PDFs. Standard Western line-breaking algorithms either refuse to break Tamil words (causing severe layout overflow or wide justification gaps) or break arbitrarily between Unicode scalar values, corrupting rendered syllables. Providing deterministic, rule-based syllable boundary identification solves the core typographic problem immediately.

**Independent Test**: Can be independently tested by passing standard Tamil words (containing *Uyir*, *Mei*, *Uyirmei*, *Aytham*, and Grantha letters) to the hyphenation engine and verifying that returned break indices and hyphenated strings never leave a pure consonant (*Mei*) or *Aytham* at the start of a new line segment, never split an *Uyirmei* cluster, and respect minimum lead/trail letter thresholds.

**Acceptance Scenarios**:

1. **Given** a multi-syllable Tamil word containing closed syllables (an *Uyir* or *Uyirmei* followed by one or more *Mei* consonants, such as `\u{0BAA}\u{0B9F}\u{0BCD}\u{0B9F}\u{0BAE}\u{0BCD}` or `\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}\u{0BA8}\u{0BBE}\u{0B9F}\u{0BC1}`), **When** requesting hyphenation break points, **Then** every *Mei* (pure consonant with pulli) remains attached to the preceding vowel-bearing letter (*Uyir* or *Uyirmei*) as a syllable coda, and break points are placed only after the coda and before the next vowel-bearing onset (*Uyirmei* or *Uyir*).
2. **Given** a Tamil word with open syllables (consecutive *Uyirmei* letters such as `\u{0B85}\u{0BA4}\u{0BBF}\u{0B95}\u{0BBE}\u{0BB0}\u{0BAE}\u{0BCD}`), **When** requesting hyphenation break points, **Then** valid break opportunities are identified between open syllables while respecting configured minimum leading (`left_min`) and trailing (`right_min`) letter counts.
3. **Given** a Tamil word and a custom or default delimiter (such as soft hyphen `U+00AD` or visible ASCII `-`), **When** formatting the hyphenated word, **Then** the delimiter is inserted exclusively at the validated syllable break boundaries without altering any underlying Tamil characters or normalization forms.
4. **Given** words containing atomic Grantha ligatures (`\u{0B95}\u{0BCD}\u{0BB7}` *Ksha*, `\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}` or `\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}` *Shri*), **When** computing hyphenation segments, **Then** the atomic ligature is treated as a single indivisible Tamil letter and is never split internally.

---

### User Story 2 - Paragraph & Mixed-Text Soft Hyphenation and Line-Width Wrapping (Priority: P2)

As a content management system or document preparation pipeline developer, I want to process full Tamil sentences and mixed-script paragraphs (containing Tamil words, English words, numerals, punctuation, and invisible joiners) to either inject soft hyphens (`U+00AD`) throughout the text or wrap lines to a target character/letter width, so that downstream renderers (browsers, PDF engines, terminal displays, and e-readers) can render justified Tamil text automatically.

**Why this priority**: Real-world documents rarely consist of isolated single words; users need to pass entire paragraphs or articles and receive text with non-Tamil tokens, punctuation, whitespace, and existing formatting preserved intact.

**Independent Test**: Can be independently tested by passing a mixed Tamil/English paragraph with punctuation and numbers into the text hyphenator and line wrapper, verifying that Tamil tokens receive valid syllable breaks, non-Tamil tokens and punctuation remain untouched, and wrapped lines respect the maximum letter width using hyphenation only when a word crosses the line boundary.

**Acceptance Scenarios**:

1. **Given** a paragraph containing Tamil words, Latin text, digits, and punctuation, **When** applying paragraph hyphenation, **Then** only contiguous Tamil word tokens are hyphenated at valid syllable boundaries while whitespace, punctuation, numbers, and non-Tamil script segments are preserved verbatim.
2. **Given** a Tamil sentence and a maximum line width (measured in tailored Tamil letters / grapheme clusters), **When** wrapping text to lines, **Then** words that fit on the current line remain unbroken, and words that exceed the remaining line capacity are broken at the latest valid hyphenation boundary that fits (including the trailing hyphen marker).
3. **Given** input text containing Zero-Width Joiner (`ZWJ`, `U+200D`) or Zero-Width Non-Joiner (`ZWNJ`, `U+200C`), **When** hyphenating or wrapping the text, **Then** all joiner code points are strictly preserved and no hyphenation break is introduced inside a joiner-linked sequence.

---

### User Story 3 - Cross-Platform Consistency & Regional Dialect Invariance (Priority: P3)

As an application author building server, web, desktop, or mobile experiences for Tamil readers across Tamil Nadu (`TN`) and Sri Lanka (`SL`), I want consistent hyphenation behavior and identical deterministic output across all supported target environments and regional Tamil varieties, so that hyphenation behaves identically everywhere my users read Tamil content.

**Why this priority**: Ensures regional inclusivity and consistent typographic layout across every platform where the toolkit is consumed.

**Independent Test**: Verify the sourced hyphenation test corpus against all supported target environments and across both `TN` and `SL` regional vocabulary, confirming 100% identical outputs and error messages.

**Acceptance Scenarios**:

1. **Given** identical Tamil inputs and configuration parameters across all supported environments, **When** invoking word hyphenation, boundary inspection, paragraph hyphenation, or line wrapping, **Then** every environment returns the exact same syllable segments, break offsets, and formatted text.
2. **Given** regional vocabulary from Tamil Nadu (`TN`) and Sri Lanka (`SL`, including Jaffna and Batticaloa lexical forms), **When** hyphenating words, **Then** orthographic syllable boundary rules operate invariantly across dialects without regional bias or character corruption.

---

### Edge Cases

- **Short words below minimum threshold**: What happens when a Tamil word has fewer Tamil letters than `left_min + right_min` (default `2 + 2 = 4` Tamil letters, where a closed syllable like `\u{0BAA}\u{0B9F}\u{0BCD}` counts by tailored *Ezhuthu* letters)? If a word cannot satisfy both the minimum leading *Ezhuthu* count (`left_min`) and minimum trailing *Ezhuthu* count (`right_min`), zero break points are returned and the word remains unbroken.
- **Stranded pure consonants (*Mei*) and *Aytham* (`\u{0B83}`)**: In accordance with W3C Tamil Layout Requirements (tam-lreq) and classical grammar, a new line or hyphenated segment MUST NEVER begin with a *Mei* (pure consonant with pulli, e.g. `\u{0BCD}`) or *Aytham* (`\u{0B83}`). In any consonant cluster (e.g., `\u{0BA4}\u{0BC1}\u{0BB0}\u{0BCD}\u{0BAA}\u{0BCD}\u{0BAA}\u{0BBF}\u{0BB0}\u{0BAF}\u{0BCB}\u{0B95}\u{0BAE}\u{0BCD}` where `\u{0BB0}\u{0BCD}` and `\u{0BAA}\u{0BCD}` are consecutive *Mei* letters), the entire contiguous sequence of *Mei* / *Aytham* letters binds to the preceding vowel-bearing letter (*Uyir* or *Uyirmei*) as coda, and any break point occurs strictly after the final *Mei* in the cluster and before the next *Uyirmei*/*Uyir*.
- **Word-initial or isolated *Mei* / invalid orthography**: If malformed input begins with an isolated *Mei*, combining vowel sign, or uncategorized cluster, the system MUST preserve all characters without failing or dropping content, and MUST NOT place a break immediately after an initial unattached mark or *Mei*.
- **Unnormalized (NFD) input**: Input text containing decomposed Tamil sequences (e.g., split two-part vowel signs `\u{0BC6}` + `\u{0BBE}` for `\u{0BCA}`) MUST be canonically normalized to NFC prior to syllable boundary analysis so that decomposed vowel signs are never mistaken for separate letters or split across lines.
- **Pre-existing soft hyphens (`U+00AD`) or explicit hyphens (`-`)**: Existing explicit hyphens (`-`) act as natural token/segment boundaries; pre-existing soft hyphens (`U+00AD`) are always preserved and augmented with automatic breaks at other valid points, so repeated hyphenation passes never stack duplicate soft hyphens (`\u{00AD}\u{00AD}`).
- **Empty or whitespace-only input**: Returns empty segments / unchanged text with zero break points and no error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a word-level hyphenation capability (`hyphenate_word`) that accepts a Tamil word and optional configuration (`delimiter`, `left_min`, `right_min`), returning the hyphenated string, the ordered list of syllable segments, and the break positions.
- **FR-002**: System MUST provide a boundary inspection capability (`hyphenation_points`) that returns each valid break point's tailored-letter (*Ezhuthu*) index, character/scalar offset, and byte offset within the normalized word.
- **FR-003**: System MUST enforce phonological and orthographic Tamil syllable structure rules (defined declaratively in the linguistic rule catalog):
  - Every syllable nucleus is an independent vowel (*Uyir*) or consonant-vowel composite (*Uyirmei*, including supported Grantha bases and atomic *Ksha* / *Shri* sequences).
  - Any pure consonant (*Mei*, consonant + `\u{0BCD}`) or *Aytham* (`\u{0B83}`) immediately following a syllable nucleus acts as part of that syllable's coda and MUST never begin a new line or hyphenated segment.
  - Consecutive *Mei* / *Aytham* sequences (geminates or multi-consonant clusters such as `\u{0BB0}\u{0BCD}\u{0BAA}\u{0BCD}`) MUST remain attached together to the preceding nucleus; a hyphenation break is permitted only after the complete coda sequence and before a following *Uyirmei* or *Uyir* onset.
- **FR-004**: System MUST enforce configurable minimum leading (`left_min`, default `2`) and minimum trailing (`right_min`, default `2`) tailored Tamil letter (*Ezhuthu*) counts around any hyphenation break point, AND require at least one vowel-bearing nucleus (*Uyir* or *Uyirmei*) on both sides of any break.
- **FR-005**: System MUST normalize input to Unicode Canonical Composition (NFC) before boundary detection while strictly preserving Zero-Width Joiner (`U+200D`), Zero-Width Non-Joiner (`U+200C`), whitespace, punctuation, and non-Tamil characters. A hyphenation break MUST NEVER be placed immediately before or after a ZWJ or ZWNJ; the letters around a joiner stay together in one segment, and joiners are never moved, merged, or dropped.
- **FR-006**: System MUST provide a text-level hyphenation capability (`hyphenate_text`) that scans arbitrary text, identifies Tamil word tokens, inserts the configured hyphenation delimiter (defaulting to soft hyphen `U+00AD`) at valid break points within each Tamil word, and preserves all surrounding punctuation, Latin text, numerals, and whitespace verbatim. A Tamil word token is a contiguous run of Tamil letters (including Grantha letters, vowel signs, pulli, aytham, and any ZWJ/ZWNJ between them); Tamil digits, Tamil symbols, punctuation, apostrophes, explicit hyphens (`-`), whitespace, and non-Tamil characters end the token and are never hyphenated or altered.
- **FR-007**: System MUST provide a deterministic line-wrapping capability (`wrap_text`) that wraps Tamil and mixed-script text to a specified maximum line width (measured in tailored grapheme clusters / *Ezhuthu* units), breaking Tamil words across lines at the latest valid hyphenation point when a word exceeds the remaining line width and appending a configurable visible hyphen (default `"-"`). Non-Tamil tokens, links, and numbers are outside hyphenation scope and are handled by the host environment or browser default wrapping without modification. For any Tamil word with no valid syllable break point that fits the remaining line width (such as short words or words where every break violates `left_min`/`right_min`), the system MUST keep the Tamil word intact without forcing an invalid orthographic break.
- **FR-008**: System MUST preserve every soft hyphen (`U+00AD`) already present in input text and MUST additionally insert the delimiter at every other valid break point in that word, never producing two adjacent soft hyphens. Hyphenating already-hyphenated output MUST be idempotent (a second pass returns identical text). A pre-existing soft hyphen that violates a syllable rule (for example, one placed before a *Mei*) is preserved verbatim as author intent and is not removed or moved.
- **FR-009**: System MUST validate configuration parameters and return explicit, deterministic errors when invalid parameters are supplied (e.g., `left_min < 1`, `right_min < 1`, or `max_width < 2` for line wrapping).
- **FR-010**: System MUST expose all hyphenation capabilities with identical behavior across all supported toolkit distribution environments and across both `TN` and `SL` regional Tamil varieties.

### Key Entities

- **HyphenationConfig**: Configuration controlling hyphenation behavior:
  - `delimiter`: Text marker inserted at valid break points (defaults to soft hyphen `"\u{00AD}"` for word/paragraph hyphenation, and `"-"` for line wrapping).
  - `left_min`: Minimum number of tailored Tamil letters (*Ezhuthu*) required before the first hyphenation break in a word (default `2`, minimum `1`).
  - `right_min`: Minimum number of tailored Tamil letters (*Ezhuthu*) required after the last hyphenation break in a word (default `2`, minimum `1`).
- **HyphenationPoint**: Metadata describing a single valid break boundary within a normalized word:
  - `letter_index`: Zero-based index in the sequence of tailored letters (*Ezhuthu*) where the break occurs (i.e., after the first `letter_index` letters).
  - `scalar_offset`: Zero-based Unicode scalar (code point) offset in the normalized word.
  - `byte_offset`: Zero-based byte offset in the normalized word.
- **HyphenationResult**: Output of hyphenating a single word:
  - `original`: Input word normalized to canonical form.
  - `hyphenated`: Word with `delimiter` inserted at each valid break point.
  - `segments`: Ordered list of unbroken syllable segments between break points (joining `segments` with `""` reconstructs `original`, and joining with `delimiter` reconstructs `hyphenated`).
  - `points`: Ordered list of `HyphenationPoint` records.
- **WrapResult**: Output of line-wrapping a text passage:
  - `lines`: Ordered list of wrapped line strings.
  - `broken_words_count`: Count of words that were hyphenated across line boundaries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of hyphenated Tamil words in the verification corpus preserve grapheme cluster integrity—zero instances of split vowel signs, stranded pulli (`\u{0BCD}`), or *Mei*-initial / *Aytham*-initial line segments.
- **SC-002**: Joining the returned `segments` of any hyphenated word without a delimiter reproduces the exact canonically normalized input string with 100% character and joiner fidelity across 10,000+ randomized test inputs.
- **SC-003**: The sourced verification corpus contains at least 120 test cases covering open/closed syllables, geminate clusters, multi-consonant codas, Grantha ligatures (*Ksha*, *Shri*), `TN` and `SL` regional words, mixed-script paragraphs, line wrapping, and error cases, passing 100% identically across all supported environments when explicitly selected for review. The corpus remains in planned (owner-review) status, is excluded from active/verified-support counts, and is only activated after explicit owner approval of the linguistic rules.
- **SC-004**: Word hyphenation completes in under 5 microseconds per word and paragraph hyphenation (1,000 characters of Tamil text) completes in under 100 microseconds on standard hardware, enabling real-time interactive typography without perceptible delay.

## Assumptions

- **Rule-Based Orthographic Syllabification Scope**: Because Tamil orthography is phonemic and explicitly marks pure consonants with a pulli (`\u{0BCD}`), syllable boundaries in written Tamil correspond deterministically to orthographic *Akshara* (nucleus + coda) boundaries. Full dictionary-backed morphological compound splitting (which requires lexicon disambiguation and sandhi/Punarchi inversion when two words fuse into a single *Uyirmei* letter, e.g., `\u{0BAE}\u{0BB0}\u{0BAE}\u{0BCD}` + `\u{0B85}\u{0B9F}\u{0BBF}` → `\u{0BAE}\u{0BB0}\u{0BAE}\u{0B9F}\u{0BBF}`) is separate from orthographic hyphenation. In v0.1, breaks occur at orthographic syllable boundaries (`\u{0BAE}\u{0BB0}-\u{0BAE}-\u{0B9F}\u{0BBF}`) which never require mutating or decomposing an existing *Uyirmei* letter into a *Mei* + *Uyir*.
- **Alignment with Standard Tamil Typographic Conventions**: The syllable boundary rules align with established Tamil typographic standards (W3C Internationalization Tamil Layout Requirements and TeX `hyph-ta` syllabic rules): break after any vowel (*Uyir*) or consonant-vowel syllable (*Uyirmei*), keep all trailing *Mei* (pulli) consonants and *Aytham* attached to the preceding syllable as coda, and never break before a *Mei*, *Aytham*, or dependent vowel sign.
- **Default Minimum Thresholds**: Consistent with standard Tamil typographic practice, `left_min` defaults to `2` tailored letters and `right_min` defaults to `2` tailored letters so single-letter prefixes or suffixes are not visually orphaned by default, while callers can explicitly set `left_min = 1` or `right_min = 1` when tighter wrapping is desired.
