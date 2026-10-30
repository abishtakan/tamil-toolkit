# Declarative linguistic data

Only TOML, CSV, and documentation belong here. No executable code. Every future
word list, suffix table, encoding map, or sandhi rule needs provenance, licensing,
versioning, and explicit regional coverage before implementation.

`core.toml` contains Unicode vowel/consonant facts and the project's documented
Sri/KSHA atomic-letter tailoring. `tamil-core/build.rs` validates the table and
compiles it into static Rust lookup slices. Larger reviewed word lists should
compile to FST/trie bytes; this tiny fixed table does not need an FST dependency.
