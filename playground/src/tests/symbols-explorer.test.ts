import { describe, it, expect } from "vitest";
import { TRADITIONAL_SYMBOLS, getSymbolInfo } from "../lib/engine";

describe("T006: Traditional Tamil Fractions & Symbols Explorer", () => {
  it("contains standard Tamil base fractions with accurate rational values", () => {
    const kani = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "காணி");
    expect(kani).toBeDefined();
    expect(kani?.glyph).toBe("𑿀");
    expect(kani?.codepoint).toBe("U+11FC0");
    expect(kani?.rational?.numerator).toBe(1);
    expect(kani?.rational?.denominator).toBe(80);
    expect(kani?.decimal_value).toBe(0.0125);

    const munthiri = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "முந்திரி");
    expect(munthiri).toBeDefined();
    expect(munthiri?.glyph).toBe("𑿂");
    expect(munthiri?.rational?.numerator).toBe(1);
    expect(munthiri?.rational?.denominator).toBe(320);

    const mukkal = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "முக்கால்");
    expect(mukkal).toBeDefined();
    expect(mukkal?.glyph).toBe("𑿔");
    expect(mukkal?.rational?.numerator).toBe(3);
    expect(mukkal?.rational?.denominator).toBe(4);
    expect(mukkal?.decimal_value).toBe(0.75);
  });

  it("contains historic land, volume, and currency measurement symbols", () => {
    const veli = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "வேலி");
    expect(veli).toBeDefined();
    expect(veli?.category).toBe("land");
    expect(veli?.glyph).toBe("𑿟");

    const kalam = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "கலம்");
    expect(kalam).toBeDefined();
    expect(kalam?.category).toBe("volume");
    expect(kalam?.glyph).toBe("𑿘");

    const kasu = TRADITIONAL_SYMBOLS.find((s) => s.name_ta === "காசு");
    expect(kasu).toBeDefined();
    expect(kasu?.category).toBe("currency");
    expect(kasu?.glyph).toBe("𑿢");
  });

  it("retrieves symbol info by glyph and codepoint", () => {
    const info = getSymbolInfo("𑿀");
    expect(info).not.toBeNull();
    expect(info?.name_ta).toBe("காணி");
    expect(info?.category).toBe("fraction");
  });
});
