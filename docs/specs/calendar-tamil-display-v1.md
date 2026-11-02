# Tamil calendar display v1

Status: planned calendar contract. The operation vectors remain planned and this
document does not activate or approve a calendar suite.

## Scope

This contract adds explicit display rendering on top of the existing calendar
definitions. It does not change the current Romanized fields or default response
shapes. The engine still computes dates and limbs using the selected Rust
profile; display data only supplies indexed names and templates.

Supported display choices are `script: "tamil" | "romanized"`,
`digits: "tamil" | "latin"`, and styles `day_month_year` and
`weekday_day_month_year`. The fixed engineering templates are respectively
`{day} {month} {solar_year}` and `{weekday}, {day} {month} {solar_year}`.
They do not claim publisher-specific punctuation, inflection, or a general
Tamil date-writing convention. Tamil digits use the existing Rust
`convert_digits` operation. No language conversion is implicit.

`format_tamil_date` accepts exactly
`{definition_id,date,context,script,digits,style}`. `date` is a Gregorian civil
date. The profile context is mandatory and is validated by the same constructor
as the corresponding calendar operation before its date coverage is applied.
`definition_id` is exactly
`thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2` or
`vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1`. A
Thirukanitham context has exactly `{region,latitude_microdegrees,
longitude_microdegrees,elevation_meters,time_zone}`; TN uses `Asia/Kolkata`
and the declared TN coordinate/elevation ranges, while SL uses
`Asia/Colombo` and the declared SL ranges. A Vākyakaraṇa context has exactly
`{reference_station,time_zone}` with `reference_station: "ujjain"` and either
supported civil zone. Context shape errors return `invalid calendar context`;
unsupported locations or zones retain the profile validator's
`unsupported location` or `unsupported time zone` error. An unknown definition,
malformed Gregorian date, non-integer date component, unsupported script,
digit style or date style returns respectively `unsupported calendar
definition`, `invalid Gregorian date`, `expected an integer in the supported
range`, `unsupported calendar display script`, `unsupported digit style` or
`unsupported calendar date style`.
The date is converted once by the selected profile. Thirukanitham remains
limited to its declared 2024–2027 civil-date coverage; Vākyakaraṇa remains
limited to the source profile's civil-date domain and Ujjain station/time-zone
choices. Unsupported locations still fail.

`calendar_display_info` accepts exactly
`{definition_id,date,context,script,digits}` and returns the selected profile's
computed Tamil solar date, its chosen month and weekday labels, cycle index and
label, and the actual five-limb values at that profile's computed day
boundary. It translates the returned limb names and includes the source
metadata for each selected label. This operation therefore requires both the
profile's solar-date and panchangam-day coverage: Thirukanitham's declared
2024–2027 range, or Vākyakaraṇa's declared civil-day and lunar-source range for
the selected zone. It also reports the profile's day-boundary and position
basis so the shared labels do not imply that the profiles calculate equal
astronomical instants. The date weekday follows the Gregorian civil date; the
`vara` field is the profile's panchangam-day value. This operation does not
claim a festival or observance selection.

The Tamil script rows are extracted as short lexical facts from Tamil Virtual
Academy's educational panchangam page, with its spellings and known table
irregularities preserved in `lexicon/calendar-tamil-display.toml`. The page's
reuse terms were not located; no license or permission is asserted. Unicode
CLDR 49's Tamil Gregorian wide weekday names provide an independent weekday
witness and are covered by Unicode's data terms. Tamil weekday names in the
Latin-script formatting style use the specific transliterations in Vidya
Mohan and Rajiv Ranjan's *Basic Tamil* (2024), chapter 6.1; that text labels
them CC BY-NC 4.0, so the noncommercial condition and attribution remain
applicable. The cycle labels
are the numbered Tamil names on the Tamil Virtual Academy page; their index
order is cross-checked against the source-pinned CICT cycle table. The existing
1889 Romanized cycle labels remain unchanged and continue to identify their
own source.

Tamil display names are factual names, not prose. No Punarchi, case ending,
regional grammar, or issuer holiday name is synthesized. The displayed solar
year is the existing profile's Gregorian year identifier containing its
source-model Chithirai 1, not a Thiruvalluvar-era year. Romanized month and
limb names are the selected calendar profile's existing output values; the
display layer exposes them unchanged and claims no new transliteration
standard. The returned metadata labels this policy separately from the
source-backed Tamil spellings and weekday transliterations.

## Validation and planned vectors

Planned vectors must cover both definitions, Tamil and Romanized script,
Tamil and Latin digits, both styles, month and year-cycle source labels, all
limb tables, unsupported script/digit/style values, malformed contexts,
unsupported Vākyakaraṇa locations, invalid Gregorian dates, and profile
coverage boundaries. Independent expected strings come from the frozen
source labels and template contract; profile-computed solar dates remain
separate derived regression cases.
