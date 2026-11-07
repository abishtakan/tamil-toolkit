# Feature Specification: Microsoft Word Office.js Add-in and Google Docs Workspace Add-on for Tamil Soft-Hyphenation (`word-docs-addins`)

**Feature Branch**: `013-word-docs-addins`  
**Created**: 2026-11-07  
**Status**: Partially Complete — Word add-in delivered; Google Docs add-on was evaluated and removed from scope per user direction
**Input**: User request: "do them [Word & Docs] with spec kit lifecycle. also use subagents for confirming it"

---

## 1. Executive Summary & Vision

Microsoft Word and Google Docs are the world's most widely used consumer and enterprise word processors. Neither natively supports Tamil syllabic line breaking nor drop-in TeX/Hunspell `.dic` dictionaries. As a result, when documents are Justified (`Ctrl + J`), Word and Docs expand inter-word spacing into unsightly "whitespace rivers".

This feature delivers **Phase 3 (Microsoft Word Office.js Web Add-in)** and **Phase 4 (Google Workspace Google Docs Add-on)**:
1. **Microsoft Word Web Add-in (`Office.js`)**: A cross-platform Taskpane Add-in running locally on Word 2019+, Microsoft 365 (Windows & macOS), and Word Online, powered by client-side WebAssembly (`tamil-toolkit-wasm`).
2. **Google Docs Workspace Add-on**: A Google Workspace Add-on running inside Google Docs via Google Apps Script and client-side JavaScript, enabling one-click selection and full-document syllabic soft-hyphen injection (`\u{00AD}`).
3. **Core Linguistic Invariant**: Zero-width soft hyphens (`\u{00AD}`) remain 0px invisible on the same line, never altering same-line letter spacing or breaking ligatures (pulli, kombu, visiri), and activating only at right-margin collisions under Justification (`Ctrl + J`).

---

## 2. User Stories

### User Story 1: Microsoft Word Office.js Taskpane Add-in (Priority: P1) 🎯 MVP
**As a** Tamil author, researcher, or publisher using Microsoft Word,  
**I want to** open a dedicated "Tamil Hyphenation" Taskpane within Word and click "Hyphenate Selection" or "Hyphenate Document",  
**So that** my justified Tamil paragraphs break gracefully across lines at phonotactically verified syllable boundaries without large gaps or broken ligatures.

#### Acceptance Criteria
1. The add-in provides a clean, responsive Taskpane UI complying with the project's classical palette (Terracotta `#963824`, Sandalwood, Palm leaf) and Office UI Fabric / Fluent styling.
2. The user can configure minimum left and right margins (default: `left_min: 2`, `right_min: 2`).
3. Calling "Hyphenate Selection" replaces Tamil words in the active selection with soft-hyphenated equivalents via `Word.run(async (context) => { ... })`.
4. Calling "Hyphenate Entire Document" traverses all body paragraphs in `context.document.body.paragraphs`.
5. The add-in executes 100% offline and locally in the browser/taskpane sandbox using client-side WebAssembly; no document text leaves the machine.
6. A valid Office Add-in manifest (`manifest.xml`) is provided with sideloading and deployment instructions for Windows Word, Mac Word, and Word Online.

---

### User Story 2: Google Docs Workspace Add-on (Priority: P2)
**As a** Google Docs user writing or editing Tamil articles and books,  
**I want to** open an Add-on sidebar in Google Docs and apply syllabic hyphenation with one click,  
**So that** justified text renders with balanced lines in Google Docs.

#### Acceptance Criteria
1. A complete Google Apps Script add-on project structure (`appsscript.json`, `Code.gs`, `Sidebar.html`) is provided.
2. The add-on provides menu items: `Tamil Toolkit > Hyphenate Selection` and `Tamil Toolkit > Hyphenate Entire Document`.
3. Injects Unicode soft-hyphens (`\u{00AD}`) into text runs via `DocumentApp.getActiveDocument()`.
4. Handles Google Docs canvas quirks by ensuring soft-hyphen characters are placed safely inside text elements without disrupting inline images, footnotes, or links.
5. Sideloading and deployment guides (`docs/integrations/google-docs-addon.md`) provide step-by-step instructions for testing and publishing to Google Workspace Marketplace.

---

### User Story 3: Verification Harness & Subagent Validation (Priority: P3)
**As a** developer or reviewer,  
**I want to** run automated tests and independent subagent verification on both add-in bundles,  
**So that** compatibility, manifest validity, API ergonomics, and idempotency are rigorously confirmed.

#### Acceptance Criteria
1. Automated unit and contract tests verify the JavaScript/TypeScript core bridge for both Word (`Office.js` mock) and Google Docs (`Apps Script` mock).
2. A research/audit subagent independently inspects the add-in manifests, packaging, and offline privacy guarantees.
3. Test suite verifies soft-hyphen idempotency: hyphenating already hyphenated text does not inject duplicate hyphens.

---

## 3. Functional Requirements

- **FR-001 (Word Manifest)**: Provide an XML manifest `integrations/office-word-addin/manifest.xml` adhering to Office Add-in schema `v1.1` with Taskpane extension point.
- **FR-002 (Word Taskpane Bundle)**: Provide `integrations/office-word-addin/index.html`, `taskpane.js`, and styling incorporating `tamil-toolkit-wasm` or pure JS fallback.
- **FR-003 (Word.run API Integration)**: Correctly load `context.document.getSelection()` and `context.document.body.paragraphs.load("text")`, perform atomic batch updates with `context.sync()`.
- **FR-004 (Google Docs Add-on Files)**: Provide `integrations/google-docs-addon/appsscript.json`, `integrations/google-docs-addon/Code.gs`, and `integrations/google-docs-addon/Sidebar.html`.
- **FR-005 (Google Docs DocumentApp)**: Implement paragraph traversal and text replacement preserving text formatting attributes (font, size, bold, italic).
- **FR-006 (Zero Data Exfiltration)**: Ensure both add-ins execute entirely within the client runtime; zero external network requests during text processing.
- **FR-007 (Documentation)**: Complete user setup guides for Microsoft Word sideloading and Google Docs Apps Script deployment in `docs/integrations/`.

---

## 4. Non-Functional Requirements & Invariants

- **Constitutional Compliance**: Zero broken diacritics, zero breaking of ligatures (`க் + ஷ`), zero alteration of same-line letter spacing.
- **Privacy & Security**: Zero telemetry or remote API calls for document contents.
- **Performance**: Processing a 50-paragraph section must complete in under 500ms on modern consumer hardware.
