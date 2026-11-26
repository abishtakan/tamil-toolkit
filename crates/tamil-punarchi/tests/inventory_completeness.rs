use tamil_punarchi::{
    punarchi_join, punarchi_rules, punarchi_rules_filtered, tables, ContextSubtype,
    GrammaticalRelation, LexicalClass, PunarchiChapter, PunarchiContext, PunarchiError,
    PunarchiProfile,
};

#[test]
fn inventory_covers_all_117_sutras_exactly() {
    let rules = punarchi_rules(PunarchiProfile::NannoolV1);
    assert_eq!(rules.len(), 117);

    let mut expected_sutras = vec![93_u16, 94];
    expected_sutras.extend(102_u16..=108);
    expected_sutras.push(136);
    expected_sutras.extend(151_u16..=257);
    assert_eq!(expected_sutras.len(), 117);

    let actual_sutras: Vec<u16> = rules.iter().map(|entry| entry.sutra).collect();
    assert_eq!(actual_sutras, expected_sutras);

    for pair in actual_sutras.windows(2) {
        assert!(
            pair[0] < pair[1],
            "sutra numbers must be strictly ascending"
        );
    }

    let chapter_counts = [
        (PunarchiChapter::Ezhuttiyal, 9_usize),
        (PunarchiChapter::Padaviyal, 1_usize),
        (PunarchiChapter::Uyireeru, 53_usize),
        (PunarchiChapter::Meyyeeru, 36_usize),
        (PunarchiChapter::Urupu, 18_usize),
    ];
    let mut total_by_chapter = 0_usize;
    for (chapter, expected_count) in chapter_counts {
        let filtered = punarchi_rules_filtered(PunarchiProfile::NannoolV1, Some(chapter), None)
            .expect("valid chapter filter must succeed");
        assert_eq!(
            filtered.len(),
            expected_count,
            "unexpected sutra count for chapter {}",
            chapter.as_str()
        );
        total_by_chapter += filtered.len();
    }
    assert_eq!(total_by_chapter, 117);

    let expected_non_exec = [151_u16, 152, 153, 154, 155, 156, 157, 239, 240, 241, 253];
    let actual_non_exec: Vec<u16> = rules
        .iter()
        .filter(|entry| !entry.executable)
        .map(|entry| entry.sutra)
        .collect();
    assert_eq!(actual_non_exec, expected_non_exec);
    assert_eq!(rules.iter().filter(|entry| entry.executable).count(), 106);
    for entry in rules.iter().filter(|entry| !entry.executable) {
        assert_eq!(
            entry.tier, "definition_or_scope",
            "non-executable sutra {} must be tier definition_or_scope",
            entry.sutra
        );
    }

    for entry in rules {
        assert!(
            (166_u16..=303).contains(&entry.tva_page),
            "sutra {} tva_page {} out of 166..=303",
            entry.sutra,
            entry.tva_page
        );
        assert_eq!(
            entry.kandigai_sutra, entry.sutra,
            "sutra {} kandigai_sutra mismatch",
            entry.sutra
        );
    }
}

#[test]
fn edition_notes_cover_all_12_verified_discrepancies() {
    let discrepancy_sutras = [
        104_u16, 105, 106, 179, 180, 195, 206, 225, 241, 242, 244, 245, 247, 250, 255,
    ];
    for sutra in discrepancy_sutras {
        let entry = tables::inventory_entry(sutra)
            .unwrap_or_else(|| panic!("missing inventory entry for sutra {sutra}"));
        assert!(
            entry
                .edition_note
                .is_some_and(|note| !note.trim().is_empty()),
            "expected non-empty edition_note for sutra {sutra}"
        );
    }
}

#[test]
fn forward_rule_to_inventory_integrity() {
    for rule in tables::RULES {
        let entry = tables::inventory_entry(rule.sutra)
            .unwrap_or_else(|| panic!("rule {} references unknown sutra {}", rule.id, rule.sutra));
        assert!(
            entry.executable || rule.sutra == 153,
            "rule {} links to non-executable sutra {}",
            rule.id,
            rule.sutra
        );
        assert_eq!(
            rule.chapter, entry.chapter,
            "rule {} chapter {} does not match inventory chapter {}",
            rule.id, rule.chapter, entry.chapter
        );
    }

    assert_eq!(tables::CHARIYAIS.len(), 17);
    assert!(tables::CASE_SUFFIXES.len() >= 6);
    let ku_suffix = tables::case_suffix_info("கு").expect("கு case suffix must exist");
    assert!(
        ku_suffix.force_165,
        "கு case suffix must set force_165 = true"
    );

    // Strict reverse coverage: every executable sutra in the 117-sutra inventory maps to >= 1 rule.
    let mut unmapped: Vec<u16> = Vec::new();
    for entry in punarchi_rules(PunarchiProfile::NannoolV1) {
        if entry.executable && !tables::RULES.iter().any(|r| r.sutra == entry.sutra) {
            unmapped.push(entry.sutra);
        }
    }
    assert!(
        unmapped.is_empty(),
        "executable sutras missing from punarchi-nannool.toml: {unmapped:?}"
    );
}

#[test]
fn all_13_contract_error_messages_match_spec() {
    let expected = [
        (
            PunarchiError::ExpectedInputObject,
            "expected punarchi input object",
        ),
        (
            PunarchiError::ExpectedStringInput,
            "expected a string input",
        ),
        (
            PunarchiError::EmptyInput,
            "punarchi: input components must not be empty",
        ),
        (
            PunarchiError::SurfaceTooLong,
            "punarchi: surface input exceeds maximum length",
        ),
        (
            PunarchiError::ExpectedProfileString,
            "expected profile to be a string",
        ),
        (
            PunarchiError::UnsupportedProfile,
            "unsupported punarchi profile",
        ),
        (
            PunarchiError::ExpectedContextObject,
            "expected punarchi context object",
        ),
        (
            PunarchiError::UnsupportedRelation,
            "unsupported punarchi relation",
        ),
        (
            PunarchiError::UnsupportedOrIncompatibleSubtype,
            "unsupported or incompatible punarchi subtype",
        ),
        (
            PunarchiError::UnsupportedLexicalClass,
            "unsupported punarchi lexical class",
        ),
        (
            PunarchiError::ExpectedPoeticBoolean,
            "expected poetic to be a boolean",
        ),
        (
            PunarchiError::UnsupportedChapter,
            "unsupported punarchi chapter",
        ),
        (
            PunarchiError::SutraOutOfRange,
            "punarchi sutra out of range",
        ),
    ];

    assert_eq!(expected.len(), 13);
    for (err, msg) in expected {
        assert_eq!(err.as_str(), msg);
        assert_eq!(err.to_string(), msg);
    }

    assert_eq!(
        PunarchiProfile::parse("tolkappiyam-v1"),
        Err(PunarchiError::UnsupportedProfile)
    );
    assert_eq!(
        PunarchiChapter::parse("unknown"),
        Err(PunarchiError::UnsupportedChapter)
    );
    assert_eq!(
        GrammaticalRelation::parse("bad"),
        Err(PunarchiError::UnsupportedRelation)
    );
    assert_eq!(
        ContextSubtype::parse("bad"),
        Err(PunarchiError::UnsupportedOrIncompatibleSubtype)
    );
    assert_eq!(
        LexicalClass::parse("bad"),
        Err(PunarchiError::UnsupportedLexicalClass)
    );

    let bad_vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        subtype: Some(ContextSubtype::Vinaithogai),
        ..Default::default()
    };
    assert_eq!(
        bad_vetrumai.validate(),
        Err(PunarchiError::UnsupportedOrIncompatibleSubtype)
    );

    let bad_alvazhi = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        subtype: Some(ContextSubtype::Case2),
        ..Default::default()
    };
    assert_eq!(
        bad_alvazhi.validate(),
        Err(PunarchiError::UnsupportedOrIncompatibleSubtype)
    );

    assert_eq!(
        punarchi_rules_filtered(PunarchiProfile::NannoolV1, None, Some(999)),
        Err(PunarchiError::SutraOutOfRange)
    );

    assert_eq!(
        punarchi_join(
            "",
            "அடி",
            &PunarchiContext::default(),
            PunarchiProfile::NannoolV1
        ),
        Err(PunarchiError::EmptyInput)
    );
    assert_eq!(
        punarchi_join(
            "   ",
            "அடி",
            &PunarchiContext::default(),
            PunarchiProfile::NannoolV1
        ),
        Err(PunarchiError::EmptyInput)
    );
}

#[test]
fn golden_rule_ids_exist_in_compiled_toml_rules() {
    use std::collections::HashSet;
    let valid_ids: HashSet<&str> = tables::RULES.iter().map(|r| r.id).collect();
    let golden_path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../tests/golden/punarchi_nannool.jsonl");
    let raw = std::fs::read_to_string(&golden_path)
        .unwrap_or_else(|e| panic!("failed to read {}: {e}", golden_path.display()));

    let mut missing: Vec<(String, String)> = Vec::new();
    for line in raw.lines().filter(|l| !l.trim().is_empty()) {
        let row: serde_json::Value = serde_json::from_str(line).expect("valid golden json");
        let vid = row["id"].as_str().unwrap_or("<unknown>").to_owned();
        if let Some(expected) = row.get("expected") {
            let mut check_rid = |rid: &str| {
                if !valid_ids.contains(rid) {
                    missing.push((vid.clone(), rid.to_owned()));
                }
            };
            if let Some(obj) = expected.as_object() {
                if let Some(arr) = obj.get("steps").and_then(|v| v.as_array()) {
                    for st in arr {
                        if let Some(rid) = st.get("rule_id").and_then(|v| v.as_str()) {
                            check_rid(rid);
                        }
                    }
                }
                if let Some(alts) = obj.get("alternatives").and_then(|v| v.as_array()) {
                    for alt in alts {
                        if let Some(arr) = alt.get("steps").and_then(|v| v.as_array()) {
                            for st in arr {
                                if let Some(rid) = st.get("rule_id").and_then(|v| v.as_str()) {
                                    check_rid(rid);
                                }
                            }
                        }
                    }
                }
            } else if let Some(arr) = expected.as_array() {
                for item in arr {
                    if let Some(rid) = item.get("rule_id").and_then(|v| v.as_str()) {
                        check_rid(rid);
                    }
                    if let Some(steps) = item.get("steps").and_then(|v| v.as_array()) {
                        for st in steps {
                            if let Some(rid) = st.get("rule_id").and_then(|v| v.as_str()) {
                                check_rid(rid);
                            }
                        }
                    }
                }
            }
        }
    }

    assert!(
        missing.is_empty(),
        "golden vectors reference rule_id(s) absent from lexicon/punarchi-nannool.toml: {missing:?}"
    );
}
