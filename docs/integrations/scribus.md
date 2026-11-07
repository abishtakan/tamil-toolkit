# Scribus Open-Source Desktop Publishing Setup Guide

Scribus is an open-source desktop publishing suite for layout and typesetting on Linux, Windows, and macOS. It natively utilizes TeX/Hunspell `.dic` hyphenation files.

---

## 1. Prerequisites

- **Dictionary File**: `hyph_ta_IN.dic` (generated in `dist/dictionaries/hyph_ta_IN.dic`).
- **Target Application**: Scribus 1.5.8+ / 1.6.x+.

---

## 2. Installing `hyph_ta_IN.dic`

### Linux (System-wide or User Directory)
- **User directory**:
  ```bash
  mkdir -p ~/.scribus/dicts/
  cp dist/dictionaries/hyph_ta_IN.dic ~/.scribus/dicts/
  ```
- **System-wide**:
  ```bash
  sudo cp dist/dictionaries/hyph_ta_IN.dic /usr/share/scribus/dicts/
  ```

### Windows
- Copy `dist/dictionaries/hyph_ta_IN.dic` to:
  `%APPDATA%\Scribus\dicts\`
  or into the Scribus installation directory:
  `C:\Program Files\Scribus 1.6.x\share\scribus\dicts\`

### macOS
- Copy `dist/dictionaries/hyph_ta_IN.dic` to:
  `~/Library/Application Support/Scribus/dicts/`

---

## 3. Configuring Hyphenation in Scribus

1. Open Scribus.
2. Go to **File** > **Preferences...** > **Hyphenator**.
3. Under the language list, verify that **Tamil (India)** or `ta_IN` appears as an installed hyphenation dictionary.
4. Set the hyphenation options:
   - **Hyphenation Language**: `Tamil (India)`.
   - **Consecutive Hyphenations Allowed**: `2`.
5. In your active document, select the text frame, then choose **Item** > **Hyphenate Text** (or press `Ctrl+Shift+H`).
