/**
 * OOXML Run-Aware Processor for Microsoft Word (Office.js)
 *
 * Transforms text inside <w:t> elements per <w:r> run while strictly preserving
 * inline character formatting (<w:rPr> bold, italic, underline, size, color),
 * tables, hyperlinks, and English/Latin run fonts.
 */

export function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function unescapeXml(xmlText: string): string {
  return xmlText
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/&amp;/g, "&");
}

function updateRunFont(runXml: string, fontFamily: string): string {
  if (!fontFamily.trim()) return runXml;
  const safeFont = escapeXml(fontFamily.trim());
  const rFontsTag = `<w:rFonts w:ascii="${safeFont}" w:hAnsi="${safeFont}" w:cs="${safeFont}" w:eastAsia="${safeFont}"/>`;

  if (/<w:rFonts\b[^>]*\/>/.test(runXml)) {
    return runXml.replace(/<w:rFonts\b[^>]*\/>/g, rFontsTag);
  }
  if (/<w:rPr>/.test(runXml)) {
    return runXml.replace("<w:rPr>", `<w:rPr>${rFontsTag}`);
  }
  // Inject <w:rPr> immediately after opening <w:r ...>
  return runXml.replace(/(<w:r\b[^>]*>)/, `$1<w:rPr>${rFontsTag}</w:rPr>`);
}

/**
 * Applies a pure text transformation to every <w:t> node in an OOXML payload,
 * preserving xml:space="preserve" and all sibling XML structure.
 */
export function transformOoxmlTextNodes(
  ooxml: string,
  transformText: (plainText: string) => string
): string {
  return ooxml.replace(
    /(<w:t\b[^>]*>)([\s\S]*?)(<\/w:t>)/g,
    (_full, openTag: string, innerXml: string, closeTag: string) => {
      const decoded = unescapeXml(innerXml);
      const updated = transformText(decoded);
      if (updated === decoded) {
        return `${openTag}${innerXml}${closeTag}`;
      }
      const needsPreserve = /^\s|\s$/.test(updated);
      const normalizedOpen =
        needsPreserve && !openTag.includes("xml:space=")
          ? openTag.replace("<w:t", '<w:t xml:space="preserve"')
          : openTag;
      return `${normalizedOpen}${escapeXml(updated)}${closeTag}`;
    }
  );
}

/**
 * Run-aware OOXML transformation: transforms <w:t> inside each <w:r> independently
 * and ONLY updates <w:rFonts> on runs whose text actually changed and contains
 * Tamil Unicode characters—leaving English/Latin/number runs in their original font.
 */
export function transformOoxmlRunsWithFont(
  ooxml: string,
  transformText: (plainText: string) => string,
  unicodeFont?: string
): { xml: string; runsChanged: number } {
  let runsChanged = 0;

  const xml = ooxml.replace(/<w:r\b[^>]*>[\s\S]*?<\/w:r>/g, (runXml) => {
    let changedInRun = false;
    let hasTamilResult = false;

    const updatedRun = runXml.replace(
      /(<w:t\b[^>]*>)([\s\S]*?)(<\/w:t>)/g,
      (_full, openTag: string, innerXml: string, closeTag: string) => {
        const decoded = unescapeXml(innerXml);
        const updated = transformText(decoded);
        if (updated === decoded) {
          return `${openTag}${innerXml}${closeTag}`;
        }
        changedInRun = true;
        if (/[\u0B80-\u0BFF]/.test(updated)) {
          hasTamilResult = true;
        }
        const needsPreserve = /^\s|\s$/.test(updated);
        const normalizedOpen =
          needsPreserve && !openTag.includes("xml:space=")
            ? openTag.replace("<w:t", '<w:t xml:space="preserve"')
            : openTag;
        return `${normalizedOpen}${escapeXml(updated)}${closeTag}`;
      }
    );

    if (!changedInRun) return runXml;
    runsChanged++;
    if (unicodeFont && hasTamilResult) {
      return updateRunFont(updatedRun, unicodeFont);
    }
    return updatedRun;
  });

  return { xml, runsChanged };
}

/**
 * Strips all Word <w:softHyphen/> elements as well as U+00AD and U+200B inside <w:t>,
 * removes transient <w:proofErr/> markers and empty runs left behind by Word-normalized
 * <w:r><w:softHyphen/></w:r>, and iteratively merges adjacent <w:r> runs with identical
 * <w:rPr> and adjacent <w:t> nodes so 3+, 4+, or 5+ fragment words always recombine
 * into one intact word before re-hyphenating or switching modes.
 */
export function removeOoxmlHyphens(ooxml: string): string {
  // 1. Remove <w:softHyphen/> and transient Word spellcheck <w:proofErr/> markers
  let cleaned = ooxml
    .replace(/<w:softHyphen\s*\/>/g, "")
    .replace(/<w:proofErr\b[^>]*\/>/g, "");

  // 2. Remove empty <w:r> elements that only held <w:softHyphen/> (never crossing </w:r>)
  cleaned = cleaned.replace(/<w:r\b[^>]*>[\s\S]*?<\/w:r>/g, (runXml) => {
    const withoutRPr = runXml
      .replace(/^<w:r\b[^>]*>/, "")
      .replace(/<\/w:r>$/, "")
      .replace(/<w:rPr>[\s\S]*?<\/w:rPr>/, "")
      .trim();
    return withoutRPr.length === 0 ? "" : runXml;
  });

  // 3. Iteratively merge adjacent <w:t> AND adjacent identical-<w:rPr> <w:r> runs
  let prev = "";
  while (cleaned !== prev) {
    prev = cleaned;

    // 3a. Merge adjacent <w:t> nodes within the same <w:r>
    cleaned = cleaned.replace(
      /(<w:t\b[^>]*>)([\s\S]*?)<\/w:t><w:t\b[^>]*>([\s\S]*?)(<\/w:t>)/g,
      (_m, openTag: string, a: string, b: string, closeTag: string) => {
        const combined = a + b;
        const decoded = unescapeXml(combined);
        const normalizedOpen =
          /^\s|\s$/.test(decoded) && !openTag.includes("xml:space=")
            ? openTag.replace("<w:t", '<w:t xml:space="preserve"')
            : openTag;
        return `${normalizedOpen}${combined}${closeTag}`;
      }
    );

    // 3b. Merge adjacent <w:r> elements with identical <w:rPr> (or both having none)
    cleaned = cleaned.replace(
      /<w:r\b[^>]*>(\s*<w:rPr>(?:(?!<\/w:rPr>)[\s\S])*<\/w:rPr>)?\s*(<w:t\b[^>]*>(?:(?!<\/w:t>)[\s\S])*<\/w:t>)\s*<\/w:r>\s*<w:r\b[^>]*>(\s*<w:rPr>(?:(?!<\/w:rPr>)[\s\S])*<\/w:rPr>)?\s*(<w:t\b[^>]*>(?:(?!<\/w:t>)[\s\S])*<\/w:t>)\s*<\/w:r>/g,
      (
        match,
        rPr1: string | undefined,
        t1: string,
        rPr2: string | undefined,
        t2: string
      ) => {
        const norm1 = (rPr1 || "").trim();
        const norm2 = (rPr2 || "").trim();
        if (norm1 !== norm2) return match;
        return `<w:r>${norm1}${t1}${t2}</w:r>`;
      }
    );
  }

  // 4. Strip U+00AD and U+200B inside <w:t> (never touches manual ASCII '-')
  return transformOoxmlTextNodes(cleaned, (txt) => txt.replace(/[\u00AD\u200B]/g, ""));
}

export function hasOoxmlSoftHyphens(ooxml: string): boolean {
  return /<w:softHyphen\s*\/>|\u00AD/.test(ooxml);
}

export function hasOoxmlZeroWidthWrap(ooxml: string): boolean {
  return /\u200B/.test(ooxml);
}

/**
 * Smart toggle for Word hyphenation / invisible wrap:
 * - If the target mode is ALREADY active on `ooxml`, removes it (toggles OFF).
 * - Otherwise strips any other break mode and applies the requested mode (toggles ON / switches mode).
 */
export function toggleHyphenateOoxml(
  ooxml: string,
  hyphenateFn: (plainText: string, delimiter: string) => string,
  useNativeSoftHyphen = true
): { xml: string; action: "applied" | "removed" | "unchanged" } {
  const alreadyInRequestedMode = useNativeSoftHyphen
    ? hasOoxmlSoftHyphens(ooxml) && !hasOoxmlZeroWidthWrap(ooxml)
    : hasOoxmlZeroWidthWrap(ooxml) && !hasOoxmlSoftHyphens(ooxml);

  if (alreadyInRequestedMode) {
    const cleaned = removeOoxmlHyphens(ooxml);
    return { xml: cleaned, action: cleaned !== ooxml ? "removed" : "unchanged" };
  }

  const applied = hyphenateOoxml(ooxml, hyphenateFn, useNativeSoftHyphen);
  return { xml: applied, action: applied !== ooxml ? "applied" : "unchanged" };
}

/**
 * Applies Tamil syllabic hyphenation to an OOXML payload.
 * When `useNativeSoftHyphen` is true, injects Word's native `<w:softHyphen/>`
 * elements between split `<w:t>` fragments so Word shows `-` only on wrap.
 * When false, injects Zero-Width Space (`\u200B`) for clean wrap without `-`.
 */
export function hyphenateOoxml(
  ooxml: string,
  hyphenateFn: (plainText: string, delimiter: string) => string,
  useNativeSoftHyphen = true
): string {
  const cleaned = removeOoxmlHyphens(ooxml);
  if (!useNativeSoftHyphen) {
    return transformOoxmlTextNodes(cleaned, (txt) => hyphenateFn(txt, "\u200B"));
  }

  return cleaned.replace(
    /(<w:t\b[^>]*>)([\s\S]*?)(<\/w:t>)/g,
    (_full, openTag: string, innerXml: string, closeTag: string) => {
      const decoded = unescapeXml(innerXml);
      const withMarker = hyphenateFn(decoded, "\u00AD");
      if (!withMarker.includes("\u00AD")) {
        return `${openTag}${innerXml}${closeTag}`;
      }
      const parts = withMarker.split("\u00AD");
      return parts
        .map((part) => {
          const needsPreserve = /^\s|\s$/.test(part);
          const tag =
            needsPreserve && !openTag.includes("xml:space=")
              ? openTag.replace("<w:t", '<w:t xml:space="preserve"')
              : openTag;
          return `${tag}${escapeXml(part)}${closeTag}`;
        })
        .join("<w:softHyphen/>");
    }
  );
}

/**
 * Legacy export kept for compatibility: applies font family across all runs.
 * Prefer `transformOoxmlRunsWithFont` so non-Tamil runs keep their fonts.
 */
export function applyOoxmlUnicodeFont(ooxml: string, fontFamily: string): string {
  if (!fontFamily.trim()) return ooxml;
  return ooxml.replace(/<w:r\b[^>]*>[\s\S]*?<\/w:r>/g, (runXml) =>
    updateRunFont(runXml, fontFamily)
  );
}
