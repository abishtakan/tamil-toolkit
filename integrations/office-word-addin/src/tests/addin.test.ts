import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, describe, expect, it } from "vitest";

import { renderManifestXml } from "../../scripts/build-manifest.mjs";
import {
  applyOoxmlUnicodeFont,
  hyphenateOoxml,
  removeOoxmlHyphens,
  toggleHyphenateOoxml,
  transformOoxmlRunsWithFont,
  transformOoxmlTextNodes,
} from "../lib/ooxml.js";
import { computeLiveKeystrokeReplacement } from "../lib/word-adapter.js";
import {
  TRADITIONAL_SYMBOLS_PALETTE,
  buildTamilDateStamp,
  convertDigits,
  convertLegacyToUnicode,
  convertUnicodeToLegacy,
  formatTraditionalInteger,
  getTransliterationSchemes,
  hyphenateText,
  initTamilEngineSync,
  inspectDocumentText,
  mixedFractionToWords,
  numberToTamilWords,
  removeHyphens,
  repairTamilText,
  sortTableRows,
  sortTamilLines,
  tamilAwareReplace,
  transliterateSuggestText,
  transliterateText,
  wordsToNumber,
} from "../lib/tamil-engine.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const addinDir = path.resolve(__dirname, "..", "..");
const wasmPath = path.join(addinDir, "src", "wasm", "tamil_toolkit_bg.wasm");

beforeAll(() => {
  const bytes = fs.readFileSync(wasmPath);
  initTamilEngineSync(bytes);
});

describe("Tamil Word Add-in Engine (Real Slim Rust/WASM)", () => {
  it("converts Bamini & TSCII bidirectionally with auto-detection", () => {
    const unicodeSample = "தமிழ் மொழி";
    const bamini = convertUnicodeToLegacy(unicodeSample, "bamini");
    expect(bamini).not.toBe(unicodeSample);

    const decoded = convertLegacyToUnicode(bamini, "bamini");
    expect(decoded.text).toBe(unicodeSample);

    const tscii = convertUnicodeToLegacy(unicodeSample, "tscii");
    const decodedTscii = convertLegacyToUnicode(tscii, "tscii");
    expect(decodedTscii.text).toBe(unicodeSample);

    // Hardened live keystroke-by-keystroke Bamini simulation: j -> k -> p -> o -> ; => தமிழ்
    let doc = "";
    for (const key of ["j", "k", "p", "o", ";"]) {
      doc += key;
      const step = computeLiveKeystrokeReplacement(doc, "bamini");
      if (step) {
        doc = doc.slice(0, doc.length - step.replaceTarget.length) + step.unicodeText;
      }
    }
    expect(doc).toBe("தமிழ்");

    // Live left-kombu + right-kaal simulation: n -> f -> h => கொ
    let kombuDoc = "n";
    expect(computeLiveKeystrokeReplacement(kombuDoc, "bamini")).toBeNull();
    kombuDoc += "f";
    const s1 = computeLiveKeystrokeReplacement(kombuDoc, "bamini");
    expect(s1?.unicodeText).toBe("கெ");
    kombuDoc = s1!.unicodeText + "h";
    expect(computeLiveKeystrokeReplacement(kombuDoc, "bamini")?.unicodeText).toBe("கொ");
  });

  it("repairs malformed Tamil Unicode (duplicate pulli, visual left kombu, zero-width)", () => {
    // Duplicate pulli: க் + ் + அ, plus zero-width space
    const malformed = "\u0B95\u0BCD\u0BCD\u200B\u0B85";
    const repaired = repairTamilText(malformed, {
      fixDuplicatePulli: true,
      reorderVisualVowels: true,
      stripZeroWidth: true,
    });
    expect(repaired.changed).toBe(true);
    expect(repaired.text).toBe("\u0B95\u0BCD\u0B85");
    expect(repaired.diagnostics.duplicate_pullis_removed).toBeGreaterThanOrEqual(1);
    expect(repaired.diagnostics.zero_width_removed).toBeGreaterThanOrEqual(1);

    // Clean words with attached ெ/ே/ை before consonants must not be flagged or corrupted
    for (const clean of ["பல்கலைக்கழகம்", "சென்னை வேலை பெண்"]) {
      const cleanRes = repairTamilText(clean, {
        fixDuplicatePulli: true,
        reorderVisualVowels: true,
        stripZeroWidth: false,
      });
      expect(cleanRes.changed).toBe(false);
      expect(cleanRes.text).toBe(clean);
      expect(cleanRes.diagnostics.visual_left_kombu_reordered).toBe(0);
    }
  });

  it("performs Tamil-aware Find & Replace across zero-width & Mayangoli variants", () => {
    const textWithZw = "த\u200Bமிழ் நாடு மற்றும் தமிள் இலக்கியம்";
    const exact = tamilAwareReplace(textWithZw, "தமிழ்", "செந்தமிழ்", { fuzzyMayangoli: false });
    expect(exact.count).toBe(1);
    expect(exact.text).toContain("செந்தமிழ் நாடு");

    const fuzzy = tamilAwareReplace(textWithZw, "தமிழ்", "செந்தமிழ்", { fuzzyMayangoli: true });
    expect(fuzzy.count).toBe(2);
  });

  it("sorts Tamil paragraphs and tables in authentic Akara Varisai (Mei before Uyirmei)", () => {
    const unsorted = ["கடல்", "அம்மா", "க்ஷேமம்", "ஆடு", "இலை"];
    const sorted = sortTamilLines(unsorted, { profile: "agara-v1", descending: false });
    expect(sorted[0]).toBe("அம்மா");
    expect(sorted[1]).toBe("ஆடு");
    expect(sorted[2]).toBe("இலை");

    const numbered = ["2. கடல்", "", "1. அம்மா"];
    const sortedNumbered = sortTamilLines(numbered, {
      ignoreLeadingNumbers: true,
      preserveEmptyPositions: true,
    });
    expect(sortedNumbered).toEqual(["1. அம்மா", "", "2. கடல்"]);

    const table = [
      ["பெயர்", "ஊர்"],
      ["கண்ணன்", "மதுரை"],
      ["அருண்", "சென்னை"],
    ];
    const sortedTable = sortTableRows(table, 0, { hasHeader: true });
    expect(sortedTable[0]).toEqual(["பெயர்", "ஊர்"]);
    expect(sortedTable[1][0]).toBe("அருண்");
    expect(sortedTable[2][0]).toBe("கண்ணன்");
  });

  it("formats numerals, currency words, Tamil digits, and traditional integers", () => {
    const words = numberToTamilWords("123", "cardinal", { locale: "TN" });
    expect(words.length).toBeGreaterThan(0);

    const currency = numberToTamilWords("1250.50", "currency", { locale: "TN", currency: "INR" });
    expect(currency).toContain("ரூபாய்");

    const lkr = numberToTamilWords("500", "currency", { locale: "SL", currency: "LKR" });
    expect(lkr).toContain("ரூபா");

    expect(convertDigits("2026", "tamil")).toBe("௨௦௨௬");
    expect(convertDigits("௨௦௨௬", "latin")).toBe("2026");
    expect(formatTraditionalInteger(1000)).toBe("௲");
    expect(TRADITIONAL_SYMBOLS_PALETTE.length).toBeGreaterThanOrEqual(10);
  });

  it("builds Tamil Calendar & Panchangam stamps for Thirukanitham and Vakya", () => {
    const drik = buildTamilDateStamp(2026, 4, 14, {
      profile: "thirukanitham",
      region: "TN",
      includePanchangam: true,
    });
    expect(drik.thiruvalluvar_year).toBeGreaterThan(2050);
    expect(drik.formatted_formal).toContain("திருவள்ளுவர் ஆண்டு");
    expect(drik.formatted_short.length).toBeGreaterThan(0);

    const vakya = buildTamilDateStamp(2026, 4, 14, {
      profile: "vakya",
      region: "TN",
      includePanchangam: false,
    });
    expect(vakya.profile_label).toContain("Vakya");
  });

  it("hyphenates Tamil words canonically and idempotently via Rust tamil-hyphen", () => {
    const longWord = "பல்கலைக்கழகங்களில்";
    const first = hyphenateText(longWord, { delimiter: "\u00AD", leftMin: 3, rightMin: 3 });
    expect(first).toContain("\u00AD");
    // Idempotent second pass
    const second = hyphenateText(first, { delimiter: "\u00AD", leftMin: 3, rightMin: 3 });
    expect(second).toBe(first);
    expect(removeHyphens(first)).toBe(longWord);

    // Short word (< 6 letters) never breaks
    expect(hyphenateText("உலகம்", { delimiter: "\u00AD", leftMin: 3, rightMin: 3 })).toBe("உலகம்");
  });

  it("inspects true Tamil graphemes, syllables, and invisible scalars", () => {
    const report = inspectDocumentText("தமிழ்\u00ADமொழி\u200B 2026");
    expect(report.word_count).toBe(2);
    expect(report.letter_count).toBe(5);
    expect(report.syllable_count).toBeGreaterThan(0);
    expect(report.soft_hyphen_count).toBe(1);
    expect(report.zero_width_count).toBe(1);
    expect(report.is_nfc).toBe(true);
  });

  it("supports Phase 6 diaspora currencies, wordsToNumber (ITN), and mixedFractionToWords", () => {
    const sgd = numberToTamilWords("1250.50", "currency", { locale: "TN", currency: "SGD" });
    expect(sgd).toContain("சிங்கப்பூர் டாலர்");

    const usd = numberToTamilWords("100", "currency", { locale: "TN", currency: "USD" });
    expect(usd).toContain("டாலர்");

    expect(wordsToNumber("நூற்று இருபத்து மூன்று", "TN")).toBe(123);
    expect(mixedFractionToWords({ whole: 1, numerator: 1, denominator: 2 }, "TN")).toBe("ஒன்றரை");
  });

  it("supports Phase 7B CID fonts (Senthamil, Shree-Tam, Softview, TBO) and Bharathi Braille", () => {
    const word = "தமிழ்";
    for (const enc of ["senthamil", "shree_tam", "softview", "tbo", "braille"] as const) {
      const encoded = convertUnicodeToLegacy(word, enc);
      expect(encoded.length).toBeGreaterThan(0);
      expect(convertLegacyToUnicode(encoded, enc).text).toBe(word);
    }
  });

  it("supports Phase 8 transliteration and Tamil99 / Anjal / Suratha Bamini schemes", () => {
    const schemes = getTransliterationSchemes();
    expect(schemes).toHaveLength(8);
    expect(schemes.map((s) => s.id)).toContain("tamil99");
    expect(transliterateText("தமிழ்", "iso-15919", "to_latin")).toBe("tamiḻ");
    expect(transliterateText("tamiḻ", "iso-15919", "to_tamil")).toBe("தமிழ்");
    expect(transliterateText("thamizh", "anjal-phonetic", "to_tamil")).toBe("தமிழ்");
    expect(transliterateText("se", "anjal-phonetic", "to_tamil")).toBe("செ");
    expect(transliterateText("Se", "anjal-phonetic", "to_tamil")).toBe("ஸெ");
    expect(transliterateText("se", "phonetic-v1", "to_tamil")).toBe("செ");
    expect(transliterateText("Se", "phonetic-v1", "to_tamil")).toBe("ஸெ");
    expect(transliterateText("jkpo;", "suratha-bamini", "to_tamil")).toBe("தமிழ்");

    expect(transliterateSuggestText("vanakkam", "phonetic-v1")).toEqual(["வனக்கம்", "வணக்கம்"]);
    expect(transliterateSuggestText("malai", "phonetic-v1")).toEqual(["மலை", "மழை", "மளை"]);
    expect(transliterateSuggestText("karai", "phonetic-v1")).toEqual(["கரை", "கறை"]);
    expect(transliterateSuggestText("palli", "phonetic-v1")).toEqual(["பல்லி", "பள்ளி"]);
    expect(transliterateSuggestText("thamil", "phonetic-v1")).toEqual(["தமில்", "தமிள்", "தமிழ்"]);
  });
});

describe("OOXML Formatting Preservation", () => {
  it("preserves bold/italic run formatting while injecting <w:softHyphen/>", () => {
    const sampleXml =
      '<w:p><w:r><w:rPr><w:b/><w:i/></w:rPr><w:t>பல்கலைக்கழகங்களில் &amp; தமிழ்</w:t></w:r></w:p>';
    const hyphenated = hyphenateOoxml(
      sampleXml,
      (txt, delim) => hyphenateText(txt, { delimiter: delim, leftMin: 3, rightMin: 3 }),
      true
    );
    expect(hyphenated).toContain("<w:b/><w:i/>");
    expect(hyphenated).toContain("<w:softHyphen/>");
    expect(hyphenated).toContain("&amp;");

    const cleaned = removeOoxmlHyphens(hyphenated);
    expect(cleaned).not.toContain("<w:softHyphen/>");
    expect(cleaned).toContain("<w:b/><w:i/>");

    // Manual hyphens (-) must NEVER be removed by removeOoxmlHyphens
    const withManualHyphen =
      '<w:p><w:r><w:t>தமிழ்-ஆங்கிலம்</w:t><w:softHyphen/><w:t>பல்கலை</w:t></w:r></w:p>';
    const cleanedManual = removeOoxmlHyphens(withManualHyphen);
    expect(cleanedManual).toContain("தமிழ்-ஆங்கிலம்");
    expect(cleanedManual).not.toContain("<w:softHyphen/>");

    // Smart toggle: 1st click applies soft-hyphen, 2nd click removes it, switching to wrap replaces it
    const fn = (txt: string, delim: string) => hyphenateText(txt, { delimiter: delim, leftMin: 3, rightMin: 3 });
    const t1 = toggleHyphenateOoxml(sampleXml, fn, true);
    expect(t1.action).toBe("applied");
    expect(t1.xml).toContain("<w:softHyphen/>");

    const t2 = toggleHyphenateOoxml(t1.xml, fn, true);
    expect(t2.action).toBe("removed");
    expect(t2.xml).not.toContain("<w:softHyphen/>");

    // Switching from soft-hyphen -> wrap without hyphen cleanly swaps modes
    const tSwitch = toggleHyphenateOoxml(t1.xml, fn, false);
    expect(tSwitch.action).toBe("applied");
    expect(tSwitch.xml).not.toContain("<w:softHyphen/>");
    expect(tSwitch.xml).toContain("\u200B");

    // 2nd click on wrap without hyphen removes it
    const tWrapOff = toggleHyphenateOoxml(tSwitch.xml, fn, false);
    expect(tWrapOff.action).toBe("removed");
    expect(tWrapOff.xml).not.toContain("\u200B");

    // Word-normalized multi-<w:r> OOXML with <w:proofErr/> & 4 fragments (how Desktop Word stores <w:softHyphen/>):
    const wordNormalizedXml =
      '<w:p>' +
      '<w:proofErr w:type="spellStart"/>' +
      '<w:r w:rsidR="001"><w:rPr><w:b/></w:rPr><w:t>பல்</w:t></w:r>' +
      '<w:r w:rsidR="002"><w:rPr><w:b/></w:rPr><w:softHyphen/></w:r>' +
      '<w:r w:rsidR="003"><w:rPr><w:b/></w:rPr><w:t>கலைக்</w:t></w:r>' +
      '<w:proofErr w:type="spellEnd"/>' +
      '<w:r w:rsidR="004"><w:rPr><w:b/></w:rPr><w:softHyphen/></w:r>' +
      '<w:r w:rsidR="005"><w:rPr><w:b/></w:rPr><w:t>கழகங்</w:t></w:r>' +
      '<w:r w:rsidR="006"><w:rPr><w:b/></w:rPr><w:softHyphen/></w:r>' +
      '<w:r w:rsidR="007"><w:rPr><w:b/></w:rPr><w:t>களில்</w:t></w:r>' +
      '</w:p>';
    // Clicking Hyphenate a 2nd time MUST keep <w:softHyphen/> and recombine all 4 fragments
    const cleanedWord = removeOoxmlHyphens(wordNormalizedXml);
    expect(cleanedWord).toContain("<w:t>பல்கலைக்கழகங்களில்</w:t>");
    const reHyphenated = hyphenateOoxml(wordNormalizedXml, fn, true);
    expect(reHyphenated).toContain("<w:softHyphen/>");
    expect(reHyphenated).toContain("<w:b/>");
    // Switching from Word-normalized soft-hyphen -> Wrap Without Hyphen MUST inject \u200B
    const switchedToWrap = hyphenateOoxml(wordNormalizedXml, fn, false);
    expect(switchedToWrap).not.toContain("<w:softHyphen/>");
    expect(switchedToWrap).toContain("\u200B");
    expect(switchedToWrap).toContain("<w:b/>");
  });

  it("updates legacy font family ONLY on converted Tamil runs, preserving English run fonts", () => {
    const xml =
      '<w:p>' +
      '<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr><w:t>Hello </w:t></w:r>' +
      '<w:r><w:rPr><w:rFonts w:ascii="Bamini" w:hAnsi="Bamini"/><w:b/></w:rPr><w:t>jkpo;</w:t></w:r>' +
      '</w:p>';
    const { xml: out, runsChanged } = transformOoxmlRunsWithFont(
      xml,
      (t) => (t.includes("jkpo;") ? convertLegacyToUnicode(t, "bamini").text : t),
      "Nirmala UI"
    );
    expect(runsChanged).toBe(1);
    expect(out).toContain('w:ascii="Calibri"');
    expect(out).toContain("Hello ");
    expect(out).toContain("தமிழ்");
    expect(out).toContain('w:cs="Nirmala UI"');
    expect(out).toContain("<w:b/>");

    // Also verify legacy helper still works
    expect(applyOoxmlUnicodeFont(transformOoxmlTextNodes(xml, (t) => t), "Latha")).toContain('w:cs="Latha"');
  });
});

describe("Microsoft AppSource Production Manifest Validation", () => {
  const prodUrl = "https://tamil-toolkit-word.vercel.app";
  const xml = renderManifestXml(prodUrl);

  it("contains zero localhost URLs and uses HTTPS everywhere", () => {
    expect(xml).not.toContain("localhost");
    expect(xml).not.toContain('DefaultValue="http://');
    expect(xml).toContain(`<SupportUrl DefaultValue="${prodUrl}/support.html" />`);
    expect(xml).toContain(`<SourceLocation DefaultValue="${prodUrl}/index.html" />`);
    expect(xml).toContain('<Set Name="WordApi" MinVersion="1.3" />');
    expect(xml).toContain("<Permissions>ReadWriteDocument</Permissions>");
  });

  it("satisfies AppSource ShortStrings (<=32 chars) and LongStrings (<=250 chars) limits", () => {
    const shortBlock = xml.match(/<bt:ShortStrings>([\s\S]*?)<\/bt:ShortStrings>/)?.[1] || "";
    const shortMatches = [...shortBlock.matchAll(/DefaultValue="([^"]+)"/g)];
    expect(shortMatches.length).toBeGreaterThan(5);
    for (const [, val] of shortMatches) {
      expect(val.length, `ShortString too long: ${val}`).toBeLessThanOrEqual(32);
    }

    const longBlock = xml.match(/<bt:LongStrings>([\s\S]*?)<\/bt:LongStrings>/)?.[1] || "";
    const longMatches = [...longBlock.matchAll(/DefaultValue="([^"]+)"/g)];
    expect(longMatches.length).toBeGreaterThan(5);
    for (const [, val] of longMatches) {
      expect(val.length, `LongString too long: ${val}`).toBeLessThanOrEqual(250);
    }
  });

  it("resolves every referenced icon asset to an existing file in public/assets/", () => {
    const iconUrls = [...xml.matchAll(/DefaultValue="https:\/\/[^"]+\/assets\/([^"?]+)/g)].map(
      (m) => m[1]
    );
    expect(iconUrls.length).toBeGreaterThan(0);
    for (const file of iconUrls) {
      const fullPath = path.join(addinDir, "public", "assets", file);
      expect(fs.existsSync(fullPath), `Missing icon asset: ${fullPath}`).toBe(true);
    }
  });
});
