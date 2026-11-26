//! Stage 1A (`136` Panpuppeyar), Stage 1B (numerals `188-199`, directions `186-187`, pronouns `247`,
//! named stems `168-170, 174, 177, 203, 222, 233`), and Stage 1C (`183-185`).

use crate::context::{
    AlterationKind, ContextSubtype, DerivationStep, GrammaticalRelation, LexicalClass,
    PunarchiContext,
};
use crate::phonology::{homorganic_nasal, is_independent_uyir, is_vallinam_initial_unit, unit_mei};
use crate::pipeline::{BoundaryFlags, BoundaryState};
use crate::tables;
use crate::uyireeru;
use tamil_core::Letters;

/// Execute Stage 1A -> 1B -> 1C returning one or more candidate `BoundaryState`s
/// (plus any pre-finalized terminal states marked via `direct_surface` when a closed-class
/// rule emits its final form directly, e.g., `170` self-compounds, `194`, `199`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Stage1Output {
    pub state: BoundaryState,
    /// When `true`, `state.left` already holds the complete joined surface (e.g., `170`, `194`, `199`).
    pub finalized: bool,
}

impl Stage1Output {
    pub fn pending(state: BoundaryState) -> Self {
        Self {
            state,
            finalized: false,
        }
    }

    pub fn done(state: BoundaryState) -> Self {
        Self {
            state,
            finalized: true,
        }
    }
}

pub fn apply_stage_1(first: &str, second: &str, context: &PunarchiContext) -> Vec<Stage1Output> {
    let initial = BoundaryState::new(first.to_owned(), second.to_owned());

    // Stage 1A: Panpuppeyar `-மை` cascade (Sutra 136).
    let after_1a = apply_stage_1a_panpuppeyar(initial, context);

    // Stage 1B: Closed-class reductions (Numerals 188-199, Directions 186-187, Pronouns 247, Named stems).
    let mut after_1b = Vec::new();
    for item in after_1a {
        if item.finalized {
            after_1b.push(item);
        } else {
            after_1b.extend(apply_stage_1b_closed_class(item.state, context));
        }
    }

    // Stage 1C: Pre-elision Kurriyalugaram mutations (`183`, `184`, `185`).
    let mut after_1c = Vec::new();
    for item in after_1b {
        if item.finalized {
            after_1c.push(item);
        } else {
            let states = apply_stage_1c_all(item.state, context);
            for s in states {
                after_1c.push(Stage1Output::pending(s));
            }
        }
    }

    after_1c
}

/// Stage 1A (Sutra 136): 8-operation *Panpuppeyar* `-மை` cascade.
fn apply_stage_1a_panpuppeyar(
    state: BoundaryState,
    context: &PunarchiContext,
) -> Vec<Stage1Output> {
    let is_panpu_stem = state.left.ends_with("மை")
        && (context.lexical_class == Some(LexicalClass::QualityNoun)
            || context.subtype == Some(ContextSubtype::Panputhogai)
            || tables::in_closed_class("panpuppeyar_mai_stems", &state.left));

    let is_pure_case = matches!(
        state.right.as_str(),
        "ஐ" | "ஆல்" | "ஆன்" | "ஒடு" | "ஓடு" | "கு" | "இன்" | "ஆது"
    ) || (context.relation == GrammaticalRelation::Vetrumai
        && tables::is_overt_case_suffix(&state.right));
    if !is_panpu_stem || is_pure_case {
        return vec![Stage1Output::pending(state)];
    }

    let Some(base) = state.left.strip_suffix("மை") else {
        return vec![Stage1Output::pending(state)];
    };
    if base.is_empty() {
        return vec![Stage1Output::pending(state)];
    }

    let right_first = Letters::new(&state.right).next().unwrap_or("");
    let right_is_vowel = is_independent_uyir(right_first);
    let right_mei = unit_mei(right_first);

    // Op 1: ஈறு போதல் (`-மை` drop).
    let mut s = state.clone();
    let before1 = format!("{} + {}", s.left, s.right);
    let after1 = format!("{base} + {}", s.right);
    s.steps.push(DerivationStep {
        sutra: 136,
        rule_id: "nannool_136_panpuppeyar_eeru_pothal".to_owned(),
        stage: 1,
        transform: AlterationKind::Keduthal,
        before: before1,
        after: after1,
    });
    s.left = base.to_owned();
    s.flags.is_derived_final = true;
    s.flags.is_panputhogai_stem = true;

    // Specific attested multi-op cascades per Nannool 136 (Viruttiyurai p.199, Kandigai 136):
    // 1. `பசு` (< `பசுமை`):
    if base == "பசு" {
        if right_is_vowel {
            // Op 3 (`ஆதி நீடல்`): `பசு -> பாசு` (`பாசடை`, `பாசி`), then Stage 3 `164`+`204`.
            let before = format!("{} + {}", s.left, s.right);
            s.left = "பாசு".to_owned();
            s.steps.push(DerivationStep {
                sutra: 136,
                rule_id: "nannool_136_panpuppeyar_aathi_needal".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before,
                after: format!("{} + {}", s.left, s.right),
            });
            return vec![Stage1Output::pending(s)];
        }
        if let Some(rm) = right_mei.as_deref() {
            if let Some(nasal) = homorganic_nasal(rm) {
                // Op 8 + Op 4 (`பசு -> பை`) + Op 7 (`இனமிகல்`: `பைந்`, `பைங்`).
                let before4 = format!("{} + {}", s.left, s.right);
                s.left = "பை".to_owned();
                s.steps.push(DerivationStep {
                    sutra: 136,
                    rule_id: "nannool_136_panpuppeyar_adi_agaram_ai".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before: before4,
                    after: format!("{} + {}", s.left, s.right),
                });
                let before7 = format!("{} + {}", s.left, s.right);
                s.left = format!("பை{nasal}");
                s.steps.push(DerivationStep {
                    sutra: 136,
                    rule_id: "nannool_136_panpuppeyar_inamigal".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thonral,
                    before: before7,
                    after: format!("{} + {}", s.left, s.right),
                });
                // Surface is `பைந்தமிழ்` / `பைங்கண்` directly without re-running `ன்/ங்` rules!
                s.left = format!("{}{}", s.left, s.right);
                if let Some(last_step) = s.steps.last_mut() {
                    last_step.after = s.left.clone();
                }
                return vec![Stage1Output::done(s)];
            }
        }
    }

    // 1b. `முது` (< `முதுமை`) + vowel: Op 3 (`ஆதி நீடல்`: `முது -> மூது`) -> `164`+`204` (`மூதூர்`, `மூதில்`).
    if base == "முது" && right_is_vowel {
        let before = format!("{} + {}", s.left, s.right);
        s.left = "மூது".to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_aathi_needal".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before,
            after: format!("{} + {}", s.left, s.right),
        });
        return vec![Stage1Output::pending(s)];
    }

    // 2. `செம்` (< `செம்மை`) + `ஆ`/`ஆம்பல்`: Op 3 (`சேம்`) + Op 6 (`சேத்`) -> `சேதாம்பல்`/`சேதா`.
    if base == "செம்" && matches!(s.right.as_str(), "ஆ" | "ஆம்பல்") {
        let before3 = format!("{} + {}", s.left, s.right);
        s.left = "சேம்".to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_aathi_needal".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: before3,
            after: format!("{} + {}", s.left, s.right),
        });
        let before6 = format!("{} + {}", s.left, s.right);
        s.left = "சேத்".to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_mey_thirithal".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: before6,
            after: format!("{} + {}", s.left, s.right),
        });
        return vec![Stage1Output::pending(s)];
    }

    // 3. `நன்`/`வன்` (< `நன்மை`/`வன்மை`): Op 6 (`நன் -> நல்`, `வன் -> வல்`) -> Stage 3 `205`+`204` (`நல்லன்`) or `227` Panputhogai (`நற்குணம்`, `நற்றமிழ்`).
    if matches!(base, "நன்" | "வன்") {
        let new_stem = if base == "நன்" {
            "நல்"
        } else {
            "வல்"
        };
        let before6 = format!("{} + {}", s.left, s.right);
        s.left = new_stem.to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_mey_thirithal".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: before6,
            after: format!("{} + {}", s.left, s.right),
        });
        return vec![Stage1Output::pending(s)];
    }

    // 4. `சிறு`, `வெறு`, `நெடு`, `குறு`, `புது` + Vowel: Op 5 (`தன்னொற்று இரட்டல்`: `சிற்று`, `வெற்று`, `நெட்டு`, `குற்று`, `புத்து`) -> `164`+`204`.
    if right_is_vowel && matches!(base, "சிறு" | "வெறு" | "நெடு" | "குறு" | "புது")
    {
        let doubled = match base {
            "சிறு" => "சிற்று",
            "வெறு" => "வெற்று",
            "நெடு" => "நெட்டு",
            "குறு" => "குற்று",
            _ => "புத்து",
        };
        let before5 = format!("{} + {}", s.left, s.right);
        s.left = doubled.to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_thannotru_irattal".to_owned(),
            stage: 1,
            transform: AlterationKind::Thonral,
            before: before5,
            after: format!("{} + {}", s.left, s.right),
        });
        return vec![Stage1Output::pending(s)];
    }

    // 5. `கரு`, `பெரு` + Vowel: Op 2 (`கரி`/`பெரி`, `கரியன்`, `பெரியன்`); for `பெரு` + non-`அன்` noun (`ஊர்`, `இன்பம்`), Op 3 `பேரு` primary (`பேரூர்`, `பேரின்பம்`).
    if right_is_vowel && matches!(base, "கரு" | "பெரு") {
        if base == "பெரு" && s.right != "அன்" {
            let mut s_long = s.clone();
            let before3 = format!("{} + {}", s_long.left, s_long.right);
            s_long.left = "பேர்".to_owned();
            s_long.steps.push(DerivationStep {
                sutra: 136,
                rule_id: "nannool_136_panpuppeyar_aathi_needal".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: before3,
                after: format!("{} + {}", s_long.left, s_long.right),
            });
            s_long.priority_rank = 20;

            let before2 = format!("{} + {}", s.left, s.right);
            s.left = "பெரி".to_owned();
            s.steps.push(DerivationStep {
                sutra: 136,
                rule_id: "nannool_136_panpuppeyar_idai_ugaram_i".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: before2,
                after: format!("{} + {}", s.left, s.right),
            });
            s.optional_variant = true;
            s.priority_rank = 45;
            return vec![Stage1Output::pending(s_long), Stage1Output::pending(s)];
        }
        let mutated = if base == "கரு" {
            "கரி"
        } else {
            "பெரி"
        };
        let before2 = format!("{} + {}", s.left, s.right);
        s.left = mutated.to_owned();
        s.steps.push(DerivationStep {
            sutra: 136,
            rule_id: "nannool_136_panpuppeyar_idai_ugaram_i".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: before2,
            after: format!("{} + {}", s.left, s.right),
        });
        return vec![Stage1Output::pending(s)];
    }

    // 6. Qualitative vowel stems (`கரு, பெரு, பரு, குறு, நெடு, பழ, அரு, இள, கடு, கொடு`) + Vallinam stop: Op 7 (`இனமிகல்`).
    if matches!(
        base,
        "கரு"
            | "பெரு"
            | "பரு"
            | "குறு"
            | "நெடு"
            | "பழ"
            | "அரு"
            | "இள"
            | "கடு"
            | "கொடு"
    ) {
        if let Some(rm) = right_mei.as_deref() {
            if is_vallinam_initial_unit(right_first) {
                if let Some(nasal) = homorganic_nasal(rm) {
                    let before7 = format!("{} + {}", s.left, s.right);
                    s.left = format!("{base}{nasal}{}", s.right);
                    s.steps.push(DerivationStep {
                        sutra: 136,
                        rule_id: "nannool_136_panpuppeyar_inamigal".to_owned(),
                        stage: 1,
                        transform: AlterationKind::Thonral,
                        before: before7,
                        after: s.left.clone(),
                    });
                    return vec![Stage1Output::done(s)];
                }
            }
        }
    }

    // 7. `செம்`, `வெம்` (`ம்`-final Thanikkuril stems):
    //    - Before `க், ச், த், ஞ், ந்` -> assimilate `ம்` (`செந்தாமரை`, `செங்கதிர்`, `செந்நீர்`).
    //    - Before `ப், ம்` and other consonants -> retain `ம்` cleanly without Stage 3 `219` elision (`செம்மலர்`, `வெம்மதி`, `செம்பொன்`).
    if base.ends_with("ம்") && !right_is_vowel {
        if let Some(rm) = right_mei.as_deref() {
            let stem_no_m = base.strip_suffix("ம்").unwrap_or(base);
            if matches!(rm, "க்" | "ச்" | "த்") {
                if let Some(nasal) = homorganic_nasal(rm) {
                    let before = format!("{} + {}", s.left, s.right);
                    s.left = format!("{stem_no_m}{nasal}{}", s.right);
                    s.steps.push(DerivationStep {
                        sutra: 219,
                        rule_id: "nannool_219_magara_nasal_assimilation".to_owned(),
                        stage: 3,
                        transform: AlterationKind::Thirithal,
                        before,
                        after: s.left.clone(),
                    });
                    return vec![Stage1Output::done(s)];
                }
            }
            if matches!(rm, "ஞ்" | "ந்") {
                let before = format!("{} + {}", s.left, s.right);
                s.left = format!("{stem_no_m}{rm}{}", s.right);
                s.steps.push(DerivationStep {
                    sutra: 219,
                    rule_id: "nannool_219_magara_nasal_assimilation".to_owned(),
                    stage: 3,
                    transform: AlterationKind::Thirithal,
                    before,
                    after: s.left.clone(),
                });
                return vec![Stage1Output::done(s)];
            }
            s.left = format!("{}{}", s.left, s.right);
            if let Some(last_step) = s.steps.last_mut() {
                last_step.after = s.left.clone();
            }
            return vec![Stage1Output::done(s)];
        }
    }

    // General Panpuppeyar fallback after `-மை` elision -> feed Stage 3.
    vec![Stage1Output::pending(s)]
}

/// Stage 1B: Priority-ordered closed-class stem reductions.
fn apply_stage_1b_closed_class(
    state: BoundaryState,
    context: &PunarchiContext,
) -> Vec<Stage1Output> {
    // 1. Numerals (`199 > 194 > 198 > 196 > 197 > 195 > 188-193`) — skip if `right` is an overt case suffix (Stage 2 `249` handles those!).
    if !tables::is_overt_case_suffix(&state.right) {
        if let Some(num_out) = try_numerals_188_to_199(&state, context) {
            return num_out;
        }
    }

    // 2. Cardinal Directions (`186`) & `தெங்கு + காய்` (`187`).
    if !tables::is_overt_case_suffix(&state.right) {
        if let Some(dir_out) = try_directions_186_187(&state) {
            return dir_out;
        }
    }

    // 3. Pronouns (`247` & `238` Vetrumai content-word delegation).
    if let Some(pro_out) = try_pronouns_247(&state, context) {
        return pro_out;
    }

    // 4. Named special stems (`168, 169, 170, 174, 177, 203, 222, 233`).
    if let Some(named_out) = try_named_stems_stage_1b(&state, context) {
        return named_out;
    }

    vec![Stage1Output::pending(state)]
}

fn try_numerals_188_to_199(
    state: &BoundaryState,
    context: &PunarchiContext,
) -> Option<Vec<Stage1Output>> {
    let l = state.left.as_str();
    let r = state.right.as_str();

    // Priority 1: Sutra 199 — Distributive reduplication (`N + N`, `N != ஒன்பது`).
    let mut distributive_199_alt: Option<Stage1Output> = None;
    if l == r {
        let surface = match l {
            "ஒன்று" => Some("ஒவ்வொன்று"),
            "இரண்டு" => Some("இவ்விரண்டு"),
            "மூன்று" => Some("மும்மூன்று"),
            "நான்கு" => Some("நந்நான்கு"),
            "ஐந்து" => Some("ஐவைந்து"),
            "ஆறு" => Some("அவ்வாறு"),
            "ஏழு" => Some("எவ்வேழு"),
            "எட்டு" => Some("எவ்வெட்டு"),
            "பத்து" => Some("பப்பத்து"),
            _ => None,
        };
        if let Some(surf) = surface {
            let mut s = state.clone();
            let before = format!("{l} + {r}");
            s.left = surf.to_owned();
            s.steps.push(DerivationStep {
                sutra: 199,
                rule_id: "nannool_199_distributive_numeral".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before,
                after: surf.to_owned(),
            });
            if context.subtype == Some(ContextSubtype::Distributive) {
                return Some(vec![Stage1Output::done(s)]);
            }
            if context.subtype.is_none() && context.relation != GrammaticalRelation::Vetrumai {
                s.required_context = Some("distributive".to_owned());
                s.optional_variant = true;
                s.priority_rank = 45;
                distributive_199_alt = Some(Stage1Output::done(s));
            }
        }
    }

    let mut out = try_numerals_inner(state, context)?;
    if let Some(d199) = distributive_199_alt {
        out.push(d199);
    }
    Some(out)
}

fn try_numerals_inner(
    state: &BoundaryState,
    context: &PunarchiContext,
) -> Option<Vec<Stage1Output>> {
    let l = state.left.as_str();
    let r = state.right.as_str();

    // Priority 2: Sutra 194 — `ஒன்பது/ஒன்பஃது + பத்து -> தொண்ணூறு`, `+ நூறு -> தொள்ளாயிரம்`.
    if matches!(l, "ஒன்பது" | "ஒன்பஃது") && matches!(r, "பத்து" | "நூறு")
    {
        let surf = if r == "பத்து" {
            "தொண்ணூறு"
        } else {
            "தொள்ளாயிரம்"
        };
        let mut s = state.clone();
        s.left = surf.to_owned();
        s.steps.push(DerivationStep {
            sutra: 194,
            rule_id: "nannool_194_onpathu_ten_hundred".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: surf.to_owned(),
        });
        return Some(vec![Stage1Output::done(s)]);
    }

    // Priority 3: Sutra 198 — `பத்து + இரண்டு -> பன்னிரண்டு` (Ummaithogai/Unspecified) vs `பதிற்றிரண்டு` (Panputhogai, 197).
    if l == "பத்து" && r == "இரண்டு" {
        let mut s198 = state.clone();
        s198.left = "பன்".to_owned();
        s198.steps.push(DerivationStep {
            sutra: 198,
            rule_id: "nannool_198_paththu_irandu".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "பத்து + இரண்டு".to_owned(),
            after: "பன் + இரண்டு".to_owned(),
        });
        s198.priority_rank = 15;

        let mut s197 = state.clone();
        s197.left = "பதிற்று".to_owned();
        s197.steps.push(DerivationStep {
            sutra: 197,
            rule_id: "nannool_197_paththu_onpathu_in_irru".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "பத்து + இரண்டு".to_owned(),
            after: "பதிற்று + இரண்டு".to_owned(),
        });
        s197.priority_rank = 35;

        return match context.subtype {
            Some(ContextSubtype::Panputhogai) => Some(vec![Stage1Output::pending(s197)]),
            Some(ContextSubtype::Ummaithogai) => Some(vec![Stage1Output::pending(s198)]),
            _ => {
                s197.required_context = Some("panputhogai".to_owned());
                Some(vec![
                    Stage1Output::pending(s198),
                    Stage1Output::pending(s197),
                ])
            }
        };
    }

    // Priority 4: Sutra 196 — `ஒருபது/ஒருபஃது..எண்பது/எண்பஃது` + `1..9` (or unit-headed phrase).
    if tables::in_closed_class("decade_numerals", l) {
        let starts_with_1_to_9 = [
            "ஒன்று",
            "இரண்டு",
            "மூன்று",
            "நான்கு",
            "ஐந்து",
            "ஆறு",
            "ஏழு",
            "எட்டு",
            "ஒன்பது",
            "ஒரு",
            "இரு",
            "எண்",
            "ஒன்பதி",
        ]
        .iter()
        .any(|p| r.starts_with(p));
        if starts_with_1_to_9 {
            let stem = l
                .strip_suffix("பஃது")
                .or_else(|| l.strip_suffix("பது"))
                .unwrap_or(l);
            let new_left = format!("{stem}பத்து");
            let mut s = state.clone();
            s.steps.push(DerivationStep {
                sutra: 196,
                rule_id: "nannool_196_decade_plus_unit".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("{new_left} + {r}"),
            });
            s.left = new_left;
            return Some(vec![Stage1Output::pending(s)]);
        }
    }

    // Priority 5: Sutra 197 — `பத்து` / `ஒன்பது` + `{1..10, ஆயிரம், கோடி, கழஞ்சு, கலம், கலன், தூணி, குறுணி, மடங்கு}`.
    if matches!(l, "பத்து" | "ஒன்பது") {
        let is_197_target = matches!(
            r,
            "ஒன்று"
                | "இரண்டு"
                | "மூன்று"
                | "நான்கு"
                | "ஐந்து"
                | "ஆறு"
                | "ஏழு"
                | "எட்டு"
                | "ஒன்பது"
                | "பத்து"
                | "ஆயிரம்"
                | "கோடி"
                | "கழஞ்சு"
                | "கலம்"
                | "கலன்"
                | "தூணி"
                | "குறுணி"
                | "மடங்கு"
        );
        if is_197_target {
            let (in_stem, irru_stem) = if l == "பத்து" {
                ("பதின்", "பதிற்று")
            } else {
                ("ஒன்பதின்", "ஒன்பதிற்று")
            };
            let make_197 = |stem: &str, opt: bool, rank: u32| {
                let mut s = state.clone();
                s.steps.push(DerivationStep {
                    sutra: 197,
                    rule_id: "nannool_197_paththu_onpathu_in_irru".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before: format!("{l} + {r}"),
                    after: format!("{stem} + {r}"),
                });
                s.left = stem.to_owned();
                if stem == in_stem {
                    s.flags.block_209_stop = true;
                }
                s.optional_variant = opt;
                s.priority_rank = rank;
                Stage1Output::pending(s)
            };

            // Viruttiyurai fn. 191: `-இன்` does NOT attach to `பத்து` before `ஒன்பது` (or `இரண்டு`/`பத்து`),
            // so additive `பத்து + ஒன்பது` elides `உ` via Sutra 164 (`பத்தொன்பது`), with `பதிற்றொன்பது` for Panputhogai.
            if l == "பத்து" && r == "ஒன்பது" {
                let mut irru = make_197(irru_stem, false, 35);
                irru.state.flags.force_165 = true;
                return match context.subtype {
                    Some(ContextSubtype::Panputhogai) => Some(vec![irru]),
                    Some(ContextSubtype::Ummaithogai) => {
                        Some(vec![Stage1Output::pending(state.clone())])
                    }
                    _ => {
                        let mut add = state.clone();
                        add.priority_rank = 15;
                        irru.state.required_context = Some("panputhogai".to_owned());
                        Some(vec![Stage1Output::pending(add), irru])
                    }
                };
            }

            if r == "பத்து" || r == "தூணி" || r == "குறுணி" {
                let mut irru = make_197(irru_stem, false, 20);
                irru.state.flags.force_165 = true;
                return Some(vec![irru]);
            }
            // Viruttiyurai fn. 191: `-இன்` does NOT attach to `ஒன்பது` before 1..9 either (`ஒன்பதிற்றொன்று`, `ஒன்பதிற்றிரண்டு`).
            if l == "ஒன்பது"
                && matches!(
                    r,
                    "ஒன்று"
                        | "இரண்டு"
                        | "மூன்று"
                        | "நான்கு"
                        | "ஐந்து"
                        | "ஆறு"
                        | "ஏழு"
                        | "எட்டு"
                        | "ஒன்பது"
                )
            {
                let mut irru = make_197(irru_stem, false, 20);
                irru.state.flags.force_165 = true;
                return Some(vec![irru]);
            }
            if r == "கோடி" {
                let mut irru = make_197(irru_stem, false, 20);
                irru.state.flags.force_165 = true;
                let mut nat = state.clone();
                nat.optional_variant = true;
                nat.priority_rank = 45;
                return Some(vec![irru, Stage1Output::pending(nat)]);
            }
            if context.subtype == Some(ContextSubtype::Panputhogai) {
                let mut irru = make_197(irru_stem, false, 20);
                irru.state.flags.force_165 = true;
                return Some(vec![irru]);
            }
            // Default additive/measure (`பதினொன்று`, `பதின்மூன்று`, `பதினாயிரம்`, `ஒன்பதினாயிரம்`) uses `-இன்`.
            if matches!(
                r,
                "ஒன்று"
                    | "மூன்று"
                    | "நான்கு"
                    | "ஐந்து"
                    | "ஆறு"
                    | "ஏழு"
                    | "எட்டு"
            ) && l == "பத்து"
            {
                let mut irru = make_197(irru_stem, true, 40);
                irru.state.flags.force_165 = true;
                return Some(vec![make_197(in_stem, false, 20), irru]);
            }
            return Some(vec![make_197(in_stem, false, 20)]);
        }
    }

    // Priority 6: Sutra 195 — `1..8 + பத்து` -> `ஒருபது / ஒருபஃது .. எண்பது / எண்பஃது`.
    if r == "பத்து" {
        let prefix = match l {
            "ஒன்று" => Some("ஒரு"),
            "இரண்டு" => Some("இரு"),
            "மூன்று" => Some("முப்"),
            "நான்கு" => Some("நாற்"),
            "ஐந்து" => Some("ஐம்"),
            "ஆறு" => Some("அறு"),
            "ஏழு" => Some("எழு"),
            "எட்டு" => Some("எண்"),
            _ => None,
        };
        if let Some(p) = prefix {
            let mut s1 = state.clone();
            let surf1 = format!("{p}பது");
            s1.left = surf1.clone();
            s1.steps.push(DerivationStep {
                sutra: 195,
                rule_id: "nannool_195_decade_paththu".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: surf1,
            });
            s1.priority_rank = 20;

            let mut s2 = state.clone();
            let surf2 = format!("{p}பஃது");
            s2.left = surf2.clone();
            s2.steps.push(DerivationStep {
                sutra: 195,
                rule_id: "nannool_195_decade_paththu".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: surf2,
            });
            s2.optional_variant = true;
            s2.priority_rank = 35;

            return Some(vec![Stage1Output::done(s1), Stage1Output::done(s2)]);
        }
    }

    // Priority 7: Sutras 188-193 — Base numerals `1..8` before other words (when `NumberWord` or `Panputhogai` or standard numeral-measure/number compounds).
    let is_num_1_to_8 = matches!(
        l,
        "ஒன்று"
            | "இரண்டு"
            | "மூன்று"
            | "நான்கு"
            | "ஐந்து"
            | "ஆறு"
            | "ஏழு"
            | "எட்டு"
    );
    if !is_num_1_to_8 {
        return None;
    }

    let r_first = Letters::new(r).next().unwrap_or("");
    let r_vowel = is_independent_uyir(r_first);
    let r_mei = unit_mei(r_first);

    match l {
        "ஒன்று" | "இரண்டு" => {
            let (c_stem, v_long, v_short) = if l == "ஒன்று" {
                ("ஒரு", "ஓர்", "ஒர்")
            } else {
                ("இரு", "ஈர்", "இர்")
            };
            if r_vowel {
                let mut s = state.clone();
                s.steps.push(DerivationStep {
                    sutra: 189,
                    rule_id: "nannool_189_one_two".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before: format!("{l} + {r}"),
                    after: format!("{v_long} + {r}"),
                });
                s.left = v_long.to_owned();
                if r == "ஆயிரம்" {
                    let mut alt = state.clone();
                    alt.steps.push(DerivationStep {
                        sutra: 189,
                        rule_id: "nannool_189_one_two".to_owned(),
                        stage: 1,
                        transform: AlterationKind::Thirithal,
                        before: format!("{l} + {r}"),
                        after: format!("{v_short} + {r}"),
                    });
                    alt.left = v_short.to_owned();
                    alt.optional_variant = true;
                    alt.priority_rank = 40;
                    return Some(vec![Stage1Output::pending(s), Stage1Output::pending(alt)]);
                }
                return Some(vec![Stage1Output::pending(s)]);
            }
            let mut s = state.clone();
            s.steps.push(DerivationStep {
                sutra: 189,
                rule_id: "nannool_189_one_two".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("{c_stem} + {r}"),
            });
            s.left = c_stem.to_owned();
            // Sutra 179 blocks 165 doubling on `ஒரு/இரு/அறு/எழு`.
            s.flags.block_165 = true;
            return Some(vec![Stage1Output::pending(s)]);
        }
        "மூன்று" => {
            if r_vowel {
                let mut s = state.clone();
                s.steps.push(DerivationStep {
                    sutra: 190,
                    rule_id: "nannool_190_three".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Keduthal,
                    before: format!("{l} + {r}"),
                    after: format!("மூ + {r}"),
                });
                s.left = "மூ".to_owned();
                return Some(vec![Stage1Output::pending(s)]);
            }
            if let Some(rm) = r_mei.as_deref() {
                let gem = if rm == "ய்" { "வ்" } else { rm };
                let mut s = state.clone();
                let surf = format!("மு{gem}{r}");
                s.left = surf.clone();
                s.steps.push(DerivationStep {
                    sutra: 190,
                    rule_id: "nannool_190_three".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before: format!("{l} + {r}"),
                    after: surf,
                });
                return Some(vec![Stage1Output::done(s)]);
            }
        }
        "நான்கு" => {
            let new_stem = if r_vowel
                || r_mei
                    .as_deref()
                    .is_some_and(|m| matches!(m, "ய்" | "ர்" | "ல்" | "வ்" | "ழ்" | "ள்"))
            {
                "நால்"
            } else if is_vallinam_initial_unit(r_first) {
                "நாற்"
            } else {
                "நான்"
            };
            let mut s = state.clone();
            s.steps.push(DerivationStep {
                sutra: 191,
                rule_id: "nannool_191_four".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("{new_stem} + {r}"),
            });
            s.left = new_stem.to_owned();
            if new_stem == "நாற்" {
                s.left = format!("{new_stem}{r}");
                if let Some(last) = s.steps.last_mut() {
                    last.after = s.left.clone();
                }
                return Some(vec![Stage1Output::done(s)]);
            }
            return Some(vec![Stage1Output::pending(s)]);
        }
        "ஐந்து" => {
            if r_vowel {
                let mut s = state.clone();
                s.steps.push(DerivationStep {
                    sutra: 192,
                    rule_id: "nannool_192_five".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Keduthal,
                    before: format!("{l} + {r}"),
                    after: format!("ஐ + {r}"),
                });
                s.left = "ஐ".to_owned();
                return Some(vec![Stage1Output::pending(s)]);
            }
            if let Some(rm) = r_mei.as_deref() {
                let coda = if let Some(n) = homorganic_nasal(rm) {
                    n
                } else if matches!(rm, "ஞ்" | "ந்" | "ம்" | "வ்") {
                    rm
                } else {
                    "ந்"
                };
                let mut s = state.clone();
                let surf = format!("ஐ{coda}{r}");
                s.left = surf.clone();
                s.steps.push(DerivationStep {
                    sutra: 192,
                    rule_id: "nannool_192_five".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before: format!("{l} + {r}"),
                    after: surf,
                });
                return Some(vec![Stage1Output::done(s)]);
            }
        }
        "ஆறு" if !r_vowel => {
            let is_noun_sense = matches!(
                context.lexical_class,
                Some(
                    LexicalClass::NonRationalNoun
                        | LexicalClass::RationalNoun
                        | LexicalClass::CommonNoun
                )
            ) || (context.effective_relation()
                == GrammaticalRelation::Vetrumai
                && context.lexical_class != Some(LexicalClass::NumberWord));
            if is_noun_sense {
                return None;
            }
            let is_clear_number = context.lexical_class == Some(LexicalClass::NumberWord)
                || context.subtype == Some(ContextSubtype::Panputhogai)
                || matches!(
                    r,
                    "பத்து"
                        | "நூறு"
                        | "ஆயிரம்"
                        | "கோடி"
                        | "கழஞ்சு"
                        | "கலம்"
                        | "நாழி"
                        | "வட்டி"
                        | "வகை"
                        | "குணம்"
                        | "சுவை"
                );
            let mut s_num = state.clone();
            s_num.steps.push(DerivationStep {
                sutra: 188,
                rule_id: "nannool_188_numeral_base".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("அறு + {r}"),
            });
            s_num.left = "அறு".to_owned();
            s_num.flags.block_165 = true;
            if is_clear_number {
                return Some(vec![Stage1Output::pending(s_num)]);
            }
            // Ambiguous (`ஆறு + நீர்` "river" vs "6"): let Stage 1C run for river noun AND emit labeled `number_word` alternative.
            s_num.required_context = Some("number_word".to_owned());
            s_num.priority_rank = 60;
            return Some(vec![
                Stage1Output::pending(state.clone()),
                Stage1Output::pending(s_num),
            ]);
        }
        "ஏழு"
            if context.subtype != Some(ContextSubtype::Imperative)
                && context.lexical_class != Some(LexicalClass::VerbalNounRoot) =>
        {
            let mut s = state.clone();
            let stem = if r_vowel || r == "கடல்" {
                "ஏழ்"
            } else {
                "எழு"
            };
            s.steps.push(DerivationStep {
                sutra: 188,
                rule_id: "nannool_188_numeral_base".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("{stem} + {r}"),
            });
            s.left = stem.to_owned();
            if !r_vowel {
                s.flags.block_165 = true;
            }
            return Some(vec![Stage1Output::pending(s)]);
        }
        "எட்டு" => {
            let mut s = state.clone();
            s.steps.push(DerivationStep {
                sutra: 193,
                rule_id: "nannool_193_eight".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("எண் + {r}"),
            });
            s.left = "எண்".to_owned();
            s.flags.block_209_stop = true;
            return Some(vec![Stage1Output::pending(s)]);
        }
        _ => {}
    }

    None
}

fn try_directions_186_187(state: &BoundaryState) -> Option<Vec<Stage1Output>> {
    let l = state.left.as_str();
    let r = state.right.as_str();

    // Sutra 187: `தெங்கு + காய் -> தேங்காய்` (+ optional `தெங்கங்காய்`).
    if l == "தெங்கு" && r == "காய்" {
        let mut s1 = state.clone();
        s1.left = "தேங்காய்".to_owned();
        s1.steps.push(DerivationStep {
            sutra: 187,
            rule_id: "nannool_187_thengu_kaai".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "தெங்கு + காய்".to_owned(),
            after: "தேங்காய்".to_owned(),
        });
        s1.priority_rank = 15;

        let mut s2 = state.clone();
        s2.left = "தெங்கங்காய்".to_owned();
        s2.steps.push(DerivationStep {
            sutra: 187,
            rule_id: "nannool_187_thengu_kaai".to_owned(),
            stage: 1,
            transform: AlterationKind::Thonral,
            before: "தெங்கு + காய்".to_owned(),
            after: "தெங்கங்காய்".to_owned(),
        });
        s2.optional_variant = true;
        s2.priority_rank = 40;

        return Some(vec![Stage1Output::done(s1), Stage1Output::done(s2)]);
    }

    // Sutra 186: Cardinal direction stems.
    if !tables::in_closed_class("direction_stems", l) {
        return None;
    }

    let r_first = Letters::new(r).next().unwrap_or("");
    // Before vowels (`வடக்கு + ஊர் -> வடக்கூர்`, `தெற்கு + ஊர் -> தெற்கூர்`), Sutra 186 `பிற` retains full Kurriyalugaram.
    if is_independent_uyir(r_first) {
        return None;
    }

    let r_mei = unit_mei(r_first);
    let mut s = state.clone();
    match l {
        "வடக்கு" | "குடக்கு" | "குணக்கு" => {
            let short = l.strip_suffix("க்கு").unwrap_or(l);
            s.steps.push(DerivationStep {
                sutra: 186,
                rule_id: "nannool_186_direction_stem".to_owned(),
                stage: 1,
                transform: AlterationKind::Keduthal,
                before: format!("{l} + {r}"),
                after: format!("{short} + {r}"),
            });
            s.left = short.to_owned();
            s.flags.block_165 = true;
            return Some(vec![Stage1Output::pending(s)]);
        }
        "தெற்கு" => {
            s.steps.push(DerivationStep {
                sutra: 186,
                rule_id: "nannool_186_direction_stem".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("தென் + {r}"),
            });
            s.left = "தென்".to_owned();
            s.flags.block_209_stop = true;
            // `தென்கிழக்கு`, `தென்மேற்கு`, `தென்குமரி` keep `ன்` natural (`block` Vetrumai stop conversion via done if non-த/ந).
            if r_mei
                .as_deref()
                .is_some_and(|m| matches!(m, "க்" | "ச்" | "ப்" | "ம்" | "வ்"))
            {
                s.left = format!("தென்{r}");
                if let Some(last) = s.steps.last_mut() {
                    last.after = s.left.clone();
                }
                return Some(vec![Stage1Output::done(s)]);
            }
            return Some(vec![Stage1Output::pending(s)]);
        }
        "மேற்கு" => {
            // Before `த`-initial (`மேற்கு + திசை -> மேற்றிசை`): retain `ற்` and block 229 deletion!
            if r_mei.as_deref() == Some("த்") {
                s.steps.push(DerivationStep {
                    sutra: 186,
                    rule_id: "nannool_186_direction_stem".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Keduthal,
                    before: format!("{l} + {r}"),
                    after: format!("மேல் + {r}"),
                });
                // Feed `மேல்` with `block_229 = true` so 237 (`திசை->றிசை`) + 227 (`ல்->ற்`) yields `மேற்றிசை`!
                s.left = "மேல்".to_owned();
                s.flags.block_229 = true;
                return Some(vec![Stage1Output::pending(s)]);
            }
            s.steps.push(DerivationStep {
                sutra: 186,
                rule_id: "nannool_186_direction_stem".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("மேல் + {r}"),
            });
            s.left = "மேல்".to_owned();
            if r_mei
                .as_deref()
                .is_some_and(|m| matches!(m, "க்" | "ச்" | "ப்"))
            {
                s.left = format!("மேல்{r}");
                if let Some(last) = s.steps.last_mut() {
                    last.after = s.left.clone();
                }
                return Some(vec![Stage1Output::done(s)]);
            }
            return Some(vec![Stage1Output::pending(s)]);
        }
        "கிழக்கு" => {
            s.steps.push(DerivationStep {
                sutra: 186,
                rule_id: "nannool_186_direction_stem".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("கீழ் + {r}"),
            });
            s.left = "கீழ்".to_owned();
            s.flags.is_direction_keezh = true;
            return Some(vec![Stage1Output::pending(s)]);
        }
        _ => {}
    }
    None
}

fn try_pronouns_247(state: &BoundaryState, context: &PunarchiContext) -> Option<Vec<Stage1Output>> {
    let l = state.left.as_str();
    let r = state.right.as_str();

    let is_case = tables::is_overt_case_suffix(r);
    let is_vetrumai = context.effective_relation() == GrammaticalRelation::Vetrumai;
    if !is_case && !is_vetrumai {
        return None;
    }

    let forms = tables::oblique_forms("pronoun_oblique_stems", l)?;
    let rule_id = if l == "நான்" {
        "nannool_247_pronoun_naan_extended"
    } else {
        "nannool_247_pronoun_oblique"
    };
    let sutra = if !is_case && is_vetrumai { 238 } else { 247 };
    let actual_rule_id = if !is_case && is_vetrumai && l != "நான்" {
        "nannool_238_vetrumai_porul_delegation"
    } else {
        rule_id
    };

    // Sutra 247.5 (`நான்கா றிரட்டல`): suppress 205 gemination before 4th case `கு` and 6th case `அது/ஆது/அ`.
    let suppress_205 = matches!(r, "கு" | "அது" | "ஆது" | "அ");
    let r_first = Letters::new(r).next().unwrap_or("");
    let block_209_stop = !is_case && is_vetrumai && !is_independent_uyir(r_first);

    let mut out = Vec::new();
    for (idx, &obl) in forms.iter().enumerate() {
        let mut s = state.clone();
        s.steps.push(DerivationStep {
            sutra,
            rule_id: actual_rule_id.to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: format!("{obl} + {r}"),
        });
        s.left = obl.to_owned();
        s.flags.is_derived_final = true;
        s.flags.suppress_205 = suppress_205;
        s.flags.block_209_stop = block_209_stop;
        if idx > 0 {
            s.optional_variant = true;
            s.priority_rank = 45;
        } else {
            s.priority_rank = 20;
        }
        out.push(Stage1Output::pending(s));
    }
    Some(out)
}

fn try_named_stems_stage_1b(
    state: &BoundaryState,
    context: &PunarchiContext,
) -> Option<Vec<Stage1Output>> {
    let l = state.left.as_str();
    let r = state.right.as_str();
    let rel = context.effective_relation();

    // Sutra 168: `வாழிய` -> optional `வாழி` (`block_165 = true`).
    if l == "வாழிய" {
        let mut s_full = state.clone();
        s_full.flags.block_165 = true;
        let mut s_short = state.clone();
        s_short.steps.push(DerivationStep {
            sutra: 168,
            rule_id: "nannool_168_vaazhiya".to_owned(),
            stage: 1,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + {r}"),
            after: format!("வாழி + {r}"),
        });
        s_short.left = "வாழி".to_owned();
        s_short.flags.is_derived_final = true;
        s_short.flags.block_165 = true;
        s_short.optional_variant = true;
        s_short.priority_rank = 45;
        return Some(vec![
            Stage1Output::pending(s_full),
            Stage1Output::pending(s_short),
        ]);
    }

    // Sutra 169: `சாவ` -> optional `சா` (feeds 165 doubling: `சாக்குத்தினான்` alongside `சாவக்குத்தினான்`).
    if l == "சாவ" {
        let mut s_short = state.clone();
        s_short.steps.push(DerivationStep {
            sutra: 169,
            rule_id: "nannool_169_saava".to_owned(),
            stage: 1,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + {r}"),
            after: format!("சா + {r}"),
        });
        s_short.left = "சா".to_owned();
        s_short.flags.is_derived_final = true;
        s_short.optional_variant = true;
        s_short.priority_rank = 45;
        return Some(vec![
            Stage1Output::pending(state.clone()),
            Stage1Output::pending(s_short),
        ]);
    }

    // Sutra 170: `பல` / `சில` (self-compounds bypass Stage 3; before other words optional `பல்`/`சில்` when non-case).
    if matches!(l, "பல" | "சில") && !tables::is_overt_case_suffix(r) {
        if l == r {
            let variants: [(&str, AlterationKind, bool, u32); 4] = if l == "பல" {
                [
                    ("பலபல", AlterationKind::Iyalbu, false, 20),
                    ("பலப்பல", AlterationKind::Thonral, true, 30),
                    ("பற்பல", AlterationKind::Thirithal, true, 35),
                    ("பல்பல", AlterationKind::Keduthal, true, 40),
                ]
            } else {
                [
                    ("சிலசில", AlterationKind::Iyalbu, false, 20),
                    ("சிலச்சில", AlterationKind::Thonral, true, 30),
                    ("சிற்சில", AlterationKind::Thirithal, true, 35),
                    ("சில்சில", AlterationKind::Keduthal, true, 40),
                ]
            };
            let mut out = Vec::new();
            for (surf, tr, opt, rank) in variants {
                let mut s = state.clone();
                s.left = surf.to_owned();
                s.steps.push(DerivationStep {
                    sutra: 170,
                    rule_id: "nannool_170_pala_sila".to_owned(),
                    stage: 1,
                    transform: tr,
                    before: format!("{l} + {r}"),
                    after: surf.to_owned(),
                });
                s.optional_variant = opt;
                s.priority_rank = rank;
                out.push(Stage1Output::done(s));
            }
            return Some(out);
        }

        // Before other words: `பல/சில` stays (`block_165 = true` per 167) + optional `பல்/சில்` fed into Stage 3.
        let mut s_nat = state.clone();
        s_nat.flags.block_165 = true;
        s_nat.priority_rank = 30;

        let short = if l == "பல" {
            "பல்"
        } else {
            "சில்"
        };
        let mut s_elide = state.clone();
        s_elide.steps.push(DerivationStep {
            sutra: 170,
            rule_id: "nannool_170_pala_sila".to_owned(),
            stage: 1,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + {r}"),
            after: format!("{short} + {r}"),
        });
        s_elide.left = short.to_owned();
        s_elide.optional_variant = true;
        s_elide.priority_rank = 45;

        return Some(vec![
            Stage1Output::pending(s_nat),
            Stage1Output::pending(s_elide),
        ]);
    }

    // Sutra 172: Short-syllable `ஆ`-final nouns (`நிலா, சுறா, கனா, இரா, புறா, விழா`):
    // prose optional `+ வு` (`நிலவு`), verse-only short `அ` (`நில`, gated on `context.poetic`).
    if !tables::is_overt_case_suffix(r) && matches!(l, "நிலா" | "சுறா" | "கனா" | "இரா" | "புறா" | "விழா")
    {
        let short = match l {
            "நிலா" => "நில",
            "சுறா" => "சுற",
            "கனா" => "கன",
            "இரா" => "இர",
            "புறா" => "புற",
            _ => "விழ",
        };
        let mut s_nat = state.clone();
        s_nat.priority_rank = 20;

        let mut s_vu = state.clone();
        let vu_stem = format!("{short}வு");
        s_vu.steps.push(DerivationStep {
            sutra: 172,
            rule_id: "nannool_172_short_aa_prose_vu".to_owned(),
            stage: 1,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("{vu_stem} + {r}"),
        });
        s_vu.left = vu_stem;
        s_vu.optional_variant = true;
        s_vu.priority_rank = 35;

        let mut out = vec![Stage1Output::pending(s_nat), Stage1Output::pending(s_vu)];
        if context.poetic {
            let mut s_poet = state.clone();
            s_poet.steps.push(DerivationStep {
                sutra: 172,
                rule_id: "nannool_172_poetic_short_aa".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: format!("{l} + {r}"),
                after: format!("{short} + {r}"),
            });
            s_poet.left = short.to_owned();
            s_poet.optional_variant = true;
            s_poet.poetic = true;
            s_poet.priority_rank = 55;
            out.push(Stage1Output::pending(s_poet));
        }
        return Some(out);
    }

    // Sutra 173 (poetic-only): `அன்றி`/`இன்றி` optionally mutate to `அன்று`/`இன்று` (`block_165 = true`).
    if context.poetic && matches!(l, "அன்றி" | "இன்றி") && !tables::is_overt_case_suffix(r)
    {
        let mut s_nat = state.clone();
        s_nat.priority_rank = 20;
        let short = if l == "அன்றி" {
            "அன்று"
        } else {
            "இன்று"
        };
        let mut s_poet = state.clone();
        s_poet.steps.push(DerivationStep {
            sutra: 173,
            rule_id: "nannool_173_poetic_anri_inri".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: format!("{short} + {r}"),
        });
        s_poet.left = short.to_owned();
        s_poet.flags.block_165 = true;
        s_poet.optional_variant = true;
        s_poet.poetic = true;
        s_poet.priority_rank = 55;
        return Some(vec![
            Stage1Output::pending(s_nat),
            Stage1Output::pending(s_poet),
        ]);
    }

    // Sutra 180 (poetic-only): `அது + அன்று -> அதான்று` alongside prose `அதுவன்று`/`அதன்று`.
    if context.poetic && l == "அது" && r == "அன்று" {
        let mut s_nat = state.clone();
        s_nat.priority_rank = 20;
        let mut s_poet = state.clone();
        s_poet.left = "அதான்று".to_owned();
        s_poet.steps.push(DerivationStep {
            sutra: 180,
            rule_id: "nannool_180_poetic_athu_anru".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "அது + அன்று".to_owned(),
            after: "அதான்று".to_owned(),
        });
        s_poet.optional_variant = true;
        s_poet.poetic = true;
        s_poet.priority_rank = 55;
        return Some(vec![
            Stage1Output::pending(s_nat),
            Stage1Output::done(s_poet),
        ]);
    }

    // Sutra 174: `நாழி + உரி -> நாடுரி` (blocking `*நாழியுரி`), `உரி + eligible -> உரிய` (`block_165 = true`).
    if l == "நாழி" && r == "உரி" {
        let mut s = state.clone();
        s.left = "நாடுரி".to_owned();
        s.steps.push(DerivationStep {
            sutra: 174,
            rule_id: "nannool_174_naazhi_uri".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "நாழி + உரி".to_owned(),
            after: "நாடுரி".to_owned(),
        });
        return Some(vec![Stage1Output::done(s)]);
    }
    if l == "உரி" && tables::in_closed_class("uri_eligible_commodities", r) {
        let mut s = state.clone();
        s.steps.push(DerivationStep {
            sutra: 174,
            rule_id: "nannool_174_naazhi_uri".to_owned(),
            stage: 1,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("உரிய + {r}"),
        });
        s.left = "உரிய".to_owned();
        s.flags.is_derived_final = true;
        s.flags.block_165 = true;
        return Some(vec![Stage1Output::pending(s)]);
    }

    // Sutra 177: `ஆ + பீ -> ஆப்பி` shortening; derived `ஆப்பி` stays natural in Alvazhi before Vallinam and doubles in Vetrumai (165).
    if l == "ஆ" && r == "பீ" {
        let mut s = state.clone();
        s.left = "ஆப்பி".to_owned();
        s.steps.push(DerivationStep {
            sutra: 177,
            rule_id: "nannool_177_aa_pee".to_owned(),
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: "ஆ + பீ".to_owned(),
            after: "ஆப்பி".to_owned(),
        });
        return Some(vec![Stage1Output::done(s)]);
    }
    if l == "ஆப்பி" {
        let mut s = state.clone();
        let r_first = Letters::new(r).next().unwrap_or("");
        if rel == GrammaticalRelation::Alvazhi && is_vallinam_initial_unit(r_first) {
            s.flags.block_165 = true;
            s.steps.push(DerivationStep {
                sutra: 177,
                rule_id: "nannool_177_aa_pee".to_owned(),
                stage: 1,
                transform: AlterationKind::Iyalbu,
                before: format!("{l} + {r}"),
                after: format!("{l}{r}"),
            });
        }
        return Some(vec![Stage1Output::pending(s)]);
    }

    // Sutra 203: `பனை` in Vetrumai.
    if l == "பனை" && rel == GrammaticalRelation::Vetrumai {
        if r == "அட்டு" {
            let mut s = state.clone();
            s.left = "பனாட்டு".to_owned();
            s.steps.push(DerivationStep {
                sutra: 203,
                rule_id: "nannool_203_panai_vetrumai".to_owned(),
                stage: 1,
                transform: AlterationKind::Thirithal,
                before: "பனை + அட்டு".to_owned(),
                after: "பனாட்டு".to_owned(),
            });
            return Some(vec![Stage1Output::done(s)]);
        }
        if r == "கொடி" {
            return None; // Feeds Sutra 165 -> `பனைக்கொடி`.
        }
        let r_first = Letters::new(r).next().unwrap_or("");
        if let Some(rm) = unit_mei(r_first) {
            if is_vallinam_initial_unit(r_first) {
                if let Some(nasal) = homorganic_nasal(&rm) {
                    let mut s_am = state.clone();
                    let surf = format!("பன{nasal}{r}");
                    s_am.left = surf.clone();
                    s_am.steps.push(DerivationStep {
                        sutra: 203,
                        rule_id: "nannool_203_panai_vetrumai".to_owned(),
                        stage: 1,
                        transform: AlterationKind::Thirithal,
                        before: format!("{l} + {r}"),
                        after: surf,
                    });
                    s_am.priority_rank = 20;
                    if r == "திரள்" {
                        let mut s_std = state.clone();
                        s_std.optional_variant = true;
                        s_std.priority_rank = 40;
                        return Some(vec![
                            Stage1Output::pending(state.clone()),
                            Stage1Output::done({
                                s_am.optional_variant = true;
                                s_am.priority_rank = 40;
                                s_am
                            }),
                        ]);
                    }
                    return Some(vec![Stage1Output::done(s_am)]);
                }
            }
        }
    }

    // Sutra 222: `அகம் + செவி/கை` (`அஞ்செவி / அகஞ்செவி`, `அங்கை / அகங்கை`); `அகம் + சிறை` (`அஞ்சிறை` poetic).
    if l == "அகம்" && matches!(r, "செவி" | "கை" | "சிறை") {
        let (contracted, full, is_poetic_only) = match r {
            "செவி" => ("அஞ்செவி", "அகஞ்செவி", false),
            "கை" => ("அங்கை", "அகங்கை", false),
            _ => ("அஞ்சிறை", "அகஞ்சிறை", true),
        };
        let mut s_full = state.clone();
        s_full.left = full.to_owned();
        s_full.steps.push(DerivationStep {
            sutra: 219,
            rule_id: "nannool_219_magara_nasal_assimilation".to_owned(),
            stage: 3,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: full.to_owned(),
        });

        let mut s_short = state.clone();
        s_short.left = contracted.to_owned();
        s_short.steps.push(DerivationStep {
            sutra: 222,
            rule_id: if is_poetic_only {
                "nannool_222_poetic_agam_sirai".to_owned()
            } else {
                "nannool_222_agam_sevi_kai".to_owned()
            },
            stage: 1,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: contracted.to_owned(),
        });

        if is_poetic_only {
            s_full.priority_rank = 20;
            if context.poetic {
                s_short.poetic = true;
                s_short.optional_variant = true;
                s_short.priority_rank = 45;
                return Some(vec![
                    Stage1Output::done(s_full),
                    Stage1Output::done(s_short),
                ]);
            }
            return Some(vec![Stage1Output::done(s_full)]);
        }
        s_short.priority_rank = 20;
        s_full.optional_variant = true;
        s_full.priority_rank = 40;
        return Some(vec![
            Stage1Output::done(s_short),
            Stage1Output::done(s_full),
        ]);
    }

    // Sutra 233: `இல்` (NegationStem) in Panputhogai -> `இல்லைப்பொருள்`/`இல்லைபொருள்`, `இல்லாப்பொருள்`, `இல்பொருள்`.
    if l == "இல்" && context.lexical_class == Some(LexicalClass::NegationStem) {
        let r_first = Letters::new(r).next().unwrap_or("");
        if is_vallinam_initial_unit(r_first) {
            let rm = unit_mei(r_first).unwrap_or_default();
            let make_il = |surf: String, tr: AlterationKind, opt: bool, rank: u32| {
                let mut s = state.clone();
                s.left = surf.clone();
                s.steps.push(DerivationStep {
                    sutra: 233,
                    rule_id: "nannool_233_il_negation".to_owned(),
                    stage: 1,
                    transform: tr,
                    before: format!("{l} + {r}"),
                    after: surf,
                });
                s.optional_variant = opt;
                s.priority_rank = rank;
                Stage1Output::done(s)
            };
            return Some(vec![
                make_il(format!("இல்லை{rm}{r}"), AlterationKind::Thonral, false, 20),
                make_il(format!("இல்லை{r}"), AlterationKind::Thonral, true, 30),
                make_il(format!("இல்லா{rm}{r}"), AlterationKind::Thonral, true, 35),
                make_il(format!("இல்{r}"), AlterationKind::Iyalbu, true, 40),
            ]);
        }
    }

    None
}

/// Stage 1C: Pre-elision Kurriyalugaram mutations (`183`, `184`, `185`).
fn apply_stage_1c_all(state: BoundaryState, context: &PunarchiContext) -> Vec<BoundaryState> {
    let rel = context.effective_relation();

    // Sutra 184: Lexicon-gated Menthodar -> Vanthodar (`மருந்து->மருத்து`, `சுரும்பு->சுருப்பு`, etc.).
    let class_184 = match rel {
        GrammaticalRelation::Vetrumai => Some("menthodar_vanthodar_vetrumai"),
        GrammaticalRelation::Alvazhi => Some("menthodar_vanthodar_alvazhi"),
        GrammaticalRelation::Unspecified => None,
    };
    if let Some(cid) = class_184 {
        if let Some(forms) = tables::oblique_forms(cid, &state.left) {
            if let Some(&converted) = forms.first() {
                let mut s = state;
                let before = format!("{} + {}", s.left, s.right);
                let after = format!("{converted} + {}", s.right);
                s.steps.push(DerivationStep {
                    sutra: 184,
                    rule_id: "nannool_184_menthodar_to_vanthodar".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before,
                    after,
                });
                s.left = converted.to_owned();
                s.flags.is_derived_final = true;
                s.flags.force_165 = true;
                return vec![s];
            }
        }
    }

    // Sutra 185: `ஐ` increment on `பண்டு/இன்று/அன்று/நேற்று` when `right` is a noun (`காலம்/நாள்/கூலி/நலம்/பொழுது`).
    if matches!(
        (state.left.as_str(), state.right.as_str()),
        ("பண்டு", "காலம்")
            | ("இன்று", "நாள்")
            | ("இன்று", "நலம்")
            | ("அன்று", "கூலி")
            | ("நேற்று", "பொழுது")
            | ("நேற்று", "கூலி")
    ) {
        if let Some(forms) = tables::oblique_forms("kurriyalugaram_ai_stems", &state.left) {
            if let Some(&ai_stem) = forms.first() {
                let mut s = state;
                let before = format!("{} + {}", s.left, s.right);
                let after = format!("{ai_stem} + {}", s.right);
                s.steps.push(DerivationStep {
                    sutra: 185,
                    rule_id: "nannool_185_kurriyalugaram_ai".to_owned(),
                    stage: 1,
                    transform: AlterationKind::Thirithal,
                    before,
                    after,
                });
                s.left = ai_stem.to_owned();
                s.flags.is_derived_final = true;
                return vec![s];
            }
        }
    }

    // Sutra 183: Nedil/Uyir-thodar `டு/று -> ட்டு/ற்று`.
    uyireeru::apply_stage_1c(state, context)
}

/// Helper used by `split.rs` and tests to inspect a Stage 1 `BoundaryFlags`.
#[allow(dead_code)]
pub fn default_flags() -> BoundaryFlags {
    BoundaryFlags::default()
}
