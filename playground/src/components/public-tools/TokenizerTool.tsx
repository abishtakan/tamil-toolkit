import { useState, useMemo } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { AlertCircle, X } from "lucide-react";

export type StopwordProfileId = tt.StopwordProfile;

export interface TokenizerSample {
  id: string;
  labelEn: string;
  labelTa: string;
  text: string;
}

export const TOKENIZER_SAMPLES: readonly TokenizerSample[] = [
  {
    id: "abbreviations",
    labelEn: "Honorifics & Currency",
    labelTa: "பட்டங்கள் & நாணயம்",
    text: "திரு. குமார் மற்றும் மு.க. அவர்கள் வந்தார். ரூ.100 அல்லது ரூ. 250 வழங்கப்பட்டது.",
  },
  {
    id: "schedule",
    labelEn: "SL Time & Examples",
    labelTa: "நேரம் & எடுத்துக்காட்டு",
    text: "பி.ப. 3.30 மணிக்கு கூட்டம் தொடங்கும். எ.கா.: தமிழ் அல்லது ஆங்கிலம் போன்ற மொழிகள்.",
  },
  {
    id: "mixed",
    labelEn: "Mixed Script & Offsets",
    labelTa: "கலப்பு உரை & நிலைகள்",
    text: "தமிழ் 2026 மற்றும் க்ஷ ஸ்ரீ 😊\nமு.ப. 9.00 மணிக்கு பதிவு செய்யவும்.",
  },
];

const STOPWORD_PROFILES: readonly {
  id: StopwordProfileId;
  labelEn: string;
  labelTa: string;
  hintEn: string;
  hintTa: string;
}[] = [
  {
    id: "none",
    labelEn: "None (All Tokens)",
    labelTa: "இல்லை (அனைத்தும்)",
    hintEn: "Default — retains every non-whitespace token.",
    hintTa: "இயல்பு — அனைத்து சொற்களையும் தக்கவைக்கும்.",
  },
  {
    id: "conservative",
    labelEn: "Conservative",
    labelTa: "குறுகிய பட்டியல்",
    hintEn: "Omits common conjunctions: மற்றும், அல்லது.",
    hintTa: "மற்றும், அல்லது ஆகியவற்றை நீக்கும்.",
  },
  {
    id: "broad",
    labelEn: "Broad Search",
    labelTa: "விரிவான தேடல்",
    hintEn: "Strict superset — omits மற்றும், அல்லது, போன்ற.",
    hintTa: "மற்றும், அல்லது, போன்ற ஆகியவற்றை நீக்கும்.",
  },
];

const KIND_STYLES: Record<tt.WordToken["kind"], string> = {
  abbreviation:
    "bg-amber-500/15 text-amber-800 dark:text-amber-300 border-amber-500/35",
  word:
    "bg-[var(--color-semman-light)] text-[var(--color-semman)] border-[var(--color-semman)]/30",
  number:
    "bg-sky-500/15 text-sky-800 dark:text-sky-300 border-sky-500/35",
  other:
    "bg-[var(--bg-raised)] text-[var(--color-muted)] border-[var(--border-line)]",
};

interface TokenizerToolProps {
  engineReady?: boolean;
}

export function TokenizerTool({ engineReady }: TokenizerToolProps) {
  const { language, t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [input, setInput] = useState<string>(TOKENIZER_SAMPLES[0].text);
  const [profile, setProfile] = useState<StopwordProfileId>("none");
  const [activeTab, setActiveTab] = useState<"words" | "sentences">("words");
  const [selectedTokenIndex, setSelectedTokenIndex] = useState<number | null>(null);

  const analysis = useMemo(() => {
    if (!ready) {
      return {
        words: [] as tt.WordToken[],
        unfilteredCount: 0,
        sentences: [] as tt.TokenizationSpan[],
        error: null as string | null,
      };
    }
    try {
      const words = tt.tokenize_words(input, profile);
      const unfilteredCount =
        profile === "none" ? words.length : tt.tokenize_words(input, "none").length;
      const sentences = tt.segment_sentences(input);
      return { words, unfilteredCount, sentences, error: null as string | null };
    } catch (err) {
      return {
        words: [] as tt.WordToken[],
        unfilteredCount: 0,
        sentences: [] as tt.TokenizationSpan[],
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }, [ready, input, profile]);

  const kindCounts = useMemo(() => {
    const counts = { word: 0, abbreviation: 0, number: 0, other: 0 };
    for (const tok of analysis.words) {
      counts[tok.kind] += 1;
    }
    return counts;
  }, [analysis.words]);

  const filteredOutCount = Math.max(0, analysis.unfilteredCount - analysis.words.length);

  const jsonOutput = useMemo(() => {
    if (!input) return "";
    return JSON.stringify(
      activeTab === "words" ? analysis.words : analysis.sentences,
      null,
      2
    );
  }, [input, activeTab, analysis.words, analysis.sentences]);

  const activeProfileMeta =
    STOPWORD_PROFILES.find((p) => p.id === profile) ?? STOPWORD_PROFILES[0];

  const handleClear = () => {
    setInput("");
    setSelectedTokenIndex(null);
  };

  const handleLoadSample = (sample: TokenizerSample) => {
    setInput(sample.text);
    setSelectedTokenIndex(null);
  };

  const kindLabel = (kind: tt.WordToken["kind"]) => {
    switch (kind) {
      case "abbreviation":
        return t.tools.tokenizer.kindAbbreviation;
      case "word":
        return t.tools.tokenizer.kindWord;
      case "number":
        return t.tools.tokenizer.kindNumber;
      case "other":
        return t.tools.tokenizer.kindOther;
    }
  };

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.tokenizer.title}
        description={t.tools.tokenizer.desc}
        actions={
          <div className="flex flex-wrap items-center gap-1.5">
            {TOKENIZER_SAMPLES.map((sample) => (
              <Button
                key={sample.id}
                variant="outline"
                size="sm"
                onClick={() => handleLoadSample(sample)}
              >
                {language === "ta" ? sample.labelTa : sample.labelEn}
              </Button>
            ))}
          </div>
        }
      />

      {/* Input Card */}
      <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] overflow-hidden">
        <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
          <span className="text-xs font-semibold text-[var(--color-mai)]">
            {t.tools.tokenizer.inputLabel}
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
          onChange={(e) => {
            setInput(e.target.value);
            setSelectedTokenIndex(null);
          }}
          placeholder={t.tools.tokenizer.inputPlaceholder}
          className="w-full min-h-[120px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
        />
      </div>

      {/* Controls: Mode Tabs & Stopword Profile */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)] self-start">
          <button
            type="button"
            onClick={() => setActiveTab("words")}
            className={`px-3.5 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "words"
                ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.tokenizer.tabWords} ({analysis.words.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("sentences")}
            className={`px-3.5 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
              activeTab === "sentences"
                ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.tokenizer.tabSentences} ({analysis.sentences.length})
          </button>
        </div>

        {activeTab === "words" && (
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs font-semibold text-[var(--color-muted)] mr-1">
                {t.tools.tokenizer.stopwordLabel}:
              </span>
              {STOPWORD_PROFILES.map((p) => {
                const active = p.id === profile;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      setProfile(p.id);
                      setSelectedTokenIndex(null);
                    }}
                    data-active={active}
                    className={`px-3 py-1 rounded-full text-xs font-medium border min-h-[32px] transition-colors cursor-pointer ${
                      active
                        ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                        : "bg-[var(--bg-surface)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
                    }`}
                  >
                    {language === "ta" ? p.labelTa : p.labelEn}
                  </button>
                );
              })}
            </div>
            <p className="text-[11px] text-[var(--color-muted)]">
              {language === "ta" ? activeProfileMeta.hintTa : activeProfileMeta.hintEn}
            </p>
          </div>
        )}
      </div>

      {analysis.error && (
        <div className="p-3 rounded-lg border border-red-300 bg-red-50/70 text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{analysis.error}</span>
        </div>
      )}

      {/* Results View */}
      {activeTab === "words" ? (
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="terracotta">
              {t.tools.tokenizer.kindWord}: {kindCounts.word}
            </Badge>
            <Badge variant="outline">
              {t.tools.tokenizer.kindAbbreviation}: {kindCounts.abbreviation}
            </Badge>
            <Badge variant="outline">
              {t.tools.tokenizer.kindNumber}: {kindCounts.number}
            </Badge>
            <Badge variant="outline">
              {t.tools.tokenizer.kindOther}: {kindCounts.other}
            </Badge>
            {filteredOutCount > 0 && (
              <Badge variant="outline">
                {t.tools.tokenizer.filteredOut}: {filteredOutCount}
              </Badge>
            )}
          </div>

          {/* Token Chips */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
                {t.tools.tokenizer.tokenSpansHeading}
              </span>
              {jsonOutput && (
                <CopyButton
                  text={jsonOutput}
                  label={t.tools.tokenizer.copyJson}
                  copiedLabel={t.actions.copied}
                  size="sm"
                  variant="outline"
                />
              )}
            </div>

            {analysis.words.length === 0 ? (
              <p className="text-sm text-[var(--color-muted)] py-4 text-center">
                {t.tools.tokenizer.emptyResult}
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {analysis.words.map((tok, idx) => {
                  const isSelected = selectedTokenIndex === idx;
                  return (
                    <button
                      key={`${tok.start_byte}-${tok.end_byte}-${idx}`}
                      type="button"
                      onClick={() => setSelectedTokenIndex(isSelected ? null : idx)}
                      className={`inline-flex items-baseline gap-1.5 px-2.5 py-1.5 rounded-lg border text-sm font-tamil transition-all cursor-pointer ${
                        KIND_STYLES[tok.kind]
                      } ${isSelected ? "ring-2 ring-[var(--color-semman)] scale-[1.02]" : ""}`}
                    >
                      <span className="font-medium">{tok.text}</span>
                      <span className="text-[10px] font-mono-tamil opacity-75">
                        {tok.start_unit}..{tok.end_unit}
                      </span>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Exact Coordinate Table */}
          {analysis.words.length > 0 && (
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-[var(--border-line)] bg-[var(--bg-raised)]/40 text-[var(--color-muted)]">
                      <th className="py-2.5 px-3 font-semibold">#</th>
                      <th className="py-2.5 px-3 font-semibold">{t.tools.tokenizer.colText}</th>
                      <th className="py-2.5 px-3 font-semibold">{t.tools.tokenizer.colKind}</th>
                      <th className="py-2.5 px-3 font-semibold">{t.tools.tokenizer.colBytes}</th>
                      <th className="py-2.5 px-3 font-semibold">{t.tools.tokenizer.colUnits}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border-line)]">
                    {analysis.words.map((tok, idx) => (
                      <tr
                        key={`${tok.start_byte}-${tok.end_byte}-${idx}`}
                        onClick={() => setSelectedTokenIndex(idx)}
                        className={`cursor-pointer transition-colors ${
                          selectedTokenIndex === idx
                            ? "bg-[var(--color-semman-light)]/50"
                            : "hover:bg-[var(--bg-raised)]/30"
                        }`}
                      >
                        <td className="py-2 px-3 font-mono-tamil text-[var(--color-muted)]">
                          {idx + 1}
                        </td>
                        <td className="py-2 px-3 font-tamil text-sm font-medium text-[var(--color-mai)]">
                          {tok.text}
                        </td>
                        <td className="py-2 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-md border text-[11px] font-medium ${KIND_STYLES[tok.kind]}`}
                          >
                            {kindLabel(tok.kind)}
                          </span>
                        </td>
                        <td className="py-2 px-3 font-mono-tamil text-[var(--color-muted)]">
                          [{tok.start_byte}, {tok.end_byte})
                        </td>
                        <td className="py-2 px-3 font-mono-tamil text-[var(--color-muted)]">
                          [{tok.start_unit}, {tok.end_unit})
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </div>
      ) : (
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider">
              {t.tools.tokenizer.sentenceSpansHeading}
            </span>
            {jsonOutput && (
              <CopyButton
                text={jsonOutput}
                label={t.tools.tokenizer.copyJson}
                copiedLabel={t.actions.copied}
                size="sm"
                variant="outline"
              />
            )}
          </div>

          {analysis.sentences.length === 0 ? (
            <p className="text-sm text-[var(--color-muted)] py-4 text-center">
              {t.tools.tokenizer.emptyResult}
            </p>
          ) : (
            <div className="space-y-2.5">
              {analysis.sentences.map((sent, idx) => (
                <div
                  key={`${sent.start_byte}-${sent.end_byte}-${idx}`}
                  className="p-3.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)]/60 space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono-tamil text-[var(--color-muted)]">
                    <span className="font-semibold text-[var(--color-semman)]">
                      #{idx + 1}
                    </span>
                    <div className="flex items-center gap-3">
                      <span>
                        {t.tools.tokenizer.colBytes}: [{sent.start_byte}, {sent.end_byte})
                      </span>
                      <span>
                        {t.tools.tokenizer.colUnits}: [{sent.start_unit}, {sent.end_unit})
                      </span>
                    </div>
                  </div>
                  <p className="font-tamil text-base leading-relaxed text-[var(--color-mai)]">
                    {sent.text}
                  </p>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      <StickyActionBar
        outputText={jsonOutput}
        onClear={handleClear}
        copyLabel={t.tools.tokenizer.copyJson}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
      />
    </div>
  );
}
