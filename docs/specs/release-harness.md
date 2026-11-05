# Release and development harness contract

Status: implemented and verified locally on 2026-10-31. This is infrastructure work; it introduces
no Tamil behavior and leaves the published alpha versions unchanged.

## Acceptance

1. One release policy defines the public Rust crate allowlist in dependency
   order, permitted registries, branch, and release channel. Cargo's workspace
   version owns the release number; Python's equivalent and npm must match it.
   Planned crates, FFI crates, Dart, PostgreSQL, and the root npm
   workspace remain excluded from publication.
2. A fast local command rejects version, dependency, package-scope, or channel
   drift. It runs in the edit gate and lightweight GitHub CI. Regression tests
   demonstrate rejection, including attempts to expose an unfinished crate.
3. Artifact builds resolve a source ref once. Every platform checks out that
   exact commit and records the same source identity, versions, and public
   scope beside its SHA-256 inventory. The expensive matrix runs on explicit
   dispatch; ordinary development retains the small Rust/Unicode CI gate.
4. Publishing remains manual, defaults to no publication, and requires an
   explicitly supplied reviewed 40-character commit plus a successful artifact
   run from the repository's release workflow on master. Every downloaded
   artifact must match that commit, release identity, and digest before upload.
   Publishing jobs for a registry serialize without cancelling an active upload.
5. Rust publishes one approved crate at a time. A dry-run repackage must match
   the reviewed archive's file contents, except Cargo's generated Cargo.lock:
   local verification patches use path sources; publication resolves the
   already published sibling crates from crates.io. Python uploads exactly the
   supported three wheels and one source archive. npm checks both Node builds
   agree and uses the policy's prerelease tag. Old release numbers are not
   embedded in the reusable gates.
6. Durable docs explain feature/specification order, local versus remote
   verification, version updates, registry credentials, release review,
   publication recovery, and context handoff. Agent instructions route to
   these docs. Historical first-alpha evidence stays preserved.

## Verification

Run release-policy failure-path tests, the existing release acceptance tests,
workflow syntax validation, `just agent-post-edit`, and the local full harness
gate. Exercise artifact checks using local downloaded alpha artifacts where
available. No registry publication or remote account changes are needed.

## Acceptance results (2026-10-31)

- `just agent-pre-stop-gate` passed on Windows/MSVC: formatting,
  Unicode/schema/source-copy checks, locked workspace check, clippy,
  21 Rust tests and doctests, harness, rebuilt bindings, and real golden parity.
  Its integration run passed 97 harness tests; the final focused release suite
  subsequently passed 37 tests, including the additional clean-source/license
  guards and a fully synchronized future-version regression.
- Python parity reported 21,285 passing tests; Vitest reported 21,283. The
  active shared corpus remains 21,277 rows; the extra assertions cover adapters.
- Actionlint 1.7.12 validated all five workflows. Archive parsing/metadata
  checks passed against 14 real downloaded first-alpha archives, without
  assigning those historical bytes a new source identity.
- The final edit gate and release-source-copy check passed. Local integration
  log: `target/release-harness-full-gate.log`.

The changed workflows have not been dispatched remotely. They require a
committed/pushed source and explicit dispatch to establish remote evidence.
Existing registry versions and account configuration were left unchanged.

## Autonomous Release Pipeline

As of `specs/004-autonomous-release-pipeline`, an engineer or AI agent can trigger the complete release workflow through unified CLI commands:

- `just release-test`: One-command execution of the pre-release test matrix (formatting, clippy, unit tests, 35,848+ golden vectors across Rust, Python, and WebAssembly, Dart tests, and mock archive packaging smoke tests).
- `just release <version>`: End-to-end autonomous release orchestrator (`tools/release_pipeline.py`). Performs git hygiene checks, bumps version numbers across all manifests, pushes to `master`, dispatches & monitors `alpha-artifacts.yml` on GitHub Actions, triggers & monitors `publish-release.yml`, generates the immutable release record in `docs/releases/`, and tags the git commit.
  - Supports `--dry-run` to stop safely after artifact matrix verification without publishing to registries.
- `just npm-sync-tags [<version>]`: Synchronizes npm registry dist-tags (`tools/release_npm_tags.py`) so that the package default landing page and unadorned `npm install tamil-toolkit` point to the current active release.

## Limits

Checks and instructions are guardrails, not an OS sandbox. Local checks do not
prove remote account configuration. Pub.dev and PostgreSQL packaging remain deferred.
Remote matrix artifact builds require valid GitHub CLI (`gh`) authentication with `repo` and `workflow` scopes.
