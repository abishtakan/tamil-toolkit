import {
  BROWSER_TARGET,
  getBrowserApi,
  isRestrictedUrl,
  openSidePanelForTab,
  setLiveBadge,
} from "../shared/browser-api.js";
import type { RuntimeRequest, TypingLayout } from "../shared/messages.js";
import {
  getPreferences,
  getSiteRules,
  originPatternFromUrl,
  reconcileSiteRulesWithPermissions,
  setSelectionHandoff,
  updatePreferences,
  upsertSiteRule,
} from "../shared/storage.js";
import { inspectText } from "../engine/inspect.js";
import {
  convertLegacyToUnicode,
  convertNumberToWords,
  getCivilDateAndHolidays,
  initTamilEngine,
  repairTamil,
  sortLines,
  transliterateToTamil,
} from "../engine/tamil-engine.js";
import {
  applyFontFixToTab,
  revokeOriginPermissions,
  setSiteFontFix,
  siteScriptId,
  syncDynamicSiteScripts,
} from "./font-fixer.js";

const api = getBrowserApi();
const tabLiveEnabled = new Map<number, boolean>();

const MENU_COPY_REPAIRED = "tt-copy-repaired";
const MENU_REPAIR_REPLACE = "tt-repair-replace";
const MENU_CONVERT_SELECTION = "tt-convert-selection";
const MENU_INSPECT_SELECTION = "tt-inspect-selection";
const MENU_OPEN_PANEL = "tt-open-panel";

async function ensureContentScriptInjected(tabId: number): Promise<boolean> {
  try {
    await api.tabs.sendMessage(tabId, { type: "PING_CONTENT" });
    return true;
  } catch {
    try {
      await api.scripting.executeScript({
        target: { tabId },
        files: ["content.js"],
      });
      return true;
    } catch {
      return false;
    }
  }
}

async function copyTextSilently(text: string): Promise<boolean> {
  if (BROWSER_TARGET === "firefox" && typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  }

  if (api?.offscreen?.createDocument) {
    try {
      const hasDoc = api.offscreen.hasDocument ? await api.offscreen.hasDocument() : false;
      if (!hasDoc) {
        await api.offscreen.createDocument({
          url: "offscreen.html",
          reasons: ["CLIPBOARD"],
          justification: "Silent plain-text copy of repaired Tamil text on right-click.",
        });
      }
      const res = await api.runtime.sendMessage({ type: "OFFSCREEN_COPY_TEXT", text });
      return Boolean(res?.ok);
    } catch {
      return false;
    }
  }
  return false;
}

async function setTabLiveState(
  tabId: number,
  enabled: boolean,
  options: { layout?: TypingLayout; showConfirmToast?: boolean } = {}
): Promise<boolean> {
  const prefs = options.layout
    ? await updatePreferences({ layout: options.layout })
    : await getPreferences();

  tabLiveEnabled.set(tabId, enabled);
  await setLiveBadge(tabId, enabled);

  const injected = await ensureContentScriptInjected(tabId);
  if (!injected) return false;

  try {
    await api.tabs.sendMessage(tabId, {
      type: "TAB_SET_LIVE_STATE",
      enabled,
      layout: prefs.layout,
      uiLang: prefs.uiLang,
      showMicroCounter: prefs.showMicroCounter,
      showConfirmToast: options.showConfirmToast ?? true,
    });
    return true;
  } catch {
    return false;
  }
}

async function toggleActiveTabLiveTyping(tab?: { id?: number; url?: string; windowId?: number }): Promise<void> {
  let targetTab = tab;
  if (!targetTab?.id) {
    const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
    targetTab = active;
  }
  if (!targetTab?.id) return;

  if (isRestrictedUrl(targetTab.url)) {
    await openSidePanelForTab(targetTab.id, targetTab.windowId);
    return;
  }

  const next = !(tabLiveEnabled.get(targetTab.id) ?? false);
  await setTabLiveState(targetTab.id, next, { showConfirmToast: true });
}

function registerContextMenus(): void {
  if (!api?.contextMenus) return;
  api.contextMenus.removeAll(() => {
    api.contextMenus.create({
      id: MENU_COPY_REPAIRED,
      title: "Copy repaired Tamil / \u0B9A\u0BC0\u0BB0\u0BAE\u0BC8\u0BA4\u0BCD\u0BA4 \u0BA4\u0BAE\u0BBF\u0BB4\u0BC8 \u0BA8\u0B95\u0BB2\u0BC6\u0B9F\u0BC1",
      contexts: ["selection"],
    });
    api.contextMenus.create({
      id: MENU_REPAIR_REPLACE,
      title: "Repair & replace in place / \u0B89\u0B9F\u0BA9\u0BC7 \u0B9A\u0BC0\u0BB0\u0BAE\u0BC8\u0BA4\u0BCD\u0BA4\u0BC1 \u0BAE\u0BBE\u0BB1\u0BCD\u0BB1\u0BC1",
      contexts: ["editable"],
    });
    api.contextMenus.create({
      id: MENU_CONVERT_SELECTION,
      title: "Convert to Tamil\u2026 / \u0BA4\u0BAE\u0BBF\u0BB4\u0BBE\u0B95 \u0BAE\u0BBE\u0BB1\u0BCD\u0BB1\u0BC1\u2026",
      contexts: ["selection"],
    });
    api.contextMenus.create({
      id: MENU_INSPECT_SELECTION,
      title: "Inspect Tamil text / \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0B89\u0BB0\u0BC8 \u0B86\u0BAF\u0BCD\u0BB5\u0BC1",
      contexts: ["selection"],
    });
    api.contextMenus.create({
      id: MENU_OPEN_PANEL,
      title: "Open Tamil Toolkit panel / \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD \u0B95\u0BB0\u0BC1\u0BB5\u0BBF\u0BAA\u0BCD \u0BAA\u0B95\u0BCD\u0B95\u0BAE\u0BCD",
      contexts: ["action", "page"],
    });
  });
}

if (api?.runtime?.onInstalled) {
  api.runtime.onInstalled.addListener(() => {
    registerContextMenus();
    void reconcileSiteRulesWithPermissions().then(syncDynamicSiteScripts);
  });
}

if (api?.runtime?.onStartup) {
  api.runtime.onStartup.addListener(() => {
    void reconcileSiteRulesWithPermissions().then(syncDynamicSiteScripts);
  });
}

if (api?.action?.onClicked) {
  api.action.onClicked.addListener((tab: { id?: number; url?: string; windowId?: number }) => {
    if (isRestrictedUrl(tab?.url)) {
      // Synchronous call for Firefox user-gesture compliance
      void openSidePanelForTab(tab?.id, tab?.windowId);
      return;
    }
    void toggleActiveTabLiveTyping(tab);
  });
}

if (api?.commands?.onCommand) {
  api.commands.onCommand.addListener((command: string) => {
    if (command === "toggle-live-typing") {
      void toggleActiveTabLiveTyping();
    }
  });
}

if (api?.contextMenus?.onClicked) {
  api.contextMenus.onClicked.addListener((info: any, tab: any) => {
    const selectedText = typeof info.selectionText === "string" ? info.selectionText : "";
    const editable = Boolean(info.editable);

    if (info.menuItemId === MENU_OPEN_PANEL) {
      void openSidePanelForTab(tab?.id, tab?.windowId);
      return;
    }

    if (info.menuItemId === MENU_CONVERT_SELECTION || info.menuItemId === MENU_INSPECT_SELECTION) {
      // Call openSidePanelForTab synchronously inside the gesture handler (Firefox requirement)
      void openSidePanelForTab(tab?.id, tab?.windowId);
      const action = info.menuItemId === MENU_CONVERT_SELECTION ? "convert" : "inspect";
      void setSelectionHandoff({
        requestId: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        tabId: tab?.id ?? -1,
        action,
        text: selectedText,
        editable,
        createdAt: Date.now(),
      });
      return;
    }

    if (info.menuItemId === MENU_REPAIR_REPLACE && typeof tab?.id === "number") {
      void (async () => {
        const injected = await ensureContentScriptInjected(tab.id);
        if (!injected) return;
        await initTamilEngine();
        if (selectedText) {
          const repaired = repairTamil(selectedText).text;
          await api.tabs.sendMessage(tab.id, {
            type: "TAB_REPLACE_TEXT",
            text: repaired,
            scope: "selection",
          });
          return;
        }
        const ctxRes = await api.tabs.sendMessage(tab.id, { type: "TAB_GET_CONTEXT_TEXT", mode: "auto" });
        if (ctxRes?.ok && typeof ctxRes.text === "string" && ctxRes.text.length > 0 && ctxRes.editable) {
          const repaired = repairTamil(ctxRes.text).text;
          await api.tabs.sendMessage(tab.id, {
            type: "TAB_REPLACE_TEXT",
            text: repaired,
            scope: "active-editor",
          });
        }
      })();
      return;
    }

    if (info.menuItemId === MENU_COPY_REPAIRED && selectedText) {
      void (async () => {
        await initTamilEngine();
        const repaired = repairTamil(selectedText).text;
        await copyTextSilently(repaired);
      })();
    }
  });
}

if (api?.tabs?.onUpdated) {
  api.tabs.onUpdated.addListener((tabId: number, changeInfo: { status?: string }, tab: { url?: string }) => {
    if (changeInfo.status !== "complete" || !tab?.url) return;
    const originPattern = originPatternFromUrl(tab.url);
    if (!originPattern) return;
    void (async () => {
      const rules = await getSiteRules();
      const rule = rules[originPattern];
      if (!rule) return;
      if (rule.improveTamilFonts) {
        await applyFontFixToTab(tabId);
      }
      if (rule.alwaysOnLiveTyping) {
        await setTabLiveState(tabId, true, { showConfirmToast: false });
      }
    })();
  });
}

if (api?.tabs?.onRemoved) {
  api.tabs.onRemoved.addListener((tabId: number) => {
    tabLiveEnabled.delete(tabId);
  });
}

async function handleMessage(msg: RuntimeRequest, sender: any): Promise<unknown> {
  switch (msg.type) {
    case "ENGINE_TRANSLITERATE": {
      await initTamilEngine();
      return { ok: true, output: transliterateToTamil(msg.text, msg.scheme) };
    }
    case "ENGINE_INSPECT": {
      await initTamilEngine();
      return { ok: true, snapshot: inspectText(msg.text, msg.source, msg.editable) };
    }
    case "ENGINE_REPAIR": {
      await initTamilEngine();
      const res = repairTamil(msg.text);
      return { ok: true, text: res.text, diagnostics: res.diagnostics };
    }
    case "ENGINE_DETECT_AND_CONVERT": {
      await initTamilEngine();
      const res = convertLegacyToUnicode(msg.text, msg.encoding);
      return { ok: true, ...res };
    }
    case "ENGINE_SORT_LINES": {
      await initTamilEngine();
      return { ok: true, text: sortLines(msg.text, msg.profile) };
    }
    case "ENGINE_NUMERAL_WORDS": {
      await initTamilEngine();
      const res = convertNumberToWords(msg.amount, msg.locale, msg.currency);
      return { ok: true, ...res };
    }
    case "ENGINE_DATE_AND_HOLIDAYS": {
      await initTamilEngine();
      const res = getCivilDateAndHolidays(msg.year, msg.month, msg.day, msg.jurisdiction);
      return { ok: true, ...res };
    }
    case "OPEN_SIDE_PANEL": {
      const tabId = sender?.tab?.id;
      const windowId = sender?.tab?.windowId;
      if (msg.handoff) {
        await setSelectionHandoff(msg.handoff);
      } else if (msg.tab) {
        await updatePreferences({ lastTab: msg.tab });
      }
      await openSidePanelForTab(tabId, windowId);
      return { ok: true };
    }
    case "TOGGLE_LIVE_TYPING": {
      let tabId = msg.tabId ?? sender?.tab?.id;
      if (typeof tabId !== "number") {
        const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
        tabId = active?.id;
      }
      if (typeof tabId !== "number") {
        return { ok: false, error: "No active tab found." };
      }
      const nextEnabled = typeof msg.enabled === "boolean" ? msg.enabled : !(tabLiveEnabled.get(tabId) ?? false);
      await setTabLiveState(tabId, nextEnabled, {
        layout: msg.layout,
        showConfirmToast: false,
      });
      const prefs = await getPreferences();
      return { ok: true, enabled: nextEnabled, layout: prefs.layout };
    }
    case "GET_TAB_LIVE_STATE": {
      let tabId = msg.tabId ?? sender?.tab?.id;
      if (typeof tabId !== "number") {
        const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
        tabId = active?.id;
      }
      const prefs = await getPreferences();
      return {
        ok: true,
        enabled: typeof tabId === "number" ? (tabLiveEnabled.get(tabId) ?? false) : false,
        layout: prefs.layout,
      };
    }
    case "SET_SITE_ALWAYS_ON": {
      if (msg.enabled) {
        const hasPerm = api?.permissions?.contains
          ? await api.permissions.contains({ origins: [msg.originPattern] })
          : true;
        if (!hasPerm) return { ok: false, error: "Site permission not granted." };
        await upsertSiteRule(msg.originPattern, { alwaysOnLiveTyping: true });
        await syncDynamicSiteScripts();
        return { ok: true, enabled: true };
      }
      const remaining = await upsertSiteRule(msg.originPattern, { alwaysOnLiveTyping: false });
      try {
        await api.scripting.unregisterContentScripts({ ids: [siteScriptId(msg.originPattern)] });
      } catch {
        // Ignore if not registered
      }
      if (!remaining && api?.permissions?.remove) {
        try {
          await api.permissions.remove({ origins: [msg.originPattern] });
        } catch {
          // Ignore
        }
      }
      return { ok: true, enabled: false };
    }
    case "SET_SITE_FONT_FIX": {
      const ok = await setSiteFontFix(msg.originPattern, msg.enabled, msg.tabId);
      return { ok, enabled: msg.enabled && ok };
    }
    case "REVOKE_SITE_PERMISSIONS": {
      await revokeOriginPermissions(msg.originPattern);
      return { ok: true };
    }
    case "PANEL_GET_TAB_CONTEXT_TEXT": {
      let tabId = msg.tabId;
      let tabUrl: string | undefined;
      if (typeof tabId !== "number") {
        const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
        tabId = active?.id;
        tabUrl = active?.url;
      } else {
        const tab = await api.tabs.get(tabId).catch(() => undefined);
        tabUrl = tab?.url;
      }
      if (typeof tabId !== "number" || isRestrictedUrl(tabUrl)) {
        return { ok: false, restricted: true, error: "Cannot inspect browser-restricted pages." };
      }
      const injected = await ensureContentScriptInjected(tabId);
      if (!injected) {
        return { ok: false, restricted: true, error: "Unable to connect to the active page." };
      }
      return await api.tabs.sendMessage(tabId, { type: "TAB_GET_CONTEXT_TEXT", mode: msg.mode });
    }
    case "PANEL_REPLACE_TAB_TEXT": {
      let tabId = msg.tabId;
      if (typeof tabId !== "number") {
        const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
        tabId = active?.id;
      }
      if (typeof tabId !== "number") return { ok: false, replaced: false };
      const injected = await ensureContentScriptInjected(tabId);
      if (!injected) return { ok: false, replaced: false };
      return await api.tabs.sendMessage(tabId, {
        type: "TAB_REPLACE_TEXT",
        text: msg.text,
        scope: msg.scope,
      });
    }
    case "PANEL_INSERT_TAB_TEXT": {
      let tabId = msg.tabId;
      if (typeof tabId !== "number") {
        const [active] = (await api.tabs.query({ active: true, currentWindow: true })) ?? [];
        tabId = active?.id;
      }
      if (typeof tabId !== "number") return { ok: false, inserted: false };
      const injected = await ensureContentScriptInjected(tabId);
      if (!injected) return { ok: false, inserted: false };
      return await api.tabs.sendMessage(tabId, {
        type: "TAB_INSERT_TEXT",
        text: msg.text,
      });
    }
    default:
      return undefined;
  }
}

const HANDLED_BACKGROUND_TYPES = new Set<string>([
  "ENGINE_TRANSLITERATE",
  "ENGINE_INSPECT",
  "ENGINE_REPAIR",
  "ENGINE_DETECT_AND_CONVERT",
  "ENGINE_SORT_LINES",
  "ENGINE_NUMERAL_WORDS",
  "ENGINE_DATE_AND_HOLIDAYS",
  "OPEN_SIDE_PANEL",
  "TOGGLE_LIVE_TYPING",
  "GET_TAB_LIVE_STATE",
  "SET_SITE_ALWAYS_ON",
  "SET_SITE_FONT_FIX",
  "REVOKE_SITE_PERMISSIONS",
  "PANEL_GET_TAB_CONTEXT_TEXT",
  "PANEL_REPLACE_TAB_TEXT",
  "PANEL_INSERT_TAB_TEXT",
]);

if (api?.runtime?.onMessage) {
  api.runtime.onMessage.addListener((msg: RuntimeRequest, sender: any, sendResponse: (res: unknown) => void) => {
    if (!msg || typeof msg.type !== "string" || !HANDLED_BACKGROUND_TYPES.has(msg.type)) {
      return false;
    }
    void handleMessage(msg, sender)
      .then((res) => {
        sendResponse(res ?? { ok: false, error: "Empty response." });
      })
      .catch((err) => {
        sendResponse({ ok: false, error: err instanceof Error ? err.message : String(err) });
      });
    return true;
  });
}
