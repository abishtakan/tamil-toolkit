# Tamil numerals and calendar completion milestone

Status: numerals v0.3 is owner-approved and implemented in the worktree. A
source-pinned historical Vakiya solar-transit kernel is specified and
implemented; the full required calendar profiles and remaining source gates
are still open. This supersedes the earlier checklist in this document, not
the compatible v0.1/v0.2 API contracts. Exactly Thirukanitham (Drik) and
Vakiya (Vakya) are required first-class profiles. Neither may be dropped to
declare completion. IMD is evidence, not a third implemented system.

Read together with [source research and acquisition ledger](numerals-calendar-source-research.md).
That ledger distinguishes inspected text, scan acquisition, and unresolved
leads. Numeric implementation and activation are complete for this worktree.
The calendar remains staged source-backed work: a bounded classical Vakiya
kernel can proceed from inspected mathematical sources without being described
as a contemporary publisher edition or a complete calendar.

## Review findings and objections

The approved numeric scope is sound and additive. Existing Rust owns bounded
integer words, exact minor-unit currency, fractions and Gregorian formatting;
canonical data lives in lexicon/numerals.toml and numerals-formats.toml.
CLDR 49 Tamil spellout and root traditional-numeral sources, Unicode 17 Tamil
numeric symbols, and ICU4J 79.1 expected spellings are now pinned in the
v0.3-specific reference manifest. Do not enlarge old integer inputs or change
old errors.
The workbench decimal-money conversion is insufficient as a public guarantee:
the exact decimal-major helper must live in Rust and be shared by every adapter.

Calendar completion is substantially larger than Gregorian Tamil labels.
Neither the name Drik nor Vakya fixes a unique implementation: publisher,
epoch, corrections, time basis and day-assignment convention must be pinned.
A modern ephemeris with a different ayanamsa is not a Vakya implementation.
The IMD fixed-month All-India Nirayana calendar is not the regional Tamil
calendar. Gregorian leap rules do not define Tamil month lengths.
A named cycle year alone cannot identify a date. Government holiday dates do
not define lunar transition times or temple observance rules. TN evidence does
not establish Jaffna, Batticaloa, Vanni or Up-Country practice.

## Required scope matrix

All rows below are required now within documented finite domains. A source gate
means acquisition remains required in this milestone, not optional future work.

| Family | Contract and reason | Evidence/readiness |
| --- | --- | --- |
| Digit conversion | Scalar-preserving Latin <-> Tamil positional digit substitution; arbitrary surrounding text preserved, including joiners. Strict number parsing is separate. | Unicode 17/tamldec already pinned. |
| Exact decimal strings | Parse, normalize and format signed values; preserve requested scale, zeros and explicit grouping. No binary floating point. | Engineering contract below; independent exact-string oracle needed. |
| Words | Existing integer range; exact decimal spellout, ordinal words and digit-sequence readings with TN/SL formal lexical profiles. | CLDR 49 and bounded ICU4J 79.1 references pinned; decimal strings use an independent exact oracle. No invented spoken grammar. |
| Traditional integers | CLDR traditional integer rendering and strict canonical inverse; positional zero is distinct from multiplicative symbols. | Root RBNF/version/license and zero/range pinned. |
| Fractions | Existing rational APIs unchanged; reverse reading of all 20 encoded forms, rational metadata; numeric mixed forms. | Unicode alternatives already pinned; lexical mixed-number inflection remains optional. |
| Percent | Exact percent parsing/formatting, explicit percent-value versus ratio conversion by 100; digit styles/grouping. | Numeric notation required; freeze CLDR spacing/symbol evidence. Percentage words only after lexical evidence. |
| Symbols | Codepoint, Unicode name, kind, rational value where defined, canonical alternative and source version. Include digits, integer signs, fractions and nonnumeric Tamil symbols without inventing values. | Pin full Unicode property subset; Kiizh is not a standalone rational. |
| Numeric ranges | Typed endpoints, inclusive/exclusive flags, exact comparison; explicit display separator; reversed endpoints fail. | Application syntax contract, no inference from a hyphenated string. |
| Money | Rust decimal-major input, INR/LKR, same exact existing minor-unit domain and outputs; reject excess precision. | Existing labels/factors; no exchange or implicit rounding. |
| Civil dates | Gregorian validation, weekday, strict ISO full-year parsing, day differences, day/month/year arithmetic; reusable date intervals. | Existing proleptic 1..9999 contract plus independent Gregorian oracle. |
| Solar conversion | Gregorian <-> Tamil solar dates for both required profiles; actual month boundaries/lengths and validation. | Thirukanitham v1 has bounded conversion and independent 2024–2026 Chennai ingress witnesses. The unmodified 1962 Vakiya edition now provides year 1–9999 Ujjain mean-sunrise conversion and month lengths, anchored to the printed 1947/Kali-5048 correspondence. Both suites remain planned. |
| Solar arithmetic | Add days/months/years, difference in civil days, year/month enumeration and ranges. | Implemented for both definitions through Rust dispatch and Python/Node/browser WASM/Dart/workbench. Seven new planned fixtures cover year bounds and day/month overflow; these do not establish independent almanac accuracy beyond each profile's source domain. |
| Eras/names | 12 months, weekdays, 60-year cycle with anchored solar year; Thiruvalluvar year with sourced actual boundary. | `format_tamil_date` and `calendar_display_info` expose sourced Tamil/Romanized month, weekday, limb and cycle labels with explicit digit styles/templates and source metadata. A TN-only `tn-thiruvalluvar-thai1-thirukanitham-v1` profile convention is implemented for 2025–2027 and explicitly disclaims official equivalence. Its computed 2026-01-14 Thai 1 differs from the official Gazette evidence; exact official boundary dates remain unresolved. |
| Profile comparison | One explicit Gregorian civil date or UTC instant evaluated under complete Thirukanitham TN/SL and supported Ujjain Vakiya contexts. | `compare_calendar_profiles` computes each shared Rust profile once and returns the two contexts, semantic bases, provenance and field differences. Derived vectors show both a solar-date disagreement and a same-instant tithi/karana disagreement. `accuracy_assessment` stays `not_assessed`; this operation does not rank the models. |
| Panchangam | All five limbs: tithi, vara, nakshatra, yoga, karana; values at instant and sunrise, all transitions over requested civil day; paksha and new/quarter/full phase events. | Thirukanitham v1 implements bounded five-limb day/instant results and Drik-only primary phase events checked against USNO 2025 UTC minutes. Classical Vakiya provides five limbs at instant and Ujjain mean-sunrise day; it does not substitute Drik phases. Both suites remain planned. |
| Local context | Sunrise/sunset, local civil date, timezone, coordinates, explicit no-rise/no-set and unsupported states; reference-station metadata. | Thirukanitham v1 pins its −47′ horizon, elevation dip, UTC+05:30 TN/SL rules and coordinate boxes. A fresh visual review of the publisher-hosted 1962 Vakiya scan verifies the Cara half-daylight equation, 55-yōjana/6° longitude conversion, precession-before-declination rule, and shadow/Cara/daylight equations (printed pp. xv–xvi, 255, 267–269). The Bhujaantara interpolation parameter and its relation to the p. 252 Bhūpādi correction remain unresolved; the source also explicitly omits Udayāntara. Vakiya remains Ujjain mean-sunrise only, without arbitrary-location sunrise/sunset. |
| Everyday periods | Rahu kalam, Yamagandam and Kuligai required as named intervals with sourced weekday tables and day/night convention. | Thirukanitham daylight-only intervals are implemented from the visually inspected Rao p. 35 weekday table and computed sunrise/sunset; three planned fixtures include Sunday/Monday and the Vakiya unsupported state. Vakiya intervals remain unavailable until its source-defined local sunset is established. No night interval or auspiciousness meaning is inferred. |
| Observances | Curated rule IDs for Puthandu, Pongal/Bhogi/Mattu Pongal, monthly Amavasai/Pournami, Ekadashi, Pradosham, Sankatahara Chaturthi, Sivarathri, Thai Poosam, Panguni Uthiram, Chitra Pournami, Vaikasi Visakam, Aadi Perukku, Krishna Jayanthi, Vinayaka Chaturthi, Navaratri/Ayudha Puja/Vijayadasami, Deepavali, Karthigai Deepam and Arudra Darshan. | The planned `thirukanitham-tamil-named-observances-v1` contains a separate bounded selector for every listed family in the TN profile. Each event follows its own named publisher/community rule; this composite does not claim one universal Tamil schedule. Exact rules, source coverage and model scope are in `calendar-observances-v1.md`. The 13 Nava Amavasya and 12 Pournami Chennai dates from Nov 2026–Oct 2027 match the Thirukanitham profile without an engine-equivalence claim. Sri Vaishnava Ekadashi and Nava Pradosham retain separate source methods and visible Nava/Drik differences. Sankatahara uses a Dharmasindhu moonrise selector; Krishna Jayanthi uses Udyog’s detailed Smarta Nishita/Rohini rule. Its 2025/2026 Chennai date witnesses match, while the selected 2027 profile date (Aug 24) differs from Drik Chennai (Aug 25); Udyog’s Aug 24 Kanchipuram page is not a Chennai witness. Independent month vectors are distinguished by fixture tags; whole-year vectors are derived regressions. Dharmasindhu Pradosham’s earlier-day threshold, Smartha Ekadashi, broader TN/SL source acceptance, and Vakiya observances remain open. All calendar suites remain planned. |
| Official holidays | Separate versioned TN and SL jurisdiction/year records; revision and public/bank/mercantile category metadata. | Implemented as `calendar_official_holidays` for TN 2025–26 and SL 2026–27 using official annual schedules, preserving named rows and applicability. TN official PDF bytes are not locally hashed; the operation returns a null digest for those records. Other years/jurisdictions and broader reuse terms remain open; calendar suite planned. Never derive legal holidays from festival algorithms. |
| Usable integration | Rust typed API, shared dispatcher, wrappers, workbench forms/results, profile comparison, source/range display. | Tamil/Romanized date formatting and date/day context display, profile comparison, and the named Thiruvalluvar convention dispatch through Rust to Python, Node/browser WASM, Dart and workbench. Comparison metadata preserves each context and basis and sets accuracy to `not_assessed`. Calendar suites remain planned. |

## Explicit optional future scope

Arbitrary-precision linguistic scales beyond current sourced range; natural
language numeral parsing; bank cheque grammar; mixed-fraction inflection;
percentage prose without evidence; scientific/engineering notation and general
arithmetic calculator; historic metrology beyond symbol metadata; currency
exchange/tax/cash rounding; all-year astronomy; BCE/historic calendar cutovers;
full astrology, horoscope, matching, planetary transits and eclipse prediction.
Other panchangam systems are excluded, not queued as milestone requirements.

Gowri periods, Nalla Neram, Abhijit, Brahma Muhurta, Durmuhurta, hora,
Chandrashtamam, Kari Naal, Amrita/Siddha/Marana day classifications and Vastu
periods are optional future named rule packs. They are not synonyms for the
27 astronomical yogas. Their publisher variants require their own source
contracts; marketing must list exactly the three supported everyday periods.
Moonrise/moonset and illumination percentage are optional; new/full/quarter
phase instants and waxing/waning status are required. Seasons and ayana labels
may be sourced metadata, but must identify solar versus climatic convention.
ICS/export widgets and arbitrary free-form date parsing are optional.

## Proposed numeric contracts (freeze before code)

Use ExactDecimal { negative: bool, coefficient: String, scale: u16 } internally;
coefficient contains canonical ASCII digits with no leading zeros except zero.
Scale retains fractional trailing zeros; zero has negative=false. Parsed
lexical leading-zero count is separate optional metadata, never value identity.
Maximum total input digits 256 (excluding separators/sign); maximum raw input
1024 UTF-8 bytes. No exponent, NaN, infinity, embedded whitespace or implicit
rounding. Sign is optional ASCII +/-. Require digits on both sides of a decimal
point when present. Default source digit script is explicit latin or tamil;
allow_mixed_digits=false rejects mixed runs. Conversion of surrounding text
continues to preserve all nondigit scalars. Reject grouping unless explicitly
requested; Indian grouping is rightmost 3 then groups of 2, no malformed groups.
Formatting grouping=none|indian, digits=latin|tamil; preserve scale by default.
Precision reduction is rejected. These are deliberate API decisions, not claims
about every Tamil numeric convention.

New dispatcher operations and typed Rust functions:

- convert_digits {text,to} -> string; parse_decimal {text,source_digits,grouping}
  -> ExactDecimal; format_decimal {value,digits,grouping} -> string.
- decimal_to_words {text,locale} -> string using CLDR decimal-point and individual
  fractional-digit rules; integral magnitude <=999999999 and <=256 fractional
  digits. Freeze whether scale-zero outputs use existing standalone forms.
- ordinal_to_words {value,locale} -> string, integers 1..999999999;
  digit_sequence_to_words {text,locale,source_digits} -> string, 1..256 digits,
  including leading zeros, deterministic one-space separators.
- format_currency_decimal / currency_decimal_to_words {amount,currency,locale}
  -> existing output strings; amount is strict decimal-major, <=2 fractional
  digits, magnitude <=999999999.99. One digit pads right; three digits fail even
  if the third is zero. No change to amount_minor operations.
- format_traditional_integer {value} and parse_traditional_integer {text}:
  proposed 1..99999999 pending root-rule verification; zero must follow pinned
  source, not invention. Parser accepts iff canonical reformat equals input.
- parse_fraction_symbol {text} -> Fraction, exactly one encoded symbol with
  optional ASCII minus; accept both duplicate-value alternatives. Return reduced
  signed rational, canonical symbol through existing fraction_symbol operation.
- symbol_info {text} -> SymbolInfo; format_mixed_fraction {whole,numerator,
  denominator,digits} -> explicit signed magnitude form. Whole and numerator
  nonnegative; numerator < positive denominator; separate negative flag avoids
  ambiguous -1 1/2 interpretation. Reject improper input rather than silently
  normalizing mixed lexical syntax. Add parse_mixed_fraction only for this
  exact emitted grammar, with sign applying to whole rational value.
- format_percent / parse_percent {text,...} returns exact percent value;
  ratio_to_percent / percent_to_ratio shift decimal scale exactly, preserving
  precision subject to 256-digit bound. No implicit 0.5-versus-50 interpretation.
- format_numeric_range {start,end,start_inclusive,end_inclusive,digits} -> string;
  no arbitrary range-text parser. Fraction/decimal comparison uses exact values.

For every new operation define exact error strings and validation precedence
in its contract and negative vectors before implementation. Suggested new errors:
invalid decimal string; decimal precision exceeds supported range;
unsupported numeric notation; invalid mixed fraction; invalid numeric range.
Keep old integer/locale/currency/date/fraction errors byte-for-byte unchanged.

## Calendar types and operations

Initially use Rust submodules calendar/{civil,solar,drik,vakya,panchangam,
observance,display}. Do not create another published crate. Data and names go
in canonical lexicon/calendar-*.toml/CSV with build.rs validation; executable
rules stay Rust. Dependencies require version, license, provenance, transitive
license review, supported-target and determinism assessment before adoption.
No Python/JS/Dart astronomical implementation, remote runtime service, or
Python-to-Rust output generator pretending to be an independent oracle.

Proposed types (wire objects mirror fields, enum strings lowercase):

```rust
// Constructor validation and fields private in the actual public Rust API.
enum PanchangamProfile { Thirukanitham, Vakiya }
struct SolarYearId { chithirai_start_gregorian_year: u16 }
struct TamilSolarDate { year: SolarYearId, month: u8, day: u8 }
struct GeoLocation { latitude_microdegrees: i32, longitude_microdegrees: i32,
                     elevation_metres: i32 }
struct CalendarContext { profile: PanchangamProfile, definition_id: String,
                         location: GeoLocation, timezone: String }
struct UtcInstant { unix_seconds: i64 } // JSON decimal string for future safety
struct TimeInterval { start: UtcInstant, end: UtcInstant } // [start,end)
struct LimbInterval { kind: LimbKind, index: u8, interval: TimeInterval }
enum DateOverflow { Reject, Clamp }
```

Year ID means the Gregorian year containing that solar year's Chithirai 1;
it is independent of the display era and 60-year name. Return cycle index
1..60, sourced name and anchor definition together; never accept a bare year
name for conversion. CalendarContext is mandatory for conversions and
panchangam, no TN/SL locale default deciding astronomy. definition_id pins the
edition/model revision; no silent profile changes. Display locale controls
names only. Separate jurisdiction and observance_rule_set from context.
Return supported coverage and provenance through calendar_profile_info.

Operations: gregorian_to_tamil_date {date,context}; tamil_to_gregorian_date
{date,context}; validate_tamil_date; tamil_month_info {year,month,context}
(start/end-exclusive Gregorian dates, length); tamil_year_info (12 months,
start/end); add_tamil_date {date,unit:days|months|years,amount,overflow,context};
date_difference (civil days); format_tamil_date {date,context,locale,style,
digits,era}; parse_tamil_date only machine grammar YYYY-MM-DD plus explicit
solar-year anchor/profile, never ambiguous localized prose. Month/year addition
rejects missing target day by default; clamp is explicit; no wrap/rollover.
Day addition uses Gregorian serial days. Gregorian add/difference reuse this
civil layer. Closed date ranges and instant intervals have different types.

thiruvalluvar_year {gregorian_date,convention_id} is separate from solar year
cycle. Required convention is contemporary TN official usage, with its actual
boundary pinned from adjacent Gazette mastheads and normative documentation.
No blanket year+31 or automatic Chithirai rollover. Historical legal regime
support outside selected coverage is optional. Avoid printing this era until
that boundary contract is established; this remains a milestone requirement.

panchangam_at {instant,context} returns five limb identifiers, paksha, current
local civil date and source/model revision. panchangam_day {date,context}
returns civil [midnight,next midnight), sunrise/sunset, sunrise limb values and
every angular-limb transition in that civil interval. Its displayed event times
are integer local minutes rounded to nearest minute. A transition at or after
the next midnight belongs to the next query date. Vara is the sunrise weekday
for a day report and civil weekday for an instant report. No skipped/repeated
tithi is invented to force one daily value. Event intervals use the new value
at the exact internal transition (right-continuous). Calendar labels must not
change merely because output rounding crosses midnight.

lunar_phases {start,end,context}: new/first-quarter/full/last-quarter events;
Vakya phases must use Vakya Sun/Moon, with profile-labelled times; an optional
physical-astronomy result must not replace them. period_intervals {date,context,
rule_set}; observances {start,end,context,rule_set,jurisdiction}; holidays
{year,jurisdiction,dataset_revision}. Return stable IDs, sourced display names,
rule/evidence IDs, dates and intervals where meaningful. No success-shaped empty
list when data/rules are unavailable.

Invalid context, unsupported definition, invalid Tamil date, outside coverage,
missing source data, invalid location/timezone and unavailable solar event need
distinct specified errors/statuses. Validate shape -> profile/context -> coverage
-> date/domain -> display options; freeze exact precedence in fixtures. No-rise
and no-set are legitimate solar-event statuses; a rule requiring sunrise must
fail explicitly there. Never use machine clock/timezone or fixed IST everywhere.

## Both profile specifications: mandatory source gates

For Thirukanitham pin a named, fully specified calculation definition,
geocentric/apparent solar and lunar
longitude definitions, ephemeris/version/coefficient provenance, TT/UT1/UTC
conversions, leap-second and delta-T model/range, precession/nutation/aberration,
ayanamsa definition/epoch/rate, angle wrap and tie convention. Pin sunrise upper
limb/centre, refraction, horizon/elevation, station, ingress-to-civil-date cutoff
and solar-year anchor. The IMD central station is not Chennai or Jaffna.
Publisher comparisons record disagreements, but the milestone does not require
a preferred publisher or universal publisher equivalence.

The required Vakiya definition may be the named, unmodified 1962 critical
Vakyakarana/Laghuprakashika edition. Transcribe and independently check its
epoch, ahargana, Sun tables, Moon vakyas/cycles, published corrections, units,
reference meridian, local adjustments, solar-month assignment and rounding.
Pin errata and edition variants when claiming compatibility with them; a
contemporary publisher is not a prerequisite for implementing the classical
profile. Do not import Drik longitude, delta-T or ayanamsa parameters into
Vakiya unless its chosen source explicitly requires them.

Shared limb geometry may be reused only after profile longitudes and time bases
are defined. IMD definitions support tithi 12-degree elongation, nakshatra and
yoga 13 degrees 20 minutes, and karana 6-degree half-tithi; karana names require
both cyclic and four fixed cases. This geometry is not a complete ephemeris.

Selected Thirukanitham strategy: deterministic Rust computation using the
MIT-licensed `astro` 2.0.0 provider, explicit 1956 Chitrapaksha anchor and P03
precession definition, finite time/zone/location rules, and JPL DE441 angular
checks. This toolkit definition is not asserted to reproduce every publisher.
For Vakiya, use genuine table-driven Rust computation from pinned canonical
constants. A finite compiled published-event table is an acceptable alternative for either profile only
with redistribution rights, complete transitions, explicit supported stations
and dates, no interpolation pretending arbitrary-location coverage, and an
independent second witness. Never fill gaps from the other profile.

The implemented Thirukanitham public date range is 2024-01-01..2027-12-31 for
the declared TN/SL coordinate boxes, with internal solar-ingress padding through
2028. The finite range is not a claim of exact equivalence to a publisher or of
all-location Tamil practice. Classical Vakiya civil conversion exposes solar
years 1..9999 from its source equation/table domain, with Gregorian labels from
0001-03-13; its five-limb Moon range has a separate Kali-day lower bound. This
is the defined calculation domain, not a claim of modern almanac accuracy
across all centuries. Expose per-operation coverage and reject padding dates as
query dates.

Time precision: integer seconds for instant input and internal event roots;
day-report sunrise/set and transition labels serialize as local integer minutes
rounded to nearest minute. The Drik root solver brackets to one UTC second and
is deterministic across targets. Independent published minute tables remain
separate compatibility witnesses; observed differences are recorded rather
than hidden with widened tolerances. Physical model accuracy is checked
separately against JPL DE441. Vakya acceptance is faithful reproduction of the chosen
tables/arithmetic at their resolution, not agreement with modern astronomy.
Source precision and rounding intervals must be recorded; day/limb assignment
has no tolerance. Near-cutoff differences against a named publisher remain
recorded compatibility findings for calendar review, not expanded tolerances.
These requirements remain open for Vakiya and observance rules.

## Independent fixtures and properties

Freeze operation schemas/errors and escaped expected JSONL before algorithms.
Keep suites planned until reviewed activation. Each success needs edition,
page/table/row, station, timezone, definition, raw source precision, conversion
of traditional time units and reviewer transcription trail. Store original
oracle outputs separately from expected projections; pin SHA-256/license.
An independent oracle cannot reuse runtime tables/code or derive expected dates
solely from round trips. Old errors and intentional unknown-operation cases stay.

- Independent Gregorian dates: year 1/9999, 1900/2000/2100 leap checks,
  1582 proleptic continuity, signed day arithmetic and month-end clamp/reject.
- Numeric: all ten digits; preserved punctuation/joiners; script mixing;
  zero/-zero; 256/257 digits; leading/trailing zeros; grouping and rejected
  exponents; decimal exact money .01/.10/.99 and precision failures; ICU ordinal
  irregulars/scale boundaries; all 20 fraction alternatives and invalid Kiizh;
  mixed negative magnitude, percent-versus-ratio and reversed ranges.
- Both calendar profiles: every daily date over final coverage, all 12 month
  boundaries each year +/-1 day; actual lengths; Chithirai/Thai changes;
  cycle wrap plus two same-name years if wider evidence obtained; independent
  Thiruvalluvar before/on/after boundary. No invented distant-year fixtures.
- All five limbs at sunrise and at exact transitions +/-1 second; angle wraps,
  new/full/quarter events, all fixed/cyclic karanas, repeated and skipped sunrise
  tithi/nakshatra, zero/one/multiple transitions per civil day, event after
  midnight, ingress near source cutoff, festival competing-day precedence.
- At least ten independently documented profile disagreement dates across solar
  boundary and lunar limbs. Same-source duplication is not independence;
  locate actual published paired outcomes before setting a count as satisfied.
- Chennai and another TN station; Colombo, Jaffna, Batticaloa, Vanni and
  Up-Country station coordinates from pinned geographic sources. Equal timezone
  does not imply equal sunrise. Label missing regional publisher evidence as
  missing. Probe UTC rollover; explicit fixed offset versus IANA zone; historical
  Colombo offset only if in range; ambiguous/nonexistent wall times rejected
  unless fold policy explicit. Latitude extrema/no-rise/no-set for computed
  solar events; table mode rejects unsupported stations.
- Errors: profile omission/unknown, mismatched definition, date out of domain,
  cycle-name-only ambiguity, invalid month/day, day beyond actual length,
  malformed time/zone, nonfinite/out-of-range coordinates, unavailable source
  and transition not bracketed. Never substitute empty data or current date.

Rust properties: 10,000 cases each for exact parse/format equivalence, money
minor-unit roundtrip, canonical traditional inverse, Gregorian/Tamil inverse
per profile, add-day/difference inverse, contiguous nonoverlapping limb
intervals, month coverage and monotone events. The Thirukanitham sector model
now has a 10,000-case bounded instant property plus independent JPL coordinate
checks. Clamp month/year arithmetic is
not an inverse property. Add independent expected results beside properties.

Proposed resource budgets to measure before acceptance: <=5 MiB additional
uncompressed runtime calendar data, <=2 MiB added compressed browser payload,
<=100 ms warm single-day query and <=2 seconds one-year calendar on a recorded
reference machine, no network and bounded event-search iterations. Table size
projection precedes acquisition at scale. Failure triggers documented design
revision, not hidden runtime downloads. Record Rust/Python/WASM/Dart timing;
no unbounded range query (maximum 366 civil days per call).

## Finite implementation sequence for Luna xhigh

1. **Completed:** freeze numeric contracts, exact new errors and independent
   ICU/exact-string vectors. Pin root RBNF and the reviewed Unicode 17 symbol
   subset. The numeric v0.3 suite is active by owner approval.
2. **Completed for the numeric slice:** implement Rust operations; compile
   canonical data; shared dispatcher and thin wrappers, 10,000-case properties,
   and real binding rebuild. Keep the full calendar gate matrix open.
3. **Calendar source work continues by bounded profile:** retain the implemented
   1962-edition Vakiya solar-transit, table-backed true-Sun, 248-row
   Candra-vakya true-Moon, caller-input local true-sunrise correction, and
   source-table Cara, Deśāntara, and Bhujaantara interpolation calculations as
   historical subprofiles. The Pai article's
   text-only cross-check is logged but is not used as fixture data until its
   equations/tables are visually verified. Independently verify additional
   Moon-cycle boundaries and connect the Cara and Deśāntara operations to
   independently sourced station/date inputs. For Bhujaantara, the new
   longitude-linear v1 convention is explicitly narrower than a date-derived
   equation-of-time pipeline. Thirukanitham v1 now uses the evaluated MIT Rust
   `astro` provider and a pinned custom Lahiri/P03 definition, with saved
   JPL DE441 references and observed publisher differences recorded. Pin
   editions/digests/
   licenses for each advertised profile and continue sourcing TN/SL witnesses,
   eras, periods, observances and holidays. Missing sources in those families
   do not block a distinct source-pinned numerical kernel; they still block
   claiming final calendar completion.
4. **Thirukanitham date/location path implemented in the worktree:** Rust owns
   the finite Sun/Moon provider, sidereal model, computed solar ingress dates,
   sunrise/sunset and five-limb instant/civil-day APIs. Its exact golden suite
   remains planned for separate calendar review. Continue only the review items
   recorded in the source ledger; do not replace source observations with
   outputs generated by this implementation.
5. **Bounded classical Vakiya civil path implemented in the worktree:** the
   1962 edition converts Gregorian/Tamil solar dates and returns five limbs at
   instants and Ujjain mean-sunrise days. Keep its suite planned. The new scan
   review confirms primary formulas for Cara, latitude/shadow, longitude
   reduction, precession, and day/night geometry, but the Bhujaantara table's
   date interpolation and connection to the Bhūpādi solar correction remain
   unresolved; Udayāntara is omitted by the edition. Do not expose arbitrary
   station daylight until those joins and source precision are resolved.
   Thirukanitham alone provides the source-backed primary phase events and
   daylight periods. Cycle titles are now available from the source-pinned
   1889 sequence. Continue with evidenced observances and jurisdictional
   holiday datasets with versioning.
6. The initial Vakiya solar-transit, true-Sun, true-Moon, Cara, Deśāntara,
   Bhujaantara and local true-sunrise
   correction operations are integrated through Python, Node/browser WASM,
   Dart and workbench forms.
   Continue integration for each newly implemented operation, with explicit
   profile/definition, station/zone,
   date/range, both-profile comparison, intervals/coverage/source details.
   Preserve the existing two local workbench commits and all unrelated changes.
7. Review expected-versus-observed acceptance matrix; activate reviewed suites;
   run just sync-release-files, check-release-policy, check-release-files,
   check-unicode, test-rust, sync-bindings, test-parity, test-dart,
   agent-post-edit, agent-pre-stop-gate; pnpm run check:workbench and
   pnpm run build:workbench; just release-check with isolated actual archives.
   Record interactive browser checks separately from browser WASM under Node.
   Update scope docs, README, CHANGELOG and status handoff during implementation.
   Update the contract, source ledger, README, CHANGELOG and status handoff during implementation.

Stop condition: every required row works inside its declared coverage in BOTH
profiles, with independent evidence and unchanged real-runtime parity; all gates
pass and limitations are documented. Unavailable calendar sources keep the
milestone open even if numeric additions pass. No additional user approval is
needed for routine authorized implementation choices; missing source facts and
redistribution rights are evidence blockers. Public crate/channel changes need
separate policy review; release-check uploads nothing. No publication implied.

## Candidate boundary after user scope revision

The user requested a releasable version with pending work recorded for later.
The broader completeness matrix above remains a future milestone, not a blocker
to the explicitly experimental alpha.5 candidate documented in
[the candidate record](../releases/numerals-calendar-candidate.md).
Krishna Jayanthi is excluded pending sourced annual month selection.
