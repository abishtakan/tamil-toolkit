# Tasks: Microsoft Word Office.js Add-in and Google Docs Add-on (`word-docs-addins`)

**Feature**: `013-word-docs-addins` | **Date**: 2026-11-07 | **Spec**: [specs/013-word-docs-addins/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/013-word-docs-addins/spec.md) | **Plan**: [specs/013-word-docs-addins/plan.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/013-word-docs-addins/plan.md)

---

## Phase 1: Setup & Shared Engine

- [X] T001 Create directories `integrations/office-word-addin` and `integrations/google-docs-addon`
- [X] T002 Implement standalone zero-dependency Tamil soft-hyphenation engine `integrations/office-word-addin/engine.js` with syllable segmentation and `\u{00AD}` injection

---

## Phase 2: User Story 1 - Microsoft Word Office.js Add-in (Priority: P1) 🎯 MVP

- [X] T003 [US1] Create valid Office Add-in manifest `integrations/office-word-addin/manifest.xml`
- [X] T004 [US1] Create taskpane interface `integrations/office-word-addin/index.html` and stylesheet `taskpane.css`
- [X] T005 [US1] Implement Word.run interaction logic in `integrations/office-word-addin/taskpane.js` (Hyphenate Selection, Hyphenate Document, Margin Controls)
- [X] T006 [US1] Write contract test `tests/integrations/test_word_addin_contract.js` verifying Word.run mock execution and idempotency

---

## Phase 3: User Story 2 - Google Docs Workspace Add-on (Priority: P2)

- [X] T007 [US2] Create Google Apps Script manifest `integrations/google-docs-addon/appsscript.json` with `documents.currentonly` scope
- [X] T008 [US2] Implement standalone Apps Script syllabic engine and document traversal in `integrations/google-docs-addon/Code.gs`
- [X] T009 [US2] Create sidebar UI `integrations/google-docs-addon/Sidebar.html` with selection/document action triggers
- [X] T010 [US2] Write contract test `tests/integrations/test_gdocs_addon_contract.js` verifying Apps Script DocumentApp mock execution

---

## Phase 4: User Story 3 - Subagent Verification & Quality Gates (Priority: P3)

- [X] T011 [US3] Invoke research subagent to audit manifests, security boundaries, and zero-exfiltration guarantees
- [X] T012 [US3] Create comprehensive guides `docs/integrations/word-office-addin.md` and `docs/integrations/google-docs-addon.md`
- [X] T013 [US3] Update `ROADMAP.md` marking Phase 3 and Phase 4 as Completed & Live
- [X] T014 [US3] Run release policy and test suites, update `docs/status.md`, and commit changes
