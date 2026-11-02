# Tamil solar-year enumeration and date arithmetic v1

Status: implementation contract and bounded-profile vectors are planned in
`calendar_solar_arithmetic.jsonl`; they do not activate either calendar suite.
Both operations dispatch through the existing Thirukanitham and classical
Vakyakarana 1962 definitions. The profile's own conversion boundaries remain
the source of every Tamil month date.

## `tamil_year_info`

Input is exactly `{definition_id,solar_year,context}`. The result contains
`definition_id`, `solar_year`, `start_date`, `end_date_exclusive`, total
`days`, and all twelve ordered `months`. Each month contains its 1-based
`month`, canonical `month_name`, Gregorian `start_date`, exclusive Gregorian
`end_date_exclusive`, and actual `days`. Vakiya results additionally identify
`reference_station` and `day_boundary`. The total range begins at Chithirai 1
and ends at the following Chithirai 1; month intervals are contiguous and
half-open. Coverage and context rules are exactly those of
`tamil_month_info` for the selected profile.
The `year_cycle` member reports the sourced romanized 60-year cycle title,
anchor and provenance documented in `calendar-year-cycle-v1.md`.

## `add_tamil_date`

Input is exactly
`{definition_id,date,unit,amount,overflow,context}`. `date` is a valid solar
Tamil date; `unit` is `days`, `months`, or `years`; `amount` is a safe integer;
`overflow` is `reject` or `clamp`. Output contains the selected
`definition_id`, the resulting `tamil_date`, its `gregorian_date`, and Vakiya
station/day-boundary metadata where applicable.

Adding days converts through the profile's existing Gregorian serial-day
operations, then reassigns the resulting civil date through that same
definition. Month/year addition first selects the target solar month in the
profile's anchored solar-year numbering. It preserves the day if the target
month contains it; otherwise `reject` returns `invalid Tamil date` and
`clamp` selects the target month's final day. It never wraps a missing date
into the following month. Input Tamil dates are validated before arithmetic;
all intermediate and resulting dates must remain in profile coverage.

Thirukanitham retains its 2024–2027 public date domain and TN/SL context
requirements. Vakiya retains solar years 1–9999, Gregorian labels beginning
0001-03-13, and the fixed Ujjain mean-sunrise civil boundary. Neither operation
extends a profile or fills unsupported dates.

Month/year addition uses internal ordinal month boundaries for target length,
then checks the resulting date's public coverage. A valid date in the final
partial month therefore supports zero additions and other valid target dates
even if that month's exclusive end is in Gregorian year 10000. Public month
metadata and full-year enumeration still fail when required endpoint dates
cannot be represented in the public Gregorian domain.

`tamil_year_cycle_info` is a separate operation for callers that need only the
cycle title. It validates the profile context and solar-year domain, then
returns the 1889 Table C romanized title sequence and its source metadata; it
does not extend either profile's ingress/date coverage.

The independent year vectors use Thirukanitham's saved JPL DE441 ingress
references plus its independently pinned Chennai report context, and the
Vakiya 1947 year uses the 1962 solar equations and Bag's Kali epoch
correspondence. The Vakiya day-add anchor is the printed Kali day 1,844,004
mapping to the end of Purattasi 24 on 1947-10-11. These vectors stay planned
pending separate calendar-owner review.
