# Implementation Plan: Autonomous Release Pipeline & npm Dist-Tag Modernization

**Branch**: `004-autonomous-release-pipeline` | **Date**: 2026-11-05 | **Spec**: [spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/004-autonomous-release-pipeline/spec.md)

**Input**: Feature specification from `specs/004-autonomous-release-pipeline/spec.md`

## Summary

Deliver a fully autonomous, single-command release workflow (`just release <version>`) that handles git hygiene verification, atomic version bumps across all manifests, remote matrix artifact builds via GitHub Actions, and coordinated publishing to crates.io, npm, and PyPI. Additionally, resolve the npm dist-tag limitation by dual-tagging releases (`latest` and channel tags) so the npm package landing page always reflects the active release, and provide a unified pre-release test command (`just release-test`).

## Technical Context

**Language/Version**: Python 3.11+ / PowerShell / GitHub Actions YAML / Bash

**Primary Dependencies**: GitHub CLI (`gh`), `tomllib`, standard Python libraries (`subprocess`, `urllib`, `json`), `just`

**Storage**: Local file system (manifests, locks, release documentation) and Git repository

**Testing**: Python `pytest`, `cargo test`, `vitest`, `dart test`, and mock/dry-run release verification (`tools/release.py all`)

**Target Platform**: Cross-platform CLI orchestrator (Windows, macOS, Linux) communicating with GitHub Actions

**Project Type**: Developer tooling, build automation, and CI/CD release pipeline

**Performance Goals**:
- Pre-release test gate (`just release-test`) completes in `< 2 minutes` locally.
- Autonomous release orchestrator streams remote GitHub Actions logs in real-time.

**Constraints**:
- Strict adherence to repository release policy (`release-policy.toml`).
- Zero version drift across Rust workspace, Python `pyproject.toml`, and npm `package.json`.
- Fail-safe abort on dirty working tree, unauthenticated `gh`, or any remote build failure.

**Scale/Scope**: Covers all 6 public crates, Python wheel/sdist packages, npm WebAssembly package, and release records.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle VI (Platform-Conforming Distribution & Policy-Governed Releases)**: PASS. All version numbers derive authoritatively from Cargo's workspace version; publishing adheres strictly to `release-policy.toml` allowlist and dependency order.
- **Principle VII (Explicit Guarantees & Rigorous Quality Gates)**: PASS. `just release-test` executes all quality gates and dry-run archive validations prior to any remote release dispatch.

No constitutional violations exist.

## Project Structure

### Documentation (this feature)

```text
specs/004-autonomous-release-pipeline/
├── spec.md                 # Feature specification
├── plan.md                 # This implementation plan
├── research.md             # Research on GH CLI orchestration & npm dist-tags
├── data-model.md           # Entities and stage state machine
├── quickstart.md           # Runnable validation guide
├── contracts/
│   ├── cli-release-pipeline.md    # CLI interface contracts
│   └── github-workflow-contract.md # GitHub Actions job contracts
└── checklists/
    └── requirements.md     # Quality checklist
```

### Source Code Changes

```text
tools/
├── release_pipeline.py     # New autonomous release orchestrator CLI
├── release_npm_tags.py     # New npm dist-tag reconciliation utility
├── tasks.py                # Add 'release-test' task combining pre-stop + dart + release-check
└── release_policy.py       # Update dist-tag verification if needed

.github/workflows/
└── publish-release.yml     # Update npm job to dual-tag with 'latest'

justfile                    # Expose 'release', 'release-test', and 'npm-sync-tags'
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| *None* | *N/A* | Standard repository release patterns and existing GitHub CLI tooling are utilized without external complexity. |
