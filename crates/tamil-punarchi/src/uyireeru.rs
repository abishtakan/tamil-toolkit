//! Chapter 1 (*Uyireerrup Punariyal*, Sutras 151-203) Stage 1C and Stage 3C vowel-final rules.

use crate::context::{
    AlterationKind, ContextSubtype, DerivationStep, GrammaticalRelation, LexicalClass,
    PunarchiContext,
};
use crate::phonology::{
    classify_ugaram, homorganic_nasal, is_independent_uyir, is_vallinam_initial_unit, unit_mei,
    unit_vowel, UgaramClass,
};
use crate::pipeline::BoundaryState;
use crate::tables;
use tamil_core::{compose_uyirmei, split_uyirmei, Letters};

/// Stage 3A Overrides (`252` `அத்தின் அகரம்`, `163` demonstratives/interrogatives + `106` `ஙனம்` + `R163.4` non-udambadumei `வ்`).
///
/// Runs strictly BEFORE Stage 3B/3C (`162`, `158`), returning `Some(Vec<BoundaryState>)` when an override fires.
pub fn apply_stage_3a(
    state: BoundaryState,
    context: &PunarchiContext,
) -> Option<Vec<BoundaryState>> {
    let l_owned = state.left.clone();
    let r_owned = state.right.clone();
    let l = l_owned.as_str();
    let r = r_owned.as_str();

    // 1. Sutra 252 (`அத்தின் அகரம்`): `அ`-final + `அத்து` (`is_chariyai_attu`) -> drop initial `அ` of `அத்து` BEFORE `162`!
    if state.flags.is_chariyai_attu && r == "அத்து" {
        let last_l = Letters::new(l).last().unwrap_or("");
        if unit_vowel(last_l).as_deref() == Some("அ") {
            let mut s = state;
            let before = format!("{} + அத்து", s.left);
            s.right = "த்து".to_owned();
            let after = format!("{}{}", s.left, s.right);
            s.steps.push(DerivationStep {
                sutra: 252,
                rule_id: "nannool_252_attin_akaram".to_owned(),
                stage: 3,
                transform: AlterationKind::Keduthal,
                before,
                after,
            });
            return Some(vec![s]);
        }
    }

    // 2. R163.4 (`நெறி`): Non-udambadumei `வ்` insertion (`விண்+அத்து->விண்வத்து`, `செல்+உழி->செல்வுழி`, `சார்+உழி->சார்வுழி`).
    if matches!((l, r), ("விண்", "அத்து") | ("செல்", "உழி") | ("சார்", "உழி"))
    {
        let mut s = state;
        let new_left = format!("{l}வ்");
        let before = format!("{l} + {r}");
        let after = format!("{new_left} + {r}");
        s.steps.push(DerivationStep {
            sutra: 163,
            rule_id: "nannool_163_non_udambadumei_v".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        s.flags.suppress_205 = true;
        return Some(vec![s]);
    }

    // 3. Sutra 106 & R163.4: `யா/ஆ/ஈ/ஊ + ஙனம் -> யாங்ஙனம் / ஆங்ஙனம் / ...`.
    if r == "ஙனம்" && matches!(l, "யா" | "ஆ" | "ஈ" | "ஊ") {
        let mut s = state;
        let new_left = format!("{l}ங்");
        let before = format!("{l} + {r}");
        let after = format!("{new_left} + {r}");
        s.steps.push(DerivationStep {
            sutra: 163,
            rule_id: "nannool_163_deictic_geminate".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        return Some(vec![s]);
    }

    // 4. Sutra 163.3 (poetic): lengthened demonstrative `ஆ` + vowel -> prose `வ்` (162) + poetic `ய்` (`ஆ + இடை -> ஆயிடை`).
    let r_first = Letters::new(r).next().unwrap_or("");
    if context.poetic
        && l == "ஆ"
        && context.lexical_class == Some(LexicalClass::Demonstrative)
        && is_independent_uyir(r_first)
    {
        let primary =
            insert_udambadumei(state.clone(), "வ்", "nannool_162_udambadumei_v", false, 25);
        let mut s = state;
        let new_left = "ஆய்".to_owned();
        let before = format!("{l} + {r}");
        let after = format!("{new_left} + {r}");
        s.steps.push(DerivationStep {
            sutra: 163,
            rule_id: "nannool_163_poetic_aa_y".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        s.optional_variant = true;
        s.poetic = true;
        s.priority_rank = 55;
        return Some(vec![primary, s]);
    }

    // 5. Sutra 163 (`அ, இ, உ, எ` demonstratives/interrogatives) + Sutra 106 (`ஙனம்`):
    //    - Before Vowel or `ய` -> insert `வ்` (then Stage 3D `205` doubles `வ்` before Vowel -> `அவ்வணி`, `இவ்வணி`).
    //    - Before `ஙனம்` -> Sutra 106 (`அங்ஙனம்`, `இங்ஙனம்`, `உங்ஙனம்`, `எங்ஙனம்`).
    //    - Before any other consonant (`க, ச, த, ப, ஞ, ந, ம, வ`) -> geminate that initial consonant (`அக்குதிரை`, `எஞ்ஞாலம்`).
    if tables::in_closed_class("deictic_interrogative_clitics", l) {
        if is_independent_uyir(r_first) || unit_mei(r_first).as_deref() == Some("ய்") {
            let mut s = state;
            let new_left = format!("{l}வ்");
            let before = format!("{l} + {r}");
            let after = format!("{new_left} + {r}");
            s.steps.push(DerivationStep {
                sutra: 163,
                rule_id: "nannool_163_deictic_v".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s.left = new_left;
            return Some(vec![s]);
        }
        if let Some(rm) = unit_mei(r_first) {
            let mut s = state;
            let new_left = format!("{l}{rm}");
            let before = format!("{l} + {r}");
            let after = format!("{new_left} + {r}");
            let (sutra, rule_id) = if r == "ஙனம்" {
                (106, "nannool_106_mozhi_muthal_nga_bound")
            } else {
                (163, "nannool_163_deictic_geminate")
            };
            s.steps.push(DerivationStep {
                sutra,
                rule_id: rule_id.to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s.left = new_left;
            return Some(vec![s]);
        }
    }

    None
}

/// Attested Sutra 183 *Vetrumai* non-doubling pair exceptions (`நாடுகிழவோன்`, `காடகம்`, `மிடறணியல்`).
const SUTRA_183_VETRUMAI_EXCEPTIONS: &[(&str, &str)] =
    &[("நாடு", "கிழவோன்"), ("காடு", "அகம்"), ("மிடறு", "அணியல்")];

/// Attested Sutra 183 *Alvazhi* doubling pairs (`காட்டரண்`, `களிற்றுயானை`, etc.).
const SUTRA_183_ALVAZHI_DOUBLERS: &[(&str, &str)] = &[
    ("காடு", "அரண்"),
    ("களிறு", "யானை"),
    ("ஏறு", "ஏனம்"),
    ("வரடு", "ஆடு"),
    ("குருடு", "கோழி"),
    ("வெளிறு", "பனை"),
];

/// Stage 1C (Sutra 183): Pre-elision `டு/று -> ட்டு/ற்று` doubling on Nedil/Uyir-thodar Kurriyalugaram.
///
/// Must execute before Stage 3 (`164` elision and `165` Valimigal) and unlocks `force_165 = true` per Sutra 182.
pub fn apply_stage_1c(state: BoundaryState, context: &PunarchiContext) -> Vec<BoundaryState> {
    if context.subtype == Some(ContextSubtype::Case2)
        && crate::urupu::is_sutra_255_pair(&state.left, &state.right)
    {
        return vec![state];
    }
    let ugaram = classify_ugaram(&state.left);
    if !matches!(ugaram, UgaramClass::NedilThodar | UgaramClass::UyirThodar) {
        return vec![state];
    }

    let left_src = state.left.clone();
    let units: Vec<&str> = Letters::new(&left_src).collect();
    let Some(&last) = units.last() else {
        return vec![state];
    };
    let doubled_tail = match last {
        "டு" => "ட்டு",
        "று" => "ற்று",
        _ => return vec![state],
    };

    let rel = context.effective_relation();
    let is_vetrumai_exc =
        SUTRA_183_VETRUMAI_EXCEPTIONS.contains(&(state.left.as_str(), state.right.as_str()));
    let is_alvazhi_doubler =
        SUTRA_183_ALVAZHI_DOUBLERS.contains(&(state.left.as_str(), state.right.as_str()));

    let make_doubled =
        |mut s: BoundaryState, req_ctx: Option<String>, rank: u32| -> BoundaryState {
            let prefix: String = units[..units.len() - 1].concat();
            let new_left = format!("{prefix}{doubled_tail}");
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 183,
                rule_id: "nannool_183_du_ru_gemination".to_owned(),
                stage: 1,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s.left = new_left;
            s.flags.is_derived_final = true;
            s.flags.force_165 = true;
            if req_ctx.is_some() {
                s.required_context = req_ctx;
            }
            s.priority_rank = s.priority_rank.min(rank);
            s
        };

    match rel {
        GrammaticalRelation::Vetrumai => {
            if is_vetrumai_exc {
                vec![state]
            } else {
                vec![make_doubled(state, None, 20)]
            }
        }
        GrammaticalRelation::Alvazhi => {
            if is_alvazhi_doubler {
                vec![make_doubled(state, None, 20)]
            } else {
                vec![state]
            }
        }
        GrammaticalRelation::Unspecified => {
            if is_alvazhi_doubler {
                vec![make_doubled(state, None, 20)]
            } else if is_vetrumai_exc {
                vec![state]
            } else {
                let vetrumai_branch = make_doubled(state.clone(), Some("vetrumai".to_owned()), 50);
                vec![state, vetrumai_branch]
            }
        }
    }
}

/// Stage 3C core vowel-final morphophonemics (`93`, `158`, `162`, `164`, `165`, `181`, `182`).
pub fn apply_stage_3c_vowel_final(
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

    let Some(final_vowel) = unit_vowel(last_l) else {
        return vec![state];
    };

    // Case A: Vowel-final + Vowel-initial (`164` Kurriyalugaram > `162` Udambadumei; Mutriyalugaram `162` > opt `164.3`).
    if is_independent_uyir(first_r) {
        return apply_vowel_plus_vowel(state, &left_units, &final_vowel);
    }

    let Some(right_mei) = unit_mei(first_r) else {
        return vec![state];
    };

    // Case B: Kurriyalugaram + `ய`-initial -> Sutra 93/164 Kurriyaligaram (`உ -> இ`).
    let ugaram = classify_ugaram(&state.left);
    if right_mei == "ய்" && ugaram.is_kurriyalugaram() {
        if let Ok(parts) = split_uyirmei(last_l) {
            if let Ok(mutated) = compose_uyirmei(&parts.mei, "இ") {
                let mut s = state;
                let prefix: String = left_units[..left_units.len() - 1].concat();
                let new_left = format!("{prefix}{mutated}");
                let before = format!("{} + {}", s.left, s.right);
                let after = format!("{new_left} + {}", s.right);
                s.steps.push(DerivationStep {
                    sutra: 93,
                    rule_id: "nannool_093_kurriyaligaram".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thirithal,
                    before,
                    after,
                });
                s.left = new_left;
                return vec![s];
            }
        }
    }

    // Mutriyalugaram optional `உ -> இ` before `ய` (Sutra 164.3, e.g. `கதவு + யாது -> கதவியாது`).
    if right_mei == "ய்"
        && ugaram == UgaramClass::Mutriyalugaram
        && tables::in_closed_class("mutriyalugaram_elision_stems", &state.left)
    {
        let mut out = vec![apply_158_iyalbu(state.clone())];
        if let Ok(parts) = split_uyirmei(last_l) {
            if let Ok(mutated) = compose_uyirmei(&parts.mei, "இ") {
                let mut alt = state;
                let prefix: String = left_units[..left_units.len() - 1].concat();
                let new_left = format!("{prefix}{mutated}");
                let before = format!("{} + {}", alt.left, alt.right);
                let after = format!("{new_left} + {}", alt.right);
                alt.steps.push(DerivationStep {
                    sutra: 164,
                    rule_id: "nannool_164_mutriyalugaram_y_igaram".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thirithal,
                    before,
                    after,
                });
                alt.left = new_left;
                alt.optional_variant = true;
                alt.priority_rank = 60;
                out.push(alt);
            }
        }
        return out;
    }

    // Case C: Sutra 158 — Nasals (`ஞ, ந, ம`) and Approximants (`ய, வ`).
    if matches!(right_mei.as_str(), "ஞ்" | "ந்" | "ம்" | "ய்" | "வ்") {
        let is_single_ai = left_units.len() == 1 && final_vowel == "ஐ";
        let is_no_or_tu = matches!(state.left.as_str(), "நொ" | "து");
        let doubles_nasal =
            (is_single_ai || is_no_or_tu) && matches!(right_mei.as_str(), "ஞ்" | "ந்" | "ம்");
        let doubles_approx = is_no_or_tu && matches!(right_mei.as_str(), "ய்" | "வ்");

        if doubles_nasal || doubles_approx {
            let mut s = state;
            let new_left = format!("{}{right_mei}", s.left);
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

        // Default Sutra 158 natural join when no earlier Stage 1-3 rule altered the boundary.
        return vec![apply_158_iyalbu(state)];
    }

    // Case D: Vallinam initial (`க, ச, த, ப`) -> Sutras 165, 181, 182.
    if is_vallinam_initial_unit(first_r) {
        return apply_vowel_plus_vallinam(state, context, &right_mei, ugaram);
    }

    vec![state]
}

fn apply_158_iyalbu(mut s: BoundaryState) -> BoundaryState {
    if s.steps.is_empty() || s.steps.last().is_some_and(|st| st.sutra == 172) {
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{}{}", s.left, s.right);
        s.steps.push(DerivationStep {
            sutra: 158,
            rule_id: "nannool_158_nasal_approximant_iyalbu".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
    }
    s
}

fn apply_vowel_plus_vowel(
    state: BoundaryState,
    left_units: &[&str],
    final_vowel: &str,
) -> Vec<BoundaryState> {
    let ugaram = classify_ugaram(&state.left);

    // Sutra 164.1: Kurriyalugaram + Vowel -> elide `உ` (`மெய் விட்டோடும்`).
    if ugaram.is_kurriyalugaram() {
        if let Ok(parts) = split_uyirmei(left_units[left_units.len() - 1]) {
            let mut s = state;
            let prefix: String = left_units[..left_units.len() - 1].concat();
            let new_left = format!("{prefix}{}", parts.mei);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 164,
                rule_id: "nannool_164_kurriyalugaram_elision".to_owned(),
                stage: 3,
                transform: AlterationKind::Keduthal,
                before,
                after,
            });
            s.left = new_left;
            return vec![s];
        }
    }

    // Sutra 162: Udambadumei (`இ, ஈ, ஐ -> ய்`; `ஏ -> ய் | வ்`; others -> `வ்`).
    let mut branches = Vec::new();
    match final_vowel {
        "இ" | "ஈ" | "ஐ" => {
            branches.push(insert_udambadumei(
                state,
                "ய்",
                "nannool_162_udambadumei_y",
                false,
                40,
            ));
        }
        "ஏ" => {
            branches.push(insert_udambadumei(
                state.clone(),
                "ய்",
                "nannool_162_udambadumei_y",
                false,
                40,
            ));
            branches.push(insert_udambadumei(
                state,
                "வ்",
                "nannool_162_udambadumei_v",
                true,
                45,
            ));
        }
        _ => {
            let primary =
                insert_udambadumei(state.clone(), "வ்", "nannool_162_udambadumei_v", false, 40);
            branches.push(primary);

            // Sutra 164.3: Attested Mutriyalugaram stems (`கதவு`, `அது`, `இது`, ...) optionally elide `உ`.
            if ugaram == UgaramClass::Mutriyalugaram
                && tables::in_closed_class("mutriyalugaram_elision_stems", &state.left)
            {
                if let Ok(parts) = split_uyirmei(left_units[left_units.len() - 1]) {
                    let mut alt = state;
                    let prefix: String = left_units[..left_units.len() - 1].concat();
                    let new_left = format!("{prefix}{}", parts.mei);
                    let before = format!("{} + {}", alt.left, alt.right);
                    let after = format!("{new_left} + {}", alt.right);
                    alt.steps.push(DerivationStep {
                        sutra: 164,
                        rule_id: "nannool_164_mutriyalugaram_elision".to_owned(),
                        stage: 3,
                        transform: AlterationKind::Keduthal,
                        before,
                        after,
                    });
                    alt.left = new_left;
                    alt.flags.suppress_205 = true;
                    alt.optional_variant = true;
                    alt.priority_rank = 60;
                    branches.push(alt);
                }
            }
        }
    }

    branches
}

fn insert_udambadumei(
    mut s: BoundaryState,
    glide: &str,
    rule_id: &str,
    optional: bool,
    rank: u32,
) -> BoundaryState {
    let new_left = format!("{}{glide}", s.left);
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 162,
        rule_id: rule_id.to_owned(),
        stage: 3,
        transform: AlterationKind::Thonral,
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

fn apply_vowel_plus_vallinam(
    state: BoundaryState,
    context: &PunarchiContext,
    right_mei: &str,
    ugaram: UgaramClass,
) -> Vec<BoundaryState> {
    // Sutra 165.2: `நொ` and `து` obligatorily double `க, ச, த, ப`.
    if matches!(state.left.as_str(), "நொ" | "து") {
        let mut s = state;
        let new_left = format!("{}{right_mei}", s.left);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 165,
            rule_id: "nannool_165_no_tu_valimigal".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }

    if state.flags.block_165 && !state.flags.force_165 {
        return vec![state];
    }

    let rel = context.effective_relation();
    let left_last_u = Letters::new(&state.left).last().unwrap_or("");
    let left_vowel = unit_vowel(left_last_u);

    // Sutra 159: Vowel-final RationalNoun / CommonNoun blocks 165 doubling unless `force_165` (`கு` per 242.2).
    if !state.flags.force_165
        && matches!(
            context.lexical_class,
            Some(LexicalClass::RationalNoun | LexicalClass::CommonNoun)
        )
    {
        if tables::is_overt_case_suffix(&state.right) {
            return vec![state];
        }
        return vec![emit_kurriyal_iyalbu(
            state,
            159,
            "nannool_159_uyartinai_poduppeyar_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 160: Final interrogative clitics `ஆ, ஏ, ஓ` stay natural before Vallinam.
    if !state.flags.force_165
        && context.lexical_class == Some(LexicalClass::Interrogative)
        && matches!(left_vowel.as_deref(), Some("ஆ" | "ஏ" | "ஓ"))
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            160,
            "nannool_160_interrogative_clitic_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 161: Second-person finite verbs stay natural before Vallinam.
    if !state.flags.force_165 && context.subtype == Some(ContextSubtype::SecondPersonVerb) {
        return vec![emit_kurriyal_iyalbu(
            state,
            161,
            "nannool_161_second_person_verb_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 166: Vowel-final tree names (`மா`, `விளா`, ...) insert homorganic nasal in Vetrumai (`மாங்காய்`).
    if rel == GrammaticalRelation::Vetrumai && context.lexical_class == Some(LexicalClass::TreeName)
    {
        if let Some(nasal) = homorganic_nasal(right_mei) {
            let mut s = state;
            let new_left = format!("{}{nasal}", s.left);
            let before = format!("{} + {}", s.left, s.right);
            let after = format!("{new_left} + {}", s.right);
            s.steps.push(DerivationStep {
                sutra: 166,
                rule_id: "nannool_166_tree_name_nasal".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            s.left = new_left;
            return vec![s];
        }
    }

    // Sutra 167: Blocks Vallinam doubling after `அ`-finals in 6 Alvazhi contexts
    // (non-rational plural verbs, அன்ன/அத்தனை/இத்தனை/எத்தனை, உம்மைத்தொகை, வியங்கோள், செய்யிய வினையெச்சம், அம்ம இடைச்சொல்).
    let is_seyyiya_vinaiyecham = context.subtype == Some(ContextSubtype::Vinaiyecham)
        && state.left.ends_with('ய')
        && Letters::new(&state.left)
            .collect::<Vec<_>>()
            .windows(2)
            .last()
            .and_then(|pair| unit_vowel(pair[0]))
            .as_deref()
            == Some("இ");
    if !state.flags.force_165
        && rel == GrammaticalRelation::Alvazhi
        && ((left_vowel.as_deref() == Some("அ")
            && (matches!(
                context.subtype,
                Some(
                    ContextSubtype::Viyankol
                        | ContextSubtype::Ummaithogai
                        | ContextSubtype::VinaiMutru
                        | ContextSubtype::KurippuVinaiMutru
                        | ContextSubtype::Peyarecham
                        | ContextSubtype::Ezhuvai
                        | ContextSubtype::Vili
                        | ContextSubtype::Vinaithogai
                )
            ) || is_seyyiya_vinaiyecham
                || matches!(
                    context.lexical_class,
                    Some(LexicalClass::NonRationalNoun | LexicalClass::CliticParticle)
                )
                || matches!(state.left.as_str(), "அன்ன" | "இன்ன" | "என்ன" | "அம்ம")))
            || matches!(state.left.as_str(), "அத்தனை" | "இத்தனை" | "எத்தனை"))
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            167,
            "nannool_167_akara_alvazhi_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 171: Blocks Vallinam doubling after `ஆ`-finals in Alvazhi (negative plural verb, vili, peyarecham, imperative/viyankol, ummaithogai).
    if !state.flags.force_165
        && rel == GrammaticalRelation::Alvazhi
        && left_vowel.as_deref() == Some("ஆ")
        && (context.lexical_class == Some(LexicalClass::NegativePluralVerb)
            || matches!(
                context.subtype,
                Some(
                    ContextSubtype::Vili
                        | ContextSubtype::Peyarecham
                        | ContextSubtype::Imperative
                        | ContextSubtype::Viyankol
                        | ContextSubtype::Ummaithogai
                        | ContextSubtype::VinaiMutru
                        | ContextSubtype::KurippuVinaiMutru
                        | ContextSubtype::Ezhuvai
                        | ContextSubtype::Vinaithogai
                )
            ))
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            171,
            "nannool_171_aakara_alvazhi_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 176: Non-rational `இ`/`ஐ`-final nouns in Alvazhi block 165 (except panputhogai/uvamaithogai).
    if !state.flags.force_165
        && rel == GrammaticalRelation::Alvazhi
        && matches!(left_vowel.as_deref(), Some("இ" | "ஐ"))
        && context.lexical_class == Some(LexicalClass::NonRationalNoun)
        && !matches!(
            context.subtype,
            Some(ContextSubtype::Panputhogai | ContextSubtype::Uvamaithogai)
        )
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            176,
            "nannool_176_ikara_aikara_alvazhi_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 179: Mutriyalugaram in `அது/இது/உது`, Case-3 `-ஒடு`, Case-6 `-அது`, and `vinaithogai` stays natural.
    if !state.flags.force_165
        && ugaram == UgaramClass::Mutriyalugaram
        && (context.subtype == Some(ContextSubtype::Vinaithogai)
            || context.lexical_class == Some(LexicalClass::Demonstrative)
            || state.left.ends_with("ஒடு")
            || (rel == GrammaticalRelation::Alvazhi
                && matches!(state.left.as_str(), "அது" | "இது" | "உது")))
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            179,
            "nannool_179_mutriyalugaram_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 176 & Valimigaa Alvazhi subtypes: finite verbs, participles, subject/vocative/coordinated compounds stay natural.
    if !state.flags.force_165
        && rel == GrammaticalRelation::Alvazhi
        && matches!(
            context.subtype,
            Some(
                ContextSubtype::Ezhuvai
                    | ContextSubtype::Vili
                    | ContextSubtype::Peyarecham
                    | ContextSubtype::VinaiMutru
                    | ContextSubtype::KurippuVinaiMutru
                    | ContextSubtype::Ummaithogai
                    | ContextSubtype::Vinaithogai
            )
        )
    {
        let (sutra, rid) = if matches!(left_vowel.as_deref(), Some("இ" | "ஐ")) {
            (176, "nannool_176_ikara_aikara_alvazhi_iyalbu")
        } else {
            (153, "nannool_153_iyalbu_passthrough")
        };
        return vec![emit_kurriyal_iyalbu(state, sutra, rid, None, 25)];
    }

    // Sutra 255: Case-2 Vetrumaithogai (`உண்மை + கண்டான்`) stays natural without Sutra 165 doubling
    // on underived vowel stems when no overt `ஐ` is present (allowing `219`-elided `மர -> மரக்குறைத்தான்`).
    if !state.flags.force_165
        && !state.flags.is_derived_final
        && context.subtype == Some(ContextSubtype::Case2)
        && !tables::is_overt_case_suffix(&state.right)
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            255,
            "nannool_255_case2_thogai_equivalence",
            None,
            25,
        )];
    }

    // Sutra 181: Locative particles (`அங்கு, இங்கு, உங்கு, எங்கு, யாண்டு`) double Vallinam (`அங்குக்கொண்டான்`).
    if context.lexical_class == Some(LexicalClass::LocativeParticle) {
        let mut s = state;
        let new_left = format!("{}{right_mei}", s.left);
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{new_left} + {}", s.right);
        s.steps.push(DerivationStep {
            sutra: 181,
            rule_id: "nannool_181_locative_particle_valimigal".to_owned(),
            stage: 3,
            transform: AlterationKind::Thonral,
            before,
            after,
        });
        s.left = new_left;
        return vec![s];
    }

    // Sutra 201: `ஏ`/`ஓ` clitic particles in first word block 165 doubling (`அவனே + கொண்டான் -> அவனேகொண்டான்`).
    if !state.flags.force_165
        && context.lexical_class == Some(LexicalClass::CliticParticle)
        && matches!(left_vowel.as_deref(), Some("ஏ" | "ஓ"))
    {
        return vec![emit_kurriyal_iyalbu(
            state,
            201,
            "nannool_201_ee_oo_clitic_iyalbu",
            None,
            25,
        )];
    }

    // Sutra 178: `பீ, நீ, மீ` in Alvazhi block 165 (`மீ` also allows optional doubling/nasal).
    if matches!(state.left.as_str(), "பீ" | "நீ" | "மீ") && rel == GrammaticalRelation::Alvazhi
    {
        let mut s_nat = state.clone();
        let before = format!("{} + {}", s_nat.left, s_nat.right);
        let after = format!("{}{}", s_nat.left, s_nat.right);
        s_nat.steps.push(DerivationStep {
            sutra: 178,
            rule_id: "nannool_178_pee_nee_mee".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before,
            after,
        });
        if state.left == "மீ" {
            let mut s_dbl = apply_165_valimigal(state.clone(), right_mei);
            s_dbl.optional_variant = true;
            s_dbl.priority_rank = 45;
            let mut out = vec![s_nat, s_dbl];
            if let Some(nasal) = homorganic_nasal(right_mei) {
                let mut s_nas = state;
                let new_left = format!("{}{nasal}", s_nas.left);
                let before = format!("{} + {}", s_nas.left, s_nas.right);
                let after = format!("{new_left} + {}", s_nas.right);
                s_nas.steps.push(DerivationStep {
                    sutra: 178,
                    rule_id: "nannool_178_pee_nee_mee".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thonral,
                    before,
                    after,
                });
                s_nas.left = new_left;
                s_nas.optional_variant = true;
                s_nas.priority_rank = 50;
                out.push(s_nas);
            }
            return out;
        }
        return vec![s_nat];
    }

    // Sutra 175: Taste `புளி` (`TastePuli`) -> primary `165` (`புளிக்கறி`) + optional nasal (`புளிங்கறி`).
    if state.left == "புளி" && context.lexical_class == Some(LexicalClass::TastePuli) {
        let primary = apply_165_valimigal(state.clone(), right_mei);
        let mut out = vec![primary];
        if let Some(nasal) = homorganic_nasal(right_mei) {
            let mut alt = state;
            let new_left = format!("புளி{nasal}");
            let before = format!("{} + {}", alt.left, alt.right);
            let after = format!("{new_left} + {}", alt.right);
            alt.steps.push(DerivationStep {
                sutra: 175,
                rule_id: "nannool_175_suvai_puli".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            alt.left = new_left;
            alt.optional_variant = true;
            alt.priority_rank = 50;
            out.push(alt);
        }
        return out;
    }

    // Sutra 200: `பூ` + Vallinam -> primary Sutra 200 homorganic nasal (`பூங்கொடி`, `பூஞ்சோலை`), optional Sutra 165 (`பூக்கொடி`).
    if state.left == "பூ" && !state.flags.force_165 {
        let mut out = Vec::new();
        if let Some(nasal) = homorganic_nasal(right_mei) {
            let mut primary = state.clone();
            let new_left = format!("பூ{nasal}");
            let before = format!("{} + {}", primary.left, primary.right);
            let after = format!("{new_left} + {}", primary.right);
            primary.steps.push(DerivationStep {
                sutra: 200,
                rule_id: "nannool_200_poo_nasal".to_owned(),
                stage: 3,
                transform: AlterationKind::Thonral,
                before,
                after,
            });
            primary.left = new_left;
            primary.optional_variant = false;
            primary.priority_rank = 25;
            out.push(primary);
        }
        let mut alt = apply_165_valimigal(state, right_mei);
        alt.optional_variant = true;
        alt.priority_rank = 45;
        out.push(alt);
        return out;
    }

    // Sutras 181 & 182: Kurriyalugaram non-doubling classes (unless `force_165` was set by Sutra 183).
    if ugaram.is_kurriyalugaram() && !state.flags.force_165 {
        let blocked_alvazhi = ugaram != UgaramClass::Vanthodar;
        let blocked_vetrumai = matches!(
            ugaram,
            UgaramClass::Idaithodar
                | UgaramClass::AythathThodar
                | UgaramClass::NedilThodar
                | UgaramClass::UyirThodar
        );

        match rel {
            GrammaticalRelation::Alvazhi if blocked_alvazhi => {
                return vec![emit_kurriyal_iyalbu(
                    state,
                    181,
                    "nannool_181_kurriyalugaram_alvazhi_iyalbu",
                    None,
                    25,
                )];
            }
            GrammaticalRelation::Vetrumai if blocked_vetrumai => {
                return vec![emit_kurriyal_iyalbu(
                    state,
                    182,
                    "nannool_182_kurriyalugaram_vetrumai_iyalbu",
                    None,
                    25,
                )];
            }
            GrammaticalRelation::Unspecified => {
                if blocked_alvazhi && blocked_vetrumai {
                    return vec![emit_kurriyal_iyalbu(
                        state,
                        181,
                        "nannool_181_kurriyalugaram_alvazhi_iyalbu",
                        None,
                        25,
                    )];
                }
                if blocked_alvazhi && !blocked_vetrumai {
                    // Menthodar: Alvazhi natural (181), Vetrumai doubles (165).
                    let alvazhi = emit_kurriyal_iyalbu(
                        state.clone(),
                        181,
                        "nannool_181_kurriyalugaram_alvazhi_iyalbu",
                        None,
                        25,
                    );
                    let mut vetrumai = apply_165_valimigal(state, right_mei);
                    vetrumai.required_context = Some("vetrumai".to_owned());
                    vetrumai.priority_rank = 50;
                    return vec![alvazhi, vetrumai];
                }
            }
            _ => {}
        }
    }

    // Default Sutra 165 *Valimigal*.
    vec![apply_165_valimigal(state, right_mei)]
}

fn emit_kurriyal_iyalbu(
    mut s: BoundaryState,
    sutra: u16,
    rule_id: &str,
    req_ctx: Option<String>,
    rank: u32,
) -> BoundaryState {
    if s.steps.is_empty() {
        let before = format!("{} + {}", s.left, s.right);
        let after = format!("{}{}", s.left, s.right);
        s.steps.push(DerivationStep {
            sutra,
            rule_id: rule_id.to_owned(),
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
}

pub fn apply_165_valimigal(mut s: BoundaryState, right_mei: &str) -> BoundaryState {
    let new_left = format!("{}{right_mei}", s.left);
    let before = format!("{} + {}", s.left, s.right);
    let after = format!("{new_left} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 165,
        rule_id: "nannool_165_valimigal".to_owned(),
        stage: 3,
        transform: AlterationKind::Thonral,
        before,
        after,
    });
    s.left = new_left;
    s
}
