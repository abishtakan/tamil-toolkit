# Feature Specification: Interactive Tamil Syllabic Hyphenator & Line Wrapper (`playground-hyphenation`)

**Feature Directory**: `specs/010-playground-hyphenation`

**Created**: 2026-11-05

**Status**: Approved

**Input**: User request: "update the playground. if not documented please do the documentation 1st and then do it"

---

## 1. Overview & Cultural Significance

In digital Tamil typography, web layout, and print typesetting, standard word-wrapping algorithms frequently break words at arbitrary character boundaries or push long words to the next line, creating jagged margins (rivers of white space). More critically, standard wrapping often strands pure consonants with *pulli* (*Mei* e.g., `க்`, `த்`, `ம்`) or *Aytham* (`ஃ`) at the beginning of a line. In classical and modern Tamil grammatical rules (W3C `tam-lreq`, *Tolkappiyam*, *Nannool*), a *Mei* or *Aytham* is phonetically vowelless and can **never** initiate a line or syllable; it strictly binds to the preceding syllable nucleus.

The **Tamil Syllabic Hyphenator & Line Wrapper** (*சொல் & பத்தி அசையசைப்பி*) provides an interactive, zero-latency visual tool in the Tamil Toolkit Playground. It enables typographers, web developers, authors, editors, and students to:
1. Deconstruct Tamil words into phonotactically valid orthographic syllables.
2. Visualize safe hyphenation breakpoints and coda bindings.
3. Inject soft hyphens (`\u00AD`) into paragraphs for print and responsive web design.
4. Experiment with responsive line wrapping across customizable letter margins and column widths.

---

## 2. User Scenarios & Testing

### User Story 1 - Interactive Word Syllabification & Breakpoint Inspector (Priority: P1) 🎯 MVP

As a typographer, editor, or language researcher, I want to type or select a Tamil word and instantly see its syllabic decomposition with visual coda binding, so that I can verify valid hyphenation points and understand how consonants cluster around vowel nuclei.

**Acceptance Scenarios**:
1. **Given** a Tamil word (e.g., `தமிழ்நாடு`, `பல்கலைக்கழகம்`, `துர்ப்பிரயோகம்`), **When** entered into the word inspector, **Then** the tool displays the word broken into distinct syllable chips (e.g., `தமிழ்` · `நாடு` or `பல்` · `க` · `லைக்` · `க` · `ழ` · `கம்`).
2. **Given** any consonant cluster or coda sequence, **When** analyzed, **Then** the interface visually flags that *Mei* codas (e.g., `ழ்` in `தமிழ்`) bind backwards to the nucleus and never begin a downstream syllable.
3. **Given** configurable safe margins (`left_min` and `right_min`, default 2), **When** adjusted, **Then** the break points dynamically update, preventing hyphenation too close to word boundaries.
4. **Given** delimiter selection, **When** switching between visible hyphen (`-`), middle dot (`·`), forward slash (`/`), or soft hyphen (`\u00AD`), **Then** the hyphenated word updates instantaneously.

---

### User Story 2 - Paragraph Soft-Hyphen (`\u{00AD}`) Injector (Priority: P2)

As a web publisher, content creator, or typesetter, I want to paste a full Tamil or mixed-script paragraph and inject invisible soft hyphens (`&shy;` / `\u00AD`) into all Tamil words, so that web browsers and desktop publishing software (InDesign, Word) can wrap Tamil text gracefully without breaking non-Tamil words, numbers, or URLs.

**Acceptance Scenarios**:
1. **Given** mixed-script or Tamil paragraph text, **When** processed, **Then** soft hyphens are injected into Tamil words at valid syllable boundaries while English words, numbers, and URLs are preserved verbatim.
2. **Given** the visual toggle "Show soft hyphens", **When** enabled, **Then** invisible `\u00AD` characters are highlighted with high-contrast indicator badges (e.g., `[­]`).
3. **Given** processed text, **When** the user clicks "Copy Text" or "Copy HTML (`&shy;`)", **Then** the clipboard receives the exact format with toast confirmation.
4. **Given** text that already contains soft hyphens, **When** processed, **Then** the operation is idempotent and duplicates are never inserted.

---

### User Story 3 - Interactive Responsive Column & Line-Wrapping Simulator (Priority: P3)

As a responsive web designer, layout artist, or print publisher, I want an interactive container width slider to test how a Tamil paragraph wraps under various column widths, comparing standard browser wrapping against syllabic hyphenated wrapping.

**Acceptance Scenarios**:
1. **Given** a column width slider (from 10 to 60 Tamil letters or 180px to 600px container width), **When** moved, **Then** the live column simulator dynamically re-wraps the text line by line.
2. **Given** a comparison toggle ("Side-by-Side Diff"), **When** activated, **Then** the user sees:
   - *Default Wrapping*: Highlights stranded *Mei* line-starts and excessive whitespace gaps.
   - *Syllabic Wrapping*: Demonstrates clean syllable breaks with trailing hyphens and balanced margins.
3. **Given** wrapped lines, **When** inspected, **Then** the letter count per line and break positions are clearly annotated.

---

## 3. UI Design Specifications ("செம்புலப் பெயல் நீர்" Design Language)

Following the playground design constitution:
- **No Neon Gradients or AI Slop**: Clean earthen palm-leaf ivory canvas (`--bg-canvas: #faf7f2`), terracotta accents (`--color-semman: #963824`), sandalwood gold accents (`--color-sandhanam: #b88628`), and deep carbon ink typography (`--color-mai: #1f1a17`). In dark mode, clean basalt granite (`#0c0e11`) and slate surfaces (`#16191f`).
- **Tabbed Ergonomics**:
  - `Word Syllables` (*சொல் அசையசைப்பு*)
  - `Paragraph Soft-Hyphens` (*பத்தி மென்-அசையசைத்தல்*)
  - `Column Wrap Preview` (*வரி மடிப்பு முன்காட்சி*)
- **High-Density Data**:
  - Letter index and byte offset indicators.
  - Interactive preset chips (`தமிழ்நாடு`, `பல்கலைக்கழகம்`, `துர்ப்பிரயோகம்`, `வணக்கம்`, `யாழ்ப்பாணம்`, `கோயம்புத்தூர்`).
- **Tactile Feedback**:
  - 1px hairline transitions, responsive active press states (`active:scale-[0.99]`), accessible contrast (AAA for text, AA for badges).

---

## 4. Technical Architecture

- **Engine Binding**: Connects directly to `tamil-toolkit/web` via `tt.execute({ op: "hyphenate_word", input })`, `tt.execute({ op: "hyphenation_points", input })`, `tt.execute({ op: "hyphenate_text", input })`, and `tt.execute({ op: "wrap_text", input })`.
- **Offline / Resilient Fallback**: Includes a lightweight, pure TypeScript syllable segmentation fallback in `playground/src/lib/engine.ts` ensuring the playground renders immediately before or without WebAssembly.
- **Bilingual Internationalization**: 100% of labels, tooltips, presets, and error messages defined in both Tamil and English in `playground/src/lib/i18n.ts`.
