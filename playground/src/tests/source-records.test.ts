import { describe, it, expect } from "vitest";
import { webcrypto } from "node:crypto";
import {
  DEFAULT_BUCKET_CACHE_CAPACITY,
  DEFAULT_SOURCE_RECORDS_LIMIT,
  HistoricalBucketData,
  HistoricalLexiconManifest,
  HistoricalSourceError,
  HistoricalSourceRecord,
  createSourceRecordsClient,
  extractRecordHighlights,
} from "../lib/source-records";

const subtle = (globalThis.crypto?.subtle ?? webcrypto.subtle) as SubtleCrypto;

async function sha256HexNode(bytes: Uint8Array): Promise<string> {
  const copy = new Uint8Array(bytes.byteLength);
  copy.set(bytes);
  const digest = await subtle.digest("SHA-256", copy.buffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function makeResponse(
  body: string | Uint8Array,
  init?: { status?: number; statusText?: string; contentType?: string }
): Response {
  const bytes =
    typeof body === "string" ? new TextEncoder().encode(body) : body;
  const status = init?.status ?? 200;
  const headers = new Headers();
  if (init?.contentType) {
    headers.set("content-type", init.contentType);
  } else {
    headers.set("content-type", "application/json; charset=utf-8");
  }
  return new Response(bytes as unknown as BodyInit, {
    status,
    statusText: init?.statusText ?? (status === 200 ? "OK" : "Not Found"),
    headers,
  });
}

async function buildFixtureBundle(
  bucketPayloads: Record<string, HistoricalBucketData>,
  overrides?: Partial<HistoricalLexiconManifest>
): Promise<{
  manifest: HistoricalLexiconManifest;
  manifestJson: string;
  bucketBytesByFile: Record<string, Uint8Array>;
}> {
  const bucketBytesByFile: Record<string, Uint8Array> = {};
  const buckets: HistoricalLexiconManifest["buckets"] = {};

  for (const [bucketId, payload] of Object.entries(bucketPayloads)) {
    const file = `${bucketId}.json`;
    const encoded = new TextEncoder().encode(JSON.stringify(payload));
    const sha256 = await sha256HexNode(encoded);
    bucketBytesByFile[file] = encoded;
    buckets[bucketId] = {
      file,
      sha256,
      bytes: encoded.byteLength,
      records: payload.records.length,
    };
  }

  const manifest: HistoricalLexiconManifest = {
    schema_version: 1,
    data_status: "owner_supplied_unverified",
    rights_status: "unresolved",
    total_records: 307243,
    distinct_keys: 177606,
    files: [
      {
        file: "primary_lemmas.csv",
        rows: 44229,
        sha256: "a".repeat(64),
        bytes: 123456,
      },
    ],
    buckets,
    ...overrides,
  };

  return {
    manifest,
    manifestJson: JSON.stringify(manifest),
    bucketBytesByFile,
  };
}

function createFixtureExecutor(bucketByQuery: Record<string, string>) {
  return (request: { op: string; input: unknown }) => {
    if (request.op === "lexicon_source_bucket") {
      if (typeof request.input !== "string" || request.input.length === 0) {
        throw new Error("lexicon source: invalid query");
      }
      const query = request.input;
      const normalized = query.normalize("NFC");
      const bucket = bucketByQuery[normalized] ?? "ab";
      return {
        query,
        normalized_query: normalized,
        bucket,
      };
    }

    if (request.op === "lexicon_source_lookup") {
      const input = request.input as {
        query: string;
        bucket: HistoricalBucketData;
        offset: number;
        limit: number;
      };
      const normalized = input.query.normalize("NFC");
      const matching = input.bucket.records.filter(
        (r) => r.lookup_key === normalized
      );
      const page = matching.slice(input.offset, input.offset + input.limit);
      return {
        query: input.query,
        normalized_query: normalized,
        status: matching.length > 0 ? "matched" : "not_found",
        data_status: "owner_supplied_unverified",
        rights_status: "unresolved",
        total: matching.length,
        offset: input.offset,
        limit: input.limit,
        records: page,
      };
    }

    throw new Error(`unsupported operation: ${request.op}`);
  };
}

describe("Historical source records client (DI unit tests with fixture executor)", () => {
  it("keeps shared manifest fetch alive when one waiter aborts", async () => {
    const bundle = await buildFixtureBundle({});
    let finish!: (response: Response) => void;
    let fetchSignal: AbortSignal | null | undefined;
    const client = createSourceRecordsClient({
      fetchImpl: async (_input, init) => {
        fetchSignal = init?.signal;
        return new Promise<Response>(resolve => { finish = resolve; });
      },
    });
    const first = new AbortController();
    const cancelled = client.loadManifest({ signal: first.signal });
    const survivor = client.loadManifest();
    const rejected = expect(cancelled).rejects.toMatchObject({ kind: "aborted" });
    first.abort();
    await rejected;
    expect(fetchSignal).toBeUndefined();
    finish(makeResponse(bundle.manifestJson));
    await expect(survivor).resolves.toMatchObject({ total_records: 307243 });
  });

  it("forced reload bypasses HTTP cache and cannot be replaced by an older fetch", async () => {
    const oldBundle = await buildFixtureBundle({}, { distinct_keys: 1 });
    const newBundle = await buildFixtureBundle({}, { distinct_keys: 2 });
    const requests: { resolve: (response: Response) => void; cache?: RequestCache }[] = [];
    const client = createSourceRecordsClient({ fetchImpl: async (_input, init) =>
      new Promise<Response>(resolve => requests.push({ resolve, cache: init?.cache })) });
    const old = client.loadManifest();
    const fresh = client.loadManifest({ forceReload: true });
    expect(requests[1].cache).toBe("no-store");
    requests[1].resolve(makeResponse(newBundle.manifestJson));
    expect((await fresh).distinct_keys).toBe(2);
    requests[0].resolve(makeResponse(oldBundle.manifestJson));
    expect((await old).distinct_keys).toBe(2);
    expect((await client.loadManifest()).distinct_keys).toBe(2);
  });

  it("rejects manifest counts that exceed safe JSON integers", async () => {
    const bundle = await buildFixtureBundle({}, { distinct_keys: 1e20 });
    const client = createSourceRecordsClient({ fetchImpl: async () => makeResponse(bundle.manifestJson) });
    await expect(client.loadManifest()).rejects.toMatchObject({ kind: "integrity_error" });
  });

  it("overlapping reloads wait for the latest generation instead of a pre-reload cache", async () => {
    const prior = await buildFixtureBundle({}, { distinct_keys: 1 });
    const latest = await buildFixtureBundle({}, { distinct_keys: 2 });
    const requests: ((response: Response) => void)[] = [];
    const client = createSourceRecordsClient({ fetchImpl: async () =>
      new Promise<Response>(resolve => requests.push(resolve)) });
    const initial = client.loadManifest();
    requests[0](makeResponse(prior.manifestJson));
    await initial;
    const olderReload = client.loadManifest({ forceReload: true });
    const newerReload = client.loadManifest({ forceReload: true });
    requests[1](makeResponse(prior.manifestJson));
    requests[2](makeResponse(latest.manifestJson));
    expect((await olderReload).distinct_keys).toBe(2);
    expect((await newerReload).distinct_keys).toBe(2);
  });

  it("fetches manifest and bucket, verifies SHA-256 + bytes via crypto.subtle, and paginates with bounded cache", async () => {
    const queryWord = "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD";
    const records: HistoricalSourceRecord[] = Array.from(
      { length: 60 },
      (_, i) => ({
        source_file: "primary_meanings.csv",
        source_row: i + 1,
        lookup_key: queryWord,
        fields: {
          headword_ta: queryWord,
          definition_en: `Meaning ${i + 1}`,
          status: "verified",
          empty_col: "",
        },
      })
    );

    const bundle = await buildFixtureBundle({
      ab: {
        schema_version: 1,
        bucket: "ab",
        records,
      },
    });

    const fetchedUrls: string[] = [];
    const fetchMock: typeof fetch = async (input) => {
      const url = String(input);
      fetchedUrls.push(url);
      if (url === "/app/historical-lexicon/manifest.json") {
        return makeResponse(bundle.manifestJson);
      }
      if (url === "/app/historical-lexicon/ab.json") {
        return makeResponse(bundle.bucketBytesByFile["ab.json"]);
      }
      return makeResponse("Not found", { status: 404, contentType: "text/plain" });
    };

    const client = createSourceRecordsClient({
      baseUrl: "/app",
      execute: createFixtureExecutor({ [queryWord]: "ab" }),
      fetchImpl: fetchMock,
      subtle,
    });

    // Page 1 (offset 0, limit 25)
    const page1 = await client.search({ query: queryWord, offset: 0 });
    expect(page1.manifest.total_records).toBe(307243);
    expect(page1.manifest.distinct_keys).toBe(177606);
    expect(page1.response.status).toBe("matched");
    expect(page1.response.data_status).toBe("owner_supplied_unverified");
    expect(page1.response.rights_status).toBe("unresolved");
    expect(page1.response.total).toBe(60);
    expect(page1.response.limit).toBe(DEFAULT_SOURCE_RECORDS_LIMIT);
    expect(page1.response.records).toHaveLength(25);
    expect(page1.response.records[0].source_row).toBe(1);
    expect(page1.response.records[24].source_row).toBe(25);
    expect(page1.cacheHit).toBe(false);
    expect(fetchedUrls).toEqual([
      "/app/historical-lexicon/manifest.json",
      "/app/historical-lexicon/ab.json",
    ]);

    // Page 2 (offset 25) reuses cached bucket and cached manifest
    const page2 = await client.search({ query: queryWord, offset: 25 });
    expect(page2.cacheHit).toBe(true);
    expect(page2.response.records).toHaveLength(25);
    expect(page2.response.records[0].source_row).toBe(26);
    expect(page2.response.records[24].source_row).toBe(50);
    expect(fetchedUrls).toHaveLength(2);

    // Page 3 (offset 50) returns remaining 10 rows
    const page3 = await client.search({ query: queryWord, offset: 50 });
    expect(page3.cacheHit).toBe(true);
    expect(page3.response.records).toHaveLength(10);
    expect(page3.response.records[0].source_row).toBe(51);
    expect(page3.response.records[9].source_row).toBe(60);
    expect(fetchedUrls).toHaveLength(2);
  });

  it("rejects SHA-256 hash mismatch before JSON.parse", async () => {
    const queryWord = "\u0B85\u0BB1\u0BAE\u0BCD";
    const bundle = await buildFixtureBundle({
      cd: {
        schema_version: 1,
        bucket: "cd",
        records: [
          {
            source_file: "primary_lemmas.csv",
            source_row: 1,
            lookup_key: queryWord,
            fields: { headword_ta: queryWord },
          },
        ],
      },
    });

    // Replace bucket body with same-byte-length invalid JSON so only hash fails,
    // proving crypto.subtle SHA-256 verification runs prior to JSON.parse.
    const expectedLen = bundle.manifest.buckets["cd"].bytes;
    const tamperedBytes = new Uint8Array(expectedLen).fill(0x7b); // "{{{..."

    const client = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ [queryWord]: "cd" }),
      fetchImpl: async (input) => {
        const url = String(input);
        if (url.endsWith("manifest.json")) return makeResponse(bundle.manifestJson);
        return makeResponse(tamperedBytes);
      },
      subtle,
    });

    await expect(client.search({ query: queryWord })).rejects.toMatchObject({
      name: "HistoricalSourceError",
      kind: "integrity_error",
    });

    try {
      await client.search({ query: queryWord });
    } catch (err) {
      expect(err).toBeInstanceOf(HistoricalSourceError);
      expect((err as HistoricalSourceError).message).toContain("SHA-256 verification failed");
    }
  });

  it("rejects byte size mismatch before JSON.parse", async () => {
    const queryWord = "\u0BAE\u0BB0\u0BAE\u0BCD";
    const bundle = await buildFixtureBundle({
      ef: {
        schema_version: 1,
        bucket: "ef",
        records: [],
      },
    });

    const truncatedBytes = bundle.bucketBytesByFile["ef.json"].slice(0, 5);
    const client = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ [queryWord]: "ef" }),
      fetchImpl: async (input) => {
        const url = String(input);
        if (url.endsWith("manifest.json")) return makeResponse(bundle.manifestJson);
        return makeResponse(truncatedBytes);
      },
      subtle,
    });

    await expect(client.search({ query: queryWord })).rejects.toMatchObject({
      kind: "integrity_error",
    });
  });

  it("distinguishes missing export assets (404 / HTML fallback) from verified not_found lookup results", async () => {
    const queryWord = "\u0B95\u0B9F\u0BB2\u0BCD";

    // Case 1: missing manifest.json (404)
    const missingManifestClient = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ [queryWord]: "01" }),
      fetchImpl: async () =>
        makeResponse("Not Found", { status: 404, contentType: "text/plain" }),
      subtle,
    });
    await expect(missingManifestClient.search({ query: queryWord })).rejects.toMatchObject({
      kind: "missing_export",
      statusCode: 404,
    });

    // Case 2: missing bucket JSON returning SPA HTML fallback with 200 OK
    const bundle = await buildFixtureBundle({
      "01": {
        schema_version: 1,
        bucket: "01",
        records: [],
      },
    });
    const htmlFallbackClient = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ [queryWord]: "01" }),
      fetchImpl: async (input) => {
        if (String(input).endsWith("manifest.json")) {
          return makeResponse(bundle.manifestJson);
        }
        return makeResponse("<!doctype html><html></html>", {
          status: 200,
          contentType: "text/html",
        });
      },
      subtle,
    });
    await expect(htmlFallbackClient.search({ query: queryWord })).rejects.toMatchObject({
      kind: "missing_export",
    });

    // Case 3: verified bucket with 0 matches -> not_found status, not an error
    const verifiedEmptyClient = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ [queryWord]: "01" }),
      fetchImpl: async (input) => {
        if (String(input).endsWith("manifest.json")) {
          return makeResponse(bundle.manifestJson);
        }
        return makeResponse(bundle.bucketBytesByFile["01.json"]);
      },
      subtle,
    });
    const emptyResult = await verifiedEmptyClient.search({ query: queryWord });
    expect(emptyResult.response.status).toBe("not_found");
    expect(emptyResult.response.total).toBe(0);
    expect(emptyResult.response.records).toEqual([]);
  });

  it("bounds bucket memory cache to 4 buckets using LRU eviction", async () => {
    const words = ["w1", "w2", "w3", "w4", "w5"];
    const bucketIds = ["01", "02", "03", "04", "05"];
    const payloads: Record<string, HistoricalBucketData> = {};
    const mapping: Record<string, string> = {};

    words.forEach((w, idx) => {
      const b = bucketIds[idx];
      mapping[w] = b;
      payloads[b] = {
        schema_version: 1,
        bucket: b,
        records: [
          {
            source_file: "primary_lemmas.csv",
            source_row: idx + 1,
            lookup_key: w,
            fields: { headword_ta: w },
          },
        ],
      };
    });

    const bundle = await buildFixtureBundle(payloads);
    const bucketFetches: string[] = [];

    const client = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor(mapping),
      cacheCapacity: DEFAULT_BUCKET_CACHE_CAPACITY,
      fetchImpl: async (input) => {
        const url = String(input);
        if (url.endsWith("manifest.json")) return makeResponse(bundle.manifestJson);
        const file = url.split("/").pop()!;
        bucketFetches.push(file);
        return makeResponse(bundle.bucketBytesByFile[file]);
      },
      subtle,
    });

    for (const w of words.slice(0, 4)) {
      await client.search({ query: w });
    }
    expect(client.getCacheStats()).toEqual({
      size: 4,
      capacity: 4,
      cachedBuckets: ["01", "02", "03", "04"],
    });

    // Access w1 again to refresh 01 in LRU, then fetch w5 -> evicts 02 (LRU)
    const refreshW1 = await client.search({ query: "w1" });
    expect(refreshW1.cacheHit).toBe(true);
    await client.search({ query: "w5" });
    expect(client.getCacheStats().size).toBe(4);
    expect(client.getCacheStats().cachedBuckets).toEqual(["03", "04", "01", "05"]);

    // Querying w2 again must re-fetch 02.json
    const refetchedW2 = await client.search({ query: "w2" });
    expect(refetchedW2.cacheHit).toBe(false);
    expect(bucketFetches).toEqual([
      "01.json",
      "02.json",
      "03.json",
      "04.json",
      "05.json",
      "02.json",
    ]);
  });

  it("cancels stale requests via AbortSignal and classifies engine errors cleanly", async () => {
    const bundle = await buildFixtureBundle({
      aa: { schema_version: 1, bucket: "aa", records: [] },
    });

    const controller = new AbortController();
    const abortingClient = createSourceRecordsClient({
      baseUrl: "/",
      execute: createFixtureExecutor({ test: "aa" }),
      fetchImpl: async (_input, init) => {
        controller.abort();
        if (init?.signal?.aborted) {
          throw new DOMException("Aborted", "AbortError");
        }
        return makeResponse(bundle.manifestJson);
      },
      subtle,
    });

    await expect(
      abortingClient.search({ query: "test", signal: controller.signal })
    ).rejects.toMatchObject({
      kind: "aborted",
    });

    const unsupportedClient = createSourceRecordsClient({
      baseUrl: "/",
      execute: () => {
        throw new Error("unsupported operation: lexicon_source_bucket");
      },
      fetchImpl: async () => makeResponse(bundle.manifestJson),
      subtle,
    });

    await expect(unsupportedClient.search({ query: "test" })).rejects.toMatchObject({
      kind: "unsupported_engine",
    });
  });

  it("extracts definitions, transliteration, domain, and explicitly isolates inherited status cells", () => {
    const highlights = extractRecordHighlights({
      headword_ta: "\u0BA4\u0BAE\u0BBF\u0BB4\u0BCD",
      definition_en: "Tamil language",
      transliteration: "tami\u1E3B",
      domain: "linguistics",
      verified: "true",
      status: "verified",
      notes: "",
    });

    expect(highlights.definitions).toEqual([
      { key: "definition_en", value: "Tamil language" },
    ]);
    expect(highlights.transliterations).toEqual([
      { key: "transliteration", value: "tami\u1E3B" },
    ]);
    expect(highlights.domains).toEqual([
      { key: "domain", value: "linguistics" },
    ]);
    expect(highlights.inheritedStatuses).toEqual([
      { key: "verified", value: "true" },
      { key: "status", value: "verified" },
    ]);
    expect(highlights.allFields).toHaveLength(7);
    expect(highlights.allFields.find((f) => f.key === "notes")?.value).toBe("");
  });
});
