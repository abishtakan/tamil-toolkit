# tamil-numerals completion: fractions and Gregorian dates

Status: engineering acceptance passed locally. This completes the documented numeral feature families:
bounded integer words, exact INR/LKR amounts, rational fractions, and Gregorian
dates in Tamil. Existing `numerals-v1` behavior remains unchanged.

## Plan and acceptance

1. Pin Unicode 17 fraction values/digits, CLDR 49 calendar data, and resolved
   ICU4J 79.1 symbols. Record sources, digests, licenses, and the word template.
2. Freeze independent ICU date and component spellout outputs. Prepare golden
   fractions using Python's exact Fraction and dates using ICU's proleptic
   Gregorian calendar, before adding Rust algorithms.
3. Compile declarative names, symbols, digits, and date patterns at build time.
   Add exact reduced Fraction and validated GregorianDate types in Rust; bind
   the four new operations through the shared dispatcher.
4. Pass all active fixtures in Rust, rebuilt Python, both WASM targets, and host
   Dart, plus full repository gates and four new 10,000-case properties.

Acceptance includes signed/zero/reducible/improper fractions, every traditional
symbol value and its Unicode alternatives, common quarter/half names, arbitrary
supported component readings, all date styles/months/weekdays, leap and century
boundaries, Gregorian years 1..9999, Tamil/Latin digits, seven regional probes,
and identical type/range/domain errors across runtimes. Reference digests,
offline regeneration, and runtime/source data agreement are mandatory.

## Fraction operations

All components are exact JSON whole numbers in +/-999,999,999; integral JSON
values such as 1.0 mean 1. No float arithmetic computes a fraction. A nonzero
denominator may be negative. Normalize its sign, reduce by the greatest common
divisor, and represent zero as 0/1.

- `format_fraction`: `{numerator, denominator, digits?}`. Return reduced `n/d`,
  including `/1` for integral results. `digits` is `latin` (default) or `tamil`.
  Tamil digits mean CLDR `tamldec`, positional U+0BE6..U+0BEF, not the historic
  multiplicative numeral system. Negative results have one ASCII minus.
- `fraction_to_words`: `{numerator, denominator, locale?}`. TN defaults; SL uses
  the existing formal lexical profile. Zero/integral results use `to_words`.
  Reduced positive 1/4, 1/2, and 3/4 use the sourced common names kaal, arai,
  and mukkaal. Other fractions use the explicit math-reading template
  `{numerator words} {division label} {denominator words}`; the division label
  is U+0BB5 U+0B95 U+0BC1 U+0BA4 U+0BCD U+0BA4 U+0BB2 U+0BCD.
  One CLDR negative prefix applies to a negative result. This is a division
  expression, not an invented locative/Punarchi or mixed-number grammar.
- `fraction_symbol`: `{numerator, denominator}`. Return the Unicode 17 Tamil
  fraction symbol for the reduced absolute value, with ASCII minus if negative.
  Where two characters share a value, choose the lower codepoint. There are
  18 distinct values and 20 encoded forms. Other values fail explicitly. The
  downscaling prefix Kiizh is not an independent rational-value symbol here.

Invalid component types/ranges use the existing integer error. Denominator zero
uses `fraction denominator must not be zero`. Unknown digits/locale use
`unsupported digit style` / `unsupported locale`. A missing symbol uses
`no traditional Tamil symbol for this fraction`. Validate components/domain
before optional fields. The common names and numeric/symbol formats are region
invariant; general word readings retain TN/SL scale conventions.

## Gregorian date formatting

`format_date` takes `{year, month, day, locale?, style?, digits?}`. The user chose
Gregorian dates in Tamil; Tamil solar-calendar conversion is outside this
contract. Dates are civil dates, not timestamps: no time zone or time-of-day.
Use the proleptic Gregorian calendar for years 1..9999, without the historical
1582 cutover. Reject impossible dates, including non-leap February 29.

Locale is TN (default) or SL; both inherit CLDR Tamil Gregorian date patterns.
`style` is `short`, `medium`, `long` (default), or `full`; `digits` is `latin`
(default) or `tamil`. The four pinned patterns are:

- short: `d/M/yy` (two-digit year, exactly as specified by CLDR);
- medium: `d MMM, y`;
- long: `d MMMM, y`;
- full: `EEEE, d MMMM, y`.

Use the resolved CLDR 49 month names, abbreviations, and weekdays, including
inheritance of wide forms for May/June/July abbreviations. Compile only the
required pattern tokens and literals; unsupported pattern syntax fails builds.
The date formatter performs no automatic linguistic spelling substitutions.

Malformed components, out-of-range years, and impossible dates all return
`invalid Gregorian date`. Validate the date before locale, style, and digits;
option errors are `unsupported locale`, `unsupported date style`, and
`unsupported digit style`. All outputs are NFC; no joiners are introduced.

## Evidence and scope

The reference manifest records exact upstream URLs, bytes/digests, and extracted
facts. Unicode/CLDR data retains the Unicode license. Common lexical facts are
evidenced by Tamil educational/Unicode material; no third-party prose or images
are redistributed. ICU is a development-only oracle, not a runtime dependency.

- [Unicode 17 numeric properties](https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt)
- [CLDR 49 Tamil locale](https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/main/ta.xml)
- [CLDR 49 Sri Lankan Tamil inheritance](https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/main/ta_LK.xml)
- [CLDR decimal digit systems](https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/supplemental/numberingSystems.xml)
- [Government of Tamil Nadu fraction proposal](https://www.unicode.org/wg2/docs/n4822-tamil-frac.pdf)
- [Tamil mathematical division terminology](https://help.libreoffice.org/latest/ta/text/smath/01/03090100.html)

This contract completes the requested numeral categories within explicit
bounds. Ordinal spellout, arbitrary decimal parsing, exchange/rounding rules,
Tamil solar-calendar astronomy, and comprehensive historical metrology are
separate capabilities, not implied by those categories. Publication remains
disabled pending release review.

## Acceptance results

The completion adds **4,446 golden vectors**, including **537 exact errors**,
bringing the shared active corpus to **21,277 vectors** and **1,625 errors**.
The integer/currency suite and all earlier modules remain passing unchanged.

Independent evidence covers 328 rational input pairs, 18 traditional values
from all 20 Unicode forms, 24 distinct component spellings, and 154 Gregorian
dates across every style/locale/digit combination. It includes all months and
weekdays, year 1 and 9999 limits, leap-century cases, dates inside the historical
1582 cutover interval under the declared proleptic calendar, invalid dates,
normalization/sign/reduction controls, and seven regional probes.

The pre-implementation Rust runner failed on the missing `format_fraction`
operation. After implementation, `just agent-pre-stop-gate` passed formatting,
Unicode/schema validation, locked workspace checking, clippy with denied
warnings, **21 Rust tests**, doctests, and **64 harness tests**. Four new
10,000-case properties bring the workspace total to seventeen properties and
**170,000 generated cases** per full gate.

All 21,277 active rows passed real Rust, rebuilt PyO3, Node WASM, browser-target
WASM, and host Dart. Python reported **21,285 tests**; Vitest and Dart each
reported **21,283 tests**. Every Vitest row invokes both WASM entry points.
The convenience APIs also consume all applicable success fixtures directly.
`just test-dart` passed host analysis and parity.

The pinned ICU artifact digest was verified. All date and component JSONL
outputs reproduced byte for byte; resolved calendar symbols reproduced
structurally exactly. Offline fixture regeneration matched Python 3.14 and
3.13.7. Source digests, runtime/source table agreement, Unicode variants, and
Python's independent weekday calculations are checked in the harness.

The workbench includes all four operations; its TypeScript check and production
bundle build passed. Binding builds resolve their pinned wasm-pack tool from
the binding package, keeping the full gate valid after the workbench split.

Verification is local Windows/MSVC; remote CI has not run. Browser-target WASM
was executed in Node; the workbench was type-checked/built without an interactive
browser check. Dart coverage is for the host shared library. The explicit bounds,
division-expression reading, single-symbol availability, and Gregorian-only
calendar scope are intentional. No general mixed-number inflection, solar
calendar conversion, or comprehensive historic-metrology claim is made.
Publication remains disabled.
