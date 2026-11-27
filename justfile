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
    uv run --locked python tools/release.py all --lexicon-profile default
    uv run --locked python -m tools.lexicon_dart_archive --profile default
    uv run --locked python tools/release.py all --lexicon-profile core
    uv run --locked python -m tools.lexicon_dart_archive --profile core
    uv run --locked python tools/release.py all --lexicon-profile full
    uv run --locked python -m tools.lexicon_dart_archive --profile full

# Explicit final runtime matrix; ordinary edit/parity gates use one selected profile.
lexicon-acceptance:
    uv run --locked python tools/tasks.py test-parity --lexicon-profile default
    uv run --locked python tools/tasks.py test-dart --lexicon-profile default
    uv run --locked python tools/tasks.py test-parity --lexicon-profile core
    uv run --locked python tools/tasks.py test-dart --lexicon-profile core
    uv run --locked python tools/tasks.py test-parity --lexicon-profile full
    uv run --locked python tools/tasks.py test-dart --lexicon-profile full

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

# Comprehensive pre-release test gate across all runtimes, clippy, golden parity, and packaging smoke checks.
release-test:
    uv run --locked python tools/tasks.py release-test

# Autonomous end-to-end release pipeline (testing, version bump, remote matrix build, and publishing).
release version *flags:
    uv run --locked python tools/release_pipeline.py release {{version}} {{flags}}

# Ensure npm registry dist-tags reflect the active release on npmjs.com.
npm-sync-tags *version:
    uv run --locked python tools/release_npm_tags.py {{version}}

# Build cleaned/organized .tlpack v2 bundles into dist/lexicon-packs/
lexicon-build:
    uv run --locked python tools/lexicon_organize.py --out target/lexicon/organized
    cargo run --release -p tamil-toolkit --bin tamil-toolkit -- lexicon compile-all target/lexicon/organized --out dist/lexicon-packs
    uv run --locked python tools/lexicon_quality_gate.py --organized-dir target/lexicon/organized --manifest dist/lexicon-packs/MANIFEST.json

# Validate organized lexicon JSONL packs, cleaning audit accounting, and optional compiled MANIFEST.json.
lexicon-quality-gate:
    uv run --locked python tools/lexicon_quality_gate.py --organized-dir target/lexicon/organized --manifest dist/lexicon-packs/MANIFEST.json

# Inspect discovered local .tlpack v2 bundles, profiles, and categories
lexicon-doctor:
    cargo run -p tamil-toolkit --bin tamil-toolkit -- lexicon doctor

# Launch the interactive Tamil Toolkit Playground locally.
playground-dev:
    pnpm --filter tamil-toolkit-playground dev

# Build the production static assets for the Playground.
playground-build:
    pnpm --filter tamil-toolkit-playground build
