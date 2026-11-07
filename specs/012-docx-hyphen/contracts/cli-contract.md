# CLI Contract: `tamil-toolkit hyphen process-docx`

## Usage
```bash
tamil-toolkit hyphen process-docx [OPTIONS] --input <INPUT_PATH>
```

## Options
| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--input <PATH>` | `-i` | Path | (Required) | Source `.docx` file to process |
| `--output <PATH>` | `-o` | Path | None | Destination `.docx` path (required unless `--inplace` is given) |
| `--inplace` | | Flag | `false` | Atomically overwrite the input file with hyphenated content |
| `--left-min <N>` | `-l` | Integer | `2` | Minimum character margin before first hyphen |
| `--right-min <N>` | `-r` | Integer | `2` | Minimum character margin after last hyphen |
| `--verbose` | `-v` | Flag | `false` | Print detailed processing statistics to stdout |

## Exit Codes
- `0`: Success. The output document is valid and written to disk.
- `1`: Invalid arguments (e.g. neither `--output` nor `--inplace` provided).
- `2`: File not found or read/write I/O error.
- `3`: Malformed ZIP archive or invalid OpenXML structure.

## Output
When `--verbose` is set:
```text
Successfully processed docx: book.docx -> book_justified.docx
  Parts updated: 3 (word/document.xml, word/header1.xml, word/footnotes.xml)
  Paragraphs scanned: 1,420
  Tamil words evaluated: 18,340
  Soft hyphens (U+00AD) injected: 31,520
```
