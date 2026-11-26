use tamil_punarchi::{
    punarchi_join, punarchi_split_candidates, ContextSubtype, GrammaticalRelation, LexicalClass,
    PunarchiContext, PunarchiProfile,
};

fn join_surf(first: &str, second: &str, ctx: &PunarchiContext) -> (String, Vec<String>) {
    let res = punarchi_join(first, second, ctx, PunarchiProfile::NannoolV1)
        .unwrap_or_else(|e| panic!("join failed for {first} + {second}: {e}"));
    let alts = res.alternatives.into_iter().map(|a| a.surface).collect();
    (res.surface, alts)
}

fn all_surfaces(first: &str, second: &str, ctx: &PunarchiContext) -> Vec<String> {
    let (primary, mut alts) = join_surf(first, second, ctx);
    let mut all = vec![primary];
    all.append(&mut alts);
    all
}

fn has_split(surface: &str, first: &str, second: &str) -> bool {
    let cands = punarchi_split_candidates(surface, PunarchiProfile::NannoolV1, false)
        .unwrap_or_else(|e| panic!("split failed for {surface}: {e}"));
    cands.iter().any(|c| c.first == first && c.second == second)
}

#[test]
fn edge_case_group_1_kurriyalugaram_vs_mutriyalugaram() {
    let unspec = PunarchiContext::default();
    let vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        ..Default::default()
    };
    let non_rat_vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        lexical_class: Some(LexicalClass::NonRationalNoun),
        ..Default::default()
    };
    let num_panpu = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        subtype: Some(ContextSubtype::Panputhogai),
        lexical_class: Some(LexicalClass::NumberWord),
        ..Default::default()
    };

    assert_eq!(join_surf("பசு", "இனம்", &unspec).0, "பசுவினம்");
    assert_eq!(join_surf("நாடு", "பற்று", &vetrumai).0, "நாட்டுப்பற்று");
    assert_eq!(join_surf("ஆறு", "நீர்", &vetrumai).0, "ஆற்றுநீர்");
    assert_eq!(join_surf("ஆறு", "நீர்", &non_rat_vetrumai).0, "ஆற்றுநீர்");
    assert_eq!(join_surf("ஆறு", "நீர்", &num_panpu).0, "அறுநீர்");

    let unspec_aaru = all_surfaces("ஆறு", "நீர்", &unspec);
    assert!(unspec_aaru.contains(&"ஆற்றுநீர்".to_owned()));
    assert!(unspec_aaru.contains(&"அறுநீர்".to_owned()));

    let (kat_p, kat_alts) = join_surf("கதவு", "ஓரம்", &unspec);
    assert_eq!(kat_p, "கதவுவோரம்");
    assert!(kat_alts.contains(&"கதவோரம்".to_owned()));
}

#[test]
fn edge_case_group_2_magara_eeru_and_sutra_220() {
    let unspec = PunarchiContext::default();
    let vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        ..Default::default()
    };
    let panpu = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        subtype: Some(ContextSubtype::Panputhogai),
        ..Default::default()
    };

    assert_eq!(join_surf("மரம்", "அடி", &vetrumai).0, "மரத்தடி");
    assert_eq!(join_surf("மரம்", "அடி", &unspec).0, "மரத்தடி");
    assert_eq!(join_surf("மரம்", "இலை", &vetrumai).0, "மரத்திலை");
    assert_eq!(join_surf("மரம்", "வேர்", &vetrumai).0, "மரவேர்");
    assert_eq!(join_surf("வட்டம்", "கல்", &panpu).0, "வட்டக்கல்");
    assert_eq!(join_surf("மரம்", "கள்", &unspec).0, "மரங்கள்");

    let (kulam_p, kulam_alts) = join_surf("குளம்", "கரை", &vetrumai);
    assert_eq!(kulam_p, "குளக்கரை");
    assert!(
        kulam_alts.contains(&"குளங்கரை".to_owned()),
        "missing Sutra 220 Vetrumai nasal alt: {kulam_alts:?}"
    );
    let nilam_all = all_surfaces("நிலம்", "கடந்தான்", &vetrumai);
    assert!(nilam_all.contains(&"நிலங்கடந்தான்".to_owned()));
}

#[test]
fn edge_case_group_3_and_4_assimilation_and_panpuppeyar() {
    let unspec = PunarchiContext::default();
    let vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        ..Default::default()
    };

    assert_eq!(join_surf("கல்", "தீது", &unspec).0, "கற்றீது");
    assert_eq!(join_surf("முள்", "தீது", &unspec).0, "முட்டீது");
    assert_eq!(join_surf("கல்", "நன்று", &unspec).0, "கன்னன்று");
    assert_eq!(join_surf("பொன்", "தகடு", &vetrumai).0, "பொற்றகடு");
    assert_eq!(join_surf("மண்", "பாண்டம்", &vetrumai).0, "மட்பாண்டம்");

    // Panpuppeyar stems must NOT leak Vetrumai Sutra 209 mutations:
    let than_all = all_surfaces("தண்மை", "தமிழ்", &unspec);
    assert_eq!(than_all[0], "தண்டமிழ்");
    assert!(!than_all.contains(&"தட்டமிழ்".to_owned()));
    let men_all = all_surfaces("மென்மை", "பூ", &unspec);
    assert_eq!(men_all[0], "மென்பூ");
    assert!(!men_all.contains(&"மெற்பூ".to_owned()));

    // Extended -மை cascades:
    assert_eq!(join_surf("பசுமை", "கூழ்", &unspec).0, "பைங்கூழ்");
    assert_eq!(join_surf("வெறுமை", "இலை", &unspec).0, "வெற்றிலை");
    assert_eq!(join_surf("செம்மை", "தமிழ்", &unspec).0, "செந்தமிழ்");
    assert_eq!(join_surf("பெருமை", "கடல்", &unspec).0, "பெருங்கடல்");
    assert_eq!(join_surf("செம்மை", "மலர்", &unspec).0, "செம்மலர்");
    assert_eq!(join_surf("வெம்மை", "மதி", &unspec).0, "வெம்மதி");
    assert_eq!(join_surf("செம்மை", "நீர்", &unspec).0, "செந்நீர்");
    assert_eq!(join_surf("முதுமை", "ஊர்", &unspec).0, "மூதூர்");
    assert_eq!(join_surf("புதுமை", "ஊர்", &unspec).0, "புத்தூர்");
    assert_eq!(join_surf("பழமை", "தமிழ்", &unspec).0, "பழந்தமிழ்");
    assert_eq!(join_surf("அருமை", "கடல்", &unspec).0, "அருங்கடல்");
    assert_eq!(join_surf("கடுமை", "சொல்", &unspec).0, "கடுஞ்சொல்");
    assert_eq!(join_surf("இளமை", "தமிழ்", &unspec).0, "இளந்தமிழ்");
    assert_eq!(join_surf("நன்மை", "தமிழ்", &unspec).0, "நற்றமிழ்");
    assert_eq!(join_surf("நன்மை", "குணம்", &unspec).0, "நற்குணம்");
    assert_eq!(join_surf("பெருமை", "ஊர்", &unspec).0, "பேரூர்");
}

#[test]
fn edge_case_group_5_poo_and_directions() {
    let unspec = PunarchiContext::default();
    let alvazhi = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        ..Default::default()
    };
    let vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        ..Default::default()
    };

    let (poo_p, poo_alts) = join_surf("பூ", "கொடி", &unspec);
    assert_eq!(poo_p, "பூங்கொடி");
    assert!(poo_alts.contains(&"பூக்கொடி".to_owned()));
    assert_eq!(join_surf("பூ", "சோலை", &unspec).0, "பூஞ்சோலை");

    // `கிழக்கு` (`கீழ்க்கடல்` / `கீழ்த்திசை`) vs lexical `கீழ்` (226):
    assert_eq!(join_surf("கிழக்கு", "கடல்", &unspec).0, "கீழ்க்கடல்");
    assert_eq!(join_surf("கிழக்கு", "திசை", &unspec).0, "கீழ்த்திசை");
    assert_eq!(join_surf("கீழ்", "குலம்", &vetrumai).0, "கீழ்குலம்");

    // `தெற்கு` & `மேற்கு`: no bogus `தெற்றிசை` / `மேஃறிசை`:
    assert_eq!(join_surf("தெற்கு", "நாடு", &unspec).0, "தென்னாடு");
    assert_eq!(join_surf("வடக்கு", "கிழக்கு", &unspec).0, "வடகிழக்கு");
    for ctx in [&unspec, &alvazhi, &vetrumai] {
        let therku_all = all_surfaces("தெற்கு", "திசை", ctx);
        assert_eq!(therku_all[0], "தென்றிசை");
        assert!(!therku_all.contains(&"தெற்றிசை".to_owned()));

        let merku_all = all_surfaces("மேற்கு", "திசை", ctx);
        assert_eq!(merku_all, vec!["மேற்றிசை".to_owned()]);
    }
}

#[test]
fn edge_case_group_6_numeral_compounds() {
    let unspec = PunarchiContext::default();
    let vetrumai = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        ..Default::default()
    };
    let distrib = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        subtype: Some(ContextSubtype::Distributive),
        ..Default::default()
    };
    let panpu = PunarchiContext {
        relation: GrammaticalRelation::Alvazhi,
        subtype: Some(ContextSubtype::Panputhogai),
        ..Default::default()
    };

    assert_eq!(join_surf("ஒன்று", "ஒன்று", &distrib).0, "ஒவ்வொன்று");
    assert!(all_surfaces("ஒன்று", "ஒன்று", &unspec).contains(&"ஒவ்வொன்று".to_owned()));
    assert_eq!(join_surf("மூன்று", "பத்து", &unspec).0, "முப்பது");
    assert_eq!(join_surf("நான்கு", "அடி", &unspec).0, "நாலடி");
    assert_eq!(join_surf("நான்கு", "நாழி", &unspec).0, "நானாழி");
    assert_eq!(join_surf("பத்து", "இரண்டு", &unspec).0, "பன்னிரண்டு");
    assert_eq!(join_surf("ஒன்பது", "பத்து", &unspec).0, "தொண்ணூறு");
    assert_eq!(join_surf("ஒன்பது", "நூறு", &unspec).0, "தொள்ளாயிரம்");

    // Viruttiyurai fn. 191 fixes:
    let (p19, p19_alts) = join_surf("பத்து", "ஒன்பது", &unspec);
    assert_eq!(p19, "பத்தொன்பது");
    assert!(!p19_alts.contains(&"பதினொன்பது".to_owned()));
    assert_eq!(join_surf("பத்து", "ஒன்பது", &panpu).0, "பதிற்றொன்பது");

    let onp_one = all_surfaces("ஒன்பது", "ஒன்று", &unspec);
    assert_eq!(onp_one[0], "ஒன்பதிற்றொன்று");
    assert!(!onp_one.contains(&"ஒன்பதினொன்று".to_owned()));
    assert!(!all_surfaces("ஒன்பது", "இரண்டு", &unspec).contains(&"ஒன்பதினிரண்டு".to_owned()));
    assert!(!all_surfaces("ஒன்பது", "ஒன்பது", &distrib).contains(&"ஒன்பதினொன்பது".to_owned()));
    assert_eq!(join_surf("ஒன்பது", "ஆயிரம்", &unspec).0, "ஒன்பதினாயிரம்");

    // `ஏழு` + vowel & `எட்டு`/`பதின்`/`ஒன்பதின்` block Sutra 209:
    assert_eq!(join_surf("ஏழு", "அடி", &unspec).0, "ஏழடி");
    assert_eq!(join_surf("ஏழு", "ஆயிரம்", &unspec).0, "ஏழாயிரம்");
    assert_eq!(join_surf("எட்டு", "கால்", &vetrumai).0, "எண்கால்");
    assert_eq!(join_surf("எட்டு", "கலம்", &vetrumai).0, "எண்கலம்");
    assert_eq!(join_surf("பத்து", "கலம்", &vetrumai).0, "பதின்கலம்");
    assert_eq!(join_surf("ஒன்பது", "கலம்", &vetrumai).0, "ஒன்பதின்கலம்");
}

#[test]
fn edge_case_group_7_reverse_split_regressions() {
    assert!(has_split("ஆற்றுநீர்", "ஆறு", "நீர்"));
    assert!(has_split("மரத்தடி", "மரம்", "அடி"));
    assert!(has_split("மரத்திலை", "மரம்", "இலை"));
    assert!(has_split("பத்தொன்பது", "பத்து", "ஒன்பது"));
    assert!(has_split("நாலடி", "நான்கு", "அடி"));
    assert!(has_split("நானாழி", "நான்கு", "நாழி"));
    assert!(has_split("கீழ்க்கடல்", "கிழக்கு", "கடல்"));
    assert!(has_split("தென்னாடு", "தெற்கு", "நாடு"));
    assert!(has_split("தென்றிசை", "தெற்கு", "திசை"));
    assert!(has_split("ஏழாயிரம்", "ஏழு", "ஆயிரம்"));
    assert!(has_split("மூதூர்", "முதுமை", "ஊர்"));
    assert!(has_split("செம்மலர்", "செம்மை", "மலர்"));
    assert!(has_split("செந்நீர்", "செம்மை", "நீர்"));
    assert!(has_split("பழந்தமிழ்", "பழமை", "தமிழ்"));
    assert!(has_split("அருங்கடல்", "அருமை", "கடல்"));
    assert!(has_split("தண்டமிழ்", "தண்மை", "தமிழ்"));
    assert!(has_split("நற்றமிழ்", "நன்மை", "தமிழ்"));
    assert!(has_split("பேரூர்", "பெருமை", "ஊர்"));

    for surf in ["கற்றீது", "தொண்ணூறு", "பன்னிரண்டு", "கிளியழகு", "நாகரிது"]
    {
        let cands = punarchi_split_candidates(surf, PunarchiProfile::NannoolV1, false).unwrap();
        assert!(
            !cands.iter().any(|c| c.second == "உ"),
            "spurious (surface, உ) split returned for {surf}: {cands:?}"
        );
    }
}
