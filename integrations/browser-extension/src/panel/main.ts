import "../shared/theme/base.css";
import { BROWSER_TARGET, getBrowserApi } from "../shared/browser-api.js";
import { stringsFor } from "../shared/i18n.js";
import type { PanelTab, UiLang } from "../shared/messages.js";
import {
  consumeSelectionHandoff,
  getPreferences,
  getSiteRules,
  updatePreferences,
} from "../shared/storage.js";
import { mountDictionaryTab } from "./tabs/dictionary-tab.js";
import { mountFixTab } from "./tabs/fix-tab.js";
import { mountInspectTab } from "./tabs/inspect-tab.js";
import { mountLiveTab } from "./tabs/live-tab.js";
import { mountToolsTab } from "./tabs/tools-tab.js";

const api = getBrowserApi();

async function loadBrowserNativeTokens(): Promise<void> {
  if (BROWSER_TARGET === "firefox") {
    await import("../shared/theme/firefox-tokens.css");
    // Optional Firefox active theme sync (zero extra permissions)
    if (api?.theme?.getCurrent) {
      try {
        const theme = await api.theme.getCurrent();
        const colors = theme?.colors;
        const root = document.documentElement.style;
        if (colors?.sidebar) root.setProperty("--surface", colors.sidebar);
        if (colors?.sidebar_text) root.setProperty("--fg", colors.sidebar_text);
        if (colors?.sidebar_border) root.setProperty("--border", colors.sidebar_border);
        if (colors?.sidebar_highlight) root.setProperty("--accent", colors.sidebar_highlight);
      } catch {
        // Use Acorn/Proton defaults
      }
    }
  } else {
    await import("../shared/theme/chrome-tokens.css");
  }
}

async function getActiveTab(): Promise<{ id?: number; url?: string } | undefined> {
  const [tab] = (await api?.tabs?.query?.({ active: true, currentWindow: true })) ?? [];
  return tab;
}

async function bootstrap(): Promise<void> {
  await loadBrowserNativeTokens();
  const prefs = await getPreferences();
  let uiLang: UiLang = prefs.uiLang;
  let activeTab: PanelTab = prefs.lastTab;
  let showMicroCounter = prefs.showMicroCounter;

  const getStrings = () => stringsFor(uiLang);

  const inspectView = document.getElementById("view-inspect")!;
  const liveView = document.getElementById("view-live")!;
  const fixView = document.getElementById("view-fix")!;
  const dictionaryView = document.getElementById("view-dictionary")!;
  const toolsView = document.getElementById("view-tools")!;
  const drawerEl = document.getElementById("settings-drawer")!;

  const inspectTab = mountInspectTab(inspectView, {
    strings: getStrings,
    getActiveTabId: async () => (await getActiveTab())?.id,
  });
  const liveTab = mountLiveTab(liveView, {
    strings: getStrings,
    getActiveTab,
  });
  const fixTab = mountFixTab(fixView, {
    strings: getStrings,
    getActiveTabId: async () => (await getActiveTab())?.id,
  });
  const dictionaryTab = mountDictionaryTab(dictionaryView, {
    strings: getStrings,
    getActiveTabId: async () => (await getActiveTab())?.id,
  });
  const toolsTab = mountToolsTab(toolsView, {
    strings: getStrings,
    getActiveTab,
  });

  function applyChromeLabels(): void {
    const s = getStrings();
    document.getElementById("brand-title")!.textContent = s.brand;
    document.getElementById("lang-toggle")!.textContent = uiLang === "ta" ? "EN" : "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
    document.getElementById("tab-inspect")!.textContent = s.tabInspect;
    document.getElementById("tab-live")!.textContent = s.tabLive;
    document.getElementById("tab-fix")!.textContent = s.tabFix;
    document.getElementById("tab-dictionary")!.textContent = s.tabDictionary;
    document.getElementById("tab-tools")!.textContent = s.tabTools;
  }

  async function syncLiveStateToActiveTab(): Promise<void> {
    const tab = await getActiveTab();
    if (typeof tab?.id !== "number") return;
    const state = await api.runtime.sendMessage({ type: "GET_TAB_LIVE_STATE", tabId: tab.id });
    if (state?.ok && state.enabled) {
      await api.tabs
        .sendMessage(tab.id, {
          type: "TAB_SET_LIVE_STATE",
          enabled: true,
          layout: state.layout,
          uiLang,
          showMicroCounter,
          showConfirmToast: false,
        })
        .catch(() => undefined);
    }
  }

  async function renderSettingsDrawer(): Promise<void> {
    const s = getStrings();
    const rules = Object.values(await getSiteRules());
    drawerEl.innerHTML = `
      <div class="stack">
        <div class="row">
          <strong>${s.settingsTitle}</strong>
          <button class="btn sm" id="close-settings" type="button">\u2715</button>
        </div>
        <div class="row">
          <div>
            <div>${s.microCounterLabel}</div>
            <div class="muted">${s.microCounterDesc}</div>
          </div>
          <button class="btn sm ${showMicroCounter ? "primary" : ""}" id="toggle-micro" type="button">
            ${showMicroCounter ? "ON" : "OFF"}
          </button>
        </div>
        <div class="stack">
          <strong>${s.sitePermissionsTitle}</strong>
          ${
            rules.length === 0
              ? `<div class="muted">${s.noSitePermissions}</div>`
              : rules
                  .map(
                    (r) => `
                <div class="row">
                  <span style="font-size:12px">${r.originPattern.replace("/*", "")}</span>
                  <button class="btn sm revoke-site" data-origin="${r.originPattern}" type="button">${s.revoke}</button>
                </div>`
                  )
                  .join("")
          }
        </div>
      </div>
    `;

    drawerEl.querySelector("#close-settings")?.addEventListener("click", () => {
      drawerEl.classList.remove("open");
    });
    drawerEl.querySelector("#toggle-micro")?.addEventListener("click", async () => {
      showMicroCounter = !showMicroCounter;
      await updatePreferences({ showMicroCounter });
      await syncLiveStateToActiveTab();
      await renderSettingsDrawer();
    });
    drawerEl.querySelectorAll(".revoke-site").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const originPattern = (btn as HTMLElement).dataset.origin;
        if (!originPattern) return;
        await api.runtime.sendMessage({ type: "REVOKE_SITE_PERMISSIONS", originPattern });
        await renderSettingsDrawer();
        await liveTab.refresh();
        await toolsTab.refresh();
      });
    });
  }

  async function switchTab(tab: PanelTab): Promise<void> {
    activeTab = tab;
    await updatePreferences({ lastTab: tab });
    document.querySelectorAll(".tab-btn").forEach((b) => {
      b.classList.toggle("active", (b as HTMLElement).dataset.tab === tab);
    });
    inspectView.style.display = tab === "inspect" ? "flex" : "none";
    liveView.style.display = tab === "live" ? "flex" : "none";
    fixView.style.display = tab === "fix" ? "flex" : "none";
    dictionaryView.style.display = tab === "dictionary" ? "flex" : "none";
    toolsView.style.display = tab === "tools" ? "flex" : "none";

    if (tab === "inspect") await inspectTab.refresh();
    if (tab === "live") await liveTab.refresh();
    if (tab === "dictionary") await dictionaryTab.refresh();
    if (tab === "tools") await toolsTab.refresh();
  }

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      void switchTab((btn as HTMLElement).dataset.tab as PanelTab);
    });
  });

  document.getElementById("lang-toggle")?.addEventListener("click", async () => {
    uiLang = uiLang === "ta" ? "en" : "ta";
    await updatePreferences({ uiLang });
    await syncLiveStateToActiveTab();
    applyChromeLabels();
    inspectTab.rerenderLabels();
    liveTab.rerenderLabels();
    fixTab.rerenderLabels();
    dictionaryTab.rerenderLabels();
    toolsTab.rerenderLabels();
    if (drawerEl.classList.contains("open")) {
      await renderSettingsDrawer();
    }
  });

  document.getElementById("settings-toggle")?.addEventListener("click", async () => {
    drawerEl.classList.toggle("open");
    if (drawerEl.classList.contains("open")) {
      await renderSettingsDrawer();
    }
  });

  applyChromeLabels();

  // Handle cold-start right-click handoff (single-use)
  const handoff = await consumeSelectionHandoff();
  if (handoff) {
    if (handoff.action === "convert") {
      await switchTab("fix");
      await fixTab.loadHandoff(handoff.text, handoff.editable);
    } else {
      await switchTab("inspect");
      await inspectTab.refresh(handoff.text, handoff.editable);
    }
  } else {
    await switchTab(activeTab);
  }
}

void bootstrap();
