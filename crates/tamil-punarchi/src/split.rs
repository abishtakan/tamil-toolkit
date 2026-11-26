//! Dictionary-free reverse Sandhi candidate generator (`punarchi_split_candidates`).
//!
//! Covers all 28 reversible surface pattern families from `research/05-precedence-and-inverse-matrix.md` §3,
//! strictly aligned to `tamil_core::Letters` written-unit boundaries and dual-pruned by:
//! 1. Nannool 102-108 *Mozhi-muthal* / *Mozhi-eetru* phonotactics (`phonology.rs`), and
//! 2. Forward-join verification (`pipeline::punarchi_join`).

use crate::context::{
    ContextSubtype, GrammaticalRelation, LexicalClass, PunarchiContext, PunarchiError,
    PunarchiProfile, SplitCandidate, MAX_SPLIT_SURFACE_BYTES,
};
use crate::phonology::{
    is_independent_uyir, is_native_mei, is_valid_mozhi_eetru, is_valid_mozhi_muthal,
    is_vallinam_initial_unit, unit_mei, unit_vowel,
};
use crate::pipeline::punarchi_join;
use crate::tables;
use std::collections::HashSet;
use tamil_core::{compose_uyirmei, is_mei, split_uyirmei, Letters};
use tamil_norm::normalize_nfc;

#[derive(Debug, Clone)]
struct UnitSpan<'a> {
    text: &'a str,
    byte_start: usize,
}

#[derive(Debug, Clone)]
struct RawProposal {
    first: String,
    second: String,
    split_byte: usize,
    split_unit: usize,
    extra_contexts: Vec<PunarchiContext>,
}

/// Generate dual-pruned, forward-verified single-boundary reverse Sandhi split candidates.
pub fn punarchi_split_candidates(
    surface: &str,
    profile: PunarchiProfile,
    poetic: bool,
) -> Result<Vec<SplitCandidate>, PunarchiError> {
    if surface.len() > MAX_SPLIT_SURFACE_BYTES {
        return Err(PunarchiError::SurfaceTooLong);
    }
    if surface.trim().is_empty() {
        return Ok(Vec::new());
    }
    // Reject explicit joiner / non-Tamil surface strings cleanly with `[]`.
    if surface
        .chars()
        .any(|c| c as u32 == 0x200C || c as u32 == 0x200D)
    {
        return Ok(Vec::new());
    }

    let surface_nfc = normalize_nfc(surface);
    let spans = collect_unit_spans(&surface_nfc);
    if spans.len() < 2 {
        return Ok(Vec::new());
    }
    if !spans.iter().all(|u| is_tamil_unit(u.text)) {
        return Ok(Vec::new());
    }

    let mut proposals: Vec<RawProposal> = Vec::new();

    // Families 1-22 & 27-28: structural written-unit boundary inversions.
    propose_structural_splits(&spans, &mut proposals);

    // Families 23-26: Chariyai, case+um, oblique pronouns, closed-class & poetic inversions.
    propose_chariyai_and_closed_class(&surface_nfc, &spans, poetic, &mut proposals);

    // Deduplicate raw `(first, second, split_byte)` proposals before running forward verification.
    let mut verified: Vec<SplitCandidate> = Vec::new();
    let mut seen_out: HashSet<(String, String, u16)> = HashSet::new();
    let mut seen_raw: HashSet<(String, String, usize)> = HashSet::new();

    for prop in proposals {
        if prop.split_unit == 0 || prop.split_unit >= spans.len() {
            continue;
        }
        if prop.first.is_empty() || prop.second.is_empty() {
            continue;
        }
        if !passes_phonotactics(&prop.first, &prop.second) {
            continue;
        }
        let raw_key = (prop.first.clone(), prop.second.clone(), prop.split_byte);
        if !seen_raw.insert(raw_key) {
            continue;
        }

        verify_and_collect(
            &surface_nfc,
            &prop,
            profile,
            poetic,
            &mut seen_out,
            &mut verified,
        );
    }

    verified.sort_by(|a, b| {
        (a.split_byte, a.sutra, a.first.as_str(), a.second.as_str()).cmp(&(
            b.split_byte,
            b.sutra,
            b.first.as_str(),
            b.second.as_str(),
        ))
    });

    Ok(verified)
}

fn collect_unit_spans(s: &str) -> Vec<UnitSpan<'_>> {
    let mut out = Vec::new();
    let mut offset = 0_usize;
    for unit in Letters::new(s) {
        out.push(UnitSpan {
            text: unit,
            byte_start: offset,
        });
        offset += unit.len();
    }
    out
}

fn is_tamil_unit(unit: &str) -> bool {
    unit.chars()
        .next()
        .is_some_and(|c| ('\u{0B82}'..='\u{0BD7}').contains(&c))
}

fn slice_units(spans: &[UnitSpan<'_>], start: usize, end: usize) -> String {
    let mut out = String::new();
    for u in &spans[start..end] {
        out.push_str(u.text);
    }
    out
}

fn passes_phonotactics(first: &str, second: &str) -> bool {
    if !is_valid_mozhi_muthal(second, Some(first)) {
        return false;
    }
    // Allow root `ந்`-final verbal noun (`பொருந்`, Sutra 207/208) alongside standard `107-108` finals.
    is_valid_mozhi_eetru(first) || first.ends_with("ந்")
}

fn ctx_rel(relation: GrammaticalRelation, poetic: bool) -> PunarchiContext {
    PunarchiContext {
        relation,
        subtype: None,
        lexical_class: None,
        poetic,
    }
}

fn ctx_class(
    relation: GrammaticalRelation,
    lexical_class: LexicalClass,
    poetic: bool,
) -> PunarchiContext {
    PunarchiContext {
        relation,
        subtype: None,
        lexical_class: Some(lexical_class),
        poetic,
    }
}

fn ctx_sub(
    relation: GrammaticalRelation,
    subtype: ContextSubtype,
    poetic: bool,
) -> PunarchiContext {
    PunarchiContext {
        relation,
        subtype: Some(subtype),
        lexical_class: None,
        poetic,
    }
}

fn verify_and_collect(
    surface_nfc: &str,
    prop: &RawProposal,
    profile: PunarchiProfile,
    poetic: bool,
    seen_out: &mut HashSet<(String, String, u16)>,
    verified: &mut Vec<SplitCandidate>,
) {
    let mut contexts = vec![
        ctx_rel(GrammaticalRelation::Unspecified, poetic),
        ctx_rel(GrammaticalRelation::Alvazhi, poetic),
        ctx_rel(GrammaticalRelation::Vetrumai, poetic),
    ];
    for extra in &prop.extra_contexts {
        let mut c = extra.clone();
        c.poetic = poetic;
        contexts.push(c);
    }

    for ctx in contexts {
        let Ok(res) = punarchi_join(&prop.first, &prop.second, &ctx, profile) else {
            continue;
        };

        if res.surface == surface_nfc {
            push_verified_candidate(prop, res.transform, res.steps, seen_out, verified);
        }
        for alt in res.alternatives {
            if alt.poetic && !poetic {
                continue;
            }
            if alt.surface == surface_nfc {
                push_verified_candidate(prop, alt.transform, alt.steps, seen_out, verified);
            }
        }
    }
}

fn push_verified_candidate(
    prop: &RawProposal,
    transform: crate::context::AlterationKind,
    steps: Vec<crate::context::DerivationStep>,
    seen_out: &mut HashSet<(String, String, u16)>,
    verified: &mut Vec<SplitCandidate>,
) {
    let primary_step = steps
        .iter()
        .find(|s| s.sutra != 204 && s.sutra != 153)
        .or_else(|| steps.first());
    let Some(step) = primary_step else {
        return;
    };
    let sutra = step.sutra;
    let rule_id = step.rule_id.clone();
    let key = (prop.first.clone(), prop.second.clone(), sutra);
    if !seen_out.insert(key) {
        return;
    }
    verified.push(SplitCandidate {
        first: prop.first.clone(),
        second: prop.second.clone(),
        sutra,
        rule_id,
        transform,
        steps,
        split_byte: prop.split_byte,
        split_unit: prop.split_unit,
    });
}

fn push_plain(
    proposals: &mut Vec<RawProposal>,
    first: String,
    second: String,
    split_byte: usize,
    split_unit: usize,
) {
    proposals.push(RawProposal {
        first,
        second,
        split_byte,
        split_unit,
        extra_contexts: Vec::new(),
    });
}

fn push_with_ctx(
    proposals: &mut Vec<RawProposal>,
    first: String,
    second: String,
    split_byte: usize,
    split_unit: usize,
    extra_contexts: Vec<PunarchiContext>,
) {
    proposals.push(RawProposal {
        first,
        second,
        split_byte,
        split_unit,
        extra_contexts,
    });
}

fn replace_first_mei(unit: &str, new_mei: &str) -> Option<String> {
    let parts = split_uyirmei(unit).ok()?;
    compose_uyirmei(new_mei, &parts.uyir).ok()
}

/// Patterns 1-22 & 27-28: iterate every internal written-unit boundary `1 <= i < n`.
fn propose_structural_splits(spans: &[UnitSpan<'_>], proposals: &mut Vec<RawProposal>) {
    let n = spans.len();

    for i in 1..n {
        let split_byte = spans[i].byte_start;
        let split_unit = i;
        let prefix = slice_units(spans, 0, i);
        let suffix = slice_units(spans, i, n);
        let cur = spans[i].text;
        let prev = spans[i - 1].text;

        // Pattern 1: Direct written-unit boundary (`153, 158-161, 167, 171, 176, 178-179, 181-182, 201, 209, 211-216, 224, 226-227, 230, 235`).
        let mut p1_extra = Vec::new();
        if prev == "ண்" {
            p1_extra.push(ctx_class(
                GrammaticalRelation::Vetrumai,
                LexicalClass::BranchName,
                false,
            ));
        }
        if prev == "ன்" {
            p1_extra.push(ctx_class(
                GrammaticalRelation::Vetrumai,
                LexicalClass::BranchName,
                false,
            ));
        }
        if prev == "ல்" || prev == "ள்" {
            p1_extra.push(ctx_class(
                GrammaticalRelation::Alvazhi,
                LexicalClass::VerbalNounDerived,
                false,
            ));
        }
        if matches!(
            unit_vowel(prev).as_deref(),
            Some("இ" | "ஐ" | "அ" | "ஆ" | "ஏ" | "ஓ" | "உ")
        ) {
            p1_extra.push(ctx_class(
                GrammaticalRelation::Alvazhi,
                LexicalClass::NonRationalNoun,
                false,
            ));
            p1_extra.push(ctx_class(
                GrammaticalRelation::Vetrumai,
                LexicalClass::RationalNoun,
                false,
            ));
            p1_extra.push(ctx_class(
                GrammaticalRelation::Alvazhi,
                LexicalClass::CliticParticle,
                false,
            ));
            p1_extra.push(ctx_class(
                GrammaticalRelation::Alvazhi,
                LexicalClass::Interrogative,
                false,
            ));
            p1_extra.push(ctx_class(
                GrammaticalRelation::Alvazhi,
                LexicalClass::NegativePluralVerb,
                false,
            ));
            p1_extra.push(ctx_sub(
                GrammaticalRelation::Alvazhi,
                ContextSubtype::Vinaithogai,
                false,
            ));
            p1_extra.push(ctx_sub(
                GrammaticalRelation::Alvazhi,
                ContextSubtype::Viyankol,
                false,
            ));
            p1_extra.push(ctx_sub(
                GrammaticalRelation::Alvazhi,
                ContextSubtype::SecondPersonVerb,
                false,
            ));
        }
        push_with_ctx(
            proposals,
            prefix.clone(),
            suffix.clone(),
            split_byte,
            split_unit,
            p1_extra,
        );
        // Sutra 183 doubled `ட்டு`/`ற்று` before non-Vallinam consonants (`ஆட்டுநன்று -> ஆடு + நன்று`, `ஆற்றுநீர் -> ஆறு + நீர்`):
        if let Some(base) = prefix.strip_suffix("ட்டு") {
            push_plain(
                proposals,
                format!("{base}டு"),
                suffix.clone(),
                split_byte,
                split_unit,
            );
        } else if let Some(base) = prefix.strip_suffix("ற்று") {
            push_plain(
                proposals,
                format!("{base}று"),
                suffix.clone(),
                split_byte,
                split_unit,
            );
        }

        // Uyirmei-splitting inversions at `cur` (Patterns 2, 3, 4, 5, 16, 17, 22).
        if !is_mei(cur) && !is_independent_uyir(cur) {
            if let Ok(parts) = split_uyirmei(cur) {
                let rest = slice_units(spans, i + 1, n);
                let second_v = format!("{}{rest}", parts.uyir);
                let mei = parts.mei.as_str();

                // Pattern 2 (`204` Udalmel Uyir): `(prefix + C், V + rest)`.
                if is_native_mei(mei) {
                    push_plain(
                        proposals,
                        format!("{prefix}{mei}"),
                        second_v.clone(),
                        split_byte,
                        split_unit,
                    );
                }

                // Pattern 3 (`205 + 204` Thanikkuril geminate): `prev == C்` and `cur == C + V`.
                if prev == mei && is_native_mei(mei) {
                    push_plain(
                        proposals,
                        prefix.clone(),
                        second_v.clone(),
                        split_byte,
                        split_unit,
                    );
                }

                // Pattern 4 (`162`, `163`, `190`, `192` Udambadumei glides):
                if matches!(mei, "ய்" | "வ்") {
                    let mut p4_extra = Vec::new();
                    if prefix == "ஆ" && mei == "ய்" {
                        p4_extra.push(ctx_class(
                            GrammaticalRelation::Alvazhi,
                            LexicalClass::Demonstrative,
                            true,
                        ));
                    }
                    push_with_ctx(
                        proposals,
                        prefix.clone(),
                        second_v.clone(),
                        split_byte,
                        split_unit,
                        p4_extra,
                    );
                    // Geminate `வ்வ்` (`அவ்வணி -> அ + அணி`, `நொவ்வழகிது -> நொ + அழகிது`).
                    if mei == "வ்" && prev == "வ்" && i >= 2 {
                        let pre2 = slice_units(spans, 0, i - 1);
                        push_plain(
                            proposals,
                            pre2,
                            second_v.clone(),
                            spans[i - 1].byte_start,
                            i - 1,
                        );
                    }
                    // Pattern 22 (`219` `மரம் + அடி -> மரவடி`): `prefix + ம்` before `வ + V`.
                    if mei == "வ்" && unit_vowel(prev).as_deref() == Some("அ") {
                        push_plain(
                            proposals,
                            format!("{prefix}ம்"),
                            second_v.clone(),
                            split_byte,
                            split_unit,
                        );
                    }
                }

                // Pattern 5 (`164` Kurriyalugaram + `183` pre-elision doubling + `164.3` Mutriyalugaram):
                if (!rest.is_empty() || parts.uyir != "உ")
                    && matches!(mei, "க்" | "ச்" | "ட்" | "த்" | "ப்" | "ற்" | "வ்")
                {
                    if let Ok(cu) = compose_uyirmei(mei, "உ") {
                        push_plain(
                            proposals,
                            format!("{prefix}{cu}"),
                            second_v.clone(),
                            split_byte,
                            split_unit,
                        );
                        // Sutra 183 (`காட்டெருமை -> காடு + எருமை`, `ஆற்றூர் -> ஆறு + ஊர்`).
                        if matches!(mei, "ட்" | "ற்") && prev == mei && i >= 2 {
                            let pre2 = slice_units(spans, 0, i - 1);
                            push_plain(
                                proposals,
                                format!("{pre2}{cu}"),
                                second_v.clone(),
                                split_byte,
                                split_unit,
                            );
                        }
                    }
                }

                // Pattern 16 (Single `ற` / `ட`, `229 + 237` non-Thanikkuril `ல்/ள் + த`):
                if mei == "ற்" && !matches!(prev, "ற்" | "ன்" | "ஃ") {
                    if let Some(t_unit) = replace_first_mei(cur, "த்") {
                        push_plain(
                            proposals,
                            format!("{prefix}ல்"),
                            format!("{t_unit}{rest}"),
                            split_byte,
                            split_unit,
                        );
                    }
                }
                if mei == "ட்" && !matches!(prev, "ட்" | "ண்" | "ஃ") {
                    if let Some(t_unit) = replace_first_mei(cur, "த்") {
                        push_plain(
                            proposals,
                            format!("{prefix}ள்"),
                            format!("{t_unit}{rest}"),
                            split_byte,
                            split_unit,
                        );
                    }
                }

                // Pattern 17 (Single `ன` / `ண`, `210/229 + 237` non-Thanikkuril `ன்/ல்/ண்/ள் + ந`):
                if mei == "ன்" && prev != "ன்" {
                    if let Some(n_unit) = replace_first_mei(cur, "ந்") {
                        let n_second = format!("{n_unit}{rest}");
                        push_plain(
                            proposals,
                            format!("{prefix}ன்"),
                            n_second.clone(),
                            split_byte,
                            split_unit,
                        );
                        push_plain(
                            proposals,
                            format!("{prefix}ல்"),
                            n_second.clone(),
                            split_byte,
                            split_unit,
                        );
                        if prefix == "மே" {
                            push_plain(
                                proposals,
                                "மேற்கு".to_owned(),
                                n_second.clone(),
                                split_byte,
                                split_unit,
                            );
                        }
                        if prefix == "தெ" {
                            push_plain(
                                proposals,
                                "தெற்கு".to_owned(),
                                n_second,
                                split_byte,
                                split_unit,
                            );
                        }
                    }
                }
                if mei == "ண்" && prev != "ண்" {
                    if let Some(n_unit) = replace_first_mei(cur, "ந்") {
                        let n_second = format!("{n_unit}{rest}");
                        push_plain(
                            proposals,
                            format!("{prefix}ண்"),
                            n_second.clone(),
                            split_byte,
                            split_unit,
                        );
                        push_plain(
                            proposals,
                            format!("{prefix}ள்"),
                            n_second,
                            split_byte,
                            split_unit,
                        );
                    }
                }

                // Pattern 6 (`93` Kurriyaligaram & `206` minority `இ` before `ய`) & Pattern 28 (`224` `ய்` deletion before `ய`):
                if mei == "ய்" {
                    // Pattern 28: `காயாது -> காய் + யாது`.
                    if !is_mei(prev) {
                        push_plain(
                            proposals,
                            format!("{prefix}ய்"),
                            suffix.clone(),
                            split_byte,
                            split_unit,
                        );
                    }
                    // Pattern 6: `prev` ends in vowel `"இ"`.
                    if let Ok(prev_parts) = split_uyirmei(prev) {
                        if prev_parts.uyir == "இ" {
                            let pre_prev = slice_units(spans, 0, i - 1);
                            let pm = prev_parts.mei.as_str();
                            // 6a (`93`): `கி/சி/டி/தி/பி/றி` -> `கு/சு/டு/து/பு/று` (plus `183` doubled `ட்டி/ற்றி -> டு/று`).
                            if matches!(pm, "க்" | "ச்" | "ட்" | "த்" | "ப்" | "ற்")
                            {
                                if let Ok(pu) = compose_uyirmei(pm, "உ") {
                                    push_plain(
                                        proposals,
                                        format!("{pre_prev}{pu}"),
                                        suffix.clone(),
                                        split_byte,
                                        split_unit,
                                    );
                                    if matches!(pm, "ட்" | "ற்") && i >= 2 && spans[i - 2].text == pm
                                    {
                                        let pre_prev2 = slice_units(spans, 0, i - 2);
                                        push_plain(
                                            proposals,
                                            format!("{pre_prev2}{pu}"),
                                            suffix.clone(),
                                            split_byte,
                                            split_unit,
                                        );
                                    }
                                }
                            }
                            // 6b (`206`): non-`ய்` consonant + `இ` before `ய` (`வேளியாவன்`, `மண்ணியாது`, `கல்லியாது`).
                            if pm != "ய்" && is_native_mei(pm) {
                                push_plain(
                                    proposals,
                                    format!("{pre_prev}{pm}"),
                                    suffix.clone(),
                                    split_byte,
                                    split_unit,
                                );
                                if i >= 2 && spans[i - 2].text == pm {
                                    let pre_prev2 = slice_units(spans, 0, i - 2);
                                    push_plain(
                                        proposals,
                                        format!("{pre_prev2}{pm}"),
                                        suffix.clone(),
                                        split_byte,
                                        split_unit,
                                    );
                                }
                            }
                        }
                    }
                }
            }
        }

        // Pattern 22 (`219` post-`ம்` deletion before Mellinam / Idaiyinam: `மரவேர் -> மரம் + வேர்`).
        if unit_vowel(prev).as_deref() == Some("அ") {
            if let Some(rm) = unit_mei(cur) {
                if matches!(
                    rm.as_str(),
                    "வ்" | "ந்" | "ம்" | "ஞ்" | "ய்" | "ர்" | "ல்" | "ழ்" | "ள்"
                ) {
                    push_plain(
                        proposals,
                        format!("{prefix}ம்"),
                        suffix.clone(),
                        split_byte,
                        split_unit,
                    );
                }
            }
        }

        // Pattern 27 (`207, 208, 212, 215, 217, 223, 225, 231, 234, 236` `-Cஉ / -CCஉ / -Cஅ` increments):
        if let Ok(prev_parts) = split_uyirmei(prev) {
            if matches!(prev_parts.uyir.as_str(), "உ" | "அ") {
                let pm = prev_parts.mei.as_str();
                let pre_prev = slice_units(spans, 0, i - 1);
                let mut stem_candidates = vec![format!("{pre_prev}{pm}")];
                if i >= 2 && spans[i - 2].text == pm {
                    let pre_prev2 = slice_units(spans, 0, i - 2);
                    stem_candidates.push(format!("{pre_prev2}{pm}"));
                }
                let next_second = if i + 1 < n
                    && is_mei(cur)
                    && matches!(cur, "க்" | "ச்" | "த்" | "ப்")
                    && unit_mei(spans[i + 1].text).as_deref() == Some(cur)
                {
                    Some(slice_units(spans, i + 1, n))
                } else {
                    None
                };
                let inc_extra = vec![
                    ctx_class(
                        GrammaticalRelation::Alvazhi,
                        LexicalClass::VerbalNounRoot,
                        false,
                    ),
                    ctx_class(
                        GrammaticalRelation::Vetrumai,
                        LexicalClass::VerbalNounRoot,
                        false,
                    ),
                    ctx_class(
                        GrammaticalRelation::Vetrumai,
                        LexicalClass::BranchName,
                        false,
                    ),
                    ctx_class(GrammaticalRelation::Alvazhi, LexicalClass::DiceVal, false),
                    ctx_class(GrammaticalRelation::Vetrumai, LexicalClass::DiceVal, false),
                    ctx_class(GrammaticalRelation::Vetrumai, LexicalClass::SwanEkin, false),
                ];
                for stem in stem_candidates {
                    if let Some(ref sec) = next_second {
                        push_with_ctx(
                            proposals,
                            stem.clone(),
                            sec.clone(),
                            split_byte,
                            split_unit,
                            inc_extra.clone(),
                        );
                    }
                    push_with_ctx(
                        proposals,
                        stem,
                        suffix.clone(),
                        split_byte,
                        split_unit,
                        inc_extra.clone(),
                    );
                }
            }
        }

        // Consonantal cluster boundaries where `cur` is a pure Mei or Aytham (`i + 1 < n`).
        if i + 1 >= n {
            continue;
        }
        let next = spans[i + 1].text;
        let next_mei = unit_mei(next);
        let after_cur = slice_units(spans, i + 1, n);
        let after_next = slice_units(spans, i + 2, n);

        // Pattern 7 & 8 (Doubled Vallinam stop `க்க / ச்ச / த்த / ப்ப`):
        if matches!(cur, "க்" | "ச்" | "த்" | "ப்") && next_mei.as_deref() == Some(cur)
        {
            let mut p7_extra = Vec::new();
            if prefix == "புளி" {
                p7_extra.push(ctx_class(
                    GrammaticalRelation::Vetrumai,
                    LexicalClass::TastePuli,
                    false,
                ));
            }
            if tables::in_closed_class("locative_particles_181", &prefix) {
                p7_extra.push(ctx_class(
                    GrammaticalRelation::Alvazhi,
                    LexicalClass::LocativeParticle,
                    false,
                ));
            }
            push_with_ctx(
                proposals,
                prefix.clone(),
                after_cur.clone(),
                split_byte,
                split_unit,
                p7_extra,
            );
            // 219 `ம்`-elision + 165 (`மரக்கால் -> மரம் + கால்`).
            if unit_vowel(prev).as_deref() == Some("அ") {
                push_plain(
                    proposals,
                    format!("{prefix}ம்"),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            // 183 doubled `ட்டு/ற்று` + 165 (`ஆட்டுக்கால் -> ஆடு + கால்`, `ஆற்றுப்பாலம் -> ஆறு + பாலம்`).
            if let Some(base) = prefix.strip_suffix("ட்டு") {
                push_plain(
                    proposals,
                    format!("{base}டு"),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            } else if let Some(base) = prefix.strip_suffix("ற்று") {
                push_plain(
                    proposals,
                    format!("{base}று"),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            // 184 Menthodar->Vanthodar reverse (`மருத்துப்பை -> மருந்து + பை`).
            for (van, men) in [
                ("மருத்து", "மருந்து"),
                ("சுருப்பு", "சுரும்பு"),
                ("கருப்பு", "கரும்பு"),
                ("கற்று", "கன்று"),
                ("எற்பு", "என்பு"),
                ("அற்பு", "அன்பு"),
                ("குரக்கு", "குரங்கு"),
            ] {
                if prefix == van {
                    push_plain(
                        proposals,
                        men.to_owned(),
                        after_cur.clone(),
                        split_byte,
                        split_unit,
                    );
                }
            }
            // 185 `-ஐ` increment reverse (`பண்டைக்காலம் -> பண்டு + காலம்`).
            for (ai_s, u_s) in [
                ("பண்டை", "பண்டு"),
                ("இற்றை", "இன்று"),
                ("அற்றை", "அன்று"),
                ("நேற்றை", "நேற்று"),
            ] {
                if prefix == ai_s {
                    push_plain(
                        proposals,
                        u_s.to_owned(),
                        after_cur.clone(),
                        split_byte,
                        split_unit,
                    );
                }
            }
        }

        // Pattern 9 (Doubled nasal/approximant `ஞ்ஞ / ந்ந / ம்ம / ய்ய / வ்வ / ங்ங` + Sutra 163 `அ/இ/உ/எ + ய -> வ்ய`):
        if cur == "வ்" && next_mei.as_deref() == Some("ய்") {
            push_plain(
                proposals,
                prefix.clone(),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
        }
        if matches!(cur, "ங்" | "ஞ்" | "ந்" | "ம்" | "ய்" | "வ்") && next_mei.as_deref() == Some(cur)
        {
            push_plain(
                proposals,
                prefix.clone(),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
            // 221 (`நுந்நூல் -> நும் + நூல்`).
            if matches!(cur, "ஞ்" | "ந்") {
                push_plain(
                    proposals,
                    format!("{prefix}ம்"),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            // 235 (`அஞ்ஞானம் -> அவ் + ஞானம்`).
            if matches!(cur, "ஞ்" | "ந்" | "ம்") {
                push_plain(
                    proposals,
                    format!("{prefix}வ்"),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
        }

        // Pattern 10 (Nasal `ங்/ஞ்/ந்/ம்` before homorganic Vallinam stop `க/ச/த/ப`):
        let homorganic_pair = matches!(
            (cur, next_mei.as_deref()),
            ("ங்", Some("க்")) | ("ஞ்", Some("ச்")) | ("ந்", Some("த்")) | ("ம்", Some("ப்"))
        );
        if homorganic_pair {
            let p10_extra = vec![
                ctx_class(GrammaticalRelation::Vetrumai, LexicalClass::TreeName, false),
                ctx_class(
                    GrammaticalRelation::Vetrumai,
                    LexicalClass::TastePuli,
                    false,
                ),
            ];
            push_with_ctx(
                proposals,
                prefix.clone(),
                after_cur.clone(),
                split_byte,
                split_unit,
                p10_extra,
            );
            push_plain(
                proposals,
                format!("{prefix}ம்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
            // 136 Panpuppeyar (`செந்தாமரை -> செம்மை + தாமரை`, `பைந்தமிழ் -> பசுமை + தமிழ்`, `கருங்குதிரை -> கருமை + குதிரை`).
            let panpu_ctx = vec![ctx_sub(
                GrammaticalRelation::Alvazhi,
                ContextSubtype::Panputhogai,
                false,
            )];
            push_with_ctx(
                proposals,
                format!("{prefix}மை"),
                after_cur.clone(),
                split_byte,
                split_unit,
                panpu_ctx.clone(),
            );
            push_with_ctx(
                proposals,
                format!("{prefix}ம்மை"),
                after_cur.clone(),
                split_byte,
                split_unit,
                panpu_ctx.clone(),
            );
            if prefix == "பை" {
                push_with_ctx(
                    proposals,
                    "பசுமை".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                    panpu_ctx,
                );
            }
            if prefix == "பன" {
                push_plain(
                    proposals,
                    "பனை".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            if prefix == "தே" {
                push_plain(
                    proposals,
                    "தேன்".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            if prefix == "புன்னைய" {
                push_plain(
                    proposals,
                    "புன்னை".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
            if prefix == "தாழ" {
                push_plain(
                    proposals,
                    "தாழை".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
        }

        // Pattern 11 (`ற்ற` -> `ல்/ன் + த` & `மேற்கு + திசை`):
        if cur == "ற்" && next_mei.as_deref() == Some("ற்") {
            if let Some(t_unit) = replace_first_mei(next, "த்") {
                let t_sec = format!("{t_unit}{after_next}");
                push_plain(
                    proposals,
                    format!("{prefix}ல்"),
                    t_sec.clone(),
                    split_byte,
                    split_unit,
                );
                push_plain(
                    proposals,
                    format!("{prefix}ன்"),
                    t_sec.clone(),
                    split_byte,
                    split_unit,
                );
                if prefix == "மே" {
                    push_plain(proposals, "மேற்கு".to_owned(), t_sec, split_byte, split_unit);
                }
            }
        }

        // Pattern 12 (`ட்ட` -> `ள்/ண் + த`):
        if cur == "ட்" && next_mei.as_deref() == Some("ட்") {
            if let Some(t_unit) = replace_first_mei(next, "த்") {
                let t_sec = format!("{t_unit}{after_next}");
                push_plain(
                    proposals,
                    format!("{prefix}ள்"),
                    t_sec.clone(),
                    split_byte,
                    split_unit,
                );
                push_plain(
                    proposals,
                    format!("{prefix}ண்"),
                    t_sec,
                    split_byte,
                    split_unit,
                );
            }
        }

        // Pattern 13 (`ன்ற` -> `ன் + த`):
        if cur == "ன்" && next_mei.as_deref() == Some("ற்") {
            if let Some(t_unit) = replace_first_mei(next, "த்") {
                let t_sec = format!("{t_unit}{after_next}");
                push_plain(
                    proposals,
                    format!("{prefix}ன்"),
                    t_sec.clone(),
                    split_byte,
                    split_unit,
                );
                if prefix == "தெ" {
                    push_plain(proposals, "தெற்கு".to_owned(), t_sec, split_byte, split_unit);
                }
            }
        }

        // Pattern 14 (`ண்ட` -> `ண் + த`):
        if cur == "ண்" && next_mei.as_deref() == Some("ட்") {
            if let Some(t_unit) = replace_first_mei(next, "த்") {
                push_plain(
                    proposals,
                    format!("{prefix}ண்"),
                    format!("{t_unit}{after_next}"),
                    split_byte,
                    split_unit,
                );
            }
        }

        // Pattern 15 (`ன்ன` / `ண்ண` -> `ன்/ல் + ந` & `ண்/ள் + ந`):
        if cur == "ன்" && next_mei.as_deref() == Some("ன்") {
            if let Some(n_unit) = replace_first_mei(next, "ந்") {
                let n_sec = format!("{n_unit}{after_next}");
                push_plain(
                    proposals,
                    format!("{prefix}ன்"),
                    n_sec.clone(),
                    split_byte,
                    split_unit,
                );
                push_plain(
                    proposals,
                    format!("{prefix}ல்"),
                    n_sec.clone(),
                    split_byte,
                    split_unit,
                );
                if prefix == "தெ" {
                    push_plain(proposals, "தெற்கு".to_owned(), n_sec, split_byte, split_unit);
                }
            }
        }
        if cur == "ண்" && next_mei.as_deref() == Some("ண்") {
            if let Some(n_unit) = replace_first_mei(next, "ந்") {
                let n_sec = format!("{n_unit}{after_next}");
                push_plain(
                    proposals,
                    format!("{prefix}ண்"),
                    n_sec.clone(),
                    split_byte,
                    split_unit,
                );
                push_plain(
                    proposals,
                    format!("{prefix}ள்"),
                    n_sec,
                    split_byte,
                    split_unit,
                );
            }
        }

        // Pattern 18 (`ற்(க/ச/ப)` / `ட்(க/ச/ப)`):
        if cur == "ற்" && matches!(next_mei.as_deref(), Some("க்" | "ச்" | "ப்")) {
            push_plain(
                proposals,
                format!("{prefix}ல்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
            push_plain(
                proposals,
                format!("{prefix}ன்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
            if prefix == "நா" {
                push_plain(
                    proposals,
                    "நான்கு".to_owned(),
                    after_cur.clone(),
                    split_byte,
                    split_unit,
                );
            }
        }
        if cur == "ட்" && matches!(next_mei.as_deref(), Some("க்" | "ச்" | "ப்")) {
            push_plain(
                proposals,
                format!("{prefix}ள்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
            push_plain(
                proposals,
                format!("{prefix}ண்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
        }

        // Pattern 19 (`ன்(ஞ/ம)` / `ண்(ஞ/ம)` -> `ல்/ள் + ஞ/ம`):
        if cur == "ன்" && matches!(next_mei.as_deref(), Some("ஞ்" | "ம்")) {
            push_plain(
                proposals,
                format!("{prefix}ல்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
        }
        if cur == "ண்" && matches!(next_mei.as_deref(), Some("ஞ்" | "ம்")) {
            push_plain(
                proposals,
                format!("{prefix}ள்"),
                after_cur.clone(),
                split_byte,
                split_unit,
            );
        }

        // Pattern 20 (`ஃற` / `ஃட`, `228 + 237`) & Pattern 21 (`ஃ(க/ச/த/ப)`, `235`):
        if cur == "ஃ" {
            if next_mei.as_deref() == Some("ற்") {
                if let Some(t_unit) = replace_first_mei(next, "த்") {
                    push_plain(
                        proposals,
                        format!("{prefix}ல்"),
                        format!("{t_unit}{after_next}"),
                        split_byte,
                        split_unit,
                    );
                }
            } else if next_mei.as_deref() == Some("ட்") {
                if let Some(t_unit) = replace_first_mei(next, "த்") {
                    push_plain(
                        proposals,
                        format!("{prefix}ள்"),
                        format!("{t_unit}{after_next}"),
                        split_byte,
                        split_unit,
                    );
                }
            }
            if is_vallinam_initial_unit(next) {
                push_plain(
                    proposals,
                    format!("{prefix}வ்"),
                    after_cur,
                    split_byte,
                    split_unit,
                );
            }
        }
    }
}

/// Patterns 23-26: Chariyai + case + `உம்`, oblique pronouns, and closed-class/poetic stems.
fn propose_chariyai_and_closed_class(
    surface: &str,
    spans: &[UnitSpan<'_>],
    poetic: bool,
    proposals: &mut Vec<RawProposal>,
) {
    let n = spans.len();
    let last_internal = n - 1;
    let last_byte = spans[last_internal].byte_start;

    // Pattern 23 (`219 + 244 + 252` `-த்து-` / `-த்த்-` + case/word):
    for i in 1..n {
        let prefix = slice_units(spans, 0, i);
        let rest = slice_units(spans, i, n);
        if rest.starts_with("த்த") || rest.starts_with("த்து") {
            let split_byte = spans[i].byte_start;
            let stem_m = format!("{prefix}ம்");
            let mut bases = vec![stem_m];
            if prefix == "மக" {
                bases.push("மக".to_owned());
            }
            for base in bases {
                for case_sfx in ["ஐ", "ஆல்", "ஆன்", "ஒடு", "ஓடு", "கு", "இன்", "இல்", "அது", "கண்"]
                {
                    push_plain(proposals, base.clone(), case_sfx.to_owned(), split_byte, i);
                }
                if let Some(after_ttu) = rest.strip_prefix("த்து") {
                    if let Some(after_stop) = after_ttu
                        .strip_prefix("க்")
                        .or_else(|| after_ttu.strip_prefix("ச்"))
                        .or_else(|| after_ttu.strip_prefix("த்"))
                        .or_else(|| after_ttu.strip_prefix("ப்"))
                    {
                        if !after_stop.is_empty() {
                            push_plain(
                                proposals,
                                base.clone(),
                                after_stop.to_owned(),
                                split_byte,
                                i,
                            );
                        }
                    } else if !after_ttu.is_empty() {
                        push_plain(proposals, base.clone(), after_ttu.to_owned(), split_byte, i);
                    }
                } else if i + 1 < n {
                    if let Ok(parts) = split_uyirmei(spans[i + 1].text) {
                        if parts.mei == "த்" && parts.uyir != "உ" {
                            let tail = slice_units(spans, i + 2, n);
                            push_plain(
                                proposals,
                                base.clone(),
                                format!("{}{tail}", parts.uyir),
                                split_byte,
                                i,
                            );
                        }
                    }
                }
            }
        }
    }

    // Pattern 24 (`243-253, 257` Chariyai + case + `உம்` post-positioning):
    let case_suffixes = [
        "ஐ",
        "ஆல்",
        "ஆன்",
        "ஒடு",
        "ஓடு",
        "கு",
        "இன்",
        "இல்",
        "அது",
        "ஆது",
        "கண்",
    ];
    // `எல்லாம்` (`245`), `எல்லாரும்` / `எல்லீரும்` (`246`):
    if surface.starts_with("எல்லா") && surface.ends_with("உம்")
        || surface.starts_with("எல்லா") && surface.ends_with("ம்")
    {
        let sb = spans[2.min(last_internal)].byte_start;
        let su = 2.min(last_internal);
        let rat_ctx = vec![ctx_class(
            GrammaticalRelation::Vetrumai,
            LexicalClass::RationalNoun,
            poetic,
        )];
        let nonrat_ctx = vec![ctx_class(
            GrammaticalRelation::Vetrumai,
            LexicalClass::NonRationalNoun,
            poetic,
        )];
        for &cs in &case_suffixes {
            push_with_ctx(
                proposals,
                "எல்லாம்".to_owned(),
                cs.to_owned(),
                sb,
                su,
                nonrat_ctx.clone(),
            );
            push_with_ctx(
                proposals,
                "எல்லாம்".to_owned(),
                cs.to_owned(),
                sb,
                su,
                rat_ctx.clone(),
            );
            push_plain(proposals, "எல்லாரும்".to_owned(), cs.to_owned(), sb, su);
        }
    }
    if surface.starts_with("எல்லீர்") {
        let sb = spans[2.min(last_internal)].byte_start;
        let su = 2.min(last_internal);
        for &cs in &case_suffixes {
            push_plain(proposals, "எல்லீரும்".to_owned(), cs.to_owned(), sb, su);
        }
    }
    // `பல/சில` (`244`), `அவ்/இவ்/உவ்/எவ்` (`250, 257`), `அஃது/இஃது/உஃது/அது/இது/உது` (`251`), `ஆ/மா/கோ` (`248`):
    let stem_prefixes: &[(&str, &[&str])] = &[
        ("பலவற்", &["பல"]),
        ("சிலவற்", &["சில"]),
        ("அவற்", &["அவ்"]),
        ("இவற்", &["இவ்"]),
        ("உவற்", &["உவ்"]),
        ("எவற்", &["எவ்"]),
        ("அத", &["அஃது", "அது"]),
        ("அஃத", &["அஃது"]),
        ("இத", &["இஃது", "இது"]),
        ("உத", &["உஃது", "உது"]),
        ("ஆன", &["ஆ"]),
        ("ஆவ", &["ஆ"]),
        ("மான", &["மா"]),
        ("மாவ", &["மா"]),
        ("கோன", &["கோ"]),
        ("கோவ", &["கோ"]),
    ];
    for &(pfx, stems) in stem_prefixes {
        if surface.starts_with(pfx) {
            let su = 1.min(last_internal);
            let sb = spans[su].byte_start;
            for &st in stems {
                for &cs in &case_suffixes {
                    push_plain(proposals, st.to_owned(), cs.to_owned(), sb, su);
                }
            }
            // General Sutra 238 content-word delegation after `அவற்று/அவற்றி..எவற்று/எவற்றி` (+ optional doubled stop):
            for &(arru_stem, orig_stem) in &[
                ("அவற்று", "அவ்"),
                ("அவற்றி", "அவ்"),
                ("இவற்று", "இவ்"),
                ("இவற்றி", "இவ்"),
                ("உவற்று", "உவ்"),
                ("உவற்றி", "உவ்"),
                ("எவற்று", "எவ்"),
                ("எவற்றி", "எவ்"),
            ] {
                if let Some(after_arru) = surface.strip_prefix(arru_stem) {
                    if !after_arru.is_empty() {
                        push_plain(
                            proposals,
                            orig_stem.to_owned(),
                            after_arru.to_owned(),
                            sb,
                            su,
                        );
                        if let Some(after_stop) = after_arru
                            .strip_prefix("க்")
                            .or_else(|| after_arru.strip_prefix("ச்"))
                            .or_else(|| after_arru.strip_prefix("த்"))
                            .or_else(|| after_arru.strip_prefix("ப்"))
                        {
                            if !after_stop.is_empty() {
                                push_plain(
                                    proposals,
                                    orig_stem.to_owned(),
                                    after_stop.to_owned(),
                                    sb,
                                    su,
                                );
                            }
                        }
                    }
                }
            }
            // Vowel-initial Sutra 238 after `அவற்ற்/இவற்ற்/உவற்ற்/எவற்ற்` (`அவற்றடி -> அவ் + அடி`):
            for &(arru_cut, orig_stem) in
                &[("அவற்", "அவ்"), ("இவற்", "இவ்"), ("உவற்", "உவ்"), ("எவற்", "எவ்")]
            {
                if let Some(after_cut) = surface.strip_prefix(arru_cut) {
                    let mut rem_units = Letters::new(after_cut);
                    if let Some(first_u) = rem_units.next() {
                        if let Ok(parts) = split_uyirmei(first_u) {
                            if parts.mei == "ற்" {
                                let tail: String = rem_units.collect();
                                push_plain(
                                    proposals,
                                    orig_stem.to_owned(),
                                    format!("{}{tail}", parts.uyir),
                                    sb,
                                    su,
                                );
                            }
                        }
                    }
                }
            }
            // Content-word delegation after `அதன்/இதன்/உதன்` & `ஆன்/மான்/கோன்`:
            for &(n_stem, orig_stem) in &[
                ("அதன்", "அது"),
                ("அதன்", "அஃது"),
                ("இதன்", "இது"),
                ("இதன்", "இஃது"),
                ("உதன்", "உது"),
                ("உதன்", "உஃது"),
                ("ஆன்", "ஆ"),
                ("மான்", "மா"),
                ("கோன்", "கோ"),
            ] {
                if let Some(after_n) = surface.strip_prefix(n_stem) {
                    if !after_n.is_empty() {
                        push_plain(proposals, orig_stem.to_owned(), after_n.to_owned(), sb, su);
                    }
                }
            }
        }
    }
    // Decade `249` (`ஒருபானை`..`ஒன்பானை`):
    for (pfx, decade) in [
        ("ஒருபா", "ஒருபது"),
        ("இருபா", "இருபது"),
        ("முப்பா", "முப்பது"),
        ("நாற்பா", "நாற்பது"),
        ("ஐம்பா", "ஐம்பது"),
        ("அறுபா", "அறுபது"),
        ("எழுபா", "எழுபது"),
        ("எண்பா", "எண்பது"),
        ("ஒன்பா", "ஒன்பது"),
    ] {
        if surface.starts_with(pfx) {
            let su = last_internal;
            for &cs in &case_suffixes {
                push_plain(proposals, decade.to_owned(), cs.to_owned(), last_byte, su);
            }
        }
    }
    // Kurriyalugaram + `இன்` + `கண்` (`254` `நாட்டின்கண்`), consonant + `உ` + `கு` (`சாத்தனுக்கு`):
    if let Some(pre) = surface.strip_suffix("ின்கண்") {
        if let Some(stem) = pre.strip_suffix("ட்ட") {
            let su = (n - 2).max(1);
            push_plain(
                proposals,
                format!("{stem}டு"),
                "கண்".to_owned(),
                spans[su].byte_start,
                su,
            );
        }
    }
    if surface.ends_with("க்கு") {
        for i in 1..n {
            let prefix = slice_units(spans, 0, i);
            let rest = slice_units(spans, i, n);
            if rest == "க்கு" {
                let sb = spans[i].byte_start;
                push_plain(proposals, prefix.clone(), "கு".to_owned(), sb, i);
                if let Some(base) = prefix.strip_suffix("மாட") {
                    push_plain(proposals, format!("{base}மாடம்"), "கு".to_owned(), sb, i);
                }
            }
        }
    }

    // Pattern 25 (`247, 238` Oblique pronouns):
    let pronoun_inverses: &[(&str, &[&str])] = &[
        ("என", &["யான்", "நான்"]),
        ("என்", &["யான்", "நான்"]),
        ("தன", &["தான்"]),
        ("தன்", &["தான்"]),
        ("நின", &["நீ"]),
        ("நின்", &["நீ"]),
        ("உன", &["நீ"]),
        ("உன்", &["நீ"]),
        ("எம", &["யாம்"]),
        ("எம்", &["யாம்"]),
        ("தம", &["தாம்"]),
        ("தம்", &["தாம்"]),
        ("நம", &["நாம்"]),
        ("நம்", &["நாம்"]),
        ("நும", &["நீர்"]),
        ("நும்", &["நீர்"]),
        ("உம", &["நீர்"]),
        ("உம்", &["நீர்"]),
    ];
    for &(ob, noms) in pronoun_inverses {
        if let Some(rem) = surface.strip_prefix(ob) {
            let su = 2.min(last_internal);
            let sb = spans[su].byte_start;
            for &nom in noms {
                for &cs in &case_suffixes {
                    push_plain(proposals, nom.to_owned(), cs.to_owned(), sb, su);
                }
                if !rem.is_empty() && !rem.starts_with('\u{0BCD}') {
                    push_plain(proposals, nom.to_owned(), rem.to_owned(), sb, su);
                }
            }
        }
    }

    // Pattern 26 (Closed-class exact & prefix-mapped compounds: `136, 168-174, 180, 186-199, 203, 222, 233`):
    let exact_compounds: &[(&str, &str, &str, Option<ContextSubtype>)] = &[
        ("தொண்ணூறு", "ஒன்பது", "பத்து", None),
        ("தொள்ளாயிரம்", "ஒன்பது", "நூறு", None),
        (
            "பன்னிரண்டு",
            "பத்து",
            "இரண்டு",
            Some(ContextSubtype::Ummaithogai),
        ),
        ("தேங்காய்", "தெங்கு", "காய்", None),
        ("தெங்கங்காய்", "தெங்கு", "காய்", None),
        ("நாடுரி", "நாழி", "உரி", None),
        ("பனாட்டு", "பனை", "அட்டு", None),
        ("அங்கை", "அகம்", "கை", None),
        ("அஞ்செவி", "அகம்", "செவி", None),
        ("அஞ்சிறை", "அகம்", "சிறை", None),
        ("அதான்று", "அது", "அன்று", None),
        ("பலபல", "பல", "பல", None),
        ("பலப்பல", "பல", "பல", None),
        ("பற்பல", "பல", "பல", None),
        ("பல்பல", "பல", "பல", None),
        ("சிலசில", "சில", "சில", None),
        ("சிலச்சில", "சில", "சில", None),
        ("சிற்சில", "சில", "சில", None),
        ("சில்சில", "சில", "சில", None),
        (
            "ஒவ்வொன்று",
            "ஒன்று",
            "ஒன்று",
            Some(ContextSubtype::Distributive),
        ),
        (
            "இவ்விரண்டு",
            "இரண்டு",
            "இரண்டு",
            Some(ContextSubtype::Distributive),
        ),
        (
            "மும்மூன்று",
            "மூன்று",
            "மூன்று",
            Some(ContextSubtype::Distributive),
        ),
        ("நந்நான்கு", "நான்கு", "நான்கு", Some(ContextSubtype::Distributive)),
        ("ஐவைந்து", "ஐந்து", "ஐந்து", Some(ContextSubtype::Distributive)),
        ("அவ்வாறு", "ஆறு", "ஆறு", Some(ContextSubtype::Distributive)),
        ("எவ்வேழு", "ஏழு", "ஏழு", Some(ContextSubtype::Distributive)),
        (
            "எவ்வெட்டு",
            "எட்டு",
            "எட்டு",
            Some(ContextSubtype::Distributive),
        ),
        ("பப்பத்து", "பத்து", "பத்து", Some(ContextSubtype::Distributive)),
        ("ஒருபது", "ஒன்று", "பத்து", None),
        ("ஒருபஃது", "ஒன்று", "பத்து", None),
        ("இருபது", "இரண்டு", "பத்து", None),
        ("இருபஃது", "இரண்டு", "பத்து", None),
        ("முப்பது", "மூன்று", "பத்து", None),
        ("நாற்பது", "நான்கு", "பத்து", None),
        ("ஐம்பது", "ஐந்து", "பத்து", None),
        ("அறுபது", "ஆறு", "பத்து", None),
        ("எழுபது", "ஏழு", "பத்து", None),
        ("எண்பது", "எட்டு", "பத்து", None),
        ("சிற்றூர்", "சிறுமை", "ஊர்", Some(ContextSubtype::Panputhogai)),
        (
            "வெற்றிலை",
            "வெறுமை",
            "இலை",
            Some(ContextSubtype::Panputhogai),
        ),
        ("கரியன்", "கருமை", "அன்", Some(ContextSubtype::Panputhogai)),
        ("பெரியன்", "பெருமை", "அன்", Some(ContextSubtype::Panputhogai)),
        ("சேதாம்பல்", "செம்மை", "ஆம்பல்", Some(ContextSubtype::Panputhogai)),
        ("பாசடை", "பசுமை", "அடை", Some(ContextSubtype::Panputhogai)),
        ("நல்லன்", "நன்மை", "அன்", Some(ContextSubtype::Panputhogai)),
        ("வல்லன்", "வன்மை", "அன்", Some(ContextSubtype::Panputhogai)),
        ("மூதூர்", "முதுமை", "ஊர்", Some(ContextSubtype::Panputhogai)),
        ("புத்தூர்", "புதுமை", "ஊர்", Some(ContextSubtype::Panputhogai)),
        ("செம்மலர்", "செம்மை", "மலர்", Some(ContextSubtype::Panputhogai)),
        ("செந்நீர்", "செம்மை", "நீர்", Some(ContextSubtype::Panputhogai)),
        ("வெம்மதி", "வெம்மை", "மதி", Some(ContextSubtype::Panputhogai)),
        ("பழந்தமிழ்", "பழமை", "தமிழ்", Some(ContextSubtype::Panputhogai)),
        ("அருங்கடல்", "அருமை", "கடல்", Some(ContextSubtype::Panputhogai)),
        ("இளந்தமிழ்", "இளமை", "தமிழ்", Some(ContextSubtype::Panputhogai)),
        ("கடுஞ்சொல்", "கடுமை", "சொல்", Some(ContextSubtype::Panputhogai)),
        ("நற்றமிழ்", "நன்மை", "தமிழ்", Some(ContextSubtype::Panputhogai)),
        ("நற்குணம்", "நன்மை", "குணம்", Some(ContextSubtype::Panputhogai)),
        ("தண்டமிழ்", "தண்மை", "தமிழ்", Some(ContextSubtype::Panputhogai)),
        ("மென்பூ", "மென்மை", "பூ", Some(ContextSubtype::Panputhogai)),
        ("பேரூர்", "பெருமை", "ஊர்", Some(ContextSubtype::Panputhogai)),
    ];
    for &(surf, f, s, sub) in exact_compounds {
        if surface == surf {
            let su = (n / 2).max(1).min(last_internal);
            let sb = spans[su].byte_start;
            let extra = sub
                .map(|st| vec![ctx_sub(GrammaticalRelation::Alvazhi, st, poetic)])
                .unwrap_or_default();
            push_with_ctx(proposals, f.to_owned(), s.to_owned(), sb, su, extra);
        }
    }

    // Prefix-based closed-class stems (Directions `186`, Numerals `188-197`, `168-174`, `233`):
    let prefix_maps: &[(&str, &str)] = &[
        ("வட", "வடக்கு"),
        ("குட", "குடக்கு"),
        ("குண", "குணக்கு"),
        ("தென்", "தெற்கு"),
        ("மேல்", "மேற்கு"),
        ("கீழ்", "கிழக்கு"),
        ("உரிய", "உரி"),
        ("வாழி", "வாழிய"),
        ("நிலவு", "நிலா"),
        ("நில", "நிலா"),
        ("அன்று", "அன்றி"),
        ("இன்று", "இன்றி"),
        ("ஒருபத்த", "ஒருபஃது"),
        ("ஒருபத்த", "ஒருபது"),
        ("பதின்", "பத்து"),
        ("பதிற்ற", "பத்து"),
        ("பதின", "பத்து"),
        ("நால்", "நான்கு"),
        ("நான்", "நான்கு"),
        ("ஒரு", "ஒன்று"),
        ("இரு", "இரண்டு"),
        ("அறு", "ஆறு"),
        ("எழு", "ஏழு"),
        ("எண்", "எட்டு"),
    ];
    for &(pfx, orig) in prefix_maps {
        if surface.starts_with(pfx) {
            let pfx_units = Letters::new(pfx).count();
            if pfx_units >= 1 && pfx_units < n {
                let sb = spans[pfx_units].byte_start;
                let rem = slice_units(spans, pfx_units, n);
                push_plain(proposals, orig.to_owned(), rem.clone(), sb, pfx_units);
                if pfx == "கீழ்" {
                    if let Some(rem_after_stop) = rem
                        .strip_prefix("க்")
                        .or_else(|| rem.strip_prefix("ச்"))
                        .or_else(|| rem.strip_prefix("த்"))
                        .or_else(|| rem.strip_prefix("ப்"))
                    {
                        if !rem_after_stop.is_empty() {
                            push_plain(
                                proposals,
                                orig.to_owned(),
                                rem_after_stop.to_owned(),
                                sb,
                                pfx_units,
                            );
                        }
                    }
                }
                // Handle fused vowel right after `பதின்`/`ஒருபத்த`/`பதிற்ற` (`பதினொன்று`, `ஒருபத்தொன்று`, `பதிற்றொன்று`).
                if matches!(pfx, "ஒருபத்த" | "பதிற்ற" | "பதின") {
                    for num_u in [
                        "ஒன்று",
                        "இரண்டு",
                        "மூன்று",
                        "நான்கு",
                        "ஐந்து",
                        "ஆறு",
                        "ஏழு",
                        "எட்டு",
                        "ஒன்பது",
                        "ஆயிரம்",
                    ] {
                        push_plain(proposals, orig.to_owned(), num_u.to_owned(), sb, pfx_units);
                    }
                }
            }
        }
    }
    // Fused `நால் + V` (`நாலடி -> நான்கு + அடி`), `நான் + ந்` (`நானாழி -> நான்கு + நாழி`), `ஏழ் + V` (`ஏழாயிரம் -> ஏழு + ஆயிரம்`):
    if n >= 2 {
        if spans[0].text == "நா" {
            if let Ok(parts) = split_uyirmei(spans[1].text) {
                if matches!(parts.mei.as_str(), "ல்" | "ன்") {
                    let tail = slice_units(spans, 2, n);
                    let sb = spans[1].byte_start;
                    let second = if parts.mei == "ல்" {
                        format!("{}{tail}", parts.uyir)
                    } else if let Ok(na_u) = compose_uyirmei("ந்", &parts.uyir) {
                        format!("{na_u}{tail}")
                    } else {
                        String::new()
                    };
                    if !second.is_empty() {
                        push_plain(proposals, "நான்கு".to_owned(), second, sb, 1);
                    }
                }
            }
        } else if spans[0].text == "ஏ" {
            if let Ok(parts) = split_uyirmei(spans[1].text) {
                if parts.mei == "ழ்" {
                    let tail = slice_units(spans, 2, n);
                    let sb = spans[1].byte_start;
                    push_plain(
                        proposals,
                        "ஏழு".to_owned(),
                        format!("{}{tail}", parts.uyir),
                        sb,
                        1,
                    );
                }
            }
        }
    }
}
