//! Chapter 2 (*Meyyeerrup Punariyal*, Sutras 204-239) Stage 3B, 3C, and 3D consonant-final rules.

use crate::context::{
    AlterationKind, ContextSubtype, DerivationStep, GrammaticalRelation, LexicalClass,
    PunarchiContext,
};
use crate::phonology::{
    homorganic_nasal, is_independent_uyir, is_native_mei, is_thanikkuril_otru,
    is_vallinam_initial_unit, unit_mei,
};
use crate::pipeline::BoundaryState;
use crate::tables;
use crate::uyireeru;
use tamil_core::{compose_uyirmei, is_mei, split_uyirmei, Letters};

/// Stage 3B (Sutra 237): Pre-mutation of `த`/`ந` after `ன்/ல்/ண்/ள்` BEFORE Stage 3C mutates the left final.
///
/// Sets `flags.triggered_237 = Some((left_final_char, orig_right_char))` so Stage 3C (`209/210/227/228/229`)
/// produces all 12 attested surface clusters/singletons and enforces Sutra 117 (`*ல்த`/`*ள்த` ban).
pub fn apply_stage_3b(mut state: BoundaryState) -> BoundaryState {
    let left_units: Vec<&str> = Letters::new(&state.left).collect();
    let right_units: Vec<&str> = Letters::new(&state.right).collect();
    let (Some(&last_l), Some(&first_r)) = (left_units.last(), right_units.first()) else {
        return state;
    };

    let left_tag = match last_l {
        "ன்" => 'ன',
        "ல்" => 'ல',
        "ண்" => 'ண',
        "ள்" => 'ள',
        _ => return state,
    };

    let Ok(r_parts) = split_uyirmei(first_r) else {
        return state;
    };

    let (orig_r_tag, new_r_mei) = match (left_tag, r_parts.mei.as_str()) {
        ('ன' | 'ல', "த்") => ('த', "ற்"),
        ('ன' | 'ல', "ந்") => ('ந', "ன்"),
        ('ண' | 'ள', "த்") => ('த', "ட்"),
        ('ண' | 'ள', "ந்") => ('ந', "ண்"),
        _ => return state,
    };

    if let Ok(mutated_first) = compose_uyirmei(new_r_mei, &r_parts.uyir) {
        let rest: String = right_units[1..].concat();
        let new_right = format!("{mutated_first}{rest}");
        let before = format!("{} + {}", state.left, state.right);
        let after = format!("{} + {new_right}", state.left);
        state.steps.push(DerivationStep {
            sutra: 237,
            rule_id: "nannool_237_ta_na_mutation".to_owned(),
            stage: 3,
            transform: AlterationKind::Thirithal,
            before,
            after,
        });
        state.right = new_right;
        state.flags.triggered_237 = Some((left_tag, orig_r_tag));
    }

    state
}

/// Stage 3C core consonant-final morphophonemics (`209-210`, `219-220`, `224`, `227-229`, `158`).
pub fn apply_stage_3c_consonant_final(
    state: BoundaryState,
    context: &PunarchiContext,
) -> Vec<BoundaryState> {
    let left_src = state.left.clone();
    let right_src = state.right.clone();
    let left_units: Vec<&str> = Letters::new(&left_src).collect();
    let right_units: Vec<&str> = Letters::new(&right_src).collect();
    let (Some(&last_l), Some(&first_r)) = (left_units.last(), right_units.first()) else {
        return vec![state];
    };

    if !is_mei(last_l) || !is_native_mei(last_l) {
        return vec![state];
    }

    match last_l {
        "ண்" | "ன்" => apply_nna_na(state, context, &left_units, last_l, first_r),
        "ம்" => apply_magaram(state, context, &left_units, first_r),
        "ய்" | "ர்" | "ழ்" => {
            apply_ya_ra_zha(state, context, &left_units, last_l, first_r)
        }
        "ல்" | "ள்" => apply_la_lla(state, context, &left_units, last_l, first_r),
        "வ்" => apply_vagaram(state, context, &left_units, first_r),
        _ => vec![state],
    }
}

/// Stage 3D (Sutra 205): *Thanikkuril Otru* doubling before independent vowels (unless `suppress_205`).
pub fn apply_stage_3d(mut state: BoundaryState) -> BoundaryState {
    if state.flags.suppress_205 {
        return state;
    }
    let right_units: Vec<&str> = Letters::new(&state.right).collect();
    let Some(&first_r) = right_units.first() else {
        return state;
    };
    if !is_independent_uyir(first_r)
        || (!is_thanikkuril_otru(&state.left) && !state.flags.force_205)
    {
        return state;
    }

    let left_units: Vec<&str> = Letters::new(&state.left).collect();
    let last_l = left_units[left_units.len() - 1];
    let new_left = format!("{}{last_l}", state.left);
    let before = format!("{} + {}", state.left, state.right);
    let after = format!("{new_left} + {}", state.right);
    state.steps.push(DerivationStep {
        sutra: 205,
        rule_id: "nannool_205_thanikkuril_otru".to_owned(),
        stage: 3,
        transform: AlterationKind::Thonral,
        before,
        after,
    });
    state.left = new_left;
    state
}

fn replace_last_unit(units: &[&str], replacement: &str) -> String {
    let prefix: String = units[..units.len() - 1].concat();
    format!("{prefix}{replacement}")
}

fn drop_last_unit(units: &[&str]) -> String {
    units[..units.len() - 1].concat()
}

fn apply_nna_na(
    state: BoundaryState,
    context: &PunarchiContext,
    left_units: &[&str],
    last_l: &str,
    first_r: &str,
) -> Vec<BoundaryState> {
    if is_independent_uyir(first_r) {
        return vec![state];
    }

    let thanikkuril = is_thanikkuril_otru(&state.left);

    // Sutra 210: Non-Thanikkuril `ண்`/`ன்` deletes before 237-mutated `ந` in both Alvazhi and Vetrumai.
    if matches!(state.flags.triggered_237, Some((_, 'ந'))) {
        if !thanikkuril {
            let mut s = state;
            let new_left = drop_last_unit(left_units);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 210,
                rule_id: "nannool_210_nna_na_elision_before_mutated_na".to_owned(),
                stage: 3,
                transform: AlterationKind::Keduthal,
                before,
                after,
            });
            s.left = new_left;
            return vec![s];
        }
        // Thanikkuril `பொன் + நன்று -> பொன்னன்று`, `மண் + நன்று -> மண்ணன்று` (237 already applied; 209 natural).
        return vec![emit_209_iyalbu(state, None, 40)];
    }

    let is_stop =
        is_vallinam_initial_unit(first_r) || matches!(state.flags.triggered_237, Some((_, 'த')));

    if state.flags.block_209_stop {
        if state.steps.iter().any(|st| st.sutra == 193) {
            return vec![emit_209_iyalbu(state, None, 25)];
        }
        return vec![state];
    }

    // Sutra 211: `ண்`-final branch/group names, `பரண்`, `கவண்` stay natural in Vetrumai; edible `எண்`/`சாண்` optional `ட்` in Alvazhi.
    if last_l == "ண்" && is_stop {
        let rel = if state.flags.is_panputhogai_stem
            && context.relation == GrammaticalRelation::Unspecified
        {
            GrammaticalRelation::Alvazhi
        } else {
            context.effective_relation()
        };
        if rel == GrammaticalRelation::Vetrumai
            && (matches!(state.left.as_str(), "பரண்" | "கவண்")
                || context.lexical_class == Some(LexicalClass::BranchName))
        {
            let mut s = state;
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{}{}", s.left, s.right);
            s.steps.push(DerivationStep {
                sutra: 211,
                rule_id: "nannool_211_nna_branch_and_measure".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            return vec![s];
        }
        if rel == GrammaticalRelation::Alvazhi
            && (context.lexical_class == Some(LexicalClass::FoodSesame)
                || (state.left == "சாண்" && context.lexical_class == Some(LexicalClass::MeasureWord)))
        {
            let mut s_nat = state.clone();
            let before = format!("{} + {}", s_nat.left, s_nat.right);
            let after = format!("{}{}", s_nat.left, s_nat.right);
            s_nat.steps.push(DerivationStep {
                sutra: 211,
                rule_id: "nannool_211_nna_branch_and_measure".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            s_nat.priority_rank = 25;

            let mut s_mut = state;
            let new_left = replace_last_unit(left_units, "ட்");
            let before = format!("{} + {}", s_mut.left, s_mut.right);
            let after = format!("{new_left} + {}", s_mut.right);
            s_mut.steps.push(DerivationStep {
                sutra: 211,
                rule_id: "nannool_211_nna_branch_and_measure".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s_mut.left = new_left;
            s_mut.optional_variant = true;
            s_mut.priority_rank = 40;
            return vec![s_nat, s_mut];
        }
    }

    // Sutra 216: `குயின்`, `ஊன்` stay natural in Vetrumai.
    if is_stop && tables::in_closed_class("kuyin_oon_stems", &state.left) {
        let mut s = state;
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{}{}", s.left, s.right);
        s.steps.push(DerivationStep {
            sutra: 216,
            rule_id: "nannool_216_kuyin_oon_iyalbu".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
        return vec![s];
    }

    // Sutra 218: `நின்` natural in Vetrumai; `தன்`/`என்` optional (`தன்பகை`/`தற்பகை`).
    if is_stop && context.effective_relation() == GrammaticalRelation::Vetrumai {
        if state.left == "நின்" {
            let mut s = state;
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{}{}", s.left, s.right);
            s.steps.push(DerivationStep {
                sutra: 218,
                rule_id: "nannool_218_than_en_nin".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            return vec![s];
        }
        if matches!(state.left.as_str(), "தன்" | "என்") && state.right != "கு" {
            let mut s_nat = state.clone();
            let before = format!("{} + {}", s_nat.left, s_nat.right);
            let after = format!("{}{}", s_nat.left, s_nat.right);
            s_nat.steps.push(DerivationStep {
                sutra: 218,
                rule_id: "nannool_218_than_en_nin".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            s_nat.priority_rank = 25;

            let mut s_mut = state;
            let new_left = replace_last_unit(left_units, "ற்");
            let before = format!("{} + {}", s_mut.left, s_mut.right);
            let after = format!("{new_left} + {}", s_mut.right);
            s_mut.steps.push(DerivationStep {
                sutra: 218,
                rule_id: "nannool_218_than_en_nin".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s_mut.left = new_left;
            s_mut.optional_variant = true;
            s_mut.priority_rank = 40;
            return vec![s_nat, s_mut];
        }
        // Sutra 213: `மீன்` optional (`மீன்கண்` / `மீற்கண்`).
        if state.left == "மீன்" {
            let mut s_nat = state.clone();
            let before = format!("{} + {}", s_nat.left, s_nat.right);
            let after = format!("{}{}", s_nat.left, s_nat.right);
            s_nat.steps.push(DerivationStep {
                sutra: 213,
                rule_id: "nannool_213_meen_vetrumai".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            s_nat.priority_rank = 30;
            let mut s_mut = state;
            let new_left = replace_last_unit(left_units, "ற்");
            let before = format!("{} + {}", s_mut.left, s_mut.right);
            let after = format!("{new_left} + {}", s_mut.right);
            s_mut.steps.push(DerivationStep {
                sutra: 213,
                rule_id: "nannool_213_meen_vetrumai".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s_mut.left = new_left;
            s_mut.optional_variant = true;
            s_mut.priority_rank = 40;
            return vec![s_nat, s_mut];
        }
    }

    // Sutra 214: `தேன்` special optionality (natural / `ன்`-drop before Mellinam / `ன்`-drop + stop or nasal before Vallinam).
    if state.left == "தேன்" {
        let rm = unit_mei(first_r).unwrap_or_default();
        let mut s_nat = state.clone();
        let before = format!("தேன் + {}", s_nat.right);
        let after = format!("தேன்{}", s_nat.right);
        s_nat.steps.push(DerivationStep {
            sutra: 214,
            rule_id: "nannool_214_then_special".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
        s_nat.priority_rank = 25;
        let mut out = vec![s_nat];
        if matches!(rm.as_str(), "ஞ்" | "ம்") {
            let mut s_drop = state;
            s_drop.steps.push(DerivationStep {
                sutra: 214,
                rule_id: "nannool_214_then_special".to_owned(),
                stage: 3,
                transform: AlterationKind::Keduthal,
                before: format!("தேன் + {}", s_drop.right),
                after: format!("தே + {}", s_drop.right),
            });
            s_drop.left = "தே".to_owned();
            s_drop.optional_variant = true;
            s_drop.priority_rank = 40;
            out.push(s_drop);
            return out;
        }
        if is_vallinam_initial_unit(first_r) {
            let mut s_stop = state.clone();
            s_stop.steps.push(DerivationStep {
                sutra: 214,
                rule_id: "nannool_214_then_special".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before: format!("தேன் + {}", s_stop.right),
                after: format!("தே{rm} + {}", s_stop.right),
            });
            s_stop.left = format!("தே{rm}");
            s_stop.optional_variant = true;
            s_stop.priority_rank = 40;
            out.push(s_stop);
            if let Some(nasal) = homorganic_nasal(&rm) {
                let mut s_nas = state;
                s_nas.steps.push(DerivationStep {
                    sutra: 214,
                    rule_id: "nannool_214_then_special".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thirithal,
                    before: format!("தேன் + {}", s_nas.right),
                    after: format!("தே{nasal} + {}", s_nas.right),
                });
                s_nas.left = format!("தே{nasal}");
                s_nas.optional_variant = true;
                s_nas.priority_rank = 45;
                out.push(s_nas);
            }
            return out;
        }
    }

    // Sutra 215: `எகின்` (SwanEkin) stays natural or takes `+ அ` + stop/nasal.
    if state.left == "எகின்" && context.lexical_class == Some(LexicalClass::SwanEkin) && is_stop
    {
        let rm = unit_mei(first_r).unwrap_or_default();
        let mut s_nat = state.clone();
        s_nat.steps.push(DerivationStep {
            sutra: 215,
            rule_id: "nannool_215_ekin_swan".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before: format!("எகின் + {}", s_nat.right),
            after: format!("எகின்{}", s_nat.right),
        });
        s_nat.priority_rank = 25;
        let mut s_stop = state.clone();
        s_stop.steps.push(DerivationStep {
            sutra: 215,
            rule_id: "nannool_215_ekin_swan".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before: format!("எகின் + {}", s_stop.right),
            after: format!("எகின{rm} + {}", s_stop.right),
        });
        s_stop.left = format!("எகின{rm}");
        s_stop.optional_variant = true;
        s_stop.priority_rank = 40;
        let mut out = vec![s_nat, s_stop];
        if let Some(nasal) = homorganic_nasal(&rm) {
            let mut s_nas = state;
            s_nas.steps.push(DerivationStep {
                sutra: 215,
                rule_id: "nannool_215_ekin_swan".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before: format!("எகின் + {}", s_nas.right),
                after: format!("எகின{nasal} + {}", s_nas.right),
            });
            s_nas.left = format!("எகின{nasal}");
            s_nas.optional_variant = true;
            s_nas.priority_rank = 45;
            out.push(s_nas);
        }
        return out;
    }

    if is_stop {
        let stop_repl = if last_l == "ண்" {
            "ட்"
        } else {
            "ற்"
        };
        let make_stop = |mut s: BoundaryState, req_ctx: Option<String>, rank: u32| {
            let new_left = replace_last_unit(left_units, stop_repl);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 209,
                rule_id: "nannool_209_nna_na_vetrumai_stop".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s.left = new_left;
            if req_ctx.is_some() {
                s.required_context = req_ctx;
            }
            s.priority_rank = s.priority_rank.min(rank);
            s
        };

        let eff_rel = if state.flags.is_panputhogai_stem
            && context.relation == GrammaticalRelation::Unspecified
        {
            GrammaticalRelation::Alvazhi
        } else {
            context.effective_relation()
        };
        return match eff_rel {
            GrammaticalRelation::Vetrumai => vec![make_stop(state, None, 35)],
            GrammaticalRelation::Alvazhi => vec![emit_209_iyalbu(state, None, 40)],
            GrammaticalRelation::Unspecified => vec![
                emit_209_iyalbu(state.clone(), None, 40),
                make_stop(state, Some("vetrumai".to_owned()), 50),
            ],
        };
    }

    let primary = emit_209_iyalbu(state.clone(), None, 45);
    if unit_mei(first_r).as_deref() == Some("ய்") {
        if let Some(alt_206) = make_206_minority_i(state, left_units, last_l) {
            return vec![primary, alt_206];
        }
    }
    vec![primary]
}

/// Sutra 206: Contested minority `இ`-insertion after non-`ய்` consonants before `ய` (`வேளியாவன்`, `மண்ணியாது`).
fn make_206_minority_i(
    mut s: BoundaryState,
    left_units: &[&str],
    last_l: &str,
) -> Option<BoundaryState> {
    if last_l == "ய்" {
        return None;
    }
    let fused_i = compose_uyirmei(last_l, "இ").ok()?;
    let new_left = if is_thanikkuril_otru(&s.left) {
        format!("{}{fused_i}", s.left)
    } else {
        replace_last_unit(left_units, &fused_i)
    };
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left}{}", s.right);
    s.steps.push(DerivationStep {
        sutra: 206,
        rule_id: "nannool_206_minority_i_before_ya".to_owned(),
        stage: 3,
        transform: AlterationKind::Thonral,
        before,
        after,
    });
    s.left = new_left;
    s.optional_variant = true;
    s.poetic = false;
    s.priority_rank = 50;
    Some(s)
}

fn emit_209_iyalbu(mut s: BoundaryState, req_ctx: Option<String>, rank: u32) -> BoundaryState {
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{}{}", s.left, s.right);
    s.steps.push(DerivationStep {
        sutra: 209,
        rule_id: "nannool_209_nna_na_iyalbu".to_owned(),
        stage: 3,
        transform: AlterationKind::Iyalbu,
        before,
        after,
    });
    if req_ctx.is_some() {
        s.required_context = req_ctx;
    }
    s.priority_rank = s.priority_rank.min(rank);
    s
}

fn apply_magaram(
    state: BoundaryState,
    context: &PunarchiContext,
    left_units: &[&str],
    first_r: &str,
) -> Vec<BoundaryState> {
    let rel = if state.flags.is_panputhogai_stem
        && context.relation == GrammaticalRelation::Unspecified
    {
        GrammaticalRelation::Alvazhi
    } else {
        context.effective_relation()
    };
    let is_compound_alvazhi = matches!(
        context.subtype,
        Some(ContextSubtype::Panputhogai | ContextSubtype::Uvamaithogai)
    );
    let is_vowel = is_independent_uyir(first_r);
    let right_mei = unit_mei(first_r);

    let make_elision_chain = |mut s: BoundaryState, req_ctx: Option<String>, rank: u32| {
        let new_left = drop_last_unit(left_units);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 219,
            rule_id: "nannool_219_magara_elision".to_owned(),
            stage: 3,
            transform: AlterationKind::Keduthal,
            before,
            after,
        });
        s.left = new_left;
        s.flags.is_derived_final = true;
        if req_ctx.is_some() {
            s.required_context = req_ctx;
        }
        s.priority_rank = s.priority_rank.min(rank);
        // After deleting `ம்`, apply vowel-final rules (162 before V, 165 before stops).
        if is_vowel || is_vallinam_initial_unit(first_r) {
            uyireeru::apply_stage_3c_vowel_final(s, context)
        } else {
            vec![s]
        }
    };

    let make_nasal_assim =
        |mut s: BoundaryState, nasal: &str, req_ctx: Option<String>, rank: u32| {
            let new_left = replace_last_unit(left_units, nasal);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 219,
                rule_id: "nannool_219_magara_nasal_assimilation".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s.left = new_left;
            if req_ctx.is_some() {
                s.required_context = req_ctx;
            }
            s.priority_rank = s.priority_rank.min(rank);
            s
        };

    let make_220_iyalbu = |mut s: BoundaryState, req_ctx: Option<String>, rank: u32| {
        if !is_vowel && s.steps.is_empty() {
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{}{}", s.left, s.right);
            s.steps.push(DerivationStep {
                sutra: 220,
                rule_id: "nannool_220_magara_alvazhi_iyalbu".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
        } else if is_vowel {
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{} + {}", s.left, s.right);
            s.steps.push(DerivationStep {
                sutra: 220,
                rule_id: "nannool_220_magara_alvazhi_iyalbu".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
        }
        if req_ctx.is_some() {
            s.required_context = req_ctx;
        }
        s.priority_rank = s.priority_rank.min(rank);
        s
    };

    // Sutra 221: `நும், தம், எம், நம்` + `ஞ`/`ந` -> `ஞ்`/`ந்` (before `ம` stays natural).
    if tables::in_closed_class("num_tham_em_nam_stems", &state.left) {
        if let Some(rm) = right_mei.as_deref() {
            if matches!(rm, "ஞ்" | "ந்") {
                let mut s = state;
                let new_left = replace_last_unit(left_units, rm);
                let before = format!("{} + {}", s.left, s.right);
                let after = format!("{new_left} + {}", s.right);
                s.steps.push(DerivationStep {
                    sutra: 221,
                    rule_id: "nannool_221_num_tham_em_nam".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thirithal,
                    before,
                    after,
                });
                s.left = new_left;
                return vec![s];
            }
            if rm == "ம்" {
                return vec![state];
            }
        }
    }

    // Case 1: Before Vallinam `{க, ச, த, ப}`.
    if let Some(rm) = right_mei.as_deref() {
        if matches!(rm, "க்" | "ச்" | "த்" | "ப்") {
            let thanikkuril_m = is_thanikkuril_otru(&state.left) || state.flags.is_short_chariyai_m;
            if thanikkuril_m {
                // `நம் + கை -> நங்கை`, `நம் + பண்பு -> நம்பண்பு`.
                if let Some(nasal) = homorganic_nasal(rm) {
                    if rm != "ப்" {
                        return vec![make_nasal_assim(state, nasal, None, 25)];
                    }
                }
                return vec![state];
            }

            return match rel {
                GrammaticalRelation::Vetrumai => {
                    let mut out = make_elision_chain(state.clone(), None, 35);
                    // Sutra 220 (`வேற்றுமை மப்போய் வலிமெலி உறழ்வும்`): optional homorganic nasal (`குளங்கரை`, `நிலங்கடந்தான்`).
                    // Skip for Case2 (`255`) where `255` already handles nasal forms like `மரங்குறைத்தான்`.
                    if matches!(rm, "க்" | "ச்" | "த்")
                        && context.subtype != Some(ContextSubtype::Case2)
                    {
                        if let Some(nasal) = homorganic_nasal(rm) {
                            let new_left = replace_last_unit(left_units, nasal);
                            let mut s_nas = state;
                            let before = format!("{} + {}", s_nas.left, s_nas.right);
                            let after = format!("{new_left} + {}", s_nas.right);
                            s_nas.steps.push(DerivationStep {
                                sutra: 220,
                                rule_id: "nannool_220_magara_vetrumai_nasal".to_owned(),
                                stage: 3,
                                transform: AlterationKind::Thirithal,
                                before,
                                after,
                            });
                            s_nas.left = new_left;
                            s_nas.optional_variant = true;
                            s_nas.priority_rank = 50;
                            out.push(s_nas);
                        }
                    }
                    out
                }
                GrammaticalRelation::Alvazhi if is_compound_alvazhi => {
                    make_elision_chain(state, None, 35)
                }
                GrammaticalRelation::Alvazhi => {
                    if rm == "ப்" {
                        vec![state]
                    } else if let Some(nasal) = homorganic_nasal(rm) {
                        vec![make_nasal_assim(state, nasal, None, 35)]
                    } else {
                        vec![state]
                    }
                }
                GrammaticalRelation::Unspecified => {
                    let mut out = Vec::new();
                    if rm == "ப்" {
                        out.push(state.clone());
                    } else if let Some(nasal) = homorganic_nasal(rm) {
                        out.push(make_nasal_assim(state.clone(), nasal, None, 35));
                    }
                    out.extend(make_elision_chain(state, Some("vetrumai".to_owned()), 50));
                    out
                }
            };
        }

        // Case 2: Before Mellinam (`ஞ, ந, ம`): Sutra 219 deletes `ம்` in both Alvazhi and Vetrumai.
        if matches!(rm, "ஞ்" | "ந்" | "ம்") {
            return make_elision_chain(state, None, 35);
        }
    }

    // Case 3: Before Vowel or Idaiyinam (`ய, ர, ல, வ, ழ, ள`).
    // Appended short-vowel `ம்`-final Chariyais (`எல்லாநம்`, `எல்லார்தம்`, `எல்லீர்நும்`) retain `ம்` before vowels so Stage 3D `205` doubles `ம்`.
    if is_vowel && (is_thanikkuril_otru(&state.left) || state.flags.is_short_chariyai_m) {
        return vec![state];
    }
    match rel {
        GrammaticalRelation::Vetrumai => make_elision_chain(state, None, 35),
        GrammaticalRelation::Alvazhi if is_compound_alvazhi => make_elision_chain(state, None, 35),
        GrammaticalRelation::Alvazhi => vec![make_220_iyalbu(state, None, 30)],
        GrammaticalRelation::Unspecified => {
            let ends_akara_m = left_units.len() >= 2
                && left_units.last().copied() == Some("ம்")
                && crate::phonology::unit_vowel(left_units[left_units.len() - 2]).as_deref()
                    == Some("அ");
            let mut out = if is_vowel && ends_akara_m && !is_thanikkuril_otru(&state.left) {
                make_elision_chain(state.clone(), Some("vetrumai".to_owned()), 45)
            } else {
                make_elision_chain(state.clone(), None, 35)
            };
            out.push(make_220_iyalbu(state, Some("alvazhi".to_owned()), 50));
            out
        }
    }
}

fn apply_ya_ra_zha(
    state: BoundaryState,
    context: &PunarchiContext,
    left_units: &[&str],
    last_l: &str,
    first_r: &str,
) -> Vec<BoundaryState> {
    if is_independent_uyir(first_r) {
        return vec![state];
    }
    let Some(rm) = unit_mei(first_r) else {
        return vec![state];
    };

    // Sutra 158: `குறில் + ய்` before `{ஞ, ந, ம}` doubles the nasal (`மெய் + ஞான்றது -> மெய்ஞ்ஞான்றது`).
    if last_l == "ய்" && is_thanikkuril_otru(&state.left) && matches!(rm.as_str(), "ஞ்" | "ந்" | "ம்")
    {
        let mut s = state;
        let new_left = format!("{}{rm}", s.left);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 158,
            rule_id: "nannool_158_kuril_y_ai_no_tu_nasal_double".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }

    // Sutra 224 (`மேல்`): non-Thanikkuril `ய்` deletes before `ய` (`காய் + யாது -> காயாது`).
    if last_l == "ய்" && !is_thanikkuril_otru(&state.left) && rm == "ய்" {
        let mut s = state;
        let new_left = drop_last_unit(left_units);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 224,
            rule_id: "nannool_224_ya_elision_before_ya".to_owned(),
            stage: 3,
            transform: AlterationKind::Keduthal,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }

    if is_vallinam_initial_unit(first_r) {
        // Direction `கிழக்கு -> கீழ்` (Sutra 186): primary doubled (`கீழ்க்கடல்`, `கீழ்த்திசை`), optional natural (`கீழ்கரை`).
        if state.left == "கீழ்" && state.flags.is_direction_keezh {
            let mut s_dbl = state.clone();
            let new_left = format!("கீழ்{rm}");
            let before = format!("கீழ் + {}", s_dbl.right);
            let after = format!("{new_left} + {}", s_dbl.right);
            s_dbl.steps.push(DerivationStep {
                sutra: 224,
                rule_id: "nannool_224_ya_ra_zha_valimigal".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s_dbl.left = new_left;
            s_dbl.optional_variant = false;
            s_dbl.priority_rank = 25;

            let mut s_nat = state;
            s_nat.optional_variant = true;
            s_nat.priority_rank = 45;
            return vec![s_dbl, s_nat];
        }
        // Sutra 226: lexical `கீழ்` ("below") + stop -> primary natural (`கீழ்குலம்`), optional doubled (`கீழ்க்குலம்`).
        if state.left == "கீழ்" {
            let mut s_nat = state.clone();
            let before = format!("கீழ் + {}", s_nat.right);
            let after = format!("கீழ்{}", s_nat.right);
            s_nat.steps.push(DerivationStep {
                sutra: 226,
                rule_id: "nannool_226_keezh_vikalpam".to_owned(),
                stage: 3,
                transform: AlterationKind::Iyalbu,
                before,
                after,
            });
            s_nat.priority_rank = 25;

            let mut s_dbl = state;
            let new_left = format!("கீழ்{rm}");
            let before = format!("கீழ் + {}", s_dbl.right);
            let after = format!("{new_left} + {}", s_dbl.right);
            s_dbl.steps.push(DerivationStep {
                sutra: 226,
                rule_id: "nannool_226_keezh_vikalpam".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s_dbl.left = new_left;
            s_dbl.optional_variant = true;
            s_dbl.priority_rank = 45;
            return vec![s_nat, s_dbl];
        }

        let make_double = |mut s: BoundaryState, req_ctx: Option<String>, rank: u32| {
            let new_left = format!("{}{rm}", s.left);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 224,
                rule_id: "nannool_224_ya_ra_zha_valimigal".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s.left = new_left;
            if req_ctx.is_some() {
                s.required_context = req_ctx;
            }
            s.priority_rank = s.priority_rank.min(rank);
            s
        };
        let make_iyalbu = |mut s: BoundaryState, rank: u32| {
            if s.steps.is_empty() {
                let before = format!("{} + {}", s.left, s.right);
                let after = format!("{}{}", s.left, s.right);
                s.steps.push(DerivationStep {
                    sutra: 224,
                    rule_id: "nannool_224_ya_ra_zha_iyalbu".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Iyalbu,
                    before,
                    after,
                });
            }
            s.priority_rank = s.priority_rank.min(rank);
            s
        };

        if state.flags.block_165 && !state.flags.force_165 {
            return vec![make_iyalbu(state, 40)];
        }

        let alvazhi_doubles = matches!(
            context.subtype,
            Some(ContextSubtype::Panputhogai | ContextSubtype::Uvamaithogai)
        ) || (last_l == "ய்"
            && context.subtype == Some(ContextSubtype::Vinaiyecham));

        return match context.effective_relation() {
            GrammaticalRelation::Vetrumai => vec![make_double(state, None, 35)],
            GrammaticalRelation::Alvazhi if alvazhi_doubles => {
                vec![make_double(state, None, 35)]
            }
            GrammaticalRelation::Alvazhi => vec![make_iyalbu(state, 40)],
            GrammaticalRelation::Unspecified => vec![
                make_iyalbu(state.clone(), 40),
                make_double(state, Some("vetrumai".to_owned()), 50),
            ],
        };
    }

    vec![state]
}

fn apply_la_lla(
    state: BoundaryState,
    context: &PunarchiContext,
    left_units: &[&str],
    last_l: &str,
    first_r: &str,
) -> Vec<BoundaryState> {
    if is_independent_uyir(first_r) {
        return vec![state];
    }

    let thanikkuril = is_thanikkuril_otru(&state.left);
    let stop_repl = if last_l == "ல்" {
        "ற்"
    } else {
        "ட்"
    };
    let nasal_repl = if last_l == "ல்" {
        "ன்"
    } else {
        "ண்"
    };
    let rel = if state.flags.is_panputhogai_stem
        && context.relation == GrammaticalRelation::Unspecified
    {
        GrammaticalRelation::Alvazhi
    } else {
        context.effective_relation()
    };

    // Sutra 230: Derived `ல்`/`ள்`-final verbal nouns (`ஆடல் + கடிது -> ஆடல்கடிது`) stay natural before Vallinam.
    if context.lexical_class == Some(LexicalClass::VerbalNounDerived) {
        let mut s = state;
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{}{}", s.left, s.right);
        s.steps.push(DerivationStep {
            sutra: 230,
            rule_id: "nannool_230_derived_verbal_noun_iyalbu".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
        return vec![s];
    }

    // Case 1: 237-mutated `ந` -> non-Thanikkuril deletes (229), Thanikkuril becomes nasal `ன்`/`ண்` (227).
    if matches!(state.flags.triggered_237, Some((_, 'ந'))) {
        if !thanikkuril && !state.flags.block_229 {
            return vec![emit_229_elision(state, left_units, None, 20)];
        }
        return vec![emit_227_nasal(state, left_units, nasal_repl, 35)];
    }

    // Case 2: 237-mutated `த` -> NEVER emit `*ல்த`/`*ள்த` (Sutra 117).
    if matches!(state.flags.triggered_237, Some((_, 'த'))) {
        if state.flags.block_229 {
            return vec![emit_227_stop(state, left_units, stop_repl, None, false, 35)];
        }
        if !thanikkuril {
            return match rel {
                GrammaticalRelation::Vetrumai => {
                    vec![emit_227_stop(state, left_units, stop_repl, None, false, 35)]
                }
                GrammaticalRelation::Alvazhi => {
                    vec![emit_229_elision(state, left_units, None, 20)]
                }
                GrammaticalRelation::Unspecified => vec![
                    emit_229_elision(state.clone(), left_units, None, 20),
                    emit_227_stop(
                        state,
                        left_units,
                        stop_repl,
                        Some("vetrumai".to_owned()),
                        false,
                        50,
                    ),
                ],
            };
        }

        // Thanikkuril `ல்/ள் + த`: Vetrumai -> 227; Alvazhi/Unspecified -> 227 + optional 228 (`ஃற/ஃட`).
        if rel == GrammaticalRelation::Vetrumai {
            return vec![emit_227_stop(state, left_units, stop_repl, None, false, 35)];
        }
        // Canonical grammatical term `அல் + திணை -> அஃறிணை` uses Sutra 228 directly.
        if state.left == "அல்" && state.right == "றிணை" {
            return vec![emit_228_aytham(state, left_units, false, 25)];
        }
        return vec![
            emit_227_stop(state.clone(), left_units, stop_repl, None, false, 30),
            emit_228_aytham(state, left_units, true, 45),
        ];
    }

    let Some(rm) = unit_mei(first_r) else {
        return vec![state];
    };

    // Case 3: `{க, ச, ப}` stops.
    if matches!(rm.as_str(), "க்" | "ச்" | "ப்") {
        // Sutra 232: `நெல், செல், கொல், சொல்` in Alvazhi obligatorily mutate `ல் -> ற்` (`நெற்கடிது`).
        if rel == GrammaticalRelation::Alvazhi
            && tables::in_closed_class("nel_sel_kol_sol_stems", &state.left)
        {
            let mut s = state;
            let new_left = replace_last_unit(left_units, "ற்");
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 232,
                rule_id: "nannool_232_nel_sel_kol_sol".to_owned(),
                stage: 3,
                transform: AlterationKind::Thirithal,
                before,
                after,
            });
            s.left = new_left;
            return vec![s];
        }

        let fixed_alvazhi_mut = state.flags.is_panputhogai_stem
            || matches!(
                context.subtype,
                Some(
                    ContextSubtype::Panputhogai
                        | ContextSubtype::Uvamaithogai
                        | ContextSubtype::Vinaiyecham
                )
            );
        let fixed_alvazhi_nat = matches!(
            context.subtype,
            Some(
                ContextSubtype::Ezhuvai
                    | ContextSubtype::Ummaithogai
                    | ContextSubtype::Vili
                    | ContextSubtype::VinaiMutru
                    | ContextSubtype::Vinaithogai
            )
        );

        return match rel {
            GrammaticalRelation::Vetrumai => {
                vec![emit_227_stop(state, left_units, stop_repl, None, false, 35)]
            }
            GrammaticalRelation::Alvazhi if fixed_alvazhi_mut => {
                vec![emit_227_stop(state, left_units, stop_repl, None, false, 35)]
            }
            GrammaticalRelation::Alvazhi if fixed_alvazhi_nat => {
                vec![emit_227_iyalbu(state, 40)]
            }
            GrammaticalRelation::Alvazhi | GrammaticalRelation::Unspecified => vec![
                emit_227_iyalbu(state.clone(), 40),
                emit_227_stop(state, left_units, stop_repl, None, true, 45),
            ],
        };
    }

    // Case 4: Mellinam (`ஞ, ம`) -> mandatory `ல் -> ன்`, `ள் -> ண்` (227).
    if matches!(rm.as_str(), "ஞ்" | "ம்") {
        return vec![emit_227_nasal(state, left_units, nasal_repl, 35)];
    }

    // Case 5: Idaiyinam -> natural (227); before `ய`, also emit contested minority Sutra 206 (`வேளியாவன்`).
    let primary = emit_227_iyalbu(state.clone(), 45);
    if rm == "ய்" {
        if let Some(alt_206) = make_206_minority_i(state, left_units, last_l) {
            return vec![primary, alt_206];
        }
    }
    vec![primary]
}

fn emit_227_stop(
    mut s: BoundaryState,
    left_units: &[&str],
    stop_repl: &str,
    req_ctx: Option<String>,
    optional: bool,
    rank: u32,
) -> BoundaryState {
    let new_left = replace_last_unit(left_units, stop_repl);
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 227,
        rule_id: "nannool_227_la_lla_stop_mutation".to_owned(),
        stage: 3,
        transform: AlterationKind::Thirithal,
        before,
        after,
    });
    s.left = new_left;
    if req_ctx.is_some() {
        s.required_context = req_ctx;
    }
    if optional {
        s.optional_variant = true;
    }
    s.priority_rank = s.priority_rank.min(rank);
    s
}

fn emit_227_nasal(
    mut s: BoundaryState,
    left_units: &[&str],
    nasal_repl: &str,
    rank: u32,
) -> BoundaryState {
    let new_left = replace_last_unit(left_units, nasal_repl);
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 227,
        rule_id: "nannool_227_la_lla_nasal_mutation".to_owned(),
        stage: 3,
        transform: AlterationKind::Thirithal,
        before,
        after,
    });
    s.left = new_left;
    s.priority_rank = s.priority_rank.min(rank);
    s
}

fn emit_227_iyalbu(mut s: BoundaryState, rank: u32) -> BoundaryState {
    if s.steps.is_empty() {
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{}{}", s.left, s.right);
        s.steps.push(DerivationStep {
            sutra: 227,
            rule_id: "nannool_227_la_lla_iyalbu".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
    }
    s.priority_rank = s.priority_rank.min(rank);
    s
}

fn emit_228_aytham(
    mut s: BoundaryState,
    left_units: &[&str],
    optional: bool,
    rank: u32,
) -> BoundaryState {
    let new_left = replace_last_unit(left_units, "ஃ");
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 228,
        rule_id: "nannool_228_la_lla_aytham".to_owned(),
        stage: 3,
        transform: AlterationKind::Thirithal,
        before,
        after,
    });
    s.left = new_left;
    if optional {
        s.optional_variant = true;
    }
    s.priority_rank = s.priority_rank.min(rank);
    s
}

fn emit_229_elision(
    mut s: BoundaryState,
    left_units: &[&str],
    req_ctx: Option<String>,
    rank: u32,
) -> BoundaryState {
    let new_left = drop_last_unit(left_units);
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 229,
        rule_id: "nannool_229_la_lla_elision".to_owned(),
        stage: 3,
        transform: AlterationKind::Keduthal,
        before,
        after,
    });
    s.left = new_left;
    if req_ctx.is_some() {
        s.required_context = req_ctx;
    }
    s.priority_rank = s.priority_rank.min(rank);
    s
}

/// Sutra 235: `அவ், இவ், உவ்` in Alvazhi (+ Vallinam -> `ஃ`, + Mellinam -> nasal, + Idaiyinam -> natural).
fn apply_vagaram(
    state: BoundaryState,
    context: &PunarchiContext,
    left_units: &[&str],
    first_r: &str,
) -> Vec<BoundaryState> {
    if is_independent_uyir(first_r) {
        return vec![state];
    }
    if !matches!(state.left.as_str(), "அவ்" | "இவ்" | "உவ்") {
        return vec![state];
    }
    if context.effective_relation() == GrammaticalRelation::Vetrumai {
        return vec![state];
    }

    let Some(rm) = unit_mei(first_r) else {
        return vec![state];
    };
    if is_vallinam_initial_unit(first_r) {
        let mut s = state;
        let new_left = replace_last_unit(left_units, "ஃ");
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 235,
            rule_id: "nannool_235_suttu_v_alvazhi".to_owned(),
            stage: 3,
            transform: AlterationKind::Thirithal,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }
    if matches!(rm.as_str(), "ஞ்" | "ந்" | "ம்") {
        let mut s = state;
        let new_left = replace_last_unit(left_units, &rm);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 235,
            rule_id: "nannool_235_suttu_v_alvazhi".to_owned(),
            stage: 3,
            transform: AlterationKind::Thirithal,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }
    let mut s = state;
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{}{}", s.left, s.right);
    s.steps.push(DerivationStep {
        sutra: 235,
        rule_id: "nannool_235_suttu_v_alvazhi".to_owned(),
        stage: 3,
        transform: AlterationKind::Iyalbu,
        before,
        after,
    });
    vec![s]
}
