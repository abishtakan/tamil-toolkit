# LT-TM / IndoWord CID profile

Status: first bounded profile implemented in Rust and wired through the shared
dispatcher. Its 664 mapping vectors and 23 contract vectors are active after
owner review; Rust, Python, WASM, and Dart parity gates pass. This work does not
establish that every
LT-TM face, IndoWord installation, or Vanavil variant has an identical table.

## Identification and evidence

The Tamil Virtual Academy catalog identifies the 2003 Tamilmann edition of
*Tolkāppiyam – Eḻuttatikāram: Iḷampūraṇam*. Its digital PDF is typeset text with
embedded Type 0 font families named `LT-TM-*`, not a scan-only document. The
official TVA legacy font list associates IndoWord with `LT-TM-Lakshman`; Azhagi
identifies LT-TM as the same encoding family as IndoWord.

The embedded PDF fonts use `/Identity-H`, with CID values represented by
big-endian 16-bit units and an identity `ToUnicode` map. A generic text
extractor therefore does not recover Tamil Unicode from the font codes. The
first title run decodes as the code sequence
`[0x0062,0x006A,0x0068,0x0161,0x0066,0x0068,0x00A5,0x00E3,0x0061,0x00AB]`,
which produces Unicode scalars
`U+0BA4 U+0BCA U+0BB2 U+0BCD U+0B95 U+0BBE U+0BAA U+0BCD U+0BAA U+0BBF U+0BAF U+0BAE U+0BCD`.
This is a spot-check against the rendered PDF title. Other inspected page-one
runs from PDF faces `LT-TM-Nakkeran`, `LT-TM-Narmada`, `LT-TM-Nila,Bold`, and
`LT-TM-Sindhu` also decoded to their visible text. These five exact face names
are the only ones the v0.1 PDF extractor automatically decodes; other
`LT-TM-*` faces and style variants remain unverified. The checks are samples,
not a claim that every code assignment in each face was compared.

The canonical map in `lexicon/lt_tm.toml` is a normalized projection of the
public Azhagi+ Portable LT-TM configuration. The source configuration's
SHA-256 is
`32fc21ffe8e2fbffa33d5f3899acfd15ee8a2ab9fc5fd5e931f9e7d4ec3326cd`; the
archive digest is
`e5fbf4b1f9a5533ac70021119641c51ddfa1df99c54162b9fa74e32ae1c1d510`. The
configuration is not bundled in its original form. The archive license
restricts derivative works of the software and related author-generated files;
that provenance and the source digest are retained here. The repository's MIT
license does not replace upstream terms.

The table has 332 unique keys and 332 unique NFC output strings. Keys contain
one to three 16-bit values. No claim of independent derivation or universal
font-family equivalence is made. The SDEV LT-TM converter describes a
Vanavil-based layout with key differences, and the inspected difference is
material: CID `0x00C4` maps to `U+0BAE U+0BBF`, while `0x00E4` maps to
`U+0BB2 U+0BC0`. Vanavil is not an alias in this profile. AnuGraphics and
Pallavar remain separate.

## API contract

The decoder accepts either:

- `codes`: an array of unsigned 16-bit PDF character codes. This is the direct
  input for `/Identity-H` text after the caller combines string fragments from
  a `TJ` run in order.
- `text`: a string whose BMP scalar values are interpreted as code values.
  This is for legacy text already exposed as code-valued Unicode characters;
  it is not a byte decoder or Windows-1252 conversion.

Operations are `lt_tm_codes_to_unicode`, `lt_tm_text_to_unicode`,
`unicode_to_lt_tm_codes`, and `unicode_to_lt_tm_text`. They all use the
`lt-tm-indoword-cid-v1` profile. The codec does not parse PDF objects, infer
font runs, or detect encodings. Callers select the LT-TM profile and split text
by the PDF font resource before conversion. Values outside `0..=65535`,
non-BMP scalars in legacy text, and UTF-16 surrogate code units in `codes` are
rejected.

Decoding uses longest-key matching with a three-code maximum and normalizes
output to NFC. A mapped code sequence takes precedence over fallback. Unmapped
ASCII digits, printable punctuation, and tab/line-break whitespace pass
through; unmapped ASCII letters and other unmapped values fail under `strict`.
`preserve` copies an unmapped valid code point unchanged. It never removes
joiners. Invalid surrogate code units fail in both policies. The default error
policy is `strict`.

Encoding normalizes input to NFC, greedily uses the longest matching Unicode
entry, permits only the same unmapped ASCII digit/punctuation/whitespace
fallback, and verifies a strict decode round trip before returning. Therefore
unmapped Tamil, other scripts, letters in English font runs, and non-ASCII
symbols fail explicitly. Legacy English runs should remain assigned to their
own PDF font and must not be sent through this Tamil-font profile.

These code mappings do not vary between TN and SL. Fixtures use `dialect:
"COMMON"` for that code-level invariance; no regional language behavior is
implied.

## Acceptance and limits

- The lexicon contains exactly 332 unique code keys and unique NFC values;
  `build.rs` validates ranges, key lengths, output normalization, duplicates,
  and the expected profile identity before generating static tries.
- Golden vectors cover every mapping in decode and encode directions, plus the
  2003 PDF title, LT-TM text input, the checked `Ä`/`ä` distinction, Ksha,
  punctuation/digits, preserve behavior, malformed inputs, and unsupported
  Unicode. The suite is active following owner review.
- Rust owns all conversion behavior. Python, WASM, and Dart use the shared Rust
  JSON dispatcher without separate mapping logic.
- The profile does not yet claim complete compatibility with all LT-TM or
  IndoWord fonts, Vanavil compatibility, PDF parsing, automatic detection,
  arbitrary English mixed runs, or full Tamil Unicode encodability.

## Sources

- [TVA Digital Library record for the 2003 edition](https://tamildigitallibrary.in/book-details/TkRnMk9UYz1BdG9aYXRvejB0bzk-/TlE9PUF0b1phdG96MHRvOQ--/TWpBPUF0b1phdG96MHRvOQ--)
- [TVA legacy font/software list](https://www.tamilvu.org/en/tamil-softwares-old)
- [Azhagi font converter inventory](https://www.azhagi.com/tamil-fonts-converter.php)
- [Azhagi+ Portable archive](https://www.azhagi.com/sai/plus/new2/AzhagiPlus-Portable.zip) and [LT-TM conversion-file documentation](https://www.azhagi.com/any-tamil-font.php)
- [SDEV LT-TM converter](https://www.sdev.in/tools/tamil-font-converter/lt-tm-to-unicode), used only to identify a Vanavil comparison lead

The inspected PDF copy's SHA-256 is
`6a74647421923520338e0d14f5820014f6ade2c0b7a145fca6baf44a4079542f`.
