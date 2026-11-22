import { getBrowserApi } from "../shared/browser-api.js";
import type { EditorKind, TypingLayout, UiLang } from "../shared/messages.js";
import {
  detectEditorKind,
  getCaretViewportRect,
  getEditorFullText,
  getTextBeforeCaret,
  replaceCharsBeforeCaret,
  replaceEditorOrSelectionText,
} from "./editor-adapter.js";
import { FloatingPill } from "./floating-pill.js";
import { HybridTypingEngine, LATIN_WORD_RE } from "./live-typing.js";

const api = getBrowserApi();

if (!(globalThis as Record<string, unknown>).__TAMIL_TOOLKIT_CONTENT_INIT__) {
  (globalThis as Record<string, unknown>).__TAMIL_TOOLKIT_CONTENT_INIT__ = true;

  let disposed = false;
  let enabled = false;
  let layout: TypingLayout = "phonetic-v1";
  let uiLang: UiLang = "en";
  let showMicroCounter = true;
  let activeEl: Element | null = null;
  let activeEditorKind: EditorKind = "none";
  let inspectDebounceTimer: number | null = null;
  let liveStreamTimer: number | null = null;
  let keyQueue: Promise<void> = Promise.resolve();

  const cleanupCallbacks: Array<() => void> = [];

  function teardownOrphan(): void {
    if (disposed) return;
    disposed = true;
    enabled = false;
    if (inspectDebounceTimer !== null) window.clearTimeout(inspectDebounceTimer);
    if (liveStreamTimer !== null) window.clearTimeout(liveStreamTimer);
    for (const fn of cleanupCallbacks) fn();
    cleanupCallbacks.length = 0;
    pill.destroy();
    delete (globalThis as Record<string, unknown>).__TAMIL_TOOLKIT_CONTENT_INIT__;
  }

  async function safeSendMessage(msg: unknown): Promise<any> {
    if (disposed || !api?.runtime?.id) {
      teardownOrphan();
      return null;
    }
    try {
      return await api.runtime.sendMessage(msg);
    } catch (err) {
      const text = err instanceof Error ? err.message : String(err);
      if (text.includes("Extension context invalidated") || !api?.runtime?.id) {
        teardownOrphan();
      }
      return null;
    }
  }

  function addDocListener<K extends keyof DocumentEventMap>(
    type: K,
    listener: (ev: DocumentEventMap[K]) => void
  ): void {
    document.addEventListener(type, listener, true);
    cleanupCallbacks.push(() => document.removeEventListener(type, listener, true));
  }

  function broadcastLiveInspect(text: string, source: "selection" | "active-editor", editable: boolean): void {
    if (disposed) return;
    if (liveStreamTimer !== null) window.clearTimeout(liveStreamTimer);
    liveStreamTimer = window.setTimeout(() => {
      void safeSendMessage({
        type: "LIVE_INSPECT_UPDATE",
        text,
        source,
        editable,
      });
    }, 120);
  }

  const transliterateViaBackground = async (raw: string, scheme: TypingLayout): Promise<string> => {
    const res = await safeSendMessage({
      type: "ENGINE_TRANSLITERATE",
      text: raw,
      scheme,
    });
    return res?.ok && typeof res.output === "string" ? res.output : raw;
  };

  const suggestViaBackground = async (raw: string, scheme: TypingLayout): Promise<string[]> => {
    const res = await safeSendMessage({
      type: "ENGINE_TRANSLITERATE",
      text: raw,
      scheme,
    });
    if (res?.ok && Array.isArray(res.candidates) && res.candidates.length > 0) {
      return res.candidates.filter((c: unknown): c is string => typeof c === "string" && c.length > 0);
    }
    if (res?.ok && typeof res.output === "string" && res.output.length > 0) {
      return [res.output];
    }
    return raw ? [raw] : [];
  };

  const typingEngine = new HybridTypingEngine(layout, transliterateViaBackground, suggestViaBackground);

  const pill = new FloatingPill({
    onToggleEnabled: () => {
      void safeSendMessage({ type: "TOGGLE_LIVE_TYPING", enabled: !enabled });
    },
    onChangeLayout: (nextLayout) => {
      layout = nextLayout;
      typingEngine.setLayout(nextLayout);
      void safeSendMessage({ type: "TOGGLE_LIVE_TYPING", enabled, layout: nextLayout });
      if (activeEl instanceof HTMLElement) {
        activeEl.focus();
      }
    },
    onScratchpadTransliterate: (raw) => transliterateViaBackground(raw, layout),
    onScratchpadInsert: (text) => {
      if (activeEl) {
        replaceCharsBeforeCaret(activeEl, 0, text);
      }
    },
    onSelectCandidate: (index) => {
      if (!activeEl) return;
      const beforeCaret = getTextBeforeCaret(activeEl);
      const result = typingEngine.commitCandidateAt(index, beforeCaret);
      if (result.handled && result.insertText !== undefined) {
        replaceCharsBeforeCaret(activeEl, result.deleteBeforeCaret ?? 0, result.insertText);
        scheduleMicroCounterUpdate(activeEl);
      }
      pill.setPreview(
        result.rawBuffer,
        result.previewText,
        getCaretViewportRect(activeEl),
        result.candidates,
        result.selectedIndex ?? 0
      );
      if (activeEl instanceof HTMLElement) {
        activeEl.focus();
      }
    },
  });

  function scheduleMicroCounterUpdate(el: Element | null): void {
    if (disposed || !el) return;
    const fullText = getEditorFullText(el);
    broadcastLiveInspect(fullText, "active-editor", true);
    if (!enabled || !showMicroCounter) return;
    if (inspectDebounceTimer !== null) window.clearTimeout(inspectDebounceTimer);
    inspectDebounceTimer = window.setTimeout(() => {
      const latestText = getEditorFullText(el);
      void safeSendMessage({
        type: "ENGINE_INSPECT",
        text: latestText,
        source: "active-editor",
        editable: true,
      }).then((res: any) => {
        if (!disposed && res?.ok && res.snapshot) {
          pill.setMicroCounter(res.snapshot.letterCount, res.snapshot.wordCount);
        }
      });
    }, 180);
  }

  addDocListener("selectionchange", () => {
    if (disposed) return;
    const selText = window.getSelection()?.toString() ?? "";
    if (selText.trim().length > 0) {
      const kind = detectEditorKind(document.activeElement);
      broadcastLiveInspect(selText, "selection", kind === "native-input" || kind === "contenteditable");
    }
  });

  addDocListener("focusin", (e) => {
    if (disposed) return;
    const target = e.target instanceof Element ? e.target : document.activeElement;
    const kind = detectEditorKind(target);
    if (kind !== "none") {
      activeEl = target;
      activeEditorKind = kind;
      typingEngine.resetWord();
      pill.setFocused(true, kind);
      scheduleMicroCounterUpdate(target);
    } else {
      activeEl = null;
      activeEditorKind = "none";
      pill.setFocused(false, "none");
    }
  });

  addDocListener("focusout", () => {
    if (disposed) return;
    window.setTimeout(() => {
      if (disposed) return;
      const current = document.activeElement;
      const kind = detectEditorKind(current);
      if (kind === "none") {
        typingEngine.resetWord();
        pill.setFocused(false, "none");
      }
    }, 60);
  });

  addDocListener("keydown", (e) => {
    if (disposed) return;
    // In-page shortcut fallback (Alt+Shift+L or Alt+Shift+T) when content script is attached
    if (e.altKey && e.shiftKey && !e.ctrlKey && !e.metaKey && (e.code === "KeyL" || e.code === "KeyT")) {
      e.preventDefault();
      void safeSendMessage({ type: "TOGGLE_LIVE_TYPING", enabled: !enabled });
      return;
    }

      if (!enabled) return;

      // Always resolve live target from the event/document so Side Panel or pill focus never leaves activeEl stale
      const targetEl =
        (e.target instanceof Element && detectEditorKind(e.target) !== "none" ? e.target : null) ??
        (detectEditorKind(document.activeElement) !== "none" ? document.activeElement : null) ??
        activeEl;
      const kind = detectEditorKind(targetEl);
      if (!targetEl || (kind !== "native-input" && kind !== "contenteditable")) return;
      activeEl = targetEl;
      activeEditorKind = kind;
      pill.setFocused(true, kind);

      const beforeCaret = getTextBeforeCaret(targetEl);
      const stateSnapshot = typingEngine.getState();
      const hasActiveWord =
        stateSnapshot.commitMode === "word-boundary" &&
        !stateSnapshot.escapedCurrentWord &&
        !e.ctrlKey &&
        !e.metaKey &&
        !e.altKey &&
        LATIN_WORD_RE.test(beforeCaret);
      const isCycleKey =
        hasActiveWord &&
        stateSnapshot.candidates.length > 1 &&
        (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Tab");
      const isNumberPickKey =
        hasActiveWord &&
        stateSnapshot.candidates.length > 0 &&
        /^[1-5]$/.test(e.key) &&
        Number(e.key) - 1 < stateSnapshot.candidates.length;
      const isSyncCommitCandidate =
        stateSnapshot.commitMode === "instant-keystroke" ||
        isCycleKey ||
        isNumberPickKey ||
        e.key === " " ||
        e.key === "Enter" ||
        e.key === "Escape" ||
        /^[.,!?;:)\]}]$/.test(e.key);

      if (!isSyncCommitCandidate) {
        if (
          e.key === "ArrowLeft" ||
          e.key === "ArrowRight" ||
          e.key === "ArrowUp" ||
          e.key === "ArrowDown" ||
          e.key === "Home" ||
          e.key === "End"
        ) {
          typingEngine.resetWord();
          pill.setPreview("", "");
        }
        return;
      }

      let preventedBoundaryKey: string | null = null;

      if (
        isCycleKey ||
        isNumberPickKey ||
        e.key === "Escape" ||
        (stateSnapshot.commitMode === "instant-keystroke" &&
          !e.ctrlKey &&
          !e.metaKey &&
          !e.altKey &&
          ((e.key.length === 1 && !/\s/.test(e.key)) ||
            (e.key === "Backspace" && stateSnapshot.rawBuffer.length > 0)))
      ) {
        e.preventDefault();
        if (isNumberPickKey) {
          preventedBoundaryKey = e.key;
        }
      } else if (
        hasActiveWord &&
        (e.key === " " || e.key === "Enter" || /^[.,!?;:)\]}]$/.test(e.key))
      ) {
        e.preventDefault();
        preventedBoundaryKey = e.key === "Enter" ? "\n" : e.key === "Tab" ? "\t" : e.key;
      }

      const key = e.key;
      const mods = { ctrlKey: e.ctrlKey, metaKey: e.metaKey, altKey: e.altKey, shiftKey: e.shiftKey };
      keyQueue = keyQueue
        .then(async () => {
          const freshBeforeCaret = targetEl ? getTextBeforeCaret(targetEl) : beforeCaret;
          const result = await typingEngine.handleKeyDown(key, mods, freshBeforeCaret);
          if (result.handled && result.insertText !== undefined && targetEl) {
            replaceCharsBeforeCaret(targetEl, result.deleteBeforeCaret ?? 0, result.insertText);
            scheduleMicroCounterUpdate(targetEl);
          } else if (!result.handled && preventedBoundaryKey !== null && targetEl) {
            replaceCharsBeforeCaret(targetEl, 0, preventedBoundaryKey);
          }
          pill.setPreview(
            result.rawBuffer,
            result.previewText,
            getCaretViewportRect(targetEl),
            result.candidates,
            result.selectedIndex ?? 0
          );
        })
        .catch(() => {
          if (preventedBoundaryKey !== null && targetEl) {
            replaceCharsBeforeCaret(targetEl, 0, preventedBoundaryKey);
          }
        });
  });

  addDocListener("input", (e) => {
    if (disposed) return;
    const target =
      (e.target instanceof Element && detectEditorKind(e.target) !== "none" ? e.target : null) ??
      (detectEditorKind(document.activeElement) !== "none" ? document.activeElement : null) ??
      activeEl;
    const kind = detectEditorKind(target);
    if (!target || (kind !== "native-input" && kind !== "contenteditable")) return;
    activeEl = target;
    activeEditorKind = kind;
    scheduleMicroCounterUpdate(target);
    if (!enabled) return;
    pill.setFocused(true, kind);
    const beforeCaret = getTextBeforeCaret(target);
    void typingEngine.updateWordPreviewFromTextBeforeCaret(beforeCaret).then((st) => {
      if (!disposed) {
        pill.setPreview(
          st.rawBuffer,
          st.previewText,
          getCaretViewportRect(target),
          st.candidates,
          st.selectedIndex
        );
      }
    });
  });

  api.runtime.onMessage.addListener((msg: any, _sender: any, sendResponse: (res: unknown) => void) => {
    if (msg?.type === "PING_CONTENT") {
      sendResponse({ ok: true });
      return false;
    }

    if (msg?.type === "TAB_SET_LIVE_STATE") {
      enabled = Boolean(msg.enabled);
      layout = msg.layout ?? layout;
      uiLang = msg.uiLang ?? uiLang;
      showMicroCounter = typeof msg.showMicroCounter === "boolean" ? msg.showMicroCounter : showMicroCounter;
      typingEngine.setLayout(layout);

      const currentEl = document.activeElement;
      const kind = detectEditorKind(currentEl);
      if (kind !== "none") {
        activeEl = currentEl;
        activeEditorKind = kind;
      }

      pill.updateState({
        enabled,
        layout,
        uiLang,
        showMicroCounter,
        editorKind: kind !== "none" ? kind : activeEditorKind,
        showConfirmToast: msg.showConfirmToast,
      });
      if (kind !== "none") {
        pill.setFocused(true, kind);
        scheduleMicroCounterUpdate(currentEl);
      }
      sendResponse({ ok: true, editorKind: kind });
      return false;
    }

    if (msg?.type === "TAB_GET_CONTEXT_TEXT") {
      if (msg.mode === "visible-page") {
        const text = (document.body?.innerText ?? "").slice(0, 120_000);
        sendResponse({ ok: true, text, source: "visible-page", editable: false });
        return false;
      }

      const selText = window.getSelection()?.toString() ?? "";
      if (selText.trim().length > 0) {
        const anchorEl = document.activeElement;
        const kind = detectEditorKind(anchorEl);
        sendResponse({
          ok: true,
          text: selText,
          source: "selection",
          editable: kind === "native-input" || kind === "contenteditable",
        });
        return false;
      }

      const focusedEl = activeEl ?? document.activeElement;
      const kind = detectEditorKind(focusedEl);
      if (kind === "native-input" || kind === "contenteditable") {
        sendResponse({
          ok: true,
          text: getEditorFullText(focusedEl),
          source: "active-editor",
          editable: true,
        });
        return false;
      }

      sendResponse({ ok: true, text: "", source: "manual", editable: false });
      return false;
    }

    if (msg?.type === "TAB_REPLACE_TEXT") {
      const target = activeEl ?? document.activeElement;
      const replaced = replaceEditorOrSelectionText(target, String(msg.text ?? ""), msg.scope ?? "selection");
      if (replaced) {
        typingEngine.resetWord();
        scheduleMicroCounterUpdate(target);
      }
      sendResponse({ ok: true, replaced });
      return false;
    }

    if (msg?.type === "TAB_INSERT_TEXT") {
      const target = activeEl ?? document.activeElement;
      const inserted = target ? replaceCharsBeforeCaret(target, 0, String(msg.text ?? "")) : false;
      if (inserted) {
        typingEngine.resetWord();
        scheduleMicroCounterUpdate(target);
      }
      sendResponse({ ok: true, inserted });
      return false;
    }

    return false;
  });
}
