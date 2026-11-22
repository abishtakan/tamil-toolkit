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
  LegacyEncoding,
  TargetLegacyEncoding,
  convertLegacyToUnicode,
  convertUnicodeToLegacy,
  getTamilLetters,
  hyphenateText,
  repairTamilText,
  sortTableRows,
  sortTamilLines,
  tamilAwareReplace,
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

/**
 * Live keystroke-by-keystroke incremental converter for Direct Word Typing Mode.
 * Handles fresh ASCII keys AND post-base modifiers right after an already-converted
 * Tamil letter (e.g., "தமிழ" + ";" -> "தமிழ்", "கெ" + "h" -> "கொ") by round-tripping
 * the preceding Tamil letter through Rust's legacy codec.
 */
export function computeLiveKeystrokeReplacement(
  textBeforeCursor: string,
  layout: Exclude<LegacyEncoding, "auto">
): { replaceTarget: string; unicodeText: string } | null {
  if (!textBeforeCursor) return null;

  const asciiMatch = textBeforeCursor.match(/([^\s\u0B80-\u0BFF]+)$/);
  if (!asciiMatch) return null;

  const rawAscii = asciiMatch[1];
  // Never rewrite pure numbers, standard sentence punctuation (excluding Bamini `;`), or URLs/emails
  if (/^[0-9.,:!?()[\]{}"'\-/\\@#$%^&*+=<>~`]+$/.test(rawAscii)) return null;
  if (/^https?:\/\//i.test(rawAscii) || rawAscii.includes("@")) return null;

  // In Bamini, hold single pending left-side vowel prefix (n=ெ, N=ே, i=ை) for the next consonant key
  if (layout === "bamini" && BAMINI_PENDING_PREFIX.has(rawAscii)) {
    return null;
  }

  const beforeAscii = textBeforeCursor.slice(0, textBeforeCursor.length - rawAscii.length);
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

/**
 * Hardened live-typing tick: reads text before the collapsed Word cursor, computes
 * the exact trailing replacement via Rust/WASM, re-checks `isStillActive()` to prevent
 * late writes after Stop, and replaces the exact trailing occurrence in-place.
 */
export async function runDirectLiveTypingTick(
  layout: Exclude<LegacyEncoding, "auto">,
  unicodeFont: string,
  isStillActive: () => boolean
): Promise<{ converted: boolean; original?: string; unicode?: string }> {
  if (!isStillActive()) return { converted: false };
  let outcome: { converted: boolean; original?: string; unicode?: string } = { converted: false };

  await Word.run(async (context) => {
    const sel = context.document.getSelection();
    sel.load("text");
    const para = sel.paragraphs.getFirst();
    const beforeCursor = para.getRange(Word.RangeLocation.start).expandTo(sel);
    beforeCursor.load("text");
    await context.sync();

    if (!isStillActive()) return;
    if (sel.text && sel.text.length > 0) return;

    const textBefore = beforeCursor.text || "";
    const live = computeLiveKeystrokeReplacement(textBefore, layout);
    if (!live) return;

    const hits = beforeCursor.search(live.replaceTarget, { matchCase: true });
    hits.load("items");
    await context.sync();

    if (!isStillActive() || hits.items.length === 0) return;

    const lastHit = hits.items[hits.items.length - 1];
    const inserted = lastHit.insertText(live.unicodeText, Word.InsertLocation.replace);
    if (unicodeFont) {
      inserted.font.name = unicodeFont;
    }
    inserted.select(Word.SelectionMode.end);
    await context.sync();

    outcome = {
      converted: true,
      original: live.replaceTarget,
      unicode: live.unicodeText,
    };
  });

  return outcome;
}

export async function runRemoveHyphens(
  scope: TargetScope,
  onProgress?: (p: BatchProgress) => void
): Promise<TransformSummary> {
  return runBatchedOoxmlTransform(scope, (xml) => removeOoxmlHyphens(xml), { onProgress });
}
