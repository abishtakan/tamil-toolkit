import { createApi, type Request } from "../bindings/js-wasm/src/api.ts";
import init, { execute as nativeExecute } from "../bindings/js-wasm/pkg-web/tamil_toolkit.js";
import wasmUrl from "../bindings/js-wasm/pkg-web/tamil_toolkit_bg.wasm?url";
import manifestJson from "../tests/golden/manifest.json";
import "./style.css";

type Outcome = { id: string; op: string; input: unknown; expected?: unknown; expected_error?: string };
type Suite = { file: string; status: "active" | "planned"; operations: string[]; reason?: string };
type PackageState = "active" | "facade" | "dispatcher" | "wasm" | "native" | "planned";
type PackageInfo = {
  id: string;
  description: string;
  state: PackageState;
  suiteFiles?: string[];
  operations?: string[];
  plannedSuite?: string;
};
type FieldSpec = {
  key: string;
  label: string;
  kind: "text" | "textarea" | "number" | "select";
  initial: string;
  inputMode?: "decimal" | "numeric";
  required?: boolean;
  options?: string[];
  help?: string;
};
type QuickExample = { label: string; values: Record<string, string> };
type OperationSpec = {
  op: string;
  label: string;
  description: string;
  fields: FieldSpec[];
  build: (values: Record<string, string>) => Request;
  examples?: QuickExample[];
};
type CaseResult = { row: Outcome; passed: boolean; actual: unknown; error?: string };
type Runtime = "wasm" | "python" | "dart" | "unavailable";

const manifest = manifestJson as { suites: Suite[] };
const fixtureLoaders = import.meta.glob("../tests/golden/*.jsonl", {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;
const suites = new Map(manifest.suites.map((suite) => [suite.file, suite]));
const activeSuites = manifest.suites.filter((suite) => suite.status === "active");
const rowsCache = new Map<string, Promise<Outcome[]>>();

function loadSuiteRows(file: string): Promise<Outcome[]> {
  const cached = rowsCache.get(file);
  if (cached) return cached;
  const load = fixtureLoaders[`../tests/golden/${file}`];
  if (!load) return Promise.reject(new Error(`Golden fixture is missing from the app bundle: ${file}`));
  const result = load().then((fixture) => fixture.trim()
    ? fixture.trim().split(/\r?\n/).map((line) => JSON.parse(line) as Outcome)
    : []);
  rowsCache.set(file, result);
  return result;
}

const packages: PackageInfo[] = [
  { id: "tamil-core", state: "active", description: "Unicode primitives, letter boundaries, and scalar inspection.", suiteFiles: ["core_graphemes.jsonl", "core_alphabet.jsonl", "core_normalization.jsonl", "core_boundaries.jsonl", "core_errors.jsonl"] },
  { id: "tamil-norm", state: "facade", description: "NFC/NFD normalization facade re-exported from tamil-core.", suiteFiles: ["core_normalization.jsonl"], operations: ["normalize_nfc", "normalize_nfd"] },
  { id: "tamil-collate", state: "active", description: "Agara Varisai comparison, ordering, and canonical search keys.", suiteFiles: ["collate_agara_varisai.jsonl"] },
  { id: "tamil-numerals", state: "active", description: "TN/SL number words, currencies, exact fractions, and Gregorian dates.", suiteFiles: ["numerals_lkr_inr.jsonl", "numerals_fractions_dates.jsonl"] },
  { id: "tamil-codec", state: "active", description: "Bamini and bounded legacy byte and CID conversion.", suiteFiles: ["codec_bamini.jsonl", "codec_unicode_to_bamini.jsonl", "codec_tscii_bytes.jsonl", "codec_tscii_iana.jsonl", "codec_unicode_to_tscii.jsonl", "codec_tscii_iana_audit.jsonl", "codec_tab.jsonl", "codec_tab_utn.jsonl", "codec_tam.jsonl", "codec_tam_utn.jsonl", "codec_anjal.jsonl", "codec_lt_tm.jsonl", "codec_vanavil.jsonl"] },
  { id: "tamil-toolkit", state: "dispatcher", description: "Shared Rust dispatcher used by bindings and the local oracle." },
  { id: "tamil-wasm", state: "wasm", description: "Browser WASM binding calling the shared Rust dispatcher." },
  { id: "tamil-python", state: "native", description: "PyO3 adapter, run directly in the Python runtime." },
  { id: "tamil-dart", state: "native", description: "Dart FFI adapter, run directly against the host shared library." },
  { id: "tamil-punarchi", state: "planned", description: "Sourced Nannool rules and licensed lexicon are not implemented yet.", plannedSuite: "punarchi_nannool.jsonl" },
  { id: "tamil-dialect", state: "planned", description: "Dialect normalization is planned; no runtime operation is available." },
  { id: "tamil-hyphen", state: "planned", description: "Hyphenation is planned; no runtime operation is available." },
  { id: "tamil-morph", state: "planned", description: "Morphology is planned; no runtime operation is available." },
  { id: "tamil-yaappu", state: "planned", description: "Prosody analysis is planned; no runtime operation is available." },
  { id: "pg_tamil", state: "planned", description: "Isolated PostgreSQL scaffold with no SQL behavior or regression suite." },
];

const demoTamil = "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd";
const maxCurrencyMinorUnits = 99_999_999_999n;

function parseHexBytes(value: string): number[] {
  const text = value.trim();
  if (!text) return [];
  return text.split(/\s+/).map((part) => {
    if (!/^(?:0x)?[0-9a-f]{2}$/i.test(part)) throw new Error("Enter bytes as two-digit hex values separated by spaces, for example BA A2 C5 FD.");
    return Number.parseInt(part.replace(/^0x/i, ""), 16);
  });
}

function parseCurrencyAmount(value: string): number {
  const match = /^([+-]?)(\d*)(?:\.(\d{0,2}))?$/.exec(value.trim());
  if (!match || (!match[2] && !match[3])) {
    throw new Error("Enter an amount with digits and an optional decimal point (up to 2 decimal places). Example: 1025.50");
  }

  const whole = (match[2] || "0").replace(/^0+(?=\d)/, "");
  if (whole.length > 9) {
    throw new Error("Amount is outside the supported range: -999,999,999.99 to 999,999,999.99.");
  }

  let minorUnits = BigInt(whole) * 100n + BigInt((match[3] || "").padEnd(2, "0") || "0");
  if (match[1] === "-") minorUnits = -minorUnits;
  if (minorUnits > maxCurrencyMinorUnits || minorUnits < -maxCurrencyMinorUnits) {
    throw new Error("Amount is outside the supported range: -999,999,999.99 to 999,999,999.99.");
  }
  return Number(minorUnits);
}

const operations: OperationSpec[] = [
  {
    op: "get_letters", label: "Get letters", description: "Split text into normalized Tamil letters and preserved non-Tamil graphemes.",
    fields: [{ key: "text", label: "Text", kind: "textarea", initial: demoTamil, help: "Paste Tamil or mixed-script text." }],
    build: (v) => ({ op: "get_letters", input: v.text }),
  },
  {
    op: "normalize_nfc", label: "Normalize NFC", description: "Apply canonical NFC normalization while preserving joiners and other scalars.",
    fields: [{ key: "text", label: "Text to normalize", kind: "textarea", initial: "\u0b95\u0bc6" }],
    build: (v) => ({ op: "normalize_nfc", input: v.text }),
  },
  {
    op: "normalize_nfd", label: "Normalize NFD", description: "Apply canonical NFD normalization.",
    fields: [{ key: "text", label: "Text to normalize", kind: "textarea", initial: "\u0b95\u0bca" }],
    build: (v) => ({ op: "normalize_nfd", input: v.text }),
  },
  {
    op: "split_uyirmei", label: "Split Uyirmei", description: "Split one valid consonant-vowel letter into mei and uyir.",
    fields: [{ key: "text", label: "One Tamil letter", kind: "text", initial: "\u0b95\u0bbe" }],
    build: (v) => ({ op: "split_uyirmei", input: v.text }),
  },
  {
    op: "compose_uyirmei", label: "Compose Uyirmei", description: "Compose a valid mei and independent uyir into NFC Tamil.",
    fields: [
      { key: "mei", label: "Mei", kind: "text", initial: "\u0b95\u0bcd" },
      { key: "uyir", label: "Uyir", kind: "text", initial: "\u0b85" },
    ],
    build: (v) => ({ op: "compose_uyirmei", input: { mei: v.mei, uyir: v.uyir } }),
  },
  {
    op: "inspect_tamil_string", label: "Inspect Tamil scalars", description: "Inspect normalization, letter counts, grapheme counts, and phonetic classes.",
    fields: [{ key: "text", label: "Text to inspect", kind: "textarea", initial: demoTamil }],
    build: (v) => ({ op: "inspect_tamil_string", input: v.text }),
  },
  {
    op: "compare", label: "Compare two strings", description: "Compare two strings using the toolkit's Agara ordering profile.",
    fields: [
      { key: "left", label: "Left value", kind: "text", initial: "\u0b95\u0bcd" },
      { key: "right", label: "Right value", kind: "text", initial: "\u0b95" },
    ],
    build: (v) => ({ op: "compare", input: { left: v.left, right: v.right } }),
  },
  {
    op: "sort_words", label: "Sort words", description: "Sort one input word per line and preserve duplicates and original spellings.",
    fields: [{ key: "words", label: "Words (one per line)", kind: "textarea", initial: "\u0bae\u0bb0\u0bae\u0bcd\n\u0b85\u0bae\u0bcd\n\u0b95\u0bb2\u0bcd" }],
    build: (v) => ({ op: "sort_words", input: v.words.split(/\r?\n/).filter((word) => word.length > 0) }),
  },
  {
    op: "sort_key", label: "Build sort key", description: "Return the versioned numeric key used for Agara ordering.",
    fields: [{ key: "text", label: "Text", kind: "textarea", initial: demoTamil }],
    build: (v) => ({ op: "sort_key", input: v.text }),
  },
  {
    op: "search_key", label: "Build search key", description: "Return a canonical exact-match search key.",
    fields: [{ key: "text", label: "Text", kind: "textarea", initial: demoTamil }],
    build: (v) => ({ op: "search_key", input: v.text }),
  },
  {
    op: "to_words", label: "Number to words", description: "Spell a supported signed integer using the selected regional profile.",
    fields: [
      { key: "value", label: "Integer", kind: "number", initial: "1025", help: "Signed whole number from -999,999,999 to 999,999,999." },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "to_words", input: { value: Number(v.value), locale: v.locale } }),
    examples: [
      { label: "Zero Â· TN", values: { value: "0", locale: "TN" } },
      { label: "Negative Â· SL", values: { value: "-12345", locale: "SL" } },
      { label: "Maximum supported", values: { value: "999999999", locale: "TN" } },
      { label: "Above maximum Â· error", values: { value: "1000000000", locale: "TN" } },
    ],
  },
  {
    op: "format_currency", label: "Format currency", description: "Format an exact amount entered in rupees, with up to two decimal places.",
    fields: [
      { key: "amount", label: "Amount", kind: "text", inputMode: "decimal", required: true, initial: "1025.50", help: "Type the amount normally, e.g. 1025.50. Use a dot and up to 2 decimal places; no grouping commas." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "format_currency", input: { amount_minor: parseCurrencyAmount(v.amount), currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR Â· 1,025.50 Â· SL", values: { amount: "1025.50", currency: "LKR", locale: "SL" } },
      { label: "INR Â· 0.99 Â· TN", values: { amount: "0.99", currency: "INR", locale: "TN" } },
      { label: "Negative amount", values: { amount: "-1.05", currency: "LKR", locale: "TN" } },
      { label: "Above maximum Â· error", values: { amount: "1000000000.00", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "currency_to_words", label: "Currency to words", description: "Spell an exact amount entered in rupees, with up to two decimal places.",
    fields: [
      { key: "amount", label: "Amount", kind: "text", inputMode: "decimal", required: true, initial: "1025.50", help: "Type the amount normally, e.g. 1025.50. Use a dot and up to 2 decimal places; no grouping commas." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "currency_to_words", input: { amount_minor: parseCurrencyAmount(v.amount), currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR Â· 1,025.50 Â· SL", values: { amount: "1025.50", currency: "LKR", locale: "SL" } },
      { label: "INR Â· 0.99 Â· TN", values: { amount: "0.99", currency: "INR", locale: "TN" } },
      { label: "Negative amount", values: { amount: "-1.05", currency: "LKR", locale: "TN" } },
      { label: "Above maximum Â· error", values: { amount: "1000000000.00", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "format_fraction", label: "Format fraction", description: "Reduce an exact fraction and render its digits.",
    fields: [
      { key: "numerator", label: "Numerator", kind: "number", initial: "2", help: "Signed whole number; magnitude up to 999,999,999." },
      { key: "denominator", label: "Denominator", kind: "number", initial: "4", help: "Must not be zero; a negative sign is allowed." },
      { key: "digits", label: "Digits", kind: "select", initial: "tamil", options: ["latin", "tamil"], help: "Tamil selects positional Tamil digits (à¯¦â€“à¯¯)." },
    ],
    build: (v) => ({ op: "format_fraction", input: { numerator: Number(v.numerator), denominator: Number(v.denominator), digits: v.digits } }),
    examples: [
      { label: "Reduce 2/4 Â· Tamil digits", values: { numerator: "2", denominator: "4", digits: "tamil" } },
      { label: "Negative Â· Latin digits", values: { numerator: "-7", denominator: "12", digits: "latin" } },
      { label: "Integral result", values: { numerator: "6", denominator: "3", digits: "latin" } },
      { label: "Zero denominator Â· error", values: { numerator: "1", denominator: "0", digits: "latin" } },
    ],
  },
  {
    op: "fraction_to_words", label: "Fraction to words", description: "Use common fraction names or an exact division expression.",
    fields: [
      { key: "numerator", label: "Numerator", kind: "number", initial: "3" },
      { key: "denominator", label: "Denominator", kind: "number", initial: "4" },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "fraction_to_words", input: { numerator: Number(v.numerator), denominator: Number(v.denominator), locale: v.locale } }),
    examples: [
      { label: "Quarter", values: { numerator: "1", denominator: "4", locale: "TN" } },
      { label: "Half", values: { numerator: "1", denominator: "2", locale: "TN" } },
      { label: "Three quarters Â· SL", values: { numerator: "3", denominator: "4", locale: "SL" } },
      { label: "General fraction", values: { numerator: "5", denominator: "8", locale: "TN" } },
      { label: "Negative fraction", values: { numerator: "-3", denominator: "4", locale: "TN" } },
    ],
  },
  {
    op: "fraction_symbol", label: "Fraction symbol", description: "Return a traditional Unicode fraction symbol when one exists.",
    fields: [
      { key: "numerator", label: "Numerator", kind: "number", initial: "1" },
      { key: "denominator", label: "Denominator", kind: "number", initial: "2" },
    ],
    build: (v) => ({ op: "fraction_symbol", input: { numerator: Number(v.numerator), denominator: Number(v.denominator) } }),
    examples: [
      { label: "One half", values: { numerator: "1", denominator: "2" } },
      { label: "Equivalent input 2/4", values: { numerator: "2", denominator: "4" } },
      { label: "Negative quarter", values: { numerator: "-1", denominator: "4" } },
      { label: "No symbol Â· error", values: { numerator: "5", denominator: "7" } },
    ],
  },
  {
    op: "format_date", label: "Format Gregorian date", description: "Format a Gregorian civil date in Tamil, for years 1 through 9999.",
    fields: [
      { key: "year", label: "Year", kind: "number", initial: "2024", help: "Gregorian years 1â€“9999 (proleptic calendar)." },
      { key: "month", label: "Month", kind: "number", initial: "2" },
      { key: "day", label: "Day", kind: "number", initial: "29" },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
      { key: "style", label: "Style", kind: "select", initial: "full", options: ["short", "medium", "long", "full"] },
      { key: "digits", label: "Digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
    ],
    build: (v) => ({ op: "format_date", input: { year: Number(v.year), month: Number(v.month), day: Number(v.day), locale: v.locale, style: v.style, digits: v.digits } }),
    examples: [
      { label: "Leap day Â· full", values: { year: "2024", month: "2", day: "29", locale: "TN", style: "full", digits: "latin" } },
      { label: "Century non-leap Â· error", values: { year: "1900", month: "2", day: "29", locale: "TN", style: "full", digits: "latin" } },
      { label: "Tamil digits Â· short", values: { year: "2024", month: "3", day: "20", locale: "TN", style: "short", digits: "tamil" } },
      { label: "Weekday Â· full Â· SL", values: { year: "2026", month: "10", day: "31", locale: "SL", style: "full", digits: "latin" } },
      { label: "Year 1 Â· short", values: { year: "1", month: "1", day: "1", locale: "TN", style: "short", digits: "latin" } },
      { label: "Year 9999 Â· long", values: { year: "9999", month: "12", day: "31", locale: "TN", style: "long", digits: "tamil" } },
    ],
  },
  {
    op: "bamini_to_unicode", label: "Bamini to Unicode", description: "Decode a selected Bamini text run with the bamini-v1 profile.",
    fields: [
      { key: "text", label: "Bamini text", kind: "textarea", initial: "jkpo;", help: "Example: jkpo; should produce U+0BA4 U+0BAE U+0BBF U+0BB4 U+0BCD." },
      { key: "errors", label: "Unknown input", kind: "select", initial: "strict", options: ["strict", "preserve"], help: "Strict reports ambiguous or unsupported characters. Preserve leaves them in the output." },
    ],
    build: (v) => ({ op: "bamini_to_unicode", input: { text: v.text, errors: v.errors } }),
  },
  {
    op: "unicode_to_bamini", label: "Unicode to Bamini", description: "Encode canonical Tamil text to Bamini when a safe round-trip mapping exists.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Try the sample text. Unsupported or non-round-trippable input returns an error." }],
    build: (v) => ({ op: "unicode_to_bamini", input: { text: v.text } }),
  },
  {
    op: "unicode_to_tscii_bytes", label: "Unicode to TSCII bytes", description: "Encode Unicode using the bounded TSCII profile.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported or non-round-trippable input returns an error." }],
    build: (v) => ({ op: "unicode_to_tscii_bytes", input: { text: v.text } }),
  },
  {
    op: "anjal_bytes_to_unicode", label: "Anjal bytes to Unicode", description: "Decode a selected legacy Anjal byte run using the bounded profile.",
    fields: [{ key: "bytes", label: "Anjal bytes (hex)", kind: "text", initial: "8D", help: "Enter two-digit hexadecimal bytes. Ambiguous bytes return an error." }],
    build: (v) => ({ op: "anjal_bytes_to_unicode", input: { bytes: parseHexBytes(v.bytes) } }),
  },
  {
    op: "unicode_to_anjal_bytes", label: "Unicode to Anjal bytes", description: "Encode Unicode using the bounded legacy Anjal profile.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported or non-round-trippable input returns an error." }],
    build: (v) => ({ op: "unicode_to_anjal_bytes", input: { text: v.text } }),
  },
  {
    op: "tam_bytes_to_unicode", label: "TAM bytes to Unicode", description: "Decode raw monolingual TAM bytes using the bounded profile.",
    fields: [{ key: "bytes", label: "TAM bytes (hex)", kind: "text", initial: "41", help: "Enter two-digit hexadecimal bytes. TAM byte 41 is a Tamil letter, not Latin A." }],
    build: (v) => ({ op: "tam_bytes_to_unicode", input: { bytes: parseHexBytes(v.bytes) } }),
  },
  {
    op: "unicode_to_tam_bytes", label: "Unicode to TAM bytes", description: "Encode Unicode using the monolingual TAM profile.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported Latin text or non-round-trippable input returns an error." }],
    build: (v) => ({ op: "unicode_to_tam_bytes", input: { text: v.text } }),
  },
  {
    op: "tab_bytes_to_unicode", label: "TAB bytes to Unicode", description: "Decode raw TAB bytes using the bounded profile.",
    fields: [{ key: "bytes", label: "TAB bytes (hex)", kind: "text", initial: "E8 A4", help: "Enter two-digit hexadecimal bytes separated by spaces." }],
    build: (v) => ({ op: "tab_bytes_to_unicode", input: { bytes: parseHexBytes(v.bytes) } }),
  },
  {
    op: "unicode_to_tab_bytes", label: "Unicode to TAB bytes", description: "Encode Unicode using the bounded TAB profile.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported or non-round-trippable input returns an error." }],
    build: (v) => ({ op: "unicode_to_tab_bytes", input: { text: v.text } }),
  },
  {
    op: "tscii_bytes_to_unicode", label: "TSCII bytes to Unicode", description: "Decode actual TSCII bytes using the bounded profile.",
    fields: [{ key: "bytes", label: "TSCII bytes (hex)", kind: "text", initial: "BA A2 C5 FD", help: "Enter two-digit hexadecimal bytes separated by spaces." }],
    build: (v) => ({ op: "tscii_bytes_to_unicode", input: { bytes: parseHexBytes(v.bytes) } }),
  },
];

const operationByName = new Map(operations.map((operation) => [operation.op, operation]));
const allOperationNames = operations.map((operation) => operation.op);
const allSuiteIds = ["tamil-toolkit", "tamil-wasm", "tamil-python", "tamil-dart"];

const $ = <T extends HTMLElement>(selector: string) => document.querySelector<T>(selector)!;
const grid = $("#package-grid");
const selectedPanel = $("#selected-package");
const operationSelect = $("#manual-operation") as HTMLSelectElement;
const manualRuntime = $("#manual-runtime");
const manualDescription = $("#manual-description");
const manualForm = $("#manual-form") as HTMLFormElement;
const manualFields = $("#manual-fields");
const manualExamples = $("#manual-examples");
const runManualButton = $("#run-manual") as HTMLButtonElement;
const resetManualButton = $("#reset-manual") as HTMLButtonElement;
const manualStatus = $("#manual-status");
const resultTitle = $("#result-title");
const resultKind = $("#result-kind");
const resultText = $("#manual-result-text");
const resultCodepoints = $("#manual-codepoints");
const resultJson = $("#manual-result-json");
const baminiDirections = $("#bamini-directions");
const runAllButton = $("#run-all") as HTMLButtonElement;
const runPackageButton = $("#run-package") as HTMLButtonElement;
const runNativeButton = $("#run-native") as HTMLButtonElement;
const requestText = $("#request-json") as HTMLTextAreaElement;
const requestButton = $("#run-request") as HTMLButtonElement;
const requestResponse = $("#request-response");
const nativeTestPanel = $("#native-test-panel");
const nativeTestOutput = $("#native-test-output");
const nativeTestState = $("#native-test-state");
const resultPanel = $("#case-results");
const summaryPanel = $("#run-summary");
const progressBar = $("#progress-bar");
const progressLabel = $("#progress-label");
const wasmState = $("#wasm-state");
const api = createApi(nativeExecute);
let selectedId = "tamil-numerals";
let selectedOperation = "format_fraction";
let running = false;
let nativeTesting = false;
let manualRunning = false;
let wasmReady = false;
let renderedFormKey = "";
let manualTimer: ReturnType<typeof setTimeout> | undefined;
let manualRequestVersion = 0;
let manualPending = false;

const stateLabel: Record<PackageState, string> = {
  active: "RUST PACKAGE",
  facade: "FACADE",
  dispatcher: "DISPATCHER",
  wasm: "BROWSER WASM",
  native: "NATIVE ADAPTER",
  planned: "PLANNED Â· UNAVAILABLE",
};

function packageSuites(info: PackageInfo): Suite[] {
  if (info.state === "dispatcher" || info.state === "wasm") return activeSuites;
  return (info.suiteFiles ?? [])
    .map((file) => suites.get(file))
    .filter((suite): suite is Suite => suite?.status === "active");
}

async function packageRows(info: PackageInfo): Promise<Outcome[]> {
  const loaded = await Promise.all(packageSuites(info).map((suite) => loadSuiteRows(suite.file)));
  return loaded.flat().filter((row) => !info.operations || info.operations.includes(row.op));
}

function operationsFor(info: PackageInfo): OperationSpec[] {
  let names: string[];
  if (info.operations) names = info.operations;
  else if (info.state === "dispatcher" || info.state === "wasm" || allSuiteIds.includes(info.id)) names = allOperationNames;
  else names = [...new Set(packageSuites(info).flatMap((suite) => suite.operations))];
  return names.map((name) => operationByName.get(name)).filter((op): op is OperationSpec => op !== undefined);
}

function runtimeFor(info: PackageInfo): Runtime {
  if (info.id === "tamil-python") return "python";
  if (info.id === "tamil-dart") return "dart";
  if (info.state === "planned") return "unavailable";
  return "wasm";
}

function runtimeLabel(runtime: Runtime): string {
  if (runtime === "python") return "Python Â· PyO3 native";
  if (runtime === "dart") return "Dart Â· FFI native";
  if (runtime === "wasm") return "Rust engine Â· browser WASM";
  return "No runtime available";
}

function stateClass(state: PackageState): string {
  if (state === "planned") return "planned";
  if (state === "native") return "native";
  return "active";
}

function renderPackages() {
  grid.replaceChildren();
  for (const info of packages) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = `package-card ${info.id === selectedId ? "selected" : ""}`;
    card.setAttribute("aria-pressed", String(info.id === selectedId));
    const top = document.createElement("span");
    top.className = "package-card-top";
    const name = document.createElement("strong");
    name.textContent = info.id;
    const badge = document.createElement("span");
    badge.className = `badge ${stateClass(info.state)}`;
    badge.textContent = stateLabel[info.state];
    top.append(name, badge);
    const description = document.createElement("span");
    description.className = "package-description";
    description.textContent = info.description;
    const foot = document.createElement("span");
    foot.className = "package-card-foot";
    if (info.state === "planned") foot.textContent = "Manual operation unavailable";
    else if (info.state === "native") foot.textContent = `${operationsFor(info).length} manual operations Â· native runtime`;
    else foot.textContent = `${operationsFor(info).length} manual operations`;
    card.append(top, description, foot);
    card.addEventListener("click", () => selectPackage(info.id));
    grid.append(card);
  }
}

function appendPackageNote(info: PackageInfo) {
  if (info.state === "planned") {
    const note = document.createElement("div");
    note.className = "planned-note";
    const suite = info.plannedSuite ? suites.get(info.plannedSuite) : undefined;
    note.textContent = suite
      ? `Not implemented. ${suite.file}: ${suite.reason ?? "Planned suite only."}`
      : "Not implemented. There is no runtime operation or active manual panel for this package yet.";
    selectedPanel.append(note);
    return;
  }
  if (info.state === "facade") {
    const note = document.createElement("div");
    note.className = "facade-note";
    note.textContent = "This facade re-exports NFC/NFD from tamil-core. The inputs below run through the shared Rust dispatcher.";
    selectedPanel.append(note);
  } else if (info.state === "native") {
    const note = document.createElement("div");
    note.className = "native-note";
    note.textContent = info.id === "tamil-python"
      ? "Manual requests run through the real PyO3 extension. It rebuilds when Rust sources change."
      : "Manual requests run through the Dart FFI package and host Rust library, rebuilt when Rust sources change.";
    selectedPanel.append(note);
  }
}

function renderSelected() {
  const info = packages.find((item) => item.id === selectedId)!;
  const packageOperations = operationsFor(info);
  selectedPanel.replaceChildren();
  const heading = document.createElement("div");
  heading.className = "selected-heading";
  const copy = document.createElement("div");
  const eyebrow = document.createElement("p");
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "Selected package";
  const title = document.createElement("h2");
  title.id = "selected-title";
  title.textContent = info.id;
  const description = document.createElement("p");
  description.className = "selected-description";
  description.textContent = info.description;
  copy.append(eyebrow, title, description);
  const badge = document.createElement("span");
  badge.className = `badge badge-large ${stateClass(info.state)}`;
  badge.textContent = stateLabel[info.state];
  heading.append(copy, badge);
  selectedPanel.append(heading);
  appendPackageNote(info);

  operationSelect.replaceChildren();
  for (const operation of packageOperations) {
    const option = document.createElement("option");
    option.value = operation.op;
    option.textContent = operation.label;
    operationSelect.append(option);
  }
  const supportsManual = packageOperations.length > 0;
  if (supportsManual && !packageOperations.some((operation) => operation.op === selectedOperation)) {
    selectedOperation = packageOperations[0].op;
  }
  operationSelect.value = selectedOperation;
  operationSelect.disabled = !supportsManual;
  manualRuntime.textContent = runtimeLabel(runtimeFor(info));
  baminiDirections.hidden = info.id !== "tamil-codec";

  const selectedSpec = packageOperations.find((operation) => operation.op === selectedOperation);
  manualDescription.textContent = selectedSpec?.description ?? "";
  const formKey = `${info.id}:${selectedSpec?.op ?? ""}`;
  if (formKey !== renderedFormKey) {
    renderFields(selectedSpec);
    renderedFormKey = formKey;
  }
  const runtime = runtimeFor(info);
  const canRun = supportsManual && (runtime === "wasm" ? wasmReady : import.meta.env.DEV);
  runManualButton.disabled = !canRun;
  resetManualButton.disabled = !supportsManual;
  manualForm.hidden = !supportsManual;
  manualStatus.textContent = !supportsManual
    ? "This package is not implemented yet."
      : manualRunning
      ? "Updating the live resultâ€¦"
      : canRun
        ? "Edit a value; the result updates automatically."
          : runtime === "wasm"
            ? "Loading Rust WASMâ€¦"
            : "Native manual requests require the local Vite development server.";

  const canRunVectors = ["active", "facade", "dispatcher", "wasm"].includes(info.state);
  runPackageButton.disabled = !canRunVectors || running || !wasmReady;
  runPackageButton.textContent = info.state === "dispatcher" || info.state === "wasm" ? "Run all vectors" : "Run package vectors";
  runAllButton.disabled = running || !wasmReady;
  const hasNativeTests = info.state !== "planned" && info.state !== "facade";
  runNativeButton.hidden = !hasNativeTests || !import.meta.env.DEV;
  runNativeButton.disabled = !hasNativeTests || nativeTesting;
  requestText.disabled = runtime === "wasm" ? !wasmReady : !supportsManual || !import.meta.env.DEV;
  requestButton.disabled = runtime === "wasm" ? !wasmReady : !supportsManual || !import.meta.env.DEV;
  if (requestText.dataset.packageId !== info.id) {
    const example = packageOperations[0];
    requestText.value = example
      ? JSON.stringify(example.build(Object.fromEntries(example.fields.map((field) => [field.key, field.initial]))), null, 2)
      : "";
    requestText.dataset.packageId = info.id;
  }
  requestResponse.textContent = supportsManual ? "Run a request to see the result." : "No request is available for this package.";
}

function renderFields(operation?: OperationSpec) {
  manualFields.replaceChildren();
  manualExamples.replaceChildren();
  manualExamples.hidden = !operation?.examples?.length;
  if (!operation) return;
  for (const field of operation.fields) {
    const wrapper = document.createElement("label");
    wrapper.className = "manual-field";
    wrapper.htmlFor = `field-${field.key}`;
    const title = document.createElement("span");
    title.className = "manual-field-label";
    title.textContent = field.label;
    let control: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement;
    if (field.kind === "textarea") {
      control = document.createElement("textarea");
      (control as HTMLTextAreaElement).rows = field.key === "words" ? 5 : 4;
      (control as HTMLTextAreaElement).spellcheck = false;
    } else if (field.kind === "select") {
      control = document.createElement("select");
      for (const choice of field.options ?? []) {
        const option = document.createElement("option");
        option.value = choice;
        option.textContent = choice;
        control.append(option);
      }
    } else {
      control = document.createElement("input");
      (control as HTMLInputElement).type = field.kind;
      if (field.kind === "number") (control as HTMLInputElement).step = "1";
      if (field.inputMode) (control as HTMLInputElement).inputMode = field.inputMode;
    }
    control.id = `field-${field.key}`;
    control.name = field.key;
    control.dataset.field = field.key;
    control.value = field.initial;
    if (field.kind === "number" || field.required) control.required = true;
    wrapper.append(title, control);
    if (field.help) {
      const help = document.createElement("small");
      help.className = "manual-field-help";
      help.textContent = field.help;
      wrapper.append(help);
    }
    manualFields.append(wrapper);
  }

  if (operation.examples?.length) {
    const label = document.createElement("span");
    label.className = "manual-examples-label";
    label.textContent = "Quick inputs";
    manualExamples.append(label);
    for (const example of operation.examples) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "example-chip";
      button.textContent = example.label;
      button.addEventListener("click", () => {
        for (const [key, value] of Object.entries(example.values)) {
          const control = [...manualFields.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("[data-field]")]
            .find((candidate) => candidate.dataset.field === key);
          if (control) control.value = value;
        }
        clearManualResult();
        scheduleManualRun(0);
      });
      manualExamples.append(button);
    }
  }
}

function selectPackage(id: string) {
  if (id === selectedId) return;
  selectedId = id;
  const defaultOperation = id === "tamil-numerals" ? "format_fraction" : undefined;
  selectedOperation = defaultOperation ?? operationsFor(packages.find((item) => item.id === id)!)[0]?.op ?? "";
  renderPackages();
  renderSelected();
  clearManualResult();
  scheduleManualRun(0);
}

function clearManualResult() {
  resultTitle.textContent = "Run an operation";
  resultKind.textContent = "WAITING";
  resultKind.className = "result-kind";
  resultText.textContent = "Your result will appear here.";
  resultCodepoints.textContent = "Output scalars: â€”";
  resultJson.textContent = "";
}

function setManualResult(title: string, value: unknown, isError = false) {
  resultTitle.textContent = title;
  resultKind.textContent = isError ? "ERROR" : "SUCCESS";
  resultKind.className = `result-kind ${isError ? "error" : "success"}`;
  resultText.replaceChildren();
  if (typeof value === "string") {
    resultText.textContent = value || "(empty string)";
  } else if (Array.isArray(value) && value.every((item) => typeof item === "string")) {
    const list = document.createElement("ol");
    for (const item of value) {
      const row = document.createElement("li");
      row.textContent = item;
      list.append(row);
    }
    resultText.append(list);
  } else {
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(value, null, 2);
    resultText.append(pre);
  }
  resultCodepoints.textContent = `Output scalars: ${scalarDescription(value)}`;
  resultJson.textContent = JSON.stringify(value, null, 2);
}

function scalarDescription(value: unknown): string {
  const scalarCodes = (text: string) => Array.from(text, (scalar) =>
    `U+${scalar.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0")}`
  ).join(" ") || "(empty)";
  if (typeof value === "string") return scalarCodes(value);
  if (Array.isArray(value) && value.every((item) => typeof item === "string")) {
    return value.map((text, index) => `${index + 1}: ${scalarCodes(text)}`).join(" Â· ") || "(empty list)";
  }
  const strings: string[] = [];
  const visit = (item: unknown, path: string) => {
    if (typeof item === "string") strings.push(`${path}: ${scalarCodes(item)}`);
    else if (Array.isArray(item)) item.forEach((child, index) => visit(child, `${path}[${index}]`));
    else if (item && typeof item === "object") {
      for (const [key, child] of Object.entries(item)) visit(child, path ? `${path}.${key}` : key);
    }
  };
  visit(value, "result");
  return strings.join(" Â· ") || "No string scalars in this output";
}

function readManualValues(): Record<string, string> {
  return Object.fromEntries([...manualFields.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("[data-field]")]
    .map((control) => [control.dataset.field!, control.value]));
}

async function executeAtRuntime(request: Request, runtime: Runtime): Promise<unknown> {
  if (runtime === "wasm") return api.execute(request);
  if (runtime !== "python" && runtime !== "dart") throw new Error("No executable runtime is available for this package.");
  const response = await fetch("/__workbench/manual-run", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ packageId: runtime === "python" ? "tamil-python" : "tamil-dart", request }),
  });
  const payload = await response.json() as { ok?: unknown; error?: string };
  if (!response.ok || payload.error !== undefined) throw new Error(payload.error ?? `Native runner returned HTTP ${response.status}`);
  return payload.ok;
}

function showManualInputNotice(title: string, message: string) {
  resultTitle.textContent = title;
  resultKind.textContent = "INPUT";
  resultKind.className = "result-kind";
  resultText.textContent = message;
  resultCodepoints.textContent = "Output scalars: â€”";
  resultJson.textContent = "";
}

function scheduleManualRun(delay = 220) {
  if (manualTimer) clearTimeout(manualTimer);
  manualRequestVersion += 1;
  const info = packages.find((item) => item.id === selectedId)!;
  if (!operationsFor(info).some((operation) => operation.op === selectedOperation)) {
    manualStatus.textContent = "This package has no implemented runtime operation.";
    return;
  }
  manualStatus.textContent = delay === 0 ? "Updating live resultâ€¦" : "Typingâ€¦ result will update shortly.";
  manualTimer = setTimeout(() => {
    manualTimer = undefined;
    void runManual();
  }, delay);
}

async function runManual() {
  if (manualRunning) {
    manualPending = true;
    return;
  }
  const info = packages.find((item) => item.id === selectedId)!;
  const operation = operationsFor(info).find((item) => item.op === selectedOperation);
  if (!operation) return;
  const requestVersion = manualRequestVersion;
  if (!manualForm.checkValidity()) {
    const invalid = manualFields.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>(":invalid");
    const label = invalid?.closest("label")?.querySelector(".manual-field-label")?.textContent ?? "This value";
    const message = invalid instanceof HTMLInputElement && invalid.type === "number"
      ? `${label} needs a valid whole number.`
      : `${label} is required.`;
    showManualInputNotice("Input needed", message);
    manualStatus.textContent = "Enter a valid value to update the result.";
    return;
  }
  const runtime = runtimeFor(info);
  if (runtime === "wasm" && !wasmReady) {
    manualStatus.textContent = "Loading Rust WASMâ€¦";
    return;
  }
  if ((runtime === "python" || runtime === "dart") && !import.meta.env.DEV) {
    manualStatus.textContent = "Native manual requests require the local Vite development server.";
    return;
  }
  manualRunning = true;
  resultKind.textContent = "UPDATING";
  resultKind.className = "result-kind updating";
  manualStatus.textContent = `Updating through ${runtimeLabel(runtime)}â€¦`;
  let succeeded = false;
  try {
    const request = operation.build(readManualValues());
    const value = await executeAtRuntime(request, runtime);
    succeeded = true;
    if (manualRequestVersion === requestVersion && selectedId === info.id && selectedOperation === operation.op) {
      setManualResult(operation.label, value);
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (manualRequestVersion === requestVersion && selectedId === info.id && selectedOperation === operation.op) {
      setManualResult(operation.label, message, true);
    }
  } finally {
    manualRunning = false;
    if (manualPending) {
      manualPending = false;
      void runManual();
    } else if (manualRequestVersion === requestVersion && selectedId === info.id && selectedOperation === operation.op) {
      manualStatus.textContent = succeeded ? "Live result updated." : "Request returned an error.";
    }
  }
}

manualForm.addEventListener("submit", (event) => {
  event.preventDefault();
  scheduleManualRun(0);
});

manualFields.addEventListener("input", () => scheduleManualRun());
manualFields.addEventListener("change", () => scheduleManualRun());

operationSelect.addEventListener("change", () => {
  selectedOperation = operationSelect.value;
  const info = packages.find((item) => item.id === selectedId)!;
  const operation = operationsFor(info).find((item) => item.op === selectedOperation);
  manualDescription.textContent = operation?.description ?? "";
  renderFields(operation);
  renderedFormKey = `${info.id}:${selectedOperation}`;
  clearManualResult();
  scheduleManualRun(0);
});

resetManualButton.addEventListener("click", () => {
  const info = packages.find((item) => item.id === selectedId)!;
  renderFields(operationsFor(info).find((item) => item.op === selectedOperation));
  clearManualResult();
  scheduleManualRun(0);
});

function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const object = value as Record<string, unknown>;
    return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${canonical(object[key])}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "undefined";
}

function runOne(row: Outcome): CaseResult {
  if (row.expected_error !== undefined) {
    try {
      const actual = api.execute({ op: row.op, input: row.input } as Request);
      return { row, passed: false, actual, error: `Expected error: ${row.expected_error}` };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return { row, passed: message === row.expected_error, actual: null, error: message };
    }
  }
  try {
    const actual = api.execute({ op: row.op, input: row.input } as Request);
    const passed = canonical(actual) === canonical(row.expected);
    return { row, passed, actual, error: passed ? undefined : "Result does not match the golden vector." };
  } catch (error) {
    return { row, passed: false, actual: null, error: error instanceof Error ? error.message : String(error) };
  }
}

function resultTextForCase(result: CaseResult, key: "actual" | "expected"): string {
  if (key === "expected" && result.row.expected_error !== undefined) return `Error: ${result.row.expected_error}`;
  if (key === "actual" && result.error && result.actual === null) return `Error: ${result.error}`;
  const value = key === "expected" ? result.row.expected : result.actual;
  const text = JSON.stringify(value, null, 2);
  return text.length > 1200 ? `${text.slice(0, 1200)}\nâ€¦ truncated` : text;
}

function renderVectorResults(results: CaseResult[], title: string) {
  const passed = results.filter((result) => result.passed).length;
  const failed = results.length - passed;
  summaryPanel.replaceChildren();
  const summary = document.createElement("div");
  summary.className = `summary-card ${failed ? "has-failures" : "all-passed"}`;
  const headline = document.createElement("strong");
  headline.textContent = failed ? `${failed.toLocaleString()} failed` : `${passed.toLocaleString()} passed`;
  const detail = document.createElement("span");
  detail.textContent = `${title} Â· ${results.length.toLocaleString()} active cases`;
  summary.append(headline, detail);
  summaryPanel.append(summary);

  resultPanel.replaceChildren();
  const shown = failed ? results.filter((result) => !result.passed).slice(0, 100) : results.slice(0, 10);
  const note = document.createElement("p");
  note.className = "results-note";
  note.textContent = failed ? `Showing up to 100 failing cases${failed > 100 ? ` of ${failed}` : ""}.` : `All cases passed. Showing ${shown.length} sample cases.`;
  resultPanel.append(note);
  const list = document.createElement("div");
  list.className = "result-list";
  for (const result of shown) {
    const row = document.createElement("details");
    row.className = `result-row ${result.passed ? "pass" : "fail"}`;
    const summaryLine = document.createElement("summary");
    const badge = document.createElement("span");
    badge.className = `result-badge ${result.passed ? "pass" : "fail"}`;
    badge.textContent = result.passed ? "PASS" : "FAIL";
    const id = document.createElement("code");
    id.textContent = result.row.id;
    const operation = document.createElement("span");
    operation.textContent = result.row.op;
    summaryLine.append(badge, id, operation);
    row.append(summaryLine);
    if (!result.passed) {
      const error = document.createElement("p");
      error.className = "failure-reason";
      error.textContent = result.error ?? "Unexpected result.";
      const expected = document.createElement("pre");
      expected.textContent = `Expected\n${resultTextForCase(result, "expected")}`;
      const actual = document.createElement("pre");
      actual.textContent = `Actual\n${resultTextForCase(result, "actual")}`;
      row.append(error, expected, actual);
    }
    list.append(row);
  }
  resultPanel.append(list);
}

async function runVectors(loadRows: () => Promise<Outcome[]>, title: string) {
  if (running || !wasmReady) return;
  running = true;
  summaryPanel.textContent = "";
  resultPanel.textContent = "";
  progressBar.style.width = "0%";
  progressLabel.textContent = "Loading fixturesâ€¦";
  try {
    const rows = await loadRows();
    const results: CaseResult[] = [];
    progressLabel.textContent = `0 / ${rows.length.toLocaleString()}`;
    for (let index = 0; index < rows.length; index += 1) {
      results.push(runOne(rows[index]));
      if ((index + 1) % 250 === 0 || index + 1 === rows.length) {
        progressBar.style.width = `${((index + 1) / rows.length) * 100}%`;
        progressLabel.textContent = `${(index + 1).toLocaleString()} / ${rows.length.toLocaleString()}`;
        await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
      }
    }
    renderVectorResults(results, title);
    progressBar.style.width = "100%";
    progressLabel.textContent = "Complete";
  } catch (error) {
    summaryPanel.textContent = `Could not load or run fixtures: ${error instanceof Error ? error.message : String(error)}`;
    progressLabel.textContent = "Failed to load";
  }
  running = false;
  renderPackages();
  renderSelected();
}

runAllButton.addEventListener("click", () => void runVectors(async () => {
  const loaded = await Promise.all(activeSuites.map((suite) => loadSuiteRows(suite.file)));
  return loaded.flat();
}, "All active golden suites"));
runPackageButton.addEventListener("click", () => {
  const info = packages.find((item) => item.id === selectedId)!;
  void runVectors(() => packageRows(info), info.id);
});

runNativeButton.addEventListener("click", async () => {
  if (nativeTesting) return;
  nativeTesting = true;
  const info = packages.find((item) => item.id === selectedId)!;
  nativeTestPanel.hidden = false;
  nativeTestOutput.textContent = `$ ${info.id} native tests\n`;
  nativeTestState.textContent = "Runningâ€¦";
  renderSelected();
  const append = (text: string) => {
    const combined = nativeTestOutput.textContent + text;
    nativeTestOutput.textContent = combined.length > 200_000 ? `[Earlier output trimmed]\n${combined.slice(-200_000)}` : combined;
    nativeTestOutput.scrollTop = nativeTestOutput.scrollHeight;
  };
  try {
    const response = await fetch("/__workbench/native-test", {
      method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ packageId: info.id }),
    });
    if (!response.ok || !response.body) throw new Error((await response.text()) || `Test runner returned HTTP ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let pending = "";
    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value, { stream: !done });
      const lines = pending.split("\n");
      pending = lines.pop() ?? "";
      for (const line of lines) {
        if (!line) continue;
        const event = JSON.parse(line) as { type: string; label?: string; text?: string; success?: boolean; message?: string };
        if (event.type === "step") append(`\n> ${event.label}\n`);
        else if (event.type === "output") append(event.text ?? "");
        else if (event.type === "complete") {
          nativeTestState.textContent = event.success ? "Passed" : "Failed";
          if (event.message) append(`\n${event.message}\n`);
        }
      }
      if (done) break;
    }
    if (pending) {
      const event = JSON.parse(pending) as { type: string; success?: boolean; message?: string };
      if (event.type === "complete") {
        nativeTestState.textContent = event.success ? "Passed" : "Failed";
        if (event.message) append(`\n${event.message}\n`);
      }
    }
  } catch (error) {
    nativeTestState.textContent = "Could not run";
    append(`\n${error instanceof Error ? error.message : String(error)}\n`);
  } finally {
    nativeTesting = false;
    renderSelected();
  }
});

requestButton.addEventListener("click", async () => {
  try {
    const request = JSON.parse(requestText.value) as Request;
    const info = packages.find((item) => item.id === selectedId)!;
    const value = await executeAtRuntime(request, runtimeFor(info));
    requestResponse.textContent = JSON.stringify(value, null, 2);
    requestResponse.className = "request-success";
  } catch (error) {
    requestResponse.textContent = error instanceof Error ? error.message : String(error);
    requestResponse.className = "request-error";
  }
});

if (import.meta.hot) {
  import.meta.hot.on("workbench:wasm-build", (event: { state: string; message?: string }) => {
    if (event.state === "building") wasmState.textContent = "Rust changed Â· rebuilding WASMâ€¦";
    else if (event.state === "failed") wasmState.textContent = `WASM rebuild failed Â· ${event.message ?? "see terminal"}`;
  });
}

$("#fixture-count").textContent = `${operations.length} interactive operations Â· ${packages.length} packages listed`;
renderPackages();
renderSelected();

try {
  await init({ module_or_path: wasmUrl });
  wasmReady = true;
  wasmState.textContent = import.meta.env.DEV ? "Rust WASM ready Â· hot reload on" : "Rust WASM ready Â· production build";
  $("#hmr-note").textContent = import.meta.env.DEV
    ? "UI edits hot reload Â· Rust or lexicon edits rebuild WASM"
    : "Local workbench build Â· native adapter requests are available in dev mode";
  runAllButton.disabled = false;
  renderSelected();
  scheduleManualRun(0);
} catch (error) {
  wasmState.textContent = `WASM failed to load Â· ${error instanceof Error ? error.message : String(error)}`;
  manualStatus.textContent = wasmState.textContent;
}
