import { describe, it, expect } from "vitest";
import { translations } from "../lib/i18n";
import {
  TOOLS,
  TOOL_GROUPS,
  filterToolsByQuery,
  isValidToolId,
  resolveLexiconViewMode,
  resolveToolFromSearch,
} from "../lib/tools";

describe("Playground Navigation & Tool Registry", () => {
  it("registers all 14 unique tools under valid navigation groups", () => {
    expect(TOOLS).toHaveLength(14);
    const ids = TOOLS.map((tool) => tool.id);
    expect(new Set(ids).size).toBe(14);

    const validGroups = new Set(TOOL_GROUPS.map((g) => g.id));
    for (const tool of TOOLS) {
      expect(validGroups.has(tool.group)).toBe(true);
      expect(isValidToolId(tool.id)).toBe(true);
    }
    expect(isValidToolId("unknown")).toBe(false);
    expect(isValidToolId(null)).toBe(false);
  });

  it("resolves ?tool= query parameters safely", () => {
    expect(resolveToolFromSearch("")).toBe("home");
    expect(resolveToolFromSearch("?lang=ta")).toBe("home");
    expect(resolveToolFromSearch("?tool=lexicon&mode=historical")).toBe("lexicon");
    expect(resolveToolFromSearch("?tool=calendar")).toBe("calendar");
    expect(resolveToolFromSearch("?tool=unknown")).toBe("home");
  });

  it("filters tools by English and Tamil titles and keywords", () => {
    expect(filterToolsByQuery("", translations.en)).toHaveLength(14);

    const baminiHits = filterToolsByQuery("bamini", translations.en);
    expect(baminiHits.some((t) => t.id === "codec")).toBe(true);

    const translitHits = filterToolsByQuery("tamil99", translations.en);
    expect(translitHits.some((t) => t.id === "translit")).toBe(true);

    const chequeHits = filterToolsByQuery("cheque", translations.en);
    expect(chequeHits.some((t) => t.id === "numeral")).toBe(true);

    const dictHitsTa = filterToolsByQuery("அகராதி", translations.ta);
    expect(dictHitsTa.some((t) => t.id === "lexicon")).toBe(true);

    const calHitsTa = filterToolsByQuery("நாட்காட்டி", translations.ta);
    expect(calHitsTa.some((t) => t.id === "calendar")).toBe(true);
  });

  it("gates unverified historical archive mode in public beta builds", () => {
    expect(resolveLexiconViewMode("?tool=lexicon&mode=historical", false)).toBe("historical");
    expect(resolveLexiconViewMode("?tool=lexicon&mode=historical", true)).toBe("verified");
    expect(resolveLexiconViewMode("?tool=lexicon", true)).toBe("verified");
  });
});
