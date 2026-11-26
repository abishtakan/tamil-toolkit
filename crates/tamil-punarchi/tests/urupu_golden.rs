mod support;

use serde_json::Value;
use tamil_punarchi::{
    punarchi_join, ContextSubtype, GrammaticalRelation, LexicalClass, PunarchiContext,
    PunarchiError, PunarchiProfile,
};

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

#[test]
fn golden_urupu_join_vectors() {
    let vectors = support::vectors_by_op_and_tag("punarchi_join", "urupu");
    assert!(!vectors.is_empty(), "expected urupu golden vectors");

    for row in vectors {
        let id = row["id"].as_str().expect("vector id");
        let actual = eval_punarchi_join(&row["input"])
            .unwrap_or_else(|err| panic!("{id}: expected success, got {err}"));
        assert_eq!(actual, row["expected"], "{id}");
    }
}
