import { describe, it, expect } from "vitest";
import { translations } from "../lib/i18n";

describe("i18n Bilingual Architecture", () => {
  it("enforces complete key parity between Tamil (ta) and English (en)", () => {
    function getDeepKeys(obj: Record<string, unknown>, prefix = ""): string[] {
      return Object.keys(obj).flatMap((key) => {
        const val = obj[key];
        const newPrefix = prefix ? `${prefix}.${key}` : key;
        if (typeof val === "object" && val !== null) {
          return getDeepKeys(val as Record<string, unknown>, newPrefix);
        }
        return [newPrefix];
      });
    }

    const taKeys = getDeepKeys(translations.ta as unknown as Record<string, unknown>).sort();
    const enKeys = getDeepKeys(translations.en as unknown as Record<string, unknown>).sort();

    expect(taKeys).toEqual(enKeys);
    expect(taKeys.length).toBeGreaterThan(45);
  });

  it("ensures no translation strings are empty or undefined", () => {
    function assertNoEmptyValues(obj: Record<string, unknown>, path = "") {
      for (const [key, val] of Object.entries(obj)) {
        const currentPath = path ? `${path}.${key}` : key;
        if (typeof val === "string") {
          expect(val.trim().length, `Empty translation at ${currentPath}`).toBeGreaterThan(0);
        } else if (typeof val === "object" && val !== null) {
          assertNoEmptyValues(val as Record<string, unknown>, currentPath);
        }
      }
    }

    assertNoEmptyValues(translations.ta as unknown as Record<string, unknown>, "ta");
    assertNoEmptyValues(translations.en as unknown as Record<string, unknown>, "en");
  });

  it("provides localized document titles for both locales", () => {
    expect(translations.ta.documentTitle).toContain("தமிழ் கருவிப் பட்டறை");
    expect(translations.en.documentTitle).toContain("Tamil Toolkit Playground");
  });

  it("provides authentic un-slopped workbench copy", () => {
    expect(translations.ta.hub.engineStatus).toContain("WebAssembly");
    expect(translations.en.hub.engineStatus).toContain("WASM");
    expect(translations.ta.hub.featuredBadge).toBe("முதன்மைக் கருவி");
    expect(translations.en.hub.featuredBadge).toBe("Featured Tool");
    expect(translations.ta.hub.launchTool).toBe("பயன்படுத்துக");
    expect(translations.en.hub.launchTool).toBe("Open Utility");
  });

  it("provides comprehensive hub tag translations", () => {
    expect(translations.ta.hub.tags.realtime).toBe("நிகழ்நேரம்");
    expect(translations.en.hub.tags.realtime).toBe("Real-time");
    expect(translations.ta.hub.tags.financial).toBe("நிதி");
    expect(translations.en.hub.tags.financial).toBe("Financial");
    expect(translations.ta.hub.tags.solar).toBe("சூரியன்");
    expect(translations.en.hub.tags.solar).toBe("Solar / Drik");
  });
});
