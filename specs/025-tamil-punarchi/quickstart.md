# Validation Quickstart — Tamil Sandhi (`tamil-punarchi`)

Use these checks at each implementation milestone to verify the 117-sūtra inventory (`93–94`, `102–108`, `136`, `151–257`), chapter rule sets, multi-step compositional joining, reverse split candidates, and multi-runtime parity.

## Prerequisites

Use the repository's locked Rust toolchain (`1.95` / MSRV `1.85`), `uv`, `just`, Node/pnpm, `wasm-pack`, and the Dart SDK. Run commands from the repository root unless noted.

## 1. Verify Pinned Reference & 117-Sūtra Inventory (Milestone 10A)

After pinning `tests/reference/punarchi-nannool/sources.json` and populating `lexicon/punarchi-nannool-inventory.toml` and `lexicon/punarchi-nannool.toml`:

```powershell
just check-unicode
uv run --locked python tools/generate_punarchi_golden.py --check
cargo test --locked -p tamil-punarchi --test inventory_completeness
```

Expect `inventory_completeness` to confirm all **117 sūtras (`93–94, 102–108, 136, 151..=257`)** are accounted for across `ezhuttiyal` (9), `padaviyal` (1), `uyireeru` (53), `meyyeeru` (36), and `urupu` (18) with valid TVA *Viruttiyurai* & *Kāṇṭikaiyurai* locators, Project Madurai cross-checks, forward rule-to-inventory integrity (with full reverse zero-unmapped-executable assertion enforced once Tiers A–D complete in US3).

## 2. Verify Standalone Rust Engine & 10,000-Case Properties (Milestones 10B–10D)

With `tests/golden/punarchi_nannool.jsonl` still `planned` in `tests/golden/manifest.json`:

```powershell
just check-unicode
uv run --locked python tools/generate_punarchi_golden.py --check
cargo test --locked -p tamil-punarchi
```

Expect:
- All chapter & feature golden suites (`prereq_golden`, `uyireeru_golden`, `meyyeeru_golden`, `urupu_golden`, `context_ambiguity_golden`, `split_golden`) pass exact surface form, derivation trace, alternative ordering, poetic gating, and error expectations, and `inventory_completeness` confirms zero unmapped executable sūtras across all 117 sūtras.
- `roundtrip_properties` passes 10,000 generated cases per core property: reversible join↔split recall, exact `split_byte`/`split_unit` written-unit alignment (no mid-`க்ஷ`/`ஸ்ரீ` cuts), canonical NFC/NFD equivalence, and verbatim preservation of non-Tamil/joiner boundaries.

## 3. Preactivation Multi-Runtime Parity (Isolated Candidate)

In an isolated preactivation integration worktree with provisional `tamil-toolkit` + Python/WASM/Dart wiring (before fixture activation or release-policy edits):

```powershell
$env:TAMIL_LEXICON_PROFILE = 'core'
$env:TAMIL_GOLDEN_INCLUDE_PLANNED = 'punarchi_nannool.jsonl'

cargo test --locked -p tamil-toolkit --features lexicon-core --test golden_suite -- --nocapture
uv run --locked maturin develop --locked --manifest-path bindings/python/Cargo.toml --features extension-module,lexicon-core
uv run --locked python -m pytest bindings/python/tests/test_golden.py -q
pnpm --filter tamil-toolkit exec wasm-pack build . --dev --target nodejs --out-dir pkg-node --out-name tamil_toolkit --locked --features lexicon-core
pnpm --filter tamil-toolkit exec wasm-pack build . --dev --target web --out-dir pkg-web --out-name tamil_toolkit --locked --features lexicon-core
pnpm --filter tamil-toolkit build
pnpm --filter tamil-toolkit test
cargo build --locked -p tamil-dart --features lexicon-core --target-dir target
Push-Location bindings/dart-flutter
try {
    dart pub get --enforce-lockfile
    dart analyze
    dart test
} finally {
    Pop-Location
}
```

Also run a direct Python wrapper smoke check exercising multi-step joining (`மரம் + ஐ → மரத்தை`), ambiguity reporting, poetic opt-in, reverse split candidates (`கல்லடி`), and unsupported profile errors.

## 4. Reviewed Activation & Final Canonical Gates

After explicit owner approval of (1) activating `punarchi_nannool.jsonl` in `tests/golden/manifest.json` and (2) adding `tamil-punarchi` to `release-policy.toml` and `.github/workflows/publish-crate.yml`:

```powershell
just sync-release-files
just agent-pre-stop-gate
just test-dart
uv run --locked python tools/release.py all --lexicon-profile default
uv run --locked python -m tools.lexicon_dart_archive --profile default
```

Expect clean synchronized release files, 100% active multi-runtime parity across Rust, Python, Node/Browser WASM, and Dart, and verified isolated `default`-profile archives. Publishing remains a separate manual release action under `docs/releases/policy.md`.
