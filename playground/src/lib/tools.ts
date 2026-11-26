import type { Translations } from "./i18n";
import { findPrimarySeoPageByToolId, findSeoPageByPath } from "./seo-pages";

export const IS_PUBLIC_BETA =
  import.meta.env.VITE_PUBLIC_BETA === "1" || import.meta.env.VITE_PUBLIC_BETA === "true";

export function resolveLexiconViewMode(
  search: string,
  isPublicBeta: boolean = IS_PUBLIC_BETA
): "verified" | "historical" {
  if (isPublicBeta) return "verified";
  const param = new URLSearchParams(search).get("mode");
  return param === "historical" ? "historical" : "verified";
}

export type ToolId =
  | "lexicon"
  | "sorter"
  | "letter"
  | "tokenizer"
  | "codec"
  | "translit"
  | "normalizer"
  | "hyphenator"
  | "batch"
  | "numeral"
  | "calendar"
  | "symbols"
  | "scalar"
  | "dispatcher"
  | "codegen";

export type ToolGroupId = "words" | "writing" | "reference" | "developer";

export type ToolIconKey =
  | "book-marked"
  | "arrow-down-az"
  | "letter-a"
  | "scan-text"
  | "type"
  | "languages"
  | "shield-check"
  | "scissors"
  | "files"
  | "banknote"
  | "calendar"
  | "book-open"
  | "cpu"
  | "terminal"
  | "code-2";

export interface ToolMeta {
  id: ToolId;
  group: ToolGroupId;
  icon: ToolIconKey;
  keywords: readonly string[];
}

export interface ToolGroupMeta {
  id: ToolGroupId;
}

export const TOOL_GROUPS: readonly ToolGroupMeta[] = [
  { id: "words" },
  { id: "writing" },
  { id: "reference" },
  { id: "developer" }
];

export const TOOLS: readonly ToolMeta[] = [
  // Dictionary & Words
  {
    id: "lexicon",
    group: "words",
    icon: "book-marked",
    keywords: [
      "dictionary",
      "lexicon",
      "word",
      "meaning",
      "wiktionary",
      "jaffna",
      "tamil",
      ...(IS_PUBLIC_BETA ? [] : ["historical"]),
      "அகராதி",
      "சொல்",
      "பொருள்",
      "சொற்களஞ்சியம்"
    ]
  },
  {
    id: "sorter",
    group: "words",
    icon: "arrow-down-az",
    keywords: [
      "sort",
      "alphabetical",
      "agara",
      "varisai",
      "collation",
      "list",
      "அகர",
      "வரிசை"
    ]
  },
  {
    id: "letter",
    group: "words",
    icon: "letter-a",
    keywords: [
      "letter",
      "syllable",
      "uyir",
      "mei",
      "uyirmei",
      "grantha",
      "maathirai",
      "mora",
      "எழுத்து",
      "உயிர்",
      "மெய்",
      "உயிர்மெய்"
    ]
  },
  {
    id: "tokenizer",
    group: "words",
    icon: "scan-text",
    keywords: [
      "tokenize",
      "tokenizer",
      "word",
      "sentence",
      "segment",
      "abbreviation",
      "stopword",
      "offset",
      "span",
      "nlp",
      "சொற்பிரிப்பு",
      "தொடர்",
      "சுருக்கம்"
    ]
  },

  // Writing & Conversion
  {
    id: "codec",
    group: "writing",
    icon: "type",
    keywords: [
      "font",
      "encoding",
      "converter",
      "bamini",
      "tscii",
      "tab",
      "tam",
      "anjal",
      "vanavil",
      "lt-tm",
      "senthamil",
      "shree-tam",
      "softview",
      "tbo",
      "braille",
      "unicode",
      "பாமினி",
      "பிரெய்லி",
      "எழுத்துரு",
      "மாற்றி"
    ]
  },
  {
    id: "translit",
    group: "writing",
    icon: "languages",
    keywords: [
      "transliteration",
      "translit",
      "romanize",
      "iso-15919",
      "madras-lexicon",
      "itrans",
      "harvard-kyoto",
      "tamil99",
      "anjal",
      "tanglish",
      "phonetic",
      "keyboard",
      "ஒலிபெயர்ப்பு",
      "தமிழ்99",
      "தட்டச்சு"
    ]
  },
  {
    id: "normalizer",
    group: "writing",
    icon: "shield-check",
    keywords: [
      "unicode",
      "normalize",
      "repair",
      "clean",
      "pulli",
      "kombu",
      "nfc",
      "nfd",
      "fold",
      "சீரமைப்பு",
      "பிழைதிருத்தம்",
      "ஒருங்குறி"
    ]
  },
  {
    id: "hyphenator",
    group: "writing",
    icon: "scissors",
    keywords: [
      "hyphen",
      "syllable",
      "wrap",
      "line",
      "soft hyphen",
      "otru",
      "libreoffice",
      "indesign",
      "அசை",
      "பத்தி",
      "வரி"
    ]
  },
  {
    id: "batch",
    group: "writing",
    icon: "files",
    keywords: [
      "batch",
      "file",
      "csv",
      "txt",
      "document",
      "bulk",
      "கோப்பு",
      "தொகுதி"
    ]
  },

  // Numbers & Calendar
  {
    id: "numeral",
    group: "reference",
    icon: "banknote",
    keywords: [
      "number",
      "words",
      "cheque",
      "currency",
      "rupee",
      "inr",
      "lkr",
      "sri lanka",
      "tamil",
      "எண்",
      "காசோலை",
      "ரூபாய்",
      "பணம்"
    ]
  },
  {
    id: "calendar",
    group: "reference",
    icon: "calendar",
    keywords: [
      "calendar",
      "panchangam",
      "date",
      "rahu",
      "yamagandam",
      "kuligai",
      "nakshatra",
      "tithi",
      "thiruvalluvar",
      "jaffna",
      "chennai",
      "colombo",
      "holiday",
      "நாட்காட்டி",
      "பஞ்சாங்கம்",
      "ராகு",
      "நட்சத்திரம்",
      "திதி"
    ]
  },
  {
    id: "symbols",
    group: "reference",
    icon: "book-open",
    keywords: [
      "fraction",
      "symbol",
      "munthiri",
      "kani",
      "veesam",
      "measure",
      "traditional",
      "பின்னம்",
      "குறியீடு",
      "முந்திரி",
      "காணி"
    ]
  },

  // Developer
  {
    id: "scalar",
    group: "developer",
    icon: "cpu",
    keywords: [
      "scalar",
      "codepoint",
      "hex",
      "zwj",
      "zwnj",
      "grapheme",
      "utf8",
      "அலகு",
      "ஒருங்குறி"
    ]
  },
  {
    id: "dispatcher",
    group: "developer",
    icon: "terminal",
    keywords: [
      "dispatcher",
      "json",
      "rpc",
      "wasm",
      "api",
      "sandbox",
      "ஆய்வகம்"
    ]
  },
  {
    id: "codegen",
    group: "developer",
    icon: "code-2",
    keywords: [
      "code",
      "snippet",
      "rust",
      "python",
      "typescript",
      "dart",
      "sdk",
      "நிரல்"
    ]
  }
];

const TOOL_ID_SET = new Set<string>(TOOLS.map((item) => item.id));

export function isValidToolId(value: string | null | undefined): value is ToolId {
  return Boolean(value && TOOL_ID_SET.has(value));
}

export function resolveToolFromSearch(search: string): ToolId | "home" {
  try {
    const params = new URLSearchParams(search);
    const raw = params.get("tool");
    if (isValidToolId(raw)) {
      return raw;
    }
  } catch {
    // Ignore malformed query string
  }
  return "home";
}

export function resolveToolFromLocation(pathname: string, search: string): ToolId | "home" {
  const seoPage = findSeoPageByPath(pathname);
  if (seoPage) {
    return seoPage.toolId;
  }
  return resolveToolFromSearch(search);
}

export function getToolHref(id: ToolId | "home"): string {
  if (id === "home") return "/";
  const seoPage = findPrimarySeoPageByToolId(id);
  return seoPage ? `/tools/${seoPage.slug}/` : `/?tool=${id}`;
}

export function getToolMeta(id: ToolId): ToolMeta {
  const found = TOOLS.find((t) => t.id === id);
  return found ?? TOOLS[0];
}

export function getToolCopy(id: ToolId, t: Translations): { title: string; desc: string } {
  return t.tools[id];
}

export function filterToolsByQuery(query: string, t: Translations): ToolMeta[] {
  const trimmed = query.trim().toLowerCase();
  if (!trimmed) return [...TOOLS];

  return TOOLS.filter((tool) => {
    const copy = getToolCopy(tool.id, t);
    if (tool.id.toLowerCase().includes(trimmed)) return true;
    if (copy.title.toLowerCase().includes(trimmed)) return true;
    if (copy.desc.toLowerCase().includes(trimmed)) return true;
    return tool.keywords.some((kw) => kw.toLowerCase().includes(trimmed));
  });
}
