# Curation and Promotion Contract v1

**Status**: Proposed interfaces for implementation; none of these commands is
implemented by the planning step. Run the existing audit today; run the proposed
interfaces only after their tasks are implemented. See [data model](../data-model.md).

## Host tool boundary

`tools/lexicon.py` is the single proposed host entry point. It owns file I/O,
CSV/JSON/TOML codecs, ID bookkeeping, source/review manifests, structural schema
validation, and deterministic reports. Linguistic inspection calls the rebuilt
native Rust adapter; a missing adapter is a clear prerequisite error, never a
Python normalization/segmentation fallback. Pure inventory/quarantine acceptance
must not require an invented linguistic result or an approved data pack.

| Subcommand | Inputs and output | Mutation behavior |
|---|---|---|
| `inventory --source PATH --output PATH` | Strict CSV/file scan, 12 file digests and all record locators/digests; default source is the frozen bundle | Only output staging under the chosen target directory |
| `stage --inventory PATH --workspace PATH` | Idempotent proposed claims, identity allocations, source leads, findings and dispositions | Explicitly writes only editorial workspace; conflicting existing revisions fail |
| `pilot --workspace PATH --selection PATH --output PATH` | Validate a committed deterministic pilot selection and report FR-019 minima and disposition completeness | Writes report only; does not approve claims |
| `validate --workspace PATH --mode structural --selection PATH --output PATH` | Schema, IDs, references, source snapshot hashes, selected-record accounting, review queues and L2 status | Read-only inputs; report output only |
| `validate --workspace PATH --mode release --pack ID --output PATH` | Nonempty pack, assertion eligibility, current review/evidence hashes, source/reuse/attribution, scope and reference closure | Read-only inputs; fail on any public-ineligible selected assertion |
| `promote --workspace PATH --pack ID --output PATH` | Generate eligible canonical tables and source/terms manifests after release validation | Explicit command writes declared canonical staging; no registry upload, automatic human review, or original-data edits |
| `export-cldf --canonical PATH --pack ID --output PATH --check` | Nonempty approved pack to CLDF with custom extensions, pinned schema validation and round-trip report | Only chosen generated export directory |

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
