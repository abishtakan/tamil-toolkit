import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import {
  auditAndNormalizeTamil,
  normalizeNfc,
  normalizeNfd,
  repairTamilTextWithDiagnostics,
  foldForSearch,
  isEngineReady,
  tt,
} from "../../lib/engine";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import {
  AlertTriangle,
  ShieldCheck,
  Info,
  Layers,
  CheckSquare,
  Square,
  ChevronDown,
  ChevronUp,
  X,
} from "lucide-react";

const SAMPLE_VOWELS = "கொங்கு கோட்டை கௌதமன் சொற்கள்";

const PULLI = String.fromCharCode(0x0bcd);
const ZWJ = String.fromCharCode(0x200d);
const SAMPLE_CORRUPTED = "க" + PULLI + PULLI + "கு தமிழ்" + ZWJ + "நாடு உயிர்மெய்";

const SAMPLE_FOLDING = "பழைய காலத்து கோவில் சிற்பங்கள், லஷ்மி தேவி & ஸ்ரீ ராமர் ஜெயந்தி";

interface NormalizerToolProps {
  engineReady?: boolean;
}

export function NormalizerTool({ engineReady }: NormalizerToolProps) {
  const { t, language } = useLanguage();
  const ready = engineReady ?? isEngineReady();
  const [inputText, setInputText] = useState(SAMPLE_VOWELS);
  const [mode, setMode] = useState<"NFC" | "REPAIR" | "FOLD" | "NFD">("NFC");
  const [foldProfile, setFoldProfile] = useState<"comprehensive" | "mayangoli" | "grantha">("comprehensive");
  const [showCodepoints, setShowCodepoints] = useState(false);
  const [repairOpts, setRepairOpts] = useState<tt.RepairOptions>({
    collapse_duplicate_pulli: true,
    reorder_visual_kombu: true,
    strip_soft_hyphens: true,
    strip_joiners: true,
  });

  const auditResult = useMemo(() => {
    void ready;
    return auditAndNormalizeTamil(inputText);
  }, [inputText, ready]);

  const repairResult = useMemo(() => {
    void ready;
    return repairTamilTextWithDiagnostics(inputText, repairOpts);
  }, [inputText, repairOpts, ready]);

  const outputText = useMemo(() => {
    void ready;
    if (mode === "NFC") return normalizeNfc(inputText);
    if (mode === "NFD") return normalizeNfd(inputText);
    if (mode === "FOLD") return foldForSearch(inputText, foldProfile);
    return repairResult.text;
  }, [mode, inputText, foldProfile, repairResult, ready]);

  const outputCodepoints = useMemo(() => {
    return Array.from(outputText).map(
      (c) => "U+" + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0")
    );
  }, [outputText]);

  const clearText = () => {
    setInputText("");
  };

  const toggleRepairOpt = (key: keyof tt.RepairOptions) => {
    setRepairOpts((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const codepointsVisible = mode === "NFD" || showCodepoints;

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.normalizer.title}
        description={t.tools.normalizer.desc}
        actions={
          <>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setInputText(SAMPLE_VOWELS);
                setMode("NFC");
              }}
            >
              {t.tools.normalizer.sampleVowelsButton}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setInputText(SAMPLE_CORRUPTED);
                setMode("REPAIR");
              }}
            >
              {t.tools.normalizer.sampleDefectiveButton}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setInputText(SAMPLE_FOLDING);
                setMode("FOLD");
              }}
            >
              {language === "ta" ? "தேடல் மாதிரி" : "Search sample"}
            </Button>
          </>
        }
      />

      {/* Mode Segmented Control & Cleanliness Pill */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
          {(
            [
              { id: "NFC", label: t.tools.normalizer.nfcLabel },
              { id: "REPAIR", label: t.tools.normalizer.repairedLabel },
              { id: "FOLD", label: t.tools.normalizer.foldLabel },
              { id: "NFD", label: t.tools.normalizer.nfdLabel },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setMode(item.id)}
              className={`px-3 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                mode === item.id
                  ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                  : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {mode === "NFD" && auditResult.decomposedVowelsCount > 0 && (
            <Badge variant="sandhanam">
              {auditResult.decomposedVowelsCount} {t.tools.normalizer.decomposedCountLabel}
            </Badge>
          )}

          {mode === "REPAIR" && repairResult.diagnostics.total_repairs > 0 && (
            <Badge variant="terracotta">
              {repairResult.diagnostics.total_repairs} {t.tools.normalizer.diagTotalRepairs}
            </Badge>
          )}

          {auditResult.isClean ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{t.tools.normalizer.statusClean}</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>
                {auditResult.anomalyCount} {t.tools.normalizer.statusAnomalies}
              </span>
            </span>
          )}
        </div>
      </div>

      {/* Mode Sub-Options */}
      {mode === "FOLD" && (
        <Card className="p-3.5 flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs font-semibold text-[var(--color-mai)]">
            {language === "ta" ? "மடிப்பு முறை:" : "Folding Profile:"}
          </span>
          <div className="flex flex-wrap items-center gap-1.5">
            {[
              { id: "comprehensive" as const, label: t.tools.normalizer.profileComprehensive },
              { id: "mayangoli" as const, label: t.tools.normalizer.profileMayangoli },
              { id: "grantha" as const, label: t.tools.normalizer.profileGrantha },
            ].map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => setFoldProfile(p.id)}
                className={`px-3 py-1 rounded-lg text-xs transition-colors border cursor-pointer ${
                  foldProfile === p.id
                    ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                    : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </Card>
      )}

      {mode === "REPAIR" && (
        <Card className="p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {t.tools.normalizer.repairOptionsHeading}
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              <Badge variant="outline">
                {t.tools.normalizer.diagDuplicatePulli}: {repairResult.diagnostics.duplicate_pulli_count}
              </Badge>
              <Badge variant="outline">
                {t.tools.normalizer.diagVisualKombu}: {repairResult.diagnostics.visual_kombu_count}
              </Badge>
              <Badge variant="outline">
                {t.tools.normalizer.diagStrippedControls}: {repairResult.diagnostics.stripped_control_count}
              </Badge>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5">
            {[
              { key: "collapse_duplicate_pulli" as const, label: t.tools.normalizer.optCollapsePulli },
              { key: "reorder_visual_kombu" as const, label: t.tools.normalizer.optReorderKombu },
              { key: "strip_soft_hyphens" as const, label: t.tools.normalizer.optStripShy },
              { key: "strip_joiners" as const, label: t.tools.normalizer.optStripJoiners },
            ].map((opt) => {
              const active = repairOpts[opt.key];
              return (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => toggleRepairOpt(opt.key)}
                  className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs transition-colors cursor-pointer text-left ${
                    active
                      ? "bg-[var(--bg-canvas)] border-[var(--color-semman)] text-[var(--color-mai)] font-semibold"
                      : "bg-[var(--bg-canvas)]/50 border-[var(--border-line)] text-[var(--color-muted)] opacity-75"
                  }`}
                >
                  {active ? (
                    <CheckSquare className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
                  ) : (
                    <Square className="w-4 h-4 text-[var(--color-muted)] shrink-0" />
                  )}
                  <span>{opt.label}</span>
                </button>
              );
            })}
          </div>
        </Card>
      )}

      {/* Dual Pane Editor */}
      <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[var(--border-line)]">
        <div className="flex flex-col">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {t.tools.normalizer.inputLabel}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                {auditResult.originalCodepoints.length} cp
              </span>
              {inputText && (
                <button
                  type="button"
                  onClick={clearText}
                  aria-label={t.actions.clear}
                  className="inline-flex items-center gap-1 text-xs text-[var(--color-muted)] hover:text-[var(--color-semman)] cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={t.tools.normalizer.inputPlaceholder}
            rows={6}
            className="w-full flex-1 min-h-[180px] p-4 bg-transparent text-base font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>

        <div className="flex flex-col bg-[var(--bg-canvas)]/40">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {t.tools.normalizer.outputLabel}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                {outputCodepoints.length} cp
              </span>
              <CopyButton text={outputText} label={t.actions.copy} size="sm" variant="outline" />
            </div>
          </div>
          <textarea
            value={outputText}
            readOnly
            rows={6}
            className="w-full flex-1 min-h-[180px] p-4 bg-transparent text-base font-tamil leading-[1.7] text-[var(--color-mai)] focus:outline-none resize-y"
          />
        </div>
      </div>

      {/* Explanatory Note */}
      <div className="p-3.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] flex items-start gap-2.5">
        <Info className="w-4 h-4 text-[var(--color-sandhanam)] shrink-0 mt-0.5" />
        <p className="text-xs text-[var(--color-muted)] leading-relaxed">
          {mode === "NFC" && t.tools.normalizer.nfcBanner}
          {mode === "NFD" && t.tools.normalizer.nfdBanner}
          {mode === "REPAIR" && t.tools.normalizer.repairedBanner}
          {mode === "FOLD" && t.tools.normalizer.foldBanner}
        </p>
      </div>

      {/* Collapsible Unicode Codepoint Inspector */}
      <Card className="p-4 sm:p-5 space-y-3">
        <button
          type="button"
          onClick={() => setShowCodepoints((prev) => !prev)}
          aria-expanded={codepointsVisible}
          className="w-full flex items-center justify-between gap-2 text-left cursor-pointer"
        >
          <span className="text-xs sm:text-sm font-bold text-[var(--color-mai)] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[var(--color-sandhanam)]" />
            <span>{t.tools.normalizer.codepointInspectorHeading}</span>
          </span>
          <div className="flex items-center gap-2 text-[11px] font-mono-tamil text-[var(--color-muted)]">
            <span>
              {auditResult.originalCodepoints.length} → {outputCodepoints.length} cp
            </span>
            {codepointsVisible ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {codepointsVisible && (
          <div className="pt-3 border-t border-[var(--border-line)] grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] space-y-1.5">
              <span className="text-[11px] font-semibold text-[var(--color-muted)] block">
                {t.tools.normalizer.inputLabel}
              </span>
              <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
                {auditResult.originalCodepoints.map((cp, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-line)] font-mono-tamil text-[10px] text-[var(--color-mai)]"
                  >
                    {cp}
                  </span>
                ))}
                {auditResult.originalCodepoints.length === 0 && (
                  <span className="text-xs text-[var(--color-muted)]">
                    {t.tools.normalizer.inputPlaceholder}
                  </span>
                )}
              </div>
            </div>

            <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] space-y-1.5">
              <span className="text-[11px] font-semibold text-[var(--color-muted)] block">
                {t.tools.normalizer.outputLabel} ({mode})
              </span>
              <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
                {outputCodepoints.map((cp, idx) => {
                  const isDecomposedSign =
                    mode === "NFD" && (cp === "U+0BC6" || cp === "U+0BC7" || cp === "U+0BBE" || cp === "U+0BD7");
                  return (
                    <span
                      key={idx}
                      className={`px-2 py-0.5 rounded-lg border font-mono-tamil text-[10px] ${
                        isDecomposedSign
                          ? "bg-[var(--color-sandhanam-light)] border-[var(--color-sandhanam)] text-[var(--color-sandhanam)] font-bold"
                          : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-mai)]"
                      }`}
                    >
                      {cp}
                    </span>
                  );
                })}
                {outputCodepoints.length === 0 && (
                  <span className="text-xs text-[var(--color-muted)]">
                    {t.tools.normalizer.inputPlaceholder}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Anomaly Diagnosis Cards */}
      {auditResult.anomalies.length > 0 && (
        <Card className="p-5 border-amber-200 dark:border-amber-900/50 bg-amber-50/40 dark:bg-amber-950/20 space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <h2 className="text-xs sm:text-sm font-bold text-amber-900 dark:text-amber-200">
              {t.tools.normalizer.anomaliesFixedLabel} ({auditResult.anomalyCount})
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {auditResult.anomalies.map((anom, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <Badge variant="terracotta">{anom.type}</Badge>
                  <span className="font-mono-tamil text-[10px] text-[var(--color-muted)]">
                    pos: {anom.position}
                  </span>
                </div>
                <p className="text-xs text-[var(--color-mai)] font-medium">
                  {language === "ta" ? anom.description_ta : anom.description_en}
                </p>
                <div className="p-1.5 rounded-lg bg-[var(--bg-canvas)] font-mono-tamil text-[11px] text-[var(--color-semman)] font-bold">
                  {anom.snippet}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <StickyActionBar
        outputText={outputText}
        onClear={clearText}
        copyLabel={t.tools.normalizer.copyNormalizedButton}
      />
    </div>
  );
}
