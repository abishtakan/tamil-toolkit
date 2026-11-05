import { useState } from "react";
import { useLanguage } from "../../lib/i18n";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { CopyButton } from "../common/CopyButton";
import { Code2, Terminal } from "lucide-react";

type LangKey = "typescript" | "python" | "rust" | "dart";

const SNIPPETS: Record<
  LangKey,
  {
    name: string;
    install: string;
    codecExample: string;
    numeralExample: string;
    calendarExample: string;
  }
> = {
  typescript: {
    name: "TypeScript / Node.js & Web",
    install: "npm install tamil-toolkit",
    codecExample: `import { bamini_to_unicode, detect_encoding } from "tamil-toolkit";

// Auto-detect & convert
const legacyText = "jkpo; nkhop";
const unicode = bamini_to_unicode(legacyText);
console.log(unicode); // "தமிழ் மொழி"`,
    numeralExample: `import { currency_to_words } from "tamil-toolkit";

const words = currency_to_words(125000);
console.log(words); // "ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய்"`,
    calendarExample: `import { gregorian_to_tamil_date } from "tamil-toolkit";

const tamilDate = gregorian_to_tamil_date(2026, 11, 5);
console.log(tamilDate.tamil_month_name, tamilDate.tamil_day);`
  },
  python: {
    name: "Python (CPython 3.10+)",
    install: "pip install tamil-toolkit",
    codecExample: `from tamil_toolkit import bamini_to_unicode, detect_encoding

legacy_text = "jkpo; nkhop"
unicode_text = bamini_to_unicode(legacy_text)
print(unicode_text) # "தமிழ் மொழி"`,
    numeralExample: `from tamil_toolkit import currency_to_words

words = currency_to_words(125000)
print(words) # "ஒரு இலட்சத்து இருபத்தைந்தாயிரம் ரூபாய்"`,
    calendarExample: `from tamil_toolkit import gregorian_to_tamil_date

tamil_date = gregorian_to_tamil_date(2026, 11, 5)
print(f"{tamil_date['tamil_month_name']} {tamil_date['tamil_day']}")`
  },
  rust: {
    name: "Rust (Cargo)",
    install: 'cargo add tamil-toolkit --features "all"',
    codecExample: `use tamil_toolkit::codec::bamini_to_unicode;

fn main() {
    let legacy = "jkpo; nkhop";
    let unicode = bamini_to_unicode(legacy);
    println!("{}", unicode); // "தமிழ் மொழி"
}`,
    numeralExample: `use tamil_toolkit::numerals::currency_to_words;

fn main() {
    let words = currency_to_words(125000.0, None).unwrap();
    println!("{}", words);
}`,
    calendarExample: `use tamil_toolkit::calendar::gregorian_to_tamil_date;

fn main() {
    let date = gregorian_to_tamil_date(2026, 11, 5).unwrap();
    println!("{} {}", date.tamil_month_name, date.tamil_day);
}`
  },
  dart: {
    name: "Dart / Flutter",
    install: "dart pub add tamil_toolkit",
    codecExample: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final unicode = toolkit.baminiToUnicode("jkpo; nkhop");
  print(unicode);
}`,
    numeralExample: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final words = toolkit.currencyToWords(125000);
  print(words);
}`,
    calendarExample: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final date = toolkit.gregorianToTamilDate(2026, 11, 5);
  print("\${date.monthName} \${date.day}");
}`
  }
};

export function CodeGenerator() {
  const { t, language } = useLanguage();

  const [activeLang, setActiveLang] = useState<LangKey>("typescript");
  const [activeCategory, setActiveCategory] = useState<"codec" | "numeral" | "calendar">("codec");

  const current = SNIPPETS[activeLang];
  const activeCode =
    activeCategory === "codec"
      ? current.codecExample
      : activeCategory === "numeral"
      ? current.numeralExample
      : current.calendarExample;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[var(--border-line)]">
        <div>
          <h2 className="text-xl sm:text-2xl font-tamil font-bold text-[var(--color-mai)]">
            {t.tools.codegen.title}
          </h2>
          <p className="text-xs sm:text-sm text-[var(--color-muted)] font-tamil-sans mt-1">
            {t.tools.codegen.desc}
          </p>
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
          {(["typescript", "python", "rust", "dart"] as LangKey[]).map((lang) => (
            <button
              key={lang}
              onClick={() => setActiveLang(lang)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all border ${
                activeLang === lang
                  ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold shadow-sm"
                  : "bg-[var(--bg-surface)] text-[var(--color-mai)] border-[var(--border-line)] hover:border-[var(--color-semman)]"
              }`}
            >
              {SNIPPETS[lang].name}
            </button>
          ))}
        </div>
      </div>

      {/* Install Command Card */}
      <Card className="bg-[var(--bg-surface)] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
          <span className="text-xs font-semibold text-[var(--color-muted)] font-tamil uppercase">
            {t.tools.codegen.installCommand}:
          </span>
          <code className="text-xs sm:text-sm font-mono-tamil font-semibold text-[var(--color-mai)] bg-[var(--bg-raised)] px-2.5 py-1 rounded-lg">
            {current.install}
          </code>
        </div>
        <CopyButton text={current.install} size="sm" variant="outline" />
      </Card>

      {/* Code Example View */}
      <Card className="p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-line)] pb-3">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-[var(--color-sandhanam)]" />
            <span className="text-sm font-tamil font-semibold text-[var(--color-mai)]">
              {language === "en" ? "Integration Snippet (Example Code)" : "மாதிரி நிரல் (Example Code Snippet)"}
            </span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant={activeCategory === "codec" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveCategory("codec")}
              className="text-xs font-tamil"
            >
              {language === "en" ? "Font Converter" : "எழுத்துரு மாற்றி"}
            </Button>
            <Button
              variant={activeCategory === "numeral" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveCategory("numeral")}
              className="text-xs font-tamil"
            >
              {language === "en" ? "Numerals & Words" : "எண் - சொல்"}
            </Button>
            <Button
              variant={activeCategory === "calendar" ? "primary" : "outline"}
              size="sm"
              onClick={() => setActiveCategory("calendar")}
              className="text-xs font-tamil"
            >
              {language === "en" ? "Calendar" : "நாட்காட்டி"}
            </Button>
            <CopyButton text={activeCode} size="sm" variant="ghost" />
          </div>
        </div>

        <div className="relative">
          <pre className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-mono-tamil text-xs sm:text-sm text-[var(--color-mai)] overflow-x-auto leading-relaxed">
            <code>{activeCode}</code>
          </pre>
        </div>
      </Card>
    </div>
  );
}
