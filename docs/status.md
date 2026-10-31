# Project handoff

Updated: 2026-10-31. Branch: `master`. Last published-status commit: `08748af`.
The publishing/development harness changes following that commit are complete
and local, awaiting commit/push; inspect `git status` for their current state.

## Current objective

The TSCII IANA byte audit expanded the unreleased decoder and encoder to all
assigned single-byte slots and corrected repeated HA byte errors. The profile has
341 byte keys and 340 canonical Unicode values. Its 22,791 active toolkit
vectors include independent audited byte and Grantha sequence cases. All
possible legacy variants and sequences remain outside the verified claim.
See [the byte audit](specs/codec-tscii-audit.md), the decoder and encoder
contracts, and [the roadmap](specs/codec-roadmap.md). The published alpha does
not contain this work; no version bump or upload was performed.

Verification: `just agent-pre-stop-gate` passed after a sequential rerun;
Rust, Python, Node/browser WASM, and Dart passed the shared corpus. The first
parallel attempt hit a Windows DLL lock. Logs: `target/tscii-audit-final-gate.log`
and `target/tscii-audit-dart.log`. Workbench TypeScript check passed.

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
passthrough, longest matching, and explicit canonical byte aliases. Detection,
Anjal, Vanavil, TAB, TAM and historical orthography remain future milestones.
Choose and source the next bounded codec profile before implementation.

After codec coverage is scoped, return to Punarchi, morphology, dialect
normalization, hyphenation, prosody, and PostgreSQL search. Each begins with a
sourced specification and golden vectors before algorithms.
