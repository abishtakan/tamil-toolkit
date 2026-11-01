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

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TsciiProfile {
    profile: String,
    source: String,
    mappings: Vec<TsciiMapping>,
    encoding_preferences: Vec<TsciiMapping>,
    #[serde(default)]
    ambiguous: Vec<ByteAmbiguous>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CidProfile {
    profile: String,
    source: String,
    source_url: String,
    source_sha256: String,
    max_key_cids: usize,
    mappings: Vec<CidMapping>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CidMapping {
    cids: Vec<u16>,
    unicode: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct TsciiMapping {
    hex: String,
    unicode: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ByteAmbiguous {
    hex: String,
    candidates: Vec<String>,
}

#[derive(Default)]
struct Node {
    edges: BTreeMap<u8, usize>,
    terminal: Option<String>,
}

#[derive(Default)]
struct CidNode {
    edges: BTreeMap<u16, usize>,
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

fn insert(nodes: &mut Vec<Node>, key: &[u8], terminal: String, maximum: usize) {
    assert!(!key.is_empty() && key.len() <= maximum, "invalid trie key");
    let mut current = 0;
    for &byte in key {
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

fn insert_cids(nodes: &mut Vec<CidNode>, key: &[u16], terminal: String, maximum: usize) {
    assert!(
        !key.is_empty() && key.len() <= maximum,
        "invalid CID trie key"
    );
    let mut current = 0;
    for &cid in key {
        current = match nodes[current].edges.get(&cid) {
            Some(&next) => next,
            None => {
                let next = nodes.len();
                nodes.push(CidNode::default());
                nodes[current].edges.insert(cid, next);
                next
            }
        };
    }
    assert!(
        nodes[current].terminal.replace(terminal).is_none(),
        "duplicate LT-TM CID key"
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

fn render_cid_nodes(nodes: &[CidNode]) -> String {
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
                .map(|(cid, next)| format!("({cid},{next})"))
                .collect::<Vec<_>>()
                .join(",");
            format!("CidNode {{edges: &[{edges}], terminal: {terminal}}}")
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
            mapping.legacy.as_bytes(),
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
            ambiguous.legacy.as_bytes(),
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
            text.as_bytes(),
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

    for (name, expected_profile, expected_keys, expected_values) in [
        ("tscii", "tscii-tamilutil-bounded-v1", 341, 340),
        ("tab", "tab-tamilutil-bounded-v1", 332, 323),
        ("tam", "tam-utn18-bounded-v1", 407, 331),
        ("anjal", "anjal-tamilutil-bounded-v1", 309, 302),
    ] {
        let path = format!("lexicon/{name}.toml");
        println!("cargo:rerun-if-changed={path}");
        let profile: TsciiProfile =
            toml::from_str(&fs::read_to_string(&path).expect("read tscii.toml"))
                .expect("valid tscii.toml");
        assert_eq!(profile.profile, expected_profile);
        assert!(!profile.source.is_empty());
        assert_eq!(profile.mappings.len(), expected_keys);
        let mut nodes = vec![Node::default()];
        let mut reverse: BTreeMap<&str, Vec<Vec<u8>>> = BTreeMap::new();
        for mapping in &profile.mappings {
            assert!(!mapping.hex.is_empty() && mapping.hex.len() % 2 == 0);
            let key: Vec<u8> = mapping
                .hex
                .as_bytes()
                .chunks_exact(2)
                .map(|pair| {
                    u8::from_str_radix(std::str::from_utf8(pair).expect("ASCII hex"), 16)
                        .expect("valid hex byte")
                })
                .collect();
            assert!((name == "tam" || key[0] >= 0x80) && valid_output(&mapping.unicode));
            reverse
                .entry(&mapping.unicode)
                .or_default()
                .push(key.clone());
            insert(
                &mut nodes,
                &key,
                format!("Terminal::Text({})", literal(&mapping.unicode)),
                3,
            );
        }
        assert_eq!(profile.ambiguous.len(), if name == "anjal" { 4 } else { 0 });
        for item in &profile.ambiguous {
            assert_eq!(
                item.hex.len(),
                2,
                "ambiguous byte keys must be single bytes"
            );
            let byte = u8::from_str_radix(&item.hex, 16).expect("valid ambiguous hex");
            assert!(byte >= 0x80);
            let unique: BTreeSet<_> = item.candidates.iter().collect();
            assert!(unique.len() >= 2 && unique.len() == item.candidates.len());
            assert!(unique.iter().all(|value| valid_output(value)));
            insert(&mut nodes, &[byte], "Terminal::Ambiguous".to_owned(), 1);
        }
        let mut preferences = BTreeMap::new();
        for item in &profile.encoding_preferences {
            let bytes = item
                .hex
                .as_bytes()
                .chunks_exact(2)
                .map(|pair| {
                    u8::from_str_radix(std::str::from_utf8(pair).expect("ASCII hex"), 16)
                        .expect("valid hex")
                })
                .collect::<Vec<_>>();
            assert_eq!(item.hex.len(), bytes.len() * 2);
            assert!(preferences.insert(item.unicode.as_str(), bytes).is_none());
        }
        let mut encode_nodes = vec![Node::default()];
        let mut maximum = 0;
        assert_eq!(reverse.len(), expected_values);
        for (text, spellings) in reverse {
            let key = match spellings.as_slice() {
                [only] => {
                    assert!(!preferences.contains_key(text));
                    only.clone()
                }
                _ => {
                    let preferred = preferences
                        .remove(text)
                        .expect("missing canonical TSCII alias preference");
                    assert!(spellings.contains(&preferred));
                    preferred
                }
            };
            maximum = maximum.max(text.len());
            let bytes = key.iter().map(u8::to_string).collect::<Vec<_>>().join(",");
            insert(
                &mut encode_nodes,
                text.as_bytes(),
                format!("Terminal::Bytes(&[{bytes}])"),
                text.len(),
            );
        }
        assert!(preferences.is_empty(), "unused TSCII alias preference");
        let code = format!(
        "pub const PROFILE: &str = {};\npub const NODES: &[Node] = &[{}];\npub const ENCODE_NODES: &[Node] = &[{}];\npub const MAX_UNICODE_KEY_BYTES: usize = {maximum};\n",
        literal(&profile.profile), render_nodes(&nodes), render_nodes(&encode_nodes)
    );
        fs::write(
            PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"))
                .join(format!("{name}_tables.rs")),
            code,
        )
        .expect("write TSCII trie");
    }

    for (name, expected_profile, expected_sha256, expected_len) in [
        (
            "lt_tm",
            "lt-tm-indoword-cid-v1",
            "32fc21ffe8e2fbffa33d5f3899acfd15ee8a2ab9fc5fd5e931f9e7d4ec3326cd",
            332,
        ),
        (
            "vanavil",
            "vanavil-avvaiyar-cid-v1",
            "4948396d50fbbaf251ddfe620ca5d8a0ccdb65b5bef07231065a5d6439754b67",
            319,
        ),
    ] {
        let path = format!("lexicon/{name}.toml");
        println!("cargo:rerun-if-changed={path}");
        let profile: CidProfile =
            toml::from_str(&fs::read_to_string(&path).expect("read CID profile toml"))
                .expect("valid CID profile toml");
        assert_eq!(profile.profile, expected_profile);
        assert!(!profile.source.is_empty() && profile.source_url.starts_with("https://"));
        assert_eq!(profile.source_sha256, expected_sha256);
        assert_eq!(profile.max_key_cids, 3);
        assert_eq!(profile.mappings.len(), expected_len);

        let mut cid_nodes = vec![CidNode::default()];
        let mut reverse: BTreeMap<&str, &[u16]> = BTreeMap::new();
        for mapping in &profile.mappings {
            assert!(!mapping.cids.is_empty() && mapping.cids.len() <= profile.max_key_cids);
            assert!(
                mapping
                    .cids
                    .iter()
                    .all(|cid| !matches!(*cid, 0xd800..=0xdfff)),
                "surrogate code unit in CID map"
            );
            assert!(
                valid_output(&mapping.unicode),
                "invalid CID profile Unicode output"
            );
            insert_cids(
                &mut cid_nodes,
                &mapping.cids,
                literal(&mapping.unicode),
                profile.max_key_cids,
            );
            assert!(
                reverse.insert(&mapping.unicode, &mapping.cids).is_none(),
                "duplicate CID profile Unicode output"
            );
        }
        assert_eq!(reverse.len(), expected_len);

        let mut encode_nodes = vec![Node::default()];
        let mut maximum_unicode_bytes = 0;
        let encodable_text = reverse
            .keys()
            .map(|text| literal(text))
            .collect::<Vec<_>>()
            .join(",");
        for (text, cids) in reverse {
            maximum_unicode_bytes = maximum_unicode_bytes.max(text.len());
            let codes = cids
                .iter()
                .map(u16::to_string)
                .collect::<Vec<_>>()
                .join(",");
            insert(
                &mut encode_nodes,
                text.as_bytes(),
                format!("Terminal::Cids(&[{codes}])"),
                text.len(),
            );
        }
        let code = format!(
            "pub const PROFILE: &str = {};\npub const MAX_KEY_CIDS: usize = {};\npub const CID_NODES: &[CidNode] = &[{}];\npub const MAX_UNICODE_KEY_BYTES: usize = {maximum_unicode_bytes};\npub const ENCODE_NODES: &[Node] = &[{}];\n#[cfg(test)] pub const ENCODABLE_TEXT: &[&str] = &[{encodable_text}];\n",
            literal(&profile.profile),
            profile.max_key_cids,
            render_cid_nodes(&cid_nodes),
            render_nodes(&encode_nodes),
        );
        fs::write(
            PathBuf::from(env::var_os("OUT_DIR").expect("OUT_DIR"))
                .join(format!("{name}_tables.rs")),
            code,
        )
        .expect("write CID tries");
    }
}
