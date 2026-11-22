# Bharathi Tamil Braille Grade 1 profile (`tamil-codec::braille`)

Status: Phase 7B engineering contract (2026-11-22). Profile: `bharathi-tamil-g1-v1`.

## Standard and provenance

Implements uncontracted Grade 1 **Bharathi Braille for Tamil** mapped to Unicode
Braille Patterns (`U+2800..U+28FF`), following *World Braille Usage* (3rd Edition,
UNESCO / Perkins / ICEVI / WBU) and India's NIEPVD Bharathi Braille standard
(cross-checked mathematically against Liblouis `ta-ta-g1.ctb`).

- Dot bitmask formula: `U+2800 + sum(1 << (dot - 1))` for dots 1–6.
- Pulli / Virama (`\u0BCD`, `்`) is represented by dot 4 (`\u2808`, `⠈`)
  **preceding** the base consonant cell (e.g., `க்` -> `⠈⠅`, `தமிழ்` -> `⠞⠍⠊⠈⠷`).
- Conjunct `க்ஷ` (`\u0B95\u0BCD\u0BB7`) uses the dedicated Bharathi cell
  dots 1-2-3-4-5 (`\u281F`, `⠟`); `க்ஷ்` -> `⠈⠟`.
- Inherent vowel `அ` (`\u0B85`) is omitted after consonants (as in Tamil Unicode);
  standalone `அ` uses dot 1 (`\u2801`, `⠁`).
- Dependent vowel signs (`ா..ௌ`) share the same Braille cell as their
  corresponding independent vowels (`ஆ..ஔ`) and follow the consonant cell.
- ASCII space (` `) maps to Braille Pattern Blank (`\u2800`, `⠀`) on encode;
  both `\u2800` and ASCII `' '` decode to ASCII `' '`. Tab and line breaks
  (`\t`, `\r`, `\n`) pass through unchanged in both directions.

## Public operations

- `unicode_to_braille { text, errors? } -> string`: NFC-normalizes input and
  encodes Tamil letters, conjunct `க்ஷ`, pulli forms, Aytham, spaces, and
  tab/newlines to Unicode Braille (`U+2800..U+28FF`). Under `strict` (default),
  unsupported scalars fail with
  `unsupported Unicode scalar for Braille at NFC byte <offset>: U+<HEX>`.
  Under `preserve`, unsupported scalars (including ZWJ/ZWNJ) pass through unchanged.
- `braille_to_unicode { text, errors? } -> string`: decodes Bharathi Tamil Grade 1
  Braille cells back to NFC Tamil Unicode. Under `strict` (default), unsupported
  Braille cells or dangling dot-4 pulli markers fail with
  `unsupported Braille scalar at character <index>: U+<HEX>` or
  `invalid Braille pulli sequence at character <index>`.
  Under `preserve`, unknown cells pass through unchanged.

## Guarantees

- Every Tamil vowel, consonant (18 native + 5 Grantha), `க்ஷ`, Aytham, uyirmei,
  and mei form has a distinct, unambiguous Bharathi Braille representation and
  round-trips losslessly (`braille_to_unicode(unicode_to_braille(s)) == normalize_nfc(s)`).
- TN and SL dialects are invariant (`dialect: "COMMON"`).
