//! Sourced Nannool Ezhuttatikaram Sandhi (`tamil-punarchi`).
//!
//! Accounts for all 117 sutras (`93-94`, `102-108`, `136`, `151-257`) under the
//! `nannool-v1` classical literary profile with zero runtime dictionary dependencies.
#![forbid(unsafe_code)]

pub mod closed_class;
pub mod context;
pub mod meyyeeru;
pub mod phonology;
pub mod pipeline;
pub mod split;
pub mod tables;
pub mod urupu;
pub mod uyireeru;

pub use context::{
    AlterationKind, ContextSubtype, DerivationStep, GrammaticalRelation, JoinAlternative,
    LexicalClass, PunarchiChapter, PunarchiContext, PunarchiError, PunarchiJoinResult,
    PunarchiProfile, SplitCandidate, MAX_SPLIT_SURFACE_BYTES,
};
pub use phonology::{
    classify_ugaram, has_boundary_barrier, is_kurriyaligaram_context, is_thanikkuril_otru,
    is_valid_mozhi_eetru, is_valid_mozhi_muthal, UgaramClass,
};
pub use pipeline::{punarchi_join, punarchi_rules, punarchi_rules_filtered};
pub use split::punarchi_split_candidates;
pub use tables::{
    CaseSuffixDef, ChariyaiDef, ClosedClassDef, ObliqueEntry, PunarchiRuleDef, SutraInventoryEntry,
};
