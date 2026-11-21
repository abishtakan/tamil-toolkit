import { useState, useEffect, useMemo, useCallback, useRef, lazy, Suspense } from "react";
import * as tt from "tamil-toolkit/web";
import { getLexiconPacks, isEngineReady, lookupLexicon } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { IS_PUBLIC_BETA, resolveLexiconViewMode } from "../../lib/tools";
import { ToolHeader } from "../common/ToolHeader";
import {
  BrowseIndexData,
  BrowseWordItem,
  CANONICAL_LEXICON_EXAMPLES,
  CONTRACT_TEST_PRESETS,
  ContractTestPreset,
  ExtendedEntryDetail,
  ExtendedManifest,
  ExtendedPackId,
  LEXICON_PACK_DISPLAY_ORDER,
  LexiconExampleItem,
  POS_HUMAN_LABELS,
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
  getPackNoticeLinks,
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
  Search,
  BookMarked,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Download,
  X,
  FlaskConical,
  Loader2,
  Database,
  BookOpen,
  SlidersHorizontal,
} from "lucide-react";

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

function downloadJsonFile(filename: string, content: string) {
  if (typeof document === "undefined" || typeof URL === "undefined") return;
  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function formatPosLabel(pos: string | null | undefined, language: "ta" | "en"): string {
  if (!pos) return "";
  const mapped = POS_HUMAN_LABELS[pos];
  if (!mapped) return pos;
  return language === "ta" ? `${mapped.ta} (${pos})` : mapped.en;
}

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

  // Group English Wiktionary entries by part of speech
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
    <Card className="p-5 sm:p-7 space-y-6">
      {/* Dictionary Headword Header */}
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
            {entries.length > 0 && (
              <span className="text-[11px] text-[var(--color-muted)]">
                · {language === "ta" ? "ஆங்கில விக்சனரி" : "English Wiktionary"}
              </span>
            )}
            {extended && (
              <span className="text-[11px] text-[var(--color-muted)]">
                · {language === "ta" ? "தமிழ் விக்சனரி" : "Tamil Wiktionary"}
              </span>
            )}
          </div>
        </div>

        <CopyButton text={headword} size="sm" variant="outline" />
      </div>

      {/* Pronunciation / Variant Forms */}
      {extraForms.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {extraForms.map((form) => (
            <div
              key={form.form_id}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-raised)] text-xs"
            >
              <span className="font-tamil font-semibold text-[var(--color-mai)]">{form.text}</span>
              <span className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                {form.representation}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* English Definitions Grouped by Part of Speech */}
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

      {/* Tamil Definitions (தமிழ் பொருள்) */}
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

      {/* Collapsible Sources & License Footer */}
      {allSafeLinks.length > 0 && (
        <div className="pt-3 border-t border-[var(--border-line)]">
          <button
            type="button"
            onClick={() => setShowProv((prev) => !prev)}
            aria-expanded={showProv}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--color-muted)] hover:text-[var(--color-semman)] py-1 cursor-pointer"
          >
            {showProv ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
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
                {extended && (
                  <a
                    href="/lexicon-extended/NOTICE.md"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] text-[var(--color-semman)] hover:border-[var(--color-semman)] text-[11px] font-medium"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span>CC-BY-SA-4.0 Attribution Notice</span>
                  </a>
                )}
              </div>
              {entries.length > 0 && (
                <div className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                  {entries.map((e) => `${e.part_of_speech.value ?? "ENTRY"}: ${e.entry_id} (rev ${e.revision.slice(0, 10)})`).join(" · ")}
                </div>
              )}
              {extended && (
                <div className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                  ta.wiktionary.org: pageid={extended.pageid} · revid={extended.revid} · {extended.source_id}
                </div>
              )}
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
  const lastConsumedNonceRef = useRef<number | undefined>(undefined);

  // Align initial letter "ந" with default activeWord "நன்றி"
  const [selectedLetter, setSelectedLetter] = useState<string>("ந");
  const [selectedPos, setSelectedPos] = useState<string>("ALL");
  const [quickSourceFilter, setQuickSourceFilter] = useState<"ALL" | ExtendedPackId>("ALL");
  const [page, setPage] = useState<number>(1);

  const [query, setQuery] = useState(() => initialQuery?.trim() ?? "");
  const [activeWord, setActiveWord] = useState(() => initialQuery?.trim() || "நன்றி");
  const [selectedPacks, setSelectedPacks] = useState<string[]>(["core"]);
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [selectedRegister, setSelectedRegister] = useState<string>("");

  const [response, setResponse] = useState<tt.LexiconLookupResponse | null>(null);
  const [extendedEntry, setExtendedEntry] = useState<ExtendedEntryDetail | null>(null);
  const [lookupError, setLookupError] = useState<string | null>(null);
  const [lastRawRequest, setLastRawRequest] = useState<string>("");
  const [lastRawResponse, setLastRawResponse] = useState<string>("");
  const [latencyMs, setLatencyMs] = useState<number>(0);

  const [showAdvancedPanel, setShowAdvancedPanel] = useState(false);
  const [showDataDetails, setShowDataDetails] = useState(false);
  const [showContractPresets, setShowContractPresets] = useState(false);
  const [showRawInspector, setShowRawInspector] = useState(false);

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

  const loadLetterBucket = useCallback(
    async (letterId: string, file: string) => {
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
    },
    []
  );

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
    const effectivePacks =
      quickSourceFilter === "ALL"
        ? undefined
        : [quickSourceFilter];
    return filterBrowseItems(activeWordPool, {
      query: filterQuery,
      letter: selectedLetter,
      packs: effectivePacks,
      pos: selectedPos,
      region: selectedRegion || "ALL",
    });
  }, [activeWordPool, query, activeWord, selectedLetter, quickSourceFilter, selectedPos, selectedRegion]);

  const fallbackSuggestions = useMemo(() => {
    if (!query.trim()) return [];
    return filterBrowseItems(activeWordPool, {
      query,
      region: selectedRegion || "ALL",
    }).slice(0, 8);
  }, [activeWordPool, query, selectedRegion]);

  useEffect(() => {
    setPage(1);
  }, [query, selectedLetter, quickSourceFilter, selectedPos, selectedRegion]);

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
    [loadExtendedDetail]
  );

  // Load initial word from extended shard immediately so entry appears even before WASM finishes
  useEffect(() => {
    const startWord = initialQuery?.trim() || "நன்றி";
    void loadExtendedDetail(startWord);
  }, [loadExtendedDetail, initialQuery]);

  // Discover compiled packs from Rust once WASM is ready
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
    } catch (err: unknown) {
      setPacksError(err instanceof Error ? err.message : String(err));
    }
  }, [ready, executeLookup]);

  // Handle subsequent quick searches dispatched from Home
  useEffect(() => {
    if (!initialQueryNonce || initialQueryNonce === lastConsumedNonceRef.current) return;
    const trimmed = initialQuery?.trim();
    if (!trimmed) return;
    lastConsumedNonceRef.current = initialQueryNonce;
    setViewMode("verified");
    setQuery(trimmed);
    setActiveWord(trimmed);
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
    if (selectedRegion && !scopeOptions.regions.includes(selectedRegion)) {
      setSelectedRegion("");
    }
    if (selectedRegister && !scopeOptions.registers.includes(selectedRegister)) {
      setSelectedRegister("");
    }
  }, [scopeOptions, selectedRegion, selectedRegister]);

  const runCurrentFormLookup = (
    overrideQuery = query,
    overridePacks = selectedPacks,
    overrideRegion = selectedRegion,
    overrideRegister = selectedRegister
  ) => {
    if (!ready) return;
    setActiveWord(overrideQuery);
    executeLookup(overrideQuery, {
      packs: overridePacks,
      region: overrideRegion === "" ? undefined : overrideRegion,
      register: overrideRegister === "" ? undefined : overrideRegister,
    });
  };

  const handleSelectBrowseWord = (item: BrowseWordItem) => {
    setActiveWord(item.word);
    if (selectedLetter === "ALL") {
      setQuery(item.word);
    }
    if (!ready) {
      void loadExtendedDetail(item.word);
      return;
    }
    const packsToUse = selectedPacks.length > 0 ? selectedPacks : availablePackIds;
    executeLookup(item.word, {
      packs: packsToUse,
      region: selectedRegion === "" ? undefined : selectedRegion,
      register: selectedRegister === "" ? undefined : selectedRegister,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    const hasTamil = /[\u0B80-\u0BFF]/.test(trimmed);
    if (!hasTamil && fallbackSuggestions.length > 0) {
      const top = fallbackSuggestions[0];
      setActiveWord(top.word);
      if (ready) {
        executeLookup(top.word, {
          packs: selectedPacks,
          region: selectedRegion === "" ? undefined : selectedRegion,
          register: selectedRegister === "" ? undefined : selectedRegister,
        });
      } else {
        void loadExtendedDetail(top.word);
      }
      return;
    }
    setActiveWord(query);
    if (ready) {
      runCurrentFormLookup(query);
    } else {
      void loadExtendedDetail(query);
    }
  };

  const handleQuickSourceFilter = (src: "ALL" | ExtendedPackId) => {
    setQuickSourceFilter(src);
    if (src === "ALL" || src === "ta_wiktionary") {
      setSelectedPacks([...availablePackIds]);
    } else if (availablePackSet.has(src)) {
      setSelectedPacks([src]);
    }
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
    setQuery(ex.query);
    setActiveWord(ex.query);
    setSelectedLetter("ALL");
    setQuickSourceFilter("ALL");
    setSelectedRegion("");
    setSelectedRegister("");
    const allHintAvailable = ex.packHint.every((p) => availablePackSet.has(p));
    const nextPacks = allHintAvailable
      ? Array.from(new Set([...selectedPacks, ...ex.packHint])).filter((p) =>
          availablePackSet.has(p)
        )
      : [...ex.packHint];

    if (allHintAvailable) {
      setSelectedPacks(nextPacks);
    }
    if (ready) {
      executeLookup(ex.query, { packs: nextPacks });
    }
  };

  const handlePresetClick = (preset: ContractTestPreset) => {
    if (!ready) return;
    setQuery(preset.query);
    setActiveWord(preset.query);
    const packs = preset.useAvailablePacks
      ? availablePackIds.length > 0
        ? availablePackIds
        : ["core"]
      : preset.packs;
    executeLookup(preset.query, {
      packs,
      region: preset.region,
      register: preset.register,
    });
  };

  const handleChooserKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (IS_PUBLIC_BETA) return;
    if (e.key === "ArrowRight" || e.key === "ArrowLeft" || e.key === "Home" || e.key === "End") {
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

  const totalActiveWords = extendedManifest?.total_words ?? browseIndex?.count ?? 9410;
  const alphabetBuckets = extendedManifest?.letters ?? browseIndex?.letters ?? [];
  const posList = extendedManifest?.pos ?? browseIndex?.pos ?? [];
  const hasAnyEntryMatch =
    (response && response.status === "matched") || Boolean(extendedEntry);

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
              <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                {totalActiveWords.toLocaleString()} {t.home.dictionaryCountSuffix}
              </span>
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

          {/* Clean Search & Filter Bar */}
          <Card className="p-4 sm:p-5 space-y-3.5">
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2.5">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-[var(--color-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  id="lexicon-query-input"
                  type="text"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    if (selectedLetter !== "ALL") setSelectedLetter("ALL");
                  }}
                  placeholder={
                    language === "ta"
                      ? `தமிழ் சொல் அல்லது ஆங்கிலப் பொருளைத் தேடுங்கள் (${totalActiveWords.toLocaleString()} சொற்கள்)...`
                      : `Search ${totalActiveWords.toLocaleString()} Tamil words or English meanings (e.g. நன்றி, அவகுணம், water)...`
                  }
                  aria-label={t.tools.lexicon.searchLabel}
                  className="w-full min-h-[44px] pl-10 pr-10 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm sm:text-base font-tamil text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
                />
                {query && (
                  <button
                    type="button"
                    onClick={() => {
                      setQuery("");
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

            {/* Quick Category & Dialect Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex flex-wrap items-center gap-1.5">
                {(
                  [
                    { id: "ALL", en: "All", ta: "அனைத்தும்" },
                    { id: "ta_wiktionary", en: "Tamil Wiktionary", ta: "தமிழ் விக்சனரி" },
                    { id: "core", en: "English Wiktionary", ta: "ஆங்கில விக்சனரி" },
                    { id: "regional", en: "Dialects", ta: "வட்டார வழக்கு" },
                    { id: "names_taxa", en: "Names & Taxa", ta: "பெயர்கள்" },
                  ] as const
                ).map((pill) => {
                  const isActive = quickSourceFilter === pill.id;
                  const disabled =
                    pill.id !== "ALL" &&
                    pill.id !== "ta_wiktionary" &&
                    !availablePackSet.has(pill.id);
                  return (
                    <button
                      key={pill.id}
                      type="button"
                      disabled={disabled || !ready}
                      onClick={() => handleQuickSourceFilter(pill.id)}
                      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer disabled:opacity-40 ${
                        isActive
                          ? "bg-[var(--color-semman)] text-[#faf7f2]"
                          : "bg-[var(--bg-raised)] text-[var(--color-mai)] hover:bg-[var(--color-semman-light)] hover:text-[var(--color-semman)]"
                      }`}
                    >
                      {language === "ta" ? pill.ta : pill.en}
                    </button>
                  );
                })}
              </div>

              <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
                <select
                  id="lexicon-pos-select"
                  value={selectedPos}
                  onChange={(e) => setSelectedPos(e.target.value)}
                  aria-label={language === "ta" ? "சொல்வகை" : "Part of speech"}
                  className="min-h-[36px] px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] focus:border-[var(--color-semman)] focus-visible:outline-none"
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

                <select
                  id="lexicon-region-select"
                  value={selectedRegion}
                  onChange={(e) => {
                    const val = e.target.value;
                    setSelectedRegion(val);
                    if (ready && activeWord) {
                      runCurrentFormLookup(activeWord, selectedPacks, val, selectedRegister);
                    }
                  }}
                  aria-label={t.tools.lexicon.regionFilterLabel}
                  className="min-h-[36px] px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] focus:border-[var(--color-semman)] focus-visible:outline-none"
                >
                  <option value="">
                    {language === "ta" ? "அனைத்து வட்டாரங்கள்" : "All dialects"}
                  </option>
                  {scopeOptions.regionEntries
                    .filter((r) => r.attestedInSelectedPacks)
                    .map((region) => (
                      <option key={region.code} value={region.code}>
                        {region.code}
                        {region.parent_code ? ` (${region.parent_code})` : ""}
                      </option>
                    ))}
                </select>
              </div>
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

          {/* Master-Detail Dictionary Workspace */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
            {/* Left Pane: Browseable Word List */}
            <Card className="lg:col-span-5 p-0 overflow-hidden flex flex-col">
              <div className="px-4 py-3 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/40 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-mai)]">
                  <BookOpen className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
                  <span>
                    {selectedLetter !== "ALL"
                      ? `${selectedLetter} · ${filteredBrowseItems.length.toLocaleString()}`
                      : language === "ta"
                        ? `${filteredBrowseItems.length.toLocaleString()} சொற்கள்`
                        : `${filteredBrowseItems.length.toLocaleString()} words`}
                  </span>
                </div>
                {totalPages > 1 && (
                  <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                    {safePage} / {totalPages}
                  </span>
                )}
              </div>

              {browseLoading || letterLoading ? (
                <div className="p-8 flex items-center justify-center gap-2 text-xs text-[var(--color-muted)]">
                  <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)]" />
                  <span>{language === "ta" ? "சொற்பட்டியல் ஏற்றப்படுகிறது..." : "Loading word list..."}</span>
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
                      setQuickSourceFilter("ALL");
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
                          onClick={() => handleSelectBrowseWord(item)}
                          className={`w-full text-left px-4 py-2.5 transition-colors cursor-pointer flex flex-col gap-0.5 ${
                            isSelected
                              ? "bg-[var(--color-semman-light)]/70 border-l-2 border-[var(--color-semman)]"
                              : "hover:bg-[var(--bg-raised)]/60"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span
                              className={`text-sm sm:text-base font-tamil font-semibold ${
                                isSelected ? "text-[var(--color-semman)]" : "text-[var(--color-mai)]"
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

              {/* Pagination Footer */}
              {totalPages > 1 && (
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

            {/* Right Pane: Selected Word Dictionary Entry */}
            <div className="lg:col-span-7 space-y-4">
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

              {!lookupError && response && !hasAnyEntryMatch && (
                <Card className="p-5 space-y-3">
                  <h2 className="text-base font-tamil font-bold text-[var(--color-mai)]">
                    {language === "ta"
                      ? `"${response.canonical_query}" நேரடியாகக் கிடைக்கவில்லை`
                      : `No exact entry for "${response.canonical_query}"`}
                  </h2>

                  {fallbackSuggestions.length > 0 ? (
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
                            onClick={() => handleSelectBrowseWord(item)}
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
                </Card>
              )}

              {hasAnyEntryMatch && (
                <UnifiedWordCard
                  word={activeWord}
                  entries={response && response.status === "matched" ? response.entries : []}
                  extended={extendedEntry}
                  canonicalQuery={response?.canonical_query}
                  language={language}
                />
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
          </div>

          {/* Collapsible Advanced Filters, Pack Controls & Developer Diagnostics */}
          <Card className="p-4 sm:p-5">
            <button
              type="button"
              onClick={() => setShowAdvancedPanel((prev) => !prev)}
              aria-expanded={showAdvancedPanel}
              className="w-full flex items-center justify-between gap-2 text-left min-h-[40px] cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <SlidersHorizontal className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
                <div>
                  <span className="text-sm font-semibold text-[var(--color-mai)] block">
                    {language === "ta"
                      ? "மேம்பட்ட வடிகட்டிகள், தொகுப்பு விவரங்கள் & உருவாக்குநர் கருவிகள்"
                      : "Advanced Filters, Pack Coverage & Developer Tools"}
                  </span>
                  <span className="text-xs text-[var(--color-muted)]">
                    {language === "ta"
                      ? "நடை வடிகட்டி, உரிம அறிவிப்புகள், ஒப்பந்தச் சோதனைகள் மற்றும் JSON வெளியீடு"
                      : "Register filter, pack checkboxes, CC-BY-SA-4.0 notices, contract presets, and raw JSON"}
                  </span>
                </div>
              </div>
              {showAdvancedPanel ? (
                <ChevronUp className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
              ) : (
                <ChevronDown className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
              )}
            </button>

            {showAdvancedPanel && (
              <div className="mt-4 pt-4 border-t border-[var(--border-line)] space-y-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="lexicon-register-select"
                      className="text-xs font-semibold text-[var(--color-mai)] block"
                    >
                      {t.tools.lexicon.registerFilterLabel} ({scopeOptions.registers.length})
                    </label>
                    <select
                      id="lexicon-register-select"
                      value={selectedRegister}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSelectedRegister(val);
                        if (ready) runCurrentFormLookup(activeWord, selectedPacks, selectedRegion, val);
                      }}
                      className="w-full min-h-[40px] px-3 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs font-mono-tamil text-[var(--color-mai)]"
                    >
                      <option value="">{t.tools.lexicon.allRegistersOption}</option>
                      {scopeOptions.registers.map((reg) => (
                        <option key={reg} value={reg}>
                          {reg}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-[var(--color-mai)] block">
                      Exact Query Diagnostics
                    </span>
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
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
                  </div>
                </div>

                {/* Pack Checkboxes & Attribution Notices */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-[var(--color-mai)] block">
                    {t.tools.lexicon.packsLabel} ({loadedTotals.loadedPackIds.join(" + ") || "none"})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
                    {LEXICON_PACK_DISPLAY_ORDER.map((packId) => {
                      const verification = catalogAlignment.byPack[packId];
                      const isAvailableInBuild = availablePackSet.has(packId);
                      const isChecked = selectedPacks.includes(packId);
                      const noticeLinks = getPackNoticeLinks(packId);
                      return (
                        <div
                          key={packId}
                          className={`p-3 rounded-xl border space-y-2 ${
                            isAvailableInBuild && isChecked
                              ? "border-[var(--color-semman)] bg-[var(--color-semman-light)]/30"
                              : "border-[var(--border-line)] bg-[var(--bg-canvas)]"
                          }`}
                        >
                          <label className="flex items-start gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              disabled={!isAvailableInBuild}
                              onChange={() => handleTogglePack(packId)}
                              aria-label={packId}
                              className="mt-0.5 h-4 w-4 accent-[var(--color-semman)]"
                            />
                            <div className="min-w-0 flex-1">
                              <span className="text-xs font-mono-tamil font-bold text-[var(--color-mai)] block">
                                {packId}
                              </span>
                              <span className="text-[10px] font-mono-tamil text-[var(--color-muted)] block">
                                {verification.status === "verified" && verification.verifiedEntryCount !== null
                                  ? `${verification.verifiedEntryCount.toLocaleString()} entries · ${(verification.verifiedSenseCount ?? 0).toLocaleString()} senses`
                                  : t.tools.lexicon.packUnavailableBadge}
                              </span>
                            </div>
                          </label>
                          {noticeLinks.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 pt-1 border-t border-[var(--border-line)]/60">
                              {noticeLinks.slice(0, 2).map((nLink) => (
                                <a
                                  key={nLink.href}
                                  href={nLink.href}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[10px] text-[var(--color-semman)] hover:underline"
                                >
                                  <ExternalLink className="w-2.5 h-2.5 shrink-0" />
                                  <span>{language === "ta" ? nLink.label_ta : nLink.label_en}</span>
                                </a>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Data Coverage Summary Toggle */}
                <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
                  <button
                    type="button"
                    onClick={() => setShowDataDetails((prev) => !prev)}
                    aria-expanded={showDataDetails}
                    className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
                  >
                    <span className="inline-flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5 text-[var(--color-semman)]" />
                      <span>{t.tools.lexicon.dataDetailsToggle}</span>
                    </span>
                    {showDataDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                  {showDataDetails && (
                    <div className="pt-2 border-t border-[var(--border-line)] space-y-2 text-xs text-[var(--color-muted)]">
                      <p>
                        Embedded WASM packs: {catalogAlignment.verifiedLoadedEntries.toLocaleString()} entries ·{" "}
                        {catalogAlignment.verifiedLoadedSenses.toLocaleString()} senses ·{" "}
                        {(catalogAlignment.verifiedDistinctHeadwords ?? 0).toLocaleString()} distinct words.
                      </p>
                      {extendedManifest && (
                        <p>
                          Extended verified dictionary (en.wiktionary.org + ta.wiktionary.org, CC-BY-SA-4.0):{" "}
                          {extendedManifest.total_words.toLocaleString()} distinct words (
                          {extendedManifest.tawiktionary_words.toLocaleString()} from Tamil Wiktionary).
                        </p>
                      )}
                      {!IS_PUBLIC_BETA && <p>{t.tools.lexicon.historicalExclusionBody}</p>}
                    </div>
                  )}
                </div>

                {/* Contract-Test Presets Toggle */}
                <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
                  <button
                    type="button"
                    onClick={() => setShowContractPresets((prev) => !prev)}
                    aria-expanded={showContractPresets}
                    className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
                  >
                    <span className="inline-flex items-center gap-1.5">
                      <FlaskConical className="w-3.5 h-3.5 text-[var(--color-sandhanam)]" />
                      <span>{t.tools.lexicon.contractPresetsToggle}</span>
                    </span>
                    {showContractPresets ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                  {showContractPresets && (
                    <div className="pt-2 border-t border-[var(--border-line)] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                      {CONTRACT_TEST_PRESETS.map((preset) => (
                        <button
                          key={preset.id}
                          type="button"
                          onClick={() => handlePresetClick(preset)}
                          disabled={!ready}
                          className="p-2.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-sandhanam)] text-left space-y-0.5 cursor-pointer disabled:opacity-50"
                        >
                          <div className="text-xs font-bold text-[var(--color-mai)]">
                            {language === "ta" ? preset.label_ta : preset.label_en}
                          </div>
                          <p className="text-[11px] text-[var(--color-muted)] leading-snug">
                            {language === "ta" ? preset.desc_ta : preset.desc_en}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Raw JSON Inspector Toggle */}
                <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] p-3 space-y-2">
                  <button
                    type="button"
                    onClick={() => setShowRawInspector((prev) => !prev)}
                    aria-expanded={showRawInspector}
                    className="w-full flex items-center justify-between text-xs font-semibold text-[var(--color-mai)] cursor-pointer"
                  >
                    <span className="inline-flex items-center gap-1.5">
                      <BookMarked className="w-3.5 h-3.5 text-[var(--color-semman)]" />
                      <span>{t.tools.lexicon.rawInspectorHeading}</span>
                    </span>
                    {showRawInspector ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                  {showRawInspector && (
                    <div className="pt-2 border-t border-[var(--border-line)] grid grid-cols-1 lg:grid-cols-2 gap-3">
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-[var(--color-mai)]">
                            {t.tools.lexicon.rawRequestLabel}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <CopyButton text={lastRawRequest} size="sm" variant="outline" />
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              disabled={!lastRawRequest}
                              onClick={() => downloadJsonFile("lexicon-request.json", lastRawRequest)}
                            >
                              <Download className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </div>
                        <pre className="text-[11px] font-mono-tamil bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-lg p-2.5 max-h-64 overflow-auto text-[var(--color-mai)]">
                          {lastRawRequest || "{}"}
                        </pre>
                      </div>
                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-[var(--color-mai)]">
                            {t.tools.lexicon.rawResponseLabel}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <CopyButton text={lastRawResponse} size="sm" variant="outline" />
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              disabled={!lastRawResponse}
                              onClick={() => downloadJsonFile("lexicon-response.json", lastRawResponse)}
                            >
                              <Download className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </div>
                        <pre className="text-[11px] font-mono-tamil bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-lg p-2.5 max-h-64 overflow-auto text-[var(--color-mai)]">
                          {lastRawResponse || "{}"}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
