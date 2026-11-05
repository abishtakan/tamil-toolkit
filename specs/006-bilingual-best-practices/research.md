# Research: Bilingual Architecture & Internationalization Best Practices

## Decision 1: Centralized Type-Safe Dictionary vs Inline Conditionals
- **Decision**: Define a single exhaustive `Translations` interface in `playground/src/lib/i18n.ts` and define both `ta` and `en` records conforming strictly to it. Remove all `language === "en" ? ... : ...` expressions from JSX.
- **Rationale**:
  - Eliminates visual inconsistencies where parts of a screen show Tamil in English mode or vice versa.
  - Compile-time guarantee: any newly introduced string must be defined for both `ta` and `en`; otherwise TypeScript `tsc -b` fails during build.
  - Clean separation between presentation logic and locale content.
- **Alternatives Considered**:
  - *Third-party i18next/react-intl*: Introduces extra dependency bundle weight and runtime overhead for a 2-language lightweight WebAssembly playground where typed object dictionaries are zero-overhead and instantly tree-shakeable.
  - *Leaving inline ternaries*: High cognitive load, breaks modularity, and prone to regressions.

## Decision 2: State Hydration & URL Synchronization Waterfall
- **Decision**: Implement a 4-tier language resolution hierarchy:
  1. URL search parameter `?lang=ta` or `?lang=en` (takes precedence on page load).
  2. Local storage (`tt_playground_lang`).
  3. Browser system language (`navigator.language.startsWith("ta")`).
  4. Default locale: `ta` (as this is a Tamil-centric toolkit).
  On user toggle:
  - Update React state (`language`).
  - Persist to `localStorage.setItem("tt_playground_lang", lang)`.
  - Update browser URL via `window.history.replaceState` preserving all other query parameters without full page reload.
  - Set `document.documentElement.lang = lang` and `document.documentElement.dir = "ltr"`.
  - Update `document.title` to the localized platform title.
- **Rationale**:
  - Provides instant shareability (e.g. sharing `https://domain.com/playground?lang=ta` guarantees the recipient sees Tamil).
  - Preserves user preference across visits.
  - Avoids polluting browser history stack with repeated language toggles.
- **Alternatives Considered**:
  - *Path-based routing (`/ta/`, `/en/`)*: Requires client-side router (like react-router) or multi-page build configuration. For the playground SPA, URL query parameters provide 100% of the shareability benefits without routing rewrite overhead.

## Decision 3: Document Semantics and Accessibility
- **Decision**: Ensure that when `language` changes, `document.documentElement.lang` immediately reflects `"ta"` or `"en"`, and `<title>` changes to match the locale.
- **Rationale**:
  - Assistive technology and screen readers (NVDA, TalkBack, VoiceOver) read the `lang` attribute to switch phonetic pronunciation dictionaries.
  - Clear tab recognition for users with multiple browser tabs.
