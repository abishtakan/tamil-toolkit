---
description: "Dependency-ordered implementation tasks for professional Tamil lexicon curation"
---

# Tasks: Professional Tamil Lexicon Curation

**Input**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts](contracts/), and [quickstart.md](quickstart.md).

**Tests**: Included because FR-020, SC-001–SC-007, the contracts, and the project
constitution explicitly require source-backed acceptance, regression proof,
reproducibility and real runtime parity. Write meaningful failure cases before
their implementation; source-backed escaped goldens precede lookup algorithms. Large dictionary CSV
uses readable UTF-8 under the user-directed 2026-11-14 storage decision; exact
scalar/control diagnostics remain escaped. The clean UTF-8 rebuild and affected proof gates
are required before reporting L2 acceptance.

**Organization**: Setup → foundation → US1 (P1) → US2 (P1) → US4 (P2) → US3 (P2)
→ integration. US4 precedes equally prioritized US3 because approved packs are
inputs to lookup. Tasks T001–T049 are verified and checked `[X]`, including
source/review closure for the six-entry fresh Wiktionary subset and compiled
L3 acceptance. T050–T069 are verified, including real runtime parity, full-corpus performance,
archives and owner-approved core-profile activation. T070 final affected checks and handoff are complete. Historical merged-source rights and lineage remain unverified.

## Format: `[ID] [P?] [Story] Description`

- Every task has a sequential ID, exact repository-relative file paths, and a
  story label in story phases. `[P]` identifies independent files within the
  explicitly named execution wave; it does not bypass earlier prerequisites.
- All data-model field names, required-field markers, enum values, cardinalities,
  and null/reference constraints are normative. The schema tasks below copy
  those contracts without inferring linguistic facts from imported categories.
- Source files under `data/sources/tamil-lexicon/` are immutable. No task may
  weaken another task's fixtures, fabricate human review, silently skip missing
  runtimes, or publish packages. Source recovery and actual reviewer decisions
  are external inputs to gated tasks, not reasons to block the structural pilot.

## Phase 1: Setup — Preserve the baseline

**Purpose**: Establish safe working locations and the exact intake inventory.

- [X] T001 Verify the 12 original files against `data/sources/tamil-lexicon.sha256.json`, confirm 307,243 logical CSV records across 11 CSVs against `docs/audits/lexicon-2026-11-13.metrics.json`, and record baseline digests/counts in `target/lexicon/baseline.json` without rewriting sources.
- [X] T002 Define the dataset namespace, schema/codec versions, immutable allocation-key rules, and editorial/approved/generated boundaries in `data/curation/tamil-lexicon/dataset.toml` and `data/curation/tamil-lexicon/README.md`; do not create a new crate, canonical wordlist, or source approval.
- [X] T003 [P] Define shared scalar, ID, digest, JSON-cell, enum, null and foreign-key schema primitives in `schemas/lexicon/common.schema.json`; encode `value_state = known | unknown | not_applicable`, require JSON null for the latter two, and enforce “A known empty string is distinct from null but is forbidden for headwords, definitions, IDs, and required locators.”

## Phase 2: Foundational — Table contracts and shared tooling

**Purpose**: Complete these shared prerequisites before the story implementations.

- [X] T004 [P] Define snapshot/source/identity/accounting row schemas in `schemas/lexicon/intake.schema.json`, copying all fields from `data-model.md`; enforce “exactly the 12 intake files in this snapshot”, “unique `(snapshot_id, ordinal)`”, “one-to-one source record”, “unique triple”, “Mapped/merged need at least one target; split needs at least two”, and no approved target mappings for excluded/quarantined records.
- [X] T005 [P] Define lexical row schemas in `schemas/lexicon/lexical.schema.json` for entries/forms/senses/texts/relations; enforce “active approved entry requires a canonical written form and at least one accepted sense”, “exactly one approved canonical written form per entry”, representation `written`, `romanization`, `ipa`, role `canonical`, `variant`, and “parent must belong to the same entry and hierarchy must be acyclic”; retain required IDs and typed nullable references exactly as designed.
- [X] T006 [P] Define assertion/evidence/decision/change/successor/finding/exception/label/scope/pack-member schemas in `schemas/lexicon/review.schema.json`; copy complete fields/enums from `data-model.md`, including “at least one verified supporting source for a public claim”, “accepted decisions cannot be transferred to changed revisions”, “unused/stale exceptions fail”, and scope state `attested`, `unrestricted`, `unknown` with affirmative evidence for unrestricted status.
- [X] T007 [P] Add structural fixtures and failing codec/path/report tests in `tests/harness/test_lexicon_foundation.py` and `tests/reference/lexicon/structural/`, covering literal backslashes, escaped controls, valid supplementary scalars, lone-surrogate rejection, known-empty versus unknown/not-applicable values, deterministic ordering and output/source overlap rejection; fixtures must not impersonate approved linguistic data.
- [X] T008 Implement shared CSV/JSON/TOML parsing, fixed headers, “UTF-8 without BOM”, “LF endings”, bytewise primary-ID sorting, exact-once `json-string-utf8-v1` decoding and clean regeneration after user-authorized deletion of uncommitted legacy staging (exact decoded field/inner-row/scalar equality to frozen originals, stable IDs/locators/source hashes, pending new claim revisions and equivalent-row byte measurements; retain no legacy payload archive), schema validation and safe atomic output handling in `tools/lexicon.py`; preserve prior valid outputs on failure and reject conflicting human edits rather than overwriting them.
- [X] T009 Implement the native Rust inspection bridge and common CLI/report/error plumbing in `tools/lexicon.py` using the existing Python dispatcher; require a rebuilt adapter for authoritative normalization/orthography/counts, never fall back to Python Tamil algorithms, and preserve contract exit codes 0/1/2 and independent L2/L3/runtime indicators from `contracts/curation.md`.

**Checkpoint**: Common schemas/codecs and tooling exist; no source or linguistic
approval is implied. T004–T007 are independent after T003, before T008.

## Phase 3: US1 — Trace and assess imported material (Priority: P1, MVP)

**Goal**: A maintainer can inventory every original record, keep source leads and
unknown evidence visible, and reimport without changing identities or sources.

**Independent Test**: Run inventory/staging twice, compare IDs and bytes, verify
12 unchanged hashes and complete record dispositions; missing source evidence
stays unknown. This does not require public packs or completion of US2–US4.

### Tests first

- [X] T010 [P] [US1] Add failing inventory/tamper/quoted-multiline/record-accounting tests in `tests/harness/test_lexicon_inventory.py`; require original hash failure before staging and file-level disposition for the supplied FST, without changing real source files.
- [X] T011 [P] [US1] Add failing repeat-import/identity tests in `tests/harness/test_lexicon_identity.py`; require IDs independent of spelling, POS and row order, preserve same-spelling/same-POS identities, reject allocation conflicts, and retain existing identities when a snapshot changes.

### Implementation

- [X] T012 [US1] Implement `inventory` in `tools/lexicon.py` to produce snapshot and source-record inventories with SHA-256, logical ordinals, physical line spans, legacy keys and row digests; include all 307,243 CSV records and treat the supplied `.fst` as an untrusted derived artifact rather than a lexical source.
- [X] T013 [US1] Implement source-lead registration and separate source-fidelity/reuse/attribution states in `tools/lexicon.py` and `data/curation/tamil-lexicon/sources.csv`; record supplied labels as unknown leads and owner-reported Python extraction without inventing URLs, licenses, dates, scripts, or verified origins.
- [X] T014 [US1] Implement prefixed UUIDv5 allocation and persisted lineage/legacy-key reconciliation in `tools/lexicon.py` and `data/curation/tamil-lexicon/identities.csv`; enforce “The allocation key must not include spelling, POS, row order, or filename version” and retain explicit committed allocation keys for later splits/new identities.
- [X] T015 [US1] Implement idempotent `stage` and exactly-one-disposition accounting in `tools/lexicon.py` for `data/curation/tamil-lexicon/source_records.csv`, `dispositions.csv`, and `record_targets.csv`; unresolved records may all be quarantined, proposed claims retain evidence links, and no source row silently disappears.
- [X] T016 [US1] Reconcile the overlapping master export into existing identities in `tools/lexicon.py`; record all 44,229 master-row dispositions while preserving additional master-only claims as pending evidence, avoiding both duplicate entries and wholesale loss of annotations in `data/curation/tamil-lexicon/assertions.csv`.
- [X] T017 [US1] Complete inventory/stage reports and negative diagnostics in `tools/lexicon.py`, including deterministic findings, exact command/mode/input digests and separate acceptance indicators; diagnostics reference locators and do not expose unreviewed full text in public manifests.
- [X] T018 [US1] Run US1 focused tests and two clean inventories/stages, verify original hashes, and record actual totals, idempotence evidence and unresolved-source leads in `docs/status.md` and `target/lexicon/us1-proof.json`; do not claim pilot, linguistic, or runtime acceptance.

**Checkpoint / MVP**: US1 provides useful complete intake traceability even with
unknown rights. It does not itself satisfy L2's representative structural review.

## Phase 4: US2 — Curate without losing linguistic distinctions (Priority: P1)

**Goal**: Represent proposed lexical structure, evidence, revisions and review
decisions without fabricating approval. Preserve unresolved material and support
source-backed human corrections later; actual eligible data is not required here.

**Independent Test**: Use structural fixtures and selected source records to
demonstrate reversible changes, complete source mappings, stale-review rejection,
unknown values, unparsed content, and auto-versus-human review separation.

### Tests first

- [X] T019 [P] [US2] Add failing entity/sense/relation/missing-value/Unicode-exception tests in `tests/harness/test_lexicon_curation.py`, including canonical form cardinality, cyclic/wrong-entry sense parents, ambiguous targets, stale exceptions and forbidden coercion of unknowns into facts.
- [X] T020 [P] [US2] Add failing review/revision/merge/split/reversal tests in `tests/harness/test_lexicon_review.py`; changed, inferred, derived or ambiguous claims cannot auto-pass, human approval cannot waive unknown reuse evidence, and changed value/evidence hashes invalidate prior decisions.

### Implementation

- [X] T021 [US2] Implement entry/form/sense/text projection and validation in `tools/lexicon.py` using `schemas/lexicon/lexical.schema.json`; keep homographic identities distinct, unknown optional fields explicit, and proposed data under `data/curation/tamil-lexicon/`, never under approved canonical data.
- [X] T022 [US2] Implement reviewable component/sense extraction proposals in `tools/lexicon.py` and `data/curation/tamil-lexicon/texts.csv`, preserving original bilingual/numbered dictionary passages, typed definitions/glosses/translations/examples/citations, and `unparsed` states instead of blind punctuation splitting or generated definitions.
- [X] T023 [US2] Implement typed entry/sense relation proposals, directionality/inverse checks and ambiguous-target queues in `tools/lexicon.py` and `data/curation/tamil-lexicon/relations.csv`; imported target IDs are evidence to inspect, not authority to choose a sense by spelling.
- [X] T024 [US2] Implement versioned grammar/domain/register/social/period/region labels and explicit scope records in `tools/lexicon.py`, `data/curation/tamil-lexicon/labels.csv`, and `scopes.csv`; preserve separate language IDs, reviewed geographic parent relationships, and unknown coverage for undocumented TN/SL varieties without inventing equivalence.
- [X] T025 [US2] Implement immutable claim revisions, compensating editorial reversals, explicit merge/split successors and tombstones in `tools/lexicon.py`, `data/curation/tamil-lexicon/changes.csv`, and `successors.csv`; enforce “IDs are never recycled” and prevent acceptance from carrying over to changed values/conventions/evidence.
- [X] T026 [US2] Implement assertion-level evidence and decision ingestion/validation in `tools/lexicon.py`, `data/curation/tamil-lexicon/evidence.csv`, and `decisions.csv`; preserve imported status/confidence as source assertions and require actual actor/method, date, evidence-bundle hash and exact assertion revision for decisions.
- [X] T027 [US2] Implement computed eligibility in `tools/lexicon.py`: only unchanged, faithfully source-verified, unambiguous claims with passed reuse/attribution/validation may use `accepted_auto_source`; corrections/inferences/derived annotations/ambiguity require `accepted_human`, and unknown evidence remains quarantined rather than an editable eligible boolean.
- [X] T028 [US2] Implement decoded-cell Unicode/scalar/orthography findings and exact revision-scoped exceptions in `tools/lexicon.py` and `data/curation/tamil-lexicon/unicode_exceptions.csv`; use native Rust for authoritative checks, preserve ZWJ/ZWNJ and original non-NFC text, and reject invalid/stale/unused exceptions without silently repairing input.
- [X] T029 [US2] Document and exercise explicit source/decision ingestion, reviewer identity, correction evidence and revision invalidation in `data/curation/tamil-lexicon/README.md`; demonstrate pending and rejection paths without fabricating a human decision or treating a source label as verified provenance.
- [X] T030 [US2] Queue and preserve imported IPA, roots, verb classes, frequency tiers, Punarchi prose and count-convention discrepancies in `tools/lexicon.py` and `data/curation/tamil-lexicon/findings.csv`; compute diagnostics via existing Rust calls and retain methods/versions without declaring unsupported annotations valid.
- [X] T031 [US2] Wire decoded curated CSV validation into `tools/tasks.py` and `tools/mcp-tamil-oracle/check_source_unicode.py` without blanket-rejecting the intentionally frozen raw bundle or weakening current source/JSONL gates; report field-specific canonical-data exceptions and unknown schema failures explicitly.
- [X] T032 [US2] Run US2 focused tests, reversible-edit/reimport checks and Unicode gate regression coverage, then record implemented curation/review behavior in `docs/status.md` and `target/lexicon/us2-proof.json`; actual source/reuse/human decisions remain pending unless evidence was genuinely supplied.

**Checkpoint**: Editorial structure and review logic work with pending/quarantined
claims. US2 does not require or imply nonempty release-eligible content.

## Phase 5: US4 — Maintain a reproducible lexicon release (Priority: P2)

**Goal**: First finish the independent structural pilot, then produce reproducible,
nonempty approved packs and lossless interchange when evidence permits.

**Independent Test**: An all-quarantine representative pilot passes structural
mode and fails release/export modes. With an actual approved subset, repeat
promotion/compilation/export byte-for-byte and reject broken references or stale
approval. The latter proof can run without US3's public lookup interface.

### Tests first

- [X] T033 [P] [US4] Add failing sampling/accounting/structural-acceptance tests in `tests/harness/test_lexicon_pilot.py`, asserting every FR-019 minimum and that zero eligible entries may pass L2 while missing dispositions or unresolved blocking accounting errors fail it.
- [X] T034 [P] [US4] Add failing L2 fail-closed release-guard tests in `tests/harness/test_lexicon_packs.py`, requiring an all-quarantine/zero-eligible workspace to return release validation exit 1 with a nonempty-pack/eligibility finding, not an unsupported-command or missing-tool error. Do not add later promotion, pack-compilation, or CLDF round-trip tests until the corresponding L3 implementation tasks.

### Structural pilot — executable before source recovery

- [X] T035 [US4] Implement deterministic coverage-first pilot selection/checking in `tools/lexicon.py` and `data/curation/tamil-lexicon/pilot-selection.toml`: at least 100 primary entries, 20 records per seven secondary CSVs, 10 multi-entry spellings with all associated entries, 10 verbs, 10 mixed-sense records, 10 technical MWEs, 10 regional records spanning TN/Jaffna, and every observed Unicode/count-discrepancy class; retain linked evidence and do not replace an existing selection silently.
- [X] T036 [US4] Implement `pilot`, `validate --mode structural`, and the early fail-closed `validate --mode release` guard in `tools/lexicon.py`: validate all selected dispositions/findings/references and report L2 independently; reuse computed eligibility to reject zero-eligible/quarantined release candidates with exit 1 and explicit findings, never grant positive release acceptance at this stage. L2 permits zero eligible assertions; full-bundle claims require all 307,243 CSV dispositions and the FST file disposition.
- [X] T037 [US4] Execute and verify the actual representative pilot, all-quarantine acceptance/release-rejection contrast, original hashes, repeatability and focused tests; run `just agent-post-edit` and `just agent-pre-stop-gate`, and record L2 acceptance or exact remaining failures in `docs/status.md` and `target/lexicon/l2-acceptance.json`. Numerals may resume after this accepted structural checkpoint even with no eligible lexical content.

**L2 checkpoint**: T001–T037 are the implemented structural slice and are verified complete (`l2_structural_accepted: true`, `eligible_assertions: 0`, `l3_pack_eligible: false`, `runtime_verified: null`; evidence in `../../target/lexicon/l2-acceptance.json` and `../../target/lexicon/pre-stop-utf8-final-retry.log`). Every test through T037 passes; positive release, promotion, compiled-pack and CLDF tests are introduced only alongside T040/T041/T043/T048, with no skip/xfail workaround. L2 unblocks Phase 6 numerals scheduling, but is not a completed Feature 021 or a runtime/dataset release approval.

### L3 approval and pack production — externally gated

- [X] T038 [US4] Recover and verify exact source locations/editions/snapshots, extraction versions and reuse/attribution evidence for a candidate nonempty subset in `data/curation/tamil-lexicon/sources.csv` and `evidence.csv`; if evidence is unavailable, record the blocking locators/reasons in `docs/status.md`, keep affected material quarantined and leave this task pending rather than inventing permission.
- [X] T039 [US4] Apply only actual source-verification/automated-acceptance decisions and genuine human decisions required for corrections/inferences/ambiguity in `data/curation/tamil-lexicon/decisions.csv`; assemble a nonempty approved candidate including real homograph cases in `pack_members.csv`. Missing decisions remain explicit L3/L4 blockers and cannot be substituted with structural fixtures.
- [X] T040 [US4] First add failing release-eligibility/reference-closure tests in `tests/harness/test_lexicon_packs.py`, then complete `validate --mode release` in `tools/lexicon.py` with nonempty-pack checks, exact revision/evidence review validity, source/terms/attribution closure, canonical-form-plus-accepted-sense requirements, scoped optional annotation exclusion and explicit cross-pack relation omission policies; retain the passing L2 rejection guard and reject ineligible claims despite an eligible headword.
- [X] T041 [US4] First add failing promotion/idempotence/conflicting-edit tests in `tests/harness/test_lexicon_packs.py`, then implement deterministic `promote` staging in `tools/lexicon.py`, generating eligible table/metadata/source-terms projections into `target/lexicon/core-canonical/` without modifying intake, auto-approving humans, uploading anything, or silently overwriting canonical/human edits.
- [X] T042 [US4] Select and pin the dev-only CLDF validator and locally available CLDF 1.3 schema digests through `pyproject.toml`, `uv.lock`, and `schemas/lexicon/cldf/`; ensure ordinary Cargo builds never require Python, remote schemas, or network access.
- [X] T043 [US4] First add failing CLDF/extended-round-trip and tampered-decision tests in `tests/harness/test_lexicon_packs.py`, then implement `export-cldf --check` in `tools/lexicon.py`, generating CSVW metadata/BibTeX and standard plus custom tables under `target/lexicon/cldf/`; retain identity, language/type distinctions, scope, accepted evidence/decisions and controls, and never accept external exported review labels as authority.
- [X] T044 [US4] After actual L3 candidate approval, integrate only its reviewed projections and applicable terms into `lexicon/dictionary/`; write `docs/specs/lexicon-v0.1.md` and source-backed escaped `tests/golden/lexicon_lookup.jsonl` expectations, validate successful expected response payloads against `specs/021-lexicon-curation/contracts/lookup-response.schema.json`, extend `tests/golden/schema.json`, and register the suite as planned in `tests/golden/manifest.json` before compiler/lookup implementation. All-quarantine L2 cannot satisfy this task or justify fixture activation.
- [X] T045 [US4] Add optional `lexicon-core`, `lexicon-terminology`, `lexicon-names-taxa`, and `lexicon-regional` features plus locked compatible CSV/FST/serialization and lower-ranked core/norm build dependencies in `crates/tamil-toolkit/Cargo.toml` and `Cargo.lock`; keep dataset features off by default, Rust MSRV 1.85, existing ranks, package/version policy, and no new crate.
- [X] T046 [US4] Implement safe offline approved-pack compilation in `crates/tamil-toolkit/build.rs` and `build_lexicon.rs`, rejecting invalid package-local data and mapping sorted unique NFC keys to complete stable-ID posting lists; use checked fixed-width little-endian offsets, reproducible manifests and `OUT_DIR` only, no unsafe mmap, supplied-FST reuse, network access or self-dependency.
- [X] T047 [US4] Extend explicit selected dictionary/schema/source-terms copying in `tools/release_files.py` and Cargo inclusion patterns in `crates/tamil-toolkit/Cargo.toml`; generate package-local `crates/tamil-toolkit/lexicon/dictionary/` copies via sync, update canonical notice inputs, and never recursively include unreviewed `data/` content or hand-edit distribution copies.
- [X] T048 [US4] Prove byte-identical pack/index generation, bounded complete postings, source/review closure, default zero-payload behavior and all supported feature combinations with `tests/harness/test_lexicon_packs.py` and `crates/tamil-toolkit/tests/lexicon_pack.rs`; inspect source archives independently because disabled features do not remove packaged source files.
- [X] T049 [US4] Run source hashes, structural/full-scope accounting checks, release validation, two clean promotions/builds, nonempty CLDF validation/round-trip, release-policy/file checks and focused tests; record actual L3 evidence, pack/source hashes, measured size budget and reproducibility results in `docs/status.md` and `target/lexicon/l3-acceptance.json`, without claiming US3 lookup or publication.

**Checkpoint**: L3 needs actual approved content; US4's pack/exchange increment
is independently verifiable before public lookup. Final runtime archive proof
is a cross-cutting task after US3, not a circular US4 prerequisite.

## Phase 6: US3 — Retrieve all reviewed matches (Priority: P2)

**Goal**: Expose bounded exact lookup and pack introspection through existing
Rust/CLI/Python/Node/browser/Dart interfaces with the clarified filtering policy.

**Independent Test**: Query the declared nonempty approved profile with unchanged
goldens and verify all homographs, canonical equivalents, filters, statuses,
ordering and exact errors in every real runtime; default absent packs error.

### Tests first

- [X] T050 [P] [US3] Add failing Rust lookup/pack-introspection tests in `crates/tamil-toolkit/tests/lexicon.rs` consuming the source-backed expectations established by T044 and validating successful response payloads against `specs/021-lexicon-curation/contracts/lookup-response.schema.json`; cover homographs, NFC/NFD equivalence, preserved controls/spaces/case, scope/register truth tables, partial metadata, ordering and disabled/default pack errors without changing expected results to fit code.
- [X] T051 [P] [US3] Add dispatcher/CLI/binding contract test cases in `tests/harness/test_lexicon_runtime.py` and `tests/reference/lexicon/runtime/`, covering contract validation order, input type/65,536-byte boundary, unknown options/filters/packs, incompatible revisions, not-found versus missing data, and identical profile manifests; do not mock active parity or fabricate an approved corpus.

### Implementation

- [X] T052 [US3] Implement request/result/error/pack metadata types and safe generated-artifact access in `crates/tamil-toolkit/src/lexicon/mod.rs`, enforcing `#![forbid(unsafe_code)]`, default packs `["core"]`, explicit nonempty selections, `status = matched | not_found`, structured provenance/review availability and the exact errors in `contracts/lookup.md`.
- [X] T053 [US3] Implement exact NFC-only matching and complete multi-pack posting aggregation in `crates/tamil-toolkit/src/lexicon/mod.rs`; enforce “Inputs larger than 65,536 UTF-8 bytes are rejected, not truncated”, identical ordered canonical-equivalence results, bytewise stable entry-ID ordering, no trimming/repair/folding/control stripping/variant expansion/result caps, and rejection of conflicting same-ID revisions.
- [X] T054 [US3] Implement accepted region/register projection in `crates/tamil-toolkit/src/lexicon/mod.rs`: attested matches or reviewed unrestricted scope, unknown excluded only under the respective filter, reviewed child-to-parent geography without parent-to-child inference, narrower/explicit-unknown sense overrides, and removal of entries with no eligible remaining senses.
- [X] T055 [US3] Implement approved sense/text/example/relation/evidence response projection in `crates/tamil-toolkit/src/lexicon/mod.rs`, sorting senses by display order then ID, retaining visible unknown optional values and `accepted_auto_source` versus `accepted_human`, and excluding quarantined text/private notes/ineligible annotations from otherwise accepted entries.
- [X] T056 [US3] Register `lexicon_lookup` and `lexicon_packs` in `crates/tamil-toolkit/src/lib.rs`, retaining the shared dispatcher error channel and operation validation order; pack introspection must succeed with zero available packs, while requested unavailable data must not return a successful empty dictionary result.
- [X] T057 [US3] Add `lexicon lookup` and `lexicon packs` routing in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` with repeated `--pack`, `--region`, and `--register`, exact dispatcher JSON and exit semantics, preserving quoted input and reusing the existing CLI structure.
- [X] T058 [P] [US3] Add feature forwarding and thin typed `lexicon_lookup`/`lexicon_packs` wrappers in `bindings/python/Cargo.toml`, `bindings/python/python/tamil_toolkit/__init__.py`, and `__init__.pyi`; serialize shared results/errors without implementing matching, source eligibility or normalization in Python.
- [X] T059 [P] [US3] Add feature forwarding and typed Node/browser exports in `bindings/js-wasm/Cargo.toml`, `bindings/js-wasm/src/api.ts`, `index.ts`, and `web.ts`; expose the same selected dataset profile, null/unknown states, results and errors without a TypeScript linguistic engine.
- [X] T060 [P] [US3] Add feature forwarding and thin `lexiconLookup`/`lexiconPacks` helpers in `bindings/dart-flutter/rust/Cargo.toml` and `bindings/dart-flutter/lib/tamil_toolkit.dart`; reuse the existing JSON C ABI and preserve identical matching/filter/error behavior without a new ABI engine.
- [X] T061 [US3] Extend binding rebuild/parity/Dart and isolated-archive profile forwarding and manifest verification in `tools/tasks.py`, `tools/release.py`, and the existing golden harnesses under `bindings/python/tests/`, `bindings/js-wasm/`, and `bindings/dart-flutter/test/`; missing/mismatched packs or runtimes fail instead of skipping active cases, and no-data negative tests remain distinct from nonempty acceptance.
- [X] T062 [US3] Rebuild Python and both WASM targets with the approved profile, run every unchanged new golden through actual Rust/Python/Node/browser runtimes and then Dart host ABI/analysis/fixtures sequentially, and save profile hashes/results under `target/lexicon/parity/`; planned-suite dedicated evidence must not be reported as active coverage before the later activation decision in `docs/status.md`.
- [X] T063 [US3] Implement and run separate `structural` and `lookup` workloads in `tools/lexicon_bench.py`, writing `target/lexicon/benchmarks.json`: measure complete inventory/staging/structural validation of all 307,243 CSV records and 12 file hashes against the under-60-second/512-MiB targets, then measure 10,000-query warm lookup p95 under 10 ms plus cold start, serialization/large responses and actual pack/default bytes. Record per-stage/end-to-end wall time, peak process-tree RSS, machine/OS/toolchain/dataset hashes, sampling method and target comparisons; do not count a pilot as the full structural benchmark or truncate content to meet targets.
- [X] T064 [US3] Run focused Rust/CLI/dispatcher/adapter regressions, disabled-feature and multi-pack compatibility tests, confirm the real approved homograph cases and all declared errors agree, and record actual lookup/coverage limits in `docs/specs/lexicon-v0.1.md` and `target/lexicon/us3-proof.json`.
- [X] T065 [US3] Complete the nonempty L4 functional evidence summary in `docs/status.md` and `target/lexicon/l4-functional.json`, explicitly distinguishing proven local runtime behavior, still-planned fixture activation, outstanding source/annotation coverage and later archive/release review; do not count an empty/all-quarantine pilot as lookup support.

**Checkpoint**: All public interfaces are implemented and locally exercised
against real approved data. Manifest activation, archive acceptance, and
publication remain distinct final decisions/gates.

## Phase 7: Polish and cross-cutting integration

- [X] T066 [P] Update actual runnable instructions, scope, limits and L0–L4 evidence in `specs/021-lexicon-curation/quickstart.md`, `lexicon/README.md`, `data/sources/README.md`, and `CHANGELOG.md`; retain unknown coverage and keep `ROADMAP.md`, `docs/specs/architecture-roadmap.md`, and Feature 016 consistent without renumbering phases or changing ranks.
- [X] T067 Run `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, release-policy and release-file checks with the declared approved profile, serialize native/Dart Windows runs, verify all original source hashes and save exact results to `target/lexicon/integration-gates.log`; repair regressions without weakening fixtures or skipping unavailable runtimes.
- [X] T068 Record the explicit owner fixture-activation and release-scope review decision in `docs/status.md` and `tests/golden/manifest.json` only after concrete nonempty parity/source/pack evidence exists; leave activation pending if no applicable authorization is recorded, preserve release-policy/version scope, and do not publish registries or infer approval from a passing structural pilot.
- [X] T069 Run `just release-check` and selected-profile offline archive consumers through `tools/release.py`, verify actual `.crate`/Python/npm/Dart content and applicable terms with disabled features inspected separately, and record approved nonempty fixture results plus archive digests in `target/lexicon/archive-proof.json`; no registry upload or root-source-checkout dependence is allowed.
- [X] T070 Re-run any gate affected by final changes, validate the implemented quickstart, and finalize `docs/status.md`, `CHANGELOG.md`, `specs/021-lexicon-curation/spec.md`, and `specs/021-lexicon-curation/tasks.md` with actual checked tasks, remaining acceptance blockers, source/pack/profile hashes and next action; never mark all tasks complete while evidence, review or required checks remain pending.

## Dependencies and execution order

### Phase and milestone dependencies

```text
Setup T001–T003
  → Foundation T004–T009
  → US1 T010–T018 (traceable intake MVP)
  → US2 T019–T032 (editorial proposals and review machinery)
  → US4 T033–T037 (L2 structural pilot; zero eligible content allowed)
      → numerals may resume after recorded L2 acceptance
      → source/reuse/decision evidence T038–T039
      → US4 T040–T049 (nonempty L3 packs and exchange)
      → US3 T050–T065 (L4 functional lookup proof)
      → Integration T066–T070 (gates, activation decision, archives, handoff)
```

All dependencies point to earlier tasks. The external source/reviewer gate
begins at T038; it must not be moved ahead of T037. While source evidence is
unavailable, report L2 accurately, keep T038 onward pending where blocked, and
continue authorized independent work; never replace the actual-data gate with
synthetic fixtures. Task generation does not waive any future acceptance item.

### User-story independence and prerequisites

| Story | Required earlier work | Standalone value and proof |
|---|---|---|
| US1 | Setup/foundation | Full original inventory, traceable records/source leads, stable IDs and repeatable staging; all evidence may be unknown |
| US2 | Shared schemas/host tooling plus US1 records | Lossless proposed lexical structure, revision-safe decisions and reversible edits tested without a public pack |
| US4 | US1/US2 tooling | L2 structural proof first; later approved packs, reproducibility and exchange can be tested independently of US3 APIs |
| US3 | US4 nonempty approved pack, T044 source-backed goldens and T045–T048 compilation/profile rules | Same complete lookup results/errors in all real runtime interfaces |

US4's final archive integration is deliberately in Phase 7, after US3, rather
than a backward dependency. Within each phase, tests precede implementation,
schemas precede parsing, source decisions precede promotion, and goldens
precede compiler/lookup behavior. Related source changes never alter identities.

### Parallel opportunities

- Setup: T003 can run alongside T002 once T001 fixes the baseline; different files.
- Foundation: T004, T005, T006 and T007 run together after T003; T008 follows them.
- US1: T010 and T011 run together after foundation; shared `tools/lexicon.py`
  implementation tasks then run sequentially.
- US2: T019 and T020 run together after US1; shared implementation/data revisions
  stay sequential, preserving decisions.
- US4: T033 and T034 run together after US2; L2 tasks precede external-evidence
  work. Pack/source mutations and promotion run sequentially.
- US3: T050 and T051 run together after L3. T058/T059/T060 run together after
  the shared model/dispatcher/CLI tasks T052–T057 settle; profile integration T061
  follows all three. Do not overlap native/Dart gate processes on Windows.
- Integration: T066 documentation may run alongside T067 verification only while
  it does not modify source/fixture/profile inputs under test; T068–T070 remain
  sequential and affected gates must be rerun.

## Parallel examples per story

These are permitted future work waves, not delegation performed by task generation.

```text
US1: T010 tests/harness/test_lexicon_inventory.py
     T011 tests/harness/test_lexicon_identity.py

US2: T019 tests/harness/test_lexicon_curation.py
     T020 tests/harness/test_lexicon_review.py

US4: T033 tests/harness/test_lexicon_pilot.py
     T034 tests/harness/test_lexicon_packs.py

US3 after shared dispatcher contract:
     T058 bindings/python/...
     T059 bindings/js-wasm/...
     T060 bindings/dart-flutter/...
```

## Requirement and acceptance coverage

| Requirements / outcomes | Principal tasks |
|---|---|
| FR-001,002,003 / SC-001,002 | T001, T010–T018, T026–T027, T038–T041, T047–T049 |
| FR-004,005,006 / SC-001,003 | T003–T008, T011, T014–T016, T019–T025 |
| FR-007,009 / SC-002,006 | T020, T025–T030, T038–T040, T055 |
| FR-008 / SC-003,004,006 | T007–T009, T019, T028, T031, T044, T050–T054 |
| FR-010,011 / SC-003,004,006 | T006, T023–T024, T034, T040, T050, T054–T055 |
| FR-012,019 / SC-001,003 | T012–T018, T033, T035–T037, T049 |
| FR-013,014,020 / SC-004 | T044, T050–T062, T064–T065, T067–T069 |
| FR-015,016,017 / SC-005,006 | T003–T009, T027–T028, T031, T034–T048, T061, T063, T067–T069 |
| FR-018 / SC-007 | T042–T043, T049, T069 |
| FR-021,022 / SC-008 | T002, T009, T018, T032, T037, T044–T047, T052, T065–T070 |

## Implementation strategy

1. **Smallest useful MVP**: T001–T018 delivers US1's trustworthy intake and
   source/identity accounting. Validate it before editorial expansion.
2. **Current scheduling objective**: T019–T037 completes proposed curation,
   review machinery and the structural pilot. All-quarantine is valid and must
   remain explicit. Record actual L2 acceptance; resume numerals if appropriate.
3. **Evidence-led expansion**: Recover a defensible subset at T038–T039, then
   promote/compile/export it at T040–T049. Keep unavailable external evidence
   visible; do not downgrade the accepted review/rights criteria to make progress.
4. **Runtime delivery**: Implement only the bounded lookup contract at T050–T065
   using unchanged source-backed goldens and the shared Rust dispatcher.
5. **Integration**: Complete T066–T070 with actual proof, a separate activation
   decision and offline archives. Publishing and new linguistic features remain
   outside these tasks. Do not automatically commit/push session edits.

## Notes

- T001–T069 are verified and checked `[X]` through source/review closure, compiled
  L3 acceptance, real runtime parity, performance, archives and owner activation.
  T070 completes the final affected checks and handoff. Historical bulk-source
  lineage remains unknown; that intake stays quarantined.
- If handing back after the MVP or another implementation checkpoint, run the
  required `agent-post-edit` and `agent-pre-stop-gate` checks and record their
  actual results; task grouping never waives the repository's integration gates.
- No FST/index/JSON/executable belongs under canonical `lexicon/`; generated
  Cargo outputs stay in `OUT_DIR`, schemas outside `lexicon/`, and originals intact.
- T031 wired decoded curated CSV validation into `tools/tasks.py` and
  `tools/mcp-tamil-oracle/check_source_unicode.py` without pretending the raw
  audit establishes Unicode 17 compliance.
- Confidence, complete-looking IPA, imported grammar fields and public access
  are not substitutes for evidence or human decisions where the spec requires them.
- A structural L2 pass cannot satisfy nonempty CLDF, lexical consumer, active
  parity, archive, or publication criteria. Preserve unfinished tasks across handoff.

## Phase 8: Review remediation

- [X] T071 Enforce exact accepted evidence/decision closure and conflict/cardinality checks for compiler scopes; reject unsupported relation shapes or preserve typed endpoints without silent loss per FR-003, FR-011, FR-014 and FR-016.
- [X] T072 Align host and compiler finite vocabulary parsing, empty-registry enforcement, structural properties and region hierarchy checks per FR-006 and FR-016.
- [X] T073 Align sense scope inheritance, not-applicable register semantics and unknown coverage accounting across host/compiler projections per FR-006, FR-010 and FR-014.
- [X] T074 Make active-suite selection profile-aware across Rust, binding harnesses and archive consumers, preserving all 36,205 active cases under core and explicit no-data negative coverage per T061, T068 and FR-020.
- [X] T075 Resolve additional review findings in multi-pack compatibility, licensed-source notice enforcement and relation assertion ownership; preserve explicit null-packs errors and unchanged goldens per FR-003, FR-011 and FR-015–FR-017.
- [X] T076 Run focused regressions, serialized affected native/binding/Dart/archive gates, update review evidence and handoff, and obtain a fresh independent Hydrogen high review before reporting remediation complete per T067, T069–T070 and FR-022.

## Phase 9: Final review relation integrity

- [X] T077 Preserve canonical sense-anchored relations and their assertion/evidence/decision closure through CLDF export and verify round trips against the intended canonical selection per FR-011, FR-018 and SC-007; add nonempty relation and tamper regressions (`tools/lexicon_cldf.py`, `tests/harness/test_lexicon_cldf.py`).
- [X] T078 Validate optional unknown/not-applicable scope backing pairs, ownership and property dimensions in Python/Rust and enforce paired-translation component, owner and non-self references per FR-006, FR-014 and FR-016; regressions: 29 Python and 21 Rust tests pass.
- [X] T079 Apply cross-pack omission before public-only relation shape and vocabulary constraints while retaining editorial integrity checks per FR-011 and FR-015; prove external entry-anchored/foreign-code relations omitted under the selected policy (`tools/lexicon_packs.py`, `tests/harness/test_lexicon_packs.py`).

## Phase 10: Expanded-pack review corrections

- [X] T080 Preserve distinct same-POS source homographs and stable per-section identities during bulk extraction per FR-004, FR-005 and FR-013; add pinned multi-etymology regressions and regenerate curated mappings.
- [X] T081 Route entries by source-backed scope on their own senses; retain unrelated page categories as evidence and unmapped qualifier prose without synthesizing domain attestations per FR-007, FR-010 and FR-014.
- [X] T082 Align default/core/full profile harnesses and isolated consumers, replace obsolete absent-word assumptions with verified absent fixtures, and report profile exclusions and dedicated full-profile coverage per FR-020 and T061.
- [X] T083 Include all packaged dictionary directories in generated license documentation; regenerate corrected packs and copies, preserve PoC linguistic payloads and frozen originals, then run full parity, measured benchmarks, archive checks and a fresh independent review before expanded-pack acceptance per FR-017, FR-022 and SC-008.

## Phase 11: Verified pipeline performance

- [X] T084 Preserve completed acceptance, three-profile archives and benchmark baseline; record the owner-stopped extra pre-stop timing as incomplete, preserving passed evidence.
- [X] T085 Share immutable real-pack validation/export fixtures across the harness session; keep tamper tests isolated and retain full checked-in pack end-to-end verification.
- [X] T086 Enable locked pytest-xdist scheduling with cross-process protection for shared Cargo/binding artifacts; prove original test-ID coverage remains intact.
- [X] T087 Profile the actual 307,243-row source pipeline and all three expanded CLDF packs; implement tests-first bounded Rust/PyO3 batch helpers at measured hot paths with exact scalar/hash/error parity.
- [X] T088 Build independent bindings concurrently in isolated Cargo directories, with content/output-verified reuse, explicit force builds and cross-process consumer leases.
- [X] T089 Keep daily gates single-profile and reserve the full runtime/archive matrix for explicit final acceptance; remove only proven duplicate invocations without losing unique assertions or property cases.
- [X] T090 Measure candidate harness, lexicon pipeline and pre-stop timings, run the full unchanged final matrix, and record exact comparisons, coverage and limitations.

## Phase 12: Owner-requested full historical bundle recovery (2026-11-16)

This expands the previous verified-pack scope. Earlier checked tasks do not mean
the 307,243-record historical bundle is approved or ready to release.

- [X] T091 Reconcile the full historical source inventory and exact spelling overlap, preserve all 12 original hashes, and document source-specific trace/reuse/quality blockers and local permission-request drafts.
- [X] T092 Reconcile the 410 Wiktionary spelling gaps and capture missing exact-title revisions; validate the seven-entry/nine-sense literal-source candidate packet with canonical/CLDF roundtrip and preserving core union.
- [X] T093 Capture all 384 available pinned pages as rendered HTML with explicit current-template provenance; produce unaccepted proposals and exact blocked/missing accounting without inventing expansions or bypassing acceptance rules.
- [ ] T094 Obtain genuine review of the rendered-source extraction policy and exact proposed claims; resolve or withhold the remaining mixed-script/unmapped-source cases. No manufactured human decisions or automatic promotion of derived proposals.
- [ ] T095 Recover applicable upstream record/edition/extraction and reuse evidence for TVA/Sorkuvai and the remaining historical collections, or explicitly agree a smaller release inventory. Preserve unresolved records; do not infer permission from source labels or public access.
- [ ] T096 Complete owner review/activation of the seven new sourced recovery vectors and any subsequent additions; finish all required integration/runtime/archive gates against the settled manifests, preserving existing accepted payloads.
- [ ] T097 Prepare the next synchronized version and reviewed release artifacts only after the included/excluded data scope and approval gates are satisfied. The requested all-record release remains open while T094-T096 are unresolved.


### Owner-directed full supplied-record access (2026-11-16)

Latest owner instruction explicitly authorizes implementing all supplied records
without additional permissions. This changes implementation scope, not the
truth of third-party rights or lexical acceptance.

- [x] T098 Specify source-record lookup and sourced planned vectors before Rust behavior.
- [x] T099 Export/index every historical CSV row with exact cell/provenance preservation and deterministic coverage proof.
- [x] T100 Expose shared Rust query semantics in the playground with pagination, original fields and truthful unverified status.
- [x] T101 Exercise new vectors in real Rust/Python/Node/browser WASM/Dart, affected gates and artifact integrity checks.
- [ ] T102 Prepare the next version only after concrete artifacts and final checks are reviewable; no automatic publishing.
