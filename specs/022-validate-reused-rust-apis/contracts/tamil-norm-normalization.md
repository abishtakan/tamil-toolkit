# Contract: `tamil-norm` Canonical Normalization & NFD-Resilient Pipelines

**Crate**: `tamil-norm` (`crates/tamil-norm/src/lib.rs`)  
**Scope**: `normalize_nfc`, `normalize_nfd`, `fold_for_search`, `repair_tamil_text`, CLI `norm` subcommands

## 1. Canonical Normalization (`normalize_nfc`, `normalize_nfd`)

### Signatures
- `pub use tamil_core::{normalize_nfc, normalize_nfd};`
- `pub fn normalize_nfc(text: &str) -> String`
- `pub fn normalize_nfd(text: &str) -> String`
- Dispatcher ops: `"normalize_nfc"`, `"normalize_nfd"` (JSON string input -> JSON string output)

### Verified Guarantees
1. **Two-Part Tamil Vowels (UAX #15 / UCD 17.0.0)**:
   - `\u{0BC6}\u{0BBE}` <-> `\u{0BCA}` (ko-series)
   - `\u{0BC7}\u{0BBE}` <-> `\u{0BCB}` (koo-series)
   - `\u{0BC6}\u{0BD7}` <-> `\u{0BCC}` (kau-series)
   - `\u{0B92}\u{0BD7}` <-> `\u{0B94}` (`\u{0B94}` `au`)
2. **Canonical Combining Class (CCC) Reordering**:
   - Combining sequences with differing non-zero CCC values reorder strictly ascending in both NFC and NFD (e.g., `\u{0B95}\u{0301}\u{0BCD}` CCC `[0, 230, 9]` -> `\u{0B95}\u{0BCD}\u{0301}` `[0, 9, 230]`).
3. **Format Controls & Joiner Preservation**:
   - `ZWNJ` (`\u{200C}`), `ZWJ` (`\u{200D}`), `BOM` (`\u{FEFF}`), `SHY` (`\u{00AD}`) are preserved verbatim in place.
   - Canonical composition does NOT bridge across a `CCC=0` barrier scalar (e.g., `\u{0B95}\u{0BC6}\u{200D}\u{0BBE}` remains uncomposed in both NFC and NFD).
4. **No Lossy Folding & No Silent Repair**:
   - `\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}` (`ஸ்ரீ`) and `\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}` (`ஶ்ரீ`) remain distinct in both NFC and NFD.
   - Repeated/malformed vowel signs (e.g., `\u{0BA4}\u{0BC1}\u{0BBE}`) remain unmodified.
5. **Idempotence & Mixed-Script Invariance**:
   - For all valid UTF-8 strings `s`: `nfc(nfc(s)) == nfc(s)`, `nfd(nfd(s)) == nfd(s)`, `nfc(nfd(s)) == nfc(s)`, `nfd(nfc(s)) == nfd(s)`.
   - ASCII, Latin, digits, punctuation, and empty string `""` round-trip unchanged unless containing non-Tamil combining marks.

## 2. Downstream `tamil-norm` NFD Consistency

- **`fold_for_search(text: &str, profile: FoldingProfile) -> String`**:
  - Given canonically equivalent NFC and NFD strings `s_nfc` and `s_nfd` across all profiles (`Mayangoli`, `Grantha`, `Comprehensive`), `fold_for_search(s_nfc, p) == fold_for_search(s_nfd, p)`.
  - Preserves joiners unless explicitly documented; folds Shri variants, `க்ஷ` + split vowels, Grantha consonants, and mayangoli classes consistently regardless of input normalization form.
- **`repair_tamil_text(text: &str, options: RepairOptions) -> RepairResult`**:
  - Given canonically equivalent NFC and NFD Tamil inputs, returns identical normalized/repaired `text` and equivalent repair counts (`visual_kombu_count`, `duplicate_pulli_count`, `stripped_control_count`, `total_repairs`).
  - With default options (`strip_format_controls: false`), `ZWJ`/`ZWNJ` are preserved (`stripped_control_count == 0`).

## 3. CLI Contract (`tamil-toolkit norm`)

- `tamil-toolkit norm nfc <TEXT>` -> NFC string stdout, exit `0`.
- `tamil-toolkit norm nfd <TEXT>` -> NFD string stdout, exit `0`.
- `tamil-toolkit norm fold [--profile <mayangoli|grantha|comprehensive>] <TEXT>` (either before or after `<TEXT>`):
  - Valid profiles exit `0` with folded stdout.
  - Unknown `--profile <name>` MUST fail loudly on stderr with non-zero exit code (no silent fallback to `comprehensive`).
