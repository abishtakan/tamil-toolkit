//! `LexiconStore` trait and `PackRegistry` for runtime multi-pack lookup, prefix/folded search,
//! relations, and morphological stem checks across `TMLPACK1` and `TMLPACK2` packs.

use std::collections::{BTreeMap, BTreeSet};
#[cfg(feature = "std-fs")]
use std::path::{Path, PathBuf};
use std::sync::Arc;

use fst::{Automaton, IntoStreamer, Streamer};
use serde::{Deserialize, Serialize};
use tamil_norm::{fold_for_search, normalize_nfc, FoldingProfile};

use crate::lookup_v1::{LookupStatus, MAX_INPUT_BYTES};
use crate::v1::{CompiledEntry, CompiledPackView, PACK_MAGIC};
use crate::v2::{
    extract_english_tokens, split_facet_tokens, CompactEntry, CompactForm, CompactPackView,
    CompactRelation, CompactSense, PackTier, PrefixPageResult, PACK_MAGIC_V2,
};

/// Maximum results returned by a single prefix search call.
pub const MAX_SEARCH_LIMIT: usize = 200;

/// Tier selector for filtering queries between verified open packs and local historical packs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum TierFilter {
    #[default]
    All,
    Open,
    Local,
}

impl TierFilter {
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_ascii_lowercase().as_str() {
            "all" => Some(Self::All),
            "open" | "verified_open" => Some(Self::Open),
            "local" | "local_historical" => Some(Self::Local),
            _ => None,
        }
    }

    pub fn matches(self, tier: PackTier) -> bool {
        match self {
            Self::All => true,
            Self::Open => tier == PackTier::VerifiedOpen,
            Self::Local => tier == PackTier::LocalHistorical,
        }
    }
}

/// High-level named loading profile for `.tlpack` bundles.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum LexiconProfile {
    /// Lightweight verified open bundle (`core`, `names_taxa`, `regional`; ~2.9 MB).
    OpenLite,
    /// Full verified open bundle (`open-lite` + `ta_wiktionary`; ~15.3 MB, 90k+ words, CC-BY-SA-4.0).
    Open,
    /// Only local/self-hosted historical packs (~30.2 MB).
    Local,
    /// Complete combined bundle (`open` + `local`; ~45.6 MB, 241k+ unique words + relations).
    #[default]
    Full,
}

impl LexiconProfile {
    pub fn parse(s: &str) -> Option<Self> {
        match s.trim().to_ascii_lowercase().as_str() {
            "open-lite" | "open_lite" | "lite" => Some(Self::OpenLite),
            "open" | "verified" | "verified_open" => Some(Self::Open),
            "local" | "local_historical" => Some(Self::Local),
            "full" | "all" => Some(Self::Full),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::OpenLite => "open-lite",
            Self::Open => "open",
            Self::Local => "local",
            Self::Full => "full",
        }
    }

    /// Returns `true` if a `.tlpack` file with stem `pack_stem` and optional parent dir name
    /// (`"open"` / `"local"`) belongs to this profile.
    pub fn includes_pack_stem(self, pack_stem: &str, in_local_dir: bool) -> bool {
        let is_local = in_local_dir || pack_stem.starts_with("local_");
        match self {
            Self::Full => true,
            Self::Local => is_local,
            Self::Open => !is_local,
            Self::OpenLite => !is_local && matches!(pack_stem, "core" | "names_taxa" | "regional"),
        }
    }
}

/// High-level conceptual lexicon category grouping open & local packs intuitively.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LexiconCategory {
    Dictionary,
    Terminology,
    Phrases,
    Regional,
    NamesTaxa,
    Heritage,
    Relations,
}

impl LexiconCategory {
    pub fn parse(s: &str) -> Option<Self> {
        match s.trim().to_ascii_lowercase().as_str() {
            "dictionary" | "dict" | "core" => Some(Self::Dictionary),
            "terminology" | "term" | "technical" => Some(Self::Terminology),
            "phrases" | "phrase" | "mwe" | "idioms" => Some(Self::Phrases),
            "regional" | "dialect" | "dialects" => Some(Self::Regional),
            "names_taxa" | "names-taxa" | "names" | "taxa" => Some(Self::NamesTaxa),
            "heritage" | "literary" | "loans" | "loanwords" => Some(Self::Heritage),
            "relations" | "synonyms" => Some(Self::Relations),
            _ => None,
        }
    }

    pub fn as_str(self) -> &'static str {
        match self {
            Self::Dictionary => "dictionary",
            Self::Terminology => "terminology",
            Self::Phrases => "phrases",
            Self::Regional => "regional",
            Self::NamesTaxa => "names_taxa",
            Self::Heritage => "heritage",
            Self::Relations => "relations",
        }
    }
}

/// Maps any canonical or local `pack_id` into its high-level [`LexiconCategory`].
pub fn pack_category(pack_id: &str) -> LexiconCategory {
    match pack_id {
        "core" | "ta_wiktionary" | "local_core" => LexiconCategory::Dictionary,
        "terminology" | "local_terminology" => LexiconCategory::Terminology,
        "local_phrases" => LexiconCategory::Phrases,
        "regional" | "local_dialect" => LexiconCategory::Regional,
        "names_taxa" | "local_names_taxa" => LexiconCategory::NamesTaxa,
        "local_literary" | "local_loans" => LexiconCategory::Heritage,
        "local_relations" => LexiconCategory::Relations,
        other if other.contains("term") => LexiconCategory::Terminology,
        other if other.contains("phrase") => LexiconCategory::Phrases,
        other if other.contains("dialect") || other.contains("region") => LexiconCategory::Regional,
        other if other.contains("name") || other.contains("taxa") => LexiconCategory::NamesTaxa,
        other if other.contains("literary") || other.contains("loan") => LexiconCategory::Heritage,
        other if other.contains("relation") => LexiconCategory::Relations,
        _ => LexiconCategory::Dictionary,
    }
}

/// Filtering and matching scope for compact lookups, stem checks, define, and relation queries.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct QueryScope {
    #[serde(default)]
    pub packs: Option<Vec<String>>,
    #[serde(default)]
    pub tier: TierFilter,
    #[serde(default)]
    pub category: Option<LexiconCategory>,
    #[serde(default)]
    pub pos: Option<String>,
    #[serde(default)]
    pub domain: Option<String>,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub register: Option<String>,
    #[serde(default)]
    pub folded: bool,
}

/// Options controlling FST prefix search and cursor pagination.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrefixSearchOptions {
    #[serde(default = "default_search_limit")]
    pub limit: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub after_key: Option<String>,
    #[serde(default)]
    pub scope: QueryScope,
}

fn default_search_limit() -> usize {
    25
}

fn is_false(b: &bool) -> bool {
    !*b
}

impl Default for PrefixSearchOptions {
    fn default() -> Self {
        Self {
            limit: default_search_limit(),
            after_key: None,
            scope: QueryScope::default(),
        }
    }
}

/// Metadata summary of a loaded pack (uniform across `TMLPACK1` and `TMLPACK2`).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactPackSummary {
    pub pack_id: String,
    pub category: LexiconCategory,
    pub index_format_version: u32,
    pub schema_version: u32,
    pub pack_tier: PackTier,
    pub rights_status: String,
    pub license: String,
    pub dataset_version: String,
    pub description: String,
    pub entry_count: u32,
    pub sense_count: u32,
    pub relation_count: u32,
    pub distinct_headwords: u32,
    pub byte_len: usize,
    pub checksum_sha256: String,
    pub has_folded_index: bool,
    pub has_relations: bool,
    #[serde(default)]
    pub has_english_index: bool,
    pub source_ids: Vec<String>,
    pub attribution_notice: String,
    pub domains: Vec<String>,
    pub regions: Vec<String>,
    pub registers: Vec<String>,
}

/// Type alias for search options used by [`LexiconStore::search_english`] and prefix search.
pub type LexiconSearchOptions = PrefixSearchOptions;

/// Type alias for prefix/English search results returned by [`LexiconStore`].
pub type LexiconPrefixSearchResult = PrefixSearchResult;

/// Aggregated statistics and facet counts across all mounted packs in a [`LexiconStore`].
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct LexiconStoreStats {
    pub pack_count: usize,
    pub total_entries: u64,
    pub total_senses: u64,
    pub total_relations: u64,
    pub total_bytes: usize,
    pub packs: Vec<CompactPackSummary>,
    #[serde(default)]
    pub category_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub pos_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub domain_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub region_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub register_counts: BTreeMap<String, u32>,
    #[serde(default)]
    pub has_english_index: bool,
}

/// Matched entry returned by compact runtime lookup, tagged with its owning pack and tier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AnnotatedEntry {
    pub pack_id: String,
    pub pack_tier: PackTier,
    pub entry: CompactEntry,
}

/// Result of [`LexiconStore::lookup_compact`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactLookupResult {
    pub status: LookupStatus,
    pub query: String,
    pub canonical_query: String,
    pub folded: bool,
    pub searched_packs: Vec<String>,
    pub total_entries: usize,
    pub entries: Vec<AnnotatedEntry>,
}

/// One autocomplete / prefix-search hit returned by [`LexiconStore::prefix_search`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrefixSearchHit {
    pub headword: String,
    pub matched_key: String,
    pub packs: Vec<String>,
    pub pack_tiers: Vec<PackTier>,
    pub pos: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preview_gloss: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub domain: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub region: Option<String>,
    pub entry_count: usize,
}

/// Result of [`LexiconStore::prefix_search`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PrefixSearchResult {
    pub prefix: String,
    pub canonical_prefix: String,
    pub folded: bool,
    pub searched_packs: Vec<String>,
    pub hits: Vec<PrefixSearchHit>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<String>,
    #[serde(default, skip_serializing_if = "is_false")]
    pub has_more: bool,
}

/// One fuzzy spelling suggestion returned by [`LexiconStore::fuzzy_search`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FuzzySearchHit {
    pub headword: String,
    pub distance: u32,
    pub packs: Vec<String>,
    pub pack_tiers: Vec<PackTier>,
    pub pos: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preview_gloss: Option<String>,
}

/// Result of [`LexiconStore::fuzzy_search`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct FuzzySearchResult {
    pub query: String,
    pub canonical_query: String,
    pub max_distance: u32,
    pub searched_packs: Vec<String>,
    pub hits: Vec<FuzzySearchHit>,
}

/// Result of [`LexiconStore::lookup_relations`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RelationsResult {
    pub status: LookupStatus,
    pub query: String,
    pub canonical_query: String,
    pub searched_packs: Vec<String>,
    pub relations: Vec<CompactRelation>,
}

/// One deduplicated meaning line inside [`WordDefinition`], preserving provenance & rights tier.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WordMeaning {
    pub text: String,
    pub language: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pos: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub domain: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub region: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub register: Option<String>,
    pub pack_id: String,
    pub category: LexiconCategory,
    pub pack_tier: PackTier,
    pub rights_status: String,
}

/// Grouped semantic relations for a single word inside [`WordDefinition`].
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct WordRelationsGroup {
    #[serde(default)]
    pub synonyms: Vec<String>,
    #[serde(default)]
    pub antonyms: Vec<String>,
    #[serde(default)]
    pub related: Vec<String>,
    #[serde(default)]
    pub hypernyms: Vec<String>,
}

/// Source attribution entry inside [`WordDefinition`].
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WordSourceRef {
    pub pack_id: String,
    pub category: LexiconCategory,
    pub pack_tier: PackTier,
    pub rights_status: String,
    pub source_id: String,
    pub source_locator: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub permalink: Option<String>,
}

/// Unified, deduplicated, provenance-preserving word definition across all mounted packs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct WordDefinition {
    pub status: LookupStatus,
    pub query: String,
    pub canonical_query: String,
    pub headword: String,
    pub folded: bool,
    pub searched_packs: Vec<String>,
    pub categories: Vec<LexiconCategory>,
    pub pos: Vec<String>,
    pub meanings_en: Vec<WordMeaning>,
    pub meanings_ta: Vec<WordMeaning>,
    pub examples: Vec<String>,
    pub variants: Vec<String>,
    pub domains: Vec<String>,
    pub regions: Vec<String>,
    pub registers: Vec<String>,
    pub standard_equivalents: Vec<String>,
    pub pure_tamil_equivalents: Vec<String>,
    pub origin_languages: Vec<String>,
    pub scientific_names: Vec<String>,
    pub literary_sources: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub matched_headwords: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub ipa: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub verb_classes: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub transitivity: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub root_words: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub etymology_types: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub dedr_ids: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub sandhi_behaviors: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub animacy_genders: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub frequency_tiers: Vec<String>,
    pub relations: WordRelationsGroup,
    pub has_verified_open: bool,
    pub has_local_historical: bool,
    pub entry_count: usize,
    pub sources: Vec<WordSourceRef>,
}

/// Owned `TMLPACK1` container backed by `Arc<[u8]>` so `PackRegistry` can mount v1 & v2 together.
#[derive(Debug, Clone)]
pub struct OwnedV1Pack {
    bytes: Arc<[u8]>,
    summary: CompactPackSummary,
}

impl OwnedV1Pack {
    pub fn parse(bytes: impl Into<Arc<[u8]>>) -> Result<Self, String> {
        let bytes: Arc<[u8]> = bytes.into();
        let view = CompiledPackView::parse(&bytes)?;
        let meta = view.metadata_ref()?;
        let checksum_sha256: String = view
            .header()
            .checksum_sha256
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect();
        let summary = CompactPackSummary {
            pack_id: meta.pack_id.clone(),
            category: pack_category(&meta.pack_id),
            index_format_version: meta.index_format_version,
            schema_version: meta.schema_version,
            pack_tier: PackTier::VerifiedOpen,
            rights_status: "CC-BY-SA-4.0".to_owned(),
            license: "CC-BY-SA-4.0".to_owned(),
            dataset_version: meta.dataset_version.clone(),
            description: meta.description.clone(),
            entry_count: meta.entry_count,
            sense_count: meta.sense_count,
            relation_count: meta.relation_count,
            distinct_headwords: view.header().key_count,
            byte_len: bytes.len(),
            checksum_sha256,
            has_folded_index: false,
            has_relations: meta.relation_count > 0,
            has_english_index: false,
            source_ids: meta.sources.iter().map(|s| s.source_id.clone()).collect(),
            attribution_notice: meta
                .sources
                .first()
                .map(|s| s.attribution_text.clone())
                .unwrap_or_default(),
            domains: meta.vocabularies.domains.clone(),
            regions: meta.coverage.region_codes.clone(),
            registers: meta.coverage.register_codes.clone(),
        };
        Ok(Self { bytes, summary })
    }

    pub fn summary(&self) -> &CompactPackSummary {
        &self.summary
    }

    pub fn bytes(&self) -> &[u8] {
        &self.bytes
    }

    fn parse_view(&self) -> Result<CompiledPackView<'_>, String> {
        CompiledPackView::parse(&self.bytes)
    }

    fn contains_exact(&self, normalized_key: &str) -> bool {
        let Ok(view) = self.parse_view() else {
            return false;
        };
        view.fst_map()
            .ok()
            .and_then(|map| map.get(normalized_key.as_bytes()))
            .is_some()
    }

    fn lookup_exact_compact(&self, query: &str) -> Result<Vec<CompactEntry>, String> {
        let view = self.parse_view()?;
        let key = normalize_nfc(query);
        let map = view.fst_map()?;
        let Some(ord) = map.get(key.as_bytes()) else {
            return Ok(Vec::new());
        };
        let range = view.posting_range(ord)?;
        let indices = view.posting_entry_indices(range)?;
        let mut out = Vec::with_capacity(indices.len());
        for idx in indices {
            let entry = view.entry(idx)?;
            out.push(v1_entry_to_compact(&entry));
        }
        Ok(out)
    }

    fn prefix_lookup_compact(
        &self,
        prefix: &str,
        limit: usize,
    ) -> Result<Vec<(String, Vec<CompactEntry>)>, String> {
        let view = self.parse_view()?;
        let norm_prefix = normalize_nfc(prefix);
        let map = view.fst_map()?;
        let matcher = fst::automaton::Str::new(&norm_prefix).starts_with();
        let mut stream = map.search(matcher).into_stream();
        let mut results = Vec::new();
        while let Some((key_bytes, ord)) = stream.next() {
            let key_str = std::str::from_utf8(key_bytes)
                .map_err(|err| format!("pack v1 fst utf8 error: {err}"))?
                .to_owned();
            let range = view.posting_range(ord)?;
            let indices = view.posting_entry_indices(range)?;
            let mut entries = Vec::with_capacity(indices.len());
            for idx in indices {
                entries.push(v1_entry_to_compact(&view.entry(idx)?));
            }
            results.push((key_str, entries));
            if results.len() >= limit {
                break;
            }
        }
        Ok(results)
    }
}

/// One loaded pack in [`PackRegistry`], supporting both `TMLPACK1` and `TMLPACK2`.
#[derive(Debug, Clone)]
pub enum LoadedPack {
    V1(OwnedV1Pack),
    V2(CompactPackView),
}

impl LoadedPack {
    /// Auto-detects `TMLPACK1` vs `TMLPACK2` magic and parses/validates the binary image.
    pub fn parse_bytes(bytes: impl Into<Arc<[u8]>>) -> Result<Self, String> {
        let bytes: Arc<[u8]> = bytes.into();
        if bytes.len() < 8 {
            return Err("lexicon pack: payload shorter than 8-byte magic header".to_owned());
        }
        match &bytes[0..8] {
            m if m == PACK_MAGIC => Ok(Self::V1(OwnedV1Pack::parse(bytes)?)),
            m if m == PACK_MAGIC_V2 => Ok(Self::V2(CompactPackView::parse(bytes)?)),
            _ => Err(
                "lexicon pack: unrecognized magic header (expected TMLPACK1 or TMLPACK2)"
                    .to_owned(),
            ),
        }
    }

    pub fn summary(&self) -> CompactPackSummary {
        match self {
            Self::V1(pack) => pack.summary().clone(),
            Self::V2(view) => {
                let meta = view.metadata_ref().expect("validated on parse");
                CompactPackSummary {
                    pack_id: meta.pack_id.clone(),
                    category: pack_category(&meta.pack_id),
                    index_format_version: meta.index_format_version,
                    schema_version: meta.schema_version,
                    pack_tier: meta.pack_tier,
                    rights_status: meta.rights_status.clone(),
                    license: meta.license.clone(),
                    dataset_version: meta.dataset_version.clone(),
                    description: meta.description.clone(),
                    entry_count: meta.entry_count,
                    sense_count: meta.sense_count,
                    relation_count: meta.relation_count,
                    distinct_headwords: meta.distinct_headwords,
                    byte_len: view.byte_len(),
                    checksum_sha256: view.checksum_hex(),
                    has_folded_index: view.has_folded_index(),
                    has_relations: view.has_relations(),
                    has_english_index: view.has_english_index(),
                    source_ids: meta.source_ids.clone(),
                    attribution_notice: meta.attribution_notice.clone(),
                    domains: meta.domains.clone(),
                    regions: meta.regions.clone(),
                    registers: meta.registers.clone(),
                }
            }
        }
    }

    pub fn pack_id(&self) -> &str {
        match self {
            Self::V1(pack) => &pack.summary().pack_id,
            Self::V2(view) => &view.metadata_ref().expect("validated on parse").pack_id,
        }
    }

    pub fn pack_tier(&self) -> PackTier {
        match self {
            Self::V1(_) => PackTier::VerifiedOpen,
            Self::V2(view) => view.metadata_ref().expect("validated on parse").pack_tier,
        }
    }

    pub fn category(&self) -> LexiconCategory {
        pack_category(self.pack_id())
    }

    pub fn contains_word(&self, key: &str, folded: bool) -> bool {
        match self {
            Self::V1(pack) => {
                if folded {
                    false
                } else {
                    pack.contains_exact(key)
                }
            }
            Self::V2(view) => {
                if folded {
                    view.contains_folded(key)
                } else {
                    view.contains_exact(key)
                }
            }
        }
    }

    pub fn lookup_compact(&self, query: &str, folded: bool) -> Result<Vec<CompactEntry>, String> {
        match self {
            Self::V1(pack) => {
                if folded {
                    Ok(Vec::new())
                } else {
                    pack.lookup_exact_compact(query)
                }
            }
            Self::V2(view) => {
                if folded {
                    view.lookup_folded(query)
                } else {
                    view.lookup_exact(query)
                }
            }
        }
    }

    pub fn prefix_lookup(
        &self,
        prefix: &str,
        limit: usize,
        folded: bool,
    ) -> Result<Vec<(String, Vec<CompactEntry>)>, String> {
        match self {
            Self::V1(pack) => {
                if folded {
                    Ok(Vec::new())
                } else {
                    pack.prefix_lookup_compact(prefix, limit)
                }
            }
            Self::V2(view) => view.prefix_lookup(prefix, limit, folded),
        }
    }

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
        match self {
            Self::V1(pack) => {
                if folded {
                    Ok((Vec::new(), false))
                } else {
                    let raw = pack.prefix_lookup_compact(prefix, max_scan.min(5_000))?;
                    let mut out = Vec::new();
                    let mut has_more = false;
                    for (k, entries) in raw {
                        if let Some(cursor) = after_key {
                            if k.as_str() <= cursor {
                                continue;
                            }
                        }
                        let matched: Vec<CompactEntry> =
                            entries.into_iter().filter(&mut predicate).collect();
                        if matched.is_empty() {
                            continue;
                        }
                        if out.len() >= limit {
                            has_more = true;
                            break;
                        }
                        out.push((k, matched));
                    }
                    Ok((out, has_more))
                }
            }
            Self::V2(view) => {
                view.prefix_lookup_filtered(prefix, after_key, limit, max_scan, folded, predicate)
            }
        }
    }

    pub fn longest_prefix_matches(&self, word: &str) -> Result<Vec<String>, String> {
        match self {
            Self::V1(_) => Ok(Vec::new()),
            Self::V2(view) => view.longest_prefix_matches(word),
        }
    }

    pub fn fuzzy_lookup(
        &self,
        word: &str,
        max_distance: u32,
        limit: usize,
    ) -> Result<Vec<(String, u32, Vec<CompactEntry>)>, String> {
        match self {
            Self::V1(_) => Ok(Vec::new()),
            Self::V2(view) => view.fuzzy_lookup(word, max_distance, limit),
        }
    }

    pub fn lookup_relations(&self, headword: &str) -> Result<Vec<CompactRelation>, String> {
        match self {
            Self::V1(_) => Ok(Vec::new()),
            Self::V2(view) => view.lookup_relations(headword),
        }
    }

    pub fn search_english(
        &self,
        query: &str,
        max_candidates: usize,
    ) -> Result<Vec<CompactEntry>, String> {
        match self {
            Self::V1(_) => Ok(Vec::new()),
            Self::V2(view) => view.search_english(query, max_candidates),
        }
    }
}

/// Core trait consumed by Rank 3–5 crates (`tamil-morph`, `tamil-dialect`, `tamil-spell`,
/// `pg_tamil`, `tamil-toolkit`) to query Tamil lexicons without coupling to storage or licensing.
pub trait LexiconStore: Send + Sync {
    /// Lists all mounted packs sorted by `pack_id`.
    fn list_packs(&self) -> Vec<CompactPackSummary>;

    /// Returns aggregated pack totals and facet counts across all mounted packs.
    fn stats(&self) -> LexiconStoreStats {
        let packs = self.list_packs();
        let total_entries: u64 = packs.iter().map(|p| u64::from(p.entry_count)).sum();
        let total_senses: u64 = packs.iter().map(|p| u64::from(p.sense_count)).sum();
        let total_relations: u64 = packs.iter().map(|p| u64::from(p.relation_count)).sum();
        let total_bytes: usize = packs.iter().map(|p| p.byte_len).sum();
        let has_english_index = packs.iter().any(|p| p.has_english_index);
        let mut category_counts: BTreeMap<String, u32> = BTreeMap::new();
        for p in &packs {
            let entry = category_counts
                .entry(p.category.as_str().to_owned())
                .or_insert(0);
            *entry = entry.saturating_add(p.entry_count);
        }
        LexiconStoreStats {
            pack_count: packs.len(),
            total_entries,
            total_senses,
            total_relations,
            total_bytes,
            packs,
            category_counts,
            pos_counts: BTreeMap::new(),
            domain_counts: BTreeMap::new(),
            region_counts: BTreeMap::new(),
            register_counts: BTreeMap::new(),
            has_english_index,
        }
    }

    /// Searches the reverse English-to-Tamil gloss/definition FST index across selected packs.
    fn search_english(
        &self,
        query: &str,
        options: &PrefixSearchOptions,
    ) -> Result<PrefixSearchResult, String>;

    /// Fast existence check (zero block decompression on `TMLPACK2` packs).
    fn contains_word(&self, word: &str, scope: &QueryScope) -> bool;

    /// Returns `true` if `word` exists in the store with the specified POS tag (e.g., `"NOUN"`, `"VERB"`).
    fn has_word_with_pos(&self, word: &str, pos: &str, scope: &QueryScope) -> bool {
        let mut scoped = scope.clone();
        scoped.pos = Some(pos.to_ascii_uppercase());
        self.lookup_compact(word, &scoped)
            .map(|res| res.total_entries > 0)
            .unwrap_or(false)
    }

    /// Performs exact NFC (or opt-in *Mayangoli*-folded) lookup across selected packs.
    fn lookup_compact(&self, word: &str, scope: &QueryScope)
        -> Result<CompactLookupResult, String>;

    /// Performs FST prefix search (autocomplete) across selected packs.
    fn prefix_search(
        &self,
        prefix: &str,
        options: &PrefixSearchOptions,
    ) -> Result<PrefixSearchResult, String>;

    /// Queries indexed lexical relations (`SYNONYM`, `ANTONYM`, `RELATED`, `HYPERNYM`).
    fn lookup_relations(&self, word: &str, scope: &QueryScope) -> Result<RelationsResult, String>;

    /// Bounded Damerau-Levenshtein fuzzy search (`max_distance` 1..=2) for spellcheck & typo recovery.
    fn fuzzy_search(
        &self,
        word: &str,
        max_distance: u32,
        options: &PrefixSearchOptions,
    ) -> Result<FuzzySearchResult, String>;

    /// Returns exact FST keys that are char-boundary prefixes of `word`, ordered longest-first.
    fn longest_prefix_matches(&self, word: &str, scope: &QueryScope)
        -> Result<Vec<String>, String>;

    /// Batch lookup convenience across multiple words.
    fn lookup_many(
        &self,
        words: &[&str],
        scope: &QueryScope,
    ) -> Result<Vec<CompactLookupResult>, String> {
        words
            .iter()
            .map(|w| self.lookup_compact(w, scope))
            .collect()
    }

    /// Returns a unified, deduplicated, provenance-preserving [`WordDefinition`] merging
    /// meanings, domains, regional/dialect notes, variants, morphological metadata, and semantic relations.
    fn define(&self, word: &str, scope: &QueryScope) -> Result<WordDefinition, String> {
        let mut lookup = self.lookup_compact(word, scope)?;
        let nfc_word = normalize_nfc(word);

        // Under folded=true, prefer exact NFC headword match first so e.g. `அரை` is never
        // retitled as `அறை` when exact `அரை` exists in the matched entries.
        if scope.folded && lookup.entries.len() > 1 {
            lookup.entries.sort_by(|a, b| {
                let a_exact = a.entry.headword == nfc_word;
                let b_exact = b.entry.headword == nfc_word;
                b_exact.cmp(&a_exact).then_with(|| {
                    (a.pack_tier, &a.pack_id, &a.entry.entry_id).cmp(&(
                        b.pack_tier,
                        &b.pack_id,
                        &b.entry.entry_id,
                    ))
                })
            });
        }

        let headword = if lookup.entries.iter().any(|e| e.entry.headword == nfc_word) {
            nfc_word.clone()
        } else {
            lookup
                .entries
                .first()
                .map(|e| e.entry.headword.clone())
                .unwrap_or_else(|| nfc_word.clone())
        };

        // Respect scope.category: only fetch relations when no category filter is set,
        // when category == Relations, or when the category itself matched at least one entry.
        let should_fetch_relations = scope.category.is_none()
            || scope.category == Some(LexiconCategory::Relations)
            || lookup.total_entries > 0;
        let rel_res = if should_fetch_relations {
            let rel_scope = QueryScope {
                packs: None,
                tier: scope.tier,
                category: None,
                ..Default::default()
            };
            self.lookup_relations(&headword, &rel_scope)?
        } else {
            RelationsResult {
                status: LookupStatus::NotFound,
                query: headword.clone(),
                canonical_query: headword.clone(),
                searched_packs: Vec::new(),
                relations: Vec::new(),
            }
        };

        let mut categories_set: BTreeSet<LexiconCategory> = BTreeSet::new();
        let mut pos_set: BTreeSet<String> = BTreeSet::new();
        let mut meanings_en: Vec<WordMeaning> = Vec::new();
        let mut meanings_ta: Vec<WordMeaning> = Vec::new();
        let mut seen_en: BTreeSet<String> = BTreeSet::new();
        let mut seen_ta: BTreeSet<String> = BTreeSet::new();
        let mut examples_set: BTreeSet<String> = BTreeSet::new();
        let mut variants_set: BTreeSet<String> = BTreeSet::new();
        let mut domains_set: BTreeSet<String> = BTreeSet::new();
        let mut regions_set: BTreeSet<String> = BTreeSet::new();
        let mut registers_set: BTreeSet<String> = BTreeSet::new();
        let mut std_eq_set: BTreeSet<String> = BTreeSet::new();
        let mut pure_ta_set: BTreeSet<String> = BTreeSet::new();
        let mut origin_set: BTreeSet<String> = BTreeSet::new();
        let mut sci_set: BTreeSet<String> = BTreeSet::new();
        let mut lit_set: BTreeSet<String> = BTreeSet::new();
        let mut matched_hw_set: BTreeSet<String> = BTreeSet::new();
        let mut ipa_set: BTreeSet<String> = BTreeSet::new();
        let mut verb_class_set: BTreeSet<String> = BTreeSet::new();
        let mut transitivity_set: BTreeSet<String> = BTreeSet::new();
        let mut root_word_set: BTreeSet<String> = BTreeSet::new();
        let mut etymology_set: BTreeSet<String> = BTreeSet::new();
        let mut dedr_set: BTreeSet<String> = BTreeSet::new();
        let mut sandhi_set: BTreeSet<String> = BTreeSet::new();
        let mut animacy_set: BTreeSet<String> = BTreeSet::new();
        let mut freq_set: BTreeSet<String> = BTreeSet::new();
        let mut sources: Vec<WordSourceRef> = Vec::new();
        let mut seen_sources: BTreeSet<(String, String)> = BTreeSet::new();
        let mut has_verified_open = false;
        let mut has_local_historical = false;

        for ann in &lookup.entries {
            let cat = pack_category(&ann.pack_id);
            categories_set.insert(cat);
            match ann.pack_tier {
                PackTier::VerifiedOpen => has_verified_open = true,
                PackTier::LocalHistorical => has_local_historical = true,
            }
            let e = &ann.entry;
            if !e.headword.is_empty() {
                matched_hw_set.insert(e.headword.clone());
            }
            if let Some(p) = e.pos.as_deref().filter(|s| !s.is_empty()) {
                pos_set.insert(p.to_owned());
            }
            if let Some(d) = e.domain.as_deref().filter(|s| !s.is_empty()) {
                for tok in split_facet_tokens(d) {
                    domains_set.insert(tok);
                }
            }
            if let Some(r) = e.region.as_deref().filter(|s| !s.is_empty()) {
                for tok in split_facet_tokens(r) {
                    regions_set.insert(tok);
                }
            }
            if let Some(reg) = e.register.as_deref().filter(|s| !s.is_empty()) {
                for tok in split_facet_tokens(reg) {
                    registers_set.insert(tok);
                }
            }
            if let Some(v) = e.standard_equivalent.as_deref().filter(|s| !s.is_empty()) {
                std_eq_set.insert(v.to_owned());
            }
            if let Some(v) = e.pure_tamil_equivalent.as_deref().filter(|s| !s.is_empty()) {
                pure_ta_set.insert(v.to_owned());
            }
            if let Some(v) = e.origin_language.as_deref().filter(|s| !s.is_empty()) {
                origin_set.insert(v.to_owned());
            }
            if let Some(v) = e.scientific_name.as_deref().filter(|s| !s.is_empty()) {
                sci_set.insert(v.to_owned());
            }
            if let Some(v) = e.literary_source.as_deref().filter(|s| !s.is_empty()) {
                lit_set.insert(v.to_owned());
            }
            if let Some(v) = e.verb_class.as_deref().filter(|s| !s.is_empty()) {
                verb_class_set.insert(v.to_owned());
            }
            if let Some(v) = e.transitivity.as_deref().filter(|s| !s.is_empty()) {
                transitivity_set.insert(v.to_owned());
            }
            if let Some(v) = e.root_word.as_deref().filter(|s| !s.is_empty()) {
                root_word_set.insert(v.to_owned());
            }
            if let Some(v) = e.etymology_type.as_deref().filter(|s| !s.is_empty()) {
                etymology_set.insert(v.to_owned());
            }
            if let Some(v) = e.dedr_id.as_deref().filter(|s| !s.is_empty()) {
                dedr_set.insert(v.to_owned());
            }
            if let Some(v) = e.sandhi_behavior.as_deref().filter(|s| !s.is_empty()) {
                sandhi_set.insert(v.to_owned());
            }
            if let Some(v) = e.animacy_gender.as_deref().filter(|s| !s.is_empty()) {
                animacy_set.insert(v.to_owned());
            }
            if let Some(v) = e.frequency_tier.as_deref().filter(|s| !s.is_empty()) {
                freq_set.insert(v.to_owned());
            }
            for form in &e.forms {
                if form.role == "variant" && !form.text.is_empty() && form.text != headword {
                    variants_set.insert(form.text.clone());
                } else if form.role == "ipa" && !form.text.is_empty() {
                    ipa_set.insert(form.text.clone());
                }
            }
            for s in &e.senses {
                let s_dom = s.domain.clone().or_else(|| e.domain.clone());
                let s_reg = s.region.clone().or_else(|| e.region.clone());
                let s_rgst = s.register.clone().or_else(|| e.register.clone());
                if let Some(d) = s_dom.as_deref().filter(|x| !x.is_empty()) {
                    for tok in split_facet_tokens(d) {
                        domains_set.insert(tok);
                    }
                }
                if let Some(r) = s_reg.as_deref().filter(|x| !x.is_empty()) {
                    for tok in split_facet_tokens(r) {
                        regions_set.insert(tok);
                    }
                }
                if let Some(rg) = s_rgst.as_deref().filter(|x| !x.is_empty()) {
                    for tok in split_facet_tokens(rg) {
                        registers_set.insert(tok);
                    }
                }
                for candidate in [s.gloss_en.as_deref(), s.definition_en.as_deref()]
                    .into_iter()
                    .flatten()
                {
                    let trimmed = candidate.trim();
                    let dedup_key = normalize_en_dedup_key(trimmed);
                    if !trimmed.is_empty() && seen_en.insert(dedup_key) {
                        meanings_en.push(WordMeaning {
                            text: trimmed.to_owned(),
                            language: "eng".to_owned(),
                            pos: e.pos.clone(),
                            domain: s_dom.clone(),
                            region: s_reg.clone(),
                            register: s_rgst.clone(),
                            pack_id: ann.pack_id.clone(),
                            category: cat,
                            pack_tier: ann.pack_tier,
                            rights_status: e.rights_status.clone(),
                        });
                    }
                }
                for candidate in [s.gloss_ta.as_deref(), s.definition_ta.as_deref()]
                    .into_iter()
                    .flatten()
                {
                    let trimmed = candidate.trim();
                    if !trimmed.is_empty() && seen_ta.insert(trimmed.to_owned()) {
                        meanings_ta.push(WordMeaning {
                            text: trimmed.to_owned(),
                            language: "tam".to_owned(),
                            pos: e.pos.clone(),
                            domain: s_dom.clone(),
                            region: s_reg.clone(),
                            register: s_rgst.clone(),
                            pack_id: ann.pack_id.clone(),
                            category: cat,
                            pack_tier: ann.pack_tier,
                            rights_status: e.rights_status.clone(),
                        });
                    }
                }
                for ex in &s.examples {
                    let trimmed = ex.trim();
                    if !trimmed.is_empty() {
                        examples_set.insert(trimmed.to_owned());
                    }
                }
            }
            if seen_sources.insert((ann.pack_id.clone(), e.source_locator.clone())) {
                sources.push(WordSourceRef {
                    pack_id: ann.pack_id.clone(),
                    category: cat,
                    pack_tier: ann.pack_tier,
                    rights_status: e.rights_status.clone(),
                    source_id: e.source_id.clone(),
                    source_locator: e.source_locator.clone(),
                    permalink: e.permalink.clone(),
                });
            }
        }

        let mut syn_set: BTreeSet<String> = BTreeSet::new();
        let mut ant_set: BTreeSet<String> = BTreeSet::new();
        let mut rel_set: BTreeSet<String> = BTreeSet::new();
        let mut hyp_set: BTreeSet<String> = BTreeSet::new();
        for rel in &rel_res.relations {
            match rel.relation_code.as_str() {
                "SYNONYM" => {
                    syn_set.insert(rel.target_headword.clone());
                }
                "ANTONYM" => {
                    ant_set.insert(rel.target_headword.clone());
                }
                "HYPERNYM" => {
                    hyp_set.insert(rel.target_headword.clone());
                }
                _ => {
                    rel_set.insert(rel.target_headword.clone());
                }
            }
        }

        let has_rels = !syn_set.is_empty()
            || !ant_set.is_empty()
            || !rel_set.is_empty()
            || !hyp_set.is_empty();
        // Record provenance & rights tier for contributing relation packs so local_relations
        // is never surfaced without honest attribution.
        if has_rels {
            let rel_packs: Vec<CompactPackSummary> = self
                .list_packs()
                .into_iter()
                .filter(|p| p.has_relations && scope.tier.matches(p.pack_tier))
                .collect();
            for rp in &rel_packs {
                match rp.pack_tier {
                    PackTier::VerifiedOpen => has_verified_open = true,
                    PackTier::LocalHistorical => has_local_historical = true,
                }
                if let Some(first_rel) = rel_res.relations.first() {
                    if seen_sources.insert((rp.pack_id.clone(), first_rel.source_locator.clone())) {
                        sources.push(WordSourceRef {
                            pack_id: rp.pack_id.clone(),
                            category: rp.category,
                            pack_tier: rp.pack_tier,
                            rights_status: rp.rights_status.clone(),
                            source_id: first_rel.source_id.clone(),
                            source_locator: first_rel.source_locator.clone(),
                            permalink: None,
                        });
                    }
                }
            }
        }

        let status = if lookup.total_entries > 0 || has_rels {
            LookupStatus::Matched
        } else {
            LookupStatus::NotFound
        };

        Ok(WordDefinition {
            status,
            query: lookup.query,
            canonical_query: lookup.canonical_query,
            headword,
            folded: lookup.folded,
            searched_packs: lookup.searched_packs,
            categories: categories_set.into_iter().collect(),
            pos: pos_set.into_iter().collect(),
            meanings_en,
            meanings_ta,
            examples: examples_set.into_iter().collect(),
            variants: variants_set.into_iter().collect(),
            domains: domains_set.into_iter().collect(),
            regions: regions_set.into_iter().collect(),
            registers: registers_set.into_iter().collect(),
            standard_equivalents: std_eq_set.into_iter().collect(),
            pure_tamil_equivalents: pure_ta_set.into_iter().collect(),
            origin_languages: origin_set.into_iter().collect(),
            scientific_names: sci_set.into_iter().collect(),
            literary_sources: lit_set.into_iter().collect(),
            matched_headwords: matched_hw_set.into_iter().collect(),
            ipa: ipa_set.into_iter().collect(),
            verb_classes: verb_class_set.into_iter().collect(),
            transitivity: transitivity_set.into_iter().collect(),
            root_words: root_word_set.into_iter().collect(),
            etymology_types: etymology_set.into_iter().collect(),
            dedr_ids: dedr_set.into_iter().collect(),
            sandhi_behaviors: sandhi_set.into_iter().collect(),
            animacy_genders: animacy_set.into_iter().collect(),
            frequency_tiers: freq_set.into_iter().collect(),
            relations: WordRelationsGroup {
                synonyms: syn_set.into_iter().collect(),
                antonyms: ant_set.into_iter().collect(),
                related: rel_set.into_iter().collect(),
                hypernyms: hyp_set.into_iter().collect(),
            },
            has_verified_open,
            has_local_historical,
            entry_count: lookup.total_entries,
            sources,
        })
    }
}

/// Dynamic in-memory registry of loaded `TMLPACK1` and `TMLPACK2` packs.
#[derive(Debug, Default, Clone)]
pub struct PackRegistry {
    packs: BTreeMap<String, LoadedPack>,
}

impl PackRegistry {
    pub fn new() -> Self {
        Self {
            packs: BTreeMap::new(),
        }
    }

    /// Returns the number of currently mounted packs.
    pub fn len(&self) -> usize {
        self.packs.len()
    }

    pub fn is_empty(&self) -> bool {
        self.packs.is_empty()
    }

    /// Validates and mounts a `.tlpack` v1 or v2 image from raw bytes, replacing any prior pack
    /// with the same `pack_id`.
    pub fn load_pack_bytes(
        &mut self,
        bytes: impl Into<Arc<[u8]>>,
    ) -> Result<CompactPackSummary, String> {
        let loaded = LoadedPack::parse_bytes(bytes)?;
        let summary = loaded.summary();
        self.packs.insert(summary.pack_id.clone(), loaded);
        Ok(summary)
    }

    /// Inserts an already-parsed [`LoadedPack`].
    pub fn insert_pack(&mut self, pack: LoadedPack) -> CompactPackSummary {
        let summary = pack.summary();
        self.packs.insert(summary.pack_id.clone(), pack);
        summary
    }

    /// Unmounts a pack by `pack_id`. Returns `true` if it was present.
    pub fn unload_pack(&mut self, pack_id: &str) -> bool {
        self.packs.remove(pack_id).is_some()
    }

    /// Clears all mounted packs.
    pub fn clear(&mut self) {
        self.packs.clear();
    }

    /// Loads one `.tlpack` file from disk.
    #[cfg(feature = "std-fs")]
    pub fn load_pack_file(&mut self, path: &Path) -> Result<CompactPackSummary, String> {
        let bytes = std::fs::read(path)
            .map_err(|err| format!("lexicon: failed to read '{}': {err}", path.display()))?;
        self.load_pack_bytes(bytes)
    }

    /// Recursively loads every `*.tlpack` file under `dir` in deterministic sorted path order.
    #[cfg(feature = "std-fs")]
    pub fn load_pack_dir(&mut self, dir: &Path) -> Result<Vec<CompactPackSummary>, String> {
        self.load_profile_from_dir(dir, LexiconProfile::Full)
    }

    /// Loads `.tlpack` files under `dir` matching the requested [`LexiconProfile`].
    #[cfg(feature = "std-fs")]
    pub fn load_profile_from_dir(
        &mut self,
        dir: &Path,
        profile: LexiconProfile,
    ) -> Result<Vec<CompactPackSummary>, String> {
        if !dir.is_dir() {
            return Err(format!(
                "lexicon: pack directory not found: '{}'",
                dir.display()
            ));
        }
        let mut files = Vec::new();
        collect_tlpack_files(dir, &mut files)?;
        files.sort();
        let mut summaries = Vec::new();
        for file in files {
            let stem = file.file_stem().and_then(|s| s.to_str()).unwrap_or("");
            let in_local_dir = file
                .parent()
                .and_then(|p| p.file_name())
                .and_then(|s| s.to_str())
                .is_some_and(|name| name.eq_ignore_ascii_case("local"));
            if !profile.includes_pack_stem(stem, in_local_dir) {
                continue;
            }
            summaries.push(self.load_pack_file(&file)?);
        }
        Ok(summaries)
    }

    /// Auto-discovers a local `.tlpack` pack directory and loads the requested [`LexiconProfile`].
    #[cfg(feature = "std-fs")]
    pub fn open_default(profile: LexiconProfile) -> Result<(PathBuf, Self), String> {
        let dir = auto_discover_pack_dir().ok_or_else(|| {
            "lexicon: no pack directory found (set TAMIL_LEXICON_DIR or run `just lexicon-build`)"
                .to_owned()
        })?;
        let mut reg = Self::new();
        let loaded = reg.load_profile_from_dir(&dir, profile)?;
        if loaded.is_empty() {
            return Err(format!(
                "lexicon: no packs matching profile '{}' in '{}'",
                profile.as_str(),
                dir.display()
            ));
        }
        Ok((dir, reg))
    }

    fn select_packs(&self, scope: &QueryScope) -> Result<Vec<&LoadedPack>, String> {
        let matches_cat = |pack: &LoadedPack| match scope.category {
            None => true,
            Some(cat) => pack.category() == cat,
        };
        if let Some(requested) = &scope.packs {
            if requested.is_empty() || requested.iter().any(String::is_empty) {
                return Err("lexicon: packs must be a nonempty string array".to_owned());
            }
            let mut ids: Vec<&str> = requested.iter().map(String::as_str).collect();
            ids.sort_unstable();
            ids.dedup();
            let mut out = Vec::with_capacity(ids.len());
            for id in ids {
                let pack = self
                    .packs
                    .get(id)
                    .ok_or_else(|| format!("lexicon: pack unavailable '{id}'"))?;
                if scope.tier.matches(pack.pack_tier()) && matches_cat(pack) {
                    out.push(pack);
                }
            }
            Ok(out)
        } else {
            Ok(self
                .packs
                .values()
                .filter(|pack| scope.tier.matches(pack.pack_tier()) && matches_cat(pack))
                .collect())
        }
    }
}

impl LexiconStore for PackRegistry {
    fn list_packs(&self) -> Vec<CompactPackSummary> {
        self.packs.values().map(LoadedPack::summary).collect()
    }

    fn stats(&self) -> LexiconStoreStats {
        let mut packs = Vec::with_capacity(self.packs.len());
        let mut total_entries: u64 = 0;
        let mut total_senses: u64 = 0;
        let mut total_relations: u64 = 0;
        let mut total_bytes: usize = 0;
        let mut category_counts: BTreeMap<String, u32> = BTreeMap::new();
        let mut pos_counts: BTreeMap<String, u32> = BTreeMap::new();
        let mut domain_counts: BTreeMap<String, u32> = BTreeMap::new();
        let mut region_counts: BTreeMap<String, u32> = BTreeMap::new();
        let mut register_counts: BTreeMap<String, u32> = BTreeMap::new();
        let mut has_english_index = false;

        for pack in self.packs.values() {
            let summary = pack.summary();
            total_entries += u64::from(summary.entry_count);
            total_senses += u64::from(summary.sense_count);
            total_relations += u64::from(summary.relation_count);
            total_bytes += summary.byte_len;
            if summary.has_english_index {
                has_english_index = true;
            }
            let cat_entry = category_counts
                .entry(summary.category.as_str().to_owned())
                .or_insert(0);
            *cat_entry = cat_entry.saturating_add(summary.entry_count);

            if let LoadedPack::V2(view) = pack {
                if let Ok(meta) = view.metadata_ref() {
                    merge_facet_counts(&mut pos_counts, &meta.pos_counts);
                    merge_facet_counts(&mut domain_counts, &meta.domain_counts);
                    merge_facet_counts(&mut region_counts, &meta.region_counts);
                    merge_facet_counts(&mut register_counts, &meta.register_counts);
                }
            }
            packs.push(summary);
        }

        LexiconStoreStats {
            pack_count: packs.len(),
            total_entries,
            total_senses,
            total_relations,
            total_bytes,
            packs,
            category_counts,
            pos_counts,
            domain_counts,
            region_counts,
            register_counts,
            has_english_index,
        }
    }

    fn search_english(
        &self,
        query: &str,
        options: &PrefixSearchOptions,
    ) -> Result<PrefixSearchResult, String> {
        if query.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        if options.limit == 0 || options.limit > MAX_SEARCH_LIMIT {
            return Err(format!(
                "lexicon: search limit must be between 1 and {MAX_SEARCH_LIMIT}"
            ));
        }
        let selected = self.select_packs(&options.scope)?;
        let searched_packs: Vec<String> = selected.iter().map(|p| p.pack_id().to_owned()).collect();
        let canonical_query = query.trim().to_ascii_lowercase();
        if canonical_query.is_empty() {
            return Ok(PrefixSearchResult {
                prefix: query.to_owned(),
                canonical_prefix: canonical_query,
                folded: false,
                searched_packs,
                hits: Vec::new(),
                next_cursor: None,
                has_more: false,
            });
        }

        let query_tokens = extract_english_tokens(&canonical_query);
        let has_post_filter = options.scope.pos.is_some()
            || options.scope.domain.is_some()
            || options.scope.region.is_some()
            || options.scope.register.is_some();
        let max_candidates = if has_post_filter {
            options.limit.saturating_mul(16).clamp(256, 2_000)
        } else {
            options.limit.saturating_mul(6).clamp(64, 800)
        };

        struct EnAgg {
            best_score: u8,
            best_tier: PackTier,
            matched_key: String,
            packs: BTreeSet<String>,
            tiers: BTreeSet<PackTier>,
            pos: BTreeSet<String>,
            preview_gloss: Option<String>,
            domain: Option<String>,
            region: Option<String>,
            entry_count: usize,
        }
        let mut by_headword: BTreeMap<String, EnAgg> = BTreeMap::new();

        for pack in selected {
            let candidates = pack.search_english(query, max_candidates)?;
            for entry in candidates {
                if !entry_matches_filter(&entry, &options.scope) {
                    continue;
                }
                let (score, best_gloss) =
                    score_english_entry(&entry, &canonical_query, &query_tokens);
                let tier = pack.pack_tier();
                let agg = by_headword
                    .entry(entry.headword.clone())
                    .or_insert_with(|| EnAgg {
                        best_score: score,
                        best_tier: tier,
                        matched_key: canonical_query.clone(),
                        packs: BTreeSet::new(),
                        tiers: BTreeSet::new(),
                        pos: BTreeSet::new(),
                        preview_gloss: best_gloss.clone(),
                        domain: entry.domain.clone(),
                        region: entry.region.clone(),
                        entry_count: 0,
                    });
                if score > agg.best_score || (score == agg.best_score && tier < agg.best_tier) {
                    agg.best_score = score;
                    agg.best_tier = tier;
                    if best_gloss.is_some() {
                        agg.preview_gloss = best_gloss;
                    }
                    if entry.domain.is_some() {
                        agg.domain = entry.domain.clone();
                    }
                    if entry.region.is_some() {
                        agg.region = entry.region.clone();
                    }
                } else if agg.preview_gloss.is_none() {
                    agg.preview_gloss = best_gloss;
                }
                agg.packs.insert(pack.pack_id().to_owned());
                agg.tiers.insert(tier);
                if let Some(p) = &entry.pos {
                    agg.pos.insert(p.clone());
                }
                if agg.domain.is_none() {
                    agg.domain = entry.domain.clone();
                }
                if agg.region.is_none() {
                    agg.region = entry.region.clone();
                }
                agg.entry_count += 1;
            }
        }

        let mut ranked: Vec<(u8, PackTier, PrefixSearchHit)> = by_headword
            .into_iter()
            .map(|(headword, agg)| {
                (
                    agg.best_score,
                    agg.best_tier,
                    PrefixSearchHit {
                        headword,
                        matched_key: agg.matched_key,
                        packs: agg.packs.into_iter().collect(),
                        pack_tiers: agg.tiers.into_iter().collect(),
                        pos: agg.pos.into_iter().collect(),
                        preview_gloss: agg.preview_gloss,
                        domain: agg.domain,
                        region: agg.region,
                        entry_count: agg.entry_count,
                    },
                )
            })
            .collect();

        ranked.sort_by(|a, b| {
            b.0.cmp(&a.0)
                .then_with(|| a.1.cmp(&b.1))
                .then_with(|| a.2.headword.cmp(&b.2.headword))
        });

        let has_more = ranked.len() > options.limit;
        ranked.truncate(options.limit);
        let hits: Vec<PrefixSearchHit> = ranked.into_iter().map(|(_, _, h)| h).collect();

        Ok(PrefixSearchResult {
            prefix: query.to_owned(),
            canonical_prefix: canonical_query,
            folded: false,
            searched_packs,
            hits,
            next_cursor: None,
            has_more,
        })
    }

    fn contains_word(&self, word: &str, scope: &QueryScope) -> bool {
        if word.is_empty() || word.len() > MAX_INPUT_BYTES {
            return false;
        }
        let Ok(selected) = self.select_packs(scope) else {
            return false;
        };
        let key = if scope.folded {
            fold_for_search(word, FoldingProfile::Mayangoli)
        } else {
            normalize_nfc(word)
        };
        selected
            .iter()
            .any(|pack| pack.contains_word(&key, scope.folded))
    }

    fn lookup_compact(
        &self,
        word: &str,
        scope: &QueryScope,
    ) -> Result<CompactLookupResult, String> {
        if word.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        let selected = self.select_packs(scope)?;
        let searched_packs: Vec<String> = selected.iter().map(|p| p.pack_id().to_owned()).collect();
        let canonical_query = if scope.folded {
            fold_for_search(word, FoldingProfile::Mayangoli)
        } else {
            normalize_nfc(word)
        };

        let mut entries = Vec::new();
        for pack in selected {
            let found = pack.lookup_compact(word, scope.folded)?;
            for entry in found {
                if entry_matches_filter(&entry, scope) {
                    entries.push(AnnotatedEntry {
                        pack_id: pack.pack_id().to_owned(),
                        pack_tier: pack.pack_tier(),
                        entry,
                    });
                }
            }
        }
        // Order verified_open before local_historical, then pack_id, then entry_id.
        entries.sort_by(|a, b| {
            (a.pack_tier, &a.pack_id, &a.entry.entry_id).cmp(&(
                b.pack_tier,
                &b.pack_id,
                &b.entry.entry_id,
            ))
        });

        let total_entries = entries.len();
        let status = if total_entries > 0 {
            LookupStatus::Matched
        } else {
            LookupStatus::NotFound
        };
        Ok(CompactLookupResult {
            status,
            query: word.to_owned(),
            canonical_query,
            folded: scope.folded,
            searched_packs,
            total_entries,
            entries,
        })
    }

    fn prefix_search(
        &self,
        prefix: &str,
        options: &PrefixSearchOptions,
    ) -> Result<PrefixSearchResult, String> {
        if prefix.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        if options.limit == 0 || options.limit > MAX_SEARCH_LIMIT {
            return Err(format!(
                "lexicon: search limit must be between 1 and {MAX_SEARCH_LIMIT}"
            ));
        }
        let selected = self.select_packs(&options.scope)?;
        let searched_packs: Vec<String> = selected.iter().map(|p| p.pack_id().to_owned()).collect();
        let canonical_prefix = if options.scope.folded {
            fold_for_search(prefix, FoldingProfile::Mayangoli)
        } else {
            normalize_nfc(prefix)
        };

        // Aggregate across selected packs keyed by canonical entry headword.
        struct Agg {
            matched_key: String,
            packs: BTreeSet<String>,
            tiers: BTreeSet<PackTier>,
            pos: BTreeSet<String>,
            preview_gloss: Option<String>,
            domain: Option<String>,
            region: Option<String>,
            entry_count: usize,
        }
        let mut by_headword: BTreeMap<String, Agg> = BTreeMap::new();
        let has_post_filter = options.scope.pos.is_some()
            || options.scope.domain.is_some()
            || options.scope.region.is_some()
            || options.scope.register.is_some();
        // Use a generous adaptive scan budget when selective post-filters (pos/domain/region/register)
        // are active so late-FST matches are never starved.
        let max_scan = if has_post_filter {
            30_000
        } else {
            options
                .limit
                .saturating_mul(2)
                .clamp(64, MAX_SEARCH_LIMIT * 2)
        };
        let mut any_pack_has_more = false;

        for pack in selected {
            let (raw_hits, pack_more) = pack.prefix_lookup_filtered(
                prefix,
                options.after_key.as_deref(),
                options.limit,
                max_scan,
                options.scope.folded,
                |entry| entry_matches_filter(entry, &options.scope),
            )?;
            if pack_more {
                any_pack_has_more = true;
            }
            for (matched_key, pack_entries) in raw_hits {
                for entry in pack_entries {
                    let agg = by_headword
                        .entry(entry.headword.clone())
                        .or_insert_with(|| Agg {
                            matched_key: matched_key.clone(),
                            packs: BTreeSet::new(),
                            tiers: BTreeSet::new(),
                            pos: BTreeSet::new(),
                            preview_gloss: None,
                            domain: None,
                            region: None,
                            entry_count: 0,
                        });
                    agg.packs.insert(pack.pack_id().to_owned());
                    agg.tiers.insert(pack.pack_tier());
                    if let Some(p) = &entry.pos {
                        agg.pos.insert(p.clone());
                    }
                    if agg.preview_gloss.is_none() {
                        agg.preview_gloss = entry.preview_gloss();
                    }
                    if agg.domain.is_none() {
                        agg.domain = entry.domain.clone();
                    }
                    if agg.region.is_none() {
                        agg.region = entry.region.clone();
                    }
                    agg.entry_count += 1;
                }
            }
        }

        let mut hits: Vec<PrefixSearchHit> = by_headword
            .into_iter()
            .map(|(headword, agg)| PrefixSearchHit {
                headword,
                matched_key: agg.matched_key,
                packs: agg.packs.into_iter().collect(),
                pack_tiers: agg.tiers.into_iter().collect(),
                pos: agg.pos.into_iter().collect(),
                preview_gloss: agg.preview_gloss,
                domain: agg.domain,
                region: agg.region,
                entry_count: agg.entry_count,
            })
            .collect();

        // Rank exact match (headword or folded matched_key) first, then ascending headword order.
        hits.sort_by(|a, b| {
            let a_exact = !canonical_prefix.is_empty()
                && (a.headword == canonical_prefix || a.matched_key == canonical_prefix);
            let b_exact = !canonical_prefix.is_empty()
                && (b.headword == canonical_prefix || b.matched_key == canonical_prefix);
            b_exact
                .cmp(&a_exact)
                .then_with(|| a.headword.cmp(&b.headword))
        });
        let truncated = hits.len() > options.limit;
        hits.truncate(options.limit);
        let has_more = truncated || any_pack_has_more;
        let next_cursor = if has_more {
            hits.last().map(|h| h.matched_key.clone())
        } else {
            None
        };

        Ok(PrefixSearchResult {
            prefix: prefix.to_owned(),
            canonical_prefix,
            folded: options.scope.folded,
            searched_packs,
            hits,
            next_cursor,
            has_more,
        })
    }

    fn lookup_relations(&self, word: &str, scope: &QueryScope) -> Result<RelationsResult, String> {
        if word.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        let selected = self.select_packs(scope)?;
        let searched_packs: Vec<String> = selected.iter().map(|p| p.pack_id().to_owned()).collect();
        let canonical_query = if scope.folded {
            fold_for_search(word, FoldingProfile::Mayangoli)
        } else {
            normalize_nfc(word)
        };
        let mut target_keys: BTreeSet<String> = BTreeSet::new();
        target_keys.insert(normalize_nfc(word));
        if scope.folded {
            if let Ok(folded_lookup) = self.lookup_compact(word, scope) {
                for ann in folded_lookup.entries {
                    target_keys.insert(ann.entry.headword);
                }
            }
        }
        let mut relations = Vec::new();
        for pack in selected {
            for key in &target_keys {
                relations.extend(pack.lookup_relations(key)?);
            }
        }
        relations.sort();
        let mut seen_triples: BTreeSet<(String, String, String)> = BTreeSet::new();
        relations.retain(|r| {
            r.source_headword != r.target_headword
                && seen_triples.insert((
                    r.source_headword.clone(),
                    r.target_headword.clone(),
                    r.relation_code.clone(),
                ))
        });
        let status = if relations.is_empty() {
            LookupStatus::NotFound
        } else {
            LookupStatus::Matched
        };
        Ok(RelationsResult {
            status,
            query: word.to_owned(),
            canonical_query,
            searched_packs,
            relations,
        })
    }

    fn fuzzy_search(
        &self,
        word: &str,
        max_distance: u32,
        options: &PrefixSearchOptions,
    ) -> Result<FuzzySearchResult, String> {
        if word.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        if options.limit == 0 || options.limit > MAX_SEARCH_LIMIT {
            return Err(format!(
                "lexicon: search limit must be between 1 and {MAX_SEARCH_LIMIT}"
            ));
        }
        let clamped_dist = max_distance.clamp(1, 2);
        let selected = self.select_packs(&options.scope)?;
        let searched_packs: Vec<String> = selected.iter().map(|p| p.pack_id().to_owned()).collect();
        let canonical_query = normalize_nfc(word);

        struct FuzzyAgg {
            distance: u32,
            packs: BTreeSet<String>,
            tiers: BTreeSet<PackTier>,
            pos: BTreeSet<String>,
            preview_gloss: Option<String>,
        }
        let mut by_headword: BTreeMap<String, FuzzyAgg> = BTreeMap::new();
        for pack in selected {
            let raw = pack.fuzzy_lookup(word, clamped_dist, options.limit)?;
            for (_key, dist, entries) in raw {
                for entry in entries {
                    if !entry_matches_filter(&entry, &options.scope) {
                        continue;
                    }
                    let agg = by_headword
                        .entry(entry.headword.clone())
                        .or_insert_with(|| FuzzyAgg {
                            distance: dist,
                            packs: BTreeSet::new(),
                            tiers: BTreeSet::new(),
                            pos: BTreeSet::new(),
                            preview_gloss: None,
                        });
                    if dist < agg.distance {
                        agg.distance = dist;
                    }
                    agg.packs.insert(pack.pack_id().to_owned());
                    agg.tiers.insert(pack.pack_tier());
                    if let Some(p) = &entry.pos {
                        agg.pos.insert(p.clone());
                    }
                    if agg.preview_gloss.is_none() {
                        agg.preview_gloss = entry.preview_gloss();
                    }
                }
            }
        }

        let mut hits: Vec<FuzzySearchHit> = by_headword
            .into_iter()
            .map(|(headword, agg)| FuzzySearchHit {
                headword,
                distance: agg.distance,
                packs: agg.packs.into_iter().collect(),
                pack_tiers: agg.tiers.into_iter().collect(),
                pos: agg.pos.into_iter().collect(),
                preview_gloss: agg.preview_gloss,
            })
            .collect();
        hits.sort_by(|a, b| {
            a.distance
                .cmp(&b.distance)
                .then_with(|| a.headword.cmp(&b.headword))
        });
        hits.truncate(options.limit);

        Ok(FuzzySearchResult {
            query: word.to_owned(),
            canonical_query,
            max_distance: clamped_dist,
            searched_packs,
            hits,
        })
    }

    fn longest_prefix_matches(
        &self,
        word: &str,
        scope: &QueryScope,
    ) -> Result<Vec<String>, String> {
        if word.len() > MAX_INPUT_BYTES {
            return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
        }
        let selected = self.select_packs(scope)?;
        let mut all: BTreeSet<String> = BTreeSet::new();
        for pack in selected {
            for pfx in pack.longest_prefix_matches(word)? {
                all.insert(pfx);
            }
        }
        let mut out: Vec<String> = all.into_iter().collect();
        out.sort_by(|a, b| b.len().cmp(&a.len()).then_with(|| a.cmp(b)));
        Ok(out)
    }
}

/// Normalizes an English gloss for deduplication by lowercasing and stripping leading
/// parenthetical transitivity/register notes (e.g. `"(transitive) to drill"` -> `"to drill"`).
fn normalize_en_dedup_key(raw: &str) -> String {
    let mut s = raw.trim();
    while s.starts_with('(') {
        let Some(end) = s.find(')') else { break };
        let rest = s[end + 1..].trim_start();
        if rest.is_empty() {
            break;
        }
        s = rest;
    }
    s.to_ascii_lowercase()
}

fn merge_facet_counts(dst: &mut BTreeMap<String, u32>, src: &BTreeMap<String, u32>) {
    for (k, &v) in src {
        let entry = dst.entry(k.clone()).or_insert(0);
        *entry = entry.saturating_add(v);
    }
}

fn contains_whole_phrase(haystack_lower: &str, needle_lower: &str) -> bool {
    if needle_lower.is_empty() || haystack_lower.len() < needle_lower.len() {
        return false;
    }
    let bytes = haystack_lower.as_bytes();
    let mut start = 0usize;
    while let Some(rel) = haystack_lower[start..].find(needle_lower) {
        let idx = start + rel;
        let end = idx + needle_lower.len();
        let left_ok = idx == 0 || !bytes[idx - 1].is_ascii_alphanumeric();
        let right_ok = end == bytes.len() || !bytes[end].is_ascii_alphanumeric();
        if left_ok && right_ok {
            return true;
        }
        start = idx + 1;
        while start < bytes.len() && !haystack_lower.is_char_boundary(start) {
            start += 1;
        }
    }
    false
}

fn has_prefix_word(haystack_lower: &str, needle_lower: &str) -> bool {
    if needle_lower.is_empty() {
        return false;
    }
    haystack_lower
        .split(|c: char| !c.is_ascii_alphanumeric())
        .any(|w| w.starts_with(needle_lower))
}

fn score_english_entry(
    entry: &CompactEntry,
    query_lower: &str,
    query_tokens: &[String],
) -> (u8, Option<String>) {
    let mut best_score = 0u8;
    let mut best_gloss: Option<String> = None;

    for sense in &entry.senses {
        if let Some(g) = sense
            .gloss_en
            .as_deref()
            .map(str::trim)
            .filter(|s| !s.is_empty())
        {
            let g_lower = g.to_ascii_lowercase();
            let score = if g_lower == query_lower {
                4
            } else if contains_whole_phrase(&g_lower, query_lower)
                || (!query_tokens.is_empty()
                    && query_tokens
                        .iter()
                        .all(|t| contains_whole_phrase(&g_lower, t)))
            {
                3
            } else if has_prefix_word(&g_lower, query_lower)
                || (!query_tokens.is_empty()
                    && query_tokens.iter().all(|t| has_prefix_word(&g_lower, t)))
            {
                2
            } else {
                0
            };
            if score > best_score {
                best_score = score;
                best_gloss = Some(g.to_owned());
            }
        }
        if best_score < 2 {
            if let Some(d) = sense
                .definition_en
                .as_deref()
                .map(str::trim)
                .filter(|s| !s.is_empty())
            {
                let d_lower = d.to_ascii_lowercase();
                let matched = contains_whole_phrase(&d_lower, query_lower)
                    || has_prefix_word(&d_lower, query_lower)
                    || (!query_tokens.is_empty()
                        && query_tokens.iter().all(|t| has_prefix_word(&d_lower, t)));
                if matched && 1 > best_score {
                    best_score = 1;
                    best_gloss = sense
                        .gloss_en
                        .as_deref()
                        .map(str::trim)
                        .filter(|s| !s.is_empty())
                        .map(str::to_owned)
                        .or_else(|| Some(d.to_owned()));
                }
            }
        }
    }

    if best_score == 0 {
        if let Some(sci) = entry
            .scientific_name
            .as_deref()
            .map(str::trim)
            .filter(|s| !s.is_empty())
        {
            let s_lower = sci.to_ascii_lowercase();
            if contains_whole_phrase(&s_lower, query_lower)
                || has_prefix_word(&s_lower, query_lower)
                || (!query_tokens.is_empty()
                    && query_tokens.iter().all(|t| has_prefix_word(&s_lower, t)))
            {
                best_score = 1;
                best_gloss = entry.preview_gloss().or_else(|| Some(sci.to_owned()));
            }
        }
    }

    (best_score, best_gloss.or_else(|| entry.preview_gloss()))
}

fn field_has_facet_token(raw: &str, target: &str) -> bool {
    split_facet_tokens(raw)
        .iter()
        .any(|tok| tok.eq_ignore_ascii_case(target))
}

/// Returns `true` if `entry` matches all active facet filters in `scope`.
pub fn entry_matches_filter(entry: &CompactEntry, scope: &QueryScope) -> bool {
    if let Some(pos) = scope.pos.as_deref() {
        let matched = entry
            .pos
            .as_deref()
            .is_some_and(|p| p.eq_ignore_ascii_case(pos));
        if !matched {
            return false;
        }
    }
    if let Some(domain) = scope.domain.as_deref() {
        let entry_match = entry
            .domain
            .as_deref()
            .is_some_and(|d| field_has_facet_token(d, domain));
        let sense_match = entry.senses.iter().any(|s| {
            s.domain
                .as_deref()
                .is_some_and(|d| field_has_facet_token(d, domain))
        });
        if !entry_match && !sense_match {
            return false;
        }
    }
    if let Some(region) = scope.region.as_deref() {
        let entry_match = entry
            .region
            .as_deref()
            .is_some_and(|r| field_has_facet_token(r, region));
        let sense_match = entry.senses.iter().any(|s| {
            s.region
                .as_deref()
                .is_some_and(|r| field_has_facet_token(r, region))
        });
        if !entry_match && !sense_match {
            return false;
        }
    }
    if let Some(register) = scope.register.as_deref() {
        let entry_match = entry
            .register
            .as_deref()
            .is_some_and(|r| field_has_facet_token(r, register));
        let sense_match = entry.senses.iter().any(|s| {
            s.register
                .as_deref()
                .is_some_and(|r| field_has_facet_token(r, register))
        });
        if !entry_match && !sense_match {
            return false;
        }
    }
    true
}

fn v1_entry_to_compact(entry: &CompiledEntry) -> CompactEntry {
    let pos = if entry.part_of_speech.availability == "available" {
        entry.part_of_speech.value.clone()
    } else {
        None
    };
    let forms = entry
        .forms
        .iter()
        .filter(|f| f.text != entry.headword)
        .map(|f| CompactForm {
            role: f.role.clone(),
            text: f.text.clone(),
        })
        .collect();
    let senses = entry
        .senses
        .iter()
        .map(|s| {
            let mut gloss_en = None;
            let mut gloss_ta = None;
            for comp in &s.components {
                if comp.language_id == "eng" && gloss_en.is_none() {
                    gloss_en = Some(comp.text.clone());
                } else if comp.language_id == "tam" && gloss_ta.is_none() {
                    gloss_ta = Some(comp.text.clone());
                }
            }
            let examples = s.examples.iter().map(|e| e.text.clone()).collect();
            let region = if s.region.state == "attested" {
                s.region.codes.first().cloned()
            } else {
                None
            };
            let register = if s.register.availability == "available" {
                s.register.value.clone()
            } else {
                None
            };
            CompactSense {
                gloss_ta,
                gloss_en,
                definition_ta: None,
                definition_en: None,
                examples,
                domain: None,
                region,
                register,
            }
        })
        .collect();
    let region = if entry.region.state == "attested" {
        entry.region.codes.first().cloned()
    } else {
        None
    };
    let register = if entry.register.availability == "available" {
        entry.register.value.clone()
    } else {
        None
    };
    let first_prov = entry.provenance.first();
    CompactEntry {
        entry_id: entry.entry_id.clone(),
        headword: entry.headword.clone(),
        pos,
        forms,
        senses,
        domain: None,
        region,
        register,
        origin_language: None,
        pure_tamil_equivalent: None,
        standard_equivalent: None,
        scientific_name: None,
        literary_source: None,
        source_id: first_prov
            .map(|p| p.source_id.clone())
            .unwrap_or_else(|| "en.wiktionary.org".to_owned()),
        source_locator: first_prov.map(|p| p.locator.clone()).unwrap_or_default(),
        rights_status: "CC-BY-SA-4.0".to_owned(),
        permalink: None,
        ..Default::default()
    }
}

/// Searches standard locations for a directory containing `.tlpack` files:
/// 1. `TAMIL_LEXICON_DIR` environment variable
/// 2. `./dist/lexicon-packs` and `./lexicon-packs` (walking up to 3 parent directories)
/// 3. `~/.tamil-toolkit/lexicon-packs`
#[cfg(feature = "std-fs")]
pub fn auto_discover_pack_dir() -> Option<PathBuf> {
    if let Ok(env_dir) = std::env::var("TAMIL_LEXICON_DIR") {
        let trimmed = env_dir.trim();
        if !trimmed.is_empty() {
            let p = PathBuf::from(trimmed);
            if dir_has_tlpack(&p) {
                return Some(p);
            }
        }
    }
    if let Ok(cwd) = std::env::current_dir() {
        let mut cur: Option<&Path> = Some(cwd.as_path());
        for _ in 0..4 {
            let Some(base) = cur else { break };
            for rel in ["dist/lexicon-packs", "lexicon-packs"] {
                let cand = base.join(rel);
                if dir_has_tlpack(&cand) {
                    return Some(cand);
                }
            }
            cur = base.parent();
        }
    }
    for home_var in ["HOME", "USERPROFILE"] {
        if let Ok(home) = std::env::var(home_var) {
            let cand = PathBuf::from(home)
                .join(".tamil-toolkit")
                .join("lexicon-packs");
            if dir_has_tlpack(&cand) {
                return Some(cand);
            }
        }
    }
    None
}

#[cfg(feature = "std-fs")]
fn dir_has_tlpack(dir: &Path) -> bool {
    if !dir.is_dir() {
        return false;
    }
    let mut files = Vec::new();
    collect_tlpack_files(dir, &mut files).is_ok() && !files.is_empty()
}

#[cfg(feature = "std-fs")]
fn collect_tlpack_files(dir: &Path, out: &mut Vec<std::path::PathBuf>) -> Result<(), String> {
    let entries = std::fs::read_dir(dir)
        .map_err(|err| format!("lexicon: failed to read dir '{}': {err}", dir.display()))?;
    for entry in entries {
        let entry = entry.map_err(|err| format!("lexicon: dir entry error: {err}"))?;
        let path = entry.path();
        if path.is_dir() {
            collect_tlpack_files(&path, out)?;
        } else if path.extension().and_then(|s| s.to_str()) == Some("tlpack") {
            out.push(path);
        }
    }
    Ok(())
}
