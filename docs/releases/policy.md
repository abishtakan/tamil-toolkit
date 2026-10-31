# Publishing policy

`release-policy.toml` defines release scope and dependency order.
`Cargo.toml`'s workspace version defines the release number. Use
`just release-status` to inspect these values and `just check-release-policy`
to detect drift. The checker is also part of `just check-unicode` and CI.

## What can ship

Only the crates in `public_crates` may reach crates.io. Their approved behavior
is exposed through the Python and npm umbrella packages. A new module needs
sourced specifications, active golden suites, Rust and binding parity, license
evidence, standalone archive verification, and release review before joining
the list and the umbrella dependencies. Active suites and specifications are
necessary evidence; their existence alone does not prove linguistic completion.

The workspace defaults to `publish = false`. FFI support crates, planned
modules, root npm workspace, workbench, Dart/Pub.dev, and PostgreSQL stay private
or deferred. A module can develop locally without becoming publishable.

Publication is an explicit release action using the session's existing user
authorization. Do not ask again when authorization already covers the action.
Normal edits, commits, pushes, tags, and passing CI do not trigger uploads.
Every publisher is manual, defaults to `confirm_publish=no`, runs on `master`,
and serializes uploads for its registry without cancelling an active publish.

## Versioning

Develop against the current version until a release batch is prepared. Do not
bump versions or publish after each feature or documentation commit. Record
changes under `CHANGELOG.md`'s Unreleased section.

The public SDK uses one synchronized release number. For an alpha release,
Rust/npm `X.Y.Z-alpha.N` corresponds to Python `X.Y.ZaN`; beta and rc use `bN`
and `rcN`. Stable versions use `X.Y.Z` everywhere. The policy's channel must
match the version: alpha/beta/rc use their named npm tag; stable uses `latest`.
The initial npm alpha currently also has a `latest` tag; that historical state
is recorded in the release runbook. Prerelease workflows explicitly select
their channel and do not request promotion to `latest`.

When preparing a release:

1. Choose the next version and write its bounded changes and compatibility
   notes. Returned errors, operation names, key formats, and Unicode behavior
   are public contracts. Explain any breaking change even during alpha.
2. Update the workspace version and all exact local `tamil-*` dependency pins
   in `Cargo.toml`, each public crate's docs.rs link, Python's project version,
   and the npm package version. Change the policy channel only if appropriate.
3. Run `cargo update --workspace` and review Cargo.lock for unintended dependency
   changes. Cargo documents this option for workspace version updates; it may
   add dependencies that were absent from the lockfile. Refresh generated
   crate READMEs/data/notices with `just sync-release-files`.
4. Run `just check-release-policy` and `just check-unicode`. Finish the release
   notes and local gates below, commit the reviewed source, and record its full
   SHA. Published versions and existing release tags must never be reused or
   moved. The first alpha has already been uploaded to all three registries.

## Development and release checks

| Stage | Required evidence |
| --- | --- |
| During edits | `just agent-post-edit`; focused checks for affected behavior |
| Feature integration | `just agent-pre-stop-gate`; Dart/workbench checks when affected |
| Release preparation | Full integration gate, `just test-dart`, workbench checks, `just release-check` |
| Normal GitHub CI | Ubuntu Rust/Unicode checks, release-policy regression tests, workflow lint |
| Explicit distribution build | Rust archive/MSRV, Node 22/24, three wheel platforms, CPython consumers |
| After publication | Fresh public installs, active golden consumers, links and digests in release record |

Local `just release-check` builds archives and real isolated consumers. It can
inspect a dirty working tree for preparation; those files are not release
evidence for publishing. The remote artifact run packages the committed source
selected below. Required metadata/digests are generated there for every target.
Node execution of the browser WASM target does not establish browser UI support.

## Build once, review, publish

1. Dispatch **Alpha distribution artifacts** (`alpha-artifacts.yml`) from
   `master` with `source_ref` set to the full reviewed commit. It resolves the
   source once; all jobs check out that immutable SHA. The expensive workflow
   runs only when explicitly dispatched and has no registry credentials.
2. Require the entire run to succeed. Download and review the archives,
   `SHA256SUMS.json`, and `release-source.json`. Every artifact records the same
   source SHA, release versions, channel, and public crate scope. Record the
   run ID and full SHA in the release record. Artifacts from the old first-alpha
   harness lack this metadata and must not be reused with the new publishers.
3. Dispatch the appropriate publishing workflow from `master` with
   `artifact_run_id`, the full `source_sha`, and `confirm_publish=publish`.
   The gate validates the run's repository, workflow ID, successful completion,
   explicit dispatch, and master branch. It then checks out the reviewed SHA
   and verifies every relevant artifact's source identity and archive hashes.
4. Rust uses `publish-crate.yml`: supply one approved `package` and follow the
   `just release-status` order. Wait for each dependency to appear on crates.io
   before dispatching its dependents. A dry-run repackage compares every file
   with the reviewed crate. Only the archive-root Cargo.lock may differ because
   local artifact verification uses sibling path patches and publication uses
   published registry siblings. The actual upload uses the same reviewed tree.
5. Python uses `publish-pypi.yml`: it validates all three platforms, then uploads
   exactly three cp311-abi3 wheels and the Linux-built source archive. npm uses
   `publish-npm.yml`: it validates both Node artifacts, requires byte-identical
   tarballs, and publishes that tarball with the policy's channel tag.
6. Verify fresh public installs, record registry links, exact source, workflow
   runs, archive hashes, and consumer results in `docs/releases/README.md` and
   the version's release record. Create the new immutable version tag against
   the reviewed commit, then update `docs/status.md`.

## Accounts and credentials

| Registry | GitHub integration | Remaining manual configuration |
| --- | --- | --- |
| crates.io | Actions secret `CARGO_REGISTRY_TOKEN`; workflow `publish-crate.yml` | Keep token scoped to the finished crates; verified account email |
| PyPI | Trusted publisher for project `tamil-toolkit`, owner/repo `abishtakan/tamil-toolkit`, workflow `publish-pypi.yml`, environment `pypi` | Preserve the environment's required reviewer |
| npm | Workflow `publish-npm.yml` with OIDC; no npm token required | Configure package trusted publisher when the next release is ready: GitHub owner `abishtakan`, repo `tamil-toolkit`, workflow `publish-npm.yml`, blank environment, permit `npm publish` |
| Pub.dev / PostgreSQL | Deferred | A separate packaging/support milestone is required |

npm requires a new trusted publisher's first successful publish within two
days; configure it when the next version is ready. Its workflow filename must
continue to match the package setting. Never commit credentials or place them
in artifacts, handoff notes, or chat. If account input is needed, use the
registry's authenticated UI or the approved secret entry mechanism.

## Failed or partial uploads

Check registry state before retrying a failed workflow: an upload can succeed
even if a subsequent step or connection fails. Record completed packages and
retry only missing uploads from the same reviewed run and SHA. Do not enable
blanket skip-existing, replace archives, force-move tags, or publish a different
build under the same version. If the artifacts or source must change after any
upload, prepare a new version and repeat the review. Expired/missing artifacts
require a new complete artifact build and review.

## References

- [Cargo workspace lockfile updates](https://doc.rust-lang.org/cargo/commands/cargo-update.html)
- [npm trusted publishers and initial validation window](https://docs.npmjs.com/trusted-publishers/)
- [GitHub workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)
