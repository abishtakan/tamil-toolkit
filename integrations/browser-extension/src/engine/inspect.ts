import type { InspectionSnapshot, InspectionSource } from "../shared/messages.js";
import { api, detectEncoding, ensureEngineReady } from "./tamil-engine.js";

const GRANTHA_BASES = new Set([0x0b9c, 0x0bb6, 0x0bb7, 0x0bb8, 0x0bb9]);
const UYIR_START = 0x0b85;
const UYIR_END = 0x0b94;
const CONSONANT_START = 0x0b95;
const CONSONANT_END = 0x0bb9;

export function inspectText(
  text: string,
  source: InspectionSource,
  editable: boolean
): InspectionSnapshot {
  ensureEngineReady();
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

  let zeroWidthCount = 0;
  let softHyphenCount = 0;
  for (const ch of text) {
    const cp = ch.codePointAt(0) ?? 0;
    if (cp === 0x00ad) {
      softHyphenCount++;
    } else if (cp === 0x200b || cp === 0x200c || cp === 0x200d || cp === 0xfeff) {
      zeroWidthCount++;
    }
  }

  const dryRepair = api.repair_tamil_text(text, {
    collapse_duplicate_pulli: true,
    reorder_visual_kombu: true,
    strip_joiners: false,
    strip_soft_hyphens: false,
  });

  let detectedLegacyEncoding: string | null = null;
  let legacyConfidence = 0;
  if (text.trim().length >= 4 && uyir + mei + uyirmei + aytham + grantha === 0) {
    try {
      const det = detectEncoding(text);
      const enc = (det.encoding ?? "").toLowerCase();
      if (
        enc &&
        enc !== "unicode" &&
        enc !== "utf-8" &&
        enc !== "utf8" &&
        enc !== "ascii" &&
        (det.confidence ?? 0) >= 0.65
      ) {
        detectedLegacyEncoding = enc;
        legacyConfidence = det.confidence ?? 0;
      }
    } catch {
      // Ignore detection errors on non-Tamil text
    }
  }

  const words = text
    .trim()
    .split(/\s+/)
    .filter((w) => w.length > 0);
  const letterCount = uyir + mei + uyirmei + aytham + grantha;
  const readingSeconds = words.length === 0 ? 0 : Math.max(1, Math.round(words.length / 3));
  const totalIssues =
    dryRepair.diagnostics.duplicate_pulli_count +
    dryRepair.diagnostics.visual_kombu_count +
    (scalarInfo.is_nfc ? 0 : 1) +
    (detectedLegacyEncoding ? 1 : 0);

  return {
    source,
    editable,
    letterCount,
    wordCount: words.length,
    syllableCount: olippasai.length,
    utf16Length: text.length,
    readingSeconds,
    breakdown: {
      uyir,
      mei,
      uyirmei,
      aytham,
      grantha,
      other,
    },
    health: {
      isNfc: scalarInfo.is_nfc,
      duplicatePullis: dryRepair.diagnostics.duplicate_pulli_count,
      visualKombus: dryRepair.diagnostics.visual_kombu_count,
      zeroWidthCount,
      softHyphenCount,
      detectedLegacyEncoding,
      legacyConfidence,
      totalIssues,
    },
  };
}
