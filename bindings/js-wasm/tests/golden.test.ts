import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { join } from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import { execute, type Request, type Currency, type Locale, type CodecErrorPolicy, type DigitStyle, type DateStyle, type LexiconLookupOptions, type LexiconLookupResponse, type LexiconPackInfo } from "../src/index.js";
import { init, execute as executeWeb } from "../src/web.js";
import * as nodeApi from "../src/index.js";
import * as webApi from "../src/web.js";

type LexiconProfile = "default" | "core" | "full";
type PackId = "core" | "names_taxa" | "regional";

function inferCompiledProfile(packs: LexiconPackInfo[], targetLabel: string): LexiconProfile {
  if (packs.length === 0) return "default";
  if (packs.length === 1 && packs[0].id === "core" && packs[0].available === true) return "core";
  if (
    packs.length === 3 &&
    JSON.stringify(packs.map((pack) => pack.id)) === JSON.stringify(["core", "names_taxa", "regional"]) &&
    packs.every((pack) => pack.available === true)
  ) {
    return "full";
  }
  throw new Error(`Unsupported compiled ${targetLabel} lexicon packs: ${JSON.stringify(packs)}`);
}

const compiledProfile = inferCompiledProfile(nodeApi.lexicon_packs(), "Node WASM");
const envProfile = process.env.TAMIL_LEXICON_PROFILE;
if (envProfile !== undefined) {
  if (envProfile !== "default" && envProfile !== "core" && envProfile !== "full") {
    throw new Error(`Unsupported TAMIL_LEXICON_PROFILE=${envProfile} (expected 'default', 'core', or 'full')`);
  }
  if (envProfile !== compiledProfile) {
    throw new Error(
      `TAMIL_LEXICON_PROFILE=${envProfile} does not match compiled Node WASM profile ${compiledProfile}`,
    );
  }
}
const activeProfile: LexiconProfile = (envProfile as LexiconProfile | undefined) ?? compiledProfile;

beforeAll(async () => {
  const bytes = readFileSync(new URL("../pkg-web/tamil_toolkit_bg.wasm", import.meta.url));
  await init({ module_or_path: bytes });
  const webCompiledProfile = inferCompiledProfile(webApi.lexicon_packs(), "Web WASM");
  if (webCompiledProfile !== activeProfile) {
    throw new Error(
      `Web WASM compiled profile ${webCompiledProfile} does not match expected profile ${activeProfile}`,
    );
  }
});

const root = fileURLToPath(new URL("../../../tests/golden/", import.meta.url));
const manifest = JSON.parse(readFileSync(join(root, "manifest.json"), "utf8"));
if (manifest.version !== 1) throw new Error("Unsupported golden manifest");
const includePlanned = new Set((process.env.TAMIL_GOLDEN_INCLUDE_PLANNED ?? "").split(",").map((name) => name.trim()).filter(Boolean));
const ids = new Set<string>();
const files = new Set<string>();
const cases: (Request & { id: string; expected?: unknown; expected_error?: string })[] = [];
let activeCount = 0;
let plannedReviewCount = 0;
let coreProfileCount = 0;
let fullProfileCount = 0;
let hasDeclaredFull = false;
let excludedProfileCount = 0;
for (const suite of manifest.suites) {
  if (files.has(suite.file)) throw new Error(`Duplicate suite: ${suite.file}`);
  files.add(suite.file);
  if (!["active", "planned"].includes(suite.status)) throw new Error("Unknown suite status");
  const requiredProfile: string | undefined = suite.required_profile;
  if (requiredProfile !== undefined && requiredProfile !== "default" && requiredProfile !== "core" && requiredProfile !== "full") {
    throw new Error(`Invalid required_profile ${requiredProfile} in ${suite.file}`);
  }
  if (suite.status === "active" && requiredProfile === "full") {
    hasDeclaredFull = true;
  }
  const text = readFileSync(join(root, suite.file), "utf8").trim();
  const rows = text ? text.split(/\r?\n/).map((line) => JSON.parse(line)) : [];
  for (const row of rows) {
    if (ids.has(row.id)) throw new Error(`Duplicate id: ${row.id}`);
    ids.add(row.id);
  }
  if (suite.status === "active") {
    if (!rows.length) throw new Error(`Empty active suite: ${suite.file}`);
    if (requiredProfile !== undefined && requiredProfile !== activeProfile) {
      excludedProfileCount += rows.length;
      console.info(
        `PROFILE_EXCLUDED ${suite.file}: requires profile '${requiredProfile}' (active profile '${activeProfile}'; ${rows.length} vectors excluded)`,
      );
      continue;
    }
    for (const row of rows) {
      if (!suite.operations.includes(row.op)) throw new Error(`Undeclared operation: ${row.op}`);
      if (Number("expected" in row) + Number("expected_error" in row) !== 1) throw new Error(`Invalid outcome: ${row.id}`);
      if ("expected_error" in row && (typeof row.expected_error !== "string" || !row.expected_error)) throw new Error(`Invalid error: ${row.id}`);
      cases.push(row);
    }
    activeCount += rows.length;
    if (requiredProfile === "core") coreProfileCount += rows.length;
    else if (requiredProfile === "full") fullProfileCount += rows.length;
  } else if (includePlanned.has(suite.file)) {
    if (requiredProfile !== undefined && requiredProfile !== activeProfile) {
      throw new Error(`Planned suite ${suite.file} requires profile '${requiredProfile}', cannot run under '${activeProfile}'`);
    }
    for (const row of rows) {
      if (!suite.operations.includes(row.op)) throw new Error(`Undeclared operation: ${row.op}`);
      if (Number("expected" in row) + Number("expected_error" in row) !== 1) throw new Error(`Invalid outcome: ${row.id}`);
      if ("expected_error" in row && (typeof row.expected_error !== "string" || !row.expected_error)) throw new Error(`Invalid error: ${row.id}`);
      cases.push(row);
    }
    plannedReviewCount += rows.length;
    if (requiredProfile === "core") coreProfileCount += rows.length;
    else if (requiredProfile === "full") fullProfileCount += rows.length;
  } else console.info(`PLANNED ${suite.file}: ${suite.reason}`);
}
const onDisk = readdirSync(root).filter((name) => name.endsWith(".jsonl")).sort();
if (JSON.stringify([...files].sort()) !== JSON.stringify(onDisk)) throw new Error("Unregistered golden suite");
if (!cases.length) throw new Error("No active golden vectors");
if (activeProfile === "core") {
  if (coreProfileCount === 0) {
    throw new Error("Selected 'core' profile must execute required_profile='core' active golden vectors");
  }
  if (excludedProfileCount !== 0) {
    throw new Error(`Selected 'core' profile unexpectedly excluded ${excludedProfileCount} active vectors`);
  }
} else if (activeProfile === "full" && hasDeclaredFull && fullProfileCount === 0) {
  throw new Error("Selected 'full' profile must execute required_profile='full' active golden vectors");
}
console.info(
  `WASM selected ${activeCount} active golden vectors for profile '${activeProfile}' (excluded ${excludedProfileCount} active vectors requiring other profiles).`,
);
if (plannedReviewCount > 0) console.info(`PRE-ACTIVATION REVIEW executed ${plannedReviewCount} selected planned vectors; they are not active parity coverage.`);

describe("shared golden vectors through real WASM", () => {
  for (const row of cases) test(row.id, () => {
    for (const invoke of [execute, executeWeb]) {
      if ("expected_error" in row) {
        let failure: unknown;
        try { invoke(vectorRequest(row)); } catch (error) { failure = error; }
        expect(failure).toBeInstanceOf(Error);
        expect((failure as Error).message).toBe(row.expected_error);
      } else {
        expect(invoke(vectorRequest(row))).toEqual(row.expected);
      }
    }
  }, row.op === "calendar_observances" ? 30_000 : undefined);
});
test("unsupported operations and invalid inputs throw across WASM", () => {
  expect(() => execute({ op: "unknown", input: "" })).toThrow();
  expect(() => execute({ op: "get_letters", input: 1 })).toThrow();
});

test("collation convenience APIs on both WASM targets", () => {
  const words = cases.find((row) => row.id === "collate_words_basic")!;
  const key = cases.find((row) => row.id === "collate_key_001")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.sort_words(words.input as string[])).toEqual(words.expected);
    expect(api.sort_key(key.input as string)).toEqual(key.expected);
    expect(api.search_key(key.input as string)).toEqual(key.expected);
    expect(api.compare(key.input as string, key.input as string)).toBe(0);
  }
});

test("numeral convenience APIs on both WASM targets", () => {
  const number = cases.find((row) => row.id === "num_014")!;
  const defaultNumber = cases.find((row) => row.id === "number_default_locale")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.to_words(1025, "SL")).toBe(number.expected);
    expect(api.to_words(100000)).toBe(defaultNumber.expected);
    for (const row of cases) {
      if ((row.op === "format_currency" || row.op === "currency_to_words") && "expected" in row) {
        const input = row.input as { amount_minor: number; currency: Currency; locale?: Locale };
        expect(api[row.op](input.amount_minor, input.currency, input.locale)).toBe(row.expected);
      }
    }
    expect(() => api.format_currency(1, "ZZZ" as Currency)).toThrow("unsupported currency");
  }
});

test("v0.3 typed numeral and civil APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const decimal = api.parse_decimal("12.3400", "latin");
    expect(decimal).toEqual({ negative: false, coefficient: "123400", scale: 4 });
    expect(api.format_decimal(decimal)).toBe("12.3400");
    expect(api.decimal_to_words("12.03", "latin").endsWith("\u0baa\u0bc1\u0bb3\u0bcd\u0bb3\u0bbf \u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd \u0bae\u0bc2\u0ba9\u0bcd\u0bb1\u0bc1")).toBe(true);
    expect(api.ordinal_to_words(21)).toBe(cases.find((row) => row.id === "n3_ordinal_21_tn")!.expected);
    expect(api.digit_sequence_to_words("0071", "latin").startsWith("\u0baa\u0bc2\u0b9c\u0bcd\u0baf\u0bae\u0bcd")).toBe(true);
    expect(api.format_currency_decimal("123.45", "latin", "LKR")).toBe("LKR 123.45");
    expect(api.parse_fraction_symbol("-\u{11fd1}")).toEqual({ numerator: -1, denominator: 2 });
    expect(api.symbol_info("\u{11fd1}").canonical_alternative).toBe(73681);
    expect(api.format_mixed_fraction({ negative: false, whole: 5, numerator: 2, denominator: 4 })).toBe("5 1/2");
    expect(api.parse_mixed_fraction("5 1/2", "latin")).toEqual({ negative: false, whole: 5, numerator: 1, denominator: 2 });
    expect(api.mixed_fraction_to_words({ negative: false, whole: 1, numerator: 1, denominator: 2 })).toBe("\u0b92\u0ba9\u0bcd\u0bb1\u0bb0\u0bc8");
    expect(api.words_to_number(api.to_words(100001, "SL"), "SL")).toBe(100001);
    expect(api.format_currency(10000021, "SGD")).toBe("SGD 100,000.21");
    const traditional = api.format_traditional_integer(1234567);
    expect(api.parse_traditional_integer(traditional)).toBe(1234567);
    expect(api.parse_percent("12.50%", "latin")).toEqual({ negative: false, coefficient: "1250", scale: 2 });
    expect(api.ratio_to_percent({ negative: false, coefficient: "125", scale: 3 })).toEqual({ negative: false, coefficient: "125", scale: 1 });
    expect(api.format_numeric_range({ type: "fraction", numerator: 1, denominator: 4 }, { type: "decimal", value: { negative: false, coefficient: "5", scale: 0 } }, false, true, " to ")).toBe("(1/4 to 5]");
    expect(api.weekday(2024, 1, 1)).toBe("monday");
    expect(api.add_gregorian_date(2024, 1, 31, "months", 1, "clamp")).toEqual({ year: 2024, month: 2, day: 29 });
    expect(api.date_difference({ year: 2024, month: 2, day: 28 }, { year: 2024, month: 3, day: 1 })).toBe(2);
    expect(api.date_interval("2024-02-28", "2024-03-01").inclusive_days).toBe(3);
  }
});

test("historical Vakyakarana solar APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const year = api.vakya_solar_transits(1890);
    expect(year.ahargana).toEqual({ days: 1851494, nadi: 6, vinadi: 15, weekday: "Saturday" });
    expect(year.transits[0]).toEqual({ rasi: "vrishabha", day_field: 4, weekday: "Tuesday", nadi: 1, vinadi: 47 });
    const sun = api.vakya_true_sun_from_mesha_elapsed(180, 19, 41);
    expect(sun.true_sun).toEqual({ degrees: 173, minutes: 28, seconds: 33 });
  }
});

test("codec convenience API on both WASM targets", () => {
  const word = cases.find((row) => row.id === "codec_word_000_tn_strict")!;
  const preserved = cases.find((row) => row.id === "codec_joiner_boundary_0")!;
  for (const api of [nodeApi, webApi]) {
    expect(api.bamini_to_unicode((word.input as { text: string }).text)).toBe(word.expected);
    const input = preserved.input as { text: string; errors: CodecErrorPolicy };
    expect(api.bamini_to_unicode(input.text, input.errors)).toBe(preserved.expected);
    expect(() => api.bamini_to_unicode("*")).toThrow("ambiguous Bamini sequence");
    expect(() => api.bamini_to_unicode("f", "ignore" as CodecErrorPolicy)).toThrow("unsupported codec error policy");
  }
});

test("encoder convenience API on both WASM targets", () => {
  const word = cases.find((row) => row.id === "encode_word_000_tn")!;
  const nfd = cases.find((row) => row.id.startsWith("encode_mapping_") && row.id.endsWith("_tn_nfd"))!;
  const collision = cases.find((row) => row.id === "encode_collision_000_tn")!;
  for (const api of [nodeApi, webApi]) {
    const text = (word.input as { text: string }).text;
    const encoded = api.unicode_to_bamini(text);
    expect(encoded).toBe(word.expected);
    expect(api.bamini_to_unicode(encoded)).toBe(api.normalize_nfc(text));
    expect(api.unicode_to_bamini((nfd.input as { text: string }).text)).toBe(nfd.expected);
    expect(() => api.unicode_to_bamini((collision.input as { text: string }).text)).toThrow(collision.expected_error);
  }
});

test("TSCII byte convenience API on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.tscii_bytes_to_unicode(new Uint8Array([0xba, 0xa2, 0xc5, 0xfd]))).toBe("\u0b9a\u0bbf\u0bb5\u0ba9\u0bcd");
    expect(api.unicode_to_tscii_bytes("\u0b87")).toEqual([0xfe]);
    expect(() => api.tscii_bytes_to_unicode([65, 255])).toThrow("unsupported TSCII byte at offset 1: 0xFF");
  }
});

test("fraction and date convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    for (const row of cases) {
      if (!("expected" in row)) continue;
      const input = row.input as { numerator: number; denominator: number; year: number; month: number; day: number; digits?: DigitStyle; locale?: Locale; style?: DateStyle };
      switch (row.op) {
        case "format_fraction": expect(api.format_fraction(input.numerator, input.denominator, input.digits)).toBe(row.expected); break;
        case "fraction_to_words": expect(api.fraction_to_words(input.numerator, input.denominator, input.locale)).toBe(row.expected); break;
        case "fraction_symbol": expect(api.fraction_symbol(input.numerator, input.denominator)).toBe(row.expected); break;
        case "format_date": expect(api.format_date(input.year, input.month, input.day, input.locale, input.style, input.digits)).toBe(row.expected); break;
      }
    }
    expect(() => api.format_fraction(1, 0)).toThrow("fraction denominator must not be zero");
    expect(() => api.format_date(2023, 2, 29)).toThrow("invalid Gregorian date");
  }
});


test("TAB byte convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.tab_bytes_to_unicode(new Uint8Array([0xe8, 0xa4]))).toBe("\u0b95\u0bbf");
    expect(api.unicode_to_tab_bytes("\u0b95\u0bbf")).toEqual([0xe8, 0xa4]);
    expect(() => api.tab_bytes_to_unicode([0x98])).toThrow("unsupported TAB byte");
  }
});


test("TAM byte convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.tam_bytes_to_unicode(new Uint8Array([0x41]))).toBe("\u0b95\u0bbf");
    expect(api.unicode_to_tam_bytes("\u0b95\u0bbf")).toEqual([0x41]);
    expect(() => api.unicode_to_tam_bytes("A")).toThrow("unsupported Unicode scalar for TAM");
  }
});


test("Anjal byte convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.anjal_bytes_to_unicode(new Uint8Array([0x8d]))).toBe("\u0b95");
    expect(api.unicode_to_anjal_bytes("\u0b95")).toEqual([0x8d]);
    expect(() => api.anjal_bytes_to_unicode([0xe5])).toThrow("ambiguous ANJAL byte");
  }
});


test("Vanavil convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.vanavil_codes_to_unicode(new Uint16Array([0x006a, 0x00e4, 0x0153]))).toBe("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
    expect(api.vanavil_text_to_unicode("j\u00e4\u0153")).toBe("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd");
    expect(api.unicode_to_vanavil_codes("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")).toEqual([0x006a, 0x00e4, 0x0153]);
    expect(api.unicode_to_vanavil_text("\u0ba4\u0bae\u0bbf\u0bb4\u0bcd")).toBe("j\u00e4\u0153");
    expect(() => api.unicode_to_vanavil_text("\u0bb6\u0bcd\u0bb0\u0bc0")).toThrow("unsupported Unicode scalar for Vanavil");
  }
});

test("Vakyakarana true-Moon convenience API on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const moon = api.vakya_true_moon_from_kali_day(1_844_004);
    expect(moon.moon_vakya_number).toBe(154);
    expect(moon.uncorrected_true_moon).toEqual({ rasi: 4, degrees: 11, minutes: 14, seconds: 1 });
    expect(moon.true_moon).toEqual({ rasi: 4, degrees: 11, minutes: 17, seconds: 32 });
  }
});

test("Vakyakarana local-sunrise correction on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const result = api.vakya_reduce_to_local_true_sunrise(
      { rasi: 4, degrees: 11, minutes: 17, seconds: 32 },
      { degrees: 14, minutes: 12, seconds: 0 },
      130,
      -266,
      -210,
    );
    expect(result.correction_arcseconds).toBe(-491);
    expect(result.local_true_position).toEqual({ rasi: 4, degrees: 11, minutes: 9, seconds: 21 });
  }
});

test("Vakyakarana Cara interval on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const result = api.vakya_cara_from_sayana_sun(
      { rasi: 4, degrees: 22, minutes: 30, seconds: 0 },
      30,
    );
    expect(result.bhuja).toEqual({ rasi: 1, degrees: 7, minutes: 30, seconds: 0 });
    expect(result.cara_vinadi_tenths).toBe(-720);
  }
});

test("Vakyakarana Deśāntara conversion on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.vakya_desantara_from_yojana_distance(244).desantara_vinadi_tenths).toBe(-266);
    expect(api.vakya_desantara_from_yojana_distance(-244).desantara_vinadi_tenths).toBe(266);
  }
});

test("Vakyakarana Bhujaantara interpolation on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    expect(api.vakya_bhujaantara_from_true_sun(5, 84_513).bhujaantara_vinadi_tenths).toBe(-210);
    expect(api.vakya_bhujaantara_from_true_sun(0, 54_000).bhujaantara_vinadi_tenths).toBe(185);
  }
});

test("Thirukanitham typed calendar APIs on both WASM targets", () => {
  const context = {
    region: "TN" as const,
    latitude_microdegrees: 13_087_840,
    longitude_microdegrees: 80_278_470,
    elevation_meters: 14,
    time_zone: "Asia/Kolkata" as const,
  };
  const date = { year: 2026, month: 11, day: 1 };
  for (const api of [nodeApi, webApi]) {
    expect(api.calendar_profile_info().definition_id).toBe("thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2");
    const converted = api.gregorian_to_tamil_date(date, context);
    expect(converted.tamil_date).toEqual({ solar_year: 2026, month: 7, month_name: "Aippasi", day: 15 });
    expect(api.tamil_to_gregorian_date(converted.tamil_date, context).gregorian_date).toEqual(date);
    expect(api.tamil_month_info(2026, 7, context).days).toBe(30);
    const year = api.tamil_year_info(2025, context);
    expect(year.days).toBe(365);
    expect(year.months).toHaveLength(12);
    expect(year.year_cycle.cycle_name).toBe("Visvavasu");
    expect(api.tamil_year_cycle_info(2024, context).cycle_name).toBe("Krodhi");
    expect(api.add_tamil_date({ solar_year: 2025, month: 1, month_name: "Chithirai", day: 1 }, "days", 1, context).gregorian_date)
      .toEqual({ year: 2025, month: 4, day: 15 });
    expect(api.panchangam_at(1_793_514_600, context).limbs.tithi.name).toBe("Saptami");
    const day = api.panchangam_day(date, context);
    expect(day.sunrise_minute_of_day).toBe(362);
    expect(day.transitions).toHaveLength(5);
    const periods = api.calendar_daylight_periods(date, context);
    expect(periods.intervals.map((period) => period.period)).toEqual([
      "yamagandam", "kuligai", "rahukalam",
    ]);
    expect(periods.intervals.map((period) => period.eighth_part)).toEqual([5, 7, 8]);
  }
}, 15_000);

test("named observance convenience API on both WASM targets", () => {
  const context = {
    region: "TN" as const,
    latitude_microdegrees: 13_087_840,
    longitude_microdegrees: 80_278_470,
    elevation_meters: 14,
    time_zone: "Asia/Kolkata" as const,
  };
  for (const api of [nodeApi, webApi]) {
    const result = api.calendar_observances(2026, context, undefined, undefined, 10);
    expect(result.rule_set_id).toBe("thirukanitham-tamil-named-observances-v1");
    expect(result.source_compatibility).toBe("publisher_equivalence_not_claimed");
    expect(result.supported_event_ids).toContain("amavasya_tithi_day");
    expect(result.supported_event_ids).not.toContain("krishna_jayanthi");
    expect(result.events.length).toBeGreaterThan(0);
  }
}, 15_000);

test("bounded Vakyakarana civil APIs on both WASM targets", () => {
  const definition = "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1";
  const context = { reference_station: "ujjain" as const, time_zone: "Asia/Kolkata" as const };
  const date = { year: 1947, month: 10, day: 11 };
  for (const api of [nodeApi, webApi]) {
    expect(api.calendar_profile_info(definition).day_boundary).toBe("ujjain_mean_sunrise");
    const converted = api.gregorian_to_tamil_date(date, context, definition);
    expect(converted.tamil_date).toEqual({ solar_year: 1947, month: 6, month_name: "Purattasi", day: 24 });
    expect(api.tamil_to_gregorian_date(converted.tamil_date, context, definition).gregorian_date).toEqual(date);
    expect(api.tamil_month_info(1947, 6, context, definition).days).toBe(30);
    const year = api.tamil_year_info(1947, context, definition);
    expect(year.days).toBe(365);
    expect(year.months).toHaveLength(12);
    expect(year.reference_station).toBe("ujjain");
    expect(year.year_cycle.cycle_name).toBe("Sarvajit");
    expect(api.tamil_year_cycle_info(1947, context, definition).cycle_index).toBe(21);
    expect(api.add_tamil_date({ solar_year: 1947, month: 6, month_name: "Purattasi", day: 24 }, "days", 1, context, "reject", definition).gregorian_date)
      .toEqual({ year: 1947, month: 10, day: 12 });
    const at = api.panchangam_at(-701_391_788, context, definition);
    expect(at.limbs.tithi.name).toBe("Dwadashi");
    expect(at.reference_station).toBe("ujjain");
    const day = api.panchangam_day(date, context, definition);
    expect(day.sunrise_minute_of_day).toBe(387);
    expect(day.sunset_minute_of_day).toBeNull();
    expect(day.sunset_status).toContain("unavailable");
  }
});

test("official annual holiday schedules on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const tn = api.calendar_official_holidays("TN", 2025);
    expect(tn.source_sha256).toBeNull();
    expect(tn.holidays).toHaveLength(24);
    expect(tn.holidays[1].name).toBe("Pongal");
    const sl = api.calendar_official_holidays("SL", 2027);
    expect(sl.source_sha256).toBe("9071010e6d253e72aee4cdd40057cebc2dfc98e45e713de65ceb9d209cb09eb9");
    expect(sl.holidays).toHaveLength(25);
  }
});

test("Thirukanitham primary lunar phases on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const result = api.lunar_phase_events(1_736_121_600, 1_738_195_200);
    expect(result.events.map((event) => event.phase)).toEqual([
      "first_quarter", "full_moon", "last_quarter", "new_moon",
    ]);
    expect(result.events.map((event) => event.utc_minute)).toEqual([
      { year: 2025, month: 1, day: 6, hour: 23, minute: 56 },
      { year: 2025, month: 1, day: 13, hour: 22, minute: 27 },
      { year: 2025, month: 1, day: 21, hour: 20, minute: 31 },
      { year: 2025, month: 1, day: 29, hour: 12, minute: 36 },
    ]);
  }
});

test("normalization repair and search folding convenience APIs on both WASM targets", () => {
  for (const api of [nodeApi, webApi]) {
    const res = api.repair_tamil_text("\u0b95\u0bcd\u0bcd");
    expect(res.text).toBe("\u0b95\u0bcd");
    expect(res.diagnostics.duplicate_pulli_count).toBe(1);
    expect(res.diagnostics.total_repairs).toBe(1);

    expect(api.fold_for_search("\u0baa\u0bb4\u0bae\u0bcd", "mayangoli")).toBe("\u0baa\u0bb2\u0bae\u0bcd");
    expect(api.fold_for_search("\u0bb0\u0bbe\u0b9c\u0bbe", "grantha")).toBe("\u0bb0\u0bbe\u0b9a\u0bbe");
  }
});

const PACK_REL_DIRS: Record<PackId, string> = {
  core: "../../../lexicon/dictionary",
  names_taxa: "../../../lexicon/packs/names_taxa",
  regional: "../../../lexicon/packs/regional",
};

interface PackManifestData {
  pack_id: string;
  dataset_version: string;
  schema_version: number;
  index_format_version: number;
  manifest_sha256: string;
  unknown_region_entries: number;
}

function readPackManifest(packId: PackId): PackManifestData {
  const tomlPath = fileURLToPath(new URL(`${PACK_REL_DIRS[packId]}/packs.toml`, import.meta.url));
  const raw = readFileSync(tomlPath, "utf8");
  const strField = (key: string): string => {
    const match = raw.match(new RegExp(`^${key}\\s*=\\s*"([^"]+)"`, "m"));
    if (!match) throw new Error(`Missing ${key} in ${tomlPath}`);
    return match[1];
  };
  const intField = (key: string): number => {
    const match = raw.match(new RegExp(`^${key}\\s*=\\s*(\\d+)`, "m"));
    if (!match) throw new Error(`Missing ${key} in ${tomlPath}`);
    return Number.parseInt(match[1], 10);
  };
  return {
    pack_id: strField("pack_id"),
    dataset_version: strField("dataset_version"),
    schema_version: intField("schema_version"),
    index_format_version: intField("index_format_version"),
    manifest_sha256: strField("manifest_sha256"),
    unknown_region_entries: intField("unknown_region_entries"),
  };
}

function parseCsvRows(raw: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;
  for (let i = 0; i < raw.length; i += 1) {
    const ch = raw[i];
    if (inQuotes) {
      if (ch === "\"") {
        if (raw[i + 1] === "\"") {
          cell += "\"";
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        cell += ch;
      }
    } else if (ch === "\"") {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n") {
      row.push(cell);
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
      cell = "";
    } else if (ch !== "\r") {
      cell += ch;
    }
  }
  if (cell.length > 0 || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }
  return rows;
}

function firstCanonicalWrittenForm(packId: PackId): string {
  const csvPath = fileURLToPath(new URL(`${PACK_REL_DIRS[packId]}/assertions.csv`, import.meta.url));
  const rows = parseCsvRows(readFileSync(csvPath, "utf8"));
  if (rows.length < 2) throw new Error(`Empty CSV: ${csvPath}`);
  const headers = rows[0];
  const subjectKindIdx = headers.indexOf("subject_kind");
  const valueJsonIdx = headers.indexOf("value_json");
  if (subjectKindIdx < 0 || valueJsonIdx < 0) throw new Error(`Missing required columns in ${csvPath}`);
  for (let i = 1; i < rows.length; i += 1) {
    const cols = rows[i];
    if (cols[subjectKindIdx] === "form") {
      const parsed = JSON.parse(cols[valueJsonIdx]);
      if (typeof parsed === "string" && parsed.length > 0) return parsed;
    }
  }
  throw new Error(`No canonical form assertion found in ${csvPath}`);
}

function absentGoldenInput(): string {
  const text = readFileSync(join(root, "lexicon_lookup.jsonl"), "utf8").trim();
  for (const line of text.split(/\r?\n/)) {
    const row = JSON.parse(line);
    if (row.id === "lexicon_lookup_not_found_absent_007") {
      expect(row.expected?.status).toBe("not_found");
      return row.input as string;
    }
  }
  throw new Error("Missing lexicon_lookup_not_found_absent_007 golden vector");
}

function assertPackMatchesManifest(pack: LexiconPackInfo, manifest: PackManifestData): void {
  expect(pack.id).toBe(manifest.pack_id);
  expect(pack.dataset_version).toBe(manifest.dataset_version);
  expect(pack.schema_version).toBe(manifest.schema_version);
  expect(pack.index_format_version).toBe(manifest.index_format_version);
  expect(pack.manifest_sha256).toBe(manifest.manifest_sha256);
  expect(pack.available).toBe(true);
  expect(pack.coverage.unknown_region_entries).toBe(manifest.unknown_region_entries);
}

test("lexicon pack manifest and convenience APIs on both WASM targets", () => {
  const profile = activeProfile;
  const envSha = process.env.TAMIL_LEXICON_MANIFEST_SHA256;
  const envVer = process.env.TAMIL_LEXICON_DATASET_VERSION;
  const rawPackManifests = process.env.TAMIL_LEXICON_PACK_MANIFESTS;
  const envPackManifests = rawPackManifests
    ? (JSON.parse(rawPackManifests) as Record<string, { dataset_version: string; manifest_sha256: string }>)
    : undefined;
  const absentInput = absentGoldenInput();

  for (const api of [nodeApi, webApi]) {
    const packs: LexiconPackInfo[] = api.lexicon_packs();
    if (profile === "default") {
      expect(packs).toEqual([]);
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf")).toThrow("lexicon: pack unavailable 'core'");
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: [] })).toThrow(
        "lexicon: packs must be a nonempty string array",
      );
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: ["unknown"] })).toThrow(
        "lexicon: unknown pack 'unknown'",
      );
    } else if (profile === "core") {
      const coreManifest = readPackManifest("core");
      expect(packs).toHaveLength(1);
      const [core] = packs;
      assertPackMatchesManifest(core, coreManifest);
      if (envSha) expect(core.manifest_sha256).toBe(envSha);
      if (envVer) expect(core.dataset_version).toBe(envVer);

      const opts: LexiconLookupOptions = { packs: ["core"] };
      const matched: LexiconLookupResponse = api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf");
      expect(matched.status).toBe("matched");
      expect(matched.entries).toHaveLength(2);
      expect(matched.packs).toEqual([core]);
      expect(api.lexicon_lookup("\u0b85\u0b9f\u0b9f\u0bbe", opts).status).toBe("matched");
      const notFound = api.lexicon_lookup(absentInput);
      expect(notFound.status).toBe("not_found");
      expect(notFound.entries).toEqual([]);

      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: ["regional"] })).toThrow(
        "lexicon: pack unavailable 'regional'",
      );
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { region: "LK-JAFFNA" })).toThrow(
        "lexicon: unknown region 'LK-JAFFNA'",
      );
      expect(() => api.lexicon_lookup("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8", { register: "written" })).toThrow(
        "lexicon: unknown register 'written'",
      );
    } else if (profile === "full") {
      const expectedIds: PackId[] = ["core", "names_taxa", "regional"];
      expect(packs.map((pack) => pack.id)).toEqual(expectedIds);
      expectedIds.forEach((packId, index) => {
        const pack = packs[index];
        assertPackMatchesManifest(pack, readPackManifest(packId));
        if (envPackManifests) {
          expect(pack.dataset_version).toBe(envPackManifests[packId]?.dataset_version);
          expect(pack.manifest_sha256).toBe(envPackManifests[packId]?.manifest_sha256);
        }
      });
      const [core] = packs;
      if (envSha) expect(core.manifest_sha256).toBe(envSha);
      if (envVer) expect(core.dataset_version).toBe(envVer);

      const matched: LexiconLookupResponse = api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf");
      expect(matched.status).toBe("matched");
      expect(matched.entries).toHaveLength(2);
      expect(matched.packs).toEqual([core]);
      const allPacks = api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: ["core", "names_taxa", "regional"] });
      expect(allPacks.status).toBe("matched");
      expect(allPacks.packs).toEqual(packs);
      for (const packId of ["names_taxa", "regional"] as const) {
        const sample = firstCanonicalWrittenForm(packId);
        const packMatch = api.lexicon_lookup(sample, { packs: [packId] });
        expect(packMatch.status).toBe("matched");
        expect(packMatch.entries.length).toBeGreaterThan(0);
      }
      const notFound = api.lexicon_lookup(absentInput);
      expect(notFound.status).toBe("not_found");
      expect(notFound.entries).toEqual([]);

      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: ["terminology"] })).toThrow(
        "lexicon: pack unavailable 'terminology'",
      );
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: [] })).toThrow(
        "lexicon: packs must be a nonempty string array",
      );
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { packs: ["unknown"] })).toThrow(
        "lexicon: unknown pack 'unknown'",
      );
      expect(() => api.lexicon_lookup("\u0ba8\u0ba9\u0bcd\u0bb1\u0bbf", { region: "LK-JAFFNA" })).toThrow(
        "lexicon: unknown region 'LK-JAFFNA'",
      );
      expect(() => api.lexicon_lookup("\u0b85\u0bb1\u0bbf\u0b95\u0bcd\u0b95\u0bc8", { register: "written" })).toThrow(
        "lexicon: unknown register 'written'",
      );
    } else {
      throw new Error(`Unsupported TAMIL_LEXICON_PROFILE=${profile}`);
    }
  }
});

function vectorRequest(row: Request): Request {
  if (!["lexicon_lookup", "lexicon_packs"].includes(row.op)) return row;
  const request: Request & Record<string, unknown> = { ...row };
  for (const key of ["id", "expected", "expected_error", "dialect", "tags", "source", "unicode_exceptions"]) delete request[key];
  return request;
}
