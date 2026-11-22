import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";
import { TRANSLIT_SCHEMES } from "../components/public-tools/TranslitTool";

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

  it("verifies EVERY TranslitTool UI sample produces its exact expected Tamil and round-trips when bidirectional", () => {
    for (const scheme of TRANSLIT_SCHEMES) {
      const toTamil = tt.transliterate(scheme.sampleLatin, scheme.id, "to_tamil");
      expect(toTamil, `scheme=${scheme.id} to_tamil`).toBe(scheme.sampleTamil);

      if (scheme.bidirectional) {
        const toLatin = tt.transliterate(scheme.sampleTamil, scheme.id, "to_latin");
        expect(toLatin, `scheme=${scheme.id} to_latin`).toBe(scheme.sampleLatin);
      }
    }
  });
});
