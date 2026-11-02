# Vakyakarana Deśāntara v1

This operation converts a signed east/west distance from Ujjain into the
Deśāntara time term. It does not convert geographic longitude or coordinates
into yojanas, assign a location, or derive a civil date.

## Definition and source

- Definition ID: `vakyakarana-1962-laghuprakashika-desantara-v1`.
- Edition: *Vakyakarana with Sundararaja's Laghuprakashika*, edited by
  T. S. Kuppanna Sastri and K. V. Sarma, Kuppuswami Sastri Research Institute,
  Madras, 1962. The inspected scan has SHA-256
  `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
- Printed p. 255 (scan PDF p. 292), rule 16b–17a, says to take the east/west
  distance from Ujjain in yojanas and divide by 55 to obtain Deśāntara in
  nāḍis. The result is positive west of Ujjain and negative east.
- Printed p. 255 (scan PDF p. 292), Example 4(b), gives 24.4 yojanas east of
  Ujjain and computes `24.4 / 55 = 0.443 nāḍi = 26.6 vināḍi`, hence a local
  correction term of −26.6 vināḍis.
- The input and output use tenths. The operation converts the exact rational
  `distance_tenths × 60 / 55` to tenths of a vināḍi and rounds to the nearest
  tenth, with ties away from zero. The edition demonstrates rounding to one
  decimal in Example 4(b); its general tie rule is not stated. The factor 55
  is preserved in canonical `lexicon/calendar-vakya-solar.toml` and compiled
  by `build.rs`.
- The scan image and source prose are not included. Attribution does not assert
  an open license for the book.

## Input and arithmetic

The operation is `vakya_desantara_from_yojana_distance` and accepts exactly
`definition_id` and `east_west_distance_tenths_yojana`. Positive distance means
east of Ujjain; negative means west. Divide its magnitude by the source's 55
yojanas per nāḍi, multiply by 60 vināḍis per nāḍi, round to tenths of a
vināḍi, then apply the sign opposite the distance sign. The returned
`desantara_vinadi_tenths` can be supplied directly to
`vakya_reduce_to_local_true_sunrise`.

Every integer input and output uses the shared exact JSON range
`−9,007,199,254,740,991..=+9,007,199,254,740,991` so JSON integers remain
exact in every supported runtime. An unsafe input or rounded result returns
`outside supported calendar coverage`; an unknown definition returns
`unsupported calendar definition`. The planned vectors remain separate from
numeric v0.3 activation.
