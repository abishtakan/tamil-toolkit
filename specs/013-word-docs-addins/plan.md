# Implementation Plan: Microsoft Word Office.js Add-in and Google Docs Add-on (`word-docs-addins`)

**Feature**: `013-word-docs-addins` | **Date**: 2026-11-07 | **Spec**: [specs/013-word-docs-addins/spec.md](file:///C:/Users/abish/Documents/dev/tamil-toolkit/specs/013-word-docs-addins/spec.md)

---

## 1. Architectural Strategy

Both Microsoft Word and Google Docs provide JavaScript-based extensibility models:
- **Microsoft Word**: Uses the **Office JavaScript API (`Office.js`)** running in a WebView / iframe taskpane. The add-in interacts with the document DOM through `Word.run(async (context) => { ... })`.
- **Google Docs**: Uses **Google Apps Script** running server-side on Google's cloud or client-side HTML service sidebars with `google.script.run`.

To maximize performance, privacy, and offline capability:
1. **Shared Pure JavaScript Linguistic Engine**: A standalone, self-contained Tamil syllabic soft-hyphenator module (`tamil-hyphen-engine.js`) derived directly from our verified phonotactic algorithm, capable of running either standalone in browser/Apps Script environments or with WebAssembly.
2. **Microsoft Word Office.js Bundle** (`integrations/office-word-addin/`):
   - `manifest.xml`: Standard Office Add-in manifest pointing to the taskpane.
   - `taskpane.html`: Responsive taskpane interface styled with modern Fluent / classical Tamil palette.
   - `taskpane.js`: Coordinates Word.run selection and body paragraph operations.
   - `taskpane.css`: Lightweight stylesheet.
3. **Google Docs Add-on Bundle** (`integrations/google-docs-addon/`):
   - `appsscript.json`: Google Apps Script manifest with Google Docs extension points and permissions (`documents.currentonly`).
   - `Code.gs`: Apps Script server-side controller managing menus, selections, and document edits.
   - `Sidebar.html`: Client sidebar with progress indicators and action buttons.
4. **Documentation & Deployment Guides**:
   - `docs/integrations/word-office-addin.md`: Sideloading in Word on Windows, Mac, and Word Online.
   - `docs/integrations/google-docs-addon.md`: Sideloading via script.google.com and deployment.

---

## 2. Directory Layout

```text
integrations/
├── office-word-addin/
│   ├── manifest.xml
│   ├── index.html
│   ├── taskpane.js
│   ├── taskpane.css
│   ├── engine.js
│   └── README.md
└── google-docs-addon/
    ├── appsscript.json
    ├── Code.gs
    ├── Sidebar.html
    ├── engine.gs
    └── README.md

docs/integrations/
├── word-office-addin.md
└── google-docs-addon.md

tests/integrations/
├── test_word_addin_contract.js
└── test_gdocs_addon_contract.js
```

---

## 3. Subagent Verification Strategy

We will invoke a specialized subagent to:
1. Validate `manifest.xml` schema against Microsoft Office Add-in XML standards (Ids, VersionOverrides, Action types).
2. Validate `appsscript.json` OAuth scopes (ensuring minimum privilege: `documents.currentonly`).
3. Verify zero-data exfiltration (no external fetch/XHR calls outside of official Microsoft Office.js CDN).
4. Run integration contract tests on the shared JS engine and node environment.
