# Microsoft Word Office.js Web Add-in Guide

The **Tamil Hyphenation Office.js Add-in** integrates seamlessly into Microsoft Word (Word 2019+, Microsoft 365 on Windows, macOS, and Word on the Web) using **native Word Ribbon buttons in the Top Bar**—with **no sidebar or taskpane clutter required**.

---

## 1. Native Ribbon Architecture (Top Bar Direct Execution)

The add-in uses Office.js `ExecuteFunction` ribbon commands. Clicking any button in the ribbon executes the logic directly in the document:

- **தமிழ் (Tamil Tab in Top Bar)**:
  - **தேர்ந்தெடுத்ததை இணை (Hyphenate Selection)**: Soft-hyphenates highlighted text or the active paragraph directly.
  - **முழு ஆவணம் (Hyphenate Document)**: Soft-hyphenates all body paragraphs in the active document.
  - **இணைப்புகளை நீக்கு (Remove Hyphens)**: Instantly strips all soft-hyphens from the selection or entire document.

---

## 2. Understanding Word's Soft-Hyphens (Optional Hyphens)

### How They Work
The add-in inserts Unicode **Soft Hyphens (`\u{00AD}`)**:
- **0px Invisible**: In normal reading and printing, soft hyphens are completely invisible inside words.
- **Dynamic Line Breaking**: Word only shows a hyphen glyph (`-`) at the right margin when a word falls at the end of a line under Justification (`Ctrl + J`) or left alignment.

### Why Do Hyphens Sometimes Appear Visible on Screen?
In Microsoft Word, optional hyphens are classified as **non-printing formatting marks**:
1. If Word's **"Show/Hide (¶)"** toggle is enabled (shortcut: `Ctrl + Shift + 8` or `Ctrl + *`), Word intentionally displays optional hyphens on screen as small hooked marks (`¬` or `-`) so you know where break opportunities exist.
2. **To hide them**: Press **`Ctrl + Shift + 8`** on your keyboard (or click the `¶` icon on Word's **Home** tab). They will become completely invisible.
3. If they still show up with `¶` off, go to **File** $\rightarrow$ **Options** $\rightarrow$ **Display** and uncheck **"Optional hyphens"** under *"Always show these formatting marks on the screen"*.

---

## 3. Phonotactic Syllable Rules & Parity

The add-in's engine (`engine.js`) adheres 100% to the core `tamil-hyphen` phonotactic algorithm and passes 120/120 golden test vectors:
- **Coda Binding**: Pure consonants with pulli (`்`) and Aytham (`ஃ`) strictly bind to the preceding vowel nucleus. A segment **never** begins with a pure consonant or Aytham.
- **Grantha Preservation**: Atomic Grantha sequences (`க்ஷ`, `ஸ்ரீ`, `ஶ்ரீ`) are never split.
- **Idempotent**: Running hyphenation multiple times is safe and never injects duplicate hyphens.
- **Margin Protection**: Preserves leading and trailing syllable margins (`left_min: 2`, `right_min: 2`).

---

## 4. Sideloading & Updating the Add-in

### Windows (Desktop Word)
1. Share `integrations/office-word-addin` as a Windows network share:
   - Path: `\\localhost\office-word-addin` (or `\\<COMPUTER_NAME>\office-word-addin`).
2. In Microsoft Word:
   - Go to **File** $\rightarrow$ **Options** $\rightarrow$ **Trust Center** $\rightarrow$ **Trust Center Settings** $\rightarrow$ **Trusted Add-in Catalogs**.
   - Add the catalog network share URL and check **Show in Menu**.
3. **To refresh/reload updated buttons**:
   - Close Microsoft Word.
   - Delete cache folder: `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\`
   - Re-open Word.
   - Go to **Insert** $\rightarrow$ **My Add-ins** $\rightarrow$ **Shared Folder** $\rightarrow$ select **Tamil Hyphenation**.
   - The **தமிழ்** tab appears in the top bar with the 3 native ribbon buttons.
