import { useState, useMemo } from "react";
import { isEngineReady, tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { X } from "lucide-react";

interface NumeralFormatterProps {
  engineReady?: boolean;
}

type NumeralTab = "currencyWords" | "traditionalDigits" | "fractionsRanges" | "datesMath";
type InputTypeMode = "currency" | "number" | "ordinal" | "digits";

export function NumeralFormatter({ engineReady }: NumeralFormatterProps) {
  const { t } = useLanguage();
  const ready = engineReady ?? isEngineReady();

  const [activeTab, setActiveTab] = useState<NumeralTab>("currencyWords");

  // Tab 1: Currency & Words (Currency and Region/Locale strictly decoupled!)
  const [input, setInput] = useState("125000");
  const [inputType, setInputType] = useState<InputTypeMode>("currency");
  const [currency, setCurrency] = useState<tt.Currency>("INR");
  const [region, setRegion] = useState<tt.Locale>("TN");
  const [sourceDigits, setSourceDigits] = useState<tt.DigitStyle>("latin");
  const [outputDigits, setOutputDigits] = useState<tt.DigitStyle>("latin");
  const [grouping, setGrouping] = useState<tt.Grouping>("indian");

  // Tab 2: Traditional Integer, Words->Number (ITN) & Digit Script
  const [tradIntInput, setTradIntInput] = useState("1250");
  const [tradParseInput, setTradParseInput] = useState("௲௨௱௫௰");
  const [itnInput, setItnInput] = useState("நூற்று இருபத்து மூன்று");
  const [itnLocale, setItnLocale] = useState<tt.Locale>("TN");
  const [digitScriptText, setDigitScriptText] = useState("ஆண்டு 2026 — 1250");

  // Tab 3: Fractions, Percentages & Ranges
  const [fracWhole, setFracWhole] = useState("0");
  const [fracNum, setFracNum] = useState("3");
  const [fracDen, setFracDen] = useState("4");
  const [fracLocale, setFracLocale] = useState<tt.Locale>("SL");
  const [fracDigits, setFracDigits] = useState<tt.DigitStyle>("latin");

  const [percentInput, setPercentInput] = useState("12.5%");
  const [rangeStart, setRangeStart] = useState("10");
  const [rangeEnd, setRangeEnd] = useState("25");
  const [rangeStartIncl, setRangeStartIncl] = useState(true);
  const [rangeEndIncl, setRangeEndIncl] = useState(true);

  // Tab 4: Dates & Date Math
  const [dateInput, setDateInput] = useState("2026-04-14");
  const [dateLocale, setDateLocale] = useState<tt.Locale>("SL");
  const [dateStyle, setDateStyle] = useState<tt.DateStyle>("full");
  const [dateDigits, setDateDigits] = useState<tt.DigitStyle>("tamil");
  const [endDateInput, setEndDateInput] = useState("2026-11-20");
  const [addUnit, setAddUnit] = useState<"days" | "months" | "years">("days");
  const [addAmount, setAddAmount] = useState("30");

  // Tab 1 Computation
  const tab1Result = useMemo(() => {
    const clean = input.trim();
    if (!ready || !clean) {
      return {
        formalWords: "",
        chequeWords: "",
        spokenWords: "",
        formattedDisplay: "",
        traditionalSymbols: "",
        error: null as string | null,
      };
    }

    try {
      let formalWords = "";
      let chequeWords = "";
      let spokenWords = "";
      let formattedDisplay = "";
      let traditionalSymbols = "";

      if (inputType === "currency") {
        formalWords = tt.currency_decimal_to_words(clean, sourceDigits, currency, region, grouping);
        const rawFormatted = tt.format_currency_decimal(clean, sourceDigits, currency, region, grouping);
        formattedDisplay =
          outputDigits === "tamil" ? tt.convert_digits(rawFormatted, "tamil") : rawFormatted;
        chequeWords = `${formalWords} மட்டும்`;
        spokenWords = formalWords
          .replace(/ரூபாய்/g, "ரூபா")
          .replace(/இலட்சத்து/g, "லட்சத்து");
      } else if (inputType === "number") {
        const parsed = tt.parse_decimal(clean, sourceDigits, grouping, false);
        formalWords = tt.decimal_to_words(clean, sourceDigits, region, grouping, false);
        formattedDisplay = tt.format_decimal(parsed, outputDigits, grouping);
        chequeWords = `${formalWords} மட்டும்`;
        spokenWords = formalWords.replace(/இலட்சத்து/g, "லட்சத்து");
      } else if (inputType === "ordinal") {
        const normalizedLatin = sourceDigits === "tamil" ? tt.convert_digits(clean, "latin") : clean;
        const intVal = Number.parseInt(normalizedLatin.replace(/,/g, ""), 10);
        if (!Number.isFinite(intVal)) throw new Error("Enter a valid integer");
        formalWords = tt.ordinal_to_words(intVal, region);
        formattedDisplay =
          outputDigits === "tamil" ? tt.convert_digits(String(intVal), "tamil") : String(intVal);
      } else {
        formalWords = tt.digit_sequence_to_words(clean, sourceDigits, region);
        formattedDisplay = tt.convert_digits(clean, outputDigits);
      }

      // Traditional Tamil symbols for positive integers <= 1,000,000
      const latinStr = tt.convert_digits(clean, "latin").replace(/,/g, "");
      if (/^\d+$/.test(latinStr)) {
        const n = Number(latinStr);
        if (Number.isInteger(n) && n > 0 && n <= 1000000) {
          try {
            traditionalSymbols = tt.format_traditional_integer(n) || "";
          } catch {
            traditionalSymbols = "";
          }
        }
      }

      return {
        formalWords,
        chequeWords,
        spokenWords,
        formattedDisplay,
        traditionalSymbols,
        error: null,
      };
    } catch (err: unknown) {
      return {
        formalWords: "",
        chequeWords: "",
        spokenWords: "",
        formattedDisplay: "",
        traditionalSymbols: "",
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }, [input, inputType, currency, region, sourceDigits, outputDigits, grouping, ready]);

  // Tab 2 Computation
  const tab2Result = useMemo(() => {
    if (!ready) {
      return {
        formattedTrad: "",
        tradError: null as string | null,
        parsedArabic: "",
        parseError: null as string | null,
        itnNumber: "",
        itnError: null as string | null,
        toTamilDigits: "",
        toLatinDigits: "",
      };
    }
    let formattedTrad = "";
    let tradError: string | null = null;
    try {
      const n = Number(tradIntInput.trim());
      if (tradIntInput.trim()) {
        if (!Number.isInteger(n)) throw new Error("Enter an integer");
        formattedTrad = tt.format_traditional_integer(n);
      }
    } catch (err: unknown) {
      tradError = err instanceof Error ? err.message : String(err);
    }

    let parsedArabic = "";
    let parseError: string | null = null;
    try {
      if (tradParseInput.trim()) {
        parsedArabic = String(tt.parse_traditional_integer(tradParseInput.trim()));
      }
    } catch (err: unknown) {
      parseError = err instanceof Error ? err.message : String(err);
    }

    let itnNumber = "";
    let itnError: string | null = null;
    try {
      if (itnInput.trim()) {
        itnNumber = String(tt.words_to_number(itnInput.trim(), itnLocale));
      }
    } catch (err: unknown) {
      itnError = err instanceof Error ? err.message : String(err);
    }

    let toTamilDigits = "";
    let toLatinDigits = "";
    try {
      if (digitScriptText) {
        toTamilDigits = tt.convert_digits(digitScriptText, "tamil");
        toLatinDigits = tt.convert_digits(digitScriptText, "latin");
      }
    } catch {
      // ignore
    }

    return {
      formattedTrad,
      tradError,
      parsedArabic,
      parseError,
      itnNumber,
      itnError,
      toTamilDigits,
      toLatinDigits,
    };
  }, [tradIntInput, tradParseInput, itnInput, itnLocale, digitScriptText, ready]);

  // Tab 3 Computation
  const tab3Result = useMemo(() => {
    if (!ready) {
      return {
        formattedFrac: "",
        fracWords: "",
        fracSymbol: "",
        fracError: null as string | null,
        formattedPercent: "",
        ratioStr: "",
        percentError: null as string | null,
        formattedRange: "",
        rangeError: null as string | null,
      };
    }

    let formattedFrac = "";
    let fracWords = "";
    let fracSymbol = "";
    let fracError: string | null = null;
    try {
      const w = Number.parseInt(fracWhole || "0", 10);
      const n = Number.parseInt(fracNum, 10);
      const d = Number.parseInt(fracDen, 10);
      if (Number.isFinite(n) && Number.isFinite(d) && d > 0) {
        if (Number.isFinite(w) && w > 0) {
          formattedFrac = tt.format_mixed_fraction(
            { negative: false, whole: w, numerator: n, denominator: d },
            fracDigits
          );
          fracWords = tt.mixed_fraction_to_words(
            { negative: false, whole: w, numerator: n, denominator: d },
            fracLocale
          );
        } else {
          formattedFrac = tt.format_fraction(n, d, fracDigits);
          fracWords = tt.fraction_to_words(n, d, fracLocale);
        }
        try {
          fracSymbol = tt.fraction_symbol(n, d);
        } catch {
          fracSymbol = "";
        }
      }
    } catch (err: unknown) {
      fracError = err instanceof Error ? err.message : String(err);
    }

    let formattedPercent = "";
    let ratioStr = "";
    let percentError: string | null = null;
    try {
      if (percentInput.trim()) {
        const pct = tt.parse_percent(percentInput.trim(), "latin", "none");
        formattedPercent = tt.format_percent(pct, fracDigits, "none");
        const ratio = tt.percent_to_ratio(pct);
        ratioStr = tt.format_decimal(ratio, "latin", "none");
      }
    } catch (err: unknown) {
      percentError = err instanceof Error ? err.message : String(err);
    }

    let formattedRange = "";
    let rangeError: string | null = null;
    try {
      if (rangeStart.trim() && rangeEnd.trim()) {
        const sVal = tt.parse_decimal(rangeStart.trim(), "latin", "none");
        const eVal = tt.parse_decimal(rangeEnd.trim(), "latin", "none");
        formattedRange = tt.format_numeric_range(
          { type: "decimal", value: sVal },
          { type: "decimal", value: eVal },
          rangeStartIncl,
          rangeEndIncl,
          "–",
          fracDigits
        );
      }
    } catch (err: unknown) {
      rangeError = err instanceof Error ? err.message : String(err);
    }

    return {
      formattedFrac,
      fracWords,
      fracSymbol,
      fracError,
      formattedPercent,
      ratioStr,
      percentError,
      formattedRange,
      rangeError,
    };
  }, [
    fracWhole,
    fracNum,
    fracDen,
    fracLocale,
    fracDigits,
    percentInput,
    rangeStart,
    rangeEnd,
    rangeStartIncl,
    rangeEndIncl,
    ready,
  ]);

  // Tab 4 Computation
  const tab4Result = useMemo(() => {
    if (!ready) {
      return {
        formattedDate: "",
        weekday: "",
        dateDiff: null as number | null,
        addedDate: "",
        error: null as string | null,
      };
    }

    let formattedDate = "";
    let weekday = "";
    let dateDiff: number | null = null;
    let addedDate = "";
    let error: string | null = null;

    try {
      const p1 = dateInput.split("-").map(Number);
      if (p1.length === 3 && p1.every(Number.isFinite)) {
        const [y, m, d] = p1;
        formattedDate = tt.format_date(y, m, d, dateLocale, dateStyle, dateDigits);
        weekday = tt.weekday(y, m, d);

        const offset = Number.parseInt(addAmount, 10);
        if (Number.isFinite(offset)) {
          const next = tt.add_gregorian_date(y, m, d, addUnit, offset, "clamp");
          addedDate = `${next.year}-${String(next.month).padStart(2, "0")}-${String(next.day).padStart(2, "0")}`;
        }

        const p2 = endDateInput.split("-").map(Number);
        if (p2.length === 3 && p2.every(Number.isFinite)) {
          dateDiff = tt.date_difference(
            { year: y, month: m, day: d },
            { year: p2[0], month: p2[1], day: p2[2] }
          );
        }
      }
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : String(err);
    }

    return { formattedDate, weekday, dateDiff, addedDate, error };
  }, [dateInput, dateLocale, dateStyle, dateDigits, endDateInput, addUnit, addAmount, ready]);

  const tabSwitcher = (
    <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
      {(
        [
          { id: "currencyWords", label: t.tools.numeral.tabCurrencyWords },
          { id: "traditionalDigits", label: t.tools.numeral.tabTraditionalDigits },
          { id: "fractionsRanges", label: t.tools.numeral.tabFractionsRanges },
          { id: "datesMath", label: t.tools.numeral.tabDatesMath },
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

  const primaryCopyText =
    activeTab === "currencyWords"
      ? tab1Result.chequeWords || tab1Result.formalWords
      : activeTab === "traditionalDigits"
        ? tab2Result.formattedTrad || tab2Result.toTamilDigits
        : activeTab === "fractionsRanges"
          ? tab3Result.fracWords || tab3Result.formattedFrac
          : tab4Result.formattedDate;

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.numeral.title}
        description={t.tools.numeral.desc}
      />

      {tabSwitcher}

      {/* TAB 1: CURRENCY, PLAIN NUMBERS, ORDINALS & DIGIT SEQUENCES */}
      {activeTab === "currencyWords" && (
        <div className="space-y-5">
          <Card className="p-4 sm:p-5 space-y-4">
            {/* Row 1: Input Type */}
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
                {(
                  [
                    { id: "currency", label: t.tools.numeral.modeCurrency },
                    { id: "number", label: t.tools.numeral.modeNumber },
                    { id: "ordinal", label: t.tools.numeral.modeOrdinal },
                    { id: "digits", label: t.tools.numeral.modeDigitSeq },
                  ] as const
                ).map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setInputType(opt.id)}
                    className={`px-3 py-1.5 min-h-[34px] rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                      inputType === opt.id
                        ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                        : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Row 2: Explicit Currency (8 currencies) & Region/Dialect (TN/SL) Selectors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {inputType === "currency" && (
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-[var(--color-muted)] block">
                    {t.tools.numeral.currencyLabel}
                  </span>
                  <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                    {(
                      [
                        { code: "INR", label: "₹ INR" },
                        { code: "LKR", label: "Rs LKR" },
                        { code: "SGD", label: "S$ SGD" },
                        { code: "MYR", label: "RM MYR" },
                        { code: "USD", label: "$ USD" },
                        { code: "EUR", label: "€ EUR" },
                        { code: "GBP", label: "£ GBP" },
                        { code: "CAD", label: "C$ CAD" },
                      ] as const
                    ).map((c) => (
                      <button
                        key={c.code}
                        type="button"
                        onClick={() => setCurrency(c.code)}
                        className={`px-2 py-1.5 min-h-[34px] rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                          currency === c.code
                            ? "bg-[var(--color-semman)] text-[#faf7f2]"
                            : "text-[var(--color-mai)] hover:bg-[var(--bg-raised)]"
                        }`}
                      >
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className={`space-y-1.5 ${inputType !== "currency" ? "sm:col-span-2 max-w-md" : ""}`}>
                <span className="text-xs font-semibold text-[var(--color-muted)] block">
                  {t.tools.numeral.regionLabel}
                </span>
                <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                  <button
                    type="button"
                    onClick={() => setRegion("TN")}
                    className={`px-3 py-2 min-h-[38px] rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                      region === "TN"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-mai)] hover:bg-[var(--bg-raised)]"
                    }`}
                  >
                    {t.tools.numeral.localeTN}
                  </button>
                  <button
                    type="button"
                    onClick={() => setRegion("SL")}
                    className={`px-3 py-2 min-h-[38px] rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                      region === "SL"
                        ? "bg-[var(--color-semman)] text-[#faf7f2]"
                        : "text-[var(--color-mai)] hover:bg-[var(--bg-raised)]"
                    }`}
                  >
                    {t.tools.numeral.localeSL}
                  </button>
                </div>
              </div>
            </div>

            {/* Row 3: Amount / Number Input */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label htmlFor="numeral-amount-input" className="text-xs font-semibold text-[var(--color-mai)]">
                  {t.tools.numeral.inputLabel}
                </label>
                {tab1Result.formattedDisplay && (
                  <span className="text-xs font-mono-tamil text-[var(--color-semman)] font-semibold">
                    {tab1Result.formattedDisplay}
                  </span>
                )}
              </div>

              <div className="relative">
                <input
                  id="numeral-amount-input"
                  type="text"
                  inputMode="decimal"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={t.tools.numeral.inputPlaceholder}
                  className="w-full rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] px-4 pr-10 py-3 text-xl font-mono-tamil font-semibold text-[var(--color-mai)] focus-visible:outline-none focus-visible:border-[var(--color-semman)] focus-visible:ring-1 focus-visible:ring-[var(--color-semman)] min-h-[52px]"
                />
                {input && (
                  <button
                    type="button"
                    onClick={() => setInput("")}
                    aria-label={t.actions.clear}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-[var(--color-muted)] hover:text-[var(--color-mai)] hover:bg-[var(--bg-raised)] cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Digit & Grouping Controls + Quick Presets */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputType("currency");
                      setCurrency("INR");
                      setRegion("TN");
                      setSourceDigits("latin");
                      setInput("125000");
                    }}
                    className="text-xs font-mono-tamil"
                  >
                    TN · ₹1,25,000
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputType("currency");
                      setCurrency("LKR");
                      setRegion("SL");
                      setSourceDigits("latin");
                      setInput("125000");
                    }}
                    className="text-xs font-mono-tamil"
                  >
                    SL · Rs 1,25,000
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputType("currency");
                      setCurrency("LKR");
                      setRegion("SL");
                      setSourceDigits("latin");
                      setInput("750.50");
                    }}
                    className="text-xs font-mono-tamil"
                  >
                    SL · Rs 750.50
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputType("currency");
                      setCurrency("SGD");
                      setRegion("TN");
                      setSourceDigits("latin");
                      setInput("1250.50");
                    }}
                    className="text-xs font-mono-tamil"
                  >
                    SG · S$1,250.50
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setInputType("number");
                      setSourceDigits("tamil");
                      setInput("௨௦௨௬");
                    }}
                    className="text-xs font-tamil"
                  >
                    ௨௦௨௬
                  </Button>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setSourceDigits((d) => (d === "latin" ? "tamil" : "latin"))}
                    className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] hover:border-[var(--color-semman)] cursor-pointer"
                  >
                    {t.tools.numeral.inputDigitsLabel}:{" "}
                    <strong>{sourceDigits === "latin" ? "0–9" : "௦–௯"}</strong>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOutputDigits((d) => (d === "latin" ? "tamil" : "latin"))}
                    className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-mai)] hover:border-[var(--color-semman)] cursor-pointer"
                  >
                    {t.tools.numeral.outputDigitsLabel}:{" "}
                    <strong>{outputDigits === "latin" ? "0–9" : "௦–௯"}</strong>
                  </button>
                  {(inputType === "currency" || inputType === "number") && (
                    <button
                      type="button"
                      onClick={() => setGrouping((g) => (g === "indian" ? "none" : "indian"))}
                      className={`px-2.5 py-1 rounded-lg border cursor-pointer ${
                        grouping === "indian"
                          ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold"
                          : "border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-muted)]"
                      }`}
                    >
                      {t.tools.numeral.groupingToggle}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </Card>

          {tab1Result.error && (
            <Card className="p-4 border-red-500/40 bg-red-500/10 text-xs text-red-700 dark:text-red-300">
              {tab1Result.error}
            </Card>
          )}

          {/* Hero Result Card */}
          <Card className="p-5 sm:p-6 border-l-4 border-l-[var(--color-semman)] space-y-2.5">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-[var(--color-semman)] uppercase tracking-wider">
                  {inputType === "currency"
                    ? t.tools.numeral.chequeWordsLabel
                    : t.tools.numeral.resultWordsLabel}
                </span>
                <Badge variant="outline" className="text-[11px]">
                  {inputType === "currency" ? `${currency} · ${region}` : region}
                </Badge>
              </div>
              {(tab1Result.chequeWords || tab1Result.formalWords) && (
                <CopyButton
                  text={
                    inputType === "currency"
                      ? tab1Result.chequeWords
                      : tab1Result.formalWords
                  }
                  size="sm"
                  variant="outline"
                />
              )}
            </div>
            <p className="text-xl sm:text-2xl font-tamil font-semibold text-[var(--color-mai)] leading-relaxed">
              {(inputType === "currency" ? tab1Result.chequeWords : tab1Result.formalWords) || "—"}
            </p>
          </Card>

          {/* Secondary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {inputType === "currency" && (
              <Card className="p-4 sm:p-5 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
                    {t.tools.numeral.formalWordsLabel}
                  </span>
                  {tab1Result.formalWords && (
                    <CopyButton text={tab1Result.formalWords} size="sm" variant="ghost" />
                  )}
                </div>
                <p className="text-base sm:text-lg font-tamil font-medium text-[var(--color-mai)] leading-relaxed">
                  {tab1Result.formalWords || "—"}
                </p>
              </Card>
            )}

            {tab1Result.spokenWords && (
              <Card className="p-4 sm:p-5 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
                    {t.tools.numeral.spokenVariantBadge}
                  </span>
                  <CopyButton text={tab1Result.spokenWords} size="sm" variant="ghost" />
                </div>
                <p className="text-base sm:text-lg font-tamil text-[var(--color-mai)] leading-relaxed">
                  {tab1Result.spokenWords}
                </p>
              </Card>
            )}

            {tab1Result.traditionalSymbols && (
              <Card className="p-4 sm:p-5 space-y-2 md:col-span-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
                    {t.tools.numeral.traditionalSymbolsLabel}
                  </span>
                  <CopyButton text={tab1Result.traditionalSymbols} size="sm" variant="ghost" />
                </div>
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-2 pt-1">
                  <p className="text-3xl font-tamil font-bold text-[var(--color-semman)] tracking-widest select-all">
                    {tab1Result.traditionalSymbols}
                  </p>
                  <span className="text-xs text-[var(--color-muted)]">
                    {t.tools.numeral.classicalNotationHeading}
                  </span>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: TRADITIONAL TAMIL INTEGERS & DIGIT CONVERTER */}
      {activeTab === "traditionalDigits" && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Arabic -> Traditional */}
            <Card className="p-5 space-y-3">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.numeral.tradFormatHeading}
              </h2>
              <div className="space-y-1.5">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.tradInputLabel}
                </label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={tradIntInput}
                  onChange={(e) => setTradIntInput(e.target.value)}
                  className="w-full min-h-[42px] px-3 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-base text-[var(--color-mai)]"
                />
              </div>
              {tab2Result.tradError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{tab2Result.tradError}</p>
              ) : (
                <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3">
                  <span className="text-3xl font-tamil font-bold text-[var(--color-semman)] select-all">
                    {tab2Result.formattedTrad || "—"}
                  </span>
                  {tab2Result.formattedTrad && (
                    <CopyButton text={tab2Result.formattedTrad} size="sm" variant="outline" />
                  )}
                </div>
              )}
            </Card>

            {/* Traditional -> Arabic */}
            <Card className="p-5 space-y-3">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.numeral.tradParseHeading}
              </h2>
              <div className="space-y-1.5">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.tradSymbolsInputLabel}
                </label>
                <input
                  type="text"
                  value={tradParseInput}
                  onChange={(e) => setTradParseInput(e.target.value)}
                  placeholder={t.tools.numeral.tradParsePlaceholder}
                  className="w-full min-h-[42px] px-3 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-lg text-[var(--color-mai)]"
                />
              </div>
              <div className="flex flex-wrap gap-1.5">
                {["௰", "௱", "௲", "௲௨௱௫௰"].map((sym) => (
                  <button
                    key={sym}
                    type="button"
                    onClick={() => setTradParseInput(sym)}
                    className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-raised)] text-sm font-tamil hover:border-[var(--color-semman)] cursor-pointer"
                  >
                    {sym}
                  </button>
                ))}
              </div>
              {tab2Result.parseError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{tab2Result.parseError}</p>
              ) : (
                <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3">
                  <span className="text-2xl font-mono-tamil font-bold text-[var(--color-mai)]">
                    {tab2Result.parsedArabic || "—"}
                  </span>
                  {tab2Result.parsedArabic && (
                    <CopyButton text={tab2Result.parsedArabic} size="sm" variant="outline" />
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Tamil Words -> Number (ITN) */}
          <Card className="p-5 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.numeral.itnHeading}
              </h2>
              <div className="inline-flex items-center gap-1 p-1 rounded-lg bg-[var(--bg-raised)] border border-[var(--border-line)]">
                {(["TN", "SL"] as const).map((loc) => (
                  <button
                    key={loc}
                    type="button"
                    onClick={() => {
                      setItnLocale(loc);
                      if (ready && itnInput.trim()) {
                        try {
                          const parsed = tt.words_to_number(itnInput.trim(), itnLocale);
                          setItnInput(tt.to_words(parsed, loc));
                        } catch {
                          // keep user input as-is
                        }
                      }
                    }}
                    className={`px-2.5 py-1 rounded text-xs font-medium cursor-pointer ${
                      itnLocale === loc
                        ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                        : "text-[var(--color-muted)]"
                    }`}
                  >
                    {loc}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-[var(--color-muted)] block">
                {t.tools.numeral.itnInputLabel}
              </label>
              <input
                type="text"
                value={itnInput}
                onChange={(e) => setItnInput(e.target.value)}
                placeholder={t.tools.numeral.itnPlaceholder}
                className="w-full min-h-[42px] px-3 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-base text-[var(--color-mai)]"
              />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {(ready
                ? [123, 25, 250000].map((n) => tt.to_words(n, itnLocale))
                : ["நூற்று இருபத்து மூன்று"]
              ).map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => setItnInput(sample)}
                  className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-raised)] text-xs font-tamil hover:border-[var(--color-semman)] cursor-pointer"
                >
                  {sample}
                </button>
              ))}
            </div>
            {tab2Result.itnError ? (
              <p className="text-xs text-red-600 dark:text-red-400">{tab2Result.itnError}</p>
            ) : (
              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between gap-3">
                <span className="text-2xl font-mono-tamil font-bold text-[var(--color-semman)]">
                  {tab2Result.itnNumber || "—"}
                </span>
                {tab2Result.itnNumber && (
                  <CopyButton text={tab2Result.itnNumber} size="sm" variant="outline" />
                )}
              </div>
            )}
          </Card>

          {/* Digit Script Converter */}
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.numeral.digitScriptHeading}
            </h2>
            <input
              type="text"
              value={digitScriptText}
              onChange={(e) => setDigitScriptText(e.target.value)}
              placeholder={t.tools.numeral.digitScriptInputPlaceholder}
              className="w-full min-h-[44px] px-3.5 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-tamil text-base text-[var(--color-mai)]"
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--color-muted)]">
                    {t.tools.numeral.convertToTamil}
                  </span>
                  <CopyButton text={tab2Result.toTamilDigits} size="sm" variant="ghost" />
                </div>
                <p className="font-tamil text-lg text-[var(--color-mai)]">
                  {tab2Result.toTamilDigits || "—"}
                </p>
              </div>
              <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--color-muted)]">
                    {t.tools.numeral.convertToLatin}
                  </span>
                  <CopyButton text={tab2Result.toLatinDigits} size="sm" variant="ghost" />
                </div>
                <p className="font-tamil text-lg text-[var(--color-mai)]">
                  {tab2Result.toLatinDigits || "—"}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 3: FRACTIONS, PERCENTAGES & NUMERIC RANGES */}
      {activeTab === "fractionsRanges" && (
        <div className="space-y-5">
          {/* Shared TN/SL & Digit Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
              {(["TN", "SL"] as const).map((loc) => (
                <button
                  key={loc}
                  type="button"
                  onClick={() => setFracLocale(loc)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer ${
                    fracLocale === loc
                      ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                      : "text-[var(--color-muted)]"
                  }`}
                >
                  {loc === "TN" ? t.tools.numeral.localeTN : t.tools.numeral.localeSL}
                </button>
              ))}
            </div>
            <div className="inline-flex items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
              {(["latin", "tamil"] as const).map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setFracDigits(d)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer ${
                    fracDigits === d
                      ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                      : "text-[var(--color-muted)]"
                  }`}
                >
                  {d === "latin" ? t.tools.numeral.digitsLatin : t.tools.numeral.digitsTamil}
                </button>
              ))}
            </div>
          </div>

          {/* Fraction Calculator */}
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.numeral.fractionCalcHeading}
            </h2>
            <div className="grid grid-cols-3 gap-3 max-w-md">
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.wholeLabel}
                </label>
                <input
                  type="number"
                  min="0"
                  value={fracWhole}
                  onChange={(e) => setFracWhole(e.target.value)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.numeratorLabel}
                </label>
                <input
                  type="number"
                  min="0"
                  value={fracNum}
                  onChange={(e) => setFracNum(e.target.value)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.denominatorLabel}
                </label>
                <input
                  type="number"
                  min="1"
                  value={fracDen}
                  onChange={(e) => setFracDen(e.target.value)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {[
                { label: "3/4", w: "0", n: "3", d: "4" },
                { label: "1 1/2 (ஒன்றரை)", w: "1", n: "1", d: "2" },
                { label: "1 1/4 (ஒன்றேகால்)", w: "1", n: "1", d: "4" },
                { label: "2 3/4 (இரண்டேமுக்கால்)", w: "2", n: "3", d: "4" },
              ].map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  onClick={() => {
                    setFracWhole(preset.w);
                    setFracNum(preset.n);
                    setFracDen(preset.d);
                  }}
                  className="px-2.5 py-1 rounded-lg border border-[var(--border-line)] bg-[var(--bg-raised)] text-xs font-tamil hover:border-[var(--color-semman)] cursor-pointer"
                >
                  {preset.label}
                </button>
              ))}
            </div>

            {tab3Result.fracError ? (
              <p className="text-xs text-red-600 dark:text-red-400">{tab3Result.fracError}</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                  <span className="text-[11px] text-[var(--color-muted)] block">
                    {t.tools.numeral.formattedAmountLabel}
                  </span>
                  <span className="text-xl font-tamil font-bold text-[var(--color-mai)]">
                    {tab3Result.formattedFrac || "—"}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                  <span className="text-[11px] text-[var(--color-muted)] block">
                    {t.tools.numeral.fractionWordsLabel}
                  </span>
                  <span className="text-base font-tamil font-semibold text-[var(--color-semman)]">
                    {tab3Result.fracWords || "—"}
                  </span>
                </div>
                <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)]">
                  <span className="text-[11px] text-[var(--color-muted)] block">
                    {t.tools.numeral.fractionSymbolLabel}
                  </span>
                  <span className="text-2xl font-tamil text-[var(--color-mai)]">
                    {tab3Result.fracSymbol || "—"}
                  </span>
                </div>
              </div>
            )}
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Percentage & Ratio */}
            <Card className="p-5 space-y-3">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.numeral.percentHeading}
              </h2>
              <input
                type="text"
                value={percentInput}
                onChange={(e) => setPercentInput(e.target.value)}
                placeholder={t.tools.numeral.percentInputLabel}
                className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
              />
              {tab3Result.percentError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{tab3Result.percentError}</p>
              ) : (
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] text-sm">
                  <span className="font-tamil font-bold text-[var(--color-semman)]">
                    {tab3Result.formattedPercent || "—"}
                  </span>
                  <span className="text-xs font-mono-tamil text-[var(--color-muted)]">
                    {t.tools.numeral.percentRatioLabel}: {tab3Result.ratioStr || "—"}
                  </span>
                </div>
              )}
            </Card>

            {/* Range Formatter */}
            <Card className="p-5 space-y-3">
              <h2 className="text-sm font-bold text-[var(--color-mai)]">
                {t.tools.numeral.rangeHeading}
              </h2>
              <div className="grid grid-cols-2 gap-2.5">
                <input
                  type="text"
                  value={rangeStart}
                  onChange={(e) => setRangeStart(e.target.value)}
                  placeholder={t.tools.numeral.rangeStartLabel}
                  className="min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
                <input
                  type="text"
                  value={rangeEnd}
                  onChange={(e) => setRangeEnd(e.target.value)}
                  placeholder={t.tools.numeral.rangeEndLabel}
                  className="min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
              </div>
              <div className="flex flex-wrap gap-3 text-xs">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rangeStartIncl}
                    onChange={(e) => setRangeStartIncl(e.target.checked)}
                    className="accent-[var(--color-semman)]"
                  />
                  <span>{t.tools.numeral.rangeStartIncl}</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rangeEndIncl}
                    onChange={(e) => setRangeEndIncl(e.target.checked)}
                    className="accent-[var(--color-semman)]"
                  />
                  <span>{t.tools.numeral.rangeEndIncl}</span>
                </label>
              </div>
              {tab3Result.rangeError ? (
                <p className="text-xs text-red-600 dark:text-red-400">{tab3Result.rangeError}</p>
              ) : (
                <div className="p-3 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex items-center justify-between">
                  <span className="font-tamil text-base font-bold text-[var(--color-mai)]">
                    {tab3Result.formattedRange || "—"}
                  </span>
                  {tab3Result.formattedRange && (
                    <CopyButton text={tab3Result.formattedRange} size="sm" variant="ghost" />
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* TAB 4: TAMIL DATES & DATE MATH */}
      {activeTab === "datesMath" && (
        <div className="space-y-5">
          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.numeral.dateFormatHeading}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.startDateLabel}
                </label>
                <input
                  type="date"
                  value={dateInput}
                  onChange={(e) => setDateInput(e.target.value)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] font-mono-tamil text-sm"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.regionLabel}
                </label>
                <select
                  value={dateLocale}
                  onChange={(e) => setDateLocale(e.target.value as tt.Locale)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm"
                >
                  <option value="TN">{t.tools.numeral.localeTN}</option>
                  <option value="SL">{t.tools.numeral.localeSL}</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.dateStyleLabel}
                </label>
                <select
                  value={dateStyle}
                  onChange={(e) => setDateStyle(e.target.value as tt.DateStyle)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm"
                >
                  <option value="short">{t.tools.numeral.styleShort}</option>
                  <option value="medium">{t.tools.numeral.styleMedium}</option>
                  <option value="long">{t.tools.numeral.styleLong}</option>
                  <option value="full">{t.tools.numeral.styleFull}</option>
                </select>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-[var(--color-muted)] block">
                  {t.tools.numeral.outputDigitsLabel}
                </label>
                <select
                  value={dateDigits}
                  onChange={(e) => setDateDigits(e.target.value as tt.DigitStyle)}
                  className="w-full min-h-[40px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] text-sm"
                >
                  <option value="latin">{t.tools.numeral.digitsLatin}</option>
                  <option value="tamil">{t.tools.numeral.digitsTamil}</option>
                </select>
              </div>
            </div>

            {tab4Result.error ? (
              <p className="text-xs text-red-600 dark:text-red-400">{tab4Result.error}</p>
            ) : (
              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xl font-tamil font-bold text-[var(--color-mai)]">
                    {tab4Result.formattedDate || "—"}
                  </p>
                  {tab4Result.weekday && (
                    <span className="text-xs text-[var(--color-muted)]">
                      {t.tools.numeral.weekdayLabel}: {tab4Result.weekday}
                    </span>
                  )}
                </div>
                {tab4Result.formattedDate && (
                  <CopyButton text={tab4Result.formattedDate} size="sm" variant="outline" />
                )}
              </div>
            )}
          </Card>

          <Card className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-[var(--color-mai)]">
              {t.tools.numeral.dateMathHeading}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2.5">
                <label className="text-xs font-semibold text-[var(--color-mai)] block">
                  {t.tools.numeral.endDateLabel}
                </label>
                <input
                  type="date"
                  value={endDateInput}
                  onChange={(e) => setEndDateInput(e.target.value)}
                  className="w-full min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] font-mono-tamil text-sm"
                />
                <div className="text-sm text-[var(--color-mai)] pt-1">
                  {t.tools.numeral.dateDifferenceLabel}:{" "}
                  <strong className="font-mono-tamil text-[var(--color-semman)]">
                    {tab4Result.dateDiff !== null ? `${tab4Result.dateDiff} ${t.tools.numeral.daysSuffix}` : "—"}
                  </strong>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2.5">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-[var(--color-muted)] block mb-1">
                      {t.tools.numeral.addAmountLabel}
                    </label>
                    <input
                      type="number"
                      value={addAmount}
                      onChange={(e) => setAddAmount(e.target.value)}
                      className="w-full min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] font-mono-tamil text-sm"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-[var(--color-muted)] block mb-1">
                      {t.tools.numeral.addUnitLabel}
                    </label>
                    <select
                      value={addUnit}
                      onChange={(e) => setAddUnit(e.target.value as "days" | "months" | "years")}
                      className="w-full min-h-[38px] px-3 py-1.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-sm"
                    >
                      <option value="days">{t.tools.numeral.unitDays}</option>
                      <option value="months">{t.tools.numeral.unitMonths}</option>
                      <option value="years">{t.tools.numeral.unitYears}</option>
                    </select>
                  </div>
                </div>
                <div className="text-sm text-[var(--color-mai)] pt-1">
                  {t.tools.numeral.resultingDateLabel}:{" "}
                  <strong className="font-mono-tamil text-[var(--color-semman)]">
                    {tab4Result.addedDate || "—"}
                  </strong>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      <StickyActionBar
        outputText={primaryCopyText}
        onClear={() => setInput("")}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
      />
    </div>
  );
}
