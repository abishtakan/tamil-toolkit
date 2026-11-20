//! Golden contract, schema, profile, CLI, and synthetic lookup tests for `tamil_toolkit::lexicon`.

#[path = "support/lexicon_unicode.rs"]
mod lexicon_unicode;

use std::collections::{BTreeMap, BTreeSet};
use std::process::Command;

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
#[cfg(all(
    feature = "lexicon-core",
    not(feature = "lexicon-terminology"),
    not(feature = "lexicon-names-taxa"),
    not(feature = "lexicon-regional")
))]
use tamil_toolkit::lexicon::lookup;
#[cfg(all(
    feature = "lexicon-core",
    not(feature = "lexicon-terminology"),
    not(feature = "lexicon-names-taxa"),
    not(feature = "lexicon-regional")
))]
use tamil_toolkit::lexicon::PackInfo;
use tamil_toolkit::lexicon::{
    lookup_in_views, packs, Acceptance, Annotation, CompiledPackMeta, Coverage, Endpoint, Entry,
    Field, Form, LabelField, LookupRequest, LookupStatus, Provenance, Relation, Scope, Sense, Text,
    MAX_INPUT_BYTES, SCHEMA_VERSION,
};
use tamil_toolkit::lexicon_pack::{
    encode_entry_slice_le, encode_posting_range_le, CompiledLabel, CompiledPackView,
    CompiledSourceNotice, CompiledVocabRegion, CompiledVocabularies, EntrySlice, PostingRange,
    CHECKSUM_OFFSET, HEADER_SIZE, INDEX_FORMAT_VERSION, PACK_MAGIC,
};
use tamil_toolkit::{execute, OPERATIONS};

#[cfg(all(
    feature = "lexicon-core",
    not(feature = "lexicon-terminology"),
    not(feature = "lexicon-names-taxa"),
    not(feature = "lexicon-regional")
))]
const GOLDEN_LEXICON_JSONL: &str = include_str!("../../../tests/golden/lexicon_lookup.jsonl");

const LOOKUP_RESPONSE_SCHEMA_JSON: &str =
    include_str!("../../../specs/021-lexicon-curation/contracts/lookup-response.schema.json");

fn is_valid_id(s: &str) -> bool {
    let mut chars = s.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    first.is_ascii_alphabetic()
        && chars.all(|c| c.is_ascii_alphanumeric() || matches!(c, '_' | '.' | ':' | '-'))
}

fn is_valid_sha256(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| matches!(b, b'0'..=b'9' | b'a'..=b'f'))
}

fn is_iso_date(s: &str) -> bool {
    let b = s.as_bytes();
    if b.len() != 10
        || !b[0..4].iter().all(u8::is_ascii_digit)
        || b[4] != b'-'
        || !b[5..7].iter().all(u8::is_ascii_digit)
        || b[7] != b'-'
        || !b[8..10].iter().all(u8::is_ascii_digit)
    {
        return false;
    }
    let year: u32 = s[0..4].parse().unwrap_or(0);
    let month: u32 = s[5..7].parse().unwrap_or(0);
    let day: u32 = s[8..10].parse().unwrap_or(0);
    if !(1..=12).contains(&month) || day < 1 {
        return false;
    }
    let leap = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
    let max_day = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => return false,
    };
    day <= max_day
}

fn matches_json_type(val: &Value, expected_type: &str) -> bool {
    match expected_type {
        "null" => val.is_null(),
        "boolean" => val.is_boolean(),
        "string" => val.is_string(),
        "array" => val.is_array(),
        "object" => val.is_object(),
        "number" => val.is_number(),
        "integer" => {
            val.is_i64()
                || val.is_u64()
                || val
                    .as_f64()
                    .is_some_and(|f| f.is_finite() && f.fract() == 0.0)
        }
        other => panic!("unhandled JSON schema type keyword: {other}"),
    }
}

fn check_schema_node(val: &Value, schema: &Value, root: &Value, path: &str) -> Result<(), String> {
    let obj = schema
        .as_object()
        .ok_or_else(|| format!("{path}: schema node must be an object"))?;

    for key in obj.keys() {
        assert!(
            matches!(
                key.as_str(),
                "$defs"
                    | "$id"
                    | "$schema"
                    | "$ref"
                    | "title"
                    | "type"
                    | "const"
                    | "enum"
                    | "minLength"
                    | "pattern"
                    | "format"
                    | "minimum"
                    | "minItems"
                    | "maxItems"
                    | "items"
                    | "uniqueItems"
                    | "properties"
                    | "required"
                    | "additionalProperties"
                    | "anyOf"
                    | "allOf"
                    | "if"
                    | "then"
                    | "else"
            ),
            "unhandled keyword `{key}` in lookup-response.schema.json"
        );
    }

    if let Some(ref_str) = obj.get("$ref").and_then(Value::as_str) {
        let def_name = ref_str
            .strip_prefix("#/$defs/")
            .unwrap_or_else(|| panic!("unsupported $ref `{ref_str}`"));
        let target = root["$defs"]
            .get(def_name)
            .unwrap_or_else(|| panic!("missing $defs/{def_name}"));
        check_schema_node(val, target, root, path)?;
    }

    if let Some(type_val) = obj.get("type") {
        let ok = match type_val {
            Value::String(t) => matches_json_type(val, t),
            Value::Array(arr) => arr
                .iter()
                .filter_map(Value::as_str)
                .any(|t| matches_json_type(val, t)),
            _ => panic!("invalid `type` in schema"),
        };
        if !ok {
            return Err(format!("{path}: expected type {type_val}, got {val}"));
        }
    }

    if let Some(expected_const) = obj.get("const") {
        if val != expected_const {
            return Err(format!(
                "{path}: expected const {expected_const}, got {val}"
            ));
        }
    }

    if let Some(enum_arr) = obj.get("enum").and_then(Value::as_array) {
        if !enum_arr.contains(val) {
            return Err(format!("{path}: value {val} not in enum {enum_arr:?}"));
        }
    }

    if let Some(s) = val.as_str() {
        if let Some(min_len) = obj.get("minLength").and_then(Value::as_u64) {
            if (s.chars().count() as u64) < min_len {
                return Err(format!("{path}: string length < minLength {min_len}"));
            }
        }
        if let Some(pat) = obj.get("pattern").and_then(Value::as_str) {
            let matched = match pat {
                "^[A-Za-z][A-Za-z0-9_.:-]*$" => is_valid_id(s),
                "^[0-9a-f]{64}$" => is_valid_sha256(s),
                other => panic!("unhandled regex pattern `{other}` in lookup-response.schema.json"),
            };
            if !matched {
                return Err(format!("{path}: string {s:?} failed pattern {pat}"));
            }
        }
        if let Some(fmt) = obj.get("format").and_then(Value::as_str) {
            match fmt {
                "date" => {
                    if !is_iso_date(s) {
                        return Err(format!("{path}: string {s:?} failed format date"));
                    }
                }
                other => panic!("unhandled format `{other}` in lookup-response.schema.json"),
            }
        }
    }

    if let Some(min_num) = obj.get("minimum").and_then(Value::as_f64) {
        if let Some(actual_num) = val.as_f64() {
            if actual_num < min_num {
                return Err(format!("{path}: number {actual_num} < minimum {min_num}"));
            }
        }
    }

    if let Some(arr) = val.as_array() {
        if let Some(min_items) = obj.get("minItems").and_then(Value::as_u64) {
            if (arr.len() as u64) < min_items {
                return Err(format!(
                    "{path}: array len {} < minItems {min_items}",
                    arr.len()
                ));
            }
        }
        if let Some(max_items) = obj.get("maxItems").and_then(Value::as_u64) {
            if (arr.len() as u64) > max_items {
                return Err(format!(
                    "{path}: array len {} > maxItems {max_items}",
                    arr.len()
                ));
            }
        }
        if obj.get("uniqueItems").and_then(Value::as_bool) == Some(true) {
            for i in 0..arr.len() {
                for j in (i + 1)..arr.len() {
                    if arr[i] == arr[j] {
                        return Err(format!("{path}: duplicate item {} in array", arr[i]));
                    }
                }
            }
        }
        if let Some(item_schema) = obj.get("items") {
            for (idx, item) in arr.iter().enumerate() {
                check_schema_node(item, item_schema, root, &format!("{path}[{idx}]"))?;
            }
        }
    }

    if let Some(map) = val.as_object() {
        if let Some(req_arr) = obj.get("required").and_then(Value::as_array) {
            for key_val in req_arr {
                let req_key = key_val.as_str().expect("required key string");
                if !map.contains_key(req_key) {
                    return Err(format!("{path}: missing required key {req_key:?}"));
                }
            }
        }
        let props = obj.get("properties").and_then(Value::as_object);
        if let Some(props_map) = props {
            for (k, prop_schema) in props_map {
                if let Some(v) = map.get(k) {
                    check_schema_node(v, prop_schema, root, &format!("{path}.{k}"))?;
                }
            }
        }
        if obj.get("additionalProperties").and_then(Value::as_bool) == Some(false) {
            for k in map.keys() {
                if !props.is_some_and(|p| p.contains_key(k)) {
                    return Err(format!("{path}: unexpected additional property {k:?}"));
                }
            }
        }
    }

    if let Some(any_of) = obj.get("anyOf").and_then(Value::as_array) {
        let mut errs = Vec::new();
        let mut ok = false;
        for branch in any_of {
            match check_schema_node(val, branch, root, path) {
                Ok(()) => {
                    ok = true;
                    break;
                }
                Err(e) => errs.push(e),
            }
        }
        if !ok {
            return Err(format!("{path}: failed all anyOf branches: {errs:?}"));
        }
    }

    if let Some(all_of) = obj.get("allOf").and_then(Value::as_array) {
        for branch in all_of {
            check_schema_node(val, branch, root, path)?;
        }
    }

    if let Some(if_schema) = obj.get("if") {
        if check_schema_node(val, if_schema, root, path).is_ok() {
            if let Some(then_schema) = obj.get("then") {
                check_schema_node(val, then_schema, root, path)?;
            }
        } else if let Some(else_schema) = obj.get("else") {
            check_schema_node(val, else_schema, root, path)?;
        }
    }

    Ok(())
}

fn validate_lookup_response_schema(val: &Value) {
    let schema: Value = serde_json::from_str(LOOKUP_RESPONSE_SCHEMA_JSON)
        .expect("parse lookup-response.schema.json");
    if let Err(err) = check_schema_node(val, &schema, &schema, "LookupResponse") {
        panic!("closed schema validation failed: {err}");
    }

    // Contract invariants not expressible purely in JSON Schema: UTF-8 byte cap & strict sorting.
    let cq = val["canonical_query"].as_str().expect("canonical_query");
    assert!(cq.len() <= MAX_INPUT_BYTES);
    let mut prev_entry_id: Option<&str> = None;
    for (eidx, e) in val["entries"]
        .as_array()
        .expect("entries")
        .iter()
        .enumerate()
    {
        let entry_id = e["entry_id"].as_str().expect("entry_id");
        if let Some(prev) = prev_entry_id {
            assert!(prev < entry_id, "entries[{eidx}] out of entry_id order");
        }
        prev_entry_id = Some(entry_id);
        let mut prev_sense_key: Option<(u64, &str)> = None;
        for (sidx, s) in e["senses"].as_array().expect("senses").iter().enumerate() {
            let key = (
                s["display_order"].as_u64().expect("display_order"),
                s["sense_id"].as_str().expect("sense_id"),
            );
            if let Some(prev) = prev_sense_key {
                assert!(prev < key, "entries[{eidx}].senses[{sidx}] out of order");
            }
            prev_sense_key = Some(key);
        }
    }
}

fn build_synthetic_tlpack(meta: &CompiledPackMeta, entries: &[Entry]) -> Vec<u8> {
    assert!(!entries.is_empty(), "synthetic pack must have >= 1 entry");
    let mut sorted_entries = entries.to_vec();
    sorted_entries.sort_by(|a, b| a.entry_id.cmp(&b.entry_id));

    let mut postings_by_key: BTreeMap<String, Vec<u32>> = BTreeMap::new();
    let mut payload_bytes = Vec::new();
    let mut entry_index_bytes = Vec::with_capacity(sorted_entries.len() * 16);

    for (ord_usize, entry) in sorted_entries.iter().enumerate() {
        let ord = u32::try_from(ord_usize).expect("entry count fits u32");
        let nfc = tamil_norm::normalize_nfc(&entry.headword);
        postings_by_key.entry(nfc).or_default().push(ord);

        let off = u64::try_from(payload_bytes.len()).expect("payload offset");
        let encoded = serde_json::to_vec(entry).expect("serialize entry");
        let len = u64::try_from(encoded.len()).expect("entry len");
        payload_bytes.extend_from_slice(&encoded);
        entry_index_bytes
            .extend_from_slice(&encode_entry_slice_le(EntrySlice { offset: off, len }));
    }

    let mut fst_builder = fst::MapBuilder::memory();
    let mut ranges_bytes = Vec::with_capacity(postings_by_key.len() * 8);
    let mut postings_bytes = Vec::new();
    let mut cursor = 0u32;

    for (key_ord, (key, ords)) in postings_by_key.iter_mut().enumerate() {
        ords.sort_unstable();
        ords.dedup();
        let count = u32::try_from(ords.len()).expect("posting count");
        ranges_bytes.extend_from_slice(&encode_posting_range_le(PostingRange {
            start: cursor,
            count,
        }));
        cursor += count;
        for &o in ords.iter() {
            postings_bytes.extend_from_slice(&o.to_le_bytes());
        }
        fst_builder
            .insert(key.as_bytes(), u64::try_from(key_ord).expect("key_ord"))
            .expect("fst insert");
    }

    let fst_bytes = fst_builder.into_inner().expect("fst bytes");
    let metadata_bytes = serde_json::to_vec(meta).expect("meta bytes");

    let key_count = u32::try_from(postings_by_key.len()).expect("key_count");
    let entry_count = u32::try_from(sorted_entries.len()).expect("entry_count");
    let posting_count = cursor;

    let fst_offset = u64::try_from(HEADER_SIZE).expect("header");
    let fst_len = u64::try_from(fst_bytes.len()).expect("fst_len");
    let ranges_offset = fst_offset + fst_len;
    let ranges_len = u64::try_from(ranges_bytes.len()).expect("ranges_len");
    let postings_offset = ranges_offset + ranges_len;
    let postings_len = u64::try_from(postings_bytes.len()).expect("postings_len");
    let entry_index_offset = postings_offset + postings_len;
    let entry_index_len = u64::try_from(entry_index_bytes.len()).expect("entry_index_len");
    let payload_offset = entry_index_offset + entry_index_len;
    let payload_len = u64::try_from(payload_bytes.len()).expect("payload_len");
    let metadata_offset = payload_offset + payload_len;
    let metadata_len = u64::try_from(metadata_bytes.len()).expect("metadata_len");

    let mut out = Vec::new();
    out.extend_from_slice(&PACK_MAGIC);
    out.extend_from_slice(&meta.index_format_version.to_le_bytes());
    out.extend_from_slice(&meta.schema_version.to_le_bytes());
    out.extend_from_slice(&0u32.to_le_bytes());
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
    assert_eq!(out.len(), CHECKSUM_OFFSET);

    let mut body = Vec::new();
    body.extend_from_slice(&fst_bytes);
    body.extend_from_slice(&ranges_bytes);
    body.extend_from_slice(&postings_bytes);
    body.extend_from_slice(&entry_index_bytes);
    body.extend_from_slice(&payload_bytes);
    body.extend_from_slice(&metadata_bytes);

    let mut hasher = Sha256::new();
    hasher.update(&out);
    hasher.update(&body);
    let digest: [u8; 32] = hasher.finalize().into();

    out.extend_from_slice(&digest);
    assert_eq!(out.len(), HEADER_SIZE);
    out.extend_from_slice(&body);
    out
}

fn sample_provenance(id_suffix: &str, auto_source: bool) -> Provenance {
    Provenance {
        assertion_id: format!("ast_synth.{id_suffix}"),
        revision_sha256: "a".repeat(64),
        source_id: "src_synth.1".to_owned(),
        locator: "synthetic:1".to_owned(),
        acceptance: Acceptance {
            decision_id: format!("dec_synth.{id_suffix}"),
            kind: if auto_source {
                "accepted_auto_source".to_owned()
            } else {
                "accepted_human".to_owned()
            },
            actor_id: if auto_source {
                None
            } else {
                Some("abish".to_owned())
            },
            method: if auto_source {
                Some("auto-fixture:v1".to_owned())
            } else {
                Some("manual-fixture:v1".to_owned())
            },
            decided_on: "2026-11-14".to_owned(),
        },
    }
}

fn sample_sense(
    sense_id: &str,
    display_order: u32,
    gloss: &str,
    region: Scope,
    register: LabelField,
    relations: Vec<Relation>,
) -> Sense {
    Sense {
        sense_id: sense_id.to_owned(),
        display_order,
        parent_sense_id: None,
        components: vec![Text {
            text_id: format!("txt_{sense_id}"),
            kind: "gloss".to_owned(),
            language_id: "eng".to_owned(),
            text: gloss.to_owned(),
            provenance: vec![sample_provenance(sense_id, false)],
        }],
        examples: vec![],
        relations,
        region,
        register,
        annotations: vec![],
        provenance: vec![sample_provenance(sense_id, false)],
    }
}

fn scope_attested(codes: &[&str], suffix: &str) -> Scope {
    Scope {
        state: "attested".to_owned(),
        codes: codes.iter().map(|s| (*s).to_owned()).collect(),
        provenance: vec![sample_provenance(suffix, false)],
    }
}

fn scope_unrestricted(suffix: &str) -> Scope {
    Scope {
        state: "unrestricted".to_owned(),
        codes: vec![],
        provenance: vec![sample_provenance(suffix, false)],
    }
}

fn scope_unknown() -> Scope {
    Scope {
        state: "unknown".to_owned(),
        codes: vec![],
        provenance: vec![],
    }
}

fn register_available(val: &str, suffix: &str) -> LabelField {
    LabelField {
        availability: "available".to_owned(),
        value: Some(val.to_owned()),
        convention: None,
        provenance: vec![sample_provenance(suffix, false)],
    }
}

fn register_unrestricted(suffix: &str) -> LabelField {
    LabelField {
        availability: "available".to_owned(),
        value: Some("unrestricted".to_owned()),
        convention: None,
        provenance: vec![sample_provenance(suffix, false)],
    }
}

fn register_unknown() -> LabelField {
    LabelField {
        availability: "unknown".to_owned(),
        value: None,
        convention: None,
        provenance: vec![],
    }
}

fn sample_entry(
    entry_id: &str,
    revision: &str,
    headword: &str,
    region: Scope,
    register: LabelField,
    senses: Vec<Sense>,
    auto_source: bool,
) -> Entry {
    Entry {
        entry_id: entry_id.to_owned(),
        revision: revision.to_owned(),
        headword: headword.to_owned(),
        language_id: "tam".to_owned(),
        part_of_speech: LabelField {
            availability: "available".to_owned(),
            value: Some("NOUN".to_owned()),
            convention: None,
            provenance: vec![sample_provenance(entry_id, auto_source)],
        },
        forms: vec![Form {
            form_id: format!("frm_{entry_id}"),
            representation: "written".to_owned(),
            role: "canonical".to_owned(),
            text: tamil_norm::normalize_nfc(headword),
            convention: None,
            provenance: vec![sample_provenance(entry_id, auto_source)],
        }],
        senses,
        region,
        register,
        annotations: vec![],
        provenance: vec![sample_provenance(entry_id, auto_source)],
    }
}

fn sample_meta(
    pack_id: &str,
    entries: &[Entry],
    labels: Vec<CompiledLabel>,
    registers: Vec<&str>,
    dataset_version: &str,
    schema_version: u32,
) -> CompiledPackMeta {
    let mut entry_revisions = BTreeMap::new();
    let mut regions = BTreeSet::new();
    let mut regs = BTreeSet::new();
    let mut unknown_region_entries = 0u64;

    for e in entries {
        entry_revisions.insert(e.entry_id.clone(), e.revision.clone());
        if e.region.state == "unknown" {
            unknown_region_entries += 1;
        }
        for c in &e.region.codes {
            regions.insert(c.clone());
        }
        for s in &e.senses {
            for c in &s.region.codes {
                regions.insert(c.clone());
            }
            if let Some(v) = &s.register.value {
                if v != "unrestricted" {
                    regs.insert(v.clone());
                }
            }
        }
        if let Some(v) = &e.register.value {
            if v != "unrestricted" {
                regs.insert(v.clone());
            }
        }
    }

    CompiledPackMeta {
        pack_id: pack_id.to_owned(),
        dataset_version: dataset_version.to_owned(),
        description: format!("synthetic {pack_id}"),
        schema_version,
        vocabulary_version: "vocab-v1".to_owned(),
        index_format_version: INDEX_FORMAT_VERSION,
        manifest_sha256: "b".repeat(64),
        entry_count: u32::try_from(entries.len()).unwrap(),
        sense_count: u32::try_from(entries.iter().map(|e| e.senses.len()).sum::<usize>()).unwrap(),
        form_count: u32::try_from(entries.iter().map(|e| e.forms.len()).sum::<usize>()).unwrap(),
        text_count: 0,
        relation_count: 0,
        assertion_count: 0,
        omitted_relation_count: 0,
        coverage: Coverage {
            language_ids: vec!["tam".to_owned()],
            region_codes: regions.into_iter().collect(),
            register_codes: regs.into_iter().collect(),
            unknown_region_entries,
        },
        entry_revisions,
        vocabularies: CompiledVocabularies {
            vocabulary_version: "vocab-v1".to_owned(),
            language_ids: vec!["tam".to_owned()],
            parts_of_speech: vec!["NOUN".to_owned(), "INTJ".to_owned()],
            relation_codes: vec!["synonym".to_owned()],
            annotation_properties: vec![],
            registers: registers.into_iter().map(str::to_owned).collect(),
            domains: vec![],
            temporals: vec![],
            varieties: vec![],
            regions: vec![],
        },
        labels,
        sources: vec![CompiledSourceNotice {
            source_id: "src_synth.1".to_owned(),
            label: "Synthetic".to_owned(),
            url: None,
            reuse_basis: "test".to_owned(),
            attribution_text: "synthetic".to_owned(),
            attribution_reference: "synthetic".to_owned(),
        }],
    }
}

fn region_label(code: &str, parent_code: Option<&str>) -> CompiledLabel {
    CompiledLabel {
        registry_id: "iso-3166-test".to_owned(),
        registry_version: "1".to_owned(),
        code: code.to_owned(),
        category: "region".to_owned(),
        display_label: code.to_owned(),
        definition: code.to_owned(),
        evidence_reference: "synthetic".to_owned(),
        parent_code: parent_code.map(str::to_owned),
    }
}

#[test]
fn operations_register_lexicon_entrypoints() {
    assert!(OPERATIONS.contains(&"lexicon_lookup"));
    assert!(OPERATIONS.contains(&"lexicon_packs"));
}

#[test]
fn dispatcher_rejects_unknown_option_keys_and_bad_packs_requests() {
    let err = execute(&json!({
        "op": "lexicon_lookup",
        "input": "test",
        "foo": 1
    }))
    .unwrap_err();
    assert_eq!(err, "lexicon: invalid options");

    let err_packs_extra = execute(&json!({
        "op": "lexicon_packs",
        "input": null,
        "packs": ["core"]
    }))
    .unwrap_err();
    assert_eq!(err_packs_extra, "lexicon: invalid options");

    let err_packs_input = execute(&json!({
        "op": "lexicon_packs",
        "input": "core"
    }))
    .unwrap_err();
    assert_eq!(err_packs_input, "lexicon: invalid options");
}

#[cfg(all(
    feature = "lexicon-core",
    not(feature = "lexicon-terminology"),
    not(feature = "lexicon-names-taxa"),
    not(feature = "lexicon-regional")
))]
#[test]
fn golden_lexicon_lookup_consumes_all_44_planned_cases_unchanged() {
    let lines: Vec<&str> = GOLDEN_LEXICON_JSONL
        .lines()
        .filter(|line| !line.trim().is_empty())
        .collect();
    assert_eq!(lines.len(), 44, "expected all 44 planned golden vectors");

    for (idx, line) in lines.iter().enumerate() {
        let row: Value = serde_json::from_str(line)
            .unwrap_or_else(|err| panic!("line {}: invalid json: {err}", idx + 1));
        let id = row["id"].as_str().expect("row id");
        let op = row["op"].as_str().expect("row op");

        let mut req = serde_json::Map::new();
        req.insert("op".to_owned(), Value::String(op.to_owned()));
        req.insert("input".to_owned(), row["input"].clone());
        for key in ["packs", "region", "register"] {
            if let Some(v) = row.get(key) {
                req.insert(key.to_owned(), v.clone());
            }
        }
        let req_val = Value::Object(req);

        if let Some(expected_error) = row.get("expected_error").and_then(Value::as_str) {
            let actual_err = match execute(&req_val) {
                Ok(ok) => panic!("{id}: expected Err({expected_error:?}), got Ok({ok})"),
                Err(err) => err,
            };
            assert_eq!(actual_err, expected_error, "{id}: error mismatch");
        } else {
            let expected = row.get("expected").expect("expected payload");
            let actual =
                execute(&req_val).unwrap_or_else(|err| panic!("{id}: unexpected error: {err}"));
            assert_eq!(&actual, expected, "{id}: payload mismatch");

            if op == "lexicon_lookup" {
                validate_lookup_response_schema(&actual);

                // Verify typed Rust API parity on valid lookups.
                let packs_opt = row.get("packs").and_then(Value::as_array).map(|arr| {
                    arr.iter()
                        .map(|v| v.as_str().unwrap().to_owned())
                        .collect::<Vec<_>>()
                });
                let typed = lookup(&LookupRequest {
                    input: row["input"].as_str().unwrap().to_owned(),
                    packs: packs_opt,
                    region: row.get("region").and_then(Value::as_str).map(str::to_owned),
                    register: row
                        .get("register")
                        .and_then(Value::as_str)
                        .map(str::to_owned),
                })
                .expect("typed lookup parity");
                assert_eq!(
                    serde_json::to_value(typed).unwrap(),
                    actual,
                    "{id}: typed Rust API must match JSON dispatcher"
                );
            } else if op == "lexicon_packs" {
                let pack_list: Vec<PackInfo> = packs().expect("typed packs()");
                assert_eq!(serde_json::to_value(pack_list).unwrap(), actual, "{id}");
            }
        }
    }
}

#[cfg(all(
    feature = "lexicon-core",
    feature = "lexicon-names-taxa",
    feature = "lexicon-regional"
))]
#[test]
fn multi_pack_core_names_taxa_and_regional_lookup_and_dialect_filters() {
    let available = packs().expect("list approved multi-pack inventory");
    let ids: Vec<&str> = available.iter().map(|p| p.id.as_str()).collect();
    assert_eq!(ids, vec!["core", "names_taxa", "regional"]);
    assert!(available.iter().all(|p| p.available));

    // Cross-pack lookup across all three open CC-BY-SA-4.0 packs succeeds with compatible versions.
    let multi = execute(&json!({
        "op": "lexicon_lookup",
        "input": "\u{0ba8}\u{0ba9}\u{0bcd}\u{0bb1}\u{0bbf}",
        "packs": ["core", "names_taxa", "regional"]
    }))
    .expect("cross-pack lookup succeeds");
    validate_lookup_response_schema(&multi);
    assert_eq!(multi["status"], "matched");
    assert_eq!(multi["packs"].as_array().unwrap().len(), 3);
    assert_eq!(multi["entries"].as_array().unwrap().len(), 2);

    // Multi-pack pluricentric TN & SL region and register filtering validate cleanly.
    for reg in ["SL", "JAFFNA", "TN", "KONGU"] {
        let res = execute(&json!({
            "op": "lexicon_lookup",
            "input": "\u{0ba8}\u{0ba9}\u{0bcd}\u{0bb1}\u{0bbf}",
            "packs": ["core", "names_taxa", "regional"],
            "region": reg
        }))
        .unwrap_or_else(|err| panic!("region filter {reg} failed: {err}"));
        validate_lookup_response_schema(&res);
    }

    for register in ["colloquial", "literary", "formal"] {
        let res = execute(&json!({
            "op": "lexicon_lookup",
            "input": "\u{0b85}\u{0ba8}\u{0bcd}\u{0ba8}\u{0bbf}\u{0bb2}\u{0bc8}",
            "packs": ["core", "regional"],
            "register": register
        }))
        .unwrap_or_else(|err| panic!("register filter {register} failed: {err}"));
        validate_lookup_response_schema(&res);
    }
}

#[cfg(feature = "lexicon-core")]
#[test]
fn utf8_65536_byte_boundary_does_not_truncate() {
    let exact_ascii = "a".repeat(MAX_INPUT_BYTES);
    let ok = execute(&json!({
        "op": "lexicon_lookup",
        "input": exact_ascii
    }))
    .expect("65536 bytes must succeed");
    validate_lookup_response_schema(&ok);
    assert_eq!(ok["status"], "not_found");
    assert_eq!(
        ok["canonical_query"].as_str().unwrap().len(),
        MAX_INPUT_BYTES
    );

    // 21845 * 3 = 65535 bytes of Tamil + 1 ASCII byte = 65536 UTF-8 bytes
    let tamil_boundary = "\u{0B85}".repeat(21845) + "x";
    assert_eq!(tamil_boundary.len(), MAX_INPUT_BYTES);
    let ok_ta = execute(&json!({
        "op": "lexicon_lookup",
        "input": tamil_boundary
    }))
    .expect("65536 multi-byte UTF-8 bytes must succeed");
    validate_lookup_response_schema(&ok_ta);
    assert_eq!(ok_ta["status"], "not_found");

    // 21845 * 3 + 3 = 65538 UTF-8 bytes -> exceeds 65536
    let tamil_over = "\u{0B85}".repeat(21846);
    assert_eq!(tamil_over.len(), 65538);
    let err = execute(&json!({
        "op": "lexicon_lookup",
        "input": tamil_over
    }))
    .unwrap_err();
    assert_eq!(err, "lexicon: input exceeds 65536 UTF-8 bytes");
}

#[cfg(not(feature = "lexicon-core"))]
#[test]
fn no_data_profile_returns_empty_packs_and_unavailable_core() {
    let listed = packs().expect("packs() succeeds in no-data build");
    assert!(listed.is_empty());

    let packs_val = execute(&json!({
        "op": "lexicon_packs",
        "input": null
    }))
    .expect("lexicon_packs must return []");
    assert_eq!(packs_val, json!([]));

    let err = execute(&json!({
        "op": "lexicon_lookup",
        "input": "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}"
    }))
    .unwrap_err();
    assert_eq!(err, "lexicon: pack unavailable 'core'");

    let typed_err = tamil_toolkit::lexicon::lookup(&LookupRequest {
        input: "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}".to_owned(),
        packs: None,
        region: None,
        register: None,
    })
    .unwrap_err();
    assert_eq!(typed_err, "lexicon: pack unavailable 'core'");
}

#[test]
fn synthetic_nfd_positive_posting_and_projection_invariants() {
    // Synthetic positive canonical-equivalence posting; exact decomposed scalars live in JSONL.
    let headword_nfc = "\u{0B95}\u{0BCA}";
    let unicode_case = lexicon_unicode::fixture("nfd_ko");
    let query_nfd = unicode_case["value"].as_str().unwrap();
    assert_ne!(headword_nfc, query_nfd);

    let mut sense = sample_sense(
        "sen_synth.1",
        1,
        "synthetic two-part vowel entry",
        scope_unknown(),
        register_unknown(),
        vec![Relation {
            relation_id: "rel_synth.1".to_owned(),
            code: "synonym".to_owned(),
            directionality: "undirected".to_owned(),
            source: Endpoint {
                kind: "sense".to_owned(),
                id: "sen_synth.1".to_owned(),
            },
            target: Endpoint {
                kind: "entry".to_owned(),
                id: "ent_synth.1".to_owned(),
            },
            provenance: vec![sample_provenance("rel1", true)],
        }],
    );
    sense.annotations = vec![Annotation {
        property: "ipa".to_owned(),
        field: Field {
            availability: "withheld".to_owned(),
            value: None,
            convention: None,
            provenance: vec![],
        },
    }];
    sense.provenance = vec![sample_provenance("sen1", true)];
    let entry = sample_entry(
        "ent_synth.1",
        &"1".repeat(64),
        headword_nfc,
        scope_unknown(),
        register_unknown(),
        vec![sense],
        true,
    );
    let meta = sample_meta(
        "core",
        std::slice::from_ref(&entry),
        vec![],
        vec![],
        "0.1.0+synth",
        1,
    );
    let bytes = build_synthetic_tlpack(&meta, &[entry]);
    let view = CompiledPackView::parse(&bytes).expect("parse synthetic tlpack");

    let res = lookup_in_views(
        &LookupRequest {
            input: query_nfd.to_owned(),
            packs: Some(vec!["core".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &view)],
    )
    .expect("positive NFD lookup");

    assert_eq!(res.schema_version, SCHEMA_VERSION);
    assert_eq!(res.status, LookupStatus::Matched);
    assert_eq!(res.canonical_query, headword_nfc);
    assert_eq!(res.entries.len(), 1);
    // Defense: undirected projected to symmetric, nullable actor_id retained on accepted_auto_source
    assert_eq!(
        res.entries[0].senses[0].relations[0].directionality,
        "symmetric"
    );
    assert_eq!(res.entries[0].provenance[0].acceptance.actor_id, None);
    let as_json = serde_json::to_value(&res).unwrap();
    validate_lookup_response_schema(&as_json);

    // Corrupted offset/checksum safety check (never panics on malformed bytes)
    let mut corrupted = bytes.clone();
    let mid = corrupted.len() - 4;
    corrupted[mid] ^= 0xFF;
    assert!(CompiledPackView::parse(&corrupted).is_err());
    assert!(CompiledPackView::parse(&bytes[..32]).is_err());
}

#[test]
fn synthetic_region_and_register_truth_table_inheritance_and_overrides() {
    let rev = "2".repeat(64);
    let labels = vec![
        region_label("IN", None),
        region_label("IN-TN", Some("IN")),
        region_label("LK", None),
        region_label("LK-JAFFNA", Some("LK")),
    ];

    // Entry 1: entry attested LK, sense 1 attested LK-JAFFNA, sense 2 attested LK, sense 3 explicit unknown
    let e1 = sample_entry(
        "ent_r.1",
        &rev,
        "\u{0B95}\u{0BB2}\u{0BCD}",
        scope_attested(&["LK"], "e1reg"),
        register_available("literary", "e1rg"),
        vec![
            sample_sense(
                "sen_r.1",
                1,
                "Jaffna child sense",
                scope_attested(&["LK-JAFFNA"], "s1"),
                register_available("colloquial", "s1rg"),
                vec![],
            ),
            sample_sense(
                "sen_r.2",
                2,
                "All-LK parent sense",
                scope_attested(&["LK"], "s2"),
                register_available("literary", "s2rg"),
                vec![],
            ),
            sample_sense(
                "sen_r.3",
                3,
                "Explicit unknown region & register override",
                scope_unknown(),
                register_unknown(),
                vec![],
            ),
        ],
        false,
    );

    // Entry 2: unrestricted region and compiler-emitted unrestricted register (availability="available", value="unrestricted")
    let e2 = sample_entry(
        "ent_r.2",
        &rev,
        "\u{0B95}\u{0BB2}\u{0BCD}",
        scope_unrestricted("e2reg"),
        register_unrestricted("e2rg"),
        vec![sample_sense(
            "sen_r.4",
            1,
            "Unrestricted sense",
            scope_unrestricted("s4"),
            register_unrestricted("s4rg"),
            vec![],
        )],
        false,
    );

    // Entry 3: Tamil Nadu attested only (incompatible with LK / LK-JAFFNA)
    let e3 = sample_entry(
        "ent_r.3",
        &rev,
        "\u{0B95}\u{0BB2}\u{0BCD}",
        scope_attested(&["IN-TN"], "e3reg"),
        register_available("literary", "e3rg"),
        vec![sample_sense(
            "sen_r.5",
            1,
            "TN-only sense",
            scope_attested(&["IN-TN"], "s5"),
            register_available("literary", "s5rg"),
            vec![],
        )],
        false,
    );

    // Entry 4: unrestricted region with explicit colloquial register
    let e4 = sample_entry(
        "ent_r.4",
        &rev,
        "\u{0B95}\u{0BB2}\u{0BCD}",
        scope_unrestricted("e4reg"),
        register_available("colloquial", "e4rg"),
        vec![sample_sense(
            "sen_r.6",
            1,
            "Colloquial unrestricted-region sense",
            scope_unrestricted("s6"),
            register_available("colloquial", "s6rg"),
            vec![],
        )],
        false,
    );

    let entries = vec![e1, e2, e3, e4];
    let meta = sample_meta(
        "core",
        &entries,
        labels,
        vec!["literary", "colloquial"],
        "0.1.0+synth",
        1,
    );
    let bytes = build_synthetic_tlpack(&meta, &entries);
    let view = CompiledPackView::parse(&bytes).expect("parse region pack");

    // 1. Unfiltered: unknown scopes stay visible, all 4 entries returned and schema-valid
    let unfiltered = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: Some(vec!["core".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&unfiltered).unwrap());
    assert_eq!(unfiltered.entries.len(), 4);
    assert_eq!(unfiltered.entries[0].senses.len(), 3);

    // 2. Region LK: includes child LK-JAFFNA (sen_r.1), LK (sen_r.2), unrestricted (e2, e4); drops unknown (sen_r.3) and IN-TN (e3)
    let lk = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: Some("LK".to_owned()),
            register: None,
        },
        &[("core", &view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&lk).unwrap());
    assert_eq!(lk.entries.len(), 3);
    assert_eq!(lk.entries[0].entry_id, "ent_r.1");
    let e1_senses: Vec<&str> = lk.entries[0]
        .senses
        .iter()
        .map(|s| s.sense_id.as_str())
        .collect();
    assert_eq!(e1_senses, vec!["sen_r.1", "sen_r.2"]);
    assert_eq!(lk.entries[1].entry_id, "ent_r.2");
    assert_eq!(lk.entries[2].entry_id, "ent_r.4");

    // 3. Region LK-JAFFNA: includes attested LK-JAFFNA (sen_r.1) + unrestricted (e2, e4); parent LK alone (sen_r.2) does NOT match child!
    let jaffna = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: Some("LK-JAFFNA".to_owned()),
            register: None,
        },
        &[("core", &view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&jaffna).unwrap());
    assert_eq!(jaffna.entries.len(), 3);
    let e1_jaffna: Vec<&str> = jaffna.entries[0]
        .senses
        .iter()
        .map(|s| s.sense_id.as_str())
        .collect();
    assert_eq!(e1_jaffna, vec!["sen_r.1"]);

    // 4. Register colloquial + region LK: exact equality matches ONLY sen_r.1 (colloquial) and ent_r.4 (colloquial);
    // compiler-emitted register "unrestricted" on ent_r.2 does NOT match colloquial filter.
    let coll_lk = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: Some("LK".to_owned()),
            register: Some("colloquial".to_owned()),
        },
        &[("core", &view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&coll_lk).unwrap());
    assert_eq!(coll_lk.entries.len(), 2);
    assert_eq!(coll_lk.entries[0].entry_id, "ent_r.1");
    assert_eq!(coll_lk.entries[0].senses.len(), 1);
    assert_eq!(coll_lk.entries[0].senses[0].sense_id, "sen_r.1");
    assert_eq!(coll_lk.entries[1].entry_id, "ent_r.4");

    // 5. Region IN-TN + register colloquial: only ent_r.4 (region unrestricted + register colloquial) survives;
    // ent_r.2 (register "unrestricted") and ent_r.3 (literary) are excluded.
    let tn_coll = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: Some("IN-TN".to_owned()),
            register: Some("colloquial".to_owned()),
        },
        &[("core", &view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&tn_coll).unwrap());
    assert_eq!(tn_coll.entries.len(), 1);
    assert_eq!(tn_coll.entries[0].entry_id, "ent_r.4");

    // 6. Verify schema validator rejects forbidden availability="unrestricted" on LabelField AND runtime never matches it as a wildcard.
    let schema: Value = serde_json::from_str(LOOKUP_RESPONSE_SCHEMA_JSON).unwrap();
    let mut bad_response = serde_json::to_value(&tn_coll).unwrap();
    bad_response["entries"][0]["senses"][0]["register"]["availability"] =
        Value::String("unrestricted".to_owned());
    assert!(
        check_schema_node(&bad_response, &schema, &schema, "LookupResponse").is_err(),
        "schema must reject availability='unrestricted' on LabelField"
    );

    let mut bad_field_entry = entries[3].clone();
    bad_field_entry.entry_id = "ent_bad.1".to_owned();
    bad_field_entry.senses[0].register = LabelField {
        availability: "unrestricted".to_owned(),
        value: Some("colloquial".to_owned()),
        convention: None,
        provenance: vec![sample_provenance("bad_reg", false)],
    };
    let bad_pack_entries = vec![bad_field_entry];
    let bad_meta = sample_meta(
        "core",
        &bad_pack_entries,
        vec![],
        vec!["colloquial"],
        "0.1.0+synth",
        1,
    );
    let bad_bytes = build_synthetic_tlpack(&bad_meta, &bad_pack_entries);
    let bad_view = CompiledPackView::parse(&bad_bytes).unwrap();
    let bad_filtered = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: None,
            register: Some("colloquial".to_owned()),
        },
        &[("core", &bad_view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&bad_filtered).unwrap());
    assert_eq!(bad_filtered.status, LookupStatus::NotFound);
    assert!(bad_filtered.entries.is_empty());

    // Check 0 surviving entries returns status=not_found (query unknown TN+colloquial on literary-only entry)
    let e3_only_entries = vec![entries[2].clone()];
    let meta3 = sample_meta(
        "core",
        &e3_only_entries,
        vec![region_label("IN-TN", None)],
        vec!["literary", "colloquial"],
        "0.1.0+synth",
        1,
    );
    let bytes3 = build_synthetic_tlpack(&meta3, &e3_only_entries);
    let view3 = CompiledPackView::parse(&bytes3).unwrap();
    let all_dropped = lookup_in_views(
        &LookupRequest {
            input: "\u{0B95}\u{0BB2}\u{0BCD}".to_owned(),
            packs: None,
            region: Some("IN-TN".to_owned()),
            register: Some("colloquial".to_owned()),
        },
        &[("core", &view3)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&all_dropped).unwrap());
    assert_eq!(all_dropped.status, LookupStatus::NotFound);
    assert!(all_dropped.entries.is_empty());
}

#[test]
fn synthetic_multipack_dedup_and_incompatible_pack_versions() {
    let rev_a = "3".repeat(64);
    let rev_b = "4".repeat(64);
    let shared = sample_entry(
        "ent_m.1",
        &rev_a,
        "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}",
        scope_unknown(),
        register_unknown(),
        vec![sample_sense(
            "sen_m.1",
            1,
            "mother",
            scope_unknown(),
            register_unknown(),
            vec![],
        )],
        false,
    );
    let extra = sample_entry(
        "ent_m.2",
        &rev_a,
        "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}",
        scope_unknown(),
        register_unknown(),
        vec![sample_sense(
            "sen_m.2",
            1,
            "term sense",
            scope_unknown(),
            register_unknown(),
            vec![],
        )],
        false,
    );

    // Compatible core + terminology sharing ent_m.1 (same revision) -> deduplicated into 2 entries sorted by entry_id
    let core_entries = vec![shared.clone()];
    let term_entries = vec![shared.clone(), extra.clone()];
    let core_meta = sample_meta("core", &core_entries, vec![], vec![], "0.1.0+synth", 1);
    let term_meta = sample_meta(
        "terminology",
        &term_entries,
        vec![],
        vec![],
        "0.1.0+synth",
        1,
    );
    let core_bytes = build_synthetic_tlpack(&core_meta, &core_entries);
    let term_bytes = build_synthetic_tlpack(&term_meta, &term_entries);
    let core_view = CompiledPackView::parse(&core_bytes).unwrap();
    let term_view = CompiledPackView::parse(&term_bytes).unwrap();

    let merged = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["terminology".to_owned(), "core".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &term_view)],
    )
    .unwrap();
    validate_lookup_response_schema(&serde_json::to_value(&merged).unwrap());
    assert_eq!(
        merged
            .packs
            .iter()
            .map(|p| p.id.as_str())
            .collect::<Vec<_>>(),
        vec!["core", "terminology"]
    );
    assert_eq!(
        merged
            .entries
            .iter()
            .map(|e| e.entry_id.as_str())
            .collect::<Vec<_>>(),
        vec!["ent_m.1", "ent_m.2"]
    );

    // Conflicting revision on same entry_id -> "lexicon: incompatible pack versions"
    let mut shared_conflict = shared.clone();
    shared_conflict.revision = rev_b;
    let term_conflict_entries = vec![shared_conflict];
    let term_conflict_meta = sample_meta(
        "terminology",
        &term_conflict_entries,
        vec![],
        vec![],
        "0.1.0+synth",
        1,
    );
    let term_conflict_bytes = build_synthetic_tlpack(&term_conflict_meta, &term_conflict_entries);
    let term_conflict_view = CompiledPackView::parse(&term_conflict_bytes).unwrap();
    let err = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "terminology".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &term_conflict_view)],
    )
    .unwrap_err();
    assert_eq!(err, "lexicon: incompatible pack versions");

    // Different dataset_version across packs -> "lexicon: incompatible pack versions"
    let term_ver_meta = sample_meta(
        "terminology",
        std::slice::from_ref(&extra),
        vec![],
        vec![],
        "0.2.0+other",
        1,
    );
    let term_ver_bytes = build_synthetic_tlpack(&term_ver_meta, &[extra]);
    let term_ver_view = CompiledPackView::parse(&term_ver_bytes).unwrap();
    let err_ver = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "terminology".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &term_ver_view)],
    )
    .unwrap_err();
    assert_eq!(err_ver, "lexicon: incompatible pack versions");
}

#[test]
fn cli_lexicon_packs_and_lookup_contract() {
    let bin = env!("CARGO_BIN_EXE_tamil-toolkit");

    // 1. lexicon packs
    let out_packs = Command::new(bin)
        .args(["lexicon", "packs"])
        .output()
        .expect("run cli lexicon packs");
    assert!(
        out_packs.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out_packs.stderr)
    );
    let parsed_packs: Value =
        serde_json::from_slice(&out_packs.stdout).expect("cli packs stdout json");
    let expected_packs = execute(&json!({"op": "lexicon_packs", "input": null})).unwrap();
    assert_eq!(parsed_packs, expected_packs);

    // 2. unknown CLI flag fails nonzero
    let out_bad_flag = Command::new(bin)
        .args([
            "lexicon",
            "lookup",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            "--bogus",
        ])
        .output()
        .expect("run cli unknown flag");
    assert!(!out_bad_flag.status.success());

    let out_bad_packs_flag = Command::new(bin)
        .args(["lexicon", "packs", "--unexpected"])
        .output()
        .expect("run cli packs bad flag");
    assert!(!out_bad_packs_flag.status.success());

    // 3. missing flag value fails nonzero
    let out_missing_val = Command::new(bin)
        .args([
            "lexicon",
            "lookup",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            "--pack",
        ])
        .output()
        .expect("run cli missing pack value");
    assert!(!out_missing_val.status.success());

    // 4. duplicate --region fails nonzero
    let out_dup_region = Command::new(bin)
        .args([
            "lexicon",
            "lookup",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            "--region",
            "IN",
            "--region",
            "LK",
        ])
        .output()
        .expect("run cli dup region");
    assert!(!out_dup_region.status.success());

    // 5. missing <TEXT>, extra positional arg, empty --pack / --region validation
    assert!(!Command::new(bin)
        .args(["lexicon", "lookup"])
        .output()
        .unwrap()
        .status
        .success());
    assert!(!Command::new(bin)
        .args(["lexicon", "lookup", "one", "two"])
        .output()
        .unwrap()
        .status
        .success());
    let out_empty_pack = Command::new(bin)
        .args([
            "lexicon",
            "lookup",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            "--pack",
            "",
        ])
        .output()
        .unwrap();
    assert!(!out_empty_pack.status.success());
    assert!(String::from_utf8_lossy(&out_empty_pack.stderr)
        .contains("lexicon: packs must be a nonempty string array"));
    let out_empty_region = Command::new(bin)
        .args([
            "lexicon",
            "lookup",
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            "--region",
            "",
        ])
        .output()
        .unwrap();
    assert!(!out_empty_region.status.success());
    assert!(String::from_utf8_lossy(&out_empty_region.stderr).contains("lexicon: invalid options"));

    #[cfg(not(feature = "lexicon-core"))]
    {
        let out_unavail = Command::new(bin)
            .args([
                "lexicon",
                "lookup",
                "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            ])
            .output()
            .unwrap();
        assert!(!out_unavail.status.success());
        assert!(String::from_utf8_lossy(&out_unavail.stderr)
            .contains("lexicon: pack unavailable 'core'"));
    }

    #[cfg(feature = "lexicon-core")]
    {
        // Quoted spaces preserved & repeated --pack accepted
        let out_ws = Command::new(bin)
            .args([
                "lexicon",
                "lookup",
                "  \u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}  ",
                "--pack",
                "core",
                "--pack",
                "core",
            ])
            .output()
            .expect("run cli whitespace");
        assert!(out_ws.status.success());
        let val_ws: Value = serde_json::from_slice(&out_ws.stdout).expect("stdout json");
        assert_eq!(val_ws["status"], "not_found");
        assert_eq!(
            val_ws["canonical_query"],
            "  \u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}  "
        );
        assert_eq!(val_ws["packs"].as_array().unwrap().len(), 1);

        // Matched homographs ordered cleanly
        let out_hit = Command::new(bin)
            .args([
                "lexicon",
                "lookup",
                "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            ])
            .output()
            .expect("run cli match");
        assert!(out_hit.status.success());
        let val_hit: Value = serde_json::from_slice(&out_hit.stdout).expect("stdout json");
        assert_eq!(val_hit["status"], "matched");
        assert_eq!(val_hit["entries"].as_array().unwrap().len(), 2);

        // Unknown region yields contract error + nonzero exit
        let out_reg = Command::new(bin)
            .args([
                "lexicon",
                "lookup",
                "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
                "--region",
                "LK-JAFFNA",
            ])
            .output()
            .expect("run cli unknown region");
        assert!(!out_reg.status.success());
        assert!(String::from_utf8_lossy(&out_reg.stderr)
            .contains("lexicon: unknown region 'LK-JAFFNA'"));
    }
}

#[test]
fn synthetic_multipack_compatible_promote_versions_with_distinct_manifest_hashes() {
    let rev_a = "c".repeat(64);
    let core_entry = sample_entry(
        "ent_compat_core",
        &rev_a,
        "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}",
        Scope {
            state: "unknown".to_owned(),
            codes: vec![],
            provenance: vec![],
        },
        LabelField {
            availability: "unknown".to_owned(),
            value: None,
            convention: None,
            provenance: vec![],
        },
        vec![sample_sense(
            "sen_compat_core",
            1,
            "mother",
            Scope {
                state: "unknown".to_owned(),
                codes: vec![],
                provenance: vec![],
            },
            LabelField {
                availability: "unknown".to_owned(),
                value: None,
                convention: None,
                provenance: vec![],
            },
            vec![],
        )],
        true,
    );
    let term_entry = sample_entry(
        "ent_compat_term",
        &"d".repeat(64),
        "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}",
        Scope {
            state: "unknown".to_owned(),
            codes: vec![],
            provenance: vec![],
        },
        LabelField {
            availability: "unknown".to_owned(),
            value: None,
            convention: None,
            provenance: vec![],
        },
        vec![sample_sense(
            "sen_compat_term",
            1,
            "termmother",
            Scope {
                state: "unknown".to_owned(),
                codes: vec![],
                provenance: vec![],
            },
            LabelField {
                availability: "unknown".to_owned(),
                value: None,
                convention: None,
                provenance: vec![],
            },
            vec![],
        )],
        true,
    );

    let mut core_meta = sample_meta(
        "core",
        std::slice::from_ref(&core_entry),
        vec![],
        vec![],
        "0.1.0+111111111111",
        1,
    );
    core_meta.manifest_sha256 = "1".repeat(64);
    let core_bytes = build_synthetic_tlpack(&core_meta, &[core_entry]);
    let core_view = CompiledPackView::parse(&core_bytes).unwrap();

    let mut term_meta = sample_meta(
        "terminology",
        std::slice::from_ref(&term_entry),
        vec![],
        vec![],
        "0.1.0+222222222222",
        1,
    );
    term_meta.manifest_sha256 = "2".repeat(64);
    let term_bytes = build_synthetic_tlpack(&term_meta, std::slice::from_ref(&term_entry));
    let term_view = CompiledPackView::parse(&term_bytes).unwrap();

    let resp = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "terminology".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &term_view)],
    )
    .expect("independently promoted compatible packs with matching base dataset_version should interoperate");
    assert_eq!(resp.status, LookupStatus::Matched);
    assert_eq!(resp.entries.len(), 2);
    assert_eq!(resp.packs[0].dataset_version, "0.1.0+111111111111");
    assert_eq!(resp.packs[1].dataset_version, "0.1.0+222222222222");

    // Different base dataset_version with distinct +manifest_hash must still fail
    let mut bad_base_meta = term_meta.clone();
    bad_base_meta.dataset_version = "0.2.0+222222222222".to_owned();
    let bad_base_bytes = build_synthetic_tlpack(&bad_base_meta, std::slice::from_ref(&term_entry));
    let bad_base_view = CompiledPackView::parse(&bad_base_bytes).unwrap();
    let err = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "terminology".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &bad_base_view)],
    )
    .unwrap_err();
    assert_eq!(err, "lexicon: incompatible pack versions");

    // Same base version (+manifest_hash differing) still rejects conflicting shared entry revisions
    let mut bad_rev_entry = term_entry.clone();
    bad_rev_entry.entry_id = "ent_compat_core".to_owned();
    bad_rev_entry.revision = "e".repeat(64);
    let mut bad_rev_meta = sample_meta(
        "terminology",
        std::slice::from_ref(&bad_rev_entry),
        vec![],
        vec![],
        "0.1.0+222222222222",
        1,
    );
    bad_rev_meta.manifest_sha256 = "2".repeat(64);
    let bad_rev_bytes = build_synthetic_tlpack(&bad_rev_meta, &[bad_rev_entry]);
    let bad_rev_view = CompiledPackView::parse(&bad_rev_bytes).unwrap();
    let err = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "terminology".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("terminology", &bad_rev_view)],
    )
    .unwrap_err();
    assert_eq!(err, "lexicon: incompatible pack versions");
}

#[test]
fn synthetic_vocabularies_regions_hierarchy_and_conflict() {
    let mk_entry = |eid: &str, rev: &str, reg_code: &str| {
        sample_entry(
            eid,
            rev,
            "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}",
            Scope {
                state: "attested".to_owned(),
                codes: vec![reg_code.to_owned()],
                provenance: vec![],
            },
            LabelField {
                availability: "unknown".to_owned(),
                value: None,
                convention: None,
                provenance: vec![],
            },
            vec![sample_sense(
                &format!("sen_{eid}"),
                1,
                "mother",
                Scope {
                    state: "attested".to_owned(),
                    codes: vec![reg_code.to_owned()],
                    provenance: vec![],
                },
                LabelField {
                    availability: "unknown".to_owned(),
                    value: None,
                    convention: None,
                    provenance: vec![],
                },
                vec![],
            )],
            true,
        )
    };

    let core_entry = mk_entry("ent_vreg_core", &"e".repeat(64), "LK-JAFFNA");
    let mut core_meta = sample_meta(
        "core",
        std::slice::from_ref(&core_entry),
        vec![],
        vec![],
        "0.1.0+aaaaaaaaaaaa",
        1,
    );
    core_meta.manifest_sha256 = "a".repeat(64);
    core_meta.vocabularies.regions = vec![
        CompiledVocabRegion {
            code: "LK".to_owned(),
            parent_code: None,
        },
        CompiledVocabRegion {
            code: "LK-JAFFNA".to_owned(),
            parent_code: Some("LK".to_owned()),
        },
    ];
    let core_bytes = build_synthetic_tlpack(&core_meta, &[core_entry]);
    let core_view = CompiledPackView::parse(&core_bytes).unwrap();

    // Parent filter "LK" matches child "LK-JAFFNA" purely from meta.vocabularies.regions
    let resp = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned()]),
            region: Some("LK".to_owned()),
            register: None,
        },
        &[("core", &core_view)],
    )
    .expect("parent region from meta.vocabularies.regions must be known and match child");
    assert_eq!(resp.status, LookupStatus::Matched);
    assert_eq!(resp.entries.len(), 1);

    // Cross-pack conflict on vocabularies.regions parent_code fails with incompatible pack versions
    let reg_entry = mk_entry("ent_vreg_reg", &"f".repeat(64), "LK-JAFFNA");
    let mut reg_meta = sample_meta(
        "regional",
        std::slice::from_ref(&reg_entry),
        vec![],
        vec![],
        "0.1.0+bbbbbbbbbbbb",
        1,
    );
    reg_meta.manifest_sha256 = "b".repeat(64);
    reg_meta.vocabularies.regions = vec![CompiledVocabRegion {
        code: "LK-JAFFNA".to_owned(),
        parent_code: Some("IN-TN".to_owned()),
    }];
    let reg_bytes = build_synthetic_tlpack(&reg_meta, &[reg_entry]);
    let reg_view = CompiledPackView::parse(&reg_bytes).unwrap();

    let err = lookup_in_views(
        &LookupRequest {
            input: "\u{0B85}\u{0BAE}\u{0BCD}\u{0BAE}\u{0BBE}".to_owned(),
            packs: Some(vec!["core".to_owned(), "regional".to_owned()]),
            region: None,
            register: None,
        },
        &[("core", &core_view), ("regional", &reg_view)],
    )
    .unwrap_err();
    assert_eq!(err, "lexicon: incompatible pack versions");
}
