import { describe, it, expect } from "vitest";
import {
  hyphenateWord,
  getHyphenationPoints,
  hyphenateText,
  wrapText,
  getLetters
} from "../lib/engine";
import { translations } from "../lib/i18n";
import { getLineStartError } from "../components/public-tools/HyphenatorTool";

describe("T010: Syllabic Hyphenator & Line Wrapper", () => {
  describe("Word Syllabification & Hyphenation", () => {
    it("deconstructs multi-syllable Tamil words into syllables", () => {
      const res = hyphenateWord("தமிழ்நாடு", { delimiter: "-" });
      expect(res.syllables).toBeDefined();
      expect(res.syllables.length).toBe(4);
      // Letters: த, மி, ழ், நா, டு -> syllables: த, மிழ், நா, டு
      expect(res.syllables).toEqual(["த", "மிழ்", "நா", "டு"]);
      expect(res.hyphenated).toBe("தமிழ்-நாடு");
    });

    it("strictly preserves the coda binding invariant (no segment starts with a pure consonant)", () => {
      const words = [
        "பல்கலைக்கழகம்",
        "தமிழ்நாடு",
        "திருக்குறள்",
        "வணக்கம்",
        "செம்மொழி",
        "அகிலத்திரட்டு"
      ];

      for (const word of words) {
        const hyphenated = hyphenateWord(word, { delimiter: "-" }).hyphenated;
        const segments = hyphenated.split("-");

        for (let i = 0; i < segments.length; i++) {
          const seg = segments[i];
          expect(seg.length).toBeGreaterThan(0);
          // Check if segment starts with a pulli / virama (U+0BCD)
          if (seg.length > 1) {
            expect(
              seg.charAt(1) === "\u0BCD",
              `Segment "${seg}" in word "${word}" illegally starts with a pulli consonant!`
            ).toBe(false);
          }
        }
      }
    });

    it("respects left_min and right_min margin constraints", () => {
      // "பல்கலைக்கழகம்" (பல்-க-லைக்-க-ழ-கம்)
      const resDefault = getHyphenationPoints("பல்கலைக்கழகம்", {
        left_min: 2,
        right_min: 2
      });

      // With higher margins (e.g. left_min: 4, right_min: 4), fewer points exist
      const resStrict = getHyphenationPoints("பல்கலைக்கழகம்", {
        left_min: 4,
        right_min: 4
      });

      expect(resDefault.length).toBeGreaterThanOrEqual(resStrict.length);
      expect(resDefault.length).toBeGreaterThan(0);
    });

    it("supports custom syllable delimiters", () => {
      const bullet = hyphenateWord("தமிழ்நாடு", { delimiter: "·" });
      expect(bullet.hyphenated).toContain("·");

      const slash = hyphenateWord("தமிழ்நாடு", { delimiter: "/" });
      expect(slash.hyphenated).toContain("/");
    });

    it("handles short words cleanly without invalid breaks", () => {
      const shortWord = "கல்";
      const res = hyphenateWord(shortWord, { left_min: 2, right_min: 2 });
      expect(res.hyphenated).toBe("கல்");

      const pts = getHyphenationPoints(shortWord, { left_min: 2, right_min: 2 });
      expect(pts.length).toBe(0);
    });
  });

  describe("Paragraph Soft-Hyphen Injection", () => {
    it("injects soft hyphens into long words in a paragraph", () => {
      const text = "பல்கலைக்கழகங்களில் ஆராய்ச்சிகள் உலகளாவிய தரத்தில் செழுமை பெற வேண்டும்.";
      const resHtml = hyphenateText(text, { delimiter: "&shy;" });
      expect(resHtml).toContain("&shy;");

      const resUnicode = hyphenateText(text, { delimiter: "\u00AD" });
      expect(resUnicode).toContain("\u00AD");
    });
  });

  describe("Column Line Wrapping Simulator", () => {
    it("wraps text into lines according to width without breaking pulli to newline", () => {
      const text =
        "பல்கலைக்கழகங்களில் தமிழ் மொழியியல் மற்றும் இலக்கிய ஆராய்ச்சிகள் உலகளாவிய தரத்தில் செழுமை பெற வேண்டும்.";
      const wrapped = wrapText(text, 15);

      expect(wrapped.lines.length).toBeGreaterThan(1);

      for (const line of wrapped.lines) {
        const error = getLineStartError(line);
        expect(
          error,
          `Syllabic wrapped line "${line}" has invalid line start error: ${error?.label}`
        ).toBeNull();
      }
    });
  });

  describe("Line Start Error Classifier (getLineStartError)", () => {
    it("flags naked pulli / virama at start of line (U+0BCD)", () => {
      // Line starting with isolated pulli from broken word
      const lineWithPulli = "\u0BCDதிரட்டு போன்ற அரிய நூ-";
      const errTa = getLineStartError(lineWithPulli, translations.ta.tools.hyphenator);
      expect(errTa).not.toBeNull();
      expect(errTa?.type).toBe("pulli");
      expect(errTa?.label).toBe("(தனிப் புள்ளித் தொடக்கம்!)");

      const errEn = getLineStartError(lineWithPulli, translations.en.tools.hyphenator);
      expect(errEn?.label).toBe("(Orphaned Pulli / Virama!)");
    });

    it("flags naked visiri at start of line (U+0BBF and U+0BC0)", () => {
      const lineVisiriKuril = "\u0BBFரட்டு போன்ற அரிய";
      const errKuril = getLineStartError(lineVisiriKuril, translations.ta.tools.hyphenator);
      expect(errKuril).not.toBeNull();
      expect(errKuril?.type).toBe("visiri");
      expect(errKuril?.label).toBe("(விசிறி மட்டும் தொடக்கம்!)");

      const lineVisiriNedil = "\u0BC0ரட்டு போன்ற அரிய";
      const errNedil = getLineStartError(lineVisiriNedil, translations.en.tools.hyphenator);
      expect(errNedil).not.toBeNull();
      expect(errNedil?.type).toBe("visiri");
      expect(errNedil?.label).toBe("(Orphaned Visiri ி/ீ!)");
    });

    it("flags other orphaned combining vowel signs (thunaikkaal, kombu, etc.)", () => {
      const lineThunaikkaal = "\u0BBEதுகாக்க வேண்டியது";
      const err1 = getLineStartError(lineThunaikkaal);
      expect(err1).not.toBeNull();
      expect(err1?.type).toBe("diacritic");

      const lineKombu = "\u0BC6 பெற வேண்டும்";
      const err2 = getLineStartError(lineKombu);
      expect(err2).not.toBeNull();
      expect(err2?.type).toBe("diacritic");
    });

    it("flags lines starting with pure consonants (Mei / ஒற்று)", () => {
      // ழ் (\u0BB4\u0BCD)
      const lineZha = "ழ் மொழியியல் மற்றும்";
      const errZha = getLineStartError(lineZha, translations.ta.tools.hyphenator);
      expect(errZha).not.toBeNull();
      expect(errZha?.type).toBe("mei");
      expect(errZha?.label).toBe("(புள்ளி எழுத்தில் தொடக்கம்!)");

      // ல் (\u0BB2\u0BCD)
      const lineL = "ல்களின் ஓலைச்சுவடிப்";
      const errL = getLineStartError(lineL, translations.en.tools.hyphenator);
      expect(errL).not.toBeNull();
      expect(errL?.type).toBe("mei");
      expect(errL?.label).toBe("(Starts with Pure Consonant / Mei!)");
    });

    it("flags lines starting with Aytham (ஃ / U+0B83)", () => {
      const lineAytham = "ஃது ஊழி பெயரினும்";
      const err = getLineStartError(lineAytham, translations.ta.tools.hyphenator);
      expect(err).not.toBeNull();
      expect(err?.type).toBe("aytham");
      expect(err?.label).toBe("(ஆய்த எழுத்தில் தொடக்கம்!)");
    });

    it("returns null for valid syllable line starts", () => {
      expect(getLineStartError("பல்கலைக்கழகங்களில்")).toBeNull();
      expect(getLineStartError("தமிழ்நாடு வாழ்க")).toBeNull();
      expect(getLineStartError("திரட்டு போன்ற அரிய")).toBeNull();
      expect(getLineStartError("உலகளாவிய தரத்தில்")).toBeNull();
      expect(getLineStartError("")).toBeNull();
      expect(getLineStartError("   ")).toBeNull();
    });
  });

  describe("i18n Translation Completeness", () => {
    it("contains all hyphenator keys in both ta and en locales", () => {
      expect(translations.ta.tools.hyphenator).toBeDefined();
      expect(translations.en.tools.hyphenator).toBeDefined();

      const taKeys = Object.keys(translations.ta.tools.hyphenator).sort();
      const enKeys = Object.keys(translations.en.tools.hyphenator).sort();

      expect(taKeys).toEqual(enKeys);
      expect(translations.ta.tools.hyphenator.title).toContain("அசையசைப்பி");
      expect(translations.en.tools.hyphenator.title).toContain("Syllabic Hyphenator");
    });
  });
});
