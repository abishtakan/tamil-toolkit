import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("T016: NumeralFormatter", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("converts numbers to formal words", () => {
    const words = tt.to_words(125000);
    expect(words).toContain("லட்சத்து");
  });

  it("converts currency amount to Tamil words in minor units", () => {
    // 125000 INR = 12500000 paise
    const words = tt.currency_to_words(12500000, "INR", "TN");
    expect(words).toContain("ரூபாய்");
  });

  it("formats traditional Tamil integer numerals", () => {
    const traditional = tt.format_traditional_integer(10);
    expect(traditional).toBe("௰"); // Traditional symbol for 10
  });
});
