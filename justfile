set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

default:
    @just --list

# Install locked dependencies and build host Python plus Node/browser WASM packages.
bootstrap:
    uv run --locked python tools/tasks.py bootstrap

doctor:
    uv run --locked python tools/tasks.py doctor

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
