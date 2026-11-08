//! Orthographic text repair engine for corrupted and legacy Tamil inputs.
#![forbid(unsafe_code)]

use crate::types::{RepairDiagnostics, RepairOptions, RepairResult};

const PULLI: char = '\u{0BCD}';
const KOMBU_E: char = '\u{0BC6}';
const KOMBU_EE: char = '\u{0BC7}';
const KOMBU_AI: char = '\u{0BC8}';
const VOWEL_SIGN_AA: char = '\u{0BBE}';
const LENGTH_MARK: char = '\u{0BD7}';
const VOWEL_SIGN_O: char = '\u{0BCA}';
const VOWEL_SIGN_OO: char = '\u{0BCB}';
const VOWEL_SIGN_AU: char = '\u{0BCC}';
const SOFT_HYPHEN: char = '\u{00AD}';
const ZWJ_CODE: u32 = 0x200D;
const ZWNJ_CODE: u32 = 0x200C;
const TAMIL_LA: char = '\u{0BB3}';

fn is_consonant_scalar(c: char) -> bool {
    matches!(
        c,
        '\u{0B95}'
            | '\u{0B99}'
            | '\u{0B9A}'
            | '\u{0B9C}'
            | '\u{0B9E}'
            | '\u{0B9F}'
            | '\u{0BA3}'
            | '\u{0BA4}'
            | '\u{0BA8}'
            | '\u{0BA9}'
            | '\u{0BAA}'
            | '\u{0BAE}'
            | '\u{0BAF}'
            | '\u{0BB0}'
            | '\u{0BB1}'
            | '\u{0BB2}'
            | '\u{0BB3}'
            | '\u{0BB4}'
            | '\u{0BB5}'
            | '\u{0BB6}'
            | '\u{0BB7}'
            | '\u{0BB8}'
            | '\u{0BB9}'
    )
}

fn match_consonant_prefix(s: &str) -> Option<(&str, usize)> {
    if s.starts_with("\u{0B95}\u{0BCD}\u{0BB7}") {
        return Some(("\u{0B95}\u{0BCD}\u{0BB7}", "\u{0B95}\u{0BCD}\u{0BB7}".len()));
    }
    if let Some(c) = s.chars().next() {
        if is_consonant_scalar(c) {
            return Some((&s[..c.len_utf8()], c.len_utf8()));
        }
    }
    None
}

/// Repair orthographic corruptions (duplicate pullis, visual kombus, soft-hyphens) in Tamil text.
pub fn repair_tamil_text(text: &str, options: &RepairOptions) -> RepairResult {
    let mut out = String::with_capacity(text.len());
    let mut duplicate_pulli_count = 0;
    let mut visual_kombu_count = 0;
    let mut stripped_control_count = 0;

    let chars: Vec<char> = text.chars().collect();
    let mut i = 0;

    while i < chars.len() {
        let c = chars[i];

        // 1. Check control characters and soft hyphens
        if options.strip_soft_hyphens
            && (c == SOFT_HYPHEN || (c < ' ' && c != '\t' && c != '\n' && c != '\r'))
        {
            stripped_control_count += 1;
            i += 1;
            continue;
        }

        // 2. Check joiners if requested
        if options.strip_joiners && (c as u32 == ZWJ_CODE || c as u32 == ZWNJ_CODE) {
            stripped_control_count += 1;
            i += 1;
            continue;
        }

        // 3. Check duplicate pulli
        if options.collapse_duplicate_pulli && c == PULLI && out.ends_with(PULLI) {
            duplicate_pulli_count += 1;
            i += 1;
            continue;
        }

        // 4. Check visual left-kombu placed before consonant
        if options.reorder_visual_kombu && (c == KOMBU_E || c == KOMBU_EE || c == KOMBU_AI) {
            let remainder: String = chars[i + 1..].iter().collect();
            if let Some((base_cons, len_bytes)) = match_consonant_prefix(&remainder) {
                let cons_char_count = remainder[..len_bytes].chars().count();
                let after_cons_idx = i + 1 + cons_char_count;
                let next_char = chars.get(after_cons_idx).copied();

                if c == KOMBU_E && next_char == Some(VOWEL_SIGN_AA) {
                    // ெ + C + ா -> C + ொ
                    out.push_str(base_cons);
                    out.push(VOWEL_SIGN_O);
                    visual_kombu_count += 1;
                    i = after_cons_idx + 1;
                    continue;
                } else if c == KOMBU_EE && next_char == Some(VOWEL_SIGN_AA) {
                    // ே + C + ா -> C + ோ
                    out.push_str(base_cons);
                    out.push(VOWEL_SIGN_OO);
                    visual_kombu_count += 1;
                    i = after_cons_idx + 1;
                    continue;
                } else if c == KOMBU_E
                    && (next_char == Some(LENGTH_MARK) || next_char == Some(TAMIL_LA))
                {
                    // ெ + C + ௗ/ள -> C + ௌ
                    out.push_str(base_cons);
                    out.push(VOWEL_SIGN_AU);
                    visual_kombu_count += 1;
                    i = after_cons_idx + 1;
                    continue;
                } else {
                    // Normal kombu + consonant swap: ெ/ே/ை + C -> C + ெ/ே/ை
                    out.push_str(base_cons);
                    out.push(c);
                    visual_kombu_count += 1;
                    i = after_cons_idx;
                    continue;
                }
            }
        }

        out.push(c);
        i += 1;
    }

    // Apply NFC normalization to clean output
    let canonical = tamil_core::normalize_nfc(&out);
    let total_repairs = duplicate_pulli_count + visual_kombu_count + stripped_control_count;

    RepairResult {
        text: canonical,
        diagnostics: RepairDiagnostics {
            duplicate_pulli_count,
            visual_kombu_count,
            stripped_control_count,
            total_repairs,
        },
    }
}
