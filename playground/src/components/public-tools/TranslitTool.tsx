import { useState, useMemo } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { AlertCircle, ArrowLeftRight, X } from "lucide-react";

export interface SchemeMeta {
  id: string;
  labelEn: string;
  labelTa: string;
  bidirectional: boolean;
  sampleLatin: string;
  sampleTamil: string;
  hint: string;
}

export const TRANSLIT_SCHEMES: readonly SchemeMeta[] = [
  {
    id: "iso-15919",
    labelEn: "ISO 15919",
    labelTa: "ISO 15919",
    bidirectional: true,
    sampleLatin: "tamiḻ moḻi",
    sampleTamil: "தமிழ் மொழி",
    hint: "ā ī ū ē ō · ṭ ṇ ṉ ṟ ḷ ḻ · ḵ (ஃ)",
  },
  {
    id: "madras-lexicon",
    labelEn: "Madras Lexicon",
    labelTa: "சென்னை அகராதி",
    bidirectional: true,
    sampleLatin: "tamiḻ nāṭu",
    sampleTamil: "தமிழ் நாடு",
    hint: "ā ī ū ē ō · ṭ ṇ ṉ ṟ ḷ ḻ · ḥ (ஃ)",
  },
  {
    id: "itrans",
    labelEn: "ITRANS",
    labelTa: "ITRANS",
    bidirectional: true,
    sampleLatin: "tamizh vaNakkam",
    sampleTamil: "தமிழ் வணக்கம்",
    hint: "aa ii uu E O · T=ட, N=ண, ^n=ன, R=ற, L=ள, zh=ழ",
  },
  {
    id: "harvard-kyoto",
    labelEn: "Harvard-Kyoto",
    labelTa: "ஹார்வர்ட்-கியோட்டோ",
    bidirectional: true,
    sampleLatin: "tamiZ vaNakkam",
    sampleTamil: "தமிழ் வணக்கம்",
    hint: "A I U E O · T=ட, N=ண, X=ன, R=ற, L=ள, Z=ழ, H=ஃ",
  },
  {
    id: "phonetic-v1",
    labelEn: "Phonetic (Tanglish)",
    labelTa: "ஒலியியல் (Tanglish)",
    bidirectional: true,
    sampleLatin: "vaNakkam thamizh",
    sampleTamil: "வணக்கம் தமிழ்",
    hint: "th=த, t=ட, nh=ந, n=ன, N=ண, zh=ழ, L=ள, R=ற",
  },
  {
    id: "tamil99",
    labelEn: "Tamil99",
    labelTa: "தமிழ்99",
    bidirectional: false,
    sampleLatin: "lks/f",
    sampleTamil: "தமிழ்",
    hint: "l=த, k=ம, s=ி, /=ழ, f=் (auto-pulli on repeated consonants)",
  },
  {
    id: "anjal-phonetic",
    labelEn: "Anjal Phonetic",
    labelTa: "அஞ்சல் ஒலியியல்",
    bidirectional: false,
    sampleLatin: "thamizh vaNakkam",
    sampleTamil: "தமிழ் வணக்கம்",
    hint: "th=த, t=ட, nh=ந, n=ன, N=ண, zh=ழ, L=ள, R=ற",
  },
  {
    id: "suratha-bamini",
    labelEn: "Suratha Bamini",
    labelTa: "சுரதா பாமினி",
    bidirectional: false,
    sampleLatin: "jkpo; tzf;fk;",
    sampleTamil: "தமிழ் வணக்கம்",
    hint: "j=த, k=ம, p=ி, o=ழ, ;=், n/N/i=ெ/ே/ை",
  },
];

const ALL_SAMPLES = new Set<string>(
  TRANSLIT_SCHEMES.flatMap((s) => [s.sampleLatin, s.sampleTamil])
);

interface TranslitToolProps {
  engineReady?: boolean;
}

export function TranslitTool({ engineReady }: TranslitToolProps) {
  const { language, t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [scheme, setScheme] = useState<string>("iso-15919");
  const [direction, setDirection] = useState<"to_tamil" | "to_latin">("to_tamil");
  const [input, setInput] = useState<string>(TRANSLIT_SCHEMES[0].sampleLatin);

  const activeScheme = useMemo(
    () => TRANSLIT_SCHEMES.find((s) => s.id === scheme) ?? TRANSLIT_SCHEMES[0],
    [scheme]
  );

  const effectiveDirection: "to_tamil" | "to_latin" = activeScheme.bidirectional
    ? direction
    : "to_tamil";

  const result = useMemo(() => {
    if (!ready || !input.trim()) {
      return { output: "", error: null as string | null };
    }
    try {
      const output = tt.transliterate(input, activeScheme.id, effectiveDirection);
      return { output, error: null as string | null };
    } catch (err) {
      return {
        output: "",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }, [ready, input, activeScheme.id, effectiveDirection]);

  const handleSelectScheme = (next: SchemeMeta) => {
    const nextDir: "to_tamil" | "to_latin" = next.bidirectional ? direction : "to_tamil";
    setScheme(next.id);
    if (!next.bidirectional) {
      setDirection("to_tamil");
    }
    if (!input.trim() || ALL_SAMPLES.has(input)) {
      setInput(nextDir === "to_tamil" ? next.sampleLatin : next.sampleTamil);
    }
  };

  const handleLoadSample = () => {
    setInput(
      effectiveDirection === "to_tamil"
        ? activeScheme.sampleLatin
        : activeScheme.sampleTamil
    );
  };

  const handleSwap = () => {
    if (!activeScheme.bidirectional) return;
    const nextDir = effectiveDirection === "to_tamil" ? "to_latin" : "to_tamil";
    setDirection(nextDir);
    if (result.output) {
      setInput(result.output);
    }
  };

  const handleClear = () => setInput("");

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.translit.title}
        description={t.tools.translit.desc}
        actions={
          <>
            <Button variant="outline" size="sm" onClick={handleLoadSample}>
              {t.actions.loadSample}
            </Button>
            {activeScheme.bidirectional && (
              <Button variant="outline" size="sm" onClick={handleSwap}>
                <ArrowLeftRight className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
                <span>
                  {effectiveDirection === "to_tamil"
                    ? t.tools.translit.dirToTamil
                    : t.tools.translit.dirToLatin}
                </span>
              </Button>
            )}
          </>
        }
      />

      {/* Scheme Selector */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
            {t.tools.translit.schemeLabel}
          </span>
          <Badge variant={activeScheme.bidirectional ? "terracotta" : "outline"} className="text-[11px]">
            {activeScheme.bidirectional
              ? t.tools.translit.bidirectionalBadge
              : t.tools.translit.keyboardOnlyBadge}
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          {TRANSLIT_SCHEMES.map((s) => {
            const isActive = s.id === activeScheme.id;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => handleSelectScheme(s)}
                data-active={isActive}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors select-none border min-h-[36px] cursor-pointer ${
                  isActive
                    ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                    : "bg-[var(--bg-surface)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
                }`}
              >
                {language === "ta" ? s.labelTa : s.labelEn}
              </button>
            );
          })}
        </div>
        <p className="text-xs font-mono-tamil text-[var(--color-muted)]">
          {activeScheme.hint}
        </p>
      </div>

      {result.error && (
        <div className="p-3 rounded-lg border border-red-300 bg-red-50/70 text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{result.error}</span>
        </div>
      )}

      {/* Split Workspace */}
      <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[var(--border-line)]">
        {/* Source Pane */}
        <div className="flex flex-col">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {effectiveDirection === "to_tamil"
                ? t.tools.translit.inputLatinLabel
                : t.tools.translit.inputTamilLabel}
            </span>
            {input && (
              <button
                type="button"
                onClick={handleClear}
                aria-label={t.actions.clear}
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
            placeholder={t.tools.translit.inputPlaceholder}
            className="w-full flex-1 min-h-[220px] sm:min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>

        {/* Output Pane */}
        <div className="flex flex-col bg-[var(--bg-canvas)]/40">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {effectiveDirection === "to_tamil"
                ? t.tools.translit.outputTamilLabel
                : t.tools.translit.outputLatinLabel}
            </span>
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
            placeholder={t.tools.translit.outputPlaceholder}
            className="w-full flex-1 min-h-[220px] sm:min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>
      </div>

      <StickyActionBar
        outputText={result.output}
        onClear={handleClear}
        onSwap={activeScheme.bidirectional ? handleSwap : undefined}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
        swapLabel={t.actions.swap}
      />
    </div>
  );
}
