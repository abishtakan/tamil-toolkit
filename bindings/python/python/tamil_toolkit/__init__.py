"""Thin adapters: all linguistic behavior executes in the Rust extension."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal, TypedDict
import urllib.parse
import urllib.request

from . import _native

__all__ = ["execute", "get_letters", "normalize_nfc", "normalize_nfd", "repair_tamil_text", "fold_for_search", "split_uyirmei", "compose_uyirmei", "inspect_tamil_string", "compare", "sort_words", "sort_key", "search_key", "to_words", "format_currency", "currency_to_words", "bamini_to_unicode", "unicode_to_bamini", "anjal_bytes_to_unicode", "unicode_to_anjal_bytes", "tam_bytes_to_unicode", "unicode_to_tam_bytes", "tab_bytes_to_unicode", "unicode_to_tab_bytes", "tscii_bytes_to_unicode", "unicode_to_tscii_bytes", "lt_tm_codes_to_unicode", "lt_tm_text_to_unicode", "unicode_to_lt_tm_codes", "unicode_to_lt_tm_text", "vanavil_codes_to_unicode", "vanavil_text_to_unicode", "unicode_to_vanavil_codes", "unicode_to_vanavil_text", "senthamil_codes_to_unicode", "senthamil_text_to_unicode", "unicode_to_senthamil_codes", "unicode_to_senthamil_text", "shree_tam_codes_to_unicode", "shree_tam_text_to_unicode", "unicode_to_shree_tam_codes", "unicode_to_shree_tam_text", "softview_codes_to_unicode", "softview_text_to_unicode", "unicode_to_softview_codes", "unicode_to_softview_text", "tbo_codes_to_unicode", "tbo_text_to_unicode", "unicode_to_tbo_codes", "unicode_to_tbo_text", "unicode_to_braille", "braille_to_unicode", "detect_encoding", "detect_and_decode", "format_fraction", "fraction_to_words", "fraction_symbol", "format_date", "vakya_solar_transits", "vakya_true_sun_from_mesha_elapsed"]
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
    "lexicon_lookup",
    "lexicon_packs",
    "lexicon_init",
    "lexicon_download",
    "lexicon_load_pack_bytes",
    "lexicon_load_pack",
    "lexicon_unload_pack",
    "lexicon_stats",
    "lexicon_define",
    "lexicon_query",
    "lexicon_search",
    "lexicon_search_english",
    "lexicon_fuzzy_search",
    "lexicon_longest_prefix",
    "lexicon_relations",
    "lexicon_source_bucket",
    "lexicon_source_lookup",
    "punarchi_join",
    "punarchi_split_candidates",
    "punarchi_rules",
]


def execute(request: dict[str, Any]) -> Any:
    return json.loads(_native.execute(json.dumps(request, ensure_ascii=True)))


__all__ += ["tokenize_words", "segment_sentences", "TokenizationSpan", "WordToken", "StopwordProfile"]


StopwordProfile = Literal["none", "conservative", "broad"]


class TokenizationSpan(TypedDict):
    text: str
    start_byte: int
    end_byte: int
    start_unit: int
    end_unit: int


class WordToken(TokenizationSpan):
    kind: Literal["abbreviation", "word", "number", "other"]


def tokenize_words(text: str, *, stopword_profile: StopwordProfile = "none") -> list[WordToken]:
    return execute({"op": "tokenize_words", "input": {"text": text, "stopword_profile": stopword_profile}})


def segment_sentences(text: str) -> list[TokenizationSpan]:
    return execute({"op": "segment_sentences", "input": {"text": text}})


def get_letters(text: str) -> list[str]:
    return execute({"op": "get_letters", "input": text})


def normalize_nfc(text: str) -> str:
    return execute({"op": "normalize_nfc", "input": text})


def normalize_nfd(text: str) -> str:
    return execute({"op": "normalize_nfd", "input": text})


def repair_tamil_text(text: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    input_payload: dict[str, Any] = {"text": text}
    if options is not None:
        input_payload["options"] = options
    return execute({"op": "repair_tamil_text", "input": input_payload})


def fold_for_search(text: str, profile: str = "comprehensive") -> str:
    return execute({"op": "fold_for_search", "input": {"text": text, "profile": profile}})


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


def compare(left: str, right: str, profile: str = "agara-v1") -> int:
    return execute({"op": "compare", "input": {"left": left, "right": right, "profile": profile}})


def sort_words(words: list[str], profile: str = "agara-v1") -> list[str]:
    return execute({"op": "sort_words", "input": {"words": words, "profile": profile}})


def sort_key(text: str, profile: str = "agara-v1") -> list[int]:
    return execute({"op": "sort_key", "input": {"text": text, "profile": profile}})


def search_key(text: str, profile: str = "agara-v1") -> list[int]:
    return execute({"op": "search_key", "input": {"text": text, "profile": profile}})


def folded_search_key(text: str, profile: str = "comprehensive", collate_profile: str = "agara-v1") -> list[int]:
    return execute({"op": "folded_search_key", "input": {"text": text, "fold_profile": profile, "collate_profile": collate_profile}})


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


def senthamil_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "senthamil_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def senthamil_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "senthamil_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_senthamil_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_senthamil_codes", "input": {"text": text}})


def unicode_to_senthamil_text(text: str) -> str:
    return execute({"op": "unicode_to_senthamil_text", "input": {"text": text}})


def shree_tam_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "shree_tam_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def shree_tam_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "shree_tam_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_shree_tam_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_shree_tam_codes", "input": {"text": text}})


def unicode_to_shree_tam_text(text: str) -> str:
    return execute({"op": "unicode_to_shree_tam_text", "input": {"text": text}})


def softview_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "softview_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def softview_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "softview_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_softview_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_softview_codes", "input": {"text": text}})


def unicode_to_softview_text(text: str) -> str:
    return execute({"op": "unicode_to_softview_text", "input": {"text": text}})


def tbo_codes_to_unicode(codes: list[int], errors: str = "strict") -> str:
    return execute({"op": "tbo_codes_to_unicode", "input": {"codes": list(codes), "errors": errors}})


def tbo_text_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "tbo_text_to_unicode", "input": {"text": text, "errors": errors}})


def unicode_to_tbo_codes(text: str) -> list[int]:
    return execute({"op": "unicode_to_tbo_codes", "input": {"text": text}})


def unicode_to_tbo_text(text: str) -> str:
    return execute({"op": "unicode_to_tbo_text", "input": {"text": text}})


def unicode_to_braille(text: str, errors: str = "strict") -> str:
    return execute({"op": "unicode_to_braille", "input": {"text": text, "errors": errors}})


def braille_to_unicode(text: str, errors: str = "strict") -> str:
    return execute({"op": "braille_to_unicode", "input": {"text": text, "errors": errors}})


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
            "format_mixed_fraction", "parse_mixed_fraction", "mixed_fraction_to_words",
            "words_to_number", "transliterate", "transliterate_schemes", "transliterate_suggest", "format_traditional_integer",
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


def mixed_fraction_to_words(negative: bool, whole: int, numerator: int, denominator: int, locale: str = "TN") -> str:
    return execute({"op": "mixed_fraction_to_words", "input": {"negative": negative, "whole": whole, "numerator": numerator, "denominator": denominator, "locale": locale}})


def words_to_number(text: str, locale: str = "TN") -> int:
    return execute({"op": "words_to_number", "input": {"text": text, "locale": locale}})


def transliterate(text: str, scheme: str, direction: str = "to_tamil") -> str:
    return execute({"op": "transliterate", "input": {"text": text, "scheme": scheme, "direction": direction}})


def transliterate_schemes() -> list[dict[str, Any]]:
    return execute({"op": "transliterate_schemes", "input": {}})


def transliterate_suggest(text: str, scheme: str = "phonetic-v1", limit: int = 5) -> list[str]:
    return execute({"op": "transliterate_suggest", "input": {"text": text, "scheme": scheme, "limit": limit}})


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


def lexicon_lookup(
    text: str,
    *,
    packs: list[str] | None = None,
    region: str | None = None,
    register: str | None = None,
) -> dict[str, Any]:
    """Look up a Tamil word in compiled embedded lexicon packs."""
    request: dict[str, Any] = {"op": "lexicon_lookup", "input": text}
    if packs is not None:
        request["packs"] = packs
    if region is not None:
        request["region"] = region
    if register is not None:
        request["register"] = register
    return execute(request)


def lexicon_packs() -> list[dict[str, Any]]:
    """Return metadata for compiled lexicon packs available in this build."""
    return execute({"op": "lexicon_packs", "input": None})


def _lexicon_scope_request(
    op: str,
    text: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    folded: bool | None = None,
    limit: int | None = None,
    after_key: str | None = None,
    max_distance: int | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {"op": op, "input": text}
    if limit is not None:
        request["limit"] = limit
    if after_key is not None:
        request["after_key"] = after_key
    if max_distance is not None:
        request["max_distance"] = max_distance
    if packs is not None:
        request["packs"] = packs
    if tier is not None:
        request["tier"] = tier
    if category is not None:
        request["category"] = category
    if pos is not None:
        request["pos"] = pos
    if domain is not None:
        request["domain"] = domain
    if region is not None:
        request["region"] = region
    if register is not None:
        request["register"] = register
    if folded is not None:
        request["folded"] = folded
    return request


DEFAULT_LEXICON_MANIFEST_URL = (
    "https://github.com/abishtakan/tamil-toolkit/releases/latest/download/MANIFEST.json"
)
_OPEN_LITE_PACK_IDS = frozenset({"core", "names_taxa", "regional"})


def _default_lexicon_dir() -> Path:
    env_dir = os.environ.get("TAMIL_LEXICON_DIR", "").strip()
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".tamil-toolkit" / "lexicon-packs"


def _default_lexicon_manifest_url() -> str:
    env_url = os.environ.get("TAMIL_LEXICON_MANIFEST_URL", "").strip()
    return env_url or DEFAULT_LEXICON_MANIFEST_URL


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest_relpath(rel_file: str) -> Path:
    normalized = rel_file.replace("\\", "/").lstrip("/")
    rel_path = Path(normalized)
    if not normalized or rel_path.is_absolute() or ".." in rel_path.parts:
        raise ValueError(f"lexicon: invalid manifest pack file path '{rel_file}'")
    return rel_path


def _select_manifest_packs(
    manifest_packs: list[dict[str, Any]],
    profile: str,
    packs: list[str] | None,
) -> list[dict[str, Any]]:
    if packs is not None:
        by_id = {
            str(entry["summary"]["pack_id"]): entry
            for entry in manifest_packs
            if isinstance(entry, dict) and isinstance(entry.get("summary"), dict)
        }
        selected: list[dict[str, Any]] = []
        seen: set[str] = set()
        for pack_id in packs:
            if pack_id in seen:
                continue
            seen.add(pack_id)
            if pack_id not in by_id:
                raise ValueError(f"lexicon: unknown pack '{pack_id}'")
            selected.append(by_id[pack_id])
        return selected

    norm = profile.strip().lower().replace("_", "-")
    if norm in ("open-lite", "lite"):
        return [e for e in manifest_packs if e["summary"].get("pack_id") in _OPEN_LITE_PACK_IDS]
    if norm in ("open", "verified", "verified-open"):
        return [e for e in manifest_packs if e["summary"].get("pack_tier") == "verified_open"]
    if norm in ("local", "local-historical"):
        return [e for e in manifest_packs if e["summary"].get("pack_tier") == "local_historical"]
    if norm in ("full", "all"):
        return list(manifest_packs)
    raise ValueError(f"lexicon: unknown profile '{profile}'")


def _fetch_bytes(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https", "file"):
        raise ValueError(f"lexicon: unsupported URL scheme '{parsed.scheme}'")
    req = urllib.request.Request(url, headers={"User-Agent": "tamil-toolkit-python"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def lexicon_download(
    profile: str = "open",
    *,
    packs: list[str] | None = None,
    dest: str | os.PathLike[str] | None = None,
    manifest_url: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Download and SHA-256-verify `.tlpack` bundles from an official or custom manifest."""
    dest_path = Path(os.fspath(dest)) if dest is not None else _default_lexicon_dir()
    resolved_manifest_url = manifest_url or _default_lexicon_manifest_url()
    manifest_bytes = _fetch_bytes(resolved_manifest_url)
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    manifest_packs = manifest.get("packs")
    if not isinstance(manifest_packs, list):
        raise ValueError("lexicon: manifest missing 'packs' list")

    selected = _select_manifest_packs(manifest_packs, profile, packs)
    dest_path.mkdir(parents=True, exist_ok=True)

    downloaded: list[str] = []
    skipped: list[str] = []
    for entry in selected:
        summary = entry["summary"]
        pack_id = str(summary["pack_id"])
        expected_sha = str(summary["checksum_sha256"]).lower()
        if not expected_sha:
            raise ValueError(f"lexicon: manifest entry '{pack_id}' missing checksum_sha256")
        rel_path = _validate_manifest_relpath(str(entry["file"]))
        target_path = dest_path / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not force and target_path.is_file():
            if _sha256_file(target_path).lower() == expected_sha:
                skipped.append(pack_id)
                continue

        pack_url = entry.get("url") or urllib.parse.urljoin(
            resolved_manifest_url, rel_path.as_posix()
        )
        parsed = urllib.parse.urlparse(pack_url)
        if parsed.scheme not in ("http", "https", "file"):
            raise ValueError(f"lexicon: unsupported URL scheme '{parsed.scheme}'")

        tmp_path = target_path.with_name(f"{target_path.name}.tmp")
        digest = hashlib.sha256()
        try:
            req = urllib.request.Request(pack_url, headers={"User-Agent": "tamil-toolkit-python"})
            with urllib.request.urlopen(req, timeout=120) as resp, tmp_path.open("wb") as out:
                while chunk := resp.read(65536):
                    digest.update(chunk)
                    out.write(chunk)
            actual_sha = digest.hexdigest().lower()
            if actual_sha != expected_sha:
                raise ValueError(
                    f"lexicon: SHA-256 mismatch for '{pack_id}': "
                    f"expected {expected_sha}, got {actual_sha}"
                )
            os.replace(tmp_path, target_path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
        downloaded.append(pack_id)

    manifest_tmp = dest_path / "MANIFEST.json.tmp"
    manifest_target = dest_path / "MANIFEST.json"
    try:
        manifest_tmp.write_bytes(manifest_bytes)
        os.replace(manifest_tmp, manifest_target)
    except Exception:
        manifest_tmp.unlink(missing_ok=True)
        raise

    return {
        "dest": str(dest_path),
        "downloaded": downloaded,
        "skipped": skipped,
        "manifest_url": resolved_manifest_url,
    }


def lexicon_init(
    profile: str = "full",
    *,
    path: str | os.PathLike[str] | None = None,
    replace: bool = True,
    auto_download: bool = False,
    manifest_url: str | None = None,
) -> dict[str, Any]:
    """Initialize the runtime lexicon registry from a named profile and pack directory."""
    payload: dict[str, Any] = {"profile": profile, "replace": replace}
    if path is not None:
        resolved_path = os.fspath(path)
        if auto_download and Path(resolved_path).is_file():
            raise ValueError(f"lexicon: pack directory not found: '{resolved_path}'")
        payload["path"] = resolved_path

    try:
        return execute({"op": "lexicon_init", "input": payload})
    except ValueError as err:
        if not auto_download:
            raise
        msg = str(err)
        recoverable = (
            "no pack directory found" in msg
            or "pack directory not found" in msg
            or "no packs matching profile" in msg
        )
        if not recoverable:
            raise
        dl = lexicon_download(
            profile=profile or "open",
            dest=path,
            manifest_url=manifest_url,
        )
        payload["path"] = dl["dest"]
        return execute({"op": "lexicon_init", "input": payload})


def lexicon_load_pack_bytes(data: bytes | bytearray) -> dict[str, Any]:
    """Load a `.tlpack` v1 or v2 binary image from bytes into the runtime registry."""
    if isinstance(data, bytearray):
        raw = bytes(data)
    elif isinstance(data, bytes):
        raw = data
    else:
        raise TypeError("data must be bytes or bytearray")
    return json.loads(_native.load_lexicon_pack_bytes(raw))


def lexicon_load_pack(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Load a `.tlpack` file or directory of packs into the runtime registry."""
    resolved = os.fspath(path) if isinstance(path, os.PathLike) else path
    if not isinstance(resolved, str):
        raise TypeError("path must be a str or os.PathLike[str]")
    return execute({"op": "lexicon_load_pack", "input": {"path": resolved}})


def lexicon_unload_pack(pack_id: str | None = None) -> dict[str, Any]:
    """Unmount one runtime pack by pack_id, or clear all runtime packs when None."""
    return execute({"op": "lexicon_unload_pack", "input": pack_id})


def lexicon_stats() -> dict[str, Any]:
    """Return runtime pack counts, entry/sense/relation totals, and loaded pack summaries."""
    return execute({"op": "lexicon_stats", "input": None})


def lexicon_define(
    text: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    folded: bool = False,
) -> dict[str, Any]:
    """Build a unified, deduplicated word definition across mounted runtime lexicon packs."""
    return execute(
        _lexicon_scope_request(
            "lexicon_define",
            text,
            packs=packs,
            tier=tier,
            category=category,
            pos=pos,
            domain=domain,
            region=region,
            register=register,
            folded=folded,
        )
    )


def lexicon_query(
    text: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    folded: bool = False,
) -> dict[str, Any]:
    """Query compact runtime lexicon entries with optional scope filters and Mayangoli folding."""
    return execute(
        _lexicon_scope_request(
            "lexicon_query",
            text,
            packs=packs,
            tier=tier,
            category=category,
            pos=pos,
            domain=domain,
            region=region,
            register=register,
            folded=folded,
        )
    )


def lexicon_search(
    prefix: str,
    *,
    limit: int = 25,
    after_key: str | None = None,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    folded: bool = False,
) -> dict[str, Any]:
    """Run FST prefix search across mounted runtime lexicon packs."""
    return execute(
        _lexicon_scope_request(
            "lexicon_search",
            prefix,
            limit=limit,
            after_key=after_key,
            packs=packs,
            tier=tier,
            category=category,
            pos=pos,
            domain=domain,
            region=region,
            register=register,
            folded=folded,
        )
    )


def lexicon_search_english(
    query: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    """Search mounted runtime lexicon packs by English gloss/definition keywords."""
    input_payload: dict[str, Any] = {"query": query, "limit": limit}
    if packs is not None:
        input_payload["packs"] = packs
    if tier is not None:
        input_payload["tier"] = tier
    if category is not None:
        input_payload["category"] = category
    if pos is not None:
        input_payload["pos"] = pos
    if domain is not None:
        input_payload["domain"] = domain
    if region is not None:
        input_payload["region"] = region
    if register is not None:
        input_payload["register"] = register
    return execute({"op": "lexicon_search_english", "input": input_payload})


def lexicon_fuzzy_search(
    text: str,
    *,
    max_distance: int = 1,
    limit: int = 10,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    pos: str | None = None,
    domain: str | None = None,
    region: str | None = None,
    register: str | None = None,
) -> dict[str, Any]:
    """Run bounded Damerau-Levenshtein fuzzy search across mounted runtime lexicon packs."""
    return execute(
        _lexicon_scope_request(
            "lexicon_fuzzy_search",
            text,
            max_distance=max_distance,
            limit=limit,
            packs=packs,
            tier=tier,
            category=category,
            pos=pos,
            domain=domain,
            region=region,
            register=register,
        )
    )


def lexicon_longest_prefix(
    text: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Return exact FST keys that are char-boundary prefixes of text, longest-first."""
    return execute(
        _lexicon_scope_request(
            "lexicon_longest_prefix",
            text,
            packs=packs,
            tier=tier,
            category=category,
        )
    )


def lexicon_relations(
    text: str,
    *,
    packs: list[str] | None = None,
    tier: str | None = None,
    category: str | None = None,
    folded: bool = False,
) -> dict[str, Any]:
    """Query indexed lexical relations for a Tamil headword across mounted packs."""
    return execute(
        _lexicon_scope_request(
            "lexicon_relations",
            text,
            packs=packs,
            tier=tier,
            category=category,
            folded=folded,
        )
    )


def lexicon_source_bucket(query: str) -> dict[str, Any]:
    """Compute the normalized SHA-256 bucket key for an owner-supplied source record query."""
    return execute({"op": "lexicon_source_bucket", "input": query})


def lexicon_source_lookup(
    query: str,
    bucket: dict[str, Any],
    *,
    offset: int = 0,
    limit: int = 25,
) -> dict[str, Any]:
    """Look up paginated owner-supplied historical source records within a validated bucket."""
    return execute({
        "op": "lexicon_source_lookup",
        "input": {
            "query": query,
            "bucket": bucket,
            "offset": offset,
            "limit": limit,
        },
    })


def punarchi_join(
    first: str,
    second: str,
    *,
    profile: str = "nannool-v1",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join two Tamil morphemes or words under the named Punarchi profile."""
    return execute({
        "op": "punarchi_join",
        "input": {
            "first": first,
            "second": second,
            "profile": profile,
            **({} if context is None else {"context": context}),
        },
    })


def punarchi_split_candidates(
    surface: str,
    *,
    profile: str = "nannool-v1",
    poetic: bool = False,
) -> list[dict[str, Any]]:
    """Return dual-pruned single-boundary Punarchi split candidates for a surface form."""
    return execute({
        "op": "punarchi_split_candidates",
        "input": {
            "surface": surface,
            "profile": profile,
            "poetic": poetic,
        },
    })


def punarchi_rules(
    *,
    profile: str = "nannool-v1",
    chapter: str | None = None,
    sutra: int | None = None,
) -> list[dict[str, Any]]:
    """Return Nannool sutra inventory entries matching optional chapter/sutra filters."""
    return execute({
        "op": "punarchi_rules",
        "input": {
            "profile": profile,
            **({} if chapter is None else {"chapter": chapter}),
            **({} if sutra is None else {"sutra": sutra}),
        },
    })


from . import calendar
