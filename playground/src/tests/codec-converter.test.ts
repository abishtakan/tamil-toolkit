import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("T015: CodecConverter & Auto-detection", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("converts Bamini text to Unicode", () => {
    // Bamini for "வணக்கம்" is typically "tzf;fk;" or similar legacy encoding pattern
    const unicodeText = "வணக்கம்";
    const bamini = tt.unicode_to_bamini(unicodeText);
    expect(bamini).toBeTruthy();

    const backToUnicode = tt.bamini_to_unicode(bamini);
    expect(backToUnicode).toBe(unicodeText);
  });

  it("auto-detects legacy encoding format", () => {
    const unicodeText = "தமிழ்நாடு";
    const bamini = tt.unicode_to_bamini(unicodeText);
    const encoder = new TextEncoder();
    const bytes = encoder.encode(bamini);

    const detected = tt.detect_encoding(bytes);
    expect(detected).toBeDefined();
    expect(detected.candidates.length).toBeGreaterThan(0);
  });

  it("round-trips TSCII bytes to Unicode and back", () => {
    const unicodeText = "தமிழ்";
    const tsciiBytes = tt.unicode_to_tscii_bytes(unicodeText);
    expect(tsciiBytes.length).toBeGreaterThan(0);

    const backToUnicode = tt.tscii_bytes_to_unicode(new Uint8Array(tsciiBytes));
    expect(backToUnicode).toBe(unicodeText);
  });

  it("round-trips Phase 7B CID fonts (Senthamil, Shree-Tam, Softview, TBO) and Bharathi Braille", () => {
    const word = "தமிழ்";

    const senthamil = tt.unicode_to_senthamil_text(word);
    expect(tt.senthamil_text_to_unicode(senthamil, "preserve")).toBe(word);

    const shree = tt.unicode_to_shree_tam_text(word);
    expect(tt.shree_tam_text_to_unicode(shree, "preserve")).toBe(word);

    const softview = tt.unicode_to_softview_text(word);
    expect(tt.softview_text_to_unicode(softview, "preserve")).toBe(word);

    const tbo = tt.unicode_to_tbo_text(word);
    expect(tt.tbo_text_to_unicode(tbo, "preserve")).toBe(word);

    const braille = tt.unicode_to_braille(word, "preserve");
    expect(braille.length).toBeGreaterThan(0);
    expect(tt.braille_to_unicode(braille, "preserve")).toBe(word);
  });
});
