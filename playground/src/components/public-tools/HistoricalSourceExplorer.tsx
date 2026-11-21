import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { isEngineReady } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { inspectExactQuery } from "../../lib/lexicon";
import {
  DEFAULT_SOURCE_RECORDS_LIMIT,
  HistoricalLexiconManifest,
  HistoricalSearchResult,
  HistoricalSourceError,
  HistoricalSourceRecord,
  SourceRecordsCacheStats,
  SourceRecordsClient,
  createSourceRecordsClient,
  extractRecordHighlights,
  normalizeBaseUrl,
} from "../../lib/source-records";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { ToolHeader } from "../common/ToolHeader";
import {
  Search,
  Database,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
  Trash2,
  FileSpreadsheet,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";

interface HistoricalSourceExplorerProps {
  engineReady?: boolean;
  client?: SourceRecordsClient;
  headerActions?: React.ReactNode;
}

const SAMPLE_HISTORICAL_QUERIES = ["தமிழ்", "அறம்", "மரம்", "கடல்"] as const;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KiB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}

function HistoricalRecordCard({
  record,
  displayIndex,
  isTamil,
}: {
  record: HistoricalSourceRecord;
  displayIndex: number;
  isTamil: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const highlights = useMemo(
    () => extractRecordHighlights(record.fields),
    [record.fields]
  );

  const rawJson = useMemo(() => JSON.stringify(record, null, 2), [record]);

  return (
    <Card className="p-4 sm:p-5 space-y-3.5 border border-[var(--border-line)] bg-[var(--bg-surface)]">
      {/* Record Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2.5 pb-3 border-b border-[var(--border-line)]">
        <div className="space-y-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
              #{displayIndex}
            </span>
            <h3 className="text-xl font-tamil font-bold text-[var(--color-mai)] break-words">
              {record.lookup_key}
            </h3>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono-tamil text-[var(--color-muted)]">
            <span className="inline-flex items-center gap-1">
              <FileSpreadsheet className="w-3.5 h-3.5 text-[var(--color-semman)] shrink-0" />
              <span>{record.source_file}</span>
            </span>
            <span>·</span>
            <span>
              {isTamil ? `வரி ${record.source_row}` : `row ${record.source_row}`}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 shrink-0">
          <Badge variant="sandhanam" className="text-[11px]">
            {isTamil
              ? "மூலப் பதிவு · மதிப்பாய்வு இல்லாதது"
              : "source original · unreviewed"}
          </Badge>
          <Badge variant="outline" className="text-[10px] font-mono-tamil">
            owner_supplied_unverified
          </Badge>
        </div>
      </div>

      {/* Prominent Definitions / Glosses */}
      {highlights.definitions.length > 0 && (
        <div className="space-y-1.5">
          {highlights.definitions.map((item) => (
            <div
              key={item.key}
              className="rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] px-3 py-2 text-sm"
            >
              <span className="text-[10px] font-mono-tamil uppercase tracking-wide text-[var(--color-muted)] block mb-0.5">
                {item.key}
              </span>
              <span className="font-tamil-sans text-[var(--color-mai)] leading-relaxed break-words">
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Transliteration & Domain / Category Pills */}
      {(highlights.transliterations.length > 0 || highlights.domains.length > 0) && (
        <div className="flex flex-wrap gap-1.5">
          {highlights.transliterations.map((item) => (
            <Badge
              key={item.key}
              variant="mono"
              className="text-[11px] max-w-full whitespace-normal text-left"
            >
              {item.key}: {item.value}
            </Badge>
          ))}
          {highlights.domains.map((item) => (
            <Badge
              key={item.key}
              variant="outline"
              className="text-[11px] font-mono-tamil max-w-full whitespace-normal text-left"
            >
              {item.key}: {item.value}
            </Badge>
          ))}
        </div>
      )}

      {/* Inherited Status / Verified Cells Explicitly Marked Unreviewed */}
      {highlights.inheritedStatuses.length > 0 && (
        <div className="rounded-xl border border-[var(--color-sandhanam)]/40 bg-[var(--color-sandhanam-light)]/50 px-3 py-2 space-y-1">
          <div className="text-[11px] font-tamil font-semibold text-[var(--color-mai)]">
            {isTamil
              ? "மூலக் கோப்பில் இருந்த நிலைப் புலம் (சரிபார்க்கப்படாத மூல உரை):"
              : "Inherited source column (source original, unreviewed):"}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {highlights.inheritedStatuses.map((item) => (
              <Badge key={item.key} variant="mono" className="text-[11px]">
                {item.key}: {item.value}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Expandable Full Original Fields */}
      <div className="pt-2 border-t border-[var(--border-line)] flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          aria-expanded={expanded}
          className="inline-flex items-center gap-1.5 text-xs font-tamil font-medium text-[var(--color-semman)] hover:underline min-h-[44px] cursor-pointer"
        >
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
          <span>
            {isTamil
              ? `மூலப் புலங்கள் அனைத்தையும் காண்க (${highlights.allFields.length})`
              : `View all original fields (${highlights.allFields.length})`}
          </span>
        </button>

        <CopyButton
          text={rawJson}
          size="sm"
          variant="outline"
          label={isTamil ? "JSON நகலெடு" : "Copy JSON"}
        />
      </div>

      {expanded && (
        <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[var(--border-line)] bg-[var(--bg-raised)]">
                  <th className="px-3 py-2 font-mono-tamil font-semibold text-[var(--color-muted)] w-1/3">
                    {isTamil ? "மூலப் புலம்" : "Original column"}
                  </th>
                  <th className="px-3 py-2 font-mono-tamil font-semibold text-[var(--color-muted)]">
                    {isTamil ? "மூல மதிப்பு (மாற்றமின்றி)" : "Verbatim value"}
                  </th>
                </tr>
              </thead>
              <tbody>
                {highlights.allFields.map((field) => (
                  <tr
                    key={field.key}
                    className="border-b border-[var(--border-line)]/60 last:border-b-0 align-top"
                  >
                    <td className="px-3 py-2 font-mono-tamil text-[11px] text-[var(--color-muted)] break-all">
                      {field.key}
                    </td>
                    <td className="px-3 py-2 font-tamil-sans text-[var(--color-mai)] whitespace-pre-wrap break-words">
                      {field.value === "" ? (
                        <span className="font-mono-tamil text-[11px] italic text-[var(--color-muted)]">
                          {isTamil ? '"" (வெற்று)' : '"" (empty)'}
                        </span>
                      ) : (
                        field.value
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Card>
  );
}

export function HistoricalSourceExplorer({
  engineReady,
  client: providedClient,
  headerActions,
}: HistoricalSourceExplorerProps) {
  const { language } = useLanguage();
  const isTamil = language === "ta";
  const ready = engineReady ?? isEngineReady();

  const client = useMemo(
    () => providedClient ?? createSourceRecordsClient(),
    [providedClient]
  );

  const [manifest, setManifest] = useState<HistoricalLexiconManifest | null>(null);
  const [manifestLoading, setManifestLoading] = useState<boolean>(false);
  const [manifestError, setManifestError] = useState<HistoricalSourceError | null>(null);

  const [query, setQuery] = useState<string>("");
  const [searchLoading, setSearchLoading] = useState<boolean>(false);
  const [searchResult, setSearchResult] = useState<HistoricalSearchResult | null>(null);
  const [searchError, setSearchError] = useState<HistoricalSourceError | null>(null);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [cacheStats, setCacheStats] = useState<SourceRecordsCacheStats>(() =>
    client.getCacheStats()
  );
  const [showBundleDetails, setShowBundleDetails] = useState<boolean>(false);

  const activeSearchAbortRef = useRef<AbortController | null>(null);
  const searchSeqRef = useRef<number>(0);
  const lastAttemptRef = useRef({ query: "", offset: 0 });

  const queryDiagnostics = useMemo(() => inspectExactQuery(query), [query]);

  const loadManifestNow = useCallback(
    async (forceReload = false) => {
      setManifestLoading(true);
      setManifestError(null);
      try {
        const loaded = await client.loadManifest({ forceReload });
        setManifest(loaded);
      } catch (err: unknown) {
        if (err instanceof HistoricalSourceError && err.kind === "aborted") {
          return;
        }
        setManifestError(
          err instanceof HistoricalSourceError
            ? err
            : new HistoricalSourceError(
                "network_error",
                err instanceof Error ? err.message : String(err),
                { cause: err }
              )
        );
      } finally {
        setManifestLoading(false);
      }
    },
    [client]
  );

  useEffect(() => {
    const controller = new AbortController();
    let mounted = true;

    setManifestLoading(true);
    client
      .loadManifest({ signal: controller.signal })
      .then((loaded) => {
        if (!mounted) return;
        setManifest(loaded);
        setManifestError(null);
      })
      .catch((err: unknown) => {
        if (!mounted) return;
        if (err instanceof HistoricalSourceError && err.kind === "aborted") {
          return;
        }
        setManifestError(
          err instanceof HistoricalSourceError
            ? err
            : new HistoricalSourceError(
                "network_error",
                err instanceof Error ? err.message : String(err),
                { cause: err }
              )
        );
      })
      .finally(() => {
        if (mounted) setManifestLoading(false);
      });

    return () => {
      mounted = false;
      controller.abort();
      activeSearchAbortRef.current?.abort();
    };
  }, [client]);

  const executeSearch = useCallback(
    async (targetQuery: string, targetOffset: number) => {
      if (!ready) return;
      lastAttemptRef.current = { query: targetQuery, offset: targetOffset };

      activeSearchAbortRef.current?.abort();
      const controller = new AbortController();
      activeSearchAbortRef.current = controller;
      const seq = ++searchSeqRef.current;

      setSearchLoading(true);
      setSearchError(null);
      const t0 = performance.now();

      try {
        const res = await client.search({
          query: targetQuery,
          offset: targetOffset,
          limit: DEFAULT_SOURCE_RECORDS_LIMIT,
          signal: controller.signal,
        });

        if (controller.signal.aborted || seq !== searchSeqRef.current) {
          return;
        }

        setLatencyMs(performance.now() - t0);
        setManifest(res.manifest);
        setManifestError(null);
        setSearchResult(res);
        setCacheStats(client.getCacheStats());
      } catch (err: unknown) {
        if (
          controller.signal.aborted ||
          seq !== searchSeqRef.current ||
          (err instanceof HistoricalSourceError && err.kind === "aborted")
        ) {
          return;
        }
        setLatencyMs(performance.now() - t0);
        setSearchResult(null);
        setSearchError(
          err instanceof HistoricalSourceError
            ? err
            : new HistoricalSourceError(
                "engine_error",
                err instanceof Error ? err.message : String(err),
                { cause: err }
              )
        );
      } finally {
        if (seq === searchSeqRef.current) {
          setSearchLoading(false);
        }
      }
    },
    [client, ready]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void executeSearch(query, 0);
  };

  const handleSampleClick = (sample: string) => {
    setQuery(sample);
    void executeSearch(sample, 0);
  };

  const handleClear = () => {
    activeSearchAbortRef.current?.abort();
    searchSeqRef.current += 1;
    setQuery("");
    setSearchResult(null);
    setSearchError(null);
    setSearchLoading(false);
  };

  const handlePageChange = (nextOffset: number) => {
    const safeOffset = Math.max(0, nextOffset);
    void executeSearch(searchResult?.response.query ?? query, safeOffset);
  };

  const totalCountText = manifest ? manifest.total_records.toLocaleString()
    : manifestLoading ? (isTamil ? "ஏற்றுகிறது…" : "loading…")
    : (isTamil ? "கிடைக்கவில்லை" : "unavailable");
  const distinctKeysText = manifest
    ? manifest.distinct_keys.toLocaleString()
    : manifestLoading
      ? isTamil
        ? "ஏற்றுகிறது…"
        : "loading…"
      : isTamil
        ? "கிடைக்கவில்லை"
        : "unavailable";

  const expectedBase = `${normalizeBaseUrl()}historical-lexicon/`;

  const response = searchResult?.response ?? null;
  const currentPage = response
    ? Math.floor(response.offset / response.limit) + 1
    : 1;
  const totalPages = response
    ? Math.max(1, Math.ceil(response.total / response.limit))
    : 1;
  const canGoPrev = Boolean(response && response.offset > 0 && !searchLoading);
  const canGoNext = Boolean(
    response &&
      response.offset + response.records.length < response.total &&
      !searchLoading
  );

  return (
    <div className="space-y-6">
      <ToolHeader
        title={isTamil ? "வரலாற்று மூலப் பதிவுகள்" : "Historical source records"}
        description={
          isTamil
            ? "உரிமையாளர் வழங்கிய மூலத் தரவு; மூல உரிமைகள் மற்றும் மொழியியல் உறுதிப்பாடு தீர்மானிக்கப்படவில்லை"
            : "Original supplied data; source rights and linguistic claims unresolved"
        }
        meta={
          <div className="flex flex-wrap items-center gap-1.5">
            <Badge variant="sandhanam" className="font-mono-tamil text-[11px]">
              {manifest?.data_status ?? "owner_supplied_unverified"}
            </Badge>
            <Badge variant="outline" className="font-mono-tamil text-[11px]">
              rights: {manifest?.rights_status ?? "unresolved"}
            </Badge>
          </div>
        }
        actions={headerActions}
      />

      {/* Compact Stats Ribbon + Collapsible File & Cache Details */}
      <Card className="p-3 sm:px-4 sm:py-3 border border-[var(--border-line)] bg-[var(--bg-surface)] space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Database className="w-3.5 h-3.5 text-[var(--color-sandhanam)] shrink-0" />
            <Badge variant="sandhanam" className="text-[11px] font-mono-tamil">
              {totalCountText}{" "}
              {isTamil ? "பதிவுகள்" : "records"} · {distinctKeysText}{" "}
              {isTamil ? "தனித் திறவுகோல்கள்" : "distinct keys"}
            </Badge>
            {manifest && (
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                {manifest.files.length} CSV · {Object.keys(manifest.buckets).length} buckets · cache{" "}
                {cacheStats.size}/{cacheStats.capacity}
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={() => setShowBundleDetails((prev) => !prev)}
            aria-expanded={showBundleDetails}
            className="inline-flex items-center gap-1.5 text-xs font-tamil font-medium text-[var(--color-semman)] hover:underline self-start sm:self-auto shrink-0 min-h-[44px] cursor-pointer"
          >
            <span>
              {isTamil ? "மூலக் கோப்புகள் & தற்காலிக சேமிப்பு" : "Source files & cache"}
            </span>
            {showBundleDetails ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </button>
        </div>

        {showBundleDetails && (
          <div className="pt-3 border-t border-[var(--border-line)] space-y-3 text-xs">
            <div className="rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-3 flex items-start gap-2.5">
              <Info className="w-4 h-4 text-[var(--color-semman)] shrink-0 mt-0.5" />
              <p className="font-tamil-sans text-[var(--color-muted)] leading-relaxed">
                {isTamil
                  ? `தேடப்படும் சொல்லுக்குரிய வாளி (.json) மட்டும் Rust இயந்திரம் வழியாகத் தேர்ந்தெடுக்கப்பட்டு, JSON பாகுபடுத்தும் முன் crypto.subtle மூலம் SHA-256 மற்றும் பைட் அளவு சரிபார்க்கப்படுகிறது (அதிகபட்சம் ${cacheStats.capacity} வாளிகள் நினைவகத்தில் வைக்கப்படும்).`
                  : `Only the Rust-selected bucket JSON is fetched for each query, verified against the manifest byte count and SHA-256 via crypto.subtle before JSON parsing, and kept in a bounded ${cacheStats.capacity}-bucket cache.`}
              </p>
            </div>

            {manifest && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                {manifest.files.map((file) => (
                  <div
                    key={file.file}
                    className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-2.5 space-y-0.5"
                  >
                    <div className="font-mono-tamil text-[11px] font-semibold text-[var(--color-mai)] truncate">
                      {file.file}
                    </div>
                    <div className="font-mono-tamil text-[10px] text-[var(--color-muted)]">
                      {file.rows.toLocaleString()} {isTamil ? "வரிசைகள்" : "rows"} ·{" "}
                      {formatBytes(file.bytes)}
                    </div>
                    <div className="font-mono-tamil text-[10px] text-[var(--color-muted)] truncate">
                      sha256: {file.sha256.slice(0, 16)}…
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Engine Loading State */}
      {!ready && (
        <Card className="p-4 border border-[var(--border-line)] bg-[var(--bg-surface)] flex items-center gap-3">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)] shrink-0" />
          <span className="text-xs sm:text-sm font-tamil text-[var(--color-mai)]">
            {isTamil
              ? "Rust WebAssembly இயந்திரம் ஏற்றப்படுகிறது…"
              : "Loading Rust WebAssembly engine…"}
          </span>
        </Card>
      )}

      {/* Search Form (Always immediately reachable) */}
      <Card className="p-5 sm:p-6 border border-[var(--border-line)] bg-[var(--bg-surface)] space-y-4">
        <form onSubmit={handleSubmit} className="space-y-3">
          <label
            htmlFor="historical-source-query-input"
            className="text-xs sm:text-sm font-tamil font-semibold text-[var(--color-mai)] block"
          >
            {isTamil
              ? "துல்லிய மூலப் பதிவுத் தேடல் (Rust NFC + வாளித் தேர்வு):"
              : "Exact source-record search (Rust NFC & bucket dispatch):"}
          </label>
          <div className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[var(--color-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                id="historical-source-query-input"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  isTamil
                    ? "தமிழ்ச் சொல் அல்லது மூலத் திறவுகோலை உள்ளிடுக (எ.கா: தமிழ், அறம்)…"
                    : "Enter Tamil headword or source lookup key (e.g. தமிழ், அறம்)…"
                }
                aria-label={
                  isTamil ? "வரலாற்று மூலப் பதிவுத் தேடல்" : "Historical source record query"
                }
                className="w-full min-h-[44px] pl-10 pr-4 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm sm:text-base font-tamil text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
              />
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={!ready}
                className="flex-1 sm:flex-none font-tamil"
              >
                {searchLoading ? (
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                ) : (
                  <Search className="w-4 h-4 mr-1.5" />
                )}
                <span>{isTamil ? "தேடு" : "Search"}</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={handleClear}
                aria-label={isTamil ? "அழி" : "Clear"}
                className="font-tamil"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[11px] font-tamil-sans text-[var(--color-muted)]">
            <span>
              {isTamil
                ? "இடைவெளி, ZWJ/ZWNJ, மென்-இணைப்பி (SHY) நீக்கப்படாது; Rust NFC சமநிலையாக்கம் மட்டுமே."
                : "Whitespace, joiners (ZWJ/ZWNJ), and soft hyphens are preserved verbatim; Rust applies NFC only."}
            </span>
            <Badge variant="mono" className="text-[10px]">
              {queryDiagnostics.utf8Bytes} UTF-8 bytes
            </Badge>
            {queryDiagnostics.hasLeadingOrTrailingWhitespace && (
              <Badge variant="sandhanam" className="text-[10px]">
                whitespace preserved
              </Badge>
            )}
            {queryDiagnostics.hasJoinersOrSoftHyphen && (
              <Badge variant="terracotta" className="text-[10px]">
                preserved: {queryDiagnostics.joinerLabels.join(", ")}
              </Badge>
            )}
          </div>
        </form>

        {/* Quick Queries */}
        <div className="space-y-2 pt-2 border-t border-[var(--border-line)]">
          <span className="text-xs font-tamil font-semibold text-[var(--color-muted)] block">
            {isTamil ? "மாதிரித் தேடல்கள்:" : "Sample queries:"}
          </span>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_HISTORICAL_QUERIES.map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => handleSampleClick(sample)}
                disabled={!ready}
                className={`inline-flex items-center px-3 py-1.5 min-h-[44px] rounded-xl border text-xs font-tamil transition-colors cursor-pointer disabled:opacity-50 ${
                  query === sample
                    ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold"
                    : "border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-[var(--color-mai)]"
                }`}
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Manifest Availability Banner (only if missing or error while not actively showing a search error) */}
      {manifestError && !searchError && (
        <Card
          className="p-4 sm:p-5 border border-[var(--color-sandhanam)]/50 bg-[var(--color-sandhanam-light)]/60 space-y-3"
          role="alert"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm font-tamil font-bold text-[var(--color-mai)]">
              <AlertTriangle className="w-4 h-4 text-[var(--color-sandhanam)] shrink-0" />
              <span>
                {manifestError.kind === "missing_export"
                  ? isTamil
                    ? "வரலாற்று மூலத் தரவுத் தொகுப்பு ஏற்றுமதி இல்லை (manifest.json கிடைக்கவில்லை)"
                    : "Historical source bundle export not found"
                  : isTamil
                    ? "வரலாற்றுத் தொகுப்பு பட்டியல் ஏற்ற முடியவில்லை"
                    : "Unable to load historical manifest"}
              </span>
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void loadManifestNow(true)}
              disabled={manifestLoading}
              className="font-tamil min-h-[44px]"
            >
              <RefreshCw
                className={`w-3.5 h-3.5 mr-1.5 ${manifestLoading ? "animate-spin" : ""}`}
              />
              <span>{isTamil ? "மீண்டும் முயல்க" : "Retry"}</span>
            </Button>
          </div>
          <p className="text-xs font-tamil-sans text-[var(--color-muted)] leading-relaxed">
            {manifestError.kind === "missing_export"
              ? isTamil
                ? `எதிர்பார்க்கப்பட்ட பாதை: ${expectedBase}manifest.json. இது தேடல் "முடிவு இல்லை" அல்ல — இந்தப் பதிப்பில் வரலாற்று வாளித் தொகுப்பு சேர்க்கப்படவில்லை.`
                : `Expected bundle export at ${expectedBase}manifest.json. This is distinct from a "no matching records" lookup result.`
              : manifestError.message}
          </p>
        </Card>
      )}

      {/* Search Loading Indicator */}
      {searchLoading && (
        <Card className="p-4 border border-[var(--border-line)] bg-[var(--bg-surface)] flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)] shrink-0" />
            <span className="text-xs sm:text-sm font-tamil text-[var(--color-mai)]">
              {isTamil
                ? "வாளிப் பதிவுப் பைல் சரிபார்க்கப்பட்டு தேடப்படுகிறது…"
                : "Verifying bucket SHA-256 and querying Rust dispatcher…"}
            </span>
          </div>
        </Card>
      )}

      {/* Search Error State (distinguishes missing_export, integrity_error, unsupported_engine, invalid_query) */}
      {searchError && !searchLoading && (
        <Card
          className="p-5 border border-red-500/40 bg-red-500/5 space-y-3"
          role="alert"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-red-700 dark:text-red-300 font-tamil font-bold text-sm">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>
                {searchError.kind === "missing_export"
                  ? isTamil
                    ? "வரலாற்றுத் தொகுப்புக் கோப்பு கிடைக்கவில்லை (Missing export)"
                    : "Historical export asset missing"
                  : searchError.kind === "integrity_error"
                    ? isTamil
                      ? "SHA-256 / தரவு ஒருமைப்பாடு சரிபார்ப்பு தோல்வி"
                      : "Integrity verification failed"
                    : searchError.kind === "unsupported_engine"
                      ? isTamil
                        ? "WASM இயந்திரம் வரலாற்றுத் தேடலை ஆதரிக்கவில்லை"
                        : "Engine does not support historical source lookup"
                      : searchError.kind === "invalid_query"
                        ? isTamil
                          ? "செல்லுபடியாகாத தேடல் உள்ளீடு"
                          : "Invalid query"
                        : isTamil
                          ? "தேடல் பிழை"
                          : "Lookup error"}
              </span>
            </div>
            <Badge variant="mono">{latencyMs.toFixed(2)} ms</Badge>
          </div>

          <pre className="text-xs font-mono-tamil text-red-700 dark:text-red-300 whitespace-pre-wrap break-words bg-[var(--bg-surface)] border border-red-500/30 rounded-xl p-3">
            {searchError.message}
          </pre>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void executeSearch(lastAttemptRef.current.query, lastAttemptRef.current.offset)}
            disabled={!ready}
            className="font-tamil min-h-[44px]"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            <span>{isTamil ? "மீண்டும் முயல்க" : "Retry"}</span>
          </Button>
        </Card>
      )}

      {/* Not Found State (Distinct from missing export!) */}
      {response && response.status === "not_found" && !searchLoading && !searchError && (
        <Card className="p-5 border border-[var(--border-line)] bg-[var(--bg-surface)] space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {isTamil ? "பொருத்தம் இல்லை" : "not_found"}
              </Badge>
              <h3 className="text-base font-tamil font-bold text-[var(--color-mai)]">
                {isTamil
                  ? "இந்தத் திறவுகோலுக்கு மூலப் பதிவுகள் இல்லை"
                  : "No matching source records"}
              </h3>
            </div>
            <Badge variant="mono">{latencyMs.toFixed(2)} ms</Badge>
          </div>
          <p className="text-xs font-tamil-sans text-[var(--color-muted)] leading-relaxed">
            {isTamil
              ? "சரிபார்க்கப்பட்ட வாளித் தரவில் துல்லிய NFC பொருத்தம் எதுவும் கிடைக்கவில்லை."
              : "The bucket file passed SHA-256 verification and Rust found 0 exact NFC matches."}
          </p>
          <div className="flex flex-wrap items-center gap-2 text-xs font-mono-tamil text-[var(--color-muted)] pt-1">
            <span>normalized_query:</span>
            <code className="px-2 py-0.5 rounded bg-[var(--bg-raised)] border border-[var(--border-line)] text-[var(--color-mai)]">
              {JSON.stringify(response.normalized_query)}
            </code>
            <span>· bucket: {searchResult?.bucketInfo.bucket}.json</span>
            <span>· {response.data_status}</span>
          </div>
        </Card>
      )}

      {/* Matched Records + Pagination */}
      {response && response.status === "matched" && !searchLoading && !searchError && searchResult && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 px-1">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="sandhanam">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>
                  {response.total.toLocaleString()}{" "}
                  {isTamil ? "பொருந்தும் பதிவுகள்" : "matching records"}
                </span>
              </Badge>
              <Badge variant="mono">
                {response.records.length > 0
                  ? `${response.offset + 1}–${response.offset + response.records.length}`
                  : "0"}{" "}
                / {response.total.toLocaleString()}
              </Badge>
              {response.normalized_query !== response.query && (
                <Badge variant="terracotta" className="font-mono-tamil">
                  NFC: {response.normalized_query}
                </Badge>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="mono">
                bucket {searchResult.bucketInfo.bucket}.json (
                {searchResult.cacheHit ? "cache hit" : "SHA-256 verified"})
              </Badge>
              <Badge variant="mono">{latencyMs.toFixed(2)} ms</Badge>
            </div>
          </div>

          {response.total > response.limit && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] px-3.5 py-2">
              <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                {isTamil
                  ? `பக்கம் ${currentPage} / ${totalPages}`
                  : `Page ${currentPage} of ${totalPages}`}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!canGoPrev}
                  onClick={() => handlePageChange(response.offset - response.limit)}
                  className="font-tamil min-h-[44px]"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  <span>{isTamil ? "முந்தைய" : "Previous"}</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!canGoNext}
                  onClick={() => handlePageChange(response.offset + response.limit)}
                  className="font-tamil min-h-[44px]"
                >
                  <span>{isTamil ? "அடுத்த" : "Next"}</span>
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-3.5">
            {response.records.map((record, idx) => (
              <HistoricalRecordCard
                key={`${record.source_file}:${record.source_row}`}
                record={record}
                displayIndex={response.offset + idx + 1}
                isTamil={isTamil}
              />
            ))}
          </div>

          {response.total > response.limit && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] px-3.5 py-2">
              <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                {isTamil
                  ? `பக்கம் ${currentPage} / ${totalPages}`
                  : `Page ${currentPage} of ${totalPages}`}
              </span>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!canGoPrev}
                  onClick={() => handlePageChange(response.offset - response.limit)}
                  className="font-tamil min-h-[44px]"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  <span>{isTamil ? "முந்தைய" : "Previous"}</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={!canGoNext}
                  onClick={() => handlePageChange(response.offset + response.limit)}
                  className="font-tamil min-h-[44px]"
                >
                  <span>{isTamil ? "அடுத்த" : "Next"}</span>
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
