# Data Model: Lexicon Dataset v1

**Status**: L1/L2 schemas (`schemas/lexicon/*.schema.json`) and editorial
workspace tables (`data/curation/tamil-lexicon/`) are implemented under
`json-string-utf8-v1` with L2 structural acceptance recorded in
[l2-acceptance.json](../../target/lexicon/l2-acceptance.json) (`0` eligible
assertions). `lexicon/dictionary/` remains unpopulated pending L3 source/review
approval. See [research](research.md) and
[validation/promotion contracts](contracts/curation.md).

## Locations and representation

- `data/sources/tamil-lexicon/`: original 12 files; never rewritten.
- `data/curation/tamil-lexicon/`: versioned identity registry, source leads,
  structural inventory, proposed claims, reviews, findings, and dispositions.
- `lexicon/dictionary/`: only L3-approved declarative pack projections; no
  unknown-rights source text, raw intake, unreviewed claims, executable code,
  FSTs, or JSON metadata. `schema.toml`, `vocabularies.toml`, and `packs.toml`
  declare version and field contracts. Machine schemas live separately in
  `schemas/lexicon/` and are synced into Cargo archives if builds need them.
- `target/lexicon/`: generated diagnostics, staging, CLDF export, and local
  indexes; generated output is not another edited source of truth.

CSV uses UTF-8 without BOM, comma delimiter, a fixed header, RFC-style quoting,
and LF endings. Table row order is bytewise primary-ID order. Multi-value
relationships use link rows, not delimiter-separated values. Free text is
stored with `json-string-utf8-v1`: each such CSV cell contains one valid JSON string
literal with visible Tamil retained as UTF-8. JSON-required and audit-sensitive
control scalars are escaped; ordinary non-ASCII letters are not expanded. CSV quoting is applied outside
JSON encoding. Decode CSV, then JSON exactly once; encode in the reverse order.
`value_json` may contain typed numbers, booleans or null as specified per field.
Objects/arrays are allowed only where schema explicitly declares their shape;
JSON object keys are ASCII schema keys, emitted in sorted order.

Missing values are explicit: `value_state = known | unknown | not_applicable`.
The latter two require JSON null. A known empty string is distinct from null
but is forbidden for headwords, definitions, IDs, and required locators. Do not
interpret literal `NA`, `null`, or backslash text as an implicit missing value.
Optional foreign-key columns use an empty CSV cell only as the documented null
foreign key; all required keys must be populated.

The uncommitted legacy escaped staging was deleted and rebuilt cleanly into
`json-string-utf8-v1` from the 12 immutable originals with the retained
namespace (`0` legacy payload archives or migration commands retained); exact
decoded payload equality ([source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json))
and pre-projection replay ([us1-proof.json](../../target/lexicon/us1-proof.json))
passed. See [storage decision](../../docs/decisions/lexicon-text-storage.md).
Storage encoding stays separate from canonical hash serialization; all rebuilt
claims start pending (`0` decisions, `0` eligible assertions) and cannot inherit
an acceptance.

## Identity rules

The dataset manifest fixes a UUID namespace. Imported lexical IDs use a typed
prefix and UUIDv5 of immutable allocation keys, such as a source-lineage ID and
legacy entry ID. The allocation key must not include spelling, POS, row order,
or filename version. Store the resulting identity registry permanently. Newly
curated entities and splits receive committed allocation keys and explicit
identity decisions; generation never improvises identities during a build.

A source-record ID instead identifies immutable evidence: snapshot digest,
logical CSV record ordinal (header is record 1), and row digest. Keep physical
line spans for diagnostics because quoted CSV cells may contain newlines.
Renumbering a future source snapshot never reallocates existing lexical IDs;
reconciliation either uses a verified stable legacy key or requests an explicit
mapping decision. Conflicting allocations are fatal, not last-write-wins.

Entries have distinct identities even with the same spelling and POS. Sense
order and display spelling are mutable properties, not primary keys. Merge and
split histories retain all retired IDs; lookup returns active identities only.

## Tables and metadata

`*` denotes a required field. Structural bookkeeping fields are not evidence
that the corresponding linguistic statement has been reviewed.

| Table / file | Fields and constraints |
|---|---|
| `dataset.toml` | `schema_version*`, `dataset_id*`, `dataset_version*`, `id_namespace*`, `text_codec*`, registry versions, pinned transformation versions, input inventory hash; no build wall clock or absolute paths |
| `snapshots.csv` | `snapshot_id*`, dataset ID, relative path, byte length, SHA-256, media type, logical row count where CSV; exactly the 12 intake files in this snapshot |
| `sources.csv` | `source_id*`, label/title JSON, publication/URL/edition/locator JSON, snapshot reference when available, retrieval-date state, extraction method/version, evidence verification state, reuse basis/state, attribution text/reference; unrecovered labels are leads with unknown evidence |
| `identities.csv` | `entity_id*`, kind, immutable allocation key, lifecycle (`active`, `merged`, `split`, `retired`), identity-decision reference; never a POS/spelling uniqueness constraint |
| `source_records.csv` | `record_id*`, snapshot ID, logical ordinal, physical-line span, legacy key JSON, raw-row digest; unique `(snapshot_id, ordinal)` |
| `dispositions.csv` | `record_id*` (one-to-one source record), disposition (`mapped`, `merged`, `split`, `excluded`, `quarantined`), structural state (`pending`, `validated`), reason code/note, finding-set hash, method/version; no unexplained exclusions |
| `record_targets.csv` | `record_id*`, `entity_id*`, target role; unique triple. Mapped/merged need at least one target; split needs at least two; excluded/quarantined have no approved target mappings but may link proposed claims through evidence |
| `entries.csv` | `entry_id*`, language/variety ID, canonical form ID, optional POS assertion ID, structural kind, revision; active approved entry requires a canonical written form and at least one accepted sense |
| `forms.csv` | `form_id*`, `entry_id*`, representation (`written`, `romanization`, `ipa`), role (`canonical`, `variant`), text assertion ID, convention assertion ID when relevant; exactly one approved canonical written form per entry |
| `senses.csv` | `sense_id*`, `entry_id*`, display order, optional parent sense ID; parent must belong to the same entry and hierarchy must be acyclic |
| `texts.csv` | `text_id*`, owner entry/sense ID, component (`definition`, `gloss`, `translation`, `example`, `citation`, `unparsed`), language ID, text assertion ID, optional paired translation ID, optional cited source locator; unparsed content never masquerades as approved definition |
| `relations.csv` | `relation_id*`, typed source/target entity IDs (`entry` or `sense`), relation-code assertion ID, directionality, optional inverse relation ID; no silent target choice by headword; unresolved proposals stay in editorial workspace |
| `assertions.csv` | `assertion_id*`, subject kind/ID, property code, `value_state*`, `value_json*`, origin (`verbatim_source`, `correction`, `inferred`, `derived`, `editorial`), source-fidelity state, ambiguity state, algorithm/convention reference, imported status/confidence JSON, claim revision SHA-256 |
| `evidence.csv` | `assertion_id*`, source ID, optional source-record ID, exact locator JSON, evidence role (`supports`, `contradicts`, `transcribes`), extraction version/digest; at least one verified supporting source for a public claim |
| `decisions.csv` | `decision_id*`, assertion ID/revision hash, evidence-bundle hash, outcome (`pending`, `accepted_auto_source`, `accepted_human`, `rejected`, `needs_review`), actor type/ID or method version, decision date, note, predecessor decision; accepted decisions cannot be transferred to changed revisions |
| `changes.csv` | `change_id*`, subject ID, old/new assertion IDs, reason/evidence, decision reference, optional inverse-change ID; append-only audit trail with compensating reversals |
| `successors.csv` | retired entry/sense ID, successor ID, merge/split role, identity-decision ID; acyclic; IDs are never recycled |
| `findings.csv` | finding ID, record/assertion ID, stable issue code, severity, scalar positions where relevant, status, resolution/exclusion reason; anomaly reporting never repairs source text |
| `unicode_exceptions.csv` | assertion ID, exact revision/value hash, kind (`non_nfc_original`, `intentional_control`), scalar sequence/position, reason, supporting decision; unused/stale exceptions fail |
| `labels.csv` | registry/version, code, category (`region`, `register`, `domain`, `social_usage`, `period`, `grammar_system`), display label JSON, definition/evidence reference, optional reviewed parent code; language tags remain separate |
| `scopes.csv` | subject entity/assertion ID, scope dimension, state (`attested`, `unrestricted`, `unknown`), label code when attested, supporting assertion/decision; unrestricted requires affirmative accepted evidence |
| `pack_members.csv` | pack ID, entry ID, included revision; optional relation inclusion policy; membership itself is reviewed, not guessed solely from source filename |

These tables are the logical v1 contract. Host schema metadata defines columns
and reference rules; generated release projections may flatten validated views
for efficient compilation. Such projections remain generated and are compared
against the approved canonical table set, not edited independently. Decisions,
findings, and raw source-record ledgers need not all ship to runtime consumers;
ship the minimal traceable approved evidence/decision projection, without private
review notes or quarantined source text.

## Claim validation and review state transitions

1. Import creates `pending` assertions and preserves imported labels literally.
   A source label, confidence 1.0, or populated IPA never implies approval.
2. Source investigation records publication fidelity, reuse basis, and attribution
   evidence independently. Source retrieval failure keeps state unknown.
3. Unchanged, source-verified, unambiguous text that passes structural, Unicode,
   and reuse checks may become `accepted_auto_source`. Schema encoding or NFC
   representation of canonical equivalents does not itself invent new content.
4. A correction, inferred/derived annotation, or ambiguous interpretation needs
   `accepted_human` with reviewer/date/evidence before release. An automated
   method may prepare proposals and compute diagnostics but not impersonate a
   human decision. Existing approved global methodology is linked explicitly;
   it is never a blanket waiver for unrelated unreviewed claims.
5. Any change to value, convention, or supporting evidence invalidates previous
   acceptance. New claim/decision references retain the old revision/history.
6. Pack eligibility is computed, never accepted from an editable boolean. It
   requires valid structure, supporting source and reuse/attribution evidence,
   applicable acceptance, no blocking findings, and dependency closure.
7. Rejection/quarantine does not delete the source record. Reimport updates
   proposals idempotently; incompatible edits require reconciliation.

An entry can ship with unknown optional POS or pronunciation if those fields
are explicitly absent/unknown and its headword plus at least one sense meet
eligibility. No ineligible annotation leaks merely because another field is
accepted. Contradictory accepted sources remain separately attributed claims
and senses; choosing a synthesized interpretation requires human review.

## Scope and filtering

Language/variety IDs resolve to declared language metadata. Custom region codes
(e.g. `IN-TN`, `IN-TN-KONGU`, `LK-JAFFNA`, `LK-BATTICALOA`, `LK-VANNI`,
`LK-UP-COUNTRY`) are project registry identifiers, not invented BCP 47 tags.
Geographic parent relationships are reviewed metadata. An attestation in a child
region can satisfy its parent query; a parent attestation alone does not prove
use in every child region. Unknown is never converted to unrestricted.

A region query retains accepted regional matches and accepted unrestricted
claims. Inherit an explicit accepted entry scope only where a sense/claim has
no narrower override. Explicit unknown/narrower scope at a sense overrides
inheritance. Filter returned senses and scoped annotations as well as entries;
exclude an entry when no eligible sense remains. This prevents a valid entry
attestation from exposing a meaning supported only in another region.
Unfiltered lookup includes otherwise eligible unknown-scope entries with that
state visible. Register filtering requires accepted equality; unknown is
excluded when a register filter is present. Social usage is not a register alias.

## Milestone transitions and completeness

- **L0**: file inventory/hash comparison and audit completed (`data/sources/tamil-lexicon.sha256.json`);
  actual source rights remain unknown until primary-dictionary and secondary
  evidence is recovered.
- **L1**: schemas (`schemas/lexicon/`), registries, `json-string-utf8-v1`
  editorial intake (`data/curation/tamil-lexicon/`), payload proof
  ([source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json)),
  and pre-projection clean replay ([us1-proof.json](../../target/lexicon/us1-proof.json))
  are implemented and verified (`263,014` initial identities, `307,243` intake records).
- **L2**: accepted ([l2-acceptance.json](../../target/lexicon/l2-acceptance.json),
  [structural-final.json](../../target/lexicon/structural-final.json)): `739`
  selected records (`101` primary entries, `20`–`22` per secondary dataset, `11`
  homograph spellings / `22` entries, `20` verbs, `74` mixed-sense cases, `18`
  technical MWEs, `22` TN/Jaffna regional cases, and all `9` observed audit issue
  classes) projected (`264,402` identities, `243` entries, `363` senses) with
  `307,243` validated quarantined dispositions, `0` eligible assertions, and
  fail-closed release rejection ([release-rejection-final.json](../../target/lexicon/release-rejection-final.json)).
  Phase 6 numerals scheduling is unblocked without granting data-release or runtime approval.
- **L3**: a nonempty relevant approved subset, with full accounting of its intake
  scope and source/review/pack closure. Full-bundle completion additionally needs
  one disposition for every one of the 307,243 logical CSV records. The supplied
  FST has file-level quarantine/disposition as an unreproducible derived artifact.
- **L4**: nonempty approved pack and real runtime acceptance including homographs,
  filters, canonical equivalence, controls, errors, packaging and parity; never
  count an empty/all-quarantine pilot as verified runtime support.

## CLDF export and round-trip

Generate `Dictionary-metadata.json` plus entries, senses, examples, languages,
`sources.bib`, and custom forms/texts/relations/claims/scope/decision tables under
`target/lexicon/cldf/<pack>/`. Metadata uses CSVW with explicit property URLs,
keys, null rules, custom extensions and foreign keys. No canonical data is
rewritten to meet a consumer format. Decode text cells to ordinary Unicode for
interchange, preserving declared original representations and controls.

Entry IDs, senses, text languages/types, all accepted forms, accepted claims,
scope, provenance and decision summaries round-trip through standard fields and
extensions. Never flatten multiple senses into one Description, guess an English
translation, or export excluded source text as a public bibliography attachment.
Target CLDF 1.3 with locally pinned schema resources/digests. Run a pinned CLDF
validator on a nonempty approved export before claiming
conformance. Imported decisions cannot be accepted merely because an external
export labels them approved: round-trip verifies equality against trusted IDs
and revision hashes, not authority to promote arbitrary outside data.
