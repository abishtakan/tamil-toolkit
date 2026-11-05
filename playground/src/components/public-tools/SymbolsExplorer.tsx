import { useState, useMemo } from "react";
import { useLanguage } from "../../lib/i18n";
import { TRADITIONAL_SYMBOLS, TraditionalSymbol } from "../../lib/engine";
import { Card } from "../ui/card";
import { Badge } from "../ui/badge";
import { CopyButton } from "../common/CopyButton";
import { StickyActionBar } from "../common/StickyActionBar";
import { Search, Compass, BookOpen, Layers } from "lucide-react";

export function SymbolsExplorer() {
  const { t, language } = useLanguage();
  const [selectedCategory, setSelectedCategory] = useState<"all" | "fraction" | "land" | "volume" | "currency">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSymbol, setSelectedSymbol] = useState<TraditionalSymbol>(TRADITIONAL_SYMBOLS[0]);

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
    { id: "currency", label: t.tools.symbols.categoryCurrency }
  ] as const;

  return (
    <div className="space-y-6 animate-in fade-in-50 duration-150">
      {/* Title & Description Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
              {t.tools.symbols.title}
            </h2>
            <Badge variant="sandhanam">Unicode 15.0+</Badge>
          </div>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans max-w-2xl leading-relaxed">
            {t.tools.symbols.desc}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <CopyButton text={selectedSymbol.glyph} label={t.tools.symbols.copySymbolButton} />
        </div>
      </div>

      {/* Controls: Search & Category Pills */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t.tools.symbols.searchPlaceholder}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--border-line)] bg-[var(--bg-surface)] text-xs sm:text-sm font-tamil text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/60 focus:border-[var(--color-semman)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[var(--color-semman)] transition-colors"
          />
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-tamil font-medium whitespace-nowrap transition-colors border ${
                selectedCategory === cat.id
                  ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-bold shadow-xs"
                  : "bg-[var(--bg-surface)] border-[var(--border-line)] text-[var(--color-muted)] hover:border-[var(--color-semman)] hover:text-[var(--color-mai)]"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Catalog List (Left) + Detail Inspector (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Symbol Grid (Cols 1-7) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="flex items-center justify-between text-xs text-[var(--color-muted)] font-tamil px-1">
            <span>
              {language === "ta" ? "கிடைத்துள்ள குறியீடுகள்:" : "Available Glyphs:"}{" "}
              <strong className="text-[var(--color-mai)] font-bold">{filteredSymbols.length}</strong>
            </span>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2.5 max-h-[500px] overflow-y-auto p-1 rounded-2xl border border-[var(--border-line)] bg-[var(--bg-surface)]">
            {filteredSymbols.map((sym) => {
              const isSelected = selectedSymbol.glyph === sym.glyph;
              return (
                <button
                  key={sym.codepoint}
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
                    <p className="text-[11px] font-tamil font-semibold truncate">
                      {language === "ta" ? sym.name_ta : sym.name_en}
                    </p>
                    <p className="text-[9px] font-mono-tamil text-[var(--color-muted)]">
                      {sym.rational ? `${sym.rational.numerator}/${sym.rational.denominator}` : sym.codepoint}
                    </p>
                  </div>
                </button>
              );
            })}

            {filteredSymbols.length === 0 && (
              <div className="col-span-full py-12 text-center text-xs text-[var(--color-muted)] font-tamil">
                {t.tools.symbols.noMatches}
              </div>
            )}
          </div>
        </div>

        {/* Detail Inspector Card (Cols 8-12) */}
        <div className="lg:col-span-5">
          <Card className="p-6 border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl sticky top-20 space-y-5">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-tamil text-[var(--color-muted)] uppercase tracking-wider block mb-1">
                  {t.tools.symbols.symbolDetailsHeading}
                </span>
                <h3 className="text-xl font-tamil font-bold text-[var(--color-mai)]">
                  {language === "ta" ? selectedSymbol.name_ta : selectedSymbol.name_en}
                </h3>
                <span className="text-xs font-tamil text-[var(--color-muted)]">
                  {language === "ta" ? selectedSymbol.name_en : selectedSymbol.name_ta}
                </span>
              </div>
              <Badge variant="terracotta">{selectedSymbol.category}</Badge>
            </div>

            {/* Giant Glyph Spotlight Tile */}
            <div className="rounded-2xl bg-[var(--bg-canvas)] border border-[var(--border-line)] p-8 flex flex-col items-center justify-center text-center space-y-2">
              <span className="text-6xl sm:text-7xl font-tamil font-normal select-all text-[var(--color-mai)]">
                {selectedSymbol.glyph}
              </span>
              <span className="text-xs font-mono-tamil text-[var(--color-semman)] font-bold">
                {selectedSymbol.codepoint}
              </span>
            </div>

            {/* Metric Fields */}
            <div className="space-y-3 divide-y divide-[var(--border-line)] text-xs font-tamil">
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
                <p className="text-xs text-[var(--color-mai)] font-tamil-sans leading-relaxed">
                  {selectedSymbol.period_usage}
                </p>
              </div>
            </div>

            {/* Action Bar */}
            <div className="pt-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(selectedSymbol.glyph);
                }}
                className="w-full inline-flex items-center justify-center min-h-[44px] px-4 py-2.5 rounded-xl bg-[var(--color-semman)] text-[#faf7f2] font-tamil text-xs sm:text-sm font-semibold hover:bg-[var(--color-semman-hover)] transition-colors shadow-xs active:scale-[0.99]"
              >
                {t.tools.symbols.copySymbolButton} ({selectedSymbol.glyph})
              </button>
            </div>
          </Card>
        </div>
      </div>

      {/* Sticky Bottom Bar for Mobile Viewports */}
      <StickyActionBar
        outputText={selectedSymbol.glyph}
        onClear={() => setSearchQuery("")}
        copyLabel={t.tools.symbols.copySymbolButton}
      />
    </div>
  );
}
