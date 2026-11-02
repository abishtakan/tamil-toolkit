# Vakyakarana local true-sunrise correction v1

This definition applies the 1962 Vakyakarana correction from a source-time
true longitude and daily motion to a caller-supplied local true-sunrise
adjustment. It does not calculate sunrise, longitude difference, Cara,
Deśāntara, Bhujaantara, or a civil date.

Cara can be computed separately from a supplied Sayana Sun and equinoctial
shadow using [the bounded Cara definition](calendar-vakya-cara-v1.md).
Deśāntara can be computed separately from a supplied signed yojana distance
using [the bounded Deśāntara definition](calendar-vakya-desantara-v1.md).
Bhujaantara can be supplied using [the experimental longitude-linear
convention](calendar-vakya-bhujaantara-v1.md). This
reduction still takes all three terms explicitly; it does not derive the
station shadow or yojana distance from a date and location.

## Definition and source

- Definition ID: `vakyakarana-1962-laghuprakashika-local-sunrise-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962. The inspected scan has SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
- Printed p. 255 (scan PDF p. 292), lines 14b–16a, says to add algebraically
  half the Cara day-length difference, the Deśāntara sunrise difference, and
  the Bhujaantara part of the equation of time. The longitude-linear
  interpolation supplied by the companion operation is an experimental
  convention; this source does not specify that interpolation equation.
  Multiply true daily motion in
  degrees by the resulting vināḍis and use it as arcseconds, adding or
  subtracting according to the sign.
- Printed p. 256 (scan PDF p. 293), Example 4(b), applies `+13.0 −26.6 −21.0
  = −34.6` vināḍis to the printed true Moon `4 rasi 11°17′32″`, with daily
  motion `14°12′`. It reports a subtractive reduction of `491″` and local
  true-sunrise Moon `4 rasi 11°09′21″`.
- A 2026-11-02 re-retrieval from the publisher-hosted PDF URL byte-matched the
  retained scan (11,159,128 bytes; SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`). The
  Introduction, printed p. xv, gives the half-daylight equation
  `sin h = tan(latitude) tan(solar declination)` and says one degree is ten
  vināḍis; p. xvi gives one nāḍi per 55 yojanas and equates that to 6° of
  longitude. Printed p. 267 says to apply the edition's precession before
  declination and Cara. Printed p. 268 rule 6 and p. 269 Example 19 describe
  latitude from equinoctial shadow, including a 12-angula gnomon and the
  Pudukkottai 2.2-angula shadow / 10°34′ example. Printed p. 269 rules 7–8
  define the Cara coefficients and derive day/night length.
- These passages expose more of the geometry than the existing kernel used,
  but they do not remove the blocker: p. 255's non-flat Bhujaantara
  interpolation remains unspecified, p. xvi does not connect its conceptual
  mean/true-Sun definition to the p. 255 table or the p. 252 Bhūpādi series,
  and Udayāntara is explicitly omitted. Arbitrary-location sunrise/sunset
  therefore remains unavailable; no extra astronomy model or assumed
  interpolation has been substituted.
- Page images and source prose are not included. Redistribution terms for the
  edition have not been established; the attribution does not assert an open
  license for the book.

## Input and arithmetic

The operation is `vakya_reduce_to_local_true_sunrise` and accepts exactly
`definition_id`, `true_position`, `daily_motion`, `cara_half_vinadi_tenths`,
`desantara_vinadi_tenths`, and `bhujaantara_vinadi_tenths`. Angle fields are
integer sexagesimal objects. `true_position` is `{rasi, degrees, minutes,
seconds}` with a 0–11 rasi and normalized subfields. `daily_motion` is
`{degrees, minutes, seconds}` in `[0,360°)`. Each signed local-time term is an
integer number of tenths of a vināḍi; this keeps decimal approximations such as
the printed 26.6 exact and avoids floating point. The caller supplies the
already sourced terms; the operation does not infer them from a location.

Convert daily motion to arcseconds `m`. Sum the three signed terms as `v`, in
tenths of a vināḍi. The signed arcsecond correction is
`trunc_toward_zero(m * v / 36,000)`, since one day has 3,600 vināḍis and the
input uses tenths. Add this signed correction to the true position and
normalize the result to one 360-degree circle. This contract truncates the
arcsecond correction toward zero to match the edition's integer-angle
precision; the source does not separately state how a fractional arcsecond is
rounded. The printed Moon example produces `v = −346`, `−491″`, and
`4 rasi 11°09′21″` under that rule.

Every integer input and output is bounded to the shared exact JSON range
`−9,007,199,254,740,991..=+9,007,199,254,740,991`. Each signed adjustment
term is checked before calculation, and the summed adjustment and correction
are checked after i128 arithmetic; an unsafe input, sum, or correction returns
`outside supported calendar coverage`. A sexagesimal angle with an out-of-range field returns
`invalid calendar angle`. Exact shape, unknown-definition, and integer errors
follow the calendar error policy used by the other source-pinned operations.
The planned fixtures are separate from numeric v0.3 activation.
