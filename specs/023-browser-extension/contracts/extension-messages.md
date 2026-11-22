# Interface Contracts: Native-Themed Tamil Browser Extension

**Feature**: `023-browser-extension`  
**Date**: 2026-11-22  
**Spec**: [spec.md](spec.md)

## 1. Internal Runtime Message Protocol (`src/shared/messages.ts`)

All messages are strictly typed discriminated unions exchanged over `chrome.runtime.sendMessage` / `chrome.tabs.sendMessage` (wrapped via `src/shared/browser-api.ts`).

### A. Content Script / Panel → Background (WASM Engine & Coordination)

| Message `type` | Payload | Response |
| :--- | :--- | :--- |
| `ENGINE_TRANSLITERATE` | `{ text: string; scheme: TypingLayout }` | `{ ok: true; output: string } \| { ok: false; error: string }` |
| `ENGINE_INSPECT` | `{ text: string; source: InspectionSource; editable: boolean }` | `{ ok: true; snapshot: InspectionSnapshot } \| { ok: false; error: string }` |
| `ENGINE_REPAIR` | `{ text: string; stripJoiners?: false }` | `{ ok: true; text: string; diagnostics: RepairDiagnostics } \| { ok: false; error: string }` |
| `ENGINE_DETECT_AND_CONVERT` | `{ text: string; encoding: LegacyEncoding \| "auto" }` | `{ ok: true; text: string; detectedEncoding: string; confidence: number; ambiguous: boolean } \| { ok: false; error: string }` |
| `ENGINE_SORT_LINES` | `{ text: string; profile: "agara-v1" \| "uyirmei-first-v1" }` | `{ ok: true; text: string } \| { ok: false; error: string }` |
| `ENGINE_NUMERAL_WORDS` | `{ amount: string; locale: "TN" \| "SL"; currency?: "INR" \| "LKR" }` | `{ ok: true; words: string; formatted: string } \| { ok: false; error: string }` |
| `ENGINE_DATE_AND_HOLIDAYS` | `{ year: number; month: number; day: number; jurisdiction: "TN" \| "SL" }` | `{ ok: true; civilDateLabel: string; holidays: OfficialHolidayItem[]; supportedYear: boolean; sourceNote: string } \| { ok: false; error: string }` |
| `OPEN_SIDE_PANEL` | `{ tab?: PanelTab; handoff?: SelectionHandoffPayload }` | `{ ok: true }` |
| `TOGGLE_LIVE_TYPING` | `{ tabId?: number; enabled?: boolean; layout?: TypingLayout }` | `{ ok: true; enabled: boolean; layout: TypingLayout }` |

### B. Background / Panel → Content Script (Active Tab Interaction)

| Message `type` | Payload | Response |
| :--- | :--- | :--- |
| `TAB_SET_LIVE_STATE` | `{ enabled: boolean; layout: TypingLayout; uiLang: "ta" \| "en"; showMicroCounter: boolean; showConfirmToast?: boolean }` | `{ ok: true; editorKind: EditorKind }` |
| `TAB_GET_CONTEXT_TEXT` | `{ mode: "auto" \| "visible-page" }` | `{ ok: true; text: string; source: InspectionSource; editable: boolean }` |
| `TAB_REPLACE_TEXT` | `{ text: string; scope: "selection" \| "active-editor" }` | `{ ok: true; replaced: boolean }` |
| `TAB_INSERT_TEXT` | `{ text: string }` | `{ ok: true; inserted: boolean }` |

### C. Background → Offscreen Document (Chrome Silent Clipboard Copy Only)

| Message `type` | Payload | Response |
| :--- | :--- | :--- |
| `OFFSCREEN_COPY_TEXT` | `{ text: string }` | `{ ok: true } \| { ok: false; error: string }` |

## 2. Canonical WASM Engine Adapter Contract (`src/engine/tamil-engine.ts`)

Every linguistic operation delegates directly to `bindings/js-wasm` (`createApi(nativeExecute)`):

| Extension Feature | Canonical `tamil-toolkit` WASM Operation(s) |
| :--- | :--- |
| Live Typing (Phonetic / Tamil99 / Anjal / Bamini) | `transliterate(text, scheme, "to_tamil")` with schemes `"phonetic-v1"`, `"tamil99"`, `"anjal-phonetic"`, `"suratha-bamini"` |
| Document & Selection Inspector | `tamil-core` letter/syllable/category inspection + `is_nfc` + `repair_text` (dry-run diagnostics) + `detect_encoding` |
| Legacy Font Conversion (7 codecs + Auto) | `detect_encoding` + `bamini_to_unicode`, `tscii_bytes_to_unicode`, `tab_bytes_to_unicode`, `tam_bytes_to_unicode`, `anjal_bytes_to_unicode`, `vanavil_text_to_unicode`, `lt_tm_text_to_unicode` (with ambiguity threshold guarding Auto mode) |
| Unicode Repair | `repair_text(text, { strip_joiners: false })` |
| Line Sorting | `sort_lines` / `collate` with `"agara-v1"` (default) and `"uyirmei-first-v1"` |
| Numerals & Currencies | `decimal_to_words`, `currency_decimal_to_words` (`TN`/`SL`, `INR`/`LKR`) |
| Civil Date & Official Holidays | `format_tamil_date` / `calendar_display_info` + `calendar_official_holidays(jurisdiction, year)` (active APIs only; 13 planned ephemeris suites strictly excluded) |

## 3. Dual-Browser Manifest Contract (`scripts/build-manifests.mjs`)

| Field | `dist/chrome/manifest.json` | `dist/firefox/manifest.json` |
| :--- | :--- | :--- |
| `manifest_version` | `3` | `3` |
| `permissions` | `["activeTab", "scripting", "contextMenus", "storage", "clipboardWrite", "sidePanel", "offscreen"]` | `["activeTab", "scripting", "contextMenus", "storage", "clipboardWrite"]` |
| `optional_host_permissions` | `["https://*/*", "http://*/*"]` (requested one origin at a time) | `["https://*/*", "http://*/*"]` (requested one origin at a time) |
| `host_permissions` | *Omitted (zero at install)* | *Omitted (zero at install)* |
| `background` | `{ "service_worker": "background.js", "type": "module" }` | `{ "scripts": ["background.js"], "type": "module" }` |
| `side_panel` / `sidebar_action` | `"side_panel": { "default_path": "panel.html" }` | `"sidebar_action": { "default_panel": "panel.html", "open_at_install": false }` |
| `commands` | `toggle-live-typing` (`Alt+Shift+T`) | `toggle-live-typing` (`Alt+Shift+T`) |
| `content_security_policy` | `"extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"` | `"extension_pages": "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"` |
| `browser_specific_settings` | *Omitted* | `gecko`: `{ "id": "tamil-toolkit@tamil-toolkit.dev", "strict_min_version": "140.0", "data_collection_permissions": { "required": ["none"] } }` |
| `web_accessible_resources` | Bundled `.woff2` Tamil fonts for opt-in font fixing only | Bundled `.woff2` Tamil fonts for opt-in font fixing only |
