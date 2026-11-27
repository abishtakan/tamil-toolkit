import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { afterAll, afterEach, beforeAll, beforeEach, describe, expect, it } from "vitest";
import { ensureToolkitInitialized } from "./setup";
import {
  defineLexiconV2,
  fuzzySearchLexiconV2,
  getLexiconLongestPrefixes,
  getLexiconRelations,
  getLexiconStats,
  loadLexiconPackBytes,
  queryLexiconV2,
  searchLexiconV2,
  unloadLexiconPack,
} from "../lib/engine";
import {
  LEXICON_CATEGORIES,
  LexiconV2PackManager,
  ProgressiveMountProgress,
  TLPACK_CACHE_NAME,
  TlpackManifest,
  buildTlpackCacheKey,
  buildV2QueryOptions,
  buildV2SearchOptions,
  fetchTlpackBytes,
  fetchTlpackManifest,
  filterTlpackManifest,
  packCategory,
  resolveTlpackUrl,
} from "../lib/lexicon-v2";
import { LanguageProvider } from "../lib/i18n";
import {
  LexiconExplorer,
  MergedWordDefinitionCard,
} from "../components/public-tools/LexiconExplorer";

const DIST_PACKS_DIR = resolve(process.cwd(), "../dist/lexicon-packs");

function readPackBytes(relPath: string): Uint8Array {
  return new Uint8Array(readFileSync(resolve(DIST_PACKS_DIR, relPath)));
}

describe("Pack Engine v2 (.tlpack FST runtime & client pack manager)", () => {
  let rawManifest: TlpackManifest;

  beforeAll(async () => {
    await ensureToolkitInitialized();
    rawManifest = JSON.parse(
      readFileSync(resolve(DIST_PACKS_DIR, "MANIFEST.json"), "utf-8")
    ) as TlpackManifest;
  });

  beforeEach(() => {
    unloadLexiconPack(null);
  });

  afterEach(() => {
    delete (globalThis as Record<string, unknown>).caches;
  });

  afterAll(() => {
    unloadLexiconPack(null);
  });

  describe("Real WASM .tlpack v2 loading, lookup, folded search, prefix autocomplete & relations", () => {
    it("mounts core, local_relations, and local_dialect packs and reports accurate stats", () => {
      const sCore = loadLexiconPackBytes(readPackBytes("open/core.tlpack"));
      const sRel = loadLexiconPackBytes(readPackBytes("local/local_relations.tlpack"));
      const sDialect = loadLexiconPackBytes(readPackBytes("local/local_dialect.tlpack"));

      expect(sCore.pack_id).toBe("core");
      expect(sCore.pack_tier).toBe("verified_open");
      expect(sCore.category).toBe("dictionary");
      expect(sCore.has_folded_index).toBe(true);

      const relManifest = rawManifest.packs.find(
        (p) => p.summary.pack_id === "local_relations"
      )!.summary;
      expect(sRel.pack_id).toBe("local_relations");
      expect(sRel.pack_tier).toBe("local_historical");
      expect(sRel.category).toBe("relations");
      expect(sRel.has_relations).toBe(true);
      expect(sRel.relation_count).toBeGreaterThan(0);
      expect(sRel.relation_count).toBe(relManifest.relation_count);

      expect(sDialect.pack_id).toBe("local_dialect");
      expect(sDialect.pack_tier).toBe("local_historical");
      expect(sDialect.category).toBe("regional");
      expect(sDialect.regions).toContain("KONGU");

      const stats = getLexiconStats();
      expect(stats.pack_count).toBe(3);
      expect(stats.total_relations).toBe(sRel.relation_count);
      expect(stats.total_entries).toBe(
        sCore.entry_count + sRel.entry_count + sDialect.entry_count
      );
      expect(stats.packs.map((p) => p.pack_id).sort()).toEqual([
        "core",
        "local_dialect",
        "local_relations",
      ]);

      const unloaded = unloadLexiconPack("local_dialect");
      expect(unloaded).toEqual({ pack_id: "local_dialect", removed: true });
      expect(getLexiconStats().pack_count).toBe(2);
    });

    it("performs exact lookup and Mayangoli folded search (தமில் -> தமிழ்)", () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));

      const exact = queryLexiconV2("தமிழ்", { tier: "open" });
      expect(exact.status).toBe("matched");
      expect(exact.folded).toBe(false);
      expect(exact.entries.length).toBeGreaterThanOrEqual(1);
      expect(exact.entries[0].pack_id).toBe("core");
      expect(exact.entries[0].pack_tier).toBe("verified_open");

      const strictMisspelled = queryLexiconV2("தமில்", { tier: "open", folded: false });
      expect(strictMisspelled.status).toBe("not_found");

      const folded = queryLexiconV2("தமில்", { tier: "open", folded: true });
      expect(folded.status).toBe("matched");
      expect(folded.folded).toBe(true);
      expect(folded.entries.some((e) => e.entry.headword === "தமிழ்")).toBe(true);
      expect(folded.entries.every((e) => e.pack_tier === "verified_open")).toBe(true);
    });

    it("supports FST prefix autocomplete across open and local packs with scope & category filters", () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_dialect.tlpack"));

      const prefixOpen = searchLexiconV2("தமிழ்", { tier: "open", limit: 10 });
      expect(prefixOpen.hits.length).toBeGreaterThanOrEqual(1);
      expect(prefixOpen.hits[0].headword).toBe("தமிழ்");
      expect(prefixOpen.hits.every((h) => h.pack_tiers.includes("verified_open"))).toBe(
        true
      );

      const foldedPrefix = searchLexiconV2("தமில்", {
        tier: "open",
        folded: true,
        limit: 10,
      });
      expect(foldedPrefix.folded).toBe(true);
      expect(foldedPrefix.hits.some((h) => h.headword === "தமிழ்")).toBe(true);

      const konguPrefix = searchLexiconV2("அ", {
        tier: "local",
        category: "regional",
        region: "KONGU",
        limit: 5,
      });
      expect(konguPrefix.hits.length).toBeGreaterThanOrEqual(1);
      expect(
        konguPrefix.hits.every((h) => h.pack_tiers.includes("local_historical"))
      ).toBe(true);
      expect(konguPrefix.hits.some((h) => h.headword === "அக்கட்ட")).toBe(true);

      const dictOnlyKongu = searchLexiconV2("அக்கட்ட", {
        category: "dictionary",
        limit: 5,
      });
      expect(dictOnlyKongu.hits.some((h) => h.headword === "அக்கட்ட")).toBe(false);

      // Empty prefix browsing works for "All" view filtered by category
      const allRegionalBrowse = searchLexiconV2("", {
        category: "regional",
        limit: 10,
      });
      expect(allRegionalBrowse.hits.length).toBe(10);
      expect(
        allRegionalBrowse.hits.every((h) => h.packs.includes("local_dialect"))
      ).toBe(true);
    });

    it("isolates open vs local tiers strictly across queries, searches, and relations", () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_dialect.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_relations.tlpack"));

      // Local dialect headword must not appear when tier is "open"
      const openOnly = queryLexiconV2("அக்கட்ட", { tier: "open" });
      expect(openOnly.status).toBe("not_found");
      expect(openOnly.searched_packs).toEqual(["core"]);

      const localOnly = queryLexiconV2("அக்கட்ட", { tier: "local" });
      expect(localOnly.status).toBe("matched");
      expect(localOnly.entries[0].pack_id).toBe("local_dialect");
      expect(localOnly.entries[0].pack_tier).toBe("local_historical");
      expect(localOnly.searched_packs).toEqual(["local_dialect", "local_relations"]);

      // Semantic relations for அன்பு live in local_relations
      const relsAll = getLexiconRelations("அன்பு");
      expect(relsAll.status).toBe("matched");
      expect(relsAll.relations.length).toBeGreaterThanOrEqual(4);
      expect(relsAll.relations.every((r) => r.relation_code === "SYNONYM")).toBe(true);
      expect(relsAll.relations.map((r) => r.target_headword)).toContain("காதல்");

      const relsOpen = getLexiconRelations("அன்பு", { tier: "open" });
      expect(relsOpen.status).toBe("not_found");
      expect(relsOpen.relations).toEqual([]);
    });

    it("returns unified merged WordDefinition via defineLexiconV2 with category filtering and provenance", async () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_dialect.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_relations.tlpack"));

      const def = await defineLexiconV2("அன்பு");
      expect(def.status).toBe("matched");
      expect(def.headword).toBe("அன்பு");
      expect(def.has_verified_open).toBe(true);
      expect(def.meanings_en.length).toBeGreaterThan(0);
      expect(def.relations.synonyms).toContain("காதல்");
      expect(def.sources.some((s) => s.pack_id === "core")).toBe(true);

      const dialectDef = await defineLexiconV2("அக்கட்ட", { category: "regional" });
      expect(dialectDef.status).toBe("matched");
      expect(dialectDef.categories).toContain("regional");
      expect(dialectDef.has_local_historical).toBe(true);
      expect(dialectDef.has_verified_open).toBe(false);

      const filteredOut = await defineLexiconV2("அக்கட்ட", { category: "terminology" });
      expect(filteredOut.status).toBe("not_found");
      expect(filteredOut.entry_count).toBe(0);
    });

    it("supports fuzzySearchLexiconV2, getLexiconLongestPrefixes, '#' browse, and after_key cursor pagination", () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));

      const fuzzy = fuzzySearchLexiconV2("தமில்", { max_distance: 1, tier: "open", limit: 6 });
      expect(fuzzy.hits.some((h) => h.headword === "தமிழ்" && h.distance === 1)).toBe(true);

      const longest = getLexiconLongestPrefixes("தமிழ்நாடு", { tier: "open" });
      expect(longest.prefixes).toContain("தமிழ்");

      const hashBrowse = searchLexiconV2("#", { tier: "open", limit: 5 });
      expect(hashBrowse.hits.length).toBeGreaterThan(0);

      const page1 = searchLexiconV2("", { tier: "open", limit: 3 });
      expect(page1.hits).toHaveLength(3);
      expect(page1.has_more).toBe(true);
      expect(page1.next_cursor).toBeTruthy();

      const page2 = searchLexiconV2("", {
        tier: "open",
        limit: 3,
        after_key: page1.next_cursor,
      });
      expect(page2.hits).toHaveLength(3);
      expect(page2.hits[0].headword).not.toBe(page1.hits[0].headword);
    });
  });

  describe("Client pack manager, progressive auto-load, Cache API & IS_PUBLIC_BETA boundary", () => {
    it("strips local/ packs from MANIFEST.json in public beta mode and blocks local/ fetches", async () => {
      const publicManifest = filterTlpackManifest(rawManifest, true);
      expect(publicManifest.pack_count).toBe(4);
      expect(publicManifest.packs.every((p) => !p.file.startsWith("local/"))).toBe(true);
      expect(
        publicManifest.packs.every((p) => p.summary.pack_tier === "verified_open")
      ).toBe(true);

      const fullManifest = filterTlpackManifest(rawManifest, false);
      expect(fullManifest.pack_count).toBe(12);
      expect(fullManifest.packs.some((p) => p.file.startsWith("local/"))).toBe(true);

      expect(() =>
        resolveTlpackUrl("local/local_relations.tlpack", "/lexicon-packs", true)
      ).toThrow(/public beta/i);
      expect(
        resolveTlpackUrl("open/core.tlpack", "/lexicon-packs", true)
      ).toBe("/lexicon-packs/open/core.tlpack");

      const mockFetch = (async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/MANIFEST.json")) {
          return new Response(JSON.stringify(rawManifest), { status: 200 });
        }
        throw new Error(`Unexpected fetch: ${url}`);
      }) as typeof fetch;

      const fetchedPublic = await fetchTlpackManifest({
        fetchImpl: mockFetch,
        isPublicBeta: true,
      });
      expect(fetchedPublic?.pack_count).toBe(4);
      expect(fetchedPublic?.packs.some((p) => p.file.startsWith("local/"))).toBe(false);
    });

    it("caches mounted packs, prevents duplicate fetches, and allows user local file mounting even in public beta", async () => {
      const manager = new LexiconV2PackManager();
      const coreEntry = rawManifest.packs.find((p) => p.summary.pack_id === "core")!;
      const relEntry = rawManifest.packs.find(
        (p) => p.summary.pack_id === "local_relations"
      )!;
      const coreBytes = readPackBytes("open/core.tlpack");
      const relBytes = readPackBytes("local/local_relations.tlpack");

      let fetchCount = 0;
      const mockFetch = (async (input: RequestInfo | URL) => {
        fetchCount++;
        const url = String(input);
        if (url.endsWith("/open/core.tlpack")) {
          return new Response(coreBytes.slice().buffer, { status: 200 });
        }
        return new Response("Not found", { status: 404 });
      }) as typeof fetch;

      // Lazy fetch & mount open pack once; second call reuses mounted cache
      const mounted1 = await manager.fetchAndMountPack(coreEntry, {
        fetchImpl: mockFetch,
        isPublicBeta: true,
      });
      const mounted2 = await manager.fetchAndMountPack(coreEntry, {
        fetchImpl: mockFetch,
        isPublicBeta: true,
      });
      expect(fetchCount).toBe(1);
      expect(mounted1.pack_id).toBe("core");
      expect(mounted2.pack_id).toBe("core");
      expect(manager.isMounted("core")).toBe(true);

      // Refuses auto-fetch of local/ pack in public beta mode
      await expect(
        manager.fetchAndMountPack(relEntry, {
          fetchImpl: mockFetch,
          isPublicBeta: true,
        })
      ).rejects.toThrow(/public beta/i);
      const localBatch = await manager.fetchAndMountTier(
        rawManifest,
        "local_historical",
        { fetchImpl: mockFetch, isPublicBeta: true }
      );
      expect(localBatch).toEqual([]);
      expect(fetchCount).toBe(1);

      // Client-side user file mounting works even when isPublicBeta is true (zero upload)
      const localFile = new File([relBytes.slice().buffer], "local_relations.tlpack");
      const userMounted = await manager.mountLocalFile(localFile);
      expect(userMounted.pack_id).toBe("local_relations");
      expect(manager.isUserLoaded("local_relations")).toBe(true);
      expect(getLexiconRelations("அன்பு").relations.length).toBeGreaterThanOrEqual(4);
    });

    it("supports Cache API hits by sha256 key, busts stale entries, and falls back when caches is undefined", async () => {
      const store = new Map<string, Response>();
      let openName = "";
      (globalThis as Record<string, unknown>).caches = {
        open: async (name: string) => {
          openName = name;
          return {
            match: async (key: RequestInfo | URL) => {
              const hit = store.get(String(key));
              return hit ? hit.clone() : undefined;
            },
            put: async (key: RequestInfo | URL, res: Response) => {
              store.set(String(key), res.clone());
            },
          };
        },
      };

      const coreBytes = readPackBytes("open/core.tlpack");
      let networkHits = 0;
      const mockFetch = (async () => {
        networkHits++;
        return new Response(coreBytes.slice().buffer, { status: 200 });
      }) as typeof fetch;

      const url = "/lexicon-packs/open/core.tlpack";
      const sha1 = "1111111111111111";
      const sha2 = "2222222222222222";

      expect(buildTlpackCacheKey(url, sha1)).toBe(`${url}?sha256=${sha1}`);

      const first = await fetchTlpackBytes(url, {
        checksumSha256: sha1,
        fetchImpl: mockFetch,
      });
      expect(openName).toBe(TLPACK_CACHE_NAME);
      expect(networkHits).toBe(1);
      expect(first.byteLength).toBe(coreBytes.byteLength);

      // Second fetch with same sha256 hits Cache API without network fetch
      const second = await fetchTlpackBytes(url, {
        checksumSha256: sha1,
        fetchImpl: mockFetch,
      });
      expect(networkHits).toBe(1);
      expect(second.byteLength).toBe(coreBytes.byteLength);

      // Updated sha256 busts cache and fetches again
      const third = await fetchTlpackBytes(url, {
        checksumSha256: sha2,
        fetchImpl: mockFetch,
      });
      expect(networkHits).toBe(2);
      expect(third.byteLength).toBe(coreBytes.byteLength);

      // Undefined caches falls back cleanly to fetch()
      delete (globalThis as Record<string, unknown>).caches;
      const fourth = await fetchTlpackBytes(url, {
        checksumSha256: sha2,
        fetchImpl: mockFetch,
      });
      expect(networkHits).toBe(3);
      expect(fourth.byteLength).toBe(coreBytes.byteLength);
    });

    it("prunes stale ?sha256= entries for the same URL from Cache API while preserving other URLs", async () => {
      const store = new Map<string, Response>();
      (globalThis as Record<string, unknown>).caches = {
        open: async () => ({
          match: async (key: RequestInfo | URL) => {
            const hit = store.get(String(key));
            return hit ? hit.clone() : undefined;
          },
          put: async (key: RequestInfo | URL, res: Response) => {
            store.set(String(key), res.clone());
          },
          keys: async () => Array.from(store.keys()).map((k) => new Request(`http://localhost${k}`)),
          delete: async (req: RequestInfo | URL) => {
            const raw = typeof req === "string" ? req : (req as Request).url;
            const pathAndQuery = raw.replace(/^http:\/\/localhost/, "");
            return store.delete(pathAndQuery);
          },
        }),
      };

      const coreBytes = readPackBytes("open/core.tlpack");
      const regBytes = readPackBytes("open/regional.tlpack");
      const mockFetch = (async (input: RequestInfo | URL) => {
        const u = String(input);
        const bytes = u.includes("regional") ? regBytes : coreBytes;
        return new Response(bytes.slice().buffer, { status: 200 });
      }) as typeof fetch;

      const coreUrl = "/lexicon-packs/open/core.tlpack";
      const regUrl = "/lexicon-packs/open/regional.tlpack";
      store.set(coreUrl, new Response(coreBytes.slice().buffer, { status: 200 }));

      await fetchTlpackBytes(coreUrl, { checksumSha256: "oldsha1", fetchImpl: mockFetch });
      await fetchTlpackBytes(regUrl, { checksumSha256: "regsha1", fetchImpl: mockFetch });
      await fetchTlpackBytes(coreUrl, { checksumSha256: "newsha2", fetchImpl: mockFetch });

      expect(store.has(`${coreUrl}?sha256=newsha2`)).toBe(true);
      expect(store.has(`${coreUrl}?sha256=oldsha1`)).toBe(false);
      expect(store.has(coreUrl)).toBe(false);
      expect(store.has(`${regUrl}?sha256=regsha1`)).toBe(true);
    });

    it("unloads only local_historical packs in unloadLocalPacks() while keeping verified_open packs mounted", () => {
      const manager = new LexiconV2PackManager();
      manager.mountBytes(readPackBytes("open/core.tlpack"), "remote");
      manager.mountBytes(readPackBytes("open/regional.tlpack"), "remote");
      manager.mountBytes(readPackBytes("local/local_dialect.tlpack"), "remote");
      manager.mountBytes(readPackBytes("local/local_relations.tlpack"), "remote");

      const unloaded = manager.unloadLocalPacks();
      expect(unloaded.sort()).toEqual(["local_dialect", "local_relations"]);

      const remaining = getLexiconStats().packs.map((p) => p.pack_id).sort();
      expect(remaining).toEqual(["core", "regional"]);
      expect(manager.getMountedPackIds().sort()).toEqual(["core", "regional"]);
    });

    it("progressively mounts open-lite -> open -> full with small packs first, local_terminology last, and deduplicates concurrent runs", async () => {
      const manager = new LexiconV2PackManager();
      const coreBytes = readPackBytes("open/core.tlpack");
      const namesBytes = readPackBytes("open/names_taxa.tlpack");
      const regBytes = readPackBytes("open/regional.tlpack");
      const relBytes = readPackBytes("local/local_relations.tlpack");
      const dialectBytes = readPackBytes("local/local_dialect.tlpack");

      // Build a lightweight manifest subset with real pack bytes mapped by file path
      const subsetFiles = new Set([
        "open/core.tlpack",
        "open/names_taxa.tlpack",
        "open/regional.tlpack",
        "open/ta_wiktionary.tlpack",
        "local/local_dialect.tlpack",
        "local/local_relations.tlpack",
        "local/local_terminology.tlpack",
      ]);
      const testManifest: TlpackManifest = {
        pack_count: subsetFiles.size,
        packs: rawManifest.packs.filter((p) => subsetFiles.has(p.file)),
      };

      const fetchOrder: string[] = [];
      const mockFetch = (async (input: RequestInfo | URL) => {
        const url = String(input);
        fetchOrder.push(url.replace("/lexicon-packs/", ""));
        // Use small real packs as valid TMLPACK2 payloads where giant packs aren't needed for ordering check
        const map: Record<string, Uint8Array> = {
          "/lexicon-packs/open/core.tlpack": coreBytes,
          "/lexicon-packs/open/names_taxa.tlpack": namesBytes,
          "/lexicon-packs/open/regional.tlpack": regBytes,
          "/lexicon-packs/open/ta_wiktionary.tlpack": coreBytes,
          "/lexicon-packs/local/local_dialect.tlpack": dialectBytes,
          "/lexicon-packs/local/local_relations.tlpack": relBytes,
          "/lexicon-packs/local/local_terminology.tlpack": dialectBytes,
        };
        const payload = map[url];
        if (!payload) {
          return new Response("Not found", { status: 404 });
        }
        return new Response(payload.slice().buffer, { status: 200 });
      }) as typeof fetch;

      // 1. Public beta mode: stops after open (Stage 2) and never touches local/
      const betaProgress: ProgressiveMountProgress[] = [];
      await manager.autoMountProgressive({
        manifest: testManifest,
        includeLocal: true, // must be ignored when isPublicBeta === true
        isPublicBeta: true,
        fetchImpl: mockFetch,
        onProgress: (p) => betaProgress.push(p),
      });

      expect(fetchOrder).toEqual([
        "open/core.tlpack",
        "open/names_taxa.tlpack",
        "open/regional.tlpack",
        "open/ta_wiktionary.tlpack",
      ]);
      expect(betaProgress.map((p) => p.stage)).toEqual([
        "open-lite",
        "open-lite",
        "open-lite",
        "open",
      ]);
      expect(betaProgress[betaProgress.length - 1].done).toBe(true);
      expect(fetchOrder.some((f) => f.startsWith("local/"))).toBe(false);

      // 2. Non-beta full mode with concurrent StrictMode double-invoke deduplication
      unloadLexiconPack(null);
      manager.resetCache();
      fetchOrder.length = 0;

      const fullProgress1: ProgressiveMountProgress[] = [];
      const fullProgress2: ProgressiveMountProgress[] = [];
      await Promise.all([
        manager.autoMountProgressive({
          manifest: testManifest,
          includeLocal: true,
          isPublicBeta: false,
          fetchImpl: mockFetch,
          onProgress: (p) => fullProgress1.push(p),
        }),
        manager.autoMountProgressive({
          manifest: testManifest,
          includeLocal: true,
          isPublicBeta: false,
          fetchImpl: mockFetch,
          onProgress: (p) => fullProgress2.push(p),
        }),
      ]);

      // Exactly 1 fetch per pack even with 2 concurrent calls
      expect(fetchOrder).toEqual([
        "open/core.tlpack",
        "open/names_taxa.tlpack",
        "open/regional.tlpack",
        "open/ta_wiktionary.tlpack",
        "local/local_dialect.tlpack",
        "local/local_relations.tlpack",
        "local/local_terminology.tlpack",
      ]);
      expect(fetchOrder[fetchOrder.length - 1]).toBe("local/local_terminology.tlpack");
      expect(fullProgress1.length).toBe(7);
      expect(fullProgress2.length).toBe(7);
      expect(fullProgress1[fullProgress1.length - 1].done).toBe(true);
    });

    it("omits empty strings and 'ALL' sentinel values and preserves category in buildV2QueryOptions / buildV2SearchOptions", () => {
      expect(
        buildV2QueryOptions({
          tier: "all",
          category: "all",
          pos: "ALL",
          domain: "",
          region: "",
          register: "",
          folded: true,
        })
      ).toEqual({ folded: true });

      expect(
        buildV2SearchOptions({
          tier: "open",
          category: "regional",
          pos: "NOUN",
          domain: "grammar",
          region: "JAFFNA",
          folded: false,
          limit: 20,
          after_key: "அகரம்",
        })
      ).toEqual({
        tier: "open",
        category: "regional",
        pos: "NOUN",
        domain: "grammar",
        region: "JAFFNA",
        folded: false,
        limit: 20,
        after_key: "அகரம்",
      });

      expect(LEXICON_CATEGORIES).toHaveLength(6);
      expect(LEXICON_CATEGORIES.map((c) => c.id)).toEqual([
        "dictionary",
        "terminology",
        "phrases",
        "regional",
        "names_taxa",
        "heritage",
      ]);
      expect(packCategory("local_literary")).toBe("heritage");
      expect(packCategory("local_relations")).toBe("relations");
    });
  });

  describe("LexiconExplorer & MergedWordDefinitionCard UI rendering", () => {
    it("renders a single unified merged word card with meanings, clickable relation chips, and honest provenance", async () => {
      loadLexiconPackBytes(readPackBytes("open/core.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_core.tlpack"));
      loadLexiconPackBytes(readPackBytes("local/local_relations.tlpack"));

      const def = await defineLexiconV2("அன்பு");
      const html = renderToStaticMarkup(
        React.createElement(MergedWordDefinitionCard, {
          definition: def,
          latencyMs: 1.25,
          language: "en",
          onSelectWord: () => {},
        })
      );

      expect(html).toContain('data-testid="merged-word-card"');
      expect(html).not.toContain('data-testid="legacy-word-card"');
      expect(html).toContain("அன்பு");
      expect(html).toContain("English Meanings");
      expect(html).toContain("Word Relations");
      expect(html).toContain("Synonyms");
      expect(html).toContain("காதல்");
      expect(html).toContain("Open + Local");
      expect(html).toContain("Provenance &amp; Sources");
    });

    it("renders IPA, morphology/etymology chips, and Mayangoli homophone switcher pills when folded", () => {
      const richHtml = renderToStaticMarkup(
        React.createElement(MergedWordDefinitionCard, {
          definition: {
            status: "matched",
            query: "அரை",
            canonical_query: "அரை",
            headword: "அரை",
            folded: true,
            searched_packs: ["core"],
            categories: ["dictionary"],
            pos: ["NOUN"],
            meanings_en: [
              {
                text: "half; waist",
                language: "en",
                pack_id: "core",
                category: "dictionary",
                pack_tier: "verified_open",
                rights_status: "CC-BY-SA-4.0",
              },
            ],
            meanings_ta: [],
            examples: [],
            variants: [],
            domains: [],
            regions: [],
            registers: [],
            standard_equivalents: [],
            pure_tamil_equivalents: [],
            origin_languages: [],
            scientific_names: [],
            literary_sources: [],
            matched_headwords: ["அரை", "அறை"],
            ipa: ["ɐɾɐɪ̯"],
            verb_classes: ["Class IV"],
            transitivity: ["transitive"],
            root_words: ["அர்"],
            etymology_types: ["Dravidian"],
            dedr_ids: ["DEDR 229"],
            sandhi_behaviors: ["doubles"],
            animacy_genders: ["neuter"],
            frequency_tiers: ["core-1k"],
            relations: { synonyms: [], antonyms: [], related: [], hypernyms: [] },
            has_verified_open: true,
            has_local_historical: false,
            entry_count: 1,
            sources: [],
          },
          latencyMs: 0.5,
          language: "en",
          onSelectWord: () => {},
        })
      );

      expect(richHtml).toContain("/ɐɾɐɪ̯/");
      expect(richHtml).toContain("Also matched:");
      expect(richHtml).toContain("அறை");
      expect(richHtml).toContain("Verb Class");
      expect(richHtml).toContain("Class IV");
      expect(richHtml).toContain("Transitivity");
      expect(richHtml).toContain("Root Word");
      expect(richHtml).toContain("Etymology");
      expect(richHtml).toContain("DEDR 229");
      expect(richHtml).toContain("Sandhi");
      expect(richHtml).toContain("Animacy / Gender");
      expect(richHtml).toContain("Frequency Tier");
    });

    it("renders LexiconExplorer with 6 category pills, Mayangoli Folded toggle, Dataset Switch, and Manage Packs & Developer Tools drawer without duplicate word cards", () => {
      // Test Tamil default (SSR / window undefined)
      const taHtml = renderToStaticMarkup(
        React.createElement(
          LanguageProvider,
          null,
          React.createElement(LexiconExplorer, { engineReady: true })
        )
      );
      expect(taHtml).toContain("மயங்கொலி மடிப்பு");
      for (const cat of LEXICON_CATEGORIES) {
        expect(taHtml).toContain(cat.label_ta.replaceAll("&", "&amp;"));
      }
      expect(taHtml).toContain("Manage Packs &amp; Developer Tools");

      // Test English mode (?lang=en)
      const prevWindow = (globalThis as Record<string, unknown>).window;
      (globalThis as Record<string, unknown>).window = {
        location: { search: "?lang=en", href: "https://localhost/?lang=en" },
      };
      try {
        const enHtml = renderToStaticMarkup(
          React.createElement(
            LanguageProvider,
            null,
            React.createElement(LexiconExplorer, { engineReady: true })
          )
        );

        expect(enHtml).toContain("Mayangoli Folded");
        for (const cat of LEXICON_CATEGORIES) {
          expect(enHtml).toContain(cat.label_en.replaceAll("&", "&amp;"));
        }
        expect(enHtml).toContain("Verified Open (90k)");
        expect(enHtml).toContain("Manage Packs &amp; Developer Tools");

        // Never renders both legacy and v2 cards stacked together
        const mergedCount = (enHtml.match(/data-testid="merged-word-card"/g) ?? []).length;
        const legacyCount = (enHtml.match(/data-testid="legacy-word-card"/g) ?? []).length;
        expect(mergedCount + legacyCount).toBeLessThanOrEqual(1);
      } finally {
        if (prevWindow === undefined) {
          delete (globalThis as Record<string, unknown>).window;
        } else {
          (globalThis as Record<string, unknown>).window = prevWindow;
        }
      }
    });
  });
});
