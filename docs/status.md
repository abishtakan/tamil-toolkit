# Project handoff

Updated: 2026-11-01. Branch: `master`. Current release source:
`af11c96ddacd0fedda0cc8c346130a71f924c0b6` (`0.1.0-alpha.2`). Operational
workflow fixes are on master after that source commit; release artifacts remain
bound to the reviewed source SHA. See [alpha-2 release record](releases/alpha-2.md).

## Current objective: finish alpha 2 publication

The immutable artifact build passed in
[run 41237000066](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237000066).
The six approved crates and npm package are published:

- crates.io: `tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`,
  `tamil-codec`, and `tamil-toolkit`, all `0.1.0-alpha.2`.
- npm: [`tamil-toolkit@0.1.0-alpha.2`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.2)
  is published using the configured OIDC trusted publisher. A fresh public
  installation passed all 26,957 active golden rows through Node and
  browser-target WASM. The `alpha` tag points at alpha 2; `latest` remains alpha 1.

PyPI run [41237423572](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237423572)
is waiting for the required `pypi` environment reviewer. The user must approve
the deployment in GitHub. Once the run succeeds, verify public PyPI digests,
install `tamil-toolkit==0.1.0a2` in a fresh interpreter, and run
`tools/release_smoke/python_consumer.py` against all active rows. Then create
and push immutable tag `v0.1.0-alpha.2` at the reviewed source SHA and finalize
the release record and handoff. Do not tag before PyPI and its public consumer
pass.

Publisher run links, registry checksums, and the full artifact inventory are
recorded in [releases/alpha-2.md](releases/alpha-2.md). Earlier publisher
workflow run 41237404162 failed before upload because Cargo 1.95 removed the
dry-run crate archive. The workflow now runs `cargo package` to retain an
archive for comparison. The retry passed; the failed run published nothing.
The follow-up Core Rust CI run 41237811990 succeeded after pinning actionlint's
official release and verifying its SHA-256.

The local shell does not have Cargo on `PATH`, so its `just agent-post-edit`
attempt stopped with “Missing cargo”. The release source itself previously
passed the complete agent gate, Dart, workbench checks/build, Unicode and
release-policy checks, and `just release-check`; see `alpha-2.md` for details.

## Scope and next development

Alpha 2 adds bounded TSCII, TAB, TAM, and Anjal byte conversion. These profiles
do not claim automatic detection or complete historical font coverage. The
current active golden suite contains 26,957 rows; planned Punarchi remains
inactive until sourced Nannool rules and a licensed lexicon exist.

Pub.dev/Dart distribution and PostgreSQL packaging remain deferred. After the
alpha 2 release is complete, choose and source the next codec profile or begin
Punarchi specification work. Continue to follow [development workflow](development.md),
[publishing policy](releases/policy.md), and the agent constitution.

Never put registry credentials in the handoff, repository, build artifacts, or
chat. Do not claim complete linguistic support from the bootstrap suites.
