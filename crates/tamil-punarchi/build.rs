use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::{env, fs, path::PathBuf};
use unicode_normalization::is_nfc;

const EXPECTED_PMUNI_SHA256: &str =
    "b970b4ee13b4b4e96dfd641b1e37d1c87bdfdc0b83fce1fcb24c664841671955";

// Enforces 117/117 inventory + forward [[rule]].sutra integrity + reverse 106/106 executable coverage.
const ENFORCE_REVERSE_COVERAGE: bool = true;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Metadata {
    profile: String,
    version: String,
    primary_edition: String,
    kandigai_edition: String,
    cross_check_edition: String,
    cross_check_sha256: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InventoryFile {
    metadata: Metadata,
    sutra: Vec<InventorySutra>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InventorySutra {
    sutra: u16,
    chapter: String,
    tier: String,
    executable: bool,
    tva_page: u16,
    kandigai_sutra: u16,
    pm_ref: String,
    summary: String,
    edition_note: Option<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RulesFile {
    metadata: Metadata,
    #[serde(default)]
    chariyai: Vec<ChariyaiRow>,
    #[serde(default)]
    case_suffix: Vec<CaseSuffixRow>,
    #[serde(default)]
    closed_class: Vec<ClosedClassRow>,
    #[serde(default)]
    rule: Vec<RuleRow>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ChariyaiRow {
    id: String,
    form: String,
    sutra: u16,
    attach_classes: Vec<String>,
    #[serde(default)]
    case_filter: Vec<String>,
    #[serde(default)]
    stack_after: Vec<String>,
    #[serde(default)]
    post_um: bool,
    #[serde(default)]
    suppress_205: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CaseSuffixRow {
    case_number: u8,
    form: String,
    sutra: u16,
    #[serde(default)]
    force_165: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ClosedClassRow {
    class_id: String,
    sutra: u16,
    stems: Vec<String>,
    #[serde(default)]
    oblique_map: BTreeMap<String, Vec<String>>,
    notes: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RuleRow {
    id: String,
    sutra: u16,
    chapter: String,
    stage: u8,
    substage: String,
    priority: u16,
    transform: String,
    relation: String,
    subtype: Option<String>,
    lexical_class: Option<String>,
    poetic: bool,
    optional: bool,
    reversible: bool,
    left_match: String,
    right_match: String,
    action: String,
    #[serde(default)]
    flags: Vec<String>,
    evidence_layer: String,
}

fn read_lexicon_file(name: &str) -> String {
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let canonical = root.join("../../lexicon").join(name);
    let path = if canonical.is_file() {
        canonical
    } else {
        root.join("lexicon").join(name)
    };
    println!("cargo:rerun-if-changed={}", path.display());
    fs::read_to_string(&path).unwrap_or_else(|e| panic!("failed to read {}: {e}", path.display()))
}

fn validate_metadata(meta: &Metadata, label: &str) {
    assert_eq!(meta.profile, "nannool-v1", "{label}: unexpected profile");
    assert_eq!(meta.version, "0.1", "{label}: unexpected version");
    assert!(
        !meta.primary_edition.trim().is_empty(),
        "{label}: empty primary_edition"
    );
    assert!(
        !meta.kandigai_edition.trim().is_empty(),
        "{label}: empty kandigai_edition"
    );
    assert!(
        !meta.cross_check_edition.trim().is_empty(),
        "{label}: empty cross_check_edition"
    );
    assert_eq!(
        meta.cross_check_sha256, EXPECTED_PMUNI_SHA256,
        "{label}: cross_check_sha256 must match tests/reference/punarchi-nannool/sources.json"
    );
}

fn expected_chapter(sutra: u16) -> &'static str {
    match sutra {
        93 | 94 | 102..=108 => "ezhuttiyal",
        136 => "padaviyal",
        151..=203 => "uyireeru",
        204..=239 => "meyyeeru",
        240..=257 => "urupu",
        _ => panic!("sutra {sutra} is outside the 117-sutra nannool-v1 set"),
    }
}

fn expected_non_executable(sutra: u16) -> bool {
    matches!(sutra, 151..=157 | 239 | 240 | 241 | 253)
}

fn expected_sutras_set() -> BTreeSet<u16> {
    let mut set = BTreeSet::new();
    set.insert(93);
    set.insert(94);
    for s in 102..=108 {
        set.insert(s);
    }
    set.insert(136);
    for s in 151..=257 {
        set.insert(s);
    }
    assert_eq!(set.len(), 117);
    set
}

fn validate_substage(stage: u8, substage: &str, rule_id: &str) {
    let expected_stage = match substage {
        "1a" | "1b" | "1c" => 1,
        "2" => 2,
        "3a" | "3b" | "3c" | "3d" => 3,
        "4" => 4,
        other => panic!("rule {rule_id}: invalid substage {other:?}"),
    };
    assert_eq!(
        stage, expected_stage,
        "rule {rule_id}: stage {stage} contradicts substage {substage:?}"
    );
}

fn main() {
    let inv_raw = read_lexicon_file("punarchi-nannool-inventory.toml");
    let rules_raw = read_lexicon_file("punarchi-nannool.toml");

    let mut inv: InventoryFile = toml::from_str(&inv_raw).expect("parse inventory TOML");
    let rules: RulesFile = toml::from_str(&rules_raw).expect("parse rules TOML");

    validate_metadata(&inv.metadata, "punarchi-nannool-inventory.toml");
    validate_metadata(&rules.metadata, "punarchi-nannool.toml");

    // 1. Validate 117-sutra inventory completeness and field invariants.
    let expected_set = expected_sutras_set();
    let mut inv_map: BTreeMap<u16, &InventorySutra> = BTreeMap::new();
    inv.sutra.sort_by_key(|s| s.sutra);

    for row in &inv.sutra {
        assert!(
            inv_map.insert(row.sutra, row).is_none(),
            "duplicate sutra {} in inventory",
            row.sutra
        );
        assert_eq!(
            row.chapter,
            expected_chapter(row.sutra),
            "sutra {}: wrong chapter {}",
            row.sutra,
            row.chapter
        );
        assert!(
            matches!(
                row.tier.as_str(),
                "phonological"
                    | "closed_class"
                    | "context_dependent"
                    | "poetic_closed"
                    | "definition_or_scope"
            ),
            "sutra {}: invalid tier {}",
            row.sutra,
            row.tier
        );
        if expected_non_executable(row.sutra) {
            assert!(
                !row.executable && row.tier == "definition_or_scope",
                "sutra {}: expected non-executable definition_or_scope",
                row.sutra
            );
        } else {
            assert!(
                row.executable,
                "sutra {}: expected executable == true",
                row.sutra
            );
        }
        assert!(
            (166..=303).contains(&row.tva_page),
            "sutra {}: tva_page {} outside 166..=303",
            row.sutra,
            row.tva_page
        );
        assert_eq!(
            row.kandigai_sutra, row.sutra,
            "sutra {}: kandigai_sutra mismatch",
            row.sutra
        );
        assert!(
            !row.pm_ref.trim().is_empty(),
            "sutra {}: empty pm_ref",
            row.sutra
        );
        assert!(
            !row.summary.trim().is_empty() && is_nfc(&row.summary),
            "sutra {}: summary must be non-empty NFC",
            row.sutra
        );
        if let Some(note) = &row.edition_note {
            assert!(
                !note.trim().is_empty() && is_nfc(note),
                "sutra {}: edition_note must be non-empty NFC",
                row.sutra
            );
        }
    }

    let seen_set: BTreeSet<u16> = inv_map.keys().copied().collect();
    assert_eq!(
        seen_set, expected_set,
        "inventory must contain exact 117 sutras"
    );

    // 2. Validate chariyai entries (all 17 from Sutra 244).
    let mut chariyai_ids = BTreeSet::new();
    assert!(
        rules.chariyai.len() >= 17,
        "expected all 17 chariyais from sutra 244, got {}",
        rules.chariyai.len()
    );
    for ch in &rules.chariyai {
        assert!(
            !ch.id.is_empty() && chariyai_ids.insert(ch.id.as_str()),
            "duplicate or empty chariyai id {:?}",
            ch.id
        );
        assert!(
            !ch.form.is_empty() && is_nfc(&ch.form),
            "chariyai {}: form must be non-empty NFC",
            ch.id
        );
        assert!(
            inv_map.contains_key(&ch.sutra),
            "chariyai {}: unknown sutra {}",
            ch.id,
            ch.sutra
        );
    }

    // 3. Validate case_suffix entries.
    assert!(
        rules.case_suffix.len() >= 6,
        "expected at least 6 oblique case_suffix entries"
    );
    for cs in &rules.case_suffix {
        assert!(
            (2..=7).contains(&cs.case_number),
            "case_suffix {}: case_number must be 2..=7",
            cs.form
        );
        assert!(
            !cs.form.is_empty() && is_nfc(&cs.form),
            "case_suffix: form must be non-empty NFC"
        );
        assert!(
            (240..=242).contains(&cs.sutra),
            "case_suffix {}: sutra {} outside 240..=242",
            cs.form,
            cs.sutra
        );
    }

    // 4. Validate closed_class entries.
    let mut class_ids = BTreeSet::new();
    for cc in &rules.closed_class {
        assert!(
            !cc.class_id.is_empty() && class_ids.insert(cc.class_id.as_str()),
            "duplicate or empty closed_class id {:?}",
            cc.class_id
        );
        assert!(
            inv_map.contains_key(&cc.sutra),
            "closed_class {}: unknown sutra {}",
            cc.class_id,
            cc.sutra
        );
        assert!(
            !cc.stems.is_empty() || !cc.oblique_map.is_empty(),
            "closed_class {}: must define stems or oblique_map",
            cc.class_id
        );
        for stem in &cc.stems {
            assert!(
                !stem.is_empty() && is_nfc(stem),
                "closed_class {}: non-NFC or empty stem {:?}",
                cc.class_id,
                stem
            );
        }
        for (k, vals) in &cc.oblique_map {
            assert!(
                !k.is_empty() && is_nfc(k) && !vals.is_empty(),
                "closed_class {}: invalid oblique_map key {:?}",
                cc.class_id,
                k
            );
            for v in vals {
                assert!(
                    !v.is_empty() && is_nfc(v),
                    "closed_class {}: invalid oblique_map value {:?}",
                    cc.class_id,
                    v
                );
            }
        }
        assert!(
            !cc.notes.trim().is_empty() && is_nfc(&cc.notes),
            "closed_class {}: notes must be non-empty NFC",
            cc.class_id
        );
    }

    // 5. Validate rules & forward referential integrity.
    let mut rule_ids = BTreeSet::new();
    let mut covered_sutras = BTreeSet::new();
    for r in &rules.rule {
        assert!(
            !r.id.is_empty() && rule_ids.insert(r.id.as_str()),
            "duplicate or empty rule id {:?}",
            r.id
        );
        let inv_entry = inv_map.get(&r.sutra).unwrap_or_else(|| {
            panic!(
                "rule {}: sutra {} not in 117-sutra inventory",
                r.id, r.sutra
            )
        });
        assert!(
            inv_entry.executable || r.sutra == 153,
            "rule {}: references non-executable sutra {}",
            r.id,
            r.sutra
        );
        assert_eq!(
            r.chapter, inv_entry.chapter,
            "rule {}: chapter {} mismatches inventory chapter {}",
            r.id, r.chapter, inv_entry.chapter
        );
        validate_substage(r.stage, &r.substage, &r.id);
        assert!(
            matches!(
                r.transform.as_str(),
                "iyalbu" | "thonral" | "thirithal" | "keduthal"
            ),
            "rule {}: invalid transform {:?}",
            r.id,
            r.transform
        );
        assert!(
            matches!(r.relation.as_str(), "unspecified" | "vetrumai" | "alvazhi"),
            "rule {}: invalid relation {:?}",
            r.id,
            r.relation
        );
        assert!(
            matches!(
                r.evidence_layer.as_str(),
                "root_sutra" | "commentary_gloss" | "attested_example" | "extended_usage"
            ),
            "rule {}: invalid evidence_layer {:?}",
            r.id,
            r.evidence_layer
        );
        assert!(
            is_nfc(&r.left_match) && is_nfc(&r.right_match) && is_nfc(&r.action),
            "rule {}: left_match/right_match/action must be NFC",
            r.id
        );
        covered_sutras.insert(r.sutra);
    }

    if ENFORCE_REVERSE_COVERAGE {
        let missing: Vec<u16> = inv
            .sutra
            .iter()
            .filter(|s| s.executable && !covered_sutras.contains(&s.sutra))
            .map(|s| s.sutra)
            .collect();
        assert!(
            missing.is_empty(),
            "executable inventory sutras missing declarative [[rule]] entries: {missing:?}"
        );
    }

    // 6. Generate static Rust tables in OUT_DIR/punarchi_tables.rs.
    let mut out = String::with_capacity(64 * 1024);
    writeln!(
        out,
        "pub const PROFILE_ID: &str = {:?};",
        inv.metadata.profile
    )
    .unwrap();
    writeln!(
        out,
        "pub const CROSS_CHECK_SHA256: &str = {:?};",
        inv.metadata.cross_check_sha256
    )
    .unwrap();

    writeln!(out, "pub const INVENTORY: &[SutraInventoryEntry] = &[").unwrap();
    for s in &inv.sutra {
        let note = match &s.edition_note {
            Some(n) => format!("Some({n:?})"),
            None => "None".to_string(),
        };
        writeln!(
            out,
            "    SutraInventoryEntry {{ sutra: {}, chapter: {:?}, tier: {:?}, executable: {}, tva_page: {}, kandigai_sutra: {}, pm_ref: {:?}, summary: {:?}, edition_note: {} }},",
            s.sutra, s.chapter, s.tier, s.executable, s.tva_page, s.kandigai_sutra, s.pm_ref, s.summary, note
        )
        .unwrap();
    }
    writeln!(out, "];").unwrap();

    writeln!(out, "pub const CHARIYAIS: &[ChariyaiDef] = &[").unwrap();
    for c in &rules.chariyai {
        writeln!(
            out,
            "    ChariyaiDef {{ id: {:?}, form: {:?}, sutra: {}, attach_classes: &{:?}, case_filter: &{:?}, stack_after: &{:?}, post_um: {}, suppress_205: {} }},",
            c.id, c.form, c.sutra, c.attach_classes, c.case_filter, c.stack_after, c.post_um, c.suppress_205
        )
        .unwrap();
    }
    writeln!(out, "];").unwrap();

    writeln!(out, "pub const CASE_SUFFIXES: &[CaseSuffixDef] = &[").unwrap();
    for cs in &rules.case_suffix {
        writeln!(
            out,
            "    CaseSuffixDef {{ case_number: {}, form: {:?}, sutra: {}, force_165: {} }},",
            cs.case_number, cs.form, cs.sutra, cs.force_165
        )
        .unwrap();
    }
    writeln!(out, "];").unwrap();

    writeln!(out, "pub const CLOSED_CLASSES: &[ClosedClassDef] = &[").unwrap();
    for cc in &rules.closed_class {
        let mut map_entries = String::new();
        for (k, v) in &cc.oblique_map {
            write!(
                map_entries,
                "ObliqueEntry {{ stem: {k:?}, forms: &{v:?} }}, "
            )
            .unwrap();
        }
        writeln!(
            out,
            "    ClosedClassDef {{ class_id: {:?}, sutra: {}, stems: &{:?}, oblique_map: &[{}], notes: {:?} }},",
            cc.class_id, cc.sutra, cc.stems, map_entries, cc.notes
        )
        .unwrap();
    }
    writeln!(out, "];").unwrap();

    writeln!(out, "pub const RULES: &[PunarchiRuleDef] = &[").unwrap();
    for r in &rules.rule {
        let subtype = match &r.subtype {
            Some(v) => format!("Some({v:?})"),
            None => "None".to_string(),
        };
        let lex = match &r.lexical_class {
            Some(v) => format!("Some({v:?})"),
            None => "None".to_string(),
        };
        writeln!(
            out,
            "    PunarchiRuleDef {{ id: {:?}, sutra: {}, chapter: {:?}, stage: {}, substage: {:?}, priority: {}, transform: {:?}, relation: {:?}, subtype: {}, lexical_class: {}, poetic: {}, optional: {}, reversible: {}, left_match: {:?}, right_match: {:?}, action: {:?}, flags: &{:?}, evidence_layer: {:?} }},",
            r.id, r.sutra, r.chapter, r.stage, r.substage, r.priority, r.transform, r.relation, subtype, lex, r.poetic, r.optional, r.reversible, r.left_match, r.right_match, r.action, r.flags, r.evidence_layer
        )
        .unwrap();
    }
    writeln!(out, "];").unwrap();

    let out_path = PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("punarchi_tables.rs");
    fs::write(out_path, out).expect("write generated punarchi_tables.rs");
}
