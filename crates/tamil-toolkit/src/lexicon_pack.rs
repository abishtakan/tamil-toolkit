//! Offline compiled lexicon pack binary format, safe reader, and profile metadata.
//!
//! This module exposes only compile-time generated pack artifacts and checked
//! container accessors for downstream runtime lookup implementations. It does
//! not register public dispatcher operations or perform query filtering.

use std::collections::BTreeMap;
use std::sync::{Arc, OnceLock};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Magic header identifying the compiled binary lexicon pack format v1.
pub const PACK_MAGIC: [u8; 8] = *b"TMLPACK1";

/// Fixed byte length of the binary `.tlpack` header in little-endian layout.
pub const HEADER_SIZE: usize = 160;

/// Byte offset of the embedded 32-byte SHA-256 content checksum in the header.
pub const CHECKSUM_OFFSET: usize = 128;

/// Compiled FST/posting index format version implemented by this build.
pub const INDEX_FORMAT_VERSION: u32 = 1;

/// Canonical CSV/TOML pack schema version implemented by this build.
pub const SCHEMA_VERSION: u32 = 1;

/// Pack header flag enabling compact interned binary entry payloads.
pub const PACK_FLAG_COMPACT_INTERNED: u32 = 1;

const COMPACT_POOL_MAGIC: [u8; 8] = *b"TMLPOOL1";
const COMPACT_POOL_HEADER_SIZE: usize = 16;

/// Required canonical layout identifier in `schema.toml`.
pub const EXPECTED_CANONICAL_FORMAT: &str = "tamil-toolkit-canonical-lexicon-v1";

/// Required CSV string cell codec identifier in `schema.toml`.
pub const EXPECTED_CSV_ENCODING: &str = "json-string-utf8-v1";

/// Canonical pack identifiers defined by the lexicon specification.
pub const KNOWN_PACK_IDS: &[&str] = &["core", "terminology", "names_taxa", "regional"];

/// Static metadata describing one approved embedded pack artifact.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EmbeddedPackArtifact {
    pub id: &'static str,
    pub dataset_version: &'static str,
    pub schema_version: u32,
    pub index_format_version: u32,
    pub manifest_sha256: &'static str,
    pub artifact_sha256: &'static str,
    pub bytes: &'static [u8],
}

mod generated {
    use super::EmbeddedPackArtifact;
    include!(concat!(env!("OUT_DIR"), "/lexicon_packs.rs"));
}

/// Returns total embedded binary payload bytes across compiled packs (`0` by default).
pub fn embedded_payload_bytes() -> usize {
    generated::EMBEDDED_PAYLOAD_BYTES
}

/// Returns the pack IDs corresponding to Cargo features enabled at compile time.
pub fn enabled_pack_features() -> &'static [&'static str] {
    generated::ENABLED_PACK_FEATURES
}

/// Returns enabled pack features that currently lack approved packaged data.
pub fn unapproved_enabled_packs() -> &'static [&'static str] {
    generated::UNAPPROVED_ENABLED_PACKS
}

/// Returns approved packs whose compiled bytes are embedded in this binary.
pub fn available_packs() -> &'static [EmbeddedPackArtifact] {
    generated::AVAILABLE_PACKS
}

/// Opens an approved compiled pack, validating its immutable embedded bytes once.
///
/// Unknown pack IDs and disabled or unapproved pack IDs yield distinct contract errors.
pub fn open_available_pack(pack_id: &str) -> Result<CompiledPackView<'static>, String> {
    if !KNOWN_PACK_IDS.contains(&pack_id) {
        return Err(format!("lexicon: unknown pack '{pack_id}'"));
    }
    let Some((index, artifact)) = available_packs()
        .iter()
        .enumerate()
        .find(|(_, pack)| pack.id == pack_id)
    else {
        return Err(format!("lexicon: pack unavailable '{pack_id}'"));
    };
    type CachedView = OnceLock<Result<CompiledPackView<'static>, String>>;
    static VIEWS: OnceLock<Vec<CachedView>> = OnceLock::new();
    let views = VIEWS.get_or_init(|| available_packs().iter().map(|_| OnceLock::new()).collect());
    views[index]
        .get_or_init(|| CompiledPackView::parse(artifact.bytes))
        .clone()
}

/// Fixed-width little-endian binary header of a compiled `.tlpack` file.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PackHeader {
    pub index_format_version: u32,
    pub schema_version: u32,
    pub flags: u32,
    pub key_count: u32,
    pub posting_count: u32,
    pub entry_count: u32,
    pub fst_offset: u64,
    pub fst_len: u64,
    pub ranges_offset: u64,
    pub ranges_len: u64,
    pub postings_offset: u64,
    pub postings_len: u64,
    pub entry_index_offset: u64,
    pub entry_index_len: u64,
    pub payload_offset: u64,
    pub payload_len: u64,
    pub metadata_offset: u64,
    pub metadata_len: u64,
    pub checksum_sha256: [u8; 32],
}

/// Fixed-width 8-byte little-endian posting list slice for one FST key ordinal.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PostingRange {
    pub start: u32,
    pub count: u32,
}

/// Fixed-width 16-byte little-endian entry payload slice relative to payload start.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EntrySlice {
    pub offset: u64,
    pub len: u64,
}

/// Pack coverage summary stored in compiled pack metadata.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledCoverage {
    pub language_ids: Vec<String>,
    pub region_codes: Vec<String>,
    pub register_codes: Vec<String>,
    pub unknown_region_entries: u64,
}

/// Controlled geographic region entry declared in `vocabularies.toml`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledVocabRegion {
    pub code: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_code: Option<String>,
}

/// Finite approved vocabularies declared in `vocabularies.toml`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledVocabularies {
    pub vocabulary_version: String,
    pub language_ids: Vec<String>,
    pub parts_of_speech: Vec<String>,
    pub relation_codes: Vec<String>,
    pub annotation_properties: Vec<String>,
    pub registers: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub domains: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub temporals: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub varieties: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub regions: Vec<CompiledVocabRegion>,
}

/// Controlled scope/label registry entry compiled from `labels.csv`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledLabel {
    pub registry_id: String,
    pub registry_version: String,
    pub code: String,
    pub category: String,
    pub display_label: String,
    pub definition: String,
    pub evidence_reference: String,
    pub parent_code: Option<String>,
}

/// Verified public source attribution summary compiled from `sources.csv`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledSourceNotice {
    pub source_id: String,
    pub label: String,
    pub url: Option<String>,
    pub reuse_basis: String,
    pub attribution_text: String,
    pub attribution_reference: String,
}

/// Reproducible pack metadata serialized in the `.tlpack` metadata section.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledPackMeta {
    pub pack_id: String,
    pub dataset_version: String,
    pub description: String,
    pub schema_version: u32,
    pub vocabulary_version: String,
    pub index_format_version: u32,
    pub manifest_sha256: String,
    pub entry_count: u32,
    pub sense_count: u32,
    pub form_count: u32,
    pub text_count: u32,
    pub relation_count: u32,
    pub assertion_count: u32,
    pub omitted_relation_count: u32,
    pub coverage: CompiledCoverage,
    pub entry_revisions: BTreeMap<String, String>,
    pub vocabularies: CompiledVocabularies,
    pub labels: Vec<CompiledLabel>,
    pub sources: Vec<CompiledSourceNotice>,
}

/// Acceptance record matching `lookup-response.schema.json#/$defs/Acceptance`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledAcceptance {
    pub decision_id: String,
    pub kind: String,
    pub actor_id: Option<String>,
    pub method: Option<String>,
    pub decided_on: String,
}

/// Provenance record matching `lookup-response.schema.json#/$defs/Provenance`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledProvenance {
    pub assertion_id: String,
    pub revision_sha256: String,
    pub source_id: String,
    pub locator: String,
    pub acceptance: CompiledAcceptance,
}

/// Scope record matching `lookup-response.schema.json#/$defs/Scope`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledScope {
    pub state: String,
    pub codes: Vec<String>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Field record matching `lookup-response.schema.json#/$defs/Field`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledField {
    pub availability: String,
    pub value: Option<serde_json::Value>,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Label field record matching `lookup-response.schema.json#/$defs/LabelField`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledLabelField {
    pub availability: String,
    pub value: Option<String>,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Annotation record matching `lookup-response.schema.json#/$defs/Annotation`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledAnnotation {
    pub property: String,
    pub field: CompiledField,
}

/// Form record matching `lookup-response.schema.json#/$defs/Form`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledForm {
    pub form_id: String,
    pub representation: String,
    pub role: String,
    pub text: String,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Text record matching `lookup-response.schema.json#/$defs/Text`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledText {
    pub text_id: String,
    pub kind: String,
    pub language_id: String,
    pub text: String,
    pub provenance: Vec<CompiledProvenance>,
}

/// Relation endpoint matching `lookup-response.schema.json#/$defs/Endpoint`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledEndpoint {
    pub kind: String,
    pub id: String,
}

/// Relation record matching `lookup-response.schema.json#/$defs/Relation`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledRelation {
    pub relation_id: String,
    pub code: String,
    pub directionality: String,
    pub source: CompiledEndpoint,
    pub target: CompiledEndpoint,
    pub provenance: Vec<CompiledProvenance>,
}

/// Sense record matching `lookup-response.schema.json#/$defs/Sense`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledSense {
    pub sense_id: String,
    pub display_order: u32,
    pub parent_sense_id: Option<String>,
    pub components: Vec<CompiledText>,
    pub examples: Vec<CompiledText>,
    pub relations: Vec<CompiledRelation>,
    pub region: CompiledScope,
    pub register: CompiledLabelField,
    pub annotations: Vec<CompiledAnnotation>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Compiled entry payload matching `lookup-response.schema.json#/$defs/Entry`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CompiledEntry {
    pub entry_id: String,
    pub revision: String,
    pub headword: String,
    pub language_id: String,
    pub part_of_speech: CompiledLabelField,
    pub forms: Vec<CompiledForm>,
    pub senses: Vec<CompiledSense>,
    pub region: CompiledScope,
    pub register: CompiledLabelField,
    pub annotations: Vec<CompiledAnnotation>,
    pub provenance: Vec<CompiledProvenance>,
}

/// Reads an unsigned 32-bit little-endian integer with bounds checking.
pub fn read_u32_le(bytes: &[u8], offset: usize) -> Result<u32, String> {
    let end = offset
        .checked_add(4)
        .ok_or_else(|| "pack header: u32 offset overflow".to_owned())?;
    let slice = bytes
        .get(offset..end)
        .ok_or_else(|| format!("pack header: truncated u32 at byte {offset}"))?;
    let arr: [u8; 4] = slice
        .try_into()
        .map_err(|_| format!("pack header: invalid u32 width at byte {offset}"))?;
    Ok(u32::from_le_bytes(arr))
}

/// Reads an unsigned 64-bit little-endian integer with bounds checking.
pub fn read_u64_le(bytes: &[u8], offset: usize) -> Result<u64, String> {
    let end = offset
        .checked_add(8)
        .ok_or_else(|| "pack header: u64 offset overflow".to_owned())?;
    let slice = bytes
        .get(offset..end)
        .ok_or_else(|| format!("pack header: truncated u64 at byte {offset}"))?;
    let arr: [u8; 8] = slice
        .try_into()
        .map_err(|_| format!("pack header: invalid u64 width at byte {offset}"))?;
    Ok(u64::from_le_bytes(arr))
}

/// Encodes one fixed-width 8-byte little-endian posting range (`start`, `count`).
pub fn encode_posting_range_le(range: PostingRange) -> [u8; 8] {
    let mut out = [0u8; 8];
    out[0..4].copy_from_slice(&range.start.to_le_bytes());
    out[4..8].copy_from_slice(&range.count.to_le_bytes());
    out
}

/// Decodes and validates a posting range against total posting count.
pub fn decode_posting_range_le(
    bytes: &[u8],
    offset: usize,
    posting_count: u32,
) -> Result<PostingRange, String> {
    let start = read_u32_le(bytes, offset)?;
    let count = read_u32_le(bytes, offset.checked_add(4).ok_or("range offset overflow")?)?;
    if count == 0 {
        return Err("pack posting range: count must be positive".to_owned());
    }
    let end = start
        .checked_add(count)
        .ok_or_else(|| "pack posting range: start + count overflow".to_owned())?;
    if end > posting_count {
        return Err(format!(
            "pack posting range: end {end} exceeds posting_count {posting_count}"
        ));
    }
    Ok(PostingRange { start, count })
}

/// Encodes one fixed-width 16-byte little-endian entry slice (`offset`, `len`).
pub fn encode_entry_slice_le(slice: EntrySlice) -> [u8; 16] {
    let mut out = [0u8; 16];
    out[0..8].copy_from_slice(&slice.offset.to_le_bytes());
    out[8..16].copy_from_slice(&slice.len.to_le_bytes());
    out
}

/// Decodes and validates an entry payload slice against `payload_len`.
pub fn decode_entry_slice_le(
    bytes: &[u8],
    offset: usize,
    payload_len: u64,
) -> Result<EntrySlice, String> {
    let item_offset = read_u64_le(bytes, offset)?;
    let item_len = read_u64_le(
        bytes,
        offset.checked_add(8).ok_or("entry slice offset overflow")?,
    )?;
    if item_len == 0 {
        return Err("pack entry slice: length must be positive".to_owned());
    }
    let end = item_offset
        .checked_add(item_len)
        .ok_or_else(|| "pack entry slice: offset + len overflow".to_owned())?;
    if end > payload_len {
        return Err(format!(
            "pack entry slice: end {end} exceeds payload_len {payload_len}"
        ));
    }
    Ok(EntrySlice {
        offset: item_offset,
        len: item_len,
    })
}

#[derive(Debug, Clone, Copy)]
struct CompactStrSpan {
    offset: usize,
    len: usize,
}

#[derive(Debug, Clone, Copy)]
struct CompactAcceptanceRef {
    decision_id: u32,
    kind: u32,
    actor_id: Option<u32>,
    method: Option<u32>,
    decided_on: u32,
}

#[derive(Debug, Clone, Copy)]
struct CompactProvenanceRef {
    assertion_id: u32,
    revision_sha256: u32,
    source_id: u32,
    locator: u32,
    acceptance_idx: u32,
}

#[derive(Debug)]
struct CompactPools {
    entries_base: u64,
    strings: Vec<CompactStrSpan>,
    acceptances: Vec<CompactAcceptanceRef>,
    provenances: Vec<CompactProvenanceRef>,
}

impl CompactPools {
    fn str_at<'a>(&self, payload: &'a [u8], idx: u32) -> Result<&'a str, String> {
        let span = self
            .strings
            .get(idx as usize)
            .ok_or_else(|| format!("pack string pool: index {idx} out of bounds"))?;
        let end = span
            .offset
            .checked_add(span.len)
            .ok_or_else(|| "pack string pool: span overflow".to_owned())?;
        let slice = payload
            .get(span.offset..end)
            .ok_or_else(|| "pack string pool: span out of bounds".to_owned())?;
        std::str::from_utf8(slice).map_err(|err| format!("pack string pool: invalid utf-8: {err}"))
    }

    fn string_owned(&self, payload: &[u8], idx: u32) -> Result<String, String> {
        self.str_at(payload, idx).map(str::to_owned)
    }

    fn opt_string(&self, payload: &[u8], raw_idx: u32) -> Result<Option<String>, String> {
        if raw_idx == 0 {
            Ok(None)
        } else {
            self.string_owned(payload, raw_idx - 1).map(Some)
        }
    }

    fn provenance(&self, payload: &[u8], idx: u32) -> Result<CompiledProvenance, String> {
        let p = self
            .provenances
            .get(idx as usize)
            .ok_or_else(|| format!("pack provenance pool: index {idx} out of bounds"))?;
        let acc = self
            .acceptances
            .get(p.acceptance_idx as usize)
            .ok_or_else(|| {
                format!(
                    "pack acceptance pool: index {} out of bounds",
                    p.acceptance_idx
                )
            })?;
        Ok(CompiledProvenance {
            assertion_id: self.string_owned(payload, p.assertion_id)?,
            revision_sha256: self.string_owned(payload, p.revision_sha256)?,
            source_id: self.string_owned(payload, p.source_id)?,
            locator: self.string_owned(payload, p.locator)?,
            acceptance: CompiledAcceptance {
                decision_id: self.string_owned(payload, acc.decision_id)?,
                kind: self.string_owned(payload, acc.kind)?,
                actor_id: acc
                    .actor_id
                    .map(|id| self.string_owned(payload, id))
                    .transpose()?,
                method: acc
                    .method
                    .map(|id| self.string_owned(payload, id))
                    .transpose()?,
                decided_on: self.string_owned(payload, acc.decided_on)?,
            },
        })
    }
}

/// Safe borrowed view over an in-memory `.tlpack` binary image.
#[derive(Debug, Clone)]
pub struct CompiledPackView<'a> {
    bytes: &'a [u8],
    header: PackHeader,
    compact_pools: Option<Arc<CompactPools>>,
    meta_cache: Arc<OnceLock<CompiledPackMeta>>,
}

impl<'a> CompiledPackView<'a> {
    /// Parses and cryptographically/structurally validates a compiled pack image.
    pub fn parse(bytes: &'a [u8]) -> Result<Self, String> {
        if bytes.len() < HEADER_SIZE {
            return Err(format!(
                "pack binary: length {} is smaller than header size {}",
                bytes.len(),
                HEADER_SIZE
            ));
        }
        if bytes.get(0..8) != Some(&PACK_MAGIC) {
            return Err("pack binary: invalid magic header".to_owned());
        }
        let index_format_version = read_u32_le(bytes, 8)?;
        if index_format_version != INDEX_FORMAT_VERSION {
            return Err(format!(
                "pack binary: unsupported index_format_version {index_format_version}"
            ));
        }
        let schema_version = read_u32_le(bytes, 12)?;
        if schema_version != SCHEMA_VERSION {
            return Err(format!(
                "pack binary: unsupported schema_version {schema_version}"
            ));
        }
        let flags = read_u32_le(bytes, 16)?;
        if flags & !PACK_FLAG_COMPACT_INTERNED != 0 {
            return Err(format!("pack binary: unsupported flags {flags}"));
        }

        let key_count = read_u32_le(bytes, 20)?;
        let posting_count = read_u32_le(bytes, 24)?;
        let entry_count = read_u32_le(bytes, 28)?;
        let fst_offset = read_u64_le(bytes, 32)?;
        let fst_len = read_u64_le(bytes, 40)?;
        let ranges_offset = read_u64_le(bytes, 48)?;
        let ranges_len = read_u64_le(bytes, 56)?;
        let postings_offset = read_u64_le(bytes, 64)?;
        let postings_len = read_u64_le(bytes, 72)?;
        let entry_index_offset = read_u64_le(bytes, 80)?;
        let entry_index_len = read_u64_le(bytes, 88)?;
        let payload_offset = read_u64_le(bytes, 96)?;
        let payload_len = read_u64_le(bytes, 104)?;
        let metadata_offset = read_u64_le(bytes, 112)?;
        let metadata_len = read_u64_le(bytes, 120)?;

        let checksum_slice = bytes
            .get(CHECKSUM_OFFSET..HEADER_SIZE)
            .ok_or_else(|| "pack header: truncated checksum".to_owned())?;
        let checksum_sha256: [u8; 32] = checksum_slice
            .try_into()
            .map_err(|_| "pack header: invalid checksum width".to_owned())?;

        let header = PackHeader {
            index_format_version,
            schema_version,
            flags,
            key_count,
            posting_count,
            entry_count,
            fst_offset,
            fst_len,
            ranges_offset,
            ranges_len,
            postings_offset,
            postings_len,
            entry_index_offset,
            entry_index_len,
            payload_offset,
            payload_len,
            metadata_offset,
            metadata_len,
            checksum_sha256,
        };

        validate_header_layout(&header, bytes.len())?;
        verify_checksum(bytes, &header.checksum_sha256)?;

        let compact_pools = if flags & PACK_FLAG_COMPACT_INTERNED != 0 {
            let payload = section_slice(bytes, header.payload_offset, header.payload_len)?;
            Some(Arc::new(parse_compact_pools(payload)?))
        } else {
            None
        };

        let view = Self {
            bytes,
            header,
            compact_pools,
            meta_cache: Arc::new(OnceLock::new()),
        };
        view.validate_sections()?;
        Ok(view)
    }

    /// Returns the parsed little-endian header.
    pub fn header(&self) -> &PackHeader {
        &self.header
    }

    /// Returns the borrowed FST bytes section.
    pub fn fst_bytes(&self) -> &'a [u8] {
        section_slice(self.bytes, self.header.fst_offset, self.header.fst_len)
            .expect("validated header fst section")
    }

    /// Opens the safe borrowed `fst::Map` over the FST section.
    pub fn fst_map(&self) -> Result<fst::Map<&'a [u8]>, String> {
        fst::Map::new(self.fst_bytes()).map_err(|err| format!("pack fst: {err}"))
    }

    /// Returns the posting range `(start, count)` for FST key ordinal `ordinal`.
    pub fn posting_range(&self, ordinal: u64) -> Result<PostingRange, String> {
        if ordinal >= u64::from(self.header.key_count) {
            return Err(format!(
                "pack posting range: ordinal {ordinal} out of bounds ({})",
                self.header.key_count
            ));
        }
        let ranges = section_slice(
            self.bytes,
            self.header.ranges_offset,
            self.header.ranges_len,
        )?;
        let byte_off = usize::try_from(ordinal)
            .ok()
            .and_then(|idx| idx.checked_mul(8))
            .ok_or_else(|| "pack posting range: index overflow".to_owned())?;
        decode_posting_range_le(ranges, byte_off, self.header.posting_count)
    }

    /// Resolves all entry ordinals in strictly ascending order for `range`.
    pub fn posting_entry_indices(&self, range: PostingRange) -> Result<Vec<u32>, String> {
        let end = range
            .start
            .checked_add(range.count)
            .ok_or_else(|| "pack posting list: range overflow".to_owned())?;
        if end > self.header.posting_count {
            return Err("pack posting list: range exceeds posting_count".to_owned());
        }
        let postings = section_slice(
            self.bytes,
            self.header.postings_offset,
            self.header.postings_len,
        )?;
        let mut out = Vec::with_capacity(
            usize::try_from(range.count).map_err(|_| "pack posting list: count overflow")?,
        );
        let mut prev: Option<u32> = None;
        for pos in range.start..end {
            let byte_off = usize::try_from(pos)
                .ok()
                .and_then(|idx| idx.checked_mul(4))
                .ok_or_else(|| "pack posting list: byte offset overflow".to_owned())?;
            let entry_ord = read_u32_le(postings, byte_off)?;
            if entry_ord >= self.header.entry_count {
                return Err(format!(
                    "pack posting list: entry ordinal {entry_ord} >= entry_count {}",
                    self.header.entry_count
                ));
            }
            if let Some(p) = prev {
                if entry_ord <= p {
                    return Err(
                        "pack posting list: entry ordinals not strictly increasing".to_owned()
                    );
                }
            }
            prev = Some(entry_ord);
            out.push(entry_ord);
        }
        Ok(out)
    }

    /// Returns the raw payload slice for `entry_ordinal`.
    ///
    /// For `flags == 0`, this is compact UTF-8 JSON; for `PACK_FLAG_COMPACT_INTERNED`,
    /// this is the interned binary entry record.
    pub fn entry_payload_bytes(&self, entry_ordinal: u32) -> Result<&'a [u8], String> {
        if entry_ordinal >= self.header.entry_count {
            return Err(format!(
                "pack entry payload: ordinal {entry_ordinal} out of bounds ({})",
                self.header.entry_count
            ));
        }
        let index = section_slice(
            self.bytes,
            self.header.entry_index_offset,
            self.header.entry_index_len,
        )?;
        let byte_off = usize::try_from(entry_ordinal)
            .ok()
            .and_then(|idx| idx.checked_mul(16))
            .ok_or_else(|| "pack entry payload: index overflow".to_owned())?;
        let slice = decode_entry_slice_le(index, byte_off, self.header.payload_len)?;
        let payload = section_slice(
            self.bytes,
            self.header.payload_offset,
            self.header.payload_len,
        )?;
        section_slice(payload, slice.offset, slice.len)
    }

    /// Deserializes one compiled entry projection from either legacy JSON or compact binary payload.
    pub fn entry(&self, entry_ordinal: u32) -> Result<CompiledEntry, String> {
        let entry_bytes = self.entry_payload_bytes(entry_ordinal)?;
        if let Some(pools) = &self.compact_pools {
            let payload = section_slice(
                self.bytes,
                self.header.payload_offset,
                self.header.payload_len,
            )?;
            decode_compact_entry(entry_bytes, payload, pools)
                .map_err(|err| format!("pack entry {entry_ordinal} decode error: {err}"))
        } else {
            serde_json::from_slice(entry_bytes)
                .map_err(|err| format!("pack entry {entry_ordinal} decode error: {err}"))
        }
    }

    /// Returns the raw compact UTF-8 JSON metadata section bytes.
    pub fn metadata_bytes(&self) -> Result<&'a [u8], String> {
        section_slice(
            self.bytes,
            self.header.metadata_offset,
            self.header.metadata_len,
        )
    }

    /// Returns a cached reference to deserialized compiled pack metadata.
    pub fn metadata_ref(&self) -> Result<&CompiledPackMeta, String> {
        if let Some(cached) = self.meta_cache.get() {
            return Ok(cached);
        }
        let bytes = self.metadata_bytes()?;
        let parsed: CompiledPackMeta = serde_json::from_slice(bytes)
            .map_err(|err| format!("pack metadata decode error: {err}"))?;
        let _ = self.meta_cache.set(parsed);
        Ok(self
            .meta_cache
            .get()
            .expect("metadata cache initialized after set"))
    }

    /// Deserializes compiled pack metadata, reusing the cached metadata when available.
    pub fn metadata(&self) -> Result<CompiledPackMeta, String> {
        self.metadata_ref().cloned()
    }

    fn validate_sections(&self) -> Result<(), String> {
        if self.header.key_count == 0 || self.header.entry_count == 0 {
            return Err("pack binary: approved pack cannot be empty".to_owned());
        }

        let map = self.fst_map()?;
        if map.len() != usize::try_from(self.header.key_count).unwrap_or(usize::MAX) {
            return Err(format!(
                "pack fst: key count {} disagrees with header key_count {}",
                map.len(),
                self.header.key_count
            ));
        }

        let mut expected_posting_cursor = 0u32;
        for ord in 0..self.header.key_count {
            let range = self.posting_range(u64::from(ord))?;
            if range.start != expected_posting_cursor {
                return Err(format!(
                    "pack posting range {ord}: expected contiguous start {expected_posting_cursor}, got {}",
                    range.start
                ));
            }
            expected_posting_cursor = range
                .start
                .checked_add(range.count)
                .ok_or_else(|| "pack posting cursor overflow".to_owned())?;
            let _ = self.posting_entry_indices(range)?;
        }
        if expected_posting_cursor != self.header.posting_count {
            return Err(format!(
                "pack posting range coverage {expected_posting_cursor} != posting_count {}",
                self.header.posting_count
            ));
        }

        let index = section_slice(
            self.bytes,
            self.header.entry_index_offset,
            self.header.entry_index_len,
        )?;
        if let Some(pools) = &self.compact_pools {
            let payload = section_slice(
                self.bytes,
                self.header.payload_offset,
                self.header.payload_len,
            )?;
            let mut expected_payload_cursor = pools.entries_base;
            let mut prev_entry_id: Option<&str> = None;
            for ord in 0..self.header.entry_count {
                let off = usize::try_from(ord)
                    .ok()
                    .and_then(|v| v.checked_mul(16))
                    .ok_or_else(|| "pack entry index overflow".to_owned())?;
                let slice = decode_entry_slice_le(index, off, self.header.payload_len)?;
                if slice.offset != expected_payload_cursor {
                    return Err(format!(
                        "pack entry {ord}: expected contiguous payload offset {expected_payload_cursor}, got {}",
                        slice.offset
                    ));
                }
                expected_payload_cursor = slice
                    .offset
                    .checked_add(slice.len)
                    .ok_or_else(|| "pack entry payload cursor overflow".to_owned())?;
                let entry_bytes = section_slice(payload, slice.offset, slice.len)?;
                let mut cursor = 0usize;
                let entry_id_idx = read_varint_u32(entry_bytes, &mut cursor)?;
                let entry_id = pools.str_at(payload, entry_id_idx)?;
                if let Some(prev) = prev_entry_id {
                    if entry_id <= prev {
                        return Err("pack entries are not strictly ordered by entry_id".to_owned());
                    }
                }
                prev_entry_id = Some(entry_id);
            }
            if expected_payload_cursor != self.header.payload_len {
                return Err(format!(
                    "pack payload coverage {expected_payload_cursor} != payload_len {}",
                    self.header.payload_len
                ));
            }
        } else {
            let mut expected_payload_cursor = 0u64;
            let mut prev_entry_id: Option<String> = None;
            for ord in 0..self.header.entry_count {
                let off = usize::try_from(ord)
                    .ok()
                    .and_then(|v| v.checked_mul(16))
                    .ok_or_else(|| "pack entry index overflow".to_owned())?;
                let slice = decode_entry_slice_le(index, off, self.header.payload_len)?;
                if slice.offset != expected_payload_cursor {
                    return Err(format!(
                        "pack entry {ord}: expected contiguous payload offset {expected_payload_cursor}, got {}",
                        slice.offset
                    ));
                }
                expected_payload_cursor = slice
                    .offset
                    .checked_add(slice.len)
                    .ok_or_else(|| "pack entry payload cursor overflow".to_owned())?;
                let entry = self.entry(ord)?;
                if let Some(prev) = &prev_entry_id {
                    if entry.entry_id <= *prev {
                        return Err("pack entries are not strictly ordered by entry_id".to_owned());
                    }
                }
                prev_entry_id = Some(entry.entry_id);
            }
            if expected_payload_cursor != self.header.payload_len {
                return Err(format!(
                    "pack payload coverage {expected_payload_cursor} != payload_len {}",
                    self.header.payload_len
                ));
            }
        }

        let expected_entries = self.header.entry_count;
        let meta = self.metadata_ref()?;
        if meta.entry_count != expected_entries {
            return Err(format!(
                "pack metadata entry_count {} != header {}",
                meta.entry_count, expected_entries
            ));
        }
        Ok(())
    }
}

fn read_varint_u32(bytes: &[u8], cursor: &mut usize) -> Result<u32, String> {
    let mut result = 0u32;
    let mut shift = 0u32;
    for step in 0..5 {
        let byte = *bytes
            .get(*cursor)
            .ok_or_else(|| "pack binary: truncated varint".to_owned())?;
        *cursor += 1;
        if step == 4 && byte >= 0x10 {
            return Err("pack binary: varint overflows u32".to_owned());
        }
        result |= u32::from(byte & 0x7F) << shift;
        if byte & 0x80 == 0 {
            return Ok(result);
        }
        shift += 7;
    }
    Err("pack binary: varint exceeds 5 bytes".to_owned())
}

fn checked_str_idx(idx: u32, string_count: u32) -> Result<u32, String> {
    if idx >= string_count {
        return Err(format!(
            "pack compact pool: string index {idx} >= string_count {string_count}"
        ));
    }
    Ok(idx)
}

fn checked_opt_str_idx(raw: u32, string_count: u32) -> Result<Option<u32>, String> {
    if raw == 0 {
        Ok(None)
    } else {
        checked_str_idx(raw - 1, string_count).map(Some)
    }
}

fn parse_compact_pools(payload: &[u8]) -> Result<CompactPools, String> {
    if payload.len() < COMPACT_POOL_HEADER_SIZE {
        return Err("pack compact pool: truncated pool header".to_owned());
    }
    if payload.get(0..8) != Some(&COMPACT_POOL_MAGIC) {
        return Err("pack compact pool: invalid pool magic".to_owned());
    }
    let entries_base = read_u64_le(payload, 8)?;
    let entries_base_usize = usize::try_from(entries_base)
        .map_err(|_| "pack compact pool: entries_base exceeds usize".to_owned())?;
    if entries_base_usize < COMPACT_POOL_HEADER_SIZE || entries_base_usize > payload.len() {
        return Err(format!(
            "pack compact pool: invalid entries_base {entries_base} for payload_len {}",
            payload.len()
        ));
    }
    let pool_bytes = &payload[..entries_base_usize];
    let mut cursor = COMPACT_POOL_HEADER_SIZE;

    let string_count = read_u32_le(pool_bytes, cursor)?;
    cursor += 4;
    let max_strings = entries_base_usize - cursor;
    if usize::try_from(string_count).unwrap_or(usize::MAX) > max_strings {
        return Err("pack compact pool: string_count exceeds pool bytes".to_owned());
    }
    let mut strings = Vec::with_capacity(string_count as usize);
    for _ in 0..string_count {
        let len_u32 = read_varint_u32(pool_bytes, &mut cursor)?;
        let len = usize::try_from(len_u32)
            .map_err(|_| "pack compact pool: string length exceeds usize".to_owned())?;
        let end = cursor
            .checked_add(len)
            .ok_or_else(|| "pack compact pool: string end overflow".to_owned())?;
        let slice = pool_bytes
            .get(cursor..end)
            .ok_or_else(|| "pack compact pool: truncated string bytes".to_owned())?;
        std::str::from_utf8(slice)
            .map_err(|err| format!("pack compact pool: invalid utf-8 string: {err}"))?;
        strings.push(CompactStrSpan {
            offset: cursor,
            len,
        });
        cursor = end;
    }

    let acceptance_count = read_u32_le(pool_bytes, cursor)?;
    cursor += 4;
    let max_acceptances = (entries_base_usize - cursor) / 5;
    if usize::try_from(acceptance_count).unwrap_or(usize::MAX) > max_acceptances {
        return Err("pack compact pool: acceptance_count exceeds pool bytes".to_owned());
    }
    let mut acceptances = Vec::with_capacity(acceptance_count as usize);
    for _ in 0..acceptance_count {
        let decision_id = checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let kind = checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let actor_id =
            checked_opt_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let method = checked_opt_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let decided_on = checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        acceptances.push(CompactAcceptanceRef {
            decision_id,
            kind,
            actor_id,
            method,
            decided_on,
        });
    }

    let provenance_count = read_u32_le(pool_bytes, cursor)?;
    cursor += 4;
    let max_provenances = (entries_base_usize - cursor) / 5;
    if usize::try_from(provenance_count).unwrap_or(usize::MAX) > max_provenances {
        return Err("pack compact pool: provenance_count exceeds pool bytes".to_owned());
    }
    let mut provenances = Vec::with_capacity(provenance_count as usize);
    for _ in 0..provenance_count {
        let assertion_id =
            checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let revision_sha256 =
            checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let source_id = checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let locator = checked_str_idx(read_varint_u32(pool_bytes, &mut cursor)?, string_count)?;
        let acceptance_idx = read_varint_u32(pool_bytes, &mut cursor)?;
        if acceptance_idx >= acceptance_count {
            return Err(format!(
                "pack compact pool: acceptance index {acceptance_idx} >= acceptance_count {acceptance_count}"
            ));
        }
        provenances.push(CompactProvenanceRef {
            assertion_id,
            revision_sha256,
            source_id,
            locator,
            acceptance_idx,
        });
    }

    if cursor != entries_base_usize {
        return Err(format!(
            "pack compact pool: pool end {cursor} != entries_base {entries_base_usize}"
        ));
    }

    Ok(CompactPools {
        entries_base,
        strings,
        acceptances,
        provenances,
    })
}

fn read_compact_vec<T>(
    bytes: &[u8],
    cursor: &mut usize,
    mut decode_item: impl FnMut(&[u8], &mut usize) -> Result<T, String>,
) -> Result<Vec<T>, String> {
    let count_u32 = read_varint_u32(bytes, cursor)?;
    let count = usize::try_from(count_u32).map_err(|_| "pack entry: count exceeds usize")?;
    let remaining = bytes.len().saturating_sub(*cursor);
    if count > remaining {
        return Err("pack entry: vec count exceeds remaining entry bytes".to_owned());
    }
    let mut out = Vec::with_capacity(count);
    for _ in 0..count {
        out.push(decode_item(bytes, cursor)?);
    }
    Ok(out)
}

fn decode_provenance_list(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<Vec<CompiledProvenance>, String> {
    read_compact_vec(bytes, cursor, |b, c| {
        let idx = read_varint_u32(b, c)?;
        pools.provenance(payload, idx)
    })
}

fn decode_label_field(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<CompiledLabelField, String> {
    let availability = pools.string_owned(payload, read_varint_u32(bytes, cursor)?)?;
    let value = pools.opt_string(payload, read_varint_u32(bytes, cursor)?)?;
    let convention = pools.opt_string(payload, read_varint_u32(bytes, cursor)?)?;
    let provenance = decode_provenance_list(bytes, cursor, payload, pools)?;
    Ok(CompiledLabelField {
        availability,
        value,
        convention,
        provenance,
    })
}

fn decode_scope(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<CompiledScope, String> {
    let state = pools.string_owned(payload, read_varint_u32(bytes, cursor)?)?;
    let codes = read_compact_vec(bytes, cursor, |b, c| {
        pools.string_owned(payload, read_varint_u32(b, c)?)
    })?;
    let provenance = decode_provenance_list(bytes, cursor, payload, pools)?;
    Ok(CompiledScope {
        state,
        codes,
        provenance,
    })
}

fn decode_field(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<CompiledField, String> {
    let availability = pools.string_owned(payload, read_varint_u32(bytes, cursor)?)?;
    let tag = *bytes
        .get(*cursor)
        .ok_or_else(|| "pack entry: truncated field value tag".to_owned())?;
    *cursor += 1;
    let value = match tag {
        0 => None,
        1 => Some(serde_json::Value::Null),
        2 => Some(serde_json::Value::Bool(false)),
        3 => Some(serde_json::Value::Bool(true)),
        4 => Some(serde_json::Value::String(
            pools.string_owned(payload, read_varint_u32(bytes, cursor)?)?,
        )),
        5 => {
            let json_str = pools.str_at(payload, read_varint_u32(bytes, cursor)?)?;
            let val: serde_json::Value = serde_json::from_str(json_str)
                .map_err(|err| format!("pack entry: invalid field json: {err}"))?;
            Some(val)
        }
        other => return Err(format!("pack entry: invalid field value tag {other}")),
    };
    let convention = pools.opt_string(payload, read_varint_u32(bytes, cursor)?)?;
    let provenance = decode_provenance_list(bytes, cursor, payload, pools)?;
    Ok(CompiledField {
        availability,
        value,
        convention,
        provenance,
    })
}

fn decode_annotations(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<Vec<CompiledAnnotation>, String> {
    read_compact_vec(bytes, cursor, |b, c| {
        let property = pools.string_owned(payload, read_varint_u32(b, c)?)?;
        let field = decode_field(b, c, payload, pools)?;
        Ok(CompiledAnnotation { property, field })
    })
}

fn decode_texts(
    bytes: &[u8],
    cursor: &mut usize,
    payload: &[u8],
    pools: &CompactPools,
) -> Result<Vec<CompiledText>, String> {
    read_compact_vec(bytes, cursor, |b, c| {
        Ok(CompiledText {
            text_id: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            kind: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            language_id: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            text: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            provenance: decode_provenance_list(b, c, payload, pools)?,
        })
    })
}

fn decode_compact_entry(
    entry_bytes: &[u8],
    payload: &[u8],
    pools: &CompactPools,
) -> Result<CompiledEntry, String> {
    let mut cursor = 0usize;
    let entry_id = pools.string_owned(payload, read_varint_u32(entry_bytes, &mut cursor)?)?;
    let revision = pools.string_owned(payload, read_varint_u32(entry_bytes, &mut cursor)?)?;
    let headword = pools.string_owned(payload, read_varint_u32(entry_bytes, &mut cursor)?)?;
    let language_id = pools.string_owned(payload, read_varint_u32(entry_bytes, &mut cursor)?)?;
    let part_of_speech = decode_label_field(entry_bytes, &mut cursor, payload, pools)?;
    let forms = read_compact_vec(entry_bytes, &mut cursor, |b, c| {
        Ok(CompiledForm {
            form_id: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            representation: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            role: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            text: pools.string_owned(payload, read_varint_u32(b, c)?)?,
            convention: pools.opt_string(payload, read_varint_u32(b, c)?)?,
            provenance: decode_provenance_list(b, c, payload, pools)?,
        })
    })?;
    let senses = read_compact_vec(entry_bytes, &mut cursor, |b, c| {
        let sense_id = pools.string_owned(payload, read_varint_u32(b, c)?)?;
        let display_order = read_varint_u32(b, c)?;
        let parent_sense_id = pools.opt_string(payload, read_varint_u32(b, c)?)?;
        let components = decode_texts(b, c, payload, pools)?;
        let examples = decode_texts(b, c, payload, pools)?;
        let relations = read_compact_vec(b, c, |rb, rc| {
            Ok(CompiledRelation {
                relation_id: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                code: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                directionality: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                source: CompiledEndpoint {
                    kind: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                    id: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                },
                target: CompiledEndpoint {
                    kind: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                    id: pools.string_owned(payload, read_varint_u32(rb, rc)?)?,
                },
                provenance: decode_provenance_list(rb, rc, payload, pools)?,
            })
        })?;
        let region = decode_scope(b, c, payload, pools)?;
        let register = decode_label_field(b, c, payload, pools)?;
        let annotations = decode_annotations(b, c, payload, pools)?;
        let provenance = decode_provenance_list(b, c, payload, pools)?;
        Ok(CompiledSense {
            sense_id,
            display_order,
            parent_sense_id,
            components,
            examples,
            relations,
            region,
            register,
            annotations,
            provenance,
        })
    })?;
    let region = decode_scope(entry_bytes, &mut cursor, payload, pools)?;
    let register = decode_label_field(entry_bytes, &mut cursor, payload, pools)?;
    let annotations = decode_annotations(entry_bytes, &mut cursor, payload, pools)?;
    let provenance = decode_provenance_list(entry_bytes, &mut cursor, payload, pools)?;

    if cursor != entry_bytes.len() {
        return Err(format!(
            "pack entry: trailing bytes after decode ({cursor} != {})",
            entry_bytes.len()
        ));
    }

    Ok(CompiledEntry {
        entry_id,
        revision,
        headword,
        language_id,
        part_of_speech,
        forms,
        senses,
        region,
        register,
        annotations,
        provenance,
    })
}

fn section_slice(bytes: &[u8], offset: u64, len: u64) -> Result<&[u8], String> {
    let start = usize::try_from(offset).map_err(|_| "pack section offset exceeds usize")?;
    let size = usize::try_from(len).map_err(|_| "pack section length exceeds usize")?;
    let end = start
        .checked_add(size)
        .ok_or_else(|| "pack section end overflow".to_owned())?;
    bytes.get(start..end).ok_or_else(|| {
        format!(
            "pack section {start}..{end} out of bounds ({})",
            bytes.len()
        )
    })
}

fn validate_header_layout(header: &PackHeader, total_len: usize) -> Result<(), String> {
    let total_u64 = u64::try_from(total_len).map_err(|_| "pack size exceeds u64")?;
    let header_u64 = u64::try_from(HEADER_SIZE).map_err(|_| "header size exceeds u64")?;

    if header.fst_offset != header_u64 {
        return Err(format!(
            "pack layout: expected fst_offset {header_u64}, got {}",
            header.fst_offset
        ));
    }
    let expected_ranges_offset = header
        .fst_offset
        .checked_add(header.fst_len)
        .ok_or("pack layout: fst end overflow")?;
    if header.ranges_offset != expected_ranges_offset {
        return Err("pack layout: non-contiguous ranges_offset".to_owned());
    }
    let expected_ranges_len = u64::from(header.key_count)
        .checked_mul(8)
        .ok_or("pack layout: ranges_len overflow")?;
    if header.ranges_len != expected_ranges_len {
        return Err("pack layout: ranges_len mismatch".to_owned());
    }

    let expected_postings_offset = header
        .ranges_offset
        .checked_add(header.ranges_len)
        .ok_or("pack layout: ranges end overflow")?;
    if header.postings_offset != expected_postings_offset {
        return Err("pack layout: non-contiguous postings_offset".to_owned());
    }
    let expected_postings_len = u64::from(header.posting_count)
        .checked_mul(4)
        .ok_or("pack layout: postings_len overflow")?;
    if header.postings_len != expected_postings_len {
        return Err("pack layout: postings_len mismatch".to_owned());
    }

    let expected_entry_index_offset = header
        .postings_offset
        .checked_add(header.postings_len)
        .ok_or("pack layout: postings end overflow")?;
    if header.entry_index_offset != expected_entry_index_offset {
        return Err("pack layout: non-contiguous entry_index_offset".to_owned());
    }
    let expected_entry_index_len = u64::from(header.entry_count)
        .checked_mul(16)
        .ok_or("pack layout: entry_index_len overflow")?;
    if header.entry_index_len != expected_entry_index_len {
        return Err("pack layout: entry_index_len mismatch".to_owned());
    }

    let expected_payload_offset = header
        .entry_index_offset
        .checked_add(header.entry_index_len)
        .ok_or("pack layout: entry_index end overflow")?;
    if header.payload_offset != expected_payload_offset {
        return Err("pack layout: non-contiguous payload_offset".to_owned());
    }

    let expected_metadata_offset = header
        .payload_offset
        .checked_add(header.payload_len)
        .ok_or("pack layout: payload end overflow")?;
    if header.metadata_offset != expected_metadata_offset {
        return Err("pack layout: non-contiguous metadata_offset".to_owned());
    }

    let expected_total = header
        .metadata_offset
        .checked_add(header.metadata_len)
        .ok_or("pack layout: total size overflow")?;
    if expected_total != total_u64 {
        return Err(format!(
            "pack layout: expected total bytes {expected_total}, got {total_u64}"
        ));
    }
    Ok(())
}

fn verify_checksum(bytes: &[u8], expected: &[u8; 32]) -> Result<(), String> {
    let mut hasher = Sha256::new();
    let head = bytes
        .get(0..CHECKSUM_OFFSET)
        .ok_or("pack checksum: header truncated")?;
    let tail = bytes
        .get(HEADER_SIZE..)
        .ok_or("pack checksum: body truncated")?;
    hasher.update(head);
    hasher.update(tail);
    let actual: [u8; 32] = hasher.finalize().into();
    if &actual != expected {
        return Err("pack binary: checksum_sha256 mismatch".to_owned());
    }
    Ok(())
}
