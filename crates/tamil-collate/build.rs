use serde::Deserialize;
use std::{collections::BTreeMap, env, fs, path::PathBuf};
use unicode_normalization::is_nfc;

#[derive(Deserialize)]
struct Profile {
    profile: String,
    key_version: u32,
    order: Vec<String>,
    expansions: Vec<Expansion>,
}

#[derive(Deserialize)]
struct Expansion {
    text: String,
    elements: Vec<String>,
}

fn literal(value: &str) -> String {
    format!(
        "\"{}\"",
        value
            .chars()
            .flat_map(char::escape_unicode)
            .collect::<String>()
    )
}

fn compile_profile(source: &str, prefix: &str) -> String {
    println!("cargo:rerun-if-changed={source}");
    let profile: Profile = toml::from_str(
        &fs::read_to_string(source).unwrap_or_else(|e| panic!("read {source}: {e}")),
    )
    .unwrap_or_else(|e| panic!("valid {source}: {e}"));
    assert_eq!(profile.key_version, 1);
    assert_eq!(
        profile.order.len(),
        325,
        "incomplete collation inventory for {source}"
    );
    let mut ranks = BTreeMap::new();
    for (index, letter) in profile.order.iter().enumerate() {
        assert!(
            !letter.is_empty() && is_nfc(letter),
            "non-NFC or empty collation element at {index} in {source}"
        );
        assert!(
            ranks.insert(letter.clone(), index as u32 + 1).is_none(),
            "duplicate collation element at {index} in {source}"
        );
    }
    let lookup = ranks
        .iter()
        .map(|(text, rank)| format!("({}, {rank})", literal(text)))
        .collect::<Vec<_>>()
        .join(",");
    let mut seen_expansions = std::collections::BTreeSet::new();
    let expansions = profile
        .expansions
        .iter()
        .map(|expansion| {
            assert!(is_nfc(&expansion.text) && !expansion.text.is_empty());
            assert!(
                seen_expansions.insert(&expansion.text),
                "duplicate expansion in {source}"
            );
            assert!(
                !ranks.contains_key(&expansion.text),
                "expansion shadows an element in {source}"
            );
            assert!(
                !expansion.elements.is_empty(),
                "empty expansion in {source}"
            );
            assert_eq!(
                expansion.elements.concat(),
                expansion.text,
                "expansion must preserve written scalars in {source}"
            );
            let weights = expansion
                .elements
                .iter()
                .map(|element| {
                    ranks
                        .get(element)
                        .unwrap_or_else(|| {
                            panic!("expansion references unknown element {element} in {source}")
                        })
                        .to_string()
                })
                .collect::<Vec<_>>()
                .join(",");
            format!("({}, &[{weights}])", literal(&expansion.text))
        })
        .collect::<Vec<_>>()
        .join(",");

    format!(
        "pub const {prefix}_PROFILE: &str = {};\npub const {prefix}_KEY_VERSION: u32 = {};\npub const {prefix}_LOOKUP: &[(&str, u32)] = &[{}];\npub const {prefix}_EXPANSIONS: &[(&str, &[u32])] = &[{}];\n",
        literal(&profile.profile), profile.key_version, lookup, expansions,
    )
}

fn main() {
    let agara_code = compile_profile("lexicon/collate.toml", "AGARA");
    let uyirmei_first_code = compile_profile("lexicon/collate_uyirmei_first.toml", "UYIRMEI_FIRST");

    let aliases = r#"
pub const PROFILE: &str = AGARA_PROFILE;
pub const KEY_VERSION: u32 = AGARA_KEY_VERSION;
pub const LOOKUP: &[(&str, u32)] = AGARA_LOOKUP;
pub const EXPANSIONS: &[(&str, &[u32])] = AGARA_EXPANSIONS;
"#;

    let code = format!("{agara_code}\n{uyirmei_first_code}\n{aliases}\n");
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("collation_tables.rs"),
        code,
    )
    .expect("write collation tables");
}
