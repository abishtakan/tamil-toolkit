# Feature Specification: Additional Interactive Linguistic & Epigraphical Tools (`add-playground-tools`)

**Feature Branch**: `008-add-playground-tools`

**Created**: 2026-11-05

**Status**: Draft

**Input**: User description: "Add more tools to the Playground"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Traditional Tamil Fractions & Epigraphical Symbol Explorer (Priority: P1) 🎯 MVP

As an epigraphist, historian, student, or Tamil writer, I want an interactive visual explorer to look up traditional Tamil fractions (such as முந்திரி, காணி, அரைக்கால், வீசம்/மாகாணி, ஒருமா, கால், அரை, முக்கால்) and historic epigraphical measurement symbols (such as வேலி, குழி, கலம், நெல், காசு), so that I can instantly view their exact rational numerical values, Unicode code points, classical names, and copy them for digital typography.

**Why this priority**: Traditional Tamil fractions and historic measurement glyphs are a unique, culturally rich heritage feature encoded in modern Unicode, but difficult for users to access or type without specialized keyboard layouts. Providing an intuitive reference and bi-directional converter delivers immediate cultural and practical value.

**Independent Test**: Can be tested independently by opening the Fractions & Symbols tool, selecting or searching for "காணி" (or entering "1/80"); verify that the system displays the symbol `𑿀` (U+11FC0), its exact fraction value (1/80 or 0.0125), historical classification (Land/Fraction), and copies the character in one tap.

**Acceptance Scenarios**:

1. **Given** the Traditional Symbols tool, **When** the user browses the symbol grid, **Then** symbols are grouped logically (Fractions, Land Measurements, Currency/Coinage, Grain/Dry Volume Measures) with live visual glyph tiles.
2. **Given** a selected traditional symbol (e.g., `௮` or `𑿀`), **When** viewed in the detail inspector, **Then** the system presents the full Tamil name, exact rational fraction (numerator and denominator), decimal approximation, Unicode hex code point, and a one-tap copy button.
3. **Given** an entered fraction or decimal (e.g., `0.75` or `3/4`), **When** typed into the converter, **Then** the tool automatically identifies matching traditional Tamil fractional notation (e.g., முக்கால் `¾` / traditional representation).

---

### User Story 2 - Real-Time Tamil Letter & Uyirmei Morphological Decomposer (Priority: P2)

As a language student, teacher, or copywriter, I want to type or paste any Tamil word or sentence and instantly see its linguistic decomposition into pure vowels (*உயிர்*), pure consonants (*மெய்*), composite letters (*உயிர்மெய்*), *ஆய்தம்* (`ஃ`), and Grantha letters, so that I can understand the underlying phonetic and orthographic composition of complex Tamil words.

**Why this priority**: Tamil orthography merges consonants and vowels into distinct visual syllables (*உயிர்மெய்*). Users frequently struggle to identify root consonants (*மெய்*) and vowel markers (*துணைக்கால், கொம்பு, புள்ளி*), especially in compound words and ligatures.

**Independent Test**: Can be tested independently by typing "தமிழ்நாடு" into the decomposer; verify that each syllable is segmented and classified (`த` = `த்` + `அ` உயிர்மெய்; `மி` = `ம்` + `இ` உயிர்மெய்; `ழ்` = `ழ்` மெய்; `நா` = `ந்` + `ஆ` உயிர்மெய்; `டு` = `ட்` + `உ` உயிர்மெய்) with interactive breakdown chips.

**Acceptance Scenarios**:

1. **Given** Tamil text input, **When** typed or pasted, **Then** the system analyzes grapheme clusters in real time and displays a visual letter-by-letter decomposition ribbon.
2. **Given** any composite *உயிர்மெய்* letter, **When** selected, **Then** the interface shows the exact root consonant (`மெய்`) and vowel (`உயிர்`) components along with the vowel marker name (e.g., *கொம்பு*, *துணைக்கால்*).
3. **Given** mixed or loan-word text containing Grantha characters (e.g., `ஜ`, `ஷ`, `ஸ`, `ஹ`, `க்ஷ`), **When** analyzed, **Then** Grantha letters are clearly flagged and distinguished from classical Sangam consonants.

---

### User Story 3 - Tamil Unicode Text Normalizer & Anomaly Repair Tool (Priority: P3)

As a digital publisher, content creator, or developer pasting Tamil text from diverse PDF, web, or legacy sources, I want to detect and clean anomalous Tamil Unicode encodings (such as broken diacritics, duplicate vowel signs, split pulli, or stray invisible format controls) and normalize text to canonical Unicode standards, so that my text renders reliably without font rendering glitches or search collation failures.

**Why this priority**: Poorly encoded Tamil text from OCR, legacy web archives, or faulty mobile keyboards contains invisible defects that break search indexing, text-to-speech engines, and font shaping engines.

**Independent Test**: Can be tested independently by pasting a text sample containing non-standard or anomalous diacritics (e.g., decomposed `க` + `ொ` instead of standard composite or duplicate pulli marks); verify that the tool detects the defects, highlights them in an interactive diff, and produces canonical, cleaned Tamil text with one-tap copy.

**Acceptance Scenarios**:

1. **Given** input text with encoding anomalies (such as duplicate pulli or split vowel signs), **When** loaded into the normalizer, **Then** the system highlights anomalies and reports an audit summary of issues fixed.
2. **Given** normalization options, **When** switching between canonical forms (NFC vs NFD), **Then** the normalized output updates live in under 50ms.
3. **Given** cleaned output text, **When** the user taps copy, **Then** clean canonical Tamil text is copied with visual toast confirmation.

---

### Edge Cases

- How does the Traditional Symbol tool handle modern numbers with no historical fraction equivalent? (The tool displays the closest traditional fractional approximation or indicates that an exact historic symbol mapping does not exist).
- What happens when non-Tamil Latin characters or numbers are typed into the Uyirmei Decomposer? (Non-Tamil characters are preserved and categorized as Latin/Punctuation without causing parsing crashes).
- What happens when text already in canonical normalized form is processed by the Normalizer? (The system confirms the text is 100% clean and reports zero anomalies detected).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an interactive explorer for traditional Tamil fractions and epigraphical symbols displaying glyph, historical name, rational value (numerator/denominator), and Unicode codepoints.
- **FR-002**: System MUST support bi-directional conversion/lookup between rational numbers (e.g., 1/16) and traditional Tamil fraction symbols (e.g., மாகாணி/வீசம் `𑿈`).
- **FR-003**: System MUST decompose Tamil strings into individual grapheme clusters and classify each unit into linguistic categories (உயிர், மெய், உயிர்மெய், ஆய்தம், கிரந்தம், punctuation).
- **FR-004**: System MUST deconstruct any selected உயிர்மெய் letter into its constituent consonant (மெய்) and vowel (உயிர்) components with associated vowel mark terminology.
- **FR-005**: System MUST detect and repair Unicode diacritic anomalies, duplicate modifiers, and non-canonical decompositions in Tamil text.
- **FR-006**: System MUST provide single-tap copy functionality with instant visual feedback for all generated results and individual symbols.
- **FR-007**: System MUST execute all linguistic and symbol computations 100% locally in the client browser with zero network transmission.
- **FR-008**: System MUST support the established bilingual architecture (தமிழ் / English) across all tool titles, instructions, category tags, and copy toasts.
- **FR-009**: System MUST adhere to the established Basalt Granite & Inscription Slate dark mode and Palm Leaf light mode design system with 1px hairline transitions and zero bouncy animations.

### Key Entities

- **TraditionalSymbol**: Represents a classical Tamil fraction or epigraphical measurement glyph (attributes: glyph, name_ta, name_en, rational_value, unicode_codepoint, category).
- **LetterDecomposition**: Represents the morphological breakdown of a Tamil syllable (attributes: syllable, base_consonant, vowel, vowel_sign_name, classification).
- **NormalizationReport**: Represents the diagnostic outcome of text cleaning (attributes: original_text, cleaned_text, anomaly_count, anomalies_repaired).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can locate any traditional Tamil fraction or symbol and copy its Unicode glyph in under 10 seconds.
- **SC-002**: Real-time letter decomposition and normalizer analysis complete in under 50 milliseconds for typical paragraph-length inputs (up to 5,000 characters).
- **SC-003**: 100% of analyzed Tamil text conforms to authentic grammatical classification rules without misidentifying root consonants or vowel signs.
- **SC-004**: Zero user data or text queries leave the client browser, maintaining complete user privacy.
- **SC-005**: All text elements across both light and dark themes maintain a minimum contrast ratio of 4.5:1 (WCAG AA) and 15:1 for primary body text (WCAG AAA).

---

## Assumptions

- Users may access the tools from modern desktop browsers and mobile devices.
- All required linguistic datasets, epigraphical tables, and normalization routines are provided by the underlying client engine without third-party web service dependencies.
- Traditional epigraphical symbols rely on modern system fonts supporting Unicode 15.0+ Tamil Supplement block (`U+11FC0`–`U+11FFF`); fallback styling ensures legible representation.
