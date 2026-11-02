# Changelog

## Unreleased

- Prepare alpha.5 with approved numeric APIs and explicitly experimental,
  bounded calendar APIs. Defer Krishna Jayanthi until annual month selection
  is sourced; earlier festival-batch notes do not imply candidate support.
  Repair source digest, adapter/dispatcher IDs, schemas and monthly regressions.
  See docs/releases/numerals-calendar-candidate.md for the release boundary.


## 0.1.0-alpha.5 / Python 0.1.0a5 - 2026-11-02

- Extend the still-planned TN Thirukanitham observance pack with the
  source-backed named festival families: Sankatahara Chaturthi, Sivarathri, Thai
  Poosam, Panguni Uthiram, Chitra Pournami, Vaikasi Visakam, Aadi Perukku,
  Krishna Jayanthi, Vinayaka Chaturthi, Navaratri/Ayudha Puja/Vijayadasami,
  Tamil Deepavali, Karthigai Deepam, and Arudra Darshan. Krishna Jayanthi is
  explicitly the Udyog Smarta Nishita/Rohini rule; separate 2025–2027 month
  vectors retain the Chennai publisher dates, including the 2027 profile/Drik
  disagreement. The same publisher's general explainer gives a different tie
  rule, and its Kanchipuram date is retained as a different-location source.
  The primary Dharmasindhu text contains additional cases beyond the selected
  finite summary. Every listed TN family now has a bounded named selector.
  All observance fixtures remain planned; no universal festival schedule or
  Vakiya date equivalence is claimed, and broader community variants remain
  pending.

- Remove an unsupported October Nava Ekadashi witness; align its coverage and
  metadata with the retained November 2 page, preserving the Drik witness.

- Extend the planned Nava Thirukanitham observance pack with a narrowly named
  Sri Vaishnava Ekadashi rule. Its local Arunodaya cutoff is sunrise minus 96
  minutes; Dashami vedha defers the fast, and a tithi that continues through
  the next morning's Arunodaya defers again. Add optional month filtering to
  the Rust dispatcher, Python/Node/browser WASM/Dart wrappers, and workbench.
  Separate October and November 2026 Chennai vectors list toolkit dates Oct
  6/22 and Nov 5/21. Nava and Drik annual dates are attributed only where each
  source actually lists them; Nava's Nov 20 and Drik's Nov 21 remain a visible
  disagreement, with no ISKCON or publisher-equivalence claim. The fixtures
  and all calendar suites remain planned. Add a separate Nava Pradosham rule:
  Trayodashi must overlap its 90-minute local-sunset window, and the later
  evening wins when the same tithi touches two windows. Four distinct monthly
  cases and 2026/2027 TamilCalendar.app date witnesses retain publisher
  differences. Dharmasindhu's three-muhurta selector remains unimplemented
  because its worship/meal threshold is not quantified; Smartha Ekadashi and
  broader community variants remain open.

- Reacquire and visually recheck the publisher-hosted 1962 Vakyakarana pages
  on local daylight. The Introduction and printed pp. 255, 267–269 establish
  additional Cara, latitude/shadow, longitude/yojana, precession, and
  day/night equations; the downloaded PDF matches the retained scan digest.
  The date interpolation for the p. 255 Bhujaantara table is still
  underdetermined, its relation to the p. 252 Bhupadi correction is not stated,
  and the source omits Udayantara. Keep arbitrary-location Vakiya sunrise/
  sunset unavailable and the existing longitude-linear operation experimental.

- Repair observance golden source metadata and restrict Chennai annual date
  witness attribution to its reference location; calendar suites remain planned.

- Correct calendar display provenance to the retained TVA digest and identify
  apparent Sun/Moon longitudes as geocentric; align bootstrap numeric activation
  status with the owner-approved manifest. Calendar activation remains pending.

- Add the named `thirukanitham-tamil-named-observances-v1` subset for Thirukanitham
  TN contexts: Tamil solar month day one and the Bhogi/Pongal/Mattu sequence,
  plus Amavasya/Pournami selection in Aparahna with a sunrise fallback. Its
  Chennai annual source pages use Vakyakarana; 13 Amavasya and 12 Pournami dates
  from Nov 2026–Oct 2027 match the selected Thirukanitham output, without an
  engine or publisher-equivalence claim. Source IDs now follow their retained
  date coverage. Vakiya and Sri Lanka return explicit unsupported results, and
  wider observance families and suite activation remain pending.

- Add profile-validated Tamil date formatting and calendar display metadata
  using source-backed Tamil/Romanized month, weekday, cycle and limb labels,
  explicit Tamil/Latin digits and two fixed templates. Add a shared Rust
  comparison for one Gregorian date or UTC instant that reports both
  Thirukanitham and Ujjain mean-sunrise Vakiya contexts and semantic bases.
  Add a TN Thai-1 Thiruvalluvar profile convention for 2025–2027 with its
  source conflict and non-equivalence to an official Gazette lookup explicit.
  Keep the display, comparison and era suites planned. Observance calculation
  now includes the separately documented Nava TN subset; broader families and
  calendar-suite activation remain pending.

- Repair Vakiya civil-day reports to include the final minute and normalize
  rounded midnight labels; keep vara tied to exact mean sunrise rather than
  rounded position time. Preserve valid solar-date arithmetic in the final
  partial month of Gregorian year 9999.

- Connect the 1962 Vakyakarana/Laghuprakashika source kernels to a bounded
  Ujjain mean-sunrise civil profile: Gregorian/Tamil solar conversion in the
  source equation's exposed range, actual month lengths, reverse conversion,
  and five limbs at instants and civil-day mean sunrise. Pin the Kali epoch to
  the independently sourced proleptic Gregorian day ordinal; correct the
  ingress assignment to the first mean sunrise at or after crossing, matching
  the 1947 printed Kali-5048 example. Keep local horizon events and arbitrary
  station corrections unavailable because the scanned 1962 geometry pages do
  not supply the Bhujaantara interpolation parameter or coordinate mappings.
  Add a separate bounded Thirukanitham primary lunar-phase event operation for
  new moon, quarters and full moon; its four 2025 UTC minute outputs match the
  USNO independent phase table. Add both flows to Python, Node/browser WASM,
  Dart and workbench interfaces. Add twelve-month solar-year enumeration and
  profile-based Tamil-date day/month/year addition to both definitions. Add
  Thirukanitham Rahukalam, Yamagandam and Kuligai intervals from computed
  daylight using a visually inspected, hashed printed source table; keep
  those intervals unavailable for Vakiya while its local sunset is unsourced.
  Add the 1889 South Indian Chronological Tables romanized 60-year solar-title
  sequence for both profile domains, independently cross-checked against the
  1941 Census chronology and CICT cycle table; retain printed historical
  spellings and return source metadata.
  Add authority-published named holiday schedules for Tamil Nadu 2025–26 and
  Sri Lanka 2026–27 through a separate jurisdiction/year data operation,
  preserving issuer categories and source limits. The Tamil Nadu Gazette PDF
  bytes were unavailable for local hashing, so those responses state a null
  digest; unsupported schedules return an explicit error.
  Keep every new calendar suite planned pending separate calendar-owner review.
- Implement a bounded Thirukanitham date and panchangam path in Rust under
  `thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2`: Gregorian/Tamil solar
  conversion, month boundaries, five-limb instant and civil-day reports,
  sunrise/sunset, and profile metadata for declared TN/SL coordinate boxes in
  2024–2027. Pin `astro` 2.0.0 (MIT), its archive digest, the true Lahiri anchor
  with source-correct mean conversion, P03 precession, apparent-coordinate
  terms, time assumptions, horizon, zones and canonical lexicon data. Add the
  shared dispatcher, typed Python/Node/WASM/Dart wrappers, and workbench forms.
  Repair partial-month reverse conversion and rounded midnight transition
  labels. Production JPL DE441 checks measure max 0.106033″ Sun / 5.899331″ Moon;
  independent second-cadence data covers 49 public and one terminal solar
  ingress and 43 limb roots, while full-day sweeps confirm all 43 events across
  eight days. Quantify 2026 publisher differences and frame, aberration,
  horizon and elevation effects without assigning hidden publisher settings.
  Keep the 18-row Drik suite planned for separate calendar review; this is not
  a universal publisher-equivalence claim.
- Extend the local workbench with manual LT-TM and Vanavil CID/code conversion
  controls. Currency inputs use the shared Rust exact major-unit decimal
  operations and convert to the existing integer minor-unit API format.
- Repair exact numeric comparison across zero scales, Indian grouping,
  canonical zero percent shifts and decimal-domain validation precedence.
  Activate the 7,341 sourced v0.3 cases following explicit owner approval;
  keep calendar coverage pending its own evidence. Make ordinal,
  fraction-symbol and traditional-integer tables canonical in root `lexicon/`
  and generate package copies from those sources. Add workbench forms for all
  supported numeral operations and update generated contract documentation.
  Published alpha 4 remains unchanged. The full calendar milestone remains
  incomplete: calendar-suite review, arbitrary-location Vakiya daylight and
  correction support, observance rules, the official Thiruvalluvar boundary,
  official Tamil Nadu holiday-byte acquisition, and broader licensed annual
  holiday coverage are still open.
- Correct the historical Cara rule to exact coefficients 20/1, 16/1 and
  20/3 and preserve rational precision through final truncation. Visually audit
  all 248 Candra-vakya rows, repair printed rows 155, 165, 207 and 217, and
  validate every complementary pair while recording the source’s 10-arcsecond
  exception at rows 100/148. Enforce shared safe JSON integer limits across the
  calendar dispatcher and typed Moon/local-reduction operations. Add derived
  boundary and numeric-limit vectors, keep all six calendar suites planned,
  and label longitude-linear Bhujaantara interpolation experimental because
  the edition supplies no interpolation equation.
- Add a source-pinned historical Vakyakarana solar-transit calculation for
  elapsed Saka years 1869–1890 and an interpolated true-Sun correction from the
  1962 Bhupadi table. Add the 248-row Candra-vakya true-Moon calculation from
  the same edition's Appendix II, including its printed Kali-day worked
  example; the printed local true-sunrise longitude correction with its
  491-arcsecond Pudukkottai Moon example; the Chapter III Cara computation
  with its −72-vināḍi worked case; and Deśāntara conversion from signed
  east/west yojana distance with the −26.6-vināḍi Pudukkottai term. Keep
  the 1962 Bhujaantara endpoint table with a separately named linear-in-rāśi
  experimental longitude-linear interpolation convention that matches the
  equal-endpoint Kanyā example without establishing a historical interpolation
  rule. Keep
  calendar fixtures planned for their own review. These bounded operations
  accept supplied Sun/shadow/distance terms and do not assign Gregorian dates,
  derive a complete local sunrise, or claim equivalence with current publisher
  editions. Route the operations through the shared Rust dispatcher, thin
  language bindings, and workbench.

## 0.1.0-alpha.4 / Python 0.1.0a4 - 2026-11-01

- Add the bounded `Vanavil Avvaiyar` (`vanavil-avvaiyar-cid-v1`) 16-bit
  code/CID profile (`vanavil_codes_to_unicode`, `vanavil_text_to_unicode`,
  `unicode_to_vanavil_codes`, `unicode_to_vanavil_text`), its canonical
  319-entry mapping table, and 661 active golden vectors across Rust, Python,
  WASM, and Dart.

- Defer further Punarchi source review and implementation at user direction;
  preserve the source contract and incomplete review criteria for later.

- Pin Thamodaran's 1999 Nannūl critical edition as the first literary Punarchi
  profile's root-text/commentary source; verify the three chapter ranges and
  document provisional Tolkāppiyam comparison areas. Add a page-indexed,
  paraphrased Markdown digest and per-sūtra viewer-page locator for the TVA HTML
  edition text, add a provisional subject ledger for sūtras 151–203, and clarify
  that Project Madurai already provides a searchable Unicode companion e-text.
  Add provisional subject ledgers for sūtras 204–239 and 240–257. Keep
  fixtures inactive pending full scan inventory and linguistic review. Record
  that the earlier CICT 1979 comparison-edition selection was premature. Inspect
  the 1979 Annamalai scan (second edition, August 1979), 2003 Tamilmann edition,
  1982 WTRI Puṇariyal Uraivaḷam, and CICT's 1996 textual-variation volume.
  Document the 1996 volume's explicit limit: it presents collected manuscript
  and print variants but does not establish a single base reading. Note the
  1992 third-edition / CICT 1996 catalog discrepancy for Sundaramurthy's later
  Annamalai edition; its title page remains unverified. Keep 1979 provisional
  and the 1996 volume as a variant apparatus, not sole authority. Add
  discovery-only Project Madurai locators for Tokai Marabu 2 and 3. Add provisional
  TVA HTML root/commentary paraphrases and example citations for Nannūl sūtras
  151–157; keep them inactive pending print and linguistic review.

- Defer PDF extraction and font inspection tooling at user direction; remove
  private `tools/tamil-pdf-extract` and exploratory test artifacts.

## 0.1.0-alpha.3 / Python 0.1.0a3 - 2026-11-01

- Add the bounded LT-TM / IndoWord 16-bit code profile, its canonical
  332-entry mapping, reverse encoder, and shared dispatcher operations.
- Activate 687 sourced LT-TM golden vectors across Rust, Python, WASM, and
  Dart. Document mapping provenance and compatibility limits.
- Refresh project and package READMEs for the synchronized alpha release.
- Keep the PDF extraction CLI private; it is not included in registry packages.

## 0.1.0-alpha.2 / Python 0.1.0a2 - 2026-11-01

- Add bounded bidirectional Anjal byte conversion with explicit ambiguity errors.

- Add bounded bidirectional TAM byte conversion with monolingual byte handling.

- Add bounded bidirectional TAB byte conversion and shared cross-runtime fixtures.

- Audit TSCII byte assignments, add missing symbols and Grantha forms, and fix repeated HA byte corruption.

- Add strict bounded Unicode to TSCII byte encoding and cross-runtime bindings.

- Add bounded TSCII byte decoding, shared fixtures, and Python, WASM, and Dart adapters.
- Remove stale generated Python extensions before rebuilding bindings.

- Add shared publishing policy checks, reusable source/digest gates, and
  serialized manual uploads for future releases.
- Resolve distribution source once across platforms; run the expensive
  artifact matrix on explicit dispatch.
- Document feature development, release preparation, and durable agent handoff.
- Use numbered workspace pytest temp runs for reliable Windows reruns.

## 0.1.0-alpha.1 / Python 0.1.0a1 - 2026-10-31

- First experimental MIT-licensed release of the Rust modules and umbrella SDK,
  Python native bindings, and Node/browser WASM package.
- Unicode normalization, tailored Ezhuthu segmentation and Mei/Uyir composition.
- Versioned Agara sorting and search keys.
- Bounded TN/SL integer words, exact INR/LKR amounts, fractions, and Gregorian dates.
- Explicit Bamini decoding and strict, round-trip-checked reverse encoding.
- Shared golden corpus with 21,277 cases and seventeen 10,000-case properties.

The module specifications document bounds and linguistic conventions. APIs may
change before stability. Other legacy encodings and the planned grammar,
morphology, dialect, publishing, prosody, and PostgreSQL modules are excluded.
Dart remains a development adapter requiring a host native library.
See [contracts and publication evidence](docs/releases/alpha-1.md).
