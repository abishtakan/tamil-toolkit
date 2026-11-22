# Changelog


## Unreleased

- **Orthographic Visual-Kombu Repair Fix (`tamil-norm`):**
  - Fixed `repair_tamil_text` in `crates/tamil-norm/src/repair.rs` so attached `ெ`/`ே`/`ை` (`\u0BC6`/`\u0BC7`/`\u0BC8`) after a bare consonant is never misclassified as a visual left-kombu before the following consonant (fixing false-positive `1 visual kombu` warnings and text corruption on words like `பல்கலைக்கழகம்`, `சென்னை`, and `வேலை`), and avoided misreading `ெ + C + ள + vowel_sign` as `ௌ`.
  - Updated browser extension `inspect-tab.ts` and `content/index.ts` to support in-place manual repair and reset rolling live-typing state on replace/insert.
- **Anjal & Phonetic Keyboard Mapping Fix (`tamil-translit`, `lexicon/translit.toml`):**
  - Moved `anjal-phonetic` and `phonetic-v1` input rules into declarative tables in `lexicon/translit.toml` compiled via `crates/tamil-translit/build.rs`.
  - Fixed lowercase `s` -> `ச` (so `se` produces `செ`, `selvam` -> `செல்வம்`, `sennai` -> `சென்னை`) while uppercase `S` maps to Grantha `ஸ` (`Se` -> `ஸெ`) and `sk` maps to `ஸ்க`.
  - Separated Murasu Anjal `ee`/`oo` (`ஏ`/`ஓ`) and `w`/`W` (`ந`/`ன`) from Tanglish `phonetic-v1` `ee`/`oo` (`ஈ`/`ஊ`) and `w`/`W` (`வ`), added homorganic clusters (`nd` -> `ண்ட`, `ndr`/`nR` -> `ன்ற`, `nt`/`nth`/`ndh` -> `ந்த`, `ttr`/`rr` -> `ற்ற`, `ngg`/medial `ng` -> `ங்க`, `njj`/medial `nj` -> `ஞ்ச`, `x`/`ksh` -> `க்ஷ`), uppercase consonant support, positional `ந` -> `n` in `phonetic-v1` `to_latin`, and `n-`/`n_` support in browser-extension live typing.
- **Native-Themed Chrome/Edge & Firefox Browser Extension (`integrations/browser-extension/`):**
  - Added dual-target Manifest V3 browser extension for Chrome/Edge (`dist/chrome`, 1.46 MiB zipped) and Firefox (`dist/firefox`, 1.45 MiB zipped + reproducible AMO source bundle) powered offline by the canonical slim Apache-2.0 `tamil-toolkit` Rust/WASM engine with zero install-time `host_permissions` and the canonical Aytham (`ஃ`) icon.
  - Supports **Live Inline Tamil Typing** (`Alt+Shift+L` shortcut + compact native toolbar popup with 1-click Side Panel launcher, `த` badge, caret-anchored word-boundary preview for Phonetic/Anjal and instant per-keystroke commit for Tamil99/Bamini, focus-aware Shadow DOM floating pill, sensitive-field exclusion, canvas Quick-Compose fallback, and opt-in per-site Always-on).
  - Supports **Live Document & Selection Tamil Inspector** (real-time streaming updates, true Tamil letter count, word count, Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, Unicode health check with 1-click in-place repair, and optional live micro-counter), **Fix Text** (7 legacy codecs + Auto ambiguity guard, joiner-preserving repair, *Agara Varisai* / *Uyirmei-first* sorting, right-click silent copy, editable in-place repair & cold-start handoff), **Tools** (TN/SL numerals & INR/LKR currency words, active civil date + official TN/SL holidays, opt-in per-site Noto Tamil font fixer), bilingual `தமிழ் / EN` UI, and native Chrome Refresh 2023 / Firefox Acorn themes.

## 0.1.0-alpha.9 / Python 0.1.0a9 - 2026-11-22

- **SEO & AI/LLM discoverability (`llms.txt`, prerendered Playground routes, registry metadata, Word support page):**
  - Added canonical root `llms.txt` and `playground/public/{llms.txt,robots.txt,sitemap.xml,og-card.svg}` targeting `https://tamil-toolkit-playground.vercel.app/`, plus build-time prerendering in `playground/vite.config.ts` (`playground/src/lib/seo-pages.ts`) for 7 clean `/tools/<slug>/` landing pages with unique titles, meta descriptions, canonical URLs, Open Graph tags, and semantic HTML fallback before React/WASM hydration.
  - Updated `playground/src/App.tsx` and `playground/src/lib/tools.ts` to navigate via real `<a href>` links with `pushState` while preserving `?tool=` bookmarks, and unified `document.title` / `<meta description>` / `<link rel="canonical">` ownership.
  - Added validated `keywords` (<=5) and `categories` to all 9 public `crates/*/Cargo.toml` manifests, enriched `bindings/python/pyproject.toml` and `bindings/js-wasm/package.json` descriptions/keywords/homepage URLs, updated `README.md` to lead with the all-in-one Rust/WASM Tamil linguistic core and multi-package-manager parity (removing the keyword-stuffing block), fixed broken integration doc links in `HyphenatorTool.tsx`, added `noindex` to the Word taskpane (`integrations/office-word-addin/index.html`), and expanded `integrations/office-word-addin/support.html` as the public Word Add-in landing page.
- **License migration (`MIT` → `Apache-2.0` + `NOTICE`):** Relicensed all
  original `tamil-toolkit` code, crates, bindings, Playground, and Word Add-in
  under **Apache License 2.0** (`LICENSE`) with a root **`NOTICE`** file
  crediting creator **Abishtakan Sivachandrathevan and tamil-toolkit
  contributors** (`https://github.com/abishtakan/tamil-toolkit`) plus all
  upstream datasets, standards, and references. Updated `release_files.py`,
  `release_policy.py`, `release.py`, `lexicon_dart_archive.py`, all crate/npm/
  PyPI manifests, and synchronized `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`,
  and crate `README.md` across all 9 public crates and 3 bindings (151 synced
  files). Third-party dataset licenses (Wiktionary CC-BY-SA-4.0, Unicode-3.0,
  upstream MIT/CC references) remain preserved.
- **Playground & Microsoft Word Add-in (Phase 6, 7B & 8 parity):**
  - Updated `playground/` (`CodecConverter.tsx`, `pdf-extract.ts`, `NumeralFormatter.tsx`, new `TranslitTool.tsx`, `tools.ts`, `App.tsx`, `i18n.ts`) to expose all 12 legacy codecs + Bharathi Tamil Braille (with PDF font hinting for Senthamil, Shree-Tam, Softview, and TBO), all 8 currencies (`INR`, `LKR`, `SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`), colloquial `mixed_fraction_to_words`, formal `words_to_number` (ITN), and a dedicated **Transliteration & Tamil99** tool covering all 8 `tamil-translit` schemes (`iso-15919`, `madras-lexicon`, `itrans`, `harvard-kyoto`, `phonetic-v1`, `tamil99`, `anjal-phonetic`, `suratha-bamini`).
  - Updated `integrations/office-word-addin/` (`src/lib/tamil-engine.ts`, `index.html`, `src/taskpane.ts`, slim MIT WASM rebuilt) to support Senthamil, Shree-Tam, Softview, TBO, and Bharathi Braille conversion, all 8 currencies + `words_to_number` (ITN) in the Insert tab, and a **Transliteration & Tamil99 Composer** drawer in the Type tab.
- **Phase 8 (`tamil-translit` v0.1):** Create Rank 2 crate `crates/tamil-translit`
  (`#![forbid(unsafe_code)]`, depending only on `tamil-core` and `tamil-norm`),
  declarative uniform UTF-8 Tamil table `lexicon/translit.toml`, and
  `docs/specs/translit-v0.1.md`. Implements lossless bidirectional scholarly
  romanization (`iso-15919`, `madras-lexicon`, `itrans`, `harvard-kyoto`) plus
  deterministic offline keyboard & phonetic input (`tamil99` with auto-pulli
  gemination & homorganic nasal+stop rules, `anjal-phonetic`, `suratha-bamini`,
  and `phonetic-v1`), backed by 522 active golden vectors
  (`tests/golden/translit_v01.jsonl`), `transliterate` / `transliterate_schemes`
  dispatcher ops, `release-policy.toml` / `release_files.py` integration, and
  full Rust/Python/WASM/Dart parity.
- **Uniform UTF-8 Tamil in `lexicon/*.toml` (Constitution 3.0.0):** Migrated all
  canonical `lexicon/*.toml` rule tables and their 10 generator scripts onto a
  shared formatter (`tools/toml_utf8.py`): literal NFC UTF-8 Tamil (UTF-8 no
  BOM, LF endings) for complete Tamil letters, attached marks, digits, and
  signs, while keeping detached Tamil combining marks, Braille
  (`U+2800..U+28FF`), Tamil Supplement (`U+11FC0..U+11FFF`), and controls
  explicitly escaped. Added TOML-aware enforcement to `check_source_unicode.py`,
  added `tests/harness/test_toml_utf8.py`, added `just check-release-files`
  ahead of `sync-release-files` in `.github/workflows/ci.yml`, and synced all
  135 release copies with 100% parsed-object equality. Golden JSONL remains
  escaped.
- **Phase 7B (`tamil-codec` — Senthamil, Shree-Tam, Softview, TBO & Bharathi Braille):**
  Add 4 new 16-bit CID legacy font profiles (`senthamil-cid-v1`, `shree-tam-cid-v1`,
  `softview-amudham-cid-v1`, `tbo-tboomi-cid-v1`) and Grade 1 Bharathi Tamil Braille
  (`bharathi-tamil-g1-v1`, `unicode_to_braille` / `braille_to_unicode`, `U+2800..U+28FF`)
  backed by `lexicon/{senthamil,shree_tam,softview,tbo,braille}.toml`,
  `docs/specs/codec-phase7-legacy.md`, `docs/specs/codec-braille.md`, 2,694 active
  golden vectors (`codec_phase7_legacy.jsonl`, `codec_braille.jsonl`), and full
  Rust/Python/WASM/Dart parity (completing Phase 7).
- **Phase 7A (Playground client-side PDF text-layer extraction):** Add 100%
  client-side, zero-upload `pdfjs-dist` text-layer extraction in
  `playground/src/lib/pdf-extract.ts` and wire **Import PDF** into
  `CodecConverter.tsx` with embedded PDF font-family profile hinting (Bamini,
  Vanavil, LT-TM, TSCII, TAB, TAM, Anjal) and explicit warnings for scanned
  image-only PDFs (no OCR). Record Phase 7 provenance/licensing status for
  queued legacy font tables (Senthamil, Shree-Tam, Softview, TBO) in
  `docs/specs/codec-roadmap.md`.
- **Phase 6 (`tamil-numerals` v0.4):** Add diaspora currency support (`SGD`,
  `MYR`, `USD`, `EUR`, `GBP`, `CAD` with 3-3 international grouping and Tamil
  major/minor labels in `lexicon/numerals-v04.toml`), colloquial Tamil
  mixed-fraction words (`mixed_fraction_to_words`, e.g., `ஒன்றேகால்`,
  `இரண்டரை`, `ஆயிரத்தரை`, `ஒரு கோடியரை`), and exact formal reverse
  word-to-number parsing (`words_to_number` ITN over `-999,999,999..=999,999,999`
  for `TN` and `SL`), backed by `docs/specs/numerals-v0.4.md`, 739 active
  golden vectors (`tests/golden/numerals_v04.jsonl`), CLI `numerals parse`
  support, and full Rust/Python/WASM/Dart parity.
- Upgrade the Microsoft Word Office.js Add-in (`integrations/office-word-addin/`,
  Spec 014) to **Tamil Toolkit (`v2.2.0.0`)** as an AppSource-ready, 100%
  client-side Fluent 2 utility suite powered by the slim MIT default-profile
  Rust/WASM build (~1.37 MB gzipped), retiring the standalone JS `engine.js`
  duplicate. Adds a 3-tab Fluent 2 Taskpane (**Type**, **Prepare**, **Insert**)
  with Light/Dark Office theme sync, `தமிழ் / EN` UI toggle, Direct Live
  Bamini Word Typing, legacy font conversion + Unicode font reassignment,
  orthographic repair, Tamil-aware Find & Replace, *Akara Varisai* paragraph &
  table sorting, numerals/currency words & traditional symbol palette, Tamil
  Calendar & Panchangam stamps, OOXML formatting-preserving hyphenation, and
  Document Inspector, plus expanded `தமிழ்` Ribbon commands, `privacy.html` /
  `support.html`, `icon-64.png`, AppSource submission kit (`release/`),
  configurable production manifest generator (`ADDIN_BASE_URL` ->
  `manifest.prod.xml`), and static hosting headers (`vercel.json`, `_headers`).
- Redesign the Playground UI/UX (`playground/`) into a cohesive, human-centered
  Tamil language workbench: replace the three-tier tab/sub-chip navigation with
  a single persistent left sidebar (plus mobile drawer), quick-filter search
  (`/` or `Ctrl/Cmd+K`), and URL query synchronization (`?tool=<id>`).
- Add an editorial Home masthead with instant dictionary lookup and quick-start
  tasks; align typography (clean sans UI chrome with Tamil serif reserved for
  headwords, prose, dates, and classical numerals); flatten repetitive badges,
  heavy shadows, and latency clutter; fix blank initial outputs; fix
  `CopyButton` check-icon contrast on light buttons; and guard PWA service worker
  registration during Vite development (`import.meta.env.DEV`) to prevent stale
  cached UI bundles on `localhost`.
- Expand Playground feature parity to cover the full Rust/WASM capability set:
  - `NumeralFormatter`: 4-tab layout (`Currency & Words`, `Traditional & Digits`,
    `Fractions, Percents & Ranges`, `Dates & Date Math`) with independent
    currency (`INR`/`LKR`) and locale (`TN`/`SL`) selectors so Sri Lankan
    Rupee (`LKR`) and `SL` wording are directly selectable.
  - `CalendarExplorer`: 4-tab layout (`Daily Panchangam & At-Time`, `Convert &
    12-Month Year`, `Observances, Holidays & Phases`, `Thirukanitham vs Vakya`)
    with TN/SL city presets, day steppers, reverse Tamil-to-Gregorian
    conversion, Tamil date arithmetic, `panchangam_at(HH:MM)`, limb transitions,
    `TN`/`SL` official holidays, lunar phase events, and side-by-side
    `compareCalendarProfiles`. Computes only the active tab lazily and runs
    heavy `tamil_year_info` and `calendar_observances` calls off the UI thread
    in `playground.worker.ts` with caching and explicit `TN` observance scope
    when an `SL` city is selected.
  - `CodecConverter` & `playground.worker.ts`: single-byte Latin-1 encoding for
    8-bit legacy encodings (`TSCII`, `TAB`, `TAM`, `Anjal`), Hex byte
    inspection/round-trip mode, `Preserve`/`Strict` error policy toggle for
    `Bamini`/`Vanavil`/`LT-TM`, and clickable `detect_encoding` candidates.
  - `LetterAnalyzer`, `TextSorter`, `SymbolsExplorer`, `ScalarInspector`,
    `CodeGenerator`, and `DispatcherSandbox`: interactive `compose_uyirmei`
    builder (18 Mei × 12 Uyir), `get_olippasai` & `are_cognates`, pairwise
    `compare` & collation/folded search keys, live `symbol_info` &
    `fraction_symbol` builder, structural `inspect_tamil_string` view, 7
    snippet categories (`TypeScript`, `Python`, `Rust`, `Dart`), and 13
    dispatcher presets.
- Add public-beta build mode (`pnpm --filter tamil-toolkit-playground build:beta`,
  `playground/build-beta.mjs`, `tools/prepare_playground.py --public-beta`, and
  `VITE_PUBLIC_BETA=1`) that excludes unresolved `historical-lexicon` assets
  from `playground/dist/`, disables the `Historical Archive` UI mode via
  `IS_PUBLIC_BETA` / `resolveLexiconViewMode`, code-splits Playground routes via
  `React.lazy` in `App.tsx`, and eliminates the Vite `worker-client.ts` dynamic
  import warning.
- Bundle self-hosted Tamil and Tamil Supplement webfonts
  (`@fontsource/noto-sans-tamil`, `@fontsource/noto-serif-tamil`,
  `@fontsource/noto-sans-tamil-supplement`) in `playground/src/index.css` and
  precache `.woff2` assets in `playground/vite.config.ts` so traditional Tamil
  signs (`U+0BF0`–`U+0BFA`) and Tamil Supplement glyphs (`U+11FC0`–`U+11FFF`)
  render reliably on mobile browsers without system font support.
- Verify with `pnpm --filter tamil-toolkit-playground test` (20 files, 124
  tests), `pnpm --filter tamil-toolkit-playground build:beta` (`tsc --noEmit` +
  public-beta Vite production build), and
  `uv run --locked python tools/tasks.py check-unicode`.

## 0.1.0-alpha.8 / Python 0.1.0a8 - 2026-11-20

- Add historical source-record search to the playground. The export indexes all
  307,243 supplied rows under 177,606 lookup keys and preserves original cells,
  duplicates and file/row locators. The separate data ZIP carries unresolved
  source rights and unverified linguistic claims. Core runtime parity, Dart,
  the production playground build and all 256 bucket hash comparisons pass.

- Merge seven freshly sourced Wiktionary entries (nine senses) into the core
  while preserving all existing entry revisions and reviewed golden payloads.
  Full data coverage becomes 9,410 written forms / 11,377 entries / 25,742 senses.
  Rust, Python, Node/browser WASM and Dart checks pass with seven new cases
  explicitly reviewed as planned; owner fixture activation remains pending.
- Capture 384 pinned Wiktionary pages as rendered HTML for the remaining gaps,
  retaining current-template provenance and hash/queue bindings. Produce a
  pending human/source-policy review packet of 237 entries / 282 senses, with
  228 candidate spellings absent from the current packs. Derived proposals
  cannot enter the existing wikitext automated-acceptance path.
- Record full-bundle source/permission blockers and local permission-request
  drafts. Preserve the 307,243 historical records; no unverified data approval,
  version bump or registry publication is claimed.

- Reconcile all 410 historical Wiktionary spelling gaps against pinned pages
  and a separate official API capture. Prepare an isolated seven-entry,
  nine-sense candidate pack with source-backed automated provenance and passing
  canonical/CLDF validation; retain explicit blockers for the remaining cases.
  Validate snapshot dates without changing the previous bulk extraction policy.
  The isolated packet was subsequently merged as recorded above; historical
  quarantine remains unchanged.

- Audit the historical 307,243-record lexicon by source and exact spelling
  overlap, with a reproducible inventory and a prioritized recovery queue.
  Separate candidate counts from approved coverage; historical claims remain
  quarantined and original source hashes remain unchanged.

- Add a bilingual full-pack lexicon playground with exact lookup, pack and scope
  filters, homographs, all senses, source/acceptance details, attribution links,
  JSON exports and contract-test presets. Dev/build prepares optimized full browser
  WASM with manifest-checked coverage; disclose historical intake exclusions.
  All89playground tests, production/PWA build and post-edit gates pass; desktop
  and mobile browser flows verified. Open `/?tool=lexicon` for direct access.

- Share fingerprinted, read-only real-pack harness fixtures and run isolated
  tests with pytest-xdist; retain all original tests and add cross-process lock,
  cache invalidation and fixture mutation checks. The optimized harness passes
  484 tests in 64.25 seconds (baseline: 447 in 1,130.88 seconds).
- Add bounded host Rust/PyO3 batches for lexicon scalar audits, exact JSON
  encoding and hashes; retain reference fallbacks and genuine offline CLDF
  validation while reusing parsed rows within each validation call. Detect
  cyclic containers and preserve dictionary-subclass fallback behavior.
- Build independent bindings concurrently with isolated Cargo targets,
  content/output-verified caches, disk preflight and process leases. Keep daily
  gates on one selected profile and expose the final three-profile runtime and
  archive matrix explicitly. All three runtime/archive profiles pass; the core development profile is restored.
  Structural benchmarks remain within budget without a measured net throughput gain.

- Avoid quadratic decision indexing during lexicon Unicode inspection: load
  review decisions only when an actual Unicode exception needs authorization,
  retaining native inspection and exact exception/revision/history checks.
  Reuse the shared compiled schema validator for review eligibility, with
  differential checks against the reference validator.

- Correct revision-pinned bulk Wiktionary homograph identities, source-backed
  regional routing and finite qualifier classification. Regenerate three packs
  containing 11,370 entries / 25,733 senses while preserving the six reviewed
  entry payloads. Add full-profile verification and refresh signed pack test
  metadata; expanded integration and archive acceptance remain in progress.

- Close Feature 021 lexicon remediation (`T071`–`T079`): preserve canonical
  sense-anchored relations and full closure through CLDF export/round-trips,
  align Python/Rust validation of optional `unknown`/`not_applicable` scope
  backing and `paired_translation_id` references, apply cross-pack relation
  omission before public-only checks while retaining editorial integrity checks,
  and optimize full-corpus `307,243`-record / `12`-file lossless structural
  ingestion and proof validation to `45.99s` / `387.39 MiB` (`45.99s` / `383.33 MiB`
  repeat), with warm core lookup p95 at `1.2445 ms` native / `1.478 ms` serialized.
  Independent review (`gemini-4-hydrogen`, `high`) and full Rust/Python/WASM/Dart/archive
  gates pass; Cargo default data features and core 6-entry manifest remain preserved.

- Add deterministic optional dictionary compilation and exact Rust lookup with
  dispatcher/CLI routes. All 16 feature combinations pass compiler checks;
  the default embeds no payload and clean core builds reproduce 50,923 bytes.
  The six-entry / 19-sense core passes 44 unchanged lookup cases, activated
  for the core profile with owner approval on 2026-11-15.
  Core/default real runtime parity and isolated archive checks pass.
  Full 307,243-record structural validation passes in 52.72 seconds /
  191.93 MiB. Release lookup p95 is 0.1148 ms native / 0.1979 ms serialized.
  Cargo default data features, crate/version/registry scope remain unchanged;
  no publishing is authorized.

- Implement nonempty release closure, deterministic canonical promotion with
  source notice/path validation, expanded review ingestion, and offline CLDF 1.3
  dictionary export/round-trip using pinned dev validators and local schemas.
  The approved six-entry core reproduces byte-for-byte; compiled runtime and
  archive/profile acceptance are verified.

- Record genuine owner approval of six revision-pinned Wiktionary entries / 19
  senses and the separate CC-BY-SA-4.0 data-pack policy; build a reviewed
  workspace with 31 accepted claims while preserving pending scope proposals,
  immutable originals and distinct same-spelling POS identities. Canonical
  notice closure, compiled packs and bounded runtime acceptance are verified.

- Create isolated pending 4-entry PRIMARY Wiktionary candidate workspace under
  `data/curation/wiktionary-candidate/` pinned to verified official
  `en.wiktionary.org` revisions (`1921` அடடா `oldid=85842017`, `3906` அந்நிலை
  `oldid=89903937`, `8218` அறிக்கை `oldid=88382210`, `28857` செப்பம்
  `oldid=61485513`) with checked-in API/wikitext snapshots, proposed
  `CC-BY-SA-4.0` attribution/disclaimer notices (`notices/ATTRIBUTION_AND_LICENSE.md`),
  allowlist builder/verifier (`tools/lexicon_wiktionary_candidate.py`),
  `4` entries / `16` senses / `24` assertions (`0` accepted decisions, `49` open
  findings, `0` IPA forms, explicit exclusions & schema-gap manifests in
  `provenance/`), focused negative/replay tests
  (`tests/harness/test_wiktionary_candidate.py`), rebuild guards that reject
  protected paths and preserve conflicting editorial changes, and audit record
  (`docs/audits/wiktionary-candidate-2026-11-14.md`); immutable 12 original
  sources, 739-record `data/curation/tamil-lexicon/`, `T038`, `T039`, and
  `T040+` pending gates remain unchanged.

- Complete Feature 021 structural curation slice (`T001`–`T037`) and L2
  structural pilot acceptance under the `json-string-utf8-v1` storage decision
  (readable UTF-8 Tamil in large dictionary CSV with reversible JSON/control
  escapes, escaped golden tests/scalar diagnostics, and no retained legacy
  staging/archive):
  - Verify all 12 immutable intake files (`307,243` logical CSV records) and
    pre-projection clean inventory/stage replay (`263,014` initial identities,
    `504,384,984` UTF-8 CSV bytes vs `581,570,653` escaped baseline;
    `target/lexicon/us1-proof.json`) plus exact decoded source field/scalar and
    subject allocation equality (`target/lexicon/source-content-proof-final.json`).
  - Project and validate the deterministic 739-record structural pilot (`264,402`
    post-projection identities, `243` entries, `609` forms, `363` senses, `637`
    texts, `1,458` scopes, `51` labels, `310,329` assertions/evidence, `966`
    findings, `0` decisions/eligible assertions): structural CLI exits `0`
    (`l2_structural_accepted: true`, `target/lexicon/structural-final.json`),
    fail-closed release guard exits `1` (`NONEMPTY_ELIGIBLE_PACK_REQUIRED`,
    `target/lexicon/release-rejection-final.json`), and L2 acceptance is
    recorded in `target/lexicon/l2-acceptance.json` and `target/lexicon/us2-proof.json`.
  - Pass `just agent-post-edit` and full `just agent-pre-stop-gate`
    (`target/lexicon/pre-stop-utf8-final-retry.log`: `277` harness tests,
    `36,161` Rust active goldens, `30` Python golden groups, `36,185` WASM tests).
  - Unblock Phase 6 numerals scheduling at L2; primary dictionary provenance
    trace (`T038`), genuine review decisions (`T039`), L3 nonempty pack/CLDF
    production, and L4 runtime lookup (`runtime_verified: null`) remain pending.

- Resolve Feature 021 analysis findings: keep the structural pilot's tests
  executable before later release/export tooling, define the full nested lookup
  response schema and illustrative example, and specify full-corpus structural
  timing/memory measurements separately from lookup benchmarks.

- Validate reused Rust APIs across `tamil-core`, `tamil-norm`, and
  `tamil-toolkit` ahead of Feature 021 (`specs/022-validate-reused-rust-apis`):
  - Add 30 escaped canonical NFC/NFD, CCC mark reordering, format-control
    barrier, Shri distinction, malformed-sequence, `inspect_tamil_string`, and
    NFD-folding/repair golden vectors in `tests/golden/norm_canonical.jsonl`
    registered in `tests/golden/manifest.json`.
  - Add `proptest` (`10,000` cases per run) and 23-consonant Tamil/Grantha NFD
    sweep tests in `tamil-norm`, confirming NFC/NFD correctness and identical
    `fold_for_search` / `repair_tamil_text` outputs on canonically equivalent
    NFC and NFD inputs.
  - Lock Feature 021 reused `tamil-core` primitive contracts (`get_letters`,
    `Letters`, `split_uyirmei`, `compose_uyirmei`, `classify_quantity`,
    `baseline_maathirai`, `get_cognate`, `are_cognates`, `get_olippasai`, and
    `inspect_tamil_string`).
  - Sync `tamil_toolkit::OPERATIONS` with all operations handled by
    `execute()` (adding 9 missing active operation names) and fix `tamil-toolkit
    norm fold --profile <value>` to fail loudly on unknown profiles and handle
    flag order before or after `<TEXT>`.
- Generate 70 dependency-ordered Feature 021 tasks with independently testable
  stories, an executable structural-pilot slice, explicit later source/review
  gates, and separate runtime, activation, and archive acceptance.
- Plan Feature 021's offline lexicon curation, evidence/review model, structural
  pilot, approved optional packs, exact lookup, and validation workflow; add
  research, data-model, interface, packaging, and quickstart design artifacts.
- Clarify that the structural lexicon pilot can unblock numerals with zero
  release-eligible content; approved data and verified runtime gates remain
  separate requirements for lexical consumers.
- Define lexicon regional filters to include attested regional matches and
  reviewed unrestricted entries, excluding unknown geographic coverage.
- Define lexicon exact lookup using NFC canonical equivalence, preserving
  original spellings and format controls without repair or lossy folding.
- Clarify lexicon review eligibility: automate acceptance of unchanged,
  source-verified content while requiring human decisions for corrections,
  inferred annotations, and ambiguous cases.
- Specify Feature 021 lexicon curation and prioritize its reviewed pilot before
  new numeral extensions. Align the main roadmap, canonical architecture, and
  Feature 016 with separate provenance, curation, data-pack, and runtime gates;
  preserve existing phase numbers and dependency ranks.

- Audit the supplied lexicon across all CSV rows, primary references, Unicode,
  native Rust count comparisons, and the supplied FST. Record editorial,
  provenance, homograph lookup, and reproducibility gaps and a curation plan;
  preserve every original source file.

- Relocate the user-supplied lexicon source bundle to
  `data/sources/tamil-lexicon/`, preserving all 12 files and recording SHA-256
  checksums. Data review and runtime integration remain pending.

## 0.1.0-alpha.7 / Python 0.1.0a7 - 2026-11-08

- Repair baseline validation blockers: preserve dictionary joiner patterns using explicit Unicode scalars, cover both controls, apply Rust formatting, resolve unused-variable/iterator warnings, and align the release acceptance test with the existing private hyphen exemption.

- Spec 016: document dependency ranks, capability boundaries and 18-phase roadmap; enforce Cargo dependency DAG ranks across runtime, build, dev and target tables, including aliases. Reject manifest-free future-crate directories and varied placeholder sources; define lifecycle evidence and reconcile the release handoff.

- Remove the developer workbench (`workbench/`), its operation coverage check (`tools/check_workbench_operations.py`), and associated npm scripts and workspace configuration.

## 0.1.0-alpha.6 / Python 0.1.0a6 - 2026-11-05

- Extract calendar modules, astronomical calculation engines (Vakiya and
  Thirukanitham), and ephemeris tables from `tamil-numerals` into the dedicated
  internal workspace crate `tamil-calendar`.
- Remove the `astro = "=2.0.0"` dependency and all calendar modules from
  `tamil-numerals`, leaving it strictly focused on numbers, currency, and date
  formatting with zero backward-compatibility shims or stubs.
- Re-export calendar APIs via `tamil-toolkit::calendar` and provide sub-namespace
  access across language bindings: `tamil_toolkit.calendar` in Python,
  `api.calendar` in WebAssembly/TypeScript, and `TamilCalendar` in Dart.
- Add developer workbench support for `tamil-calendar` with a dedicated package
  card and operations in `workbench/main.ts`.

## 0.1.0-alpha.5 / Python 0.1.0a5 - 2026-11-02

- Publish the reviewed Rust crates, npm package, and PyPI distributions from
  the immutable CI artifacts; tag v0.1.0-alpha.5 points to the reviewed source.
  Fresh public Rust, Python, and npm consumers passed all active golden vectors.
  Numeric v0.3 remains approved; calendar APIs remain experimental and planned.
  See docs/releases/alpha-5.md for publisher runs and digests.

- Extend the still-planned TN Thirukanitham observance pack with bounded
  source-named selector work for Sankatahara Chaturthi, Sivarathri, Thai Poosam,
  Panguni Uthiram, Chitra Pournami, Vaikasi Visakam, Aadi Perukku, Vinayaka
  Chaturthi, Navaratri/Ayudha Puja/Vijayadasami, Tamil Deepavali, Karthigai
  Deepam, and Arudra Darshan. Krishna Jayanthi is excluded from the alpha.5
  event inventory because annual festival-month selection lacks a sourced
  contract; historical helper output is not a supported selector. All
  observance fixtures remain planned; no universal festival schedule or Vakiya
  date equivalence is claimed, and broader community variants remain pending.

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
