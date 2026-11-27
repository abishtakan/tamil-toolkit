//! Exact compiled-lexicon runtime lookup, dynamic `TMLPACK1`/`TMLPACK2` pack registry,
//! FST prefix/folded search, and lexical relations backed by Rank 2 [`tamil_lexicon`].

use std::path::Path;
use std::sync::{OnceLock, RwLock};

use serde_json::{json, Value};

pub use crate::lexicon_pack::{available_packs, open_available_pack};
pub use tamil_lexicon::lookup_v1::{
    lookup_in_views, pack_info_from_meta, validate_request_inputs, Acceptance, Annotation,
    CompiledPackMeta, CompiledPackView, Coverage, Endpoint, Entry, Field, Form, LabelField,
    LookupRequest, LookupResponse, LookupStatus, PackInfo, Provenance, Relation, Scope, Sense,
    Text, DEFAULT_PACKS, KNOWN_PACK_IDS, MAX_INPUT_BYTES, SCHEMA_VERSION,
};
pub use tamil_lexicon::store::{
    auto_discover_pack_dir, entry_matches_filter, pack_category, AnnotatedEntry,
    CompactLookupResult, CompactPackSummary, FuzzySearchHit, FuzzySearchResult, LexiconCategory,
    LexiconPrefixSearchResult, LexiconProfile, LexiconSearchOptions, LexiconStore,
    LexiconStoreStats, LoadedPack, PackRegistry, PrefixSearchHit, PrefixSearchOptions,
    PrefixSearchResult, QueryScope, RelationsResult, TierFilter, WordDefinition, WordMeaning,
    WordRelationsGroup, WordSourceRef, MAX_SEARCH_LIMIT,
};
pub use tamil_lexicon::v2::{
    build_compact_pack, extract_english_tokens, split_facet_tokens, CompactEntry, CompactForm,
    CompactPackHeader, CompactPackInput, CompactPackMeta, CompactPackView, CompactRelation,
    CompactSense, PackTier, V2_FLAG_HAS_ENGLISH_INDEX,
};

fn runtime_registry_lock() -> &'static RwLock<PackRegistry> {
    static REGISTRY: OnceLock<RwLock<PackRegistry>> = OnceLock::new();
    REGISTRY.get_or_init(|| RwLock::new(PackRegistry::new()))
}

/// Mounts a `.tlpack` v1 or v2 binary image into the process runtime registry.
pub fn load_pack_bytes(bytes: Vec<u8>) -> Result<CompactPackSummary, String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.load_pack_bytes(bytes)
}

/// Mounts a `.tlpack` v1 or v2 binary image and returns its summary as JSON (for FFI/WASM).
pub fn load_pack_bytes_json(bytes: &[u8]) -> Result<String, String> {
    let summary = load_pack_bytes(bytes.to_vec())?;
    serde_json::to_string(&summary).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Loads and mounts one `.tlpack` v1 or v2 file from disk into the runtime registry.
pub fn load_pack_file(path: &Path) -> Result<CompactPackSummary, String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.load_pack_file(path)
}

/// Recursively loads all `*.tlpack` files from `dir` into the runtime registry.
pub fn load_pack_dir(dir: &Path) -> Result<Vec<CompactPackSummary>, String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.load_pack_dir(dir)
}

/// Loads `.tlpack` files matching `profile` from `dir` into the runtime registry.
pub fn load_profile_from_dir(
    dir: &Path,
    profile: LexiconProfile,
) -> Result<Vec<CompactPackSummary>, String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.load_profile_from_dir(dir, profile)
}

/// Initializes the runtime registry with `profile` from `dir` (or auto-discovered pack directory).
///
/// When `replace` is `true`, clears previously mounted packs first so the registry reflects
/// exactly the requested profile.
pub fn init_runtime(
    profile: LexiconProfile,
    dir: Option<&Path>,
    replace: bool,
) -> Result<(std::path::PathBuf, Vec<CompactPackSummary>), String> {
    let resolved = match dir {
        Some(path) => path.to_path_buf(),
        None => auto_discover_pack_dir().ok_or_else(|| {
            "lexicon: no pack directory found (set TAMIL_LEXICON_DIR or run `just lexicon-build`)"
                .to_owned()
        })?,
    };
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    if replace {
        guard.clear();
    }
    let loaded = guard.load_profile_from_dir(&resolved, profile)?;
    if loaded.is_empty() {
        return Err(format!(
            "lexicon: no packs matching profile '{}' in '{}'",
            profile.as_str(),
            resolved.display()
        ));
    }
    Ok((resolved, loaded))
}

/// Unmounts one runtime pack by `pack_id`.
pub fn unload_pack(pack_id: &str) -> Result<bool, String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    Ok(guard.unload_pack(pack_id))
}

/// Clears all dynamically mounted runtime packs.
pub fn clear_runtime_packs() -> Result<(), String> {
    let mut guard = runtime_registry_lock()
        .write()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.clear();
    Ok(())
}

/// Lists all packs currently mounted in the dynamic runtime registry.
pub fn runtime_packs() -> Result<Vec<CompactPackSummary>, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    Ok(guard.list_packs())
}

/// Queries the runtime registry for compact entries matching `word` and `scope`.
pub fn query_runtime(word: &str, scope: &QueryScope) -> Result<CompactLookupResult, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.lookup_compact(word, scope)
}

/// Runs FST prefix search across the runtime registry.
pub fn search_runtime(
    prefix: &str,
    options: &PrefixSearchOptions,
) -> Result<PrefixSearchResult, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.prefix_search(prefix, options)
}

/// Runs reverse English-to-Tamil gloss/definition search across the runtime registry.
pub fn search_english_runtime(
    query: &str,
    options: &PrefixSearchOptions,
) -> Result<PrefixSearchResult, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.search_english(query, options)
}

/// Returns aggregated statistics and facet counts across all mounted runtime packs.
pub fn stats_runtime() -> Result<LexiconStoreStats, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    Ok(guard.stats())
}

/// Queries indexed lexical relations across the runtime registry.
pub fn relations_runtime(word: &str, scope: &QueryScope) -> Result<RelationsResult, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.lookup_relations(word, scope)
}

/// Builds a unified, deduplicated word definition across all mounted packs in the runtime registry.
pub fn define_runtime(word: &str, scope: &QueryScope) -> Result<WordDefinition, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.define(word, scope)
}

/// Runs bounded Damerau-Levenshtein fuzzy search across the runtime registry.
pub fn fuzzy_search_runtime(
    word: &str,
    max_distance: u32,
    options: &PrefixSearchOptions,
) -> Result<FuzzySearchResult, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.fuzzy_search(word, max_distance, options)
}

/// Returns exact FST keys that are char-boundary prefixes of `word`, longest-first.
pub fn longest_prefix_runtime(word: &str, scope: &QueryScope) -> Result<Vec<String>, String> {
    let guard = runtime_registry_lock()
        .read()
        .map_err(|_| "lexicon: runtime registry lock poisoned".to_owned())?;
    guard.longest_prefix_matches(word, scope)
}

/// Fast existence check across the runtime registry.
pub fn contains_word_runtime(word: &str, scope: &QueryScope) -> bool {
    runtime_registry_lock()
        .read()
        .map(|guard| guard.contains_word(word, scope))
        .unwrap_or(false)
}

/// Returns metadata for every approved `TMLPACK1` pack embedded in this build, sorted by pack ID.
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

/// Performs an exact NFC-normalized lookup over approved embedded `TMLPACK1` lexicon packs.
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

    tamil_lexicon::lookup_v1::lookup_with_validated_packs(
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

/// Shared JSON dispatcher entrypoint for `op = "lexicon_load_pack"`.
///
/// Accepts `input` as an object containing either:
/// - `{"path": "<file_or_dir>"}` (native host filesystem load)
/// - `{"bytes": [u8, ...]}` (byte array, works in WASM and FFI)
pub fn execute_load_pack(input: &Value) -> Result<Value, String> {
    let obj = input
        .as_object()
        .ok_or_else(|| "lexicon: load_pack input must be an object".to_owned())?;
    if let Some(path_val) = obj.get("path") {
        let path_str = path_val
            .as_str()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| "lexicon: path must be a nonempty string".to_owned())?;
        let p = Path::new(path_str);
        if p.is_dir() {
            let summaries = load_pack_dir(p)?;
            return serde_json::to_value(json!({ "loaded": summaries }))
                .map_err(|err| format!("lexicon: serialize error: {err}"));
        }
        let summary = load_pack_file(p)?;
        return serde_json::to_value(json!({ "loaded": [summary] }))
            .map_err(|err| format!("lexicon: serialize error: {err}"));
    }
    if let Some(bytes_val) = obj.get("bytes") {
        let arr = bytes_val
            .as_array()
            .ok_or_else(|| "lexicon: bytes must be an array of u8".to_owned())?;
        let mut raw = Vec::with_capacity(arr.len());
        for item in arr {
            let n = item
                .as_u64()
                .and_then(|v| u8::try_from(v).ok())
                .ok_or_else(|| "lexicon: bytes array must contain integers 0..=255".to_owned())?;
            raw.push(n);
        }
        let summary = load_pack_bytes(raw)?;
        return serde_json::to_value(json!({ "loaded": [summary] }))
            .map_err(|err| format!("lexicon: serialize error: {err}"));
    }
    Err("lexicon: load_pack requires 'path' or 'bytes'".to_owned())
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_unload_pack"`.
pub fn execute_unload_pack(input: &Value) -> Result<Value, String> {
    if input.is_null() {
        clear_runtime_packs()?;
        return Ok(json!({ "cleared": true }));
    }
    let pack_id = input
        .as_str()
        .filter(|s| !s.is_empty())
        .ok_or_else(|| "lexicon: pack_id must be a nonempty string or null".to_owned())?;
    let removed = unload_pack(pack_id)?;
    Ok(json!({ "pack_id": pack_id, "removed": removed }))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_stats"`.
pub fn execute_stats(request: &Value, input: &Value) -> Result<Value, String> {
    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    if obj.keys().any(|k| k != "op" && k != "input") || !input.is_null() {
        return Err("lexicon: invalid options".to_owned());
    }
    let stats = stats_runtime()?;
    serde_json::to_value(stats).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_query"`.
pub fn execute_query(request: &Value, input: &Value) -> Result<Value, String> {
    let text = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, false)?;
    let res = query_runtime(text, &scope)?;
    serde_json::to_value(res).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_search"`.
pub fn execute_search(request: &Value, input: &Value) -> Result<Value, String> {
    let prefix = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, true)?;
    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    let limit = match obj.get("limit") {
        None | Some(Value::Null) => 25usize,
        Some(v) => {
            let n = v
                .as_u64()
                .ok_or_else(|| "lexicon: limit must be an integer".to_owned())?;
            usize::try_from(n).map_err(|_| "lexicon: invalid limit".to_owned())?
        }
    };
    let after_key = parse_optional_filter_option(obj.get("after_key"))?;
    let res = search_runtime(
        prefix,
        &PrefixSearchOptions {
            limit,
            after_key,
            scope,
        },
    )?;
    serde_json::to_value(res).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_fuzzy_search"`.
pub fn execute_fuzzy_search(request: &Value, input: &Value) -> Result<Value, String> {
    let word = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, true)?;
    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    let limit = match obj.get("limit") {
        None | Some(Value::Null) => 10usize,
        Some(v) => {
            let n = v
                .as_u64()
                .ok_or_else(|| "lexicon: limit must be an integer".to_owned())?;
            usize::try_from(n).map_err(|_| "lexicon: invalid limit".to_owned())?
        }
    };
    let max_distance = match obj.get("max_distance") {
        None | Some(Value::Null) => 1u32,
        Some(v) => {
            let n = v
                .as_u64()
                .ok_or_else(|| "lexicon: max_distance must be an integer (1 or 2)".to_owned())?;
            u32::try_from(n).map_err(|_| "lexicon: invalid max_distance".to_owned())?
        }
    };
    let res = fuzzy_search_runtime(
        word,
        max_distance,
        &PrefixSearchOptions {
            limit,
            after_key: None,
            scope,
        },
    )?;
    serde_json::to_value(res).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_longest_prefix"`.
pub fn execute_longest_prefix(request: &Value, input: &Value) -> Result<Value, String> {
    let word = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, false)?;
    let prefixes = longest_prefix_runtime(word, &scope)?;
    Ok(json!({
        "query": word,
        "prefixes": prefixes,
    }))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_relations"`.
pub fn execute_relations(request: &Value, input: &Value) -> Result<Value, String> {
    let text = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, false)?;
    let res = relations_runtime(text, &scope)?;
    serde_json::to_value(res).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_define"`.
pub fn execute_define(request: &Value, input: &Value) -> Result<Value, String> {
    let text = input
        .as_str()
        .ok_or_else(|| "lexicon: input must be a string".to_owned())?;
    let scope = parse_query_scope(request, false)?;
    let res = define_runtime(text, &scope)?;
    serde_json::to_value(res).map_err(|err| format!("lexicon: serialize error: {err}"))
}

/// Shared JSON dispatcher entrypoint for `op = "lexicon_init"`.
///
/// Accepts `input` as:
/// - `null` (loads `"full"` profile from auto-discovered pack directory)
/// - a profile string (`"open-lite"`, `"open"`, `"local"`, `"full"`)
/// - an object `{ "profile"?: string, "path"?: string, "replace"?: bool }`
pub fn execute_init(input: &Value) -> Result<Value, String> {
    let (profile, path_opt, replace) = if input.is_null() {
        (LexiconProfile::Full, None, true)
    } else if let Some(profile_str) = input.as_str() {
        let profile = LexiconProfile::parse(profile_str)
            .ok_or_else(|| format!("lexicon: unknown profile '{profile_str}'"))?;
        (profile, None, true)
    } else if let Some(obj) = input.as_object() {
        for key in obj.keys() {
            if !matches!(key.as_str(), "profile" | "path" | "replace") {
                return Err("lexicon: invalid options".to_owned());
            }
        }
        let profile = match obj.get("profile") {
            None | Some(Value::Null) => LexiconProfile::Full,
            Some(Value::String(s)) => {
                LexiconProfile::parse(s).ok_or_else(|| format!("lexicon: unknown profile '{s}'"))?
            }
            _ => return Err("lexicon: invalid options".to_owned()),
        };
        let path_opt = match obj.get("path") {
            None | Some(Value::Null) => None,
            Some(Value::String(s)) if !s.trim().is_empty() => Some(s.clone()),
            _ => return Err("lexicon: path must be a nonempty string".to_owned()),
        };
        let replace = match obj.get("replace") {
            None | Some(Value::Null) => true,
            Some(Value::Bool(b)) => *b,
            _ => return Err("lexicon: invalid options".to_owned()),
        };
        (profile, path_opt, replace)
    } else {
        return Err("lexicon: init input must be null, a profile string, or an object".to_owned());
    };

    let (dir, loaded) = init_runtime(profile, path_opt.as_deref().map(Path::new), replace)?;
    let total_entries: u64 = loaded.iter().map(|p| u64::from(p.entry_count)).sum();
    let total_senses: u64 = loaded.iter().map(|p| u64::from(p.sense_count)).sum();
    let total_relations: u64 = loaded.iter().map(|p| u64::from(p.relation_count)).sum();
    let total_bytes: usize = loaded.iter().map(|p| p.byte_len).sum();
    Ok(json!({
        "directory": dir.to_string_lossy(),
        "profile": profile.as_str(),
        "pack_count": loaded.len(),
        "total_entries": total_entries,
        "total_senses": total_senses,
        "total_relations": total_relations,
        "total_bytes": total_bytes,
        "loaded": loaded,
    }))
}

pub(crate) fn parse_query_scope(request: &Value, allow_limit: bool) -> Result<QueryScope, String> {
    let obj = request
        .as_object()
        .ok_or_else(|| "lexicon: invalid options".to_owned())?;
    for key in obj.keys() {
        let ok = matches!(
            key.as_str(),
            "op" | "input"
                | "packs"
                | "tier"
                | "category"
                | "pos"
                | "domain"
                | "region"
                | "register"
                | "folded"
        ) || (allow_limit
            && matches!(key.as_str(), "limit" | "after_key" | "max_distance"));
        if !ok {
            return Err("lexicon: invalid options".to_owned());
        }
    }
    let packs = match obj.get("packs") {
        None | Some(Value::Null) => None,
        Some(raw) => Some(parse_packs_option(raw)?),
    };
    let tier = match obj.get("tier") {
        None | Some(Value::Null) => TierFilter::All,
        Some(Value::String(s)) => {
            TierFilter::parse(s).ok_or_else(|| format!("lexicon: unknown tier '{s}'"))?
        }
        _ => return Err("lexicon: invalid options".to_owned()),
    };
    let category = match obj.get("category") {
        None | Some(Value::Null) => None,
        Some(Value::String(s)) => Some(
            LexiconCategory::parse(s).ok_or_else(|| format!("lexicon: unknown category '{s}'"))?,
        ),
        _ => return Err("lexicon: invalid options".to_owned()),
    };
    let folded = match obj.get("folded") {
        None | Some(Value::Null) => false,
        Some(Value::Bool(b)) => *b,
        _ => return Err("lexicon: invalid options".to_owned()),
    };
    Ok(QueryScope {
        packs,
        tier,
        category,
        pos: parse_optional_filter_option(obj.get("pos"))?,
        domain: parse_optional_filter_option(obj.get("domain"))?,
        region: parse_optional_filter_option(obj.get("region"))?,
        register: parse_optional_filter_option(obj.get("register"))?,
        folded,
    })
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
