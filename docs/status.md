# Project handoff

## Release `0.2.0` Published (2026-11-26)

- **Published registries (`v0.2.0`, feature source commit `babc5840bae618e5981995c24b0183304340c30a`, release commit `4af1cc32b5d9d31b52aefc0729e1c8f7d8c73e3f`, artifact run [`45789325971`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45789325971) — 14/14 jobs green):**
  - **crates.io** ([run `45790043541`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45790043541)): all 10 slim `Apache-2.0` crates (`tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`, `tamil-calendar`, `tamil-codec`, `tamil-hyphen`, `tamil-translit`, `tamil-tokenize`, `tamil-toolkit`) published at `0.2.0`.
  - **npm** ([run `45790267117`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45790267117)): `tamil-toolkit@0.2.0` published via OIDC (`latest` dist-tag pointing to `0.2.0`; SHA-256 `e9d924ddc4bef6f914e50b7957574606eadb0b2af502742dda7609fd4e95b53c`).
  - **PyPI** ([run `45790379993`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45790379993)): `tamil-toolkit 0.2.0` published via OIDC (Linux, Windows, macOS abi3 wheels + sdist recorded in [`docs/releases/v0.2.0.md`](releases/v0.2.0.md)).
- **Release highlights:**
  - First public release of `tamil-tokenize` (`0.2.0`, Rank 2, `Apache-2.0`, `#![forbid(unsafe_code)]`) with `tokenize_words` / `segment_sentences` across Rust, Python, TypeScript/WASM, and Dart, 54 active golden vectors (`40,265` active vectors total), and the Playground Tokenizer tool.
  - Full pre-release verification (`just agent-pre-stop-gate`, `just test-dart`, `default`-profile Rust/Python/npm/Dart archives) passed on `babc584`; see [`docs/releases/v0.2.0.md`](releases/v0.2.0.md).

## Phase 9 (`tamil-tokenize`) activated and integrated (2026-11-26)

- **Scope (`crates/tamil-tokenize/`, `crates/tamil-toolkit/`, `bindings/{python,js-wasm,dart-flutter}/`, `lexicon/tokenize-{v0.1,unicode-v17}.toml`, `tests/golden/tokenize_v01.jsonl`, `release-policy.toml`, `tools/release_{files,policy}.py`, `tools/release.py`, `.github/workflows/publish-crate.yml`, `docs/specs/tokenize-v0.1.md`):**
  - Owner approved activating all 54 fixtures in `tests/golden/tokenize_v01.jsonl` and adding `tamil-tokenize` (Rank 2, `Apache-2.0`, `#![forbid(unsafe_code)]`) to the public allowlist in `release-policy.toml` before `tamil-toolkit`.
  - Exposed `pub use tamil_tokenize as tokenize;`, `tokenize_words`, and `segment_sentences` through the shared Rust dispatcher and typed Python, TypeScript/WASM (Node + browser), and Dart convenience APIs, preserving exact UTF-8 byte and written-unit offsets (`[start_byte, end_byte)`, `[start_unit, end_unit)`), six attested Tamil abbreviations (`திரு.`, `மு.க.`, `பி.ப.`, `மு.ப.`, `எ.கா.`, `ரூ.`), and opt-in stopword profiles (`none`, `conservative`, `broad`).
  - Updated `stage_python()` in `tools/release.py` so the staged `python-sdist` workspace includes canonical dictionary packs/schemas while keeping the published crates.io `tamil-toolkit` crate slim (`99,995` bytes) and `Apache-2.0` only.
- **Checks:**
  - `just check-unicode`: passed (`40,265` active vectors = `40,211` + `54`; `157` synced release files verified).
  - `just agent-pre-stop-gate`: `cargo fmt --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `245` Rust workspace/property tests (including Unicode 17 Word/Sentence reference suites and 10,000-case properties), `524` harness tests, Rust active parity (`40,265` vectors), Python (`32/32`), and Node/browser-target WASM (`40,291/40,291`) all passed.
  - `just test-dart` (`40,286/40,286`, clean `dart analyze`) and quickstart Python wrapper check passed.
  - Isolated `default`-profile archives passed across Rust (`tamil-tokenize-0.1.0.crate` `29,133` bytes; `tamil-toolkit-0.1.0.crate` `99,995` bytes; `40,221` golden rows), Python (sdist + win_amd64 wheel, `40,221` golden rows), npm (Node + browser-target WASM + strict `tsc`, `40,221` golden rows), and Dart (`archive_sha256` `1fa2e0dc6409f349c2a3dc43b58fc23a6649da96d5766a3c7c22601221ac361e`, `40,221` golden rows). Note: `just release-check`'s `core`/`full` Rust `.crate` consumer step stops on the slim `tamil-toolkit` `.crate` by design (bulk `CC-BY-SA-4.0` dictionary CSVs are excluded from crates.io archives).
- **Next:** Optional cleanup of the temporary `../tamil-toolkit-phase9-candidate` worktree, version bump / manual release when ready to publish `tamil-tokenize`, or next roadmap phase.

## Release `0.1.0` Published (2026-11-24)

- **Published registries (`v0.1.0`, source commit `fbed514303a80bd2f9d6a9819113f4afbd32597b`, artifact run [`45338097329`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45338097329) — 14/14 jobs green):**
  - **crates.io** ([run `45338626800`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45338626800)): all 9 slim `Apache-2.0` crates (`tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`, `tamil-calendar`, `tamil-codec`, `tamil-hyphen`, `tamil-translit`, `tamil-toolkit`) published at `0.1.0`.
  - **npm** ([run `45338629795`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45338629795)): `tamil-toolkit@0.1.0` published via OIDC (`latest` dist-tag pointing to `0.1.0`).
  - **PyPI** ([run `45338632488`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45338632488)): `tamil-toolkit 0.1.0` published via OIDC (Linux, Windows, macOS abi3 wheels + sdist recorded in `docs/releases/v0.1.0.md`).
- **Release highlights:**
  - Added `pub use tamil_translit as translit;` on `crates/tamil-toolkit/src/lib.rs`, cleaned up READMEs/changelog, and recorded bounded/experimental `tamil-calendar` scope in `docs/releases/v0.1.0.md`.
  - Finalized Rank 0–6 future crate plan in `ROADMAP.md`, `docs/specs/architecture-roadmap.md` (`FR-012`), and `tools/release_policy.py` (`tamil-lexicon` registered at Rank 2 as unscaffolded).
- **Next:** Phase 9 (`tamil-tokenize`), or external store/deployment follow-ups (Redeploy Playground & Word Add-in v2.5.0 to Vercel, Chrome Web Store / Firefox AMO extension submission, Word AppSource review).

## Release `0.1.0-alpha.10` / Python `0.1.0a10` Published (2026-11-22)

- **Published registries (`v0.1.0-alpha.10`, source commit `ba4fa913bf327157323eeb7f8975e4f39b29224a`, artifact run `45057597093`):**
  - **crates.io** ([run `45058020552`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552)): all 9 approved crates (`tamil-core`, `tamil-norm`, `tamil-collate`, `tamil-numerals`, `tamil-calendar`, `tamil-codec`, `tamil-hyphen`, `tamil-translit`, `tamil-toolkit`) published at `0.1.0-alpha.10`.
  - **npm** ([run `45058040282`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058040282)): `tamil-toolkit@0.1.0-alpha.10` published via OIDC (`alpha` and `latest` dist-tags pointing to `0.1.0-alpha.10`; SHA-256 `113b88d7b42db841b1b712cac5b26c4744f4e6ba0787c41932ec2bdb9b8a77f4`).
  - **PyPI** ([run `45058060092`](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058060092)): `tamil-toolkit 0.1.0a10` published via OIDC (Linux, Windows, macOS wheels + sdist recorded in `docs/releases/alpha-10.md`).
  - Hardened `dispatch_and_watch()` in `tools/release_pipeline.py` so workflow run matching never latches onto an older run ID before a newly dispatched workflow appears in `gh run list`.

## Mayangoli Preview Candidates & Google/Microsoft IME Cycling (`tamil-translit`, Browser Extension & Word Add-in, 2026-11-22)

- **Scope (`crates/tamil-translit/`, `crates/tamil-toolkit/`, `bindings/`, `tests/golden/`, `docs/specs/translit-v0.1.md`, `integrations/browser-extension/`, `integrations/office-word-addin/`):**
  - Added `transliterate_suggest` in `crates/tamil-translit/src/lib.rs` and exposed it via `crates/tamil-toolkit` (`OPERATIONS` & `execute`), `bindings/js-wasm`, `bindings/python`, and `bindings/dart-flutter`, backed by 11 new golden vectors in `tests/golden/translit_v01.jsonl` (570 total translit vectors; 40,211 active vectors overall).
  - Enforced Tamil phonotactic locks in `mayangoli_variants`: word-initial letters (`ந`, `ல`, `ர`) never mutate into illegal initials (`ண/ன/ள/ழ/ற`), homorganic/rhotic clusters (`ந்த`, `ண்ட`, `ன்ற`, `ற்ற`) and `ர்`/`ற்` codas stay locked, geminates (`ன்ன↔ண்ண`, `ல்ல↔ள்ள`) mutate as atomic units, and `ழ` never geminates.
  - Upgraded the Browser Extension (`floating-pill.ts`, `live-typing.ts`, `content/index.ts`, `background/index.ts`) and Word Add-in (`index.html`, `styles.css`, `taskpane.ts`, `word-adapter.ts`, `tamil-engine.ts`) with numbered Mayangoli candidate menus, Google/Microsoft keyboard cycling (`ArrowDown`/`ArrowUp`, `Tab`/`Shift+Tab`, `Space`/`Enter`/punctuation commit, `1`–`5` direct pick, mouse click, `Escape`), and 1-click Word cursor/selection replacement.
- **Checks:** `check-unicode` (40,211 active vectors, 151 release files verified), `cargo test -p tamil-translit --locked` (3/3), `cargo test -p tamil-toolkit --locked --test golden_suite` (5/5), `test-parity` (Rust 5/5, Python 31/31, Node/Browser WASM 40,236/40,236), `tamil-browser-extension` (`13/13` tests, Chrome/Firefox builds, `2/2` E2E bundle checks), `tamil-word-addin` (`16/16` tests, build + manifest), and `tamil-toolkit-playground` `build:beta` + `test` (`22` test files, `133/133` tests) all passed.

## Orthographic Visual-Kombu Repair Fix (`tamil-norm`, 2026-11-22)

- **Scope (`crates/tamil-norm/src/repair.rs`, `tests/golden/norm_repair.jsonl`, `integrations/browser-extension/`, `integrations/office-word-addin/`):**
  - Fixed `repair_tamil_text` in `crates/tamil-norm/src/repair.rs` to verify `!prev_is_bare_consonant` before treating `ெ`/`ே`/`ை` (`\u0BC6`/`\u0BC7`/`\u0BC8`) as a visual left-kombu before a consonant, and checked `!la_followed_by_sign` on typewriter `ெ + C + ள` -> `ௌ`. Added unit test and 3 golden vectors (`norm_repair_016..018`).
  - Updated browser extension `inspect-tab.ts` (manual repair button visibility/guard) and `content/index.ts` (`typingEngine.resetWord()` on `TAB_REPLACE_TEXT` / `TAB_INSERT_TEXT`), plus regression tests in `engine.test.ts` and `addin.test.ts`.

## Anjal & Phonetic Keyboard Mapping Fix (`tamil-translit`, 2026-11-22)

- **Scope (`lexicon/translit.toml`, `crates/tamil-translit/`, `docs/specs/translit-v0.1.md`, `tools/generate_translit_golden.py`, `tests/golden/translit_v01.jsonl`, `playground/`, `integrations/browser-extension/`, `integrations/office-word-addin/`):**
  - Replaced the shared hardcoded `phonetic_to_tamil` mapping in `crates/tamil-translit/src/lib.rs` with separate declarative `[anjal_phonetic]` and `[phonetic_v1]` tables in `lexicon/translit.toml` compiled via `build.rs`.
  - Fixed lowercase `s` -> `ச` (`se` -> `செ`, `selvam` -> `செல்வம்`, `sennai` -> `சென்னை`) and uppercase `S` -> `ஸ` (`Se` -> `ஸெ`), with `sk`/`Sk` -> `ஸ்க` and `phonetic = "S"` for `ஸ`.
  - Separated Anjal (`ee`/`oo` -> `ஏ`/`ஓ`, `w`/`W` -> `ந`/`ன`) from `phonetic-v1` (`ee`/`oo` -> `ஈ`/`ஊ`, `w`/`W` -> `வ`), added homorganic clusters (`nd`, `ndr`/`nR`, `nt`/`nth`/`ndh`, `ttr`/`rr`, `ngg`/medial `ng`, `njj`/medial `nj`, `x`/`ksh`), case-tolerant consonant handling, positional `ந` -> `n` in `phonetic-v1` `to_latin`, and `n-`/`n_` buffer support in browser-extension `LATIN_WORD_RE`.

## Native-Themed Chrome/Edge & Firefox Browser Extension (`023-browser-extension`, 2026-11-22)

- **Scope (`integrations/browser-extension/`, `integrations/shared/prepare-slim-wasm.mjs`, `integrations/office-word-addin/scripts/prepare-wasm.mjs`, `pnpm-workspace.yaml`, `specs/023-browser-extension/`):**
  - Extracted the shared slim Apache-2.0 default-profile WASM builder into `integrations/shared/prepare-slim-wasm.mjs` and wired both `integrations/office-word-addin` and `integrations/browser-extension` to reuse it.
  - Built dual-target MV3 packages (`dist/chrome` and `dist/firefox`) with zero install-time `host_permissions` (`activeTab` + opt-in single-origin permissions only), CSP `'wasm-unsafe-eval'`, Chrome `sidePanel` + `offscreen` silent clipboard host, and Firefox `sidebar_action` (`open_at_install: false`), non-persistent `background.scripts`, and `gecko.data_collection_permissions: none`.
  - Implemented **Live Inline Tamil Typing** (`Alt+Shift+L` shortcut + compact native toolbar popup `popup.html` with 1-click Side Panel launcher and Aytham `ஃ` icon, `த` badge, hybrid commitment: caret-anchored word-boundary preview + `Esc` English bypass for Phonetic/Anjal and instant per-keystroke conversion for Tamil99/Bamini including `;` pulli and punctuation-key letters, sensitive-field guard, focus-aware Shadow DOM floating pill, canvas-editor Quick-Compose scratchpad, and opt-in per-site Always-on).
  - Implemented **Live Document & Selection Tamil Inspector** (`tamil-core` / `tamil-norm` true Tamil letter count, word count, UTF-16 comparison, Uyir/Mei/Uyirmei/Aytham/Grantha breakdown, live streaming updates on typing/selection, Unicode health check with 1-click "Repair in place", optional live micro-counter, and 1-click "Inspect visible page").
  - Implemented **Fix Text** (7 legacy codecs + normalized `-v1` Auto ambiguity guard, joiner-preserving repair, *Agara Varisai* / *Uyirmei-first* sort, right-click silent copy, editable-field in-place repair & cold-start handoff) and **Tools** (native Chrome Refresh 2023 & Firefox Acorn/Proton + `browser.theme` tokens, bilingual `தமிழ் / EN`, TN/SL numerals & INR/LKR currency words, active civil date + official TN/SL holidays, and opt-in per-site Noto Tamil + Tamil Supplement font fixer with user-gesture permission prompt & revocation).
- **Checks:** `pnpm --filter tamil-browser-extension build` (both `dist/chrome` & `dist/firefox`, `tsc --noEmit`), `pnpm --filter tamil-browser-extension test` (**3/3 test files, 11/11 real-WASM + hybrid-typing + manifest tests**), `pnpm --filter tamil-browser-extension package` (**Chrome ZIP: 1,490.4 KiB**, **Firefox ZIP: 1,489.5 KiB**, **AMO source: 115.4 KiB** — all under the 2 MiB budget), `pnpm --filter tamil-browser-extension e2e` (**2/2 bundle checks**), and repo `check-unicode` / `check-release-policy` / `check-release-files`.
- **Owner follow-up outside git:** Load `dist/chrome` unpacked in Chrome/Edge and `dist/firefox/manifest.json` in Firefox `about:debugging` for final manual store-submission review.

## SEO & AI/LLM Discoverability Upgrade (2026-11-22)

- **Scope (`llms.txt`, `playground/`, `crates/*/Cargo.toml`, `bindings/`, `integrations/office-word-addin/`, `README.md`):**
  - Audited with Sol Medium and positioned around our core USP: fast, memory-safe, all-in-one Rust + WebAssembly Tamil linguistic engine with multi-package-manager parity (`crates.io`, `PyPI`, `npm`, `Dart`, `Word`).
  - Added `llms.txt` (root & `playground/public/llms.txt`), `playground/public/robots.txt`, `playground/public/sitemap.xml`, `playground/public/og-card.svg`, and build-time prerendering (`playground/vite.config.ts` + `playground/src/lib/seo-pages.ts`) for 7 canonical `/tools/<slug>/` static HTML pages (`bamini-to-unicode`, `tamil-number-to-words`, `tamil99-keyboard`, `agara-varisai-sorter`, `tamil-braille-converter`, `tamil-hyphenation`, `tamil-panchangam`).
  - Converted sidebar tool links to `<a href>` with `pushState`, kept `?tool=` bookmarks working, unified `document.title`/`canonical`/`description` ownership in `App.tsx`, and fixed broken integration doc links in `HyphenatorTool.tsx`.
  - Added validated `keywords` and `categories` to all 9 public `crates/*/Cargo.toml`, enriched PyPI & npm metadata, updated `README.md`, added `noindex` to Word taskpane `index.html`, and upgraded `integrations/office-word-addin/support.html` as the public landing page.
- **Checks:** Word Add-in build + 16/16 tests, Playground `build:beta` (all 7 prerendered `dist/tools/*/index.html` verified) + 22/22 test files (132/132 tests), and `check-unicode` (151 release files verified, 40,160 active vectors).
- **Owner follow-up outside git:** Fill in GitHub About/Description/Website/Topics, redeploy Playground & Word Add-in to Vercel, submit `sitemap.xml` in Google Search Console & Bing Webmaster Tools.

## License Migration: `MIT` → `Apache-2.0` + `NOTICE` (2026-11-22)

- **Scope (`LICENSE`, `NOTICE`, `Cargo.toml`, `crates/*/Cargo.toml`, `bindings/`, `playground/`, `integrations/office-word-addin/`, `tools/release_*.py`, `tests/harness/`):**
  - Replaced root `LICENSE` with verbatim **Apache License, Version 2.0** (`Copyright 2026 Abishtakan Sivachandrathevan and tamil-toolkit contributors`) and added canonical root `NOTICE` crediting `Abishtakan Sivachandrathevan and tamil-toolkit contributors` (`https://github.com/abishtakan/tamil-toolkit`) alongside all upstream data, standard, and reference attributions.
  - Updated `Cargo.toml`, all 9 public `crates/*/Cargo.toml` (`include` lists now ship `NOTICE`), `bindings/python/pyproject.toml`, `bindings/js-wasm/package.json`, `release-policy.toml`, `tools/release_policy.py`, `tools/release_files.py`, `tools/release.py`, `tools/lexicon_dart_archive.py`, `README.md`, `CONTRIBUTING.md`, `playground/src/App.tsx`, and `integrations/office-word-addin/`.
  - Synchronized all 151 release source copies (`LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, crate `README.md`, and lexicon copies) across all 9 public crates and 3 bindings; preserved all third-party dataset licenses (`CC-BY-SA-4.0`, `Unicode-3.0`, upstream MIT/CC references).
  - Also removed implemented `tamil-translit` from `UNSCAFFOLDED_PLANNED_CRATES` and added `'tamil-translit'` to `.github/workflows/publish-crate.yml`.
- **Checks:** `check-unicode` (151 release files verified, 40,160 active vectors) and all 91 release/license harness tests passed.

## Playground & Microsoft Word Add-in Update: Phases 6, 7B & 8 Feature Parity (2026-11-22)

- **Scope (`playground/`, `integrations/office-word-addin/`):**
  - **Playground (`playground/`):**
    - `CodecConverter.tsx` + `pdf-extract.ts`: Added Senthamil (`senthamil-cid-v1`), Shree-Tam (`shree-tam-cid-v1`), Softview (`softview-amudham-cid-v1`), TBO (`tbo-tboomi-cid-v1`), and Bharathi Tamil Braille (`bharathi-tamil-g1-v1`), plus PDF font-family heuristic hints for the 4 new CID fonts.
    - `NumeralFormatter.tsx`: Expanded Currency selector to all 8 currencies (`INR`, `LKR`, `SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`), wired `mixed_fraction_to_words` for mixed fractions (`1 1/2` -> `ஒன்றரை`, etc.), and added a **Tamil Words → Number (ITN)** (`words_to_number`) card in Tab 2.
    - `TranslitTool.tsx` + `tools.ts` + `App.tsx` + `i18n.ts`: Added 14th tool (**Transliteration & Tamil99**) exposing all 8 `tamil-translit` schemes (`iso-15919`, `madras-lexicon`, `itrans`, `harvard-kyoto`, `phonetic-v1`, `tamil99`, `anjal-phonetic`, `suratha-bamini`) with full EN/TA bilingual UI.
  - **Microsoft Word Add-in (`integrations/office-word-addin/`):**
    - Rebuilt slim MIT default-profile WASM (`3,296.4 KiB` / `1,412 KiB` gzipped) with Phases 6, 7B, and 8.
    - Extended `src/lib/tamil-engine.ts`, `index.html`, and `src/taskpane.ts` with Senthamil, Shree-Tam, Softview, TBO, and Bharathi Braille conversion, all 8 currencies + `words_to_number` (ITN) in the Insert tab, and a **Transliteration & Tamil99 Composer** drawer in the Type tab.
- **Checks:**
  - `pnpm --filter tamil-word-addin build` + `pnpm --filter tamil-word-addin test`: slim WASM rebuilt, `tsc --noEmit`, `vite build`, manifest generation, and **16/16** Vitest tests passed.
  - `pnpm --filter tamil-toolkit-playground build:beta` + `pnpm --filter tamil-toolkit-playground test`: `tsc --noEmit`, `vite build`, PWA precache, and **22/22 test files (131/131 tests)** passed.
  - `uv run --locked python tools/tasks.py check-unicode`: passed (40,160 active vectors, 139 release source copies verified).
- **Next:** Phase 9 (`tamil-tokenize`) or Chrome/Edge MV3 Browser Extension v1.

## Phase 8 (`tamil-translit` v0.1 Complete): Orthographic Romanization & Deterministic Offline Input (2026-11-22)

- **Scope (`crates/tamil-translit/`, `lexicon/translit.toml`, `docs/specs/translit-v0.1.md`, `tests/golden/translit_v01.jsonl`):**
  - Created Rank 2 crate `tamil-translit` (`#![forbid(unsafe_code)]`, depending only on `tamil-core` and `tamil-norm`) compiled from uniform readable NFC UTF-8 `lexicon/translit.toml`.
  - Implemented 8 deterministic schemes: 4 lossless bidirectional scholarly schemes (`iso-15919`, `madras-lexicon`, `itrans`, `harvard-kyoto`) + 4 offline keyboard/phonetic profiles (`tamil99` stateful gemination & homorganic nasal+stop auto-pulli, `anjal-phonetic`, `suratha-bamini` live left-kombu composer, and `phonetic-v1` bidirectional Tanglish v1).
  - Added 522 active golden vectors (`tests/golden/translit_v01.jsonl`, 40,160 total active vectors), registered in `release-policy.toml` and `release_files.py` (139 synced copies), and exposed `transliterate` / `transliterate_schemes` across Rust, Python, Node/Browser WASM, and Dart.
- **Next:** Phase 9 (`tamil-tokenize`) or Chrome/Edge MV3 Browser Extension v1.

## Uniform Readable UTF-8 Tamil in `lexicon/*.toml` (2026-11-22, Constitution 3.0.0)

- **Scope (`tools/toml_utf8.py`, 27 `lexicon/*.toml` files, 10 generators, `check_source_unicode.py`, `.github/workflows/ci.yml`, Constitution 3.0.0 & docs):**
  - Migrated all canonical `lexicon/*.toml` rule tables to uniform readable NFC UTF-8 Tamil (UTF-8 no BOM, LF line endings) while keeping detached Tamil combining marks (`U+0B82`, `U+0BBE..U+0BC2`, `U+0BC6..U+0BC8`, `U+0BCA..U+0BCD`, `U+0BD7`), Braille (`U+2800..U+28FF`), Tamil Supplement (`U+11FC0..U+11FFF`), and control/special characters escaped. Golden JSONL (`tests/golden/*.jsonl`) and dictionary pack metadata (`lexicon/dictionary/*.toml`, `lexicon/packs/*/*.toml`) stay untouched.
  - Verified 100% parsed `tomllib.loads` semantic equality against `HEAD` across all 41 `lexicon/**/*.toml` files, replayed all 10 generators, synced 135 release copies (`release_files.py sync`), enforced TOML spelling/BOM/LF in `check_source_unicode.py`, added `tests/harness/test_toml_utf8.py`, and added `just check-release-files` before sync in `.github/workflows/ci.yml`.
- **Next:** Phase 8 (`tamil-translit`).

## Phase 7B (`tamil-codec` Complete): Senthamil, Shree-Tam, Softview, TBO & Bharathi Braille (2026-11-22)

- **Scope (`crates/tamil-codec/`, `lexicon/{senthamil,shree_tam,softview,tbo,braille}.toml`, `docs/specs/codec-phase7-legacy.md`, `docs/specs/codec-braille.md`):**
  - Added `senthamil-cid-v1` (308 keys), `shree-tam-cid-v1` (316 keys), `softview-amudham-cid-v1` (313 keys), and `tbo-tboomi-cid-v1` (316 keys) projected from `AzhagiPlus-Portable.zip` (`e5fbf4b1f9a5533ac70021119641c51ddfa1df99c54162b9fa74e32ae1c1d510`) with 2,534 active golden vectors (`tests/golden/codec_phase7_legacy.jsonl`).
  - Added `tamil-codec::braille` (`bharathi-tamil-g1-v1`, `unicode_to_braille`, `braille_to_unicode`, `U+2800..U+28FF`) following World Braille Usage / NIEPVD Bharathi Braille with 160 active golden vectors (`tests/golden/codec_braille.jsonl`).
  - Wired all 18 operations into `tamil-toolkit` dispatcher and Python, TypeScript/WASM, and Dart bindings; synced 135 release source copies.
- **Next:** Phase 8 (`tamil-translit`).

## Phase 7A (`tamil-codec` / Playground): Client-Side Legacy PDF Text-Layer Extraction (2026-11-22)

- **Scope (`playground/src/lib/pdf-extract.ts`, `playground/src/components/public-tools/CodecConverter.tsx`, `docs/specs/codec-roadmap.md`):**
  - Added 100% client-side, zero-upload `pdfjs-dist` (legacy build for broad browser/Node compatibility) text-layer extraction, lazy-loaded via dynamic `import()` so initial Playground load is unaffected.
  - Added embedded PDF font-family heuristic hinting (`inferCodecFromPdfFonts`) for Bamini, Vanavil, LT-TM, TSCII, TAB, TAM, and Anjal, plus explicit bilingual EN/TA warnings for scanned image-only PDFs (no OCR).
  - Documented provenance/licensing status for queued legacy font tables (Senthamil, Shree-Tam, Softview, TBO) in `docs/specs/codec-roadmap.md` (no GPL-3.0 table copying into MIT `crates/tamil-codec`; primary `.ttf` `cmap` or permissive mapping witnesses required).
- **Checks:** `pnpm --filter tamil-toolkit-playground test` (21/21 files, 127/127 passed), `pnpm --filter tamil-toolkit-playground build:beta` (`tsc --noEmit` + `vite build` + PWA precache), `check-unicode` (36,944 active vectors, 130 release source copies verified).
- **Next:** Decide whether to add `tamil-codec::braille` (Bharathi / Unicode Braille Grade 1) or proceed directly to **Phase 8 (`tamil-translit`)**.

## Phase 6 (`tamil-numerals` v0.4): Diaspora Currencies, Colloquial Mixed Fractions & Formal ITN (2026-11-22)

- **Scope (`crates/tamil-numerals/`, `docs/specs/numerals-v0.4.md`, `lexicon/numerals-v04.toml`):**
  - Extended `Currency` directly from `{INR, LKR}` to `{INR, LKR, SGD, MYR, USD, EUR, GBP, CAD}` across `format_currency`, `currency_to_words`, `format_currency_decimal`, and `currency_decimal_to_words` (3-2 Indian grouping preserved for `INR`/`LKR`; 3-3 international grouping for diaspora currencies). Updated v0.1 unknown-currency negative fixture from `"USD"` to `"ZZZ"` with owner approval.
  - Added `mixed_fraction_to_words` (`-999,999,999..=999,999,999`, `TN`/`SL`) with declarative ending rules in `lexicon/numerals-v04.toml` (`ஒன்றேகால்`, `ஒன்றரை`, `ஒன்றேமுக்கால்`, `ஆயிரத்தரை`, `ஒரு கோடியரை`, fraction reduction matching `format_mixed_fraction`, and explicit `மற்றும்` fallback).
  - Added `words_to_number` (exact formal ITN inverse of `to_words` over `-999,999,999..=999,999,999` for `TN` and `SL`) driven directly from the compiled CLDR 49 RBNF rule tables with a canonical round-trip check; wired CLI `tamil-toolkit numerals parse` to fall back from traditional glyphs to `words_to_number`.
  - Added 739 active golden vectors (`tests/golden/numerals_v04.jsonl`, generated deterministically by `tools/generate_numerals_v04_golden.py` from frozen ICU4J outputs), schema/manifest entries, harness checks (`tests/harness/test_numerals_v04_acceptance.py`), and Python/TypeScript-WASM/Dart typed wrappers and convenience tests.
- **Next:** Phase 7 (`tamil-codec` Senthamil/Shree-Tam/Softview/TBO + Playground `PDF.js` text-layer extraction), then Phase 8 (`tamil-translit`).

## Microsoft Word Add-in v2.2 — Tamil Toolkit for Word & AppSource Submission (2026-11-22)

- **Scope (`integrations/office-word-addin/`, Spec 014):** Upgraded from a standalone JS hyphenation-only add-in to **Tamil Toolkit (`v2.2.0.0`)**, a Fluent 2 + TypeScript Office.js utility suite backed 100% client-side by the slim MIT default-profile Rust/WASM build (`scripts/prepare-wasm.mjs`, ~3.1 MiB uncompressed / ~1.37 MiB gzipped — 15x smaller than the full-lexicon playground WASM). Retired the duplicate `engine.js`, `commands.js`, `taskpane.js`, and `taskpane.css` files.
- **Capabilities:**
  - **Expanded `தமிழ்` Ribbon (`src/commands.ts`):** Open Taskpane (`Tamil Toolkit`), Convert to Unicode, Live Bamini ON/OFF, Sort *Akara Varisai*, Insert Tamil Date, Repair Unicode, Hyphenate Selection, Hyphenate Document, Wrap Without Hyphen, Remove Hyphens.
  - **3-Tab Fluent 2 Taskpane (`index.html`, `src/taskpane.ts`, `src/styles.css`, `src/lib/*`):** **Type** (Live Bamini direct Word typing, instant/batch legacy conversion across Bamini, TSCII, TAB, TAM, Anjal, Vanavil, and LT-TM with `<w:rFonts>` Unicode font reassignment, orthographic repair, live composer, Tamil-aware Find & Replace, Document Inspector), **Prepare** (*Akara Varisai* & `uyirmei-first-v1` paragraph/list/table sorting, 1-click Prepare Legacy Document, OOXML formatting-preserving hyphenation in 25-paragraph batches), and **Insert** (Tamil Calendar & Panchangam stamps for `Thirukanitham`/`Vakya`, numerals/currency `INR`/`LKR` for `TN`/`SL`, traditional fractions & heritage symbols), with automatic Office Light/Dark theme sync and `தமிழ் / EN` UI language toggle (`src/lib/i18n.ts`).
  - **AppSource & Production Deployment:** Added `scripts/build-manifest.mjs` generating `manifest.xml` (`https://localhost:3000`) and `dist/manifest.prod.xml` (parameterized via `ADDIN_BASE_URL`, zero `localhost` URLs, `<DisplayName>Tamil Toolkit</DisplayName>`, `<HighResolutionIconUrl>` `icon-64.png`, `WordApi 1.3`, `ReadWriteDocument`), `privacy.html`, `support.html`, `public/vercel.json`, `public/_headers`, and store assets under `release/` (`tamil-toolkit-word-manifest.xml`, `store-logo-300x300.png`, `banner-1366x768.png`, `APPSOURCE_SUBMISSION.md`). Deployed to Vercel Production (`https://tamil-toolkit-word.vercel.app`) and submitted to Partner Center (`Pre-processing` / publisher vetting in review). Updated `docs/integrations/word-office-addin.md`.
- **Checks:**
  - `pnpm --filter tamil-word-addin build` + `pnpm --filter tamil-word-addin test`: slim WASM prepare, `tsc --noEmit`, `vite build`, manifest generation, and 13/13 Vitest tests passed against real slim Rust/WASM.
  - `npx --yes office-addin-manifest validate integrations/office-word-addin/release/tamil-toolkit-word-manifest.xml`: valid.
  - `uv run --locked python tools/tasks.py check-unicode`: passed (36,205 active vectors; 129 release source copies verified).

## Playground UI/UX redesign & full WASM feature parity (2026-11-20, current uncommitted work)

- **Scope (`playground/`)**: Replaced the 3-tier `Home / Public Tools / Developer Tools` + sub-chip layout with a single persistent desktop sidebar (`264px`), mobile slide-over drawer, keyboard-focusable tool filter (`/` or `Ctrl/Cmd+K`), and URL query synchronization (`?tool=<id>`). Added `playground/src/lib/tools.ts`, `playground/src/components/common/ToolHeader.tsx`, `playground/src/tests/navigation.test.ts`, and `playground/src/tests/full-features.test.ts`.
- **Usability & visual improvements**: Preserved the *ஓலைச்சுவடி & செம்மண் / கருங்கல்* palette tokens while separating clean sans UI chrome from Tamil serif reading text, removing gratuitous badges/shadows/latency clutter, fixing `CopyButton` light-variant check-icon contrast, fixing on-mount blank state across tools, and disabling PWA service worker registration in dev mode (`playground/src/pwa.ts`) so `localhost` serves fresh bundles.
- **Full WASM feature parity & bug fixes**:
  - `NumeralFormatter`: 4 sub-tabs (`Currency & Words`, `Traditional & Digits`, `Fractions, Percents & Ranges`, `Dates & Date Math`) with independent `INR`/`LKR` and `TN`/`SL` selectors, Tamil/Latin digit toggles, Indian grouping, ordinals, digit sequences, traditional integer format/parse, mixed fractions, percents/ratios, numeric ranges, and Tamil/Gregorian date arithmetic.
  - `CalendarExplorer`: 4 sub-tabs with Thirukanitham vs Vakya Civil profile toggle, TN/SL city presets + GPS check, `panchangam_at(HH:MM)`, limb transitions, reverse `tamil_to_gregorian_date` + `add_tamil_date` + 12-month schedule, observances + `TN`/`SL` official holidays + `lunar_phase_events`, and side-by-side `compareCalendarProfiles`. Lazy per-tab computation plus cached Web Worker execution (`runWorkerExecute` in `worker-client.ts` / `playground.worker.ts`) for `tamil_year_info` and `calendar_observances` eliminates the main-thread freeze.
  - `CodecConverter` & `playground.worker.ts`: single-byte Latin-1 encoding for `TSCII`/`TAB`/`TAM`/`Anjal`, Hex byte mode, `Preserve`/`Strict` codec error policy toggle for `Bamini`/`Vanavil`/`LT-TM`, and clickable `detect_encoding` candidate chips.
  - `LetterAnalyzer`, `TextSorter`, `SymbolsExplorer`, `ScalarInspector`, `CodeGenerator`, & `DispatcherSandbox`: added interactive `compose_uyirmei` builder, `get_olippasai` & `are_cognates`, pairwise `compare` & sort/search/folded keys, live `symbol_info` & `fraction_symbol` builder, structural `inspect_tamil_string` inspection, 7 snippet categories across TS/Python/Rust/Dart, and 13 dispatcher presets.
- **Public-beta packaging & mobile Tamil font support (`playground/`)**: Added `build:beta` (`playground/build-beta.mjs` + `VITE_PUBLIC_BETA=1` + `tools/prepare_playground.py --public-beta`) to keep `historical-lexicon/` out of `playground/dist/` and hide the unresolved-rights `Historical Archive` mode at compile/runtime (`IS_PUBLIC_BETA`, `resolveLexiconViewMode`), lazy-loaded all 13 tool routes via `React.lazy` for smaller JS chunks, cleaned the `worker-client.ts` import warning, and bundled self-hosted `@fontsource/noto-sans-tamil`, `@fontsource/noto-serif-tamil`, and `@fontsource/noto-sans-tamil-supplement` `.woff2` subsets (`U+0B82-0BFA` and `U+11FC0-11FFF`) in `playground/src/index.css` + `playground/vite.config.ts` so traditional Tamil signs and Tamil Supplement glyphs render on mobile devices.
- **Checks**:
  - `pnpm --filter tamil-toolkit-playground test`: 20 test files, 124 passed, 0 failed.
  - `pnpm --filter tamil-toolkit-playground build:beta`: `prepare.mjs --public-beta`, `tsc --noEmit` (0 errors), and `vite build` passed with `playground/dist/historical-lexicon` excluded and 8 subset `.woff2` font files precached.
  - `uv run --locked python tools/tasks.py check-unicode`: release policy, Unicode/schema gate (36,205 active vectors), numeral projections (2 rulesets, 72 symbols, 19 rules), and 129 release source copies verified.
- **Workspace**: Branch `master`, changes uncommitted under `playground/`, `CHANGELOG.md`, and `docs/status.md`; no Rust crates, `lexicon/`, or `bindings/` modified; no publishing.

## Alpha 8 release (published 2026-11-20)

Published Rust/npm `0.1.0-alpha.8` and Python `0.1.0a8` to crates.io, npm, and
PyPI from reviewed source commit `9fc40f6ae081d8cc0a0307fa7325de4f2f66db6d`
(immutable tag `v0.1.0-alpha.8`) and artifact run `44755276268` (14/14 jobs
green). See the [release record](releases/alpha-8.md) for all publisher run
links and verified registry SHA-256 checksums.

- **crates.io:** All 8 crates (`tamil-core`, `tamil-norm`, `tamil-collate`,
  `tamil-numerals`, `tamil-calendar`, `tamil-codec`, `tamil-hyphen`,
  `tamil-toolkit` at `0.1.0-alpha.8`, slim MIT profile) published in run
  `44756065322`.
- **npm:** `tamil-toolkit@0.1.0-alpha.8` (`alpha` and `latest` tags) published
  via `publish-npm.yml` in run `44756738415`.
- **PyPI:** `tamil-toolkit 0.1.0a8` (Linux/Windows/macOS wheels + sdist)
  published via `publish-pypi.yml` in run `44756745737`.
- **Playground:** Upgraded to 90,167 active verified `CC-BY-SA-4.0` Tamil
  entries (85,889 extracted from official `ta.wiktionary.org` dump) with
  unified single-card dictionary UI and Search & Browse.
- **Pending:** Historical source-record ZIP remains a separate local artifact
  with unresolved source rights; planned Wiktionary/historical golden suites
  remain planned pending activation review.


## Historical source-record explorer (2026-11-20)

Latest owner direction explicitly authorizes implementing access to all supplied
historical records without additional permission records. Source rights remain
unresolved; do not synthesize accepted decisions or a third-party license.
The separate source-record contract in docs/specs/lexicon-source-records.md is
implemented in Rust with a playground view. It indexes all 307,243
CSV rows, preserving originals/duplicates/empty cells and source-file/row locators.
This supplements the verified dictionary; it does not turn source rows into
verified lexical entries. Earlier permission-blocker notes below describe the
verified promotion path, not a prohibition on this owner-directed implementation.
This checkpoint predates the alpha.8 version preparation above.

The full export is now built at playground/public/historical-lexicon/:
307,243 records / 177,606 distinct lookup keys, all original cells identical.
A separate 23,361,785-byte data ZIP is retained at
 target/lexicon/full-recovery/historical-source-records-2026-11-16.zip
(SHA-256 d0bcf6c5ef4ddabf35306883585da37882d18a9e82aab8ad92f747379a5223fc).
Rust source-record tests pass (7 tests including 10,000 property cases).
All 111 playground tests and the production build pass, including real browser
WASM queries that retrieve original fields from all eleven CSV tables. On
2026-11-20, the local production preview returned HTTP 200 at
http://localhost:5173/?tool=lexicon&mode=historical. All 256 bucket hashes match
between the verified export, its ZIP and the production playground.

Core integration passed across two runs. The first run passed formatting,
release policy, Unicode/schema, 129 release-file comparisons, Clippy, workspace
Rust (227 passed, one skipped), doctests and harness (522 passed). Its disk
preflight stopped the WASM rebuild. Reversible NTFS compression of generated
files provided enough space for a successful binding rebuild and parity resume.
Rust and Python golden checks passed, along with 36,242 JavaScript tests. The
Rust/Python/WASM review ran both planned lexicon suites (12 additional vectors);
Dart also passed its review run (36,237 tests). These suites retain planned
status pending activation review. The historical data ZIP has separate terms
metadata, and the Rust crate package list contains the source-record tooling.

See target/lexicon/full-recovery/historical-implementation-proof.json for the
recorded evidence and the two integration logs. Alpha.8 release preparation is tracked above.

## Full historical-bundle recovery and release objective (2026-11-16, active)

Current integration checkpoint: the preserving seven-entry core union is now
installed in `lexicon/dictionary/`, dataset `0.1.0+a211334e3659`, manifest
`a211334e3659647deb4fc30a1c5c6778f4fa9ef98815ed44674a7d5d7dc05bdf`.
Core has 10,343 entries / 23,827 senses; full data has 9,410 written forms /
11,377 entries / 25,742 senses. Base backup is retained at
`target/lexicon/full-recovery/base-core-before-integration/`.
All old entry revisions and the 44 existing golden entry payloads are exact.
Only old expected pack metadata/citations were refreshed. Seven new sourced
vectors live in `tests/golden/lexicon_gap_recovery.jsonl` as PLANNED; do not count
them active or activate without owner review. Distribution copies (129 files)
and playground catalog/notices have been synchronized. Core parity + explicit
planned-vector review then Dart is running in root exec session91029; logs are
`target/lexicon/full-recovery/core-parity.log`, `core-dart.log` and
`runtime-checks.json`. Python and both WASM builds completed; Rust/Python/WASM
fixture execution follows. Earlier attempts stopped on golden ID hyphens and
then the legal-text closure: re-promotion had used the Markdown wrapper checksum.
The merger now requires pinned raw license support from the original reviewed
workspace, matching input legal notices. No compiler check was weakened. Corrected
stage is `target/lexicon/full-recovery/merge-core-7-legal/`; prior failed evidence
is retained. Original source rows remain frozen.

User expanded the target from 410 Wiktionary gaps to the entire 307,243-record
historical bundle and eventual next release. User confirmed no additional written
permission/open-license records for TVA/Sorkuvai, Oxford/Apple, Tamilcube or Cre-A.
Do not infer source grants, approve historical claims, or publish unknown-rights
data. Keep progressing with freshly source-backed recoveries and preserve the
full unresolved inventory. Workspace version stays alpha.7 until a release batch
is actually prepared; existing v0.1.0-alpha.7 tag is immutable.

Saji Hydrogen tasks: technical source recovery (completed research; see
`docs/audits/historical-technical-recovery-2026-11-16.md` and
`target/lexicon/full-recovery/technical/permission-request-packet.md`); rendered
Wiktionary recovery is active under task ending `279c0ec8-34b4-4ba5-b541-3010dea20336`.
It owns only new `tools/lexicon_wiktionary_rendered.py`, its tests/spec, and
`data/sources/enwiktionary-tamil-rendered-2026-11-16/`. Follow completion wake-up;
do not poll a running delegate. Provider is antigravity_saji/Hydrogen/high.

Root added tests-first `tools/lexicon_merge.py` and
`tests/harness/test_lexicon_merge.py` (6 tests pass), with
`docs/specs/lexicon-pack-merge.md`. It preserves base rows/revisions, resolves
private record/snapshot support explicitly, rejects identity/registry conflicts,
and preserves incoming attribution via content-named notice files. A register
display alias is accepted only through the existing finite Wiktionary mapping.
Full core + seven candidates staged successfully at
`target/lexicon/full-recovery/merge-core-7/canonical`: 10,343 entries / 23,827
senses, all 10,336 existing entry revisions preserved; runtime not yet installed.
This earlier staged union used a separate incoming notice filename. The installed
release-compatible union instead preserves complete capture-attribution blocks
within the approved attribution filename (source references stay unchanged).
Historical sources remain unchanged; live core now includes the seven additions
described at the top of this section. Rendered candidates remain proposed only.

Technical findings: 120,482 rows have exact downstream database trace but no
recovered upstream harvest/record IDs or applicable project grant; both
definition columns empty. Research flags encoding/punctuation/space-variant
quality issues; these are not authorization to repair or delete original rows.
No contacts were messaged. Full-bundle release is unresolved while those source
and reuse blockers remain. Continue recoverable slices; report exact exclusions.

## Wiktionary gap recovery candidate packet (2026-11-16)

See `docs/audits/wiktionary-gap-recovery-2026-11-16.md`, its complete 410-record
escaped reconciliation queue, and `docs/reviews/wiktionary-gap-candidate-proof-2026-11-16.json`.
The original pinned snapshot contains 333 gap titles, all parser-blocked.
Fresh exact-title API captures for the other 77 pinned 51 revisions and returned
26 missing pages. The unchanged parser recovered 7 entries / 9 senses, leaving
377 parser-blocked spellings and 26 missing pages. No aliases silently followed.

Separate source capture: `data/sources/enwiktionary-tamil-gap-2026-11-16/`.
Reconciliation/fetch CLI: `python -m tools.lexicon_wiktionary_gaps` (see report).
Isolated workspace, canonical candidate and CLDF export live under
`target/lexicon/wiktionary-gaps-final/`; do not replace the current core with this
seven-entry candidate pack. Its 25 automated source claims pass release and
canonical validation and genuine offline CLDF validation/roundtrip. Accurate
2026-11-16 snapshot dates propagate through identity, metadata and decisions;
existing 2026-11-15 defaults remain unchanged. No template policy was relaxed.

Current 9,403-form runtime/playground packs remain unchanged, as do all 12
historical hashes and historical acceptance decisions. Runtime integration
requires merging this packet, source-backed fixtures and metadata refresh,
preservation checks and runtime/archive acceptance. Next extraction work is
the 134 place-template pages using pinned rendering/dependency evidence.

Checks: 29 focused tests pass; full harness 501 passed in 78.82s (80.041s runner);
agent-post-edit passes in 37.151s (Unicode/schema/release copies, Rust formatting,
workspace/core checks). Isolated pack/CLDF passes and all 20 canonical files
reproduce byte-identically. Final source/canonical/historical fingerprints match.
Independent Hydrogen review confirmed bounded accounting and isolation; its five
reuse/provenance/freshness findings were corrected with local regression tests.
Logs and timings: `target/lexicon/wiktionary-gaps-final/checks.json` and sibling logs.
No current runtime/binding/archive integration is claimed for these candidates.

## Historical source readiness report (2026-11-16)

See `docs/audits/lexicon-source-readiness-2026-11-16.md` and adjacent measured
JSON, generated by `tools/audit_lexicon_readiness.py`. All 12 frozen files and
recovered package exports match their original hashes. Exact headword/phrase
cell union: 177,606 distinct strings; 8,968 overlap current written forms and
168,638 are absent candidates, not approved words. No normalization or trimming
was performed. Current runtime coverage remains 9,403 written forms.

Historical workspace still has zero acceptance decisions and 27 sources with
unknown evidence/reuse states. Priority: reconcile the 410 absent spellings in
26,138 Wiktionary-labelled meanings against the existing pinned snapshot; recover
separate TVA/Sorkuvai extraction and reuse evidence for the largest technical
slice. Do not promote old mixed-source definitions by relabelling their lemma.
No source, curation, canonical or binding data changed; no publishing.

Checks: deterministic byte-identical inventory replay, row/group totals and set
partitions pass; Unicode/schema/release-policy and 129 release-copy gate passes.
Runtime and archive matrices were not repeated for this reporting-only change.

## Full lexicon playground ready (2026-11-16)

User can open http://localhost:5173/?tool=lexicon. Vite is running in root exec
session57088 on127.0.0.1:5173. `just playground-dev` starts it again when needed.
Normal dev/build scripts now prepare optimized full-profile browser WASM and a
manifest-derived catalog/attribution assets; Cargo default data features stay off.
Browser WASM is intentionally full; Node/Python/Dart bindings were not rebuilt.

Lexicon is featured first on the hub. English/Tamil UI includes all3usablepacks,
pack selection, finite16-region/34-register filters, homographs/all senses,
source/human-vs-auto provenance, safe links, examples, advanced error presets,
raw JSON/copy/download and explicit historical307243-record exclusion. Data
coverage and attribution are expandable; query appears prominently on mobile.
Catalog counts are withheld if loaded pack manifests mismatch canonical metadata.

Checks: playground89tests pass (including real full-profile WASM), TypeScript
check/production PWA build pass, catalog verification passes, and agent-post-edit
(format/Unicode/schema/release129copies/workspace/core checks) passes. Browser
checks: direct link,3packs,2nanrihomographs/3senses, JAFFNApositive/unknown-negative,
English/Tamil/theme controls, desktop1280andmobile390 with no document overflow.
Intentional NFD/joiner fixtures use explicit scalar constructors; no gate weakened.
Production precaches ~46MiBfullWASM plus attribution Markdown (64MiBfilecap).
Build uses tsc --noEmit instead of shared incremental tsbuildinfo to avoid Windows
mapped-file collisions. Runtime covers current9403headwords/11370entries/25733senses;
the quarantined historical intake is not available for lookup. No engine/data
semantics, schema/golden/public version/publishing scope changed. No publishing.

## Completed optimization acceptance (2026-11-16)

All requested code and acceptance checks are complete. See
`docs/audits/lexicon-performance-2026-11-16.md` and
`target/lexicon/speed-candidate/acceptance-summary.json`.

- Harness: all original 447 cases retained; 484 passed in 64.25s (before1130.88s).
- Core binding synchronization: cold200.681069s, verified warm1.344987s.
- Exact single-profile pre-stop: passed835.532051s. Before attempts were incomplete;
  do not claim a whole-gate speedup ratio. Rust220 passed, existing ignored calendar
  evidence exporter unchanged; no new skips.
- Structural307243 records/12 files: debug47.121055s/391.40MiB; optimized45.351766s/
  390.30MiB. Budgets pass, but measured throughput did not improve over40.918690s.
- Default/core/full Rust/Python/Node/browser-WASM and Dart runtime matrix passed.
  All isolated Rust/Python/npm and private Dart archives passed in all3profiles.
- Core development profile restored and parity/Dart rechecked (121.690161s).
- Independent Hydrogen high review and bounded follow-ups: no actionable issues.
  Original12source hashes reverified; baseline evidence preserved. No publishing,
  default-data feature, crate/version/registry scope change. No commands remain running.

The history below records failed attempts and diagnostics; the completion above
supersedes their pending-state notes. No extra unmodified baseline should restart.

## Current final verification (2026-11-16)

All requested optimization code is integrated. Exact pre-stop gate passed in
835.532051s: 220 Rust tests passed (one existing ignored evidence exporter),
484 harness tests passed in 64.25s, then real core parity passed. Core/default/full
runtime parity and Dart all pass. Independent Hydrogen high review and bounded
follow-ups report no actionable issues. Baseline results remain preserved.

Root acceptance runner continues in exec session 38245:
`uv run --locked python target/lexicon/run_speed_acceptance.py parity-full`.
Full parity and Dart have completed. It is now running isolated default archives,
then default Dart archive, core archives/Dart archive, full archives/Dart archive.
Each step writes `target/lexicon/speed-candidate/<step>-result.json` and stops on
failure; preserve all passed steps. Completed default/full Cargo caches were
cleared with confined Cargo-managed cleanup before archives; core caches and all
canonical outputs/evidence remain. About 9 GiB was free at archive start.

After archives: restore core bindings/parity/Dart if archives altered canonical
outputs; finish evidence, report chart and task T090. Measurements and limitations
are in `docs/audits/lexicon-performance-2026-11-16.md`. Structural processing meets
budgets but did not improve over baseline. No publishing or scope/version change.

## Optimization integration (2026-11-16, current)

The owner stopped the extra baseline. Do not restart it. Completed acceptance,
archive and benchmark evidence remains under `target/lexicon/speed-baseline/`.
Its exact pre-stop attempts were incomplete (disk full, then owner stopped),
so there is no valid passing before-time for that whole command.

All three optimization implementations are applied; workers have stopped edits.
Full parallel harness: 481 passed in 70.79s / 71.774509s command wall time,
versus baseline 447 passed in 1130.88s. All original IDs remain. Two native
cycle/dict-subclass regressions and one build-mode regression were added after
that run; all nine native-batch parity tests pass on the actual rebuilt PyO3.
Explicit `--dist=load` shared-lock tests: 3 passed in 19.44s.

Independent Hydrogen high review found cycle and iterable-pair issues in the
native helper; both were reproduced tests-first and fixed. Fresh review found
no actionable issues; a narrow build-mode fallback follow-up is in progress.

Measurement caught a real debug-batch regression: structural work took 92.62s.
That failed report is preserved as `speed-candidate/lexicon-benchmarks.json`.
Optimized native JSON/hash batches are about twice as fast as CPython on 5000
real rows, but debug Rust batches are slower. Host adapters therefore use
native generic batches only when `HOST_BATCH_OPTIMIZED` is true; debug builds
use the exact reference validators/encoder/hashes. Unicode audit batches stay
in Rust in both modes. No Unicode, schema or source-integrity check was removed.
Current isolated measurement: `speed-candidate/structural-final-debug.json`.
Next: optimized-build measurement, actual concurrent cold/warm binding builds,
timed single-profile pre-stop, final runtime/archive matrix, then evidence and
task closure. Do not overlap builds/tests with performance measurements.

Latest measured results: debug structural 47.121055s / 391.40 MiB;
optimized structural 45.351766s / 390.30 MiB. Both budgets pass, but neither
improves the preserved 40.918690s baseline. Serial fixtures + real native checks:
76 passed in 128.68s. Concurrent core bindings (all four targets): 200.681069s
cold; verified warm reuse: 1.344987s. These are not comparable cold/warm baselines.

The first candidate exact pre-stop ran 756.656629s: 220 Rust tests passed,
then 17 fake-build harness tests failed because they depended on actual free
disk space. Unit fixtures now control disk usage; dedicated low-disk rejection
tests and production preflight are unchanged. Focused 28 tests pass; bounded
independent review found no issues. Failed gate evidence is preserved as
`speed-candidate/pre-stop-first-failed*`. Scoped Cargo-managed cleanup removed
5.0 GiB of old root WASM package artifacts; baseline evidence hashes matched
before/after. No broad `cargo clean` or recursive shell deletion was used.

Root is running `target/lexicon/run_speed_acceptance.py pre-stop` in exec session
9023. It records each step separately in `speed-candidate/*-result.json`, stops
on failure, and preserves already-passed steps. It currently reruns the exact
gate for a valid whole-command timing after the test-only repair, then executes
Dart/core and default/full parity + Dart, followed by all three isolated archives.
Code is frozen except documentation/task evidence. Monitor disk; completed
non-core isolated Cargo caches may need Cargo-managed cleanup before the next
cold profile. Retain core caches, archives, logs, progress JSON and raw data.
Detailed evidence: `docs/audits/lexicon-performance-2026-11-16.md`.

The sections below preserve earlier investigation history; this section owns
the current state.

## Bulk expansion verification in progress (2026-11-15)

LATEST OWNER STEERING: stop the extra baseline run, preserve results, apply
optimizations now. The extra timing process tree was stopped explicitly; its
partial log is `speed-baseline/pre-stop-user-stopped.log`, result state is
`stopped_by_user` (not a passing timing). Completed acceptance/archive/benchmark
baselines remain intact. Both target-only optimization proposals are now applied
to live source; pytest-xdist3.8.0/execnet2.1.2 are locked dev dependencies.
First focused run: 40passed/3failed66.12s (new binding cache tests). Binding worker
owns live tools/tasks.py + test_task_speed.py to fix these, deduplicate confirmed
same-profile Rust invocations and validate. Fixture worker owns applied conftest,
five fixture test modules and tools/lexicon_wiktionary_candidate.py; validates
serial/parallel isolation and immutable real-pack caches. Root already added
fixture path confinement before deletion and POSIX lock timeout parity.
Native worker now owns fresh actual-corpus/CLDF profiles and tests-first batch
Rust/PyO3 helper implementation. No canonical PyO3 rebuild until root coordinates
after workers stop consuming the Windows DLL. Do not restart the extra baseline.
New real benchmarks/final acceptance must run serially after implementation.
Current implementation validation: 20 binding-speed unit tests passed in 4.34s.
Collected 473 harness cases; all 447 baseline passed IDs are retained, with 26
added cases (`target/lexicon/speed-test-id-coverage.json`). Root actual profiles
completed via runpy with repository imports: full 307243-row stage/check/prove
and valid/round-trip-checked CLDF exports for core/names_taxa/regional. Native
worker has completed profiles and is authorized to implement measured batch
helpers; profiling wall times are instrumented diagnostics, not candidate timing.
Root canonical core PyO3 rebuild passed (54.77s Cargo build), then all six direct
native batch parity tests passed in 3.84s. Interrupted provider task-311 is NOT
counted as passing. Root now runs the full parallel harness with captured timing,
JUnit and durations via `target/lexicon/measure_candidate_harness.py`; outputs
under `speed-candidate/`. No other heavy jobs should overlap this measurement.

Resume update (2026-11-16): exact pre-stop timing failed after 1718.285468s
when the drive filled during pytest (8 failed, 301 passed, then pytest output
flush raised ENOSPC). Individual failure traces were lost in the interrupted
report; their causes must be checked on rerun. Source fingerprints remained
unchanged. Failure evidence
is preserved as `speed-baseline/pre-stop-disk-full.log` and
`pre-stop-disk-full-result.json`; it is not a passing gate baseline.
No optimization proposal has been applied. Recursive shell cleanup was rejected
by automatic approval; Cargo-managed cleanup of tamil-toolkit/python/wasm/dart
removed 43133 generated files / 19.3GiB and recovered about 21.17GB free.
Accepted archives, benchmarks, raw sources and proposals remain intact.
The exact unmodified single-profile pre-stop measurement has restarted. This run
has cold Cargo outputs after cleanup; record that condition in comparisons.

Owner's next instruction (2026-11-16): finish and preserve the current acceptance
and archive/benchmark baseline before any further optimization edits; retain
already-passed steps unless a step fails. The harness baseline is now recorded:
447 passed in 1130.88s. Immutable copied log/result:
`target/lexicon/speed-baseline/harness.log` and `harness-result.json`.
Runtime acceptance is now passed and copied to
`target/lexicon/speed-baseline/acceptance-progress.json`: current post-edit 84.580s,
default binding rebuild 11.261s and final default parity 68.176s. All actual
default/core/full archives, private Dart archives and combined enforced benchmarks
now pass; final reports were copied to `speed-baseline/archive-progress.json` and
`speed-baseline/lexicon-benchmarks.json`. Structural baseline is 40.918690s /
388.26 MiB; stage 20.959690s, inventory 3.613759s, validation 16.300280s. Lookup
10,000-query warm p95 is 6.5444ms native / 7.3160ms serialized on expanded core.
No successful baseline steps were discarded.
Baseline archive progress: default archives passed (225.883s), default private
Dart archive passed (13.800s), core archives passed (421.627s). Core private Dart
archive correctly rejected a stale default DLL: the helper copied the last build
without building the selected profile. This failed-step repair now builds the
requested profile before packaging; four focused tests pass in 1.12s. The queue
resumed at `dart-archive-core`, preserving the three completed archive steps in
`speed-baseline/archive-progress-before-dart-repair.json`. This is a baseline
failure fix, not the deferred optimization work. Core Dart now passes (27.020s),
full archives pass (419.692s), full Dart passes (25.533s), and combined benchmarks
pass (101.015s).
After baseline completion, optimize shared read-only real-pack fixtures, safe
pytest-xdist isolation, profiled batch Rust/PyO3 validation/hash/scalar work,
isolated concurrent binding targets and fast single-profile daily verification.
Keep the three-profile/four-runtime plus archives matrix for final acceptance.
Report exact harness, lexicon benchmark and pre-stop before/after timings and
unchanged assertions/checks/coverage. An exact additional unmodified single-profile
`just agent-pre-stop-gate` baseline is running under
`target/lexicon/speed-baseline/measure_pre_stop.py`; result/log live beside it.
Root source/tests/config stay frozen until this timing completes. Three Hydrogen
high workers are preparing target-only fixture/xdist and binding candidate patches
and a native-batch design; no tests/builds/profiling or repository edits are allowed
in those tasks during the timing window. Review/apply proposals only afterward.

Long harness run diagnosed and stopped at the owner's request (2026-11-16):
`py-spy` located eager whole-decision indexing in `unicode_findings` for every
canonical assertion, including claims without exceptions. Roughly 50,000 claims
and decisions made this quadratic; candidate tests repeatedly scanned the pack.
The index/terminal calculation now runs only upon the first actual exception.
Native Unicode inspection and every exception authorization check remain intact.
Three regression cases failed before; 97 focused review/curation/pack tests passed
after in 11.17s. A bounded 1,000-claim / 5,000-decision comparison returned identical
findings in 0.4875s before / 0.0542s after (9.00x). Evidence:
`target/lexicon/slow-harness-stack.txt`, `lazy-unicode-before.log`,
`lazy-unicode-focused.log`, `lazy-unicode-measurement.json`.
The full harness is rerunning with per-test names, durations and a 120s diagnostic
stack timeout in `target/lexicon/lazy-unicode-full-harness.log`. Old gate/archive
coordinators were stopped; resume the remaining gate/archive sequence only after
this fresh run and the current source checks pass.
A five-second follow-up profile also found 406/499 samples in the review helper's
Python JSON Schema validator. `_valid` now reuses the existing shared compiled
`validate_row` path and its strict scalar/nonstandard-value fallback. Four-table
mutation parity checks compare it with the reference validator. Combined focused
verification now passes 106 tests in 9.00s; the full harness has restarted with
both fixes. Independent Hydrogen high review reported no actionable findings,
including preserved exception authorization, scalar checks, schema fallback and
import-cycle safety. A second profile now shows ordinary streaming row decoding
and native inspection rather than eager whole-decision indexing.
`target/lexicon/finish_after_harness_performance_fix.py` waits for this full run,
then performs current post-edit checks and the remaining default binding/parity
steps. Progress stays in `corrected-acceptance-progress.json`. The separate archive
coordinator waits for that sequence to pass; no concurrent native builds run.

Current corrected packs contain 11,370 entries / 25,733 senses: core 10,336 /
23,818 (`0.1.0+1f2bc70dc132`), names_taxa 762 / 906
(`0.1.0+279048283410`), regional 272 / 1,009 (`0.1.0+b97b5f21230d`).
Native-checked regeneration and promotion passed. All six reviewed lexical
payloads remain exactly equal; the 44 golden cases retain their executable
expectations apart from approved pack metadata. Source citations now match the
new metadata. Evidence: `target/lexicon/corrected-pack-refresh-proof.json`.

T080/T081 are implemented and checked: distinct same-POS homographs, own-entry
regional routing, finite qualifier mappings and literal unmapped prose. Twelve
extractor tests passed after four new pinned regressions failed before fixes.
Release synchronization/check passed for 129 files. Full-profile PyO3, Node WASM,
browser WASM and TypeScript library builds passed. Default Cargo data features,
crate version and registry scope remain unchanged. Original 12 sources stay
quarantined and immutable. No publishing, commit or push is authorized.

The initial focused profile run found six failures (30 passed). Root repaired
planned-suite test setup, unit profile isolation, signed archive fixture CSVs,
direct-script Dart imports and stale static-helper checks. The targeted rerun
passed six tests; its remaining static check passed separately after aligning it
with golden helpers and parameterized unavailable-pack errors. Independent review
found stale Rust/CLDF count/hash assertions; these are refreshed too. The final
narrow Hydrogen high re-review reported no findings after the helper/citation
correction. This read-only verdict does not replace the running integration gates.

Serialized acceptance is running, with stop-on-failure behavior:
Current CLDF verification passed all 14 tests (297.03s). Full Rust verification
then passed five golden, ten lookup and 25 compiler tests after fixing an absent
optional TOML key insertion in a fixture. Full parity rebuilt bindings and passed
Rust, then exposed Python's incorrect assumption that default lookup searches all
compiled packs. Root corrected Python/TS default expectations to core and added
explicit three-pack metadata checks in Python/TS/Dart. Current full parity reuses
the verified full binding builds because only test expectations changed; core and
default steps still rebuild normally. Full-profile parity now passes: Rust five
tests / 36,161 baseline vectors with 44 core-only exclusions, Python 31 tests,
Node/browser WASM 36,186 tests. Serialized Dart follows before core/default parity.
Full/core/default parity and Dart all passed. The final gate passed formatting,
Unicode/schema (36,205 active vectors), release policy, release copies (129 files)
and workspace checks, then found a missing import in the default-profile typed
lookup test. Root qualified that test call explicitly. Nine default lookup tests
and full workspace Clippy now pass. The queue resumes the remaining pre-stop
Rust/harness/rebuild/parity steps; archives remain gated on their success.
`target/lexicon/run_corrected_acceptance.py` runs current CLDF tests, full Rust
lexicon suites, full/core/default real parity and Dart, then the default full
pre-stop gate. Status: `target/lexicon/corrected-acceptance-progress.json`.
A second runner waits for all those steps to pass before actual default/core/full
archives, private Dart archives, a core binding rebuild and isolated combined
benchmarks. Status: `target/lexicon/corrected-archive-progress.json`. Logs use
`target/lexicon/corrected-*.log`. Neither runner publishes. If a step fails, fix
that failure before resuming its remaining sequence; do not claim queued steps
passed. T082/T083 and final expanded acceptance remain open.

Implementation/audit context:
`docs/audits/expanded-lexicon-corrections-2026-11-15.md`.
Earlier six-entry acceptance and pre-correction counts below are historical.

## Feature 021 remediation closed and verified (2026-11-15)
Host baseline completed: 88 passed / 12 failed in 1474.60 seconds. Nine failures
concern archive fixtures missing newly packaged notice paths; the profile worker
owns these. Three benchmark failures exposed old six-entry assumptions and an
anchor list that consumed the whole expanded query budget. Root bounded seeded
anchors while preserving largest-sense/homograph/NFD/miss/boundary coverage and
filtered actual canonical keys out of negative requests. Counts and cold-start
expectations now derive from pack metadata. All 10 benchmark tests pass in 8.71s
(target/lexicon/expanded-benchmark-tests.log). No latency claim follows from unit
stub tests; real expanded-pack measurements remain pending.

- **Scope & invariants preserved**: six revision-pinned Wiktionary entries / 19
  senses / 31 accepted claims (`lexicon/dictionary/packs.toml` `0.1.0+4d1309d05391`,
  manifest `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`,
  compiled core pack `50,923` bytes, default Cargo payload `0` bytes),
  immutable 12-file originals (`data/sources/tamil-lexicon/`), Cargo default
  data features off, historical intake quarantined, and no publishing/commit/push.
- **Correctness fixes completed (`T071`–`T079`)**:
  - `T077` (`tools/lexicon_cldf.py`, `tests/harness/test_lexicon_cldf.py`): CLDF
    export closure preserves canonical sense-anchored (`sense -> sense` and
    `sense -> entry`) relations plus their assertion/evidence/decision closure
    and enforces round-trip table equality (`ROUNDTRIP_TABLE_MISMATCH`) and pack
    eligibility (`UNSUPPORTED_RELATION_SOURCE_KIND`, external closure); nonempty
    and tampered closure regressions pass (`52` CLDF+pack tests).
  - `T078` (`tools/lexicon_tables.py`, `crates/tamil-toolkit/build_lexicon.rs`,
    `tests/harness/test_lexicon_scope_backing.py`, `crates/tamil-toolkit/tests/lexicon_pack.rs`):
    Python and Rust validate optional `unknown`/`not_applicable` scope backing
    `(supporting_assertion_id, decision_id)` pairs, ownership, dimensions, and
    non-self `paired_translation_id` component/owner references.
  - `T079` (`tools/lexicon_packs.py`, `tests/harness/test_lexicon_packs.py`):
    `_evaluate_workspace` validates editorial integrity before applying cross-pack
    relation omission policies (`OMITTING_POLICIES`), and enforces public
    shape/vocabulary checks only on non-omitted internal relations.
- **Full-corpus structural & lookup benchmarks (`T063`, isolated)**:
  - Structural full corpus (`307,243` CSV records across `12` immutable source
    files, `canonical_proof_used: true`, `full_corpus_verified: true`,
    `pilot_substituted: false`): Run 1 (`target/lexicon/benchmarks.json`) passed
    in **`45.993746s`** (`<= 60.0s`) and **`387.39 MiB`** peak process-tree RSS
    (`<= 512.0 MiB`); Run 2 repeatability
    (`target/lexicon/benchmarks-structural-repeat.json`) passed in
    **`45.994234s`** and **`383.33 MiB`** peak RSS.
  - Lookup (`core`, `6` entries / `19` senses): cold-start `import 2.3018 ms`,
    `first_lookup 3.3947 ms`, `37.11 MiB` peak RSS; `10,000` seeded warm queries
    passed at **`1.2445 ms`** native p95 / **`1.478 ms`** serialized p95
    (`<= 10.0 ms`). (Measured on the 6-entry core pack; large-pack scaling
    remains for Step 2 expansion.)
- **Serialized verification gates (`target/lexicon/final-verify-*.log`)**:
  - `agent-pre-stop-gate`: `cargo fmt`, `release_policy.py`, `check_source_unicode.py`
    (`36,205` active vectors), numeral checks, `release_files.py` (`89` files),
    `cargo check`, `cargo clippy -- -D warnings`, `cargo nextest` (`214 passed, 1 skipped`
    existing `#[ignore]` in `drik.rs`; `48 passed, 0 skipped` on `tamil-toolkit --features lexicon-core`),
    `pytest tests/harness` (`427 passed`), `sync-bindings`, Rust/Python (`31` groups)
    and WASM (`36,230 passed`) golden parity.
  - Serialized Dart & isolated archives: `dart-core` (`36,225` tests) &
    `dart-archive-core` (`36,205` rows); `dart-default` (`36,181` tests) &
    `dart-archive-default` (`36,161` rows, `44` `PROFILE_EXCLUDED`); `archives-core`
    (`11` archives, `36,205` rows on Node/browser WASM + `tsc --strict`) &
    `archives-default` (`31` archives, `36,161` rows, `44` `PROFILE_EXCLUDED`);
    `sync-bindings --lexicon-profile core`.
- **Independent review**: fresh `gemini-4-hydrogen` (`high`) read-only review
  ([Independent Review: Feature 021 Remediation (Attempt 2)](t3-thread://v2/7b4f9a3a-2db3-42ae-b39f-ffc0c15e5b21/thread:delegated-task:command%3Amcp%3A0b76d8ad-b434-4f34-94e1-30ffd3cee66e%3Adelegate-task%3Acd6f7f98-9b08-4df8-b573-2c13d561daed))
  returned **APPROVED** with zero blocking findings.
- **Next**: await owner confirmation of the Step 2 bulk lexicon expansion
  proposal before making Step 2 edits.

Earlier checkpoints below are historical evidence; pending/completion claims
are superseded by the current remediation checkpoint above.

## Feature 021 verified core; owner activation approved (2026-11-15)

- **Scope**: six revision-pinned Wiktionary entries, five spellings and 19 senses;
  31 claims approved by `abish` on 2026-11-14 under the separate CC-BY-SA-4.0
  data policy. Engine code remains MIT. Historical merged-source intake stays
  quarantined; structured scopes remain unknown, with two pending proposals.
- **Pack**: `0.1.0+4d1309d05391`, manifest
  `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`.
  Default compiled payload is zero; core is 50,923 bytes. Promotion, offline
  CLDF round trips and compiler reproducibility are verified.
- **Runtime proof**: 36,205 active vectors, including 44 unchanged lexicon vectors
  pass in actual Rust/Python/Node/browser WASM and Dart. Default no-data
  behavior is verified separately. `target/lexicon/l4-functional.json` and
  `parity/core-profile.json` bind source/review/profile and runtime evidence.
- **Performance**: fresh inventory, staging and complete validation of 307,243
  records / 12 original files passes in **52.72 seconds / 191.93 MiB**.
  Both read-only validation subprocesses are included in process-tree RSS.
  Exact source payload equality is verified. Release core lookup passes 10,000
  queries per pass at p95 0.1148 ms native / 0.1979 ms with Python serialization.
  These measurements cover the six-entry lookup pack, not large-pack scaling.
  Evidence: `target/lexicon/benchmarks.json`.
- **Gates**: final core pre-stop gate exited 0: Unicode/schema, 89 release-copy
  checks, Clippy, 204 Rust tests (one existing intentional skip), 390 harness
  tests, 31 Python groups and 36,230 WASM tests. Serialized core Dart passed
  analysis and 36,225 tests. `target/lexicon/integration-gates.log` records both.
- **Archives**: 11 current Rust/Python/npm artifacts per core/default profile
  pass isolated consumers, manifest checks and applicable SPDX/notice closure.
  Both private Dart bundles pass after extraction (core 36,205 rows; default
  36,161). Evidence: `target/lexicon/archive-proof.json`. No registry upload.
- **Activation**: `abish` approved the 44-vector core-profile activation on
  2026-11-15. Receipt: `docs/reviews/lexicon-fixture-activation-2026-11-15.json`.
  Canonical verification selects core to execute every active vector; Cargo
  default data features remain off. Crate/version/registry scope is unchanged.
  Final affected gates, Dart and archive checks pass; T001–T070 are complete
  for this bounded reviewed core. Post-activation evidence is recorded in
  `target/lexicon/activation-final-gate.log`, `activation-dart.log` and
  `activation-archives.log`. Broader dictionary expansion requires new source
  evidence and review. No publication is authorized.
- **Workspace**: branch `master`, work uncommitted; no push/publication.
  Feature 022 and all 12 immutable original sources are preserved.

Earlier sections below are historical milestone evidence, superseded by this
checkpoint where their implementation/pending status differs.

## Feature 021 L2 structural pilot accepted (2026-11-14)

- **Objective & status**: Completed Feature 021 structural slice (`T001`–`T037`)
  under the `json-string-utf8-v1` storage decision on branch `master` (changes
  remain uncommitted; Feature 022 work and all 12 immutable source files in
  `data/sources/tamil-lexicon/` are preserved). `T038`–`T039` now have fresh-source and genuine human-review evidence for
  the six-entry Wiktionary core subset; `T040`–`T043` host tooling and CLDF
  proof are complete; `T044` source-backed planned goldens are complete; `T045`–`T070` remain in progress/pending
  (T066 docs partially updated). The historical bulk-source lineage remains unverified.
- **L0/L1 intake & proofs**:
  - Verified all 12 frozen original source hashes (`data/sources/tamil-lexicon.sha256.json`)
    and 307,243 logical CSV records (`../target/lexicon/baseline.json`).
  - Pre-projection intake & clean replay proof ([us1-proof.json](../target/lexicon/us1-proof.json)):
    307,243 source records, 307,243 validated quarantined dispositions, 263,014
    initial identities, 44,229 master records retained, 27 unknown source leads,
    and byte-identical independent inventory/stage replay (`clean_inventory_and_stage_replay_identical: true`).
    Total UTF-8 intake CSV size before projection is `504,384,984` bytes vs
    `581,570,653` bytes in the discarded escaped baseline (`legacy_csv_byte_baseline`),
    with payload duplication remaining in both representations.
  - Exact source-content proof ([source-content-proof-final.json](../target/lexicon/source-content-proof-final.json)):
    verifies 307,243 matching raw assertions, 44,229 master records, 0 missing or
    duplicate assertions, `exact_decoded_source_fields_and_scalars: true`,
    `subject_ids_match_immutable_allocations: true`, and 12 verified source hashes.
- **L2 structural pilot & fail-closed release guard**:
  - Representative projection & US2 proof ([us2-proof.json](../target/lexicon/us2-proof.json),
    [l2-acceptance.json](../target/lexicon/l2-acceptance.json)): 739 selected
    records (`101` primary entries; `20`–`22` per each of the 7 secondary files;
    `11` homograph spellings / `22` entries; `20` verbs; `74` mixed-sense records;
    `18` technical MWEs; `22` regional records spanning `17` TN and `5` Jaffna; all
    `9` observed audit issue classes). Post-projection editorial workspace counts:
    `264,402` identities, `243` entries, `609` forms, `363` senses, `637` texts,
    `1,458` scopes, `51` labels, `310,329` assertions/evidence, `966` findings,
    `0` decisions, `0` eligible assertions.
  - Structural validation CLI ([structural-final.json](../target/lexicon/structural-final.json)):
    exit `0`, `l2_structural_accepted: true`, `l3_pack_eligible: false`,
    `eligible_assertions: 0`, `runtime_verified: null`, `findings: []`.
  - Release validation fail-closed guard ([release-rejection-final.json](../target/lexicon/release-rejection-final.json)):
    exit `1`, `l2_structural_accepted: false`, `l3_pack_eligible: false`,
    `eligible_assertions: 0`, `NONEMPTY_ELIGIBLE_PACK_REQUIRED`.
- **Verification checks & outcomes**:
  - `just agent-post-edit` passed (exit `0`, [post-edit-utf8.log](../target/lexicon/post-edit-utf8.log)).
  - Focused lexicon tests: `120 passed, 156 deselected` ([focused-utf8-final.log](../target/lexicon/focused-utf8-final.log)).
  - Full `just agent-pre-stop-gate` passed (exit `0`, [pre-stop-utf8-final-retry.log](../target/lexicon/pre-stop-utf8-final-retry.log)):
    `cargo fmt --all -- --check`, `release_policy.py`, `check_source_unicode.py`
    (with `check_curated_csv`), numeral projections, 65 release source copies,
    `cargo check`, `cargo clippy` (`-D warnings`), `cargo nextest` (`182 passed, 1 skipped`),
    `277` pytest harness tests, rebuilt Python/WASM bindings, `36,161` Rust active
    golden vectors, `30` Python golden groups, and `36,185` WASM tests.
  - `dictionary_runtime_implemented: false`, `fixture_activation_changed: false`,
    `runtime_verified: null`. Dart host tests were not run for this host-only slice.
  - Note: Reproducible `--payloads-only` proof runs via `tools/lexicon_proof.py`;
    clean inventory/stage replay belongs **before** projection (`263,014` initial
    identities vs `264,402` post-projection identities).
- **Scheduling & next concrete action**:
  - **Phase 6 numerals work is now unblocked at L2** (structural acceptance grants
    no data-release, source/reuse, or runtime approval).
  - User selected **primary dictionary** for the Feature 021 provenance trace
    (`T038`, tracked in
    [primary-dictionary-provenance-2026-11-14.md](C:/Users/abish/Documents/dev/tamil-toolkit/docs/audits/primary-dictionary-provenance-2026-11-14.md),
    [utlkd-package-lineage-2026-11-14.md](C:/Users/abish/Documents/dev/tamil-toolkit/docs/audits/utlkd-package-lineage-2026-11-14.md),
    [wiktionary-snapshot-recovery-2026-11-14.md](C:/Users/abish/Documents/dev/tamil-toolkit/docs/audits/wiktionary-snapshot-recovery-2026-11-14.md),
    [primary-provenance-leads.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/primary-provenance-leads.json),
    and
    [evidence-index.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/evidence-index.json)).
    Whereas `tamil-toolkit` repo history holds no raw extraction or packaging
    scripts, read-only inspection of the supplied external package
    [utlkd_reusable_package](C:/Users/abish/Downloads/utlkd_reusable_package)
    matched all 12 frozen `tamil-lexicon` files byte-for-byte, linked the CSVs
    1-to-1 to `utlkd_primary.sqlite` (`44,229` lemmas / `63,633` meanings /
    `19,849` relationships; `README.md` `68,689`/`88,093`/`19,859` is stale),
    and recovered downstream CSV/30-col/FST builders (`export_all_datasets.py`,
    `master_30col_compiler.rs`, `fst_engine.rs`, `validate_final_distribution.py`),
    the macOS Apple Oxford extractor (`extract_apple_oxford_dictionary.py`),
    and an earlier v2.0 cleanup harness (`utlkd_harness.py`). Those scripts show
    packaging capability rather than upstream execution proof: web scrapers, the
    `22,128`-row Rust secondary-to-primary promotion pipeline, generators for
    transliteration, IPA (`921` DSAL non-`-தல்` verb IPA anomalies), and
    `12,021` `(கலைச்சொல்)` placeholders, and snapshot-specific reuse evidence
    remain missing, while owner SQLite tags conflict with DSAL (`CC BY-NC-ND 2.0`),
    Cre-A (`12`/`12`/`12` records), TVA/Sorkuvai, Tamilcube, and proprietary
    `SRC-OXFORD-APPLE`. Dedicated Wiktionary/Kaikki recovery (`SRC-WIKT-TAMIL`,
    `8,575` distinct `word_id`s union, `0` `source_evidence` rows, `27` of `101`
    pilot entries) confirmed `kaikki_tamil.jsonl`, ingestion scripts, and per-entry
    `pageid`/`revid` are missing. Sampled later revisions conflict with treating
    the entire merged slice as an unchanged 2024 extraction. October 2026 Kaikki
    is a candidate lead; template/module drift and possible later enrichment
    prevent proving a shared extraction interval or original file identity,
    and isolated `371` mixed DSAL/Wiktionary words, cross-page sense folding,
    POS collapsing, and broken algorithmic `verb_conjugations` (`அருள்வஆன்`).
    `T038` stays **pending**; next step is either owner recovery of original
    `kaikki_tamil.jsonl`/ingestion logs or root/`T039` scoping of an independent
    fresh candidate anchored to pinned `enwiktionary` dump (`20261001`/`20261101`)
    and `oldid` permalinks under CC BY-SA 4.0 / GFDL attribution rules. Existing
    material stays quarantined; genuine source and review decisions (`T039`)
    precede L3/L4 pack work (`T040`–`T070`).
  - **Separate pending 4-entry PRIMARY Wiktionary candidate created (2026-11-14)**:
    Under explicit user authorization, created an isolated candidate workspace in
    [data/curation/wiktionary-candidate/](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/README.md)
    (`dataset_id = wiktionary-en-tamil-candidate`, rebuilt offline via
    [lexicon_wiktionary_candidate.py](C:/Users/abish/Documents/dev/tamil-toolkit/tools/lexicon_wiktionary_candidate.py)
    and documented in
    [wiktionary-candidate-2026-11-14.md](C:/Users/abish/Documents/dev/tamil-toolkit/docs/audits/wiktionary-candidate-2026-11-14.md))
    for legacy `word_id`s `1921` (`அடடா`, `revid=85842017`), `3906` (`அந்நிலை`,
    `revid=89903937`), `8218` (`அறிக்கை`, `revid=88382210`), and `28857` (`செப்பம்`,
    `revid=61485513`), verified identically against both saved candidate checks and
    fresh `en.wiktionary.org` API responses (`2026-11-14T08:01Z` UTC).
    Preserves checked-in API/wikitext snapshots, Wikimedia/CC-BY-SA-4.0 notices
    and disclaimers (`ATTRIBUTION_AND_LICENSE.md`), `4` entries, `4` canonical
    written forms (`0` IPA forms), `16` senses, `24` assertions, `24` pending/review
    decisions (`4 pending`, `20 needs_review`, `0 accepted_human`, `0 accepted_auto_source`),
    `49` open review findings, explicit unpinned-template/etymology/synthetic-PDr/DEDR
    exclusions (`exclusions.json`), raw wikitext span/template provenance
    (`extraction_provenance.json`), and recorded schema gaps (`schema_gaps.json`).
    All 12 immutable `data/sources/tamil-lexicon/` files and `data/curation/tamil-lexicon/`
    remain untouched; `release_guard` stays fail-closed (`eligible_assertions: 0`,
    `l3_pack_eligible: false`, `runtime_verified: null`, `NONEMPTY_ELIGIBLE_PACK_REQUIRED`);
    `check_curated_csv` reports `0` structural findings; deterministic replay across
    `25` generated files shows `0` diffs (`target/lexicon/wiktionary-candidate/`);
    and `tests/harness/test_wiktionary_candidate.py` (`11 passed`) verifies tamper,
    unpinned `revid`, template-IPA injection, auto-accept rejection, protected-path
    rejection, and preservation of editorial changes before any rebuild writes.
    Post-edit passed; full pre-stop components through Clippy/Rust and all `288`
    harness tests passed. Its direct-Python invocation then failed to find
    `maturin` on PATH. The documented `uv run --locked python tools/tasks.py
    test-parity` then passed (exit `0`), including license checks, rebuilt Python
    and both WASM bindings, `36,161` Rust active vectors, `30` Python golden
    groups and `36,185` WASM tests. All pre-stop components passed across these
    runs; the original combined command exit remains `1`, not a claimed clean
    single-run pass. Evidence and log hashes are in
    `target/lexicon/wiktionary-candidate/checkpoint-root.json`. `T038`
    historical slice remains unverified (`[ ]`), and `T039`/`T040+` remain pending.

## Feature 021 reviewed core and canonical staging (2026-11-14)

- User approved the exact [six-entry / 19-sense decision sheet](../docs/reviews/wiktionary-core-decision.md) and separate CC-BY-SA-4.0 data-pack policy as reviewer `abish` on `2026-11-14`. The [approval receipt](../docs/reviews/wiktionary-core-approval-2026-11-14.json) binds 31 claims to packet SHA-256 `0b2168d07e9b45b5316994c1d97648ebf5de3ad666de050b10afbe5dfa58695b`.
- [Reviewed workspace](../data/curation/wiktionary-core-reviewed/README.md): six entries, 19 senses, 31 accepted-human claims, six core pack members. The two superseded assertions stay rejected and two structured scope proposals stay pending. The two நன்றி POS entries remain separate. No IPA or historical mixed-source bulk material is approved.
- Coordinator verified `verify --dataset reviewed` and release eligibility: six included entries, 31 eligible assertions, no blocking findings. `T038` and `T039` are checked for the fresh pinned-source route only. Pending candidate workspaces, approval packet and all 12 frozen originals remain preserved.
- Canonical notice closure is fixed and checked in `lexicon/dictionary/`: dataset `0.1.0+4d1309d05391`, manifest SHA-256 `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`, with required public attribution and CC legal text. Missing notices and unsafe paths fail validation; private raw API references are excluded. Two independent promotions are byte-identical and match the canonical tree.
- T040–T043 are complete: release closure/promotion, exact dev validator pins (`pycldf==2.2.0`, `csvw==4.2.0`), local CLDF 1.3 assets and the main `export-cldf` CLI. Independent real-data exports validate offline and round-trip six entries / 19 senses / 31 assertions without loss of canonical rows; two clean exports are byte-identical (`dbc9cd09b2c4d267f09ef25493656c7b99d25005614a2a326b632519d75dc54b`). Evidence: `target/lexicon/l3-host-proof.json` and `core-cldf-coordinator.json`. This proves canonical interchange, not transfer of complete private editorial history, compiled packs or runtime lookup.
- Coordinator integration tests: 41 pack/CLDF/lookup-contract tests passed. Source-backed planned goldens are being authored before compiler/runtime code. Source-archive data/license copying and compiled-pack acceptance remain pending; no fixture activation or registry publication is claimed.
- The source-backed [module contract](specs/lexicon-v0.1.md) precedes runtime implementation. Lookup ID/actor serialization regression tests pass (5 tests). The host focused pack/review/candidate/schema tests pass (107 tests); pilot tests and final integration gates still need completed results (the delegated pilot job was interrupted by a provider restart).

## Feature 021 analysis remediation (2026-11-13)

- User authorized fixing I1/U1/C1 and rerunning `speckit-analyze`. Preserved
  Feature 022 work and the 12 original intake files; no runtime implementation
  or new source/review approval is part of this documentation change.
- I1: T034 now tests only L2's actual zero-eligible release-rejection guard;
  T036 implements it before T037's unchanged full gate. Later release,
  promotion and CLDF tests are introduced with T040/T041/T043, not left failing
  across L2. Task IDs/count remain 70; no skip/xfail or weakened gate.
- U1: Added the closed nested response contract and explicitly schema-only
  example under `specs/021-lexicon-curation/contracts/lookup-response.*.json`.
  Required fields, null/availability rules, scope, provenance and decision
  types are specified before T044 goldens and T050/T052 runtime work. Example
  metadata is illustrative and cannot approve content or count as a golden.
- C1: T063 now measures complete inventory/staging/structural validation of
  all 307,243 CSV records and 12 hashes, with stage/end-to-end time, peak
  process-tree RSS, method/machine/input identity and target comparisons;
  lookup remains a separate workload. Plan, pack contract and quickstart agree.
- Verification passed: response schema/positive examples and 12 invalid
  response cases, 70 task IDs/paths/earlier-only dependencies, staged L2 test
  order, links/code fences, all four clarifications and all 12 source hashes.
  `agent-post-edit` passed (`target/lexicon-remediation-post-edit.log`) and
  `git diff --check` passed. No runtime/parity/archive support was implemented
  or claimed. Changes remain uncommitted.
- Next: complete the requested read-only `speckit-analyze` recheck; after a
  clean result, proceed to `speckit-implement` for the structural slice through
  T037, preserving external source/review gates for later work.

## Feature 022 reused-Rust & NFC/NFD validation handoff (2026-11-13)

- Completed full SpecKit lifecycle (`spec.md`, `research.md`, `data-model.md`,
  `contracts/`, `quickstart.md`, `tasks.md`, consistency analysis, and
  implementation) under [specs/022-validate-reused-rust-apis/](../specs/022-validate-reused-rust-apis/spec.md)
  to validate `tamil-core`, `tamil-norm`, and `tamil-toolkit` ahead of Feature
  021 without altering `specs/021-lexicon-curation/` or the 12 intake files.
- Verified `tamil-norm` NFC & NFD canonical normalization (Unicode 17.0.0 UAX
  #15 two-part vowels, CCC reordering, `ZWJ`/`ZWNJ`/`BOM`/`SHY` barriers,
  Shri distinctions, non-repair of malformed sequences, idempotence, and NFD vs
  NFC equivalence in `fold_for_search` and `repair_tamil_text`) with 30 new
  escaped active golden vectors ([norm_canonical.jsonl](../tests/golden/norm_canonical.jsonl)),
  10,000-case `proptest` invariants ([norm_tests.rs](../crates/tamil-norm/tests/norm_tests.rs)),
  and 23-consonant sweeps ([folding_tests.rs](../crates/tamil-norm/tests/folding_tests.rs),
  [repair_tests.rs](../crates/tamil-norm/tests/repair_tests.rs)).
- Validated Feature 021-reused `tamil-core` primitives and `inspect_tamil_string`
  joiner/NFD contracts ([phonology_tests.rs](../crates/tamil-core/tests/phonology_tests.rs)).
- Fixed `tamil-toolkit` dispatcher/CLI gaps uncovered during validation: added 9
  omitted implemented operations to `tamil_toolkit::OPERATIONS` ([lib.rs](../crates/tamil-toolkit/src/lib.rs))
  and fixed `norm fold --profile` strict rejection & flag ordering ([tamil-toolkit.rs](../crates/tamil-toolkit/src/bin/tamil-toolkit.rs)),
  backed by tests in [golden_suite.rs](../crates/tamil-toolkit/tests/golden_suite.rs).
- Next: Resume Feature 021 with `speckit-analyze` and implementation on
  [specs/021-lexicon-curation/tasks.md](../specs/021-lexicon-curation/tasks.md).

## Feature 021 tasks handoff (2026-11-13)

- Completed `speckit-tasks` using the resolved project template and all design
  artifacts. Created [tasks.md](../specs/021-lexicon-curation/tasks.md): 70
  unchecked tasks; US1 9, US2 14, US4 17, US3 16, with 14 setup/foundation/
  integration tasks. The equal-priority P2 stories place US4 packs before US3
  lookup so their dependencies point forward in execution order.
- T001–T018 is the traceable-intake MVP; T001–T037 is the structural L2 slice,
  permitting zero eligible content. Source/reuse recovery and actual reviewer
  decisions gate T038 onward; no synthetic fixture or all-quarantine pilot can
  satisfy nonempty L3/L4, activation, or archive criteria. All four clarification
  decisions remain intact; originals and implementation files are unchanged.
- Tasks include per-story independent tests, parallel waves/examples, field
  constraints, requirement/outcome traceability and explicit source/evidence/
  owner-activation boundaries. Generation creates no curated data, active suite,
  runtime implementation, registry publication or Git commit.
- Validation passed: 70 sequential IDs, required story labels and exact paths,
  earlier-only inline dependencies, 17 parallelizable tasks in explicit waves,
  all 22 requirements/eight outcomes mapped, four clarifications preserved,
  links/code fences, and all 12 original source hashes. `agent-post-edit`
  passed (`target/lexicon-tasks-post-edit.log`), as did `git diff --check`.
  No task hooks configured; no runtime/parity/archive completion is claimed.
- Next: `speckit-analyze` to check cross-artifact consistency, then implement
  the authorized structural slice using `speckit-implement`. Keep external
  evidence-gated work pending when inputs are unavailable, without weakening
  its acceptance conditions. Actual branch remains `master`; edits uncommitted.

## Feature 021 planning handoff (2026-11-13)

- Completed `speckit-plan` Phase 0 research and Phase 1 design. The setup
  script resolved feature context `021-lexicon-curation`; actual Git branch
  remains `master`. No branch switch, implementation, or task generation.
- Added [plan](../specs/021-lexicon-curation/plan.md), research, data model,
  curation/lookup/pack contracts, and quickstart in the same feature directory.
  Gemini 4 Hydrogen researched schema/editorial design; `gpt-6.1-sol` with
  `reasoningEffort=xhigh` researched Rust ownership and integration. Both
  completed read-only tasks; findings were consolidated with local/official
  source evidence.
- Design: immutable intake, editorial workspace, and only approved canonical
  projections; per-claim source/review decisions and repeatable identities;
  structural L2 permits zero eligible content; L3/L4 require a nonempty approved
  subset and actual runtime evidence. Runtime stays in the existing Rust facade
  with optional data features off by default and complete homograph postings.
- No source tables, runtime module, new Cargo dependencies, binding features,
  active suite, data pack, or public release were created. Proposed quickstart
  commands are explicitly marked unavailable until implementation. Source
  recovery remains an external data-approval dependency, not guessed evidence.
- Checks passed: `agent-post-edit` via `tools/tasks.py` (log:
  `target/lexicon-plan-post-edit.log`), `git diff --check`, links/code fences
  across seven design artifacts, four preserved clarifications and FR/SC IDs,
  no `tasks.md`, unchanged actual branch, and all 12 source hashes. Pre/post
  constitution checks pass at design level; full runtime/parity/archive gates
  remain unrun and required at implementation integration. No plan hooks exist.
- Task generation is recorded in the newer handoff above. Preserve the four
  clarification decisions and human review/reuse requirements during execution.

## Feature 021 specification handoff (2026-11-13)

- Clarification completed (four questions answered): Q1 answered B. Unchanged source-verified content
  may pass automated acceptance checks; corrections, inferred annotations,
  and ambiguous cases require human review. Recorded in Feature 021
  Clarifications, Story 2, FR-007, and SC-002. Automated acceptance is distinct
  from human linguistic review.
- Q2 answered A: exact lookup compares NFC-normalized input and accepted
  canonical spelling, returning identical ordered results for canonical
  equivalents. Original source text and controls remain preserved; repair and
  lossy folding are excluded. Recorded in Clarifications, Story 3, FR-013,
  and SC-004.
- Q3 answered A: region-filtered results include attested regional matches
  and explicitly reviewed geographically unrestricted entries, excluding
  unknown coverage. Missing region labels do not imply unrestricted usage;
  unfiltered lookup retains otherwise eligible unknown-coverage entries.
  Recorded in Clarifications, Story 3, FR-014, and SC-004.
- Q4 answered C: L2 requires the pilot sampling minima, completed structural
  review, and validated dispositions/accounting; zero release-eligible content
  is permitted. Unresolved evidence remains quarantined or excluded. Phase 6
  can resume after L2 acceptance; lexical consumer claims still require relevant
  L3-approved data and L4 runtime verification. Aligned Feature 021 and all
  three roadmap documents; source/reuse and human-review gates remain intact.
- Clarification validation: quality checklist 16/16 → 16/16, no marker changes;
  four accepted answers integrated without remaining conflicting pilot gates.
  `agent-post-edit` passed (`target/lexicon-clarify-post-edit.log`), as did
  whitespace, roadmap agreement/phase preservation, and all 12 source hashes.
  Operational performance/pack-size budgets remain planning work; proceed to
  `speckit-plan`. No clarification hooks configured or source files changed.
- User requested `speckit-specify`, Gemini Hydrogen and Sol xhigh subagents,
  and roadmap alignment for professional lexicon curation before numerals.
- Created [Feature 021](../specs/021-lexicon-curation/spec.md) and its
  [quality checklist](../specs/021-lexicon-curation/checklists/requirements.md).
  Gemini 4 Hydrogen and `gpt-6.1-sol` with `reasoningEffort=xhigh` completed
  read-only source/schema and integration/DAG reviews; recommendations are
  reflected in the specification and roadmap data gates.
- Updated `ROADMAP.md`, `docs/specs/architecture-roadmap.md`, and Feature 016
  with named lexicon milestones L0–L4, preserving Phase 0–17 and crate ranks.
  Phase 6 resumes after L2 structural-pilot acceptance; relevant L3-approved subsets
  gate morphology/dialect/spelling, with pronunciation evidence required for
  lexical G2P exceptions/evaluation. Independent tracks retain their scope.
- Specification checklist passes; no curated pilot, active lexicon runtime,
  new crate, suite activation, or publication is claimed. The 12 source files
  are preserved. `.specify/feature.json` selects Feature 021 locally (ignored
  by Git); branch remains `master`, with all session edits uncommitted.
- Verification passed: `agent-post-edit` via `tools/tasks.py` (log:
  `target/lexicon-spec-post-edit.log`), `git diff --check`, requirement/outcome
  completeness, identical L0–L4 roadmap text, preserved phase numbering/rank-6
  dependency rows, and all 12 original SHA-256 hashes. No runtime changes;
  full parity and archive tests were not rerun.
- Planning is now recorded in the newer handoff above. Recover source evidence
  while implementing the structural pilot after task generation.

## Lexicon intake (2026-11-13)

- Priority: organize the user-supplied lexicon before further numerals work.
- Moved the root `tamil-lexicon/` bundle to `data/sources/tamil-lexicon/`.
  All 12 original files are unchanged; SHA-256 comparisons passed after moving.
  Inventory: `data/sources/tamil-lexicon.sha256.json`; intake scope and pending
  reviews: `data/sources/README.md`.
- No runtime integration or release-data changes. Provenance, licensing,
  schema, Unicode, regional coverage, and FST reproducibility are unreviewed.
- Audit completed: [findings and plan](audits/lexicon-2026-11-13.md), with full
  metrics beside the report and a reusable `tools/audit_lexicon_source.py`.
  All CSVs parse; primary references and sense counts agree. FST integrity
  passes but stores one ID per spelling, omitting direct access to 398 entry
  IDs. Source records, sense extraction, annotation evidence, regional labels,
  and reproducible builds need work. All 12 original hashes still match.
- Checks: full-row audit and native Rust count comparison completed; isolated
  FST integrity/key export passed; `agent-post-edit` and `git diff --check`
  passed. Log: `target/lexicon-audit-post-edit.log`. No runtime change or new
  suite activation; full parity/release tests were not rerun.
- Owner reports public online sources combined with Python extraction.
  Exact URLs, extraction scripts, terms, and annotation origins remain unknown.
- Next: recover source/extraction records and use Feature 021 planning to define
  the canonical model and curate a representative pilot before bulk transformation.
  Relocation, audit tools/report, and intake notes remain uncommitted.

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

## Compiler handoff (2026-11-14)

T044 is verified: 44 ASCII-escaped planned cases validate against the golden schema, bound to core manifest `4d1309d05391be1087c11590d664b8669b49ef8312b6c32e4bb32aa86b135079`. Active coverage remains 36,161 vectors. Packaging copies/policy check pass (89 files), but focused packaging tests exposed an incomplete temporary policy fixture and missing Cargo PATH discovery; coordinator fixed those narrowly. Compiler work now starts after the source-backed expected cases, preserving existing package include/license edits. No activation or runtime acceptance is claimed.

## Rust compiler verification (2026-11-14)

Coordinator reran `lexicon_pack` under no-default-features and lexicon-core: 13/13 tests pass in each profile after the reviewed Unicode-exception fix. Independent clean target-directory builds prove zero default payload and byte-identical core artifacts: 50,923 bytes, SHA-256 `283e32d7b3dbfa11d1bedc201a95e90bcb064021dba96fd6a44a61491f5137ea`. Evidence: `target/lexicon/compiler-clean-proof.json`, `compiler-default-final.log`, `compiler-core-final.log`. Individual non-core features and all-features tests and focused clippy passed in the delegated logs; the exhaustive profile matrix and final L3 summary still need recording. Runtime lookup, binding support, activation and archive acceptance remain pending.

## L3 compiled core accepted (2026-11-14)

T045–T049 are complete: all 16 feature combinations pass, default payload is zero, two clean core builds are byte-identical (50,923 bytes), source/review/notice closure and independent CLDF round trips pass. `target/lexicon/l3-acceptance.json` binds these proofs to the reviewed six-entry / 19-sense core. Runtime lookup, actual binding parity, fixture activation and archive acceptance remain pending; 44 lookup vectors stay planned.
