# Quickstart Validation: Feature 021

**Status**: Design guide. The audit command below exists today. All commands
under “After implementation” are proposed interfaces and must not be represented
as already runnable or passing. No dataset, schema, lookup operation, or public
pack is implemented by `speckit-plan`.

## Existing baseline check

From the repository root, with the documented Python environment available:

```powershell
uv run --locked python tools/audit_lexicon_source.py --output target/lexicon/intake-audit.json
```

Expected: 12 files hash-identical to the intake inventory, consistent CSV record
widths, 44,229 primary entries, 63,633 meaning rows, and 19,849 primary relations.
The structural inventory totals 307,243 logical CSV records across 11 CSVs;
the FST has file-level inventory. These are intake totals, not approved vocabulary.
The existing optional `--runtime-check` compares the locally installed native
Rust binding; rebuild before treating new runtime behavior as verified.

Authoritative contracts: [curation](contracts/curation.md),
[lookup](contracts/lookup.md), [packs](contracts/packs.md),
[data model](data-model.md). Do not edit or normalize the 12 input files.

## After implementation — L1/L2 structural workflow

Prerequisites: implemented host tooling/schemas, committed identity namespace,
and the source checksums. For linguistic inspection, rebuild the existing native
binding; a missing binding must not invoke a second Tamil engine.

```powershell
uv run --locked python tools/lexicon.py inventory --source data/sources/tamil-lexicon --output target/lexicon/inventory
uv run --locked python tools/lexicon.py stage --inventory target/lexicon/inventory --workspace data/curation/tamil-lexicon
uv run --locked python tools/lexicon.py pilot --workspace data/curation/tamil-lexicon --selection data/curation/tamil-lexicon/pilot-selection.toml --output target/lexicon/pilot-report.json
uv run --locked python tools/lexicon.py validate --workspace data/curation/tamil-lexicon --mode structural --selection data/curation/tamil-lexicon/pilot-selection.toml --output target/lexicon/structural-report.json
```

Verify every FR-019 sampling minimum and 100% selected-record dispositions.
Each unresolved source, reuse, or linguistic condition has a quarantine/exclusion
reason and is not falsely approved. A report with `l2_structural_accepted=true`
and zero eligible assertions is a valid L2 outcome; L3/L4 remain pending. Record
accepted L2 evidence in the handoff before resuming Phase 6. Do not infer full-
bundle accounting from the selected pilot.

Repeat inventory and staging with identical inputs: IDs, tables, findings and
report hashes must agree, with no duplicate rows. Change a copied input in an
isolated test fixture and confirm hash rejection; never alter the real originals.
Use malformed fixture records for broken references, invalid cell escapes, stale
exceptions, source-label-only approval and review-hash invalidation tests.

## After implementation — L3 source evidence and approved subsets

First recover source/extraction evidence and record actual review/reuse decisions.
Source labels alone are insufficient. Use human decisions for corrections,
inferred/derived annotations and ambiguity; unchanged source-verified claims may
use the specified automated acceptance path. No unattended tool fabricates a
human decision. A release validation example:

```powershell
uv run --locked python tools/lexicon.py validate --workspace data/curation/tamil-lexicon --mode release --pack core --output target/lexicon/core-release-report.json
uv run --locked python tools/lexicon.py promote --workspace data/curation/tamil-lexicon --pack core --output target/lexicon/core-canonical
```

An all-quarantine workspace must fail this mode even if L2 passed. A nonempty
eligible subset must retain required forms, senses, scope, approved evidence and
source terms, excluding unreviewed optional annotations. Review the generated
canonical projection before integrating it into `lexicon/dictionary/`.
Promotion does not publish or activate runtime support.

Compare two clean promotions from identical inputs. Confirm original source
hashes remain identical, every affected source row has a disposition, and
master-only claims are retained without creating duplicate entries. Verify that
only approved assertions enter the resulting pack and required attributions and
terms accompany every selected source.

## After implementation — L4 lookup and profiles

Before runtime algorithms, add the module specification and sourced escaped
`tests/golden/lexicon_lookup.jsonl` cases with planned status. The implementation
must consume these unchanged. Build a declared nonempty approved profile:

```powershell
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon packs
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon lookup 'example' --pack core
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon lookup 'example' --pack core --region LK-JAFFNA
```

`example` is a shape demonstration; test expectations must use actual reviewed
headwords from the golden file, not invent an approved entry for these examples.
Use the same selected dataset revision/features when rebuilding Python, Node,
browser WASM and Dart. Update the existing binding-sync tools to carry the same
profile; a mismatch is an error rather than grounds to skip an active row.

Acceptance checks:

- Every approved homograph returns, ordered by stable entry ID; no first-ID-only
  behavior or result cap. Conflicting same-ID revisions across packs fail.
- NFC/NFD-equivalent queries yield identical results; case, spaces, controls,
  joiners, soft hyphens, and original text stay preserved according to contract.
- Region filtering includes attested matches/unrestricted reviewed scope;
  excludes unknown or other-region-only scope; unknown remains visible without
  a region filter. Sense-level overrides prevent incompatible meanings leaking.
- Register filters, unknown optional fields, not-found, invalid types/options,
  byte limits, unsupported pack/filter errors, and exact error strings agree
  across Rust, Python, both WASM targets, and Dart.
- No-data/default builds report absent packs explicitly and embed zero lexicon
  data bytes; they cannot satisfy nonempty runtime acceptance.

## After implementation — exchange, offline archives and final gates

```powershell
uv run --locked python tools/lexicon.py export-cldf --canonical lexicon/dictionary --pack core --output target/lexicon/cldf/core --check
just sync-release-files
just check-release-files
just check-release-policy
just agent-post-edit
just agent-pre-stop-gate
just test-dart
just release-check
```

Run shared-native/Dart gates sequentially on Windows to avoid overlapping DLL
locks. Export validation requires the pinned CLDF dev validator and locally
available schema resources; ordinary Cargo compilation needs no Python/network.
Confirm lossless extended round-trip of a nonempty approved subset. Compare
identical data/index output bytes from two independent generation directories.
Inspect actual `.crate`, Python/npm and Dart inventories for approved sources
and full required terms; disabled features do not hide unsafe source-archive
contents. Standalone Cargo consumers build from synced package-local inputs,
without access to the root lexicon or source collection. No registry upload.

Record runtime counts, profile/dataset versions, hashes, size/memory/timing and
actual command results. Owner activation and manual release decisions remain
separate. Passing L2 alone must never trigger those decisions automatically.
