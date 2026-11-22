use serde::Deserialize;
use std::{collections::BTreeSet, env, fs, path::PathBuf};
use unicode_normalization::is_nfc;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TranslitProfile {
    profile: String,
    pulli: String,
    aytham: String,
    ksha: String,
    sri: String,
    vowels: Vec<VowelRow>,
    consonants: Vec<ConsonantRow>,
    aytham_tokens: AythamTokens,
    tamil99: Tamil99Config,
    suratha_bamini: SurathaBaminiConfig,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct VowelRow {
    independent: String,
    dependent: String,
    iso_15919: String,
    madras_lexicon: String,
    itrans: String,
    harvard_kyoto: String,
    phonetic: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ConsonantRow {
    tamil: String,
    iso_15919: String,
    madras_lexicon: String,
    itrans: String,
    harvard_kyoto: String,
    phonetic: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct AythamTokens {
    iso_15919: String,
    madras_lexicon: String,
    itrans: String,
    harvard_kyoto: String,
    phonetic: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Tamil99Config {
    pulli_key: String,
    aytham_key: String,
    vowels: Vec<Tamil99Vowel>,
    consonants: Vec<KeyTamil>,
    special: Vec<KeyTamil>,
    homorganic_pairs: Vec<[String; 2]>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Tamil99Vowel {
    key: String,
    independent: String,
    dependent: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct KeyTamil {
    key: String,
    tamil: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SurathaBaminiConfig {
    pulli_key: String,
    pre_vowel_e: String,
    pre_vowel_ee: String,
    pre_vowel_ai: String,
    post_vowel_aa: String,
    post_vowel_i: String,
    post_vowel_ii: String,
    post_vowel_au_suffix: String,
    vowels: Vec<KeyTamil>,
    consonants: Vec<KeyTamil>,
    precomposed_u: Vec<KeyTamil>,
}

fn lit(text: &str) -> String {
    format!(
        "\"{}\"",
        text.chars()
            .flat_map(char::escape_unicode)
            .collect::<String>()
    )
}

fn single_char(s: &str) -> char {
    let mut it = s.chars();
    let ch = it.next().expect("non-empty char");
    assert!(it.next().is_none(), "expected single scalar: {s}");
    ch
}

fn char_lit(ch: char) -> String {
    format!("'\\u{{{:x}}}'", u32::from(ch))
}

fn main() {
    let path = "lexicon/translit.toml";
    println!("cargo:rerun-if-changed={path}");
    let data: TranslitProfile =
        toml::from_str(&fs::read_to_string(path).expect("read lexicon/translit.toml"))
            .expect("valid lexicon/translit.toml");
    assert_eq!(data.profile, "translit-v0.1");
    assert_eq!(data.vowels.len(), 12);
    assert_eq!(data.consonants.len(), 23);
    assert!(is_nfc(&data.aytham) && is_nfc(&data.ksha) && is_nfc(&data.sri));

    let vowel_rows: Vec<String> = data
        .vowels
        .iter()
        .map(|v| {
            let ind = single_char(&v.independent);
            let dep = if v.dependent.is_empty() {
                "None".to_owned()
            } else {
                format!("Some({})", char_lit(single_char(&v.dependent)))
            };
            format!(
                "VowelEntry {{ independent: {}, dependent: {dep}, iso_15919: {}, madras_lexicon: {}, itrans: {}, harvard_kyoto: {}, phonetic: {} }}",
                char_lit(ind),
                lit(&v.iso_15919),
                lit(&v.madras_lexicon),
                lit(&v.itrans),
                lit(&v.harvard_kyoto),
                lit(&v.phonetic),
            )
        })
        .collect();

    let cons_rows: Vec<String> = data
        .consonants
        .iter()
        .map(|c| {
            let ta = single_char(&c.tamil);
            format!(
                "ConsonantEntry {{ tamil: {}, iso_15919: {}, madras_lexicon: {}, itrans: {}, harvard_kyoto: {}, phonetic: {} }}",
                char_lit(ta),
                lit(&c.iso_15919),
                lit(&c.madras_lexicon),
                lit(&c.itrans),
                lit(&c.harvard_kyoto),
                lit(&c.phonetic),
            )
        })
        .collect();

    let mut t99_keys = BTreeSet::new();
    for k in [&data.tamil99.pulli_key, &data.tamil99.aytham_key] {
        assert!(t99_keys.insert(single_char(k)), "duplicate tamil99 key");
    }
    let t99_vowels: Vec<String> = data
        .tamil99
        .vowels
        .iter()
        .map(|v| {
            let k = single_char(&v.key);
            assert!(t99_keys.insert(k), "duplicate tamil99 vowel key");
            let dep = if v.dependent.is_empty() {
                "None".to_owned()
            } else {
                format!("Some({})", char_lit(single_char(&v.dependent)))
            };
            format!(
                "({}, {}, {dep})",
                char_lit(k),
                char_lit(single_char(&v.independent))
            )
        })
        .collect();
    let t99_cons: Vec<String> = data
        .tamil99
        .consonants
        .iter()
        .map(|c| {
            let k = single_char(&c.key);
            assert!(t99_keys.insert(k), "duplicate tamil99 consonant key");
            format!("({}, {})", char_lit(k), char_lit(single_char(&c.tamil)))
        })
        .collect();
    let t99_special: Vec<String> = data
        .tamil99
        .special
        .iter()
        .map(|s| {
            let k = single_char(&s.key);
            assert!(t99_keys.insert(k), "duplicate tamil99 special key");
            format!("({}, {})", char_lit(k), lit(&s.tamil))
        })
        .collect();
    let t99_homo: Vec<String> = data
        .tamil99
        .homorganic_pairs
        .iter()
        .map(|[a, b]| {
            format!(
                "({}, {})",
                char_lit(single_char(a)),
                char_lit(single_char(b))
            )
        })
        .collect();

    let sb_vowels: Vec<String> = data
        .suratha_bamini
        .vowels
        .iter()
        .map(|v| {
            format!(
                "({}, {})",
                char_lit(single_char(&v.key)),
                char_lit(single_char(&v.tamil))
            )
        })
        .collect();
    let sb_cons: Vec<String> = data
        .suratha_bamini
        .consonants
        .iter()
        .map(|c| {
            format!(
                "({}, {})",
                char_lit(single_char(&c.key)),
                char_lit(single_char(&c.tamil))
            )
        })
        .collect();
    let sb_u: Vec<String> = data
        .suratha_bamini
        .precomposed_u
        .iter()
        .map(|u| format!("({}, {})", char_lit(single_char(&u.key)), lit(&u.tamil)))
        .collect();

    let out = format!(
        "pub const PROFILE: &str = {};\n\
         pub const PULLI: char = {};\n\
         pub const AYTHAM: char = {};\n\
         pub const VOWELS: &[VowelEntry] = &[{}];\n\
         pub const CONSONANTS: &[ConsonantEntry] = &[{}];\n\
         pub const AYTHAM_ISO: &str = {};\n\
         pub const AYTHAM_MTL: &str = {};\n\
         pub const AYTHAM_ITRANS: &str = {};\n\
         pub const AYTHAM_HK: &str = {};\n\
         pub const AYTHAM_PHONETIC: &str = {};\n\
         pub const T99_PULLI_KEY: char = {};\n\
         pub const T99_AYTHAM_KEY: char = {};\n\
         pub const T99_VOWELS: &[(char, char, Option<char>)] = &[{}];\n\
         pub const T99_CONSONANTS: &[(char, char)] = &[{}];\n\
         pub const T99_SPECIAL: &[(char, &str)] = &[{}];\n\
         pub const T99_HOMORGANIC: &[(char, char)] = &[{}];\n\
         pub const SB_PULLI_KEY: char = {};\n\
         pub const SB_PRE_E: char = {};\n\
         pub const SB_PRE_EE: char = {};\n\
         pub const SB_PRE_AI: char = {};\n\
         pub const SB_POST_AA: char = {};\n\
         pub const SB_POST_I: char = {};\n\
         pub const SB_POST_II: char = {};\n\
         pub const SB_POST_AU: char = {};\n\
         pub const SB_VOWELS: &[(char, char)] = &[{}];\n\
         pub const SB_CONSONANTS: &[(char, char)] = &[{}];\n\
         pub const SB_PRECOMPOSED_U: &[(char, &str)] = &[{}];\n",
        lit(&data.profile),
        char_lit(single_char(&data.pulli)),
        char_lit(single_char(&data.aytham)),
        vowel_rows.join(","),
        cons_rows.join(","),
        lit(&data.aytham_tokens.iso_15919),
        lit(&data.aytham_tokens.madras_lexicon),
        lit(&data.aytham_tokens.itrans),
        lit(&data.aytham_tokens.harvard_kyoto),
        lit(&data.aytham_tokens.phonetic),
        char_lit(single_char(&data.tamil99.pulli_key)),
        char_lit(single_char(&data.tamil99.aytham_key)),
        t99_vowels.join(","),
        t99_cons.join(","),
        t99_special.join(","),
        t99_homo.join(","),
        char_lit(single_char(&data.suratha_bamini.pulli_key)),
        char_lit(single_char(&data.suratha_bamini.pre_vowel_e)),
        char_lit(single_char(&data.suratha_bamini.pre_vowel_ee)),
        char_lit(single_char(&data.suratha_bamini.pre_vowel_ai)),
        char_lit(single_char(&data.suratha_bamini.post_vowel_aa)),
        char_lit(single_char(&data.suratha_bamini.post_vowel_i)),
        char_lit(single_char(&data.suratha_bamini.post_vowel_ii)),
        char_lit(single_char(&data.suratha_bamini.post_vowel_au_suffix)),
        sb_vowels.join(","),
        sb_cons.join(","),
        sb_u.join(","),
    );
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("translit_tables.rs"),
        out,
    )
    .expect("write translit_tables.rs");
}
