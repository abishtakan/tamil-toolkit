import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import * as tt from "tamil-toolkit/web";
import { ensureToolkitInitialized } from "./setup";
import {
  getLexiconPacks,
  hasEmbeddedLexiconPacks,
  lookupLexicon,
  searchLexiconEnglishV2,
  transliterateSuggest,
} from "../lib/engine";
import {
  IS_OPEN_ONLY_CHANNEL,
  TlpackManifest,
  fetchTlpackManifest,
  filterTlpackManifest,
  formatCompactFacetCount,
  getDefaultLexiconBaseUrl,
  isAsciiLatinQuery,
  mergeEnglishAndTanglishHits,
  resolveIsOpenOnlyChannel,
  resolveTlpackUrl,
} from "../lib/lexicon-v2";
import { LanguageProvider } from "../lib/i18n";
import { LexiconExplorer } from "../components/public-tools/LexiconExplorer";
import { LexiconPackDrawer } from "../components/public-tools/lexicon/LexiconPackDrawer";

const DIST_MANIFEST_PATH = resolve(
  process.cwd(),
  "../dist/lexicon-packs/MANIFEST.json"
);

describe("Wave 2B: Full-Channel Activation, Unified Search, Facet Counts & Slim-WASM Readiness", () => {
  let rawManifest: TlpackManifest;

  beforeAll(async () => {
    await ensureToolkitInitialized();
    rawManifest = JSON.parse(
      readFileSync(DIST_MANIFEST_PATH, "utf-8")
    ) as TlpackManifest;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("Configurable full vs open pack channel & CDN baseUrl override", () => {
    it("defaults to full channel (IS_OPEN_ONLY_CHANNEL === false) and switches only on 'open'", () => {
      expect(IS_OPEN_ONLY_CHANNEL).toBe(false);
      expect(resolveIsOpenOnlyChannel(undefined)).toBe(false);
      expect(resolveIsOpenOnlyChannel("")).toBe(false);
      expect(resolveIsOpenOnlyChannel("full")).toBe(false);
      expect(resolveIsOpenOnlyChannel("FULL")).toBe(false);
      expect(resolveIsOpenOnlyChannel("open")).toBe(true);
      expect(resolveIsOpenOnlyChannel(" Open ")).toBe(true);
    });

    it("supports VITE_LEXICON_BASE_URL override for R2/CDN origins and defaults to /lexicon-packs", async () => {
      expect(getDefaultLexiconBaseUrl(undefined)).toBe("/lexicon-packs");
      expect(getDefaultLexiconBaseUrl("")).toBe("/lexicon-packs");
      expect(getDefaultLexiconBaseUrl("https://cdn.example.com/packs/")).toBe(
        "https://cdn.example.com/packs"
      );

      const cdnBase = getDefaultLexiconBaseUrl("https://r2.example.org/v2/");
      expect(resolveTlpackUrl("open/core.tlpack", cdnBase, false)).toBe(
        "https://r2.example.org/v2/open/core.tlpack"
      );
      expect(resolveTlpackUrl("local/local_core.tlpack", cdnBase, false)).toBe(
        "https://r2.example.org/v2/local/local_core.tlpack"
      );
      expect(() =>
        resolveTlpackUrl("local/local_core.tlpack", cdnBase, true)
      ).toThrow(/open-only/i);

      const requestedUrls: string[] = [];
      const mockFetch = (async (input: RequestInfo | URL) => {
        requestedUrls.push(String(input));
        return new Response(JSON.stringify(rawManifest), { status: 200 });
      }) as typeof fetch;

      const fullManifest = await fetchTlpackManifest({
        baseUrl: cdnBase,
        fetchImpl: mockFetch,
        isOpenOnly: false,
      });
      expect(requestedUrls[0]).toBe("https://r2.example.org/v2/MANIFEST.json");
      expect(fullManifest?.pack_count).toBe(12);

      const openManifest = await fetchTlpackManifest({
        baseUrl: cdnBase,
        fetchImpl: mockFetch,
        isOpenOnly: true,
      });
      expect(openManifest?.pack_count).toBe(4);
      expect(
        openManifest?.packs.every(
          (p) => p.summary.pack_tier === "verified_open"
        )
      ).toBe(true);
    });

    it("preserves exact pack_tier, rights_status, license, and source_ids in full channel manifest", () => {
      const full = filterTlpackManifest(rawManifest, false);
      expect(full.pack_count).toBe(12);
      const localTerm = full.packs.find(
        (p) => p.summary.pack_id === "local_terminology"
      );
      expect(localTerm?.summary.pack_tier).toBe("local_historical");
      expect(localTerm?.summary.rights_status).toBe("unresolved");
      expect(localTerm?.summary.license).toBe("UNRESOLVED_LOCAL_ONLY");
      expect(localTerm?.summary.source_ids).toEqual([
        "TVA_KALAICHOL",
        "sorkuvai_technical",
      ]);
    });
  });

  describe("Unified Tamil + Tanglish + English search & searchLexiconEnglishV2", () => {
    it("dispatches searchLexiconEnglishV2 via lexiconSearchEnglish and strips ALL/empty options", () => {
      const searchSpy = vi
        .spyOn(tt, "lexiconSearchEnglish")
        .mockReturnValue({
          prefix: "gratitude",
          canonical_prefix: "gratitude",
          folded: false,
          searched_packs: ["core"],
          hits: [
            {
              headword: "\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf",
              matched_key: "gratitude",
              packs: ["core"],
              pack_tiers: ["verified_open"],
              pos: ["NOUN"],
              preview_gloss: "gratitude; thankfulness",
              entry_count: 2,
            },
          ],
        } satisfies tt.LexiconPrefixSearchResult);

      const res = searchLexiconEnglishV2("gratitude", {
        tier: "all",
        category: "all",
        pos: "ALL",
        domain: "ALL",
        region: "",
        register: "",
        limit: 25,
      });

      expect(searchSpy).toHaveBeenCalledWith("gratitude", {
        limit: 25,
      });
      expect(res.hits).toHaveLength(1);
      expect(res.hits[0].headword).toBe("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf");
    });

    it("detects ASCII Latin queries and merges English gloss matches before deduplicated Tanglish hits", () => {
      expect(isAsciiLatinQuery("gratitude")).toBe(true);
      expect(isAsciiLatinQuery("nandri")).toBe(true);
      expect(isAsciiLatinQuery("water")).toBe(true);
      expect(isAsciiLatinQuery("நன்றி")).toBe(false);
      expect(isAsciiLatinQuery("tamiḻ")).toBe(false);
      expect(isAsciiLatinQuery("   ")).toBe(false);

      const englishHits: tt.LexiconPrefixSearchHit[] = [
        {
          headword: "அருவி",
          matched_key: "waterfall",
          packs: ["core"],
          pack_tiers: ["verified_open"],
          pos: ["NOUN"],
          preview_gloss: "waterfall; cascade",
          entry_count: 1,
        },
        {
          headword: "நீர்",
          matched_key: "water",
          packs: ["core"],
          pack_tiers: ["verified_open"],
          pos: ["NOUN"],
          preview_gloss: "water; liquid",
          entry_count: 2,
        },
      ];
      const tanglishHits: tt.LexiconPrefixSearchHit[] = [
        {
          headword: "நீர்",
          matched_key: "நீர்",
          packs: ["core"],
          pack_tiers: ["verified_open"],
          pos: ["NOUN"],
          preview_gloss: "water",
          entry_count: 2,
        },
        {
          headword: "வாடர்",
          matched_key: "வாடர்",
          packs: ["local_loans"],
          pack_tiers: ["local_historical"],
          pos: ["NOUN"],
          preview_gloss: "warder",
          entry_count: 1,
        },
      ];

      const merged = mergeEnglishAndTanglishHits("water", englishHits, tanglishHits);
      expect(merged.map((h) => h.headword)).toEqual(["நீர்", "அருவி", "வாடர்"]);
      expect(merged.map((h) => h.matchSource)).toEqual([
        "english",
        "english",
        "tanglish",
      ]);
    });

    it("generates real WASM Tanglish transliteration suggestions via transliterateSuggest", () => {
      const suggestions = transliterateSuggest("nandri", "phonetic-v1", 5);
      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions).toContain("நன்றி");
    });
  });

  describe("Slim-WASM readiness (zero dependency on embedded v1 dictionary bytes)", () => {
    it("returns empty packs and safe not_found responses when WASM has 0 embedded v1 packs", () => {
      vi.spyOn(tt, "lexicon_packs").mockReturnValue([]);
      const lookupSpy = vi.spyOn(tt, "lexicon_lookup");

      expect(getLexiconPacks()).toEqual([]);
      expect(hasEmbeddedLexiconPacks()).toBe(false);

      const defaultRes = lookupLexicon("நன்றி");
      expect(defaultRes).toEqual({
        schema_version: 1,
        status: "not_found",
        canonical_query: "நன்றி",
        packs: [],
        entries: [],
      });

      const coreRes = lookupLexicon("நன்றி", { packs: ["core"] });
      expect(coreRes.status).toBe("not_found");
      expect(coreRes.entries).toEqual([]);
      expect(lookupSpy).not.toHaveBeenCalled();

      // Explicit invalid contract requests still delegate to Rust contract validation
      expect(() => lookupLexicon("நன்றி", { packs: ["terminology"] })).toThrow(
        "lexicon: pack unavailable 'terminology'"
      );
    });

    it("returns [] safely when lexicon_packs throws", () => {
      vi.spyOn(tt, "lexicon_packs").mockImplementation(() => {
        throw new Error("not initialized");
      });
      expect(getLexiconPacks()).toEqual([]);
      expect(hasEmbeddedLexiconPacks()).toBe(false);
    });

    it("hides legacy v1 pack checkboxes in LexiconPackDrawer when availablePackSet is empty", () => {
      const html = renderToStaticMarkup(
        React.createElement(
          LanguageProvider,
          null,
          React.createElement(LexiconPackDrawer, {
            ready: true,
            v2Stats: {
              pack_count: 1,
              total_entries: 10343,
              total_senses: 23827,
              total_relations: 0,
              total_bytes: 3034952,
              packs: [],
            },
            v2MountedIds: new Set(["core"]),
            v2LoadingAction: null,
            v2Error: null,
            v2OpenManifestPacks: [],
            v2LocalManifestPacks: [],
            v2ExtraMountedPacks: [],
            groupedManifestPacks: [],
            allOpenMounted: false,
            allLocalMounted: false,
            onLoadV2Tier: () => {},
            onToggleV2ManifestPack: () => {},
            onLocalTlpackFiles: () => {},
            onUnloadAllV2: () => {},
            onUnloadSingleV2Pack: () => {},
            onOpenHistoricalMode: () => {},
            scopeOptions: {
              regions: [],
              regionEntries: [],
              attestedRegions: [],
              registers: [],
              unknownRegionEntries: 0,
            },
            selectedRegister: "",
            onChangeRegister: () => {},
            v2Domains: [],
            v2Domain: "ALL",
            onChangeV2Domain: () => {},
            queryDiagnostics: {
              utf8Bytes: 0,
              hasLeadingOrTrailingWhitespace: false,
              hasJoinersOrSoftHyphen: false,
              joinerLabels: [],
            },
            loadedTotals: { loadedPackIds: [] },
            catalogAlignment: {
              isFullCatalogVerified: false,
              hasStaleMismatch: false,
              byPack: {} as never,
              verifiedLoadedEntries: 0,
              verifiedLoadedSenses: 0,
              verifiedDistinctHeadwords: null,
              verifiedPackIds: [],
              stalePackIds: [],
              unavailablePackIds: [],
            },
            availablePackSet: new Set(),
            selectedPacks: [],
            onTogglePack: () => {},
            extendedManifest: null,
            onPresetClick: () => {},
            lastRawRequest: "",
            lastRawResponse: "",
          })
        )
      );

      expect(html).toContain("Manage Packs &amp; Developer Tools");
    });
  });

  describe("LexiconExplorer UI enhancements (placeholder, Domain dropdown, facet counts)", () => {
    it("renders unified Tamil/Tanglish/English placeholder, Domain dropdown, and Full Archive toggle", () => {
      const prevWindow = (globalThis as Record<string, unknown>).window;
      (globalThis as Record<string, unknown>).window = {
        location: { search: "?lang=en", href: "https://localhost/?lang=en" },
      };
      try {
        const html = renderToStaticMarkup(
          React.createElement(
            LanguageProvider,
            null,
            React.createElement(LexiconExplorer, { engineReady: true })
          )
        );
        expect(html).toContain("Look up Tamil, Tanglish, or English");
        expect(html).toContain('id="lexicon-domain-select"');
        expect(html).toContain("All domains");
        expect(html).toContain("Full Archive (241k)");
        expect(html).toContain("Verified Open (90k)");
      } finally {
        if (prevWindow === undefined) {
          delete (globalThis as Record<string, unknown>).window;
        } else {
          (globalThis as Record<string, unknown>).window = prevWindow;
        }
      }
    });

    it("formats category facet counts cleanly (e.g. 118k, 10.3k)", () => {
      expect(formatCompactFacetCount(118189)).toBe("118k");
      expect(formatCompactFacetCount(10321)).toBe("10.3k");
      expect(formatCompactFacetCount(1439)).toBe("1.4k");
      expect(formatCompactFacetCount(272)).toBe("272");
    });
  });
});
