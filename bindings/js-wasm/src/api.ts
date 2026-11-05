export interface Uyirmei { mei: string; uyir: string }
export interface Request { op: string; input: unknown }
export interface EncodingCandidate { encoding: string; confidence: number }
export interface DetectionResult {
  status: "detected" | "uncertain";
  encoding: string | null;
  confidence: number;
  reason: string | null;
  candidates: EncodingCandidate[];
}
export type Locale = "TN" | "SL";
export type Currency = "INR" | "LKR";
export type CodecErrorPolicy = "strict" | "preserve";
export type DigitStyle = "latin" | "tamil";
export type DateStyle = "short" | "medium" | "long" | "full";
export type Grouping = "none" | "indian";
export interface ExactDecimal { negative: boolean; coefficient: string; scale: number }
export interface MixedFraction { negative: boolean; whole: number; numerator: number; denominator: number }
export type NumericRangeEndpoint = { type: "decimal"; value: ExactDecimal } | { type: "fraction"; numerator: number; denominator: number };
export interface GregorianDate { year: number; month: number; day: number }
export type CalendarDisplayScript = "tamil" | "romanized";
export type CalendarDisplayDigits = DigitStyle;
export type CalendarDisplayStyle = "day_month_year" | "weekday_day_month_year";
export type CalendarRegion = "TN" | "SL";
export interface CalendarContext {
  region: CalendarRegion;
  latitude_microdegrees: number;
  longitude_microdegrees: number;
  elevation_meters: number;
  time_zone: "Asia/Kolkata" | "Asia/Colombo";
}
export interface VakyaCivilContext { reference_station: "ujjain"; time_zone: "Asia/Kolkata" | "Asia/Colombo" }
export type CalendarContextInput = CalendarContext | VakyaCivilContext;
export type CalendarProfileComparisonMoment =
  | { date: GregorianDate; instant_unix_seconds?: never }
  | { date?: never; instant_unix_seconds: number };
export type CalendarProfileComparisonInput = CalendarProfileComparisonMoment & {
  thirukanitham_context: CalendarContext;
  vakya_context: VakyaCivilContext;
};
export interface CalendarProfileComparisonResult {
  comparison_basis: "same_gregorian_civil_date" | "same_utc_instant";
  moment: CalendarProfileComparisonMoment;
  profiles: Record<string, unknown>;
  differing_fields: string[];
  accuracy_assessment: "not_assessed";
}
export type CalendarObservanceId = "puthandu" | "bhogi_pandigai" | "pongal" | "mattu_pongal" | "amavasya_tithi_day" | "pournami_tithi_day" | "sri_vaishnava_ekadashi" | "nava_pradosham" | "aadi_perukku" | "thai_poosam" | "panguni_uthiram" | "vaikasi_visakam" | "arudra_darshan" | "karthigai_deepam" | "chitra_pournami" | "vinayaka_chaturthi" | "sivarathri" | "deepavali" | "navaratri_ghatasthapana" | "ayudha_puja" | "vijayadasami" | "sankatahara_chaturthi" | "krishna_jayanthi";
export interface CalendarObservanceSource { id: string; url: string; locator: string; sha256: string | null; year: number | null }
export interface CalendarObservanceEvent {
  event_id: CalendarObservanceId; display_name: string; date: GregorianDate;
  rule_id: string; tithi_index: number | null; nakshatra_index: number | null;
  source_ids: string[];
}
export interface CalendarObservances {
  definition_id: string; rule_set_id: "thirukanitham-tamil-named-observances-v1";
  gregorian_year: number; jurisdiction: "TN"; context: CalendarContext;
  scope_note: string; astronomy_note: string;
  source_compatibility: "publisher_equivalence_not_claimed";
  reuse_terms_status: string; sources: CalendarObservanceSource[];
  supported_event_ids: CalendarObservanceId[]; events: CalendarObservanceEvent[];
}
export interface ThiruvalluvarYearInfo {
  convention_id: "tn-thiruvalluvar-thai1-thirukanitham-v1";
  calendar_definition_id: string;
  context: CalendarContext;
  gregorian_date: GregorianDate;
  thiruvalluvar_year: number;
  thai1_date: GregorianDate;
  boundary_status: "before_thai1" | "on_or_after_thai1";
  year_number_rule: string;
  official_equivalence: "not_established";
  scope_note: string;
  known_source_conflict: string;
  sources: Array<{ id: string; url: string; locator: string }>;
}
export const calendarDefinitions = {
  thirukanitham: "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2",
  vakyaCivil: "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1",
} as const;
export interface ThirukanithamProfileInfo {
  profile: string;
  definition_id: string;
  coverage: { start_date: string; end_date: string };
  solar_year: { start: number; end: number; meaning: string };
  ephemeris: {
    provider: string; version: string; license: string; archive_sha256: string;
    sun_model: string; moon_model: string; nutation_model: string;
    solar_coordinate_definition: string; lunar_coordinate_definition: string;
  };
  time_model: {
    tt_minus_utc_millis: number; ut1_minus_utc_assumed_millis: number;
    ut1_minus_utc_max_abs_millis: number; time_zone_database_release: string;
  };
  sidereal_definition: string;
  sidereal_parameters: {
    coordinate_definition: string; true_anchor_milliarcseconds: number;
    mean_anchor_microarcseconds: number; anchor_jd_centidays: number;
    p03_picoarcseconds_per_power: number[]; p03_epoch_jd_millidays: number;
    p03_century_days: number;
  };
  sunrise: {
    center_altitude_arcminutes: number; refraction_arcminutes: number;
    solar_semidiameter_arcminutes: number; earth_radius_meters: number;
    horizon_definition: string;
  };
  vara_definition: string;
  solar_month_rule: string;
  supported_regions: {
    region: string; time_zone: string; utc_offset_seconds: number;
    latitude_min_microdegrees: number; latitude_max_microdegrees: number;
    longitude_min_microdegrees: number; longitude_max_microdegrees: number;
  }[];
  reference_stations: {
    id: string; region: string; latitude_microdegrees: number;
    longitude_microdegrees: number; elevation_meters: number; source: string;
  }[];
  sources: string[];
}
export interface TamilSolarDate { solar_year: number; month: number; month_name: string; day: number }
export interface CalendarDateConversion { definition_id: string; gregorian_date: GregorianDate; tamil_date: TamilSolarDate; reference_station?: string; day_boundary?: string }
export interface TamilMonthInfo {
  definition_id: string; solar_year: number; month: number; month_name: string;
  start_date: GregorianDate; end_date_exclusive: GregorianDate; days: number;
  reference_station?: string; day_boundary?: string;
}
export interface TamilYearInfo {
  definition_id: string; solar_year: number; start_date: GregorianDate;
  year_cycle: TamilSolarYearCycle;
  end_date_exclusive: GregorianDate; days: number;
  months: Array<Pick<TamilMonthInfo, "month" | "month_name" | "start_date" | "end_date_exclusive" | "days">>;
  reference_station?: string; day_boundary?: string;
}
export interface TamilSolarYearCycle {
  solar_year: number;
  cycle_index: number;
  cycle_name: string;
  anchor: { solar_year: number; cycle_index: number };
  source_id: string;
  source: string;
  source_sha256: string;
  region_scope: string;
  sources: string[];
}
export interface TamilYearCycleInfo extends TamilSolarYearCycle { definition_id: string }
export interface OfficialHolidayYearInfo {
  jurisdiction: "TN" | "SL"; year: number; schedule_id: string; source_id: string;
  source: string; source_url: string; source_sha256: string | null;
  reuse_terms_status: "unverified"; scope_note: string;
  holidays: Array<{ date: GregorianDate; name: string; categories: string[] }>;
}
export interface AddTamilDateResult {
  definition_id: string; tamil_date: TamilSolarDate; gregorian_date: GregorianDate;
  reference_station?: string; day_boundary?: string;
}
export interface CalendarDaylightPeriod {
  period: "rahukalam" | "yamagandam" | "kuligai";
  eighth_part: number;
  start_local_time: { hour: number; minute: number; second: number };
  end_local_time: { hour: number; minute: number; second: number };
}
export interface CalendarDaylightPeriods {
  definition_id: string; date: GregorianDate; weekday: string;
  rule_id: string; daylight_basis: string;
  sunrise_local_time: { hour: number; minute: number; second: number };
  sunset_local_time: { hour: number; minute: number; second: number };
  intervals: CalendarDaylightPeriod[]; source: string; source_sha256: string;
}
export type LunarPhase = "new_moon" | "first_quarter" | "full_moon" | "last_quarter";
export interface LunarPhaseEvent {
  phase: LunarPhase;
  ecliptic_longitude_difference_degrees: 0 | 90 | 180 | 270;
  utc_minute: GregorianDate & { hour: number; minute: number };
}
export interface LunarPhaseEvents { definition_id: string; events: LunarPhaseEvent[] }
export interface CalendarLimb { index: number; name: string; paksha: "shukla" | "krishna" | null }
export interface CalendarLimbs { tithi: CalendarLimb; nakshatra: CalendarLimb; yoga: CalendarLimb; karana: CalendarLimb }
export interface PanchangamAt {
  definition_id: string; local_date: GregorianDate;
  local_time: { hour: number; minute: number; second: number };
  vara: string; limbs: CalendarLimbs; reference_station?: string; position_basis?: string;
}
export interface PanchangamTransition {
  limb: "tithi" | "nakshatra" | "yoga" | "karana";
  from_index: number; to_index: number; day_offset: number;
  minute_of_day: number;
}
export interface PanchangamDay {
  definition_id: string; date: GregorianDate;
  sunrise_minute_of_day: number; sunset_minute_of_day: number | null;
  vara: string; limbs_at_sunrise: CalendarLimbs; transitions: PanchangamTransition[];
  sunrise_basis?: string; sunset_status?: string;
}
export interface VakyaCivilProfileInfo {
  profile: string; definition_id: string; coverage: Record<string, unknown>;
  epoch: Record<string, unknown>; reference_station: Record<string, unknown>;
  day_boundary: string; solar_model: Record<string, unknown>;
  moon_model: Record<string, unknown>; local_sunrise: Record<string, unknown>;
  sources: string[]; [key: string]: unknown;
}
export type CalendarProfileInfo = VakyaCivilProfileInfo | ThirukanithamProfileInfo;
export interface Ahargana { days: number; nadi: number; vinadi: number; weekday: string }
export interface SolarTransit { rasi: string; day_field: number; weekday: string; nadi: number; vinadi: number }
export interface VakyaSolarYear { definition_id: string; saka_year_elapsed: number; kali_year: number; ahargana: Ahargana; transits: SolarTransit[] }
export interface DmsAngle { degrees: number; minutes: number; seconds: number }
export interface VakyaTrueSun { definition_id: string; elapsed_from_mesha: { days: number; nadi: number; vinadi: number }; approximate_sun: DmsAngle; bhupadi_correction: DmsAngle; true_sun: DmsAngle }
export interface RasiDmsAngle { rasi: number; degrees: number; minutes: number; seconds: number }
export interface VakyaTrueMoon { definition_id: string; kali_day: number; quotients: { period_12372: number; period_3031: number; period_248: number }; moon_vakya_number: number; uncorrected_true_moon: RasiDmsAngle; daily_motion: DmsAngle; vinadi_adjustment: number; correction_seconds: number; true_moon: RasiDmsAngle }
export interface VakyaLocalSunriseReduction { definition_id: string; true_position: RasiDmsAngle; daily_motion: DmsAngle; adjustment_vinadi_tenths: { cara_half: number; desantara: number; bhujaantara: number; total: number }; correction_arcseconds: number; local_true_position: RasiDmsAngle }
export interface VakyaCara { definition_id: string; sayana_sun: RasiDmsAngle; bhuja: RasiDmsAngle; equinoctial_shadow_tenths: number; cara_vinadi_tenths: number }
export interface VakyaDesantara { definition_id: string; east_west_distance_tenths_yojana: number; desantara_vinadi_tenths: number }
export interface VakyaBhujaantara { definition_id: string; sun_rasi: number; sun_rasi_progress_arcseconds: number; bracketing_endpoint_vinadi: [number, number]; bhujaantara_vinadi_tenths: number }
export interface SymbolInfo { codepoint: number; name: string; kind: string; rational: { numerator: number; denominator: number } | null; canonical_alternative: number | null; source_version: string }
export interface Inspection {
  nfc: string; nfd: string; is_nfc: boolean; is_nfd: boolean;
  ezhuthu_count: number; grapheme_count: number;
  letters: { text: string; classification: string }[];
}

/** Serialization only. The Rust dispatcher owns every operation. */
export function createApi(nativeExecute: (request: string) => string) {
  const execute = (request: Request): unknown => JSON.parse(nativeExecute(JSON.stringify(request)));
  const thirukanithamDefinition = calendarDefinitions.thirukanitham;
  return {
    execute,
    get_letters: (text: string) => execute({ op: "get_letters", input: text }) as string[],
    normalize_nfc: (text: string) => execute({ op: "normalize_nfc", input: text }) as string,
    normalize_nfd: (text: string) => execute({ op: "normalize_nfd", input: text }) as string,
    split_uyirmei: (text: string) => execute({ op: "split_uyirmei", input: text }) as Uyirmei,
    compose_uyirmei: (mei: string, uyir: string) => execute({ op: "compose_uyirmei", input: { mei, uyir } }) as string,
    inspect_tamil_string: (text: string) => execute({ op: "inspect_tamil_string", input: text }) as Inspection,
    compare: (left: string, right: string) => execute({ op: "compare", input: { left, right } }) as -1 | 0 | 1,
    sort_words: (words: string[]) => execute({ op: "sort_words", input: words }) as string[],
    sort_key: (text: string) => execute({ op: "sort_key", input: text }) as number[],
    search_key: (text: string) => execute({ op: "search_key", input: text }) as number[],
    to_words: (value: number, locale: Locale = "TN") => execute({ op: "to_words", input: { value, locale } }) as string,
    format_currency: (amount_minor: number, currency: Currency, locale: Locale = "TN") => execute({ op: "format_currency", input: { amount_minor, currency, locale } }) as string,
    currency_to_words: (amount_minor: number, currency: Currency, locale: Locale = "TN") => execute({ op: "currency_to_words", input: { amount_minor, currency, locale } }) as string,
    bamini_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "bamini_to_unicode", input: { text, errors } }) as string,
    unicode_to_bamini: (text: string) => execute({ op: "unicode_to_bamini", input: { text } }) as string,
    anjal_bytes_to_unicode: (bytes: Uint8Array | number[]) => execute({ op: "anjal_bytes_to_unicode", input: { bytes: Array.from(bytes) } }) as string,
    unicode_to_anjal_bytes: (text: string) => execute({ op: "unicode_to_anjal_bytes", input: { text } }) as number[],
    tam_bytes_to_unicode: (bytes: Uint8Array | number[]) => execute({ op: "tam_bytes_to_unicode", input: { bytes: Array.from(bytes) } }) as string,
    unicode_to_tam_bytes: (text: string) => execute({ op: "unicode_to_tam_bytes", input: { text } }) as number[],
    tab_bytes_to_unicode: (bytes: Uint8Array | number[]) => execute({ op: "tab_bytes_to_unicode", input: { bytes: Array.from(bytes) } }) as string,
    unicode_to_tab_bytes: (text: string) => execute({ op: "unicode_to_tab_bytes", input: { text } }) as number[],
    tscii_bytes_to_unicode: (bytes: Uint8Array | number[]) => execute({ op: "tscii_bytes_to_unicode", input: { bytes: Array.from(bytes) } }) as string,
    unicode_to_tscii_bytes: (text: string) => execute({ op: "unicode_to_tscii_bytes", input: { text } }) as number[],
    lt_tm_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "lt_tm_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    lt_tm_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "lt_tm_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_lt_tm_codes: (text: string) => execute({ op: "unicode_to_lt_tm_codes", input: { text } }) as number[],
    unicode_to_lt_tm_text: (text: string) => execute({ op: "unicode_to_lt_tm_text", input: { text } }) as string,
    vanavil_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "vanavil_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    vanavil_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "vanavil_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_vanavil_codes: (text: string) => execute({ op: "unicode_to_vanavil_codes", input: { text } }) as number[],
    unicode_to_vanavil_text: (text: string) => execute({ op: "unicode_to_vanavil_text", input: { text } }) as string,
    detect_encoding: (data: Uint8Array | Uint16Array | number[] | string) => {
      let input: unknown;
      if (typeof data === "string") {
        input = { text: data };
      } else if (data instanceof Uint8Array) {
        input = { bytes: Array.from(data) };
      } else if (data instanceof Uint16Array) {
        input = { codes: Array.from(data) };
      } else if (Array.isArray(data)) {
        if (data.some((x) => x > 255)) {
          input = { codes: data };
        } else {
          input = { bytes: data };
        }
      } else {
        throw new Error("data must be Uint8Array, Uint16Array, number[], or string");
      }
      return execute({ op: "detect_encoding", input }) as DetectionResult;
    },
    detectEncoding: (data: Uint8Array | Uint16Array | number[] | string) => {
      let input: unknown;
      if (typeof data === "string") {
        input = { text: data };
      } else if (data instanceof Uint8Array) {
        input = { bytes: Array.from(data) };
      } else if (data instanceof Uint16Array) {
        input = { codes: Array.from(data) };
      } else if (Array.isArray(data)) {
        if (data.some((x) => x > 255)) {
          input = { codes: data };
        } else {
          input = { bytes: data };
        }
      } else {
        throw new Error("data must be Uint8Array, Uint16Array, number[], or string");
      }
      return execute({ op: "detect_encoding", input }) as DetectionResult;
    },
    detect_and_decode: (data: Uint8Array | number[] | string) => {
      let input: unknown;
      if (typeof data === "string") {
        input = { text: data };
      } else if (data instanceof Uint8Array) {
        input = { bytes: Array.from(data) };
      } else if (Array.isArray(data)) {
        input = { bytes: data };
      } else {
        throw new Error("data must be Uint8Array, number[], or string");
      }
      return execute({ op: "detect_and_decode", input }) as string;
    },
    detectAndDecode: (data: Uint8Array | number[] | string) => {
      let input: unknown;
      if (typeof data === "string") {
        input = { text: data };
      } else if (data instanceof Uint8Array) {
        input = { bytes: Array.from(data) };
      } else if (Array.isArray(data)) {
        input = { bytes: data };
      } else {
        throw new Error("data must be Uint8Array, number[], or string");
      }
      return execute({ op: "detect_and_decode", input }) as string;
    },
    format_fraction: (numerator: number, denominator: number, digits: DigitStyle = "latin") => execute({ op: "format_fraction", input: { numerator, denominator, digits } }) as string,
    fraction_to_words: (numerator: number, denominator: number, locale: Locale = "TN") => execute({ op: "fraction_to_words", input: { numerator, denominator, locale } }) as string,
    fraction_symbol: (numerator: number, denominator: number) => execute({ op: "fraction_symbol", input: { numerator, denominator } }) as string,
    format_date: (year: number, month: number, day: number, locale: Locale = "TN", style: DateStyle = "long", digits: DigitStyle = "latin") => execute({ op: "format_date", input: { year, month, day, locale, style, digits } }) as string,
    convert_digits: (text: string, to: DigitStyle) => execute({ op: "convert_digits", input: { text, to } }) as string,
    parse_decimal: (text: string, source_digits: DigitStyle, grouping: Grouping = "none", allow_mixed_digits = false) => execute({ op: "parse_decimal", input: { text, source_digits, grouping, allow_mixed_digits } }) as ExactDecimal,
    format_decimal: (value: ExactDecimal, digits: DigitStyle = "latin", grouping: Grouping = "none") => execute({ op: "format_decimal", input: { value, digits, grouping } }) as string,
    decimal_to_words: (text: string, source_digits: DigitStyle, locale: Locale = "TN", grouping: Grouping = "none", allow_mixed_digits = false) => execute({ op: "decimal_to_words", input: { text, source_digits, locale, grouping, allow_mixed_digits } }) as string,
    ordinal_to_words: (value: number, locale: Locale = "TN") => execute({ op: "ordinal_to_words", input: { value, locale } }) as string,
    digit_sequence_to_words: (text: string, source_digits: DigitStyle, locale: Locale = "TN") => execute({ op: "digit_sequence_to_words", input: { text, source_digits, locale } }) as string,
    format_currency_decimal: (amount: string, source_digits: DigitStyle, currency: Currency, locale: Locale = "TN", grouping: Grouping = "none") => execute({ op: "format_currency_decimal", input: { amount, source_digits, currency, locale, grouping } }) as string,
    currency_decimal_to_words: (amount: string, source_digits: DigitStyle, currency: Currency, locale: Locale = "TN", grouping: Grouping = "none") => execute({ op: "currency_decimal_to_words", input: { amount, source_digits, currency, locale, grouping } }) as string,
    parse_fraction_symbol: (text: string) => execute({ op: "parse_fraction_symbol", input: { text } }) as { numerator: number; denominator: number },
    symbol_info: (text: string) => execute({ op: "symbol_info", input: { text } }) as SymbolInfo,
    format_mixed_fraction: (value: MixedFraction, digits: DigitStyle = "latin") => execute({ op: "format_mixed_fraction", input: { ...value, digits } }) as string,
    parse_mixed_fraction: (text: string, source_digits: DigitStyle) => execute({ op: "parse_mixed_fraction", input: { text, source_digits } }) as MixedFraction,
    format_traditional_integer: (value: number) => execute({ op: "format_traditional_integer", input: { value } }) as string,
    parse_traditional_integer: (text: string) => execute({ op: "parse_traditional_integer", input: { text } }) as number,
    parse_percent: (text: string, source_digits: DigitStyle, grouping: Grouping = "none") => execute({ op: "parse_percent", input: { text, source_digits, grouping } }) as ExactDecimal,
    format_percent: (value: ExactDecimal, digits: DigitStyle = "latin", grouping: Grouping = "none") => execute({ op: "format_percent", input: { value, digits, grouping } }) as string,
    ratio_to_percent: (value: ExactDecimal) => execute({ op: "ratio_to_percent", input: { value } }) as ExactDecimal,
    percent_to_ratio: (value: ExactDecimal) => execute({ op: "percent_to_ratio", input: { value } }) as ExactDecimal,
    format_numeric_range: (start: NumericRangeEndpoint, end: NumericRangeEndpoint, start_inclusive: boolean, end_inclusive: boolean, separator = "–", digits: DigitStyle = "latin") => execute({ op: "format_numeric_range", input: { start, end, start_inclusive, end_inclusive, separator, digits } }) as string,
    validate_gregorian_date: (year: number, month: number, day: number) => execute({ op: "validate_gregorian_date", input: { year, month, day } }) as boolean,
    parse_gregorian_date: (text: string) => execute({ op: "parse_gregorian_date", input: { text } }) as GregorianDate,
    weekday: (year: number, month: number, day: number) => execute({ op: "weekday", input: { year, month, day } }) as string,
    add_gregorian_date: (year: number, month: number, day: number, unit: "days" | "months" | "years", amount: number, overflow: "reject" | "clamp" = "reject") => execute({ op: "add_gregorian_date", input: { year, month, day, unit, amount, overflow } }) as GregorianDate,
    date_difference: (start: GregorianDate, end: GregorianDate) => execute({ op: "date_difference", input: { start, end } }) as number,
    date_interval: (start: string, end: string) => execute({ op: "date_interval", input: { start, end } }) as { start: string; end: string; inclusive_days: number },
    vakya_solar_transits: (saka_year_elapsed: number) => execute({ op: "vakya_solar_transits", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", saka_year_elapsed } }) as VakyaSolarYear,
    vakya_true_sun_from_mesha_elapsed: (elapsed_days: number, nadi: number, vinadi: number) => execute({ op: "vakya_true_sun_from_mesha_elapsed", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", elapsed_days, nadi, vinadi } }) as VakyaTrueSun,
    vakya_true_moon_from_kali_day: (kali_day: number) => execute({ op: "vakya_true_moon_from_kali_day", input: { definition_id: "vakyakarana-1962-laghuprakashika-true-moon-v1", kali_day } }) as VakyaTrueMoon,
    vakya_reduce_to_local_true_sunrise: (true_position: RasiDmsAngle, daily_motion: DmsAngle, cara_half_vinadi_tenths: number, desantara_vinadi_tenths: number, bhujaantara_vinadi_tenths: number) => execute({ op: "vakya_reduce_to_local_true_sunrise", input: { definition_id: "vakyakarana-1962-laghuprakashika-local-sunrise-v1", true_position, daily_motion, cara_half_vinadi_tenths, desantara_vinadi_tenths, bhujaantara_vinadi_tenths } }) as VakyaLocalSunriseReduction,
    vakya_cara_from_sayana_sun: (sayana_sun: RasiDmsAngle, equinoctial_shadow_tenths: number) => execute({ op: "vakya_cara_from_sayana_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-cara-v1", sayana_sun, equinoctial_shadow_tenths } }) as VakyaCara,
    vakya_desantara_from_yojana_distance: (east_west_distance_tenths_yojana: number) => execute({ op: "vakya_desantara_from_yojana_distance", input: { definition_id: "vakyakarana-1962-laghuprakashika-desantara-v1", east_west_distance_tenths_yojana } }) as VakyaDesantara,
    vakya_bhujaantara_from_true_sun: (sun_rasi: number, sun_rasi_progress_arcseconds: number) => execute({ op: "vakya_bhujaantara_from_true_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1", sun_rasi, sun_rasi_progress_arcseconds } }) as VakyaBhujaantara,
    calendar_profile_info: (definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_profile_info", input: { definition_id } }) as CalendarProfileInfo,
    gregorian_to_tamil_date: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "gregorian_to_tamil_date", input: { definition_id, date, context } }) as CalendarDateConversion,
    tamil_to_gregorian_date: (date: TamilSolarDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_to_gregorian_date", input: { definition_id, date: { solar_year: date.solar_year, month: date.month, day: date.day }, context } }) as { definition_id: string; tamil_date: TamilSolarDate; gregorian_date: GregorianDate; reference_station?: string; day_boundary?: string },
    tamil_month_info: (solar_year: number, month: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_month_info", input: { definition_id, solar_year, month, context } }) as TamilMonthInfo,
    tamil_year_info: (solar_year: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_year_info", input: { definition_id, solar_year, context } }) as TamilYearInfo,
    tamil_year_cycle_info: (solar_year: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_year_cycle_info", input: { definition_id, solar_year, context } }) as TamilYearCycleInfo,
    calendar_official_holidays: (jurisdiction: "TN" | "SL", year: number) => execute({ op: "calendar_official_holidays", input: { jurisdiction, year } }) as OfficialHolidayYearInfo,
    calendar_observances: (gregorian_year: number, context: CalendarContextInput, rule_set = "thirukanitham-tamil-named-observances-v1", definition_id: string = thirukanithamDefinition, month?: number) => execute({ op: "calendar_observances", input: { definition_id, rule_set, gregorian_year, ...(month === undefined ? {} : { month }), context } }) as CalendarObservances,
    add_tamil_date: (date: TamilSolarDate, unit: "days" | "months" | "years", amount: number, context: CalendarContextInput, overflow: "reject" | "clamp" = "reject", definition_id: string = thirukanithamDefinition) => execute({ op: "add_tamil_date", input: { definition_id, date: { solar_year: date.solar_year, month: date.month, day: date.day }, unit, amount, overflow, context } }) as AddTamilDateResult,
    panchangam_at: (instant_unix_seconds: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "panchangam_at", input: { definition_id, instant_unix_seconds, context } }) as PanchangamAt,
    panchangam_day: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "panchangam_day", input: { definition_id, date, context } }) as PanchangamDay,
    lunar_phase_events: (start_unix_seconds: number, end_unix_seconds: number, definition_id: string = thirukanithamDefinition) => execute({ op: "lunar_phase_events", input: { definition_id, start_unix_seconds, end_unix_seconds } }) as LunarPhaseEvents,
    calendar_daylight_periods: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_daylight_periods", input: { definition_id, date, context } }) as CalendarDaylightPeriods,
    format_tamil_date: (date: GregorianDate, context: CalendarContextInput, script: CalendarDisplayScript = "tamil", digits: CalendarDisplayDigits = "latin", style: CalendarDisplayStyle = "weekday_day_month_year", definition_id: string = thirukanithamDefinition) => execute({ op: "format_tamil_date", input: { definition_id, date, context, script, digits, style } }) as string,
    calendar_display_info: (date: GregorianDate, context: CalendarContextInput, script: CalendarDisplayScript = "tamil", digits: CalendarDisplayDigits = "latin", definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_display_info", input: { definition_id, date, context, script, digits } }) as Record<string, unknown>,
    compare_calendar_profiles: (input: CalendarProfileComparisonInput) => execute({ op: "compare_calendar_profiles", input }) as CalendarProfileComparisonResult,
    thiruvalluvar_year_info: (date: GregorianDate, context: CalendarContext, convention_id: ThiruvalluvarYearInfo["convention_id"] = "tn-thiruvalluvar-thai1-thirukanitham-v1") => execute({ op: "thiruvalluvar_year_info", input: { date, context, convention_id } }) as ThiruvalluvarYearInfo,
    calendar: {
      profileInfo: (definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_profile_info", input: { definition_id } }) as CalendarProfileInfo,
      gregorianToTamilDate: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "gregorian_to_tamil_date", input: { definition_id, date, context } }) as CalendarDateConversion,
      tamilToGregorianDate: (date: TamilSolarDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_to_gregorian_date", input: { definition_id, date: { solar_year: date.solar_year, month: date.month, day: date.day }, context } }) as { definition_id: string; tamil_date: TamilSolarDate; gregorian_date: GregorianDate; reference_station?: string; day_boundary?: string },
      monthInfo: (solar_year: number, month: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_month_info", input: { definition_id, solar_year, month, context } }) as TamilMonthInfo,
      yearInfo: (solar_year: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_year_info", input: { definition_id, solar_year, context } }) as TamilYearInfo,
      yearCycleInfo: (solar_year: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "tamil_year_cycle_info", input: { definition_id, solar_year, context } }) as TamilYearCycleInfo,
      officialHolidays: (jurisdiction: "TN" | "SL", year: number) => execute({ op: "calendar_official_holidays", input: { jurisdiction, year } }) as OfficialHolidayYearInfo,
      observances: (gregorian_year: number, context: CalendarContextInput, rule_set = "thirukanitham-tamil-named-observances-v1", definition_id: string = thirukanithamDefinition, month?: number) => execute({ op: "calendar_observances", input: { definition_id, rule_set, gregorian_year, ...(month === undefined ? {} : { month }), context } }) as CalendarObservances,
      addTamilDate: (date: TamilSolarDate, unit: "days" | "months" | "years", amount: number, context: CalendarContextInput, overflow: "reject" | "clamp" = "reject", definition_id: string = thirukanithamDefinition) => execute({ op: "add_tamil_date", input: { definition_id, date: { solar_year: date.solar_year, month: date.month, day: date.day }, unit, amount, overflow, context } }) as AddTamilDateResult,
      panchangamAt: (instant_unix_seconds: number, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "panchangam_at", input: { definition_id, instant_unix_seconds, context } }) as PanchangamAt,
      panchangamDay: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "panchangam_day", input: { definition_id, date, context } }) as PanchangamDay,
      lunarPhaseEvents: (start_unix_seconds: number, end_unix_seconds: number, definition_id: string = thirukanithamDefinition) => execute({ op: "lunar_phase_events", input: { definition_id, start_unix_seconds, end_unix_seconds } }) as LunarPhaseEvents,
      daylightPeriods: (date: GregorianDate, context: CalendarContextInput, definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_daylight_periods", input: { definition_id, date, context } }) as CalendarDaylightPeriods,
      formatTamilDate: (date: GregorianDate, context: CalendarContextInput, script: CalendarDisplayScript = "tamil", digits: CalendarDisplayDigits = "latin", style: CalendarDisplayStyle = "weekday_day_month_year", definition_id: string = thirukanithamDefinition) => execute({ op: "format_tamil_date", input: { definition_id, date, context, script, digits, style } }) as string,
      displayInfo: (date: GregorianDate, context: CalendarContextInput, script: CalendarDisplayScript = "tamil", digits: CalendarDisplayDigits = "latin", definition_id: string = thirukanithamDefinition) => execute({ op: "calendar_display_info", input: { definition_id, date, context, script, digits } }) as Record<string, unknown>,
      compareProfiles: (input: CalendarProfileComparisonInput) => execute({ op: "compare_calendar_profiles", input }) as CalendarProfileComparisonResult,
      thiruvalluvarYearInfo: (date: GregorianDate, context: CalendarContext, convention_id: ThiruvalluvarYearInfo["convention_id"] = "tn-thiruvalluvar-thai1-thirukanitham-v1") => execute({ op: "thiruvalluvar_year_info", input: { date, context, convention_id } }) as ThiruvalluvarYearInfo,
      vakyaSolarTransits: (saka_year_elapsed: number) => execute({ op: "vakya_solar_transits", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", saka_year_elapsed } }) as VakyaSolarYear,
      vakyaTrueSunFromMeshaElapsed: (elapsed_days: number, nadi: number, vinadi: number) => execute({ op: "vakya_true_sun_from_mesha_elapsed", input: { definition_id: "vakyakarana-1962-laghuprakashika-solar-transits-v1", elapsed_days, nadi, vinadi } }) as VakyaTrueSun,
      vakyaTrueMoonFromKaliDay: (kali_day: number) => execute({ op: "vakya_true_moon_from_kali_day", input: { definition_id: "vakyakarana-1962-laghuprakashika-true-moon-v1", kali_day } }) as VakyaTrueMoon,
      vakyaReduceToLocalTrueSunrise: (true_position: RasiDmsAngle, daily_motion: DmsAngle, cara_half_vinadi_tenths: number, desantara_vinadi_tenths: number, bhujaantara_vinadi_tenths: number) => execute({ op: "vakya_reduce_to_local_true_sunrise", input: { definition_id: "vakyakarana-1962-laghuprakashika-local-sunrise-v1", true_position, daily_motion, cara_half_vinadi_tenths, desantara_vinadi_tenths, bhujaantara_vinadi_tenths } }) as VakyaLocalSunriseReduction,
      vakyaCaraFromSayanaSun: (sayana_sun: RasiDmsAngle, equinoctial_shadow_tenths: number) => execute({ op: "vakya_cara_from_sayana_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-cara-v1", sayana_sun, equinoctial_shadow_tenths } }) as VakyaCara,
      vakyaDesantaraFromYojanaDistance: (east_west_distance_tenths_yojana: number) => execute({ op: "vakya_desantara_from_yojana_distance", input: { definition_id: "vakyakarana-1962-laghuprakashika-desantara-v1", east_west_distance_tenths_yojana } }) as VakyaDesantara,
      vakyaBhujaantaraFromTrueSun: (sun_rasi: number, sun_rasi_progress_arcseconds: number) => execute({ op: "vakya_bhujaantara_from_true_sun", input: { definition_id: "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1", sun_rasi, sun_rasi_progress_arcseconds } }) as VakyaBhujaantara,
    },
  };
}
