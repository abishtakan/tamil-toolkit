import { useState, useTransition } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { ArrowDownAZ, ArrowUpZA, Filter, Sparkles } from "lucide-react";

const SAMPLE_WORDS = `பாரதி
அகத்தியர்
கம்பர்
திருவள்ளுவர்
ஔவையார்
இளங்கோவடிகள்
தொல்காப்பியர்
உமறுப்புலவர்`;

export function TextSorter() {
  const { t } = useLanguage();
  const [, startTransition] = useTransition();

  const [input, setInput] = useState(SAMPLE_WORDS);
  const [output, setOutput] = useState("");
  const [ascending, setAscending] = useState(true);
  const [removeDuplicates, setRemoveDuplicates] = useState(true);
  const [wordCount, setWordCount] = useState(0);
  const [latency, setLatency] = useState(0);

  const performSort = (raw: string, isAsc: boolean, dedup: boolean) => {
    const lines = raw
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    if (lines.length === 0) {
      setOutput("");
      setWordCount(0);
      setLatency(0);
      return;
    }

    const t0 = performance.now();
    try {
      let words = lines;
      if (dedup) {
        words = Array.from(new Set(words));
      }

      const sorted = tt.sort_words(words);
      if (!isAsc) {
        sorted.reverse();
      }

      setOutput(sorted.join("\n"));
      setWordCount(sorted.length);
    } catch (err) {
      console.error("Sorting error:", err);
    } finally {
      setLatency(performance.now() - t0);
    }
  };

  const handleInputChange = (val: string) => {
    setInput(val);
    startTransition(() => {
      performSort(val, ascending, removeDuplicates);
    });
  };

  const handleToggleOrder = () => {
    const next = !ascending;
    setAscending(next);
    startTransition(() => {
      performSort(input, next, removeDuplicates);
    });
  };

  const handleToggleDedup = () => {
    const next = !removeDuplicates;
    setRemoveDuplicates(next);
    startTransition(() => {
      performSort(input, ascending, next);
    });
  };

  const handleClear = () => {
    setInput("");
    setOutput("");
    setWordCount(0);
    setLatency(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.sorter.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.sorter.desc}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleInputChange(SAMPLE_WORDS)}
            className="text-xs font-tamil text-[var(--color-semman)] border-[var(--color-semman)]/30"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            <span>{t.actions.loadSample}</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleOrder}
            className="text-xs font-tamil"
          >
            {ascending ? (
              <>
                <ArrowDownAZ className="w-3.5 h-3.5 mr-1" />
                <span>{t.tools.sorter.sortAsc}</span>
              </>
            ) : (
              <>
                <ArrowUpZA className="w-3.5 h-3.5 mr-1" />
                <span>{t.tools.sorter.sortDesc}</span>
              </>
            )}
          </Button>

          <Button
            variant={removeDuplicates ? "primary" : "outline"}
            size="sm"
            onClick={handleToggleDedup}
            className="text-xs font-tamil"
          >
            <Filter className="w-3.5 h-3.5 mr-1" />
            <span>{t.tools.sorter.removeDups}</span>
          </Button>
        </div>
      </div>

      {/* Editor Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
              {t.tools.sorter.inputWordsLabel}
            </span>
            {input && (
              <button
                onClick={handleClear}
                className="text-xs text-[var(--color-muted)] hover:text-red-600 font-tamil"
              >
                {t.actions.clear}
              </button>
            )}
          </div>
          <Textarea
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder={t.tools.sorter.inputPlaceholder}
            className="min-h-[220px]"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
                {t.tools.sorter.collationOutputLabel}
              </span>
              {wordCount > 0 && (
                <Badge variant="terracotta">
                  {wordCount} {t.tools.sorter.wordsCountSuffix}
                </Badge>
              )}
            </div>
            {latency > 0 && <Badge variant="mono">{latency.toFixed(1)} ms</Badge>}
          </div>

          <div className="relative">
            <Textarea
              readOnly
              value={output}
              placeholder={t.tools.sorter.outputPlaceholder}
              className="min-h-[220px] bg-[var(--bg-raised)]/70 text-[var(--color-mai)] font-medium"
            />
            {output && (
              <div className="hidden md:block absolute bottom-3 right-3">
                <CopyButton
                  text={output}
                  label={t.actions.copy}
                  copiedLabel={t.actions.copied}
                  size="sm"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <StickyActionBar
        outputText={output}
        onClear={handleClear}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
      />
    </div>
  );
}
