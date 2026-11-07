# Feature Specification: Full Tamil Utility Suite for Microsoft Word Add-in

**Feature Branch**: `[014-word-tamil-utility-suite]`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "This add in should be full tamil utility for ms word. instead of lot of add-in or work around they should do it with from the add-in. use flash subagents for planning and iterate"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Legacy Font Conversion & Orthographic Repair in Word (Priority: P1)

A Tamil author, government official, journalist, or publisher opens an archive document or pastes text typed in a legacy Tamil font encoding (such as Bamini, Vanavil Avvaiyar, TSCII, TAB, TAM, Anjal, or Shree-Lipi LT-TM) or text copied from PDFs/OCR with broken vowel signs and duplicate pulli marks. Instead of copying paragraphs out to third-party web converters and losing formatting, they select the text (or the entire document) inside Microsoft Word and convert it to clean, standard Unicode Tamil—or convert Unicode text back to a legacy publisher font—in a single action while preserving inline styling and updating the font family for immediate legibility.

**Why this priority**: Legacy font incompatibility and malformed Unicode diacritics are the single biggest daily pain point for Tamil Microsoft Word users across government, legal, academic, and publishing workflows. Eliminating external copy-paste workarounds delivers immediate standalone value.

**Independent Test**: Can be fully tested by opening a Word document containing Bamini/Vanavil/TSCII encoded text and malformed Unicode sequences, invoking the conversion and normalization actions from the Word add-in, and verifying that all Tamil text becomes valid, searchable Unicode rendered in a legible Unicode Tamil font while bold/italic styling and English/numeric spans remain intact.

**Acceptance Scenarios**:

1. **Given** a Word selection, table, or document containing legacy-encoded Tamil text (Bamini, TSCII, TAB, TAM, Anjal, Vanavil Avvaiyar, or LT-TM), **When** the user triggers "Auto-Convert to Unicode" or selects a specific source encoding, **Then** the text is replaced in-place with canonical Unicode Tamil, the font family is updated to a configured Unicode Tamil font so it renders legibly immediately, character formatting (bold, italic, underline, font size) is preserved, and non-mapped English/numeric spans remain untouched.
2. **Given** a Word selection in standard Unicode Tamil that must be sent to a legacy desktop publishing workflow, **When** the user chooses "Convert Unicode to Legacy Encoding" and selects a target encoding (such as Bamini, TSCII, TAB, or TAM), **Then** the selected Unicode Tamil text is accurately converted into the target legacy character sequence.
3. **Given** Tamil text pasted from a PDF or web page containing duplicate pulli marks, out-of-order vowel signs, split compound vowels, or stray invisible zero-width characters, **When** the user runs "Normalize & Repair Tamil", **Then** all orthographic defects are repaired into canonical form and the user receives a summary of repaired anomalies.
4. **Given** a document where standard search fails to match Tamil words due to underlying encoding or invisible character differences, **When** the user searches or replaces text using the Tamil-Aware Find & Replace tool, **Then** all orthographically equivalent occurrences are matched and updated regardless of underlying composed/decomposed vowel differences or stray zero-width characters.

---

### User Story 2 - Authentic Tamil Alphabetical Sorting (*Akara Varisai*) for Lists & Tables (Priority: P2)

An editor, teacher, or legal clerk compiling a Tamil glossary, name roster, bibliography, numbered list, or multi-column table in Microsoft Word needs to sort the entries alphabetically. Standard Word sorting orders Tamil characters by raw character code value, which scrambles pure consonants (Mei) after vowel-consonants (Uyirmei) and misorders Grantha characters. Using the add-in, the user selects paragraphs, list items, or table rows and sorts them in authentic Tamil lexicographical order (*Akara Varisai*).

**Why this priority**: Microsoft Word's built-in sort does not implement Tamil phonotactic *Akara Varisai* rules (placing pure consonant `க்` before `க, கா, கி...`). Providing one-click authentic Tamil sorting for both paragraphs and tables inside Word removes the need to export lists or tables to external tools or sort manually.

**Independent Test**: Can be fully tested by selecting an unsorted list of Tamil paragraphs and an unsorted multi-column Tamil table in Word, clicking Sort (*Akara Varisai*) in ascending or descending order, and verifying exact dictionary order with row integrity preserved.

**Acceptance Scenarios**:

1. **Given** a selection of multiple paragraphs or list items in Word containing Tamil words, **When** the user clicks "Sort Tamil (Akara Varisai - Ascending)", **Then** the paragraphs are reordered in-place following standard Tamil dictionary order (Uyir $\rightarrow$ Aytham $\rightarrow$ Mei before Uyirmei series $\rightarrow$ Grantha letters).
2. **Given** a selection of Tamil paragraphs, **When** the user selects "Sort Tamil (Descending)" or enables "Ignore Leading Numbers/Bullets" in the utility pane, **Then** the paragraphs are reordered in reverse Tamil alphabetical order while respecting the chosen prefix-handling rule.
3. **Given** a Word table containing multiple rows of Tamil text (such as an employee register, glossary, or index), **When** the user selects the table and chooses "Sort Table by Column" with *Akara Varisai* (optionally preserving a header row), **Then** the table rows are reordered based on the chosen column's Tamil alphabetical order while keeping all adjacent cells in each row aligned.

---

### User Story 3 - Numerals, Legal/Currency Words, Traditional Symbols & Calendar Stamps (Priority: P3)

A professional drafting a Tamil legal deed, financial invoice, academic manuscript, or official government letter in Word needs to write out numeric figures or currency amounts in formal Tamil words, convert between standard digits (`0–9`) and Tamil digits (`௦–௯`), insert traditional Tamil fractions (`முந்திரி`, `காணி`, `வீசம்`, `கால்`, `அரை`, `முக்கால்`) or classical heritage symbols, or insert an official Tamil calendar date header (Thiruvalluvar Year, 60-year cycle name, Tamil solar month/day, and Panchangam details). They perform all of these directly from the add-in without looking up reference charts or external calculators.

**Why this priority**: Official, legal, financial, and cultural Tamil documents frequently require number-to-word expansion, regional dialect awareness (Tamil Nadu vs. Sri Lanka/diaspora conventions), and Tamil solar calendar dates. Consolidating these into the Word ribbon and utility pane makes the add-in a complete authoring companion.

**Independent Test**: Can be fully tested by selecting a number (e.g., `125450.75`) in a Word document to convert or append its formal Tamil word/currency representation, inserting a Tamil calendar date stamp at the cursor using either Thirukanitham or Vakya calculation, and inserting traditional fraction symbols from the palette.

**Acceptance Scenarios**:

1. **Given** a selected numeric value or currency figure in a document, **When** the user invokes "Number / Currency to Tamil Words" (choosing cardinal, ordinal, decimal, or currency mode with INR, LKR, SGD, USD, EUR, or GBP), **Then** the add-in inserts or replaces the selection with the exact Tamil word representation (supporting both Indian/TN lakh-crore and international/SL scale conventions where applicable).
2. **Given** selected text containing numbers, **When** the user toggles digit script conversion, **Then** standard digits (`0–9`) are converted to Tamil digits (`௦–௯`), traditional additive numerals (`௰`, `௱`, `௲`), or vice versa.
3. **Given** the cursor positioned in a document, **When** the user selects a date (defaulting to today) and clicks "Insert Tamil Date Stamp", **Then** a formatted Tamil date header (including Thiruvalluvar Year, Tamil solar month and day, Jovian year name, and optional Panchangam limbs/auspicious times or TN/SL holiday status) is inserted at the cursor.
4. **Given** a user authoring heritage or mathematical Tamil text, **When** they select a traditional fraction (e.g., `1/320 முந்திரி` through `3/4 முக்கால்`) or classical measurement/currency symbol from the symbol palette, **Then** the symbol and/or its Tamil name is inserted at the cursor position.

---

### User Story 4 - Unified Tamil Ribbon, Syllabic Hyphenation & Document Inspector (Priority: P4)

A Tamil writer or desktop publisher wants a single, cohesive workspace inside Microsoft Word where top-bar Ribbon buttons provide instant one-click access to frequent actions (Hyphenate, Auto-Convert to Unicode, Normalize & Repair, Sort Akara Varisai, Number to Words, Insert Tamil Date) and an interactive Utility Taskpane provides fine-grained controls, live previews, and a Tamil Document Inspector showing true Tamil letter (grapheme) counts, syllable counts, Uyir/Mei/Uyirmei/Grantha breakdowns, and invisible character diagnostics.

**Why this priority**: Unifies the existing syllabic hyphenation capabilities with all new Tamil utilities into a single discoverable interface so users never need to install multiple single-purpose add-ins or switch windows.

**Independent Test**: Can be fully tested by verifying the top-bar `தமிழ்` Ribbon tab groups and opening the Tamil Utility Taskpane to inspect a Tamil document's character/syllable statistics and run any tool with live preview before applying changes to the document.

**Acceptance Scenarios**:

1. **Given** a justified Tamil document with uneven word spacing, **When** the user uses the Ribbon or Taskpane hyphenation controls (soft hyphenation with configurable left/right syllable margins, zero-width syllable wrapping, or hyphen removal), **Then** words break cleanly only at valid Tamil syllable boundaries without splitting consonant clusters (`க்ஷ`, `ஸ்ரீ`, or pulli-bound codas).
2. **Given** a selection or full document in Word, **When** the user opens the Document Inspector tab in the Taskpane, **Then** the add-in displays accurate counts of total Tamil letters (graphemes), words, syllables, vowels (*Uyir*), pure consonants (*Mei*), vowel-consonants (*Uyirmei*), *Aytham*, *Grantha* characters, and any non-standard or zero-width code points.
3. **Given** a user working in either Tamil or English interface preference, **When** they interact with the Ribbon and Taskpane, **Then** all labels, tooltips, and status messages are clearly understandable in a bilingual Tamil/English layout.

---

### Edge Cases

- **Mixed-Script Selections (Tamil + English + Punctuation + Formulas)**: When converting legacy encodings, normalizing Unicode, hyphenating, or converting numerals across a selection that mixes Tamil with English words, URLs, email addresses, or punctuation, how does the system avoid corrupting non-Tamil text? (System must scope transformations strictly to relevant spans or provide an option to target only Tamil/legacy runs).
- **Ambiguous Short Selections in Legacy Auto-Detection**: What happens when a user runs "Auto-Convert to Unicode" on a 1–2 word snippet where multiple legacy 8-bit encodings share overlapping byte patterns? (System must display the detected confidence level and allow one-click override/preview in the Taskpane or reversal via standard application Undo actions).
- **Preserving Rich Document Structure**: What happens when a user runs document-wide normalization, legacy conversion, or hyphenation on a document containing tables, headers, footers, hyperlinks, footnotes, or mixed character styles? (System must preserve inline formatting and structural elements across body paragraphs, tables, and optional headers/footers rather than flattening paragraphs to unstyled plain text).
- **Mixed or Empty Lines During Collation Sorting**: How does *Akara Varisai* sorting handle empty paragraphs, leading whitespace, punctuation, numbered prefixes, or English words mixed into a Tamil list or table? (Empty lines should be preserved or grouped predictably; leading punctuation/whitespace stripped for sort-key comparison while preserved in output; non-Tamil items sorted deterministically after or before Tamil items).
- **Large Documents (50–100+ Pages)**: How does the system behave when processing an entire book manuscript? (Operations must process paragraphs in non-blocking batches with progress feedback so the document editor remains responsive).
- **Offline / Restricted Corporate Environments**: What happens when the user is editing confidential documents without external internet access? (All Tamil processing must run 100% locally within the add-in client without sending document text to external servers).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The add-in MUST provide bidirectional font encoding conversion between standard Unicode Tamil and legacy Tamil encodings: Bamini, TSCII, TAB, TAM, Anjal, Vanavil Avvaiyar, and LT-TM (Shree-Lipi), operating on the active selection, table cells, or the entire document. When converting from legacy encodings to Unicode, the add-in MUST automatically update legacy font family assignments to a configured standard Unicode Tamil font so converted text renders legibly immediately.
- **FR-002**: The add-in MUST include automatic legacy encoding detection that identifies the source encoding of selected text and reports detection confidence before or during conversion.
- **FR-003**: The add-in MUST provide a Unicode Normalization & Orthographic Repair action that fixes malformed vowel sign sequences, strips duplicate pulli (virama) marks, normalizes canonical Unicode composition (NFC/NFD), and cleans up stray zero-width formatting characters while preserving valid joiner sequences.
- **FR-004**: The add-in MUST provide *Akara Varisai* alphabetical sorting for selected paragraphs, list items, and table rows (by a selected column, with optional header-row preservation) in both ascending and descending order, accurately ordering vowels (*Uyir*), *Aytham*, pure consonants (*Mei*) prior to vowel-consonants (*Uyirmei*), and *Grantha* characters.
- **FR-005**: The add-in MUST convert numeric values in a selection (or entered in the taskpane) into Tamil words across cardinal numbers, decimals, ordinals, and formatted currency wording (supporting INR, LKR, SGD, USD, EUR, and GBP), with support for regional Tamil Nadu and Sri Lankan/international phrasing conventions.
- **FR-006**: The add-in MUST convert numeric digits between standard Arabic digits (`0–9`), Tamil digits (`௦–௯`), and traditional Tamil additive numerals (`௰`, `௱`, `௲`), and provide an interactive palette to browse and insert traditional Tamil fractions (`முந்திரி`, `காணி`, `மாகாணி/வீசம்`, `கால்`, `அரை`, `முக்கால்`) and heritage measurement/currency symbols.
- **FR-007**: The add-in MUST provide a Tamil Calendar & Panchangam utility capable of generating and inserting formatted Tamil date stamps (including Tamil solar month and day, Thiruvalluvar Year, 60-year cycle name, ephemeris calculation mode selection between Thirukanitham and Vakya, Panchangam limbs, and Tamil Nadu / Sri Lanka official holiday indicators).
- **FR-008**: The add-in MUST preserve and expose phonotactic Tamil syllabic hyphenation and line-wrapping controls (Hyphenate Selection, Hyphenate Document, Wrap Without Hyphen, Remove Hyphens, and configurable minimum left/right syllable margins) that never split Tamil grapheme clusters, pulli-bound codas, or Grantha conjuncts.
- **FR-009**: The add-in MUST provide a Tamil Document Inspector in the taskpane that analyzes the active selection or full document and reports counts of Tamil words, graphemes (true Tamil letters), syllables, *Uyir*, *Mei*, *Uyirmei*, *Aytham*, *Grantha* characters, and invisible/formatting code points.
- **FR-010**: The add-in MUST organize its user interface into (a) an expanded top-bar `தமிழ்` Ribbon tab with grouped one-click commands for the most frequent actions, and (b) a unified multi-tool Taskpane workbench allowing live preview, configuration, and insertion for all utilities.
- **FR-011**: In-place document transformations (conversion, normalization, hyphenation, digit conversion, and sorting) MUST preserve existing inline character formatting (such as bold, italic, underline, and font size) across body text and tables, and support standard application Undo operations.
- **FR-012**: All linguistic processing MUST execute 100% client-side within the Word add-in environment using a unified, client-side linguistic processing engine, transmitting zero document content over the network and maintaining complete parity across Tamil Nadu and Sri Lankan dialect/orthographic inputs.
- **FR-013**: The add-in MUST provide an orthographically normalized Tamil Find & Replace utility that matches and replaces Tamil words across the document even when source text contains composed vs. decomposed vowel differences or invisible zero-width formatting characters.

### Key Entities

- **Document Text Range / Selection**: The active user selection, table range, or collection of document paragraphs (body text, tables, and optional headers/footers) targeted for in-place transformation, sorting, search, or inspection while preserving rich-text styling.
- **Encoding Conversion Profile**: Defines source encoding (Auto-detect, Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM, or Unicode), target encoding, target Unicode font family, confidence score, and mixed-script preservation rules.
- **Orthographic Repair Report**: Summary of detected and repaired Unicode anomalies (duplicate pullis removed, split vowel signs recomposed, stray zero-width characters cleaned).
- **Numeral & Symbol Format Request**: Configuration specifying input number/fraction, output mode (cardinal words, ordinal words, decimal words, legal currency words, Tamil digits, traditional numerals, or heritage symbols), and currency/regional convention (TN vs. SL/International).
- **Tamil Date / Panchangam Stamp**: A structured calendar record for a selected Gregorian date and location/calculation system (Thirukanitham or Vakya), containing Tamil solar month, day, Thiruvalluvar year, 60-year cycle name, Panchangam limbs, and formatted insertion templates.
- **Linguistic Inspection Profile**: Aggregated grapheme and syllable breakdown of a text range (total Tamil letters, Uyir, Mei, Uyirmei, Aytham, Grantha, ASCII/other, and code point scalar diagnostics).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete all eight core Tamil document workflows (legacy font conversion, Unicode repair, Tamil-aware Find & Replace, *Akara Varisai* paragraph/table sorting, numeral/currency word expansion, traditional fraction/symbol insertion, Tamil date stamping, and syllabic hyphenation) entirely within Microsoft Word with **0 external tools or copy-paste workarounds**.
- **SC-002**: In-place transformation of a standard 10-paragraph selection (legacy conversion, normalization, or hyphenation) completes in **under 500 milliseconds**, and sorting 500 Tamil list or table items completes in **under 1 second**.
- **SC-003**: Legacy encoding conversion, Unicode normalization, numeral formatting, collation sorting, calendar calculations, and syllabic hyphenation achieve **100% output accuracy** against authoritative Tamil linguistic, orthographic, and Unicode collation standards.
- **SC-004**: **100% of user document processing** occurs locally on the client device with **zero network requests** transmitting document text or personal data (verifiable via network inspection and Microsoft AppSource privacy certification readiness).
- **SC-005**: At least **90% of target operations** (hyphenation, auto-convert to Unicode, normalize/repair, sort selection, number to words, insert date stamp) can be triggered in **1–2 clicks** directly from the `தமிழ்` Ribbon tab without requiring manual configuration.

## Assumptions

- Microsoft Word Desktop (Windows/macOS, Word 2019+ / Microsoft 365) and Word on the Web are the target host environments, supporting standard Office Add-in Ribbon commands and Taskpane surfaces.
- Specialized grammatical analysis features such as classical poetic meter analysis (*Yaappu*), automated morphological root parsing, and classical sandhi (*Punarchi*) compound splitting are excluded from this release scope and reserved for future iterations.
- When converting legacy font text to Unicode in Word, if the source text was styled with a legacy non-Unicode font family (e.g., `"Bamini"`), the add-in defaults to assigning a standard system-available Unicode Tamil font (such as `"Nirmala UI"`, `"Latha"`, or `"Noto Sans Tamil"`, configurable by the user) so converted characters render legibly immediately.
