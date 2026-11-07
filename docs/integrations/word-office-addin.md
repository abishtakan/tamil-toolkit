# Microsoft Word Office.js Web Add-in Guide

The **Tamil Hyphenation Office.js Add-in** provides a native Taskpane inside Microsoft Word (Word 2019+, Microsoft 365 on Windows, macOS, and Word on the Web) for phonotactically verified syllabic soft-hyphenation.

---

## 1. Why Soft Hyphens in Word?

When Tamil paragraphs in Microsoft Word are **Justified** (`Ctrl + J`), Word expands space between words, causing ugly spacing gaps ("whitespace rivers") because it lacks a built-in Tamil hyphenator.

The add-in inserts Unicode **Soft Hyphens (`\u{00AD}`)**:
- **0px Invisible**: Never visible inside lines; zero distortion of letter spacing or ligatures (புள்ளி, கொம்பு, விசிறி).
- **Dynamic Line Breaking**: Word displays a hyphen glyph at the right margin only when a word collides with the margin under Justification.

---

## 2. Features

- **தேர்ந்தெடுத்ததை இணைக்கவும் (Hyphenate Selection)**: Select any paragraphs or table cells and soft-hyphenate with one click.
- **முழு ஆவணத்தையும் இணைக்கவும் (Hyphenate Entire Document)**: Traverses all body paragraphs in Word atomically using `Word.run`.
- **Configurable Margins**: Customize minimum left (`left_min: 2`) and right (`right_min: 2`) syllable counts.
- **100% Offline & Private**: Executes entirely inside the Word client sandbox; zero text exfiltration.

---

## 3. Sideloading & Testing the Add-in

### A. Windows (Desktop Word)
1. Share the `integrations/office-word-addin` folder as a Windows network share:
   - Right-click `integrations/office-word-addin` $\rightarrow$ **Properties** $\rightarrow$ **Sharing** $\rightarrow$ **Share**.
   - Copy the network path (e.g. `\\localhost\office-word-addin`).
2. In Microsoft Word:
   - Go to **File** $\rightarrow$ **Options** $\rightarrow$ **Trust Center** $\rightarrow$ **Trust Center Settings** $\rightarrow$ **Trusted Add-in Catalogs**.
   - Paste the path, click **Add catalog**, check **Show in Menu**, and click **OK**.
   - Restart Word.
3. Open a document, go to **Insert** $\rightarrow$ **My Add-ins** $\rightarrow$ **Shared Folder** $\rightarrow$ Select **Tamil Hyphenation**.
4. The **தமிழ்** tab will appear in the Word ribbon. Click **Tamil Hyphenator** to open the taskpane.

### B. Word on the Web (Office Online)
1. Open any document in [Word Online](https://office.live.com/start/Word.aspx).
2. Go to **Insert** $\rightarrow$ **Add-ins** $\rightarrow$ **Upload My Add-in**.
3. Browse and select `integrations/office-word-addin/manifest.xml`.
4. The taskpane opens on the right side of the editor.
