import { useState, useEffect } from "react";
import { useLanguage } from "./lib/i18n";
import { initializeEngine, isEngineReady } from "./lib/engine";
import { OverviewHub } from "./components/common/OverviewHub";
import { CodecConverter } from "./components/public-tools/CodecConverter";
import { NumeralFormatter } from "./components/public-tools/NumeralFormatter";
import { CalendarExplorer } from "./components/public-tools/CalendarExplorer";
import { TextSorter } from "./components/public-tools/TextSorter";
import { ScalarInspector } from "./components/developer-tools/ScalarInspector";
import { DispatcherSandbox } from "./components/developer-tools/DispatcherSandbox";
import { CodeGenerator } from "./components/developer-tools/CodeGenerator";
import { BatchProcessor } from "./components/developer-tools/BatchProcessor";
import { Button } from "./components/ui/button";
import { Badge } from "./components/ui/badge";
import {
  Globe,
  Sun,
  Moon,
  Sparkles,
  LayoutGrid,
  Type,
  Banknote,
  Calendar,
  ArrowDownAZ,
  Cpu,
  Terminal,
  Code2,
  Files,
  ShieldCheck
} from "lucide-react";

export function App() {
  const { language, setLanguage, t } = useLanguage();
  const [engineReady, setEngineReady] = useState(isEngineReady());
  const [activeTab, setActiveTab] = useState<"hub" | "public" | "dev">("hub");
  const [activePublicTool, setActivePublicTool] = useState<string>("codec");
  const [activeDevTool, setActiveDevTool] = useState<string>("scalar");
  const [isDark, setIsDark] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return (
        localStorage.getItem("tt_playground_theme") === "dark" ||
        window.matchMedia("(prefers-color-scheme: dark)").matches
      );
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

  const handleSelectFromHub = (tab: "public" | "dev", toolId: string) => {
    setActiveTab(tab);
    if (tab === "public") {
      setActivePublicTool(toolId);
    } else {
      setActiveDevTool(toolId);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggleLanguage = () => {
    setLanguage(language === "ta" ? "en" : "ta");
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-canvas)] text-[var(--color-mai)] flex flex-col font-tamil-sans">
      {/* Top Header */}
      <header className="sticky top-0 z-30 border-b border-[var(--border-line)] bg-[var(--bg-surface)]/95 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          {/* Brand Logo & Name */}
          <button
            onClick={() => setActiveTab("hub")}
            className="flex items-center gap-2.5 text-left group cursor-pointer"
          >
            <div className="w-9 h-9 rounded-xl bg-[var(--color-semman)] text-[#faf7f2] flex items-center justify-center font-tamil font-bold text-lg shadow-sm group-hover:scale-105 transition-transform">
              த
            </div>
            <div>
              <span className="font-tamil font-bold text-base sm:text-lg tracking-tight block text-[var(--color-mai)] leading-tight">
                {t.siteTitle}
              </span>
              <span className="text-[10px] text-[var(--color-muted)] font-mono-tamil hidden sm:block">
                tamil-toolkit v0.1.0-alpha.6
              </span>
            </div>
          </button>

          {/* Privacy Badge on Desktop */}
          <div className="hidden lg:flex items-center gap-1.5 text-xs text-[var(--color-muted)] bg-[var(--bg-canvas)] px-3 py-1.5 rounded-full border border-[var(--border-line)]">
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--color-semman)]" />
            <span className="font-tamil">{t.privacyBadge}</span>
          </div>

          {/* Controls: Language & Theme Toggle */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleLanguage}
              className="text-xs font-tamil border-[var(--border-line)] min-h-[38px] px-3"
              aria-label="Toggle language"
            >
              <Globe className="w-3.5 h-3.5 mr-1.5 text-[var(--color-semman)]" />
              <span className="font-semibold">{language === "ta" ? "English" : "தமிழ்"}</span>
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="text-[var(--color-muted)] hover:text-[var(--color-mai)] min-h-[38px] min-w-[38px]"
              aria-label="Toggle theme"
            >
              {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 pb-24 md:pb-12 space-y-6">
        {/* Navigation Tabs Bar */}
        <nav aria-label="Main navigation" className="flex items-center justify-between border-b border-[var(--border-line)] pb-3 overflow-x-auto no-scrollbar gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("hub")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium font-tamil transition-all ${
                activeTab === "hub"
                  ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold shadow-sm"
                  : "bg-[var(--bg-surface)] text-[var(--color-muted)] hover:text-[var(--color-mai)] border border-[var(--border-line)]"
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span>{t.tabs.hub}</span>
            </button>

            <button
              onClick={() => setActiveTab("public")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium font-tamil transition-all ${
                activeTab === "public"
                  ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold shadow-sm"
                  : "bg-[var(--bg-surface)] text-[var(--color-muted)] hover:text-[var(--color-mai)] border border-[var(--border-line)]"
              }`}
            >
              <Sparkles className="w-4 h-4" />
              <span>{t.tabs.publicTools}</span>
            </button>

            <button
              onClick={() => setActiveTab("dev")}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium font-tamil transition-all ${
                activeTab === "dev"
                  ? "bg-[var(--color-semman)] text-[#faf7f2] font-semibold shadow-sm"
                  : "bg-[var(--bg-surface)] text-[var(--color-muted)] hover:text-[var(--color-mai)] border border-[var(--border-line)]"
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>{t.tabs.devTools}</span>
            </button>
          </div>

          {!engineReady && (
            <Badge variant="outline" className="animate-pulse text-xs text-[var(--color-sandhanam)] border-[var(--color-sandhanam)]/40">
              WASM Engine Loading…
            </Badge>
          )}
        </nav>

        {/* View Switcher */}
        {activeTab === "hub" && <OverviewHub onSelectTool={handleSelectFromHub} />}

        {activeTab === "public" && (
          <div className="space-y-6">
            {/* Tool Selection Sub-Chips */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
              {[
                { id: "codec", label: t.tools.codec.title, icon: Type },
                { id: "numeral", label: t.tools.numeral.title, icon: Banknote },
                { id: "calendar", label: t.tools.calendar.title, icon: Calendar },
                { id: "sorter", label: t.tools.sorter.title, icon: ArrowDownAZ }
              ].map((tool) => {
                const Icon = tool.icon;
                const isActive = activePublicTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setActivePublicTool(tool.id)}
                    className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-tamil font-medium whitespace-nowrap transition-all border ${
                      isActive
                        ? "bg-[var(--bg-surface)] border-[var(--color-semman)] text-[var(--color-semman)] font-bold shadow-xs"
                        : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tool.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Active Public Tool View */}
            {activePublicTool === "codec" && <CodecConverter />}
            {activePublicTool === "numeral" && <NumeralFormatter />}
            {activePublicTool === "calendar" && <CalendarExplorer />}
            {activePublicTool === "sorter" && <TextSorter />}
          </div>
        )}

        {activeTab === "dev" && (
          <div className="space-y-6">
            {/* Tool Selection Sub-Chips */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
              {[
                { id: "scalar", label: t.tools.scalar.title, icon: Cpu },
                { id: "dispatcher", label: t.tools.dispatcher.title, icon: Terminal },
                { id: "codegen", label: t.tools.codegen.title, icon: Code2 },
                { id: "batch", label: t.tools.batch.title, icon: Files }
              ].map((tool) => {
                const Icon = tool.icon;
                const isActive = activeDevTool === tool.id;
                return (
                  <button
                    key={tool.id}
                    onClick={() => setActiveDevTool(tool.id)}
                    className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-tamil font-medium whitespace-nowrap transition-all border ${
                      isActive
                        ? "bg-[var(--bg-surface)] border-[var(--color-sandhanam)] text-[var(--color-sandhanam)] font-bold shadow-xs"
                        : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-muted)] hover:text-[var(--color-mai)]"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tool.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Active Dev Tool View */}
            {activeDevTool === "scalar" && <ScalarInspector />}
            {activeDevTool === "dispatcher" && <DispatcherSandbox />}
            {activeDevTool === "codegen" && <CodeGenerator />}
            {activeDevTool === "batch" && <BatchProcessor />}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--border-line)] bg-[var(--bg-surface)] py-6 mt-auto">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-tamil text-[var(--color-muted)] text-center sm:text-left">
          <p>
            {language === "en"
              ? "Tamil Toolkit Playground · WebAssembly Engine"
              : "தமிழ் கருவிப் பட்டறை · Tamil Toolkit WebAssembly Engine"}
          </p>
          <p className="font-mono-tamil">
            Rust owns linguistic behavior · MIT Licensed
          </p>
        </div>
      </footer>
    </div>
  );
}
