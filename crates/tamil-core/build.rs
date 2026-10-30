use serde::Deserialize;
use std::{collections::BTreeMap, env, fs, path::PathBuf};

#[derive(Deserialize)]
struct Rules {
    version: u32,
    pulli: String,
    aytham: String,
    atomic_letters: Vec<String>,
    consonants: BTreeMap<String, Vec<String>>,
    vowels: Vec<Vowel>,
}

#[derive(Deserialize)]
struct Vowel {
    uyir: String,
    sign: String,
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
    let source = "../../lexicon/core.toml";
    println!("cargo:rerun-if-changed={source}");
    let rules: Rules = toml::from_str(&fs::read_to_string(source).expect("read core.toml"))
        .expect("valid core.toml");
    assert_eq!(rules.version, 1, "unsupported core table version");
    assert_eq!(rules.pulli.chars().count(), 1);
    assert_eq!(rules.aytham.chars().count(), 1);
    assert_eq!(rules.vowels.len(), 12);
    let mut seen = std::collections::BTreeSet::new();
    let consonants = rules
        .consonants
        .iter()
        .flat_map(|(class, letters)| {
            assert!(["vallinam", "mellinam", "idaiyinam", "grantha"].contains(&class.as_str()));
            letters.iter().map(move |letter| (letter, class))
        })
        .map(|(letter, class)| {
            assert!(
                !letter.is_empty() && seen.insert(letter.clone()),
                "duplicate consonant"
            );
            format!("({}, {})", literal(letter), literal(class))
        })
        .collect::<Vec<_>>()
        .join(",");
    let mut seen_vowels = std::collections::BTreeSet::new();
    let mut seen_signs = std::collections::BTreeSet::new();
    let vowels = rules
        .vowels
        .iter()
        .map(|v| {
            assert_eq!(v.uyir.chars().count(), 1);
            assert!(seen_vowels.insert(v.uyir.clone()) && seen_signs.insert(v.sign.clone()));
            format!("({}, {})", literal(&v.uyir), literal(&v.sign))
        })
        .collect::<Vec<_>>()
        .join(",");
    let mut atomic = rules.atomic_letters;
    assert!(atomic.iter().all(|s| !s.is_empty()));
    atomic.sort_by_key(|s| std::cmp::Reverse(s.len()));
    let atomic = atomic
        .iter()
        .map(|s| literal(s))
        .collect::<Vec<_>>()
        .join(",");
    let generated = format!(
        "pub const PULLI: &str = {};\npub const AYTHAM: &str = {};\npub const CONSONANTS: &[(&str, &str)] = &[{}];\npub const VOWELS: &[(&str, &str)] = &[{}];\npub const ATOMIC_LETTERS: &[&str] = &[{}];\n",
        literal(&rules.pulli), literal(&rules.aytham), consonants, vowels, atomic
    );
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("core_tables.rs"),
        generated,
    )
    .expect("write core tables");
}
