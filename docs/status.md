# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

The bounded TSCII byte decoder and strict reverse encoder are implemented in
the local development tree and remain unreleased. They share 22,585 active
vectors across the toolkit; 638 cover the new encoder. The previously published
alpha packages do not contain TSCII conversion. No version bump or registry
upload was performed. Contracts: [decoder](specs/codec-tscii-draft.md),
[encoder](specs/codec-tscii-encode.md), and [roadmap](specs/codec-roadmap.md).

Verification: `just agent-pre-stop-gate` passed including 105 harness tests
and the complete Rust, Python and WASM parity suite; `just test-dart` and the
workbench TypeScript check passed. Logs: `target/tscii-encode-gate.log` and
`target/tscii-encode-dart.log`.

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
313-key TSCII byte decoder and a 312-key strict reverse encoder, with ASCII
passthrough, longest matching, and explicit canonical byte aliases. Detection,
Anjal, Vanavil, TAB, TAM and historical orthography remain future milestones.
Choose and source the next bounded codec profile before implementation.

After codec coverage is scoped, return to Punarchi, morphology, dialect
normalization, hyphenation, prosody, and PostgreSQL search. Each begins with a
sourced specification and golden vectors before algorithms.
