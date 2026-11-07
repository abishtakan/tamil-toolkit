# Feature Specification: Autonomous Release Pipeline & npm Dist-Tag Modernization

**Feature Branch**: `004-autonomous-release-pipeline`

**Created**: 2026-11-05

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "what's the current release workflow is it well optimised or have any blockers. it should be very autonomous if i tell ai agent to release the new version it should easily do it. like one cli command for testing. then release it. other than your finding the npm default page stays 0.1.0-alpha.1 . it has latest tag i guess."

## Clarifications

### Session 2026-11-05

- Q: How should the autonomous release command handle the transition from artifact verification to permanent registry publication? → A: Unattended by default with an explicit `--dry-run` flag to stop before publishing.
- Q: How should the npm `latest` dist-tag behave for active alpha releases? → A: Dual-tag both `latest` and `alpha` so npm homepage and `npm install tamil-toolkit` automatically serve the newest active release.
- Q: What level of automation should the release CLI command provide? → A: Full autonomous pipeline (`just release <version>`) executing test verification, version bump, push, artifact build wait, publish dispatch wait, release record generation, tagging, and push.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Autonomous End-to-End Release Execution (Priority: P1)

An engineer or an autonomous AI agent needs to release a new version of `tamil-toolkit` (e.g. `0.1.0-alpha.6`) across all three public registries (crates.io, npm, and PyPI) by issuing a single high-level CLI command, without having to manually monitor GitHub Actions tabs, copy run IDs or 40-character commit hashes, or trigger multiple separate workflows by hand.

**Why this priority**: Eliminates human friction, context switching, and procedural mistakes during releases. Releases become reproducible, deterministic, and fully executable by AI coding agents.

**Independent Test**: Running the release command with a target version in a clean repository prepares the release, triggers the remote matrix build, watches for completion, dispatches publication, verifies registry indexes, and generates the permanent release ledger documentation automatically.

**Acceptance Scenarios**:

1. **Given** a clean git working directory on `master` with passing test suites, **When** the agent invokes the release command `just release <version>` (or `python tools/release_pipeline.py release <version>`), **Then** the pipeline bumps version across all crate manifests, locks, and package files, commits and pushes to `master`, dispatches `alpha-artifacts.yml`, watches the run to success, extracts `run_id` and source commit SHA, dispatches `publish-release.yml`, confirms publication across crates.io, npm, and PyPI, and updates `docs/releases/<record>.md`.
2. **Given** an uncommitted modification or dirty git state, **When** the release command is initiated, **Then** the pipeline halts immediately before modifying any version numbers or making any commits, returning an explicit error message.
3. **Given** a failure in the remote matrix build (e.g. build failure on macOS wheel), **When** the artifact workflow fails, **Then** the pipeline halts immediately, outputs the GitHub Actions log URL, and refuses to trigger `publish-release.yml`.

---

### User Story 2 - npm Default Landing Page & Dist-Tag Synchronization (Priority: P2)

When users navigate to `https://www.npmjs.com/package/tamil-toolkit` or run `npm install tamil-toolkit`, they should see and receive the newest approved release rather than having the default npm package page frozen at `0.1.0-alpha.1`.

**Why this priority**: Currently, npm releases for alpha versions are published exclusively under `--tag alpha`. Because `0.1.0-alpha.1` was tagged `latest`, npm's default landing page permanently displays `0.1.0-alpha.1`, misleading consumers about the library's active state and features.

**Independent Test**: Inspecting npm registry dist-tags (`npm view tamil-toolkit dist-tags`) reveals that the default tag resolves to the active release version, and subsequent releases automatically update the designated landing tag.

**Acceptance Scenarios**:

1. **Given** a new version publication to npm, **When** the npm publish job completes, **Then** npm dual-tags the release with both the channel tag (`alpha`) and `latest` (`npm publish --tag <channel>` followed by `npm dist-tag add tamil-toolkit@<version> latest`), ensuring the npmjs.com homepage and `npm install tamil-toolkit` automatically serve the newest active release.
2. **Given** existing published versions where `latest` is stalled at `0.1.0-alpha.1`, **When** the dist-tag synchronization step runs, **Then** `latest` is retagged to match the current active release (`0.1.0-alpha.5`).

---

### User Story 3 - Unified One-Command Pre-Release Test Gate (Priority: P3)

Before authorizing or executing a release, an engineer or AI agent needs a single CLI command that runs the full, non-destructive test matrix across all three runtimes, including linters, formatters, golden vector parity, and distribution packaging smoke checks.

**Why this priority**: Guarantees zero regressions and confirms that every package artifact can be built and imported in isolated consumer environments before any version commit or git tag is created.

**Independent Test**: Running `just release-test` executes all formatting, clippy, Rust unit/doctests, Python pytest, Vitest WASM, Dart tests, all 35,848 golden vectors, and dry-run release packaging checks in one unattended invocation.

**Acceptance Scenarios**:

1. **Given** code changes in the repository, **When** `just release-test` is run, **Then** it validates code format, clippy (-D warnings), all unit tests, golden parity across Rust, Python, Node WASM, and Web WASM, Dart tests, and distribution archive creation (`tools/release.py all`), exiting 0 only if all gates pass.
2. **Given** any lint failure, test regression, or golden vector mismatch, **When** `just release-test` runs, **Then** it fails fast with the specific failing target and error trace, preventing release execution.

---

### Edge Cases

- **GitHub CLI Authentication Failure**: What happens if `gh` is not installed or not authenticated? The pipeline must detect `gh` presence and auth status upfront, exiting with a clear instruction before making changes.
- **Remote Branch Protection / Direct Push Blocked**: What happens if `git push origin master` is rejected due to GitHub branch protection rules? The tool must detect push rejection, offer a branch/PR fallback mode, and explain how to proceed.
- **Registry Propagation Lag**: What happens if crates.io or npm takes 30–60 seconds to index a newly published package before the next dependent crate or release record can see it? The pipeline must implement bounded exponential backoff polling (e.g. up to 12 attempts at 5-second intervals) before timing out.
- **PyPI Environment Review Gate**: What happens if the GitHub Actions `pypi` environment requires manual human approval? The pipeline must recognize the `waiting` / pending approval status, notify the user with the direct review URL, and wait cleanly without crashing.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single top-level CLI command (`just release-test`) that performs the complete pre-release test and verification gate across all runtimes (Rust, Python, WebAssembly, Dart), linters, formatting, and archive build tests.
- **FR-002**: The system MUST provide an autonomous release command (`just release <version>` / `python tools/release_pipeline.py release <version>`) that orchestrates the entire release lifecycle without requiring manual monitoring or copying of intermediate hashes.
- **FR-003**: The autonomous release command MUST verify that the local git repository is on branch `master`, has no uncommitted changes, and is synchronized with `origin/master` before modifying files.
- **FR-004**: The release command MUST invoke `release_policy.py prepare <version> --lockfile --changelog`, create an atomic release commit, and push it to the remote repository.
- **FR-005**: The release command MUST trigger the GitHub Actions workflow `alpha-artifacts.yml` using the GitHub CLI, monitor its progress until successful completion, and extract the artifact `run_id` and full 40-character source commit SHA.
- **FR-006**: The release command MUST dispatch the GitHub Actions workflow `publish-release.yml` with the extracted `artifact_run_id`, `source_sha`, and `confirm_publish=publish`, streaming or polling workflow status until all publishing jobs succeed.
- **FR-007**: The release command MUST automatically generate the release ledger via `release_policy.py release-record <run_id>`, commit the resulting `docs/releases/<record>.md`, tag the commit with `v<version>`, and push tags and documentation to the remote repository.
- **FR-008**: The release and publishing workflow MUST ensure that npm registry dist-tags reflect the newest active release on the package's primary landing page on npmjs.com by dual-tagging the published tarball with both the channel tag and `latest` (using OIDC trusted publishing in `publish-release.yml`).
- **FR-009**: The pipeline MUST provide a one-time dist-tag reconciliation command (`just npm-sync-tags`) to immediately point `latest` to the current active release (`0.1.0-alpha.5`) on npm.
- **FR-010**: The release command MUST execute unattended by default when all test gates and artifact verification succeed, and MUST support a `--dry-run` flag that builds and verifies all artifacts remotely without triggering `publish-release.yml`.

### Key Entities

- **ReleasePolicy**: Defines release channel, authorized public crates in dependency order, allowed registries, and version format rules.
- **ArtifactRun**: A completed GitHub Actions run of `alpha-artifacts.yml` containing compiled platform wheels, tarballs, and crates accompanied by `release-source.json` and `SHA256SUMS.json`.
- **ReleaseRecord**: An immutable markdown document (`docs/releases/<name>.md`) recording the reviewed commit SHA, workflow run URLs, and authoritative registry SHA-256 checksums from crates.io, PyPI, and npm.
- **DistTag**: An npm registry pointer (e.g. `latest`, `alpha`) associating a symbolic channel name with a specific semantic version number.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer or AI agent can trigger a complete release with exactly **one CLI command** (`just release <version>`), requiring zero manual intervention when GitHub secrets and permissions are in place.
- **SC-002**: Complete pre-release test verification can be executed in under **2 minutes** locally via `just release-test`.
- **SC-003**: The npm default package page (`https://www.npmjs.com/package/tamil-toolkit`) displays the newest release version rather than staying pinned to `0.1.0-alpha.1`.
- **SC-004**: Zero false releases or dirty state commits — 100% of releases produce verifiable cryptographic digests and an immutable release record matching the reviewed git commit.

---

## Assumptions

- The operator (user or AI agent) has GitHub CLI `gh` installed and authenticated with `repo` and `workflow` permissions to `abishtakan/tamil-toolkit`.
- GitHub repository secrets contain the necessary credentials (`CARGO_REGISTRY_TOKEN` for crates.io; OIDC trusted publishing is configured for npm and PyPI).
- Network access to GitHub API, crates.io API, npmjs API, and PyPI API is available during release execution.
- If branch protection rules require pull requests for `master`, a PR-based variant or branch bypass is available for release commits.
