# Tamil numerals v0.4: Diaspora currencies, colloquial mixed fractions & formal ITN

Status: Phase 6 engineering contract (2026-11-22). Additive on top of
`numerals-v0.1`, `numerals-v0.2`, and `numerals-v0.3`. Existing `INR`/`LKR`
outputs, integer/decimal/fraction/date operations, and error precedence remain
byte-for-byte unchanged, except that `"USD"` is now a supported currency (the
v0.1 unknown-currency negative fixture uses `"ZZZ"`).

## 1. Diaspora currencies (`SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`)

`Currency` is extended from `{INR, LKR}` to `{INR, LKR, SGD, MYR, USD, EUR, GBP, CAD}`.
All four currency operations (`format_currency`, `currency_to_words`,
`format_currency_decimal`, `currency_decimal_to_words`) accept all eight ISO 4217
codes across both `TN` and `SL` formal profiles.

Declarative labels and grouping live in `lexicon/numerals-v04.toml` (compiled at
build time into static tables; `lexicon/numerals.toml` remains unchanged for
v0.1 CLDR rule-table verification):

| Code | Grouping | Factor | Major label (Tamil) | Minor label (Tamil) |
| --- | --- | ---: | --- | --- |
| `INR` | 3-2 (Indian) | 100 | `\u0BB0\u0BC2\u0BAA\u0BBE\u0BAF\u0BCD` (ரூபாய்) | `\u0BAA\u0BC8\u0B9A\u0BBE` (பைசா) |
| `LKR` | 3-2 (Indian) | 100 | `\u0BB0\u0BC2\u0BAA\u0BBE` (ரூபா) | `\u0B9A\u0BA4\u0BAE\u0BCD` (சதம்) |
| `SGD` | 3-3 (International) | 100 | `\u0B9A\u0BBF\u0B99\u0BCD\u0B95\u0BAA\u0BCD\u0BAA\u0BC2\u0BB0\u0BCD \u0B9F\u0BBE\u0BB2\u0BB0\u0BCD` | `\u0B9A\u0BC6\u0BA9\u0BCD\u0B9F\u0BCD` |
| `MYR` | 3-3 (International) | 100 | `\u0BAE\u0BB2\u0BC7\u0B9A\u0BBF\u0BAF \u0BB0\u0BBF\u0B99\u0BCD\u0B95\u0BBF\u0B9F\u0BCD` | `\u0B9A\u0BC6\u0BA9\u0BCD` |
| `USD` | 3-3 (International) | 100 | `\u0B85\u0BAE\u0BC6\u0BB0\u0BBF\u0B95\u0BCD\u0B95 \u0B9F\u0BBE\u0BB2\u0BB0\u0BCD` | `\u0B9A\u0BC6\u0BA9\u0BCD\u0B9F\u0BCD` |
| `EUR` | 3-3 (International) | 100 | `\u0BAF\u0BC2\u0BB0\u0BCB` | `\u0B9A\u0BC6\u0BA9\u0BCD\u0B9F\u0BCD` |
| `GBP` | 3-3 (International) | 100 | `\u0BAA\u0BBF\u0BB0\u0BBF\u0B9F\u0BCD\u0B9F\u0BBF\u0BB7\u0BCD \u0BAA\u0BB5\u0BC1\u0BA3\u0BCD\u0B9F\u0BCD` | `\u0BAA\u0BC6\u0BA9\u0BCD\u0BB8\u0BCD` |
| `CAD` | 3-3 (International) | 100 | `\u0B95\u0BA9\u0B9F\u0BBF\u0BAF \u0B9F\u0BBE\u0BB2\u0BB0\u0BCD` | `\u0B9A\u0BC6\u0BA9\u0BCD\u0B9F\u0BCD` |

- `format_currency` emits `CODE [-]grouped_major.minor` with exactly two decimal
  places and each currency's declared grouping (`3-2` for `INR`/`LKR`, `3-3` for
  diaspora currencies).
- `currency_to_words` uses the existing CLDR 49 `%spellout-cardinal` major and
  minor words joined with each currency's invariant major/minor label.
- Unknown currency codes (such as `"ZZZ"`, `"inr"`, `""`, `null`) continue to
  fail with `"unsupported currency"`.

## 2. Colloquial mixed fraction words (`mixed_fraction_to_words`)

Operation: `mixed_fraction_to_words { negative, whole, numerator, denominator, locale? } -> string`.

- Validation order: validate `MixedFraction` (`validate_mixed_fraction` ->
  `"invalid mixed fraction"`), then validate `locale` (`"TN"` default, `"TN"` or
  `"SL"` -> `"unsupported locale"`).
- When `numerator == 0`: delegates to `to_words(signed_whole, locale)`.
- When `whole == 0`: delegates to `fraction_to_words(Fraction::new(signed_numerator, denominator), locale)`
  (`1/4` -> `கால்`, `1/2` -> `அரை`, `3/4` -> `முக்கால்`, other proper fractions ->
  `<num> வகுத்தல் <den>`).
- When `whole > 0` and `(numerator, denominator)` is `(1, 4)`, `(1, 2)`, or `(3, 4)`:
  compounds `to_words(whole, locale)` with the declarative ending rules in
  `lexicon/numerals-v04.toml`:
  - Ending in `\u0BC1` (e.g. `ஒன்று`, `இரண்டு`, `பத்து`, `நூறு`): strip `\u0BC1`
    and append `\u0BC7\u0B95\u0BBE\u0BB2\u0BCD` (`-ஏகால்`), `\u0BB0\u0BC8` (`-அரை`),
    or `\u0BC7\u0BAE\u0BC1\u0B95\u0BCD\u0B95\u0BBE\u0BB2\u0BCD` (`-ஏமுக்கால்`) ->
    `ஒன்றேகால்`, `ஒன்றரை`, `ஒன்றேமுக்கால்`, `இரண்டரை`, `நூறரை`.
  - Ending in `\u0BAE\u0BCD` (e.g. `தொள்ளாயிரம்`, `ஆயிரம்`, `ஒரு லட்சம்`/`ஒரு இலட்சம்`):
    strip `\u0BAE\u0BCD` and append `த்தேகால்` / `த்தரை` / `த்தேமுக்கால்` ->
    `ஆயிரத்தரை`, `ஒரு லட்சத்தேகால்`, `ஒரு இலட்சத்தரை`.
  - Ending in `\u0BBF` (e.g. `ஒரு கோடி`): keep `\u0BBF` and append
    `யேகால்` / `யரை` / `யேமுக்கால்` -> `ஒரு கோடியரை`, `ஒரு கோடியேகால்`.
- When `whole > 0` and `(numerator, denominator)` is any other reduced proper
  fraction: emits `<whole_words> \u0BAE\u0BB1\u0BCD\u0BB1\u0BC1\u0BAE\u0BCD <fraction_words>`
  (using `மற்றும்`).
- Negative mixed fractions prepend a single CLDR negative prefix (`எதிர்ம `) to
  the compound magnitude (`-1 1/2` -> `எதிர்ம ஒன்றரை`). Output is NFC.

## 3. Formal reverse word-to-number parsing / ITN (`words_to_number`)

Operation: `words_to_number { text, locale? } -> i64`.

- Exact, deterministic inverse of `to_words` over `-999,999,999..=999,999,999`
  for the declared `TN` and `SL` CLDR 49 `%spellout-numbering` profiles.
- Input `text` must be a JSON string (missing/non-string ->
  `"expected a string input"`). `locale` defaults to `"TN"` (invalid ->
  `"unsupported locale"`).
- Input is NFC-normalized before parsing; NFD equivalent spellings are accepted.
- Leading/trailing whitespace, empty strings, doubled spaces, negative zero
  (`எதிர்ம பூஜ்யம்`), cross-locale stems (`இலட்சம்` under `TN` or `லட்சம்` under
  `SL`), cardinal-only forms (`ஒரு`, `பதினொரு`), out-of-order place values,
  and out-of-range words fail with `"invalid Tamil number words"`.
- Canonical round-trip invariant: `words_to_number(text, locale)` returns `Ok(n)`
  if and only if `n` is in `-999,999,999..=999,999,999` and
  `to_words(n, locale) == Ok(normalize_nfc(text))`.

## Sources

- CLDR 49 `common/main/ta.xml` and `common/rbnf/ta.xml` (Unicode-3.0).
- Frozen independent ICU4J 79.1 outputs in `tests/reference/numerals-v0.1/`.
- Formal Tamil grammar / standard Singapore & Malaysia Tamil currency usage.
