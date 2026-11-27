import os
from typing import Any, Literal, TypedDict

class Uyirmei(TypedDict):
    mei: str
    uyir: str

class RepairDiagnostics(TypedDict):
    duplicate_pulli_count: int
    visual_kombu_count: int
    stripped_control_count: int
    total_repairs: int

class RepairResult(TypedDict):
    text: str
    diagnostics: RepairDiagnostics

class RepairOptions(TypedDict, total=False):
    collapse_duplicate_pulli: bool
    reorder_visual_kombu: bool
    strip_soft_hyphens: bool
    strip_joiners: bool

FoldingProfile = Literal["mayangoli", "grantha", "comprehensive"]

class HyphenationPoint(TypedDict):
    letter_index: int
    byte_offset: int

class HyphenationResult(TypedDict):
    word: str
    syllables: list[str]
    hyphenated: str

class WrapResult(TypedDict):
    lines: list[str]
    wrapped: str

class EncodingCandidate(TypedDict):
    encoding: str
    confidence: float

class DetectionResult(TypedDict):
    status: str
    encoding: str | None
    confidence: float
    reason: str | None
    candidates: list[EncodingCandidate]

class ExactDecimal(TypedDict):
    negative: bool
    coefficient: str
    scale: int

class MixedFraction(TypedDict):
    negative: bool
    whole: int
    numerator: int
    denominator: int

class Ahargana(TypedDict):
    days: int
    nadi: int
    vinadi: int
    weekday: str

class SolarTransit(TypedDict):
    rasi: str
    day_field: int
    weekday: str
    nadi: int
    vinadi: int

class VakyaSolarYear(TypedDict):
    definition_id: str
    saka_year_elapsed: int
    kali_year: int
    ahargana: Ahargana
    transits: list[SolarTransit]

class DmsAngle(TypedDict):
    degrees: int
    minutes: int
    seconds: int

class VakyaTrueSun(TypedDict):
    definition_id: str
    elapsed_from_mesha: dict[str, int]
    approximate_sun: DmsAngle
    bhupadi_correction: DmsAngle
    true_sun: DmsAngle

class RasiDmsAngle(TypedDict):
    rasi: int
    degrees: int
    minutes: int
    seconds: int

class VakyaTrueMoon(TypedDict):
    definition_id: str
    kali_day: int
    quotients: dict[str, int]
    moon_vakya_number: int
    uncorrected_true_moon: RasiDmsAngle
    daily_motion: DmsAngle
    vinadi_adjustment: int
    correction_seconds: int
    true_moon: RasiDmsAngle

class VakyaLocalSunriseReduction(TypedDict):
    definition_id: str
    true_position: RasiDmsAngle
    daily_motion: DmsAngle
    adjustment_vinadi_tenths: dict[str, int]
    correction_arcseconds: int
    local_true_position: RasiDmsAngle

class VakyaCara(TypedDict):
    definition_id: str
    sayana_sun: RasiDmsAngle
    bhuja: RasiDmsAngle
    equinoctial_shadow_tenths: int
    cara_vinadi_tenths: int

class VakyaDesantara(TypedDict):
    definition_id: str
    east_west_distance_tenths_yojana: int
    desantara_vinadi_tenths: int

class VakyaBhujaantara(TypedDict):
    definition_id: str
    sun_rasi: int
    sun_rasi_progress_arcseconds: int
    bracketing_endpoint_vinadi: tuple[int, int]
    bhujaantara_vinadi_tenths: int

class CalendarProfileInfo(TypedDict):
    profile: str
    definition_id: str
    coverage: dict[str, str]
    solar_year: dict[str, Any]
    ephemeris: dict[str, Any]
    time_model: dict[str, Any]
    sidereal_definition: str
    sidereal_parameters: dict[str, Any]
    vara_definition: str
    sunrise: dict[str, Any]
    solar_month_rule: str
    supported_regions: list[dict[str, Any]]
    reference_stations: list[dict[str, Any]]
    sources: list[str]

class RangeDecimalEndpoint(TypedDict):
    type: str
    value: ExactDecimal

class RangeFractionEndpoint(TypedDict):
    type: str
    numerator: int
    denominator: int

class CalendarContext(TypedDict):
    region: str
    latitude_microdegrees: int
    longitude_microdegrees: int
    elevation_meters: int
    time_zone: str

class VakyaCivilContext(TypedDict):
    reference_station: str
    time_zone: str

class CalendarObservanceSource(TypedDict):
    id: str
    url: str
    locator: str
    sha256: str | None
    year: int | None

class CalendarObservanceEvent(TypedDict):
    event_id: str
    display_name: str
    date: dict[str, int]
    rule_id: str
    tithi_index: int | None
    nakshatra_index: int | None
    source_ids: list[str]

class CalendarObservances(TypedDict):
    definition_id: str
    rule_set_id: str
    gregorian_year: int
    jurisdiction: str
    context: CalendarContext
    scope_note: str
    astronomy_note: str
    source_compatibility: Literal["publisher_equivalence_not_claimed"]
    reuse_terms_status: str
    sources: list[CalendarObservanceSource]
    supported_event_ids: list[str]
    events: list[CalendarObservanceEvent]

CalendarDisplayScript = Literal["tamil", "romanized"]
CalendarDisplayDigits = Literal["latin", "tamil"]
CalendarDisplayStyle = Literal["day_month_year", "weekday_day_month_year"]

class TamilSolarDate(TypedDict):
    solar_year: int
    month: int
    day: int

StopwordProfile = Literal["none", "conservative", "broad"]


class TokenizationSpan(TypedDict):
    text: str
    start_byte: int
    end_byte: int
    start_unit: int
    end_unit: int


class WordToken(TokenizationSpan):
    kind: Literal["abbreviation", "word", "number", "other"]


def tokenize_words(text: str, *, stopword_profile: StopwordProfile = "none") -> list[WordToken]: ...
def segment_sentences(text: str) -> list[TokenizationSpan]: ...
def execute(request: dict[str, Any]) -> Any: ...
def get_letters(text: str) -> list[str]: ...
def normalize_nfc(text: str) -> str: ...
def normalize_nfd(text: str) -> str: ...
def repair_tamil_text(text: str, options: RepairOptions | None = ...) -> RepairResult: ...
def fold_for_search(text: str, profile: FoldingProfile | str = "comprehensive") -> str: ...
def split_uyirmei(text: str) -> Uyirmei: ...
def compose_uyirmei(mei: str, uyir: str) -> str: ...
def inspect_tamil_string(text: str) -> dict[str, Any]: ...
def compare(left: str, right: str, profile: str = "agara-v1") -> int: ...
def sort_words(words: list[str], profile: str = "agara-v1") -> list[str]: ...
def sort_key(text: str, profile: str = "agara-v1") -> list[int]: ...
def search_key(text: str, profile: str = "agara-v1") -> list[int]: ...
def folded_search_key(text: str, profile: str = "comprehensive", collate_profile: str = "agara-v1") -> list[int]: ...
def to_words(value: int, locale: str = "TN") -> str: ...
def format_currency(amount_minor: int, currency: str, locale: str = "TN") -> str: ...
def currency_to_words(amount_minor: int, currency: str, locale: str = "TN") -> str: ...
def bamini_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_bamini(text: str) -> str: ...
def anjal_bytes_to_unicode(data: bytes | list[int]) -> str: ...
def unicode_to_anjal_bytes(text: str) -> bytes: ...
def tam_bytes_to_unicode(data: bytes | list[int]) -> str: ...
def unicode_to_tam_bytes(text: str) -> bytes: ...
def tab_bytes_to_unicode(data: bytes | list[int]) -> str: ...
def unicode_to_tab_bytes(text: str) -> bytes: ...
def tscii_bytes_to_unicode(data: bytes | list[int]) -> str: ...
def unicode_to_tscii_bytes(text: str) -> bytes: ...
def lt_tm_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def lt_tm_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_lt_tm_codes(text: str) -> list[int]: ...
def unicode_to_lt_tm_text(text: str) -> str: ...
def vanavil_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def vanavil_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_vanavil_codes(text: str) -> list[int]: ...
def unicode_to_vanavil_text(text: str) -> str: ...
def senthamil_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def senthamil_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_senthamil_codes(text: str) -> list[int]: ...
def unicode_to_senthamil_text(text: str) -> str: ...
def shree_tam_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def shree_tam_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_shree_tam_codes(text: str) -> list[int]: ...
def unicode_to_shree_tam_text(text: str) -> str: ...
def softview_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def softview_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_softview_codes(text: str) -> list[int]: ...
def unicode_to_softview_text(text: str) -> str: ...
def tbo_codes_to_unicode(codes: list[int], errors: str = "strict") -> str: ...
def tbo_text_to_unicode(text: str, errors: str = "strict") -> str: ...
def unicode_to_tbo_codes(text: str) -> list[int]: ...
def unicode_to_tbo_text(text: str) -> str: ...
def unicode_to_braille(text: str, errors: str = "strict") -> str: ...
def braille_to_unicode(text: str, errors: str = "strict") -> str: ...
def detect_encoding(data: bytes | bytearray | str | list[int]) -> DetectionResult: ...
def detect_and_decode(data: bytes | bytearray | str | list[int]) -> str: ...
def format_fraction(numerator: int, denominator: int, digits: str = "latin") -> str: ...
def fraction_to_words(numerator: int, denominator: int, locale: str = "TN") -> str: ...
def fraction_symbol(numerator: int, denominator: int) -> str: ...
def format_date(year: int, month: int, day: int, locale: str = "TN", style: str = "long", digits: str = "latin") -> str: ...
def convert_digits(text: str, to: str) -> str: ...
def parse_decimal(text: str, source_digits: str, grouping: str = "none", allow_mixed_digits: bool = False) -> ExactDecimal: ...
def format_decimal(value: ExactDecimal, digits: str = "latin", grouping: str = "none") -> str: ...
def decimal_to_words(text: str, source_digits: str, locale: str = "TN", grouping: str = "none", allow_mixed_digits: bool = False) -> str: ...
def ordinal_to_words(value: int, locale: str = "TN") -> str: ...
def digit_sequence_to_words(text: str, source_digits: str, locale: str = "TN") -> str: ...
def format_currency_decimal(amount: str, source_digits: str, currency: str, locale: str = "TN", grouping: str = "none") -> str: ...
def currency_decimal_to_words(amount: str, source_digits: str, currency: str, locale: str = "TN", grouping: str = "none") -> str: ...
def parse_fraction_symbol(text: str) -> dict[str, int]: ...
def symbol_info(text: str) -> dict[str, Any]: ...
def format_mixed_fraction(negative: bool, whole: int, numerator: int, denominator: int, digits: str = "latin") -> str: ...
def parse_mixed_fraction(text: str, source_digits: str) -> MixedFraction: ...
def mixed_fraction_to_words(negative: bool, whole: int, numerator: int, denominator: int, locale: str = "TN") -> str: ...
def words_to_number(text: str, locale: str = "TN") -> int: ...
def transliterate(text: str, scheme: str, direction: str = "to_tamil") -> str: ...
def transliterate_schemes() -> list[dict[str, Any]]: ...
def transliterate_suggest(text: str, scheme: str = "phonetic-v1", limit: int = 5) -> list[str]: ...
def format_traditional_integer(value: int) -> str: ...
def parse_traditional_integer(text: str) -> int: ...
def parse_percent(text: str, source_digits: str, grouping: str = "none") -> ExactDecimal: ...
def format_percent(value: ExactDecimal, digits: str = "latin", grouping: str = "none") -> str: ...
def ratio_to_percent(value: ExactDecimal) -> ExactDecimal: ...
def percent_to_ratio(value: ExactDecimal) -> ExactDecimal: ...
def format_numeric_range(start: RangeDecimalEndpoint | RangeFractionEndpoint, end: RangeDecimalEndpoint | RangeFractionEndpoint, start_inclusive: bool, end_inclusive: bool, separator: str = "–", digits: str = "latin") -> str: ...
def validate_gregorian_date(year: int, month: int, day: int) -> bool: ...
def parse_gregorian_date(text: str) -> dict[str, int]: ...
def weekday(year: int, month: int, day: int) -> str: ...
def add_gregorian_date(year: int, month: int, day: int, unit: str, amount: int, overflow: str = "reject") -> dict[str, int]: ...
def date_difference(start: dict[str, int], end: dict[str, int]) -> int: ...
def date_interval(start: str, end: str) -> dict[str, Any]: ...
def vakya_solar_transits(saka_year_elapsed: int) -> VakyaSolarYear: ...
def vakya_true_sun_from_mesha_elapsed(elapsed_days: int, nadi: int, vinadi: int) -> VakyaTrueSun: ...
def vakya_true_moon_from_kali_day(kali_day: int) -> VakyaTrueMoon: ...
def vakya_reduce_to_local_true_sunrise(true_position: RasiDmsAngle, daily_motion: DmsAngle, cara_half_vinadi_tenths: int, desantara_vinadi_tenths: int, bhujaantara_vinadi_tenths: int) -> VakyaLocalSunriseReduction: ...
def vakya_cara_from_sayana_sun(sayana_sun: RasiDmsAngle, equinoctial_shadow_tenths: int) -> VakyaCara: ...
def vakya_desantara_from_yojana_distance(east_west_distance_tenths_yojana: int) -> VakyaDesantara: ...
def vakya_bhujaantara_from_true_sun(sun_rasi: int, sun_rasi_progress_arcseconds: int) -> VakyaBhujaantara: ...
def calendar_profile_info(definition_id: str = ...) -> dict[str, Any]: ...
def gregorian_to_tamil_date(date: GregorianDate, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def tamil_to_gregorian_date(date: TamilSolarDate, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def tamil_month_info(solar_year: int, month: int, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def tamil_year_info(solar_year: int, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def tamil_year_cycle_info(solar_year: int, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def calendar_official_holidays(jurisdiction: str, year: int) -> dict[str, Any]: ...
def calendar_observances(gregorian_year: int, context: CalendarContext | VakyaCivilContext, rule_set: str = ..., definition_id: str = ..., month: int | None = ...) -> CalendarObservances: ...
def add_tamil_date(date: TamilSolarDate, unit: str, amount: int, context: CalendarContext | VakyaCivilContext, overflow: str = ..., definition_id: str = ...) -> dict[str, Any]: ...
def panchangam_at(instant_unix_seconds: int, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def panchangam_day(date: GregorianDate, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def lunar_phase_events(start_unix_seconds: int, end_unix_seconds: int, definition_id: str = ...) -> dict[str, Any]: ...
def calendar_daylight_periods(date: GregorianDate, context: CalendarContext | VakyaCivilContext, definition_id: str = ...) -> dict[str, Any]: ...
def format_tamil_date(date: GregorianDate, context: CalendarContext | VakyaCivilContext, script: CalendarDisplayScript = ..., digits: CalendarDisplayDigits = ..., style: CalendarDisplayStyle = ..., definition_id: str = ...) -> str: ...
def calendar_display_info(date: GregorianDate, context: CalendarContext | VakyaCivilContext, script: CalendarDisplayScript = ..., digits: CalendarDisplayDigits = ..., definition_id: str = ...) -> dict[str, Any]: ...
def compare_calendar_profiles(thirukanitham_context: CalendarContext, vakya_context: VakyaCivilContext, *, date: GregorianDate | None = ..., instant_unix_seconds: int | None = ...) -> dict[str, Any]: ...
def thiruvalluvar_year_info(date: GregorianDate, context: CalendarContext, convention_id: str = ...) -> dict[str, Any]: ...
def hyphenate_word(word: str, delimiter: str = ..., left_min: int = ..., right_min: int = ...) -> HyphenationResult: ...
def hyphenation_points(word: str, left_min: int = ..., right_min: int = ...) -> list[HyphenationPoint]: ...
def hyphenate_text(text: str, delimiter: str = ..., left_min: int = ..., right_min: int = ...) -> str: ...
def wrap_text(text: str, max_width: int, delimiter: str = ..., left_min: int = ..., right_min: int = ...) -> WrapResult: ...
def process_docx(input_path: str, output_path: str, left_min: int = ..., right_min: int = ...) -> dict[str, Any]: ...

class Olippasai(TypedDict):
    text: str
    start_byte: int
    end_byte: int
    start_letter_idx: int
    end_letter_idx: int
    has_coda: bool
    coda_count: int

def classify_quantity(letter: str) -> str: ...
def baseline_maathirai(letter: str) -> float: ...
def is_kuril(letter: str) -> bool: ...
def is_nedil(letter: str) -> bool: ...
def is_mei(letter: str) -> bool: ...
def is_otru(letter: str) -> bool: ...
def is_aytham(letter: str) -> bool: ...
def get_cognate(letter: str) -> str | None: ...
def are_cognates(left: str, right: str) -> bool: ...
def get_olippasai(text: str) -> list[Olippasai]: ...

LexiconPackId = Literal["core", "terminology", "names_taxa", "regional"]
LexiconFieldAvailability = Literal["available", "unknown", "not_applicable", "withheld"]
LexiconScopeState = Literal["attested", "unrestricted", "unknown"]
LexiconAcceptanceKind = Literal["accepted_auto_source", "accepted_human"]
LexiconFormRepresentation = Literal["written", "romanization", "ipa"]
LexiconFormRole = Literal["canonical", "variant"]
LexiconComponentKind = Literal["definition", "gloss", "translation", "citation"]
LexiconDirectionality = Literal["directed", "symmetric"]
LexiconEndpointKind = Literal["entry", "sense"]
LexiconLookupStatus = Literal["matched", "not_found"]

class LexiconAcceptance(TypedDict):
    decision_id: str
    kind: LexiconAcceptanceKind
    actor_id: str | None
    method: str | None
    decided_on: str

class LexiconProvenance(TypedDict):
    assertion_id: str
    revision_sha256: str
    source_id: str
    locator: str
    acceptance: LexiconAcceptance

class LexiconScope(TypedDict):
    state: LexiconScopeState
    codes: list[str]
    provenance: list[LexiconProvenance]

class LexiconField(TypedDict):
    availability: LexiconFieldAvailability
    value: str | int | float | bool | None
    convention: str | None
    provenance: list[LexiconProvenance]

class LexiconLabelField(TypedDict):
    availability: LexiconFieldAvailability
    value: str | None
    convention: str | None
    provenance: list[LexiconProvenance]

class LexiconAnnotation(TypedDict):
    property: str
    field: LexiconField

class LexiconForm(TypedDict):
    form_id: str
    representation: LexiconFormRepresentation
    role: LexiconFormRole
    text: str
    convention: str | None
    provenance: list[LexiconProvenance]

class LexiconComponentText(TypedDict):
    text_id: str
    kind: LexiconComponentKind
    language_id: str
    text: str
    provenance: list[LexiconProvenance]

class LexiconExampleText(TypedDict):
    text_id: str
    kind: Literal["example"]
    language_id: str
    text: str
    provenance: list[LexiconProvenance]

class LexiconEndpoint(TypedDict):
    kind: LexiconEndpointKind
    id: str

class LexiconRelation(TypedDict):
    relation_id: str
    code: str
    directionality: LexiconDirectionality
    source: LexiconEndpoint
    target: LexiconEndpoint
    provenance: list[LexiconProvenance]

class LexiconSense(TypedDict):
    sense_id: str
    display_order: int
    parent_sense_id: str | None
    components: list[LexiconComponentText]
    examples: list[LexiconExampleText]
    relations: list[LexiconRelation]
    region: LexiconScope
    register: LexiconLabelField
    annotations: list[LexiconAnnotation]
    provenance: list[LexiconProvenance]

class LexiconEntry(TypedDict):
    entry_id: str
    revision: str
    headword: str
    language_id: str
    part_of_speech: LexiconLabelField
    forms: list[LexiconForm]
    senses: list[LexiconSense]
    region: LexiconScope
    register: LexiconLabelField
    annotations: list[LexiconAnnotation]
    provenance: list[LexiconProvenance]

class LexiconCoverage(TypedDict):
    language_ids: list[str]
    region_codes: list[str]
    register_codes: list[str]
    unknown_region_entries: int

class LexiconPackInfo(TypedDict):
    id: LexiconPackId
    dataset_version: str
    schema_version: Literal[1]
    index_format_version: int
    manifest_sha256: str
    available: Literal[True]
    coverage: LexiconCoverage

class LexiconLookupResponse(TypedDict):
    schema_version: Literal[1]
    status: LexiconLookupStatus
    canonical_query: str
    packs: list[LexiconPackInfo]
    entries: list[LexiconEntry]

def lexicon_lookup(
    text: str,
    *,
    packs: list[str] | None = None,
    region: str | None = None,
    register: str | None = None,
) -> LexiconLookupResponse: ...
def lexicon_packs() -> list[LexiconPackInfo]: ...

LexiconPackTier = Literal["verified_open", "local_historical"]
LexiconTierFilter = Literal["all", "open", "local"]
LexiconProfile = Literal["open-lite", "open", "local", "full"]
LexiconCategory = Literal[
    "dictionary",
    "terminology",
    "phrases",
    "regional",
    "names_taxa",
    "heritage",
    "relations",
]

class LexiconCompactForm(TypedDict):
    role: str
    text: str

class LexiconCompactSense(TypedDict, total=False):
    gloss_ta: str
    gloss_en: str
    definition_ta: str
    definition_en: str
    examples: list[str]
    domain: str
    region: str
    register: str

class _LexiconCompactEntryRequired(TypedDict):
    entry_id: str
    headword: str
    source_id: str
    source_locator: str
    rights_status: str

class LexiconCompactEntry(_LexiconCompactEntryRequired, total=False):
    pos: str
    forms: list[LexiconCompactForm]
    senses: list[LexiconCompactSense]
    domain: str
    region: str
    register: str
    origin_language: str
    pure_tamil_equivalent: str
    standard_equivalent: str
    scientific_name: str
    literary_source: str
    verb_class: str
    transitivity: str
    root_word: str
    etymology_type: str
    dedr_id: str
    sandhi_behavior: str
    animacy_gender: str
    frequency_tier: str
    permalink: str

class LexiconCompactRelation(TypedDict):
    source_headword: str
    target_headword: str
    relation_code: str
    directionality: str
    source_id: str
    source_locator: str

class LexiconCompactPackSummary(TypedDict):
    pack_id: str
    category: LexiconCategory
    index_format_version: int
    schema_version: int
    pack_tier: LexiconPackTier
    rights_status: str
    license: str
    dataset_version: str
    description: str
    entry_count: int
    sense_count: int
    relation_count: int
    distinct_headwords: int
    byte_len: int
    checksum_sha256: str
    has_folded_index: bool
    has_relations: bool
    has_english_index: bool
    source_ids: list[str]
    attribution_notice: str
    domains: list[str]
    regions: list[str]
    registers: list[str]

class LexiconAnnotatedEntry(TypedDict):
    pack_id: str
    pack_tier: LexiconPackTier
    entry: LexiconCompactEntry

class LexiconCompactLookupResult(TypedDict):
    status: LexiconLookupStatus
    query: str
    canonical_query: str
    folded: bool
    searched_packs: list[str]
    total_entries: int
    entries: list[LexiconAnnotatedEntry]

class _LexiconPrefixSearchHitRequired(TypedDict):
    headword: str
    matched_key: str
    packs: list[str]
    pack_tiers: list[LexiconPackTier]
    pos: list[str]
    entry_count: int

class LexiconPrefixSearchHit(_LexiconPrefixSearchHitRequired, total=False):
    preview_gloss: str
    domain: str
    region: str

class _LexiconPrefixSearchResultRequired(TypedDict):
    prefix: str
    canonical_prefix: str
    folded: bool
    searched_packs: list[str]
    hits: list[LexiconPrefixSearchHit]

class LexiconPrefixSearchResult(_LexiconPrefixSearchResultRequired, total=False):
    next_cursor: str
    has_more: bool

class _LexiconFuzzySearchHitRequired(TypedDict):
    headword: str
    distance: int
    packs: list[str]
    pack_tiers: list[LexiconPackTier]
    pos: list[str]

class LexiconFuzzySearchHit(_LexiconFuzzySearchHitRequired, total=False):
    preview_gloss: str

class LexiconFuzzySearchResult(TypedDict):
    query: str
    canonical_query: str
    max_distance: int
    searched_packs: list[str]
    hits: list[LexiconFuzzySearchHit]

class LexiconLongestPrefixResult(TypedDict):
    query: str
    prefixes: list[str]

class LexiconRelationsResult(TypedDict):
    status: LexiconLookupStatus
    query: str
    canonical_query: str
    searched_packs: list[str]
    relations: list[LexiconCompactRelation]

class LexiconStatsResult(TypedDict):
    pack_count: int
    total_entries: int
    total_senses: int
    total_relations: int
    total_bytes: int
    packs: list[LexiconCompactPackSummary]
    category_counts: dict[str, int]
    pos_counts: dict[str, int]
    domain_counts: dict[str, int]
    region_counts: dict[str, int]
    register_counts: dict[str, int]
    has_english_index: bool

class LexiconDownloadResult(TypedDict):
    dest: str
    downloaded: list[str]
    skipped: list[str]
    manifest_url: str

class LexiconLoadPackResult(TypedDict):
    loaded: list[LexiconCompactPackSummary]

class LexiconUnloadPackResult(TypedDict, total=False):
    pack_id: str
    removed: bool
    cleared: bool

class _LexiconWordMeaningRequired(TypedDict):
    text: str
    language: str
    pack_id: str
    category: LexiconCategory
    pack_tier: LexiconPackTier
    rights_status: str

class LexiconWordMeaning(_LexiconWordMeaningRequired, total=False):
    pos: str
    domain: str
    region: str
    register: str

class LexiconWordRelationsGroup(TypedDict):
    synonyms: list[str]
    antonyms: list[str]
    related: list[str]
    hypernyms: list[str]

class _LexiconWordSourceRefRequired(TypedDict):
    pack_id: str
    category: LexiconCategory
    pack_tier: LexiconPackTier
    rights_status: str
    source_id: str
    source_locator: str

class LexiconWordSourceRef(_LexiconWordSourceRefRequired, total=False):
    permalink: str

class _LexiconWordDefinitionRequired(TypedDict):
    status: LexiconLookupStatus
    query: str
    canonical_query: str
    headword: str
    folded: bool
    searched_packs: list[str]
    categories: list[LexiconCategory]
    pos: list[str]
    meanings_en: list[LexiconWordMeaning]
    meanings_ta: list[LexiconWordMeaning]
    examples: list[str]
    variants: list[str]
    domains: list[str]
    regions: list[str]
    registers: list[str]
    standard_equivalents: list[str]
    pure_tamil_equivalents: list[str]
    origin_languages: list[str]
    scientific_names: list[str]
    literary_sources: list[str]
    relations: LexiconWordRelationsGroup
    has_verified_open: bool
    has_local_historical: bool
    entry_count: int
    sources: list[LexiconWordSourceRef]

class LexiconWordDefinition(_LexiconWordDefinitionRequired, total=False):
    matched_headwords: list[str]
    ipa: list[str]
    verb_classes: list[str]
    transitivity: list[str]
    root_words: list[str]
    etymology_types: list[str]
    dedr_ids: list[str]
    sandhi_behaviors: list[str]
    animacy_genders: list[str]
    frequency_tiers: list[str]

class LexiconInitResult(TypedDict):
    directory: str
    profile: LexiconProfile
    pack_count: int
    total_entries: int
    total_senses: int
    total_relations: int
    total_bytes: int
    loaded: list[LexiconCompactPackSummary]

class LexiconSourceBucketResult(TypedDict):
    query: str
    normalized_query: str
    bucket: str

class LexiconSourceRecord(TypedDict):
    source_file: str
    source_row: int
    lookup_key: str
    fields: dict[str, str]

class LexiconSourceBucketPayload(TypedDict):
    schema_version: int
    bucket: str
    records: list[LexiconSourceRecord]

class LexiconSourceLookupResult(TypedDict):
    query: str
    normalized_query: str
    status: LexiconLookupStatus
    data_status: str
    rights_status: str
    total: int
    offset: int
    limit: int
    records: list[LexiconSourceRecord]

DEFAULT_LEXICON_MANIFEST_URL: str

def lexicon_download(
    profile: LexiconProfile | str = ...,
    *,
    packs: list[str] | None = ...,
    dest: str | os.PathLike[str] | None = ...,
    manifest_url: str | None = ...,
    force: bool = ...,
) -> LexiconDownloadResult: ...
def lexicon_init(
    profile: LexiconProfile | str = ...,
    *,
    path: str | os.PathLike[str] | None = ...,
    replace: bool = ...,
    auto_download: bool = ...,
    manifest_url: str | None = ...,
) -> LexiconInitResult: ...
def lexicon_load_pack_bytes(data: bytes | bytearray) -> LexiconCompactPackSummary: ...
def lexicon_load_pack(path: str | os.PathLike[str]) -> LexiconLoadPackResult: ...
def lexicon_unload_pack(pack_id: str | None = ...) -> LexiconUnloadPackResult: ...
def lexicon_stats() -> LexiconStatsResult: ...
def lexicon_define(
    text: str,
    *,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    pos: str | None = ...,
    domain: str | None = ...,
    region: str | None = ...,
    register: str | None = ...,
    folded: bool = ...,
) -> LexiconWordDefinition: ...
def lexicon_query(
    text: str,
    *,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    pos: str | None = ...,
    domain: str | None = ...,
    region: str | None = ...,
    register: str | None = ...,
    folded: bool = ...,
) -> LexiconCompactLookupResult: ...
def lexicon_search(
    prefix: str,
    *,
    limit: int = ...,
    after_key: str | None = ...,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    pos: str | None = ...,
    domain: str | None = ...,
    region: str | None = ...,
    register: str | None = ...,
    folded: bool = ...,
) -> LexiconPrefixSearchResult: ...
def lexicon_search_english(
    query: str,
    *,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    pos: str | None = ...,
    domain: str | None = ...,
    region: str | None = ...,
    register: str | None = ...,
    limit: int = ...,
) -> LexiconPrefixSearchResult: ...
def lexicon_fuzzy_search(
    text: str,
    *,
    max_distance: int = ...,
    limit: int = ...,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    pos: str | None = ...,
    domain: str | None = ...,
    region: str | None = ...,
    register: str | None = ...,
) -> LexiconFuzzySearchResult: ...
def lexicon_longest_prefix(
    text: str,
    *,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
) -> LexiconLongestPrefixResult: ...
def lexicon_relations(
    text: str,
    *,
    packs: list[str] | None = ...,
    tier: LexiconTierFilter | str | None = ...,
    category: LexiconCategory | str | None = ...,
    folded: bool = ...,
) -> LexiconRelationsResult: ...
def lexicon_source_bucket(query: str) -> LexiconSourceBucketResult: ...
def lexicon_source_lookup(
    query: str,
    bucket: LexiconSourceBucketPayload | dict[str, Any],
    *,
    offset: int = ...,
    limit: int = ...,
) -> LexiconSourceLookupResult: ...

PunarchiProfile = Literal["nannool-v1"]
PunarchiChapter = Literal["ezhuttiyal", "padaviyal", "uyireeru", "meyyeeru", "urupu"]
GrammaticalRelation = Literal["unspecified", "vetrumai", "alvazhi"]

class PunarchiContext(TypedDict, total=False):
    relation: GrammaticalRelation
    subtype: str | None
    lexical_class: str | None
    poetic: bool

class DerivationStep(TypedDict):
    sutra: int
    rule_id: str
    stage: int
    transform: Literal["iyalbu", "thonral", "thirithal", "keduthal"]
    before: str
    after: str

class JoinAlternative(TypedDict):
    surface: str
    transform: Literal["iyalbu", "thonral", "thirithal", "keduthal"]
    steps: list[DerivationStep]
    required_context: str | None
    optional_variant: bool
    poetic: bool

class PunarchiJoinResult(TypedDict):
    profile: PunarchiProfile
    surface: str
    transform: Literal["iyalbu", "thonral", "thirithal", "keduthal"]
    steps: list[DerivationStep]
    alternatives: list[JoinAlternative]

class SplitCandidate(TypedDict):
    first: str
    second: str
    sutra: int
    rule_id: str
    transform: Literal["iyalbu", "thonral", "thirithal", "keduthal"]
    steps: list[DerivationStep]
    split_byte: int
    split_unit: int

class SutraInventoryEntry(TypedDict):
    sutra: int
    chapter: PunarchiChapter
    tier: Literal[
        "phonological",
        "closed_class",
        "context_dependent",
        "poetic_closed",
        "definition_or_scope",
    ]
    executable: bool
    tva_page: int
    kandigai_sutra: int
    pm_ref: str
    summary: str
    edition_note: str | None

def punarchi_join(
    first: str,
    second: str,
    *,
    profile: PunarchiProfile = "nannool-v1",
    context: PunarchiContext | None = None,
) -> PunarchiJoinResult: ...
def punarchi_split_candidates(
    surface: str,
    *,
    profile: PunarchiProfile = "nannool-v1",
    poetic: bool = False,
) -> list[SplitCandidate]: ...
def punarchi_rules(
    *,
    profile: PunarchiProfile = "nannool-v1",
    chapter: PunarchiChapter | None = None,
    sutra: int | None = None,
) -> list[SutraInventoryEntry]: ...
