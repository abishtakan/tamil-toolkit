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

fn main() {
    let source = "lexicon/collate.toml";
    println!("cargo:rerun-if-changed={source}");
    let profile: Profile = toml::from_str(&fs::read_to_string(source).expect("read collate.toml"))
        .expect("valid collate.toml");
    assert_eq!(profile.profile, "agara-v1");
    assert_eq!(profile.key_version, 1);
    assert_eq!(profile.order.len(), 325, "incomplete collation inventory");
    let mut ranks = BTreeMap::new();
    for (index, letter) in profile.order.iter().enumerate() {
        assert!(
            !letter.is_empty() && is_nfc(letter),
            "non-NFC or empty collation element at {index}"
        );
        assert!(
            ranks.insert(letter.clone(), index as u32 + 1).is_none(),
            "duplicate collation element at {index}"
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
                "duplicate expansion"
            );
            assert!(
                !ranks.contains_key(&expansion.text),
                "expansion shadows an element"
            );
            assert!(!expansion.elements.is_empty(), "empty expansion");
            assert_eq!(
                expansion.elements.concat(),
                expansion.text,
                "expansion must preserve written scalars"
            );
            let weights = expansion
                .elements
                .iter()
                .map(|element| {
                    ranks
                        .get(element)
                        .expect("expansion references an unknown element")
                        .to_string()
                })
                .collect::<Vec<_>>()
                .join(",");
            format!("({}, &[{weights}])", literal(&expansion.text))
        })
        .collect::<Vec<_>>()
        .join(",");
    let code = format!(
        "pub const PROFILE: &str = {};\npub const KEY_VERSION: u32 = {};\npub const LOOKUP: &[(&str, u32)] = &[{}];\npub const EXPANSIONS: &[(&str, &[u32])] = &[{}];\n",
        literal(&profile.profile), profile.key_version, lookup, expansions,
    );
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("collation_tables.rs"),
        code,
    )
    .expect("write collation tables");
}
