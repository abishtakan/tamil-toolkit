# PDF-aware LT-TM text extraction v0.1

Status: implemented as a private Python utility. `just test-pdf-extract` and
the full `just agent-pre-stop-gate` passed on 2026-11-01.
The optional OCR Markdown path was added on 2026-11-01; its focused suite
passes (13 tests). The latest agent gates stopped because Cargo is unavailable
in the local shell; no Rust code changed.

## Placement and responsibility

This is a private developer utility in `tools/tamil-pdf-extract/`, not a
public Cargo crate or umbrella SDK module. PDF object parsing and CLI output
are document I/O concerns and should not add a PDF dependency to the runtime
libraries. The utility uses pypdf for PDF structure. Optional OCR uses
pypdfium2/Pillow to render pages and a separately installed Tesseract process.
All font-code conversion must call `tamil_toolkit.execute` and the existing Rust
dispatcher. It must not implement or copy LT-TM mappings.

The first profile is explicitly selected with `--profile lt-tm`. The tool is
for the inspected 2003 Tamilmann *Tolkāppiyam* source, whose PDF has Type 0
fonts with `/Identity-H` and `LT-TM-*` base-font names. The codec's mapping
provenance and compatibility bounds are defined in
[`codec-lt-tm.md`](codec-lt-tm.md); this extractor does not broaden those
claims.

## Input and supported PDF content

- Accept a local, unencrypted PDF path and reject unreadable, encrypted, or
  structurally invalid documents with a nonzero CLI result and a diagnostic
  on stderr.
- Require the caller to select `lt-tm`; do not guess a codec from bytes,
  rendered text, font family, or page contents.
- Read page content streams in order. Support text-showing operators `Tj`,
  `TJ`, `'`, and `"`. For `TJ`, concatenate string operands in order and ignore
  numeric kerning adjustments; do not split a code sequence at array-fragment
  boundaries.
- Track the current `Tf` font resource. Decode only a Type 0 font with exact
  `/Identity-H` encoding and one of these visually spot-checked PDF face names:
  `LT-TM-Nehru`, `LT-TM-Nakkeran`, `LT-TM-Narmada`, `LT-TM-Nila,Bold`, or
  `LT-TM-Sindhu`. A six-uppercase-letter PDF subset prefix and `+` is stripped
  before this exact comparison. Other `LT-TM-*` faces and style variants stay
  unsupported until independently checked.
- Recurse through invoked Form XObjects using their own resources, preserve
  the page/form path and local operator index, and guard against a form cycle.
  Count invoked image XObjects and inline images. Default JSONL extraction
  does not OCR images; image-only pages remain explicitly unrecognized text in
  that output.
- Preserve unrecognized or unverified font runs as raw bytes with an
  `unsupported_font` status. Do not send them to the LT-TM codec.

## Output contract

The CLI emits UTF-8 JSON Lines: one record per text-showing operation and one
page summary after that page's runs. JSON strings must escape non-ASCII
characters so Tamil output can be reviewed as Unicode escapes. A text-run
record includes page number, content path, local operator index/name, font
resource and resolved font metadata, original string bytes as lowercase hex,
16-bit big-endian codes when the run is an even-length `/Identity-H` string,
status, decoded text when available, and an error when decoding fails.

Statuses are `decoded`, `unsupported_font`, `missing_font`,
`malformed_identity_h`, and `decode_error`. An odd-length Identity-H byte
string is malformed and must not be truncated. Surrogate code units and
unmapped strict-profile codes are reported as decoder errors with original
bytes retained. Joiners and all other decoded scalars are preserved exactly
as returned by the Rust dispatcher.

Page summaries report text-run counts by status, invoked form count, image
XObject count, and inline-image count. Output follows stream traversal order;
the tool does not infer word spaces, reorder columns, reconstruct paragraphs,
or make visual-layout claims. Rendering remains a human verification step for
the source document, not a fallback decoder.

## Acceptance criteria

1. The local package has a locked dependency set and a CLI entry point, but is
   excluded from Cargo workspace membership and public release allowlists.
2. Synthetic PDFs verify all four text-showing operators and TJ fragment
   concatenation using the shared Rust codec; expected Tamil is represented in
   source tests with `\u` escapes.
3. Synthetic PDFs verify an unsupported non-LT-TM font and an unverified
   LT-TM face are reported with raw bytes and never decoded, odd Identity-H
   input is reported without truncation, and a surrogate/decode failure
   retains its raw bytes.
4. A Form XObject's own font resources are traversed, cycles are bounded, and
   raster XObjects/inline images are counted without OCR claims.
5. The actual source PDF inventory reports per-page font identities, text
   run outcomes, and invoked raster-image counts. The title and representative
   runs are checked against rendered pages. Unknown fonts or decode errors are
   listed; zero errors for one file do not establish support for every
   LT-TM/IndoWord font.
6. Existing codec golden vectors remain unchanged and continue passing all
   repository gates. No Rust linguistic behavior or golden suite is changed.
7. Optional `--ocr-markdown` renders every PDF page and writes page-numbered
   Tesseract output to a separate Markdown file. It preserves OCR scalars and
   joiners as returned, labels the result as an unverified draft, and leaves
   the JSONL run records and Rust dispatcher unchanged. Tests verify page
   boundaries, joiner preservation, DPI validation, and CLI output routing.

## Source audit result

The 351-page source produced 24,356 text-showing operations across 38 font
names. The five allowlisted families account for 103 decoded runs with no
strict-codec errors. The other 24,253 runs across 31 font names remain
`unsupported_font`; these include other LT-TM faces as well as TTC and Times
fonts. The walk saw one invoked image XObject, no inline images, and no forms.
The default JSONL extraction performs no OCR. An independent PDFium text-page pass found all 103 raw
CID sequences, which checks the parser's code capture but not the codec's
Unicode mapping. Rendered pages 1, 3, 5, 6, 16, 17, 27, 40, 60, and 78 were
spot-checked; the title and visible decoded headings compared on those pages
matched. These counts do not constitute a full visual audit of all 103 runs
or a semantic verification of every code assignment in the allowlisted faces.
See the [decoded-run review ledger](codec-lt-tm-pdf-review.md) for every raw CID
sequence and Rust output scalar sequence, plus the readable spot-checks.

## Source and limits

The source evidence is the 2003 Tamilmann PDF described in
[`codec-lt-tm.md`](codec-lt-tm.md), SHA-256
`6a74647421923520338e0d14f5820014f6ade2c0b7a145fca6baf44a4079542f`.
The PDF is a digitally typeset document with embedded fonts, not a
scan-only source. The local inspection copy is not bundled or redistributed
by this package. Optional OCR is a separate review aid, not a validated
transcription and not a replacement for verified font mappings. It does not
implement general font auto-detection, page layout reconstruction, or
searchable-PDF generation.

### Standard Tesseract spot-check (2026-11-01)

Tesseract 5.4.0.20240606 with the standard `tam` model was run on pages 1, 81,
and 290 at 300 DPI with page segmentation modes 3 and 6. The cover and
one-column prose were mostly readable as drafts, though recognition and
spacing errors remained. The two-column index page contained fragmented and
misordered lines and a misread heading. The mode-3 output contained 15, 86,
and 43 U+200C scalars on pages 1, 81, and 290; mode 6 contained 14, 87, and 45.
No manually verified ground-truth transcription was available, so these samples
do not support CER/WER claims. Tesseract remains a draft aid and is not
accepted as a verified full-book transcription source.
