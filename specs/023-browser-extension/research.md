# Research & Architectural Decisions: Native-Themed Tamil Browser Extension

**Feature**: `023-browser-extension`  
**Date**: 2026-11-22  
**Spec**: [spec.md](spec.md)

## 1. Dual-Browser MV3 Architecture (Chrome/Edge vs. Firefox)

- **Decision**: Maintain a single TypeScript + Vite codebase under `integrations/browser-extension/` with a manifest generator (`scripts/build-manifests.mjs`) emitting target-specific MV3 packages in `dist/chrome/` and `dist/firefox/`, sharing one thin `src/shared/browser-api.ts` compatibility shim.
- **Rationale**:
  - Chrome/Edge (116+) use `sidePanel`, a service worker (`background.service_worker`), and `offscreen` for silent clipboard writes on right-click repair.
  - Firefox (140+) uses `sidebar_action` (`open_at_install: false`), non-persistent `background.scripts`, `browser_specific_settings.gecko` (with stable ID and `data_collection_permissions: { required: ["none"] }`), and supports direct `navigator.clipboard.writeText()` in background/user-gesture contexts without an offscreen document.
  - Firefox requires `browser.sidebarAction.open()` to be invoked synchronously within the user-gesture handler before awaiting storage or WASM; separating the manifest and wrapping the open call in `browser-api.ts` guarantees deterministic cold-start behavior on both browsers.
- **Alternatives considered**:
  - *Single shared `manifest.json`*: Rejected because Chrome warns/rejects `sidebar_action` and `background.scripts`, while Firefox rejects `side_panel` and `offscreen` for store review.
  - *WXT / Plasmo meta-framework*: Rejected to keep dependencies minimal, match the repo's existing Vite 8 + TypeScript 7 + Vitest 5 stack (`integrations/office-word-addin`), and guarantee reproducible AMO source builds with zero opaque codegen.

## 2. Zero-Scary-Permissions Live Inline Typing & Per-Site Opt-In

- **Decision**:
  - **Required permissions**: `activeTab`, `scripting`, `contextMenus`, `storage`, `clipboardWrite` (+ `sidePanel`, `offscreen` on Chrome only). **Zero required host permissions** (`<all_urls>` is never requested at install).
  - **Activation**: Clicking the toolbar icon (`action.onClicked`) or pressing the manifest command shortcut (`Alt+Shift+T`) grants temporary `activeTab` access and dynamically injects the lightweight content script (`src/content/index.ts`) into the active tab, toggling Live Typing ON/OFF and updating the toolbar badge (`த` / empty). On browser-restricted URLs (`chrome://`, `edge://`, `about:`, store pages), clicking the icon opens the Side Panel / Sidebar directly.
  - **Optional per-site persistence**: "Always on for this site" and "Improve Tamil fonts here" call `permissions.request({ origins: ["https://<hostname>/*"] })` strictly for the current origin, registering a dynamic content script (`scripting.registerContentScripts`) or CSS injection (`scripting.insertCSS`) and allowing one-click revocation (`permissions.remove` + `scripting.removeCSS` / `unregisterContentScripts`).
- **Rationale**: Chrome Web Store and Mozilla AMO reviewers scrutinize `<all_urls>` heavily, and users distrust extensions that ask to "Read and change all your data on all websites." On-demand `activeTab` + opt-in per-origin permissions give instant 1-click live typing with the cleanest possible privacy posture.
- **Alternatives considered**:
  - *Static `content_scripts` on `<all_urls>`*: Rejected due to broad install warning and slower store review.
  - *Side-panel-only copy-paste*: Rejected per user requirement for direct live inline typing without copy-paste friction.

## 3. Hybrid Live Typing Engine & Modern Web Editor Compatibility

- **Decision**: Implement a two-mode inline engine in `src/content/live-typing.ts` backed by the canonical Rust/WASM `transliterate` API (`phonetic-v1`, `tamil99`, `anjal-phonetic`, `suratha-bamini`):
  - **Phonetic (`phonetic-v1`) & Anjal (`anjal-phonetic`)**: Track the active Latin word before the caret, render a live Tamil preview in the Shadow DOM floating pill, and commit on Space, Enter, or punctuation. Pressing `Escape` marks the current word as bypassed so English words stay intact. Backspace edits raw Latin letters naturally before commit.
  - **Tamil99 (`tamil99`) & Bamini (`suratha-bamini`)**: Maintain a short rolling syllable/keystroke buffer for the current sequence and replace inline immediately per keystroke so fixed-layout typists get instant Tamil feedback.
  - **Editor insertion strategy**:
    - Native `<input>` / `<textarea>`: `setRangeText()` + dispatching `input` event (`inputType: "insertReplacementText"`, `bubbles: true`) so React/Vue/Angular controlled inputs update reliably.
    - `contenteditable` (Gmail, WhatsApp Web, X, LinkedIn, Reddit, Notion): Collapse selection over the replaced range and invoke `document.execCommand("insertText", false, replacement)` (falling back to `Range.deleteContents()` + `insertNode()` + `InputEvent`), preserving editor Undo stacks and framework state.
  - **Sensitive input guard**: Automatically stay inactive when `activeElement` is `input[type=password|email|url|tel|number|hidden|date|time|color|range]` or carries `autocomplete` tokens like `one-time-code` / `cc-*`.
  - **Canvas fallback**: Detect known canvas editors (e.g., Google Docs `.kix-canvas-tile-content`, Figma `<canvas>`) or failed inline replacement and surface a compact Quick-Compose scratchpad inside the Shadow DOM pill with 1-click Copy / Insert.
- **Rationale**: Covers real-world web editors safely while honoring both Phonetic/Anjal muscle memory and Tamil99/Bamini muscle memory, and never breaks credentials or canvas apps.
- **Alternatives considered**:
  - *Single word-boundary mode for all layouts*: Rejected during clarification (feels laggy for Tamil99/Bamini typists).
  - *Direct DOM text-node mutation on `contenteditable`*: Rejected because it desyncs React/Draft.js/Lexical/ProseMirror internal state and breaks Undo.

## 4. WASM Execution Placement & Package Size Budget (< 2 MiB)

- **Decision**:
  - Reuse the slim Apache-2.0 default-profile WASM build (`bindings/js-wasm`, no heavy lexicon packs) via a shared script helper extracted from `integrations/office-word-addin/scripts/prepare-wasm.mjs` (accepting `--out-dir`).
  - Run the slim WASM module in the **extension context** (Side Panel / Sidebar and Background Service Worker / Event Page, where `extension_pages` CSP allows `script-src 'self' 'wasm-unsafe-eval'; object-src 'self'`).
  - Content scripts remain tiny (< 25 KiB JS) and send lightweight RPC messages (`TRANSLITERATE_WORD`, `REPAIR_TEXT`, `INSPECT_TEXT`) over `runtime.sendMessage` to the background WASM host (round-trip < 5 ms local IPC, well under the 50 ms budget), avoiding host-page CSP `wasm-unsafe-eval` restrictions on sites like GitHub or Gmail!
- **Rationale**: Strict host sites (GitHub, Gmail, banking apps) set `Content-Security-Policy` headers that block `WebAssembly.instantiate` inside injected content scripts. Hosting WASM in the extension's own background/panel origin works on 100% of websites, loads WASM once per browser session, and keeps total compressed ZIP size well under 1.5 MiB (strictly below SC-005's 2 MB cap).
- **Alternatives considered**:
  - *Loading WASM directly in every content script*: Rejected because host-page CSP blocks WASM compilation on strict sites and duplicates memory per tab.
  - *Duplicating transliteration/inspection rules in JS inside the content script*: Strictly forbidden by Constitution Principle I ("Rust Owns Linguistic Behavior").

## 5. Native Host-Browser Theming & Shadow DOM Isolation

- **Decision**:
  - Use a shared semantic CSS custom-property system (`src/shared/theme/base.css`) with two build-selected token layers:
    - `chrome-tokens.css` (Chrome Refresh 2023 tonal surfaces `#f8f9fa`/`#ffffff` light, `#202124`/`#292a2d` dark, accent `#1a73e8`/`#8ab4f8`, pill controls, `1px` hairline dividers `#dadce0`/`#3c4043`).
    - `firefox-tokens.css` (Firefox Acorn/Proton surfaces `#f9f9fb`/`#ffffff` light, `#1c1b22`/`#2b2a33` dark, accent `#0060df`/`#00ddff`, tighter `4px–8px` radii, `2px` focus rings), enhanced at runtime with optional `browser.theme.getCurrent()` color mapping when available.
  - Isolate the on-page floating pill inside an open **Shadow DOM** root with adopted stylesheets using the same browser-specific tokens + `prefers-color-scheme`, so host page CSS never leaks in and extension CSS never leaks out.
  - Bundle subsetted `Noto Sans Tamil` (weights 400/500/600) and `Noto Sans Tamil Supplement` (`U+11FC0–U+11FFF`) `.woff2` files from `@fontsource` (matching `playground/src/index.css`) for Tamil glyphs only, keeping UI chrome in native system fonts.
- **Rationale**: Achieves genuine native browser look-and-feel on both Chrome/Edge and Firefox with zero duplicate UI components and minimal bundle overhead (~180 KiB for WOFF2 subsets).
- **Alternatives considered**:
  - *Tailwind CSS or heavy UI component library (MUI/Radix)*: Rejected to keep the extension lean, native-looking, and fast-loading without framework bloat.

## 6. Inspection Engine & Calendar Scope Guardrails

- **Decision**:
  - Reuse the exact `tamil-core` inspection logic pattern proven in `integrations/office-word-addin/src/lib/tamil-engine.ts` (`word_count`, `letter_count`, `syllable_count`, `uyir_count`, `mei_count`, `uyirmei_count`, `aytham_count`, `grantha_count`, `zero_width_count`, `soft_hyphen_count`, `is_nfc`, plus `detect_encoding` and `repair_text` dry-run diagnostics).
  - Restrict the Tools → Dates view exclusively to **active** calendar APIs (`format_tamil_date`, `calendar_display_info`, `calendar_official_holidays` for `TN` and `SL`), surfacing clear source attribution and unsupported-year messaging; never expose any of the 13 `planned` ephemeris/panchangam suites.
- **Rationale**: Honors Constitution Principles I, III, V, and VII and guarantees zero hallucinated or unimplemented linguistic/calendar claims.
- **Alternatives considered**:
  - *JS regex letter counting in the extension UI*: Strictly forbidden by Constitution Principle I and II.
