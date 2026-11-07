const assert = require("assert");
const { describe, it } = require("node:test");
const {
  hyphenateText,
  hyphenateWord,
  removeHyphens,
  hyphenateOoxml,
  removeOoxmlHyphens,
  getTamilLetters,
  SOFT_HYPHEN
} = require("../../integrations/office-word-addin/engine.js");

describe("Word Add-in Engine & Office.js Contract Tests", () => {
  it("should soft-hyphenate Tamil words at phonotactic syllable boundaries", () => {
    const input = "தமிழ்நாடு";
    const result = hyphenateWord(input, 2, 2);
    assert(result.includes(SOFT_HYPHEN), "Expected soft hyphen in word");
    assert.strictEqual(result.replace(/\u00AD/g, ""), input, "Stripping soft hyphens must yield exact input");
  });

  it("should preserve English and punctuation runs untouched", () => {
    const input = "வணக்கம் (Welcome) 123!";
    const result = hyphenateText(input);
    assert(result.includes("Welcome"), "English words must remain intact");
    assert(result.includes("123!"), "Numbers and symbols must remain intact");
  });

  it("should be strictly idempotent", () => {
    const input = "வானூர்தி நிலையத்திற்கு வருகை தந்த பயணிகளுக்கு வாழ்த்துகள்.";
    const run1 = hyphenateText(input);
    const run2 = hyphenateText(run1);
    const run3 = hyphenateText(run2);
    assert.strictEqual(run1, run2, "Second run must match first run exactly");
    assert.strictEqual(run2, run3, "Third run must match second run exactly");
  });

  it("should inject native <w:softHyphen/> elements into Word OOXML and remain idempotent", () => {
    const sampleOoxml = `<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>பல்கலைக்கழகம் மற்றும் Welcome</w:t></w:r></w:p>`;
    const ooxml1 = hyphenateOoxml(sampleOoxml, 2, 2);
    assert(ooxml1.includes("<w:softHyphen/>"), "Must contain native <w:softHyphen/> tag");
    assert(!ooxml1.includes(SOFT_HYPHEN), "Must NOT contain raw U+00AD inside <w:t>");
    assert(ooxml1.includes("<w:rPr><w:b/></w:rPr>"), "Run properties must be preserved");

    // Idempotency check on OOXML
    const ooxml2 = hyphenateOoxml(ooxml1, 2, 2);
    assert.strictEqual(ooxml1, ooxml2, "hyphenateOoxml must be strictly idempotent");

    // Removal check on OOXML
    const cleaned = removeOoxmlHyphens(ooxml2);
    assert(!cleaned.includes("<w:softHyphen/>"), "removeOoxmlHyphens must remove all <w:softHyphen/> tags");
    assert(cleaned.includes(">பல்கலைக்கழகம் மற்றும் Welcome</w:t>"), "Text must be cleanly merged back into single <w:t>");
  });

  it("should cleanly remove soft hyphens with removeHyphens", () => {
    const text = "வணக்\u00ADகம்";
    const cleaned = removeHyphens(text);
    assert.strictEqual(cleaned, "வணக்கம்");
    assert.strictEqual(cleaned.includes(SOFT_HYPHEN), false);
  });

  it("should segment tailored Tamil letters including Grantha", () => {
    const letters = getTamilLetters("தமிழ்நாடு மற்றும் ஶ்ரீலங்கா");
    assert(letters.includes("த"));
    assert(letters.includes("மி"));
    assert(letters.includes("ழ்"));
    assert(letters.includes("ஶ்ரீ"));
  });
});
