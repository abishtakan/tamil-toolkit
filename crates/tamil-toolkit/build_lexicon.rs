//! Offline canonical lexicon pack validator and `.tlpack` compiler.
#![forbid(unsafe_code)]

use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

const PACK_MAGIC: [u8; 8] = *b"TMLPACK1";
const HEADER_SIZE: usize = 160;
const INDEX_FORMAT_VERSION: u32 = 1;
const SCHEMA_VERSION: u32 = 1;
#[allow(dead_code)]
pub const PACK_FLAG_COMPACT_INTERNED: u32 = 1;
const COMPACT_POOL_MAGIC: [u8; 8] = *b"TMLPOOL1";
const EXPECTED_FORMAT: &str = "tamil-toolkit-canonical-lexicon-v1";
const EXPECTED_CSV_ENCODING: &str = "json-string-utf8-v1";
const KNOWN_PACK_IDS: &[&str] = &["core", "terminology", "names_taxa", "regional"];
const CC_BY_SA_URL: &str = "https://creativecommons.org/licenses/by-sa/4.0/legalcode";
const CC_BY_SA_LEGALCODE_SHA256: &str =
    "28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5";
const CC_BY_SA_LEGALCODE_LF_SHA256: &str =
    "23ee78c8bae49cf08ea2f0c84945c66b987ebe4520881fb51b3dad4fb43d07c2";

const REQUIRED_BASE_FILES: &[&str] = &[
    "ATTRIBUTION_AND_TERMS.md",
    "assertions.csv",
    "decisions.csv",
    "entries.csv",
    "evidence.csv",
    "forms.csv",
    "identities.csv",
    "labels.csv",
    "pack_members.csv",
    "relations.csv",
    "schema.toml",
    "scopes.csv",
    "senses.csv",
    "sources.csv",
    "texts.csv",
    "unicode_exceptions.csv",
    "vocabularies.toml",
];

const SCHEMA_FILENAMES: &[&str] = &[
    "common.schema.json",
    "intake.schema.json",
    "lexical.schema.json",
    "review.schema.json",
];

const AUDIT_CONTROL_EXTRA_CPS: &[u32] = &[0x00AD, 0x200C, 0x200D, 0x2028, 0x2029, 0xFEFF];

/// Result of compiling one canonical lexicon pack directory into binary form.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledPackOutput {
    pub pack_id: String,
    pub dataset_version: String,
    pub schema_version: u32,
    pub index_format_version: u32,
    pub manifest_sha256: String,
    pub artifact_sha256: String,
    pub bytes: Vec<u8>,
}

/// Validates a canonical lexicon directory and compiles a `.tlpack` binary image.
pub fn compile_pack_dir(
    pack_dir: &Path,
    schemas_dir: Option<&Path>,
    expected_pack_id: Option<&str>,
) -> Result<CompiledPackOutput, String> {
    compile_pack_dir_with_flags(
        pack_dir,
        schemas_dir,
        expected_pack_id,
        PACK_FLAG_COMPACT_INTERNED,
    )
}

/// Validates a canonical lexicon directory and compiles a `.tlpack` binary image with explicit header flags.
#[allow(dead_code)]
pub fn compile_pack_dir_with_flags(
    pack_dir: &Path,
    schemas_dir: Option<&Path>,
    expected_pack_id: Option<&str>,
    flags: u32,
) -> Result<CompiledPackOutput, String> {
    if let Some(sdir) = schemas_dir {
        verify_schemas_dir(sdir)?;
    }

    let tracked_bytes = collect_and_verify_pack_dir(pack_dir)?;
    let packs_raw = read_plain_text_file(&pack_dir.join("packs.toml"), "packs.toml")?;
    let packs_doc: PacksToml =
        toml::from_str(&packs_raw).map_err(|err| format!("packs.toml parse error: {err}"))?;

    let schema_raw = text_from_tracked(&tracked_bytes, "schema.toml")?;
    let schema_doc: SchemaToml =
        toml::from_str(&schema_raw).map_err(|err| format!("schema.toml parse error: {err}"))?;

    let vocab_raw = text_from_tracked(&tracked_bytes, "vocabularies.toml")?;
    let vocab_doc: VocabulariesToml = toml::from_str(&vocab_raw)
        .map_err(|err| format!("vocabularies.toml parse error: {err}"))?;

    verify_manifests(
        &packs_doc,
        &schema_doc,
        &vocab_doc,
        &tracked_bytes,
        expected_pack_id,
    )?;

    let tables = parse_all_csv_tables(&tracked_bytes, &schema_doc, &packs_doc)?;
    verify_notices_and_sources(&tracked_bytes, &tables.sources)?;
    let validated = validate_review_and_unicode(&tables)?;
    let (meta, entries) =
        validate_structure_and_project(&packs_doc, &vocab_doc, &tables, &validated)?;

    let bytes = build_tlpack_binary_with_flags(&meta, &entries, flags)?;
    let artifact_sha256 = sha256_hex(&bytes);

    Ok(CompiledPackOutput {
        pack_id: packs_doc.pack_id,
        dataset_version: packs_doc.dataset_version,
        schema_version: packs_doc.schema_version,
        index_format_version: packs_doc.index_format_version,
        manifest_sha256: packs_doc.manifest_sha256,
        artifact_sha256,
        bytes,
    })
}

/// Validates cross-pack revision consistency across multiple compiled packs.
#[allow(dead_code)]
pub fn validate_cross_pack_revisions(
    revisions_by_pack: &[(&str, &BTreeMap<String, String>)],
) -> Result<(), String> {
    let mut seen: BTreeMap<&str, (&str, &str)> = BTreeMap::new();
    for (pack_id, map) in revisions_by_pack {
        for (entry_id, revision) in *map {
            if let Some((prev_pack, prev_rev)) = seen.get(entry_id.as_str()) {
                if *prev_rev != revision.as_str() {
                    return Err(format!(
                        "cross-pack revision conflict for {entry_id}: {prev_pack}={prev_rev}, {pack_id}={revision}"
                    ));
                }
            } else {
                seen.insert(entry_id.as_str(), (*pack_id, revision.as_str()));
            }
        }
    }
    Ok(())
}

/// Canonical ASCII-escaped sorted JSON serializer matching `tools/lexicon.py:json_text`.
pub fn canonical_ascii_json(value: &Value) -> Result<String, String> {
    let mut out = String::new();
    write_canonical_json(value, &mut out)?;
    Ok(out)
}

fn write_canonical_json(value: &Value, out: &mut String) -> Result<(), String> {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(true) => out.push_str("true"),
        Value::Bool(false) => out.push_str("false"),
        Value::Number(num) => {
            if let Some(f) = num.as_f64() {
                if !f.is_finite() {
                    return Err("non-finite JSON number forbidden".to_owned());
                }
            }
            out.push_str(&num.to_string());
        }
        Value::String(s) => write_python_ascii_json_string(s, out),
        Value::Array(items) => {
            out.push('[');
            for (idx, item) in items.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_canonical_json(item, out)?;
            }
            out.push(']');
        }
        Value::Object(map) => {
            out.push('{');
            let sorted: BTreeMap<&str, &Value> = map.iter().map(|(k, v)| (k.as_str(), v)).collect();
            for (idx, (k, v)) in sorted.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_python_ascii_json_string(k, out);
                out.push(':');
                write_canonical_json(v, out)?;
            }
            out.push('}');
        }
    }
    Ok(())
}

fn write_python_ascii_json_string(s: &str, out: &mut String) {
    out.push('"');
    for ch in s.chars() {
        let cp = ch as u32;
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\u{0008}' => out.push_str("\\b"),
            '\u{000C}' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            _ if cp < 0x20 => {
                out.push_str(&format!("\\u{cp:04x}"));
            }
            _ if cp <= 0x7E => out.push(ch),
            _ if cp <= 0xFFFF => {
                out.push_str(&format!("\\u{cp:04x}"));
            }
            _ => {
                let adj = cp - 0x1_0000;
                let hi = 0xD800 + (adj >> 10);
                let lo = 0xDC00 + (adj & 0x3FF);
                out.push_str(&format!("\\u{hi:04x}\\u{lo:04x}"));
            }
        }
    }
    out.push('"');
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut hex = String::with_capacity(64);
    for byte in digest {
        hex.push_str(&format!("{byte:02x}"));
    }
    hex
}

fn verify_schemas_dir(schemas_dir: &Path) -> Result<(), String> {
    let meta = fs::symlink_metadata(schemas_dir).map_err(|err| {
        format!(
            "schemas directory unavailable {}: {err}",
            schemas_dir.display()
        )
    })?;
    if meta.file_type().is_symlink() || !meta.is_dir() {
        return Err(format!(
            "schemas path must be a real directory: {}",
            schemas_dir.display()
        ));
    }
    for name in SCHEMA_FILENAMES {
        let path = schemas_dir.join(name);
        let fmeta = fs::symlink_metadata(&path)
            .map_err(|err| format!("missing schema file {name}: {err}"))?;
        if fmeta.file_type().is_symlink() || !fmeta.is_file() {
            return Err(format!("schema entry must be a regular file: {name}"));
        }
        let content = fs::read_to_string(&path)
            .map_err(|err| format!("unreadable UTF-8 schema {name}: {err}"))?;
        let _: Value = serde_json::from_str(&content)
            .map_err(|err| format!("invalid JSON schema {name}: {err}"))?;
    }
    Ok(())
}

fn collect_and_verify_pack_dir(pack_dir: &Path) -> Result<BTreeMap<String, Vec<u8>>, String> {
    let meta = fs::symlink_metadata(pack_dir)
        .map_err(|err| format!("pack directory unavailable {}: {err}", pack_dir.display()))?;
    if meta.file_type().is_symlink() || !meta.is_dir() {
        return Err(format!(
            "pack path must be a real directory: {}",
            pack_dir.display()
        ));
    }

    let mut actual_files = BTreeMap::new();
    walk_pack_dir_no_symlinks(pack_dir, pack_dir, &mut actual_files)?;

    if !actual_files.contains_key("packs.toml") {
        return Err("missing required packs.toml".to_owned());
    }
    actual_files.remove("packs.toml");

    let required_set: BTreeSet<&str> = REQUIRED_BASE_FILES.iter().copied().collect();
    let actual_set: BTreeSet<&str> = actual_files.keys().map(String::as_str).collect();
    let missing: Vec<&str> = required_set.difference(&actual_set).copied().collect();
    if !missing.is_empty() {
        return Err(format!(
            "pack directory missing required files: {missing:?}"
        ));
    }
    let extra: Vec<&str> = actual_set
        .difference(&required_set)
        .copied()
        .filter(|rel| {
            !(rel.starts_with("notices/") && (rel.ends_with(".md") || rel.ends_with(".toml")))
        })
        .collect();
    if !extra.is_empty() {
        return Err(format!(
            "pack directory contains unexpected untracked/non-notice files: {extra:?}"
        ));
    }
    Ok(actual_files)
}

fn walk_pack_dir_no_symlinks(
    root: &Path,
    dir: &Path,
    out: &mut BTreeMap<String, Vec<u8>>,
) -> Result<(), String> {
    let mut entries: Vec<_> = fs::read_dir(dir)
        .map_err(|err| format!("read_dir {} failed: {err}", dir.display()))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|err| format!("dir entry error in {}: {err}", dir.display()))?;
    entries.sort_by_key(|e| e.file_name());

    for entry in entries {
        let path = entry.path();
        let meta = fs::symlink_metadata(&path)
            .map_err(|err| format!("metadata failed {}: {err}", path.display()))?;
        if meta.file_type().is_symlink() {
            return Err(format!(
                "symlinks forbidden in pack dir: {}",
                path.display()
            ));
        }
        let rel = path
            .strip_prefix(root)
            .map_err(|_| "strip_prefix failed".to_owned())?;
        let rel_posix = rel
            .components()
            .map(|c| c.as_os_str().to_string_lossy().into_owned())
            .collect::<Vec<_>>()
            .join("/");
        if meta.is_dir() {
            if rel_posix != "notices" {
                return Err(format!("unexpected subdirectory in pack: {rel_posix}"));
            }
            walk_pack_dir_no_symlinks(root, &path, out)?;
        } else if meta.is_file() {
            validate_relative_path(&rel_posix)?;
            let bytes =
                fs::read(&path).map_err(|err| format!("failed reading {rel_posix}: {err}"))?;
            out.insert(rel_posix, bytes);
        } else {
            return Err(format!("unsupported filesystem entry type: {rel_posix}"));
        }
    }
    Ok(())
}

fn validate_relative_path(path: &str) -> Result<(), String> {
    if path.is_empty() || path.starts_with('/') || path.starts_with('\\') || path.contains('\\') {
        return Err(format!("invalid relative pack path: {path:?}"));
    }
    let bytes = path.as_bytes();
    if bytes.len() >= 2 && bytes[0].is_ascii_alphabetic() && bytes[1] == b':' {
        return Err(format!("drive-letter path forbidden: {path:?}"));
    }
    if path
        .split('/')
        .any(|seg| seg.is_empty() || seg == "." || seg == "..")
    {
        return Err(format!("path traversal segment forbidden: {path:?}"));
    }
    Ok(())
}

fn read_plain_text_file(path: &Path, label: &str) -> Result<String, String> {
    let bytes = fs::read(path).map_err(|err| format!("failed reading {label}: {err}"))?;
    validate_plain_utf8_no_bom_no_cr(&bytes, label)
}

fn text_from_tracked(
    tracked: &BTreeMap<String, Vec<u8>>,
    rel_path: &str,
) -> Result<String, String> {
    let bytes = tracked
        .get(rel_path)
        .ok_or_else(|| format!("missing tracked file {rel_path}"))?;
    validate_plain_utf8_no_bom_no_cr(bytes, rel_path)
}

fn validate_plain_utf8_no_bom_no_cr(bytes: &[u8], label: &str) -> Result<String, String> {
    if bytes.starts_with(&[0xEF, 0xBB, 0xBF]) {
        return Err(format!("{label}: UTF-8 BOM is forbidden"));
    }
    if bytes.contains(&b'\r') {
        return Err(format!("{label}: CR/CRLF line endings are forbidden"));
    }
    std::str::from_utf8(bytes)
        .map(str::to_owned)
        .map_err(|err| format!("{label}: invalid UTF-8: {err}"))
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PacksToml {
    schema_version: u32,
    pack_id: String,
    dataset_version: String,
    description: String,
    vocabulary_version: String,
    l3_pack_eligible: bool,
    l2_structural_accepted: bool,
    index_format_version: u32,
    manifest_sha256: String,
    entry_count: u32,
    sense_count: u32,
    form_count: u32,
    text_count: u32,
    relation_count: u32,
    assertion_count: u32,
    omitted_relation_count: u32,
    coverage: PackCoverageToml,
    entry_revisions: BTreeMap<String, String>,
    files: Vec<PackFileToml>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PackCoverageToml {
    language_ids: Vec<String>,
    region_codes: Vec<String>,
    register_codes: Vec<String>,
    unknown_region_entries: u64,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct PackFileToml {
    path: String,
    sha256: String,
    bytes: u64,
    rows: Option<u64>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
#[allow(dead_code)]
struct SchemaToml {
    schema_version: u32,
    format: String,
    csv_encoding: String,
    pack_id: String,
    lookup_id_pattern: String,
    undirected_lookup_directionality: String,
    acceptance_auto_source_nullable_actor: bool,
    acceptance_human_requires_nonempty_actor: bool,
    entry_provenance_rule: String,
    sense_provenance_rule: String,
    tables: BTreeMap<String, Vec<String>>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct VocabRegionToml {
    code: String,
    parent_code: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct VocabulariesToml {
    schema_version: u32,
    vocabulary_version: String,
    language_ids: Vec<String>,
    parts_of_speech: Vec<String>,
    relation_codes: Vec<String>,
    annotation_properties: Vec<String>,
    registers: Vec<String>,
    #[serde(default)]
    domains: Vec<String>,
    #[serde(default)]
    temporals: Vec<String>,
    #[serde(default)]
    varieties: Vec<String>,
    #[serde(default)]
    regions: Vec<VocabRegionToml>,
}

fn verify_manifests(
    packs: &PacksToml,
    schema: &SchemaToml,
    vocab: &VocabulariesToml,
    tracked: &BTreeMap<String, Vec<u8>>,
    expected_pack_id: Option<&str>,
) -> Result<(), String> {
    if packs.schema_version != SCHEMA_VERSION || schema.schema_version != SCHEMA_VERSION {
        return Err("unsupported schema_version".to_owned());
    }
    if vocab.schema_version != SCHEMA_VERSION {
        return Err("unsupported vocabularies schema_version".to_owned());
    }
    if packs.index_format_version != INDEX_FORMAT_VERSION {
        return Err(format!(
            "unsupported index_format_version {}",
            packs.index_format_version
        ));
    }
    if !KNOWN_PACK_IDS.contains(&packs.pack_id.as_str()) {
        return Err(format!("unknown pack_id {:?}", packs.pack_id));
    }
    if let Some(expected) = expected_pack_id {
        if packs.pack_id != expected {
            return Err(format!(
                "pack_id mismatch: expected {expected:?}, got {:?}",
                packs.pack_id
            ));
        }
    }
    if schema.pack_id != packs.pack_id {
        return Err("schema.toml pack_id disagrees with packs.toml".to_owned());
    }
    if schema.format != EXPECTED_FORMAT {
        return Err(format!("unsupported canonical format {:?}", schema.format));
    }
    if schema.csv_encoding != EXPECTED_CSV_ENCODING {
        return Err(format!(
            "unsupported csv_encoding {:?}",
            schema.csv_encoding
        ));
    }
    if !packs.l3_pack_eligible || packs.l2_structural_accepted {
        return Err(
            "pack must have l3_pack_eligible=true and l2_structural_accepted=false".to_owned(),
        );
    }
    if packs.dataset_version.trim().is_empty() || packs.description.trim().is_empty() {
        return Err("dataset_version and description must be nonempty".to_owned());
    }
    if packs.vocabulary_version != vocab.vocabulary_version || vocab.vocabulary_version.is_empty() {
        return Err("vocabulary_version mismatch or empty".to_owned());
    }
    if packs.entry_count == 0
        || packs.sense_count == 0
        || packs.form_count == 0
        || packs.text_count == 0
    {
        return Err("approved pack cannot have zero entries, senses, forms, or texts".to_owned());
    }
    if !is_sha256_hex(&packs.manifest_sha256) {
        return Err("manifest_sha256 must be 64 lowercase hex digits".to_owned());
    }

    let expected_tables = expected_table_headers();
    if schema.tables.len() != expected_tables.len() {
        return Err("schema.toml [tables] table set mismatch".to_owned());
    }
    for (name, cols) in &expected_tables {
        let actual = schema
            .tables
            .get(*name)
            .ok_or_else(|| format!("schema.toml missing table {name}"))?;
        if actual.iter().map(String::as_str).collect::<Vec<_>>() != *cols {
            return Err(format!("schema.toml columns mismatch for table {name}"));
        }
    }

    if packs.files.len() != tracked.len() {
        return Err(format!(
            "packs.toml [[files]] count {} != tracked count {}",
            packs.files.len(),
            tracked.len()
        ));
    }
    let mut seen_paths = BTreeSet::new();
    let mut manifest_items = Vec::with_capacity(packs.files.len());
    let mut prev_path: Option<&str> = None;

    for file in &packs.files {
        validate_relative_path(&file.path)?;
        if let Some(prev) = prev_path {
            if file.path.as_str() <= prev {
                return Err("packs.toml [[files]] must be strictly sorted by path".to_owned());
            }
        }
        prev_path = Some(&file.path);
        if !seen_paths.insert(file.path.clone()) {
            return Err(format!("duplicate path in packs.toml: {}", file.path));
        }
        let actual_bytes = tracked
            .get(&file.path)
            .ok_or_else(|| format!("packs.toml lists missing file {}", file.path))?;
        let actual_len = u64::try_from(actual_bytes.len()).map_err(|_| "file len exceeds u64")?;
        if file.bytes != actual_len {
            return Err(format!(
                "byte length mismatch for {}: manifest={}, actual={actual_len}",
                file.path, file.bytes
            ));
        }
        let actual_sha = sha256_hex(actual_bytes);
        if file.sha256 != actual_sha {
            return Err(format!(
                "sha256 mismatch for {}: manifest={}, actual={actual_sha}",
                file.path, file.sha256
            ));
        }
        if file.path.ends_with(".csv") && file.rows.is_none() {
            return Err(format!("missing CSV row count for {}", file.path));
        }
        manifest_items.push(serde_json::json!({
            "path": file.path,
            "sha256": file.sha256,
            "bytes": file.bytes,
        }));
    }

    let manifest_json = canonical_ascii_json(&Value::Array(manifest_items))?;
    let recomputed_manifest = sha256_hex(manifest_json.as_bytes());
    if recomputed_manifest != packs.manifest_sha256 {
        return Err(format!(
            "manifest_sha256 mismatch: expected {recomputed_manifest}, got {}",
            packs.manifest_sha256
        ));
    }

    for items in [
        &vocab.language_ids,
        &vocab.parts_of_speech,
        &vocab.relation_codes,
        &vocab.annotation_properties,
        &vocab.registers,
        &vocab.domains,
        &vocab.temporals,
        &vocab.varieties,
    ] {
        let mut uniq = HashSet::new();
        for code in items {
            if !is_valid_id(code) || !uniq.insert(code.as_str()) {
                return Err(format!("invalid or duplicate vocabulary item {code:?}"));
            }
        }
    }

    let mut region_parents: HashMap<&str, Option<&str>> = HashMap::new();
    for reg in &vocab.regions {
        if !is_valid_id(&reg.code) {
            return Err(format!(
                "invalid region code in vocabularies.toml: {:?}",
                reg.code
            ));
        }
        if region_parents
            .insert(reg.code.as_str(), reg.parent_code.as_deref())
            .is_some()
        {
            return Err(format!(
                "duplicate region code in vocabularies.toml: {:?}",
                reg.code
            ));
        }
        if let Some(parent) = reg.parent_code.as_deref() {
            if !is_valid_id(parent) {
                return Err(format!(
                    "invalid parent_code {:?} for region {:?}",
                    parent, reg.code
                ));
            }
        }
    }
    for reg in &vocab.regions {
        let mut seen = HashSet::new();
        seen.insert(reg.code.as_str());
        let mut cur = reg.parent_code.as_deref();
        while let Some(parent) = cur {
            if !seen.insert(parent) {
                return Err(format!(
                    "cycle in vocabularies.toml regions involving {:?}",
                    parent
                ));
            }
            let next = region_parents.get(parent).ok_or_else(|| {
                format!(
                    "unknown region parent_code {:?} in vocabularies.toml for {:?}",
                    parent, reg.code
                )
            })?;
            cur = *next;
        }
    }

    Ok(())
}

fn expected_table_headers() -> BTreeMap<&'static str, &'static [&'static str]> {
    BTreeMap::from([
        (
            "identities",
            &[
                "entity_id",
                "kind",
                "allocation_key",
                "lifecycle",
                "identity_decision_id",
            ][..],
        ),
        (
            "entries",
            &[
                "entry_id",
                "language_id",
                "variety_id",
                "canonical_form_id",
                "pos_assertion_id",
                "structural_kind",
                "revision",
            ][..],
        ),
        (
            "forms",
            &[
                "form_id",
                "entry_id",
                "representation",
                "role",
                "text_assertion_id",
                "convention_assertion_id",
            ][..],
        ),
        (
            "senses",
            &["sense_id", "entry_id", "display_order", "parent_sense_id"][..],
        ),
        (
            "texts",
            &[
                "text_id",
                "owner_kind",
                "owner_id",
                "component",
                "language_id",
                "text_assertion_id",
                "paired_translation_id",
                "cited_source_locator_json",
            ][..],
        ),
        (
            "relations",
            &[
                "relation_id",
                "source_kind",
                "source_id",
                "target_kind",
                "target_id",
                "relation_code_assertion_id",
                "directionality",
                "inverse_relation_id",
            ][..],
        ),
        (
            "assertions",
            &[
                "assertion_id",
                "subject_kind",
                "subject_id",
                "property_code",
                "value_state",
                "value_json",
                "origin",
                "source_fidelity_state",
                "ambiguity_state",
                "algorithm_reference",
                "convention_reference",
                "imported_status_json",
                "imported_confidence_json",
                "claim_revision_sha256",
            ][..],
        ),
        (
            "evidence",
            &[
                "assertion_id",
                "source_id",
                "source_record_id",
                "locator_json",
                "evidence_role",
                "extraction_version",
                "extraction_sha256",
            ][..],
        ),
        (
            "decisions",
            &[
                "decision_id",
                "assertion_id",
                "assertion_revision_sha256",
                "evidence_bundle_sha256",
                "outcome",
                "actor_type",
                "actor_id",
                "method_version",
                "decision_date",
                "note_json",
                "predecessor_decision_id",
            ][..],
        ),
        (
            "sources",
            &[
                "source_id",
                "label_json",
                "publication_json",
                "url_json",
                "edition_json",
                "locator_json",
                "snapshot_id",
                "retrieval_date_state",
                "retrieval_date_json",
                "extraction_method",
                "extraction_version",
                "evidence_verification_state",
                "reuse_basis_json",
                "reuse_state",
                "attribution_text_json",
                "attribution_reference_json",
            ][..],
        ),
        (
            "scopes",
            &[
                "subject_kind",
                "subject_id",
                "dimension",
                "state",
                "label_code",
                "supporting_assertion_id",
                "decision_id",
            ][..],
        ),
        (
            "labels",
            &[
                "registry_id",
                "registry_version",
                "code",
                "category",
                "display_label_json",
                "definition_json",
                "evidence_reference",
                "parent_code",
            ][..],
        ),
        (
            "unicode_exceptions",
            &[
                "assertion_id",
                "claim_revision_sha256",
                "value_sha256",
                "kind",
                "scalar_sequence",
                "scalar_position",
                "reason_json",
                "decision_id",
            ][..],
        ),
        (
            "pack_members",
            &[
                "pack_id",
                "entry_id",
                "included_revision",
                "relation_inclusion_policy",
            ][..],
        ),
    ])
}

#[derive(Debug)]
struct IdentityRow {
    entity_id: String,
    kind: String,
    lifecycle: String,
}

#[derive(Debug)]
struct EntryRow {
    entry_id: String,
    language_id: String,
    variety_id: Option<String>,
    canonical_form_id: String,
    pos_assertion_id: String,
    revision: String,
}

#[derive(Debug)]
struct FormRow {
    form_id: String,
    entry_id: String,
    representation: String,
    role: String,
    text_assertion_id: String,
    convention_assertion_id: Option<String>,
}

#[derive(Debug)]
struct SenseRow {
    sense_id: String,
    entry_id: String,
    display_order: u32,
    parent_sense_id: Option<String>,
}

#[derive(Debug)]
struct TextRow {
    text_id: String,
    owner_kind: String,
    owner_id: String,
    component: String,
    language_id: String,
    text_assertion_id: String,
    paired_translation_id: Option<String>,
}

#[derive(Debug)]
struct RelationRow {
    relation_id: String,
    source_kind: String,
    source_id: String,
    target_kind: String,
    target_id: String,
    relation_code_assertion_id: String,
    directionality: String,
    inverse_relation_id: Option<String>,
}

#[derive(Debug)]
struct AssertionRow {
    assertion_id: String,
    subject_kind: String,
    subject_id: String,
    property_code: String,
    value_state: String,
    value_json: Value,
    origin: String,
    source_fidelity_state: String,
    ambiguity_state: String,
    algorithm_reference: Option<String>,
    convention_reference: Option<String>,
    imported_status_json: Value,
    imported_confidence_json: Value,
    claim_revision_sha256: String,
}

#[derive(Debug)]
struct EvidenceRow {
    assertion_id: String,
    source_id: String,
    source_record_id: Option<String>,
    locator_json: String,
    evidence_role: String,
    extraction_version: String,
    extraction_sha256: String,
}

#[derive(Debug)]
struct DecisionRow {
    decision_id: String,
    assertion_id: String,
    assertion_revision_sha256: String,
    evidence_bundle_sha256: String,
    outcome: String,
    actor_type: String,
    actor_id: Option<String>,
    method_version: Option<String>,
    decision_date: String,
    predecessor_decision_id: Option<String>,
}

#[derive(Debug)]
struct SourceRow {
    source_id: String,
    label_json: String,
    url_json: Option<String>,
    evidence_verification_state: String,
    reuse_basis_json: Option<String>,
    reuse_state: String,
    attribution_text_json: Option<String>,
    attribution_reference_json: Option<String>,
}

#[derive(Debug)]
struct ScopeRow {
    subject_kind: String,
    subject_id: String,
    dimension: String,
    state: String,
    label_code: Option<String>,
    supporting_assertion_id: Option<String>,
    decision_id: Option<String>,
}

#[derive(Debug)]
struct LabelRow {
    registry_id: String,
    registry_version: String,
    code: String,
    category: String,
    display_label_json: String,
    definition_json: String,
    evidence_reference: String,
    parent_code: Option<String>,
}

#[derive(Debug)]
struct UnicodeExceptionRow {
    assertion_id: String,
    claim_revision_sha256: String,
    value_sha256: String,
    kind: String,
    scalar_sequence: Vec<u32>,
    scalar_position: usize,
    reason_json: String,
    decision_id: String,
}

#[derive(Debug)]
struct PackMemberRow {
    pack_id: String,
    entry_id: String,
    included_revision: String,
}

struct CanonicalTables {
    identities: Vec<IdentityRow>,
    entries: Vec<EntryRow>,
    forms: Vec<FormRow>,
    senses: Vec<SenseRow>,
    texts: Vec<TextRow>,
    relations: Vec<RelationRow>,
    assertions: Vec<AssertionRow>,
    evidence: Vec<EvidenceRow>,
    decisions: Vec<DecisionRow>,
    sources: Vec<SourceRow>,
    scopes: Vec<ScopeRow>,
    labels: Vec<LabelRow>,
    unicode_exceptions: Vec<UnicodeExceptionRow>,
    pack_members: Vec<PackMemberRow>,
}

fn read_csv_rows(
    tracked: &BTreeMap<String, Vec<u8>>,
    schema: &SchemaToml,
    packs: &PacksToml,
    table_name: &str,
) -> Result<Vec<Vec<String>>, String> {
    let filename = format!("{table_name}.csv");
    let raw = text_from_tracked(tracked, &filename)?;
    let expected_cols = schema
        .tables
        .get(table_name)
        .ok_or_else(|| format!("schema.toml missing table {table_name}"))?;

    let mut reader = csv::ReaderBuilder::new()
        .has_headers(false)
        .flexible(false)
        .from_reader(raw.as_bytes());
    let mut records = reader.records();
    let header = records
        .next()
        .ok_or_else(|| format!("{filename}: missing CSV header"))?
        .map_err(|err| format!("{filename}: header parse error: {err}"))?;
    let actual_cols: Vec<&str> = header.iter().collect();
    let expected_slice: Vec<&str> = expected_cols.iter().map(String::as_str).collect();
    if actual_cols != expected_slice {
        return Err(format!(
            "{filename}: header mismatch: expected {expected_slice:?}, got {actual_cols:?}"
        ));
    }

    let mut out = Vec::new();
    for (idx, rec_res) in records.enumerate() {
        let record =
            rec_res.map_err(|err| format!("{filename} row {}: CSV parse error: {err}", idx + 2))?;
        if record.len() != expected_cols.len() {
            return Err(format!(
                "{filename} row {}: column count {} != {}",
                idx + 2,
                record.len(),
                expected_cols.len()
            ));
        }
        out.push(record.iter().map(str::to_owned).collect());
    }

    if let Some(meta_file) = packs.files.iter().find(|f| f.path == filename) {
        let actual_rows = u64::try_from(out.len()).map_err(|_| "row count overflow")?;
        if meta_file.rows != Some(actual_rows) {
            return Err(format!(
                "{filename}: packs.toml rows={:?}, actual={actual_rows}",
                meta_file.rows
            ));
        }
    }
    Ok(out)
}

fn is_valid_id(val: &str) -> bool {
    let mut chars = val.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    first.is_ascii_alphabetic()
        && chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, '_' | '.' | ':' | '-'))
}

fn is_sha256_hex(val: &str) -> bool {
    val.len() == 64 && val.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

fn is_valid_iso_date(val: &str) -> bool {
    let b = val.as_bytes();
    if b.len() != 10 || b[4] != b'-' || b[7] != b'-' {
        return false;
    }
    let Ok(year) = val[0..4].parse::<u32>() else {
        return false;
    };
    let Ok(month) = val[5..7].parse::<u32>() else {
        return false;
    };
    let Ok(day) = val[8..10].parse::<u32>() else {
        return false;
    };
    if year == 0 || !(1..=12).contains(&month) || day == 0 {
        return false;
    }
    let max_day = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            let leap = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
            if leap {
                29
            } else {
                28
            }
        }
        _ => return false,
    };
    day <= max_day
}

fn parse_req_id(cell: &str, ctx: &str) -> Result<String, String> {
    if !is_valid_id(cell) {
        return Err(format!("{ctx}: invalid ID {cell:?}"));
    }
    Ok(cell.to_owned())
}

fn parse_opt_id(cell: &str, ctx: &str) -> Result<Option<String>, String> {
    if cell.is_empty() {
        return Ok(None);
    }
    parse_req_id(cell, ctx).map(Some)
}

fn parse_req_sha256(cell: &str, ctx: &str) -> Result<String, String> {
    if !is_sha256_hex(cell) {
        return Err(format!("{ctx}: invalid sha256 {cell:?}"));
    }
    Ok(cell.to_owned())
}

fn parse_req_nonempty_str(cell: &str, ctx: &str) -> Result<String, String> {
    if cell.is_empty() {
        return Err(format!("{ctx}: required nonempty string is empty"));
    }
    Ok(cell.to_owned())
}

fn parse_opt_nonempty_str(cell: &str, ctx: &str) -> Result<Option<String>, String> {
    if cell.is_empty() {
        return Ok(None);
    }
    parse_req_nonempty_str(cell, ctx).map(Some)
}

fn is_audit_control(cp: u32) -> bool {
    AUDIT_CONTROL_EXTRA_CPS.contains(&cp) || cp < 32 || (0x7F..=0x9F).contains(&cp)
}

fn decode_json_cell(raw_cell: &str, ctx: &str) -> Result<Value, String> {
    if raw_cell.is_empty() {
        return Err(format!("{ctx}: JSON cell cannot be empty"));
    }
    for (idx, ch) in raw_cell.chars().enumerate() {
        if is_audit_control(ch as u32) {
            return Err(format!(
                "{ctx}: raw unescaped control U+{:04X} at scalar {idx} forbidden in json-string-utf8-v1 cell",
                ch as u32
            ));
        }
    }
    serde_json::from_str::<Value>(raw_cell).map_err(|err| format!("{ctx}: JSON cell error: {err}"))
}

fn decode_req_json_str(raw_cell: &str, nonempty: bool, ctx: &str) -> Result<String, String> {
    match decode_json_cell(raw_cell, ctx)? {
        Value::String(s) => {
            if nonempty && s.is_empty() {
                return Err(format!("{ctx}: expected nonempty decoded JSON string"));
            }
            Ok(s)
        }
        other => Err(format!("{ctx}: expected JSON string, got {other}")),
    }
}

fn decode_opt_json_str(
    raw_cell: &str,
    nonempty: bool,
    ctx: &str,
) -> Result<Option<String>, String> {
    match decode_json_cell(raw_cell, ctx)? {
        Value::Null => Ok(None),
        Value::String(s) => {
            if nonempty && s.is_empty() {
                return Err(format!("{ctx}: expected nonempty string or null"));
            }
            Ok(Some(s))
        }
        other => Err(format!("{ctx}: expected JSON string or null, got {other}")),
    }
}

fn ensure_enum<'a>(val: &'a str, allowed: &[&str], ctx: &str) -> Result<&'a str, String> {
    if !allowed.contains(&val) {
        return Err(format!("{ctx}: invalid enum value {val:?}"));
    }
    Ok(val)
}

fn parse_all_csv_tables(
    tracked: &BTreeMap<String, Vec<u8>>,
    schema: &SchemaToml,
    packs: &PacksToml,
) -> Result<CanonicalTables, String> {
    let identities = read_csv_rows(tracked, schema, packs, "identities")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("identities row {}", i + 2);
            let entity_id = parse_req_id(&r[0], &ctx)?;
            ensure_enum(
                &r[1],
                &["entry", "form", "sense", "text", "relation", "assertion"],
                &ctx,
            )?;
            let _alloc = parse_req_nonempty_str(&r[2], &ctx)?;
            ensure_enum(&r[3], &["active", "retired", "merged", "split"], &ctx)?;
            let _dec = parse_opt_id(&r[4], &ctx)?;
            Ok(IdentityRow {
                entity_id,
                kind: r[1].clone(),
                lifecycle: r[3].clone(),
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let entries = read_csv_rows(tracked, schema, packs, "entries")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("entries row {}", i + 2);
            Ok(EntryRow {
                entry_id: parse_req_id(&r[0], &ctx)?,
                language_id: parse_req_id(&r[1], &ctx)?,
                variety_id: parse_opt_id(&r[2], &ctx)?,
                canonical_form_id: parse_req_id(&r[3], &ctx)?,
                pos_assertion_id: parse_req_id(&r[4], &ctx)?,
                revision: parse_req_sha256(&r[6], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let forms = read_csv_rows(tracked, schema, packs, "forms")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("forms row {}", i + 2);
            ensure_enum(&r[2], &["written", "romanization", "ipa"], &ctx)?;
            ensure_enum(&r[3], &["canonical", "variant"], &ctx)?;
            Ok(FormRow {
                form_id: parse_req_id(&r[0], &ctx)?,
                entry_id: parse_req_id(&r[1], &ctx)?,
                representation: r[2].clone(),
                role: r[3].clone(),
                text_assertion_id: parse_req_id(&r[4], &ctx)?,
                convention_assertion_id: parse_opt_id(&r[5], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let senses = read_csv_rows(tracked, schema, packs, "senses")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("senses row {}", i + 2);
            let display_order: u32 = r[2]
                .parse()
                .map_err(|_| format!("{ctx}: invalid display_order {:?}", r[2]))?;
            if display_order == 0 {
                return Err(format!("{ctx}: display_order must be >= 1"));
            }
            Ok(SenseRow {
                sense_id: parse_req_id(&r[0], &ctx)?,
                entry_id: parse_req_id(&r[1], &ctx)?,
                display_order,
                parent_sense_id: parse_opt_id(&r[3], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let texts = read_csv_rows(tracked, schema, packs, "texts")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("texts row {}", i + 2);
            ensure_enum(&r[1], &["entry", "sense"], &ctx)?;
            ensure_enum(
                &r[3],
                &[
                    "definition",
                    "gloss",
                    "translation",
                    "example",
                    "citation",
                    "unparsed",
                ],
                &ctx,
            )?;
            let _cited = decode_opt_json_str(&r[7], true, &ctx)?;
            Ok(TextRow {
                text_id: parse_req_id(&r[0], &ctx)?,
                owner_kind: r[1].clone(),
                owner_id: parse_req_id(&r[2], &ctx)?,
                component: r[3].clone(),
                language_id: parse_req_id(&r[4], &ctx)?,
                text_assertion_id: parse_req_id(&r[5], &ctx)?,
                paired_translation_id: parse_opt_id(&r[6], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let relations = read_csv_rows(tracked, schema, packs, "relations")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("relations row {}", i + 2);
            ensure_enum(&r[1], &["entry", "sense"], &ctx)?;
            ensure_enum(&r[3], &["entry", "sense"], &ctx)?;
            ensure_enum(&r[6], &["directed", "undirected"], &ctx)?;
            Ok(RelationRow {
                relation_id: parse_req_id(&r[0], &ctx)?,
                source_kind: r[1].clone(),
                source_id: parse_req_id(&r[2], &ctx)?,
                target_kind: r[3].clone(),
                target_id: parse_req_id(&r[4], &ctx)?,
                relation_code_assertion_id: parse_req_id(&r[5], &ctx)?,
                directionality: r[6].clone(),
                inverse_relation_id: parse_opt_id(&r[7], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let assertions = read_csv_rows(tracked, schema, packs, "assertions")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("assertions row {}", i + 2);
            ensure_enum(
                &r[1],
                &["entry", "form", "sense", "text", "relation", "assertion"],
                &ctx,
            )?;
            ensure_enum(&r[4], &["known", "unknown", "not_applicable"], &ctx)?;
            let value_json = decode_json_cell(&r[5], &ctx)?;
            if r[4] == "known" && value_json.is_null() {
                return Err(format!(
                    "{ctx}: known value_state requires non-null value_json"
                ));
            }
            if r[4] != "known" && !value_json.is_null() {
                return Err(format!(
                    "{ctx}: non-known value_state requires null value_json"
                ));
            }
            ensure_enum(
                &r[6],
                &[
                    "verbatim_source",
                    "correction",
                    "inferred",
                    "derived",
                    "editorial",
                ],
                &ctx,
            )?;
            ensure_enum(
                &r[7],
                &["unknown", "unverified", "verified", "changed"],
                &ctx,
            )?;
            ensure_enum(&r[8], &["unknown", "unambiguous", "ambiguous"], &ctx)?;
            let imported_status_json = decode_json_cell(&r[11], &ctx)?;
            let imported_confidence_json = decode_json_cell(&r[12], &ctx)?;
            Ok(AssertionRow {
                assertion_id: parse_req_id(&r[0], &ctx)?,
                subject_kind: r[1].clone(),
                subject_id: parse_req_id(&r[2], &ctx)?,
                property_code: parse_req_id(&r[3], &ctx)?,
                value_state: r[4].clone(),
                value_json,
                origin: r[6].clone(),
                source_fidelity_state: r[7].clone(),
                ambiguity_state: r[8].clone(),
                algorithm_reference: parse_opt_id(&r[9], &ctx)?,
                convention_reference: parse_opt_id(&r[10], &ctx)?,
                imported_status_json,
                imported_confidence_json,
                claim_revision_sha256: parse_req_sha256(&r[13], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let evidence = read_csv_rows(tracked, schema, packs, "evidence")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("evidence row {}", i + 2);
            ensure_enum(&r[4], &["supports", "contradicts", "transcribes"], &ctx)?;
            Ok(EvidenceRow {
                assertion_id: parse_req_id(&r[0], &ctx)?,
                source_id: parse_req_id(&r[1], &ctx)?,
                source_record_id: parse_opt_id(&r[2], &ctx)?,
                locator_json: decode_req_json_str(&r[3], true, &ctx)?,
                evidence_role: r[4].clone(),
                extraction_version: parse_req_nonempty_str(&r[5], &ctx)?,
                extraction_sha256: parse_req_sha256(&r[6], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let decisions = read_csv_rows(tracked, schema, packs, "decisions")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("decisions row {}", i + 2);
            ensure_enum(
                &r[4],
                &[
                    "pending",
                    "accepted_auto_source",
                    "accepted_human",
                    "rejected",
                    "needs_review",
                ],
                &ctx,
            )?;
            ensure_enum(&r[5], &["human", "automated"], &ctx)?;
            let actor_id = parse_opt_id(&r[6], &ctx)?;
            let method_version = parse_opt_nonempty_str(&r[7], &ctx)?;
            if !is_valid_iso_date(&r[8]) {
                return Err(format!("{ctx}: invalid decision_date {:?}", r[8]));
            }
            let _note = decode_req_json_str(&r[9], false, &ctx)?;
            Ok(DecisionRow {
                decision_id: parse_req_id(&r[0], &ctx)?,
                assertion_id: parse_req_id(&r[1], &ctx)?,
                assertion_revision_sha256: parse_req_sha256(&r[2], &ctx)?,
                evidence_bundle_sha256: parse_req_sha256(&r[3], &ctx)?,
                outcome: r[4].clone(),
                actor_type: r[5].clone(),
                actor_id,
                method_version,
                decision_date: r[8].clone(),
                predecessor_decision_id: parse_opt_id(&r[10], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let sources = read_csv_rows(tracked, schema, packs, "sources")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("sources row {}", i + 2);
            let _pub = decode_opt_json_str(&r[2], false, &ctx)?;
            let _edition = decode_opt_json_str(&r[4], false, &ctx)?;
            let _loc = decode_opt_json_str(&r[5], true, &ctx)?;
            let _snap = parse_opt_id(&r[6], &ctx)?;
            ensure_enum(&r[7], &["known", "unknown", "not_applicable"], &ctx)?;
            let _rdate = decode_opt_json_str(&r[8], false, &ctx)?;
            let _em = parse_opt_nonempty_str(&r[9], &ctx)?;
            let _ev = parse_opt_nonempty_str(&r[10], &ctx)?;
            ensure_enum(
                &r[11],
                &["unknown", "unverified", "verified", "failed"],
                &ctx,
            )?;
            ensure_enum(
                &r[13],
                &["unknown", "permitted", "restricted", "prohibited"],
                &ctx,
            )?;
            Ok(SourceRow {
                source_id: parse_req_id(&r[0], &ctx)?,
                label_json: decode_req_json_str(&r[1], true, &ctx)?,
                url_json: decode_opt_json_str(&r[3], false, &ctx)?,
                evidence_verification_state: r[11].clone(),
                reuse_basis_json: decode_opt_json_str(&r[12], true, &ctx)?,
                reuse_state: r[13].clone(),
                attribution_text_json: decode_opt_json_str(&r[14], false, &ctx)?,
                attribution_reference_json: decode_opt_json_str(&r[15], true, &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let scopes = read_csv_rows(tracked, schema, packs, "scopes")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("scopes row {}", i + 2);
            ensure_enum(
                &r[0],
                &["entry", "sense", "form", "text", "relation", "assertion"],
                &ctx,
            )?;
            ensure_enum(
                &r[2],
                &[
                    "region",
                    "register",
                    "domain",
                    "social_usage",
                    "period",
                    "grammar_system",
                ],
                &ctx,
            )?;
            if r[2] == "register" {
                ensure_enum(
                    &r[3],
                    &["attested", "unrestricted", "unknown", "not_applicable"],
                    &ctx,
                )?;
            } else {
                ensure_enum(&r[3], &["attested", "unrestricted", "unknown"], &ctx)?;
            }
            let label_code = parse_opt_id(&r[4], &ctx)?;
            let supporting_assertion_id = parse_opt_id(&r[5], &ctx)?;
            let decision_id = parse_opt_id(&r[6], &ctx)?;
            match r[3].as_str() {
                "attested" => {
                    if label_code.is_none()
                        || supporting_assertion_id.is_none()
                        || decision_id.is_none()
                    {
                        return Err(format!(
                            "{ctx}: attested scope requires label, assertion, decision"
                        ));
                    }
                }
                "unrestricted" => {
                    if label_code.is_some()
                        || supporting_assertion_id.is_none()
                        || decision_id.is_none()
                    {
                        return Err(format!(
                            "{ctx}: unrestricted scope forbids label and requires evidence"
                        ));
                    }
                }
                "not_applicable" => {
                    if label_code.is_some() {
                        return Err(format!("{ctx}: not_applicable scope forbids label_code"));
                    }
                }
                _ => {
                    if label_code.is_some() {
                        return Err(format!("{ctx}: unknown scope forbids label_code"));
                    }
                }
            }
            Ok(ScopeRow {
                subject_kind: r[0].clone(),
                subject_id: parse_req_id(&r[1], &ctx)?,
                dimension: r[2].clone(),
                state: r[3].clone(),
                label_code,
                supporting_assertion_id,
                decision_id,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let labels = read_csv_rows(tracked, schema, packs, "labels")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("labels row {}", i + 2);
            ensure_enum(
                &r[3],
                &[
                    "region",
                    "register",
                    "domain",
                    "social_usage",
                    "period",
                    "grammar_system",
                ],
                &ctx,
            )?;
            Ok(LabelRow {
                registry_id: parse_req_id(&r[0], &ctx)?,
                registry_version: parse_req_nonempty_str(&r[1], &ctx)?,
                code: parse_req_id(&r[2], &ctx)?,
                category: r[3].clone(),
                display_label_json: decode_req_json_str(&r[4], true, &ctx)?,
                definition_json: decode_req_json_str(&r[5], true, &ctx)?,
                evidence_reference: parse_req_id(&r[6], &ctx)?,
                parent_code: parse_opt_id(&r[7], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let unicode_exceptions = read_csv_rows(tracked, schema, packs, "unicode_exceptions")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("unicode_exceptions row {}", i + 2);
            ensure_enum(&r[3], &["non_nfc_original", "intentional_control"], &ctx)?;
            let seq_val = decode_json_cell(&r[4], &ctx)?;
            let arr = seq_val
                .as_array()
                .ok_or_else(|| format!("{ctx}: scalar_sequence must be array"))?;
            if arr.is_empty() {
                return Err(format!("{ctx}: scalar_sequence cannot be empty"));
            }
            let mut seq = Vec::with_capacity(arr.len());
            for item in arr {
                let cp_i64 = item
                    .as_i64()
                    .ok_or_else(|| format!("{ctx}: scalar codepoint must be int"))?;
                let cp = u32::try_from(cp_i64)
                    .map_err(|_| format!("{ctx}: invalid scalar codepoint {cp_i64}"))?;
                if cp > 0x10_FFFF || (0xD800..=0xDFFF).contains(&cp) {
                    return Err(format!("{ctx}: invalid Unicode scalar {cp:#x}"));
                }
                seq.push(cp);
            }
            let pos_val = decode_json_cell(&r[5], &ctx)?;
            let pos_u64 = pos_val
                .as_u64()
                .ok_or_else(|| format!("{ctx}: scalar_position must be unsigned int"))?;
            let scalar_position =
                usize::try_from(pos_u64).map_err(|_| format!("{ctx}: scalar_position overflow"))?;
            Ok(UnicodeExceptionRow {
                assertion_id: parse_req_id(&r[0], &ctx)?,
                claim_revision_sha256: parse_req_sha256(&r[1], &ctx)?,
                value_sha256: parse_req_sha256(&r[2], &ctx)?,
                kind: r[3].clone(),
                scalar_sequence: seq,
                scalar_position,
                reason_json: decode_req_json_str(&r[6], true, &ctx)?,
                decision_id: parse_req_id(&r[7], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    let pack_members = read_csv_rows(tracked, schema, packs, "pack_members")?
        .into_iter()
        .enumerate()
        .map(|(i, r)| {
            let ctx = format!("pack_members row {}", i + 2);
            let _pol = parse_opt_nonempty_str(&r[3], &ctx)?;
            Ok(PackMemberRow {
                pack_id: parse_req_id(&r[0], &ctx)?,
                entry_id: parse_req_id(&r[1], &ctx)?,
                included_revision: parse_req_sha256(&r[2], &ctx)?,
            })
        })
        .collect::<Result<Vec<_>, String>>()?;

    Ok(CanonicalTables {
        identities,
        entries,
        forms,
        senses,
        texts,
        relations,
        assertions,
        evidence,
        decisions,
        sources,
        scopes,
        labels,
        unicode_exceptions,
        pack_members,
    })
}

fn has_windows_path(text: &str) -> bool {
    let bytes = text.as_bytes();
    for i in 0..bytes.len() {
        // UNC path: \\<host>\<share>
        if i + 3 < bytes.len() && bytes[i] == b'\\' && bytes[i + 1] == b'\\' {
            let mut j = i + 2;
            while j < bytes.len()
                && (bytes[j].is_ascii_alphanumeric() || matches!(bytes[j], b'_' | b'.' | b'-'))
            {
                j += 1;
            }
            if j > i + 2 && j < bytes.len() && bytes[j] == b'\\' {
                return true;
            }
        }
        // Drive-letter path: (?<![A-Za-z0-9+.-])[A-Za-z]:(\\|/)
        if i + 2 < bytes.len()
            && bytes[i].is_ascii_alphabetic()
            && bytes[i + 1] == b':'
            && (bytes[i + 2] == b'\\' || bytes[i + 2] == b'/')
        {
            let prev_ok = i == 0
                || !(bytes[i - 1].is_ascii_alphanumeric()
                    || matches!(bytes[i - 1], b'+' | b'.' | b'-'));
            if prev_ok {
                return true;
            }
        }
    }
    false
}

fn has_private_notice_json_ref(text: &str) -> bool {
    let lower = text.to_ascii_lowercase();
    let bytes = lower.as_bytes();
    let needle = b".json";
    let mut pos = 0;
    while let Some(rel) = lower[pos..].find(".json") {
        let idx = pos + rel;
        let after = idx + needle.len();
        let after_ok =
            after >= bytes.len() || !(bytes[after].is_ascii_alphanumeric() || bytes[after] == b'_');
        if after_ok {
            let mut start = idx;
            while start > 0
                && (bytes[start - 1].is_ascii_alphanumeric()
                    || matches!(bytes[start - 1], b'_' | b'.' | b'-'))
            {
                start -= 1;
            }
            let prefix = &lower[start..idx];
            if prefix == "fetch_manifest" || (prefix.len() > 4 && prefix.ends_with("_api")) {
                return true;
            }
        }
        pos = idx + 1;
    }
    false
}

fn check_public_notice_safety(text: &str, filename: &str) -> Result<(), String> {
    if text.trim().is_empty() {
        return Err(format!("{filename}: notice file cannot be empty"));
    }
    if tamil_norm::normalize_nfc(text) != text {
        return Err(format!("{filename}: notice must be UTF-8 NFC normalized"));
    }
    if has_windows_path(text) {
        return Err(format!("{filename}: notice exposes local Windows/UNC path"));
    }
    if has_private_notice_json_ref(text) {
        return Err(format!(
            "{filename}: notice references private editorial JSON"
        ));
    }
    let lowered = text.to_ascii_lowercase();
    for forbidden in [
        "data/curation",
        "data\\curation",
        "data/sources",
        "data\\sources",
        "/tmp/",
        ".jsonl",
    ] {
        if lowered.contains(forbidden) {
            return Err(format!(
                "{filename}: contains forbidden private/host reference {forbidden:?}"
            ));
        }
    }
    Ok(())
}

enum AttributionRefKind {
    Url,
    LocalFile(String),
    Bibliographic,
    Unsafe,
}

fn classify_attribution_ref(raw: &str) -> AttributionRefKind {
    let s = raw.trim();
    let lower = s.to_ascii_lowercase();
    if lower.starts_with("https://")
        || lower.starts_with("http://")
        || lower.starts_with("mailto:")
        || lower.starts_with("urn:")
    {
        return AttributionRefKind::Url;
    }
    if lower.starts_with("file:")
        || (s.len() >= 2 && s.as_bytes()[0].is_ascii_alphabetic() && s.as_bytes()[1] == b':')
        || s.starts_with('/')
        || s.starts_with('\\')
        || s.contains('\\')
    {
        return AttributionRefKind::Unsafe;
    }
    let filename = s.rsplit('/').next().unwrap_or(s);
    let suffix_lower = filename
        .rfind('.')
        .map(|dot| filename[dot..].to_ascii_lowercase())
        .unwrap_or_default();
    let file_like = matches!(
        suffix_lower.as_str(),
        ".md" | ".txt" | ".toml" | ".csv" | ".json" | ".rst" | ".html" | ".htm"
    );
    if s.contains('/') || s.starts_with('.') || file_like {
        if validate_relative_path(s).is_err() {
            return AttributionRefKind::Unsafe;
        }
        if (suffix_lower != ".md" && suffix_lower != ".toml")
            || has_private_notice_json_ref(s)
            || lower.ends_with(".json")
        {
            return AttributionRefKind::Unsafe;
        }
        return AttributionRefKind::LocalFile(s.to_owned());
    }
    AttributionRefKind::Bibliographic
}

fn resolve_markdown_ref(raw: &str) -> &str {
    if let Some(open) = raw.find("](") {
        if let Some(close) = raw[open + 2..].find(')') {
            return &raw[open + 2..open + 2 + close];
        }
    }
    raw
}

fn contains_cc_by_sa_closure(doc: &str) -> bool {
    let has_label = doc.contains("CC-BY-SA-4.0");
    let has_url = doc.contains(CC_BY_SA_URL);
    let has_hash =
        doc.contains(CC_BY_SA_LEGALCODE_SHA256) || doc.contains(CC_BY_SA_LEGALCODE_LF_SHA256);
    has_label && has_url && has_hash
}

fn verify_pinned_cc_by_sa_markdown(cc_text: &str) -> Result<(), String> {
    if !cc_text.contains(CC_BY_SA_URL) {
        return Err("notices/CC-BY-SA-4.0.md missing canonical license URI".to_owned());
    }
    if !cc_text.contains("Attribution-ShareAlike 4.0 International") {
        return Err("notices/CC-BY-SA-4.0.md missing license text header".to_owned());
    }
    let cc_lf = cc_text.replace("\r\n", "\n").replace('\r', "\n");
    let body_lf = cc_lf
        .split_once("\n---\n\n")
        .map(|(_, b)| b)
        .ok_or_else(|| "notices/CC-BY-SA-4.0.md missing pinned header/body separator".to_owned())?;
    let body_lf_hash = sha256_hex(body_lf.as_bytes());
    let body_raw_hash = cc_text
        .split_once("\n---\n\n")
        .or_else(|| cc_text.split_once("\r\n---\r\n\r\n"))
        .map(|(_, b)| sha256_hex(b.as_bytes()));
    if body_lf_hash != CC_BY_SA_LEGALCODE_LF_SHA256
        && body_raw_hash.as_deref() != Some(CC_BY_SA_LEGALCODE_SHA256)
    {
        return Err(
            "notices/CC-BY-SA-4.0.md legal text body does not match pinned CC-BY-SA-4.0 SHA-256"
                .to_owned(),
        );
    }
    Ok(())
}

fn verify_notices_and_sources(
    tracked: &BTreeMap<String, Vec<u8>>,
    sources: &[SourceRow],
) -> Result<(), String> {
    let terms = text_from_tracked(tracked, "ATTRIBUTION_AND_TERMS.md")?;
    check_public_notice_safety(&terms, "ATTRIBUTION_AND_TERMS.md")?;

    for rel in tracked.keys() {
        if rel.starts_with("notices/") && (rel.ends_with(".md") || rel.ends_with(".toml")) {
            let notice_txt = text_from_tracked(tracked, rel)?;
            check_public_notice_safety(&notice_txt, rel)?;
        }
    }

    if tracked.contains_key("notices/CC-BY-SA-4.0.md") {
        let cc_text = text_from_tracked(tracked, "notices/CC-BY-SA-4.0.md")?;
        verify_pinned_cc_by_sa_markdown(&cc_text)?;
    }

    if sources.is_empty() {
        return Err("approved pack must declare at least one verified source".to_owned());
    }
    let mut seen_sources = HashSet::new();
    let mut needs_cc_legal_file = false;
    for src in sources {
        if !seen_sources.insert(src.source_id.as_str()) {
            return Err(format!("duplicate source_id {}", src.source_id));
        }
        if src.evidence_verification_state != "verified" {
            return Err(format!(
                "source {} is not verified ({})",
                src.source_id, src.evidence_verification_state
            ));
        }
        if src.reuse_state != "permitted" {
            return Err(format!(
                "source {} reuse_state is not permitted ({})",
                src.source_id, src.reuse_state
            ));
        }
        let basis = src
            .reuse_basis_json
            .as_deref()
            .filter(|s| !s.trim().is_empty())
            .ok_or_else(|| format!("source {} missing reuse_basis", src.source_id))?;
        let attr_text = src
            .attribution_text_json
            .as_deref()
            .map(str::trim)
            .filter(|s| !s.is_empty());
        let attr_ref_raw = src
            .attribution_reference_json
            .as_deref()
            .map(str::trim)
            .filter(|s| !s.is_empty());
        if attr_text.is_none() && attr_ref_raw.is_none() {
            return Err(format!(
                "source {} requires attribution_text or attribution_reference",
                src.source_id
            ));
        }
        if !terms.contains(&src.source_id) {
            return Err(format!(
                "ATTRIBUTION_AND_TERMS.md missing attribution closure for {}",
                src.source_id
            ));
        }
        if let Some(txt) = attr_text {
            if !terms.contains(txt) {
                return Err(format!(
                    "ATTRIBUTION_AND_TERMS.md missing attribution text for {}",
                    src.source_id
                ));
            }
        }
        let is_cc_by_sa = basis.to_ascii_lowercase().contains("cc-by-sa-4.0");
        if is_cc_by_sa {
            needs_cc_legal_file = true;
            if !contains_cc_by_sa_closure(&terms) {
                return Err(
                    "ATTRIBUTION_AND_TERMS.md missing CC-BY-SA-4.0 legalcode URI or SHA-256 closure"
                        .to_owned(),
                );
            }
        }
        if let Some(raw_ref) = attr_ref_raw {
            let resolved_ref = resolve_markdown_ref(raw_ref);
            match classify_attribution_ref(resolved_ref) {
                AttributionRefKind::Unsafe => {
                    return Err(format!(
                        "source {} has unsafe or non-canonical attribution_reference {resolved_ref:?}",
                        src.source_id
                    ));
                }
                AttributionRefKind::LocalFile(rel) => {
                    if !tracked.contains_key(&rel) {
                        return Err(format!(
                            "source {} attribution_reference {rel:?} missing from pack",
                            src.source_id
                        ));
                    }
                    if is_cc_by_sa {
                        let local_doc = text_from_tracked(tracked, &rel)?;
                        if !contains_cc_by_sa_closure(&local_doc) {
                            return Err(format!(
                                "public notice {rel:?} missing CC-BY-SA-4.0 legalcode URI or SHA-256 closure"
                            ));
                        }
                    }
                }
                AttributionRefKind::Url | AttributionRefKind::Bibliographic => {}
            }
        }
    }
    if needs_cc_legal_file && !tracked.contains_key("notices/CC-BY-SA-4.0.md") {
        return Err("CC-BY-SA-4.0 source missing legal notice file".to_owned());
    }
    Ok(())
}

struct AcceptedDecisionInfo<'a> {
    decision: &'a DecisionRow,
    evidence: Vec<&'a EvidenceRow>,
}

struct ValidatedReview<'a> {
    assertions_by_id: HashMap<&'a str, &'a AssertionRow>,
    accepted_by_assertion: HashMap<&'a str, AcceptedDecisionInfo<'a>>,
}

fn validate_review_and_unicode<'a>(
    tables: &'a CanonicalTables,
) -> Result<ValidatedReview<'a>, String> {
    let sources_by_id: HashMap<&str, &SourceRow> = tables
        .sources
        .iter()
        .map(|s| (s.source_id.as_str(), s))
        .collect();

    let mut evidence_by_aid: HashMap<&str, Vec<&EvidenceRow>> = HashMap::new();
    for ev in &tables.evidence {
        if !sources_by_id.contains_key(ev.source_id.as_str()) {
            return Err(format!(
                "evidence references unknown source {}",
                ev.source_id
            ));
        }
        evidence_by_aid
            .entry(ev.assertion_id.as_str())
            .or_default()
            .push(ev);
    }

    let mut decisions_by_id: HashMap<&str, &DecisionRow> = HashMap::new();
    let mut decisions_by_aid: HashMap<&str, Vec<&DecisionRow>> = HashMap::new();
    for dec in &tables.decisions {
        if decisions_by_id
            .insert(dec.decision_id.as_str(), dec)
            .is_some()
        {
            return Err(format!("duplicate decision_id {}", dec.decision_id));
        }
        decisions_by_aid
            .entry(dec.assertion_id.as_str())
            .or_default()
            .push(dec);
    }

    let mut assertions_by_id: HashMap<&str, &AssertionRow> = HashMap::new();
    let mut accepted_by_assertion: HashMap<&str, AcceptedDecisionInfo> = HashMap::new();
    let mut anomalies: Vec<(String, String, String, usize, Vec<u32>)> = Vec::new();

    for asr in &tables.assertions {
        if assertions_by_id
            .insert(asr.assertion_id.as_str(), asr)
            .is_some()
        {
            return Err(format!("duplicate assertion_id {}", asr.assertion_id));
        }

        let recomputed_rev = compute_claim_revision(asr)?;
        if recomputed_rev != asr.claim_revision_sha256 {
            return Err(format!(
                "claim_revision_sha256 mismatch for {}: expected {recomputed_rev}, got {}",
                asr.assertion_id, asr.claim_revision_sha256
            ));
        }

        let mut ev_rows = evidence_by_aid
            .get(asr.assertion_id.as_str())
            .cloned()
            .unwrap_or_default();
        if ev_rows.is_empty() {
            return Err(format!("assertion {} has no evidence", asr.assertion_id));
        }
        let has_supports = ev_rows.iter().any(|e| e.evidence_role == "supports");
        if !has_supports {
            return Err(format!(
                "assertion {} missing supporting evidence row",
                asr.assertion_id
            ));
        }
        ev_rows.sort_by(|a, b| {
            a.source_id
                .cmp(&b.source_id)
                .then(a.locator_json.cmp(&b.locator_json))
                .then(a.extraction_sha256.cmp(&b.extraction_sha256))
        });
        let ev_hash = compute_evidence_hash(&ev_rows)?;

        let decs = decisions_by_aid
            .get(asr.assertion_id.as_str())
            .ok_or_else(|| format!("assertion {} has no decisions", asr.assertion_id))?;
        let terminal = resolve_terminal_decision(&asr.assertion_id, decs)?;

        if terminal.assertion_revision_sha256 != asr.claim_revision_sha256 {
            return Err(format!(
                "decision {} stale assertion_revision_sha256 for {}",
                terminal.decision_id, asr.assertion_id
            ));
        }
        if terminal.evidence_bundle_sha256 != ev_hash {
            return Err(format!(
                "decision {} stale evidence_bundle_sha256 for {}: expected {ev_hash}, got {}",
                terminal.decision_id, asr.assertion_id, terminal.evidence_bundle_sha256
            ));
        }

        match terminal.outcome.as_str() {
            "accepted_human" => {
                if terminal.actor_type != "human"
                    || terminal
                        .actor_id
                        .as_deref()
                        .is_none_or(|s| s.trim().is_empty())
                {
                    return Err(format!(
                        "accepted_human decision {} requires human actor_type and nonempty actor_id",
                        terminal.decision_id
                    ));
                }
            }
            "accepted_auto_source" => {
                let has_contradict = ev_rows.iter().any(|e| e.evidence_role == "contradicts");
                if terminal.actor_type != "automated"
                    || terminal
                        .method_version
                        .as_deref()
                        .is_none_or(|s| s.trim().is_empty())
                    || asr.origin != "verbatim_source"
                    || asr.source_fidelity_state != "verified"
                    || asr.ambiguity_state != "unambiguous"
                    || has_contradict
                {
                    return Err(format!(
                        "accepted_auto_source preconditions violated on {}",
                        asr.assertion_id
                    ));
                }
            }
            other => {
                return Err(format!(
                    "assertion {} terminal decision {} is not accepted ({other})",
                    asr.assertion_id, terminal.decision_id
                ));
            }
        }

        collect_unicode_anomalies(&asr.assertion_id, &asr.value_json, &mut anomalies)?;

        accepted_by_assertion.insert(
            asr.assertion_id.as_str(),
            AcceptedDecisionInfo {
                decision: terminal,
                evidence: ev_rows,
            },
        );
    }

    for dec in &tables.decisions {
        if !assertions_by_id.contains_key(dec.assertion_id.as_str()) {
            return Err(format!(
                "decision {} references unknown assertion {}",
                dec.decision_id, dec.assertion_id
            ));
        }
    }

    reconcile_unicode_exceptions(
        &tables.unicode_exceptions,
        &anomalies,
        &assertions_by_id,
        &accepted_by_assertion,
        &decisions_by_id,
    )?;

    Ok(ValidatedReview {
        assertions_by_id,
        accepted_by_assertion,
    })
}

fn compute_claim_revision(asr: &AssertionRow) -> Result<String, String> {
    let obj = serde_json::json!({
        "assertion_id": asr.assertion_id,
        "subject_kind": asr.subject_kind,
        "subject_id": asr.subject_id,
        "property_code": asr.property_code,
        "value_state": asr.value_state,
        "value_json": asr.value_json,
        "origin": asr.origin,
        "source_fidelity_state": asr.source_fidelity_state,
        "ambiguity_state": asr.ambiguity_state,
        "algorithm_reference": asr.algorithm_reference,
        "convention_reference": asr.convention_reference,
        "imported_status_json": asr.imported_status_json,
        "imported_confidence_json": asr.imported_confidence_json,
    });
    let canonical = canonical_ascii_json(&obj)?;
    Ok(sha256_hex(canonical.as_bytes()))
}

fn compute_evidence_hash(rows: &[&EvidenceRow]) -> Result<String, String> {
    let mut encoded_rows = Vec::with_capacity(rows.len());
    for ev in rows {
        let obj = serde_json::json!({
            "assertion_id": ev.assertion_id,
            "source_id": ev.source_id,
            "source_record_id": ev.source_record_id,
            "locator_json": ev.locator_json,
            "evidence_role": ev.evidence_role,
            "extraction_version": ev.extraction_version,
            "extraction_sha256": ev.extraction_sha256,
        });
        let text = canonical_ascii_json(&obj)?;
        encoded_rows.push((text, obj));
    }
    encoded_rows.sort_by(|a, b| a.0.cmp(&b.0));
    let arr = Value::Array(encoded_rows.into_iter().map(|(_, v)| v).collect());
    let canonical = canonical_ascii_json(&arr)?;
    Ok(sha256_hex(canonical.as_bytes()))
}

fn resolve_terminal_decision<'a>(
    assertion_id: &str,
    decs: &[&'a DecisionRow],
) -> Result<&'a DecisionRow, String> {
    let ids: HashSet<&str> = decs.iter().map(|d| d.decision_id.as_str()).collect();
    let mut referenced_preds = HashSet::new();
    for dec in decs {
        if let Some(pred) = &dec.predecessor_decision_id {
            if pred == &dec.decision_id {
                return Err(format!("self-cycle in decision {}", dec.decision_id));
            }
            if !ids.contains(pred.as_str()) {
                return Err(format!(
                    "decision {} predecessor {pred} missing for {assertion_id}",
                    dec.decision_id
                ));
            }
            if !referenced_preds.insert(pred.as_str()) {
                return Err(format!(
                    "forked decision history on predecessor {pred} for {assertion_id}"
                ));
            }
        }
    }
    let terminals: Vec<&DecisionRow> = decs
        .iter()
        .copied()
        .filter(|d| !referenced_preds.contains(d.decision_id.as_str()))
        .collect();
    if terminals.len() != 1 {
        return Err(format!(
            "expected single terminal decision for {assertion_id}, found {}",
            terminals.len()
        ));
    }
    Ok(terminals[0])
}

fn collect_unicode_anomalies(
    assertion_id: &str,
    value: &Value,
    out: &mut Vec<(String, String, String, usize, Vec<u32>)>,
) -> Result<(), String> {
    match value {
        Value::String(s) => inspect_text_anomalies(assertion_id, s, out),
        Value::Array(items) => {
            for item in items {
                collect_unicode_anomalies(assertion_id, item, out)?;
            }
            Ok(())
        }
        Value::Object(map) => {
            for (k, v) in map {
                if !k.is_ascii() {
                    return Err(format!(
                        "assertion {assertion_id}: non-ASCII object key {k:?}"
                    ));
                }
                collect_unicode_anomalies(assertion_id, v, out)?;
            }
            Ok(())
        }
        _ => Ok(()),
    }
}

fn inspect_text_anomalies(
    assertion_id: &str,
    text: &str,
    out: &mut Vec<(String, String, String, usize, Vec<u32>)>,
) -> Result<(), String> {
    let report = tamil_core::inspect_tamil_string(text);
    if !report.is_nfc {
        let cps: Vec<u32> = text.chars().map(|c| c as u32).collect();
        out.push((
            assertion_id.to_owned(),
            "non_nfc_original".to_owned(),
            text.to_owned(),
            0,
            cps,
        ));
    }
    for (pos, ch) in text.chars().enumerate() {
        let cp = ch as u32;
        if cp < 32 || (0x7F..=0x9F).contains(&cp) {
            return Err(format!(
                "assertion {assertion_id}: disallowed C0/C1 control U+{cp:04X} at scalar {pos}"
            ));
        }
        if AUDIT_CONTROL_EXTRA_CPS.contains(&cp) {
            out.push((
                assertion_id.to_owned(),
                "intentional_control".to_owned(),
                text.to_owned(),
                pos,
                vec![cp],
            ));
        }
    }
    let bad_cluster = report.letters.iter().any(|letter| {
        letter.classification == "other"
            && letter
                .text
                .chars()
                .any(|c| ('\u{0B80}'..='\u{0BDF}').contains(&c))
    });
    if bad_cluster {
        return Err(format!(
            "assertion {assertion_id}: invalid_orthography classified by tamil-core"
        ));
    }
    Ok(())
}

fn reconcile_unicode_exceptions(
    exceptions: &[UnicodeExceptionRow],
    anomalies: &[(String, String, String, usize, Vec<u32>)],
    assertions_by_id: &HashMap<&str, &AssertionRow>,
    accepted_by_assertion: &HashMap<&str, AcceptedDecisionInfo>,
    decisions_by_id: &HashMap<&str, &DecisionRow>,
) -> Result<(), String> {
    let mut seen_keys = HashSet::new();
    let mut matched_anomaly_indices = HashSet::new();

    for exc in exceptions {
        if exc.reason_json.trim().is_empty() {
            return Err("unicode_exceptions: empty reason".to_owned());
        }
        let key = (
            exc.assertion_id.as_str(),
            exc.claim_revision_sha256.as_str(),
            exc.value_sha256.as_str(),
            exc.kind.as_str(),
            exc.scalar_position,
        );
        if !seen_keys.insert(key) {
            return Err(format!(
                "duplicate unicode exception for {}",
                exc.assertion_id
            ));
        }
        let asr = assertions_by_id
            .get(exc.assertion_id.as_str())
            .ok_or_else(|| format!("unicode exception dangling assertion {}", exc.assertion_id))?;
        if asr.claim_revision_sha256 != exc.claim_revision_sha256 {
            return Err(format!(
                "stale unicode exception claim_revision on {}",
                exc.assertion_id
            ));
        }
        let dec = decisions_by_id
            .get(exc.decision_id.as_str())
            .ok_or_else(|| format!("unicode exception unknown decision {}", exc.decision_id))?;
        let term = accepted_by_assertion
            .get(exc.assertion_id.as_str())
            .ok_or_else(|| {
                format!(
                    "unicode exception missing accepted decision on {}",
                    exc.assertion_id
                )
            })?;
        if dec.assertion_id != exc.assertion_id || dec.decision_id != term.decision.decision_id {
            return Err(format!(
                "unicode exception decision {} does not match current accepted decision",
                exc.decision_id
            ));
        }

        let mut matched_idx = None;
        for (idx, (aid, kind, text, pos, seq)) in anomalies.iter().enumerate() {
            if aid == &exc.assertion_id
                && kind == &exc.kind
                && *pos == exc.scalar_position
                && seq == &exc.scalar_sequence
                && sha256_hex(text.as_bytes()) == exc.value_sha256
            {
                matched_idx = Some(idx);
                break;
            }
        }
        let Some(idx) = matched_idx else {
            return Err(format!(
                "unused or mismatched unicode exception for {} ({} at {})",
                exc.assertion_id, exc.kind, exc.scalar_position
            ));
        };
        matched_anomaly_indices.insert(idx);
    }

    for (idx, (aid, kind, _, pos, _)) in anomalies.iter().enumerate() {
        if !matched_anomaly_indices.contains(&idx) {
            return Err(format!(
                "unexcepted Unicode anomaly {kind} on {aid} at scalar {pos}"
            ));
        }
    }
    Ok(())
}

// ---------- Structural, linguistic & projection compilation ----------

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledCoverageOut {
    pub language_ids: Vec<String>,
    pub region_codes: Vec<String>,
    pub register_codes: Vec<String>,
    pub unknown_region_entries: u64,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledVocabRegionOut {
    pub code: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_code: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledVocabulariesOut {
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
    pub regions: Vec<CompiledVocabRegionOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledLabelOut {
    pub registry_id: String,
    pub registry_version: String,
    pub code: String,
    pub category: String,
    pub display_label: String,
    pub definition: String,
    pub evidence_reference: String,
    pub parent_code: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledSourceNoticeOut {
    pub source_id: String,
    pub label: String,
    pub url: Option<String>,
    pub reuse_basis: String,
    pub attribution_text: String,
    pub attribution_reference: String,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledPackMetaOut {
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
    pub coverage: CompiledCoverageOut,
    pub entry_revisions: BTreeMap<String, String>,
    pub vocabularies: CompiledVocabulariesOut,
    pub labels: Vec<CompiledLabelOut>,
    pub sources: Vec<CompiledSourceNoticeOut>,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
#[allow(dead_code)]
pub struct CompiledAcceptanceOut {
    pub decision_id: String,
    pub kind: String,
    pub actor_id: Option<String>,
    pub method: Option<String>,
    pub decided_on: String,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
#[allow(dead_code)]
pub struct CompiledProvenanceOut {
    pub assertion_id: String,
    pub revision_sha256: String,
    pub source_id: String,
    pub locator: String,
    pub acceptance: CompiledAcceptanceOut,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledScopeOut {
    pub state: String,
    pub codes: Vec<String>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledFieldOut {
    pub availability: String,
    pub value: Option<Value>,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledLabelFieldOut {
    pub availability: String,
    pub value: Option<String>,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledAnnotationOut {
    pub property: String,
    pub field: CompiledFieldOut,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledFormOut {
    pub form_id: String,
    pub representation: String,
    pub role: String,
    pub text: String,
    pub convention: Option<String>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledTextOut {
    pub text_id: String,
    pub kind: String,
    pub language_id: String,
    pub text: String,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledEndpointOut {
    pub kind: String,
    pub id: String,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledRelationOut {
    pub relation_id: String,
    pub code: String,
    pub directionality: String,
    pub source: CompiledEndpointOut,
    pub target: CompiledEndpointOut,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledSenseOut {
    pub sense_id: String,
    pub display_order: u32,
    pub parent_sense_id: Option<String>,
    pub components: Vec<CompiledTextOut>,
    pub examples: Vec<CompiledTextOut>,
    pub relations: Vec<CompiledRelationOut>,
    pub region: CompiledScopeOut,
    pub register: CompiledLabelFieldOut,
    pub annotations: Vec<CompiledAnnotationOut>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

#[derive(Debug, Clone, Serialize)]
#[allow(dead_code)]
pub struct CompiledEntryOut {
    pub entry_id: String,
    pub revision: String,
    pub headword: String,
    pub language_id: String,
    pub part_of_speech: CompiledLabelFieldOut,
    pub forms: Vec<CompiledFormOut>,
    pub senses: Vec<CompiledSenseOut>,
    pub region: CompiledScopeOut,
    pub register: CompiledLabelFieldOut,
    pub annotations: Vec<CompiledAnnotationOut>,
    pub provenance: Vec<CompiledProvenanceOut>,
}

fn validate_structure_and_project(
    packs: &PacksToml,
    vocab: &VocabulariesToml,
    tables: &CanonicalTables,
    review: &ValidatedReview<'_>,
) -> Result<(CompiledPackMetaOut, Vec<CompiledEntryOut>), String> {
    let mut identity_map: HashMap<(&str, &str), &IdentityRow> = HashMap::new();
    for id_row in &tables.identities {
        if id_row.lifecycle != "active" {
            return Err(format!(
                "non-active identity {} ({})",
                id_row.entity_id, id_row.lifecycle
            ));
        }
        if identity_map
            .insert((id_row.kind.as_str(), id_row.entity_id.as_str()), id_row)
            .is_some()
        {
            return Err(format!(
                "duplicate identity ({}, {})",
                id_row.kind, id_row.entity_id
            ));
        }
    }

    let check_active_id = |kind: &str, id: &str| -> Result<(), String> {
        if !identity_map.contains_key(&(kind, id)) {
            return Err(format!("missing active identity for ({kind}, {id})"));
        }
        Ok(())
    };

    let vocab_region_parents: HashMap<&str, Option<&str>> = vocab
        .regions
        .iter()
        .map(|r| (r.code.as_str(), r.parent_code.as_deref()))
        .collect();

    // Label registry validation & acyclic hierarchy
    let mut labels_by_cat_code: HashMap<(&str, &str), &LabelRow> = HashMap::new();
    for lbl in &tables.labels {
        if !review
            .accepted_by_assertion
            .contains_key(lbl.evidence_reference.as_str())
        {
            return Err(format!(
                "label {} evidence_reference {} is not an accepted assertion",
                lbl.code, lbl.evidence_reference
            ));
        }
        if lbl.category == "region" {
            if let Some(v_parent) = vocab_region_parents.get(lbl.code.as_str()) {
                if lbl.parent_code.as_deref() != *v_parent {
                    return Err(format!(
                        "label {} region parent_code {:?} disagrees with vocabularies.toml {:?}",
                        lbl.code, lbl.parent_code, v_parent
                    ));
                }
            }
        }
        if labels_by_cat_code
            .insert((lbl.category.as_str(), lbl.code.as_str()), lbl)
            .is_some()
        {
            return Err(format!("duplicate label ({}, {})", lbl.category, lbl.code));
        }
    }
    for lbl in &tables.labels {
        let mut cursor = lbl.parent_code.as_deref();
        let mut visited = HashSet::new();
        visited.insert(lbl.code.as_str());
        while let Some(parent) = cursor {
            if !visited.insert(parent) {
                return Err(format!("cyclic label hierarchy involving {}", lbl.code));
            }
            let parent_row = labels_by_cat_code
                .get(&(lbl.category.as_str(), parent))
                .ok_or_else(|| format!("label {} missing parent_code {parent}", lbl.code))?;
            cursor = parent_row.parent_code.as_deref();
        }
    }

    let lang_set: HashSet<&str> = vocab.language_ids.iter().map(String::as_str).collect();
    let pos_set: HashSet<&str> = vocab.parts_of_speech.iter().map(String::as_str).collect();
    let rel_set: HashSet<&str> = vocab.relation_codes.iter().map(String::as_str).collect();
    let ann_set: HashSet<&str> = vocab
        .annotation_properties
        .iter()
        .map(String::as_str)
        .collect();
    let reg_set: HashSet<&str> = vocab.registers.iter().map(String::as_str).collect();
    let domain_set: HashSet<&str> = vocab.domains.iter().map(String::as_str).collect();
    let temporal_set: HashSet<&str> = vocab.temporals.iter().map(String::as_str).collect();
    let variety_set: HashSet<&str> = vocab.varieties.iter().map(String::as_str).collect();

    // Entries index + pack_members closure
    let mut entries_by_id: HashMap<&str, &EntryRow> = HashMap::new();
    for ent in &tables.entries {
        check_active_id("entry", &ent.entry_id)?;
        if !lang_set.contains(ent.language_id.as_str()) {
            return Err(format!(
                "entry {} unknown language_id {}",
                ent.entry_id, ent.language_id
            ));
        }
        if let Some(vid) = &ent.variety_id {
            if !variety_set.contains(vid.as_str()) {
                return Err(format!("entry {} unknown variety_id {vid:?}", ent.entry_id));
            }
        }
        if entries_by_id.insert(ent.entry_id.as_str(), ent).is_some() {
            return Err(format!("duplicate entry_id {}", ent.entry_id));
        }
    }

    let mut member_revs = BTreeMap::new();
    for pm in &tables.pack_members {
        if pm.pack_id != packs.pack_id {
            return Err(format!(
                "pack_members row has pack_id {}, expected {}",
                pm.pack_id, packs.pack_id
            ));
        }
        let ent = entries_by_id
            .get(pm.entry_id.as_str())
            .ok_or_else(|| format!("pack_members references missing entry {}", pm.entry_id))?;
        if ent.revision != pm.included_revision {
            return Err(format!(
                "pack_members revision mismatch for {}",
                pm.entry_id
            ));
        }
        if member_revs
            .insert(pm.entry_id.clone(), pm.included_revision.clone())
            .is_some()
        {
            return Err(format!("duplicate pack_members entry {}", pm.entry_id));
        }
    }
    if member_revs != packs.entry_revisions {
        return Err("packs.toml [entry_revisions] disagrees with entries/pack_members".to_owned());
    }
    if member_revs.len() != entries_by_id.len() {
        return Err("entries.csv contains entries omitted from pack_members.csv".to_owned());
    }

    // Forms validation
    let mut forms_by_entry: HashMap<&str, Vec<&FormRow>> = HashMap::new();
    let mut form_ids = HashSet::new();
    for frm in &tables.forms {
        check_active_id("form", &frm.form_id)?;
        if !form_ids.insert(frm.form_id.as_str()) {
            return Err(format!("duplicate form_id {}", frm.form_id));
        }
        if !entries_by_id.contains_key(frm.entry_id.as_str()) {
            return Err(format!(
                "form {} references missing entry {}",
                frm.form_id, frm.entry_id
            ));
        }
        let txt_asr = review
            .assertions_by_id
            .get(frm.text_assertion_id.as_str())
            .ok_or_else(|| {
                format!(
                    "form {} missing assertion {}",
                    frm.form_id, frm.text_assertion_id
                )
            })?;
        if txt_asr.subject_kind != "form"
            || txt_asr.subject_id != frm.form_id
            || txt_asr.property_code != "headword"
            || txt_asr.value_state != "known"
        {
            return Err(format!(
                "form {} invalid text_assertion {}",
                frm.form_id, frm.text_assertion_id
            ));
        }
        let txt_str = txt_asr
            .value_json
            .as_str()
            .filter(|s| !s.is_empty())
            .ok_or_else(|| format!("form {} headword must be nonempty string", frm.form_id))?;
        let _ = txt_str;
        if let Some(conv_aid) = &frm.convention_assertion_id {
            let conv_asr = review
                .assertions_by_id
                .get(conv_aid.as_str())
                .ok_or_else(|| {
                    format!(
                        "form {} missing convention assertion {conv_aid}",
                        frm.form_id
                    )
                })?;
            if conv_asr.subject_kind != "form" || conv_asr.subject_id != frm.form_id {
                return Err(format!(
                    "form {} convention assertion owner mismatch",
                    frm.form_id
                ));
            }
        }
        forms_by_entry
            .entry(frm.entry_id.as_str())
            .or_default()
            .push(frm);
    }

    // Senses validation & acyclic hierarchy within entry
    let mut senses_by_id: HashMap<&str, &SenseRow> = HashMap::new();
    let mut senses_by_entry: HashMap<&str, Vec<&SenseRow>> = HashMap::new();
    for sen in &tables.senses {
        check_active_id("sense", &sen.sense_id)?;
        if !entries_by_id.contains_key(sen.entry_id.as_str()) {
            return Err(format!(
                "sense {} references missing entry {}",
                sen.sense_id, sen.entry_id
            ));
        }
        if senses_by_id.insert(sen.sense_id.as_str(), sen).is_some() {
            return Err(format!("duplicate sense_id {}", sen.sense_id));
        }
        senses_by_entry
            .entry(sen.entry_id.as_str())
            .or_default()
            .push(sen);
    }
    for sen in &tables.senses {
        let mut cursor = sen.parent_sense_id.as_deref();
        let mut seen = HashSet::new();
        seen.insert(sen.sense_id.as_str());
        while let Some(pid) = cursor {
            if !seen.insert(pid) {
                return Err(format!("cyclic parent_sense_id involving {}", sen.sense_id));
            }
            let parent_row = senses_by_id
                .get(pid)
                .ok_or_else(|| format!("sense {} missing parent_sense_id {pid}", sen.sense_id))?;
            if parent_row.entry_id != sen.entry_id {
                return Err(format!(
                    "sense {} parent {pid} belongs to different entry {}",
                    sen.sense_id, parent_row.entry_id
                ));
            }
            cursor = parent_row.parent_sense_id.as_deref();
        }
    }

    // Texts validation
    let mut text_ids = HashSet::new();
    let mut texts_by_sense: HashMap<&str, Vec<&TextRow>> = HashMap::new();
    for txt in &tables.texts {
        check_active_id("text", &txt.text_id)?;
        if !text_ids.insert(txt.text_id.as_str()) {
            return Err(format!("duplicate text_id {}", txt.text_id));
        }
        if txt.component == "unparsed" {
            return Err(format!(
                "text {}: unparsed component forbidden in approved pack",
                txt.text_id
            ));
        }
        if txt.owner_kind != "sense" {
            return Err(format!(
                "text {}: entry-owned texts forbidden without reparenting ({})",
                txt.text_id, txt.owner_kind
            ));
        }
        if !senses_by_id.contains_key(txt.owner_id.as_str()) {
            return Err(format!(
                "text {} references missing sense {}",
                txt.text_id, txt.owner_id
            ));
        }
        if !lang_set.contains(txt.language_id.as_str()) {
            return Err(format!(
                "text {} unknown language_id {}",
                txt.text_id, txt.language_id
            ));
        }
        let asr = review
            .assertions_by_id
            .get(txt.text_assertion_id.as_str())
            .ok_or_else(|| {
                format!(
                    "text {} missing assertion {}",
                    txt.text_id, txt.text_assertion_id
                )
            })?;
        if asr.subject_kind != "text" || asr.subject_id != txt.text_id || asr.value_state != "known"
        {
            return Err(format!("text {} assertion mismatch", txt.text_id));
        }
        let s = asr
            .value_json
            .as_str()
            .filter(|v| !v.is_empty())
            .ok_or_else(|| format!("text {} value must be nonempty string", txt.text_id))?;
        let _ = s;
        texts_by_sense
            .entry(txt.owner_id.as_str())
            .or_default()
            .push(txt);
    }
    let texts_by_id: HashMap<&str, &TextRow> = tables
        .texts
        .iter()
        .map(|t| (t.text_id.as_str(), t))
        .collect();
    for txt in &tables.texts {
        if let Some(pid) = &txt.paired_translation_id {
            let paired = texts_by_id.get(pid.as_str()).ok_or_else(|| {
                format!("text {} dangling paired_translation_id {pid}", txt.text_id)
            })?;
            if pid == &txt.text_id
                || paired.component != "translation"
                || paired.owner_kind != txt.owner_kind
                || paired.owner_id != txt.owner_id
            {
                return Err(format!("text {} invalid paired_translation_id {pid}: must reference another translation with the same owner", txt.text_id));
            }
        }
    }

    // Relations validation
    let mut relations_by_id: HashMap<&str, &RelationRow> = HashMap::new();
    let mut relations_by_sense: HashMap<&str, Vec<&RelationRow>> = HashMap::new();
    for rel in &tables.relations {
        check_active_id("relation", &rel.relation_id)?;
        if relations_by_id
            .insert(rel.relation_id.as_str(), rel)
            .is_some()
        {
            return Err(format!("duplicate relation_id {}", rel.relation_id));
        }
        if rel.source_kind != "sense" {
            return Err(format!(
                "relation {} unsupported source_kind {:?}: LookupResponse only projects sense-anchored relations",
                rel.relation_id, rel.source_kind
            ));
        }
        let check_ep = |kind: &str, id: &str| -> Result<(), String> {
            match kind {
                "entry" => {
                    if !entries_by_id.contains_key(id) {
                        return Err(format!(
                            "relation {} dangling entry endpoint {id}",
                            rel.relation_id
                        ));
                    }
                }
                "sense" => {
                    if !senses_by_id.contains_key(id) {
                        return Err(format!(
                            "relation {} dangling sense endpoint {id}",
                            rel.relation_id
                        ));
                    }
                }
                other => return Err(format!("invalid endpoint kind {other}")),
            }
            Ok(())
        };
        check_ep(&rel.source_kind, &rel.source_id)?;
        check_ep(&rel.target_kind, &rel.target_id)?;
        let code_asr = review
            .assertions_by_id
            .get(rel.relation_code_assertion_id.as_str())
            .ok_or_else(|| format!("relation {} missing code assertion", rel.relation_id))?;
        let _ = review
            .accepted_by_assertion
            .get(rel.relation_code_assertion_id.as_str())
            .ok_or_else(|| {
                format!(
                    "relation {} code assertion {} not accepted",
                    rel.relation_id, rel.relation_code_assertion_id
                )
            })?;
        if code_asr.subject_kind != "relation"
            || code_asr.subject_id != rel.relation_id
            || code_asr.property_code != "relation_code"
            || code_asr.value_state != "known"
        {
            return Err(format!(
                "relation {} code assertion {} subject/property/state mismatch",
                rel.relation_id, rel.relation_code_assertion_id
            ));
        }
        let code = code_asr
            .value_json
            .as_str()
            .ok_or_else(|| format!("relation {} code must be string", rel.relation_id))?;
        if !rel_set.contains(code) {
            return Err(format!(
                "relation {} unknown code {code:?}",
                rel.relation_id
            ));
        }
        relations_by_sense
            .entry(rel.source_id.as_str())
            .or_default()
            .push(rel);
    }
    for rel in &tables.relations {
        if let Some(inv) = &rel.inverse_relation_id {
            if inv == &rel.relation_id {
                return Err(format!(
                    "relation {} inverse_relation_id cannot reference self",
                    rel.relation_id
                ));
            }
            let inv_rel = relations_by_id
                .get(inv.as_str())
                .ok_or_else(|| format!("relation {} dangling inverse {inv}", rel.relation_id))?;
            let swapped = inv_rel.source_kind == rel.target_kind
                && inv_rel.source_id == rel.target_id
                && inv_rel.target_kind == rel.source_kind
                && inv_rel.target_id == rel.source_id;
            let back_ok = inv_rel
                .inverse_relation_id
                .as_deref()
                .is_none_or(|b| b == rel.relation_id);
            if !swapped || inv_rel.directionality != rel.directionality || !back_ok {
                return Err(format!(
                    "relation {} inverse_relation_id {inv} incompatible endpoints/directionality",
                    rel.relation_id
                ));
            }
        }
    }

    // Scopes validation
    let scope_dim_matches_prop = |dim: &str, prop: &str| -> bool {
        prop == "scope_attestation"
            || match dim {
                "region" => prop == "region_scope",
                "register" => prop == "register_scope",
                "domain" => prop == "domain_scope",
                "social_usage" => prop == "social_usage_scope",
                "period" => matches!(prop, "temporal_scope" | "period_scope"),
                "grammar_system" => prop == "grammar_system_scope",
                _ => false,
            }
    };
    let mut scopes_by_subject: HashMap<(&str, &str), Vec<&ScopeRow>> = HashMap::new();
    let mut seen_scope_keys: HashSet<(&str, &str, &str, &str, Option<&str>)> = HashSet::new();
    for sc in &tables.scopes {
        match sc.subject_kind.as_str() {
            "entry" => {
                if !entries_by_id.contains_key(sc.subject_id.as_str()) {
                    return Err(format!("scope dangling entry {}", sc.subject_id));
                }
            }
            "sense" => {
                if !senses_by_id.contains_key(sc.subject_id.as_str()) {
                    return Err(format!("scope dangling sense {}", sc.subject_id));
                }
            }
            other => {
                if !identity_map.contains_key(&(other, sc.subject_id.as_str())) {
                    return Err(format!("scope dangling ({other}, {})", sc.subject_id));
                }
            }
        }
        if !seen_scope_keys.insert((
            sc.subject_kind.as_str(),
            sc.subject_id.as_str(),
            sc.dimension.as_str(),
            sc.state.as_str(),
            sc.label_code.as_deref(),
        )) {
            return Err(format!(
                "duplicate scope ({}, {}, {}, {}, {:?})",
                sc.subject_kind, sc.subject_id, sc.dimension, sc.state, sc.label_code
            ));
        }
        if sc.state == "attested" {
            let code = sc
                .label_code
                .as_deref()
                .ok_or_else(|| "attested scope missing label_code".to_owned())?;
            let lbl = labels_by_cat_code
                .get(&(sc.dimension.as_str(), code))
                .ok_or_else(|| {
                    format!("scope references unknown label ({}, {code})", sc.dimension)
                })?;
            match sc.dimension.as_str() {
                "register" if !reg_set.contains(code) => {
                    return Err(format!(
                        "scope register label {code:?} not in vocabularies.toml registers"
                    ));
                }
                "domain" if !domain_set.contains(code) => {
                    return Err(format!(
                        "scope domain label {code:?} not in vocabularies.toml domains"
                    ));
                }
                "period" if !temporal_set.contains(code) => {
                    return Err(format!(
                        "scope period label {code:?} not in vocabularies.toml temporals"
                    ));
                }
                "variety" if !variety_set.contains(code) => {
                    return Err(format!(
                        "scope variety label {code:?} not in vocabularies.toml varieties"
                    ));
                }
                "region" => {
                    let v_parent = vocab_region_parents.get(code).ok_or_else(|| {
                        format!("scope region label {code:?} not in vocabularies.toml regions")
                    })?;
                    if lbl.parent_code.as_deref() != *v_parent {
                        return Err(format!(
                            "scope region label {code:?} parent_code mismatch vs vocabularies.toml"
                        ));
                    }
                }
                _ => {}
            }
        }
        if matches!(sc.state.as_str(), "attested" | "unrestricted") {
            let aid = sc
                .supporting_assertion_id
                .as_deref()
                .ok_or_else(|| format!("{} scope missing supporting_assertion_id", sc.state))?;
            let dec_id = sc
                .decision_id
                .as_deref()
                .ok_or_else(|| format!("scope assertion {aid} missing decision_id"))?;
            let asr = review
                .assertions_by_id
                .get(aid)
                .ok_or_else(|| format!("scope missing supporting_assertion {aid}"))?;
            if asr.subject_kind != sc.subject_kind || asr.subject_id != sc.subject_id {
                return Err(format!(
                    "scope assertion {aid} owner ({}, {}) != ({}, {})",
                    asr.subject_kind, asr.subject_id, sc.subject_kind, sc.subject_id
                ));
            }
            if asr.value_state != "known" {
                return Err(format!(
                    "scope assertion {aid} must have value_state == known, found {:?}",
                    asr.value_state
                ));
            }
            if !scope_dim_matches_prop(&sc.dimension, &asr.property_code) {
                return Err(format!(
                    "scope dimension {:?} disagrees with assertion {aid} property_code {:?}",
                    sc.dimension, asr.property_code
                ));
            }
            let term = review
                .accepted_by_assertion
                .get(aid)
                .ok_or_else(|| format!("scope assertion {aid} not accepted"))?;
            if term.decision.decision_id != dec_id {
                return Err(format!("scope decision_id {dec_id} mismatch for {aid}"));
            }
            if term.decision.assertion_revision_sha256 != asr.claim_revision_sha256 {
                return Err(format!(
                    "scope decision {dec_id} revision mismatch for assertion {aid}"
                ));
            }
        } else if sc.supporting_assertion_id.is_some() || sc.decision_id.is_some() {
            let aid = sc
                .supporting_assertion_id
                .as_ref()
                .ok_or_else(|| "scope decision without supporting_assertion_id".to_owned())?;
            let dec_id = sc
                .decision_id
                .as_deref()
                .ok_or_else(|| format!("scope assertion {aid} missing decision_id"))?;
            let asr = review
                .assertions_by_id
                .get(aid.as_str())
                .ok_or_else(|| format!("scope missing supporting_assertion {aid}"))?;
            if asr.subject_kind != sc.subject_kind
                || asr.subject_id != sc.subject_id
                || !scope_dim_matches_prop(&sc.dimension, &asr.property_code)
            {
                return Err(format!("scope assertion {aid} owner/property mismatch"));
            }
            let term = review
                .accepted_by_assertion
                .get(aid.as_str())
                .ok_or_else(|| format!("scope assertion {aid} not accepted"))?;
            if term.decision.decision_id != dec_id
                || term.decision.assertion_revision_sha256 != asr.claim_revision_sha256
            {
                return Err(format!("scope decision_id {dec_id} mismatch for {aid}"));
            }
        }
        scopes_by_subject
            .entry((sc.subject_kind.as_str(), sc.subject_id.as_str()))
            .or_default()
            .push(sc);
    }
    for ((skind, sid), rows) in &scopes_by_subject {
        let mut by_dim: HashMap<&str, Vec<&ScopeRow>> = HashMap::new();
        for r in rows {
            by_dim.entry(r.dimension.as_str()).or_default().push(*r);
        }
        for (dim, dim_rows) in by_dim {
            let states: HashSet<&str> = dim_rows.iter().map(|r| r.state.as_str()).collect();
            if states.len() > 1 {
                return Err(format!(
                    "conflicting scope states for ({skind}, {sid}, {dim})"
                ));
            }
            if dim_rows.len() > 1 && states.iter().any(|s| *s != "attested") {
                return Err(format!(
                    "duplicate non-attested scope rows for ({skind}, {sid}, {dim})"
                ));
            }
            if dim == "register" && dim_rows.len() > 1 {
                return Err(format!(
                    "multiple register scope rows for ({skind}, {sid}); register is single-valued"
                ));
            }
        }
    }

    // Annotation assertions vocabulary check
    const CORE_STRUCTURAL_PROPS: &[&str] = &[
        "headword",
        "part_of_speech",
        "relation_code",
        "definition",
        "gloss",
        "translation",
        "citation",
        "example",
        "region_scope",
        "register_scope",
        "domain_scope",
        "temporal_scope",
        "period_scope",
        "variety_scope",
        "social_usage_scope",
        "grammar_system_scope",
        "scope_attestation",
        "unparsed_text",
        "pronunciation_ipa",
        "transliteration",
        "orthography_convention",
    ];
    for asr in &tables.assertions {
        if !CORE_STRUCTURAL_PROPS.contains(&asr.property_code.as_str())
            && !ann_set.contains(asr.property_code.as_str())
        {
            return Err(format!(
                "assertion {} unknown property_code {:?}",
                asr.assertion_id, asr.property_code
            ));
        }
        if let Some(conv) = &asr.convention_reference {
            if conv.trim().is_empty() {
                return Err("empty convention_reference".to_owned());
            }
        }
        if let Some(alg) = &asr.algorithm_reference {
            if alg.trim().is_empty() {
                return Err("empty algorithm_reference".to_owned());
            }
        }
    }

    // Build compiled entries in deterministic bytewise entry_id order
    let mut sorted_entries: Vec<&EntryRow> = tables.entries.iter().collect();
    sorted_entries.sort_by(|a, b| a.entry_id.cmp(&b.entry_id));

    let mut compiled_entries = Vec::with_capacity(sorted_entries.len());
    let mut cov_langs = BTreeSet::new();
    let mut cov_regions = BTreeSet::new();
    let mut cov_registers = BTreeSet::new();
    let mut unknown_region_entries = 0u64;

    for ent in sorted_entries {
        cov_langs.insert(ent.language_id.clone());
        let e_forms = forms_by_entry
            .get(ent.entry_id.as_str())
            .ok_or_else(|| format!("entry {} has no forms", ent.entry_id))?;

        let canonical_written: Vec<&FormRow> = e_forms
            .iter()
            .copied()
            .filter(|f| f.representation == "written" && f.role == "canonical")
            .collect();
        if canonical_written.len() != 1 {
            return Err(format!(
                "entry {} must have exactly 1 canonical written form, found {}",
                ent.entry_id,
                canonical_written.len()
            ));
        }
        if canonical_written[0].form_id != ent.canonical_form_id {
            return Err(format!(
                "entry {} canonical_form_id {} != canonical written form {}",
                ent.entry_id, ent.canonical_form_id, canonical_written[0].form_id
            ));
        }

        let mut sorted_forms = e_forms.clone();
        sorted_forms.sort_by(|a, b| {
            let ra = if a.role == "canonical" { 0u8 } else { 1u8 };
            let rb = if b.role == "canonical" { 0u8 } else { 1u8 };
            ra.cmp(&rb).then(a.form_id.cmp(&b.form_id))
        });

        let mut projected_forms = Vec::with_capacity(sorted_forms.len());
        let mut canonical_headword = String::new();
        let mut canonical_hw_prov = Vec::new();
        for f in sorted_forms {
            let txt_asr = review.assertions_by_id[f.text_assertion_id.as_str()];
            let text_val = txt_asr.value_json.as_str().unwrap().to_owned();
            let prov = make_provenance_list(&f.text_assertion_id, review);
            let conv = f.convention_assertion_id.as_ref().and_then(|cid| {
                review.assertions_by_id[cid.as_str()]
                    .value_json
                    .as_str()
                    .map(str::to_owned)
            });
            if f.form_id == ent.canonical_form_id {
                canonical_headword = text_val.clone();
                canonical_hw_prov = prov.clone();
            }
            projected_forms.push(CompiledFormOut {
                form_id: f.form_id.clone(),
                representation: f.representation.clone(),
                role: f.role.clone(),
                text: text_val,
                convention: conv,
                provenance: prov,
            });
        }

        let pos_asr = review
            .assertions_by_id
            .get(ent.pos_assertion_id.as_str())
            .ok_or_else(|| {
                format!(
                    "entry {} missing pos_assertion {}",
                    ent.entry_id, ent.pos_assertion_id
                )
            })?;
        let pos_val = pos_asr
            .value_json
            .as_str()
            .filter(|v| pos_set.contains(*v))
            .ok_or_else(|| {
                format!(
                    "entry {} unknown part_of_speech {:?}",
                    ent.entry_id, pos_asr.value_json
                )
            })?
            .to_owned();
        let pos_prov = make_provenance_list(&ent.pos_assertion_id, review);
        let pos_field = CompiledLabelFieldOut {
            availability: "available".to_owned(),
            value: Some(pos_val),
            convention: None,
            provenance: pos_prov.clone(),
        };

        let entry_annotations = build_annotations(
            "entry",
            &ent.entry_id,
            tables,
            review,
            CORE_STRUCTURAL_PROPS,
        );
        let mut entry_prov = canonical_hw_prov;
        entry_prov.extend(pos_prov);
        for a in &entry_annotations {
            entry_prov.extend(a.field.provenance.clone());
        }
        let entry_prov = dedup_provenance(entry_prov);

        let entry_region = build_scope("entry", &ent.entry_id, &scopes_by_subject, review)?;
        if entry_region.state == "unknown" {
            unknown_region_entries += 1;
        }
        for c in &entry_region.codes {
            cov_regions.insert(c.clone());
        }
        let entry_register =
            build_register_field("entry", &ent.entry_id, &scopes_by_subject, review)?;
        if let Some(rv) = &entry_register.value {
            if rv != "unrestricted" {
                cov_registers.insert(rv.clone());
            }
        }

        let mut e_senses = senses_by_entry
            .get(ent.entry_id.as_str())
            .cloned()
            .unwrap_or_default();
        if e_senses.is_empty() {
            return Err(format!("entry {} has zero senses", ent.entry_id));
        }
        e_senses.sort_by(|a, b| {
            a.display_order
                .cmp(&b.display_order)
                .then(a.sense_id.cmp(&b.sense_id))
        });

        let mut projected_senses = Vec::with_capacity(e_senses.len());
        for sen in e_senses {
            let mut s_texts = texts_by_sense
                .get(sen.sense_id.as_str())
                .cloned()
                .unwrap_or_default();
            s_texts.sort_by(|a, b| {
                a.component
                    .cmp(&b.component)
                    .then(a.text_id.cmp(&b.text_id))
            });

            let mut comps = Vec::new();
            let mut examples = Vec::new();
            let mut s_prov = Vec::new();
            for t in s_texts {
                let text_val = review.assertions_by_id[t.text_assertion_id.as_str()]
                    .value_json
                    .as_str()
                    .unwrap()
                    .to_owned();
                let t_prov = make_provenance_list(&t.text_assertion_id, review);
                s_prov.extend(t_prov.clone());
                let out_t = CompiledTextOut {
                    text_id: t.text_id.clone(),
                    kind: t.component.clone(),
                    language_id: t.language_id.clone(),
                    text: text_val,
                    provenance: t_prov,
                };
                if t.component == "example" {
                    examples.push(out_t);
                } else {
                    comps.push(out_t);
                }
            }
            if comps.is_empty() {
                return Err(format!(
                    "sense {} has no primary definition/gloss/translation/citation",
                    sen.sense_id
                ));
            }

            let mut s_rels_raw = relations_by_sense
                .get(sen.sense_id.as_str())
                .cloned()
                .unwrap_or_default();
            s_rels_raw.sort_by(|a, b| a.relation_id.cmp(&b.relation_id));
            let s_rels = s_rels_raw
                .into_iter()
                .map(|r| CompiledRelationOut {
                    relation_id: r.relation_id.clone(),
                    code: review.assertions_by_id[r.relation_code_assertion_id.as_str()]
                        .value_json
                        .as_str()
                        .unwrap()
                        .to_owned(),
                    directionality: if r.directionality == "undirected" {
                        "symmetric".to_owned()
                    } else {
                        "directed".to_owned()
                    },
                    source: CompiledEndpointOut {
                        kind: r.source_kind.clone(),
                        id: r.source_id.clone(),
                    },
                    target: CompiledEndpointOut {
                        kind: r.target_kind.clone(),
                        id: r.target_id.clone(),
                    },
                    provenance: make_provenance_list(&r.relation_code_assertion_id, review),
                })
                .collect();

            let s_anns = build_annotations(
                "sense",
                &sen.sense_id,
                tables,
                review,
                CORE_STRUCTURAL_PROPS,
            );
            for a in &s_anns {
                s_prov.extend(a.field.provenance.clone());
            }

            // Inherit entry scope only when sense lacks explicit rows for that dimension.
            let sense_rows = scopes_by_subject.get(&("sense", sen.sense_id.as_str()));
            let has_region_row = sense_rows
                .map(|rows| rows.iter().any(|r| r.dimension == "region"))
                .unwrap_or(false);
            let sense_region = if has_region_row {
                let s = build_scope("sense", &sen.sense_id, &scopes_by_subject, review)?;
                for c in &s.codes {
                    cov_regions.insert(c.clone());
                }
                s
            } else {
                entry_region.clone()
            };

            let has_register_row = sense_rows
                .map(|rows| rows.iter().any(|r| r.dimension == "register"))
                .unwrap_or(false);
            let sense_register = if has_register_row {
                let reg = build_register_field("sense", &sen.sense_id, &scopes_by_subject, review)?;
                if let Some(rv) = &reg.value {
                    if rv != "unrestricted" {
                        cov_registers.insert(rv.clone());
                    }
                }
                reg
            } else {
                entry_register.clone()
            };

            projected_senses.push(CompiledSenseOut {
                sense_id: sen.sense_id.clone(),
                display_order: sen.display_order,
                parent_sense_id: sen.parent_sense_id.clone(),
                components: comps,
                examples,
                relations: s_rels,
                region: sense_region,
                register: sense_register,
                annotations: s_anns,
                provenance: dedup_provenance(s_prov),
            });
        }

        compiled_entries.push(CompiledEntryOut {
            entry_id: ent.entry_id.clone(),
            revision: ent.revision.clone(),
            headword: canonical_headword,
            language_id: ent.language_id.clone(),
            part_of_speech: pos_field,
            forms: projected_forms,
            senses: projected_senses,
            region: entry_region,
            register: entry_register,
            annotations: entry_annotations,
            provenance: entry_prov,
        });
    }

    // Verify counts and coverage against packs.toml
    let actual_entry_count =
        u32::try_from(tables.entries.len()).map_err(|_| "entry_count overflow")?;
    let actual_sense_count =
        u32::try_from(tables.senses.len()).map_err(|_| "sense_count overflow")?;
    let actual_form_count = u32::try_from(tables.forms.len()).map_err(|_| "form_count overflow")?;
    let actual_text_count = u32::try_from(tables.texts.len()).map_err(|_| "text_count overflow")?;
    let actual_rel_count =
        u32::try_from(tables.relations.len()).map_err(|_| "relation_count overflow")?;
    let actual_asr_count =
        u32::try_from(tables.assertions.len()).map_err(|_| "assertion_count overflow")?;

    if packs.entry_count != actual_entry_count
        || packs.sense_count != actual_sense_count
        || packs.form_count != actual_form_count
        || packs.text_count != actual_text_count
        || packs.relation_count != actual_rel_count
        || packs.assertion_count != actual_asr_count
    {
        return Err("packs.toml table counts do not match CSV rows".to_owned());
    }

    let cov_langs_vec: Vec<String> = cov_langs.into_iter().collect();
    let cov_regions_vec: Vec<String> = cov_regions.into_iter().collect();
    let cov_registers_vec: Vec<String> = cov_registers.into_iter().collect();
    if packs.coverage.language_ids != cov_langs_vec
        || packs.coverage.region_codes != cov_regions_vec
        || packs.coverage.register_codes != cov_registers_vec
        || packs.coverage.unknown_region_entries != unknown_region_entries
    {
        return Err("packs.toml [coverage] disagrees with compiled entries".to_owned());
    }

    let mut labels_out: Vec<CompiledLabelOut> = tables
        .labels
        .iter()
        .map(|l| CompiledLabelOut {
            registry_id: l.registry_id.clone(),
            registry_version: l.registry_version.clone(),
            code: l.code.clone(),
            category: l.category.clone(),
            display_label: l.display_label_json.clone(),
            definition: l.definition_json.clone(),
            evidence_reference: l.evidence_reference.clone(),
            parent_code: l.parent_code.clone(),
        })
        .collect();
    labels_out.sort_by(|a, b| a.category.cmp(&b.category).then(a.code.cmp(&b.code)));

    let mut sources_out: Vec<CompiledSourceNoticeOut> = tables
        .sources
        .iter()
        .map(|s| CompiledSourceNoticeOut {
            source_id: s.source_id.clone(),
            label: s.label_json.clone(),
            url: s.url_json.clone(),
            reuse_basis: s.reuse_basis_json.clone().unwrap_or_default(),
            attribution_text: s.attribution_text_json.clone().unwrap_or_default(),
            attribution_reference: s.attribution_reference_json.clone().unwrap_or_default(),
        })
        .collect();
    sources_out.sort_by(|a, b| a.source_id.cmp(&b.source_id));

    let meta = CompiledPackMetaOut {
        pack_id: packs.pack_id.clone(),
        dataset_version: packs.dataset_version.clone(),
        description: packs.description.clone(),
        schema_version: packs.schema_version,
        vocabulary_version: packs.vocabulary_version.clone(),
        index_format_version: packs.index_format_version,
        manifest_sha256: packs.manifest_sha256.clone(),
        entry_count: actual_entry_count,
        sense_count: actual_sense_count,
        form_count: actual_form_count,
        text_count: actual_text_count,
        relation_count: actual_rel_count,
        assertion_count: actual_asr_count,
        omitted_relation_count: packs.omitted_relation_count,
        coverage: CompiledCoverageOut {
            language_ids: cov_langs_vec,
            region_codes: cov_regions_vec,
            register_codes: cov_registers_vec,
            unknown_region_entries,
        },
        entry_revisions: packs.entry_revisions.clone(),
        vocabularies: CompiledVocabulariesOut {
            vocabulary_version: vocab.vocabulary_version.clone(),
            language_ids: vocab.language_ids.clone(),
            parts_of_speech: vocab.parts_of_speech.clone(),
            relation_codes: vocab.relation_codes.clone(),
            annotation_properties: vocab.annotation_properties.clone(),
            registers: vocab.registers.clone(),
            domains: vocab.domains.clone(),
            temporals: vocab.temporals.clone(),
            varieties: vocab.varieties.clone(),
            regions: vocab
                .regions
                .iter()
                .map(|r| CompiledVocabRegionOut {
                    code: r.code.clone(),
                    parent_code: r.parent_code.clone(),
                })
                .collect(),
        },
        labels: labels_out,
        sources: sources_out,
    };

    Ok((meta, compiled_entries))
}

fn make_provenance_list(
    assertion_id: &str,
    review: &ValidatedReview<'_>,
) -> Vec<CompiledProvenanceOut> {
    let asr = review.assertions_by_id[assertion_id];
    let info = &review.accepted_by_assertion[assertion_id];
    let dec = info.decision;
    let acceptance = CompiledAcceptanceOut {
        decision_id: dec.decision_id.clone(),
        kind: dec.outcome.clone(),
        actor_id: if dec.outcome == "accepted_human" {
            dec.actor_id.clone()
        } else {
            None
        },
        method: dec.method_version.clone(),
        decided_on: dec.decision_date.clone(),
    };
    let mut out = Vec::new();
    for ev in &info.evidence {
        if ev.evidence_role == "supports" {
            out.push(CompiledProvenanceOut {
                assertion_id: assertion_id.to_owned(),
                revision_sha256: asr.claim_revision_sha256.clone(),
                source_id: ev.source_id.clone(),
                locator: ev.locator_json.clone(),
                acceptance: acceptance.clone(),
            });
        }
    }
    dedup_provenance(out)
}

fn dedup_provenance(items: Vec<CompiledProvenanceOut>) -> Vec<CompiledProvenanceOut> {
    let set: BTreeSet<CompiledProvenanceOut> = items.into_iter().collect();
    set.into_iter().collect()
}

fn build_scope(
    kind: &str,
    sid: &str,
    scopes_by_subject: &HashMap<(&str, &str), Vec<&ScopeRow>>,
    review: &ValidatedReview<'_>,
) -> Result<CompiledScopeOut, String> {
    let rows: Vec<&ScopeRow> = scopes_by_subject
        .get(&(kind, sid))
        .into_iter()
        .flat_map(|v| v.iter().copied())
        .filter(|r| r.dimension == "region")
        .collect();
    if rows.is_empty() {
        return Ok(CompiledScopeOut {
            state: "unknown".to_owned(),
            codes: Vec::new(),
            provenance: Vec::new(),
        });
    }
    if rows.iter().any(|r| r.state == "attested") {
        let mut codes = BTreeSet::new();
        let mut provs = Vec::new();
        for r in &rows {
            if r.state != "attested" {
                return Err(format!(
                    "conflicting region scope states for ({kind}, {sid})"
                ));
            }
            let code = r.label_code.clone().ok_or_else(|| {
                format!("attested region scope for ({kind}, {sid}) missing label_code")
            })?;
            let aid = r.supporting_assertion_id.as_deref().ok_or_else(|| {
                format!("attested region scope for ({kind}, {sid}) missing supporting_assertion_id")
            })?;
            codes.insert(code);
            provs.extend(make_provenance_list(aid, review));
        }
        let provenance = dedup_provenance(provs);
        if provenance.is_empty() {
            return Err(format!(
                "attested region scope for ({kind}, {sid}) has empty provenance"
            ));
        }
        return Ok(CompiledScopeOut {
            state: "attested".to_owned(),
            codes: codes.into_iter().collect(),
            provenance,
        });
    }
    if rows.iter().any(|r| r.state == "unrestricted") {
        let mut provs = Vec::new();
        for r in &rows {
            if r.state != "unrestricted" {
                return Err(format!(
                    "conflicting region scope states for ({kind}, {sid})"
                ));
            }
            let aid = r.supporting_assertion_id.as_deref().ok_or_else(|| {
                format!(
                    "unrestricted region scope for ({kind}, {sid}) missing supporting_assertion_id"
                )
            })?;
            provs.extend(make_provenance_list(aid, review));
        }
        let provenance = dedup_provenance(provs);
        if provenance.is_empty() {
            return Err(format!(
                "unrestricted region scope for ({kind}, {sid}) has empty provenance"
            ));
        }
        return Ok(CompiledScopeOut {
            state: "unrestricted".to_owned(),
            codes: Vec::new(),
            provenance,
        });
    }
    Ok(CompiledScopeOut {
        state: "unknown".to_owned(),
        codes: Vec::new(),
        provenance: Vec::new(),
    })
}

fn build_register_field(
    kind: &str,
    sid: &str,
    scopes_by_subject: &HashMap<(&str, &str), Vec<&ScopeRow>>,
    review: &ValidatedReview<'_>,
) -> Result<CompiledLabelFieldOut, String> {
    let rows: Vec<&ScopeRow> = scopes_by_subject
        .get(&(kind, sid))
        .into_iter()
        .flat_map(|v| v.iter().copied())
        .filter(|r| r.dimension == "register")
        .collect();
    if rows.len() > 1 {
        return Err(format!(
            "multiple register scope rows for ({kind}, {sid}); register is single-valued"
        ));
    }
    if let Some(first) = rows.first() {
        match first.state.as_str() {
            "attested" => {
                let aid = first.supporting_assertion_id.as_deref().ok_or_else(|| {
                    format!("attested register scope for ({kind}, {sid}) missing supporting_assertion_id")
                })?;
                let code = first.label_code.clone().ok_or_else(|| {
                    format!("attested register scope for ({kind}, {sid}) missing label_code")
                })?;
                let provenance = make_provenance_list(aid, review);
                if provenance.is_empty() {
                    return Err(format!(
                        "attested register scope for ({kind}, {sid}) has empty provenance"
                    ));
                }
                return Ok(CompiledLabelFieldOut {
                    availability: "available".to_owned(),
                    value: Some(code),
                    convention: None,
                    provenance,
                });
            }
            "unrestricted" => {
                let aid = first.supporting_assertion_id.as_deref().ok_or_else(|| {
                    format!("unrestricted register scope for ({kind}, {sid}) missing supporting_assertion_id")
                })?;
                let provenance = make_provenance_list(aid, review);
                if provenance.is_empty() {
                    return Err(format!(
                        "unrestricted register scope for ({kind}, {sid}) has empty provenance"
                    ));
                }
                return Ok(CompiledLabelFieldOut {
                    availability: "available".to_owned(),
                    value: Some("unrestricted".to_owned()),
                    convention: None,
                    provenance,
                });
            }
            "not_applicable" => {
                return Ok(CompiledLabelFieldOut {
                    availability: "not_applicable".to_owned(),
                    value: None,
                    convention: None,
                    provenance: Vec::new(),
                });
            }
            _ => {}
        }
    }
    Ok(CompiledLabelFieldOut {
        availability: "unknown".to_owned(),
        value: None,
        convention: None,
        provenance: Vec::new(),
    })
}

fn build_annotations(
    kind: &str,
    sid: &str,
    tables: &CanonicalTables,
    review: &ValidatedReview<'_>,
    core_props: &[&str],
) -> Vec<CompiledAnnotationOut> {
    let mut matching: Vec<&AssertionRow> = tables
        .assertions
        .iter()
        .filter(|a| {
            a.subject_kind == kind
                && a.subject_id == sid
                && !core_props.contains(&a.property_code.as_str())
        })
        .collect();
    matching.sort_by(|a, b| {
        a.property_code
            .cmp(&b.property_code)
            .then(a.assertion_id.cmp(&b.assertion_id))
    });
    matching
        .into_iter()
        .map(|a| CompiledAnnotationOut {
            property: a.property_code.clone(),
            field: CompiledFieldOut {
                availability: if a.value_state == "known" {
                    "available".to_owned()
                } else {
                    a.value_state.clone()
                },
                value: if a.value_state == "known" {
                    Some(a.value_json.clone())
                } else {
                    None
                },
                convention: a.convention_reference.clone(),
                provenance: make_provenance_list(&a.assertion_id, review),
            },
        })
        .collect()
}

fn write_varint_u32(mut value: u32, out: &mut Vec<u8>) {
    loop {
        let mut byte = (value & 0x7F) as u8;
        value >>= 7;
        if value != 0 {
            byte |= 0x80;
        }
        out.push(byte);
        if value == 0 {
            break;
        }
    }
}

type InternedAcceptance = (u32, u32, Option<u32>, Option<u32>, u32);
type InternedProvenance = (u32, u32, u32, u32, u32);

struct CompactPoolBuilder {
    string_map: HashMap<String, u32>,
    strings: Vec<String>,
    acceptance_map: HashMap<CompiledAcceptanceOut, u32>,
    acceptances: Vec<InternedAcceptance>,
    provenance_map: HashMap<CompiledProvenanceOut, u32>,
    provenances: Vec<InternedProvenance>,
}

impl CompactPoolBuilder {
    fn new() -> Self {
        Self {
            string_map: HashMap::new(),
            strings: Vec::new(),
            acceptance_map: HashMap::new(),
            acceptances: Vec::new(),
            provenance_map: HashMap::new(),
            provenances: Vec::new(),
        }
    }

    fn intern_str(&mut self, value: &str) -> Result<u32, String> {
        if let Some(&idx) = self.string_map.get(value) {
            return Ok(idx);
        }
        let idx = u32::try_from(self.strings.len())
            .map_err(|_| "string pool count exceeds u32".to_owned())?;
        let owned = value.to_owned();
        self.strings.push(owned.clone());
        self.string_map.insert(owned, idx);
        Ok(idx)
    }

    fn intern_acceptance(&mut self, acc: &CompiledAcceptanceOut) -> Result<u32, String> {
        if let Some(&idx) = self.acceptance_map.get(acc) {
            return Ok(idx);
        }
        let decision_id = self.intern_str(&acc.decision_id)?;
        let kind = self.intern_str(&acc.kind)?;
        let actor_id = acc
            .actor_id
            .as_deref()
            .map(|s| self.intern_str(s))
            .transpose()?;
        let method = acc
            .method
            .as_deref()
            .map(|s| self.intern_str(s))
            .transpose()?;
        let decided_on = self.intern_str(&acc.decided_on)?;
        let idx = u32::try_from(self.acceptances.len())
            .map_err(|_| "acceptance pool count exceeds u32".to_owned())?;
        self.acceptances
            .push((decision_id, kind, actor_id, method, decided_on));
        self.acceptance_map.insert(acc.clone(), idx);
        Ok(idx)
    }

    fn intern_provenance(&mut self, prov: &CompiledProvenanceOut) -> Result<u32, String> {
        if let Some(&idx) = self.provenance_map.get(prov) {
            return Ok(idx);
        }
        let assertion_id = self.intern_str(&prov.assertion_id)?;
        let revision_sha256 = self.intern_str(&prov.revision_sha256)?;
        let source_id = self.intern_str(&prov.source_id)?;
        let locator = self.intern_str(&prov.locator)?;
        let acceptance_idx = self.intern_acceptance(&prov.acceptance)?;
        let idx = u32::try_from(self.provenances.len())
            .map_err(|_| "provenance pool count exceeds u32".to_owned())?;
        self.provenances.push((
            assertion_id,
            revision_sha256,
            source_id,
            locator,
            acceptance_idx,
        ));
        self.provenance_map.insert(prov.clone(), idx);
        Ok(idx)
    }

    fn encode_str(&mut self, value: &str, out: &mut Vec<u8>) -> Result<(), String> {
        let idx = self.intern_str(value)?;
        write_varint_u32(idx, out);
        Ok(())
    }

    fn encode_opt_str(&mut self, value: Option<&str>, out: &mut Vec<u8>) -> Result<(), String> {
        match value {
            None => write_varint_u32(0, out),
            Some(s) => {
                let idx = self.intern_str(s)?;
                let encoded = idx
                    .checked_add(1)
                    .ok_or_else(|| "string pool index + 1 overflows u32".to_owned())?;
                write_varint_u32(encoded, out);
            }
        }
        Ok(())
    }

    fn encode_provenance_list(
        &mut self,
        items: &[CompiledProvenanceOut],
        out: &mut Vec<u8>,
    ) -> Result<(), String> {
        let count = u32::try_from(items.len())
            .map_err(|_| "provenance list count exceeds u32".to_owned())?;
        write_varint_u32(count, out);
        for item in items {
            let idx = self.intern_provenance(item)?;
            write_varint_u32(idx, out);
        }
        Ok(())
    }

    fn encode_label_field(
        &mut self,
        field: &CompiledLabelFieldOut,
        out: &mut Vec<u8>,
    ) -> Result<(), String> {
        self.encode_str(&field.availability, out)?;
        self.encode_opt_str(field.value.as_deref(), out)?;
        self.encode_opt_str(field.convention.as_deref(), out)?;
        self.encode_provenance_list(&field.provenance, out)
    }

    fn encode_scope(&mut self, scope: &CompiledScopeOut, out: &mut Vec<u8>) -> Result<(), String> {
        self.encode_str(&scope.state, out)?;
        let count = u32::try_from(scope.codes.len())
            .map_err(|_| "scope codes count exceeds u32".to_owned())?;
        write_varint_u32(count, out);
        for code in &scope.codes {
            self.encode_str(code, out)?;
        }
        self.encode_provenance_list(&scope.provenance, out)
    }

    fn encode_field(&mut self, field: &CompiledFieldOut, out: &mut Vec<u8>) -> Result<(), String> {
        self.encode_str(&field.availability, out)?;
        match &field.value {
            None | Some(Value::Null) => out.push(0),
            Some(Value::Bool(false)) => out.push(2),
            Some(Value::Bool(true)) => out.push(3),
            Some(Value::String(s)) => {
                out.push(4);
                self.encode_str(s, out)?;
            }
            Some(other) => {
                out.push(5);
                let json_str = serde_json::to_string(other)
                    .map_err(|err| format!("compact field json encode error: {err}"))?;
                self.encode_str(&json_str, out)?;
            }
        }
        self.encode_opt_str(field.convention.as_deref(), out)?;
        self.encode_provenance_list(&field.provenance, out)
    }

    fn encode_annotations(
        &mut self,
        items: &[CompiledAnnotationOut],
        out: &mut Vec<u8>,
    ) -> Result<(), String> {
        let count =
            u32::try_from(items.len()).map_err(|_| "annotations count exceeds u32".to_owned())?;
        write_varint_u32(count, out);
        for item in items {
            self.encode_str(&item.property, out)?;
            self.encode_field(&item.field, out)?;
        }
        Ok(())
    }

    fn encode_texts(&mut self, items: &[CompiledTextOut], out: &mut Vec<u8>) -> Result<(), String> {
        let count = u32::try_from(items.len()).map_err(|_| "texts count exceeds u32".to_owned())?;
        write_varint_u32(count, out);
        for item in items {
            self.encode_str(&item.text_id, out)?;
            self.encode_str(&item.kind, out)?;
            self.encode_str(&item.language_id, out)?;
            self.encode_str(&item.text, out)?;
            self.encode_provenance_list(&item.provenance, out)?;
        }
        Ok(())
    }

    fn encode_entry(&mut self, entry: &CompiledEntryOut) -> Result<Vec<u8>, String> {
        let mut out = Vec::with_capacity(128);
        self.encode_str(&entry.entry_id, &mut out)?;
        self.encode_str(&entry.revision, &mut out)?;
        self.encode_str(&entry.headword, &mut out)?;
        self.encode_str(&entry.language_id, &mut out)?;
        self.encode_label_field(&entry.part_of_speech, &mut out)?;

        let form_count =
            u32::try_from(entry.forms.len()).map_err(|_| "forms count exceeds u32".to_owned())?;
        write_varint_u32(form_count, &mut out);
        for form in &entry.forms {
            self.encode_str(&form.form_id, &mut out)?;
            self.encode_str(&form.representation, &mut out)?;
            self.encode_str(&form.role, &mut out)?;
            self.encode_str(&form.text, &mut out)?;
            self.encode_opt_str(form.convention.as_deref(), &mut out)?;
            self.encode_provenance_list(&form.provenance, &mut out)?;
        }

        let sense_count =
            u32::try_from(entry.senses.len()).map_err(|_| "senses count exceeds u32".to_owned())?;
        write_varint_u32(sense_count, &mut out);
        for sense in &entry.senses {
            self.encode_str(&sense.sense_id, &mut out)?;
            write_varint_u32(sense.display_order, &mut out);
            self.encode_opt_str(sense.parent_sense_id.as_deref(), &mut out)?;
            self.encode_texts(&sense.components, &mut out)?;
            self.encode_texts(&sense.examples, &mut out)?;

            let rel_count = u32::try_from(sense.relations.len())
                .map_err(|_| "relations count exceeds u32".to_owned())?;
            write_varint_u32(rel_count, &mut out);
            for rel in &sense.relations {
                self.encode_str(&rel.relation_id, &mut out)?;
                self.encode_str(&rel.code, &mut out)?;
                self.encode_str(&rel.directionality, &mut out)?;
                self.encode_str(&rel.source.kind, &mut out)?;
                self.encode_str(&rel.source.id, &mut out)?;
                self.encode_str(&rel.target.kind, &mut out)?;
                self.encode_str(&rel.target.id, &mut out)?;
                self.encode_provenance_list(&rel.provenance, &mut out)?;
            }

            self.encode_scope(&sense.region, &mut out)?;
            self.encode_label_field(&sense.register, &mut out)?;
            self.encode_annotations(&sense.annotations, &mut out)?;
            self.encode_provenance_list(&sense.provenance, &mut out)?;
        }

        self.encode_scope(&entry.region, &mut out)?;
        self.encode_label_field(&entry.register, &mut out)?;
        self.encode_annotations(&entry.annotations, &mut out)?;
        self.encode_provenance_list(&entry.provenance, &mut out)?;
        Ok(out)
    }

    fn write_pools(&self, out: &mut Vec<u8>) -> Result<(), String> {
        out.extend_from_slice(&COMPACT_POOL_MAGIC);
        let base_patch_pos = out.len();
        out.extend_from_slice(&0u64.to_le_bytes());

        let str_count = u32::try_from(self.strings.len())
            .map_err(|_| "string pool count exceeds u32".to_owned())?;
        out.extend_from_slice(&str_count.to_le_bytes());
        for s in &self.strings {
            let len = u32::try_from(s.len())
                .map_err(|_| "pooled string length exceeds u32".to_owned())?;
            write_varint_u32(len, out);
            out.extend_from_slice(s.as_bytes());
        }

        let acc_count = u32::try_from(self.acceptances.len())
            .map_err(|_| "acceptance pool count exceeds u32".to_owned())?;
        out.extend_from_slice(&acc_count.to_le_bytes());
        for &(decision_id, kind, actor_id, method, decided_on) in &self.acceptances {
            write_varint_u32(decision_id, out);
            write_varint_u32(kind, out);
            write_varint_u32(
                actor_id
                    .map(|v| v.checked_add(1).ok_or("actor_id pool index overflow"))
                    .transpose()?
                    .unwrap_or(0),
                out,
            );
            write_varint_u32(
                method
                    .map(|v| v.checked_add(1).ok_or("method pool index overflow"))
                    .transpose()?
                    .unwrap_or(0),
                out,
            );
            write_varint_u32(decided_on, out);
        }

        let prov_count = u32::try_from(self.provenances.len())
            .map_err(|_| "provenance pool count exceeds u32".to_owned())?;
        out.extend_from_slice(&prov_count.to_le_bytes());
        for &(assertion_id, revision_sha256, source_id, locator, acceptance_idx) in
            &self.provenances
        {
            write_varint_u32(assertion_id, out);
            write_varint_u32(revision_sha256, out);
            write_varint_u32(source_id, out);
            write_varint_u32(locator, out);
            write_varint_u32(acceptance_idx, out);
        }

        let entries_base =
            u64::try_from(out.len()).map_err(|_| "entries_base exceeds u64".to_owned())?;
        out[base_patch_pos..base_patch_pos + 8].copy_from_slice(&entries_base.to_le_bytes());
        Ok(())
    }
}

#[allow(dead_code)]
pub fn build_tlpack_binary(
    meta: &CompiledPackMetaOut,
    entries: &[CompiledEntryOut],
) -> Result<Vec<u8>, String> {
    build_tlpack_binary_with_flags(meta, entries, PACK_FLAG_COMPACT_INTERNED)
}

#[allow(dead_code)]
pub fn build_tlpack_binary_with_flags(
    meta: &CompiledPackMetaOut,
    entries: &[CompiledEntryOut],
    flags: u32,
) -> Result<Vec<u8>, String> {
    if entries.is_empty() {
        return Err("cannot compile empty approved entry set".to_owned());
    }
    if flags != 0 && flags != PACK_FLAG_COMPACT_INTERNED {
        return Err(format!("unsupported tlpack build flags {flags}"));
    }

    let mut postings_by_key: BTreeMap<String, Vec<u32>> = BTreeMap::new();
    let mut payload_bytes = Vec::new();
    let mut entry_index_bytes = Vec::with_capacity(entries.len() * 16);

    if flags == PACK_FLAG_COMPACT_INTERNED {
        let mut pools = CompactPoolBuilder::new();
        let mut encoded_entries = Vec::with_capacity(entries.len());
        for (ord_usize, entry) in entries.iter().enumerate() {
            let ord = u32::try_from(ord_usize).map_err(|_| "entry ordinal exceeds u32")?;
            let nfc_key = tamil_norm::normalize_nfc(&entry.headword);
            if nfc_key.is_empty() {
                return Err(format!("empty normalized headword on {}", entry.entry_id));
            }
            postings_by_key.entry(nfc_key).or_default().push(ord);
            encoded_entries.push(pools.encode_entry(entry)?);
        }

        pools.write_pools(&mut payload_bytes)?;
        for encoded_entry in encoded_entries {
            let entry_offset =
                u64::try_from(payload_bytes.len()).map_err(|_| "payload offset overflow")?;
            let entry_len =
                u64::try_from(encoded_entry.len()).map_err(|_| "entry length overflow")?;
            payload_bytes.extend_from_slice(&encoded_entry);
            entry_index_bytes.extend_from_slice(&entry_offset.to_le_bytes());
            entry_index_bytes.extend_from_slice(&entry_len.to_le_bytes());
        }
    } else {
        for (ord_usize, entry) in entries.iter().enumerate() {
            let ord = u32::try_from(ord_usize).map_err(|_| "entry ordinal exceeds u32")?;
            let nfc_key = tamil_norm::normalize_nfc(&entry.headword);
            if nfc_key.is_empty() {
                return Err(format!("empty normalized headword on {}", entry.entry_id));
            }
            postings_by_key.entry(nfc_key).or_default().push(ord);

            let entry_offset =
                u64::try_from(payload_bytes.len()).map_err(|_| "payload offset overflow")?;
            let encoded_entry =
                serde_json::to_vec(entry).map_err(|err| format!("entry serialize error: {err}"))?;
            let entry_len =
                u64::try_from(encoded_entry.len()).map_err(|_| "entry length overflow")?;
            payload_bytes.extend_from_slice(&encoded_entry);
            entry_index_bytes.extend_from_slice(&entry_offset.to_le_bytes());
            entry_index_bytes.extend_from_slice(&entry_len.to_le_bytes());
        }
    }

    let mut fst_builder = fst::MapBuilder::memory();
    let mut ranges_bytes = Vec::with_capacity(postings_by_key.len() * 8);
    let mut postings_bytes = Vec::new();
    let mut posting_cursor = 0u32;

    for (key_ord_usize, (key, ords)) in postings_by_key.iter_mut().enumerate() {
        ords.sort_unstable();
        ords.dedup();
        let start = posting_cursor;
        let count = u32::try_from(ords.len()).map_err(|_| "posting count exceeds u32")?;
        posting_cursor = posting_cursor
            .checked_add(count)
            .ok_or("total posting count overflow")?;

        ranges_bytes.extend_from_slice(&start.to_le_bytes());
        ranges_bytes.extend_from_slice(&count.to_le_bytes());
        for entry_ord in ords {
            postings_bytes.extend_from_slice(&entry_ord.to_le_bytes());
        }
        let key_ord = u64::try_from(key_ord_usize).map_err(|_| "key ordinal overflow")?;
        fst_builder
            .insert(key.as_bytes(), key_ord)
            .map_err(|err| format!("fst insert failed: {err}"))?;
    }

    let fst_bytes = fst_builder
        .into_inner()
        .map_err(|err| format!("fst finalize failed: {err}"))?;
    let metadata_bytes =
        serde_json::to_vec(meta).map_err(|err| format!("meta serialize error: {err}"))?;

    let key_count = u32::try_from(postings_by_key.len()).map_err(|_| "key_count exceeds u32")?;
    let entry_count = u32::try_from(entries.len()).map_err(|_| "entry_count exceeds u32")?;
    let posting_count = posting_cursor;

    let fst_offset = u64::try_from(HEADER_SIZE).map_err(|_| "header size overflow")?;
    let fst_len = u64::try_from(fst_bytes.len()).map_err(|_| "fst length overflow")?;
    let ranges_offset = fst_offset
        .checked_add(fst_len)
        .ok_or("ranges offset overflow")?;
    let ranges_len = u64::try_from(ranges_bytes.len()).map_err(|_| "ranges length overflow")?;
    let postings_offset = ranges_offset
        .checked_add(ranges_len)
        .ok_or("postings offset overflow")?;
    let postings_len =
        u64::try_from(postings_bytes.len()).map_err(|_| "postings length overflow")?;
    let entry_index_offset = postings_offset
        .checked_add(postings_len)
        .ok_or("entry_index offset overflow")?;
    let entry_index_len =
        u64::try_from(entry_index_bytes.len()).map_err(|_| "entry_index length overflow")?;
    let payload_offset = entry_index_offset
        .checked_add(entry_index_len)
        .ok_or("payload offset overflow")?;
    let payload_len = u64::try_from(payload_bytes.len()).map_err(|_| "payload length overflow")?;
    let metadata_offset = payload_offset
        .checked_add(payload_len)
        .ok_or("metadata offset overflow")?;
    let metadata_len =
        u64::try_from(metadata_bytes.len()).map_err(|_| "metadata length overflow")?;
    let total_len_u64 = metadata_offset
        .checked_add(metadata_len)
        .ok_or("total binary size overflow")?;
    let total_len = usize::try_from(total_len_u64).map_err(|_| "total size exceeds usize")?;

    let mut out = Vec::with_capacity(total_len);
    out.extend_from_slice(&PACK_MAGIC);
    out.extend_from_slice(&INDEX_FORMAT_VERSION.to_le_bytes());
    out.extend_from_slice(&SCHEMA_VERSION.to_le_bytes());
    out.extend_from_slice(&flags.to_le_bytes());
    out.extend_from_slice(&key_count.to_le_bytes());
    out.extend_from_slice(&posting_count.to_le_bytes());
    out.extend_from_slice(&entry_count.to_le_bytes());
    out.extend_from_slice(&fst_offset.to_le_bytes());
    out.extend_from_slice(&fst_len.to_le_bytes());
    out.extend_from_slice(&ranges_offset.to_le_bytes());
    out.extend_from_slice(&ranges_len.to_le_bytes());
    out.extend_from_slice(&postings_offset.to_le_bytes());
    out.extend_from_slice(&postings_len.to_le_bytes());
    out.extend_from_slice(&entry_index_offset.to_le_bytes());
    out.extend_from_slice(&entry_index_len.to_le_bytes());
    out.extend_from_slice(&payload_offset.to_le_bytes());
    out.extend_from_slice(&payload_len.to_le_bytes());
    out.extend_from_slice(&metadata_offset.to_le_bytes());
    out.extend_from_slice(&metadata_len.to_le_bytes());

    let mut body = Vec::with_capacity(total_len - HEADER_SIZE);
    body.extend_from_slice(&fst_bytes);
    body.extend_from_slice(&ranges_bytes);
    body.extend_from_slice(&postings_bytes);
    body.extend_from_slice(&entry_index_bytes);
    body.extend_from_slice(&payload_bytes);
    body.extend_from_slice(&metadata_bytes);

    let mut hasher = Sha256::new();
    hasher.update(&out);
    hasher.update(&body);
    let checksum: [u8; 32] = hasher.finalize().into();

    out.extend_from_slice(&checksum);
    debug_assert_eq!(out.len(), HEADER_SIZE);
    out.extend_from_slice(&body);
    debug_assert_eq!(out.len(), total_len);
    Ok(out)
}
