# tamil-numerals v0.1 plan and acceptance contract

Status: v0.1 engineering acceptance passed locally. Profile: `numerals-v1`,
based on CLDR 49 Tamil spellout.
The [completion contract](numerals-v0.2.md) adds fractions and Gregorian dates
without changing this integer/currency behavior.

## Plan and scope

1. Freeze CLDR 49 Tamil RBNF and numeric/currency metadata. Record source URLs,
   digests, licensing, and the narrowly declared TN/SL lexical profiles.
2. Generate independent expected output with ICU4J 79.1 using those frozen
   rules. Store the reference output and compile checked-in golden JSONL from
   it; never use the Rust implementation or its tables to derive expectations.
3. Compile declarative rules from lexicon/numerals.toml into static Rust rules.
   Implement the finite, required rule subset and exact integer money handling.
4. Expose typed Python, WASM, and Dart wrappers and verify the same success/error
   vectors, property invariants, full repository gate, and host Dart gate.

This milestone supports signed integer words from -999,999,999 through
999,999,999, and LKR/INR amounts from -99,999,999,999 through 99,999,999,999
minor units. All supported numbers are safely representable in JavaScript.
Fractions, dates, ordinals, arbitrary decimal parsing, exchange rates, and
rounding are separate milestones.

## Public operations

- `to_words`: input `{value, locale?}`; return an NFC Tamil string using CLDR's
  standalone `%spellout-numbering` forms. Locale defaults to TN.
- `format_currency`: input `{amount_minor, currency, locale?}`; return
  `CODE [-]grouped_major.minor` with exactly two fractional digits.
- `currency_to_words`: same input; return the noun/cardinal form of the major
  amount, the major-unit label, then the cardinal minor amount and subunit label.
  Both units are always present, including zero subunits. Negative amounts have
  exactly one leading CLDR negative prefix, even when the major part is zero.

Locale values are exactly `TN` and `SL`; currency values are exactly `INR` and
`LKR`. Currency and locale are independent: test all four combinations.
JSON numbers must denote whole values in the supported range. Integral numeric
values such as 1.0 have the same meaning as 1 across runtimes. Fractional values,
numeric strings, booleans, missing values, and other types fail. Validation and
all money calculations use integer parsing, division, remainder, and formatting;
no floating-point arithmetic computes a monetary amount.

Exact integer failures use `expected an integer in the supported range`.
Unknown/malformed locale and currency use `unsupported locale` and
`unsupported currency`. Validation order is amount/value, locale, then currency.

## Linguistic and regional decisions

Use CLDR 49's revised Tamil rules, not the earlier CLDR 48 spellout data. The
standalone and noun/cardinal rule sets differ, including one and eleven; they
must not be interchanged. Literal forms and connective rules are sourced data,
not guessed Punarchi rules. The supported range ends below CLDR's larger arabam
and karabam scales.

TN follows the frozen CLDR rules. SL uses the same bounded formal spelling
profile with the explicit lakh stem replacement `0BB2 0B9F 0BCD 0B9A` to
`0B87 0BB2 0B9F 0BCD 0B9A` (ilatcham), evidenced by Sri Lankan government usage.
This is a declared lexical profile, not a claim to cover all regional speech.
Jaffna, Batticaloa, Vanni, and Up-Country probes use this SL profile; Kongu and
Chennai probes use TN. No other regional pronunciation differences are invented.

Use invariant denomination labels: INR `0BB0 0BC2 0BAA 0BBE 0BAF 0BCD` and
`0BAA 0BC8 0B9A 0BBE`; LKR `0BB0 0BC2 0BAA 0BBE` and `0B9A 0BA4 0BAE 0BCD`.
The words operation is an explicit amount-with-unit-label rendering, not a bank
cheque template. The ISO code in numeric output disambiguates the currency.
Both currencies have 100 minor units; no cash-denomination rounding is applied.

Numeric display uses Latin digits and 3-2 grouping from CLDR Tamil; ta_LK
inherits the same grouping. Currency codes replace ambiguous symbols in this
API's declared display template. A negative one-minor-unit amount is formatted
as `INR -0.01` or `LKR -0.01`; zero is never negative.

## Acceptance criteria

- Independent ICU expectations cover every integer 0..999 for TN and SL, all
  tens/hundreds, irregular teens, thousand/lakh/crore boundaries, every 1..99
  scale multiplier with representative remainders, negatives, and range limits.
- Golden amounts cover all 100 subunit values, zero/one major unit, carries,
  negatives below one major unit, grouping changes, large limits, all currency/
  locale pairs, and standalone versus noun-form distinctions.
- Shared negatives cover invalid/missing values, fractions, booleans, strings,
  malformed locale/currency, and values just outside each supported range.
- All generated Tamil is NFC with deterministic spaces and no joiners. Numeric
  money strings round-trip exactly to their original signed minor-unit amount.
- Declarative rules and labels compile at build time, validate their supported
  syntax/references, and agree with frozen independent evidence. No hardcoded
  Tamil word lists appear in Rust or bindings.
- Fixture regeneration is offline and deterministic. Reference digests, case
  counts, source rule agreement, and required regional coverage are checked.
- Three 10,000-case properties exercise arbitrary signed input without panic,
  exact money round trips, and successful NFC word output within range.
- All rows pass Rust, rebuilt PyO3, Node/browser-target WASM, and host Dart.
  Typed convenience APIs are tested directly. Existing core/collation behavior
  stays passing, as do `just agent-pre-stop-gate` and `just test-dart`.

## Sources

- https://cldr.unicode.org/downloads/cldr-49
- https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/rbnf/ta.xml
- https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/main/ta.xml
- https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/main/ta_LK.xml
- https://raw.githubusercontent.com/unicode-org/cldr/release-49/common/supplemental/supplementalData.xml
- https://www.parliament.lk/ta/home/parliament-news/view/5363 (ilatcham and rupee usage)
- https://tamil.ciaboc.gov.lk/media-centre/latest-news/1077-2025-11-06-17-18-30 (connected ilatcham stem)
- [Central Bank of Sri Lanka, circulating coins](https://www.cbsl.gov.lk/ta/பணத்தாள்கள்/நாணயத்தாள்களும்-குத்திகளும்/சுற்றோட்டத்திலுள்ள-நாணயக்குத்திகள்) (Tamil denomination labels).
- [Tamil Virtual Academy, fourth-standard Kanakku textbook](https://www.tamildigitallibrary.in/admin/assets/book/TVA_BOK_0000963_%E0%AE%95%E0%AE%A3%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%81.pdf),
  printed page 30 (rupee/paise labels and 100 paise per rupee).

Only lexical/format facts are extracted from government/textbook pages; no
prose or images from them are redistributed. Frozen CLDR data retains its
Unicode license. ICU4J is a development-only reference tool and is not a runtime
or CI dependency. Its version and artifact digest are recorded with evidence.

## Acceptance results

All stated engineering criteria passed in the local Windows/MSVC environment.
The new suite has **7,528 vectors**, including **134 exact errors**, bringing
the active shared corpus to **13,073 vectors** with **280 errors** overall.

The independent reference contains 2,147 signed integer inputs, each with
standalone/cardinal results for TN and SL, and 383 exact money amounts. Golden
coverage includes every integer 0..999, every minor-unit value 0..99, scale
multipliers and boundaries, all four currency/locale pairs, seven regional
probes, default locale, integral JSON numbers, and validation precedence.

Before implementation, the unchanged Rust runner failed on the missing
`to_words` operation. After implementation, `just agent-pre-stop-gate` passed
formatting, Unicode/schema checks, locked workspace checking, clippy with denied
warnings, **12 Rust tests**, doctests, and **53 harness tests**. Three numeral
properties each run 10,000 generated cases; the full workspace now runs eight
such properties, totaling **80,000 cases** per gate.

Every active golden row passed Rust, rebuilt PyO3, Node WASM, browser-target
WASM, and host Dart. Python reported **13,078 tests**; Vitest reported
**13,076 tests**, with each golden row executed through both WASM entry points;
Dart reported **13,076 tests**. All three bindings test their numeral convenience
APIs directly. `just test-dart` also passed static analysis without issues.

The pinned ICU4J artifact's digest was verified, then both independent reference
outputs were reproduced byte for byte using the checked-in Java source. Offline
fixture regeneration matched under Python 3.14 and 3.13.7. Harness tests enforce
reference digests, runtime/source rule agreement, and required coverage.

Verification is local; remote CI has not run. Browser-target WASM was loaded in
Node rather than an interactive browser. Dart coverage is for the host shared
library, without mobile packaging. These are bounded formal lexical profiles,
not comprehensive regional speech or cheque-writing grammar. Fractions and
dates are covered separately by the completion contract. Publication remains disabled.
