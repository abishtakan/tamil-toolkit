//! Compact block-compressed `.tlpack` v2 (`TMLPACK2`) binary format: builder and safe reader.
//!
//! Designed for 100k–300k+ word Tamil lexicons across native Rust, Python, Dart, and WASM:
//! - Deterministic little-endian header (`224` bytes) with full-file SHA-256 verification.
//! - `fst` 0.4.7 exact NFC FST (headwords + `variant` forms) for O(key_len) exact & prefix search.
//! - Optional *Mayangoli*-folded FST (`tamil_norm::fold_for_search(..., FoldingProfile::Mayangoli)`).
//! - Pure-Rust raw-deflate 32 KiB compressed entry blocks (`flate2` / `miniz_oxide`, zero `unsafe`,
//!   WASM-safe), so point lookups decompress only a single block.
//! - Optional indexed relations section (`SYNONYM`, `ANTONYM`, `RELATED`, `HYPERNYM`).

use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::io::{Read, Write};
use std::sync::{Arc, OnceLock, RwLock};

use flate2::read::DeflateDecoder;
use flate2::write::DeflateEncoder;
use flate2::Compression;
use fst::{Automaton, IntoStreamer, Map, MapBuilder, Streamer};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tamil_norm::{fold_for_search, normalize_nfc, FoldingProfile};

use crate::v1::{read_u32_le, read_u64_le};

/// Magic header identifying the compact binary lexicon pack format v2.
pub const PACK_MAGIC_V2: [u8; 8] = *b"TMLPACK2";

/// Fixed byte length of the `TMLPACK2` binary header in little-endian layout.
pub const HEADER_SIZE_V2: usize = 224;

/// Byte offset of the 32-byte SHA-256 content checksum in the `TMLPACK2` header.
pub const CHECKSUM_OFFSET_V2: usize = 192;

/// Compiled binary index format version for `TMLPACK2`.
pub const INDEX_FORMAT_VERSION_V2: u32 = 2;

/// Schema version for `TMLPACK2` compact entries and manifests.
pub const SCHEMA_VERSION_V2: u32 = 2;

/// Header flag indicating raw-deflate compressed payload blocks.
pub const V2_FLAG_DEFLATE_BLOCKS: u32 = 1 << 0;

/// Header flag indicating presence of a *Mayangoli*-folded FST index.
pub const V2_FLAG_HAS_FOLDED_INDEX: u32 = 1 << 1;

/// Header flag indicating presence of a headword-indexed relations section.
pub const V2_FLAG_HAS_RELATIONS: u32 = 1 << 2;

/// Header flag indicating presence of a reverse English gloss/definition FST index.
pub const V2_FLAG_HAS_ENGLISH_INDEX: u32 = 1 << 3;

const ENGLISH_STOPWORDS: &[&str] = &[
    "a", "an", "the", "of", "to", "in", "on", "or", "is", "be", "by", "at", "as", "for", "and",
    "with", "from", "into", "that", "this", "it", "its", "are", "was", "were", "not", "one", "who",
    "which",
];

/// Splits a `,` or `;` delimited facet field (`domain`, `region`, `register`) into trimmed,
/// non-empty atomic tokens.
pub fn split_facet_tokens(raw: &str) -> Vec<String> {
    raw.split([',', ';'])
        .map(str::trim)
        .filter(|s| !s.is_empty())
        .map(str::to_owned)
        .collect()
}

/// Deterministic English gloss/definition tokenizer for the reverse English-to-Tamil FST index.
///
/// Extracts unique lowercase ASCII `[a-z0-9]` tokens of length >= 2 (capped at 64 chars),
/// skipping tiny English stopwords.
pub fn extract_english_tokens(text: &str) -> Vec<String> {
    extract_english_tokens_inner(text, 2, true)
}

fn extract_english_words_fallback(text: &str) -> Vec<String> {
    extract_english_tokens_inner(text, 1, false)
}

fn extract_english_tokens_inner(text: &str, min_len: usize, filter_stopwords: bool) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut seen: BTreeSet<String> = BTreeSet::new();
    let mut current = String::new();

    let mut flush = |buf: &mut String| {
        if buf.len() >= min_len {
            if buf.len() > 64 {
                buf.truncate(64);
            }
            let is_stop = filter_stopwords && ENGLISH_STOPWORDS.contains(&buf.as_str());
            if !is_stop && seen.insert(buf.clone()) {
                tokens.push(buf.clone());
            }
        }
        buf.clear();
    };

    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() {
            if current.len() < 64 {
                current.push(ch.to_ascii_lowercase());
            }
        } else if !current.is_empty() {
            flush(&mut current);
        }
    }
    if !current.is_empty() {
        flush(&mut current);
    }
    tokens
}

/// Target uncompressed payload size per compressed block (32 KiB).
const TARGET_BLOCK_RAW_BYTES: usize = 32 * 1024;

/// Hard upper bound on any single decompressed block (8 MiB) to defend against crafted bombs.
const MAX_DECOMPRESSED_BLOCK_BYTES: usize = 8 * 1024 * 1024;

/// Provenance & rights classification tier for a compiled lexicon pack.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PackTier {
    /// Verified open-licensed lexical pack (e.g., `CC-BY-SA-4.0` Wiktionary).
    VerifiedOpen,
    /// Owner-supplied local/self-hosted historical pack with unresolved third-party rights.
    LocalHistorical,
}

impl PackTier {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::VerifiedOpen => "verified_open",
            Self::LocalHistorical => "local_historical",
        }
    }
}

/// Alternate written, romanized, or raw-source form attached to a `CompactEntry`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactForm {
    pub role: String,
    pub text: String,
}

/// Compact sense record inside a `CompactEntry`.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct CompactSense {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub gloss_ta: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub gloss_en: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub definition_ta: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub definition_en: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub examples: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub domain: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub region: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub register: Option<String>,
}

/// Compact lexical entry stored inside `TMLPACK2` blocks.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactEntry {
    pub entry_id: String,
    pub headword: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pos: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub forms: Vec<CompactForm>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub senses: Vec<CompactSense>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub domain: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub region: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub register: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub origin_language: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pure_tamil_equivalent: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub standard_equivalent: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scientific_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub literary_source: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub verb_class: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transitivity: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub root_word: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub etymology_type: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dedr_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sandhi_behavior: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub animacy_gender: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub frequency_tier: Option<String>,
    pub source_id: String,
    pub source_locator: String,
    pub rights_status: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub permalink: Option<String>,
}

impl CompactEntry {
    /// Returns a concise preview gloss (prefers English gloss/def, falls back to Tamil gloss/def).
    pub fn preview_gloss(&self) -> Option<String> {
        for sense in &self.senses {
            if let Some(g) = sense.gloss_en.as_deref().filter(|s| !s.is_empty()) {
                return Some(truncate_chars(g, 96));
            }
            if let Some(d) = sense.definition_en.as_deref().filter(|s| !s.is_empty()) {
                return Some(truncate_chars(d, 96));
            }
            if let Some(g) = sense.gloss_ta.as_deref().filter(|s| !s.is_empty()) {
                return Some(truncate_chars(g, 96));
            }
            if let Some(d) = sense.definition_ta.as_deref().filter(|s| !s.is_empty()) {
                return Some(truncate_chars(d, 96));
            }
        }
        if let Some(eq) = self
            .standard_equivalent
            .as_deref()
            .filter(|s| !s.is_empty())
        {
            return Some(truncate_chars(eq, 96));
        }
        if let Some(eq) = self
            .pure_tamil_equivalent
            .as_deref()
            .filter(|s| !s.is_empty())
        {
            return Some(truncate_chars(eq, 96));
        }
        if let Some(sci) = self.scientific_name.as_deref().filter(|s| !s.is_empty()) {
            return Some(truncate_chars(sci, 96));
        }
        None
    }
}

/// Directed or symmetric lexical relation stored in `TMLPACK2` relation sections.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct CompactRelation {
    pub source_headword: String,
    pub target_headword: String,
    pub relation_code: String,
    pub directionality: String,
    pub source_id: String,
    pub source_locator: String,
}

/// Pack-level metadata serialized as compact JSON in the `TMLPACK2` metadata section.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactPackMeta {
    pub schema_version: u32,
    pub index_format_version: u32,
    pub pack_id: String,
    pub pack_tier: PackTier,
    pub rights_status: String,
    pub license: String,
    pub dataset_version: String,
    pub description: String,
    pub source_ids: Vec<String>,
    pub attribution_notice: String,
    pub entry_count: u32,
    pub sense_count: u32,
    pub relation_count: u32,
    pub distinct_headwords: u32,
    #[serde(default)]
    pub pos_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub domain_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub region_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub register_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub domains: Vec<String>,
    #[serde(default)]
    pub regions: Vec<String>,
    #[serde(default)]
    pub registers: Vec<String>,
    #[serde(default)]
    pub en_key_count: u32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub en_index_offset: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub en_index_len: Option<u64>,
}

/// Input payload passed to [`build_compact_pack`] to deterministically compile a `TMLPACK2` image.
#[derive(Debug, Clone)]
pub struct CompactPackInput {
    pub pack_id: String,
    pub pack_tier: PackTier,
    pub rights_status: String,
    pub license: String,
    pub dataset_version: String,
    pub description: String,
    pub source_ids: Vec<String>,
    pub attribution_notice: String,
    pub entries: Vec<CompactEntry>,
    pub relations: Vec<CompactRelation>,
    pub build_folded_index: bool,
}

/// Fixed-width little-endian binary header of a `TMLPACK2` file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompactPackHeader {
    pub index_format_version: u32,
    pub schema_version: u32,
    pub flags: u32,
    pub key_count: u32,
    pub posting_count: u32,
    pub entry_count: u32,
    pub block_count: u32,
    pub relation_count: u32,
    pub folded_key_count: u32,
    pub fst_offset: u64,
    pub fst_len: u64,
    pub ranges_offset: u64,
    pub ranges_len: u64,
    pub postings_offset: u64,
    pub postings_len: u64,
    pub entry_loc_offset: u64,
    pub entry_loc_len: u64,
    pub block_index_offset: u64,
    pub block_index_len: u64,
    pub blocks_offset: u64,
    pub blocks_len: u64,
    pub folded_offset: u64,
    pub folded_len: u64,
    pub relations_offset: u64,
    pub relations_len: u64,
    pub metadata_offset: u64,
    pub metadata_len: u64,
    pub checksum_sha256: [u8; 32],
}

#[derive(Debug, Clone, Copy)]
struct EntryLoc {
    block_idx: u32,
    offset_in_block: u32,
    byte_len: u32,
}

#[derive(Debug, Clone, Copy)]
struct BlockIndexEntry {
    compressed_offset: u64,
    compressed_len: u32,
    raw_len: u32,
}

/// Deterministically compiles a [`CompactPackInput`] into a verified `TMLPACK2` byte vector.
pub fn build_compact_pack(input: &CompactPackInput) -> Result<Vec<u8>, String> {
    if input.pack_id.trim().is_empty() {
        return Err("pack v2 build: pack_id cannot be empty".to_owned());
    }
    if input.entries.is_empty() && input.relations.is_empty() {
        return Err("pack v2 build: pack must contain at least one entry or relation".to_owned());
    }

    // 1. Canonicalize & deterministically sort entries by (entry_id) for stable entry ordinals.
    let mut entries = input.entries.clone();
    for entry in &mut entries {
        entry.headword = normalize_nfc(&entry.headword);
        if entry.headword.is_empty() {
            return Err(format!(
                "pack v2 build: entry '{}' has empty headword",
                entry.entry_id
            ));
        }
        for form in &mut entry.forms {
            form.text = normalize_nfc(&form.text);
        }
    }
    entries.sort_by(|a, b| a.entry_id.cmp(&b.entry_id));
    for win in entries.windows(2) {
        if win[0].entry_id == win[1].entry_id {
            return Err(format!(
                "pack v2 build: duplicate entry_id '{}'",
                win[0].entry_id
            ));
        }
    }

    // 2. Collect metadata stats and exact / folded / English key -> entry_ord posting lists.
    let mut exact_postings: BTreeMap<String, BTreeSet<u32>> = BTreeMap::new();
    let mut folded_postings: BTreeMap<String, BTreeSet<u32>> = BTreeMap::new();
    let mut en_postings: BTreeMap<String, BTreeSet<u32>> = BTreeMap::new();
    let mut headwords_set: BTreeSet<String> = BTreeSet::new();
    let mut pos_counts: BTreeMap<String, u32> = BTreeMap::new();
    let mut domain_counts: BTreeMap<String, u32> = BTreeMap::new();
    let mut region_counts: BTreeMap<String, u32> = BTreeMap::new();
    let mut register_counts: BTreeMap<String, u32> = BTreeMap::new();
    let mut domains: BTreeSet<String> = BTreeSet::new();
    let mut regions: BTreeSet<String> = BTreeSet::new();
    let mut registers: BTreeSet<String> = BTreeSet::new();
    let mut source_ids: BTreeSet<String> = input.source_ids.iter().cloned().collect();
    let mut sense_count: u32 = 0;

    for (idx, entry) in entries.iter().enumerate() {
        let ord = u32::try_from(idx).map_err(|_| "pack v2 build: entry_count exceeds u32")?;
        headwords_set.insert(entry.headword.clone());
        exact_postings
            .entry(entry.headword.clone())
            .or_default()
            .insert(ord);

        if input.build_folded_index {
            let folded = fold_for_search(&entry.headword, FoldingProfile::Mayangoli);
            if !folded.is_empty() {
                folded_postings.entry(folded).or_default().insert(ord);
            }
        }

        // Index explicit variant forms (e.g., spaceless Sorkuvai variants) so exact lookup finds them.
        for form in &entry.forms {
            if form.role == "variant" && !form.text.is_empty() {
                exact_postings
                    .entry(form.text.clone())
                    .or_default()
                    .insert(ord);
                if input.build_folded_index {
                    let folded = fold_for_search(&form.text, FoldingProfile::Mayangoli);
                    if !folded.is_empty() {
                        folded_postings.entry(folded).or_default().insert(ord);
                    }
                }
            }
        }

        if let Some(pos) = entry.pos.as_deref().filter(|s| !s.is_empty()) {
            *pos_counts.entry(pos.to_owned()).or_insert(0) += 1;
        }
        let mut entry_domains: BTreeSet<String> = BTreeSet::new();
        let mut entry_regions: BTreeSet<String> = BTreeSet::new();
        let mut entry_registers: BTreeSet<String> = BTreeSet::new();
        if let Some(d) = entry.domain.as_deref().filter(|s| !s.is_empty()) {
            entry_domains.extend(split_facet_tokens(d));
        }
        if let Some(r) = entry.region.as_deref().filter(|s| !s.is_empty()) {
            entry_regions.extend(split_facet_tokens(r));
        }
        if let Some(reg) = entry.register.as_deref().filter(|s| !s.is_empty()) {
            entry_registers.extend(split_facet_tokens(reg));
        }
        if !entry.source_id.is_empty() {
            source_ids.insert(entry.source_id.clone());
        }
        if let Some(sci) = entry.scientific_name.as_deref().filter(|s| !s.is_empty()) {
            for tok in extract_english_tokens(sci) {
                en_postings.entry(tok).or_default().insert(ord);
            }
        }
        sense_count = sense_count
            .checked_add(u32::try_from(entry.senses.len()).unwrap_or(u32::MAX))
            .ok_or("pack v2 build: sense_count overflow")?;
        for s in &entry.senses {
            if let Some(d) = s.domain.as_deref().filter(|x| !x.is_empty()) {
                entry_domains.extend(split_facet_tokens(d));
            }
            if let Some(r) = s.region.as_deref().filter(|x| !x.is_empty()) {
                entry_regions.extend(split_facet_tokens(r));
            }
            if let Some(reg) = s.register.as_deref().filter(|x| !x.is_empty()) {
                entry_registers.extend(split_facet_tokens(reg));
            }
            for text in [s.gloss_en.as_deref(), s.definition_en.as_deref()]
                .into_iter()
                .flatten()
                .filter(|x| !x.is_empty())
            {
                for tok in extract_english_tokens(text) {
                    en_postings.entry(tok).or_default().insert(ord);
                }
            }
        }
        for tok in entry_domains {
            domains.insert(tok.clone());
            *domain_counts.entry(tok).or_insert(0) += 1;
        }
        for tok in entry_regions {
            regions.insert(tok.clone());
            *region_counts.entry(tok).or_insert(0) += 1;
        }
        for tok in entry_registers {
            registers.insert(tok.clone());
            *register_counts.entry(tok).or_insert(0) += 1;
        }
    }

    // 3. Build exact FST + ranges + postings.
    let BuiltFstIndex {
        fst_bytes,
        ranges_bytes,
        postings_bytes,
        key_count,
        posting_count,
    } = build_fst_index(&exact_postings)?;

    // 4. Pack entries into deterministic 32 KiB raw-deflate blocks.
    let mut entry_loc_bytes = Vec::with_capacity(entries.len() * 12);
    let mut block_index_bytes = Vec::new();
    let mut blocks_bytes = Vec::new();
    let mut current_block: Vec<u8> = Vec::with_capacity(TARGET_BLOCK_RAW_BYTES);
    let mut block_count: u32 = 0;

    let flush_block = |raw: &mut Vec<u8>,
                       block_index: &mut Vec<u8>,
                       blocks: &mut Vec<u8>,
                       count: &mut u32|
     -> Result<(), String> {
        if raw.is_empty() {
            return Ok(());
        }
        let compressed = deflate_bytes(raw)?;
        let comp_offset =
            u64::try_from(blocks.len()).map_err(|_| "pack v2 build: blocks offset overflow")?;
        let comp_len = u32::try_from(compressed.len())
            .map_err(|_| "pack v2 build: compressed block exceeds u32")?;
        let raw_len =
            u32::try_from(raw.len()).map_err(|_| "pack v2 build: raw block exceeds u32")?;
        block_index.extend_from_slice(&comp_offset.to_le_bytes());
        block_index.extend_from_slice(&comp_len.to_le_bytes());
        block_index.extend_from_slice(&raw_len.to_le_bytes());
        blocks.extend_from_slice(&compressed);
        *count = count
            .checked_add(1)
            .ok_or("pack v2 build: block_count overflow")?;
        raw.clear();
        Ok(())
    };

    for entry in &entries {
        let serialized = serde_json::to_vec(entry)
            .map_err(|err| format!("pack v2 build: serialize entry error: {err}"))?;
        if !current_block.is_empty()
            && current_block.len() + serialized.len() > TARGET_BLOCK_RAW_BYTES
        {
            flush_block(
                &mut current_block,
                &mut block_index_bytes,
                &mut blocks_bytes,
                &mut block_count,
            )?;
        }
        let offset_in_block = u32::try_from(current_block.len())
            .map_err(|_| "pack v2 build: entry block offset overflow")?;
        let byte_len =
            u32::try_from(serialized.len()).map_err(|_| "pack v2 build: entry exceeds u32")?;
        current_block.extend_from_slice(&serialized);
        entry_loc_bytes.extend_from_slice(&block_count.to_le_bytes());
        entry_loc_bytes.extend_from_slice(&offset_in_block.to_le_bytes());
        entry_loc_bytes.extend_from_slice(&byte_len.to_le_bytes());
    }
    flush_block(
        &mut current_block,
        &mut block_index_bytes,
        &mut blocks_bytes,
        &mut block_count,
    )?;

    // 5. Build optional folded FST section.
    let mut flags = V2_FLAG_DEFLATE_BLOCKS;
    let (folded_section, folded_key_count) =
        if input.build_folded_index && !folded_postings.is_empty() {
            flags |= V2_FLAG_HAS_FOLDED_INDEX;
            encode_sub_index_section(&folded_postings)?
        } else {
            (Vec::new(), 0u32)
        };

    // 6. Build optional relations section (source_headword -> compressed relation blocks).
    let mut relations = input.relations.clone();
    for rel in &mut relations {
        rel.source_headword = normalize_nfc(&rel.source_headword);
        rel.target_headword = normalize_nfc(&rel.target_headword);
        if !rel.source_id.is_empty() {
            source_ids.insert(rel.source_id.clone());
        }
    }
    relations.sort();
    {
        let mut seen_triples: BTreeSet<(String, String, String)> = BTreeSet::new();
        relations.retain(|rel| {
            rel.source_headword != rel.target_headword
                && seen_triples.insert((
                    rel.source_headword.clone(),
                    rel.target_headword.clone(),
                    rel.relation_code.clone(),
                ))
        });
    }
    let relation_count =
        u32::try_from(relations.len()).map_err(|_| "pack v2 build: relation_count exceeds u32")?;
    let relations_section = if !relations.is_empty() {
        flags |= V2_FLAG_HAS_RELATIONS;
        build_relations_section(&relations)?
    } else {
        Vec::new()
    };

    // 6b. Build optional reverse English gloss/definition FST section.
    let (en_section, en_key_count) = if !en_postings.is_empty() {
        flags |= V2_FLAG_HAS_ENGLISH_INDEX;
        encode_sub_index_section(&en_postings)?
    } else {
        (Vec::new(), 0u32)
    };

    // Compute section offsets before serializing metadata so metadata records exact en_index_offset/len.
    let pre_en_sections: [&[u8]; 8] = [
        &fst_bytes,
        &ranges_bytes,
        &postings_bytes,
        &entry_loc_bytes,
        &block_index_bytes,
        &blocks_bytes,
        &folded_section,
        &relations_section,
    ];
    let mut pre_offsets = [(0u64, 0u64); 8];
    let mut cursor = HEADER_SIZE_V2 as u64;
    for (i, sec) in pre_en_sections.iter().enumerate() {
        let len = sec.len() as u64;
        pre_offsets[i] = (cursor, len);
        cursor = cursor
            .checked_add(len)
            .ok_or("pack v2 build: total file size overflow")?;
    }
    let (en_index_offset, en_index_len) = if !en_section.is_empty() {
        let en_off = cursor;
        let en_len = en_section.len() as u64;
        cursor = cursor
            .checked_add(en_len)
            .ok_or("pack v2 build: total file size overflow")?;
        (Some(en_off), Some(en_len))
    } else {
        (None, None)
    };

    // 7. Build metadata JSON section.
    let meta = CompactPackMeta {
        schema_version: SCHEMA_VERSION_V2,
        index_format_version: INDEX_FORMAT_VERSION_V2,
        pack_id: input.pack_id.clone(),
        pack_tier: input.pack_tier,
        rights_status: input.rights_status.clone(),
        license: input.license.clone(),
        dataset_version: input.dataset_version.clone(),
        description: input.description.clone(),
        source_ids: source_ids.into_iter().collect(),
        attribution_notice: input.attribution_notice.clone(),
        entry_count: u32::try_from(entries.len()).unwrap_or(u32::MAX),
        sense_count,
        relation_count,
        distinct_headwords: u32::try_from(headwords_set.len()).unwrap_or(u32::MAX),
        pos_counts,
        domain_counts,
        region_counts,
        register_counts,
        domains: domains.into_iter().collect(),
        regions: regions.into_iter().collect(),
        registers: registers.into_iter().collect(),
        en_key_count,
        en_index_offset,
        en_index_len,
    };
    let meta_bytes = serde_json::to_vec(&meta)
        .map_err(|err| format!("pack v2 build: serialize metadata error: {err}"))?;

    // 8. Assemble contiguous header (9-slot table; en_section sits between relations and metadata) + SHA-256.
    let mut offsets = [(0u64, 0u64); 9];
    offsets[..8].copy_from_slice(&pre_offsets);
    offsets[8] = (cursor, meta_bytes.len() as u64);
    cursor = cursor
        .checked_add(meta_bytes.len() as u64)
        .ok_or("pack v2 build: total file size overflow")?;

    let total_len = usize::try_from(cursor).map_err(|_| "pack v2 build: file exceeds usize")?;
    let mut out = Vec::with_capacity(total_len);
    out.extend_from_slice(&PACK_MAGIC_V2);
    out.extend_from_slice(&INDEX_FORMAT_VERSION_V2.to_le_bytes());
    out.extend_from_slice(&SCHEMA_VERSION_V2.to_le_bytes());
    out.extend_from_slice(&flags.to_le_bytes());
    out.extend_from_slice(&key_count.to_le_bytes());
    out.extend_from_slice(&posting_count.to_le_bytes());
    out.extend_from_slice(&(entries.len() as u32).to_le_bytes());
    out.extend_from_slice(&block_count.to_le_bytes());
    out.extend_from_slice(&relation_count.to_le_bytes());
    out.extend_from_slice(&folded_key_count.to_le_bytes());
    out.extend_from_slice(&0u32.to_le_bytes()); // reserved
    for (off, len) in offsets {
        out.extend_from_slice(&off.to_le_bytes());
        out.extend_from_slice(&len.to_le_bytes());
    }
    debug_assert_eq!(out.len(), CHECKSUM_OFFSET_V2);
    out.extend_from_slice(&[0u8; 32]); // checksum placeholder
    debug_assert_eq!(out.len(), HEADER_SIZE_V2);

    for sec in pre_en_sections {
        out.extend_from_slice(sec);
    }
    out.extend_from_slice(&en_section);
    out.extend_from_slice(&meta_bytes);

    let mut hasher = Sha256::new();
    hasher.update(&out[..CHECKSUM_OFFSET_V2]);
    hasher.update(&out[HEADER_SIZE_V2..]);
    let digest: [u8; 32] = hasher.finalize().into();
    out[CHECKSUM_OFFSET_V2..HEADER_SIZE_V2].copy_from_slice(&digest);

    Ok(out)
}

struct BuiltFstIndex {
    fst_bytes: Vec<u8>,
    ranges_bytes: Vec<u8>,
    postings_bytes: Vec<u8>,
    key_count: u32,
    posting_count: u32,
}

struct SubIndexSections<'a> {
    fst: &'a [u8],
    ranges: &'a [u8],
    postings: &'a [u8],
}

fn encode_sub_index_section(
    postings_map: &BTreeMap<String, BTreeSet<u32>>,
) -> Result<(Vec<u8>, u32), String> {
    let BuiltFstIndex {
        fst_bytes,
        ranges_bytes,
        postings_bytes,
        key_count,
        ..
    } = build_fst_index(postings_map)?;
    let mut sec =
        Vec::with_capacity(24 + fst_bytes.len() + ranges_bytes.len() + postings_bytes.len());
    sec.extend_from_slice(&(fst_bytes.len() as u64).to_le_bytes());
    sec.extend_from_slice(&(ranges_bytes.len() as u64).to_le_bytes());
    sec.extend_from_slice(&(postings_bytes.len() as u64).to_le_bytes());
    sec.extend_from_slice(&fst_bytes);
    sec.extend_from_slice(&ranges_bytes);
    sec.extend_from_slice(&postings_bytes);
    Ok((sec, key_count))
}

struct RelationSections<'a> {
    fst: &'a [u8],
    loc_table: &'a [u8],
    block_index: &'a [u8],
    blocks: &'a [u8],
}

fn build_fst_index(
    postings_map: &BTreeMap<String, BTreeSet<u32>>,
) -> Result<BuiltFstIndex, String> {
    let mut builder = MapBuilder::memory();
    let mut ranges = Vec::with_capacity(postings_map.len() * 8);
    let mut postings = Vec::new();
    let mut posting_cursor: u32 = 0;

    for (ord, (key, ids)) in postings_map.iter().enumerate() {
        builder
            .insert(key.as_bytes(), ord as u64)
            .map_err(|err| format!("pack v2 build: fst insert error: {err}"))?;
        let count =
            u32::try_from(ids.len()).map_err(|_| "pack v2 build: posting count overflow")?;
        ranges.extend_from_slice(&posting_cursor.to_le_bytes());
        ranges.extend_from_slice(&count.to_le_bytes());
        for &entry_ord in ids {
            postings.extend_from_slice(&entry_ord.to_le_bytes());
        }
        posting_cursor = posting_cursor
            .checked_add(count)
            .ok_or("pack v2 build: posting cursor overflow")?;
    }

    let fst_bytes = builder
        .into_inner()
        .map_err(|err| format!("pack v2 build: fst finalize error: {err}"))?;
    let key_count =
        u32::try_from(postings_map.len()).map_err(|_| "pack v2 build: key_count overflow")?;
    Ok(BuiltFstIndex {
        fst_bytes,
        ranges_bytes: ranges,
        postings_bytes: postings,
        key_count,
        posting_count: posting_cursor,
    })
}

fn build_relations_section(relations: &[CompactRelation]) -> Result<Vec<u8>, String> {
    let mut grouped: BTreeMap<&str, Vec<&CompactRelation>> = BTreeMap::new();
    for rel in relations {
        grouped
            .entry(rel.source_headword.as_str())
            .or_default()
            .push(rel);
    }

    let mut builder = MapBuilder::memory();
    let mut loc_table = Vec::with_capacity(grouped.len() * 12);
    let mut block_index = Vec::new();
    let mut blocks = Vec::new();
    let mut current_block: Vec<u8> = Vec::with_capacity(TARGET_BLOCK_RAW_BYTES);
    let mut block_count: u32 = 0;

    let flush = |raw: &mut Vec<u8>,
                 bidx: &mut Vec<u8>,
                 blks: &mut Vec<u8>,
                 cnt: &mut u32|
     -> Result<(), String> {
        if raw.is_empty() {
            return Ok(());
        }
        let comp = deflate_bytes(raw)?;
        bidx.extend_from_slice(&(blks.len() as u64).to_le_bytes());
        bidx.extend_from_slice(&(comp.len() as u32).to_le_bytes());
        bidx.extend_from_slice(&(raw.len() as u32).to_le_bytes());
        blks.extend_from_slice(&comp);
        *cnt += 1;
        raw.clear();
        Ok(())
    };

    for (ord, (key, list)) in grouped.iter().enumerate() {
        builder
            .insert(key.as_bytes(), ord as u64)
            .map_err(|err| format!("pack v2 build: relation fst error: {err}"))?;
        let serialized = serde_json::to_vec(list)
            .map_err(|err| format!("pack v2 build: relation serialize error: {err}"))?;
        if !current_block.is_empty()
            && current_block.len() + serialized.len() > TARGET_BLOCK_RAW_BYTES
        {
            flush(
                &mut current_block,
                &mut block_index,
                &mut blocks,
                &mut block_count,
            )?;
        }
        let offset = current_block.len() as u32;
        let len = serialized.len() as u32;
        current_block.extend_from_slice(&serialized);
        loc_table.extend_from_slice(&block_count.to_le_bytes());
        loc_table.extend_from_slice(&offset.to_le_bytes());
        loc_table.extend_from_slice(&len.to_le_bytes());
    }
    flush(
        &mut current_block,
        &mut block_index,
        &mut blocks,
        &mut block_count,
    )?;

    let fst_bytes = builder
        .into_inner()
        .map_err(|err| format!("pack v2 build: relation fst finalize error: {err}"))?;

    let mut out = Vec::with_capacity(
        32 + fst_bytes.len() + loc_table.len() + block_index.len() + blocks.len(),
    );
    out.extend_from_slice(&(fst_bytes.len() as u64).to_le_bytes());
    out.extend_from_slice(&(loc_table.len() as u64).to_le_bytes());
    out.extend_from_slice(&(block_index.len() as u64).to_le_bytes());
    out.extend_from_slice(&(blocks.len() as u64).to_le_bytes());
    out.extend_from_slice(&fst_bytes);
    out.extend_from_slice(&loc_table);
    out.extend_from_slice(&block_index);
    out.extend_from_slice(&blocks);
    Ok(out)
}

fn deflate_bytes(raw: &[u8]) -> Result<Vec<u8>, String> {
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::new(6));
    encoder
        .write_all(raw)
        .map_err(|err| format!("pack v2 deflate error: {err}"))?;
    encoder
        .finish()
        .map_err(|err| format!("pack v2 deflate finish error: {err}"))
}

fn inflate_bytes(compressed: &[u8], expected_raw_len: u32) -> Result<Vec<u8>, String> {
    let expected =
        usize::try_from(expected_raw_len).map_err(|_| "pack v2 inflate: raw_len exceeds usize")?;
    if expected > MAX_DECOMPRESSED_BLOCK_BYTES {
        return Err(format!(
            "pack v2 inflate: block raw_len {expected} exceeds safety limit {MAX_DECOMPRESSED_BLOCK_BYTES}"
        ));
    }
    let decoder = DeflateDecoder::new(compressed);
    let mut limited = decoder.take((expected as u64).saturating_add(1));
    let mut out = Vec::with_capacity(expected);
    limited
        .read_to_end(&mut out)
        .map_err(|err| format!("pack v2 inflate error: {err}"))?;
    if out.len() != expected {
        return Err(format!(
            "pack v2 inflate: decoded {} bytes, expected {expected}",
            out.len()
        ));
    }
    Ok(out)
}

/// Maximum number of decompressed 32 KiB payload blocks cached per `CompactPackView` (~1 MiB).
const BLOCK_CACHE_CAPACITY: usize = 32;

/// First Tamil independent vowel (`அ`, `U+0B85`), used as default browse start on empty prefix.
const TAMIL_LETTER_START: &str = "\u{0B85}";

type BlockCache = Arc<RwLock<VecDeque<(u32, Arc<[u8]>)>>>;

/// Key-to-entries pairs returned by an FST prefix scan.
pub type PrefixEntryMatches = Vec<(String, Vec<CompactEntry>)>;

/// Paginated FST prefix scan output: `(matched_rows, has_more)`.
pub type PrefixPageResult = (PrefixEntryMatches, bool);

/// Safe, `Send + Sync + Clone` view over an in-memory `TMLPACK2` binary image.
#[derive(Debug, Clone)]
pub struct CompactPackView {
    bytes: Arc<[u8]>,
    header: CompactPackHeader,
    meta_cache: Arc<OnceLock<CompactPackMeta>>,
    block_cache: BlockCache,
}

impl CompactPackView {
    /// Parses and cryptographically/structurally validates a `TMLPACK2` binary image.
    pub fn parse(bytes: impl Into<Arc<[u8]>>) -> Result<Self, String> {
        let bytes: Arc<[u8]> = bytes.into();
        if bytes.len() < HEADER_SIZE_V2 {
            return Err(format!(
                "pack v2: length {} is smaller than header size {}",
                bytes.len(),
                HEADER_SIZE_V2
            ));
        }
        if bytes.get(0..8) != Some(&PACK_MAGIC_V2) {
            return Err("pack v2: invalid magic header".to_owned());
        }
        let index_format_version = read_u32_le(&bytes, 8)?;
        if index_format_version != INDEX_FORMAT_VERSION_V2 {
            return Err(format!(
                "pack v2: unsupported index_format_version {index_format_version}"
            ));
        }
        let schema_version = read_u32_le(&bytes, 12)?;
        if schema_version != SCHEMA_VERSION_V2 {
            return Err(format!(
                "pack v2: unsupported schema_version {schema_version}"
            ));
        }
        let flags = read_u32_le(&bytes, 16)?;
        let allowed_flags = V2_FLAG_DEFLATE_BLOCKS
            | V2_FLAG_HAS_FOLDED_INDEX
            | V2_FLAG_HAS_RELATIONS
            | V2_FLAG_HAS_ENGLISH_INDEX;
        if flags & !allowed_flags != 0 {
            return Err(format!("pack v2: unsupported flags {flags}"));
        }
        let key_count = read_u32_le(&bytes, 20)?;
        let posting_count = read_u32_le(&bytes, 24)?;
        let entry_count = read_u32_le(&bytes, 28)?;
        let block_count = read_u32_le(&bytes, 32)?;
        let relation_count = read_u32_le(&bytes, 36)?;
        let folded_key_count = read_u32_le(&bytes, 40)?;
        let reserved = read_u32_le(&bytes, 44)?;
        if reserved != 0 {
            return Err(format!("pack v2: non-zero reserved field {reserved}"));
        }

        let mut sec = [(0u64, 0u64); 9];
        for (i, pair) in sec.iter_mut().enumerate() {
            let base = 48 + i * 16;
            *pair = (read_u64_le(&bytes, base)?, read_u64_le(&bytes, base + 8)?);
        }
        let checksum_sha256: [u8; 32] = bytes
            .get(CHECKSUM_OFFSET_V2..HEADER_SIZE_V2)
            .ok_or("pack v2: truncated checksum")?
            .try_into()
            .map_err(|_| "pack v2: invalid checksum width")?;

        let header = CompactPackHeader {
            index_format_version,
            schema_version,
            flags,
            key_count,
            posting_count,
            entry_count,
            block_count,
            relation_count,
            folded_key_count,
            fst_offset: sec[0].0,
            fst_len: sec[0].1,
            ranges_offset: sec[1].0,
            ranges_len: sec[1].1,
            postings_offset: sec[2].0,
            postings_len: sec[2].1,
            entry_loc_offset: sec[3].0,
            entry_loc_len: sec[3].1,
            block_index_offset: sec[4].0,
            block_index_len: sec[4].1,
            blocks_offset: sec[5].0,
            blocks_len: sec[5].1,
            folded_offset: sec[6].0,
            folded_len: sec[6].1,
            relations_offset: sec[7].0,
            relations_len: sec[7].1,
            metadata_offset: sec[8].0,
            metadata_len: sec[8].1,
            checksum_sha256,
        };

        validate_v2_layout(&header, bytes.len())?;

        // Verify full-file SHA-256 checksum.
        let mut hasher = Sha256::new();
        hasher.update(&bytes[..CHECKSUM_OFFSET_V2]);
        hasher.update(&bytes[HEADER_SIZE_V2..]);
        let actual: [u8; 32] = hasher.finalize().into();
        if actual != header.checksum_sha256 {
            return Err("pack v2: checksum_sha256 mismatch".to_owned());
        }

        let view = Self {
            bytes,
            header,
            meta_cache: Arc::new(OnceLock::new()),
            block_cache: Arc::new(RwLock::new(VecDeque::with_capacity(BLOCK_CACHE_CAPACITY))),
        };

        // Validate FSTs and parse metadata immediately so corrupt packs fail on load.
        let map = view.fst_map()?;
        if map.len() != usize::try_from(view.header.key_count).unwrap_or(usize::MAX) {
            return Err(format!(
                "pack v2: fst key_count {} != header {}",
                map.len(),
                view.header.key_count
            ));
        }
        let meta = view.metadata_ref()?;
        if meta.entry_count != view.header.entry_count {
            return Err(format!(
                "pack v2: metadata entry_count {} != header {}",
                meta.entry_count, view.header.entry_count
            ));
        }
        if meta.relation_count != view.header.relation_count {
            return Err(format!(
                "pack v2: metadata relation_count {} != header {}",
                meta.relation_count, view.header.relation_count
            ));
        }
        if view.has_folded_index() {
            let _ = view.folded_sections()?;
        }
        if view.has_relations() {
            let _ = view.relation_sections()?;
        }
        if view.header.flags & V2_FLAG_HAS_ENGLISH_INDEX != 0 {
            let expected_off = view
                .header
                .relations_offset
                .checked_add(view.header.relations_len)
                .ok_or("pack v2: english index offset overflow")?;
            let expected_len = view
                .header
                .metadata_offset
                .checked_sub(expected_off)
                .ok_or("pack v2: english index length underflow")?;
            if meta.en_index_offset != Some(expected_off) || meta.en_index_len != Some(expected_len)
            {
                return Err("pack v2: metadata en_index bounds mismatch".to_owned());
            }
            let en_sec = view.en_sections()?;
            let en_map =
                Map::new(en_sec.fst).map_err(|err| format!("pack v2 english fst error: {err}"))?;
            if en_map.len() != usize::try_from(meta.en_key_count).unwrap_or(usize::MAX) {
                return Err(format!(
                    "pack v2: english fst key_count {} != metadata {}",
                    en_map.len(),
                    meta.en_key_count
                ));
            }
            if en_sec.ranges.len() != en_map.len().saturating_mul(8) {
                return Err("pack v2: english ranges_len mismatch".to_owned());
            }
        } else if meta.en_index_offset.is_some() || meta.en_index_len.is_some() {
            return Err("pack v2: unexpected en_index metadata without flag".to_owned());
        }
        Ok(view)
    }

    /// Returns total serialized byte size of this pack.
    pub fn byte_len(&self) -> usize {
        self.bytes.len()
    }

    /// Returns the hex SHA-256 checksum from the verified header.
    pub fn checksum_hex(&self) -> String {
        self.header
            .checksum_sha256
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect()
    }

    pub fn header(&self) -> &CompactPackHeader {
        &self.header
    }

    pub fn has_folded_index(&self) -> bool {
        self.header.flags & V2_FLAG_HAS_FOLDED_INDEX != 0 && self.header.folded_len > 0
    }

    pub fn has_relations(&self) -> bool {
        self.header.flags & V2_FLAG_HAS_RELATIONS != 0 && self.header.relations_len > 0
    }

    pub fn has_english_index(&self) -> bool {
        self.header.flags & V2_FLAG_HAS_ENGLISH_INDEX != 0
            && self
                .metadata_ref()
                .ok()
                .is_some_and(|m| m.en_index_offset.is_some() && m.en_index_len.is_some())
    }

    pub fn metadata_ref(&self) -> Result<&CompactPackMeta, String> {
        if let Some(cached) = self.meta_cache.get() {
            return Ok(cached);
        }
        let raw = slice_section(
            &self.bytes,
            self.header.metadata_offset,
            self.header.metadata_len,
        )?;
        let parsed: CompactPackMeta =
            serde_json::from_slice(raw).map_err(|err| format!("pack v2 metadata error: {err}"))?;
        let _ = self.meta_cache.set(parsed);
        Ok(self.meta_cache.get().expect("initialized"))
    }

    pub fn fst_map(&self) -> Result<Map<&[u8]>, String> {
        let bytes = slice_section(&self.bytes, self.header.fst_offset, self.header.fst_len)?;
        Map::new(bytes).map_err(|err| format!("pack v2 fst error: {err}"))
    }

    /// O(key_len) existence check with zero block decompression.
    pub fn contains_exact(&self, normalized_key: &str) -> bool {
        if self.header.key_count == 0 {
            return false;
        }
        self.fst_map()
            .ok()
            .and_then(|map| map.get(normalized_key.as_bytes()))
            .is_some()
    }

    /// O(key_len) *Mayangoli*-folded existence check with zero block decompression.
    pub fn contains_folded(&self, folded_key: &str) -> bool {
        if !self.has_folded_index() {
            return false;
        }
        self.folded_sections()
            .ok()
            .and_then(|sec| Map::new(sec.fst).ok())
            .and_then(|map| map.get(folded_key.as_bytes()))
            .is_some()
    }

    /// Looks up all entries matching an exact NFC key (or variant form).
    pub fn lookup_exact(&self, query: &str) -> Result<Vec<CompactEntry>, String> {
        if self.header.key_count == 0 {
            return Ok(Vec::new());
        }
        let key = normalize_nfc(query);
        let map = self.fst_map()?;
        let Some(ord) = map.get(key.as_bytes()) else {
            return Ok(Vec::new());
        };
        let ranges = slice_section(
            &self.bytes,
            self.header.ranges_offset,
            self.header.ranges_len,
        )?;
        let postings = slice_section(
            &self.bytes,
            self.header.postings_offset,
            self.header.postings_len,
        )?;
        let entry_ords = read_postings_for_ord(ranges, postings, ord, self.header.entry_count)?;
        self.decode_entries(&entry_ords)
    }

    /// Looks up all entries matching a *Mayangoli*-folded query.
    pub fn lookup_folded(&self, query: &str) -> Result<Vec<CompactEntry>, String> {
        if !self.has_folded_index() {
            return Ok(Vec::new());
        }
        let folded_key = fold_for_search(query, FoldingProfile::Mayangoli);
        if folded_key.is_empty() {
            return Ok(Vec::new());
        }
        let folded = self.folded_sections()?;
        let map = Map::new(folded.fst).map_err(|err| format!("pack v2 folded fst error: {err}"))?;
        let Some(ord) = map.get(folded_key.as_bytes()) else {
            return Ok(Vec::new());
        };
        let entry_ords =
            read_postings_for_ord(folded.ranges, folded.postings, ord, self.header.entry_count)?;
        self.decode_entries(&entry_ords)
    }

    /// Streams up to `limit` distinct FST keys matching `prefix` (exact NFC or *Mayangoli*-folded),
    /// returning `(matched_key, Vec<CompactEntry>)`.
    pub fn prefix_lookup(
        &self,
        prefix: &str,
        limit: usize,
        folded: bool,
    ) -> Result<Vec<(String, Vec<CompactEntry>)>, String> {
        let (rows, _) = self.prefix_lookup_filtered(
            prefix,
            None,
            limit,
            limit.saturating_mul(2).max(16),
            folded,
            |_| true,
        )?;
        Ok(rows)
    }

    /// Streams up to `limit` matching FST keys with optional cursor pagination (`after_key`),
    /// adaptive scan budget (`max_scan`), and entry-level predicate filtering.
    ///
    /// Special browse conventions when `!folded`:
    /// - Empty `prefix` with `after_key == None` starts at Tamil letter `அ` (`U+0B85`) so
    ///   punctuation/ASCII/Aytham keys do not starve default dictionary browsing.
    /// - `prefix == "#"` browses keys strictly before `U+0B85` (punctuation, ASCII, digits, `ஃ`).
    ///
    /// Returns `(matched_rows, has_more)`.
    pub fn prefix_lookup_filtered<F>(
        &self,
        prefix: &str,
        after_key: Option<&str>,
        limit: usize,
        max_scan: usize,
        folded: bool,
        mut predicate: F,
    ) -> Result<PrefixPageResult, String>
    where
        F: FnMut(&CompactEntry) -> bool,
    {
        if limit == 0 || self.header.entry_count == 0 {
            return Ok((Vec::new(), false));
        }
        if folded {
            if !self.has_folded_index() {
                return Ok((Vec::new(), false));
            }
            let norm_prefix = fold_for_search(prefix, FoldingProfile::Mayangoli);
            let fsec = self.folded_sections()?;
            let map =
                Map::new(fsec.fst).map_err(|err| format!("pack v2 folded fst error: {err}"))?;
            self.stream_prefix_filtered(
                &map,
                fsec.ranges,
                fsec.postings,
                &norm_prefix,
                after_key,
                limit,
                max_scan,
                false,
                &mut predicate,
            )
        } else {
            if self.header.key_count == 0 {
                return Ok((Vec::new(), false));
            }
            let norm_prefix = normalize_nfc(prefix);
            let map = self.fst_map()?;
            let ranges = slice_section(
                &self.bytes,
                self.header.ranges_offset,
                self.header.ranges_len,
            )?;
            let postings = slice_section(
                &self.bytes,
                self.header.postings_offset,
                self.header.postings_len,
            )?;
            let non_tamil_bucket = norm_prefix == "#";
            let effective_prefix = if non_tamil_bucket { "" } else { &norm_prefix };
            self.stream_prefix_filtered(
                &map,
                ranges,
                postings,
                effective_prefix,
                after_key,
                limit,
                max_scan,
                non_tamil_bucket,
                &mut predicate,
            )
        }
    }

    /// Returns all exact FST keys that are char-boundary prefixes of `word`, ordered longest-first.
    /// Zero block decompression — pure O(len) FST probes for morphological stemmers & splitters.
    pub fn longest_prefix_matches(&self, word: &str) -> Result<Vec<String>, String> {
        if self.header.key_count == 0 || word.is_empty() {
            return Ok(Vec::new());
        }
        let nfc = normalize_nfc(word);
        let map = self.fst_map()?;
        let mut boundaries: Vec<usize> = nfc.char_indices().map(|(i, _)| i).skip(1).collect();
        boundaries.push(nfc.len());
        let mut out = Vec::new();
        for &end in boundaries.iter().rev() {
            let candidate = &nfc[..end];
            if map.get(candidate.as_bytes()).is_some() {
                out.push(candidate.to_owned());
            }
        }
        Ok(out)
    }

    /// Bounded Damerau-Levenshtein fuzzy search (`max_distance` in `1..=2`) over exact NFC FST keys.
    /// Zero block decompression during candidate scanning; only decodes final top-`limit` hits.
    pub fn fuzzy_lookup(
        &self,
        word: &str,
        max_distance: u32,
        limit: usize,
    ) -> Result<Vec<(String, u32, Vec<CompactEntry>)>, String> {
        if self.header.key_count == 0 || word.is_empty() || limit == 0 {
            return Ok(Vec::new());
        }
        let max_dist = max_distance.clamp(1, 2) as usize;
        let nfc = normalize_nfc(word);
        let target_chars: Vec<char> = nfc.chars().collect();
        if target_chars.is_empty() {
            return Ok(Vec::new());
        }
        let target_len = target_chars.len();
        let target_folded = fold_for_search(&nfc, FoldingProfile::Mayangoli);

        let map = self.fst_map()?;
        let ranges = slice_section(
            &self.bytes,
            self.header.ranges_offset,
            self.header.ranges_len,
        )?;
        let postings = slice_section(
            &self.bytes,
            self.header.postings_offset,
            self.header.postings_len,
        )?;

        // Collect candidate FST prefixes so we never scan unrelated letters:
        // first scalar, second scalar (deletion of first char), and folded first scalar.
        let mut seed_prefixes: BTreeSet<String> = BTreeSet::new();
        let c0 = target_chars[0];
        seed_prefixes.insert(c0.to_string());
        if target_len >= 2 {
            seed_prefixes.insert(target_chars[1].to_string());
        }
        if let Some(fc0) = target_folded.chars().next() {
            seed_prefixes.insert(fc0.to_string());
        }
        // Common Mayangoli initial confusions (ல/ள/ழ, ந/ன/ண, ர/ற, ச/ஸ).
        for alt in mayangoli_initial_alternatives(c0) {
            seed_prefixes.insert(alt.to_string());
        }

        let mut scored: BTreeMap<String, (u32, u64)> = BTreeMap::new();
        // Fast path: include any folded-index exact matches first (often dist 1-2 across Mayangoli).
        if self.has_folded_index() && !target_folded.is_empty() {
            if let Ok(folded_entries) = self.lookup_folded(&nfc) {
                for entry in folded_entries {
                    let cand_chars: Vec<char> = entry.headword.chars().collect();
                    let d = damerau_levenshtein(&target_chars, &cand_chars, max_dist);
                    if d <= max_dist {
                        if let Some(ord) = map.get(entry.headword.as_bytes()) {
                            scored.entry(entry.headword).or_insert((d as u32, ord));
                        }
                    }
                }
            }
        }

        for pfx in &seed_prefixes {
            let matcher = fst::automaton::Str::new(pfx).starts_with();
            let mut stream = map.search(matcher).into_stream();
            while let Some((key_bytes, ord)) = stream.next() {
                let Ok(key_str) = std::str::from_utf8(key_bytes) else {
                    continue;
                };
                // Quick byte-length bound before char decoding (each Tamil char is 3 UTF-8 bytes).
                let byte_diff = key_str.len().abs_diff(nfc.len());
                if byte_diff > max_dist * 4 + 3 {
                    continue;
                }
                let cand_chars: Vec<char> = key_str.chars().collect();
                if cand_chars.len().abs_diff(target_len) > max_dist {
                    continue;
                }
                let dist = damerau_levenshtein(&target_chars, &cand_chars, max_dist);
                if dist <= max_dist {
                    scored
                        .entry(key_str.to_owned())
                        .and_modify(|(prev_d, _)| {
                            if (dist as u32) < *prev_d {
                                *prev_d = dist as u32;
                            }
                        })
                        .or_insert((dist as u32, ord));
                }
            }
        }

        let mut ranked: Vec<(String, u32, u64)> = scored
            .into_iter()
            .map(|(k, (d, ord))| (k, d, ord))
            .collect();
        ranked.sort_by(|a, b| a.1.cmp(&b.1).then_with(|| a.0.cmp(&b.0)));
        ranked.truncate(limit);

        let mut results = Vec::with_capacity(ranked.len());
        for (key_str, dist, ord) in ranked {
            let entry_ords = read_postings_for_ord(ranges, postings, ord, self.header.entry_count)?;
            let entries = self.decode_entries(&entry_ords)?;
            results.push((key_str, dist, entries));
        }
        Ok(results)
    }

    /// Searches the reverse English gloss/definition FST index for entries matching `query`.
    ///
    /// Returns up to `max_candidates` matching `CompactEntry` records. Single-token queries
    /// prioritize exact token matches followed by prefix matches; multi-token queries intersect
    /// per-token postings and fall back to overlap-ranked union if the intersection is empty.
    pub fn search_english(
        &self,
        query: &str,
        max_candidates: usize,
    ) -> Result<Vec<CompactEntry>, String> {
        if !self.has_english_index() || max_candidates == 0 || query.trim().is_empty() {
            return Ok(Vec::new());
        }
        let mut tokens = extract_english_tokens(query);
        if tokens.is_empty() {
            tokens = extract_english_words_fallback(query);
        }
        if tokens.is_empty() {
            return Ok(Vec::new());
        }

        let en_sec = self.en_sections()?;
        let map =
            Map::new(en_sec.fst).map_err(|err| format!("pack v2 english fst error: {err}"))?;
        let entry_count = self.header.entry_count;

        let selected_ords: Vec<u32> = if tokens.len() == 1 {
            let tok = &tokens[0];
            let mut ords = Vec::new();
            let mut seen: BTreeSet<u32> = BTreeSet::new();
            if let Some(ord) = map.get(tok.as_bytes()) {
                for e_ord in
                    read_postings_for_ord(en_sec.ranges, en_sec.postings, ord, entry_count)?
                {
                    if seen.insert(e_ord) {
                        ords.push(e_ord);
                        if ords.len() >= max_candidates {
                            return self.decode_entries(&ords);
                        }
                    }
                }
            }
            let matcher = fst::automaton::Str::new(tok).starts_with();
            let mut stream = map.search(matcher).into_stream();
            while let Some((key_bytes, ord)) = stream.next() {
                if key_bytes == tok.as_bytes() {
                    continue;
                }
                for e_ord in
                    read_postings_for_ord(en_sec.ranges, en_sec.postings, ord, entry_count)?
                {
                    if seen.insert(e_ord) {
                        ords.push(e_ord);
                        if ords.len() >= max_candidates {
                            return self.decode_entries(&ords);
                        }
                    }
                }
            }
            ords
        } else {
            let per_token_cap = max_candidates.saturating_mul(16).max(1024);
            let mut per_token_sets: Vec<BTreeSet<u32>> = Vec::with_capacity(tokens.len());
            for tok in &tokens {
                let mut set = BTreeSet::new();
                if let Some(ord) = map.get(tok.as_bytes()) {
                    for e_ord in
                        read_postings_for_ord(en_sec.ranges, en_sec.postings, ord, entry_count)?
                    {
                        set.insert(e_ord);
                    }
                }
                if set.len() < per_token_cap {
                    let matcher = fst::automaton::Str::new(tok).starts_with();
                    let mut stream = map.search(matcher).into_stream();
                    while let Some((key_bytes, ord)) = stream.next() {
                        if key_bytes == tok.as_bytes() {
                            continue;
                        }
                        for e_ord in
                            read_postings_for_ord(en_sec.ranges, en_sec.postings, ord, entry_count)?
                        {
                            set.insert(e_ord);
                            if set.len() >= per_token_cap {
                                break;
                            }
                        }
                        if set.len() >= per_token_cap {
                            break;
                        }
                    }
                }
                per_token_sets.push(set);
            }

            let mut intersected = Vec::new();
            if let Some((first, rest)) = per_token_sets.split_first() {
                for &ord in first {
                    if rest.iter().all(|s| s.contains(&ord)) {
                        intersected.push(ord);
                        if intersected.len() >= max_candidates {
                            break;
                        }
                    }
                }
            }
            if !intersected.is_empty() {
                intersected
            } else {
                let mut overlap: BTreeMap<u32, usize> = BTreeMap::new();
                for set in &per_token_sets {
                    for &ord in set {
                        *overlap.entry(ord).or_insert(0) += 1;
                    }
                }
                let mut ranked: Vec<(u32, usize)> = overlap.into_iter().collect();
                ranked.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
                ranked.truncate(max_candidates);
                ranked.into_iter().map(|(ord, _)| ord).collect()
            }
        };

        self.decode_entries(&selected_ords)
    }

    /// Looks up all indexed relations for `source_headword` (NFC-normalized).
    pub fn lookup_relations(&self, headword: &str) -> Result<Vec<CompactRelation>, String> {
        if !self.has_relations() {
            return Ok(Vec::new());
        }
        let key = normalize_nfc(headword);
        let rsec = self.relation_sections()?;
        let map = Map::new(rsec.fst).map_err(|err| format!("pack v2 relation fst error: {err}"))?;
        let Some(ord) = map.get(key.as_bytes()) else {
            return Ok(Vec::new());
        };
        let off = usize::try_from(ord)
            .ok()
            .and_then(|v| v.checked_mul(12))
            .ok_or("pack v2 relation loc overflow")?;
        let block_idx = read_u32_le(rsec.loc_table, off)?;
        let offset_in_block = read_u32_le(rsec.loc_table, off + 4)?;
        let byte_len = read_u32_le(rsec.loc_table, off + 8)?;
        let raw_block = decode_block_from_slices(rsec.block_index, rsec.blocks, block_idx)?;
        let start = offset_in_block as usize;
        let end = start
            .checked_add(byte_len as usize)
            .ok_or("pack v2 relation slice overflow")?;
        let slice = raw_block
            .get(start..end)
            .ok_or("pack v2 relation slice out of bounds")?;
        serde_json::from_slice(slice).map_err(|err| format!("pack v2 relation decode error: {err}"))
    }

    #[allow(clippy::too_many_arguments)]
    fn stream_prefix_filtered<F>(
        &self,
        map: &Map<&[u8]>,
        ranges: &[u8],
        postings: &[u8],
        prefix: &str,
        after_key: Option<&str>,
        limit: usize,
        max_scan: usize,
        non_tamil_bucket: bool,
        predicate: &mut F,
    ) -> Result<PrefixPageResult, String>
    where
        F: FnMut(&CompactEntry) -> bool,
    {
        let mut results = Vec::new();
        let mut scanned = 0usize;
        let mut has_more = false;
        let matcher = fst::automaton::Str::new(prefix).starts_with();
        let mut builder = map.search(matcher);
        if let Some(cursor) = after_key.filter(|s| !s.is_empty()) {
            builder = builder.gt(cursor.as_bytes());
        } else if non_tamil_bucket {
            builder = builder.lt(TAMIL_LETTER_START.as_bytes());
        } else if prefix.is_empty() {
            builder = builder.ge(TAMIL_LETTER_START.as_bytes());
        }
        if non_tamil_bucket && after_key.is_some() {
            builder = builder.lt(TAMIL_LETTER_START.as_bytes());
        }

        let mut stream = builder.into_stream();
        while let Some((key_bytes, ord)) = stream.next() {
            scanned += 1;
            if scanned > max_scan {
                has_more = true;
                break;
            }
            let key_str = std::str::from_utf8(key_bytes)
                .map_err(|err| format!("pack v2 fst utf8 error: {err}"))?
                .to_owned();
            let entry_ords = read_postings_for_ord(ranges, postings, ord, self.header.entry_count)?;
            let decoded = self.decode_entries(&entry_ords)?;
            let matched: Vec<CompactEntry> = decoded.into_iter().filter(&mut *predicate).collect();
            if matched.is_empty() {
                continue;
            }
            if results.len() >= limit {
                has_more = true;
                break;
            }
            results.push((key_str, matched));
        }
        Ok((results, has_more))
    }

    fn get_or_decode_block(
        &self,
        block_index: &[u8],
        blocks: &[u8],
        block_idx: u32,
    ) -> Result<Arc<[u8]>, String> {
        if let Ok(guard) = self.block_cache.read() {
            if let Some((_, cached)) = guard.iter().find(|(idx, _)| *idx == block_idx) {
                return Ok(Arc::clone(cached));
            }
        }
        let raw: Arc<[u8]> = decode_block_from_slices(block_index, blocks, block_idx)?.into();
        if let Ok(mut guard) = self.block_cache.write() {
            if !guard.iter().any(|(idx, _)| *idx == block_idx) {
                if guard.len() >= BLOCK_CACHE_CAPACITY {
                    guard.pop_front();
                }
                guard.push_back((block_idx, Arc::clone(&raw)));
            }
        }
        Ok(raw)
    }

    fn decode_entries(&self, entry_ords: &[u32]) -> Result<Vec<CompactEntry>, String> {
        let entry_locs = slice_section(
            &self.bytes,
            self.header.entry_loc_offset,
            self.header.entry_loc_len,
        )?;
        let block_index = slice_section(
            &self.bytes,
            self.header.block_index_offset,
            self.header.block_index_len,
        )?;
        let blocks = slice_section(
            &self.bytes,
            self.header.blocks_offset,
            self.header.blocks_len,
        )?;

        let mut out = Vec::with_capacity(entry_ords.len());
        for &ord in entry_ords {
            let loc = read_entry_loc(entry_locs, ord)?;
            let raw_block = self.get_or_decode_block(block_index, blocks, loc.block_idx)?;
            let start = loc.offset_in_block as usize;
            let end = start
                .checked_add(loc.byte_len as usize)
                .ok_or("pack v2 entry slice overflow")?;
            let entry_bytes = raw_block
                .get(start..end)
                .ok_or("pack v2 entry slice out of bounds")?;
            let entry: CompactEntry = serde_json::from_slice(entry_bytes)
                .map_err(|err| format!("pack v2 entry {ord} decode error: {err}"))?;
            out.push(entry);
        }
        Ok(out)
    }

    fn folded_sections(&self) -> Result<SubIndexSections<'_>, String> {
        parse_sub_index_sections(
            &self.bytes,
            self.header.folded_offset,
            self.header.folded_len,
            "folded",
        )
    }

    fn en_sections(&self) -> Result<SubIndexSections<'_>, String> {
        let meta = self.metadata_ref()?;
        let (Some(offset), Some(len)) = (meta.en_index_offset, meta.en_index_len) else {
            return Err("pack v2 english section missing from metadata".to_owned());
        };
        parse_sub_index_sections(&self.bytes, offset, len, "english")
    }

    fn relation_sections(&self) -> Result<RelationSections<'_>, String> {
        let sec = slice_section(
            &self.bytes,
            self.header.relations_offset,
            self.header.relations_len,
        )?;
        if sec.len() < 32 {
            return Err("pack v2 relations section truncated".to_owned());
        }
        let fst_len = read_u64_le(sec, 0)?;
        let loc_len = read_u64_le(sec, 8)?;
        let bidx_len = read_u64_le(sec, 16)?;
        let blks_len = read_u64_le(sec, 24)?;
        let fst_off = 32u64;
        let loc_off = fst_off
            .checked_add(fst_len)
            .ok_or("pack v2 relation loc offset overflow")?;
        let bidx_off = loc_off
            .checked_add(loc_len)
            .ok_or("pack v2 relation block_index offset overflow")?;
        let blks_off = bidx_off
            .checked_add(bidx_len)
            .ok_or("pack v2 relation blocks offset overflow")?;
        let end = blks_off
            .checked_add(blks_len)
            .ok_or("pack v2 relation end overflow")?;
        if end != sec.len() as u64 {
            return Err("pack v2 relations section length mismatch".to_owned());
        }
        Ok(RelationSections {
            fst: slice_section(sec, fst_off, fst_len)?,
            loc_table: slice_section(sec, loc_off, loc_len)?,
            block_index: slice_section(sec, bidx_off, bidx_len)?,
            blocks: slice_section(sec, blks_off, blks_len)?,
        })
    }
}

fn read_entry_loc(table: &[u8], ord: u32) -> Result<EntryLoc, String> {
    let off = usize::try_from(ord)
        .ok()
        .and_then(|v| v.checked_mul(12))
        .ok_or("pack v2 entry_loc index overflow")?;
    Ok(EntryLoc {
        block_idx: read_u32_le(table, off)?,
        offset_in_block: read_u32_le(table, off + 4)?,
        byte_len: read_u32_le(table, off + 8)?,
    })
}

fn decode_block_from_slices(
    block_index: &[u8],
    blocks: &[u8],
    block_idx: u32,
) -> Result<Vec<u8>, String> {
    let off = usize::try_from(block_idx)
        .ok()
        .and_then(|v| v.checked_mul(16))
        .ok_or("pack v2 block_index overflow")?;
    let entry = BlockIndexEntry {
        compressed_offset: read_u64_le(block_index, off)?,
        compressed_len: read_u32_le(block_index, off + 8)?,
        raw_len: read_u32_le(block_index, off + 12)?,
    };
    let compressed = slice_section(
        blocks,
        entry.compressed_offset,
        u64::from(entry.compressed_len),
    )?;
    inflate_bytes(compressed, entry.raw_len)
}

fn read_postings_for_ord(
    ranges: &[u8],
    postings: &[u8],
    ord: u64,
    entry_count: u32,
) -> Result<Vec<u32>, String> {
    let off = usize::try_from(ord)
        .ok()
        .and_then(|v| v.checked_mul(8))
        .ok_or("pack v2 posting range overflow")?;
    let start = read_u32_le(ranges, off)?;
    let count = read_u32_le(ranges, off + 4)?;
    let mut out = Vec::with_capacity(count as usize);
    for i in 0..count {
        let p_off = usize::try_from(start.checked_add(i).ok_or("pack v2 posting idx overflow")?)
            .ok()
            .and_then(|v| v.checked_mul(4))
            .ok_or("pack v2 posting byte offset overflow")?;
        let entry_ord = read_u32_le(postings, p_off)?;
        if entry_ord >= entry_count {
            return Err(format!(
                "pack v2 posting entry_ord {entry_ord} >= entry_count {entry_count}"
            ));
        }
        out.push(entry_ord);
    }
    Ok(out)
}

fn slice_section(bytes: &[u8], offset: u64, len: u64) -> Result<&[u8], String> {
    let start = usize::try_from(offset).map_err(|_| "pack v2 offset exceeds usize")?;
    let size = usize::try_from(len).map_err(|_| "pack v2 len exceeds usize")?;
    let end = start.checked_add(size).ok_or("pack v2 end overflow")?;
    bytes.get(start..end).ok_or_else(|| {
        format!(
            "pack v2 section {start}..{end} out of bounds ({})",
            bytes.len()
        )
    })
}

fn parse_sub_index_sections<'a>(
    bytes: &'a [u8],
    offset: u64,
    len: u64,
    label: &str,
) -> Result<SubIndexSections<'a>, String> {
    let sec = slice_section(bytes, offset, len)?;
    if sec.len() < 24 {
        return Err(format!("pack v2 {label} section truncated"));
    }
    let fst_len = read_u64_le(sec, 0)?;
    let ranges_len = read_u64_le(sec, 8)?;
    let postings_len = read_u64_le(sec, 16)?;
    let fst_off = 24u64;
    let ranges_off = fst_off
        .checked_add(fst_len)
        .ok_or_else(|| format!("pack v2 {label} ranges offset overflow"))?;
    let postings_off = ranges_off
        .checked_add(ranges_len)
        .ok_or_else(|| format!("pack v2 {label} postings offset overflow"))?;
    let end = postings_off
        .checked_add(postings_len)
        .ok_or_else(|| format!("pack v2 {label} end overflow"))?;
    if end != sec.len() as u64 {
        return Err(format!("pack v2 {label} section length mismatch"));
    }
    Ok(SubIndexSections {
        fst: slice_section(sec, fst_off, fst_len)?,
        ranges: slice_section(sec, ranges_off, ranges_len)?,
        postings: slice_section(sec, postings_off, postings_len)?,
    })
}

fn validate_v2_layout(header: &CompactPackHeader, total_len: usize) -> Result<(), String> {
    let pre_sections = [
        (header.fst_offset, header.fst_len),
        (header.ranges_offset, header.ranges_len),
        (header.postings_offset, header.postings_len),
        (header.entry_loc_offset, header.entry_loc_len),
        (header.block_index_offset, header.block_index_len),
        (header.blocks_offset, header.blocks_len),
        (header.folded_offset, header.folded_len),
        (header.relations_offset, header.relations_len),
    ];
    let mut cursor = HEADER_SIZE_V2 as u64;
    for (idx, (off, len)) in pre_sections.iter().enumerate() {
        if *off != cursor {
            return Err(format!(
                "pack v2 layout: section {idx} expected offset {cursor}, got {off}"
            ));
        }
        cursor = cursor
            .checked_add(*len)
            .ok_or("pack v2 layout: size overflow")?;
    }
    if header.flags & V2_FLAG_HAS_ENGLISH_INDEX != 0 {
        let gap = header
            .metadata_offset
            .checked_sub(cursor)
            .ok_or("pack v2 layout: metadata offset precedes relations")?;
        if gap < 24 {
            return Err("pack v2 layout: english section smaller than framing header".to_owned());
        }
        cursor = header.metadata_offset;
    } else if header.metadata_offset != cursor {
        return Err(format!(
            "pack v2 layout: section 8 expected offset {cursor}, got {}",
            header.metadata_offset
        ));
    }
    cursor = cursor
        .checked_add(header.metadata_len)
        .ok_or("pack v2 layout: size overflow")?;
    if cursor != total_len as u64 {
        return Err(format!(
            "pack v2 layout: expected total bytes {cursor}, got {total_len}"
        ));
    }
    if header.ranges_len != u64::from(header.key_count) * 8 {
        return Err("pack v2 layout: ranges_len mismatch".to_owned());
    }
    if header.postings_len != u64::from(header.posting_count) * 4 {
        return Err("pack v2 layout: postings_len mismatch".to_owned());
    }
    if header.entry_loc_len != u64::from(header.entry_count) * 12 {
        return Err("pack v2 layout: entry_loc_len mismatch".to_owned());
    }
    if header.block_index_len != u64::from(header.block_count) * 16 {
        return Err("pack v2 layout: block_index_len mismatch".to_owned());
    }
    Ok(())
}

fn mayangoli_initial_alternatives(c: char) -> &'static [char] {
    match c {
        '\u{0BB2}' | '\u{0BB3}' | '\u{0BB4}' => &['\u{0BB2}', '\u{0BB3}', '\u{0BB4}'],
        '\u{0BA8}' | '\u{0BA9}' | '\u{0BA3}' => &['\u{0BA8}', '\u{0BA9}', '\u{0BA3}'],
        '\u{0BB0}' | '\u{0BB1}' => &['\u{0BB0}', '\u{0BB1}'],
        '\u{0B9A}' | '\u{0BB8}' | '\u{0BB6}' => &['\u{0B9A}', '\u{0BB8}', '\u{0BB6}'],
        _ => &[],
    }
}

/// Optimal string alignment (restricted Damerau-Levenshtein) with early exit above `max_dist`.
fn damerau_levenshtein(a: &[char], b: &[char], max_dist: usize) -> usize {
    let m = a.len();
    let n = b.len();
    if m.abs_diff(n) > max_dist {
        return max_dist + 1;
    }
    if m == 0 {
        return n;
    }
    if n == 0 {
        return m;
    }
    let inf = max_dist + 1;
    let mut prev2 = vec![0usize; n + 1];
    let mut prev1: Vec<usize> = (0..=n).collect();
    let mut curr = vec![0usize; n + 1];

    for i in 1..=m {
        curr[0] = i;
        let mut row_min = curr[0];
        for j in 1..=n {
            let cost = usize::from(a[i - 1] != b[j - 1]);
            let mut val = (prev1[j] + 1).min(curr[j - 1] + 1).min(prev1[j - 1] + cost);
            if i > 1 && j > 1 && a[i - 1] == b[j - 2] && a[i - 2] == b[j - 1] {
                val = val.min(prev2[j - 2] + 1);
            }
            curr[j] = val;
            if val < row_min {
                row_min = val;
            }
        }
        if row_min > max_dist {
            return inf;
        }
        std::mem::swap(&mut prev2, &mut prev1);
        std::mem::swap(&mut prev1, &mut curr);
    }
    prev1[n]
}

fn truncate_chars(s: &str, max_chars: usize) -> String {
    let mut chars = s.chars();
    let prefix: String = chars.by_ref().take(max_chars).collect();
    if chars.next().is_some() {
        format!("{prefix}…")
    } else {
        prefix
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn split_facet_tokens_handles_commas_semicolons_and_whitespace() {
        assert_eq!(
            split_facet_tokens("  physics , Optics;  ;astronomy "),
            vec!["physics", "Optics", "astronomy"]
        );
        assert!(split_facet_tokens(" , ; ").is_empty());
    }

    #[test]
    fn extract_english_tokens_normalizes_dedups_and_filters_stopwords() {
        let toks = extract_english_tokens("The Water of Life, and water-fall (H2O)!");
        assert_eq!(toks, vec!["water", "life", "fall", "h2o"]);
        assert!(extract_english_tokens("a an the of to in").is_empty());
        let long = "a".repeat(80);
        let long_toks = extract_english_tokens(&long);
        assert_eq!(long_toks.len(), 1);
        assert_eq!(long_toks[0].len(), 64);
    }

    #[test]
    fn english_index_and_facet_counts_roundtrip() {
        let input = CompactPackInput {
            pack_id: "en_unit".to_owned(),
            pack_tier: PackTier::VerifiedOpen,
            rights_status: "CC-BY-SA-4.0".to_owned(),
            license: "CC-BY-SA-4.0".to_owned(),
            dataset_version: "0.2.0".to_owned(),
            description: "unit".to_owned(),
            source_ids: vec!["s1".to_owned()],
            attribution_notice: "notice".to_owned(),
            entries: vec![
                CompactEntry {
                    entry_id: "e1".to_owned(),
                    headword: "\u{0BA8}\u{0BC0}\u{0BB0}\u{0BCD}".to_owned(),
                    pos: Some("NOUN".to_owned()),
                    domain: Some("Chemistry, Nature".to_owned()),
                    region: Some("TN; SL-JAFFNA".to_owned()),
                    register: Some("standard, literary".to_owned()),
                    senses: vec![CompactSense {
                        gloss_en: Some("water".to_owned()),
                        definition_en: Some("clear liquid H2O".to_owned()),
                        ..Default::default()
                    }],
                    source_id: "s1".to_owned(),
                    source_locator: "s1:1".to_owned(),
                    rights_status: "CC-BY-SA-4.0".to_owned(),
                    ..Default::default()
                },
                CompactEntry {
                    entry_id: "e2".to_owned(),
                    headword: "\u{0B85}\u{0BB0}\u{0BC1}\u{0BB5}\u{0BBF}".to_owned(),
                    pos: Some("NOUN".to_owned()),
                    domain: Some("Geography".to_owned()),
                    scientific_name: Some("Aqua cascade".to_owned()),
                    senses: vec![CompactSense {
                        gloss_en: Some("waterfall".to_owned()),
                        definition_en: Some("falling water cascade".to_owned()),
                        ..Default::default()
                    }],
                    source_id: "s1".to_owned(),
                    source_locator: "s1:2".to_owned(),
                    rights_status: "CC-BY-SA-4.0".to_owned(),
                    ..Default::default()
                },
            ],
            relations: vec![],
            build_folded_index: true,
        };
        let bytes = build_compact_pack(&input).expect("build");
        let view = CompactPackView::parse(bytes).expect("parse");
        assert!(view.has_english_index());
        let meta = view.metadata_ref().expect("meta");
        assert_eq!(meta.domain_counts.get("Chemistry"), Some(&1));
        assert_eq!(meta.domain_counts.get("Nature"), Some(&1));
        assert_eq!(meta.region_counts.get("TN"), Some(&1));
        assert_eq!(meta.region_counts.get("SL-JAFFNA"), Some(&1));
        assert_eq!(meta.register_counts.get("standard"), Some(&1));
        assert_eq!(meta.register_counts.get("literary"), Some(&1));
        assert!(meta.en_key_count >= 5);

        let hits = view.search_english("water", 10).expect("search water");
        assert_eq!(hits.len(), 2);
        assert_eq!(hits[0].entry_id, "e1");

        let multi = view
            .search_english("falling cascade", 10)
            .expect("multi token");
        assert_eq!(multi.len(), 1);
        assert_eq!(multi[0].entry_id, "e2");

        // Union fallback when intersection is empty
        let fallback = view
            .search_english("liquid cascade", 10)
            .expect("union fallback");
        assert_eq!(fallback.len(), 2);
    }

    #[test]
    fn tamil_only_pack_without_english_index_roundtrips_cleanly() {
        let input = CompactPackInput {
            pack_id: "ta_only".to_owned(),
            pack_tier: PackTier::VerifiedOpen,
            rights_status: "CC-BY-SA-4.0".to_owned(),
            license: "CC-BY-SA-4.0".to_owned(),
            dataset_version: "0.2.0".to_owned(),
            description: "ta only".to_owned(),
            source_ids: vec!["s1".to_owned()],
            attribution_notice: "notice".to_owned(),
            entries: vec![CompactEntry {
                entry_id: "t1".to_owned(),
                headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}".to_owned(),
                senses: vec![CompactSense {
                    gloss_ta: Some("\u{0BAE}\u{0BCA}\u{0BB4}\u{0BBF}".to_owned()),
                    ..Default::default()
                }],
                source_id: "s1".to_owned(),
                source_locator: "s1:1".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            }],
            relations: vec![],
            build_folded_index: false,
        };
        let bytes = build_compact_pack(&input).expect("build");
        let view = CompactPackView::parse(bytes).expect("parse");
        assert!(!view.has_english_index());
        assert!(view.search_english("tamil", 10).expect("search").is_empty());
    }
}
