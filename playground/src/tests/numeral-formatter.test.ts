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

  it("supports Phase 6 diaspora currencies, mixed fraction words, and words_to_number (ITN)", () => {
    const sgd = tt.currency_decimal_to_words("1250.50", "latin", "SGD", "TN", "none");
    expect(sgd).toContain("சிங்கப்பூர் டாலர்");

    const usd = tt.currency_decimal_to_words("100", "latin", "USD", "TN", "none");
    expect(usd).toContain("டாலர்");

    const half = tt.mixed_fraction_to_words(
      { negative: false, whole: 1, numerator: 1, denominator: 2 },
      "TN"
    );
    expect(half).toBe("ஒன்றரை");

    expect(tt.words_to_number("நூற்று இருபத்து மூன்று", "TN")).toBe(123);
  });
});
