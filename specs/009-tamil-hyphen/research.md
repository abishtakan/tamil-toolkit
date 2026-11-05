# Phase 0 Research: Tamil Syllable Hyphenation (`tamil-hyphen`)

**Feature**: `009-tamil-hyphen`  
**Date**: 2026-11-05  
**Status**: Completed  

## 1. Syllable Boundary Identification (Phonotactics & Orthography)

### Decision
Base all hyphenation break decisions on the phonological and orthographic structure of Tamil *Aksharas* (syllabic units), following classical grammars (*Tholkappiyam* and *Nannool*) and modern internationalization standards (**W3C Tamil Layout Requirements `tam-lreq`** and **W3C Indic Layout Requirements `ilreq`**):
1. **Syllable Nucleus**: An independent vowel (*Uyir*) or consonant-vowel composite (*Uyirmei*, including single-codepoint Grantha consonants and atomic conjuncts *Ksha* `க்ஷ` and *Shri* `ஸ்ரீ`).
2. **Syllable Coda**: Any pure consonant (*Mei* with pulli `\u{0BCD}`) or *Aytham* (`ஃ`, `\u{0B83}`) following a nucleus acts strictly as the coda of that syllable.
3. **Consonant Sequences (Clusters & Geminates)**: When multiple pure consonants appear consecutively (e.g. `ர்ப்ப்` in `துர்ப்பிரயோகம்` or `த்த்` in `வைத்தியர்`), the entire contiguous sequence of *Mei* letters binds to the preceding nucleus as coda.
4. **Forbidden Line-Start (*Mei* / *Aytham*)**: A hyphenated line segment or new line MUST NEVER begin with a *Mei* (`புள்ளி` consonant) or *Aytham* (`ஃ`).
5. **Break Opportunities**: Hyphenation points occur only after a complete syllable coda and before a following vowel-bearing letter (*Uyirmei* or *Uyir*).

### Rationale
Tamil orthography is phonemically regular: consonants without an inherent vowel are explicitly marked with a pulli (`\u{0BCD}`). Unlike English, which requires huge hyphenation dictionaries because of irregular spelling, Tamil syllabification is 100% deterministic from the surface orthography. Binding codas to the preceding syllable matches how Tamil words are pronounced and meets all W3C line breaking requirements.

### Alternatives Evaluated
- **Liang Hyphenation Patterns (TeX `hyph-ta`)**: Evaluated TeX's pattern table. TeX's Tamil patterns implement essentially the same rule set (break after vowels, bind pulli to preceding consonant) but with TeX-specific numeric weights. A direct deterministic state-machine over tailored *Ezhuthu* letters is faster, smaller, requires no pattern tables or heap allocation, and guarantees 0% cluster-splitting errors.
- **Morphological / Punarchi Compound Splitting**: In compound words where sandhi merges letters (e.g., `மரம்` + `அடி` → `மரமடி`), true morphological decomposition would require splitting `ம` into `ம்` + `அ` and showing `மரம்-அடி`. This is rejected for v0.1 because standard typography and hyphenation never alter or re-spell printed text; breaks must occur along existing character boundaries.

---

## 2. Letter Counting and Margins (`left_min`, `right_min`)

### Decision
- Measure margins strictly in **tailored Tamil letters (*Ezhuthu*)**, not Unicode code points or UTF-8 bytes, using `tamil_core::Letters`.
- Default values: `left_min = 2`, `right_min = 2` tailored letters.
- Both parameters are configurable per request (with validation: `left_min >= 1`, `right_min >= 1`).
- An additional requirement: at least one vowel-bearing syllable nucleus (*Uyir* or *Uyirmei*) must exist on both sides of any break point.

### Rationale
- Standard Unicode character count would count `கொ` as 2 code points and `ஸ்ரீ` as 4 code points, corrupting letter-based margins. Tailored grapheme clusters (*Ezhuthu*) provide an exact 1:1 mapping with human perception of Tamil letters.
- `left_min = 2, right_min = 2` ensures that a word has at least 4 tailored letters before any break can occur, preventing awkward single-letter orphans.

---

## 3. Paragraph Scanning, Non-Tamil Tokens, and URLs

### Decision
- Contiguous runs of Tamil letters (including Grantha letters, vowel signs, pulli, aytham, and internal ZWJ/ZWNJ) form hyphenatable Tamil word tokens.
- Non-Tamil characters (Latin alphabet, ASCII digits, punctuation, whitespace, Tamil numerals `\u{0BE6}..\u{0BEF}`, and Tamil epigraphical symbols `\u{11FC0}..\u{11FFF}`) end the Tamil token and are **never** hyphenated or modified by `tamil-hyphen`.
- In line wrapping (`wrap_text`), non-Tamil tokens, links, and numbers are outside hyphenation scope and are handled by the host environment or browser default wrapping without modification.
- If a Tamil word has no valid break point that fits the remaining line width, it is kept whole on its own line without forcing an invalid orthographic break.

### Rationale
Preserves the toolkit's strict non-Tamil preservation principle (Principle II & VII). Web browsers and word processors already have standard wrapping behaviors for URLs and Latin text; `tamil-hyphen` focuses specifically on solving the missing Tamil typographic capability.

---

## 4. Soft Hyphen (`U+00AD`) Handling and Idempotency

### Decision
- When hyphenating text (`hyphenate_text`), existing author-placed soft hyphens (`U+00AD`) are preserved verbatim.
- The engine computes valid breaks on the underlying normalized word and augments the text by adding soft hyphens at other valid points.
- It strictly deduplicates adjacent soft hyphens, ensuring `hyphenate_text(hyphenate_text(text)) == hyphenate_text(text)` (idempotency).

### Rationale
Authors occasionally insert manual soft hyphens to force a specific wrap point; preserving them respects author intent while still enabling automatic typographic wrapping for the rest of the text.

---

## 5. Performance and Allocation Strategy

### Decision
- Core syllabification algorithm in `crates/tamil-hyphen` operates over borrowed slices (`&str`) and letter slices using `tamil_core::Letters`.
- Point calculation (`hyphenation_points`) returns an iterator or pre-allocated `Vec<HyphenationPoint>` with sub-5μs latency for typical words.
- Zero external dependencies in `tamil-hyphen` (only workspace dependencies: `tamil-core`, and optionally `tamil-norm` for normalization).

### Rationale
Meets SC-004 (< 5μs per word) and aligns with the toolkit's zero-allocation core principles.
