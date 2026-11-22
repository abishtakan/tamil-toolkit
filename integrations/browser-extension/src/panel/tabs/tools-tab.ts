import { getBrowserApi } from "../../shared/browser-api.js";
import type { UiStrings } from "../../shared/i18n.js";
import type { NumeralLocale, OfficialHolidayItem, SupportedCurrency } from "../../shared/messages.js";
import { getPreferences, getSiteRules, originPatternFromUrl, updatePreferences } from "../../shared/storage.js";

export interface ToolsTabContext {
  strings: () => UiStrings;
  getActiveTab: () => Promise<{ id?: number; url?: string } | undefined>;
}

export function mountToolsTab(container: HTMLElement, ctx: ToolsTabContext): {
  refresh: () => Promise<void>;
  rerenderLabels: () => void;
} {
  const api = getBrowserApi();
  let locale: NumeralLocale = "TN";
  let currency: SupportedCurrency | "" = "INR";
  let amount = "2500";
  let numeralResult = "";
  let civilDateLabel = "";
  let holidays: OfficialHolidayItem[] = [];
  let sourceNote = "";
  let supportedYear = true;
  let currentOrigin: string | null = null;
  let fontFixEnabled = false;

  function render(): void {
    const s = ctx.strings();
    container.innerHTML = `
      <div class="card stack">
        <strong>${s.numbersTitle}</strong>
        <div class="row">
          <select id="tools-locale">
            <option value="TN">${s.localeTN}</option>
            <option value="SL">${s.localeSL}</option>
          </select>
          <select id="tools-currency">
            <option value="">${s.noCurrency}</option>
            <option value="INR">INR (\u20B9)</option>
            <option value="LKR">LKR (Rs.)</option>
          </select>
        </div>
        <input type="text" id="tools-amount" value="${amount}" placeholder="2500" />
        <div class="output-box" id="tools-num-out">${numeralResult}</div>
      </div>

      <div class="card stack">
        <strong>${s.datesTitle}</strong>
        <div class="output-box" style="min-height:auto;font-weight:600">${civilDateLabel || "\u2014"}</div>
        <div class="muted">${sourceNote}</div>
        ${
          supportedYear
            ? `<div class="holiday-list">
                ${holidays
                  .slice(0, 12)
                  .map(
                    (h) =>
                      `<div class="holiday-item"><span>${h.tamilName || h.name}</span><span class="muted">${h.date}</span></div>`
                  )
                  .join("")}
              </div>`
            : `<div class="warn-text" style="font-size:12px">${s.unsupportedYear}</div>`
        }
      </div>

      <div class="card row" style="${currentOrigin ? "" : "display:none"}">
        <div>
          <strong>${s.fontFixTitle}</strong>
          <div class="muted">${s.fontFixDesc}</div>
        </div>
        <button class="btn sm ${fontFixEnabled ? "primary" : ""}" id="tools-font-btn" type="button">
          ${fontFixEnabled ? "ON" : "OFF"}
        </button>
      </div>
    `;

    const locSel = container.querySelector("#tools-locale") as HTMLSelectElement;
    locSel.value = locale;
    locSel.addEventListener("change", async () => {
      locale = locSel.value as NumeralLocale;
      currency = locale === "SL" ? "LKR" : "INR";
      await updatePreferences({ numeralLocale: locale, currency });
      await loadNumeralAndDate();
    });

    const curSel = container.querySelector("#tools-currency") as HTMLSelectElement;
    curSel.value = currency;
    curSel.addEventListener("change", async () => {
      currency = curSel.value as SupportedCurrency | "";
      if (currency) {
        await updatePreferences({ currency });
      }
      await loadNumeralWords();
    });

    const amtIn = container.querySelector("#tools-amount") as HTMLInputElement;
    amtIn.addEventListener("input", () => {
      amount = amtIn.value;
      void loadNumeralWords();
    });

    container.querySelector("#tools-font-btn")?.addEventListener("click", async () => {
      if (!currentOrigin) return;
      const next = !fontFixEnabled;
      if (next && api?.permissions?.request) {
        const granted = await api.permissions.request({ origins: [currentOrigin] });
        if (!granted) return;
      }
      const tab = await ctx.getActiveTab();
      const res = await api.runtime.sendMessage({
        type: "SET_SITE_FONT_FIX",
        tabId: tab?.id,
        originPattern: currentOrigin,
        enabled: next,
      });
      if (res?.ok) {
        fontFixEnabled = Boolean(res.enabled);
        render();
      }
    });
  }

  async function loadNumeralWords(): Promise<void> {
    const outEl = container.querySelector("#tools-num-out");
    if (!amount.trim()) {
      numeralResult = "";
      if (outEl) outEl.textContent = "";
      return;
    }
    const res = await api.runtime.sendMessage({
      type: "ENGINE_NUMERAL_WORDS",
      amount,
      locale,
      currency: currency || undefined,
    });
    numeralResult = res?.ok ? `${res.words}${currency ? ` (${res.formatted})` : ""}` : (res?.error ?? "");
    if (outEl) outEl.textContent = numeralResult;
  }

  async function loadNumeralAndDate(): Promise<void> {
    await loadNumeralWords();
    const now = new Date();
    const res = await api.runtime.sendMessage({
      type: "ENGINE_DATE_AND_HOLIDAYS",
      year: now.getFullYear(),
      month: now.getMonth() + 1,
      day: now.getDate(),
      jurisdiction: locale,
    });
    if (res?.ok) {
      civilDateLabel = res.civilDateLabel;
      holidays = res.holidays ?? [];
      supportedYear = Boolean(res.supportedYear);
      sourceNote = res.sourceNote ?? "";
    }
    render();
  }

  async function refresh(): Promise<void> {
    const prefs = await getPreferences();
    locale = prefs.numeralLocale;
    currency = prefs.currency;
    const tab = await ctx.getActiveTab();
    currentOrigin = tab?.url ? originPatternFromUrl(tab.url) : null;
    if (currentOrigin) {
      const rules = await getSiteRules();
      fontFixEnabled = Boolean(rules[currentOrigin]?.improveTamilFonts);
    } else {
      fontFixEnabled = false;
    }
    await loadNumeralAndDate();
  }

  render();

  return {
    refresh,
    rerenderLabels: render,
  };
}
