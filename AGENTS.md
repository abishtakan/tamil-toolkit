# tamil-toolkit: Agentic Engineering Constitution

## Architectural invariants

1. **Rust owns linguistic behavior.** Algorithms belong in `crates/tamil-*`.
   Python, TypeScript/WASM, and Dart are thin serialization/FFI adapters. The
   oracle uses the same Rust dispatcher; never add a second Tamil engine.
2. **Inspect Tamil by scalars.** Never infer canonical composition, character
   boundaries, or invisible joiners from rendered text. Call the local
   `tamil-oracle` MCP tool `inspect_tamil_string` / `inspect_codepoints`, or use
   explicit hexadecimal escapes. Keep Tamil in golden JSONL and declarative
   data escaped and reviewable. Never silently remove ZWJ/ZWNJ from user input.
3. **Golden vectors precede implementation.** Add sourced cases in
   `tests/golden/<module>.jsonl` and a specification before algorithms. Every
   active case runs unchanged in Rust, Python, and WASM. Unsupported operations
   fail. Planned suites are visibly unimplemented, never counted as passing.
4. **Separate data from the engine.** Word lists, suffixes, font/encoding maps,
   and grammar rules belong in `lexicon/*.toml` or CSV, with sources and licenses.
   Compile them using `build.rs` into static tables or FST/trie bytes as suitable.
   No executable code belongs in `lexicon/`. Never hallucinate Punarchi rules.
5. **Tamil is pluricentric.** Cover TN and SL, including Jaffna, Batticaloa,
   Vanni, and Up-Country when relevant. Specify regional scope and test regional
   invariance where a Unicode operation does not depend on dialect.
6. **Respect platform naming.** Public Rust/Python/npm distributions use
   `tamil-*`; Python imports and Dart/Pub identifiers use `tamil_*` as required.
   PostgreSQL uses `pg_tamil`. Publishing remains disabled until release review.
7. **State actual guarantees.** Borrowed core iteration can avoid allocations;
   normalization and FFI allocate. Role instructions and hooks are guardrails,
   not an operating-system sandbox. Do not claim complete linguistic support
   from a passing bootstrap suite.

## Required verification

- `just check-unicode`: validate source Unicode, decoded JSONL, schema, global
  IDs, manifest coverage, and exact, reasoned Unicode exceptions.
- `just test-rust`: locked workspace tests and 10,000 cases per core property.
  Uses nextest if installed; explicitly falls back to `cargo test` otherwise.
- `just sync-bindings`: rebuild PyO3 and both Node/browser WASM packages, then
  generate TypeScript declarations. Python declarations live beside the wrapper.
- `just test-parity`: rebuild first, then consume every active JSONL row in real
  Rust, Python, and WASM runtimes. Never skip missing bindings or use mocks.
- `just test-dart`: verify the host C ABI, Dart analysis, and the same fixtures.
- `just agent-post-edit`: formatting check, Unicode/schema gate, workspace check.
- `just agent-pre-stop-gate`: the full clippy, Rust, harness, and parity gate.

Use `.claude/agents/linguist-spec.md`, `rust-core-dev.md`, and `bindings-sync.md`
for isolated roles when delegation is requested. Do not weaken another role's
fixtures to make an implementation pass. See `docs/agent-harness.md` for hook
scope and enforcement limitations. See `docs/specs/bootstrap.md` before edits.

## Cloudflare

When interacting with Cloudflare, use the cf CLI unless the project has a
Wrangler configuration file.
