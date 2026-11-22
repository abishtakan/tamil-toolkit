import { useState, useMemo, useRef, type ChangeEvent } from "react";
import {
  bytesToHex,
  hexToBytes,
  isEngineReady,
  latin1BytesToString,
  stringToLatin1Bytes,
  tt,
} from "../../lib/engine";
import { extractPdfTextLayer, type PdfExtractionResult } from "../../lib/pdf-extract";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { AlertCircle, ArrowLeftRight, FileText, X } from "lucide-react";

export type CodecProfile =
  | "auto"
  | "bamini-v1"
  | "tscii-1.7-v1"
  | "tab-v1"
  | "tam-v1"
  | "anjal-v1"
  | "vanavil-avvaiyar-cid-v1"
  | "lt-tm-cid-v1"
  | "senthamil-cid-v1"
  | "shree-tam-cid-v1"
  | "softview-amudham-cid-v1"
  | "tbo-tboomi-cid-v1"
  | "bharathi-tamil-g1-v1";

const PROFILES: { id: CodecProfile; labelEn: string; labelTa: string }[] = [
  { id: "auto", labelEn: "Auto-Detect", labelTa: "தானியங்கி" },
  { id: "bamini-v1", labelEn: "Bamini", labelTa: "பாமினி" },
  { id: "tscii-1.7-v1", labelEn: "TSCII", labelTa: "TSCII" },
  { id: "tab-v1", labelEn: "TAB", labelTa: "TAB" },
  { id: "tam-v1", labelEn: "TAM", labelTa: "TAM" },
  { id: "anjal-v1", labelEn: "Anjal", labelTa: "அஞ்சல்" },
  { id: "vanavil-avvaiyar-cid-v1", labelEn: "Vanavil", labelTa: "வானவில்" },
  { id: "lt-tm-cid-v1", labelEn: "LT-TM", labelTa: "LT-TM" },
  { id: "senthamil-cid-v1", labelEn: "Senthamil", labelTa: "செந்தமிழ்" },
  { id: "shree-tam-cid-v1", labelEn: "Shree-Tam", labelTa: "ஸ்ரீ-தமிழ்" },
  { id: "softview-amudham-cid-v1", labelEn: "Softview", labelTa: "அமுதம்" },
  { id: "tbo-tboomi-cid-v1", labelEn: "TBO", labelTa: "தினபூமி" },
  { id: "bharathi-tamil-g1-v1", labelEn: "Braille", labelTa: "பிரெய்லி" },
];

const BYTE_CODECS = new Set<CodecProfile>([
  "tscii-1.7-v1",
  "tab-v1",
  "tam-v1",
  "anjal-v1",
]);

const TEXT_POLICY_CODECS = new Set<CodecProfile>([
  "bamini-v1",
  "vanavil-avvaiyar-cid-v1",
  "lt-tm-cid-v1",
  "senthamil-cid-v1",
  "shree-tam-cid-v1",
  "softview-amudham-cid-v1",
  "tbo-tboomi-cid-v1",
  "bharathi-tamil-g1-v1",
]);

const BAMINI_SAMPLE = "jkpo; nkhop cyfpd; njhd;ikahd nkhopfspy; xd;whFk;.";
const TSCII_HEX_SAMPLE = "be c1 a2 fa";
const UNICODE_SAMPLE = "தமிழ் மொழி உலகின் தொன்மையான மொழிகளில் ஒன்றாகும்.";

function encodeInputBytes(text: string, hexMode: boolean): Uint8Array | null {
  if (hexMode) {
    return hexToBytes(text);
  }
  if (/[^\x00-\xff]/.test(text)) {
    return new TextEncoder().encode(text);
  }
  return stringToLatin1Bytes(text);
}

interface CodecConverterProps {
  engineReady?: boolean;
}

export function CodecConverter({ engineReady }: CodecConverterProps) {
  const { language, t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [input, setInput] = useState("");
  const [selectedProfile, setSelectedProfile] = useState<CodecProfile>("auto");
  const [direction, setDirection] = useState<"to_unicode" | "from_unicode">("to_unicode");
  const [errorPolicy, setErrorPolicy] = useState<"preserve" | "strict">("preserve");
  const [hexMode, setHexMode] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfInfo, setPdfInfo] = useState<PdfExtractionResult | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const pdfInputRef = useRef<HTMLInputElement | null>(null);

  const conversion = useMemo(() => {
    if (!ready || !input.trim()) {
      return {
        output: "",
        detectedProfile: null as string | null,
        confidence: null as number | null,
        candidates: [] as { encoding: string; confidence: number }[],
        error: null as string | null,
      };
    }

    try {
      if (direction === "to_unicode") {
        let activeProfile = selectedProfile;
        let detectedProfile: string | null = selectedProfile;
        let confidence: number | null = 1.0;
        let candidates: { encoding: string; confidence: number }[] = [];

        const inputBytes = encodeInputBytes(input, hexMode);
        if (hexMode && !inputBytes) {
          return {
            output: "",
            detectedProfile: null,
            confidence: null,
            candidates: [],
            error: "Invalid hex byte sequence (expected even count of 0-9 / a-f nibbles).",
          };
        }

        if (selectedProfile === "auto") {
          const detection = tt.detect_encoding(inputBytes!);
          if (detection && detection.encoding) {
            activeProfile = detection.encoding as CodecProfile;
            detectedProfile = detection.encoding;
            confidence = detection.confidence;
          } else {
            activeProfile = "bamini-v1";
            detectedProfile = "bamini-v1";
            confidence = 0.5;
          }
          if (Array.isArray(detection?.candidates)) {
            candidates = detection.candidates.slice(0, 4);
          }
        }

        let res = "";
        switch (activeProfile) {
          case "bamini-v1":
            res = tt.bamini_to_unicode(input, errorPolicy);
            break;
          case "tscii-1.7-v1":
            res = tt.tscii_bytes_to_unicode(inputBytes!);
            break;
          case "tab-v1":
            res = tt.tab_bytes_to_unicode(inputBytes!);
            break;
          case "tam-v1":
            res = tt.tam_bytes_to_unicode(inputBytes!);
            break;
          case "anjal-v1":
            res = tt.anjal_bytes_to_unicode(inputBytes!);
            break;
          case "vanavil-avvaiyar-cid-v1":
            res = tt.vanavil_text_to_unicode(input, errorPolicy);
            break;
          case "lt-tm-cid-v1":
            res = tt.lt_tm_text_to_unicode(input, errorPolicy);
            break;
          case "senthamil-cid-v1":
            res = tt.senthamil_text_to_unicode(input, errorPolicy);
            break;
          case "shree-tam-cid-v1":
            res = tt.shree_tam_text_to_unicode(input, errorPolicy);
            break;
          case "softview-amudham-cid-v1":
            res = tt.softview_text_to_unicode(input, errorPolicy);
            break;
          case "tbo-tboomi-cid-v1":
            res = tt.tbo_text_to_unicode(input, errorPolicy);
            break;
          case "bharathi-tamil-g1-v1":
            res = tt.braille_to_unicode(input, errorPolicy);
            break;
          default:
            res = tt.bamini_to_unicode(input, errorPolicy);
        }
        return { output: res, detectedProfile, confidence, candidates, error: null };
      } else {
        const activeProfile = selectedProfile === "auto" ? "bamini-v1" : selectedProfile;
        let res = "";
        switch (activeProfile) {
          case "bamini-v1":
            res = tt.unicode_to_bamini(input);
            break;
          case "tscii-1.7-v1": {
            const bytes = tt.unicode_to_tscii_bytes(input);
            res = hexMode ? bytesToHex(bytes) : latin1BytesToString(bytes);
            break;
          }
          case "tab-v1": {
            const bytes = tt.unicode_to_tab_bytes(input);
            res = hexMode ? bytesToHex(bytes) : latin1BytesToString(bytes);
            break;
          }
          case "tam-v1": {
            const bytes = tt.unicode_to_tam_bytes(input);
            res = hexMode ? bytesToHex(bytes) : latin1BytesToString(bytes);
            break;
          }
          case "anjal-v1": {
            const bytes = tt.unicode_to_anjal_bytes(input);
            res = hexMode ? bytesToHex(bytes) : latin1BytesToString(bytes);
            break;
          }
          case "vanavil-avvaiyar-cid-v1":
            res = tt.unicode_to_vanavil_text(input);
            break;
          case "lt-tm-cid-v1":
            res = tt.unicode_to_lt_tm_text(input);
            break;
          case "senthamil-cid-v1":
            res = tt.unicode_to_senthamil_text(input);
            break;
          case "shree-tam-cid-v1":
            res = tt.unicode_to_shree_tam_text(input);
            break;
          case "softview-amudham-cid-v1":
            res = tt.unicode_to_softview_text(input);
            break;
          case "tbo-tboomi-cid-v1":
            res = tt.unicode_to_tbo_text(input);
            break;
          case "bharathi-tamil-g1-v1":
            res = tt.unicode_to_braille(input, errorPolicy);
            break;
          default:
            res = tt.unicode_to_bamini(input);
        }
        return { output: res, detectedProfile: activeProfile, confidence: null, candidates: [], error: null };
      }
    } catch (err) {
      return {
        output: "",
        detectedProfile: null,
        confidence: null,
        candidates: [],
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }, [input, selectedProfile, direction, errorPolicy, hexMode, ready]);

  const effectiveProfile =
    selectedProfile === "auto"
      ? (conversion.detectedProfile as CodecProfile | null) ?? "bamini-v1"
      : selectedProfile;
  const showByteToggle = selectedProfile === "auto" || BYTE_CODECS.has(effectiveProfile);
  const showPolicyToggle = direction === "to_unicode" && TEXT_POLICY_CODECS.has(effectiveProfile);

  const handleSwap = () => {
    const nextDir = direction === "to_unicode" ? "from_unicode" : "to_unicode";
    if (nextDir === "from_unicode" && selectedProfile === "auto") {
      const candidate = conversion.detectedProfile as CodecProfile | null;
      const isSpecific = candidate && candidate !== "auto" && PROFILES.some((p) => p.id === candidate);
      setSelectedProfile(isSpecific ? candidate : "bamini-v1");
    }
    setDirection(nextDir);
    if (conversion.output) {
      setInput(conversion.output);
    }
  };

  const handleClear = () => {
    setInput("");
    setPdfInfo(null);
    setPdfError(null);
  };

  const handlePdfChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setPdfLoading(true);
    setPdfError(null);
    setPdfInfo(null);
    try {
      const buffer = await file.arrayBuffer();
      const result = await extractPdfTextLayer(buffer, file.name);
      setPdfInfo(result);
      if (!result.hasTextLayer) {
        setPdfError(t.tools.codec.pdfNoTextLayer);
        return;
      }
      setDirection("to_unicode");
      setHexMode(false);
      if (result.suggestedProfile) {
        setSelectedProfile(result.suggestedProfile);
      } else {
        setSelectedProfile("auto");
      }
      setInput(result.text);
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : String(err));
    } finally {
      setPdfLoading(false);
    }
  };

  const handleLoadSample = () => {
    if (direction === "to_unicode" && BYTE_CODECS.has(selectedProfile) && hexMode) {
      setInput(TSCII_HEX_SAMPLE);
      return;
    }
    setInput(direction === "to_unicode" ? BAMINI_SAMPLE : UNICODE_SAMPLE);
  };

  const handleLoadTsciiHexSample = () => {
    setDirection("to_unicode");
    setSelectedProfile("tscii-1.7-v1");
    setHexMode(true);
    setInput(TSCII_HEX_SAMPLE);
  };

  const visibleProfiles = direction === "to_unicode"
    ? PROFILES
    : PROFILES.filter((p) => p.id !== "auto");

  const getProfileLabel = (profileId: string) =>
    PROFILES.find((p) => p.id === profileId)?.[language === "ta" ? "labelTa" : "labelEn"] ??
    profileId;

  const detectedLabel = conversion.detectedProfile
    ? getProfileLabel(conversion.detectedProfile)
    : null;

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.codec.title}
        description={t.tools.codec.desc}
        actions={
          <>
            <input
              ref={pdfInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handlePdfChange}
              className="hidden"
              aria-label={t.tools.codec.importPdf}
            />
            <Button
              variant="outline"
              size="sm"
              disabled={pdfLoading}
              onClick={() => pdfInputRef.current?.click()}
            >
              <FileText className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
              <span>{pdfLoading ? t.tools.codec.importingPdf : t.tools.codec.importPdf}</span>
            </Button>
            <Button variant="outline" size="sm" onClick={handleLoadSample}>
              {t.actions.loadSample}
            </Button>
            <Button variant="outline" size="sm" onClick={handleLoadTsciiHexSample}>
              {t.tools.codec.sampleTsciiHex}
            </Button>
            <Button variant="outline" size="sm" onClick={handleSwap}>
              <ArrowLeftRight className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
              <span>
                {direction === "to_unicode"
                  ? t.tools.codec.directionLegacyToUnicode
                  : t.tools.codec.directionUnicodeToLegacy}
              </span>
            </Button>
          </>
        }
      />

      {/* Font Profile Selector + Codec Options */}
      <div className="space-y-3">
        <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wider block">
          {direction === "to_unicode" ? t.tools.codec.allProfiles : t.tools.codec.targetFontLabel}
        </span>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
            {visibleProfiles.map((p) => {
              const isActive =
                direction === "from_unicode" && selectedProfile === "auto"
                  ? p.id === "bamini-v1"
                  : selectedProfile === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setSelectedProfile(p.id)}
                  data-active={isActive}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors select-none border min-h-[36px] cursor-pointer ${
                    isActive
                      ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                      : "bg-[var(--bg-surface)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
                  }`}
                >
                  {language === "ta" ? p.labelTa : p.labelEn}
                </button>
              );
            })}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {showPolicyToggle && (
              <div className="flex items-center gap-1.5 bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-lg px-2 py-1">
                <span className="text-[11px] font-medium text-[var(--color-muted)]">
                  {t.tools.codec.errorPolicyLabel}:
                </span>
                <button
                  type="button"
                  onClick={() => setErrorPolicy("preserve")}
                  className={`px-2 py-0.5 rounded text-xs cursor-pointer ${
                    errorPolicy === "preserve"
                      ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold"
                      : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                  }`}
                >
                  {t.tools.codec.policyPreserve}
                </button>
                <button
                  type="button"
                  onClick={() => setErrorPolicy("strict")}
                  className={`px-2 py-0.5 rounded text-xs cursor-pointer ${
                    errorPolicy === "strict"
                      ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold"
                      : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                  }`}
                >
                  {t.tools.codec.policyStrict}
                </button>
              </div>
            )}

            {showByteToggle && (
              <button
                type="button"
                onClick={() => setHexMode((prev) => !prev)}
                aria-pressed={hexMode}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                  hexMode
                    ? "bg-[var(--color-semman-soft)] border-[var(--color-semman)] text-[var(--color-semman)] font-semibold"
                    : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                }`}
              >
                {t.tools.codec.hexModeToggle}
              </button>
            )}
          </div>
        </div>

        {direction === "to_unicode" && selectedProfile === "auto" && conversion.candidates.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-[var(--color-muted)] font-medium">
              {t.tools.codec.detectedCandidatesLabel}:
            </span>
            {conversion.candidates.map((cand) => (
              <button
                key={cand.encoding}
                type="button"
                onClick={() => setSelectedProfile(cand.encoding as CodecProfile)}
                className="px-2.5 py-0.5 rounded-full border border-[var(--border-line)] bg-[var(--bg-surface)] hover:border-[var(--color-semman)] text-[var(--color-mai)] transition-colors cursor-pointer"
              >
                {getProfileLabel(cand.encoding)} ({(cand.confidence * 100).toFixed(0)}%)
              </button>
            ))}
          </div>
        )}
      </div>

      {pdfInfo && pdfInfo.hasTextLayer && (
        <div className="p-3 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] text-xs text-[var(--color-mai)] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 shrink-0 text-[var(--color-semman)]" />
            <span>
              <strong>{pdfInfo.fileName}</strong> · {pdfInfo.extractedPages}/{pdfInfo.pageCount}{" "}
              {pdfInfo.pageCount === 1 ? "page" : "pages"} · {t.tools.codec.pdfExtractedSummary}
            </span>
          </div>
          {pdfInfo.suggestedProfile && (
            <Badge variant="terracotta" className="text-[11px]">
              {getProfileLabel(pdfInfo.suggestedProfile)}
            </Badge>
          )}
        </div>
      )}

      {(pdfError || conversion.error) && (
        <div className="p-3 rounded-lg border border-red-300 bg-red-50/70 text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{pdfError ?? conversion.error}</span>
        </div>
      )}

      {/* Unified Split Conversion Workspace */}
      <div className="rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] overflow-hidden grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[var(--border-line)]">
        {/* Source Pane */}
        <div className="flex flex-col">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)]">
                {direction === "to_unicode"
                  ? t.tools.codec.inputLegacyLabel
                  : t.tools.codec.inputUnicodeLabel}
              </span>
              {direction === "to_unicode" && selectedProfile === "auto" && detectedLabel && (
                <Badge variant="terracotta" className="text-[11px]">
                  {detectedLabel}
                  {conversion.confidence ? ` · ${(conversion.confidence * 100).toFixed(0)}%` : ""}
                </Badge>
              )}
            </div>
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
            placeholder={t.tools.codec.inputPlaceholder}
            className="w-full flex-1 min-h-[220px] sm:min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>

        {/* Output Pane */}
        <div className="flex flex-col bg-[var(--bg-canvas)]/40">
          <div className="px-4 py-2.5 border-b border-[var(--border-line)] bg-[var(--bg-raised)]/30 flex items-center justify-between gap-2 min-h-[44px]">
            <span className="text-xs font-semibold text-[var(--color-mai)]">
              {direction === "to_unicode"
                ? t.tools.codec.outputUnicodeLabel
                : t.tools.codec.outputLegacyLabel}
            </span>
            {conversion.output && (
              <CopyButton
                text={conversion.output}
                label={t.actions.copy}
                copiedLabel={t.actions.copied}
                size="sm"
                variant="outline"
              />
            )}
          </div>
          <textarea
            readOnly
            value={conversion.output}
            placeholder={t.tools.codec.outputPlaceholder}
            className="w-full flex-1 min-h-[220px] sm:min-h-[260px] p-4 bg-transparent text-base sm:text-lg font-tamil leading-[1.7] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:outline-none resize-y"
          />
        </div>
      </div>

      {/* Mobile Sticky Thumb Action Bar */}
      <StickyActionBar
        outputText={conversion.output}
        onClear={handleClear}
        onSwap={handleSwap}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
        swapLabel={t.actions.swap}
      />
    </div>
  );
}
