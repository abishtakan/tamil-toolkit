//! Tests-first verification suite for the offline lexicon pack compiler and binary container.
#![forbid(unsafe_code)]

#[path = "support/lexicon_unicode.rs"]
mod lexicon_unicode;

#[path = "../build_lexicon.rs"]
mod build_lexicon;

use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use proptest::prelude::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

#[allow(unused_imports)]
use tamil_toolkit::lexicon_pack::{
    available_packs, decode_entry_slice_le, decode_posting_range_le, embedded_payload_bytes,
    enabled_pack_features, encode_entry_slice_le, encode_posting_range_le, open_available_pack,
    read_u64_le, unapproved_enabled_packs, CompiledPackView, EntrySlice, PostingRange,
    CHECKSUM_OFFSET, EXPECTED_CANONICAL_FORMAT, EXPECTED_CSV_ENCODING, HEADER_SIZE,
    INDEX_FORMAT_VERSION, PACK_FLAG_COMPACT_INTERNED, PACK_MAGIC, SCHEMA_VERSION,
};

const CORE_MANIFEST_SHA256: &str =
    "a211334e3659647deb4fc30a1c5c6778f4fa9ef98815ed44674a7d5d7dc05bdf";
const CORE_DATASET_VERSION: &str = "0.1.0+a211334e3659";
const NANRI: &str = "\u{0ba8}\u{0ba9}\u{0bcd}\u{0bb1}\u{0bbf}";
const NANRI_ID_1: &str = "ent_a08297c3-424d-5a37-aaf0-4135d7476669";
#[allow(dead_code)]
const NANRI_ID_2: &str = "ent_f063763c-36ac-55c6-b288-8da7f9ab6fff";

static NEXT_TEMP_ID: AtomicU64 = AtomicU64::new(0);

#[test]
fn embedded_view_reuse_is_thread_safe_and_does_not_trust_external_bytes() {
    for artifact in available_packs() {
        std::thread::scope(|scope| {
            for _ in 0..8 {
                scope.spawn(|| {
                    let view = open_available_pack(artifact.id).unwrap();
                    assert_eq!(view.metadata().unwrap().pack_id, artifact.id);
                    assert!(view.header().entry_count > 0);
                });
            }
        });
        let mut changed = artifact.bytes.to_vec();
        let last = changed.len() - 1;
        changed[last] ^= 1;
        // Opening the trusted embedded version must never approve a different
        // byte buffer carrying the same metadata or pack ID.
        assert!(CompiledPackView::parse(&changed).is_err());
        assert!(open_available_pack(artifact.id).is_ok());
    }
}

struct TempDirGuard {
    path: PathBuf,
}

impl TempDirGuard {
    fn new(label: &str) -> Self {
        let id = NEXT_TEMP_ID.fetch_add(1, Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!(
            "tamil-toolkit-pack-test-{label}-{}-{id}",
            std::process::id()
        ));
        fs::create_dir_all(&dir).expect("create temp dir");
        Self { path: dir }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TempDirGuard {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn manifest_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn package_dictionary_dir() -> PathBuf {
    manifest_dir().join("lexicon").join("dictionary")
}

fn package_schemas_dir() -> PathBuf {
    manifest_dir().join("schemas").join("lexicon")
}

fn copy_dir_recursive(src: &Path, dst: &Path) {
    fs::create_dir_all(dst).expect("create dst dir");
    for entry in fs::read_dir(src).expect("read src dir") {
        let entry = entry.expect("dir entry");
        let ty = entry.file_type().expect("file type");
        let target = dst.join(entry.file_name());
        if ty.is_dir() {
            copy_dir_recursive(&entry.path(), &target);
        } else {
            fs::copy(entry.path(), target).expect("copy file");
        }
    }
}

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    digest.iter().map(|b| format!("{b:02x}")).collect()
}

fn recompute_packs_toml_manifest(pack_dir: &Path) {
    let packs_path = pack_dir.join("packs.toml");
    let raw = fs::read_to_string(&packs_path).expect("read packs.toml");
    let mut doc: toml::Value = toml::from_str(&raw).expect("parse packs.toml");
    let table = doc.as_table_mut().expect("packs root table");
    let mut updated_files = Vec::new();

    if let Some(toml::Value::Array(files)) = table.get("files") {
        for item in files {
            let mut ftable = item.as_table().expect("file table").clone();
            let rel = ftable
                .get("path")
                .and_then(toml::Value::as_str)
                .expect("file path")
                .to_owned();
            let file_path = pack_dir.join(&rel);
            let bytes = fs::read(&file_path).expect("read tracked file");
            ftable.insert("sha256".to_owned(), toml::Value::String(sha256_hex(&bytes)));
            ftable.insert(
                "bytes".to_owned(),
                toml::Value::Integer(i64::try_from(bytes.len()).expect("len fits i64")),
            );
            if rel.ends_with(".csv") {
                let text = std::str::from_utf8(&bytes).expect("utf8 csv");
                let line_count = text.lines().count();
                let data_rows = line_count.saturating_sub(1);
                ftable.insert(
                    "rows".to_owned(),
                    toml::Value::Integer(i64::try_from(data_rows).expect("rows fit i64")),
                );
            }
            updated_files.push(ftable);
        }
    }
    updated_files.sort_by(|a, b| {
        let pa = a.get("path").and_then(toml::Value::as_str).unwrap_or("");
        let pb = b.get("path").and_then(toml::Value::as_str).unwrap_or("");
        pa.cmp(pb)
    });

    let manifest_items: Vec<Value> = updated_files
        .iter()
        .map(|f| {
            json!({
                "path": f.get("path").and_then(toml::Value::as_str).unwrap(),
                "sha256": f.get("sha256").and_then(toml::Value::as_str).unwrap(),
                "bytes": f.get("bytes").and_then(toml::Value::as_integer).unwrap(),
            })
        })
        .collect();
    let canonical = build_lexicon::canonical_ascii_json(&Value::Array(manifest_items))
        .expect("canonical manifest json");
    let new_manifest = sha256_hex(canonical.as_bytes());
    table.insert(
        "manifest_sha256".to_owned(),
        toml::Value::String(new_manifest),
    );
    table.insert(
        "files".to_owned(),
        toml::Value::Array(updated_files.into_iter().map(toml::Value::Table).collect()),
    );
    let rendered = toml::to_string(&doc).expect("serialize packs.toml");
    fs::write(&packs_path, rendered.replace("\r\n", "\n")).expect("write packs.toml");
}

fn clone_full_core_pack_to_temp(label: &str) -> (TempDirGuard, PathBuf, PathBuf) {
    let tmp = TempDirGuard::new(label);
    let pack_dir = tmp.path().join("dictionary");
    let schemas_dir = tmp.path().join("schemas");
    copy_dir_recursive(&package_dictionary_dir(), &pack_dir);
    copy_dir_recursive(&package_schemas_dir(), &schemas_dir);
    (tmp, pack_dir, schemas_dir)
}

fn filter_csv_rows(
    src: &Path,
    dst: &Path,
    mut keep: impl FnMut(&csv::StringRecord) -> bool,
) -> usize {
    let mut rdr = csv::ReaderBuilder::new()
        .has_headers(true)
        .from_path(src)
        .expect("read csv");
    let headers = rdr.headers().expect("headers").clone();
    let mut wtr = csv::WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_path(dst)
        .expect("write csv");
    wtr.write_record(&headers).expect("write headers");
    let mut count = 0usize;
    for rec in rdr.records() {
        let rec = rec.expect("csv record");
        if keep(&rec) {
            wtr.write_record(&rec).expect("write record");
            count += 1;
        }
    }
    wtr.flush().expect("flush csv");
    count
}

fn pilot_core_template_dir() -> &'static PathBuf {
    static TEMPLATE: std::sync::OnceLock<(TempDirGuard, PathBuf)> = std::sync::OnceLock::new();
    &TEMPLATE
        .get_or_init(|| {
            let tmp = TempDirGuard::new("pilot-core-template");
            let dst = tmp.path().join("dictionary");
            let src = package_dictionary_dir();
            fs::create_dir_all(&dst).expect("create pilot dst");
            // Copy static non-CSV files & notices directory
            for entry in fs::read_dir(&src).expect("read src") {
                let entry = entry.expect("entry");
                let name = entry.file_name();
                let target = dst.join(&name);
                if entry.file_type().expect("ty").is_dir() {
                    copy_dir_recursive(&entry.path(), &target);
                } else if !name.to_string_lossy().ends_with(".csv") {
                    fs::copy(entry.path(), target).expect("copy static file");
                }
            }

            // Keep only the 6 human-reviewed pilot entries (structural_kind != "wiktionary_bulk")
            let mut kept_entries = std::collections::BTreeSet::new();
            let mut kept_subjects = std::collections::BTreeSet::new();
            let entry_count =
                filter_csv_rows(&src.join("entries.csv"), &dst.join("entries.csv"), |r| {
                    let keep = r.get(5) != Some("wiktionary_bulk");
                    if keep {
                        let eid = r.get(0).unwrap().to_owned();
                        kept_entries.insert(eid.clone());
                        kept_subjects.insert(eid);
                    }
                    keep
                });
            let form_count = filter_csv_rows(&src.join("forms.csv"), &dst.join("forms.csv"), |r| {
                let keep = r.get(1).is_some_and(|eid| kept_entries.contains(eid));
                if keep {
                    kept_subjects.insert(r.get(0).unwrap().to_owned());
                }
                keep
            });
            let sense_count =
                filter_csv_rows(&src.join("senses.csv"), &dst.join("senses.csv"), |r| {
                    let keep = r.get(1).is_some_and(|eid| kept_entries.contains(eid));
                    if keep {
                        kept_subjects.insert(r.get(0).unwrap().to_owned());
                    }
                    keep
                });
            let text_count = filter_csv_rows(&src.join("texts.csv"), &dst.join("texts.csv"), |r| {
                let keep = r.get(2).is_some_and(|oid| kept_subjects.contains(oid));
                if keep {
                    kept_subjects.insert(r.get(0).unwrap().to_owned());
                }
                keep
            });
            filter_csv_rows(
                &src.join("pack_members.csv"),
                &dst.join("pack_members.csv"),
                |r| r.get(1).is_some_and(|eid| kept_entries.contains(eid)),
            );
            filter_csv_rows(&src.join("scopes.csv"), &dst.join("scopes.csv"), |r| {
                r.get(1).is_some_and(|sid| kept_subjects.contains(sid))
            });
            let mut kept_assertions = std::collections::BTreeSet::new();
            let assertion_count = filter_csv_rows(
                &src.join("assertions.csv"),
                &dst.join("assertions.csv"),
                |r| {
                    let keep = r.get(2).is_some_and(|sid| kept_subjects.contains(sid));
                    if keep {
                        kept_assertions.insert(r.get(0).unwrap().to_owned());
                    }
                    keep
                },
            );
            let mut kept_sources = std::collections::BTreeSet::new();
            filter_csv_rows(&src.join("evidence.csv"), &dst.join("evidence.csv"), |r| {
                let keep = r.get(0).is_some_and(|aid| kept_assertions.contains(aid));
                if keep {
                    kept_sources.insert(r.get(1).unwrap().to_owned());
                }
                keep
            });
            filter_csv_rows(
                &src.join("decisions.csv"),
                &dst.join("decisions.csv"),
                |r| r.get(1).is_some_and(|aid| kept_assertions.contains(aid)),
            );
            filter_csv_rows(
                &src.join("identities.csv"),
                &dst.join("identities.csv"),
                |r| r.get(0).is_some_and(|id| kept_subjects.contains(id)),
            );
            filter_csv_rows(&src.join("sources.csv"), &dst.join("sources.csv"), |r| {
                r.get(0).is_some_and(|sid| kept_sources.contains(sid))
            });
            for empty_csv in ["labels.csv", "relations.csv", "unicode_exceptions.csv"] {
                filter_csv_rows(&src.join(empty_csv), &dst.join(empty_csv), |_| false);
            }

            // Update packs.toml counts, coverage, and entry_revisions for the 6 pilot entries
            let packs_path = dst.join("packs.toml");
            let mut doc: toml::Value =
                toml::from_str(&fs::read_to_string(&packs_path).expect("read packs.toml"))
                    .expect("parse packs.toml");
            let table = doc.as_table_mut().expect("root table");
            table.insert(
                "entry_count".to_owned(),
                toml::Value::Integer(entry_count as i64),
            );
            table.insert(
                "sense_count".to_owned(),
                toml::Value::Integer(sense_count as i64),
            );
            table.insert(
                "form_count".to_owned(),
                toml::Value::Integer(form_count as i64),
            );
            table.insert(
                "text_count".to_owned(),
                toml::Value::Integer(text_count as i64),
            );
            table.insert(
                "assertion_count".to_owned(),
                toml::Value::Integer(assertion_count as i64),
            );
            if let Some(toml::Value::Table(cov)) = table.get_mut("coverage") {
                cov.insert("region_codes".to_owned(), toml::Value::Array(Vec::new()));
                cov.insert("register_codes".to_owned(), toml::Value::Array(Vec::new()));
                cov.insert(
                    "unknown_region_entries".to_owned(),
                    toml::Value::Integer(entry_count as i64),
                );
            }
            if let Some(toml::Value::Table(revs)) = table.get_mut("entry_revisions") {
                revs.retain(|k, _| kept_entries.contains(k));
            }
            fs::write(
                &packs_path,
                toml::to_string_pretty(&doc).expect("serialize packs.toml"),
            )
            .expect("write packs.toml");
            sync_full_packs_toml(&dst);
            (tmp, dst)
        })
        .1
}

fn clone_core_pack_to_temp(label: &str) -> (TempDirGuard, PathBuf, PathBuf) {
    let tmp = TempDirGuard::new(label);
    let pack_dir = tmp.path().join("dictionary");
    let schemas_dir = tmp.path().join("schemas");
    copy_dir_recursive(pilot_core_template_dir(), &pack_dir);
    copy_dir_recursive(&package_schemas_dir(), &schemas_dir);
    (tmp, pack_dir, schemas_dir)
}

fn rewrite_csv_and_remint_manifest(
    pack_dir: &Path,
    filename: &str,
    mut transform: impl FnMut(&str) -> String,
) {
    let target = pack_dir.join(filename);
    let original = fs::read_to_string(&target).expect("read csv");
    let updated = transform(&original);
    fs::write(&target, updated).expect("write csv");
    recompute_packs_toml_manifest(pack_dir);
}

#[test]
fn embedded_feature_profile_respects_defaults_and_approval_boundary() {
    #[cfg(not(feature = "lexicon-core"))]
    {
        assert_eq!(embedded_payload_bytes(), 0);
        assert!(available_packs().is_empty());
        assert_eq!(
            open_available_pack("core").unwrap_err(),
            "lexicon: pack unavailable 'core'"
        );
    }

    #[cfg(feature = "lexicon-core")]
    {
        assert!(enabled_pack_features().contains(&"core"));
        assert!(embedded_payload_bytes() > HEADER_SIZE);
        let expected_pack_count = 1usize
            + usize::from(cfg!(feature = "lexicon-names-taxa"))
            + usize::from(cfg!(feature = "lexicon-regional"));
        assert_eq!(available_packs().len(), expected_pack_count);
        let core_meta = available_packs()
            .iter()
            .find(|p| p.id == "core")
            .expect("core pack available");
        assert_eq!(core_meta.id, "core");
        assert_eq!(core_meta.dataset_version, CORE_DATASET_VERSION);
        assert_eq!(core_meta.schema_version, SCHEMA_VERSION);
        assert_eq!(core_meta.index_format_version, INDEX_FORMAT_VERSION);
        assert_eq!(core_meta.manifest_sha256, CORE_MANIFEST_SHA256);

        let view = open_available_pack("core").expect("open valid embedded core pack");
        assert_eq!(view.header().entry_count, 10343);
        let fst = view.fst_map().expect("open fst");
        let nanri_ord = fst.get(NANRI).expect("FST contains nanri");
        let range = view.posting_range(nanri_ord).expect("posting range");
        assert_eq!(range.count, 2);
        let entry_indices = view.posting_entry_indices(range).expect("posting indices");
        let mut entry_ids = Vec::new();
        for idx in entry_indices {
            let entry = view.entry(idx).expect("decode entry");
            entry_ids.push(entry.entry_id);
        }
        assert_eq!(entry_ids, vec![NANRI_ID_1, NANRI_ID_2]);
    }

    #[cfg(feature = "lexicon-terminology")]
    {
        assert!(enabled_pack_features().contains(&"terminology"));
        assert!(unapproved_enabled_packs().contains(&"terminology"));
        assert!(!available_packs().iter().any(|p| p.id == "terminology"));
        assert_eq!(
            open_available_pack("terminology").unwrap_err(),
            "lexicon: pack unavailable 'terminology'"
        );
    }

    #[cfg(feature = "lexicon-names-taxa")]
    {
        assert!(enabled_pack_features().contains(&"names_taxa"));
        assert!(!unapproved_enabled_packs().contains(&"names_taxa"));
        assert!(available_packs().iter().any(|p| p.id == "names_taxa"));
        let view =
            open_available_pack("names_taxa").expect("open approved embedded names_taxa pack");
        assert_eq!(view.header().entry_count, 762);
    }

    #[cfg(feature = "lexicon-regional")]
    {
        assert!(enabled_pack_features().contains(&"regional"));
        assert!(!unapproved_enabled_packs().contains(&"regional"));
        assert!(available_packs().iter().any(|p| p.id == "regional"));
        let view = open_available_pack("regional").expect("open approved embedded regional pack");
        assert_eq!(view.header().entry_count, 272);
    }

    assert_eq!(
        open_available_pack("nonexistent_pack").unwrap_err(),
        "lexicon: unknown pack 'nonexistent_pack'"
    );
}

#[test]
fn real_core_pack_compiles_reproducibly_and_uses_compact_utf8_payloads() {
    let (_tmp_a, dir_a, schemas_a) = clone_full_core_pack_to_temp("repro-a");
    let (_tmp_b, dir_b, schemas_b) = clone_full_core_pack_to_temp("repro-b");

    let out_a = build_lexicon::compile_pack_dir(&dir_a, Some(&schemas_a), Some("core"))
        .expect("compile isolated core pack A");
    let out_b = build_lexicon::compile_pack_dir(&dir_b, Some(&schemas_b), Some("core"))
        .expect("compile isolated core pack B");

    assert_eq!(out_a.pack_id, "core");
    assert_eq!(out_a.dataset_version, CORE_DATASET_VERSION);
    assert_eq!(out_a.manifest_sha256, CORE_MANIFEST_SHA256);
    assert_eq!(out_a.schema_version, SCHEMA_VERSION);
    assert_eq!(out_a.index_format_version, INDEX_FORMAT_VERSION);
    assert_eq!(
        out_a.bytes, out_b.bytes,
        "two clean compiles must be byte-identical"
    );
    assert_eq!(out_a.artifact_sha256, out_b.artifact_sha256);

    let view = CompiledPackView::parse(&out_a.bytes).expect("parse compiled tlpack");
    assert_eq!(view.header().flags, PACK_FLAG_COMPACT_INTERNED);
    let meta = view.metadata().expect("decode meta");
    assert_eq!(meta.entry_count, 10343);
    assert_eq!(meta.sense_count, 23827);
    assert_eq!(meta.assertion_count, 50718);
    assert_eq!(meta.form_count, 10343);
    assert_eq!(meta.text_count, 23827);
    assert_eq!(meta.relation_count, 0);
    assert_eq!(meta.omitted_relation_count, 0);
    assert_eq!(meta.coverage.unknown_region_entries, 10342);

    let fst = view.fst_map().expect("fst");
    let nanri_ord = fst.get(NANRI).expect("nanri key present");
    let range = view.posting_range(nanri_ord).expect("range");
    assert_eq!(range.count, 2);
    let indices = view.posting_entry_indices(range).expect("indices");
    assert_eq!(indices.len(), 2);

    let decoded_entry = view.entry(indices[0]).expect("decode compact entry");
    assert_eq!(decoded_entry.headword, NANRI);
    let payload_off = usize::try_from(view.header().payload_offset).unwrap();
    let payload_len = usize::try_from(view.header().payload_len).unwrap();
    let payload_slice = &out_a.bytes[payload_off..payload_off + payload_len];
    assert!(
        payload_slice
            .windows(NANRI.len())
            .any(|w| w == NANRI.as_bytes()),
        "compact string pool must store raw UTF-8 Tamil rather than editorial ASCII escapes"
    );
    assert!(
        !decoded_entry.headword.contains("\\u"),
        "decoded entry headword must remain raw UTF-8 Tamil"
    );

    let legacy =
        build_lexicon::compile_pack_dir_with_flags(&dir_a, Some(&schemas_a), Some("core"), 0)
            .expect("compile legacy core pack");
    let legacy_view = CompiledPackView::parse(&legacy.bytes).expect("parse legacy tlpack");
    let raw_nanri_payload = legacy_view
        .entry_payload_bytes(indices[0])
        .expect("legacy payload slice");
    let raw_str = std::str::from_utf8(raw_nanri_payload).expect("utf8 payload");
    assert!(
        raw_str.contains(NANRI) && !raw_str.contains("\\u0ba8"),
        "runtime payload must store compact UTF-8 Tamil rather than editorial ASCII escapes"
    );
    assert!(
        !raw_str.contains("\\u0ba8"),
        "runtime payload must not retain unnecessary \\u0ba8 escapes"
    );
}

#[test]
fn compiler_rejects_missing_extra_path_traversal_and_manifest_tampering() {
    // Missing tracked file
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("missing-file");
        fs::remove_file(dir.join("labels.csv")).expect("remove labels.csv");
        let err = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).unwrap_err();
        assert!(!err.is_empty());
    }

    // Extra unmanifested file
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("extra-file");
        fs::write(dir.join("unexpected.txt"), "rogue\n").expect("write extra");
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Path traversal inside packs.toml
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("path-traversal");
        let p = dir.join("packs.toml");
        let txt = fs::read_to_string(&p)
            .unwrap()
            .replace("labels.csv", "../labels.csv");
        fs::write(&p, txt).unwrap();
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Tampered CSV byte without updating packs.toml sha256/manifest
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("tamper-sha");
        let p = dir.join("ATTRIBUTION_AND_TERMS.md");
        let mut content = fs::read_to_string(&p).unwrap();
        content.push_str("\n<!-- tamper -->\n");
        fs::write(&p, content).unwrap();
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Tampered manifest_sha256 alone
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("tamper-manifest");
        let p = dir.join("packs.toml");
        let mut doc: toml::Value = toml::from_str(&fs::read_to_string(&p).unwrap()).unwrap();
        doc.as_table_mut().unwrap().insert(
            "manifest_sha256".to_owned(),
            toml::Value::String("0".repeat(64)),
        );
        fs::write(&p, toml::to_string_pretty(&doc).unwrap()).unwrap();
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // L3 unapproved pack (l3_pack_eligible = false) must never be treated as approved
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("not-l3-approved");
        let p = dir.join("packs.toml");
        let txt = fs::read_to_string(&p)
            .unwrap()
            .replace("l3_pack_eligible = true", "l3_pack_eligible = false");
        fs::write(&p, txt).unwrap();
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

#[test]
fn compiler_rejects_csv_bom_crlf_headers_and_raw_controls() {
    // UTF-8 BOM in CSV
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("csv-bom");
        let p = dir.join("entries.csv");
        let mut bytes = vec![0xEF, 0xBB, 0xBF];
        bytes.extend_from_slice(&fs::read(&p).unwrap());
        fs::write(&p, bytes).unwrap();
        recompute_packs_toml_manifest(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // CRLF in CSV
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("csv-crlf");
        rewrite_csv_and_remint_manifest(&dir, "entries.csv", |s| s.replace('\n', "\r\n"));
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Wrong CSV header column
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("csv-header");
        rewrite_csv_and_remint_manifest(&dir, "entries.csv", |s| {
            s.replacen("revision", "rev_bad", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Reject raw unescaped ZWJ in a JSON cell; fixture preserves the exact scalar.
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("raw-zwj");
        rewrite_csv_and_remint_manifest(&dir, "assertions.csv", |s| {
            s.replacen(
                "that moment",
                lexicon_unicode::fixture("raw_zwj_text")["value"]
                    .as_str()
                    .unwrap(),
                1,
            )
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Unsupported schema format / csv_encoding
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("bad-schema");
        let p = dir.join("schema.toml");
        let txt = fs::read_to_string(&p)
            .unwrap()
            .replace(EXPECTED_CANONICAL_FORMAT, "bad-format");
        fs::write(&p, txt).unwrap();
        recompute_packs_toml_manifest(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());

        let p = dir.join("schema.toml");
        let txt2 = fs::read_to_string(&p)
            .unwrap()
            .replace("bad-format", EXPECTED_CANONICAL_FORMAT)
            .replace(EXPECTED_CSV_ENCODING, "raw-ascii");
        fs::write(&p, txt2).unwrap();
        recompute_packs_toml_manifest(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

#[test]
fn compiler_rejects_notice_attribution_and_source_reuse_failures() {
    // Missing CC-BY-SA-4.0 notice
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("missing-cc");
        fs::remove_file(dir.join("notices").join("CC-BY-SA-4.0.md")).unwrap();
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Private local host path leaked in ATTRIBUTION_AND_TERMS.md
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("private-notice-path");
        let p = dir.join("ATTRIBUTION_AND_TERMS.md");
        let mut txt = fs::read_to_string(&p).unwrap();
        txt.push_str("\nRef: C:\\Users\\private\\secret.jsonl\n");
        fs::write(&p, txt).unwrap();
        recompute_packs_toml_manifest(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Unverified source
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("unverified-source");
        rewrite_csv_and_remint_manifest(&dir, "sources.csv", |s| {
            s.replacen(",verified,", ",unverified,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Non-permitted reuse state
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("restricted-source");
        rewrite_csv_and_remint_manifest(&dir, "sources.csv", |s| {
            s.replacen(",permitted,", ",restricted,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

#[test]
fn compiler_rejects_review_staleness_wrong_actor_and_invalid_auto_acceptance() {
    // Tampered assertion claim value (claim_revision_sha256 mismatch)
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("claim-tamper");
        rewrite_csv_and_remint_manifest(&dir, "assertions.csv", |s| {
            s.replacen("that moment", "tampered moment", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Tampered evidence row (evidence_bundle_sha256 mismatch)
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("evidence-tamper");
        rewrite_csv_and_remint_manifest(&dir, "evidence.csv", |s| {
            s.replacen("field=page.title", "field=page.tampered", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // accepted_human without actor_id
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("missing-human-actor");
        rewrite_csv_and_remint_manifest(&dir, "decisions.csv", |s| {
            s.replacen(",accepted_human,human,abish,", ",accepted_human,human,,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // accepted_auto_source on non-verbatim/changed/ambiguous assertion
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("invalid-auto-accept");
        rewrite_csv_and_remint_manifest(&dir, "decisions.csv", |s| {
            s.replacen(
                ",accepted_human,human,abish,",
                ",accepted_auto_source,automated,,",
                1,
            )
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Non-accepted terminal outcome (pending)
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("pending-decision");
        rewrite_csv_and_remint_manifest(&dir, "decisions.csv", |s| {
            s.replacen(",accepted_human,", ",pending,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

#[test]
fn compiler_rejects_fk_lifecycle_hierarchy_text_and_vocabulary_violations() {
    // Retired identity lifecycle
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("retired-identity");
        rewrite_csv_and_remint_manifest(&dir, "identities.csv", |s| {
            s.replacen(",active,", ",retired,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Self-cyclic sense hierarchy
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("sense-cycle");
        rewrite_csv_and_remint_manifest(&dir, "senses.csv", |s| {
            let mut lines: Vec<String> = s.lines().map(str::to_owned).collect();
            let first_sid = lines[1].split(',').next().unwrap().to_owned();
            lines[1] = format!("{}{first_sid}", lines[1]);
            lines.join("\n") + "\n"
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Unparsed text component
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("unparsed-text");
        rewrite_csv_and_remint_manifest(&dir, "texts.csv", |s| {
            s.replacen(",definition,", ",unparsed,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Entry-owned text
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("entry-owned-text");
        rewrite_csv_and_remint_manifest(&dir, "texts.csv", |s| s.replacen(",sense,", ",entry,", 1));
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Duplicate canonical written form in forms.csv + Missing canonical written form
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("no-canonical-written");
        rewrite_csv_and_remint_manifest(&dir, "forms.csv", |s| {
            s.replacen(",written,canonical,", ",written,variant,", 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Unknown POS vocabulary code
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("unknown-vocab");
        let p = dir.join("vocabularies.toml");
        let txt = fs::read_to_string(&p)
            .unwrap()
            .replace("\"NOUN\"", "\"VERB\"");
        fs::write(&p, txt).unwrap();
        recompute_packs_toml_manifest(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

#[test]
fn cross_pack_revision_conflicts_are_rejected_while_identical_revisions_succeed() {
    let mut pack_a = BTreeMap::new();
    pack_a.insert(NANRI_ID_1.to_owned(), "a".repeat(64));
    let mut pack_b_same = BTreeMap::new();
    pack_b_same.insert(NANRI_ID_1.to_owned(), "a".repeat(64));
    let mut pack_b_conflict = BTreeMap::new();
    pack_b_conflict.insert(NANRI_ID_1.to_owned(), "b".repeat(64));

    assert!(build_lexicon::validate_cross_pack_revisions(&[
        ("core", &pack_a),
        ("terminology", &pack_b_same),
    ])
    .is_ok());

    let err = build_lexicon::validate_cross_pack_revisions(&[
        ("core", &pack_a),
        ("terminology", &pack_b_conflict),
    ])
    .unwrap_err();
    assert!(err.contains(NANRI_ID_1));
}

#[test]
fn compiled_binary_rejects_checksum_bounds_and_overflow_tampering() {
    let (_tmp, dir, schemas) = clone_core_pack_to_temp("binary-tamper");
    let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
        .expect("compile valid pack");
    let valid = compiled.bytes;
    assert_eq!(&valid[0..8], &PACK_MAGIC);

    // Bit-flip in payload fails checksum
    let mut flipped = valid.clone();
    let last = flipped.len() - 1;
    flipped[last] ^= 0x01;
    assert!(CompiledPackView::parse(&flipped).is_err());

    // Truncated header fails
    assert!(CompiledPackView::parse(&valid[..HEADER_SIZE - 1]).is_err());

    // Corrupted magic fails
    let mut bad_magic = valid.clone();
    bad_magic[0] = b'X';
    assert!(CompiledPackView::parse(&bad_magic).is_err());

    // Corrupted / unsupported flags rejected (both raw mutation and with valid checksum)
    let mut bad_flags = valid.clone();
    bad_flags[16..20].copy_from_slice(&2u32.to_le_bytes());
    assert!(CompiledPackView::parse(&bad_flags).is_err());
    recompute_tlpack_checksum(&mut bad_flags);
    assert!(CompiledPackView::parse(&bad_flags).is_err());

    // Zero count in PostingRange rejected
    let zero_range = encode_posting_range_le(PostingRange { start: 0, count: 0 });
    assert!(decode_posting_range_le(&zero_range, 0, 10).is_err());

    // Out-of-bounds / u32 overflow in PostingRange rejected
    let overflow_range = encode_posting_range_le(PostingRange {
        start: u32::MAX,
        count: 2,
    });
    assert!(decode_posting_range_le(&overflow_range, 0, u32::MAX).is_err());

    // Out-of-bounds / u64 overflow in EntrySlice rejected
    let overflow_slice = encode_entry_slice_le(EntrySlice {
        offset: u64::MAX,
        len: 4,
    });
    assert!(decode_entry_slice_le(&overflow_slice, 0, u64::MAX).is_err());
}

#[test]
fn unexcepted_non_nfc_and_zwj_are_rejected_in_assertions() {
    // Non-NFC Tamil assertion value without unicode_exceptions row is rejected
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("non-nfc");
        // NFD sequence for 'கொ': U+0B95 U+0BC6 U+0BBE (NFC is U+0B95 U+0BCA)
        let unicode_case = lexicon_unicode::fixture("nfd_ko");
        let nfd_ko = unicode_case["value"].as_str().unwrap();
        assert_ne!(tamil_norm::normalize_nfc(nfd_ko), nfd_ko);
        rewrite_csv_and_remint_manifest(&dir, "assertions.csv", |s| {
            s.replacen("that moment", nfd_ko, 1)
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // Escaped ZWJ inside an assertion value without a reviewed scalar exception is rejected
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("unexcepted-zwj");
        rewrite_csv_and_remint_manifest(&dir, "assertions.csv", |s| {
            s.replacen(
                "that moment",
                lexicon_unicode::fixture("raw_zwj_text")["json"]
                    .as_str()
                    .unwrap()
                    .trim_matches('"'),
                1,
            )
        });
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
}

fn apply_headword_unicode_exceptions(
    dir: &Path,
    target_aid: &str,
    raw_text: &str,
    escaped_value_json: &str,
    zwj_pos: usize,
) {
    let mut asr_rdr = csv::Reader::from_path(dir.join("assertions.csv")).unwrap();
    let headers: Vec<String> = asr_rdr
        .headers()
        .unwrap()
        .iter()
        .map(str::to_owned)
        .collect();
    let mut rows: Vec<Vec<String>> = asr_rdr
        .records()
        .map(|r| r.unwrap().iter().map(str::to_owned).collect())
        .collect();
    let mut new_claim_rev = String::new();
    for row in &mut rows {
        if row[0] == target_aid {
            row[5] = escaped_value_json.to_owned();
            let claim_obj = serde_json::json!({
                "assertion_id": row[0],
                "subject_kind": row[1],
                "subject_id": row[2],
                "property_code": row[3],
                "value_state": row[4],
                "value_json": raw_text,
                "origin": row[6],
                "source_fidelity_state": row[7],
                "ambiguity_state": row[8],
                "algorithm_reference": Value::Null,
                "convention_reference": Value::Null,
                "imported_status_json": Value::Null,
                "imported_confidence_json": Value::Null,
            });
            let canon = build_lexicon::canonical_ascii_json(&claim_obj).unwrap();
            new_claim_rev = sha256_hex(canon.as_bytes());
            row[13] = new_claim_rev.clone();
        }
    }
    let mut wtr = csv::WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_path(dir.join("assertions.csv"))
        .unwrap();
    wtr.write_record(&headers).unwrap();
    for r in &rows {
        wtr.write_record(r).unwrap();
    }
    wtr.flush().unwrap();

    let mut dec_rdr = csv::Reader::from_path(dir.join("decisions.csv")).unwrap();
    let dec_headers: Vec<String> = dec_rdr
        .headers()
        .unwrap()
        .iter()
        .map(str::to_owned)
        .collect();
    let mut dec_rows: Vec<Vec<String>> = dec_rdr
        .records()
        .map(|r| r.unwrap().iter().map(str::to_owned).collect())
        .collect();
    let mut target_dec_id = String::new();
    for r in &mut dec_rows {
        if r[1] == target_aid {
            r[2] = new_claim_rev.clone();
            target_dec_id = r[0].clone();
        }
    }
    let mut dwtr = csv::WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_path(dir.join("decisions.csv"))
        .unwrap();
    dwtr.write_record(&dec_headers).unwrap();
    for r in &dec_rows {
        dwtr.write_record(r).unwrap();
    }
    dwtr.flush().unwrap();

    let val_hash = sha256_hex(raw_text.as_bytes());
    let seq_json =
        serde_json::to_string(&raw_text.chars().map(|c| c as u32).collect::<Vec<_>>()).unwrap();
    let zwj_pos_str = zwj_pos.to_string();
    let mut u_wtr = csv::WriterBuilder::new()
        .terminator(csv::Terminator::Any(b'\n'))
        .from_path(dir.join("unicode_exceptions.csv"))
        .unwrap();
    u_wtr
        .write_record([
            "assertion_id",
            "claim_revision_sha256",
            "value_sha256",
            "kind",
            "scalar_sequence",
            "scalar_position",
            "reason_json",
            "decision_id",
        ])
        .unwrap();
    u_wtr
        .write_record([
            target_aid,
            &new_claim_rev,
            &val_hash,
            "non_nfc_original",
            &seq_json,
            "0",
            "\"documented synthetic non-NFC source form\"",
            &target_dec_id,
        ])
        .unwrap();
    u_wtr
        .write_record([
            target_aid,
            &new_claim_rev,
            &val_hash,
            "intentional_control",
            "[8205]",
            &zwj_pos_str,
            "\"documented synthetic ZWJ joiner\"",
            &target_dec_id,
        ])
        .unwrap();
    u_wtr.flush().unwrap();
    recompute_packs_toml_manifest(dir);
}

#[test]
fn valid_unicode_exception_compiles_with_nfc_fst_key_and_preserved_zwj() {
    let (_tmp, dir, schemas) = clone_core_pack_to_temp("accepted-zwj-nfd");
    // Use existing form headword assertion ast_1c2d7143-f154-5703-8291-76b4727f5948 ("அந்நிலை")
    // and add a documented ZWJ + non-NFC Tamil sequence via unicode_exceptions.csv.
    // Separate the ZWJ with a space so UAX-29 keeps it out of the Tamil grapheme cluster
    // (Tamil+ZWJ in one cluster is unwaivable invalid_orthography per review rules).
    let target_aid = "ast_1c2d7143-f154-5703-8291-76b4727f5948";
    let unicode_case = lexicon_unicode::fixture("nfd_space_zwj");
    let new_headword_raw = unicode_case["value"].as_str().unwrap();
    let zwj = lexicon_unicode::fixture("zwj")["value"]
        .as_str()
        .unwrap()
        .chars()
        .next()
        .unwrap();
    let expected_nfc_key = tamil_norm::normalize_nfc(new_headword_raw);
    assert_ne!(new_headword_raw, expected_nfc_key);
    assert!(expected_nfc_key.contains(zwj));

    apply_headword_unicode_exceptions(
        &dir,
        target_aid,
        new_headword_raw,
        unicode_case["json"].as_str().unwrap(),
        4,
    );
    let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
        .expect("accepted unicode exceptions should compile cleanly");
    let view = CompiledPackView::parse(&compiled.bytes).unwrap();
    let fst = view.fst_map().unwrap();
    let ord = fst
        .get(expected_nfc_key.as_bytes())
        .expect("NFC key with preserved ZWJ must exist in FST");
    let indices = view
        .posting_entry_indices(view.posting_range(ord).unwrap())
        .unwrap();
    let entry = view.entry(indices[0]).unwrap();
    assert!(entry.headword.contains(zwj));

    // Also verify invalid_orthography (ZWJ attached directly inside a Tamil grapheme cluster)
    // remains non-waivable even when matching non_nfc_original + intentional_control exceptions exist.
    let (_tmp_bad, bad_dir, bad_schemas) = clone_core_pack_to_temp("unwaivable-orthography-zwj");
    apply_headword_unicode_exceptions(
        &bad_dir,
        target_aid,
        lexicon_unicode::fixture("nfd_zwj")["value"]
            .as_str()
            .unwrap(),
        lexicon_unicode::fixture("nfd_zwj")["json"]
            .as_str()
            .unwrap(),
        3,
    );
    let err = build_lexicon::compile_pack_dir(&bad_dir, Some(&bad_schemas), Some("core"))
        .expect_err("invalid_orthography must not be waivable by unicode_exceptions");
    assert!(
        err.contains("invalid_orthography"),
        "unexpected error: {err}"
    );
}

proptest! {
    #![proptest_config(ProptestConfig {
        cases: 10_000,
        failure_persistence: None,
        ..ProptestConfig::default()
    })]

    #[test]
    fn posting_range_and_entry_slice_checked_le_roundtrip(
        start in 0u32..1_000_000,
        count in 1u32..1_000,
        slack in 0u32..1_000,
        offset in 0u64..1_000_000_000,
        len in 1u64..1_000_000,
        u64_slack in 0u64..1_000_000,
    ) {
        let total_postings = start + count + slack;
        let encoded_range = encode_posting_range_le(PostingRange { start, count });
        let decoded_range = decode_posting_range_le(&encoded_range, 0, total_postings).unwrap();
        prop_assert_eq!(decoded_range, PostingRange { start, count });

        let too_small = start + count - 1;
        prop_assert!(decode_posting_range_le(&encoded_range, 0, too_small).is_err());

        let total_payload = offset + len + u64_slack;
        let encoded_slice = encode_entry_slice_le(EntrySlice { offset, len });
        let decoded_slice = decode_entry_slice_le(&encoded_slice, 0, total_payload).unwrap();
        prop_assert_eq!(decoded_slice, EntrySlice { offset, len });

        let too_small_payload = offset + len - 1;
        prop_assert!(decode_entry_slice_le(&encoded_slice, 0, too_small_payload).is_err());
    }

    #[test]
    fn canonical_ascii_json_produces_valid_pure_ascii_json(
        s in ".{0,64}",
        n in any::<i64>(),
        flag in any::<bool>(),
    ) {
        let val = json!({
            "z_str": s,
            "a_num": n,
            "m_flag": flag,
        });
        let encoded = build_lexicon::canonical_ascii_json(&val).expect("encode ascii json");
        prop_assert!(encoded.is_ascii(), "canonical JSON must be pure ASCII: {encoded}");
        let idx_a = encoded.find("\"a_num\"").unwrap();
        let idx_m = encoded.find("\"m_flag\"").unwrap();
        let idx_z = encoded.find("\"z_str\"").unwrap();
        prop_assert!(idx_a < idx_m && idx_m < idx_z, "keys must be sorted");
        let reparsed: Value = serde_json::from_str(&encoded).expect("roundtrip valid json");
        prop_assert_eq!(reparsed, val);
    }
}

fn append_csv_row(path: &Path, row: &[&str]) {
    let mut existing = fs::read_to_string(path).expect("read csv");
    if !existing.ends_with('\n') {
        existing.push('\n');
    }
    let mut wtr = csv::WriterBuilder::new()
        .has_headers(false)
        .terminator(csv::Terminator::Any(b'\n'))
        .from_writer(Vec::new());
    wtr.write_record(row).expect("write csv record");
    let encoded = String::from_utf8(wtr.into_inner().expect("flush")).expect("utf8");
    existing.push_str(&encoded);
    fs::write(path, existing).expect("write updated csv");
}

fn add_accepted_claim(
    dir: &Path,
    aid: &str,
    subject_kind: &str,
    subject_id: &str,
    property_code: &str,
    value: &Value,
    dec_id: &str,
) -> String {
    let value_json_str = build_lexicon::canonical_ascii_json(value).expect("encode value_json");
    let claim_obj = json!({
        "assertion_id": aid,
        "subject_kind": subject_kind,
        "subject_id": subject_id,
        "property_code": property_code,
        "value_state": "known",
        "value_json": value,
        "origin": "editorial",
        "source_fidelity_state": "verified",
        "ambiguity_state": "unambiguous",
        "algorithm_reference": Value::Null,
        "convention_reference": Value::Null,
        "imported_status_json": Value::Null,
        "imported_confidence_json": Value::Null,
    });
    let claim_rev = sha256_hex(
        build_lexicon::canonical_ascii_json(&claim_obj)
            .expect("canonical claim")
            .as_bytes(),
    );
    append_csv_row(
        &dir.join("assertions.csv"),
        &[
            aid,
            subject_kind,
            subject_id,
            property_code,
            "known",
            &value_json_str,
            "editorial",
            "verified",
            "unambiguous",
            "",
            "",
            "null",
            "null",
            &claim_rev,
        ],
    );

    let source_id = "src_2b7f1069-5437-5079-ac9a-77778e972340";
    let locator = format!("synthetic-test:{aid}");
    let locator_cell = build_lexicon::canonical_ascii_json(&json!(locator)).unwrap();
    let ext_sha = "a".repeat(64);
    let ev_arr = json!([{
        "assertion_id": aid,
        "source_id": source_id,
        "source_record_id": Value::Null,
        "locator_json": locator,
        "evidence_role": "supports",
        "extraction_version": "synthetic-v1",
        "extraction_sha256": ext_sha,
    }]);
    let ev_hash = sha256_hex(
        build_lexicon::canonical_ascii_json(&ev_arr)
            .expect("canonical ev")
            .as_bytes(),
    );
    append_csv_row(
        &dir.join("evidence.csv"),
        &[
            aid,
            source_id,
            "",
            &locator_cell,
            "supports",
            "synthetic-v1",
            &ext_sha,
        ],
    );
    append_csv_row(
        &dir.join("decisions.csv"),
        &[
            dec_id,
            aid,
            &claim_rev,
            &ev_hash,
            "accepted_human",
            "human",
            "abish",
            "synthetic-review-v1",
            "2026-11-15",
            "\"\"",
            "",
        ],
    );
    claim_rev
}

fn sync_full_packs_toml(dir: &Path) {
    let mut tracked_paths = Vec::new();
    fn walk_files(root: &Path, cur: &Path, out: &mut Vec<String>) {
        for entry in fs::read_dir(cur).unwrap() {
            let entry = entry.unwrap();
            let path = entry.path();
            let rel = path
                .strip_prefix(root)
                .unwrap()
                .components()
                .map(|c| c.as_os_str().to_string_lossy().into_owned())
                .collect::<Vec<_>>()
                .join("/");
            if path.is_dir() {
                walk_files(root, &path, out);
            } else if rel != "packs.toml" {
                out.push(rel);
            }
        }
    }
    walk_files(dir, dir, &mut tracked_paths);
    tracked_paths.sort();

    let packs_path = dir.join("packs.toml");
    let raw = fs::read_to_string(&packs_path).expect("read packs.toml");
    let mut doc: toml::Value = toml::from_str(&raw).expect("parse packs.toml");
    let table = doc.as_table_mut().expect("root table");

    let mut file_tables = Vec::new();
    let mut manifest_items = Vec::new();
    for rel in &tracked_paths {
        let bytes = fs::read(dir.join(rel)).unwrap();
        let sha = sha256_hex(&bytes);
        let len = i64::try_from(bytes.len()).unwrap();
        let mut ft = toml::map::Map::new();
        ft.insert("path".to_owned(), toml::Value::String(rel.clone()));
        ft.insert("sha256".to_owned(), toml::Value::String(sha.clone()));
        ft.insert("bytes".to_owned(), toml::Value::Integer(len));
        if rel.ends_with(".csv") {
            let rows = std::str::from_utf8(&bytes)
                .unwrap()
                .lines()
                .count()
                .saturating_sub(1);
            ft.insert(
                "rows".to_owned(),
                toml::Value::Integer(i64::try_from(rows).unwrap()),
            );
            match rel.as_str() {
                "assertions.csv" => {
                    table.insert(
                        "assertion_count".to_owned(),
                        toml::Value::Integer(i64::try_from(rows).unwrap()),
                    );
                }
                "relations.csv" => {
                    table.insert(
                        "relation_count".to_owned(),
                        toml::Value::Integer(i64::try_from(rows).unwrap()),
                    );
                }
                _ => {}
            }
        }
        file_tables.push(toml::Value::Table(ft));
        manifest_items.push(json!({"path": rel, "sha256": sha, "bytes": len}));
    }
    let manifest_sha = sha256_hex(
        build_lexicon::canonical_ascii_json(&Value::Array(manifest_items))
            .unwrap()
            .as_bytes(),
    );
    table.insert(
        "manifest_sha256".to_owned(),
        toml::Value::String(manifest_sha),
    );
    table.insert("files".to_owned(), toml::Value::Array(file_tables));
    fs::write(
        &packs_path,
        toml::to_string(&doc).unwrap().replace("\r\n", "\n"),
    )
    .unwrap();
}

fn update_packs_coverage(
    dir: &Path,
    region_codes: Vec<&str>,
    register_codes: Vec<&str>,
    unknown_region_entries: i64,
) {
    let packs_path = dir.join("packs.toml");
    let raw = fs::read_to_string(&packs_path).unwrap();
    let mut doc: toml::Value = toml::from_str(&raw).unwrap();
    let cov = doc
        .as_table_mut()
        .unwrap()
        .get_mut("coverage")
        .unwrap()
        .as_table_mut()
        .unwrap();
    cov.insert(
        "region_codes".to_owned(),
        toml::Value::Array(
            region_codes
                .into_iter()
                .map(|s| toml::Value::String(s.to_owned()))
                .collect(),
        ),
    );
    cov.insert(
        "register_codes".to_owned(),
        toml::Value::Array(
            register_codes
                .into_iter()
                .map(|s| toml::Value::String(s.to_owned()))
                .collect(),
        ),
    );
    cov.insert(
        "unknown_region_entries".to_owned(),
        toml::Value::Integer(unknown_region_entries),
    );
    fs::write(
        &packs_path,
        toml::to_string(&doc).unwrap().replace("\r\n", "\n"),
    )
    .unwrap();
}

fn merge_packs_coverage(
    dir: &Path,
    add_regions: &[&str],
    add_registers: &[&str],
    unknown_delta: i64,
) {
    let packs_path = dir.join("packs.toml");
    let raw = fs::read_to_string(&packs_path).unwrap();
    let mut doc: toml::Value = toml::from_str(&raw).unwrap();
    let cov = doc
        .as_table_mut()
        .unwrap()
        .get_mut("coverage")
        .unwrap()
        .as_table_mut()
        .unwrap();
    for (key, additions) in [
        ("region_codes", add_regions),
        ("register_codes", add_registers),
    ] {
        let mut items: Vec<String> = cov
            .get(key)
            .and_then(toml::Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|v| v.as_str().map(str::to_owned))
            .collect();
        for add in additions {
            if !items.iter().any(|existing| existing == add) {
                items.push((*add).to_owned());
            }
        }
        items.sort();
        cov.insert(
            key.to_owned(),
            toml::Value::Array(items.into_iter().map(toml::Value::String).collect()),
        );
    }
    let prev_unknown = cov
        .get("unknown_region_entries")
        .and_then(toml::Value::as_integer)
        .unwrap_or(0);
    cov.insert(
        "unknown_region_entries".to_owned(),
        toml::Value::Integer(prev_unknown + unknown_delta),
    );
    fs::write(
        &packs_path,
        toml::to_string(&doc).unwrap().replace("\r\n", "\n"),
    )
    .unwrap();
}

fn merge_vocabularies_toml(
    dir: &Path,
    add_domains: &[&str],
    add_relations: &[&str],
    add_temporals: &[&str],
    add_varieties: &[&str],
    add_regions: &[(&str, Option<&str>)],
) {
    let vocab_path = dir.join("vocabularies.toml");
    let raw = fs::read_to_string(&vocab_path).unwrap();
    let mut doc: toml::Value = toml::from_str(&raw).unwrap();
    let table = doc.as_table_mut().unwrap();
    for (key, additions) in [
        ("domains", add_domains),
        ("relation_codes", add_relations),
        ("temporals", add_temporals),
        ("varieties", add_varieties),
    ] {
        let mut items: Vec<String> = table
            .get(key)
            .and_then(toml::Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|v| v.as_str().map(str::to_owned))
            .collect();
        for add in additions {
            if !items.iter().any(|existing| existing == add) {
                items.push((*add).to_owned());
            }
        }
        items.sort();
        table.insert(
            key.to_owned(),
            toml::Value::Array(items.into_iter().map(toml::Value::String).collect()),
        );
    }
    if !add_regions.is_empty() {
        let mut regs = table
            .get("regions")
            .and_then(toml::Value::as_array)
            .cloned()
            .unwrap_or_default();
        for (code, parent) in add_regions {
            let exists = regs.iter().any(|r| {
                r.as_table()
                    .and_then(|t| t.get("code"))
                    .and_then(toml::Value::as_str)
                    == Some(*code)
            });
            if !exists {
                let mut rt = toml::map::Map::new();
                rt.insert("code".to_owned(), toml::Value::String((*code).to_owned()));
                if let Some(p) = parent {
                    rt.insert(
                        "parent_code".to_owned(),
                        toml::Value::String((*p).to_owned()),
                    );
                }
                regs.push(toml::Value::Table(rt));
            }
        }
        table.insert("regions".to_owned(), toml::Value::Array(regs));
    }
    fs::write(
        &vocab_path,
        toml::to_string(&doc).unwrap().replace("\r\n", "\n"),
    )
    .unwrap();
}

#[test]
fn compiler_enforces_scope_ownership_property_provenance_and_cardinality() {
    let ent_id = "ent_5e50b59e-3d35-52af-a248-fd4a0de475de";
    let other_ent_id = "ent_9469d6ba-b9ac-563d-9a16-c5d77397f148";
    let unowned_pos_aid = "ast_429209cd-e65f-5689-b396-92150a3781cd";
    let unowned_pos_dec = "dec_82476765-95be-593c-aa59-a847e9e4f58f";

    // (1a) Scope pointing to an assertion owned by another entity must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("scope-wrong-owner");
        add_accepted_claim(
            &dir,
            "ast_scope_wrong_owner",
            "entry",
            other_ent_id,
            "region_scope",
            &json!("unrestricted"),
            "dec_scope_wrong_owner",
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!(
                    "entry,{ent_id},region,unrestricted,,ast_scope_wrong_owner,dec_scope_wrong_owner"
                ),
                1,
            )
        });
        update_packs_coverage(&dir, vec![], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "scope with wrong assertion owner must be rejected"
        );
    }

    // (1b) Scope pointing to wrong assertion property (part_of_speech instead of region_scope) must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("scope-wrong-prop");
        let _ = unowned_pos_aid;
        let _ = unowned_pos_dec;
        add_accepted_claim(
            &dir,
            "ast_scope_wrong_prop",
            "entry",
            ent_id,
            "part_of_speech",
            &json!("NOUN"),
            "dec_scope_wrong_prop",
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!(
                    "entry,{ent_id},region,unrestricted,,ast_scope_wrong_prop,dec_scope_wrong_prop"
                ),
                1,
            )
        });
        update_packs_coverage(&dir, vec![], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "scope with non-scope property_code must be rejected"
        );
    }

    // (1c) Region label whose evidence_reference is a source_id rather than an accepted assertion must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("scope-label-source-bypass");
        add_accepted_claim(
            &dir,
            "ast_reg_jaffna",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK-JAFFNA"),
            "dec_reg_jaffna",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK-JAFFNA",
                "region",
                "\"Jaffna\"",
                "\"Northern Peninsula\"",
                "src_2b7f1069-5437-5079-ac9a-77778e972340",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!("entry,{ent_id},region,attested,LK-JAFFNA,ast_reg_jaffna,dec_reg_jaffna"),
                1,
            )
        });
        update_packs_coverage(&dir, vec!["LK-JAFFNA"], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "label evidence_reference must be an accepted assertion, not a raw source_id"
        );
    }

    // (1d) Conflicting scope states (attested + unrestricted) on same subject/dimension must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("scope-conflict-states");
        add_accepted_claim(
            &dir,
            "ast_reg_lbl_ev",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK"),
            "dec_reg_lbl_ev",
        );
        add_accepted_claim(
            &dir,
            "ast_reg_att",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK"),
            "dec_reg_att",
        );
        add_accepted_claim(
            &dir,
            "ast_reg_unr",
            "entry",
            ent_id,
            "region_scope",
            &json!("unrestricted"),
            "dec_reg_unr",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK",
                "region",
                "\"Sri Lanka\"",
                "\"Island region\"",
                "ast_reg_lbl_ev",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            let replaced = s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!("entry,{ent_id},region,attested,LK,ast_reg_att,dec_reg_att"),
                1,
            );
            format!("{replaced}entry,{ent_id},region,unrestricted,,ast_reg_unr,dec_reg_unr\n")
        });
        update_packs_coverage(&dir, vec!["LK"], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "conflicting attested and unrestricted scope states must be rejected"
        );
    }
}

#[test]
fn compiler_supports_vocabularies_finite_registries_and_region_hierarchy() {
    let ent_id = "ent_5e50b59e-3d35-52af-a248-fd4a0de475de";

    // (2a) Valid Python-promoted vocabularies.toml with domains, temporals, varieties, and [[regions]]
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-full-valid");
        add_accepted_claim(
            &dir,
            "ast_lbl_lk",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK"),
            "dec_lbl_lk",
        );
        add_accepted_claim(
            &dir,
            "ast_scope_jaffna",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK-JAFFNA"),
            "dec_scope_jaffna",
        );
        add_accepted_claim(
            &dir,
            "ast_scope_dom",
            "entry",
            ent_id,
            "domain_scope",
            &json!("syntax_test"),
            "dec_scope_dom",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK",
                "region",
                "\"Sri Lanka\"",
                "\"Island region\"",
                "ast_lbl_lk",
                "",
            ],
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK-JAFFNA",
                "region",
                "\"Jaffna\"",
                "\"Northern Jaffna region\"",
                "ast_lbl_lk",
                "LK",
            ],
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "dom-test",
                "1",
                "syntax_test",
                "domain",
                "\"Syntax Test\"",
                "\"Syntactic test domain\"",
                "ast_scope_dom",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            let r1 = s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!(
                    "entry,{ent_id},region,attested,LK-JAFFNA,ast_scope_jaffna,dec_scope_jaffna"
                ),
                1,
            );
            r1.replacen(
                &format!("entry,{ent_id},domain,unknown,,,"),
                &format!("entry,{ent_id},domain,attested,syntax_test,ast_scope_dom,dec_scope_dom"),
                1,
            )
        });
        merge_vocabularies_toml(
            &dir,
            &["syntax_test"],
            &[],
            &["modern"],
            &["literary"],
            &[("LK", None), ("LK-JAFFNA", Some("LK"))],
        );
        merge_packs_coverage(&dir, &["LK-JAFFNA"], &[], -1);
        sync_full_packs_toml(&dir);
        let out = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
            .expect("Python-promoted vocabularies.toml with domains/temporals/varieties/regions must compile");
        assert!(CompiledPackView::parse(&out.bytes).is_ok());
    }

    // (2b) Cyclic [[regions]] in vocabularies.toml must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-region-cycle");
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n\n",
            "[[regions]]\n",
            "code = \"REG-A\"\n",
            "parent_code = \"REG-B\"\n\n",
            "[[regions]]\n",
            "code = \"REG-B\"\n",
            "parent_code = \"REG-A\"\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "cyclic region hierarchy in vocabularies.toml must be rejected"
        );
    }

    // (2c) labels.csv region parent_code disagreeing with vocabularies.toml must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-label-parent-mismatch");
        add_accepted_claim(
            &dir,
            "ast_lbl_lk2",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK"),
            "dec_lbl_lk2",
        );
        add_accepted_claim(
            &dir,
            "ast_scope_jaffna2",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK-JAFFNA"),
            "dec_scope_jaffna2",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK",
                "region",
                "\"Sri Lanka\"",
                "\"Island region\"",
                "ast_lbl_lk2",
                "",
            ],
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK-JAFFNA",
                "region",
                "\"Jaffna\"",
                "\"Northern Jaffna region\"",
                "ast_lbl_lk2",
                "LK",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!(
                    "entry,{ent_id},region,attested,LK-JAFFNA,ast_scope_jaffna2,dec_scope_jaffna2"
                ),
                1,
            )
        });
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n\n",
            "[[regions]]\n",
            "code = \"LK\"\n\n",
            "[[regions]]\n",
            "code = \"LK-JAFFNA\"\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        update_packs_coverage(&dir, vec!["LK-JAFFNA"], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "labels.csv parent_code mismatch vs vocabularies.toml [[regions]] must be rejected"
        );
    }

    // (2d) Omitted [[regions]] must fail when an attested region scope is present
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-omitted-region");
        add_accepted_claim(
            &dir,
            "ast_reg_omitted",
            "entry",
            ent_id,
            "region_scope",
            &json!("LK"),
            "dec_reg_omitted",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "geo-test",
                "1",
                "LK",
                "region",
                "\"Sri Lanka\"",
                "\"Island region\"",
                "ast_reg_omitted",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},region,unknown,,,"),
                &format!("entry,{ent_id},region,attested,LK,ast_reg_omitted,dec_reg_omitted"),
                1,
            )
        });
        update_packs_coverage(&dir, vec!["LK"], vec![], 5);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "omitted [[regions]] must fail when attested region scope exists"
        );
    }

    // (2e) Empty/omitted domains must fail when an attested domain scope is present
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-empty-domain");
        add_accepted_claim(
            &dir,
            "ast_dom_empty",
            "entry",
            ent_id,
            "domain_scope",
            &json!("grammar"),
            "dec_dom_empty",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "dom-test",
                "1",
                "grammar",
                "domain",
                "\"Grammar\"",
                "\"Grammatical term\"",
                "ast_dom_empty",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},domain,unknown,,,"),
                &format!("entry,{ent_id},domain,attested,grammar,ast_dom_empty,dec_dom_empty"),
                1,
            )
        });
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n",
            "domains = []\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "empty domains must fail when attested domain scope exists"
        );
    }

    // (2f) Empty/omitted temporals must fail when an attested period scope is present
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-empty-period");
        add_accepted_claim(
            &dir,
            "ast_per_empty",
            "entry",
            ent_id,
            "temporal_scope",
            &json!("classical"),
            "dec_per_empty",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "per-test",
                "1",
                "classical",
                "period",
                "\"Classical\"",
                "\"Classical period\"",
                "ast_per_empty",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},period,unknown,,,"),
                &format!("entry,{ent_id},period,attested,classical,ast_per_empty,dec_per_empty"),
                1,
            )
        });
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n",
            "temporals = []\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "empty temporals must fail when attested period scope exists"
        );
    }

    // (2g) Entry variety_id with empty varieties or unlisted value fails; listed variety succeeds
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-empty-variety");
        let baseline_vocab = fs::read_to_string(dir.join("vocabularies.toml")).unwrap();
        rewrite_csv_and_remint_manifest(&dir, "entries.csv", |s| {
            s.replacen(
                &format!("{ent_id},tam,,"),
                &format!("{ent_id},tam,literary,"),
                1,
            )
        });
        let empty_vocab = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n",
            "varieties = []\n",
        );
        let mut fixture_vocab: toml::Value = toml::from_str(&baseline_vocab).unwrap();
        fixture_vocab.as_table_mut().unwrap().insert(
            "varieties".to_owned(),
            toml::from_str::<toml::Value>(empty_vocab).unwrap()["varieties"].clone(),
        );
        fs::write(
            dir.join("vocabularies.toml"),
            toml::to_string(&fixture_vocab).unwrap(),
        )
        .unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "entry variety_id with empty varieties must be rejected"
        );

        let unlisted_vocab = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = []\n",
            "varieties = [\"spoken\"]\n",
        );
        fixture_vocab["varieties"] =
            toml::from_str::<toml::Value>(unlisted_vocab).unwrap()["varieties"].clone();
        fs::write(
            dir.join("vocabularies.toml"),
            toml::to_string(&fixture_vocab).unwrap(),
        )
        .unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "entry variety_id missing from varieties registry must be rejected"
        );

        fs::write(dir.join("vocabularies.toml"), baseline_vocab).unwrap();
        merge_vocabularies_toml(&dir, &[], &[], &[], &["literary"], &[]);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_ok(),
            "listed entry variety_id must compile"
        );
    }

    // (2h) Valid period scope using temporal_scope or period_scope alias compiles cleanly
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("vocab-valid-period-alias");
        add_accepted_claim(
            &dir,
            "ast_per_temporal_alias",
            "entry",
            ent_id,
            "temporal_scope",
            &json!("classical"),
            "dec_per_temporal_alias",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "per-test",
                "1",
                "classical",
                "period",
                "\"Classical\"",
                "\"Classical period\"",
                "ast_per_temporal_alias",
                "",
            ],
        );
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},period,unknown,,,"),
                &format!(
                    "entry,{ent_id},period,attested,classical,ast_per_temporal_alias,dec_per_temporal_alias"
                ),
                1,
            )
        });
        merge_vocabularies_toml(&dir, &[], &[], &["classical"], &[], &[]);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_ok(),
            "period scope backed by temporal_scope alias must compile"
        );
    }
}

#[test]
fn compiler_handles_register_not_applicable_and_rejects_multirow_register() {
    let ent_id = "ent_5e50b59e-3d35-52af-a248-fd4a0de475de";

    // (3a) register state not_applicable preserves availability = "not_applicable"
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("register-na");
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            s.replacen(
                &format!("entry,{ent_id},register,unknown,,,"),
                &format!("entry,{ent_id},register,not_applicable,,,"),
                1,
            )
        });
        sync_full_packs_toml(&dir);
        let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
            .expect("register not_applicable should compile cleanly");
        let view = CompiledPackView::parse(&compiled.bytes).unwrap();
        let entry = (0..view.header().entry_count)
            .map(|i| view.entry(i).unwrap())
            .find(|e| e.entry_id == ent_id)
            .unwrap();
        assert_eq!(entry.register.availability, "not_applicable");
        assert_eq!(entry.register.value, None);
        assert!(entry.register.provenance.is_empty());
    }

    // (3b) multirow register on same subject must be rejected rather than silently ignored
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("register-multirow");
        add_accepted_claim(
            &dir,
            "ast_reg_formal",
            "entry",
            ent_id,
            "register_scope",
            &json!("formal"),
            "dec_reg_formal",
        );
        add_accepted_claim(
            &dir,
            "ast_reg_lit",
            "entry",
            ent_id,
            "register_scope",
            &json!("literary"),
            "dec_reg_lit",
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "reg-test",
                "1",
                "formal",
                "register",
                "\"Formal\"",
                "\"Formal register\"",
                "ast_reg_formal",
                "",
            ],
        );
        append_csv_row(
            &dir.join("labels.csv"),
            &[
                "reg-test",
                "1",
                "literary",
                "register",
                "\"Literary\"",
                "\"Literary register\"",
                "ast_reg_lit",
                "",
            ],
        );
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = []\n",
            "annotation_properties = []\n",
            "registers = [\"formal\", \"literary\"]\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
            let replaced = s.replacen(
                &format!("entry,{ent_id},register,unknown,,,"),
                &format!("entry,{ent_id},register,attested,formal,ast_reg_formal,dec_reg_formal"),
                1,
            );
            format!("{replaced}entry,{ent_id},register,attested,literary,ast_reg_lit,dec_reg_lit\n")
        });
        update_packs_coverage(&dir, vec![], vec!["formal", "literary"], 6);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "multirow register must be rejected instead of silently ignoring rows 2..N"
        );
    }
}

#[test]
fn compiler_validates_relations_and_rejects_unsupported_entry_level_relations() {
    let ent_a = "ent_5e50b59e-3d35-52af-a248-fd4a0de475de";
    let ent_b = "ent_9469d6ba-b9ac-563d-9a16-c5d77397f148";
    let sen_a = "sen_28f47fad-a25a-5f7b-8a52-d80aecf26084";

    // (4a) Valid sense -> entry relation preserves typed endpoints & symmetric projection
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("rel-sense-to-entry");
        let rid = "rel_valid_s_e";
        add_accepted_claim(
            &dir,
            "ast_rel_code_ok",
            "relation",
            rid,
            "relation_code",
            &json!("synonym"),
            "dec_rel_code_ok",
        );
        append_csv_row(
            &dir.join("identities.csv"),
            &[rid, "relation", "test:rel:ok", "active", ""],
        );
        append_csv_row(
            &dir.join("relations.csv"),
            &[
                rid,
                "sense",
                sen_a,
                "entry",
                ent_b,
                "ast_rel_code_ok",
                "undirected",
                "",
            ],
        );
        merge_vocabularies_toml(&dir, &[], &["synonym"], &[], &[], &[]);
        sync_full_packs_toml(&dir);
        let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
            .expect("valid sense->entry relation compiles");
        let view = CompiledPackView::parse(&compiled.bytes).unwrap();
        let entry = (0..view.header().entry_count)
            .map(|i| view.entry(i).unwrap())
            .find(|e| e.entry_id == ent_a)
            .unwrap();
        let sense = entry.senses.iter().find(|s| s.sense_id == sen_a).unwrap();
        assert_eq!(sense.relations.len(), 1);
        assert_eq!(sense.relations[0].directionality, "symmetric");
        assert_eq!(sense.relations[0].source.kind, "sense");
        assert_eq!(sense.relations[0].target.kind, "entry");
        assert_eq!(sense.relations[0].target.id, ent_b);
    }

    // (4b) Relation code assertion owned by wrong subject must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("rel-wrong-owner");
        let rid = "rel_wrong_owner";
        add_accepted_claim(
            &dir,
            "ast_rel_wrong_owner",
            "entry",
            ent_a,
            "relation_code",
            &json!("synonym"),
            "dec_rel_wrong_owner",
        );
        append_csv_row(
            &dir.join("identities.csv"),
            &[rid, "relation", "test:rel:bad-owner", "active", ""],
        );
        append_csv_row(
            &dir.join("relations.csv"),
            &[
                rid,
                "sense",
                sen_a,
                "entry",
                ent_b,
                "ast_rel_wrong_owner",
                "directed",
                "",
            ],
        );
        let vocab_toml = concat!(
            "schema_version = 1\n",
            "vocabulary_version = \"1\"\n",
            "language_ids = [\"eng\", \"tam\"]\n",
            "parts_of_speech = [\"INTJ\", \"NOUN\"]\n",
            "relation_codes = [\"synonym\"]\n",
            "annotation_properties = [\"relation_code\"]\n",
            "registers = []\n",
        );
        fs::write(dir.join("vocabularies.toml"), vocab_toml).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "relation_code assertion not owned by relation must fail"
        );
    }

    // (4c) Entry-level relation (source_kind == "entry") must be rejected rather than silently dropped
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("rel-entry-source");
        let rid = "rel_entry_src";
        add_accepted_claim(
            &dir,
            "ast_rel_entry_src",
            "relation",
            rid,
            "relation_code",
            &json!("synonym"),
            "dec_rel_entry_src",
        );
        append_csv_row(
            &dir.join("identities.csv"),
            &[rid, "relation", "test:rel:entry-src", "active", ""],
        );
        append_csv_row(
            &dir.join("relations.csv"),
            &[
                rid,
                "entry",
                ent_a,
                "entry",
                ent_b,
                "ast_rel_entry_src",
                "directed",
                "",
            ],
        );
        merge_vocabularies_toml(&dir, &[], &["synonym"], &[], &[], &[]);
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "unsupported entry-level relation must fail explicitly instead of being silently dropped"
        );
    }
}

#[test]
fn compiler_aligns_core_structural_properties_with_python() {
    let ent_id = "ent_5e50b59e-3d35-52af-a248-fd4a0de475de";
    let (_tmp, dir, schemas) = clone_core_pack_to_temp("core-structural-props");
    for (idx, prop) in [
        "region_scope",
        "register_scope",
        "domain_scope",
        "temporal_scope",
        "period_scope",
        "variety_scope",
        "social_usage_scope",
        "grammar_system_scope",
        "scope_attestation",
        "pronunciation_ipa",
        "transliteration",
        "orthography_convention",
        "unparsed_text",
    ]
    .iter()
    .enumerate()
    {
        add_accepted_claim(
            &dir,
            &format!("ast_core_prop_{idx}"),
            "entry",
            ent_id,
            prop,
            &json!("sample"),
            &format!("dec_core_prop_{idx}"),
        );
    }
    rewrite_csv_and_remint_manifest(&dir, "scopes.csv", |s| {
        s.replacen(
            &format!("entry,{ent_id},region,unknown,,,"),
            &format!("entry,{ent_id},region,unrestricted,,ast_core_prop_0,dec_core_prop_0"),
            1,
        )
    });
    merge_packs_coverage(&dir, &[], &[], -1);
    sync_full_packs_toml(&dir);
    let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
        .expect("Python CORE_STRUCTURAL_PROPERTIES must be accepted without annotation_properties");
    let view = CompiledPackView::parse(&compiled.bytes).unwrap();
    let entry = (0..view.header().entry_count)
        .map(|i| view.entry(i).unwrap())
        .find(|e| e.entry_id == ent_id)
        .unwrap();
    assert!(
        entry.annotations.is_empty(),
        "core structural properties must not leak into public annotations"
    );
}

#[test]
fn compiler_aligns_notice_validation_for_non_cc_and_cc_packs() {
    // (7a) Non-CC pack without CC-BY-SA-4.0 files or notices/ATTRIBUTION_AND_LICENSE.md compiles
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("non-cc-pack");
        fs::remove_file(dir.join("notices").join("CC-BY-SA-4.0.md")).unwrap();
        fs::remove_file(dir.join("notices").join("ATTRIBUTION_AND_LICENSE.md")).unwrap();
        fs::remove_dir(dir.join("notices")).unwrap();

        let mut src_rdr = csv::Reader::from_path(dir.join("sources.csv")).unwrap();
        let headers = src_rdr.headers().unwrap().clone();
        let mut rows: Vec<Vec<String>> = src_rdr
            .records()
            .map(|r| r.unwrap().iter().map(str::to_owned).collect())
            .collect();
        let mut terms_lines = vec![
            "# Attribution and Reuse Terms: `core`".to_owned(),
            String::new(),
        ];
        for r in &mut rows {
            r[12] = "\"MIT-Data-1.0\"".to_owned();
            r[14] = "\"Synthetic Clean Attribution\"".to_owned();
            r[15] = "\"https://example.org/terms\"".to_owned();
            terms_lines.push(format!("## Source `{}`", r[0]));
            terms_lines.push("- Attribution Text: Synthetic Clean Attribution".to_owned());
        }
        let mut wtr = csv::WriterBuilder::new()
            .terminator(csv::Terminator::Any(b'\n'))
            .from_path(dir.join("sources.csv"))
            .unwrap();
        wtr.write_record(&headers).unwrap();
        for r in &rows {
            wtr.write_record(r).unwrap();
        }
        wtr.flush().unwrap();
        fs::write(
            dir.join("ATTRIBUTION_AND_TERMS.md"),
            terms_lines.join("\n") + "\n",
        )
        .unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_ok(),
            "non-CC pack without CC-BY-SA-4.0 notice files must compile"
        );
    }

    // (7b) CC-BY-SA-4.0 stub lacking pinned legal text body (even with header phrase & URI & hash) fails
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("cc-stub-body");
        let stub = concat!(
            "# Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)\n\n",
            "- Canonical License URI: https://creativecommons.org/licenses/by-sa/4.0/legalcode\n",
            "- Source Legal Text File: `notices/cc_by_sa_4_0_legalcode.txt`\n",
            "- Source SHA-256: `28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5`\n\n",
            "---\n\n",
            "Attribution-ShareAlike 4.0 International\nStubbed truncated text.\n",
        );
        fs::write(dir.join("notices").join("CC-BY-SA-4.0.md"), stub).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "CC-BY-SA-4.0.md with altered/truncated legal body must fail pinned SHA-256 verification"
        );
    }

    // (7c) CC-BY-SA-4.0 missing canonical URI in CC-BY-SA-4.0.md fails
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("cc-missing-uri");
        let p = dir.join("notices").join("CC-BY-SA-4.0.md");
        let txt = fs::read_to_string(&p).unwrap().replace(
            "https://creativecommons.org/licenses/by-sa/4.0/legalcode",
            "https://example.org/other-license",
        );
        fs::write(&p, txt).unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "CC-BY-SA-4.0.md missing canonical URI must fail"
        );
    }

    // (7d) Notice with private *_api.json, non-NFC Unicode, or D:\ path must fail
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("notice-private-api-json");
        let p = dir.join("ATTRIBUTION_AND_TERMS.md");
        let mut txt = fs::read_to_string(&p).unwrap();
        txt.push_str("\nSee wiktionary_api.json for dump.\n");
        fs::write(&p, txt).unwrap();
        sync_full_packs_toml(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("notice-non-nfc");
        let p = dir.join("ATTRIBUTION_AND_TERMS.md");
        let mut txt = fs::read_to_string(&p).unwrap();
        txt.push_str(&format!(
            "\n{}\n",
            lexicon_unicode::fixture("nfd_ko")["value"]
                .as_str()
                .unwrap()
        ));
        fs::write(&p, txt).unwrap();
        sync_full_packs_toml(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("notice-d-drive");
        let p = dir.join("ATTRIBUTION_AND_TERMS.md");
        let mut txt = fs::read_to_string(&p).unwrap();
        txt.push_str("\nSource path: D:\\builds\\notes.txt\n");
        fs::write(&p, txt).unwrap();
        sync_full_packs_toml(&dir);
        assert!(build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err());
    }

    // (7e) CC-BY-SA-4.0 source with remote/bibliographic locator still requires pinned CC notice
    {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp("cc-remote-no-notice");
        fs::remove_file(dir.join("notices").join("CC-BY-SA-4.0.md")).unwrap();
        let mut src_rdr = csv::Reader::from_path(dir.join("sources.csv")).unwrap();
        let headers = src_rdr.headers().unwrap().clone();
        let mut rows: Vec<Vec<String>> = src_rdr
            .records()
            .map(|r| r.unwrap().iter().map(str::to_owned).collect())
            .collect();
        for r in &mut rows {
            r[12] = "\"CC-BY-SA-4.0\"".to_owned();
            r[15] = "\"https://creativecommons.org/licenses/by-sa/4.0/\"".to_owned();
        }
        let mut wtr = csv::WriterBuilder::new()
            .terminator(csv::Terminator::Any(b'\n'))
            .from_path(dir.join("sources.csv"))
            .unwrap();
        wtr.write_record(&headers).unwrap();
        for r in &rows {
            wtr.write_record(r).unwrap();
        }
        wtr.flush().unwrap();
        sync_full_packs_toml(&dir);
        assert!(
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).is_err(),
            "CC-BY-SA-4.0 source with remote attribution_reference still requires notices/CC-BY-SA-4.0.md"
        );
    }
}

#[test]
fn compiler_rejects_optional_scope_backing_and_invalid_translation_pairs() {
    for mutation in [
        "decision_only",
        "wrong_claim",
        "paired_self",
        "paired_nontranslation",
    ] {
        let (_tmp, dir, schemas) = clone_core_pack_to_temp(mutation);
        let (table, column, value) = if mutation == "decision_only" {
            ("scopes.csv", "decision_id", "dec_missing".to_owned())
        } else if mutation == "wrong_claim" {
            (
                "scopes.csv",
                "supporting_assertion_id",
                "ast_missing".to_owned(),
            )
        } else {
            let mut reader = csv::Reader::from_path(dir.join("texts.csv")).unwrap();
            let rows = reader.records().map(Result::unwrap).collect::<Vec<_>>();
            let target = if mutation == "paired_self" { 0 } else { 1 };
            (
                "texts.csv",
                "paired_translation_id",
                rows[target][0].to_owned(),
            )
        };
        rewrite_csv_and_remint_manifest(&dir, table, |content| {
            let mut reader = csv::Reader::from_reader(content.as_bytes());
            let header = reader.headers().unwrap().clone();
            let col = header.iter().position(|h| h == column).unwrap();
            let mut rows = reader.records().map(Result::unwrap).collect::<Vec<_>>();
            let mut row = rows[0].iter().map(str::to_owned).collect::<Vec<_>>();
            row[col] = value.clone();
            if table == "scopes.csv" {
                row[header.iter().position(|h| h == "state").unwrap()] = "unknown".to_owned();
                row[header.iter().position(|h| h == "label_code").unwrap()] = String::new();
            }
            rows[0] = csv::StringRecord::from(row);
            let mut writer = csv::WriterBuilder::new()
                .terminator(csv::Terminator::Any(b'\n'))
                .from_writer(Vec::new());
            writer.write_record(&header).unwrap();
            for row in rows {
                writer.write_record(&row).unwrap();
            }
            String::from_utf8(writer.into_inner().unwrap()).unwrap()
        });
        sync_full_packs_toml(&dir);
        let error =
            build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core")).unwrap_err();
        assert!(
            error.contains("scope") || error.contains("paired_translation"),
            "{mutation}: {error}"
        );
    }
}

fn recompute_tlpack_checksum(bytes: &mut [u8]) {
    let mut hasher = Sha256::new();
    hasher.update(&bytes[..CHECKSUM_OFFSET]);
    hasher.update(&bytes[HEADER_SIZE..]);
    let digest: [u8; 32] = hasher.finalize().into();
    bytes[CHECKSUM_OFFSET..HEADER_SIZE].copy_from_slice(&digest);
}

#[test]
fn compact_interned_pack_matches_legacy_json_round_trip_and_shrinks_core() {
    let (_tmp, dir, schemas) = clone_full_core_pack_to_temp("compact-vs-legacy");
    let legacy = build_lexicon::compile_pack_dir_with_flags(&dir, Some(&schemas), Some("core"), 0)
        .expect("compile legacy core pack");
    let compact = build_lexicon::compile_pack_dir_with_flags(
        &dir,
        Some(&schemas),
        Some("core"),
        PACK_FLAG_COMPACT_INTERNED,
    )
    .expect("compile compact core pack");

    let default_compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
        .expect("default compile emits compact format");
    assert_eq!(default_compiled.bytes, compact.bytes);

    let legacy_view = CompiledPackView::parse(&legacy.bytes).expect("parse legacy view");
    let compact_view = CompiledPackView::parse(&compact.bytes).expect("parse compact view");

    assert_eq!(legacy_view.header().flags, 0);
    assert_eq!(compact_view.header().flags, PACK_FLAG_COMPACT_INTERNED);
    assert_eq!(
        compact_view.metadata().expect("compact meta"),
        legacy_view.metadata().expect("legacy meta")
    );
    assert_eq!(
        compact_view.header().entry_count,
        legacy_view.header().entry_count
    );
    assert_eq!(
        compact_view.header().key_count,
        legacy_view.header().key_count
    );
    assert_eq!(
        compact_view.header().posting_count,
        legacy_view.header().posting_count
    );

    for ord in 0..compact_view.header().entry_count {
        assert_eq!(
            compact_view.entry(ord).expect("compact entry"),
            legacy_view.entry(ord).expect("legacy entry"),
            "entry ordinal {ord} mismatch between compact and legacy"
        );
    }

    assert!(
        compact.bytes.len() * 2 < legacy.bytes.len(),
        "expected compact core bytes ({}) < 50% of legacy bytes ({})",
        compact.bytes.len(),
        legacy.bytes.len()
    );
}

fn synthetic_provenance(
    suffix: &str,
    actor_id: Option<&str>,
    method: Option<&str>,
) -> build_lexicon::CompiledProvenanceOut {
    build_lexicon::CompiledProvenanceOut {
        assertion_id: format!("ast_{suffix}"),
        revision_sha256: "a".repeat(64),
        source_id: "src_test".to_owned(),
        locator: "row=1".to_owned(),
        acceptance: build_lexicon::CompiledAcceptanceOut {
            decision_id: format!("dec_{suffix}"),
            kind: if actor_id.is_some() {
                "accepted_human".to_owned()
            } else {
                "accepted_auto_source".to_owned()
            },
            actor_id: actor_id.map(str::to_owned),
            method: method.map(str::to_owned),
            decided_on: "2026-04-01".to_owned(),
        },
    }
}

fn synthetic_meta_base(
    entry_revisions: BTreeMap<String, String>,
    entry_count: u32,
    sense_count: u32,
) -> build_lexicon::CompiledPackMetaOut {
    build_lexicon::CompiledPackMetaOut {
        pack_id: "core".to_owned(),
        dataset_version: "0.1.0+synthetic".to_owned(),
        description: "synthetic round-trip & scaling pack".to_owned(),
        schema_version: SCHEMA_VERSION,
        vocabulary_version: "1".to_owned(),
        index_format_version: INDEX_FORMAT_VERSION,
        manifest_sha256: "b".repeat(64),
        entry_count,
        sense_count,
        form_count: entry_count,
        text_count: sense_count,
        relation_count: 0,
        assertion_count: entry_count,
        omitted_relation_count: 0,
        coverage: build_lexicon::CompiledCoverageOut {
            language_ids: vec!["tam".to_owned(), "eng".to_owned()],
            region_codes: vec!["IN-TN".to_owned()],
            register_codes: vec!["formal".to_owned()],
            unknown_region_entries: 0,
        },
        entry_revisions,
        vocabularies: build_lexicon::CompiledVocabulariesOut {
            vocabulary_version: "1".to_owned(),
            language_ids: vec!["tam".to_owned(), "eng".to_owned()],
            parts_of_speech: vec!["NOUN".to_owned()],
            relation_codes: vec!["synonym".to_owned()],
            annotation_properties: vec![
                "prop_none".to_owned(),
                "prop_null".to_owned(),
                "prop_false".to_owned(),
                "prop_true".to_owned(),
                "prop_str".to_owned(),
                "prop_num".to_owned(),
                "prop_arr".to_owned(),
                "prop_obj".to_owned(),
            ],
            registers: vec!["formal".to_owned()],
            domains: vec![],
            temporals: vec![],
            varieties: vec![],
            regions: vec![build_lexicon::CompiledVocabRegionOut {
                code: "IN-TN".to_owned(),
                parent_code: None,
            }],
        },
        labels: vec![],
        sources: vec![],
    }
}

#[test]
fn compact_interned_preserves_all_field_variants_and_relations_losslessly() {
    let prov_human = vec![synthetic_provenance(
        "h",
        Some("editor_1"),
        Some("manual_v1"),
    )];
    let prov_auto = vec![synthetic_provenance("a", None, Some("auto_v1"))];

    let entries = vec![
        build_lexicon::CompiledEntryOut {
            entry_id: "ent_0001".to_owned(),
            revision: "c".repeat(64),
            headword: NANRI.to_owned(),
            language_id: "tam".to_owned(),
            part_of_speech: build_lexicon::CompiledLabelFieldOut {
                availability: "available".to_owned(),
                value: Some("NOUN".to_owned()),
                convention: Some("conv_pos".to_owned()),
                provenance: prov_human.clone(),
            },
            forms: vec![build_lexicon::CompiledFormOut {
                form_id: "frm_0001".to_owned(),
                representation: "written".to_owned(),
                role: "canonical".to_owned(),
                text: NANRI.to_owned(),
                convention: Some("ortho_v1".to_owned()),
                provenance: prov_human.clone(),
            }],
            senses: vec![build_lexicon::CompiledSenseOut {
                sense_id: "sen_0001".to_owned(),
                display_order: 1,
                parent_sense_id: None,
                components: vec![build_lexicon::CompiledTextOut {
                    text_id: "txt_0001".to_owned(),
                    kind: "definition".to_owned(),
                    language_id: "eng".to_owned(),
                    text: "gratitude".to_owned(),
                    provenance: prov_auto.clone(),
                }],
                examples: vec![build_lexicon::CompiledTextOut {
                    text_id: "txt_0002".to_owned(),
                    kind: "example".to_owned(),
                    language_id: "tam".to_owned(),
                    text: NANRI.to_owned(),
                    provenance: prov_human.clone(),
                }],
                relations: vec![build_lexicon::CompiledRelationOut {
                    relation_id: "rel_0001".to_owned(),
                    code: "synonym".to_owned(),
                    directionality: "symmetric".to_owned(),
                    source: build_lexicon::CompiledEndpointOut {
                        kind: "sense".to_owned(),
                        id: "sen_0001".to_owned(),
                    },
                    target: build_lexicon::CompiledEndpointOut {
                        kind: "entry".to_owned(),
                        id: "ent_0002".to_owned(),
                    },
                    provenance: prov_human.clone(),
                }],
                region: build_lexicon::CompiledScopeOut {
                    state: "attested".to_owned(),
                    codes: vec!["IN-TN".to_owned()],
                    provenance: prov_human.clone(),
                },
                register: build_lexicon::CompiledLabelFieldOut {
                    availability: "available".to_owned(),
                    value: Some("formal".to_owned()),
                    convention: None,
                    provenance: prov_auto.clone(),
                },
                annotations: vec![
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_none".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "unknown".to_owned(),
                            value: None,
                            convention: None,
                            provenance: vec![],
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_null".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "not_applicable".to_owned(),
                            value: Some(Value::Null),
                            convention: None,
                            provenance: vec![],
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_false".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(Value::Bool(false)),
                            convention: None,
                            provenance: prov_auto.clone(),
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_true".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(Value::Bool(true)),
                            convention: Some("conv_bool".to_owned()),
                            provenance: prov_human.clone(),
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_str".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(json!(NANRI)),
                            convention: None,
                            provenance: prov_human.clone(),
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_num".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(json!(42)),
                            convention: None,
                            provenance: prov_auto.clone(),
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_arr".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(json!(["a", 1, true, null])),
                            convention: None,
                            provenance: prov_auto.clone(),
                        },
                    },
                    build_lexicon::CompiledAnnotationOut {
                        property: "prop_obj".to_owned(),
                        field: build_lexicon::CompiledFieldOut {
                            availability: "available".to_owned(),
                            value: Some(json!({"head": NANRI, "weight": 2})),
                            convention: None,
                            provenance: prov_human.clone(),
                        },
                    },
                ],
                provenance: prov_human.clone(),
            }],
            region: build_lexicon::CompiledScopeOut {
                state: "attested".to_owned(),
                codes: vec!["IN-TN".to_owned()],
                provenance: prov_human.clone(),
            },
            register: build_lexicon::CompiledLabelFieldOut {
                availability: "available".to_owned(),
                value: Some("formal".to_owned()),
                convention: None,
                provenance: prov_human.clone(),
            },
            annotations: vec![],
            provenance: prov_human.clone(),
        },
        build_lexicon::CompiledEntryOut {
            entry_id: "ent_0002".to_owned(),
            revision: "d".repeat(64),
            headword: "\u{0bb5}\u{0ba3}\u{0b95}\u{0bcd}\u{0b95}\u{0bae}\u{0bcd}".to_owned(),
            language_id: "tam".to_owned(),
            part_of_speech: build_lexicon::CompiledLabelFieldOut {
                availability: "available".to_owned(),
                value: Some("NOUN".to_owned()),
                convention: None,
                provenance: prov_auto.clone(),
            },
            forms: vec![build_lexicon::CompiledFormOut {
                form_id: "frm_0002".to_owned(),
                representation: "written".to_owned(),
                role: "canonical".to_owned(),
                text: "\u{0bb5}\u{0ba3}\u{0b95}\u{0bcd}\u{0b95}\u{0bae}\u{0bcd}".to_owned(),
                convention: None,
                provenance: prov_auto.clone(),
            }],
            senses: vec![build_lexicon::CompiledSenseOut {
                sense_id: "sen_0002".to_owned(),
                display_order: 2,
                parent_sense_id: Some("sen_0001".to_owned()),
                components: vec![build_lexicon::CompiledTextOut {
                    text_id: "txt_0003".to_owned(),
                    kind: "gloss".to_owned(),
                    language_id: "eng".to_owned(),
                    text: "greeting".to_owned(),
                    provenance: prov_auto.clone(),
                }],
                examples: vec![],
                relations: vec![],
                region: build_lexicon::CompiledScopeOut {
                    state: "unknown".to_owned(),
                    codes: vec![],
                    provenance: vec![],
                },
                register: build_lexicon::CompiledLabelFieldOut {
                    availability: "unknown".to_owned(),
                    value: None,
                    convention: None,
                    provenance: vec![],
                },
                annotations: vec![],
                provenance: prov_auto.clone(),
            }],
            region: build_lexicon::CompiledScopeOut {
                state: "unknown".to_owned(),
                codes: vec![],
                provenance: vec![],
            },
            register: build_lexicon::CompiledLabelFieldOut {
                availability: "unknown".to_owned(),
                value: None,
                convention: None,
                provenance: vec![],
            },
            annotations: vec![],
            provenance: prov_auto,
        },
    ];

    let mut revs = BTreeMap::new();
    revs.insert("ent_0001".to_owned(), "c".repeat(64));
    revs.insert("ent_0002".to_owned(), "d".repeat(64));
    let meta = synthetic_meta_base(revs, 2, 2);

    let legacy_bytes =
        build_lexicon::build_tlpack_binary_with_flags(&meta, &entries, 0).expect("legacy build");
    let compact_bytes = build_lexicon::build_tlpack_binary(&meta, &entries).expect("compact build");

    let legacy_view = CompiledPackView::parse(&legacy_bytes).expect("parse legacy");
    let compact_view = CompiledPackView::parse(&compact_bytes).expect("parse compact");

    for ord in 0..2 {
        assert_eq!(
            compact_view.entry(ord).expect("compact entry"),
            legacy_view.entry(ord).expect("legacy entry")
        );
    }
}

#[test]
fn compact_interned_rejects_malformed_pool_indices_and_out_of_order_entries() {
    let (_tmp, dir, schemas) = clone_core_pack_to_temp("compact-malformed");
    let compiled = build_lexicon::compile_pack_dir(&dir, Some(&schemas), Some("core"))
        .expect("compile compact pack");
    let valid = compiled.bytes;
    let payload_off = usize::try_from(read_u64_le(&valid, 96).unwrap()).unwrap();
    let payload_len = usize::try_from(read_u64_le(&valid, 104).unwrap()).unwrap();
    let entry_index_off = usize::try_from(read_u64_le(&valid, 80).unwrap()).unwrap();

    // (1) Corrupted checksum fails
    {
        let mut bad_sum = valid.clone();
        bad_sum[payload_off + 20] ^= 0x01;
        assert!(CompiledPackView::parse(&bad_sum).is_err());
    }

    // (2) Bad pool magic (with valid checksum) fails
    {
        let mut bad_magic = valid.clone();
        bad_magic[payload_off + 7] = b'X';
        recompute_tlpack_checksum(&mut bad_magic);
        assert!(CompiledPackView::parse(&bad_magic).is_err());
    }

    // (3) Truncated / mismatched entries_base (with valid checksum) fails
    {
        let mut bad_base = valid.clone();
        let orig_base = read_u64_le(&bad_base, payload_off + 8).unwrap();
        bad_base[payload_off + 8..payload_off + 16].copy_from_slice(&(orig_base - 1).to_le_bytes());
        recompute_tlpack_checksum(&mut bad_base);
        assert!(CompiledPackView::parse(&bad_base).is_err());
    }

    // (4) Out-of-bounds entries_base > payload_len (with valid checksum) fails
    {
        let mut huge_base = valid.clone();
        huge_base[payload_off + 8..payload_off + 16]
            .copy_from_slice(&(payload_len as u64 + 1).to_le_bytes());
        recompute_tlpack_checksum(&mut huge_base);
        assert!(CompiledPackView::parse(&huge_base).is_err());
    }

    // (5) Out-of-order entry_id (swap entry 0 and entry 1 entry_index slices, with valid checksum) fails
    {
        let mut swapped = valid.clone();
        let slice0 = swapped[entry_index_off..entry_index_off + 16].to_vec();
        let slice1 = swapped[entry_index_off + 16..entry_index_off + 32].to_vec();
        swapped[entry_index_off..entry_index_off + 16].copy_from_slice(&slice1);
        swapped[entry_index_off + 16..entry_index_off + 32].copy_from_slice(&slice0);
        recompute_tlpack_checksum(&mut swapped);
        assert!(CompiledPackView::parse(&swapped).is_err());
    }

    // (6) Invalid string/provenance index inside entry record (with valid checksum) fails decode
    {
        let mut bad_entry_idx = valid.clone();
        let entry0_rel_off =
            usize::try_from(read_u64_le(&bad_entry_idx, entry_index_off).unwrap()).unwrap();
        // `entry_id` of entry 0 is always interned first (index 0, 1-byte varint), so bytes 1..6 start `revision`.
        // Encoding u32::MAX as a 5-byte varint guarantees an out-of-bounds string pool lookup regardless of pool size.
        bad_entry_idx[payload_off + entry0_rel_off + 1..payload_off + entry0_rel_off + 6]
            .copy_from_slice(&[0xFF, 0xFF, 0xFF, 0xFF, 0x0F]);
        recompute_tlpack_checksum(&mut bad_entry_idx);
        let view =
            CompiledPackView::parse(&bad_entry_idx).expect("parse checks only leading entry_id");
        assert!(view.entry(0).is_err());
    }
}

#[test]
fn compact_interned_scales_to_2000_entries_under_1mb_and_caches_metadata() {
    const ENTRY_COUNT: usize = 2_000;
    const SENSE_COUNT: usize = 5_000;

    let shared_prov = vec![
        synthetic_provenance("shared_1", Some("editor_ta"), Some("curation_v1")),
        synthetic_provenance("shared_2", None, Some("import_v1")),
    ];
    let shared_region = build_lexicon::CompiledScopeOut {
        state: "attested".to_owned(),
        codes: vec!["IN-TN".to_owned()],
        provenance: vec![shared_prov[0].clone()],
    };
    let shared_register = build_lexicon::CompiledLabelFieldOut {
        availability: "available".to_owned(),
        value: Some("formal".to_owned()),
        convention: None,
        provenance: vec![shared_prov[1].clone()],
    };

    let mut entries = Vec::with_capacity(ENTRY_COUNT);
    let mut entry_revisions = BTreeMap::new();
    let mut sense_seq = 0usize;
    let shared_rev = "e".repeat(64);

    for i in 0..ENTRY_COUNT {
        let entry_id = format!("ent_{i:06}");
        entry_revisions.insert(entry_id.clone(), shared_rev.clone());
        let headword = format!("{NANRI}_{i}");
        let senses_for_entry = if i % 2 == 0 { 3 } else { 2 }; // 1000*3 + 1000*2 = 5000 senses
        let mut senses = Vec::with_capacity(senses_for_entry);
        for s_idx in 0..senses_for_entry {
            let sid = format!("sen_{sense_seq:06}");
            let tid = format!("txt_{sense_seq:06}");
            sense_seq += 1;
            senses.push(build_lexicon::CompiledSenseOut {
                sense_id: sid,
                display_order: (s_idx + 1) as u32,
                parent_sense_id: None,
                components: vec![build_lexicon::CompiledTextOut {
                    text_id: tid,
                    kind: "definition".to_owned(),
                    language_id: "eng".to_owned(),
                    text: format!("meaning {i}.{s_idx}"),
                    provenance: vec![shared_prov[s_idx % 2].clone()],
                }],
                examples: vec![],
                relations: vec![],
                region: shared_region.clone(),
                register: shared_register.clone(),
                annotations: vec![],
                provenance: shared_prov.clone(),
            });
        }
        entries.push(build_lexicon::CompiledEntryOut {
            entry_id,
            revision: shared_rev.clone(),
            headword: headword.clone(),
            language_id: "tam".to_owned(),
            part_of_speech: build_lexicon::CompiledLabelFieldOut {
                availability: "available".to_owned(),
                value: Some("NOUN".to_owned()),
                convention: None,
                provenance: vec![shared_prov[0].clone()],
            },
            forms: vec![build_lexicon::CompiledFormOut {
                form_id: format!("frm_{i:06}"),
                representation: "written".to_owned(),
                role: "canonical".to_owned(),
                text: headword,
                convention: None,
                provenance: vec![shared_prov[0].clone()],
            }],
            senses,
            region: shared_region.clone(),
            register: shared_register.clone(),
            annotations: vec![],
            provenance: shared_prov.clone(),
        });
    }
    assert_eq!(sense_seq, SENSE_COUNT);

    let meta = synthetic_meta_base(entry_revisions, ENTRY_COUNT as u32, SENSE_COUNT as u32);
    let bytes = build_lexicon::build_tlpack_binary(&meta, &entries)
        .expect("build 2000-entry compact tlpack");
    assert!(
        bytes.len() < 1_000_000,
        "2000-entry / 5000-sense compact pack must be < 1 MB, got {} bytes",
        bytes.len()
    );

    let view = CompiledPackView::parse(&bytes).expect("parse 2000-entry compact pack");
    let meta_ptr_1 = view.metadata_ref().expect("cached meta 1") as *const _;
    let meta_ptr_2 = view.metadata_ref().expect("cached meta 2") as *const _;
    assert!(
        std::ptr::eq(meta_ptr_1, meta_ptr_2),
        "metadata_ref must return the cached CompiledPackMeta pointer without re-parsing"
    );

    let target_query = format!("{NANRI}_1234");
    let req = tamil_toolkit::lexicon::LookupRequest {
        input: target_query.clone(),
        packs: Some(vec!["core".to_owned()]),
        region: Some("IN-TN".to_owned()),
        register: Some("formal".to_owned()),
    };
    let resp = tamil_toolkit::lexicon::lookup_in_views(&req, &[("core", &view)])
        .expect("lookup in 2000-entry pack");
    assert_eq!(resp.status, tamil_toolkit::lexicon::LookupStatus::Matched);
    assert_eq!(resp.canonical_query, target_query);
    assert_eq!(resp.entries.len(), 1);
    assert_eq!(resp.entries[0].entry_id, "ent_001234");
    assert_eq!(resp.entries[0].senses.len(), 3);
}
