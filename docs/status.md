# Project handoff

Updated: 2026-11-01. Branch: `master`. Current release source:
`af11c96ddacd0fedda0cc8c346130a71f924c0b6` (`0.1.0-alpha.2`). Operational
workflow fixes are on master after that source commit; release artifacts remain
bound to the reviewed source SHA. See [alpha-2 release record](releases/alpha-2.md).

## Current status: alpha 2 released

The immutable artifact build passed in
[run 41237000066](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237000066).
The reviewed release is published on crates.io, npm and PyPI, and tag
[`v0.1.0-alpha.2`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.2)
points to the release source.

- crates.io: `tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`,
  `tamil-codec`, and `tamil-toolkit`, all `0.1.0-alpha.2`.
- npm: [`tamil-toolkit@0.1.0-alpha.2`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.2)
  is published using the configured OIDC trusted publisher. A fresh public
  installation passed all 26,957 active golden rows through Node and
  browser-target WASM. The `alpha` tag points at alpha 2; `latest` remains alpha 1.

- PyPI: `tamil-toolkit 0.1.0a2`. OIDC publisher run
  [41237423572](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237423572)
  passed the configured `pypi` reviewer gate. Public artifact digests matched
  the reviewed wheels/source archive; a fresh Windows CPython 3.13.7 install
  passed all 26,957 active golden rows.

Publisher run links, registry checksums, and the full artifact inventory are
recorded in [releases/alpha-2.md](releases/alpha-2.md). Earlier publisher
workflow run 41237404162 failed before upload because Cargo 1.95 removed the
dry-run crate archive. The workflow now runs `cargo package` to retain an
archive for comparison. The retry passed; the failed run published nothing.
The final Core Rust CI run
[41238338654](https://github.com/abishtakan/tamil-toolkit/actions/runs/41238338654)
passed after pinning actionlint's official release and verifying its SHA-256.

The local shell does not have Cargo on `PATH`, so its `just agent-post-edit`
attempt stopped with “Missing cargo”. The release source itself previously
passed the complete agent gate, Dart, workbench checks/build, Unicode and
release-policy checks, and `just release-check`; see `alpha-2.md` for details.

## Scope and next development

Alpha 2 adds bounded TSCII, TAB, TAM, and Anjal byte conversion. These profiles
do not claim automatic detection or complete historical font coverage. The
current active golden suite contains 26,957 rows; planned Punarchi remains
inactive until sourced Nannool rules and a licensed lexicon exist.

Pub.dev/Dart distribution and PostgreSQL packaging remain deferred. Next, choose
and source the next codec profile or begin Punarchi specification work. Continue
to follow [development workflow](development.md),
[publishing policy](releases/policy.md), and the agent constitution.

Never put registry credentials in the handoff, repository, build artifacts, or
chat. Do not claim complete linguistic support from the bootstrap suites.
