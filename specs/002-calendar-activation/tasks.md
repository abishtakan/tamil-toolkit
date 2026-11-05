# Tasks: Calendar Golden Suite Activation (Phase 1)

**Branch**: `002-calendar-activation` | **Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)

## Phase 1: Golden Vector & Manifest Updates (Priority: P1) 🎯 MVP

- [x] T001 Update `tests/golden/manifest.json` transitioning `calendar_official_holidays.jsonl`, `calendar_tamil_display.jsonl`, and `calendar_thiruvalluvar_year.jsonl` from `"planned"` to `"active"`.
- [x] T002 Update tags in `tests/golden/calendar_official_holidays.jsonl` removing `"planned"`.
- [x] T003 Update tags in `tests/golden/calendar_tamil_display.jsonl` removing `"planned"`.
- [x] T004 Update tags in `tests/golden/calendar_thiruvalluvar_year.jsonl` removing `"planned"`.

## Phase 2: Multi-Runtime Parity Verification

- [x] T005 Run Unicode and schema gate `just check-unicode` verifying all 35,890 active vectors pass schema and NFC checks.
- [x] T006 Run Rust golden suite test with `cargo test -p tamil-toolkit --test golden_suite` (35,890 passed).
- [x] T007 Run Python golden suite test with `pytest bindings/python/tests/test_golden.py` (26 passed).
- [x] T008 Run WASM golden suite test with `pnpm --filter tamil-toolkit test` (35,913 passed).
- [x] T009 Run playground test suite `pnpm --filter tamil-toolkit-playground test` (30 passed).

## Phase 3: Status & Documentation Polish

- [x] T010 Update `docs/status.md` recording the activation of the 4 civil and tabular calendar suites.
- [x] T011 Run repository pre-stop gate `just agent-post-edit`.
