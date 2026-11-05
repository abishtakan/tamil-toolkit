# Phase 1: Data Model (`tamil-hyphen`)

**Feature**: `009-tamil-hyphen`  
**Date**: 2026-11-05  
**Status**: Completed  

## 1. Entities & Data Structures

### `HyphenationConfig`
Encapsulates runtime parameters controlling hyphenation and wrapping behavior.

| Field | Type | Default | Validation / Constraints | Description |
| :--- | :--- | :--- | :--- | :--- |
| `delimiter` | `String` | `"\u{00AD}"` (soft hyphen) | Non-empty string | String inserted at valid syllable break points (e.g. `"-"` for wrapping, `"\u{00AD}"` for paragraph text). |
| `left_min` | `usize` | `2` | `>= 1` | Minimum number of tailored Tamil letters (*Ezhuthu*) required before the first break in a word. |
| `right_min` | `usize` | `2` | `>= 1` | Minimum number of tailored Tamil letters (*Ezhuthu*) required after the last break in a word. |

---

### `HyphenationPoint`
Represents an exact break opportunity identified within an NFC-normalized Tamil word.

| Field | Type | Description |
| :--- | :--- | :--- |
| `letter_index` | `usize` | Zero-based tailored letter (*Ezhuthu*) index where break occurs (break is after letter `index`). |
| `scalar_offset` | `usize` | Zero-based Unicode scalar (code point) offset in the normalized string. |
| `byte_offset` | `usize` | Zero-based UTF-8 byte offset in the normalized string. |

---

### `HyphenationResult`
The output of hyphenating a single Tamil word.

| Field | Type | Description | Invariant |
| :--- | :--- | :--- | :--- |
| `original` | `String` | Input word normalized to NFC. | `original == segments.join("")` |
| `hyphenated` | `String` | Word with `delimiter` inserted at each valid break point. | `hyphenated == segments.join(&delimiter)` |
| `segments` | `Vec<String>` | Ordered unbroken syllable segments. | Each segment contains at least one letter; no segment starts with a *Mei* or *Aytham*. |
| `points` | `Vec<HyphenationPoint>` | Metadata for each break point. | `points.len() == segments.len() - 1` (when `segments.len() >= 1`) |

---

### `WrapResult`
The output of wrapping a paragraph of text to a maximum line width.

| Field | Type | Description |
| :--- | :--- | :--- |
| `lines` | `Vec<String>` | Ordered list of wrapped line strings. |
| `broken_words_count` | `usize` | Count of Tamil words that were split across line boundaries using hyphenation. |

---

## 2. Syllable State Machine (`Akshara` Model)

During word scanning, each tailored letter (*Ezhuthu*) is categorized using the core tables:

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LetterClass {
    Uyir,          // Independent vowel (அ, ஆ...)
    Uyirmei,       // Consonant + Vowel composite (க, கா, கி, கை...)
    Mei,           // Pure consonant with pulli (க், த், ம்...)
    Aytham,        // Aytham letter (ஃ)
    AtomicGrantha, // Multi-grapheme atomic conjuncts (க்ஷ, ஸ்ரீ)
    Other,         // Non-Tamil or unclassified
}
```

### Syllable Boundaries & Break Validity:
A boundary between letter at index `i` and letter at index `i + 1` is a **valid syllable break** if and only if:
1. Letter `i + 1` is a valid syllable onset: `Uyirmei`, `Uyir`, or `AtomicGrantha`.
2. Letter `i + 1` is **NOT** a `Mei` (pure consonant) and **NOT** `Aytham`.
3. Letter `i` is either:
   - A `Mei` or `Aytham` that followed a preceding `Uyir` or `Uyirmei` (the end of a syllable coda).
   - A `Uyir`, `Uyirmei`, or `AtomicGrantha` where letter `i + 1` is another `Uyir` or `Uyirmei` onset (open syllable boundary).
4. **Margin check**: `(i + 1) >= left_min` AND `(total_letters - (i + 1)) >= right_min`.
5. **Nucleus check**: There is at least one vowel-bearing nucleus (*Uyir* or *Uyirmei*) on the left side `0..=i`, AND at least one on the right side `(i+1)..total_letters`.
6. **Joiner check**: Neither letter `i` nor letter `i + 1` is adjacent to a `ZWJ` (`U+200D`) or `ZWNJ` (`U+200C`).
