# CLI Contract: Autonomous Release Pipeline

## 1. Unified Test Gate Command

### Syntax
```bash
just release-test
# or
uv run --locked python tools/tasks.py release-test
```

### Behavior
- Executes:
  1. `agent-pre-stop-gate` (formatting, clippy, unit tests, golden parity).
  2. `test-dart` (Dart FFI bindings & tests).
  3. `tools/release.py all` (repackages real crates, wheels, npm tarballs, and runs isolated smoke tests).
- Exit Codes:
  - `0`: All test suites, linters, and package packaging checks passed cleanly.
  - `1`: Any test, lint, or packaging check failed (with stderr/stdout logs).

---

## 2. Autonomous Release Orchestrator

### Syntax
```bash
just release <version> [--dry-run]
# or
uv run --locked python tools/release_pipeline.py release <version> [--dry-run]
```

### Arguments
- `<version>`: Required semantic version string adhering to release policy (e.g. `0.1.0-alpha.6`).
- `--dry-run`: Optional flag. When passed, the pipeline runs all pre-flight checks, bumps version, pushes commit, and verifies the remote artifact build (`alpha-artifacts.yml`), but halts before triggering `publish-release.yml`.

### Exit Codes
- `0`: Release completed successfully across crates.io, npm, and PyPI, and release documentation recorded.
- `1`: Failure at any stage (dirty git tree, unauthenticated `gh`, matrix build failure, registry publishing rejection).

---

## 3. npm Dist-Tag Synchronization

### Syntax
```bash
just npm-sync-tags [<version>]
# or
uv run --locked python tools/release_npm_tags.py [--version <version>]
```

### Behavior
- Points npm's `latest` dist-tag for `tamil-toolkit` to the specified version (defaulting to the active workspace version in `Cargo.toml`).
- Ensures the default package page on npmjs.com matches the newest active release.
