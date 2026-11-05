import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import { analyzeTamilText, getLetters, splitUyirmei } from "../lib/engine";

describe("T008: Tamil Letter & Uyirmei Morphological Decomposer", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("segments Tamil words into grapheme clusters accurately", () => {
    const letters = getLetters("தமிழ்");
    expect(letters).toEqual(["த", "மி", "ழ்"]);

    const stateLetters = getLetters("தமிழ்நாடு");
    expect(stateLetters).toEqual(["த", "மி", "ழ்", "நா", "டு"]);
  });

  it("deconstructs composite uyirmei syllables into root consonant and vowel", () => {
    expect(splitUyirmei("பொ")).toEqual(["ப்", "ஒ"]);
    expect(splitUyirmei("த")).toEqual(["த்", "அ"]);
    expect(splitUyirmei("நா")).toEqual(["ந்", "ஆ"]);
    expect(splitUyirmei("டு")).toEqual(["ட்", "உ"]);
    expect(splitUyirmei("க்")).toBeNull();
    expect(splitUyirmei("அ")).toBeNull();
  });

  it("analyzes and categorizes vowels, consonants, uyirmei, and aytham", () => {
    const report = analyzeTamilText("அஃது");
    expect(report.total_letters).toBe(3);
    expect(report.vowel_count).toBe(1); // 'அ'
    expect(report.syllables[1].kind).toBe("aaytham"); // 'ஃ'
    expect(report.uyirmei_count).toBe(1); // 'து'
  });

  it("accurately calculates uyirmei count in sample sentences without returning 0", () => {
    const sample = "தமிழ்நாடு வாழ்க! அஃது சீரிளமைத் திறம்";
    const report = analyzeTamilText(sample);
    expect(report.uyirmei_count).toBe(13);
    expect(report.consonant_count).toBe(4);
    expect(report.vowel_count).toBe(1);
    expect(report.syllables[0].kind).toBe("uyirmei");
    expect(report.syllables[0].base_consonant).toBe("த்");
    expect(report.syllables[0].vowel).toBe("அ");
  });

  it("flags Grantha loan characters cleanly", () => {
    const report = analyzeTamilText("ஶ்ரீராம்");
    expect(report.grantha_count).toBeGreaterThan(0);
  });
});
