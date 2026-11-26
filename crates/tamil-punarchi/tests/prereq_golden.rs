mod support;

use serde_json::Value;
use tamil_core::compose_uyirmei;
use tamil_punarchi::{
    classify_ugaram, is_kurriyaligaram_context, is_thanikkuril_otru, is_valid_mozhi_eetru,
    is_valid_mozhi_muthal, punarchi_join, punarchi_rules_filtered, ContextSubtype,
    GrammaticalRelation, LexicalClass, PunarchiChapter, PunarchiContext, PunarchiError,
    PunarchiProfile, UgaramClass, MAX_SPLIT_SURFACE_BYTES,
};

#[test]
fn sutra_94_six_kurriyalugaram_classes_vs_mutriyalugaram() {
    for word in ["நாகு", "காசு", "நீறு"] {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::NedilThodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in ["எஃகு", "கஃசு", "இருபஃது"] {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::AythathThodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in ["வரகு", "பலாசு", "போவது", "ஒன்பது", "இறும்பூது", "கயிறு"]
    {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::UyirThodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in ["கொக்கு", "பிண்ணாக்கு", "விளையாட்டு", "கச்சு", "பற்று", "குருத்து"]
    {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::Vanthodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in [
        "குரங்கு",
        "பட்டாங்கு",
        "சுண்ணாம்பு",
        "சங்கு",
        "பஞ்சு",
        "அம்பு",
        "கன்று",
    ] {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::Menthodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in ["அல்கு", "வெய்து", "சால்பு", "தெள்கு"]
    {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::Idaithodar, "{word}");
        assert!(cls.is_kurriyalugaram(), "{word}");
    }

    for word in [
        "பசு",
        "புது",
        "அது",
        "இது",
        "உது",
        "எது",
        "தெரு",
        "கடு",
        "நடு",
        "வடு",
        "உ",
        "கு",
    ] {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::Mutriyalugaram, "{word}");
        assert!(!cls.is_kurriyalugaram(), "{word}");
    }

    for word in ["மரம்", "பூ", "மணி", "கல்"] {
        let cls = classify_ugaram(word);
        assert_eq!(cls, UgaramClass::NonU, "{word}");
        assert!(!cls.is_kurriyalugaram(), "{word}");
    }
}

#[test]
fn sutra_93_kurriyaligaram_detection() {
    for word in ["நாகு", "எஃகு", "வரகு", "கொக்கு", "குரங்கு", "அல்கு", "தெள்கு"]
    {
        assert!(
            is_kurriyaligaram_context(word, "யாது"),
            "{word} + யாது should trigger Kurriyaligaram"
        );
    }

    assert!(!is_kurriyaligaram_context("பசு", "யாது"));
    assert!(!is_kurriyaligaram_context("அது", "யாது"));

    assert!(is_kurriyaligaram_context("கேள்", "மியா"));
    assert!(is_kurriyaligaram_context("செல்", "மியா"));
}

#[test]
fn sutras_102_to_106_mozhi_muthal() {
    let all_vowels = ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ"];
    for vowel in all_vowels {
        assert!(is_valid_mozhi_muthal(vowel, None), "vowel {vowel}");
    }

    for mei in ["க்", "ச்", "த்", "ந்", "ப்", "ம்"] {
        for vowel in all_vowels {
            let unit = compose_uyirmei(mei, vowel).expect("valid uyirmei");
            assert!(is_valid_mozhi_muthal(&unit, None), "unrestricted {unit}");
        }
    }

    for allowed in ["வ", "வா", "வி", "வீ", "வெ", "வே", "வை", "வௌ"] {
        assert!(is_valid_mozhi_muthal(allowed, None), "allowed {allowed}");
    }
    for disallowed in ["வு", "வூ", "வொ", "வோ"] {
        assert!(
            !is_valid_mozhi_muthal(disallowed, None),
            "disallowed {disallowed}"
        );
    }

    for allowed in ["ய", "யா", "யு", "யூ", "யோ", "யௌ"] {
        assert!(is_valid_mozhi_muthal(allowed, None), "allowed {allowed}");
    }
    for disallowed in ["யி", "யீ", "யெ", "யே", "யை", "யொ"] {
        assert!(
            !is_valid_mozhi_muthal(disallowed, None),
            "disallowed {disallowed}"
        );
    }

    for allowed in ["ஞ", "ஞா", "ஞெ", "ஞொ"] {
        assert!(is_valid_mozhi_muthal(allowed, None), "allowed {allowed}");
    }
    for disallowed in ["ஞி", "ஞீ", "ஞு", "ஞூ", "ஞே", "ஞை", "ஞோ", "ஞௌ"]
    {
        assert!(
            !is_valid_mozhi_muthal(disallowed, None),
            "disallowed {disallowed}"
        );
    }

    for trigger in ["அ", "இ", "உ", "யா", "எ"] {
        assert!(
            is_valid_mozhi_muthal("ஙனம்", Some(trigger)),
            "ஙனம் after {trigger}"
        );
    }
    assert!(!is_valid_mozhi_muthal("ஙனம்", None));
    assert!(!is_valid_mozhi_muthal("ஙனம்", Some("கல்")));

    for disallowed_mei in ["ட்", "ண்", "ர்", "ல்", "ழ்", "ள்", "ற்", "ன்"]
    {
        let unit = compose_uyirmei(disallowed_mei, "அ").expect("valid uyirmei");
        assert!(!is_valid_mozhi_muthal(&unit, None), "disallowed {unit}");
    }
    for pure_mei in ["க்", "ச்", "ம்", "ல்", "ஃ"] {
        assert!(
            !is_valid_mozhi_muthal(pure_mei, None),
            "disallowed {pure_mei}"
        );
    }
}

#[test]
fn sutras_107_to_108_mozhi_eetru() {
    let all_vowels = ["அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ"];
    for vowel in all_vowels {
        assert!(is_valid_mozhi_eetru(vowel), "standalone vowel {vowel}");
    }

    for word in [
        "உரிஞ்",
        "மண்",
        "பொருந்",
        "மரம்",
        "பொன்",
        "வேய்",
        "வேர்",
        "வேல்",
        "தெவ்",
        "வீழ்",
        "வாள்",
    ] {
        assert!(is_valid_mozhi_eetru(word), "legal eetru {word}");
    }

    for disallowed in ["ங்", "க்", "ச்", "ட்", "த்", "ப்", "ற்", "ஃ"]
    {
        assert!(
            !is_valid_mozhi_eetru(disallowed),
            "disallowed eetru {disallowed}"
        );
    }

    for disallowed in ["கெ", "செ", "தெ"] {
        assert!(
            !is_valid_mozhi_eetru(disallowed),
            "disallowed C+எ {disallowed}"
        );
    }

    assert!(is_valid_mozhi_eetru("நொ"));
    for disallowed in ["கொ", "சொ"] {
        assert!(
            !is_valid_mozhi_eetru(disallowed),
            "disallowed C+ஒ {disallowed}"
        );
    }

    for allowed in ["கௌ", "வௌ"] {
        assert!(is_valid_mozhi_eetru(allowed), "allowed C+ஔ {allowed}");
    }
    for disallowed in ["சௌ", "மௌ"] {
        assert!(
            !is_valid_mozhi_eetru(disallowed),
            "disallowed C+ஔ {disallowed}"
        );
    }
}

#[test]
fn sutra_205_thanikkuril_otru() {
    for word in ["கல்", "பொன்", "மண்", "நொவ்", "பல்", "எண்", "தன்", "அவ்"]
    {
        assert!(
            is_thanikkuril_otru(word),
            "{word} should be thanikkuril_otru"
        );
    }

    for word in ["வேல்", "வாள்", "தூண்", "மரம்", "அரசு", "நாகு"]
    {
        assert!(
            !is_thanikkuril_otru(word),
            "{word} should not be thanikkuril_otru"
        );
    }
}

fn eval_punarchi_rules(input: &Value) -> Result<Value, PunarchiError> {
    let profile = match input.get("profile") {
        None => PunarchiProfile::default(),
        Some(v) => PunarchiProfile::parse(v.as_str().ok_or(PunarchiError::ExpectedProfileString)?)?,
    };
    let chapter = match input.get("chapter") {
        None => None,
        Some(v) => Some(PunarchiChapter::parse(
            v.as_str().ok_or(PunarchiError::UnsupportedChapter)?,
        )?),
    };
    let sutra = match input.get("sutra") {
        None => None,
        Some(v) => {
            let num = v.as_u64().ok_or(PunarchiError::SutraOutOfRange)?;
            Some(u16::try_from(num).map_err(|_| PunarchiError::SutraOutOfRange)?)
        }
    };
    let entries = punarchi_rules_filtered(profile, chapter, sutra)?;
    Ok(serde_json::to_value(entries).expect("serialize SutraInventoryEntry"))
}

fn eval_punarchi_join(input: &Value) -> Result<Value, PunarchiError> {
    let first = input
        .get("first")
        .and_then(Value::as_str)
        .ok_or(PunarchiError::ExpectedStringInput)?;
    let second = input
        .get("second")
        .and_then(Value::as_str)
        .ok_or(PunarchiError::ExpectedStringInput)?;
    let profile = match input.get("profile") {
        None => PunarchiProfile::default(),
        Some(v) => PunarchiProfile::parse(v.as_str().ok_or(PunarchiError::ExpectedProfileString)?)?,
    };

    let mut context = PunarchiContext::default();
    if let Some(ctx_val) = input.get("context") {
        let obj = ctx_val
            .as_object()
            .ok_or(PunarchiError::ExpectedContextObject)?;
        if let Some(rel) = obj.get("relation") {
            let rel_str = rel.as_str().ok_or(PunarchiError::UnsupportedRelation)?;
            context.relation = GrammaticalRelation::parse(rel_str)?;
        }
        if let Some(sub) = obj.get("subtype") {
            let sub_str = sub
                .as_str()
                .ok_or(PunarchiError::UnsupportedOrIncompatibleSubtype)?;
            context.subtype = Some(ContextSubtype::parse(sub_str)?);
        }
        if let Some(lc) = obj.get("lexical_class") {
            let lc_str = lc.as_str().ok_or(PunarchiError::UnsupportedLexicalClass)?;
            context.lexical_class = Some(LexicalClass::parse(lc_str)?);
        }
        if let Some(poetic) = obj.get("poetic") {
            context.poetic = poetic
                .as_bool()
                .ok_or(PunarchiError::ExpectedPoeticBoolean)?;
        }
    }

    let result = punarchi_join(first, second, &context, profile)?;
    Ok(serde_json::to_value(result).expect("serialize PunarchiJoinResult"))
}

fn eval_punarchi_split_candidates_validation(input: &Value) -> Result<Value, PunarchiError> {
    let surface = input
        .get("surface")
        .and_then(Value::as_str)
        .ok_or(PunarchiError::ExpectedStringInput)?;
    if surface.trim().is_empty() {
        return Err(PunarchiError::EmptyInput);
    }
    if surface.len() > MAX_SPLIT_SURFACE_BYTES {
        return Err(PunarchiError::SurfaceTooLong);
    }
    let _profile = match input.get("profile") {
        None => PunarchiProfile::default(),
        Some(v) => PunarchiProfile::parse(v.as_str().ok_or(PunarchiError::ExpectedProfileString)?)?,
    };
    if let Some(poetic) = input.get("poetic") {
        let _ = poetic
            .as_bool()
            .ok_or(PunarchiError::ExpectedPoeticBoolean)?;
    }
    Ok(Value::Array(Vec::new()))
}

#[test]
fn golden_prereq_rules_and_error_rows() {
    let vectors = support::vectors_by_tag("prereq");
    assert!(!vectors.is_empty(), "expected prereq golden vectors");

    for row in vectors {
        let id = row["id"].as_str().expect("vector id");
        let op = row["op"].as_str().expect("vector op");
        let input = &row["input"];

        let outcome = match op {
            "punarchi_rules" => eval_punarchi_rules(input),
            "punarchi_join" => eval_punarchi_join(input),
            "punarchi_split_candidates" => eval_punarchi_split_candidates_validation(input),
            other => panic!("{id}: unexpected op {other}"),
        };

        if let Some(expected_err) = row.get("expected_error").and_then(Value::as_str) {
            let err = outcome.expect_err(&format!("{id}: expected error {expected_err:?}"));
            assert_eq!(err.as_str(), expected_err, "{id}");
        } else {
            let actual = outcome.unwrap_or_else(|err| panic!("{id}: expected success, got {err}"));
            assert_eq!(actual, row["expected"], "{id}");
        }
    }
}

#[test]
fn golden_panpuppeyar_136_join_vectors() {
    let vectors = support::vectors_by_op_and_tag("punarchi_join", "panpuppeyar");
    assert!(!vectors.is_empty(), "expected panpuppeyar golden vectors");

    for row in vectors {
        let id = row["id"].as_str().expect("vector id");
        let actual = eval_punarchi_join(&row["input"])
            .unwrap_or_else(|err| panic!("{id}: expected success, got {err}"));
        assert_eq!(actual, row["expected"], "{id}");
    }
}
