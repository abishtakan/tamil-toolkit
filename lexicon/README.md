# Declarative linguistic data

Only TOML, CSV, and documentation belong here. No executable code. Every future
word list, suffix table, encoding map, or sandhi rule needs provenance, licensing,
versioning, and explicit regional coverage before implementation.

This directory is canonical. `just sync-release-files` generates checked copies
inside each public crate's `lexicon/` directory so standalone Cargo builds need
no files outside their archives. Never edit those copies. `just check-unicode`
also checks their exact bytes. Run the sync command after canonical data edits.

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

`lt_tm.toml` stores a normalized projection of the documented Azhagi+ Portable
LT-TM mapping configuration as 16-bit code sequences. The source digest, terms,
and bounded profile scope are recorded in `docs/specs/codec-lt-tm.md`.
`tamil-codec/build.rs` validates its 332 keys and unique NFC values before
compiling static CID and reverse-Unicode tries. It does not make every
LT-TM/IndoWord font or Vanavil variant equivalent.

`vanavil.toml` stores a normalized projection of the documented Azhagi+ Portable
Vanavil (`Vanavil Avvaiyar`) mapping configuration as 16-bit code sequences,
cross-checked against `Vanavilavvai.ttf`. The source digest, terms, `0x00C0..0x00CF`
↔ `0x00E0..0x00EF` block transposition against LT-TM, and bounded profile scope
are recorded in `docs/specs/codec-vanavil.md`. `tamil-codec/build.rs` validates
its 319 keys and unique NFC values before compiling static code and
reverse-Unicode tries.
