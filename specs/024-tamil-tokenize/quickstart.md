# Validation Quickstart — Tamil Word and Sentence Tokenization

Use these checks as each implementation stage lands. This feature currently has a specification and design. The tokenizer crate, operations, and planned fixture suite are deliverables of the implementation phase. [Plan and delivery order](plan.md)

## Prerequisites

Use the repository’s locked Rust toolchain and development setup. Have Cargo, `uv`, `just`, Node and pnpm, the WASM build tools, and the Dart SDK available. Run commands at the repository root unless indicated. The preactivation examples use PowerShell and the repo’s `core` lexicon profile to accommodate already active dictionary fixtures. The tokenizer itself needs no dictionary pack. [Development setup](../../docs/development.md)

## Verify the evidence and standalone engine

With the sourced suite registered as `planned`, run the existing schema and Unicode gate. Once the private crate exists, run its locked tests.

```powershell
just check-unicode
cargo test --locked -p tamil-tokenize
```

Expect the raw Unicode baseline to match the official word and sentence files. Expect every reviewed Tamil fixture to recover its exact source through both ranges. The corpus report should show missed and spurious boundaries for the default and tailored results by case group, with exact expected results for all reviewed cases. Include adjacent abbreviations, independent terminators, inflected words, and joiner-interrupted written units. [Verification design](data-model.md#verification-records)

## Verify all runtimes before activation

Use the isolated integration candidate with the facade and adapter changes. Select the planned suite explicitly. Build with the existing lower-level commands because the public release-policy check excludes the provisional facade dependency from the canonical gate. Use checkout-local build outputs throughout. Record this run as planned-suite evidence.

```powershell
$env:TAMIL_LEXICON_PROFILE = 'core'
$env:TAMIL_GOLDEN_INCLUDE_PLANNED = 'tokenize_v01.jsonl'

just sync-release-files
cargo test --locked -p tamil-toolkit --features lexicon-core --test golden_suite -- --nocapture
uv run --locked maturin develop --locked --manifest-path bindings/python/Cargo.toml --features extension-module,lexicon-core
uv run --locked python tools/mcp-tamil-oracle/check_source_unicode.py
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

Require the expected planned results and errors across native Rust, Python, Node and browser-target WASM, and Dart. Start a fresh shell for the final gate to clear the candidate-only selection.

## Exercise the public wrappers

After rebuilding the candidate Python binding, run these checks against the same shared operations. The encoded source contains a decomposed vowel sign. The second example tests the honorific once its attested context is admitted. [Input, output, and error contract](contracts/tokenizer.md)

```powershell
@'
from tamil_toolkit import segment_sentences, tokenize_words

text = "x \u0b95\u0bc6\u0bbe. \U0001f600"
word = tokenize_words(text)[1]
assert (word["start_byte"], word["end_byte"]) == (2, 11)
assert (word["start_unit"], word["end_unit"]) == (2, 3)
assert word["text"] == text.encode("utf-8")[2:11].decode("utf-8")

sentence = ("\u0ba4\u0bbf\u0bb0\u0bc1. "
            "\u0b95\u0bc1\u0bae\u0bbe\u0bb0\u0bcd "
            "\u0bb5\u0ba8\u0bcd\u0ba4\u0bbe\u0bb0\u0bcd.")
assert [item["text"] for item in segment_sentences(sentence)] == [sentence]

try:
    tokenize_words(text, stopword_profile="unknown")
except ValueError as error:
    assert str(error) == "unsupported stopword profile"
else:
    raise AssertionError("unknown profile was accepted")
'@ | uv run --locked python -
```

The shared fixtures cover all three filtering profiles. They check that every retained token keeps its original offsets and that the broader profile removes at least one reviewed term beyond the conservative profile.

Run the binding smoke tests added by T026 and T027. Each test calls both convenience methods on `x \u0b95\u0bc6\u0bbe. \U0001f600`. The Tamil word must retain its original text and ranges `[2, 11)` bytes and `[2, 3)` units. Check that a returned sentence also selects its exact source text. Call the word method again with `unknown` and verify `unsupported stopword profile` through the native error transport.

- **Node and browser-target WASM** — Use the separate Node and web exports in `bindings/js-wasm/tests/golden.test.ts`, initializing web WASM from the actual module bytes as the runner already does. Exercise the runtime error through `Reflect.apply` if the TypeScript profile type admits only valid literals. Run `pnpm --filter tamil-toolkit exec vitest run tests/golden.test.ts` from the root.
- **Dart** — Call `TamilToolkit.tokenizeWords` and `TamilToolkit.segmentSentences` with the host C ABI loaded in `bindings/dart-flutter/test/golden_test.dart`. Check the invalid string through `ArgumentError.message`. Run `dart test test/golden_test.dart` from `bindings/dart-flutter`.

## Verify the reviewed integration candidate

After fixture activation and release scope are reviewed and included in the candidate, run the canonical gates sequentially.

```powershell
just sync-release-files
just agent-pre-stop-gate
just test-dart
just release-check
```

Expect clean generated copies, active real-runtime parity, and isolated archive consumers that resolve the new dependency closure. Record exact fixture counts, package sizes, and runtime results in the handoff. `just release-check` performs local archive verification. [Publishing policy](../../docs/releases/policy.md)
