import { describe, it, expect, beforeAll } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import * as tt from "tamil-toolkit/web";
import {
  PUNARCHI_JOIN_PRESETS,
  PUNARCHI_SPLIT_PRESETS,
} from "../components/public-tools/PunarchiTool";
import punarchiReviewRaw from "../generated/punarchi-review-data.json";

describe("Phase 10: PunarchiTool & tamil-punarchi WASM workbench", () => {
  beforeAll(async () => {
    await ensureToolkitInitialized();
  });

  it("evaluates every Join Lab preset cleanly through real browser WASM", () => {
    for (const preset of PUNARCHI_JOIN_PRESETS) {
      const res = tt.punarchi_join(preset.first, preset.second, {
        context: preset.context,
        profile: "nannool-v1",
      });
      expect(res.profile, `preset=${preset.id}`).toBe("nannool-v1");
      expect(res.surface.length, `preset=${preset.id}`).toBeGreaterThan(0);
      expect(res.steps.length, `preset=${preset.id}`).toBeGreaterThan(0);
    }

    // Spot-check key linguistic invariants
    const maram = tt.punarchi_join("மரம்", "ஐ", {
      context: { relation: "vetrumai", subtype: "case_2" },
    });
    expect(maram.surface).toBe("மரத்தை");
    expect(maram.steps.map((s) => s.sutra)).toContain(252);

    const naaduIn = tt.punarchi_join("நாடு", "இன்", {
      context: { relation: "vetrumai", subtype: "case_5" },
    });
    expect(naaduIn.surface).toBe("நாட்டின்");
    expect(naaduIn.alternatives.some((a) => a.surface.includes("இனின்"))).toBe(false);

    const zwnjChar = String.fromCodePoint(0x200c);
    const zwnj = tt.punarchi_join("கல்", `${zwnjChar}தீது`);
    expect(zwnj.surface).toBe(`கல்${zwnjChar}தீது`);
    expect(zwnj.steps[0].sutra).toBe(153);

    expect(tt.punarchi_join("பத்து", "ஒன்பது").surface).toBe("பத்தொன்பது");
    expect(tt.punarchi_join("மரம்", "அடி").surface).toBe("மரத்தடி");
    expect(tt.punarchi_join("செம்மை", "மலர்").surface).toBe("செம்மலர்");
    expect(tt.punarchi_join("பூ", "கொடி").surface).toBe("பூங்கொடி");
    expect(tt.punarchi_join("கிழக்கு", "கடல்").surface).toBe("கீழ்க்கடல்");
    expect(tt.punarchi_join("ஏழு", "ஆயிரம்").surface).toBe("ஏழாயிரம்");
    expect(
      tt.punarchi_split_candidates("ஆற்றுநீர்").some((c) => c.first === "ஆறு" && c.second === "நீர்")
    ).toBe(true);
    expect(
      tt.punarchi_split_candidates("மரத்தடி").some((c) => c.first === "மரம்" && c.second === "அடி")
    ).toBe(true);
  });

  it("evaluates every Split Lab preset and round-trips through punarchi_join", () => {
    for (const preset of PUNARCHI_SPLIT_PRESETS) {
      const cands = tt.punarchi_split_candidates(preset.surface, {
        profile: "nannool-v1",
        poetic: Boolean(preset.poetic),
      });
      expect(cands.length, `surface=${preset.surface}`).toBeGreaterThan(0);
      for (const c of cands) {
        expect(c.first.length).toBeGreaterThan(0);
        expect(c.second.length).toBeGreaterThan(0);
        expect(c.steps.length).toBeGreaterThan(0);
      }
    }

    // Atomic ligature boundary safety
    const sri = tt.punarchi_split_candidates("ஸ்ரீராமன்", {
      profile: "nannool-v1",
      poetic: false,
    });
    for (const c of sri) {
      expect(c.first).not.toBe("ஸ்");
      expect(c.first).not.toBe("ஸ்ரீ்");
    }
  });

  it("exposes all 117 Nannool sutras and aligns with generated punarchi-review-data.json", () => {
    const all = tt.punarchi_rules({ profile: "nannool-v1" });
    expect(all).toHaveLength(117);
    expect(all.filter((e) => e.executable)).toHaveLength(106);
    expect(all.filter((e) => Boolean(e.edition_note))).toHaveLength(15);

    expect(punarchiReviewRaw.rule_count).toBe(punarchiReviewRaw.rules.length);
    expect(punarchiReviewRaw.rule_count).toBeGreaterThanOrEqual(143);
    expect(punarchiReviewRaw.closed_class_count).toBe(punarchiReviewRaw.closed_classes.length);
    expect(punarchiReviewRaw.closed_class_count).toBeGreaterThanOrEqual(35);
    expect(punarchiReviewRaw.golden_count).toBe(268);

    expect(punarchiReviewRaw.wikisource_page_base).toContain("https://ta.wikisource.org/wiki/");
    const sutraNotes = punarchiReviewRaw.sutra_notes as Record<
      string,
      { summary_ta: string; wikisource_pages: number[]; tolkappiyam_sutras: number[] }
    >;
    expect(Object.keys(sutraNotes)).toHaveLength(117);
    let wikisourceCovered = 0;
    for (const entry of all) {
      const note = sutraNotes[String(entry.sutra)];
      expect(note, `missing sutra_notes for ${entry.sutra}`).toBeDefined();
      expect(note.summary_ta.trim().length, `empty summary_ta for ${entry.sutra}`).toBeGreaterThan(5);
      if (note.wikisource_pages.length > 0) wikisourceCovered += 1;
    }
    expect(wikisourceCovered).toBeGreaterThanOrEqual(80);

    const validRuleIds = new Set(punarchiReviewRaw.rules.map((r) => r.id));
    for (const preset of PUNARCHI_JOIN_PRESETS) {
      const res = tt.punarchi_join(preset.first, preset.second, {
        context: preset.context,
        profile: "nannool-v1",
      });
      for (const step of res.steps) {
        expect(validRuleIds.has(step.rule_id), `missing rule_id ${step.rule_id}`).toBe(true);
      }
    }
  });

  it("rejects incompatible relation+subtype pairs with exact contract error", () => {
    expect(() =>
      tt.punarchi_join("கல்", "அடி", {
        context: { relation: "alvazhi", subtype: "case_2" },
        profile: "nannool-v1",
      })
    ).toThrow("unsupported or incompatible punarchi subtype");
  });
});
