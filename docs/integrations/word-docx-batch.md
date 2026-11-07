# Headless OpenXML DOCX Batch Hyphenation Guide

This guide covers batch processing of Microsoft Word (`.docx`) manuscripts, academic books, and legal documents for clean, grammatically sound Tamil justification.

---

## 1. Why Batch-Process `.docx` Documents?

Desktop publishing applications (LibreOffice, InDesign, Scribus) accept Frank Liang / Hunspell `.dic` pattern files directly. In contrast, Microsoft Word uses signed, closed binary proofing packages and lacks built-in Tamil syllabic line-breaking.

The universal cross-platform solution is the **Unicode Soft Hyphen (`\u00AD`)**:
- **On the same line**: `\u00AD` has zero glyph width (`0px`). It remains completely invisible; kerning, tracking, and letter spacing are untouched.
- **At margin collision**: When paragraph alignment is set to **Justified (`Ctrl + J`)**, Word automatically wraps the word at the soft hyphen and displays `-` at the end of the line.
- **Copy/Search safe**: Soft hyphens are ignored by search engines and spell checkers.

`tamil-toolkit hyphen process-docx` automatically traverses all prose runs in a Word document and injects soft hyphens in seconds without manual intervention.

---

## 2. Using the CLI

### Basic Usage
Process an input document to a new file:
```bash
tamil-toolkit hyphen process-docx --input manuscript.docx --output manuscript_justified.docx
```

### In-Place Atomic Replacement
Update the document directly in-place:
```bash
tamil-toolkit hyphen process-docx --input manuscript.docx --inplace --verbose
```

### Options Reference
| Option | Short | Default | Description |
|---|---|---|---|
| `--input <PATH>` | `-i` | (Required) | Source `.docx` file |
| `--output <PATH>` | `-o` | None | Destination `.docx` path (required unless `--inplace` is used) |
| `--inplace` | | `false` | Overwrite the input file atomically |
| `--left-min <N>` | `-l` | `2` | Minimum Tamil letters before first hyphen |
| `--right-min <N>` | `-r` | `2` | Minimum Tamil letters after last hyphen |
| `-v, --verbose` | `-v` | `false` | Print detailed processing statistics |

### Example CLI Output
```text
Successfully processed docx: manuscript.docx -> manuscript_justified.docx
  Parts updated: 4 (word/document.xml, word/header1.xml, word/footer1.xml, word/footnotes.xml)
  Paragraphs scanned: 1,420
  Tamil words evaluated: 18,340
  Soft hyphens (U+00AD) injected: 31,520
```

---

## 3. Using the Python SDK

### Direct Python API
```python
import tamil_toolkit as tamil

stats = tamil.process_docx(
    input_path="manuscript.docx",
    output_path="manuscript_justified.docx",
    left_min=2,
    right_min=2,
)

print(f"Injected {stats['soft_hyphens_inserted']} soft hyphens across {stats['paragraphs_processed']} paragraphs.")
```

### Integration with `python-docx`
If your publishing pipeline already manipulates `.docx` files using `python-docx`:
```python
import docx
import tamil_toolkit as tamil

doc = docx.Document("input.docx")

for para in doc.paragraphs:
    for run in para.runs:
        # Check if run contains Tamil
        if any('\u0b80' <= c <= '\u0bff' for c in run.text):
            run.text = tamil.hyphenate_text(run.text)

doc.save("output_justified.docx")
```

---

## 4. Microsoft Word Typesetting Workflow

1. **Process Document**:
   Run `tamil-toolkit hyphen process-docx --input book.docx --output book_ready.docx`.
2. **Open in Word**:
   Open `book_ready.docx` in Microsoft Word (Desktop or Web).
3. **Set Justification**:
   Select all text (`Ctrl + A`) and press **Justify (`Ctrl + J`)**.
4. **Inspect Soft Hyphens (Optional)**:
   Press **`Ctrl + Shift + 8`** (or `Ctrl + *`) to toggle formatting marks. Soft hyphens appear as small discretionary hyphen marks (`¬`) in Word.
5. **Print or Export to PDF**:
   When printed or exported to PDF, soft hyphens that fall at margin boundaries render cleanly as standard hyphens (`-`). Soft hyphens within the line remain 100% invisible.
