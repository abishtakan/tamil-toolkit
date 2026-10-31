# Declarative linguistic data

Only TOML, CSV, and documentation belong here. No executable code. Every future
word list, suffix table, encoding map, or sandhi rule needs provenance, licensing,
versioning, and explicit regional coverage before implementation.

`core.toml` contains Unicode vowel/consonant facts and the project's documented
Sri/KSHA atomic-letter tailoring. `tamil-core/build.rs` validates the table and
compiles it into static Rust lookup slices. Larger reviewed word lists should
compile to FST/trie bytes; this tiny fixed table does not need an FST dependency.

`collate.toml` declares the versioned Agara inventory and written Shri expansions.
`tamil-collate/build.rs` checks its normalization, uniqueness, and expansion
integrity and compiles a binary-search lookup table. Independent Unicode/CLDR
references and golden expectations live in tests/reference and tests/golden.

`numerals.toml` contains the bounded CLDR 49 spellout rule subset, grouping,
negative prefix, INR/LKR denomination labels, and the declared SL lakh-stem
override. Sources, Unicode licensing, and regional limits are recorded in
`docs/specs/numerals-v0.1.md`. Its build script validates rule references and
syntax and compiles static operations for both profiles. Frozen independent
ICU4J results test those operations; Java/ICU are not runtime dependencies.
