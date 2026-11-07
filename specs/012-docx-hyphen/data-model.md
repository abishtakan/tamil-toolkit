# Data Model: Headless OpenXML DOCX Batch Processor (`docx-hyphen`)

**Feature**: `012-docx-hyphen` | **Date**: 2026-11-07

---

## 1. Entities & Types

### `DocxStats`
Metrics returned after processing a `.docx` document:
```rust
#[derive(Debug, Clone, PartialEq, Eq, Default, serde::Serialize, serde::Deserialize)]
pub struct DocxStats {
    /// Number of distinct XML parts inspected and updated (e.g. document.xml, headers, footers).
    pub parts_updated: usize,
    /// Total count of <w:p> paragraph elements traversed.
    pub paragraphs_processed: usize,
    /// Total count of Tamil words detected and evaluated.
    pub words_hyphenated: usize,
    /// Total count of soft hyphens (U+00AD) newly injected.
    pub soft_hyphens_inserted: usize,
}
```

### `DocxError`
Error taxonomy for `.docx` archive traversal and XML parsing:
```rust
#[derive(Debug, thiserror::Error)]
pub enum DocxError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("ZIP archive error: {0}")]
    Zip(#[from] zip::result::ZipError),

    #[error("Invalid OpenXML document: {0}")]
    InvalidArchive(String),

    #[error("Malformed XML in part '{part}': {error}")]
    XmlError { part: String, error: String },
}
```

### `DocxPartTarget`
Enumeration of XML parts within a `.docx` container that contain readable prose:
- `word/document.xml`
- `word/header*.xml` (e.g. `word/header1.xml`, `word/header2.xml`)
- `word/footer*.xml` (e.g. `word/footer1.xml`, `word/footer2.xml`)
- `word/footnotes.xml`
- `word/endnotes.xml`

All other parts in the ZIP container (e.g., `[Content_Types].xml`, `_rels/.rels`, styles, settings, theme, media images) are passed through byte-for-byte unmodified.
