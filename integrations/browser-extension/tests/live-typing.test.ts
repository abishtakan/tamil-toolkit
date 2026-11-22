import { describe, expect, it } from "vitest";
import { HybridTypingEngine } from "../src/content/live-typing.js";
import { isSensitiveField } from "../src/content/editor-adapter.js";
import { commitModeForLayout } from "../src/shared/messages.js";

const mockTranslit = async (raw: string, layout: string): Promise<string> => {
  if (layout === "phonetic-v1" || layout === "anjal-phonetic") {
    if (raw === "vanakkam") return "\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD";
    if (raw === "tamil") return "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
  }
  if (layout === "tamil99") {
    if (raw === "h") return "\u0B95";
    if (raw === "hq") return "\u0B95\u0BBE";
    if (raw === ";") return "\u0BA8";
    if (raw === "]") return "\u0B9E";
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
});
