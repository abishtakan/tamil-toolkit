import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import {
  getLetters,
  hyphenateWord,
  getHyphenationPoints,
  hyphenateText,
  wrapText,
  HyphenationOptions
} from "../../lib/engine";
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
  BookOpen
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

  // Handle lone combining mark rendered with dotted circle \u25CC if present
  if (trimmed.charCodeAt(0) === 0x25cc && trimmed.length > 1) {
    trimmed = trimmed.slice(1);
  }

  const firstChar = trimmed.charAt(0);
  const firstCp = firstChar.charCodeAt(0);

  // 1. Naked pulli / virama (U+0BCD)
  if (firstCp === 0x0bcd) {
    return {
      hasError: true,
      type: "pulli",
      label: labels?.errOrphanedPulli || "(தனிப் புள்ளித் தொடக்கம்!)"
    };
  }

  // 2. Naked visiri (U+0BBF, U+0BC0)
  if (firstCp === 0x0bbf || firstCp === 0x0bc0) {
    return {
      hasError: true,
      type: "visiri",
      label: labels?.errOrphanedVisiri || "(விசிறி மட்டும் தொடக்கம்!)"
    };
  }

  // 3. Other orphaned combining vowel signs / diacritics
  if (
    (firstCp >= 0x0bbe && firstCp <= 0x0bcc) ||
    firstCp === 0x0bd7 ||
    firstCp === 0x0b82
  ) {
    return {
      hasError: true,
      type: "diacritic",
      label: labels?.errOrphanedDiacritic || "(சிதைந்த குறியீடு தொடக்கம்!)"
    };
  }

  // 4. Starts with a pure consonant (Mei / ஒற்று) - base consonant followed by virama
  if (trimmed.length > 1 && trimmed.charAt(1) === "\u0bcd") {
    return {
      hasError: true,
      type: "mei",
      label: labels?.errPureConsonant || "(புள்ளி எழுத்தில் தொடக்கம்!)"
    };
  }

  // 5. Starts with Aytham (ஃ / U+0B83)
  if (firstChar === "\u0b83") {
    return {
      hasError: true,
      type: "aytham",
      label: labels?.errAytham || "(ஆய்த எழுத்தில் தொடக்கம்!)"
    };
  }

  return null;
}

export function HyphenatorTool() {
  const { t } = useLanguage();

  // Tab State: "word" | "text" | "wrap"
  const [activeTab, setActiveTab] = useState<"word" | "text" | "wrap">("word");

  // Options State
  const [leftMin, setLeftMin] = useState<number>(3);
  const [rightMin, setRightMin] = useState<number>(3);
  const [delimiter, setDelimiter] = useState<string>("-");

  // Tab 1 (Word) State
  const [wordInput, setWordInput] = useState<string>("தமிழ்நாடு");

  // Tab 2 (Text) State
  const defaultParagraph =
    "பல்கலைக்கழகங்களில் தமிழ் மொழியியல் மற்றும் இலக்கிய ஆராய்ச்சிகள் உலகளாவிய தரத்தில் செழுமை பெற வேண்டும். அகிலத்திரட்டு போன்ற அரிய நூல்களின் ஓலைச்சுவடிப் பதிப்புகளைப் பாதுகாக்க வேண்டியது இன்றியமையாத மரபாகும்.";
  const [textInput, setTextInput] = useState<string>(defaultParagraph);
  const [showSoftHyphens, setShowSoftHyphens] = useState<boolean>(true);

  // Tab 3 (Wrap) State
  const [wrapWidth, setWrapWidth] = useState<number>(18);
  const [compareNaive, setCompareNaive] = useState<boolean>(true);

  // Preset sample words
  const sampleWords = [
    "தமிழ்நாடு",
    "பல்கலைக்கழகம்",
    "திருக்குறள்",
    "செம்மொழி",
    "அகிலத்திரட்டு",
    "வணக்கம்"
  ];

  const currentOptions: HyphenationOptions = useMemo(
    () => ({
      left_min: leftMin,
      right_min: rightMin,
      delimiter: delimiter
    }),
    [leftMin, rightMin, delimiter]
  );

  const wordLetters = useMemo(
    () => getLetters(wordInput.trim()),
    [wordInput]
  );

  // Tab 1 Computations
  const wordResult = useMemo(() => {
    const trimmed = wordInput.trim();
    if (!trimmed) {
      return {
        hyphenated: "",
        syllables: [] as string[],
        breakpoints: [] as ReturnType<typeof getHyphenationPoints>
      };
    }
    const res = hyphenateWord(trimmed, currentOptions);
    const pts = getHyphenationPoints(trimmed, currentOptions);
    return {
      hyphenated: res.hyphenated,
      syllables: res.syllables,
      breakpoints: pts
    };
  }, [wordInput, currentOptions]);

  // Tab 2 Computations
  const textHyphenatedHtml = useMemo(() => {
    if (!textInput) return "";
    return hyphenateText(textInput, {
      ...currentOptions,
      delimiter: "&shy;"
    });
  }, [textInput, currentOptions]);

  const textHyphenatedUnicode = useMemo(() => {
    if (!textInput) return "";
    return hyphenateText(textInput, {
      ...currentOptions,
      delimiter: "\u00AD"
    });
  }, [textInput, currentOptions]);

  const textHyphenatedZwsp = useMemo(() => {
    if (!textInput) return "";
    return hyphenateText(textInput, {
      ...currentOptions,
      delimiter: "\u200B"
    });
  }, [textInput, currentOptions]);

  // Tab 3 Computations
  const wrappedResult = useMemo(() => {
    if (!textInput) return { lines: [], overflow_count: 0 };
    return wrapText(textInput, wrapWidth, currentOptions);
  }, [textInput, wrapWidth, currentOptions]);

  // Naive wrap for comparison: wraps strictly by character count without syllable boundary checks
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
        // Naive character slicing
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

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-150">
      {/* Title & Description Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
              {t.tools.hyphenator.title}
            </h2>
            <Badge variant="terracotta">Grammar-Safe</Badge>
            <Badge variant="sandhanam">WASM + SIMD</Badge>
          </div>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans max-w-2xl leading-relaxed">
            {t.tools.hyphenator.desc}
          </p>
        </div>

        {/* Global Tab Switcher */}
        <div className="flex items-center gap-1.5 p-1 bg-[var(--bg-surface)] border border-[var(--border-line)] rounded-xl shrink-0">
          <button
            onClick={() => setActiveTab("word")}
            className={`px-3 py-1.5 rounded-lg text-xs font-tamil font-medium transition-all ${
              activeTab === "word"
                ? "bg-[var(--color-semman)] text-[#faf7f2] font-bold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.hyphenator.tabWord}
          </button>
          <button
            onClick={() => setActiveTab("text")}
            className={`px-3 py-1.5 rounded-lg text-xs font-tamil font-medium transition-all ${
              activeTab === "text"
                ? "bg-[var(--color-semman)] text-[#faf7f2] font-bold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.hyphenator.tabText}
          </button>
          <button
            onClick={() => setActiveTab("wrap")}
            className={`px-3 py-1.5 rounded-lg text-xs font-tamil font-medium transition-all ${
              activeTab === "wrap"
                ? "bg-[var(--color-semman)] text-[#faf7f2] font-bold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {t.tools.hyphenator.tabWrap}
          </button>
        </div>
      </div>

      {/* Global Margin & Delimiter Configuration Strip */}
      <Card className="p-4 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-[var(--color-semman)]" />
            <span className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)]">
              {t.tools.hyphenator.marginHeading}
            </span>
          </div>
          <span className="text-[11px] font-tamil-sans text-[var(--color-muted)]">
            Tamil Orthographic Constraints
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {/* Left Margin Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-tamil">
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

          {/* Right Margin Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs font-tamil">
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

          {/* Syllable Delimiter Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-tamil text-[var(--color-muted)] block">
              {t.tools.hyphenator.delimiterLabel}
            </label>
            <div className="grid grid-cols-5 gap-1.5">
              {[
                { val: "-", label: "-" },
                { val: "·", label: "·" },
                { val: "/", label: "/" },
                { val: "\u00AD", label: "shy" },
                { val: "\u200B", label: "none" }
              ].map((item) => (
                <button
                  key={item.label}
                  type="button"
                  onClick={() => setDelimiter(item.val)}
                  className={`py-1.5 rounded-xl text-xs font-mono font-medium border text-center transition-colors ${
                    delimiter === item.val
                      ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
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

      {/* Tab 1: Single Word Syllable Analysis */}
      {activeTab === "word" && (
        <div className="space-y-6">
          {/* Input Section & Preset Chips */}
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
            <div>
              <label className="block text-xs sm:text-sm font-tamil font-semibold text-[var(--color-mai)] mb-2">
                {t.tools.hyphenator.wordInputLabel}
              </label>
              <input
                type="text"
                value={wordInput}
                onChange={(e) => setWordInput(e.target.value)}
                placeholder={t.tools.hyphenator.wordPlaceholder}
                className="w-full px-4 py-3 text-base sm:text-lg font-tamil rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)] transition-colors"
              />
            </div>

            {/* Presets */}
            <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-[var(--border-line)]">
              <span className="text-xs font-tamil text-[var(--color-muted)]">
                {t.tools.hyphenator.sampleWordsHeading}
              </span>
              {sampleWords.map((word) => (
                <button
                  key={word}
                  type="button"
                  onClick={() => setWordInput(word)}
                  className="px-2.5 py-1 text-xs font-tamil rounded-lg bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] transition-colors cursor-pointer"
                >
                  {word}
                </button>
              ))}
            </div>
          </Card>

          {/* Results Bento: Syllable Units + Delimited Word */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Syllable Unit Ribbon (Col 1-7) */}
            <Card className="lg:col-span-7 p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                <div className="flex items-center gap-2">
                  <Scissors className="w-4 h-4 text-[var(--color-semman)]" />
                  <span className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.hyphenator.syllableChipsHeading}
                  </span>
                </div>
                <Badge variant="outline">
                  {wordResult.syllables.length} {t.tools.hyphenator.syllablesCount}
                </Badge>
              </div>

              {/* Syllable Badges */}
              {wordResult.syllables.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {wordResult.syllables.map((syl, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)] text-base font-tamil font-bold text-[var(--color-mai)] shadow-xs"
                      >
                        <span className="text-xs font-mono text-[var(--color-muted)]">
                          #{i + 1}
                        </span>
                        <span>{syl}</span>
                      </div>
                    ))}
                  </div>

                  {/* Formatted Output with Delimiter */}
                  <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3">
                    <div>
                      <span className="text-[11px] font-tamil text-[var(--color-muted)] block mb-1">
                        Formatted Syllables:
                      </span>
                      <span className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-semman)] tracking-wide">
                        {wordResult.hyphenated || wordInput}
                      </span>
                    </div>
                    <CopyButton
                      text={wordResult.hyphenated || wordInput}
                      label={t.actions.copy}
                    />
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans">
                  {t.tools.hyphenator.wordPlaceholder}
                </p>
              )}

              {/* Coda Binding Guarantee Alert */}
              <div className="p-3.5 rounded-xl bg-[var(--color-sandhanam-light)] border border-[var(--color-sandhanam)]/30 text-xs font-tamil text-[var(--color-mai)] space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-[var(--color-semman)]">
                  <ShieldCheck className="w-4 h-4 shrink-0" />
                  <span>{t.tools.hyphenator.codaBindingNotice}</span>
                </div>
                <p className="leading-relaxed pl-5 text-[11px] text-[var(--color-muted)]">
                  {t.tools.hyphenator.codaBindingRule}
                </p>
              </div>
            </Card>

            {/* Permissible Breakpoints Table (Col 8-12) */}
            <Card className="lg:col-span-5 p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
              <div className="border-b border-[var(--border-line)] pb-2.5 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.hyphenator.breakpointsHeading}
                  </span>
                  <Badge variant="sandhanam">
                    {wordResult.breakpoints.length} {t.tools.hyphenator.breakpointsCount}
                  </Badge>
                </div>
                <p className="text-[11px] text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.hyphenator.breakpointsDesc}
                </p>
              </div>

              {wordResult.breakpoints.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-tamil">
                    <thead>
                      <tr className="border-b border-[var(--border-line)] text-[var(--color-muted)]">
                        <th className="pb-2 font-medium">#</th>
                        <th className="pb-2 font-medium">Line 1 (-) | Line 2</th>
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
                          <tr key={idx} className="group hover:bg-[var(--bg-raised)]/50">
                            <td className="py-2.5 font-mono text-[var(--color-muted)]">
                              #{idx + 1}
                            </td>
                            <td className="py-2.5 font-semibold text-[var(--color-mai)]">
                              <span className="text-[var(--color-semman)]">{left}-</span>
                              <span className="px-1.5 text-[var(--color-muted)]">/</span>
                              <span>{right}</span>
                            </td>
                            <td className="py-2.5 text-right font-mono text-[11px] text-[var(--color-muted)]">
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
                  <AlertCircle className="w-8 h-8 mx-auto text-[var(--color-sandhanam)] opacity-80" />
                  <p className="text-xs text-[var(--color-muted)] font-tamil">
                    {t.tools.hyphenator.noBreakpoints}
                  </p>
                  <p className="text-[11px] text-[var(--color-muted)]/70 font-tamil-sans">
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
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
              <label className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)]">
                {t.tools.hyphenator.textInputLabel}
              </label>
              <button
                type="button"
                onClick={() => setTextInput(defaultParagraph)}
                className="text-xs font-tamil text-[var(--color-semman)] hover:underline cursor-pointer"
              >
                {t.tools.hyphenator.sampleParagraphButton}
              </button>
            </div>

            <textarea
              rows={4}
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={t.tools.hyphenator.textPlaceholder}
              className="w-full px-4 py-3 text-xs sm:text-sm font-tamil rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)] transition-colors leading-relaxed"
            />

            {/* Soft-Hyphen Options Strip */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-[var(--border-line)]">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={showSoftHyphens}
                  onChange={(e) => setShowSoftHyphens(e.target.checked)}
                  className="rounded border-[var(--border-line)] accent-[var(--color-semman)] w-4 h-4 cursor-pointer"
                />
                <span className="text-xs font-tamil text-[var(--color-mai)]">
                  {t.tools.hyphenator.showSoftHyphensToggle}
                </span>
              </label>

              <div className="flex flex-wrap items-center gap-2">
                <CopyButton
                  html={`<p>${textHyphenatedHtml}</p>`}
                  text={textHyphenatedUnicode}
                  label={t.tools.hyphenator.copyWordButton}
                  variant="primary"
                />
                <CopyButton
                  html={`<p>${textHyphenatedZwsp.split("\u200B").join("<wbr>")}</p>`}
                  text={textHyphenatedZwsp}
                  label={t.tools.hyphenator.copyNoHyphenButton}
                  variant="outline"
                />
                <CopyButton
                  text={textHyphenatedHtml}
                  label={t.tools.hyphenator.copyHtmlButton}
                  variant="outline"
                />
                <CopyButton
                  text={textHyphenatedUnicode}
                  label={t.tools.hyphenator.copyTextButton}
                  variant="outline"
                />
              </div>
            </div>
          </Card>

          {/* Rendered Preview Container */}
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--color-semman)]" />
                <span className="text-xs sm:text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {showSoftHyphens
                    ? "Injected Soft-Hyphen Visual Preview"
                    : "Browser Flow Preview (Resize Window)"}
                </span>
              </div>
              <span className="text-[11px] font-mono text-[var(--color-muted)]">
                &amp;shy; injected
              </span>
            </div>

            <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-sm sm:text-base leading-loose text-[var(--color-mai)]">
              {showSoftHyphens ? (
                // Display visible marks for soft-hyphens
                <span>
                  {textHyphenatedHtml.split("&shy;").map((part, i, arr) => (
                    <span key={i}>
                      {part}
                      {i < arr.length - 1 && (
                        <span
                          title="Soft Hyphen Breakpoint (&shy;)"
                          className="mx-0.5 px-1 py-0.5 rounded text-[11px] font-mono font-bold bg-[var(--color-semman-light)] text-[var(--color-semman)] border border-[var(--color-semman)]/30 select-none inline-flex items-center justify-center"
                        >
                          ·
                        </span>
                      )}
                    </span>
                  ))}
                </span>
              ) : (
                // Render true HTML with soft hyphens for responsive browser-native break testing
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
          {/* Controls: Width Slider & Comparison Toggle */}
          <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1 flex-1 max-w-sm">
                <div className="flex justify-between items-center text-xs font-tamil">
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

              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={compareNaive}
                    onChange={(e) => setCompareNaive(e.target.checked)}
                    className="rounded border-[var(--border-line)] accent-[var(--color-semman)] w-4 h-4 cursor-pointer"
                  />
                  <span className="text-xs font-tamil font-medium text-[var(--color-mai)]">
                    {t.tools.hyphenator.compareToggle}
                  </span>
                </label>
              </div>
            </div>
          </Card>

          {/* Columns Simulation Grid */}
          <div
            className={`grid gap-6 ${
              compareNaive ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1 max-w-xl mx-auto"
            }`}
          >
            {/* Column A: Naive Wrap (Shows Broken Pulli) */}
            {compareNaive && (
              <Card className="p-5 bg-[var(--bg-surface)] border border-rose-300 dark:border-rose-900/50 rounded-2xl shadow-xs space-y-3">
                <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                  <div className="flex items-center gap-2 text-rose-700 dark:text-rose-400">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-xs sm:text-sm font-tamil font-bold">
                      {t.tools.hyphenator.defaultWrapHeading}
                    </span>
                  </div>
                  <Badge variant="outline" className="border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-400">
                    {naiveLines.length} {t.tools.hyphenator.lineCount}
                  </Badge>
                </div>

                {/* Simulated Narrow Column Container */}
                <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-xs sm:text-sm leading-relaxed space-y-1.5 font-mono">
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
                        <span className="text-[10px] text-[var(--color-muted)] select-none mr-2 font-mono">
                          {String(idx + 1).padStart(2, "0")}
                        </span>
                        <span>{line}</span>
                        {lineError && (
                          <span className="ml-2 text-[10px] font-tamil font-bold text-rose-600 dark:text-rose-400">
                            {lineError.label}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Card>
            )}

            {/* Column B: Syllabic Wrap (Compliant) */}
            <Card className="p-5 bg-[var(--bg-surface)] border border-emerald-300 dark:border-emerald-900/50 rounded-2xl shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2.5">
                <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
                  <ShieldCheck className="w-4 h-4" />
                  <span className="text-xs sm:text-sm font-tamil font-bold">
                    {t.tools.hyphenator.syllabicWrapHeading}
                  </span>
                </div>
                <Badge variant="outline" className="border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400">
                  {wrappedResult.lines.length} {t.tools.hyphenator.lineCount}
                </Badge>
              </div>

              {/* Simulated Narrow Column Container */}
              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-tamil text-xs sm:text-sm leading-relaxed space-y-1.5 font-mono">
                {wrappedResult.lines.map((line, idx) => (
                  <div
                    key={idx}
                    className="px-2 py-1 rounded text-[var(--color-mai)] bg-[var(--bg-surface)] border border-[var(--border-line)] hover:border-[var(--color-semman)] transition-colors"
                  >
                    <span className="text-[10px] text-[var(--color-muted)] select-none mr-2 font-mono">
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
      <Card className="p-5 bg-[var(--bg-surface)] border-[var(--border-line)] rounded-2xl shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-line)] pb-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Download className="w-5 h-5 text-[var(--color-semman)]" />
              <h3 className="text-sm sm:text-base font-tamil font-bold text-[var(--color-mai)]">
                {t.tools.hyphenator.integrationsTitle}
              </h3>
            </div>
            <p className="text-xs text-[var(--color-muted)] font-tamil-sans">
              {t.tools.hyphenator.integrationsDesc}
            </p>
          </div>
          <Badge variant="outline" className="border-emerald-300 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400 self-start sm:self-auto font-mono text-[11px]">
            ta-IN · ta-LK · ta-SG · ta-MY · ta
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Download Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href="/downloads/tamil-hyphenation.oxt"
              download="tamil-hyphenation.oxt"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-tamil font-bold bg-[var(--color-semman)] text-[#faf7f2] hover:bg-[var(--color-semman)]/90 shadow-xs transition-colors"
            >
              <Download className="w-4 h-4" />
              {t.tools.hyphenator.downloadOxtButton}
            </a>
            <a
              href="/downloads/hyph_ta_IN.dic"
              download="hyph_ta_IN.dic"
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-tamil font-medium bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)] hover:border-[var(--color-semman)] hover:text-[var(--color-semman)] transition-colors"
            >
              <Download className="w-4 h-4" />
              {t.tools.hyphenator.downloadDicButton}
            </a>
          </div>

          {/* Integration Setup Guides Links */}
          <div className="flex flex-wrap items-center gap-2.5 text-xs font-tamil text-[var(--color-muted)]">
            <span className="font-semibold text-[var(--color-mai)]">Setup Guides:</span>
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
