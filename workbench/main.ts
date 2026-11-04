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
  kind: "text" | "textarea" | "number" | "select" | "date";
  initial: string;
  inputMode?: "decimal" | "numeric";
  required?: boolean;
  options?: string[];
  help?: string;
  visibleWhen?: { key: string; value: string };
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
const numeralOperationNames = manifest.suites
  .filter((suite) => ["numerals_lkr_inr.jsonl", "numerals_fractions_dates.jsonl", "numerals_v03.jsonl"].includes(suite.file))
  .flatMap((suite) => suite.operations);
const calendarSuiteFiles = [
  "calendar_vakya_solar.jsonl", "calendar_vakya_moon.jsonl", "calendar_vakya_local_sunrise.jsonl",
  "calendar_vakya_cara.jsonl", "calendar_vakya_desantara.jsonl", "calendar_vakya_bhujaantara.jsonl",
  "calendar_vakya_civil.jsonl", "calendar_thirukanitham.jsonl", "calendar_lunar_phases.jsonl",
  "calendar_solar_arithmetic.jsonl", "calendar_daylight_periods.jsonl", "calendar_year_cycle.jsonl",
  "calendar_official_holidays.jsonl", "calendar_tamil_display.jsonl", "calendar_profile_comparison.jsonl",
  "calendar_thiruvalluvar_year.jsonl", "calendar_observances.jsonl"
];
const calendarOperationNames = manifest.suites
  .filter((suite) => calendarSuiteFiles.includes(suite.file))
  .flatMap((suite) => suite.operations);
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
  { id: "tamil-numerals", state: "active", description: "TN/SL number words, exact numeric strings, fractions, and Gregorian civil dates.", suiteFiles: ["numerals_lkr_inr.jsonl", "numerals_fractions_dates.jsonl", "numerals_v03.jsonl"], operations: numeralOperationNames },
  { id: "tamil-calendar", state: "active", description: "Solar arithmetic, Vakiya and Thirukanitham models, five limbs, holidays, and observances.", suiteFiles: calendarSuiteFiles, operations: calendarOperationNames },
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
function parseHexBytes(value: string): number[] {
  const text = value.trim();
  if (!text) return [];
  return text.split(/\s+/).map((part) => {
    if (!/^(?:0x)?[0-9a-f]{2}$/i.test(part)) throw new Error("Enter bytes as two-digit hex values separated by spaces, for example BA A2 C5 FD.");
    return Number.parseInt(part.replace(/^0x/i, ""), 16);
  });
}

function parseHexCodes(value: string): number[] {
  const text = value.trim();
  if (!text) return [];
  return text.split(/\s+/).map((part) => {
    if (!/^(?:0x)?[0-9a-f]{1,4}$/i.test(part)) throw new Error("Enter 16-bit hexadecimal codes separated by spaces, for example 0062 006A 0161.");
    return Number.parseInt(part.replace(/^0x/i, ""), 16);
  });
}

function exactValueFields(prefix = ""): FieldSpec[] {
  const key = (name: string) => prefix ? `${prefix}_${name}` : name;
  const label = (name: string) => prefix ? `${prefix[0].toUpperCase()}${prefix.slice(1)} ${name}` : name;
  return [
    { key: key("negative"), label: label("sign"), kind: "select", initial: "false", options: ["false", "true"] },
    { key: key("coefficient"), label: label("coefficient digits"), kind: "text", inputMode: "numeric", required: true, initial: "123400", help: "ASCII digits without a sign or decimal point; up to 256 digits." },
    { key: key("scale"), label: label("scale"), kind: "number", initial: "4", help: "Number of fractional digits, from 0 through 256." },
  ];
}

function exactValueFromFields(values: Record<string, string>, prefix = "") {
  const key = (name: string) => prefix ? `${prefix}_${name}` : name;
  return {
    negative: values[key("negative")] === "true",
    coefficient: values[key("coefficient")],
    scale: Number(values[key("scale")]),
  };
}

function numericEndpointFields(prefix: "start" | "end", initialType: "decimal" | "fraction"): FieldSpec[] {
  const capitalized = prefix[0].toUpperCase() + prefix.slice(1);
  return [
    { key: `${prefix}_type`, label: `${capitalized} endpoint`, kind: "select", initial: initialType, options: ["decimal", "fraction"] },
    { key: `${prefix}_negative`, label: `${capitalized} decimal sign`, kind: "select", initial: "false", options: ["false", "true"] },
    { key: `${prefix}_coefficient`, label: `${capitalized} decimal coefficient`, kind: "text", inputMode: "numeric", required: true, initial: "1", help: "ASCII digits; used when this endpoint is decimal." },
    { key: `${prefix}_scale`, label: `${capitalized} decimal scale`, kind: "number", initial: "1", help: "Used when this endpoint is decimal." },
    { key: `${prefix}_numerator`, label: `${capitalized} fraction numerator`, kind: "number", initial: "1", help: "Signed integer; used when this endpoint is a fraction." },
    { key: `${prefix}_denominator`, label: `${capitalized} fraction denominator`, kind: "number", initial: "2", help: "Positive integer; used when this endpoint is a fraction." },
  ];
}

function numericEndpointFromFields(values: Record<string, string>, prefix: "start" | "end") {
  if (values[`${prefix}_type`] === "decimal") {
    return { type: "decimal", value: exactValueFromFields(values, prefix) };
  }
  return {
    type: "fraction",
    numerator: Number(values[`${prefix}_numerator`]),
    denominator: Number(values[`${prefix}_denominator`]),
  };
}

function isoDateParts(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) throw new Error("Enter an ISO date in YYYY-MM-DD form.");
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
}

function utcDateStartUnix(value: string) {
  const timestamp = Date.parse(`${value}T00:00:00Z`);
  if (!Number.isSafeInteger(timestamp)) throw new Error("Enter a valid ISO UTC date.");
  return timestamp / 1_000;
}

const thirukanithamDefinition = "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2";
const vakyaCivilDefinition = "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1";
const thirukanithamChoice = "Thirukanitham";
const vakyaCivilChoice = "Vakyakarana 1962 · Ujjain";

function selectedCalendarDefinition(values: Record<string, string>) {
  return values.calendar_profile === vakyaCivilChoice ? vakyaCivilDefinition : thirukanithamDefinition;
}

function selectedCalendarContext(values: Record<string, string>) {
  return values.calendar_profile === vakyaCivilChoice
    ? { reference_station: "ujjain", time_zone: values.time_zone }
    : drikContext(values);
}

function calendarContextFields(profileInitial = thirukanithamChoice): FieldSpec[] {
  return [
    { key: "calendar_profile", label: "Calendar profile", kind: "select", initial: profileInitial, options: [thirukanithamChoice, vakyaCivilChoice] },
    { key: "time_zone", label: "Time zone", kind: "select", initial: "Asia/Kolkata", options: ["Asia/Kolkata", "Asia/Colombo"], help: "Vakyakarana civil calculations use the fixed Ujjain reference station; this zone only labels the civil instant." , visibleWhen: { key: "calendar_profile", value: vakyaCivilChoice } },
    ...drikContextFields().map((field) => ({ ...field, visibleWhen: { key: "calendar_profile", value: thirukanithamChoice } })),
  ];
}

function drikContextFields(): FieldSpec[] {
  return [
    { key: "region", label: "Region", kind: "select", initial: "TN", options: ["TN", "SL"], help: "TN uses Asia/Kolkata; SL uses Asia/Colombo. Both are UTC+05:30 throughout this profile's range." },
    { key: "latitude", label: "Latitude (degrees north)", kind: "text", inputMode: "decimal", required: true, initial: "13.087840", help: "TN: 8.000000–13.700000. SL: 5.800000–9.900000." },
    { key: "longitude", label: "Longitude (degrees east)", kind: "text", inputMode: "decimal", required: true, initial: "80.278470", help: "TN: 76.000000–80.500000. SL: 79.400000–82.000000." },
    { key: "elevation", label: "Elevation (metres)", kind: "number", initial: "14", help: "Supported range −100 through 3000 metres." },
  ];
}

function drikContext(values: Record<string, string>) {
  const region = values.region as "TN" | "SL";
  const decimalDegrees = (value: string, field: string) => {
    if (!/^-?\d{1,3}(?:\.\d{1,6})?$/.test(value)) throw new Error(`${field} must use decimal degrees with at most six decimal places.`);
    return Math.round(Number(value) * 1_000_000);
  };
  return {
    region,
    latitude_microdegrees: decimalDegrees(values.latitude, "Latitude"),
    longitude_microdegrees: decimalDegrees(values.longitude, "Longitude"),
    elevation_meters: Number(values.elevation),
    time_zone: region === "TN" ? "Asia/Kolkata" : "Asia/Colombo",
  };
}

function drikLocalInstant(values: Record<string, string>) {
  const { year, month, day } = isoDateParts(values.local_date);
  const match = /^(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(values.local_time);
  if (!match) throw new Error("Enter local time as HH:MM or HH:MM:SS.");
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  const second = Number(match[3] ?? "0");
  if (hour > 23 || minute > 59 || second > 59) throw new Error("Enter a valid local 24-hour time.");
  // This finite profile pins both supported modern zones to UTC+05:30.
  return Math.floor(Date.UTC(year, month - 1, day, hour, minute, second) / 1000) - 19_800;
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
    op: "format_currency", label: "Format minor-unit amount", description: "Format an integer number of minor units using the existing INR or LKR operation.",
    fields: [
      { key: "amount_minor", label: "Minor units (paise or cents)", kind: "number", initial: "102550", help: "Signed integer; 100 minor units make one major unit." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "format_currency", input: { amount_minor: Number(v.amount_minor), currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR 1,025.50 · SL", values: { amount_minor: "102550", currency: "LKR", locale: "SL" } },
      { label: "Negative INR · TN", values: { amount_minor: "-105", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "currency_to_words", label: "Minor-unit currency to words", description: "Spell an integer minor-unit amount using the existing TN or SL currency profile.",
    fields: [
      { key: "amount_minor", label: "Minor units (paise or cents)", kind: "number", initial: "102550", help: "Signed integer; 100 minor units make one major unit." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "currency_to_words", input: { amount_minor: Number(v.amount_minor), currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR 1,025.50 · SL", values: { amount_minor: "102550", currency: "LKR", locale: "SL" } },
      { label: "Zero paise · INR", values: { amount_minor: "100", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "format_currency_decimal", label: "Format currency", description: "Format an exact amount entered in rupees, with up to two decimal places.",
    fields: [
      { key: "amount", label: "Amount", kind: "text", inputMode: "decimal", required: true, initial: "1025.50", help: "Type the amount normally, e.g. 1025.50. Use a dot and up to 2 decimal places; no grouping commas." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "format_currency_decimal", input: { amount: v.amount, source_digits: "latin", currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR Â· 1,025.50 Â· SL", values: { amount: "1025.50", currency: "LKR", locale: "SL" } },
      { label: "INR Â· 0.99 Â· TN", values: { amount: "0.99", currency: "INR", locale: "TN" } },
      { label: "Negative amount", values: { amount: "-1.05", currency: "LKR", locale: "TN" } },
      { label: "Above maximum Â· error", values: { amount: "1000000000.00", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "currency_decimal_to_words", label: "Currency to words", description: "Spell an exact amount entered in rupees, with up to two decimal places.",
    fields: [
      { key: "amount", label: "Amount", kind: "text", inputMode: "decimal", required: true, initial: "1025.50", help: "Type the amount normally, e.g. 1025.50. Use a dot and up to 2 decimal places; no grouping commas." },
      { key: "currency", label: "Currency", kind: "select", initial: "LKR", options: ["INR", "LKR"] },
      { key: "locale", label: "Locale", kind: "select", initial: "SL", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "currency_decimal_to_words", input: { amount: v.amount, source_digits: "latin", currency: v.currency, locale: v.locale } }),
    examples: [
      { label: "LKR Â· 1,025.50 Â· SL", values: { amount: "1025.50", currency: "LKR", locale: "SL" } },
      { label: "INR Â· 0.99 Â· TN", values: { amount: "0.99", currency: "INR", locale: "TN" } },
      { label: "Negative amount", values: { amount: "-1.05", currency: "LKR", locale: "TN" } },
      { label: "Above maximum Â· error", values: { amount: "1000000000.00", currency: "INR", locale: "TN" } },
    ],
  },
  {
    op: "convert_digits", label: "Convert digit script", description: "Replace only Latin or Tamil positional digits; preserve all other characters.",
    fields: [
      { key: "text", label: "Text", kind: "textarea", initial: "ID 2026 / \u0be7\u0be8", help: "Paste any text; punctuation, spaces, and joiners are preserved." },
      { key: "to", label: "Convert digits to", kind: "select", initial: "tamil", options: ["latin", "tamil"] },
    ],
    build: (v) => ({ op: "convert_digits", input: { text: v.text, to: v.to } }),
    examples: [
      { label: "Latin to Tamil", values: { text: "ID 2026 / 9", to: "tamil" } },
      { label: "Tamil to Latin", values: { text: "\u0be8\u0be6\u0be8\u0bec", to: "latin" } },
    ],
  },
  {
    op: "parse_decimal", label: "Parse exact decimal", description: "Parse a bounded decimal string into sign, coefficient digits, and scale without floating point.",
    fields: [
      { key: "text", label: "Decimal text", kind: "text", inputMode: "decimal", required: true, initial: "12,34,567.80" },
      { key: "source_digits", label: "Source digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "grouping", label: "Grouping", kind: "select", initial: "indian", options: ["none", "indian"] },
      { key: "allow_mixed_digits", label: "Allow mixed digit scripts", kind: "select", initial: "false", options: ["false", "true"] },
    ],
    build: (v) => ({ op: "parse_decimal", input: { text: v.text, source_digits: v.source_digits, grouping: v.grouping, allow_mixed_digits: v.allow_mixed_digits === "true" } }),
    examples: [
      { label: "Indian grouping", values: { text: "12,34,567.80", source_digits: "latin", grouping: "indian", allow_mixed_digits: "false" } },
      { label: "Tamil digits", values: { text: "\u0be7\u0be8.\u0be9\u0bea\u0be6\u0be6", source_digits: "tamil", grouping: "none", allow_mixed_digits: "false" } },
      { label: "Retained fractional zeroes", values: { text: "-0.0500", source_digits: "latin", grouping: "none", allow_mixed_digits: "false" } },
    ],
  },
  {
    op: "format_decimal", label: "Format exact decimal", description: "Render an exact decimal while retaining its scale and choosing digit and grouping styles.",
    fields: [
      ...exactValueFields(),
      { key: "digits", label: "Output digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "grouping", label: "Grouping", kind: "select", initial: "indian", options: ["none", "indian"] },
    ],
    build: (v) => ({ op: "format_decimal", input: { value: exactValueFromFields(v), digits: v.digits, grouping: v.grouping } }),
    examples: [
      { label: "Grouped Tamil digits", values: { negative: "false", coefficient: "123456700", scale: "2", digits: "tamil", grouping: "indian" } },
      { label: "Negative with retained zeroes", values: { negative: "true", coefficient: "1200", scale: "3", digits: "latin", grouping: "none" } },
    ],
  },
  {
    op: "decimal_to_words", label: "Decimal to words", description: "Use the pinned formal Tamil decimal spellout and read each fractional digit separately.",
    fields: [
      { key: "text", label: "Decimal text", kind: "text", inputMode: "decimal", required: true, initial: "12.03" },
      { key: "source_digits", label: "Source digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
      { key: "grouping", label: "Grouping", kind: "select", initial: "none", options: ["none", "indian"] },
      { key: "allow_mixed_digits", label: "Allow mixed digit scripts", kind: "select", initial: "false", options: ["false", "true"] },
    ],
    build: (v) => ({ op: "decimal_to_words", input: { text: v.text, source_digits: v.source_digits, locale: v.locale, grouping: v.grouping, allow_mixed_digits: v.allow_mixed_digits === "true" } }),
    examples: [
      { label: "Preserve fractional zero", values: { text: "12.03", source_digits: "latin", locale: "TN", grouping: "none", allow_mixed_digits: "false" } },
      { label: "Sri Lankan profile", values: { text: "100000.20", source_digits: "latin", locale: "SL", grouping: "none", allow_mixed_digits: "false" } },
    ],
  },
  {
    op: "ordinal_to_words", label: "Ordinal to words", description: "Spell a positive integer ordinal using the declared TN or SL formal profile.",
    fields: [
      { key: "value", label: "Positive integer", kind: "number", initial: "21", help: "Supported range: 1 through 999,999,999." },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "ordinal_to_words", input: { value: Number(v.value), locale: v.locale } }),
    examples: [
      { label: "21st Â· TN", values: { value: "21", locale: "TN" } },
      { label: "100,000th Â· SL", values: { value: "100000", locale: "SL" } },
    ],
  },
  {
    op: "digit_sequence_to_words", label: "Digit sequence to words", description: "Read each digit separately while preserving leading zeroes.",
    fields: [
      { key: "text", label: "Digit sequence", kind: "text", inputMode: "numeric", required: true, initial: "0071" },
      { key: "source_digits", label: "Source digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "locale", label: "Locale", kind: "select", initial: "TN", options: ["TN", "SL"] },
    ],
    build: (v) => ({ op: "digit_sequence_to_words", input: { text: v.text, source_digits: v.source_digits, locale: v.locale } }),
    examples: [
      { label: "Keep leading zeroes", values: { text: "0071", source_digits: "latin", locale: "TN" } },
      { label: "Tamil digits Â· SL", values: { text: "\u0be6\u0be6\u0bed\u0be7", source_digits: "tamil", locale: "SL" } },
    ],
  },
  {
    op: "parse_fraction_symbol", label: "Read Tamil fraction symbol", description: "Return the exact reduced rational value for one encoded Tamil fraction scalar.",
    fields: [{ key: "text", label: "One fraction symbol", kind: "text", required: true, initial: String.fromCodePoint(0x11fd1), help: "Paste exactly one Unicode Tamil fraction symbol, optionally preceded by an ASCII minus sign." }],
    build: (v) => ({ op: "parse_fraction_symbol", input: { text: v.text } }),
    examples: [
      { label: "Half", values: { text: String.fromCodePoint(0x11fd1) } },
      { label: "One thirty-second", values: { text: String.fromCodePoint(0x11fc7) } },
    ],
  },
  {
    op: "symbol_info", label: "Inspect Tamil numeric symbol", description: "Show Unicode name, codepoint, category, and any sourced rational value for a supported symbol.",
    fields: [{ key: "text", label: "One Tamil symbol", kind: "text", required: true, initial: String.fromCodePoint(0x0bf0), help: "Paste one scalar from the declared Tamil numeric and clerical subset." }],
    build: (v) => ({ op: "symbol_info", input: { text: v.text } }),
    examples: [
      { label: "Tamil number ten", values: { text: String.fromCodePoint(0x0bf0) } },
      { label: "Tamil half symbol", values: { text: String.fromCodePoint(0x11fd1) } },
    ],
  },
  {
    op: "format_mixed_fraction", label: "Format mixed fraction", description: "Reduce and render a whole number plus a proper fractional part.",
    fields: [
      { key: "negative", label: "Negative", kind: "select", initial: "false", options: ["false", "true"] },
      { key: "whole", label: "Whole part", kind: "number", initial: "5" },
      { key: "numerator", label: "Fraction numerator", kind: "number", initial: "2" },
      { key: "denominator", label: "Fraction denominator", kind: "number", initial: "4" },
      { key: "digits", label: "Digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
    ],
    build: (v) => ({ op: "format_mixed_fraction", input: { negative: v.negative === "true", whole: Number(v.whole), numerator: Number(v.numerator), denominator: Number(v.denominator), digits: v.digits } }),
    examples: [
      { label: "Reduce 5 2/4", values: { negative: "false", whole: "5", numerator: "2", denominator: "4", digits: "latin" } },
      { label: "Tamil digits Â· quarter", values: { negative: "false", whole: "0", numerator: "1", denominator: "4", digits: "tamil" } },
    ],
  },
  {
    op: "parse_mixed_fraction", label: "Parse mixed fraction", description: "Parse only the canonical mixed-fraction format returned by the formatter.",
    fields: [
      { key: "text", label: "Mixed fraction", kind: "text", required: true, initial: "5 1/2", help: "Use one space between whole and fraction; fractions must be reduced." },
      { key: "source_digits", label: "Source digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
    ],
    build: (v) => ({ op: "parse_mixed_fraction", input: { text: v.text, source_digits: v.source_digits } }),
    examples: [
      { label: "Positive mixed value", values: { text: "5 1/2", source_digits: "latin" } },
      { label: "Negative proper fraction", values: { text: "-0 1/4", source_digits: "latin" } },
    ],
  },
  {
    op: "format_traditional_integer", label: "Format traditional integer", description: "Render a bounded integer with the canonical CLDR Tamil traditional-number rules.",
    fields: [{ key: "value", label: "Integer", kind: "number", initial: "1234567", help: "Supported range: -99,999,999 through 99,999,999." }],
    build: (v) => ({ op: "format_traditional_integer", input: { value: Number(v.value) } }),
    examples: [
      { label: "1,234,567", values: { value: "1234567" } },
      { label: "Negative integer", values: { value: "-125" } },
    ],
  },
  {
    op: "parse_traditional_integer", label: "Parse traditional integer", description: "Accept a traditional Tamil number only when it is in canonical CLDR form.",
    fields: [{ key: "text", label: "Traditional Tamil integer", kind: "text", required: true, initial: "\u0bf0\u0be8\u0bf1\u0bf2\u0be9\u0bf0\u0bea\u0bf2\u0beb\u0bf1\u0bec\u0bf0\u0bed", help: "Paste a complete canonical traditional integer; positional digits and multiplicative signs are distinct." }],
    build: (v) => ({ op: "parse_traditional_integer", input: { text: v.text } }),
    examples: [
      { label: "Canonical sample", values: { text: "\u0bf0\u0be8\u0bf1\u0bf2\u0be9\u0bf0\u0bea\u0bf2\u0beb\u0bf1\u0bec\u0bf0\u0bed" } },
      { label: "Tamil positional zero", values: { text: "\u0be6" } },
    ],
  },
  {
    op: "parse_percent", label: "Parse percent", description: "Parse a decimal percent with an adjacent ASCII percent sign; the result is a percent value.",
    fields: [
      { key: "text", label: "Percent text", kind: "text", inputMode: "decimal", required: true, initial: "12.50%" },
      { key: "source_digits", label: "Source digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "grouping", label: "Grouping", kind: "select", initial: "none", options: ["none", "indian"] },
    ],
    build: (v) => ({ op: "parse_percent", input: { text: v.text, source_digits: v.source_digits, grouping: v.grouping } }),
    examples: [
      { label: "Exact retained scale", values: { text: "12.50%", source_digits: "latin", grouping: "none" } },
      { label: "Tamil digits", values: { text: "\u0be7\u0be8.\u0beb\u0be6%", source_digits: "tamil", grouping: "none" } },
    ],
  },
  {
    op: "format_percent", label: "Format percent", description: "Format an exact percent value with selected digits and optional Indian grouping.",
    fields: [
      ...exactValueFields(),
      { key: "digits", label: "Output digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
      { key: "grouping", label: "Grouping", kind: "select", initial: "none", options: ["none", "indian"] },
    ],
    build: (v) => ({ op: "format_percent", input: { value: exactValueFromFields(v), digits: v.digits, grouping: v.grouping } }),
    examples: [
      { label: "12.50 percent", values: { negative: "false", coefficient: "1250", scale: "2", digits: "latin", grouping: "none" } },
      { label: "Tamil percent digits", values: { negative: "false", coefficient: "123456", scale: "2", digits: "tamil", grouping: "indian" } },
    ],
  },
  {
    op: "ratio_to_percent", label: "Ratio to percent value", description: "Multiply an exact ratio by 100 by shifting its decimal scale; no rounding is used.",
    fields: exactValueFields(),
    build: (v) => ({ op: "ratio_to_percent", input: { value: exactValueFromFields(v) } }),
    examples: [
      { label: "0.125 ratio", values: { negative: "false", coefficient: "125", scale: "3" } },
      { label: "Zero at scale 0", values: { negative: "false", coefficient: "0", scale: "0" } },
    ],
  },
  {
    op: "percent_to_ratio", label: "Percent value to ratio", description: "Divide an exact percent value by 100 by shifting its decimal scale; no rounding is used.",
    fields: exactValueFields(),
    build: (v) => ({ op: "percent_to_ratio", input: { value: exactValueFromFields(v) } }),
    examples: [
      { label: "12.5 percent", values: { negative: "false", coefficient: "125", scale: "1" } },
      { label: "Zero at scale 254", values: { negative: "false", coefficient: "0", scale: "254" } },
    ],
  },
  {
    op: "format_numeric_range", label: "Format exact numeric range", description: "Compare decimal and fraction endpoints exactly, then render an interval with explicit boundary flags.",
    fields: [
      ...numericEndpointFields("start", "decimal"),
      ...numericEndpointFields("end", "fraction"),
      { key: "start_inclusive", label: "Include start", kind: "select", initial: "true", options: ["true", "false"] },
      { key: "end_inclusive", label: "Include end", kind: "select", initial: "false", options: ["true", "false"] },
      { key: "separator", label: "Separator", kind: "text", required: true, initial: "..", help: "Use a nonempty separator of at most eight Unicode scalars." },
      { key: "digits", label: "Output digits", kind: "select", initial: "latin", options: ["latin", "tamil"] },
    ],
    build: (v) => ({ op: "format_numeric_range", input: { start: numericEndpointFromFields(v, "start"), end: numericEndpointFromFields(v, "end"), start_inclusive: v.start_inclusive === "true", end_inclusive: v.end_inclusive === "true", separator: v.separator, digits: v.digits } }),
    examples: [
      { label: "Decimal to fraction", values: { start_type: "decimal", start_negative: "false", start_coefficient: "1", start_scale: "1", end_type: "fraction", end_numerator: "1", end_denominator: "2", start_inclusive: "true", end_inclusive: "false", separator: "..", digits: "latin" } },
      { label: "Equal zero endpoints", values: { start_type: "decimal", start_negative: "false", start_coefficient: "0", start_scale: "2", end_type: "fraction", end_numerator: "0", end_denominator: "1", start_inclusive: "true", end_inclusive: "true", separator: " to ", digits: "tamil" } },
    ],
  },
  {
    op: "validate_gregorian_date", label: "Validate Gregorian date", description: "Check a date in the bounded proleptic Gregorian domain (years 1 through 9999).",
    fields: [
      { key: "year", label: "Year", kind: "number", initial: "2024" },
      { key: "month", label: "Month", kind: "number", initial: "2" },
      { key: "day", label: "Day", kind: "number", initial: "29" },
    ],
    build: (v) => ({ op: "validate_gregorian_date", input: { year: Number(v.year), month: Number(v.month), day: Number(v.day) } }),
    examples: [
      { label: "Leap day", values: { year: "2024", month: "2", day: "29" } },
      { label: "1900 is not leap", values: { year: "1900", month: "2", day: "29" } },
    ],
  },
  {
    op: "parse_gregorian_date", label: "Parse ISO date", description: "Parse exactly YYYY-MM-DD and validate the Gregorian day for that month.",
    fields: [{ key: "text", label: "ISO date", kind: "text", required: true, initial: "2000-02-29", help: "Four year digits, then two month and day digits." }],
    build: (v) => ({ op: "parse_gregorian_date", input: { text: v.text } }),
    examples: [
      { label: "Leap day", values: { text: "2000-02-29" } },
      { label: "Bad width Â· error", values: { text: "2024-2-01" } },
    ],
  },
  {
    op: "weekday", label: "Find weekday", description: "Return the stable lowercase English weekday for a validated Gregorian date.",
    fields: [
      { key: "year", label: "Year", kind: "number", initial: "2024" },
      { key: "month", label: "Month", kind: "number", initial: "1" },
      { key: "day", label: "Day", kind: "number", initial: "1" },
    ],
    build: (v) => ({ op: "weekday", input: { year: Number(v.year), month: Number(v.month), day: Number(v.day) } }),
    examples: [
      { label: "2024-01-01", values: { year: "2024", month: "1", day: "1" } },
      { label: "2024-01-07", values: { year: "2024", month: "1", day: "7" } },
    ],
  },
  {
    op: "add_gregorian_date", label: "Add to Gregorian date", description: "Add signed days, months, or years; month/year operations can reject or clamp a missing target day.",
    fields: [
      { key: "year", label: "Year", kind: "number", initial: "2024" },
      { key: "month", label: "Month", kind: "number", initial: "1" },
      { key: "day", label: "Day", kind: "number", initial: "31" },
      { key: "unit", label: "Unit", kind: "select", initial: "months", options: ["days", "months", "years"] },
      { key: "amount", label: "Amount to add", kind: "number", initial: "1" },
      { key: "overflow", label: "Missing target day", kind: "select", initial: "clamp", options: ["reject", "clamp"] },
    ],
    build: (v) => ({ op: "add_gregorian_date", input: { year: Number(v.year), month: Number(v.month), day: Number(v.day), unit: v.unit, amount: Number(v.amount), overflow: v.overflow } }),
    examples: [
      { label: "Jan 31 + one month · clamp", values: { year: "2024", month: "1", day: "31", unit: "months", amount: "1", overflow: "clamp" } },
      { label: "Leap day + one year · reject", values: { year: "2024", month: "2", day: "29", unit: "years", amount: "1", overflow: "reject" } },
      { label: "Date domain edge · error", values: { year: "1", month: "1", day: "1", unit: "days", amount: "-1", overflow: "reject" } },
    ],
  },
  {
    op: "date_difference", label: "Difference between dates", description: "Return signed civil days as end minus start.",
    fields: [
      { key: "start", label: "Start date", kind: "date", required: true, initial: "2024-02-28" },
      { key: "end", label: "End date", kind: "date", required: true, initial: "2024-03-01" },
    ],
    build: (v) => ({ op: "date_difference", input: { start: isoDateParts(v.start), end: isoDateParts(v.end) } }),
    examples: [
      { label: "Across leap day", values: { start: "2024-02-28", end: "2024-03-01" } },
      { label: "Reverse direction", values: { start: "2024-03-01", end: "2024-02-28" } },
    ],
  },
  {
    op: "date_interval", label: "Count inclusive date interval", description: "Return canonical ISO endpoints and the number of included civil days.",
    fields: [
      { key: "start", label: "First included date", kind: "date", required: true, initial: "2024-02-28" },
      { key: "end", label: "Last included date", kind: "date", required: true, initial: "2024-03-01" },
    ],
    build: (v) => ({ op: "date_interval", input: { start: v.start, end: v.end } }),
    examples: [
      { label: "Include both leap-year endpoints", values: { start: "2024-02-28", end: "2024-03-01" } },
      { label: "Reverse order Â· error", values: { start: "2024-03-02", end: "2024-03-01" } },
    ],
  },
  {
    op: "calendar_profile_info", label: "Calendar profile information", description: "Inspect either the Thirukanitham source profile or the bounded classical 1962 Vakyakarana Ujjain civil profile, including coverage, time basis and limitations.",
    fields: [{ key: "calendar_profile", label: "Calendar profile", kind: "select", initial: thirukanithamChoice, options: [thirukanithamChoice, vakyaCivilChoice] }],
    build: (v) => ({ op: "calendar_profile_info", input: { definition_id: selectedCalendarDefinition(v) } }),
  },
  {
    op: "thiruvalluvar_year_info", label: "Thiruvalluvar year · named convention", description: "Apply the TN Thai-1 year convention using the Thirukanitham profile's month-10 boundary for 2025–2027. Output marks this as a profile convention, not an official Gazette lookup; the documented 2026 Gazette conflict is included.",
    fields: [
      { key: "date", label: "Gregorian civil date", kind: "date", required: true, initial: "2025-01-14" },
      ...drikContextFields().filter((field) => field.key !== "region"),
    ],
    build: (v) => ({ op: "thiruvalluvar_year_info", input: { convention_id: "tn-thiruvalluvar-thai1-thirukanitham-v1", date: isoDateParts(v.date), context: { ...drikContext(v), region: "TN", time_zone: "Asia/Kolkata" } } }),
    examples: [
      { label: "Before 2025 profile Thai 1", values: { date: "2025-01-13", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "On 2025 profile Thai 1", values: { date: "2025-01-14", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
    ],
  },
  {
    op: "gregorian_to_tamil_date", label: "Gregorian to Tamil solar date", description: "Convert a civil date with the selected definition. Vakyakarana is bounded to the Ujjain mean-sunrise reference station; Thirukanitham uses the selected TN/SL location.",
    fields: [
      { key: "date", label: "Gregorian date", kind: "date", required: true, initial: "2026-11-01" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "gregorian_to_tamil_date", input: { definition_id: selectedCalendarDefinition(v), date: isoDateParts(v.date), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Chennai Aippasi", values: { date: "2026-11-01", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Colombo", values: { date: "2026-11-01", calendar_profile: thirukanithamChoice, region: "SL", latitude: "6.935480", longitude: "79.848680", elevation: "7" } },
      { label: "1962 Vakyakarana worked date", values: { date: "1947-10-11", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "format_tamil_date", label: "Format a Tamil solar date", description: "Format a Gregorian civil date with source-backed Tamil or Romanized month and weekday labels. Tamil and Latin digits are selected independently; the output uses a declared template without grammatical inflection.",
    fields: [
      { key: "date", label: "Gregorian date", kind: "date", required: true, initial: "2026-04-14" },
      { key: "script", label: "Display script", kind: "select", initial: "tamil", options: ["tamil", "romanized"] },
      { key: "digits", label: "Digits", kind: "select", initial: "tamil", options: ["tamil", "latin"] },
      { key: "style", label: "Format template", kind: "select", initial: "weekday_day_month_year", options: ["weekday_day_month_year", "day_month_year"] },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "format_tamil_date", input: { definition_id: selectedCalendarDefinition(v), date: isoDateParts(v.date), context: selectedCalendarContext(v), script: v.script, digits: v.digits, style: v.style } }),
    examples: [
      { label: "Chithirai 1 · Tamil digits", values: { date: "2026-04-14", script: "tamil", digits: "tamil", style: "weekday_day_month_year", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "1947 Vakyakarana · Romanized", values: { date: "1947-10-11", script: "romanized", digits: "latin", style: "weekday_day_month_year", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "calendar_display_info", label: "Calendar labels and day context", description: "Return the computed Tamil solar date, year-cycle label, weekday, and panchangam-at-sunrise labels with source and boundary metadata for the selected model and context.",
    fields: [
      { key: "date", label: "Gregorian date", kind: "date", required: true, initial: "2026-11-01" },
      { key: "script", label: "Display script", kind: "select", initial: "tamil", options: ["tamil", "romanized"] },
      { key: "digits", label: "Date digits", kind: "select", initial: "tamil", options: ["tamil", "latin"] },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "calendar_display_info", input: { definition_id: selectedCalendarDefinition(v), date: isoDateParts(v.date), context: selectedCalendarContext(v), script: v.script, digits: v.digits } }),
  },
  {
    op: "compare_calendar_profiles", label: "Compare calendar profiles", description: "Compute both named profiles for one Gregorian date or UTC instant. Contexts, day-boundary basis, and source metadata remain separate; differences do not rank accuracy.",
    fields: [
      { key: "moment", label: "Compare at", kind: "select", initial: "date", options: ["date", "instant"] },
      { key: "date", label: "Gregorian date", kind: "date", required: true, initial: "2026-04-14", visibleWhen: { key: "moment", value: "date" } },
      { key: "instant_unix_seconds", label: "UTC Unix second", kind: "number", initial: "1793514600", visibleWhen: { key: "moment", value: "instant" } },
      { key: "vakya_time_zone", label: "Vakyakarana civil label zone", kind: "select", initial: "Asia/Kolkata", options: ["Asia/Kolkata", "Asia/Colombo"] },
      ...drikContextFields(),
    ],
    build: (v) => ({ op: "compare_calendar_profiles", input: { ...(v.moment === "date" ? { date: isoDateParts(v.date) } : { instant_unix_seconds: Number(v.instant_unix_seconds) }), thirukanitham_context: drikContext(v), vakya_context: { reference_station: "ujjain", time_zone: v.vakya_time_zone } } }),
    examples: [
      { label: "2026 Chithirai boundary date", values: { moment: "date", date: "2026-04-14", region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14", vakya_time_zone: "Asia/Kolkata" } },
      { label: "Same UTC instant · reported limbs", values: { moment: "instant", instant_unix_seconds: "1793514600", region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14", vakya_time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "tamil_to_gregorian_date", label: "Tamil solar date to Gregorian", description: "Reverse-convert a month and day with the selected solar definition; invalid month days are rejected.",
    fields: [
      { key: "solar_year", label: "Solar year (Gregorian year containing Chithirai 1)", kind: "number", initial: "2026" },
      { key: "month", label: "Tamil solar month (1–12)", kind: "number", initial: "7" },
      { key: "day", label: "Day of month", kind: "number", initial: "15" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "tamil_to_gregorian_date", input: { definition_id: selectedCalendarDefinition(v), date: { solar_year: Number(v.solar_year), month: Number(v.month), day: Number(v.day) }, context: selectedCalendarContext(v) } }),
    examples: [{ label: "15 Aippasi 2026", values: { solar_year: "2026", month: "7", day: "15", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } }, { label: "24 Purattasi 1947", values: { solar_year: "1947", month: "6", day: "24", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } }],
  },
  {
    op: "tamil_month_info", label: "Tamil month boundaries (Thirukanitham)", description: "Get computed Gregorian start, exclusive end and actual length for one solar month.",
    fields: [
      { key: "solar_year", label: "Solar year", kind: "number", initial: "2026" },
      { key: "month", label: "Tamil solar month (1–12)", kind: "number", initial: "7" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "tamil_month_info", input: { definition_id: selectedCalendarDefinition(v), solar_year: Number(v.solar_year), month: Number(v.month), context: selectedCalendarContext(v) } }),
  },
  {
    op: "tamil_year_info", label: "Tamil solar year and months", description: "Enumerate all twelve contiguous Gregorian month intervals using the selected Thirukanitham or classical Vakyakarana profile.",
    fields: [
      { key: "solar_year", label: "Solar year (Gregorian year containing Chithirai 1)", kind: "number", initial: "2025" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "tamil_year_info", input: { definition_id: selectedCalendarDefinition(v), solar_year: Number(v.solar_year), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Thirukanitham · 2025", values: { solar_year: "2025", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Vakyakarana · 1947", values: { solar_year: "1947", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "tamil_year_cycle_info", label: "Tamil 60-year cycle title", description: "Return the romanized cycle name from the documented 1889 South Indian table for the selected profile's solar-year range.",
    fields: [
      { key: "solar_year", label: "Solar year (Gregorian year containing Chithirai 1)", kind: "number", initial: "2025" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "tamil_year_cycle_info", input: { definition_id: selectedCalendarDefinition(v), solar_year: Number(v.solar_year), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Thirukanitham · Krodhi", values: { solar_year: "2024", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Vakyakarana · Sarvajit", values: { solar_year: "1947", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "calendar_official_holidays", label: "Published public holiday schedule", description: "Return named holidays and the issuing authority's applicability categories for the four bundled annual schedules. Unlisted jurisdiction/year pairs return an explicit unavailable error.",
    fields: [
      { key: "jurisdiction", label: "Jurisdiction", kind: "select", initial: "TN", options: ["TN", "SL"] },
      { key: "year", label: "Published schedule year", kind: "number", initial: "2025" },
    ],
    build: (v) => ({ op: "calendar_official_holidays", input: { jurisdiction: v.jurisdiction, year: Number(v.year) } }),
    examples: [
      { label: "Tamil Nadu · 2025", values: { jurisdiction: "TN", year: "2025" } },
      { label: "Sri Lanka · 2027", values: { jurisdiction: "SL", year: "2027" } },
    ],
  },
  {
    op: "calendar_observances", label: "Tamil observances · sourced subset", description: "Calculate the named Thirukanitham Tamil Nadu solar, lunar, and Sri Vaishnava Arunodaya observances. Enter a month to return a separately scoped monthly result. Publisher-equivalent dates are not claimed; Vakiya and Sri Lanka are unsupported.",
    fields: [
      { key: "gregorian_year", label: "Gregorian year (2025–2027)", kind: "number", initial: "2026" },
      { key: "month", label: "Month 1–12 (optional)", kind: "text", initial: "" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "calendar_observances", input: { definition_id: selectedCalendarDefinition(v), rule_set: "thirukanitham-tamil-named-observances-v1", gregorian_year: Number(v.gregorian_year), ...(v.month.trim() ? { month: Number(v.month) } : {}), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Chennai · 2026", values: { gregorian_year: "2026", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Vakiya · explicitly unsupported", values: { gregorian_year: "2026", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "add_tamil_date", label: "Add to a Tamil solar date", description: "Add days, months, or years within the selected definition. Month and year overflow can reject or clamp to the target month's last day.",
    fields: [
      { key: "solar_year", label: "Solar year", kind: "number", initial: "2025" },
      { key: "month", label: "Tamil solar month (1–12)", kind: "number", initial: "1" },
      { key: "day", label: "Day of month", kind: "number", initial: "1" },
      { key: "unit", label: "Unit", kind: "select", initial: "days", options: ["days", "months", "years"] },
      { key: "amount", label: "Signed amount", kind: "number", initial: "1" },
      { key: "overflow", label: "Month-day overflow", kind: "select", initial: "reject", options: ["reject", "clamp"], help: "Used when adding months or years targets a shorter month." },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "add_tamil_date", input: { definition_id: selectedCalendarDefinition(v), date: { solar_year: Number(v.solar_year), month: Number(v.month), day: Number(v.day) }, unit: v.unit, amount: Number(v.amount), overflow: v.overflow, context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Thirukanitham · next day", values: { solar_year: "2025", month: "1", day: "1", unit: "days", amount: "1", overflow: "reject", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Vakyakarana · Purattasi next day", values: { solar_year: "1947", month: "6", day: "24", unit: "days", amount: "1", overflow: "reject", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "lunar_phase_events", label: "Primary lunar phase events (Thirukanitham)", description: "List new moon, first quarter, full moon and last quarter roots in a bounded UTC interval. The source model is geocentric and these instants do not depend on observer location.",
    fields: [
      { key: "start_date", label: "Start date (UTC, inclusive)", kind: "date", required: true, initial: "2025-01-06" },
      { key: "end_date_exclusive", label: "End date (UTC, exclusive)", kind: "date", required: true, initial: "2025-01-30" },
    ],
    build: (v) => ({ op: "lunar_phase_events", input: { definition_id: thirukanithamDefinition, start_unix_seconds: utcDateStartUnix(v.start_date), end_unix_seconds: utcDateStartUnix(v.end_date_exclusive) } }),
    examples: [{ label: "USNO January 2025 phases", values: { start_date: "2025-01-06", end_date_exclusive: "2025-01-30" } }],
  },
  {
    op: "calendar_daylight_periods", label: "Rahu, Yamagandam and Kuligai", description: "Divide the selected Thirukanitham profile's computed sunrise-to-sunset daylight into eight equal parts and apply the sourced weekday slots. Vakiya sunset is unavailable in its source-bounded civil profile.",
    fields: [
      { key: "date", label: "Local civil date", kind: "date", required: true, initial: "2026-11-01" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "calendar_daylight_periods", input: { definition_id: selectedCalendarDefinition(v), date: isoDateParts(v.date), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Chennai · Sunday", values: { date: "2026-11-01", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Ujjain · source sunset unavailable", values: { date: "1947-10-11", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "panchangam_at", label: "Five limbs at a local time (Thirukanitham)", description: "Enter a local civil time; it is converted using the profile's pinned UTC+05:30 zone rules. Returns tithi, vara, nakshatra, yoga and karana.",
    fields: [
      { key: "local_date", label: "Local date", kind: "date", required: true, initial: "2026-11-01" },
      { key: "local_time", label: "Local time (24-hour)", kind: "text", required: true, initial: "12:00", help: "HH:MM or HH:MM:SS, interpreted in the selected region's time zone." },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "panchangam_at", input: { definition_id: selectedCalendarDefinition(v), instant_unix_seconds: drikLocalInstant(v), context: selectedCalendarContext(v) } }),
    examples: [{ label: "Chennai noon", values: { local_date: "2026-11-01", local_time: "12:00", calendar_profile: thirukanithamChoice, region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } }, { label: "Ujjain mean sunrise · source limbs", values: { local_date: "1947-10-11", local_time: "06:26:52", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } }],
  },
  {
    op: "panchangam_day", label: "Panchangam civil day", description: "Return source-defined sunrise basis, five limbs and transitions. Vakyakarana v1 reports Ujjain mean sunrise and leaves true local sunset unavailable until its Bhujaantara interpolation is established.",
    fields: [
      { key: "date", label: "Local civil date", kind: "date", required: true, initial: "2026-11-01" },
      ...calendarContextFields(),
    ],
    build: (v) => ({ op: "panchangam_day", input: { definition_id: selectedCalendarDefinition(v), date: isoDateParts(v.date), context: selectedCalendarContext(v) } }),
    examples: [
      { label: "Chennai · 2026-11-01", values: { date: "2026-11-01", region: "TN", latitude: "13.087840", longitude: "80.278470", elevation: "14" } },
      { label: "Colombo · 2026-11-01", values: { date: "2026-11-01", calendar_profile: thirukanithamChoice, region: "SL", latitude: "6.935480", longitude: "79.848680", elevation: "7" } },
      { label: "Ujjain mean-sunrise day · 1947", values: { date: "1947-10-11", calendar_profile: vakyaCivilChoice, time_zone: "Asia/Kolkata" } },
    ],
  },
  {
    op: "vakya_solar_transits", label: "Vakyakarana solar transits", description: "Source-pinned 1962 edition arithmetic for Saka 1869–1890. Returns Kali ahargana and twelve annual solar-vakya residuals; it does not assign Gregorian month dates or represent a current publisher edition.",
    fields: [
      { key: "saka_year_elapsed", label: "Elapsed Saka year", kind: "number", initial: "1890", help: "Supported range: 1869–1890 inclusive." },
    ],
    build: (v) => ({ op: "vakya_solar_transits", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", saka_year_elapsed: Number(v.saka_year_elapsed) } }),
    examples: [
      { label: "1962 edition worked year", values: { saka_year_elapsed: "1869" } },
      { label: "2019 article comparison year", values: { saka_year_elapsed: "1890" } },
      { label: "Outside evidence window · error", values: { saka_year_elapsed: "1891" } },
    ],
  },
  {
    op: "vakya_true_sun_from_mesha_elapsed", label: "Vakyakarana true Sun from Mesha", description: "Interpolate the 1962 Bhupadi correction table for elapsed days, nāḍi and vināḍi from Mesha Saṅkramaṇa. Returns approximate Sun, correction and true Sun; a caller must supply the elapsed interval.",
    fields: [
      { key: "elapsed_days", label: "Elapsed days", kind: "number", initial: "180", help: "Table coverage: 0–370 days; day 370 accepts no additional time." },
      { key: "nadi", label: "Nāḍi", kind: "number", initial: "19", help: "Integer from 0 to 59." },
      { key: "vinadi", label: "Vināḍi", kind: "number", initial: "41", help: "Integer from 0 to 59." },
    ],
    build: (v) => ({ op: "vakya_true_sun_from_mesha_elapsed", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", elapsed_days: Number(v.elapsed_days), nadi: Number(v.nadi), vinadi: Number(v.vinadi) } }),
    examples: [
      { label: "Printed worked example", values: { elapsed_days: "180", nadi: "19", vinadi: "41" } },
      { label: "Mesha origin", values: { elapsed_days: "0", nadi: "0", vinadi: "0" } },
      { label: "Beyond correction table · error", values: { elapsed_days: "371", nadi: "0", vinadi: "0" } },
    ],
  },
  {
    op: "vakya_true_moon_from_kali_day", label: "Vakyakarana true Moon", description: "Apply the 1962 Candra-vakya table and correction for a Kali day. Returns the source-profile lunar longitude and calculation terms; it does not assign a Gregorian date or local sunrise.",
    fields: [
      { key: "kali_day", label: "Kali day", kind: "number", initial: "1844004", help: "Supported from Kali day 1,600,984." },
    ],
    build: (v) => ({ op: "vakya_true_moon_from_kali_day", input: { definition_id: "vakyakarana-1962-laghuprakashika-true-moon-v1", kali_day: Number(v.kali_day) } }),
    examples: [
      { label: "Printed worked example", values: { kali_day: "1844004" } },
      { label: "248-day cycle boundary", values: { kali_day: "1601232" } },
      { label: "Before supported epoch · error", values: { kali_day: "1600983" } },
    ],
  },
  {
    op: "vakya_reduce_to_local_true_sunrise", label: "Vakyakarana local sunrise reduction", description: "Apply the 1962 local true-sunrise correction to a supplied true longitude and daily motion. Supply already derived half-Cara, Deśāntara and Bhujaantara terms in tenths of a vināḍi; this form does not calculate sunrise or infer those terms from a location.",
    fields: [
      { key: "rasi", label: "True longitude rasi", kind: "number", initial: "4", help: "Integer 0–11." },
      { key: "degrees", label: "True longitude degrees within rasi", kind: "number", initial: "11", help: "Integer 0–29." },
      { key: "minutes", label: "True longitude minutes", kind: "number", initial: "17", help: "Integer 0–59." },
      { key: "seconds", label: "True longitude seconds", kind: "number", initial: "32", help: "Integer 0–59." },
      { key: "motion_degrees", label: "Daily motion degrees", kind: "number", initial: "14", help: "Integer 0–359." },
      { key: "motion_minutes", label: "Daily motion minutes", kind: "number", initial: "12", help: "Integer 0–59." },
      { key: "motion_seconds", label: "Daily motion seconds", kind: "number", initial: "0", help: "Integer 0–59." },
      { key: "cara", label: "Half-Cara (tenths of vināḍi)", kind: "number", initial: "130" },
      { key: "desantara", label: "Deśāntara (tenths of vināḍi)", kind: "number", initial: "-266" },
      { key: "bhujaantara", label: "Bhujaantara (tenths of vināḍi)", kind: "number", initial: "-210" },
    ],
    build: (v) => ({ op: "vakya_reduce_to_local_true_sunrise", input: { definition_id: "vakyakarana-1962-laghuprakashika-local-sunrise-v1", true_position: { rasi: Number(v.rasi), degrees: Number(v.degrees), minutes: Number(v.minutes), seconds: Number(v.seconds) }, daily_motion: { degrees: Number(v.motion_degrees), minutes: Number(v.motion_minutes), seconds: Number(v.motion_seconds) }, cara_half_vinadi_tenths: Number(v.cara), desantara_vinadi_tenths: Number(v.desantara), bhujaantara_vinadi_tenths: Number(v.bhujaantara) } }),
    examples: [
      { label: "Printed Moon example", values: { rasi: "4", degrees: "11", minutes: "17", seconds: "32", motion_degrees: "14", motion_minutes: "12", motion_seconds: "0", cara: "130", desantara: "-266", bhujaantara: "-210" } },
      { label: "No local-time correction", values: { rasi: "4", degrees: "11", minutes: "17", seconds: "32", motion_degrees: "14", motion_minutes: "12", motion_seconds: "0", cara: "0", desantara: "0", bhujaantara: "0" } },
    ],
  },
  {
    op: "vakya_cara_from_sayana_sun", label: "Vakyakarana Cara interval", description: "Compute the 1962 Cara interval from a supplied Sayana Sun and the place's equinoctial shadow. The form does not derive precession, solar longitude or observer shadow from a civil date or coordinates.",
    fields: [
      { key: "rasi", label: "Sayana Sun rasi", kind: "number", initial: "4", help: "Integer 0–11." },
      { key: "degrees", label: "Sayana Sun degrees within rasi", kind: "number", initial: "22", help: "Integer 0–29." },
      { key: "minutes", label: "Sayana Sun minutes", kind: "number", initial: "30", help: "Integer 0–59." },
      { key: "seconds", label: "Sayana Sun seconds", kind: "number", initial: "0", help: "Integer 0–59." },
      { key: "shadow", label: "Equinoctial shadow (tenths of angula)", kind: "number", initial: "30", help: "Nonnegative integer; 30 means 3.0 angulas." },
    ],
    build: (v) => ({ op: "vakya_cara_from_sayana_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-cara-v1", sayana_sun: { rasi: Number(v.rasi), degrees: Number(v.degrees), minutes: Number(v.minutes), seconds: Number(v.seconds) }, equinoctial_shadow_tenths: Number(v.shadow) } }),
    examples: [
      { label: "Printed Example 20", values: { rasi: "4", degrees: "22", minutes: "30", seconds: "0", shadow: "30" } },
      { label: "Opposite half-circle sign", values: { rasi: "10", degrees: "22", minutes: "30", seconds: "0", shadow: "30" } },
      { label: "Negative shadow · error", values: { rasi: "4", degrees: "22", minutes: "30", seconds: "0", shadow: "-1" } },
    ],
  },
  {
    op: "vakya_desantara_from_yojana_distance", label: "Vakyakarana Deśāntara", description: "Convert a supplied east/west yojana distance from Ujjain into tenths of a vināḍi. Positive distance means east; the returned correction is negative east and positive west. Geographic coordinates are not converted to yojanas.",
    fields: [
      { key: "distance", label: "East/west distance (tenths of yojana)", kind: "number", initial: "244", help: "Positive east of Ujjain; negative west. 244 means 24.4 yojanas." },
    ],
    build: (v) => ({ op: "vakya_desantara_from_yojana_distance", input: { definition_id: "vakyakarana-1962-laghuprakashika-desantara-v1", east_west_distance_tenths_yojana: Number(v.distance) } }),
    examples: [
      { label: "Printed Pudukkottai distance", values: { distance: "244" } },
      { label: "West of Ujjain", values: { distance: "-244" } },
      { label: "Ujjain reference", values: { distance: "0" } },
    ],
  },
  {
    op: "vakya_bhujaantara_from_true_sun", label: "Vakyakarana Bhujaantara (experimental)", description: "Apply an experimental longitude-linear interpolation convention to the 1962 Bhujaantara endpoint table. The edition does not specify the interpolation parameter or equation, and this form does not derive the position from a civil date.",
    fields: [
      { key: "rasi", label: "Zero-based Sun rasi (0 = Mesha, 5 = Kanya)", kind: "number", initial: "5", help: "Integer 0–11, following the 1962 Vakiya rasi count." },
      { key: "progress", label: "Progress in rasi (arcseconds)", kind: "number", initial: "84513", help: "Integer 0–108000; 108000 arcseconds is 30 degrees." },
    ],
    build: (v) => ({ op: "vakya_bhujaantara_from_true_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1", sun_rasi: Number(v.rasi), sun_rasi_progress_arcseconds: Number(v.progress) } }),
    examples: [
      { label: "Printed Kanya example", values: { rasi: "5", progress: "84513" } },
      { label: "Mesha midpoint (experimental)", values: { rasi: "0", progress: "54000" } },
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
  {
    op: "lt_tm_codes_to_unicode", label: "LT-TM codes to Unicode", description: "Decode 16-bit LT-TM / IndoWord character codes from a selected font run.",
    fields: [
      { key: "codes", label: "16-bit codes (hex)", kind: "text", initial: "0062 006A 0068 0161 0066 0068 00A5 00E3 0061 00AB", help: "Enter one to four hexadecimal digits per code, separated by spaces. These are 16-bit codes, not bytes." },
      { key: "errors", label: "Unknown input", kind: "select", initial: "strict", options: ["strict", "preserve"] },
    ],
    build: (v) => ({ op: "lt_tm_codes_to_unicode", input: { codes: parseHexCodes(v.codes), errors: v.errors } }),
    examples: [
      { label: "TVA PDF title run", values: { codes: "0062 006A 0068 0161 0066 0068 00A5 00E3 0061 00AB", errors: "strict" } },
      { label: "Preserve unmapped ASCII x", values: { codes: "0078", errors: "preserve" } },
    ],
  },
  {
    op: "lt_tm_text_to_unicode", label: "LT-TM legacy text to Unicode", description: "Decode BMP code-valued text already extracted from an LT-TM / IndoWord font run.",
    fields: [
      { key: "text", label: "LT-TM code-valued text", kind: "textarea", initial: "\u0062\u006a\u0068\u0161\u0066\u0068\u00a5\u00e3\u0061\u00ab", help: "Paste legacy text with its original code-valued characters. This is not a byte decoder or Windows-1252 conversion." },
      { key: "errors", label: "Unknown input", kind: "select", initial: "strict", options: ["strict", "preserve"] },
    ],
    build: (v) => ({ op: "lt_tm_text_to_unicode", input: { text: v.text, errors: v.errors } }),
    examples: [
      { label: "TVA PDF title run", values: { text: "\u0062\u006a\u0068\u0161\u0066\u0068\u00a5\u00e3\u0061\u00ab", errors: "strict" } },
      { label: "Preserve unmapped ASCII x", values: { text: "\u0078", errors: "preserve" } },
    ],
  },
  {
    op: "unicode_to_lt_tm_codes", label: "Unicode to LT-TM codes", description: "Encode Unicode Tamil to 16-bit LT-TM / IndoWord character codes.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported or non-round-trippable input returns an error. Output is an array of hexadecimal code values in the raw JSON panel." }],
    build: (v) => ({ op: "unicode_to_lt_tm_codes", input: { text: v.text } }),
    examples: [{ label: "Sample Tamil word", values: { text: demoTamil } }],
  },
  {
    op: "unicode_to_lt_tm_text", label: "Unicode to LT-TM legacy text", description: "Encode Unicode Tamil to text containing LT-TM / IndoWord code-valued characters.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "The result contains legacy code-valued characters; use the raw JSON panel to inspect its scalars." }],
    build: (v) => ({ op: "unicode_to_lt_tm_text", input: { text: v.text } }),
    examples: [{ label: "Sample Tamil word", values: { text: demoTamil } }],
  },
  {
    op: "vanavil_codes_to_unicode", label: "Vanavil codes to Unicode", description: "Decode 16-bit Vanavil Avvaiyar character codes from a selected font run.",
    fields: [
      { key: "codes", label: "16-bit codes (hex)", kind: "text", initial: "00C4 00E4", help: "Enter one to four hexadecimal digits per code, separated by spaces. These are 16-bit codes, not bytes." },
      { key: "errors", label: "Unknown input", kind: "select", initial: "strict", options: ["strict", "preserve"] },
    ],
    build: (v) => ({ op: "vanavil_codes_to_unicode", input: { codes: parseHexCodes(v.codes), errors: v.errors } }),
    examples: [
      { label: "Distinguish 00C4 / 00E4", values: { codes: "00C4 00E4", errors: "strict" } },
      { label: "Preserve unmapped ASCII x", values: { codes: "0078", errors: "preserve" } },
    ],
  },
  {
    op: "vanavil_text_to_unicode", label: "Vanavil legacy text to Unicode", description: "Decode BMP code-valued text already extracted from a Vanavil Avvaiyar font run.",
    fields: [
      { key: "text", label: "Vanavil code-valued text", kind: "textarea", initial: "\u00c4\u00e4", help: "Paste legacy text with its original code-valued characters. This is not a byte decoder." },
      { key: "errors", label: "Unknown input", kind: "select", initial: "strict", options: ["strict", "preserve"] },
    ],
    build: (v) => ({ op: "vanavil_text_to_unicode", input: { text: v.text, errors: v.errors } }),
    examples: [
      { label: "Distinguish Ä / ä", values: { text: "\u00c4\u00e4", errors: "strict" } },
      { label: "Preserve unmapped ASCII x", values: { text: "\u0078", errors: "preserve" } },
    ],
  },
  {
    op: "unicode_to_vanavil_codes", label: "Unicode to Vanavil codes", description: "Encode Unicode Tamil to 16-bit Vanavil Avvaiyar character codes.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "Unsupported or non-round-trippable input returns an error. Output is an array of hexadecimal code values in the raw JSON panel." }],
    build: (v) => ({ op: "unicode_to_vanavil_codes", input: { text: v.text } }),
    examples: [
      { label: "Sample Tamil word", values: { text: demoTamil } },
      { label: "Vanavil 00C4 / 00E4 contrast", values: { text: "\u0bb2\u0bc0\u0bae\u0bbf" } },
    ],
  },
  {
    op: "unicode_to_vanavil_text", label: "Unicode to Vanavil legacy text", description: "Encode Unicode Tamil to text containing Vanavil Avvaiyar code-valued characters.",
    fields: [{ key: "text", label: "Unicode Tamil text", kind: "textarea", initial: demoTamil, help: "The result contains legacy code-valued characters; use the raw JSON panel to inspect its scalars." }],
    build: (v) => ({ op: "unicode_to_vanavil_text", input: { text: v.text } }),
    examples: [{ label: "Sample Tamil word", values: { text: demoTamil } }],
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
  } else if (info.id === "tamil-calendar" && (suites.get("calendar_vakya_solar.jsonl")?.status === "planned" || suites.get("calendar_thirukanitham.jsonl")?.status === "planned")) {
    const note = document.createElement("div");
    note.className = "planned-note";
    note.textContent = "Choose Thirukanitham or the unmodified 1962 Vakyakarana Ujjain mean-sunrise civil profile in the date and panchangam forms. Vakyakarana arbitrary-location corrections and true local horizon sunrise remain unavailable pending source evidence; both calendar suites remain planned for separate owner review.";
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
    control.dataset.required = String(field.kind === "number" || field.required === true);
    control.value = field.initial;
    control.required = field.kind === "number" || field.required === true;
    if (field.visibleWhen) {
      wrapper.dataset.visibleWhenKey = field.visibleWhen.key;
      wrapper.dataset.visibleWhenValue = field.visibleWhen.value;
    }
    wrapper.append(title, control);
    if (field.help) {
      const help = document.createElement("small");
      help.className = "manual-field-help";
      help.textContent = field.help;
      wrapper.append(help);
    }
    manualFields.append(wrapper);
  }
  refreshConditionalFields();

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

function refreshConditionalFields() {
  const values = readManualValues();
  for (const wrapper of manualFields.querySelectorAll<HTMLLabelElement>(".manual-field[data-visible-when-key]")) {
    const key = wrapper.dataset.visibleWhenKey!;
    const visible = values[key] === wrapper.dataset.visibleWhenValue;
    const control = wrapper.querySelector<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("[data-field]");
    wrapper.hidden = !visible;
    if (control) {
      control.disabled = !visible;
      control.required = visible && control.dataset.required === "true";
    }
  }
}

function selectPackage(id: string) {
  if (id === selectedId) return;
  selectedId = id;
  const defaultOperation = id === "tamil-numerals" ? "format_fraction" : id === "tamil-calendar" ? "gregorian_to_tamil_date" : undefined;
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
manualFields.addEventListener("change", () => {
  refreshConditionalFields();
  scheduleManualRun();
});

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
