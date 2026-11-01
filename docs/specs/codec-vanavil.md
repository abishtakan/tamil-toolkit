# Vanavil (`Vanavil Avvaiyar`) CID profile

Status: first bounded profile implemented in Rust and wired through the shared
dispatcher. Its 638 mapping vectors and 23 contract vectors (661 total) are
active after owner review; Rust, Python, WASM, and Dart parity gates pass. This
work does not establish that every Vanavil face or installation has an identical
table.

## Identification and evidence

`Vanavil Avvaiyar` is the standard legacy font face distributed with the Vanavil
Tamil interface software listed in the Tamil Virtual Academy legacy software
inventory. While Vanavil and LT-TM (`LT-TM-*` / IndoWord) share the same ASCII
base consonant keys (`0x0021..0x007E`), pre-base vowel modifiers (`b` for
`U+0BC6`, `n` for `U+0BC7`, `i` for `U+0BC8`), post-base modifiers (`h` for
`U+0BBE`, `s` for `U+0BCC`/`U+0B94`, `&` and `]` for Grantha `-u`/`-uu`), and
Windows-1252 high-code scalars (`0x0152..0x203A`), their Latin-1 uppercase and
lowercase blocks `0x00C0..0x00CF` and `0x00E0..0x00EF` are transposed
(`code ^ 0x0020`).

Specifically:

- Every code assignment at `0x00C0..0x00CF` in `lt-tm-indoword-cid-v1`
  (`U+0B99 U+0BBF` through `U+0BB9 U+0BBF`) is at `0x00E0..0x00EF` in
  `vanavil-avvaiyar-cid-v1`.
- Every code assignment at `0x00E0..0x00EF` in `lt-tm-indoword-cid-v1`
  (`U+0BB9 U+0BCD`, `U+0B9A U+0BBF`, `U+0BA4 U+0BBF`, `U+0BAA U+0BBF`,
  `U+0BB2 U+0BC0` through `U+0B95 U+0BCD U+0BB7 U+0BC0`, `U+0BAF U+0BC1`,
  `U+0BB5 U+0BC1`, and `U+0B87`) is at `0x00C0..0x00CF` in
  `vanavil-avvaiyar-cid-v1`.
- For example, `0x00C4` (`Ä`) maps to `U+0BB2 U+0BC0` (`லீ`) and `0x00E4` (`ä`)
  maps to `U+0BAE U+0BBF` (`மி`) in Vanavil Avvaiyar, whereas LT-TM reverses
  those two slots. Similarly, independent vowel `இ` (`U+0B87`) is `0x00CF` (`Ï`)
  in Vanavil Avvaiyar versus `0x00EF` (`ï`) in LT-TM.
- `Vanavil Avvaiyar` maps Tamil credit sign `U+0BFA` (`௺`) at `0x00B7` (`·`)
  rather than `0x2219`, and does not assign distinct glyphs for Grantha `ஶ`
  (`U+0BB6`, which LT-TM places at `0x2122`, `0x2013`, `0x2014`, and `0x2022`).
  In the Azhagi+ Vanavil phonetic input table, the `ஶ` row falls back to `Z`
  (`U+0BB8 U+0BCD`) and `0x00F5` (`U+0BB7`), which already have unambiguous
  primary mappings (`ஸ்` and `ஷ`) and are therefore not duplicated as ambiguous
  `ஶ` entries in this profile.

The canonical map in `lexicon/vanavil.toml` is a normalized projection of the
public Azhagi+ Portable Vanavil configuration
(`AzhagiPlus-Tamil-Vanavil-PhoneticTransliteration.txt`). The source
configuration's SHA-256 is
`4948396d50fbbaf251ddfe620ca5d8a0ccdb65b5bef07231065a5d6439754b67`; the
archive digest is
`e5fbf4b1f9a5533ac70021119641c51ddfa1df99c54162b9fa74e32ae1c1d510`. The
configuration is not bundled in its original form. The archive license
restricts derivative works of the software and related author-generated files;
that provenance and the source digest are retained here. The repository's MIT
license does not replace upstream terms.

The glyph assignments were independently cross-checked against the `cmap` table
of `Vanavilavvai.ttf` (SHA-256
`ba7f814d22dbbf66498b19a52efb62b8412bc52bde0452e624af601d17b709a7`). Other
public converter tables (`open-tamil`'s `encode2utf8.py` under GPL-3.0-or-later,
TVA's `Vanavil.xml` under GPL-2.0, and `aril-core`'s `vanavil.rs` derived from
that lineage) were inspected only for mathematical verification and were not
copied or vendored.

The table has 319 unique keys and 319 unique NFC output strings. Keys contain
one to three 16-bit values. LT-TM, AnuGraphics, and Pallavar remain separate
profiles.

## API contract

The decoder accepts either:

- `codes`: an array of unsigned 16-bit character codes (`0..=65535`).
- `text`: a string whose BMP scalar values are interpreted as code values.
  This is for legacy text already exposed as code-valued Unicode characters
  (including Windows-1252 decoded scalars in `0x0152..0x203A`); it is not a raw
  8-bit byte decoder.

Operations are `vanavil_codes_to_unicode`, `vanavil_text_to_unicode`,
`unicode_to_vanavil_codes`, and `unicode_to_vanavil_text`. They all use the
`vanavil-avvaiyar-cid-v1` profile. The codec does not parse document containers,
infer font runs, or detect encodings. Values outside `0..=65535`, non-BMP
scalars in legacy text, and UTF-16 surrogate code units in `codes` are rejected.

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
unmapped Tamil (such as `U+0BB6` `ஶ`), other scripts, letters in English font
runs, and non-ASCII symbols fail explicitly.

These code mappings do not vary between TN and SL. Fixtures use `dialect:
"COMMON"` for that code-level invariance; no regional language behavior is
implied.

## Acceptance and limits

- The lexicon contains exactly 319 unique code keys and unique NFC values;
  `build.rs` validates ranges, key lengths, output normalization, duplicates,
  and the expected profile identity before generating static tries.
- Golden vectors cover every mapping in decode and encode directions, plus
  common Vanavil words/sentences, legacy text input, the checked `Ä`/`ä` and
  `Ï`/`ï` distinctions against LT-TM, Ksha (`B`, `ø`, `Ì`, `º`), Shri (`$`),
  punctuation/digits, preserve behavior, malformed inputs, and unsupported
  Unicode (including `U+0BB6` `ஶ`).
- Rust owns all conversion behavior. Python, WASM, and Dart use the shared Rust
  JSON dispatcher without separate mapping logic.
- The profile does not claim complete compatibility with all Vanavil font faces,
  LT-TM compatibility, document parsing, automatic detection, arbitrary English
  mixed runs, or full Tamil Unicode encodability.

## Sources

- [TVA legacy font/software list](https://www.tamilvu.org/en/tamil-softwares-old)
- [Azhagi font converter inventory](https://www.azhagi.com/tamil-fonts-converter.php)
- [Azhagi+ Portable archive](https://www.azhagi.com/sai/plus/new2/AzhagiPlus-Portable.zip) and [Vanavil conversion-file documentation](https://www.azhagi.com/any-tamil-font.php)
- [SDEV Vanavil to Unicode converter](https://www.sdev.in/tools/tamil-font-converter/vanavil-to-unicode), used only as an independent behavior comparison
