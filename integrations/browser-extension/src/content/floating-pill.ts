import { BROWSER_TARGET } from "../shared/browser-api.js";
import { stringsFor } from "../shared/i18n.js";
import type { EditorKind, TypingLayout, UiLang } from "../shared/messages.js";
import type { CaretRect } from "./editor-adapter.js";

export interface FloatingPillCallbacks {
  onToggleEnabled: () => void;
  onChangeLayout: (layout: TypingLayout) => void;
  onScratchpadTransliterate: (raw: string) => Promise<string>;
  onScratchpadInsert: (text: string) => void;
}

const HOST_ID = "tamil-toolkit-floating-pill-host";

const PILL_STYLES = `
:host {
  all: initial;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif;
  color-scheme: light dark;
}
.tt-root {
  --bg: ${BROWSER_TARGET === "firefox" ? "#ffffff" : "#ffffff"};
  --bg-muted: ${BROWSER_TARGET === "firefox" ? "#f0f0f4" : "#f1f3f4"};
  --fg: ${BROWSER_TARGET === "firefox" ? "#15141a" : "#202124"};
  --fg-muted: ${BROWSER_TARGET === "firefox" ? "#5b5b66" : "#5f6368"};
  --border: ${BROWSER_TARGET === "firefox" ? "#d7d7db" : "#dadce0"};
  --accent: ${BROWSER_TARGET === "firefox" ? "#0060df" : "#1a73e8"};
  --accent-fg: #ffffff;
  --radius: ${BROWSER_TARGET === "firefox" ? "8px" : "999px"};
  --radius-card: ${BROWSER_TARGET === "firefox" ? "8px" : "14px"};
}
@media (prefers-color-scheme: dark) {
  .tt-root {
    --bg: ${BROWSER_TARGET === "firefox" ? "#2b2a33" : "#292a2d"};
    --bg-muted: ${BROWSER_TARGET === "firefox" ? "#1c1b22" : "#202124"};
    --fg: ${BROWSER_TARGET === "firefox" ? "#fbfbfe" : "#e8eaed"};
    --fg-muted: ${BROWSER_TARGET === "firefox" ? "#bfbfc9" : "#9aa0a6"};
    --border: ${BROWSER_TARGET === "firefox" ? "#52525e" : "#3c4043"};
    --accent: ${BROWSER_TARGET === "firefox" ? "#00ddff" : "#8ab4f8"};
    --accent-fg: ${BROWSER_TARGET === "firefox" ? "#15141a" : "#202124"};
  }
}
.pill-shell {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 2147483646;
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
  opacity: 0;
  transform: translateY(6px);
  pointer-events: none;
  transition: opacity 0.16s ease, transform 0.16s ease;
}
.pill-shell.visible {
  opacity: 1;
  transform: translateY(0);
  pointer-events: auto;
}
.preview-chip, .scratch-card, .pill-bar {
  background: var(--bg);
  color: var(--fg);
  border: 1px solid var(--border);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
  font-size: 12px;
  line-height: 1.4;
}
.preview-chip {
  position: fixed;
  z-index: 2147483647;
  border-radius: var(--radius-card);
  padding: 5px 10px;
  display: none;
  align-items: center;
  gap: 8px;
  pointer-events: none;
  white-space: nowrap;
}
.preview-chip.show { display: inline-flex; }
.preview-chip.anchored-fallback {
  right: 16px;
  bottom: 58px;
}
.preview-raw { color: var(--fg-muted); font-family: ui-monospace, monospace; font-size: 11px; }
.preview-out { color: var(--accent); font-weight: 600; font-size: 13px; }
.pill-bar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: var(--radius);
}
.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1e8e3e;
}
.dot.off { background: var(--fg-muted); }
.btn {
  border: 1px solid var(--border);
  background: var(--bg-muted);
  color: var(--fg);
  border-radius: var(--radius);
  padding: 3px 9px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}
.btn.on {
  background: var(--accent);
  color: var(--accent-fg);
  border-color: var(--accent);
}
.select {
  appearance: none;
  -webkit-appearance: none;
  border: 1px solid var(--border);
  background-color: var(--bg-muted);
  color: var(--fg);
  border-radius: var(--radius);
  padding: 3px 26px 3px 10px;
  font-size: 11.5px;
  outline: none;
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%235f6368' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 4.5 6 8l3.5-3.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 9px center;
  background-size: 11px 11px;
}
@media (prefers-color-scheme: dark) {
  .select {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='11' height='11' viewBox='0 0 12 12'%3E%3Cpath fill='none' stroke='%239aa0a6' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M2.5 4.5 6 8l3.5-3.5'/%3E%3C/svg%3E");
  }
}
.counter {
  font-size: 11px;
  color: var(--fg-muted);
  padding: 0 4px;
  display: none;
}
.counter.show { display: inline; }
.scratch-card {
  border-radius: var(--radius-card);
  padding: 8px 10px;
  width: 280px;
  display: none;
  flex-direction: column;
  gap: 6px;
}
.scratch-card.show { display: flex; }
.scratch-title { font-size: 11px; color: var(--fg-muted); }
.scratch-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid var(--border);
  background: var(--bg-muted);
  color: var(--fg);
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12.5px;
  outline: none;
}
.scratch-out {
  min-height: 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fg);
}
.scratch-actions { display: flex; gap: 6px; justify-content: flex-end; }
`;

export class FloatingPill {
  private host: HTMLElement | null = null;
  private shadow: ShadowRoot | null = null;
  private shellEl: HTMLElement | null = null;
  private dotEl: HTMLElement | null = null;
  private toggleBtn: HTMLButtonElement | null = null;
  private layoutSelect: HTMLSelectElement | null = null;
  private counterEl: HTMLElement | null = null;
  private previewChip: HTMLElement | null = null;
  private previewRaw: HTMLElement | null = null;
  private previewOut: HTMLElement | null = null;
  private scratchCard: HTMLElement | null = null;
  private scratchInput: HTMLInputElement | null = null;
  private scratchOut: HTMLElement | null = null;
  private confirmTimer: number | null = null;
  private focused = false;
  private enabled = false;
  private editorKind: EditorKind = "none";
  private readonly callbacks: FloatingPillCallbacks;

  constructor(callbacks: FloatingPillCallbacks) {
    this.callbacks = callbacks;
  }

  mount(): void {
    if (this.host || typeof document === "undefined") return;
    const existing = document.getElementById(HOST_ID);
    if (existing) existing.remove();

    this.host = document.createElement("div");
    this.host.id = HOST_ID;
    this.shadow = this.host.attachShadow({ mode: "open" });

    const style = document.createElement("style");
    style.textContent = PILL_STYLES;

    const root = document.createElement("div");
    root.className = "tt-root";
    root.innerHTML = `
      <div class="preview-chip" id="tt-preview">
        <span class="preview-raw" id="tt-raw"></span>
        <span>\u2192</span>
        <span class="preview-out" id="tt-out"></span>
      </div>
      <div class="pill-shell" id="tt-shell">
        <div class="scratch-card" id="tt-scratch">
          <div class="scratch-title">Quick Compose (canvas editor fallback)</div>
          <input class="scratch-input" id="tt-scratch-in" type="text" placeholder="Type Tamil here..." />
          <div class="scratch-out" id="tt-scratch-out"></div>
          <div class="scratch-actions">
            <button class="btn" id="tt-scratch-copy" type="button">Copy</button>
            <button class="btn on" id="tt-scratch-insert" type="button">Insert</button>
          </div>
        </div>
        <div class="pill-bar">
          <span class="dot" id="tt-dot"></span>
          <button class="btn on" id="tt-toggle" type="button">\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD ON</button>
          <select class="select" id="tt-layout" aria-label="Tamil typing layout">
            <option value="phonetic-v1">Phonetic</option>
            <option value="tamil99">Tamil99</option>
            <option value="anjal-phonetic">Anjal</option>
            <option value="suratha-bamini">Bamini</option>
          </select>
          <span class="counter" id="tt-counter"></span>
        </div>
      </div>
    `;

    this.shadow.append(style, root);
    document.documentElement.appendChild(this.host);

    this.shellEl = this.shadow.getElementById("tt-shell");
    this.dotEl = this.shadow.getElementById("tt-dot");
    this.toggleBtn = this.shadow.getElementById("tt-toggle") as HTMLButtonElement;
    this.layoutSelect = this.shadow.getElementById("tt-layout") as HTMLSelectElement;
    this.counterEl = this.shadow.getElementById("tt-counter");
    this.previewChip = this.shadow.getElementById("tt-preview");
    this.previewRaw = this.shadow.getElementById("tt-raw");
    this.previewOut = this.shadow.getElementById("tt-out");
    this.scratchCard = this.shadow.getElementById("tt-scratch");
    this.scratchInput = this.shadow.getElementById("tt-scratch-in") as HTMLInputElement;
    this.scratchOut = this.shadow.getElementById("tt-scratch-out");

    this.toggleBtn.addEventListener("mousedown", (e) => e.preventDefault());
    this.toggleBtn.addEventListener("click", () => this.callbacks.onToggleEnabled());
    this.layoutSelect.addEventListener("change", () => {
      this.callbacks.onChangeLayout(this.layoutSelect!.value as TypingLayout);
    });

    this.scratchInput.addEventListener("input", () => {
      const val = this.scratchInput?.value ?? "";
      void this.callbacks.onScratchpadTransliterate(val).then((converted) => {
        if (this.scratchOut) this.scratchOut.textContent = converted;
      });
    });

    this.shadow.getElementById("tt-scratch-copy")?.addEventListener("click", () => {
      const out = this.scratchOut?.textContent ?? "";
      if (out && navigator.clipboard?.writeText) {
        void navigator.clipboard.writeText(out);
      }
    });
    this.shadow.getElementById("tt-scratch-insert")?.addEventListener("click", () => {
      const out = this.scratchOut?.textContent ?? "";
      if (out) {
        this.callbacks.onScratchpadInsert(out);
        if (this.scratchInput) this.scratchInput.value = "";
        if (this.scratchOut) this.scratchOut.textContent = "";
      }
    });
  }

  updateState(opts: {
    enabled: boolean;
    layout: TypingLayout;
    uiLang: UiLang;
    showMicroCounter: boolean;
    editorKind: EditorKind;
    showConfirmToast?: boolean;
  }): void {
    this.mount();
    this.enabled = opts.enabled;
    this.editorKind = opts.editorKind;

    const s = stringsFor(opts.uiLang);
    const scratchTitle = this.shadow?.querySelector(".scratch-title");
    if (scratchTitle) scratchTitle.textContent = s.pillScratchTitle;
    if (this.scratchInput) this.scratchInput.placeholder = s.pillScratchPlaceholder;
    const copyBtn = this.shadow?.getElementById("tt-scratch-copy");
    if (copyBtn) copyBtn.textContent = s.pillCopy;
    const insertBtn = this.shadow?.getElementById("tt-scratch-insert");
    if (insertBtn) insertBtn.textContent = s.pillInsert;
    if (this.layoutSelect) {
      const labels: Record<TypingLayout, string> = {
        "phonetic-v1": s.pillLayoutPhonetic,
        tamil99: s.pillLayoutTamil99,
        "anjal-phonetic": s.pillLayoutAnjal,
        "suratha-bamini": s.pillLayoutBamini,
      };
      for (const opt of Array.from(this.layoutSelect.options)) {
        const key = opt.value as TypingLayout;
        if (labels[key]) opt.textContent = labels[key];
      }
    }

    if (this.dotEl) this.dotEl.classList.toggle("off", !opts.enabled);
    if (this.toggleBtn) {
      this.toggleBtn.classList.toggle("on", opts.enabled);
      this.toggleBtn.textContent = opts.enabled ? "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD ON" : "EN";
    }
    if (this.layoutSelect) {
      this.layoutSelect.value = opts.layout;
    }
    if (this.counterEl) {
      this.counterEl.classList.toggle("show", opts.showMicroCounter && opts.enabled);
    }
    if (this.scratchCard) {
      this.scratchCard.classList.toggle("show", opts.enabled && opts.editorKind === "canvas-fallback");
    }

    if (opts.showConfirmToast) {
      this.flashConfirmation();
    } else {
      this.syncVisibility();
    }
  }

  setFocused(focused: boolean, editorKind: EditorKind): void {
    this.focused = focused;
    this.editorKind = editorKind;
    if (this.scratchCard) {
      this.scratchCard.classList.toggle("show", this.enabled && editorKind === "canvas-fallback");
    }
    if (!focused) {
      this.setPreview("", "");
    }
    this.syncVisibility();
  }

  setPreview(raw: string, out: string, caretRect?: CaretRect | null): void {
    if (!this.previewChip || !this.previewRaw || !this.previewOut) return;
    const show = this.enabled && raw.length > 0 && out.length > 0;
    this.previewChip.classList.toggle("show", show);
    if (show) {
      this.previewRaw.textContent = raw;
      this.previewOut.textContent = out;
      if (caretRect && typeof window !== "undefined") {
        this.previewChip.classList.remove("anchored-fallback");
        const estWidth = Math.max(120, (raw.length + out.length) * 9 + 44);
        const left = Math.max(8, Math.min(caretRect.left, window.innerWidth - estWidth - 8));
        const spaceBelow = window.innerHeight - caretRect.bottom;
        const top = spaceBelow >= 44 ? caretRect.bottom + 6 : Math.max(8, caretRect.top - 36);
        this.previewChip.style.left = `${Math.round(left)}px`;
        this.previewChip.style.top = `${Math.round(top)}px`;
      } else {
        this.previewChip.classList.add("anchored-fallback");
        this.previewChip.style.left = "";
        this.previewChip.style.top = "";
      }
      if (!this.focused) {
        this.focused = true;
        this.syncVisibility();
      }
    }
  }

  setMicroCounter(letters: number, words: number): void {
    if (!this.counterEl) return;
    this.counterEl.textContent = `${letters} \u0B8E\u0BB4\u0BC1\u0BA4\u0BCD\u0BA4\u0BC1 \u00B7 ${words} \u0B9A\u0BCA\u0BB2\u0BCD`;
  }

  private flashConfirmation(): void {
    if (this.confirmTimer !== null) {
      window.clearTimeout(this.confirmTimer);
    }
    this.shellEl?.classList.add("visible");
    this.confirmTimer = window.setTimeout(() => {
      this.confirmTimer = null;
      this.syncVisibility();
    }, 2000);
  }

  private syncVisibility(): void {
    if (!this.shellEl) return;
    const shouldShow =
      this.enabled && (this.focused || this.editorKind === "canvas-fallback" || this.confirmTimer !== null);
    this.shellEl.classList.toggle("visible", shouldShow);
  }

  destroy(): void {
    if (this.confirmTimer !== null) {
      window.clearTimeout(this.confirmTimer);
      this.confirmTimer = null;
    }
    this.host?.remove();
    this.host = null;
    this.shadow = null;
  }
}
