# Thirukanitham calendar profile v1

Status: implementation contract; its golden suite remains **planned** pending
the separate calendar acceptance review. Numeric v0.3 approval does not
activate this suite.

## Identity and scope

`thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2` is this toolkit's bounded,
reproducible Drik definition. It is not a claim that every publisher or every
Tamil almanac uses the same ephemeris, ayanamsa, sunrise convention, rounding,
or ingress rule. The selected model uses Rust `astro` 2.0.0 (MIT), its VSOP87-D
Earth/Sun implementation and partial ELP-2000/82 Moon series, plus the profile
rules below. The dependency's approximate Delta-T routine is not used.

Public civil-date coverage is 2024-01-01 through 2027-12-31 inclusive. Internal
astronomical padding covers the solar ingress roots needed for those dates;
padding dates are not accepted as public query dates. The only supported
regions/zones are:

| Region | IANA zone | Supported coordinates |
| --- | --- | --- |
| `TN` | `Asia/Kolkata` | latitude 8.000000°..13.700000° N; longitude 76.000000°..80.500000° E |
| `SL` | `Asia/Colombo` | latitude 5.800000°..9.900000° N; longitude 79.400000°..82.000000° E |

Elevation is an integer metre in −100..=3000. Coordinates are signed integer
microdegrees. Chennai and Colombo reference points are recorded in the source
ledger. These regional boxes are the complete supported-location contract;
there is no machine-zone lookup and no polar-location behavior is implied.
Both zone rules are pinned to IANA tzdata 2026f and the supported civil range
has UTC+05:30 in both zones.

`solar_year` is the Gregorian year in which that year's Chithirai begins. The
solar month numbering is 1 Mesha/Chithirai, 2 Vrishabha/Vaikasi, 3 Mithuna/Aani,
4 Karka/Aadi, 5 Simha/Avani, 6 Kanya/Purattasi, 7 Tula/Aippasi,
8 Vrischika/Karthigai, 9 Dhanu/Margazhi, 10 Makara/Thai, 11 Kumbha/Maasi,
12 Mina/Panguni. `solar_year` is not a Thiruvalluvar year or a named 60-year
cycle year.

## Ephemeris and time definition

The Sun and Moon are evaluated at `TT = UTC + 69.184 s`, using the pinned
`TAI − UTC = 37 s` plus `TT − TAI = 32.184 s`; this applies only while that
leap-second assumption remains true. Earth rotation uses `UT1 = UTC`, with the
documented bound `|UT1 − UTC| ≤ 0.9 s`. The supported range does not use the
crate's forecast Delta-T polynomial. Any later leap-second announcement
requires a profile version change or revised time data.

The 23°15′00.658″ Chitrapaksha/Lahiri anchor at JD(TT) 2435553.5
(1956-03-21 00:00 TDT) is a **true** ayanamsa, relative to the true equinox
and including nutation. It is not a mean-coordinate anchor. The selected
`astro` 2.0.0 63-term IAU 1980 nutation model gives +16.768479927″ in longitude
at that epoch, so the profile derives the mean anchor by subtracting that
value: 23°14′43.889520″. The positive sign and subtraction are checked against
an independent ERFA/SOFA IAU 2000A evaluation (+16.777905560″); the 0.009426″
difference is the declared nutation-series difference. The anchor, derivation
and independent checkpoints are recorded in `lexicon/calendar-thirukanitham.toml`
and `tests/reference/calendar-thirukanitham-v1/independent-transforms.json`.

The mean anchor advances using the IAU 2006 P03 general-precession-in-longitude
polynomial `5028.796195 T + 1.1054348 T² + 0.00007964 T³ − 0.000023857 T⁴ −
0.0000000383 T⁵` arcseconds, where `T` is Julian centuries from J2000. This
creates the mean ayanamsa. The same 63-term IAU 1980 nutation in longitude is
added to obtain the true ayanamsa at each instant. Sidereal longitudes
consistently subtract this true ayanamsa from the profile's apparent
coordinates. Since both sides use the same nutation model, date-dependent
nutation cancels; it is not silently left in a sidereal ingress or limb
coordinate. The named sidereal definition is
`lahiri-1956-true-anchor-p03-true-iau1980-v2`; it does not assert equivalence
to a commercial Lahiri implementation.

The solar coordinate is VSOP87-D geocentric mean ecliptic longitude plus the
provider's FK5 correction, IAU 1980 nutation in longitude, and solar annual
aberration. It has no separate light-time or gravitational-deflection
correction. The lunar coordinate is partial ELP-2000/82 geocentric mean
longitude plus the same IAU 1980 nutation; no separate FK5, lunar aberration,
light-time, or gravitational-deflection correction is applied. These are
bounded apparent-longitude approximations. Differences from JPL apparent
coordinates are measured against saved JPL values; expected corrections are
not removed from JPL to conceal model error. Longitude wraps into `[0°, 360°)`,
and an angle exactly on a limb boundary belongs to the following limb
(right-continuous intervals).

The root solver bisects integer UTC seconds and returns the first second at or
after a crossing. A civil-day report searches exactly the half-open local
interval `[local midnight, next local midnight)`; membership uses the exact
root even when its display minute rounds onto an adjacent date. Each event's
display date, day offset and minute are derived together by rounding the local
timestamp to the nearest minute, with exact half-minute ties rounded forward.
Events sort by exact root instant, with a stable limb order only for exact
ties. Rise/set labels use the same nearest-minute half-up rule. Instant queries
accept integer Unix UTC seconds and do not round input.
All JSON numeric values are integers within the JavaScript safe-integer range;
no astronomical floating-point value is serialized.

## Sunrise, sunset, and solar-month day assignment

The solar center crosses an apparent altitude of −47 arcminutes at a sea-level
unobstructed horizon: 31′ horizontal refraction plus the 16′ solar
semidiameter. Elevation raises the effective horizon by geometric dip computed
from a 6,371,000 m spherical Earth radius. The Sun is evaluated geocentrically;
terrain, pressure, temperature, local obstructions, and observer-specific
refraction are outside this profile. A failed rise/set root is an explicit
`solar event unavailable` error; no fabricated event or empty-success result
is allowed. The supported latitude bands have one sunrise and one sunset on
each covered civil date.

Solar months are defined by geocentric apparent Sun longitude crossing a
sidereal 30° sign boundary. The ingress opens the same local civil date if it
is at or before that date's computed sunset; otherwise it opens the following
local civil date. Exact ingress/sunset equality is assigned to the ingress
date. The contract is local to the supplied region, coordinates, elevation,
and zone; it does not assert one universal rule for all almanacs.

## Limbs and operations

Tithi is the 12° geocentric apparent Moon-minus-Sun elongation sector, numbered
1..30;
paksha is `shukla` for sectors 1..15 and `krishna` for 16..30. Nakshatra is
the 13°20′ true-sidereal apparent Moon sector, numbered 1..27. Yoga is the
13°20′ sector of the wrapped sum of true-sidereal apparent Sun and Moon,
numbered 1..27. Karana is the 6°
half-tithi sector, indexed 0..59. Sector 0 is Kimstughna; sectors 1..56 cycle
through Bava, Balava, Kaulava, Taitila, Gara, Vanija, and Vishti; sectors 57..59
are Sakuni, Chatushpada, and Naga. Vara is the local weekday attached
to computed sunrise for a day report, and the local civil weekday for an
instant report. Four angular limbs have transitions during the local civil
day; vara is reported at sunrise and changes at the next sunrise.
`panchangam_day` reports the local civil weekday of the report date (the
weekday at its sunrise). `panchangam_at` reports the local Gregorian civil
weekday, including before sunrise; it does not return the traditional
sunrise-to-sunrise vara for the previous date.

The shared dispatcher operations are:

- `calendar_profile_info {definition_id}`
- `gregorian_to_tamil_date {definition_id,date,context}`
- `tamil_to_gregorian_date {definition_id,date,context}`
- `tamil_month_info {definition_id,solar_year,month,context}`
- `panchangam_at {definition_id,instant_unix_seconds,context}`
- `panchangam_day {definition_id,date,context}`

Dates have integer `year`, `month`, `day`; the Tamil date has `solar_year`,
`month`, `day`. Context requires `region`, `latitude_microdegrees`,
`longitude_microdegrees`, `elevation_meters`, and `time_zone`. Public Gregorian
dates and dates produced by reverse conversion must fall inside the coverage
range. Reverse conversion resolves the actual month start and next start,
validates `day` against that true month length, then checks the resolved
Gregorian date against public coverage. This permits valid days in a partial
2023 month that resolve in 2024, while rejecting unsupported dates and invalid
days in partial or final months. Solar years 2023..=2027 are accepted only
when the resolved Gregorian date is in public coverage. Date conversion uses the computed
ingress-day table; it never assumes April 14, a fixed month length, or
Gregorian year + 31.

Validation precedence is: operation-specific required-field/type validation;
definition id; region, zone, coordinate/elevation context; public coverage;
Gregorian or Tamil date validity; computed event availability. The stable
errors are `expected an integer in the supported range`, `unsupported calendar
definition`, `invalid calendar context`, `unsupported time zone`,
`unsupported location`, `outside supported calendar coverage`,
`invalid Gregorian date`, `invalid Tamil date`, and `solar event unavailable`.

## Evidence and acceptance separation

The physical comparison uses actual production apparent solar and lunar
longitudes, apparent elongation, true-sidereal longitudes and derived
coordinates against saved NASA/JPL Horizons DE441 apparent geocentric
ecliptic-of-date values. JPL reports UTC times and apparent coordinates using
its documented IAU 1976/1980 model, including light-time, solar gravitational
deflection and stellar aberration. Toolkit TT is pinned to UTC+69.184 s;
Horizons input/output times remain UT/UTC. Independent ERFA/SOFA IAU 2000A
nutation and the published P03 polynomial transform JPL samples to the Lahiri
sidereal frame. Query settings, raw-response hashes, extracted rows and the
transform recipe are in the reference manifests. The physical tolerances
remain Sun ≤1.0 arcsecond and Moon ≤10.0 arcseconds. Composite elongation and
yoga error bounds are the measured sum of component coordinate errors; they
do not widen either primitive tolerance.

Independent root evidence covers 49 public solar month ingresses plus the
terminal ingress after coverage, and 43 limb transition roots. Raw JPL
positions are sampled at one-second cadence around each selected root and
classified with the independent ERFA/P03 transform; the profile roots are
within 3 seconds of the JPL ingress brackets and 4 seconds of the limb
brackets. Separately, independent 60-second JPL sweeps cover eight full local
civil days across 40 Chennai, Colombo, Jaffna and Jaffna-elevation report
contexts. The JPL-derived event sets contain the same 43 limb transitions as
the full Rust reports, with no missing or extra crossing. The report rows and
window centers are profile-derived; only the JPL classifications and brackets
are independent expected evidence. Coverage includes the partial month at
2024-01-01 and the final public month plus its exclusive 2028 ingress.
Exact cross-runtime JSON parity is separate evidence.

The 2026-11-01 Chennai comparison retains each observed difference without
claiming a cause. The saved publisher snapshot reports sunrise 06:03, sunset
17:42, yoga change 14:39, tithi/karana change 14:51 and next-day Pushya exit
04:30. The corrected profile reports 06:02, 17:43, 14:39, 14:52 and 04:31.
Colombo reports 05:58/17:50 at the publisher and 05:58/17:51 in the corrected
profile. Component variants measure the former mean-coordinate pipeline's
2026 Chennai roots, the Lahiri-anchor and apparent-coordinate corrections,
and the model's elevation sensitivity. At zero elevation with the same −47′
horizon, Chennai reports 06:02:49/17:41:59 and Colombo 05:58:05/17:50:14;
those values round to the saved publisher daylight labels. This demonstrates
a possible elevation contribution, not the publisher's actual setting or the
cause of the remaining limb differences. Exact values, old-to-corrected root
deltas, and the full day comparison are in
`tests/reference/calendar-thirukanitham-v1/publisher-correction-components-2026-11-01.json`.
Adjacent Chennai pages place the Nov 1 03:51 and 05:39 events on the Oct 31
sunrise-day, while the toolkit includes them in the Nov 1 midnight-to-midnight
report. The Nov 1 page's next-day 04:30 Pushya exit is followed by Ayilyam at
the Nov 2 sunrise. These neighboring observations reconcile day assignment
and after-state, not the publisher's exact roots or calculation settings. The
saved short observations, page URLs and digests are in
`tests/reference/calendar-thirukanitham-v1/drik-panchang-observations-2026-11-01.json`.
Adjacent observations and extraction receipts are in
`tests/reference/calendar-thirukanitham-v1/drik-panchang-adjacent-observations-2026-10-31_11-02.json`.
No publisher page bytes were retained, so these hashes alone cannot reproduce
the extracted values. The receipt preserves factual fields, source URL and
query date, not page text or markup; it cannot be re-audited against a local
page snapshot. Independent JPL requests and outputs are recorded in
`horizons-root-request-manifest.json`, `independent-root-observations.json`,
`horizons-full-day-request-manifest.json` and
`independent-full-day-observations.json`; raw response digests and
transformation script versions are included there.
Those publisher pages report sunrise-day limb cutoffs, not every transition in
the civil `[midnight,next midnight)` interval; they are compatibility evidence
and do not supply complete exact `panchangam_day` golden outputs. Rust tests
check the observed minute differences directly while the shared golden suite
keeps independently sourced instant categories.
The publisher page does not document the internal engine or full model settings,
so these remain compatibility findings with unassigned cause. The suite remains planned pending separate calendar
review, and no publisher equality guarantee is made. The saved IMD regional
calendar independently witnesses the solar month boundaries for the cited
2026–27 rows. Full Vakiya date, location, and five-limb support remains a
separate unfinished requirement.
