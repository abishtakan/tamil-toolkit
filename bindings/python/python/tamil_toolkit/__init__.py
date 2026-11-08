"""Thin adapters: all linguistic behavior executes in the Rust extension."""

import json
from typing import Any

from . import _native

__all__ = ["execute", "get_letters", "normalize_nfc", "normalize_nfd", "split_uyirmei", "compose_uyirmei", "inspect_tamil_string", "compare", "sort_words", "sort_key", "search_key", "to_words", "format_currency", "currency_to_words", "bamini_to_unicode", "unicode_to_bamini", "anjal_bytes_to_unicode", "unicode_to_anjal_bytes", "tam_bytes_to_unicode", "unicode_to_tam_bytes", "tab_bytes_to_unicode", "unicode_to_tab_bytes", "tscii_bytes_to_unicode", "unicode_to_tscii_bytes", "lt_tm_codes_to_unicode", "lt_tm_text_to_unicode", "unicode_to_lt_tm_codes", "unicode_to_lt_tm_text", "vanavil_codes_to_unicode", "vanavil_text_to_unicode", "unicode_to_vanavil_codes", "unicode_to_vanavil_text", "detect_encoding", "detect_and_decode", "format_fraction", "fraction_to_words", "fraction_symbol", "format_date", "vakya_solar_transits", "vakya_true_sun_from_mesha_elapsed"]
__all__.append("vakya_true_moon_from_kali_day")
__all__.append("vakya_reduce_to_local_true_sunrise")
__all__.append("vakya_cara_from_sayana_sun")
__all__.append("vakya_desantara_from_yojana_distance")
__all__.append("vakya_bhujaantara_from_true_sun")
__all__ += [
    "format_tamil_date",
    "calendar_display_info",
    "compare_calendar_profiles",
    "thiruvalluvar_year_info",
    "calendar",
    "hyphenate_word",
    "hyphenation_points",
    "hyphenate_text",
    "wrap_text",
    "classify_quantity",
    "baseline_maathirai",
    "is_kuril",
    "is_nedil",
    "is_mei",
    "is_otru",
    "is_aytham",
    "get_cognate",
    "are_cognates",
    "get_olippasai",
]


def execute(request: dict[str, Any]) -> Any:
    return json.loads(_native.execute(json.dumps(request, ensure_ascii=True)))


def get_letters(text: str) -> list[str]:
    return execute({"op": "get_letters", "input": text})


def normalize_nfc(text: str) -> str:
    return execute({"op": "normalize_nfc", "input": text})


def normalize_nfd(text: str) -> str:
    return execute({"op": "normalize_nfd", "input": text})


def split_uyirmei(text: str) -> dict[str, str]:
    return execute({"op": "split_uyirmei", "input": text})


def compose_uyirmei(mei: str, uyir: str) -> str:
    return execute({"op": "compose_uyirmei", "input": {"mei": mei, "uyir": uyir}})


def inspect_tamil_string(text: str) -> dict[str, Any]:
    return execute({"op": "inspect_tamil_string", "input": text})


def classify_quantity(letter: str) -> str:
    return execute({"op": "classify_quantity", "input": letter})


def baseline_maathirai(letter: str) -> float:
    return execute({"op": "baseline_maathirai", "input": letter})


def is_kuril(letter: str) -> bool:
    return classify_quantity(letter) == "kuril"


def is_nedil(letter: str) -> bool:
    return classify_quantity(letter) == "nedil"


def is_mei(letter: str) -> bool:
    return classify_quantity(letter) == "mei"


def is_otru(letter: str) -> bool:
    return is_mei(letter)


def is_aytham(letter: str) -> bool:
    return classify_quantity(letter) == "aytham"


def get_cognate(letter: str) -> str | None:
    return execute({"op": "get_cognate", "input": letter})


def are_cognates(left: str, right: str) -> bool:
    return execute({"op": "are_cognates", "input": {"left": left, "right": right}})


def get_olippasai(text: str) -> list[dict[str, Any]]:
    return execute({"op": "get_olippasai", "input": text})


def compare(left: str, right: str) -> int:
    return execute({"op": "compare", "input": {"left": left, "right": right}})


def sort_words(words: list[str]) -> list[str]:
    return execute({"op": "sort_words", "input": words})


def sort_key(text: str) -> list[int]:
    return execute({"op": "sort_key", "input": text})


def search_key(text: str) -> list[int]:
    return execute({"op": "search_key", "input": text})


def to_words(value: int, locale: str = "TN") -> str:
    return execute({"op": "to_words", "input": {"value": value, "locale": locale}})


def format_currency(amount_minor: int, currency: str, locale: str = "TN") -> str:
    return execute({"op": "format_currency", "input": {"amount_minor": amount_minor, "currency": currency, "locale": locale}})


def currency_to_words(amount_minor: int, currency: str, locale: str = "TN") -> str:
    return execute({"op": "currency_to_words", "input": {"amount_minor": amount_minor, "currency": currency, "locale": locale}})


def bamini_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "bamini_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_bamini(text: str) -> str:
    return execute({"op": "unicode_to_bamini", "input": {"text": text}})


def anjal_bytes_to_unicode(data: bytes | list[int]) -> str:
    return execute({"op": "anjal_bytes_to_unicode", "input": {"bytes": list(data)}})


def unicode_to_anjal_bytes(text: str) -> bytes:
    return bytes(execute({"op": "unicode_to_anjal_bytes", "input": {"text": text}}))


def tam_bytes_to_unicode(data: bytes | list[int]) -> str:
    return execute({"op": "tam_bytes_to_unicode", "input": {"bytes": list(data)}})


def unicode_to_tam_bytes(text: str) -> bytes:
    return bytes(execute({"op": "unicode_to_tam_bytes", "input": {"text": text}}))


def tab_bytes_to_unicode(data: bytes | list[int]) -> str:
    return execute({"op": "tab_bytes_to_unicode", "input": {"bytes": list(data)}})


def unicode_to_tab_bytes(text: str) -> bytes:
    return bytes(execute({"op": "unicode_to_tab_bytes", "input": {"text": text}}))


def tscii_bytes_to_unicode(data: bytes | list[int]) -> str:
    return execute({"op": "tscii_bytes_to_unicode", "input": {"bytes": list(data)}})


def unicode_to_tscii_bytes(text: str) -> bytes:
    return bytes(execute({"op": "unicode_to_tscii_bytes", "input": {"text": text}}))


def lt_tm_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "lt_tm_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def lt_tm_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "lt_tm_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_lt_tm_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_lt_tm_codes", "input": {"text": text}})


def unicode_to_lt_tm_text(text: str) -> str:
    return execute({"op": "unicode_to_lt_tm_text", "input": {"text": text}})


def vanavil_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "vanavil_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def vanavil_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "vanavil_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_vanavil_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_vanavil_codes", "input": {"text": text}})


def unicode_to_vanavil_text(text: str) -> str:
    return execute({"op": "unicode_to_vanavil_text", "input": {"text": text}})


def detect_encoding(data: bytes | bytearray | str | list[int]) -> dict[str, Any]:
    if isinstance(data, (bytes, bytearray)):
        input_payload = {"bytes": list(data)}
    elif isinstance(data, str):
        input_payload = {"text": data}
    elif isinstance(data, list):
        if any(x > 255 for x in data):
            input_payload = {"codes": data}
        else:
            input_payload = {"bytes": data}
    else:
        raise ValueError("data must be bytes, str, or list of ints")
    return execute({"op": "detect_encoding", "input": input_payload})


def detect_and_decode(data: bytes | bytearray | str | list[int]) -> str:
    if isinstance(data, (bytes, bytearray)):
        input_payload = {"bytes": list(data)}
    elif isinstance(data, str):
        input_payload = {"text": data}
    elif isinstance(data, list):
        input_payload = {"bytes": data}
    else:
        raise ValueError("data must be bytes or str")
    return execute({"op": "detect_and_decode", "input": input_payload})


def format_fraction(numerator: int, denominator: int, digits: str = "latin") -> str:
    return execute({"op": "format_fraction", "input": {"numerator": numerator, "denominator": denominator, "digits": digits}})


def fraction_to_words(numerator: int, denominator: int, locale: str = "TN") -> str:
    return execute({"op": "fraction_to_words", "input": {"numerator": numerator, "denominator": denominator, "locale": locale}})


def fraction_symbol(numerator: int, denominator: int) -> str:
    return execute({"op": "fraction_symbol", "input": {"numerator": numerator, "denominator": denominator}})


def format_date(year: int, month: int, day: int, locale: str = "TN", style: str = "long", digits: str = "latin") -> str:
    return execute({"op": "format_date", "input": {"year": year, "month": month, "day": day, "locale": locale, "style": style, "digits": digits}})


__all__ += ["convert_digits", "parse_decimal", "format_decimal", "decimal_to_words",
            "ordinal_to_words", "digit_sequence_to_words", "format_currency_decimal",
            "currency_decimal_to_words", "parse_fraction_symbol", "symbol_info",
            "format_mixed_fraction", "parse_mixed_fraction", "format_traditional_integer",
            "parse_traditional_integer", "parse_percent", "format_percent", "ratio_to_percent",
            "percent_to_ratio", "format_numeric_range", "validate_gregorian_date",
            "parse_gregorian_date", "weekday", "add_gregorian_date", "date_difference", "date_interval"]


def convert_digits(text: str, to: str) -> str:
    return execute({"op": "convert_digits", "input": {"text": text, "to": to}})


def parse_decimal(text: str, source_digits: str, grouping: str = "none", allow_mixed_digits: bool = False) -> dict[str, Any]:
    return execute({"op": "parse_decimal", "input": {"text": text, "source_digits": source_digits, "grouping": grouping, "allow_mixed_digits": allow_mixed_digits}})


def format_decimal(value: dict[str, Any], digits: str = "latin", grouping: str = "none") -> str:
    return execute({"op": "format_decimal", "input": {"value": value, "digits": digits, "grouping": grouping}})


def decimal_to_words(text: str, source_digits: str, locale: str = "TN", grouping: str = "none", allow_mixed_digits: bool = False) -> str:
    return execute({"op": "decimal_to_words", "input": {"text": text, "source_digits": source_digits, "locale": locale, "grouping": grouping, "allow_mixed_digits": allow_mixed_digits}})


def ordinal_to_words(value: int, locale: str = "TN") -> str:
    return execute({"op": "ordinal_to_words", "input": {"value": value, "locale": locale}})


def digit_sequence_to_words(text: str, source_digits: str, locale: str = "TN") -> str:
    return execute({"op": "digit_sequence_to_words", "input": {"text": text, "source_digits": source_digits, "locale": locale}})


def format_currency_decimal(amount: str, source_digits: str, currency: str, locale: str = "TN", grouping: str = "none") -> str:
    return execute({"op": "format_currency_decimal", "input": {"amount": amount, "source_digits": source_digits, "currency": currency, "locale": locale, "grouping": grouping}})


def currency_decimal_to_words(amount: str, source_digits: str, currency: str, locale: str = "TN", grouping: str = "none") -> str:
    return execute({"op": "currency_decimal_to_words", "input": {"amount": amount, "source_digits": source_digits, "currency": currency, "locale": locale, "grouping": grouping}})


def parse_fraction_symbol(text: str) -> dict[str, int]:
    return execute({"op": "parse_fraction_symbol", "input": {"text": text}})


def symbol_info(text: str) -> dict[str, Any]:
    return execute({"op": "symbol_info", "input": {"text": text}})


def format_mixed_fraction(negative: bool, whole: int, numerator: int, denominator: int, digits: str = "latin") -> str:
    return execute({"op": "format_mixed_fraction", "input": {"negative": negative, "whole": whole, "numerator": numerator, "denominator": denominator, "digits": digits}})


def parse_mixed_fraction(text: str, source_digits: str) -> dict[str, Any]:
    return execute({"op": "parse_mixed_fraction", "input": {"text": text, "source_digits": source_digits}})


def format_traditional_integer(value: int) -> str:
    return execute({"op": "format_traditional_integer", "input": {"value": value}})


def parse_traditional_integer(text: str) -> int:
    return execute({"op": "parse_traditional_integer", "input": {"text": text}})


def parse_percent(text: str, source_digits: str, grouping: str = "none") -> dict[str, Any]:
    return execute({"op": "parse_percent", "input": {"text": text, "source_digits": source_digits, "grouping": grouping}})


def format_percent(value: dict[str, Any], digits: str = "latin", grouping: str = "none") -> str:
    return execute({"op": "format_percent", "input": {"value": value, "digits": digits, "grouping": grouping}})


def ratio_to_percent(value: dict[str, Any]) -> dict[str, Any]:
    return execute({"op": "ratio_to_percent", "input": {"value": value}})


def percent_to_ratio(value: dict[str, Any]) -> dict[str, Any]:
    return execute({"op": "percent_to_ratio", "input": {"value": value}})


def format_numeric_range(start: dict[str, Any], end: dict[str, Any], start_inclusive: bool, end_inclusive: bool, separator: str = "–", digits: str = "latin") -> str:
    return execute({"op": "format_numeric_range", "input": {"start": start, "end": end, "start_inclusive": start_inclusive, "end_inclusive": end_inclusive, "separator": separator, "digits": digits}})


def validate_gregorian_date(year: int, month: int, day: int) -> bool:
    return execute({"op": "validate_gregorian_date", "input": {"year": year, "month": month, "day": day}})


def parse_gregorian_date(text: str) -> dict[str, int]:
    return execute({"op": "parse_gregorian_date", "input": {"text": text}})


def weekday(year: int, month: int, day: int) -> str:
    return execute({"op": "weekday", "input": {"year": year, "month": month, "day": day}})


def add_gregorian_date(year: int, month: int, day: int, unit: str, amount: int, overflow: str = "reject") -> dict[str, int]:
    return execute({"op": "add_gregorian_date", "input": {"year": year, "month": month, "day": day, "unit": unit, "amount": amount, "overflow": overflow}})


def date_difference(start: dict[str, int], end: dict[str, int]) -> int:
    return execute({"op": "date_difference", "input": {"start": start, "end": end}})


def date_interval(start: str, end: str) -> dict[str, Any]:
    return execute({"op": "date_interval", "input": {"start": start, "end": end}})


def vakya_solar_transits(saka_year_elapsed: int) -> dict[str, Any]:
    """Return source-pinned 1962 Vakyakarana solar transit arithmetic."""
    return execute({
        "op": "vakya_solar_transits",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-solar-transits-v1",
            "saka_year_elapsed": saka_year_elapsed,
        },
    })


def vakya_true_sun_from_mesha_elapsed(elapsed_days: int, nadi: int, vinadi: int) -> dict[str, Any]:
    """Apply the 1962 Vakyakarana Bhupadi table to time elapsed from Mesha."""
    return execute({
        "op": "vakya_true_sun_from_mesha_elapsed",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-solar-transits-v1",
            "elapsed_days": elapsed_days,
            "nadi": nadi,
            "vinadi": vinadi,
        },
    })


def vakya_true_moon_from_kali_day(kali_day: int) -> dict[str, Any]:
    """Return the 1962 Vakyakarana Candra-vakya true Moon for a Kali day."""
    return execute({
        "op": "vakya_true_moon_from_kali_day",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-true-moon-v1",
            "kali_day": kali_day,
        },
    })


def vakya_reduce_to_local_true_sunrise(
    true_position: dict[str, int],
    daily_motion: dict[str, int],
    cara_half_vinadi_tenths: int,
    desantara_vinadi_tenths: int,
    bhujaantara_vinadi_tenths: int,
) -> dict[str, Any]:
    """Apply the 1962 source's signed local true-sunrise correction."""
    return execute({
        "op": "vakya_reduce_to_local_true_sunrise",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-local-sunrise-v1",
            "true_position": true_position,
            "daily_motion": daily_motion,
            "cara_half_vinadi_tenths": cara_half_vinadi_tenths,
            "desantara_vinadi_tenths": desantara_vinadi_tenths,
            "bhujaantara_vinadi_tenths": bhujaantara_vinadi_tenths,
        },
    })


def vakya_cara_from_sayana_sun(
    sayana_sun: dict[str, int], equinoctial_shadow_tenths: int,
) -> dict[str, Any]:
    """Compute the 1962 Vakyakarana Cara interval from Sayana Sun and shadow."""
    return execute({
        "op": "vakya_cara_from_sayana_sun",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-cara-v1",
            "sayana_sun": sayana_sun,
            "equinoctial_shadow_tenths": equinoctial_shadow_tenths,
        },
    })


def vakya_desantara_from_yojana_distance(
    east_west_distance_tenths_yojana: int,
) -> dict[str, Any]:
    """Convert the 1962 Ujjain yojana distance to Deśāntara vināḍis."""
    return execute({
        "op": "vakya_desantara_from_yojana_distance",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-desantara-v1",
            "east_west_distance_tenths_yojana": east_west_distance_tenths_yojana,
        },
    })


def vakya_bhujaantara_from_true_sun(
    sun_rasi: int, sun_rasi_progress_arcseconds: int,
) -> dict[str, Any]:
    """Interpolate the 1962 Bhujaantara table within a source rasi."""
    return execute({
        "op": "vakya_bhujaantara_from_true_sun",
        "input": {
            "definition_id": "vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1",
            "sun_rasi": sun_rasi,
            "sun_rasi_progress_arcseconds": sun_rasi_progress_arcseconds,
        },
    })


THIRUKANITHAM_DEFINITION = "thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2"
VAKYA_CIVIL_DEFINITION = "vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1"


def calendar_profile_info(definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the selected finite calendar model, coverage, station, and sources."""
    return execute({"op": "calendar_profile_info", "input": {"definition_id": definition_id}})


def gregorian_to_tamil_date(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Convert a Gregorian date with the selected definition and its context."""
    return execute({"op": "gregorian_to_tamil_date", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def tamil_to_gregorian_date(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Convert a solar Tamil date with the selected definition and context."""
    return execute({"op": "tamil_to_gregorian_date", "input": {
        "definition_id": definition_id,
        "date": {"solar_year": date["solar_year"], "month": date["month"], "day": date["day"]},
        "context": context,
    }})


def tamil_month_info(solar_year: int, month: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    return execute({"op": "tamil_month_info", "input": {
        "definition_id": definition_id,
        "solar_year": solar_year, "month": month, "context": context,
    }})


def tamil_year_info(solar_year: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Enumerate all twelve source-profile month intervals in one solar year."""
    return execute({"op": "tamil_year_info", "input": {
        "definition_id": definition_id, "solar_year": solar_year, "context": context,
    }})


def tamil_year_cycle_info(solar_year: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the sourced romanized 60-year title for a supported solar year."""
    return execute({"op": "tamil_year_cycle_info", "input": {
        "definition_id": definition_id, "solar_year": solar_year, "context": context,
    }})


def calendar_official_holidays(jurisdiction: str, year: int) -> dict[str, Any]:
    """Return an authority-published named-holiday schedule for a supported year."""
    return execute({"op": "calendar_official_holidays", "input": {
        "jurisdiction": jurisdiction, "year": year,
    }})


def calendar_observances(
    gregorian_year: int, context: dict[str, Any],
    rule_set: str = "thirukanitham-tamil-named-observances-v1",
    definition_id: str = THIRUKANITHAM_DEFINITION,
    month: int | None = None,
) -> dict[str, Any]:
    """Calculate the named source-limited Tamil Nadu observance subset."""
    return execute({"op": "calendar_observances", "input": {
        "definition_id": definition_id, "rule_set": rule_set,
        "gregorian_year": gregorian_year, "context": context,
        **({"month": month} if month is not None else {}),
    }})


def add_tamil_date(
    date: dict[str, int], unit: str, amount: int, context: dict[str, Any],
    overflow: str = "reject", definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Add days, months, or years using the selected profile's date boundaries."""
    return execute({"op": "add_tamil_date", "input": {
        "definition_id": definition_id,
        "date": {"solar_year": date["solar_year"], "month": date["month"], "day": date["day"]},
        "unit": unit, "amount": amount, "overflow": overflow, "context": context,
    }})


def panchangam_at(instant_unix_seconds: int, context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return the five limb values at an integer Unix UTC second."""
    return execute({"op": "panchangam_at", "input": {
        "definition_id": definition_id,
        "instant_unix_seconds": instant_unix_seconds, "context": context,
    }})


def panchangam_day(date: dict[str, int], context: dict[str, Any], definition_id: str = THIRUKANITHAM_DEFINITION) -> dict[str, Any]:
    """Return rise/set and every limb transition over the local civil day."""
    return execute({"op": "panchangam_day", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def lunar_phase_events(
    start_unix_seconds: int,
    end_unix_seconds: int,
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return bounded Thirukanitham geocentric primary phases in UTC."""
    return execute({"op": "lunar_phase_events", "input": {
        "definition_id": definition_id,
        "start_unix_seconds": start_unix_seconds,
        "end_unix_seconds": end_unix_seconds,
    }})


def calendar_daylight_periods(
    date: dict[str, int], context: dict[str, Any],
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return source-defined weekday intervals within computed daylight."""
    return execute({"op": "calendar_daylight_periods", "input": {
        "definition_id": definition_id, "date": date, "context": context,
    }})


def format_tamil_date(
    date: dict[str, int], context: dict[str, Any], script: str = "tamil",
    digits: str = "latin", style: str = "weekday_day_month_year",
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> str:
    """Format a validated solar date with explicitly selected script and digits."""
    return execute({"op": "format_tamil_date", "input": {
        "definition_id": definition_id, "date": date, "context": context,
        "script": script, "digits": digits, "style": style,
    }})


def calendar_display_info(
    date: dict[str, int], context: dict[str, Any], script: str = "tamil",
    digits: str = "latin",
    definition_id: str = THIRUKANITHAM_DEFINITION,
) -> dict[str, Any]:
    """Return formatted date, year-cycle and panchangam labels with provenance."""
    return execute({"op": "calendar_display_info", "input": {
        "definition_id": definition_id, "date": date, "context": context,
        "script": script, "digits": digits,
    }})


def compare_calendar_profiles(
    thirukanitham_context: dict[str, Any], vakya_context: dict[str, Any], *,
    date: dict[str, int] | None = None,
    instant_unix_seconds: int | None = None,
) -> dict[str, Any]:
    """Compare both declared profiles at one date or one UTC instant."""
    input_value: dict[str, Any] = {
        "thirukanitham_context": thirukanitham_context,
        "vakya_context": vakya_context,
    }
    if date is not None:
        input_value["date"] = date
    if instant_unix_seconds is not None:
        input_value["instant_unix_seconds"] = instant_unix_seconds
    return execute({"op": "compare_calendar_profiles", "input": input_value})


def thiruvalluvar_year_info(
    date: dict[str, int], context: dict[str, Any],
    convention_id: str = "tn-thiruvalluvar-thai1-thirukanitham-v1",
) -> dict[str, Any]:
    """Return the named Thirukanitham Thai-1 era convention, not a Gazette lookup."""
    return execute({"op": "thiruvalluvar_year_info", "input": {
        "convention_id": convention_id, "date": date, "context": context,
    }})


def hyphenate_word(
    word: str,
    delimiter: str = "\u00AD",
    left_min: int = 2,
    right_min: int = 2,
) -> dict[str, Any]:
    """Hyphenate a single Tamil word at valid syllable boundaries."""
    return execute({
        "op": "hyphenate_word",
        "input": {
            "word": word,
            "delimiter": delimiter,
            "left_min": left_min,
            "right_min": right_min,
        },
    })


def hyphenation_points(
    word: str,
    left_min: int = 2,
    right_min: int = 2,
) -> list[dict[str, Any]]:
    """Return valid syllable hyphenation points within a Tamil word."""
    return execute({
        "op": "hyphenation_points",
        "input": {
            "word": word,
            "left_min": left_min,
            "right_min": right_min,
        },
    })


def hyphenate_text(
    text: str,
    delimiter: str = "\u00AD",
    left_min: int = 2,
    right_min: int = 2,
) -> str:
    """Inject soft hyphens into Tamil words across full text or paragraphs."""
    return execute({
        "op": "hyphenate_text",
        "input": {
            "text": text,
            "delimiter": delimiter,
            "left_min": left_min,
            "right_min": right_min,
        },
    })


def wrap_text(
    text: str,
    max_width: int,
    delimiter: str = "-",
    left_min: int = 2,
    right_min: int = 2,
) -> dict[str, Any]:
    """Wrap text to max_width Tamil letters using hyphenation."""
    return execute({
        "op": "wrap_text",
        "input": {
            "text": text,
            "max_width": max_width,
            "delimiter": delimiter,
            "left_min": left_min,
            "right_min": right_min,
        },
    })


def process_docx(
    input_path: str,
    output_path: str,
    left_min: int = 2,
    right_min: int = 2,
) -> dict[str, Any]:
    """Batch-hyphenate an OpenXML Word document (.docx), injecting soft-hyphens into Tamil text runs."""
    return execute({
        "op": "process_docx",
        "input": {
            "input_path": input_path,
            "output_path": output_path,
            "left_min": left_min,
            "right_min": right_min,
        },
    })


from . import calendar
