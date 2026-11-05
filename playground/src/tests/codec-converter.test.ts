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
});
