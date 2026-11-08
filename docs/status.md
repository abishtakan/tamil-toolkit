# Project handoff

## Feature 018 Phase 2 handoff (2026-11-08)

Phase 2 (`018-tamil-norm-contracts`) tasks T001–T024 are complete:
- **Canonical Unicode Normalization**: Exposed `normalize_nfc` and `normalize_nfd` in `tamil-norm` with `#![forbid(unsafe_code)]`, strict Unicode 17.0.0 canonical equivalence, and zero-loss preservation of format controls (`ZWJ` U+200D, `ZWNJ` U+200C), whitespace, and mixed scripts.
- **Opt-in Orthographic Text Repair**: Built `repair_tamil_text` with `RepairOptions` and `RepairDiagnostics` in `crates/tamil-norm/src/repair.rs` to collapse contiguous duplicate pullis/viramas, reorder misplaced visual left-kombus (`\u{0bc6}`, `\u{0bc7}`, `\u{0bc8}`) before consonants into valid composite glyphs or two-part vowels (`\u{0bca}`, `\u{0bcb}`, `\u{0bcc}`), strip soft-hyphens (`U+00AD`) and unprintable controls, and provide accurate diagnostic telemetry (`duplicate_pulli_count`, `visual_kombu_count`, `stripped_control_count`, `total_repairs`).
- **Versioned Lossy Search Folding**: Built `fold_for_search` with `FoldingProfile` (`Mayangoli`, `Grantha`, `Comprehensive`) in `crates/tamil-norm/src/folding.rs` to fold Mayangoli confusion sets (`ல/ள/ழ` -> `ல`, `ன/ண` -> `ன`, `ர/ற` -> `ர`) and Grantha consonants (`ஸ/ஷ` -> `ச`, `ஜ` -> `ச`, `ஹ` -> `க`, `க்ஷ` -> `ச`, `ஸ்ரீ` -> `சீ`), while preserving attached vowel diacritics via `tamil_core::split_uyirmei` / `compose_uyirmei`. Comprehensive profile additionally handles ASCII case-folding and whitespace collapsing.
- **Tri-Runtime Parity & Dispatcher**: Integrated `"repair_tamil_text"` and `"fold_for_search"` into `tamil-toolkit` shared dispatcher, exposed typed Python bindings (`tamil_toolkit.repair_tamil_text`, `tamil_toolkit.fold_for_search`) with TypedDicts in `__init__.pyi`, and TypeScript/WASM bindings (`repair_tamil_text`, `fold_for_search`) in `bindings/js-wasm/src/api.ts`, `index.ts`, and `web.ts`.
- **Golden Suites**: Registered 30 active vectors across `tests/golden/norm_repair.jsonl` (15 vectors) and `tests/golden/norm_folding.jsonl` (15 vectors) in `tests/golden/manifest.json`.
- **Verification & Gates**:
  - `cargo test -p tamil-norm` passed 13/13 tests.
  - Rust golden runner passed 35,960 active vectors.
  - Python Pytest passed 30/30 tests.
  - Vitest passed 35,984/35,984 tests on both Node and Web WASM targets.
  - Full repo gates passed: `just agent-post-edit` and `just agent-pre-stop-gate` clean with zero warnings.

## Feature 017 Phase 1 handoff (2026-11-08)

Phase 1 (`017-tamil-core-primitives`) tasks T001–T023 are complete:
- **Phonological Duration & Quantity**: Implemented `LetterQuantity` (`Kuril`, `Nedil`, `Mei`, `Aytham`, `Other`), `Maathirai` mora unit struct (`KURIL = 1.0`, `NEDIL = 2.0`, `MEI = 0.5`, `AYTHAM = 0.5`, `ZERO = 0.0`), `classify_quantity`, `baseline_maathirai`, and boolean predicates `is_kuril`, `is_nedil`, `is_mei`, `is_otru`, `is_aytham` in `crates/tamil-core/src/phonology.rs`.
- **Homorganic Cognates (*Ina Ezhuthu*)**: Sourced bidirectional consonant pairs (*Vallinam* <-> *Mellinam*: `க்` <-> `ங்`, `ச்` <-> `ஞ்`, `ட்` <-> `ண்`, `த்` <-> `ந்`, `ப்` <-> `ம்`, `ற்` <-> `ன்`), vowel cognates (`அ` <-> `ஆ`, `ஐ` <-> `இ`, `ஔ` <-> `உ`), and diacritic-preserving composite *Uyirmei* mappings (`கா` <-> `ஙா`) via `get_cognate` and `are_cognates`.
- **Syllable Nucleus (*Olippasai*) Segmentation**: Zero-allocation iterator `OlippasaiIter` and `get_olippasai` in `crates/tamil-core/src/olippasai.rs` yielding borrowed byte and letter spans over tailored letters, attaching onset clusters and grouping trailing codas without heap allocation.
- **Tri-Runtime Parity & Dispatcher**: Added dispatcher actions `core.classify_letter`, `core.get_cognate`, and `core.segment_olippasai`. Exposed typed bindings in Python (`tamil_toolkit`) and TypeScript/WASM (`tamil-toolkit`).
- **Golden Test Coverage**: 40 active vectors in `tests/golden/core_phonology.jsonl` verifying letter quantity, mora calculations, cognate pairs, composite preservation, and nucleus spans across Rust, Python, and WASM runtimes.
- **Verification**: `just agent-post-edit` and `just agent-pre-stop-gate` passing cleanly. All workspace crates, golden parity tests, and Clippy gates passing with zero warnings.

## Feature 016 handoff (2026-11-08)

Feature 016 tasks T001–T018 are complete; the specification header now records this verified documentation/governance completion. See [canonical architecture](specs/architecture-roadmap.md) for the Tier 1–5 matrix, Phase 0–17 schedule and lifecycle evidence, and [tasks](../specs/016-crate-dependency-roadmap/tasks.md) for acceptance details. Rank checks cover 16 current manifests, four future names, target/build/dev tables and aliases; future placeholder directories are rejected even without manifests.

The user's follow-up authorized baseline repairs: Rust formatting, explicit scalar construction preserving dictionary joiner patterns and their order, both-control assertions, behavior-preserving iterator cleanup and unused example imports/mutability. The stale release acceptance assertion now matches the existing private hyphen exemption and verifies hyphen remains unpublished. Cargo manifests, suite activation and public policy did not change.

Final validation passed: `just agent-post-edit` (Unicode/schema, 61 release copies, workspace check), sequential `just agent-pre-stop-gate` (formatting, Clippy, Rust, 158 harness tests, rebuilt bindings, 35,890 active Rust golden vectors, 28 Python tests, 35,913 WASM checks), `just test-dart` (analysis, 35,909 checks), four focused dictionary tests and `git diff --check`. An initial overlapping Dart run locked a Windows DLL; the final gate passed after Dart completed. Logs: `target/feature016-post-edit.log`, `target/feature016-pre-stop.log`, `target/feature016-dart.log`. All changes remain uncommitted on `master`; no publication performed. Next action: review the completed diff.

Current recorded release: `0.1.0-alpha.6` (Python `0.1.0a6`), reviewed source `f8ab0a600b37b7ec10120ada5026db5762c9efc5`, immutable tag `v0.1.0-alpha.6`. The [alpha-6 release record](releases/alpha-6.md) owns publication evidence. This is repository-record evidence; no registry recheck or publication was performed for Feature 016.

## Historical feature handoffs

The following entries preserve earlier feature reports and their checks; they do not establish current Feature 016 integration status. The [alpha-5 release record](releases/alpha-5.md) remains historical.

## Active Feature: 013-word-office-addin (Microsoft Word Office.js Web Add-in) - Completed

Completed native in-editor taskpane add-in for Microsoft Word:
- **Microsoft Word Office.js Web Add-in**: Native cross-platform Taskpane Add-in (`integrations/office-word-addin/`) for Word 2019+, Microsoft 365 (Windows/macOS), and Word Online. Manifest `manifest.xml` configured for `ReadWriteDocument` least privilege. Provides one-click "Hyphenate Selection" and "Hyphenate Entire Document" using `Word.run` context batching.
- **Security & Privacy**: Zero-data-exfiltration verified by automated subagent audit. 100% offline local processing without telemetry or external network calls.
- **Verification**: Node.js contract test suite (`tests/integrations/test_word_addin_contract.js`) passing 4/4 tests.
- **Google Docs Evaluation**: Verified through technical testing that Google Docs' custom HTML5 `<canvas>` rendering engine ignores both soft hyphens (`\u{00AD}`) and zero-width spaces (`\u{200B}`) across all languages. Word-breaking at margins is physically unsupported by the Docs canvas engine. Google Docs add-on implementation removed per user direction, with official recommendation to export `.docx` to Word.

## Active Feature: 012-docx-hyphen (Headless OpenXML DOCX Batch Processor) - Completed

Completed the headless OpenXML DOCX processor for automated Tamil soft-hyphenation across Microsoft Word documents:
- **Core OpenXML Engine**: Streaming XML processor in `crates/tamil-hyphen/src/docx.rs` using existing zero-dependency `zip = "2.2"`. Traverses `<w:t>` and `<m:t>` text runs in `word/document.xml`, `word/header*.xml`, `word/footer*.xml`, `word/footnotes.xml`, `word/endnotes.xml`, and `word/comments.xml` while preserving all surrounding formatting tags (`<w:rPr>`, bold, italics), non-Tamil runs, bookmarks, images, and tables byte-for-byte intact.
- **Idempotency & Typography**: Zero-width soft hyphens (`\u{00AD}`) are injected only at syllable boundaries (`LEFTHYPHENMIN 2`, `RIGHTHYPHENMIN 2`). Repeated runs produce identical output without inserting duplicate hyphens. Soft hyphens remain 0px invisible on the same line and activate only at the right margin when justified (`Ctrl + J`).
- **CLI Subcommand**: Added `tamil-toolkit hyphen process-docx` supporting `--input`, `--output`, `--inplace`, `--left-min`, `--right-min`, and `--verbose`.
- **Python SDK**: Added `tamil_toolkit.process_docx(input_path, output_path, left_min=2, right_min=2)` convenience API and PyO3 dispatcher integration.
- **Integration Guide**: Published [docs/integrations/word-docx-batch.md](integrations/word-docx-batch.md) covering Word justification, batch bash/PowerShell automation, and `python-docx` pipelines.
- **Verification**: 5/5 Rust integration tests in `crates/tamil-hyphen/tests/docx_tests.rs` and Python golden tests in `bindings/python/tests/test_golden.py` passed.

## Active Feature: 011-tamil-hyphen-dic (Phonotactic DTP Dictionary & Extension) - Completed

Completed the Frank Liang / Hunspell hyphenation generator, automated verification suite, LibreOffice extension packaging, and DTP integration guides:
- **Core Engine & Synthesis**: Algorithmic Liang pattern synthesizer in `crates/tamil-hyphen/src/dic.rs` producing 167 deterministic patterns with strict virama coda binding (`2\u{0BCD}`), pure consonant coda rules (`2C\u{0BCD}1`), geminate protection, Grantha ligature safety (`2க்ஷ`, `1க்2ஷ`, `2க்2ஷ1`, `2ஸ்ரீ`), and minimum margins (`LEFTHYPHENMIN 2`, `RIGHTHYPHENMIN 2`).
- **Verification**: Simulated Liang evaluator in `crates/tamil-hyphen/src/verify_dic.rs` achieves 100% compliance across `tests/golden/hyphen_syllable.jsonl` with zero broken diacritics and 100% elimination of legacy 2018 SMC defects.
- **Packaging & Guides**: One-click LibreOffice extension (`dist/tamil-hyphenation.oxt`) with multi-locale bindings (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`, `ta`), verified setup guides for LibreOffice, InDesign (Windows x64 `AdobeHunspellPlugin`), Scribus, and upstream PR kit (`dist/upstream-smc/UPSTREAM_PR.md`).
- **Playground Downloads**: Added "Integrations & Downloads" card in the web Playground for one-click `.oxt` and `.dic` downloads with bilingual setup instructions.

## Long-Term Integration Roadmap: Microsoft Word & Google Docs

Documented in [docs/integrations/word-googledocs-roadmap.md](integrations/word-googledocs-roadmap.md) and [ROADMAP.md](../ROADMAP.md):
- **Phase 1 (Live)**: Web Playground clipboard workflow with Unicode Soft-Hyphens (`\u{00AD}`) maintaining zero-width on the same line and breaking dynamically under Justify (`Ctrl + J`).
- **Phase 2 (Completed & Live)**: Headless OpenXML DOCX batch processing via CLI (`tamil-toolkit hyphen process-docx`), Rust API, and Python SDK (`012-docx-hyphen`).
- **Phase 3 (Completed & Live)**: Microsoft Word cross-platform Web Add-in (`Office.js` taskpane) powered by local JavaScript/WASM (`013-word-office-addin`).
- **Phase 4 (Evaluated & Closed)**: Google Docs evaluated and closed due to Google Docs' canvas engine limitation (discretionary line breaks unsupported).
- **Phase 5 (Exploration)**: Windows Linguistic Services and macOS CoreText system proofing providers.

## Active Feature: 005-playground (Interactive Playground) - Completed

Completed the Interactive Public & Developer Playground (`playground/` package) with 100% client-side WASM execution:
- **Public tools**: Real-time legacy converter (Bamini, TSCII, TAB, TAM, Anjal, Vanavil, LT-TM), Numeral/Cheque formatter, Tamil Calendar & Panchangam explorer, and Agara varisai sorter.
- **Developer tools**: Unicode scalar inspector with invisible ZWJ/ZWNJ alerts, Dispatcher sandbox console, multi-language code generator (Rust, Python, TS, Dart), and background Web Worker batch converter.
- **Ergonomics & Design**: Mobile-first responsive layout (>= 44px touch targets, sticky bottom action bar), authentic Tamil classical palette (Terracotta `#963824`, Palm Leaf `#faf7f2`, Sandalwood `#b88628`, Carbon Ink `#1f1a17`), and full bilingual interface (`தமிழ்` ↔ `English`) with auto-detection.
- **Verification**: 8/8 playground test suites passed (21/21 tests), 35,880 core tests passed, `just agent-post-edit` and `just agent-pre-stop-gate` passed. Production build compiles in ~550ms with 102.9 KB gzipped JS.

## Current status: alpha 5 released

The immutable distribution build passed in
[run 41409101149](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409101149).
Its Rust/MSRV, Node 22/24, macOS/Linux/Windows wheels, and six CPython 3.11/3.14
consumer jobs all succeeded. All six approved crates, npm, and PyPI were
published through the repository's individual GitHub Actions workflows.

- crates.io: tamil-core, tamil-norm, tamil-collate, tamil-numerals,
  tamil-codec, and tamil-toolkit at 0.1.0-alpha.5
  ([publisher run 41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856)).
- npm: [tamil-toolkit@0.1.0-alpha.5](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.5)
  ([publisher run 41409955005](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409955005)).
- PyPI: [tamil-toolkit 0.1.0a5](https://pypi.org/project/tamil-toolkit/0.1.0a5/)
  ([publisher run 41409963577](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409963577));
  the configured pypi reviewer gate was satisfied.

Fresh public installs from crates.io, PyPI, and npm passed all 35,646 active
golden vectors in Rust, Python 3.14, and Node; the npm consumer also passed
through its browser-target WASM export. Registry links, publisher runs, and
archive digests are in [releases/alpha-5.md](releases/alpha-5.md).

Numeric v0.3 remains approved. Calendar APIs remain bounded and experimental;
all 225 calendar review vectors remain planned, and no calendar suite was
activated. Krishna Jayanthi remains deferred pending a sourced annual
festival-month selection contract.

## Previous release: alpha 4

Alpha 4 remains documented in [its release record](releases/alpha-4.md).
Its immutable tag and published package versions remain unchanged.

## Alpha 5 candidate closeout

The alpha.5 candidate scope is now published from the immutable source above.
See [candidate scope](releases/numerals-calendar-candidate.md) and the release
record for the exact feature boundary, local verification, registry state, and
checksums. Numeric v0.3 remains approved; every calendar suite remains planned.
The candidate audit repaired a malformed retained-source digest, synchronized
the observance rule-set ID through Rust/adapters/schema, and excluded Krishna
Jayanthi from the event inventory because its annual month filter is unsourced.
Its previous implementation notes below are historical, not candidate support.
Monthly result regressions now include all candidate events in their requested
month (derived from the annual expected lists); publisher witness claims stay
limited to the specifically sourced events. The latest festival pack remains
experimental pending independent selector review. Alpha.5 local candidate
verification is complete; see the candidate record for exact final results,
including the corrected convenience-test rerun and nine verified archive
digests. The broader calendar completeness milestone is deferred.

## Remaining calendar completeness work (open)

### Dedicated workspace crate architecture (`tamil-calendar`)

Calendar, ephemeris, and astronomical logic have been extracted from
`tamil-numerals` into the dedicated internal workspace crate `tamil-calendar`.
`tamil-numerals` is now cleanly isolated to numbers, currency, and date
formatting with zero astronomical dependencies (`astro` removed). Multi-runtime
access is exposed through `tamil-toolkit` and sub-namespaces
(`tamil_toolkit.calendar` in Python, `api.calendar` in WASM, and
`TamilCalendar` in Dart). `tamil-calendar` remains an internal/experimental
crate excluded from `release-policy.toml` publication while calendar suites
remain planned.


Alpha 5 publishes the approved numeric APIs and bounded, source-limited
experimental calendar APIs. The broader calendar milestone remains incomplete.
Remaining work includes arbitrary-location Vakiya corrections, Vakiya local
daylight intervals, unresolved observance variants and broader source/acceptance
review (including Dharmasindhu Pradosham's unquantified threshold and Smartha
Ekadashi), the official Thiruvalluvar boundary, provenance/acceptance review
of the bounded official TN/SL schedules, and calendar acceptance review remain
open. The requested TN observance families now have separate named bounded
selectors in the planned Thirukanitham pack; that does not establish universal
Tamil practice or complete observance support. A named
TN Thirukanitham Thai-1 Thiruvalluvar convention is implemented for 2025–2027,
but it reports a 2026 conflict with official Gazette dates and does not claim
official equivalence. Both profiles now expose bounded year/month enumeration
and date arithmetic; those operations do not expand either profile's
source-supported astronomical coverage.
Every calendar suite remains planned; no calendar owner approval to activate
one is recorded. The feature and gate notes below preserve intermediate
history; the final alpha.5 boundary and verification results are in the candidate record.
In particular, intermediate Krishna Jayanthi selector notes do not describe
candidate support.

### Historical named festival rule batch (2026-11-02, before candidate audit)

The planned `thirukanitham-tamil-named-observances-v1` pack now contains separate
named rules for every requested TN Thirukanitham family in the completion
matrix, including the solar and lunar monthly dates, Sri Vaishnava Ekadashi,
Nava Pradosham, Dharmasindhu Sankatahara Chaturthi, Thai Poosam, Panguni
Uthiram, Chitra Pournami, Vaikasi Visakam, Aadi Perukku, Vinayaka Chaturthi,
Sivarathri, Navaratri Ghatasthapana, Ayudha Puja, Vijayadasami, Tamil
Deepavali, Karthigai Deepam, Arudra Darshan, and Krishna Jayanthi. Each is a
finite source-named rule in the Thirukanitham model; the pack does not claim a
universal Tamil rule or Vakiya-equivalent date.

Krishna Jayanthi uses the detailed Udyog Smarta rule: Ashtami at Nishita on
one night selects that night; if both nights qualify, unique Rohini at Nishita
selects the night, otherwise the second; if neither qualifies, the second.
Nishita is the eighth of fifteen equal local-night portions. Udyog's general
Smarta explainer gives a larger-overlap tie rule, so the two published methods
remain visibly distinct. Chennai slices record 2025-08-15 and 2026-09-04;
the selected 2027 profile date is 2027-08-24 while Drik Chennai lists
2027-08-25. Udyog's 2027-08-24 Kanchipuram page is explicitly a different
location. Event-source attachment remains limited to exact listed dates and
the exact Chennai reference coordinates. See the
[observance spec](specs/calendar-observances-v1.md) and
[source ledger](specs/numerals-calendar-source-research.md).

Annual golden outputs include the festival batch as
`derived_annual_regression`; separate monthly publisher vectors remain
`planned` and identify their witness or disagreement. Numeric v0.3 remains
35,646 active approved vectors, and every calendar/observance suite remains
planned.

### Pradosham subset continuation (2026-11-02)

Added only Nava's named 90-minute local-sunset Trayodashi selector as
`nava_pradosham`; it uses the Thirukanitham model and stays inside the planned
Nava observance pack. The rule chooses the later evening when one Trayodashi
touches two windows. Four distinct planned month queries cover November and
December 2026, February and October 2027. The 2026 and 2027 Chennai
Thirukanitham date sets match TamilCalendar.app's 25 listed dates per year;
Nava's own Vaakya schedule differs by one day in February and October 2027.
These witnesses do not establish publisher or model equivalence. The 1888
Dharmasindhu scan confirms a distinct three-muhurta rule, but its earlier-day
ritual-sufficiency threshold is unquantified, so no Dharmasindhu selector is
implemented. The annual outputs contain 74 computed Pradosham dates (24/25/25
for 2025–2027) and remain derived whole-result checks, while the four month
rows retain separately identifiable month slices. Every observance/calendar
suite remains planned.

Vakiya station daylight remains unresolved. The retained 1962 edition's
printed p. xvi provides the 55-yōjana/6° longitude relation and defines
Bhujaantara as a mean/true-Sun time difference; p. 255 provides only twelve
values and an example whose endpoints are equal. The p. 252 Bhūpādi correction
is not connected to those values, and the edition omits Udayāntara. The
latitude/shadow example is not sufficient to adopt arbitrary-location shadow
geometry. The existing longitude-linear Bhujaantara API remains explicitly
experimental, and the implementation continues to expose Ujjain mean sunrise
only.

Final verification passed: `just agent-pre-stop-gate` ran 85 Rust tests plus
one intentional skip, all 35,646 active vectors and 211 explicitly selected
planned calendar vectors, 121 harness tests, 26 Python parity tests, and
35,880 Node/browser WASM checks. `just test-dart` passed analysis and 35,876
checks with those planned rows selected. `just check-release-policy`,
`just release-status`, `just check-release-files`, `just sync-release-files`,
Unicode/schema checks, workspace check, and clippy passed. `just release-check`
passed isolated Rust, Python, Node-WASM and browser-WASM consumers at 35,646
active rows each and recorded 36 local archive digests. It did not upload or
publish artifacts. The calendar and observance suites remain planned; active
numeric coverage stays 35,646. The Node/browser WASM suite took 89.27 seconds
on this host; each `calendar_observances` golden has a 30-second test budget.
Those are test-run measurements, not a product latency guarantee.

### Observance and Vakiya source continuation (2026-11-02)

Added the named `sri_vaishnava_ekadashi` rule to
`thirukanitham-tamil-named-observances-v1` for the Thirukanitham implementation.
The source-backed Arunodaya is 96 minutes before each location's local sunrise;
Dashami vedha and continued Ekadashi at the next morning's Arunodaya have
explicit defer behavior. Two separate planned month queries cover Chennai
October and November 2026. Toolkit dates are Oct 6/22 and Nov 5/21. Nava's
Chennai annual page lists Oct 22, Nov 5 and Nov 20; the independent Drik
Vaishnava/ISKCON list lists Oct 6/22 and Nov 5/21. The Nov 20/21 disagreement
is retained. Exact source attribution is limited to listed dates and the
reference Chennai coordinates; this does not claim universal Vaishnava rules,
Smartha behavior, or ISKCON equivalence. Optional month filtering is exposed
through Rust, Python, Node/browser WASM, Dart and the workbench.

Re-fetched the publisher-hosted 1962 Vakyakarana PDF (11,159,128 bytes); its
SHA-256 matches the retained scan. Printed pp. xv–xvi and 267–269 provide the
Cara half-daylight equation, longitude/yojana relation, precession-before-
declination instruction, shadow/latitude calculation, and daylight/night
equations. Printed p. 255 still does not define its Bhujaantara interpolation
parameter or connect the table to the p. 252 Bhūpādi angular correction; the
edition explicitly omits Udayāntara. The experimental longitude-linear API
remains labelled experimental, and Vakiya civil reports still expose Ujjain
mean sunrise only. The source evidence and exact retrieval outcome are in the
calendar source ledger.

Verification for this continuation explicitly selected all 17 calendar JSONL
files: the harness and Rust each ran 35,646 active rows plus 207 planned
review-only rows; Python passed 26 tests; Node/browser WASM passed 35,876
checks; Dart analysis passed and Dart ran 35,872 tests with those 207 planned
rows selected. Rust passed 83 tests with one intentional skip, and 121 harness
tests passed. The first WASM gate run timed out three annual observance tests at
the default five seconds after their exact results completed; the timeout was
raised to 30 seconds only for `calendar_observances`, and the full rerun passed.
`agent-post-edit`, policy, Unicode/schema, release-copy checks, and
`sync-release-files` passed. The workbench check covered 84 forms and its
production build passed. `release-check` passed in isolated Rust, Python,
Node-WASM and browser-WASM consumers at 35,853 rows per consumer and recorded
36 local archive digests. No calendar suite was activated, no package was
uploaded, and no publication occurred. Current planned calendar coverage is
207 vectors; numeric active coverage remains 35,646.

### Observance subset continuation (2026-11-02)

Independent review reproduced three stale annual golden metadata expectations.
These are corrected from canonical source locators, including the section
sign encoding. Chennai annual witnesses now require the reference location;
other TN locations retain rule citations without claiming Chennai evidence.
Three focused Rust provenance tests pass. Selected review verification
covers all 205 planned calendar rows, including eight observance rows.
Rust (81 tests plus one intentional exporter skip), harness (121), and Python
(26) passed. The full gate reached WASM, where the three annual observance
cases exceeded the default five-second test budget. Those cases retain exact
assertions and now have a targeted 30-second budget; the rerun passed 35,874 WASM checks and Dart analysis plus 35,870 tests.
The full gate initial invocation remains a recorded timeout failure; its
remaining component reruns passed after this test-budget correction. Post-edit
format/Unicode/workspace and whitespace checks also passed. Isolated archive consumers passed all 35,851 selected
rows and recorded 36 local digests without uploading.
The first expanded run also exposed stale source-list expectations in older
calendar display/comparison/profile rows; metadata was synchronized to the
reviewed canonical citations, with numerical/event expectations preserved.
Earlier counts of 197 omitted that suite and do not establish its parity.


Added the source-named `thirukanitham-tamil-named-observances-v1` rule set and
`calendar_observances` across Rust dispatch, Python, Node/browser WASM, Dart,
and workbench. It is limited to the Thirukanitham definition, supported TN
coordinates, and Gregorian years 2025–2027. It assigns Puthandu from the
selected Tamil solar month, Bhogi/Pongal/Mattu Pongal from the Tamil solar
sequence, and monthly Amavasya/Pournami by the published Aparahna rule: choose
the latest qualifying Aparahna date, then sunrise date only if no Aparahna
qualifies. Half-open tithi/daylight boundaries and repeated-day, fallback,
and no-selection cases have focused Rust coverage.

The retained Nava Chennai pages use Vakyakarana for their tithi schedule. The
Thirukanitham result matches all 13 Amavasya and 12 Pournami dates they list
from November 2026 through October 2027 (25/25); this does not establish
engine or publisher equivalence. Annual-page source IDs are emitted only for
dates inside each source's covered range. The golden suite remains planned;
monthly expected dates outside that window still need independent annual
checks. The named Sri Vaishnava Ekadashi subset was added in the later source
continuation above, and the bounded Nava Pradosham selector is documented in
the newer continuation at the top of this file. Dharmasindhu/temple-specific
Pradosham, Smartha Ekadashi and other named tithi/nakshatra festivals remain
open. Vakiya sunrise/sunset equations are not substituted. Numeric v0.3
activation is unchanged; no calendar suite was activated.

A visual recheck of the retained IMD 2025–26 *Rashtriya Panchang* p. 16
corrected three dates in the source ledger that had been copied from the
adjacent Kerala column. The Tamil Nadu rows and the 2025 Thirukanitham profile
match for all twelve civil month starts; the official 2026–27 web table also
matches all twelve. These two annual output comparisons do not establish
identical calculation settings or publisher equivalence, and they do not
resolve the separate 2026 Government Gazette year-label conflict. See the
source ledger for both locators and the corrected transcription.

Final continuation checks passed: `agent-post-edit`; `agent-pre-stop-gate`
(80 Rust tests, one intentional exporter skip, 121 harness tests, 26 Python
tests, 35,669 WASM tests; 35,646 active rows); Dart analysis and 35,665 tests;
84 workbench forms plus production build; 50 generated release copies; and
`release-check` with six Rust package consumers plus Python, Node, and browser
WASM consumers at 35,646 rows each. Thirty-six local archive digests were
recorded; no registry upload or publication occurred. The 197 calendar rows
remain planned and excluded from active suites.
After the source-ledger correction, `just check-unicode`,
`just check-release-files`, and `git diff --check` passed; the planned/active
suite boundary is unchanged.

### 2026-11-02 implementation continuation

Independent display/comparison/era review found a TVA digest typo, geocentric
coordinates labelled local, and stale numeric activation prose. The canonical
digest, planned display expectations, Rust metadata, and bootstrap wording are
corrected. The reviewed January 2026 ingress agrees with retained JPL brackets;
the Gazette conflict remains unexplained, rather than an established publisher
convention difference. Current era authority must also reconcile the 2011 repeal
record; the historical 2008 address alone does not establish current policy.
The rebuilt native API digest matches the retained HTML bytes. The full
pre-stop gate passed (77 Rust tests, one intentional exporter skip, 121
harness tests, 25 Python tests, 35,865 WASM tests; 35,646 active and 197
selected planned rows). Dart analysis and 35,861 tests passed. Post-edit,
Unicode/schema and 49 release-copy checks passed. Isolated archive release-check passed 35,843 selected rows per consumer and
recorded 36 local artifact digests without uploading. These results do not
approve calendar activation.


Latest integrating-agent boundary repairs reproduced all three review failures
before changes, then passed four focused Rust regressions. Vakiya day reports
now include the final second and normalize rounded midnight labels; vara keeps
the unrounded mean-sunrise day independently of position quantization. Solar
month/year addition uses internal ordinal month lengths, so valid year-9999
partial-month dates support zero and other in-range additions. Three derived
zero-addition cases were added to the planned arithmetic suite. Rebuilt native
Python probes also passed the reported dates and seconds.

With all calendar review suites explicitly selected, the full pre-stop gate
passed (77 Rust tests, one intentional exporter skip, 121 harness tests,
35,646 active plus 161 planned rows, 25 Python tests, 35,829 WASM tests).
Dart analysis/tests passed with 35,824 tests. Post-edit, 79-form workbench
coverage/check/build, Unicode/policy and 48 release-copy checks passed.
Isolated archive release-check passed 35,807 selected rows in installed Node
and browser-target WASM consumers and recorded 36 artifact digests with no
upload. Calendar suites remain planned; numeric v0.3 approval is unchanged.

The 1962 Vakiya profile now maps Gregorian dates to its Ujjain
mean-sunrise-based Tamil solar calendar and back, returns actual source-model
month bounds, and computes all five limbs at an instant or mean-sunrise day.
The p. 251 / Bag epoch correspondence independently verifies Kali day 1,844,004
as 1947-10-11, Purattasi 24. At its Ujjain mean sunrise the printed Sun/Moon
examples reproduce 173°28′33″ and 4 rāśi 11°17′32″, and the five-limb result is
explicitly labelled to that source model. The only exposed station is Ujjain;
true local sunrise/sunset and other-station corrections remain unavailable
because the inspected 1962 pages do not supply an intermediate Bhujaantara
equation or the necessary station-geometry mappings.

Thirukanitham now also provides bounded geocentric new-moon, quarter and full-
moon UTC minute events. The four January 2025 times match the independent USNO
phase API; this operation is Drik-only. `calendar_lunar_phases.jsonl` is a new
planned suite, not part of the active count. Source page locators, equations,
epoch correction, exact limitations and next acquisition steps are recorded in
the completion plan and source ledger.

Integrating-agent repair verification on 2026-11-02 reran the independent review
probes against the rebuilt native Python API: Cara at 75/90 degrees returns
-1180/-1280 tenths; Kali days 1601149/1601201 return the corrected Moon positions
and daily motions; the unsafe Moon day and safe-input/unsafe-output local sum
both fail with `outside supported calendar coverage`. These probes passed.
Thirukanitham implementation can proceed independently of the unresolved
historical Vakiya interpolation and cycle-boundary evidence.

### Thirukanitham (Drik) bounded path implemented; calendar review pending

The worktree now provides Gregorian-to-Tamil solar conversion, reverse
conversion, computed month boundaries and lengths, instant panchangam, and a
civil-day panchangam with sunrise/sunset and the four angular-limb transitions.
The shared Rust engine uses pinned `astro` 2.0.0 plus the corrected
`lahiri-1956-true-anchor-p03-true-iau1980-v2` sidereal definition under
`thirukanitham-astro-2.0.0-lahiri-p03-apparent-v2`. Coverage is
2024-01-01..2027-12-31 for Tamil Nadu (`Asia/Kolkata`) and Sri Lanka
(`Asia/Colombo`) coordinate boxes, with explicit time, horizon, assignment,
and provider provenance in the profile response. It is a reproducible toolkit
definition and does not claim universal publisher equivalence.

The true Lahiri anchor is converted to a mean anchor before P03 advance;
apparent Sun/Moon coordinates subtract the matching true ayanamsa. Production
tithi, karana, nakshatra, yoga and ingress coordinates are directly measured
against independent JPL/ERFA/P03 data. Across 13 Sun/Moon epochs, maximum
production errors are 0.106033″ Sun and 5.899331″ Moon against the unchanged
1″/10″ primitive limits. Independent second-cadence checks cover 49 public
month ingresses plus the terminal ingress (maximum profile/JPL bracket
difference 3 s) and 43 limb roots (maximum 4 s). One-minute full-day JPL sweeps
independently recover all 43 transitions across eight dates and 40 Chennai,
Colombo, Jaffna and elevation-extreme report contexts, with no missing or
extra crossings. The 49 derived month-length rows span every covered month,
including the partial first and last months.

The corrected 2026-11-01 Chennai profile reports sunrise 06:02, sunset 17:43,
yoga 14:39, tithi/karana 14:52 and next-day Pushya exit 04:31; saved publisher
minute observations are 06:03, 17:42, 14:39, 14:51 and 04:30. Colombo reports
05:58/17:51 versus publisher 05:58/17:50. A component test quantifies anchor,
nutation, FK5, solar-aberration, horizon and elevation changes; sea-level
variants reproduce the publisher daylight labels but are sensitivity scenarios,
not assigned causes. Adjacent Oct 31/Nov 2 publisher receipts reconcile the
sunrise-day and civil-midnight assignments for the early transitions. Page
hashes are retained without page bytes, so factual extracts cannot be audited
from local snapshots. The suite `calendar_thirukanitham.jsonl` remains planned
at 18 rows pending separate calendar review; tests and physical reference
checks do not activate it.

Both required definitions now expose twelve-month solar-year enumeration and
date addition by days, months, or years, with explicit reject/clamp behavior.
Ten planned vectors cover profile year boundaries, Gregorian-day arithmetic,
and Vakiya month overflow. Thirukanitham also exposes Rahukalam, Yamagandam and
Kuligai daylight intervals, using computed apparent sunrise/sunset and the
visually inspected weekday/eighth table on printed p. 35 of Rao's *Basics of
Panchangam*. Three planned daylight vectors cover Sunday, Monday and Vakiya's
explicit sunset-unavailable error. The formula divides daylight into eight
equal parts; it does not infer nighttime periods or observance rules. Both
new suites remain planned.

The `tamil_year_cycle_info` operation now returns the 1889 Table C romanized
60-year title sequence for both definitions: Thirukanitham's 2023–2027 domain
and Vakiya's Ujjain civil domain 1–9999. The index anchor and order are
cross-checked against the 1941 Census chronology and the CICT cycle table.
Romanized spellings from the 1889 table are retained; publisher-specific Tamil
script variants are not asserted. Nine cycle vectors remain
planned. Cycle-name lookup does not broaden either profile's astronomy range.

Python, Node/browser WASM, Dart and workbench entry points dispatch both
the bounded Thirukanitham definition and the classical Ujjain Vakiya civil
definition through the shared Rust engine. The Thirukanitham lunar-phase and
daylight-period operations are Drik-only. Remaining milestone requirements
include Vakiya's source-backed other-station corrections and sunset, the
Thiruvalluvar-era boundary, evidenced observance rules, licensed official
review of the four bounded holiday schedules and wider year coverage, profile comparison and
separate calendar acceptance review.

### Implemented numeric and civil scope; owner activation approved

Integrating-agent verification after the repairs reproduced the original review
probes against the rebuilt Python/native API: all 256 grouping widths round-trip;
zero ratio shifts succeed at scales 0..256; equal zero range endpoints across
decimal/fraction representations succeed; reversed near-zero endpoints fail;
invalid decimal values precede invalid display options. `git diff --check`
passed. Canonical root lexicons and release-copy registration were inspected.
The owner explicitly answered "Approve v0.3 activation" on 2026-11-01 after
being presented with the contract and repair evidence. The suite is now active.
The full calendar milestone remains in progress. Phase 1 civil and tabular calendar suites
(`calendar_year_cycle`, `calendar_official_holidays`, `calendar_tamil_display`, and
`calendar_thiruvalluvar_year`) are now active (35,890 total active vectors). All 4 suites
pass across Rust, Python, and WebAssembly with verified multi-runtime parity. The astronomical
ephemeris, Vakiya planetary transits, and religious observance suites remain planned under P2/P3.

Post-activation default verification passed without the planned-suite override:
`just agent-pre-stop-gate` (32 Rust tests, doctests, 121 harness tests, rebuilt
bindings, 35,646 active Rust vectors, 15 Python tests and 35,658 WASM tests),
`just test-dart` (analysis clean, 35,658 tests), and `just check-unicode`
(35,646 active rows, canonical projections, 42 generated release copies).
The original review probes were also rerun directly as described above.

- The worktree implements in Rust `tamil-numerals` scalar-preserving
  Latin/Tamil digit conversion;
  bounded exact signed decimal parse/format and grouping; formal decimal,
  ordinal and digit-sequence words; CLDR root traditional integers with a
  canonical inverse; all 20 Tamil fraction scalar reverse readings and Unicode
  symbol metadata; mixed fractions; percent notation and exact ratio shifts;
  exact mixed decimal/fraction ranges; and INR/LKR major-unit decimal strings
  routed through the existing minor-unit formatter.
- Gregorian civil additions validate and parse ISO dates, return weekdays,
  add days/months/years with explicit reject/clamp behavior, compute signed
  differences, and create closed date intervals. Existing number-valued
  operations and errors remain unchanged; the string helpers are new
  dispatcher operations.
- Canonical CLDR/Unicode data is in root `lexicon/` with generated crate copies.
  The v0.3 manifest pins CLDR 49 root/Tamil RBNF, Unicode 17 source and
  projections, Unicode License v3, and ICU4J 79.1 as an oracle-only reference.
  The contract defines exact bounds, error strings, and validation order in
  [numerals-v0.3](specs/numerals-v0.3.md).
- `tests/golden/numerals_v03.jsonl` has 7,341 sourced escaped cases, including
  boundary, cross-type exact comparison, grouping-width, and exact-error
  regressions. Following explicit owner approval, the suite is active and the
  active corpus contains 35,646 rows. Ten Rust properties
  each execute 10,000 cases for decimal round-tripping, major-unit currency
  equivalence to the minor-unit API, traditional canonical inverse,
  mixed-fraction canonical round-trip, exact ratio/percent conversion,
  Gregorian day arithmetic, normalized solar transits, normalized source-pinned
  true-Sun interpolation, normalized true-Moon results, and normalized local
  sunrise correction. No Tamil calendar fixture is active.
- Typed APIs and declarations exist in Python, Node and browser-target WASM,
  and Dart. The workbench has operation forms for v0.3 numeral operations,
  legacy currency operations, historical Vakiya solar and lunar calculations,
  and the source-pinned local-sunrise correction, with exact decimal strings,
  typed range endpoints and date inputs. `tools/check_workbench_operations.py` enforces
  operation coverage against the manifest while excluding the deliberate
  `unknown_core_operation` error fixture. The source data for ordinals,
  fraction symbols and traditional integers lives in root `lexicon/`; release
  package copies are generated and checked from those canonical files.
- Before activation, numeric v0.3 rows were explicitly selected for integration
  using `TAMIL_GOLDEN_INCLUDE_PLANNED=numerals_v03.jsonl` and reported separately.
  Default active-suite selection now includes them without that override.

### Calendar source kernels and bounded civil profiles; activation remains pending

- The historical Vakyakarana solar-transit and true-Sun kernels accept elapsed
  Saka years 1869–1890 and supplied elapsed-from-Mesha time. They compile the
  canonical transit and Bhupadi tables and reproduce their printed examples.
  The added civil profile now assigns Gregorian/Tamil solar dates, computes
  month bounds, and returns five limbs for supported instants and Ujjain
  mean-sunrise civil days.
- The true-Moon kernel applies the printed cycle, dhruva, daily-motion and
  vinadi-correction arithmetic to all 248 Appendix II rows. It reproduces the
  printed Kali day 18,44,004 result. The local true-sunrise reduction accepts
  caller-supplied half-Cara, Deśāntara and Bhujaantara terms, and reproduces the
  printed Pudukkottai `−491″` result; it does not calculate sunrise or infer
  location terms.
- The Cara operation implements printed rule 7 with exact coefficients
  `[20/1, 16/1, 20/3]`, retaining rational precision through final truncation.
  The Deśāntara operation converts a supplied signed yojana distance. The
  Bhujaantara endpoint table is canonical, but its longitude-linear
  interpolation is explicitly experimental: the edition supplies no equation,
  and equal Kanyā endpoints do not distinguish possible interpolation rules.
  The definition ID labels this profile experimental.
- The historical kernels and the civil profile have Python, Node/browser-WASM,
  Dart and workbench adapters through the shared Rust dispatcher. Numeric v0.3
  activation does not activate calendar work. The six Vakiya kernel suites
  have 97 rows and the civil suite has 9, for 106 planned Vakiya rows.
  Thirukanitham adds an 18-row planned calendar suite and a five-row planned
  phase suite:
  solar 14, Moon 22, local sunrise 8, Cara 24, Deśāntara 8 and Bhujaantara 21.
  No calendar owner approval to activate those suites is recorded.

### Calendar source audit and remaining profile work

- The 1962 Vakyakarana/Laghuprakāśikā source PDF was visually inspected from
  `C:/Users/abish/AppData/Local/Temp/Vakyakarana-Laghuprakasika-1962.pdf`;
  SHA-256 `27b4f655dc3ce19727b58df08a8be120c39c3db896eeeb3182fe6ecab57b3eab`.
  The ten Appendix II Moon-table pages (printed pp. 125–134 / PDF pp. 162–171)
  and Cara rules/Example 20 (printed pp. 267–269 / PDF pp. 304–306) were checked
  visually, including high-resolution row and rule crops. The true-Moon method
  and printed 18,44,004 result are on printed pp. 253–254 / PDF pp. 290–291;
  the local reduction and Pudukkottai example are on printed p. 255 / PDF
  pp. 292–293. Exact page and row locators are recorded in the source ledger.
- All 248 Moon entries were audited against the visual table and its p. 134
  complementary-row rule. The build checks all pairs and anchors reviewed
  values. Source rows 155, 165, 207 and 217 were corrected from visual evidence.
  Printed rows 100 and 148 sum to 27°34′ rather than the stated 27°44′; this
  visible 10-arcsecond source discrepancy is preserved and explicitly checked.
  The printed 18,44,004 result is the only independent Moon output witness.
  The one-based zero-remainder and 3,031-/12,372-day boundary vectors are
  derived from the printed equations and table, and are labelled as derived.
- Printed Cara rule 7 gives the successive exact coefficients 20/1, 16/1 and
  20/3. The rational accumulator preserves partial-segment precision and
  truncates only the final tenth. For a 30-tenth shadow, independent exact
  expectations are −1180 at 75° and −1280 at 90°; vectors also cover 60°,
  180°, 270°, signs, third-segment fractions and near-boundary truncation. The
  printed Example 20 still yields −72 vināḍis. Bhuja/Cara are zero at 0°/180°
  and maximal at 90°/270°.
- The 1962 text lists twelve Bhujaantara rāśi endpoints and asks for a date
  interpolation, but supplies no interpolation equation. Its Kanyā example
  has equal endpoints and does not establish longitude interpolation. The
  current longitude-linear calculation is therefore an experimental project
  convention, not an independently verified historical rule. A complete
  historical engine needs a source equation or an independent nonflat
  date/solar-position witness; neither is available here. The date/location
  pipeline also needs sourced solar position, station shadow, yojana offset,
  half-Cara and civil-date assignment.
- Pai's 2019 eight-page article has 1,027 lines of publisher-extracted text.
  Its p. 546 Saka-1890 ahargana result and p. 547 twelve transit values agree
  with the implemented 1962 arithmetic; its p. 549–550 iteration reports a
  10-vināḍi Mithuna difference and a 2-vināḍi Vṛṣabha difference from the
  historical text. The local PDF download still fails DNS, page screenshots
  return HTTP 502, and the browser host is unavailable. OCR substitutions and
  sign errors remain, so the article is diagnostic evidence only: no value was
  added to runtime data or goldens. See the ledger for page locators and exact
  attempts.
- Current Pambu/Manonmani, Arcot and Srirangam editions are identified, but no
  contemporary computation sheet, corrections, or rights for finite data
  redistribution has been acquired. No modern-edition equivalence is claimed.
- For Thirukanitham, use the bounded toolkit definition described above and
  in the source ledger. Its Rust `astro` 2.0.0 provider compiles on MSVC and
  wasm32, carries the preserved MIT notice, and is independently checked
  against saved JPL DE441 coordinates. The Lahiri/P03 mean-coordinate contract,
  TT/UT1 assumptions, horizon and solar-month assignment are pinned. Chennai
  and Colombo Drik comparisons retain the measured minute-level differences;
  they are not treated as universal publisher errors or compatibility passes.
  Swiss Ephemeris is not a runtime dependency, so its license does not block
  this selected definition. The Thirukanitham golden suite remains planned
  pending separate calendar review.
- Earlier alternative-model research found a MIT/Apache Rust `vsop87` implementation,
  but it covers planetary positions only, lacks the Moon and full apparent
  topocentric pipeline, and its repository is archived. Astronomy Engine is
  MIT and includes lunar/solar events but documents roughly one-arcminute
  accuracy and is C/C++ rather than Rust-native. ERFA is BSD-3-Clause but only
  supplies astronomy transformations. Siderust is Rust-native with VSOP87 and
  ELP2000, but its code is AGPL-3.0; its separate archive is BSD-3-Clause and
  has VSOP/ELP migrations marked pending with dataset-specific terms still to
  check. IMCCE VSOP2013/VSOP87/ELP are primary theory/data leads, but retrieved
  sources did not establish coefficient redistribution terms. Those options
  were not selected; the evaluated MIT `astro` provider is now used for the
  bounded Thirukanitham definition above. The complete contemporary Vakiya
  profile is still unimplemented. No modern Drik values are labelled Vakiya.
- TN official Gazette mastheads bracket the 2025 Thiruvalluvar-year rollover
  (8 January: Margazhi 24/year 2055; 22 January: Thai 9/year 2056), and an
  official Governor's address says Thai 1 was declared Tamil New Year. The
  original order and directly inspected adjacent Thai-1 mastheads, including a
  leap-year case, remain to acquire before activating an era fixture.
- Earlier 2026-only holiday research is superseded by the four bounded annual
  records described below. The Tamil Nadu Gazette viewer exposed the complete
  2025 and 2026 orders, but direct official-host PDF downloads timed out, so
  their API digest is null. Central Bank of Sri Lanka official HTML snapshots
  for 2026/2027 are byte-hashed. Other jurisdictions/years and dataset reuse
  terms remain open; the older SL department PDF fetch failure remains
  irrelevant to these CBSL bank/public/mercantile records.
- Independent SL publisher evidence for Jaffna, Batticaloa, Vanni and
  Up-Country stations; Vakiya other-station horizon calculations; community-
  specific observance precedence; wider versioned TN/SL holiday coverage and
  reuse terms remain open. The three Thirukanitham Rahu/Yamagandam/Kuligai
  periods are implemented from the inspected handbook table and still need
  separate suite activation review.
  Thirukanitham's new UTC phase events use the pinned geocentric provider;
  they do not provide Vakiya phase events or date a religious observance.

The Vakiya civil path is bounded to Ujjain mean sunrise. Bhujaantara needs a
primary interpolation rule or an independently worked non-flat date/solar-
position example before other stations can be supported; longitude-linear
interpolation remains experimental. The edition's inspected geometry pages
also do not establish the geodetic latitude-to-shadow or longitude-to-yojana
mapping needed to join Cara and Deśāntara inputs. These are the exact source
blockers for true local horizon sunrise and arbitrary-location correction.
The bounded Thirukanitham conversion and five-limb path has a named
provider/model, finite domain, independent coordinate and ingress witnesses,
and recorded publisher differences. Its suite still needs separate calendar
review. The remaining full-calendar work includes Vakiya's arbitrary-location
horizon and daylight calculations, the Thiruvalluvar boundary, observance
rules and multi-year TN/SL holiday datasets. These
requirements block full calendar completion, but do not block the implemented
bounded profile operations or the explicitly bounded holiday schedule lookup.

### Earlier numeric integration verification (before the calendar slice)

- `just check-release-policy`, `just release-status`, `just check-unicode`,
  `just check-release-files` and `just sync-release-files` pass. Release status
  remains alpha 4 (`0.1.0-alpha.4` / `0.1.0a4`); no version or channel drift.
  Unicode/schema reports 28,305 active rows and validates the 7,341 planned
  v0.3 rows separately. Canonical projections report 2 ordinal rule sets, 72
  symbols and 19 traditional rules; all 42 generated release copies match.
- `just test-rust`: 32 workspace tests and doctests pass. `just agent-post-edit`
  passes formatting, policy, Unicode/schema, projection, release-copy and
  workspace checks. `just agent-pre-stop-gate` passes Clippy, all 32 Rust
  tests, 121 harness tests, binding rebuild, Python and WASM parity.
- With `TAMIL_GOLDEN_INCLUDE_PLANNED=numerals_v03.jsonl`, real Rust, Python,
  Node, browser-WASM, Dart and isolated archive consumers executed the 7,341
  review-only vectors without changing manifest status. Rust passed all 28,305
  active vectors separately; Python passed 15 tests; Vitest and Dart each
  passed 35,658 tests. Dart analysis reported no issues.
- `just sync-bindings` rebuilt PyO3, Node/browser WASM and TypeScript
  declarations. `pnpm run check:workbench` passes TypeScript and coverage for
  all 60 manifest operations. `pnpm run build:workbench` passes. The first
  build attempt lacked Cargo on that shell's PATH; rerunning with the installed
  Cargo directory added succeeded.
- `just release-check` passes `cargo package`, Python sdist/wheel, npm pack,
  and isolated Rust/Python/Node/browser-WASM consumers. Each runtime consumer
  passed 35,646 total rows (28,305 active plus 7,341 explicitly selected
  planned rows). It recorded 36 local archive digests and performed no
  registry upload or publication.
- No interactive browser test was run. The browser-target module was built and
  its real WASM executed through the browser export in automated tests and the
  isolated consumer; this does not claim an interactive browser UI check.

### Current worktree verification (2026-11-02)

- The default `just agent-pre-stop-gate` passed: formatting, release policy,
  Unicode/schema, generated source copies, workspace check, Clippy, 42 Rust
  tests, 121 harness tests, binding rebuild, 35,646 active Rust golden rows,
  21 Python tests and 35,664 default WASM tests. Calendar rows remain outside
  the active count.
- In the earlier Vakiya-kernel review, six Vakiya JSONL files were explicitly
  selected: Rust executed 97 planned rows alongside 35,646 active rows;
  `just test-parity` passed 21 Python tests and 35,761 Node/browser-WASM tests.
  `just test-dart` passed analysis and 35,756 tests; its output separately
  identified 97 selected planned rows. Those six Vakiya suites remain
  `planned`; the separately added 18-row Thirukanitham suite was not part of
  that run and also remains `planned`.
- `just check-release-policy`, `just release-status`, `just check-unicode`,
  `just check-release-files`, `just sync-release-files` and `just sync-bindings`
  passed. Release status remains alpha 4 (`0.1.0-alpha.4` / `0.1.0a4`); the
  45 generated release files match. Unicode/schema confirmed 35,646 active
  golden rows and validated planned vectors separately.
- `pnpm --dir workbench run check` verified 73 forms. The workbench production
  build passed with Cargo on PATH. `just release-check` passed all six Rust
  package archives, Python sdist/wheel, npm pack, and isolated Rust, Python,
  Node and browser-WASM consumers on 35,646 active rows. It recorded 36 local
  archive digests and performed no registry upload or publication.
- Rebuilt Python/native probes now return Cara `−1180` at 75° and `−1280` at
  90° (old outputs: `−1170`, `−1260`); Moon days 1,601,149 and 1,601,201 now
  return `7 rasi 16°29′07″` / `12°04′` and `6 rasi 14°49′07″` / `12°28′`
  (old outputs: `7 rasi 16°25′07″` / `12°00′` and `6 rasi 15°49′07″` /
  `13°28′`). The Moon day 9,007,199,254,740,993 and local reduction terms
  `(9,007,199,254,740,991, 2, 0)` both now return
  `outside supported calendar coverage`.
- No interactive browser UI test was run; the browser-target WASM was exercised
  through real automated runtime tests and the isolated archive consumer.

### Thirukanitham implementation verification (2026-11-02)

Integrating-agent probes after the frame/boundary repairs confirmed Gregorian
January 1, 7 and 13, 2024 round-trip through Tamil dates in both supported zones;
December 31, 2023 remains rejected. The October 16, 2027 public transition
labels are chronological and use valid rounded day/minute fields. The corrected
ephemeris changes the old near-midnight root, so its original 23:59:44 rounding
case is additionally retained as a direct Rust helper regression. The JPL/ERFA
reference scripts and full-day comparison were inspected: classification uses
raw external coordinates, and the tested event set is not taken solely from
production output. Calendar activation remains pending.

- `calendar_thirukanitham.jsonl` has 18 source-backed exact vectors and remains
  `planned`. With `TAMIL_GOLDEN_INCLUDE_PLANNED=calendar_thirukanitham.jsonl`,
  all 18 passed unchanged in Rust, Python, Node WASM, browser-target WASM and
  Dart. The source-backed daily Drik values are stored separately because the
  publisher snapshot does not provide a full civil-midnight transition table;
  the Rust comparison test records the measured Chennai/Colombo differences.
- The latest `just agent-pre-stop-gate` passed formatting, release policy,
  Unicode/schema, 45 generated release copies, workspace check, Clippy, 62 Rust
  tests (one intentional skip) and doctests, 121 harness tests, rebuilt
  bindings, 35,646 active Rust vectors, 22 Python tests and 35,665 default
  Node-WASM tests.
- The selected-suite `just test-parity` passed all 18 planned vectors in Rust,
  Python and Node WASM, with the 35,646 active Rust rows reported separately.
  `just test-dart` with the same selection passed 35,678 checks; Dart analysis
  reported no issues.
- `just check-unicode`, `just check-release-policy`, and
  `just check-release-files` passed. The workbench check verified 73 forms and
  its production build passed. `just release-check` passed Rust archives,
  Python sdist/wheel, npm pack, and isolated consumers on 35,646 active vectors.
  A second archive review selected 18 planned vectors; the installed Node and
  browser-target WASM packages each passed all 35,664 rows under the Node smoke
  runner. Both archive runs recorded 36 local artifact digests and performed
  no upload. No interactive browser UI test was run.

### Solar arithmetic and daylight continuation (2026-11-02)

Both definitions now expose `tamil_year_info` and `add_tamil_date` through the
shared Rust dispatcher, typed Python/Node/browser WASM/Dart methods, and
workbench. Each year operation returns its twelve computed source-model months;
date arithmetic accepts days, months or years and explicit reject/clamp
overflow. Thirukanitham is limited to its covered solar years and local boxes
(2023–2027 year identifiers, 2024-01-01..2027-12-31 civil dates); Vakiya
enumeration follows the 1962 equation's exposed solar-year domain 1..9999, with
the printed-table lower bound retained for five-limb Moon results. This is not
independent physical validation across those centuries. Seven planned cases
check year information and arithmetic, including Vakiya month overflow.

`calendar_daylight_periods` is implemented for Thirukanitham using the
visually inspected Rao p. 35 weekday table and computed apparent sunrise and
sunset. Its Sunday and Monday Chennai cases return three chronological
daylight intervals to the second. The source PDF hash is
`4716fae5ca5634f9a88be5482e7335e3cbe5bc4df27a31923f2e8946d3e9e750`. The same
operation explicitly errors for Vakiya because the classical source does not
yet define supported local sunset geometry. The 7-row
`calendar_solar_arithmetic.jsonl` and 3-row `calendar_daylight_periods.jsonl`
are planned, as are all other calendar suites. Altogether 139 planned calendar
vectors were selected and passed unchanged through Rust, Python, Node WASM,
browser-target WASM and Dart; numeric v0.3 remains the only owner-approved
activation.

Final verification after these additions: `just agent-pre-stop-gate` passed
formatting, release policy, Unicode/schema, 46 generated release copies,
workspace check, Clippy, 69 Rust tests (one intentional skip), doctests, 121
harness tests, rebuilt bindings, 35,646 active Rust vectors, 24 Python tests
and 35,667 default WASM tests. The selected planned Dart run passed analysis and
35,801 tests. Workbench check verified 77 forms and its production build
passed. `just release-check` with all 139 calendar vectors explicitly selected
passed six Rust archives, Python sdist/wheel, npm pack, and isolated Rust,
Python, Node and browser-target WASM consumers at 35,785 rows; 36 local archive
digests were recorded. No registry upload occurred. No interactive browser UI
test was run. All calendar suite statuses remain planned pending owner review.

### Authority-published holiday schedule continuation (2026-11-02)

- Added `calendar_official_holidays({jurisdiction,year})` through the shared
  Rust dispatcher, Python, Node/browser WASM, Dart and workbench. It returns
  named rows only for TN 2025/2026 and SL 2026/2027: 24, 24, 26 and 25 rows
  respectively. Categories and repeated dates are preserved. The 99 holiday
  facts are canonical in `lexicon/calendar-official-holidays.toml` and compiled
  by `build.rs`; data rows are not derived from religious rules or panchangam
  output.
- Primary evidence: Tamil Nadu G.O. Ms. No. 792 (2025), Extraordinary issue
  375, Annexure PDF pages 1–3; G.O. Ms. No. 708 (2026), issue 721, Annexure
  PDF pages 1–3. The official viewer exposed all 24 rows in each order, but
  direct file acquisition timed out, so those responses expose
  `source_sha256: null`. CBSL 2026 and 2027 pages have local HTML digests
  `5d2c3f0b...e0590c84` and `9071010e...cb09eb9`; independent row-by-row parsing
  confirmed every date, title, and B/P/M category against the local bytes.
  All four schedules report `reuse_terms_status: "unverified"`; this does not
  claim a source license. The schedule contract and page-level source ledger
  record these limits.
- Ten holiday golden cases cover every schedule plus unsupported year,
  invalid jurisdiction, negative/unsafe/fractional years, and extra fields.
  The suite remains `planned`; calendar owner activation is not approved.
- Final gates after the change: `agent-pre-stop-gate` passed 73 Rust tests
  (one intentional skip), 121 harness tests, 35,646 active Rust golden rows,
  and 158 explicitly selected planned calendar rows; Python passed 25 tests,
  and Node plus browser-target WASM passed 35,826 tests. `test-dart` passed
  analysis and 35,821 tests. Workbench check verified 79 forms and its
  production build passed. `release-check` passed six Rust archives, Python
  sdist/wheel, npm packaging and isolated Rust/Python/Node/browser-WASM
  consumers at 35,804 rows; 36 artifact digests were recorded. No package was
  uploaded and no interactive browser UI was tested.
- The full calendar milestone remains open. Next source gates are official
  Tamil Nadu PDF byte acquisition/reuse-term review; a non-flat dated
  Vakiya Bhujaantara worked case plus the latitude-to-shadow and
  longitude-to-yojana rules before any arbitrary-location extension; the
  Vakiya source-defined local sunset; the actual Thai-1 authority for
  Thiruvalluvar era dates; and community-specific observance evidence. Keep
  Ujjain mean-sunrise as the honest Vakiya location scope and preserve every
  unresolved requirement as pending.

### Calendar display, comparison, and era continuation (2026-11-02)

- Added `format_tamil_date`, `calendar_display_info`,
  `compare_calendar_profiles`, and `thiruvalluvar_year_info` in the Rust
  dispatcher and exposed them through Python, Node/browser WASM, Dart, and the
  workbench. The display APIs require a validated profile/date context and
  explicit Tamil/Romanized script, Tamil/Latin digits, and one of two fixed
  templates. Tamil month, weekday, limb, and year-cycle labels are escaped in
  canonical source data; source/license metadata records TVA and CLDR terms,
  MSU weekday transliteration CC BY-NC 4.0, and the independent 1889 cycle
  sequence. Existing Romanized month/limb names are returned unchanged. No
  inflection or holiday-name translation is generated.
- `compare_calendar_profiles` evaluates both named models for one Gregorian
  date or exact UTC instant, returns both contexts, semantic bases, provenance,
  and field differences, and leaves `accuracy_assessment` as `not_assessed`.
  Planned vectors contain one solar-date disagreement, one same-instant
  tithi/karana disagreement, a matching selected-field case, both date-domain
  edges, out-of-domain errors, malformed types, and invalid contexts.
- `tn-thiruvalluvar-thai1-thirukanitham-v1` computes the 31 BCE year numbering
  around the selected Thirukanitham TN Thai-1 boundary for 2025–2027. It is an
  explicit profile convention, not an official year lookup. The official
  Tamil Nadu Gazette issue 2 Part I PDF p. 1 says Jan 14 2026 is Margazhi 30 /
  year 2056; issue 31 PDF p. 1 says Jan 23 is Thai 9 / year 2057. The profile
  starts Thai 1 on Jan 14, so the API returns this known mismatch and
  `official_equivalence: not_established`. The exact official annual boundary
  table remains open. No local PDF digest is asserted.
- Rao *Basics of Panchangam* (2005) pp. 13–18 and 31–32 were inspected for
  sunrise tithi referral, Smartha/Vaishnava Ekadashi variants, Arunodaya and
  Dashami vedha, calculation differences, second-day policy, and Pradosha's
  sunset interval. This review did not establish one source pack for the full
  curated list. The later Nava subset covers only Puthandu, Pongal/Bhogi/Mattu
  Pongal and the Amavasya/Pournami day-selection rule; remaining observance
  families stay pending. Astronomical limb transitions and official holidays
  are kept as separate data/results.
- The display suite has 13 rows, comparison 13, and Thiruvalluvar 10; all
  remain `planned`. The complete selected calendar set contains 197 planned
  rows while the active corpus remains 35,646.
- Final gates passed: `agent-post-edit`; `agent-pre-stop-gate` with all 16
  calendar suites selected (77 Rust tests started, one intentional skip,
  121 harness tests, 35,646 active plus 197 planned Rust rows, 25 Python
  tests, and 35,865 Node/browser-WASM tests); Dart analysis and 35,861 checks;
  83-form workbench coverage/check and production build; policy, Unicode/schema,
  and all 49 generated release-copy checks. `just release-check` passed six
  Rust package consumers, Python sdist/wheel consumers, and installed Node and
  browser-WASM consumers at 35,843 rows; 36 local archive digests were
  recorded. No artifact was uploaded or published. No interactive browser UI
  test was run.

## Scope and next development

Alpha 4 adds the bounded `Vanavil Avvaiyar` (`vanavil-avvaiyar-cid-v1`) 16-bit
code/CID profile alongside the bounded LT-TM / IndoWord 16-bit profile. Byte and CID profiles
do not claim automatic detection or complete historical-font coverage. The
immutable alpha 4 suite has 28,305 rows; the current worktree has
35,646 active rows after owner approval of the 7,341 v0.3 rows. Punarchi work is deferred at
user direction. Preliminary research and its open criteria remain documented
under [the v0.1 source and scope contract](specs/punarchi-v0.1.md). The
contract selects the Nannūl Eḻuttatikāram root text for the first named literary
profile, matching the toolkit's stated merger scope; Tolkāppiyam remains a
separate foundational comparison. The primary edition is A. Thamodaran's 1999
critical edition of the Nannūl root text with Sankara Namasivayar's Viruttiyurai,
corrected by Sivagnana Munivar. Its title page, editorial method, and formatted
HTML viewer text for sūtras 204–205 were inspected; the inspected pages contain
no scan image. Project Madurai's e-text of the Vavilla
1926 edition is retained as a contents/numbering cross-check. The three Nannūl
section ranges are verified. Page-indexed paraphrases, root-number locators,
and first-pass subject ledgers for sūtras 151–203, 204–239, and 240–257 are
recorded in the [Punarchi source notes](specs/punarchi-source-notes.md). These
notes are provisional. When work resumes, exact conditions,
commentary/examples, Tamil grammar review, printed-page mapping, and variant
review remain open.
The TVA viewer provides formatted HTML text, not a scan in the inspected pages;
printed-page mapping and variants still need print-level verification.
Project Madurai's
complete 1926-based Unicode e-text is searchable and linked there; it is a
cross-check, not a duplicate or a replacement for the pinned edition. The
Tolkāppiyam comparison source audit has inspected the 1979 Annamalai
Iḷampūraṇar scan, the 2003 Tamilmann edition, and the 1982 WTRI Puṇariyal
commentary compilation. The 1979 title verso says second edition, August 1979;
it is only a provisional citation witness. A major variant resource is the
1996 *Textual Variation of Tolkappiyam: A Deep Study* (CICT's English catalog
title): its editors collate
manuscript and printed witnesses, but explicitly do not establish one base
reading. Use it as a variant apparatus, not a definitive root-text edition.
Thiagarajar lists a 1992 third edition of Sundaramurthy's Annamalai text;
CICT catalogs a matching 1996 record, but no title-page scan confirms whether
it is revised or reprinted. No sole Tolkāppiyam comparison edition is pinned.
No rule engine or active fixture was added. Existing repositories were
audited as non-authoritative leads; the review found incompatible/unclear
license declarations and upstream issue reports, so no code or data was
reused. The planned suite remains inactive pending rule-level source review
and sourced merger fixtures. A lexical splitter is deferred until its own
lexicon provenance/redistribution review.

Pub.dev/Dart distribution, PostgreSQL packaging, and PDF font extraction
remain deferred. The next active codec research is to compare Vanavil
independently. Punarchi remains deferred with no scheduled restart. When
resumed, obtain and inspect
the Annamalai/Sundaramurthy 1992 third edition or the cataloged 1996 copy, then
compare its title page, preface, and relevant readings with the 1979 witness
and the 1996 variant apparatus. If no later copy is accessible, explicitly
retain 1979 only as a working citation witness. Continue the rule-level Nannūl
audit from sūtra 158 (100 of 107 remain), validate the provisional subject
ledgers, and record exact conditions, commentary, and examples; obtain
print-level pagination and variant evidence. Record citations and variants,
then obtain Tamil grammar review before writing merger fixtures. Keep lexical
splitting deferred until a suitable licensed lexicon is found.
Continue to follow
[development workflow](development.md),
[publishing policy](releases/policy.md), and the agent constitution.

### Local workbench handoff (2026-11-01; retired)

- Status: The developer workbench has been completely decommissioned and removed from the repository (`workbench/`, `tools/check_workbench_operations.py`, and root scripts). A dedicated public playground offering practical tools powered by the toolkit packages is planned for the future; planning and ideation will be handled in a later milestone. The entries below are preserved for historical record.
- Objective: keep the browser workbench aligned with active package operations
  for manual testing. Base commit: `1f1eb23`; workbench implementation:
  `3c03992` on `master`.
- The manual panel now covers all 35 supported active operations. This includes
  the eight LT-TM and Vanavil CID/code and legacy-text directions. Decoders take
  whitespace-separated 16-bit hexadecimal codes or code-valued text and expose
  strict/preserve handling. Encoders accept Unicode text and return either code
  arrays or code-valued text. The intentional `unknown_core_operation` negative
  fixture remains unavailable as a supported operation.
- Currency forms accept decimal amounts such as `1025.50` and convert exactly
  to the existing integer `amount_minor` request. No Rust/API behavior changed.
- Checks: `pnpm run check:workbench` passed; manifest comparison found 35/35
  supported operations; `pnpm run build:workbench` passed (release copies,
  browser WASM, and Vite production bundle); `git diff --check` passed. The
  local Vite page and updated module returned HTTP 200. Browser automation was
  unavailable, so rendered-browser interaction was not checked here.
- The hot-reload server is decommissioned.
- Uncommitted work after saving this handoff: none.

### Punarchi handoff (2026-11-01; deferred)

- Scheduling: further Punarchi work is deferred at user direction. Keep the
  research and resume criteria here; do not treat this source audit as the next
  development milestone. No implementation or active fixture exists.
- Base: `master` at the alpha 3 release source listed above. The source
  contract and notes preserve the preliminary research; current scheduling
  status and resume criteria are recorded here. No rule engine or activated
  suite exists.
- Completed: created the [v0.1 source and scope contract](specs/punarchi-v0.1.md)
  and a [page-indexed source digest, locators, and first-pass subject ledgers](specs/punarchi-source-notes.md)
  for Uyirīṟṟup Puṇariyal 151–203, Meyyīṟṟup Puṇariyal 204–239, and Urupu
  Puṇariyal 240–257 from the TVA HTML edition text,
  selected Thamodaran's 1999 Nannūl critical edition as the primary
  root-text/commentary witness, verified its editorial notes and representative
  sūtras, and verified all three Nannūl section ranges. An earlier draft had
  selected the CICT 1979 Iḷampūraṇar edition for Tolkāppiyam comparison; that
  selection was withdrawn after later publications were found. Follow-up
  source review inspected the 1979, 2003, and 1982 TVA scans plus CICT's 1996
  textual-variation volume. Added a provisional
  root/commentary/example audit for Nannūl sūtras 151–157 from TVA pages
  218–225. Existing implementation leads were reviewed. The suite remains
  planned; no fixtures, code, or external data were added.
- Checks: `git diff --check` completed without whitespace errors;
  `just check-unicode` passed (release policy, Unicode/schema gate with 26,957
  active vectors, and 34 generated source copies).
- Resume criteria: obtain the Annamalai/Sundaramurthy 1992 third edition or CICT's
  matching 1996 cataloged copy and compare its title verso, preface, and
  readings with the inspected 1979 witness. CICT's 1996 *Textual Variation of
  Tolkappiyam: A Deep Study* is now inspected and documented as a rich
  variant apparatus, but its editors explicitly do not establish a single
  base reading. Keep it as a required cross-check, not the root-text authority.
  The 2003 Tamilmann source is a later commentary witness; the 1982 WTRI
  *Puṇariyal Uraivaḷam* is a commentary compilation. The CICT 2025 English
  monograph released in 2026 is a separate interpretation source. Also continue
  the rule-level Nannūl audit from sūtra 158 onward (100 of 107 remain),
  validate the provisional 151–257 subject ledgers, and record each rule's
  exact conditions, commentary, and examples; obtain print-level pagination
  and variant evidence. Only
  then add escaped, sourced merger vectors before implementation. Clarify
  upstream licenses before considering reuse. A lexical splitter remains a
  later milestone with separate lexicon review.
- Checks on the prior documentation pass: `just check-unicode` passed (26,957
  active vectors, planned suites validated separately, 34 generated release
  copies verified); `git diff --check` reported no whitespace errors. The
  source-comparison documentation edits in this handoff still need the gates
  rerun. No Rust code changed.
- Source-selection outcome: 1979 is confirmed as a second edition, August
  1979, and remains only a provisional witness. The 1992 third edition / 1996
  catalog date discrepancy is unresolved because no later title page or
  preface scan was found. The 1996 variant study publishes readings and
  manuscript/print witness discussion, while explicitly declining to establish
  a single base text. No Tolkāppiyam edition is pinned as sole authority. When
  a reviewed Nannūl rule requires comparison, record the exact passage,
  commentary layer, and material variants before deciding its relationship.

### LT-TM codec handoff (2026-11-01)

- The 2003 Tamilmann *Tolkāppiyam* PDF is digitally typeset text using embedded
  `LT-TM-*` font faces; it is not scan-only. The profile consumes 16-bit
  `/Identity-H` codes; ordinary extraction does not return reliable Tamil
  Unicode. Several page-one font runs and the title were checked against the
  rendered page.
- `lexicon/lt_tm.toml` is the canonical, normalized 332-entry mapping
  projection. The build compiles a CID trie and reverse Unicode trie. Rust
  exposes code-array and legacy code-valued text conversion through the shared
  dispatcher, so Python, Node/browser WASM, and Dart use the same engine.
- `tests/golden/codec_lt_tm.jsonl` contains 687 escaped, sourced vectors: all
  mapping entries in both directions plus PDF, normalization, fallback, and
  error cases. The owner reviewed [the profile contract](specs/codec-lt-tm.md)
  and activated the suite; it now counts as parity coverage.
- The source projection is based on the Azhagi+ Portable LT-TM configuration;
  its digest and bundled terms are recorded in the contract. The toolkit MIT
  license does not replace those terms. This is a bounded profile and does not
  establish that every LT-TM/IndoWord font is equivalent. Vanavil, AnuGraphics,
  and Pallavar are not aliases. The profile consumes character code arrays and
  code-valued text directly; PDF document parsing and font detection are outside
  its scope.
- Checks completed: `just agent-pre-stop-gate` passed, including Clippy,
  25 Rust tests, doctests, 115 harness tests, and 27,644 Rust golden vectors;
  Python passed 27,656 cases; Vitest passed 27,654; `just test-dart` passed
  analysis and 27,654 host-FFI fixture tests. `just sync-bindings` rebuilt
  PyO3, Node/browser WASM, and TypeScript declarations. The initial Rust run
  caught a missing final virama in one expected phrase; the fixture was fixed
  and the complete gate rerun passed.
- Broader compatibility with all LT-TM font families remains unverified; do
  not claim Vanavil, AnuGraphics, or Pallavar aliases. This work is
  committed as `3255bd4`.

### Vanavil codec handoff (2026-11-01)

- `Vanavil Avvaiyar` (`vanavil-avvaiyar-cid-v1`) is implemented as an explicit,
  bounded 16-bit code/CID profile (`vanavil_codes_to_unicode`,
  `vanavil_text_to_unicode`, `unicode_to_vanavil_codes`,
  `unicode_to_vanavil_text`) across `tamil-codec`, `tamil-toolkit`, Python,
  Node/browser WASM, and Dart.
- `lexicon/vanavil.toml` is the canonical, normalized 319-entry mapping
  projection derived from the audited Azhagi+ Portable `Vanavil Avvaiyar`
  configuration (`SHA-256: 4948396d50fbbaf251ddfe620ca5d8a0ccdb65b5bef07231065a5d6439754b67`).
  Compared to `lt_tm.toml`, `Vanavil Avvaiyar` transposes `0x00C0..0x00CF` and
  `0x00E0..0x00EF` (`cid ^ 0x0020`), assigns `U+0BFA` (`௺`) to `0x00B7`, and
  omits the 13 `ஶ` (`U+0BB6`) entries (`332 - 13 = 319` mappings).
- `tests/golden/codec_vanavil.jsonl` adds 661 escaped, sourced golden vectors
  (638 mapping decode/encode vectors plus 23 phrase, transposition, `ஶ`
  rejection, NFD normalization, joiner-boundary, and error-policy vectors),
  bringing the active golden corpus to 28,305 rows.

### PDF extraction status (2026-11-01; deferred / removed)

- Per user direction, the private developer utility `tools/tamil-pdf-extract/`
  and exploratory PDF/OCR test artifacts were removed from the codebase.
- PDF font inspection and document extraction remain deferred.
- The LT-TM CID profile in `tamil-codec` remains intact, active, and fully
  tested with its 687 golden vectors.

Never put registry credentials in the handoff, repository, build artifacts, or
chat. Do not claim complete linguistic support from the bootstrap suites.

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
