import { getBrowserApi, getExtensionUrl } from "../shared/browser-api.js";
import { getSiteRules, removeSiteRule, upsertSiteRule } from "../shared/storage.js";

const FONT_CSS_CACHE = new Map<string, string>();

export function buildTamilFontFixCss(): string {
  const cached = FONT_CSS_CACHE.get("default");
  if (cached) return cached;

  const noto400 = getExtensionUrl("fonts/noto-sans-tamil-tamil-400-normal.woff2");
  const noto500 = getExtensionUrl("fonts/noto-sans-tamil-tamil-500-normal.woff2");
  const noto600 = getExtensionUrl("fonts/noto-sans-tamil-tamil-600-normal.woff2");
  const supp400 = getExtensionUrl("fonts/noto-sans-tamil-supplement-tamil-supplement-400-normal.woff2");

  const css = `
@font-face {
  font-family: "TamilToolkitNoto";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("${noto400}") format("woff2");
  unicode-range: U+0964-0965, U+0B82-0BFA, U+200C-200D, U+20B9, U+25CC;
}
@font-face {
  font-family: "TamilToolkitNoto";
  font-style: normal;
  font-weight: 500;
  font-display: swap;
  src: url("${noto500}") format("woff2");
  unicode-range: U+0964-0965, U+0B82-0BFA, U+200C-200D, U+20B9, U+25CC;
}
@font-face {
  font-family: "TamilToolkitNoto";
  font-style: normal;
  font-weight: 600;
  font-display: swap;
  src: url("${noto600}") format("woff2");
  unicode-range: U+0964-0965, U+0B82-0BFA, U+200C-200D, U+20B9, U+25CC;
}
@font-face {
  font-family: "TamilToolkitNotoSupplement";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("${supp400}") format("woff2");
  unicode-range: U+11FC0-11FFF;
}
:lang(ta):not(input):not(textarea):not([contenteditable="true"]):not([contenteditable=""]) {
  font-family: "TamilToolkitNoto", "TamilToolkitNotoSupplement", inherit !important;
}
`;
  FONT_CSS_CACHE.set("default", css);
  return css;
}

export async function applyFontFixToTab(tabId: number): Promise<void> {
  const api = getBrowserApi();
  if (!api?.scripting?.insertCSS) return;
  await api.scripting.insertCSS({
    target: { tabId },
    css: buildTamilFontFixCss(),
  });
}

export async function removeFontFixFromTab(tabId: number): Promise<void> {
  const api = getBrowserApi();
  if (!api?.scripting?.removeCSS) return;
  try {
    await api.scripting.removeCSS({
      target: { tabId },
      css: buildTamilFontFixCss(),
    });
  } catch {
    // Tab may have navigated or CSS may not be present
  }
}

export async function setSiteFontFix(
  originPattern: string,
  enabled: boolean,
  tabId?: number
): Promise<boolean> {
  const api = getBrowserApi();
  if (enabled) {
    const hasPerm = api?.permissions?.contains
      ? await api.permissions.contains({ origins: [originPattern] })
      : true;
    if (!hasPerm) return false;
    await upsertSiteRule(originPattern, { improveTamilFonts: true });
    if (typeof tabId === "number") {
      await applyFontFixToTab(tabId);
    }
    return true;
  }

  if (typeof tabId === "number") {
    await removeFontFixFromTab(tabId);
  }
  const remaining = await upsertSiteRule(originPattern, { improveTamilFonts: false });
  if (!remaining && api?.permissions?.remove) {
    try {
      await api.permissions.remove({ origins: [originPattern] });
    } catch {
      // Ignore if already revoked
    }
  }
  return true;
}

export async function revokeOriginPermissions(originPattern: string): Promise<void> {
  const api = getBrowserApi();
  const tabs = (await api?.tabs?.query?.({ url: originPattern })) ?? [];
  for (const tab of tabs) {
    if (typeof tab.id === "number") {
      await removeFontFixFromTab(tab.id);
    }
  }
  await removeSiteRule(originPattern);
  const scriptId = siteScriptId(originPattern);
  if (api?.scripting?.unregisterContentScripts) {
    try {
      await api.scripting.unregisterContentScripts({ ids: [scriptId] });
    } catch {
      // Not registered
    }
  }
  if (api?.permissions?.remove) {
    try {
      await api.permissions.remove({ origins: [originPattern] });
    } catch {
      // Already revoked
    }
  }
}

export function siteScriptId(originPattern: string): string {
  return `tt-live-${originPattern.replace(/[^a-z0-9]/gi, "_").slice(0, 48)}`;
}

export async function syncDynamicSiteScripts(): Promise<void> {
  const api = getBrowserApi();
  if (!api?.scripting?.registerContentScripts) return;
  const rules = await getSiteRules();
  for (const rule of Object.values(rules)) {
    const id = siteScriptId(rule.originPattern);
    if (rule.alwaysOnLiveTyping) {
      try {
        await api.scripting.unregisterContentScripts({ ids: [id] });
      } catch {
        // Ignore if not previously registered
      }
      try {
        await api.scripting.registerContentScripts([
          {
            id,
            matches: [rule.originPattern],
            js: ["content.js"],
            runAt: "document_idle",
          },
        ]);
      } catch {
        // Origin permission may have been revoked externally
      }
    }
  }
}
