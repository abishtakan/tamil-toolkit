# Lexicon v0.2: Rank 2 `tamil-lexicon` Crate, `TMLPACK2` Compact Runtime Format & `LexiconStore`

Status: specification for Rank 2 crate extraction (`crates/tamil-lexicon`) and compact external `.tlpack` v2 runtime packs (`TMLPACK2`). Supersedes neither `docs/specs/lexicon-v0.1.md` nor the `TMLPACK1` audit-provenance contract; both `TMLPACK1` and `TMLPACK2` are supported side-by-side.

## 1. Crate Boundary & Architectural Invariants

- **Crate**: `crates/tamil-lexicon` (`Rank 2`, `Apache-2.0`, `#![forbid(unsafe_code)]`).
- **Allowed internal dependencies**: `tamil-core` (`Rank 0`) and `tamil-norm` (`Rank 1`) only.
- **Forbidden inside `tamil-lexicon`**:
  - No `build.rs` and no `include_bytes!` of `CC-BY-SA-4.0` or unresolved historical datasets.
  - No `csv` crate, no `source_records` raw-CSV exporter, and no network I/O.
  - Published `crates.io`, `PyPI`, and `npm` packages remain strictly slim `Apache-2.0` reader-only packages (`0` embedded third-party/unresolved bytes by default).
- **WASM safety**: All compression/decompression uses pure-Rust `flate2` (`rust_backend` / `miniz_oxide`), zero C FFI, and zero `unsafe`. Native filesystem helpers (`load_pack_file`, `load_pack_dir`) are gated behind the additive `std-fs` feature (`default = ["std-fs"]`).

## 2. Provenance & Rights Tiers

Every `TMLPACK2` pack declares two explicit, non-forgeable classification fields in its verified header metadata:

- **`pack_tier`**:
  - `"verified_open"`: Verified open-licensed datasets (e.g., `en.wiktionary.org` and `ta.wiktionary.org` under `CC-BY-SA-4.0`).
  - `"local_historical"`: Cleaned, deduplicated, categorized packs derived from the owner-supplied 307,243-row historical bundle (`data/sources/tamil-lexicon/`) for local/self-hosted use only.
- **`rights_status`**:
  - `"CC-BY-SA-4.0"` (or other verified SPDX identifier) for `"verified_open"` packs.
  - `"unresolved"` for `"local_historical"` packs.

Consumers MUST NEVER present `"local_historical"` records as `"verified_open"` or fabricate human approval / third-party redistribution licenses. Callers may filter queries by `tier`: `"open"`, `"local"`, or `"all"` (default `"all"` across whatever packs the caller explicitly loaded into their `PackRegistry`).

## 3. Binary Format `TMLPACK2` (`index_format_version = 2`)

Deterministic little-endian binary container validated on load (magic, bounds, section contiguity, and full-file SHA-256 checksum).

### 3.1 Header (`224` bytes, little-endian)

| Offset | Size | Field | Description |
|---:|---:|---|---|
| `0` | 8 | `magic` | ASCII `TMLPACK2` |
| `8` | 4 | `index_format_version` | `2u32` |
| `12` | 4 | `schema_version` | `2u32` |
| `16` | 4 | `flags` | Bit 0: `DEFLATE_BLOCKS (1)`, Bit 1: `HAS_FOLDED_INDEX (2)`, Bit 2: `HAS_RELATIONS (4)` |
| `20` | 4 | `key_count` | Distinct exact NFC FST keys |
| `24` | 4 | `posting_count` | Total `(key -> entry_ord)` postings |
| `28` | 4 | `entry_count` | Total `CompactEntry` records |
| `32` | 4 | `block_count` | Compressed payload block count |
| `36` | 4 | `relation_count` | Total `CompactRelation` records |
| `40` | 4 | `folded_key_count` | Distinct *Mayangoli*-folded FST keys (`0` if flag bit 1 unset) |
| `44` | 4 | `reserved` | Must be `0` |
| `48..192` | `9 * 16` | Section table | Contiguous `(offset: u64, len: u64)` pairs for: `fst`, `ranges`, `postings`, `entry_loc`, `block_index`, `blocks`, `folded_index`, `relations`, `metadata` |
| `192..224` | 32 | `checksum_sha256` | SHA-256 of `bytes[0..192] || bytes[224..]` |

### 3.2 Sections

1. **`fst`**: `fst::Map` mapping sorted UTF-8 NFC exact keys (canonical `headword` plus any `forms` with `role == "variant"`) to key ordinals `0..key_count`.
2. **`ranges`**: `key_count * 8` bytes of `(start: u32, count: u32)` into `postings`.
3. **`postings`**: `posting_count * 4` bytes of strictly increasing `entry_ord: u32` per key.
4. **`entry_loc`**: `entry_count * 12` bytes of `(block_idx: u32, offset_in_block: u32, byte_len: u32)`.
5. **`block_index`**: `block_count * 16` bytes of `(compressed_offset: u64, compressed_len: u32, raw_len: u32)`.
6. **`blocks`**: Concatenated deterministic raw-deflate compressed payload blocks (~32 KiB uncompressed target per block, fixed level 6). Point lookup decompresses only the single block containing the requested entry.
7. **`folded_index`** (optional, flag bit 1): Framed `[fst_len: u64, ranges_len: u64, postings_len: u64, fst, ranges, postings]` indexed by `tamil_norm::fold_for_search(key, FoldingProfile::Mayangoli)`.
8. **`relations`** (optional, flag bit 2): Framed `[fst_len: u64, ranges_len: u64, block_index_len: u64, blocks_len: u64, fst, ranges, block_index, blocks]` mapping NFC `source_headword` to compressed `CompactRelation` slices.
9. **`metadata`**: Compact UTF-8 JSON `CompactPackMeta`.

## 4. `LexiconStore` Trait & `PackRegistry`

`tamil-lexicon` exposes `pub trait LexiconStore` for Rank 3–5 crates (`tamil-morph`, `tamil-dialect`, `tamil-spell`, `pg_tamil`, `tamil-toolkit`):

- `list_packs() -> Vec<CompactPackSummary>`
- `contains_word(word, scope) -> bool` (O(key_len) FST probe, zero block decompression)
- `has_word_with_pos(word, pos, scope) -> bool`
- `lookup_compact(word, scope) -> Result<CompactLookupResult, String>` (exact NFC, or *Mayangoli* folded when `scope.folded == true`)
- `prefix_search(prefix, options) -> Result<PrefixSearchResult, String>` (FST prefix scan with optional `folded`, `pos`, `domain`, `region`, `register`, `tier`, `packs`, and `limit` in `1..=200`)
- `lookup_relations(word, scope) -> Result<RelationsResult, String>`

`PackRegistry` implements `LexiconStore` over any combination of dynamically mounted `TMLPACK1` and `TMLPACK2` packs loaded from bytes (`load_pack_bytes`), files (`load_pack_file`), or directories (`load_pack_dir`).

## 5. Exact Normalization & Error Rules

- Exact lookup applies canonical NFC (`tamil_norm::normalize_nfc`) only. Whitespace, case, punctuation, ZWJ (`U+200D`), ZWNJ (`U+200C`), and soft hyphen (`U+00AD`) are preserved verbatim.
- Folded lookup (`folded: true`) is strictly opt-in and uses `tamil_norm::fold_for_search(..., FoldingProfile::Mayangoli)`.
- Maximum input length is `65,536` UTF-8 bytes; inputs exceeding the bound fail closed rather than truncating.
- Corrupt magic, bad checksum, truncated sections, invalid UTF-8, or oversized decompressed blocks fail closed on load/read.

## 6. Intuitive Ergonomics: Profiles, Categories, Unified `define`, and Auto-Discovery

To make both local CLI/SDK development and browser Playground UX intuitive without hiding licensing tiers:

1. **Named Loading Profiles (`LexiconProfile`)**:
   - `"open-lite"`: Lightweight verified open bundle (`core`, `names_taxa`, `regional`; ~2.9 MB, `CC-BY-SA-4.0`).
   - `"open"`: Full verified open bundle (`open-lite` + `ta_wiktionary`; ~15.3 MB, 90k+ headwords, `CC-BY-SA-4.0`).
   - `"local"`: Only local/self-hosted historical archive packs (~30.2 MB, `unresolved`).
   - `"full"` (default): Complete combined bundle (`open` + `local`; ~45.6 MB, 241k+ unique headwords + 19.8k relations).
2. **Conceptual Categories (`LexiconCategory`)**:
   - Every pack maps deterministically via `pack_category(pack_id)` to one of 7 logical categories:
     - `dictionary` (`core`, `ta_wiktionary`, `local_core`)
     - `terminology` (`terminology`, `local_terminology`)
     - `phrases` (`local_phrases`)
     - `regional` (`regional`, `local_dialect`)
     - `names_taxa` (`names_taxa`, `local_names_taxa`)
     - `heritage` (`local_literary`, `local_loans`)
     - `relations` (`local_relations`)
   - `QueryScope.category` filters lookups, prefix searches, and unified definitions by category across both open and local tracks.
3. **Unified `WordDefinition` (`LexiconStore::define` / `op = "lexicon_define"`)**:
   - Merges raw `CompactEntry` matches across all mounted packs into one deduplicated, provenance-preserving word view containing `pos`, `meanings_en`, `meanings_ta`, `examples`, `variants`, `domains`, `regions`, `registers`, `standard_equivalents`, `pure_tamil_equivalents`, `origin_languages`, `scientific_names`, `literary_sources`, grouped `relations` (`synonyms`, `antonyms`, `related`, `hypernyms`), explicit `has_verified_open` / `has_local_historical` flags, and per-pack `sources`.
   - Every `WordMeaning` and `WordSourceRef` preserves its owning `pack_id`, `category`, `pack_tier`, and `rights_status`.
4. **Zero-Config Pack Auto-Discovery (`auto_discover_pack_dir` / `op = "lexicon_init"`)**:
   - Searches in deterministic order: `TAMIL_LEXICON_DIR` → `./dist/lexicon-packs` & `./lexicon-packs` (walking up to 3 parent directories) → `~/.tamil-toolkit/lexicon-packs`.
   - `tamil-toolkit lexicon doctor` reports discovered directory, available profiles, categories, counts, and setup hints.
