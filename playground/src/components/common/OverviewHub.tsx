import { useLanguage } from "../../lib/i18n";
import {
  Type,
  Banknote,
  Calendar,
  ArrowDownAZ,
  Terminal,
  Code2,
  Files,
  Cpu,
  BookOpen,
  Sparkles,
  ShieldCheck,
  ArrowRight
} from "lucide-react";

interface OverviewHubProps {
  onSelectTool: (tab: "public" | "dev", toolId: string) => void;
}

export function OverviewHub({ onSelectTool }: OverviewHubProps) {
  const { t } = useLanguage();

  const legacyProfiles = [
    "Bamini",
    "TSCII",
    "TAB",
    "TAM",
    "Anjal",
    "Vanavil",
    "LT-TM"
  ];

  return (
    <div className="space-y-8 py-2">
      {/* Workbench Header (Clean & Confident, No Defensive Badges) */}
      <div className="border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl p-6 sm:p-7 shadow-xs">
        <h1 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)] tracking-tight">
          {t.siteTitle}
        </h1>
        <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans leading-relaxed mt-1.5 max-w-2xl">
          {t.siteSubtitle}
        </p>
      </div>

      {/* Asymmetric Bento Workbench Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
          <h2 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
            {t.tabs.publicTools}
          </h2>
          <span className="text-xs text-[var(--color-muted)] font-tamil-sans">
            {t.hub.realtimeHeading}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Bento Hero Slot: Legacy Font & Encoding Converter (Col 1-7) */}
          <div className="lg:col-span-7">
            <div
              onClick={() => onSelectTool("public", "codec")}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectTool("public", "codec");
                }
              }}
              role="button"
              tabIndex={0}
              className="h-full border border-[var(--border-line)] hover:border-[var(--color-semman)] bg-[var(--bg-surface)] hover:bg-[var(--bg-raised)]/30 rounded-2xl p-6 flex flex-col justify-between transition-colors duration-150 cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] active:scale-[0.99]"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center shrink-0">
                    <Type className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.codec.title}
                  </h3>
                </div>

                <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.codec.desc}
                </p>

                {/* Supported Font Encodings List */}
                <div className="pt-2">
                  <div className="flex flex-wrap gap-1.5">
                    {legacyProfiles.map((profile) => (
                      <span
                        key={profile}
                        className="text-[11px] px-2.5 py-1 rounded-md bg-[var(--bg-raised)] text-[var(--color-mai)] border border-[var(--border-line)] font-mono-tamil"
                      >
                        {profile}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-6 flex items-center justify-between border-t border-[var(--border-line)] mt-4">
                <span className="text-xs font-semibold text-[var(--color-semman)] font-tamil">
                  {t.hub.launchTool}
                </span>
                <ArrowRight className="w-4 h-4 text-[var(--color-semman)]" />
              </div>
            </div>
          </div>

          {/* Bento Slot 2: Numeral & Legal Cheque Formatter (Col 8-12) */}
          <div className="lg:col-span-5">
            <div
              onClick={() => onSelectTool("public", "numeral")}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectTool("public", "numeral");
                }
              }}
              role="button"
              tabIndex={0}
              className="h-full border border-[var(--border-line)] hover:border-[var(--color-sandhanam)] bg-[var(--bg-surface)] hover:bg-[var(--bg-raised)]/30 rounded-2xl p-6 flex flex-col justify-between transition-colors duration-150 cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-sandhanam)] active:scale-[0.99]"
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--color-sandhanam-light)] text-[var(--color-sandhanam)] flex items-center justify-center shrink-0">
                    <Banknote className="w-5 h-5" />
                  </div>
                  <h3 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.numeral.title}
                  </h3>
                </div>

                <p className="text-xs text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.numeral.desc}
                </p>

                {/* Practical Cheque Notation Preview */}
                <div className="rounded-xl bg-[var(--bg-raised)] p-3.5 border border-[var(--border-line)] space-y-1">
                  <span className="text-[11px] font-mono-tamil text-[var(--color-muted)] block">
                    125000 INR
                  </span>
                  <p className="text-xs font-tamil font-semibold text-[var(--color-mai)] truncate">
                    ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய் மட்டும்
                  </p>
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between border-t border-[var(--border-line)] mt-4">
                <span className="text-xs font-semibold text-[var(--color-sandhanam)] font-tamil">
                  {t.hub.launchTool}
                </span>
                <ArrowRight className="w-4 h-4 text-[var(--color-sandhanam)]" />
              </div>
            </div>
          </div>

          {/* Bento Slot 3: Solar Calendar & Panchangam (Col 1-4) */}
          <div className="lg:col-span-4">
            <div
              onClick={() => onSelectTool("public", "calendar")}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectTool("public", "calendar");
                }
              }}
              role="button"
              tabIndex={0}
              className="h-full border border-[var(--border-line)] hover:border-[var(--color-semman)] bg-[var(--bg-surface)] hover:bg-[var(--bg-raised)]/30 rounded-2xl p-6 flex flex-col justify-between transition-colors duration-150 cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] active:scale-[0.99]"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center shrink-0">
                    <Calendar className="w-5 h-5" />
                  </div>
                  <h3 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.calendar.title}
                  </h3>
                </div>

                <p className="text-xs text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.calendar.desc}
                </p>

                <div className="text-xs font-tamil text-[var(--color-muted)] pt-1">
                  60-ஆண்டு சுழற்சி • திருக்கணித சூரிய மாதம்
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between border-t border-[var(--border-line)] mt-4">
                <span className="text-xs font-semibold text-[var(--color-semman)] font-tamil">
                  {t.hub.launchTool}
                </span>
                <ArrowRight className="w-4 h-4 text-[var(--color-semman)]" />
              </div>
            </div>
          </div>

          {/* Bento Slot 4: Agara Varisai Sorter (Col 5-8) */}
          <div className="lg:col-span-4">
            <div
              onClick={() => onSelectTool("public", "sorter")}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectTool("public", "sorter");
                }
              }}
              role="button"
              tabIndex={0}
              className="h-full border border-[var(--border-line)] hover:border-[var(--color-semman)] bg-[var(--bg-surface)] hover:bg-[var(--bg-raised)]/30 rounded-2xl p-6 flex flex-col justify-between transition-colors duration-150 cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-semman)] active:scale-[0.99]"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--color-semman-light)] text-[var(--color-semman)] flex items-center justify-center shrink-0">
                    <ArrowDownAZ className="w-5 h-5" />
                  </div>
                  <h3 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.sorter.title}
                  </h3>
                </div>

                <p className="text-xs text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.sorter.desc}
                </p>

                <div className="text-xs font-tamil text-[var(--color-muted)] pt-1">
                  அகரவரிசை: உயிர் (அ..ஔ) → மெய் → உயிர்மெய்
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between border-t border-[var(--border-line)] mt-4">
                <span className="text-xs font-semibold text-[var(--color-semman)] font-tamil">
                  {t.hub.launchTool}
                </span>
                <ArrowRight className="w-4 h-4 text-[var(--color-semman)]" />
              </div>
            </div>
          </div>

          {/* Bento Slot 5: Traditional Fractions & Symbols (Col 9-12) */}
          <div className="lg:col-span-4">
            <div
              onClick={() => onSelectTool("public", "symbols")}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectTool("public", "symbols");
                }
              }}
              role="button"
              tabIndex={0}
              className="h-full border border-[var(--border-line)] hover:border-[var(--color-sandhanam)] bg-[var(--bg-surface)] hover:bg-[var(--bg-raised)]/30 rounded-2xl p-6 flex flex-col justify-between transition-colors duration-150 cursor-pointer text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-sandhanam)] active:scale-[0.99]"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--color-sandhanam-light)] text-[var(--color-sandhanam)] flex items-center justify-center shrink-0">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <h3 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
                    {t.tools.symbols.title}
                  </h3>
                </div>

                <p className="text-xs text-[var(--color-muted)] font-tamil-sans leading-relaxed">
                  {t.tools.symbols.desc}
                </p>

                <div className="rounded-xl bg-[var(--bg-raised)] p-2.5 border border-[var(--border-line)] flex items-center justify-around font-tamil font-bold text-base text-[var(--color-mai)]">
                  <span>𑿀 (1/80)</span>
                  <span>𑿈 (1/16)</span>
                  <span>𑿒 (1/4)</span>
                  <span>𑿔 (3/4)</span>
                </div>
              </div>

              <div className="pt-4 flex items-center justify-between border-t border-[var(--border-line)] mt-4">
                <span className="text-xs font-semibold text-[var(--color-sandhanam)] font-tamil">
                  {t.hub.launchTool}
                </span>
                <ArrowRight className="w-4 h-4 text-[var(--color-sandhanam)]" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Integrated Developer Diagnostic Console */}
      <section className="space-y-4 pt-2">
        <div className="flex items-center justify-between border-b border-[var(--border-line)] pb-2">
          <h2 className="text-base sm:text-lg font-tamil font-bold text-[var(--color-mai)]">
            {t.tabs.devTools}
          </h2>
          <span className="text-xs text-[var(--color-muted)] font-tamil-sans">
            {t.hub.devToolsHeading}
          </span>
        </div>

        <div className="border border-[var(--border-line)] bg-[var(--bg-surface)] rounded-2xl divide-y divide-[var(--border-line)] overflow-hidden shadow-xs">
          {/* Diagnostic Item: Scalar Inspector */}
          <div
            onClick={() => onSelectTool("dev", "scalar")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "scalar");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.scalar.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.scalar.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Diagnostic Item: Letter & Syllable Analyzer */}
          <div
            onClick={() => onSelectTool("dev", "letter")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "letter");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.letter.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.letter.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Diagnostic Item: Unicode Text Normalizer */}
          <div
            onClick={() => onSelectTool("dev", "normalizer")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "normalizer");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.normalizer.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.normalizer.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Diagnostic Item: Dispatcher Sandbox */}
          <div
            onClick={() => onSelectTool("dev", "dispatcher")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "dispatcher");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <Terminal className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.dispatcher.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.dispatcher.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Diagnostic Item: Code Generator */}
          <div
            onClick={() => onSelectTool("dev", "codegen")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "codegen");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <Code2 className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.codegen.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.codegen.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>

          {/* Diagnostic Item: Batch Processor */}
          <div
            onClick={() => onSelectTool("dev", "batch")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelectTool("dev", "batch");
              }
            }}
            role="button"
            tabIndex={0}
            className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-[var(--bg-raised)]/50 transition-colors duration-120 cursor-pointer focus-visible:outline-none focus-visible:bg-[var(--bg-raised)]"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--bg-raised)] text-[var(--color-sandhanam)] border border-[var(--border-line)] flex items-center justify-center shrink-0">
                <Files className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-tamil font-bold text-[var(--color-mai)]">
                  {t.tools.batch.title}
                </h4>
                <p className="text-xs text-[var(--color-muted)] font-tamil-sans line-clamp-1 mt-0.5">
                  {t.tools.batch.desc}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 self-end sm:self-center text-xs font-tamil text-[var(--color-sandhanam)] font-semibold shrink-0">
              <span>{t.actions.inspect}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
