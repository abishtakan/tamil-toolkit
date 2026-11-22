import { getBrowserApi } from "../../shared/browser-api.js";
import type { UiStrings } from "../../shared/i18n.js";
import type { InspectionSnapshot, InspectionSource } from "../../shared/messages.js";

export interface InspectTabContext {
  strings: () => UiStrings;
  getActiveTabId: () => Promise<number | undefined>;
}

export function mountInspectTab(container: HTMLElement, ctx: InspectTabContext): {
  refresh: (handoffText?: string, handoffEditable?: boolean) => Promise<void>;
  rerenderLabels: () => void;
} {
  const api = getBrowserApi();
  let currentText = "";
  let currentSource: InspectionSource = "manual";
  let currentEditable = false;

  function renderShell(): void {
    const s = ctx.strings();
    container.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-val" id="ins-letters">0</div>
          <div class="stat-lbl">${s.tamilLetters}</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="ins-words">0</div>
          <div class="stat-lbl">${s.words}</div>
        </div>
        <div class="stat-card">
          <div class="stat-val" id="ins-utf16">0</div>
          <div class="stat-lbl">${s.utf16Units}</div>
        </div>
      </div>

      <div class="card">
        <div class="row">
          <strong>${s.letterBreakdown}</strong>
          <span class="muted" id="ins-readtime">0s</span>
        </div>
        <div class="bar-track">
          <div class="seg-uyir" id="bar-uyir" style="width:0%"></div>
          <div class="seg-mei" id="bar-mei" style="width:0%"></div>
          <div class="seg-uyirmei" id="bar-uyirmei" style="width:0%"></div>
          <div class="seg-aytham" id="bar-aytham" style="width:0%"></div>
          <div class="seg-grantha" id="bar-grantha" style="width:0%"></div>
        </div>
        <div class="legend">
          <span class="legend-item"><i class="swatch seg-uyir"></i>${s.uyir} <b id="c-uyir">0</b></span>
          <span class="legend-item"><i class="swatch seg-mei"></i>${s.mei} <b id="c-mei">0</b></span>
          <span class="legend-item"><i class="swatch seg-uyirmei"></i>${s.uyirmei} <b id="c-uyirmei">0</b></span>
          <span class="legend-item"><i class="swatch seg-aytham"></i>${s.aytham} <b id="c-aytham">0</b></span>
          <span class="legend-item"><i class="swatch seg-grantha"></i>${s.grantha} <b id="c-grantha">0</b></span>
        </div>
      </div>

      <div class="card row">
        <div>
          <div id="ins-health-title" class="ok-text">${s.healthClean}</div>
          <div id="ins-health-detail" class="muted">${s.healthCleanDetail}</div>
        </div>
        <button class="btn primary sm" id="ins-repair-btn" type="button" style="display:none">${s.repairInPlace}</button>
      </div>

      <div class="card stack">
        <div class="row">
          <button class="btn sm" id="ins-refresh-btn" type="button">${s.refreshInspect}</button>
          <button class="btn sm" id="ins-page-btn" type="button">${s.inspectVisiblePage}</button>
        </div>
        <textarea id="ins-manual" rows="4" placeholder="${s.inspectPlaceholder}"></textarea>
      </div>
    `;

    const manualTa = container.querySelector("#ins-manual") as HTMLTextAreaElement;
    manualTa.value = currentText;
    manualTa.addEventListener("input", () => {
      currentText = manualTa.value;
      currentSource = "manual";
      currentEditable = false;
      void runInspect(currentText, "manual", false);
    });

    container.querySelector("#ins-refresh-btn")?.addEventListener("click", () => {
      void pullFromActiveTab("auto");
    });
    container.querySelector("#ins-page-btn")?.addEventListener("click", () => {
      void pullFromActiveTab("visible-page");
    });
    container.querySelector("#ins-repair-btn")?.addEventListener("click", () => {
      void repairInPlace();
    });
  }

  function paintSnapshot(snap: InspectionSnapshot): void {
    const s = ctx.strings();
    const set = (id: string, val: string | number) => {
      const el = container.querySelector(`#${id}`);
      if (el) el.textContent = String(val);
    };
    set("ins-letters", snap.letterCount);
    set("ins-words", snap.wordCount);
    set("ins-utf16", snap.utf16Length);
    set("ins-readtime", snap.readingSeconds > 0 ? `~${snap.readingSeconds}s` : "0s");

    const { uyir, mei, uyirmei, aytham, grantha } = snap.breakdown;
    set("c-uyir", uyir);
    set("c-mei", mei);
    set("c-uyirmei", uyirmei);
    set("c-aytham", aytham);
    set("c-grantha", grantha);

    const denom = Math.max(1, snap.letterCount);
    const setW = (id: string, n: number) => {
      const el = container.querySelector(`#${id}`) as HTMLElement | null;
      if (el) el.style.width = `${(n / denom) * 100}%`;
    };
    setW("bar-uyir", uyir);
    setW("bar-mei", mei);
    setW("bar-uyirmei", uyirmei);
    setW("bar-aytham", aytham);
    setW("bar-grantha", grantha);

    const titleEl = container.querySelector("#ins-health-title") as HTMLElement | null;
    const detailEl = container.querySelector("#ins-health-detail") as HTMLElement | null;
    const repairBtn = container.querySelector("#ins-repair-btn") as HTMLButtonElement | null;

    if (snap.health.totalIssues > 0) {
      if (titleEl) {
        titleEl.className = "warn-text";
        titleEl.textContent = s.healthIssuesFound(snap.health.totalIssues);
      }
      if (detailEl) {
        const parts: string[] = [];
        if (snap.health.visualKombus > 0) parts.push(s.healthVisualKombu(snap.health.visualKombus));
        if (snap.health.duplicatePullis > 0) parts.push(s.healthDuplicatePulli(snap.health.duplicatePullis));
        if (!snap.health.isNfc) parts.push(s.healthNonNfc);
        if (snap.health.detectedLegacyEncoding) parts.push(s.healthLegacyDetected(snap.health.detectedLegacyEncoding));
        detailEl.textContent = parts.join(" \u00B7 ");
      }
      if (repairBtn) {
        repairBtn.style.display =
          (snap.editable || currentSource === "manual") && !snap.health.detectedLegacyEncoding
            ? "inline-block"
            : "none";
      }
    } else {
      if (titleEl) {
        titleEl.className = "ok-text";
        titleEl.textContent = s.healthClean;
      }
      if (detailEl) {
        detailEl.textContent =
          snap.health.zeroWidthCount > 0
            ? `${s.healthCleanDetail} (${s.healthJoinersPreserved(snap.health.zeroWidthCount)})`
            : s.healthCleanDetail;
      }
      if (repairBtn) repairBtn.style.display = "none";
    }
  }

  async function runInspect(text: string, source: InspectionSource, editable: boolean): Promise<void> {
    const res = await api.runtime.sendMessage({
      type: "ENGINE_INSPECT",
      text,
      source,
      editable,
    });
    if (res?.ok && res.snapshot) {
      paintSnapshot(res.snapshot);
    }
  }

  async function pullFromActiveTab(mode: "auto" | "visible-page"): Promise<void> {
    const tabId = await ctx.getActiveTabId();
    try {
      const res = await api.runtime.sendMessage({
        type: "PANEL_GET_TAB_CONTEXT_TEXT",
        tabId,
        mode,
      });
      if (res?.ok && typeof res.text === "string") {
        currentText = res.text;
        currentSource = res.source ?? "manual";
        currentEditable = Boolean(res.editable);
        const manualTa = container.querySelector("#ins-manual") as HTMLTextAreaElement | null;
        if (manualTa) manualTa.value = currentText;
        await runInspect(currentText, currentSource, currentEditable);
      }
    } catch {
      // Restricted page — keep manual mode
    }
  }

  async function repairInPlace(): Promise<void> {
    const res = await api.runtime.sendMessage({ type: "ENGINE_REPAIR", text: currentText });
    if (!res?.ok) return;
    if (currentSource !== "manual" && currentEditable) {
      const tabId = await ctx.getActiveTabId();
      await api.runtime.sendMessage({
        type: "PANEL_REPLACE_TAB_TEXT",
        tabId,
        text: res.text,
        scope: currentSource === "selection" ? "selection" : "active-editor",
      });
    }
    currentText = res.text;
    const manualTa = container.querySelector("#ins-manual") as HTMLTextAreaElement | null;
    if (manualTa) manualTa.value = currentText;
    await runInspect(currentText, currentSource, currentEditable);
  }

  renderShell();

  // Live stream updates from the active web page as the user types or highlights text
  if (api?.runtime?.onMessage) {
    api.runtime.onMessage.addListener((msg: any) => {
      if (msg?.type !== "LIVE_INSPECT_UPDATE") return false;
      const manualTa = container.querySelector("#ins-manual") as HTMLTextAreaElement | null;
      if (manualTa && document.activeElement === manualTa) return false;
      currentText = typeof msg.text === "string" ? msg.text : "";
      currentSource = msg.source ?? "active-editor";
      currentEditable = Boolean(msg.editable);
      if (manualTa) manualTa.value = currentText;
      void runInspect(currentText, currentSource, currentEditable);
      return false;
    });
  }

  return {
    async refresh(handoffText?: string, handoffEditable?: boolean) {
      if (typeof handoffText === "string" && handoffText.length > 0) {
        currentText = handoffText;
        currentSource = "selection";
        currentEditable = Boolean(handoffEditable);
        const manualTa = container.querySelector("#ins-manual") as HTMLTextAreaElement | null;
        if (manualTa) manualTa.value = currentText;
        await runInspect(currentText, currentSource, currentEditable);
      } else {
        await pullFromActiveTab("auto");
      }
    },
    rerenderLabels() {
      renderShell();
      void runInspect(currentText, currentSource, currentEditable);
    },
  };
}
