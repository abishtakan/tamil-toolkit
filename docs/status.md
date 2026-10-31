# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

The unreleased Anjal milestone adds a 309-key byte decoder and 302-value strict
reverse encoder, with 1,250 shared Anjal cases. Four conflicting byte values
(E5–E8) are explicit errors unless a longer unambiguous sequence matches; a
source U+2212 glyph is not representable as a byte and is excluded. Across the
source tree there are 26,957 active vectors. The [Anjal contract](specs/codec-anjal.md)
records representation and limits. TAB and TAM work remains preserved. The
published alpha does not contain these codec additions; no version bump or upload
occurred. The next alpha must use a new synchronized version; the existing
`0.1.0-alpha.1` has already been published and must not be reused.

Verification: `just agent-pre-stop-gate` passed, including 115 harness tests
and Rust/Python/Node/browser WASM parity. `just test-dart`, workbench checking,
and `just release-check` passed; installed Python and Node/browser WASM archives
each consumed all 26,957 active vectors. These archives were built from a dirty
working tree with the existing version and are local preparation evidence, not
publishable release evidence. Logs: `target/anjal-final-gate.log`,
`target/anjal-final-dart.log` and `target/anjal-release-check.log`.

Release candidate version: `0.1.0-alpha.2` (Python `0.1.0a2`). On 2026-11-01
the six crates, PyPI and npm showed only the previously recorded alpha release
(and npm stage version); recheck availability when preparing a release. Bump and
regenerate versions in a dedicated release batch, then verify artifacts from the
reviewed committed source according to `docs/releases/policy.md`.

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
