# Lexicon v0.1: bounded exact lookup

Status: reviewed core implemented and verified across Rust, Python, Node/browser
WASM, Dart and isolated archives. The owner approved activation of all 44 escaped
lexicon vectors on 2026-11-15 for the data-enabled core verification profile.
Cargo default data features remain off; no publication is authorized.
The initial six-entry, 19-sense content and separate CC-BY-SA-4.0 data-pack policy
were approved by `abish` on 2026-11-14. That decision is bound to exact assertion
and evidence hashes in the [approval receipt](../reviews/wiktionary-core-approval-2026-11-14.json).
Canonical promotion and compiled-pack acceptance are recorded in
`target/lexicon/l3-acceptance.json`. Nonempty binding parity and isolated archive
proof are recorded in `target/lexicon/l4-functional.json`; the separate fixture
activation receipt is [recorded here](../reviews/lexicon-fixture-activation-2026-11-15.json).

## Normative contracts

The [lookup contract](../../specs/021-lexicon-curation/contracts/lookup.md),
[closed response schema](../../specs/021-lexicon-curation/contracts/lookup-response.schema.json),
[pack contract](../../specs/021-lexicon-curation/contracts/packs.md), and
[data model](../../specs/021-lexicon-curation/data-model.md) define the exact request,
response, error strings, validation order, storage and review constraints. This
module specification does not relax those contracts.

## Reviewed initial scope

The [decision sheet](../reviews/wiktionary-core-decision.md) specifies these
entries, preserving English sense order, punctuation and visible qualifiers:

| Headword | POS | Senses | Official revision |
|---|---|---:|---:|
| அடடா | INTJ | 2 | 85842017 |
| அந்நிலை | NOUN | 1 | 89903937 |
| அறிக்கை | NOUN | 4 | 88382210 |
| செப்பம் | NOUN | 9 | 61485513 |
| நன்றி | INTJ | 1 | 93647113 |
| நன்றி | NOUN | 2 | 93647113 |

The two நன்றி entries keep distinct stable identities. An unfiltered exact
query must return both, sorted by entry ID, with their own accepted senses. No
spelling/POS heuristic may merge them. This bounded profile does not establish
comprehensive Tamil vocabulary or any regional/dialect coverage.

The written/Catholicism qualifiers in அறிக்கை remain visible in the accepted
text. Structured register/domain/region proposals remain unknown or pending;
approval of text does not turn those proposals into attestations. No supplied
IPA, etymology, morphology, generated conjugation, frequency, root or DEDR
annotation is part of this approved initial slice.

Pinned raw API/wikitext snapshots, byte hashes, source spans and transformation
records are retained in the isolated candidate workspaces. The approved route is
fresh official Wiktionary revisions; it does not recover the missing historical
Kaikki download or approve the old mixed-source bulk intake.

## Engine and interface behavior

Rust in `tamil-toolkit` owns compilation, lookup and filtering. Python,
TypeScript/WASM and Dart serialize the shared dispatcher only. The existing
`tamil-norm` implementation supplies NFC. No runtime networking, query logging,
repair, trimming, search folding, variant expansion, pronunciation synthesis or
morphological inference belongs to this interface.

`lexicon_lookup` accepts a string up to 65,536 UTF-8 bytes, with optional selected
packs and controlled region/register filters. Validation follows the contract's
input, options, pack-name, availability and filter order. Empty input is valid
and returns not-found after profile validation. Invalid inputs are rejected,
never truncated or coerced.

NFC canonical equivalence is the only key transformation. Whitespace, case,
punctuation, joiners, soft hyphens and mixed scripts are preserved. All accepted
canonical-headword matches are returned, with no first-homograph selection or
result cap. Sense order is explicit display order then ID. Repeated equal
entry/revision records across packs are deduplicated; conflicting revisions fail.

Region filtering uses only accepted attestation, reviewed child-to-parent
geography and reviewed unrestricted scope. Unknown scope is excluded by a
filter; parent-to-child inference is forbidden. Explicit sense overrides take
precedence over entry scope. Register filtering matches the accepted registry
value exactly. No entry with zero remaining senses is returned. With no filter,
unknown optional scope remains visible rather than excluding reviewed content.

`lexicon_packs` returns compiled pack metadata and may return an empty list in a
no-data build. `lexicon_lookup` requesting an unavailable pack returns the exact
contract error; it must not return a successful empty dictionary. Default builds
embed zero dictionary payload. The additive `lexicon-core`,
`lexicon-terminology`, `lexicon-names-taxa` and `lexicon-regional` features are off
by default; feature existence is not evidence that a corresponding data pack
has approved content.

## Provenance and compilation

Every published value must resolve to its exact accepted revision, source
locator, review identity/method/date and applicable source terms. Genuine human
review is represented by the recorded actor; automatic-source acceptance retains
a null actor if none was recorded and requires its method. Pending scope or
annotation evidence cannot become public provenance for another claim.

The approved data route preserves CC-BY-SA-4.0 notices, per-entry source/history
attribution and applicable upstream disclaimers. Data terms are recorded
separately from the engine/tooling code license. Source archives must carry the
applicable data terms even when the feature embedding that data is disabled.
No unreviewed intake, private notes or omitted annotations may be included in
those archives to satisfy a missing dependency.

Offline build tooling validates the promoted package-local inputs and writes
only to `OUT_DIR`. Keys, postings and manifests are sorted deterministically.
Offsets/counts use checked fixed-width little-endian encodings; safe reads and
`forbid(unsafe_code)` apply. The supplied untrusted FST is never an input.
Python and remote schemas are not required by standalone Cargo consumers.

## Acceptance evidence

The complete fresh structural workload verified 307,243 source CSV records and
12 frozen file hashes in 52.72 seconds, peaking at 191.93 MiB including both
validation worker processes. The time and memory targets pass. See
`target/lexicon/benchmarks.json`. This is full-corpus evidence, not a pilot.
The release PyO3 core workload verified 10,000 queries per pass and all returned
entries/senses, with p95 of 0.1148 ms native dispatch and 0.1979 ms including
Python serialization. These measurements establish neither large-dictionary
lookup scaling nor cross-runtime parity. The pack remains six reviewed entries.

Source-backed escaped lookup goldens must precede the Rust compiler/lookup
implementation, pass the closed response schema and be registered as planned.
Real expected responses must carry actual promoted source/review/pack hashes;
illustrative schema examples are not test data or approval.

### Active golden suite coverage (`tests/golden/lexicon_lookup.jsonl`)

- Registered in `tests/golden/manifest.json` with `"status": "active"`,
  operations `["lexicon_lookup", "lexicon_packs"]`, data-enabled `core` pack
  profile requirement (`lexicon-core`), following owner activation approval
  on 2026-11-15 (`active` golden count is `36205`).
- Frozen against validated canonical `lexicon/dictionary` dataset
  `0.1.0+4d1309d05391` (`manifest_sha256`
  `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`) and human
  approval receipt `docs/reviews/wiktionary-core-approval-2026-11-14.json`
  (packet `0b2168d07e9b45b5316994c1d97648ebf5de3ad666de050b10afbe5dfa58695b`,
  `actor_id: "abish"`, `decided_on: "2026-11-14"`, 31 approved claims across
  5 raw Wiktionary revisions).
- Coverage (44 escaped JSONL cases: `lexicon_lookup_atataa_001`..`lexicon_packs_err_invalid_input_044`):
  all 5 distinct canonical written queries covering all 6 entries and all 19
  senses; shared-spelling homograph ordering (`\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf`:
  `ent_a08297c3-424d-5a37-aaf0-4135d7476669` `NOUN` before
  `ent_f063763c-36ac-55c6-b288-8da7f9ab6fff` `INTJ` bytewise); duplicate pack
  deduplication; empty and absent `not_found`; exact 65,536-byte boundary vs
  65,537-byte ASCII and 65,538-byte multibyte UTF-8 overflow errors; composed and
  NFD-decomposed two-part Tamil vowel `not_found` queries asserting
  `canonical_query` NFC; whitespace, `ZWJ`, `ZWNJ`, soft hyphen, case, and
  mixed-script preservation; input/option/pack shape, unknown pack,
  unavailable pack (`terminology`, `names_taxa`, `regional`), unknown
  `region`/`register` errors against currently empty registries, validation
  order precedence, and `lexicon_packs` core introspection/invalid-input error.
- Profile-specific and synthetic unit coverage beyond the active real-data suite:
  1. No-data / disabled-`core` build profile negative tests (`lexicon_packs` ->
     `[]`, `lexicon_lookup` -> unavailable error) live in dedicated runtime
     unit fixtures rather than mixing contradictory pack profiles into this
     suite.
  2. Positive NFD-decomposed posting lookup cannot be claimed on the 6 approved
     headwords because none contain canonically decomposable Tamil two-part
     vowels (`NFD == NFC` for all 6); synthetic Rust unit fixtures exercise
     positive NFD posting lookup.
  3. Positive valid-code `region`/`register` filter matching awaits real
     versioned registry additions and reviewed scope attestations; synthetic
     structural Rust unit fixtures cover valid-code filter semantics
     without fabricating published regional claims.
  4. Arbitrary unknown option keys on `lexicon_lookup` (`foo: 1` ->
     `lexicon: invalid options`) remain tested in Rust/binding unit suites so
     `tests/golden/schema.json` preserves top-level `additionalProperties: false`.
  5. Multi-pack `incompatible pack versions` errors require two compiled packs
     with mismatched dataset/schema metadata in runtime tests.

Acceptance requires nonempty reviewed homograph behavior, NFC equivalence,
filter/unknown-scope and exact-error checks, byte-identical clean data builds,
zero-payload defaults, supported feature/profile combinations and real
Rust/Python/both-WASM parity. Dart host/analysis/fixture checks run separately on
Windows. Isolated offline archive consumers must prove the same approved
profile without depending on the repository root. Benchmarks measure full intake
and lookup separately and report actual misses against targets.

Fixture activation needs its recorded owner decision after concrete source,
pack and parity evidence. Archive proof and publication remain separate;
Feature 021 authorizes no registry upload.

## Profile-specific verification and review corrections

Active suites declare their required data profile. Core verification executes
all 36,205 active vectors; explicit no-data verification executes the 36,161
baseline vectors and reports the 44 core-only exclusions. A missing required
core pack or an explicit runtime/profile mismatch is an error, not an exclusion.
Cargo default data features remain off. Dataset compatibility compares release
versions independently of per-pack `+` build hashes, while enforcing schema,
vocabulary, region hierarchy and shared-entry revision agreement. Compiler and
host validation must both enforce scope evidence and closed finite vocabularies,
including empty lists; structured missing values and inherited scope remain
distinct. Regression and fresh independent review results are pending.
