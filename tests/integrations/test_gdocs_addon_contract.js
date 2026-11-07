const assert = require("assert");
const { describe, it } = require("node:test");
const { hyphenateTamilWord, hyphenateString, SOFT_HYPHEN_CHAR } = require("../../integrations/google-docs-addon/Code.gs");

describe("Google Docs Add-on Engine & Apps Script Contract Tests", () => {
  it("should soft-hyphenate Tamil words accurately", () => {
    const word = "தமிழ்நாடு";
    const res = hyphenateTamilWord(word, 2, 2);
    assert(res.includes(SOFT_HYPHEN_CHAR), "Must contain soft hyphen");
    assert.strictEqual(res.replace(/\u00AD/g, ""), word, "Clean text must match input exactly");
  });

  it("should preserve punctuation and non-Tamil tokens", () => {
    const text = "பல்கலைக்கழகம் (University) - 2026!";
    const res = hyphenateString(text);
    assert(res.includes("University"));
    assert(res.includes("2026!"));
  });

  it("should be strictly idempotent across multiple passes", () => {
    const text = "தமிழ் இலக்கியக் கழகத்தின் ஆண்டு விழா மலர் வெளியீடு.";
    const p1 = hyphenateString(text);
    const p2 = hyphenateString(p1);
    const p3 = hyphenateString(p2);
    assert.strictEqual(p1, p2, "Second pass must equal first pass");
    assert.strictEqual(p2, p3, "Third pass must equal second pass");
  });

  it("simulates Google Docs DocumentApp element traversal", () => {
    const mockElements = [
      {
        text: "தொழில்நுட்பப் புரட்சி மனித வாழ்வை மாற்றியுள்ளது.",
        isPartial: () => false,
        getElement: function() {
          return {
            asText: () => ({
              getText: () => this.text,
              setText: (t) => { this.text = t; }
            })
          };
        }
      }
    ];

    let modified = 0;
    for (const el of mockElements) {
      const textEl = el.getElement().asText();
      const txt = textEl.getText();
      const hyp = hyphenateString(txt, 2, 2);
      if (hyp !== txt) {
        textEl.setText(hyp);
        modified++;
      }
    }

    assert.strictEqual(modified, 1, "Mock element must be modified");
    assert(mockElements[0].text.includes(SOFT_HYPHEN_CHAR));
  });
});
