# Vakyakarana classical true-Moon arithmetic v1

This definition computes the Vakyakarana/Laghuprakashika table-based true
Moon for a Kali day number. It is a source-pinned historical arithmetic
profile, not a contemporary publisher's panchangam, a Drik ephemeris, or a
Gregorian calendar conversion.

## Definition and source

- Definition ID: `vakyakarana-1962-laghuprakashika-true-moon-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962.
- The visually inspected worked method/example is printed pp. 253–254
  (scan PDF pp. 290–291). It computes the true Moon for Kali day 18,44,004
  and reports 4 signs, 11 degrees, 17 minutes, 32 seconds.
- Appendix II, printed pp. 125–134 (scan PDF pp. 162–171), contains the
  248 day-indexed Candra-vakya values. All ten table pages were inspected
  visually at high resolution against the canonical projection. Each source
  row is stored as `[rasi, degrees, minutes]` in original day order, with
  seconds zero. The English verification note on printed p. 134 gives the
  first, penultimate, and last rows as 0-12-3, 0-15-41 and 0-27-44, and states
  the complementary-row rule. Its one visibly discordant printed pair is
  documented in the source ledger and preserved as printed.
- The inspected scan SHA-256 is
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
  Source prose and page images are not included. The edition's redistribution
  terms have not been established; this attribution does not assert an open
  license for the book or table.

## Input and domain

The operation is `vakya_true_moon_from_kali_day` with exactly
`definition_id` and `kali_day`. `kali_day` is an integer in
`1,600,984..=9,007,199,254,740,991`, the shared exact JSON integer range's
positive limit. Larger positive i64 values return
`outside supported calendar coverage`; the lower bound is the epoch subtracted
by the printed algorithm. Earlier days are not part of this contract. This
operation does not convert Gregorian dates or assign a local sunrise/day
boundary.

## Arithmetic

Let `e = kali_day - 1,600,984`. Use Euclidean quotient/remainder decomposition:

```text
q1, r1 = divmod(e, 12,372)
q2, r2 = divmod(r1, 3,031)
q3, r3 = divmod(r2, 248)
```

The source's angular constants, expressed in arcseconds, are 9-27-48-10,
11-7-31-1, 0-27-44-6, and the fixed dhruva 7-2-0-7. For a nonzero `r3`,
add table row `r3` and use `q3` cycles. For `r3 = 0`, use row 248 and one fewer completed 248-day cycle. This one-based normalization follows the 1–248 printed table; the source gives no worked example exactly at this boundary. The raw `q3` remains in the vinadi correction below.

The uncorrected longitude is the normalized sum of the three quotient terms,
dhruva, and the selected table value. Daily motion is the positive normalized
difference between this uncorrected longitude and the previous Kali day's
uncorrected longitude, so the 248, 3,031 and 12,372-day transitions use the
same arithmetic. The source's worked example verifies the ordinary
nonboundary case.

The source's signed vinadi adjustment is `v = 32*q3 - 8*q2`. Let `m` be the
daily motion in arcseconds and `b = 13 degrees, 11 minutes`. The correction is
`trunc_toward_zero((m - b) * v / 3600)` arcseconds. The printed worked example
has `m = 14 degrees, 12 minutes`, `v = 208`, and reports +211 seconds. Adding
the signed correction to the uncorrected Moon and normalizing to one full
circle gives the true Moon.

The output returns the definition, input Kali day, three raw quotients,
normalized table row number, uncorrected longitude, daily motion, signed
vinadi adjustment, correction in seconds and corrected true longitude.
Angles are `{rasi, degrees, minutes, seconds}` where one rasi is 30 degrees.
The source example establishes truncation toward zero to whole arcseconds.
Inputs and every integer output use the shared exact JSON range
`−9,007,199,254,740,991..=+9,007,199,254,740,991`; calculations retain i128
intermediates and reject unsafe quotients or corrections. No modern-astronomy
accuracy claim is made.

## Table concordance and fixture evidence

For each table row `n` from 1 through 247, printed p. 134 says to subtract row
`248 − n` from Bhavet sukham. In normalized arcseconds this requires
`row[n] + row[248 − n] = 12 rāśis + 27°44′` modulo one 360° circle. The build
validates this for every complementary pair and pins the first, final, and
reviewed rows. Printed rows 100 and 148 are a documented exception: their
visually printed values sum to `12 rāśis + 27°34′`, ten arcseconds short of
the stated rule. The lexicon preserves those printed values rather than
silently correcting the book. See the source ledger for page locators and the
four corrected transcription rows.

Only the Kali-day 18,44,004 result is a printed worked output. Table lookups,
one-based zero-remainder cases, and cycle-boundary expected values are derived
from the visually checked table and printed equations. They are regression
fixtures for this implementation, not independently observed historical
outputs.

## Errors and vectors

Both operations require exactly the documented keys, else
`invalid calendar input`. A missing, non-string, or unknown definition returns
`unsupported calendar definition`. A noninteger day returns
`expected an integer in the supported range`; a day below 1,600,984 returns
`outside supported calendar coverage`.

Escaped vectors are in `tests/golden/calendar_vakya_moon.jsonl`. The suite is
planned for its own review. Numeric v0.3 activation does not activate this
calendar suite.
