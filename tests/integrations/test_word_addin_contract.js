const assert = require("assert");
const { describe, it } = require("node:test");
const { hyphenateText, hyphenateWord, removeHyphens, getTamilLetters, SOFT_HYPHEN } = require("../../integrations/office-word-addin/engine.js");

describe("Word Add-in Engine & Office.js Contract Tests", () => {
  it("should soft-hyphenate Tamil words at phonotactic syllable boundaries", () => {
    const input = "தமிழ்நாடு";
    const result = hyphenateWord(input, 2, 2);
    // த-மிழ்-நா-டு with leftMin=2, rightMin=2: syllables are ["த", "மிழ்", "நா", "டு"]
    // valid boundaries after syllable 2 (after "மிழ்"): "தமிழ்\u00ADநாடு"
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

  it("simulates Word.run paragraph traversal correctly", async () => {
    // Mock Office Word environment
    const mockDocument = {
      body: {
        paragraphs: {
          items: [
            {
              text: "தமிழ்நாடு அரசு தொல்லியல் துறை வெளியீடு.",
              insertText(newText, location) {
                this.text = newText;
              }
            },
            {
              text: "English paragraph untouched.",
              insertText(newText, location) {
                this.text = newText;
              }
            }
          ]
        }
      }
    };

    let modified = 0;
    for (const para of mockDocument.body.paragraphs.items) {
      if (/[\u0B80-\u0BFF]/.test(para.text)) {
        const hyphenated = hyphenateText(para.text, 2, 2);
        if (hyphenated !== para.text) {
          para.insertText(hyphenated, "replace");
          modified++;
        }
      }
    }

    assert.strictEqual(modified, 1, "Only the Tamil paragraph should be modified");
    assert(mockDocument.body.paragraphs.items[0].text.includes(SOFT_HYPHEN));
    assert.strictEqual(mockDocument.body.paragraphs.items[1].text, "English paragraph untouched.");
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
