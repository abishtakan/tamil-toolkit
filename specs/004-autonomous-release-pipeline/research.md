# Research: Autonomous Release Pipeline & npm Dist-Tag Modernization

## 1. GitHub Actions Orchestration via GitHub CLI (`gh`)

### Context
Releasing `tamil-toolkit` requires dispatching two chained GitHub Actions workflows on branch `master`:
1. `alpha-artifacts.yml`: Multi-platform matrix build producing wheels, tarballs, and crates with `release-source.json` and `SHA256SUMS.json`.
2. `publish-release.yml`: Verifies reviewed commit SHA and artifact digests, then publishes to crates.io, npm, and PyPI.

### Decision
Use Python's standard `subprocess` invoking the officially installed and authenticated GitHub CLI (`gh`):
- To trigger artifacts build:
  ```bash
  gh workflow run alpha-artifacts.yml -f source_ref=master
  ```
- To locate the triggered workflow run and stream status:
  Use `gh run list --workflow=alpha-artifacts.yml --branch=master --limit=1 --json databaseId,headSha,status,conclusion` followed by `gh run watch <run_id> --exit-status`.
- To trigger publish:
  ```bash
  gh workflow run publish-release.yml -f artifact_run_id=<run_id> -f source_sha=<head_sha> -f confirm_publish=publish
  ```
- To watch publication:
  `gh run watch <publish_run_id> --exit-status`.

### Alternatives Considered
- Direct Python HTTP requests using `urllib` and GitHub REST API tokens: Rejected because `gh` is already authenticated with OAuth keyring in the environment, natively handles paging and token refreshes, and provides `gh run watch` streaming terminal output.

---

## 2. npm Dist-Tag Management (`latest` vs Channel Tags)

### Context
Currently, npm packages published during the alpha phase use `npm publish "$TARBALL" --tag "$NPM_TAG"`, where `NPM_TAG` is `alpha`.
Because version `0.1.0-alpha.1` was previously tagged as `latest`, npm's default landing page (`https://www.npmjs.com/package/tamil-toolkit`) and plain `npm install tamil-toolkit` remain frozen at `0.1.0-alpha.1`, even though `0.1.0-alpha.5` is published under `alpha`.

### Decision
1. **In `publish-release.yml`**:
   After `npm publish "$TARBALL" --tag "$NPM_TAG"`, add an explicit dist-tag command:
   ```bash
   npm dist-tag add "tamil-toolkit@$VERSION" latest
   ```
   This dual-tags the package: `alpha` points to `$VERSION` AND `latest` points to `$VERSION`.
2. **One-time reconciliation tool**:
   Provide `tools/release_npm_tags.py` exposed via `just npm-sync-tags` that uses npm CLI (with auth or via an authenticated GitHub dispatch / OIDC workflow) to immediately promote `0.1.0-alpha.5` to `latest`.

### Alternatives Considered
- Publish directly with `--tag latest`: Rejected as the primary tag because `release_policy.py` expects `--tag alpha` during the alpha channel; dual-tagging satisfies both policy and npm landing page requirements.
- Leave `latest` on `0.1.0-alpha.1` until 1.0.0: Rejected because users and documentation links expect the package landing page to show the current, actively maintained release.

---

## 3. Unified Testing CLI (`just release-test`)

### Context
Before initiating a release, an agent or developer must verify that the codebase satisfies all linters, formatting, Unicode normalization, 35,848 golden vectors across 3 runtimes, Dart tests, and archive packaging checks.

### Decision
Define a composite command `release-test` in `justfile` and `tools/tasks.py`:
- Step 1: `agent-pre-stop-gate` (formatting, unicode, clippy, unit tests, golden parity across Rust, Python, WASM).
- Step 2: `test-dart` (runs full Dart test suite against native FFI).
- Step 3: `release-check` (`tools/release.py all` — builds real crate, wheel, and npm archives in isolated temp venvs and tests consumer smoke imports).

### Alternatives Considered
- Running only unit tests: Insufficient because it does not test wheel compilation or isolated consumer imports.
- Running `release-test` inside GitHub Actions only: Too slow for local developer/agent feedback loop (10-15 mins vs < 2 mins locally).

---

## 4. Release Orchestration CLI (`tools/release_pipeline.py`)

### Context
An autonomous agent needs a single script that coordinates the local and remote phases with clear status output, failure handling, and idempotency.

### Decision
Implement `tools/release_pipeline.py` with the following stages:
1. **Pre-flight**:
   - Check `git status --porcelain` is empty.
   - Check current branch is `master`.
   - Check `gh auth status` exits 0.
   - Run `release_policy.py check`.
2. **Version Bump**:
   - Run `release_policy.py prepare <version> --lockfile --changelog`.
   - Git commit: `git commit -am "release: <version>"`.
   - Git push: `git push origin master`.
3. **Artifact Generation**:
   - Trigger `gh workflow run alpha-artifacts.yml -f source_ref=master`.
   - Poll and watch run to completion (`gh run watch`).
   - Extract `run_id` and 40-character `head_sha`.
4. **Publishing**:
   - If `--dry-run` is passed, stop here and report artifacts URL.
   - Otherwise, trigger `gh workflow run publish-release.yml -f artifact_run_id=<run_id> -f source_sha=<head_sha> -f confirm_publish=publish`.
   - Watch publish run to completion.
5. **Finalization**:
   - Run `release_policy.py release-record <run_id>`.
   - Create Git tag: `git tag -a "v<version>" -m "Release <version>"`.
   - Git commit release record: `git commit -am "docs: record release <version>"`.
   - Push commits and tags: `git push origin master --tags`.
