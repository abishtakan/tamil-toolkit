import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import { analyzeTamilText, AnalyzedSyllable, isEngineReady, tt } from "../../lib/engine";
import { ToolHeader } from "../common/ToolHeader";
import { Textarea } from "../ui/textarea";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Layers, Code, Type, Clock, Scale, Link2 } from "lucide-react";
import type * as ttTypes from "tamil-toolkit";

const SAMPLE_TEXT = "தமிழ்நாடு வாழ்க! அஃது சீரிளமைத் திறம்";
const MEI_CONSONANTS = [
  "க்", "ங்", "ச்", "ஞ்", "ட்", "ண்", "த்", "ந்", "ப்",
  "ம்", "ய்", "ர்", "ல்", "வ்", "ழ்", "ள்", "ற்", "ன்",
];
const UYIR_VOWELS = [
  "அ", "ஆ", "இ", "ஈ", "உ", "ஊ", "எ", "ஏ", "ஐ", "ஒ", "ஓ", "ஔ",
];

type LetterSubTab = "breakdown" | "composer" | "olippasai";

interface LetterAnalyzerProps {
  engineReady?: boolean;
}

export function LetterAnalyzer({ engineReady }: LetterAnalyzerProps) {
  const { t, language } = useLanguage();
  const ready = engineReady ?? isEngineReady();
  const [activeTab, setActiveTab] = useState<LetterSubTab>("breakdown");
  const [inputText, setInputText] = useState(SAMPLE_TEXT);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);

  // Composer state
  const [selectedMei, setSelectedMei] = useState("க்");
  const [selectedUyir, setSelectedUyir] = useState("அ");

  // Olippasai & cognate state
  const [olippasaiInput, setOlippasaiInput] = useState("தங்கம்");
  const [cognateLeft, setCognateLeft] = useState("க்");
  const [cognateRight, setCognateRight] = useState("ங்");

  const report = useMemo(() => {
    void ready;
    return analyzeTamilText(inputText);
  }, [inputText, ready]);

  const selectedSyllable: AnalyzedSyllable | null = useMemo(() => {
    if (report.syllables.length === 0) return null;
    return report.syllables[selectedIndex] || report.syllables[0];
  }, [report, selectedIndex]);

  const composerResult = useMemo(() => {
    if (!ready) return { composed: "", maathirai: 0, series: [] as { uyir: string; glyph: string }[] };
    try {
      const composed = tt.compose_uyirmei(selectedMei, selectedUyir);
      const maathirai = tt.baseline_maathirai(composed);
      const series = UYIR_VOWELS.map((uyir) => ({
        uyir,
        glyph: tt.compose_uyirmei(selectedMei, uyir),
      }));
      return { composed, maathirai, series };
    } catch {
      return { composed: "", maathirai: 0, series: [] };
    }
  }, [selectedMei, selectedUyir, ready]);

  const olippasaiResult = useMemo(() => {
    if (!ready || !olippasaiInput.trim()) return [];
    try {
      return tt.get_olippasai(olippasaiInput);
    } catch {
      return [];
    }
  }, [olippasaiInput, ready]);

  const cognateResult = useMemo(() => {
    if (!ready || !cognateLeft.trim() || !cognateRight.trim()) {
      return { areCognates: false, leftPair: null as string | null, rightPair: null as string | null };
    }
    try {
      return {
        areCognates: tt.are_cognates(cognateLeft.trim(), cognateRight.trim()),
        leftPair: tt.get_cognate(cognateLeft.trim()),
        rightPair: tt.get_cognate(cognateRight.trim()),
      };
    } catch {
      return { areCognates: false, leftPair: null, rightPair: null };
    }
  }, [cognateLeft, cognateRight, ready]);

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

  const getQuantityLabel = (quantity?: ttTypes.LetterQuantity | null): string => {
    switch (quantity) {
      case "kuril":
        return language === "ta" ? "குறில் (Short)" : "Short (Kuril)";
      case "nedil":
        return language === "ta" ? "நெடில் (Long)" : "Long (Nedil)";
      case "mei":
        return language === "ta" ? "மெய் / ஒற்று (Consonant)" : "Consonant (Mei)";
      case "aytham":
        return language === "ta" ? "ஆய்தம் (Visarga)" : "Aytham (Visarga)";
      default:
        return "—";
    }
  };

  const subTabs: { id: LetterSubTab; label: string }[] = [
    { id: "breakdown", label: t.tools.letter.tabBreakdown },
    { id: "composer", label: t.tools.letter.tabComposer },
    { id: "olippasai", label: t.tools.letter.tabOlippasai },
  ];

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.letter.title}
        description={t.tools.letter.desc}
        actions={
          activeTab === "breakdown" ? (
            <>
              <Button type="button" variant="outline" size="sm" onClick={loadSample}>
                {t.actions.loadSample}
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={clearText} disabled={!inputText}>
                {t.actions.clear}
              </Button>
            </>
          ) : undefined
        }
      />

      {/* Sub-navigation Pills */}
      <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
        {subTabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-3.5 py-1.5 min-h-[36px] rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
              activeTab === tab.id
                ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "breakdown" && (
        <>

      {/* Input Area */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label htmlFor="letter-analyzer-input" className="text-xs font-semibold text-[var(--color-mai)]">
            {t.tools.letter.inputLabel}
          </label>
          <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--color-muted)]">
            <span>
              {t.tools.letter.syllablesCount}:{" "}
              <strong className="font-mono-tamil text-[var(--color-mai)]">{report.total_letters}</strong>
            </span>
            <span>·</span>
            <span>
              {t.tools.letter.uyirCount}:{" "}
              <strong className="font-mono-tamil text-[var(--color-sandhanam)]">{report.vowel_count}</strong>
            </span>
            <span>·</span>
            <span>
              {t.tools.letter.meiCount}:{" "}
              <strong className="font-mono-tamil text-[var(--color-semman)]">{report.consonant_count}</strong>
            </span>
            <span>·</span>
            <span>
              {t.tools.letter.uyirmeiCount}:{" "}
              <strong className="font-mono-tamil text-[var(--color-mai)]">{report.uyirmei_count}</strong>
            </span>
            {report.grantha_count > 0 && (
              <>
                <span>·</span>
                <span>
                  {t.tools.letter.granthaCount}:{" "}
                  <strong className="font-mono-tamil text-[var(--color-mai)]">{report.grantha_count}</strong>
                </span>
              </>
            )}
          </div>
        </div>
        <Textarea
          id="letter-analyzer-input"
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

      {/* Main Layout: Syllables Ribbon (Left) + Detail Breakdown (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7 space-y-2.5">
          <span className="text-xs text-[var(--color-muted)] block px-1">
            {t.tools.letter.selectPrompt}
          </span>

          <Card className="p-4 flex flex-wrap gap-2 max-h-[420px] overflow-y-auto">
            {report.syllables.map((syl, i) => {
              const isSelected = selectedIndex === i;
              return (
                <button
                  key={i}
                  type="button"
                  onClick={() => setSelectedIndex(i)}
                  className={`px-3.5 py-2 rounded-xl border text-center transition-colors flex items-center gap-1.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] ${
                    isSelected
                      ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-bold"
                      : "border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] hover:border-[var(--color-semman)]/50"
                  }`}
                >
                  <span className="text-lg font-tamil">{syl.raw}</span>
                  <span className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                    {i + 1}
                  </span>
                </button>
              );
            })}

            {report.syllables.length === 0 && (
              <div className="py-12 w-full text-center text-xs text-[var(--color-muted)]">
                {t.tools.letter.inputPlaceholder}
              </div>
            )}
          </Card>
        </div>

        {/* Selected Syllable Inspector Card */}
        <div className="lg:col-span-5">
          {selectedSyllable ? (
            <Card className="p-6 sticky top-20 space-y-5">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1.5">
                  <span className="text-[11px] text-[var(--color-muted)] uppercase tracking-wider block">
                    {t.tools.letter.selectedSyllableHeading} #{selectedSyllable.index + 1}
                  </span>
                  <Badge variant={getKindBadgeVariant(selectedSyllable.kind)}>
                    {getKindLabel(selectedSyllable.kind)}
                  </Badge>
                </div>
                <CopyButton text={selectedSyllable.raw} label={t.actions.copy} size="sm" variant="outline" />
              </div>

              <div className="rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-6 flex flex-col items-center justify-center text-center space-y-2">
                <span className="text-5xl sm:text-6xl font-tamil select-all text-[var(--color-mai)]">
                  {selectedSyllable.raw}
                </span>
                {selectedSyllable.base_consonant && selectedSyllable.vowel && (
                  <p className="text-sm font-tamil font-semibold text-[var(--color-semman)]">
                    {selectedSyllable.base_consonant} + {selectedSyllable.vowel} = {selectedSyllable.raw}
                  </p>
                )}
                <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                  {selectedSyllable.codepoints.join(" + ")}
                </span>
              </div>

              <div className="space-y-3 divide-y divide-[var(--border-line)] text-xs">
                {selectedSyllable.base_consonant && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Type className="w-3.5 h-3.5" />
                      {t.tools.letter.rootConsonantLabel}
                    </span>
                    <span className="font-tamil font-bold text-sm text-[var(--color-semman)]">
                      {selectedSyllable.base_consonant}
                    </span>
                  </div>
                )}

                {selectedSyllable.vowel && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)]">
                      {t.tools.letter.vowelLabel}
                    </span>
                    <span className="font-tamil font-bold text-sm text-[var(--color-sandhanam)]">
                      {selectedSyllable.vowel}
                    </span>
                  </div>
                )}

                {selectedSyllable.quantity && selectedSyllable.quantity !== "other" && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Scale className="w-3.5 h-3.5" />
                      {t.tools.letter.quantityLabel}
                    </span>
                    <Badge variant="outline" className="font-semibold">
                      {getQuantityLabel(selectedSyllable.quantity)}
                    </Badge>
                  </div>
                )}

                {selectedSyllable.maathirai != null && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5" />
                      {t.tools.letter.moraLabel}
                    </span>
                    <span className="font-mono-tamil font-bold text-sm text-[var(--color-mai)]">
                      {selectedSyllable.maathirai}{" "}
                      <span className="text-xs font-tamil-sans text-[var(--color-muted)] font-normal">
                        {language === "ta" ? "மாத்திரை" : "mora"}
                      </span>
                    </span>
                  </div>
                )}

                {selectedSyllable.cognate && (
                  <div className="pt-2.5 flex items-center justify-between">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Link2 className="w-3.5 h-3.5" />
                      {t.tools.letter.cognateLabel}
                    </span>
                    <span className="font-tamil font-bold text-sm text-[var(--color-sandhanam)]">
                      {(selectedSyllable.base_consonant || selectedSyllable.raw)} ↔ {selectedSyllable.cognate}
                    </span>
                  </div>
                )}

                {selectedSyllable.vowel_sign_name_ta && (
                  <div className="pt-2.5 flex flex-col gap-1">
                    <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5" />
                      {t.tools.letter.vowelSignLabel}
                    </span>
                    <p className="text-xs font-tamil text-[var(--color-mai)] font-medium">
                      {selectedSyllable.vowel_sign_name_ta}
                    </p>
                  </div>
                )}

                <div className="pt-2.5 flex flex-col gap-1">
                  <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                    <Code className="w-3.5 h-3.5" />
                    {t.tools.letter.codepointsLabel}
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
            <Card className="p-8 text-center text-xs text-[var(--color-muted)]">
              {t.tools.letter.selectPrompt}
            </Card>
          )}
        </div>
      </div>

      <StickyActionBar
        outputText={
          activeTab === "breakdown"
            ? selectedSyllable?.raw || ""
            : activeTab === "composer"
              ? composerResult.composed
              : olippasaiInput
        }
        onClear={clearText}
      />
        </>
      )}

      {activeTab === "composer" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <Card className="p-5 lg:col-span-7 space-y-5">
              <div className="space-y-2">
                <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider block">
                  {t.tools.letter.composerMeiLabel}
                </span>
                <div className="grid grid-cols-6 sm:grid-cols-9 gap-1.5">
                  {MEI_CONSONANTS.map((mei) => (
                    <button
                      key={mei}
                      type="button"
                      onClick={() => setSelectedMei(mei)}
                      className={`py-2 rounded-lg border font-tamil text-base cursor-pointer transition-colors ${
                        selectedMei === mei
                          ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold"
                          : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                      }`}
                    >
                      {mei}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider block">
                  {t.tools.letter.composerUyirLabel}
                </span>
                <div className="grid grid-cols-6 gap-1.5">
                  {UYIR_VOWELS.map((uyir) => (
                    <button
                      key={uyir}
                      type="button"
                      onClick={() => setSelectedUyir(uyir)}
                      className={`py-2 rounded-lg border font-tamil text-base cursor-pointer transition-colors ${
                        selectedUyir === uyir
                          ? "bg-[var(--color-sandhanam)] text-[#faf7f2] border-[var(--color-sandhanam)] font-bold"
                          : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-sandhanam)]"
                      }`}
                    >
                      {uyir}
                    </button>
                  ))}
                </div>
              </div>
            </Card>

            <Card className="p-6 lg:col-span-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                  {t.tools.letter.composedResultLabel}
                </span>
                {composerResult.composed && (
                  <CopyButton text={composerResult.composed} size="sm" variant="outline" />
                )}
              </div>

              <div className="rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-6 flex flex-col items-center justify-center text-center space-y-2">
                <span className="text-6xl font-tamil text-[var(--color-mai)] select-all">
                  {composerResult.composed || "—"}
                </span>
                <p className="text-sm font-tamil font-semibold text-[var(--color-semman)]">
                  {selectedMei} + {selectedUyir} = {composerResult.composed}
                </p>
                <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                  {Array.from(composerResult.composed)
                    .map((ch) => `U+${(ch.codePointAt(0) ?? 0).toString(16).toUpperCase().padStart(4, "0")}`)
                    .join(" + ")}
                  {" · "}
                  {composerResult.maathirai} {language === "ta" ? "மாத்திரை" : "mora"}
                </span>
              </div>
            </Card>
          </div>

          <Card className="p-5 space-y-3">
            <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider block">
              {t.tools.letter.allVowelsRowLabel} ({selectedMei})
            </span>
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-12 gap-2">
              {composerResult.series.map((item) => (
                <button
                  key={item.uyir}
                  type="button"
                  onClick={() => setSelectedUyir(item.uyir)}
                  className={`p-2.5 rounded-xl border text-center cursor-pointer transition-colors ${
                    selectedUyir === item.uyir
                      ? "bg-[var(--color-semman-light)] border-[var(--color-semman)] text-[var(--color-semman)] font-bold"
                      : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]/50"
                  }`}
                >
                  <div className="text-xl font-tamil">{item.glyph}</div>
                  <div className="text-[10px] font-tamil text-[var(--color-muted)] mt-0.5">{item.uyir}</div>
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}

      {activeTab === "olippasai" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-semibold text-[var(--color-mai)]">
              {t.tools.letter.olippasaiHeading}
            </h2>
            <input
              type="text"
              value={olippasaiInput}
              onChange={(e) => setOlippasaiInput(e.target.value)}
              placeholder={t.tools.letter.inputPlaceholder}
              className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-base text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
            />
            <div className="space-y-2">
              {olippasaiResult.map((unit, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-xl font-tamil font-bold text-[var(--color-mai)]">{unit.text}</span>
                    <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                      letters {unit.start_letter_idx}..{unit.end_letter_idx} · bytes {unit.start_byte}..{unit.end_byte}
                    </span>
                  </div>
                  <Badge variant={unit.has_coda ? "terracotta" : "outline"} className="text-[11px]">
                    {unit.has_coda ? `${t.tools.letter.codaYes} (${unit.coda_count})` : t.tools.letter.codaNo}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-semibold text-[var(--color-mai)]">
              {t.tools.letter.cognateCheckHeading}
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <input
                type="text"
                value={cognateLeft}
                onChange={(e) => setCognateLeft(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-lg text-center text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
              />
              <input
                type="text"
                value={cognateRight}
                onChange={(e) => setCognateRight(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-lg text-center text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
              />
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2 text-center">
              <Badge
                variant={cognateResult.areCognates ? "terracotta" : "outline"}
                className="text-xs px-3 py-1"
              >
                {cognateResult.areCognates ? t.tools.letter.cognateYes : t.tools.letter.cognateNo}
              </Badge>
              <div className="text-xs text-[var(--color-muted)] flex items-center justify-center gap-4 pt-1 font-tamil">
                <span>
                  {cognateLeft} ↔ {cognateResult.leftPair ?? "—"}
                </span>
                <span>·</span>
                <span>
                  {cognateRight} ↔ {cognateResult.rightPair ?? "—"}
                </span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
