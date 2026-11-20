# Implementation Plan: Professional Tamil Lexicon Curation

**Branch**: `master` (actual Git branch) | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Feature context**: `021-lexicon-curation` (the setup script's logical feature
identifier, not a Git branch switch). Input is the clarified feature specification.
Planning ends at design; this command does not create tasks or implement tooling.

## Summary

Preserve the supplied 92,616,773-byte bundle and build a traceable editorial
pipeline before introducing dictionary lookup. Inventory all 307,243 CSV records,
record stable identities/dispositions and per-assertion evidence, then validate
the representative structural pilot. L2 can pass with all content quarantined;
this permits Phase 6 scheduling but grants no source, linguistic, or runtime
approval. A later nonempty approved subset enables reproducible offline pack
compilation and exact NFC lookup through the existing Rust facade and adapters.

The design separates immutable `data/sources/`, editorial `data/curation/`,
reviewed canonical CSV/TOML in `lexicon/dictionary/`, and generated artifacts in
`target/`/Cargo `OUT_DIR`. It preserves every eligible homograph through posting
lists. No new crate, rank, web service, editor, morphology engine or public release
is introduced by this feature's curation work.

## Technical Context

**Language/Version**: Existing Rust 2021 workspace, MSRV 1.85; Python 3.11+
structural/orchestration tooling; existing TypeScript and Dart thin adapters.

**Primary Dependencies**: Reuse `tamil-core`, `tamil-norm`, `serde_json`, TOML and
existing Python `jsonschema`. Plan Rust `csv` 1.x plus `fst` 0.4.7 without default
features for approved-pack compilation/runtime; lock exact compatible resolutions
before implementation gates. Use a pinned dev-only CLDF validator at L3 export;
no additional service or database dependency. Native Rust handles all authoritative
Tamil normalization/inspection/counts; Python handles serialization and accounting.

**Storage**: Versioned CSV tables/TOML manifests and identity registry; readable UTF-8
JSON free-text cells (`json-string-utf8-v1`) with explicit missing-value states; no independently edited
SQLite/master/XML copy. Source rights/evidence may remain unknown in editorial
storage. Only approved eligible projections enter canonical distribution data.

**Testing**: Pytest structural/accounting and failure tests; Rust safe compiler/
lookup tests; sourced escaped JSONL before new linguistic behavior; shared Rust,
Python, Node/browser WASM and Dart parity at L4; deterministic build comparisons,
CLDF round-trip, feature-disabled errors, and isolated archive consumers.

**Target Platform**: Windows/Linux host tooling, standalone Rust, Python native
extensions, Node/browser WASM, and Dart host C ABI. All build/runtime data access
is offline and package-local; no website deployment or network lookup.

**Project Type**: Existing library/CLI workspace plus offline data tooling.

**Performance Goals**: Full structural processing target under 60 seconds and
512 MiB peak memory; 10,000-query warm exact lookup p95 under 10 ms for inputs
up to 65,536 UTF-8 bytes, excluding result serialization. Record cold start,
response size and end-to-end wrapper costs separately. These are unmeasured
engineering targets, not guarantees. Default builds embed zero dictionary bytes;
measure and approve each optional pack's size budget at L3 before distribution.

The structural benchmark covers all 307,243 CSV records and all 12 original file
hashes through inventory, staging and structural validation, using fresh output
directories. Measure per-stage and total wall time and peak process-tree resident
memory, including native work; record machine/OS/tool versions, input digests,
memory-sampling method and target comparisons. Exclude environment installation
and compilation, never silently exclude an executed processing stage. Measure
lookup separately. A pilot run cannot satisfy the full structural workload target.
Target misses are reported with evidence; they do not justify lost records,
truncated matches, or mislabeling an engineering target as a verified guarantee.

**Constraints**: Unchanged source hashes; stable lexical IDs; complete record
accounting; no unrequested text repair/folding; unknown region excluded only
when region-filtered; affirmative unrestricted evidence; human decisions for
corrections/inference/ambiguity; zero eligible data permitted at L2; no runtime
or packaging claim from an empty/all-quarantine pilot. No automatic publication.

**Scale/Scope**: 44,229 primary entries, 63,633 supplied meaning records, 19,849
relationships, 135,303 secondary records, and 44,229 overlapping master records.
The structural pilot selects at least 100 primary entries plus 20 from each of
seven secondary tables and every required issue class, adding linked rows and
all entries for at least 10 multi-entry spellings. Intake counts are not approved
vocabulary totals. Initial consumer scope is exact lookup, typed approved senses,
provenance and region/register filtering; search expansion is deferred.

## Constitution Check

*Pre-research design gate and post-design re-evaluation are recorded separately
from unrun implementation/activation/release gates.*

| Principle | Pre-research check | Post-design disposition |
|---|---|---|
| I. Single Rust linguistic engine | Existing dispatcher and lower-ranked norm/core are available | Pass: lookup in facade; Python has no replacement Tamil algorithms; future lower consumers compile approved data without depending upward |
| II. Scalar inspection | Intake remains immutable and audit limitations are explicit | Pass under Constitution 2.0.0: UTF-8 dictionary cell codec, escaped scalar/control diagnostics, decoded CSV gate, reasoned field exceptions, Rust Unicode authority, preserved controls |
| III. Goldens precede behavior | No new algorithm is being implemented | Pass at design: future module contract and sourced escaped planned suites precede runtime code; no activation claimed |
| IV. Data separate from code | Unreviewed bundle is outside canonical data | Pass: reviewed CSV/TOML projections only; indexes in OUT_DIR; scripts/schemas outside lexicon; no guessed Punarchi rules |
| V. Pluricentric coverage | TN/SL and unknown scope are explicit | Pass: reviewed geographic hierarchy separate from register/social labels; no inferred Batticaloa/Vanni/Up-Country coverage |
| VI. Naming and publication | No new package, version, registry action or allowlist change | Pass: existing facade and bindings; data/terms selection independently reviewed before archives; manual release policy retained |
| VII. Actual guarantees | L2 structural acceptance does not establish runtime support | Pass: milestone-specific reports, unmeasured performance targets, nonempty L3/L4 evidence and full future integration gates |

No constitutional waiver or rank change is required. Actual implementation must
run the required repository gates; this design check does not assert those future
gates passed. Missing external source/rights evidence is a quarantinable data
condition, not an unresolved design decision or reason to manufacture permission.

## Project Structure

### Documentation (this feature)

```text
specs/021-lexicon-curation/
  spec.md
  plan.md
  research.md
  data-model.md
  quickstart.md
  contracts/
    curation.md
    lookup.md
    lookup-response.schema.json
    lookup-response.example.json
    packs.md
  checklists/requirements.md
```

`tasks.md` tracks all 70 tasks through L1/L2 structural intake, reviewed L3
six-entry / 19-sense core, and bounded L4 runtime parity, performance and archives.
The owner approved core-profile fixture activation on 2026-11-15. Historical
merged-source bulk material remains quarantined; only the separately pinned and
reviewed core has release-eligible claims.

### Source Code (repository root)

Implemented L1–L4 runtime/profile paths and verification artifacts:

```text
data/sources/tamil-lexicon/                    # unchanged 12-file intake (verified, quarantined)
data/sources/tamil-lexicon.sha256.json          # existing intake inventory (verified)
data/curation/tamil-lexicon/                   # implemented L1/L2 UTF-8 workspace & 739-record selection (0 eligible)
data/curation/wiktionary-candidate/            # isolated 4-entry pinned Wiktionary candidate workspace
data/curation/wiktionary-homograph-candidate/  # isolated 1-page / 2-entry homograph candidate workspace
data/curation/wiktionary-core-reviewed/        # L3 human-reviewed 6-entry / 19-sense / 31-claim workspace
docs/reviews/wiktionary-core-approval-2026-11-14.json  # immutable human approval receipt (abish)
schemas/lexicon/                               # implemented JSON schemas + pinned CLDF 1.3 schema digests
tools/lexicon.py                               # implemented L1–L3 host CLI (inventory/stage/select-pilot/curate/review-ingest/pilot/validate/promote/export-cldf)
tools/audit_lexicon_source.py                  # existing diagnostic audit retained
tools/lexicon_wiktionary_candidate.py          # offline pinned-Wiktionary candidate & reviewed workspace builder/verifier
tools/tasks.py                                 # Unicode/schema gate + T061 --lexicon-profile orchestration
tools/release_files.py                         # implemented L3 explicit dictionary/schema/notice sync mapping
tools/release.py                               # T061 --lexicon-profile archive verification
tools/mcp-tamil-oracle/check_source_unicode.py # validates decoded curated CSV + findings/exceptions
target/lexicon/                                # L1–L3 proofs, focused runtime logs, and in-progress benchmark output
lexicon/dictionary/                            # L3 canonical core projection (0.1.0+4d1309d05391, separate CC-BY-SA-4.0)
crates/tamil-toolkit/
  build.rs                                     # implemented L3/L4 approved-pack build hook (OUT_DIR only)
  build_lexicon.rs                             # implemented L3/L4 safe FST/posting .tlpack compiler
  src/lexicon/mod.rs                           # implemented L4 safe exact NFC lookup, filtering, metadata, errors (allocates on NFC/decode)
  src/lexicon_pack.rs                          # implemented L3/L4 safe little-endian .tlpack container & profile metadata
  src/lib.rs                                   # implemented L4 dispatcher registration (lexicon_lookup/lexicon_packs)
  src/bin/tamil-toolkit.rs                     # implemented L4 CLI routing (lexicon lookup/packs)
  lexicon/dictionary/                          # sync-generated package-local copies (with notices)
  schemas/lexicon/                             # sync-generated package-local schemas
  tests/lexicon_pack.rs                        # implemented L3 compiler & 16-feature matrix tests
  tests/lexicon.rs                             # implemented focused Rust lookup/CLI tests (8 core / 7 default)
bindings/python/                               # feature forwarding + thin wrappers (real parity integration underway)
bindings/js-wasm/                              # feature forwarding + typed Node/Web wrappers (real parity integration underway)
bindings/dart-flutter/                         # feature forwarding + thin C ABI wrappers (real parity integration underway)
tests/harness/test_lexicon_*.py                # implemented L1–L3/runtime-contract harness tests
tests/golden/lexicon_lookup.jsonl              # 44 escaped L4 goldens (owner-activated for core in manifest.json)
docs/specs/lexicon-v0.1.md                     # L4 module contract (T044)
tools/lexicon_bench.py                         # implemented T063 structural & lookup benchmark runner (307,243-record run active)
```

**Structure Decision**: Keep runtime ownership in existing Rank-5 `tamil-toolkit`.
Its build script may depend on lower-ranked norm/core and external serializers;
it cannot depend on itself. No rank-2 phonetics to rank-3 morphology edge is added.
Approved data remains reusable by future crates through explicit build inputs.
`release_files.py` and Cargo inclusion must gain nested selected-file support;
their present flat TOML mapping does not already package this dataset.

## Phase 0 — Research outcome

[research.md](research.md) resolves storage, IDs, state transitions, Unicode,
compilation, pack defaults, interfaces, exchange and performance targeting.
Gemini 4 Hydrogen researched schema/editorial data; Sol (`gpt-6.1-sol`, `xhigh`)
researched repository ownership, contracts and packaging. Both were read-only.

Adopted their separation of milestone gates, assertion-level review and offline
packaging constraints. Corrected the distinction between CLDF CSVW metadata and
Frictionless schemas, and retained master-only claims rather than dropping the
entire overlapping master file. Chose FST posting lists for the target large
reviewed dataset; sorted static tables remain a simpler alternative recorded in
research, but no second index format is required for the first implementation.

## Phase 1 — Design outcome

- [data-model.md](data-model.md): logical tables, UTF-8 cell codec, immutable
  identities, revisions, evidence, dispositions, scope and milestone transitions.
- [contracts/curation.md](contracts/curation.md): deterministic host commands,
  reports, errors, repeatable imports, structural acceptance and promotion rules.
- [contracts/lookup.md](contracts/lookup.md): exact dispatcher/CLI/wrapper shapes,
  pack availability, matching/filtering, ordering and errors, with a complete
  [response schema](contracts/lookup-response.schema.json) and explicitly
  illustrative [matched example](contracts/lookup-response.example.json).
- [contracts/packs.md](contracts/packs.md): additive features, complete posting
  lists, offline manifests, archive/source terms and feature profiles.
- [quickstart.md](quickstart.md): existing audit command and clearly separated
  future structural, approval, runtime, interchange and packaging validation.

## Execution milestones and stop conditions

| Milestone | Deliverable and acceptance | Boundary |
|---|---|---|
| L1 | Implement schema/registries, inventory, stable IDs, disposition tooling, source leads and decoded CSV validation | Stop before declaring source/linguistic approval; all unknown evidence may stay pending |
| L2 | Commit deterministic representative selection, validate structural pilot/accounting, retain quarantines and record acceptance | May resume numerals even with zero eligible content; no lookup/CLDF release claim |
| L3 | Recover eligible evidence incrementally; accept claims under the clarified review policy; produce nonempty closed approved subsets and reproducible canonical/export/terms manifests | No source guess, automatic human approval, or silent loss; full-bundle accounting remains separately visible |
| L4 | Sourced module spec/goldens first; safe Rust compiler and exact lookup; CLI/thin bindings; shared profiles, real parity/Dart; isolated archives, explicit activation/release review | Cannot pass with empty packs, mocks, missing runtimes, skipped cases or unknown data rights |

Task generation should make L1/L2 independently executable and preserve L3/L4
acceptance as later gated work, rather than weakening it when evidence is absent.
Minimal initial tooling may store the logical review/link model in fewer physical
CSV files if schema/reference/round-trip semantics remain identical; do not build
a generic editorial platform or every future language tool.

## Validation and requirement traceability

| Specification outcomes | Main design and required proof |
|---|---|
| SC-001 / FR-001,005,012 | Source digests, identity registry and one disposition per input record; idempotent reimport and merge/split/reversal tests |
| SC-002 / FR-002,003,007 | Exact claim/evidence revision acceptance, auto/human distinction, source/terms closure and ineligible-claim rejection |
| SC-003 / FR-004,006,008–011,019 | Coverage-first pilot, schema/Unicode/reference findings, all-quarantine structural pass and separate release failure |
| SC-004 / FR-013,014,020 | All homographs, NFC equivalents, preserved controls, scope/register truth tables, exact ordering/errors across all runtimes |
| SC-005 / FR-015–017 | Optional pack closure, byte-for-byte build comparison, feature-disabled inventory/payload and standalone offline archives |
| SC-006 / FR-008–010,016 | Explicit issue-class policies, scalar/normalization exceptions, human correction/inference decisions, no silent text edits |
| SC-007 / FR-018,022 | Nonempty approved CLDF export, pinned validation and lossless extended round-trip; L2 cannot satisfy this milestone |
| SC-008 / FR-021,022 | Consistent L0–L4 roadmap/status, stable phase/rank rules and separate approval/activation/publication evidence |

During implementation use focused meaningful tests for identity/accounting,
review invalidation, exact matching and data eligibility. Run `just agent-post-edit`
for integration edits; L4 additionally requires `just agent-pre-stop-gate`,
`just test-dart`, release policy/files checks and `just release-check`. Rebuild
bindings before parity; serialize Dart and shared-native gate runs to avoid the
recorded Windows DLL-lock issue. Do not rerun full parity for this documentation-
only planning output or claim it was run. Capture actual results in the handoff.

## Complexity Tracking

No constitutional violations or exceptions. Added data/index dependencies and
logical review tables serve specific specification requirements. No new crate,
hosted service, database, workflow engine, UI, or general-purpose search layer is
needed. Keep folded/prefix/fuzzy search, inflection, phonetic synthesis, spellcheck,
and dialect transformation outside Feature 021's initial consumer scope.


## Storage revision — 2026-11-14

Applied the user-directed distinction documented in
[the storage decision](../../docs/decisions/lexicon-text-storage.md): readable
UTF-8 dictionary CSV (`json-string-utf8-v1`), escaped exact-character
tests/diagnostics, and separately measured compact runtime output. Uncommitted
legacy staging and temporary copies were deleted with no legacy archive retained.
The clean UTF-8 rebuild, exact decoded source-content equality
([source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json)),
pre-projection clean replay and equivalent-row byte measurement
([us1-proof.json](../../target/lexicon/us1-proof.json): `504,384,984` UTF-8 CSV
bytes vs `581,570,653` escaped baseline across `307,243` intake rows / `263,014`
initial identities), 739-record structural pilot
([l2-acceptance.json](../../target/lexicon/l2-acceptance.json),
[us2-proof.json](../../target/lexicon/us2-proof.json),
[structural-final.json](../../target/lexicon/structural-final.json)), fail-closed
release rejection ([release-rejection-final.json](../../target/lexicon/release-rejection-final.json)),
and full pre-stop gate ([pre-stop-utf8-final-retry.log](../../target/lexicon/pre-stop-utf8-final-retry.log))
have all passed.

## Implementation progress — 2026-11-15

- **L3 canonical & compiler acceptance**: Owner `abish` approved the
  six-entry / 19-sense Wiktionary core (`31` claims, packet SHA-256
  `0b2168d07e9b45b5316994c1d97648ebf5de3ad666de050b10afbe5dfa58695b`) on
  `2026-11-14` under separate **CC-BY-SA-4.0** data terms while toolkit engine
  code stays **MIT**. `lexicon/dictionary/` (`0.1.0+4d1309d05391`, canonical
  manifest SHA-256 `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`),
  offline CLDF 1.3 export/round-trip (`dbc9cd09b2c4d267f09ef25493656c7b99d25005614a2a326b632519d75dc54b`),
  all 16 feature combinations, `0`-byte default payload, and deterministic
  `50,923`-byte core `.tlpack` compilation (SHA-256
  `283e32d7b3dbfa11d1bedc201a95e90bcb064021dba96fd6a44a61491f5137ea`) are
  recorded in [l3-acceptance.json](../../target/lexicon/l3-acceptance.json).
  Structured scopes remain `unknown` (`2` pending proposals), no IPA/etymology/
  morphology/DEDR claims are approved, and historical `data/curation/tamil-lexicon/`
  remains quarantined.
- **L4 runtime verified**: `build_lexicon.rs`, `src/lexicon_pack.rs`,
  `src/lexicon/mod.rs` (allocating on NFC query normalization and payload
  deserialization; no zero-allocation claim), `src/lib.rs`, and
  `src/bin/tamil-toolkit.rs` pass `8` focused `core` Rust tests (including all
  `44` unchanged **active** goldens in `tests/golden/lexicon_lookup.jsonl`),
  `7` focused `default` tests, and `core` `clippy -D warnings`
  ([runtime-core-root.log](../../target/lexicon/runtime-core-root.log),
  [runtime-default-root.log](../../target/lexicon/runtime-default-root.log),
  [runtime-clippy-root.log](../../target/lexicon/runtime-clippy-root.log)).
- **Acceptance**: Real Rust/Python/Node/browser/Dart parity, full structural and
  lookup benchmarks, final gates and isolated archives pass for the bounded core.
  The owner approved its 44-vector activation on 2026-11-15. No publication or
  historical source-rights approval follows from this checkpoint.

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
