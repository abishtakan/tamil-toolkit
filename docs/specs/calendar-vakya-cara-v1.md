# Vakyakarana Cara interval v1

This operation computes the signed Cara interval from a supplied Sayana solar
longitude and the place's equinoctial shadow. It does not calculate the
precession, solar longitude, observer's latitude, or equinoctial shadow from a
Gregorian date or coordinates.

## Definition and source

- Definition ID: `vakyakarana-1962-laghuprakashika-cara-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962. The inspected scan has SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
- Printed pp. 267–269 (scan PDF pp. 304–306), rules 1–7 and Example 20,
  define Bhuja by the distance from the nearest 90-degree point, give Cara
  interval coefficients 20, 16 and 6⅔ (exactly 20/3) for successive
  30-degree Bhuja segments, multiply each interval by the equinoctial shadow,
  and assign a negative sign
  for Sayana longitude from 0 to 180 degrees and a positive sign from 180 to
  360 degrees.
- Example 20 uses Sayana longitude 4 rasi 22°30′ (3 rasi 29° plus 23°30′),
  an equinoctial shadow of 3 angulas, and Bhuja 1 rasi 7°30′. It obtains
  `20 × 3 + 16 × 3 × 7°30′ / 30° = 72` vināḍis, negative because the Sayana
  longitude is in the first half of the circle. The expected result is −72
  vināḍis.
- The source's example lands on an integer vināḍi and does not exercise the
  third coefficient. For general sexagesimal inputs this operation returns
  tenths of a vināḍi. It accumulates the exact rational contribution of every
  complete and partial segment, then truncates only the final fractional tenth
  toward zero; the edition does not state a finer rounding rule. The canonical
  `lexicon/calendar-vakya-solar.toml` stores all three coefficients as exact
  numerator/denominator pairs and `build.rs` validates and compiles them.
- The scan image and source prose are not included. The attribution does not
  assert an open license for the book.

## Input and arithmetic

The operation is `vakya_cara_from_sayana_sun` and accepts exactly
`definition_id`, `sayana_sun`, and `equinoctial_shadow_tenths`. The Sayana Sun
uses normalized `{rasi, degrees, minutes, seconds}` with rasi 0–11 and
sexagesimal fields in range. The equinoctial shadow is nonnegative tenths of
an angula.

Fold the Sayana longitude into its nearest 90-degree quadrant to obtain Bhuja
in 0–90 degrees. Traverse its complete 30-degree segments using exact
coefficients `[20/1, 16/1, 20/3]`; multiply a partial segment by its exact
arcsecond fraction of 108,000. Coefficients are vināḍis per angula; the
input's tenths-of-angula scale therefore yields tenths of a vināḍi. Preserve
the full rational sum until truncation toward zero to an integer tenth, then
apply the source half-circle sign. The folded Bhuja and Cara are zero at 0° and
180°, and reach their maxima at 90° and 270°; the sign is negative before
180° and positive from 180° onward.

The operation returns the normalized Sayana longitude, Bhuja, supplied
equinoctial shadow and signed `cara_vinadi_tenths`. Every integer input and
output is bounded to the shared exact JSON range `−9,007,199,254,740,991` to
`+9,007,199,254,740,991`; an unsafe integer returns
`outside supported calendar coverage`. A negative shadow returns
`invalid calendar input`, and malformed sexagesimal fields return
`invalid calendar angle`. The fixture suite is planned and does not change
numeric v0.3 activation.
