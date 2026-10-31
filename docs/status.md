# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

Finish reusable publishing rules and the development harness before starting
the next linguistic feature. Acceptance is in
[release-harness.md](specs/release-harness.md). Shared release-policy checks,
immutable source selection, artifact verification, and documentation are
implemented and locally verified. The full `just agent-pre-stop-gate` passed;
the final release-focused suite passed 37 tests and actionlint validated all
five workflows. See [acceptance evidence](specs/release-harness.md#acceptance-results-2026-10-31).
Log: `target/release-harness-full-gate.log`.

Next action: commit/push this infrastructure batch when requested, then define
the next bounded linguistic milestone. The changed workflows have not run on
GitHub yet; an explicit artifact dispatch is needed to establish remote
distribution evidence before a future publication. No new version was created
and no registry upload/account change was performed during this work.

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

Punarchi, morphology, dialect normalization, hyphenation, prosody, additional
legacy encodings/detection, and PostgreSQL search remain planned. A next
linguistic milestone has not been selected. Start with a bounded sourced
specification and acceptance criteria before algorithms.
