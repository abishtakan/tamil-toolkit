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

**Storage**: Versioned CSV tables/TOML manifests and identity registry; escaped
JSON free-text cells with explicit missing-value states; no independently edited
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
| II. Scalar inspection | Intake remains immutable and audit limitations are explicit | Pass: escaped text codec, decoded CSV gate, reasoned field exceptions, Rust Unicode authority, preserved controls |
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
    packs.md
  checklists/requirements.md
```

`tasks.md` is intentionally not generated here; the next workflow is
`speckit-tasks`. Research and design are complete; implementation milestones
L1–L4 remain pending.

### Source Code (repository root)

The following are planned locations, not files created by this command:

```text
data/sources/tamil-lexicon/                 # unchanged intake exists today
data/sources/tamil-lexicon.sha256.json       # existing intake inventory
data/curation/tamil-lexicon/                # metadata, IDs, proposals, decisions
lexicon/dictionary/                         # L3-approved projections only
schemas/lexicon/                            # schemas outside lexicon/
tools/lexicon.py                            # host structural/curation entry point
tools/audit_lexicon_source.py                # existing diagnostic audit retained
tools/tasks.py                             # add structural CSV gate/profile checks
tools/release_files.py                     # explicit approved distribution mapping
crates/tamil-toolkit/
  build.rs
  build_lexicon.rs
  src/lexicon/mod.rs                        # safe lookup, metadata, errors
  src/lib.rs                               # existing facade/dispatcher registration
  src/bin/tamil-toolkit.rs                  # existing CLI routing
  lexicon/dictionary/                       # sync-generated package-local copies
  tests/lexicon.rs
bindings/python/                            # feature forwarding, wrapper, .pyi
bindings/js-wasm/                           # feature forwarding, typed Node/Web API
bindings/dart-flutter/                      # feature forwarding, C ABI wrappers
tests/harness/test_lexicon_data.py
tests/golden/lexicon_lookup.jsonl            # add sourced planned suite first
docs/specs/lexicon-v0.1.md                  # module behavior/fixtures contract
target/lexicon/                             # reports, staged exports, comparisons
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

- [data-model.md](data-model.md): logical tables, escaped cell codec, immutable
  identities, revisions, evidence, dispositions, scope and milestone transitions.
- [contracts/curation.md](contracts/curation.md): deterministic host commands,
  reports, errors, repeatable imports, structural acceptance and promotion rules.
- [contracts/lookup.md](contracts/lookup.md): exact dispatcher/CLI/wrapper shapes,
  pack availability, matching/filtering, ordering and errors.
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
