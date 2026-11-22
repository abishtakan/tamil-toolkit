# Feature Specification: Native-Themed Tamil Browser Extension

**Feature Branch**: `023-browser-extension`

**Created**: 2026-11-22

**Status**: Draft

**Input**: User description: "Chrome/Edge and Firefox browser extension for everyday Tamil typing, text repair/legacy conversion, live document inspection (Tamil letter count, word count, script breakdown, health check), numerals/dates, and opt-in font fixing — featuring direct live inline typing on web pages (no copy-paste friction), native host-browser theming (Chrome theme on Chrome/Edge, Firefox theme on Firefox), bilingual Tamil/English UI, and strict zero-clutter, privacy-first design."

## Clarifications

### Session 2026-11-22

- Q: How should live Tamil typing update text inside a web page input as you type across Phonetic, Tamil99, Anjal, and Bamini layouts? → A: Hybrid mode — Phonetic and Anjal preview the current word and commit on word boundaries (Space, Enter, or punctuation, with Escape keeping English), while Tamil99 and Bamini convert immediately per keystroke.
- Q: What should happen when the user clicks the extension's toolbar icon? → A: Toggle Live Tamil Typing ON/OFF immediately on the current tab (showing a `த` badge and the floating pill), with a one-click button on the pill and context menu to open the Side Panel / Sidebar (and opening the Side Panel directly on restricted pages where page typing is unavailable).
- Q: When Live Tamil Typing is turned ON for a tab, when should the on-page floating pill be visible? → A: Focus-aware — appear briefly (~2 seconds) on toggle for confirmation, stay visible while an editable field is focused, and auto-hide when reading non-editable page content.
- Q: When the user opens the Inspect view with no text highlighted and no text box focused, what should it inspect by default? → A: Auto-inspect the highlighted selection or focused editable field; when neither is active, present a one-click "Inspect visible page" action alongside a standalone paste/type input.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Inline Tamil Typing on Any Web Page (Priority: P1)

A Tamil user composing an email, chat message, comment, or web form activates Live Tamil Typing with a keyboard shortcut or toolbar action and types directly inside the web page's input field using their preferred keyboard layout (Phonetic Tanglish, Tamil99, Anjal, or Bamini). As they type, each word previews and commits cleanly into standard Tamil text in place—without switching windows or copying and pasting—while an unobtrusive floating control lets them toggle between Tamil and English or switch layouts in one click.

**Why this priority**: Direct live typing is the highest-frequency daily Tamil task in a browser. Eliminating copy-paste friction is the primary reason users install and keep a Tamil browser extension.

**Independent Test**: Can be fully tested by opening a standard web page with a text input or multi-line editor, toggling Live Tamil Typing on, typing a sentence in Phonetic (Tanglish), Tamil99, Anjal, or Bamini, toggling back to English, and verifying that standard Tamil text is committed inline while Backspace and browser Undo continue to work naturally.

**Acceptance Scenarios**:

1. **Given** a user is focused inside a standard text field or rich-text editor on a web page and activates Live Tamil Typing via keyboard shortcut or toolbar button, **When** they type a word in Phonetic (Tanglish) or Anjal and press Space or Enter (or type directly in Tamil99 or Bamini where each keystroke converts immediately), **Then** the text commits inline as properly formed Tamil text in that same field without requiring copy-paste.
2. **Given** Live Tamil Typing is active on a web page, **When** the user presses Escape while composing a word or switches the floating pill to English, **Then** the untransliterated Latin text is preserved as typed and subsequent keystrokes remain in English.
3. **Given** Live Tamil Typing is active, **When** the user switches layouts in the floating pill (between Phonetic, Tamil99, Anjal, and Bamini), **Then** subsequent keystrokes immediately use the newly selected layout and the chosen layout is remembered for future sessions.
4. **Given** a user is working in a canvas-based or restricted web editor where direct inline text replacement is blocked by the site, **When** they activate Live Tamil Typing, **Then** the extension clearly provides a compact quick-compose scratchpad with one-action copy or paste guidance instead of silently failing.
5. **Given** a user wants Live Tamil Typing ready automatically on a frequently used website, **When** they enable "Always on for this site", **Then** the extension requests permission only for that specific website and activates automatically on future visits to that site without requesting broad access to all websites.

---

### User Story 2 - Live Document and Selection Tamil Inspector (Priority: P2)

A writer, student, journalist, or editor opens the extension's side panel (or clicks Inspect from the floating pill) to inspect the active text field, selected text, or visible page content. They immediately see true Tamil linguistic counts—actual Tamil letter count (எழுத்து), word count (சொல்), syllable count, estimated reading time, and a visual breakdown across Uyir (உயிர்), Mei (மெய்), Uyirmei (உயிர்மெய்), Aytham (ஆய்தம்), and Grantha (கிரந்தம்)—alongside a Unicode health check that flags broken vowel signs, duplicate pullis, hidden invisible characters, or legacy font encodings with a one-click in-place repair option.

**Why this priority**: Standard browsers and word counters miscount Tamil by measuring raw character units rather than true Tamil letters (for example, counting தமிழ் as 5 instead of 4). Giving writers instant linguistic counts and text-health diagnostics directly on the web page solves a major everyday gap.

**Independent Test**: Can be fully tested by typing or selecting Tamil text (including both clean text and text with visual-order vowel signs or duplicate pullis) on a web page, opening the Inspect view, verifying the true Tamil letter count, word count, category breakdown, and health warnings, and triggering one-click in-place repair when editable.

**Acceptance Scenarios**:

1. **Given** a user has typed or selected Tamil text on a web page, **When** they open the Inspect view, **Then** it displays the exact Tamil letter count (counting each Uyir, Mei, Uyirmei, Aytham, and Grantha unit as one letter), word count, raw character-unit count, and estimated reading time.
2. **Given** the inspected text contains mixed Tamil letter categories, **When** the Inspect view updates, **Then** it displays an accurate breakdown of Uyir, Mei, Uyirmei, Aytham, and Grantha counts.
3. **Given** the inspected text inside an editable field contains malformed Tamil sequences (such as visually reversed left vowel signs, duplicate pullis, or non-canonical composition), **When** the Inspect view evaluates the text, **Then** it flags the specific issue count and provides a "Repair in place" action that fixes the text directly in the editor while preserving intentional invisible joiners (U+200D and U+200C).
4. **Given** a user types in a supported web editor with Live Tamil Typing active, **When** the optional live micro-counter is enabled, **Then** a subtle letter and word counter updates in real time without obstructing the writing area.

---

### User Story 3 - In-Place Legacy Text Conversion, Repair, and Line Sorting (Priority: P3)

A user encounters garbled legacy-encoded Tamil text (such as Bamini, TSCII, TAB, TAM, Anjal, Vanavil, or LT-TM), broken Unicode Tamil, or an unsorted list of Tamil names or lines on a web page. They can right-click selected text or open the Fix Text tab to convert, repair, or sort lines in Tamil alphabetical order (அகர வரிசை default, with Uyirmei-first as a secondary option), applying changes directly in place inside editable fields or copying cleanly from read-only pages.

**Why this priority**: Legacy-encoded Tamil text and broken Unicode remain widespread across government portals, news archives, and pasted documents; instant conversion and repair remove tedious external web-tool workflows.

**Independent Test**: Can be fully tested by selecting legacy Bamini or TSCII text on a read-only page and inside an editable field, running Auto-detect and explicit conversion, repairing broken Tamil text, and sorting multi-line Tamil lists in both alphabetical orders.

**Acceptance Scenarios**:

1. **Given** a user selects broken Tamil text on a read-only page and chooses "Copy repaired Tamil" from the right-click menu, **When** the action runs, **Then** the repaired text is copied to the clipboard silently without forcing the side panel open, and intentional joiners (U+200D and U+200C) are preserved.
2. **Given** a user selects legacy-encoded Tamil text and chooses "Convert to Tamil..." from the right-click menu, **When** the Fix Text view opens, **Then** the selected text is pre-filled with a live preview of the converted Tamil output; if auto-detection is ambiguous, the user is prompted to pick the exact encoding before replacing or copying.
3. **Given** a user selects legacy or broken Tamil text inside an editable field, **When** they trigger "Repair & Replace" or "Convert & Replace", **Then** the selected text is replaced directly in place without manual copy-paste.
4. **Given** a user has a multi-line list of Tamil items, **When** they choose Sort Lines in Fix Text, **Then** the lines are sorted using traditional Tamil alphabetical order (அகர வரிசை) by default, with an option to switch to Uyirmei-first ordering.

---

### User Story 4 - Native Host-Browser Appearance, Bilingual Interface, and Compact Everyday Tools (Priority: P4)

A user opens the extension in Chrome, Edge, or Firefox and experiences an interface that looks and feels like a built-in part of their browser—matching Chrome's visual language on Chrome/Edge and Firefox's visual language on Firefox, automatically following Light and Dark mode, and speaking their preferred UI language (Tamil or English). Inside a secondary Tools tab, they can also convert numbers and currencies (INR and LKR, with Tamil Nadu and Sri Lanka wording) into Tamil words, check today's Tamil civil date and official TN/SL holidays, or opt in to improve Tamil font rendering on websites with broken Tamil fonts.

**Why this priority**: Native visual polish, bilingual accessibility, and lightweight companion utilities (numerals, dates, per-site font fixing) complete the everyday toolkit without cluttering the primary typing and inspection workflows.

**Independent Test**: Can be fully tested by opening the extension in both Chrome/Edge and Firefox under Light and Dark themes, switching the UI between Tamil and English, converting numbers/currencies for TN and SL locales, viewing today's civil date and official holiday data, and toggling per-site font improvement on and off.

**Acceptance Scenarios**:

1. **Given** the extension is opened in Chrome or Edge, **When** the user views the side panel or on-page floating pill in Light or Dark mode, **Then** the surfaces, typography, spacing, controls, and accent styling match Chrome's native side-panel aesthetic; when opened in Firefox, they match Firefox's native sidebar aesthetic (and adapt to active Firefox theme colors where available).
2. **Given** a user opens the extension for the first time, **When** their browser locale is Tamil, **Then** the interface defaults to Tamil; otherwise it defaults to English, and a persistent one-click `தமிழ் / EN` toggle switches the entire interface immediately and remembers the choice.
3. **Given** a user opens the Tools tab, **When** they enter a number or currency amount (INR or LKR) and select Tamil Nadu or Sri Lanka wording, **Then** the extension displays the accurate Tamil number words offline.
4. **Given** a user opens the Dates section in Tools, **When** viewing today's date or official holidays, **Then** it displays the supported Tamil Nadu civil date and official TN/SL holiday entries with clear source attribution and transparent messaging for unsupported years (without showing unimplemented astronomical panchangam calculations).
5. **Given** a user visits a website where Tamil text or Tamil Supplement characters (U+11FC0–U+11FFF) render poorly, **When** they opt in to "Improve Tamil fonts here", **Then** readable bundled Tamil fonts are applied only to Tamil reading content on that site (never overriding editable inputs), and revoking the site restores the site's original styling cleanly.

---

### Edge Cases

- **Canvas and proprietary web editors (e.g., Google Docs, Figma, custom canvas editors)**: Direct inline text editing is not possible; the extension must detect or allow graceful fallback to the floating quick-compose scratchpad without corrupting cursor state or dropping keystrokes.
- **Ambiguous legacy encoding detection**: When short or mixed-script text cannot be unambiguously classified as a single legacy encoding, Auto mode must never silently apply a wrong conversion—it must ask the user to select the encoding explicitly.
- **Invisible format controls (U+200D ZWJ, U+200C ZWNJ)**: Repair and normalization flows must preserve intentional joiners by default and never silently strip them from user text.
- **Shadowed or hostile page styles**: The on-page floating typing pill must be visually isolated so host website stylesheets never distort its layout, and its own styles never leak onto the host website.
- **Read-only vs. editable selection**: Right-click and panel actions must offer in-place replacement only when the target field is editable, falling back smoothly to clipboard copy on read-only pages.
- **Offline operation and restricted browser pages**: All linguistic features must work 100% offline with zero external network requests. On browser-restricted pages (such as internal settings pages or extension stores) where page injection is disallowed, the side panel must remain usable as a standalone typing, inspection, conversion, and tools workspace with a clear notice that live page typing is unavailable on that page.
- **Empty or non-Tamil input**: Inspecting empty or purely English text must show zero Tamil letter counts cleanly without errors, and converting already-valid Unicode Tamil in Auto mode must preserve it cleanly.
- **Unsupported holiday or calendar years**: Requests outside the supported official holiday dataset must display a clear, honest unsupported-year notice rather than fabricated dates.
- **Sensitive or non-prose input fields**: Live Inline Tamil Typing must automatically stay inactive on password, email address, URL, telephone, numeric, and one-time-code input fields so credentials and structured inputs are never altered or intercepted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The extension MUST support Chrome, Edge, and Firefox with feature-equivalent core capabilities across both browser families.
- **FR-002**: The extension MUST operate 100% offline for all linguistic, inspection, conversion, sorting, numeral, date, and font-rendering features, sending zero user text or telemetry to any external server.
- **FR-003**: Clicking the extension toolbar icon or pressing the configurable keyboard shortcut (defaulting to `Alt+Shift+T`) MUST immediately toggle Live Inline Tamil Typing ON/OFF on the active tab (displaying an active `த` toolbar badge and a focus-aware on-page floating pill) across supported text inputs, multi-line text boxes, and standard editable regions. The floating pill MUST appear briefly (~2 seconds) on toggle for confirmation, stay visible while an editable field is focused, and auto-hide when reading non-editable content; both the floating pill and toolbar/page context menus MUST provide one-click access to open the Side Panel / Sidebar. On browser-restricted pages where live page typing is unavailable, clicking the toolbar icon MUST open the Side Panel / Sidebar directly.
- **FR-004**: Live Inline Tamil Typing MUST support four everyday Tamil input layouts: Phonetic (Tanglish), Tamil99, Anjal, and Bamini, allowing users to switch layouts from either the floating pill or the side panel and persisting the last-used layout.
- **FR-005**: Live Inline Tamil Typing MUST use a hybrid commitment model: Phonetic (Tanglish) and Anjal MUST display a lightweight inline word preview while composing, commit on word boundaries (Space, Enter, or punctuation), and allow cancelling transliteration for the current word with Escape; Tamil99 and Bamini MUST convert immediately per keystroke. Both modes MUST preserve natural Backspace editing and browser Undo behavior.
- **FR-006**: On websites or canvas-based editors where inline text replacement is unavailable, the extension MUST provide a quick-compose fallback scratchpad with one-action copy or paste guidance.
- **FR-007**: The extension MUST request zero broad "all websites" host permissions at install time; on-demand activation MUST apply only to the active tab, and persistent per-site activation ("Always on for this site") or per-site font fixing MUST require explicit user opt-in scoped strictly to that single website, with a clear list and one-click revocation in Settings.
- **FR-008**: The extension MUST provide an Inspect view that automatically analyzes the current highlighted selection or focused editable field and reports true Tamil letter count (எழுத்து), word count (சொல்), syllable count, raw character-unit count, estimated reading time, and per-category breakdown (Uyir, Mei, Uyirmei, Aytham, Grantha). When neither a selection nor a focused editable field is active, the Inspect view MUST offer a one-click "Inspect visible page" action as well as a standalone paste/type box.
- **FR-009**: The Inspect view MUST run a Unicode health check reporting non-canonical composition, visually reversed left vowel signs, duplicate pullis, hidden zero-width/soft-hyphen characters, and detected legacy encodings, and MUST offer a one-click "Repair in place" action when inspecting an editable field.
- **FR-010**: The extension MUST provide an optional live micro-counter showing Tamil letter and word counts while typing in an active editor.
- **FR-011**: The extension MUST support converting legacy-encoded Tamil text to standard Unicode Tamil across Bamini, TSCII, TAB, TAM, Anjal, Vanavil, and LT-TM, with an Auto-detect default that requires explicit user confirmation when detection is ambiguous.
- **FR-012**: The extension MUST support repairing malformed Unicode Tamil text (preserving U+200D and U+200C by default) and sorting multi-line Tamil text in traditional alphabetical order (அகர வரிசை default) and Uyirmei-first order.
- **FR-013**: Selection right-click actions MUST include silent "Copy repaired Tamil" (without forcing the side panel open on success), "Convert to Tamil..." (opening Fix Text pre-filled with live preview), and in-place replace when the selection is inside an editable field.
- **FR-014**: The extension MUST provide a Tools view supporting offline number-to-Tamil-words and currency-to-Tamil-words conversion (INR and LKR with explicit Tamil Nadu and Sri Lanka regional wording), today's supported Tamil Nadu civil date, and official TN/SL holiday entries with source attribution and honest unsupported-year messaging.
- **FR-015**: The extension MUST provide an opt-in per-site "Improve Tamil fonts here" control that applies bundled readable Tamil and Tamil Supplement (U+11FC0–U+11FFF) fonts only to Tamil reading elements on that site (excluding editable inputs) and cleanly restores original styling when revoked.
- **FR-016**: The extension UI MUST adapt visually to feel native to the host browser—following Chrome's native side-panel visual language on Chrome/Edge and Firefox's native sidebar visual language on Firefox—and automatically follow system Light and Dark appearance.
- **FR-017**: The extension UI MUST be fully bilingual in Tamil and English, auto-defaulting to Tamil when the browser locale is Tamil, with a persistent one-click `தமிழ் / EN` toggle.
- **FR-018**: All linguistic operations MUST delegate exclusively to the single canonical `tamil-toolkit` engine (no duplicated Tamil linguistic logic in the extension UI) and MUST NOT expose unimplemented/planned astronomical ephemeris features or heavy dictionary packs that bloat install size.

### Key Entities

- **User Preferences**: Persistent local settings storing UI language (`ta` or `en`), active typing layout (`phonetic`, `tamil99`, `anjal`, `bamini`), last opened panel tab, numeral regional dialect (`TN` or `SL`), and live micro-counter visibility.
- **Per-Site Permission Record**: User-granted site-scoped configuration recording which specific hostnames have opted in to "Always-on Live Typing" and/or "Improve Tamil Fonts Here", supporting inspection and one-click revocation.
- **Active Composition Session**: Transient in-tab typing state tracking whether live Tamil typing is enabled for the current tab, the active layout, the current word buffer being composed, and whether the focused field supports inline replacement or requires the scratchpad fallback.
- **Inspection Snapshot**: Transient analysis result for a text selection, active editor, or page, containing true Tamil letter count, word count, syllable count, character-unit count, script category counts (Uyir, Mei, Uyirmei, Aytham, Grantha), reading time estimate, and Unicode health diagnostics.
- **Selection Handoff Payload**: Short-lived single-use transfer item carrying right-clicked page text (and whether the source was editable) into the side panel when opening Fix Text or Inspect from a cold start.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can activate Live Tamil Typing on a standard web page and commit their first Tamil sentence inline in under 5 seconds without copying or pasting.
- **SC-002**: Live inline typing preview and word commit feel instantaneous to the user, completing in under 50 milliseconds per keystroke or word commit completely offline.
- **SC-003**: Document and selection inspection returns 100% accurate Tamil letter counts, script-category breakdowns, and Unicode health diagnostics matching the canonical toolkit test vectors across all active test cases.
- **SC-004**: 100% of active conversion, repair, sorting, transliteration, numeral, and supported civil-date/holiday scenarios produce identical results offline with zero external network requests.
- **SC-005**: The installable extension package stays compact (under 2 MB compressed per browser) with zero broad host-permission warnings required at installation.
- **SC-006**: Users can switch UI language (Tamil/English), toggle Live Tamil Typing (`தமிழ் / EN`), or repair malformed text in place in a single click or keyboard shortcut from their current workflow.
- **SC-007**: First-time users on both Chrome/Edge and Firefox can identify and complete any primary task (Live Type, Inspect, Fix Text) within 3 seconds of opening the extension without encountering developer jargon or visual clutter.

## Assumptions

- **Target Browsers**: Modern desktop versions of Google Chrome, Microsoft Edge, and Mozilla Firefox that support side panels / sidebars and modern extension packaging; mobile browser extensions are out of scope for v1.
- **Scope Exclusions (Anti-Clutter)**: Scholarly romanization schemes (ISO 15919, ITRANS, Harvard-Kyoto, Madras Lexicon), full dictionary/morphological lookup packs, hyphenation, batch/PDF conversion, symbol tables, reverse legacy export, and planned astronomical panchangam/ephemeris suites remain in the web Playground and are intentionally excluded from the browser extension to keep it fast, compact, and uncluttered.
- **Regional Dialect Coverage**: All Unicode inspection, repair, sorting, and typing operations are dialect-invariant across Tamil Nadu and Sri Lanka; numeral/currency wording and official holiday listings explicitly support both Tamil Nadu (TN / INR) and Sri Lanka (SL / LKR) scopes.
- **Single-Engine Reuse**: The extension reuses the existing canonical `tamil-toolkit` engine already validated across the repository, without introducing any secondary Tamil text-processing implementation.
- **Canvas Editor Constraint**: Because browser security and canvas rendering models in apps like Google Docs prevent reliable direct inline text replacement by extensions, providing an explicit quick-compose scratchpad fallback is the safest, most predictable user experience.
