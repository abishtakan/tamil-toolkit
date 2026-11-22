import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";

describe("Phase 8: TranslitTool & tamil-translit WASM bindings", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("lists all 8 supported transliteration and keyboard schemes", () => {
    const schemes = tt.transliterate_schemes();
    const ids = schemes.map((s) => s.id);
    expect(ids).toHaveLength(8);
    expect(ids).toContain("iso-15919");
    expect(ids).toContain("tamil99");
    expect(ids).toContain("anjal-phonetic");
    expect(ids).toContain("phonetic-v1");
  });

  it("round-trips scholarly ISO 15919 and converts Tamil99 & Anjal Phonetic", () => {
    const tamil = "தமிழ்";
    const latin = tt.transliterate(tamil, "iso-15919", "to_latin");
    expect(latin).toBe("tamiḻ");
    expect(tt.transliterate(latin, "iso-15919", "to_tamil")).toBe(tamil);

    expect(tt.transliterate("thamizh", "anjal-phonetic", "to_tamil")).toBe("தமிழ்");
    expect(tt.transliterate("jkpo;", "suratha-bamini", "to_tamil")).toBe("தமிழ்");
  });
});
