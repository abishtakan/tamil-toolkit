import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import { analyzeTamilText, AnalyzedSyllable } from "../../lib/engine";
import { Textarea } from "../ui/textarea";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Sparkles, Layers, Code, Type } from "lucide-react";

const SAMPLE_TEXT = "தமிழ்நாடு வாழ்க! அஃது சீரிளமைத் திறம்";

export function LetterAnalyzer() {
  const { t, language } = useLanguage();
  const [inputText, setInputText] = useState(SAMPLE_TEXT);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  const report = useMemo(() => {
    return analyzeTamilText(inputText);
  }, [inputText]);

  const selectedSyllable: AnalyzedSyllable | null = useMemo(() => {
    if (report.syllables.length === 0) return null;
    return report.syllables[selectedIndex] || report.syllables[0];
  }, [report, selectedIndex]);

  const loadSample = () => {
    setInputText(SAMPLE_TEXT);
    setSelectedIndex(0);
  };

  const clearText = () => {
    setInputText("");
    setSelectedIndex(0);
  };

  const getKindBadgeVariant = (kind: string): "default" | "terracotta" | "sandhanam" | "outline" | "mono" => {
    switch (kind) {
      case "uyir":
        return "sandhanam";
      case "mei":
        return "terracotta";
      case "uyirmei":
        return "default";
      case "aaytham":
        return "sandhanam";
      case "grantha":
        return "outline";
      default:
        return "outline";
    }
  };

  const getKindLabel = (kind: string): string => {
    switch (kind) {
      case "uyir":
        return language === "ta" ? "உயிர் (Vowel)" : "Vowel (Uyir)";
      case "mei":
        return language === "ta" ? "மெய் (Consonant)" : "Consonant (Mei)";
      case "uyirmei":
        return language === "ta" ? "உயிர்மெய் (Composite)" : "Composite (Uyirmei)";
      case "aaytham":
        return language === "ta" ? "ஆய்தம் (Visarga)" : "Aytham (Visarga)";
      case "grantha":
        return language === "ta" ? "கிரந்தம் (Grantha)" : "Grantha Loan Letter";
      default:
        return language === "ta" ? "பிற குறியீடு" : "Other / Symbol";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-150">
      {/* Title & Description Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
              {t.tools.letter.title}
            </h2>
            <Badge variant="terracotta">Grammatical Parser</Badge>
          </div>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans max-w-2xl leading-relaxed">
            {t.tools.letter.desc}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button variant="outline" size="sm" onClick={loadSample}>
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            {t.actions.loadSample}
          </Button>
          <Button variant="ghost" size="sm" onClick={clearText} disabled={!inputText}>
            {t.actions.clear}
          </Button>
        </div>
      </div>

      {/* Input Textarea Area */}
      <div className="space-y-2">
        <label className="text-xs font-tamil font-semibold text-[var(--color-mai)] block">
          {t.tools.letter.inputLabel}
        </label>
        <Textarea
          value={inputText}
          onChange={(e) => {
            setInputText(e.target.value);
            setSelectedIndex(0);
          }}
          placeholder={t.tools.letter.inputPlaceholder}
          rows={3}
          className="font-tamil text-base sm:text-lg leading-relaxed resize-y"
        />
      </div>

      {/* Summary Statistics Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-center">
          <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-0.5">
            {t.tools.letter.syllablesCount}
          </span>
          <span className="text-xl font-mono-tamil font-bold text-[var(--color-mai)]">
            {report.total_letters}
          </span>
        </div>

        <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-center">
          <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-0.5">
            {t.tools.letter.uyirCount}
          </span>
          <span className="text-xl font-mono-tamil font-bold text-[var(--color-sandhanam)]">
            {report.vowel_count}
          </span>
        </div>

        <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-center">
          <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-0.5">
            {t.tools.letter.meiCount}
          </span>
          <span className="text-xl font-mono-tamil font-bold text-[var(--color-semman)]">
            {report.consonant_count}
          </span>
        </div>

        <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-center">
          <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-0.5">
            {t.tools.letter.uyirmeiCount}
          </span>
          <span className="text-xl font-mono-tamil font-bold text-[var(--color-mai)]">
            {report.uyirmei_count}
          </span>
        </div>

        <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-center col-span-2 sm:col-span-1">
          <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-0.5">
            {t.tools.letter.granthaCount}
          </span>
          <span className="text-xl font-mono-tamil font-bold text-[var(--color-muted)]">
            {report.grantha_count}
          </span>
        </div>
      </div>

      {/* Main Layout: Syllables Ribbon (Left) + Detail Breakdown (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Syllable Chips List (Cols 1-7) */}
        <div className="lg:col-span-7 space-y-3">
          <span className="text-xs font-tamil text-[var(--color-muted)] block px-1">
            {t.tools.letter.selectPrompt}:
          </span>

          <div className="p-4 rounded-2xl border border-[var(--border-line)] bg-[var(--bg-surface)] flex flex-wrap gap-2 max-h-[400px] overflow-y-auto">
            {report.syllables.map((syl, i) => {
              const isSelected = selectedIndex === i;
              return (
                <button
                  key={i}
                  onClick={() => setSelectedIndex(i)}
                  className={`px-3.5 py-2 rounded-xl border text-center transition-colors flex items-center gap-1.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] ${
                    isSelected
                      ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-bold shadow-xs"
                      : "border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] hover:border-[var(--color-semman)]/50"
                  }`}
                >
                  <span className="text-lg font-tamil">{syl.raw}</span>
                  <span className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                    #{i + 1}
                  </span>
                </button>
              );
            })}

            {report.syllables.length === 0 && (
              <div className="py-12 w-full text-center text-xs text-[var(--color-muted)] font-tamil">
                {t.tools.letter.inputPlaceholder}
              </div>
            )}
          </div>
        </div>

        {/* Selected Syllable Inspector Card (Cols 8-12) */}
        <div className="lg:col-span-5">
          {selectedSyllable ? (
            <Card className="p-6 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl sticky top-20 space-y-5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-tamil text-[var(--color-muted)] uppercase tracking-wider block mb-1">
                    {t.tools.letter.selectedSyllableHeading} #{selectedSyllable.index + 1}
                  </span>
                  <Badge variant={getKindBadgeVariant(selectedSyllable.kind)}>
                    {getKindLabel(selectedSyllable.kind)}
                  </Badge>
                </div>
                <CopyButton text={selectedSyllable.raw} label={t.actions.copy} />
              </div>

              {/* Big Glyph Spotlight */}
              <div className="rounded-2xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-6 flex flex-col items-center justify-center text-center space-y-1">
                <span className="text-5xl sm:text-6xl font-tamil select-all text-[var(--color-mai)]">
                  {selectedSyllable.raw}
                </span>
                <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                  {selectedSyllable.codepoints.join(" + ")}
                </span>
              </div>

              {/* Decomposition Fields */}
              <div className="space-y-3 divide-y divide-[var(--border-line)] text-xs font-tamil">
                {selectedSyllable.base_consonant && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Type className="w-3.5 h-3.5" />
                      {t.tools.letter.rootConsonantLabel}:
                    </span>
                    <span className="font-tamil font-bold text-sm text-[var(--color-semman)]">
                      {selectedSyllable.base_consonant}
                    </span>
                  </div>
                )}

                {selectedSyllable.vowel && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      {t.tools.letter.vowelLabel}:
                    </span>
                    <span className="font-tamil font-bold text-sm text-[var(--color-sandhanam)]">
                      {selectedSyllable.vowel}
                    </span>
                  </div>
                )}

                {selectedSyllable.vowel_sign_name_ta && (
                  <div className="pt-2.5 flex flex-col gap-1">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      {t.tools.letter.vowelSignLabel}:
                    </span>
                    <p className="text-xs font-tamil text-[var(--color-mai)] font-medium">
                      {selectedSyllable.vowel_sign_name_ta}
                    </p>
                  </div>
                )}

                <div className="pt-2.5 flex flex-col gap-1">
                  <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                    <Code className="w-3.5 h-3.5" />
                    {t.tools.letter.codepointsLabel}:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {selectedSyllable.codepoints.map((cp, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded-lg bg-[var(--bg-canvas)] border border-[var(--border-line)] font-mono-tamil text-[11px] text-[var(--color-mai)]"
                      >
                        {cp}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          ) : (
            <Card className="p-8 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl text-center text-xs text-[var(--color-muted)] font-tamil">
              {t.tools.letter.selectPrompt}
            </Card>
          )}
        </div>
      </div>

      {/* Sticky Mobile Bar */}
      <StickyActionBar
        outputText={selectedSyllable?.raw || ""}
        onClear={clearText}
      />
    </div>
  );
}
