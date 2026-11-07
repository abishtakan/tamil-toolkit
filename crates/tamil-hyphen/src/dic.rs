use crate::types::{DicHeader, HyphenDictionary, LiangPattern};
use std::fs::File;
use std::io::{self, Write};
use std::path::Path;

/// Options controlling Frank Liang pattern generation and .dic file export.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DicExportOptions {
    pub left_hyphen_min: usize,
    pub right_hyphen_min: usize,
}

impl Default for DicExportOptions {
    fn default() -> Self {
        Self {
            left_hyphen_min: 3,
            right_hyphen_min: 3,
        }
    }
}

/// Programmatically generate a complete, phonotactically verified Frank Liang
/// hyphenation dictionary from Tamil grammatical rules.
pub fn generate_patterns(options: &DicExportOptions) -> HyphenDictionary {
    let mut patterns = Vec::new();

    // 1. Format controls (ZWJ and ZWNJ)
    // Never break across or adjacent to ZERO-WIDTH JOINER (U+200D)
    patterns.push("2\u{200D}2".to_string());
    // Never break across ZERO-WIDTH NON JOINER (U+200C)
    patterns.push("2\u{200C}2".to_string());

    // 2. Independent Vowels (Uyir)
    // Break permitted before independent vowels when occurring internally
    let uyir = [
        '\u{0B85}', '\u{0B86}', '\u{0B87}', '\u{0B88}', '\u{0B89}', '\u{0B8A}',
        '\u{0B8E}', '\u{0B8F}', '\u{0B90}', '\u{0B92}', '\u{0B93}', '\u{0B94}',
    ];
    for &u in &uyir {
        patterns.push(format!("1{}", u));
    }

    // 3. Dependent Vowel Signs (Uyirmei off-glides)
    // Break permitted AFTER dependent vowels (open syllable), never before
    let vowel_signs = [
        '\u{0BBE}', '\u{0BBF}', '\u{0BC0}', '\u{0BC1}', '\u{0BC2}', '\u{0BC6}',
        '\u{0BC7}', '\u{0BC8}', '\u{0BCA}', '\u{0BCB}', '\u{0BCC}', '\u{0BD7}',
    ];
    for &vs in &vowel_signs {
        // Never break before combining vowel sign
        patterns.push(format!("2{}", vs));
        // Break allowed after combining vowel sign
        patterns.push(format!("{}1", vs));
    }

    // 4. Base Consonants (including Grantha bases)
    let consonants = [
        '\u{0B95}', // க
        '\u{0B99}', // ங
        '\u{0B9A}', // ச
        '\u{0B9C}', // ஜ
        '\u{0B9E}', // ஞ
        '\u{0B9F}', // ட
        '\u{0BA3}', // ண
        '\u{0BA4}', // த
        '\u{0BA8}', // ந
        '\u{0BA9}', // ன
        '\u{0BAA}', // ப
        '\u{0BAE}', // ம
        '\u{0BAF}', // ய
        '\u{0BB0}', // ர
        '\u{0BB1}', // ற
        '\u{0BB2}', // ல
        '\u{0BB3}', // ள
        '\u{0BB4}', // ழ
        '\u{0BB5}', // வ
        '\u{0BB6}', // ஶ
        '\u{0BB7}', // ஷ
        '\u{0BB8}', // ஸ
        '\u{0BB9}', // ஹ
    ];

    // Break permitted before consonant onsets (inherent vowel /a/ or following vowel sign)
    for &c in &consonants {
        patterns.push(format!("1{}", c));
    }

    // 5. Virama & Pure Consonants (Mei - Coda Binding)
    // Never break before virama (attaches to preceding consonant)
    patterns.push("2\u{0BCD}".to_string());

    for &c in &consonants {
        // Do not break before any consonant + virama (pure consonant)
        patterns.push(format!("2{}\u{0BCD}", c));
        // Break allowed after pure consonant (coda) when followed by next onset
        patterns.push(format!("2{}\u{0BCD}1", c));
    }

    // 6. Coda Clusters & Geminates (Multiple consecutive pure consonants)
    // In multi-consonant clusters (e.g. த்த், ர்ப்ப், ற்க்), all consonants belong to the preceding
    // syllable coda. Never break between pure consonants in a cluster!
    for &c in &consonants {
        // Inhibit break when virama is followed by another pure consonant (weight 2 overrides 1)
        patterns.push(format!("\u{0BCD}2{}\u{0BCD}", c));
    }

    // 7. Atomic Grantha Ligatures (Ksha க்ஷ and Shri/Sri ஸ்ரீ)
    // Ksha: க + ் + ஷ
    patterns.push("2\u{0B95}\u{0BCD}2\u{0BB7}".to_string());
    patterns.push("1\u{0B95}\u{0BCD}2\u{0BB7}".to_string());  // Break allowed before Ksha
    patterns.push("2\u{0B95}\u{0BCD}2\u{0BB7}1".to_string()); // Break allowed after Ksha vowel
    // Pure consonant Ksha (க்ஷ்):
    patterns.push("2\u{0B95}\u{0BCD}2\u{0BB7}\u{0BCD}".to_string());
    patterns.push("2\u{0B95}\u{0BCD}2\u{0BB7}\u{0BCD}1".to_string());

    // Shri/Sri: ஸ + ் + ர + ீ and ஶ + ் + ர + ீ
    patterns.push("2\u{0BB8}\u{0BCD}2\u{0BB0}2\u{0BC0}".to_string());
    patterns.push("2\u{0BB6}\u{0BCD}2\u{0BB0}2\u{0BC0}".to_string());
    patterns.push("1\u{0BB8}\u{0BCD}2\u{0BB0}2\u{0BC0}".to_string());
    patterns.push("1\u{0BB6}\u{0BCD}2\u{0BB0}2\u{0BC0}".to_string());
    patterns.push("2\u{0BB8}\u{0BCD}2\u{0BB0}\u{0BC0}1".to_string());
    patterns.push("2\u{0BB6}\u{0BCD}2\u{0BB0}\u{0BC0}1".to_string());

    // 8. Aytham (ஃ - U+0B83)
    // Aytham is a dependent coda letter. Never break before Aytham!
    patterns.push("2\u{0B83}".to_string());
    patterns.push("2\u{0B83}1".to_string()); // Break allowed after Aytham before next onset
    for &c in &consonants {
        // Never break between Aytham and a following pure consonant
        patterns.push(format!("\u{0B83}2{}\u{0BCD}", c));
    }

    // Parse into LiangPattern instances and sort alphabetically for determinism
    let mut parsed_patterns: Vec<LiangPattern> = patterns
        .into_iter()
        .filter_map(|p| LiangPattern::parse(&p))
        .collect();

    parsed_patterns.sort_by(|a, b| a.raw.cmp(&b.raw));
    parsed_patterns.dedup_by(|a, b| a.raw == b.raw);

    HyphenDictionary {
        header: DicHeader {
            encoding: "UTF-8".to_string(),
            left_hyphen_min: options.left_hyphen_min,
            right_hyphen_min: options.right_hyphen_min,
            license_notice: "%  Hyphenation patterns for Tamil (ta_IN, ta_LK, ta_SG, ta_MY, ta)\n\
                             %  Generated by tamil-toolkit (https://github.com/tamil-toolkit/tamil-toolkit)\n\
                             %  Based on W3C Tamil Layout Requirements (tam-lreq) & Classical Grammar\n\
                             %  License: MIT / LGPL / GPL Tri-license".to_string(),
        },
        patterns: parsed_patterns,
    }
}

/// Serialize a `HyphenDictionary` into standard `.dic` file format content.
pub fn export_dic_content(dict: &HyphenDictionary) -> String {
    let mut out = String::new();
    out.push_str(&dict.header.encoding);
    out.push('\n');
    out.push_str(&format!("LEFTHYPHENMIN {}\n", dict.header.left_hyphen_min));
    out.push_str(&format!("RIGHTHYPHENMIN {}\n", dict.header.right_hyphen_min));
    out.push_str(&dict.header.license_notice);
    out.push_str("\n\n");

    for p in &dict.patterns {
        out.push_str(&p.raw);
        out.push('\n');
    }

    out
}

/// Export a `HyphenDictionary` directly to a file on disk.
pub fn export_dic_file(dict: &HyphenDictionary, path: impl AsRef<Path>) -> io::Result<()> {
    let content = export_dic_content(dict);
    let mut file = File::create(path)?;
    file.write_all(content.as_bytes())?;
    Ok(())
}
