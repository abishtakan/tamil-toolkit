# Quickstart & Validation Guide: Autonomous Release Pipeline

This guide demonstrates how an engineer or AI agent validates and runs the release pipeline end-to-end.

---

## 1. Prerequisites

1. Working directory clean (`git status --porcelain` is empty).
2. GitHub CLI `gh` installed and authenticated:
   ```bash
   gh auth status
   ```
3. Network connectivity to GitHub, crates.io, npm, and PyPI.

---

## 2. Step 1: Execute Complete Pre-Release Test Gate

Run the unified test command to verify all runtimes and smoke package builds locally:

```bash
just release-test
```

**Expected Result**:
- Formatting, Unicode, Clippy pass.
- 35,848 golden vectors pass across Rust, Python, and Vitest.
- Dart tests pass.
- Isolated package archives and smoke consumers build cleanly.
- Command exits with code 0 in `< 2 minutes`.

---

## 3. Step 2: Immediate Reconciliation of npm `latest` Tag

To immediately fix the npm package landing page for the currently published version (`0.1.0-alpha.5`):

```bash
just npm-sync-tags
```

**Expected Result**:
- `npm view tamil-toolkit dist-tags` shows:
  ```json
  {
    "alpha": "0.1.0-alpha.5",
    "latest": "0.1.0-alpha.5"
  }
  ```
- Visiting `https://www.npmjs.com/package/tamil-toolkit` displays `0.1.0-alpha.5`.

---

## 4. Step 3: Trigger Autonomous Release

To release a new version (e.g. `0.1.0-alpha.6`) completely unattended:

```bash
just release 0.1.0-alpha.6
```

### Dry-Run Mode (Safe Test):
To test the pipeline without uploading to registries:
```bash
just release 0.1.0-alpha.6 --dry-run
```

**Expected Result**:
1. Verifies git cleanliness and runs pre-flight checks.
2. Updates `Cargo.toml`, `Cargo.lock`, `pyproject.toml`, `package.json`, and scaffolds release doc.
3. Commits and pushes `release: 0.1.0-alpha.6` to `master`.
4. Triggers `alpha-artifacts.yml` and streams progress until completion.
5. In dry-run mode, exits with artifact run URL. In normal mode, triggers `publish-release.yml`.
6. Confirms successful upload to crates.io, npm (with dual-tag), and PyPI.
7. Generates `docs/releases/alpha-6.md`, creates tag `v0.1.0-alpha.6`, and pushes tag and documentation to GitHub.
