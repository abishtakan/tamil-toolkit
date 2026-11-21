import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "../../lib/i18n";
import { getLexiconPacks, isEngineReady } from "../../lib/engine";
import { ExtendedManifest, verifyPackCatalogAlignment } from "../../lib/lexicon";
import { TOOLS, ToolGroupId, ToolId, getToolCopy } from "../../lib/tools";
import { ToolIcon } from "../../App";
import { Button } from "../ui/button";
import { Search, ArrowRight } from "lucide-react";

interface OverviewHubProps {
  onSelectTool: (toolId: ToolId) => void;
  onQuickDictionarySearch?: (query: string) => void;
  engineReady?: boolean;
}

const EVERYDAY_GROUPS: readonly ToolGroupId[] = ["words", "writing", "reference"];

export function OverviewHub({
  onSelectTool,
  onQuickDictionarySearch,
  engineReady,
}: OverviewHubProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();
  const [dictQuery, setDictQuery] = useState("");

  const lexiconAlignment = useMemo(() => {
    if (!ready) return null;
    try {
      return verifyPackCatalogAlignment(getLexiconPacks());
    } catch {
      return null;
    }
  }, [ready]);

  const [extendedManifest, setExtendedManifest] = useState<ExtendedManifest | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch("/lexicon-extended/manifest.json")
      .then((res) => (res.ok ? (res.json() as Promise<ExtendedManifest>) : null))
      .then((data) => {
        if (!cancelled) setExtendedManifest(data);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  const getToolPreviewHint = (id: ToolId): string | null => {
    switch (id) {
      case "lexicon":
        if (extendedManifest) {
          return `${extendedManifest.total_words.toLocaleString()} ${t.home.dictionaryCountSuffix}`;
        }
        if (lexiconAlignment && !lexiconAlignment.hasStaleMismatch && lexiconAlignment.verifiedDistinctHeadwords) {
          return `${lexiconAlignment.verifiedDistinctHeadwords.toLocaleString()} ${t.home.dictionaryCountSuffix}`;
        }
        return null;
      case "codec":
        return "jkpo; → தமிழ்";
      case "numeral":
        return "₹1,25,000 → ஒரு இலட்சத்து…";
      case "calendar":
        return "தமிழ் மாதம் · நட்சத்திரம் · ராகு காலம்";
      case "sorter":
        return "அ → ஆ → க → ன";
      case "letter":
        return "தமிழ் = த + மி + ழ்";
      case "normalizer":
        return "NFC · NFD · மயங்கொலி";
      case "hyphenator":
        return "தமிழ்நாடு → தமிழ்-நாடு";
      case "symbols":
        return "𑿀 (1/80) · 𑿒 (1/4) · 𑿔 (3/4)";
      case "batch":
        return ".txt / .csv";
      default:
        return null;
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onQuickDictionarySearch) {
      onQuickDictionarySearch(dictQuery);
    } else {
      onSelectTool("lexicon");
    }
  };

  const developerTools = useMemo(
    () => TOOLS.filter((tool) => tool.group === "developer"),
    []
  );

  return (
    <div className="space-y-10">
      {/* Clean Editorial Masthead & Direct Dictionary Search */}
      <section className="space-y-5 pb-7 border-b border-[var(--border-line)]">
        <div className="space-y-2 max-w-2xl">
          <h1 className="text-2xl sm:text-3xl font-tamil font-bold tracking-tight text-[var(--color-mai)]">
            {t.siteTitle}
          </h1>
          <p className="text-sm sm:text-base text-[var(--color-muted)] leading-relaxed">
            {t.home.heroSummary}
          </p>
        </div>

        {/* Instant Dictionary Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5 max-w-2xl">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[var(--color-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={dictQuery}
              onChange={(e) => setDictQuery(e.target.value)}
              placeholder={t.home.searchPlaceholder}
              aria-label={t.home.searchPlaceholder}
              className="w-full min-h-[46px] pl-10 pr-4 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-sm sm:text-base font-tamil text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus-visible:outline-none focus-visible:border-[var(--color-semman)] focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
            />
          </div>
          <Button type="submit" variant="primary" size="md" className="shrink-0 min-h-[46px] px-5">
            <span>{t.home.searchAction}</span>
            <ArrowRight className="w-4 h-4 ml-1.5" />
          </Button>
        </form>

        {/* Quick-Start Common Tasks */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-medium text-[var(--color-muted)] mr-1">
            {t.home.quickStartLabel}
          </span>
          {[
            { tool: "codec" as ToolId, label: t.home.quickBamini },
            { tool: "numeral" as ToolId, label: t.home.quickCheque },
            { tool: "calendar" as ToolId, label: t.home.quickCalendar },
            { tool: "normalizer" as ToolId, label: t.home.quickClean },
          ].map((item) => (
            <button
              key={item.tool}
              type="button"
              onClick={() => onSelectTool(item.tool)}
              className="px-3 py-1.5 rounded-full border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] text-xs font-medium text-[var(--color-mai)] transition-colors cursor-pointer"
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {/* Human-Grouped Everyday Tools */}
      <div className="space-y-8">
        {EVERYDAY_GROUPS.map((groupId) => {
          const groupTools = TOOLS.filter((tool) => tool.group === groupId);
          return (
            <section key={groupId} className="space-y-3.5">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                {t.navGroups[groupId]}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {groupTools.map((tool) => {
                  const copy = getToolCopy(tool.id, t);
                  const hint = getToolPreviewHint(tool.id);
                  return (
                    <button
                      key={tool.id}
                      type="button"
                      onClick={() => onSelectTool(tool.id)}
                      className="group text-left rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] hover:bg-[var(--bg-raised)]/30 p-4 sm:p-5 flex flex-col justify-between gap-3 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] active:scale-[0.99]"
                    >
                      <div className="space-y-2.5">
                        <div className="flex items-start justify-between gap-3">
                          <div className="w-9 h-9 rounded-lg bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center shrink-0">
                            <ToolIcon icon={tool.icon} className="w-4 h-4" />
                          </div>
                          <ArrowRight className="w-4 h-4 text-[var(--color-muted)] opacity-0 group-hover:opacity-100 group-hover:text-[var(--color-semman)] transition-opacity shrink-0 mt-1" />
                        </div>

                        <div className="space-y-1">
                          <h3 className="text-base font-tamil font-bold text-[var(--color-mai)] group-hover:text-[var(--color-semman)] transition-colors">
                            {copy.title}
                          </h3>
                          <p className="text-xs text-[var(--color-muted)] leading-relaxed line-clamp-2">
                            {copy.desc}
                          </p>
                        </div>
                      </div>

                      {hint && (
                        <div className="pt-2.5 border-t border-[var(--border-line)]/70 text-[11px] font-tamil text-[var(--color-muted)] truncate">
                          {hint}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {/* Compact Developer Strip */}
      <section className="pt-4 border-t border-[var(--border-line)] space-y-3.5">
        <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            {t.home.developerSectionTitle}
          </h2>
          <p className="text-xs text-[var(--color-muted)]">{t.home.developerSectionDesc}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {developerTools.map((tool) => {
            const copy = getToolCopy(tool.id, t);
            return (
              <button
                key={tool.id}
                type="button"
                onClick={() => onSelectTool(tool.id)}
                className="group text-left rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-sandhanam)] px-4 py-3.5 flex items-center gap-3 transition-colors cursor-pointer active:scale-[0.99]"
              >
                <div className="w-8 h-8 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                  <ToolIcon icon={tool.icon} className="w-4 h-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-semibold text-[var(--color-mai)] group-hover:text-[var(--color-sandhanam)] transition-colors truncate">
                    {copy.title}
                  </h3>
                  <p className="text-xs text-[var(--color-muted)] truncate">{copy.desc}</p>
                </div>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
