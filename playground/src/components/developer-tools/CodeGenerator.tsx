import { useState } from "react";
import { useLanguage } from "../../lib/i18n";
import { ToolHeader } from "../common/ToolHeader";
import { Card } from "../ui/card";
import { CopyButton } from "../common/CopyButton";
import { Code2, Terminal } from "lucide-react";

type LangKey = "typescript" | "python" | "rust" | "dart";
type SnippetCategory =
  | "codec"
  | "numeral"
  | "calendar"
  | "lexicon"
  | "hyphenator"
  | "normalizer"
  | "sorter"
  | "tokenizer"
  | "punarchi";

const SNIPPETS: Record<
  LangKey,
  {
    name: string;
    install: string;
    examples: Record<SnippetCategory, string>;
  }
> = {
  typescript: {
    name: "TypeScript / Web",
    install: "npm install tamil-toolkit",
    examples: {
      codec: `import { bamini_to_unicode, detect_encoding } from "tamil-toolkit";

const legacyText = "jkpo; nkhop";
const unicode = bamini_to_unicode(legacyText, "preserve");
console.log(unicode); // "தமிழ் மொழி"`,
      numeral: `import { currency_to_words } from "tamil-toolkit";

const inr = currency_to_words(12500000, "INR", "TN");
const lkr = currency_to_words(12500000, "LKR", "SL");
console.log({ inr, lkr });`,
      calendar: `import { gregorian_to_tamil_date, panchangam_day } from "tamil-toolkit";

const context = {
  region: "SL" as const,
  latitude_microdegrees: 9661500,
  longitude_microdegrees: 80025500,
  elevation_meters: 5,
  time_zone: "Asia/Colombo",
};
const tamilDate = gregorian_to_tamil_date({ year: 2026, month: 4, day: 14 }, context);
console.log(tamilDate.tamil_date.month_name, tamilDate.tamil_date.day);`,
      lexicon: `import { lexicon_lookup } from "tamil-toolkit";

const res = lexicon_lookup("நன்றி");
console.log(res.entry?.senses[0]?.gloss_en);`,
      hyphenator: `import { hyphenate_word } from "tamil-toolkit";

const res = hyphenate_word("திருவள்ளுவர்", "-", 2, 2);
console.log(res.hyphenated);`,
      normalizer: `import { repair_tamil_text, fold_for_search } from "tamil-toolkit";

const repaired = repair_tamil_text("தமிழ்");
const folded = fold_for_search("பழம்", "comprehensive");
console.log(repaired.text, folded);`,
      sorter: `import { sort_words, compare } from "tamil-toolkit";

const sorted = sort_words(["பாரதி", "அகத்தியர்", "கம்பர்"], "agara-v1");
console.log(sorted, compare("அகத்தியர்", "கம்பர்", "agara-v1"));`,
      tokenizer: `import { tokenize_words, segment_sentences } from "tamil-toolkit";

const text = "திரு. குமார் மற்றும் ரூ.100 வந்தது.";
console.log(tokenize_words(text, "conservative"));
console.log(segment_sentences(text));`,
      punarchi: `import { punarchi_join, punarchi_split_candidates } from "tamil-toolkit";

const joined = punarchi_join("மரம்", "ஐ", {
  context: { relation: "vetrumai", subtype: "case_2" },
});
console.log(joined.surface, joined.steps.map((s) => s.sutra)); // "மரத்தை", [219, 244, 252, 164, 204]
console.log(punarchi_split_candidates("செந்தாமரை"));`,
    },
  },
  python: {
    name: "Python 3.10+",
    install: "pip install tamil-toolkit",
    examples: {
      codec: `from tamil_toolkit import bamini_to_unicode

legacy_text = "jkpo; nkhop"
unicode_text = bamini_to_unicode(legacy_text)
print(unicode_text)  # "தமிழ் மொழி"`,
      numeral: `from tamil_toolkit import currency_to_words

inr = currency_to_words(12500000, "INR", "TN")
lkr = currency_to_words(12500000, "LKR", "SL")
print(inr, lkr)`,
      calendar: `from tamil_toolkit import gregorian_to_tamil_date

tamil_date = gregorian_to_tamil_date(
    {"year": 2026, "month": 4, "day": 14},
    {
        "region": "SL",
        "latitude_microdegrees": 9661500,
        "longitude_microdegrees": 80025500,
        "elevation_meters": 5,
        "time_zone": "Asia/Colombo",
    },
)
print(tamil_date["tamil_date"]["month_name"], tamil_date["tamil_date"]["day"])`,
      lexicon: `from tamil_toolkit import lexicon_lookup

result = lexicon_lookup("நன்றி")
print(result)`,
      hyphenator: `from tamil_toolkit import hyphenate_word

result = hyphenate_word("திருவள்ளுவர்", delimiter="-", left_min=2, right_min=2)
print(result["hyphenated"])`,
      normalizer: `from tamil_toolkit import repair_tamil_text, fold_for_search

repaired = repair_tamil_text("தமிழ்")
folded = fold_for_search("பழம்", profile="comprehensive")
print(repaired["text"], folded)`,
      sorter: `from tamil_toolkit import sort_words, compare

words = sort_words(["பாரதி", "அகத்தியர்", "கம்பர்"], profile="agara-v1")
print(words, compare("அகத்தியர்", "கம்பர்", profile="agara-v1"))`,
      tokenizer: `from tamil_toolkit import tokenize_words, segment_sentences

text = "திரு. குமார் மற்றும் ரூ.100 வந்தது."
print(tokenize_words(text, stopword_profile="conservative"))
print(segment_sentences(text))`,
      punarchi: `from tamil_toolkit import punarchi_join, punarchi_split_candidates

res = punarchi_join("மரம்", "ஐ", context={"relation": "vetrumai", "subtype": "case_2"})
print(res["surface"], [s["sutra"] for s in res["steps"]])  # மரத்தை
print(punarchi_split_candidates("செந்தாமரை"))`,
    },
  },
  rust: {
    name: "Rust (Cargo)",
    install: 'cargo add tamil-toolkit --features "all"',
    examples: {
      codec: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"bamini_to_unicode","input":{"text":"jkpo; nkhop","errors":"preserve"}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      numeral: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"currency_to_words","input":{"amount_minor":12500000,"currency":"LKR","locale":"SL"}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      calendar: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"gregorian_to_tamil_date","input":{"date":{"year":2026,"month":4,"day":14},"context":{"region":"SL","latitude_microdegrees":9661500,"longitude_microdegrees":80025500,"elevation_meters":5,"time_zone":"Asia/Colombo"}}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      lexicon: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"lexicon_lookup","input":"நன்றி"}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      hyphenator: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"hyphenate_word","input":{"word":"திருவள்ளுவர்","delimiter":"-","left_min":2,"right_min":2}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      normalizer: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"repair_tamil_text","input":{"text":"தமிழ்"}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      sorter: `use tamil_toolkit::execute_json;

fn main() {
    let req = r#"{"op":"sort_words","input":{"words":["பாரதி","அகத்தியர்","கம்பர்"],"profile":"agara-v1"}}"#;
    println!("{}", execute_json(req).unwrap());
}`,
      tokenizer: `use tamil_toolkit::tokenize::{segment_sentences, tokenize_words, StopwordProfile};

fn main() {
    let text = "திரு. குமார் மற்றும் ரூ.100 வந்தது.";
    println!("{:?}", tokenize_words(text, StopwordProfile::Conservative));
    println!("{:?}", segment_sentences(text));
}`,
      punarchi: `use tamil_toolkit::punarchi::{
    punarchi_join, punarchi_split_candidates, ContextSubtype, GrammaticalRelation,
    PunarchiContext, PunarchiProfile,
};

fn main() {
    let ctx = PunarchiContext {
        relation: GrammaticalRelation::Vetrumai,
        subtype: Some(ContextSubtype::Case2),
        ..Default::default()
    };
    let res = punarchi_join("மரம்", "ஐ", &ctx, PunarchiProfile::NannoolV1).unwrap();
    println!("{} {:?}", res.surface, res.steps);
    println!("{:?}", punarchi_split_candidates("செந்தாமரை", PunarchiProfile::NannoolV1, false));
}`,
    },
  },
  dart: {
    name: "Dart / Flutter",
    install: "dart pub add tamil_toolkit",
    examples: {
      codec: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final unicode = toolkit.baminiToUnicode("jkpo; nkhop");
  print(unicode);
}`,
      numeral: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final lkr = toolkit.currencyToWords(12500000, "LKR", "SL");
  print(lkr);
}`,
      calendar: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final date = toolkit.gregorianToTamilDate(
    {'year': 2026, 'month': 4, 'day': 14},
    CalendarContext(
      region: 'SL',
      latitudeMicrodegrees: 9661500,
      longitudeMicrodegrees: 80025500,
      elevationMeters: 5,
      timeZone: 'Asia/Colombo',
    ),
  );
  print(date);
}`,
      lexicon: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final res = toolkit.lexiconLookup("நன்றி");
  print(res);
}`,
      hyphenator: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final res = toolkit.hyphenateWord("திருவள்ளுவர்", delimiter: "-");
  print(res['hyphenated']);
}`,
      normalizer: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final res = toolkit.execute({
    'op': 'repair_tamil_text',
    'input': {'text': 'தமிழ்'},
  });
  print(res);
}`,
      sorter: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final sorted = toolkit.sortWords(["பாரதி", "அகத்தியர்", "கம்பர்"]);
  print(sorted);
}`,
      tokenizer: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final text = "திரு. குமார் மற்றும் ரூ.100 வந்தது.";
  print(toolkit.tokenizeWords(text, stopwordProfile: 'conservative'));
  print(toolkit.segmentSentences(text));
}`,
      punarchi: `import 'package:tamil_toolkit/tamil_toolkit.dart';

void main() {
  final toolkit = TamilToolkit();
  final joined = toolkit.punarchiJoin(
    "மரம்",
    "ஐ",
    context: {'relation': 'vetrumai', 'subtype': 'case_2'},
  );
  print(joined['surface']); // மரத்தை
  print(toolkit.punarchiSplitCandidates("செந்தாமரை"));
}`,
    },
  },
};

export function CodeGenerator() {
  const { t } = useLanguage();

  const [activeLang, setActiveLang] = useState<LangKey>("typescript");
  const [activeCategory, setActiveCategory] = useState<SnippetCategory>("codec");

  const current = SNIPPETS[activeLang];
  const activeCode = current.examples[activeCategory];

  const categories: { id: SnippetCategory; label: string }[] = [
    { id: "codec", label: t.tools.codegen.tabCodec },
    { id: "numeral", label: t.tools.codegen.tabNumeral },
    { id: "calendar", label: t.tools.codegen.tabCalendar },
    { id: "lexicon", label: t.tools.codegen.tabLexicon },
    { id: "hyphenator", label: t.tools.codegen.tabHyphenator },
    { id: "normalizer", label: t.tools.codegen.tabNormalizer },
    { id: "sorter", label: t.tools.codegen.tabSorter },
    { id: "tokenizer", label: t.tools.codegen.tabTokenizer },
    { id: "punarchi", label: t.tools.codegen.tabPunarchi },
  ];

  return (
    <div className="space-y-6">
      <ToolHeader
        title={t.tools.codegen.title}
        description={t.tools.codegen.desc}
      />

      {/* Language Tabs */}
      <div className="inline-flex flex-wrap items-center gap-1 p-1 rounded-xl bg-[var(--bg-raised)] border border-[var(--border-line)]">
        {(["typescript", "python", "rust", "dart"] as LangKey[]).map((lang) => (
          <button
            key={lang}
            type="button"
            onClick={() => setActiveLang(lang)}
            className={`px-3.5 py-1.5 min-h-[36px] rounded-lg text-xs font-medium whitespace-nowrap transition-colors cursor-pointer ${
              activeLang === lang
                ? "bg-[var(--bg-surface)] text-[var(--color-semman)] font-semibold shadow-xs"
                : "text-[var(--color-muted)] hover:text-[var(--color-mai)]"
            }`}
          >
            {SNIPPETS[lang].name}
          </button>
        ))}
      </div>

      {/* Install Command Card */}
      <Card className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Terminal className="w-4 h-4 text-[var(--color-semman)] shrink-0" />
          <span className="text-xs font-semibold text-[var(--color-muted)] uppercase">
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
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-line)] pb-3">
          <div className="flex items-center gap-2">
            <Code2 className="w-4 h-4 text-[var(--color-sandhanam)]" />
            <span className="text-sm font-semibold text-[var(--color-mai)]">
              {t.tools.codegen.snippetHeading}
            </span>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            {categories.map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setActiveCategory(cat.id)}
                className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                  activeCategory === cat.id
                    ? "bg-[var(--color-semman)] text-[#faf7f2] border-[var(--color-semman)] font-semibold"
                    : "bg-[var(--bg-canvas)] border-[var(--border-line)] text-[var(--color-mai)] hover:border-[var(--color-semman)]"
                }`}
              >
                {cat.label}
              </button>
            ))}
            <CopyButton text={activeCode} size="sm" variant="outline" />
          </div>
        </div>

        <pre className="p-4 rounded-xl bg-[var(--bg-canvas)] border border-[var(--border-line)] font-mono-tamil text-xs sm:text-sm text-[var(--color-mai)] overflow-x-auto leading-relaxed">
          <code>{activeCode}</code>
        </pre>
      </Card>
    </div>
  );
}
