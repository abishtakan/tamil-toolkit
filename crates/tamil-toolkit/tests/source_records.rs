//! Golden, runtime validation, proptest, and synthetic exporter tests for `tamil_toolkit::source_records`.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use proptest::prelude::*;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use tamil_toolkit::execute;
use tamil_toolkit::source_records::{
    bucket_for_normalized, execute_bucket, execute_lookup, DATA_STATUS,
    ERR_INVALID_BUCKET_OR_OPTIONS, ERR_INVALID_QUERY, MAX_QUERY_BYTES, RIGHTS_STATUS,
};

const GOLDEN_SOURCE_RECORDS_JSONL: &str =
    include_str!("../../../tests/golden/lexicon_source_records.jsonl");

static TEMP_COUNTER: AtomicU64 = AtomicU64::new(0);

struct TempDirGuard {
    path: PathBuf,
}

impl TempDirGuard {
    fn new(prefix: &str) -> Self {
        let id = TEMP_COUNTER.fetch_add(1, Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!(
            "tamil_toolkit_sr_{prefix}_{}_{}",
            std::process::id(),
            id
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

fn sha256_hex(bytes: &[u8]) -> String {
    let digest = Sha256::digest(bytes);
    let mut out = String::with_capacity(64);
    for b in digest {
        out.push_str(&format!("{b:02x}"));
    }
    out
}

fn make_record(
    source_file: &str,
    source_row: u64,
    lookup_key: &str,
    fields: BTreeMap<&str, &str>,
) -> Value {
    let fields_map: serde_json::Map<String, Value> = fields
        .into_iter()
        .map(|(k, v)| (k.to_owned(), Value::String(v.to_owned())))
        .collect();
    json!({
        "source_file": source_file,
        "source_row": source_row,
        "lookup_key": lookup_key,
        "fields": fields_map,
    })
}

fn make_bucket(bucket_id: &str, records: Vec<Value>) -> Value {
    json!({
        "schema_version": 1,
        "bucket": bucket_id,
        "records": records,
    })
}

#[test]
fn golden_source_records_vectors() {
    let lines: Vec<&str> = GOLDEN_SOURCE_RECORDS_JSONL
        .lines()
        .filter(|line| !line.trim().is_empty())
        .collect();
    assert_eq!(lines.len(), 5);

    for line in lines {
        let case: Value = serde_json::from_str(line).expect("parse golden JSONL row");
        let id = case["id"].as_str().expect("id");
        let req = json!({
            "op": case["op"],
            "input": case["input"],
        });
        let result = execute(&req);
        if let Some(expected) = case.get("expected") {
            let actual = result.unwrap_or_else(|err| panic!("{id}: unexpected error: {err}"));
            assert_eq!(&actual, expected, "{id}: response mismatch");
        } else if let Some(expected_err) = case.get("expected_error").and_then(Value::as_str) {
            let actual_err = result.expect_err(&format!("{id}: expected error"));
            assert_eq!(actual_err, expected_err, "{id}: error mismatch");
        } else {
            panic!("{id}: missing expected or expected_error");
        }
    }
}

#[test]
fn nfd_whitespace_case_and_joiners_preserved() {
    let nfc = "\u{0B95}\u{0BCA}\u{0BB2}\u{0BCD}";
    let nfd = tamil_norm::normalize_nfd(nfc);
    assert_ne!(nfc, nfd);

    let bucket_nfc = execute_bucket(&json!(nfc)).expect("bucket nfc");
    let bucket_nfd = execute_bucket(&json!(nfd)).expect("bucket nfd");
    assert_eq!(bucket_nfc["bucket"], bucket_nfd["bucket"]);
    assert_eq!(bucket_nfd["query"], nfd);
    assert_eq!(bucket_nfd["normalized_query"], nfc);

    let bucket_id = bucket_nfc["bucket"].as_str().expect("bucket str");
    let zwj = char::from_u32(0x200D).expect("zwj");
    let with_zwj = format!("{nfc}{zwj}");
    let with_spaces = format!(" {nfc} ");

    let bucket_zwj = execute_bucket(&json!(with_zwj)).expect("bucket zwj");
    assert_eq!(bucket_zwj["query"], with_zwj);
    assert_eq!(bucket_zwj["normalized_query"], with_zwj);

    let bucket_ws = execute_bucket(&json!(with_spaces)).expect("bucket ws");
    assert_eq!(bucket_ws["query"], with_spaces);
    assert_eq!(bucket_ws["normalized_query"], with_spaces);

    // NFD query matches NFC bucket record and preserves original query string.
    let rec = make_record(
        "primary_lemmas.csv",
        4,
        nfc,
        BTreeMap::from([("headword_ta", nfd.as_str()), ("note", "")]),
    );
    let lookup_res = execute_lookup(&json!({
        "query": nfd,
        "bucket": make_bucket(bucket_id, vec![rec.clone()]),
        "offset": 0,
        "limit": 10,
    }))
    .expect("nfd lookup");
    assert_eq!(lookup_res["query"], nfd);
    assert_eq!(lookup_res["normalized_query"], nfc);
    assert_eq!(lookup_res["status"], "matched");
    assert_eq!(lookup_res["total"], 1);
    assert_eq!(lookup_res["records"], json!([rec]));

    // Case-folding is never applied.
    let upper = "Homo";
    let lower = "homo";
    let upper_bucket = bucket_for_normalized(upper);
    let lower_bucket = bucket_for_normalized(lower);
    assert_ne!(upper_bucket, lower_bucket);
    let absent = execute_lookup(&json!({
        "query": upper,
        "bucket": make_bucket(&upper_bucket, vec![]),
        "offset": 0,
        "limit": 10,
    }))
    .expect("absent lookup");
    assert_eq!(absent["status"], "not_found");
    assert_eq!(absent["data_status"], DATA_STATUS);
    assert_eq!(absent["rights_status"], RIGHTS_STATUS);
    assert_eq!(absent["total"], 0);
    assert_eq!(absent["records"], json!([]));
}

#[test]
fn pagination_sorting_and_duplicate_preservation() {
    let key = "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}";
    let other_key = "other";
    let target_bucket = bucket_for_normalized(key);

    // Construct records in unsorted order, including duplicate content with distinct rows.
    let r3 = make_record(
        "primary_meanings.csv",
        10,
        key,
        BTreeMap::from([("headword_ta", key), ("meaning_en", "Tamil")]),
    );
    let r2 = make_record(
        "primary_lemmas.csv",
        2,
        key,
        BTreeMap::from([("headword_ta", key), ("word_id", "1")]),
    );
    let r1 = make_record(
        "primary_lemmas.csv",
        1,
        key,
        BTreeMap::from([("headword_ta", key), ("word_id", "1")]),
    );

    let mut records = vec![r3.clone(), r2.clone(), r1.clone()];
    // Only add another key if it happens to collide into the same bucket; either way tested below.
    if bucket_for_normalized(other_key) == target_bucket {
        records.push(make_record(
            "primary_lemmas.csv",
            99,
            other_key,
            BTreeMap::from([("headword_ta", other_key)]),
        ));
    }

    let page1 = execute_lookup(&json!({
        "query": key,
        "bucket": make_bucket(&target_bucket, records.clone()),
        "offset": 1,
        "limit": 2,
    }))
    .expect("page1");
    assert_eq!(page1["status"], "matched");
    assert_eq!(page1["total"], 3);
    assert_eq!(page1["offset"], 1);
    assert_eq!(page1["limit"], 2);
    assert_eq!(page1["records"], json!([r2, r3]));

    let page0 = execute_lookup(&json!({
        "query": key,
        "bucket": make_bucket(&target_bucket, records.clone()),
        "offset": 0,
        "limit": 1,
    }))
    .expect("page0");
    assert_eq!(page0["records"], json!([r1]));

    let past_end = execute_lookup(&json!({
        "query": key,
        "bucket": make_bucket(&target_bucket, records),
        "offset": 3,
        "limit": 25,
    }))
    .expect("past_end");
    assert_eq!(past_end["status"], "matched");
    assert_eq!(past_end["total"], 3);
    assert_eq!(past_end["records"], json!([]));
}

#[test]
fn rejects_malformed_queries_options_buckets_and_records() {
    // Query validation on lexicon_source_bucket.
    for bad in [json!(null), json!(42), json!({}), json!([]), json!("")] {
        assert_eq!(execute_bucket(&bad).unwrap_err(), ERR_INVALID_QUERY);
    }
    let too_long = "a".repeat(MAX_QUERY_BYTES + 1);
    assert_eq!(
        execute_bucket(&json!(too_long)).unwrap_err(),
        ERR_INVALID_QUERY
    );
    let max_ok = "a".repeat(MAX_QUERY_BYTES);
    assert!(execute_bucket(&json!(max_ok)).is_ok());

    let key = "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}";
    let bucket_id = bucket_for_normalized(key);
    let valid_rec = make_record(
        "primary_lemmas.csv",
        1,
        key,
        BTreeMap::from([("headword_ta", key)]),
    );

    // Invalid query inside lookup takes precedence over invalid bucket content.
    assert_eq!(
        execute_lookup(&json!({
            "query": "",
            "bucket": make_bucket("zz", vec![]),
            "offset": 0,
            "limit": 10,
        }))
        .unwrap_err(),
        ERR_INVALID_QUERY
    );

    // Wrong top-level shape.
    for bad_req in [
        json!(null),
        json!({"query": key, "bucket": make_bucket(&bucket_id, vec![]), "offset": 0}),
        json!({"query": key, "bucket": make_bucket(&bucket_id, vec![]), "offset": 0, "limit": 10, "extra": 1}),
    ] {
        assert_eq!(
            execute_lookup(&bad_req).unwrap_err(),
            ERR_INVALID_BUCKET_OR_OPTIONS
        );
    }

    // Invalid pagination bounds / types.
    for (offset, limit) in [
        (json!(-1), json!(10)),
        (json!(1_000_001), json!(10)),
        (json!(1.5), json!(10)),
        (json!("0"), json!(10)),
        (json!(0), json!(0)),
        (json!(0), json!(101)),
        (json!(0), json!(-5)),
        (json!(0), json!(1.5)),
    ] {
        assert_eq!(
            execute_lookup(&json!({
                "query": key,
                "bucket": make_bucket(&bucket_id, vec![]),
                "offset": offset,
                "limit": limit,
            }))
            .unwrap_err(),
            ERR_INVALID_BUCKET_OR_OPTIONS
        );
    }

    // Wrong bucket schema_version / bucket mismatch / bad hex.
    let other_bucket = if bucket_id == "00" { "01" } else { "00" };
    for bad_bucket in [
        json!({"schema_version": 2, "bucket": bucket_id, "records": []}),
        json!({"schema_version": 1, "bucket": "AF", "records": []}),
        json!({"schema_version": 1, "bucket": "zz", "records": []}),
        json!({"schema_version": 1, "bucket": other_bucket, "records": []}),
        json!({"schema_version": 1, "bucket": bucket_id, "records": [], "extra": true}),
    ] {
        assert_eq!(
            execute_lookup(&json!({
                "query": key,
                "bucket": bad_bucket,
                "offset": 0,
                "limit": 10,
            }))
            .unwrap_err(),
            ERR_INVALID_BUCKET_OR_OPTIONS
        );
    }

    // Duplicate (source_file, source_row) locator.
    assert_eq!(
        execute_lookup(&json!({
            "query": key,
            "bucket": make_bucket(&bucket_id, vec![valid_rec.clone(), valid_rec]),
            "offset": 0,
            "limit": 10,
        }))
        .unwrap_err(),
        ERR_INVALID_BUCKET_OR_OPTIONS
    );

    // Unsafe source_file, non-positive source_row, non-NFC lookup_key, wrong-bucket record, non-string field.
    let nfd_key = tamil_norm::normalize_nfd("\u{0B95}\u{0BCA}\u{0BB2}\u{0BCD}");
    assert_ne!(tamil_norm::normalize_nfc(&nfd_key), nfd_key);
    let wrong_key = "different_key_for_wrong_bucket";
    let bad_records = [
        make_record("../evil.csv", 1, key, BTreeMap::from([("a", "b")])),
        make_record("dir/a.csv", 1, key, BTreeMap::from([("a", "b")])),
        make_record("a\\b.csv", 1, key, BTreeMap::from([("a", "b")])),
        make_record("not_csv.txt", 1, key, BTreeMap::from([("a", "b")])),
        make_record(".csv", 1, key, BTreeMap::from([("a", "b")])),
        make_record("primary_lemmas.csv", 0, key, BTreeMap::from([("a", "b")])),
        make_record("primary_lemmas.csv", 1, "", BTreeMap::from([("a", "b")])),
        make_record(
            "primary_lemmas.csv",
            1,
            &nfd_key,
            BTreeMap::from([("a", "b")]),
        ),
        make_record(
            "primary_lemmas.csv",
            1,
            wrong_key,
            BTreeMap::from([("a", "b")]),
        ),
        json!({
            "source_file": "primary_lemmas.csv",
            "source_row": 1,
            "lookup_key": key,
            "fields": {"a": 123},
        }),
        json!({
            "source_file": "primary_lemmas.csv",
            "source_row": 1,
            "lookup_key": key,
            "fields": {},
            "extra": "nope",
        }),
    ];
    for bad_rec in bad_records {
        assert_eq!(
            execute_lookup(&json!({
                "query": key,
                "bucket": make_bucket(&bucket_id, vec![bad_rec]),
                "offset": 0,
                "limit": 10,
            }))
            .unwrap_err(),
            ERR_INVALID_BUCKET_OR_OPTIONS
        );
    }
}

fn write_synthetic_bundle(source_dir: &Path, manifest_path: &Path) {
    let nfc = "\u{0B95}\u{0BCA}\u{0BB2}\u{0BCD}";
    let nfd = tamil_norm::normalize_nfd(nfc);
    let zwj = char::from_u32(0x200D).expect("zwj");
    let zwj_term = format!("\u{0B85}{zwj}\u{0B83}");

    // 11 CSV files + 1 FST file = 12 frozen files.
    let files: Vec<(&str, String)> = vec![
        (
            "primary_lemmas.csv",
            format!(
                "word_id,headword_ta,notes\n\
                 1,{nfd},\"line1\nline2\"\n\
                 2, spaced ,dup\n\
                 3, spaced ,dup\n"
            ),
        ),
        ("primary_lexicon.fst", "SYNTHETIC_FST_BYTES".to_owned()),
        (
            "primary_meanings.csv",
            format!("meaning_id,headword_ta,meaning_en\n10,{nfc},kill\n"),
        ),
        (
            "primary_relationships.csv",
            format!("relationship_id,source_headword_ta,target_headword_ta\n1,{nfc},target\n"),
        ),
        (
            "secondary_archaic_literary_terms.csv",
            "archaic_id,term_ta\n1,archaic_term\n".to_owned(),
        ),
        (
            "secondary_dialect_colloquialisms.csv",
            "colloquial_id,term_ta\n1,dialect_term\n".to_owned(),
        ),
        (
            "secondary_phrases_mwes.csv",
            "phrase_id,phrase_ta\n1,phrase_term\n".to_owned(),
        ),
        (
            "secondary_proper_names_toponyms.csv",
            "proper_id,name_ta\n1,Jaffna\n".to_owned(),
        ),
        (
            "secondary_scientific_taxa.csv",
            "taxa_id,scientific_name,tamil_name\n\
             1,Oryza sativa,\n\
             2,,\n"
                .to_owned(),
        ),
        (
            "secondary_specialized_technical_terms.csv",
            format!("term_id,term_ta,empty_col\n1,{zwj_term},\n"),
        ),
        (
            "secondary_transliterations_loanwords.csv",
            "loanword_id,transliterated_ta\n1,loan_term\n".to_owned(),
        ),
        (
            "unified_master_30col.csv",
            format!("word_id,headword_ta\n1,{nfc}\n"),
        ),
    ];

    let mut manifest_entries = Vec::new();
    for (name, content) in &files {
        let bytes = content.as_bytes();
        fs::write(source_dir.join(name), bytes).expect("write synthetic source");
        manifest_entries.push(json!({
            "file": name,
            "bytes": bytes.len(),
            "sha256": sha256_hex(bytes),
        }));
    }
    fs::write(
        manifest_path,
        serde_json::to_string_pretty(&manifest_entries).expect("serialize pin"),
    )
    .expect("write synthetic pin");
}

#[test]
fn exporter_synthetic_bundle_determinism_fallbacks_and_roundtrip() {
    let root = TempDirGuard::new("exporter_ok");
    let source_dir = root.path().join("source");
    let manifest_path = root.path().join("pin.json");
    let out_a = root.path().join("out_a");
    let out_b = root.path().join("out_b");
    fs::create_dir_all(&source_dir).expect("mkdir source");
    write_synthetic_bundle(&source_dir, &manifest_path);

    let bin = env!("CARGO_BIN_EXE_source-records");
    for out in [&out_a, &out_b] {
        let output = Command::new(bin)
            .args([&source_dir, &manifest_path, out])
            .output()
            .expect("run source-records");
        assert!(
            output.status.success(),
            "exporter failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }

    // Byte-for-byte deterministic across all 256 buckets, NOTICE.md, and manifest.json.
    for i in 0..=255u8 {
        let fname = format!("{i:02x}.json");
        assert_eq!(
            fs::read(out_a.join(&fname)).expect("read out_a bucket"),
            fs::read(out_b.join(&fname)).expect("read out_b bucket"),
            "non-deterministic bucket {fname}"
        );
    }
    assert_eq!(
        fs::read(out_a.join("NOTICE.md")).expect("notice a"),
        fs::read(out_b.join("NOTICE.md")).expect("notice b"),
    );
    assert_eq!(
        fs::read(out_a.join("manifest.json")).expect("manifest a"),
        fs::read(out_b.join("manifest.json")).expect("manifest b"),
    );

    let manifest: Value =
        serde_json::from_slice(&fs::read(out_a.join("manifest.json")).expect("read manifest"))
            .expect("parse manifest");
    assert_eq!(manifest["schema_version"], 1);
    assert_eq!(manifest["data_status"], DATA_STATUS);
    assert_eq!(manifest["rights_status"], RIGHTS_STATUS);
    assert_eq!(
        manifest["owner_direction"],
        "Explicit user request 2026-11-16; no third-party rights grant asserted"
    );
    // 3 + 1 + 1 + 1 + 1 + 1 + 1 + 2 + 1 + 1 + 1 = 14 rows across 11 CSVs.
    assert_eq!(manifest["total_records"], 14);
    assert_eq!(manifest["files"].as_array().expect("files").len(), 11);
    assert_eq!(manifest["buckets"].as_object().expect("buckets").len(), 256);

    let notice = fs::read_to_string(out_a.join("NOTICE.md")).expect("read NOTICE.md");
    assert!(notice.contains(DATA_STATUS));
    assert!(notice.contains(RIGHTS_STATUS));
    assert!(
        notice.contains("Explicit user request 2026-11-16; no third-party rights grant asserted")
    );

    // Verify all 256 bucket checksums and sizes, and test round-trip lookup for key features.
    let mut observed_total = 0u64;
    let mut distinct_keys = BTreeSet::new();
    for (bucket_id, meta) in manifest["buckets"].as_object().expect("buckets obj") {
        let fname = meta["file"].as_str().expect("bucket file");
        assert_eq!(fname, format!("{bucket_id}.json"));
        let raw = fs::read(out_a.join(fname)).expect("read bucket");
        assert_eq!(raw.len() as u64, meta["bytes"].as_u64().expect("bytes"));
        assert_eq!(sha256_hex(&raw), meta["sha256"].as_str().expect("sha256"));
        let parsed: Value = serde_json::from_slice(&raw).expect("parse bucket");
        let recs = parsed["records"].as_array().expect("records");
        assert_eq!(recs.len() as u64, meta["records"].as_u64().expect("count"));
        observed_total += recs.len() as u64;
        for rec in recs {
            distinct_keys.insert(rec["lookup_key"].as_str().expect("lookup_key").to_owned());
        }
    }
    assert_eq!(observed_total, 14);
    assert_eq!(
        distinct_keys.len() as u64,
        manifest["distinct_keys"].as_u64().expect("distinct_keys")
    );

    // Check fallback keys, NFD cell preservation, multiline row numbering, and duplicate rows.
    for (query, expected_total, expected_first_file, expected_first_row) in [
        (
            "\u{0B95}\u{0BCA}\u{0BB2}\u{0BCD}",
            4u64,
            "primary_lemmas.csv",
            1u64,
        ),
        (" spaced ", 2u64, "primary_lemmas.csv", 2u64),
        ("Oryza sativa", 1u64, "secondary_scientific_taxa.csv", 1u64),
        (
            "secondary_scientific_taxa.csv:2",
            1u64,
            "secondary_scientific_taxa.csv",
            2u64,
        ),
    ] {
        let bucket_res = execute_bucket(&json!(query)).expect("bucket");
        let b_id = bucket_res["bucket"].as_str().expect("b_id");
        let bucket_json: Value = serde_json::from_slice(
            &fs::read(out_a.join(format!("{b_id}.json"))).expect("read bucket"),
        )
        .expect("parse bucket");
        let lookup_res = execute_lookup(&json!({
            "query": query,
            "bucket": bucket_json,
            "offset": 0,
            "limit": 25,
        }))
        .expect("roundtrip lookup");
        assert_eq!(lookup_res["status"], "matched");
        assert_eq!(lookup_res["total"], expected_total);
        assert_eq!(lookup_res["records"][0]["source_file"], expected_first_file);
        assert_eq!(lookup_res["records"][0]["source_row"], expected_first_row);
    }

    // Verify NFD cell and multiline cell were preserved verbatim in primary_lemmas.csv:1.
    let nfc = "\u{0B95}\u{0BCA}\u{0BB2}\u{0BCD}";
    let nfd = tamil_norm::normalize_nfd(nfc);
    let b_id = bucket_for_normalized(nfc);
    let bucket_json: Value =
        serde_json::from_slice(&fs::read(out_a.join(format!("{b_id}.json"))).expect("read bucket"))
            .expect("parse bucket");
    let res = execute_lookup(&json!({
        "query": nfc,
        "bucket": bucket_json,
        "offset": 0,
        "limit": 10,
    }))
    .expect("lookup");
    assert_eq!(res["records"][0]["fields"]["headword_ta"], nfd);
    assert_eq!(res["records"][0]["fields"]["notes"], "line1\nline2");
}

#[test]
fn exporter_rejects_existing_output_bad_checksums_extra_csv_and_malformed_csv() {
    let bin = env!("CARGO_BIN_EXE_source-records");

    // 1. Existing output directory fails without touching contents.
    {
        let root = TempDirGuard::new("exp_exists");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("existing");
        fs::create_dir_all(&source_dir).unwrap();
        fs::create_dir_all(&out).unwrap();
        fs::write(out.join("keep.txt"), b"keep").unwrap();
        write_synthetic_bundle(&source_dir, &pin);

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert_eq!(fs::read(out.join("keep.txt")).unwrap(), b"keep");
    }

    // 2. Corrupted FST checksum fails before creating output directory.
    {
        let root = TempDirGuard::new("exp_bad_fst");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("out");
        fs::create_dir_all(&source_dir).unwrap();
        write_synthetic_bundle(&source_dir, &pin);
        fs::write(
            source_dir.join("primary_lexicon.fst"),
            b"TAMPERED_FST_BYTES",
        )
        .unwrap();

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert!(!out.exists());
    }

    // 3. Extra CSV file in source directory fails before creating output directory.
    {
        let root = TempDirGuard::new("exp_extra_csv");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("out");
        fs::create_dir_all(&source_dir).unwrap();
        write_synthetic_bundle(&source_dir, &pin);
        fs::write(source_dir.join("extra_unexpected.csv"), b"a,b\n1,2\n").unwrap();

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert!(!out.exists());
    }

    // 4. Unsafe path in frozen manifest fails before creating output directory.
    {
        let root = TempDirGuard::new("exp_unsafe_path");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("out");
        fs::create_dir_all(&source_dir).unwrap();
        write_synthetic_bundle(&source_dir, &pin);
        let mut entries: Value = serde_json::from_str(&fs::read_to_string(&pin).unwrap()).unwrap();
        entries[0]["file"] = json!("../primary_lemmas.csv");
        fs::write(&pin, serde_json::to_string(&entries).unwrap()).unwrap();

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert!(!out.exists());
    }

    // 5. Duplicate CSV header leaves no usable manifest.
    {
        let root = TempDirGuard::new("exp_dup_header");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("out");
        fs::create_dir_all(&source_dir).unwrap();
        write_synthetic_bundle(&source_dir, &pin);

        let bad_csv = b"word_id,headword_ta,word_id\n1,test,2\n";
        fs::write(source_dir.join("primary_lemmas.csv"), bad_csv).unwrap();
        let mut entries: Value = serde_json::from_str(&fs::read_to_string(&pin).unwrap()).unwrap();
        for item in entries.as_array_mut().unwrap() {
            if item["file"] == "primary_lemmas.csv" {
                item["bytes"] = json!(bad_csv.len());
                item["sha256"] = json!(sha256_hex(bad_csv));
            }
        }
        fs::write(&pin, serde_json::to_string(&entries).unwrap()).unwrap();

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert!(!out.join("manifest.json").exists());
    }

    // 6. Wrong CSV row width leaves no usable manifest.
    {
        let root = TempDirGuard::new("exp_bad_width");
        let source_dir = root.path().join("source");
        let pin = root.path().join("pin.json");
        let out = root.path().join("out");
        fs::create_dir_all(&source_dir).unwrap();
        write_synthetic_bundle(&source_dir, &pin);

        let bad_csv = b"word_id,headword_ta\n1,test,extra_col\n";
        fs::write(source_dir.join("primary_lemmas.csv"), bad_csv).unwrap();
        let mut entries: Value = serde_json::from_str(&fs::read_to_string(&pin).unwrap()).unwrap();
        for item in entries.as_array_mut().unwrap() {
            if item["file"] == "primary_lemmas.csv" {
                item["bytes"] = json!(bad_csv.len());
                item["sha256"] = json!(sha256_hex(bad_csv));
            }
        }
        fs::write(&pin, serde_json::to_string(&entries).unwrap()).unwrap();

        let status = Command::new(bin)
            .args([&source_dir, &pin, &out])
            .status()
            .unwrap();
        assert!(!status.success());
        assert!(!out.join("manifest.json").exists());
    }
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(10_000))]

    #[test]
    fn prop_bucket_and_empty_lookup_invariants(query in ".{1,200}") {
        prop_assume!(!query.is_empty() && query.len() <= MAX_QUERY_BYTES);
        let res = execute_bucket(&json!(query)).expect("valid non-empty query");
        prop_assert_eq!(res["query"].as_str(), Some(query.as_str()));

        let normalized = res["normalized_query"].as_str().expect("normalized_query");
        let expected_nfc = tamil_norm::normalize_nfc(&query);
        prop_assert_eq!(normalized, expected_nfc.as_str());

        let bucket_id = res["bucket"].as_str().expect("bucket");
        prop_assert_eq!(bucket_id.len(), 2);
        prop_assert!(bucket_id.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f')));

        // NFD form routes to the same bucket as NFC form.
        let nfd = tamil_norm::normalize_nfd(&query);
        if !nfd.is_empty() && nfd.len() <= MAX_QUERY_BYTES {
            let nfd_res = execute_bucket(&json!(nfd)).expect("nfd bucket");
            prop_assert_eq!(nfd_res["bucket"].as_str(), Some(bucket_id));
            prop_assert_eq!(nfd_res["normalized_query"].as_str(), Some(normalized));
        }

        // Lookup against an empty validated bucket succeeds with not_found.
        let lookup = execute_lookup(&json!({
            "query": query,
            "bucket": make_bucket(bucket_id, vec![]),
            "offset": 0,
            "limit": 25,
        })).expect("empty bucket lookup");
        prop_assert_eq!(lookup["status"].as_str(), Some("not_found"));
        prop_assert_eq!(lookup["data_status"].as_str(), Some(DATA_STATUS));
        prop_assert_eq!(lookup["rights_status"].as_str(), Some(RIGHTS_STATUS));
        prop_assert_eq!(lookup["total"].as_u64(), Some(0));
    }
}
