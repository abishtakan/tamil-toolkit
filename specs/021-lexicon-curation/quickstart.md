# Quickstart Validation: Feature 021

**Status**: L1/L2 intake, reviewed L3 core and bounded real L4 runtime parity
are verified. Core/default Rust, Python, Node/browser WASM and Dart checks and
isolated archive consumers pass. Performance and final gates pass; owner core-profile activation was approved on 2026-11-15.

- **L1/L2 historical intake (`data/curation/tamil-lexicon/`)**: Clean UTF-8
  intake/replay ([us1-proof.json](../../target/lexicon/us1-proof.json)), exact
  source-content equality ([source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json)),
  739-record pilot ([us2-proof.json](../../target/lexicon/us2-proof.json),
  [l2-acceptance.json](../../target/lexicon/l2-acceptance.json),
  [structural-final.json](../../target/lexicon/structural-final.json)), and
  fail-closed release rejection ([release-rejection-final.json](../../target/lexicon/release-rejection-final.json))
  passed (`0` accepted decisions, `0` eligible assertions; historical merged
  bundle remains quarantined, Phase 6 numerals scheduling unblocked).
- **L3 reviewed Wiktionary core (`lexicon/dictionary/`)**: Six entries, `19`
  senses, `31` genuine human-accepted claims (`abish`, `2026-11-14`,
  [approval receipt](../../docs/reviews/wiktionary-core-approval-2026-11-14.json)),
  canonical dataset `0.1.0+4d1309d05391` (manifest SHA-256
  `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`), offline
  CLDF 1.3 validation/round-trip (`dbc9cd09b2c4d267f09ef25493656c7b99d25005614a2a326b632519d75dc54b`),
  all `16` feature combinations, `0`-byte default payload, and deterministic
  `50,923`-byte core `.tlpack` compilation (SHA-256
  `283e32d7b3dbfa11d1bedc201a95e90bcb064021dba96fd6a44a61491f5137ea`,
  [l3-acceptance.json](../../target/lexicon/l3-acceptance.json)). Separate
  **CC-BY-SA-4.0** data terms apply to Wiktionary records while engine/tooling
  code remains **MIT**; structured scopes stay `unknown` (`2` pending
  proposals) with no IPA, etymology, morphology, or DEDR runtime claims.
- **L4 focused Rust checks**: Safe lookup/dispatcher/CLI pass `8` focused
  `core` Rust tests (including all `44` unchanged **active** goldens in
  [lexicon_lookup.jsonl](../../tests/golden/lexicon_lookup.jsonl)), `7` focused
  `default` tests, and `core` `clippy -D warnings`
  ([runtime-core-root.log](../../target/lexicon/runtime-core-root.log),
  [runtime-default-root.log](../../target/lexicon/runtime-default-root.log),
  [runtime-clippy-root.log](../../target/lexicon/runtime-clippy-root.log)).
  Lookup allocates on NFC query normalization and entry deserialization (no
  zero-allocation claim).

See [the storage decision](../../docs/decisions/lexicon-text-storage.md). Exact
scalar diagnostics and golden vectors remain escaped.

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

## Structural workflow — implemented L1/L2 verification

Prerequisites: implemented host tooling/schemas (`tools/lexicon.py`,
`schemas/lexicon/`), committed identity namespace (`data/curation/tamil-lexicon/dataset.toml`),
source checksums (`data/sources/tamil-lexicon.sha256.json`), and rebuilt native
Python adapter (`just sync-bindings`). Note:

- Clean full inventory/stage replay belongs **before** `curate` projection
  (`263,014` initial identities before projection vs `264,402` after projection).
- `select-pilot` is a **conditional one-time creation** when
  `data/curation/tamil-lexicon/pilot-selection.toml` does not yet exist; the
  existing `739`-record selection is preserved and must not be silently replaced
  (if the file already exists, `select-pilot` checks equality rather than overwriting it).
- Exact decoded payload/scalar equality against the 12 frozen originals is
  independently reproducible after staging or projection via `--payloads-only`.

```powershell
# 1. Optional fresh intake replay (263,014 initial identities).
# Use a new scratch directory; the existing editorial workspace is already projected.
$intakeReplayRoot = Join-Path 'target/lexicon' ('intake-check-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$intakeReplayRoot/workspace" -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath data/curation/tamil-lexicon/dataset.toml -Destination "$intakeReplayRoot/workspace/dataset.toml"
uv run --locked python tools/lexicon.py inventory --source data/sources/tamil-lexicon --output "$intakeReplayRoot/inventory"
uv run --locked python tools/lexicon.py stage --inventory "$intakeReplayRoot/inventory" --workspace "$intakeReplayRoot/workspace"
uv run --locked python tools/lexicon_proof.py --workspace "$intakeReplayRoot/workspace" --inventory "$intakeReplayRoot/inventory" --output "$intakeReplayRoot/proof.json" --replay

# 2. One-time pilot selection (only if pilot-selection.toml does not exist; checks without replacing if present)
if (-not (Test-Path data/curation/tamil-lexicon/pilot-selection.toml)) {
  uv run --locked python tools/lexicon.py select-pilot --selection data/curation/tamil-lexicon/pilot-selection.toml
}

# 3. Representative 739-record projection, payload proof, structural pass (exit 0), and release guard rejection (exit 1)
uv run --locked python tools/lexicon.py curate --workspace data/curation/tamil-lexicon --selection data/curation/tamil-lexicon/pilot-selection.toml
uv run --locked python tools/lexicon_proof.py --workspace data/curation/tamil-lexicon --output target/lexicon/source-content-proof-final.json --payloads-only
uv run --locked python tools/lexicon.py pilot --workspace data/curation/tamil-lexicon --selection data/curation/tamil-lexicon/pilot-selection.toml --output target/lexicon/pilot-report.json
uv run --locked python tools/lexicon.py validate --workspace data/curation/tamil-lexicon --mode structural --selection data/curation/tamil-lexicon/pilot-selection.toml --output target/lexicon/structural-final.json
uv run --locked python tools/lexicon.py validate --workspace data/curation/tamil-lexicon --mode release --pack core --output target/lexicon/release-rejection-final.json
```

`validate --mode structural` exits `0` (`l2_structural_accepted: true`,
`eligible_assertions: 0`, `739` selected records) and `validate --mode release --pack core`
exits `1` (`NONEMPTY_ELIGIBLE_PACK_REQUIRED`), confirming fail-closed L2 semantics
for the quarantined historical intake. Separately supplied curation/review CSVs
can be appended with implemented
`uv run --locked python tools/lexicon.py review-ingest --workspace WORKSPACE --table sources|evidence|decisions|pack_members|scopes|labels|unicode_exceptions|changes|successors --input PATH`.
Do not infer full-bundle approval from the selected pilot.

## Implemented — L3 reviewed core, promotion, sync & CLDF export (T038–T049)

The approved fresh Wiktionary core (`data/curation/wiktionary-core-reviewed/`,
`6` entries, `19` senses, `31` accepted-human claims, `2` pending scope
proposals, `2` rejected superseded assertions) passes source/replay verification,
release validation, deterministic canonical promotion, release-file sync, and
offline CLDF 1.3 round-trip checks:

```powershell
# 1. Verify reviewed Wiktionary workspace and deterministic rebuild replay
uv run --locked python -m tools.lexicon_wiktionary_candidate verify --dataset reviewed
uv run --locked python -m tools.lexicon_wiktionary_candidate replay-check --dataset reviewed

# 2. Release validation, deterministic canonical promotion, and offline CLDF 1.3 round-trip
uv run --locked python tools/lexicon.py validate --workspace data/curation/wiktionary-core-reviewed --mode release --pack core --output target/lexicon/core-release-report.json
uv run --locked python tools/lexicon.py promote --workspace data/curation/wiktionary-core-reviewed --pack core --output target/lexicon/core-canonical --report target/lexicon/core-promote-report.json
uv run --locked python tools/lexicon.py export-cldf --canonical lexicon/dictionary --pack core --output target/lexicon/cldf/core --check --report-output target/lexicon/cldf/core-report.json

# 3. Sync canonical dictionary/schema/notice copies into crates/tamil-toolkit and verify policy/files
just sync-release-files
just check-release-files
just check-release-policy
```

Compare two clean promotions and two clean CLDF exports from identical inputs
to confirm byte-identical outputs (`lexicon/dictionary/` manifest SHA-256
`4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`; CLDF SHA-256
`dbc9cd09b2c4d267f09ef25493656c7b99d25005614a2a326b632519d75dc54b`). Promotion
does not publish packages, approve historical bulk files, or activate golden
suites.

## Implemented (focused Rust) — L4 lookup and CLI

`docs/specs/lexicon-v0.1.md` and the `44` escaped **active** vectors in
`tests/golden/lexicon_lookup.jsonl` are registered in `tests/golden/manifest.json`
(`"status": "active"`). Focused Rust tests and CLI routes work against the
compiled `core` profile and the zero-payload `default` profile:

```powershell
# Focused Rust runtime tests (default no-data vs lexicon-core profile)
cargo test --locked -p tamil-toolkit --test lexicon
cargo test --locked -p tamil-toolkit --features lexicon-core --test lexicon
cargo test --locked -p tamil-toolkit --features lexicon-core --test lexicon_pack

# CLI introspection & exact NFC lookup (default returns []; core returns manifest metadata)
cargo run --locked -p tamil-toolkit --bin tamil-toolkit -- lexicon packs
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon packs
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon lookup "நன்றி" --pack core
```

Note on `"நன்றி"`: returns both distinct stable-ID entries (`NOUN` and `INTJ`,
sorted bytewise by entry ID) with `unknown` structured region/register scopes;
passing `--region` or `--register` currently returns the contract invalid-filter
error because the approved `core` registries have empty `region_codes` /
`register_codes` and `2` pending scope proposals. `lexicon_lookup` allocates on
NFC query normalization and payload deserialization (not zero-allocation).

Acceptance checks (focused Rust verified; cross-runtime parity underway):

- Every approved homograph returns, ordered by stable entry ID; no first-ID-only
  behavior or result cap. Conflicting same-ID revisions across packs fail.
- NFC/NFD-equivalent queries yield identical results; case, spaces, controls,
  joiners, soft hyphens, and original text stay preserved according to contract.
- Region filtering includes attested matches/unrestricted reviewed scope;
  excludes unknown or other-region-only scope; unknown remains visible without
  a region filter. Sense-level overrides prevent incompatible meanings leaking.
- Register filters, unknown optional fields, not-found, invalid types/options,
  byte limits, unsupported pack/filter errors, and exact error strings must agree
  across Rust, Python, both WASM targets, and Dart.
- No-data/default builds report absent packs explicitly (`lexicon packs` -> `[]`,
  `lexicon lookup` -> `lexicon: pack unavailable 'core'`) and embed `0` lexicon
  data bytes; they cannot satisfy nonempty runtime acceptance.

## Verified benchmarks, profile parity, offline archives and gates

The separate `structural` and `lookup` workloads, actual multi-runtime parity,
isolated offline archives and owner fixture activation are verified. The commands
below reproduce those checks. Validate real response payloads against
[the closed response schema](contracts/lookup-response.schema.json); the
[schema-only example](contracts/lookup-response.example.json) is illustrative
only.

```powershell
# T063 benchmarks (do not run overlapping structural benchmarks while a bulk run is active)
uv run --locked python tools/lexicon_bench.py structural --output target/lexicon/benchmarks-structural.json
uv run --locked python tools/lexicon_bench.py lookup --output target/lexicon/benchmarks-lookup.json

# T061 profile-forwarded parity & gates (default zero-payload and core profile; serialize native/Dart runs on Windows)
uv run --locked python tools/tasks.py test-rust --lexicon-profile core
uv run --locked python tools/tasks.py sync-bindings --lexicon-profile core
uv run --locked python tools/tasks.py test-parity --lexicon-profile core
uv run --locked python tools/tasks.py test-dart --lexicon-profile core
uv run --locked python tools/tasks.py agent-pre-stop-gate --lexicon-profile core

# Canonical gates select core while Cargo default data features stay off
just agent-post-edit
just agent-pre-stop-gate
just test-dart

# Isolated offline archive verification (no registry upload)
uv run --locked python tools/release.py all --lexicon-profile core
just release-check
```

Note: `tools/tasks.py` and `tools/release.py` accept `--lexicon-profile default|core`
(and `test-lexicon-parity` runs `core` parity + Dart sequentially), whereas
`justfile` recipes (`just test-parity`, `just agent-pre-stop-gate`, `just test-dart`,
`just release-check`) now select core implicitly to execute every active vector.
Cargo default features remain off; explicit `--lexicon-profile default` builds
are for dedicated no-data checks, not full active-suite parity. Run shared-native
and Dart gates sequentially on Windows to avoid overlapping DLL locks.
Confirm lossless extended round-trip and inspect actual `.crate`, Python/npm,
and Dart inventories for approved sources and full CC-BY-SA-4.0 / MIT notices;
disabled features do not remove packaged `lexicon/dictionary/` source files.
Owner fixture activation is recorded in `tests/golden/manifest.json` and
`docs/reviews/lexicon-fixture-activation-2026-11-15.json`. Manual publication
remains a separate action and is not authorized.


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
