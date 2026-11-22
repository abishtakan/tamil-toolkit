# Quickstart Validation Guide: Native-Themed Tamil Browser Extension

**Feature**: `023-browser-extension`  
**Date**: 2026-11-22  
**Spec**: [spec.md](spec.md) | **Contracts**: [extension-messages.md](contracts/extension-messages.md) | **Data Model**: [data-model.md](data-model.md)

## Prerequisites

- Node.js 22+ and `pnpm` (workspace installed at repo root)
- Rust toolchain + `wasm-pack` (for building the slim Apache-2.0 WASM artifact)
- Chrome 116+ / Edge (for Chromium unpacked testing) and Firefox 140+ (for `about:debugging` / `web-ext` testing)

## 1. Build & Unit Verification (Real Slim WASM)

```bash
# Install workspace dependencies (after integrations/browser-extension is added to pnpm-workspace.yaml)
pnpm install

# Build slim WASM + Chrome MV3 + Firefox MV3 bundles
pnpm --filter tamil-browser-extension build

# Run Vitest suite against real slim WASM (translit, inspection, 7 codecs, repair, sort, numerals, active calendar)
pnpm --filter tamil-browser-extension test

# Package Chrome Web Store ZIP, Firefox AMO ZIP, and AMO reproducible source bundle
pnpm --filter tamil-browser-extension package
```

**Expected outcomes**:
- `integrations/browser-extension/dist/chrome/` and `integrations/browser-extension/dist/firefox/` are generated with valid manifests and bundled `LICENSE` + `NOTICE` + font notices.
- Each compressed browser ZIP is under **2 MiB** (target < 1.5 MiB) and contains zero broad host permissions.
- All Vitest assertions pass against the real compiled slim WASM binary (no mocks).

## 2. End-to-End Browser Validation Scenarios

### Chrome / Edge (`chrome://extensions` → Developer Mode → Load unpacked → `dist/chrome`)
1. **Zero-permission install**: Confirm Chrome displays no "Read and change all your data on all websites" warning.
2. **One-click live typing (P1)**: Focus a `<textarea>` or Gmail/WhatsApp Web composer, click the toolbar icon (or press `Alt+Shift+T`), verify the `த` badge appears and the Chrome-themed Shadow DOM floating pill appears for ~2s and stays visible while focused.
   - Type `vanakkam tamil ` in **Phonetic** → commits `வணக்கம் தமிழ் ` inline; type `test` + `Esc` → keeps `test`.
   - Switch pill to **Tamil99** / **Bamini** → verify instant per-keystroke Tamil output and clean Backspace/Undo.
   - Click outside onto non-editable text → floating pill auto-hides.
   - Focus a `<input type="password">` or `<input type="email">` → verify live typing stays inactive.
3. **Live Document Inspector (P2)**: Click **Inspect** on the pill (or open Side Panel → Inspect). Verify true Tamil letter count (`தமிழ்` = 4, not 5), Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, and Unicode health check; load broken Tamil (`visual kombu` / duplicate pulli) and verify 1-click **Repair in place** fixes it while preserving `U+200D` / `U+200C`.
4. **Right-click & Fix Text (P3)**:
   - Select broken Tamil on a read-only page → right-click → **Copy repaired Tamil** → copies silently without opening the side panel.
   - Select legacy Bamini/TSCII text → right-click → **Convert to Tamil…** → opens Side Panel → Fix Text pre-filled; verify ambiguous input prompts for explicit codec selection.
5. **Native Theme, Bilingual & Tools (P4)**: Toggle OS Light/Dark mode and `தமிழ் / EN` toggle; verify Chrome Refresh 2023 styling, TN/SL numeral & INR/LKR currency words, today's TN civil date + official TN/SL holidays, and opt-in **Improve Tamil fonts here** (plus Settings revocation).
6. **Restricted page fallback**: Open `chrome://settings` and click the toolbar icon → Side Panel opens directly as a standalone workspace.

### Firefox (`about:debugging#/runtime/this-firefox` → Load Temporary Add-on → `dist/firefox/manifest.json`)
- Repeat scenarios 1–6 above, additionally verifying:
  - Native Firefox Acorn/Proton sidebar styling (and `browser.theme.getCurrent()` adaptation).
  - Synchronous `sidebarAction.open()` on cold-start right-click **Convert to Tamil…**.
  - `web-ext lint` passes with zero errors.

## 3. Repository Quality Gates

```bash
just check-unicode
just check-release-policy
just check-release-files
```
