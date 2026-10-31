---
description: Review release scope, version alignment, and real distribution evidence.
---

Read AGENTS.md, docs/status.md, release-policy.toml, and docs/releases/policy.md.
The requested release work is: $ARGUMENTS

1. Inspect git status and `just release-status`. Only approved finished crates
   and the Python/npm umbrellas can ship. Keep deferred packages private.
2. Check version/channel alignment with `just check-release-policy`. Prepare
   release notes and canonical source copies when applicable. Do not bump a
   version merely to inspect readiness or retry an already published version.
3. Complete the applicable local integration gates and `just release-check`.
   Record exact evidence, limits, source SHA, and any remaining account setup.
4. Publication requires the policy's manual workflow and concrete artifact
   review. Respect existing session authorization; do not request it again.
   Use the full reviewed SHA and a successful artifact run. Never expose keys
   in chat or handoff notes. Do not dispatch publication as a readiness check.
5. Update docs/status.md and the release record with the result and next action.
