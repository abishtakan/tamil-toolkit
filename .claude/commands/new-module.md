---
description: Specify and scaffold a Tamil module using golden vectors before algorithms.
---

Read AGENTS.md and docs/specs/bootstrap.md. The requested module is: $ARGUMENTS

1. Check existing modules, the manifest, and declarative rules for reuse.
2. Write a sourced docs/specs specification, TN/SL golden JSONL coverage, and
   declarative data. Inspect Tamil by scalars. Mark unresolved facts planned.
3. Validate with `just check-unicode`. Do not fabricate linguistic expectations.
4. Implement reviewed behavior in Rust, with appropriate property tests.
5. Activate its suite only when every vector is implemented and approved in
   the specification. Expose thin bindings in every supported runtime.
6. Run `just agent-pre-stop-gate` and, when affected, `just test-dart`. Report
   remaining planned behavior explicitly. Delegate roles only when requested.
