/* eslint-disable @typescript-eslint/no-explicit-any */

export type BrowserTarget = "chrome" | "firefox";

declare const __BROWSER_TARGET__: BrowserTarget | undefined;

export const BROWSER_TARGET: BrowserTarget =
  typeof __BROWSER_TARGET__ !== "undefined"
    ? __BROWSER_TARGET__
    : typeof globalThis !== "undefined" && "browser" in globalThis && !("sidePanel" in ((globalThis as any).chrome ?? {}))
      ? "firefox"
      : "chrome";

export function getBrowserApi(): any {
  const g = globalThis as any;
  return g.browser ?? g.chrome;
}

export function isRestrictedUrl(url?: string): boolean {
  if (!url) return true;
  return (
    url.startsWith("chrome://") ||
    url.startsWith("chrome-extension://") ||
    url.startsWith("edge://") ||
    url.startsWith("about:") ||
    url.startsWith("moz-extension://") ||
    url.startsWith("https://chromewebstore.google.com") ||
    url.startsWith("https://chrome.google.com/webstore") ||
    url.startsWith("https://addons.mozilla.org")
  );
}

export function openSidePanelForTab(tabId?: number, windowId?: number): Promise<void> {
  const api = getBrowserApi();
  if (BROWSER_TARGET === "firefox" && api?.sidebarAction?.open) {
    // Must be called synchronously inside a user-gesture handler on Firefox
    return Promise.resolve(api.sidebarAction.open());
  }
  if (api?.sidePanel?.open) {
    if (typeof tabId === "number") {
      return Promise.resolve(api.sidePanel.open({ tabId }));
    }
    if (typeof windowId === "number") {
      return Promise.resolve(api.sidePanel.open({ windowId }));
    }
  }
  return Promise.resolve();
}

export async function setLiveBadge(tabId: number, enabled: boolean): Promise<void> {
  const api = getBrowserApi();
  if (!api?.action) return;
  await api.action.setBadgeText({ tabId, text: enabled ? "\u0BA4" : "" });
  if (enabled && api.action.setBadgeBackgroundColor) {
    const color = BROWSER_TARGET === "firefox" ? "#0060df" : "#1a73e8";
    await api.action.setBadgeBackgroundColor({ tabId, color });
  }
}

export function getUiLanguage(): "ta" | "en" {
  const api = getBrowserApi();
  const locale: string =
    (typeof api?.i18n?.getUILanguage === "function" ? api.i18n.getUILanguage() : undefined) ||
    (typeof navigator !== "undefined" ? navigator.language : "en") ||
    "en";
  return locale.toLowerCase().startsWith("ta") ? "ta" : "en";
}

export function getExtensionUrl(relPath: string): string {
  const api = getBrowserApi();
  return api?.runtime?.getURL ? api.runtime.getURL(relPath) : relPath;
}
