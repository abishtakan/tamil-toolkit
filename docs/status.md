# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

Prepare the second public alpha, `0.1.0-alpha.2` (Python `0.1.0a2`), including
bounded TSCII, TAB, TAM and Anjal byte conversion. The release scope and
compatibility notes are in [alpha-2.md](releases/alpha-2.md). Anjal implementation
is committed as `3cbcb5c`. Versions are synchronized locally; the target versions
were checked absent on all six crates, PyPI and npm on 2026-11-01. No alpha.2
package has been published.

The versioned source passed the full gate, Dart, workbench and local archive
checks; each isolated consumer passed all 26,957 vectors. The workspace lockfile
has no third-party dependency changes. Commit the reviewed release source, push,
and dispatch the immutable artifact matrix.
Only reviewed successful artifacts from that matrix are eligible for manual
publishing workflows. npm trusted-publisher setup requires npm authentication;
see [publishing policy](releases/policy.md).

## Published and implemented

- Rust: `tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`,
  `tamil-codec`, `tamil-toolkit` at `0.1.0-alpha.1`.
- Python: `tamil-toolkit 0.1.0a1`. npm: `tamil-toolkit 0.1.0-alpha.1`.
- Shared behavior: core Unicode/Ezhuthu, normalization, Agara collation,
  bounded TN/SL numerals, INR/LKR, fractions, Gregorian Tamil dates, explicit
  Bamini conversion both ways, and the Rust-backed local Tamil oracle.
- 21,277 active golden vectors. Module contracts define bounded support;
  this does not imply complete Tamil linguistic coverage.

Registry links, source commits, artifact runs, and archive digests live in the
[release record](releases/README.md). Use
[publishing policy](releases/policy.md) for future releases and
[development workflow](development.md) for feature integration.

## Deferred and planned

Pub.dev/Dart distribution and PostgreSQL packaging are explicitly deferred.
The Dart host adapter exists; mobile native-library distribution is future
work. npm's OIDC workflow is ready; configure its package trusted publisher
when the next version is ready, then validate it within two days. No npm token
is required in GitHub. PyPI uses `publish-pypi.yml` with environment `pypi`;
npm uses `publish-npm.yml`; crates.io uses `publish-crate.yml` and the existing
Actions secret. Never copy secret values here.

## Codec development handoff

The current tree supports explicit Bamini conversion both ways and a bounded
341-key TSCII byte decoder and a 340-key strict reverse encoder, with ASCII
passthrough, longest matching, and explicit canonical byte aliases. The unreleased TAB and TAM profiles provide conversion in both directions.
The unreleased Anjal profile supports bounded bidirectional conversion. Detection,
Vanavil and historical orthography remain future milestones.
Choose and source the next bounded codec profile before implementation.

After codec coverage is scoped, return to Punarchi, morphology, dialect
normalization, hyphenation, prosody, and PostgreSQL search. Each begins with a
sourced specification and golden vectors before algorithms.
