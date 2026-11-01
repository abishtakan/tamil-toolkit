# Alpha 3 release

Release scope for Rust/npm `0.1.0-alpha.3` and Python `0.1.0a3`.

## Compatibility and scope

Alpha 3 adds the bounded LT-TM / IndoWord 16-bit code profile. The Rust codec
exposes code-array and legacy code-valued text conversion in both directions;
the Python and TypeScript/WASM adapters expose the same operations through
their shared `execute` dispatcher. The profile includes 332 unique mapping
entries and 687 active sourced golden vectors.

This profile is not an 8-bit decoder. It does not parse PDFs, select PDF font
runs, detect encodings, or claim that every LT-TM or IndoWord font has the same
mapping. Vanavil, AnuGraphics, and Pallavar are not aliases. See the
[LT-TM profile contract](../specs/codec-lt-tm.md) for provenance, operation
inputs, fallback, errors, and acceptance limits.

The private PDF extraction utility in `tools/tamil-pdf-extract/` is not part of
the published crates, PyPI package, or npm package. Other planned linguistic
modules and Dart/Pub distribution remain outside the alpha release scope.

## Reviewed source and publication evidence

Publication evidence is recorded here after the artifact build and registry
uploads. The release source must be the full commit SHA selected by the
successful **Alpha distribution artifacts** workflow. Registry packages must
come from that run's validated artifacts; do not reuse or replace this version.

## Public package set

Alpha releases publish the synchronized public SDK batch: six approved Rust
crates, the Python package, and the npm package. Rust crates follow the
dependency order in [`release-policy.toml`](../../release-policy.toml). The
npm `alpha` tag is used; `latest` is not promoted.
