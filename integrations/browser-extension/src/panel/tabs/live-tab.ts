import { getBrowserApi } from "../../shared/browser-api.js";
import type { UiStrings } from "../../shared/i18n.js";
import type { TypingLayout } from "../../shared/messages.js";
import { getPreferences, getSiteRules, originPatternFromUrl, updatePreferences } from "../../shared/storage.js";

export interface LiveTabContext {
  strings: () => UiStrings;
  getActiveTab: () => Promise<{ id?: number; url?: string } | undefined>;
}

export function mountLiveTab(container: HTMLElement, ctx: LiveTabContext): {
  refresh: () => Promise<void>;
  rerenderLabels: () => void;
} {
  const api = getBrowserApi();
  let liveEnabled = false;
  let currentLayout: TypingLayout = "phonetic-v1";
  let currentOrigin: string | null = null;
  let alwaysOnSite = false;

  function render(): void {
    const s = ctx.strings();
    const hostLabel = currentOrigin ? new URL(currentOrigin.replace("/*", "/")).hostname : "this site";

    container.innerHTML = `
      <div class="card row">
        <div>
          <strong>${s.liveTypingLabel}</strong>
          <div class="muted">${s.liveTypingDesc}</div>
        </div>
        <button class="btn sm ${liveEnabled ? "primary" : ""}" id="live-toggle-btn" type="button">
          ${liveEnabled ? "ON" : "OFF"}
        </button>
      </div>

      <div class="card stack">
        <label class="muted" for="live-layout-select">${s.layoutLabel}</label>
        <select id="live-layout-select">
          <option value="phonetic-v1">Phonetic (Tanglish)</option>
          <option value="tamil99">Tamil99</option>
          <option value="anjal-phonetic">Anjal</option>
          <option value="suratha-bamini">Bamini / Suratha Bamini</option>
        </select>
      </div>

      <div class="card row" id="always-on-card" style="${currentOrigin ? "" : "display:none"}">
        <div>
          <strong>${s.alwaysOnSiteLabel} (${hostLabel})</strong>
          <div class="muted">${s.alwaysOnSiteDesc}</div>
        </div>
        <button class="btn sm ${alwaysOnSite ? "primary" : ""}" id="site-always-btn" type="button">
          ${alwaysOnSite ? "ON" : "OFF"}
        </button>
      </div>

      <div class="card stack">
        <label class="muted" for="scratch-raw">${s.scratchpadLabel}</label>
        <textarea id="scratch-raw" rows="3" placeholder="${s.scratchpadPlaceholder}"></textarea>
        <div class="output-box" id="scratch-out"></div>
        <div class="row">
          <button class="btn primary sm" id="scratch-insert" type="button">${s.insertIntoPage}</button>
          <button class="btn sm" id="scratch-copy" type="button">${s.copy}</button>
        </div>
      </div>
    `;

    const layoutSelect = container.querySelector("#live-layout-select") as HTMLSelectElement;
    layoutSelect.value = currentLayout;
    layoutSelect.addEventListener("change", async () => {
      currentLayout = layoutSelect.value as TypingLayout;
      await updatePreferences({ layout: currentLayout });
      const tab = await ctx.getActiveTab();
      await api.runtime.sendMessage({
        type: "TOGGLE_LIVE_TYPING",
        tabId: tab?.id,
        enabled: liveEnabled,
        layout: currentLayout,
      });
      await updateScratchpadPreview();
    });

    container.querySelector("#live-toggle-btn")?.addEventListener("click", async () => {
      const tab = await ctx.getActiveTab();
      const res = await api.runtime.sendMessage({
        type: "TOGGLE_LIVE_TYPING",
        tabId: tab?.id,
        enabled: !liveEnabled,
        layout: currentLayout,
      });
      if (res?.ok) {
        liveEnabled = Boolean(res.enabled);
        render();
      }
    });

    container.querySelector("#site-always-btn")?.addEventListener("click", async () => {
      if (!currentOrigin) return;
      const next = !alwaysOnSite;
      if (next && api?.permissions?.request) {
        const granted = await api.permissions.request({ origins: [currentOrigin] });
        if (!granted) return;
      }
      const res = await api.runtime.sendMessage({
        type: "SET_SITE_ALWAYS_ON",
        originPattern: currentOrigin,
        enabled: next,
      });
      if (res?.ok) {
        alwaysOnSite = Boolean(res.enabled);
        render();
      }
    });

    const scratchRaw = container.querySelector("#scratch-raw") as HTMLTextAreaElement;
    scratchRaw.addEventListener("input", () => {
      void updateScratchpadPreview();
    });

    container.querySelector("#scratch-copy")?.addEventListener("click", async (e) => {
      const out = (container.querySelector("#scratch-out")?.textContent ?? "").trim();
      if (!out) return;
      await navigator.clipboard.writeText(out);
      const btn = e.target as HTMLButtonElement;
      btn.textContent = s.copied;
      window.setTimeout(() => {
        btn.textContent = s.copy;
      }, 1400);
    });

    container.querySelector("#scratch-insert")?.addEventListener("click", async () => {
      const out = (container.querySelector("#scratch-out")?.textContent ?? "").trim();
      if (!out) return;
      const tab = await ctx.getActiveTab();
      await api.runtime
        .sendMessage({ type: "PANEL_INSERT_TAB_TEXT", tabId: tab?.id, text: out })
        .catch(() => undefined);
    });
  }

  async function updateScratchpadPreview(): Promise<void> {
    const raw = (container.querySelector("#scratch-raw") as HTMLTextAreaElement | null)?.value ?? "";
    const outEl = container.querySelector("#scratch-out");
    if (!outEl) return;
    if (!raw) {
      outEl.textContent = "";
      return;
    }
    const res = await api.runtime.sendMessage({
      type: "ENGINE_TRANSLITERATE",
      text: raw,
      scheme: currentLayout,
    });
    outEl.textContent = res?.ok ? res.output : raw;
  }

  async function refresh(): Promise<void> {
    const prefs = await getPreferences();
    currentLayout = prefs.layout;
    const tab = await ctx.getActiveTab();
    currentOrigin = tab?.url ? originPatternFromUrl(tab.url) : null;
    if (currentOrigin) {
      const rules = await getSiteRules();
      alwaysOnSite = Boolean(rules[currentOrigin]?.alwaysOnLiveTyping);
    } else {
      alwaysOnSite = false;
    }
    const state = await api.runtime.sendMessage({ type: "GET_TAB_LIVE_STATE", tabId: tab?.id });
    if (state?.ok) {
      liveEnabled = Boolean(state.enabled);
    }
    render();
  }

  render();

  return {
    refresh,
    rerenderLabels: render,
  };
}
