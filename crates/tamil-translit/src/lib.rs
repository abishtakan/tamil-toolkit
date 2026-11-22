//! Lossless Tamil orthographic romanization (ISO 15919, Madras Lexicon, ITRANS,
//! Harvard-Kyoto) and deterministic offline input (Tamil99, Anjal phonetic,
//! Suratha Bamini, rule-based Phonetic/Tanglish v1).
//! See `docs/specs/translit-v0.1.md` for the normative contract.
#![forbid(unsafe_code)]

use tamil_core::normalize_nfc;

pub(crate) struct VowelEntry {
    pub(crate) independent: char,
    pub(crate) dependent: Option<char>,
    pub(crate) iso_15919: &'static str,
    pub(crate) madras_lexicon: &'static str,
    pub(crate) itrans: &'static str,
    pub(crate) harvard_kyoto: &'static str,
    pub(crate) phonetic: &'static str,
}

pub(crate) struct ConsonantEntry {
    pub(crate) tamil: char,
    pub(crate) iso_15919: &'static str,
    pub(crate) madras_lexicon: &'static str,
    pub(crate) itrans: &'static str,
    pub(crate) harvard_kyoto: &'static str,
    pub(crate) phonetic: &'static str,
}

mod tables {
    use super::{ConsonantEntry, VowelEntry};
    include!(concat!(env!("OUT_DIR"), "/translit_tables.rs"));
}

pub use tables::PROFILE;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Scheme {
    Iso15919,
    MadrasLexicon,
    Itrans,
    HarvardKyoto,
    Tamil99,
    AnjalPhonetic,
    SurathaBamini,
    PhoneticV1,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction {
    ToTamil,
    ToLatin,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SchemeInfo {
    pub id: &'static str,
    pub category: &'static str,
    pub bidirectional: bool,
}

pub const SCHEMES: &[SchemeInfo] = &[
    SchemeInfo {
        id: "iso-15919",
        category: "scholarly",
        bidirectional: true,
    },
    SchemeInfo {
        id: "madras-lexicon",
        category: "scholarly",
        bidirectional: true,
    },
    SchemeInfo {
        id: "itrans",
        category: "scholarly",
        bidirectional: true,
    },
    SchemeInfo {
        id: "harvard-kyoto",
        category: "scholarly",
        bidirectional: true,
    },
    SchemeInfo {
        id: "tamil99",
        category: "keyboard",
        bidirectional: false,
    },
    SchemeInfo {
        id: "anjal-phonetic",
        category: "phonetic",
        bidirectional: false,
    },
    SchemeInfo {
        id: "suratha-bamini",
        category: "keyboard",
        bidirectional: false,
    },
    SchemeInfo {
        id: "phonetic-v1",
        category: "phonetic",
        bidirectional: true,
    },
];

impl Scheme {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "iso-15919" => Ok(Self::Iso15919),
            "madras-lexicon" => Ok(Self::MadrasLexicon),
            "itrans" => Ok(Self::Itrans),
            "harvard-kyoto" => Ok(Self::HarvardKyoto),
            "tamil99" => Ok(Self::Tamil99),
            "anjal-phonetic" => Ok(Self::AnjalPhonetic),
            "suratha-bamini" => Ok(Self::SurathaBamini),
            "phonetic-v1" => Ok(Self::PhoneticV1),
            _ => Err("unsupported transliteration scheme".into()),
        }
    }

    pub fn id(self) -> &'static str {
        match self {
            Self::Iso15919 => "iso-15919",
            Self::MadrasLexicon => "madras-lexicon",
            Self::Itrans => "itrans",
            Self::HarvardKyoto => "harvard-kyoto",
            Self::Tamil99 => "tamil99",
            Self::AnjalPhonetic => "anjal-phonetic",
            Self::SurathaBamini => "suratha-bamini",
            Self::PhoneticV1 => "phonetic-v1",
        }
    }

    fn vowel_token(self, v: &VowelEntry) -> &'static str {
        match self {
            Self::Iso15919 => v.iso_15919,
            Self::MadrasLexicon => v.madras_lexicon,
            Self::Itrans => v.itrans,
            Self::HarvardKyoto => v.harvard_kyoto,
            Self::PhoneticV1 => v.phonetic,
            _ => "",
        }
    }

    fn consonant_token(self, c: &ConsonantEntry) -> &'static str {
        match self {
            Self::Iso15919 => c.iso_15919,
            Self::MadrasLexicon => c.madras_lexicon,
            Self::Itrans => c.itrans,
            Self::HarvardKyoto => c.harvard_kyoto,
            Self::PhoneticV1 => c.phonetic,
            _ => "",
        }
    }

    fn aytham_token(self) -> &'static str {
        match self {
            Self::Iso15919 => tables::AYTHAM_ISO,
            Self::MadrasLexicon => tables::AYTHAM_MTL,
            Self::Itrans => tables::AYTHAM_ITRANS,
            Self::HarvardKyoto => tables::AYTHAM_HK,
            Self::PhoneticV1 => tables::AYTHAM_PHONETIC,
            _ => "",
        }
    }
}

impl Direction {
    pub fn parse(value: &str) -> Result<Self, String> {
        match value {
            "to_tamil" => Ok(Self::ToTamil),
            "to_latin" => Ok(Self::ToLatin),
            _ => Err("unsupported transliteration direction".into()),
        }
    }
}

/// Transliterate text between Tamil Unicode and a scholarly/keyboard/phonetic scheme.
pub fn transliterate(text: &str, scheme: Scheme, direction: Direction) -> Result<String, String> {
    match direction {
        Direction::ToLatin => match scheme {
            Scheme::Iso15919
            | Scheme::MadrasLexicon
            | Scheme::Itrans
            | Scheme::HarvardKyoto
            | Scheme::PhoneticV1 => Ok(tamil_to_latin(text, scheme)),
            Scheme::Tamil99 | Scheme::AnjalPhonetic | Scheme::SurathaBamini => {
                Err("reverse transliteration is not supported for keyboard layout".into())
            }
        },
        Direction::ToTamil => match scheme {
            Scheme::Iso15919 | Scheme::MadrasLexicon | Scheme::Itrans | Scheme::HarvardKyoto => {
                Ok(scholarly_latin_to_tamil(text, scheme))
            }
            Scheme::Tamil99 => Ok(tamil99_to_tamil(text)),
            Scheme::AnjalPhonetic => Ok(phonetic_to_tamil(text)),
            Scheme::SurathaBamini => Ok(suratha_bamini_to_tamil(text)),
            Scheme::PhoneticV1 => Ok(phonetic_to_tamil(text)),
        },
    }
}

fn find_vowel_by_ind(ch: char) -> Option<&'static VowelEntry> {
    tables::VOWELS.iter().find(|v| v.independent == ch)
}

fn find_vowel_by_dep(ch: char) -> Option<&'static VowelEntry> {
    tables::VOWELS.iter().find(|v| v.dependent == Some(ch))
}

fn find_consonant(ch: char) -> Option<&'static ConsonantEntry> {
    tables::CONSONANTS.iter().find(|c| c.tamil == ch)
}

fn tamil_to_latin(text: &str, scheme: Scheme) -> String {
    let normalized = normalize_nfc(text);
    let chars: Vec<char> = normalized.chars().collect();
    let mut out = String::with_capacity(normalized.len());
    let mut i = 0;
    while i < chars.len() {
        let ch = chars[i];
        if let Some(cons) = find_consonant(ch) {
            out.push_str(scheme.consonant_token(cons));
            i += 1;
            if let Some(&next) = chars.get(i) {
                if next == tables::PULLI {
                    i += 1;
                } else if let Some(v) = find_vowel_by_dep(next) {
                    out.push_str(scheme.vowel_token(v));
                    i += 1;
                } else {
                    out.push('a');
                }
            } else {
                out.push('a');
            }
        } else if let Some(v) = find_vowel_by_ind(ch) {
            out.push_str(scheme.vowel_token(v));
            i += 1;
        } else if ch == tables::AYTHAM {
            out.push_str(scheme.aytham_token());
            i += 1;
        } else {
            out.push(ch);
            i += 1;
        }
    }
    out
}

fn match_longest_vowel(tail: &str, scheme: Scheme) -> Option<(usize, &'static VowelEntry)> {
    let mut best: Option<(usize, &'static VowelEntry)> = None;
    for v in tables::VOWELS {
        let tok = scheme.vowel_token(v);
        if !tok.is_empty() && tail.starts_with(tok) && best.is_none_or(|(len, _)| tok.len() > len) {
            best = Some((tok.len(), v));
        }
    }
    best
}

fn match_longest_consonant(tail: &str, scheme: Scheme) -> Option<(usize, &'static ConsonantEntry)> {
    let mut best: Option<(usize, &'static ConsonantEntry)> = None;
    for c in tables::CONSONANTS {
        let tok = scheme.consonant_token(c);
        if !tok.is_empty() && tail.starts_with(tok) && best.is_none_or(|(len, _)| tok.len() > len) {
            best = Some((tok.len(), c));
        }
    }
    best
}

fn scholarly_latin_to_tamil(text: &str, scheme: Scheme) -> String {
    let normalized = normalize_nfc(text);
    let mut out = String::with_capacity(normalized.len() * 2);
    let mut i = 0;
    let bytes = normalized.as_bytes();
    while i < bytes.len() {
        let tail = &normalized[i..];
        let ay_tok = scheme.aytham_token();
        let cons_match = match_longest_consonant(tail, scheme);
        let vowel_match = match_longest_vowel(tail, scheme);

        // Choose longest match among consonant, vowel, and aytham.
        let best_cons_len = cons_match.map_or(0, |(l, _)| l);
        let best_vowel_len = vowel_match.map_or(0, |(l, _)| l);
        let best_ay_len = if !ay_tok.is_empty() && tail.starts_with(ay_tok) {
            ay_tok.len()
        } else {
            0
        };

        if best_cons_len > 0 && best_cons_len >= best_vowel_len && best_cons_len >= best_ay_len {
            let (clen, cons) = cons_match.unwrap();
            out.push(cons.tamil);
            i += clen;
            if let Some((vlen, v)) = match_longest_vowel(&normalized[i..], scheme) {
                if let Some(dep) = v.dependent {
                    out.push(dep);
                }
                i += vlen;
            } else {
                out.push(tables::PULLI);
            }
        } else if best_vowel_len > 0 && best_vowel_len >= best_ay_len {
            let (vlen, v) = vowel_match.unwrap();
            out.push(v.independent);
            i += vlen;
        } else if best_ay_len > 0 {
            out.push(tables::AYTHAM);
            i += best_ay_len;
        } else {
            let ch = tail.chars().next().expect("non-empty tail");
            out.push(ch);
            i += ch.len_utf8();
        }
    }
    normalize_nfc(&out)
}

fn tamil99_to_tamil(text: &str) -> String {
    let mut out = String::with_capacity(text.len() * 2);
    // Track whether the immediately preceding emitted char is a bare Tamil consonant.
    let mut prev_cons: Option<char> = None;
    for ch in text.chars() {
        if ch == tables::T99_PULLI_KEY {
            if prev_cons.is_some() {
                out.push(tables::PULLI);
                prev_cons = None;
            } else {
                out.push(tables::PULLI);
            }
            continue;
        }
        if ch == tables::T99_AYTHAM_KEY {
            out.push(tables::AYTHAM);
            prev_cons = None;
            continue;
        }
        if let Some(&(_, special)) = tables::T99_SPECIAL.iter().find(|&&(k, _)| k == ch) {
            out.push_str(special);
            prev_cons = None;
            continue;
        }
        if let Some(&(_, ind, dep)) = tables::T99_VOWELS.iter().find(|&&(k, _, _)| k == ch) {
            if prev_cons.is_some() {
                // 'a' suppresses inherent-vowel continuation (prev_cons = None) without adding a sign.
                if let Some(sign) = dep {
                    out.push(sign);
                }
                prev_cons = None;
            } else {
                out.push(ind);
            }
            continue;
        }
        if let Some(&(_, cons)) = tables::T99_CONSONANTS.iter().find(|&&(k, _)| k == ch) {
            if let Some(prev) = prev_cons {
                let is_geminate = prev == cons;
                let is_homorganic = tables::T99_HOMORGANIC
                    .iter()
                    .any(|&(nasal, stop)| nasal == prev && stop == cons);
                if is_geminate || is_homorganic {
                    out.push(tables::PULLI);
                }
            }
            out.push(cons);
            prev_cons = Some(cons);
            continue;
        }
        out.push(ch);
        prev_cons = None;
    }
    normalize_nfc(&out)
}

fn suratha_bamini_to_tamil(text: &str) -> String {
    let chars: Vec<char> = text.chars().collect();
    let mut out = String::with_capacity(text.len() * 2);
    let mut i = 0;
    while i < chars.len() {
        let ch = chars[i];
        // Handle pre-base visual vowel modifiers: n (ெ), N (ே), i (ை)
        if ch == tables::SB_PRE_E || ch == tables::SB_PRE_EE || ch == tables::SB_PRE_AI {
            if let Some(&next) = chars.get(i + 1) {
                if let Some(&(_, cons)) = tables::SB_CONSONANTS.iter().find(|&&(k, _)| k == next) {
                    out.push(cons);
                    i += 2;
                    if ch == tables::SB_PRE_E {
                        if chars.get(i) == Some(&tables::SB_POST_AA) {
                            out.push('\u{0BCA}');
                            i += 1;
                        } else if chars.get(i) == Some(&tables::SB_POST_AU) {
                            out.push('\u{0BCC}');
                            i += 1;
                        } else {
                            out.push('\u{0BC6}');
                        }
                    } else if ch == tables::SB_PRE_EE {
                        if chars.get(i) == Some(&tables::SB_POST_AA) {
                            out.push('\u{0BCB}');
                            i += 1;
                        } else {
                            out.push('\u{0BC7}');
                        }
                    } else {
                        out.push('\u{0BC8}');
                    }
                    continue;
                }
            }
        }
        if let Some(&(_, cons)) = tables::SB_CONSONANTS.iter().find(|&&(k, _)| k == ch) {
            out.push(cons);
            i += 1;
            if let Some(&post) = chars.get(i) {
                if post == tables::SB_PULLI_KEY {
                    out.push(tables::PULLI);
                    i += 1;
                } else if post == tables::SB_POST_AA {
                    out.push('\u{0BBE}');
                    i += 1;
                } else if post == tables::SB_POST_I {
                    out.push('\u{0BBF}');
                    i += 1;
                } else if post == tables::SB_POST_II {
                    out.push('\u{0BC0}');
                    i += 1;
                }
            }
            continue;
        }
        if let Some(&(_, pre_u)) = tables::SB_PRECOMPOSED_U.iter().find(|&&(k, _)| k == ch) {
            out.push_str(pre_u);
            i += 1;
            continue;
        }
        if let Some(&(_, v)) = tables::SB_VOWELS.iter().find(|&&(k, _)| k == ch) {
            out.push(v);
            i += 1;
            continue;
        }
        out.push(ch);
        i += 1;
    }
    normalize_nfc(&out)
}

/// Rule-based deterministic Anjal / Phonetic v1 Roman-to-Tamil input.
fn phonetic_to_tamil(text: &str) -> String {
    const VOWEL_RULES: &[(&str, char, Option<char>)] = &[
        ("aa", '\u{0B86}', Some('\u{0BBE}')),
        ("ee", '\u{0B88}', Some('\u{0BC0}')),
        ("ii", '\u{0B88}', Some('\u{0BC0}')),
        ("oo", '\u{0B8A}', Some('\u{0BC2}')),
        ("uu", '\u{0B8A}', Some('\u{0BC2}')),
        ("ae", '\u{0B8F}', Some('\u{0BC7}')),
        ("ai", '\u{0B90}', Some('\u{0BC8}')),
        ("oa", '\u{0B93}', Some('\u{0BCB}')),
        ("au", '\u{0B94}', Some('\u{0BCC}')),
        ("ow", '\u{0B94}', Some('\u{0BCC}')),
        ("A", '\u{0B86}', Some('\u{0BBE}')),
        ("I", '\u{0B88}', Some('\u{0BC0}')),
        ("U", '\u{0B8A}', Some('\u{0BC2}')),
        ("E", '\u{0B8F}', Some('\u{0BC7}')),
        ("O", '\u{0B93}', Some('\u{0BCB}')),
        ("a", '\u{0B85}', None),
        ("i", '\u{0B87}', Some('\u{0BBF}')),
        ("u", '\u{0B89}', Some('\u{0BC1}')),
        ("e", '\u{0B8E}', Some('\u{0BC6}')),
        ("o", '\u{0B92}', Some('\u{0BCA}')),
    ];

    // Special clusters that emit a nasal+pulli + stop (like ng -> ங்க when followed by vowel, or ங்)
    const CONS_RULES: &[(&str, &str)] = &[
        ("ksh", "\u{0B95}\u{0BCD}\u{0BB7}"),
        ("sh", "\u{0BB7}"),
        ("Sh", "\u{0BB7}"),
        ("zh", "\u{0BB4}"),
        ("ch", "\u{0B9A}"),
        ("th", "\u{0BA4}"),
        ("dh", "\u{0BA4}"),
        ("nh", "\u{0BA8}"),
        ("nj", "\u{0B9E}"),
        ("ny", "\u{0B9E}"),
        ("ng", "\u{0B99}\u{0BCD}\u{0B95}"),
        ("k", "\u{0B95}"),
        ("g", "\u{0B95}"),
        ("c", "\u{0B9A}"),
        ("s", "\u{0BB8}"),
        ("j", "\u{0B9C}"),
        ("T", "\u{0B9F}"),
        ("t", "\u{0B9F}"),
        ("d", "\u{0B9F}"),
        ("N", "\u{0BA3}"),
        ("p", "\u{0BAA}"),
        ("b", "\u{0BAA}"),
        ("m", "\u{0BAE}"),
        ("y", "\u{0BAF}"),
        ("r", "\u{0BB0}"),
        ("R", "\u{0BB1}"),
        ("l", "\u{0BB2}"),
        ("L", "\u{0BB3}"),
        ("z", "\u{0BB4}"),
        ("v", "\u{0BB5}"),
        ("w", "\u{0BB5}"),
        ("S", "\u{0BB6}"),
        ("h", "\u{0BB9}"),
    ];

    let mut out = String::with_capacity(text.len() * 2);
    let mut i = 0;
    let bytes = text.as_bytes();
    let mut at_word_start = true;
    while i < bytes.len() {
        let tail = &text[i..];
        if tail.starts_with("sri") || tail.starts_with("shri") {
            out.push_str("\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}");
            i += if tail.starts_with("shri") { 4 } else { 3 };
            at_word_start = false;
            continue;
        }
        if tail.starts_with('q') {
            out.push(tables::AYTHAM);
            i += 1;
            at_word_start = false;
            continue;
        }
        // Check consonant rules first (longest match), plus positional 'n' (word-initial -> ந, else -> ன; before th/dh -> ந)
        let matched_cons: Option<(usize, &str)> = if tail.starts_with("nth")
            || tail.starts_with("ndh")
        {
            Some((1, "\u{0BA8}"))
        } else if let Some(&(pat, tam)) = CONS_RULES.iter().find(|&&(p, _)| tail.starts_with(p)) {
            Some((pat.len(), tam))
        } else if tail.starts_with('n') {
            Some((
                1,
                if at_word_start {
                    "\u{0BA8}"
                } else {
                    "\u{0BA9}"
                },
            ))
        } else {
            None
        };

        if let Some((clen, tam)) = matched_cons {
            out.push_str(tam);
            i += clen;
            at_word_start = false;
            if let Some(&(vpat, _, dep)) = VOWEL_RULES
                .iter()
                .find(|&&(p, _, _)| text[i..].starts_with(p))
            {
                if let Some(sign) = dep {
                    out.push(sign);
                }
                i += vpat.len();
            } else {
                out.push(tables::PULLI);
            }
            continue;
        }
        if let Some(&(vpat, ind, _)) = VOWEL_RULES.iter().find(|&&(p, _, _)| tail.starts_with(p)) {
            out.push(ind);
            i += vpat.len();
            at_word_start = false;
            continue;
        }
        let ch = tail.chars().next().expect("non-empty tail");
        out.push(ch);
        i += ch.len_utf8();
        at_word_start = !ch.is_alphabetic();
    }
    normalize_nfc(&out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    const SCHOLARLY: [Scheme; 4] = [
        Scheme::Iso15919,
        Scheme::MadrasLexicon,
        Scheme::Itrans,
        Scheme::HarvardKyoto,
    ];

    const ALL_SCHEMES: [Scheme; 8] = [
        Scheme::Iso15919,
        Scheme::MadrasLexicon,
        Scheme::Itrans,
        Scheme::HarvardKyoto,
        Scheme::Tamil99,
        Scheme::AnjalPhonetic,
        Scheme::SurathaBamini,
        Scheme::PhoneticV1,
    ];

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(10_000))]
        #[test]
        fn arbitrary_utf8_never_panics_across_all_schemes(text in ".{0,64}") {
            for scheme in ALL_SCHEMES {
                let _ = transliterate(&text, scheme, Direction::ToTamil);
                let _ = transliterate(&text, scheme, Direction::ToLatin);
            }
        }
        #[test]
        fn scholarly_schemes_roundtrip_valid_tamil_words(
            parts in prop::collection::vec(0usize..58, 0..20),
            scheme_idx in 0usize..4,
        ) {
            let scheme = SCHOLARLY[scheme_idx];
            let mut tamil = String::new();
            let mut at_word_start = true;
            for p in parts {
                match p {
                    0..=11 if at_word_start => {
                        tamil.push(tables::VOWELS[p].independent);
                        at_word_start = false;
                    }
                    12 => {
                        tamil.push(tables::AYTHAM);
                        at_word_start = false;
                    }
                    13..=35 => {
                        tamil.push(tables::CONSONANTS[p - 13].tamil);
                        at_word_start = false;
                    }
                    36..=45 => {
                        tamil.push(tables::CONSONANTS[p - 36].tamil);
                        tamil.push(tables::PULLI);
                        at_word_start = false;
                    }
                    46..=56 => {
                        tamil.push(tables::CONSONANTS[(p - 46) % 23].tamil);
                        if let Some(dep) = tables::VOWELS[(p - 46) + 1].dependent {
                            tamil.push(dep);
                        }
                        at_word_start = false;
                    }
                    _ => {
                        tamil.push(' ');
                        at_word_start = true;
                    }
                }
            }
            let latin = transliterate(&tamil, scheme, Direction::ToLatin).unwrap();
            let back = transliterate(&latin, scheme, Direction::ToTamil).unwrap();
            prop_assert_eq!(back, normalize_nfc(&tamil));
        }
    }
}
