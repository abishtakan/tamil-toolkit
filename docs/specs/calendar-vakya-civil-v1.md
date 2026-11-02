# Vākyakaraṇa classical civil and panchangam profile v1

Status: implementation contract and independent vectors are frozen; suite
`calendar_vakya_civil.jsonl` remains **planned** pending calendar-owner review.
This is an unmodified mathematical profile of the 1962 Vākyakaraṇa with
Laghuprakāśikā, not a Pambu, Arcot, Srirangam, or current publisher edition.
Its outputs are the classical model's results and make no claim of current
publisher equivalence or modern physical accuracy.

## Definition and references

- Definition ID: `vakyakarana-1962-laghuprakashika-civil-ujjain-mean-sunrise-v1`.
- Primary: *Vākyakaraṇa with Sundararāja's Laghuprakāśikā*, eds. T. S.
  Kuppanna Sastri and K. V. Sarma, 1962. Scan SHA-256:
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
  The scanned pages are image-only and the relevant equations/examples were
  visually checked at printed pp. 250–256 (PDF pp. 287–293), xvi (PDF p. 23),
  and 267–269 (PDF pp. 304–306).
- The Kali epoch's proleptic Gregorian equivalence and day-number convention
  are independently pinned by A. K. Bag, “Ahargaṇa and Weekdays as per Modern
  Sūryasiddhānta,” *Indian Journal of History of Science* 36(1–2), 2001, p. 63.
- R. Venketeswara Pai, “The rationale for Śrīrguṇamitrādivākyas as described
  in the Laghuprakāśikā,” *Journal of Astronomical History and Heritage* 22(3),
  2019, pp. 545–552, is an independent mathematical cross-check for the
  ahargaṇa and solar-transit derivation. It is not a source for publisher
  substitutions or a replacement for the primary edition.
- The 1962 edition's redistribution terms have not been established. The
  implementation encodes equations and compact table data; it does not bundle
  scan pages or source prose. Release promotion of the tables remains subject
  to the existing provenance/license review.

## Station, civil day, and coverage

The sole station is `ujjain`, fixed to the edition's Ujjain reference meridian
and to modern station coordinates 23°11′N, 75°47′E (IMD station metadata).
The civil day label is the proleptic-Gregorian date at Ujjain's **mean
sunrise**, not midnight and not a calculated local horizon sunrise. One Kali
day increments at that mean-sunrise boundary. Kali day zero is Friday,
3102 BCE-01-23 in proleptic Gregorian notation (astronomical year −3101),
06:00 local mean time at Ujjain. Its ordinal relative to Gregorian
0001-01-01 day zero is −1,132,960; the independent epoch source gives Julian
day number 588466 for this sunrise. The source's local mean time is not silently
treated as Indian Standard Time.

Date conversion has the exact Gregorian input domain 0001-03-13 through
9999-12-31. The first date is the source-model Chithirai 1 for solar year 1;
earlier Gregorian dates precede the finite year-number domain. The Saka elapsed
year is found by matching the source ahargaṇa
year-start boundaries, not by assuming a Gregorian year plus a constant. The
ahargaṇa equation is evaluated in rational arithmetic and rounded to the
nearest vināḍi (24 seconds). The civil date for each ingress is the first
Ujjain mean sunrise at or after the source-model crossing. A crossing exactly
at mean sunrise belongs to that date; any later crossing belongs to the next
mean-sunrise date. This rule reproduces the edition's independent worked
correspondence: at Kali day 1,844,004's mean sunrise, the Sun is 180 days
19 nāḍi 41 vināḍi past Meṣa and the edition labels the date the end of the
24th Kanyā. The footnote's day/night fraction rule applies to its reported
whole-day ahargaṇa, not as a half-day threshold for solar-month starts.

`context` is exactly `{ "reference_station": "ujjain", "time_zone": ... }`.
The supported time-zone identifiers are `Asia/Kolkata` and `Asia/Colombo`;
both use UTC+05:30 for instant conversion only in their declared stable
periods. Instant and day reports accept `Asia/Kolkata` from 1947-01-01 onward
and `Asia/Colombo` from 2007-01-01 onward. Earlier timezone-history
discontinuities are outside this v1 instant contract. Date conversion is
anchored to Ujjain mean-sunrise dates; choosing a display timezone does not
move its astronomical station. Unsupported stations and zones fail explicitly.

The 1962 solar equations are annual, not restricted to the two worked Saka
years. Solar date conversion therefore covers all civil years above, subject
to exact Gregorian and integer bounds. It does not promise equivalence to a
contemporary almanac. Five-limb calculations additionally require the printed
248-row Moon model's lower Kali-day bound (1,600,984); higher days are limited
by the exact JSON integer ceiling. The current compatibility date is reported
per operation, not inferred from a property of the Gregorian calendar.

Arbitrary latitude/longitude is unsupported. The 1962 local-sunrise reduction
requires Cara, Deśāntara, and Bhujaantara. The source gives the Deśāntara
scale and Bhujaantara endpoints but not the interpolation parameter; the
longitude-linear interpolation operation remains explicitly experimental and
is not called by this profile. Consequently, true local sunrise/sunset and
other-station local-day labels are not fabricated.

## Solar date conversion

Let `y = Saka_elapsed + 3179`. The source's ahargaṇa at the beginning of the
true solar year is

```text
A = 365*y + y/4 + (5*y - 1237)/576
```

with the complete expression evaluated as a rational number. One day is 60
nāḍi and one nāḍi is 60 vināḍi. The Vākyakaraṇa's existing true-Sun function
starts at Meṣa Saṅkramaṇa and uses the 37 printed Bhūpādi corrections at
10-day intervals. Its first approximation is elapsed days/clock-fraction as
degrees, followed by the edition's table interpolation and subtraction. The
12 sign boundaries are the first 24-second vināḍi at which that source true
Sun reaches the corresponding multiple of 30 degrees. This same source model
is used for Gregorian-to-Tamil and reverse conversion; no Drik longitude,
ayanāṃśa, or modern ephemeris is substituted.

Solar month indices are 1–12 in Mesha-through-Mina order and use the existing
canonical Tamil solar month labels. `solar_year` is the Gregorian year
containing the assigned Chithirai 1. Day is a count of mean-sunrise dates from
that month ingress, starting at 1. Reverse conversion rejects absent days;
it never clamps or rolls into a following month. `tamil_month_info` returns
the Gregorian start, exclusive end, and the source-model day count.

The primary worked civil correspondence is Saka elapsed 1869 / Kali 5048:
the edition gives ahargaṇa 1,843,823-40-19, assigns the New Year's day to
Monday after the nighttime ingress, and gives Kali day 1,844,004 as the end
of the 24th Kanyā. Bag's epoch equivalence maps Kali day 1,844,004 to
1947-10-11. The same source's true-Sun example at 180 days 19 nāḍi 41
vināḍi is 173°28′33″; its Moon example for that Kali day is 4 rāśi,
11°17′32″. These are the independent anchors in the planned vectors.

## Instant/day five-limb output

The profile's astronomy is evaluated at the specified instant after converting
the selected zone to the Ujjain reference meridian. The station offset is
longitude difference from the 82°30′E IST meridian at four minutes per degree:
Ujjain mean solar time is IST minus 26 minutes 52 seconds. All internal time
arithmetic uses integer seconds and rounds to the nearest 24-second vināḍi,
ties upward. This rounding applies only to astronomical position evaluation. Vara uses
the unrounded mean-sunrise day, so it changes at exactly 06:26:52 rather than
at a rounded vinadi carry. A civil-day scan includes its final second; rounded
transition labels carry into day offset 1 at midnight and remain ordered by
the exact underlying crossing time.

The true Sun is evaluated from elapsed time since the source
Meṣa event. The true Moon at integer Kali-day mean sunrise comes from the
existing 1962 248/3031/12372-day kernel; within the day its printed daily
motion is proportioned across elapsed vināḍi with integer truncation toward
zero. No latitude correction or experimental Bhujaantara is applied.

The five limb sectors use the source profile's own sidereal Sun/Moon angles:

- tithi = `floor(wrap(Moon - Sun) / 12°) + 1`, index 1–30; paksha is bright
  for 1–15 and dark for 16–30;
- nakṣatra = `floor(Moon / 13°20′) + 1`, index 1–27;
- yoga = `floor(wrap(Sun + Moon) / 13°20′) + 1`, index 1–27;
- karaṇa index = `floor(wrap(Moon - Sun) / 6°)`, index 0–59, using the seven
  cyclic names in sectors 1–56 and the four fixed cases in sectors 0, 57–59;
- vara is Friday advanced by the Kali-day number modulo seven.

Sector boundaries are right-continuous: an exact boundary belongs to the new
sector. `panchangam_at` returns the current five limbs at integer UTC Unix
seconds. `panchangam_day` returns transitions over the selected timezone's
midnight-to-midnight civil interval, rounded to nearest local minute, plus
limbs at the Ujjain mean-sunrise reference instant. The mean-sunrise label is
06:26:52 in either supported +05:30 zone (displayed minute 06:27); it is not a
claim of the true local sunrise. The sunset status is `unavailable` until the
source-defined Bhujaantara interpolation parameter is established. A day
report includes that status and reason instead of returning a fabricated
sunset or an empty success-shaped calendar.

## API and exact errors

Existing generic calendar operations dispatch by `definition_id`. Calls that
omit it through a high-level adapter keep the current Thirukanitham default.
Vakiya inputs use the exact context above; ordinary users never supply Kali
days, elapsed Mesha time, solar angles, shadow, or yojana corrections.
`calendar_profile_info` reports the definition, station, operation-specific
coverage, day boundary, equation IDs, fixed timezone assumptions, source URLs,
and the unsupported true-local-sunrise scope.

For all six generic operations the top-level request shape and exact fields
are validated first. Errors are `invalid calendar input`, `unsupported
calendar definition`, `invalid calendar context`, `unsupported location`,
`unsupported time zone`, `invalid Gregorian date`, `invalid Tamil date`, and
`outside supported calendar coverage` as applicable. Context checks precede
date-domain checks; date shape precedes profile dispatch, preserving the
shared dispatcher convention. Unknown zones/stations never fall back to the
machine locale. The planned suite validates the selected examples and
negative cases; it remains inactive until the owner separately reviews and
activates all calendar vectors.

## Still required for the full milestone

This profile is not the whole calendar milestone. The source-equation work
still must independently validate a non-flat Bhujaantara interpolation
parameter before supporting arbitrary locations or true local sunrise. The
bounded Drik lunar-phase API, both-profile solar enumeration/arithmetic,
Drik daylight periods and four official TN/SL holiday schedules are implemented.
Their calendar suites remain planned; schedule provenance, amendments and
broader year coverage remain review requirements. Tamil-script display,
sourced observances, arbitrary-location Vakiya daylight and the Thiruvalluvar-era
boundary remain open rows in the completion matrix. Do not mark the milestone complete or activate its
planned suites on the strength of these profile vectors.
