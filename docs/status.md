# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

The unreleased TAM milestone adds a 407-key byte decoder and a 331-value strict
reverse encoder, with 1,545 shared TAM cases. Across the source tree there are
25,707 active golden vectors. TAM is monolingual: byte 41 maps to a Tamil glyph,
not Latin A. The [TAM contract](specs/codec-tam.md) describes its scope and the
TAB-compatible aliases. TAB work remains local and is preserved. The published
alpha does not include TAM, TAB or TSCII. No version bump or upload occurred.

Verification: `just agent-pre-stop-gate` passed, including 112 harness tests
and shared Rust, Python and Node/browser WASM parity. `just test-dart` and the
workbench TypeScript check passed on the same 25,707 vectors. Logs:
`target/tam-final-gate.log` and `target/tam-final-dart.log`.

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
Detection, Anjal, Vanavil and historical orthography remain future milestones.
Choose and source the next bounded codec profile before implementation.

After codec coverage is scoped, return to Punarchi, morphology, dialect
normalization, hyphenation, prosody, and PostgreSQL search. Each begins with a
sourced specification and golden vectors before algorithms.
