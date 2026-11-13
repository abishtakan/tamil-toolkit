# Research: Professional Tamil Lexicon Curation

**Date**: 2026-11-13 | **Feature**: [spec.md](spec.md)

This records planning decisions, not implemented behavior or data approval. The
four clarification answers govern all decisions below. Source URLs/scripts,
source-specific reuse evidence, and linguistic adjudication remain external
acceptance dependencies with explicit quarantine outcomes; no design question
is left unresolved by their absence.

## 1. Separate intake, editorial workspace, and approved canonical packs

**Decision**: Preserve the 12 originals in `data/sources/tamil-lexicon/` and the
adjacent checksum inventory. Put source leads, import records, identity registry,
dispositions, proposed assertions, and editorial decisions in
`data/curation/tamil-lexicon/`. Promote only approved eligible projections to
`lexicon/dictionary/` through a checked promotion operation. Use CSV tables and
TOML metadata. Schemas may be JSON under `schemas/lexicon/`; no JSON, binary
indexes, or executable files go under `lexicon/`.

**Rationale**: Unknown source terms must not become canonical approved data.
L2 structural acceptance may contain only quarantine records. The current
Unicode gate permits only `.toml`, `.csv`, and `.md` under `lexicon/` and does
not yet decode CSV contents. Its CSV coverage must be extended, not assumed.

**Alternatives considered**: Editing the intake; treating the master CSV as a
second source of truth; moving the supplied FST into `lexicon/`; putting all
unreviewed content in canonical tables. Each obscures evidence or violates the
existing boundaries. SQLite and a web editor are unnecessary initial systems.

## 2. Stable identity and complete accounting

**Decision**: Allocate prefixed UUIDv5 IDs from a committed dataset namespace
and immutable source lineage/legacy keys for first import. Never seed entry IDs
from spelling, POS, ordering, or source row position. Persist the identity
registry; manual splits/new entities use explicit new allocation keys committed
before builds. Snapshot-specific record IDs may include the file digest and
logical CSV record ordinal because they identify evidence, not lexical identity.
Repeated import reconciles through the registry and existing dispositions.

**Rationale**: IDs survive spelling/POS corrections, while builds allocate no
random identities. A split/merge records explicit successor links and tombstones.
Every source row has exactly one disposition, with zero-to-many target mappings.
The 44,229 master rows are accounted against existing entries; additional
master-only assertions are retained as unreviewed evidence, not discarded.

**Alternatives considered**: Headword/POS hashes conflate homographs; sorting
based integers drift; generating fresh random IDs during each build defeats
reproducibility. Excluding every master field as duplication loses annotations.

## 3. Field-level claims and acceptance

**Decision**: Keep lexical structure separate from assertions, evidence links,
review decisions, and changes. Eligibility is derived by validation, never a
hand-editable `verified=true`. An unchanged, faithfully extracted assertion may
receive `accepted_auto_source` only with verified source fidelity, documented
reuse basis/attribution, passing validation, and no unresolved ambiguity.
`accepted_human` requires a named reviewer, date, decision, and evidence for a
correction, inference, or ambiguous interpretation. Both paths preserve origin.
Changing a claim invalidates its prior acceptance by revision hash.

**Rationale**: This implements clarification B while preserving unknown values.
Source verification is not an assertion that every source statement is true.
Human linguistic approval cannot establish reuse permission by itself.

**Alternatives considered**: Trusting the imported `verified`/`1.0`; accepting
inferred IPA because it is populated; requiring human adjudication to finish the
structural pilot. These conflict with the specification or clarified L2 gate.

## 4. Escaped Unicode and a single linguistic engine

**Decision**: Use an explicit `json-string-v1` codec for CSV free-text cells:
CSV parsing yields a JSON string literal, which is decoded exactly once using
a standard JSON parser. All non-ASCII characters and controls are escaped in
canonical files. Use `null` for unknown and a separately declared
`not_applicable` state rather than sentinel text. Preserve literal backslashes
through ordinary JSON escaping; reject lone surrogate escapes. Original text
may be non-NFC with a reasoned field-specific finding; accepted canonical
forms must be NFC through `tamil-norm`. Canonical-equivalence computation,
orthography inspection, and derived quantities call existing Rust operations.
Python orchestration performs file/schema/accounting work only.

**Rationale**: CSV quoting alone cannot express Unicode escapes. A declared
standard JSON cell codec is reversible and keeps Tamil/control scalars visible
in review without implementing a second Tamil engine. Pure packaging codecs
are serialization, not linguistic algorithms.

**Alternatives considered**: Raw Tamil in curated files; an ad hoc backslash
replacement; Python `unicodedata` as authoritative normalization; silently
stripping controls. The existing audit's Python normalization is diagnostic
only and does not certify the project Unicode version.

## 5. Rust ownership and offline pack compilation

**Decision**: Add future runtime lookup under `crates/tamil-toolkit/src/lexicon/`
and host validation/compilation helpers under the same existing crate. No new
crate, rank, or `tamil-morph` dependency. Build approved canonical projections
using a future `crates/tamil-toolkit/build.rs` and `build_lexicon.rs`, with
lower-ranked `tamil-norm`/`tamil-core` build dependencies as required. A sorted
FST maps NFC UTF-8 spelling to posting-list ordinal, never directly to one entry.
Posting lists contain every matching entry ID in stable bytewise ID order.

Use `fst` 0.4.7 with default features disabled, pinned by Cargo.lock, and the
`csv` crate 1.x for CSV decoding (lock the actual supported version during
implementation). Generated immutable metadata and posting offsets are embedded
without unsafe mmap. Builds must work from synced package-local data, offline,
without a source checkout or a network request. Hashes and revisions enter a
reproducible manifest; wall clocks, absolute paths, and random IDs do not.

**Rationale**: The facade already owns the shared dispatcher and is Rank 5.
Consumers in lower crates compile relevant approved data independently later;
they never depend on the facade. The [fst MapBuilder contract](https://docs.rs/fst/latest/fst/map/struct.MapBuilder.html)
requires sorted unique keys and stores a single integer per key, so a posting
list is necessary to retain all homographs.

**Alternatives considered**: A new lexicon crate/rank, importing the unknown
binary builder, runtime downloading, an FST mapping each spelling to its first
ID, or adding a morphology dependency to phonetics. These add unsupported scope
or break ownership/completeness.

Sorted static key/range tables are a valid simpler alternative for a tiny pilot.
The large target wordlist and the existing demonstrated FST intake scale justify
choosing one FST/posting format at L3 rather than maintaining two runtime index
formats. No FST implementation is needed to finish the structural L2 pilot.

## 6. Optional packs and exact lookup

**Decision**: Keep dataset features off by default. Plan additive opt-ins for
`lexicon-core`, `lexicon-terminology`, `lexicon-names-taxa`, and
`lexicon-regional`; expose the same selected pack profile through all bindings.
Reject requested absent packs rather than returning an empty word result.
NFC canonical equality is the only matching transformation. No trimming,
case-folding, variant expansion, repair, or removal of format controls occurs.
Region codes live in a documented registry separate from language tags.
Region filtering accepts explicit regional attestations and reviewed unrestricted
scope, excludes unknown scope, and prevents narrower contradictory senses from
leaking through entry-level tags. Register filtering uses explicit matches;
unknown register is excluded only when that filter is requested.

**Rationale**: This implements the clarified exact and regional semantics and
keeps dataset size out of default WASM builds. Cargo features are additive
([Cargo reference](https://doc.rust-lang.org/cargo/reference/features.html));
pack selection must tolerate feature unification and document loaded packs.

**Alternatives considered**: Shipping the 92.6 MB intake by default, treating
an uncompiled pack as a word not found, inheriting unknown regional coverage
as universal, or promising fuzzy/folded search in this feature.

## 7. Interchange and reproducibility

**Decision**: Generate a CLDF Dictionary export at L3/L4 from a nonempty eligible
subset, targeting the CLDF 1.3 schema release with pinned schema digests. Use
Entries, Senses, Examples, Languages, BibTeX sources, and documented
custom forms/relations/assertions/review extension tables. Preserve every curated
field needed for round-trip in extensions. Use CSVW JSON metadata in the output
folder, not JSON files in `lexicon/`; do not describe this as Frictionless schema.
Language IDs identify declared language/variety records; arbitrary region codes
are not passed off as registered language tags. Cite BibTeX sources with locators.
TEI Lex-0 is a future export, not a second editing format.

**Rationale**: The [official CLDF specification](https://github.com/cldf/cldf)
defines Dictionary and CSVW metadata, including source and reference semantics;
its [ontology](https://cldf.clld.org/v1.0/terms.html) distinguishes entry/sense
and example tables. [TEI Lex-0](https://lex-0.org/) provides a later dictionary
exchange target. Formal conformance requires an actual export validator run;
custom canonical tables are not called CLDF-conformant by implication.

**Alternatives considered**: A lossy single `Description` column with no language
or sense distinction; equating a source bibliography with a standard SourceTable;
maintaining parallel XML and CSV originals; declaring conformance before export.

## 8. Scale, performance targets, and release gates

**Decision**: Validate all 307,243 logical CSV records for inventory/accounting;
select the structural pilot deterministically from the full manifest and report
all FR-019 coverage classes. A source record can be quarantined with a valid
reason; unsupported linguistic annotations cannot pass as facts. L2 needs no
eligible entries. L3/L4 require nonempty approved subsets and source/review
closure before lexical support is claimed.

Planning targets: full structural inventory/validation under 60 seconds and
512 MiB peak memory on a documented Windows x64 reference machine; warmed
10,000-query exact lookup p95 under 10 ms for inputs up to 64 KiB, excluding
serialization of large results. Record result sizes, cold-start, memory, and
artifact size separately. These are unmeasured engineering targets, not current
performance guarantees. Default no-data builds must embed zero lexicon data
bytes. Opt-in pack byte counts and browser loading costs are measured at L3,
with any accepted budget change recorded rather than sacrificing completeness.

**Rationale**: Local deterministic lookup does not need hosting, uptime SLOs,
or a network service. Warm lookup targets cannot hide construction/startup or
unbounded response costs. Full post-edit/parity/archive gates apply at actual
integration, not to this documentation-only planning output.

**Alternatives considered**: Guessing packed sizes before source selection,
using a truncated result cap to meet timing targets, treating an all-quarantine
pilot as a passing runtime suite, or blocking unrelated phases on unavailable
source permissions after the user explicitly chose structural acceptance.
