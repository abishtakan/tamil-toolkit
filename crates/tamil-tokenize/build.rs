use serde::Deserialize;
use std::collections::{BTreeMap, BTreeSet};
use std::{env, fs, path::PathBuf};
use unicode_normalization::{is_nfc, UnicodeNormalization};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Inventory {
    version: String,
    stopword_source: String,
    stopword_sha256: String,
    stopword_license: String,
    stopword_attribution: String,
    abbreviation: Vec<Abbreviation>,
    stopword: Vec<Stopword>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Abbreviation {
    form: String,
    #[serde(rename = "use")]
    usage: String,
    following: String,
    min_spaces: usize,
    punctuation: String,
    region: String,
    source: String,
    locator: String,
    rights: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Stopword {
    word: String,
    tier: String,
    rationale: String,
}

#[derive(Deserialize)]
struct Properties {
    version: String,
    #[serde(flatten)]
    ranges: BTreeMap<String, Vec<[u32; 2]>>,
}

fn input(name: &str) -> String {
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let canonical = root.join("../../lexicon").join(name);
    let path = if canonical.is_file() {
        canonical
    } else {
        root.join("lexicon").join(name)
    };
    println!("cargo:rerun-if-changed={}", path.display());
    fs::read_to_string(path).expect("read canonical tokenizer inputs")
}

fn main() {
    let properties: Properties = toml::from_str(&input("tokenize-unicode-v17.toml")).unwrap();
    assert_eq!(properties.version, "17.0.0");
    let mut generated = String::new();
    for name in [
        "letter",
        "mark",
        "decimal",
        "format",
        "whitespace",
        "hard",
        "sentence_tail",
        "terminator",
    ] {
        let intervals = &properties.ranges[name];
        assert!(!intervals.is_empty());
        assert!(intervals.iter().all(|[a, b]| a <= b && *b <= 0x10ffff));
        assert!(intervals.windows(2).all(|w| w[0][1] < w[1][0]));
        generated.push_str(&format!(
            "pub(super) const {}: &[[u32; 2]] = &{intervals:?};\n",
            name.to_ascii_uppercase()
        ));
    }

    let mut data: Inventory = toml::from_str(&input("tokenize-v0.1.toml")).unwrap();
    assert_eq!(data.version, "0.1");
    assert_eq!(data.stopword_license, "Apache-2.0");
    assert!(
        data.stopword_source.starts_with("https://")
            && !data.stopword_attribution.trim().is_empty()
    );
    assert!(
        data.stopword_sha256.len() == 64
            && data.stopword_sha256.bytes().all(|b| b.is_ascii_hexdigit())
    );
    let mut forms = BTreeSet::new();
    data.abbreviation.sort_by(|a, b| a.form.cmp(&b.form));
    generated.push_str("pub(super) const ABBREVIATIONS: &[Abbreviation] = &[\n");
    for row in data.abbreviation {
        assert!(row.form.ends_with('.') && is_nfc(&row.form) && forms.insert(row.form.clone()));
        assert!(row
            .form
            .chars()
            .all(|c| c == '.' || ('\u{0b80}'..='\u{0bff}').contains(&c)));
        assert!(matches!(
            row.usage.as_str(),
            "honorific" | "initials" | "afternoon" | "morning" | "example" | "currency"
        ));
        assert!(
            matches!(row.region.as_str(), "TN" | "SL")
                && row.source.starts_with("https://")
                && !row.locator.trim().is_empty()
                && !row.rights.trim().is_empty()
        );
        assert!(row.min_spaces <= 1);
        assert!(row.punctuation.chars().all(|c| matches!(c, ':' | ')')));
        let following = match row.following.as_str() {
            "tamil" => "Tamil",
            "decimal" => "Decimal",
            _ => panic!("unknown abbreviation context"),
        };
        let max_bytes = row.form.nfd().map(char::len_utf8).sum::<usize>();
        generated.push_str(&format!("Abbreviation {{ form: {:?}, max_bytes: {max_bytes}, following: Following::{following}, min_spaces: {}, punctuation: {:?} }},\n", row.form, row.min_spaces, row.punctuation));
    }
    generated.push_str("];\n");

    let mut conservative = BTreeSet::new();
    let mut broad = BTreeSet::new();
    for row in data.stopword {
        assert!(!row.word.is_empty() && is_nfc(&row.word) && !row.rationale.trim().is_empty());
        assert!(row
            .word
            .chars()
            .all(|c| ('\u{0b80}'..='\u{0bff}').contains(&c)));
        match row.tier.as_str() {
            "conservative" => assert!(conservative.insert(row.word.clone())),
            "broad" => (),
            _ => panic!("unknown curated stopword tier"),
        }
        assert!(broad.insert(row.word));
    }
    assert!(!conservative.is_empty() && broad.len() > conservative.len());
    for (name, list) in [("CONSERVATIVE", conservative), ("BROAD", broad)] {
        let list: Vec<_> = list.iter().collect();
        generated.push_str(&format!("pub(super) const {name}: &[&str] = &{list:?};\n"));
    }
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("tables.rs"),
        generated,
    )
    .unwrap();
}
