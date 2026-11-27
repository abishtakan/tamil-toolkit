//! Unit and property tests for `tamil-lexicon` (`TMLPACK2`, `PackRegistry`, and `LexiconStore`).
#![forbid(unsafe_code)]

use proptest::prelude::*;
use tamil_lexicon::{
    build_compact_pack, pack_category, CompactEntry, CompactForm, CompactPackInput,
    CompactPackView, CompactRelation, CompactSense, LexiconCategory, LexiconProfile, LexiconStore,
    LookupStatus, PackRegistry, PackTier, PrefixSearchOptions, QueryScope, TierFilter,
    CHECKSUM_OFFSET_V2, HEADER_SIZE_V2,
};

fn sample_open_input() -> CompactPackInput {
    CompactPackInput {
        pack_id: "core_test".to_owned(),
        pack_tier: PackTier::VerifiedOpen,
        rights_status: "CC-BY-SA-4.0".to_owned(),
        license: "CC-BY-SA-4.0".to_owned(),
        dataset_version: "0.2.0".to_owned(),
        description: "Test verified open pack".to_owned(),
        source_ids: vec!["enwiktionary".to_owned()],
        attribution_notice: "CC-BY-SA-4.0 Wiktionary contributors".to_owned(),
        entries: vec![
            CompactEntry {
                entry_id: "open_001".to_owned(),
                headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}".to_owned(), // தமிழ்
                pos: Some("NOUN".to_owned()),
                forms: vec![],
                senses: vec![CompactSense {
                    gloss_ta: Some(
                        "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD} \u{0BAE}\u{0BCA}\u{0BB4}\u{0BBF}"
                            .to_owned(),
                    ),
                    gloss_en: Some("Tamil language".to_owned()),
                    ..Default::default()
                }],
                domain: Some("linguistics".to_owned()),
                region: None,
                register: Some("standard".to_owned()),
                origin_language: None,
                pure_tamil_equivalent: None,
                standard_equivalent: None,
                scientific_name: None,
                literary_source: None,
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:oldid=1".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                permalink: Some("https://en.wiktionary.org/w/index.php?oldid=1".to_owned()),
                ..Default::default()
            },
            CompactEntry {
                entry_id: "open_002".to_owned(),
                headword: "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}".to_owned(), // நன்றி
                pos: Some("NOUN".to_owned()),
                senses: vec![CompactSense {
                    gloss_en: Some("gratitude".to_owned()),
                    ..Default::default()
                }],
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:oldid=2".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            },
            CompactEntry {
                entry_id: "open_003".to_owned(),
                headword: "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}".to_owned(), // நன்றி (homograph)
                pos: Some("INTJ".to_owned()),
                senses: vec![CompactSense {
                    gloss_en: Some("thank you".to_owned()),
                    ..Default::default()
                }],
                source_id: "enwiktionary".to_owned(),
                source_locator: "enwiktionary:oldid=2".to_owned(),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            },
        ],
        relations: vec![],
        build_folded_index: true,
    }
}

fn sample_local_input() -> CompactPackInput {
    CompactPackInput {
        pack_id: "local_term_test".to_owned(),
        pack_tier: PackTier::LocalHistorical,
        rights_status: "unresolved".to_owned(),
        license: "UNRESOLVED_LOCAL_ONLY".to_owned(),
        dataset_version: "0.2.0".to_owned(),
        description: "Test local terminology pack".to_owned(),
        source_ids: vec!["TVA_KALAICHOL".to_owned()],
        attribution_notice: "Owner-supplied local archive".to_owned(),
        entries: vec![CompactEntry {
            entry_id: "lterm_001".to_owned(),
            headword: "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD} \u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}".to_owned(), // அக்குள் கோடு
            pos: None,
            forms: vec![CompactForm {
                role: "variant".to_owned(),
                text: "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD}\u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}".to_owned(), // அக்குள்கோடு
            }],
            senses: vec![CompactSense {
                gloss_en: Some("mid axillary line".to_owned()),
                domain: Some("Anatomy".to_owned()),
                ..Default::default()
            }],
            domain: Some("Anatomy".to_owned()),
            region: None,
            register: None,
            origin_language: None,
            pure_tamil_equivalent: None,
            standard_equivalent: None,
            scientific_name: None,
            literary_source: None,
            source_id: "TVA_KALAICHOL".to_owned(),
            source_locator: "secondary_specialized_technical_terms.csv:1".to_owned(),
            rights_status: "unresolved".to_owned(),
            ..Default::default()
        }],
        relations: vec![CompactRelation {
            source_headword: "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}".to_owned(),
            target_headword:
                "\u{0B9A}\u{0BC6}\u{0BA8}\u{0BCD}\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
                    .to_owned(),
            relation_code: "RELATED".to_owned(),
            directionality: "symmetric".to_owned(),
            source_id: "primary_relationships.csv".to_owned(),
            source_locator: "primary_relationships.csv:1".to_owned(),
        }],
        build_folded_index: true,
    }
}

#[test]
fn tmlpack2_is_deterministic_and_roundtrips_homographs_variants_folded_and_relations() {
    let bytes_a = build_compact_pack(&sample_open_input()).expect("build open A");
    let bytes_b = build_compact_pack(&sample_open_input()).expect("build open B");
    assert_eq!(bytes_a, bytes_b, "TMLPACK2 build must be byte-identical");

    let local_bytes = build_compact_pack(&sample_local_input()).expect("build local");

    let mut reg = PackRegistry::new();
    let s1 = reg.load_pack_bytes(bytes_a).expect("load open");
    let s2 = reg.load_pack_bytes(local_bytes).expect("load local");
    assert_eq!(s1.pack_tier, PackTier::VerifiedOpen);
    assert_eq!(s2.pack_tier, PackTier::LocalHistorical);
    assert!(s1.has_folded_index);
    assert!(s2.has_relations);

    // Homographs preserved
    let res = reg
        .lookup_compact(
            "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
            &QueryScope::default(),
        )
        .expect("lookup nanri");
    assert_eq!(res.status, LookupStatus::Matched);
    assert_eq!(res.total_entries, 2);

    // POS filter & LexiconStore::has_word_with_pos
    assert!(reg.has_word_with_pos(
        "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
        "INTJ",
        &QueryScope::default()
    ));
    assert!(!reg.has_word_with_pos(
        "\u{0BA8}\u{0BA9}\u{0BCD}\u{0BB1}\u{0BBF}",
        "VERB",
        &QueryScope::default()
    ));

    // Variant form lookup (spaceless Sorkuvai variant resolves to canonical TVA entry)
    let var_res = reg
        .lookup_compact(
            "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD}\u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}",
            &QueryScope::default(),
        )
        .expect("lookup variant");
    assert_eq!(var_res.total_entries, 1);
    assert_eq!(
        var_res.entries[0].entry.headword,
        "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD} \u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}"
    );

    // Tier isolation: Open-only excludes local_historical pack
    let open_only = QueryScope {
        tier: TierFilter::Open,
        ..Default::default()
    };
    assert!(!reg.contains_word(
        "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD} \u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}",
        &open_only
    ));
    assert!(reg.contains_word("\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}", &open_only));

    // Mayangoli-folded lookup: "தமில்" (ல instead of ழ) finds "தமிழ்"!
    let folded_scope = QueryScope {
        folded: true,
        ..Default::default()
    };
    let folded_res = reg
        .lookup_compact("\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB2}\u{0BCD}", &folded_scope)
        .expect("folded lookup");
    assert_eq!(folded_res.total_entries, 1);
    assert_eq!(
        folded_res.entries[0].entry.headword,
        "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    );

    // Prefix search
    let pfx = reg
        .prefix_search(
            "\u{0BA4}\u{0BAE}",
            &PrefixSearchOptions {
                limit: 10,
                after_key: None,
                scope: QueryScope::default(),
            },
        )
        .expect("prefix search");
    assert_eq!(pfx.hits.len(), 1);
    assert_eq!(
        pfx.hits[0].headword,
        "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"
    );

    // Longest-prefix stemmer probe (Rank 3-4 primitive)
    let stems = reg
        .longest_prefix_matches(
            "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}\u{0BA8}\u{0BBE}\u{0B9F}\u{0BC1}",
            &QueryScope::default(),
        )
        .expect("stems");
    assert_eq!(stems, vec!["\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"]);

    // Bounded Damerau-Levenshtein fuzzy search (Rank 3-4 primitive: தமில் -> தமிழ்)
    let fuzzy = reg
        .fuzzy_search(
            "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB2}\u{0BCD}",
            1,
            &PrefixSearchOptions::default(),
        )
        .expect("fuzzy search");
    assert!(fuzzy
        .hits
        .iter()
        .any(|h| h.headword == "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}" && h.distance == 1));

    // Relations lookup
    let rels = reg
        .lookup_relations(
            "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}",
            &QueryScope::default(),
        )
        .expect("relations");
    assert_eq!(rels.status, LookupStatus::Matched);
    assert_eq!(rels.relations.len(), 1);
    assert_eq!(rels.relations[0].relation_code, "RELATED");

    // Category mapping & category-filtered lookup
    assert_eq!(s1.category, LexiconCategory::Dictionary);
    assert_eq!(s2.category, LexiconCategory::Terminology);
    assert_eq!(pack_category("local_phrases"), LexiconCategory::Phrases);
    assert_eq!(pack_category("regional"), LexiconCategory::Regional);
    assert_eq!(pack_category("names_taxa"), LexiconCategory::NamesTaxa);
    assert_eq!(pack_category("local_literary"), LexiconCategory::Heritage);
    assert_eq!(pack_category("local_relations"), LexiconCategory::Relations);
    assert!(LexiconProfile::OpenLite.includes_pack_stem("core", false));
    assert!(!LexiconProfile::OpenLite.includes_pack_stem("ta_wiktionary", false));
    assert!(LexiconProfile::Open.includes_pack_stem("ta_wiktionary", false));
    assert!(!LexiconProfile::Open.includes_pack_stem("local_core", true));
    assert!(LexiconProfile::Local.includes_pack_stem("local_core", true));
    assert!(LexiconProfile::Full.includes_pack_stem("local_core", true));

    let term_only = QueryScope {
        category: Some(LexiconCategory::Terminology),
        ..Default::default()
    };
    assert!(!reg.contains_word("\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}", &term_only));
    assert!(reg.contains_word(
        "\u{0B85}\u{0B95}\u{0BCD}\u{0B95}\u{0BC1}\u{0BB3}\u{0BCD} \u{0B95}\u{0BCB}\u{0B9F}\u{0BC1}",
        &term_only
    ));

    // Unified WordDefinition merges meanings + relations + provenance (including local_relations!)
    let def = reg
        .define(
            "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}",
            &QueryScope::default(),
        )
        .expect("define tamil");
    assert_eq!(def.status, LookupStatus::Matched);
    assert_eq!(def.headword, "\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}");
    assert!(def.has_verified_open);
    assert!(
        def.has_local_historical,
        "local_relations provenance must be recorded"
    );
    assert_eq!(def.categories, vec![LexiconCategory::Dictionary]);
    assert_eq!(def.meanings_en.len(), 1);
    assert_eq!(def.meanings_en[0].text, "Tamil language");
    assert_eq!(def.meanings_ta.len(), 1);
    assert_eq!(
        def.relations.related,
        vec!["\u{0B9A}\u{0BC6}\u{0BA8}\u{0BCD}\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}"]
    );
    assert_eq!(def.sources.len(), 2);

    // Category filter on define() must NOT leak relations when category has zero entry matches (H2)
    let def_term_miss = reg
        .define("\u{0BA4}\u{0BAE}\u{0BBF}\u{0BB4}\u{0BCD}", &term_only)
        .expect("define tamil in terminology");
    assert_eq!(def_term_miss.status, LookupStatus::NotFound);
    assert_eq!(def_term_miss.entry_count, 0);
    assert!(def_term_miss.relations.related.is_empty());
}

#[test]
fn tmlpack2_rejects_corrupted_bytes_and_bad_checksum() {
    let original = build_compact_pack(&sample_open_input()).expect("build");
    assert!(original.len() > HEADER_SIZE_V2);

    // Corrupt payload byte
    let mut bad_payload = original.clone();
    let last = bad_payload.len() - 1;
    bad_payload[last] ^= 0xFF;
    assert!(CompactPackView::parse(bad_payload).is_err());

    // Corrupt checksum byte
    let mut bad_chk = original.clone();
    bad_chk[CHECKSUM_OFFSET_V2] ^= 0x01;
    assert!(CompactPackView::parse(bad_chk).is_err());

    // Corrupt magic
    let mut bad_magic = original;
    bad_magic[7] = b'9';
    assert!(CompactPackView::parse(bad_magic).is_err());
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(256))]
    #[test]
    fn prop_tmlpack2_arbitrary_tamil_headwords_roundtrip_nfc(
        words in prop::collection::vec("[\u{0B85}-\u{0BB9}][\u{0BBE}-\u{0BCD}]{0,2}", 1..12)
    ) {
        let entries: Vec<CompactEntry> = words
            .iter()
            .enumerate()
            .map(|(i, w)| CompactEntry {
                entry_id: format!("p_{i:04}"),
                headword: w.clone(),
                pos: Some("NOUN".to_owned()),
                forms: vec![],
                senses: vec![],
                domain: None,
                region: None,
                register: None,
                origin_language: None,
                pure_tamil_equivalent: None,
                standard_equivalent: None,
                scientific_name: None,
                literary_source: None,
                source_id: "prop".to_owned(),
                source_locator: format!("prop:{i}"),
                rights_status: "CC-BY-SA-4.0".to_owned(),
                ..Default::default()
            })
            .collect();
        let bytes = build_compact_pack(&CompactPackInput {
            pack_id: "prop_pack".to_owned(),
            pack_tier: PackTier::VerifiedOpen,
            rights_status: "CC-BY-SA-4.0".to_owned(),
            license: "CC-BY-SA-4.0".to_owned(),
            dataset_version: "0.2.0".to_owned(),
            description: "prop".to_owned(),
            source_ids: vec!["prop".to_owned()],
            attribution_notice: "prop".to_owned(),
            entries,
            relations: vec![],
            build_folded_index: true,
        }).expect("build prop pack");
        let view = CompactPackView::parse(bytes).expect("parse prop pack");
        for w in &words {
            let nfc = tamil_norm::normalize_nfc(w);
            prop_assert!(view.contains_exact(&nfc));
            let found = view.lookup_exact(w).expect("lookup");
            prop_assert!(!found.is_empty());
        }
    }
}
