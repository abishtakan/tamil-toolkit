//! Data models and option types for Tamil normalization, repair, and folding.
#![forbid(unsafe_code)]

use serde::{Deserialize, Serialize};

/// Configuration options for opt-in orthographic text repair.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepairOptions {
    /// Collapse contiguous duplicate viramas/pullis (e.g. `க்்` -> `க்`). Default: true.
    pub collapse_duplicate_pulli: bool,
    /// Reorder visual/legacy left-side kombus placed before consonants (e.g. `ெக` -> `கெ`). Default: true.
    pub reorder_visual_kombu: bool,
    /// Strip soft-hyphens (U+00AD) and non-printable control characters. Default: true.
    pub strip_soft_hyphens: bool,
    /// Strip Zero-Width Joiner (ZWJ, U+200D) and Zero-Width Non-Joiner (ZWNJ, U+200C). Default: false.
    pub strip_joiners: bool,
}

impl Default for RepairOptions {
    fn default() -> Self {
        Self {
            collapse_duplicate_pulli: true,
            reorder_visual_kombu: true,
            strip_soft_hyphens: true,
            strip_joiners: false,
        }
    }
}

/// Telemetry metrics on repairs performed during normalization.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct RepairDiagnostics {
    /// Number of duplicate pulli occurrences collapsed.
    pub duplicate_pulli_count: usize,
    /// Number of visual left kombus reordered to proper consonant-vowel composite positions.
    pub visual_kombu_count: usize,
    /// Number of soft-hyphens, control characters, and (if enabled) joiners stripped.
    pub stripped_control_count: usize,
    /// Grand total of all repairs applied.
    pub total_repairs: usize,
}

/// The outcome of an orthographic repair operation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RepairResult {
    /// The repaired, normalized text.
    pub text: String,
    /// Detailed diagnostic counts.
    pub diagnostics: RepairDiagnostics,
}

/// Lossy search-folding profile selector.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FoldingProfile {
    /// Folds Mayangoli confusion sets: ல/ள/ழ -> ல; ன/ண -> ன; ர/ற -> ர.
    Mayangoli,
    /// Folds Grantha consonants to native equivalents: ஸ/ஷ -> ச; ஜ -> ச; ஹ -> க; க்ஷ -> ச.
    Grantha,
    /// Combines Mayangoli + Grantha folding, lowercases ASCII text, and normalizes whitespace.
    Comprehensive,
}

impl FoldingProfile {
    /// Parse profile from string name.
    pub fn parse(s: &str) -> Option<Self> {
        match s.to_ascii_lowercase().as_str() {
            "mayangoli" => Some(Self::Mayangoli),
            "grantha" => Some(Self::Grantha),
            "comprehensive" => Some(Self::Comprehensive),
            _ => None,
        }
    }
}
