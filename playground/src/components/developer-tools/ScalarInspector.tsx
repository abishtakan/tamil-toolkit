import { useState, useTransition } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Textarea } from "../ui/textarea";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { AlertTriangle, CheckCircle, Sparkles } from "lucide-react";

interface ScalarDetail {
  char: string;
  codePoint: number;
  hex: string;
  name: string;
  isInvisible: boolean;
}

export function ScalarInspector() {
  const { t } = useLanguage();
  const [, startTransition] = useTransition();

  const [input, setInput] = useState("தமிழ்");
  const [scalars, setScalars] = useState<ScalarDetail[]>([]);
  const [clusters, setClusters] = useState<string[]>([]);
  const [hasInvisible, setHasInvisible] = useState(false);
  const [latency, setLatency] = useState(0);

  const inspectText = (text: string) => {
    if (!text) {
      setScalars([]);
      setClusters([]);
      setHasInvisible(false);
      setLatency(0);
      return;
    }

    const t0 = performance.now();
    try {
      // 1. Grapheme clusters
      const letterClusters = tt.get_letters(text);
      setClusters(letterClusters || []);

      // 2. Scalars
      const details: ScalarDetail[] = [];
      let invisibleDetected = false;

      for (const char of text) {
        const cp = char.codePointAt(0) || 0;
        const hex = `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`;
        const isInvisible = cp === 0x200c || cp === 0x200d || cp === 0xfeff || cp === 0x00ad;
        if (isInvisible) invisibleDetected = true;

        details.push({
          char: isInvisible ? (cp === 0x200d ? "[ZWJ]" : "[ZWNJ]") : char,
          codePoint: cp,
          hex,
          name: isInvisible ? "Invisible Control" : "Tamil Scalar",
          isInvisible
        });
      }

      setScalars(details);
      setHasInvisible(invisibleDetected);
    } catch (err) {
      console.error("Scalar inspection error:", err);
    } finally {
      setLatency(performance.now() - t0);
    }
  };

  const handleInputChange = (val: string) => {
    setInput(val);
    startTransition(() => {
      inspectText(val);
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.scalar.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.scalar.desc}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleInputChange("தமிழ்")}
            className="text-xs font-tamil text-[var(--color-semman)] border-[var(--color-semman)]/30"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            <span>தமிழ்</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleInputChange("ஸ்ரீ")}
            className="text-xs font-tamil"
          >
            <span>ஸ்ரீ</span>
          </Button>
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
            {t.tools.scalar.inputLabel}
          </label>
          {latency > 0 && <Badge variant="mono">{latency.toFixed(1)} ms</Badge>}
        </div>
        <Textarea
          value={input}
          onChange={(e) => handleInputChange(e.target.value)}
          placeholder={t.tools.scalar.inputPlaceholder}
          className="min-h-[100px]"
        />
      </div>

      {/* Invisible Control Status Notice */}
      {hasInvisible ? (
        <Card className="bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/50 p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
          <p className="text-xs sm:text-sm font-tamil font-medium text-red-800 dark:text-red-300">
            {t.tools.scalar.invisibleNotice}
          </p>
        </Card>
      ) : (
        <Card className="bg-[var(--bg-surface)] p-4 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-[var(--color-semman)] shrink-0" />
          <p className="text-xs sm:text-sm font-tamil text-[var(--color-muted)]">
            {t.tools.scalar.noInvisibleNotice}
          </p>
        </Card>
      )}

      {/* Clusters and Scalars Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Grapheme Clusters */}
        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil uppercase tracking-wide">
              {t.tools.scalar.clusterCountLabel} ({clusters.length})
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {clusters.map((c, i) => (
              <div
                key={i}
                className="px-3.5 py-2 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)] text-center"
              >
                <div className="text-xl font-tamil font-bold text-[var(--color-mai)]">
                  {c}
                </div>
                <div className="text-[10px] font-mono-tamil text-[var(--color-muted)] mt-0.5">
                  #{i + 1}
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Unicode Codepoints */}
        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil uppercase tracking-wide">
              {t.tools.scalar.scalarCountLabel} ({scalars.length})
            </span>
            <CopyButton
              text={scalars.map((s) => `${s.char} (${s.hex})`).join(", ")}
              size="sm"
              variant="ghost"
            />
          </div>
          <div className="flex flex-wrap gap-2 pt-1 max-h-[300px] overflow-y-auto">
            {scalars.map((s, i) => (
              <div
                key={i}
                className={`px-3 py-1.5 rounded-xl border text-center transition-all ${
                  s.isInvisible
                    ? "bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-700 dark:text-red-300 font-bold"
                    : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)]"
                }`}
              >
                <div className="text-base font-tamil font-semibold">{s.char}</div>
                <div className="text-[10px] font-mono-tamil text-[var(--color-semman)] font-bold">
                  {s.hex}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
