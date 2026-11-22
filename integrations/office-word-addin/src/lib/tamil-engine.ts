import {
  calendarDefinitions,
  createApi,
  type CollationProfile,
  type Currency,
  type DetectionResult,
  type Locale,
  type RepairDiagnostics,
} from "../../../../bindings/js-wasm/src/api.js";
import init, { initSync, execute as nativeExecute } from "../wasm/tamil_toolkit.js";

export type { CollationProfile, DetectionResult, RepairDiagnostics };

export type LegacyEncoding =
  | "auto"
  | "bamini"
  | "tscii"
  | "tab"
  | "tam"
  | "anjal"
  | "vanavil"
  | "lt_tm";

export type TargetLegacyEncoding = Exclude<LegacyEncoding, "auto">;
export type NumeralLocale = Locale;
export type SupportedCurrency = Currency;
export type CalendarProfile = "thirukanitham" | "vakya";

export interface RepairSummary {
  text: string;
  changed: boolean;
  diagnostics: {
    duplicate_pullis_removed: number;
    visual_left_kombu_reordered: number;
    zero_width_removed: number;
    total_repairs: number;
  };
}

export interface InspectionResult {
  word_count: number;
  letter_count: number;
  syllable_count: number;
  uyir_count: number;
  mei_count: number;
  uyirmei_count: number;
  aytham_count: number;
  grantha_count: number;
  other_count: number;
  zero_width_count: number;
  soft_hyphen_count: number;
  is_nfc: boolean;
  non_nfc_warning: boolean;
  invisible_codepoints: Array<{ codepoint: string; name: string; count: number }>;
}

export interface TraditionalSymbolItem {
  codepoint: string;
  glyph: string;
  name_ta: string;
  name_en: string;
  category: "fraction" | "measure" | "currency";
  value_label: string;
}

export interface TamilDateStamp {
  gregorian: string;
  tamil_month: string;
  tamil_day: number;
  solar_year: number;
  thiruvalluvar_year: number;
  jovian_year: string;
  weekday_ta: string;
  profile_label: string;
  tithi?: string;
  nakshatra?: string;
  yogam?: string;
  karanam?: string;
  holiday_name?: string;
  formatted_short: string;
  formatted_formal: string;
  formatted_panchangam: string;
}

const api = createApi(nativeExecute);

let initPromise: Promise<void> | null = null;
let ready = false;

export async function initTamilEngine(): Promise<void> {
  if (ready) return;
  if (!initPromise) {
    initPromise = (async () => {
      try {
        await init();
        ready = true;
      } catch (err) {
        initPromise = null;
        throw err;
      }
    })();
  }
  return initPromise;
}

export function initTamilEngineSync(wasmBytes: BufferSource): void {
  if (ready) return;
  initSync({ module: wasmBytes });
  ready = true;
}

export function isTamilEngineReady(): boolean {
  return ready;
}

function ensureReady(): void {
  if (!ready) {
    throw new Error("Tamil WASM engine is not initialized. Call initTamilEngine() first.");
  }
}

export function stringToLatin1Bytes(text: string): number[] {
  const bytes: number[] = [];
  for (let i = 0; i < text.length; i++) {
    bytes.push(text.charCodeAt(i) & 0xff);
  }
  return bytes;
}

export function latin1BytesToString(bytes: number[]): string {
  let out = "";
  for (let i = 0; i < bytes.length; i++) {
    out += String.fromCharCode(bytes[i] & 0xff);
  }
  return out;
}

// ---------------------------------------------------------------------------
// 1. Legacy Font Detection & Bidirectional Conversion
// ---------------------------------------------------------------------------

export function detectEncoding(text: string): DetectionResult {
  ensureReady();
  const isPureLatin1 = Array.from(text).every((ch) => (ch.codePointAt(0) ?? 0) <= 0xff);
  return isPureLatin1
    ? api.detect_encoding(stringToLatin1Bytes(text))
    : api.detect_encoding(text);
}

export function convertLegacyToUnicode(
  text: string,
  encoding: LegacyEncoding = "auto"
): { text: string; detectedEncoding: string; confidence: number } {
  ensureReady();
  if (!text) return { text: "", detectedEncoding: "unicode", confidence: 1 };

  let chosen: string = encoding;
  let confidence = 1;

  if (encoding === "auto") {
    const det = detectEncoding(text);
    chosen = (det.encoding || "unicode").toLowerCase();
    confidence = det.confidence ?? 0;
    if (chosen === "unicode" || chosen === "utf-8" || chosen === "utf8" || chosen === "ascii") {
      return { text: api.normalize_nfc(text), detectedEncoding: chosen, confidence };
    }
  }

  switch (chosen) {
    case "bamini":
      return { text: api.bamini_to_unicode(text, "preserve"), detectedEncoding: "bamini", confidence };
    case "tscii":
      return { text: api.tscii_bytes_to_unicode(stringToLatin1Bytes(text)), detectedEncoding: "tscii", confidence };
    case "tab":
      return { text: api.tab_bytes_to_unicode(stringToLatin1Bytes(text)), detectedEncoding: "tab", confidence };
    case "tam":
      return { text: api.tam_bytes_to_unicode(stringToLatin1Bytes(text)), detectedEncoding: "tam", confidence };
    case "anjal":
      return { text: api.anjal_bytes_to_unicode(stringToLatin1Bytes(text)), detectedEncoding: "anjal", confidence };
    case "vanavil":
      return { text: api.vanavil_text_to_unicode(text, "preserve"), detectedEncoding: "vanavil", confidence };
    case "lt_tm":
    case "lt-tm":
    case "lttm":
      return { text: api.lt_tm_text_to_unicode(text, "preserve"), detectedEncoding: "lt_tm", confidence };
    default:
      return { text: api.normalize_nfc(text), detectedEncoding: chosen, confidence };
  }
}

export function convertUnicodeToLegacy(text: string, target: TargetLegacyEncoding): string {
  ensureReady();
  if (!text) return "";
  switch (target) {
    case "bamini":
      return api.unicode_to_bamini(text);
    case "tscii":
      return latin1BytesToString(api.unicode_to_tscii_bytes(text));
    case "tab":
      return latin1BytesToString(api.unicode_to_tab_bytes(text));
    case "tam":
      return latin1BytesToString(api.unicode_to_tam_bytes(text));
    case "anjal":
      return latin1BytesToString(api.unicode_to_anjal_bytes(text));
    case "vanavil":
      return api.unicode_to_vanavil_text(text);
    case "lt_tm":
      return api.unicode_to_lt_tm_text(text);
  }
}

// ---------------------------------------------------------------------------
// 2. Unicode Normalization, Orthographic Repair & Tamil-Aware Find/Replace
// ---------------------------------------------------------------------------

export function normalizeNfc(text: string): string {
  ensureReady();
  return api.normalize_nfc(text);
}

export function normalizeNfd(text: string): string {
  ensureReady();
  return api.normalize_nfd(text);
}

export function getTamilLetters(text: string): string[] {
  ensureReady();
  return api.get_letters(text);
}

export function repairTamilText(
  text: string,
  options: {
    fixDuplicatePulli?: boolean;
    reorderVisualVowels?: boolean;
    stripZeroWidth?: boolean;
    stripSoftHyphens?: boolean;
  } = {}
): RepairSummary {
  ensureReady();
  const res = api.repair_tamil_text(text, {
    collapse_duplicate_pulli: options.fixDuplicatePulli ?? true,
    reorder_visual_kombu: options.reorderVisualVowels ?? true,
    strip_joiners: options.stripZeroWidth ?? true,
    strip_soft_hyphens: options.stripSoftHyphens ?? false,
  });

  // Also strip ZWSP (U+200B) when stripZeroWidth is enabled
  let outText = res.text;
  let zwspRemoved = 0;
  if (options.stripZeroWidth ?? true) {
    const matches = outText.match(/\u200B/g);
    if (matches) {
      zwspRemoved = matches.length;
      outText = outText.replace(/\u200B/g, "");
    }
  }

  return {
    text: outText,
    changed: outText !== text,
    diagnostics: {
      duplicate_pullis_removed: res.diagnostics.duplicate_pulli_count,
      visual_left_kombu_reordered: res.diagnostics.visual_kombu_count,
      zero_width_removed: res.diagnostics.stripped_control_count + zwspRemoved,
      total_repairs: res.diagnostics.total_repairs + zwspRemoved,
    },
  };
}

export function foldForSearch(
  text: string,
  profile: "mayangoli" | "grantha" | "comprehensive" = "comprehensive"
): string {
  ensureReady();
  return api.fold_for_search(text, profile);
}

export function tamilAwareReplace(
  source: string,
  query: string,
  replacement: string,
  options: { fuzzyMayangoli?: boolean } = {}
): { text: string; count: number } {
  ensureReady();
  if (!query) return { text: source, count: 0 };

  const normalizeForCompare = (s: string): string => {
    const repaired = api.repair_tamil_text(s, {
      collapse_duplicate_pulli: false,
      reorder_visual_kombu: false,
      strip_soft_hyphens: true,
      strip_joiners: true,
    }).text;
    const stripped = repaired.replace(/\u200B/g, "");
    const nfc = api.normalize_nfc(stripped);
    return options.fuzzyMayangoli ? api.fold_for_search(nfc, "comprehensive") : nfc;
  };

  const letters = api.get_letters(source);
  const tokens = letters.map((l) => ({ raw: l, norm: normalizeForCompare(l) }));
  const queryLetters = api
    .get_letters(query)
    .map((l) => normalizeForCompare(l))
    .filter((l) => l.length > 0);

  if (queryLetters.length === 0) return { text: source, count: 0 };

  let out = "";
  let count = 0;
  let i = 0;

  while (i < tokens.length) {
    if (tokens[i].norm.length === 0) {
      out += tokens[i].raw;
      i++;
      continue;
    }

    let j = i;
    let q = 0;
    while (j < tokens.length && q < queryLetters.length) {
      if (tokens[j].norm.length === 0) {
        j++;
        continue;
      }
      if (tokens[j].norm === queryLetters[q]) {
        j++;
        q++;
      } else {
        break;
      }
    }

    if (q === queryLetters.length) {
      out += replacement;
      count++;
      i = j;
    } else {
      out += tokens[i].raw;
      i++;
    }
  }

  return { text: out, count };
}

// ---------------------------------------------------------------------------
// 3. Authentic Tamil Alphabetical Sorting (Akara Varisai)
// ---------------------------------------------------------------------------

function stripLeadingPrefix(line: string): string {
  return line.replace(/^\s*(?:[\d\u0BE6-\u0BEF]+[.)\-:]|\u2022|[-*])\s+/, "").trim();
}

export function compareTamil(
  left: string,
  right: string,
  profile: CollationProfile = "agara-v1"
): -1 | 0 | 1 {
  ensureReady();
  return api.compare(left, right, profile);
}

export function sortTamilLines(
  lines: string[],
  options: {
    descending?: boolean;
    profile?: CollationProfile;
    ignoreLeadingNumbers?: boolean;
    preserveEmptyPositions?: boolean;
  } = {}
): string[] {
  ensureReady();
  const profile = options.profile ?? "agara-v1";
  const dir = options.descending ? -1 : 1;
  const ignorePrefix = options.ignoreLeadingNumbers ?? false;

  const nonEmpty: Array<{ idx: number; raw: string; keyText: string }> = [];
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    if (raw.trim().length > 0) {
      nonEmpty.push({
        idx: i,
        raw,
        keyText: ignorePrefix ? stripLeadingPrefix(raw) : raw.trim(),
      });
    }
  }

  nonEmpty.sort((a, b) => {
    const cmp = api.compare(a.keyText, b.keyText, profile);
    if (cmp !== 0) return cmp * dir;
    return a.idx - b.idx;
  });

  if (options.preserveEmptyPositions ?? true) {
    const result = [...lines];
    let k = 0;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim().length > 0) {
        result[i] = nonEmpty[k++].raw;
      }
    }
    return result;
  }

  return nonEmpty.map((item) => item.raw);
}

export function sortTableRows<T extends string[]>(
  rows: T[],
  columnIndex: number,
  options: {
    hasHeader?: boolean;
    descending?: boolean;
    profile?: CollationProfile;
  } = {}
): T[] {
  ensureReady();
  if (rows.length <= 1) return [...rows];
  const hasHeader = options.hasHeader ?? true;
  const header = hasHeader ? [rows[0]] : [];
  const body = (hasHeader ? rows.slice(1) : rows).map((row, idx) => ({ row, idx }));
  const profile = options.profile ?? "agara-v1";
  const dir = options.descending ? -1 : 1;

  body.sort((a, b) => {
    const left = (a.row[columnIndex] ?? "").trim();
    const right = (b.row[columnIndex] ?? "").trim();
    const cmp = api.compare(left, right, profile);
    if (cmp !== 0) return cmp * dir;
    return a.idx - b.idx;
  });

  return [...header, ...body.map((b) => b.row)];
}

// ---------------------------------------------------------------------------
// 4. Numerals, Currency Words, Digits & Traditional Symbols
// ---------------------------------------------------------------------------

export function numberToTamilWords(
  input: string,
  mode: "cardinal" | "decimal" | "ordinal" | "currency",
  options: {
    locale?: NumeralLocale;
    currency?: SupportedCurrency;
  } = {}
): string {
  ensureReady();
  const clean = input.trim().replace(/,/g, "");
  const locale = options.locale ?? "TN";

  if (mode === "currency") {
    const currency = options.currency ?? "INR";
    return api.currency_decimal_to_words(clean, "latin", currency, locale);
  }

  if (mode === "ordinal") {
    const n = Number.parseInt(clean, 10);
    if (!Number.isFinite(n) || n < 1) {
      throw new Error("Ordinal requires a positive integer (1 or greater).");
    }
    return api.ordinal_to_words(n, locale);
  }

  if (mode === "decimal" || clean.includes(".")) {
    return api.decimal_to_words(clean, "latin", locale);
  }

  const n = Number.parseInt(clean, 10);
  if (!Number.isFinite(n)) {
    throw new Error("Invalid integer input.");
  }
  return api.to_words(n, locale);
}

export function convertDigits(text: string, to: "tamil" | "latin"): string {
  ensureReady();
  return api.convert_digits(text, to);
}

export function formatTraditionalInteger(value: number): string {
  ensureReady();
  return api.format_traditional_integer(value);
}

export const TRADITIONAL_SYMBOLS_PALETTE: TraditionalSymbolItem[] = [
  { codepoint: "U+11FC2", glyph: "\u{11FC2}", name_ta: "முந்திரி", name_en: "Munthiri", category: "fraction", value_label: "1/320" },
  { codepoint: "U+11FC1", glyph: "\u{11FC1}", name_ta: "அரைக்காணி", name_en: "Araikkani", category: "fraction", value_label: "1/160" },
  { codepoint: "U+11FC0", glyph: "\u{11FC0}", name_ta: "காணி", name_en: "Kani", category: "fraction", value_label: "1/80" },
  { codepoint: "U+11FCD", glyph: "\u{11FCD}", name_ta: "அரைமா", name_en: "Araima", category: "fraction", value_label: "1/40" },
  { codepoint: "U+11FCE", glyph: "\u{11FCE}", name_ta: "மா", name_en: "Ma", category: "fraction", value_label: "1/20" },
  { codepoint: "U+11FC8", glyph: "\u{11FC8}", name_ta: "மாகாணி (வீசம்)", name_en: "Makani / Veesam", category: "fraction", value_label: "1/16" },
  { codepoint: "U+11FC9", glyph: "\u{11FC9}", name_ta: "அரைக்கால்", name_en: "Araikkal", category: "fraction", value_label: "1/8" },
  { codepoint: "U+11FD2", glyph: "\u{11FD2}", name_ta: "கால்", name_en: "Kal", category: "fraction", value_label: "1/4" },
  { codepoint: "U+11FD3", glyph: "\u{11FD3}", name_ta: "அரை", name_en: "Arai", category: "fraction", value_label: "1/2" },
  { codepoint: "U+11FD4", glyph: "\u{11FD4}", name_ta: "முக்கால்", name_en: "Mukkal", category: "fraction", value_label: "3/4" },
  { codepoint: "U+0BF9", glyph: "\u0BF9", name_ta: "ரூபாய்", name_en: "Tamil Rupee Sign", category: "currency", value_label: "ரூ" },
  { codepoint: "U+0BF3", glyph: "\u0BF3", name_ta: "நாள்", name_en: "Day Sign", category: "measure", value_label: "Day" },
  { codepoint: "U+0BF4", glyph: "\u0BF4", name_ta: "மாதம்", name_en: "Month Sign", category: "measure", value_label: "Month" },
  { codepoint: "U+0BF5", glyph: "\u0BF5", name_ta: "வருடம்", name_en: "Year Sign", category: "measure", value_label: "Year" },
  { codepoint: "U+0BFA", glyph: "\u0BFA", name_ta: "எண்", name_en: "Number Sign", category: "measure", value_label: "No." },
];

// ---------------------------------------------------------------------------
// 5. Tamil Calendar & Panchangam Date Stamps
// ---------------------------------------------------------------------------

const TN_CALENDAR_CONTEXT = {
  region: "TN" as const,
  latitude_microdegrees: 13_082_700,
  longitude_microdegrees: 80_270_700,
  elevation_meters: 6,
  time_zone: "Asia/Kolkata" as const,
};

const SL_CALENDAR_CONTEXT = {
  region: "SL" as const,
  latitude_microdegrees: 9_661_500,
  longitude_microdegrees: 80_025_500,
  elevation_meters: 5,
  time_zone: "Asia/Colombo" as const,
};

function vakyaContextFor(region: NumeralLocale) {
  return {
    reference_station: "ujjain" as const,
    time_zone: region === "SL" ? ("Asia/Colombo" as const) : ("Asia/Kolkata" as const),
  };
}

export function buildTamilDateStamp(
  year: number,
  month: number,
  day: number,
  options: {
    profile?: CalendarProfile;
    region?: NumeralLocale;
    includePanchangam?: boolean;
  } = {}
): TamilDateStamp {
  ensureReady();
  const profile = options.profile ?? "thirukanitham";
  const region = options.region ?? "TN";
  const definitionId =
    profile === "vakya" ? calendarDefinitions.vakyaCivil : calendarDefinitions.thirukanitham;
  const drikCtx = region === "SL" ? SL_CALENDAR_CONTEXT : TN_CALENDAR_CONTEXT;
  const context = profile === "vakya" ? vakyaContextFor(region) : drikCtx;

  const conv = api.gregorian_to_tamil_date({ year, month, day }, context, definitionId);
  const cycle = api.tamil_year_cycle_info(conv.tamil_date.solar_year, context, definitionId);
  const tv = api.thiruvalluvar_year_info({ year, month, day }, drikCtx);
  const formattedShort = api.format_tamil_date(
    { year, month, day },
    context,
    "tamil",
    "latin",
    "weekday_day_month_year",
    definitionId
  );
  const weekdayTa = api.weekday(year, month, day);

  const jovianYear = cycle.cycle_name || "";
  const tamilMonth = conv.tamil_date.month_name || String(conv.tamil_date.month);

  let tithi: string | undefined;
  let nakshatra: string | undefined;
  let yogam: string | undefined;
  let karanam: string | undefined;

  if (options.includePanchangam) {
    try {
      const pDay = api.panchangam_day({ year, month, day }, context, definitionId);
      tithi = pDay.limbs_at_sunrise?.tithi?.name;
      nakshatra = pDay.limbs_at_sunrise?.nakshatra?.name;
      yogam = pDay.limbs_at_sunrise?.yoga?.name;
      karanam = pDay.limbs_at_sunrise?.karana?.name;
    } catch {
      // Optional enrichment
    }
  }

  let holidayName: string | undefined;
  try {
    const hol = api.calendar_official_holidays(region, year);
    const match = hol.holidays.find(
      (h) =>
        h.date.year === year &&
        h.date.month === month &&
        h.date.day === day
    );
    if (match) {
      holidayName = match.name;
    }
  } catch {
    // Year outside holiday dataset range
  }

  const gregorianIso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  const formattedFormal = `திருவள்ளுவர் ஆண்டு ${tv.thiruvalluvar_year}, ${jovianYear} ஆண்டு, ${formattedShort}`;
  const limbs = [tithi, nakshatra, yogam, karanam].filter(Boolean).join(" | ");
  const formattedPanchangam = limbs ? `${formattedFormal} (${limbs})` : formattedFormal;

  return {
    gregorian: gregorianIso,
    tamil_month: tamilMonth,
    tamil_day: conv.tamil_date.day,
    solar_year: conv.tamil_date.solar_year,
    thiruvalluvar_year: tv.thiruvalluvar_year,
    jovian_year: jovianYear,
    weekday_ta: weekdayTa,
    profile_label: profile === "vakya" ? "Vakya (1962)" : "Thirukanitham (Drik)",
    tithi,
    nakshatra,
    yogam,
    karanam,
    holiday_name: holidayName,
    formatted_short: formattedShort,
    formatted_formal: formattedFormal,
    formatted_panchangam: formattedPanchangam,
  };
}

// ---------------------------------------------------------------------------
// 6. Syllabic Hyphenation (Canonical Rust tamil-hyphen)
// ---------------------------------------------------------------------------

export function hyphenateText(
  text: string,
  options: {
    delimiter?: string;
    leftMin?: number;
    rightMin?: number;
  } = {}
): string {
  ensureReady();
  const cleaned = removeHyphens(text);
  return api.hyphenate_text(
    cleaned,
    options.delimiter ?? "\u00AD",
    options.leftMin ?? 3,
    options.rightMin ?? 3
  );
}

export function removeHyphens(text: string): string {
  return text.replace(/[\u00AD\u200B]/g, "");
}

// ---------------------------------------------------------------------------
// 7. Document Inspector (True Tamil Graphemes, Syllables & Scalars)
// ---------------------------------------------------------------------------

const GRANTHA_BASES = new Set([0x0b9c, 0x0bb6, 0x0bb7, 0x0bb8, 0x0bb9]);
const UYIR_START = 0x0b85;
const UYIR_END = 0x0b94;
const CONSONANT_START = 0x0b95;
const CONSONANT_END = 0x0bb9;

export function inspectDocumentText(text: string): InspectionResult {
  ensureReady();
  const letters = api.get_letters(text);
  const olippasai = api.get_olippasai(text);
  const scalarInfo = api.inspect_tamil_string(text);

  let uyir = 0;
  let mei = 0;
  let uyirmei = 0;
  let aytham = 0;
  let grantha = 0;
  let other = 0;

  for (const letter of letters) {
    if (letter === "\u0B83") {
      aytham++;
      continue;
    }
    if (
      letter.startsWith("\u0B95\u0BCD\u0BB7") ||
      letter.startsWith("\u0BB8\u0BCD\u0BB0\u0BC0") ||
      letter.startsWith("\u0BB6\u0BCD\u0BB0\u0BC0")
    ) {
      grantha++;
      continue;
    }
    const cp = letter.codePointAt(0) ?? 0;
    if (cp >= UYIR_START && cp <= UYIR_END) {
      uyir++;
    } else if (GRANTHA_BASES.has(cp)) {
      grantha++;
    } else if (cp >= CONSONANT_START && cp <= CONSONANT_END) {
      if (letter.endsWith("\u0BCD")) {
        mei++;
      } else {
        uyirmei++;
      }
    } else if (letter.trim().length > 0) {
      other++;
    }
  }

  const invisibleMap = new Map<string, { codepoint: string; name: string; count: number }>();
  let zwCount = 0;
  let shyCount = 0;

  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    if (cp === 0x00ad) {
      shyCount++;
      const prev = invisibleMap.get("U+00AD") ?? { codepoint: "U+00AD", name: "SOFT HYPHEN", count: 0 };
      prev.count++;
      invisibleMap.set("U+00AD", prev);
    } else if (cp === 0x200b || cp === 0x200c || cp === 0x200d || cp === 0xfeff) {
      zwCount++;
      const hex = `U+${cp.toString(16).toUpperCase().padStart(4, "0")}`;
      const names: Record<number, string> = {
        0x200b: "ZERO WIDTH SPACE",
        0x200c: "ZERO WIDTH NON-JOINER",
        0x200d: "ZERO WIDTH JOINER",
        0xfeff: "BYTE ORDER MARK",
      };
      const prev = invisibleMap.get(hex) ?? { codepoint: hex, name: names[cp] || "INVISIBLE", count: 0 };
      prev.count++;
      invisibleMap.set(hex, prev);
    }
  }

  const words = text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0);
  const tamilLetterCount = uyir + mei + uyirmei + aytham + grantha;
  const isNfc = scalarInfo.is_nfc;

  return {
    word_count: words.length,
    letter_count: tamilLetterCount,
    syllable_count: olippasai.length,
    uyir_count: uyir,
    mei_count: mei,
    uyirmei_count: uyirmei,
    aytham_count: aytham,
    grantha_count: grantha,
    other_count: other,
    zero_width_count: zwCount,
    soft_hyphen_count: shyCount,
    is_nfc: isNfc,
    non_nfc_warning: !isNfc,
    invisible_codepoints: Array.from(invisibleMap.values()),
  };
}
