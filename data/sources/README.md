# Source data intake

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
