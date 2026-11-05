# Quickstart & Verification Guide: Interactive Playground (`playground`)

**Feature**: `005-playground` | **Date**: 2026-11-05

This guide provides step-by-step instructions for running, testing, and validating the `tamil-toolkit` Playground locally.

---

## 1. Prerequisites

- **Node.js**: `v22.0.0` or higher
- **pnpm**: `v10.0.0` or higher
- **Rust Toolchain**: `1.85+` (for compiling the underlying WebAssembly package via `wasm-pack`)
- Modern web browser (Chrome, Safari, Firefox, or Edge) with WebAssembly and Web Worker support

---

## 2. Setup & Local Development

From the repository root:

```bash
# 1. Ensure the Rust WebAssembly package is freshly compiled
just sync-bindings

# 2. Install workspace dependencies
pnpm install

# 3. Start the playground development server with instant HMR
pnpm --filter playground dev
```

The application will start on `http://localhost:5173`.

---

## 3. End-to-End Verification Scenarios

### Scenario 1: Real-Time Legacy Font Conversion (Zero Clicks)
1. Navigate to `http://localhost:5173`.
2. The **Legacy Font Converter** is selected by default.
3. Paste a Bamini sample into the input box:
   ```text
   jkpo; nkhop cyfpd; njhd;ikahd nkhopfspy; xd;whFk;.
   ```
4. **Verification**:
   - The encoding badge automatically shows `bamini-v1` with > 90% confidence.
   - The output box displays converted Unicode in real time: `தமிழ் மொழி உலகின் தொன்மையான மொழிகளில் ஒன்றாகும்.`
   - No "Submit" or "Convert" button was pressed.
   - Click the prominent **Copy** button; a toast appears confirming "Copied to clipboard".

---

### Scenario 2: Number to Formal Tamil Words
1. Tap the **Numeral Formatter** tab.
2. Enter `125000` in the amount field and toggle **Currency (INR)**.
3. **Verification**:
   - Formal words: `ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய்`
   - Cheque format: `ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய் மட்டும்`
   - Spoken words: `ஒரு லட்சத்து இருபத்தஞ்சாயிரம் ரூபா`
   - Traditional numeral symbols: `௱௨௰௫௲`

---

### Scenario 3: Mobile Viewport & Touch Ergonomics
1. Open Developer Tools in your browser (F12) and toggle device emulation (e.g. **iPhone 14 / Pixel 7**, width 390px).
2. Type or paste text.
3. **Verification**:
   - Primary action buttons (**Copy**, **Clear**, **Swap**) remain docked in a sticky bottom bar accessible by thumb.
   - Touch targets are large (≥ 44×44px).
   - No horizontal scrollbars appear on any screen width.

---

### Scenario 4: Developer Diagnostics & Code Snippets
1. Switch to the **Developer Tools** tab and select **Unicode Scalar Inspector**.
2. Type `தமிழ்`.
3. **Verification**:
   - Displays 4 grapheme clusters: `த`, `மி`, `ழ்`.
   - Each scalar is broken down into hex badges: `U+0B94`, `U+0BAE`, `U+0BC0`, `U+0BB4`, `U+0BCD`.
   - Indicates `0 invisible controls` (no stray ZWJ/ZWNJ).
4. Click the **Code Generator** sub-tab.
5. **Verification**:
   - Generates exact, copy-pasteable snippets for **Rust**, **Python**, **TypeScript**, and **Dart**.

---

### Scenario 5: Offline Execution & Zero Network Telemetry
1. Open browser DevTools → **Network** tab.
2. Clear the network log.
3. Perform conversions, calculations, and collation.
4. **Verification**:
   - **Zero HTTP requests** are fired during text conversion or calculations.
   - In DevTools → Network, toggle **Offline**.
   - Reload or interact with the playground; the application remains fully functional.

---

## 4. Production Build & Static Output

To test the optimized production build:

```bash
# Build static Single Page Application
pnpm --filter playground build

# Preview static distribution locally
pnpm --filter playground preview
```

The output in `playground/dist/` is ready to deploy directly to GitHub Pages or any static CDN.
