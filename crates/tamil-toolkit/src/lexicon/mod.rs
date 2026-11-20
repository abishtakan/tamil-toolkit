//! Exact compiled-lexicon runtime lookup and pack metadata introspection.
//!
//! Reads deterministically compiled `.tlpack` artifacts via [`crate::lexicon_pack`]
//! without duplicating binary decoding or Tamil normalization logic. Query
//! normalization uses [`tamil_norm::normalize_nfc`] (allocating a canonical
//! `String` when needed), and matching entries are deserialized on demand from
//! verified little-endian payload slices.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use serde_json::Value;

pub use crate::lexicon_pack::{
    available_packs, open_available_pack, CompiledAcceptance as Acceptance,
    CompiledAnnotation as Annotation, CompiledCoverage as Coverage, CompiledEndpoint as Endpoint,
    CompiledEntry as Entry, CompiledField as Field, CompiledForm as Form,
    CompiledLabelField as LabelField, CompiledPackMeta, CompiledPackView,
    CompiledProvenance as Provenance, CompiledRelation as Relation, CompiledScope as Scope,
    CompiledSense as Sense, CompiledText as Text, KNOWN_PACK_IDS,
};

/// Lookup response contract version matching `lookup-response.schema.json`.
pub const SCHEMA_VERSION: u32 = crate::lexicon_pack::SCHEMA_VERSION;

/// Maximum accepted UTF-8 input length in bytes (no silent truncation).
pub const MAX_INPUT_BYTES: usize = 65_536;

/// Default selected pack IDs when `"packs"` is omitted by a caller.
pub const DEFAULT_PACKS: &[&str] = &["core"];

/// Lookup match outcome discriminant.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LookupStatus {
    Matched,
    NotFound,
}

/// Typed lookup request matching the `lexicon_lookup` dispatcher contract.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LookupRequest {
    pub input: String,
    #[serde(default)]
    pub packs: Option<Vec<String>>,
    #[serde(default)]
    pub region: Option<String>,
    #[serde(default)]
    pub register: Option<String>,
}

/// Public pack metadata returned by `lexicon_packs` and embedded in `LookupResponse`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PackInfo {
    pub id: String,
    pub dataset_version: String,
    pub schema_version: u32,
    pub index_format_version: u32,
    pub manifest_sha256: String,
    pub available: bool,
    pub coverage: Coverage,
}

/// Closed lookup response matching `specs/021-lexicon-curation/contracts/lookup-response.schema.json`.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LookupResponse {
    pub schema_version: u32,
    pub status: LookupStatus,
    pub canonical_query: String,
    pub packs: Vec<PackInfo>,
    pub entries: Vec<Entry>,
}

struct OpenedPack<'a> {
    id: String,
    meta: &'a CompiledPackMeta,
    view: &'a CompiledPackView<'a>,
}

/// Returns metadata for every approved pack embedded in this build, sorted by pack ID.
///
/// Validates each embedded `.tlpack` artifact cleanly rather than exposing unverified headers.
pub fn packs() -> Result<Vec<PackInfo>, String> {
    let mut items = Vec::new();
    for artifact in available_packs() {
        let view = open_available_pack(artifact.id)?;
        let meta = view.metadata_ref()?;
        items.push(pack_info_from_meta(artifact.id, meta));
    }
    items.sort_by(|a, b| a.id.cmp(&b.id));
    Ok(items)
}

/// Performs an exact NFC-normalized lookup over approved embedded lexicon packs.
///
/// Allocates `canonical_query` via `tamil_norm::normalize_nfc` and deserialized
/// matching entries/pack metadata from embedded binary slices.
pub fn lookup(request: &LookupRequest) -> Result<LookupResponse, String> {
    let selected = validate_request_inputs(
        &request.input,
        request.packs.as_deref(),
        request.region.as_deref(),
        request.register.as_deref(),
    )?;

    let mut views = Vec::with_capacity(selected.len());
    for pack_id in &selected {
        views.push((pack_id.as_str(), open_available_pack(pack_id)?));
    }
    let refs: Vec<(&str, &CompiledPackView<'_>)> =
        views.iter().map(|(id, view)| (*id, view)).collect();

    lookup_with_validated_packs(
        &request.input,
        &selected,
        request.region.as_deref(),
        request.register.as_deref(),
        &refs,
    )
}

/// Borrowed convenience wrapper around [`lookup`].
pub fn lookup_str(
    input: &str,
    packs: Option<&[&str]>,
    region: Option<&str>,
    register: Option<&str>,
) -> Result<LookupResponse, String> {
    let req = LookupRequest {
        input: input.to_owned(),
        packs: packs.map(|slice| slice.iter().map(|s| (*s).to_owned()).collect()),
        region: region.map(str::to_owned),
        register: register.map(str::to_owned),
    };
    lookup(&req)
}

/// Runs exact lookup validation, compatibility checks, filtering, and sorting
/// over caller-supplied compiled pack views.
pub fn lookup_in_views<'a>(
    request: &LookupRequest,
    available: &[(&str, &'a CompiledPackView<'a>)],
) -> Result<LookupResponse, String> {
    let selected = validate_request_inputs(
        &request.input,
        request.packs.as_deref(),
        request.region.as_deref(),
        request.register.as_deref(),
    )?;

    let mut opened_pairs = Vec::with_capacity(selected.len());
    for pack_id in &selected {
        let Some((_, view)) = available.iter().find(|(id, _)| *id == pack_id) else {
            return Err(format!("lexicon: pack unavailable '{pack_id}'"));
        };
        opened_pairs.push((pack_id.as_str(), *view));
    }

    lookup_with_validated_packs(
        &request.input,
        &selected,
        request.region.as_deref(),
        request.register.as_deref(),
        &opened_pairs,
    )
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_packs"`.
pub fn execute_packs(request: &Value, input: &Value) -> Result<Value, String> {
    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    if obj.keys().any(|k| k != "op" && k != "input") || !input.is_null() {
        return Err("lexicon: invalid options".to_owned());
    }
    let result = packs()?;
    serde_json::to_value(result).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_lookup"`.
pub fn execute_lookup(request: &Value, input: &Value) -> Result<Value, String> {
    let text = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    if text.len() > MAX_INPUT_BYTES {
        return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
    }

    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    for key in obj.keys() {
        if !matches!(
            key.as_str(),
            "op" | "input" | "packs" | "region" | "register"
        ) {
            return Err("lexicon: invalid options".to_owned());
        }
    }

    let region = parse_optional_filter_option(obj.get("region"))?;
    let register = parse_optional_filter_option(obj.get("register"))?;
    let packs = match obj.get("packs") {
        None => None,
        Some(raw) => Some(parse_packs_option(raw)?),
    };

    let response = lookup(&LookupRequest {
        input: text.to_owned(),
        packs,
        region,
        register,
    })?;
    serde_json::to_value(response).map_err(|err| format!("lexicon: serialize error: {err}"))
}

fn parse_optional_filter_option(value: Option<&Value>) -> Result<Option<String>, String> {
    match value {
        None | Some(Value::Null) => Ok(None),
        Some(Value::String(s)) if !s.is_empty() => Ok(Some(s.clone())),
        _ => Err("lexicon: invalid options".to_owned()),
    }
}

fn parse_packs_option(value: &Value) -> Result<Vec<String>, String> {
    let arr = value
        .as_array()
        .ok_or_else(|| "lexicon: packs must be a nonempty string array".to_owned())?;
    if arr.is_empty() {
        return Err("lexicon: packs must be a nonempty string array".to_owned());
    }
    let mut out = Vec::with_capacity(arr.len());
    for item in arr {
        let s = item
            .as_str()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| "lexicon: packs must be a nonempty string array".to_owned())?;
        out.push(s.to_owned());
    }
    Ok(out)
}

fn validate_request_inputs(
    input: &str,
    packs: Option<&[String]>,
    region: Option<&str>,
    register: Option<&str>,
) -> Result<Vec<String>, String> {
    if input.len() > MAX_INPUT_BYTES {
        return Err("lexicon: input exceeds 65536 UTF-8 bytes".to_owned());
    }
    if matches!(region, Some("")) || matches!(register, Some("")) {
        return Err("lexicon: invalid options".to_owned());
    }

    let mut selected = match packs {
        None => DEFAULT_PACKS.iter().map(|s| (*s).to_owned()).collect(),
        Some(slice) => {
            if slice.is_empty() || slice.iter().any(String::is_empty) {
                return Err("lexicon: packs must be a nonempty string array".to_owned());
            }
            slice.to_vec()
        }
    };
    selected.sort_unstable();
    selected.dedup();

    // Check every requested pack name against KNOWN_PACK_IDS before checking pack availability.
    for pack_id in &selected {
        if !KNOWN_PACK_IDS.contains(&pack_id.as_str()) {
            return Err(format!("lexicon: unknown pack '{pack_id}'"));
        }
    }

    Ok(selected)
}

fn lookup_with_validated_packs<'a>(
    input: &str,
    selected: &[String],
    region_filter: Option<&str>,
    register_filter: Option<&str>,
    views: &[(&str, &'a CompiledPackView<'a>)],
) -> Result<LookupResponse, String> {
    let mut opened = Vec::with_capacity(selected.len());
    for (pack_id, view) in views {
        let meta = view.metadata_ref()?;
        if meta.pack_id != *pack_id {
            return Err("lexicon: incompatible pack versions".to_owned());
        }
        opened.push(OpenedPack {
            id: (*pack_id).to_owned(),
            meta,
            view,
        });
    }

    let region_parents = validate_pack_compatibility(&opened)?;
    validate_filter_codes(&opened, &region_parents, region_filter, register_filter)?;

    let canonical_query = tamil_norm::normalize_nfc(input);
    let mut by_entry_id: BTreeMap<String, Entry> = BTreeMap::new();

    for pack in &opened {
        let fst = pack.view.fst_map()?;
        let Some(key_ord) = fst.get(canonical_query.as_bytes()) else {
            continue;
        };
        let range = pack.view.posting_range(key_ord)?;
        let indices = pack.view.posting_entry_indices(range)?;
        for entry_ord in indices {
            let mut entry = pack.view.entry(entry_ord)?;
            if let Some(existing) = by_entry_id.get(&entry.entry_id) {
                if existing.revision != entry.revision {
                    return Err("lexicon: incompatible pack versions".to_owned());
                }
                continue;
            }
            if project_and_filter_entry(&mut entry, region_filter, register_filter, &region_parents)
            {
                by_entry_id.insert(entry.entry_id.clone(), entry);
            }
        }
    }

    let entries: Vec<Entry> = by_entry_id.into_values().collect();
    let status = if entries.is_empty() {
        LookupStatus::NotFound
    } else {
        LookupStatus::Matched
    };
    let pack_infos: Vec<PackInfo> = opened
        .iter()
        .map(|pack| pack_info_from_meta(&pack.id, pack.meta))
        .collect();

    Ok(LookupResponse {
        schema_version: SCHEMA_VERSION,
        status,
        canonical_query,
        packs: pack_infos,
        entries,
    })
}

fn dataset_version_compat_key(version: &str) -> Result<&str, String> {
    let trimmed = version.trim();
    if trimmed.is_empty() {
        return Err("lexicon: incompatible pack versions".to_owned());
    }
    match trimmed.split_once('+') {
        Some((base, build)) if !base.is_empty() && !build.is_empty() => Ok(base),
        Some(_) => Err("lexicon: incompatible pack versions".to_owned()),
        None => Ok(trimmed),
    }
}

fn validate_pack_compatibility<'a>(
    opened: &'a [OpenedPack<'a>],
) -> Result<BTreeMap<String, Option<String>>, String> {
    let first = opened
        .first()
        .ok_or_else(|| "lexicon: packs must be a nonempty string array".to_owned())?;
    let expected_schema = first.meta.schema_version;
    let expected_index = first.meta.index_format_version;
    let expected_dataset_base = dataset_version_compat_key(&first.meta.dataset_version)?;
    let expected_vocab = &first.meta.vocabularies.vocabulary_version;

    if expected_schema != SCHEMA_VERSION
        || expected_index != crate::lexicon_pack::INDEX_FORMAT_VERSION
    {
        return Err("lexicon: incompatible pack versions".to_owned());
    }

    let mut seen_revisions: BTreeMap<&str, &str> = BTreeMap::new();
    let mut region_parents: BTreeMap<String, Option<String>> = BTreeMap::new();

    for pack in opened {
        let hdr = pack.view.header();
        let pack_dataset_base = dataset_version_compat_key(&pack.meta.dataset_version)?;
        if hdr.schema_version != expected_schema
            || hdr.index_format_version != expected_index
            || pack.meta.schema_version != expected_schema
            || pack.meta.index_format_version != expected_index
            || pack_dataset_base != expected_dataset_base
            || &pack.meta.vocabularies.vocabulary_version != expected_vocab
        {
            return Err("lexicon: incompatible pack versions".to_owned());
        }

        if opened.len() > 1 {
            for (entry_id, rev) in &pack.meta.entry_revisions {
                if let Some(prev) = seen_revisions.insert(entry_id.as_str(), rev.as_str()) {
                    if prev != rev.as_str() {
                        return Err("lexicon: incompatible pack versions".to_owned());
                    }
                }
            }
        }

        for reg in &pack.meta.vocabularies.regions {
            if let Some(prev_parent) =
                region_parents.insert(reg.code.clone(), reg.parent_code.clone())
            {
                if prev_parent != reg.parent_code {
                    return Err("lexicon: incompatible pack versions".to_owned());
                }
            }
        }

        for label in &pack.meta.labels {
            if label.category == "region" {
                if let Some(prev_parent) =
                    region_parents.insert(label.code.clone(), label.parent_code.clone())
                {
                    if prev_parent != label.parent_code {
                        return Err("lexicon: incompatible pack versions".to_owned());
                    }
                }
            }
        }
    }

    Ok(region_parents)
}

fn validate_filter_codes(
    opened: &[OpenedPack<'_>],
    region_parents: &BTreeMap<String, Option<String>>,
    region_filter: Option<&str>,
    register_filter: Option<&str>,
) -> Result<(), String> {
    if let Some(region) = region_filter {
        if !region_parents.contains_key(region) {
            return Err(format!("lexicon: unknown region '{region}'"));
        }
    }

    if let Some(register) = register_filter {
        let mut known_registers: BTreeSet<&str> = BTreeSet::new();
        for pack in opened {
            for r in &pack.meta.vocabularies.registers {
                known_registers.insert(r.as_str());
            }
            for label in &pack.meta.labels {
                if label.category == "register" {
                    known_registers.insert(label.code.as_str());
                }
            }
        }
        if !known_registers.contains(register) {
            return Err(format!("lexicon: unknown register '{register}'"));
        }
    }

    Ok(())
}

fn project_and_filter_entry(
    entry: &mut Entry,
    region_filter: Option<&str>,
    register_filter: Option<&str>,
    region_parents: &BTreeMap<String, Option<String>>,
) -> bool {
    entry.senses.retain(|sense| {
        let region_ok = match region_filter {
            None => true,
            Some(target) => matches_region(&sense.region, target, region_parents),
        };
        let register_ok = match register_filter {
            None => true,
            Some(target) => matches_register(&sense.register, target),
        };
        region_ok && register_ok
    });

    if entry.senses.is_empty() {
        return false;
    }

    for sense in &mut entry.senses {
        for rel in &mut sense.relations {
            if rel.directionality == "undirected" {
                rel.directionality = "symmetric".to_owned();
            }
        }
        sense
            .relations
            .sort_by(|a, b| a.relation_id.cmp(&b.relation_id));
        sense.components.sort_by(|a, b| a.text_id.cmp(&b.text_id));
        sense.examples.sort_by(|a, b| a.text_id.cmp(&b.text_id));
        sense
            .annotations
            .sort_by(|a, b| a.property.cmp(&b.property));
    }

    entry.forms.sort_by(|a, b| a.form_id.cmp(&b.form_id));
    entry
        .annotations
        .sort_by(|a, b| a.property.cmp(&b.property));
    entry
        .senses
        .sort_by(|a, b| (a.display_order, &a.sense_id).cmp(&(b.display_order, &b.sense_id)));
    true
}

fn matches_region(
    scope: &Scope,
    requested_region: &str,
    region_parents: &BTreeMap<String, Option<String>>,
) -> bool {
    match scope.state.as_str() {
        "unrestricted" => true,
        "attested" => scope
            .codes
            .iter()
            .any(|code| is_same_or_child_region(code, requested_region, region_parents)),
        _ => false,
    }
}

fn is_same_or_child_region(
    attested_code: &str,
    requested_region: &str,
    region_parents: &BTreeMap<String, Option<String>>,
) -> bool {
    let mut cur = Some(attested_code);
    let max_hops = region_parents.len().saturating_add(1);
    for _ in 0..max_hops {
        let Some(code) = cur else {
            return false;
        };
        if code == requested_region {
            return true;
        }
        cur = region_parents.get(code).and_then(|p| p.as_deref());
    }
    false
}

fn matches_register(field: &LabelField, requested_register: &str) -> bool {
    field.availability == "available" && field.value.as_deref() == Some(requested_register)
}

fn pack_info_from_meta(pack_id: &str, meta: &CompiledPackMeta) -> PackInfo {
    PackInfo {
        id: pack_id.to_owned(),
        dataset_version: meta.dataset_version.clone(),
        schema_version: meta.schema_version,
        index_format_version: meta.index_format_version,
        manifest_sha256: meta.manifest_sha256.clone(),
        available: true,
        coverage: meta.coverage.clone(),
    }
}
