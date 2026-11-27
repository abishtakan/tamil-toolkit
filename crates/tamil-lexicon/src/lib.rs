//! Pure Apache-2.0 Tamil lexicon runtime pack reader, compact `.tlpack` v2 builder/reader,
//! exact & prefix/folded FST search, and `LexiconStore` trait.
//!
//! `tamil-lexicon` is a **Rank 2** crate depending only on `tamil-core` (Rank 0) and
//! `tamil-norm` (Rank 1). It contains zero `build.rs`, zero `csv`, zero `source_records`,
//! and zero bundled third-party dictionary bytes.
#![forbid(unsafe_code)]

pub mod lookup_v1;
pub mod store;
pub mod v1;
pub mod v2;

pub use lookup_v1::{
    lookup_in_views, validate_request_inputs, LookupRequest, LookupResponse, LookupStatus,
    PackInfo, DEFAULT_PACKS, MAX_INPUT_BYTES, SCHEMA_VERSION,
};
#[cfg(feature = "std-fs")]
pub use store::auto_discover_pack_dir;
pub use store::{
    entry_matches_filter, pack_category, CompactLookupResult, CompactPackSummary, FuzzySearchHit,
    FuzzySearchResult, LexiconCategory, LexiconPrefixSearchResult, LexiconProfile,
    LexiconSearchOptions, LexiconStore, LexiconStoreStats, LoadedPack, PackRegistry,
    PrefixSearchHit, PrefixSearchOptions, PrefixSearchResult, QueryScope, RelationsResult,
    TierFilter, WordDefinition, WordMeaning, WordRelationsGroup, WordSourceRef,
};
pub use v1::{
    CompiledAcceptance, CompiledAnnotation, CompiledCoverage, CompiledEndpoint, CompiledEntry,
    CompiledField, CompiledForm, CompiledLabel, CompiledLabelField, CompiledPackMeta,
    CompiledPackView, CompiledProvenance, CompiledRelation, CompiledScope, CompiledSense,
    CompiledSourceNotice, CompiledText, CompiledVocabRegion, CompiledVocabularies, EntrySlice,
    PackHeader, PostingRange, CHECKSUM_OFFSET, EXPECTED_CANONICAL_FORMAT, EXPECTED_CSV_ENCODING,
    HEADER_SIZE, INDEX_FORMAT_VERSION, KNOWN_PACK_IDS, PACK_FLAG_COMPACT_INTERNED, PACK_MAGIC,
};
pub use v2::{
    build_compact_pack, extract_english_tokens, split_facet_tokens, CompactEntry, CompactForm,
    CompactPackHeader, CompactPackInput, CompactPackMeta, CompactPackView, CompactRelation,
    CompactSense, PackTier, CHECKSUM_OFFSET_V2, HEADER_SIZE_V2, INDEX_FORMAT_VERSION_V2,
    PACK_MAGIC_V2, SCHEMA_VERSION_V2, V2_FLAG_DEFLATE_BLOCKS, V2_FLAG_HAS_ENGLISH_INDEX,
    V2_FLAG_HAS_FOLDED_INDEX, V2_FLAG_HAS_RELATIONS,
};
