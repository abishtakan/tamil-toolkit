# Tamil numerals completion: exact strings and civil arithmetic

Status: additive engineering contract frozen 2026-11-01. No existing
`numerals-v0.1` or `numerals-v0.2` operation, input, fixture, or error changes.
Tamil solar conversion and both panchangam profiles remain separately gated by
the source ledger in `numerals-calendar-source-research.md`.

## Shared exact decimal model

Wire values use `{ "negative": bool, "coefficient": string, "scale": u16 }`.
`coefficient` is ASCII digits, has no leading zero unless it is `"0"`, and
`scale` retains fractional trailing zeros. Zero always has `negative=false`.
Thus `-0.00` parses as `{negative:false, coefficient:"0", scale:2}` and formats
as `0.00`. No floating point is used.

Decimal text is at most 1024 UTF-8 bytes and 256 digits (sign, decimal point,
and grouping separators do not count toward the digit bound). A sign is an
optional leading ASCII `+` or `-`. A decimal point is ASCII `.` and, if used,
requires at least one digit on each side. Exponents, NaN, infinity, whitespace,
parentheses, and non-ASCII punctuation are unsupported notation. Leading
integer zeroes are accepted and removed from the coefficient. Fractional
zeroes are retained. `source_digits` is required and is `latin` or `tamil`;
`allow_mixed_digits` defaults to `false`, and if true accepts both those digit
sets in one string. `grouping` defaults to `none`; only `none` and `indian` are
supported. Indian grouping is rightmost 3 digits then groups of 2, with no
leading empty group or malformed separator placement.

Exact errors:

| Condition | Error |
| --- | --- |
| Malformed decimal syntax, grouping, or source-script digit | `invalid decimal string` |
| More than 1024 bytes, 256 digits, or scale greater than 256 | `decimal precision exceeds supported range` |
| Exponent, NaN, infinity, or unsupported notation | `unsupported numeric notation` |
| Malformed/noncanonical `ExactDecimal` object | `invalid decimal value` |
| Invalid `source_digits` or display `digits` | `unsupported digit style` |
| Invalid grouping option | `unsupported grouping` |
| Invalid destination in `convert_digits` | `unsupported digit style` |

For `parse_decimal`, validation is object/string shape, byte/digit limits,
`source_digits`, `grouping`, notation/syntax, then canonicalization. For
`format_decimal`, validate the exact-value shape and range, then `digits`, then
`grouping`. A missing or wrong-type required string keeps the shared
`expected a string input` error.

## Digit and word operations

- `convert_digits {text,to}` preserves every scalar except ASCII digits
  U+0030..U+0039 and Tamil positional digits U+0BE6..U+0BEF, which are mapped
  one-for-one. `to` is `latin` or `tamil`; punctuation, ZWJ/ZWNJ, and all other
  text are unchanged.
- `parse_decimal {text,source_digits,grouping?,allow_mixed_digits?}` returns an
  `ExactDecimal` object. `format_decimal {value,digits?,grouping?}` returns a
  canonical decimal string, retaining `scale` and applying optional Indian
  grouping after canonicalization.
- `decimal_to_words {text,locale?,source_digits,grouping?,allow_mixed_digits?}`
  uses CLDR 49 Tamil `%spellout-numbering`. An integral part may not exceed
  999,999,999; scale is at most 256. Scale zero delegates unchanged to existing
  `to_words`. For scale greater than zero, emit the integer part, CLDR's Tamil
  decimal-point word, then each fractional digit as a standalone number word,
  joined by one ASCII space; this preserves lexical zeroes. Exactly one
  existing negative prefix applies to the entire value. This is formal CLDR
  spellout, not a newly inferred spoken convention.
- `ordinal_to_words {value,locale?}` accepts 1..999,999,999 and uses the pinned
  CLDR 49 Tamil `%spellout-ordinal` rules plus the existing declared SL lakh
  stem profile. Errors are `expected a positive integer in the supported
  range`, then existing `unsupported locale` validation.
- `digit_sequence_to_words {text,locale?,source_digits}` accepts 1..256 digits,
  preserves leading zeroes, and joins each standalone CLDR digit reading with
  one ASCII space. Errors are `invalid digit sequence` or
  `digit sequence exceeds supported range`; locale and digit-style errors keep
  their existing spelling.

## Exact money and fractional symbol operations

- `format_currency_decimal` and `currency_decimal_to_words` take a major-unit
  decimal `amount`, explicit `source_digits`, optional `grouping`, `currency`,
  and optional `locale`. The magnitude cap is 999,999,999.99. At most two
  fractional digits are accepted; one fractional digit is padded on the right
  for the existing two-decimal output. Three digits fail even when the last is
  zero. There is no rounding. The operation converts to the existing minor
  unit API and returns exactly its output. Errors are
  `currency amount has more than two fractional digits`,
  `currency amount exceeds supported range`, followed by existing locale and
  currency errors. Validation order is decimal syntax, scale, magnitude, locale,
  currency. Existing integer minor-unit operations are unchanged.
- `parse_fraction_symbol {text}` accepts exactly one Unicode 17 Tamil fraction
  scalar, optionally preceded by ASCII `-`; it accepts all 20 encoded forms,
  including the duplicate one-sixteenth and one-half forms. It returns the
  reduced signed rational as `{numerator,denominator}` with positive
  denominator. `Kiizh` U+11FD4 is not a standalone rational and fails with
  `expected a traditional Tamil fraction symbol`.
- `symbol_info {text}` accepts exactly one scalar from the pinned symbol subset:
  Tamil positional digits, Tamil 10/100/1000 signs, all 20 encoded fractions,
  U+0BD0 Tamil Om, U+0BF3..U+0BFA Tamil calendar/clerical/currency/number
  signs, and the named Tamil Supplement nonnumeric symbols. It returns integer
  `codepoint`, exact Unicode `name`, `kind`, optional reduced `rational`,
  optional `canonical_alternative`, and `source_version:"Unicode 17.0.0"`.
  Nonnumeric symbols return `rational:null`; Kiizh has no independent value.
  Unknown/multiscalar text fails with `unsupported Tamil numeric symbol`.
- `format_mixed_fraction {negative,whole,numerator,denominator,digits?}`
  requires nonnegative bounded components, denominator > 0, and numerator <
  denominator. It reduces the fractional part. The sign applies to the entire
  magnitude. Output is `[-]whole numerator/denominator`; a zero fractional
  part is omitted and a zero whole is retained for a proper fraction. Improper
  input fails with `invalid mixed fraction`.
- `parse_mixed_fraction {text,source_digits}` accepts only the formatter's
  canonical grammar and representation; it returns
  `{negative,whole,numerator,denominator}`. Unreduced fractions, grouping,
  leading zeroes, extra spaces, and negative zero fail with
  `invalid mixed fraction`.
- `format_traditional_integer {value}` and `parse_traditional_integer {text}`
  use CLDR 49 root RBNF `%tamil` and `%%tamil-thousands`, bounded to signed
  99,999,999. Zero is U+0BE6 TAMIL DIGIT ZERO; negative values use the rule's
  U+2212 MINUS SIGN. The parser accepts iff decoding and canonical reformatting
  reproduce the complete input scalar sequence. Formatting failures use
  `expected a traditional Tamil integer in the supported range`; parsing
  failures use `invalid canonical traditional Tamil integer`.

## Percentages and numeric ranges

- `parse_percent {text,source_digits,grouping?}` parses exactly one trailing
  ASCII `%` with no intervening space and returns the decimal percent value.
  `format_percent {value,digits?,grouping?}` renders that value with `%`.
  CLDR 49 Tamil number data identifies the percent sign as ASCII `%`; no prose
  percent wording is provided.
- `ratio_to_percent {value}` and `percent_to_ratio {value}` shift decimal scale
  by two exactly. They preserve representable trailing zeroes and reject any
  result exceeding the coefficient/scale limit with
  `decimal precision exceeds supported range`. They do not interpret a value
  as either a ratio or percent implicitly.
- `format_numeric_range {start,end,start_inclusive,end_inclusive,separator,
  digits?}` takes tagged endpoints: either
  `{type:"decimal",value:ExactDecimal}` or
  `{type:"fraction",numerator,denominator}`. It compares endpoints exactly,
  renders fractions through the existing Latin/Tamil ratio form and decimals
  through `format_decimal`, and emits `[start<separator>end]` with `(` or `)`
  at exclusive boundaries. `separator` is a required nonempty string of at
  most eight scalars. It never parses range prose. Shape/domain/reversed bounds
  and malformed flags/separator fail with `invalid numeric range`; invalid
  digits use `unsupported digit style`.

## Civil Gregorian extensions

These operations reuse the existing validated proleptic Gregorian domain
(years 1..9999), without changing `format_date`:

- `validate_gregorian_date {year,month,day}` returns `true` or the existing
  `invalid Gregorian date` error.
- `parse_gregorian_date {text}` accepts exactly `YYYY-MM-DD` with four year
  digits and two month/day digits, then returns `{year,month,day}`. Invalid
  shape or date is `invalid Gregorian date`.
- `weekday {year,month,day}` returns one of `monday` through `sunday` in
  lowercase English; it is a stable enum, not a localized weekday name.
- `add_gregorian_date {year,month,day,unit,amount,overflow?}` supports signed
  whole `amount` and `days|months|years`. Month/year addition rejects a missing
  target day by default; `overflow:"clamp"` explicitly clamps to the target
  month end. `overflow` defaults to `reject`. Out-of-domain results use
  `Gregorian date arithmetic out of range`; bad units/policies use
  `unsupported date unit` / `unsupported date overflow policy`.
- `date_difference {start,end}` returns signed civil days `end - start`.
- `date_interval {start,end}` returns a closed interval with canonical ISO
  endpoints and inclusive day count; start after end fails with
  `invalid date interval`.

Date fields are validated before options; an invalid date wins over invalid
`unit`/`overflow`. Existing `format_date` errors and precedence remain
byte-for-byte stable.

## Source pins and explicit blockers

CLDR 49 (`release-49`) Tamil ordinal and decimal lexical facts are taken from
the existing pinned `ta.xml`; expected ordinal words must come from the pinned
ICU4J 79.1 reference generator and expected decimal parsing/formatting from an
independent exact-string implementation. Unicode 17 `UnicodeData.txt` supplies
digit/fraction values and names. These references retain Unicode-3.0 terms.

CLDR 49 `common/supplemental/numberingSystems.xml` identifies `taml` as an
algorithmic Tamil system and points to `tamil`; `common/rbnf/root.xml` defines
`%tamil` and `%%tamil-thousands`. Its 100,000,000 fallback bounds the
traditional rule set to 0..99,999,999 before applying the separately specified
sign. The pinned full source and extracted rule data are recorded in
`tests/reference/numerals-v0.3/sources.json` and canonical
`lexicon/numerals-traditional.toml`.

Calendar APIs, observance data, panchangam calculations and holiday datasets
remain gated. Both Thirukanitham and Vakiya are mandatory. See the source
ledger for source acquisition outcomes, scan inspection, licensing, regional
coverage, and the exact evidence needed before either astronomical engine can
be implemented.

## Regression evidence and activation

The owner explicitly approved v0.3 activation in this session on 2026-11-01.
The checked-in suite contains 7,341 sourced escaped rows and is active in the
manifest; the full active corpus contains 35,646 rows. Its adversarial rows include exact `Fraction`-oracle
comparisons for zero endpoints across scales 0..256, decimal/fraction cross
comparisons, signed negatives and close unequal values; Indian grouping and
parser round trips for every width 1..256; Tamil-digit grouping samples and
malformed grouping; zero ratio/percent shifts through the maximum scale;
combined-invalid validation precedence; range/domain bounds; and Gregorian
leap, century, year-boundary and out-of-domain cases. Expected arithmetic and
date results are generated independently of the Rust implementation.

The ordinal, symbol and traditional-integer projections are checked against
pinned sources by `just check-unicode` and the harness source test.
Before owner activation, Rust, Python, Node/browser-WASM, Dart and isolated release
consumers exercised this suite through `TAMIL_GOLDEN_INCLUDE_PLANNED` for
integration evidence. That execution was separate from owner review. The
owner subsequently answered "Approve v0.3 activation" after being presented
with this contract, case counts and repaired review findings. Default active
suite selection now includes these rows without an environment override.
This approval does not activate any calendar behavior or authorize publication.
