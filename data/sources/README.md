# Source data intake

The [2026-11-16 source readiness report](../../docs/audits/lexicon-source-readiness-2026-11-16.md)
separates historical record counts, distinct spelling candidates, exact overlap
with the current three usable packs, and source-specific recovery blockers.
It supersedes the older checkpoint counts below for current runtime coverage;
it does not approve or unquarantine any historical claim.

`tamil-lexicon/` contains the original user-supplied lexicon bundle, relocated
from the repository root without changing its 12 files. The adjacent
`tamil-lexicon.sha256.json` records each original filename, byte size, and SHA-256;
all hashes were checked after the move.

This is an unreviewed source snapshot, separate from the canonical reviewed
data in `lexicon/`. It includes CSV exports and a supplied binary FST index.
Source provenance, licensing, schema, Unicode integrity, regional coverage,
and index reproducibility remain to be audited. No runtime or release packaging
consumes this bundle yet. The repository license does not establish the license
of these supplied files.

Preserve these originals during curation. Put reviewed declarative projections
in `lexicon/` once their source and contracts are established; generate runtime
indexes from those projections through the Rust build pipeline.

The [2026-11-13 audit](../../docs/audits/lexicon-2026-11-13.md) records structural
checks, editorial and provenance gaps, and the proposed order of work. The owner
reports public online sources combined through Python extraction; exact source
and permission records remain to be recovered.


Feature 021's [storage decision](../../docs/decisions/lexicon-text-storage.md)
and completed L2 structural slice (`T001`–`T037`,
[l2-acceptance.json](../../target/lexicon/l2-acceptance.json)) use readable
UTF-8 in `data/curation/tamil-lexicon/` without rewriting, normalizing,
re-escaping, or relabeling any frozen source file. All 12 original files and the
[checksum manifest](tamil-lexicon.sha256.json) remain byte-identical and
authoritative (`source-content-proof-final.json` verified `307,243` raw assertions).
Escaped scalar diagnostics stay separate from source storage. The historical
merged-source bundle remains **quarantined** (`0` eligible assertions) because
its snapshot lineage and source-specific reuse rights remain unverified.

Separately, an isolated fresh Wiktionary route (`data/curation/wiktionary-candidate/`,
`data/curation/wiktionary-homograph-candidate/`, and
`data/curation/wiktionary-core-reviewed/`) pinned official `en.wiktionary.org`
`oldid` revisions and received genuine human review (`abish`, `2026-11-14`,
[approval receipt](../../docs/reviews/wiktionary-core-approval-2026-11-14.json))
for `6` entries, `19` senses, and `31` accepted claims under separate
**CC-BY-SA-4.0** data terms (engine code remains MIT), reaching L3 canonical and
compiler acceptance in `lexicon/dictionary/` (`0.1.0+4d1309d05391`, manifest
SHA-256 `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`,
[l3-acceptance.json](../../target/lexicon/l3-acceptance.json)). That fresh route
does not validate or unquarantine the 12 historical intake files. Full
307,243-record structural benchmarking, multi-runtime binding parity, final
gates and isolated archive proof pass; core-profile activation is approved.


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


## Owner-directed supplied-record access (2026-11-16)

The owner explicitly requested searchable inclusion of all 307,243 supplied CSV
records without additional permission records. The separate historical export
preserves original cells, duplicates and file/row provenance. It is labelled
`owner_supplied_unverified`, with `rights_status: unresolved`; no new content
license or accepted dictionary decision is inferred. The existing verified
curation eligibility of historical claims remains unchanged. The twelve frozen
files are not rewritten. See
[the source-record contract](../../docs/specs/lexicon-source-records.md) and run
`uv run --locked python tools/prepare_historical_lexicon.py` to prepare the
playground artifact.
