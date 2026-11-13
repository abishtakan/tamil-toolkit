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

```json
{
  "schema_version": 1,
  "status": "not_found",
  "canonical_query": "\u0b85",
  "packs": [{"id": "core", "dataset_version": "1", "manifest_sha256": "..."}],
  "entries": []
}
```

`status = matched | not_found`. Both empty dictionary matching and complete
filter exclusion produce not-found; they do not assert that a word does not
exist in Tamil or is absent from a geographic variety. The caller can inspect
pack scope/review metadata to assess coverage. `manifest_sha256` is a full hash
in actual responses; the ellipsis above is illustrative only.

A matched entry includes `entry_id`, `revision`, `headword`, language/variety ID,
known/unknown optional POS, effective region/register states, source/decision
summaries, and ordered `senses`. Each sense includes stable ID/order, typed
language-tagged text components, approved examples/relations when present, and
scope/provenance summaries. Original source text is exposed only if it is itself
eligible and selected; no raw intake or unparsed unreviewed paragraph leaks.
Return unknown optional properties as null with their availability states;
empty arrays mean no selected records, not a claim that no such evidence exists.

Every returned assertion references source IDs and locators and distinguishes
`accepted_auto_source` from `accepted_human`. Confidence is returned only when
its method and evidence are approved. Public responses omit private review notes.
No runtime networking, corpus frequency guesses, user-input logging, or telemetry.

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
