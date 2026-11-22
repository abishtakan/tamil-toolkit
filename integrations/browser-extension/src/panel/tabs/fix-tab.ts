import { getBrowserApi } from "../../shared/browser-api.js";
import type { UiStrings } from "../../shared/i18n.js";
import type { LegacyEncoding, SortProfile } from "../../shared/messages.js";
import { getPreferences, updatePreferences } from "../../shared/storage.js";

export interface FixTabContext {
  strings: () => UiStrings;
  getActiveTabId: () => Promise<number | undefined>;
}

type FixMode = "convert" | "repair" | "sort";

export function mountFixTab(container: HTMLElement, ctx: FixTabContext): {
  loadHandoff: (text: string, editable: boolean) => Promise<void>;
  rerenderLabels: () => void;
} {
  const api = getBrowserApi();
  let mode: FixMode = "convert";
  let encoding: LegacyEncoding = "auto";
  let sortProfile: SortProfile = "agara-v1";
  let inputText = "";
  let outputText = "";
  let ambiguous = false;
  let editableTarget = false;

  function render(): void {
    const s = ctx.strings();
    container.innerHTML = `
      <div class="segmented">
        <button class="seg-btn ${mode === "convert" ? "active" : ""}" data-mode="convert" type="button">${s.modeConvert}</button>
        <button class="seg-btn ${mode === "repair" ? "active" : ""}" data-mode="repair" type="button">${s.modeRepair}</button>
        <button class="seg-btn ${mode === "sort" ? "active" : ""}" data-mode="sort" type="button">${s.modeSort}</button>
      </div>

      ${
        mode === "convert"
          ? `<select id="fix-encoding">
              <option value="auto">${s.encodingAuto}</option>
              <option value="bamini">Bamini</option>
              <option value="tscii">TSCII</option>
              <option value="tab">TAB</option>
              <option value="tam">TAM</option>
              <option value="anjal">Anjal</option>
              <option value="vanavil">Vanavil</option>
              <option value="lt_tm">LT-TM</option>
            </select>`
          : ""
      }

      ${
        mode === "sort"
          ? `<select id="fix-sort-profile">
              <option value="agara-v1">${s.sortAgara}</option>
              <option value="uyirmei-first-v1">${s.sortUyirmei}</option>
            </select>`
          : ""
      }

      <textarea id="fix-input" rows="4" placeholder="${s.fixPlaceholder}"></textarea>

      ${ambiguous ? `<div class="warn-text" style="font-size:12px">${s.ambiguousPrompt}</div>` : ""}

      <div class="output-box" id="fix-output"></div>

      <div class="row">
        ${
          editableTarget
            ? `<button class="btn primary sm" id="fix-replace-btn" type="button" ${ambiguous ? "disabled" : ""}>${s.replaceInPage}</button>`
            : "<span></span>"
        }
        <button class="btn sm ${editableTarget ? "" : "primary"}" id="fix-copy-btn" type="button" ${ambiguous ? "disabled" : ""}>${s.copy}</button>
      </div>
    `;

    container.querySelectorAll(".seg-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        mode = (btn as HTMLElement).dataset.mode as FixMode;
        ambiguous = false;
        render();
        void recompute();
      });
    });

    const encSel = container.querySelector("#fix-encoding") as HTMLSelectElement | null;
    if (encSel) {
      encSel.value = encoding;
      encSel.addEventListener("change", () => {
        encoding = encSel.value as LegacyEncoding;
        void recompute();
      });
    }

    const sortSel = container.querySelector("#fix-sort-profile") as HTMLSelectElement | null;
    if (sortSel) {
      sortSel.value = sortProfile;
      sortSel.addEventListener("change", async () => {
        sortProfile = sortSel.value as SortProfile;
        await updatePreferences({ sortProfile });
        void recompute();
      });
    }

    const inputEl = container.querySelector("#fix-input") as HTMLTextAreaElement;
    inputEl.value = inputText;
    inputEl.addEventListener("input", () => {
      inputText = inputEl.value;
      void recompute();
    });

    const outputEl = container.querySelector("#fix-output");
    if (outputEl) outputEl.textContent = outputText;

    container.querySelector("#fix-copy-btn")?.addEventListener("click", async (e) => {
      if (!outputText || ambiguous) return;
      await navigator.clipboard.writeText(outputText);
      const btn = e.target as HTMLButtonElement;
      btn.textContent = s.copied;
      window.setTimeout(() => {
        btn.textContent = s.copy;
      }, 1400);
    });

    container.querySelector("#fix-replace-btn")?.addEventListener("click", async () => {
      if (!outputText || ambiguous) return;
      const tabId = await ctx.getActiveTabId();
      await api.runtime.sendMessage({
        type: "PANEL_REPLACE_TAB_TEXT",
        tabId,
        text: outputText,
        scope: "selection",
      });
    });
  }

  async function recompute(): Promise<void> {
    if (!inputText) {
      outputText = "";
      ambiguous = false;
      const outEl = container.querySelector("#fix-output");
      if (outEl) outEl.textContent = "";
      return;
    }

    if (mode === "convert") {
      const res = await api.runtime.sendMessage({
        type: "ENGINE_DETECT_AND_CONVERT",
        text: inputText,
        encoding,
      });
      if (res?.ok) {
        ambiguous = Boolean(res.ambiguous);
        outputText = ambiguous ? "" : res.text;
        render();
      }
      return;
    }

    if (mode === "repair") {
      ambiguous = false;
      const res = await api.runtime.sendMessage({
        type: "ENGINE_REPAIR",
        text: inputText,
        stripJoiners: false,
      });
      if (res?.ok) {
        outputText = res.text;
        const outEl = container.querySelector("#fix-output");
        if (outEl) outEl.textContent = outputText;
      }
      return;
    }

    ambiguous = false;
    const res = await api.runtime.sendMessage({
      type: "ENGINE_SORT_LINES",
      text: inputText,
      profile: sortProfile,
    });
    if (res?.ok) {
      outputText = res.text;
      const outEl = container.querySelector("#fix-output");
      if (outEl) outEl.textContent = outputText;
    }
  }

  void getPreferences().then((p) => {
    sortProfile = p.sortProfile;
    render();
  });

  return {
    async loadHandoff(text: string, editable: boolean) {
      mode = "convert";
      encoding = "auto";
      inputText = text;
      editableTarget = editable;
      render();
      await recompute();
    },
    rerenderLabels: render,
  };
}
