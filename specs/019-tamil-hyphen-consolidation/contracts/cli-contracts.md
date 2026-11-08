# CLI Interface Contracts: tamil-toolkit CLI

## Binary: `tamil-toolkit`

### Global Syntax
```
tamil-toolkit <COMMAND> <SUBCOMMAND> [OPTIONS] [ARGUMENTS]
```

### 1. `core` Subcommands
- `tamil-toolkit core letters <TEXT> [--json]`
  - Output: Lines of tailored letters or JSON array `["த", "மி", "ழ்"]`.
- `tamil-toolkit core inspect <TEXT>`
  - Output: JSON string with `nfc`, `nfd`, `ezhuthu_count`, `grapheme_count`, `letters`.
- `tamil-toolkit core split-uyirmei <LETTER>`
  - Output: JSON object `{"mei": "...", "uyir": "..."}` or exit code 1 if invalid.
- `tamil-toolkit core compose-uyirmei <MEI> <UYIR>`
  - Output: Single composed Tamil letter (e.g. `க` + `அ` -> `க`).

### 2. `norm` Subcommands
- `tamil-toolkit norm nfc <TEXT>`
  - Output: Canonical NFC string.
- `tamil-toolkit norm nfd <TEXT>`
  - Output: Canonical NFD string.
- `tamil-toolkit norm repair <TEXT> [--json]`
  - Output: Repaired text (or JSON object including diagnostic repair counts).
- `tamil-toolkit norm fold <TEXT> [--profile default|mayangoli|grantha]`
  - Output: Folded search key string.

### 3. `codec` Subcommands
- `tamil-toolkit codec convert <TEXT> --from <ENC> --to <ENC>`
  - Encodings: `unicode`, `tscii`, `tam`, `tab`, `anjal`.
  - Output: Converted string.
- `tamil-toolkit codec detect <TEXT>`
  - Output: JSON `{"encoding": "...", "confidence": 0.95}`.

### 4. `collate` Subcommands
- `tamil-toolkit collate compare <STR1> <STR2>`
  - Output: `-1` (if STR1 < STR2), `0` (if STR1 == STR2), `1` (if STR1 > STR2).
- `tamil-toolkit collate key <TEXT> [--profile default|uyirmei_first]`
  - Output: Hexadecimal sort key string.
- `tamil-toolkit collate sort <FILE>`
  - Output: Lines from file sorted by Tamil alphabetical order.

### 5. `numerals` Subcommands
- `tamil-toolkit numerals to-words <NUMBER>`
  - Output: Tamil words string (e.g. `2026` -> `இரண்டாயிரத்து இருபத்து ஆறு`).
- `tamil-toolkit numerals to-numeral <NUMBER>`
  - Output: Traditional Tamil numeral string.
- `tamil-toolkit numerals parse <WORDS>`
  - Output: Parsed integer.

### 6. `calendar` Subcommands
- `tamil-toolkit calendar info [--date YYYY-MM-DD]`
  - Output: JSON object with Tamil year name, month name, day, paksha, thithi, nakshatra.

### 7. `hyphen` Subcommands
- `tamil-toolkit hyphen word <WORD> [-l N] [-r N] [-d DELIM]`
  - Output: Hyphenated word string.
- `tamil-toolkit hyphen text <TEXT> [-l N] [-r N] [-d DELIM]`
  - Output: Hyphenated text with soft-hyphens or custom delimiter.
- `tamil-toolkit hyphen wrap <TEXT> -w <WIDTH> [-l N] [-r N] [-d DELIM]`
  - Output: Text wrapped to target width.
- `tamil-toolkit hyphen export-dic [OPTIONS]`
  - Preserves existing options (`-o`, `-l`, `-r`, `--verify`).
- `tamil-toolkit hyphen package-oxt [OPTIONS]`
  - Preserves existing options (`-i`, `-o`, `-v`).
- `tamil-toolkit hyphen process-docx [OPTIONS]`
  - Preserves existing options (`-i`, `-o`, `--inplace`, `-l`, `-r`, `-v`).
