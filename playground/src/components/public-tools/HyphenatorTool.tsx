import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import {
  getLetters,
  hyphenateWord,
  getHyphenationPoints,
  hyphenateText,
  wrapText,
  HyphenationOptions,
  isEngineReady,
} from "../../lib/engine";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import {
  Scissors,
  Sliders,
  FileText,
  ShieldCheck,
  AlertCircle,
  Download,
  BookOpen,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export interface LineStartError {
  hasError: boolean;
  type: "pulli" | "visiri" | "diacritic" | "mei" | "aytham";
  label: string;
}

export function getLineStartError(
  line: string,
  labels?: {
    errOrphanedPulli?: string;
    errOrphanedVisiri?: string;
    errOrphanedDiacritic?: string;
    errPureConsonant?: string;
    errAytham?: string;
  }
): LineStartError | null {
  let trimmed = line.trimStart();
  if (!trimmed) return null;

  if (trimmed.charCodeAt(0) === 0x25cc && trimmed.length > 1) {
    trimmed = trimmed.slice(1);
  }

  const firstChar = trimmed.charAt(0);
  const firstCp = firstChar.charCodeAt(0);

  if (firstCp === 0x0bcd) {
    return {
      hasError: true,
      type: "pulli",
      label: labels?.errOrphanedPulli || "(தனிப் புள்ளித் தொடக்கம்!)",
    };
  }

  if (firstCp === 0x0bbf || firstCp === 0x0bc0) {
    return {
      hasError: true,
      type: "visiri",
      label: labels?.errOrphanedVisiri || "(விசிறி மட்டும் தொடக்கம்!)",
    };
  }

  if (
    (firstCp >= 0x0bbe && firstCp <= 0x0bcc) ||
    firstCp === 0x0bd7 ||
    firstCp === 0x0b82
  ) {
    return {
      hasError: true,
      type: "diacritic",
      label: labels?.errOrphanedDiacritic || "(சிதைந்த குறியீடு தொடக்கம்!)",
    };
  }

  if (trimmed.length > 1 && trimmed.charAt(1) === "\u0bcd") {
    return {
      hasError: true,
      type: "mei",
      label: labels?.errPureConsonant || "(புள்ளி எழுத்தில் தொடக்கம்!)",
    };
  }

  if (firstChar === "\u0b83") {
    return {
      hasError: true,
      type: "aytham",
      label: labels?.errAytham || "(ஆய்த எழுத்தில் தொடக்கம்!)",
    };
  }

  return null;
}

interface HyphenatorToolProps {
  engineReady?: boolean;
}

export function HyphenatorTool({ engineReady }: HyphenatorToolProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [activeTab, setActiveTab] = useState<"word" | "text" | "wrap">("word");
  const [showSettings, setShowSettings] = useState(false);

  const [leftMin, setLeftMin] = useState<number>(3);
  const [rightMin, setRightMin] = useState<number>(3);
  const [delimiter, setDelimiter] = useState<string>("-");

  const [wordInput, setWordInput] = useState<string>("தமிழ்நாடு");

  const defaultParagraph =
    "பல்கலைக்கழகங்களில் தமிழ் மொழியியல் மற்றும் இலக்கிய ஆராய்ச்சிகள் உலகளாவிய தரத்தில் செழுமை பெற வேண்டும். அகிலத்திரட்டு போன்ற அரிய நூல்களின் ஓலைச்சுவடிப் பதிப்புகளைப் பாதுகாக்க வேண்டியது இன்றியமையாத மரபாகும்.";
  const [textInput, setTextInput] = useState<string>(defaultParagraph);
  const [showSoftHyphens, setShowSoftHyphens] = useState<boolean>(true);

  const [wrapWidth, setWrapWidth] = useState<number>(18);
  const [compareNaive, setCompareNaive] = useState<boolean>(true);

  const sampleWords = [
    "தமிழ்நாடு",
    "பல்கலைக்கழகம்",
    "திருக்குறள்",
    "செம்மொழி",
    "அகிலத்திரட்டு",
    "வணக்கம்",
  ];

  const currentOptions: HyphenationOptions = useMemo(
    () => ({
      left_min: leftMin,
      right_min: rightMin,
      delimiter,
    }),
    [leftMin, rightMin, delimiter]
  );

  const wordLetters = useMemo(
    () => (ready ? getLetters(wordInput.trim()) : Array.from(wordInput.trim())),
    [wordInput, ready]
  );

  const wordResult = useMemo(() => {
    const trimmed = wordInput.trim();
    if (!ready || !trimmed) {
      return {
        hyphenated: trimmed,
        syllables: [] as string[],
        breakpoints: [] as ReturnType<typeof getHyphenationPoints>,
      };
    }
    const res = hyphenateWord(trimmed, currentOptions);
    const pts = getHyphenationPoints(trimmed, currentOptions);
    return {
      hyphenated: res.hyphenated,
      syllables: res.syllables,
      breakpoints: pts,
    };
  }, [wordInput, currentOptions, ready]);

  const textHyphenatedHtml = useMemo(() => {
    if (!ready || !textInput) return textInput;
    return hyphenateText(textInput, { ...currentOptions, delimiter: "&shy;" });
  }, [textInput, currentOptions, ready]);

  const textHyphenatedUnicode = useMemo(() => {
    if (!ready || !textInput) return textInput;
    return hyphenateText(textInput, { ...currentOptions, delimiter: "\u00AD" });
  }, [textInput, currentOptions, ready]);

  const textHyphenatedZwsp = useMemo(() => {
    if (!ready || !textInput) return textInput;
    return hyphenateText(textInput, { ...currentOptions, delimiter: "\u200B" });
  }, [textInput, currentOptions, ready]);

  const wrappedResult = useMemo(() => {
    if (!ready || !textInput) return { lines: [], overflow_count: 0 };
    return wrapText(textInput, wrapWidth, currentOptions);
  }, [textInput, wrapWidth, currentOptions, ready]);

  const naiveLines = useMemo(() => {
    if (!textInput) return [];
    const words = textInput.split(/\s+/).filter(Boolean);
    const lines: string[] = [];
    let currentLine = "";

    for (const w of words) {
      if (!currentLine) {
        currentLine = w;
      } else if (currentLine.length + 1 + w.length <= wrapWidth) {
        currentLine += " " + w;
      } else {
        const remainingSpace = wrapWidth - currentLine.length - 1;
        if (remainingSpace > 1 && w.length > remainingSpace) {
          lines.push(currentLine + " " + w.slice(0, remainingSpace) + "-");
          currentLine = w.slice(remainingSpace);
        } else {
          lines.push(currentLine);
          currentLine = w;
        }
      }
    }
    if (currentLine) lines.push(currentLine);
    return lines;
  }, [textInput, wrapWidth]);

  const modeSwitcher = (
    <div className="inline-flex items-center gap-1 p-1 bg-[var(--bg-raised)] border border-[var(--border-line)] rounded-xl">
      {(
        [
          { id: "word", label: t.tools.hyphenator.tabWord },
          { id: "text", label: t.tools.hyphenator.tabText },
          { id: "wrap", label: t.tools.hyphenator.tabWrap },
        ] as const
      ).map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => setActiveTab(tab.id)}
          className={`px-3 py-1.5 min-h-[36px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
            activeTab === tab.id
              ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
              : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );

  const delimiterSummary =
    delimiter === "\u00AD" ? "shy" : delimiter === "\u200B" ? "ZWSP" : delimiter;

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.hyphenator.title}
        description={t.tools.hyphenator.desc}
        actions={modeSwitcher}
      />

      {/* Tab 1: Single Word Syllable Analysis */}
      {activeTab === "word" && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <div>
              <label
                htmlFor="hyphenator-word-input"
                className="block text-xs font-semibold text-[var(--color-mai)] mb-2"
              >
                {t.tools.hyphenator.wordInputLabel}
              </label>
              <input
                id="hyphenator-word-input"
                type="text"
                value={wordInput}
                onChange={(e) => setWordInput(e.target.value)}
                placeholder={t.tools.hyphenator.wordPlaceholder}
                className="w-full px-4 py-3 text-base sm:text-lg font-tamil rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
              />
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[var(--border-line)]">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-xs text-[var(--color-muted)] mr-1">
                  {t.tools.hyphenator.sampleWordsHeading}
                </span>
                {sampleWords.map((word) => (
                  <button
                    key={word}
                    type="button"
                    onClick={() => setWordInput(word)}
                    className={`px-2.5 py-1 text-xs font-tamil rounded-lg border transition-colors cursor-pointer ${
                      wordInput.trim() === word
                        ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold"
                        : "bg-[var(--bg-raised)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
                    }`}
                  >
                    {word}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => setShowSettings((prev) => !prev)}
                aria-expanded={showSettings}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs text-[var(--color-muted)] hover:text-[var(--color-mai)] hover:bg-[var(--bg-raised)] cursor-pointer"
              >
                <Sliders className="w-3.5 h-3.5" />
                <span>
                  {t.tools.hyphenator.settingsToggle}: {leftMin}/{rightMin} · &ldquo;{delimiterSummary}&rdquo;
                </span>
                {showSettings ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>
          </Card>

          {showSettings && (
            <Card className="p-4 sm:p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                <span className="text-xs sm:text-sm font-bold text-[var(--color-mai)]">
                  {t.tools.hyphenator.marginHeading}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[var(--color-muted)]">
                      {t.tools.hyphenator.leftMarginLabel}
                    </span>
                    <span className="font-mono-tamil font-bold text-[var(--color-mai)] px-2 py-0.5 rounded-md bg-[var(--bg-raised)] border border-[var(--border-line)]">
                      {leftMin}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={leftMin}
                    onChange={(e) => setLeftMin(parseInt(e.target.value, 10))}
                    className="w-full accent-[var(--color-semman)] cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[var(--color-muted)]">
                      {t.tools.hyphenator.rightMarginLabel}
                    </span>
                    <span className="font-mono-tamil font-bold text-[var(--color-mai)] px-2 py-0.5 rounded-md bg-[var(--bg-raised)] border border-[var(--border-line)]">
                      {rightMin}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={rightMin}
                    onChange={(e) => setRightMin(parseInt(e.target.value, 10))}
                    className="w-full accent-[var(--color-semman)] cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs text-[var(--color-muted)] block">
                    {t.tools.hyphenator.delimiterLabel}
                  </label>
                  <div className="grid grid-cols-5 gap-1.5">
                    {[
                      { val: "-", label: "-" },
                      { val: "·", label: "·" },
                      { val: "/", label: "/" },
                      { val: "\u00AD", label: "shy" },
                      { val: "\u200B", label: "none" },
                    ].map((item) => (
                      <button
                        key={item.label}
                        type="button"
                        onClick={() => setDelimiter(item.val)}
                        className={`py-1.5 rounded-lg text-xs font-mono-tamil font-medium border text-center transition-colors cursor-pointer ${
                          delimiter === item.val
                            ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold"
                            : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Results: Syllable Units + Breakpoints */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            <Card className="lg:col-span-7 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                <div className="flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-[var(--color-semman)]" />
                  <span className="text-xs sm:text-sm font-bold text-[var(--color-mai)]">
                    {t.tools.hyphenator.syllableChipsHeading}
                  </span>
                </div>
                <Badge variant="outline">
                  {wordResult.syllables.length} {t.tools.hyphenator.syllablesCount}
                </Badge>
              </div>

              {wordResult.syllables.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {wordResult.syllables.map((syl, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)] text-base font-tamil font-bold text-[var(--color-mai)]"
                      >
                        <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                          {i + 1}
                        </span>
                        <span>{syl}</span>
                      </div>
                    ))}
                  </div>

                  <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3">
                    <div>
                      <span className="text-[11px] text-[var(--color-muted)] block mb-1">
                        {t.tools.hyphenator.formattedSyllablesLabel}
                      </span>
                      <span className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-semman)] tracking-wide">
                        {wordResult.hyphenated || wordInput}
                      </span>
                    </div>
                    <CopyButton
                      text={wordResult.hyphenated || wordInput}
                      label={t.actions.copy}
                      variant="outline"
                      size="sm"
                    />
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[var(--color-muted)]">
                  {t.tools.hyphenator.wordPlaceholder}
                </p>
              )}

              <div className="p-3.5 rounded-xl bg-[var(--color-sandhanam-light)] border border-[var(--color-sandhanam)]/30 text-xs text-[var(--color-mai)] space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-[var(--color-semman)]">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  <span>{t.tools.hyphenator.codaBindingNotice}</span>
                </div>
                <p className="leading-relaxed pl-5 text-[11px] text-[var(--color-muted)]">
                  {t.tools.hyphenator.codaBindingRule}
                </p>
              </div>
            </Card>

            <Card className="lg:col-span-5 p-5 space-y-4">
              <div className="border-b border-[var(--border-line)] pb-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm font-bold text-[var(--color-mai)]">
                    {t.tools.hyphenator.breakpointsHeading}
                  </span>
                  <Badge variant="sandhanam">
                    {wordResult.breakpoints.length} {t.tools.hyphenator.breakpointsCount}
                  </Badge>
                </div>
                <p className="text-[11px] text-[var(--color-muted)] leading-relaxed">
                  {t.tools.hyphenator.breakpointsDesc}
                </p>
              </div>

              {wordResult.breakpoints.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[var(--border-line)] text-[var(--color-muted)]">
                        <th className="pb-2 font-medium">#</th>
                        <th className="pb-2 font-medium">Line 1 (-) / Line 2</th>
                        <th className="pb-2 font-medium text-right">Letters</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[var(--border-line)]">
                      {wordResult.breakpoints.map((pt, idx) => {
                        const left = wordLetters.slice(0, pt.letter_index).join("");
                        const right = wordLetters.slice(pt.letter_index).join("");
                        const leftLetters = pt.letter_index;
                        const rightLetters = wordLetters.length - pt.letter_index;
                        return (
                          <tr key={idx} className="hover:bg-[var(--bg-raised)]/40">
                            <td className="py-2.5 font-mono-tamil text-[var(--color-muted)]">
                              {idx + 1}
                            </td>
                            <td className="py-2.5 font-tamil font-semibold text-[var(--color-mai)]">
                              <span className="text-[var(--color-semman)]">{left}-</span>
                              <span className="px-1.5 text-[var(--color-muted)]">/</span>
                              <span>{right}</span>
                            </td>
                            <td className="py-2.5 text-right font-mono-tamil text-[11px] text-[var(--color-muted)]">
                              {leftLetters} + {rightLetters}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-8 text-center space-y-2">
                  <AlertCircle className="w-7 h-7 mx-auto text-[var(--color-sandhanam)] opacity-80" />
                  <p className="text-xs text-[var(--color-muted)]">
                    {t.tools.hyphenator.noBreakpoints}
                  </p>
                  <p className="text-[11px] text-[var(--color-muted)]/70">
                    {t.tools.hyphenator.shortWordNotice}
                  </p>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* Tab 2: Paragraph Soft-Hyphens */}
      {activeTab === "text" && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
              <label className="text-xs sm:text-sm font-bold text-[var(--color-mai)]">
                {t.tools.hyphenator.textInputLabel}
              </label>
              <button
                type="button"
                onClick={() => setTextInput(defaultParagraph)}
                className="text-xs font-medium text-[var(--color-semman)] hover:underline cursor-pointer"
              >
                {t.tools.hyphenator.sampleParagraphButton}
              </button>
            </div>

            <textarea
              rows={4}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={t.tools.hyphenator.textPlaceholder}
              className="w-full px-4 py-3 text-sm font-tamil rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)] leading-relaxed"
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--border-line)]">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showSoftHyphens}
                  onChange={(e) => setShowSoftHyphens(e.target.checked)}
                  className="rounded border-[var(--border-line)] accent-[var(--color-semman)] w-4 h-4 cursor-pointer"
                />
                <span className="text-xs text-[var(--color-mai)]">
                  {t.tools.hyphenator.showSoftHyphensToggle}
                </span>
              </label>

              <div className="flex flex-wrap items-center gap-2">
                <CopyButton
                  html={`<p>${textHyphenatedHtml}</p>`}
                  text={textHyphenatedUnicode}
                  label={t.tools.hyphenator.copyWordButton}
                  variant="primary"
                  size="sm"
                />
                <CopyButton
                  html={`<p>${textHyphenatedZwsp.split("\u200B").join("<wbr>")}</p>`}
                  text={textHyphenatedZwsp}
                  label={t.tools.hyphenator.copyNoHyphenButton}
                  variant="outline"
                  size="sm"
                />
                <CopyButton
                  text={textHyphenatedHtml}
                  label={t.tools.hyphenator.copyHtmlButton}
                  variant="outline"
                  size="sm"
                />
                <CopyButton
                  text={textHyphenatedUnicode}
                  label={t.tools.hyphenator.copyTextButton}
                  variant="outline"
                  size="sm"
                />
              </div>
            </div>
          </Card>

          <Card className="p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--color-semman)]" />
                <span className="text-xs sm:text-sm font-bold text-[var(--color-mai)]">
                  {showSoftHyphens
                    ? t.tools.hyphenator.visualPreviewHeading
                    : t.tools.hyphenator.browserFlowHeading}
                </span>
              </div>
              <span className="text-[11px] font-mono-tamil text-[var(--color-muted)]">
                &amp;shy;
              </span>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-sm sm:text-base leading-loose text-[var(--color-mai)]">
              {showSoftHyphens ? (
                <span>
                  {textHyphenatedHtml.split("&shy;").map((part, i, arr) => (
                    <span key={i}>
                      {part}
                      {i < arr.length - 1 && (
                        <span
                          title="Soft Hyphen Breakpoint (&shy;)"
                          className="mx-0.5 px-1 py-0.5 rounded text-[11px] font-mono-tamil font-bold bg-[var(--color-semman-light)] text-[var(--color-semman)] border border-[var(--color-semman)]/30 select-none inline-flex items-center justify-center"
                        >
                          ·
                        </span>
                      )}
                    </span>
                  ))}
                </span>
              ) : (
                <div
                  className="hyphens-auto break-words leading-relaxed"
                  dangerouslySetInnerHTML={{ __html: textHyphenatedHtml }}
                />
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Tab 3: Column Wrap Simulator */}
      {activeTab === "wrap" && (
        <div className="space-y-6">
          <Card className="p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1 flex-1 max-w-sm">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-[var(--color-mai)]">
                    {t.tools.hyphenator.columnWidthLabel}
                  </span>
                  <span className="font-mono-tamil font-bold text-[var(--color-semman)] px-2.5 py-0.5 rounded-md bg-[var(--bg-raised)] border border-[var(--border-line)]">
                    {wrapWidth} {t.tools.hyphenator.columnWidthLetters}
                  </span>
                </div>
                <input
                  type="range"
                  min="8"
                  max="35"
                  value={wrapWidth}
                  onChange={(e) => setWrapWidth(parseInt(e.target.value, 10))}
                  className="w-full accent-[var(--color-semman)] cursor-pointer"
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={compareNaive}
                  onChange={(e) => setCompareNaive(e.target.checked)}
                  className="rounded border-[var(--border-line)] accent-[var(--color-semman)] w-4 h-4 cursor-pointer"
                />
                <span className="text-xs font-medium text-[var(--color-mai)]">
                  {t.tools.hyphenator.compareToggle}
                </span>
              </label>
            </div>
          </Card>

          <div
            className={`grid gap-6 ${
              compareNaive ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1 max-w-xl mx-auto"
            }`}
          >
            {compareNaive && (
              <Card className="p-5 border-rose-300 dark:border-rose-900/50 space-y-3">
                <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                  <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-xs sm:text-sm font-bold">
                      {t.tools.hyphenator.defaultWrapHeading}
                    </span>
                  </div>
                  <Badge variant="outline" className="border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-400">
                    {naiveLines.length} {t.tools.hyphenator.lineCount}
                  </Badge>
                </div>

                <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-xs sm:text-sm leading-relaxed space-y-1.5">
                  {naiveLines.map((line, idx) => {
                    const lineError = getLineStartError(line, t.tools.hyphenator);
                    return (
                      <div
                        key={idx}
                        className={`px-2 py-1 rounded transition-colors ${
                          lineError
                            ? "bg-rose-100 dark:bg-rose-950/50 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800"
                            : "text-[var(--color-mai)]"
                        }`}
                      >
                        <span className="text-[10px] text-[var(--color-muted)] select-none mr-2 font-mono-tamil">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <span>{line}</span>
                        {lineError && (
                          <span className="ml-2 text-[10px] font-bold text-rose-600 dark:text-rose-400">
                            {lineError.label}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}

            <Card className="p-5 border-emerald-300 dark:border-emerald-900/50 space-y-3">
              <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                  <ShieldCheck className="w-4 h-4" />
                  <span className="text-xs sm:text-sm font-bold">
                    {t.tools.hyphenator.syllabicWrapHeading}
                  </span>
                </div>
                <Badge variant="outline" className="border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400">
                  {wrappedResult.lines.length} {t.tools.hyphenator.lineCount}
                </Badge>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-xs sm:text-sm leading-relaxed space-y-1.5">
                {wrappedResult.lines.map((line, idx) => (
                  <div
                    key={idx}
                    className="px-2 py-1 rounded text-[var(--color-mai)] bg-[var(--bg-surface)] border border-[var(--border-line)]"
                  >
                    <span className="text-[10px] text-[var(--color-muted)] select-none mr-2 font-mono-tamil">
                      {String(idx + 1).padStart(2, "0")}
                    </span>
                    <span>{line}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Desktop Publishing & Office Integrations Card */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-line)] pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Download className="w-4 h-4 text-[var(--color-semman)]" />
              <h2 className="text-sm sm:text-base font-bold text-[var(--color-mai)]">
                {t.tools.hyphenator.integrationsTitle}
              </h2>
            </div>
            <p className="text-xs text-[var(--color-muted)]">
              {t.tools.hyphenator.integrationsDesc}
            </p>
          </div>
          <Badge variant="mono" className="self-start sm:self-auto">
            ta-IN · ta-LK · ta-SG · ta-MY
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href="/downloads/tamil-hyphenation.oxt"
              download="tamil-hyphenation.oxt"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-semman)] text-[#faf7f2] hover:bg-[var(--color-semman-hover)] transition-colors"
            >
              <Download className="w-4 h-4" />
              {t.tools.hyphenator.downloadOxtButton}
            </a>
            <a
              href="/downloads/hyph_ta_IN.dic"
              download="hyph_ta_IN.dic"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-medium bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] transition-colors"
            >
              <Download className="w-4 h-4" />
              {t.tools.hyphenator.downloadDicButton}
            </a>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-xs text-[var(--color-muted)]">
            <span className="font-semibold text-[var(--color-mai)]">
              {t.tools.hyphenator.setupGuidesLabel}
            </span>
            <a
              href="https://github.com/tamil-toolkit/tamil-toolkit/blob/main/docs/integrations/libreoffice.md"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[var(--color-semman)] hover:underline"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {t.tools.hyphenator.libreofficeGuide}
            </a>
            <span>·</span>
            <a
              href="https://github.com/tamil-toolkit/tamil-toolkit/blob/main/docs/integrations/indesign.md"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[var(--color-semman)] hover:underline"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {t.tools.hyphenator.indesignGuide}
            </a>
            <span>·</span>
            <a
              href="https://github.com/tamil-toolkit/tamil-toolkit/blob/main/docs/integrations/scribus.md"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-[var(--color-semman)] hover:underline"
            >
              <BookOpen className="w-3.5 h-3.5" />
              {t.tools.hyphenator.scribusGuide}
            </a>
          </div>
        </div>
      </Card>
    </div>
  );
}
