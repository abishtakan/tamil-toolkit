# Feature Specification: Headless OpenXML DOCX Batch Processor for Tamil Soft-Hyphenation (`docx-hyphen`)

**Feature Branch**: `012-docx-hyphen`

**Created**: 2026-11-07

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "Phase 2 of the Word & Google Docs long-term integration roadmap: Implement headless OpenXML DOCX batch processing CLI subcommand (`tamil-toolkit hyphen process-docx`), Rust crate API, and Python SDK for Tamil soft-hyphenation."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Headless DOCX CLI Batch Hyphenation (Priority: P1) 🎯 MVP

As a book publisher, academic author, or typographer working with Microsoft Word manuscripts (`.docx`), I want a CLI tool `tamil-toolkit hyphen process-docx` that scans an entire Word document, detects Tamil text runs, and injects invisible Unicode Soft-Hyphens (`\u{00AD}`) at phonotactically verified syllable boundaries, so that when the document is opened in Microsoft Word with Justified alignment (`Ctrl + J`), Tamil paragraphs break cleanly at margins without awkward white rivers or manual hyphen insertion.

**Why this priority**: Word manuscripts and legal documents contain hundreds of pages. Authors cannot manually copy and paste paragraphs through web interfaces. A headless CLI tool enables batch processing of entire books, contracts, and journals in seconds.

**Independent Test**: Can be tested independently by taking a standard `.docx` file with Tamil text, running `tamil-toolkit hyphen process-docx --input book.docx --output book_justified.docx`, unzipping the output, and verifying that `<w:t>` elements in `word/document.xml` contain `\u{00AD}` at syllable breaks while paragraph styles, runs, bold/italics, and non-Tamil words are completely untouched.

**Acceptance Scenarios**:
1. **Given** an input `.docx` file containing Tamil text, **When** running `tamil-toolkit hyphen process-docx --input in.docx --output out.docx`, **Then** all Tamil text runs inside `<w:t>` have soft-hyphens injected at valid syllable boundaries, respecting `LEFTHYPHENMIN 2` and `RIGHTHYPHENMIN 2`.
2. **Given** a `.docx` containing styled runs (bold, italic, font changes, color, highlighting), **When** processing the document, **Then** all XML tags, run properties (`<w:rPr>`), bookmarks, hyperlinks, comments, and table structures (`<w:tbl>`) remain valid and byte-for-byte syntactically intact.
3. **Given** a document containing mixed Tamil, English, Arabic numerals, URLs, and punctuation, **When** processed, **Then** non-Tamil tokens are preserved with zero modifications or corruptions.
4. **Given** an already-hyphenated `.docx` file, **When** processed a second time with `process-docx`, **Then** the process is idempotent and does not inject duplicate soft-hyphens (`\u{00AD}\u{00AD}`).
5. **Given** a `--inplace` flag, **When** invoked, **Then** the source document is safely processed via an atomic temporary file replacement.

---

### User Story 2 - Rust Core API & In-Memory OpenXML Processing (Priority: P2)

As a Rust developer building typesetting pipelines or web backends, I want in-memory buffer and file-based APIs in the `tamil-hyphen` crate for processing OpenXML `.docx` byte streams directly without disk roundtrips.

**Why this priority**: High-throughput document servers, web conversion services, and automated build bots require in-memory stream processing without temporary disk writes.

**Independent Test**: Can be tested by passing a `Vec<u8>` containing `.docx` ZIP data to `process_docx_bytes`, verifying that the returned bytes form a valid, loadable `.docx` archive with verified soft-hyphen injection and an accurate `DocxStats` summary.

**Acceptance Scenarios**:
1. **Given** a valid `.docx` byte slice, **When** calling `tamil_hyphen::docx::process_docx_bytes(&bytes, &config)`, **Then** it returns `Ok((output_bytes, stats))` where `stats.paragraphs_processed`, `stats.words_hyphenated`, and `stats.soft_hyphens_inserted` accurately reflect the changes.
2. **Given** an invalid or non-ZIP file, **When** passed to the API, **Then** it returns an explicit `DocxError::InvalidArchive` or `DocxError::CorruptXml` rather than panicking.
3. **Given** text across multiple OpenXML XML parts (`word/document.xml`, `word/header*.xml`, `word/footer*.xml`, `word/footnotes.xml`, `word/endnotes.xml`), **When** processed, **Then** headers, footers, and footnotes are hyphenated with the same phonotactic guarantees as the main body.

---

### User Story 3 - Python SDK & Scripting Interface (Priority: P3)

As a Python data scientist, publisher, or content manager, I want a Python binding `tamil_toolkit.hyphen.process_docx(input_path, output_path)` and a recipe for `python-docx` integration, so that I can automate document processing in Python workflows.

**Why this priority**: Python is the lingua franca of batch document publishing, NLP pipelines, and academic digital humanities tools.

**Independent Test**: In Python, run `tamil_toolkit.hyphen.process_docx("test.docx", "out.docx")` and assert that the file is created, valid, and returns a dict with processing statistics.

**Acceptance Scenarios**:
1. **Given** Python 3.11+, **When** importing `tamil_toolkit.hyphen` and running `process_docx(input_path, output_path)`, **Then** the target file is created with soft hyphens and returns a dictionary with processing counts.
2. **Given** invalid file paths, **When** called from Python, **Then** it raises a Python `FileNotFoundError` or `ValueError` with clear error messages.

---

### User Story 4 - Word Document Integration Documentation & Verification (Priority: P4)

As a technical writer and document author, I want detailed documentation and step-by-step guides showing how to use `process-docx` with Microsoft Word, LibreOffice, and Google Docs, along with empirical verification on real-world test documents.

**Why this priority**: Users need to understand how the soft-hyphen workflow functions in Microsoft Word (e.g. enabling Justify `Ctrl + J`, adjusting paragraph margins, and viewing soft-hyphens with `Ctrl + Shift + *`).

**Independent Test**: Read `docs/integrations/word-docx-batch.md` and execute test scenarios on sample `.docx` documents.

**Acceptance Scenarios**:
1. **Given** the documentation in `docs/integrations/word-docx-batch.md`, **When** followed by an end user, **Then** it provides clear instructions on batch processing, Microsoft Word paragraph justification, and keyboard shortcuts.
2. **Given** a golden test suite of `.docx` fixtures, **When** run through the test harness, **Then** all fixtures pass structure and content integrity checks.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an OpenXML parser and serializer capable of reading and updating `.docx` archives (ZIP files).
- **FR-002**: System MUST parse XML text nodes (`<w:t>`) within paragraphs (`<w:p>`) across:
  - `word/document.xml` (main text)
  - `word/header*.xml` (document headers)
  - `word/footer*.xml` (document footers)
  - `word/footnotes.xml` (footnotes)
  - `word/endnotes.xml` (endnotes)
- **FR-003**: System MUST identify Tamil words within `<w:t>` elements and insert Unicode Soft-Hyphens (`\u{00AD}`) at valid syllable break points using `tamil-hyphen::hyphenate_text`.
- **FR-004**: System MUST strictly preserve all other OpenXML files (e.g., `[Content_Types].xml`, `_rels/.rels`, `word/styles.xml`, `word/fontTable.xml`, `word/settings.xml`) and all sibling/parent XML tags and attributes without alteration.
- **FR-005**: System MUST guarantee idempotency: scanning text that already contains `\u{00AD}` MUST NOT inject duplicate soft-hyphens.
- **FR-006**: System MUST expose a CLI subcommand:
  ```bash
  tamil-toolkit hyphen process-docx [OPTIONS] --input <FILE>
  ```
  Options:
  - `-i, --input <PATH>`: Input `.docx` file path.
  - `-o, --output <PATH>`: Output `.docx` file path (required unless `--inplace` is specified).
  - `--inplace`: Overwrite the input file safely using atomic replacement.
  - `--left-min <N>`: Minimum letters before first hyphen (default: `2`).
  - `--right-min <N>`: Minimum letters after last hyphen (default: `2`).
  - `-v, --verbose`: Print detailed statistics (paragraphs, words, hyphens inserted).
- **FR-007**: System MUST provide Rust public functions in `tamil_hyphen::docx`:
  - `process_docx_bytes(data: &[u8], config: Option<&HyphenationConfig>) -> Result<(Vec<u8>, DocxStats), DocxError>`
  - `process_docx_file<P: AsRef<Path>, Q: AsRef<Path>>(input: P, output: Q, config: Option<&HyphenationConfig>) -> Result<DocxStats, DocxError>`
- **FR-008**: System MUST expose Python bindings in `tamil_toolkit.hyphen.process_docx(input_path, output_path, left_min=2, right_min=2)`.
- **FR-009**: System MUST document integration instructions in `docs/integrations/word-docx-batch.md`.

---

## Success Criteria *(mandatory)*

- **SC-001**: 100% preservation of non-Tamil text, paragraph formatting runs, bookmarks, hyperlinks, comments, tables, and images in processed `.docx` files.
- **SC-002**: Zero broken diacritics (zero occurrences of line-initial or isolated virama, combining vowel signs, or Aytham).
- **SC-003**: Exactly 0 duplicate soft-hyphens when processing a document multiple times.
- **SC-004**: Processing performance of at least 500 pages per minute (under 1 second for typical 50-page manuscripts).
- **SC-005**: All output `.docx` files open cleanly in Microsoft Word (2016, 2019, 2021, M365) and LibreOffice Writer without XML corruption warnings or repair prompts.
