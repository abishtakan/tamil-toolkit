# Feature Specification: Tamil Word and Sentence Tokenization

**Feature Branch**: `master` (current branch)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Phase 9 from the [project roadmap](../../ROADMAP.md), covering surface word and sentence spans, sourced Tamil abbreviations, and stopword profiles.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Locate words in the original text (Priority: P1)

A developer building a text inspector or search tool can find a word in Tamil or mixed-script text and highlight its exact location in the submitted document.

**Why this priority**: Search and annotation both depend on offsets that point back to the submitted text, including when its accents, vowel signs, or invisible joiners affect how it is encoded.

**Independent Test**: Segment mixed-script text and extract each returned token using its byte range. Check the range of written units against the known boundaries in the same input.

**Acceptance Scenarios**

1. **Given** Tamil prose with Latin text, numbers, emoji, and punctuation, **When** a developer requests word tokens, **Then** the tokens appear in source order, carry their kind and both ranges, and account for all non-whitespace text.
2. **Given** a Tamil letter written with decomposed vowel signs, either supported Shri spelling, a KSHA form, or text containing a joiner, **When** a developer extracts each token by its byte range, **Then** the result retains the original scalars and the boundaries preserve each whole written unit.
3. **Given** empty or whitespace-only text, **When** a developer requests word tokens or sentences, **Then** the result is empty.
4. **Given** a reviewed honorific or currency marker written immediately before its name or amount, **When** a developer requests word tokens, **Then** the abbreviation and the adjacent content have distinct source spans.
5. **Given** a normally written Tamil word with attached inflections or clitics, **When** a developer requests word tokens, **Then** the entire surface word stays in one span.

---

### User Story 2 - Read sentences containing Tamil abbreviations (Priority: P2)

An editor or corpus curator can split Tamil prose into sentences without turning an honorific, a dotted name initial, a time marker, or a currency abbreviation into a false sentence break in a documented context.

**Why this priority**: A false break changes which text readers and downstream tools see as a sentence.

**Independent Test**: Split a passage that combines documented abbreviations with actual sentence endings and compare the extracted spans to independently annotated ranges.

**Acceptance Scenarios**

1. **Given** a reviewed abbreviation in its documented continuation context, **When** a developer requests sentences, **Then** the text continues across its abbreviation periods and splits at the next sentence boundary.
2. **Given** an abbreviation followed by a hard line break, end of text, or an independent sentence terminator, **When** a developer requests sentences, **Then** the boundary is retained. For other text outside the documented continuation patterns, the baseline decides whether the final period ends a sentence.
3. **Given** text with an unknown dotted form, a decimal, or closing quotation marks, **When** a developer requests sentences, **Then** the documented baseline punctuation rules apply wherever a reviewed abbreviation rule does not apply. Closing punctuation stays with the sentence it ends.

---

### User Story 3 - Control which stopwords a search omits (Priority: P3)

A search maintainer can retain all tokens, omit a small conservative set of Tamil stopwords, or choose a broader set for a search workflow where additional omissions are acceptable.

**Why this priority**: Stopword filtering changes what users can find. The search maintainer needs a predictable choice and an audit trail for the terms it affects.

**Independent Test**: Request tokens for the same passage under all three profiles and compare the remaining text and source ranges.

**Acceptance Scenarios**

1. **Given** a passage containing a conservative-list term, a broader-list-only term, and an unlisted term, **When** a developer selects each profile, **Then** the default retains all three, the conservative profile omits only its own term, and the broader profile omits both listed terms. The retained tokens keep their original text, positions, and order.
2. **Given** a listed term in canonically equivalent spellings, an unlisted inflection, or a spelling with an extra joiner, **When** a developer enables a stopword profile, **Then** both equivalent spellings match and filtering retains the unlisted inflection and joiner-bearing form.
3. **Given** a request naming an unsupported profile, **When** a developer requests filtered tokens, **Then** the request returns an error identifying the unsupported selection.

---

### Edge Cases

- Non-Tamil text uses the baseline boundaries. Mixed-script text can contain numbers in either Tamil or Latin digits and multi-scalar emoji.
- A byte or written-unit range can include digits, punctuation, or other scripts. A written-unit index is an absolute position in the full document, including whitespace.
- Detached Tamil marks, malformed clusters, and standalone format controls stay addressable in the original text. Input spelling and encoding are preserved.
- Repeated terminators and closing quotes follow the baseline punctuation rules. Line breaks still close sentences after an abbreviation, and the final sentence can end without punctuation.
- Lookup uses canonical equivalence for complete tokens. An inflection, substring, or visually similar spelling requires its own reviewed entry to be filtered.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** Each sentence and token MUST carry its exact source text, a zero-based UTF-8 byte range, and a zero-based written-unit range. Ranges include their start and exclude their end. Both ranges refer to the original document, including for retained tokens in filtered results.
- **FR-002** Segmentation MUST keep whole user-perceived written units together, including the toolkit’s existing Tamil letter conventions. It MUST preserve original spelling, Unicode composition, and format controls, including ZWJ and ZWNJ.
- **FR-003** Word tokenization MUST return ordered, non-overlapping spans for words, decimal-number tokens, reviewed abbreviations, and other non-whitespace content. Sentence segmentation MUST return ordered, non-overlapping spans that collectively cover all non-whitespace content, with boundary whitespace omitted and interior whitespace preserved.
- **FR-004** Sentence segmentation MUST follow the documented Unicode baseline and honor the documented continuation contexts of reviewed Tamil abbreviations. A context rule MUST retain hard line boundaries, end of text, and independent sentence terminators. An unknown candidate or context MUST use baseline segmentation.
- **FR-005** Stopword filtering MUST be opt-in and offer a disabled, conservative, and broader search profile. The broader list MUST be a strict superset of the conservative list. Filtering MUST retain the text, order, and positions of surviving tokens and MUST leave sentence segmentation independent of the stopword profile.
- **FR-006** Stopword matching MUST compare complete word tokens by canonical equivalence. The operation MUST reject an unknown profile selection with an error and MUST retain non-word tokens under every profile.
- **FR-007** Every shipped abbreviation and stopword MUST have traceable evidence, a reviewed use or inclusion rationale, and documented terms for any redistributed data. The supported abbreviation contexts and profile membership MUST be documented.
- **FR-008** The feature MUST support written Tamil from Tamil Nadu and Sri Lanka under one boundary profile. Regional usage MUST be documented where evidenced. Identical input and settings MUST give identical results across locales and supported consumers, without network access.

### Key Entities *(include if feature involves data)*

- **Source span** contains an unchanged substring and the two ranges that locate it in the document.
- **Token** is a source span classified as a word, decimal-number token, reviewed abbreviation, or other content for counting or filtering.
- **Sentence** is a source span bounded by the documented sentence rules.
- **Abbreviation entry** gives a surface form, supported context, usage evidence, and any scope limits.
- **Stopword profile** is a named, documented set of complete words selected for a specific filtering purpose.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** In 100% of agreed span fixtures, every reported byte and written-unit range selects the same original substring. Unfiltered results account for every non-whitespace written unit once within each result list.
- **SC-002** Every admitted abbreviation has at least one positive continuation fixture and one negative-context or boundary fixture. All expected sentence boundaries are reproduced in the reviewed cases, including Tamil Nadu and Sri Lankan examples.
- **SC-003** All three stopword profiles produce the expected selections on the same acceptance passage, including a term unique to the broader list. All retained tokens have the same text and ranges as the unfiltered result, and every unknown profile case returns an error.
- **SC-004** All supported consumers produce identical expected spans, token kinds, and filtering outcomes on the shared acceptance cases. Regional fixtures cover Tamil Nadu, Jaffna, Batticaloa, Vanni, and Up-Country for the shared boundary behavior.
- **SC-005** A manually annotated set of Tamil Nadu and Sri Lankan passages records expected word and sentence boundaries, including adjacent abbreviations and intact inflected words. Acceptance reports missed and spurious boundaries by case group for the documented baseline and the Phase 9 profile. The reviewed fixtures match exactly and contain zero splits inside a written unit.

## Assumptions

- The initial release covers modern written Tamil and ordinary mixed-script Unicode text. Its ranges count the toolkit’s written units, including punctuation, non-Tamil clusters, and whitespace. A Tamil-letter tally is a separate measure.
- Abbreviation support is limited to attested forms and contexts. The regional witnesses establish occurrence in the documented context. Broader use or an exclusive regional label requires its own evidence.
- The conservative profile is a reviewed subset of a broader search list. Profile membership and changes require editorial review because the choice affects search recall and precision.
- Morphological splitting, clitic detachment, sandhi analysis, missing-space recovery, spelling repair, dedicated URL and email parsing, and integration-specific search ranking are outside Phase 9.
- Phase 9 provides linguistic source spans and runs locally. Model inference, model-specific token IDs and counts, and model-budget chunking are outside this release. A separate chunking tool could use these spans as cut points and measure each assembled chunk with the target model’s encoder.
- The [Phase 9 module contract](../../docs/specs/tokenize-v0.1.md) defines the boundary baseline, records candidate sources, and sets the fixture review criteria.
