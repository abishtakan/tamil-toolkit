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

export function detectEditorKind(el: Element | null, doc: Document = document): EditorKind {
  if (isCanvasEditorDocument(doc)) {
    return "canvas-fallback";
  }
  if (!el || isSensitiveField(el)) {
    return "none";
  }
  if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
    return "native-input";
  }
  const htmlEl = el as HTMLElement;
  if (htmlEl.isContentEditable) {
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
  if (range.startContainer.nodeType === Node.TEXT_NODE) {
    return (range.startContainer.textContent ?? "").slice(0, range.startOffset);
  }
  return "";
}

export function replaceCharsBeforeCaret(el: Element, deleteCount: number, replacement: string): boolean {
  if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
    const field = el as HTMLInputElement | HTMLTextAreaElement;
    const end = field.selectionStart ?? field.value.length;
    const start = Math.max(0, end - deleteCount);
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

  const range = sel.getRangeAt(0);
  if (range.startContainer.nodeType === Node.TEXT_NODE && deleteCount > 0) {
    const startOffset = Math.max(0, range.startOffset - deleteCount);
    const replaceRange = doc.createRange();
    replaceRange.setStart(range.startContainer, startOffset);
    replaceRange.setEnd(range.startContainer, range.startOffset);
    sel.removeAllRanges();
    sel.addRange(replaceRange);
  }

  if (typeof doc.execCommand === "function") {
    const ok = doc.execCommand("insertText", false, replacement);
    if (ok) return true;
  }

  // Fallback for environments where execCommand is unavailable
  const fallbackRange = sel.getRangeAt(0);
  fallbackRange.deleteContents();
  const node = doc.createTextNode(replacement);
  fallbackRange.insertNode(node);
  fallbackRange.setStartAfter(node);
  fallbackRange.collapse(true);
  sel.removeAllRanges();
  sel.addRange(fallbackRange);
  el.dispatchEvent(
    new InputEvent("input", {
      bubbles: true,
      cancelable: false,
      inputType: "insertReplacementText",
      data: replacement,
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
