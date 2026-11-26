//! Core acyclic 4-stage forward Sandhi pipeline, branch deduplication, canonical ranking, and rule queries.

use crate::closed_class;
use crate::context::{
    AlterationKind, DerivationStep, GrammaticalRelation, JoinAlternative, PunarchiChapter,
    PunarchiContext, PunarchiError, PunarchiJoinResult, PunarchiProfile,
};
use crate::meyyeeru;
use crate::phonology::{has_boundary_barrier, is_independent_uyir, is_native_mei};
use crate::tables::{self, SutraInventoryEntry};
use crate::urupu::{self, StagedChain};
use crate::uyireeru;
use std::collections::HashSet;
use tamil_core::{compose_uyirmei, is_mei, Letters};
use tamil_norm::normalize_nfc;

/// Transient per-boundary state preventing downstream general rules from clobbering upstream exceptions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct BoundaryFlags {
    /// Marks derived finals (`விதியீறு`) such as `வட்டம்->வட்ட`, `ஆடு->ஆட்டு`.
    pub is_derived_final: bool,
    /// Blocks Sutra 165 Vallinam doubling (`167, 168, 171, 173, 174, 177, 178, 179, 181, 182, 201`).
    pub block_165: bool,
    /// Forces Sutra 165 Vallinam doubling (`165.2` `நொ/து`, `183` `டு/று`, `242.2` `கு`).
    pub force_165: bool,
    /// Suppresses Sutra 205 Thanikkuril doubling (`247.5` pronouns + `250.3` `அவ்/இவ்/உவ்/எவ்`).
    pub suppress_205: bool,
    /// Forces Sutra 205 coda doubling on appended short-vowel Chariyais (`நம்/தம்/நும்` in `எல்லாநம்மை`).
    pub force_205: bool,
    /// Marks appended short-vowel `ம்`-final Chariyai (`நம்/தம்/நும்/அம்`) so `219` assimilates instead of deleting `ம்`.
    pub is_short_chariyai_m: bool,
    /// Blocks Sutra 209 `ன் -> ற்` stop mutation on Chariyai `அன்/இன்/ன்` before content words (`அதன்கோடு`, `நாட்டின்கண்`, `ஆன்கோடு`).
    pub block_209_stop: bool,
    /// Marks `அத்து` Chariyai segment so Sutra 252 fires in Stage 3A before Sutra 162.
    pub is_chariyai_attu: bool,
    /// Records pre-mutation `(left_final, orig_right_initial)` from Stage 3B (`237`) for Stage 3C (`209/210/227/228/229`).
    pub triggered_237: Option<(char, char)>,
    /// Blocks Sutra 229 deletion (e.g. `மேற்கு + திசை -> மேற்றிசை` in Sutra 186).
    pub block_229: bool,
    /// Marks Sutra 186 direction-derived `கீழ்` (`கிழக்கு -> கீழ்`) so Sutra 226 does not demote `கீழ்க்கடல்`/`கீழ்த்திசை`.
    pub is_direction_keezh: bool,
    /// Marks Sutra 136 `-மை` dropped stems (`Panputhogai` *Alvazhi*) so `209` does not emit bogus `Vetrumai` variants.
    pub is_panputhogai_stem: bool,
}

/// Active boundary state threaded through Stages 1 -> 2 -> 3A -> 3B -> 3C -> 3D -> 4.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryState {
    pub left: String,
    pub right: String,
    pub flags: BoundaryFlags,
    pub steps: Vec<DerivationStep>,
    pub required_context: Option<String>,
    pub optional_variant: bool,
    pub poetic: bool,
    pub priority_rank: u32,
}

impl BoundaryState {
    pub fn new(left: String, right: String) -> Self {
        Self {
            left,
            right,
            flags: BoundaryFlags::default(),
            steps: Vec::new(),
            required_context: None,
            optional_variant: false,
            poetic: false,
            priority_rank: 100,
        }
    }
}

/// One segment in a Stage 2 multi-segment chain folded left-to-right.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FoldSegment {
    pub text: String,
    pub flags: BoundaryFlags,
}

impl FoldSegment {
    pub fn plain(text: impl Into<String>) -> Self {
        Self {
            text: text.into(),
            flags: BoundaryFlags::default(),
        }
    }

    pub fn with_flags(text: impl Into<String>, flags: BoundaryFlags) -> Self {
        Self {
            text: text.into(),
            flags,
        }
    }
}

/// Candidate derivation branch produced during pipeline evaluation.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Branch {
    pub surface: String,
    pub steps: Vec<DerivationStep>,
    pub required_context: Option<String>,
    pub optional_variant: bool,
    pub poetic: bool,
    pub priority_rank: u32,
}

impl Branch {
    pub fn primary_transform(&self) -> AlterationKind {
        let mut saw_thonral = false;
        let mut saw_thirithal = false;
        let mut saw_keduthal = false;
        for step in &self.steps {
            match step.transform {
                AlterationKind::Iyalbu => {}
                AlterationKind::Thonral => saw_thonral = true,
                AlterationKind::Thirithal => saw_thirithal = true,
                AlterationKind::Keduthal => saw_keduthal = true,
            }
        }
        match (saw_thirithal, saw_keduthal, saw_thonral) {
            (true, _, _) => AlterationKind::Thirithal,
            (false, true, true) => AlterationKind::Thirithal,
            (false, true, false) => AlterationKind::Keduthal,
            (false, false, true) => AlterationKind::Thonral,
            (false, false, false) => AlterationKind::Iyalbu,
        }
    }

    fn rule_signature(&self) -> Vec<&str> {
        self.steps.iter().map(|s| s.rule_id.as_str()).collect()
    }

    fn sort_key(&self) -> (u8, u8, u32, u16, &str) {
        let poetic_key = u8::from(self.poetic);
        let optional_key = u8::from(self.optional_variant || self.required_context.is_some());
        let first_sutra = self
            .steps
            .iter()
            .find(|s| s.sutra != 153 && s.sutra != 204)
            .or_else(|| self.steps.first())
            .map_or(u16::MAX, |s| s.sutra);
        (
            poetic_key,
            optional_key,
            self.priority_rank,
            first_sutra,
            self.surface.as_str(),
        )
    }
}

/// Return the full 117-sutra inventory for `profile`.
pub fn punarchi_rules(profile: PunarchiProfile) -> &'static [SutraInventoryEntry] {
    match profile {
        PunarchiProfile::NannoolV1 => tables::INVENTORY,
    }
}

/// Filter the 117-sutra inventory by optional chapter and/or exact sutra number.
pub fn punarchi_rules_filtered(
    profile: PunarchiProfile,
    chapter: Option<PunarchiChapter>,
    sutra: Option<u16>,
) -> Result<Vec<SutraInventoryEntry>, PunarchiError> {
    let entries = punarchi_rules(profile);
    if let Some(num) = sutra {
        let Some(entry) = tables::inventory_entry(num) else {
            return Err(PunarchiError::SutraOutOfRange);
        };
        if let Some(ch) = chapter {
            if entry.chapter != ch.as_str() {
                return Ok(Vec::new());
            }
        }
        return Ok(vec![*entry]);
    }

    let out = match chapter {
        Some(ch) => entries
            .iter()
            .copied()
            .filter(|e| e.chapter == ch.as_str())
            .collect(),
        None => entries.to_vec(),
    };
    Ok(out)
}

/// Stage 4: Orthographic fusion (Sutra 204 *Udalmel Uyir*) + canonical NFC normalization.
pub fn apply_stage_4_fusion(left: &str, right: &str, steps: &mut Vec<DerivationStep>) -> String {
    let left_nfc = normalize_nfc(left);
    let right_nfc = normalize_nfc(right);

    let left_units: Vec<&str> = Letters::new(&left_nfc).collect();
    let right_units: Vec<&str> = Letters::new(&right_nfc).collect();

    if let (Some(&last_l), Some(&first_r)) = (left_units.last(), right_units.first()) {
        if is_mei(last_l) && is_native_mei(last_l) && is_independent_uyir(first_r) {
            if let Ok(fused) = compose_uyirmei(last_l, first_r) {
                let prefix: String = left_units[..left_units.len() - 1].concat();
                let suffix: String = right_units[1..].concat();
                let after = normalize_nfc(&format!("{prefix}{fused}{suffix}"));
                steps.push(DerivationStep {
                    sutra: 204,
                    rule_id: "nannool_204_udalmel_uyir".to_owned(),
                    stage: 4,
                    transform: AlterationKind::Iyalbu,
                    before: format!("{left_nfc} + {right_nfc}"),
                    after: after.clone(),
                });
                return after;
            }
        }
    }

    normalize_nfc(&format!("{left_nfc}{right_nfc}"))
}

/// Evaluate Stages `3A -> 3B -> 3C -> 3D -> 4` across a single boundary state.
pub fn evaluate_boundary(
    state: BoundaryState,
    context: &PunarchiContext,
    emit_passthrough_if_empty: bool,
) -> Vec<Branch> {
    let steps_before_fold = state.steps.len();

    // Stage 3A: Pre-glide boundary overrides (`252`, `163`, `106`, `R163.4`).
    // When Stage 3A fires (`Some`), it bypasses Stage 3B/3C and proceeds directly to Stage 3D -> Stage 4.
    let s_3c_list = if let Some(override_states) = uyireeru::apply_stage_3a(state.clone(), context)
    {
        override_states
    } else {
        // Stage 3B: Pre-mutation 237 (`ன்/ல்/ண்/ள் + த/ந`).
        let s_3b = meyyeeru::apply_stage_3b(state);

        // Stage 3C: Disjoint by final (pure Mei consonant vs Vowel/Uyirmei).
        let is_cons_final = Letters::new(&s_3b.left)
            .last()
            .is_some_and(|u| is_mei(u) && is_native_mei(u));

        if is_cons_final {
            meyyeeru::apply_stage_3c_consonant_final(s_3b, context)
        } else {
            uyireeru::apply_stage_3c_vowel_final(s_3b, context)
        }
    };

    // Stage 3D (205) -> Stage 4 (204 fusion + NFC + optional fallback 153).
    let mut branches = Vec::with_capacity(s_3c_list.len());
    for s_3c in s_3c_list {
        let mut s_3d = meyyeeru::apply_stage_3d(s_3c);
        let before_fallback = format!("{} + {}", s_3d.left, s_3d.right);
        let steps_before_s4 = s_3d.steps.len();
        let surface = apply_stage_4_fusion(&s_3d.left, &s_3d.right, &mut s_3d.steps);
        if s_3d.steps.is_empty() && emit_passthrough_if_empty {
            s_3d.steps.push(DerivationStep {
                sutra: 153,
                rule_id: "nannool_153_iyalbu_passthrough".to_owned(),
                stage: 4,
                transform: AlterationKind::Iyalbu,
                before: before_fallback,
                after: surface.clone(),
            });
        } else if s_3d.steps.len() == steps_before_s4 && s_3d.steps.len() > steps_before_fold {
            // Final Stage 3 step completes this boundary directly without a Stage 4 `204` fusion step.
            if let Some(last_step) = s_3d.steps.last_mut() {
                last_step.after = surface.clone();
            }
        } else if emit_passthrough_if_empty
            && s_3d.steps.len() == steps_before_s4
            && s_3d.steps.last().is_some_and(|st| st.after.contains(" + "))
        {
            if let Some(last_step) = s_3d.steps.last_mut() {
                last_step.after = surface.clone();
            }
        }
        branches.push(Branch {
            surface,
            steps: s_3d.steps,
            required_context: s_3d.required_context,
            optional_variant: s_3d.optional_variant,
            poetic: s_3d.poetic,
            priority_rank: s_3d.priority_rank,
        });
    }
    branches
}

/// Fold a Stage 2 multi-segment chain strictly left-to-right through Stages 3A -> 4.
fn fold_chain(chain: StagedChain, context: &PunarchiContext) -> Vec<Branch> {
    if chain.segments.is_empty() {
        return Vec::new();
    }
    if chain.segments.len() == 1 {
        return vec![Branch {
            surface: normalize_nfc(&chain.segments[0].text),
            steps: chain.steps,
            required_context: chain.required_context,
            optional_variant: chain.optional_variant,
            poetic: chain.poetic,
            priority_rank: chain.priority_rank,
        }];
    }

    let mut active: Vec<(Branch, BoundaryFlags)> = vec![(
        Branch {
            surface: chain.segments[0].text.clone(),
            steps: chain.steps,
            required_context: chain.required_context,
            optional_variant: chain.optional_variant,
            poetic: chain.poetic,
            priority_rank: chain.priority_rank,
        },
        chain.segments[0].flags,
    )];

    let last_idx = chain.segments.len() - 1;
    for (idx, next_seg) in chain.segments.iter().enumerate().skip(1) {
        let is_final_fold = idx == last_idx;
        let mut next_active = Vec::new();
        for (acc_branch, acc_flags) in active {
            let mut fold_flags = acc_flags;
            fold_flags.is_chariyai_attu = next_seg.flags.is_chariyai_attu;
            let state = BoundaryState {
                left: acc_branch.surface,
                right: next_seg.text.clone(),
                flags: fold_flags,
                steps: acc_branch.steps,
                required_context: acc_branch.required_context,
                optional_variant: acc_branch.optional_variant,
                poetic: acc_branch.poetic,
                priority_rank: acc_branch.priority_rank,
            };
            let mut outgoing_flags = next_seg.flags;
            outgoing_flags.is_chariyai_attu = false;
            for b in evaluate_boundary(state, context, is_final_fold) {
                next_active.push((b, outgoing_flags));
            }
        }
        active = next_active;
    }

    active.into_iter().map(|(b, _)| b).collect()
}

/// Join two words through the acyclic 4-stage pipeline.
pub fn punarchi_join(
    first: &str,
    second: &str,
    context: &PunarchiContext,
    profile: PunarchiProfile,
) -> Result<PunarchiJoinResult, PunarchiError> {
    if first.trim().is_empty() || second.trim().is_empty() {
        return Err(PunarchiError::EmptyInput);
    }
    context.validate()?;

    // Stage 0: Non-Tamil / ZWJ / ZWNJ boundary barrier -> verbatim Iyalbu passthrough.
    if has_boundary_barrier(first, second) {
        let surface = format!("{first}{second}");
        return Ok(PunarchiJoinResult {
            profile,
            surface: surface.clone(),
            transform: AlterationKind::Iyalbu,
            steps: vec![DerivationStep {
                sutra: 153,
                rule_id: "nannool_153_iyalbu_passthrough".to_owned(),
                stage: 4,
                transform: AlterationKind::Iyalbu,
                before: format!("{first} + {second}"),
                after: surface,
            }],
            alternatives: Vec::new(),
        });
    }

    let first_nfc = normalize_nfc(first);
    let second_nfc = normalize_nfc(second);

    // Promote Unspecified relation to Vetrumai for unambiguous overt case suffixes.
    let mut effective_ctx = context.clone();
    if effective_ctx.relation == GrammaticalRelation::Unspecified
        && effective_ctx.subtype.is_none()
        && matches!(
            second_nfc.as_str(),
            "ஐ" | "ஆல்" | "ஆன்" | "ஒடு" | "ஓடு" | "கு" | "இன்" | "ஆது"
        )
    {
        effective_ctx.relation = GrammaticalRelation::Vetrumai;
    }

    // Stage 1: Panpuppeyar (136) -> Closed-class (186-199, 247, named) -> Pre-elision Kurriyalugaram (183-185).
    let stage1_outputs = closed_class::apply_stage_1(&first_nfc, &second_nfc, &effective_ctx);

    let mut branches = Vec::new();
    for item in stage1_outputs {
        if item.finalized {
            let s = item.state;
            branches.push(Branch {
                surface: normalize_nfc(&s.left),
                steps: s.steps,
                required_context: s.required_context,
                optional_variant: s.optional_variant,
                poetic: s.poetic,
                priority_rank: s.priority_rank,
            });
            continue;
        }
        // Stage 2: Urupu & Chariyai staging -> multi-segment left-to-right fold (Stages 3A -> 4).
        let chains = urupu::apply_stage_2(item.state, &effective_ctx);
        for chain in chains {
            branches.extend(fold_chain(chain, &effective_ctx));
        }
    }

    finalize_branches(profile, branches)
}

/// Deduplicate branches by `(surface, rule_ids)`, sort canonically, and construct `PunarchiJoinResult`.
pub fn finalize_branches(
    profile: PunarchiProfile,
    mut branches: Vec<Branch>,
) -> Result<PunarchiJoinResult, PunarchiError> {
    branches.sort_by(|a, b| a.sort_key().cmp(&b.sort_key()));

    let mut seen: HashSet<(String, Vec<String>)> = HashSet::new();
    let mut unique: Vec<Branch> = Vec::with_capacity(branches.len());
    for branch in branches {
        let sig: Vec<String> = branch
            .rule_signature()
            .into_iter()
            .map(str::to_owned)
            .collect();
        if seen.insert((branch.surface.clone(), sig)) {
            unique.push(branch);
        }
    }

    let primary = unique.remove(0);
    let primary_transform = primary.primary_transform();
    let alternatives = unique
        .into_iter()
        .map(|b| {
            let transform = b.primary_transform();
            JoinAlternative {
                surface: b.surface,
                transform,
                steps: b.steps,
                required_context: b.required_context,
                optional_variant: b.optional_variant,
                poetic: b.poetic,
            }
        })
        .collect();

    Ok(PunarchiJoinResult {
        profile,
        surface: primary.surface,
        transform: primary_transform,
        steps: primary.steps,
        alternatives,
    })
}
