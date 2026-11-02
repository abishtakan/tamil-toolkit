# Bounded Thirukanitham lunar phase events v1

Status: implementation contract and independent source observations; the
`calendar_lunar_phases.jsonl` suite remains planned until separate calendar
owner review. This operation belongs only to the named Thirukanitham Drik
definition. It does not provide a third calendar profile or Vakiya phase
substitute.

## Contract

`lunar_phase_events` accepts exactly
`{definition_id,start_unix_seconds,end_unix_seconds}`. The definition must be
`thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2`. Inputs are whole UTC Unix
seconds in the existing 2024-01-01 through 2027-12-31 provider domain. The
interval is half-open `[start,end)` and may be at most 35 days. Invalid or
empty intervals fail with `invalid calendar input`; out-of-domain endpoints
fail with `outside supported calendar coverage`.

The result is `{definition_id,events}`. Events are sorted by their first UTC
second at the phase boundary. Each event has `phase`,
`ecliptic_longitude_difference_degrees`, and `utc_minute` with integer
`year,month,day,hour,minute`. The event root is solved at whole-second
resolution and its public UTC label is rounded to nearest minute, ties upward.
The four phase labels occur when geocentric apparent ecliptic lunar longitude
minus solar longitude is 0° (new), 90° (first quarter), 180° (full), or 270°
(last quarter), with increasing longitude difference. Events exactly at the
start are included; events at the exclusive end are omitted. A query with no
phase crossings returns an empty `events` array because that is a complete,
well-defined interval result.

These are global geocentric phase instants; no observer coordinates or local
time zone shift the root. The UTC output avoids attaching a local civil label
without context. The selected astronomy remains exactly the Thirukanitham
profile's pinned `astro` 2.0.0 apparent Sun/Moon model; results are not
relabelled as another Drik publisher's values.

## Independent definition and observations

The U.S. Naval Observatory defines the principal phases by the excess of
apparent ecliptic longitude of Moon over Sun at 0°, 90°, 180°, and 270° and
publishes their times in Universal Time. It explicitly states that the phase
instants are independent of observing location. The independent January 2025
expected times below are taken from its official phase API (`year=2025`):

| Phase | UTC minute |
| --- | --- |
| First quarter | 2025-01-06 23:56 |
| Full moon | 2025-01-13 22:27 |
| Last quarter | 2025-01-21 20:31 |
| New moon | 2025-01-29 12:36 |

Sources: <https://aa.usno.navy.mil/faq/asa_glossary> (definition),
<https://aa.usno.navy.mil/faq/moon_phases> (geographic independence), and
<https://aa.usno.navy.mil/api/moon/phases/year?year=2025> (worked expected
times). USNO publishes UTC to the nearest minute; the model contract also
reports UTC to nearest minute. The planned vectors retain USNO's values
unchanged so a model disagreement remains visible.

The operation's supported date range remains the Thirukanitham provider's
reviewed 2024–2027 range. Agreement with USNO is evidence for these expected
events, not a claim of exact current-publisher compatibility or full
astronomical accuracy outside the selected definition and domain.
