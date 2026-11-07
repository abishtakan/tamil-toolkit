# Google Docs Workspace Add-on Guide

The **Tamil Hyphenator Google Docs Add-on** adds phonotactically verified syllabic soft-hyphenation to Google Docs directly via Google Apps Script.

---

## 1. Features

- **தமிழ் (Tamil Toolkit) Menu**: Directly integrated into the Google Docs top menu bar.
- **Interactive Sidebar**: Adjust minimum syllable margins (`left_min`, `right_min`) and monitor progress.
- **One-Click Actions**:
  - `தேர்ந்தெடுத்ததை இணைக்கவும் (Hyphenate Selection)`
  - `முழு ஆவணத்தையும் இணைக்கவும் (Hyphenate Document)`
- **Minimal OAuth Scope**: Operates strictly within:
  - `https://www.googleapis.com/auth/documents.currentonly` (accesses only the active opened document, never your Google Drive or other files).
  - `https://www.googleapis.com/auth/script.container.ui` (allows displaying the sidebar and custom menus inside the document UI).
- **100% Private**: No document text leaves Google's infrastructure.

---

## 2. Installation & Sideloading via Apps Script

1. Open your document in **Google Docs**.
2. Click **Extensions** $\rightarrow$ **Apps Script**.
3. In the Apps Script editor:
   - Copy the contents of [`integrations/google-docs-addon/Code.gs`](../../integrations/google-docs-addon/Code.gs) into `Code.gs`.
   - Click the **+** button next to Files $\rightarrow$ select **HTML** $\rightarrow$ name it `Sidebar`.
   - Copy the contents of [`integrations/google-docs-addon/Sidebar.html`](../../integrations/google-docs-addon/Sidebar.html) into `Sidebar.html`.
   - Go to **Project Settings** (gear icon) $\rightarrow$ check **Show "appsscript.json" manifest file in editor**.
   - Copy the contents of [`integrations/google-docs-addon/appsscript.json`](../../integrations/google-docs-addon/appsscript.json) into `appsscript.json`.
4. Click **Save** (disk icon).
5. Switch back to your Google Docs tab and refresh the page.
6. The **தமிழ் (Tamil Toolkit)** menu will now appear in the menu bar. Click **மென்-இணைப்புப் பலகம் (Open Hyphenator Sidebar)**.
