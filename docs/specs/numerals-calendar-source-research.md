# Numerals/calendar source research and acquisition ledger

## Tamil calendar display labels (2026-11-02)

The additive display contract is
[`calendar-tamil-display-v1.md`](calendar-tamil-display-v1.md); profile
comparison is specified in
[`calendar-profile-comparison-v1.md`](calendar-profile-comparison-v1.md).
Both suites are planned. Neither changes the existing Romanized response
fields or activates calendar fixtures.

- The root data `lexicon/calendar-tamil-display.toml` stores escaped, indexed
  Tamil month, tithi, nakshatra, yoga, karana and 60-year cycle labels from
  Tamil Virtual Academy, *கல்வெட்டுக்களில் பஞ்சாங்கக் குறிப்புகள்*,
  <https://www.tamilvu.org/tdb/titles_cont/inscription/html/panchangam.htm>.
  The downloaded HTML snapshot SHA-256 is
  `ea510ec5a2ceacf3cc4c75f0dfb1a9f6f866ef398db2f1ab1639109c53a5300e`.
  Locators are lines 9–11, 22–49, 50–64, 64–90, 92–104, and 105–163 in the
  accessible text. These are limited factual names, not copied prose or a page
  image; the page states no reuse license, so none is asserted.
- The Tamil weekday spellings are independently checked against the wide
  Gregorian weekdays in Unicode CLDR 49 `common/main/ta.xml`, pinned at
  <https://github.com/unicode-org/cldr/blob/release-49/common/main/ta.xml>.
  The retained file digest is
  `69ca3f6a2792ed1ce1cc01a708462ae30d5fc25e25e026b73c1fa3b1fb63c626`.
  The Latin transliterations are the seven entries in the “Transliteration”
  column of Vidya Mohan and Rajiv Ranjan, *Basic Tamil* (2024), chapter 6.1,
  <https://openbooks.lib.msu.edu/basictamil/chapter/chapter-6-1/>; the fetched
  HTML digest is
  `d8dfe164fa37b207813346e866f52b2cea467889205cc9cd069aa7135e91bff1`.
  The textbook identifies this material as CC BY-NC 4.0. The noncommercial
  term and attribution are retained in the generated third-party notice; no
  textbook images or surrounding prose are included.
- Tamil Virtual Academy's 60 numbered year names are indexed by position and
  cross-checked against the CICT three-page cycle table and the independently
  source-pinned 1889 romanized sequence. The source's 60th entry is printed
  beside the next “Ruthu” heading; only `அட்சய` is recorded as its numbered
  year name. The TVA karana paragraph says there are eleven types but lists
  both `பத்திரை` and `விஷ்டி` with irregular numbering. Runtime's indexed
  `Vishti` uses the source's `விஷ்டி` spelling and the alternate source form is
  retained as a note. No other source variant is silently regularized.
- `format_tamil_date` uses only the explicit fixed templates in the contract,
  an explicit script and digit style, and the selected Rust profile's
  context-validated Gregorian conversion. `calendar_display_info` returns the
  same labels with the profile/date/context and source bases. Romanized
  month/limb spellings continue to come from existing profile data; Romanized
  year titles remain the 1889 South Indian table's spellings. Tamil-script
  labels are the sourced TVA educational spellings; no Sri Lankan publisher
  spelling or inflection is claimed. The displayed solar-year identifier is
  not a Thiruvalluvar year.

## Thirukanitham implementation evaluation (2026-11-02)

The bounded, unreleased toolkit definition is
`thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2`; its contract is
[`calendar-thirukanitham-v1.md`](calendar-thirukanitham-v1.md). This name
identifies one reproducible profile. It does not claim equality with every
publisher’s settings or every regional Thirukanitham.

- **Runtime and licensing:** Rust `astro = 2.0.0` from
  <https://github.com/saurvs/astro-rust> is the only runtime astronomy engine.
  Its MIT license and exact archive SHA-256
  `199632E1A87451CF771DA7ADEBA192CAB923EDE42657AC3DE0133BA6F4AE14BE` are
  retained with the source package. Python/PyERFA is used only by the
  independent-reference preparation tool; it is not a runtime dependency.
- **Sidereal anchor and frame:** Swiss Ephemeris §2.8.5 documents
  23°15′00.658″ at JD(TT) 2435553.5 as the true Lahiri/Chitrapaksha value,
  including nutation (<https://www.astro.com/swisseph/swisseph.htm>). It must
  not be advanced as a mean anchor. `astro`’s selected 63-term IAU 1980
  longitude nutation is +16.768479927″ at that epoch. The source-correct mean
  anchor is therefore true minus nutation = 23°14′43.889520″, stored as
  `83683889520` microarcseconds in the canonical root lexicon. Independent
  ERFA/SOFA IAU 2000A gives +16.777905560″ and a mean anchor of
  23°14′43.88009444″; its 0.009426″ difference from the profile anchor is the
  declared nutation-series difference, not a fitted constant. ERFA is
  <https://github.com/liberfa/erfa>; the reference tool pins PyERFA 2.0.1.5.
- **Precession and consistent sidereal coordinates:** the mean anchor advances
  with the IAU 2006 P03 general-precession-in-longitude polynomial
  (`5028.796195 T + 1.1054348 T² + 0.00007964 T³ − 0.000023857 T⁴ −
  0.0000000383 T⁵` arcseconds; `T` in Julian centuries from J2000). Production
  limb and ingress coordinates are apparent-of-date and subtract the true
  ayanamsa (P03 mean value plus the same model’s date nutation). Thus the
  date-dependent nutation cancels from sidereal longitude. Independent
  ERFA/P03 checkpoints cover the 1956 anchor, J2000, 2024 January/August,
  2025 April, 2026 November and 2027 December, including negative and positive
  nutation phases. Checkpoint data and the Decimal P03 calculation are in
  `tests/reference/calendar-thirukanitham-v1/independent-transforms.json`
  (SHA-256 `8E211B349D6536001B4FD01C1F1EE2E4D03E3B380ECB86B38039A446618B44C1`).
  Its extraction script and both retained raw-response digests are recorded in
  `horizons-request-manifest.json`.
- **Physical definitions:** Sun longitude is VSOP87-D geocentric mean plus
  FK5, IAU 1980 nutation and solar annual aberration. No separate solar
  light-time or gravitational-deflection correction is added. Moon longitude
  is the partial ELP-2000/82 geocentric mean plus that nutation; no separate
  lunar FK5, aberration, light-time or gravitational-deflection correction is
  added. These declared approximations are compared directly with JPL’s
  apparent-airless geocentric ecliptic-of-date coordinates; no expected
  correction is stripped from JPL values. The time model is TT = UTC + 69.184
  seconds and UT1 = UTC with a stated 0.9-second bound. Primary specification
  sources include the [IAU 2006 Resolution B1](https://iauarchive.eso.org/static/resolutions/IAU2006_Resol1.pdf)
  and [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html).
- **Measured production accuracy:** the 13 retained DE441 sample epochs span
  2024–2027; both full raw responses and their request/response digests are in
  `horizons-request-manifest.json`. The test now measures the coordinates
  actually used by tithi, karana, nakshatra and yoga, plus the derived
  elongation and true-sidereal coordinates. Maximum observed absolute errors
  are Sun 0.106033″ (limit 1.0″), Moon 5.899331″ (limit 10.0″), elongation
  5.798747″, sidereal Sun 0.103310″ and sidereal Moon 5.899345″. The previous
  test compared a separate apparent-position reconstruction while production
  used mean coordinates; its production maxima were 26.378634″ Sun, 14.655556″
  Moon, 24.037562″ elongation, 4.261727″ sidereal Sun and 20.198668″ sidereal
  Moon. The 1″/10″ primitive limits are unchanged. These are physical
  coordinate measurements, distinct from categorical publisher observations
  and from same-engine regression properties.
- **Independent roots and complete-day coverage:** the raw root manifest retains
  118 JPL requests/responses with full query parameters, URLs, byte counts and
  SHA-256 digests. ERFA/SOFA IAU 2000A plus an independent Decimal P03
  transformation finds all 49 public month ingresses and the terminal ingress
  after coverage, with the corrected profile within 3 seconds of every
  one-second JPL bracket. It also classifies 43 limb transitions from 1-second
  windows, with at most 4 seconds between the profile root and JPL bracket.
  Separate 60-second full-day sweeps cover eight civil dates and all 40
  Chennai, Colombo, Jaffna and Jaffna-elevation derived contexts. Their
  independent JPL transition sets exactly match the 43 Rust-report events;
  the full-day sweep detects both missing and extra crossings. The selected
  report dates include new-moon and full-moon wraps, karana 57/58/59 and 59/0,
  a transition seconds from sunrise, and a root near midnight. The report
  windows and profile reports are derived and are not treated as independent
  expectations. First/last month roots span the partial 2023 solar-year 9
  month through the terminal 2028 month-10 ingress; all 49 ingress-derived
  local month starts/lengths across Chennai, Colombo and Jaffna are retained.
  Raw source and output hashes are listed at the end of this section.
- **Solar months and location scope:** the sunrise horizon is a geocentric
  solar-center altitude of −47′ (31′ refraction plus 16′ semidiameter) with
  spherical elevation dip using a 6,371,000 m Earth radius. The profile covers
  the declared TN and SL coordinate boxes and the modern fixed UTC+05:30
  conventions. Chennai, Colombo and Jaffna reference coordinates and sources
  are canonical data; Jaffna is GeoNames 1242833 at 9.668450° N,
  80.007420° E, ca. 7 m. The derived regression inventory records 40 complete
  civil-day reports across these sites and elevation samples, and 49 month
  boundaries/lengths from the partial coverage-start month through the partial
  coverage-end month. It is explicitly tagged as output of this Rust profile,
  not independent astronomical evidence. Independent ingress-root validation
  is recorded separately from those derived month values.
- **2026-11-01 publisher observations:** the saved Chennai page says sunrise
  06:03, sunset 17:42, Sadhya ends 14:39, Saptami and Bava end 14:51, and
  Pushya ends 2026-11-02 04:30. The corrected profile reports sunrise 06:02,
  sunset 17:43, 14:39, 14:52, 14:52 and 04:31. Colombo reports sunrise 05:58
  and sunset 17:50; the profile reports 05:58 and 17:51. The former profile
  produced yoga 14:40 and tithi/karana 14:53. These facts are rounded
  publisher observations; they do not expose exact roots or the publisher’s
  ephemeris, elevation, refraction, frame, ayanamsa or time settings. The
  retained factual receipt includes URLs and page digests, but no page bytes;
  hashes alone cannot reproduce or re-audit those extracted values. No
  publisher cause is assigned to the remaining differences. The source page
  reuse terms are unknown, so no webpage HTML is redistributed.
- **Correction decomposition and sunrise-day reconciliation:** a pinned
  component-variant test retains the old mean-coordinate/true-anchor-as-mean
  model and the corrected P03/apparent model at the actual Nov 1 Chennai
  transition roots. For tithi 22→23 the old mean pipeline crosses at 14:52:49,
  and the corrected pipeline at 14:52:11 (−38 seconds); anchor correction has
  no tithi effect because tithi is not sidereal. At the crossing, the selected
  model's nutation is +8.293120″, solar FK5 is −0.090330″ and solar annual
  aberration is −20.642856″, yielding +20.733186″ change in apparent elongation
  after the common Sun/Moon nutation cancels. For nakshatra 7→8, correcting the
  anchor moves 05:40:20 to 05:39:52 (−28 seconds), and true-coordinate
  nutation cancels in the sidereal frame. For yoga 22→23, anchor correction
  moves 14:39:47 to 14:38:54 (−53 seconds); apparent solar FK5/aberration
  moves it forward 33 seconds to 14:39:27. These are model component
  measurements, not inferred publisher settings. The same test finds that
  changing only elevation from Chennai's 14 m to sea level moves sunrise/sunset
  by −31/+31 seconds, and Colombo's 7 m to sea level by −21/+21 seconds.
  Keeping the profile's −47′ horizon but using sea level yields 06:02:49/17:41:59
  in Chennai and 05:58:05/17:50:14 in Colombo. Those round to the observed
  publisher labels, which is a sensitivity scenario rather than evidence that
  the publisher uses sea level. Changing the profile horizon from −47′ to a
  geometric center crossing shifts each station's sunrise/sunset by about
  196–200 seconds. All exact values are in
  `publisher-correction-components-2026-11-01.json`.
- **Adjacent publisher-day receipts:** retained factual extracts for Chennai
  Oct 31 and Nov 2 show the publisher's sunrise-day grouping. Its Oct 31 page
  lists Vishti ending at 03:51 and Punarpoosam ending at 05:39 on Nov 1, before
  the Nov 1 sunrise; the toolkit's Nov 1 civil report includes the corresponding
  03:52:02 and 05:39:52 roots. The Nov 1 page lists Pushya ending at 04:30 on
  Nov 2, and the Nov 2 page shows Ayilyam at sunrise. This reconciles day
  assignment and after-state only. The adjacent page hashes are retained, but
  their bytes were not because reuse terms are unknown; the hashes therefore
  cannot reproduce or independently audit the extracts. The receipt is
  `drik-panchang-adjacent-observations-2026-10-31_11-02.json`; the pages are
  [Chennai Oct 31](https://www.drikpanchang.com/tamil/tamil-month-panchangam.html?date=31%2F10%2F2026&geoname-id=1264527)
  and [Chennai Nov 2](https://www.drikpanchang.com/tamil/tamil-month-panchangam.html?date=02%2F11%2F2026&geoname-id=1264527).
- **Reproduction and retained digests:** install `pyerfa==2.0.1.5` from
  `tools/requirements-thirukanitham-reference.txt`, run
  `python tools/prepare_thirukanitham_derived_reports.py` to regenerate the
  explicitly profile-derived 40-day/49-month projection, then run
  `python tools/acquire_thirukanitham_jpl_root_samples.py` and
  `python tools/prepare_thirukanitham_jpl_root_observations.py`; then run
  `python tools/acquire_thirukanitham_jpl_full_day_samples.py` and
  `python tools/prepare_thirukanitham_jpl_full_day_observations.py`. The root
  derived projection SHA-256 is
  `19CA5B4D59F2384F71E4A5E0013BAF526ACDB613CCFFAAF4B0A8E374A7469CB1`.
  The root manifest SHA-256 is
  `15FF18596B436A17DEC684DD89DE5528F3AB107B24DB0538124263E9F05125F1`; its
  independent output is
  `926682EC7C726A18BC815841D5815F5894AFC409886D075EFBC278AC23F99858`.
  The full-day request manifest SHA-256 is
  `8F96BF3F9831C0ED6D39B4F5E795D984927105842E6BCB8C057C6950EFDF85D5`; its
  independent output is
  `EA153352F563BDB0D1642E17A0508C58047508906BF258BDC5ABDBEA80F96157`.
  Each manifest hashes its raw responses and request URLs; outputs record
  manifest and transformation-script hashes. The separate extracted JPL
  coordinate observations and independently transformed checkpoint hashes
  remain in `horizons-request-manifest.json` and
  `independent-transforms.json`.
- **Activation boundary:** the 18-row calendar suite remains planned; no owner
  review authorizes activation. Numeric v0.3 approval does not apply to the
  calendar. Six Vakiya suites remain planned (97 rows). The milestone stays
  open for full Vakiya support, era/phases/periods/observances/holidays and
  separate calendar acceptance evidence.

## Historical Vakiya transcription and arithmetic repair (2026-11-02)

The local primary scan at
`C:/Users/abish/AppData/Local/Temp/Vakyakarana-Laghuprakasika-1962.pdf`
was visually rendered and inspected after confirming SHA-256
`27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
Appendix II's complete Moon table was reviewed across all ten printed pages:

| Printed page | Scan PDF page | Table rows |
| --- | ---: | ---: |
| 125 | 162 | 1–23 |
| 126 | 163 | 24–51 |
| 127 | 164 | 52–79 |
| 128 | 165 | 80–107 |
| 129 | 166 | 108–132 |
| 130 | 167 | 133–157 |
| 131 | 168 | 158–182 |
| 132 | 169 | 183–207 |
| 133 | 170 | 208–232 |
| 134 | 171 | 233–248 and the English verification rule |

The printed p. 134 verifier gives row 1 as 0-12-3, row 247 as 0-15-41,
row 248 as 0-27-44, and says to recover a doubtful row `n` by subtracting row
`248 − n` from Bhavet sukham. Therefore each complement pair sums to
12 rāśis + 27°44′ modulo 360°. The build validates every pair for rows 1–247
against this invariant. It preserves and explicitly checks the sole printed
source discrepancy: row 100 on printed p. 128 / PDF p. 165 is 8-1-17 and row
148 on printed p. 130 / PDF p. 167 is 4-26-17, summing to 12 rāśis + 27°34′,
ten arcseconds short of the prose rule. These values remain faithful to the
visible print rather than being silently inferred from the complementary
formula.

Direct high-resolution page review and the complementary invariant identified
four transcription corrections in the canonical table:

| Row | Printed source | Visually printed value | Complement check |
| ---: | --- | --- | --- |
| 155 | p. 130 / PDF p. 167 | 8-5-52 | row 93 (p. 128 / PDF p. 165) is 4-21-52; pair gives 12 rāśis + 27°44′ |
| 165 | p. 131 / PDF p. 168 | 0-14-29 | row 83 (p. 128 / PDF p. 165) is 0-13-15; pair gives 0°27′44″ |
| 207 | p. 132 / PDF p. 169 | 6-27-53 | row 41 (p. 126 / PDF p. 163) is 5-29-51; pair gives 12 rāśis + 27°44′ |
| 217 | p. 133 / PDF p. 170 | 11-12-49 | row 31 (p. 126 / PDF p. 163) is 1-14-55; pair gives 12 rāśis + 27°44′ |

Rows 155 and 207 were additional errors exposed by checking all complement
pairs, then confirmed against their page images. No other canonical row is
changed. The build pins these four direct readings and the p. 134 start/end
anchors in addition to checking the complementary rule, so the concordance
gate is not a digest comparison of a generated copy with itself.

Cara rule 7 was rechecked visually at printed p. 269 / PDF p. 306. It reads
20, 16, and 6⅔ for the three successive Bhuja rāśis. The canonical coefficients
are exact fractions `20/1`, `16/1`, `20/3`. At 75° with 30 shadow tenths,
`(20 + 16 + 10/3) × 30 = 1180` tenths, signed negative in the first half;
at 90° the exact result is `(20 + 16 + 20/3) × 30 = 1280` tenths. Partial
segments remain rational until the final documented truncation toward zero.
For a 30-tenth shadow, 70° gives exact magnitude 3440/3 and −1146 after
truncation; 80° gives 3640/3 and −1213. At 75° one second below/above the
partial-segment edge, final truncation yields −1179/−1180; at 90° minus one
second it yields −1279. Endpoint vectors cover 60°, 90°, 180° and 270°; paired 180°−1″ and
180°+1″ cases verify the sign boundary. Near-zero sign vectors are also
recorded. Example 20 exercises only the first two coefficients and
does not validate the third.

Source-derived Cara and Moon vectors were written before changing algorithms or
canonical table entries. At Kali day 1,601,149, corrected row 165 yields
uncorrected 7-16-29-7 with 12-04 daily motion; its successor day
1,601,150 has 12-02 motion. At Kali day 1,601,201, corrected row 217 yields
6-14-49-7 with 12-28 daily motion; its successor day 1,601,202 has 12-17
motion. Rows 155 and 207 have separate derived vectors. Moon table lookups and
248/3,031/12,372-day boundary expectations are independently calculated from
the printed table and equations, not copied from runtime output. The printed Kali-day 18,44,004
example remains the only independently observed Moon output in this fixture
set; derived vectors are labeled as such. No numerical fixtures activate the
six planned calendar suites.

The seven calendar operations now share the exact JSON integer interval
`−9,007,199,254,740,991..=+9,007,199,254,740,991`. This is an adapter/runtime
transport bound, not an added historical astronomical convention. Rust keeps
i128 intermediates and rejects unsafe numeric inputs and outputs with
`outside supported calendar coverage`.

The Bhujaantara endpoint table remains source-transcribed, but longitude-linear
interpolation is explicitly experimental. Rule 16a provides no interpolation
parameter or equation, and Example 4(b)'s equal −21 endpoints cannot
distinguish time from longitude interpolation. No independent nonflat
historical witness has been found or inferred.

## Calculation-source follow-up (2026-11-01)

- Venketeswara Pai R., “The rationale for Srirgunamitradivakyas as described
  in the Laghuprakashika,” *Journal of Astronomical History and Heritage*
  22(3), 545–552 (2019), DOI 10.3724/SP.J.1440-2807.2019.03.13,
  <https://cdn.sciengine.com/doi/pdfView/243DF073EF884DF7AA2A82C5143ED578>.
  The publisher endpoint yielded text for the complete eight-page article.
  Local `curl` attempts to the Science Press CDN and the NARIT archive failed
  DNS resolution; PDF screenshot requests returned HTTP 502, and the browser
  surface was unavailable. No article bytes, digest, rendered pages, or visual
  equation/table check were obtained. The extracted text is retained as a
  cross-check only, not as runtime data or a golden source.
- The extracted text on printed p. 546 gives the Kali ahargana equation
  `A = 365*y + y/4 + (5*y - 1237)/576`; for elapsed Saka 1890 (`y=5069`) it
  reports `A=1,851,494.10417` days, rounded to 1,851,494 days, 6 nadi,
  15 vinadi, Saturday. The OCR at the example line has apparent equation-token
  errors; the equation/result pair agrees with the visually inspected 1962
  worked example's arithmetic method, so the OCR line itself is not treated as
  authority. Printed p. 547 describes the twelve solar-vakya offsets added to
  the annual Mesa dhruva. Its extracted Table 1 for Saka 1890 reads, in source
  order: 4-01-47, 7-25-59, 4-02-37, 7-30-49, 3-32-59, 6-00-21, 7-54-28,
  2-24-52, 3-45-45, 5-13-01, 7-01-25, 2-21-46. These are textual
  cross-checks only because that page image was not available for inspection.
- The same extracted article discusses the true-sun correction ratio and
  iteration on printed pp. 548–550, including a Gemini worked example. It may
  guide later image-verified transcription, but no coefficients or true-sun
  equations from those OCR passages have been implemented.

### Acquisition reattempt and exact calculation locators (2026-11-02)

- Reattempted the publisher PDF locally at the URL above. PowerShell reported
  `No such host is known (cdn.sciengine.com)`; the web PDF screenshot service
  again returned HTTP 502 on p. 547. Searches for the article title, DOI and
  file identifier found no alternate full-text PDF. The publisher's web text
  extractor does expose all eight pages, so equation/table locators can now be
  recorded, but no image or binary is available for visual verification.
- Printed p. 546, equations (1)–(6), gives the mean/true ahargana correction
  and Kali-day formula. Printed pp. 547–548, equations (7)–(10), give the
  civil-day-per-mean-longitude ratio and solar correction. Its Saka
  1890 worked example has obvious OCR substitutions in the displayed
  arithmetic (`5069/5`, `12375`), so the page's numerals cannot be trusted
  without the image. Printed p. 547, Table 1, is the twelve Saka-1890
  transit values and can be compared with the 1962 list plus annual dhruva;
  some extracted cells also contain OCR signs/digit errors.
- Printed p. 548, equation (10), and p. 549, equations (11)–(13), describe
  deriving mean solar
  longitude at a sign boundary by iterating the Bhāskara correction
  `asin((3/80) sin(θ₀ − θA))`, converting the mean-longitude interval to
  civil days, then taking the remainder modulo seven as the transit vākya.
  The example on p. 549 reports the Mithuna iteration reaching 59.31153° after
  ten iterations. Table 2 (p. 549) lists computed mean longitudes; Table 3
  (p. 550) compares the twelve text vākyas with computed values. The prose
  says the computation uses modern sine values and acknowledges differences
  from the text (e.g. 6|19|44 versus 6|19|34 for Mithuna). These are useful
  independent-method and discrepancy locators, not implementation inputs or
  accepted golden values until the equations and tables are visually checked.
- No new engine was added from OCR. The existing bounded profile remains
  pinned to the visually checked 1962 text, not to a reconstructed 2019
  algorithm. The exact remaining acquisition item is an inspectable copy of
  printed pp. 546–550 (or an independently obtained scan) to verify the
  equation symbols, constants, iteration, and all twelve rows of Tables 1–3.
  The article's data/reuse terms also remain unestablished.

### Latest publisher text extraction and diagnostic comparison (2026-11-02)

- The Science Press PDF text extractor returned 1,027 lines for the complete
  article. A second local PowerShell download attempt failed with
  `No such host is known (cdn.sciengine.com)`; web PDF screenshots of pp. 546
  and 547 returned HTTP 502; the computer-use browser host reported that its
  browser access host was unavailable. No binary, digest, rendered page image,
  or visual verification resulted. These are acquisition failures, not a
  reason to hold source-backed work using the separately inspected 1962 scan.
- Text at printed p. 546, equation (5) and the Saka-1890 worked example,
  independently cross-checks the implemented ahargana result
  `1,851,494 days, 6 nāḍi, 15 vināḍi`. The displayed OCR arithmetic contains
  apparent digit/operator substitutions, so this is agreement of the stated
  equation/result with the 1962 calculation, not a transcription authority.
- The OCR extraction of printed p. 547 Table 1 agrees with the twelve 1890
  transit values already computed from the 1962 table. The `7-25-59` cell has
  a stray OCR sign and other cells may contain digit/sign errors; it is only a
  diagnostic check, not fixture or runtime evidence.
- Printed p. 549's extracted Gemini example reports convergence to
  `59.31153°` after ten iterations. Printed p. 550 Table 3 discussion reports
  the historical Mithuna text value `6|19|44` versus its modern-sine iterative
  value `6|19|34` (10 vināḍis), and Vṛṣabha `2|55|32` versus `2|55|30`
  (2 vināḍis). This is a documented method/discrepancy lead. Because the
  equation symbols and table cells remain unverified visually, none of these
  values has been added to the runtime profile or golden suite.
- A direct open of the publisher-indexed PDF exposed all eight pages as a
  1,027-line text extraction. It identifies the article's finite solar method:
  the Kali ahargaṇa relation on p. 546; the Bhāskara correction
  `asin((3/80) sin(θ₀ − θA))` with solar apogee 78° on pp. 546 and 548; and
  reverse iteration from each true sign boundary to its mean longitude on
  pp. 548–550. The extracted Mithuna worked case starts at 60°, reaches mean
  longitude 59.31153° after ten iterations, then compares the derived
  `6|19|34` with the text vākya `6|19|44`. Table 1 OCR also contains a visibly
  suspect `7-25--59` cell. These details make the paper a useful independent
  algorithm lead, but the extraction is not a visual transcription.
- Acquisition was retried on 2026-11-02 using the exact publisher PDF URL.
  `Resolve-DnsName` returned no DNS record for `cdn.sciengine.com`; Google DNS
  over HTTPS returned NXDOMAIN (status 3). PDF page screenshots for the
  equations/tables returned HTTP 502. The official NARIT archive filename
  resolves to a 77,517-byte HTML page shell rather than a PDF, and the current
  `www.sciengine.com/sci-open/doi/pdfView/<id>` endpoint responds `No Fund
  Article`. No PDF bytes or digest, and no rendered article page, were
  obtained. The 2019 text has not been used as runtime data, goldens, or a
  visually validated definition. Its article and data reuse terms were not
  established.

- K. Mahesh, "Sankramavakyas of the Vakyakarana" (2014), Indian National
  Science Academy repository metadata inspected at
  <https://insa.ndl.gov.in/items/212f26a3-cc31-4111-b476-80345eb50370/full>.
  The publisher PDF link returned HTTP 403. Article calculations were not read.
- The primary 2023 JAHH planetary-table article PDF at
  <https://dds.sciengine.com/cfs/files/pdfs/1440-2807/23F9CD88F1C2437D80C0B0178CCD328A.pdf>
  timed out; the alternate publisher PDF endpoint returned HTTP 418. Search
  extracts are navigation leads, not verified numerical evidence.
- The coderganesh/tamil-astrology-rasi-chart repository README was inspected.
  It declares AGPL-3.0 and describes its own accuracy limitations. No code or
  tables were imported; its existence does not supply a reviewed engine.

The owner answered "No" to having preferred publisher editions and explicitly
approved numeric v0.3 activation on 2026-11-01. Source acquisition and
source-pinned mathematical work can proceed without treating a contemporary
publisher's undisclosed corrections as a prerequisite. Do not claim modern
commercial-publisher equivalence for a classical profile.

Research log updated: 2026-11-02 (initial acquisition notes dated 2026-11-01).
Companion to the
[completion plan](numerals-completion-plan.md). This is an evidence ledger,
not a declaration of final calendar completion. The new historical solar-
transit definition is documented separately; its fixtures remain planned. No
downloaded third-party scan was checked in.

## Inspected primary text

1. IMD Positional Astronomy Centre, Rashtriya Panchang web edition labelled
   Saka 1948 / 2026-2027,
   [Explanation](https://packolkata.imd.gov.in/panchang/en/explanation),
   sections Explanation and Details of the Panchang. HTML inspected, no print
   pagination. Explanation paragraphs 1-7 distinguish National and All-India
   Nirayana calendars, their fixed months and leap rules. Details paragraphs
   defining tithi/nakshatra/yoga/karana give their angular divisions and cyclic
   versus fixed karanas. Station/time paragraph specifies central station
   82 degrees 30 minutes E, 23 degrees 11 minutes N and IST. Rise/set paragraph
   describes upper limbs. This is sufficient evidence for shared limb concepts,
   not a pinned Tamil Drik ephemeris or a Vakya parameter sheet. Footer reserves
   Government of India rights; no general redistribution license established.
   Extract facts with attribution; do not copy site tables wholesale under MIT.

2. Same edition, [Regional calendars](https://packolkata.imd.gov.in/panchang/en/regional-calendars),
   Tamil Nadu Calendar table, twelve rows Chittirai through Panguni, inspected.
   As a limited independent boundary witness, it gives Aadi beginning July 17,
   2026 and Arppisi beginning October 18, 2026. The fixed All-India calendar in
   Explanation instead places corresponding starts on July 16 and October 16.
   These differences demonstrate why replacing Tamil conversion with the
   uniform calendar is wrong. They do not establish which contemporary Tamil
   publisher's Drik or Vakya algorithm the regional table reproduces.
   Next: obtain the edition's methodological notes explaining regional cutoff
   rules and Tamil printed daily tables; confirm publisher correspondence.

3. Government of Tamil Nadu, Gazette No. 5, Part VI section 1, February 5,
   2025, [PDF](https://www.stationeryprinting.tn.gov.in/gazette/2025/5_VI_1_2025.pdf),
   PDF page 1 / printed page 55, masthead inspected via extracted PDF text:
   Thai 23, Kurothi, Thiruvalluvar Aandu 2056. This independently pairs Gregorian,
   Tamil solar date, named cycle year and numbered era. It does not prove the
   boundary date. Government copyright notice present; no MIT redistribution
   permission inferred. Record factual pairs with source locators.

4. Kanchi Kamakoti Peetham, Balabodha Sangraham Part 2, translated by
   P. R. Kannan, [publisher PDF](https://www.kamakoti.org/kamakoti/books/Balabodha%20Sangraham%20-%202.pdf),
   title page and Summary of Panchanga Contents inspected as extracted text;
   PDF/printed page 18 explicitly distinguishes Vakya and Triganita and says
   Srimatham follows Triganita. Page 17 describes daylight subdivisions and
   conditional sunrise-based clock examples. This is primary institutional
   testimony, not numerical precision evidence or a complete period table.
   Date/edition number and redistribution terms not established. Obtain a
   dated edition and source works for individual observance rules before reuse.

5. Sri Sringeri Sharada Peetham,
   [publisher's Panchangam index](https://www.srisharadapeetham.com/gallery/downloadables/panchangam),
   inspected HTML table: 2023 Shobhakrit, 2024 Krodhi, 2025 Visvavasu.
   Tamil 2025 is marked Coming Soon. This supports acquisition routing and
   limited named-year witnesses, not a computational definition. Published
   Kannada PDF must not be assumed to be the Tamil Vakya edition.
   Next: obtain the actual Tamil almanac, inspect title, colophon, station,
   introduction, daily tables and terms; record page-specific observations.

## Inspected classical Vakya source; contemporary lineage remains open

Vakyakarana with Sundararaja's Laghuprakasika, editors T. S. Kuppanna Sastri
and K. V. Sarma, Kuppuswami Sastri Research Institute, Madras, 1962.
[Hosted scan](https://www.ebharatisampat.in/pdfs/ebharati-pdf-1644580379VakyaKarana-LaghuParkasikaVyakhya-Ed-KuppannaSastri-SarmaKV-1962.pdf).
Downloaded outside the repository and rendered for visual inspection with
PyMuPDF 1.26.7; 339 image-only pages; SHA-256
`27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
Text extraction returned no text for the sampled pages, so the following claims
come from page images, not OCR or empty extracted text:

- PDF page 1 is the cover; page 5 is the contents. Contents list the
  introduction, Vakyakarana text, and appendices containing Candra-Vakyani and
  Kujādi-Pañcagraha-Mārga-vākyani. The title/editor/publisher details were
  checked against the cover image; title-verso copyright/rights were not
  established.
- PDF page 8 (Introduction) describes the text/commentary tradition and its
  relation to almanac calculation.
- PDF pages 18–20 (printed Introduction xi–xiii) were visually inspected for
  sidereal-period and Mahayuga/epicycle tables, named comparison traditions,
  and epoch/mean-year discussion. The visible text gives a mean-sunrise epoch
  at Ujjain and the traditional mean-year expression `365-15-31-15`; this is
  recorded as a lead for scholarly transcription, not as an adopted constant.
- PDF page 24 (printed Introduction xvii) explains mean/true corrections and
  the use of fixed apses; PDF page 26 (printed Introduction xix) shows cycle,
  reference-longitude and period tables.
- PDF page 49 (printed Vakyakarana p. 10) was visually checked as the start of
  the calculation text. Appendix II's 248 Candra-vakya values, printed pp.
  125–134 (scan PDF pp. 162–171), have now been visually transcribed into
  `lexicon/calendar-vakya-moon.toml` as day-ordered `[rasi, degrees, minutes]`
  rows. The build checks row count, scalar fields, and independently checked
  anchor rows 1, 153, 154, 247 and 248. The source's p. 134 verification note
  says vakya 1 plus penultimate vakya 247 equals vakya 248 (0-12-3 + 0-15-41
  = 0-27-44).
- PDF page 288 (printed English translation p. 251) was visually checked for
  the Saka 1869 ahargana worked example, the Ujjain mean-sunrise epoch/weekday,
  its units, and the twelve solar-vakya offsets. These finite facts are
  transcribed in `lexicon/calendar-vakya-solar.toml`; their arithmetic contract
  and escaped expectations are in `docs/specs/calendar-vakya-solar-v1.md` and
  the planned `calendar_vakya_solar.jsonl` suite. PDF page 289 (printed p. 252)
  was visually inspected and its 37 Bhupadi correction values at 10-day
  increments (14, 32, 54, 78, 105, 133, 163, 194, 224, 254, 284, 311, 335,
  358, 376, 391, 403, 411, 415, 416, 412, 406, 398, 386, 374, 361, 347, 334,
  322, 311, 303, 297, 295, 296, 301, 309, 322 arcminutes) were transcribed into
  `lexicon/calendar-vakya-solar.toml`. The same page explains interpolation;
  PDF page 290 (printed p. 253) gives an elapsed value of 180 days, 19 nāḍi,
  41 vināḍi, approximate Sun 180°19′41″, correction 6°51′8″ and true Sun
  173°28′33″. `vakya_true_sun_from_mesha_elapsed` reproduces this example with
  integer interpolation and nearest-arcsecond rounding.
- PDF page 290 (printed p. 253) gives the true-Moon algorithm: subtract Kali
  day 16,00,984; successively divide by 12,372, 3,031 and 248; apply angular
  factors 9-27-48-10, 11-7-31-1 and 0-27-44-6 plus dhruva 7-2-0-7; then add
  the residual Candra-vakya. PDF page 291 (printed p. 254) defines signed
  vinadis as `32*q248 - 8*q3031`, compares daily motion with 13°11′, and gives
  the complete Kali day 18,44,004 worked example. It reports quotient tuple
  `(19,2,7)`, vakya 154 (7-21-48), uncorrected Moon 4-11-14-1, daily motion
  14°12′, adjustment +208 vinadis, +211 correction seconds, and true Moon
  4-11-17-32. `vakya_true_moon_from_kali_day` reproduces this example using
  integer arcseconds and truncation toward zero. At an exact 248-day remainder
  of zero, the implementation maps to printed row 248 and borrows one cycle
  from its angle sum; this source-derived one-based convention has no separate
  worked example in the edition and is identified in the contract.
- PDF page 292 (printed p. 255), lines 14b–16a, specifies the local true-
  sunrise correction as the algebraic sum of half-Cara, Deśāntara and
  Bhujaantara vināḍis multiplied by true daily motion to obtain arcseconds.
  PDF page 293 (printed p. 256), Example 4(b), supplies `+13.0`, `−26.6`,
  `−21.0` vināḍis for a Pudukkottai Moon example; `−34.6` vināḍis gives
  `−491″` and local true Moon `4 rasi 11°09′21″`. The bounded
  `vakya_reduce_to_local_true_sunrise` operation reproduces that example from
  the already computed terms. Calculating those terms from daylight, longitude,
  equation of time and station, then assigning a civil date, remain open.

- PDF page 292 (printed p. 255), rule 16b–17a and Example 4(b), was also
  visually checked for the Deśāntara conversion: use the signed east/west
  distance from Ujjain in yojanas, divide by 55 for nāḍis, and apply positive
  west / negative east. The Pudukkottai distance 24.4 yojanas east yields
  `24.4 / 55 = 0.443 nāḍi = −26.6 vināḍi`. The bounded
  `vakya_desantara_from_yojana_distance` operation reproduces −26.6 vināḍis
  when given 24.4 yojanas east. It does not convert a geographic coordinate
  into yojanas or infer a station's distance.

- PDF page 292 (printed p. 255), rule 16a, visually lists the Bhujaantara
  values at the ends of Meṣa through Mīna as `+16, +7, −5, −15, −21, −21,
  −14, −6, +4, +14, +20, +21` vināḍis. On the same page Example 4 states that
  the date ends on 24 Kanyā and that the interpolation is −21 because both
  the end of Siṃha and the end of Kanyā have −21. PDF page 293 (printed p. 256),
  Example 4(a), identifies the supplied True Sun as `5 rāśis 23°28′33″`.
  The equal-endpoint example cannot distinguish time interpolation from
  longitude interpolation. Rule 16a supplies no interpolation parameter or
  equation. The `vakya_bhujaantara_from_true_sun` operation therefore retains
  longitude-linear interpolation only as an explicitly experimental
  convention. Its nonflat interpolation fixtures are derived from that
  convention, not independent historical outputs or an accepted general
  historical law.
  The canonical runtime table is a short numerical transcription; the scan
  and surrounding prose are not distributed. No blanket license conclusion
  is inferred from the scan's copyright status; any additional reproduced
  material or claimed edition rights still require their own terms review.

- PDF pages 304–306 (printed English translation pp. 267–269), Chapter III,
  rules 1–8 and Example 20, were additionally rendered and visually inspected.
  Printed p. 269 states that the Cara coefficients for successive 30-degree
  Bhuja segments are 20, 16 and 6⅔ (exactly 20/3), multiplied by the station's
  equinoctial shadow, and gives the sign by the Sayana half-circle. Example 20 uses
  Sayana Sun 4 rasi 22°30′, shadow 3 angulas and Bhuja 1 rasi 7°30′ to obtain
  −72 vināḍis. The bounded `vakya_cara_from_sayana_sun` kernel reproduces
  this example from the exact rational canonical coefficients in
  `calendar-vakya-solar.toml`; that example does not exercise the third
  coefficient.
  Its input still requires the caller to supply Sayana Sun and equinoctial
  shadow; it does not derive precession or observer geometry.

This scan supports the explicitly named historical solar-transit, true-Sun,
true-Moon, Cara, and Deśāntara kernels, plus a Bhujaantara endpoint table with
an experimental interpolation convention; it
does not establish which contemporary publisher's Vakiya profile is required,
its later correction/bīja lineage, local-term derivation, station/time/day
assignment, all published rounding, errata, or redistribution rights. It does
not justify claiming a modern edition or complete Vakiya calendar. Do not
substitute modern Drik longitudes under a Vakiya name.

## Contemporary publisher and edition acquisition

Current named leads include Manonmani Vilas Press's *Asal 28-No. Visuvavasu
Varusha Suttha Vakkiya Panchangam 2025–26* and its listed *Parabhava* 2026–27
edition; Arcot Seetharama Iyer's Arcot Vakya edition; and Srirangam Temple's
Vakiya almanac. A [secondary publisher directory](https://nityapanchangam.com/panchangams/pambu-panchangam/)
identifies Pambu as Manonmani Vilasam Press, Chennai, and a [current book
catalog](https://www.exoticindiaart.com/book-publisher/manonmani%2Bvilasam%2Bpress%2Bchennai/)
identifies the 2026–27 title and publisher.
These are acquisition leads only: no physical or digital contemporary edition
was obtained, and seller copy does not disclose the equations, corrections,
rights, or exact reference meridian. A contemporary methodology page says it
compares a publisher's Chennai entries and describes ghati reckoning, but does
not name that publisher; it is not a primary authority
([methodology page](https://navapanchangam.com/methodology.html)).

Concrete acquisition steps: obtain the 2025–26 and 2026–27 Pambu/Manonmani
books directly from the publisher; request the computation-method and errata
pages, table provenance, rights for redistribution of a finite machine-readable
projection, and permission to publish page-located fixtures. Obtain the
current Arcot and Srirangam editions as independent named lineages. Compare
their title verso, preface, reference station, epoch, tables, worked examples,
corrections, and daily outputs with the 1962 critical edition. Transcribe any
candidate table twice independently and maintain arithmetic checks. Do not
promote retailer metadata or a modern website into a profile definition.

## Official annual holiday records inspected (2026 discovery year only)

These legal schedules are separate from astronomical or observance
calculations. Copies below are research artifacts in ignored `target/`; neither
is shipped in the repository or a package because no reuse permission or
applicable open-data license was established.

1. Sri Lanka, Gazette Extraordinary No. 2438/22, 27 May 2025, Order under
   section 04 of the Holidays Act No. 29 of 1971, declaring 2026 Public and
   Bank Holidays. Official record:
   [gazette PDF](https://www.documents.gov.lk/view/extra-gazettes/2025/5/2438-22_E.pdf)
   and [official 2025 extraordinary-gazette index](https://www.documents.gov.lk/view/egz/egz_2025.html).
   The two page images were rendered and visually checked: page 1 is the
   signed/order text and page 2 the 26-entry schedule. PDF text extraction
   confirms the order title, authority, and year; the schedule was visually
   checked, including Thai Pongal on 15 January. Official-host direct download
   failed from this environment, so a mirror copy from Sri Lanka Mirror was
   used for inspection; its SHA-256 is
   `a0af7154a3bd3dc22472f11568f0a5f75ac8024e19dc1d79853639417ceec08d`.
   The digest is for the mirror copy, not independently authenticated against
   bytes served by the official host. The official index/search extraction
   independently identifies No. 2438/22, the date, Ministry, Act, and 2026
   schedule. Confirmed that its legend distinguishes Public and Bank
   Holidays. No Tamil/Sinhala schedule amendments or multi-year revision
   series were incorporated.
2. Tamil Nadu, G.O. Ms. No. 708, Public (Miscellaneous), 11 November 2025;
   [official 2025 extraordinary index](https://www.stationeryprinting.tn.gov.in/extra_ordinary_lists.php?id=MjAyNQ%3D%3D), row 721, identifies public holidays for
   government offices and commercial/co-operative banks for 2026. A
   government-hosted 2025 Gazette copy was not obtained from the site's slow
   file host. A 5-page image-only mirror scan was rendered and pages 4–5
   visually checked; SHA-256
   `23d870590763124b66812daac2be1034286ca5df11cbde17816bcae477589088`.
   It contains 24 listed items, including an April 1 annual bank-account
   closing that is not a general government-office holiday. The Government's
   order and the gazetted appended notification distinguish the classes.
   The TN Stationery and Printing service page says gazette copies may be
   obtained from the Government Publication Depot, Assistant Director
   (Publications), 110 Anna Salai, Chennai, phone 044-2852-0038/4412/4413.
   Obtain and hash the official bytes and ask the department for written data
   reuse terms before considering a checked-in projection.

The TN publisher portal policy found in this pass says reproduction of
state-owned website content is subject to proper permission from the
respective department. The Sri Lanka open-data reuse page applies to material
published through that portal and does not establish a license for gazettes.
Therefore neither research copy is treated as redistributable. Coverage is
only one year per jurisdiction, below the plan's requested multiyear range.

## Additional contemporary source search and technical leads

The observations in this section record the initial 2026-11-01 search. The
provider evaluation and implementation status at the top of this ledger
supersede the earlier open Thirukanitham-provider question.

- Sri Lanka Department of Government Printing's official
  [Tamil-language 2026 calendar PDF](https://documents.gov.lk/view/calander/2026/2026_T.pdf)
  is now located. Search-indexed extraction labels government, bank, commercial
  and Poya-day holidays and says changes may apply; the final lines identify
  the Department of Government Printing. `curl` and the PDF screenshot endpoint
  returned 404 from this environment even though web-indexed PDF text is
  available. No page image was rendered, file digest or revision status is
  confirmed, so this is not a visually inspected fixture source. Continue by
  obtaining the Tamil/English original through the Department and compare it
  with Gazette No. 2438/22.
- Namma Calendar's [2026 dual-calendar PDF page](https://nammacalendar.com/en/tamil-calendar/2026/pdf/)
  says its Vakya pages use dates from a Chennai printed almanac, with thithi and
  star at sunrise; its paired Thirukanitha edition uses Chennai sunrise. It
  lists twelve month starts and festival outputs, but names no almanac
  publisher or computation sheets. This is a secondary output witness and
  discovery route, not a primary definition, independent implementation, or
  permission to redistribute. Compare selected pages with an acquired named
  publisher original only after that identity is established.
- Nava Panchangam's [methodology page](https://navapanchangam.com/methodology.html)
  gives one explicit contemporary Drik candidate: Swiss Ephemeris, Lahiri
  (Chitrapaksha), apparent/refraction-corrected local sunrise, and a
  before-sunset sankranti day rule. It also describes Vakya ghati timing from
  the Sun's geometric centre on the true horizon and a single transition
  instant converted to each local clock. The page claims checks against printed
  data but does not name either publisher or give the corrections/parameters
  and rounding needed to reproduce them. It is a technical lead, not a source
  authority for this package.
- Astrodienst's primary [Swiss Ephemeris documentation](https://www.astro.com/swisseph/swisseph.htm)
  describes version 2.10/current ephemerides and dual licensing: AGPL or a
  paid professional license. The AGPL option conflicts with this toolkit's MIT
  distribution policy unless the project changes license; the professional
  option requires a signed paid contract. Its programmer's manual says generic
  Hindu sunrise uses geocentric solar centre, ignores refraction and solar
  latitude, while Nava's Drik candidate describes apparent, refracted local
  sunrise. The difference confirms that merely choosing the library does not
  resolve a particular Tamil publisher's convention. Swiss Ephemeris was not
  selected; the bounded toolkit definition was subsequently implemented with
  the MIT Rust `astro` provider and explicit Lahiri/P03 rules described above.
  Publisher-specific differences remain an acceptance-review item, not a
  blocker to the selected toolkit profile.
- The TN direct-file acquisition attempt for G.O. Ms. No. 708 used the official
  index entry and the corresponding `721_Ex_II_1_2025.pdf` path. The official
  host timed out on both attempts. The visually inspected mirror remains
  discovery evidence only; obtain the Government Publication Depot copy and
  written reuse terms.

## Leads and partial boundary evidence, not activated fixtures

- TN 2025 official masthead evidence now brackets the Thiruvalluvar year:
  [Gazette No. 2, 8 January](https://www.stationeryprinting.tn.gov.in/gazette/2025/2_VI_1_2025.pdf)
  says Margazhi 24, Kurothi, year 2055, and
  [Gazette No. 3, 22 January](https://www.stationeryprinting.tn.gov.in/gazette/2025/3_VI_1_2025.pdf)
  says Thai 9, year 2056. The latter gives one independently observed
  Gregorian/Tamil/era pair. A 2008 official Governor's address hosted by the
  Rural Development Department states that the Government declared Thai 1 the
  Tamil New Year, and says the Gazette had used the Valluvar year since 1972.
  This is useful normative testimony but not the underlying order text or a
  directly inspected Thai 1 masthead. Obtain the original order/Gazette and
  adjacent official mastheads for 2025 and another leap-year boundary before
  activating a Thiruvalluvar fixture. Do not confuse the Thai 2 Thiruvalluvar
  Day holiday with the era rollover.
- Sri Lanka Department of Government Printing,
  [2026 desk calendar](https://www.documents.gov.lk/view/calander/2026/2026_E.pdf):
  search-indexed full document includes public/bank/mercantile holidays and
  phase times in Sri Lanka Standard Time. Direct opens timed out or returned
  404 (host variants differed). The separately located official Tamil-language
  2026 calendar is described above, but its binary and rendered pages remain
  inaccessible. Neither calendar is a verified fixture source in this review.
  Acquire working official Tamil/English PDFs, inspect legends and amendment
  notices, pin bytes and page numbers. The official holiday Gazette for 2026
  is a separate acquisition target; legal observance is distinct from a
  computed religious date.
- Central Bank of Sri Lanka [2026 holidays](https://www.cbsl.gov.lk/en/node/19362):
  direct fetch returned 403. Search results are leads only. Neither this nor
  embassy holiday pages establishes regional panchangam calculations.
- TN and SL contemporary almanacs: obtain dated publisher originals rather
  than retailer summaries. Specifically seek a TN Drik almanac, TN Vakya
  almanac, and SL Vakya/Thirukanitha editions with reference stations and
  stated adjustments. Jaffna publisher testimony must not be generalized to
  Batticaloa, Vanni or Up-Country without local comparison. No independent
  SL computational source has been established by this pass.
- Contemporary websites advertising both engines and profile disagreements
  appeared in search. They are discovery leads, not primary calculation
  authorities or independent oracles. No code, constants or claimed comparison
  counts were imported. Trace claims back to printed publisher sources.

## Numeric evidence pinned and inspected locally

Read Rust lib.rs/formats.rs and canonical numerals TOML headers, both v0.1/v0.2
contracts and reference source manifests. Existing formal TN/SL scope,
MAX_INTEGER=999999999 and MAX_MINOR=99999999999 are compatible with the major
unit cap. CLDR 49 Tamil ordinal, decimal-point, and spellout rules and root
traditional rules are pinned in `tests/reference/numerals-v0.3/sources.json`;
Unicode 17 source and Tamil/Tamil-Supplement projections have source and
projection digests. `tools/prepare_numerals_v03_reference.py` records URLs,
licenses, derivation methods, and inspection notes. ICU4J 79.1 generates only
the bounded ordinal and traditional spelling references; exact decimal,
syntax/error and Gregorian expected values use separate Python string,
`fractions.Fraction`, and `datetime` logic plus explicit boundary/error cases.
ICU4J is not an astronomical oracle and is not a runtime dependency. Unicode
data retain the pinned Unicode License v3 notice.

## Additional astronomical implementation and profile candidates

This section records alternatives and earlier output leads. The selected
toolkit implementation is documented above; none of these alternatives is a
runtime dependency or an assertion of universal publisher equivalence.

- **Named Thirukanitha candidate:** `Nava-Thirukanitha-Lahiri-Apparent-Sunrise-TN-v1`.
  Nava's methodology identifies true positions from Swiss Ephemeris with the
  Lahiri/Chitrapaksha ayanamsa, apparent refraction-corrected sunrise at the
  selected coordinates, and a Tamil Nadu month-start rule that assigns
  sankranti to the same day when it occurs before local sunset and otherwise
  to the next day. The page claims a 725-day Chennai-2026/Lucknow-2025 check
  where tithi, nakshatra, Moon rasi and paksha matched published Drik data and
  sunrise was within seconds. The Swiss Ephemeris version, exact observer
  inputs, time-scale/conversion settings, rounding, named comparison publishers
  and raw paired outputs are not supplied there, so this is a profile lead, not
  an accepted definition or an independently reproduced comparison.
- **One-day output acquisition:** On 2026-11-01 for Chennai, Nava's public
  default page labels its displayed engine Vākya and reports Saptami until
  19:22, Punarvasu until 10:37, and sunrise 06:06 IST. Drik Panchang reports
  Saptami until 14:51, Pushya until 04:30 on 2026-11-02, sunrise 06:03, and
  Lahiri ayanamsa 24.238661°. A separate `panchangam.org` daily page reports
  the same tithi and nakshatra cutoffs as Drik Panchang, while sunrise is
  06:06. This is evidence of a Vakya/Drik disagreement and a minute-rounded
  sunrise discrepancy. It is not counted as two independent calculation
  lineages: the Drik-matching site does not document its engine lineage, and
  the Nava `SWISS_LAHIRI` date-specific page fetch was blocked by its site.
  No fixture is activated from this single date.
- **Permissive Rust planetary candidate:** the `vsop87` Rust crate 3.0.0
  implements VSOP87 A/B/C/D/E and declares MIT OR Apache-2.0. Its docs state
  sub-arcsecond planetary accuracy over stated year spans and show a test value
  matched to NASA reference data. It is pure Rust and merits a controlled
  technical assessment, but it does not provide the Moon or a complete apparent
  topocentric pipeline; the repository was archived in February 2026. It is
  not sufficient by itself for tithi/nakshatra transitions, and the origin and
  redistribution terms for its bundled coefficient data still need an
  explicit source audit before vendoring or release use.
- **Permissive C candidate:** Astronomy Engine's upstream repository carries
  an MIT license and implements Sun/Moon/planet positions, phases and rise/set,
  with observer coordinates and optional refraction. Its own README describes
  accuracy within about one arcminute and bases the model on VSOP87/NOVAS C
  3.1. It is not Rust-native; a Rust FFI or port would be an engineering
  option, but the stated angular bound and cross-language/data provenance need
  transition-specific comparisons before selection.
- **Reusable transformations:** ERFA is a BSD-3-Clause C implementation of
  SOFA-derived fundamental-astronomy routines, but it is not a planetary or
  lunar ephemeris. It could supply transformations in a larger design, not
  close the ephemeris requirement on its own.
- **Rust-native but incompatible as-is:** Siderust supplies VSOP87 and
  ELP2000-82B in Rust, but the project declares AGPL-3.0 and states dual
  licensing would be needed for a differently licensed project. Its separate
  `siderust-archive` is BSD-3-Clause, but the top-level manifest marks VSOP87
  and ELP2000 family migrations pending and says upstream dataset terms must be
  checked in each family manifest. This is a research source for models, not
  an MIT-compatible dependency decision.
- **Primary theory/data leads:** IMCCE documents VSOP2013 and publishes
  technical descriptions; its files are fitted to INPOP10a. The retrieved
  README/paper did not establish redistribution terms for coefficient files.
  IMCCE's VSOP87 and ELP82B archives are primary formulation/data leads, but
  their raw-file licenses remain unverified. No coefficient set is copied.

### Exact output and astronomy-source URLs inspected

- Nava methodology: <https://navapanchangam.com/methodology.html>
- Nava Chennai page, default Vākya display on 2026-11-01:
  <https://navapanchangam.com/panchangam/chennai>
- Drik Panchang Chennai 2026-11-01:
  <https://www.drikpanchang.com/panchang/day-panchang.html?geoname-id=1264527>
- `panchangam.org` Chennai daily output, 2026-11-01:
  <https://tamil.panchangam.org/dailypanchangam.php?date=2026-11-01>
- Rust `vsop87` 3.0.0: <https://docs.rs/vsop87/3.0.0/vsop87/>
  and <https://github.com/Razican/vsop87-rs> (repository now archived).
- Astronomy Engine upstream README and MIT license:
  <https://github.com/cosinekitty/astronomy> and
  <https://github.com/cosinekitty/astronomy/blob/master/LICENSE>
- ERFA upstream source and BSD-3-Clause terms:
  <https://github.com/liberfa/erfa> and
  <https://github.com/liberfa/erfa/blob/master/LICENSE>
- Siderust license/model status and archive dataset manifests:
  <https://github.com/Siderust/siderust>;
  <https://github.com/Siderust/archive/blob/main/README.md>;
  <https://github.com/Siderust/archive/blob/main/src/vsop/manifest.toml>;
  <https://github.com/Siderust/archive/blob/main/src/elp/manifest.toml>.
- IMCCE planetary theory overview and VSOP2013 source README:
  <https://www.imcce.fr/recherche/equipes/pegase/theories> and
  <https://ftp.imcce.fr/pub/ephem/planets/vsop2013/solution/README.pdf>.

## Source blocker closure checklist

| Blocker | Concrete acquisition/deliverable | Prevents |
| --- | --- | --- |
| Exact publisher compatibility | A publisher methodological sheet naming its ephemeris, ayanamsa, time/horizon/cutoff and event rounding, plus terms for reusing more than short facts | Claiming that the toolkit definition reproduces a named publisher or activating a publisher-equivalence suite |
| Classical Vakiya local correction parameters | The bounded 1962 edition profile supplies source-backed civil dates and five limbs at Ujjain mean sunrise. A 2026-11-02 publisher-hosted PDF retrieval byte-matched the retained scan. Printed pp. xv–xvi and 267–269 provide Cara half-daylight, longitude/yojana, precession, shadow/latitude, and day/night equations. Printed p. 255 still gives only a date-interpolation instruction with equal −21 endpoints; it does not identify the interpolation parameter or connect the p. 252 Bhūpādi series to its Bhujaantara table. Udayāntara is explicitly neglected. | Arbitrary-location Vakiya corrections and true horizon sunrise/sunset; not the bounded Ujjain profile |
| Era boundary | Original Thai-1 government order and adjacent, visually inspected TN mastheads including a leap-year case; current evidence brackets 2025 and gives official Thai-1 testimony | Thiruvalluvar date output |
| Regional comparison coverage | Additional independently documented TN and SL stations, especially Jaffna/Batticaloa/Vanni/Up-Country, within the selected model's finite coordinate/timezone profile | Broad regional publisher-equivalence claims |
| Everyday/observance rules | Publisher/source section per period and observance, precedence and tie cases | Period/festival activation |
| Calendar comparison breadth | Additional independently documented calculation/publication lineages and transition samples with matching profile/location definitions; preserve exact disagreements | Activating the source comparison suite or claiming publisher alignment |
| Runtime/data licensing | Written reuse terms for any expanded Drik pages, official TN/SL Gazette bytes, and multiyear holiday sources. The `astro` 2.0.0 MIT license and archive digest are already pinned. | Distribution of adopted publisher/holiday data |

## Tamil solar-month assignment and observance source acquisition (2026-11-02)

This section supersedes the earlier “not established” status for the Tamil
solar month-assignment rule and for the small observance subset below. It does
not establish the official Thiruvalluvar-year boundary, authorize calendar
fixture activation, or claim publisher equivalence.

### Month assignment authority and multi-month comparison

- The visually inspected facsimile of Robert Sewell and Sankara Balkrishna
  Dikshit, *The Indian Calendar* (1896), printed p. 12, §28 (PDF p. 28), says
  solar months are treated civilly as beginning at sunrise, distinguishes
  southern rules, and names the rule “Tamil Rule” for Tamil and Tinnevelly:
  ingress after sunrise and before sunset opens the month on the same day;
  ingress after sunset opens it on the following day. The scanned source bytes
  are retained at
  `tmp/research/sewell-dikshit-indian-calendar-1896.pdf`, SHA-256
  `0d441771519c93ed9066c2da57bba8f9f908750e1a15a20b1e8d6916682dc7bc`.
  The historical passage does not explicitly resolve an ingress before
  sunrise.
- The Positional Astronomy Centre’s *Indian Calendar* source, “The Tamil rule”
  section, states the same civil date is used when samkranti is before local
  sunset, otherwise the following date. This current government summary does
  cover the pre-sunrise part of the civil date. The stable source URL is
  <https://packolkata.gov.in/INDIAN_CALADAR_PAC.pdf>. Its boundary wording
  supports the existing reproducible
  `ingress_at_or_before_local_sunset_opens_same_date` profile convention.
- The official IMD English *Rashtriya Panchang* 1947 SE (2025–26) was retained
  as `tmp/research/english-rashtriya-panchang-2025-26/RP 1947 SE English
  Final.pdf`; its ZIP SHA-256 is
  `B67440C7C59A68AED6B20E5CADC171DA83579FA7A568E0E3DC9D2B8F3E842C02`.
  The PDF was visually checked at PDF p. 11 (day starts at sunrise and regional
  month table), p. 12 (calculation explanation), and p. 16 (full Tamil Nadu
  solar-month table). A fresh visual review of p. 16 confirms the Tamil Nadu
  column lists: Chithirai 14 Apr 2025; Vaikasi 15 May; Aani 15 Jun; Aadi
  16 Jul; Avani 17 Aug; Purattasi 17 Sep; Arppisi (Aippasi) 17 Oct;
  Karthigai 16 Nov; Margali 16 Dec; Thai 14 Jan 2026; Maasi 13 Feb; Panguni
  15 Mar. These twelve starts match `tamil_year_info` for the 2025
  Thirukanitham Chennai solar year. The prior transcription had inadvertently
  mixed the adjacent Kerala column into three Tamil Nadu rows (Aadi, Aippasi,
  Karthigai); the rendered page is retained at
  `tmp/research/english-rashtriya-panchang-2025-26/page-16.png` for audit.
- The official web edition's 2026–27 Tamil Nadu table,
  <https://packolkata.imd.gov.in/panchang/en/regional-calendars>, lines 86–119,
  publishes all twelve month starts and all twelve match the named
  Thirukanitham profile for 2026–27. IMD's explanation says its calculation
  for the beginning of saura months uses a fixed ayanamsa of 23°15′ and
  separately discusses nirayana samkrantis. The source does not establish that
  this paragraph maps one-to-one to every row in its regional Tamil table. The
  published civil-date matches do not prove that the underlying settings or
  source calculations are identical to the toolkit's variable-Lahiri model.
- Drik Panchang's first-party Tamil Nadu Puthandu and Pongal descriptions and
  Chennai 2025–2027 annual pages agree with the toolkit for the sampled
  Chithirai 1 and Thai 1 dates: Puthandu is 14 April in all three years;
  Pongal is 14 January in 2025 and 2026, and 15 January in 2027. Its 2026
  Chennai calendar also lists Bhogi 13 January and Mattu Pongal 15 January.
  These event witnesses are not proof of complete publisher-model equality.
- Therefore the existing Thirukanitham definition is retained and justified
  by a named Tamil-rule source plus its independently measured apparent
  Lahiri ingress model. Its API continues to state the exact toolkit profile;
  it is not relabelled as the IMD, Drik, or every printed Tamil calendar. The
  conflict between the 2026 Government Gazette mastheads remains a separate
  official-era issue: IMD and Drik's Jan 14 Thai output does not reconcile the
  Gazette's Jan 14 Margazhi 30 / year 2056 and Jan 23 Thai 9 / year 2057.

The English IMD ZIP, extracted PDF, rendered page images, and Sewell–Dikshit
scan are local research materials only. Facts and short locators are recorded
here; no scanned page or long publisher prose has been added to distributable
data.

### Bounded Nava / Tamil-rule observance subset

The named rule subset is `nava-panchangam-tamil-observances-v1`, specified in
[`calendar-observances-v1.md`](calendar-observances-v1.md). It combines the
primary Tamil solar-month assignment rules already recorded above with Drik
Panchang's Chennai 2025–2027 named solar-festival schedules, and Nava
Panchangam's published Amavasya/Pournami day-selection rule. The rule engine is
Thirukanitham only; Nava's annual tithi answer pages explicitly use its
Vakyakarana engine, so those dates are independent witnesses of rule
application and not Thirukanitham expected values or publisher-equivalence
claims. No positions from the source's Vakyakarana output enter the toolkit
calculation.

Nava methodology page section “How a festival gets its date” says tithi-based
observances are judged in Aparahna and the later date wins when the tithi
covers two consecutive Aparahna windows; when none is covered, it falls back
to the date on which the tithi prevails at sunrise. Nava's Amavasya and
Pournami annual pages repeat this precise local rule and provide start/end
interval examples for Chennai from November 2026 through October 2027. An
Aparahna window is the fourth of five equal daylight intervals; the
implementation uses its half-open interval from 3/5 to 4/5 of local
sunrise-to-sunset daylight. If an interval has neither Aparahna nor sunrise
presence, no day is invented. A tithi repeated across two Aparahnas selects
the later date; a skipped Aparahna uses the sunrise fallback when available.
The Pournami page says the dates are intended for observance but advises that
temples/families may keep separate evening practices. This pack does not claim
to schedule every ritual.

Nava source snapshots retained under `tmp/research/`:
- `nava-methodology.html`, SHA-256
  `0a9b815e3e33e3f4911742433ee5fe5d802f27d1fa3c87bb9300811410006195`.
- `nava-amavasya-chennai.html`, SHA-256
  `7965cc8113410e1ed35ed408442e62e1b7f8178c5f2c0b152758ebc02193c9eb`.
- `nava-pournami-chennai.html`, SHA-256
  `c92f7e132e818f997a42a82a32c9372b3ce6fa33c59211655d3236e8a90b3dbc`.

These are retained fetched HTML bytes and extracted text, not visually inspected
page images. The web-readable methodology states the tithi day precedence at
[lines 30–33](https://navapanchangam.com/methodology.html); its Amavasya page
states the Aparahna and sunrise fallback and Vakyakarana engine at
[lines 20–37](https://navapanchangam.com/answers/amavasya-dates), and its
Pournami page gives the same precedence and engine at
[lines 20–36](https://navapanchangam.com/answers/pournami-dates). The selected
Thirukanitham Chennai implementation output matches the 13 listed Amavasya
and 12 listed Pournami dates (25/25) from November 2026 through October 2027.
The March 2027 Amavasya interval is published as 7 March 14:37 to 8 March
15:37, with 8 March selected; that is a concrete later-day witness for an
interval spanning consecutive afternoons. The source pages use Vakyakarana,
so matching dates do not prove engine or publisher equivalence. The toolkit's
monthly event source IDs are now attached only when the event date lies inside
the page's retained date range. Other staged monthly outputs have no annual
date witness yet and remain unverified.

The Drik Bhogi sequence description and annual solar schedules are retained as
factual witnesses; no page markup, images, or annual event tables are copied.
Nava reuse terms have not been established, and Drik says its data are
copyrighted. No redistribution permission is asserted.

This was the 2026-11-01 checkpoint: all observance goldens remained planned;
calendar-owner review and further source-backed family work were outstanding.
The named-family work below supersedes the then-current list of unimplemented
families. The entire suite still remains planned pending independent expected
output review and activation approval. The Vakyakarana/Thirukanitham astronomy
distinction remains explicit, and no single community rule is inferred across
the separately named selectors.

### Named Sri Vaishnava Ekadashi and Vakiya daylight source review (2026-11-02)

The observance pack now has one separately named Ekadashi rule:
`nava_sri_vaishnava_arunodaya_defer`. This is the finite Chennai/Tamil Nadu
Nava Sri Vaishnava rule described in
[`calendar-observances-v1.md`](calendar-observances-v1.md), not a Smartha,
ISKCON, or universal Vaishnava selector. The Hari-bhakti-vilāsa verses
12.318–320 reject Dashami at Arunodaya and move the fast to Dvadashi; 12.328
defines Arunodaya as four ghatis before sunrise. Rao, *Basics of Panchangam*
(2005), printed pp. 14–16, specifies 4 ghatis = 96 minutes and describes the
Dashami-veddha deferral. Nava's Chennai answer page states its Sri Vaishnava
operational treatment of Dashami at Arunodaya and of Ekadashi that continues
past the next morning's Arunodaya. The engine computes these cutoffs using
each local Thirukanitham sunrise; it does not use Nava's Vakyakarana positions.

Two independent monthly query cases were added for Chennai 2026-10 and
2026-11. Their Thirukanitham results contain Oct 6 and 22, and Nov 5 and 21.
The exact-source lists preserve the evidence boundary: Nava's Chennai annual
page includes Oct 22 and Nov 5 but says Nov 20 for its later November date;
Drik's separate ISKCON list includes Oct 6, Oct 22, Nov 5 and Nov 21. The
Nov 20/21 difference remains visible. Drik's dates are only an independent
Vaishnava-calendar witness, not an assertion of ISKCON equivalence with the
Nava Sri Vaishnava rule. Both monthly vectors and the entire observance suite
remain planned.

Snapshots and references for this addition:
- `tmp/research/hari-bhakti-vilasa-vilasa-12.html`, SHA-256
  `40bdcf628b26ccd39cdc6193783c7477ff46c3734817c709f1cb79c4a7d764ef`;
  Hari-bhakti-vilāsa 12.318–320 and 12.328 are at
  <https://www.anantasatsang.org/scripture/radha-bhakti/hari-bhakti-vilasa/vilasa-12>.
- `tmp/research/basics-of-panchangam-2005.pdf`, SHA-256
  `4716fae5ca5634f9a88be5482e7335e3cbe5bc4df27a31923f2e8946d3e9e750`,
  printed pp. 14–16.
- `tmp/research/nava-next-ekadashi-2026-11-02.html`, SHA-256
  `d930613acfbe8592a80b383317a579d06d308ef02bdcf2d8b9f8147d4c717566`;
  <https://navapanchangam.com/answers/next-ekadashi>.
- `tmp/research/drik-iskcon-ekadashi-chennai-2026.html`, SHA-256
  `1afc94f5b4c0ce0942273be2f5c0794ca268c9d1bb65f2cb7b2cb99719a27905`;
  <https://www.drikpanchang.com/iskcon/iskcon-ekadashi-list.html?geoname-id=1264527>.

The annual dates are retained as factual locators, not redistributed. The
fixture source lists attach the Nava and Drik annual records only to dates each
page actually lists, and only for the exact Chennai reference coordinates.
Nava reuse terms are not established; Drik states its data are copyrighted.

#### 1962 Vakyakarana local-sunrise equations: new evidence, unresolved join

On 2026-11-02 the publisher-hosted 1962 edition was fetched from
<https://www.ebharatisampat.in/pdfs/ebharati-pdf-1644580379VakyaKarana-LaghuParkasikaVyakhya-Ed-KuppannaSastri-SarmaKV-1962.pdf>.
The web reader rejected the 11,159,128-byte PDF at its content-size limit;
`Invoke-WebRequest` retrieved the full file as
`tmp/research/ebharati-vakyakarana-1962-retrieval.pdf` (11,159,128 bytes,
SHA-256 `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`).
That digest matches the already retained `target/numerals-reference-vakyakarana-1962.pdf`;
this verifies the same scan from the publisher host, not an independent edition.
The relevant page images were checked again at printed pp. 255, 267, 268 and
269 (scan PDF pp. 292, 304, 305 and 306).

- The edition's Introduction, printed p. xv, describes Cara as the difference
  of daylight from 30 nāḍīs, with its half (`carārdha`) shifting sunrise later
  when daylight is shorter and earlier when it is longer. It gives
  `sin h = tan φ tan δ` for the half-daylight angle and converts one degree to
  ten vināḍis. It says the first three corrections are used here and the
  fourth, Udayāntara, is neglected. This is a source equation and an explicit
  limitation, not a modern ephemeris substitution.
- Printed p. xvi states one nāḍi per 55 yojanas for Deśāntara, equivalent in
  the text to 6° longitude per 55 yojanas. Thus the source supplies a
  longitude-offset conversion; it does not provide a geodesic distance
  function. The same page defines Bhujaantara as the equation-of-time portion
  due to the Sun's unequal motion and describes it as the time corresponding
  to the difference between mean and true Sun; sunrise is later when true Sun
  is greater.
- Printed p. 267, rules 1–2a, gives the edition's precession calculation and
  says to add precession before using declination and shadow in Cara. Its
  examples yield 23°56′ for Kali year 5048 and 23°52′ for Kali year 5060.
- Printed p. 268, rule 6, obtains latitude from equinoctial shadow by
  multiplying shadow by 43, dividing by the equinoctial hypotenuse, then
  finding the arc. Printed p. 269, Example 19, uses a 12-angula gnomon and a
  2.2-angula shadow (2 angulas 12 yavāngulas), computes hypotenuse 12.2, and
  reports 10°34′ latitude (noting the actual latitude as 10°24′). Rule 7 gives
  Cara coefficients 20, 16 and 6⅔ by successive 30° Bhuja segments; rule 8
  reverses Cara's sign against 30 nāḍīs for daylight and subtracts daylight
  from 60 nāḍīs for night.
- Printed p. 255, rules 14b–17a, combines half-Cara, Deśāntara and
  Bhujaantara vināḍis and applies the sum to true daily motion. Rule 16a lists
  the twelve Bhujaantara values at rāśi ends. Example 4 interpolates for a date
  ending 24 Kanyā but its two endpoints are both −21, so it cannot distinguish
  elapsed-date interpolation from longitude interpolation. It supplies no
  interpolation ratio or numerical non-flat example.

The direct definition on p. xvi does not itself specify which Vakyakarana
position values or approximation produce the tabulated p. 255 endpoints. The
p. 252 Bhūpādi table is a separate correction series, in arcminutes, and the
edition does not give a conversion tying that series to the p. 255
Bhujaantara-in-vināḍi table. Do not substitute `true_sun - approximate_sun`
from the transit kernel, reinterpret the endpoints as elapsed-date values, or
promote longitude-linear interpolation. The existing interpolation API stays
explicitly experimental; no local sunrise/sunset implementation has been
added. A future implementation still needs the source's exact Bhujaantara
date parameter and its connection to the selected Vakyakarana Sun calculation,
plus defined precision and civil-day assignment. The shadow inversion is
bounded by the printed 12-angula example; using `12 × tan(latitude)` for an
arbitrary station would be a derived geometric inference and has not been
adopted as a new API.

#### Pradosham sources: distinct current selector and primary digest rule

On 2026-11-02, the Nava Chennai Pradosham page was fetched as
`tmp/research/nava-pradosham.html` (62,904 bytes, SHA-256
`feaf7ad87e62841933ddabee280c00469d672237c908e5ef95978d76d94fe840`). The
page identifies its own method: a 90-minute window beginning at local sunset;
Trayodashi must be present in the window; if one tithi touches two evening
windows, select the later evening. It also states the displayed tithi dates
come from Nava's Vaakya engine. This page is a primary statement of Nava's
current product rule, not a temple-wide Tamil rule or a religiously universal
selector.

Two independent published Chennai/Tamil Nadu lists were retrieved from
TamilCalendar.app. The 2026 page is retained as
`tmp/research/tamilcalendar-pradosham-2026.html` (66,734 bytes, SHA-256
`df2011c53c7b0167232ea0fba417cc36f48291ea76368962551e9258de095737`); it lists
25 monthly dates and says it publishes dates without giving its selector.
The 2027 page is
`tmp/research/tamilcalendar-pradosham-2027.html` (66,717 bytes, SHA-256
`e240ae8b915d9d351923de47897c9b2042031138dbc76d5464b94c2b4766fb39`), also
with 25 dates and no method statement. The pages state Chennai & Tamil Nadu
coverage and do not establish reuse terms. The toolkit's independently
selected Thirukanitham dates match all 25 listed dates in each page. Four
separately identifiable monthly vectors record November/December 2026 and
February/October 2027. Nava's own schedule differs in February 2027 (Nava
Feb 4/18; toolkit and TamilCalendar.app Feb 3/18) and October 2027 (Nava
Oct 13/27; toolkit and TamilCalendar.app Oct 12/27). Those differences are
retained rather than normalized to Nava.

To check the historical rule, the 1888 Nirṇaya-Sāgara Press Dharmasindhu scan
was retrieved from Internet Archive item
<https://archive.org/details/dharmasindhubykashinathupadhyaya1888nirnaysagarpress_498_a>.
The 47,171,224-byte PDF is `tmp/research/dharmasindhu-1888.pdf`, SHA-256
`c2ff32ff9e03fc143c5690444697878812306e8a6d8fd2259bbb709e5009875`; its
2,447,754-byte OCR text is retained as `tmp/research/dharmasindhu-1888-djvu.txt`,
SHA-256 `0c18f97d630355f8899c590ffe6208ccdce50f04db6a2f8fbfd0009c837603a5`.
The scan was visually checked at printed p. 20 (PDF p. 43, leaf 56),
`tmp/research/dharmasindhu-page-43.png`. Its Trayodaśī-nirṇaya defines the
Pradoṣa window as three muhūrtas after sunset. When both evenings qualify,
equal coverage or equal touching selects the later day. With unequal
coverage, the earlier day is eligible only if its excess is sufficient for
both divine worship and the night meal; otherwise the later day is selected.
If neither evening has coverage, the text selects the later day. The
sufficiency condition is qualitative and supplies no duration threshold. No
inference such as a half-window or one-muhūrta minimum is supported by this
passage. This Dharmasindhu rule is not folded into the separate Nava
90-minute selector; a temple/community source and a resolvable
ritual-sufficiency criterion remain needed before advertising that broader
rule.

Independent Ekadashi provenance repair (2026-11-02): the retained Nava
next-ekadashi page is updated November 2 and begins November 5, 2026. The
October 22 attribution was unsupported and removed; the independent Drik
witness remains. Canonical coverage, observed dates and fixture metadata are
corrected without changing calculated dates. Rebuilt native October output
was checked directly. The full pre-stop gate passed (85 Rust tests plus one
intentional exporter skip, 121 harness tests, 26 Python tests, 35,880 WASM
checks). Dart analysis and 35,876 tests passed. Post-edit and 50 release-copy
checks passed. Isolated archives executed all 35,857 selected rows (35,646
active plus 211 planned), recorded 36 local digests and made no upload. The
initial concurrent Dart/doctest DLL lock was resolved by rerunning the gate
after Dart completed; the final full gate exited successfully.

### Remaining named Thirukanitham festival families (2026-11-02)

The source-first implementation batch now includes separately identified
selectors for Sankatahara Chaturthi, Sivarathri, Thai Poosam, Panguni Uthiram,
Chitra Pournami, Vaikasi Visakam, Aadi Perukku, Smarta Krishna Jayanthi,
Vinayaka Chaturthi, Navaratri Ghatasthapana, Ayudha Puja, Vijayadasami,
Deepavali, Karthigai Deepam, and Arudra Darshan. Earlier solar-month, lunar
phase, Nava Sri Vaishnava Ekadashi, and Nava Pradosham rules remain distinct.
The canonical rule IDs, source URLs, locators, exact observed-date coverage,
and retained page digests are in [`calendar-observances.toml`](../../lexicon/calendar-observances.toml);
the operation and half-open interval selectors are specified in
[`calendar-observances-v1.md`](calendar-observances-v1.md). These are named
Thirukanitham Tamil Nadu profiles. They do not establish a universal Hindu
festival calendar or Vakiya dates for Sri Lanka.

Rule evidence is intentionally plural. The pack combines its named Drik
Chennai annual/festival pages with individual method descriptions from Udaya,
PujaDeep, Anudina, Udyog, the Dharmasindhu scan, and the US Naval Observatory
moonrise definition where cited by each rule. For example, the Thai Poosam
rule follows the bounded PujaDeep daytime Pournami-plus-Pushya, then sunrise
Pushya selector; it does not silently substitute Udaya's different priority.
The Vijayadasami, Sivarathri, Deepavali, and Ghatasthapana selectors likewise
implement only the finite conditions stated in their named sources. Any source
exception not implemented in the contract remains outside this pack.

Smarta Krishna Jayanthi uses the detailed Udyog puja-vidhi selector: Krishna
Ashtami at the eighth of fifteen equal night muhurtas; one qualifying night
selects that night; if both qualify, Rohini at the window selects, otherwise
the second; if neither qualifies, the second. Udyog's general Smarta/Vaishnava
overview instead chooses the greater Ashtami overlap when both nights qualify.
That internal publisher conflict is preserved in the lexicon and the overview
is not the selected rule. The scanned Dharmasindhu Janmashtami passage contains
additional cases; this implementation does not claim to cover them all.

Three August/September month fixtures carry manually source-checked Krishna
dates: Drik Chennai lists 2025-08-15 and 2026-09-04, while its 2027 Chennai
page lists 2027-08-25. The selected bounded Thirukanitham Smarta rule computes
2027-08-24; the separate Udyog Kanchipuram page also lists August 24, but is
kept at its own location and is not attached to Chennai. The 2027 month case
is marked as a source-date disagreement. These monthly slices are tagged as
independent publisher witnesses and remain distinct from the 2025–2027 annual
derived regression rows. Source records carry only exact listed dates and
locations. The Krishna dates are short factual observations, not a claim of
publisher-engine equivalence or permission to redistribute source tables.

The expanded `calendar_observances.jsonl` has 28 planned rows, including the
three Krishna month slices; the planned status is unchanged. It does not
activate any of those rows or alter the 35,646 active approved numeric cases.
Any future activation still needs calendar-owner approval and independent
review of expected dates. Broader Smarta/Vaishnava/temple acceptance, the
Dharmasindhu Pradosham sufficiency threshold, source-backed Sri Lankan and
Vakiya observance profiles, local true sunrise/sunset and Bhujaantara
interpolation, the official Thiruvalluvar-year boundary conflict, and the
remaining source-provenance requirements are open milestone items.
