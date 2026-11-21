import { useState, useMemo } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Textarea } from "../ui/textarea";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { AlertTriangle, CheckCircle } from "lucide-react";

interface ScalarDetail {
  char: string;
  codePoint: number;
  hex: string;
  isInvisible: boolean;
}

function formatControlLabel(cp: number): string {
  switch (cp) {
    case 0x200d:
      return "[ZWJ]";
    case 0x200c:
      return "[ZWNJ]";
    case 0xfeff:
      return "[BOM]";
    case 0x00ad:
      return "[SHY]";
    default:
      return "[CTRL]";
  }
}

// Construct sample with ZWJ and NFD sequence via code points so source stays clean NFC
const SAMPLE_WITH_ZWJ_NFD =
  String.fromCodePoint(0x0ba4, 0x0bae, 0x0bbf, 0x0bb4, 0x0bcd, 0x200d) +
  " " +
  String.fromCodePoint(0x0b95, 0x0bc6, 0x0bbe);

interface ScalarInspectorProps {
  engineReady?: boolean;
}

export function ScalarInspector({ engineReady }: ScalarInspectorProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [input, setInput] = useState("தமிழ்");

  const inspected = useMemo(() => {
    if (!input) {
      return {
        scalars: [] as ScalarDetail[],
        clusters: [] as string[],
        hasInvisible: false,
      };
    }

    let clusters: string[] = [];
    let rustInspection: tt.Inspection | null = null;
    if (ready) {
      try {
        rustInspection = tt.inspect_tamil_string(input);
        clusters = rustInspection.letters.map((l) => l.text);
      } catch {
        try {
          clusters = tt.get_letters(input) || [];
        } catch {
          clusters = Array.from(input);
        }
      }
    } else {
      clusters = Array.from(input);
    }

    const scalars: ScalarDetail[] = [];
    let hasInvisible = false;

    for (const char of input) {
      const cp = char.codePointAt(0) || 0;
      const hex = `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`;
      const isInvisible =
        cp === 0x200c || cp === 0x200d || cp === 0xfeff || cp === 0x00ad;
      if (isInvisible) hasInvisible = true;

      scalars.push({
        char: isInvisible ? formatControlLabel(cp) : char,
        codePoint: cp,
        hex,
        isInvisible,
      });
    }

    return { scalars, clusters, hasInvisible, rustInspection };
  }, [input, ready]);

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.scalar.title}
        description={t.tools.scalar.desc}
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setInput("தமிழ்")}
              className="font-tamil"
            >
              தமிழ்
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setInput("ஸ்ரீ")}
              className="font-tamil"
            >
              ஸ்ரீ
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setInput(SAMPLE_WITH_ZWJ_NFD)}
            >
              {t.tools.scalar.sampleInvisible}
            </Button>
          </>
        }
      />

      {/* Input */}
      <div className="space-y-2">
        <label htmlFor="scalar-inspector-input" className="text-xs font-semibold text-[var(--color-mai)] block">
          {t.tools.scalar.inputLabel}
        </label>
        <Textarea
          id="scalar-inspector-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t.tools.scalar.inputPlaceholder}
          className="min-h-[100px]"
        />
      </div>

      {/* Invisible Control Status Notice */}
      {inspected.hasInvisible ? (
        <Card className="bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-900/50 p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400 shrink-0" />
          <p className="text-xs sm:text-sm font-medium text-red-800 dark:text-red-300">
            {t.tools.scalar.invisibleNotice}
          </p>
        </Card>
      ) : (
        <Card className="p-4 flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-[var(--color-semman)] shrink-0" />
          <p className="text-xs sm:text-sm text-[var(--color-muted)]">
            {t.tools.scalar.noInvisibleNotice}
          </p>
        </Card>
      )}

      {/* Structural Rust Inspection */}
      {inspected.rustInspection && (
        <Card className="p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-line)] pb-2.5">
            <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
              {t.tools.scalar.rustInspectHeading}
            </span>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge variant={inspected.rustInspection.is_nfc ? "terracotta" : "outline"}>
                {t.tools.scalar.nfcStatusLabel}: {inspected.rustInspection.is_nfc ? "Yes" : "No"}
              </Badge>
              <Badge variant={inspected.rustInspection.is_nfd ? "terracotta" : "outline"}>
                {t.tools.scalar.nfdStatusLabel}: {inspected.rustInspection.is_nfd ? "Yes" : "No"}
              </Badge>
              <Badge variant="outline">
                {t.tools.scalar.ezhuthuCountLabel}: {inspected.rustInspection.ezhuthu_count}
              </Badge>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-medium text-[var(--color-muted)] block">
              {t.tools.scalar.classificationsHeading}
            </span>
            <div className="flex flex-wrap gap-2">
              {inspected.rustInspection.letters.map((letter, idx) => (
                <div
                  key={idx}
                  className="px-3 py-1.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center gap-2"
                >
                  <span className="text-lg font-tamil text-[var(--color-mai)]">{letter.text}</span>
                  <span className="text-[10px] font-mono-tamil px-1.5 py-0.5 rounded bg-[var(--bg-raised)] text-[var(--color-semman)]">
                    {letter.classification}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* Clusters and Scalars Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
              {t.tools.scalar.clusterCountLabel} ({inspected.clusters.length})
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {inspected.clusters.map((c, i) => (
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

        <Card className="p-5 space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
              {t.tools.scalar.scalarCountLabel} ({inspected.scalars.length})
            </span>
            <CopyButton
              text={inspected.scalars.map((s) => `${s.char} (${s.hex})`).join(", ")}
              size="sm"
              variant="ghost"
            />
          </div>
          <div className="flex flex-wrap gap-2 pt-1 max-h-[300px] overflow-y-auto">
            {inspected.scalars.map((s, i) => (
              <div
                key={i}
                className={`px-3 py-1.5 rounded-xl border text-center transition-colors ${
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
