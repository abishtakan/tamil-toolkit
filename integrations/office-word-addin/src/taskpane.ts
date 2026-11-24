import { registerRibbonCommands } from "./commands.js";
import { STRINGS, UiLang, getSavedLang, saveLang } from "./lib/i18n.js";
import {
  configureLiveTyping,
  isLiveTypingActive,
  setLiveTypingSuspended,
  subscribeLiveTyping,
  toggleLiveTyping,
} from "./lib/live-typing.js";
import {
  CalendarProfile,
  CollationProfile,
  KeyboardLayout,
  LegacyEncoding,
  NumeralLocale,
  SupportedCurrency,
  TRADITIONAL_SYMBOLS_PALETTE,
  TargetLegacyEncoding,
  buildTamilDateStamp,
  convertDigits,
  convertKeyboardToUnicode,
  formatTraditionalInteger,
  initTamilEngine,
  inspectDocumentText,
  isTamilEngineReady,
  numberToTamilWords,
  repairTamilText,
  transliterateSuggestText,
  transliterateText,
  wordsToNumber,
} from "./lib/tamil-engine.js";
import {
  TargetScope,
  getCanvasMayangoliCandidates,
  insertAtCursor,
  isWordHost,
  readTargetText,
  readWordAtCursorOrSelection,
  replaceTrailingOrSelectedWord,
  runHyphenation,
  runKeyboardToUnicode,
  runPrepareLegacyDocument,
  runRemoveHyphens,
  runSortSelectedTable,
  runSortSelectionParagraphs,
  runTamilFindAndReplace,
  runUnicodeToLegacy,
} from "./lib/word-adapter.js";

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing element #${id}`);
  return el;
}

function setStatus(message: string, kind: "info" | "success" | "error" = "info"): void {
  const bar = $("status-bar");
  bar.className = `status-bar status-${kind}`;
  bar.textContent = message;
}

function setBusy(busy: boolean): void {
  document.querySelectorAll<HTMLButtonElement>("button[data-action]").forEach((btn) => {
    btn.disabled = busy;
  });
}

function syncWordTheme(): void {
  try {
    const theme = typeof Office !== "undefined" ? Office.context?.officeTheme : undefined;
    const bgHex = theme?.bodyBackgroundColor;
    if (bgHex && /^#[0-9a-f]{6}$/i.test(bgHex)) {
      const r = Number.parseInt(bgHex.slice(1, 3), 16);
      const g = Number.parseInt(bgHex.slice(3, 5), 16);
      const b = Number.parseInt(bgHex.slice(5, 7), 16);
      const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
      document.documentElement.dataset.theme = luminance < 0.5 ? "dark" : "light";
      document.documentElement.style.setProperty("--bg", bgHex);
    }
  } catch {
    // Fall back to system prefers-color-scheme
  }
}

function applyLanguage(lang: UiLang): void {
  const dict = STRINGS[lang];
  document.documentElement.lang = lang;
  document.querySelectorAll<HTMLElement>("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (key && dict[key]) {
      el.textContent = dict[key];
    }
  });
  const toggleBtn = $("btn-lang-toggle");
  toggleBtn.textContent = lang === "en" ? "தமிழ்" : "EN";
}

function initTabs(onTabActivated?: (tabName: string) => void): void {
  const tabs = Array.from(document.querySelectorAll<HTMLButtonElement>(".tab-btn"));
  const panels = Array.from(document.querySelectorAll<HTMLElement>(".tab-panel"));

  const activate = (btn: HTMLButtonElement, focusTab = false): void => {
    const target = btn.dataset.tab;
    tabs.forEach((t) => {
      const active = t === btn;
      t.classList.toggle("active", active);
      t.setAttribute("aria-selected", String(active));
      t.tabIndex = active ? 0 : -1;
    });
    panels.forEach((p) => {
      p.hidden = p.id !== `panel-${target}`;
    });
    if (focusTab) btn.focus();
    if (target) onTabActivated?.(target);
  };

  tabs.forEach((btn, idx) => {
    btn.addEventListener("click", () => activate(btn));
    btn.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") {
        e.preventDefault();
        activate(tabs[(idx + 1) % tabs.length], true);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        activate(tabs[(idx - 1 + tabs.length) % tabs.length], true);
      } else if (e.key === "Home") {
        e.preventDefault();
        activate(tabs[0], true);
      } else if (e.key === "End") {
        e.preventDefault();
        activate(tabs[tabs.length - 1], true);
      }
    });
  });
}

function renderSymbolPalette(): void {
  const grid = $("symbol-palette");
  grid.innerHTML = "";
  for (const item of TRADITIONAL_SYMBOLS_PALETTE) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "symbol-chip";
    btn.title = `${item.name_ta} (${item.name_en}) — ${item.value_label} [${item.codepoint}]`;
    btn.innerHTML = `<span class="sym-glyph">${item.glyph}</span><span class="sym-name">${item.name_ta}</span><span class="sym-val">${item.value_label}</span>`;
    btn.addEventListener("click", () => {
      void runGuarded(async () => {
        const insertMode = ($("symbol-insert-mode") as HTMLSelectElement).value;
        const payload =
          insertMode === "glyph-name"
            ? `${item.glyph} (${item.name_ta})`
            : insertMode === "name"
              ? item.name_ta
              : item.glyph;
        if (isWordHost()) {
          await insertAtCursor(payload, true);
          setStatus(`Inserted ${payload}`, "success");
        } else {
          await navigator.clipboard?.writeText(payload).catch(() => {});
          setStatus(`Copied ${payload}`, "info");
        }
      });
    });
    grid.appendChild(btn);
  }
}

async function runGuarded(task: () => Promise<void>): Promise<void> {
  setBusy(true);
  setLiveTypingSuspended(true);
  try {
    await initTamilEngine();
    await task();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    setStatus(`Error: ${msg}`, "error");
  } finally {
    setLiveTypingSuspended(false);
    setBusy(false);
  }
}

const KEYBOARD_LAYOUT_META: Record<
  KeyboardLayout,
  {
    label: string;
    desc: string;
    placeholder: string;
    keymapTitle: string;
    keys: Array<[string, string]>;
  }
> = {
  "phonetic-v1": {
    label: "Phonetic",
    desc: "Turn ON, click on your Word page, and type Phonetic Tanglish + Space (e.g. vanakkam, malai). Live Mayangoli choices appear below.",
    placeholder: "e.g. vanakkam thamizh (Space/1-5/↑↓ pick · Ctrl+Enter insert)...",
    keymapTitle: "Quick Key Guide (Phonetic Tanglish)",
    keys: [
      ["அ / ஆ", "a / aa"],
      ["இ / ஈ", "i / ee"],
      ["உ / ஊ", "u / oo"],
      ["எ / ஏ / ஐ", "e / ae / ai"],
      ["ஒ / ஓ / ஔ", "o / oa / au"],
      ["க / ங / ச", "k / ng / ch"],
      ["ட / ண / த", "t / N / th"],
      ["ந / ன / ம", "nh / n / m"],
      ["ர / ற / ல", "r / R / l"],
      ["ள / ழ / வ", "L / zh / v"],
      ["ற்ற / ன்ற", "ttr / ndr"],
      ["தமிழ்", "thamizh"],
    ],
  },
  "anjal-phonetic": {
    label: "Anjal Phonetic",
    desc: "Turn ON, click on your Word page, and type Anjal Phonetic + Space (e.g. vaNakkam, thamizh). Live Mayangoli choices appear below.",
    placeholder: "e.g. vaNakkam thamizh (Space/1-5/↑↓ pick · Ctrl+Enter insert)...",
    keymapTitle: "Quick Key Guide (Anjal Phonetic)",
    keys: [
      ["அ / ஆ", "a / aa"],
      ["இ / ஈ", "i / ii"],
      ["உ / ஊ", "u / uu"],
      ["எ / ஏ / ஐ", "e / ee / ai"],
      ["ஒ / ஓ / ஔ", "o / oo / au"],
      ["க / ங / ச", "k / ng / ch"],
      ["ட / ண / த", "t / N / th"],
      ["ந / ன / ம", "w / W / m"],
      ["ர / ற / ல", "r / R / l"],
      ["ள / ழ / வ", "L / z / v"],
      ["ற்ற / ன்ற", "ttr / ndr"],
      ["தமிழ்", "thamizh"],
    ],
  },
  tamil99: {
    label: "Tamil99",
    desc: "Turn ON, click on your Word page, and type official Tamil99 keys (e.g. lks/f → தமிழ்). Auto-handles pulli for doubled/nasal stops.",
    placeholder: "e.g. lks/f → தமிழ் (Ctrl+Enter insert)...",
    keymapTitle: "Quick Key Guide (Tamil99)",
    keys: [
      ["அ / ஆ", "a / q"],
      ["இ / ஈ", "s / w"],
      ["உ / ஊ", "d / e"],
      ["எ / ஏ / ஐ", "g / t / r"],
      ["ஒ / ஓ / ஔ", "c / x / z"],
      ["க / ங / ச", "h / b / ["],
      ["ட / ண / த", "o / p / l"],
      ["ந / ப / ம", "; / j / k"],
      ["ர / ற / ல", "m / u / n"],
      ["ள / ழ / வ", "y / / / v"],
      ["் (Pulli)", "f"],
      ["தமிழ்", "lks/f"],
    ],
  },
  bamini: {
    label: "Bamini",
    desc: "Turn ON, click on your Word page, and type Bamini keys (e.g. jkpo; → தமிழ்). Keys convert live to Unicode as you type.",
    placeholder: "e.g. jkpo; → தமிழ் (Ctrl+Enter insert)...",
    keymapTitle: "Quick Key Guide (Bamini)",
    keys: [
      ["க / ச / ட", "f / r / l"],
      ["த / ப / ம", "j / g / k"],
      ["ழ / வ / ண", "o / t / z"],
      ["் (Pulli)", ";"],
      ["ா", "h"],
      ["ி / ீ", "p / P"],
      ["ெ / ே", "n / N"],
      ["ை", "i"],
      ["தமிழ்", "jkpo;"],
    ],
  },
};

function wireTypeTab(): () => void {
  const toggleBtn = $("btn-direct-toggle") as HTMLButtonElement;
  const badge = $("direct-mode-badge");
  const layoutSelect = $("type-layout") as HTMLSelectElement;
  const fontSelect = $("type-font") as HTMLSelectElement;
  const directDesc = $("direct-typing-desc");
  const keymapSummary = $("keymap-summary");
  const keymapGrid = $("keymap-grid");
  const canvasCandidatesEl = $("canvas-candidates");
  const translitInput = $("translit-input") as HTMLTextAreaElement;
  const translitCandidatesEl = $("translit-candidates");
  const translitOutput = $("translit-output");
  const clearOpt = $("opt-composer-clear") as HTMLInputElement;

  const COMPOSER_WORD_RE = /([A-Za-z][A-Za-z_-]*)$/;
  let currentTranslit = "";
  let activeCandidates: string[] = [];
  let selectedCandidateIndex = 0;
  let activeCandidateWord = "";
  let escapedComposerWord = "";
  let docCandidateWord = "";
  let docCandidates: string[] = [];
  let docSelectedCandidateIndex = 0;
  const lastRenderKeys = new WeakMap<HTMLElement, string>();
  let lastRenderedKeymapKey = "";
  let docRefreshTimer: number | null = null;
  let isLiveActive = false;

  const getLayout = (): KeyboardLayout => layoutSelect.value as KeyboardLayout;

  const isSuggestLayout = (layout: KeyboardLayout): boolean =>
    layout === "phonetic-v1" || layout === "anjal-phonetic";

  const renderKeyGuide = (layout: KeyboardLayout): void => {
    const meta = KEYBOARD_LAYOUT_META[layout];
    keymapSummary.textContent = meta.keymapTitle;
    if (lastRenderedKeymapKey === layout) return;
    lastRenderedKeymapKey = layout;
    keymapGrid.replaceChildren();
    for (const [label, key] of meta.keys) {
      const cell = document.createElement("div");
      cell.className = "keymap-cell";
      const span = document.createElement("span");
      span.textContent = label;
      const kbd = document.createElement("kbd");
      kbd.textContent = key;
      cell.append(span, kbd);
      keymapGrid.appendChild(cell);
    }
  };

  const syncLayoutCopy = (): void => {
    const layout = getLayout();
    const meta = KEYBOARD_LAYOUT_META[layout];
    directDesc.textContent = meta.desc;
    toggleBtn.textContent = isLiveActive
      ? `Stop Live Word Typing (${meta.label} · LIVE)`
      : `Start Live Word Typing (${meta.label} → Unicode)`;
    translitInput.placeholder = meta.placeholder;
    renderKeyGuide(layout);
  };

  // Keep Taskpane UI & live Word Mayangoli candidates in sync
  subscribeLiveTyping((state, status) => {
    isLiveActive = state.active;
    badge.textContent = state.active ? "LIVE" : "OFF";
    badge.style.color = state.active ? "var(--success-fg)" : "";
    toggleBtn.className = state.active ? "btn btn-danger" : "btn btn-primary";
    syncLayoutCopy();

    if (status?.message && status.kind) {
      setStatus(status.message, status.kind);
    }

    if (isTamilEngineReady() && status) {
      if (status.pendingWord && isSuggestLayout(state.layout)) {
        const cands = getCanvasMayangoliCandidates(status.pendingWord, state.layout, 5);
        if (cands.length > 0) {
          if (docCandidateWord !== status.pendingWord) {
            docSelectedCandidateIndex = 0;
          } else {
            docSelectedCandidateIndex = Math.min(docSelectedCandidateIndex, cands.length - 1);
          }
          docCandidateWord = status.pendingWord;
          docCandidates = cands;
          renderCandidateBar("document", cands, docSelectedCandidateIndex);
          return;
        }
      }
      if (status.activeTamilWord && isSuggestLayout(state.layout)) {
        const cands = getCanvasMayangoliCandidates(status.activeTamilWord, state.layout, 5);
        if (cands.length > 1) {
          const idx = Math.max(0, cands.indexOf(status.activeTamilWord));
          docCandidateWord = status.activeTamilWord;
          docCandidates = cands;
          docSelectedCandidateIndex = idx;
          renderCandidateBar("document", cands, idx);
          return;
        }
      }
      if ("pendingWord" in status || "activeTamilWord" in status) {
        docCandidateWord = "";
        docCandidates = [];
        docSelectedCandidateIndex = 0;
        renderCandidateBar("document", [], 0);
      }
    }
  });

  layoutSelect.addEventListener("change", () => {
    configureLiveTyping({ layout: getLayout() });
    syncLayoutCopy();
    updateTranslitPreview(true);
  });
  fontSelect.addEventListener("change", () => {
    configureLiveTyping({ font: fontSelect.value });
  });

  toggleBtn.addEventListener("click", () => {
    configureLiveTyping({
      layout: getLayout(),
      font: fontSelect.value,
    });
    void toggleLiveTyping();
  });

  $("btn-convert-active-para").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) {
        setStatus("Open inside Microsoft Word to convert active paragraph.", "info");
        return;
      }
      const layout = getLayout();
      const summary = await runKeyboardToUnicode("paragraph", layout, fontSelect.value);
      setStatus(
        `Converted active paragraph (${KEYBOARD_LAYOUT_META[layout].label} → Unicode, ${summary.rangesModified} updated).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  $("btn-convert-selection").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) {
        setStatus("Open inside Microsoft Word to convert selection.", "info");
        return;
      }
      const layout = getLayout();
      const summary = await runKeyboardToUnicode("selection", layout, fontSelect.value);
      if (summary.rangesProcessed === 0) {
        setStatus("Select text in Word first (or click Convert Paragraph).", "info");
        return;
      }
      setStatus(
        `Converted selection (${KEYBOARD_LAYOUT_META[layout].label} → Unicode, ${summary.rangesModified} updated).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  const applyDocCandidate = async (idx: number): Promise<void> => {
    const cand = docCandidates[idx];
    const targetWord = docCandidateWord;
    if (!cand || !targetWord) return;
    docSelectedCandidateIndex = idx;
    renderCandidateBar("document", docCandidates, idx);
    if (targetWord === cand) return;

    await runGuarded(async () => {
      const ok = await replaceTrailingOrSelectedWord(targetWord, cand, fontSelect.value || undefined);
      if (ok) {
        docCandidateWord = cand;
        docSelectedCandidateIndex = idx;
        renderCandidateBar("document", docCandidates, idx);
        setStatus(`Replaced "${targetWord}" → "${cand}" in Word.`, "success");
      }
    });
  };

  const renderCandidateBar = (
    mode: "composer" | "document",
    candidates: string[],
    selectedIdx: number
  ): void => {
    const container = mode === "document" ? canvasCandidatesEl : translitCandidatesEl;
    const visible =
      candidates.length > 0 &&
      (mode !== "document" || candidates.length > 1 || /^[A-Za-z]/.test(docCandidateWord));
    const currentWord = mode === "document" ? docCandidateWord : activeCandidateWord;
    const renderKey = visible
      ? `${mode}|${currentWord}|${selectedIdx}|${candidates.join("\u0001")}`
      : "hidden";
    if (lastRenderKeys.get(container) === renderKey) {
      return;
    }
    lastRenderKeys.set(container, renderKey);

    container.replaceChildren();
    if (!visible) {
      container.hidden = true;
      return;
    }

    container.hidden = false;
    candidates.forEach((cand, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = idx === selectedIdx ? "candidate-chip active" : "candidate-chip";
      const num = document.createElement("span");
      num.className = "candidate-num";
      num.textContent = String(idx + 1);
      const label = document.createElement("span");
      label.textContent = cand;
      btn.append(num, label);
      btn.addEventListener("mousedown", (e) => e.preventDefault());
      btn.addEventListener("click", () => {
        if (mode === "composer") {
          commitComposerCandidate(idx, " ");
        } else {
          void applyDocCandidate(idx);
        }
      });
      container.appendChild(btn);
    });

    if (mode === "composer" && candidates.length > 1) {
      const hint = document.createElement("div");
      hint.className = "candidate-hint";
      hint.textContent = `↑↓ / Tab cycle · 1–${candidates.length} / Space / Enter select`;
      container.appendChild(hint);
    } else if (mode === "document") {
      const hint = document.createElement("div");
      hint.className = "candidate-hint";
      hint.textContent = `Before Space: 1–${candidates.length} / Tab / "/" cycle · or click`;
      container.appendChild(hint);
    }
  };

  const commitComposerCandidate = (index: number, trailing = " "): boolean => {
    if (index < 0 || index >= activeCandidates.length) return false;
    const caret = translitInput.selectionStart ?? translitInput.value.length;
    const before = translitInput.value.slice(0, caret);
    const match = before.match(COMPOSER_WORD_RE);
    if (!match) return false;

    const word = match[1];
    const chosen = activeCandidates[index];
    if (!chosen || chosen === word) return false;

    const wordStart = caret - word.length;
    const nextValue =
      translitInput.value.slice(0, wordStart) + chosen + trailing + translitInput.value.slice(caret);
    const nextCaret = wordStart + chosen.length + trailing.length;
    translitInput.value = nextValue;
    translitInput.setSelectionRange(nextCaret, nextCaret);
    activeCandidateWord = "";
    activeCandidates = [];
    selectedCandidateIndex = 0;
    escapedComposerWord = "";
    updateTranslitPreview(true);
    translitInput.focus();
    return true;
  };

  const updateTranslitPreview = (resetCandidateIndex = true): void => {
    const layout = getLayout();
    const raw = translitInput.value;
    if (!raw) {
      currentTranslit = "";
      activeCandidateWord = "";
      activeCandidates = [];
      selectedCandidateIndex = 0;
      escapedComposerWord = "";
      translitOutput.innerHTML = '<span class="live-output-empty">Live Tamil preview...</span>';
      renderCandidateBar("composer", [], 0);
      return;
    }
    if (!isTamilEngineReady()) return;

    try {
      if (isSuggestLayout(layout)) {
        const caret = translitInput.selectionStart ?? raw.length;
        const beforeCaret = raw.slice(0, caret);
        const afterCaret = raw.slice(caret);
        const match = beforeCaret.match(COMPOSER_WORD_RE);
        if (match && escapedComposerWord !== match[1]) {
          escapedComposerWord = "";
          const word = match[1];
          if (resetCandidateIndex || word !== activeCandidateWord || activeCandidates.length === 0) {
            activeCandidateWord = word;
            activeCandidates = transliterateSuggestText(word, layout, 5);
            selectedCandidateIndex = 0;
          }
          const chosen = activeCandidates[selectedCandidateIndex] ?? activeCandidates[0] ?? "";
          const prefixRaw = beforeCaret.slice(0, beforeCaret.length - word.length);
          const prefixTamil = prefixRaw ? convertKeyboardToUnicode(prefixRaw, layout) : "";
          const suffixTamil = afterCaret ? convertKeyboardToUnicode(afterCaret, layout) : "";
          currentTranslit = `${prefixTamil}${chosen}${suffixTamil}`;
          translitOutput.textContent = currentTranslit;
          renderCandidateBar("composer", activeCandidates, selectedCandidateIndex);
          return;
        }
      }

      activeCandidateWord = "";
      activeCandidates = [];
      selectedCandidateIndex = 0;
      renderCandidateBar("composer", [], 0);
      currentTranslit = convertKeyboardToUnicode(raw, layout);
      translitOutput.textContent = currentTranslit;
    } catch (err) {
      currentTranslit = "";
      activeCandidates = [];
      renderCandidateBar("composer", [], 0);
      translitOutput.textContent = err instanceof Error ? err.message : String(err);
    }
  };

  const refreshDocMayangoliCandidates = async (): Promise<void> => {
    if (!isWordHost() || !isTamilEngineReady()) return;
    try {
      const word = await readWordAtCursorOrSelection();
      if (!word) {
        docCandidateWord = "";
        docCandidates = [];
        docSelectedCandidateIndex = 0;
        renderCandidateBar("document", [], 0);
        return;
      }
      const layout = getLayout();
      const scheme = layout === "anjal-phonetic" ? "anjal-phonetic" : "phonetic-v1";
      const isLatinPending = /^[A-Za-z][A-Za-z_-]*$/.test(word) && isSuggestLayout(layout);
      const isTamilWord = /[\u0B80-\u0BFF]/.test(word);
      if (!isLatinPending && !isTamilWord) {
        docCandidateWord = "";
        docCandidates = [];
        docSelectedCandidateIndex = 0;
        renderCandidateBar("document", [], 0);
        return;
      }
      const cands = getCanvasMayangoliCandidates(word, scheme, 5);
      if (cands.length > 1 || (isLatinPending && cands.length > 0)) {
        const idx = Math.max(0, cands.indexOf(word));
        docCandidateWord = word;
        docCandidates = cands;
        docSelectedCandidateIndex = idx;
        renderCandidateBar("document", cands, idx);
      } else {
        docCandidateWord = "";
        docCandidates = [];
        docSelectedCandidateIndex = 0;
        renderCandidateBar("document", [], 0);
      }
    } catch {
      // Ignore transient Word selection read errors
    }
  };

  if (isWordHost()) {
    try {
      Office.context?.document?.addHandlerAsync(Office.EventType.DocumentSelectionChanged, () => {
        if (isLiveTypingActive()) return;
        if (docRefreshTimer !== null) window.clearTimeout(docRefreshTimer);
        docRefreshTimer = window.setTimeout(() => {
          void refreshDocMayangoliCandidates();
        }, 180);
      });
    } catch {
      // Optional event subscription
    }
  }

  const insertTranslit = async (): Promise<void> => {
    updateTranslitPreview(false);
    if (!currentTranslit.trim()) {
      setStatus("Type text to insert first.", "error");
      return;
    }
    if (isWordHost()) {
      await insertAtCursor(currentTranslit, true, fontSelect.value || undefined);
      setStatus("Inserted Unicode Tamil at cursor.", "success");
    } else {
      await navigator.clipboard?.writeText(currentTranslit).catch(() => {});
      setStatus("Copied Unicode Tamil.", "info");
    }
    if (clearOpt.checked) {
      translitInput.value = "";
      updateTranslitPreview(true);
      translitInput.focus();
    }
  };

  translitInput.addEventListener("input", () => updateTranslitPreview(true));
  translitInput.addEventListener("click", () => updateTranslitPreview(true));
  translitInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void runGuarded(insertTranslit);
      return;
    }

    const layout = getLayout();
    if (!isSuggestLayout(layout) || e.ctrlKey || e.metaKey || e.altKey) {
      return;
    }

    if (e.key === "Escape" && activeCandidates.length > 0 && activeCandidateWord) {
      e.preventDefault();
      escapedComposerWord = activeCandidateWord;
      updateTranslitPreview(false);
      return;
    }

    if (activeCandidates.length > 1 && (e.key === "ArrowDown" || (e.key === "Tab" && !e.shiftKey))) {
      e.preventDefault();
      selectedCandidateIndex = (selectedCandidateIndex + 1) % activeCandidates.length;
      updateTranslitPreview(false);
      return;
    }

    if (activeCandidates.length > 1 && (e.key === "ArrowUp" || (e.key === "Tab" && e.shiftKey))) {
      e.preventDefault();
      selectedCandidateIndex = (selectedCandidateIndex - 1 + activeCandidates.length) % activeCandidates.length;
      updateTranslitPreview(false);
      return;
    }

    if (activeCandidates.length > 0 && /^[1-5]$/.test(e.key)) {
      const idx = Number(e.key) - 1;
      if (idx < activeCandidates.length) {
        e.preventDefault();
        commitComposerCandidate(idx, " ");
        return;
      }
    }

    if (activeCandidates.length > 0 && (e.key === " " || e.key === "Enter")) {
      const suffix = e.key === " " ? " " : "";
      if (commitComposerCandidate(selectedCandidateIndex, suffix)) {
        e.preventDefault();
      }
      return;
    }

    if (
      e.key === "ArrowLeft" ||
      e.key === "ArrowRight" ||
      e.key === "Home" ||
      e.key === "End"
    ) {
      queueMicrotask(() => updateTranslitPreview(true));
    }
  });
  $("btn-translit-insert").addEventListener("click", () => void runGuarded(insertTranslit));
  $("btn-translit-copy").addEventListener("click", () => {
    void runGuarded(async () => {
      updateTranslitPreview(false);
      if (!currentTranslit) return;
      await navigator.clipboard?.writeText(currentTranslit);
      setStatus("Copied Unicode Tamil.", "success");
    });
  });

  window.addEventListener("keydown", (e) => {
    if (
      docCandidates.length === 0 ||
      canvasCandidatesEl.hidden ||
      e.ctrlKey ||
      e.metaKey ||
      e.altKey
    ) {
      return;
    }
    const target = e.target as HTMLElement | null;
    if (target && target.closest("input, textarea, select, [contenteditable='true']")) {
      return;
    }

    if (docCandidates.length > 1 && (e.key === "ArrowDown" || (e.key === "Tab" && !e.shiftKey))) {
      e.preventDefault();
      const next = (docSelectedCandidateIndex + 1) % docCandidates.length;
      void applyDocCandidate(next);
      return;
    }

    if (docCandidates.length > 1 && (e.key === "ArrowUp" || (e.key === "Tab" && e.shiftKey))) {
      e.preventDefault();
      const prev = (docSelectedCandidateIndex - 1 + docCandidates.length) % docCandidates.length;
      void applyDocCandidate(prev);
      return;
    }

    if (/^[1-5]$/.test(e.key)) {
      const idx = Number(e.key) - 1;
      if (idx < docCandidates.length) {
        e.preventDefault();
        void applyDocCandidate(idx);
      }
      return;
    }

    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      void applyDocCandidate(docSelectedCandidateIndex);
    }
  });

  // Scholarly bidirectional transliteration (ISO 15919 / Madras Lexicon / ITRANS / HK)
  const scholarlyScheme = $("scholarly-scheme") as HTMLSelectElement;
  const scholarlyDir = $("scholarly-direction") as HTMLSelectElement;
  const scholarlyInput = $("scholarly-input") as HTMLTextAreaElement;
  const scholarlyOutput = $("scholarly-output");
  let currentScholarly = "";

  const updateScholarlyPreview = (): void => {
    const raw = scholarlyInput.value;
    if (!raw) {
      currentScholarly = "";
      scholarlyOutput.innerHTML = '<span class="live-output-empty">Live scholarly transliteration preview...</span>';
      return;
    }
    if (!isTamilEngineReady()) return;
    try {
      currentScholarly = transliterateText(
        raw,
        scholarlyScheme.value,
        scholarlyDir.value as "to_tamil" | "to_latin"
      );
      scholarlyOutput.textContent = currentScholarly;
    } catch (err) {
      currentScholarly = "";
      scholarlyOutput.textContent = err instanceof Error ? err.message : String(err);
    }
  };

  const insertScholarly = async (): Promise<void> => {
    updateScholarlyPreview();
    if (!currentScholarly.trim()) {
      setStatus("Type scholarly text first.", "error");
      return;
    }
    if (isWordHost()) {
      await insertAtCursor(currentScholarly, true, fontSelect.value || undefined);
      setStatus("Inserted transliterated text at cursor.", "success");
    } else {
      await navigator.clipboard?.writeText(currentScholarly).catch(() => {});
      setStatus("Copied transliterated text.", "info");
    }
  };

  scholarlyInput.addEventListener("input", updateScholarlyPreview);
  scholarlyScheme.addEventListener("change", updateScholarlyPreview);
  scholarlyDir.addEventListener("change", updateScholarlyPreview);
  scholarlyInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void runGuarded(insertScholarly);
    }
  });
  $("btn-scholarly-insert").addEventListener("click", () => void runGuarded(insertScholarly));
  $("btn-scholarly-copy").addEventListener("click", () => {
    void runGuarded(async () => {
      updateScholarlyPreview();
      if (!currentScholarly) return;
      await navigator.clipboard?.writeText(currentScholarly);
      setStatus("Copied transliterated text.", "success");
    });
  });

  syncLayoutCopy();
  updateTranslitPreview(true);
  updateScholarlyPreview();
  return syncLayoutCopy;
}

function wirePrepareTab(): (quiet?: boolean) => Promise<void> {
  const getPrepareScope = (): TargetScope =>
    ($("prepare-scope") as HTMLSelectElement).value as TargetScope;
  const inspectBadge = $("inspect-scope-badge");
  let inspectTimer: number | null = null;

  $("btn-prepare-run").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) {
        setStatus("Open inside Microsoft Word to prepare a document.", "info");
        return;
      }
      const scope = getPrepareScope();
      const summary = await runPrepareLegacyDocument(
        {
          scope,
          includeHeadersFooters: ($("opt-prep-headers") as HTMLInputElement).checked,
          convertLegacy: ($("opt-prep-convert") as HTMLInputElement).checked,
          sourceEncoding: ($("legacy-source-encoding") as HTMLSelectElement).value as LegacyEncoding,
          unicodeFont: ($("unicode-font-family") as HTMLSelectElement).value,
          repairUnicode: ($("opt-prep-repair") as HTMLInputElement).checked,
          stripZeroWidth: false,
          stripSoftHyphens: false,
          hyphenate: ($("opt-prep-hyphen") as HTMLInputElement).checked,
          leftMin: Number.parseInt(($("left-min") as HTMLInputElement).value, 10) || 3,
          rightMin: Number.parseInt(($("right-min") as HTMLInputElement).value, 10) || 3,
          useNativeSoftHyphen: true,
        },
        (p) => setStatus(`Preparing ${p.processed}/${p.total} range(s)...`, "info")
      );
      if (summary.rangesProcessed === 0) {
        setStatus(`No text found in ${scope}.`, "info");
        return;
      }
      const failedSuffix = summary.rangesFailed > 0 ? `, ${summary.rangesFailed} skipped` : "";
      setStatus(
        `Done: ${summary.rangesModified}/${summary.rangesProcessed} updated${failedSuffix}.`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  $("btn-find-replace").addEventListener("click", () => {
    void runGuarded(async () => {
      const query = ($("find-query") as HTMLInputElement).value;
      const replacement = ($("replace-value") as HTMLInputElement).value;
      const fuzzy = ($("opt-fuzzy-mayangoli") as HTMLInputElement).checked;
      if (!query.trim()) {
        setStatus("Enter Tamil text to find.", "error");
        return;
      }
      if (!isWordHost()) return;
      const res = await runTamilFindAndReplace(getPrepareScope(), query, replacement, fuzzy);
      setStatus(
        `Replaced ${res.totalReplacements} match(es) across ${res.paragraphsUpdated} paragraph(s).`,
        res.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  $("btn-sort-paragraphs").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const profile = ($("sort-profile") as HTMLSelectElement).value as CollationProfile;
      const descending = ($("sort-direction") as HTMLSelectElement).value === "desc";
      const ignoreLeadingNumbers = ($("opt-ignore-prefix") as HTMLInputElement).checked;
      const res = await runSortSelectionParagraphs({ profile, descending, ignoreLeadingNumbers });
      setStatus(
        res.sortedCount >= 2 ? `Sorted ${res.sortedCount} paragraphs (${profile}).` : "Select 2+ paragraphs to sort.",
        res.sortedCount >= 2 ? "success" : "info"
      );
    });
  });

  $("btn-sort-table").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const profile = ($("sort-profile") as HTMLSelectElement).value as CollationProfile;
      const descending = ($("sort-direction") as HTMLSelectElement).value === "desc";
      const columnIndex = Math.max(
        0,
        (Number.parseInt(($("sort-col-index") as HTMLInputElement).value, 10) || 1) - 1
      );
      const hasHeader = ($("opt-table-header") as HTMLInputElement).checked;
      const res = await runSortSelectedTable({ columnIndex, hasHeader, descending, profile });
      setStatus(
        res.sortedRows > 0 ? `Sorted ${res.sortedRows} table row(s).` : "Place cursor in a table with 2+ rows.",
        res.sortedRows > 0 ? "success" : "info"
      );
    });
  });

  const getMargins = () => ({
    leftMin: Math.max(1, Math.min(5, Number.parseInt(($("left-min") as HTMLInputElement).value, 10) || 3)),
    rightMin: Math.max(1, Math.min(5, Number.parseInt(($("right-min") as HTMLInputElement).value, 10) || 3)),
  });

  $("btn-hyphen-sel").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const { leftMin, rightMin } = getMargins();
      const s = await runHyphenation("selection", { leftMin, rightMin, useNativeSoftHyphen: true, toggle: false });
      setStatus(`Soft-hyphenated ${s.rangesModified}/${s.rangesProcessed} range(s).`, "success");
    });
  });

  $("btn-hyphen-doc").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const { leftMin, rightMin } = getMargins();
      const s = await runHyphenation(
        "document",
        { leftMin, rightMin, useNativeSoftHyphen: true, toggle: false },
        (p) => setStatus(`Hyphenating ${p.processed}/${p.total}...`, "info")
      );
      setStatus(`Soft-hyphenated ${s.rangesModified}/${s.rangesProcessed} paragraph(s).`, "success");
    });
  });

  $("btn-wrap-nohyphen").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const { leftMin, rightMin } = getMargins();
      const s = await runHyphenation(
        "document",
        { leftMin, rightMin, useNativeSoftHyphen: false, toggle: false },
        (p) => setStatus(`Wrapping ${p.processed}/${p.total}...`, "info")
      );
      setStatus(`Applied invisible wrap to ${s.rangesModified} paragraph(s) (no '-').`, "success");
    });
  });

  $("btn-remove-hyphens").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const s = await runRemoveHyphens("document", (p) =>
        setStatus(`Cleaning ${p.processed}/${p.total}...`, "info")
      );
      setStatus(`Removed hyphens from ${s.rangesModified} paragraph(s).`, "success");
    });
  });

  $("btn-unicode-to-legacy").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const target = ($("legacy-target-encoding") as HTMLSelectElement).value as TargetLegacyEncoding;
      const s = await runUnicodeToLegacy(getPrepareScope(), target, (p) =>
        setStatus(`Encoding ${p.processed}/${p.total}...`, "info")
      );
      setStatus(`Encoded ${s.rangesModified} range(s) to ${target.toUpperCase()}.`, "success");
    });
  });

  const runInspect = async (
    scope: TargetScope,
    quiet = false,
    preloadedText?: string
  ): Promise<void> => {
    const text =
      preloadedText !== undefined
        ? preloadedText
        : isWordHost()
          ? await readTargetText(scope)
          : "தமிழ் மொழி இனிமையானது.";
    const report = inspectDocumentText(text);
    inspectBadge.textContent = !isWordHost()
      ? "Preview"
      : scope === "selection"
        ? "Selection"
        : "Document";
    $("inspect-results").innerHTML = `
      <div class="stat-grid">
        <div class="stat-card"><span>Words</span><strong>${report.word_count}</strong></div>
        <div class="stat-card"><span>Tamil Letters</span><strong>${report.letter_count}</strong></div>
        <div class="stat-card"><span>Syllables</span><strong>${report.syllable_count}</strong></div>
        <div class="stat-card"><span>NFC Clean</span><strong>${report.is_nfc ? "Yes" : "No"}</strong></div>
      </div>
      <div class="breakdown-list">
        <div>உயிர் (Uyir): <strong>${report.uyir_count}</strong></div>
        <div>மெய் (Mei): <strong>${report.mei_count}</strong></div>
        <div>உயிர்மெய் (Uyirmei): <strong>${report.uyirmei_count}</strong></div>
        <div>ஆய்தம் (Aytham): <strong>${report.aytham_count}</strong></div>
        <div>கிரந்தம் (Grantha): <strong>${report.grantha_count}</strong></div>
        <div>Other / Latin: <strong>${report.other_count}</strong></div>
        <div>Soft Hyphens: <strong>${report.soft_hyphen_count}</strong></div>
        <div>Zero-Width: <strong>${report.zero_width_count}</strong></div>
      </div>
    `;
    if (!quiet) {
      setStatus(`Inspected ${report.word_count} word(s), ${report.letter_count} Tamil letter(s).`, "success");
    }
  };

  const runInspectAuto = async (quiet = true): Promise<void> => {
    if (!isTamilEngineReady()) return;
    try {
      if (!isWordHost()) {
        await runInspect("document", quiet);
        return;
      }
      const sel = await readTargetText("selection");
      if (sel.trim().length > 0) {
        await runInspect("selection", quiet, sel);
      } else {
        await runInspect("document", quiet);
      }
    } catch {
      // Ignore transient Word read errors during auto-inspect
    }
  };

  if (isWordHost()) {
    try {
      Office.context?.document?.addHandlerAsync(Office.EventType.DocumentSelectionChanged, () => {
        if ($("panel-prepare").hidden) return;
        if (inspectTimer !== null) window.clearTimeout(inspectTimer);
        inspectTimer = window.setTimeout(() => {
          void runInspectAuto(true);
        }, 250);
      });
    } catch {
      // Optional event subscription
    }
  }

  $("btn-inspect-sel").addEventListener("click", () => void runGuarded(() => runInspect("selection")));
  $("btn-inspect-doc").addEventListener("click", () => void runGuarded(() => runInspect("document")));
  return runInspectAuto;
}

function wireInsertTab(): void {
  const dateInput = $("cal-date") as HTMLInputElement;
  const now = new Date();
  dateInput.value = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  let lastStamp: ReturnType<typeof buildTamilDateStamp> | null = null;

  const refreshCalendar = async (): Promise<void> => {
    const [y, m, d] = dateInput.value.split("-").map((v) => Number.parseInt(v, 10));
    if (!y || !m || !d) return;
    const profile = ($("cal-profile") as HTMLSelectElement).value as CalendarProfile;
    const region = ($("cal-region") as HTMLSelectElement).value as NumeralLocale;
    const includePanchangam = ($("opt-cal-panchangam") as HTMLInputElement).checked;

    const stamp = buildTamilDateStamp(y, m, d, { profile, region, includePanchangam });
    lastStamp = stamp;

    $("cal-preview").innerHTML = `
      <div><strong>${stamp.formatted_short}</strong></div>
      <div class="meta-line">திருவள்ளுவர் ஆண்டு ${stamp.thiruvalluvar_year} · ${stamp.jovian_year} · ${stamp.profile_label}</div>
      ${stamp.tithi || stamp.nakshatra ? `<div class="meta-line">${[stamp.tithi, stamp.nakshatra, stamp.yogam, stamp.karanam].filter(Boolean).join(" · ")}</div>` : ""}
      ${stamp.holiday_name ? `<div class="holiday-pill">${region} Holiday: ${stamp.holiday_name}</div>` : ""}
    `;
  };

  $("btn-cal-refresh").addEventListener("click", () => {
    void runGuarded(async () => {
      await refreshCalendar();
      setStatus("Tamil date updated.", "success");
    });
  });

  $("btn-cal-insert-short").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!lastStamp) await refreshCalendar();
      if (lastStamp && isWordHost()) {
        await insertAtCursor(lastStamp.formatted_short, true);
        setStatus("Inserted short Tamil date.", "success");
      }
    });
  });

  $("btn-cal-insert-formal").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!lastStamp) await refreshCalendar();
      if (!lastStamp) return;
      const text = ($("opt-cal-panchangam") as HTMLInputElement).checked
        ? lastStamp.formatted_panchangam
        : lastStamp.formatted_formal;
      if (isWordHost()) {
        await insertAtCursor(text, true);
        setStatus("Inserted formal Tamil date header.", "success");
      }
    });
  });

  const numInputEl = $("num-input") as HTMLInputElement;
  const numModeEl = $("num-mode") as HTMLSelectElement;
  const numLocaleEl = $("num-locale") as HTMLSelectElement;
  const numCurrencyEl = $("num-currency") as HTMLSelectElement;
  const numOutputEl = $("num-output") as HTMLTextAreaElement;

  const computeNumPreview = (): string => {
    const raw = numInputEl.value.trim();
    const mode = numModeEl.value as
      | "cardinal"
      | "decimal"
      | "ordinal"
      | "currency"
      | "traditional"
      | "words_to_number";
    const locale = numLocaleEl.value as NumeralLocale;
    const currency = numCurrencyEl.value as SupportedCurrency;

    if (!raw) return "";
    if (mode === "traditional") {
      return formatTraditionalInteger(Number.parseInt(raw.replace(/,/g, ""), 10));
    }
    if (mode === "words_to_number") {
      return String(wordsToNumber(raw, locale));
    }
    return numberToTamilWords(raw, mode, { locale, currency });
  };

  const updateNumOutputLive = (): void => {
    if (!isTamilEngineReady()) return;
    if (!numInputEl.value.trim()) {
      numOutputEl.value = "";
      return;
    }
    try {
      numOutputEl.value = computeNumPreview();
    } catch {
      // Ignore partial intermediate input while typing
    }
  };

  numInputEl.addEventListener("input", updateNumOutputLive);
  numModeEl.addEventListener("change", updateNumOutputLive);
  numLocaleEl.addEventListener("change", updateNumOutputLive);
  numCurrencyEl.addEventListener("change", updateNumOutputLive);

  void initTamilEngine()
    .then(() => {
      updateNumOutputLive();
      return refreshCalendar();
    })
    .catch(() => {});

  $("btn-num-preview").addEventListener("click", () => {
    if (isTamilEngineReady()) {
      try {
        numOutputEl.value = computeNumPreview();
        setStatus("Tamil words ready.", "success");
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setStatus(`Error: ${msg}`, "error");
      }
      return;
    }
    void runGuarded(async () => {
      numOutputEl.value = computeNumPreview();
      setStatus("Tamil words ready.", "success");
    });
  });

  $("btn-num-from-selection").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const sel = (await readTargetText("selection")).trim();
      ($("num-input") as HTMLInputElement).value = sel;
      ($("num-output") as HTMLTextAreaElement).value = computeNumPreview();
      setStatus("Loaded selection and formatted Tamil words.", "success");
    });
  });

  $("btn-num-insert").addEventListener("click", () => {
    void runGuarded(async () => {
      const out = ($("num-output") as HTMLTextAreaElement).value.trim() || computeNumPreview();
      ($("num-output") as HTMLTextAreaElement).value = out;
      if (!out) return;
      if (isWordHost()) {
        await insertAtCursor(out, true);
        setStatus("Inserted Tamil numeral words.", "success");
      }
    });
  });

  $("btn-digits-to-tamil").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const sel = await readTargetText("selection");
      await insertAtCursor(convertDigits(sel, "tamil"), true);
      setStatus("Converted digits to Tamil (௦–௯).", "success");
    });
  });

  $("btn-digits-to-latin").addEventListener("click", () => {
    void runGuarded(async () => {
      if (!isWordHost()) return;
      const sel = await readTargetText("selection");
      await insertAtCursor(convertDigits(sel, "latin"), true);
      setStatus("Converted digits to Arabic/Latin (0–9).", "success");
    });
  });
}

function bootstrap(): void {
  syncWordTheme();

  let currentLang: UiLang = getSavedLang();
  applyLanguage(currentLang);

  // Share Ribbon command execution & status bar in SharedRuntime
  registerRibbonCommands(setStatus);

  renderSymbolPalette();
  const syncLayoutCopy = wireTypeTab();
  const refreshInspect = wirePrepareTab();
  wireInsertTab();
  initTabs((tab) => {
    if (tab === "prepare") {
      void refreshInspect(true);
    }
  });

  $("btn-lang-toggle").addEventListener("click", () => {
    currentLang = currentLang === "en" ? "ta" : "en";
    saveLang(currentLang);
    applyLanguage(currentLang);
    syncLayoutCopy();
  });

  if (!isWordHost()) {
    const banner = $("host-banner");
    banner.hidden = false;
    banner.textContent = "Browser Preview — Open inside Microsoft Word for direct document editing.";
  }

  void initTamilEngine()
    .then(() => {
      setStatus("Ready · 100% local Rust/WASM", "success");
      if (!isWordHost() || !$("panel-prepare").hidden) {
        void refreshInspect(true);
      }
    })
    .catch((err) => setStatus(`Engine init failed: ${String(err)}`, "error"));
}

if (typeof Office !== "undefined" && typeof Office.onReady === "function") {
  Office.onReady(() => bootstrap());
} else {
  window.addEventListener("DOMContentLoaded", bootstrap);
}
