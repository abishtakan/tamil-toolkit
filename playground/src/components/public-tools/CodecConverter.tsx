import { useState, useEffect, useTransition } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Textarea } from "../ui/textarea";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { ArrowLeftRight, Sparkles } from "lucide-react";

export type CodecProfile =
  | "auto"
  | "bamini-v1"
  | "tscii-1.7-v1"
  | "tab-v1"
  | "tam-v1"
  | "anjal-v1"
  | "vanavil-avvaiyar-cid-v1"
  | "lt-tm-cid-v1";

const PROFILES: { id: CodecProfile; labelEn: string; labelTa: string }[] = [
  { id: "auto", labelEn: "Auto-Detect", labelTa: "தானியங்கி" },
  { id: "bamini-v1", labelEn: "Bamini", labelTa: "பாமினி" },
  { id: "tscii-1.7-v1", labelEn: "TSCII", labelTa: "TSCII" },
  { id: "tab-v1", labelEn: "TAB", labelTa: "TAB" },
  { id: "tam-v1", labelEn: "TAM", labelTa: "TAM" },
  { id: "anjal-v1", labelEn: "Anjal", labelTa: "அஞ்சல்" },
  { id: "vanavil-avvaiyar-cid-v1", labelEn: "Vanavil", labelTa: "வானவில்" },
  { id: "lt-tm-cid-v1", labelEn: "LT-TM", labelTa: "LT-TM" }
];

const BAMINI_SAMPLE = "jkpo; nkhop cyfpd; njhd;ikahd nkhopfspy; xd;whFk;.";
const UNICODE_SAMPLE = "தமிழ் மொழி உலகின் தொன்மையான மொழிகளில் ஒன்றாகும்.";

export function CodecConverter() {
  const { language, t } = useLanguage();
  const [, startTransition] = useTransition();

  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [selectedProfile, setSelectedProfile] = useState<CodecProfile>("auto");
  const [detectedProfile, setDetectedProfile] = useState<string | null>(null);
  const [confidence, setConfidence] = useState<number | null>(null);
  const [direction, setDirection] = useState<"to_unicode" | "from_unicode">("to_unicode");
  const [latency, setLatency] = useState<number>(0);

  const convertText = (text: string, profile: CodecProfile, dir: "to_unicode" | "from_unicode") => {
    if (!text.trim()) {
      setOutput("");
      setDetectedProfile(null);
      setConfidence(null);
      setLatency(0);
      return;
    }

    const t0 = performance.now();
    try {
      if (dir === "to_unicode") {
        let activeProfile = profile;
        if (profile === "auto") {
          const encoder = new TextEncoder();
          const bytes = encoder.encode(text);
          const detection = tt.detect_encoding(bytes);
          if (detection && detection.encoding) {
            activeProfile = detection.encoding as CodecProfile;
            setDetectedProfile(detection.encoding);
            setConfidence(detection.confidence);
          } else {
            activeProfile = "bamini-v1"; // graceful fallback
            setDetectedProfile("bamini-v1 (fallback)");
            setConfidence(0.5);
          }
        } else {
          setDetectedProfile(profile);
          setConfidence(1.0);
        }

        let res = "";
        const encoder = new TextEncoder();
        switch (activeProfile) {
          case "bamini-v1":
            res = tt.bamini_to_unicode(text);
            break;
          case "tscii-1.7-v1":
            res = tt.tscii_bytes_to_unicode(encoder.encode(text));
            break;
          case "tab-v1":
            res = tt.tab_bytes_to_unicode(encoder.encode(text));
            break;
          case "tam-v1":
            res = tt.tam_bytes_to_unicode(encoder.encode(text));
            break;
          case "anjal-v1":
            res = tt.anjal_bytes_to_unicode(encoder.encode(text));
            break;
          case "vanavil-avvaiyar-cid-v1":
            res = tt.vanavil_text_to_unicode(text);
            break;
          case "lt-tm-cid-v1":
            res = tt.lt_tm_text_to_unicode(text);
            break;
          default:
            res = tt.bamini_to_unicode(text);
        }
        setOutput(res);
      } else {
        // from_unicode to legacy font
        let activeProfile = profile === "auto" ? "bamini-v1" : profile;
        setDetectedProfile(activeProfile);
        let res = "";
        const decoder = new TextDecoder("utf-8");
        switch (activeProfile) {
          case "bamini-v1":
            res = tt.unicode_to_bamini(text);
            break;
          case "tscii-1.7-v1":
            res = decoder.decode(new Uint8Array(tt.unicode_to_tscii_bytes(text)));
            break;
          case "tab-v1":
            res = decoder.decode(new Uint8Array(tt.unicode_to_tab_bytes(text)));
            break;
          case "tam-v1":
            res = decoder.decode(new Uint8Array(tt.unicode_to_tam_bytes(text)));
            break;
          case "anjal-v1":
            res = decoder.decode(new Uint8Array(tt.unicode_to_anjal_bytes(text)));
            break;
          case "vanavil-avvaiyar-cid-v1":
            res = tt.unicode_to_vanavil_text(text);
            break;
          case "lt-tm-cid-v1":
            res = tt.unicode_to_lt_tm_text(text);
            break;
          default:
            res = tt.unicode_to_bamini(text);
        }
        setOutput(res);
      }
    } catch (err) {
      console.error("Conversion error:", err);
      setOutput("Error during conversion");
    } finally {
      setLatency(performance.now() - t0);
    }
  };

  useEffect(() => {
    startTransition(() => {
      convertText(input, selectedProfile, direction);
    });
  }, [input, selectedProfile, direction]);

  const handleSwap = () => {
    const nextDir = direction === "to_unicode" ? "from_unicode" : "to_unicode";
    setDirection(nextDir);
    setInput(output);
  };

  const handleClear = () => {
    setInput("");
    setOutput("");
    setDetectedProfile(null);
    setConfidence(null);
    setLatency(0);
  };

  const handleLoadSample = () => {
    if (direction === "to_unicode") {
      setInput(BAMINI_SAMPLE);
    } else {
      setInput(UNICODE_SAMPLE);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tool Header & Earthen Chips */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.codec.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.codec.desc}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={handleLoadSample}
            className="text-xs font-tamil text-[var(--color-semman)] border-[var(--color-semman)]/30"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            <span>{t.actions.loadSample}</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleSwap}
            className="text-xs font-tamil"
          >
            <ArrowLeftRight className="w-3.5 h-3.5 mr-1" />
            <span>
              {direction === "to_unicode"
                ? language === "en" ? "→ Unicode" : "→ ஒருங்குறி"
                : language === "en" ? "→ Legacy Font" : "→ எழுத்துரு"}
            </span>
          </Button>
        </div>
      </div>

      {/* Swipeable Single-Tap Profile Chips */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-[var(--color-muted)] font-tamil tracking-wide uppercase">
          {t.tools.codec.allProfiles}
        </label>
        <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
          {PROFILES.map((p) => {
            const isActive = selectedProfile === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setSelectedProfile(p.id)}
                data-active={isActive}
                className={`px-3.5 py-1.5 rounded-full text-xs font-medium font-tamil whitespace-nowrap transition-all select-none border min-h-[38px] ${
                  isActive
                    ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] shadow-sm font-semibold"
                    : "bg-[var(--bg-surface)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
                }`}
              >
                {language === "ta" ? p.labelTa : p.labelEn}
              </button>
            );
          })}
        </div>
      </div>

      {/* Editor Grid: Mobile Stacked / Desktop Side-by-Side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Input Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
              {direction === "to_unicode"
                ? language === "en" ? "Input (Legacy Text / Font):" : "உள்ளீடு (பழைய எழுத்துரு / Text):"
                : language === "en" ? "Input (Tamil Unicode):" : "உள்ளீடு (தமிழ் ஒருங்குறி / Unicode):"}
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
            onChange={(e) => setInput(e.target.value)}
            placeholder={t.tools.codec.inputPlaceholder}
            className="min-h-[160px] sm:min-h-[200px]"
          />
        </div>

        {/* Output Panel */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
                {direction === "to_unicode"
                  ? language === "en" ? "Output (Modern Unicode):" : "வெளியீடு (ஒருங்குறி / Unicode):"
                  : language === "en" ? "Output (Legacy Encoded Font):" : "வெளியீடு (பழைய எழுத்துரு / Output):"}
              </span>
              {detectedProfile && (
                <Badge variant="terracotta">
                  {detectedProfile} {confidence ? `(${(confidence * 100).toFixed(0)}%)` : ""}
                </Badge>
              )}
            </div>
            {latency > 0 && (
              <Badge variant="mono">{latency.toFixed(1)} ms</Badge>
            )}
          </div>
          <div className="relative">
            <Textarea
              readOnly
              value={output}
              placeholder={t.tools.codec.outputPlaceholder}
              className="min-h-[160px] sm:min-h-[200px] bg-[var(--bg-raised)]/70 text-[var(--color-mai)] font-medium"
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

      {/* Mobile Sticky Thumb Action Bar */}
      <StickyActionBar
        outputText={output}
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
