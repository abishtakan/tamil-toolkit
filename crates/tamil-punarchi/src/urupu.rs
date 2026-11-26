//! Stage 2 (*Urupu Punariyal*, Sutras 240-257, 238, and stem-level Chariyai increments):
//! Multi-segment Chariyai staging, `உம்` post-positioning, `254` `இன்` filter, and `242.2` `கு`/`கண்` asymmetry.

use crate::context::{
    AlterationKind, ContextSubtype, DerivationStep, GrammaticalRelation, LexicalClass,
    PunarchiContext,
};
use crate::phonology::{classify_ugaram, is_independent_uyir, is_vallinam_initial_unit, unit_mei};
use crate::pipeline::{BoundaryFlags, BoundaryState, FoldSegment};
use crate::tables;
use tamil_core::Letters;

/// A staged multi-segment chain emitted by Stage 2 for left-to-right folding through Stages 3-4.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StagedChain {
    pub segments: Vec<FoldSegment>,
    pub steps: Vec<DerivationStep>,
    pub required_context: Option<String>,
    pub optional_variant: bool,
    pub poetic: bool,
    pub priority_rank: u32,
}

impl StagedChain {
    pub fn from_state(state: BoundaryState) -> Self {
        let mut left_flags = state.flags;
        let right_flags = BoundaryFlags::default();
        // Sutra 242.2: 4th-case `கு` forces Sutra 165 doubling even after Uyartinai/Poduppeyar.
        if state.right == "கு" {
            left_flags.force_165 = true;
        }
        Self {
            segments: vec![
                FoldSegment::with_flags(state.left, left_flags),
                FoldSegment::with_flags(state.right, right_flags),
            ],
            steps: state.steps,
            required_context: state.required_context,
            optional_variant: state.optional_variant,
            poetic: state.poetic,
            priority_rank: state.priority_rank,
        }
    }
}

/// Expand a Stage 1 `BoundaryState` into one or more Stage 2 multi-segment chains (`2 <= len <= 5`).
pub fn apply_stage_2(state: BoundaryState, context: &PunarchiContext) -> Vec<StagedChain> {
    let l = state.left.as_str();
    let r = state.right.as_str();
    let rel = context.effective_relation();
    let is_case = tables::is_overt_case_suffix(r) && rel != GrammaticalRelation::Alvazhi;
    let is_vetrumai = rel == GrammaticalRelation::Vetrumai || is_case;

    // 0A. Sutra 256: Case-3 agentive nouns before passive-action compounds (`பேய் + கோட்பட்டான்`, `பேய் + பிடிக்கப்பட்டான்`).
    if context.lexical_class == Some(LexicalClass::PassiveActionCompound)
        && (is_vetrumai || context.subtype == Some(ContextSubtype::Case3))
        && !is_case
    {
        if let Some(chains) = try_sutra_256_passive_agent(&state) {
            return chains;
        }
    }

    // 0B. Sutra 255: Case-2 (`ஐ`) elision compounds (`thogai`) cross-state Iyalbu/Vikaram patterns.
    if context.subtype == Some(ContextSubtype::Case2) && !is_case {
        if let Some(chains) = try_sutra_255_case2_thogai(&state) {
            return chains;
        }
    }

    // 1. Sutra 245 (`எல்லாம்`) + Sutra 238 delegation.
    if l == "எல்லாம்" && is_vetrumai {
        return stage_245_ellaam(state, context, is_case);
    }

    // 2. Sutra 246 (`எல்லாரும்`, `எல்லீரும்`) + Sutra 238 delegation.
    if matches!(l, "எல்லாரும்" | "எல்லீரும்") && is_vetrumai {
        return stage_246_ellaarum(state, is_case);
    }

    // 3. Sutra 247.4 (Oblique pronoun stem + `கு` -> `[stem, அ, கு]` with `suppress_205 = true`).
    if r == "கு"
        && matches!(
            l,
            "தன்" | "தம்"
                | "நம்"
                | "என்"
                | "எம்"
                | "நின்"
                | "நும்"
                | "உன்"
                | "உம்"
        )
    {
        let mut s = state;
        s.steps.push(DerivationStep {
            sutra: 247,
            rule_id: "nannool_247_pronoun_ku_a".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{} + கு", s.left),
            after: format!("{} + அ + கு", s.left),
        });
        let mut f0 = s.flags;
        f0.suppress_205 = true;
        let f1 = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        return vec![StagedChain {
            segments: vec![
                FoldSegment::with_flags(s.left, f0),
                FoldSegment::with_flags("அ", f1),
                FoldSegment::plain("கு"),
            ],
            steps: s.steps,
            required_context: s.required_context,
            optional_variant: s.optional_variant,
            poetic: s.poetic,
            priority_rank: s.priority_rank.min(20),
        }];
    }

    // 4. Sutra 248 (`ஆ, மா, கோ, ஆமா`) + case / Vetrumai (`238`).
    if tables::in_closed_class("aa_maa_ko_stems", l)
        && is_vetrumai
        && (is_case || matches!(r, "கோடு" | "குணம்"))
    {
        return stage_248_aa_maa_ko(state, is_case);
    }

    // 5. Sutra 249 (`ஒருபது/ஒருபஃது..எண்பது/எண்பஃது, ஒன்பது` + case suffix -> optional `ஆன்`).
    if is_case && (tables::in_closed_class("decade_numerals", l) || l == "ஒன்பது") {
        return stage_249_decade_aan(state);
    }

    // 6. Sutras 250 & 257 (`அவ், இவ், உவ், எவ்` + case / Vetrumai -> `[stem, அற்று (+ இன்), second]` with `suppress_205 = true`).
    if tables::in_closed_class("demonstrative_v_stems", l) && is_vetrumai {
        return stage_250_257_av_ev_arru(state, is_case);
    }

    // 7. Sutra 251 (`அஃது, இஃது, உஃது, அது, இது, உது` + case / Vetrumai -> `[அது, அன் (+ உ), second]`).
    if tables::in_closed_class("demonstrative_u_stems", l)
        && is_vetrumai
        && (is_case || r == "கோடு")
    {
        return stage_251_ahdu_an(state, is_case);
    }

    // 8. `பல` / `சில` + overt case suffix (`பல + ஐ -> பலவற்றை`, Sutra 244 `அற்று`).
    if matches!(l, "பல" | "சில") && is_case {
        let mut s = state;
        s.steps.push(DerivationStep {
            sutra: 244,
            rule_id: "nannool_244_chariyai_arru".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{} + {}", s.left, s.right),
            after: format!("{} + அற்று + {}", s.left, s.right),
        });
        let mut f_arru = BoundaryFlags::default();
        if s.right == "கு" {
            f_arru.force_165 = true;
        }
        return vec![StagedChain {
            segments: vec![
                FoldSegment::with_flags(s.left, s.flags),
                FoldSegment::with_flags("அற்று", f_arru),
                FoldSegment::plain(s.right),
            ],
            steps: s.steps,
            required_context: s.required_context,
            optional_variant: s.optional_variant,
            poetic: s.poetic,
            priority_rank: 20,
        }];
    }

    // 9. `மக + அத்து` or `ம்`-final neuter noun + case (`மரம் + ஐ -> மரத்தை`, `மரம் + கு -> மரத்துக்கு`, `மரம் + இலை -> மரத்திலை`).
    if l == "மக" && r == "அத்து" {
        let f_attu = BoundaryFlags {
            is_chariyai_attu: true,
            ..Default::default()
        };
        return vec![StagedChain {
            segments: vec![
                FoldSegment::plain("மக"),
                FoldSegment::with_flags("அத்து", f_attu),
            ],
            steps: state.steps,
            required_context: state.required_context,
            optional_variant: state.optional_variant,
            poetic: state.poetic,
            priority_rank: 20,
        }];
    }
    if l == "மக" && r == "கை" && is_vetrumai {
        // Attested Sutra 252 example `மக + கை` via `அத்து` -> `மகத்துக்கை`.
        let mut s = state;
        s.steps.push(DerivationStep {
            sutra: 244,
            rule_id: "nannool_244_chariyai_attu".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: "மக + கை".to_owned(),
            after: "மக + அத்து + கை".to_owned(),
        });
        let f_attu = BoundaryFlags {
            is_chariyai_attu: true,
            force_165: true,
            ..Default::default()
        };
        return vec![StagedChain {
            segments: vec![
                FoldSegment::plain("மக"),
                FoldSegment::with_flags("அத்து", f_attu),
                FoldSegment::plain("கை"),
            ],
            steps: s.steps,
            required_context: s.required_context,
            optional_variant: s.optional_variant,
            poetic: s.poetic,
            priority_rank: 20,
        }];
    }
    if l.ends_with("ம்") && is_case && !matches!(l, "தம்" | "நம்" | "எம்" | "நும்" | "உம்")
    {
        return stage_magara_attu(state, context);
    }
    // Sutra 243/244/252/253: `-அம்`-final non-rational content-word Vetrumai compounds
    // before vowels (`மரம் + அடி -> மரத்தடி`, `மரம் + இலை -> மரத்திலை`) or attested `குறை` (`மரத்துக்குறை`).
    let ends_with_akara_magaram = {
        let l_units: Vec<&str> = Letters::new(l).collect();
        l_units.len() >= 2
            && l_units.last().copied() == Some("ம்")
            && crate::phonology::unit_vowel(l_units[l_units.len() - 2]).as_deref() == Some("அ")
    };
    if !is_case
        && !state.flags.is_panputhogai_stem
        && ends_with_akara_magaram
        && !crate::phonology::is_thanikkuril_otru(l)
        && !matches!(l, "அகம்" | "எல்லாம்" | "தம்" | "நம்" | "எம்" | "நும்" | "உம்")
        && !tables::in_closed_class("eem_kam_urum_stems", l)
        && (is_vetrumai || rel == GrammaticalRelation::Unspecified)
        && !matches!(
            context.subtype,
            Some(
                ContextSubtype::Panputhogai
                    | ContextSubtype::Uvamaithogai
                    | ContextSubtype::Ezhuvai
                    | ContextSubtype::Vili
                    | ContextSubtype::Peyarecham
                    | ContextSubtype::VinaiMutru
                    | ContextSubtype::Ummaithogai
                    | ContextSubtype::Vinaithogai
            )
        )
    {
        let r_first = Letters::new(r).next().unwrap_or("");
        let r_vowel = is_independent_uyir(r_first);
        if r_vowel || r == "குறை" {
            let mut chains = Vec::new();
            let stem = l.strip_suffix("ம்").unwrap_or(l).to_owned();
            let mut s_attu = state.clone();
            s_attu.steps.push(DerivationStep {
                sutra: 219,
                rule_id: "nannool_219_magara_elision".to_owned(),
                stage: 1,
                transform: AlterationKind::Keduthal,
                before: format!("{l} + {r}"),
                after: format!("{stem} + {r}"),
            });
            s_attu.steps.push(DerivationStep {
                sutra: 244,
                rule_id: "nannool_244_chariyai_attu".to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{stem} + {r}"),
                after: format!("{stem} + அத்து + {r}"),
            });
            let f_attu = BoundaryFlags {
                is_chariyai_attu: true,
                ..Default::default()
            };
            chains.push(StagedChain {
                segments: vec![
                    FoldSegment::plain(stem),
                    FoldSegment::with_flags("அத்து", f_attu),
                    FoldSegment::plain(r.to_owned()),
                ],
                steps: s_attu.steps,
                required_context: if rel == GrammaticalRelation::Unspecified {
                    Some("vetrumai".to_owned())
                } else {
                    None
                },
                optional_variant: r == "குறை" && rel == GrammaticalRelation::Unspecified,
                poetic: false,
                priority_rank: 18,
            });
            let mut std_chain = StagedChain::from_state(state);
            if rel == GrammaticalRelation::Vetrumai && r_vowel {
                std_chain.optional_variant = true;
                std_chain.priority_rank = 45;
            }
            chains.push(std_chain);
            return chains;
        }
    }

    // 10. Kurriyalugaram + case suffix with Sutra 254 `இன்`-before-`இன்` hard filter!
    if is_case && classify_ugaram(l).is_kurriyalugaram() {
        // Sutra 254: NEVER insert `இன்` chariyai before 5th-case `இன்` (`நாடு + இன் -> நாட்டின்`, never `*நாட்டினின்`).
        if r == "இன்" {
            return vec![StagedChain::from_state(state)];
        }
        // 7th-case `கண்` takes `இன்` chariyai on doubled Kurriyalugaram (`நாடு + கண் -> நாட்டின்கண்`, Sutra 254).
        if r == "கண்" {
            let mut s = state;
            s.steps.push(DerivationStep {
                sutra: 244,
                rule_id: "nannool_244_chariyai_in".to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{} + கண்", s.left),
                after: format!("{} + இன் + கண்", s.left),
            });
            let f_in = BoundaryFlags {
                block_209_stop: true,
                ..Default::default()
            };
            return vec![StagedChain {
                segments: vec![
                    FoldSegment::with_flags(s.left, s.flags),
                    FoldSegment::with_flags("இன்", f_in),
                    FoldSegment::plain("கண்"),
                ],
                steps: s.steps,
                required_context: s.required_context,
                optional_variant: s.optional_variant,
                poetic: s.poetic,
                priority_rank: 20,
            }];
        }
    }

    // 11. Sutra 244 `உ` chariyai before 4th-case `கு` on consonant-final nouns (`சாத்தன் + கு -> சாத்தனுக்கு`).
    if r == "கு" {
        let last_u = Letters::new(l).last().unwrap_or("");
        if matches!(last_u, "ன்" | "ண்" | "ல்" | "ள்" | "ர்" | "ழ்" | "ய்")
        {
            let mut s = state;
            s.steps.push(DerivationStep {
                sutra: 244,
                rule_id: "nannool_244_chariyai_u".to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{} + கு", s.left),
                after: format!("{} + உ + கு", s.left),
            });
            let f_u = BoundaryFlags {
                force_165: true,
                ..Default::default()
            };
            return vec![StagedChain {
                segments: vec![
                    FoldSegment::with_flags(s.left, s.flags),
                    FoldSegment::with_flags("உ", f_u),
                    FoldSegment::plain("கு"),
                ],
                steps: s.steps,
                required_context: s.required_context,
                optional_variant: s.optional_variant,
                poetic: s.poetic,
                priority_rank: 20,
            }];
        }
    }

    // 12. Stem-level increments (`202`, `217`, `223`, `225`, `231`, `234`, `236`).
    if let Some(inc_chains) = try_stem_increments(state.clone(), context) {
        return inc_chains;
    }

    vec![StagedChain::from_state(state)]
}

fn try_sutra_255_case2_thogai(state: &BoundaryState) -> Option<Vec<StagedChain>> {
    let l = state.left.as_str();
    let r = state.right.as_str();

    // Attested *Iyalpil vikaram* & *annapiravum* (Viruttiyurai pno=298, Kandigai 255).
    let special_vikaram = match (l, r) {
        ("நின்", "புறம்") => Some("நிற்புறம்"),
        ("தலைவன்", "புகழ்ந்தான்") => Some("தலைவற்புகழ்ந்தான்"),
        ("மக", "கொடுத்தான்") => Some("மகட்கொடுத்தான்"),
        ("தாய்", "கொலை") => Some("தாய்க்கொலை"),
        ("மரம்", "குறைத்தான்") => Some("மரங்குறைத்தான்"),
        _ => None,
    };
    if let Some(surf) = special_vikaram {
        let mut s_primary = state.clone();
        s_primary.steps.push(DerivationStep {
            sutra: 255,
            rule_id: "nannool_255_case2_thogai_equivalence".to_owned(),
            stage: 2,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + {r}"),
            after: surf.to_owned(),
        });
        let primary = StagedChain {
            segments: vec![FoldSegment::plain(surf)],
            steps: s_primary.steps,
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 20,
        };
        let mut regular = StagedChain::from_state(state.clone());
        regular.optional_variant = true;
        regular.priority_rank = 45;
        return Some(vec![primary, regular]);
    }

    // Attested *Vikarattu iyalpu* (Case-2 `ஐ` elided before transitive verbs; Viruttiyurai pno=298, Kandigai 255).
    let is_vikarattu_iyalpu = matches!(
        (l, r),
        ("மண்", "கொணர்ந்தான்")
            | ("மண்", "சுமந்தான்")
            | ("பொன்", "கொடுத்தான்")
            | ("மரம்", "வெட்டினான்")
            | ("மாடு", "கொண்டான்")
            | ("பயறு", "தின்றான்")
            | ("கனி", "தின்றான்")
    );
    if is_vikarattu_iyalpu {
        let surf = format!("{l}{r}");
        let mut s_primary = state.clone();
        s_primary.steps.push(DerivationStep {
            sutra: 255,
            rule_id: "nannool_255_case2_thogai_equivalence".to_owned(),
            stage: 2,
            transform: AlterationKind::Iyalbu,
            before: format!("{l} + {r}"),
            after: surf.clone(),
        });
        let primary = StagedChain {
            segments: vec![FoldSegment::plain(surf)],
            steps: s_primary.steps,
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 20,
        };
        let mut regular = StagedChain::from_state(state.clone());
        regular.optional_variant = true;
        regular.priority_rank = 45;
        return Some(vec![primary, regular]);
    }

    None
}

fn try_sutra_256_passive_agent(state: &BoundaryState) -> Option<Vec<StagedChain>> {
    let l = state.left.as_str();
    let r = state.right.as_str();
    let r_first = Letters::new(r).next().unwrap_or("");
    if !is_vallinam_initial_unit(r_first) {
        return None;
    }
    let rm = unit_mei(r_first)?;

    // Pure Iyalpu passive verbs (`பேய் பிடிக்கப்பட்டான்`, `புலி கடிக்கப்பட்டான்`; Viruttiyurai pno=300, Kandigai 256).
    let nat_surf = format!("{l}{r}");
    let mut s_nat = state.clone();
    s_nat.steps.push(DerivationStep {
        sutra: 256,
        rule_id: "nannool_256_case3_passive_agent".to_owned(),
        stage: 2,
        transform: AlterationKind::Iyalbu,
        before: format!("{l} + {r}"),
        after: nat_surf.clone(),
    });
    let nat_chain = StagedChain {
        segments: vec![FoldSegment::plain(nat_surf)],
        steps: s_nat.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    };

    if matches!(r, "பிடிக்கப்பட்டான்" | "கடிக்கப்பட்டான்")
    {
        return Some(vec![nat_chain]);
    }

    // Vikarpam passive compounds (`பேய் கோட்பட்டான் / பேய்க் கோட்பட்டான்`, `புலி கோட்பட்டான் / புலிக் கோட்பட்டான்`).
    let dbl_surf = format!("{l}{rm}{r}");
    let mut s_dbl = state.clone();
    s_dbl.steps.push(DerivationStep {
        sutra: 256,
        rule_id: "nannool_256_case3_passive_agent".to_owned(),
        stage: 2,
        transform: AlterationKind::Thonral,
        before: format!("{l} + {r}"),
        after: dbl_surf.clone(),
    });
    let dbl_chain = StagedChain {
        segments: vec![FoldSegment::plain(dbl_surf)],
        steps: s_dbl.steps,
        required_context: None,
        optional_variant: true,
        poetic: false,
        priority_rank: 35,
    };

    Some(vec![nat_chain, dbl_chain])
}

fn stage_245_ellaam(
    state: BoundaryState,
    context: &PunarchiContext,
    is_case: bool,
) -> Vec<StagedChain> {
    let r = state.right.clone();
    let sutra = if is_case { 245 } else { 238 };
    let mut out = Vec::new();

    let make_non_rational = |with_in: bool, req_ctx: Option<String>, opt: bool, rank: u32| {
        let mut s = state.clone();
        let after = if with_in {
            format!("எல்லா + அற்று + இன் + {r} + உம்")
        } else {
            format!("எல்லா + அற்று + {r} + உம்")
        };
        s.steps.push(DerivationStep {
            sutra,
            rule_id: if is_case {
                "nannool_245_ellaam_arru_um".to_owned()
            } else {
                "nannool_238_vetrumai_porul_delegation".to_owned()
            },
            stage: 2,
            transform: AlterationKind::Thirithal,
            before: format!("எல்லாம் + {r}"),
            after,
        });
        let f_arru = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        let mut segs = vec![
            FoldSegment::plain("எல்லா"),
            FoldSegment::with_flags("அற்று", f_arru),
        ];
        if with_in {
            segs.push(FoldSegment::plain("இன்"));
        }
        segs.push(FoldSegment::plain(r.clone()));
        segs.push(FoldSegment::plain("உம்"));
        StagedChain {
            segments: segs,
            steps: s.steps,
            required_context: req_ctx,
            optional_variant: opt,
            poetic: false,
            priority_rank: rank,
        }
    };

    let make_rational = |req_ctx: Option<String>, rank: u32| {
        let mut s = state.clone();
        let (after, segs) = if r == "கு" {
            let f_nam = BoundaryFlags {
                suppress_205: true,
                ..Default::default()
            };
            let f_a = BoundaryFlags {
                force_165: true,
                ..Default::default()
            };
            (
                "எல்லா + நம் + அ + கு + உம்".to_owned(),
                vec![
                    FoldSegment::with_flags("எல்லாநம்", f_nam),
                    FoldSegment::with_flags("அ", f_a),
                    FoldSegment::plain("கு"),
                    FoldSegment::plain("உம்"),
                ],
            )
        } else {
            let f_nam = BoundaryFlags {
                force_205: true,
                is_short_chariyai_m: true,
                ..Default::default()
            };
            (
                format!("எல்லா + நம் + {r} + உம்"),
                vec![
                    FoldSegment::with_flags("எல்லாநம்", f_nam),
                    FoldSegment::plain(r.clone()),
                    FoldSegment::plain("உம்"),
                ],
            )
        };
        s.steps.push(DerivationStep {
            sutra,
            rule_id: if is_case {
                "nannool_245_ellaam_nam_um".to_owned()
            } else {
                "nannool_238_vetrumai_porul_delegation".to_owned()
            },
            stage: 2,
            transform: AlterationKind::Thirithal,
            before: format!("எல்லாம் + {r}"),
            after,
        });
        StagedChain {
            segments: segs,
            steps: s.steps,
            required_context: req_ctx,
            optional_variant: false,
            poetic: false,
            priority_rank: rank,
        }
    };

    match context.lexical_class {
        Some(LexicalClass::RationalNoun) => {
            out.push(make_rational(None, 20));
        }
        Some(LexicalClass::NonRationalNoun) => {
            out.push(make_non_rational(false, None, false, 20));
            if is_case && r != "இன்" {
                out.push(make_non_rational(true, None, true, 35));
            }
        }
        _ => {
            out.push(make_non_rational(false, None, false, 20));
            if is_case && r != "இன்" {
                out.push(make_non_rational(true, None, true, 35));
            }
            out.push(make_rational(Some("rational_noun".to_owned()), 45));
        }
    }

    out
}

fn stage_246_ellaarum(state: BoundaryState, is_case: bool) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let (base, chariyai) = if l == "எல்லாரும்" {
        ("எல்லார்", "தம்")
    } else {
        ("எல்லீர்", "நும்")
    };
    let sutra = if is_case { 246 } else { 238 };
    let rule_id = if is_case {
        "nannool_246_ellaarum_ellaeerum_um"
    } else {
        "nannool_238_vetrumai_porul_delegation"
    };

    let mut s_with = state.clone();
    let fused_ch = format!("{base}{chariyai}");
    let (after_with, segs_with) = if r == "கு" {
        let f_ch = BoundaryFlags {
            suppress_205: true,
            ..Default::default()
        };
        let f_a = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        (
            format!("{base} + {chariyai} + அ + கு + உம்"),
            vec![
                FoldSegment::with_flags(fused_ch, f_ch),
                FoldSegment::with_flags("அ", f_a),
                FoldSegment::plain("கு"),
                FoldSegment::plain("உம்"),
            ],
        )
    } else {
        let f_ch = BoundaryFlags {
            force_205: true,
            is_short_chariyai_m: true,
            ..Default::default()
        };
        (
            format!("{base} + {chariyai} + {r} + உம்"),
            vec![
                FoldSegment::with_flags(fused_ch, f_ch),
                FoldSegment::plain(r.clone()),
                FoldSegment::plain("உம்"),
            ],
        )
    };
    s_with.steps.push(DerivationStep {
        sutra,
        rule_id: rule_id.to_owned(),
        stage: 2,
        transform: AlterationKind::Thirithal,
        before: format!("{l} + {r}"),
        after: after_with,
    });
    let with_chariyai = StagedChain {
        segments: segs_with,
        steps: s_with.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    };

    let mut s_without = state;
    s_without.steps.push(DerivationStep {
        sutra,
        rule_id: rule_id.to_owned(),
        stage: 2,
        transform: AlterationKind::Thirithal,
        before: format!("{l} + {r}"),
        after: format!("{base} + {r} + உம்"),
    });
    let without_chariyai = StagedChain {
        segments: vec![
            FoldSegment::plain(base),
            FoldSegment::plain(r),
            FoldSegment::plain("உம்"),
        ],
        steps: s_without.steps,
        required_context: None,
        optional_variant: true,
        poetic: false,
        priority_rank: 35,
    };

    vec![with_chariyai, without_chariyai]
}

fn stage_248_aa_maa_ko(state: BoundaryState, is_case: bool) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let sutra = if is_case { 248 } else { 238 };
    let rule_id = if is_case {
        "nannool_248_aa_maa_ko"
    } else {
        "nannool_238_vetrumai_porul_delegation"
    };

    if !is_case {
        // Sutra 238 content-word delegation (`ஆ + கோடு -> ஆன்கோடு`).
        let mut s = state;
        s.steps.push(DerivationStep {
            sutra,
            rule_id: rule_id.to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("{l}ன் + {r}"),
        });
        let f0 = BoundaryFlags {
            block_165: true,
            block_209_stop: true,
            ..Default::default()
        };
        return vec![StagedChain {
            segments: vec![
                FoldSegment::with_flags(format!("{l}ன்"), f0),
                FoldSegment::plain(r),
            ],
            steps: s.steps,
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 20,
        }];
    }

    let mut out = Vec::new();
    // Path 1: `ன்` (+ `உ` before `கு`) -> `ஆனை`, `ஆனுக்கு`.
    let mut s_n = state.clone();
    let mut segs_n = vec![FoldSegment::plain(format!("{l}ன்"))];
    let after_n = if r == "கு" {
        let fu = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        segs_n.push(FoldSegment::with_flags("உ", fu));
        format!("{l}ன் + உ + கு")
    } else {
        format!("{l}ன் + {r}")
    };
    segs_n.push(FoldSegment::plain(r.clone()));
    s_n.steps.push(DerivationStep {
        sutra: 248,
        rule_id: "nannool_248_aa_maa_ko".to_owned(),
        stage: 2,
        transform: AlterationKind::Thonral,
        before: format!("{l} + {r}"),
        after: after_n,
    });
    out.push(StagedChain {
        segments: segs_n,
        steps: s_n.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    });

    // Path 2: `வ்` (+ `உ` before `கு`) -> `ஆவை`, `ஆவுக்கு`.
    let mut s_v = state.clone();
    if r == "கு" {
        let fu = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        s_v.steps.push(DerivationStep {
            sutra: 248,
            rule_id: "nannool_248_aa_maa_ko".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + கு"),
            after: format!("{l} + உ + கு"),
        });
        out.push(StagedChain {
            segments: vec![
                FoldSegment::plain(l.clone()),
                FoldSegment::with_flags("உ", fu),
                FoldSegment::plain("கு"),
            ],
            steps: s_v.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 35,
        });
    } else {
        let mut c = StagedChain::from_state(s_v);
        c.optional_variant = true;
        c.priority_rank = 35;
        out.push(c);
    }

    // Path 3: `இன்` (+ `உ` before `கு`) — blocked before 5th-case `இன்` per Sutra 254!
    if r != "இன்" {
        let mut s_in = state;
        let mut segs_in = vec![FoldSegment::plain(l.clone()), FoldSegment::plain("இன்")];
        let after_in = if r == "கு" {
            let fu = BoundaryFlags {
                force_165: true,
                ..Default::default()
            };
            segs_in.push(FoldSegment::with_flags("உ", fu));
            format!("{l} + இன் + உ + கு")
        } else {
            format!("{l} + இன் + {r}")
        };
        segs_in.push(FoldSegment::plain(r));
        s_in.steps.push(DerivationStep {
            sutra: 248,
            rule_id: "nannool_248_aa_maa_ko".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {}", segs_in.last().unwrap().text),
            after: after_in,
        });
        out.push(StagedChain {
            segments: segs_in,
            steps: s_in.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 40,
        });
    }

    out
}

fn stage_249_decade_aan(state: BoundaryState) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let prefix = l
        .strip_suffix("பஃது")
        .or_else(|| l.strip_suffix("பது"))
        .unwrap_or(&l);
    let mut s_aan = state.clone();
    let p_stem = format!("{prefix}ப்");
    s_aan.steps.push(DerivationStep {
        sutra: 249,
        rule_id: "nannool_249_decade_aan".to_owned(),
        stage: 2,
        transform: AlterationKind::Thirithal,
        before: format!("{l} + {r}"),
        after: format!("{p_stem} + ஆன் + {r}"),
    });
    let f_p = BoundaryFlags {
        suppress_205: true,
        ..Default::default()
    };
    let aan_chain = StagedChain {
        segments: vec![
            FoldSegment::with_flags(p_stem, f_p),
            FoldSegment::plain("ஆன்"),
            FoldSegment::plain(r),
        ],
        steps: s_aan.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    };

    let mut std_chain = StagedChain::from_state(state);
    std_chain.optional_variant = true;
    std_chain.priority_rank = 40;

    vec![aan_chain, std_chain]
}

fn stage_250_257_av_ev_arru(state: BoundaryState, is_case: bool) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let is_ev = l == "எவ்";
    let (sutra, rule_id) = if is_ev {
        (257, "nannool_257_ev_arru")
    } else if is_case {
        (250, "nannool_250_av_iv_uv_arru")
    } else {
        (238, "nannool_238_vetrumai_porul_delegation")
    };

    // Sutra 250.3: suppress Sutra 205 gemination (`அவற்றை`, never `*அவ்வற்றை`).
    let f0 = BoundaryFlags {
        suppress_205: true,
        ..Default::default()
    };
    let f_arru = BoundaryFlags {
        force_165: true,
        ..Default::default()
    };

    let mut s1 = state.clone();
    s1.steps.push(DerivationStep {
        sutra,
        rule_id: rule_id.to_owned(),
        stage: 2,
        transform: AlterationKind::Thonral,
        before: format!("{l} + {r}"),
        after: format!("{l} + அற்று + {r}"),
    });
    let mut out = vec![StagedChain {
        segments: vec![
            FoldSegment::with_flags(l.clone(), f0),
            FoldSegment::with_flags("அற்று", f_arru),
            FoldSegment::plain(r.clone()),
        ],
        steps: s1.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    }];

    // Sutra 250.2: optional `+ இன்` (`அவற்றினை`), blocked before 5th-case `இன்` per 254.
    if is_case && r != "இன்" {
        let mut s2 = state;
        s2.steps.push(DerivationStep {
            sutra,
            rule_id: rule_id.to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("{l} + அற்று + இன் + {r}"),
        });
        out.push(StagedChain {
            segments: vec![
                FoldSegment::with_flags(l, f0),
                FoldSegment::plain("அற்று"),
                FoldSegment::plain("இன்"),
                FoldSegment::plain(r),
            ],
            steps: s2.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 35,
        });
    }

    out
}

fn stage_251_ahdu_an(state: BoundaryState, is_case: bool) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let base_no_aytham = match l.as_str() {
        "அஃது" | "அது" => "அது",
        "இஃது" | "இது" => "இது",
        _ => "உது",
    };
    let sutra = if is_case { 251 } else { 238 };
    let rule_id = if is_case {
        "nannool_251_ahdu_an"
    } else {
        "nannool_238_vetrumai_porul_delegation"
    };

    let mut out = Vec::new();
    // Path 1: `base_no_aytham` + `அன்` + `r` (eliding `உ` of `அது` into `அன்` -> `அதன்`).
    let mut s1 = state.clone();
    s1.steps.push(DerivationStep {
        sutra,
        rule_id: rule_id.to_owned(),
        stage: 2,
        transform: AlterationKind::Thirithal,
        before: format!("{l} + {r}"),
        after: format!("{base_no_aytham} + அன் + {r}"),
    });
    // Strip `உ` directly so `அது + அன்` -> `அத் + அன்` -> `அதன்` cleanly even though `அது` is Mutriyalugaram.
    let stem_cut = base_no_aytham.strip_suffix("து").unwrap_or(base_no_aytham);
    let f_cut = BoundaryFlags {
        suppress_205: true,
        ..Default::default()
    };
    let f_an = BoundaryFlags {
        block_209_stop: !is_case,
        ..Default::default()
    };
    out.push(StagedChain {
        segments: vec![
            FoldSegment::with_flags(format!("{stem_cut}த்"), f_cut),
            FoldSegment::with_flags("அன்", f_an),
            FoldSegment::plain(r.clone()),
        ],
        steps: s1.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    });

    // If `r == "கு"`, also emit `அன் + உ + கு` (`அதனுக்கு`).
    if r == "கு" {
        let mut s_u = state.clone();
        s_u.steps.push(DerivationStep {
            sutra: 251,
            rule_id: "nannool_251_ahdu_an".to_owned(),
            stage: 2,
            transform: AlterationKind::Thirithal,
            before: format!("{l} + கு"),
            after: format!("{base_no_aytham} + அன் + உ + கு"),
        });
        let fu = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        out.push(StagedChain {
            segments: vec![
                FoldSegment::with_flags(format!("{stem_cut}த்"), f_cut),
                FoldSegment::plain("அன்"),
                FoldSegment::with_flags("உ", fu),
                FoldSegment::plain("கு"),
            ],
            steps: s_u.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 35,
        });
    } else if is_case {
        // Optional no-`அன்` form (`அஃதை` / `அதை`).
        let mut s_no_an = state;
        let base_cut = l.strip_suffix("து").unwrap_or(&l);
        s_no_an.steps.push(DerivationStep {
            sutra: 164,
            rule_id: "nannool_164_kurriyalugaram_elision".to_owned(),
            stage: 3,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + {r}"),
            after: format!("{base_cut}த் + {r}"),
        });
        out.push(StagedChain {
            segments: vec![
                FoldSegment::with_flags(format!("{base_cut}த்"), f_cut),
                FoldSegment::plain(r),
            ],
            steps: s_no_an.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 45,
        });
    }

    out
}

fn stage_magara_attu(state: BoundaryState, context: &PunarchiContext) -> Vec<StagedChain> {
    let l = state.left.clone();
    let r = state.right.clone();
    let stem = l.strip_suffix("ம்").unwrap_or(&l).to_owned();

    // Sutra 219 (`மரம் -> மர`) + Sutra 244 (`அத்து`) -> Fold 1 triggers Sutra 252 in Stage 3A!
    let mut s1 = state.clone();
    s1.steps.push(DerivationStep {
        sutra: 219,
        rule_id: "nannool_219_magara_elision".to_owned(),
        stage: 1,
        transform: AlterationKind::Keduthal,
        before: format!("{l} + {r}"),
        after: format!("{stem} + {r}"),
    });
    s1.steps.push(DerivationStep {
        sutra: 244,
        rule_id: "nannool_244_chariyai_attu".to_owned(),
        stage: 2,
        transform: AlterationKind::Thonral,
        before: format!("{stem} + {r}"),
        after: format!("{stem} + அத்து + {r}"),
    });

    let f_attu = BoundaryFlags {
        is_chariyai_attu: true,
        force_165: r == "கு",
        ..Default::default()
    };

    let mut out = vec![StagedChain {
        segments: vec![
            FoldSegment::plain(stem.clone()),
            FoldSegment::with_flags("அத்து", f_attu),
            FoldSegment::plain(r.clone()),
        ],
        steps: s1.steps,
        required_context: None,
        optional_variant: false,
        poetic: false,
        priority_rank: 20,
    }];

    // Sutra 243 multi-chariyai stacked variant (`அத்து + இன்`, or `அத்து + இன் + உ` before `கு`), respecting 254 (no `இன்` before `இன்`).
    if r != "இன்" {
        let mut s2 = state.clone();
        s2.steps.push(DerivationStep {
            sutra: 219,
            rule_id: "nannool_219_magara_elision".to_owned(),
            stage: 1,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + {r}"),
            after: format!("{stem} + {r}"),
        });
        let mut segs2 = vec![
            FoldSegment::plain(stem.clone()),
            FoldSegment::with_flags("அத்து", f_attu),
            FoldSegment::plain("இன்"),
        ];
        let after2 = if r == "கு" {
            let fu = BoundaryFlags {
                force_165: true,
                ..Default::default()
            };
            segs2.push(FoldSegment::with_flags("உ", fu));
            format!("{stem} + அத்து + இன் + உ + கு")
        } else {
            format!("{stem} + அத்து + இன் + {r}")
        };
        segs2.push(FoldSegment::plain(r.clone()));
        s2.steps.push(DerivationStep {
            sutra: 243,
            rule_id: "nannool_243_multi_chariyai".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{stem} + {r}"),
            after: after2,
        });
        out.push(StagedChain {
            segments: segs2,
            steps: s2.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 35,
        });
    }

    // Sutra 243.3: poetic omission of `அத்து` (`மாடம் + கு -> மாடக்கு`) when `poetic == true`.
    if context.poetic && r == "கு" {
        let mut s_poet = state;
        s_poet.steps.push(DerivationStep {
            sutra: 219,
            rule_id: "nannool_219_magara_elision".to_owned(),
            stage: 1,
            transform: AlterationKind::Keduthal,
            before: format!("{l} + கு"),
            after: format!("{stem} + கு"),
        });
        s_poet.steps.push(DerivationStep {
            sutra: 243,
            rule_id: "nannool_243_poetic_attu_omission".to_owned(),
            stage: 2,
            transform: AlterationKind::Keduthal,
            before: format!("{stem} + கு"),
            after: format!("{stem} + கு"),
        });
        let f_stem = BoundaryFlags {
            force_165: true,
            ..Default::default()
        };
        out.push(StagedChain {
            segments: vec![
                FoldSegment::with_flags(stem, f_stem),
                FoldSegment::plain("கு"),
            ],
            steps: s_poet.steps,
            required_context: None,
            optional_variant: true,
            poetic: true,
            priority_rank: 60,
        });
    }

    out
}

fn try_stem_increments(
    state: BoundaryState,
    context: &PunarchiContext,
) -> Option<Vec<StagedChain>> {
    let l_owned = state.left.clone();
    let r_owned = state.right.clone();
    let l = l_owned.as_str();
    let r = r_owned.as_str();
    let r_first = Letters::new(r).next().unwrap_or("");
    let r_vowel = is_independent_uyir(r_first);
    let r_mei = unit_mei(r_first);
    let rel = context.effective_relation();

    // Sutra 202: `ஐ`-final botanical stems + `அம்` in Vetrumai.
    if rel == GrammaticalRelation::Vetrumai {
        if tables::in_closed_class("ai_retain_am_stems", l) {
            let mut s = state;
            s.steps.push(DerivationStep {
                sutra: 202,
                rule_id: "nannool_202_ai_am_chariyai".to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{l} + {r}"),
                after: format!("{l} + அம் + {r}"),
            });
            let f_am = BoundaryFlags {
                is_short_chariyai_m: true,
                ..Default::default()
            };
            return Some(vec![StagedChain {
                segments: vec![
                    FoldSegment::plain(l),
                    FoldSegment::with_flags("அம்", f_am),
                    FoldSegment::plain(r),
                ],
                steps: s.steps,
                required_context: None,
                optional_variant: false,
                poetic: false,
                priority_rank: 20,
            }]);
        }
        if tables::in_closed_class("ai_drop_am_stems", l) {
            let units: Vec<&str> = Letters::new(l).collect();
            if let Some(&last_u) = units.last() {
                if let Ok(parts) = tamil_core::split_uyirmei(last_u) {
                    let prefix: String = units[..units.len() - 1].concat();
                    let cut = format!("{prefix}{}", parts.mei);
                    let mut s = state;
                    s.steps.push(DerivationStep {
                        sutra: 202,
                        rule_id: "nannool_202_ai_am_chariyai".to_owned(),
                        stage: 2,
                        transform: AlterationKind::Thirithal,
                        before: format!("{l} + {r}"),
                        after: format!("{cut} + அம் + {r}"),
                    });
                    let f_cut = BoundaryFlags {
                        suppress_205: true,
                        ..Default::default()
                    };
                    let f_am = BoundaryFlags {
                        is_short_chariyai_m: true,
                        ..Default::default()
                    };
                    return Some(vec![StagedChain {
                        segments: vec![
                            FoldSegment::with_flags(cut, f_cut),
                            FoldSegment::with_flags("அம்", f_am),
                            FoldSegment::plain(r),
                        ],
                        steps: s.steps,
                        required_context: None,
                        optional_variant: false,
                        poetic: false,
                        priority_rank: 20,
                    }]);
                }
            }
        }
    }

    // Sutra 207 & 208: Root verbal nouns / imperatives ending in `ஞ, ண, ந, ம, ல, வ, ள, ன` + non-`ய` consonant -> `+ உ` (`207`), `ந்` Vetrumai -> `+ அ` (`208`).
    if !r_vowel && r_mei.as_deref() != Some("ய்") {
        let last_u = Letters::new(l).last().unwrap_or("");
        if matches!(last_u, "ஞ்" | "ண்" | "ந்" | "ம்" | "ல்" | "வ்" | "ள்" | "ன்")
            && (context.lexical_class == Some(LexicalClass::VerbalNounRoot)
                || context.subtype == Some(crate::context::ContextSubtype::Imperative))
        {
            let mut out = Vec::new();
            let mut s_u = state.clone();
            s_u.steps.push(DerivationStep {
                sutra: 207,
                rule_id: "nannool_207_verbal_noun_root_u".to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{l} + {r}"),
                after: format!("{l} + உ + {r}"),
            });
            let fu = BoundaryFlags {
                force_165: is_vallinam_initial_unit(r_first),
                ..Default::default()
            };
            out.push(StagedChain {
                segments: vec![
                    FoldSegment::plain(l),
                    FoldSegment::with_flags("உ", fu),
                    FoldSegment::plain(r),
                ],
                steps: s_u.steps,
                required_context: None,
                optional_variant: false,
                poetic: false,
                priority_rank: 20,
            });
            if last_u == "ந்"
                && rel == GrammaticalRelation::Vetrumai
                && context.lexical_class == Some(LexicalClass::VerbalNounRoot)
            {
                let mut s_a = state.clone();
                s_a.steps.push(DerivationStep {
                    sutra: 208,
                    rule_id: "nannool_208_na_verbal_noun_a".to_owned(),
                    stage: 2,
                    transform: AlterationKind::Thonral,
                    before: format!("{l} + {r}"),
                    after: format!("{l} + அ + {r}"),
                });
                let fa = BoundaryFlags {
                    force_165: is_vallinam_initial_unit(r_first),
                    ..Default::default()
                };
                out.push(StagedChain {
                    segments: vec![
                        FoldSegment::plain(l),
                        FoldSegment::with_flags("அ", fa),
                        FoldSegment::plain(r),
                    ],
                    steps: s_a.steps,
                    required_context: None,
                    optional_variant: true,
                    poetic: false,
                    priority_rank: 35,
                });
            }
            if context.subtype == Some(crate::context::ContextSubtype::Imperative)
                && matches!(last_u, "ண்" | "ன்" | "ல்" | "ள்")
            {
                let mut nat = StagedChain::from_state(state);
                nat.optional_variant = true;
                nat.priority_rank = 40;
                out.push(nat);
            }
            return Some(out);
        }
    }

    // Sutra 212: `ன்`-final clan/branch names (`எயின் + குடி`) stay natural or take `+ அ` in Vetrumai (`எயின்குடி` / `எயினக்குடி`).
    if l.ends_with("ன்")
        && rel == GrammaticalRelation::Vetrumai
        && context.lexical_class == Some(LexicalClass::BranchName)
        && !r_vowel
    {
        let mut s_nat = state.clone();
        s_nat.steps.push(DerivationStep {
            sutra: 212,
            rule_id: "nannool_212_na_branch_name".to_owned(),
            stage: 3,
            transform: AlterationKind::Iyalbu,
            before: format!("{l} + {r}"),
            after: format!("{l}{r}"),
        });
        let f_nat = BoundaryFlags {
            block_209_stop: true,
            ..Default::default()
        };
        let nat_chain = StagedChain {
            segments: vec![FoldSegment::with_flags(l, f_nat), FoldSegment::plain(r)],
            steps: s_nat.steps,
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 20,
        };

        let mut s_a = state;
        s_a.steps.push(DerivationStep {
            sutra: 212,
            rule_id: "nannool_212_na_branch_name".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("{l} + அ + {r}"),
        });
        let fa = BoundaryFlags {
            force_165: is_vallinam_initial_unit(r_first),
            ..Default::default()
        };
        let a_chain = StagedChain {
            segments: vec![
                FoldSegment::plain(l),
                FoldSegment::with_flags("அ", fa),
                FoldSegment::plain(r),
            ],
            steps: s_a.steps,
            required_context: None,
            optional_variant: true,
            poetic: false,
            priority_rank: 35,
        };
        return Some(vec![nat_chain, a_chain]);
    }

    // Sutra 217 (`மின், பின், பன், கன்`), 223 (`ஈம், கம், உரும்`), 231 (`வல்` DiceVal), 234 (`புள், வள்`), 236 (`தெவ்`) + consonant != `ய`.
    if !r_vowel && r_mei.as_deref() != Some("ய்") {
        let inc_rule = if tables::in_closed_class("min_pin_pan_kan_stems", l) {
            Some((217, "nannool_217_min_pin_pan_kan"))
        } else if tables::in_closed_class("eem_kam_urum_stems", l) {
            Some((223, "nannool_223_eem_kam_urum"))
        } else if l == "வல்" && context.lexical_class == Some(LexicalClass::DiceVal) {
            Some((231, "nannool_231_val_dice"))
        } else if tables::in_closed_class("pul_val_stems", l) {
            Some((234, "nannool_234_pul_val"))
        } else if l == "தெவ்" {
            Some((236, "nannool_236_thev"))
        } else {
            None
        };

        if let Some((sutra, rid)) = inc_rule {
            let mut out = Vec::new();
            let mut s_u = state.clone();
            s_u.steps.push(DerivationStep {
                sutra,
                rule_id: rid.to_owned(),
                stage: 2,
                transform: AlterationKind::Thonral,
                before: format!("{l} + {r}"),
                after: format!("{l} + உ + {r}"),
            });
            let f_stem = BoundaryFlags {
                is_short_chariyai_m: l.ends_with("ம்"),
                ..Default::default()
            };
            let fu = BoundaryFlags {
                force_165: is_vallinam_initial_unit(r_first),
                ..Default::default()
            };
            out.push(StagedChain {
                segments: vec![
                    FoldSegment::with_flags(l, f_stem),
                    FoldSegment::with_flags("உ", fu),
                    FoldSegment::plain(r),
                ],
                steps: s_u.steps,
                required_context: None,
                optional_variant: false,
                poetic: false,
                priority_rank: 20,
            });

            // Optional `+ அ` for `ஈம்/கம்/வல்` (223/231 Vetrumai) and `கன்` (217 before Vallinam).
            let allow_a = (matches!(l, "ஈம்" | "கம்" | "வல்") && rel == GrammaticalRelation::Vetrumai)
                || (l == "கன்" && is_vallinam_initial_unit(r_first));
            if allow_a {
                let mut s_a = state.clone();
                s_a.steps.push(DerivationStep {
                    sutra,
                    rule_id: rid.to_owned(),
                    stage: 2,
                    transform: AlterationKind::Thonral,
                    before: format!("{l} + {r}"),
                    after: format!("{l} + அ + {r}"),
                });
                let fa = BoundaryFlags {
                    force_165: is_vallinam_initial_unit(r_first),
                    ..Default::default()
                };
                out.push(StagedChain {
                    segments: vec![
                        FoldSegment::with_flags(l, f_stem),
                        FoldSegment::with_flags("அ", fa),
                        FoldSegment::plain(r),
                    ],
                    steps: s_a.steps,
                    required_context: None,
                    optional_variant: true,
                    poetic: false,
                    priority_rank: 35,
                });
            }

            // Sutra 236: `தெவ்` + `ம` also allows `வ் -> ம்` (`தெம்மன்னர்`).
            if l == "தெவ்" && r_mei.as_deref() == Some("ம்") {
                let mut s_m = state;
                s_m.steps.push(DerivationStep {
                    sutra: 236,
                    rule_id: "nannool_236_thev".to_owned(),
                    stage: 2,
                    transform: AlterationKind::Thirithal,
                    before: format!("தெவ் + {r}"),
                    after: format!("தெம் + {r}"),
                });
                out.push(StagedChain {
                    segments: vec![FoldSegment::plain("தெம்"), FoldSegment::plain(r)],
                    steps: s_m.steps,
                    required_context: None,
                    optional_variant: true,
                    poetic: false,
                    priority_rank: 35,
                });
            }
            return Some(out);
        }
    }

    // Sutra 225: `தமிழ்` in Vetrumai before consonant (`+ அ`), `தாழ் + கோல்` (`+ அ` -> `தாழக்கோல்`).
    if (l == "தமிழ்"
        && rel == GrammaticalRelation::Vetrumai
        && !r_vowel
        && !tables::is_overt_case_suffix(r))
        || (l == "தாழ்" && r == "கோல்")
    {
        let mut s = state;
        s.steps.push(DerivationStep {
            sutra: 225,
            rule_id: "nannool_225_tamil_thaazh".to_owned(),
            stage: 2,
            transform: AlterationKind::Thonral,
            before: format!("{l} + {r}"),
            after: format!("{l} + அ + {r}"),
        });
        let fa = BoundaryFlags {
            force_165: is_vallinam_initial_unit(r_first),
            ..Default::default()
        };
        return Some(vec![StagedChain {
            segments: vec![
                FoldSegment::plain(l),
                FoldSegment::with_flags("அ", fa),
                FoldSegment::plain(r),
            ],
            steps: s.steps,
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 20,
        }]);
    }

    None
}
