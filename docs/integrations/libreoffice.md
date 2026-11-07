# LibreOffice Tamil Hyphenation Setup Guide

This guide walks through installing and enabling the phonotactically verified Tamil hyphenation dictionary in **LibreOffice Writer** (versions 7.0+ / 24.x+ on Windows, macOS, and Linux).

---

## 1. Prerequisites & Download

- **Extension File**: `tamil-hyphenation.oxt` (available from releases or directly generated via `tamil-toolkit hyphen package-oxt`).
- **Compatibility**: LibreOffice Writer, OpenOffice 4.x.
- **Locales Covered**:
  - `ta-IN` (Tamil - India)
  - `ta-LK` (Tamil - Sri Lanka)
  - `ta-SG` (Tamil - Singapore)
  - `ta-MY` (Tamil - Malaysia)
  - `ta` (Generic Tamil)

---

## 2. One-Click Installation

1. Open **LibreOffice Writer**.
2. Navigate to the top menu: **Tools** > **Extension Manager...** (or press `Ctrl+Alt+E`).
3. Click the **Add...** button.
4. Browse and select `tamil-hyphenation.oxt` (located in your downloads or project `dist/` directory).
5. If prompted with the license dialogue, review the MIT/LGPL/GPL terms and click **Accept**.
6. The extension **"Tamil Syllabic Hyphenation Dictionary"** will now appear in your Extension Manager with an enabled status.
7. Click **Close** and restart LibreOffice when prompted.

---

## 3. Enabling Hyphenation in Your Document

To enable automatic Tamil hyphenation for justified or publication-quality paragraphs:

1. Select your Tamil text or press `Ctrl+A` to select the entire document.
2. In the bottom status bar, ensure the language is set to **Tamil** (e.g. `Tamil (India)` or `Tamil (Sri Lanka)`).
3. Right-click the selected text and choose **Paragraph...** > **Paragraph...** (or press `Alt+Enter`).
4. Switch to the **Text Flow** tab.
5. Under the **Hyphenation** group:
   - Check **Automatically**.
   - Set **Characters at line begin**: `2` (enforces `LEFTHYPHENMIN 2`).
   - Set **Characters at line end**: `2` (enforces `RIGHTHYPHENMIN 2`).
   - (Optional) Set **Maximum number of consecutive hyphens**: `2` or `3` to avoid hyphen ladders.
6. Click **OK**.

---

## 4. Verification & Quality Guarantees

- **No Orphaned Consonants**: Pure consonants (`க்`, `த்`, `ப்`, etc.) will always remain attached to their syllable coda and will never appear isolated at the start of a new line.
- **Grantha Ligature Integrity**: Conjuncts such as `க்ஷ` (`க்ஷ`) and `ஸ்ரீ` (`ஸ்ரீ`) will never be split across line breaks (`க்-ஷ`).
- **Zero Broken Diacritics**: Combining vowel signs (`ா`, `ி`, `ீ`, `ு`, `ூ`, etc.) will never be detached from their base consonant.
