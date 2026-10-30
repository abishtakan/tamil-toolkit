---
description: Rebuild real bindings and run every active golden vector across runtimes.
---

Run `just test-parity`; do not skip missing runtimes or use stale builds.
Read tests/golden/manifest.json and report active counts separately from planned
suites. Run `just test-dart` if Dart is in scope. Report actual command results.
