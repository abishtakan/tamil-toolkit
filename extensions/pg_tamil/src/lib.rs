//! PostgreSQL integration scaffold. No full-text-search dictionary exists yet.
pgrx::pg_module_magic!();

// Add only thin pg_extern wrappers after PostgreSQL-specific vectors exist.
// All normalization and morphology must delegate into tamil-norm/tamil-morph.
