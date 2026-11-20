# Feature 021 Remaining Implementation Audit & Code Plan (`T038`–`T070`)

- **Date**: `2026-11-14`
- **Role / Scope**: Read-only architecture, schema, tooling, packaging, runtime, and execution-wave audit for `specs/021-lexicon-curation/tasks.md` (`T038`–`T070`), following L1/L2 structural completion (`T001`–`T037`) under `json-string-utf8-v1`.
- **Non-Approval Statement**: Nothing in this document approves linguistic content, verifies `T038` source/reuse rights, grants `T039` human acceptance, or clears `CC-BY-SA-4.0` / `GFDL` distribution policy. Specifically, the isolated 4-entry / 16-sense candidate in `data/curation/wiktionary-candidate/` (`24` assertions: `4 pending`, `20 needs_review`, `0` accepted decisions, `reuse_state = "restricted"`, `49` findings, `eligible_assertions = 0`) remains strictly pending external evidence and policy clearance.

---

## 1. Current Baseline & External Gate Boundary

| Area | Implemented State (`T001`–`T037`) | Blocking / Remaining (`T038`–`T070`) |
|---|---|---|
| Immutable Intake (`data/sources/tamil-lexicon/`) | 12 original files untouched; SHA-256 manifest + 307,243 raw assertions verified (`tools/lexicon_proof.py`). | `T038` external source/edition/reuse recovery; `T049`/`T067` original-12 hash re-checks. |
| Editorial Tooling (`tools/lexicon*.py`) | `inventory`, `stage`, `select-pilot`, `curate`, `review-ingest`, `pilot`, `validate --mode structural\|release` (fail-closed guard only). | `review-ingest` expansion (`pack_members`, `scopes`, `labels`, `unicode_exceptions`, `changes`, `successors`), full L3 closure `validate --mode release` (`T040`), `promote` (`T041`), `export-cldf --check` (`T043`). |
| Candidate Workspaces | `data/curation/tamil-lexicon/` (`739`-record L2 structural pilot, `0` eligible assertions) + isolated `data/curation/wiktionary-candidate/` (`4` entries, `16` senses, `0` eligible assertions). | `T038` source/reuse verification + `T039` genuine human decisions & real homograph in `pack_members.csv` before any `lexicon/dictionary/` integration (`T044`). |
| Canonical Data (`lexicon/dictionary/`) | Empty; `tools/lexicon_validate.py:check_curated_csv` expects editorial filenames in `lexicon/dictionary/` when populated. | Canonical pack tables + `packs.toml` + vocabularies + attribution notices (`T044`), plus canonical validator support. |
| Rust Core & CLI (`crates/tamil-toolkit/`) | No `src/lexicon/`, no `build.rs`/`build_lexicon.rs`, no `lexicon-*` Cargo features, `fst`/`csv` absent from `Cargo.lock`. | Feature gating (`T045`), `build.rs`/`build_lexicon.rs` (`T046`), `release_files.py` + `Cargo.toml` include/notices (`T047`), `src/lexicon/mod.rs` (`T052`–`T055`), `lib.rs` dispatcher (`T056`), CLI (`T057`). |
| Python / WASM / Dart / Parity / Smoke | Pure UTF-8/core/calendar/hyphen bindings only (`bindings/python`, `bindings/js-wasm`, `bindings/dart-flutter`); 0 lexicon ops. | `T058`–`T062` feature forwarding, wrappers, manifest/parity wiring (`tools/tasks.py`, `tools/release.py`), `T067`–`T069` gates & smoke consumers. |
| Spec, Goldens, Benchmarks, Docs | `docs/specs/lexicon-v0.1.md`, `tests/golden/lexicon_lookup.jsonl`, `tools/lexicon_bench.py`, `schemas/lexicon/cldf/` absent. | `T042`, `T044`, `T049`, `T063`–`T066`, `T068`, `T070`. |

---

## 2. Closed-Schema Consistency & Data/Licensing Separation Audit

### 2.1 Finite Schema & Contract Discrepancies to Resolve Before `T041` / `T052`

1. **`relations.directionality` enum conflict**:
   - `schemas/lexicon/lexical.schema.json:195-200` allows `["directed", "undirected"]`.
   - `specs/021-lexicon-curation/contracts/lookup-response.schema.json:477-482` and `specs/021-lexicon-curation/contracts/lookup.md:106` specify `["directed", "symmetric"]`.
   - **Required fix**: Align before `T041`/`T044` (either migrate editorial enum or deterministically map `"undirected"` -> `"symmetric"` at `promote`, and document in `docs/specs/lexicon-v0.1.md`). Every `Relation` also requires both `"source"` and `"target"` `Endpoint` objects (`lookup-response.schema.json:497-505`).
2. **Identifier regex divergence (`.` and `:`)**:
   - `schemas/lexicon/common.schema.json:18-22` permits `^[A-Za-z][A-Za-z0-9_.:-]*$`.
   - `specs/021-lexicon-curation/contracts/lookup-response.schema.json` enforces stricter `^[A-Za-z][A-Za-z0-9_-]*$` on `Acceptance.decision_id` (L48), `Acceptance.actor_id` (L58), `Provenance.assertion_id` (L109), `source_id` (L117), `Scope.codes` (L150), `Annotation.property` (L340), `Form.form_id` (L357), `Text.text_id` (L410), `language_id` (L423), `Endpoint.id` (L457), `Relation.relation_id` (L471), `Relation.code` (L475), `Sense.sense_id` (L512), `parent_sense_id` (L522), `Entry.entry_id` (L617), `Coverage.*` (L691, L699, L707).
   - **Hazard**: Note synthetic fixtures such as `tests/harness/test_lexicon_packs.py:199` use `actor_id = "human.reviewer"`, which passes CSV validation and fails `lookup-response.schema.json`. Either normalize/align the regex contract or enforce the stricter `[A-Za-z][A-Za-z0-9_-]*` pattern at `validate --mode release` (`T040`).
   - Also normalize snapshot prefix consistency (`lexicon.py` `snap` vs `lexicon_wiktionary_candidate.py:543` / `test_lexicon_packs.py:90` `snp`; both satisfy the stricter pattern).
3. **`Acceptance.actor_id` nullability for `accepted_auto_source`**:
   - `schemas/lexicon/review.schema.json:207-209` makes `decisions.actor_id` `nullableId` (e.g., `None` with non-empty `method_version` for automated acceptance).
   - `contracts/lookup-response.schema.json:56-59` requires non-null `actor_id` matching `^[A-Za-z][A-Za-z0-9_-]*$`.
   - **Required fix**: Define exact deterministic `actor_id` projection in `promote`/`lookup` (e.g., `"automated"` or derived `method_version` token matching `^[A-Za-z][A-Za-z0-9_-]*$`) or permit `type: ["string", "null"]` when `outcome == "accepted_auto_source"`.
4. **`texts` ownership & `"unparsed"` components**:
   - `schemas/lexicon/lexical.schema.json:116-120` permits `owner_kind = "entry" | "sense"` and `component = "unparsed"`.
   - `contracts/lookup-response.schema.json:412-419,549-563` embeds texts ONLY on `Sense.components` (`definition | gloss | translation | citation`, `minItems: 1`) and `Sense.examples` (`example`), with no `"unparsed"` kind and no entry-level `texts` array.
   - **Required fix**: `validate --mode release` (`T040`) and `promote` (`T041`) MUST exclude `"unparsed"` texts, forbid counting `"unparsed"` texts toward a sense's minimum component requirement, and define entry-owned text handling (reject or disallow promotion unless mapped to a sense).
5. **Non-empty `Entry.provenance` and `Sense.provenance` derivation**:
   - Observed in `data/curation/wiktionary-candidate/entries.csv`, `senses.csv`, and `assertions.csv`: `entries` holds `pos_assertion_id` (nullable in `lexical.schema.json`) and `canonical_form_id`; `senses` has no assertion FK column; `assertions.csv` holds `form/headword`, `entry/part_of_speech`, and `text/gloss|definition` assertions, with zero `sense`-subject existence assertions.
   - Yet `contracts/lookup-response.schema.json:595,665-666` requires `minItems: 1` on both `Sense.provenance` and `Entry.provenance`.
   - **Required fix**: Explicitly define closed provenance aggregation in `T040`/`T041`/`T055`:
     - `Entry.provenance`: deduplicated union of eligible assertions on the entry (`pos_assertion_id`, entry annotations) + canonical `Form` (`headword`) assertion.
     - `Sense.provenance`: deduplicated union of eligible assertions on the sense's promoted `components`, `examples`, and sense-subject assertions (guaranteed non-empty because every promoted sense requires `>= 1` accepted non-`unparsed` component).
6. **Finite lookup vocabularies (`unknown region` / `unknown register` / POS / property / relation codes)**:
   - `contracts/lookup.md:175` requires exact errors `lexicon: unknown region '<id>'` and `lexicon: unknown register '<id>'`, validated deterministically after unknown/unavailable pack checks.
   - Neither `lexicon/dictionary/` nor `schemas/lexicon/` currently declares a closed finite vocabulary file.
   - **Required fix**: Introduce a canonical declarative registry `lexicon/dictionary/vocabularies.toml` (covering valid `region` codes including geographic parent closure, `register` codes, `part_of_speech` tags, `annotation` property codes, and `relation` codes matching `^[A-Za-z][A-Za-z0-9_-]*$`) consumed by `T040`/`T041`, `build_lexicon.rs` (`T046`), and `src/lexicon/mod.rs` (`T052`/`T054`).

### 2.2 Data & Licensing Separation Audit

- **Pure Rust Engine vs. Host Tooling**: `crates/tamil-toolkit` MUST remain 100% pure Rust (`#![forbid(unsafe_code)]`, offline `build.rs` into `OUT_DIR`, zero Python fallback, zero reads of `data/sources/` or `data/curation/` at build or runtime).
- **Editorial Validation Path Conflict (`tools/lexicon_validate.py` & `check_source_unicode.py`)**:
  - `tools/mcp-tamil-oracle/check_source_unicode.py:50-51` restricts `ROOT/lexicon/**` to `.toml`, `.csv`, `.md` (compatible with promoted CSV/TOML/notice docs; compiled `.fst` and posting tables MUST reside only in Cargo `OUT_DIR`).
  - However, `tools/lexicon_validate.py:check_curated_csv` validates `ROOT/lexicon/dictionary/` using all 21 editorial schema names in `schemas/lexicon/`. Before `T044` writes `lexicon/dictionary/`, `check_curated_csv()` MUST recognize canonical promoted layout (`packs.toml`, `vocabularies.toml`, canonical CSVs, `attribution.csv`/`sources` metadata) vs. editorial workspaces (`data/curation/*`) without weakening decoded UTF-8 / `json-string-utf8-v1` / scalar-exception checks.
- **Crate Source-Tarball Licensing Hazard (`crates/tamil-toolkit/Cargo.toml` + `tools/release_files.py`)**:
  - `crates/tamil-toolkit/Cargo.toml:10` sets MIT license (`license.workspace = true`). `contracts/packs.md` flags that disabled Cargo features do **not** strip files matching `package.include` from `.crate` source tarballs on `crates.io`.
  - If `T047` adds `lexicon/dictionary/**` to `crates/tamil-toolkit/Cargo.toml` `include`, any `CC-BY-SA-4.0` (e.g., Wiktionary candidate) or non-MIT pack checked into `lexicon/dictionary/` will be bundled into the MIT-licensed `.crate` sdist.
  - **Required boundary**:
    1. Keep non-MIT / unreviewed datasets out of `lexicon/dictionary/` and `crates/tamil-toolkit/Cargo.toml` until license terms and attribution packaging are explicitly cleared (`T038`, `T066`, `T070`).
    2. Upgrade `tools/release_files.py` (currently flat `lexicon/<file>.toml` map) to explicitly enumerate approved `lexicon/dictionary/**` files AND inject per-source/pack attribution/license/disclaimer notices into `crates/tamil-toolkit/THIRD_PARTY_NOTICES.md` and `bindings/*/THIRD_PARTY_NOTICES.md`.
    3. Verify both enabled and default (features-off) archives in `T048` and `T069` (`just release-check` / `tools/release.py`).

---

## 3. Tooling Reuse vs. Exact Implementation Gap Map (`T038`–`T070`)

### 3.1 Host Python Tooling (`tools/lexicon*.py`)

| Module / Entrypoint | Existing Reusable Surface | Exact Gaps to Close | Tasks |
|---|---|---|---|
| `tools/lexicon.py` | CLI dispatch (`inventory`, `stage`, `select-pilot`, `curate`, `review-ingest`, `pilot`, `validate`), `native_inspect`, `allocate_id`, `json_text`/`data_json`, `safe_output`. | Register `promote` (`T041`) and `export-cldf` (`T043`) subcommands with exit codes `0`/`1`/`2` matching `contracts/curation.md`. | `T041`, `T043` |
| `tools/lexicon_ingest.py` | Append/idempotent conflict-checked ingest for `sources`, `evidence`, `decisions`. | Support ingesting `pack_members`, `scopes`, `labels`, `unicode_exceptions`, `changes`, `successors` (`--table` choices) so external review packages can land cleanly without manual CSV surgery. | `T039` prep / `T040` |
| `tools/lexicon_review.py` | `claim_revision`, `evidence_hash`, `eligibility`, `validate_history`, `unicode_findings` (native Rust `native_inspect`). | Enforce `^[A-Za-z][A-Za-z0-9_-]*$` ID compatibility check for promotable claims/labels/actors, and reject `"restricted"` / non-`"permitted"` `reuse_state` + missing `attribution_text_json`. | `T040` |
| `tools/lexicon_pilot.py` | `select_pilot`, `pilot`, early fail-closed `release_guard` (counts claim `eligibility()`, always blocks with `FULL_RELEASE_CLOSURE_NOT_IMPLEMENTED`). | Complete `release_guard` (`T040`): invoke `validate_relations` + `validate_history`, enforce pack-level closure (active identity, canonical written `headword` form, `part_of_speech`, >=1 active sense with >=1 eligible non-`unparsed` component, exclusion of quarantined/ineligible annotations & entries with 0 remaining senses, cross-pack relation target closure or `evidence_only_external` omission, conflict detection across multi-pack `entry_id`s, non-empty attribution/reuse closure). Preserve existing L2 zero-eligible exit-1 test behavior. | `T040` |
| `tools/lexicon_validate.py` | `validate_projection`, `check_curated_csv` (called by `tools/mcp-tamil-oracle/check_source_unicode.py`). | Add canonical promoted-pack directory validation (`packs.toml`, `vocabularies.toml`, pack CSVs) alongside existing 21-table editorial workspace validation so `T044` populates `lexicon/dictionary/` without breaking `just check-unicode`. | `T040`, `T044` |
| New `tools/lexicon_promote.py` (or inside `lexicon_pilot.py`) | Reuse `read_rows`, `write_rows`, `eligibility`, `atomic_json`, `safe_output`, `digest`. | Implement deterministic `promote` into `target/lexicon/core-canonical/` (`T041`): filter strictly eligible rows for requested pack(s), compute `Entry.provenance` & `Sense.provenance`, project `packs.toml` + `vocabularies.toml` + attribution manifest, fail on canonical human-edit conflicts, never mutate `data/sources/` or `data/curation/`. | `T041` |
| New `tools/lexicon_cldf.py` + `schemas/lexicon/cldf/` + `pyproject.toml` | Reuse `table_rows` / `read_rows`, `json_string_utf8_v1` decode. | Pin offline CLDF validator (`pycldf` + `csvw` in `pyproject.toml` `[project.optional-dependencies] dev` + `uv.lock`) and local CLDF 1.3 schemas/digests in `schemas/lexicon/cldf/` (`T042`); implement `export-cldf --check` -> `target/lexicon/cldf/` (`T043`) with CSVW metadata, BibTeX, standard Wordlist/Dictionary tables + custom provenance/review extension tables. | `T042`, `T043` |
| `tools/lexicon_bench.py` (new) | Call `tools.lexicon`, `tools.lexicon_stage`, `tools.lexicon_validate`, compiled Rust CLI / FFI. | Benchmark full 307,243-row `structural` pipeline (`< 60s`, `< 512 MiB` peak RSS) and 10,000-query warm Rust `lookup` (`p95 < 10 ms`) + cold start + payload sizes -> `target/lexicon/benchmarks.json`. | `T063` |

### 3.2 Rust Engine, Build Script, Dispatcher, CLI & Bindings

| File / Symbol | Existing Surface | Exact Code Changes Required | Tasks |
|---|---|---|---|
| `Cargo.toml`, `Cargo.lock` | Workspace `0.1.0-alpha.7`, MSRV `1.85`; lacks `csv`/`fst`. | Add `csv = "1"` and `fst = { version = "0.4.7", default-features = false }` to `[workspace.dependencies]`; update `Cargo.lock` (`--locked` gates require locked resolution). | `T045` |
| `crates/tamil-toolkit/Cargo.toml` | Ranks & public `dependencies` compliant (`tools/release_policy.py` Rank 5); no `[features]` or `[build-dependencies]`. | Add `[features]`: `default = []`, `lexicon-core = ["dep:fst"]`, `lexicon-terminology = ["dep:fst"]`, `lexicon-names-taxa = ["dep:fst"]`, `lexicon-regional = ["dep:fst"]` (`fst` optional dependency). Add `[build-dependencies]`: `csv.workspace = true`, `fst.workspace = true`, `serde.workspace = true`, `serde_json.workspace = true`, `toml.workspace = true`, `tamil-core.workspace = true`, `tamil-norm.workspace = true` (check `release_policy.py` DAG: Ranks 0/1 < Rank 5). Extend `include` for `lexicon/dictionary/**` ONLY after `T044`/`T047` licensing clearance. | `T045`, `T047` |
| `crates/tamil-toolkit/build.rs` & `build_lexicon.rs` | None (`crates/tamil-toolkit` has no build script yet). | Compile package-local `lexicon/dictionary/` (`packs.toml`, `vocabularies.toml`, promoted pack CSVs) strictly into `OUT_DIR` ONLY when corresponding `lexicon-*` features are active; emit `cargo:rerun-if-changed=...`; normalize keys via `tamil_norm::normalize_nfc`; verify unique sorted keys; write `fst::MapBuilder` bytes + fixed-width little-endian posting offsets/payload tables + pack metadata/manifest (`compatible_schema_version`, SHA-256). Fail build on invalid/non-NFC/stale/inconsistent pack data. Keep empty stub generation when all `lexicon-*` features are disabled. | `T046` |
| `crates/tamil-toolkit/src/lexicon/mod.rs` (new) | None (`#![forbid(unsafe_code)]` crate root). | Public types (`LookupRequest`, `LookupOptions`, `LookupResponse`, `PackInfo`, `Entry`, `Form`, `Sense`, `TextItem`, `Relation`, `Scope`, `Provenance`, `Acceptance`, etc.); `include_bytes!(concat!(env!("OUT_DIR"), ...))` behind `#[cfg(feature = "...")]`; `lookup(word, &options)` and `packs()`; exact validation order & all 8 exact `lexicon: ...` errors from `contracts/lookup.md:168-177`; 65,536 UTF-8 byte cap; NFC via `tamil_norm::normalize_nfc`; multi-pack posting merge + conflict check (`incompatible pack versions`) + stable `entry_id` & `display_order`/`sense_id` ordering; `region`/`register` truth table (attested + `unrestricted`, excluding `unknown`, child->parent geography without parent->child, sense overrides, drop entries with 0 remaining senses). | `T052`–`T055` |
| `crates/tamil-toolkit/src/lib.rs` | `OPERATIONS` (L809–909), `execute()` dispatcher (L1754+ / L2052 `execute_json`). | Append `"lexicon_lookup"` and `"lexicon_packs"` to `OPERATIONS`; route in `execute()` returning exact `Result<Value, String>` error channel; ensure `lexicon_packs` succeeds even when `compiled: false` / zero features enabled, while `lexicon_lookup` returns `lexicon: pack unavailable '<id>'` for disabled known packs. | `T056` |
| `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` | Usage table (L22–32), command match (L1293). | Add `lexicon` command group: `lexicon lookup <WORD> [--pack ID]... [--region CODE]... [--register CODE]... [--json]` and `lexicon packs [--json]`, preserving exact verbatim string quoting and JSON/exit parity with `execute()`. | `T057` |
| `bindings/python/` | `Cargo.toml`, `src/lib.rs`, `python/tamil_toolkit/__init__.py`, `__init__.pyi`. | Forward optional features (`lexicon-*`) on `tamil-python` Cargo manifest if configured per build profile; add `lexicon_lookup(word, options=None)` & `lexicon_packs()` thin wrappers + `TypedDict`s in `__init__.pyi`. | `T058` |
| `bindings/js-wasm/` | `Cargo.toml`, `src/api.ts`, `src/index.ts`, `src/web.ts`. | Forward optional features on `tamil-wasm`; add typed interfaces (`LookupOptions`, `LookupResponse`, `PackInfo`, etc.) in `api.ts`; export `lexicon_lookup` & `lexicon_packs` in BOTH `index.ts` (Node) and `web.ts` (browser). | `T059` |
| `bindings/dart-flutter/` | `rust/Cargo.toml`, `lib/tamil_toolkit.dart`. | Forward optional features on `tamil-dart`; add typed Dart classes + `lexiconLookup` / `lexiconPacks` helpers calling `execute({'op': ...})` over existing C ABI (`tamil_toolkit_call`). | `T060` |
| Gate / Smoke / Release Scripts | `tools/tasks.py`, `tools/release.py`, `tools/release_files.py`, `tools/release_smoke/*`. | `release_files.py`: directory sync for `lexicon/dictionary/**` + generated attribution notices (`T047`). `tasks.py` & `release.py`: profile feature-forwarding option for rebuild/parity/Dart/isolated consumer builds without disabling default zero-payload checks (`T061`). Add lexicon assertions in `release_smoke/*` (`T069`). | `T047`, `T061`, `T069` |

---

## 4. User-Blocking External Decisions vs. Independent Engineering Work

### 4.1 User / Owner Blocking Decisions (Cannot Be Syntheticized or Inferred)
1. **`T038` Source & Reuse Evidence Recovery**: Real source editions, snapshot checksums/locators, and explicit redistribution/reuse basis (`reuse_state = "permitted"`) in `sources.csv` & `evidence.csv` (whether from `data/curation/tamil-lexicon/` recovered sources or cleared `CC-BY-SA-4.0` Wiktionary snapshots).
2. **`T039` Genuine Human Review + Real Homograph Assignment**: Real human acceptance decisions (`accepted_human` with reviewer identity/date or verified automated basis where eligible), open finding resolution (`wiktionary-candidate` has `49` open findings and `20` `needs_review` items), and explicit `pack_members.csv` curation containing a real homograph.
3. **`T042` Offline CLDF Dev Dependency Selection**: Confirm adding pinned `pycldf` / `csvw` (dev-only) to `pyproject.toml` & `uv.lock` alongside checked-in CLDF 1.3 schema JSON/digests under `schemas/lexicon/cldf/`.
4. **`T066` / `T068` / `T070` Activation, License-Packaging & Release Decisions**:
   - Explicitly approving `tests/golden/lexicon_lookup.jsonl` transition from `planned` -> `active` (`T068`) only after L3/L4 proof.
   - Explicitly deciding whether any `CC-BY-SA-4.0` pack can be included inside MIT-licensed `crates.io` / PyPI / npm archives (`crates/tamil-toolkit/Cargo.toml` `include`, `THIRD_PARTY_NOTICES.md`) vs. separate distribution (`T047`/`T066`/`T070`).

### 4.2 Independent Engineering Work Safe to Execute Before Approval
All tooling and schema-consistency prep below relies solely on **synthetic** test workspaces in `pytest` (never promoting synthetic fixtures to `lexicon/dictionary/`, never altering the 12 frozen intake files, never marking `T038`/`T039` or any `T044`+ runtime pack active):
- Schema discrepancy resolution (`directionality`, ID regex/actor projection, finite `vocabularies.toml` specification in `docs/specs/lexicon-v0.1.md`, `Entry`/`Sense` provenance rules).
- `review-ingest` table expansion (`pack_members`, `scopes`, `labels`, `unicode_exceptions`, `changes`, `successors`).
- **`T040`–`T043`**: Failing L3 tests in `tests/harness/test_lexicon_packs.py` FIRST -> complete `validate --mode release`, deterministic `promote` (`target/lexicon/core-canonical/`), `T042` offline CLDF schemas/validator, `export-cldf --check` -> `target/lexicon/cldf/`, plus `lexicon_validate.check_curated_csv` canonical layout support.
- *Wait-gated at `T044`*: Populating `lexicon/dictionary/` and authoring sourced real-data `tests/golden/lexicon_lookup.jsonl` (`T044`) MUST wait for actual `T038` + `T039` approval, and Rust lookup implementation (`T050`–`T057`) MUST follow `T044` so source-backed goldens strictly precede algorithms.

---

## 5. Dependency-Ordered Waves & Disjoint Ownership Boundaries

Follow strict **tests-first** order (`T040/T041/T043` harness tests before code; `T044` spec/goldens before `T050`–`T057`; `T050`–`T051` Rust/contract tests before `T052`–`T060`). **Never overlap parallel file writers on the same file, and never overlap Rust/PyO3/WASM parity with Dart/DLL tests on Windows.**

### Wave A — Pre-Approval Schema Closure & L3 Tooling Tests-First (No `data/` or `lexicon/dictionary/` edits)
- **Step A1 (Sequential — Shared Spec/Schema Alignment)**:
  - Resolve Section 2.1 schema inconsistencies (`lookup-response.schema.json` / `lexical.schema.json` / `common.schema.json` / `lookup.md`) and draft the schema/vocabulary sections of `docs/specs/lexicon-v0.1.md`.
- **Step A2 (Parallelizable — Disjoint Ownership)**:
  - **Worker A2a (`tools/` host L3)**: Extend `tests/harness/test_lexicon_packs.py` (failing `T040`/`T041` closure/promotion tests FIRST) -> extend `tools/lexicon_ingest.py`, `tools/lexicon_pilot.py` (`release_guard`), `tools/lexicon_validate.py`, `tools/lexicon_promote.py`, `tools/lexicon.py` (`T040`, `T041`).
  - **Worker A2b (`CLDF` offline schemas/dev-deps — after `T042` dep sign-off)**: Pin `pyproject.toml` / `uv.lock` dev CLDF validator + `schemas/lexicon/cldf/` (`T042`). Then (after A2a finishes `test_lexicon_packs.py` promotion fixtures) add failing CLDF tests in `tests/harness/test_lexicon_packs.py` and implement `tools/lexicon_cldf.py` + `export-cldf` CLI hook (`T043`).

### Wave B — External Gate & Real Candidate Promotion (`T038` -> `T039` -> `T044`)
*Blocked until user/owner supplies `T038` & `T039` evidence and `CC-BY-SA-4.0` / primary licensing decision:*
- **Step B1 (`T038` + `T039`)**: Ingest real `sources`, `evidence`, `decisions`, `pack_members` via `review-ingest` (respecting sibling worker's prepared evidence & real homograph); resolve/document open findings.
- **Step B2 (`T040`–`T041` real validation)**: Run `validate --mode release` (exit 0) and `promote` into `target/lexicon/core-canonical/`.
- **Step B3 (`T044` — Goldens Preceding Runtime)**: Integrate reviewed canonical CSV/TOML + notices into `lexicon/dictionary/` (keeping `data/sources/` and `data/curation/` untouched); finalize `docs/specs/lexicon-v0.1.md`; add source-backed escaped `tests/golden/lexicon_lookup.jsonl` (validated against `lookup-response.schema.json`); extend `tests/golden/schema.json`; register suite as `"status": "planned"` in `tests/golden/manifest.json`.

### Wave C — Offline Pack Compilation & L3 Checkpoint (`T045` -> `T046`–`T048` -> `T049`)
- **Step C1 (`T045` — Sequential Crate/Lock Prep)**: Add `csv` & `fst` to `Cargo.toml` / `Cargo.lock` and feature flags + build-deps to `crates/tamil-toolkit/Cargo.toml`.
- **Step C2 (Parallelizable — Disjoint Ownership)**:
  - **Worker C2a (Rust Build Compiler — `T046`, Rust tests in `T048`)**: Author `crates/tamil-toolkit/build.rs`, `crates/tamil-toolkit/build_lexicon.rs`, and `crates/tamil-toolkit/tests/lexicon_pack.rs` (byte-identical FST/posting generation in `OUT_DIR`, zero-payload default feature checks, all feature subsets).
  - **Worker C2b (Release Sync & Archive Checks — `T047`, harness pack tests in `T048`)**: Update `tools/release_files.py`, regenerate `crates/tamil-toolkit/lexicon/dictionary/` & `THIRD_PARTY_NOTICES.md` (`just sync-release-files`), and add Python archive-inspection tests to `tests/harness/test_lexicon_packs.py`. *(Sync `crates/tamil-toolkit/Cargo.toml` `include` edit in a single owner step cleanly before C2b verification.)*
- **Step C3 (`T049` — Root Sequential Checkpoint)**: Clean two-run `promote` + `cargo build` reproducibility check, CLDF round-trip verification (`T043`), `just check-release-policy`, `just check-release-files`, `just check-unicode`, record `docs/status.md` & `target/lexicon/l3-acceptance.json`.

### Wave D — Pure-Rust Runtime & Dispatcher (`T050`–`T051` -> `T052`–`T057`)
- **Step D1 (`T050` & `T051` in Parallel — Tests First, Disjoint Ownership)**:
  - `T050`: Add failing Rust tests in `crates/tamil-toolkit/tests/lexicon.rs` consuming `T044` expectations + `lookup-response.schema.json` validation.
  - `T051`: Add contract/validation-order/error tests in `tests/harness/test_lexicon_runtime.py` + `tests/reference/lexicon/runtime/`.
- **Step D2 (`T052`–`T055` Sequential — Owned by Rust Core)**: Implement `crates/tamil-toolkit/src/lexicon/mod.rs` iteratively (`mod.rs` types & artifact readers -> NFC matching & multi-pack aggregation -> region/register filter truth table -> response/provenance projection).
- **Step D3 (`T056` then `T057` Sequential)**: Register `lexicon_lookup` / `lexicon_packs` in `crates/tamil-toolkit/src/lib.rs` (`T056`), then add CLI `lexicon lookup` / `lexicon packs` handlers in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs` (`T057`).

### Wave E — Parallel Binding Adapters -> Sequential Parity & Benchmarks (`T058`..`T060` -> `T061`–`T065`)
- **Step E1 (`T058`, `T059`, `T060` in Parallel — Strict Disjoint Directories)**:
  - `T058`: `bindings/python/` (`Cargo.toml`, `python/tamil_toolkit/__init__.py`, `__init__.pyi`).
  - `T059`: `bindings/js-wasm/` (`Cargo.toml`, `src/api.ts`, `src/index.ts`, `src/web.ts`).
  - `T060`: `bindings/dart-flutter/` (`rust/Cargo.toml`, `lib/tamil_toolkit.dart`).
- **Step E2 (`T061` + `T063` tooling)**: Wire profile feature forwarding & parity test harnesses in `tools/tasks.py`, `tools/release.py`, `bindings/*/tests/` (`T061`); implement `tools/lexicon_bench.py` (`T063`).
- **Step E3 (`T062`–`T065` Sequential Root Execution — Windows DLL & UV Discipline)**:
  1. Rebuild/test Python & Node/Browser WASM via `uv run --locked python tools/tasks.py test-parity` (with planned suite flag while `T068` is pending, plus default no-pack negative checks; **`maturin` requires the `uv` environment**).
  2. **Separately (never concurrently with PyO3/Cargo)**: run `just test-dart` so Windows does not lock `tamil_toolkit_ffi.dll` / `_native.pyd`.
  3. Record `target/lexicon/parity/`, run `tools/lexicon_bench.py` -> `target/lexicon/benchmarks.json`, run focused regressions -> `target/lexicon/us3-proof.json`, and record `docs/status.md` + `target/lexicon/l4-functional.json`.

### Wave F — Polish, Full Gates, Activation Decision & Release Smoke (`T066`–`T070`)
- **Step F1 (`T066` Docs — Disjoint from test execution if non-code inputs stay stable)**: Update `specs/021-lexicon-curation/quickstart.md`, `lexicon/README.md`, `data/sources/README.md`, `CHANGELOG.md` (preserving `ROADMAP.md` & `docs/specs/architecture-roadmap.md` ranks/phases).
- **Step F2 (`T068` Explicit Owner Decision -> `T067` Gates -> `T069` Archive Consumers -> `T070` Closure)**:
  - Only upon explicit owner approval (`T068`), flip `tests/golden/lexicon_lookup.jsonl` in `tests/golden/manifest.json` from `"planned"` to `"active"` and record release-scope review in `docs/status.md`.
  - Root executes sequentially in `uv run --locked`:
    1. `just agent-post-edit` (`check-release-policy`, `check-unicode`, `check-release-files`, `cargo fmt --check`, `cargo check --workspace --locked`)
    2. `just agent-pre-stop-gate` (inside `uv run --locked` so `maturin` succeeds)
    3. `just test-dart` (after parity/cargo exits to avoid Windows DLL locks)
    4. `just release-check` (`tools/release.py` + `tools/release_smoke/*` across `.crate`, Python wheel/sdist, npm Node/browser tarballs, inspecting disabled-feature and enabled-feature packages separately -> `target/lexicon/archive-proof.json`)
  - Finalize `docs/status.md`, `CHANGELOG.md`, `specs/021-lexicon-curation/spec.md`, and `tasks.md` checkboxes strictly matching verified gates (`T070`). No commit or registry publish.
