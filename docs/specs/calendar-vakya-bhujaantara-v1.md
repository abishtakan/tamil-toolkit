# Vakyakarana Bhujaantara interpolation v1 (experimental convention)

This operation applies an experimental longitude-linear interpolation
convention to the 1962 edition's Bhujaantara endpoint values. It does not
implement a source-verified general historical interpolation rule, or
calculate a date, solar longitude, equation of time, or observer position.

## Definition and source

- Definition ID: `vakyakarana-1962-laghuprakashika-bhujaantara-linear-experimental-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962. The inspected scan has SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
- Printed p. 255 (scan PDF p. 292), rule 16a, lists Bhujaantara in vināḍis at
  the ends of Meṣa through Mīna, in order:
  `+16, +7, −5, −15, −21, −21, −14, −6, +4, +14, +20, +21`.
- The edition's Introduction, printed p. xvi, describes Bhujaantara as the
  equation-of-time part due to the Sun's unequal motion, or the time
  corresponding to the longitude difference between mean and true Sun; it says
  sunrise is later when the true Sun is greater. The same page relates 55
  yojanas to 6° of longitude. This conceptual definition does not identify
  which position series or numerical approximation yields the rule 16a table.
- Printed p. 256 (scan PDF p. 293), Example 4(b), says to interpolate for the
  date ending 24 Kanyā. It uses `−21` at both the end of Siṃha and end of
  Kanyā, yielding `−21` vināḍis. Because those endpoints are equal, the example
  does not distinguish time interpolation from longitude interpolation.
- Rule 16a lists twelve rāśi-end values and requests interpolation for a date,
  but supplies no interpolation parameter or equation. The equal-endpoint
  worked case does not establish interpolation by date, longitude, or another
  variable. The p. 252 Bhūpādi correction series is separate angular data; the
  edition does not state how it maps to the p. 255 Bhujaantara-in-vināḍi
  values. Definition v1 therefore retains supplied longitude progress only as
  an explicit experimental engineering convention. Its nonflat midpoint and
  rounding vectors are derived from that convention and are not independent
  historical evidence. The endpoint data are retained in canonical
  `lexicon/calendar-vakya-solar.toml` and compiled by `build.rs`.
- The source scan and prose are not included. No license for the book is
  asserted; the canonical data is a short transcription of numerical values.

## Input and arithmetic

The experimental operation is `vakya_bhujaantara_from_true_sun` and accepts exactly
`definition_id`, `sun_rasi`, and `sun_rasi_progress_arcseconds`. `sun_rasi` is
the zero-based rāśi count used by the existing Vakiya longitude types: 0 is
Meṣa, 1 is Vṛṣabha, and 5 is Kanyā. Progress is an integer from 0 through
108,000 arcseconds (30°), inclusive. At progress 0, interpolate from the
previous rāśi's endpoint; at 108,000, the current rāśi endpoint is returned.
Adjacent representations of a shared endpoint therefore agree.

For rāśi index `i`, let `left` be the endpoint value for `(i − 1) mod 12` and
`right` the endpoint value for `i`. Compute

`left × 10 + (right − left) × 10 × progress / 108000`

in integer arithmetic, rounding to the nearest tenth of a vināḍi with exact
ties away from zero. The output `bhujaantara_vinadi_tenths` is signed and can
be passed to `vakya_reduce_to_local_true_sunrise`. For the printed example,
both bracketing endpoint values are `−21`, so its interpolation is exactly
`−210` tenths regardless of progress within Kanyā.

The result also returns the input and its two bracketing endpoint values so
the convention remains auditable. Every integer input and output uses the
shared exact JSON range `−9,007,199,254,740,991..=+9,007,199,254,740,991`;
an unsafe integer returns `outside supported calendar coverage`. `sun_rasi`
outside 0–11 or progress outside 0–108,000 returns `invalid calendar angle`; a
malformed object returns `invalid calendar input`, and an unknown definition
returns `unsupported calendar definition`. Golden vectors remain in a planned
calendar suite and do not change numeric v0.3 activation or establish the
historical interpolation law.
