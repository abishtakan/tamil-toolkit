import { tt } from "./engine";

export const DEFAULT_SOURCE_RECORDS_LIMIT = 25;
export const MAX_SOURCE_RECORDS_LIMIT = 100;
export const MAX_SOURCE_RECORDS_OFFSET = 1_000_000;
export const DEFAULT_BUCKET_CACHE_CAPACITY = 4;
export const HISTORICAL_EXPECTED_TOTAL_RECORDS = 307_243;

export type HistoricalDataStatus = "owner_supplied_unverified";
export type HistoricalRightsStatus = "unresolved";

export interface HistoricalManifestFileEntry {
  file: string;
  rows: number;
  sha256: string;
  bytes: number;
}

export interface HistoricalManifestBucketEntry {
  file: string;
  sha256: string;
  bytes: number;
  records: number;
}

export interface HistoricalLexiconManifest {
  schema_version: 1;
  data_status: HistoricalDataStatus;
  rights_status: HistoricalRightsStatus;
  total_records: number;
  distinct_keys: number;
  files: HistoricalManifestFileEntry[];
  buckets: Record<string, HistoricalManifestBucketEntry>;
}

export interface HistoricalSourceBucketResult {
  query: string;
  normalized_query: string;
  bucket: string;
}

export interface HistoricalSourceRecord {
  source_file: string;
  source_row: number;
  lookup_key: string;
  fields: Record<string, string>;
}

export interface HistoricalBucketData {
  schema_version: 1;
  bucket: string;
  records: HistoricalSourceRecord[];
}

export interface HistoricalSourceLookupResponse {
  query: string;
  normalized_query: string;
  status: "matched" | "not_found";
  data_status: HistoricalDataStatus;
  rights_status: HistoricalRightsStatus;
  total: number;
  offset: number;
  limit: number;
  records: HistoricalSourceRecord[];
}

export type HistoricalSourceErrorKind =
  | "missing_export"
  | "integrity_error"
  | "unsupported_engine"
  | "invalid_query"
  | "engine_error"
  | "network_error"
  | "aborted";

export class HistoricalSourceError extends Error {
  readonly kind: HistoricalSourceErrorKind;
  readonly statusCode?: number;
  readonly url?: string;

  constructor(
    kind: HistoricalSourceErrorKind,
    message: string,
    details?: { statusCode?: number; url?: string; cause?: unknown }
  ) {
    super(message, details?.cause !== undefined ? { cause: details.cause } : undefined);
    this.name = "HistoricalSourceError";
    this.kind = kind;
    this.statusCode = details?.statusCode;
    this.url = details?.url;
  }
}

export type SourceRecordsExecutor = (request: { op: string; input: unknown }) => unknown;

export interface SourceRecordsClientOptions {
  baseUrl?: string;
  execute?: SourceRecordsExecutor;
  fetchImpl?: typeof fetch;
  subtle?: SubtleCrypto;
  cacheCapacity?: number;
}

export interface HistoricalSearchResult {
  manifest: HistoricalLexiconManifest;
  bucketInfo: HistoricalSourceBucketResult;
  response: HistoricalSourceLookupResponse;
  cacheHit: boolean;
  bucketBytes: number;
  bucketSha256: string;
}

export interface SourceRecordsCacheStats {
  size: number;
  capacity: number;
  cachedBuckets: string[];
}

export interface RecordFieldHighlight {
  key: string;
  value: string;
}

export interface ExtractedRecordHighlights {
  definitions: RecordFieldHighlight[];
  transliterations: RecordFieldHighlight[];
  domains: RecordFieldHighlight[];
  inheritedStatuses: RecordFieldHighlight[];
  allFields: RecordFieldHighlight[];
}

const DEFINITION_FIELD_KEYS = [
  "definition_ta",
  "definition_en",
  "definition",
  "meaning_ta",
  "meaning_en",
  "meaning",
  "english_gloss",
  "gloss",
  "english_term",
  "translation",
  "description",
] as const;

const TRANSLITERATION_FIELD_KEYS = [
  "transliteration",
  "romanization",
  "iso_15919",
  "ipa",
  "transliterated_ta",
  "pronunciation",
  "phonetic",
] as const;

const DOMAIN_FIELD_KEYS = [
  "domain",
  "domains",
  "category",
  "subject",
  "pos",
  "part_of_speech",
  "scientific_name",
  "taxon",
  "literary_source",
  "relation_type",
  "target_headword_ta",
  "region",
  "dialect",
] as const;

const INHERITED_STATUS_KEY_RE =
  /(^|_)(verified|is_verified|status|verification_status|reviewed|approved|confidence)(_|$)/i;

const SHA256_HEX_RE = /^[0-9a-f]{64}$/i;
const BUCKET_HEX_RE = /^[0-9a-f]{2}$/;
const SAFE_FILENAME_RE = /^[A-Za-z0-9._-]+$/;

export function normalizeBaseUrl(baseUrl?: string): string {
  const raw = baseUrl ?? (import.meta.env.BASE_URL || "/");
  if (!raw) return "/";
  return raw.endsWith("/") ? raw : `${raw}/`;
}

export function isSafeManifestFilename(name: unknown): name is string {
  return (
    typeof name === "string" &&
    name.length > 0 &&
    !name.includes("..") &&
    !name.includes("/") &&
    !name.includes("\\") &&
    SAFE_FILENAME_RE.test(name)
  );
}

function isNonNegativeSafeInt(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function isPlainRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function classifyEngineError(err: unknown): HistoricalSourceError {
  if (err instanceof HistoricalSourceError) return err;
  const message = err instanceof Error ? err.message : String(err);
  const lower = message.toLowerCase();
  if (
    lower.includes("unsupported operation") ||
    lower.includes("unknown operation") ||
    lower.includes("not implemented")
  ) {
    return new HistoricalSourceError("unsupported_engine", message, { cause: err });
  }
  if (lower.includes("lexicon source: invalid query")) {
    return new HistoricalSourceError("invalid_query", message, { cause: err });
  }
  return new HistoricalSourceError("engine_error", message, { cause: err });
}

export async function sha256Hex(
  buffer: ArrayBuffer,
  subtle?: SubtleCrypto
): Promise<string> {
  const cryptoSubtle = subtle ?? globalThis.crypto?.subtle;
  if (!cryptoSubtle || typeof cryptoSubtle.digest !== "function") {
    throw new HistoricalSourceError(
      "integrity_error",
      "Web Crypto API (crypto.subtle.digest) is unavailable to verify historical bundle hashes."
    );
  }
  const digest = await cryptoSubtle.digest("SHA-256", buffer);
  const bytes = new Uint8Array(digest);
  let hex = "";
  for (let i = 0; i < bytes.length; i++) {
    hex += bytes[i].toString(16).padStart(2, "0");
  }
  return hex;
}

export function validateManifest(raw: unknown, sourceUrl: string): HistoricalLexiconManifest {
  if (!isPlainRecord(raw)) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Invalid historical manifest shape at ${sourceUrl}: expected JSON object.`,
      { url: sourceUrl }
    );
  }

  if (raw.schema_version !== 1) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Unsupported historical manifest schema_version at ${sourceUrl}.`,
      { url: sourceUrl }
    );
  }

  if (raw.data_status !== "owner_supplied_unverified" || raw.rights_status !== "unresolved") {
    throw new HistoricalSourceError(
      "integrity_error",
      `Historical manifest at ${sourceUrl} has unexpected data/rights status.`,
      { url: sourceUrl }
    );
  }

  if (!isNonNegativeSafeInt(raw.total_records) || !isNonNegativeSafeInt(raw.distinct_keys)) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Historical manifest at ${sourceUrl} is missing valid record or distinct_keys counts.`,
      { url: sourceUrl }
    );
  }

  if (!Array.isArray(raw.files)) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Historical manifest at ${sourceUrl} is missing files inventory.`,
      { url: sourceUrl }
    );
  }

  const files: HistoricalManifestFileEntry[] = raw.files.map((entry, idx) => {
    if (
      !isPlainRecord(entry) ||
      !isSafeManifestFilename(entry.file) ||
      !isNonNegativeSafeInt(entry.rows) ||
      typeof entry.sha256 !== "string" ||
      !SHA256_HEX_RE.test(entry.sha256) ||
      !isNonNegativeSafeInt(entry.bytes)
    ) {
      throw new HistoricalSourceError(
        "integrity_error",
        `Historical manifest files[${idx}] is malformed at ${sourceUrl}.`,
        { url: sourceUrl }
      );
    }
    return {
      file: entry.file,
      rows: entry.rows,
      sha256: entry.sha256.toLowerCase(),
      bytes: entry.bytes,
    };
  });

  if (!isPlainRecord(raw.buckets)) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Historical manifest at ${sourceUrl} is missing buckets map.`,
      { url: sourceUrl }
    );
  }

  const buckets: Record<string, HistoricalManifestBucketEntry> = {};
  for (const [bucketKey, entry] of Object.entries(raw.buckets)) {
    if (
      !BUCKET_HEX_RE.test(bucketKey) ||
      !isPlainRecord(entry) ||
      !isSafeManifestFilename(entry.file) ||
      typeof entry.sha256 !== "string" ||
      !SHA256_HEX_RE.test(entry.sha256) ||
      !isNonNegativeSafeInt(entry.bytes) ||
      !isNonNegativeSafeInt(entry.records)
    ) {
      throw new HistoricalSourceError(
        "integrity_error",
        `Historical manifest bucket entry '${bucketKey}' is malformed at ${sourceUrl}.`,
        { url: sourceUrl }
      );
    }
    buckets[bucketKey] = {
      file: entry.file,
      sha256: entry.sha256.toLowerCase(),
      bytes: entry.bytes,
      records: entry.records,
    };
  }

  return {
    schema_version: 1,
    data_status: "owner_supplied_unverified",
    rights_status: "unresolved",
    total_records: raw.total_records,
    distinct_keys: raw.distinct_keys,
    files,
    buckets,
  };
}

export function validateBucketPayload(
  raw: unknown,
  expectedBucket: string,
  sourceUrl: string
): HistoricalBucketData {
  if (
    !isPlainRecord(raw) ||
    raw.schema_version !== 1 ||
    raw.bucket !== expectedBucket ||
    !Array.isArray(raw.records)
  ) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Invalid historical bucket payload for '${expectedBucket}' at ${sourceUrl}.`,
      { url: sourceUrl }
    );
  }
  return {
    schema_version: 1,
    bucket: raw.bucket,
    records: raw.records as HistoricalSourceRecord[],
  };
}

async function fetchVerifiedJsonAsset(params: {
  url: string;
  fetchImpl: typeof fetch;
  subtle?: SubtleCrypto;
  signal?: AbortSignal;
  expectedBytes?: number;
  expectedSha256?: string;
  cache?: RequestCache;
}): Promise<unknown> {
  const { url, fetchImpl, subtle, signal, expectedBytes, expectedSha256 } = params;

  if (signal?.aborted) {
    throw new HistoricalSourceError("aborted", "Request cancelled.", { url });
  }

  let response: Response;
  try {
    response = await fetchImpl(url, { signal, cache: params.cache });
  } catch (err: unknown) {
    if (
      signal?.aborted ||
      (err instanceof Error && err.name === "AbortError")
    ) {
      throw new HistoricalSourceError("aborted", "Request cancelled.", { url, cause: err });
    }
    const msg = err instanceof Error ? err.message : String(err);
    throw new HistoricalSourceError(
      "network_error",
      `Failed to fetch historical asset ${url}: ${msg}`,
      { url, cause: err }
    );
  }

  if (!response.ok) {
    throw new HistoricalSourceError(
      "missing_export",
      `Historical source asset not found (${response.status}): ${url}`,
      { statusCode: response.status, url }
    );
  }

  const contentType = response.headers?.get?.("content-type")?.toLowerCase() ?? "";
  if (contentType.includes("text/html")) {
    throw new HistoricalSourceError(
      "missing_export",
      `Historical source asset missing (server returned HTML fallback): ${url}`,
      { statusCode: response.status, url }
    );
  }

  let buffer: ArrayBuffer;
  try {
    buffer = await response.arrayBuffer();
  } catch (err: unknown) {
    if (signal?.aborted || (err instanceof Error && err.name === "AbortError")) {
      throw new HistoricalSourceError("aborted", "Request cancelled.", { url, cause: err });
    }
    throw new HistoricalSourceError(
      "network_error",
      `Failed reading historical asset body from ${url}.`,
      { url, cause: err }
    );
  }

  if (signal?.aborted) {
    throw new HistoricalSourceError("aborted", "Request cancelled.", { url });
  }

  if (expectedBytes !== undefined && buffer.byteLength !== expectedBytes) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Byte size mismatch for ${url}: expected ${expectedBytes} bytes, received ${buffer.byteLength} bytes.`,
      { url }
    );
  }

  if (expectedSha256 !== undefined) {
    const actualSha256 = await sha256Hex(buffer, subtle);
    if (actualSha256 !== expectedSha256.toLowerCase()) {
      throw new HistoricalSourceError(
        "integrity_error",
        `SHA-256 verification failed for ${url}: expected ${expectedSha256.toLowerCase()}, got ${actualSha256}.`,
        { url }
      );
    }
  }

  if (signal?.aborted) {
    throw new HistoricalSourceError("aborted", "Request cancelled.", { url });
  }

  let text: string;
  try {
    text = new TextDecoder("utf-8", { fatal: true }).decode(buffer);
  } catch (err: unknown) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Invalid UTF-8 in historical asset ${url}.`,
      { url, cause: err }
    );
  }

  const trimmed = text.trimStart();
  if (trimmed.startsWith("<")) {
    throw new HistoricalSourceError(
      "missing_export",
      `Historical source asset missing (HTML document returned): ${url}`,
      { url }
    );
  }

  try {
    return JSON.parse(text);
  } catch (err: unknown) {
    throw new HistoricalSourceError(
      "integrity_error",
      `Malformed JSON in historical asset ${url}.`,
      { url, cause: err }
    );
  }
}

export function extractRecordHighlights(
  fields: Record<string, string>
): ExtractedRecordHighlights {
  const definitions: RecordFieldHighlight[] = [];
  const transliterations: RecordFieldHighlight[] = [];
  const domains: RecordFieldHighlight[] = [];
  const inheritedStatuses: RecordFieldHighlight[] = [];
  const usedKeys = new Set<string>();

  for (const key of DEFINITION_FIELD_KEYS) {
    const val = fields[key];
    if (typeof val === "string" && val !== "") {
      definitions.push({ key, value: val });
      usedKeys.add(key);
    }
  }

  for (const key of TRANSLITERATION_FIELD_KEYS) {
    const val = fields[key];
    if (typeof val === "string" && val !== "" && !usedKeys.has(key)) {
      transliterations.push({ key, value: val });
      usedKeys.add(key);
    }
  }

  for (const key of DOMAIN_FIELD_KEYS) {
    const val = fields[key];
    if (typeof val === "string" && val !== "" && !usedKeys.has(key)) {
      domains.push({ key, value: val });
      usedKeys.add(key);
    }
  }

  for (const [key, val] of Object.entries(fields)) {
    if (typeof val === "string" && val !== "" && INHERITED_STATUS_KEY_RE.test(key)) {
      inheritedStatuses.push({ key, value: val });
    }
  }

  const allFields = Object.entries(fields).map(([key, value]) => ({
    key,
    value: typeof value === "string" ? value : String(value ?? ""),
  }));

  return {
    definitions,
    transliterations,
    domains,
    inheritedStatuses,
    allFields,
  };
}

export function createSourceRecordsClient(options?: SourceRecordsClientOptions) {
  const baseUrl = normalizeBaseUrl(options?.baseUrl);
  const execute: SourceRecordsExecutor =
    options?.execute ?? ((request) => tt.execute(request));
  const fetchImpl: typeof fetch =
    options?.fetchImpl ?? ((input, init) => globalThis.fetch(input, init));
  const subtle = options?.subtle;
  const cacheCapacity = Math.max(
    1,
    Math.floor(options?.cacheCapacity ?? DEFAULT_BUCKET_CACHE_CAPACITY)
  );

  let manifestCache: HistoricalLexiconManifest | null = null;
  let manifestPromise: Promise<HistoricalLexiconManifest> | null = null;
  let manifestGeneration = 0;
  const bucketCache = new Map<string, HistoricalBucketData>();

  function waitForManifest(
    pending: Promise<HistoricalLexiconManifest>, signal?: AbortSignal
  ): Promise<HistoricalLexiconManifest> {
    if (!signal) return pending;
    return new Promise((resolve, reject) => {
      const abort = () => reject(new HistoricalSourceError("aborted", "Request cancelled."));
      if (signal.aborted) { abort(); return; }
      signal.addEventListener("abort", abort, { once: true });
      pending.then(
        value => { signal.removeEventListener("abort", abort); resolve(value); },
        error => { signal.removeEventListener("abort", abort); reject(error); }
      );
    });
  }

  async function loadManifest(opts?: {
    forceReload?: boolean;
    signal?: AbortSignal;
  }): Promise<HistoricalLexiconManifest> {
    if (opts?.signal?.aborted) {
      throw new HistoricalSourceError("aborted", "Request cancelled.");
    }
    if (!opts?.forceReload && manifestCache) {
      return manifestCache;
    }
    if (!opts?.forceReload && manifestPromise) {
      return waitForManifest(manifestPromise, opts?.signal);
    }

    const manifestUrl = `${baseUrl}historical-lexicon/manifest.json`;
    const generation = ++manifestGeneration;
    const run: Promise<HistoricalLexiconManifest> = (async () => {
      const raw = await fetchVerifiedJsonAsset({
        url: manifestUrl,
        fetchImpl,
        subtle,
        // This fetch is shared: an individual waiter's cancellation must not
        // abort other callers (including React StrictMode's second mount).
        cache: opts?.forceReload ? "no-store" : undefined,
      });
      const validated = validateManifest(raw, manifestUrl);
      if (generation === manifestGeneration) {
        manifestCache = validated;
      } else if (manifestPromise) {
        return manifestPromise;
      } else if (manifestCache) {
        return manifestCache;
      }
      return validated;
    })();

    manifestPromise = run;
    const clearPending = () => {
      if (manifestPromise === run) {
        manifestPromise = null;
      }
    };
    void run.then(clearPending, clearPending);
    return waitForManifest(run, opts?.signal);
  }

  function resolveBucket(query: string): HistoricalSourceBucketResult {
    let raw: unknown;
    try {
      raw = execute({ op: "lexicon_source_bucket", input: query });
    } catch (err: unknown) {
      throw classifyEngineError(err);
    }

    if (
      !isPlainRecord(raw) ||
      typeof raw.query !== "string" ||
      typeof raw.normalized_query !== "string" ||
      typeof raw.bucket !== "string" ||
      !BUCKET_HEX_RE.test(raw.bucket)
    ) {
      throw new HistoricalSourceError(
        "engine_error",
        "Unexpected response shape from lexicon_source_bucket."
      );
    }

    return {
      query: raw.query,
      normalized_query: raw.normalized_query,
      bucket: raw.bucket,
    };
  }

  async function loadBucket(
    bucketId: string,
    manifest: HistoricalLexiconManifest,
    signal?: AbortSignal
  ): Promise<{
    data: HistoricalBucketData;
    cacheHit: boolean;
    entry: HistoricalManifestBucketEntry;
  }> {
    const entry = manifest.buckets[bucketId];
    if (!entry) {
      throw new HistoricalSourceError(
        "missing_export",
        `Bucket '${bucketId}' is not present in historical-lexicon/manifest.json.`
      );
    }

    const cacheKey = `${bucketId}:${entry.sha256}:${entry.bytes}`;
    const existing = bucketCache.get(cacheKey);
    if (existing) {
      bucketCache.delete(cacheKey);
      bucketCache.set(cacheKey, existing);
      return { data: existing, cacheHit: true, entry };
    }

    const bucketUrl = `${baseUrl}historical-lexicon/${entry.file}`;
    const raw = await fetchVerifiedJsonAsset({
      url: bucketUrl,
      fetchImpl,
      subtle,
      signal,
      expectedBytes: entry.bytes,
      expectedSha256: entry.sha256,
    });
    const validated = validateBucketPayload(raw, bucketId, bucketUrl);

    if (bucketCache.size >= cacheCapacity) {
      const oldestKey = bucketCache.keys().next().value;
      if (oldestKey !== undefined) {
        bucketCache.delete(oldestKey);
      }
    }
    bucketCache.set(cacheKey, validated);

    return { data: validated, cacheHit: false, entry };
  }

  function lookupInBucket(params: {
    query: string;
    bucket: HistoricalBucketData;
    offset: number;
    limit: number;
  }): HistoricalSourceLookupResponse {
    let raw: unknown;
    try {
      raw = execute({
        op: "lexicon_source_lookup",
        input: {
          query: params.query,
          bucket: params.bucket,
          offset: params.offset,
          limit: params.limit,
        },
      });
    } catch (err: unknown) {
      throw classifyEngineError(err);
    }

    if (
      !isPlainRecord(raw) ||
      typeof raw.query !== "string" ||
      typeof raw.normalized_query !== "string" ||
      (raw.status !== "matched" && raw.status !== "not_found") ||
      raw.data_status !== "owner_supplied_unverified" ||
      raw.rights_status !== "unresolved" ||
      !isNonNegativeSafeInt(raw.total) ||
      !isNonNegativeSafeInt(raw.offset) ||
      !isNonNegativeSafeInt(raw.limit) ||
      !Array.isArray(raw.records)
    ) {
      throw new HistoricalSourceError(
        "engine_error",
        "Unexpected response shape from lexicon_source_lookup."
      );
    }

    return {
      query: raw.query,
      normalized_query: raw.normalized_query,
      status: raw.status,
      data_status: raw.data_status,
      rights_status: raw.rights_status,
      total: raw.total,
      offset: raw.offset,
      limit: raw.limit,
      records: raw.records as HistoricalSourceRecord[],
    };
  }

  async function search(params: {
    query: string;
    offset?: number;
    limit?: number;
    signal?: AbortSignal;
  }): Promise<HistoricalSearchResult> {
    const offset = params.offset ?? 0;
    const limit = params.limit ?? DEFAULT_SOURCE_RECORDS_LIMIT;

    const bucketInfo = resolveBucket(params.query);
    const manifest = await loadManifest({ signal: params.signal });
    if (params.signal?.aborted) {
      throw new HistoricalSourceError("aborted", "Request cancelled.");
    }

    const { data, cacheHit, entry } = await loadBucket(
      bucketInfo.bucket,
      manifest,
      params.signal
    );
    if (params.signal?.aborted) {
      throw new HistoricalSourceError("aborted", "Request cancelled.");
    }

    const response = lookupInBucket({
      query: params.query,
      bucket: data,
      offset,
      limit,
    });

    return {
      manifest,
      bucketInfo,
      response,
      cacheHit,
      bucketBytes: entry.bytes,
      bucketSha256: entry.sha256,
    };
  }

  function getCacheStats(): SourceRecordsCacheStats {
    return {
      size: bucketCache.size,
      capacity: cacheCapacity,
      cachedBuckets: Array.from(bucketCache.keys()).map((k) => k.split(":")[0]),
    };
  }

  function clearCache(): void {
    manifestGeneration += 1;
    manifestCache = null;
    manifestPromise = null;
    bucketCache.clear();
  }

  return {
    loadManifest,
    resolveBucket,
    loadBucket,
    lookupInBucket,
    search,
    getCacheStats,
    clearCache,
  };
}

export type SourceRecordsClient = ReturnType<typeof createSourceRecordsClient>;
