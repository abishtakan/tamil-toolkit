import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";
import { TOKENIZER_SAMPLES } from "../components/public-tools/TokenizerTool";

describe("Phase 9: TokenizerTool & tamil-tokenize WASM bindings", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("tokenizes all TokenizerTool UI samples with exact UTF-8 byte slicing", () => {
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    for (const sample of TOKENIZER_SAMPLES) {
      const bytes = encoder.encode(sample.text);
      const words = tt.tokenize_words(sample.text, "none");
      expect(words.length, `sample=${sample.id} words`).toBeGreaterThan(0);
      for (const tok of words) {
        expect(decoder.decode(bytes.slice(tok.start_byte, tok.end_byte))).toBe(tok.text);
        expect(tok.end_byte).toBeGreaterThan(tok.start_byte);
        expect(tok.end_unit).toBeGreaterThan(tok.start_unit);
      }

      const sentences = tt.segment_sentences(sample.text);
      expect(sentences.length, `sample=${sample.id} sentences`).toBeGreaterThan(0);
      for (const sent of sentences) {
        expect(decoder.decode(bytes.slice(sent.start_byte, sent.end_byte))).toBe(sent.text);
      }
    }
  });

  it("keeps attested Tamil abbreviations intact across sentences and splits adjacent tokens", () => {
    const sample = TOKENIZER_SAMPLES[0].text;
    const sentences = tt.segment_sentences(sample);
    expect(sentences).toHaveLength(2);
    expect(sentences[0].text).toBe("திரு. குமார் மற்றும் மு.க. அவர்கள் வந்தார்.");
    expect(sentences[1].text).toBe("ரூ.100 அல்லது ரூ. 250 வழங்கப்பட்டது.");

    const words = tt.tokenize_words(sample, "none");
    const abbrevs = words.filter((w) => w.kind === "abbreviation").map((w) => w.text);
    expect(abbrevs).toEqual(["திரு.", "மு.க.", "ரூ.", "ரூ."]);
  });

  it("applies none, conservative, and broad stopword profiles while preserving original offsets", () => {
    const text = "தமிழ் மற்றும் ஆங்கிலம் அல்லது பிரெஞ்சு போன்ற மொழிகள்";
    const none = tt.tokenize_words(text, "none");
    const conservative = tt.tokenize_words(text, "conservative");
    const broad = tt.tokenize_words(text, "broad");

    expect(none.map((t) => t.text)).toContain("மற்றும்");
    expect(none.map((t) => t.text)).toContain("அல்லது");
    expect(none.map((t) => t.text)).toContain("போன்ற");

    expect(conservative.map((t) => t.text)).not.toContain("மற்றும்");
    expect(conservative.map((t) => t.text)).not.toContain("அல்லது");
    expect(conservative.map((t) => t.text)).toContain("போன்ற");

    expect(broad.map((t) => t.text)).not.toContain("போன்ற");
    expect(broad.length).toBeLessThan(conservative.length);

    // Surviving tokens keep identical original byte/unit ranges
    const lastNone = none[none.length - 1];
    const lastBroad = broad[broad.length - 1];
    expect(lastBroad).toEqual(lastNone);
  });
});
