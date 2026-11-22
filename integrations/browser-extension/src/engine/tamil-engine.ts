import {
  calendarDefinitions,
  createApi,
  type CollationProfile,
  type Currency,
  type DetectionResult,
  type Locale,
} from "../../../../bindings/js-wasm/src/api.js";
import init, { initSync, execute as nativeExecute } from "../wasm/tamil_toolkit.js";
import { getExtensionUrl } from "../shared/browser-api.js";
import type {
  LegacyEncoding,
  OfficialHolidayItem,
  RepairDiagnostics,
  TypingLayout,
} from "../shared/messages.js";

export const api = createApi(nativeExecute);

let initPromise: Promise<void> | null = null;
let ready = false;

export async function initTamilEngine(wasmUrl?: string): Promise<void> {
  if (ready) return;
  if (!initPromise) {
    initPromise = (async () => {
      try {
        await (wasmUrl ? init({ module_or_path: wasmUrl }) : init());
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

export function ensureEngineReady(): void {
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

// ---------------------------------------------------------------------------
// 1. Live Transliteration (Phase 8: Phonetic, Tamil99, Anjal, Suratha Bamini)
// ---------------------------------------------------------------------------

export function transliterateToTamil(text: string, scheme: TypingLayout): string {
  ensureEngineReady();
  if (!text) return "";
  return api.transliterate(text, scheme, "to_tamil");
}

export function transliterateSuggestToTamil(
  text: string,
  scheme: TypingLayout,
  limit = 5
): string[] {
  ensureEngineReady();
  if (!text) return [];
  return api.transliterate_suggest(text, scheme, limit);
}

// ---------------------------------------------------------------------------
// 2. Legacy Encoding Detection & Conversion (7 Codecs + Auto Ambiguity Guard)
// ---------------------------------------------------------------------------

const AMBIGUITY_CONFIDENCE_THRESHOLD = 0.65;
const SUPPORTED_LEGACY = new Set(["bamini", "tscii", "tab", "tam", "anjal", "vanavil", "lt_tm"]);

function normalizeCodecId(raw: string): string {
  return raw.toLowerCase().trim().replace(/-v\d+$/, "").replace(/-/g, "_");
}

export function detectEncoding(text: string): DetectionResult {
  ensureEngineReady();
  const isPureLatin1 = Array.from(text).every((ch) => (ch.codePointAt(0) ?? 0) <= 0xff);
  return isPureLatin1 ? api.detect_encoding(stringToLatin1Bytes(text)) : api.detect_encoding(text);
}

export function convertLegacyToUnicode(
  text: string,
  encoding: LegacyEncoding = "auto"
): { text: string; detectedEncoding: string; confidence: number; ambiguous: boolean } {
  ensureEngineReady();
  if (!text) {
    return { text: "", detectedEncoding: "unicode", confidence: 1, ambiguous: false };
  }

  let chosen: string = encoding;
  let confidence = 1;

  if (encoding === "auto") {
    const det = detectEncoding(text);
    chosen = normalizeCodecId(det.encoding || "unicode");
    confidence = det.confidence ?? 0;

    if (chosen === "unicode" || chosen === "utf_8" || chosen === "utf8") {
      const hasTamilUnicode = /[\u0B80-\u0BFF]/.test(text);
      if (hasTamilUnicode) {
        return { text: api.normalize_nfc(text), detectedEncoding: "unicode", confidence, ambiguous: false };
      }
      return { text, detectedEncoding: chosen, confidence, ambiguous: true };
    }

    const candidates = det.candidates ?? [];
    const topTwoClose =
      candidates.length >= 2 &&
      Math.abs((candidates[0]?.confidence ?? 0) - (candidates[1]?.confidence ?? 0)) < 0.08;

    if (!SUPPORTED_LEGACY.has(chosen) || confidence < AMBIGUITY_CONFIDENCE_THRESHOLD || topTwoClose) {
      return {
        text,
        detectedEncoding: chosen,
        confidence,
        ambiguous: true,
      };
    }
  } else {
    chosen = normalizeCodecId(encoding);
  }

  switch (chosen) {
    case "bamini":
      return { text: api.bamini_to_unicode(text, "preserve"), detectedEncoding: "bamini", confidence, ambiguous: false };
    case "tscii":
      return {
        text: api.tscii_bytes_to_unicode(stringToLatin1Bytes(text)),
        detectedEncoding: "tscii",
        confidence,
        ambiguous: false,
      };
    case "tab":
      return {
        text: api.tab_bytes_to_unicode(stringToLatin1Bytes(text)),
        detectedEncoding: "tab",
        confidence,
        ambiguous: false,
      };
    case "tam":
      return {
        text: api.tam_bytes_to_unicode(stringToLatin1Bytes(text)),
        detectedEncoding: "tam",
        confidence,
        ambiguous: false,
      };
    case "anjal":
      return {
        text: api.anjal_bytes_to_unicode(stringToLatin1Bytes(text)),
        detectedEncoding: "anjal",
        confidence,
        ambiguous: false,
      };
    case "vanavil":
      return {
        text: api.vanavil_text_to_unicode(text, "preserve"),
        detectedEncoding: "vanavil",
        confidence,
        ambiguous: false,
      };
    case "lt_tm":
    case "lt-tm":
      return {
        text: api.lt_tm_text_to_unicode(text, "preserve"),
        detectedEncoding: "lt_tm",
        confidence,
        ambiguous: false,
      };
    default:
      return { text: api.normalize_nfc(text), detectedEncoding: chosen, confidence, ambiguous: true };
  }
}

// ---------------------------------------------------------------------------
// 3. Joiner-Preserving Unicode Repair & Line Sorting
// ---------------------------------------------------------------------------

export function repairTamil(text: string): { text: string; diagnostics: RepairDiagnostics } {
  ensureEngineReady();
  const res = api.repair_tamil_text(text, {
    collapse_duplicate_pulli: true,
    reorder_visual_kombu: true,
    strip_joiners: false,
    strip_soft_hyphens: false,
  });
  return {
    text: api.normalize_nfc(res.text),
    diagnostics: res.diagnostics,
  };
}

export function sortLines(text: string, profile: CollationProfile = "agara-v1"): string {
  ensureEngineReady();
  const lines = text.split(/\r?\n/);
  const nonEmpty = lines.filter((l) => l.trim().length > 0);
  nonEmpty.sort((a, b) => api.compare(a.trim(), b.trim(), profile));
  return nonEmpty.join("\n");
}

// ---------------------------------------------------------------------------
// 4. Numerals & Currencies (TN / SL, INR / LKR)
// ---------------------------------------------------------------------------

export function convertNumberToWords(
  amount: string,
  locale: Locale = "TN",
  currency?: Currency
): { words: string; formatted: string } {
  ensureEngineReady();
  const clean = amount.trim().replace(/,/g, "");
  if (!clean || !/^-?\d+(?:\.\d+)?$/.test(clean)) {
    throw new Error("Enter a valid number (for example: 2500 or 125.50).");
  }

  if (currency) {
    const words = api.currency_decimal_to_words(clean, "latin", currency, locale);
    const formatted = api.format_currency_decimal(clean, "latin", currency, locale, "indian");
    return { words, formatted };
  }

  const words = clean.includes(".")
    ? api.decimal_to_words(clean, "latin", locale)
    : api.to_words(Number.parseInt(clean, 10), locale);
  return { words, formatted: clean };
}

// ---------------------------------------------------------------------------
// 5. Active Civil Date & Official TN/SL Holidays (No Planned Ephemeris Suites)
// ---------------------------------------------------------------------------

const TN_CIVIL_CONTEXT = {
  region: "TN" as const,
  latitude_microdegrees: 13_082_700,
  longitude_microdegrees: 80_270_700,
  elevation_meters: 6,
  time_zone: "Asia/Kolkata" as const,
};

export function getCivilDateAndHolidays(
  year: number,
  month: number,
  day: number,
  jurisdiction: Locale = "TN"
): {
  civilDateLabel: string;
  holidays: OfficialHolidayItem[];
  supportedYear: boolean;
  sourceNote: string;
} {
  ensureEngineReady();
  let civilDateLabel = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  try {
    civilDateLabel = api.format_tamil_date(
      { year, month, day },
      TN_CIVIL_CONTEXT,
      "tamil",
      "latin",
      "weekday_day_month_year",
      calendarDefinitions.thirukanitham
    );
  } catch {
    civilDateLabel = api.format_date(year, month, day, jurisdiction, "long", "latin");
  }

  try {
    const info = api.calendar_official_holidays(jurisdiction, year) as unknown as {
      holidays?: Array<{
        gregorian_date?: { year: number; month: number; day: number };
        date?: string | { year: number; month: number; day: number };
        name?: string;
        english_name?: string;
        tamil_name?: string;
        category?: string;
      }>;
      source?: string;
      source_citation?: string;
    };
    const formatDateObj = (d?: { year: number; month: number; day: number }) =>
      d ? `${d.year}-${String(d.month).padStart(2, "0")}-${String(d.day).padStart(2, "0")}` : "";
    const items: OfficialHolidayItem[] = (info.holidays ?? []).map((h) => {
      const dateStr =
        typeof h.date === "string"
          ? h.date
          : formatDateObj(h.gregorian_date ?? (h.date && typeof h.date === "object" ? h.date : undefined));
      return {
        date: dateStr,
        name: h.english_name ?? h.name ?? "",
        tamilName: h.tamil_name,
        category: h.category,
      };
    });
    return {
      civilDateLabel,
      holidays: items,
      supportedYear: true,
      sourceNote:
        info.source_citation ??
        info.source ??
        (jurisdiction === "TN" ? "Tamil Nadu Government Official Gazette" : "Sri Lanka Public Administration Gazette"),
    };
  } catch {
    return {
      civilDateLabel,
      holidays: [],
      supportedYear: false,
      sourceNote: `Official ${jurisdiction} holiday dataset does not cover ${year}.`,
    };
  }
}
