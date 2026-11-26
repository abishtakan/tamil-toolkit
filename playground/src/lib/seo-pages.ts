export const PLAYGROUND_ORIGIN = "https://tamil-toolkit-playground.vercel.app";

export interface SeoToolPage {
  slug: string;
  toolId:
    | "codec"
    | "numeral"
    | "translit"
    | "sorter"
    | "hyphenator"
    | "calendar"
    | "tokenizer"
    | "punarchi";
  defaultCodecProfile?: string;
  title: string;
  description: string;
  h1: string;
  summary: string;
  example: string;
  limits: string;
}

export const SEO_TOOL_PAGES: readonly SeoToolPage[] = [
  {
    slug: "bamini-to-unicode",
    toolId: "codec",
    title: "Bamini, TSCII & Legacy Tamil Font to Unicode Converter | Tamil Toolkit",
    description:
      "Convert Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM, Senthamil, Shree-Tam, Softview, and TBO text or legacy PDF text layers to Tamil Unicode locally in your browser.",
    h1: "Bamini, TSCII & Legacy Tamil Font to Unicode Converter",
    summary:
      "Bidirectional conversion between legacy Tamil encodings (Bamini, TSCII 1.7, TAB, TAM, Anjal, Vanavil Avvaiyar, LT-TM, Senthamil, Shree-Tam, Softview, TBO) and NFC Tamil Unicode, plus client-side PDF text-layer import.",
    example: "Bamini: jkpo; nkhop → Unicode: தமிழ் மொழி",
    limits:
      "Uses bounded declarative mapping tables; PDF import extracts selectable text layers locally and does not perform OCR on scanned images.",
  },
  {
    slug: "tamil-number-to-words",
    toolId: "numeral",
    title: "Tamil Number to Words & Cheque Formatter (INR, LKR, SGD, USD) | Tamil Toolkit",
    description:
      "Convert numbers and cheque amounts to formal Tamil Nadu (TN) and Sri Lanka (SL) Tamil words across INR, LKR, SGD, MYR, USD, EUR, GBP, and CAD, plus words-to-number (ITN) and mixed fractions.",
    h1: "Tamil Number to Words & Cheque Amount Formatter",
    summary:
      "Exact decimal currency spellout for INR, LKR, SGD, MYR, USD, EUR, GBP, and CAD in Tamil Nadu (ta-IN) and Sri Lanka (ta-LK) dialects, colloquial mixed fractions (ஒன்றரை, ஒன்றேகால்), formal ITN words-to-number, and traditional Tamil numerals (௰, ௱, ௲).",
    example: "125000 (INR, TN) → ஒரு லட்சத்து இருபத்து ஐந்து ஆயிரம் ரூபாய் மட்டும்",
    limits:
      "Formal spellout and ITN cover bounded integers from -999,999,999 to 999,999,999 using CLDR 49 Tamil RBNF rules.",
  },
  {
    slug: "tamil99-keyboard",
    toolId: "translit",
    title: "Tamil99 Online Keyboard & Tamil Transliteration (ISO 15919, Tanglish) | Tamil Toolkit",
    description:
      "Type Tamil online with Tamil99, Anjal Phonetic, Suratha Bamini, and Tanglish, or transliterate bidirectionally using ISO 15919, Madras Lexicon, ITRANS, and Harvard-Kyoto.",
    h1: "Tamil99 Online Keyboard & Tamil Transliteration",
    summary:
      "Deterministic offline transliteration and keyboard input covering ISO 15919, Madras Lexicon, ITRANS, Harvard-Kyoto, Phonetic (Tanglish), Tamil99 (with auto-pulli gemination and homorganic nasal+stop rules), Anjal Phonetic, and Suratha Bamini.",
    example: "Tamil99: lks/f → தமிழ் · ISO 15919: tamiḻ moḻi ↔ தமிழ் மொழி",
    limits:
      "Tamil99, Anjal Phonetic, and Suratha Bamini are one-way input profiles (keystrokes to Tamil Unicode); scholarly and phonetic-v1 schemes are bidirectional.",
  },
  {
    slug: "agara-varisai-sorter",
    toolId: "sorter",
    title: "Agara Varisai Tamil Alphabetical Sorter (அகர வரிசை) | Tamil Toolkit",
    description:
      "Sort Tamil words and lists in authentic Mei-first Agara Varisai or school Uyirmei-first alphabetical order locally in your browser via Rust/WebAssembly.",
    h1: "Agara Varisai Tamil Alphabetical Sorter (அகர வரிசை)",
    summary:
      "Lexicographical Tamil collation following traditional Mei-first Agara Varisai (agara-v1) and school Uyirmei-first (uyirmei-first-v1) order, with pairwise comparison and canonical sort/search keys.",
    example: "கடல், அம்மா, ஆடு, இலை → அம்மா, ஆடு, இலை, கடல்",
    limits:
      "Deterministic collation profiles defined in lexicon/collate.toml and lexicon/collate_uyirmei_first.toml.",
  },
  {
    slug: "tamil-braille-converter",
    toolId: "codec",
    defaultCodecProfile: "bharathi-tamil-g1-v1",
    title: "Tamil Braille Converter (Bharathi Grade 1, U+2800..U+28FF) | Tamil Toolkit",
    description:
      "Convert Tamil Unicode text to and from Bharathi Tamil Braille Grade 1 Unicode Braille patterns (U+2800..U+28FF) locally in your browser.",
    h1: "Bharathi Tamil Braille Grade 1 Converter",
    summary:
      "Bidirectional Unicode Tamil to Bharathi Tamil Braille Grade 1 conversion using Unicode Braille Patterns (U+2800..U+28FF) with strict or preserve error handling.",
    example: "Unicode: தமிழ் ↔ Bharathi Braille Grade 1 (U+2800..U+28FF)",
    limits:
      "Covers Bharathi Tamil Braille Grade 1 uncontracted letters, vowel signs, numerals, and punctuation as documented in docs/specs/codec-braille.md.",
  },
  {
    slug: "tamil-hyphenation",
    toolId: "hyphenator",
    title: "Tamil Syllabic Hyphenator & Soft-Hyphen Tool (Word, LibreOffice, InDesign) | Tamil Toolkit",
    description:
      "Split Tamil words into syllables and insert coda-binding soft hyphens without breaking pure consonants (ஒற்று). Includes LibreOffice .oxt and Hunspell .dic downloads.",
    h1: "Tamil Syllabic Hyphenator & Line Wrapper",
    summary:
      "Coda-binding Tamil syllabic hyphenation that keeps pulli consonants (ஒற்று) attached to the preceding syllable, with copyable soft hyphens, column-wrap preview, Hunspell .dic, and LibreOffice .oxt downloads.",
    example: "பல்கலைக்கழகங்களில் → பல்·க·லைக்·க·ழ·கங்·க·ளில்",
    limits:
      "Default left/right margins are 3 Tamil letters; words shorter than leftMin + rightMin are not hyphenated.",
  },
  {
    slug: "tamil-panchangam",
    toolId: "calendar",
    title: "Tamil Calendar & Panchangam Explorer (Thirukanitham & Vakya) | Tamil Toolkit",
    description:
      "Check Tamil solar dates, Thiruvalluvar year, 60-year Jovian cycle, Tithi, Nakshatra, Yoga, Karana, Rahu Kalam, and Tamil Nadu / Sri Lanka holidays locally in your browser.",
    h1: "Tamil Solar Calendar & Panchangam Explorer",
    summary:
      "Bounded Thirukanitham (Drik) and 1962 Vakya Civil solar-lunar calendar conversion, five Panchangam limbs, daylight timings (Rahu Kalam, Yamagandam, Kuligai), and TN/SL official holiday snapshots.",
    example: "Gregorian 2026-04-14 → சித்திரை 1 (Tamil New Year / Puthandu)",
    limits:
      "Calendar profiles cover documented bounded date and TN/SL location ranges; see docs/specs/calendar-thirukanitham-v1.md and calendar-vakya-civil-v1.md.",
  },
  {
    slug: "tamil-tokenizer",
    toolId: "tokenizer",
    title: "Tamil Word & Sentence Tokenizer (Source Offsets & Stopwords) | Tamil Toolkit",
    description:
      "Tokenize Tamil text into words and sentences with exact UTF-8 byte and written-unit offsets, attested Tamil abbreviation handling (திரு., மு.க., பி.ப., ரூ.), and opt-in stopword filtering.",
    h1: "Tamil Word & Sentence Tokenizer",
    summary:
      "Offline, source-preserving UAX #29 tailored Tamil word and sentence segmentation keeping written units and attested TN/SL abbreviations intact, with none, conservative, and broad stopword profiles.",
    example: "திரு. குமார் வந்தார். → 1 sentence; [திரு., குமார், வந்தார், .]",
    limits:
      "Provides linguistic source spans and opt-in stopword filtering; model-specific subword token IDs and chunk budgeting are separate layers.",
  },
  {
    slug: "tamil-punarchi",
    toolId: "punarchi",
    title: "Tamil Punarchi (Sandhi) Engine — Complete 117-Sutra Nannool Workbench | Tamil Toolkit",
    description:
      "Join and split Tamil words with full Nannool Ezhuttatikaram 117-sutra derivation traces, two-level Vetrumai/Alvazhi context, multi-segment Chariyai folding, and interactive sutra explorer.",
    h1: "Tamil Punarchi (Sandhi) Workbench — Nannool Ezhuttatikaram",
    summary:
      "Offline deterministic Tamil Sandhi engine implementing all 117 Nannool Ezhuttatikaram sutras (93–94, 102–108, 136, 151–257) with step-by-step rule traces, dictionary-free forward-verified split candidates, and interactive sutra logic review.",
    example: "மரம் + ஐ (Vetrumai) → மரத்தை · செம்மை + தாமரை → செந்தாமரை",
    limits:
      "Pure morphophonemic engine (dictionary-free reverse split candidates up to 256 UTF-8 bytes); dictionary-backed lexical ranking belongs to Phase 11.",
  },
];

export function findSeoPageByPath(pathname: string): SeoToolPage | null {
  const clean = pathname.replace(/\/+$/, "");
  const match = clean.match(/^\/tools\/([a-z0-9-]+)$/);
  if (!match) return null;
  return SEO_TOOL_PAGES.find((p) => p.slug === match[1]) ?? null;
}

export function findPrimarySeoPageByToolId(toolId: string): SeoToolPage | null {
  return SEO_TOOL_PAGES.find((p) => p.toolId === toolId && !p.defaultCodecProfile) ?? null;
}
