import { registerRibbonCommands } from "./commands.js";
import { STRINGS, UiLang, getSavedLang, saveLang } from "./lib/i18n.js";
import {
  configureLiveTyping,
  subscribeLiveTyping,
  toggleLiveTyping,
} from "./lib/live-typing.js";
import {
  CalendarProfile,
  CollationProfile,
  LegacyEncoding,
  NumeralLocale,
  SupportedCurrency,
  TRADITIONAL_SYMBOLS_PALETTE,
  TargetLegacyEncoding,
  buildTamilDateStamp,
  convertDigits,
  convertLegacyToUnicode,
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
  insertAtCursor,
  isWordHost,
  readTargetText,
  readWordAtCursorOrSelection,
  replaceTrailingOrSelectedWord,
  runHyphenation,
  runLegacyToUnicode,
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

function initTabs(): void {
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
  try {
    await initTamilEngine();
    await task();
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    setStatus(`Error: ${msg}`, "error");
  } finally {
    setBusy(false);
  }
}

function wireTypeTab(): void {
  const toggleBtn = $("btn-direct-toggle") as HTMLButtonElement;
  const badge = $("direct-mode-badge");
  const layoutSelect = $("type-layout") as HTMLSelectElement;
  const fontSelect = $("type-font") as HTMLSelectElement;
  const rawInput = $("type-raw-input") as HTMLTextAreaElement;
  const liveOutput = $("type-live-output");
  const clearOpt = $("opt-type-clear") as HTMLInputElement;

  let currentUnicode = "";

  // Keep Taskpane UI in sync when toggled from either the top Ribbon or the sidebar
  subscribeLiveTyping((state, status) => {
    badge.textContent = state.active ? "LIVE" : "OFF";
    badge.style.color = state.active ? "var(--success-fg)" : "";
    toggleBtn.textContent = state.active
      ? "Stop Live Word Typing (Currently LIVE)"
      : "Start Live Word Typing (Bamini → Unicode)";
    toggleBtn.className = state.active ? "btn btn-danger" : "btn btn-primary";
    if (status) {
      setStatus(status.message, status.kind);
    }
  });

  layoutSelect.addEventListener("change", () => {
    configureLiveTyping({ layout: layoutSelect.value as Exclude<LegacyEncoding, "auto"> });
  });
  fontSelect.addEventListener("change", () => {
    configureLiveTyping({ font: fontSelect.value });
  });

  toggleBtn.addEventListener("click", () => {
    configureLiveTyping({
      layout: layoutSelect.value as Exclude<LegacyEncoding, "auto">,
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
      const layout = layoutSelect.value as LegacyEncoding;
      const summary = await runLegacyToUnicode("paragraph", layout, fontSelect.value);
      setStatus(
        `Converted active paragraph (${layout.toUpperCase()} → Unicode, ${summary.rangesModified} updated).`,
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
      const layout = layoutSelect.value as LegacyEncoding;
      const summary = await runLegacyToUnicode("selection", layout, fontSelect.value);
      if (summary.rangesProcessed === 0) {
        setStatus("Select text in Word first (or click Convert Active Paragraph).", "info");
        return;
      }
      setStatus(
        `Converted selection (${layout.toUpperCase()} → Unicode, ${summary.rangesModified} updated).`,
        summary.rangesFailed > 0 ? "error" : "success"
      );
    });
  });

  const updateLivePreview = (): void => {
    const raw = rawInput.value;
    if (!raw) {
      currentUnicode = "";
      liveOutput.innerHTML = '<span class="live-output-empty">Live Unicode Tamil preview...</span>';
      return;
    }
    if (!isTamilEngineReady()) return;
    try {
      const layout = layoutSelect.value as LegacyEncoding;
      const converted = convertLegacyToUnicode(raw, layout).text;
      currentUnicode = repairTamilText(converted, {
        fixDuplicatePulli: true,
        reorderVisualVowels: true,
        stripZeroWidth: false,
      }).text;
      liveOutput.textContent = currentUnicode;
    } catch {
      currentUnicode = raw;
      liveOutput.textContent = raw;
    }
  };

  const insertTypedText = async (): Promise<void> => {
    updateLivePreview();
    if (!currentUnicode.trim()) {
      setStatus("Type Bamini keys first (e.g. jkpo;).", "error");
      return;
    }
    if (isWordHost()) {
      await insertAtCursor(currentUnicode, true, fontSelect.value || undefined);
      setStatus("Inserted Unicode Tamil at cursor.", "success");
    } else {
      await navigator.clipboard?.writeText(currentUnicode).catch(() => {});
      setStatus("Copied Unicode Tamil.", "info");
    }
    if (clearOpt.checked) {
      rawInput.value = "";
      updateLivePreview();
      rawInput.focus();
    }
  };

  rawInput.addEventListener("input", updateLivePreview);
  layoutSelect.addEventListener("change", updateLivePreview);
  rawInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void runGuarded(insertTypedText);
    }
  });

  $("btn-type-insert").addEventListener("click", () => void runGuarded(insertTypedText));
  $("btn-type-copy").addEventListener("click", () => {
    void runGuarded(async () => {
      updateLivePreview();
      if (!currentUnicode) return;
      await navigator.clipboard?.writeText(currentUnicode);
      setStatus("Copied Unicode Tamil.", "success");
    });
  });

  // Transliteration & Tamil99 Composer
  const translitScheme = $("translit-scheme") as HTMLSelectElement;
  const translitDir = $("translit-direction") as HTMLSelectElement;
  const translitInput = $("translit-input") as HTMLTextAreaElement;
  const translitCandidatesEl = $("translit-candidates");
  const translitOutput = $("translit-output");
  const KEYBOARD_ONLY_SCHEMES = new Set(["tamil99", "anjal-phonetic", "suratha-bamini"]);
  const TRANSLIT_PLACEHOLDERS: Record<string, string> = {
    "anjal-phonetic": "e.g. thamizh vaNakkam (Ctrl+Enter to insert)...",
    tamil99: "e.g. lks/f → தமிழ் (Ctrl+Enter to insert)...",
    "phonetic-v1": "e.g. vaNakkam thamizh (Ctrl+Enter to insert)...",
    "suratha-bamini": "e.g. jkpo; tzf;fk; (Ctrl+Enter to insert)...",
    "iso-15919": "e.g. tamiḻ moḻi (Ctrl+Enter to insert)...",
    "madras-lexicon": "e.g. tamiḻ nāṭu (Ctrl+Enter to insert)...",
    itrans: "e.g. tamizh vaNakkam (Ctrl+Enter to insert)...",
    "harvard-kyoto": "e.g. tamiZ vaNakkam (Ctrl+Enter to insert)...",
  };
  const COMPOSER_WORD_RE = /([A-Za-z][A-Za-z_-]*)$/;
  let currentTranslit = "";
  let activeCandidates: string[] = [];
  let selectedCandidateIndex = 0;
  let activeCandidateWord = "";
  let escapedComposerWord = "";
  let docCandidateWord = "";
  let docCandidates: string[] = [];
  let docRefreshTimer: number | null = null;

  const isSuggestScheme = (scheme: string, isKeyboardOnly: boolean): boolean =>
    (scheme === "anjal-phonetic" || scheme === "phonetic-v1") &&
    (isKeyboardOnly || translitDir.value === "to_tamil");

  const renderCandidateBar = (
    mode: "composer" | "document",
    candidates: string[],
    selectedIdx: number
  ): void => {
    translitCandidatesEl.replaceChildren();
    if (candidates.length === 0 || (mode === "document" && candidates.length <= 1)) {
      translitCandidatesEl.hidden = true;
      return;
    }

    translitCandidatesEl.hidden = false;
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
          void runGuarded(async () => {
            const targetWord = docCandidateWord;
            const ok = await replaceTrailingOrSelectedWord(targetWord, cand, fontSelect.value || undefined);
            if (ok) {
              docCandidateWord = cand;
              renderCandidateBar("document", docCandidates, idx);
              setStatus(`Replaced "${targetWord}" → "${cand}" in Word.`, "success");
            }
          });
        }
      });
      translitCandidatesEl.appendChild(btn);
    });

    if (mode === "composer" && candidates.length > 1) {
      const hint = document.createElement("div");
      hint.className = "candidate-hint";
      hint.textContent = `↑↓ / Tab cycle · 1–${candidates.length} / Space / Enter select`;
      translitCandidatesEl.appendChild(hint);
    } else if (mode === "document") {
      const hint = document.createElement("div");
      hint.className = "candidate-hint";
      hint.textContent = `Word cursor "${docCandidateWord}" · click to replace in document`;
      translitCandidatesEl.appendChild(hint);
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
    const scheme = translitScheme.value;
    const isKeyboardOnly = KEYBOARD_ONLY_SCHEMES.has(scheme);
    if (isKeyboardOnly && translitDir.value !== "to_tamil") {
      translitDir.value = "to_tamil";
    }
    translitDir.disabled = isKeyboardOnly;
    translitInput.placeholder =
      !isKeyboardOnly && translitDir.value === "to_latin"
        ? "e.g. தமிழ் வணக்கம் (Ctrl+Enter to insert)..."
        : (TRANSLIT_PLACEHOLDERS[scheme] ?? "Type text to transliterate (Ctrl+Enter to insert)...");

    const raw = translitInput.value;
    if (!raw) {
      currentTranslit = "";
      activeCandidateWord = "";
      activeCandidates = [];
      selectedCandidateIndex = 0;
      escapedComposerWord = "";
      translitOutput.innerHTML = '<span class="live-output-empty">Live transliteration preview...</span>';
      if (docCandidates.length > 1 && docCandidateWord) {
        renderCandidateBar("document", docCandidates, Math.max(0, docCandidates.indexOf(docCandidateWord)));
      } else {
        renderCandidateBar("composer", [], 0);
      }
      return;
    }
    if (!isTamilEngineReady()) return;

    try {
      const dir = (isKeyboardOnly ? "to_tamil" : translitDir.value) as "to_tamil" | "to_latin";
      if (isSuggestScheme(scheme, isKeyboardOnly)) {
        const caret = translitInput.selectionStart ?? raw.length;
        const beforeCaret = raw.slice(0, caret);
        const afterCaret = raw.slice(caret);
        const match = beforeCaret.match(COMPOSER_WORD_RE);
        if (match && escapedComposerWord !== match[1]) {
          escapedComposerWord = "";
          const word = match[1];
          if (resetCandidateIndex || word !== activeCandidateWord || activeCandidates.length === 0) {
            activeCandidateWord = word;
            activeCandidates = transliterateSuggestText(word, scheme, 5);
            selectedCandidateIndex = 0;
          }
          const chosen = activeCandidates[selectedCandidateIndex] ?? activeCandidates[0] ?? "";
          const prefixRaw = beforeCaret.slice(0, beforeCaret.length - word.length);
          const prefixTamil = prefixRaw ? transliterateText(prefixRaw, scheme, "to_tamil") : "";
          const suffixTamil = afterCaret ? transliterateText(afterCaret, scheme, "to_tamil") : "";
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
      currentTranslit = transliterateText(raw, scheme, dir);
      translitOutput.textContent = currentTranslit;
    } catch (err) {
      currentTranslit = "";
      activeCandidates = [];
      renderCandidateBar("composer", [], 0);
      translitOutput.textContent = err instanceof Error ? err.message : String(err);
    }
  };

  const refreshDocMayangoliCandidates = async (): Promise<void> => {
    if (!isWordHost() || !isTamilEngineReady() || translitInput.value.trim().length > 0) return;
    try {
      const word = await readWordAtCursorOrSelection();
      if (!word || !/[\u0B80-\u0BFF]/.test(word) || translitInput.value.trim().length > 0) {
        docCandidateWord = "";
        docCandidates = [];
        if (translitInput.value.trim().length === 0) renderCandidateBar("composer", [], 0);
        return;
      }
      const cands = transliterateSuggestText(word, "phonetic-v1", 5);
      if (cands.length > 1) {
        docCandidateWord = word;
        docCandidates = cands;
        renderCandidateBar("document", cands, Math.max(0, cands.indexOf(word)));
      } else {
        docCandidateWord = "";
        docCandidates = [];
        renderCandidateBar("composer", [], 0);
      }
    } catch {
      // Ignore transient Word selection read errors
    }
  };

  if (isWordHost()) {
    try {
      Office.context?.document?.addHandlerAsync(Office.EventType.DocumentSelectionChanged, () => {
        if (docRefreshTimer !== null) window.clearTimeout(docRefreshTimer);
        docRefreshTimer = window.setTimeout(() => {
          void refreshDocMayangoliCandidates();
        }, 180);
      });
    } catch {
      // Optional event subscription
    }
  }

  subscribeLiveTyping((_state, status) => {
    if (status?.message.startsWith("Live:") && isWordHost() && translitInput.value.trim().length === 0) {
      void refreshDocMayangoliCandidates();
    }
  });

  const insertTranslit = async (): Promise<void> => {
    updateTranslitPreview(false);
    if (!currentTranslit.trim()) {
      setStatus("Type text to transliterate first.", "error");
      return;
    }
    if (isWordHost()) {
      await insertAtCursor(currentTranslit, true, fontSelect.value || undefined);
      setStatus("Inserted transliterated text at cursor.", "success");
    } else {
      await navigator.clipboard?.writeText(currentTranslit).catch(() => {});
      setStatus("Copied transliterated text.", "info");
    }
  };

  translitInput.addEventListener("input", () => updateTranslitPreview(true));
  translitInput.addEventListener("click", () => updateTranslitPreview(true));
  translitScheme.addEventListener("change", () => updateTranslitPreview(true));
  translitDir.addEventListener("change", () => updateTranslitPreview(true));
  translitInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      void runGuarded(insertTranslit);
      return;
    }

    const scheme = translitScheme.value;
    const isKeyboardOnly = KEYBOARD_ONLY_SCHEMES.has(scheme);
    if (!isSuggestScheme(scheme, isKeyboardOnly) || e.ctrlKey || e.metaKey || e.altKey) {
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
      setStatus("Copied transliterated text.", "success");
    });
  });
  updateTranslitPreview(true);
}

function wirePrepareTab(): void {
  const getPrepareScope = (): TargetScope =>
    ($("prepare-scope") as HTMLSelectElement).value as TargetScope;

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

  const runInspect = async (scope: TargetScope) => {
    const text = isWordHost() ? await readTargetText(scope) : "தமிழ் மொழி இனிமையானது.";
    const report = inspectDocumentText(text);
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
    setStatus(`Inspected ${report.word_count} word(s), ${report.letter_count} Tamil letter(s).`, "success");
  };

  $("btn-inspect-sel").addEventListener("click", () => void runGuarded(() => runInspect("selection")));
  $("btn-inspect-doc").addEventListener("click", () => void runGuarded(() => runInspect("document")));
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
        await insertAtCursor(lastStamp.formatted_short, true, "Nirmala UI");
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
        await insertAtCursor(text, true, "Nirmala UI");
        setStatus("Inserted formal Tamil date header.", "success");
      }
    });
  });

  void initTamilEngine().then(() => refreshCalendar()).catch(() => {});

  const computeNumPreview = (): string => {
    const raw = ($("num-input") as HTMLInputElement).value.trim();
    const mode = ($("num-mode") as HTMLSelectElement).value as
      | "cardinal"
      | "decimal"
      | "ordinal"
      | "currency"
      | "traditional"
      | "words_to_number";
    const locale = ($("num-locale") as HTMLSelectElement).value as NumeralLocale;
    const currency = ($("num-currency") as HTMLSelectElement).value as SupportedCurrency;

    if (!raw) return "";
    if (mode === "traditional") {
      return formatTraditionalInteger(Number.parseInt(raw.replace(/,/g, ""), 10));
    }
    if (mode === "words_to_number") {
      return String(wordsToNumber(raw, locale));
    }
    return numberToTamilWords(raw, mode, { locale, currency });
  };

  $("btn-num-preview").addEventListener("click", () => {
    void runGuarded(async () => {
      ($("num-output") as HTMLTextAreaElement).value = computeNumPreview();
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
        await insertAtCursor(out, true, "Nirmala UI");
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
  $("btn-lang-toggle").addEventListener("click", () => {
    currentLang = currentLang === "en" ? "ta" : "en";
    saveLang(currentLang);
    applyLanguage(currentLang);
  });

  // Share Ribbon command execution & status bar in SharedRuntime
  registerRibbonCommands(setStatus);

  initTabs();
  renderSymbolPalette();
  wireTypeTab();
  wirePrepareTab();
  wireInsertTab();

  if (!isWordHost()) {
    const banner = $("host-banner");
    banner.hidden = false;
    banner.textContent = "Browser Preview — Open inside Microsoft Word for direct document editing.";
  }

  void initTamilEngine()
    .then(() => setStatus("Ready · 100% local Rust/WASM", "success"))
    .catch((err) => setStatus(`Engine init failed: ${String(err)}`, "error"));
}

if (typeof Office !== "undefined" && typeof Office.onReady === "function") {
  Office.onReady(() => bootstrap());
} else {
  window.addEventListener("DOMContentLoaded", bootstrap);
}
