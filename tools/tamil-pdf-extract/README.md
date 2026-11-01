# tamil-pdf-extract

Private local utility for extracting text runs from the inspected 2003
Tamilmann PDF when its font uses the LT-TM Identity-H mapping. PDF parsing is
handled by pypdf; Tamil conversion is delegated to the existing Rust-backed
`tamil-toolkit` Python binding.

Automatic decoding is restricted to the exact spot-checked faces
`LT-TM-Nehru`, `LT-TM-Nakkeran`, `LT-TM-Narmada`, `LT-TM-Nila,Bold`, and
`LT-TM-Sindhu`. Other font faces, including other names beginning `LT-TM-`,
are emitted as unsupported raw runs pending independent mapping checks.

From the repository root:

```powershell
uv run --project tools/tamil-pdf-extract --locked tamil-pdf-extract path\to\2003.pdf --profile lt-tm
```

The command writes JSONL to stdout. Tamil strings are JSON-escaped. Each text
record retains page, content path, operator, font, raw byte hex, code units,
status, and decoded text or error. Page summaries report image/form counts.
Redirect stdout to a file to preserve the extraction. Default mode does not
OCR. The optional OCR mode below writes a separate, page-numbered Markdown
draft and does not change JSONL extraction records.

## Optional page OCR draft

Install the optional PDF rendering dependencies:

~~~powershell
uv sync --project tools/tamil-pdf-extract --locked --extra ocr
~~~

Install Tesseract OCR with its Tamil language data separately, then request a
page-numbered Markdown draft:

~~~powershell
uv run --project tools/tamil-pdf-extract --locked --extra ocr tamil-pdf-extract path\to\source.pdf --profile lt-tm --ocr-markdown target\review.md --tesseract "C:\Program Files\Tesseract-OCR\tesseract.exe" > $null
~~~

OCR mode renders every page and writes the recognized text to the Markdown
file. It is machine-generated draft text, not a verified transcription: OCR
can insert, omit, or substitute Tamil characters and joiners. Compare every
page with the PDF before using the text as a source. The extractor does not
reconstruct columns, tables, or reading order.

This package is not a public SDK distribution. Its version and supported
profile are governed by
[`../../docs/specs/pdf-extract-v0.1.md`](../../docs/specs/pdf-extract-v0.1.md).
