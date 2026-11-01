# LT-TM / IndoWord codec source assessment

Status: the PDF's encoding family is identified as LT-TM / IndoWord. A public
LT-TM configuration is available in Azhagi+ Portable, but the bundled license
restricts derivative works of its software and related author-generated files.
Do not copy it into the toolkit. Independently derive and verify a reusable
map, and finalize the public input representation, before implementation.
There is no implementation or active golden suite.

## Finding

The Tamil Virtual Academy Digital Library catalogs the source as the 2003
Tamilmann edition of *Tolkāppiyam – Eḻuttatikāram: Iḷampūraṇam*. The downloaded
PDF is digitally typeset text, not a scan-only document. Its text is rendered
with embedded Type 0 fonts whose family names include `LT-TM-Roja`,
`LT-TM-Mullai`, `LT-TM-Anita`, `LT-TM-Sindhu`, `LT-TM-Pandian`, and other
`LT-TM-*` faces. The inspected copy contains 18 face/style names across 12
families.

The official TVA software list pairs AnuGraphics with Pallavar and IndoWord
with `LT-TM-Lakshman` in its old non-Unicode font inventory. Azhagi explicitly
describes LT-TM as the same encoding as IndoWord. These sources support
identifying the PDF as an LT-TM / IndoWord-family font encoding, rather than
Bamini, TSCII, TAB, TAM, or Anjal. They do not make AnuGraphics or Pallavar
aliases for LT-TM.

An Azhagi+ LT-TM configuration spot-check agrees with the PDF's visible title:
the first `/F1` run begins with CIDs `0062 006A 0068` (`bjh`), which the LT-TM
profile renders as U+0BA4 U+0BCA. This is one checked sequence, not full
document-wide validation.

Do not yet claim that every `LT-TM-*` face and IndoWord share one complete code
table. A modern LT-TM converter describes its profile as based on Vanavil with
a few keys changed. This is a useful comparison lead, not proof of
equivalence. Compare the actual mappings before declaring aliases.

## PDF text representation

The embedded fonts use `/Identity-H` and `CIDFontType2`, with `/CIDToGIDMap`
streams. Their `/ToUnicode` CMaps map each CID to the same numeric value, so
the PDF's text layer does not carry reliable Tamil Unicode. A generic text
extractor can return the legacy codes as unrelated characters or replacement
characters even though the page visibly renders correctly.

PDF content strings are 16-bit big-endian character codes under `/Identity-H`;
the inspected CIDs include values beyond the byte range. This PDF-layer form
must not be silently treated as raw 8-bit input or as Windows-1252. Determine
whether the public codec accepts legacy text characters, bytes, or explicit
16-bit CIDs, and document how a caller supplies the font selection. The codec
itself should not parse PDFs or infer font runs.

The inspected local PDF copy has SHA-256
`6a74647421923520338e0d14f5820014f6ade2c0b7a145fca6baf44a4079542f`.
The PDF is not copied into this repository; use the catalog link below to
retrieve the source and verify the digest.

## Mapping reference and reuse limit

Azhagi+ Portable documents support for LT-TM and includes
`AzhagiPlus-Tamil-LtTm-PhoneticTransliteration.txt` in its Tamil
`Tamil-All-PhoneticTransliteration` directory. The text file is UTF-16, 5,386
bytes, and is a structured key-sequence configuration rather than a direct
one-byte code table. The official Azhagi documentation says these files support
typing and conversion. The archive's `License.txt` grants free use of Azhagi+
but prohibits derivative works of the software or documentation, and defines
the software to include related author-generated files. Treat the configuration
as a comparison reference only; it was not added to the repository or copied
into the lexicon.

For reproducibility, the public [Azhagi+ Portable archive](https://www.azhagi.com/sai/plus/new2/AzhagiPlus-Portable.zip)
downloaded for this assessment has SHA-256
`e5fbf4b1f9a5533ac70021119641c51ddfa1df99c54162b9fa74e32ae1c1d510`; the
LT-TM text file has SHA-256
`32fc21ffe8e2fbffa33d5f3899acfd15ee8a2ab9fc5fd5e931f9e7d4ec3326cd`; and
the bundled license has SHA-256
`8c8801d01086a51edaa5db6afa5f4895b7ba14faa0dfee52f03e6163a6b5baa4`.
The [portable download page](https://azhagi.com/steps-portable.php) describes
the package; the [conversion-file documentation](https://www.azhagi.com/any-tamil-font.php)
describes LT-TM text files and their role.

## Implementation gate

Before implementation:

1. Independently derive the map from inspectable LT-TM font/code evidence and
   readable Tamil source text, or obtain a separately licensed mapping source.
   Record version, digest, attribution, and terms. Do not copy Azhagi's
   author-generated configuration.
2. Compare code-to-Unicode assignments for the PDF's embedded LT-TM faces and
   the proposed IndoWord/Vanavil aliases. Keep AnuGraphics/Pallavar separate
   unless a mapping comparison proves equivalence. Record conflicts and
   unsupported codes instead of selecting by font name alone.
3. Specify the input unit, selected-profile behavior, decode/encode direction,
   normalization, punctuation and English handling, invalid input behavior,
   and whether any encoder is one-to-one.
4. Add escaped, sourced golden vectors before Rust code. Include vectors
   verified against this PDF's rendered pages and an independent mapping
   reference. Keep the suite planned until the map is independently reviewed.
5. Implement the bounded profile in Rust and expose it through the shared
   dispatcher and thin Python, WASM, and Dart bindings. Do not add PDF parsing or
   automatic font/encoding detection to the codec profile.

## Sources

- [Tamil Virtual Academy Digital Library record for the 2003 source](https://tamildigitallibrary.in/book-details/TkRnMk9UYz1BdG9aYXRvejB0bzk-/TlE9PUF0b1phdG96MHRvOQ--/TWpBPUF0b1phdG96MHRvOQ--)
- [TVA legacy font/software list](https://www.tamilvu.org/en/tamil-softwares-old) (pairs AnuGraphics/Pallavar and IndoWord/LT-TM-Lakshman)
- [Azhagi font converter inventory](https://www.azhagi.com/tamil-fonts-converter.php) (identifies LT-TM as the same encoding as IndoWord)
- [SDEV LT-TM converter](https://www.sdev.in/tools/tamil-font-converter/lt-tm-to-unicode) (describes a Vanavil-based layout with some key differences; comparison lead only)
- [Azhagi+ Portable download page](https://azhagi.com/steps-portable.php) and [LT-TM conversion-file documentation](https://www.azhagi.com/any-tamil-font.php) (public comparison reference; bundled license restricts derivative works)
