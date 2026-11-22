import { getBrowserApi, getUiLanguage } from "./browser-api.js";
import type {
  NumeralLocale,
  PanelTab,
  SelectionHandoffPayload,
  SortProfile,
  SupportedCurrency,
  TypingLayout,
  UiLang,
} from "./messages.js";

export interface UserPreferences {
  uiLang: UiLang;
  layout: TypingLayout;
  lastTab: PanelTab;
  numeralLocale: NumeralLocale;
  currency: SupportedCurrency;
  sortProfile: SortProfile;
  showMicroCounter: boolean;
}

export interface PerSitePermissionRecord {
  originPattern: string;
  alwaysOnLiveTyping: boolean;
  improveTamilFonts: boolean;
  updatedAt: number;
}

const PREFS_KEY = "prefs_v1";
const SITE_RULES_KEY = "site_rules_v1";
const HANDOFF_KEY = "handoff_latest";
const HANDOFF_TTL_MS = 60_000;

const VALID_LAYOUTS = new Set<TypingLayout>([
  "phonetic-v1",
  "tamil99",
  "anjal-phonetic",
  "suratha-bamini",
]);
const VALID_TABS = new Set<PanelTab>(["inspect", "live", "fix", "tools"]);
const VALID_SORT = new Set<SortProfile>(["agara-v1", "uyirmei-first-v1"]);
const ORIGIN_RE = /^https?:\/\/[^/*]+\/\*$/;

export function defaultPreferences(): UserPreferences {
  return {
    uiLang: getUiLanguage(),
    layout: "phonetic-v1",
    lastTab: "live",
    numeralLocale: "TN",
    currency: "INR",
    sortProfile: "agara-v1",
    showMicroCounter: true,
  };
}

function sanitizePrefs(raw: Partial<UserPreferences> | undefined): UserPreferences {
  const base = defaultPreferences();
  if (!raw || typeof raw !== "object") return base;
  return {
    uiLang: raw.uiLang === "ta" || raw.uiLang === "en" ? raw.uiLang : base.uiLang,
    layout: raw.layout && VALID_LAYOUTS.has(raw.layout) ? raw.layout : base.layout,
    lastTab: raw.lastTab && VALID_TABS.has(raw.lastTab) ? raw.lastTab : base.lastTab,
    numeralLocale: raw.numeralLocale === "SL" ? "SL" : "TN",
    currency: raw.currency === "LKR" ? "LKR" : "INR",
    sortProfile: raw.sortProfile && VALID_SORT.has(raw.sortProfile) ? raw.sortProfile : base.sortProfile,
    showMicroCounter: typeof raw.showMicroCounter === "boolean" ? raw.showMicroCounter : base.showMicroCounter,
  };
}

export function originPatternFromUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") return null;
    const pattern = `${parsed.protocol}//${parsed.hostname}/*`;
    return ORIGIN_RE.test(pattern) ? pattern : null;
  } catch {
    return null;
  }
}

export function isValidSingleOriginPattern(pattern: string): boolean {
  return ORIGIN_RE.test(pattern);
}

export async function getPreferences(): Promise<UserPreferences> {
  const api = getBrowserApi();
  if (!api?.storage?.local) return defaultPreferences();
  const data = await api.storage.local.get(PREFS_KEY);
  return sanitizePrefs(data?.[PREFS_KEY]);
}

export async function updatePreferences(patch: Partial<UserPreferences>): Promise<UserPreferences> {
  const current = await getPreferences();
  const next = sanitizePrefs({ ...current, ...patch });
  const api = getBrowserApi();
  if (api?.storage?.local) {
    await api.storage.local.set({ [PREFS_KEY]: next });
  }
  return next;
}

export async function getSiteRules(): Promise<Record<string, PerSitePermissionRecord>> {
  const api = getBrowserApi();
  if (!api?.storage?.local) return {};
  const data = await api.storage.local.get(SITE_RULES_KEY);
  const rules = (data?.[SITE_RULES_KEY] ?? {}) as Record<string, PerSitePermissionRecord>;
  return rules;
}

export async function upsertSiteRule(
  originPattern: string,
  patch: Partial<Pick<PerSitePermissionRecord, "alwaysOnLiveTyping" | "improveTamilFonts">>
): Promise<PerSitePermissionRecord | null> {
  if (!isValidSingleOriginPattern(originPattern)) {
    throw new Error(`Invalid single-origin pattern: ${originPattern}`);
  }
  const rules = await getSiteRules();
  const prev = rules[originPattern] ?? {
    originPattern,
    alwaysOnLiveTyping: false,
    improveTamilFonts: false,
    updatedAt: Date.now(),
  };
  const next: PerSitePermissionRecord = {
    originPattern,
    alwaysOnLiveTyping: patch.alwaysOnLiveTyping ?? prev.alwaysOnLiveTyping,
    improveTamilFonts: patch.improveTamilFonts ?? prev.improveTamilFonts,
    updatedAt: Date.now(),
  };

  if (!next.alwaysOnLiveTyping && !next.improveTamilFonts) {
    delete rules[originPattern];
  } else {
    rules[originPattern] = next;
  }

  const api = getBrowserApi();
  if (api?.storage?.local) {
    await api.storage.local.set({ [SITE_RULES_KEY]: rules });
  }
  return rules[originPattern] ?? null;
}

export async function removeSiteRule(originPattern: string): Promise<void> {
  const rules = await getSiteRules();
  delete rules[originPattern];
  const api = getBrowserApi();
  if (api?.storage?.local) {
    await api.storage.local.set({ [SITE_RULES_KEY]: rules });
  }
}

export async function reconcileSiteRulesWithPermissions(): Promise<Record<string, PerSitePermissionRecord>> {
  const api = getBrowserApi();
  const rules = await getSiteRules();
  if (!api?.permissions?.getAll) return rules;
  const granted = await api.permissions.getAll();
  const grantedOrigins = new Set<string>(granted?.origins ?? []);
  let changed = false;
  for (const originPattern of Object.keys(rules)) {
    if (!grantedOrigins.has(originPattern)) {
      delete rules[originPattern];
      changed = true;
    }
  }
  if (changed && api?.storage?.local) {
    await api.storage.local.set({ [SITE_RULES_KEY]: rules });
  }
  return rules;
}

export async function setSelectionHandoff(payload: SelectionHandoffPayload): Promise<void> {
  const api = getBrowserApi();
  const store = api?.storage?.session ?? api?.storage?.local;
  if (!store) return;
  await store.set({ [HANDOFF_KEY]: payload });
}

export async function consumeSelectionHandoff(): Promise<SelectionHandoffPayload | null> {
  const api = getBrowserApi();
  const store = api?.storage?.session ?? api?.storage?.local;
  if (!store) return null;
  const data = await store.get(HANDOFF_KEY);
  const payload = data?.[HANDOFF_KEY] as SelectionHandoffPayload | undefined;
  if (!payload) return null;
  await store.remove(HANDOFF_KEY);
  if (Date.now() - payload.createdAt > HANDOFF_TTL_MS) {
    return null;
  }
  return payload;
}
