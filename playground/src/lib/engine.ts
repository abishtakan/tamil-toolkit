import { init } from "tamil-toolkit/web";
import * as tt from "tamil-toolkit/web";

export interface EngineStatus {
  isReady: boolean;
  isLoading: boolean;
  error: Error | null;
}

let initPromise: Promise<void> | null = null;
let isInitialized = false;

export async function initializeEngine(): Promise<void> {
  if (isInitialized) return;
  if (!initPromise) {
    initPromise = (async () => {
      try {
        await init();
        isInitialized = true;
      } catch (err) {
        initPromise = null;
        throw err;
      }
    })();
  }
  return initPromise;
}

export function isEngineReady(): boolean {
  return isInitialized;
}

// ---------------------------------------------------------------------------
// 1. Traditional Fractions & Epigraphical Symbols Types & Data
// ---------------------------------------------------------------------------

export interface TraditionalSymbol {
  codepoint: string;
  glyph: string;
  name_ta: string;
  name_en: string;
  category: "fraction" | "land" | "volume" | "currency";
  rational: {
    numerator: number;
    denominator: number;
  } | null;
  decimal_value: number | null;
  period_usage: string;
}

export const TRADITIONAL_SYMBOLS: TraditionalSymbol[] = [
  // Fractions (பின்னங்கள்)
  { codepoint: "U+11FC0", glyph: "𑿀", name_ta: "காணி", name_en: "Kani", category: "fraction", rational: { numerator: 1, denominator: 80 }, decimal_value: 0.0125, period_usage: "Classical inscriptional land & revenue fraction" },
  { codepoint: "U+11FC1", glyph: "𑿁", name_ta: "அரைக்காணி", name_en: "Araikkani", category: "fraction", rational: { numerator: 1, denominator: 160 }, decimal_value: 0.00625, period_usage: "Half of Kani (1/160)" },
  { codepoint: "U+11FC2", glyph: "𑿂", name_ta: "முந்திரி", name_en: "Munthiri", category: "fraction", rational: { numerator: 1, denominator: 320 }, decimal_value: 0.003125, period_usage: "Standard base fraction (1/320)" },
  { codepoint: "U+11FC3", glyph: "𑿃", name_ta: "கீழ்முந்திரி", name_en: "Keezh Mundhiri", category: "fraction", rational: { numerator: 1, denominator: 102400 }, decimal_value: 0.000009765625, period_usage: "Micro-fraction (1/320 of 1/320)" },
  { codepoint: "U+11FC8", glyph: "𑿈", name_ta: "மாகாணி (வீசம்)", name_en: "Makani / Veesam", category: "fraction", rational: { numerator: 1, denominator: 16 }, decimal_value: 0.0625, period_usage: "One sixteenth (1/16)" },
  { codepoint: "U+11FC9", glyph: "𑿉", name_ta: "அரைக்கால்", name_en: "Araikkal", category: "fraction", rational: { numerator: 1, denominator: 8 }, decimal_value: 0.125, period_usage: "One eighth (1/8)" },
  { codepoint: "U+11FCA", glyph: "𑿊", name_ta: "முக்கால்வீசம்", name_en: "Mukkal Veesam", category: "fraction", rational: { numerator: 3, denominator: 16 }, decimal_value: 0.1875, period_usage: "Three sixteenths (3/16)" },
  { codepoint: "U+11FCB", glyph: "𑿋", name_ta: "முக்காணி", name_en: "Mukkani", category: "fraction", rational: { numerator: 3, denominator: 80 }, decimal_value: 0.0375, period_usage: "Three Kanis (3/80)" },
  { codepoint: "U+11FCD", glyph: "𑿍", name_ta: "அரைமா", name_en: "Araima", category: "fraction", rational: { numerator: 1, denominator: 40 }, decimal_value: 0.025, period_usage: "Half of Ma (1/40)" },
  { codepoint: "U+11FCE", glyph: "𑿎", name_ta: "மா (ஒருமா)", name_en: "Oru Ma", category: "fraction", rational: { numerator: 1, denominator: 20 }, decimal_value: 0.05, period_usage: "One twentieth (1/20)" },
  { codepoint: "U+11FCF", glyph: "𑿏", name_ta: "இருமா", name_en: "Iruma", category: "fraction", rational: { numerator: 1, denominator: 10 }, decimal_value: 0.1, period_usage: "One tenth (1/10)" },
  { codepoint: "U+11FD0", glyph: "𑿐", name_ta: "மும்மா", name_en: "Mumma", category: "fraction", rational: { numerator: 3, denominator: 20 }, decimal_value: 0.15, period_usage: "Three twentieths (3/20)" },
  { codepoint: "U+11FD1", glyph: "𑿑", name_ta: "நான்மா", name_en: "Nanma", category: "fraction", rational: { numerator: 1, denominator: 5 }, decimal_value: 0.2, period_usage: "One fifth (1/5)" },
  { codepoint: "U+11FD2", glyph: "𑿒", name_ta: "கால்", name_en: "Kal (Quarter)", category: "fraction", rational: { numerator: 1, denominator: 4 }, decimal_value: 0.25, period_usage: "One quarter (1/4)" },
  { codepoint: "U+11FD3", glyph: "𑿓", name_ta: "அரை", name_en: "Arai (Half)", category: "fraction", rational: { numerator: 1, denominator: 2 }, decimal_value: 0.5, period_usage: "One half (1/2)" },
  { codepoint: "U+11FD4", glyph: "𑿔", name_ta: "முக்கால்", name_en: "Mukkal (Three Quarters)", category: "fraction", rational: { numerator: 3, denominator: 4 }, decimal_value: 0.75, period_usage: "Three quarters (3/4)" },

  // Land Measures (நில அளவை)
  { codepoint: "U+11FDE", glyph: "𑿞", name_ta: "குழி", name_en: "Kuzhi", category: "land", rational: null, decimal_value: null, period_usage: "Classical Tamil land survey area measure" },
  { codepoint: "U+11FDF", glyph: "𑿟", name_ta: "வேலி", name_en: "Veli", category: "land", rational: null, decimal_value: null, period_usage: "Equal to 2,000 Kuzhi (approx. 6.6 acres)" },

  // Volume Measures (முகத்தல் & தானிய அளவை)
  { codepoint: "U+11FD8", glyph: "𑿘", name_ta: "கலம்", name_en: "Kalam", category: "volume", rational: null, decimal_value: null, period_usage: "Grain dry capacity unit (approx. 34.5 kg or 12 Marakkal)" },
  { codepoint: "U+11FD9", glyph: "𑿙", name_ta: "பதக்கு", name_en: "Padhakku", category: "volume", rational: null, decimal_value: null, period_usage: "Dry capacity unit (2 Thooni or 1/3 Kalam)" },
  { codepoint: "U+11FDA", glyph: "𑿚", name_ta: "தூணி", name_en: "Thooni", category: "volume", rational: null, decimal_value: null, period_usage: "Dry capacity unit (approx. 4 Marakkal)" },
  { codepoint: "U+11FDB", glyph: "𑿛", name_ta: "நாழி", name_en: "Nazhi", category: "volume", rational: null, decimal_value: null, period_usage: "Daily domestic liquid/grain measure (4 Uzhakku)" },
  { codepoint: "U+11FDC", glyph: "𑿜", name_ta: "உழக்கு", name_en: "Uzhakku", category: "volume", rational: null, decimal_value: null, period_usage: "Domestic capacity unit (2 Aazhakku)" },
  { codepoint: "U+11FDD", glyph: "𑿝", name_ta: "ஆழாக்கு", name_en: "Aazhakku", category: "volume", rational: null, decimal_value: null, period_usage: "Base dry volume measure (approx. 168 ml)" },

  // Currency & Weights (நாணயம் & எடைகள்)
  { codepoint: "U+11FE0", glyph: "𑿠", name_ta: "நெல்", name_en: "Nel", category: "currency", rational: null, decimal_value: null, period_usage: "Base grain weight unit in Chola metallurgy" },
  { codepoint: "U+11FE1", glyph: "𑿡", name_ta: "கழஞ்சு", name_en: "Kazhanju", category: "currency", rational: null, decimal_value: null, period_usage: "Ancient gold coin weight unit (approx. 4.8 to 5.2 grams)" },
  { codepoint: "U+11FE2", glyph: "𑿢", name_ta: "காசு", name_en: "Kasu", category: "currency", rational: null, decimal_value: null, period_usage: "Chola & Pandyan coin denomination" },
  { codepoint: "U+11FE3", glyph: "𑿣", name_ta: "பணம்", name_en: "Panam", category: "currency", rational: null, decimal_value: null, period_usage: "Historic small coin fraction" },
  { codepoint: "U+11FE4", glyph: "𑿤", name_ta: "பொன்", name_en: "Pon", category: "currency", rational: null, decimal_value: null, period_usage: "Gold bullion / sovereign denomination" },
  { codepoint: "U+11FE5", glyph: "𑿥", name_ta: "வராகன்", name_en: "Varahan", category: "currency", rational: null, decimal_value: null, period_usage: "Gold pagoda sovereign coin" },
  { codepoint: "U+0BF9", glyph: "௹", name_ta: "ரூபாய்", name_en: "Rupee Sign", category: "currency", rational: null, decimal_value: null, period_usage: "Traditional Tamil rupee currency symbol" }
];

export function getSymbolInfo(char: string): TraditionalSymbol | null {
  const match = TRADITIONAL_SYMBOLS.find((s) => s.glyph === char || s.codepoint === char);
  if (match) return match;
  try {
    const raw = tt.execute({ op: "symbol_info", input: char }) as {
      codepoint: string;
      name: string;
      kind: string;
      rational?: { numerator: number; denominator: number } | null;
    };
    if (raw && raw.codepoint) {
      return {
        codepoint: raw.codepoint,
        glyph: char,
        name_ta: raw.name,
        name_en: raw.kind,
        category: "fraction",
        rational: raw.rational || null,
        decimal_value: raw.rational ? raw.rational.numerator / raw.rational.denominator : null,
        period_usage: "Unicode Tamil Supplement block"
      };
    }
  } catch {
    // Graceful fallback
  }
  return null;
}

// ---------------------------------------------------------------------------
// 2. Tamil Letter & Morphological Decomposition Types & Helpers
// ---------------------------------------------------------------------------

export type TamilCharKind =
  | "uyir"          // Pure vowel (அ, ஆ, ...)
  | "mei"           // Pure consonant with pulli (க், ங், ...)
  | "uyirmei"       // Syllabic consonant + vowel (க, கா, ...)
  | "aaytham"       // Visarga / Aytham (ஃ)
  | "grantha"       // Grantha consonant / syllable (ஜ, ஷ, ...)
  | "other";

export interface AnalyzedSyllable {
  index: number;
  raw: string;
  kind: TamilCharKind;
  base_consonant: string | null;
  vowel: string | null;
  vowel_sign: string | null;
  vowel_sign_name_ta: string | null;
  codepoints: string[];
}

export interface WordAnalysisReport {
  word: string;
  syllables: AnalyzedSyllable[];
  total_letters: number;
  vowel_count: number;
  consonant_count: number;
  uyirmei_count: number;
  grantha_count: number;
}

const NFD_O = String.fromCharCode(0x0bc6, 0x0bbe);
const NFD_OO = String.fromCharCode(0x0bc7, 0x0bbe);
const NFD_AU = String.fromCharCode(0x0bc6, 0x0bd7);

const VOWEL_SIGN_NAMES: Record<string, string> = {
  "\u0BBE": "துணைக்கால் (ஆ-காரக் குறி)",
  "\u0BBF": "மேல்விலங்கு (இ-காரக் குறி)",
  "\u0BC0": "சுழித்த மேல்விலங்கு (ஈ-காரக் குறி)",
  "\u0BC1": "கீழ்விலங்கு (உ-காரக் குறி)",
  "\u0BC2": "கீழ்விலங்கு சுழி (ஊ-காரக் குறி)",
  "\u0BC6": "ஒற்றைக்கொம்பு (எ-காரக் குறி)",
  "\u0BC7": "இரட்டைக்கொம்பு (ஏ-காரக் குறி)",
  "\u0BC8": "இணைக்கொம்பு (ஐ-காரக் குறி)",
  "\u0BCA": "ஒற்றைக்கொம்பு + துணைக்கால் (ஒ-காரக் குறி)",
  "\u0BCB": "இரட்டைக்கொம்பு + துணைக்கால் (ஓ-காரக் குறி)",
  "\u0BCC": "ஒற்றைக்கொம்பு + ளகர மெய்க்கூறு (ஔ-காரக் குறி)",
  [NFD_O]: "ஒற்றைக்கொம்பு + துணைக்கால் (ஒ-காரக் குறி / NFD)",
  [NFD_OO]: "இரட்டைக்கொம்பு + துணைக்கால் (ஓ-காரக் குறி / NFD)",
  [NFD_AU]: "ஒற்றைக்கொம்பு + ளகர மெய்க்கூறு (ஔ-காரக் குறி / NFD)"
};

const GRANTHA_CHARS = new Set(["ஜ", "ஷ", "ஸ", "ஹ", "க்ஷ", "ஶ்ரீ", "ஶ"]);

export function getLetters(text: string): string[] {
  if (!text) return [];
  try {
    const letters = tt.execute({ op: "get_letters", input: text }) as string[];
    if (Array.isArray(letters)) return letters;
  } catch {
    // Fallback grapheme splitting
  }
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    const segmenter = new Intl.Segmenter("ta", { granularity: "grapheme" });
    return Array.from(segmenter.segment(text)).map((s) => s.segment);
  }
  return Array.from(text);
}

const PULLI_CHAR = String.fromCharCode(0x0bcd);

const TAMIL_CONSONANTS_LIST: { base: string; mei: string }[] = [
  { base: "க்ஷ", mei: "க்ஷ்" },
  { base: "க", mei: "க்" },
  { base: "ங", mei: "ங்" },
  { base: "ச", mei: "ச்" },
  { base: "ஞ", mei: "ஞ்" },
  { base: "ட", mei: "ட்" },
  { base: "ண", mei: "ண்" },
  { base: "த", mei: "த்" },
  { base: "ந", mei: "ந்" },
  { base: "ப", mei: "ப்" },
  { base: "ம", mei: "ம்" },
  { base: "ய", mei: "ய்" },
  { base: "ர", mei: "ர்" },
  { base: "ல", mei: "ல்" },
  { base: "வ", mei: "வ்" },
  { base: "ழ", mei: "ழ்" },
  { base: "ள", mei: "ள்" },
  { base: "ற", mei: "ற்" },
  { base: "ன", mei: "ன்" },
  { base: "ஜ", mei: "ஜ்" },
  { base: "ஷ", mei: "ஷ்" },
  { base: "ஸ", mei: "ஸ்" },
  { base: "ஹ", mei: "ஹ்" }
];

const VOWEL_SIGNS_MAP: [string, string][] = [
  [NFD_O, "ஒ"],
  [NFD_OO, "ஓ"],
  [NFD_AU, "ஔ"],
  ["", "அ"],
  ["\u0BBE", "ஆ"],
  ["\u0BBF", "இ"],
  ["\u0BC0", "ஈ"],
  ["\u0BC1", "உ"],
  ["\u0BC2", "ஊ"],
  ["\u0BC6", "எ"],
  ["\u0BC7", "ஏ"],
  ["\u0BC8", "ஐ"],
  ["\u0BCA", "ஒ"],
  ["\u0BCB", "ஓ"],
  ["\u0BCC", "ஔ"]
];

export function splitUyirmeiJs(syllable: string): [string, string] | null {
  if (!syllable) return null;
  if (syllable.endsWith(PULLI_CHAR)) return null;

  for (const { base, mei } of TAMIL_CONSONANTS_LIST) {
    if (syllable.startsWith(base)) {
      const remainder = syllable.slice(base.length);
      if (remainder.includes(PULLI_CHAR)) return null;
      for (const [sign, uyir] of VOWEL_SIGNS_MAP) {
        if (remainder === sign) {
          return [mei, uyir];
        }
      }
    }
  }
  return null;
}

export function splitUyirmei(syllable: string): [string, string] | null {
  if (!syllable) return null;
  try {
    const fn = (tt as any).split_uyirmei;
    if (typeof fn === "function") {
      const res = fn(syllable);
      if (res && typeof res === "object") {
        if (typeof res.mei === "string" && typeof res.uyir === "string") {
          return [res.mei, res.uyir];
        }
      }
    }
    const parts = tt.execute({ op: "split_uyirmei", input: syllable }) as any;
    if (parts && typeof parts === "object") {
      if (typeof parts.mei === "string" && typeof parts.uyir === "string") {
        return [parts.mei, parts.uyir];
      }
      if (Array.isArray(parts) && parts.length === 2) {
        return parts as [string, string];
      }
    }
  } catch {
    // Non-uyirmei fallback
  }
  return splitUyirmeiJs(syllable);
}

export function analyzeTamilText(text: string): WordAnalysisReport {
  const letters = getLetters(text);
  const syllables: AnalyzedSyllable[] = [];

  let vowel_count = 0;
  let consonant_count = 0;
  let uyirmei_count = 0;
  let grantha_count = 0;

  letters.forEach((syl, i) => {
    const codepoints = Array.from(syl).map(
      (c) => "U+" + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0")
    );

    // Aytham ஃ
    if (syl === "ஃ") {
      syllables.push({
        index: i,
        raw: syl,
        kind: "aaytham",
        base_consonant: null,
        vowel: null,
        vowel_sign: null,
        vowel_sign_name_ta: "ஆய்த எழுத்து (தனிநிலை)",
        codepoints
      });
      return;
    }

    // Grantha check
    const isGrantha = Array.from(GRANTHA_CHARS).some((g) => syl.startsWith(g) || syl.includes(g));
    if (isGrantha) {
      grantha_count++;
      syllables.push({
        index: i,
        raw: syl,
        kind: "grantha",
        base_consonant: syl,
        vowel: null,
        vowel_sign: null,
        vowel_sign_name_ta: "வடமொழி கிரந்த எழுத்து",
        codepoints
      });
      return;
    }

    // Pure vowel (உயிர்)
    if (/^[அஆஇஈஉஊஎஏஐஒஓஔ]/.test(syl) && syl.length === 1) {
      vowel_count++;
      syllables.push({
        index: i,
        raw: syl,
        kind: "uyir",
        base_consonant: null,
        vowel: syl,
        vowel_sign: null,
        vowel_sign_name_ta: "தனி உயிரெழுத்து (முதல் எழுத்து)",
        codepoints
      });
      return;
    }

    // Pure consonant with pulli (மெய்)
    if (syl.endsWith("்") || syl.includes("\u0BCD")) {
      consonant_count++;
      syllables.push({
        index: i,
        raw: syl,
        kind: "mei",
        base_consonant: syl,
        vowel: null,
        vowel_sign: "்",
        vowel_sign_name_ta: "புள்ளி (மெய்க்குறி)",
        codepoints
      });
      return;
    }

    // Uyirmei check
    const split = splitUyirmei(syl);
    if (split) {
      uyirmei_count++;
      const [mei, uyir] = split;
      // Extract vowel diacritic sign: base consonant is mei without pulli
      const baseChar = mei.endsWith(PULLI_CHAR) ? mei.slice(0, -PULLI_CHAR.length) : mei[0];
      const signPart = syl.startsWith(baseChar) ? syl.slice(baseChar.length) : "";
      const vowelSignName = (signPart && VOWEL_SIGN_NAMES[signPart]) || (uyir === "அ" ? "அகர உயிர்மெய் (இயல்பு வடிவம்)" : null);

      syllables.push({
        index: i,
        raw: syl,
        kind: "uyirmei",
        base_consonant: mei,
        vowel: uyir,
        vowel_sign: signPart || null,
        vowel_sign_name_ta: vowelSignName,
        codepoints
      });
      return;
    }

    // Other / punctuation / non-Tamil
    syllables.push({
      index: i,
      raw: syl,
      kind: "other",
      base_consonant: null,
      vowel: null,
      vowel_sign: null,
      vowel_sign_name_ta: null,
      codepoints
    });
  });

  return {
    word: text,
    syllables,
    total_letters: syllables.length,
    vowel_count,
    consonant_count,
    uyirmei_count,
    grantha_count
  };
}

// ---------------------------------------------------------------------------
// 3. Tamil Unicode Text Normalizer Helpers & Anomaly Diagnostics
// ---------------------------------------------------------------------------

export interface NormalizationAnomaly {
  position: number;
  type: "duplicate_pulli" | "split_vowel" | "stray_format_control" | "non_nfc";
  description_ta: string;
  description_en: string;
  snippet: string;
}

export interface NormalizationResult {
  originalText: string;
  normalizedTextNFC: string;
  normalizedTextNFD: string;
  repairedText: string;
  isClean: boolean;
  isNfc: boolean;
  isNfd: boolean;
  anomalyCount: number;
  anomalies: NormalizationAnomaly[];
  decomposedVowelsCount: number;
  originalCodepoints: string[];
  nfcCodepoints: string[];
  nfdCodepoints: string[];
  repairedCodepoints: string[];
  processingLatencyMs: number;
}

export function normalizeNfc(text: string): string {
  if (!text) return "";
  try {
    const fn = (tt as any).normalize_nfc;
    if (typeof fn === "function") {
      const res = fn(text);
      if (typeof res === "string") return res;
    }
    const res = tt.execute({ op: "normalize_nfc", input: text });
    if (typeof res === "string") return res;
  } catch {
    // JavaScript fallback
  }
  return text.normalize("NFC");
}

export function normalizeNfd(text: string): string {
  if (!text) return "";
  try {
    const fn = (tt as any).normalize_nfd;
    if (typeof fn === "function") {
      const res = fn(text);
      if (typeof res === "string") return res;
    }
    const res = tt.execute({ op: "normalize_nfd", input: text });
    if (typeof res === "string") return res;
  } catch {
    // JavaScript fallback
  }
  return text.normalize("NFD");
}

export function repairTamilText(rawText: string): string {
  if (!rawText) return "";
  // 1. Collapse duplicate consecutive pulli marks (U+0BCD U+0BCD+ -> U+0BCD)
  let repaired = rawText.replace(new RegExp(PULLI_CHAR + "{2,}", "g"), PULLI_CHAR);

  // 2. Remove stray invisible format controls outside legitimate sequences (ZWJ 0x200D, ZWNJ 0x200C, BOM 0xFEFF, ZWSP 0x200B)
  let cleaned = "";
  for (let i = 0; i < repaired.length; i++) {
    const cp = repaired.charCodeAt(i);
    if (cp === 0x200b || cp === 0x200c || cp === 0x200d || cp === 0xfeff) {
      continue;
    }
    cleaned += repaired[i];
  }

  // 3. Normalize to canonical NFC
  return normalizeNfc(cleaned);
}

export function auditAndNormalizeTamil(rawText: string): NormalizationResult {
  const t0 = performance.now();
  const nfc = normalizeNfc(rawText);
  const nfd = normalizeNfd(rawText);
  const repaired = repairTamilText(rawText);
  const anomalies: NormalizationAnomaly[] = [];

  // Check 1: Duplicate pulli marks
  const dupPulliRegex = new RegExp(PULLI_CHAR + "{2,}", "g");
  let match: RegExpExecArray | null;
  while ((match = dupPulliRegex.exec(rawText)) !== null) {
    anomalies.push({
      position: match.index,
      type: "duplicate_pulli",
      description_ta: "இரட்டைப் புள்ளி (Duplicate Pulli) கண்டறியப்பட்டது",
      description_en: "Consecutive duplicate pulli (virama) marks detected",
      snippet: rawText.substring(Math.max(0, match.index - 2), Math.min(rawText.length, match.index + 3))
    });
  }

  // Check 2: Stray invisible format controls (ZWJ / ZWNJ / BOM / ZWSP)
  for (let i = 0; i < rawText.length; i++) {
    const cp = rawText.charCodeAt(i);
    if (cp === 0x200b || cp === 0x200c || cp === 0x200d || cp === 0xfeff) {
      const code = "U+" + cp.toString(16).toUpperCase().padStart(4, "0");
      anomalies.push({
        position: i,
        type: "stray_format_control",
        description_ta: `தேவையற்ற மறைமுகக் குறியீடு (${code}) கண்டறியப்பட்டது`,
        description_en: `Stray invisible format control (${code}) detected`,
        snippet: rawText.substring(Math.max(0, i - 2), Math.min(rawText.length, i + 3))
      });
    }
  }

  // Check 3: Raw != NFC difference
  if (rawText !== nfc && anomalies.length === 0) {
    anomalies.push({
      position: 0,
      type: "non_nfc",
      description_ta: "உரை நியம ஒருங்குறி வடிவில் (NFC) இல்லை; இணைத்துச் சீரமைக்கப்பட்டது",
      description_en: "Text was in decomposed / non-canonical sequence; normalized to canonical NFC",
      snippet: rawText.substring(0, Math.min(rawText.length, 12))
    });
  }

  // Check 4: Count two-part vowel decompositions in text
  let decomposedVowelsCount = 0;
  for (let i = 0; i < nfd.length; i++) {
    const cp = nfd.charCodeAt(i);
    if (cp === 0x0bc6 || cp === 0x0bc7) {
      if (i + 1 < nfd.length) {
        const nextCp = nfd.charCodeAt(i + 1);
        if (nextCp === 0x0bbe || nextCp === 0x0bd7) {
          decomposedVowelsCount++;
        }
      }
    }
  }

  const toCodepoints = (str: string) =>
    Array.from(str).map((c) => "U+" + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, "0"));

  const elapsed = performance.now() - t0;

  return {
    originalText: rawText,
    normalizedTextNFC: nfc,
    normalizedTextNFD: nfd,
    repairedText: repaired,
    isClean: anomalies.length === 0 && rawText === nfc,
    isNfc: rawText === nfc,
    isNfd: rawText === nfd,
    anomalyCount: anomalies.length,
    anomalies,
    decomposedVowelsCount,
    originalCodepoints: toCodepoints(rawText),
    nfcCodepoints: toCodepoints(nfc),
    nfdCodepoints: toCodepoints(nfd),
    repairedCodepoints: toCodepoints(repaired),
    processingLatencyMs: elapsed
  };
}

// ---------------------------------------------------------------------------
// 4. Tamil Syllabic Hyphenation & Responsive Line Wrapping
// ---------------------------------------------------------------------------

export interface HyphenationPoint {
  point_index: number;
  letter_index: number;
  byte_offset: number;
}

export interface HyphenationResult {
  word: string;
  syllables: string[];
  hyphenated: string;
}

export interface WrapResult {
  lines: string[];
  wrapped: string;
}

export interface HyphenationOptions {
  delimiter?: string;
  left_min?: number;
  right_min?: number;
}

function isTamilWord(str: string): boolean {
  for (let i = 0; i < str.length; i++) {
    const cp = str.charCodeAt(i);
    if (cp >= 0x0b80 && cp <= 0x0bff) return true;
  }
  return false;
}

export function getTamilSyllables(word: string): string[] {
  const letters = getLetters(word);
  if (letters.length === 0) return [];

  const isCoda = (l: string) => l.endsWith("\u0BCD") || l === "\u0B83";
  const isNucleus = (l: string) => !isCoda(l) && isTamilWord(l);

  const syllables: string[] = [];
  let current: string[] = [];

  for (let i = 0; i < letters.length; i++) {
    const l = letters[i];
    if (isNucleus(l)) {
      if (current.length > 0) {
        syllables.push(current.join(""));
        current = [];
      }
      current.push(l);
    } else {
      current.push(l);
    }
  }

  if (current.length > 0) {
    syllables.push(current.join(""));
  }

  return syllables;
}

export function fallbackHyphenateWord(
  word: string,
  options?: HyphenationOptions
): HyphenationResult {
  const delimiter = options?.delimiter ?? "\u00AD";
  const leftMin = options?.left_min ?? 2;
  const rightMin = options?.right_min ?? 2;

  const syllables = getTamilSyllables(word);
  const totalLetters = getLetters(word).length;

  if (totalLetters < leftMin + rightMin || syllables.length <= 1) {
    return {
      word,
      syllables: syllables.length > 0 ? syllables : [word],
      hyphenated: word,
    };
  }

  // Calculate permissible break points between syllables
  const segments: string[] = [];
  let currentSegment = "";
  let cumulativeLetters = 0;

  for (let i = 0; i < syllables.length; i++) {
    const syl = syllables[i];
    const sylLetters = getLetters(syl).length;
    currentSegment += syl;
    cumulativeLetters += sylLetters;

    const remainingLetters = totalLetters - cumulativeLetters;
    if (
      i < syllables.length - 1 &&
      cumulativeLetters >= leftMin &&
      remainingLetters >= rightMin
    ) {
      segments.push(currentSegment);
      currentSegment = "";
    }
  }
  if (currentSegment) {
    segments.push(currentSegment);
  }

  return {
    word,
    syllables,
    hyphenated: segments.join(delimiter),
  };
}

export function hyphenateWord(
  word: string,
  options?: HyphenationOptions
): HyphenationResult {
  if (!word) return { word: "", syllables: [], hyphenated: "" };
  try {
    const fn = (tt as any).hyphenate_word;
    if (typeof fn === "function") {
      const res = fn(
        word,
        options?.delimiter ?? "\u00AD",
        options?.left_min ?? 2,
        options?.right_min ?? 2
      );
      if (res && Array.isArray(res.syllables)) return res;
    }
    const res = tt.execute({
      op: "hyphenate_word",
      input: {
        word,
        delimiter: options?.delimiter ?? "\u00AD",
        left_min: options?.left_min ?? 2,
        right_min: options?.right_min ?? 2,
      },
    }) as HyphenationResult;
    if (res && Array.isArray(res.syllables)) return res;
  } catch {
    // Fallback to JS engine
  }
  return fallbackHyphenateWord(word, options);
}

export function getHyphenationPoints(
  word: string,
  options?: { left_min?: number; right_min?: number }
): HyphenationPoint[] {
  if (!word) return [];
  try {
    const fn = (tt as any).hyphenation_points;
    if (typeof fn === "function") {
      const res = fn(word, options?.left_min ?? 2, options?.right_min ?? 2);
      if (Array.isArray(res)) return res;
    }
    const res = tt.execute({
      op: "hyphenation_points",
      input: {
        word,
        left_min: options?.left_min ?? 2,
        right_min: options?.right_min ?? 2,
      },
    }) as HyphenationPoint[];
    if (Array.isArray(res)) return res;
  } catch {
    // Fallback
  }

  const leftMin = options?.left_min ?? 2;
  const rightMin = options?.right_min ?? 2;
  const syllables = getTamilSyllables(word);
  const totalLetters = getLetters(word).length;
  if (totalLetters < leftMin + rightMin || syllables.length <= 1) {
    return [];
  }

  const encoder = new TextEncoder();
  const points: HyphenationPoint[] = [];
  let cumulativeLetters = 0;
  let cumulativeBytes = 0;
  let pointIndex = 0;

  for (let i = 0; i < syllables.length - 1; i++) {
    const syl = syllables[i];
    cumulativeLetters += getLetters(syl).length;
    cumulativeBytes += encoder.encode(syl).length;
    const remainingLetters = totalLetters - cumulativeLetters;

    if (cumulativeLetters >= leftMin && remainingLetters >= rightMin) {
      points.push({
        point_index: pointIndex++,
        letter_index: cumulativeLetters,
        byte_offset: cumulativeBytes,
      });
    }
  }

  return points;
}

export function hyphenateText(
  text: string,
  options?: HyphenationOptions
): string {
  if (!text) return "";
  try {
    const fn = (tt as any).hyphenate_text;
    if (typeof fn === "function") {
      const res = fn(
        text,
        options?.delimiter ?? "\u00AD",
        options?.left_min ?? 2,
        options?.right_min ?? 2
      );
      if (typeof res === "string") return res;
    }
    const res = tt.execute({
      op: "hyphenate_text",
      input: {
        text,
        delimiter: options?.delimiter ?? "\u00AD",
        left_min: options?.left_min ?? 2,
        right_min: options?.right_min ?? 2,
      },
    });
    if (typeof res === "string") return res;
  } catch {
    // Fallback
  }
  const delimiter = options?.delimiter ?? "\u00AD";
  const cleaned = text.split("\u00AD").join("");
  return cleaned.replace(/[\u0B80-\u0BFF]+/g, (match) => {
    return hyphenateWord(match, { ...options, delimiter }).hyphenated;
  });
}

export function wrapText(
  text: string,
  maxWidth: number,
  options?: HyphenationOptions
): WrapResult {
  if (!text) return { lines: [], wrapped: "" };
  try {
    const fn = (tt as any).wrap_text;
    if (typeof fn === "function") {
      const res = fn(
        text,
        maxWidth,
        options?.delimiter ?? "-",
        options?.left_min ?? 2,
        options?.right_min ?? 2
      );
      if (res && Array.isArray(res.lines)) return res;
    }
    const res = tt.execute({
      op: "wrap_text",
      input: {
        text,
        max_width: maxWidth,
        delimiter: options?.delimiter ?? "-",
        left_min: options?.left_min ?? 2,
        right_min: options?.right_min ?? 2,
      },
    }) as WrapResult;
    if (res && Array.isArray(res.lines)) return res;
  } catch {
    // Fallback
  }
  const words = text.split(/\s+/);
  const lines: string[] = [];
  let currentLine: string[] = [];
  let currentLen = 0;

  for (const w of words) {
    const wLen = getLetters(w).length;
    if (currentLen + (currentLine.length > 0 ? 1 : 0) + wLen <= maxWidth) {
      currentLine.push(w);
      currentLen += (currentLine.length > 1 ? 1 : 0) + wLen;
    } else {
      if (currentLine.length > 0) {
        lines.push(currentLine.join(" "));
      }
      currentLine = [w];
      currentLen = wLen;
    }
  }
  if (currentLine.length > 0) {
    lines.push(currentLine.join(" "));
  }

  return {
    lines,
    wrapped: lines.join("\n"),
  };
}

export { tt };
