import "../shared/theme/base.css";
import {
  BROWSER_TARGET,
  getBrowserApi,
  isRestrictedUrl,
  openSidePanelForTab,
} from "../shared/browser-api.js";
import { stringsFor } from "../shared/i18n.js";
import type { TypingLayout, UiLang } from "../shared/messages.js";
import { getPreferences, updatePreferences } from "../shared/storage.js";

const api = getBrowserApi();

async function loadTheme(): Promise<void> {
  if (BROWSER_TARGET === "firefox") {
    await import("../shared/theme/firefox-tokens.css");
  } else {
    await import("../shared/theme/chrome-tokens.css");
  }
}

async function bootstrap(): Promise<void> {
  await loadTheme();
  const prefs = await getPreferences();
  let uiLang: UiLang = prefs.uiLang;
  let layout: TypingLayout = prefs.layout;
  let liveEnabled = false;

  const [activeTab] = (await api?.tabs?.query?.({ active: true, currentWindow: true })) ?? [];
  const restricted = isRestrictedUrl(activeTab?.url);

  if (!restricted && typeof activeTab?.id === "number") {
    const state = await api.runtime
      .sendMessage({ type: "GET_TAB_LIVE_STATE", tabId: activeTab.id })
      .catch(() => null);
    if (state?.ok) {
      liveEnabled = Boolean(state.enabled);
    }
  }

  const brandEl = document.getElementById("pop-brand")!;
  const langBtn = document.getElementById("pop-lang") as HTMLButtonElement;
  const liveTitleEl = document.getElementById("pop-live-title")!;
  const liveDescEl = document.getElementById("pop-live-desc")!;
  const liveBtn = document.getElementById("pop-live-btn") as HTMLButtonElement;
  const layoutLbl = document.getElementById("pop-layout-lbl")!;
  const layoutSel = document.getElementById("pop-layout") as HTMLSelectElement;
  const openPanelBtn = document.getElementById("pop-open-panel") as HTMLButtonElement;

  function render(): void {
    const s = stringsFor(uiLang);
    brandEl.textContent = s.brand;
    langBtn.textContent = uiLang === "ta" ? "EN" : "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
    liveTitleEl.textContent = s.liveTypingLabel;
    liveDescEl.textContent = restricted
      ? uiLang === "ta"
        ? "\u0B87\u0BA8\u0BCD\u0BA4 \u0BAA\u0B95\u0BCD\u0B95\u0BA4\u0BCD\u0BA4\u0BBF\u0BB2\u0BCD \u0BA8\u0BC7\u0BB0\u0B9F\u0BBF \u0BA4\u0B9F\u0BCD\u0B9F\u0B9A\u0BCD\u0B9A\u0BC1 \u0B87\u0BB2\u0BCD\u0BB2\u0BC8"
        : "Unavailable on browser-restricted page"
      : "Alt+Shift+L";
    liveBtn.disabled = restricted;
    liveBtn.textContent = liveEnabled ? "ON" : "OFF";
    liveBtn.classList.toggle("primary", liveEnabled);
    layoutLbl.textContent = s.layoutLabel;
    layoutSel.value = layout;
    openPanelBtn.textContent =
      uiLang === "ta"
        ? "\u0BAA\u0B95\u0BCD\u0B95\u0BAA\u0BCD \u0BAA\u0B95\u0BC1\u0BA4\u0BBF\u0BAF\u0BC8\u0BA4\u0BCD \u0BA4\u0BBF\u0BB1 (\u0B86\u0BAF\u0BCD\u0BB5\u0BC1 \u00B7 \u0B9A\u0BC0\u0BB0\u0BAE\u0BC8 \u00B7 \u0B95\u0BB0\u0BC1\u0BB5\u0BBF\u0B95\u0BB3\u0BCD)"
        : "Open Side Panel (Inspect \u00B7 Fix \u00B7 Tools)";
  }

  langBtn.addEventListener("click", async () => {
    uiLang = uiLang === "ta" ? "en" : "ta";
    await updatePreferences({ uiLang });
    render();
  });

  liveBtn.addEventListener("click", async () => {
    if (restricted || typeof activeTab?.id !== "number") return;
    const res = await api.runtime.sendMessage({
      type: "TOGGLE_LIVE_TYPING",
      tabId: activeTab.id,
      enabled: !liveEnabled,
      layout,
    });
    if (res?.ok) {
      liveEnabled = Boolean(res.enabled);
      render();
    }
  });

  layoutSel.addEventListener("change", async () => {
    layout = layoutSel.value as TypingLayout;
    await updatePreferences({ layout });
    if (!restricted && typeof activeTab?.id === "number") {
      await api.runtime.sendMessage({
        type: "TOGGLE_LIVE_TYPING",
        tabId: activeTab.id,
        enabled: liveEnabled,
        layout,
      });
    }
  });

  openPanelBtn.addEventListener("click", () => {
    // Must be called synchronously inside the click handler so Chrome & Firefox accept the user gesture
    void openSidePanelForTab(activeTab?.id, activeTab?.windowId).finally(() => {
      window.close();
    });
  });

  render();
}

void bootstrap();
