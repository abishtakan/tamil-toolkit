import fs from "node:fs";
import path from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { inspectText } from "../src/engine/inspect.js";
import {
  api,
  convertLegacyToUnicode,
  convertNumberToWords,
  getCivilDateAndHolidays,
  initTamilEngineSync,
  repairTamil,
  sortLines,
  transliterateToTamil,
} from "../src/engine/tamil-engine.js";

beforeAll(() => {
  const wasmPath = path.resolve(import.meta.dirname, "..", "src", "wasm", "tamil_toolkit_bg.wasm");
  const wasmBytes = fs.readFileSync(wasmPath);
  initTamilEngineSync(wasmBytes);
});

describe("Canonical slim WASM engine adapter", () => {
  it("US1: transliterates across phonetic-v1, tamil99, anjal-phonetic, and suratha-bamini", () => {
    expect(transliterateToTamil("vaNakkam", "phonetic-v1")).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD");
    expect(transliterateToTamil("thamizh", "phonetic-v1")).toBe("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD");
    expect(transliterateToTamil("vaNakkam", "anjal-phonetic")).toBe("\u0BB5\u0BA3\u0B95\u0BCD\u0B95\u0BAE\u0BCD");
    expect(transliterateToTamil("h", "tamil99")).toBe("\u0B95");
    expect(transliterateToTamil("f", "suratha-bamini")).toBe("\u0B95");
    expect(transliterateToTamil("jkpo;", "suratha-bamini")).toBe("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD");
  });

  it("US2: inspects true Tamil letter count, category breakdown, and Unicode health", () => {
    // \u0BA4\u0BAE\u0BBF\u0BB4\u0BCD = 3 true Tamil letters (Uyirmei + Uyirmei + Mei) vs 5 UTF-16 code units
    const clean = inspectText("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD", "selection", true);
    expect(clean.letterCount).toBe(3);
    expect(clean.utf16Length).toBe(5);
    expect(clean.wordCount).toBe(1);
    expect(clean.breakdown.uyirmei).toBe(2);
    expect(clean.breakdown.mei).toBe(1);
    expect(clean.health.isNfc).toBe(true);
    expect(clean.health.totalIssues).toBe(0);

    // Visual left-kombu (\u0BC6\u0B9A) + duplicate pulli (\u0BA4\u0BCD\u0BCD)
    const broken = inspectText("\u0BC6\u0B9A\u0BA9\u0BCD\u0BCD\u0BA9\u0BC8", "active-editor", true);
    expect(broken.health.visualKombus).toBeGreaterThanOrEqual(1);
    expect(broken.health.duplicatePullis).toBeGreaterThanOrEqual(1);
    expect(broken.health.totalIssues).toBeGreaterThanOrEqual(2);
  });

  it("US3: repairs Tamil while preserving ZWJ/ZWNJ, converts legacy codecs, and sorts lines", () => {
    const zwj = String.fromCodePoint(0x200d);
    const withJoiner = `\u0BC6\u0B9A\u0BA9\u0BCD\u0BCD\u0BA9\u0BC8${zwj}`;
    const repaired = repairTamil(withJoiner);
    expect(repaired.text).toContain(zwj);
    expect(repaired.text).toContain("\u0B9A\u0BC6");
    expect(repaired.diagnostics.duplicate_pulli_count).toBeGreaterThanOrEqual(1);

    const bamini = convertLegacyToUnicode("jkpo;", "bamini");
    expect(bamini.ambiguous).toBe(false);
    expect(bamini.text).toBe("\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD");

    const sample = "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
    const fromBytes = (bytes: number[]) => bytes.map((b) => String.fromCharCode(b & 0xff)).join("");

    expect(convertLegacyToUnicode(fromBytes(api.unicode_to_tscii_bytes(sample)), "tscii").text).toBe(sample);
    expect(convertLegacyToUnicode(fromBytes(api.unicode_to_tab_bytes(sample)), "tab").text).toBe(sample);
    expect(convertLegacyToUnicode(fromBytes(api.unicode_to_tam_bytes(sample)), "tam").text).toBe(sample);
    expect(convertLegacyToUnicode(fromBytes(api.unicode_to_anjal_bytes(sample)), "anjal").text).toBe(sample);
    expect(convertLegacyToUnicode(api.unicode_to_vanavil_text(sample), "vanavil").text).toBe(sample);
    expect(convertLegacyToUnicode(api.unicode_to_lt_tm_text(sample), "lt_tm").text).toBe(sample);

    // Auto-detect ambiguity guard on short ASCII text
    const ambiguousAuto = convertLegacyToUnicode("abc", "auto");
    expect(ambiguousAuto.ambiguous).toBe(true);

    const sortedAgara = sortLines("\u0B95\u0BAE\u0BB2\u0BAE\u0BCD\n\u0B85\u0BAE\u0BCD\u0BAE\u0BBE\n\u0B86\u0B9F\u0BC1", "agara-v1");
    expect(sortedAgara.split("\n")).toEqual([
      "\u0B85\u0BAE\u0BCD\u0BAE\u0BBE",
      "\u0B86\u0B9F\u0BC1",
      "\u0B95\u0BAE\u0BB2\u0BAE\u0BCD",
    ]);

    const sortedUyirmei = sortLines("\u0B95\u0BCD\n\u0B95\n\u0B95\u0BBE", "uyirmei-first-v1");
    expect(sortedUyirmei.split("\n")).toEqual(["\u0B95", "\u0B95\u0BBE", "\u0B95\u0BCD"]);
  });

  it("US4: converts TN/SL numerals & currencies and loads active civil date / holidays", () => {
    const inr = convertNumberToWords("2500", "TN", "INR");
    expect(inr.words.length).toBeGreaterThan(5);

    const lkr = convertNumberToWords("2500", "SL", "LKR");
    expect(lkr.words.length).toBeGreaterThan(5);

    const supported = getCivilDateAndHolidays(2026, 4, 14, "TN");
    expect(supported.civilDateLabel.length).toBeGreaterThan(3);
    expect(supported.supportedYear).toBe(true);
    expect(supported.holidays.length).toBeGreaterThan(0);
    expect(supported.holidays[0].date).toMatch(/^\d{4}-\d{2}-\d{2}$/);

    const unsupported = getCivilDateAndHolidays(1800, 1, 1, "TN");
    expect(unsupported.supportedYear).toBe(false);
    expect(unsupported.holidays).toEqual([]);
  });
});
