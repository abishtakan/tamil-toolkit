//! Build-time compiled static Nannool inventory, Chariyai, case-suffix, closed-class, and rule tables.

use serde::Serialize;

/// Auditable inventory record for one of the 117 Nannool Ezhuttatikaram sutras (`nannool-v1`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct SutraInventoryEntry {
    pub sutra: u16,
    pub chapter: &'static str,
    pub tier: &'static str,
    pub executable: bool,
    pub tva_page: u16,
    pub kandigai_sutra: u16,
    pub pm_ref: &'static str,
    pub summary: &'static str,
    pub edition_note: Option<&'static str>,
}

/// Declarative connecting increment (*Chariyai*, Nannool Sutra 244).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct ChariyaiDef {
    pub id: &'static str,
    pub form: &'static str,
    pub sutra: u16,
    pub attach_classes: &'static [&'static str],
    pub case_filter: &'static [&'static str],
    pub stack_after: &'static [&'static str],
    pub post_um: bool,
    pub suppress_205: bool,
}

/// Declarative oblique case suffix (*Vetrumai Urupu*, Nannool Sutras 240-242).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct CaseSuffixDef {
    pub case_number: u8,
    pub form: &'static str,
    pub sutra: u16,
    pub force_165: bool,
}

/// Mapping from a nominative closed-class stem to one or more oblique stems.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct ObliqueEntry {
    pub stem: &'static str,
    pub forms: &'static [&'static str],
}

/// Finite closed lexical class declared in `lexicon/punarchi-nannool.toml`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct ClosedClassDef {
    pub class_id: &'static str,
    pub sutra: u16,
    pub stems: &'static [&'static str],
    pub oblique_map: &'static [ObliqueEntry],
    pub notes: &'static str,
}

/// Declarative rule entry compiled from `lexicon/punarchi-nannool.toml`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct PunarchiRuleDef {
    pub id: &'static str,
    pub sutra: u16,
    pub chapter: &'static str,
    pub stage: u8,
    pub substage: &'static str,
    pub priority: u16,
    pub transform: &'static str,
    pub relation: &'static str,
    pub subtype: Option<&'static str>,
    pub lexical_class: Option<&'static str>,
    pub poetic: bool,
    pub optional: bool,
    pub reversible: bool,
    pub left_match: &'static str,
    pub right_match: &'static str,
    pub action: &'static str,
    pub flags: &'static [&'static str],
    pub evidence_layer: &'static str,
}

include!(concat!(env!("OUT_DIR"), "/punarchi_tables.rs"));

/// Look up an inventory entry by exact sutra number.
pub fn inventory_entry(sutra: u16) -> Option<&'static SutraInventoryEntry> {
    INVENTORY
        .binary_search_by_key(&sutra, |e| e.sutra)
        .ok()
        .map(|idx| &INVENTORY[idx])
}

/// Look up a closed-class definition by `class_id`.
pub fn closed_class(class_id: &str) -> Option<&'static ClosedClassDef> {
    CLOSED_CLASSES.iter().find(|c| c.class_id == class_id)
}

/// Check whether `stem` belongs to a named closed class.
pub fn in_closed_class(class_id: &str, stem: &str) -> bool {
    closed_class(class_id).is_some_and(|c| c.stems.contains(&stem))
}

/// Look up oblique stem forms for a stem in a named closed class.
pub fn oblique_forms(class_id: &str, stem: &str) -> Option<&'static [&'static str]> {
    closed_class(class_id).and_then(|c| {
        c.oblique_map
            .iter()
            .find(|entry| entry.stem == stem)
            .map(|entry| entry.forms)
    })
}

/// Look up an overt case suffix definition by NFC Tamil form (e.g., `ஐ`, `ஆல்`, `கு`, `இன்`, `அது`, `கண்`).
pub fn case_suffix_info(form: &str) -> Option<&'static CaseSuffixDef> {
    CASE_SUFFIXES.iter().find(|c| c.form == form)
}

/// Return true if `form` is one of the overt oblique case suffixes (`2..=7`).
pub fn is_overt_case_suffix(form: &str) -> bool {
    case_suffix_info(form).is_some()
}

/// Look up a declarative rule definition by `id`.
pub fn rule_by_id(id: &str) -> Option<&'static PunarchiRuleDef> {
    RULES.iter().find(|r| r.id == id)
}

/// Iterate over declarative rules linked to a specific sutra number.
pub fn rules_for_sutra(sutra: u16) -> impl Iterator<Item = &'static PunarchiRuleDef> {
    RULES.iter().filter(move |r| r.sutra == sutra)
}
