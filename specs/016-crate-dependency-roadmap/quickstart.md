# Quickstart & Validation Guide: Crate Dependency DAG & Architecture Roadmap (`016`)

**Date**: 2026-11-08  
**Feature**: [spec.md](spec.md) | **Contract**: [dependency-dag-contract.md](contracts/dependency-dag-contract.md)

---

## 1. Overview

Feature `016-crate-dependency-roadmap` is a documentation, architecture specification, and policy-governance milestone. It establishes:
1. The normative architecture specification in [`docs/specs/architecture-roadmap.md`](../../docs/specs/architecture-roadmap.md) and [`specs/016-crate-dependency-roadmap/spec.md`](spec.md).
2. The synchronized project roadmap in [`ROADMAP.md`](../../ROADMAP.md).
3. The automated `Rank 0`–`Rank 6` DAG invariant check in [`tools/release_policy.py`](../../tools/release_policy.py) (`just check-release-policy`).

---

## 2. Validation Commands

### Step 1: Verify the Automated `Rank 0`–`Rank 6` Dependency DAG & Release Policy Gate
Run the policy checker from the repository root:

```powershell
python tools/release_policy.py check
```

**Expected Outcome**:
- Exits with code `0`.
- Verifies that every `crates/*/Cargo.toml`, `extensions/pg_tamil/Cargo.toml`, and `bindings/*/Cargo.toml` satisfies `Rank(dependency) < Rank(dependent)` across `[dependencies]`, `[build-dependencies]`, and `[dev-dependencies]`.

### Step 2: Run the Policy Unit Tests
Run the harness test suite for `release_policy.py`:

```powershell
uv run --locked pytest tests/harness/test_release_policy.py
```

**Expected Outcome**:
- All unit tests pass, including tests verifying that out-of-rank or circular dependencies in `[dependencies]`, `[build-dependencies]`, or `[dev-dependencies]` are rejected.

### Step 3: Verify Unicode, Schema & Workspace Integrity
Run the repository post-edit checks:

```powershell
python tools/check_unicode.py
cargo test --workspace
```

**Expected Outcome**:
- `check_unicode.py` passes with zero unescaped non-ASCII regressions in golden suites and all release file copies synchronized.
- `cargo test --workspace` compiles cleanly and passes all unit, integration, and doc tests with zero modifications to Rust crate logic.
