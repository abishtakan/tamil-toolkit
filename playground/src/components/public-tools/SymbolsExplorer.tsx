import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import { isEngineReady, TRADITIONAL_SYMBOLS, TraditionalSymbol, tt } from "../../lib/engine";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Search, Compass, BookOpen, Layers, Sparkles, X } from "lucide-react";

export function SymbolsExplorer() {
  const { t, language } = useLanguage();
  const ready = isEngineReady();
  const [selectedCategory, setSelectedCategory] = useState<"all" | "fraction" | "land" | "volume" | "currency">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<TraditionalSymbol>(TRADITIONAL_SYMBOLS[0]);

  const [inspectInput, setInspectInput] = useState("௳");
  const [fracNumerator, setFracNumerator] = useState("3");
  const [fracDenominator, setFracDenominator] = useState("4");
  const [fracLocale, setFracLocale] = useState<"TN" | "SL">("TN");

  const liveInspect = useMemo(() => {
    if (!ready || !inspectInput.trim()) return null;
    try {
      const symbolChar = Array.from(inspectInput.trim())[0];
      const info = tt.symbol_info(symbolChar);
      let fractionWords: string | null = null;
      if (info?.rational) {
        fractionWords = tt.fraction_to_words(
          info.rational.numerator,
          info.rational.denominator,
          fracLocale
        );
      } else {
        try {
          const parsed = tt.parse_fraction_symbol(symbolChar);
          if (parsed) {
            fractionWords = tt.fraction_to_words(parsed.numerator, parsed.denominator, fracLocale);
          }
        } catch {
          // Not a fraction symbol
        }
      }
      return { symbolChar, info, fractionWords };
    } catch {
      return null;
    }
  }, [inspectInput, fracLocale, ready]);

  const liveFraction = useMemo(() => {
    if (!ready) return null;
    const num = Number.parseInt(fracNumerator, 10);
    const den = Number.parseInt(fracDenominator, 10);
    if (!Number.isFinite(num) || !Number.isFinite(den) || den <= 0) {
      return null;
    }
    try {
      const glyph = tt.fraction_symbol(num, den);
      const words = tt.fraction_to_words(num, den, fracLocale);
      return { glyph, words };
    } catch {
      try {
        const words = tt.fraction_to_words(num, den, fracLocale);
        return { glyph: "", words };
      } catch {
        return null;
      }
    }
  }, [fracNumerator, fracDenominator, fracLocale, ready]);

  const filteredSymbols = useMemo(() => {
    return TRADITIONAL_SYMBOLS.filter((sym) => {
      const matchesCategory = selectedCategory === "all" || sym.category === selectedCategory;
      if (!matchesCategory) return false;

      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase().trim();

      const matchesGlyph = sym.glyph.includes(q);
      const matchesNameTa = sym.name_ta.toLowerCase().includes(q);
      const matchesNameEn = sym.name_en.toLowerCase().includes(q);
      const matchesCodepoint = sym.codepoint.toLowerCase().includes(q);
      const matchesRational = sym.rational ? `${sym.rational.numerator}/${sym.rational.denominator}`.includes(q) : false;
      const matchesDecimal = sym.decimal_value !== null ? String(sym.decimal_value).includes(q) : false;

      return matchesGlyph || matchesNameTa || matchesNameEn || matchesCodepoint || matchesRational || matchesDecimal;
    });
  }, [selectedCategory, searchQuery]);

  const categories = [
    { id: "all", label: t.tools.symbols.categoryAll },
    { id: "fraction", label: t.tools.symbols.categoryFractions },
    { id: "land", label: t.tools.symbols.categoryLand },
    { id: "volume", label: t.tools.symbols.categoryVolume },
    { id: "currency", label: t.tools.symbols.categoryCurrency },
  ] as const;

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.symbols.title}
        description={t.tools.symbols.desc}
        actions={
          <CopyButton
            text={selectedSymbol.glyph}
            label={`${t.tools.symbols.copySymbolButton} (${selectedSymbol.glyph})`}
            size="sm"
          />
        }
      />

      {/* Live Rust Symbol Inspector & Fraction Builder */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-line)] pb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--color-semman)]" />
            <h2 className="text-sm font-semibold text-[var(--color-mai)]">
              {t.tools.symbols.liveCalcHeading}
            </h2>
          </div>
          <div className="inline-flex rounded-lg border border-[var(--border-line)] p-0.5 bg-[var(--bg-canvas)]">
            {(["TN", "SL"] as const).map((loc) => (
              <button
                key={loc}
                type="button"
                onClick={() => setFracLocale(loc)}
                className={`px-2.5 py-0.5 rounded-md text-xs font-medium cursor-pointer ${
                  fracLocale === loc
                    ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold"
                    : "text-[var(--color-muted)]"
                }`}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2.5">
            <label htmlFor="symbol-live-inspect" className="text-xs font-medium text-[var(--color-muted)] block">
              {t.tools.symbols.inspectAnySymbolLabel}
            </label>
            <div className="flex items-center gap-2">
              <input
                id="symbol-live-inspect"
                type="text"
                value={inspectInput}
                onChange={(e) => setInspectInput(e.target.value)}
                placeholder={t.tools.symbols.inspectAnyPlaceholder}
                className="w-24 px-3 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] text-2xl font-tamil text-center text-[var(--color-mai)] focus:border-[var(--color-semman)] focus:outline-none"
              />
              {liveInspect && (
                <div className="flex-1 min-w-0 text-xs space-y-0.5">
                  <div className="font-semibold text-[var(--color-mai)] truncate">
                    {liveInspect.info.name}
                  </div>
                  <div className="font-mono-tamil text-[11px] text-[var(--color-muted)]">
                    U+{liveInspect.info.codepoint.toString(16).toUpperCase().padStart(4, "0")} · {liveInspect.info.kind} · {liveInspect.info.source_version}
                  </div>
                  {liveInspect.fractionWords && (
                    <div className="font-tamil text-[var(--color-semman)] font-medium">
                      {liveInspect.fractionWords}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] space-y-2.5">
            <span className="text-xs font-medium text-[var(--color-muted)] block">
              {t.tools.symbols.fractionBuilderLabel}
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <input
                type="number"
                min={1}
                value={fracNumerator}
                onChange={(e) => setFracNumerator(e.target.value)}
                aria-label="Fraction numerator"
                className="w-16 px-2.5 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] font-mono-tamil text-sm text-[var(--color-mai)]"
              />
              <span className="text-[var(--color-muted)] font-bold">/</span>
              <input
                type="number"
                min={1}
                value={fracDenominator}
                onChange={(e) => setFracDenominator(e.target.value)}
                aria-label="Fraction denominator"
                className="w-16 px-2.5 py-1.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-surface)] font-mono-tamil text-sm text-[var(--color-mai)]"
              />
              {liveFraction && (
                <div className="flex-1 flex items-center justify-between gap-2 min-w-0 pl-2">
                  <div className="min-w-0">
                    {liveFraction.glyph && (
                      <span className="text-2xl font-tamil text-[var(--color-semman)] mr-2 align-middle">
                        {liveFraction.glyph}
                      </span>
                    )}
                    <span className="text-xs font-tamil font-semibold text-[var(--color-mai)]">
                      {liveFraction.words}
                    </span>
                  </div>
                  {liveFraction.glyph && (
                    <CopyButton text={liveFraction.glyph} size="sm" variant="outline" />
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Search & Category Pills */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)] pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t.tools.symbols.searchPlaceholder}
            aria-label={t.tools.symbols.searchPlaceholder}
            className="w-full min-h-[42px] pl-10 pr-9 py-2 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-sm text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)]"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              aria-label={t.actions.clear}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-md text-[var(--color-muted)] hover:text-[var(--color-mai)] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 min-h-[36px] rounded-xl text-xs font-medium whitespace-nowrap transition-colors border cursor-pointer ${
                selectedCategory === cat.id
                  ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                  : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Catalog List (Left) + Detail Inspector (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7 space-y-2.5">
          <div className="text-xs text-[var(--color-muted)] px-1">
            {language === "ta" ? "கிடைத்துள்ள குறியீடுகள்:" : "Available Glyphs:"}{" "}
            <strong className="text-[var(--color-mai)] font-semibold">{filteredSymbols.length}</strong>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2.5 max-h-[500px] overflow-y-auto p-3 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)]">
            {filteredSymbols.map((sym) => {
              const isSelected = selectedSymbol.glyph === sym.glyph;
              return (
                <button
                  key={sym.codepoint}
                  type="button"
                  onClick={() => setSelectedSymbol(sym)}
                  className={`p-3 rounded-xl border text-center transition-colors flex flex-col items-center justify-between min-h-[90px] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] ${
                    isSelected
                      ? "border-[var(--color-semman)] bg-[var(--color-semman-light)] text-[var(--color-semman)]"
                      : "border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)]/50 text-[var(--color-mai)]"
                  }`}
                >
                  <span className="text-2xl sm:text-3xl font-tamil font-normal py-1">
                    {sym.glyph}
                  </span>
                  <div className="space-y-0.5 w-full truncate">
                    <p className="text-[11px] font-medium truncate">
                      {language === "ta" ? sym.name_ta : sym.name_en}
                    </p>
                    <p className="text-[10px] font-mono-tamil text-[var(--color-muted)]">
                      {sym.rational ? `${sym.rational.numerator}/${sym.rational.denominator}` : sym.codepoint}
                    </p>
                  </div>
                </button>
              );
            })}

            {filteredSymbols.length === 0 && (
              <div className="col-span-full py-12 text-center text-xs text-[var(--color-muted)]">
                {t.tools.symbols.noMatches}
              </div>
            )}
          </div>
        </div>

        {/* Detail Inspector Card */}
        <div className="lg:col-span-5">
          <Card className="p-6 sticky top-20 space-y-5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-[11px] text-[var(--color-muted)] uppercase tracking-wider block mb-1">
                  {t.tools.symbols.symbolDetailsHeading}
                </span>
                <h2 className="text-xl font-tamil font-bold text-[var(--color-mai)]">
                  {language === "ta" ? selectedSymbol.name_ta : selectedSymbol.name_en}
                </h2>
                <span className="text-xs text-[var(--color-muted)]">
                  {language === "ta" ? selectedSymbol.name_en : selectedSymbol.name_ta}
                </span>
              </div>
              <Badge variant="terracotta" className="capitalize">{selectedSymbol.category}</Badge>
            </div>

            <div className="rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-8 flex flex-col items-center justify-center text-center space-y-2">
              <span className="text-6xl sm:text-7xl font-tamil font-normal select-all text-[var(--color-mai)]">
                {selectedSymbol.glyph}
              </span>
              <span className="text-xs font-mono-tamil text-[var(--color-semman)] font-bold">
                {selectedSymbol.codepoint}
              </span>
            </div>

            <div className="space-y-3 divide-y divide-[var(--border-line)] text-xs">
              {selectedSymbol.rational && (
                <div className="pt-2.5 flex items-center justify-between">
                  <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5" />
                    {t.tools.symbols.rationalLabel}:
                  </span>
                  <span className="font-mono-tamil font-bold text-[var(--color-mai)] text-sm">
                    {selectedSymbol.rational.numerator} / {selectedSymbol.rational.denominator}
                  </span>
                </div>
              )}

              {selectedSymbol.decimal_value !== null && (
                <div className="pt-2.5 flex items-center justify-between">
                  <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5" />
                    {t.tools.symbols.decimalLabel}:
                  </span>
                  <span className="font-mono-tamil font-semibold text-[var(--color-mai)]">
                    {selectedSymbol.decimal_value}
                  </span>
                </div>
              )}

              <div className="pt-2.5 flex flex-col gap-1">
                <span className="text-[var(--color-muted)] flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5" />
                  {t.tools.symbols.periodLabel}:
                </span>
                <p className="text-xs text-[var(--color-mai)] leading-relaxed">
                  {selectedSymbol.period_usage}
                </p>
              </div>
            </div>

            <CopyButton
              text={selectedSymbol.glyph}
              label={`${t.tools.symbols.copySymbolButton} (${selectedSymbol.glyph})`}
              copiedLabel={t.actions.copied}
              className="w-full"
            />
          </Card>
        </div>
      </div>

      <StickyActionBar
        outputText={selectedSymbol.glyph}
        onClear={() => setSearchQuery("")}
        copyLabel={t.tools.symbols.copySymbolButton}
      />
    </div>
  );
}
