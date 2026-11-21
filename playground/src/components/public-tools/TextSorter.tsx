import { useState, useMemo } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { ArrowDownAZ, ArrowUpZA, Filter, Scale, X } from "lucide-react";

const SAMPLE_WORDS = `பாரதி
அகத்தியர்
கம்பர்
திருவள்ளுவர்
ஔவையார்
இளங்கோவடிகள்
தொல்காப்பியர்
உமறுப்புலவர்`;

interface TextSorterProps {
  engineReady?: boolean;
}

export function TextSorter({ engineReady }: TextSorterProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [input, setInput] = useState(SAMPLE_WORDS);
  const [ascending, setAscending] = useState(true);
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [profile, setProfile] = useState<tt.CollationProfile>("agara-v1");
  const [wordA, setWordA] = useState("அகத்தியர்");
  const [wordB, setWordB] = useState("கம்பர்");

  const result = useMemo(() => {
    const lines = input
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (!ready || lines.length === 0) {
      return { output: "", wordCount: 0 };
    }

    try {
      const words = removeDuplicates ? Array.from(new Set(lines)) : lines;
      const sorted = tt.sort_words(words, profile);
      if (!ascending) {
        sorted.reverse();
      }
      return { output: sorted.join("\n"), wordCount: sorted.length };
    } catch (err) {
      console.error("Sorting error:", err);
      return { output: "", wordCount: 0 };
    }
  }, [input, ascending, removeDuplicates, profile, ready]);

  const compareAnalysis = useMemo(() => {
    if (!ready || (!wordA.trim() && !wordB.trim())) {
      return null;
    }
    try {
      const cmp = tt.compare(wordA, wordB, profile);
      const sortKeyA = Array.from(tt.sort_key(wordA, profile));
      const sortKeyB = Array.from(tt.sort_key(wordB, profile));
      const searchKeyA = Array.from(tt.search_key(wordA, profile));
      const foldedKeyA = Array.from(tt.folded_search_key(wordA, "comprehensive", profile));
      return { cmp, sortKeyA, sortKeyB, searchKeyA, foldedKeyA };
    } catch {
      return null;
    }
  }, [wordA, wordB, profile, ready]);

  const handleClear = () => {
    setInput("");
  };

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.sorter.title}
        description={t.tools.sorter.desc}
        actions={
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setInput(SAMPLE_WORDS)}
          >
            {t.actions.loadSample}
          </Button>
        }
      />

      {/* Sort Options Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
          {(
            [
              { id: "agara-v1", label: t.tools.sorter.profileAgara },
              { id: "uyirmei-first-v1", label: t.tools.sorter.profileUyirmei },
            ] as const
          ).map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setProfile(p.id)}
              className={`px-3 py-1.5 min-h-[34px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                profile === p.id
                  ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                  : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setAscending((prev) => !prev)}
          >
            {ascending ? (
              <>
                <ArrowDownAZ className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
                <span>{t.tools.sorter.sortAsc}</span>
              </>
            ) : (
              <>
                <ArrowUpZA className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
                <span>{t.tools.sorter.sortDesc}</span>
              </>
            )}
          </Button>

          <Button
            type="button"
            variant={removeDuplicates ? "primary" : "outline"}
            size="sm"
            onClick={() => setRemoveDuplicates((prev) => !prev)}
          >
            <Filter className="w-3.5 h-3.5 mr-1.5" />
            <span>{t.tools.sorter.removeDups}</span>
          </Button>
        </div>
      </div>

      {/* Unified Split Input / Output Workspace */}
      <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[var(--border-line)]">
        <div className="flex flex-col">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {t.tools.sorter.inputWordsLabel}
            </span>
            {input && (
              <button
                type="button"
                onClick={handleClear}
                className="inline-flex items-center gap-1 text-xs text-[var(--color-muted)] hover:text-[var(--color-semman)] cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
                <span>{t.actions.clear}</span>
              </button>
            )}
          </div>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t.tools.sorter.inputPlaceholder}
            className="w-full flex-1 min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>

        <div className="flex flex-col bg-[var(--bg-canvas)]/40">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)]">
                {t.tools.sorter.collationOutputLabel}
              </span>
              {result.wordCount > 0 && (
                <Badge variant="terracotta">
                  {result.wordCount} {t.tools.sorter.wordsCountSuffix}
                </Badge>
              )}
            </div>
            {result.output && (
              <CopyButton
                text={result.output}
                label={t.actions.copy}
                copiedLabel={t.actions.copied}
                size="sm"
                variant="outline"
              />
            )}
          </div>
          <textarea
            readOnly
            value={result.output}
            placeholder={t.tools.sorter.outputPlaceholder}
            className="w-full flex-1 min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>
      </div>

      {/* Pairwise Compare & Sort Key Inspector */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-line)] pb-3">
          <div className="flex items-center gap-2">
            <Scale className="w-4 h-4 text-[var(--color-semman)]" />
            <h2 className="text-sm font-semibold text-[var(--color-mai)]">
              {t.tools.sorter.compareHeading}
            </h2>
          </div>
          {compareAnalysis && (
            <Badge
              variant={compareAnalysis.cmp === 0 ? "outline" : "terracotta"}
              className="text-xs font-semibold"
            >
              {compareAnalysis.cmp < 0
                ? t.tools.sorter.compareResultBefore
                : compareAnalysis.cmp > 0
                  ? t.tools.sorter.compareResultAfter
                  : t.tools.sorter.compareResultEqual}
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label htmlFor="sorter-word-a" className="text-xs font-medium text-[var(--color-muted)] block">
              {t.tools.sorter.wordALabel}
            </label>
            <input
              id="sorter-word-a"
              type="text"
              value={wordA}
              onChange={(e) => setWordA(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-base text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="sorter-word-b" className="text-xs font-medium text-[var(--color-muted)] block">
              {t.tools.sorter.wordBLabel}
            </label>
            <input
              id="sorter-word-b"
              type="text"
              value={wordB}
              onChange={(e) => setWordB(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-base text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
            />
          </div>
        </div>

        {compareAnalysis && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 text-xs">
            <div className="p-3 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5">
              <div className="flex items-center justify-between text-[var(--color-muted)]">
                <span>{t.tools.sorter.sortKeyLabel} ({wordA})</span>
                <CopyButton text={JSON.stringify(compareAnalysis.sortKeyA)} size="sm" variant="ghost" />
              </div>
              <p className="font-mono-tamil text-[11px] text-[var(--color-mai)] break-all">
                [{compareAnalysis.sortKeyA.join(", ")}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5">
              <div className="flex items-center justify-between text-[var(--color-muted)]">
                <span>{t.tools.sorter.sortKeyLabel} ({wordB})</span>
                <CopyButton text={JSON.stringify(compareAnalysis.sortKeyB)} size="sm" variant="ghost" />
              </div>
              <p className="font-mono-tamil text-[11px] text-[var(--color-mai)] break-all">
                [{compareAnalysis.sortKeyB.join(", ")}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5">
              <div className="flex items-center justify-between text-[var(--color-muted)]">
                <span>{t.tools.sorter.searchKeyLabel} ({wordA})</span>
                <CopyButton text={JSON.stringify(compareAnalysis.searchKeyA)} size="sm" variant="ghost" />
              </div>
              <p className="font-mono-tamil text-[11px] text-[var(--color-mai)] break-all">
                [{compareAnalysis.searchKeyA.join(", ")}]
              </p>
            </div>

            <div className="p-3 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-1.5">
              <div className="flex items-center justify-between text-[var(--color-muted)]">
                <span>{t.tools.sorter.foldedKeyLabel} ({wordA})</span>
                <CopyButton text={JSON.stringify(compareAnalysis.foldedKeyA)} size="sm" variant="ghost" />
              </div>
              <p className="font-mono-tamil text-[11px] text-[var(--color-mai)] break-all">
                [{compareAnalysis.foldedKeyA.join(", ")}]
              </p>
            </div>
          </div>
        )}
      </Card>

      <StickyActionBar
        outputText={result.output}
        onClear={handleClear}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
      />
    </div>
  );
}
