# Feature Specification: Bilingual Architecture & Internationalization Best Practices

**Feature Branch**: `006-bilingual-best-practices`

**Created**: 2026-11-05

**Status**: Complete — listed implementation tasks and verification are complete (2026-11-08)

**Input**: User description: "Enhance bilingual i18n architecture with centralized dictionary, URL synchronization, and full accessibility"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Centralized Translation Catalog & Zero Inline Logic (Priority: P1)

As a multilingual user and developer, I want every visible text element, label, placeholder, tag, button, and status indicator across all playground tools to be served from a centralized, type-safe dictionary rather than inline conditional expressions, so that language switching is complete, consistent, and strictly maintainable.

**Why this priority**: Inline conditionals (`language === "en" ? ... : ...`) scattered throughout components cause missed translations, visual bugs (such as residual English or Tamil in the wrong view), and prevent scaling to additional locales. Centralizing all strings into a single translation schema guarantees 100% UI consistency.

**Independent Test**: Can be tested by loading the playground in both Tamil and English and verifying that 100% of visible strings, tool titles, descriptions, card tags, form inputs, dropzones, code comments, and buttons display in the chosen language with zero untranslated fragments.

**Acceptance Scenarios**:

1. **Given** the application is viewed in English (`en`), **When** browsing any tool or hub card, **Then** all labels, badges, action buttons, placeholders, and error messages are rendered in English from the centralized dictionary.
2. **Given** the application is viewed in Tamil (`ta`), **When** browsing any tool or hub card, **Then** all labels, badges, action buttons, placeholders, and error messages are rendered in classical/standard Tamil from the centralized dictionary.
3. **Given** the developer adds or modifies a translation key, **When** compiling TypeScript, **Then** static typing enforces that both `ta` and `en` definitions satisfy the `Translations` contract with zero missing keys.

---

### User Story 2 - Shareable Language State via URL Synchronization (Priority: P2)

As a user sharing a playground tool with colleagues, I want the language state to be reflected in the browser URL query parameter (e.g. `?lang=ta` or `?lang=en`) so that anyone opening the shared link automatically experiences the intended language without having to manually switch it.

**Why this priority**: Client-only storage (like `localStorage`) fails when URLs are shared across users or devices. URL parameter awareness provides shareability and bookmarkability while maintaining zero-backend static deployment.

**Independent Test**: Can be tested by navigating to `/?lang=ta` and verifying the app loads in Tamil, switching language to English and observing the URL updates to `/?lang=en` without page refresh, and reloading the page to confirm the URL preference takes precedence.

**Acceptance Scenarios**:

1. **Given** a user opens a link with `?lang=ta`, **When** the page initializes, **Then** the interface renders in Tamil, overriding device locale or prior local storage.
2. **Given** a user opens a link with `?lang=en`, **When** the page initializes, **Then** the interface renders in English, overriding device locale or prior local storage.
3. **Given** a user toggles the language switcher in the header, **When** the language changes, **Then** the URL query parameter updates smoothly via browser history API without triggering a full page reload or loss of active input state.
4. **Given** no `lang` query parameter is present in the URL, **When** the page initializes, **Then** the app falls back to `localStorage` preference, then browser language (`navigator.language`), and finally defaults to Tamil (`ta`).

---

### User Story 3 - Document Semantics, Titles, and Accessibility (Priority: P3)

As a user utilizing screen readers or assistive technology, I want the root HTML document language attribute (`<html lang="...">`), directional attribute, and document title (`document.title`) to dynamically reflect the selected language so that text-to-speech synthesizers use the correct phonetic rules and browser tabs are clearly identifiable.

**Why this priority**: When `<html lang>` does not match the content, assistive screen readers (TalkBack, VoiceOver, NVDA) pronounce Tamil text using Latin phoneme synthesis or fail to parse text clusters. Dynamic document title updates also improve tab accessibility.

**Independent Test**: Can be tested by switching languages and inspecting `document.documentElement.lang` and `document.title`, verifying that Tamil mode sets `lang="ta"` and updates the title to the Tamil platform name, while English mode sets `lang="en"` and updates the title to the English platform name.

**Acceptance Scenarios**:

1. **Given** the active language is Tamil (`ta`), **When** inspecting the DOM, **Then** `<html lang="ta">` is set and the browser tab title displays `"தமிழ் கருவிப் பட்டறை | Tamil Toolkit"`.
2. **Given** the active language is English (`en`), **When** inspecting the DOM, **Then** `<html lang="en">` is set and the browser tab title displays `"Tamil Toolkit Playground | WebAssembly Diagnostics"`.

---

### Edge Cases

- **Invalid Query Parameter**: When the URL contains an unrecognized language code (e.g., `?lang=fr` or `?lang=xyz`), the system falls back safely to stored preference or default without throwing errors.
- **Combined Query Parameters**: When the URL already contains existing parameters (e.g., tool presets or tab routing), toggling language preserves existing query parameters and only updates/adds the `lang` key.
- **Local Storage Disabled/Restricted**: When `localStorage` is blocked by private browsing security policies, the language provider falls back gracefully to in-memory state and URL parameters without crashing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a centralized TypeScript interface (`Translations`) defining all UI strings, labels, badges, options, tags, and status notices used across all views.
- **FR-002**: System MUST enforce 100% key parity between `ta` (Tamil) and `en` (English) dictionaries at compile time.
- **FR-003**: System MUST eliminate all hardcoded inline language conditionals (`language === "en" ? ... : ...`) from presentation components in favor of centralized translation keys.
- **FR-004**: System MUST read the initial language from the URL query parameter `?lang=` if present and valid (`ta` or `en`).
- **FR-005**: System MUST update the URL query parameter `lang` when the user switches language, using `window.history.replaceState` to avoid polluting the navigation history.
- **FR-006**: System MUST persist the selected language in browser local storage (`tt_playground_lang`) whenever it is explicitly toggled by the user.
- **FR-007**: System MUST update `document.documentElement.lang` whenever the active language changes.
- **FR-008**: System MUST update `document.title` to the appropriate localized title when the active language changes.
- **FR-009**: System MUST operate completely client-side with zero external network requests for translation assets or localization services.

### Key Entities

- **Language**: The active locale identifier, restricted to the literal union type `"ta" | "en"`.
- **Translations**: The comprehensive structured dictionary containing nested string records for navigation tabs, actions, common elements, and all tool-specific interfaces.
- **LanguageContext**: The React context providing the active `language`, the setter function `setLanguage`, and the localized `t` translations record to the component tree.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero occurrences of inline language conditional ternaries (`language === "..." ? ... : ...`) in presentation component JSX.
- **SC-002**: 100% of user-facing UI text elements across all 9 playground components adapt immediately upon language toggle without requiring page refresh.
- **SC-003**: Opening a shared URL with `?lang=ta` or `?lang=en` accurately loads the designated language in under 50 milliseconds without flicker.
- **SC-004**: TypeScript build (`tsc -b`) and playground test suite pass with zero errors, confirming full dictionary type coverage.
- **SC-005**: 100% client-side privacy preservation: 0 bytes of translation data or user interaction transmitted across the network.

## Assumptions

- The primary audience for the playground requires both native Tamil terminology (for cultural authenticity, linguists, and regional developers) and standard English technical terms (for global developers and cross-platform integrations).
- The application is a client-side WebAssembly single-page application, so URL query parameters (`?lang=ta`) are the standard, non-destructive mechanism for link sharing and state bookmarking without requiring server-side URL routing rules.
