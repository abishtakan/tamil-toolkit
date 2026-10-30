@AGENTS.md

Read `docs/specs/bootstrap.md` and `tests/golden/manifest.json` before changing
behavior. Use the project oracle for scalar inspection rather than visual guesses.

When role delegation is requested, isolate specification (`linguist-spec`), Rust
implementation (`rust-core-dev`), and FFI integration (`bindings-sync`) in that
order. Scope each task to its role's allowed write paths. A spec agent can hand
back reviewed data before its feature exists; the integrating parent owns the
final full gate. Do not activate planned suites without reviewing their rules.

Commands: `/new-module`, `/verify-parity`, `/audit-unicode`.
