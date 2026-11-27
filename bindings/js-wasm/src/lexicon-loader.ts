import type {
  LexiconCompactPackSummary,
  LexiconPackTier,
  LexiconProfile,
  LexiconStatsResult,
  LexiconTierFilter,
} from "./api.js";

export const DEFAULT_LEXICON_MANIFEST_URL =
  "https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json";

const DEFAULT_CACHE_NAME = "tamil-toolkit-tlpack-v2";
const OPEN_LITE_PACK_IDS = new Set(["core", "names_taxa", "regional"]);

export interface LexiconPackManifestEntry {
  file: string;
  url?: string;
  summary: LexiconCompactPackSummary;
}

export interface LexiconPackManifest {
  schema_version: number;
  pack_count: number;
  packs: LexiconPackManifestEntry[];
}

export interface MountLexiconProgress {
  phase: "manifest" | "downloading" | "verifying" | "mounting" | "complete";
  packId?: string;
  completedPacks: number;
  totalPacks: number;
  bytesLoaded?: number;
  totalBytes?: number;
  cached?: boolean;
}

export interface MountLexiconResult {
  loadedPackIds: string[];
  skippedPackIds: string[];
  stats: LexiconStatsResult;
}

export interface LexiconRuntimeAdapter {
  lexicon_load_pack_bytes: (bytes: Uint8Array) => LexiconCompactPackSummary;
  lexicon_stats: () => LexiconStatsResult;
  lexicon_unload_pack?: (packId?: string | null) => unknown;
}

export interface MountLexiconOptions {
  profile?: LexiconProfile;
  packIds?: string[];
  manifestUrl?: string;
  baseUrl?: string;
  cacheName?: string;
  useCache?: boolean;
  force?: boolean;
  fetchFn?: typeof fetch;
  onProgress?: (progress: MountLexiconProgress) => void;
  loadLexiconPackBytes?: (packId: string, bytes: Uint8Array) => LexiconCompactPackSummary;
  getStats?: () => LexiconStatsResult;
  runtime?: LexiconRuntimeAdapter;
}

export interface LexiconPackClientOptions {
  manifestUrl?: string;
  baseUrl?: string;
  cacheName?: string;
  useCache?: boolean;
  fetchFn?: typeof fetch;
  onProgress?: (progress: MountLexiconProgress) => void;
  loadLexiconPackBytes?: (packId: string, bytes: Uint8Array) => LexiconCompactPackSummary;
  getStats?: () => LexiconStatsResult;
  unloadPack?: (packId?: string | null) => unknown;
  runtime?: LexiconRuntimeAdapter;
}

export interface LexiconPackClientStatus {
  stats: LexiconStatsResult;
  loadedPackIds: string[];
  hasOpenPacks: boolean;
  hasLocalPacks: boolean;
  hasEnglishIndex: boolean;
}

function normalizeProfile(profile: string): LexiconProfile {
  const norm = profile.trim().toLowerCase().replace(/_/g, "-");
  if (norm === "open-lite" || norm === "lite") return "open-lite";
  if (norm === "open" || norm === "verified" || norm === "verified-open") return "open";
  if (norm === "local" || norm === "local-historical") return "local";
  if (norm === "full" || norm === "all") return "full";
  throw new Error(`lexicon: unknown profile '${profile}'`);
}

export function filterManifestPacks(
  manifest: LexiconPackManifest,
  profile: LexiconProfile = "open",
  packIds?: string[],
): LexiconPackManifestEntry[] {
  const entries = Array.isArray(manifest.packs) ? manifest.packs : [];
  if (packIds !== undefined) {
    const byId = new Map<string, LexiconPackManifestEntry>();
    for (const entry of entries) {
      if (entry?.summary?.pack_id) {
        byId.set(entry.summary.pack_id, entry);
      }
    }
    const selected: LexiconPackManifestEntry[] = [];
    const seen = new Set<string>();
    for (const packId of packIds) {
      if (seen.has(packId)) continue;
      seen.add(packId);
      const found = byId.get(packId);
      if (!found) {
        throw new Error(`lexicon: unknown pack '${packId}'`);
      }
      selected.push(found);
    }
    return selected;
  }

  const normalized = normalizeProfile(profile);
  if (normalized === "open-lite") {
    return entries.filter((entry) => OPEN_LITE_PACK_IDS.has(entry.summary.pack_id));
  }
  if (normalized === "open") {
    return entries.filter((entry) => entry.summary.pack_tier === "verified_open");
  }
  if (normalized === "local") {
    return entries.filter((entry) => entry.summary.pack_tier === "local_historical");
  }
  return [...entries];
}

function resolveManifestUrl(options: Pick<MountLexiconOptions, "manifestUrl" | "baseUrl">): string {
  if (options.manifestUrl) {
    return options.manifestUrl;
  }
  if (options.baseUrl) {
    const trimmed = options.baseUrl.replace(/\/+$/, "");
    return `${trimmed}/MANIFEST.json`;
  }
  return DEFAULT_LEXICON_MANIFEST_URL;
}

function resolvePackUrl(entry: LexiconPackManifestEntry, manifestUrl: string): string {
  if (entry.url) {
    return entry.url;
  }
  const rel = entry.file.replace(/\\/g, "/").replace(/^\/+/, "");
  if (!rel || rel.split("/").includes("..")) {
    throw new Error(`lexicon: invalid manifest pack file path '${entry.file}'`);
  }
  try {
    return new URL(rel, manifestUrl).toString();
  } catch {
    const base = manifestUrl.replace(/\/[^/]*$/, "");
    return `${base}/${rel}`;
  }
}

function withShaQuery(url: string, sha256: string): string {
  try {
    const parsed = new URL(url);
    parsed.searchParams.set("sha256", sha256);
    return parsed.toString();
  } catch {
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}sha256=${encodeURIComponent(sha256)}`;
  }
}

async function computeSha256Hex(bytes: Uint8Array): Promise<string | null> {
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) {
    return null;
  }
  const view =
    bytes.byteOffset === 0 && bytes.byteLength === bytes.buffer.byteLength
      ? bytes
      : bytes.slice();
  const digest = await subtle.digest("SHA-256", view as BufferSource);
  const arr = new Uint8Array(digest);
  let hex = "";
  for (let i = 0; i < arr.length; i += 1) {
    hex += arr[i].toString(16).padStart(2, "0");
  }
  return hex;
}

async function pruneStaleCacheEntries(
  cache: Cache,
  packUrl: string,
  expectedSha: string,
): Promise<void> {
  if (typeof cache.keys !== "function") {
    return;
  }
  let targetPath: string | null = null;
  try {
    targetPath = new URL(packUrl).pathname;
  } catch {
    targetPath = null;
  }
  const keys = await cache.keys();
  for (const req of keys) {
    const reqUrl = typeof req === "string" ? req : req.url;
    try {
      const parsed = new URL(reqUrl);
      if (targetPath !== null && parsed.pathname === targetPath) {
        const cachedSha = parsed.searchParams.get("sha256");
        if (cachedSha !== null && cachedSha.toLowerCase() !== expectedSha.toLowerCase()) {
          await cache.delete(req);
        }
      }
    } catch {
      // Ignore unparseable cache keys.
    }
  }
}

function emptyStats(): LexiconStatsResult {
  return {
    pack_count: 0,
    total_entries: 0,
    total_senses: 0,
    total_relations: 0,
    total_bytes: 0,
    packs: [],
    category_counts: {},
    pos_counts: {},
    domain_counts: {},
    region_counts: {},
    register_counts: {},
    has_english_index: false,
  };
}

export async function mountLexiconFromUrl(
  options: MountLexiconOptions = {},
): Promise<MountLexiconResult> {
  const loadPackBytes =
    options.loadLexiconPackBytes ??
    (options.runtime
      ? (_packId: string, bytes: Uint8Array) => options.runtime!.lexicon_load_pack_bytes(bytes)
      : undefined);
  if (!loadPackBytes) {
    throw new Error(
      "lexicon: loadLexiconPackBytes or runtime adapter is required when calling mountLexiconFromUrl",
    );
  }
  const getStats =
    options.getStats ?? (options.runtime ? () => options.runtime!.lexicon_stats() : undefined);

  const fetchImpl = options.fetchFn ?? globalThis.fetch;
  if (typeof fetchImpl !== "function") {
    throw new Error("lexicon: global fetch is unavailable; provide fetchFn in options");
  }

  const manifestUrl = resolveManifestUrl(options);
  options.onProgress?.({
    phase: "manifest",
    completedPacks: 0,
    totalPacks: 0,
  });

  const manifestResp = await fetchImpl(manifestUrl);
  if (!manifestResp.ok) {
    throw new Error(
      `lexicon: failed to fetch manifest from ${manifestUrl} (${manifestResp.status} ${manifestResp.statusText})`,
    );
  }
  const manifest = (await manifestResp.json()) as LexiconPackManifest;
  const selected = filterManifestPacks(manifest, options.profile ?? "open", options.packIds);

  const mountedById = new Map<string, LexiconCompactPackSummary>();
  if (getStats) {
    for (const mounted of getStats().packs ?? []) {
      mountedById.set(mounted.pack_id, mounted);
    }
  }

  const canUseCache =
    options.useCache !== false && typeof globalThis.caches !== "undefined";
  const cache = canUseCache
    ? await globalThis.caches.open(options.cacheName ?? DEFAULT_CACHE_NAME)
    : undefined;

  const loadedPackIds: string[] = [];
  const skippedPackIds: string[] = [];
  const totalPacks = selected.length;
  let completedPacks = 0;

  for (const entry of selected) {
    const packId = entry.summary.pack_id;
    const expectedSha = entry.summary.checksum_sha256.toLowerCase();
    const totalBytes = entry.summary.byte_len;

    const alreadyMounted = mountedById.get(packId);
    if (
      !options.force &&
      alreadyMounted &&
      alreadyMounted.checksum_sha256.toLowerCase() === expectedSha
    ) {
      skippedPackIds.push(packId);
      completedPacks += 1;
      options.onProgress?.({
        phase: "mounting",
        packId,
        completedPacks,
        totalPacks,
        bytesLoaded: totalBytes,
        totalBytes,
        cached: true,
      });
      continue;
    }

    const packUrl = resolvePackUrl(entry, manifestUrl);
    const cacheUrl = withShaQuery(packUrl, expectedSha);
    let bytes: Uint8Array | undefined;
    let fromCache = false;

    if (cache && !options.force) {
      const cached = await cache.match(cacheUrl);
      if (cached) {
        const candidate = new Uint8Array(await cached.arrayBuffer());
        const actualSha = await computeSha256Hex(candidate);
        if (actualSha === null || actualSha === expectedSha) {
          bytes = candidate;
          fromCache = true;
        } else {
          await cache.delete(cacheUrl);
        }
      }
    }

    if (!bytes) {
      options.onProgress?.({
        phase: "downloading",
        packId,
        completedPacks,
        totalPacks,
        bytesLoaded: 0,
        totalBytes,
        cached: false,
      });
      const packResp = await fetchImpl(packUrl);
      if (!packResp.ok) {
        throw new Error(
          `lexicon: failed to download pack '${packId}' from ${packUrl} (${packResp.status} ${packResp.statusText})`,
        );
      }
      bytes = new Uint8Array(await packResp.arrayBuffer());
      options.onProgress?.({
        phase: "verifying",
        packId,
        completedPacks,
        totalPacks,
        bytesLoaded: bytes.byteLength,
        totalBytes,
        cached: false,
      });
      const actualSha = await computeSha256Hex(bytes);
      if (actualSha !== null && actualSha !== expectedSha) {
        throw new Error(
          `lexicon: SHA-256 mismatch for '${packId}': expected ${expectedSha}, got ${actualSha}`,
        );
      }
      if (cache) {
        await pruneStaleCacheEntries(cache, packUrl, expectedSha);
        const body =
          bytes.byteOffset === 0 && bytes.byteLength === bytes.buffer.byteLength
            ? bytes
            : bytes.slice();
        await cache.put(
          cacheUrl,
          new Response(body as BodyInit, {
            headers: { "Content-Type": "application/octet-stream" },
          }),
        );
      }
    }

    options.onProgress?.({
      phase: "mounting",
      packId,
      completedPacks,
      totalPacks,
      bytesLoaded: bytes.byteLength,
      totalBytes,
      cached: fromCache,
    });
    loadPackBytes(packId, bytes);
    loadedPackIds.push(packId);
    completedPacks += 1;
  }

  const stats = getStats ? getStats() : emptyStats();
  options.onProgress?.({
    phase: "complete",
    completedPacks,
    totalPacks,
  });

  return { loadedPackIds, skippedPackIds, stats };
}

export class LexiconPackClient {
  private readonly options: LexiconPackClientOptions;

  constructor(options: LexiconPackClientOptions = {}) {
    this.options = options;
  }

  private resolveStats(): LexiconStatsResult {
    const getStats =
      this.options.getStats ??
      (this.options.runtime ? () => this.options.runtime!.lexicon_stats() : undefined);
    if (!getStats) {
      throw new Error("lexicon: getStats or runtime adapter is required");
    }
    return getStats();
  }

  async loadProfile(
    profile: LexiconProfile = "open",
    overrides: Partial<MountLexiconOptions> = {},
  ): Promise<MountLexiconResult> {
    return mountLexiconFromUrl({
      manifestUrl: this.options.manifestUrl,
      baseUrl: this.options.baseUrl,
      cacheName: this.options.cacheName,
      useCache: this.options.useCache,
      fetchFn: this.options.fetchFn,
      onProgress: this.options.onProgress,
      loadLexiconPackBytes: this.options.loadLexiconPackBytes,
      getStats: this.options.getStats,
      runtime: this.options.runtime,
      ...overrides,
      profile,
    });
  }

  async loadProgressive(
    targetProfile: LexiconProfile = "open",
    overrides: Partial<MountLexiconOptions> = {},
  ): Promise<MountLexiconResult> {
    const first = await this.loadProfile("open-lite", overrides);
    if (targetProfile === "open-lite") {
      return first;
    }
    const second = await this.loadProfile(targetProfile, overrides);
    const loadedPackIds = Array.from(
      new Set([...first.loadedPackIds, ...second.loadedPackIds]),
    );
    const loadedSet = new Set(loadedPackIds);
    const skippedPackIds = Array.from(
      new Set([...first.skippedPackIds, ...second.skippedPackIds]),
    ).filter((id) => !loadedSet.has(id));
    return {
      loadedPackIds,
      skippedPackIds,
      stats: second.stats,
    };
  }

  unloadTier(tier: LexiconTierFilter | LexiconPackTier): string[] {
    const unload =
      this.options.unloadPack ??
      (this.options.runtime?.lexicon_unload_pack
        ? (id?: string | null) => this.options.runtime!.lexicon_unload_pack!(id ?? null)
        : undefined);
    if (!unload) {
      throw new Error("lexicon: unloadPack or runtime adapter is required");
    }
    const norm = tier.trim().toLowerCase();
    if (norm === "all") {
      const current = this.resolveStats().packs.map((p) => p.pack_id);
      unload(null);
      return current;
    }
    const targetTier: LexiconPackTier =
      norm === "open" || norm === "verified_open"
        ? "verified_open"
        : norm === "local" || norm === "local_historical"
          ? "local_historical"
          : (() => {
              throw new Error(`lexicon: unknown tier '${tier}'`);
            })();
    const matching = this.resolveStats()
      .packs.filter((p) => p.pack_tier === targetTier)
      .map((p) => p.pack_id);
    for (const packId of matching) {
      unload(packId);
    }
    return matching;
  }

  status(): LexiconPackClientStatus {
    const stats = this.resolveStats();
    const packs = stats.packs ?? [];
    return {
      stats,
      loadedPackIds: packs.map((p) => p.pack_id),
      hasOpenPacks: packs.some((p) => p.pack_tier === "verified_open"),
      hasLocalPacks: packs.some((p) => p.pack_tier === "local_historical"),
      hasEnglishIndex: Boolean(stats.has_english_index ?? packs.some((p) => p.has_english_index)),
    };
  }
}

export function createLexiconLoader(runtime: LexiconRuntimeAdapter) {
  class BoundLexiconPackClient extends LexiconPackClient {
    constructor(options: LexiconPackClientOptions = {}) {
      super({ runtime, ...options });
    }
  }
  return {
    mountLexiconFromUrl: (options: MountLexiconOptions = {}) =>
      mountLexiconFromUrl({ runtime, ...options }),
    LexiconPackClient: BoundLexiconPackClient as typeof LexiconPackClient,
  };
}
