# Contract: i18n Translation & URL State Interface

## 1. Module Exports (`playground/src/lib/i18n.ts`)

```typescript
export type Language = "ta" | "en";
export interface Translations { ... }
export const translations: Record<Language, Translations>;
export function LanguageProvider({ children }: { children: React.ReactNode }): React.ReactElement;
export function useLanguage(): LanguageContextType;
```

## 2. URL Query State Contract
- Key: `lang`
- Accepted Values: `"ta"` | `"en"`
- Behavior on unrecognized value: ignored, falls back to storage/system default.
- Updating behavior: `window.history.replaceState(null, "", url.toString())` preserves pathname, hash, and other search parameters.

## 3. DOM Semantics Contract
- `document.documentElement.lang`: dynamically synchronizes to `"ta"` or `"en"`.
- `document.documentElement.dir`: `"ltr"`.
- `document.title`:
  - `ta`: `"தமிழ் கருவிப் பட்டறை | Tamil Toolkit"`
  - `en`: `"Tamil Toolkit Playground | WebAssembly Diagnostics"`
