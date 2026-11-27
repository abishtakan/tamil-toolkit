import {
  createApi,
  type LexiconCompactPackSummary,
  type LexiconFuzzySearchHit,
  type LexiconFuzzySearchOptions,
  type LexiconFuzzySearchResult,
  type LexiconPrefixSearchHit,
  type LexiconPrefixSearchResult,
  type LexiconQueryOptions,
  type LexiconSearchOptions,
  type LexiconStatsResult,
  type LexiconWordDefinition,
} from "../../../../bindings/js-wasm/src/api.js";
import * as wasmPkg from "../wasm/tamil_toolkit.js";
import { initTamilEngine, isTamilEngineReady } from "./tamil-engine.js";

export type {
  LexiconCompactPackSummary,
  LexiconFuzzySearchHit,
  LexiconFuzzySearchResult,
  LexiconPrefixSearchHit,
  LexiconPrefixSearchResult,
  LexiconStatsResult,
  LexiconWordDefinition,
};

export type LexiconMountProfile = "open-lite" | "open" | "full";

export interface TlpackManifestEntry {
  file: string;
  summary: LexiconCompactPackSummary;
}

export interface TlpackManifest {
  pack_count: number;
  packs: TlpackManifestEntry[];
}

export interface LocalMountBatchResult {
  mounted: LexiconCompactPackSummary[];
  errors: Array<{ fileName: string; message: string }>;
}

export interface MountProgress {
  profile: LexiconMountProfile;
  loadedPacks: number;
  totalPacks: number;
  lastPackId?: string;
  done: boolean;
}

export interface UnifiedSearchResult {
  query: string;
  mode: "tamil" | "english";
  definition: LexiconWordDefinition | null;
  prefixHits: LexiconPrefixSearchHit[];
  englishHits: LexiconPrefixSearchHit[];
  fuzzyHits: LexiconFuzzySearchHit[];
}

export const DEFAULT_LEXICON_MANIFEST_URL =
  "https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json";
export const WORD_TLPACK_CACHE_NAME = "tamil-toolkit-tlpack-v2";

const STORAGE_MANIFEST_KEY = "tamil-toolkit-word-lexicon-manifest";
const STORAGE_PROFILE_KEY = "tamil-toolkit-word-lexicon-profile";
const OPEN_LITE_PACK_IDS = new Set(["core", "names_taxa", "regional"]);

type NativeLoadPackFn = (bytes: Uint8Array) => string;

const nativeLoadPackBytes = (
  wasmPkg as unknown as { load_lexicon_pack_bytes?: NativeLoadPackFn }
).load_lexicon_pack_bytes;

const lexiconApi = createApi(wasmPkg.execute, nativeLoadPackBytes);

function ensureReady(): void {
  if (!isTamilEngineReady()) {
    throw new Error("Tamil WASM engine is not initialized. Call initTamilEngine() first.");
  }
}

export function getSavedLexiconPrefs(): {
  manifestUrl: string;
  profile: LexiconMountProfile;
} {
  let manifestUrl = DEFAULT_LEXICON_MANIFEST_URL;
  let profile: LexiconMountProfile = "open-lite";
  try {
    const rawUrl = window.localStorage?.getItem(STORAGE_MANIFEST_KEY)?.trim();
    if (rawUrl) {
      const parsed = new URL(rawUrl);
      if (parsed.protocol === "https:" || parsed.protocol === "http:") {
        manifestUrl = parsed.toString();
      }
    }
    const rawProfile = window.localStorage?.getItem(STORAGE_PROFILE_KEY);
    if (rawProfile === "open-lite" || rawProfile === "open" || rawProfile === "full") {
      profile = rawProfile;
    }
  } catch {
    // Ignore storage restriction in sandboxed Office iframes
  }
  return { manifestUrl, profile };
}

export function saveLexiconPrefs(patch: {
  manifestUrl?: string;
  profile?: LexiconMountProfile;
}): void {
  try {
    if (patch.manifestUrl !== undefined) {
      const trimmed = patch.manifestUrl.trim();
      if (trimmed) {
        window.localStorage?.setItem(STORAGE_MANIFEST_KEY, trimmed);
      } else {
        window.localStorage?.removeItem(STORAGE_MANIFEST_KEY);
      }
    }
    if (patch.profile !== undefined) {
      window.localStorage?.setItem(STORAGE_PROFILE_KEY, patch.profile);
    }
  } catch {
    // Ignore storage restriction
  }
}

function normalizeRelFile(file: string): string {
  return file.replace(/\\/g, "/").replace(/^\/+/, "");
}

function isLocalPackEntry(entry: Pick<TlpackManifestEntry, "file" | "summary">): boolean {
  const rel = normalizeRelFile(entry.file);
  return (
    rel.startsWith("local/") ||
    rel.includes("/local/") ||
    entry.summary.pack_tier === "local_historical"
  );
}

function entryMatchesProfile(
  entry: TlpackManifestEntry,
  profile: LexiconMountProfile
): boolean {
  const isLocal = isLocalPackEntry(entry);
  if (profile === "full") return true;
  if (profile === "open") return !isLocal;
  return !isLocal && OPEN_LITE_PACK_IDS.has(entry.summary.pack_id);
}

function resolvePackCandidates(file: string, manifestUrl: string): string[] {
  const rel = normalizeRelFile(file);
  if (!rel) {
    throw new Error("Pack file path cannot be empty.");
  }
  const primary = new URL(rel, manifestUrl).toString();
  const baseName = rel.split("/").pop();
  if (baseName && baseName !== rel) {
    const flatFallback = new URL(baseName, manifestUrl).toString();
    if (flatFallback !== primary) {
      return [primary, flatFallback];
    }
  }
  return [primary];
}

function buildCacheKey(resolvedUrl: string, checksumSha256?: string): string {
  const sha = checksumSha256?.trim();
  return sha ? `${resolvedUrl}?sha256=${sha}` : resolvedUrl;
}

async function fetchPackBytesCached(
  candidateUrls: readonly string[],
  checksumSha256?: string,
  fetchImpl: typeof fetch = fetch
): Promise<Uint8Array> {
  const hasCache = typeof caches !== "undefined";
  let cache: Cache | null = null;

  if (hasCache) {
    try {
      cache = await caches.open(WORD_TLPACK_CACHE_NAME);
      for (const url of candidateUrls) {
        const cached = await cache.match(buildCacheKey(url, checksumSha256));
        if (cached && cached.ok) {
          return new Uint8Array(await cached.arrayBuffer());
        }
      }
    } catch {
      cache = null;
    }
  }

  let lastStatus = 0;
  let lastUrl = candidateUrls[0];
  let fetchedUrl = candidateUrls[0];
  let bytes: Uint8Array | null = null;

  for (const url of candidateUrls) {
    lastUrl = url;
    const res = await fetchImpl(url);
    if (res.ok) {
      fetchedUrl = url;
      bytes = new Uint8Array(await res.arrayBuffer());
      break;
    }
    lastStatus = res.status;
    if (res.status !== 404) {
      break;
    }
  }

  if (!bytes) {
    throw new Error(`Failed to fetch ${lastUrl}: HTTP ${lastStatus || "network error"}`);
  }

  if (cache) {
    const cacheKey = buildCacheKey(fetchedUrl, checksumSha256);
    try {
      await cache.put(
        cacheKey,
        new Response(bytes.slice().buffer, {
          status: 200,
          headers: { "Content-Type": "application/octet-stream" },
        })
      );
      if (typeof cache.keys === "function" && typeof cache.delete === "function") {
        const prefix = `${fetchedUrl}?sha256=`;
        for (const req of await cache.keys()) {
          const reqUrl = typeof req === "string" ? req : req.url;
          if (reqUrl !== cacheKey && (reqUrl === fetchedUrl || reqUrl.startsWith(prefix))) {
            await cache.delete(req);
          }
        }
      }
    } catch {
      // Ignore Cache API write/quota failures
    }
  }

  return bytes;
}

export async function fetchManifest(
  manifestUrl: string = DEFAULT_LEXICON_MANIFEST_URL,
  fetchImpl: typeof fetch = fetch
): Promise<TlpackManifest> {
  const res = await fetchImpl(manifestUrl);
  if (!res.ok) {
    throw new Error(`Failed to fetch manifest (${manifestUrl}): HTTP ${res.status}`);
  }
  const parsed = (await res.json()) as TlpackManifest;
  if (!parsed || !Array.isArray(parsed.packs)) {
    throw new Error("Invalid .tlpack MANIFEST.json format.");
  }
  return {
    pack_count: parsed.packs.length,
    packs: parsed.packs.map((entry) => ({
      ...entry,
      file: normalizeRelFile(entry.file),
    })),
  };
}

class WordLexiconClient {
  private userLoadedIds = new Set<string>();
  private inFlight = new Map<string, Promise<LexiconCompactPackSummary>>();

  async ensureReady(): Promise<void> {
    await initTamilEngine();
    ensureReady();
  }

  getStats(): LexiconStatsResult {
    ensureReady();
    return lexiconApi.lexicon_stats();
  }

  mountBytes(
    bytes: Uint8Array,
    source: "remote" | "local-file" = "local-file"
  ): LexiconCompactPackSummary {
    ensureReady();
    const summary = lexiconApi.lexicon_load_pack_bytes(bytes);
    if (source === "local-file") {
      this.userLoadedIds.add(summary.pack_id);
    } else {
      this.userLoadedIds.delete(summary.pack_id);
    }
    return summary;
  }

  async mountLocalFile(file: File): Promise<LexiconCompactPackSummary> {
    await this.ensureReady();
    const bytes = new Uint8Array(await file.arrayBuffer());
    return this.mountBytes(bytes, "local-file");
  }

  async mountLocalFiles(
    files: FileList | readonly File[]
  ): Promise<LocalMountBatchResult> {
    await this.ensureReady();
    const mounted: LexiconCompactPackSummary[] = [];
    const errors: Array<{ fileName: string; message: string }> = [];
    for (const file of Array.from(files)) {
      try {
        mounted.push(await this.mountLocalFile(file));
      } catch (err) {
        errors.push({
          fileName: file.name,
          message: err instanceof Error ? err.message : String(err),
        });
      }
    }
    return { mounted, errors };
  }

  unloadPack(packId: string): boolean {
    ensureReady();
    const res = lexiconApi.lexicon_unload_pack(packId);
    this.userLoadedIds.delete(packId);
    return "removed" in res ? res.removed : false;
  }

  clearAllPacks(): void {
    ensureReady();
    lexiconApi.lexicon_unload_pack(null);
    this.userLoadedIds.clear();
  }

  async mountProfile(
    profile: LexiconMountProfile,
    manifestUrl: string = DEFAULT_LEXICON_MANIFEST_URL,
    options: {
      onProgress?: (p: MountProgress) => void;
      fetchImpl?: typeof fetch;
    } = {}
  ): Promise<LexiconCompactPackSummary[]> {
    await this.ensureReady();
    const manifest = await fetchManifest(manifestUrl, options.fetchImpl);
    const targetEntries = manifest.packs.filter((entry) =>
      entryMatchesProfile(entry, profile)
    );
    const targetIds = new Set(targetEntries.map((e) => e.summary.pack_id));

    const currentStats = this.getStats();
    for (const pack of currentStats.packs) {
      if (!this.userLoadedIds.has(pack.pack_id) && !targetIds.has(pack.pack_id)) {
        this.unloadPack(pack.pack_id);
      }
    }

    const mountedIds = new Set(this.getStats().packs.map((p) => p.pack_id));
    const mounted: LexiconCompactPackSummary[] = [];
    const totalPacks = targetEntries.length;
    let loadedPacks = 0;

    for (const entry of targetEntries) {
      const packId = entry.summary.pack_id;
      if (mountedIds.has(packId)) {
        const existing = this.getStats().packs.find((p) => p.pack_id === packId);
        if (existing) mounted.push(existing);
        loadedPacks++;
        options.onProgress?.({
          profile,
          loadedPacks,
          totalPacks,
          lastPackId: packId,
          done: loadedPacks === totalPacks,
        });
        continue;
      }

      let task = this.inFlight.get(packId);
      if (!task) {
        task = (async () => {
          const urls = resolvePackCandidates(entry.file, manifestUrl);
          const bytes = await fetchPackBytesCached(
            urls,
            entry.summary.checksum_sha256,
            options.fetchImpl
          );
          return this.mountBytes(bytes, "remote");
        })();
        this.inFlight.set(packId, task);
      }

      try {
        const summary = await task;
        mounted.push(summary);
      } finally {
        this.inFlight.delete(packId);
      }

      loadedPacks++;
      options.onProgress?.({
        profile,
        loadedPacks,
        totalPacks,
        lastPackId: packId,
        done: loadedPacks === totalPacks,
      });
    }

    if (totalPacks === 0) {
      options.onProgress?.({
        profile,
        loadedPacks: 0,
        totalPacks: 0,
        done: true,
      });
    }

    return mounted;
  }

  define(word: string, options?: LexiconQueryOptions): LexiconWordDefinition {
    ensureReady();
    return lexiconApi.lexicon_define(word, options);
  }

  searchPrefix(
    prefix: string,
    options?: LexiconSearchOptions
  ): LexiconPrefixSearchResult {
    ensureReady();
    return lexiconApi.lexicon_search(prefix, options);
  }

  searchEnglish(
    query: string,
    options?: LexiconSearchOptions
  ): LexiconPrefixSearchResult {
    ensureReady();
    return lexiconApi.execute({
      op: "lexicon_search_english",
      input: query,
      ...(options ?? {}),
    }) as LexiconPrefixSearchResult;
  }

  fuzzySearch(
    word: string,
    options?: LexiconFuzzySearchOptions
  ): LexiconFuzzySearchResult {
    ensureReady();
    return lexiconApi.lexicon_fuzzy_search(word, options);
  }

  searchUnified(rawQuery: string, limit = 12): UnifiedSearchResult {
    ensureReady();
    const query = rawQuery.trim();
    const hasTamil = /[\u0B80-\u0BFF]/.test(query);

    if (!query) {
      return {
        query: "",
        mode: "tamil",
        definition: null,
        prefixHits: [],
        englishHits: [],
        fuzzyHits: [],
      };
    }

    if (!hasTamil) {
      const en = this.searchEnglish(query, { limit });
      let definition: LexiconWordDefinition | null = null;
      if (en.hits.length > 0) {
        const topDef = this.define(en.hits[0].headword, { folded: false });
        if (topDef.status === "matched") {
          definition = topDef;
        }
      }
      return {
        query,
        mode: "english",
        definition,
        prefixHits: [],
        englishHits: en.hits,
        fuzzyHits: [],
      };
    }

    const def = this.define(query, { folded: true });
    const prefix = this.searchPrefix(query, { folded: true, limit });
    const hasMatchedDef = def.status === "matched";
    let fuzzyHits: LexiconFuzzySearchHit[] = [];

    if (!hasMatchedDef && prefix.hits.length === 0) {
      fuzzyHits = this.fuzzySearch(query, { max_distance: 2, limit: 8 }).hits;
    }

    return {
      query,
      mode: "tamil",
      definition: hasMatchedDef ? def : null,
      prefixHits: prefix.hits,
      englishHits: [],
      fuzzyHits,
    };
  }
}

export const lexiconClient = new WordLexiconClient();
