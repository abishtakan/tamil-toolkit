# Canonical lexicon pack union

The host merge utility combines already validated packs of the same pack ID in
a fresh staging directory. It adds no linguistic behavior and grants no source
approval. Every input must pass canonical hash/schema/reuse validation first.

The first input is the preservation baseline. All existing rows and entry
revisions must remain exact. Identity conflicts fail. A shared label may retain
the baseline's definition/evidence only when its category, parent and display
are identical, or when display variants resolve to the same code in the existing
finite Wiktionary register map. Arbitrary display/parent changes fail.

Complete attribution blocks remain intact. An additional attribution block is
appended under a content-identified heading in the existing approved attribution
file; original and incoming source references remain valid. Conflicting legal
code text fails. Other notice collisions use content-derived filenames and must
still satisfy archive layout validation before integration. Private source-record/snapshot references
must resolve from explicitly supplied original workspaces; references are never
removed or replaced with fabricated support rows.
The original pinned legal-text file must also be supplied through that support
workspace and match the input canonical notices. Re-promotion must preserve the
source legal-text checksum, rather than substituting the Markdown wrapper hash.

The resulting workspace goes through the existing release validator and
deterministic canonical promoter. The utility then verifies that every baseline
row and every baseline entry revision survived. It never installs the result
into `lexicon/` and never changes runtime features or publishes an artifact.

```powershell
uv run --locked python -m tools.lexicon_merge `
  --input lexicon/dictionary `
  --input target/lexicon/wiktionary-gaps-final/candidate-canonical `
  --support-workspace data/curation/wiktionary-core-reviewed `
  --output target/lexicon/full-recovery/merge-core-7
```

Integration of a staged result still requires source-backed golden review,
metadata/catalog refresh, release-file synchronization, runtime parity and
isolated archive acceptance. A successful union is not evidence that the
unverified historical bundle is ready to distribute.
