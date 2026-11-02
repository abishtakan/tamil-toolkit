# Calendar profile comparison v1

Status: planned calendar contract; it is not an accuracy ranking and does not
activate either calendar fixture suite.

`compare_calendar_profiles` accepts exactly one explicit comparison moment and
both fully specified contexts:

```json
{
  "date": {"year": 2026, "month": 4, "day": 14},
  "thirukanitham_context": {
    "region": "TN", "latitude_microdegrees": 13087840,
    "longitude_microdegrees": 80278470, "elevation_meters": 14,
    "time_zone": "Asia/Kolkata"
  },
  "vakya_context": {"reference_station": "ujjain", "time_zone": "Asia/Kolkata"}
}
```

The root object has exactly the keys `date` (or `instant_unix_seconds`),
`thirukanitham_context`, and `vakya_context`. A `date` is an integer
`{year,month,day}` and must be a valid Gregorian date. Date comparison is
bounded to the Thirukanitham 2024–2027 civil-date domain. The Thirukanitham
context has exactly `region`, `latitude_microdegrees`,
`longitude_microdegrees`, `elevation_meters`, and `time_zone`; TN accepts
`Asia/Kolkata` with the region's declared coordinate box and SL accepts
`Asia/Colombo` with its declared box. The Vākyakaraṇa context has exactly
`reference_station: "ujjain"` and `time_zone: "Asia/Kolkata" | "Asia/Colombo"`.
No arbitrary Vākyakaraṇa station is accepted.

For an instant comparison, `date` is replaced with `instant_unix_seconds`.
Supplying neither or both is an invalid calendar input. Both contexts are
validated before their profile calculations. Each selected profile calculation
runs once for that comparison. The operation reports each result, its
definition, context, and semantic basis, then lists fields whose returned
values differ. It does not normalize unlike solar-day definitions into an
assertion of equality.

The result has `comparison_basis` (`same_gregorian_civil_date` or
`same_utc_instant`), the original `moment`, `profiles.thirukanitham`,
`profiles.vakya_civil`, `differing_fields`, and
`accuracy_assessment: "not_assessed"`. Each profile entry contains its
`definition_id`, validated `context`, `semantic_basis`, and computed `result`.
Date results contain the Gregorian date and Tamil solar date; instant results
contain the existing panchangam-at response. Date differences use paths
`solar_date.solar_year`, `solar_date.month`, and `solar_date.day`; instant
differences use paths for each unequal returned civil date/time, vara, and
limb index/paksha. An empty difference list means only that those selected
reported fields match for the supplied inputs.

Date comparisons run one Gregorian-to-solar-date conversion per profile and
compare the resulting solar year, month, and day. Instant comparisons run one
instant panchangam calculation per profile and compare the reported local
civil date/time, vara, and limb indices. The Thirukanitham result is the
bounded local apparent-position profile at the supplied TN/SL coordinates. The
Vākyakaraṇa result uses its 1962 source tables and Ujjain mean-solar-time
positions with the chosen Kolkata or Colombo civil label. A difference is a
profile difference for these declared contexts and bases; it does not identify
which output is preferable.

Unsupported Vākyakaraṇa locations and unsupported dates/instants continue to
fail through the existing profile validators. The response must name both
contexts and both day/position bases even when no compared field differs.
Malformed shape or a missing/both comparison moments returns
`invalid calendar input`; a non-integer date component returns
`expected an integer in the supported range`; an impossible Gregorian date
returns `invalid Gregorian date`; invalid Thirukanitham context returns
`invalid calendar context`; unsupported Vākyakaraṇa station returns
`unsupported location`; unsupported zone returns `unsupported time zone`; and
dates outside the Thirukanitham comparison domain return
`outside supported calendar coverage`.

Planned vectors include a solar-date disagreement and an instant with
Thirukanitham/Vākyakaraṇa tithi and karana differences, alongside a same-instant
case where the selected fields happen to match. They also need timezone
context differences, each profile's cutoff, invalid/unsupported contexts and
the one-moment-only input rule. Current model-difference examples are explicitly
derived regressions; they do not independently establish accuracy. No equality
is manufactured.

Both entries also keep their definition-specific semantic basis and explicit
context next to each result. A same-date comparison may therefore report a
local apparent-position date at one supplied TN/SL location and a Vākyakaraṇa
Ujjain mean-sunrise date without implying that those are the same astronomical
day. An instant comparison likewise retains the Thirukanitham local civil
clock and the Vākyakaraṇa Ujjain mean-solar-time position basis. A match in
selected result fields is not a model-equivalence or accuracy claim.
