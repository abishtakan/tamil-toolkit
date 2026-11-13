# Contract: Reused `tamil-core` Primitives for Feature 021

**Crate**: `tamil-core` (`crates/tamil-core/src/lib.rs`, `src/phonology.rs`, `src/olippasai.rs`)  
**Consumed by**: Feature 021 build-time lexicon compiler (`build.rs`), runtime lookup/curation, verification tests

## Verified Primitive Matrix

| Symbol | Input Contract | Output Contract | Verified Edge Behavior |
|--------|----------------|-----------------|------------------------|
| `normalize_nfc(&str)` | Arbitrary `&str` | Owned `String` in NFC | Preserves joiners/BOM/SHY; composes Tamil 2-part vowels |
| `normalize_nfd(&str)` | Arbitrary `&str` | Owned `String` in NFD | Decomposes Tamil 2-part vowels; preserves joiners |
| `get_letters(&str)` | Arbitrary `&str` (NFC or NFD) | `Vec<String>` of NFC tailored clusters | Normalizes to NFC first; returns `[]` on `""`; keeps `க்ஷ`/`ஸ்ரீ` intact |
| `Letters::new(&str)` | Caller-normalized `&str` | Borrowed iterator `&'a str` (zero allocation) | Does NOT normalize NFD to NFC; caller must normalize beforehand if NFD possible |
| `split_uyirmei(&str)` | Single tailored letter or Uyir (`&str`) | `Result<UyirmeiParts, ToolkitError>` (`mei`, `uyir`) | Handles NFC and canonical NFD two-part vowels (`\u{0B95}\u{0BC6}\u{0BBE}` -> `\u{0B95}\u{0BCD}` + `\u{0B92}`) |
| `compose_uyirmei(&str, &str)` | Mei (`\u{0B95}\u{0BCD}`) + Uyir (`\u{0B92}`) | `Result<String, ToolkitError>` | Produces NFC composed letter (`\u{0B95}\u{0BCA}`); rejects invalid pairs |
| `inspect_tamil_string(&str)` | Arbitrary `&str` | `Inspection` (`nfc`, `nfd`, `is_nfc`, `is_nfd`, `grapheme_count`, `ezhuthu_count`, `letters`) | Never strips `ZWJ`/`ZWNJ`; note `ZWJ`/`ZWNJ` extends a UAX #29 grapheme cluster classifying it `"other"` and decrementing `ezhuthu_count` |
| `classify_quantity(&str)` | Single tailored letter | `LetterQuantity` (`Kuril`, `Nedil`, `Mei`, `Aytham`, `Other`) | Multi-letter words return `Other`; callers iterate `get_letters` / `Letters::new` per letter |
| `baseline_maathirai(&str)` | Single tailored letter | `Maathirai` (`value()` in `f64`) | Multi-letter words return `0.0`; `kuril=1.0`, `nedil=2.0`, `mei/aytham=0.5` |
| `get_cognate(&str)` | Single consonant/mei letter | `Option<&'static str>` | Maps vallinam <-> mellinam (`க` <-> `ங`); returns `None` on multi-letter strings or non-paired letters |
| `are_cognates(&str, &str)` | Two consonant/mei strings | `bool` | Symmetric check for paired vallinam/mellinam |
| `get_olippasai(&str)` | Tamil word/phrase (`&str`) | `Vec<OlippasaiSegment>` | Segments syllables with byte/letter offsets and coda flags |

## Reuse Notes for Feature 021

- Feature 021 build scripts (`build.rs`) and runtime inspection MUST normalize via `normalize_nfc` / `get_letters` before using `Letters::new` or single-letter predicates (`classify_quantity`, `baseline_maathirai`, `get_cognate`).
- When detecting invisible controls (`ZWJ`, `ZWNJ`, `BOM`, `SHY`) with exact scalar positions in lexicon intake auditing, Feature 021 scans `text.char_indices()` directly alongside `inspect_tamil_string` because `inspect_tamil_string` reports per-cluster summaries rather than per-scalar byte offsets.
