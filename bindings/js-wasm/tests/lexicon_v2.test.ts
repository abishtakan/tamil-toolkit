import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, describe, expect, test } from "vitest";
import { createApi } from "../src/api.js";
import * as nodeApi from "../src/index.js";
import * as webApi from "../src/web.js";
import {
  DEFAULT_LEXICON_MANIFEST_URL,
  LexiconPackClient,
  filterManifestPacks,
  mountLexiconFromUrl,
  type LexiconPackManifest,
} from "../src/lexicon-loader.js";
import type { LexiconCompactPackSummary, LexiconStatsResult } from "../src/api.js";

function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function makeSummary(
  packId: string,
  tier: "verified_open" | "local_historical",
  category: LexiconCompactPackSummary["category"],
  bytes: Uint8Array,
): LexiconCompactPackSummary {
  return {
    pack_id: packId,
    category,
    index_format_version: 2,
    schema_version: 2,
    pack_tier: tier,
    rights_status: tier === "verified_open" ? "CC-BY-SA-4.0" : "unresolved",
    license: tier === "verified_open" ? "CC-BY-SA-4.0" : "UNRESOLVED_LOCAL_ONLY",
    dataset_version: "0.2.0",
    description: `Mock ${packId}`,
    entry_count: 1,
    sense_count: 1,
    relation_count: 0,
    distinct_headwords: 1,
    byte_len: bytes.byteLength,
    checksum_sha256: sha256(bytes),
    has_folded_index: true,
    has_relations: false,
    has_english_index: true,
    source_ids: ["mock"],
    attribution_notice: "mock",
    domains: [],
    regions: [],
    registers: [],
  };
}

function buildMockFixture() {
  const files: Record<string, Uint8Array> = {
    "open/core.tlpack": new TextEncoder().encode("MOCK-CORE"),
    "open/names_taxa.tlpack": new TextEncoder().encode("MOCK-NAMES"),
    "open/regional.tlpack": new TextEncoder().encode("MOCK-REGIONAL"),
    "open/ta_wiktionary.tlpack": new TextEncoder().encode("MOCK-TAWIKI"),
    "local/local_core.tlpack": new TextEncoder().encode("MOCK-LOCAL"),
  };
  const manifest: LexiconPackManifest = {
    schema_version: 2,
    pack_count: 5,
    packs: [
      {
        file: "open/core.tlpack",
        summary: makeSummary("core", "verified_open", "dictionary", files["open/core.tlpack"]),
      },
      {
        file: "open/names_taxa.tlpack",
        summary: makeSummary("names_taxa", "verified_open", "names_taxa", files["open/names_taxa.tlpack"]),
      },
      {
        file: "open/regional.tlpack",
        summary: makeSummary("regional", "verified_open", "regional", files["open/regional.tlpack"]),
      },
      {
        file: "open/ta_wiktionary.tlpack",
        summary: makeSummary("ta_wiktionary", "verified_open", "dictionary", files["open/ta_wiktionary.tlpack"]),
      },
      {
        file: "local/local_core.tlpack",
        summary: makeSummary("local_core", "local_historical", "dictionary", files["local/local_core.tlpack"]),
      },
    ],
  };
  return { files, manifest };
}

class MemoryCache implements Cache {
  private readonly store = new Map<string, Response>();

  async match(request: RequestInfo | URL): Promise<Response | undefined> {
    const key = typeof request === "string" ? request : request instanceof URL ? request.toString() : request.url;
    const hit = this.store.get(key);
    return hit ? hit.clone() : undefined;
  }

  async put(request: RequestInfo | URL, response: Response): Promise<void> {
    const key = typeof request === "string" ? request : request instanceof URL ? request.toString() : request.url;
    this.store.set(key, response.clone());
  }

  async delete(request: RequestInfo | URL): Promise<boolean> {
    const key = typeof request === "string" ? request : request instanceof URL ? request.toString() : request.url;
    return this.store.delete(key);
  }

  async keys(): Promise<readonly globalThis.Request[]> {
    return Array.from(this.store.keys()).map((url) => new Request(url));
  }

  async add(): Promise<void> {
    throw new Error("not implemented");
  }

  async addAll(): Promise<void> {
    throw new Error("not implemented");
  }

  async matchAll(): Promise<readonly Response[]> {
    return [];
  }
}

describe("JS/WASM lexicon v2 bindings and loader", () => {
  beforeAll(async () => {
    const bytes = readFileSync(new URL("../pkg-web/tamil_toolkit_bg.wasm", import.meta.url));
    await webApi.init({ module_or_path: bytes });
  });

  test("preserves exact export parity between Node and Web entrypoints", () => {
    expect(DEFAULT_LEXICON_MANIFEST_URL).toBe(
      "https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json",
    );
    for (const key of [
      "lexiconSearchEnglish",
      "lexicon_search_english",
      "DEFAULT_LEXICON_MANIFEST_URL",
      "filterManifestPacks",
      "mountLexiconFromUrl",
      "LexiconPackClient",
      "createLexiconLoader",
    ] as const) {
      expect(typeof (nodeApi as Record<string, unknown>)[key]).toBe(
        typeof (webApi as Record<string, unknown>)[key],
      );
      expect((nodeApi as Record<string, unknown>)[key]).toBeDefined();
    }
  });

  test("lexiconSearchEnglish serializes request and preserves facet stats types", () => {
    const requests: unknown[] = [];
    const api = createApi((raw) => {
      const req = JSON.parse(raw);
      requests.push(req);
      if (req.op === "lexicon_search_english") {
        return JSON.stringify({
          prefix: req.input.query,
          canonical_prefix: req.input.query.toLowerCase(),
          folded: false,
          searched_packs: ["core"],
          hits: [
            {
              headword: "\u0ba8\u0bc0\u0bb0\u0bcd",
              matched_key: "water",
              packs: ["core"],
              pack_tiers: ["verified_open"],
              pos: ["noun"],
              preview_gloss: "water",
              entry_count: 1,
            },
          ],
          has_more: false,
        });
      }
      if (req.op === "lexicon_stats") {
        return JSON.stringify({
          pack_count: 1,
          total_entries: 1,
          total_senses: 1,
          total_relations: 0,
          total_bytes: 16,
          packs: [],
          category_counts: { dictionary: 1 },
          pos_counts: { noun: 1 },
          domain_counts: {},
          region_counts: {},
          register_counts: {},
          has_english_index: true,
        });
      }
      throw new Error(`Unexpected op: ${req.op}`);
    });

    const result = api.lexiconSearchEnglish("water", {
      category: "dictionary",
      pos: "noun",
      domain: "Nature",
      region: "TN",
      register: "standard",
      limit: 15,
    });
    expect(result.hits[0].headword).toBe("\u0ba8\u0bc0\u0bb0\u0bcd");
    expect(requests[0]).toEqual({
      op: "lexicon_search_english",
      input: {
        query: "water",
        category: "dictionary",
        pos: "noun",
        domain: "Nature",
        region: "TN",
        register: "standard",
        limit: 15,
      },
    });
    const stats = api.lexicon_stats();
    expect(stats.has_english_index).toBe(true);
    expect(stats.category_counts).toEqual({ dictionary: 1 });
  });

  test("filterManifestPacks filters open-lite, open, local, full, and packIds", () => {
    const { manifest } = buildMockFixture();
    expect(filterManifestPacks(manifest, "open-lite").map((e) => e.summary.pack_id)).toEqual([
      "core",
      "names_taxa",
      "regional",
    ]);
    expect(filterManifestPacks(manifest, "open").map((e) => e.summary.pack_id)).toEqual([
      "core",
      "names_taxa",
      "regional",
      "ta_wiktionary",
    ]);
    expect(filterManifestPacks(manifest, "local").map((e) => e.summary.pack_id)).toEqual([
      "local_core",
    ]);
    expect(filterManifestPacks(manifest, "full").map((e) => e.summary.pack_id)).toHaveLength(5);
    expect(
      filterManifestPacks(manifest, "open", ["regional", "core", "regional"]).map(
        (e) => e.summary.pack_id,
      ),
    ).toEqual(["regional", "core"]);
    expect(() => filterManifestPacks(manifest, "open", ["missing"])).toThrow(
      "lexicon: unknown pack 'missing'",
    );
  });

  test("mountLexiconFromUrl downloads, caches, prunes stale SHA, and skips mounted packs", async () => {
    const { files, manifest } = buildMockFixture();
    const mounted = new Map<string, LexiconCompactPackSummary>();
    const fetchedUrls: string[] = [];

    const mockCache = new MemoryCache();
    const staleUrl = "https://cdn.example.test/packs/open/core.tlpack?sha256=" + "a".repeat(64);
    await mockCache.put(staleUrl, new Response(new Uint8Array([1, 2, 3])));
    const originalCaches = globalThis.caches;
    Object.defineProperty(globalThis, "caches", {
      configurable: true,
      value: {
        open: async (name: string) => {
          expect(name).toBe("tamil-toolkit-tlpack-v2");
          return mockCache;
        },
      } as unknown as CacheStorage,
    });

    try {
      const fetchFn: typeof fetch = async (input) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
        fetchedUrls.push(url);
        if (url === "https://cdn.example.test/packs/MANIFEST.json") {
          return new Response(JSON.stringify(manifest), { status: 200 });
        }
        const rel = url.replace("https://cdn.example.test/packs/", "");
        const blob = files[rel];
        if (!blob) {
          return new Response("Not Found", { status: 404, statusText: "Not Found" });
        }
        return new Response(blob as unknown as BodyInit, { status: 200 });
      };

      const progressPhases: string[] = [];
      const getStats = (): LexiconStatsResult => {
        const packs = Array.from(mounted.values());
        return {
          pack_count: packs.length,
          total_entries: packs.length,
          total_senses: packs.length,
          total_relations: 0,
          total_bytes: packs.reduce((acc, p) => acc + p.byte_len, 0),
          packs,
          has_english_index: packs.some((p) => p.has_english_index),
        };
      };

      const first = await mountLexiconFromUrl({
        profile: "open-lite",
        baseUrl: "https://cdn.example.test/packs",
        fetchFn,
        onProgress: (p) => progressPhases.push(p.phase),
        loadLexiconPackBytes: (packId, bytes) => {
          const entry = manifest.packs.find((p) => p.summary.pack_id === packId)!;
          expect(bytes).toEqual(files[entry.file]);
          mounted.set(packId, entry.summary);
          return entry.summary;
        },
        getStats,
      });

      expect(first.loadedPackIds).toEqual(["core", "names_taxa", "regional"]);
      expect(first.skippedPackIds).toEqual([]);
      expect(first.stats.pack_count).toBe(3);
      expect(progressPhases[0]).toBe("manifest");
      expect(progressPhases[progressPhases.length - 1]).toBe("complete");

      // Stale SHA entry was pruned from Cache API
      const cacheKeys = (await mockCache.keys()).map((r) => r.url);
      expect(cacheKeys).not.toContain(staleUrl);
      expect(cacheKeys.some((k) => k.includes("open/core.tlpack?sha256="))).toBe(true);

      // Re-mounting skips already-mounted packs
      fetchedUrls.length = 0;
      const second = await mountLexiconFromUrl({
        profile: "open-lite",
        baseUrl: "https://cdn.example.test/packs",
        fetchFn,
        loadLexiconPackBytes: () => {
          throw new Error("should not reload mounted packs");
        },
        getStats,
      });
      expect(second.loadedPackIds).toEqual([]);
      expect(second.skippedPackIds).toEqual(["core", "names_taxa", "regional"]);
      expect(fetchedUrls).toEqual(["https://cdn.example.test/packs/MANIFEST.json"]);

      // Progressive client loads remaining open pack and can unload by tier
      const client = new LexiconPackClient({
        baseUrl: "https://cdn.example.test/packs",
        fetchFn,
        loadLexiconPackBytes: (packId) => {
          const entry = manifest.packs.find((p) => p.summary.pack_id === packId)!;
          mounted.set(packId, entry.summary);
          return entry.summary;
        },
        getStats,
        unloadPack: (packId) => {
          if (packId === null || packId === undefined) mounted.clear();
          else mounted.delete(packId);
        },
      });
      const prog = await client.loadProgressive("open");
      expect(prog.skippedPackIds).toEqual(["core", "names_taxa", "regional"]);
      expect(prog.loadedPackIds).toEqual(["ta_wiktionary"]);
      expect(client.status().hasOpenPacks).toBe(true);
      expect(client.status().hasLocalPacks).toBe(false);
      expect(client.status().hasEnglishIndex).toBe(true);
      expect(client.unloadTier("open")).toEqual([
        "core",
        "names_taxa",
        "regional",
        "ta_wiktionary",
      ]);
      expect(client.status().loadedPackIds).toEqual([]);
    } finally {
      Object.defineProperty(globalThis, "caches", {
        configurable: true,
        value: originalCaches,
      });
    }
  });

  test("Node WASM lexiconSearchEnglish when rebuilt and packs exist", (ctx) => {
    const root = fileURLToPath(new URL("../../..", import.meta.url));
    const corePath = join(root, "dist/lexicon-packs/open/core.tlpack");
    if (!existsSync(corePath)) {
      ctx.skip();
      return;
    }
    nodeApi.lexicon_unload_pack(null);
    try {
      try {
        nodeApi.lexicon_load_pack_bytes(new Uint8Array(readFileSync(corePath)));
      } catch (err) {
        if (err instanceof Error && err.message.includes("unsupported flags")) {
          ctx.skip();
          return;
        }
        throw err;
      }
      const stats = nodeApi.lexicon_stats();
      if (stats.has_english_index === undefined) {
        ctx.skip();
        return;
      }
      expect(stats.has_english_index).toBe(true);
      expect(stats.category_counts?.dictionary).toBeGreaterThan(0);
      const en = nodeApi.lexiconSearchEnglish("water", { limit: 10 });
      expect(en.hits.length).toBeGreaterThan(0);
    } finally {
      nodeApi.lexicon_unload_pack(null);
    }
  });
});
