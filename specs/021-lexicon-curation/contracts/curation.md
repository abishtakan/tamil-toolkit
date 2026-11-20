# Curation and Promotion Contract v1

**Status**: L1/L2 structural curation interfaces (`inventory`, `stage`,
`select-pilot`, `curate`, `review-ingest` across 9 tables, `pilot`,
`validate --mode structural`, and the fail-closed `validate --mode release`
guard in `tools/lexicon.py`, plus `tools/lexicon_proof.py` /
`tools/lexicon_validate.py`) are implemented and L2-verified
(`../../../target/lexicon/l2-acceptance.json`). L3 commands (`validate --mode release`
nonempty closure, `promote`, and `export-cldf --check`) are implemented and
L3-verified on the human-approved six-entry / 19-sense Wiktionary core
(`../../../target/lexicon/l3-acceptance.json`, canonical manifest
`4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`). The
307,243-record historical intake under `data/curation/tamil-lexicon/` remains
quarantined (`0` eligible assertions). See [data model](../data-model.md).

## Host tool boundary

Large dictionary CSV uses `json-string-utf8-v1`: visible Tamil remains UTF-8,
while JSON-required escapes and audit-sensitive controls remain reversible.
Golden test/scalar diagnostics retain explicit escapes. Canonical hash
serialization is separate from storage encoding. Under the
[storage decision](../../../docs/decisions/lexicon-text-storage.md), uncommitted
legacy staging was deleted with no legacy archive or migration command retained;
the clean UTF-8 rebuild, exact decoded source-content proof
([source-content-proof-final.json](../../../target/lexicon/source-content-proof-final.json)),
pre-projection clean replay ([us1-proof.json](../../../target/lexicon/us1-proof.json)),
and L2 structural acceptance ([l2-acceptance.json](../../../target/lexicon/l2-acceptance.json))
are complete, while L3 source/review/pack promotion remains pending.

`tools/lexicon.py` is the single host entry point. It owns file I/O,
CSV/JSON/TOML codecs, ID bookkeeping, source/review manifests, structural schema
validation, and deterministic reports. Linguistic inspection calls the rebuilt
native Rust adapter; a missing adapter is a clear prerequisite error, never a
Python normalization/segmentation fallback. Pure inventory/quarantine acceptance
does not require an invented linguistic result or an approved data pack.

| Subcommand | Status & inputs/output | Mutation behavior |
|---|---|---|
| `inventory --source PATH --output PATH` | **Implemented (L1)**: strict CSV/file scan, 12 file digests and all record locators/digests; default source is the frozen bundle | Only output staging under the chosen target directory |
| `stage --inventory PATH --workspace PATH` | **Implemented (L1)**: idempotent proposed claims, identity allocations, source leads, findings and dispositions | Explicitly writes only editorial workspace; conflicting existing revisions fail |
| `select-pilot --selection PATH [--source PATH]` | **Implemented (L2)**: one-time creation of deterministic coverage-first `pilot-selection.toml`; checks rather than replacing an existing selection | Writes selection TOML only if absent; errors on conflict with existing file |
| `curate --workspace PATH --selection PATH` | **Implemented (L2)**: lossless unapproved structural projection of selected records into `entries`/`forms`/`senses`/`texts`/`relations`/`scopes`/`labels`/`findings` | Explicitly writes editorial workspace tables; conflicting existing revisions fail |
| `review-ingest --workspace PATH --table sources\|evidence\|decisions\|pack_members\|scopes\|labels\|unicode_exceptions\|changes\|successors --input PATH` | **Implemented (L2/L3)**: append-only ingestion of externally supplied curation/review CSV records across the 9 supported tables | Writes target workspace table only; rejects inputs inside workspace or stale revisions |
| `pilot --workspace PATH --selection PATH --output PATH` | **Implemented (L2)**: validate a committed deterministic pilot selection and report FR-019 minima and disposition completeness | Writes report only; does not approve claims |
| `validate --workspace PATH --mode structural --selection PATH --output PATH` | **Implemented (L2)**: schema, IDs, references, source snapshot hashes, selected-record accounting, review queues and L2 status (exit `0` on L2) | Read-only inputs; report output only |
| `validate --workspace PATH --mode release [--pack ID] --output PATH` | **Implemented (L2/L3)**: fail-closed exit `1` on `0` eligible assertions (L2 guard) and nonempty pack, revision/evidence review validity, source/terms closure, and dependency checks (exit `0` on L3-eligible workspace; default `--pack core`) | Read-only inputs; fails on any zero-eligible or public-ineligible selected assertion |
| `promote --workspace PATH [--pack ID] [--output PATH] [--report PATH]` | **Implemented (L3)**: generate deterministic eligible canonical tables (`.csv`, `.toml`, `.md`) and source/terms manifests after release validation (default `--pack core`, default output `target/lexicon/<pack>-canonical`) | Explicit command writes declared canonical staging; no registry upload, automatic human review, or original-data edits |
| `export-cldf --canonical PATH --pack core\|terminology\|names_taxa\|regional --output PATH [--check] [--report-output PATH]` | **Implemented (L3)**: nonempty approved pack to offline CLDF 1.3 with custom extensions, pinned `pycldf==2.2.0`/`csvw==4.2.0` schema validation (`schemas/lexicon/cldf/`), and lossless round-trip report (`--check`) | Only chosen generated export directory (plus optional `--report-output`) |

No command infers source URLs or permissions from labels; no command sets
`accepted_human` on behalf of an automated agent. Source verification and reuse
decisions arrive as explicit evidence records. Staging a claim is not promoting it.

Every command resolves input/output paths before writing, rejects outputs inside
the frozen source directory, and rejects output overlap with inputs unless the
command explicitly targets its editorial workspace. It never silently replaces
conflicting human edits. Generate into a sibling staging directory, validate,
and replace only intended outputs; a failure leaves the last valid dataset
usable. Recover by rerunning identical inputs, not by deleting intake/history.
No execution, downloads, remote services, or SQL are encoded in data cells.

## Reports, exit codes, and deterministic ordering

Reports use JSON with `schema_version`, command/mode, dataset/selection versions,
input digests, record and disposition counts, sorted findings, and separate
`l2_structural_accepted`, `l3_pack_eligible`, and `runtime_verified` indicators.
The last indicator is absent/null unless supplied by an actual verified runtime
manifest; the structural validator cannot invent it. Each finding includes a
stable code, severity, entity/record ID, field or scalar positions, and actionable
reason. Include no build clock, machine path, random IDs, or full source text
in a public manifest. Local diagnostics can reference frozen records by locator.

Exit 0 means the requested mode passed, not that all later modes passed. Exit 1
means the requested validation/acceptance failed; exit 2 means invalid command
arguments, inaccessible inputs, hash mismatch, missing prerequisites, or unsupported
schema/version. Diagnostics go to stderr; a requested JSON report is written
only to its output path. Results are stable for unchanged input and tool versions.

L2 validation may exit 0 with `eligible_assertions = 0` and every sampled record
quarantined. Its report must say why and must not use `published`, `active`, or
`runtime_verified=true`. Full-bundle structural accounting requires 307,243 CSV
record dispositions; pilot validation applies only to the explicit selected set
and linked dependencies. Never imply full import accounting from a pilot report.

Before the L2 checkpoint, implement an actual fail-closed release guard using
computed eligibility: a zero-eligible/all-quarantine candidate returns validation
exit 1 with an eligibility/nonempty-pack finding. Unsupported-command or missing-
dependency exit 2 is not evidence of correct release rejection. Positive release
acceptance, promotion and CLDF tests are introduced with their later implementations;
no failing future test, skip, xfail or weakened gate is carried across L2.

## Pilot selection

Commit `data/curation/tamil-lexicon/pilot-selection.toml`, listing snapshot/record
IDs and purpose codes. Deterministic selection uses an explicit coverage-first
list drawn from audit findings and imported categories, then fills remaining
minima in stable record-ID order. Re-running selection checks, rather than
silently replacing, an existing reviewed selection. Include all meanings and
relevant relationship evidence needed to review each selected primary entry;
linked evidence does not replace the minimum counts for each source category.

Required minima are the specification's 100 primary entries, 20 records from
each of seven secondary CSVs, at least 10 homographic spellings with every
associated entry, 10 verbs, 10 mixed-sense records, 10 technical MWEs, 10 regional
records spanning TN and Jaffna, and every audit Unicode/count-disagreement class.
Class labels describe why rows were sampled, not acceptance of their linguistic
claims. The sample may grow to satisfy complete homograph and anomaly coverage.
Every selected record has exactly one validated disposition. Pending evidence
requires quarantine/exclusion with an explicit reason and retained history.

## Source and review enforcement

An automatic acceptance decision is invalid unless its exact claim revision is
unchanged source text, fidelity is verified, the supporting source locator is
available, reuse/attribution checks pass, and ambiguity/findings are resolved.
A human acceptance decision is invalid without a real recorded human actor,
date, evidence and exact revision hash. Human review cannot waive unknown reuse
basis. Human corrections/inferences are proposed and withheld until decided.

Source leads may be recovered incrementally. Approval of one source does not
approve all similarly named datasets. Pack generation selects eligible assertions
and required structural dependencies only; unknown optional fields remain absent
or explicitly unknown. It must fail rather than expose an ineligible definition
or relationship through an otherwise accepted headword. Full source terms and
attribution are packaged where required; data does not inherit the toolkit's MIT
license merely because it is bundled.

## Negative acceptance scenarios

- Altering any frozen source byte fails hash verification before staging.
- Repeating an unchanged stage/import produces the same IDs and no duplicate rows.
- Duplicate IDs, conflicting allocation keys, cyclic sense parents, invalid JSON
  cells, lone surrogates, broken references and stale exceptions fail validation.
- An all-quarantine pilot with validated sampling/accounting passes L2, fails
  release/export validation, and cannot activate a lookup suite.
- An automatically accepted changed/inferred/ambiguous claim fails release
  validation; a source label or imported confidence does not satisfy evidence.
- A stale review hash fails after a value or its evidence changes.
- A master-row disposition may merge into an existing lexical identity while
  retaining distinct unreviewed master-only claims; no second entry is created.
- Two identical inventories/promotions/exports have identical bytes; invalid
  reimports preserve prior valid data and pending manual decisions.
