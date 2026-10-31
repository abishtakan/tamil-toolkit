"""Thin adapters: all linguistic behavior executes in the Rust extension."""

import json
from typing import Any

from . import _native

__all__ = ["execute", "get_letters", "normalize_nfc", "normalize_nfd", "split_uyirmei", "compose_uyirmei", "inspect_tamil_string", "compare", "sort_words", "sort_key", "search_key", "to_words", "format_currency", "currency_to_words", "bamini_to_unicode", "unicode_to_bamini", "tscii_bytes_to_unicode", "unicode_to_tscii_bytes", "format_fraction", "fraction_to_words", "fraction_symbol", "format_date"]


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


def tscii_bytes_to_unicode(data: bytes | list[int]) -> str:
    return execute({"op": "tscii_bytes_to_unicode", "input": {"bytes": list(data)}})


def unicode_to_tscii_bytes(text: str) -> bytes:
    return bytes(execute({"op": "unicode_to_tscii_bytes", "input": {"text": text}}))


def format_fraction(numerator: int, denominator: int, digits: str = "latin") -> str:
    return execute({"op": "format_fraction", "input": {"numerator": numerator, "denominator": denominator, "digits": digits}})


def fraction_to_words(numerator: int, denominator: int, locale: str = "TN") -> str:
    return execute({"op": "fraction_to_words", "input": {"numerator": numerator, "denominator": denominator, "locale": locale}})


def fraction_symbol(numerator: int, denominator: int) -> str:
    return execute({"op": "fraction_symbol", "input": {"numerator": numerator, "denominator": denominator}})


def format_date(year: int, month: int, day: int, locale: str = "TN", style: str = "long", digits: str = "latin") -> str:
    return execute({"op": "format_date", "input": {"year": year, "month": month, "day": day, "locale": locale, "style": style, "digits": digits}})
