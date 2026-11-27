//! PostgreSQL extension (`pg_tamil`) providing thin SQL wrappers over `tamil-lexicon`.
//! All linguistic lookup, prefix/folded FST search, English reverse lookup, and pack loading
//! delegate to `tamil_lexicon::PackRegistry`.

use std::path::PathBuf;
use std::sync::{OnceLock, RwLock};

use pgrx::prelude::*;
use serde_json::json;
use tamil_lexicon::{
    auto_discover_pack_dir, LexiconProfile, LexiconStore, PackRegistry, PrefixSearchOptions,
    QueryScope,
};

pgrx::pg_module_magic!();

#[derive(Default)]
struct RegistryState {
    registry: PackRegistry,
    initialized: bool,
}

fn registry_lock() -> &'static RwLock<RegistryState> {
    static STATE: OnceLock<RwLock<RegistryState>> = OnceLock::new();
    STATE.get_or_init(|| RwLock::new(RegistryState::default()))
}

fn ensure_registry_ready() -> Result<(), String> {
    {
        let guard = registry_lock()
            .read()
            .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
        if guard.initialized {
            return Ok(());
        }
    }

    let mut guard = registry_lock()
        .write()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    if guard.initialized {
        return Ok(());
    }

    if let Some(dir) = auto_discover_pack_dir() {
        let _ = guard
            .registry
            .load_profile_from_dir(&dir, LexiconProfile::Full)?;
    }
    guard.initialized = true;
    Ok(())
}

fn parse_limit(limit: Option<i32>) -> Result<usize, String> {
    match limit {
        None => Ok(25),
        Some(n) if n > 0 => Ok(n as usize),
        Some(_) => Err("pg_tamil: limit must be a positive integer".to_owned()),
    }
}

fn serialize_json<T: serde::Serialize>(value: &T) -> Result<String, String> {
    serde_json::to_string(value).map_err(|err| format!("pg_tamil: JSON serialize error: {err}"))
}

fn init_impl(dir: Option<&str>, profile: Option<&str>) -> Result<String, String> {
    let parsed_profile = match profile.map(str::trim).filter(|s| !s.is_empty()) {
        None => LexiconProfile::Full,
        Some(raw) => LexiconProfile::parse(raw)
            .ok_or_else(|| format!("pg_tamil: unknown lexicon profile '{raw}'"))?,
    };

    let resolved_dir = match dir.map(str::trim).filter(|s| !s.is_empty()) {
        Some(raw) => PathBuf::from(raw),
        None => auto_discover_pack_dir().ok_or_else(|| {
            "pg_tamil: no .tlpack directory found (set TAMIL_LEXICON_DIR or pass dir)"
                .to_owned()
        })?,
    };

    let mut guard = registry_lock()
        .write()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    guard.registry.clear();
    let loaded = guard
        .registry
        .load_profile_from_dir(&resolved_dir, parsed_profile)?;
    if loaded.is_empty() {
        return Err(format!(
            "pg_tamil: no packs matching profile '{}' in '{}'",
            parsed_profile.as_str(),
            resolved_dir.display()
        ));
    }
    guard.initialized = true;

    let total_entries: u64 = loaded.iter().map(|p| u64::from(p.entry_count)).sum();
    let total_senses: u64 = loaded.iter().map(|p| u64::from(p.sense_count)).sum();
    let total_relations: u64 = loaded.iter().map(|p| u64::from(p.relation_count)).sum();
    let total_bytes: usize = loaded.iter().map(|p| p.byte_len).sum();

    serialize_json(&json!({
        "directory": resolved_dir.to_string_lossy(),
        "profile": parsed_profile.as_str(),
        "pack_count": loaded.len(),
        "total_entries": total_entries,
        "total_senses": total_senses,
        "total_relations": total_relations,
        "total_bytes": total_bytes,
        "loaded": loaded,
    }))
}

fn stats_impl() -> Result<String, String> {
    ensure_registry_ready()?;
    let guard = registry_lock()
        .read()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    serialize_json(&guard.registry.stats())
}

fn define_impl(word: &str, folded: Option<bool>) -> Result<String, String> {
    ensure_registry_ready()?;
    let scope = QueryScope {
        folded: folded.unwrap_or(false),
        ..QueryScope::default()
    };
    let guard = registry_lock()
        .read()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    let def = guard.registry.define(word, &scope)?;
    serialize_json(&def)
}

fn search_impl(prefix: &str, limit: Option<i32>, folded: Option<bool>) -> Result<String, String> {
    ensure_registry_ready()?;
    let options = PrefixSearchOptions {
        limit: parse_limit(limit)?,
        after_key: None,
        scope: QueryScope {
            folded: folded.unwrap_or(false),
            ..QueryScope::default()
        },
    };
    let guard = registry_lock()
        .read()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    let res = guard.registry.prefix_search(prefix, &options)?;
    serialize_json(&res)
}

fn search_english_impl(query: &str, limit: Option<i32>) -> Result<String, String> {
    ensure_registry_ready()?;
    let options = PrefixSearchOptions {
        limit: parse_limit(limit)?,
        after_key: None,
        scope: QueryScope::default(),
    };
    let guard = registry_lock()
        .read()
        .map_err(|_| "pg_tamil: lexicon registry lock poisoned".to_owned())?;
    let res = guard.registry.search_english(query, &options)?;
    serialize_json(&res)
}

fn unwrap_or_pg_error(res: Result<String, String>) -> String {
    match res {
        Ok(json) => json,
        Err(err) => pgrx::error!("{err}"),
    }
}

/// Initializes or reloads the backend-local `.tlpack` registry from `dir` (or auto-discovered
/// `TAMIL_LEXICON_DIR`) for `profile` (`open-lite`, `open`, `local`, or `full`).
#[pg_extern]
fn tamil_lexicon_init(dir: Option<&str>, profile: Option<&str>) -> String {
    unwrap_or_pg_error(init_impl(dir, profile))
}

/// Returns JSON `LexiconStoreStats` for all mounted `.tlpack` packs in the backend session.
#[pg_extern]
fn tamil_lexicon_stats() -> String {
    unwrap_or_pg_error(stats_impl())
}

/// Returns unified JSON `WordDefinition` for `word`, optionally with Mayangoli `folded` matching.
#[pg_extern]
fn tamil_define(word: &str, folded: Option<bool>) -> String {
    unwrap_or_pg_error(define_impl(word, folded))
}

/// Runs FST prefix search (exact NFC or Mayangoli `folded`) and returns JSON `LexiconPrefixSearchResult`.
#[pg_extern]
fn tamil_lexicon_search(prefix: &str, limit: Option<i32>, folded: Option<bool>) -> String {
    unwrap_or_pg_error(search_impl(prefix, limit, folded))
}

/// Runs reverse English-to-Tamil gloss/definition search and returns JSON `LexiconPrefixSearchResult`.
#[pg_extern]
fn tamil_lexicon_search_english(query: &str, limit: Option<i32>) -> String {
    unwrap_or_pg_error(search_english_impl(query, limit))
}
