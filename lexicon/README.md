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

`numerals-formats.toml` supplies Unicode fraction symbols, common lexical names,
the division-reading label, CLDR date symbols/patterns, and decimal digit sets.
The format build helper validates these facts and compiles the required date
tokens and static lookup tables. Exact rational and Gregorian calendar behavior
remains in Rust; evidence is frozen under `tests/reference/numerals-v0.2`.

`bamini.toml` stores the pinned MIT-sourced `bamini-v1` mappings, explicit
ambiguity candidates, and pass-through characters. `tamil-codec/build.rs`
validates them and compiles static decoder/encoder tries. Its canonical alias
preference selects the primary source's first RA+VIRAMA spelling; other aliases
remain valid decoder inputs. Source/license files and independent
encoder evidence live under `tests/reference/codec-v0.1`. See the codec
specification for the five unsupported ambiguous forms and profile differences.
