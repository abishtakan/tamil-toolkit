# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

The first bounded TSCII byte-decoding milestone is implemented locally and is
unreleased. See [the decoder contract](specs/codec-tscii-draft.md) and
[codec roadmap](specs/codec-roadmap.md). The current source has 21,947 active
golden vectors, including 670 TSCII vectors. Published alpha packages do not
include this decoder. No version bump or registry upload was performed.

Verification: Rust workspace, Clippy, release/Unicode gates, 104 harness tests,
Dart, and Rust/Python/WASM parity passed. The first full gate exposed a stale
Python native extension; its rebuild cleanup and focused regression test passed,
then `just test-parity` passed on the corrected build. Workbench TypeScript check
passed. Logs: `target/tscii-final-gate.log`, `target/tscii-final-parity.log`,
and `target/tscii-dart.log`.

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
313-key TSCII byte decoder, with ASCII passthrough, longest matching and strict
errors. TSCII reverse conversion, detection, Anjal, Vanavil, TAB, TAM and
historical orthography remain future milestones. Source provenance and profile
limits are in the codec specifications. Next, define and source a bounded reverse
TSCII contract and fixtures before implementation; ambiguous byte aliases must
have an explicit canonical encoding choice.

After codec coverage is scoped, return to Punarchi, morphology, dialect
normalization, hyphenation, prosody, and PostgreSQL search. Each begins with a
sourced specification and golden vectors before algorithms.
