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


Large approved dictionary CSV tables use readable UTF-8 Tamil under the versioned
`json-string-utf8-v1` cell codec; JSON-required and audit-sensitive control escapes
remain reversible. Small rule tables and golden test vectors retain explicit
escapes. Compiled `.tlpack` runtime artifacts use a deterministic little-endian
binary format compiled into `OUT_DIR` by `crates/tamil-toolkit/build.rs` and
`build_lexicon.rs`, not UTF-8 CSV escapes or the untrusted intake FST. See
[the storage decision](../docs/decisions/lexicon-text-storage.md).

`lexicon/dictionary/` holds the canonical L3-approved `core` projection
(`dataset_version = 0.1.0+4d1309d05391`, `manifest_sha256 = 4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`)
built from the human-reviewed Wiktionary subset (`6` entries, `19` senses, `31`
accepted claims signed by `abish` on `2026-11-14`; two `நன்றி` POS entries
remain distinct). Structured scopes remain `unknown` (`2` pending scope
proposals), and no IPA, etymology, morphology, frequency, root, or DEDR claims
are included. These Wiktionary-derived records are licensed separately under
**CC-BY-SA-4.0** with required attribution and notices in
[ATTRIBUTION_AND_TERMS.md](dictionary/ATTRIBUTION_AND_TERMS.md),
[notices/ATTRIBUTION_AND_LICENSE.md](dictionary/notices/ATTRIBUTION_AND_LICENSE.md),
and [notices/CC-BY-SA-4.0.md](dictionary/notices/CC-BY-SA-4.0.md); engine/tooling
code retains its **MIT** license.

`just sync-release-files` copies selected canonical dictionary and schema files into
`crates/tamil-toolkit/lexicon/dictionary/` and `crates/tamil-toolkit/schemas/lexicon/`.
Default builds embed `0` payload bytes (`lexicon-*` features are off by default);
enabling `lexicon-core` compiles the verified `50,923`-byte `.tlpack` artifact
(SHA-256 `283e32d7b3dbfa11d1bedc201a95e90bcb064021dba96fd6a44a61491f5137ea`,
[l3-acceptance.json](../target/lexicon/l3-acceptance.json)), while Cargo source
archives still carry the packaged `lexicon/dictionary/` data and notices even
when dataset features are disabled. The historical 307,243-record intake under
`data/curation/tamil-lexicon/` remains quarantined (`0` eligible assertions;
[l2-acceptance.json](../target/lexicon/l2-acceptance.json)). Rust lookup and CLI
support, binding parity, benchmarks, final gates and isolated archives are
verified for the bounded core. The owner approved its 44-vector activation
on 2026-11-15.


## Verified consumer checkpoint — 2026-11-15

The six-entry / 19-sense core passes all 44 unchanged active lexicon vectors
in real Rust, Python, Node/browser WASM and Dart. Core/default isolated archives
and private Dart bundles pass with applicable terms. Final core gates pass
390 harness tests, 31 Python groups, 36,230 WASM tests and all required Rust,
Unicode, Clippy and release-copy checks. Evidence: `target/lexicon/` contains
`l4-functional.json`, `archive-proof.json` and `integration-gates.log`.

Fresh complete intake/proof verifies 307,243 records and 12 original hashes in
52.72 seconds at 191.93 MiB; both structural targets pass. Release core lookup
p95 is 0.1148 ms native / 0.1979 ms with Python serialization (10,000 queries
per pass). See `benchmarks.json`; no large-pack lookup scaling is claimed.
The owner approved core-profile activation of the 44 vectors on 2026-11-15.
Canonical verification uses core; Cargo default data features stay off. No registry
upload or version/allowlist expansion occurred. Historical source intake stays
quarantined; scopes remain unknown and omitted annotations stay excluded.
