import {
  hasOoxmlSoftHyphens,
  hasOoxmlZeroWidthWrap,
  hyphenateOoxml,
  removeOoxmlHyphens,
  transformOoxmlRunsWithFont,
  transformOoxmlTextNodes,
} from "./ooxml.js";
import {
  CollationProfile,
  KeyboardLayout,
  LegacyEncoding,
  TargetLegacyEncoding,
  convertKeyboardToUnicode,
  convertLegacyToUnicode,
  convertUnicodeToLegacy,
  getTamilLetters,
  hyphenateText,
  repairTamilText,
  sortTableRows,
  sortTamilLines,
  tamilAwareReplace,
  transliterateSuggestText,
  transliterateText,
} from "./tamil-engine.js";

export type TargetScope = "selection" | "paragraph" | "document";

export interface BatchProgress {
  processed: number;
  total: number;
}

export interface TransformSummary {
  rangesProcessed: number;
  rangesModified: number;
  rangesFailed: number;
  details?: string;
}

export interface PrepareDocumentOptions {
  scope: TargetScope;
  includeHeadersFooters?: boolean;
  convertLegacy?: boolean;
  sourceEncoding?: LegacyEncoding;
  unicodeFont?: string;
  repairUnicode?: boolean;
  stripZeroWidth?: boolean;
  stripSoftHyphens?: boolean;
  hyphenate?: boolean;
  leftMin?: number;
  rightMin?: number;
  useNativeSoftHyphen?: boolean;
}

const BATCH_SIZE = 25;

export function isWordHost(): boolean {
  return typeof Word !== "undefined" && typeof Word.run === "function";
}

async function resolveRanges(
  context: Word.RequestContext,
  scope: TargetScope,
  includeHeadersFooters = false
): Promise<Word.Range[]> {
  if (scope === "selection") {
    const selection = context.document.getSelection();
    selection.load("text");
    await context.sync();
    if (selection.text && selection.text.trim().length > 0) {
      return [selection];
    }
    return [];
  }

  if (scope === "paragraph") {
    const selection = context.document.getSelection();
    const firstPara = selection.paragraphs.getFirst();
    firstPara.load("text");
    await context.sync();
    if (firstPara.text && firstPara.text.trim().length > 0) {
      return [firstPara.getRange(Word.RangeLocation.content)];
    }
    return [];
  }

  // Body & Tables: WordApi 1.3 body.paragraphs includes table cell paragraphs without double traversal
  const paragraphs = context.document.body.paragraphs;
  paragraphs.load("items/text");
  await context.sync();

  const ranges: Word.Range[] = [];
  for (const para of paragraphs.items) {
    if (para.text && para.text.trim().length > 0) {
      ranges.push(para.getRange(Word.RangeLocation.content));
    }
  }

  if (includeHeadersFooters) {
    try {
      const sections = context.document.sections;
      sections.load("items");
      await context.sync();
      const headerFooterParas: Word.ParagraphCollection[] = [];
      for (const sec of sections.items) {
        const hdr = sec.getHeader(Word.HeaderFooterType.primary).paragraphs;
        const ftr = sec.getFooter(Word.HeaderFooterType.primary).paragraphs;
        hdr.load("items/text");
        ftr.load("items/text");
        headerFooterParas.push(hdr, ftr);
      }
      await context.sync();
      for (const col of headerFooterParas) {
        for (const para of col.items) {
          if (para.text && para.text.trim().length > 0) {
            ranges.push(para.getRange(Word.RangeLocation.content));
          }
        }
      }
    } catch {
      // Some minimal Word hosts restrict header/footer APIs; body+tables still proceed
    }
  }

  return ranges;
}

/**
 * True 2-sync-per-chunk batched OOXML processor:
 *   1) Queue getOoxml() for up to 25 ranges -> 1 context.sync()
 *   2) Run pure Rust/WASM transforms locally in JS
 *   3) Queue insertOoxml() ONLY for changed ranges -> 1 context.sync()
 * Never silently strips inline formatting via plain-text fallback; failed chunks are reported.
 */
async function runBatchedOoxmlTransform(
  scope: TargetScope,
  ooxmlTransform: (xml: string) => string,
  options: {
    includeHeadersFooters?: boolean;
    onProgress?: (p: BatchProgress) => void;
  } = {}
): Promise<TransformSummary> {
  let rangesProcessed = 0;
  let rangesModified = 0;
  let rangesFailed = 0;

  await Word.run(async (context) => {
    const ranges = await resolveRanges(context, scope, options.includeHeadersFooters ?? false);
    const total = ranges.length;

    for (let i = 0; i < total; i += BATCH_SIZE) {
      const chunk = ranges.slice(i, i + BATCH_SIZE);
      try {
        // 1. Batched read sync
        const ooxmlResults = chunk.map((r) => r.getOoxml());
        await context.sync();

        // 2. Local Rust/WASM planning + queue changed writes
        let chunkWrites = 0;
        for (let j = 0; j < chunk.length; j++) {
          const originalXml = ooxmlResults[j]?.value;
          rangesProcessed++;
          if (!originalXml) continue;

          const updatedXml = ooxmlTransform(originalXml);
          if (updatedXml !== originalXml) {
            chunk[j].insertOoxml(updatedXml, Word.InsertLocation.replace);
            chunkWrites++;
          }
        }

        // 3. Batched write sync (only if something changed)
        if (chunkWrites > 0) {
          await context.sync();
          rangesModified += chunkWrites;
        }
      } catch {
        rangesFailed += chunk.length;
      }

      options.onProgress?.({ processed: Math.min(i + BATCH_SIZE, total), total });
    }
  });

  return { rangesProcessed, rangesModified, rangesFailed };
}

export async function readTargetText(scope: TargetScope): Promise<string> {
  return Word.run(async (context) => {
    if (scope === "selection") {
      const sel = context.document.getSelection();
      sel.load("text");
      await context.sync();
      return sel.text || "";
    }
    if (scope === "paragraph") {
      const firstPara = context.document.getSelection().paragraphs.getFirst();
      firstPara.load("text");
      await context.sync();
      return firstPara.text || "";
    }
    const body = context.document.body;
    body.load("text");
    await context.sync();
    return body.text || "";
  });
}

export async function insertAtCursor(
  text: string,
  replaceSelection = true,
  fontName?: string
): Promise<void> {
  await Word.run(async (context) => {
    const sel = context.document.getSelection();
    const inserted = sel.insertText(
      text,
      replaceSelection ? Word.InsertLocation.replace : Word.InsertLocation.after
    );
    if (fontName) {
      inserted.font.name = fontName;
    }
    inserted.select(Word.SelectionMode.end);
    await context.sync();
  });
}

/**
 * 1-Pass "Prepare Legacy Document" pipeline:
 * Combines Legacy -> Unicode conversion, Unicode NFC/orthographic repair,
 * and optional syllabic hyphenation in a single batched OOXML read/write pass.
 */
export async function runPrepareLegacyDocument(
  opts: PrepareDocumentOptions,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary & { detectedEncoding: string }> {
  const sourceEncoding = opts.sourceEncoding ?? "auto";
  let detectedEncoding: string = sourceEncoding;
  let dupPullis = 0;
  let visualVowels = 0;
  let zwRemoved = 0;

  const summary = await runBatchedOoxmlTransform(
    opts.scope,
    (xml) => {
      let current = xml;

      if (opts.convertLegacy) {
        const res = transformOoxmlRunsWithFont(
          current,
          (txt) => {
            const conv = convertLegacyToUnicode(txt, sourceEncoding);
            if (sourceEncoding === "auto" && detectedEncoding === "auto" && conv.detectedEncoding !== "unicode") {
              detectedEncoding = conv.detectedEncoding;
            }
            return conv.text;
          },
          opts.unicodeFont
        );
        current = res.xml;
      }

      if (opts.repairUnicode) {
        current = transformOoxmlTextNodes(current, (txt) => {
          const r = repairTamilText(txt, {
            fixDuplicatePulli: true,
            reorderVisualVowels: true,
            stripZeroWidth: opts.stripZeroWidth ?? false,
            stripSoftHyphens: opts.stripSoftHyphens ?? false,
          });
          dupPullis += r.diagnostics.duplicate_pullis_removed;
          visualVowels += r.diagnostics.visual_left_kombu_reordered;
          zwRemoved += r.diagnostics.zero_width_removed;
          return r.text;
        });
      }

      if (opts.hyphenate) {
        current = hyphenateOoxml(
          current,
          (txt, delim) =>
            hyphenateText(txt, {
              delimiter: delim,
              leftMin: opts.leftMin ?? 3,
              rightMin: opts.rightMin ?? 3,
            }),
          opts.useNativeSoftHyphen ?? true
        );
      }

      return current;
    },
    {
      includeHeadersFooters: opts.includeHeadersFooters ?? false,
      onProgress,
    }
  );

  return {
    ...summary,
    detectedEncoding,
    details: opts.repairUnicode ? `pulli=${dupPullis}, kombu=${visualVowels}, zw=${zwRemoved}` : undefined,
  };
}

export async function runLegacyToUnicode(
  scope: TargetScope,
  sourceEncoding: LegacyEncoding,
  unicodeFont: string,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary & { detectedEncoding: string }> {
  return runPrepareLegacyDocument(
    {
      scope,
      convertLegacy: true,
      sourceEncoding,
      unicodeFont,
      repairUnicode: false,
      hyphenate: false,
    },
    onProgress
  );
}

export async function runKeyboardToUnicode(
  scope: TargetScope,
  layout: KeyboardLayout,
  unicodeFont: string,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary> {
  if (layout === "bamini") {
    return runLegacyToUnicode(scope, "bamini", unicodeFont, onProgress);
  }
  return runBatchedOoxmlTransform(
    scope,
    (xml) =>
      transformOoxmlRunsWithFont(
        xml,
        (txt) => convertKeyboardToUnicode(txt, layout),
        unicodeFont
      ).xml,
    { onProgress }
  );
}

export async function runUnicodeToLegacy(
  scope: TargetScope,
  targetEncoding: TargetLegacyEncoding,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary> {
  return runBatchedOoxmlTransform(
    scope,
    (xml) => transformOoxmlTextNodes(xml, (txt) => convertUnicodeToLegacy(txt, targetEncoding)),
    { onProgress }
  );
}

export async function runRepairTamil(
  scope: TargetScope,
  options: {
    fixDuplicatePulli?: boolean;
    reorderVisualVowels?: boolean;
    stripZeroWidth?: boolean;
    stripSoftHyphens?: boolean;
  } = {},
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary> {
  return runPrepareLegacyDocument(
    {
      scope,
      convertLegacy: false,
      repairUnicode: true,
      stripZeroWidth: options.stripZeroWidth ?? false,
      stripSoftHyphens: options.stripSoftHyphens ?? false,
      hyphenate: false,
    },
    onProgress
  );
}

export async function runTamilFindAndReplace(
  scope: TargetScope,
  query: string,
  replacement: string,
  fuzzyMayangoli = false,
  onProgress?: (p: BatchProgress) => void
): Promise<{ totalReplacements: number; paragraphsUpdated: number; rangesFailed: number }> {
  let totalReplacements = 0;

  const summary = await runBatchedOoxmlTransform(
    scope,
    (xml) =>
      transformOoxmlTextNodes(xml, (txt) => {
        const r = tamilAwareReplace(txt, query, replacement, { fuzzyMayangoli });
        totalReplacements += r.count;
        return r.text;
      }),
    { onProgress }
  );

  return {
    totalReplacements,
    paragraphsUpdated: summary.rangesModified,
    rangesFailed: summary.rangesFailed,
  };
}

export async function runSortSelectionParagraphs(options: {
  descending?: boolean;
  profile?: CollationProfile;
  ignoreLeadingNumbers?: boolean;
} = {}): Promise<{ sortedCount: number }> {
  let sortedCount = 0;

  await Word.run(async (context) => {
    const selection = context.document.getSelection();
    const paragraphs = selection.paragraphs;
    paragraphs.load("items/text");
    await context.sync();

    if (paragraphs.items.length < 2) {
      return;
    }

    const originalTexts = paragraphs.items.map((p) => p.text);
    const sorted = sortTamilLines(originalTexts, {
      descending: options.descending,
      profile: options.profile,
      ignoreLeadingNumbers: options.ignoreLeadingNumbers,
      preserveEmptyPositions: true,
    });

    for (let i = 0; i < paragraphs.items.length; i++) {
      if (sorted[i] !== originalTexts[i]) {
        paragraphs.items[i].insertText(sorted[i], Word.InsertLocation.replace);
      }
    }
    await context.sync();
    sortedCount = paragraphs.items.length;
  });

  return { sortedCount };
}

export async function runSortSelectedTable(options: {
  columnIndex: number;
  hasHeader: boolean;
  descending?: boolean;
  profile?: CollationProfile;
}): Promise<{ sortedRows: number }> {
  let sortedRows = 0;

  await Word.run(async (context) => {
    const selection = context.document.getSelection();
    const tables = selection.tables;
    tables.load("items");
    await context.sync();

    const table = tables.items[0] ?? selection.parentTableOrNullObject;
    table.load("isNullObject,values");
    await context.sync();

    if (table.isNullObject || !table.values || table.values.length < 2) {
      return;
    }

    const sorted = sortTableRows(table.values, options.columnIndex, {
      hasHeader: options.hasHeader,
      descending: options.descending,
      profile: options.profile,
    });

    table.values = sorted;
    await context.sync();
    sortedRows = options.hasHeader ? sorted.length - 1 : sorted.length;
  });

  return { sortedRows };
}

export async function runHyphenation(
  scope: TargetScope,
  options: {
    leftMin?: number;
    rightMin?: number;
    useNativeSoftHyphen?: boolean;
    includeHeadersFooters?: boolean;
    toggle?: boolean;
  } = {},
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary & { modeAction: "applied" | "removed" }> {
  const useSoftHyphen = options.useNativeSoftHyphen ?? true;
  const shouldToggle = options.toggle ?? false;

  if (!shouldToggle) {
    const res = await runPrepareLegacyDocument(
      {
        scope,
        includeHeadersFooters: options.includeHeadersFooters ?? false,
        convertLegacy: false,
        repairUnicode: false,
        hyphenate: true,
        leftMin: options.leftMin ?? 3,
        rightMin: options.rightMin ?? 3,
        useNativeSoftHyphen: useSoftHyphen,
      },
      onProgress
    );
    return { ...res, modeAction: "applied" };
  }

  // Decide toggle direction consistently across the entire scope:
  // If any range in scope already has the requested mode (and not the opposite mode), toggle OFF;
  // otherwise switch/apply the requested mode ON across all ranges.
  let shouldRemove = false;
  await Word.run(async (context) => {
    const ranges = await resolveRanges(context, scope, options.includeHeadersFooters ?? false);
    const sample = ranges.slice(0, BATCH_SIZE);
    const reads = sample.map((r) => r.getOoxml());
    await context.sync();

    let hasRequested = false;
    let hasOpposite = false;
    for (const res of reads) {
      const xml = res?.value || "";
      if (useSoftHyphen) {
        if (hasOoxmlSoftHyphens(xml)) hasRequested = true;
        if (hasOoxmlZeroWidthWrap(xml)) hasOpposite = true;
      } else {
        if (hasOoxmlZeroWidthWrap(xml)) hasRequested = true;
        if (hasOoxmlSoftHyphens(xml)) hasOpposite = true;
      }
    }
    shouldRemove = hasRequested && !hasOpposite;
  });

  if (shouldRemove) {
    const removed = await runBatchedOoxmlTransform(scope, (xml) => removeOoxmlHyphens(xml), {
      includeHeadersFooters: options.includeHeadersFooters ?? false,
      onProgress,
    });
    return { ...removed, modeAction: "removed" };
  }

  const applied = await runPrepareLegacyDocument(
    {
      scope,
      includeHeadersFooters: options.includeHeadersFooters ?? false,
      convertLegacy: false,
      repairUnicode: false,
      hyphenate: true,
      leftMin: options.leftMin ?? 3,
      rightMin: options.rightMin ?? 3,
      useNativeSoftHyphen: useSoftHyphen,
    },
    onProgress
  );
  return { ...applied, modeAction: "applied" };
}

const BAMINI_PENDING_PREFIX = new Set(["n", "N", "i"]);
const PHONETIC_LAYOUTS = new Set<string>(["phonetic-v1", "anjal-phonetic"]);
const PHONETIC_BOUNDARY_RE = /([A-Za-z][A-Za-z_-]*)([\s.,!?;:)\]}]+)$/;
const PHONETIC_PENDING_RE = /([A-Za-z][A-Za-z_-]*)$/;
const PHONETIC_MID_DIGIT_RE = /([A-Za-z][A-Za-z_-]*)([1-5])$/;
const PHONETIC_POST_DIGIT_RE = /([\u0B80-\u0BFF]+)([1-5])$/;
const PHONETIC_MID_CYCLE_RE = /([A-Za-z][A-Za-z_-]*)([\t/])$/;
const PHONETIC_POST_CYCLE_RE = /([\u0B80-\u0BFF]+)([\t/])$/;
const ACTIVE_TAMIL_WORD_RE = /([\u0B80-\u0BFF]+)$/;

// Inverse of canonical [tamil99] consonants in crates/tamil-translit/lexicon/translit.toml
const TAMIL99_BARE_CONSONANT_TO_KEY: Record<string, string> = {
  க: "h",
  ங: "b",
  ச: "[",
  ஞ: "]",
  ட: "o",
  ண: "p",
  த: "l",
  ந: ";",
  ன: "i",
  ப: "j",
  ம: "k",
  ய: "'",
  ர: "m",
  ற: "u",
  ல: "n",
  ள: "y",
  ழ: "/",
  வ: "v",
  ஸ: "Q",
  ஷ: "W",
  ஜ: "E",
  ஹ: "R",
};

function isUrlOrEmailToken(text: string): boolean {
  const tokenMatch = text.match(/(\S+)$/);
  const fullToken = tokenMatch ? tokenMatch[1] : "";
  return /^https?:\/\//i.test(fullToken) || fullToken.includes("@");
}

function mayangoliAnchorScore(word: string): number {
  let score = 0;
  for (const ch of word) {
    if (ch === "\u0BA3" || ch === "\u0BB4" || ch === "\u0BB1") {
      score += 1;
    } else if (ch === "\u0BB3") {
      score += 2;
    }
  }
  return score;
}

export function getCanvasMayangoliCandidates(
  word: string,
  layout: KeyboardLayout,
  limit = 5
): string[] {
  if (!word) return [];
  const rawCands = transliterateSuggestText(word, layout, limit);
  if (rawCands.length <= 1 || /^[A-Za-z]/.test(word)) {
    return rawCands;
  }

  let anchor = rawCands[0];
  let bestScore = mayangoliAnchorScore(anchor);
  for (let i = 1; i < rawCands.length; i++) {
    const cand = rawCands[i];
    const score = mayangoliAnchorScore(cand);
    if (score < bestScore || (score === bestScore && cand < anchor)) {
      bestScore = score;
      anchor = cand;
    }
  }

  if (anchor === word) return rawCands;
  const anchored = transliterateSuggestText(anchor, layout, limit);
  return anchored.includes(word) ? anchored : rawCands;
}

export function extractPendingPhoneticWord(textBeforeCursor: string): string {
  if (!textBeforeCursor || isUrlOrEmailToken(textBeforeCursor)) return "";
  const match = textBeforeCursor.match(PHONETIC_PENDING_RE);
  return match ? match[1] : "";
}

export function extractActiveCanvasMayangoliWord(
  textBeforeCursor: string,
  layout: KeyboardLayout | Exclude<LegacyEncoding, "auto">
): string {
  if (!textBeforeCursor || (layout !== "phonetic-v1" && layout !== "anjal-phonetic")) return "";
  const match = textBeforeCursor.match(ACTIVE_TAMIL_WORD_RE);
  if (!match) return "";
  const word = match[1];
  const candidates = getCanvasMayangoliCandidates(word, layout, 5);
  return candidates.length > 1 ? word : "";
}

/**
 * Live keystroke-by-keystroke / word-boundary converter for Direct Word Typing Mode.
 * - Phonetic & Anjal:
 *   - Converts completed Roman word on whitespace or sentence punctuation.
 *   - Supports direct number-key selection (1–5) mid-word ("vanakkam2" -> "வணக்கம் ") or post-word ("வனக்கம் 2" -> "வணக்கம் ").
 *   - Supports canvas candidate cycling via Tab or "/" mid-word ("malai\t" -> "மழை") or post-word ("மழை\t" -> "மளை").
 * - Tamil99: converts keystroke-by-keystroke, combining bare consonants with vowels, pulli, geminates, and homorganic nasals.
 * - Bamini / Legacy: handles fresh ASCII keys and post-base modifiers right after an already-converted Tamil letter.
 */
export function computeLiveKeystrokeReplacement(
  textBeforeCursor: string,
  layout: KeyboardLayout | Exclude<LegacyEncoding, "auto">
): { replaceTarget: string; unicodeText: string } | null {
  if (!textBeforeCursor) return null;

  if (layout === "phonetic-v1" || layout === "anjal-phonetic") {
    // 1. Mid-word direct number selection (e.g. "vanakkam2" -> "வணக்கம் ") when Mayangoli alternatives exist
    const midDigitMatch = textBeforeCursor.match(PHONETIC_MID_DIGIT_RE);
    if (midDigitMatch && !isUrlOrEmailToken(textBeforeCursor)) {
      const word = midDigitMatch[1];
      const digit = midDigitMatch[2];
      const idx = Number(digit) - 1;
      const candidates = getCanvasMayangoliCandidates(word, layout, 5);
      if (candidates.length > 1 && idx >= 0 && idx < candidates.length) {
        const beforeWord = textBeforeCursor.slice(
          0,
          textBeforeCursor.length - word.length - digit.length
        );
        const prefixMatch = beforeWord.match(
          /((?:[A-Za-z][A-Za-z_-]*[\s.,!?;:)\]}]+)+)$/
        );
        if (prefixMatch && !isUrlOrEmailToken(beforeWord.trimEnd())) {
          const translatedPrefix = prefixMatch[1].replace(/[A-Za-z][A-Za-z_-]*/g, (w) => {
            const t = transliterateText(w, layout, "to_tamil");
            return t && /[\u0B80-\u0BFF]/.test(t) ? t : w;
          });
          return {
            replaceTarget: `${prefixMatch[1]}${word}${digit}`,
            unicodeText: `${translatedPrefix}${candidates[idx]} `,
          };
        }
        return {
          replaceTarget: `${word}${digit}`,
          unicodeText: `${candidates[idx]} `,
        };
      }
    }

    // 2. Post-word attached number selection (e.g. "வனக்கம்2" or "மலை2" -> "மழை "; numbers after space type normally)
    const postDigitMatch = textBeforeCursor.match(PHONETIC_POST_DIGIT_RE);
    if (postDigitMatch) {
      const tamilWord = postDigitMatch[1];
      const digit = postDigitMatch[2];
      const idx = Number(digit) - 1;
      const candidates = getCanvasMayangoliCandidates(tamilWord, layout, 5);
      if (candidates.length > 1 && idx >= 0 && idx < candidates.length) {
        return {
          replaceTarget: `${tamilWord}${digit}`,
          unicodeText: `${candidates[idx]} `,
        };
      }
    }

    // 3. Mid-word canvas cycling via Tab or "/" (e.g. "malai\t" -> "மழை")
    const midCycleMatch = textBeforeCursor.match(PHONETIC_MID_CYCLE_RE);
    if (midCycleMatch && !isUrlOrEmailToken(textBeforeCursor)) {
      const word = midCycleMatch[1];
      const cycleKey = midCycleMatch[2];
      const candidates = getCanvasMayangoliCandidates(word, layout, 5);
      if (candidates.length > 0) {
        const chosen = candidates.length > 1 ? candidates[1] : candidates[0];
        return {
          replaceTarget: `${word}${cycleKey}`,
          unicodeText: chosen,
        };
      }
    }

    // 4. Post-word attached canvas cycling via Tab or "/" (e.g. "மழை\t" -> "மளை")
    const postCycleMatch = textBeforeCursor.match(PHONETIC_POST_CYCLE_RE);
    if (postCycleMatch) {
      const tamilWord = postCycleMatch[1];
      const cycleKey = postCycleMatch[2];
      const candidates = getCanvasMayangoliCandidates(tamilWord, layout, 5);
      if (candidates.length > 1) {
        const currentIndex = Math.max(0, candidates.indexOf(tamilWord));
        const nextIndex = (currentIndex + 1) % candidates.length;
        return {
          replaceTarget: `${tamilWord}${cycleKey}`,
          unicodeText: candidates[nextIndex],
        };
      }
    }

    // 5. Multi-word & partial-next-word commit on whitespace or punctuation
    const multiMatch = textBeforeCursor.match(
      /((?:[A-Za-z][A-Za-z_-]*[\s.,!?;:)\]}]+)+)([A-Za-z][A-Za-z_-]*)?$/
    );
    if (!multiMatch) return null;

    const completedSegment = multiMatch[1];
    const pendingTail = multiMatch[2] ?? "";
    const matchStart = multiMatch.index ?? textBeforeCursor.length - multiMatch[0].length;
    const prefixBefore = textBeforeCursor.slice(0, matchStart);
    if (matchStart > 0 && /[@:/\w.-]$/.test(prefixBefore)) {
      // Avoid translating trailing hostname/path tokens attached to URLs or emails
      const attachedToken = prefixBefore.match(/(\S+)$/)?.[1] ?? "";
      if (/https?:\/\/|@/i.test(attachedToken) || /\.[A-Za-z0-9-]+$/.test(attachedToken)) {
        return null;
      }
    }

    let convertedAny = false;
    const translatedSegment = completedSegment.replace(/[A-Za-z][A-Za-z_-]*/g, (word) => {
      const tamil = transliterateText(word, layout, "to_tamil");
      if (tamil && tamil !== word && /[\u0B80-\u0BFF]/.test(tamil)) {
        convertedAny = true;
        return tamil;
      }
      return word;
    });
    if (!convertedAny) return null;

    return {
      replaceTarget: `${completedSegment}${pendingTail}`,
      unicodeText: `${translatedSegment}${pendingTail}`,
    };
  }

  if (layout === "tamil99") {
    const asciiMatch = textBeforeCursor.match(/[^\s\u0B80-\u0BFF][^\u0B80-\u0BFF\r\n]*$/);
    if (!asciiMatch) return null;

    const rawAscii = asciiMatch[0];
    if (/^https?:\/\//i.test(rawAscii) || rawAscii.includes("@")) return null;

    const beforeAscii = textBeforeCursor.slice(0, textBeforeCursor.length - rawAscii.length);
    let prevBareCons = "";
    if (beforeAscii.length > 0 && /[\u0B80-\u0BFF]$/.test(beforeAscii)) {
      const letters = getTamilLetters(beforeAscii);
      const last = letters[letters.length - 1];
      if (last && TAMIL99_BARE_CONSONANT_TO_KEY[last]) {
        prevBareCons = last;
      }
    }

    const replaceTarget = prevBareCons ? `${prevBareCons}${rawAscii}` : rawAscii;
    const combined = prevBareCons
      ? `${TAMIL99_BARE_CONSONANT_TO_KEY[prevBareCons]}${rawAscii}`
      : rawAscii;

    const converted = transliterateText(combined, "tamil99", "to_tamil");
    if (!converted || converted === replaceTarget || !/[\u0B80-\u0BFF]/.test(converted)) {
      return null;
    }

    return { replaceTarget, unicodeText: converted };
  }

  const asciiMatch = textBeforeCursor.match(/[^\s\u0B80-\u0BFF][^\u0B80-\u0BFF\r\n]*$/);
  if (!asciiMatch) return null;

  let rawAscii = asciiMatch[0];
  // Never rewrite pure numbers, standard sentence punctuation (excluding Bamini `;`), or URLs/emails
  if (/^[0-9.,:!?()[\]{}"'\-/\\@#$%^&*+=<>~`\s]+$/.test(rawAscii)) return null;
  if (/^https?:\/\//i.test(rawAscii) || rawAscii.includes("@")) return null;

  // In Bamini, hold single pending left-side vowel prefix (n=ெ, N=ே, i=ை) for the next consonant key,
  // and split trailing [nNi] off multi-key bursts so e.g. "jkpo;n" converts "jkpo;" -> "தமிழ்" while keeping "n".
  if (layout === "bamini") {
    if (BAMINI_PENDING_PREFIX.has(rawAscii)) {
      return null;
    }
    if (rawAscii.length > 1 && BAMINI_PENDING_PREFIX.has(rawAscii[rawAscii.length - 1])) {
      rawAscii = rawAscii.slice(0, -1);
      if (/^[0-9.,:!?()[\]{}"'\-/\\@#$%^&*+=<>~`\s]+$/.test(rawAscii)) return null;
    }
  }

  const beforeAscii = textBeforeCursor.slice(
    0,
    textBeforeCursor.length - asciiMatch[0].length
  );
  let prevTamilLetter = "";
  if (beforeAscii.length > 0 && /[\u0B80-\u0BFF]$/.test(beforeAscii)) {
    const letters = getTamilLetters(beforeAscii);
    const last = letters[letters.length - 1];
    if (last && /[\u0B80-\u0BFF]/.test(last)) {
      prevTamilLetter = last;
    }
  }

  const replaceTarget = prevTamilLetter ? `${prevTamilLetter}${rawAscii}` : rawAscii;
  const legacyCombined = prevTamilLetter
    ? `${convertUnicodeToLegacy(prevTamilLetter, layout)}${rawAscii}`
    : rawAscii;

  const decoded = convertLegacyToUnicode(legacyCombined, layout).text;
  const repaired = repairTamilText(decoded, {
    fixDuplicatePulli: true,
    reorderVisualVowels: true,
    stripZeroWidth: false,
  }).text;

  if (!repaired || repaired === replaceTarget) return null;
  if (!/[\u0B80-\u0BFF]/.test(repaired)) return null;

  return { replaceTarget, unicodeText: repaired };
}

let lastObservedTextBefore = "";
let lastObservedLayout = "";
let pendingBurstText = "";
let pendingBurstLayout = "";
let pendingBurstTicks = 0;

export function resetLiveTypingCache(): void {
  lastObservedTextBefore = "";
  lastObservedLayout = "";
  pendingBurstText = "";
  pendingBurstLayout = "";
  pendingBurstTicks = 0;
}

function isImmediateTrigger(
  textBefore: string,
  layout: KeyboardLayout | Exclude<LegacyEncoding, "auto">
): boolean {
  if (!textBefore) return false;
  if (PHONETIC_LAYOUTS.has(layout)) {
    return /[\s.,!?;:)\]}1-5\t/]$/.test(textBefore);
  }
  return /\s$/.test(textBefore);
}

/**
 * Hardened live-typing tick: reads text before the collapsed Word cursor, debounces
 * mid-burst keystrokes so fast typing never blocks or teleports the cursor, verifies
 * no new keystrokes arrived mid-sync, and converts all buffered words/tokens in one pass.
 */
export async function runDirectLiveTypingTick(
  layout: KeyboardLayout | Exclude<LegacyEncoding, "auto">,
  unicodeFont: string,
  isStillActive: () => boolean
): Promise<{
  converted: boolean;
  unchanged?: boolean;
  activeInput?: boolean;
  original?: string;
  unicode?: string;
  pendingWord?: string;
  activeTamilWord?: string;
}> {
  if (!isStillActive()) return { converted: false };
  let outcome: {
    converted: boolean;
    unchanged?: boolean;
    activeInput?: boolean;
    original?: string;
    unicode?: string;
    pendingWord?: string;
    activeTamilWord?: string;
  } = {
    converted: false,
  };

  await Word.run(async (context) => {
    const sel = context.document.getSelection();
    sel.load("text");
    const para = sel.paragraphs.getFirst();
    const beforeCursor = para.getRange(Word.RangeLocation.start).expandTo(sel);
    beforeCursor.load("text");
    await context.sync();

    if (!isStillActive()) return;
    if (sel.text && sel.text.length > 0) {
      outcome = { converted: false, unchanged: true };
      return;
    }

    const textBefore = beforeCursor.text || "";
    if (textBefore === lastObservedTextBefore && layout === lastObservedLayout) {
      outcome = { converted: false, unchanged: true };
      return;
    }

    const isPhonetic = PHONETIC_LAYOUTS.has(layout);
    const immediate = isImmediateTrigger(textBefore, layout);
    const burstChanged = textBefore !== pendingBurstText || layout !== pendingBurstLayout;
    if (burstChanged) {
      pendingBurstText = textBefore;
      pendingBurstLayout = layout;
      pendingBurstTicks++;
      // Wait briefly when typing mid-word without a space/delimiter so fast bursts convert in one pass
      if (!immediate && pendingBurstTicks < 3) {
        const pendingWord = isPhonetic ? extractPendingPhoneticWord(textBefore) : "";
        const activeTamilWord =
          isPhonetic && !pendingWord ? extractActiveCanvasMayangoliWord(textBefore, layout) : "";
        outcome = {
          converted: false,
          activeInput: true,
          pendingWord,
          activeTamilWord,
        };
        return;
      }
    }
    pendingBurstTicks = 0;

    const live = computeLiveKeystrokeReplacement(textBefore, layout);
    if (!live) {
      lastObservedTextBefore = textBefore;
      lastObservedLayout = layout;
      const pendingWord = isPhonetic ? extractPendingPhoneticWord(textBefore) : "";
      const activeTamilWord =
        isPhonetic && !pendingWord ? extractActiveCanvasMayangoliWord(textBefore, layout) : "";
      outcome = {
        converted: false,
        activeInput: true,
        pendingWord,
        activeTamilWord,
      };
      return;
    }

    // Word Range.search does not match literal "\t" reliably; search the base token before Tab and expand to sel
    const searchQuery = live.replaceTarget.includes("\t")
      ? live.replaceTarget.replace(/[\s\t]+$/, "")
      : live.replaceTarget;
    if (!searchQuery) return;

    const hits = beforeCursor.search(searchQuery, {
      matchCase: true,
      matchWildcards: false,
    });
    const currentSel = context.document.getSelection();
    const currentBefore = currentSel.paragraphs.getFirst().getRange(Word.RangeLocation.start).expandTo(currentSel);
    currentBefore.load("text");
    hits.load("items");
    await context.sync();

    if (!isStillActive() || hits.items.length === 0) return;

    // If new keys arrived in Word during the search sync, abort this write so next tick batches everything cleanly
    const latestBefore = currentBefore.text || "";
    if (latestBefore !== textBefore) {
      pendingBurstText = latestBefore;
      pendingBurstLayout = layout;
      outcome = { converted: false, activeInput: true };
      return;
    }

    const lastHit = hits.items[hits.items.length - 1];
    const replaceRange = live.replaceTarget.includes("\t") ? lastHit.expandTo(sel) : lastHit;
    const inserted = replaceRange.insertText(live.unicodeText, Word.InsertLocation.replace);
    if (textBefore.endsWith(live.replaceTarget)) {
      if (unicodeFont) {
        inserted.font.name = unicodeFont;
      }
      inserted.select(Word.SelectionMode.end);
    } else if (unicodeFont) {
      inserted.font.name = unicodeFont;
    }
    await context.sync();

    lastObservedTextBefore = "";
    lastObservedLayout = "";
    pendingBurstText = "";
    pendingBurstLayout = "";
    pendingBurstTicks = 0;
    const activeTamilWord = isPhonetic
      ? extractActiveCanvasMayangoliWord(live.unicodeText, layout)
      : "";
    outcome = {
      converted: true,
      activeInput: true,
      original: live.replaceTarget,
      unicode: live.unicodeText,
      pendingWord: "",
      activeTamilWord,
    };
  });

  return outcome;
}

export async function readWordAtCursorOrSelection(): Promise<string> {
  let word = "";
  await Word.run(async (context) => {
    const sel = context.document.getSelection();
    sel.load("text");
    const para = sel.paragraphs.getFirst();
    const beforeCursor = para.getRange(Word.RangeLocation.start).expandTo(sel);
    beforeCursor.load("text");
    await context.sync();

    if (sel.text && sel.text.trim().length > 0) {
      word = sel.text.trim();
      return;
    }

    const before = beforeCursor.text || "";
    const match = before.match(/([\u0B80-\u0BFF]+|[A-Za-z][A-Za-z_-]*)$/);
    word = match ? match[1] : "";
  });
  return word;
}

export async function replaceTrailingOrSelectedWord(
  targetWord: string,
  replacementWord: string,
  unicodeFont?: string
): Promise<boolean> {
  if (!targetWord || !replacementWord || targetWord === replacementWord) return false;
  let replaced = false;
  await Word.run(async (context) => {
    const sel = context.document.getSelection();
    sel.load("text");
    const para = sel.paragraphs.getFirst();
    const beforeCursor = para.getRange(Word.RangeLocation.start).expandTo(sel);
    beforeCursor.load("text");
    await context.sync();

    if (sel.text && sel.text.trim() === targetWord) {
      const inserted = sel.insertText(replacementWord, Word.InsertLocation.replace);
      if (unicodeFont) {
        inserted.font.name = unicodeFont;
      }
      inserted.select(Word.SelectionMode.end);
      await context.sync();
      replaced = true;
      return;
    }

    const textBefore = beforeCursor.text || "";
    const trailingSpace = textBefore.match(/(\s+)$/)?.[1] ?? "";
    const hits = beforeCursor.search(targetWord, {
      matchCase: true,
      matchWildcards: false,
    });
    hits.load("items");
    await context.sync();
    if (hits.items.length === 0) return;

    const lastHit = hits.items[hits.items.length - 1];
    const replaceRange = trailingSpace ? lastHit.expandTo(sel) : lastHit;
    const inserted = replaceRange.insertText(`${replacementWord}${trailingSpace}`, Word.InsertLocation.replace);
    if (unicodeFont) {
      inserted.font.name = unicodeFont;
    }
    inserted.select(Word.SelectionMode.end);
    await context.sync();
    replaced = true;
  });
  return replaced;
}

export async function runRemoveHyphens(
  scope: TargetScope,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary> {
  return runBatchedOoxmlTransform(scope, (xml) => removeOoxmlHyphens(xml), { onProgress });
}
