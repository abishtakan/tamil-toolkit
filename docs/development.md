# Development workflow

Start with `AGENTS.md`, `docs/status.md`, the relevant module specification,
and `tests/golden/manifest.json`. Check the working tree before editing so
another contributor's changes stay intact. `docs/status.md` is the concise
handoff; module specifications own behavior and the release record owns
publication evidence.

## Feature lifecycle

1. Define the feature's bounded inputs, outputs, errors, regional scope,
   source/licensing evidence, and observable acceptance criteria in a module
   specification. Inspect Tamil scalars through the oracle or escapes.
2. Write sourced golden cases and declarative rules before Rust algorithms.
   Keep unresolved suites planned. Implement behavior in Rust, then expose
   identical calls through Python, WASM, and Dart. Reuse the Rust dispatcher.
3. Run focused regression checks while editing and `just agent-post-edit`
   before integration. Canonical lexicon/license changes need
   `just sync-release-files` before checks; generated copies are never edited
   directly. A changed public operation also needs binding declarations.
4. Run `just agent-pre-stop-gate` at integration completion. When Dart or shared
   behavior is affected, run `just test-dart`. Treat fixture
   activation and a public release allowlist change as separate reviewed steps.
5. Record the outcome under Unreleased in `CHANGELOG.md`, update the module's
   acceptance evidence and `docs/status.md`, and report actual checks and
   remaining limits. Preserve current session authorization for commit/push;
   publishing follows the separate [publishing policy](releases/policy.md).

## Keeping work fast

Ordinary GitHub pushes and pull requests run the small Ubuntu Rust/Unicode,
release-policy, and workflow-lint gate. A newer run cancels an obsolete CI run.
Full harness and Python/WASM/Dart parity checks run locally.
The expensive cross-platform archive matrix is an explicit release dispatch.
A passing small CI run does not replace local parity evidence.

Use locked dependencies and warm caches. Rebuild bindings before parity; a
stale native extension can otherwise hide Rust changes. Specification-only
handoffs can finish with schema/Unicode evidence while implementation is
pending; the integrating agent owns the final full gate. Delegate specialist
roles only when requested. These role files and hooks are tool guardrails,
not filesystem permissions.

Pytest uses numbered directories beneath `target/pytest-temp` through the
documented `PYTEST_DEBUG_TEMPROOT` setting in `conftest.py`. This avoids the
account's inaccessible system temp base and deleting the previous active test
run on Windows. Explicit user `--basetemp` or environment settings are honored.

## Handoff before ending or losing context

Update `docs/status.md` with the objective, branch/commit and uncommitted work,
completed acceptance criteria, exact checks and outcomes, pending issues, and
the next concrete action. Keep evidence paths and registry workflow filenames;
omit secrets and large logs. Durable facts belong in their specifications or
release records; link to them instead of copying them into every handoff.

On resumption, read that status, check `git status`, and continue the unfinished
acceptance criteria. Do not repeat completed checks without changed inputs,
new failures, or unresolved concerns. Do not describe an unpublished module
or a planned suite as completed support.
