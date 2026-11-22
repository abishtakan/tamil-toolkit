/**
 * Client-side PDF.js text-layer extraction for legacy-encoded Tamil PDFs.
 * Runs 100% in the browser (no uploads, no OCR).
 */

export type PdfCodecHint =
  | "bamini-v1"
  | "tscii-1.7-v1"
  | "tab-v1"
  | "tam-v1"
  | "anjal-v1"
  | "vanavil-avvaiyar-cid-v1"
  | "lt-tm-cid-v1"
  | "senthamil-cid-v1"
  | "shree-tam-cid-v1"
  | "softview-amudham-cid-v1"
  | "tbo-tboomi-cid-v1"
  | null;

export interface PdfExtractionResult {
  fileName: string;
  pageCount: number;
  extractedPages: number;
  text: string;
  fontNames: string[];
  suggestedProfile: PdfCodecHint;
  hasTextLayer: boolean;
}

const MAX_PDF_BYTES = 25 * 1024 * 1024; // 25 MiB safety cap
const MAX_PDF_PAGES = 200;

/**
 * Infer a likely legacy Tamil codec profile from embedded PDF font family names.
 */
export function inferCodecFromPdfFonts(fontNames: string[]): PdfCodecHint {
  const joined = fontNames.join(" ").toLowerCase();
  if (/\bbamini\b|baamini/.test(joined)) return "bamini-v1";
  if (/vanavil|avvaiyar/.test(joined)) return "vanavil-avvaiyar-cid-v1";
  if (/lt-tm|lttm|indoword/.test(joined)) return "lt-tm-cid-v1";
  if (/senthamil|stmzh/.test(joined)) return "senthamil-cid-v1";
  if (/shree[-_ ]?tam|shreetam/.test(joined)) return "shree-tam-cid-v1";
  if (/softview|amudham/.test(joined)) return "softview-amudham-cid-v1";
  if (/tboomi|tamilbible|\btbo\b/.test(joined)) return "tbo-tboomi-cid-v1";
  if (/tscii|\btsc[_-]/.test(joined)) return "tscii-1.7-v1";
  if (/\btab[_-]|\btab\b/.test(joined)) return "tab-v1";
  if (/\btam[_-]|\btam\b/.test(joined)) return "tam-v1";
  if (/anjal/.test(joined)) return "anjal-v1";
  return null;
}

/**
 * Extract selectable text runs and font hints from a PDF buffer using PDF.js.
 * Does not perform OCR on scanned image-only PDFs.
 */
export async function extractPdfTextLayer(
  data: ArrayBuffer | Uint8Array,
  fileName = "document.pdf",
): Promise<PdfExtractionResult> {
  const bytes = data instanceof Uint8Array ? data : new Uint8Array(data);
  if (bytes.byteLength === 0) {
    throw new Error("The selected PDF file is empty.");
  }
  if (bytes.byteLength > MAX_PDF_BYTES) {
    throw new Error("PDF exceeds the 25 MB client-side safety limit.");
  }

  const pdfjs = await import("pdfjs-dist/legacy/build/pdf.mjs");
  if (!pdfjs.GlobalWorkerOptions.workerSrc) {
    const workerUrl = new URL(
      "pdfjs-dist/legacy/build/pdf.worker.min.mjs",
      import.meta.url,
    );
    pdfjs.GlobalWorkerOptions.workerSrc = workerUrl.toString();
  }

  const loadingTask = pdfjs.getDocument({
    data: bytes,
    useSystemFonts: true,
  });

  const pdf = await loadingTask.promise;
  try {
    const pageCount = pdf.numPages;
    const limit = Math.min(pageCount, MAX_PDF_PAGES);
    const pages: string[] = [];
    const fontSet = new Set<string>();

    for (let pageNumber = 1; pageNumber <= limit; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber);
      const content = await page.getTextContent();

      if (content.styles && typeof content.styles === "object") {
        for (const style of Object.values(content.styles)) {
          const family = (style as { fontFamily?: string }).fontFamily;
          if (family && typeof family === "string") {
            fontSet.add(family);
          }
        }
      }

      const lines: string[] = [];
      let currentLine = "";
      for (const item of content.items) {
        if (!("str" in item)) continue;
        const textItem = item as { str: string; hasEOL?: boolean; fontName?: string };
        if (textItem.fontName) {
          fontSet.add(textItem.fontName);
        }
        currentLine += textItem.str;
        if (textItem.hasEOL) {
          lines.push(currentLine);
          currentLine = "";
        }
      }
      if (currentLine.length > 0) {
        lines.push(currentLine);
      }
      const pageText = lines.join("\n").trim();
      if (pageText.length > 0) {
        pages.push(pageText);
      }
    }

    const text = pages.join("\n\n");
    const fontNames = Array.from(fontSet);
    return {
      fileName,
      pageCount,
      extractedPages: limit,
      text,
      fontNames,
      suggestedProfile: inferCodecFromPdfFonts(fontNames),
      hasTextLayer: text.trim().length > 0,
    };
  } finally {
    await loadingTask.destroy();
  }
}
