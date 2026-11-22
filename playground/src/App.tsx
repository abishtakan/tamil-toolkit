import { useState, useEffect, useRef, useMemo, useCallback, lazy, Suspense } from "react";
import { useLanguage } from "./lib/i18n";
import { initializeEngine, isEngineReady } from "./lib/engine";
import {
  TOOLS,
  TOOL_GROUPS,
  ToolGroupId,
  ToolIconKey,
  ToolId,
  filterToolsByQuery,
  getToolCopy,
  getToolMeta,
  resolveToolFromSearch,
} from "./lib/tools";
import { OverviewHub } from "./components/common/OverviewHub";

const CodecConverter = lazy(() =>
  import("./components/public-tools/CodecConverter").then((m) => ({ default: m.CodecConverter }))
);
const TranslitTool = lazy(() =>
  import("./components/public-tools/TranslitTool").then((m) => ({ default: m.TranslitTool }))
);
const NumeralFormatter = lazy(() =>
  import("./components/public-tools/NumeralFormatter").then((m) => ({ default: m.NumeralFormatter }))
);
const CalendarExplorer = lazy(() =>
  import("./components/public-tools/CalendarExplorer").then((m) => ({ default: m.CalendarExplorer }))
);
const TextSorter = lazy(() =>
  import("./components/public-tools/TextSorter").then((m) => ({ default: m.TextSorter }))
);
const SymbolsExplorer = lazy(() =>
  import("./components/public-tools/SymbolsExplorer").then((m) => ({ default: m.SymbolsExplorer }))
);
const HyphenatorTool = lazy(() =>
  import("./components/public-tools/HyphenatorTool").then((m) => ({ default: m.HyphenatorTool }))
);
const LexiconExplorer = lazy(() =>
  import("./components/public-tools/LexiconExplorer").then((m) => ({ default: m.LexiconExplorer }))
);
const ScalarInspector = lazy(() =>
  import("./components/developer-tools/ScalarInspector").then((m) => ({ default: m.ScalarInspector }))
);
const LetterAnalyzer = lazy(() =>
  import("./components/developer-tools/LetterAnalyzer").then((m) => ({ default: m.LetterAnalyzer }))
);
const NormalizerTool = lazy(() =>
  import("./components/developer-tools/NormalizerTool").then((m) => ({ default: m.NormalizerTool }))
);
const DispatcherSandbox = lazy(() =>
  import("./components/developer-tools/DispatcherSandbox").then((m) => ({ default: m.DispatcherSandbox }))
);
const CodeGenerator = lazy(() =>
  import("./components/developer-tools/CodeGenerator").then((m) => ({ default: m.CodeGenerator }))
);
const BatchProcessor = lazy(() =>
  import("./components/developer-tools/BatchProcessor").then((m) => ({ default: m.BatchProcessor }))
);
import {
  Globe,
  Sun,
  Moon,
  Home,
  Menu,
  X,
  Search,
  Type,
  Languages,
  Banknote,
  Calendar,
  ArrowDownAZ,
  BookOpen,
  BookMarked,
  Scissors,
  ShieldCheck,
  Cpu,
  Terminal,
  Code2,
  Files,
  Loader2,
  AlignLeft,
} from "lucide-react";

function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 64 64"
      aria-hidden="true"
      className={className}
    >
      <rect width="64" height="64" rx="16" fill="#181513" />
      <circle cx="32" cy="20.8" r="8.4" fill="#e05338" />
      <circle cx="20" cy="41.6" r="8.4" fill="#faf7f2" />
      <circle cx="44" cy="41.6" r="8.4" fill="#faf7f2" />
    </svg>
  );
}

export function ToolIcon({ icon, className }: { icon: ToolIconKey; className?: string }) {
  switch (icon) {
    case "book-marked":
      return <BookMarked className={className} />;
    case "arrow-down-az":
      return <ArrowDownAZ className={className} />;
    case "letter-a":
      return <AlignLeft className={className} />;
    case "type":
      return <Type className={className} />;
    case "languages":
      return <Languages className={className} />;
    case "shield-check":
      return <ShieldCheck className={className} />;
    case "scissors":
      return <Scissors className={className} />;
    case "files":
      return <Files className={className} />;
    case "banknote":
      return <Banknote className={className} />;
    case "calendar":
      return <Calendar className={className} />;
    case "book-open":
      return <BookOpen className={className} />;
    case "cpu":
      return <Cpu className={className} />;
    case "terminal":
      return <Terminal className={className} />;
    case "code-2":
      return <Code2 className={className} />;
  }
}

export function App() {
  const { language, setLanguage, t } = useLanguage();
  const [engineReady, setEngineReady] = useState(isEngineReady());
  const [activeTool, setActiveTool] = useState<ToolId | "home">(() =>
    typeof window !== "undefined" ? resolveToolFromSearch(window.location.search) : "home"
  );
  const [pendingLexiconQuery, setPendingLexiconQuery] = useState<{
    query: string;
    nonce: number;
  } | null>(null);

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [toolFilterQuery, setToolFilterQuery] = useState("");
  const desktopSearchRef = useRef<HTMLInputElement>(null);
  const mobileSearchRef = useRef<HTMLInputElement>(null);

  const [isDark, setIsDark] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("tt_playground_theme");
      if (saved === "dark") return true;
      if (saved === "light") return false;
      return window.matchMedia("(prefers-color-scheme: dark)").matches;
    }
    return false;
  });

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("tt_playground_theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("tt_playground_theme", "light");
    }
  }, [isDark]);

  useEffect(() => {
    initializeEngine()
      .then(() => setEngineReady(true))
      .catch((err) => console.error("Engine init error:", err));
  }, []);

  // Sync browser back/forward navigation with ?tool=...
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handlePopState = () => {
      setActiveTool(resolveToolFromSearch(window.location.search));
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Keyboard shortcuts: "/" or Ctrl/Cmd+K focuses tool filter; Escape clears or closes mobile drawer
  useEffect(() => {
    if (typeof window === "undefined") return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (mobileMenuOpen) {
          setMobileMenuOpen(false);
          return;
        }
        if (
          document.activeElement === desktopSearchRef.current ||
          document.activeElement === mobileSearchRef.current
        ) {
          if (toolFilterQuery) {
            setToolFilterQuery("");
          } else {
            (document.activeElement as HTMLElement).blur();
          }
        }
        return;
      }

      const target = e.target as HTMLElement | null;
      const isEditing =
        target &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.tagName === "SELECT" ||
          target.isContentEditable);

      if ((e.key === "k" && (e.ctrlKey || e.metaKey)) || (e.key === "/" && !isEditing)) {
        e.preventDefault();
        if (window.innerWidth >= 1024) {
          desktopSearchRef.current?.focus();
          desktopSearchRef.current?.select();
        } else {
          setMobileMenuOpen(true);
          setTimeout(() => mobileSearchRef.current?.focus(), 40);
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen, toolFilterQuery]);

  const navigateToTool = useCallback((next: ToolId | "home") => {
    setActiveTool(next);
    setMobileMenuOpen(false);
    try {
      if (typeof window !== "undefined") {
        const url = new URL(window.location.href);
        if (next === "home") {
          url.searchParams.delete("tool");
          url.searchParams.delete("mode");
        } else {
          url.searchParams.set("tool", next);
          if (next !== "lexicon") {
            url.searchParams.delete("mode");
          }
        }
        window.history.replaceState(null, "", url.toString());
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } catch {
      // Ignore history restriction
    }
  }, []);

  const handleQuickDictionarySearch = useCallback(
    (query: string) => {
      const cleaned = query.trim();
      if (cleaned) {
        setPendingLexiconQuery({ query: cleaned, nonce: Date.now() });
      }
      navigateToTool("lexicon");
    },
    [navigateToTool]
  );

  const toggleLanguage = () => {
    setLanguage(language === "ta" ? "en" : "ta");
  };

  const toggleTheme = () => {
    setIsDark((prev) => !prev);
  };

  const filteredTools = useMemo(
    () => filterToolsByQuery(toolFilterQuery, t),
    [toolFilterQuery, t]
  );

  const groupedTools = useMemo(() => {
    const map = new Map<ToolGroupId, typeof filteredTools>();
    for (const group of TOOL_GROUPS) {
      map.set(group.id, []);
    }
    for (const tool of filteredTools) {
      const bucket = map.get(tool.group);
      if (bucket) bucket.push(tool);
    }
    return map;
  }, [filteredTools]);

  const activeTitle = useMemo(() => {
    if (activeTool === "home") return t.siteTitle;
    return getToolCopy(activeTool, t).title;
  }, [activeTool, t]);

  const renderSidebarBody = (searchInputRef: React.RefObject<HTMLInputElement | null>) => (
    <div className="flex flex-col h-full">
      {/* Brand Header */}
      <div className="px-4 h-16 flex items-center justify-between border-b border-[var(--border-line)] shrink-0">
        <button
          type="button"
          onClick={() => navigateToTool("home")}
          className="flex items-center gap-2.5 text-left group cursor-pointer rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)]"
        >
          <BrandMark className="w-8 h-8 rounded-lg shrink-0 ring-1 ring-black/10 dark:ring-white/15 group-hover:scale-[1.03] transition-transform" />
          <div className="min-w-0">
            <span className="font-tamil font-bold text-sm text-[var(--color-mai)] block leading-tight truncate">
              {t.siteTitle}
            </span>
            <span className="text-[10px] text-[var(--color-muted)] font-mono-tamil block">
              v0.1.0-alpha.8
            </span>
          </div>
        </button>

        <button
          type="button"
          onClick={() => setMobileMenuOpen(false)}
          aria-label={t.shell.closeMenu}
          className="lg:hidden min-w-[40px] min-h-[40px] flex items-center justify-center rounded-lg text-[var(--color-muted)] hover:text-[var(--color-mai)] hover:bg-[var(--bg-raised)] cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Filter Input */}
      <div className="p-3 border-b border-[var(--border-line)] shrink-0">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[var(--color-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            ref={searchInputRef}
            type="text"
            value={toolFilterQuery}
            onChange={(e) => setToolFilterQuery(e.target.value)}
            placeholder={t.shell.searchPlaceholder}
            aria-label={t.shell.searchPlaceholder}
            className="w-full h-9 pl-8 pr-8 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs text-[var(--color-mai)] placeholder:text-[var(--color-muted)]/70 focus-visible:outline-none focus-visible:border-[var(--color-semman)]"
          />
          {toolFilterQuery ? (
            <button
              type="button"
              onClick={() => setToolFilterQuery("")}
              aria-label={t.shell.clearSearch}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 p-1 rounded text-[var(--color-muted)] hover:text-[var(--color-mai)] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          ) : (
            <kbd className="hidden lg:inline-flex items-center justify-center px-1.5 h-5 text-[10px] font-mono-tamil text-[var(--color-muted)] bg-[var(--bg-surface)] border border-[var(--border-line)] rounded absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
              /
            </kbd>
          )}
        </div>
      </div>

      {/* Scrollable Navigation Groups */}
      <nav aria-label="Playground tools" className="flex-1 overflow-y-auto px-2.5 py-3 space-y-5">
        {/* Home Item */}
        {!toolFilterQuery.trim() && (
          <div>
            <button
              type="button"
              onClick={() => navigateToTool("home")}
              aria-current={activeTool === "home" ? "page" : undefined}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer ${
                activeTool === "home"
                  ? "bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold"
                  : "text-[var(--color-mai)] hover:bg-[var(--bg-raised)]"
              }`}
            >
              <Home className="w-4 h-4 shrink-0" />
              <span className="truncate">{t.shell.homeLabel}</span>
            </button>
          </div>
        )}

        {/* Tool Groups */}
        {TOOL_GROUPS.map((group) => {
          const items = groupedTools.get(group.id) ?? [];
          if (items.length === 0) return null;
          return (
            <div key={group.id} className="space-y-1">
              <div className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                {t.navGroups[group.id]}
              </div>
              {items.map((tool) => {
                const copy = getToolCopy(tool.id, t);
                const isActive = activeTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    type="button"
                    onClick={() => navigateToTool(tool.id)}
                    aria-current={isActive ? "page" : undefined}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-left text-[13px] transition-colors cursor-pointer ${
                      isActive
                        ? "bg-[var(--color-semman-light)] text-[var(--color-semman)] font-semibold border-l-2 border-[var(--color-semman)]"
                        : "text-[var(--color-mai)] hover:bg-[var(--bg-raised)]"
                    }`}
                  >
                    <ToolIcon
                      icon={tool.icon}
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-[var(--color-semman)]" : "text-[var(--color-muted)]"
                      }`}
                    />
                    <span className="truncate">{copy.title}</span>
                  </button>
                );
              })}
            </div>
          );
        })}

        {filteredTools.length === 0 && (
          <div className="px-3 py-6 text-center space-y-2">
            <p className="text-xs text-[var(--color-muted)]">{t.shell.noToolsFound}</p>
            <button
              type="button"
              onClick={() => setToolFilterQuery("")}
              className="text-xs font-medium text-[var(--color-semman)] hover:underline cursor-pointer"
            >
              {t.shell.clearSearch}
            </button>
          </div>
        )}
      </nav>

      {/* Sidebar Bottom Utilities */}
      <div className="p-3 border-t border-[var(--border-line)] space-y-2.5 shrink-0 bg-[var(--bg-surface)]">
        <div className="flex items-center justify-between gap-2 px-1">
          <div className="flex items-center gap-2 text-xs text-[var(--color-muted)]">
            {engineReady ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-600 dark:bg-emerald-400 shrink-0" />
                <span>{t.shell.engineReady}</span>
              </>
            ) : (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--color-sandhanam)] shrink-0" />
                <span>{t.shell.engineLoading}</span>
              </>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={toggleLanguage}
            aria-label={t.nav.switchPrompt}
            className="flex items-center justify-center gap-1.5 min-h-[38px] px-2.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-xs font-medium text-[var(--color-mai)] cursor-pointer"
          >
            <Globe className="w-3.5 h-3.5 text-[var(--color-semman)] shrink-0" />
            <span className="truncate">{t.nav.switchLanguageName}</span>
          </button>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label={isDark ? t.shell.themeLight : t.shell.themeDark}
            className="flex items-center justify-center gap-1.5 min-h-[38px] px-2.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] hover:border-[var(--color-semman)] text-xs font-medium text-[var(--color-mai)] cursor-pointer"
          >
            {isDark ? (
              <Sun className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            ) : (
              <Moon className="w-3.5 h-3.5 text-[var(--color-muted)] shrink-0" />
            )}
            <span className="truncate">{isDark ? "Light" : "Dark"}</span>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--color-mai)] flex flex-col lg:flex-row">
      {/* Desktop Sticky Sidebar */}
      <aside className="hidden lg:flex lg:w-[264px] lg:shrink-0 lg:sticky lg:top-0 lg:h-screen border-r border-[var(--border-line)] bg-[var(--bg-surface)] flex-col z-20">
        {renderSidebarBody(desktopSearchRef)}
      </aside>

      {/* Mobile & Tablet Top Header */}
      <header className="lg:hidden sticky top-0 z-30 h-14 border-b border-[var(--border-line)] bg-[var(--bg-surface)]/95 backdrop-blur-md px-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            aria-label={t.shell.openMenu}
            className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-xl text-[var(--color-mai)] hover:bg-[var(--bg-raised)] cursor-pointer shrink-0"
          >
            <Menu className="w-5 h-5" />
          </button>
          <button
            type="button"
            onClick={() => navigateToTool("home")}
            className="flex items-center gap-2 min-w-0 text-left cursor-pointer"
          >
            {activeTool === "home" ? (
              <BrandMark className="w-7 h-7 rounded-lg shrink-0 ring-1 ring-black/10 dark:ring-white/15" />
            ) : (
              <div className="w-7 h-7 rounded-lg bg-[var(--color-semman)] text-[#faf7f2] flex items-center justify-center shrink-0">
                <ToolIcon icon={getToolMeta(activeTool).icon} className="w-3.5 h-3.5" />
              </div>
            )}
            <span className="font-tamil font-bold text-sm text-[var(--color-mai)] truncate">
              {activeTitle}
            </span>
          </button>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <button
            type="button"
            onClick={toggleLanguage}
            aria-label={t.nav.switchPrompt}
            className="min-h-[38px] px-2.5 rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-xs font-medium text-[var(--color-mai)] inline-flex items-center gap-1 cursor-pointer"
          >
            <Globe className="w-3.5 h-3.5 text-[var(--color-semman)]" />
            <span>{t.nav.switchLanguageName}</span>
          </button>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label={isDark ? t.shell.themeLight : t.shell.themeDark}
            className="min-w-[38px] min-h-[38px] flex items-center justify-center rounded-lg border border-[var(--border-line)] bg-[var(--bg-canvas)] text-[var(--color-muted)] cursor-pointer"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </header>

      {/* Mobile Slide-Over Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/40 backdrop-blur-[1px]"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <aside
            aria-label="Mobile navigation"
            className="relative w-[280px] max-w-[85vw] h-full bg-[var(--bg-surface)] border-r border-[var(--border-line)] shadow-xl z-10 flex flex-col"
          >
            {renderSidebarBody(mobileSearchRef)}
          </aside>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col">
        <main className="flex-1 w-full max-w-5xl mx-auto px-4 sm:px-8 py-6 sm:py-8 pb-24 lg:pb-12">
          {activeTool === "home" && (
            <OverviewHub
              onSelectTool={navigateToTool}
              onQuickDictionarySearch={handleQuickDictionarySearch}
              engineReady={engineReady}
            />
          )}
          <Suspense
            fallback={
              <div className="py-12 flex items-center justify-center gap-2 text-sm text-[var(--color-muted)]">
                <Loader2 className="w-4 h-4 animate-spin text-[var(--color-semman)]" />
                <span>{t.shell.engineLoading}</span>
              </div>
            }
          >
            {activeTool === "lexicon" && (
              <LexiconExplorer
                engineReady={engineReady}
                initialQuery={pendingLexiconQuery?.query}
                initialQueryNonce={pendingLexiconQuery?.nonce}
              />
            )}
            {activeTool === "codec" && <CodecConverter engineReady={engineReady} />}
            {activeTool === "translit" && <TranslitTool engineReady={engineReady} />}
            {activeTool === "numeral" && <NumeralFormatter engineReady={engineReady} />}
            {activeTool === "calendar" && <CalendarExplorer engineReady={engineReady} />}
            {activeTool === "sorter" && <TextSorter engineReady={engineReady} />}
            {activeTool === "symbols" && <SymbolsExplorer />}
            {activeTool === "hyphenator" && <HyphenatorTool engineReady={engineReady} />}
            {activeTool === "scalar" && <ScalarInspector engineReady={engineReady} />}
            {activeTool === "letter" && <LetterAnalyzer engineReady={engineReady} />}
            {activeTool === "normalizer" && <NormalizerTool engineReady={engineReady} />}
            {activeTool === "dispatcher" && <DispatcherSandbox engineReady={engineReady} />}
            {activeTool === "codegen" && <CodeGenerator />}
            {activeTool === "batch" && <BatchProcessor />}
          </Suspense>
        </main>

        {/* Quiet Footer */}
        <footer className="border-t border-[var(--border-line)] bg-[var(--bg-surface)]/50 py-4 mt-auto">
          <div className="max-w-5xl mx-auto px-4 sm:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[var(--color-muted)] text-center sm:text-left">
            <p>{t.nav.footerNotice}</p>
            <p className="font-mono-tamil text-[11px]">{TOOLS.length} tools · Apache-2.0 License</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
