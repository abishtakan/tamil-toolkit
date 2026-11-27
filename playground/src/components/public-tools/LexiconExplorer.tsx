import {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
  lazy,
  Suspense,
} from "react";
import * as tt from "tamil-toolkit/web";
import {
  defineLexiconV2,
  fuzzySearchLexiconV2,
  getLexiconLongestPrefixes,
  getLexiconPacks,
  isEngineReady,
  lookupLexicon,
  searchLexiconEnglishV2,
  searchLexiconV2,
  transliterateSuggest,
  type LexiconCategory,
  type LexiconV2Stats,
  type LexiconWordDefinition,
} from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { IS_PUBLIC_BETA, resolveLexiconViewMode } from "../../lib/tools";
import {
  IS_OPEN_ONLY_CHANNEL,
  LEXICON_CATEGORIES,
  ProgressiveMountProgress,
  TlpackManifest,
  TlpackManifestEntry,
  UnifiedLexiconSearchHit,
  buildV2QueryOptions,
  buildV2SearchOptions,
  fetchTlpackManifest,
  formatCompactFacetCount,
  isAsciiLatinQuery,
  isLocalPackEntry,
  lexiconV2Manager,
  mergeEnglishAndTanglishHits,
  packCategory,
} from "../../lib/lexicon-v2";
import { ToolHeader } from "../common/ToolHeader";
import {
  BrowseIndexData,
  BrowseWordItem,
  CANONICAL_LEXICON_EXAMPLES,
  ContractTestPreset,
  ExtendedEntryDetail,
  ExtendedManifest,
  LexiconExampleItem,
  RawBrowseIndexPayload,
  RawExtendedLetterRow,
  buildLexiconLookupOptions,
  buildLexiconRawRequest,
  collectEntryProvenance,
  computeLoadedPackTotals,
  deriveFiniteScopeOptions,
  extractSafeLinksFromProvenance,
  filterBrowseItems,
  findExtendedLetterBucket,
  inspectExactQuery,
  parseBrowseIndex,
  parseExtendedLetterRows,
  sha256PrefixHex,
  verifyPackCatalogAlignment,
} from "../../lib/lexicon";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import {
  MergedWordDefinitionCard,
  formatPosLabel,
} from "./lexicon/MergedWordDefinitionCard";
import { LexiconPackDrawer } from "./lexicon/LexiconPackDrawer";
import {
  Search,
  BookMarked,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  X,
  Loader2,
  Database,
  BookOpen,
  Sparkles,
  CheckCircle2,
} from "lucide-react";

export { MergedWordDefinitionCard };

interface LexiconExplorerProps {
  engineReady?: boolean;
  initialQuery?: string;
  initialQueryNonce?: number;
}

const LazyHistoricalSourceExplorer = lazy(() =>
  import("./HistoricalSourceExplorer").then((m) => ({
    default: m.HistoricalSourceExplorer,
  }))
);

const PAGE_SIZE = 40;

function AttestedScopeBadges({
  region,
  register,
}: {
  region: tt.LexiconScope;
  register: tt.LexiconLabelField;
}) {
  const hasRegion = region.state === "attested" && region.codes.length > 0;
  const hasRegister = register.availability === "available" && Boolean(register.value);
  if (!hasRegion && !hasRegister) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {hasRegion &&
        region.codes.map((code) => (
          <Badge key={code} variant="sandhanam" className="text-[11px]">
            {code}
          </Badge>
        ))}
      {hasRegister && register.value && (
        <Badge variant="outline" className="text-[11px] capitalize">
          {register.value}
        </Badge>
      )}
    </div>
  );
}

/**
 * Legacy v1 + extended-shard fallback card rendered ONLY while v2 packs are still booting
 * (or when no v2 packs are mounted). Never stacked alongside `MergedWordDefinitionCard`.
 */
function UnifiedWordCard({
  word,
  entries,
  extended,
  canonicalQuery,
  language,
}: {
  word: string;
  entries: readonly tt.LexiconEntry[];
  extended: ExtendedEntryDetail | null;
  canonicalQuery?: string;
  language: "ta" | "en";
}) {
  const [showProv, setShowProv] = useState(false);

  const headword = entries[0]?.headword ?? word;

  const posGroups = useMemo(() => {
    const groups: {
      pos: string;
      entries: tt.LexiconEntry[];
      senses: tt.LexiconSense[];
      regions: string[];
      registers: string[];
    }[] = [];
    const byPos = new Map<string, (typeof groups)[number]>();

    for (const entry of entries) {
      const pos =
        entry.part_of_speech.availability === "available" && entry.part_of_speech.value
          ? entry.part_of_speech.value
          : "OTHER";
      let group = byPos.get(pos);
      if (!group) {
        group = { pos, entries: [], senses: [], regions: [], registers: [] };
        byPos.set(pos, group);
        groups.push(group);
      }
      group.entries.push(entry);
      group.senses.push(...entry.senses);
      if (entry.region.state === "attested") {
        for (const r of entry.region.codes) {
          if (!group.regions.includes(r)) group.regions.push(r);
        }
      }
      if (entry.register.availability === "available" && entry.register.value) {
        if (!group.registers.includes(entry.register.value)) {
          group.registers.push(entry.register.value);
        }
      }
    }
    return groups;
  }, [entries]);

  const allPosLabels = useMemo(() => {
    const set = new Set<string>();
    for (const g of posGroups) {
      if (g.pos !== "OTHER") set.add(g.pos);
    }
    if (extended?.pos) set.add(extended.pos);
    return Array.from(set);
  }, [posGroups, extended]);

  const extraForms = useMemo(() => {
    const seen = new Set<string>();
    const out: tt.LexiconForm[] = [];
    for (const entry of entries) {
      for (const form of entry.forms) {
        if (form.text === headword && form.representation === "written") continue;
        const key = `${form.representation}:${form.text}`;
        if (!seen.has(key)) {
          seen.add(key);
          out.push(form);
        }
      }
    }
    return out;
  }, [entries, headword]);

  const allSafeLinks = useMemo(() => {
    const map = new Map<string, { label: string; href: string }>();
    for (const entry of entries) {
      for (const p of collectEntryProvenance(entry)) {
        for (const link of extractSafeLinksFromProvenance(p)) {
          if (!map.has(link.href)) {
            map.set(link.href, {
              label: `en.wiktionary.org · ${link.label}`,
              href: link.href,
            });
          }
        }
      }
    }
    if (extended) {
      map.set(extended.permalink, {
        label: "ta.wiktionary.org · permalink",
        href: extended.permalink,
      });
      map.set(extended.history_url, {
        label: "ta.wiktionary.org · history",
        href: extended.history_url,
      });
    }
    return Array.from(map.values());
  }, [entries, extended]);

  const extraEngTranslations = useMemo(() => {
    if (!extended || extended.eng_trans.length === 0) return [];
    const existingLower = new Set<string>();
    for (const entry of entries) {
      for (const s of entry.senses) {
        for (const c of s.components) {
          existingLower.add(c.text.trim().toLowerCase());
        }
      }
    }
    return extended.eng_trans.filter((tr) => !existingLower.has(tr.trim().toLowerCase()));
  }, [entries, extended]);

  return (
    <Card className="p-5 sm:p-7 space-y-6" data-testid="legacy-word-card">
      <div className="flex flex-wrap items-start justify-between gap-3 pb-4 border-b border-[var(--border-line)]">
        <div className="space-y-1.5">
          <div className="flex flex-wrap items-baseline gap-3">
            <h2 className="text-3xl sm:text-4xl font-tamil font-bold text-[var(--color-mai)] tracking-tight">
              {headword}
            </h2>
            {canonicalQuery && canonicalQuery !== word && (
              <Badge variant="sandhanam" className="text-[11px] font-mono-tamil">
                NFC: {canonicalQuery}
              </Badge>
            )}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs text-[var(--color-muted)]">
            {allPosLabels.length > 0 && (
              <span className="font-tamil italic text-sm text-[var(--color-semman)] font-medium">
                {allPosLabels.map((p) => formatPosLabel(p, language)).join(" · ")}
              </span>
            )}
            <Badge variant="terracotta" className="text-[10px]">
              Verified Open · CC-BY-SA-4.0
            </Badge>
          </div>
        </div>

        <CopyButton text={headword} size="sm" variant="outline" />
      </div>

      {extraForms.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {extraForms.map((form) => (
            <div
              key={form.form_id}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-raised)] text-xs"
            >
              <span className="font-tamil font-semibold text-[var(--color-mai)]">
                {form.text}
              </span>
              <span className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                {form.representation}
              </span>
            </div>
          ))}
        </div>
      )}

      {posGroups.length > 0 && (
        <div className="space-y-5">
          {posGroups.map((group) => (
            <section key={group.pos} className="space-y-2.5">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-sm font-tamil font-bold italic text-[var(--color-semman)]">
                  {formatPosLabel(group.pos, language)}
                </h3>
                {group.regions.map((r) => (
                  <Badge key={r} variant="sandhanam" className="text-[10px]">
                    {r}
                  </Badge>
                ))}
                {group.registers.map((reg) => (
                  <Badge key={reg} variant="outline" className="text-[10px] capitalize">
                    {reg}
                  </Badge>
                ))}
              </div>

              <ol className="space-y-3">
                {group.senses.map((sense, idx) => (
                  <li key={sense.sense_id} className="flex items-baseline gap-2.5">
                    <span className="text-xs font-mono-tamil font-semibold text-[var(--color-muted)] w-5 text-right shrink-0">
                      {idx + 1}.
                    </span>
                    <div className="min-w-0 flex-1 space-y-1.5">
                      {sense.components.map((comp) => (
                        <p
                          key={comp.text_id}
                          className="text-sm sm:text-[15px] text-[var(--color-mai)] leading-relaxed"
                        >
                          {comp.text}
                        </p>
                      ))}

                      <AttestedScopeBadges region={sense.region} register={sense.register} />

                      {sense.examples.length > 0 && (
                        <div className="pt-1 space-y-1">
                          {sense.examples.map((ex) => (
                            <p
                              key={ex.text_id}
                              className="text-xs font-tamil text-[var(--color-muted)] pl-2.5 border-l-2 border-[var(--color-sandhanam)]/70"
                            >
                              “{ex.text}”
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          ))}
        </div>
      )}

      {extended && (extended.tam_defs.length > 0 || extraEngTranslations.length > 0) && (
        <div
          className={`space-y-4 ${
            posGroups.length > 0 ? "pt-5 border-t border-[var(--border-line)]" : ""
          }`}
        >
          {extended.tam_defs.length > 0 && (
            <section className="space-y-2.5">
              <h3 className="text-sm font-tamil font-bold text-[var(--color-semman)]">
                {language === "ta" ? "தமிழ் பொருள்" : "Tamil Definitions (தமிழ் பொருள்)"}
              </h3>
              <ol className="space-y-2.5">
                {extended.tam_defs.map((def, idx) => (
                  <li key={idx} className="flex items-baseline gap-2.5">
                    <span className="text-xs font-mono-tamil font-semibold text-[var(--color-muted)] w-5 text-right shrink-0">
                      {idx + 1}.
                    </span>
                    <p className="text-sm sm:text-[15px] font-tamil text-[var(--color-mai)] leading-relaxed">
                      {def}
                    </p>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {extraEngTranslations.length > 0 && (
            <section className="space-y-2">
              <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
                {language === "ta" ? "ஆங்கில மொழிபெயர்ப்புகள்" : "English Translations"}
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {extraEngTranslations.map((tr, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-full border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs sm:text-sm text-[var(--color-mai)]"
                  >
                    {tr}
                  </span>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {allSafeLinks.length > 0 && (
        <div className="pt-3 border-t border-[var(--border-line)]">
          <button
            type="button"
            onClick={() => setShowProv((prev) => !prev)}
            aria-expanded={showProv}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-muted)] hover:text-[var(--color-semman)] py-1 cursor-pointer"
          >
            {showProv ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
            <span>
              {language === "ta" ? "மூலங்கள் & உரிமம்" : "Sources & License"} (CC-BY-SA-4.0)
            </span>
          </button>

          {showProv && (
            <div className="mt-2.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-3.5 space-y-2.5 text-xs">
              <div className="flex flex-wrap gap-2">
                {allSafeLinks.map((link) => (
                  <a
                    key={link.href}
                    href={link.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] text-[var(--color-semman)] hover:border-[var(--color-semman)] text-[11px] font-medium"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>{link.label}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

export function LexiconExplorer({
  engineReady,
  initialQuery,
  initialQueryNonce,
}: LexiconExplorerProps) {
  const { t, language } = useLanguage();
  const ready = engineReady ?? isEngineReady();
  const [viewMode, setViewMode] = useState<"verified" | "historical">(() =>
    typeof window !== "undefined" ? resolveLexiconViewMode(window.location.search) : "verified"
  );

  // Dataset scope: Verified Open (90k) vs Full Archive (241k), locked to "open" only when IS_OPEN_ONLY_CHANNEL is true
  const [datasetScope, setDatasetScope] = useState<"open" | "full">(() =>
    IS_OPEN_ONLY_CHANNEL ? "open" : "full"
  );
  const [selectedCategory, setSelectedCategory] = useState<LexiconCategory | "all">("all");

  const [availablePacks, setAvailablePacks] = useState<tt.LexiconPackInfo[]>([]);
  const [packsError, setPacksError] = useState<string | null>(null);

  const [browseIndex, setBrowseIndex] = useState<BrowseIndexData | null>(null);
  const [extendedManifest, setExtendedManifest] = useState<ExtendedManifest | null>(null);
  const [activeLetterItems, setActiveLetterItems] = useState<BrowseWordItem[] | null>(null);
  const [browseLoading, setBrowseLoading] = useState<boolean>(true);
  const [letterLoading, setLetterLoading] = useState<boolean>(false);
  const [browseError, setBrowseError] = useState<string | null>(null);

  const letterCacheRef = useRef<Map<string, BrowseWordItem[]>>(new Map());
  const shardCacheRef = useRef<Map<string, Record<string, ExtendedEntryDetail>>>(new Map());
  const shardRequestSeqRef = useRef<number>(0);
  const defineRequestSeqRef = useRef<number>(0);
  const lastConsumedNonceRef = useRef<number | undefined>(undefined);
  const searchBoxRef = useRef<HTMLDivElement>(null);

  const [selectedLetter, setSelectedLetter] = useState<string>("ந");
  const [selectedPos, setSelectedPos] = useState<string>("ALL");
  const [page, setPage] = useState<number>(1);

  const [query, setQuery] = useState(() => initialQuery?.trim() ?? "");
  const [activeWord, setActiveWord] = useState(() => initialQuery?.trim() || "நன்றி");
  const [autocompleteOpen, setAutocompleteOpen] = useState(false);

  const [selectedPacks, setSelectedPacks] = useState<string[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [selectedRegister, setSelectedRegister] = useState<string>("");

  const [response, setResponse] = useState<tt.LexiconLookupResponse | null>(null);
  const [extendedEntry, setExtendedEntry] = useState<ExtendedEntryDetail | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lastRawRequest, setLastRawRequest] = useState<string>("");
  const [lastRawResponse, setLastRawResponse] = useState<string>("");
  const [latencyMs, setLatencyMs] = useState<number>(0);

  // Pack Engine v2 (.tlpack FST runtime) state
  const [v2Manifest, setV2Manifest] = useState<TlpackManifest | null>(null);
  const [v2Stats, setV2Stats] = useState<LexiconV2Stats>({
    pack_count: 0,
    total_entries: 0,
    total_senses: 0,
    total_relations: 0,
    total_bytes: 0,
    packs: [],
  });
  const [v2Progress, setV2Progress] = useState<ProgressiveMountProgress | null>(null);
  const [v2LoadingAction, setV2LoadingAction] = useState<string | null>(null);
  const [v2Error, setV2Error] = useState<string | null>(null);
  const [v2Folded, setV2Folded] = useState(false);
  const [v2Domain, setV2Domain] = useState<string>("ALL");
  const [v2BrowseHits, setV2BrowseHits] = useState<UnifiedLexiconSearchHit[]>([]);
  const [tanglishSuggestions, setTanglishSuggestions] = useState<string[]>([]);
  const [v2NextCursor, setV2NextCursor] = useState<string | undefined>(undefined);
  const [v2HasMore, setV2HasMore] = useState<boolean>(false);
  const [v2CanonicalPrefix, setV2CanonicalPrefix] = useState<string>("");
  const [v2LoadingMore, setV2LoadingMore] = useState<boolean>(false);
  const [v2Definition, setV2Definition] = useState<LexiconWordDefinition | null>(null);
  const [v2LatencyMs, setV2LatencyMs] = useState<number>(0);
  const [leftPaneMode, setLeftPaneMode] = useState<"auto" | "v2" | "browse">("auto");

  const effectiveTier: tt.LexiconTierFilter = useMemo(() => {
    if (IS_OPEN_ONLY_CHANNEL || datasetScope === "open") return "open";
    return "all";
  }, [datasetScope]);

  const availablePackIds = useMemo(
    () => availablePacks.map((p) => p.id),
    [availablePacks]
  );

  const availablePackSet = useMemo(
    () => new Set<string>(availablePackIds),
    [availablePackIds]
  );

  const scopeOptions = useMemo(
    () => deriveFiniteScopeOptions(availablePacks, selectedPacks),
    [availablePacks, selectedPacks]
  );

  const loadedTotals = useMemo(
    () => computeLoadedPackTotals(availablePacks),
    [availablePacks]
  );

  const catalogAlignment = useMemo(
    () => verifyPackCatalogAlignment(availablePacks),
    [availablePacks]
  );

  const queryDiagnostics = useMemo(() => inspectExactQuery(query), [query]);

  // Close autocomplete dropdown on outside click
  useEffect(() => {
    if (typeof document === "undefined") return;
    const handleDocClick = (e: MouseEvent) => {
      if (
        searchBoxRef.current &&
        !searchBoxRef.current.contains(e.target as Node)
      ) {
        setAutocompleteOpen(false);
      }
    };
    document.addEventListener("mousedown", handleDocClick);
    return () => document.removeEventListener("mousedown", handleDocClick);
  }, []);

  // Load legacy browse manifest
  useEffect(() => {
    let cancelled = false;
    setBrowseLoading(true);
    fetch("/lexicon-extended/manifest.json")
      .then((res) => (res.ok ? (res.json() as Promise<ExtendedManifest>) : null))
      .then((extManifest) => {
        if (!cancelled) {
          setExtendedManifest(extManifest);
          setBrowseError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setBrowseError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setBrowseLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Lazy-load embedded browse index when English query or ALL letter is needed
  useEffect(() => {
    if (browseIndex) return;
    const trimmed = query.trim();
    const isEnglishQuery = Boolean(trimmed && !/[\u0B80-\u0BFF]/.test(trimmed));
    const needsEmbeddedAll = selectedLetter === "ALL" || isEnglishQuery;
    if (!needsEmbeddedAll) return;

    let cancelled = false;
    fetch("/lexicon-browse-index.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<RawBrowseIndexPayload>;
      })
      .then((rawEmbedded) => {
        if (!cancelled) {
          setBrowseIndex(parseBrowseIndex(rawEmbedded));
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [browseIndex, selectedLetter, query]);

  const loadLetterBucket = useCallback(async (letterId: string, file: string) => {
    const cached = letterCacheRef.current.get(letterId);
    if (cached) {
      setActiveLetterItems(cached);
      return cached;
    }
    setLetterLoading(true);
    try {
      const res = await fetch(`/lexicon-extended/letters/${file}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const rawRows = (await res.json()) as RawExtendedLetterRow[];
      const parsed = parseExtendedLetterRows(rawRows, letterId);
      letterCacheRef.current.set(letterId, parsed);
      setActiveLetterItems(parsed);
      return parsed;
    } catch {
      setActiveLetterItems(null);
      return null;
    } finally {
      setLetterLoading(false);
    }
  }, []);

  const loadExtendedDetail = useCallback(async (word: string) => {
    const seq = ++shardRequestSeqRef.current;
    const normalized = word.trim().normalize("NFC");
    if (!normalized) {
      if (shardRequestSeqRef.current === seq) setExtendedEntry(null);
      return null;
    }
    try {
      const hex = await sha256PrefixHex(normalized);
      let shard = shardCacheRef.current.get(hex);
      if (!shard) {
        const res = await fetch(`/lexicon-extended/shards/${hex}.json`);
        if (!res.ok) {
          if (shardRequestSeqRef.current === seq) setExtendedEntry(null);
          return null;
        }
        shard = (await res.json()) as Record<string, ExtendedEntryDetail>;
        shardCacheRef.current.set(hex, shard);
      }
      const hit = shard[normalized] ?? null;
      if (shardRequestSeqRef.current === seq) {
        setExtendedEntry(hit);
      }
      return hit;
    } catch {
      if (shardRequestSeqRef.current === seq) setExtendedEntry(null);
      return null;
    }
  }, []);

  useEffect(() => {
    if (!extendedManifest) return;
    if (selectedLetter !== "ALL") {
      const bucket = extendedManifest.letters.find((b) => b.id === selectedLetter);
      if (bucket) {
        void loadLetterBucket(bucket.id, bucket.file);
        return;
      }
    }
    const trimmed = query.trim();
    if (trimmed && /[\u0B80-\u0BFF]/.test(trimmed)) {
      const bucket = findExtendedLetterBucket(trimmed, extendedManifest.letters);
      if (bucket) {
        void loadLetterBucket(bucket.id, bucket.file);
        return;
      }
    }
    setActiveLetterItems(null);
  }, [extendedManifest, selectedLetter, query, loadLetterBucket]);

  const activeWordPool = useMemo(() => {
    if (activeLetterItems && activeLetterItems.length > 0) {
      return activeLetterItems;
    }
    return browseIndex?.items ?? [];
  }, [activeLetterItems, browseIndex]);

  const filteredBrowseItems = useMemo(() => {
    const filterQuery = query.trim() === activeWord && selectedLetter !== "ALL" ? "" : query;
    const legacyPacksFilter =
      selectedCategory === "regional"
        ? ["regional"]
        : selectedCategory === "names_taxa"
          ? ["names_taxa"]
          : selectedCategory === "dictionary"
            ? ["core", "ta_wiktionary"]
            : undefined;
    return filterBrowseItems(activeWordPool, {
      query: filterQuery,
      letter: selectedLetter,
      packs: legacyPacksFilter,
      pos: selectedPos,
      region: selectedRegion || "ALL",
    });
  }, [activeWordPool, query, activeWord, selectedLetter, selectedCategory, selectedPos, selectedRegion]);

  const fallbackSuggestions = useMemo(() => {
    if (!query.trim()) return [];
    return filterBrowseItems(activeWordPool, {
      query,
      region: selectedRegion || "ALL",
    }).slice(0, 8);
  }, [activeWordPool, query, selectedRegion]);

  useEffect(() => {
    setPage(1);
  }, [query, selectedLetter, selectedCategory, selectedPos, selectedRegion, datasetScope, v2Folded, v2Domain]);

  const totalPages = Math.max(1, Math.ceil(filteredBrowseItems.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pagedItems = useMemo(() => {
    const start = (safePage - 1) * PAGE_SIZE;
    return filteredBrowseItems.slice(start, start + PAGE_SIZE);
  }, [filteredBrowseItems, safePage]);

  const executeLookup = useCallback(
    (
      nextQuery: string,
      optsInput: { packs?: string[]; region?: string; register?: string }
    ) => {
      if (optsInput.packs && optsInput.packs.length === 0) {
        // Allow explicit empty-packs contract tests to hit Rust directly
      } else if (!optsInput.packs && availablePackIds.length === 0) {
        void loadExtendedDetail(nextQuery);
        return;
      }
      const options = buildLexiconLookupOptions(optsInput);
      const rawReqObj = buildLexiconRawRequest(nextQuery, options);
      setLastRawRequest(JSON.stringify(rawReqObj, null, 2));

      const t0 = performance.now();
      try {
        const res = lookupLexicon(nextQuery, options);
        setLatencyMs(performance.now() - t0);
        setResponse(res);
        setLookupError(null);
        setLastRawResponse(JSON.stringify(res, null, 2));
      } catch (err: unknown) {
        setLatencyMs(performance.now() - t0);
        const msg = err instanceof Error ? err.message : String(err);
        setResponse(null);
        setLookupError(msg);
        setLastRawResponse(JSON.stringify({ error: msg }, null, 2));
      }
      void loadExtendedDetail(nextQuery);
    },
    [loadExtendedDetail, availablePackIds.length]
  );

  // Fetch Pack Engine v2 MANIFEST.json on mount (enforcing IS_PUBLIC_BETA)
  useEffect(() => {
    let cancelled = false;
    fetchTlpackManifest()
      .then((manifest) => {
        if (!cancelled) {
          setV2Manifest(manifest);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setV2Manifest(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Load initial word from extended shard immediately so content appears before WASM finishes
  useEffect(() => {
    const startWord = initialQuery?.trim() || "நன்றி";
    void loadExtendedDetail(startWord);
  }, [loadExtendedDetail, initialQuery]);

  // Discover compiled legacy packs from Rust once WASM is ready
  useEffect(() => {
    if (!ready) return;
    try {
      const packs = getLexiconPacks();
      setAvailablePacks(packs);
      setPacksError(null);
      const ids = packs.map((p) => p.id);
      setSelectedPacks(ids);
      if (ids.length > 0) {
        executeLookup(activeWord || "நன்றி", { packs: ids });
      }
      setV2Stats(lexiconV2Manager.syncFromEngine());
    } catch (err: unknown) {
      setPacksError(err instanceof Error ? err.message : String(err));
    }
  }, [ready, executeLookup]);

  // Progressive Auto-Load (.tlpack v2) on startup & when switching to Full Archive
  useEffect(() => {
    if (!ready) return;
    let cancelled = false;
    const includeLocal = !IS_OPEN_ONLY_CHANNEL && datasetScope === "full";

    if (!includeLocal) {
      const removed = lexiconV2Manager.unloadLocalPacks();
      if (removed.length > 0) {
        setV2Stats(lexiconV2Manager.syncFromEngine());
      }
    }

    lexiconV2Manager
      .autoMountProgressive({
        manifest: v2Manifest ?? undefined,
        includeLocal,
        onProgress: (prog) => {
          if (cancelled) return;
          setV2Progress(prog);
          setV2Stats(lexiconV2Manager.syncFromEngine());
        },
      })
      .then(() => {
        if (!cancelled) {
          setV2Stats(lexiconV2Manager.syncFromEngine());
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setV2Error(err instanceof Error ? err.message : String(err));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [ready, datasetScope, v2Manifest]);

  const v2MountedIds = useMemo(
    () => new Set(v2Stats.packs.map((p) => p.pack_id)),
    [v2Stats.packs]
  );

  const v2HasLocalMounted = useMemo(
    () => v2Stats.packs.some((p) => p.pack_tier === "local_historical"),
    [v2Stats.packs]
  );

  const v2DomainCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    if (v2Stats.domain_counts) {
      for (const [dom, count] of Object.entries(v2Stats.domain_counts)) {
        const trimmed = dom.trim();
        if (
          trimmed &&
          trimmed.length <= 48 &&
          !trimmed.startsWith("/") &&
          !trimmed.startsWith(".") &&
          count > 0
        ) {
          counts[trimmed] = count;
        }
      }
    }
    return counts;
  }, [v2Stats.domain_counts]);

  const v2Domains = useMemo(() => {
    const set = new Set<string>(Object.keys(v2DomainCounts));
    for (const pack of v2Stats.packs) {
      if (effectiveTier === "open" && pack.pack_tier !== "verified_open") continue;
      for (const d of pack.domains) {
        const trimmed = d.trim();
        if (trimmed && trimmed.length <= 48 && !trimmed.startsWith("/") && !trimmed.startsWith(".")) {
          set.add(trimmed);
        }
      }
    }
    return Array.from(set).sort((a, b) => {
      const ca = v2DomainCounts[a] ?? 0;
      const cb = v2DomainCounts[b] ?? 0;
      if (ca !== cb) return cb - ca;
      return a.localeCompare(b);
    });
  }, [v2Stats.packs, v2DomainCounts, effectiveTier]);

  const v2CategoryCounts = useMemo(() => {
    if (
      v2Stats.category_counts &&
      Object.keys(v2Stats.category_counts).length > 0 &&
      (effectiveTier === "all" || !v2HasLocalMounted)
    ) {
      return v2Stats.category_counts;
    }
    const derived: Record<string, number> = {};
    for (const pack of v2Stats.packs) {
      if (effectiveTier === "open" && pack.pack_tier !== "verified_open") continue;
      const cat = pack.category ?? packCategory(pack.pack_id);
      derived[cat] = (derived[cat] ?? 0) + pack.entry_count;
    }
    return derived;
  }, [v2Stats.category_counts, v2Stats.packs, effectiveTier, v2HasLocalMounted]);

  const v2Regions = useMemo(() => {
    const set = new Set<string>();
    for (const pack of v2Stats.packs) {
      for (const raw of pack.regions) {
        for (const tok of raw.split(/[,;]/)) {
          const clean = tok.trim();
          if (clean) set.add(clean);
        }
      }
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [v2Stats.packs]);

  const v2OpenManifestPacks = useMemo(
    () =>
      (v2Manifest?.packs ?? []).filter(
        (p) => p.summary.pack_tier === "verified_open" && !isLocalPackEntry(p)
      ),
    [v2Manifest]
  );

  const v2LocalManifestPacks = useMemo(
    () =>
      IS_OPEN_ONLY_CHANNEL
        ? []
        : (v2Manifest?.packs ?? []).filter((p) => isLocalPackEntry(p)),
    [v2Manifest]
  );

  const v2ExtraMountedPacks = useMemo(() => {
    const manifestIds = new Set((v2Manifest?.packs ?? []).map((p) => p.summary.pack_id));
    return v2Stats.packs.filter((p) => !manifestIds.has(p.pack_id));
  }, [v2Manifest, v2Stats.packs]);

  useEffect(() => {
    if (v2Domain !== "ALL" && !v2Domains.includes(v2Domain)) {
      setV2Domain("ALL");
    }
  }, [v2Domain, v2Domains]);

  // Live FST Browse & Unified Search (Tamil + Tanglish + Reverse English) whenever v2 packs are mounted
  const isAsciiQuery = useMemo(() => isAsciiLatinQuery(query), [query]);

  const isNonTamilNonAsciiQuery = useMemo(() => {
    const trimmed = query.trim();
    return Boolean(trimmed && !/[\u0B80-\u0BFF]/.test(trimmed) && !isAsciiQuery);
  }, [query, isAsciiQuery]);

  const v2BrowsePrefix = useMemo(() => {
    const trimmed = query.trim();
    if (trimmed.length > 0) return trimmed;
    if (selectedLetter !== "ALL") return selectedLetter;
    return "";
  }, [query, selectedLetter]);

  useEffect(() => {
    if (!ready || v2Stats.pack_count === 0 || isNonTamilNonAsciiQuery) {
      setV2BrowseHits([]);
      setTanglishSuggestions([]);
      setV2NextCursor(undefined);
      setV2HasMore(false);
      setV2CanonicalPrefix("");
      return;
    }

    if (isAsciiQuery) {
      const trimmed = query.trim();
      let englishHits: tt.LexiconPrefixSearchHit[] = [];
      try {
        const englishOpts = buildV2SearchOptions({
          tier: effectiveTier,
          category: selectedCategory,
          pos: selectedPos,
          domain: v2Domain,
          region: selectedRegion,
          register: selectedRegister,
          limit: 50,
        });
        englishHits = searchLexiconEnglishV2(trimmed, englishOpts).hits;
      } catch {
        englishHits = [];
      }

      const candidates = transliterateSuggest(trimmed, "phonetic-v1", 5);
      setTanglishSuggestions(candidates);

      const tanglishHits: tt.LexiconPrefixSearchHit[] = [];
      const prefixOpts = buildV2SearchOptions({
        tier: effectiveTier,
        category: selectedCategory,
        folded: v2Folded,
        pos: selectedPos,
        domain: v2Domain,
        region: selectedRegion,
        register: selectedRegister,
        limit: 8,
      });
      for (const candidate of candidates) {
        try {
          const res = searchLexiconV2(candidate, prefixOpts);
          for (const hit of res.hits) {
            tanglishHits.push({
              ...hit,
              matched_key: hit.headword === candidate ? candidate : hit.matched_key,
            });
          }
        } catch {
          // Skip failed candidate lookup
        }
      }

      setV2BrowseHits(
        mergeEnglishAndTanglishHits(trimmed, englishHits, tanglishHits)
      );
      setV2NextCursor(undefined);
      setV2HasMore(false);
      setV2CanonicalPrefix(trimmed);
      return;
    }

    setTanglishSuggestions([]);
    try {
      const opts = buildV2SearchOptions({
        tier: effectiveTier,
        category: selectedCategory,
        folded: v2Folded && query.trim().length > 0,
        pos: selectedPos,
        domain: v2Domain,
        region: selectedRegion,
        register: selectedRegister,
        limit: 200,
      });
      const res = searchLexiconV2(v2BrowsePrefix, opts);
      setV2BrowseHits(res.hits.map((h) => ({ ...h, matchSource: "tamil" as const })));
      setV2NextCursor(res.next_cursor);
      setV2HasMore(Boolean(res.has_more && res.next_cursor));
      setV2CanonicalPrefix(res.canonical_prefix);
    } catch {
      setV2BrowseHits([]);
      setV2NextCursor(undefined);
      setV2HasMore(false);
      setV2CanonicalPrefix("");
    }
  }, [
    ready,
    v2Stats.pack_count,
    v2Stats.total_entries,
    v2BrowsePrefix,
    isAsciiQuery,
    isNonTamilNonAsciiQuery,
    query,
    effectiveTier,
    selectedCategory,
    v2Folded,
    selectedPos,
    v2Domain,
    selectedRegion,
    selectedRegister,
  ]);

  const handleLoadMoreV2 = useCallback(() => {
    if (!ready || !v2HasMore || !v2NextCursor || v2LoadingMore) return;
    setV2LoadingMore(true);
    try {
      const opts = buildV2SearchOptions({
        tier: effectiveTier,
        category: selectedCategory,
        folded: v2Folded && query.trim().length > 0,
        pos: selectedPos,
        domain: v2Domain,
        region: selectedRegion,
        register: selectedRegister,
        limit: 200,
        after_key: v2NextCursor,
      });
      const res = searchLexiconV2(v2BrowsePrefix, opts);
      setV2BrowseHits((prev) => {
        const seen = new Set(prev.map((h) => h.headword));
        const appended = res.hits.filter((h) => !seen.has(h.headword));
        return [...prev, ...appended];
      });
      setV2NextCursor(res.next_cursor);
      setV2HasMore(Boolean(res.has_more && res.next_cursor));
    } catch {
      setV2HasMore(false);
    } finally {
      setV2LoadingMore(false);
    }
  }, [
    ready,
    v2HasMore,
    v2NextCursor,
    v2LoadingMore,
    effectiveTier,
    selectedCategory,
    v2Folded,
    query,
    selectedPos,
    v2Domain,
    selectedRegion,
    selectedRegister,
    v2BrowsePrefix,
  ]);

  // Unified Word Definition (`lexicon_define`) for activeWord whenever v2 packs are mounted
  useEffect(() => {
    if (!ready || v2Stats.pack_count === 0) {
      setV2Definition(null);
      return;
    }
    const target = activeWord.trim();
    if (!target) {
      setV2Definition(null);
      return;
    }
    const seq = ++defineRequestSeqRef.current;
    const t0 = performance.now();
    const qOpts = buildV2QueryOptions({
      tier: effectiveTier,
      category: selectedCategory,
      folded: v2Folded,
      pos: selectedPos,
      domain: v2Domain,
      region: selectedRegion,
      register: selectedRegister,
    });

    defineLexiconV2(target, qOpts)
      .then((def) => {
        if (defineRequestSeqRef.current !== seq) return;
        setV2LatencyMs(performance.now() - t0);
        setV2Definition(def);
        if (!lookupError) {
          setLastRawRequest(
            JSON.stringify({ op: "lexicon_define", input: target, ...qOpts }, null, 2)
          );
          setLastRawResponse(JSON.stringify(def, null, 2));
        }
      })
      .catch(() => {
        if (defineRequestSeqRef.current !== seq) return;
        setV2LatencyMs(performance.now() - t0);
        setV2Definition(null);
      });
  }, [
    ready,
    v2Stats.pack_count,
    v2Stats.total_entries,
    v2Stats.total_relations,
    activeWord,
    effectiveTier,
    selectedCategory,
    v2Folded,
    selectedPos,
    v2Domain,
    selectedRegion,
    selectedRegister,
    lookupError,
  ]);

  const handleLoadV2Tier = async (tier: tt.LexiconPackTier) => {
    if (!ready || !v2Manifest) return;
    const actionKey = tier === "verified_open" ? "open" : "local";
    setV2LoadingAction(actionKey);
    setV2Error(null);
    try {
      await lexiconV2Manager.fetchAndMountTier(v2Manifest, tier);
      setV2Stats(lexiconV2Manager.syncFromEngine());
    } catch (err: unknown) {
      setV2Error(err instanceof Error ? err.message : String(err));
    } finally {
      setV2LoadingAction(null);
    }
  };

  const handleToggleV2ManifestPack = async (entry: TlpackManifestEntry) => {
    if (!ready) return;
    const packId = entry.summary.pack_id;
    setV2LoadingAction(packId);
    setV2Error(null);
    try {
      if (v2MountedIds.has(packId)) {
        lexiconV2Manager.unloadPack(packId);
      } else {
        await lexiconV2Manager.fetchAndMountPack(entry);
      }
      setV2Stats(lexiconV2Manager.syncFromEngine());
    } catch (err: unknown) {
      setV2Error(err instanceof Error ? err.message : String(err));
    } finally {
      setV2LoadingAction(null);
    }
  };

  const handleLocalTlpackFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !ready) return;
    setV2LoadingAction("file");
    setV2Error(null);
    try {
      const result = await lexiconV2Manager.mountLocalFiles(files);
      setV2Stats(lexiconV2Manager.syncFromEngine());
      if (result.errors.length > 0) {
        setV2Error(
          result.errors.map((err) => `${err.fileName}: ${err.message}`).join(" · ")
        );
      }
    } catch (err: unknown) {
      setV2Error(err instanceof Error ? err.message : String(err));
    } finally {
      setV2LoadingAction(null);
      e.target.value = "";
    }
  };

  const handleUnloadAllV2 = () => {
    if (!ready) return;
    lexiconV2Manager.clearAll();
    setV2Stats(lexiconV2Manager.syncFromEngine());
    setV2Definition(null);
    setV2Error(null);
  };

  // Handle subsequent quick searches dispatched from Home
  useEffect(() => {
    if (!initialQueryNonce || initialQueryNonce === lastConsumedNonceRef.current) return;
    const trimmed = initialQuery?.trim();
    if (!trimmed) return;
    lastConsumedNonceRef.current = initialQueryNonce;
    setViewMode("verified");
    setQuery(trimmed);
    setActiveWord(trimmed);
    setLookupError(null);
    if (extendedManifest) {
      const bucket = findExtendedLetterBucket(trimmed, extendedManifest.letters);
      setSelectedLetter(bucket ? bucket.id : "ALL");
    } else {
      setSelectedLetter("ALL");
    }
    if (ready) {
      const packs = selectedPacks.length > 0 ? selectedPacks : availablePackIds;
      executeLookup(trimmed, {
        packs,
        region: selectedRegion === "" ? undefined : selectedRegion,
        register: selectedRegister === "" ? undefined : selectedRegister,
      });
    } else {
      void loadExtendedDetail(trimmed);
    }
  }, [
    initialQueryNonce,
    initialQuery,
    extendedManifest,
    ready,
    selectedPacks,
    availablePackIds,
    selectedRegion,
    selectedRegister,
    executeLookup,
    loadExtendedDetail,
  ]);

  useEffect(() => {
    const validRegions = new Set<string>([...scopeOptions.regions, ...v2Regions]);
    if (selectedRegion && validRegions.size > 0 && !validRegions.has(selectedRegion)) {
      setSelectedRegion("");
    }
    if (selectedRegister && !scopeOptions.registers.includes(selectedRegister)) {
      setSelectedRegister("");
    }
  }, [scopeOptions, v2Regions, selectedRegion, selectedRegister]);

  const selectWord = useCallback(
    (nextWord: string, syncInput: boolean = true) => {
      setLookupError(null);
      setActiveWord(nextWord);
      if (syncInput) {
        setQuery(nextWord);
      }
      setAutocompleteOpen(false);
      if (!ready || availablePackIds.length === 0) {
        void loadExtendedDetail(nextWord);
        return;
      }
      const packsToUse = selectedPacks.length > 0 ? selectedPacks : availablePackIds;
      const legacyRegion =
        selectedRegion && scopeOptions.regions.includes(selectedRegion)
          ? selectedRegion
          : undefined;
      const legacyRegister =
        selectedRegister && scopeOptions.registers.includes(selectedRegister)
          ? selectedRegister
          : undefined;
      if (selectedRegion && !legacyRegion && v2Stats.pack_count > 0) {
        // Region is a v2-only dialect (e.g. GEN_Z, SPOKEN, CHENNAI); v2 define handles it directly.
        return;
      }
      executeLookup(nextWord, {
        packs: packsToUse,
        region: legacyRegion,
        register: legacyRegister,
      });
    },
    [
      ready,
      availablePackIds,
      selectedPacks,
      selectedRegion,
      selectedRegister,
      scopeOptions.regions,
      scopeOptions.registers,
      v2Stats.pack_count,
      executeLookup,
      loadExtendedDetail,
    ]
  );

  const runCurrentFormLookup = (
    overrideQuery = query,
    overridePacks = selectedPacks,
    overrideRegion = selectedRegion,
    overrideRegister = selectedRegister
  ) => {
    if (!ready) return;
    setLookupError(null);
    setActiveWord(overrideQuery);
    if (availablePackIds.length === 0) {
      void loadExtendedDetail(overrideQuery);
      return;
    }
    const legacyRegion =
      overrideRegion && scopeOptions.regions.includes(overrideRegion)
        ? overrideRegion
        : undefined;
    const legacyRegister =
      overrideRegister && scopeOptions.registers.includes(overrideRegister)
        ? overrideRegister
        : undefined;
    if (overrideRegion && !legacyRegion && v2Stats.pack_count > 0) {
      return;
    }
    executeLookup(overrideQuery, {
      packs: overridePacks,
      region: legacyRegion,
      register: legacyRegister,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAutocompleteOpen(false);
    const trimmed = query.trim();
    if (!trimmed) return;
    const hasTamil = /[\u0B80-\u0BFF]/.test(trimmed);
    if (!hasTamil) {
      if (isV2Active && v2Hits.length > 0) {
        selectWord(v2Hits[0].headword, false);
        return;
      }
      if (tanglishSuggestions.length > 0) {
        selectWord(tanglishSuggestions[0], false);
        return;
      }
      if (fallbackSuggestions.length > 0) {
        selectWord(fallbackSuggestions[0].word, false);
        return;
      }
    }
    selectWord(query, false);
  };

  const handleTogglePack = (packId: tt.LexiconPackId) => {
    const next = selectedPacks.includes(packId)
      ? selectedPacks.filter((p) => p !== packId)
      : [...selectedPacks, packId];
    setSelectedPacks(next);
    if (ready) {
      runCurrentFormLookup(activeWord, next, selectedRegion, selectedRegister);
    }
  };

  const handleExampleClick = (ex: LexiconExampleItem) => {
    setLookupError(null);
    setQuery(ex.query);
    setActiveWord(ex.query);
    setSelectedLetter("ALL");
    setSelectedCategory("all");
    setSelectedRegion("");
    setSelectedRegister("");
    setAutocompleteOpen(false);
    const allHintAvailable = ex.packHint.every((p) => availablePackSet.has(p));
    const nextPacks = allHintAvailable
      ? Array.from(new Set([...selectedPacks, ...ex.packHint])).filter((p) =>
          availablePackSet.has(p)
        )
      : [...ex.packHint];

    if (allHintAvailable) {
      setSelectedPacks(nextPacks);
    }
    if (ready && availablePackIds.length > 0) {
      executeLookup(ex.query, { packs: nextPacks });
    } else {
      void loadExtendedDetail(ex.query);
    }
  };

  const handlePresetClick = (preset: ContractTestPreset) => {
    if (!ready) return;
    setQuery(preset.query);
    setActiveWord(preset.query);
    setAutocompleteOpen(false);
    if (preset.useAvailablePacks && availablePackIds.length === 0) {
      void loadExtendedDetail(preset.query);
      return;
    }
    const packs = preset.useAvailablePacks
      ? availablePackIds
      : preset.packs;
    executeLookup(preset.query, {
      packs,
      region: preset.region,
      register: preset.register,
    });
  };

  const handleChooserKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (IS_PUBLIC_BETA) return;
    if (
      e.key === "ArrowRight" ||
      e.key === "ArrowLeft" ||
      e.key === "Home" ||
      e.key === "End"
    ) {
      e.preventDefault();
      if (e.key === "Home") {
        setViewMode("verified");
      } else if (e.key === "End") {
        setViewMode("historical");
      } else {
        setViewMode((prev) => (prev === "verified" ? "historical" : "verified"));
      }
    }
  };

  const totalActiveWords =
    v2Stats.pack_count > 0
      ? v2Stats.packs.reduce((sum, p) => sum + p.distinct_headwords, 0)
      : extendedManifest?.total_words ?? browseIndex?.count ?? 9410;
  const alphabetBuckets = extendedManifest?.letters ?? browseIndex?.letters ?? [];
  const posList = useMemo(() => {
    const set = new Set<string>(extendedManifest?.pos ?? browseIndex?.pos ?? []);
    set.add("PHRASE");
    for (const pack of v2Stats.packs) {
      const maybePos = (pack as { pos?: string[] }).pos;
      if (Array.isArray(maybePos)) {
        for (const p of maybePos) {
          if (p) set.add(p);
        }
      }
    }
    for (const hit of v2BrowseHits) {
      for (const p of hit.pos) {
        if (p) set.add(p);
      }
    }
    if (v2Definition?.pos) {
      for (const p of v2Definition.pos) {
        if (p) set.add(p);
      }
    }
    return Array.from(set);
  }, [extendedManifest, browseIndex, v2Stats.packs, v2BrowseHits, v2Definition]);

  const v2Hits = useMemo(() => {
    const raw = v2BrowseHits;
    const trimmedQuery = query.trim();
    if (isAsciiQuery || raw.length <= 1 || trimmedQuery.length === 0) return raw;
    const canonicalPrefix = v2CanonicalPrefix || trimmedQuery;
    const sorted = [...raw];
    sorted.sort((a, b) => {
      const aExact = a.headword === canonicalPrefix || a.matched_key === canonicalPrefix;
      const bExact = b.headword === canonicalPrefix || b.matched_key === canonicalPrefix;
      if (aExact !== bExact) return aExact ? -1 : 1;
      if (ready) {
        try {
          const cmp = tt.compare(a.headword, b.headword);
          if (cmp !== 0) return cmp;
        } catch {
          // Fall back to Unicode codepoint order if collate is unavailable
        }
      }
      return a.headword < b.headword ? -1 : a.headword > b.headword ? 1 : 0;
    });
    return sorted;
  }, [v2BrowseHits, v2CanonicalPrefix, query, ready, isAsciiQuery]);
  const autocompleteHits = useMemo(
    () => (query.trim().length > 0 ? v2Hits.slice(0, 10) : []),
    [query, v2Hits]
  );

  const allOpenMounted =
    v2OpenManifestPacks.length > 0 &&
    v2OpenManifestPacks.every((p) => v2MountedIds.has(p.summary.pack_id));
  const allLocalMounted =
    v2LocalManifestPacks.length > 0 &&
    v2LocalManifestPacks.every((p) => v2MountedIds.has(p.summary.pack_id));

  const scopedV2Totals = useMemo(() => {
    const matchingPacks = v2Stats.packs.filter((p) => {
      if (effectiveTier === "open" && p.pack_tier !== "verified_open") return false;
      const cat = p.category ?? packCategory(p.pack_id);
      if (selectedCategory !== "all" && cat !== selectedCategory) return false;
      return true;
    });
    const entries = matchingPacks.reduce((sum, p) => sum + p.entry_count, 0);
    const headwords = matchingPacks.reduce((sum, p) => sum + p.distinct_headwords, 0);
    const isCompleteFullUnion =
      selectedCategory === "all" &&
      effectiveTier === "all" &&
      allOpenMounted &&
      allLocalMounted;
    const isCompleteOpenUnion =
      selectedCategory === "all" &&
      effectiveTier === "open" &&
      allOpenMounted;
    return {
      packCount: matchingPacks.length,
      entries,
      headwords,
      isCompleteFullUnion,
      isCompleteOpenUnion,
    };
  }, [v2Stats.packs, effectiveTier, selectedCategory, allOpenMounted, allLocalMounted]);

  const showV2PrefixHits =
    v2Stats.pack_count > 0 &&
    !isNonTamilNonAsciiQuery &&
    (leftPaneMode === "v2" || leftPaneMode === "auto");

  const v2TotalPages = Math.max(1, Math.ceil(v2Hits.length / PAGE_SIZE));
  const safeV2Page = Math.min(page, v2TotalPages);
  const pagedV2Hits = useMemo(() => {
    const start = (safeV2Page - 1) * PAGE_SIZE;
    return v2Hits.slice(start, start + PAGE_SIZE);
  }, [v2Hits, safeV2Page]);

  const v2SidebarCountLabel = useMemo(() => {
    const hasNarrowFilters =
      query.trim().length > 0 ||
      selectedLetter !== "ALL" ||
      selectedPos !== "ALL" ||
      v2Domain !== "ALL" ||
      Boolean(selectedRegion) ||
      Boolean(selectedRegister);
    const hitSuffix = v2HasMore ? "+" : "";

    if (query.trim().length > 0 && isAsciiQuery) {
      return language === "ta"
        ? `ஆங்கிலம் & தங்கிலிஷ் · ${v2Hits.length}${hitSuffix}`
        : `English & Tanglish · ${v2Hits.length}${hitSuffix}`;
    }
    if (query.trim().length > 0) {
      return language === "ta"
        ? `முன்னொட்டுத் தேடல் · ${v2Hits.length}${hitSuffix}`
        : `Prefix Matches · ${v2Hits.length}${hitSuffix}`;
    }
    if (selectedLetter !== "ALL") {
      return language === "ta"
        ? `${selectedLetter} · ${v2Hits.length.toLocaleString()}${hitSuffix} சொற்கள்`
        : `${selectedLetter} · ${v2Hits.length.toLocaleString()}${hitSuffix} words`;
    }
    if (hasNarrowFilters) {
      return language === "ta"
        ? `${v2Hits.length.toLocaleString()}${hitSuffix} சொற்கள்`
        : `${v2Hits.length.toLocaleString()}${hitSuffix} words`;
    }
    if (scopedV2Totals.isCompleteFullUnion) {
      return language === "ta" ? "241,127 சொற்கள்" : "241,127 words";
    }
    if (scopedV2Totals.isCompleteOpenUnion) {
      return language === "ta" ? "90,167 சொற்கள்" : "90,167 words";
    }
    if (scopedV2Totals.packCount === 1) {
      return language === "ta"
        ? `${scopedV2Totals.headwords.toLocaleString()} சொற்கள்`
        : `${scopedV2Totals.headwords.toLocaleString()} words`;
    }
    return language === "ta"
      ? `${scopedV2Totals.entries.toLocaleString()} பதிவுகள்`
      : `${scopedV2Totals.entries.toLocaleString()} entries`;
  }, [
    query,
    selectedLetter,
    selectedPos,
    v2Domain,
    selectedRegion,
    selectedRegister,
    v2Hits.length,
    v2HasMore,
    scopedV2Totals,
    language,
    isAsciiQuery,
  ]);

  const isV2Active = v2Stats.pack_count > 0;
  const hasV2DefinitionMatch = Boolean(v2Definition && v2Definition.status === "matched");
  const hasLegacyMatch =
    Boolean(response && response.status === "matched") || Boolean(extendedEntry);

  const v2FuzzySuggestions = useMemo(() => {
    if (!ready || !isV2Active || v2Definition?.status !== "not_found") return [];
    const target = activeWord.trim();
    if (!target) return [];
    try {
      return fuzzySearchLexiconV2(target, {
        max_distance: 2,
        tier: effectiveTier,
        limit: 6,
      }).hits;
    } catch {
      return [];
    }
  }, [ready, isV2Active, v2Definition, activeWord, effectiveTier]);

  const v2LongestPrefixes = useMemo(() => {
    if (!ready || !isV2Active || v2Definition?.status !== "not_found") return [];
    const target = activeWord.trim();
    if (!target) return [];
    try {
      return getLexiconLongestPrefixes(target, {
        tier: effectiveTier,
      }).prefixes.filter((p) => p !== target);
    } catch {
      return [];
    }
  }, [ready, isV2Active, v2Definition, activeWord, effectiveTier]);

  const mergedRegionOptions = useMemo(() => {
    const byCode = new Map<string, { code: string; parent_code?: string }>();
    for (const r of scopeOptions.regionEntries) {
      if (r.attestedInSelectedPacks || v2Regions.includes(r.code)) {
        byCode.set(r.code, { code: r.code, parent_code: r.parent_code });
      }
    }
    for (const code of v2Regions) {
      if (!byCode.has(code)) {
        byCode.set(code, { code });
      }
    }
    return Array.from(byCode.values()).sort((a, b) => a.code.localeCompare(b.code));
  }, [scopeOptions.regionEntries, v2Regions]);

  // Group manifest packs by category for the Developer Tools table
  const groupedManifestPacks = useMemo(() => {
    const allEntries = [...v2OpenManifestPacks, ...v2LocalManifestPacks];
    const groups = new Map<LexiconCategory, TlpackManifestEntry[]>();
    for (const entry of allEntries) {
      const cat = entry.summary.category ?? packCategory(entry.summary.pack_id);
      const list = groups.get(cat) ?? [];
      list.push(entry);
      groups.set(cat, list);
    }
    return Array.from(groups.entries());
  }, [v2OpenManifestPacks, v2LocalManifestPacks]);

  const headerStatusPill = useMemo(() => {
    if (!ready) {
      return (
        <Badge variant="mono" className="text-[11px]">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>{language === "ta" ? "பொறி ஏற்றப்படுகிறது…" : "Booting WASM…"}</span>
        </Badge>
      );
    }
    if (v2Progress && !v2Progress.done) {
      const label =
        datasetScope === "full" && !IS_OPEN_ONLY_CHANNEL
          ? language === "ta"
            ? `முழு அகராதி… ${v2Progress.loadedPacks}/${v2Progress.totalPacks}`
            : `Loading full dictionary… ${v2Progress.loadedPacks}/${v2Progress.totalPacks}`
          : language === "ta"
            ? `திறந்த அகராதி… ${v2Progress.loadedPacks}/${v2Progress.totalPacks}`
            : `Loading open dictionary… ${v2Progress.loadedPacks}/${v2Progress.totalPacks}`;
      return (
        <Badge variant="sandhanam" className="text-[11px]">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span>{label}</span>
        </Badge>
      );
    }
    if (v2Stats.pack_count > 0) {
      const isFullReady =
        !IS_OPEN_ONLY_CHANNEL &&
        datasetScope === "full" &&
        allOpenMounted &&
        allLocalMounted;
      const isFullPartial =
        !IS_OPEN_ONLY_CHANNEL && datasetScope === "full" && v2HasLocalMounted;
      let statusLabel: string;
      if (isFullReady) {
        statusLabel = language === "ta" ? "முழு 241k · தயார்" : "Full 241k · Ready";
      } else if (isFullPartial) {
        statusLabel =
          language === "ta"
            ? `முழு · ${v2Stats.pack_count} தொகுப்புகள்`
            : `Full · ${v2Stats.pack_count} packs`;
      } else if (allOpenMounted) {
        statusLabel = language === "ta" ? "திறந்த 90k · தயார்" : "Open 90k · Ready";
      } else {
        statusLabel =
          language === "ta"
            ? `திறந்த · ${v2Stats.pack_count} தொகுப்புகள்`
            : `Open · ${v2Stats.pack_count} ${v2Stats.pack_count === 1 ? "pack" : "packs"}`;
      }
      return (
        <Badge
          variant={isFullReady || isFullPartial ? "sandhanam" : "terracotta"}
          className="text-[11px]"
        >
          <CheckCircle2 className="w-3 h-3" />
          <span>{statusLabel}</span>
        </Badge>
      );
    }
    return (
      <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
        {totalActiveWords.toLocaleString()} {t.home.dictionaryCountSuffix}
      </span>
    );
  }, [
    ready,
    v2Progress,
    v2Stats.pack_count,
    v2HasLocalMounted,
    allOpenMounted,
    allLocalMounted,
    datasetScope,
    language,
    totalActiveWords,
    t.home.dictionaryCountSuffix,
  ]);

  const modeSwitcher = (
    <div
      role="tablist"
      aria-label={language === "ta" ? "சொற்களஞ்சியப் பார்வைத் தேர்வு" : "Lexicon mode chooser"}
      onKeyDown={handleChooserKeyDown}
      className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]"
    >
      <button
        id="lexicon-tab-verified"
        type="button"
        role="tab"
        aria-selected={viewMode === "verified"}
        aria-controls="lexicon-panel-verified"
        tabIndex={viewMode === "verified" ? 0 : -1}
        onClick={() => setViewMode("verified")}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
          viewMode === "verified"
            ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
            : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
        }`}
      >
        <BookMarked className="w-3.5 h-3.5 shrink-0" />
        <span>{language === "ta" ? "அகராதி" : "Dictionary"}</span>
      </button>

      <button
        id="lexicon-tab-historical"
        type="button"
        role="tab"
        aria-selected={viewMode === "historical"}
        aria-controls="lexicon-panel-historical"
        tabIndex={viewMode === "historical" ? 0 : -1}
        onClick={() => setViewMode("historical")}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
          viewMode === "historical"
            ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
            : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
        }`}
      >
        <Database className="w-3.5 h-3.5 shrink-0" />
        <span>
          {language === "ta" ? "வரலாற்றுப் பதிவுகள்" : "Historical Archive"}
        </span>
      </button>
    </div>
  );

  const showHistoricalMode = !IS_PUBLIC_BETA && viewMode === "historical";

  return (
    <div className="space-y-6">
      {showHistoricalMode ? (
        <div
          id="lexicon-panel-historical"
          role="tabpanel"
          aria-labelledby="lexicon-tab-historical"
        >
          <Suspense
            fallback={
              <div className="py-12 flex items-center justify-center gap-2 text-sm text-[var(--color-muted)]">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)]" />
                <span>{t.shell.engineLoading}</span>
              </div>
            }
          >
            <LazyHistoricalSourceExplorer engineReady={ready} headerActions={modeSwitcher} />
          </Suspense>
        </div>
      ) : (
        <div
          id="lexicon-panel-verified"
          role="tabpanel"
          aria-labelledby="lexicon-tab-verified"
          className="space-y-5"
        >
          <ToolHeader
            title={t.tools.lexicon.title}
            description={t.tools.lexicon.desc}
            meta={
              <div className="flex flex-wrap items-center gap-2">
                {headerStatusPill}
                {v2Stats.pack_count > 0 && (
                  <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                    {v2Stats.total_entries.toLocaleString()}{" "}
                    {language === "ta" ? "பதிவுகள்" : "entries"}
                    {v2Stats.total_relations > 0
                      ? ` · ${v2Stats.total_relations.toLocaleString()} ${
                          language === "ta" ? "தொடர்புகள்" : "relations"
                        }`
                      : ""}
                  </span>
                )}
              </div>
            }
            actions={!IS_PUBLIC_BETA ? modeSwitcher : undefined}
          />

          {/* Loading / Error Banners */}
          {!ready && (
            <Card className="p-4 flex items-center gap-3">
              <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)] shrink-0" />
              <div className="space-y-0.5">
                <span className="text-sm font-semibold text-[var(--color-mai)] block">
                  {t.tools.lexicon.loadingEngine}
                </span>
                <span className="text-xs text-[var(--color-muted)]">
                  {t.tools.lexicon.firstLoadSizeNote}
                </span>
              </div>
            </Card>
          )}

          {packsError && (
            <Card className="p-4 border-red-500/40 bg-red-500/10 text-xs font-mono-tamil text-red-700 dark:text-red-300">
              {packsError}
            </Card>
          )}

          {/* Clean, Intuitive Search & Filter Controls */}
          <Card className="p-4 sm:p-5 space-y-3.5">
            <div ref={searchBoxRef} className="relative">
              <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 text-[var(--color-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    id="lexicon-query-input"
                    type="text"
                    value={query}
                    autoComplete="off"
                    onFocus={() => {
                      if (query.trim().length > 0) setAutocompleteOpen(true);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Escape") setAutocompleteOpen(false);
                    }}
                    onChange={(e) => {
                      const val = e.target.value;
                      setQuery(val);
                      setAutocompleteOpen(val.trim().length > 0);
                      if (selectedLetter !== "ALL") setSelectedLetter("ALL");
                    }}
                    placeholder={
                      language === "ta"
                        ? `தமிழ், தங்கிலிஷ் அல்லது ஆங்கிலத்தில் தேடுங்கள் (எ.கா. தமிழ், nandri, gratitude, water)...`
                        : `Look up Tamil, Tanglish, or English (e.g. தமிழ், nandri, gratitude, water)...`
                    }
                    aria-label={t.tools.lexicon.searchLabel}
                    aria-expanded={autocompleteOpen && query.trim().length > 0}
                    className="w-full min-h-[44px] pl-10 pr-10 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm sm:text-base font-tamil text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
                  />
                  {query && (
                    <button
                      type="button"
                      onClick={() => {
                        setQuery("");
                        setAutocompleteOpen(false);
                        setSelectedLetter("ALL");
                      }}
                      aria-label={t.actions.clear}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-[var(--color-muted)] hover:text-[var(--color-mai)] hover:bg-[var(--bg-raised)] cursor-pointer"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <Button type="submit" variant="primary" size="md" className="shrink-0">
                  <Search className="w-4 h-4 mr-1.5" />
                  <span>{t.tools.lexicon.searchButton}</span>
                </Button>
              </form>

              {/* Instant Autocomplete Dropdown */}
              {autocompleteOpen &&
                query.trim().length > 0 &&
                (isV2Active
                  ? autocompleteHits.length > 0 || (isAsciiQuery && tanglishSuggestions.length > 0)
                  : fallbackSuggestions.length > 0 || (isAsciiQuery && tanglishSuggestions.length > 0)) && (
                  <div
                    role="listbox"
                    aria-label={
                      language === "ta" ? "உடனடி சொல் பரிந்துரைகள்" : "Instant suggestions"
                    }
                    className="absolute left-0 right-0 z-30 mt-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] shadow-lg overflow-hidden divide-y divide-[var(--border-line)]/60 max-h-80 overflow-y-auto"
                  >
                    {isAsciiQuery && tanglishSuggestions.length > 0 && (
                      <div className="px-3.5 py-2 bg-[var(--bg-raised)]/50 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                          {language === "ta" ? "தங்கிலிஷ்:" : "Tanglish:"}
                        </span>
                        {tanglishSuggestions.map((cand) => (
                          <button
                            key={`tg-${cand}`}
                            type="button"
                            onClick={() => selectWord(cand, true)}
                            className="px-2 py-0.5 rounded-full border border-[var(--color-sandhanam)]/60 bg-[var(--bg-surface)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] text-xs font-tamil text-[var(--color-mai)] transition-colors cursor-pointer"
                          >
                            {cand}
                          </button>
                        ))}
                      </div>
                    )}
                    {isV2Active
                      ? autocompleteHits.map((hit) => (
                          <button
                            key={`ac-${hit.headword}-${hit.packs.join(",")}`}
                            type="button"
                            role="option"
                            aria-selected={activeWord === hit.headword}
                            onClick={() => selectWord(hit.headword, !isAsciiQuery)}
                            className="w-full text-left px-3.5 py-2.5 hover:bg-[var(--bg-raised)]/80 transition-colors cursor-pointer flex items-center justify-between gap-2"
                          >
                            <div className="min-w-0 flex-1">
                              <div className="flex flex-wrap items-baseline gap-2">
                                <span className="text-sm font-tamil font-semibold text-[var(--color-mai)]">
                                  {hit.headword}
                                </span>
                                {hit.matched_key !== hit.headword && (
                                  <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                                    ← {hit.matched_key}
                                  </span>
                                )}
                              </div>
                              {hit.preview_gloss && (
                                <p className="text-xs text-[var(--color-muted)] truncate">
                                  {hit.preview_gloss}
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-1 shrink-0">
                              {hit.matchSource === "english" && (
                                <Badge
                                  variant="outline"
                                  title={language === "ta" ? "ஆங்கிலப் பொருள் பொருத்தம்" : "English match"}
                                  className="text-[9px] px-1.5 py-0"
                                >
                                  EN
                                </Badge>
                              )}
                              {hit.matchSource === "tanglish" && (
                                <Badge variant="sandhanam" className="text-[9px] px-1.5 py-0">
                                  Tanglish
                                </Badge>
                              )}
                              {hit.pack_tiers.includes("verified_open") && (
                                <Badge variant="terracotta" className="text-[9px] px-1.5 py-0">
                                  Open
                                </Badge>
                              )}
                              {hit.pack_tiers.includes("local_historical") && (
                                <Badge variant="sandhanam" className="text-[9px] px-1.5 py-0">
                                  Local
                                </Badge>
                              )}
                              {hit.pos.slice(0, 1).map((p) => (
                                <span
                                  key={p}
                                  className="text-[10px] font-mono-tamil text-[var(--color-muted)] bg-[var(--bg-canvas)] border border-[var(--border-line)] rounded px-1.5 py-0.5"
                                >
                                  {p}
                                </span>
                              ))}
                            </div>
                          </button>
                        ))
                      : fallbackSuggestions.map((item) => (
                          <button
                            key={`ac-fb-${item.word}`}
                            type="button"
                            role="option"
                            aria-selected={activeWord === item.word}
                            onClick={() => selectWord(item.word, !isAsciiQuery)}
                            className="w-full text-left px-3.5 py-2.5 hover:bg-[var(--bg-raised)]/80 transition-colors cursor-pointer flex items-center justify-between gap-2"
                          >
                            <div className="min-w-0 flex-1">
                              <span className="text-sm font-tamil font-semibold text-[var(--color-mai)] block">
                                {item.word}
                              </span>
                              {item.gloss && (
                                <p className="text-xs text-[var(--color-muted)] truncate">
                                  {item.gloss}
                                </p>
                              )}
                            </div>
                            {item.pos.slice(0, 1).map((p) => (
                              <span
                                key={p}
                                className="text-[10px] font-mono-tamil text-[var(--color-muted)] bg-[var(--bg-canvas)] border border-[var(--border-line)] rounded px-1.5 py-0.5 shrink-0"
                              >
                                {p}
                              </span>
                            ))}
                          </button>
                        ))}
                  </div>
                )}
            </div>

            {/* Primary Controls: Mayangoli Folded + Dataset Switch + POS/Domain/Dialect */}
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                aria-pressed={v2Folded}
                onClick={() => setV2Folded((prev) => !prev)}
                title={
                  language === "ta"
                    ? "ல/ள/ழ, ன/ண, ர/ற எழுத்து வேறுபாடின்றித் தேடுங்கள்"
                    : "Spelling-tolerant search across ல/ள/ழ, ன/ண, ர/ற (e.g. தமில் → தமிழ்)"
                }
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] rounded-full text-xs font-medium border transition-colors cursor-pointer ${
                  v2Folded
                    ? "bg-[var(--color-sandhanam)] text-[#faf7f2] border-[var(--color-sandhanam)]"
                    : "bg-[var(--bg-canvas)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-sandhanam)]"
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 shrink-0" />
                <span>
                  {language === "ta" ? "மயங்கொலி மடிப்பு" : "Mayangoli Folded"}
                </span>
              </button>

              {/* Dataset Switch: Verified Open (90k) vs Full Archive (241k) */}
              {IS_OPEN_ONLY_CHANNEL ? (
                <Badge variant="terracotta" className="text-xs py-1 px-3">
                  {language === "ta"
                    ? "சரிபார்க்கப்பட்ட திறந்த தொகுப்பு (90k)"
                    : "Verified Open (90k)"}
                </Badge>
              ) : (
                <div
                  role="group"
                  aria-label={language === "ta" ? "தொகுப்பு வரம்பு" : "Dataset scope"}
                  className="inline-flex items-center gap-1 p-0.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)]"
                >
                  <button
                    type="button"
                    aria-pressed={datasetScope === "open"}
                    onClick={() => {
                      setDatasetScope("open");
                      if (ready) {
                        const removed = lexiconV2Manager.unloadLocalPacks();
                        if (removed.length > 0) {
                          setV2Stats(lexiconV2Manager.syncFromEngine());
                        }
                      }
                    }}
                    className={`px-2.5 py-1 min-h-[32px] rounded-md text-xs font-medium transition-colors cursor-pointer ${
                      datasetScope === "open"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                    }`}
                  >
                    {language === "ta"
                      ? "சரிபார்க்கப்பட்ட திறந்த தொகுப்பு (90k)"
                      : "Verified Open (90k)"}
                  </button>
                  <button
                    type="button"
                    aria-pressed={datasetScope === "full"}
                    onClick={() => setDatasetScope("full")}
                    className={`px-2.5 py-1 min-h-[32px] rounded-md text-xs font-medium transition-colors cursor-pointer ${
                      datasetScope === "full"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                    }`}
                  >
                    {language === "ta"
                      ? "முழுக் காப்பகம் (241k)"
                      : "Full Archive (241k)"}
                  </button>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
                <div className="relative inline-flex items-center">
                  <select
                    id="lexicon-pos-select"
                    value={selectedPos}
                    onChange={(e) => setSelectedPos(e.target.value)}
                    aria-label={language === "ta" ? "சொல்வகை" : "Part of speech"}
                    className="appearance-none min-h-[36px] pl-3 pr-9 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] focus:border-[var(--color-semman)] focus-visible:outline-none cursor-pointer"
                  >
                    <option value="ALL">
                      {language === "ta" ? "அனைத்து சொல்வகைகள்" : "All parts of speech"}
                    </option>
                    {posList.map((p) => (
                      <option key={p} value={p}>
                        {formatPosLabel(p, language)}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2" />
                </div>

                <div className="relative inline-flex items-center">
                  <select
                    id="lexicon-domain-select"
                    value={v2Domain}
                    onChange={(e) => setV2Domain(e.target.value)}
                    aria-label={language === "ta" ? "துறை" : "Domain"}
                    className="appearance-none min-h-[36px] pl-3 pr-9 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] focus:border-[var(--color-semman)] focus-visible:outline-none cursor-pointer max-w-[200px]"
                  >
                    <option value="ALL">
                      {language === "ta"
                        ? `அனைத்து துறைகள்${v2Domains.length > 0 ? ` (${v2Domains.length})` : ""}`
                        : `All domains${v2Domains.length > 0 ? ` (${v2Domains.length})` : ""}`}
                    </option>
                    {v2Domains.map((dom) => {
                      const count = v2DomainCounts[dom];
                      return (
                        <option key={dom} value={dom}>
                          {count ? `${dom} (${count.toLocaleString()})` : dom}
                        </option>
                      );
                    })}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2" />
                </div>

                <div className="relative inline-flex items-center">
                  <select
                    id="lexicon-region-select"
                    value={selectedRegion}
                    onChange={(e) => {
                      const val = e.target.value;
                      setLookupError(null);
                      setSelectedRegion(val);
                      if (
                        ready &&
                        activeWord &&
                        availablePackIds.length > 0 &&
                        (!val || scopeOptions.regions.includes(val))
                      ) {
                        runCurrentFormLookup(activeWord, selectedPacks, val, selectedRegister);
                      }
                    }}
                    aria-label={t.tools.lexicon.regionFilterLabel}
                    className="appearance-none min-h-[36px] pl-3 pr-9 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] focus:border-[var(--color-semman)] focus-visible:outline-none cursor-pointer"
                  >
                    <option value="">
                      {language === "ta" ? "அனைத்து வட்டாரங்கள்" : "All dialects"}
                    </option>
                    {mergedRegionOptions.map((region) => (
                      <option key={region.code} value={region.code}>
                        {region.code}
                        {region.parent_code ? ` (${region.parent_code})` : ""}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-3.5 h-3.5 text-[var(--color-muted)] pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2" />
                </div>
              </div>
            </div>

            {/* 6 Category Pills + All */}
            <div
              role="group"
              aria-label={language === "ta" ? "வகை வடிகட்டிகள்" : "Category filters"}
              className="flex flex-wrap items-center gap-1.5 pt-1"
            >
              {(() => {
                const totalEntries = LEXICON_CATEGORIES.reduce(
                  (sum, cat) => sum + (v2CategoryCounts[cat.id] ?? 0),
                  0
                );
                const allLabel = language === "ta" ? "அனைத்தும்" : "All";
                return (
                  <button
                    type="button"
                    aria-pressed={selectedCategory === "all"}
                    onClick={() => setSelectedCategory("all")}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                      selectedCategory === "all"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "bg-[var(--bg-raised)] text-[var(--color-mai)] hover:bg-[var(--color-semman-light)] hover:text-[var(--color-semman)]"
                    }`}
                  >
                    {totalEntries > 0
                      ? `${allLabel} · ${formatCompactFacetCount(totalEntries)}`
                      : allLabel}
                  </button>
                );
              })()}
              {LEXICON_CATEGORIES.map((cat) => {
                const isActive = selectedCategory === cat.id;
                const count = v2CategoryCounts[cat.id] ?? 0;
                const label = language === "ta" ? cat.label_ta : cat.label_en;
                return (
                  <button
                    key={cat.id}
                    type="button"
                    aria-pressed={isActive}
                    title={language === "ta" ? cat.description_ta : cat.description_en}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                      isActive
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "bg-[var(--bg-raised)] text-[var(--color-mai)] hover:bg-[var(--color-semman-light)] hover:text-[var(--color-semman)]"
                    }`}
                  >
                    {count > 0 ? `${label} · ${formatCompactFacetCount(count)}` : label}
                  </button>
                );
              })}
            </div>

            {/* Compact Alphabet Strip */}
            {alphabetBuckets.length > 0 && (
              <div className="pt-2.5 border-t border-[var(--border-line)]/70">
                <div className="flex items-center sm:flex-wrap gap-1 overflow-x-auto no-scrollbar pb-0.5 sm:pb-0">
                  <button
                    type="button"
                    onClick={() => setSelectedLetter("ALL")}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold shrink-0 transition-colors cursor-pointer ${
                      selectedLetter === "ALL"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "bg-[var(--bg-canvas)] border border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                    }`}
                  >
                    {language === "ta" ? "அனைத்தும்" : "All"}
                  </button>
                  {alphabetBuckets.map((bucket) => {
                    const active = selectedLetter === bucket.id;
                    return (
                      <button
                        key={bucket.id}
                        type="button"
                        onClick={() => {
                          setSelectedLetter(bucket.id);
                          setQuery("");
                          setAutocompleteOpen(false);
                        }}
                        title={`${bucket.id} (${bucket.count.toLocaleString()} words)`}
                        className={`min-w-[30px] px-2 py-1 rounded-lg text-xs sm:text-sm font-tamil font-medium shrink-0 transition-colors cursor-pointer ${
                          active
                            ? "bg-[var(--color-semman)] text-[#faf7f2]"
                            : "bg-[var(--bg-canvas)] border border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)]"
                        }`}
                      >
                        {bucket.id}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </Card>

          {/* Master-Detail Dictionary Workspace (Word Card first on mobile!) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            {/* Primary Word Definition Column (right on desktop, first on mobile) */}
            <div className="order-1 lg:order-2 lg:col-span-7 space-y-4">
              {lookupError && (
                <Card className="p-5 border-red-500/40 bg-red-500/5 space-y-3" role="alert">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2 text-red-700 dark:text-red-300 font-bold text-sm">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>{t.tools.lexicon.statusError}</span>
                    </div>
                    <Badge variant="mono">{latencyMs.toFixed(2)} ms</Badge>
                  </div>
                  <pre className="text-xs font-mono-tamil text-red-700 dark:text-red-300 whitespace-pre-wrap break-words bg-[var(--bg-surface)] border border-red-500/30 rounded-xl p-3">
                    {lookupError}
                  </pre>
                  {availablePackIds.length > 0 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedPacks(availablePackIds);
                        setSelectedRegion("");
                        setSelectedRegister("");
                        executeLookup(activeWord, { packs: availablePackIds });
                      }}
                    >
                      {t.tools.lexicon.resetToAvailablePacks}
                    </Button>
                  )}
                </Card>
              )}

              {/* ONE Unified, Merged Word Card when v2 is mounted */}
              {!lookupError && isV2Active && hasV2DefinitionMatch && v2Definition && (
                <MergedWordDefinitionCard
                  definition={v2Definition}
                  latencyMs={v2LatencyMs}
                  language={language}
                  onSelectWord={(next) => selectWord(next)}
                />
              )}

              {/* Smooth fallback to legacy card ONLY while v2 packs are booting / not mounted */}
              {!lookupError && !isV2Active && hasLegacyMatch && (
                <UnifiedWordCard
                  word={activeWord}
                  entries={response && response.status === "matched" ? response.entries : []}
                  extended={extendedEntry}
                  canonicalQuery={response?.canonical_query}
                  language={language}
                />
              )}

              {/* Empty / Not Found state */}
              {!lookupError &&
                ((isV2Active && v2Definition && !hasV2DefinitionMatch) ||
                  (!isV2Active && response && !hasLegacyMatch)) && (
                  <Card className="p-5 space-y-3">
                    <h2 className="text-base font-tamil font-bold text-[var(--color-mai)]">
                      {language === "ta"
                        ? `"${v2Definition?.canonical_query ?? response?.canonical_query ?? activeWord}" கிடைக்கவில்லை`
                        : `No exact entry for "${v2Definition?.canonical_query ?? response?.canonical_query ?? activeWord}"`}
                    </h2>

                    <div className="flex flex-wrap gap-2">
                      {selectedCategory !== "all" && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedCategory("all")}
                        >
                          {language === "ta" ? "அனைத்து வகைகளிலும் தேடு" : "Search all categories"}
                        </Button>
                      )}
                      {isV2Active && !v2Folded && (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setV2Folded(true)}
                        >
                          <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                          <span>
                            {language === "ta"
                              ? "மயங்கொலி மடிப்புடன் தேடு"
                              : "Try Mayangoli Folded Search"}
                          </span>
                        </Button>
                      )}
                    </div>

                    {v2FuzzySuggestions.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs font-semibold text-[var(--color-semman)]">
                          {language === "ta"
                            ? "நீங்கள் தேடியது இதுவா? (Did you mean?)"
                            : "Did you mean?"}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {v2FuzzySuggestions.map((hit) => (
                            <button
                              key={`fuzzy-${hit.headword}`}
                              type="button"
                              onClick={() => selectWord(hit.headword)}
                              className="px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-left transition-colors cursor-pointer"
                            >
                              <div className="flex items-center gap-1.5">
                                <span className="text-sm font-tamil font-semibold text-[var(--color-mai)]">
                                  {hit.headword}
                                </span>
                                {hit.pos.slice(0, 1).map((p) => (
                                  <Badge key={p} variant="outline" className="text-[9px] px-1.5 py-0">
                                    {p}
                                  </Badge>
                                ))}
                              </div>
                              {hit.preview_gloss && (
                                <span className="text-[11px] text-[var(--color-muted)] block max-w-[220px] truncate">
                                  {hit.preview_gloss}
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : fallbackSuggestions.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs text-[var(--color-muted)]">
                          {language === "ta"
                            ? "தொடர்புடைய சொற்கள் (தொட்டுப் பார்க்கவும்):"
                            : "Closest matching words (click to open):"}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {fallbackSuggestions.map((item) => (
                            <button
                              key={item.word}
                              type="button"
                              onClick={() => selectWord(item.word, false)}
                              className="px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-left transition-colors cursor-pointer"
                            >
                              <span className="text-sm font-tamil font-semibold text-[var(--color-mai)] block">
                                {item.word}
                              </span>
                              {item.gloss && (
                                <span className="text-[11px] text-[var(--color-muted)] block max-w-[200px] truncate">
                                  {item.gloss}
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-[var(--color-muted)] leading-relaxed">
                        {t.tools.lexicon.notFoundBody}
                      </p>
                    )}

                    {v2LongestPrefixes.length > 0 && (
                      <div className="space-y-1.5 pt-2 border-t border-[var(--border-line)]/60">
                        <p className="text-xs text-[var(--color-muted)]">
                          {language === "ta"
                            ? "சொல்லிலுள்ள முன்னொட்டுச் சொற்கள்:"
                            : "Longest matching prefixes in query:"}
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {v2LongestPrefixes.slice(0, 6).map((prefix) => (
                            <button
                              key={`lp-${prefix}`}
                              type="button"
                              onClick={() => selectWord(prefix)}
                              className="px-2.5 py-1 rounded-full border border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-xs font-tamil text-[var(--color-mai)] cursor-pointer"
                            >
                              {prefix}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </Card>
                )}

              {/* Quick Starter Words */}
              <Card className="p-4 space-y-2.5">
                <span className="text-xs font-semibold text-[var(--color-muted)] block">
                  {language === "ta" ? "எடுத்துக்காட்டுச் சொற்கள்" : "Try these words"}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {CANONICAL_LEXICON_EXAMPLES.slice(0, 8).map((ex) => (
                    <button
                      key={ex.id}
                      type="button"
                      onClick={() => handleExampleClick(ex)}
                      disabled={!ready}
                      title={language === "ta" ? ex.note_ta : ex.note_en}
                      className={`px-2.5 py-1 rounded-lg border text-xs font-tamil transition-colors cursor-pointer disabled:opacity-50 ${
                        activeWord === ex.query
                          ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold"
                          : "border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-[var(--color-mai)]"
                      }`}
                    >
                      {language === "ta" ? ex.label_ta : ex.label_en}
                    </button>
                  ))}
                </div>
              </Card>
            </div>

            {/* Browse / FST Hits Sidebar (left on desktop, second on mobile) */}
            <Card className="order-2 lg:order-1 lg:col-span-5 p-0 overflow-hidden flex flex-col">
              <div className="px-4 py-3 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/40 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-mai)]">
                  <BookOpen className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
                  <span>
                    {showV2PrefixHits
                      ? v2SidebarCountLabel
                      : selectedLetter !== "ALL"
                        ? `${selectedLetter} · ${filteredBrowseItems.length.toLocaleString()}`
                        : language === "ta"
                          ? `${filteredBrowseItems.length.toLocaleString()} சொற்கள்`
                          : `${filteredBrowseItems.length.toLocaleString()} words`}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {v2Stats.pack_count > 0 && !isNonTamilNonAsciiQuery && (
                    <div className="inline-flex items-center gap-0.5 p-0.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[10px]">
                      <button
                        type="button"
                        onClick={() => setLeftPaneMode("v2")}
                        className={`px-2 py-0.5 rounded cursor-pointer ${
                          showV2PrefixHits
                            ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold"
                            : "text-[var(--color-muted)]"
                        }`}
                      >
                        FST
                      </button>
                      <button
                        type="button"
                        onClick={() => setLeftPaneMode("browse")}
                        className={`px-2 py-0.5 rounded cursor-pointer ${
                          !showV2PrefixHits
                            ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold"
                            : "text-[var(--color-muted)]"
                        }`}
                      >
                        {language === "ta" ? "அடிப்படை" : "Index"}
                      </button>
                    </div>
                  )}
                  {showV2PrefixHits
                    ? v2TotalPages > 1 && (
                        <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                          {safeV2Page} / {v2TotalPages}
                        </span>
                      )
                    : totalPages > 1 && (
                        <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                          {safePage} / {totalPages}
                        </span>
                      )}
                </div>
              </div>

              {showV2PrefixHits && isAsciiQuery && tanglishSuggestions.length > 0 && (
                <div className="px-4 py-2 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex flex-wrap items-center gap-1.5">
                  <span className="text-[10px] font-semibold uppercase tracking-wide text-[var(--color-muted)]">
                    {language === "ta" ? "தங்கிலிஷ்:" : "Tanglish:"}
                  </span>
                  {tanglishSuggestions.map((cand) => (
                    <button
                      key={`sb-tg-${cand}`}
                      type="button"
                      onClick={() => selectWord(cand, true)}
                      className="px-2 py-0.5 rounded-full border border-[var(--color-sandhanam)]/60 bg-[var(--bg-surface)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] text-xs font-tamil text-[var(--color-mai)] transition-colors cursor-pointer"
                    >
                      {cand}
                    </button>
                  ))}
                </div>
              )}

              {showV2PrefixHits ? (
                v2Hits.length === 0 ? (
                  <div className="p-6 text-center space-y-2">
                    <p className="text-sm text-[var(--color-muted)]">
                      {query.trim()
                        ? language === "ta"
                          ? `“${query.trim()}” என்பதற்கு ஏற்ற முடிவுகள் இல்லை.`
                          : `No matches for “${query.trim()}”.`
                        : language === "ta"
                          ? "இந்த வடிகட்டிகளுக்குப் பொருந்தும் சொற்கள் இல்லை."
                          : "No words match these filters."}
                    </p>
                    {query.trim() && !isAsciiQuery && !v2Folded ? (
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => setV2Folded(true)}
                      >
                        <Sparkles className="w-3.5 h-3.5 mr-1.5" />
                        <span>
                          {language === "ta"
                            ? "மயங்கொலி மடிப்புடன் தேடு"
                            : "Try Mayangoli Folded Search"}
                        </span>
                      </Button>
                    ) : (
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setQuery("");
                          setSelectedLetter("ALL");
                          setSelectedPos("ALL");
                          setSelectedCategory("all");
                          setSelectedRegion("");
                          setV2Domain("ALL");
                        }}
                      >
                        {language === "ta" ? "வடிகட்டிகளை மீட்டமை" : "Reset filters"}
                      </Button>
                    )}
                  </div>
                ) : (
                  <ul className="divide-y divide-[var(--border-line)]/60 max-h-[540px] overflow-y-auto">
                    {pagedV2Hits.map((hit) => {
                      const isSelected = activeWord === hit.headword;
                      return (
                        <li key={`${hit.headword}:${hit.packs.join(",")}`}>
                          <button
                            type="button"
                            onClick={() => selectWord(hit.headword, !isAsciiQuery && query.trim().length > 0)}
                            className={`w-full text-left px-4 py-2.5 transition-colors cursor-pointer flex flex-col gap-1 ${
                              isSelected
                                ? "bg-[var(--color-semman-light)]/70 border-l-2 border-[var(--color-semman)]"
                                : "hover:bg-[var(--bg-raised)]/60"
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex flex-wrap items-baseline gap-1.5 min-w-0">
                                <span
                                  className={`text-sm sm:text-base font-tamil font-semibold ${
                                    isSelected
                                      ? "text-[var(--color-semman)]"
                                      : "text-[var(--color-mai)]"
                                  }`}
                                >
                                  {hit.headword}
                                </span>
                                {hit.matched_key !== hit.headword && (
                                  <span className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                                    ({hit.matched_key})
                                  </span>
                                )}
                              </div>
                              <div className="flex flex-wrap items-center gap-1 shrink-0">
                                {hit.matchSource === "english" && (
                                  <Badge
                                    variant="outline"
                                    title={language === "ta" ? "ஆங்கிலப் பொருள் பொருத்தம்" : "English match"}
                                    className="text-[9px] px-1.5 py-0"
                                  >
                                    EN
                                  </Badge>
                                )}
                                {hit.matchSource === "tanglish" && (
                                  <Badge variant="sandhanam" className="text-[9px] px-1.5 py-0">
                                    Tanglish
                                  </Badge>
                                )}
                                {hit.pack_tiers.includes("verified_open") && (
                                  <Badge variant="terracotta" className="text-[9px] px-1.5 py-0">
                                    Open
                                  </Badge>
                                )}
                                {hit.pack_tiers.includes("local_historical") && (
                                  <Badge variant="sandhanam" className="text-[9px] px-1.5 py-0">
                                    Local
                                  </Badge>
                                )}
                                {hit.pos.slice(0, 2).map((p) => (
                                  <span
                                    key={p}
                                    className="text-[10px] font-mono-tamil text-[var(--color-muted)] bg-[var(--bg-canvas)] border border-[var(--border-line)] rounded px-1.5 py-0.5"
                                  >
                                    {p}
                                  </span>
                                ))}
                              </div>
                            </div>
                            {hit.preview_gloss && (
                              <p className="text-xs text-[var(--color-muted)] truncate">
                                {hit.preview_gloss}
                              </p>
                            )}
                            <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono-tamil text-[var(--color-muted)]">
                              <span>{hit.packs.join(" · ")}</span>
                              {hit.domain && <span>· {hit.domain}</span>}
                              {hit.region && <span>· {hit.region}</span>}
                            </div>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )
              ) : browseLoading || letterLoading ? (
                <div className="p-8 flex items-center justify-center gap-2 text-xs text-[var(--color-muted)]">
                  <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)]" />
                  <span>
                    {language === "ta" ? "சொற்பட்டியல் ஏற்றப்படுகிறது..." : "Loading word list..."}
                  </span>
                </div>
              ) : browseError ? (
                <div className="p-4 text-xs text-[var(--color-muted)]">
                  {language === "ta"
                    ? "உலாவல் பட்டியல் கிடைக்கவில்லை; நேரடித் தேடலைப் பயன்படுத்தலாம்."
                    : "Browse list unavailable; direct search still works."}
                </div>
              ) : pagedItems.length === 0 ? (
                <div className="p-6 text-center space-y-2">
                  <p className="text-sm text-[var(--color-muted)]">
                    {language === "ta"
                      ? "இந்த வடிகட்டிகளுக்குப் பொருந்தும் சொற்கள் இல்லை."
                      : "No words match these filters."}
                  </p>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setQuery("");
                      setSelectedLetter("ALL");
                      setSelectedPos("ALL");
                      setSelectedCategory("all");
                      setSelectedRegion("");
                      setSelectedPacks([...availablePackIds]);
                    }}
                  >
                    {language === "ta" ? "வடிகட்டிகளை மீட்டமை" : "Reset filters"}
                  </Button>
                </div>
              ) : (
                <ul className="divide-y divide-[var(--border-line)]/60 max-h-[540px] overflow-y-auto">
                  {pagedItems.map((item) => {
                    const isSelected = activeWord === item.word;
                    return (
                      <li key={item.word}>
                        <button
                          type="button"
                          onClick={() => selectWord(item.word, selectedLetter === "ALL")}
                          className={`w-full text-left px-4 py-2.5 transition-colors cursor-pointer flex flex-col gap-0.5 ${
                            isSelected
                              ? "bg-[var(--color-semman-light)]/70 border-l-2 border-[var(--color-semman)]"
                              : "hover:bg-[var(--bg-raised)]/60"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span
                              className={`text-sm sm:text-base font-tamil font-semibold ${
                                isSelected
                                  ? "text-[var(--color-semman)]"
                                  : "text-[var(--color-mai)]"
                              }`}
                            >
                              {item.word}
                            </span>
                            <div className="flex items-center gap-1 shrink-0">
                              {item.regions.slice(0, 2).map((reg) => (
                                <Badge key={reg} variant="sandhanam" className="text-[10px] px-1.5 py-0">
                                  {reg}
                                </Badge>
                              ))}
                              {item.pos.slice(0, 2).map((p) => (
                                <span
                                  key={p}
                                  className="text-[10px] font-mono-tamil text-[var(--color-muted)] bg-[var(--bg-canvas)] border border-[var(--border-line)] rounded px-1.5 py-0.5"
                                >
                                  {p}
                                </span>
                              ))}
                            </div>
                          </div>
                          {item.gloss && (
                            <p className="text-xs text-[var(--color-muted)] truncate">
                              {item.gloss}
                            </p>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}

              {showV2PrefixHits && (v2TotalPages > 1 || v2HasMore) && (
                <div className="px-3 py-2.5 border-t border-[var(--border-line)] bg-[var(--bg-raised)]/40 space-y-2">
                  {v2TotalPages > 1 && (
                    <div className="flex items-center justify-between gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={safeV2Page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        <ChevronLeft className="w-4 h-4 mr-1" />
                        <span>{language === "ta" ? "முந்தைய" : "Prev"}</span>
                      </Button>
                      <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                        {((safeV2Page - 1) * PAGE_SIZE + 1).toLocaleString()}–
                        {Math.min(safeV2Page * PAGE_SIZE, v2Hits.length).toLocaleString()}
                        {v2HasMore ? "+" : ""}
                      </span>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={safeV2Page >= v2TotalPages}
                        onClick={() => setPage((p) => Math.min(v2TotalPages, p + 1))}
                      >
                        <span>{language === "ta" ? "அடுத்த" : "Next"}</span>
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Button>
                    </div>
                  )}
                  {safeV2Page >= v2TotalPages && v2HasMore && (
                    <div className="flex justify-center">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={v2LoadingMore}
                        onClick={handleLoadMoreV2}
                      >
                        {v2LoadingMore && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
                        <span>
                          {language === "ta"
                            ? `மேலும் ஏற்றுக (${v2Hits.length.toLocaleString()}+ ஏற்றப்பட்டது)`
                            : `Load more (${v2Hits.length.toLocaleString()}+ loaded)`}
                        </span>
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {!showV2PrefixHits && totalPages > 1 && (
                <div className="px-3 py-2.5 border-t border-[var(--border-line)] bg-[var(--bg-raised)]/40 flex items-center justify-between gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={safePage <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    <span>{language === "ta" ? "முந்தைய" : "Prev"}</span>
                  </Button>
                  <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                    {((safePage - 1) * PAGE_SIZE + 1).toLocaleString()}–
                    {Math.min(safePage * PAGE_SIZE, filteredBrowseItems.length).toLocaleString()}
                  </span>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={safePage >= totalPages}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  >
                    <span>{language === "ta" ? "அடுத்த" : "Next"}</span>
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              )}
            </Card>
          </div>

          {/* Collapsible "Manage Packs & Developer Tools" Drawer */}
          <LexiconPackDrawer
            ready={ready}
            v2Stats={v2Stats}
            v2MountedIds={v2MountedIds}
            v2LoadingAction={v2LoadingAction}
            v2Error={v2Error}
            v2OpenManifestPacks={v2OpenManifestPacks}
            v2LocalManifestPacks={v2LocalManifestPacks}
            v2ExtraMountedPacks={v2ExtraMountedPacks}
            groupedManifestPacks={groupedManifestPacks}
            allOpenMounted={allOpenMounted}
            allLocalMounted={allLocalMounted}
            onLoadV2Tier={(tier) => void handleLoadV2Tier(tier)}
            onToggleV2ManifestPack={(entry) => void handleToggleV2ManifestPack(entry)}
            onLocalTlpackFiles={(e) => void handleLocalTlpackFiles(e)}
            onUnloadAllV2={handleUnloadAllV2}
            onUnloadSingleV2Pack={(packId) => {
              lexiconV2Manager.unloadPack(packId);
              setV2Stats(lexiconV2Manager.syncFromEngine());
            }}
            onOpenHistoricalMode={() => setViewMode("historical")}
            scopeOptions={scopeOptions}
            selectedRegister={selectedRegister}
            onChangeRegister={(val) => {
              setSelectedRegister(val);
              if (ready) runCurrentFormLookup(activeWord, selectedPacks, selectedRegion, val);
            }}
            v2Domains={v2Domains}
            v2Domain={v2Domain}
            onChangeV2Domain={setV2Domain}
            queryDiagnostics={queryDiagnostics}
            loadedTotals={loadedTotals}
            catalogAlignment={catalogAlignment}
            availablePackSet={availablePackSet}
            selectedPacks={selectedPacks}
            onTogglePack={handleTogglePack}
            extendedManifest={extendedManifest}
            onPresetClick={handlePresetClick}
            lastRawRequest={lastRawRequest}
            lastRawResponse={lastRawResponse}
          />
        </div>
      )}
    </div>
  );
}
