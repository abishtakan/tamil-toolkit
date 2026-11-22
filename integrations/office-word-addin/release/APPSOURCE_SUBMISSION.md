# Microsoft AppSource Submission Kit — Tamil Toolkit for Word (`v2.2.0.0`)

## 1. Live Production Deployment (Verified HTTP 200)
- **Production Origin:** `https://tamil-toolkit-word.vercel.app`
- **Taskpane URL:** `https://tamil-toolkit-word.vercel.app/index.html`
- **Privacy Policy URL:** `https://tamil-toolkit-word.vercel.app/privacy.html`
- **Support URL:** `https://tamil-toolkit-word.vercel.app/support.html`
- **Upload Manifest File:** `integrations/office-word-addin/release/tamil-toolkit-word-manifest.xml` (validated with `office-addin-manifest validate`)
- **App Icon (32×32 / 80×80):** `assets/icon-32.png`, `assets/icon-80.png` (Aytham `ஃ` brand mark)

---

## 2. Ready-to-Paste Store Listing Copy (Partner Center → Offer Listing)

- **Name:** `Tamil Toolkit`
- **Summary (<= 100 chars):** `100% client-side Tamil suite: legacy font conversions, sorting, numerals, calendar & hyphenation.`
- **Description:**
  > **Tamil Toolkit** brings a complete, 100% client-side Tamil linguistic utility suite directly into Microsoft Word (Windows, macOS, and Word on the Web) — powered by a fast, Apache-2.0-licensed Rust/WebAssembly engine with zero cloud data transmission.
  >
  > **Key Capabilities:**
  > - **Live Bamini → Unicode Typing & Legacy Conversion:** Type directly on your Word page using Bamini layout with live Unicode conversion (toggle ON/OFF from the top `தமிழ்` Ribbon), or convert existing Bamini, TSCII, TAB, TAM, Anjal, Vanavil Avvaiyar, and LT-TM (Shree-Lipi) selections/documents while preserving inline bold/italic formatting and English run fonts.
  > - **1-Click Prepare Legacy Document:** Convert legacy encodings, normalize Unicode NFC / repair duplicate pullis and visual left-kombu signs (preserving ZWJ/ZWNJ), and optionally hyphenate in a single batched pass.
  > - **Authentic *Akara Varisai* Sorting:** Sort Tamil paragraphs, numbered/bulleted lists, and multi-column Word tables in authentic Tamil dictionary order (`agara-v1` Mei-first or `uyirmei-first-v1` school order).
  > - **Tamil Numerals, Currency Words & Traditional Symbols:** Convert numbers and amounts (`INR`/`LKR`, `TN`/`SL`) into formal Tamil words, toggle Arabic (`0–9`) ↔ Tamil (`௦–௯`) digits, and insert traditional Tamil fractions (`முந்திரி`, `காணி`, `கால்`, `அரை`, `முக்கால்`) and heritage symbols.
  > - **Tamil Calendar & Panchangam Stamps:** Insert formatted Tamil solar dates, Thiruvalluvar years, 60-year cycle names, and optional Panchangam limbs (*Thirukanitham* or *Vakya* profiles) with TN/SL holiday indicators.
  > - **Canonical Tamil Syllabic Hyphenation:** Insert native Word soft hyphens (`<w:softHyphen/>`) or invisible syllable wrap points (`\u200B`) for balanced justified paragraphs without splitting consonant clusters or Grantha conjuncts.
  > - **Document Inspector & Tamil-Aware Find & Replace:** Inspect true Tamil graphemes, syllables, Uyir/Mei/Uyirmei/Grantha breakdowns, and invisible code points.
  >
  > **Privacy:** All processing runs 100% locally inside your Word session. Zero document text leaves your device.

- **Categories:** `Productivity`, `Writing`
- **Supported Platforms:** Word on Windows (2019+ / M365), Word on Mac (2016+ / M365), Word on the Web, Word on iPad.

---

## 3. Ready-to-Paste Certification Notes for Microsoft Reviewers

> **Authentication:** None required. No sign-in, no account, and no paid subscription. All processing runs 100% client-side via WebAssembly (`tamil_toolkit_bg-*.wasm`). Zero user document data is transmitted over the network.
>
> **How to Test:**
> 1. Open a blank Word document and click the **தமிழ்** tab on the top Ribbon.
> 2. **Convert Legacy Bamini → Unicode:** Type `jkpo;` in the document, select it, and click **Convert to Unicode** on the Ribbon. It converts in-place to `தமிழ்` in `Nirmala UI` while preserving any bold/italic formatting and supporting standard Word Undo (`Ctrl+Z`).
> 3. **Live Bamini Typing (Optional):** Click **Live Bamini ON/OFF** on the Ribbon (or in the **Type** tab of the Taskpane), click on the document page, and type `jkpo;` — it converts live to `தமிழ்`. Click **Live Bamini ON/OFF** again to turn it off.
> 4. **Akara Varisai Sort:** Type three paragraphs (`கடல்`, `அம்மா`, `ஆடு`), select all three, and click **Sort Akara Varisai** → reorders to `அம்மா`, `ஆடு`, `கடல்`.
> 5. **Insert Tamil Date:** Open the **Insert Tamil** Ribbon dropdown → click **Insert Tamil Date** → inserts today's formatted Thiruvalluvar year and Tamil solar date at the cursor.
> 6. **Syllabic Hyphenation:** Type `பல்கலைக்கழகங்களில்`, select it, open **Hyphenation** → **Hyphenate Selection** (inserts native `<w:softHyphen/>`), then click **Remove Hyphenation** to cleanly remove soft hyphens while preserving any manual `-` hyphens.
> 7. **Taskpane:** Click **Tamil Toolkit** on the Ribbon to open the 3-tab Fluent 2 pane (**Type**, **Prepare**, **Insert**), which automatically adapts to Word's Dark/Light theme and includes a **தமிழ் / EN** UI language toggle.

---

## 4. Exact Submission Steps (Microsoft Partner Center)

1. Go to [Microsoft Partner Center — Commercial Marketplace](https://partner.microsoft.com/dashboard/commercial-marketplace/overview) and sign in with your Microsoft Publisher account.
2. Click **+ New offer → Office Add-in**.
3. Under **Product setup → Package**, upload:
   `integrations/office-word-addin/release/tamil-toolkit-word-manifest.xml`
4. Under **Offer listing**, paste the title, summary, description, Privacy URL (`https://tamil-toolkit-word.vercel.app/privacy.html`), Support URL (`https://tamil-toolkit-word.vercel.app/support.html`), and upload screenshots of the `தமிழ்` Ribbon and 3-tab Taskpane (300×300 store logo can be scaled from `assets/icon-80.png` / `playground/public/favicon.svg`).
5. Under **Review and publish → Notes for certification**, paste Section 3 above and click **Publish**.

### Bonus: Try It on Any PC / Mac / Browser Right Now (Before AppSource Approval)
- **Word on the Web:** Open [word.new](https://word.new/) → **Add-ins → More Add-ins → My Add-ins → Upload My Add-in** → upload `integrations/office-word-addin/release/tamil-toolkit-word-manifest.xml`. Works immediately with **zero localhost server**!
- **Microsoft 365 Admin Center (Org Rollout):** Upload `tamil-toolkit-word-manifest.xml` under **Settings → Integrated apps → Upload custom apps**.
