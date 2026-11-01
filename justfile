set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

default:
    @just --list

# Install locked dependencies and build host Python plus Node/browser WASM packages.
bootstrap:
    uv run --locked python tools/tasks.py bootstrap

doctor:
    uv run --locked python tools/tasks.py doctor

# Fast package scope/version checks and the dependency-ordered release inventory.
check-release-policy:
    uv run --locked python tools/release_policy.py check

release-status:
    uv run --locked python tools/release_policy.py status

# Deterministically bump versions, sync READMEs/crates, and prepare release records.
release-prepare version:
    uv run --locked python tools/release_policy.py prepare {{version}} --lockfile

# Generate or update the release record from a distribution artifact run.
release-record run_id:
    uv run --locked python tools/release_policy.py release-record {{run_id}}

# Refresh checked distribution copies from canonical lexicon/license sources.
sync-release-files:
    uv run --locked python tools/release_files.py

check-release-files:
    uv run --locked python tools/release_files.py --check

# Actual archives and isolated consumers; does not upload to any registry.
release-check:
    uv run --locked python tools/release.py all

check-unicode:
    uv run --locked python tools/tasks.py check-unicode

# Uses nextest when installed; otherwise cargo test, including 10,000-case properties.
test-rust:
    uv run --locked python tools/tasks.py test-rust

sync-bindings:
    uv run --locked python tools/tasks.py sync-bindings

# Rebuild first: stale Python extensions or WASM never satisfy parity.
test-parity:
    uv run --locked python tools/tasks.py test-parity

test-dart:
    uv run --locked python tools/tasks.py test-dart

test-harness:
    uv run --locked python tools/tasks.py test-harness

agent-post-edit:
    uv run --locked python tools/tasks.py agent-post-edit

agent-pre-stop-gate:
    uv run --locked python tools/tasks.py agent-pre-stop-gate
