import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import {
  auditAndNormalizeTamil,
  normalizeNfc,
  normalizeNfd,
  repairTamilTextWithDiagnostics,
  foldForSearch,
  tt
} from "../../lib/engine";
import { Textarea } from "../ui/textarea";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Sparkles, AlertTriangle, ShieldCheck, Info, Layers, RefreshCw, Search, CheckSquare, Square } from "lucide-react";

// Canonical two-part vowels sample: கொ, கோ, கௌ
const SAMPLE_VOWELS = "கொங்கு கோட்டை கௌதமன் சொற்கள்";

// Corrupted text sample with duplicate virama and stray joiner constructed dynamically
const PULLI = String.fromCharCode(0x0bcd);
const ZWJ = String.fromCharCode(0x200d);
const SAMPLE_CORRUPTED = "க" + PULLI + PULLI + "கு தமிழ்" + ZWJ + "நாடு உயிர்மெய்";

// Sample with Mayangoli confusion and Grantha consonants for Search Folding
const SAMPLE_FOLDING = "பழைய காலத்து கோவில் சிற்பங்கள், லஷ்மி தேவி & ஸ்ரீ ராமர் ஜெயந்தி";

export function NormalizerTool() {
  const { t, language } = useLanguage();
  const [inputText, setInputText] = useState(SAMPLE_VOWELS);
  const [mode, setMode] = useState<"NFC" | "NFD" | "REPAIR" | "FOLD">("NFC");
  const [foldProfile, setFoldProfile] = useState<"comprehensive" | "mayangoli" | "grantha">("comprehensive");
  const [repairOpts, setRepairOpts] = useState<tt.RepairOptions>({
    collapse_duplicate_pulli: true,
    reorder_visual_kombu: true,
    strip_soft_hyphens: true,
    strip_joiners: true,
  });

  const auditResult = useMemo(() => {
    return auditAndNormalizeTamil(inputText);
  }, [inputText]);

  const repairResult = useMemo(() => {
    return repairTamilTextWithDiagnostics(inputText, repairOpts);
  }, [inputText, repairOpts]);

  const outputText = useMemo(() => {
    if (mode === "NFC") return normalizeNfc(inputText);
    if (mode === "NFD") return normalizeNfd(inputText);
    if (mode === "FOLD") return foldForSearch(inputText, foldProfile);
    return repairResult.text;
  }, [mode, inputText, foldProfile, repairResult]);

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

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-150">
      {/* Title & Description Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
              {t.tools.normalizer.title}
            </h2>
            <Badge variant="terracotta">Unicode UAX #15 & Contracts</Badge>
          </div>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans max-w-2xl leading-relaxed">
            {t.tools.normalizer.desc}
          </p>
        </div>

        {/* Sample Actions */}
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInputText(SAMPLE_VOWELS);
              setMode("NFC");
            }}
            className="text-xs"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            {t.tools.normalizer.sampleVowelsButton}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInputText(SAMPLE_CORRUPTED);
              setMode("REPAIR");
            }}
            className="text-xs text-[var(--color-semman)] hover:text-[var(--color-semman)]"
          >
            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
            {t.tools.normalizer.sampleDefectiveButton}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInputText(SAMPLE_FOLDING);
              setMode("FOLD");
            }}
            className="text-xs"
          >
            <Search className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            {language === "ta" ? "தேடல் மாதிரி" : "Search Sample"}
          </Button>
          <Button variant="ghost" size="sm" onClick={clearText} disabled={!inputText}>
            {t.actions.clear}
          </Button>
        </div>
      </div>

      {/* Mode Selector & Status Ribbon */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setMode("NFC")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-tamil font-medium transition-colors border ${
              mode === "NFC"
                ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
                : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.normalizer.nfcLabel}
          </button>
          <button
            onClick={() => setMode("NFD")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-tamil font-medium transition-colors border ${
              mode === "NFD"
                ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
                : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.normalizer.nfdLabel}
          </button>
          <button
            onClick={() => setMode("REPAIR")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-tamil font-medium transition-colors border ${
              mode === "REPAIR"
                ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
                : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
            }`}
          >
            <RefreshCw className="w-3 h-3 inline mr-1" />
            {t.tools.normalizer.repairedLabel}
          </button>
          <button
            onClick={() => setMode("FOLD")}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-tamil font-medium transition-colors border ${
              mode === "FOLD"
                ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
                : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
            }`}
          >
            <Search className="w-3 h-3 inline mr-1" />
            {t.tools.normalizer.foldLabel}
          </button>
        </div>

        {/* Diagnosis Status Badge */}
        <div className="flex flex-wrap items-center gap-2">
          {mode === "NFD" && auditResult.decomposedVowelsCount > 0 && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-tamil font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800">
              <Layers className="w-3.5 h-3.5" />
              <span>
                {auditResult.decomposedVowelsCount} {t.tools.normalizer.decomposedCountLabel}
              </span>
            </div>
          )}

          {mode === "REPAIR" && repairResult.diagnostics.total_repairs > 0 && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-tamil font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>
                {repairResult.diagnostics.total_repairs} {t.tools.normalizer.diagTotalRepairs}
              </span>
            </div>
          )}

          {auditResult.isClean ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-tamil font-medium bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{t.tools.normalizer.statusClean}</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-tamil font-medium bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>
                {auditResult.anomalyCount} {t.tools.normalizer.statusAnomalies}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Sub-controls: Search Profile Selector OR Repair Options */}
      {mode === "FOLD" && (
        <Card className="p-3.5 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-[var(--color-sandhanam)]" />
            <span className="text-xs font-tamil font-bold text-[var(--color-mai)]">
              {language === "ta" ? "மடிப்பு விவரம் (Profile):" : "Folding Profile:"}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: "comprehensive" as const, label: t.tools.normalizer.profileComprehensive },
              { id: "mayangoli" as const, label: t.tools.normalizer.profileMayangoli },
              { id: "grantha" as const, label: t.tools.normalizer.profileGrantha }
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setFoldProfile(p.id)}
                className={`px-3 py-1 rounded-xl text-xs font-tamil transition-colors border ${
                  foldProfile === p.id
                    ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
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
        <Card className="p-4 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-tamil font-bold text-[var(--color-mai)] flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5 text-[var(--color-semman)]" />
              {t.tools.normalizer.repairOptionsHeading}
            </span>
            <div className="flex flex-wrap items-center gap-2">
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

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 pt-1">
            {[
              { key: "collapse_duplicate_pulli" as const, label: t.tools.normalizer.optCollapsePulli },
              { key: "reorder_visual_kombu" as const, label: t.tools.normalizer.optReorderKombu },
              { key: "strip_soft_hyphens" as const, label: t.tools.normalizer.optStripShy },
              { key: "strip_joiners" as const, label: t.tools.normalizer.optStripJoiners }
            ].map((opt) => {
              const active = repairOpts[opt.key];
              return (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => toggleRepairOpt(opt.key)}
                  className={`flex items-center gap-2 p-2.5 rounded-xl border text-xs font-tamil transition-colors cursor-pointer text-left ${
                    active
                      ? "bg-[var(--bg-canvas)] border-[var(--color-semman)] text-[var(--color-mai)] font-semibold"
                      : "bg-[var(--bg-canvas)]/50 border-[var(--border-line)] text-[var(--color-muted)] opacity-70"
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

      {/* Explanatory Mode Banner */}
      <div className="p-3.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] flex items-start gap-3">
        <Info className="w-4 h-4 text-[var(--color-sandhanam)] shrink-0 mt-0.5" />
        <p className="text-xs text-[var(--color-mai)] leading-relaxed font-tamil">
          {mode === "NFC" && t.tools.normalizer.nfcBanner}
          {mode === "NFD" && t.tools.normalizer.nfdBanner}
          {mode === "REPAIR" && t.tools.normalizer.repairedBanner}
          {mode === "FOLD" && t.tools.normalizer.foldBanner}
        </p>
      </div>

      {/* Dual Pane Editor: Raw Input vs Normalized Output */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Pane: Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-tamil font-semibold text-[var(--color-mai)]">
              {t.tools.normalizer.inputLabel}
            </label>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                {inputText.length} chars ({auditResult.originalCodepoints.length} codepoints)
              </span>
            </div>
          </div>
          <Textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={t.tools.normalizer.inputPlaceholder}
            rows={7}
            className="font-tamil text-base leading-relaxed resize-y"
          />
        </div>

        {/* Right Pane: Output */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-tamil font-semibold text-[var(--color-mai)]">
              {t.tools.normalizer.outputLabel}
            </label>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                {outputText.length} chars ({outputCodepoints.length} codepoints)
              </span>
              <CopyButton text={outputText} label={t.actions.copy} />
            </div>
          </div>
          <Textarea
            value={outputText}
            readOnly
            rows={7}
            className="font-tamil text-base leading-relaxed resize-y bg-[var(--bg-canvas)]"
          />
        </div>
      </div>

      {/* Unicode Codepoints Inspector */}
      <Card className="p-4 sm:p-5 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[var(--color-sandhanam)]" />
            {t.tools.normalizer.codepointInspectorHeading}
          </h4>
          <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
            Input: {auditResult.originalCodepoints.length} cp | Output: {outputCodepoints.length} cp
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Input Codepoints */}
          <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] space-y-1.5">
            <span className="text-[11px] font-tamil font-semibold text-[var(--color-muted)] block">
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
                <span className="text-xs text-[var(--color-muted)] font-tamil">
                  {t.tools.normalizer.inputPlaceholder}
                </span>
              )}
            </div>
          </div>

          {/* Output Codepoints */}
          <div className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] space-y-1.5">
            <span className="text-[11px] font-tamil font-semibold text-[var(--color-muted)] block">
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
                        ? "bg-[var(--color-sandhanam-light)] border-[var(--color-sandhanam)] text-[var(--color-sandhanam)] font-bold shadow-xs"
                        : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-mai)]"
                    }`}
                  >
                    {cp}
                  </span>
                );
              })}
              {outputCodepoints.length === 0 && (
                <span className="text-xs text-[var(--color-muted)] font-tamil">
                  {t.tools.normalizer.inputPlaceholder}
                </span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Anomaly Diagnosis Cards */}
      {auditResult.anomalies.length > 0 && (
        <Card className="p-5 border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20 rounded-2xl space-y-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <h4 className="text-xs sm:text-sm font-tamil font-bold text-amber-900 dark:text-amber-200">
              {t.tools.normalizer.anomaliesFixedLabel} ({auditResult.anomalyCount})
            </h4>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {auditResult.anomalies.map((anom, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-xs font-tamil space-y-1"
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
                  Snippet: {anom.snippet}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Sticky Mobile Bar */}
      <StickyActionBar
        outputText={outputText}
        onClear={clearText}
        copyLabel={t.tools.normalizer.copyNormalizedButton}
      />
    </div>
  );
}
