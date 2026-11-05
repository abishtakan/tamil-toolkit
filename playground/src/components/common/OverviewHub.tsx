import { useLanguage } from "../../lib/i18n";
import { Card, CardHeader, CardTitle, CardDescription } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Type,
  Banknote,
  Calendar,
  ArrowDownAZ,
  Terminal,
  Code2,
  Files,
  Cpu,
  ArrowRight
} from "lucide-react";

interface OverviewHubProps {
  onSelectTool: (tab: "public" | "dev", toolId: string) => void;
}

export function OverviewHub({ onSelectTool }: OverviewHubProps) {
  const { t, language } = useLanguage();

  const publicTools = [
    {
      id: "codec",
      title: t.tools.codec.title,
      desc: t.tools.codec.desc,
      icon: Type,
      tag: language === "en" ? "Real-time" : "அதிவேகம்"
    },
    {
      id: "numeral",
      title: t.tools.numeral.title,
      desc: t.tools.numeral.desc,
      icon: Banknote,
      tag: language === "en" ? "Financial" : "காசோலை"
    },
    {
      id: "calendar",
      title: t.tools.calendar.title,
      desc: t.tools.calendar.desc,
      icon: Calendar,
      tag: language === "en" ? "Solar / Drik" : "பஞ்சாங்கம்"
    },
    {
      id: "sorter",
      title: t.tools.sorter.title,
      desc: t.tools.sorter.desc,
      icon: ArrowDownAZ,
      tag: language === "en" ? "Collation" : "இலக்கணம்"
    }
  ];

  const devTools = [
    {
      id: "scalar",
      title: t.tools.scalar.title,
      desc: t.tools.scalar.desc,
      icon: Cpu,
      tag: language === "en" ? "Unicode" : "ஒருங்குறி"
    },
    {
      id: "dispatcher",
      title: t.tools.dispatcher.title,
      desc: t.tools.dispatcher.desc,
      icon: Terminal,
      tag: "JSON"
    },
    {
      id: "codegen",
      title: t.tools.codegen.title,
      desc: t.tools.codegen.desc,
      icon: Code2,
      tag: "Rust / Python / TS"
    },
    {
      id: "batch",
      title: t.tools.batch.title,
      desc: t.tools.batch.desc,
      icon: Files,
      tag: "Web Worker"
    }
  ];

  return (
    <div className="space-y-10 py-2">
      {/* Hero Welcome in Terracotta Palette */}
      <div className="rounded-3xl border border-[var(--border-line)] bg-gradient-to-br from-[var(--bg-surface)] to-[var(--bg-raised)] p-6 sm:p-10 shadow-sm relative overflow-hidden">
        <div className="relative z-10 max-w-2xl space-y-3">
          <Badge variant="terracotta" className="px-3 py-1 text-xs">
            {t.privacyBadge}
          </Badge>
          <h1 className="text-2xl sm:text-4xl font-tamil font-bold text-[var(--color-mai)] leading-tight">
            {t.siteTitle}
          </h1>
          <p className="text-sm sm:text-base text-[var(--color-muted)] font-tamil-sans leading-relaxed">
            {t.siteSubtitle}
          </p>
        </div>
      </div>

      {/* Public Tools Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
          <h2 className="text-lg sm:text-xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tabs.publicTools}
          </h2>
          <span className="text-xs text-[var(--color-muted)] font-tamil-sans">
            {language === "en" ? "Zero-latency in-browser utilities" : "நொடியில் இயங்கும் பயன்பாட்டுக் கருவிகள்"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {publicTools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => onSelectTool("public", tool.id)}
                className="text-left group cursor-pointer"
              >
                <Card className="h-full hover:border-[var(--color-semman)] hover:shadow-md transition-all duration-200 p-5 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center group-hover:scale-105 transition-transform">
                        <Icon className="w-5 h-5" />
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {tool.tag}
                      </Badge>
                    </div>

                    <CardHeader className="p-0">
                      <CardTitle className="text-base group-hover:text-[var(--color-semman)] transition-colors">
                        {tool.title}
                      </CardTitle>
                      <CardDescription className="line-clamp-2 text-xs mt-1">
                        {tool.desc}
                      </CardDescription>
                    </CardHeader>
                  </div>

                  <div className="pt-4 flex items-center text-xs font-semibold text-[var(--color-semman)] font-tamil">
                    <span>{language === "en" ? "Open Tool" : "தொடங்கு"}</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                  </div>
                </Card>
              </button>
            );
          })}
        </div>
      </section>

      {/* Developer Diagnostics Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
          <h2 className="text-lg sm:text-xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tabs.devTools}
          </h2>
          <span className="text-xs text-[var(--color-muted)] font-tamil-sans">
            {language === "en" ? "Diagnostics & low-level sandbox" : "நிரலாளர்கள் & ஒருங்குறி ஆய்வகம்"}
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {devTools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => onSelectTool("dev", tool.id)}
                className="text-left group cursor-pointer"
              >
                <Card className="h-full hover:border-[var(--color-sandhanam)] hover:shadow-md transition-all duration-200 p-5 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="w-10 h-10 rounded-xl bg-[#fcf5e8] dark:bg-[#2d2211] text-[var(--color-sandhanam)] flex items-center justify-center group-hover:scale-105 transition-transform">
                        <Icon className="w-5 h-5" />
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {tool.tag}
                      </Badge>
                    </div>

                    <CardHeader className="p-0">
                      <CardTitle className="text-base group-hover:text-[var(--color-sandhanam)] transition-colors">
                        {tool.title}
                      </CardTitle>
                      <CardDescription className="line-clamp-2 text-xs mt-1">
                        {tool.desc}
                      </CardDescription>
                    </CardHeader>
                  </div>

                  <div className="pt-4 flex items-center text-xs font-semibold text-[var(--color-sandhanam)] font-tamil">
                    <span>{language === "en" ? "Inspect" : "ஆய்வு செய்"}</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                  </div>
                </Card>
              </button>
            );
          })}
        </div>
      </section>
    </div>
  );
}
