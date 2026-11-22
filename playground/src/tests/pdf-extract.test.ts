import { describe, expect, it } from "vitest";
import { extractPdfTextLayer, inferCodecFromPdfFonts } from "../lib/pdf-extract";

/**
 * Build a minimal valid single-page PDF 1.4 containing the given ASCII text stream.
 */
function buildMinimalPdf(text: string): Uint8Array {
  const escaped = text.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
  const stream = `BT /F1 12 Tf 72 720 Td (${escaped}) Tj ET\n`;
  const objects = [
    "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
    "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
    "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
    "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    `5 0 obj << /Length ${stream.length} >> stream\n${stream}endstream endobj\n`,
  ];

  let body = "%PDF-1.4\n";
  const offsets: number[] = [0];
  for (const obj of objects) {
    offsets.push(body.length);
    body += obj;
  }
  const xrefPos = body.length;
  body += `xref\n0 ${objects.length + 1}\n`;
  body += "0000000000 65535 f \n";
  for (let i = 1; i < offsets.length; i += 1) {
    body += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
  }
  body += `trailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefPos}\n%%EOF\n`;
  return new TextEncoder().encode(body);
}

describe("pdf-extract client-side text layer", () => {
  it("infers legacy Tamil codec profiles from PDF font names", () => {
    expect(inferCodecFromPdfFonts(["Bamini-Regular"])).toBe("bamini-v1");
    expect(inferCodecFromPdfFonts(["Vanavil-Avvaiyar"])).toBe("vanavil-avvaiyar-cid-v1");
    expect(inferCodecFromPdfFonts(["LT-TM-Barani"])).toBe("lt-tm-cid-v1");
    expect(inferCodecFromPdfFonts(["Senthamil-Regular"])).toBe("senthamil-cid-v1");
    expect(inferCodecFromPdfFonts(["SHREE-TAM-0802"])).toBe("shree-tam-cid-v1");
    expect(inferCodecFromPdfFonts(["Softview-Amudham"])).toBe("softview-amudham-cid-v1");
    expect(inferCodecFromPdfFonts(["Tboomi-Regular"])).toBe("tbo-tboomi-cid-v1");
    expect(inferCodecFromPdfFonts(["TSC_Times"])).toBe("tscii-1.7-v1");
    expect(inferCodecFromPdfFonts(["TAB-Anna"])).toBe("tab-v1");
    expect(inferCodecFromPdfFonts(["TAM_Kadal"])).toBe("tam-v1");
    expect(inferCodecFromPdfFonts(["Anjal-Regular"])).toBe("anjal-v1");
    expect(inferCodecFromPdfFonts(["Helvetica", "Times-Roman"])).toBeNull();
  });

  it("rejects empty PDF buffers", async () => {
    await expect(extractPdfTextLayer(new Uint8Array(0), "empty.pdf")).rejects.toThrow(
      /empty/i,
    );
  });

  it("extracts legacy Bamini text layer from a real PDF document", async () => {
    const pdfBytes = buildMinimalPdf("jkpo;");
    const result = await extractPdfTextLayer(pdfBytes, "sample.pdf");
    expect(result.fileName).toBe("sample.pdf");
    expect(result.pageCount).toBe(1);
    expect(result.extractedPages).toBe(1);
    expect(result.hasTextLayer).toBe(true);
    expect(result.text).toContain("jkpo;");
  });
});
