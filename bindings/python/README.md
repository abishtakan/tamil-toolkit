# tamil-toolkit for Python

Install the experimental MIT-licensed alpha with
`python -m pip install --pre tamil-toolkit`, then import as
`import tamil_toolkit as tamil`. Development builds use `just sync-bindings`.
The package delegates all linguistic behavior to Rust through PyO3.

The SDK includes Unicode normalization and tailored Ezhuthu segmentation,
Mei/Uyir composition, Agara collation, bounded TN/SL integer/currency words,
exact fractions, Gregorian dates, Bamini, and bounded TSCII, TAB, TAM and Anjal
byte conversion. Other
linguistic modules remain planned. Read the bounded contracts at
https://github.com/abishtakan/tamil-toolkit/tree/HEAD/docs/specs.

```python
import tamil_toolkit as tamil

assert tamil.format_fraction(2, 4) == "1/2"
assert tamil.format_currency(102550, "LKR", "SL") == "LKR 1,025.50"
date = tamil.format_date(2024, 2, 29, "SL", "full", "tamil")
```

The alpha targets GIL-enabled CPython 3.11+ through abi3 wheels. Linux x64, Windows x64,
and macOS arm64 wheels require their artifact CI jobs to pass before release.
Source builds require Rust 1.85+. APIs may change before stability.
See LICENSE, THIRD_PARTY_NOTICES.md, and bundled dependency license notices.

Collation APIs: `compare(left, right)`, `sort_words(words)`, `sort_key(text)`,
and `search_key(text)`. Keys are numeric arrays for the versioned `agara-v1`
profile; compare arrays lexicographically and retain the version with indexes.
Sorting preserves original text and canonical ties. See the linked specifications.

This distribution provides `tscii_bytes_to_unicode(bytes([0xba, 0xa2, 0xc5, 0xfd]))`.

`unicode_to_tscii_bytes(text)` returns Python `bytes`.

This distribution provides `tab_bytes_to_unicode(data)` and `unicode_to_tab_bytes(text)`.

This distribution provides `tam_bytes_to_unicode(data)` and `unicode_to_tam_bytes(text)`; TAM bytes do not preserve Latin letters.

This distribution provides `anjal_bytes_to_unicode(data)` and `unicode_to_anjal_bytes(text)`; ambiguous legacy bytes raise an error.
