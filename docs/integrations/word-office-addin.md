# Microsoft Word Office.js Web Add-in Guide (AppSource-Ready)

The **Tamil Toolkit Word Utility Suite (`v2.0.0.0`)** integrates directly into **Microsoft Word** (Word 2019+, Microsoft 365 on Windows, macOS, and Word on the Web) using **native Top-Bar Ribbon buttons** and a **6-tab Utility Taskpane**, powered 100% client-side by the slim MIT Rust/WASM `tamil-toolkit` engine.

---

## 1. Features Included (Spec 014)

- **Top-Bar `தமிழ்` Ribbon Tab (1-Click Execution):**
  - **Utilities Group:** Open Tamil Toolkit Taskpane, Auto-Convert Legacy Font → Unicode, Normalize NFC & Repair Tamil.
  - **Sort & Date Group:** Sort Selection (*Akara Varisai*), Insert Today's Tamil Date Header.
  - **Hyphenation Group:** Hyphenate Selection, Hyphenate Document, Wrap Without Hyphen (`\u200B`), Remove All Hyphens.
- **6-Tab Utility Taskpane (`index.html`):**
  1. **Convert & Repair:** Auto-detect & bidirectional conversion (Bamini, TSCII, TAB, TAM, Anjal, Vanavil Avvaiyar, LT-TM) with automatic Unicode font assignment (`Nirmala UI` / `Noto Sans Tamil` / `Latha`), orthographic repair (`repair_tamil_text`), and Tamil-aware Find & Replace (NFC/NFD, zero-width, and optional *Mayangoli* fuzzy matching).
  2. **Sort:** Authentic *Akara Varisai* (`agara-v1`) and school dictionary (`uyirmei-first-v1`) sorting for paragraphs, numbered/bulleted lists, and multi-column Word tables (with header-row preservation).
  3. **Numerals & Symbols:** Cardinal, decimal, ordinal, and legal currency words (`INR`/`LKR`, `TN`/`SL`), Arabic↔Tamil digit toggling, traditional additive numerals (`௰`, `௱`, `௲`), and a 1-click traditional fraction & heritage symbol palette.
  4. **Calendar:** Tamil solar date & Thiruvalluvar year stamps with *Thirukanitham* (Drik) or *Vakya* (1962) profiles, optional *Panchangam* limbs, and TN/SL official holiday indicators.
  5. **Hyphenation:** Canonical Rust `tamil-hyphen` 5-step *Asai* hyphenation with configurable `left_min` / `right_min` margins, OOXML inline formatting preservation (`<w:b/>`, `<w:i/>`, `<w:rPr>`), and batch processing for large documents.
  6. **Inspector:** True Tamil grapheme counts, syllable counts, Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, NFC verification, and invisible scalar diagnostics.

---

## 2. Building & Deploying for Microsoft AppSource / M365 Admin Center

Because the add-in compiles to a static, 100% client-side bundle (`dist/`), it can be hosted on any HTTPS static host (Vercel, Cloudflare Pages, Azure Static Web Apps, or GitHub Pages) and distributed globally—not just on one PC.

### Step 1: Build with Your Production HTTPS Domain
```bash
# Set ADDIN_BASE_URL to your deployed HTTPS origin (no trailing slash)
ADDIN_BASE_URL=https://tamil-toolkit-word.vercel.app pnpm --filter tamil-word-addin build
```
On Windows PowerShell:
```powershell
$env:ADDIN_BASE_URL = "https://tamil-toolkit-word.vercel.app"
pnpm --filter tamil-word-addin build
```

This produces `integrations/office-word-addin/dist/` containing:
- `index.html`, `commands.html`, `privacy.html`, `support.html`
- `assets/*.js`, `assets/*.css`, `assets/*.wasm` (slim MIT ~1.37 MB gzipped), `assets/*.png`
- `vercel.json` and `_headers` (with `application/wasm` MIME type and CORS headers)
- `manifest.prod.xml` (zero `localhost` URLs, HTTPS-only, `WordApi 1.3`, `ReadWriteDocument`, validated `ShortStrings <= 32` & `LongStrings <= 250`)

### Step 2: Deploy `dist/` to HTTPS Hosting
- **Vercel:** Deploy `integrations/office-word-addin/dist` (`vercel --prod` from `dist/` or configure root directory in Vercel).
- **Cloudflare Pages:** Deploy `integrations/office-word-addin/dist` via `cf` CLI / Cloudflare Pages (`_headers` is automatically honored).
- Verify these URLs return HTTP 200 over HTTPS:
  - `<ADDIN_BASE_URL>/index.html`
  - `<ADDIN_BASE_URL>/commands.html`
  - `<ADDIN_BASE_URL>/privacy.html`
  - `<ADDIN_BASE_URL>/support.html`
  - `<ADDIN_BASE_URL>/assets/icon-32.png` & `<ADDIN_BASE_URL>/assets/icon-80.png`

### Step 3: Validate the Production Manifest
```bash
npx office-addin-manifest validate integrations/office-word-addin/dist/manifest.prod.xml
```

### Step 4: Publish to Microsoft AppSource (or M365 Organization Store)
- **Public Microsoft AppSource (Partner Center):**
  1. Sign in to [Microsoft Partner Center](https://partner.microsoft.com/) → **Marketplace offers** → **Office Add-in**.
  2. Upload `integrations/office-word-addin/manifest.prod.xml`.
  3. Provide the hosted Privacy Policy URL (`<ADDIN_BASE_URL>/privacy.html`) and Support URL (`<ADDIN_BASE_URL>/support.html`).
  4. In the AppSource certification notes, confirm:
     - **100% client-side execution** via WebAssembly (no sign-in required, no document data transmitted).
     - Test steps across Word Desktop (Windows/macOS) and Word on the Web using the `தமிழ்` Ribbon tab and Taskpane.
- **Organization-wide Rollout (Microsoft 365 Admin Center):**
  1. Open **Microsoft 365 Admin Center** → **Settings** → **Integrated apps** → **Upload custom apps**.
  2. Upload `manifest.prod.xml` and assign to users/groups.

---

## 3. Local Development & Testing on Your PC

```powershell
# 1. Build slim WASM + production bundle + local manifest.xml
pnpm --filter tamil-word-addin build

# 2. Run automated tests (real slim Rust/WASM + OOXML + AppSource manifest checks)
pnpm --filter tamil-word-addin test

# 3. Serve locally over HTTPS (https://localhost:3000)
pnpm --filter tamil-word-addin serve:local
```

To sideload locally in Desktop Word (Windows), add `\\localhost\office-word-addin` under **File → Options → Trust Center → Trusted Add-in Catalogs**, clear `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` when updating ribbon buttons, and insert **Tamil Toolkit — Word Utility** from **Insert → My Add-ins → Shared Folder**.
