import { useState, useTransition } from "react";
import { tt } from "../../lib/engine";
import { useLanguage } from "../../lib/i18n";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Sparkles, Banknote } from "lucide-react";

export function NumeralFormatter() {
  const { t } = useLanguage();
  const [, startTransition] = useTransition();

  const [input, setInput] = useState("125000");
  const [isCurrency, setIsCurrency] = useState(true);

  // Formatted outputs
  const [formalWords, setFormalWords] = useState("");
  const [chequeWords, setChequeWords] = useState("");
  const [spokenWords, setSpokenWords] = useState("");
  const [traditionalSymbols, setTraditionalSymbols] = useState("");
  const [latency, setLatency] = useState(0);

  const formatNumber = (val: string, currency: boolean) => {
    const clean = val.trim();
    if (!clean) {
      setFormalWords("");
      setChequeWords("");
      setSpokenWords("");
      setTraditionalSymbols("");
      setLatency(0);
      return;
    }

    const t0 = performance.now();
    try {
      const num = parseFloat(clean);
      if (isNaN(num)) return;

      if (currency) {
        // Currency words (amount in minor units: paise for INR)
        const minorUnits = Math.round(num * 100);
        const words = tt.currency_to_words(minorUnits, "INR", "TN");
        setFormalWords(words);
        setChequeWords(`${words} மட்டும்`);
        setSpokenWords(words.replace("ரூபாய்", "ரூபா").replace("இலட்சத்து", "லட்சத்து"));
      } else {
        // Standard integer/decimal words
        const words = tt.to_words(num);
        setFormalWords(words);
        setChequeWords(`${words} மட்டும்`);
        setSpokenWords(words.replace("இலட்சத்து", "லட்சத்து"));
      }

      // Traditional numeral symbols (integers)
      if (Number.isInteger(num) && num > 0 && num <= 1000000) {
        try {
          const trad = tt.format_traditional_integer(Math.floor(num));
          setTraditionalSymbols(trad || "");
        } catch {
          setTraditionalSymbols("");
        }
      } else {
        setTraditionalSymbols("");
      }
    } catch (err) {
      console.error("Numeral formatting error:", err);
    } finally {
      setLatency(performance.now() - t0);
    }
  };

  const handleInputChange = (val: string) => {
    setInput(val);
    startTransition(() => {
      formatNumber(val, isCurrency);
    });
  };

  const handleToggleCurrency = () => {
    const next = !isCurrency;
    setIsCurrency(next);
    startTransition(() => {
      formatNumber(input, next);
    });
  };

  const handleClear = () => {
    setInput("");
    setFormalWords("");
    setChequeWords("");
    setSpokenWords("");
    setTraditionalSymbols("");
    setLatency(0);
  };

  const handleSample = (val: string) => {
    setInput(val);
    startTransition(() => {
      formatNumber(val, isCurrency);
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.numeral.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.numeral.desc}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSample("125000")}
            className="text-xs font-tamil text-[var(--color-semman)] border-[var(--color-semman)]/30"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1 text-[var(--color-sandhanam)]" />
            <span>₹1,25,000</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSample("750.50")}
            className="text-xs font-tamil"
          >
            <span>₹750.50</span>
          </Button>
        </div>
      </div>

      {/* Input & Options */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold text-[var(--color-mai)] font-tamil">
            {t.tools.numeral.inputLabel}
          </label>
          {latency > 0 && <Badge variant="mono">{latency.toFixed(1)} ms</Badge>}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            placeholder={t.tools.numeral.inputPlaceholder}
            className="flex-1 rounded-xl border border-[var(--border-line)] bg-[var(--bg-canvas)] px-4 py-3 text-lg font-tamil text-[var(--color-mai)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] min-h-[48px]"
          />

          <Button
            variant={isCurrency ? "primary" : "outline"}
            size="md"
            onClick={handleToggleCurrency}
            className="font-tamil whitespace-nowrap min-h-[48px]"
          >
            <Banknote className="w-4 h-4 mr-1.5" />
            <span>{t.tools.numeral.currencyToggle}</span>
          </Button>
        </div>
      </div>

      {/* Results Display Cards */}
      <div className="grid grid-cols-1 gap-4 pt-2">
        {/* Formal Words */}
        <Card className="bg-[var(--bg-surface)]">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil uppercase tracking-wide">
              {t.tools.numeral.formalWordsLabel}
            </span>
            {formalWords && <CopyButton text={formalWords} size="sm" variant="ghost" />}
          </div>
          <p className="text-lg sm:text-xl font-tamil font-semibold text-[var(--color-mai)] leading-relaxed">
            {formalWords || "—"}
          </p>
        </Card>

        {/* Cheque Format */}
        <Card className="bg-[var(--bg-surface)] border-l-4 border-l-[var(--color-semman)]">
          <div className="flex items-center justify-between pb-2">
            <span className="text-xs font-semibold text-[var(--color-semman)] font-tamil uppercase tracking-wide">
              {t.tools.numeral.chequeWordsLabel}
            </span>
            {chequeWords && <CopyButton text={chequeWords} size="sm" variant="ghost" />}
          </div>
          <p className="text-base sm:text-lg font-tamil font-medium text-[var(--color-mai)] leading-relaxed">
            {chequeWords || "—"}
          </p>
        </Card>

        {/* Spoken Tamil Format */}
        {spokenWords && (
          <Card className="bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil uppercase tracking-wide">
                {t.tools.numeral.spokenVariantBadge}
              </span>
              <CopyButton text={spokenWords} size="sm" variant="ghost" />
            </div>
            <p className="text-base sm:text-lg font-tamil text-[var(--color-mai)] leading-relaxed">
              {spokenWords}
            </p>
          </Card>
        )}

        {/* Traditional Tamil Numeral Symbols */}
        {traditionalSymbols && (
          <Card className="bg-[var(--bg-surface)] border-2 border-[var(--color-sandhanam)] shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-line)]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--color-sandhanam)]"></span>
                <span className="text-xs font-bold text-[var(--color-mai)] font-tamil uppercase tracking-wide">
                  {t.tools.numeral.traditionalSymbolsLabel}
                </span>
                <Badge variant="sandhanam">
                  {t.tools.numeral.classicalTamilBadge}
                </Badge>
              </div>
              <CopyButton text={traditionalSymbols} size="sm" variant="outline" />
            </div>
            <div className="mt-3 p-4 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)] flex flex-col sm:flex-row sm:items-baseline justify-between gap-2">
              <p className="text-3xl sm:text-4xl font-tamil font-extrabold text-[var(--color-semman)] tracking-widest select-all">
                {traditionalSymbols}
              </p>
              <span className="text-xs font-tamil text-[var(--color-muted)]">
                {t.tools.numeral.classicalNotationHeading}
              </span>
            </div>
          </Card>
        )}
      </div>

      <StickyActionBar
        outputText={chequeWords || formalWords}
        onClear={handleClear}
        copyLabel={t.actions.copy}
        copiedLabel={t.actions.copied}
        clearLabel={t.actions.clear}
      />
    </div>
  );
}
