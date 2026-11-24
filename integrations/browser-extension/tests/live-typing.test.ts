import { describe, expect, it } from "vitest";
import { HybridTypingEngine } from "../src/content/live-typing.js";
import {
  detectEditorKind,
  hasNonCollapsedSelection,
  isSensitiveField,
  replaceCharsBeforeCaret,
  resolveEditableRoot,
} from "../src/content/editor-adapter.js";
import { commitModeForLayout } from "../src/shared/messages.js";

const mockTranslit = async (raw: string, layout: string): Promise<string> => {
  if (layout === "phonetic-v1" || layout === "anjal-phonetic") {
    if (raw === "vanakkam") return "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD";
    if (raw === "tamil") return "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
    if (raw === "mawn-a") return "\u0BAE\u0BA8\u0BCD\u0BA9";
    if (raw === "n_aa") return "\u0BA9\u0BBE";
  }
  if (layout === "tamil99") {
    if (raw === "h") return "\u0B95";
    if (raw === "hq") return "\u0B95\u0BBE";
    if (raw === ";") return "\u0BA8";
    if (raw === "]") return "\u0B9E";
    if (raw === "a") return "\u0B85";
    if (raw === "ak") return "\u0B85\u0BAE\u0BCD";
    if (raw === "akf") return "\u0B85\u0BAE";
    if (raw === "akfk") return "\u0B85\u0BAE\u0BCD\u0BAE";
    if (raw === "akfkq") return "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE";
  }
  if (layout === "suratha-bamini") {
    if (raw === "f") return "\u0B95";
    if (raw === "f;") return "\u0B95\u0BCD";
    if (raw === ",") return "\u0B87";
    if (raw === "]") return "\u0BB8";
  }
  return raw;
};

describe("HybridTypingEngine & sensitive field guard", () => {
  it("maps Phonetic/Anjal to word-boundary and Tamil99/Bamini to instant-keystroke", () => {
    expect(commitModeForLayout("phonetic-v1")).toBe("word-boundary");
    expect(commitModeForLayout("anjal-phonetic")).toBe("word-boundary");
    expect(commitModeForLayout("tamil99")).toBe("instant-keystroke");
    expect(commitModeForLayout("suratha-bamini")).toBe("instant-keystroke");
  });

  it("commits Phonetic word on Space and respects Escape to keep English", async () => {
    const engine = new HybridTypingEngine("phonetic-v1", mockTranslit);
    await engine.updateWordPreviewFromTextBeforeCaret("vanakkam");
    expect(engine.getState().previewText).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD");

    const committed = await engine.handleKeyDown(" ", {}, "vanakkam");
    expect(committed.handled).toBe(true);
    expect(committed.deleteBeforeCaret).toBe(8);
    expect(committed.insertText).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD ");

    await engine.updateWordPreviewFromTextBeforeCaret("tamil");
    const esc = await engine.handleKeyDown("Escape", {}, "tamil");
    expect(esc.handled).toBe(true);
    const spaceAfterEsc = await engine.handleKeyDown(" ", {}, "tamil");
    expect(spaceAfterEsc.handled).toBe(false);
  });

  it("converts Tamil99 immediately per keystroke and rolls back cleanly on Backspace", async () => {
    const engine = new HybridTypingEngine("tamil99", mockTranslit);
    const k1 = await engine.handleKeyDown("h", {}, "");
    expect(k1.handled).toBe(true);
    expect(k1.deleteBeforeCaret).toBe(0);
    expect(k1.insertText).toBe("\u0B95");

    const k2 = await engine.handleKeyDown("q", {}, "\u0B95");
    expect(k2.handled).toBe(true);
    expect(k2.deleteBeforeCaret).toBe(1);
    expect(k2.insertText).toBe("\u0B95\u0BBE");

    const bs = await engine.handleKeyDown("Backspace", {}, "\u0B95\u0BBE");
    expect(bs.handled).toBe(true);
    expect(bs.deleteBeforeCaret).toBe(2);
    expect(bs.insertText).toBe("\u0B95");

    // Punctuation keys that map to Tamil letters in Tamil99 (';' -> ந, ']' -> ஞ) must not reset buffer
    engine.resetWord();
    const na = await engine.handleKeyDown(";", {}, "");
    expect(na.handled).toBe(true);
    expect(na.insertText).toBe("\u0BA8");
  });

  it("handles Bamini pulli (;) and punctuation-key letters (, and ]) without dropping them", async () => {
    const engine = new HybridTypingEngine("suratha-bamini", mockTranslit);
    const k1 = await engine.handleKeyDown("f", {}, "");
    expect(k1.handled).toBe(true);
    expect(k1.insertText).toBe("\u0B95");

    const pulli = await engine.handleKeyDown(";", {}, "\u0B95");
    expect(pulli.handled).toBe(true);
    expect(pulli.deleteBeforeCaret).toBe(1);
    expect(pulli.insertText).toBe("\u0B95\u0BCD");

    engine.resetWord();
    const comma = await engine.handleKeyDown(",", {}, "");
    expect(comma.handled).toBe(true);
    expect(comma.insertText).toBe("\u0B87");
  });

  it("guards password, email, url, tel, number, and one-time-code inputs", () => {
    const makeInput = (type: string, autocomplete = "") =>
      ({
        tagName: "INPUT",
        type,
        readOnly: false,
        disabled: false,
        getAttribute: (name: string) => (name === "autocomplete" ? autocomplete : null),
      }) as unknown as Element;

    expect(isSensitiveField(makeInput("password"))).toBe(true);
    expect(isSensitiveField(makeInput("email"))).toBe(true);
    expect(isSensitiveField(makeInput("url"))).toBe(true);
    expect(isSensitiveField(makeInput("tel"))).toBe(true);
    expect(isSensitiveField(makeInput("number"))).toBe(true);
    expect(isSensitiveField(makeInput("text", "one-time-code"))).toBe(true);
    expect(isSensitiveField(makeInput("text", "cc-number"))).toBe(true);
    expect(isSensitiveField(makeInput("text"))).toBe(false);
  });

  it("keeps n- and n_ inside the word-boundary buffer instead of splitting the word", async () => {
    const engine = new HybridTypingEngine("anjal-phonetic", mockTranslit);
    await engine.updateWordPreviewFromTextBeforeCaret("mawn-a");
    expect(engine.getState().rawBuffer).toBe("mawn-a");
    expect(engine.getState().previewText).toBe("\u0BAE\u0BA8\u0BCD\u0BA9");

    const committed = await engine.handleKeyDown(" ", {}, "n_aa");
    expect(committed.handled).toBe(true);
    expect(committed.deleteBeforeCaret).toBe(4);
    expect(committed.insertText).toBe("\u0BA9\u0BBE ");
  });

  it("supports Google/Microsoft candidate cycling (ArrowDown/Up/Tab, Space, 1-5, and click)", async () => {
    const mockSuggest = async (raw: string): Promise<string[]> => {
      if (raw === "vanakkam") return ["\u0BB5\u0BA9\u0B95\u0BCD\u0B95\u0BAE\u0BCD", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"];
      if (raw === "malai") return ["\u0BAE\u0BB2\u0BC8", "\u0BAE\u0BB4\u0BC8", "\u0BAE\u0BB3\u0BC8"];
      return [raw];
    };

    const engine = new HybridTypingEngine("phonetic-v1", mockTranslit, mockSuggest);
    await engine.updateWordPreviewFromTextBeforeCaret("vanakkam");
    expect(engine.getState().candidates).toEqual(["\u0BB5\u0BA9\u0B95\u0BCD\u0B95\u0BAE\u0BCD", "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD"]);
    expect(engine.getState().selectedIndex).toBe(0);

    // ArrowDown cycles to 2nd Mayangoli candidate without committing yet
    const down = await engine.handleKeyDown("ArrowDown", {}, "vanakkam");
    expect(down.handled).toBe(true);
    expect(down.insertText).toBeUndefined();
    expect(down.selectedIndex).toBe(1);
    expect(down.previewText).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD");

    // Space commits the highlighted candidate
    const spaceCommit = await engine.handleKeyDown(" ", {}, "vanakkam");
    expect(spaceCommit.handled).toBe(true);
    expect(spaceCommit.deleteBeforeCaret).toBe(8);
    expect(spaceCommit.insertText).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD ");

    // Tab / Shift+Tab cycling and Enter without trailing newline on cycled candidate
    await engine.updateWordPreviewFromTextBeforeCaret("malai");
    const tab1 = await engine.handleKeyDown("Tab", {}, "malai");
    expect(tab1.selectedIndex).toBe(1);
    expect(tab1.previewText).toBe("\u0BAE\u0BB4\u0BC8");
    const tab2 = await engine.handleKeyDown("Tab", {}, "malai");
    expect(tab2.selectedIndex).toBe(2);
    expect(tab2.previewText).toBe("\u0BAE\u0BB3\u0BC8");
    const shiftTab = await engine.handleKeyDown("Tab", { shiftKey: true }, "malai");
    expect(shiftTab.selectedIndex).toBe(1);
    const enterCycled = await engine.handleKeyDown("Enter", {}, "malai");
    expect(enterCycled.handled).toBe(true);
    expect(enterCycled.insertText).toBe("\u0BAE\u0BB4\u0BC8");

    // Number key 2 direct pick
    await engine.updateWordPreviewFromTextBeforeCaret("malai");
    const numPick = await engine.handleKeyDown("2", {}, "malai");
    expect(numPick.handled).toBe(true);
    expect(numPick.insertText).toBe("\u0BAE\u0BB4\u0BC8 ");

    // Out-of-range digit is not swallowed
    await engine.updateWordPreviewFromTextBeforeCaret("vanakkam");
    const digitOut = await engine.handleKeyDown("4", {}, "vanakkam");
    expect(digitOut.handled).toBe(false);

    // Click commitCandidateAt
    await engine.updateWordPreviewFromTextBeforeCaret("malai");
    const clickPick = engine.commitCandidateAt(2, "malai");
    expect(clickPick.handled).toBe(true);
    expect(clickPick.deleteBeforeCaret).toBe(5);
    expect(clickPick.insertText).toBe("\u0BAE\u0BB3\u0BC8 ");
  });

  it("commits Phonetic word on Enter without appending a trailing newline", async () => {
    const engine = new HybridTypingEngine("phonetic-v1", mockTranslit);
    await engine.updateWordPreviewFromTextBeforeCaret("vanakkam");
    const enterCommit = await engine.handleKeyDown("Enter", {}, "vanakkam");
    expect(enterCommit.handled).toBe(true);
    expect(enterCommit.deleteBeforeCaret).toBe(8);
    expect(enterCommit.insertText).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD");
  });

  it("resolves Lexical editable root and replaces text atomically across microtask commits without leaving first letter or repeating Bamini characters", async () => {
    const prevInputEvent = (globalThis as Record<string, unknown>).InputEvent;
    class MockInputEvent extends Event {
      inputType: string;
      data: string | null;
      constructor(type: string, init: { bubbles?: boolean; cancelable?: boolean; inputType?: string; data?: string | null } = {}) {
        super(type, init);
        this.inputType = init.inputType ?? "";
        this.data = init.data ?? null;
      }
    }
    (globalThis as Record<string, unknown>).InputEvent = MockInputEvent;

    try {
      const createLexicalHarness = (
        initialText: string,
        microtaskMode: boolean,
        options: { ignoreInsertReplacement?: boolean } = {}
      ) => {
        let stateText = initialText;
        let domText = initialText;
        let selStart = initialText.length;
        let selEnd = initialText.length;
        let nodeDirtyInTurn = false;
        let beforeInputEvents = 0;
        const listeners = new Map<string, Array<{ fn: (ev: Event) => void; capture: boolean }>>();

        const textNode: { nodeType: number; textContent: string } = {
          nodeType: 3,
          get textContent() {
            return domText;
          },
          set textContent(v: string) {
            domText = v;
          },
        };

        const syncDom = () => {
          domText = stateText;
          nodeDirtyInTurn = false;
        };

        const makeRange = (start: number, end: number) => {
          const range: any = {
            startContainer: textNode,
            endContainer: textNode,
            startOffset: start,
            endOffset: end,
            setStart(container: unknown, offset: number) {
              range.startContainer = container;
              range.startOffset = offset;
            },
            setEnd(container: unknown, offset: number) {
              range.endContainer = container;
              range.endOffset = offset;
            },
            collapse(toStart?: boolean) {
              if (toStart) {
                range.endContainer = range.startContainer;
                range.endOffset = range.startOffset;
              } else {
                range.startContainer = range.endContainer;
                range.startOffset = range.endOffset;
              }
            },
            cloneRange() {
              return makeRange(range.startOffset, range.endOffset);
            },
            deleteContents() {
              throw new Error("Raw DOM fallback must not run when Lexical intercepts beforeinput");
            },
            insertNode() {
              throw new Error("Raw DOM fallback must not run when Lexical intercepts beforeinput");
            },
          };
          return range;
        };

        const selObj = {
          rangeCount: 1,
          get isCollapsed() {
            return selStart === selEnd;
          },
          getRangeAt: () => makeRange(selStart, selEnd),
          collapseToEnd: () => {
            selStart = selEnd;
          },
          removeAllRanges: () => {
            selStart = 0;
            selEnd = 0;
          },
          addRange: (r: { startOffset: number; endOffset: number }) => {
            selStart = r.startOffset;
            selEnd = r.endOffset;
          },
        };

        const rootEl: any = {
          tagName: "DIV",
          isContentEditable: true,
          contains: (n: unknown) => n === rootEl || n === spanEl || n === textNode,
          focus: () => {
            docObj.activeElement = rootEl;
          },
          hasAttribute: (attr: string) => attr === "data-lexical-editor",
          getAttribute: (attr: string) => (attr === "data-lexical-editor" ? "true" : null),
          querySelector: (sel: string) => (sel === "[data-lexical-text]" ? spanEl : null),
          closest: (selector: string) =>
            selector.includes("data-lexical-editor") ? rootEl : null,
          addEventListener: (type: string, fn: (ev: Event) => void, capture = false) => {
            const list = listeners.get(type) ?? [];
            list.push({ fn, capture: Boolean(capture) });
            listeners.set(type, list);
          },
          removeEventListener: (type: string, fn: (ev: Event) => void, capture = false) => {
            const list = listeners.get(type) ?? [];
            listeners.set(
              type,
              list.filter((entry) => entry.fn !== fn || entry.capture !== Boolean(capture))
            );
          },
          dispatchEvent: (ev: Event) => {
            const list = listeners.get(ev.type) ?? [];
            for (const entry of [...list]) {
              entry.fn(ev);
            }
            return !ev.defaultPrevented;
          },
        };

        rootEl.addEventListener("beforeinput", (ev: Event) => {
          const inputEv = ev as MockInputEvent;
          beforeInputEvents += 1;
          if (inputEv.inputType === "deleteContentBackward") {
            ev.preventDefault();
            if (microtaskMode && nodeDirtyInTurn) {
              return;
            }
            const delStart = selStart < selEnd ? selStart : Math.max(0, selStart - 1);
            const delEnd = selEnd;
            if (delEnd > delStart) {
              stateText = stateText.slice(0, delStart) + stateText.slice(delEnd);
              selStart = delStart;
              selEnd = delStart;
              if (microtaskMode) {
                nodeDirtyInTurn = true;
                queueMicrotask(syncDom);
              } else {
                syncDom();
              }
            }
          } else if (inputEv.inputType === "insertReplacementText") {
            if (options.ignoreInsertReplacement) {
              return;
            }
            ev.preventDefault();
            const data = inputEv.data ?? "";
            const clampedStart = Math.min(selStart, stateText.length);
            const clampedEnd = Math.min(selEnd, stateText.length);
            stateText = stateText.slice(0, clampedStart) + data + stateText.slice(clampedEnd);
            const nextCaret = clampedStart + data.length;
            selStart = nextCaret;
            selEnd = nextCaret;
            if (microtaskMode) {
              nodeDirtyInTurn = true;
              queueMicrotask(syncDom);
            } else {
              syncDom();
            }
          } else if (inputEv.inputType === "insertText" && inputEv.data) {
            const isCleanSingleChar =
              inputEv.data.length === 1 && !nodeDirtyInTurn && selStart === selEnd;
            const clampedStart = Math.min(selStart, stateText.length);
            const clampedEnd = Math.min(selEnd, stateText.length);
            stateText = stateText.slice(0, clampedStart) + inputEv.data + stateText.slice(clampedEnd);
            const nextCaret = clampedStart + inputEv.data.length;
            selStart = nextCaret;
            selEnd = nextCaret;
            if (isCleanSingleChar) {
              syncDom();
              return;
            }
            ev.preventDefault();
            if (microtaskMode) {
              nodeDirtyInTurn = true;
              queueMicrotask(syncDom);
            } else {
              syncDom();
            }
          }
        });

        const spanEl: any = {
          tagName: "SPAN",
          isContentEditable: true,
          closest: (selector: string) =>
            selector.includes("data-lexical-editor") ? rootEl : null,
          hasAttribute: (attr: string) => attr === "data-lexical-text",
          getAttribute: (attr: string) => (attr === "data-lexical-text" ? "true" : null),
          ownerDocument: undefined as any,
        };

        // Model real Chromium execCommand("delete"): does not fire beforeinput, returns true,
        // and when deleting the last character of a span (childList mutation), Lexical's
        // MutationObserver reverts it back to the 1-character text.
        const docObj: any = {
          activeElement: spanEl,
          location: { hostname: "web.whatsapp.com" },
          getSelection: () => selObj,
          createRange: () => makeRange(0, 0),
          execCommand: (cmd: string, _ui: boolean, arg?: string) => {
            if (cmd === "delete") {
              if (selStart === selEnd && selStart > 0) {
                if (stateText.length === 1) {
                  // Simulate Lexical MutationObserver reverting childList removal of the last char
                  return true;
                }
                const delAt = selStart - 1;
                stateText = stateText.slice(0, delAt) + stateText.slice(selStart);
                selStart = delAt;
                selEnd = delAt;
                syncDom();
              }
              return true;
            }
            if (cmd === "insertText") {
              const ev = new MockInputEvent("beforeinput", {
                bubbles: true,
                cancelable: true,
                inputType: "insertText",
                data: arg ?? "",
              });
              const ok = rootEl.dispatchEvent(ev);
              return ok && !ev.defaultPrevented;
            }
            return false;
          },
        };

        const appendNativeText = (text: string) => {
          const clamped = Math.min(selStart, stateText.length);
          stateText = stateText.slice(0, clamped) + text + stateText.slice(clamped);
          selStart = clamped + text.length;
          selEnd = selStart;
          syncDom();
        };

        rootEl.ownerDocument = docObj;
        spanEl.ownerDocument = docObj;
        return {
          rootEl,
          spanEl,
          docObj,
          appendNativeText,
          getDomText: () => domText,
          getBeforeInputCount: () => beforeInputEvents,
        };
      };

      const ammaTamilSpace = "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE ";
      const vaaTamilSpace = "\u0BB5\u0BBE ";

      const syncHarness = createLexicalHarness("ammaa", false);
      expect(resolveEditableRoot(syncHarness.spanEl)).toBe(syncHarness.rootEl);
      expect(detectEditorKind(syncHarness.spanEl, syncHarness.docObj)).toBe("contenteditable");
      expect(await replaceCharsBeforeCaret(syncHarness.spanEl, 5, ammaTamilSpace)).toBe(true);
      expect(syncHarness.getDomText()).toBe(ammaTamilSpace);

      // First word ("ammaa" -> "அம்மா ") followed by second word ("vaa" -> "அம்மா வா ")
      const microHarness = createLexicalHarness("ammaa", true);
      expect(await replaceCharsBeforeCaret(microHarness.spanEl, 5, ammaTamilSpace)).toBe(true);
      expect(microHarness.getDomText()).toBe(ammaTamilSpace);
      expect(microHarness.getBeforeInputCount()).toBe(1);

      microHarness.appendNativeText("vaa");
      expect(await replaceCharsBeforeCaret(microHarness.spanEl, 3, vaaTamilSpace)).toBe(true);
      expect(microHarness.getDomText()).toBe(`${ammaTamilSpace}${vaaTamilSpace}`);

      const midWordHarness = createLexicalHarness("hello ammaa", true);
      expect(await replaceCharsBeforeCaret(midWordHarness.spanEl, 5, ammaTamilSpace)).toBe(true);
      expect(midWordHarness.getDomText()).toBe(`hello ${ammaTamilSpace}`);

      // Bamini sequence ('' -> 'ய' -> 'யக' -> Backspace 'ய' -> Backspace '' -> 'க')
      const baminiHarness = createLexicalHarness("", true);
      expect(await replaceCharsBeforeCaret(baminiHarness.spanEl, 0, "\u0BAF")).toBe(true);
      expect(baminiHarness.getDomText()).toBe("\u0BAF");
      expect(baminiHarness.getBeforeInputCount()).toBe(1);

      expect(await replaceCharsBeforeCaret(baminiHarness.spanEl, 1, "\u0BAF\u0B95")).toBe(true);
      expect(baminiHarness.getDomText()).toBe("\u0BAF\u0B95");

      expect(await replaceCharsBeforeCaret(baminiHarness.spanEl, 2, "\u0BAF")).toBe(true);
      expect(baminiHarness.getDomText()).toBe("\u0BAF");

      expect(await replaceCharsBeforeCaret(baminiHarness.spanEl, 1, "")).toBe(true);
      expect(baminiHarness.getDomText()).toBe("");

      expect(await replaceCharsBeforeCaret(baminiHarness.spanEl, 0, "\u0B95")).toBe(true);
      expect(baminiHarness.getDomText()).toBe("\u0B95");

      // Bamini left-kombu at offset 0 ('' -> 'ெ' -> 'கெ' -> 'ெ' -> '')
      const kombuHarness = createLexicalHarness("", true);
      expect(await replaceCharsBeforeCaret(kombuHarness.spanEl, 0, "\u0BC6")).toBe(true);
      expect(kombuHarness.getDomText()).toBe("\u0BC6");
      expect(await replaceCharsBeforeCaret(kombuHarness.spanEl, 1, "\u0B95\u0BC6")).toBe(true);
      expect(kombuHarness.getDomText()).toBe("\u0B95\u0BC6");
      expect(await replaceCharsBeforeCaret(kombuHarness.spanEl, 2, "\u0BC6")).toBe(true);
      expect(kombuHarness.getDomText()).toBe("\u0BC6");
      expect(await replaceCharsBeforeCaret(kombuHarness.spanEl, 1, "")).toBe(true);
      expect(kombuHarness.getDomText()).toBe("");

      // Fallback Layer 2: editor ignores insertReplacementText and MutationObserver reverts execCommand("delete") on the last char
      const fallbackHarness = createLexicalHarness("ammaa", true, { ignoreInsertReplacement: true });
      expect(await replaceCharsBeforeCaret(fallbackHarness.spanEl, 5, ammaTamilSpace)).toBe(true);
      expect(fallbackHarness.getDomText()).toBe(ammaTamilSpace);

      // Replacing a non-collapsed Lexical selection (Ctrl+A -> type new char) replaces instead of prepending
      const selectAllHarness = createLexicalHarness("\u0B85\u0BAE\u0BCD\u0BAE\u0BBE", true);
      const fullSel = selectAllHarness.docObj.getSelection();
      const fullRange = selectAllHarness.docObj.createRange();
      fullRange.setStart(fullSel.getRangeAt(0).startContainer, 0);
      fullRange.setEnd(fullSel.getRangeAt(0).endContainer, 5);
      fullSel.removeAllRanges();
      fullSel.addRange(fullRange);
      expect(hasNonCollapsedSelection(selectAllHarness.spanEl)).toBe(true);
      expect(await replaceCharsBeforeCaret(selectAllHarness.spanEl, 0, "\u0B95")).toBe(true);
      expect(selectAllHarness.getDomText()).toBe("\u0B95");
      expect(hasNonCollapsedSelection(selectAllHarness.spanEl)).toBe(false);
    } finally {
      (globalThis as Record<string, unknown>).InputEvent = prevInputEvent;
    }
  });

  it("resets Tamil99 rolling buffer on Ctrl+A, Delete, Ctrl+X/V/Backspace, selection Backspace, or caret mismatch", async () => {
    const engine = new HybridTypingEngine("tamil99", mockTranslit);
    for (const k of ["a", "k", "f", "k", "q"]) {
      await engine.handleKeyDown(k, {}, "");
    }
    expect(engine.getState().rawBuffer).toBe("akfkq");
    expect(engine.getState().previewText).toBe("\u0B85\u0BAE\u0BCD\u0BAE\u0BBE");

    // Ctrl+A resets rawBuffer so subsequent Backspace on selection never rolls back "akfkq" -> "அம்ம"
    const ctrlA = await engine.handleKeyDown("a", { ctrlKey: true }, "");
    expect(ctrlA.handled).toBe(false);
    expect(engine.getState().rawBuffer).toBe("");
    const bsAfterCtrlA = await engine.handleKeyDown("Backspace", {}, "");
    expect(bsAfterCtrlA.handled).toBe(false);

    // Backspace when selection is non-collapsed (textBeforeCaret === "") or caret moved mid-word resets buffer
    for (const k of ["a", "k", "f", "k", "q"]) {
      await engine.handleKeyDown(k, {}, "");
    }
    const bsNonCollapsed = await engine.handleKeyDown("Backspace", {}, "");
    expect(bsNonCollapsed.handled).toBe(false);
    expect(engine.getState().rawBuffer).toBe("");

    for (const k of ["a", "k", "f", "k", "q"]) {
      await engine.handleKeyDown(k, {}, "");
    }
    const bsMidWord = await engine.handleKeyDown("Backspace", {}, "\u0B85\u0BAE\u0BCD");
    expect(bsMidWord.handled).toBe(false);
    expect(engine.getState().rawBuffer).toBe("");

    // Delete, Ctrl+X, Ctrl+V, Ctrl+Backspace all reset rawBuffer
    for (const resetCall of [
      () => engine.handleKeyDown("Delete", {}, "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
      () => engine.handleKeyDown("x", { ctrlKey: true }, ""),
      () => engine.handleKeyDown("v", { ctrlKey: true }, ""),
      () => engine.handleKeyDown("Backspace", { ctrlKey: true }, "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE"),
    ]) {
      for (const k of ["a", "k"]) {
        await engine.handleKeyDown(k, {}, "");
      }
      expect(engine.getState().rawBuffer).toBe("ak");
      const res = await resetCall();
      expect(res.handled).toBe(false);
      expect(engine.getState().rawBuffer).toBe("");
    }
  });

  it("detects non-collapsed selections and replaces selected textarea text without prepending", async () => {
    const prevInputEvent = (globalThis as Record<string, unknown>).InputEvent;
    class MockInputEvent extends Event {
      inputType: string;
      data: string | null;
      constructor(type: string, init: { bubbles?: boolean; cancelable?: boolean; inputType?: string; data?: string | null } = {}) {
        super(type, init);
        this.inputType = init.inputType ?? "";
        this.data = init.data ?? null;
      }
    }
    (globalThis as Record<string, unknown>).InputEvent = MockInputEvent;

    try {
      const ta: any = {
        tagName: "TEXTAREA",
        value: "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE",
        selectionStart: 0,
        selectionEnd: 5,
        setRangeText(replacement: string, start: number, end: number) {
          ta.value = ta.value.slice(0, start) + replacement + ta.value.slice(end);
          ta.selectionStart = start + replacement.length;
          ta.selectionEnd = ta.selectionStart;
        },
        dispatchEvent: () => true,
      };
      expect(hasNonCollapsedSelection(ta)).toBe(true);
      expect(await replaceCharsBeforeCaret(ta, 0, "\u0B95")).toBe(true);
      expect(ta.value).toBe("\u0B95");
      expect(hasNonCollapsedSelection(ta)).toBe(false);
    } finally {
      (globalThis as Record<string, unknown>).InputEvent = prevInputEvent;
    }
  });
});
