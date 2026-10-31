use serde::Deserialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    env, fs,
    path::PathBuf,
};
use unicode_normalization::is_nfc;

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Profile {
    profile: String,
    max_key_bytes: usize,
    passthrough: String,
    mappings: Vec<Mapping>,
    ambiguous: Vec<Ambiguous>,
    encoding_preferences: Vec<Mapping>,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Mapping {
    legacy: String,
    unicode: String,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Ambiguous {
    legacy: String,
    candidates: Vec<String>,
}

#[derive(Default)]
struct Node {
    edges: BTreeMap<u8, usize>,
    terminal: Option<String>,
}

fn literal(text: &str) -> String {
    format!(
        "\"{}\"",
        text.chars()
            .flat_map(char::escape_unicode)
            .collect::<String>()
    )
}

fn valid_output(text: &str) -> bool {
    !text.is_empty()
        && is_nfc(text)
        && text
            .chars()
            .all(|c| !matches!(u32::from(c), 0x200c | 0x200d))
}

fn insert(nodes: &mut Vec<Node>, key: &str, terminal: String, maximum: usize) {
    assert!(!key.is_empty() && key.len() <= maximum, "invalid trie key");
    let mut current = 0;
    for byte in key.bytes() {
        current = match nodes[current].edges.get(&byte) {
            Some(&next) => next,
            None => {
                let next = nodes.len();
                nodes.push(Node::default());
                nodes[current].edges.insert(byte, next);
                next
            }
        };
    }
    assert!(
        nodes[current].terminal.replace(terminal).is_none(),
        "duplicate or ambiguous key in mappings"
    );
}

fn render_nodes(nodes: &[Node]) -> String {
    nodes
        .iter()
        .map(|node| {
            let terminal = node
                .terminal
                .as_ref()
                .map(|value| format!("Some({value})"))
                .unwrap_or("None".into());
            let edges = node
                .edges
                .iter()
                .map(|(byte, next)| format!("({byte},{next})"))
                .collect::<Vec<_>>()
                .join(",");
            format!("Node {{edges: &[{edges}], terminal: {terminal}}}")
        })
        .collect::<Vec<_>>()
        .join(",\n")
}

fn main() {
    let path = "lexicon/bamini.toml";
    println!("cargo:rerun-if-changed={path}");
    let profile: Profile = toml::from_str(&fs::read_to_string(path).expect("read bamini.toml"))
        .expect("valid bamini.toml");
    assert_eq!(profile.profile, "bamini-v1");
    assert_eq!(profile.max_key_bytes, 3);
    assert_eq!(
        profile.mappings.len(),
        298,
        "incomplete unambiguous profile"
    );
    assert_eq!(profile.ambiguous.len(), 1);
    let mut nodes = vec![Node::default()];
    let mut used_bytes = BTreeSet::new();
    for mapping in &profile.mappings {
        assert!(mapping.legacy.is_ascii(), "non-ASCII legacy key");
        assert!(
            valid_output(&mapping.unicode),
            "empty/non-NFC/joiner output"
        );
        insert(
            &mut nodes,
            &mapping.legacy,
            format!("Terminal::Text({})", literal(&mapping.unicode)),
            profile.max_key_bytes,
        );
        used_bytes.extend(mapping.legacy.bytes());
    }
    for ambiguous in &profile.ambiguous {
        assert!(ambiguous.legacy.is_ascii(), "non-ASCII ambiguity key");
        assert_eq!(
            ambiguous.legacy.len(),
            1,
            "v1 ambiguity diagnostics require single-byte keys"
        );
        let unique: BTreeSet<_> = ambiguous.candidates.iter().collect();
        assert!(unique.len() >= 2 && unique.len() == ambiguous.candidates.len());
        assert!(unique.iter().all(|text| valid_output(text)));
        insert(
            &mut nodes,
            &ambiguous.legacy,
            "Terminal::Ambiguous".to_owned(),
            profile.max_key_bytes,
        );
        used_bytes.extend(ambiguous.legacy.bytes());
    }
    assert_eq!(
        profile.passthrough.bytes().collect::<BTreeSet<_>>().len(),
        profile.passthrough.len(),
        "duplicate or non-ASCII pass-through scalar"
    );
    assert!(profile.passthrough.is_ascii() && !profile.passthrough.is_empty());
    assert!(
        profile
            .passthrough
            .bytes()
            .all(|byte| !used_bytes.contains(&byte)),
        "pass-through overlaps encoding syntax"
    );
    let mut preferences: BTreeMap<&str, &str> = profile
        .encoding_preferences
        .iter()
        .map(|entry| (entry.unicode.as_str(), entry.legacy.as_str()))
        .collect();
    assert_eq!(
        preferences.len(),
        profile.encoding_preferences.len(),
        "duplicate encoder preference"
    );
    let mut reverse: BTreeMap<&str, Vec<&str>> = BTreeMap::new();
    for mapping in &profile.mappings {
        reverse
            .entry(&mapping.unicode)
            .or_default()
            .push(&mapping.legacy);
    }
    let canonical: Vec<_> = reverse
        .into_iter()
        .map(|(text, spellings)| {
            let key = match spellings.as_slice() {
                [only] => {
                    assert!(
                        !preferences.contains_key(text),
                        "unused preference for a unique mapping"
                    );
                    *only
                }
                _ => {
                    let preferred = preferences
                        .remove(text)
                        .expect("missing canonical alias preference");
                    assert!(
                        spellings.contains(&preferred),
                        "preference is not a decoder alias"
                    );
                    preferred
                }
            };
            (text, key)
        })
        .collect();
    assert!(preferences.is_empty(), "unknown/unused encoder preference");
    assert_eq!(canonical.len(), 296);
    let maximum = canonical
        .iter()
        .map(|(text, _)| text.len())
        .max()
        .expect("encoder entries");
    let mut encode_nodes = vec![Node::default()];
    for &(text, key) in &canonical {
        insert(
            &mut encode_nodes,
            text,
            format!("Terminal::Text({})", literal(key)),
            maximum,
        );
    }
    let test_inputs = canonical
        .iter()
        .map(|(text, _)| literal(text))
        .collect::<Vec<_>>()
        .join(",");
    let code = format!("pub const PROFILE: &str = {};\npub const MAX_KEY_BYTES: usize = {};\npub const PASSTHROUGH: &str = {};\npub const NODES: &[Node] = &[{}];\npub const MAX_UNICODE_KEY_BYTES: usize = {maximum};\npub const ENCODE_NODES: &[Node] = &[{}];\n#[cfg(test)] pub const ENCODABLE_TEXT: &[&str] = &[{test_inputs}];\n",
                       literal(&profile.profile), profile.max_key_bytes, literal(&profile.passthrough), render_nodes(&nodes), render_nodes(&encode_nodes));
    fs::write(
        PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR")).join("bamini_tables.rs"),
        code,
    )
    .expect("write Bamini trie");
}
