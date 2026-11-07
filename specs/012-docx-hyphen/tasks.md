# Tasks: Headless OpenXML DOCX Batch Processor (`docx-hyphen`)

**Feature**: `012-docx-hyphen` | **Date**: 2026-11-07 | **Spec**: [specs/012-docx-hyphen/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/012-docx-hyphen/spec.md) | **Plan**: [specs/012-docx-hyphen/plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/012-docx-hyphen/plan.md)

## Summary of Phases

1. **Phase 1: Setup**: Dependencies and test directories.
2. **Phase 2: Foundational**: Core types (`DocxStats`, `DocxError`) and data structures.
3. **Phase 3: User Story 1 (P1) 🎯 MVP**: Core OpenXML `<w:t>` streaming processor, file & buffer APIs, and CLI `process-docx`.
4. **Phase 4: User Story 2 (P2)**: Multi-part processing (headers, footers, footnotes, endnotes) and error handling.
5. **Phase 5: User Story 3 (P3)**: Python SDK binding (`tamil_toolkit.hyphen.process_docx`).
6. **Phase 6: User Story 4 (P4)**: Integration documentation, quickstart validation, and quality gates.

---

## Phase 1: Setup

- [X] T001 Standardize dependencies in `crates/tamil-hyphen/Cargo.toml` (zero new external crates; leverage existing `zip = "2.2"`)
- [X] T002 [P] Create test fixture generator and test harness in `crates/tamil-hyphen/tests/docx_tests.rs`

---

## Phase 2: Foundational

- [X] T003 Define `DocxStats` and `DocxError` types in `crates/tamil-hyphen/src/types.rs`

---

## Phase 3: User Story 1 - Core OpenXML Processor & CLI (Priority: P1) 🎯 MVP

- [X] T004 [US1] Implement XML streaming text replacer for `<w:t>` elements preserving all XML attributes and surrounding formatting tags in `crates/tamil-hyphen/src/docx.rs`
- [X] T005 [US1] Implement `process_docx_bytes` and `process_docx_file` in `crates/tamil-hyphen/src/docx.rs` and expose in `crates/tamil-hyphen/src/lib.rs`
- [X] T006 [US1] Implement CLI command `tamil-toolkit hyphen process-docx` with `--input`, `--output`, `--inplace`, `--left-min`, `--right-min`, and `--verbose` in `crates/tamil-toolkit/src/bin/tamil-toolkit.rs`
- [X] T007 [US1] Write integration tests in `crates/tamil-hyphen/tests/docx_tests.rs` verifying run formatting preservation, non-Tamil pass-through, and soft-hyphen idempotency

---

## Phase 4: User Story 2 - Multi-Part Processing (Priority: P2)

- [X] T008 [US2] Extend `process_docx_bytes` to traverse and hyphenate `word/header*.xml`, `word/footer*.xml`, `word/footnotes.xml`, and `word/endnotes.xml`
- [X] T009 [US2] Add unit tests verifying headers, footers, footnotes, and tables in `crates/tamil-hyphen/tests/docx_tests.rs`

---

## Phase 5: User Story 3 - Python SDK Binding (Priority: P3)

- [X] T010 [US3] Add PyO3 binding `process_docx` in `crates/tamil-toolkit/src/lib.rs` and expose convenience API in `bindings/python/python/tamil_toolkit/__init__.py` and type stubs in `__init__.pyi`
- [X] T011 [US3] Add Python integration test in `bindings/python/tests/test_golden.py`

---

## Phase 6: User Story 4 - Integration Guide & Quality Gates (Priority: P4)

- [X] T012 [P] [US4] Write integration guide in `docs/integrations/word-docx-batch.md` explaining Word justification, soft hyphens (`Ctrl + -`), and batch conversion
- [X] T013 Update `README.md` and `ROADMAP.md` marking Phase 2 (DOCX Batch Processor) completed
- [X] T014 Run full quality gates: `cargo test -p tamil-hyphen`, `cargo test -p tamil-toolkit`, and `python tools/release_policy.py check`
