# Vakyakarana classical solar-transit arithmetic v1

This specification defines one narrow, historical Vakiya calculation. It is
not a contemporary Pambu/Manonmani, Arcot, or Srirangam calendar profile and
does not assign Gregorian dates to Tamil months.

## Definition and evidence

- Definition ID: `vakyakarana-1962-laghuprakashika-solar-transits-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962.
- Primary page: printed English translation p. 251 (scan PDF p. 288), which
  gives the ahargana worked example for Saka 1869 and the solar-vakya list.
  The inspected scan is image-only, SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
- Independent research cross-check: Venketeswara Pai R., “The rationale for
  Srirgunamitradivakyas as described in the Laghuprakashika,” *Journal of
  Astronomical History and Heritage* 22(3), 545–552 (2019), especially pp.
  546–547, DOI 10.3724/SP.J.1440-2807.2019.03.13. Publisher text was retrieved
  from the PDF endpoint, but the PDF bytes could not be acquired or visually
  inspected; its OCR text is not used as runtime data or as a golden value.
- The 1962 scan's rights statement was not established. This implementation
  independently expresses mathematical facts and short Latin transliterations;
  it does not include source prose, page images, or a copied code listing.
  Bundling the finite mathematical table does not assert that the book or
  article is openly licensed. The project must resolve redistribution terms
  before promoting this data into a public release.

## Supported contract

Input is exactly an object with `definition_id` and `saka_year_elapsed`.
Coverage is limited to Saka years 1869 through 1890 inclusive, anchored by
the source's worked examples at both endpoints. `saka_year_elapsed` is an
integer. The corresponding Kali year is `y = saka_year_elapsed + 3179`.

The source's ahargana is evaluated exactly as

```text
A = 365*y + y/4 + (5*y - 1237)/576
```

where the fractions are rational, not truncated integer divisions. `A` is
measured in days from the Kali epoch, stated in the edition as mean sunrise at
Ujjain on Friday. One day is 60 nāḍi and one nāḍi is 60 vināḍi. The integral
vināḍi representation rounds the exact fractional day to the nearest vināḍi
(half up); no half-vināḍi tie occurs in the supported interval. The weekday is
the Kali Friday advanced by `floor(A) mod 7` days.

The twelve annual solar vakyas in the canonical data are added to the annual
dhruva (`floor(A) mod 7` days plus the nāḍi/vināḍi remainder). A transit's
`day_field` is the unwrapped sum of those day fields and any time carry; it may
exceed seven. Its weekday is Kali Friday advanced by `day_field mod 7`. The
order is Vṛṣabha through Mīna followed by Meṣa of the next solar year.

The operation `vakya_true_sun_from_mesha_elapsed` implements the historical
true-Sun correction from printed translation pp. 252–253 (scan PDF pp. 289–290).
Its caller supplies elapsed days, nāḍi, and vināḍi from Meṣa Saṅkramaṇa; it
does not find that event from a civil date. The approximate Sun is
`elapsed_days° + nāḍi′ + vināḍi″`. The 37 Bhūpādi corrections in the canonical
table are arc minutes at 10-day intervals from 10 through 370 days, with the
Mesha origin fixed at zero. The correction is linearly interpolated through
elapsed vināḍi and rounded to the nearest arcsecond, then subtracted from the
approximate Sun and normalized to 0°–359°59′59″. The edition's worked example
at 180 days, 19 nāḍi, 41 vināḍi produces approximate Sun 180°19′41″, correction
6°51′8″ and true Sun 173°28′33″. This is a table-backed historical model,
not a modern ephemeris or a contemporary publisher's corrected calendar.
Elapsed time is limited to 0–370 days; at day 370 the time remainder must be
zero because no later correction point is tabulated.

The transit result returns the profile ID, Saka and Kali years, the ahargana
day/time and weekday, and twelve source-ordered transit residuals. The true-Sun
result returns its approximate angle, interpolated correction and corrected
angle. These operations do not provide a Gregorian date, month-start
civil-day assignment, local time or timezone, regional adjustment,
sunrise/sunset, Moon position, panchanga limbs, periods, observances, holidays,
or current publisher corrections. COMMON dialect scope means only that this
arithmetic is not language-dialect dependent; it makes no TN/SL calendar-
coverage claim.

Errors and precedence:

Both operations require an object with exactly their documented keys, else
`invalid calendar input`. A missing, non-string, or unrecognized definition ID
returns `unsupported calendar definition`. The transit operation then checks
integer Saka year and the 1869–1890 coverage range. The true-Sun operation
checks integer elapsed fields, validates nāḍi and vināḍi in 0–59 (else
`invalid calendar time`), then checks its elapsed-time coverage range. Integer
type failures return `expected an integer in the supported range`. Calendar
JSON integer fields also obey the shared exact range
`−9,007,199,254,740,991..=+9,007,199,254,740,991`; values outside it return
`outside supported calendar coverage`.

Calendar vectors remain in a planned suite. The owner's activation of the
numeric v0.3 suite did not activate calendar fixtures.
