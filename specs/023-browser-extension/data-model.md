# Data Model: Native-Themed Tamil Browser Extension

**Feature**: `023-browser-extension`  
**Date**: 2026-11-22  
**Spec**: [spec.md](spec.md)

All state is stored strictly locally in browser extension storage (`storage.local` for persistent user settings, `storage.session` for transient tab/handoff state). Zero data leaves the device.

## 1. UserPreferences (`storage.local["prefs_v1"]`)

Persistent user configuration shared across the side panel, background worker, and content scripts.

| Field | Type | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- |
| `uiLang` | `"ta" \| "en"` | `"ta"` if `i18n.getUILanguage()` starts with `"ta"`, else `"en"` | Must be `"ta"` or `"en"`. |
| `layout` | `"phonetic-v1" \| "tamil99" \| "anjal-phonetic" \| "suratha-bamini"` | `"phonetic-v1"` | Must map 1:1 to a supported `tamil-translit` scheme ID. |
| `lastTab` | `"inspect" \| "live" \| "fix" \| "tools"` | `"live"` | Restored when reopening the side panel. |
| `numeralLocale` | `"TN" \| "SL"` | `"TN"` | Controls numeral/currency wording and default holiday jurisdiction. |
| `currency` | `"INR" \| "LKR"` | `"INR"` | Paired with `numeralLocale` (`INR` default for `TN`, `LKR` for `SL`). |
| `sortProfile` | `"agara-v1" \| "uyirmei-first-v1"` | `"agara-v1"` | Maps directly to `tamil-collate` profile IDs. |
| `showMicroCounter` | `boolean` | `true` | Controls optional live `எழுத்து · சொல்` counter in the floating pill. |

## 2. PerSitePermissionRecord (`storage.local["site_rules_v1"]`)

Tracks user-opted-in hostnames (`Map<hostname, SiteRule>`), always reconciled against actual browser `permissions.getAll()` origins on startup and Settings open.

| Field | Type | Default | Validation / Constraints |
| :--- | :--- | :--- | :--- |
| `originPattern` | `string` | — | Strictly `https://<hostname>/*` or `http://<hostname>/*`; never `<all_urls>`. |
| `alwaysOnLiveTyping` | `boolean` | `false` | When `true`, content script auto-attaches on matching origin visits. |
| `improveTamilFonts` | `boolean` | `false` | When `true`, injects bundled Noto Tamil + Tamil Supplement CSS on `:lang(ta)` reading elements outside editable inputs. |
| `updatedAt` | `number` | `Date.now()` | Epoch milliseconds for audit/sorting in Settings. |

**State Transitions**:
- `Unregistered` → `Active` (requires explicit user gesture + `permissions.request({ origins: [originPattern] })` approval).
- `Active` → `Revoked` (removes injected CSS via `scripting.removeCSS`, unregisters dynamic script if neither flag remains, calls `permissions.remove`, and deletes the record).

## 3. ActiveCompositionSession (In-Memory per Tab + `storage.session["tab_state_<tabId>"]`)

Transient per-tab typing state managed by the background coordinator and mirrored in the tab's content script.

| Field | Type | Constraints |
| :--- | :--- | :--- |
| `tabId` | `number` | Valid active browser tab ID. |
| `enabled` | `boolean` | `true` when Live Tamil Typing is toggled ON for this tab (`த` badge shown). |
| `layout` | `TypingLayout` | Synced from `UserPreferences.layout`; switchable live from pill or panel. |
| `commitMode` | `"word-boundary" \| "instant-keystroke"` | Derived deterministically: `"word-boundary"` for `phonetic-v1` and `anjal-phonetic`; `"instant-keystroke"` for `tamil99` and `suratha-bamini`. |
| `rawBuffer` | `string` | Current uncommitted Latin word/sequence before caret (cleared on Space/Enter/blur/Escape). |
| `previewText` | `string` | Latest Rust/WASM transliteration preview for `rawBuffer`. |
| `escapedCurrentWord` | `boolean` | `true` after user presses `Escape`, preventing transliteration until next word boundary. |
| `editorKind` | `"native-input" \| "contenteditable" \| "canvas-fallback" \| "none"` | Determines whether inline replacement runs directly or falls back to Quick-Compose scratchpad. |
| `pillVisible` | `boolean` | Focus-aware: `true` for ~2s on toggle confirmation, `true` while an editable field is focused, `false` when reading non-editable content. |

## 4. InspectionSnapshot (Transient, Computed On Demand)

Produced by the canonical `tamil-toolkit` WASM engine for a selection, focused editor, visible page, or standalone pasted text.

| Field | Type | Notes |
| :--- | :--- | :--- |
| `source` | `"selection" \| "active-editor" \| "visible-page" \| "manual"` | Identifies what was inspected. |
| `editable` | `boolean` | Enables one-click "Repair in place" only when `true`. |
| `letterCount` | `number` | True Tamil linguistic letters (`uyir + mei + uyirmei + aytham + grantha`). |
| `wordCount` | `number` | Whitespace-delimited word count. |
| `syllableCount` | `number` | Syllables (`olippasai`) from `tamil-core`. |
| `utf16Length` | `number` | Raw JS string length for comparison against true letter count. |
| `readingSeconds` | `number` | Estimated reading time (~180 words/min, min 1s when non-empty). |
| `breakdown` | `{ uyir: number; mei: number; uyirmei: number; aytham: number; grantha: number; other: number }` | Per-category letter counts. |
| `health` | `{ isNfc: boolean; duplicatePullis: number; visualKombus: number; zeroWidthCount: number; softHyphenCount: number; detectedLegacyEncoding: string \| null; legacyConfidence: number; totalIssues: number }` | Drives the Health badge and "Repair in place" CTA. |

## 5. SelectionHandoffPayload (`storage.session["handoff_latest"]`)

Short-lived single-use payload for cold-start right-click actions ("Convert to Tamil…", "Inspect selection").

| Field | Type | Constraints |
| :--- | :--- | :--- |
| `requestId` | `string` | Unique monotonic/UUID token so each handoff is consumed exactly once. |
| `tabId` | `number` | Originating tab ID (for optional in-place replacement). |
| `action` | `"convert" \| "inspect"` | Target side-panel tab to activate on open. |
| `text` | `string` | Selected text captured from context menu or content script. |
| `editable` | `boolean` | Whether the selection originated inside an editable field. |
| `createdAt` | `number` | Expired/discarded if older than 60 seconds. |
