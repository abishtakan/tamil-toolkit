import type { EditorKind } from "../shared/messages.js";

const SENSITIVE_INPUT_TYPES = new Set([
  "password",
  "email",
  "url",
  "tel",
  "number",
  "hidden",
  "date",
  "datetime-local",
  "month",
  "week",
  "time",
  "color",
  "range",
  "file",
  "checkbox",
  "radio",
  "submit",
  "button",
  "reset",
]);

export function isSensitiveField(el: Element | null): boolean {
  if (!el) return false;
  if (el.tagName === "INPUT") {
    const input = el as HTMLInputElement;
    const type = (input.type || "text").toLowerCase();
    if (SENSITIVE_INPUT_TYPES.has(type)) return true;
    if (input.readOnly || input.disabled) return true;
  }
  if (el.tagName === "TEXTAREA") {
    const ta = el as HTMLTextAreaElement;
    if (ta.readOnly || ta.disabled) return true;
  }
  const ac = (el.getAttribute("autocomplete") || "").toLowerCase();
  if (
    ac.includes("one-time-code") ||
    ac.includes("current-password") ||
    ac.includes("new-password") ||
    ac.includes("cc-")
  ) {
    return true;
  }
  return false;
}

export function isCanvasEditorDocument(doc: Document = document): boolean {
  const host = doc.location?.hostname ?? "";
  if (host === "docs.google.com" && doc.querySelector(".kix-canvas-tile-content, .kix-appview-editor")) {
    return true;
  }
  if (host === "www.figma.com" || host === "figma.com") {
    return true;
  }
  return false;
}

const CONTROLLED_EDITOR_HOSTS = [
  "whatsapp.com",
  "messenger.com",
  "facebook.com",
  "instagram.com",
  "threads.net",
  "discord.com",
  "slack.com",
  "notion.so",
  "reddit.com",
  "x.com",
  "twitter.com",
];

// Strip Lexical/contenteditable empty-span caret placeholders (U+200B, U+FEFF) when reading
// Latin tokens before the caret, while leaving ZWJ (U+200D) and ZWNJ (U+200C) untouched.
const EMPTY_SPAN_PLACEHOLDERS_RE = /[\u200B\uFEFF]/g;

export function resolveEditableRoot(el: Element | null): HTMLElement | null {
  if (!el) return null;
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    return el as HTMLElement;
  }
  const root =
    typeof el.closest === "function"
      ? el.closest(
          "[data-lexical-editor='true'], [contenteditable='true'], [contenteditable=''], [contenteditable='plaintext-only']"
        )
      : null;
  if (root) {
    return root as HTMLElement;
  }
  const htmlEl = el as HTMLElement;
  if (htmlEl.isContentEditable || (typeof el.hasAttribute === "function" && el.hasAttribute("data-lexical-editor"))) {
    return htmlEl;
  }
  return null;
}

function isLexicalOrControlledEditor(root: HTMLElement): boolean {
  if (
    root.hasAttribute?.("data-lexical-editor") ||
    root.hasAttribute?.("data-slate-editor") ||
    Boolean(root.querySelector?.("[data-lexical-text]")) ||
    root.classList?.contains?.("DraftEditor-root") ||
    Boolean(root.closest?.(".DraftEditor-root"))
  ) {
    return true;
  }
  const host = root.ownerDocument?.location?.hostname ?? "";
  return CONTROLLED_EDITOR_HOSTS.some((domain) => host === domain || host.endsWith(`.${domain}`));
}

export function detectEditorKind(el: Element | null, doc: Document = document): EditorKind {
  if (isCanvasEditorDocument(doc)) {
    return "canvas-fallback";
  }
  const resolved = resolveEditableRoot(el) ?? el;
  if (!resolved || isSensitiveField(resolved) || isSensitiveField(el)) {
    return "none";
  }
  if (resolved.tagName === "TEXTAREA" || resolved.tagName === "INPUT") {
    return "native-input";
  }
  const htmlEl = resolved as HTMLElement;
  if (htmlEl.isContentEditable || (typeof resolved.hasAttribute === "function" && resolved.hasAttribute("data-lexical-editor"))) {
    return "contenteditable";
  }
  return "none";
}

export function getTextBeforeCaret(el: Element): string {
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    const pos = field.selectionStart ?? field.value.length;
    return field.value.slice(0, pos);
  }

  const sel = el.ownerDocument?.getSelection();
  if (!sel || sel.rangeCount === 0 || !sel.isCollapsed) return "";
  const range = sel.getRangeAt(0);
  if (range.startContainer.nodeType === 3) {
    return (range.startContainer.textContent ?? "")
      .slice(0, range.startOffset)
      .replace(EMPTY_SPAN_PLACEHOLDERS_RE, "");
  }
  const root = resolveEditableRoot(el) ?? el;
  if (typeof root.contains === "function" && !root.contains(range.startContainer)) {
    return "";
  }
  const startParent =
    range.startContainer.nodeType === 1
      ? (range.startContainer as Element)
      : range.startContainer.parentElement;
  const blockStart = startParent?.closest?.("p, div, li") ?? root;
  const scopeEl =
    typeof root.contains === "function" && root.contains(blockStart) ? blockStart : root;
  if (typeof range.cloneRange === "function") {
    const preRange = range.cloneRange();
    preRange.selectNodeContents(scopeEl);
    preRange.setEnd(range.startContainer, range.startOffset);
    return preRange.toString().replace(EMPTY_SPAN_PLACEHOLDERS_RE, "");
  }
  return "";
}

export function hasNonCollapsedSelection(el: Element | null): boolean {
  if (!el) return false;
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    return (
      field.selectionStart !== null &&
      field.selectionEnd !== null &&
      field.selectionEnd > field.selectionStart
    );
  }
  const sel = el.ownerDocument?.getSelection();
  return Boolean(sel && sel.rangeCount > 0 && !sel.isCollapsed);
}

function nextMicrotask(): Promise<void> {
  return new Promise<void>((resolve) => {
    queueMicrotask(() => {
      queueMicrotask(resolve);
    });
  });
}

function findLastTextNode(node: Node): Text | null {
  if (node.nodeType === 3) {
    return (node.textContent ?? "").replace(EMPTY_SPAN_PLACEHOLDERS_RE, "").length > 0
      ? (node as Text)
      : null;
  }
  const children = node.childNodes;
  if (!children) return null;
  for (let i = children.length - 1; i >= 0; i -= 1) {
    const found = findLastTextNode(children[i]);
    if (found) return found;
  }
  return null;
}

function selectTextRangeBackward(
  textNode: Text,
  endOffset: number,
  deleteCount: number,
  doc: Document,
  sel: Selection,
  fallbackRange?: Range
): Range | null {
  const text = textNode.textContent ?? "";
  let startOffset = endOffset;
  let counted = 0;
  while (startOffset > 0 && counted < deleteCount) {
    startOffset -= 1;
    const ch = text[startOffset];
    if (ch !== "\u200B" && ch !== "\uFEFF") {
      counted += 1;
    }
  }
  if (typeof doc.createRange === "function") {
    const replaceRange = doc.createRange();
    replaceRange.setStart(textNode, startOffset);
    replaceRange.setEnd(textNode, endOffset);
    if (typeof sel.removeAllRanges === "function" && typeof sel.addRange === "function") {
      sel.removeAllRanges();
      sel.addRange(replaceRange);
    } else if (fallbackRange && typeof fallbackRange.setStart === "function") {
      fallbackRange.setStart(textNode, startOffset);
    }
    return replaceRange;
  }
  if (fallbackRange && typeof fallbackRange.setStart === "function") {
    fallbackRange.setStart(textNode, startOffset);
    return fallbackRange;
  }
  return null;
}

function selectCharsBeforeCaret(
  root: HTMLElement,
  doc: Document,
  sel: Selection,
  deleteCount: number
): Range | null {
  const range = sel.getRangeAt(0);
  if (deleteCount <= 0) {
    return range;
  }
  if (range.startContainer.nodeType === 3) {
    return selectTextRangeBackward(
      range.startContainer as Text,
      range.startOffset,
      deleteCount,
      doc,
      sel,
      range
    );
  }
  if (
    range.startContainer.nodeType === 1 &&
    range.startOffset > 0 &&
    (typeof root.contains !== "function" || root.contains(range.startContainer))
  ) {
    const children = range.startContainer.childNodes;
    if (children) {
      for (let i = Math.min(range.startOffset - 1, children.length - 1); i >= 0; i -= 1) {
        const found = findLastTextNode(children[i]);
        if (found && (typeof root.contains !== "function" || root.contains(found))) {
          return selectTextRangeBackward(
            found,
            (found.textContent ?? "").length,
            deleteCount,
            doc,
            sel,
            range
          );
        }
      }
    }
  }
  return range;
}

export async function replaceCharsBeforeCaret(
  el: Element,
  deleteCount: number,
  replacement: string
): Promise<boolean> {
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    const selStart = field.selectionStart ?? field.value.length;
    const selEnd = field.selectionEnd ?? selStart;
    const start = deleteCount > 0 ? Math.max(0, selStart - deleteCount) : selStart;
    const end = deleteCount > 0 ? selStart : selEnd;
    field.setRangeText(replacement, start, end, "end");
    field.dispatchEvent(
      new InputEvent("input", {
        bubbles: true,
        cancelable: false,
        inputType: "insertReplacementText",
        data: replacement,
      })
    );
    return true;
  }

  const doc = el.ownerDocument;
  const sel = doc?.getSelection();
  if (!doc || !sel || sel.rangeCount === 0) return false;

  const root = resolveEditableRoot(el) ?? (el as HTMLElement);
  if (
    typeof root.focus === "function" &&
    doc.activeElement !== root &&
    !(typeof root.contains === "function" && doc.activeElement && root.contains(doc.activeElement))
  ) {
    root.focus();
  }

  if (deleteCount > 0 && !sel.isCollapsed && typeof sel.collapseToEnd === "function") {
    sel.collapseToEnd();
  }

  const beforeAll = getTextBeforeCaret(root);

  let effectiveDeleteCount = deleteCount;
  let effectiveReplacement = replacement;
  if (deleteCount > 0 && replacement.length > 0 && beforeAll.length >= deleteCount) {
    const toDelete = beforeAll.slice(beforeAll.length - deleteCount);
    const maxPrefix = Math.min(toDelete.length, replacement.length);
    let commonPrefix = 0;
    while (
      commonPrefix < maxPrefix &&
      toDelete.charCodeAt(commonPrefix) === replacement.charCodeAt(commonPrefix)
    ) {
      commonPrefix += 1;
    }
    if (
      commonPrefix > 0 &&
      toDelete.charCodeAt(commonPrefix - 1) >= 0xd800 &&
      toDelete.charCodeAt(commonPrefix - 1) <= 0xdbff
    ) {
      commonPrefix -= 1;
    }
    if (commonPrefix > 0) {
      effectiveDeleteCount -= commonPrefix;
      effectiveReplacement = replacement.slice(commonPrefix);
    }
  }

  if (effectiveDeleteCount === 0 && effectiveReplacement.length === 0) {
    return true;
  }

  const observeBeforeInputPrevented = (action: () => void): boolean => {
    let prevented = false;
    const listener = (ev: Event) => {
      if (ev.defaultPrevented) prevented = true;
    };
    root.addEventListener?.("beforeinput", listener, false);
    try {
      action();
    } finally {
      root.removeEventListener?.("beforeinput", listener, false);
    }
    return prevented;
  };

  if (isLexicalOrControlledEditor(root)) {
    const currentRange = sel.getRangeAt(0);
    const origRange =
      typeof currentRange.cloneRange === "function" ? currentRange.cloneRange() : null;

    // Layer 1: Atomic beforeinput over selected range (Lexical / Slate / ProseMirror).
    if (typeof InputEvent === "function") {
      const selectedRange =
        effectiveDeleteCount > 0
          ? selectCharsBeforeCaret(root, doc, sel, effectiveDeleteCount)
          : currentRange;

      let targetRanges: StaticRange[] | undefined;
      if (
        typeof StaticRange === "function" &&
        selectedRange &&
        "startContainer" in selectedRange &&
        "endContainer" in selectedRange
      ) {
        try {
          targetRanges = [
            new StaticRange({
              startContainer: selectedRange.startContainer,
              startOffset: selectedRange.startOffset,
              endContainer: selectedRange.endContainer,
              endOffset: selectedRange.endOffset,
            }),
          ];
        } catch {
          targetRanges = undefined;
        }
      }

      const ev = new InputEvent("beforeinput", {
        bubbles: true,
        cancelable: true,
        inputType: effectiveReplacement.length > 0 ? "insertReplacementText" : "deleteContentBackward",
        data: effectiveReplacement.length > 0 ? effectiveReplacement : null,
        ...(targetRanges ? { targetRanges } : {}),
      });
      const dispatchOk = root.dispatchEvent(ev);
      await nextMicrotask();
      if (
        !dispatchOk ||
        ev.defaultPrevented ||
        (Boolean(sel.isCollapsed) && getTextBeforeCaret(root) !== beforeAll)
      ) {
        return true;
      }

      if (origRange && typeof sel.removeAllRanges === "function" && typeof sel.addRange === "function") {
        sel.removeAllRanges();
        sel.addRange(origRange);
      } else if (!sel.isCollapsed && typeof sel.collapseToEnd === "function") {
        sel.collapseToEnd();
      }
    }

    // Layer 2: Collapsed delete + insert fallback for controlled editors that ignore insertReplacementText.
    if (effectiveDeleteCount > 0 && !sel.isCollapsed && typeof sel.collapseToEnd === "function") {
      sel.collapseToEnd();
    }

    let deletedHandled = effectiveDeleteCount === 0;
    if (effectiveDeleteCount > 0) {
      for (let i = 0; i < effectiveDeleteCount; i += 1) {
        const lenBefore = getTextBeforeCaret(root).length;
        let stepDeleted = false;

        if (typeof doc.execCommand === "function") {
          const prevented = observeBeforeInputPrevented(() => {
            doc.execCommand("delete", false);
          });
          await nextMicrotask();
          if (!sel.isCollapsed && typeof sel.collapseToEnd === "function") {
            sel.collapseToEnd();
          }
          // Do not trust bare execCommand("delete") return value when a MutationObserver reverts childList removal.
          if (prevented || getTextBeforeCaret(root).length < lenBefore) {
            stepDeleted = true;
          }
        }

        if (!stepDeleted && typeof InputEvent === "function") {
          const ev = new InputEvent("beforeinput", {
            bubbles: true,
            cancelable: true,
            inputType: "deleteContentBackward",
          });
          const dispatchOk = root.dispatchEvent(ev);
          await nextMicrotask();
          if (!sel.isCollapsed && typeof sel.collapseToEnd === "function") {
            sel.collapseToEnd();
          }
          if (!dispatchOk || ev.defaultPrevented || getTextBeforeCaret(root).length < lenBefore) {
            stepDeleted = true;
          }
        }

        if (stepDeleted) {
          deletedHandled = true;
        } else {
          break;
        }
      }
    }

    let insertedHandled = effectiveReplacement.length === 0;
    if (deletedHandled && effectiveReplacement.length > 0) {
      const beforeIns = getTextBeforeCaret(root);

      if (typeof doc.execCommand === "function") {
        const prevented = observeBeforeInputPrevented(() => {
          doc.execCommand("insertText", false, effectiveReplacement);
        });
        await nextMicrotask();
        if (prevented || getTextBeforeCaret(root) !== beforeIns) {
          insertedHandled = true;
        }
      }

      if (!insertedHandled && typeof InputEvent === "function") {
        const ev = new InputEvent("beforeinput", {
          bubbles: true,
          cancelable: true,
          inputType: "insertText",
          data: effectiveReplacement,
        });
        const dispatchOk = root.dispatchEvent(ev);
        await nextMicrotask();
        if (!dispatchOk || ev.defaultPrevented || getTextBeforeCaret(root) !== beforeIns) {
          insertedHandled = true;
        }
      }

      if (
        !insertedHandled &&
        typeof ClipboardEvent === "function" &&
        typeof DataTransfer === "function"
      ) {
        const dt = new DataTransfer();
        dt.setData("text/plain", effectiveReplacement);
        const pasteEv = new ClipboardEvent("paste", {
          bubbles: true,
          cancelable: true,
          clipboardData: dt,
        });
        const dispatchOk = root.dispatchEvent(pasteEv);
        await nextMicrotask();
        if (!dispatchOk || pasteEv.defaultPrevented || getTextBeforeCaret(root) !== beforeIns) {
          insertedHandled = true;
        }
      }
    }

    return getTextBeforeCaret(root) !== beforeAll || (deletedHandled && insertedHandled);
  }

  if (effectiveDeleteCount > 0) {
    selectCharsBeforeCaret(root, doc, sel, effectiveDeleteCount);
  }

  if (effectiveReplacement.length > 0) {
    if (typeof doc.execCommand === "function") {
      const ok = doc.execCommand("insertText", false, effectiveReplacement);
      if (ok || (sel.isCollapsed && getTextBeforeCaret(root) !== beforeAll)) return true;
    }
  } else if (typeof doc.execCommand === "function") {
    const ok = doc.execCommand("delete", false);
    if (ok || (sel.isCollapsed && getTextBeforeCaret(root) !== beforeAll)) return true;
  }

  // Fallback for non-controlled environments where execCommand is unavailable
  const fallbackRange = sel.getRangeAt(0);
  fallbackRange.deleteContents();
  if (effectiveReplacement.length > 0) {
    const node = doc.createTextNode(effectiveReplacement);
    fallbackRange.insertNode(node);
    fallbackRange.setStartAfter(node);
  }
  fallbackRange.collapse(true);
  sel.removeAllRanges();
  sel.addRange(fallbackRange);
  root.dispatchEvent(
    new InputEvent("input", {
      bubbles: true,
      cancelable: false,
      inputType: effectiveReplacement.length > 0 ? "insertReplacementText" : "deleteContentBackward",
      data: effectiveReplacement.length > 0 ? effectiveReplacement : null,
    })
  );
  return true;
}

export function getEditorFullText(el: Element | null): string {
  if (!el) return "";
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    return (el as HTMLInputElement | HTMLTextAreaElement).value;
  }
  return (el as HTMLElement).innerText ?? el.textContent ?? "";
}

export function replaceEditorOrSelectionText(
  el: Element | null,
  replacement: string,
  scope: "selection" | "active-editor"
): boolean {
  if (!el || isSensitiveField(el)) return false;

  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    if (scope === "selection" && field.selectionStart !== null && field.selectionEnd !== null && field.selectionEnd > field.selectionStart) {
      field.setRangeText(replacement, field.selectionStart, field.selectionEnd, "end");
    } else {
      field.setRangeText(replacement, 0, field.value.length, "end");
    }
    field.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertReplacementText", data: replacement }));
    return true;
  }

  const htmlEl = el as HTMLElement;
  if (!htmlEl.isContentEditable) return false;
  const doc = el.ownerDocument;
  const sel = doc?.getSelection();
  if (!doc || !sel) return false;

  if (scope === "active-editor" || sel.isCollapsed) {
    const full = doc.createRange();
    full.selectNodeContents(htmlEl);
    sel.removeAllRanges();
    sel.addRange(full);
  }
  if (typeof doc.execCommand === "function" && doc.execCommand("insertText", false, replacement)) {
    return true;
  }
  htmlEl.textContent = replacement;
  htmlEl.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertReplacementText", data: replacement }));
  return true;
}

export interface CaretRect {
  left: number;
  top: number;
  bottom: number;
}

const MIRROR_PROPS = [
  "boxSizing",
  "width",
  "fontSize",
  "fontFamily",
  "fontWeight",
  "fontStyle",
  "letterSpacing",
  "textTransform",
  "wordSpacing",
  "textIndent",
  "lineHeight",
  "paddingTop",
  "paddingRight",
  "paddingBottom",
  "paddingLeft",
  "borderTopWidth",
  "borderRightWidth",
  "borderBottomWidth",
  "borderLeftWidth",
  "tabSize",
] as const;

export function getCaretViewportRect(el: Element | null): CaretRect | null {
  if (!el || typeof window === "undefined") return null;

  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    const rect = field.getBoundingClientRect();
    const pos = field.selectionStart ?? field.value.length;
    const style = window.getComputedStyle(field);
    const mirror = document.createElement("div");
    mirror.style.position = "fixed";
    mirror.style.visibility = "hidden";
    mirror.style.pointerEvents = "none";
    mirror.style.top = "0";
    mirror.style.left = "-9999px";
    mirror.style.overflow = "hidden";
    mirror.style.whiteSpace = el.tagName === "INPUT" ? "pre" : "pre-wrap";
    mirror.style.wordWrap = "break-word";

    for (const prop of MIRROR_PROPS) {
      mirror.style[prop] = style[prop];
    }

    mirror.textContent = field.value.slice(0, pos);
    const marker = document.createElement("span");
    marker.textContent = String.fromCodePoint(0x200b);
    mirror.appendChild(marker);
    document.body.appendChild(mirror);

    const markerLeft = marker.offsetLeft - field.scrollLeft;
    const markerTop = marker.offsetTop - field.scrollTop;
    const lineHeight = Number.parseFloat(style.lineHeight) || Number.parseFloat(style.fontSize) * 1.35 || 20;
    mirror.remove();

    return {
      left: rect.left + Math.max(0, Math.min(markerLeft, rect.width)),
      top: rect.top + Math.max(0, Math.min(markerTop, rect.height)),
      bottom: rect.top + Math.max(0, Math.min(markerTop + lineHeight, rect.height + 4)),
    };
  }

  const sel = el.ownerDocument?.getSelection();
  if (sel && sel.rangeCount > 0) {
    const range = sel.getRangeAt(0).cloneRange();
    range.collapse(true);
    const rects = range.getClientRects();
    const r = rects.length > 0 ? rects[0] : range.getBoundingClientRect();
    if (r && (r.width > 0 || r.height > 0 || r.top > 0 || r.left > 0)) {
      return { left: r.left, top: r.top, bottom: r.bottom || r.top + 20 };
    }
  }

  const fallback = el.getBoundingClientRect();
  return { left: fallback.left, top: fallback.top, bottom: fallback.bottom };
}
