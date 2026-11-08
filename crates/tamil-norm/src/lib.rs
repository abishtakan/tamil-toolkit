//! Canonical normalization, orthographic text repair, and lossy search folding for Tamil.
#![forbid(unsafe_code)]

pub mod folding;
pub mod repair;
pub mod types;

// Re-export canonical Unicode normalization from tamil-core
pub use tamil_core::{normalize_nfc, normalize_nfd};

// Re-export types
pub use types::{FoldingProfile, RepairDiagnostics, RepairOptions, RepairResult};

// Re-export engines
pub use folding::fold_for_search;
pub use repair::repair_tamil_text;
