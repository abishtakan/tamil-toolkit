export interface Uyirmei { mei: string; uyir: string }
export interface Olippasai {
  text: string;
  start_byte: number;
  end_byte: number;
  start_letter_idx: number;
  end_letter_idx: number;
  has_coda: boolean;
  coda_count: number;
}
export type LetterQuantity = "kuril" | "nedil" | "mei" | "aytham" | "other";
export type CollationProfile = "agara-v1" | "uyirmei-first-v1";
export interface HyphenationPoint { letter_index: number; byte_offset: number }
export interface HyphenationResult { word: string; syllables: string[]; hyphenated: string }
export interface WrapResult { lines: string[]; wrapped: string }
export interface RepairDiagnostics {
  duplicate_pulli_count: number;
  visual_kombu_count: number;
  stripped_control_count: number;
  total_repairs: number;
}
export interface RepairResult {
  text: string;
  diagnostics: RepairDiagnostics;
}
export interface RepairOptions {
  collapse_duplicate_pulli?: boolean;
  reorder_visual_kombu?: boolean;
  strip_soft_hyphens?: boolean;
  strip_joiners?: boolean;
}
export type FoldingProfile = "mayangoli" | "grantha" | "comprehensive";
export type StopwordProfile = "none" | "conservative" | "broad";
export interface TokenizationSpan {
  text: string;
  start_byte: number;
  end_byte: number;
  start_unit: number;
  end_unit: number;
}
export interface WordToken extends TokenizationSpan {
  kind: "abbreviation" | "word" | "number" | "other";
}
export interface Request { op: string; input: unknown }
export interface EncodingCandidate { encoding: string; confidence: number }
export type LexiconPackId = "core" | "terminology" | "names_taxa" | "regional";
export type LexiconFieldAvailability = "available" | "unknown" | "not_applicable" | "withheld";
export type LexiconScopeState = "attested" | "unrestricted" | "unknown";
export type LexiconAcceptanceKind = "accepted_auto_source" | "accepted_human";
export type LexiconFormRepresentation = "written" | "romanization" | "ipa";
export type LexiconFormRole = "canonical" | "variant";
export type LexiconComponentKind = "definition" | "gloss" | "translation" | "citation";
export type LexiconDirectionality = "directed" | "symmetric";
export type LexiconEndpointKind = "entry" | "sense";
export type LexiconLookupStatus = "matched" | "not_found";
export interface LexiconLookupOptions {
  packs?: string[];
  region?: string;
  register?: string;
}
export interface LexiconAcceptance {
  decision_id: string;
  kind: LexiconAcceptanceKind;
  actor_id: string | null;
  method: string | null;
  decided_on: string;
}
export interface LexiconProvenance {
  assertion_id: string;
  revision_sha256: string;
  source_id: string;
  locator: string;
  acceptance: LexiconAcceptance;
}
export interface LexiconScope {
  state: LexiconScopeState;
  codes: string[];
  provenance: LexiconProvenance[];
}
export interface LexiconField {
  availability: LexiconFieldAvailability;
  value: string | number | boolean | null;
  convention: string | null;
  provenance: LexiconProvenance[];
}
export interface LexiconLabelField {
  availability: LexiconFieldAvailability;
  value: string | null;
  convention: string | null;
  provenance: LexiconProvenance[];
}
export interface LexiconAnnotation {
  property: string;
  field: LexiconField;
}
export interface LexiconForm {
  form_id: string;
  representation: LexiconFormRepresentation;
  role: LexiconFormRole;
  text: string;
  convention: string | null;
  provenance: LexiconProvenance[];
}
export interface LexiconComponentText {
  text_id: string;
  kind: LexiconComponentKind;
  language_id: string;
  text: string;
  provenance: LexiconProvenance[];
}
export interface LexiconExampleText {
  text_id: string;
  kind: "example";
  language_id: string;
  text: string;
  provenance: LexiconProvenance[];
}
export interface LexiconEndpoint {
  kind: LexiconEndpointKind;
  id: string;
}
export interface LexiconRelation {
  relation_id: string;
  code: string;
  directionality: LexiconDirectionality;
  source: LexiconEndpoint;
  target: LexiconEndpoint;
  provenance: LexiconProvenance[];
}
export interface LexiconSense {
  sense_id: string;
  display_order: number;
  parent_sense_id: string | null;
  components: LexiconComponentText[];
  examples: LexiconExampleText[];
  relations: LexiconRelation[];
  region: LexiconScope;
  register: LexiconLabelField;
  annotations: LexiconAnnotation[];
  provenance: LexiconProvenance[];
}
export interface LexiconEntry {
  entry_id: string;
  revision: string;
  headword: string;
  language_id: string;
  part_of_speech: LexiconLabelField;
  forms: LexiconForm[];
  senses: LexiconSense[];
  region: LexiconScope;
  register: LexiconLabelField;
  annotations: LexiconAnnotation[];
  provenance: LexiconProvenance[];
}
export interface LexiconCoverage {
  language_ids: string[];
  region_codes: string[];
  register_codes: string[];
  unknown_region_entries: number;
}
export interface LexiconPackInfo {
  id: LexiconPackId;
  dataset_version: string;
  schema_version: 1;
  index_format_version: number;
  manifest_sha256: string;
  available: true;
  coverage: LexiconCoverage;
}
export interface LexiconLookupResponse {
  schema_version: 1;
  status: LexiconLookupStatus;
  canonical_query: string;
  packs: LexiconPackInfo[];
  entries: LexiconEntry[];
}
export type LexiconPackTier = "verified_open" | "local_historical";
export type LexiconTierFilter = "all" | "open" | "local";
export type LexiconProfile = "open-lite" | "open" | "local" | "full";
export type LexiconCategory =
  | "dictionary"
  | "terminology"
  | "phrases"
  | "regional"
  | "names_taxa"
  | "heritage"
  | "relations";
export interface LexiconCompactForm {
  role: string;
  text: string;
}
export interface LexiconCompactSense {
  gloss_ta?: string;
  gloss_en?: string;
  definition_ta?: string;
  definition_en?: string;
  examples?: string[];
  domain?: string;
  region?: string;
  register?: string;
}
export interface LexiconCompactEntry {
  entry_id: string;
  headword: string;
  pos?: string;
  forms?: LexiconCompactForm[];
  senses?: LexiconCompactSense[];
  domain?: string;
  region?: string;
  register?: string;
  origin_language?: string;
  pure_tamil_equivalent?: string;
  standard_equivalent?: string;
  scientific_name?: string;
  literary_source?: string;
  verb_class?: string;
  transitivity?: string;
  root_word?: string;
  etymology_type?: string;
  dedr_id?: string;
  sandhi_behavior?: string;
  animacy_gender?: string;
  frequency_tier?: string;
  source_id: string;
  source_locator: string;
  rights_status: string;
  permalink?: string;
}
export interface LexiconCompactRelation {
  source_headword: string;
  target_headword: string;
  relation_code: string;
  directionality: string;
  source_id: string;
  source_locator: string;
}
export interface LexiconCompactPackSummary {
  pack_id: string;
  category: LexiconCategory;
  index_format_version: number;
  schema_version: number;
  pack_tier: LexiconPackTier;
  rights_status: string;
  license: string;
  dataset_version: string;
  description: string;
  entry_count: number;
  sense_count: number;
  relation_count: number;
  distinct_headwords: number;
  byte_len: number;
  checksum_sha256: string;
  has_folded_index: boolean;
  has_relations: boolean;
  has_english_index?: boolean;
  source_ids: string[];
  attribution_notice: string;
  domains: string[];
  regions: string[];
  registers: string[];
}
export interface LexiconAnnotatedEntry {
  pack_id: string;
  pack_tier: LexiconPackTier;
  entry: LexiconCompactEntry;
}
export interface LexiconQueryOptions {
  packs?: string[];
  tier?: LexiconTierFilter;
  category?: LexiconCategory | string;
  pos?: string;
  domain?: string;
  region?: string;
  register?: string;
  folded?: boolean;
}
export interface LexiconSearchOptions extends LexiconQueryOptions {
  limit?: number;
  after_key?: string;
}
export interface LexiconFuzzySearchOptions extends Omit<LexiconQueryOptions, "folded"> {
  max_distance?: 1 | 2;
  limit?: number;
}
export interface LexiconCompactLookupResult {
  status: LexiconLookupStatus;
  query: string;
  canonical_query: string;
  folded: boolean;
  searched_packs: string[];
  total_entries: number;
  entries: LexiconAnnotatedEntry[];
}
export interface LexiconPrefixSearchHit {
  headword: string;
  matched_key: string;
  packs: string[];
  pack_tiers: LexiconPackTier[];
  pos: string[];
  preview_gloss?: string;
  domain?: string;
  region?: string;
  entry_count: number;
}
export interface LexiconPrefixSearchResult {
  prefix: string;
  canonical_prefix: string;
  folded: boolean;
  searched_packs: string[];
  hits: LexiconPrefixSearchHit[];
  next_cursor?: string;
  has_more?: boolean;
}
export interface LexiconFuzzySearchHit {
  headword: string;
  distance: number;
  packs: string[];
  pack_tiers: LexiconPackTier[];
  pos: string[];
  preview_gloss?: string;
}
export interface LexiconFuzzySearchResult {
  query: string;
  canonical_query: string;
  max_distance: number;
  searched_packs: string[];
  hits: LexiconFuzzySearchHit[];
}
export interface LexiconLongestPrefixResult {
  query: string;
  prefixes: string[];
}
export interface LexiconRelationsResult {
  status: LexiconLookupStatus;
  query: string;
  canonical_query: string;
  searched_packs: string[];
  relations: LexiconCompactRelation[];
}
export interface LexiconStatsResult {
  pack_count: number;
  total_entries: number;
  total_senses: number;
  total_relations: number;
  total_bytes: number;
  packs: LexiconCompactPackSummary[];
  category_counts?: Record<string, number>;
  pos_counts?: Record<string, number>;
  domain_counts?: Record<string, number>;
  region_counts?: Record<string, number>;
  register_counts?: Record<string, number>;
  has_english_index?: boolean;
}
export interface LexiconWordMeaning {
  text: string;
  language: string;
  pos?: string;
  domain?: string;
  region?: string;
  register?: string;
  pack_id: string;
  category: LexiconCategory;
  pack_tier: LexiconPackTier;
  rights_status: string;
}
export interface LexiconWordRelationsGroup {
  synonyms: string[];
  antonyms: string[];
  related: string[];
  hypernyms: string[];
}
export interface LexiconWordSourceRef {
  pack_id: string;
  category: LexiconCategory;
  pack_tier: LexiconPackTier;
  rights_status: string;
  source_id: string;
  source_locator: string;
  permalink?: string;
}
export interface LexiconWordDefinition {
  status: LexiconLookupStatus;
  query: string;
  canonical_query: string;
  headword: string;
  folded: boolean;
  searched_packs: string[];
  categories: LexiconCategory[];
  pos: string[];
  meanings_en: LexiconWordMeaning[];
  meanings_ta: LexiconWordMeaning[];
  examples: string[];
  variants: string[];
  domains: string[];
  regions: string[];
  registers: string[];
  standard_equivalents: string[];
  pure_tamil_equivalents: string[];
  origin_languages: string[];
  scientific_names: string[];
  literary_sources: string[];
  matched_headwords?: string[];
  ipa?: string[];
  verb_classes?: string[];
  transitivity?: string[];
  root_words?: string[];
  etymology_types?: string[];
  dedr_ids?: string[];
  sandhi_behaviors?: string[];
  animacy_genders?: string[];
  frequency_tiers?: string[];
  relations: LexiconWordRelationsGroup;
  has_verified_open: boolean;
  has_local_historical: boolean;
  entry_count: number;
  sources: LexiconWordSourceRef[];
}
export interface LexiconInitOptions {
  profile?: LexiconProfile | string;
  path?: string;
  replace?: boolean;
}
export interface LexiconInitResult {
  directory: string;
  profile: LexiconProfile;
  pack_count: number;
  total_entries: number;
  total_senses: number;
  total_relations: number;
  total_bytes: number;
  loaded: LexiconCompactPackSummary[];
}
export interface LexiconSourceBucketResult {
  query: string;
  normalized_query: string;
  bucket: string;
}
export interface LexiconSourceRecord {
  source_file: string;
  source_row: number;
  lookup_key: string;
  fields: Record<string, string>;
}
export interface LexiconSourceBucketPayload {
  schema_version: number;
  bucket: string;
  records: LexiconSourceRecord[];
}
export interface LexiconSourceLookupResult {
  query: string;
  normalized_query: string;
  status: LexiconLookupStatus;
  data_status: string;
  rights_status: string;
  total: number;
  offset: number;
  limit: number;
  records: LexiconSourceRecord[];
}
export interface DetectionResult {
  status: "detected" | "uncertain";
  encoding: string | null;
  confidence: number;
  reason: string | null;
  candidates: EncodingCandidate[];
}
export type Locale = "TN" | "SL";
export type Currency = "INR" | "LKR" | "SGD" | "MYR" | "USD" | "EUR" | "GBP" | "CAD";
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
export type PunarchiProfile = "nannool-v1";
export type PunarchiChapter = "ezhuttiyal" | "padaviyal" | "uyireeru" | "meyyeeru" | "urupu";
export type PunarchiRelation = "unspecified" | "vetrumai" | "alvazhi";
export type PunarchiAlterationKind = "iyalbu" | "thonral" | "thirithal" | "keduthal";
export interface PunarchiContext {
  relation?: PunarchiRelation;
  subtype?: string;
  lexical_class?: string;
  poetic?: boolean;
}
export interface PunarchiDerivationStep {
  sutra: number;
  rule_id: string;
  stage: number;
  transform: PunarchiAlterationKind;
  before: string;
  after: string;
}
export interface PunarchiJoinAlternative {
  surface: string;
  transform: PunarchiAlterationKind;
  steps: PunarchiDerivationStep[];
  required_context: string | null;
  optional_variant: boolean;
  poetic: boolean;
}
export interface PunarchiJoinResult {
  profile: PunarchiProfile;
  surface: string;
  transform: PunarchiAlterationKind;
  steps: PunarchiDerivationStep[];
  alternatives: PunarchiJoinAlternative[];
}
export interface PunarchiSplitCandidate {
  first: string;
  second: string;
  sutra: number;
  rule_id: string;
  transform: PunarchiAlterationKind;
  steps: PunarchiDerivationStep[];
  split_byte: number;
  split_unit: number;
}
export interface PunarchiSutraInventoryEntry {
  sutra: number;
  chapter: PunarchiChapter;
  tier: string;
  executable: boolean;
  tva_page: number;
  kandigai_sutra: number;
  pm_ref: string;
  summary: string;
  edition_note: string | null;
}

/** Serialization only. The Rust dispatcher owns every operation. */
export function createApi(
  nativeExecute: (request: string) => string,
  nativeLoadPackBytes?: (bytes: Uint8Array) => string,
) {
  const execute = (request: Request): unknown => JSON.parse(nativeExecute(JSON.stringify(request)));
  const buildScopedLexiconRequest = (op: string, input: string, options?: object): Request => {
    if (options === undefined) {
      return { op, input };
    }
    if (options !== null && typeof options === "object" && !Array.isArray(options)) {
      return { ...options, op, input } as Request;
    }
    return { options, op, input } as unknown as Request;
  };
  const thirukanithamDefinition = calendarDefinitions.thirukanitham;
  return {
    execute,
    tokenize_words: (text: string, stopwordProfile?: StopwordProfile) =>
      execute({ op: "tokenize_words", input: { text, stopword_profile: stopwordProfile } }) as WordToken[],
    segment_sentences: (text: string) =>
      execute({ op: "segment_sentences", input: { text } }) as TokenizationSpan[],
    get_letters: (text: string) => execute({ op: "get_letters", input: text }) as string[],
    normalize_nfc: (text: string) => execute({ op: "normalize_nfc", input: text }) as string,
    normalize_nfd: (text: string) => execute({ op: "normalize_nfd", input: text }) as string,
    repair_tamil_text: (text: string, options?: RepairOptions) =>
      execute({ op: "repair_tamil_text", input: options ? { text, options } : { text } }) as RepairResult,
    fold_for_search: (text: string, profile: FoldingProfile = "comprehensive") =>
      execute({ op: "fold_for_search", input: { text, profile } }) as string,
    split_uyirmei: (text: string) => execute({ op: "split_uyirmei", input: text }) as Uyirmei,
    compose_uyirmei: (mei: string, uyir: string) => execute({ op: "compose_uyirmei", input: { mei, uyir } }) as string,
    inspect_tamil_string: (text: string) => execute({ op: "inspect_tamil_string", input: text }) as Inspection,
    classify_quantity: (letter: string) => execute({ op: "classify_quantity", input: letter }) as LetterQuantity,
    baseline_maathirai: (letter: string) => execute({ op: "baseline_maathirai", input: letter }) as number,
    is_kuril: (letter: string) => (execute({ op: "classify_quantity", input: letter }) as string) === "kuril",
    is_nedil: (letter: string) => (execute({ op: "classify_quantity", input: letter }) as string) === "nedil",
    is_mei: (letter: string) => (execute({ op: "classify_quantity", input: letter }) as string) === "mei",
    is_otru: (letter: string) => (execute({ op: "classify_quantity", input: letter }) as string) === "mei",
    is_aytham: (letter: string) => (execute({ op: "classify_quantity", input: letter }) as string) === "aytham",
    get_cognate: (letter: string) => execute({ op: "get_cognate", input: letter }) as string | null,
    are_cognates: (left: string, right: string) => execute({ op: "are_cognates", input: { left, right } }) as boolean,
    get_olippasai: (text: string) => execute({ op: "get_olippasai", input: text }) as Olippasai[],
    compare: (left: string, right: string, profile: CollationProfile = "agara-v1") =>
      execute({ op: "compare", input: { left, right, profile } }) as -1 | 0 | 1,
    sort_words: (words: string[], profile: CollationProfile = "agara-v1") =>
      execute({ op: "sort_words", input: { words, profile } }) as string[],
    sort_key: (text: string, profile: CollationProfile = "agara-v1") =>
      execute({ op: "sort_key", input: { text, profile } }) as number[],
    search_key: (text: string, profile: CollationProfile = "agara-v1") =>
      execute({ op: "search_key", input: { text, profile } }) as number[],
    folded_search_key: (
      text: string,
      profile: FoldingProfile = "comprehensive",
      collate_profile: CollationProfile = "agara-v1"
    ) =>
      execute({
        op: "folded_search_key",
        input: { text, fold_profile: profile, collate_profile },
      }) as number[],
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
    senthamil_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "senthamil_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    senthamil_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "senthamil_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_senthamil_codes: (text: string) => execute({ op: "unicode_to_senthamil_codes", input: { text } }) as number[],
    unicode_to_senthamil_text: (text: string) => execute({ op: "unicode_to_senthamil_text", input: { text } }) as string,
    shree_tam_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "shree_tam_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    shree_tam_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "shree_tam_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_shree_tam_codes: (text: string) => execute({ op: "unicode_to_shree_tam_codes", input: { text } }) as number[],
    unicode_to_shree_tam_text: (text: string) => execute({ op: "unicode_to_shree_tam_text", input: { text } }) as string,
    softview_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "softview_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    softview_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "softview_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_softview_codes: (text: string) => execute({ op: "unicode_to_softview_codes", input: { text } }) as number[],
    unicode_to_softview_text: (text: string) => execute({ op: "unicode_to_softview_text", input: { text } }) as string,
    tbo_codes_to_unicode: (codes: Uint16Array | number[], errors: CodecErrorPolicy = "strict") => execute({ op: "tbo_codes_to_unicode", input: { codes: Array.from(codes), errors } }) as string,
    tbo_text_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "tbo_text_to_unicode", input: { text, errors } }) as string,
    unicode_to_tbo_codes: (text: string) => execute({ op: "unicode_to_tbo_codes", input: { text } }) as number[],
    unicode_to_tbo_text: (text: string) => execute({ op: "unicode_to_tbo_text", input: { text } }) as string,
    unicode_to_braille: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "unicode_to_braille", input: { text, errors } }) as string,
    braille_to_unicode: (text: string, errors: CodecErrorPolicy = "strict") => execute({ op: "braille_to_unicode", input: { text, errors } }) as string,
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
    mixed_fraction_to_words: (value: MixedFraction, locale: Locale = "TN") => execute({ op: "mixed_fraction_to_words", input: { ...value, locale } }) as string,
    words_to_number: (text: string, locale: Locale = "TN") => execute({ op: "words_to_number", input: { text, locale } }) as number,
    transliterate: (text: string, scheme: string, direction: "to_tamil" | "to_latin" = "to_tamil") => execute({ op: "transliterate", input: { text, scheme, direction } }) as string,
    transliterate_schemes: () => execute({ op: "transliterate_schemes", input: {} }) as { id: string; category: string; directions: string[] }[],
    transliterate_suggest: (text: string, scheme: string = "phonetic-v1", limit: number = 5) => execute({ op: "transliterate_suggest", input: { text, scheme, limit } }) as string[],
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
    hyphenate_word: (word: string, delimiter: string = "\u00AD", left_min: number = 2, right_min: number = 2) =>
      execute({ op: "hyphenate_word", input: { word, delimiter, left_min, right_min } }) as HyphenationResult,
    hyphenation_points: (word: string, left_min: number = 2, right_min: number = 2) =>
      execute({ op: "hyphenation_points", input: { word, left_min, right_min } }) as HyphenationPoint[],
    hyphenate_text: (text: string, delimiter: string = "\u00AD", left_min: number = 2, right_min: number = 2) =>
      execute({ op: "hyphenate_text", input: { text, delimiter, left_min, right_min } }) as string,
    wrap_text: (text: string, max_width: number, delimiter: string = "-", left_min: number = 2, right_min: number = 2) =>
      execute({ op: "wrap_text", input: { text, max_width, delimiter, left_min, right_min } }) as WrapResult,
    lexicon_lookup: (text: string, options?: LexiconLookupOptions) => {
      const request: Record<string, unknown> =
        options === undefined
          ? { op: "lexicon_lookup", input: text }
          : options !== null && typeof options === "object" && !Array.isArray(options)
            ? { ...options, op: "lexicon_lookup", input: text }
            : { options, op: "lexicon_lookup", input: text };
      return execute(request as unknown as Request) as LexiconLookupResponse;
    },
    lexicon_packs: () => execute({ op: "lexicon_packs", input: null }) as LexiconPackInfo[],
    lexicon_init: (options?: LexiconProfile | LexiconInitOptions) =>
      execute({ op: "lexicon_init", input: options ?? null }) as LexiconInitResult,
    lexicon_load_pack_bytes: (bytes: Uint8Array): LexiconCompactPackSummary => {
      if (nativeLoadPackBytes) {
        return JSON.parse(nativeLoadPackBytes(bytes)) as LexiconCompactPackSummary;
      }
      const result = execute({
        op: "lexicon_load_pack",
        input: { bytes: Array.from(bytes) },
      }) as { loaded: LexiconCompactPackSummary[] };
      return result.loaded[0];
    },
    lexicon_load_pack: (path: string) =>
      execute({ op: "lexicon_load_pack", input: { path } }) as { loaded: LexiconCompactPackSummary[] },
    lexicon_unload_pack: (packId: string | null = null) =>
      execute({ op: "lexicon_unload_pack", input: packId ?? null }) as
        | { pack_id: string; removed: boolean }
        | { cleared: boolean },
    lexicon_stats: () => execute({ op: "lexicon_stats", input: null }) as LexiconStatsResult,
    lexicon_define: (text: string, options?: LexiconQueryOptions) =>
      execute(buildScopedLexiconRequest("lexicon_define", text, options)) as LexiconWordDefinition,
    lexicon_query: (text: string, options?: LexiconQueryOptions) =>
      execute(buildScopedLexiconRequest("lexicon_query", text, options)) as LexiconCompactLookupResult,
    lexicon_search: (prefix: string, options?: LexiconSearchOptions) =>
      execute(buildScopedLexiconRequest("lexicon_search", prefix, options)) as LexiconPrefixSearchResult,
    lexicon_search_english: (query: string, options?: LexiconSearchOptions) => {
      const input: Record<string, unknown> = { query };
      if (options !== undefined && options !== null && typeof options === "object" && !Array.isArray(options)) {
        for (const key of ["packs", "tier", "category", "pos", "domain", "region", "register", "limit"] as const) {
          const val = options[key];
          if (val !== undefined) {
            input[key] = val;
          }
        }
      }
      return execute({ op: "lexicon_search_english", input }) as LexiconPrefixSearchResult;
    },
    lexiconSearchEnglish: (query: string, options?: LexiconSearchOptions) => {
      const input: Record<string, unknown> = { query };
      if (options !== undefined && options !== null && typeof options === "object" && !Array.isArray(options)) {
        for (const key of ["packs", "tier", "category", "pos", "domain", "region", "register", "limit"] as const) {
          const val = options[key];
          if (val !== undefined) {
            input[key] = val;
          }
        }
      }
      return execute({ op: "lexicon_search_english", input }) as LexiconPrefixSearchResult;
    },
    lexicon_fuzzy_search: (text: string, options?: LexiconFuzzySearchOptions) =>
      execute(buildScopedLexiconRequest("lexicon_fuzzy_search", text, options)) as LexiconFuzzySearchResult,
    lexicon_longest_prefix: (
      text: string,
      options?: Pick<LexiconQueryOptions, "packs" | "tier" | "category">,
    ) =>
      execute(buildScopedLexiconRequest("lexicon_longest_prefix", text, options)) as LexiconLongestPrefixResult,
    lexicon_relations: (text: string, options?: Pick<LexiconQueryOptions, "packs" | "tier" | "category" | "folded">) =>
      execute(buildScopedLexiconRequest("lexicon_relations", text, options)) as LexiconRelationsResult,
    lexicon_source_bucket: (query: string) =>
      execute({ op: "lexicon_source_bucket", input: query }) as LexiconSourceBucketResult,
    lexicon_source_lookup: (
      query: string,
      bucket: LexiconSourceBucketPayload | Record<string, unknown>,
      offset: number = 0,
      limit: number = 25,
    ) =>
      execute({
        op: "lexicon_source_lookup",
        input: { query, bucket, offset, limit },
      }) as LexiconSourceLookupResult,
    punarchi_join: (first: string, second: string, options?: { profile?: PunarchiProfile; context?: PunarchiContext }) =>
      execute({
        op: "punarchi_join",
        input: {
          first,
          second,
          ...(options?.profile !== undefined ? { profile: options.profile } : {}),
          ...(options?.context !== undefined ? { context: options.context } : {}),
        },
      }) as PunarchiJoinResult,
    punarchi_split_candidates: (surface: string, options?: { profile?: PunarchiProfile; poetic?: boolean }) =>
      execute({
        op: "punarchi_split_candidates",
        input: {
          surface,
          ...(options?.profile !== undefined ? { profile: options.profile } : {}),
          ...(options?.poetic !== undefined ? { poetic: options.poetic } : {}),
        },
      }) as PunarchiSplitCandidate[],
    punarchi_rules: (options?: { profile?: PunarchiProfile; chapter?: PunarchiChapter; sutra?: number }) =>
      execute({
        op: "punarchi_rules",
        input: {
          ...(options?.profile !== undefined ? { profile: options.profile } : {}),
          ...(options?.chapter !== undefined ? { chapter: options.chapter } : {}),
          ...(options?.sutra !== undefined ? { sutra: options.sutra } : {}),
        },
      }) as PunarchiSutraInventoryEntry[],
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
