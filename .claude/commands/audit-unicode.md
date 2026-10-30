---
description: Inspect Unicode source, golden schema, and exact scalar differences.
---

Run `just check-unicode`. Inspect suspect text with the local oracle's
inspect_tamil_string and diff_tamil_outputs tools. Validate changed JSONL with
validate_golden_schema. Preserve intentional normalization/joiner fixtures using
exact pointer-scoped, reasoned exceptions. Never normalize fixtures wholesale.
