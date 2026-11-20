# Exact Lookup and Pack Contract v1

**Status**: Planned L4 interface; no new runtime operation is implemented or
activated by these documents. See [data model](../data-model.md) and
[pack compilation](packs.md). Names below are fixed design choices for task
generation and must be tested through the existing shared dispatcher.

## Interface and data availability

Rust facade module: `tamil_toolkit::lexicon`. Proposed Rust functions:
`lookup(&LookupRequest) -> Result<LookupResponse, LexiconError>` and
`packs() -> Vec<PackInfo>`. The module owns no morphology, phonetic synthesis,
or search folding. All runtimes serialize the same request/result model.

Dispatcher operations:

- `lexicon_lookup`: `input` is a string; optional top-level `packs`, `region`,
  and `register` fields. Unknown option fields are rejected within this operation.
- `lexicon_packs`: `input` is null; returns compiled pack IDs, dataset/format
  versions, scope summaries, approval-manifest digest and availability.

Use flat operation names to match the repository dispatcher style. Python adds
`lexicon_lookup(text, *, packs=None, region=None, register=None)` and
`lexicon_packs()`; TypeScript exports the same operation names with typed options;
Dart adds thin `lexiconLookup` / `lexiconPacks` helpers. The C ABI continues to
carry the existing JSON dispatcher without an independent engine or new ABI.

```json
{
  "op": "lexicon_lookup",
  "input": "\u0b85",
  "packs": ["core"],
  "region": "LK-JAFFNA",
  "register": null
}
```

This is a request-shape example, not a claim that U+0B85 is eligible or has
particular regional use in an approved dataset. Default `packs` is `["core"]`;
core must be compiled and eligible or the operation errors. Explicit nonempty
pack selection is required for a build without core. Duplicate pack IDs are
collapsed; selected IDs are sorted for deterministic responses. Empty selection
is invalid. Unknown IDs and known-but-disabled packs are distinct errors.

Data features are off by default. `lexicon_packs` succeeds with an empty available
list in a no-data build; `lexicon_lookup` reports unavailable data. It must not
pretend an absent dataset is an empty dictionary. Active golden lookup rows
require a declared matching nonempty pack profile in every runtime; disabled
pack behavior has separate negative tests.

## Validation and matching

Validation order is fixed: input type/size, option shape/types, pack names,
pack availability, then filter codes. A string input may be empty; empty input
returns not-found after request/profile validation. Inputs larger than 65,536
UTF-8 bytes are rejected, not truncated. Region/register codes are nonempty
strings from the versioned registries or null. Arrays, arbitrary scalar coercion,
invalid filter codes, and unsupported options are errors. No silent fallback.

1. Normalize input to NFC through `tamil-norm`; preserve case, whitespace,
   punctuation, joiners, soft hyphens, mixed scripts, and other format controls.
2. Compare against the pack's accepted canonical headword forms only. Canonically
   equivalent source forms share the key but their lexical identities remain
   distinct. Variant/IPA/transliteration forms do not become exact keys unless
   explicitly promoted to an accepted canonical entry in the data contract.
3. Collect all matching entry IDs from every selected pack's posting list;
   deduplicate identical entry/revision records across packs. Conflicting revisions
   for one ID fail pack compatibility validation rather than using load order.
4. Project accepted senses/annotations and apply scope filters. Requested region
   includes attested equality, attestations within reviewed child regions, and
   reviewed unrestricted scope; unknown scope and incompatible-region-only
   content are excluded. A parent-region attestation alone does not prove its
   children. Explicit narrower/unknown sense scope overrides inherited entry scope.
5. Register filtering matches accepted controlled labels exactly; unknown register
   is excluded when a filter is supplied. Without either filter, unknown scopes
   remain visible on otherwise eligible content. Drop entries with no eligible
   senses remaining. Excluded optional annotations stay absent with an availability
   state; they are never generated during lookup.
6. Sort entries by bytewise stable entry ID. Sort senses by explicit display order,
   then sense ID; sort other repeated records by stable ID. Never return only the
   first homograph, choose one source interpretation, or truncate matches.

## Response

The normative closed JSON Schema is [lookup-response.schema.json](lookup-response.schema.json).
Every listed property is required; extra properties are rejected. The complete
[matched example](lookup-response.example.json) demonstrates shape only: its
`example` IDs, zero digests and source/acceptance metadata are deliberately
illustrative. It is not a real source decision, approved dataset, golden vector,
or evidence of successful lookup. Real goldens must replace it with actual
source-backed eligible records before implementation.

| Object | Required fields and constraints |
|---|---|
| LookupResponse | `schema_version: 1`, `status: matched \| not_found`, `canonical_query: string`, nonempty `packs: PackInfo[]`, `entries: Entry[]`; matched requires at least one entry and not_found requires zero |
| PackInfo | `id: core \| terminology \| names_taxa \| regional`, nonempty `dataset_version`, `schema_version: 1`, positive `index_format_version`, full `manifest_sha256`, `available: true`, `coverage: Coverage` |
| Coverage | Unique `language_ids`, `region_codes`, `register_codes` arrays and nonnegative integer `unknown_region_entries` |
| Entry | Nonempty `entry_id`, SHA-256 `revision`, nonempty NFC `headword`, `language_id`, `part_of_speech: LabelField`, nonempty `forms: Form[]`, nonempty `senses: Sense[]`, `region: Scope`, `register: LabelField`, `annotations: Annotation[]`, nonempty `provenance: Provenance[]` |
| Sense | `sense_id`, positive integer `display_order`, `parent_sense_id: ID or null`, nonempty `components: Text[]`, `examples: Text[]`, `relations: Relation[]`, `region`, `register`, `annotations`, nonempty `provenance` |
| Form | `form_id`, `representation: written \| romanization \| ipa`, `role: canonical \| variant`, nonempty `text`, `convention: nonempty string or null`, nonempty `provenance` |
| Text | `text_id`, `kind`, `language_id`, nonempty `text`, nonempty `provenance`; components permit definition/gloss/translation/citation, examples require kind example |
| Scope | `state: attested \| unrestricted \| unknown`, unique `codes: ID[]`, `provenance`; attested requires codes and evidence, unrestricted requires evidence and no codes, unknown requires no codes/evidence |
| Field | `availability: available \| unknown \| not_applicable \| withheld`, `value: string/number/boolean or null`, `convention: string or null`, `provenance`; available requires nonnull value and evidence, other states require null value/convention and empty evidence |
| LabelField | Field with value restricted to a nonempty string or null; used for POS and register |
| Annotation | `property: ID` and `field: Field`; property codes come from the declared registry |
| Relation | `relation_id`, `code`, `directionality: directed \| symmetric`, typed `source`/`target: Endpoint`, nonempty `provenance` |
| Endpoint | `kind: entry \| sense`, `id: ID`, resolving inside the selected approved pack union |
| Provenance | `assertion_id`, `revision_sha256`, `source_id`, nonempty `locator`, `acceptance: Acceptance` |
| Acceptance | `decision_id`, `kind: accepted_auto_source \| accepted_human`, `actor_id: ID or null`, `method: nonempty string or null`, ISO date `decided_on`; human acceptance requires an actual nonempty actor ID, automatic acceptance requires a nonempty method |

IDs match `[A-Za-z][A-Za-z0-9_.:-]*`; digests are exactly 64 lowercase hex digits.
JSON null is a value, not a string. `withheld` is public projection availability
for an ineligible/unselected optional annotation, not a new curated `value_state`:
its text, convention, source evidence and private review details are not exposed.
`unknown` preserves genuinely unknown values; it never asserts lexical absence.
Only emit optional annotations selected by the profile, with their availability
visible; empty repeated arrays mean no selected records, not lack of all evidence.
Confidence is exposed only with an approved method and evidence.

Schema validation is necessary but insufficient for eligibility. In addition,
validate registry references, dates, unique IDs/pack IDs, exact approved revisions,
source/review/terms eligibility, canonical NFC, exactly one canonical written
form agreeing with the headword, parent/target reference closure, accepted scopes,
and the documented ordering. Filtered senses reference approved pack identities;
no unapproved source text or private review note is returned. A decision-shaped
JSON object alone can never approve a real claim.

Entry and sense region/register fields report effective accepted scope after
inheritance and overrides have been applied; they are not raw editorial scope
records. A missing editorial override and an explicit unknown override remain
distinct during computation even when the final result reports unknown scope.

`lexicon_packs` returns an array of the same PackInfo objects (the schema's
`$defs/PackInfo`), sorted by pack ID; the empty array is valid in a no-data build.
Lookup returns selected compatible pack metadata only. A not-found result has
this exact root shape, with actual compatible PackInfo objects in `packs`:

```json
{
  "schema_version": 1,
  "status": "not_found",
  "canonical_query": "demo",
  "packs": [{
    "id": "core",
    "dataset_version": "example-only",
    "schema_version": 1,
    "index_format_version": 1,
    "manifest_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    "available": true,
    "coverage": {"language_ids": ["lang_example"], "region_codes": [], "register_codes": [], "unknown_region_entries": 1}
  }],
  "entries": []
}
```

This is also a schema illustration, not an available pack. Complete filter
exclusion and absent spelling both yield not_found; neither asserts that the
word is absent from Tamil or a geographic variety. Unavailable requested data
is an error, not not_found. No runtime networking, telemetry, user-input logging,
or synthesized missing definitions is part of the response contract.

## Error contract

Map structured internal errors into the existing dispatcher's error channel;
wrappers must not convert errors into successful empty results. Golden cases
assert these exact messages:

| Condition | Error string |
|---|---|
| Input is not a string | `lexicon: input must be a string` |
| Input exceeds byte limit | `lexicon: input exceeds 65536 UTF-8 bytes` |
| Malformed/unknown option shape | `lexicon: invalid options` |
| Empty or malformed packs array | `lexicon: packs must be a nonempty string array` |
| Unknown pack ID | `lexicon: unknown pack '<id>'` |
| Requested pack not compiled/approved | `lexicon: pack unavailable '<id>'` |
| Invalid region/register code | `lexicon: unknown region '<id>'` / `lexicon: unknown register '<id>'` |
| Incompatible selected dataset/schema revisions | `lexicon: incompatible pack versions` |

Build-time corruption, unresolved references, invalid reviewed metadata, and
artifact hash mismatches fail compilation/pack validation. They never become
an ordinary word-not-found response. A supplied malformed external package is
not loaded by this v1 embedded-pack interface.

## CLI

```powershell
cargo run --locked -p tamil-toolkit --bin tamil-toolkit --features lexicon-core -- lexicon lookup 'example' --pack core
cargo run --locked -p tamil-toolkit --bin tamil-toolkit -- lexicon packs
```

Commands above are planned and depend on implementation and approved data.
`lookup <TEXT>` accepts repeated `--pack ID`, optional `--region ID`, and optional
`--register ID`. Quote the input to preserve spaces. Emit the same JSON value as
the dispatcher; exit 0 for matched/not-found, nonzero for errors. Reuse existing
CLI argument parsing; do not add an HTTP server, UI, or new parsing framework.

## Golden acceptance matrix

Before implementing lookup, add sourced, escaped JSONL cases with planned suite
status, then implement against unchanged expectations. Cover one-to-many
homographs; same-spelling/same-POS historical distinctions; NFC/NFD equality;
unchanged original text; preserved ZWJ/ZWNJ and deliberate nonmatches; empty and
unknown inputs; type/size errors; region match/unrestricted/unknown/other-region
truth table; sense overrides; register matching; partial annotations; disabled
packs; duplicate IDs across packs; conflicting revisions; ordering; and omitted
optional relations. Use the same declared pack snapshot in Rust, Python, Node
and browser WASM, and Dart. No missing-pack skip, mock, or all-quarantine substitute
satisfies active parity. Explicit manifest activation and publication review remain
separate actions from test execution.

## Editorial-to-public projection rules

Public identifiers retain recorded dots and colons as well as letters, digits,
underscores and hyphens; they are never rewritten to fit a narrower output regex.
Accepted human decisions require their actual nonempty reviewer ID. Automatic
source decisions retain a null actor ID when none was recorded, alongside the
required nonempty method; projection must not invent an actor.

Editorial relation directionality `undirected` projects to public `symmetric`;
`directed` remains `directed`. Both typed endpoints are preserved. This is a
serialization mapping, not inference of an inverse or a new lexical relationship.

Entry provenance is the deduplicated accepted evidence supporting its canonical
written form and POS; sense provenance comes from its accepted definition/gloss
components. Parent provenance never licenses unaccepted child claims. Quarantined
`unparsed` passages are excluded. An accepted entry-owned text that cannot be
represented by the response needs an explicit reviewed reparenting or documented
omission policy; it must not disappear silently during promotion.

Published region/register and other code vocabularies are finite, versioned pack
metadata validated before lookup. Identifier syntax alone does not establish
membership, attestation or geographic hierarchy.
