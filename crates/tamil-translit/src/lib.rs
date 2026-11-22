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

pub const DEFAULT_SUGGEST_LIMIT: usize = 5;
pub const MAX_SUGGEST_LIMIT: usize = 10;

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
            Scheme::AnjalPhonetic => Ok(phonetic_scheme_to_tamil(text, &ANJAL_TABLE)),
            Scheme::SurathaBamini => Ok(suratha_bamini_to_tamil(text)),
            Scheme::PhoneticV1 => Ok(phonetic_scheme_to_tamil(text, &PHONETIC_V1_TABLE)),
        },
    }
}

/// Generate primary Tamil transliteration plus phonotactically valid Mayangoli alternatives.
pub fn transliterate_suggest(
    text: &str,
    scheme: Scheme,
    limit: usize,
) -> Result<Vec<String>, String> {
    if limit == 0 {
        return Err("expected a positive integer limit".into());
    }
    let max_items = limit.min(MAX_SUGGEST_LIMIT);
    let primary = transliterate(text, scheme, Direction::ToTamil)?;
    if primary.trim().is_empty() {
        return Ok(Vec::new());
    }
    if matches!(scheme, Scheme::PhoneticV1 | Scheme::AnjalPhonetic)
        || text.chars().any(|c| ('\u{0B80}'..='\u{0BFF}').contains(&c))
    {
        Ok(mayangoli_variants(&primary, max_items))
    } else {
        Ok(vec![primary])
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
    let mut at_word_start = true;
    while i < chars.len() {
        let ch = chars[i];
        if let Some(cons) = find_consonant(ch) {
            if scheme == Scheme::PhoneticV1
                && ch == '\u{0BA8}'
                && (at_word_start
                    || (chars.get(i + 1) == Some(&tables::PULLI)
                        && chars.get(i + 2) == Some(&'\u{0BA4}')))
            {
                out.push('n');
            } else {
                out.push_str(scheme.consonant_token(cons));
            }
            i += 1;
            at_word_start = false;
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
            at_word_start = false;
        } else if ch == tables::AYTHAM {
            out.push_str(scheme.aytham_token());
            i += 1;
            at_word_start = false;
        } else {
            out.push(ch);
            i += 1;
            at_word_start = !ch.is_alphabetic();
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

struct PhoneticTable {
    sri_tokens: &'static [&'static str],
    aytham_keys: &'static [char],
    initial_n: &'static str,
    medial_n: &'static str,
    contextual_clusters: &'static [(&'static str, &'static str)],
    vowels: &'static [(&'static str, char, Option<char>)],
    consonants: &'static [(&'static str, &'static str)],
}

const ANJAL_TABLE: PhoneticTable = PhoneticTable {
    sri_tokens: tables::ANJAL_SRI_TOKENS,
    aytham_keys: tables::ANJAL_AYTHAM_KEYS,
    initial_n: tables::ANJAL_INITIAL_N,
    medial_n: tables::ANJAL_MEDIAL_N,
    contextual_clusters: tables::ANJAL_CONTEXTUAL_CLUSTERS,
    vowels: tables::ANJAL_VOWELS,
    consonants: tables::ANJAL_CONSONANTS,
};

const PHONETIC_V1_TABLE: PhoneticTable = PhoneticTable {
    sri_tokens: tables::PHONETIC_V1_SRI_TOKENS,
    aytham_keys: tables::PHONETIC_V1_AYTHAM_KEYS,
    initial_n: tables::PHONETIC_V1_INITIAL_N,
    medial_n: tables::PHONETIC_V1_MEDIAL_N,
    contextual_clusters: tables::PHONETIC_V1_CONTEXTUAL_CLUSTERS,
    vowels: tables::PHONETIC_V1_VOWELS,
    consonants: tables::PHONETIC_V1_CONSONANTS,
};

/// Rule-based deterministic Anjal / Phonetic v1 Roman-to-Tamil input.
fn phonetic_scheme_to_tamil(text: &str, cfg: &PhoneticTable) -> String {
    let mut out = String::with_capacity(text.len() * 2);
    let mut i = 0;
    let bytes = text.as_bytes();
    let mut at_word_start = true;
    while i < bytes.len() {
        let tail = &text[i..];
        if let Some(&tok) = cfg.sri_tokens.iter().find(|&&tok| tail.starts_with(tok)) {
            out.push_str(tables::SRI);
            i += tok.len();
            at_word_start = false;
            continue;
        }
        if let Some(&k) = cfg.aytham_keys.iter().find(|&&k| tail.starts_with(k)) {
            out.push(tables::AYTHAM);
            i += k.len_utf8();
            at_word_start = false;
            continue;
        }
        // Contextual clusters (e.g. medial ng/nj followed by a vowel -> ங்க/ஞ்ச)
        let contextual_match =
            if !at_word_start && !tail.starts_with("ngg") && !tail.starts_with("njj") {
                cfg.contextual_clusters
                    .iter()
                    .find(|&&(pat, _)| {
                        tail.starts_with(pat)
                            && cfg
                                .vowels
                                .iter()
                                .any(|&(vpat, _, _)| tail[pat.len()..].starts_with(vpat))
                    })
                    .map(|&(pat, tam)| (pat.len(), tam))
            } else {
                None
            };

        let matched_cons: Option<(usize, &str)> = if contextual_match.is_some() {
            contextual_match
        } else if let Some(&(pat, tam)) = cfg.consonants.iter().find(|&&(p, _)| tail.starts_with(p))
        {
            Some((pat.len(), tam))
        } else if tail.starts_with('n') {
            Some((
                1,
                if at_word_start {
                    cfg.initial_n
                } else {
                    cfg.medial_n
                },
            ))
        } else {
            None
        };

        if let Some((clen, tam)) = matched_cons {
            out.push_str(tam);
            i += clen;
            at_word_start = false;
            if let Some(&(vpat, _, dep)) = cfg
                .vowels
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
        if let Some(&(vpat, ind, _)) = cfg.vowels.iter().find(|&&(p, _, _)| tail.starts_with(p)) {
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

fn is_tamil_word_char(ch: char) -> bool {
    matches!(ch, '\u{0B82}'..='\u{0BCD}' | '\u{0BD7}') || ch.is_alphabetic()
}

enum MayangoliSegment {
    Fixed(String),
    Variable(&'static [&'static str]),
}

fn push_fixed_str(segments: &mut Vec<MayangoliSegment>, text: &str) {
    if let Some(MayangoliSegment::Fixed(existing)) = segments.last_mut() {
        existing.push_str(text);
    } else {
        segments.push(MayangoliSegment::Fixed(text.to_owned()));
    }
}

fn push_fixed_char(segments: &mut Vec<MayangoliSegment>, ch: char) {
    if let Some(MayangoliSegment::Fixed(existing)) = segments.last_mut() {
        existing.push(ch);
    } else {
        segments.push(MayangoliSegment::Fixed(ch.to_string()));
    }
}

fn render_segments(segments: &[MayangoliSegment], choices: &[usize]) -> String {
    let mut rendered = String::new();
    for (idx, seg) in segments.iter().enumerate() {
        match seg {
            MayangoliSegment::Fixed(text) => rendered.push_str(text),
            MayangoliSegment::Variable(opts) => rendered.push_str(opts[choices[idx]]),
        }
    }
    normalize_nfc(&rendered)
}

fn push_unique_candidate(out: &mut Vec<String>, candidate: String, limit: usize) {
    if out.len() < limit && !out.contains(&candidate) {
        out.push(candidate);
    }
}

fn emit_sub_combinations(
    segments: &[MayangoliSegment],
    active_vars: &[usize],
    pos: usize,
    subs_left: usize,
    choices: &mut [usize],
    out: &mut Vec<String>,
    limit: usize,
) {
    if out.len() >= limit {
        return;
    }
    if subs_left == 0 {
        push_unique_candidate(out, render_segments(segments, choices), limit);
        return;
    }
    if pos + subs_left > active_vars.len() {
        return;
    }
    let seg_idx = active_vars[pos];
    if let MayangoliSegment::Variable(opts) = segments[seg_idx] {
        for choice in 1..opts.len() {
            choices[seg_idx] = choice;
            emit_sub_combinations(
                segments,
                active_vars,
                pos + 1,
                subs_left - 1,
                choices,
                out,
                limit,
            );
            if out.len() >= limit {
                choices[seg_idx] = 0;
                return;
            }
        }
        choices[seg_idx] = 0;
    }
    emit_sub_combinations(
        segments,
        active_vars,
        pos + 1,
        subs_left,
        choices,
        out,
        limit,
    );
}

fn mayangoli_variants(tamil_text: &str, limit: usize) -> Vec<String> {
    let normalized = normalize_nfc(tamil_text);
    let chars: Vec<char> = normalized.chars().collect();
    let mut segments: Vec<MayangoliSegment> = Vec::new();
    let mut i = 0;

    while i < chars.len() {
        let ch = chars[i];
        let at_word_start = i == 0 || !is_tamil_word_char(chars[i - 1]);

        if i + 2 < chars.len() && chars[i + 1] == tables::PULLI {
            let next = chars[i + 2];
            match (ch, next) {
                ('\u{0BA8}', '\u{0BA4}')
                | ('\u{0BA3}', '\u{0B9F}')
                | ('\u{0BA9}', '\u{0BB1}')
                | ('\u{0BB1}', '\u{0BB1}') => {
                    let cluster: String = chars[i..i + 3].iter().collect();
                    push_fixed_str(&mut segments, &cluster);
                    i += 3;
                    continue;
                }
                ('\u{0BA9}', '\u{0BA9}') if !at_word_start => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BA9}\u{0BCD}\u{0BA9}",
                        "\u{0BA3}\u{0BCD}\u{0BA3}",
                    ]));
                    i += 3;
                    continue;
                }
                ('\u{0BA3}', '\u{0BA3}') if !at_word_start => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BA3}\u{0BCD}\u{0BA3}",
                        "\u{0BA9}\u{0BCD}\u{0BA9}",
                    ]));
                    i += 3;
                    continue;
                }
                ('\u{0BB2}', '\u{0BB2}') if !at_word_start => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BB2}\u{0BCD}\u{0BB2}",
                        "\u{0BB3}\u{0BCD}\u{0BB3}",
                    ]));
                    i += 3;
                    continue;
                }
                ('\u{0BB3}', '\u{0BB3}') if !at_word_start => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BB3}\u{0BCD}\u{0BB3}",
                        "\u{0BB2}\u{0BCD}\u{0BB2}",
                    ]));
                    i += 3;
                    continue;
                }
                _ => {}
            }
        }

        if !at_word_start {
            match ch {
                '\u{0BA9}' => {
                    segments.push(MayangoliSegment::Variable(&["\u{0BA9}", "\u{0BA3}"]));
                    i += 1;
                    continue;
                }
                '\u{0BA3}' => {
                    segments.push(MayangoliSegment::Variable(&["\u{0BA3}", "\u{0BA9}"]));
                    i += 1;
                    continue;
                }
                '\u{0BB2}' => {
                    if chars.get(i + 1) == Some(&tables::PULLI) {
                        segments.push(MayangoliSegment::Variable(&[
                            "\u{0BB2}", "\u{0BB3}", "\u{0BB4}",
                        ]));
                    } else {
                        segments.push(MayangoliSegment::Variable(&[
                            "\u{0BB2}", "\u{0BB4}", "\u{0BB3}",
                        ]));
                    }
                    i += 1;
                    continue;
                }
                '\u{0BB4}' => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BB4}", "\u{0BB2}", "\u{0BB3}",
                    ]));
                    i += 1;
                    continue;
                }
                '\u{0BB3}' => {
                    segments.push(MayangoliSegment::Variable(&[
                        "\u{0BB3}", "\u{0BB2}", "\u{0BB4}",
                    ]));
                    i += 1;
                    continue;
                }
                '\u{0BB0}' if chars.get(i + 1) != Some(&tables::PULLI) => {
                    segments.push(MayangoliSegment::Variable(&["\u{0BB0}", "\u{0BB1}"]));
                    i += 1;
                    continue;
                }
                '\u{0BB1}' if chars.get(i + 1) != Some(&tables::PULLI) => {
                    segments.push(MayangoliSegment::Variable(&["\u{0BB1}", "\u{0BB0}"]));
                    i += 1;
                    continue;
                }
                _ => {}
            }
        }

        push_fixed_char(&mut segments, ch);
        i += 1;
    }

    let var_indices: Vec<usize> = segments
        .iter()
        .enumerate()
        .filter_map(|(idx, seg)| matches!(seg, MayangoliSegment::Variable(_)).then_some(idx))
        .collect();

    let mut choices = vec![0usize; segments.len()];
    let mut out = Vec::with_capacity(limit);
    push_unique_candidate(&mut out, render_segments(&segments, &choices), limit);
    if var_indices.is_empty() || out.len() >= limit {
        return out;
    }

    let active_vars = &var_indices[..var_indices.len().min(4)];

    // Distance 1: breadth-first across choice tiers (first alt per slot, then second alt per slot)
    for choice_tier in 1..=2usize {
        for &seg_idx in active_vars {
            if let MayangoliSegment::Variable(opts) = segments[seg_idx] {
                if choice_tier < opts.len() {
                    choices[seg_idx] = choice_tier;
                    push_unique_candidate(&mut out, render_segments(&segments, &choices), limit);
                    choices[seg_idx] = 0;
                    if out.len() >= limit {
                        return out;
                    }
                }
            }
        }
    }

    // Distance >= 2: multi-slot combinations up to active slot count
    for dist in 2..=active_vars.len() {
        emit_sub_combinations(
            &segments,
            active_vars,
            0,
            dist,
            &mut choices,
            &mut out,
            limit,
        );
        if out.len() >= limit {
            break;
        }
    }

    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;

    #[test]
    fn mayangoli_suggestions_respect_phonotactics() {
        assert_eq!(
            transliterate_suggest("vanakkam", Scheme::PhoneticV1, 5).unwrap(),
            vec!["வனக்கம்", "வணக்கம்"]
        );
        assert_eq!(
            transliterate_suggest("malai", Scheme::PhoneticV1, 5).unwrap(),
            vec!["மலை", "மழை", "மளை"]
        );
        assert_eq!(
            transliterate_suggest("manam", Scheme::PhoneticV1, 5).unwrap(),
            vec!["மனம்", "மணம்"]
        );
        assert_eq!(
            transliterate_suggest("karai", Scheme::PhoneticV1, 5).unwrap(),
            vec!["கரை", "கறை"]
        );
        assert_eq!(
            transliterate_suggest("palli", Scheme::PhoneticV1, 5).unwrap(),
            vec!["பல்லி", "பள்ளி"]
        );
        assert_eq!(
            transliterate_suggest("anna", Scheme::PhoneticV1, 5).unwrap(),
            vec!["அன்ன", "அண்ண"]
        );
        assert_eq!(
            transliterate_suggest("thamil", Scheme::PhoneticV1, 5).unwrap(),
            vec!["தமில்", "தமிள்", "தமிழ்"]
        );
        assert_eq!(
            transliterate_suggest("avargal", Scheme::PhoneticV1, 5).unwrap(),
            vec!["அவர்கல்", "அவர்கள்", "அவர்கழ்"]
        );
        assert_eq!(
            transliterate_suggest("nandri", Scheme::PhoneticV1, 5).unwrap(),
            vec!["நன்றி"]
        );
        assert_eq!(
            transliterate_suggest("avar", Scheme::PhoneticV1, 5).unwrap(),
            vec!["அவர்"]
        );
        assert!(transliterate_suggest("vanakkam", Scheme::PhoneticV1, 0).is_err());
    }

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
