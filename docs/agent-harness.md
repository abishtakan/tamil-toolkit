# Agent guardrails

AGENTS.md applies across agents. CLAUDE.md imports it; Cursor has always-on
rules. `.mcp.json` registers the local stdio oracle. Client support for these
files varies; confirm registration in your client. The harness never uploads
text or calls a model to decide Tamil boundaries.

Claude hooks use the [official hooks contract](https://code.claude.com/docs/en/hooks).
The Python adapter reads event JSON, runs tasks from the repository root, and
converts nonzero verification results into exit 2. A plain command exit 1 is
not sufficient to block a Claude Stop event. There is no unconditional
`stop_hook_active` bypass: a failed gate remains failed until the issue is fixed.

PreToolUse checks `agent_type` for the three named specialist roles. It rejects
Write/Edit outside each role's resolved allowed roots and restricts shell tools
to exact verification commands. Read-only tools remain available. Role files
also constrain the available tools. The integrating parent owns the full Stop
gate; specification handoffs can precede implementation without pretending the
feature is complete. PostToolUse checks edits; it cannot undo a completed write.

These are tool-interface guardrails, not OS write permissions. They depend on
the client providing agent_type and invoking hooks, and cannot secure a hostile
process, disabled hooks, changed configuration, or another unrestricted client.
For a hard permission boundary, run roles in separate sandboxes with read-only
fixture/data mounts. Do not describe Markdown path lists as filesystem ACLs.

Post-edit checks are incremental but not guaranteed to finish in two seconds.
The Stop gate rebuilds bindings before parity and may take minutes from a cold
cache. Missing tools or build failures block it rather than silently skipping.

CI independently runs the same gate on Ubuntu and Windows, plus host Dart FFI
verification. PostgreSQL setup remains a separate planned integration because
it needs a PostgreSQL/pgrx toolchain and reviewed morphology/search semantics.
