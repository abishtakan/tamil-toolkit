# Adobe InDesign Tamil Hyphenation Setup Guide

Adobe InDesign uses the **AdobeHunspellPlugin** (`libhyphen` Frank Liang algorithm) for international hyphenation. Unlike standard user-data plugins, custom Hunspell hyphenation dictionaries in Adobe InDesign on Windows must be installed directly into the InDesign linguistics plugin directory and registered in its internal `Info.plist` registry file.

This guide provides the exact Windows and macOS folder hierarchies and step-by-step instructions for **Adobe InDesign CC (2020 through 2025+)**.

---

## 1. Prerequisites

- **Dictionary File**: `hyph_ta_IN.dic` (generated in `dist/dictionaries/hyph_ta_IN.dic`).
- **Target Application**: Adobe InDesign CC 2020, 2021, 2022, 2023, 2024, or 2025 (64-bit).
- **Permissions**: Administrator privileges on Windows (required to write to `C:\Program Files\`).

---

## 2. Windows Folder Hierarchy & Installation

### Step A: Locate the InDesign Hunspell Plugin Directory

In modern 64-bit Windows installations of Adobe InDesign CC, the dictionary files are stored under:

```text
C:\Program Files\Adobe\Adobe InDesign <Year>\Resources\Dictionaries\LILO\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\
```

For example, on InDesign 2024:
`C:\Program Files\Adobe\Adobe InDesign 2024\Resources\Dictionaries\LILO\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\`

> **Note on Older Releases**: In legacy CS5/CS6 or early CC releases, this directory was located under `C:\Program Files\Common Files\Adobe\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\` or `C:\Program Files\Adobe\Adobe InDesign <Version>\Plug-Ins\Dictionaries\...`.

---

### Step B: Create the `ta_IN` Folder and Copy `hyph_ta_IN.dic`

1. Open File Explorer as Administrator and navigate into the `Dictionaries` subfolder:
   ```text
   C:\Program Files\Adobe\Adobe InDesign <Year>\Resources\Dictionaries\LILO\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\Dictionaries\
   ```
2. Create a new subfolder named **`ta_IN`** (ISO 639-1 language and ISO 3166 country code):
   ```text
   ...\AdobeHunspellPlugin\Dictionaries\ta_IN\
   ```
3. Copy `dist/dictionaries/hyph_ta_IN.dic` into this new folder:
   ```text
   ...\AdobeHunspellPlugin\Dictionaries\ta_IN\hyph_ta_IN.dic
   ```

*(Optional: If you also have a Tamil spelling wordlist `.dic` and affix `.aff`, they should be placed in the same folder as `ta_IN.dic` and `ta_IN.aff` respectively).*

---

### Step C: Register `ta_IN` in `Info.plist` (CRITICAL)

InDesign indexes languages through an XML property list file (`Info.plist`) located alongside the `Dictionaries` directory. **If `ta_IN` is not registered in `Info.plist`, InDesign will not surface Hunspell hyphenation for Tamil in Preferences.**

1. Open your text editor (e.g., Notepad, Notepad++, or VS Code) **as Administrator** (right-click > *Run as administrator*).
2. Open the file:
   ```text
   C:\Program Files\Adobe\Adobe InDesign <Year>\Resources\Dictionaries\LILO\Linguistics\Providers\Plugins2\AdobeHunspellPlugin\Info.plist
   ```
3. Search for `<key>HyphenationService</key>`. You will see an `<array>` of language codes:
   ```xml
   <key>HyphenationService</key>
   <array>
       <string>da_DK</string>
       <string>de_AT</string>
       <string>de_CH</string>
       <string>de_DE</string>
       <!-- Add ta_IN here -->
       <string>ta_IN</string>
   </array>
   ```
4. Insert `<string>ta_IN</string>` into the `<array>` block.
5. If you also added spelling files, add `<string>ta_IN</string>` under `<key>SpellingService</key>` and `<key>UserDictionaryService</key>`.
6. Save and close `Info.plist`.

---

## 3. macOS Folder Structure (Reference)

On macOS, the corresponding paths are:

- **Dictionaries Folder**:
  ```text
  /Applications/Adobe InDesign <Year>/Resources/Dictionaries/LILO/Linguistics/Providers/Plugins2/AdobeHunspellPlugin.bundle/Contents/SharedSupport/Dictionaries/ta_IN/hyph_ta_IN.dic
  ```
- **`Info.plist` Location**:
  ```text
  /Applications/Adobe InDesign <Year>/Resources/Dictionaries/LILO/Linguistics/Providers/Plugins2/AdobeHunspellPlugin.bundle/Contents/Info.plist
  ```

---

## 4. Configuring InDesign Preferences

1. Launch (or restart) Adobe InDesign.
2. Open **Edit** > **Preferences** > **Dictionary...** (or press `Ctrl + K` and select the **Dictionary** tab).
3. In the **Language** drop-down menu, select **Tamil** (or **Tamil: India**).
4. Under the **Hyphenation** dropdown, ensure **Hunspell** is selected as the provider.
5. Click **OK**.

---

## 5. Applying Publication-Grade Hyphenation to Text

1. Select your Tamil text frame or paragraph.
2. **Enable Indic OpenType Shaping**:
   - In the **Paragraph** panel flyout menu (or **Control** bar hamburger menu), select:
     **Adobe World-Ready Paragraph Composer** (or *Adobe World-Ready Single-line Composer*).
   - *This is essential for correct Tamil script shaping, virama positioning, and Grantha ligatures.*
3. **Configure Hyphenation Settings**:
   - In the **Paragraph** panel flyout menu, choose **Hyphenation...**.
   - Check **Hyphenate**.
   - Set **Words with at least**: `5` letters.
   - Set **After first**: `2` letters (matches `LEFTHYPHENMIN 2` to prevent 1-letter breaks like `அ-ம்மா`).
   - Set **Before last**: `2` letters (matches `RIGHTHYPHENMIN 2`).
   - Set **Hyphen Limit**: `2` hyphens.
4. Click **OK**.

---

## 6. Troubleshooting Checklist

| Issue | Cause | Solution |
|---|---|---|
| Tamil does not show "Hunspell" under Preferences > Dictionary | Language code not registered in `Info.plist` | Re-open `Info.plist` as Admin and ensure `<string>ta_IN</string>` is added inside `<key>HyphenationService</key><array>...</array>`. |
| Changes to `Info.plist` could not be saved | Missing Administrator privileges | Launch Notepad / text editor by right-clicking and choosing "Run as administrator", then open `Info.plist`. |
| Hyphenation breaks diacritics or creates dotted circles | Standard Composer active instead of World-Ready Composer | Switch paragraph composer to **Adobe World-Ready Paragraph Composer**. |
| Word breaks after first single letter (`அ-`) | InDesign hyphenation settings allow 1-letter break | In Paragraph > Hyphenation, ensure **After first** is set to `2` or higher. |
