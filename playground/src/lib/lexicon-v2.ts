import type * as tt from "tamil-toolkit/web";
import {
  getLexiconStats,
  loadLexiconPackBytes,
  unloadLexiconPack,
  type LexiconV2Stats,
} from "./engine";

export interface TlpackManifestEntry {
  file: string;
  summary: tt.LexiconCompactPackSummary;
}

export interface TlpackManifest {
  pack_count: number;
  packs: TlpackManifestEntry[];
}

export interface V2PackFetchOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  isOpenOnly?: boolean;
  isPublicBeta?: boolean;
  useCache?: boolean;
}

export interface V2LocalMountBatchResult {
  mounted: tt.LexiconCompactPackSummary[];
  errors: Array<{ fileName: string; message: string }>;
}

export interface V2QueryScopeInput {
  packs?: readonly string[];
  tier?: tt.LexiconTierFilter;
  category?: tt.LexiconCategory | "all" | string;
  pos?: string;
  domain?: string;
  region?: string;
  register?: string;
  folded?: boolean;
}

export interface V2SearchOptionsInput extends V2QueryScopeInput {
  limit?: number;
  after_key?: string;
}

export type BrowseLexiconCategory = Exclude<tt.LexiconCategory, "relations">;

export interface LexiconCategoryMeta {
  id: tt.LexiconCategory;
  label_en: string;
  label_ta: string;
  description_en: string;
  description_ta: string;
}

export const LEXICON_CATEGORIES: readonly (LexiconCategoryMeta & {
  id: BrowseLexiconCategory;
})[] = [
  {
    id: "dictionary",
    label_en: "Dictionary",
    label_ta: "அகராதி",
    description_en: "Core Tamil definitions and Wiktionary entries",
    description_ta: "அடிப்படைத் தமிழ் அகராதி மற்றும் விக்சனரி பதிவுகள்",
  },
  {
    id: "terminology",
    label_en: "Terminology",
    label_ta: "கலைச்சொற்கள்",
    description_en: "Technical, scientific, and domain glossaries",
    description_ta: "அறிவியல், தொழில்நுட்பம் மற்றும் துறைசார் கலைச்சொற்கள்",
  },
  {
    id: "phrases",
    label_en: "Phrases",
    label_ta: "சொற்றொடர்கள்",
    description_en: "Multi-word expressions, idioms, and proverbs",
    description_ta: "மரபுத்தொடர்கள், பழமொழிகள் மற்றும் கூட்டுச்சொற்கள்",
  },
  {
    id: "regional",
    label_en: "Regional",
    label_ta: "வட்டார வழக்கு",
    description_en: "TN & SL regional varieties (Jaffna, Kongu, Chennai)",
    description_ta: "இலங்கை மற்றும் தமிழ்நாடு வட்டார வழக்குச் சொற்கள்",
  },
  {
    id: "names_taxa",
    label_en: "Names & Taxa",
    label_ta: "பெயர்கள் & உயிரினம்",
    description_en: "Proper names, flora, fauna, and scientific taxa",
    description_ta: "சிறப்புப் பெயர்கள், தாவரங்கள் மற்றும் விலங்கினப் பெயர்கள்",
  },
  {
    id: "heritage",
    label_en: "Heritage",
    label_ta: "பாரம்பரியம்",
    description_en: "Classical literary Tamil and historical loanword strata",
    description_ta: "சங்க இலக்கியச் சொற்கள் மற்றும் பிறமொழிக் கடன் சொற்கள்",
  },
];

export const LEXICON_RELATIONS_CATEGORY: LexiconCategoryMeta = {
  id: "relations",
  label_en: "Relations",
  label_ta: "சொல் தொடர்புகள்",
  description_en: "Semantic synonyms, antonyms, related terms, and hypernyms",
  description_ta: "ஒத்த சொற்கள், எதிர்ச்சொற்கள் மற்றும் தொடர்புடைய சொற்கள்",
};

const CATEGORY_META_MAP = new Map<tt.LexiconCategory, LexiconCategoryMeta>([
  ...LEXICON_CATEGORIES.map((c) => [c.id, c] as const),
  [LEXICON_RELATIONS_CATEGORY.id, LEXICON_RELATIONS_CATEGORY],
]);

/**
 * Returns display metadata for a high-level `LexiconCategory`.
 */
export function getLexiconCategoryMeta(
  category: tt.LexiconCategory
): LexiconCategoryMeta {
  return CATEGORY_META_MAP.get(category) ?? LEXICON_CATEGORIES[0];
}

/**
 * Maps any canonical or local `pack_id` into its high-level `LexiconCategory`,
 * matching Rust `tamil_lexicon::pack_category`.
 */
export function packCategory(packId: string): tt.LexiconCategory {
  switch (packId) {
    case "core":
    case "ta_wiktionary":
    case "local_core":
      return "dictionary";
    case "terminology":
    case "local_terminology":
      return "terminology";
    case "local_phrases":
      return "phrases";
    case "regional":
    case "local_dialect":
      return "regional";
    case "names_taxa":
    case "local_names_taxa":
      return "names_taxa";
    case "local_literary":
    case "local_loans":
      return "heritage";
    case "local_relations":
      return "relations";
    default: {
      const lower = packId.toLowerCase();
      if (lower.includes("term")) return "terminology";
      if (lower.includes("phrase")) return "phrases";
      if (lower.includes("dialect") || lower.includes("region")) return "regional";
      if (lower.includes("name") || lower.includes("taxa")) return "names_taxa";
      if (lower.includes("literary") || lower.includes("loan")) return "heritage";
      if (lower.includes("relation")) return "relations";
      return "dictionary";
    }
  }
}

export type ProgressiveLoadStage = "open-lite" | "open" | "full";

export interface ProgressiveMountProgress {
  stage: ProgressiveLoadStage;
  loadedPacks: number;
  totalPacks: number;
  mountedWordEstimate: number;
  lastPackId?: string;
  done: boolean;
}

export interface AutoMountProgressiveOptions extends V2PackFetchOptions {
  manifest?: TlpackManifest | null;
  includeLocal?: boolean;
  onProgress?: (progress: ProgressiveMountProgress) => void;
}

export const TLPACK_CACHE_NAME = "tamil-toolkit-tlpack-v2";
const OPEN_LITE_PACK_ORDER = ["core", "names_taxa", "regional"] as const;
const ASCII_LATIN_QUERY_RE = /^[A-Za-z0-9\s\-']+$/;

/**
 * Resolves whether the playground `.tlpack` channel is locked to `open` (`verified_open` only).
 * Defaults to `false` (`full` channel: all 12 packs / ~241k words) unless `VITE_LEXICON_CHANNEL=open`.
 */
export function resolveIsOpenOnlyChannel(
  channel: string | undefined = (
    import.meta as unknown as { env?: Record<string, string | undefined> }
  ).env?.VITE_LEXICON_CHANNEL
): boolean {
  return (channel ?? "").trim().toLowerCase() === "open";
}

export const IS_OPEN_ONLY_CHANNEL = resolveIsOpenOnlyChannel();

/**
 * Resolves the `.tlpack` base URL from `import.meta.env.VITE_LEXICON_BASE_URL`
 * (supporting Cloudflare R2 or custom CDN origins), defaulting to `"/lexicon-packs"`.
 */
export function getDefaultLexiconBaseUrl(
  overrideEnv?: string | undefined
): string {
  const raw =
    overrideEnv !== undefined
      ? overrideEnv
      : (
          import.meta as unknown as { env?: Record<string, string | undefined> }
        ).env?.VITE_LEXICON_BASE_URL;
  const trimmed = (raw ?? "").trim().replace(/\/+$/, "");
  return trimmed || "/lexicon-packs";
}

export const DEFAULT_LEXICON_BASE_URL = getDefaultLexiconBaseUrl();

function resolveOpenOnlyOption(options?: V2PackFetchOptions): boolean {
  return options?.isOpenOnly ?? options?.isPublicBeta ?? IS_OPEN_ONLY_CHANNEL;
}

export type UnifiedSearchHitSource = "tamil" | "english" | "tanglish";

export interface UnifiedLexiconSearchHit extends tt.LexiconPrefixSearchHit {
  matchSource?: UnifiedSearchHitSource;
}

/**
 * Returns true for pure ASCII Latin queries (English words or Tanglish input).
 */
export function isAsciiLatinQuery(query: string): boolean {
  const trimmed = query.trim();
  return trimmed.length > 0 && ASCII_LATIN_QUERY_RE.test(trimmed);
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function scoreEnglishGlossMatch(
  hit: tt.LexiconPrefixSearchHit,
  qLower: string
): number {
  if (hit.matched_key.trim().toLowerCase() === qLower) return 0;
  const gloss = (hit.preview_gloss ?? "").trim().toLowerCase();
  if (!gloss) return 2;
  if (gloss === qLower) return 0;
  const segments = gloss.split(/[;,/()]+/);
  for (const seg of segments) {
    if (seg.trim() === qLower) return 0;
  }
  const wordRe = new RegExp(`\\b${escapeRegExp(qLower)}\\b`, "i");
  if (wordRe.test(gloss)) return 1;
  return 2;
}

/**
 * Merges reverse English gloss lookup hits and phonetic Tanglish-to-Tamil lookup hits,
 * deduplicated by `headword`, prioritizing exact English gloss matches first.
 */
export function mergeEnglishAndTanglishHits(
  query: string,
  englishHits: readonly tt.LexiconPrefixSearchHit[],
  tanglishHits: readonly tt.LexiconPrefixSearchHit[]
): UnifiedLexiconSearchHit[] {
  const qLower = query.trim().toLowerCase();
  const rankedEnglish = englishHits
    .map((hit, index) => ({
      hit,
      index,
      score: qLower ? scoreEnglishGlossMatch(hit, qLower) : 2,
    }))
    .sort((a, b) => (a.score !== b.score ? a.score - b.score : a.index - b.index));

  const seen = new Set<string>();
  const out: UnifiedLexiconSearchHit[] = [];

  for (const { hit } of rankedEnglish) {
    if (seen.has(hit.headword)) continue;
    seen.add(hit.headword);
    out.push({ ...hit, matchSource: "english" });
  }

  for (const hit of tanglishHits) {
    if (seen.has(hit.headword)) continue;
    seen.add(hit.headword);
    out.push({ ...hit, matchSource: "tanglish" });
  }

  return out;
}

/**
 * Formats large facet entry counts concisely for pills (e.g. `118k`, `10.3k`, `272`).
 */
export function formatCompactFacetCount(count: number): string {
  if (count >= 100_000) return `${Math.round(count / 1000)}k`;
  if (count >= 1_000) {
    return `${(count / 1000).toFixed(1).replace(/\.0$/, "")}k`;
  }
  return count.toLocaleString();
}

function normalizeRelFile(file: string): string {
  return file.replace(/\\/g, "/").replace(/^\/+/, "");
}

/**
 * Returns true if the manifest entry points to a `local/` or `local_historical` pack.
 */
export function isLocalPackEntry(
  entry: Pick<TlpackManifestEntry, "file" | "summary">
): boolean {
  const rel = normalizeRelFile(entry.file);
  return (
    rel.startsWith("local/") ||
    rel.includes("/local/") ||
    entry.summary.pack_tier === "local_historical"
  );
}

/**
 * Filters a `.tlpack` manifest for runtime mode. In `open` channel mode,
 * all `local/` / `local_historical` entries are excluded.
 */
export function filterTlpackManifest(
  manifest: TlpackManifest,
  isOpenOnly: boolean = IS_OPEN_ONLY_CHANNEL
): TlpackManifest {
  const packs = manifest.packs
    .map((entry) => ({
      ...entry,
      file: normalizeRelFile(entry.file),
    }))
    .filter((entry) => !(isOpenOnly && isLocalPackEntry(entry)));
  return {
    pack_count: packs.length,
    packs,
  };
}

/**
 * Resolves a `.tlpack` asset URL under `baseUrl`, refusing `local/` paths in `open` channel mode.
 */
export function resolveTlpackUrl(
  file: string,
  baseUrl: string = getDefaultLexiconBaseUrl(),
  isOpenOnly: boolean = IS_OPEN_ONLY_CHANNEL
): string {
  const rel = normalizeRelFile(file);
  if (!rel) {
    throw new Error("Pack file path cannot be empty");
  }
  if (isOpenOnly && (rel.startsWith("local/") || rel.includes("/local/"))) {
    throw new Error(
      `Refusing to auto-fetch local historical pack '${rel}' in open-only / public beta mode`
    );
  }
  const cleanBase = baseUrl.replace(/\/+$/, "");
  return `${cleanBase}/${rel}`;
}

/**
 * Builds the Cache API key for a `.tlpack` URL, incorporating `sha256` to bust stale entries.
 */
export function buildTlpackCacheKey(
  resolvedUrl: string,
  checksumSha256?: string
): string {
  const sha = checksumSha256?.trim();
  return sha ? `${resolvedUrl}?sha256=${sha}` : resolvedUrl;
}

/**
 * Fetches `.tlpack` bytes using the Browser Cache API (`tamil-toolkit-tlpack-v2`) when
 * `caches` is available, falling back seamlessly to standard `fetch()`.
 */
export async function fetchTlpackBytes(
  resolvedUrl: string,
  options: {
    checksumSha256?: string;
    fetchImpl?: typeof fetch;
    useCache?: boolean;
    fileLabel?: string;
  } = {}
): Promise<Uint8Array> {
  const fetchFn = options.fetchImpl ?? fetch;
  const useCache = options.useCache !== false && typeof caches !== "undefined";
  const cacheKey = buildTlpackCacheKey(resolvedUrl, options.checksumSha256);

  let cache: Cache | null = null;
  if (useCache) {
    try {
      cache = await caches.open(TLPACK_CACHE_NAME);
      const cached = await cache.match(cacheKey);
      if (cached && cached.ok) {
        const buffer = await cached.arrayBuffer();
        return new Uint8Array(buffer);
      }
    } catch {
      cache = null;
    }
  }

  const res = await fetchFn(resolvedUrl);
  if (!res.ok) {
    throw new Error(
      `Failed to fetch ${options.fileLabel ?? resolvedUrl}: HTTP ${res.status}`
    );
  }
  const buffer = await res.arrayBuffer();
  const bytes = new Uint8Array(buffer);

  if (cache) {
    try {
      await cache.put(
        cacheKey,
        new Response(bytes.slice().buffer, {
          status: 200,
          headers: { "Content-Type": "application/octet-stream" },
        })
      );
      if (typeof cache.keys === "function" && typeof cache.delete === "function") {
        const existingKeys = await cache.keys();
        const base =
          typeof location !== "undefined" && location?.href
            ? location.href
            : "http://localhost";
        const normalizeKey = (raw: string): string => {
          try {
            return new URL(raw, base).href;
          } catch {
            return raw;
          }
        };
        const targetBase = normalizeKey(resolvedUrl);
        const targetCurrent = normalizeKey(cacheKey);
        const targetShaPrefix = `${targetBase}?sha256=`;

        for (const req of existingKeys) {
          const rawUrl = typeof req === "string" ? req : req.url;
          const normalizedUrl = normalizeKey(rawUrl);
          if (
            normalizedUrl !== targetCurrent &&
            (normalizedUrl === targetBase || normalizedUrl.startsWith(targetShaPrefix))
          ) {
            await cache.delete(req);
          }
        }
      }
    } catch {
      // Ignore Cache API write/quota failures (private browsing, etc.)
    }
  }

  return bytes;
}

/**
 * Fetches `${baseUrl}/MANIFEST.json` if present, applying `IS_OPEN_ONLY_CHANNEL` filtering.
 * Returns `null` when the manifest endpoint responds with non-OK (e.g., 404).
 */
export async function fetchTlpackManifest(
  options: V2PackFetchOptions = {}
): Promise<TlpackManifest | null> {
  const baseUrl = (options.baseUrl ?? getDefaultLexiconBaseUrl()).replace(/\/+$/, "");
  const fetchFn = options.fetchImpl ?? fetch;
  const isOpenOnly = resolveOpenOnlyOption(options);

  const res = await fetchFn(`${baseUrl}/MANIFEST.json`);
  if (!res.ok) {
    return null;
  }
  const raw = (await res.json()) as TlpackManifest;
  if (!raw || !Array.isArray(raw.packs)) {
    return null;
  }
  return filterTlpackManifest(raw, isOpenOnly);
}

/**
 * Builds clean `LexiconQueryOptions` without empty filter strings (which Rust rejects).
 */
export function buildV2QueryOptions(
  input: V2QueryScopeInput
): tt.LexiconQueryOptions {
  const opts: tt.LexiconQueryOptions = {};
  if (input.packs && input.packs.length > 0) {
    opts.packs = [...input.packs];
  }
  if (input.tier && input.tier !== "all") {
    opts.tier = input.tier;
  }
  if (
    input.category &&
    input.category.trim() &&
    input.category !== "all" &&
    input.category !== "ALL"
  ) {
    opts.category = input.category.trim();
  }
  if (input.pos && input.pos.trim() && input.pos !== "ALL") {
    opts.pos = input.pos.trim();
  }
  if (input.domain && input.domain.trim() && input.domain !== "ALL") {
    opts.domain = input.domain.trim();
  }
  if (input.region && input.region.trim() && input.region !== "ALL") {
    opts.region = input.region.trim();
  }
  if (input.register && input.register.trim() && input.register !== "ALL") {
    opts.register = input.register.trim();
  }
  if (input.folded !== undefined) {
    opts.folded = input.folded;
  }
  return opts;
}

/**
 * Builds clean `LexiconSearchOptions` for FST prefix search without empty filter strings.
 */
export function buildV2SearchOptions(
  input: V2SearchOptionsInput
): tt.LexiconSearchOptions {
  const opts: tt.LexiconSearchOptions = buildV2QueryOptions(input);
  if (input.limit !== undefined) {
    opts.limit = input.limit;
  }
  if (input.after_key !== undefined && input.after_key !== "") {
    opts.after_key = input.after_key;
  }
  return opts;
}

/**
 * Formats pack byte lengths into concise human-readable sizes.
 */
export function formatPackBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function buildProgressiveStagePlan(
  manifest: TlpackManifest,
  includeLocal: boolean,
  isPublicBeta: boolean
): Array<{ stage: ProgressiveLoadStage; entry: TlpackManifestEntry }> {
  const safeManifest = filterTlpackManifest(manifest, isPublicBeta);
  const openPacks = safeManifest.packs.filter(
    (entry) => entry.summary.pack_tier === "verified_open" && !isLocalPackEntry(entry)
  );

  const stage1Entries: TlpackManifestEntry[] = [];
  for (const id of OPEN_LITE_PACK_ORDER) {
    const hit = openPacks.find((entry) => entry.summary.pack_id === id);
    if (hit) stage1Entries.push(hit);
  }
  for (const entry of openPacks) {
    if (
      entry.summary.pack_id !== "ta_wiktionary" &&
      !stage1Entries.some((item) => item.summary.pack_id === entry.summary.pack_id)
    ) {
      stage1Entries.push(entry);
    }
  }

  const stage2Entries = openPacks.filter(
    (entry) => entry.summary.pack_id === "ta_wiktionary"
  );

  const stage3Entries =
    !isPublicBeta && includeLocal
      ? safeManifest.packs
          .filter((entry) => isLocalPackEntry(entry))
          .sort((a, b) => {
            const aTerm = a.summary.pack_id === "local_terminology" ? 1 : 0;
            const bTerm = b.summary.pack_id === "local_terminology" ? 1 : 0;
            if (aTerm !== bTerm) return aTerm - bTerm;
            if (a.summary.byte_len !== b.summary.byte_len) {
              return a.summary.byte_len - b.summary.byte_len;
            }
            return a.summary.pack_id.localeCompare(b.summary.pack_id);
          })
      : [];

  return [
    ...stage1Entries.map((entry) => ({ stage: "open-lite" as const, entry })),
    ...stage2Entries.map((entry) => ({ stage: "open" as const, entry })),
    ...stage3Entries.map((entry) => ({ stage: "full" as const, entry })),
  ];
}

/**
 * Client-side `.tlpack` v2 pack manager for browser WASM.
 * Caches mounted pack IDs, fetches hosted packs lazily on demand (with Cache API support),
 * enforces `IS_OPEN_ONLY_CHANNEL` restrictions on `local/` fetches, and supports 100% local
 * mounting of user-selected `.tlpack` files with zero server upload.
 */
export class LexiconV2PackManager {
  private mountedPacks = new Map<string, tt.LexiconCompactPackSummary>();
  private inFlight = new Map<string, Promise<tt.LexiconCompactPackSummary>>();
  private userLoadedIds = new Set<string>();
  private localEpoch = 0;
  private progressiveRuns = new Map<
    string,
    {
      promise: Promise<tt.LexiconCompactPackSummary[]>;
      listeners: Set<(progress: ProgressiveMountProgress) => void>;
    }
  >();

  /**
   * Synchronizes the local pack cache with the Rust WASM runtime registry.
   */
  syncFromEngine(): LexiconV2Stats {
    const stats = getLexiconStats();
    const next = new Map<string, tt.LexiconCompactPackSummary>();
    for (const pack of stats.packs) {
      next.set(pack.pack_id, pack);
    }
    this.mountedPacks = next;
    for (const id of Array.from(this.userLoadedIds)) {
      if (!next.has(id)) {
        this.userLoadedIds.delete(id);
      }
    }
    return stats;
  }

  getMountedPacks(): tt.LexiconCompactPackSummary[] {
    return Array.from(this.mountedPacks.values());
  }

  getMountedPackIds(): string[] {
    return Array.from(this.mountedPacks.keys());
  }

  getMountedWordEstimate(): number {
    let total = 0;
    for (const pack of this.mountedPacks.values()) {
      total += pack.distinct_headwords;
    }
    return total;
  }

  isMounted(packId: string): boolean {
    return this.mountedPacks.has(packId);
  }

  isUserLoaded(packId: string): boolean {
    return this.userLoadedIds.has(packId);
  }

  /**
   * Lazily fetches a hosted `.tlpack` file (using Cache API when available) and mounts it
   * into the WASM engine. Deduplicates concurrent requests and skips fetch if already mounted.
   */
  async fetchAndMountPack(
    entry: TlpackManifestEntry,
    options: V2PackFetchOptions = {}
  ): Promise<tt.LexiconCompactPackSummary> {
    const isOpenOnly = resolveOpenOnlyOption(options);
    if (isOpenOnly && isLocalPackEntry(entry)) {
      throw new Error(
        `Local archive pack '${entry.summary.pack_id}' cannot be auto-fetched in open-only / public beta builds`
      );
    }

    const packId = entry.summary.pack_id;
    const cached = this.mountedPacks.get(packId);
    if (cached) {
      return cached;
    }

    const existingPromise = this.inFlight.get(packId);
    if (existingPromise) {
      return existingPromise;
    }

    const url = resolveTlpackUrl(
      entry.file,
      options.baseUrl ?? getDefaultLexiconBaseUrl(),
      isOpenOnly
    );

    const task = (async () => {
      const bytes = await fetchTlpackBytes(url, {
        checksumSha256: entry.summary.checksum_sha256,
        fetchImpl: options.fetchImpl,
        useCache: options.useCache,
        fileLabel: entry.file,
      });
      const summary = loadLexiconPackBytes(bytes);
      this.mountedPacks.set(summary.pack_id, summary);
      this.userLoadedIds.delete(summary.pack_id);
      return summary;
    })();

    this.inFlight.set(packId, task);
    try {
      return await task;
    } finally {
      this.inFlight.delete(packId);
    }
  }

  /**
   * Fetches and mounts all packs in a given tier (`verified_open` or `local_historical`).
   * In `open` channel mode, `local_historical` is never auto-fetched and returns `[]`.
   */
  async fetchAndMountTier(
    manifest: TlpackManifest,
    tier: tt.LexiconPackTier,
    options: V2PackFetchOptions = {}
  ): Promise<tt.LexiconCompactPackSummary[]> {
    const isOpenOnly = resolveOpenOnlyOption(options);
    if (isOpenOnly && tier === "local_historical") {
      return [];
    }

    const candidates = manifest.packs.filter(
      (entry) =>
        entry.summary.pack_tier === tier &&
        !(isOpenOnly && isLocalPackEntry(entry))
    );

    const results: tt.LexiconCompactPackSummary[] = [];
    for (const entry of candidates) {
      results.push(await this.fetchAndMountPack(entry, options));
    }
    return results;
  }

  /**
   * Progressively mounts packs in priority stages:
   * - Stage 1 (`open-lite`): `core`, `names_taxa`, `regional`
   * - Stage 2 (`open`): `ta_wiktionary`
   * - Stage 3 (`full`, only when `!isOpenOnly && includeLocal`): `local/*` small packs first, `local_terminology` last.
   * Deduplicates concurrent calls (including React StrictMode double mounts).
   */
  async autoMountProgressive(
    options: AutoMountProgressiveOptions = {}
  ): Promise<tt.LexiconCompactPackSummary[]> {
    const isOpenOnly = resolveOpenOnlyOption(options);
    const includeLocal = !isOpenOnly && Boolean(options.includeLocal);
    const scopeKey = `${isOpenOnly ? "open-only" : "full-channel"}:${includeLocal ? "full" : "open"}`;

    const existing = this.progressiveRuns.get(scopeKey);
    if (existing) {
      if (options.onProgress) {
        existing.listeners.add(options.onProgress);
      }
      return existing.promise;
    }

    const listeners = new Set<(progress: ProgressiveMountProgress) => void>();
    if (options.onProgress) {
      listeners.add(options.onProgress);
    }

    const emit = (progress: ProgressiveMountProgress) => {
      for (const listener of listeners) {
        listener(progress);
      }
    };

    const runPromise = (async () => {
      // If upgrading from open -> full while open is still running, wait for open first.
      if (includeLocal) {
        const openRun = this.progressiveRuns.get(
          `${isOpenOnly ? "open-only" : "full-channel"}:open`
        );
        if (openRun) {
          try {
            await openRun.promise;
          } catch {
            // Continue and attempt full plan independently
          }
        }
      }

      const rawManifest =
        options.manifest ??
        (await fetchTlpackManifest({
          baseUrl: options.baseUrl,
          fetchImpl: options.fetchImpl,
          isOpenOnly,
        }));

      if (!rawManifest || rawManifest.packs.length === 0) {
        emit({
          stage: includeLocal ? "full" : "open",
          loadedPacks: 0,
          totalPacks: 0,
          mountedWordEstimate: this.getMountedWordEstimate(),
          done: true,
        });
        return [];
      }

      const plan = buildProgressiveStagePlan(rawManifest, includeLocal, isOpenOnly);
      const totalPacks = plan.length;
      if (totalPacks === 0) {
        emit({
          stage: includeLocal ? "full" : "open",
          loadedPacks: 0,
          totalPacks: 0,
          mountedWordEstimate: this.getMountedWordEstimate(),
          done: true,
        });
        return [];
      }

      const mounted: tt.LexiconCompactPackSummary[] = [];
      let loadedPacks = 0;
      const startLocalEpoch = this.localEpoch;

      for (const step of plan) {
        if (step.stage === "full" && this.localEpoch !== startLocalEpoch) {
          break;
        }
        const summary = await this.fetchAndMountPack(step.entry, {
          baseUrl: options.baseUrl,
          fetchImpl: options.fetchImpl,
          isOpenOnly,
          useCache: options.useCache,
        });
        if (step.stage === "full" && this.localEpoch !== startLocalEpoch) {
          this.unloadPack(summary.pack_id);
          break;
        }
        mounted.push(summary);
        loadedPacks++;
        emit({
          stage: step.stage,
          loadedPacks,
          totalPacks,
          mountedWordEstimate: this.getMountedWordEstimate(),
          lastPackId: summary.pack_id,
          done: loadedPacks === totalPacks,
        });
      }

      return mounted;
    })();

    this.progressiveRuns.set(scopeKey, { promise: runPromise, listeners });
    try {
      return await runPromise;
    } finally {
      this.progressiveRuns.delete(scopeKey);
    }
  }

  /**
   * Mounts raw `.tlpack` bytes directly into the WASM engine.
   */
  mountBytes(
    bytes: Uint8Array,
    source: "remote" | "local-file" = "local-file"
  ): tt.LexiconCompactPackSummary {
    const summary = loadLexiconPackBytes(bytes);
    this.mountedPacks.set(summary.pack_id, summary);
    if (source === "local-file") {
      this.userLoadedIds.add(summary.pack_id);
    } else {
      this.userLoadedIds.delete(summary.pack_id);
    }
    return summary;
  }

  /**
   * Mounts a user-selected `.tlpack` File from local disk 100% client-side (zero upload).
   * Permitted even in `IS_PUBLIC_BETA` because no network fetch occurs.
   */
  async mountLocalFile(file: File): Promise<tt.LexiconCompactPackSummary> {
    const buffer = await file.arrayBuffer();
    return this.mountBytes(new Uint8Array(buffer), "local-file");
  }

  /**
   * Mounts multiple user-selected `.tlpack` files, collecting any per-file validation errors.
   */
  async mountLocalFiles(
    files: FileList | readonly File[]
  ): Promise<V2LocalMountBatchResult> {
    const mounted: tt.LexiconCompactPackSummary[] = [];
    const errors: Array<{ fileName: string; message: string }> = [];
    const list = Array.from(files);
    for (const file of list) {
      try {
        mounted.push(await this.mountLocalFile(file));
      } catch (err: unknown) {
        errors.push({
          fileName: file.name,
          message: err instanceof Error ? err.message : String(err),
        });
      }
    }
    return { mounted, errors };
  }

  /**
   * Unmounts one pack by ID from the Rust WASM runtime registry.
   */
  unloadPack(packId: string): boolean {
    const res = unloadLexiconPack(packId);
    this.mountedPacks.delete(packId);
    this.userLoadedIds.delete(packId);
    return "removed" in res ? res.removed : false;
  }

  /**
   * Unmounts every currently mounted `local_historical` pack and returns the unloaded pack IDs.
   */
  unloadLocalPacks(): string[] {
    this.localEpoch++;
    this.syncFromEngine();
    const unloaded: string[] = [];
    for (const pack of Array.from(this.mountedPacks.values())) {
      if (pack.pack_tier === "local_historical") {
        if (this.unloadPack(pack.pack_id)) {
          unloaded.push(pack.pack_id);
        }
      }
    }
    return unloaded;
  }

  /**
   * Clears all mounted packs from the Rust WASM runtime registry.
   */
  clearAll(): void {
    unloadLexiconPack(null);
    this.mountedPacks.clear();
    this.userLoadedIds.clear();
  }

  /**
   * Resets only the JS-side cache (useful in tests after direct engine calls).
   */
  resetCache(): void {
    this.mountedPacks.clear();
    this.inFlight.clear();
    this.userLoadedIds.clear();
    this.progressiveRuns.clear();
  }
}

export const lexiconV2Manager = new LexiconV2PackManager();
