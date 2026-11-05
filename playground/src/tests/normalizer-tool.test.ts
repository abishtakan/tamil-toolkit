import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import { normalizeNfc, normalizeNfd, repairTamilText, auditAndNormalizeTamil } from "../lib/engine";

describe("T010: Tamil Unicode Text Normalizer & Anomaly Repair", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("normalizes text to canonical NFC standard", () => {
    const input = "தமிழ்";
    const nfc = normalizeNfc(input);
    expect(nfc).toBe("தமிழ்");
  });

  it("converts two-part vowel signs to decomposed NFD and round-trips to NFC", () => {
    // "கொ" is composed U+0B95 U+0BCA (length 2 in codepoints)
    // In NFD, it decomposes to U+0B95 U+0BC6 U+0BBE (length 3 in codepoints)
    const input = "கொங்கு கோட்டை கௌதமன்";
    const nfd = normalizeNfd(input);
    expect(nfd).not.toBe(input);
    expect(Array.from(nfd).length).toBeGreaterThan(Array.from(input).length);

    // Round-trip back to canonical NFC
    const nfcRoundtrip = normalizeNfc(nfd);
    expect(nfcRoundtrip).toBe(input);
  });

  it("detects and repairs duplicate pulli anomalies", () => {
    const pulli = String.fromCharCode(0x0bcd);
    const malformed = "க" + pulli + pulli + "கு";
    const audit = auditAndNormalizeTamil(malformed);
    expect(audit.isClean).toBe(false);
    expect(audit.anomalyCount).toBeGreaterThan(0);
    expect(audit.anomalies.some((a) => a.type === "duplicate_pulli")).toBe(true);

    // Verified repair: collapses duplicate pulli to single pulli
    const repaired = repairTamilText(malformed);
    expect(repaired).toBe("க்" + "கு");
  });

  it("detects and strips stray invisible format controls (ZWJ / ZWNJ)", () => {
    const zwj = String.fromCharCode(0x200d);
    const withZwj = "தமிழ்" + zwj + "நாடு";
    const audit = auditAndNormalizeTamil(withZwj);
    expect(audit.isClean).toBe(false);
    expect(audit.anomalies.some((a) => a.type === "stray_format_control")).toBe(true);

    const repaired = repairTamilText(withZwj);
    expect(repaired).toBe("தமிழ்நாடு");
    expect(repaired.includes(zwj)).toBe(false);
  });

  it("confirms already clean text as clean", () => {
    const clean = "வணக்கம் வாழ்க";
    const audit = auditAndNormalizeTamil(clean);
    expect(audit.isClean).toBe(true);
    expect(audit.anomalyCount).toBe(0);
    expect(audit.repairedText).toBe(clean);
  });
});
