//! Integration tests for `tamil-lexicon` v0.2 runtime dispatcher operations (`TMLPACK2`).
#![forbid(unsafe_code)]

use std::sync::Mutex;

use serde_json::{json, Value};
use tamil_toolkit::execute;
use tamil_toolkit::lexicon::{
    build_compact_pack, clear_runtime_packs, load_pack_bytes, CompactEntry, CompactForm,
    CompactPackInput, CompactRelation, CompactSense, PackTier,
};

const GOLDEN_V02_JSONL: &str = include_str!("../../../tests/golden/lexicon_v02_runtime.jsonl");

static REGISTRY_TEST_LOCK: Mutex<()> = Mutex::new(());

#[test]
fn golden_lexicon_v02_runtime_vectors_pass() {
    let _guard = REGISTRY_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    clear_runtime_packs().expect("clear runtime packs");
    for (idx, line) in GOLDEN_V02_JSONL.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let row: Value = serde_json::from_str(line)
            .unwrap_or_else(|e| panic!("line {} parse error: {e}", idx + 1));
        let id = row["id"].as_str().unwrap();
        let req = json!({
            "op": row["op"],
            "input": row["input"],
        });
        let result = execute(&req);
        if let Some(expected_err) = row.get("expected_error").and_then(Value::as_str) {
            let err = result.expect_err(&format!("{id}: expected error"));
            assert_eq!(err, expected_err, "{id}: error mismatch");
        } else {
            let actual = result.unwrap_or_else(|e| panic!("{id}: unexpected error: {e}"));
            assert_eq!(actual, row["expected"], "{id}: response mismatch");
        }
    }
}

#[test]
fn dispatcher_roundtrips_loaded_tmlpack2_open_and_local_packs() {
    let _guard = REGISTRY_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    clear_runtime_packs().expect("clear runtime packs");

    let open_bytes = build_compact_pack(&CompactPackInput {
        pack_id: "test_open".to_owned(),
        pack_tier: PackTier::VerifiedOpen,
        rights_status: "CC-BY-SA-4.0".to_owned(),
        license: "CC-BY-SA-4.0".to_owned(),
        dataset_version: "0.2.0".to_owned(),
        description: "Open test pack".to_owned(),
        source_ids: vec!["enwiktionary".to_owned()],
        attribution_notice: "CC-BY-SA-4.0".to_owned(),
        entries: vec![CompactEntry {
            entry_id: "o_1".to_owned(),
            headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}".to_owned(),
            pos: Some("NOUN".to_owned()),
            forms: vec![],
            senses: vec![CompactSense {
                gloss_en: Some("Tamil".to_owned()),
                ..Default::default()
            }],
            domain: Some("linguistics".to_owned()),
            region: None,
            register: None,
            origin_language: None,
            pure_tamil_equivalent: None,
            standard_equivalent: None,
            scientific_name: None,
            literary_source: None,
            source_id: "enwiktionary".to_owned(),
            source_locator: "enwiktionary:1".to_owned(),
            rights_status: "CC-BY-SA-4.0".to_owned(),
            ..Default::default()
        }],
        relations: vec![],
        build_folded_index: true,
    })
    .expect("build open pack");

    let local_bytes = build_compact_pack(&CompactPackInput {
        pack_id: "test_local".to_owned(),
        pack_tier: PackTier::LocalHistorical,
        rights_status: "unresolved".to_owned(),
        license: "UNRESOLVED_LOCAL_ONLY".to_owned(),
        dataset_version: "0.2.0".to_owned(),
        description: "Local test pack".to_owned(),
        source_ids: vec!["TVA_KALAICHOL".to_owned()],
        attribution_notice: "Local only".to_owned(),
        entries: vec![CompactEntry {
            entry_id: "l_1".to_owned(),
            headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD} \u{0BA8}\u{0BBE}\u{0B9F}\u{0BC1}"
                .to_owned(),
            pos: None,
            forms: vec![CompactForm {
                role: "variant".to_owned(),
                text: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}\u{0BA8}\u{0BBE}\u{0B9F}\u{0BC1}"
                    .to_owned(),
            }],
            senses: vec![CompactSense {
                gloss_en: Some("Tamil Nadu".to_owned()),
                domain: Some("Geography".to_owned()),
                ..Default::default()
            }],
            domain: Some("Geography".to_owned()),
            region: Some("TN".to_owned()),
            register: None,
            origin_language: None,
            pure_tamil_equivalent: None,
            standard_equivalent: None,
            scientific_name: None,
            literary_source: None,
            source_id: "TVA_KALAICHOL".to_owned(),
            source_locator: "test.csv:1".to_owned(),
            rights_status: "unresolved".to_owned(),
            ..Default::default()
        }],
        relations: vec![CompactRelation {
            source_headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}".to_owned(),
            target_headword:
                "\u{0B9A}\u{0BC6}\u{0BA8}\u{0BCD}\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
                    .to_owned(),
            relation_code: "SYNONYM".to_owned(),
            directionality: "symmetric".to_owned(),
            source_id: "primary_relationships.csv".to_owned(),
            source_locator: "primary_relationships.csv:1".to_owned(),
        }],
        build_folded_index: true,
    })
    .expect("build local pack");

    let s1 = load_pack_bytes(open_bytes).expect("load open");
    let s2 = load_pack_bytes(local_bytes).expect("load local");
    assert_eq!(s1.pack_id, "test_open");
    assert_eq!(s2.pack_id, "test_local");

    let stats = execute(&json!({ "op": "lexicon_stats", "input": null })).expect("stats");
    assert_eq!(stats["pack_count"], 2);
    assert_eq!(stats["total_entries"], 2);
    assert_eq!(stats["total_relations"], 1);

    // Folded open-only query
    let folded_open = execute(&json!({
        "op": "lexicon_query",
        "input": "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB2}\u{0BCD}",
        "folded": true,
        "tier": "open"
    }))
    .expect("folded query");
    assert_eq!(folded_open["status"], "matched");
    assert_eq!(folded_open["total_entries"], 1);
    assert_eq!(folded_open["entries"][0]["pack_id"], "test_open");

    // Prefix search across both packs
    let search = execute(&json!({
        "op": "lexicon_search",
        "input": "\u{0BA4}\u{0BAE}\u{0BBF}",
        "limit": 10
    }))
    .expect("search");
    assert_eq!(search["hits"].as_array().unwrap().len(), 2);

    // Relations query
    let rels = execute(&json!({
        "op": "lexicon_relations",
        "input": "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    }))
    .expect("relations");
    assert_eq!(rels["status"], "matched");
    assert_eq!(rels["relations"][0]["relation_code"], "SYNONYM");

    // Unified define query merges open entry + local relation
    let def = execute(&json!({
        "op": "lexicon_define",
        "input": "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    }))
    .expect("define");
    assert_eq!(def["status"], "matched");
    assert_eq!(def["headword"], "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}");
    assert_eq!(def["has_verified_open"], true);
    assert_eq!(def["meanings_en"][0]["text"], "Tamil");
    assert_eq!(
        def["relations"]["synonyms"][0],
        "\u{0B9A}\u{0BC6}\u{0BA8}\u{0BCD}\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    );

    // Category filter on query/search
    let cat_miss = execute(&json!({
        "op": "lexicon_query",
        "input": "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}",
        "category": "terminology"
    }))
    .expect("category filter");
    assert_eq!(cat_miss["status"], "not_found");

    // Verify facet counts in lexicon_stats
    assert_eq!(stats["has_english_index"], true);
    assert_eq!(stats["category_counts"]["dictionary"], 2);
    assert_eq!(stats["pos_counts"]["NOUN"], 1);
    assert_eq!(stats["domain_counts"]["linguistics"], 1);
    assert_eq!(stats["domain_counts"]["Geography"], 1);
    assert_eq!(stats["region_counts"]["TN"], 1);

    // Reverse English gloss search via execute & lexicon_search_english helper
    let en_hit = execute(&json!({
        "op": "lexicon_search_english",
        "input": {
            "query": "Tamil",
            "category": "dictionary",
            "limit": 5
        }
    }))
    .expect("lexicon_search_english");
    assert_eq!(en_hit["hits"].as_array().unwrap().len(), 2);
    assert_eq!(
        en_hit["hits"][0]["headword"],
        "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    );

    let en_direct = tamil_toolkit::lexicon_search_english(&json!({
        "query": "Tamil Nadu",
        "domain": "Geography",
        "region": "TN",
        "limit": 5
    }))
    .expect("direct lexicon_search_english");
    assert_eq!(en_direct["hits"].as_array().unwrap().len(), 1);
    assert_eq!(
        en_direct["hits"][0]["headword"],
        "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD} \u{0BA8}\u{0BBE}\u{0B9F}\u{0BC1}"
    );

    // Cleanup
    clear_runtime_packs().expect("clear");
}

#[test]
fn english_search_ranking_and_atomic_facets_and_cli_pack_commands() {
    let _guard = REGISTRY_TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    clear_runtime_packs().expect("clear");

    let open_bytes = build_compact_pack(&CompactPackInput {
        pack_id: "core".to_owned(),
        pack_tier: PackTier::VerifiedOpen,
        rights_status: "CC-BY-SA-4.0".to_owned(),
        license: "CC-BY-SA-4.0".to_owned(),
        dataset_version: "0.2.0".to_owned(),
        description: "Open water test".to_owned(),
        source_ids: vec!["enwiktionary".to_owned()],
        attribution_notice: "CC-BY-SA-4.0".to_owned(),
        entries: vec![
            CompactEntry {
                entry_id: "w1".to_owned(),
                headword: "\u{0BA8}\u{0BC0}\u{0BB0}\u{0BCD}".to_owned(),
                pos: Some("NOUN".to_owned()),
                domain: Some("Nature, Chemistry".to_owned()),
                region: Some("TN; SL-JAFFNA".to_owned()),
                register: Some("standard; literary".to_owned()),
                senses: vec![CompactSense {
                    gloss_en: Some("water".to_owned()),
                    definition_en: Some("liquid H2O".to_owned()),
                    ..Default::default()
                }],
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:1".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            },
            CompactEntry {
                entry_id: "w2".to_owned(),
                headword: "\u{0B85}\u{0BB0}\u{0BC1}\u{0BB5}\u{0BBF}".to_owned(),
                pos: Some("NOUN".to_owned()),
                domain: Some("Geography".to_owned()),
                senses: vec![CompactSense {
                    gloss_en: Some("waterfall".to_owned()),
                    definition_en: Some("cascade of falling water".to_owned()),
                    ..Default::default()
                }],
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:2".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            },
            CompactEntry {
                entry_id: "w3".to_owned(),
                headword: "\u{0B95}\u{0B9F}\u{0BB2}\u{0BCD}".to_owned(),
                pos: Some("NOUN".to_owned()),
                domain: Some("Geography".to_owned()),
                senses: vec![CompactSense {
                    gloss_en: Some("sea".to_owned()),
                    definition_en: Some("large body of salt water".to_owned()),
                    ..Default::default()
                }],
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:3".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            },
        ],
        relations: vec![],
        build_folded_index: true,
    })
    .expect("build core");

    let summary = load_pack_bytes(open_bytes.clone()).expect("load core");
    assert!(summary.has_english_index);

    let stats = execute(&json!({ "op": "lexicon_stats", "input": null })).expect("stats");
    assert_eq!(stats["domain_counts"]["Nature"], 1);
    assert_eq!(stats["domain_counts"]["Chemistry"], 1);
    assert_eq!(stats["domain_counts"]["Geography"], 2);
    assert_eq!(stats["register_counts"]["standard"], 1);
    assert_eq!(stats["register_counts"]["literary"], 1);
    assert_eq!(stats["region_counts"]["SL-JAFFNA"], 1);

    // Exact gloss ("water") ranks above prefix gloss ("waterfall") and definition-only ("sea")
    let ranked = execute(&json!({
        "op": "lexicon_search_english",
        "input": "water",
        "limit": 10
    }))
    .expect("search water");
    let hits = ranked["hits"].as_array().unwrap();
    assert_eq!(hits.len(), 3);
    assert_eq!(hits[0]["headword"], "\u{0BA8}\u{0BC0}\u{0BB0}\u{0BCD}");
    assert_eq!(
        hits[1]["headword"],
        "\u{0B85}\u{0BB0}\u{0BC1}\u{0BB5}\u{0BBF}"
    );
    assert_eq!(hits[2]["headword"], "\u{0B95}\u{0B9F}\u{0BB2}\u{0BCD}");

    // Atomic domain & register filters match individual tokens inside comma/semicolon strings
    let chem = execute(&json!({
        "op": "lexicon_search_english",
        "input": "water",
        "domain": "chemistry",
        "register": "literary",
        "region": "SL-JAFFNA"
    }))
    .expect("filtered search");
    assert_eq!(chem["hits"].as_array().unwrap().len(), 1);
    assert_eq!(
        chem["hits"][0]["headword"],
        "\u{0BA8}\u{0BC0}\u{0BB0}\u{0BCD}"
    );

    clear_runtime_packs().expect("clear");

    // Verify CLI status, verify, search-en, and remove on a temporary directory
    let temp_dir =
        std::env::temp_dir().join(format!("tamil_lexicon_cli_test_{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&temp_dir);
    std::fs::create_dir_all(temp_dir.join("open")).expect("mkdir");
    std::fs::write(temp_dir.join("open/core.tlpack"), &open_bytes).expect("write tlpack");
    let manifest = json!({
        "schema_version": 2,
        "pack_count": 1,
        "packs": [{
            "file": "open/core.tlpack",
            "summary": summary,
        }]
    });
    std::fs::write(
        temp_dir.join("MANIFEST.json"),
        serde_json::to_string_pretty(&manifest).unwrap(),
    )
    .expect("write manifest");

    let bin = env!("CARGO_BIN_EXE_tamil-toolkit");
    let dir_str = temp_dir.to_string_lossy().to_string();

    let status_out = std::process::Command::new(bin)
        .args(["lexicon", "status", "--dir", &dir_str, "--json"])
        .output()
        .expect("run status");
    assert!(status_out.status.success(), "status failed");
    let status_json: Value = serde_json::from_slice(&status_out.stdout).expect("parse status json");
    assert_eq!(status_json["has_english_index"], true);
    assert_eq!(status_json["pack_count"], 1);

    let verify_out = std::process::Command::new(bin)
        .args(["lexicon", "verify", "--dir", &dir_str])
        .output()
        .expect("run verify");
    assert!(
        verify_out.status.success(),
        "verify failed: {}",
        String::from_utf8_lossy(&verify_out.stderr)
    );

    let search_out = std::process::Command::new(bin)
        .args([
            "lexicon",
            "search-en",
            "water",
            "--pack-dir",
            &dir_str,
            "--json",
        ])
        .output()
        .expect("run search-en");
    assert!(search_out.status.success(), "search-en failed");
    let search_json: Value =
        serde_json::from_slice(&search_out.stdout).expect("parse search-en json");
    assert_eq!(search_json["hits"].as_array().unwrap().len(), 3);

    let remove_out = std::process::Command::new(bin)
        .args(["lexicon", "remove", "core", "--dir", &dir_str])
        .output()
        .expect("run remove");
    assert!(remove_out.status.success(), "remove failed");
    assert!(!temp_dir.join("open/core.tlpack").exists());

    let _ = std::fs::remove_dir_all(&temp_dir);
}
