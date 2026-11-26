# Tasks: Tamil Sandhi (`tamil-punarchi` — Complete Nannūl Eḻuttatikāram 117 Sūtras)

**Input**: Design documents from `/specs/025-tamil-punarchi/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/punarchi.md`, `quickstart.md`, and `research/00..05*.md`)
**Prerequisites**: All 117 primary-witness-audited *Nannūl* sūtras (`93–94`, `102–108`, `136`, `151–257`), pinned in `tests/reference/punarchi-nannool/sources.json`, verified across TVA 1999 *Viruttiyurai*, TVA Āṟumuka Nāvalar *Kāṇṭikaiyurai*, and Project Madurai `pmuni0147.html`.

**Tests**: Included as mandatory test-first golden vector & property tasks per Constitution Principle III (*Golden Vectors Precede Implementation*) and Principle VII (*10,000-case property tests & full quality gates*). Every golden vector must be generated/validated programmatically (zero hand-counted byte/unit offsets or unverified examples).

**Organization**: Tasks are grouped by user story (`US1`–`US4`) after Setup & Foundational phases so each increment is independently testable and verifiable. Suggested model delegation tags (`[Hydrogen-Med]` for repeatable/token-heavy TOML/fixture authoring and `[Neon]` for core algorithmic/precedence Rust) are noted in descriptions.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story label (`[US1]`, `[US2]`, `[US3]`, `[US4]`) — used only in User Story phases
- All file paths are relative to the repository root (`C:/Users/abish/Documents/dev/tamil-toolkit`)

---

## Phase 1: Setup (Crate Configuration, Manifest & Programmatic Fixture Tooling)

**Purpose**: Configure `crates/tamil-punarchi` as a Rank 2 workspace crate (`#![forbid(unsafe_code)]`), register planned operations in `tests/golden/manifest.json`, and build the programmatic golden-vector generator/validator before authoring any rule data.

- [X] T001 Configure Rank 2 dependencies (`tamil-core`, `tamil-norm`, `serde`), build-dependencies (`serde`, `toml`, `unicode-normalization`), and dev-dependencies (`serde_json`, `proptest`) keeping `publish.workspace = true` in `crates/tamil-punarchi/Cargo.toml`
- [X] T002 [P] Update the existing `planned` `punarchi_nannool.jsonl` suite entry to declare `operations: ["punarchi_join", "punarchi_split_candidates", "punarchi_rules"]` (keeping `"status": "planned"`) in `tests/golden/manifest.json`
- [X] T003 [P] Create standalone golden JSONL fixture loader (`load_punarchi_vectors`, chapter/operation filtering, escaped JSON deserialization) in `crates/tamil-punarchi/tests/support/mod.rs`
- [X] T004 [P] Create programmatic golden-vector compiler and validator (`--check` mode verifying NFC input, escaped non-ASCII JSONL output, globally unique `punarchi_*` IDs, witness provenance `viruttiyurai_pno`/`kandigai`/`extended_usage`, exact UTF-8 byte & written-unit offsets without hand counting, and zero copied commentary prose) in `tools/generate_punarchi_golden.py` `[Neon]`

**Checkpoint**: Crate manifest, planned golden registration, Rust test harness helper, and programmatic vector validator are ready.

---

## Phase 2: Foundational (117-Sūtra Inventory, Schema Compiler, Phonology & 4-Stage Pipeline Core — Milestone 10A)

**Purpose**: Core declarative data schema, build-time validation, phonology prerequisites (`93–94`, `102–108`, `205`), context validation, and the acyclic 4-stage pipeline skeleton.

**⚠️ CRITICAL**: No user story implementation can begin until this phase is complete and `inventory_completeness` passes.

- [X] T005 Author complete **117-sūtra** canonical inventory (`93, 94, 102..=108, 136, 151..=257` across `ezhuttiyal` [9], `padaviyal` [1], `uyireeru` [53], `meyyeeru` [36], `urupu` [18]) with exact `chapter`, `tier` (`phonological | closed_class | context_dependent | poetic_closed | definition_or_scope`), `executable` (`false` for `151–157, 239, 240, 241, 253`; `true` for executable rules and linked extensions of `238`/`257`), `tva_page` (`166..=303`), `kandigai_sutra`, `pm_ref`, concise factual `summary`, and all 12 verified `edition_note` entries (using readable NFC UTF-8 Tamil per Principle II) in `lexicon/punarchi-nannool-inventory.toml` `[Hydrogen-Med]`
- [X] T006 [P] Author declarative schema skeleton and core tables (`[metadata]` pinning `profile = "nannool-v1"` and `cross_check_sha256` matching `tests/reference/punarchi-nannool/sources.json`, all 17 `[[chariyai]]` entries from Sūtra `244`, all 6 oblique `[[case_suffix]]` entries from Sūtras `240–242` with `force_165 = true` on `கு` per `242.2`, and base `[[closed_class]]`/`[[rule]]` tables) in `lexicon/punarchi-nannool.toml` `[Hydrogen-Med]`
- [X] T007 Implement build-time TOML validator and static Rust codegen asserting: exact 117/117 sūtra uniqueness and chapter-range alignment, valid `tva_page`/`kandigai_sutra`, NFC validity of all Tamil stems, unique rule `id`, valid `substage` (`1a | 1b | 1c | 2 | 3a | 3b | 3c | 3d | 4`) and `evidence_layer` (`root_sutra | commentary_gloss | attested_example | extended_usage`), and forward referential integrity (every `[[rule]].sutra` exists in inventory with `executable == true`; strict reverse coverage of all `executable == true` sūtras activates in `T034` once Tiers A–D are populated) in `crates/tamil-punarchi/build.rs` `[Neon]`
- [X] T008 [P] Implement static compiled table accessors (`INVENTORY`, `RULES`, `CHARIYAIS`, `CASE_SUFFIXES`, `CLOSED_CLASSES`) including generated `OUT_DIR` tables in `crates/tamil-punarchi/src/tables.rs` `[Neon]`
- [X] T009 [P] Implement domain types and contract validator (`PunarchiProfile::NannoolV1`, `PunarchiChapter` [5 variants], `GrammaticalRelation` [`Unspecified | Vetrumai | Alvazhi`], `ContextSubtype` [6 *Vetrumai* `Case2..Case7` + 14 *Nannūl* 152 *Alvazhi* + `Imperative`, `SecondPersonVerb`, `Viyankol`, `Distributive`, `Ilakkanappoli`], `LexicalClass` [all 27 audited tags], `PunarchiContext` with `poetic: bool` defaulting `false`, `AlterationKind`, `DerivationStep`, `JoinAlternative`, `PunarchiJoinResult`, `SplitCandidate`, and `PunarchiError` emitting all 13 exact contract error strings from `contracts/punarchi.md`) in `crates/tamil-punarchi/src/context.rs` `[Neon]`
- [X] T010 [P] Implement prerequisite phonology & phonotactics over `tamil-core` (`classify_ugaram` exact Sūtra `94` decision tree distinguishing all 6 *Kurriyalugaram* classes from 2-letter `CVCu` *Mutriyalugaram* `பசு/புது/அது/தெரு/கடு`, `is_kurriyaligaram_context` Sūtra `93`, `is_valid_mozhi_muthal` Sūtras `102–106` with `வ`[8]/`ய`[6]/`ஞ`[4]/bound `ஙனம்`, `is_valid_mozhi_eetru` Sūtras `107–108` with 12 vowels + 11 pure consonants excluding `C+எ`, `C+ஒ`≠`நொ`, `C+ஔ`∉`{கௌ,வௌ}`, `is_thanikkuril_otru` Sūtra `205`, and boundary non-Tamil/`ZWJ`/`ZWNJ` barrier detector over `tamil_core::Letters`) in `crates/tamil-punarchi/src/phonology.rs` `[Neon]`
- [X] T011 Implement core acyclic 4-stage forward pipeline (`BoundaryFlags`: `is_derived_final`, `block_165`, `force_165`, `suppress_205`, `is_chariyai_attu`, `triggered_237`; Stage 0 validation/barrier passthrough/NFC; Stage `1A→1B→1C` hooks; Stage `2` left-to-right multi-segment fold; Stage `3A→3B→3C→3D` hooks; Stage `4` Sūtra `204` `compose_uyirmei` fusion + `tamil_norm::normalize_nfc`; branch deduplication by `(surface, rule_ids)`; canonical priority sorting; and `punarchi_rules` filter query) in `crates/tamil-punarchi/src/pipeline.rs` `[Neon]`
- [X] T012 [P] Write inventory completeness & schema contract test verifying all 117 sūtras (`93–94, 102–108, 136, 151..=257`), all 12 `edition_note` entries, exact chapter counts, forward rule-to-inventory integrity, and all 13 validation error messages (with the reverse zero-unmapped-executable assertion enabled in `T034`) in `crates/tamil-punarchi/tests/inventory_completeness.rs` `[Hydrogen-Med]`
- [X] T013 [P] Write prerequisite phonology & error-contract golden vectors (`93` *Kurriyaligaram*, `94` 6-class vs *Mutriyalugaram*, `102–108` phonotactics, and contract error rows) into `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` and write `crates/tamil-punarchi/tests/prereq_golden.rs` `[Hydrogen-Med]`
- [X] T014 Verify Phase 2 foundation: run `just check-unicode`, `uv run --locked python tools/generate_punarchi_golden.py --check`, and `cargo test --locked -p tamil-punarchi --test inventory_completeness --test prereq_golden`

**Checkpoint**: Foundation complete — all 117 sūtras validated at build time, phonology `93–94`/`102–108`/`205` and 4-stage pipeline skeleton proven. User story phases can begin.

---

## Phase 3: User Story 1 — Join Two Tamil Words with a Complete *Nannūl* Rule Trace (Priority: P1) 🎯 MVP

**Goal**: Deliver accurate forward joining with ordered sūtra derivation traces across core phonological *Uyirīṟṟup Puṇariyal* and *Meyyīṟṟup Puṇariyal* boundaries — including *Iyalbu*, *Udambadumei*, *Kurriyalugaram*/*Kurriyaligaram*, *Udalmel Uyir*, *Thanikkuril Otru*, *Magara* deletion/assimilation, `ய்/ர்/ழ்`, and all 12 `237`-interaction outputs (`ற்ற/ட்ட/ன்ற/ண்ட/ன்ன/ண்ண/ஃற/ஃட` + post-`210`/`229` singletons `ற/ட/ன/ண`).

**Independent Test**: Run `uyireeru_golden` and `meyyeeru_golden` on core phonological pairs (`மணி+அடி→மணியடி`, `பூ+இதழ்→பூவிதழ்`, `நாகு+அரிது→நாகரிது`, `நாகு+யாது→நாகியாது`, `கல்+அடி→கல்லடி`, `தமிழ்+அம்மா→தமிழம்மா`, `மரம்+வேர்→மரவேர்`, `கல்+சிலை→கற்சிலை`, `முள்+செடி→முட்செடி`, `அல்+திணை→அஃறிணை`, `வேல்+தீது→வேறீது`, `வாள்+தீது→வாடீது`, `தூண்+நன்று→தூணன்று`, `பொன்+மணி→பொன்மணி`, decomposed NFD equivalents, and `ZWJ`/`ZWNJ`/non-Tamil *Iyalbu* passthrough) and verify exact `surface`, `transform`, and `steps`.

### Tests for User Story 1 (Golden Vectors First — Must Fail Before Implementation) ⚠️

- [X] T015 [P] [US1] Author witness-backed escaped golden vectors for core *Uyirīṟṟup Puṇariyal* (`153`, `158`, `162`, `164` incl. `93` *Kurriyaligaram* & `164.3` *Mutriyalugaram* optionality, `165`, `181–183` incl. `ஆடு+கால்→ஆட்டுக்கால்` & `காடு+எருமை→காட்டெருமை`, NFD equivalence, `ZWJ`/`ZWNJ`/non-Tamil passthrough, and `COMMON`/`TN`/`SL` invariance) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T016 [P] [US1] Author witness-backed escaped golden vectors for core *Meyyīṟṟup Puṇariyal* (`204–205`, `209–210`, `219–220`, `224` incl. `காய்+யாது→காயாது`, `227–229` incl. `117` `*ல்த/*ள்த` ban, and all 12 `237` surface clusters/singletons: `ற்ற/ட்ட/ன்ற/ண்ட/ன்ன/ண்ண/ஃற/ஃட/ற/ட/ன/ண`) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T017 [P] [US1] Write standalone chapter test runners asserting exact `surface`, `transform`, and ordered `steps` for core US1 vectors in `crates/tamil-punarchi/tests/uyireeru_golden.rs` and `crates/tamil-punarchi/tests/meyyeeru_golden.rs` `[Hydrogen-Med]`

### Implementation for User Story 1

- [X] T018 [P] [US1] Populate core phonological *Uyirīṟṟu* (`93, 153, 158, 162, 164, 165, 181–183`) and *Meyyīṟṟu* (`204–205, 209–210, 219–220, 224, 227–229, 237`) declarative rule entries with exact `substage`, `priority`, and `evidence_layer` in `lexicon/punarchi-nannool.toml` `[Hydrogen-Med]`
- [X] T019 [US1] Implement Stage `1C` (`183` pre-elision `டு/று→ட்டு/ற்று` with `force_165` unlock) and Stage `3C` core vowel-final rules (`93+164 > 162` for *Kurriyalugaram*; `162 > opt 164.3` for *Mutriyalugaram*; `158` `குறில்+ய்`/`தனி ஐ`/`நொ`/`து` doubling; `181–182` blockers; `165` default *Valimigal* respecting `block_165`/`force_165`/`is_derived_final`) in `crates/tamil-punarchi/src/uyireeru.rs` `[Neon]`
- [X] T020 [US1] Implement Stage `3B` pre-mutation `237` (`ன்/ல் + த/ந → ற/ன`, `ண்/ள் + த/ந → ட/ண` setting `triggered_237`), Stage `3C` core consonant-final rules (`209–210`, `219–220`, `224`, `227–229` enforcing `117` cluster ban against `*ல்த/*ள்த`), Stage `3D` `205` *Thanikkuril Otru* (respecting `suppress_205`), and Stage `4` `204` fusion in `crates/tamil-punarchi/src/meyyeeru.rs` `[Neon]`
- [X] T021 [US1] Wire `uyireeru` and `meyyeeru` modules into `crates/tamil-punarchi/src/pipeline.rs` and export `punarchi_join` and `punarchi_rules` in `crates/tamil-punarchi/src/lib.rs` `[Neon]`
- [X] T022 [US1] Verify US1 MVP independently: run `just check-unicode` and `cargo test --locked -p tamil-punarchi --test uyireeru_golden --test meyyeeru_golden`

**Checkpoint**: User Story 1 (MVP) is complete and independently verified across all core phonological *Uyirīṟṟu* and *Meyyīṟṟu* rules, including all 12 `237` surface outputs.

---

## Phase 4: User Story 2 — Join Closed-Class Stems, *Panpuppeyar* (`136`), Directions, Numerals, Pronouns & Case Suffixes (Priority: P2)

**Goal**: Deliver 100% dictionary-free declarative support for all closed word classes in *Nannūl* — *Panpuppeyar* `-மை` cascade (`136`), demonstratives/interrogatives (`163`, `235`, `250–251`, `257`), cardinal directions & `தெங்கு` (`186–187`), complete numeral compounding (`188–199`, `249`), all named special stems (`168–170`, `174–175`, `177–178`, `184–185`, `200`, `202–203`, `213–218`, `221–223`, `225–226`, `231–234`, `236`, `248`), pronouns & quantifiers (`238`, `245–247`), and all 17 *Chariyais* with multi-segment left-to-right folding (`240–257`, including `252` `அத்தின் அகரம்`, `247.5`/`250.3` anti-gemination, `254` `இன்` filter, and `242.2` `கு`/`கண்` asymmetry).

**Independent Test**: Run `prereq_golden`, `uyireeru_golden`, `meyyeeru_golden`, and `urupu_golden` on multi-step closed-class & case-suffix pairs (`செம்மை+தாமரை→செந்தாமரை`, `பசுமை+தமிழ்→பைந்தமிழ்`, `சிறுமை+ஊர்→சிற்றூர்`, `மரம்+ஐ→மரத்தை` with `219→244→252→164→204`, `மக+அத்து+கை→மகத்துக்கை`, `பல+ஐ→பலவற்றை`, `அவ்+ஐ→அவற்றை`, `எவ்+ஐ→எவற்றை`, `எல்லாம்+ஐ→எல்லாவற்றையும்`/`எல்லாநம்மையும்`, `எல்லாரும்+ஐ→எல்லார்தம்மையும்`/`எல்லாரையும்`, `யான்/நான்+கு→எனக்கு`, `தான்+கு→தனக்கு`, `தான்+அது→தனது`, `நீ+ஐ→நின்னை`/`உன்னை`, `ஒன்பது+பத்து→தொண்ணூறு`, `ஒன்பது+நூறு→தொள்ளாயிரம்`, `பத்து+இரண்டு→பன்னிரண்டு`, `வடக்கு+கிழக்கு→வடகிழக்கு`, `மேற்கு+திசை→மேற்றிசை`, `தெங்கு+காய்→தேங்காய்`, `நாழி+உரி→நாடுரி`, `அ+அணி→அவ்வணி`, `நாடு+இன்→நாட்டின்` [no `*நாட்டினின்`]).

### Tests for User Story 2 (Golden Vectors First — Must Fail Before Implementation) ⚠️

- [X] T023 [P] [US2] Author witness-backed escaped golden vectors for *Panpuppeyar* `-மை` (`136`), demonstratives/interrogatives (`163` incl. `R163.4` `விண்வத்து`/`செல்வுழி`/`சார்வுழி`), directions (`186` incl. `மேற்றிசை` vs `229` & `மேனாடு`), `தெங்கு` (`187`), all numeral rules (`188–199`), and named *Uyirīṟṟu* stems (`168–170`, `174–175`, `177–178`, `184–185`, `200`, `202–203`) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T024 [P] [US2] Author witness-backed escaped golden vectors for named *Meyyīṟṟu* stems (`213–218`, `221–223`, `225–226`, `231–236`, `238` *Vetrumai* content-word delegation) and all *Urupu Puṇariyal* rules (`240–257`, multi-segment stacked *Chariyais* `அற்று+இன்`, `அத்து+இன்+உ`, `வ்+இன்+உ`, `அன்+உ`, `ன்+அ`, `உம்` post-positioning `245–246`, `247` + `247.5` anti-gemination + extended `நான்→என்`, `248`, `249`, `250.3` anti-gemination, `251`, `252`, `254` `இன்`-blocking & `242.2` `கு`/`கண்` asymmetry, `257` `எவ்→எவற்றை`) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T025 [P] [US2] Write *Urupu Puṇariyal* golden suite in `crates/tamil-punarchi/tests/urupu_golden.rs` and expand `prereq_golden.rs` (`136`), `uyireeru_golden.rs`, and `meyyeeru_golden.rs` to cover all US2 vectors `[Hydrogen-Med]`

### Implementation for User Story 2

- [X] T026 [P] [US2] Populate all closed-class stem sets, oblique maps, multi-segment *Chariyai* rules, and named-stem rules (`136`, `163`, `168–170`, `174–175`, `177–178`, `184–200`, `202–203`, `213–218`, `221–223`, `225–226`, `231–236`, `238`, `242–252`, `254`, `257`) in `lexicon/punarchi-nannool.toml` `[Hydrogen-Med]`
- [X] T027 [US2] Implement Stage `1A` *Panpuppeyar* `-மை` 8-operation ordered cascade (`136`), Stage `1B` closed-class stem reductions (numeral priority chain `199 > 194 > 198 > 196 > 197 > 195 > 188–193`, directions `186` with `மேற்+திசை→மேற்றிசை` `229`-bypass guard, `187`, pronouns `247`/`238` with `247.5` `suppress_205` & `extended_usage` `நான்→என்`, `170` self-compound bypass, and named stems `168–169, 174, 177, 203, 222, 233`), and Stage `1C` (`184–185`) in `crates/tamil-punarchi/src/closed_class.rs` `[Neon]`
- [X] T028 [US2] Implement Stage `2` *Urupu Puṇariyal* *Chariyai* staging, stacked *Chariyai* expansion, `உம்` post-positioning (`245–246`), `238` *Vetrumai* content-word delegation (`245–251`), `248–251`/`257` stem-chariyai rules (setting `250.3` `suppress_205` on `அவ்/இவ்/உவ்/எவ்`), `254` `இன்`-before-`இன்` hard filter & `242.2` `கு`/`கண்` `force_165` asymmetry, and stem-level `உ`/`அ`/`அம்` increments (`202, 207–208, 212, 215, 217, 223, 225, 231, 234, 236`) in `crates/tamil-punarchi/src/urupu.rs` `[Neon]`
- [X] T029 [US2] Implement Stage `3A` overrides (`252` `அத்தின் அகரம்` strictly before `162`, and `163` demonstratives/interrogatives + `106` bound `ஙனம்` + `R163.4` non-*udambadumei* `வ்` strictly before `162`/`158`) plus Stage `3C` named exceptions (`175`, `178`, `200`, `213–218`, `221–223`, `225–226`, `231–236`) and connect `closed_class` + `urupu` into `crates/tamil-punarchi/src/pipeline.rs`, `uyireeru.rs`, and `meyyeeru.rs` `[Neon]`
- [X] T030 [US2] Verify US2 independently: run `just check-unicode` and `cargo test --locked -p tamil-punarchi --test prereq_golden --test uyireeru_golden --test meyyeeru_golden --test urupu_golden`

**Checkpoint**: User Stories 1 and 2 pass independently — all 117 sūtras' phonological and closed-class rules compose end-to-end with zero external dictionary.

---

## Phase 5: User Story 3 — Control Grammatical Context, Ambiguity Reporting & Opt-In Poetic Mode (Priority: P3)

**Goal**: Deliver full two-level `PunarchiContext` disambiguation (`Vetrumai` vs `Alvazhi`, all 25 `ContextSubtype` values, all 27 `LexicalClass` tags), deterministic primary + labeled `alternatives` reporting whenever context is omitted or *Nannūl* permits optionality (`உறழ்வு`/`விகற்பம்`), commentary-preferred priority ordering (`161, 175, 206, 211, 226`), and opt-in closed-form poetic rules (`163.3, 172.1, 173, 180, 222 அஞ்சிறை, 243.3`).

**Independent Test**: Submit ambiguous pairs (`பொன்+தகடு`, `கல்+குறிது`, `ஏ+அடி`, `மரம்+குளம்`, `நம்பி+கை` vs `நம்பி+கு`, `உண்ணா+குதிரைகள்`, `கிளி+குறிது`, `அங்கு+கொண்டான்` vs `அன்று+கண்டான்`, `வேள்+யாவன்`, `அது+அன்று`, `நிலா+விரி`, `அன்றி+பிடியா`, `மாடம்+கு`) with (a) omitted context confirming primary + labeled `alternatives`, (b) explicit context confirming exact single selection, and (c) `poetic: false` vs `poetic: true` confirming verse-only rules stay inactive by default.

### Tests for User Story 3 (Golden Vectors First — Must Fail Before Implementation) ⚠️

- [X] T031 [P] [US3] Author witness-backed escaped golden vectors for context disambiguation, ambiguity `alternatives`, commentary-preferred optionality (`159–161`, `166–167` all 6 `அ`-final classes, `171`, `175–176`, `179`, `181` locative vs temporal particles, `201` `ஏ/ஓ` directionality, `206` contested minority behind `158`, `207–208`, `211–212`, `220`, `226`, `229–230`, `255–256`), and closed-form poetic opt-in (`163.3`, `172.1`, `173`, `180`, `222` `அஞ்சிறை`, `243.3`) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T032 [P] [US3] Write context-disambiguation, ambiguity-ranking, and poetic-gating test suite in `crates/tamil-punarchi/tests/context_ambiguity_golden.rs` `[Hydrogen-Med]`

### Implementation for User Story 3

- [X] T033 [P] [US3] Populate remaining Tier C context-dependent rules (`159–161, 166–167, 171, 176, 179, 201, 206–208, 211–212, 230, 255–256`) and Tier D closed-form poetic rules (`163.3, 172.1, 173, 180, 222 அஞ்சிறை, 243.3`) with explicit commentary-preferred `priority` weights (`161`, `175`, `206`, `211`, `226`) in `lexicon/punarchi-nannool.toml` `[Hydrogen-Med]`
- [X] T034 [US3] Complete context-conditioned filtering, `required_context`/`optional_variant`/`poetic` alternative labeling, commentary-preferred primary tie-breaking, and strict `poetic: bool` gating (ensuring `177, 228, 235, 255` remain active when `poetic: false` and `206` emits as optional alternative behind `158`) across `crates/tamil-punarchi/src/pipeline.rs`, `uyireeru.rs`, `meyyeeru.rs`, and `urupu.rs`, and enable the strict reverse completeness assertion (zero unmapped `executable == true` sūtras across all 117 sūtras) in `crates/tamil-punarchi/build.rs` and `crates/tamil-punarchi/tests/inventory_completeness.rs` `[Neon]`
- [X] T035 [US3] Verify US3 independently: run `just check-unicode` and `cargo test --locked -p tamil-punarchi --test inventory_completeness --test context_ambiguity_golden`

**Checkpoint**: User Stories 1, 2, and 3 pass independently — full 117-sūtra forward Sandhi engine is context-exact, ambiguity-transparent, and poetic-safe.

---

## Phase 6: User Story 4 — Dictionary-Free Reverse Split Candidate Generation & 10,000-Case Properties (Priority: P4)

**Goal**: Deliver `punarchi_split_candidates(surface, profile, poetic)` inverting all **28 reversible surface pattern families** from `research/05-precedence-and-inverse-matrix.md` §3 at exact `tamil_core::Letters` written-unit boundaries, dual-pruned by *Nannūl* `102–108` *Mozhi-muthal*/*Mozhi-eetru* phonotactics + forward-join verification, capped at 256 UTF-8 bytes, and proven with 10,000-case property tests.

**Independent Test**: Run `split_golden` (covering all 28 inverse patterns, `கல்லடி` with `split_byte: 9, split_unit: 2`, all 12 `237` clusters/singletons `கற்றீது/முட்டீது/பொன்றீது/மண்டீது/கன்னன்று/மண்ணன்று/கஃறீது/முஃடீது/வேறீது/வாடீது/தூணன்று/அரசனல்லன்`, *Kurriyaligaram* `நாகியாது`, *Panpuppeyar* `செந்தாமரை/பைந்தமிழ்/சிற்றூர்`, *Chariyai* + `உம்` `மரத்தை/பலவற்றை/எல்லாவற்றையும்/எல்லாநம்மையும்/எல்லார்தம்மையும்/அவற்றை/எவற்றை`, oblique pronouns `எனக்கு/தனக்கு/தன்னை`, `-Cஉ/-Cஅ` increments, `காயாது`, ligature `க்ஷ`/`ஸ்ரீ` atomic safety, single-unit/non-Tamil `[]`, >256-byte error) and 10,000-case `roundtrip_properties`.

### Tests for User Story 4 (Golden Vectors & Properties First — Must Fail Before Implementation) ⚠️

- [X] T036 [P] [US4] Author witness-backed escaped reverse-split golden vectors covering all 28 inverse pattern families, exact programmatically computed `split_byte`/`split_unit` coordinates (e.g., `கல்லடி` `split_byte: 9, split_unit: 2`), multi-rule ambiguity (`ற்` → `ல்/ன்/ற்`), phonotactic pruning (rejecting impossible word-initial `ட்/ண்/ற்/ள்` and word-final stops), ligatures `க்ஷ`/`ஸ்ரீ`, empty `[]` on single-unit/non-Tamil input, and >256-byte error (`"punarchi: surface input exceeds maximum length"`) in `tests/golden/punarchi_nannool.jsonl` via `tools/generate_punarchi_golden.py` `[Hydrogen-Med]`
- [X] T037 [P] [US4] Write reverse-split golden test suite in `crates/tamil-punarchi/tests/split_golden.rs` `[Hydrogen-Med]`
- [X] T038 [P] [US4] Write 10,000-case `proptest` round-trip and integrity suite verifying: 100% forward→split round-trip recall on reversible rules across all 28 pattern families, exact `split_byte`/`split_unit` alignment on `tamil_core::Letters` boundaries (zero mid-`க்ஷ`/`ஸ்ரீ`/vowel-sign cuts), `102–108` phonotactic validity, NFC/NFD equivalence, `ZWJ`/`ZWNJ`/non-Tamil verbatim preservation, and bounded deterministic output in `crates/tamil-punarchi/tests/roundtrip_properties.rs` `[Neon]`

### Implementation for User Story 4

- [X] T039 [US4] Implement dictionary-free single-boundary reverse candidate generator covering all 28 inverse pattern families (`153`, `204`, `205`, `162`, `164`+`94`, `93`+`206`, `165/163/170/175/178/200/203/219/220`, `224/226`, `158/106/221/235`, `166/202/214`, all 12 `237` clusters/singletons `ற்ற/ட்ட/ன்ற/ண்ட/ன்ன/ண்ண/ஃற/ஃட/ற/ட/ன/ண`, `ற்/ட்+க/ச/ப`, `ன்/ண்+ஞ/ம`, `ஃ+க/ச/த/ப`, `219` post-`ம்` deletion, `252` `-த்து-/-த்த்-`, `243–253/257` *Chariyai* + case + `உம்`, `247` oblique pronouns, closed-class `136/168–170/172–174/177/184–199/202–203/214/222/233/236`, `-Cஉ/-CCஉ/-Cஅ` increments `207–208/212/215/217/223/225/231/234/236`, and `224` non-*Thanikkuril* `ய்` deletion) with dual pruning (`phonology::is_valid_mozhi_eetru`/`is_valid_mozhi_muthal` + forward-join verification), 256-byte input cap, deduplication by `(first, second, primary_sutra)`, and deterministic `(split_byte, sutra, first, second)` ordering in `crates/tamil-punarchi/src/split.rs` `[Neon]`
- [X] T040 [US4] Export `punarchi_split_candidates` and finalize crate documentation/exports (`#![forbid(unsafe_code)]`, zero `STATUS = "planned"` stub) in `crates/tamil-punarchi/src/lib.rs` `[Neon]`
- [X] T041 [US4] Verify US4 independently: run `just check-unicode` and `cargo test --locked -p tamil-punarchi --test split_golden --test roundtrip_properties`

**Checkpoint**: All four user stories (`US1`–`US4`) pass independently in standalone Rust with 10,000-case property verification!

---

## Phase 7: Polish, Preactivation Multi-Runtime Parity & Reviewed Integration (Milestone 10E)

**Purpose**: Complete standalone Rust quality gates, run isolated preactivation multi-runtime parity across Rust/Python/Node-WASM/Browser-WASM/Dart BEFORE activating fixtures or editing release policy, present readable Tamil review for owner approval, and finalize documentation/release sync.

- [X] T042 Run full standalone Rust verification (`cargo fmt --all -- --check`, `cargo clippy --locked -p tamil-punarchi --all-targets -- -D warnings`, `cargo test --locked -p tamil-punarchi`, `just check-unicode`) and measure observed join/split latencies for `docs/specs/punarchi-nannool-v1.md` `[Neon]`
- [X] T043 [P] Run independent adversarial verification pass over `lexicon/punarchi-nannool-inventory.toml`, `lexicon/punarchi-nannool.toml`, and `tests/golden/punarchi_nannool.jsonl` checking 117/117 sūtra linkage, witness provenance, and zero fabricated examples `[Hydrogen-Med]`
- [X] T044 Create isolated preactivation candidate integration (keeping `punarchi_nannool.jsonl` `planned` and `release-policy.toml` unchanged): wire `punarchi_join`, `punarchi_split_candidates`, and `punarchi_rules` into `crates/tamil-toolkit/Cargo.toml` and `crates/tamil-toolkit/src/lib.rs`, and verify `tools/mcp-tamil-oracle/` cleanly forwards all three operations through `tamil_toolkit::execute` `[Neon]`
- [X] T045 [P] Wire thin serialization adapters & type stubs for `punarchi_join`, `punarchi_split_candidates`, and `punarchi_rules` in `bindings/python/python/tamil_toolkit/__init__.py`, `bindings/python/python/tamil_toolkit/__init__.pyi`, and `bindings/python/tests/test_golden.py` `[Hydrogen-Med]`
- [X] T046 [P] Wire thin serialization adapters & TypeScript declarations for `punarchi_join`, `punarchi_split_candidates`, and `punarchi_rules` in `bindings/js-wasm/src/api.ts`, `bindings/js-wasm/src/index.ts`, `bindings/js-wasm/src/web.ts`, and `bindings/js-wasm/tests/golden.test.ts` `[Hydrogen-Med]`
- [X] T047 [P] Wire thin C ABI wrappers & tests for `punarchiJoin`, `punarchiSplitCandidates`, and `punarchiRules` in `bindings/dart-flutter/lib/tamil_toolkit.dart` and `bindings/dart-flutter/test/golden_test.dart` `[Hydrogen-Med]`
- [X] T048 Execute full 4-runtime preactivation parity with `TAMIL_GOLDEN_INCLUDE_PLANNED=punarchi_nannool.jsonl` (Rust `tamil-toolkit`, `tools/mcp-tamil-oracle/` dispatcher smoke check, Python `maturin` + `pytest`, Node & Browser `wasm-pack` + `pnpm test`, Dart `dart analyze` + `dart test`, plus Python smoke test on `மரம்+ஐ→மரத்தை` & `கல்லடி`) per `specs/025-tamil-punarchi/quickstart.md` §3
- [ ] T049 **OWNER REVIEW GATE**: Present readable Tamil golden fixture summary, 117-sūtra inventory coverage report, measured latencies, and proposed release-policy diff to the repository owner for explicit approval before activating `tests/golden/punarchi_nannool.jsonl` or editing `release-policy.toml`
- [ ] T050 (Post owner approval) Activate `punarchi_nannool.jsonl` (`"status": "active"`) in `tests/golden/manifest.json`, wire `tools/generate_punarchi_golden.py --check` into `tools/tasks.py` (`just check-unicode`), and add `tamil-punarchi` (Rank 2) to `release-policy.toml`, `tools/release_files.py`, and `.github/workflows/publish-crate.yml`
- [ ] T051 [P] (Post owner approval) Author active module contract & verification record in `docs/specs/punarchi-nannool-v1.md`, update `docs/status.md`, `CHANGELOG.md`, `README.md`, and `ROADMAP.md` `[Hydrogen-Med]`
- [ ] T052 (Post owner approval) Run final canonical release gates per `quickstart.md` §4: `just sync-release-files`, `just agent-pre-stop-gate`, `just test-dart`, `uv run --locked python tools/release.py all --lexicon-profile default`, and `uv run --locked python -m tools.lexicon_dart_archive --profile default`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup: T001–T004)**: No dependencies — starts immediately.
- **Phase 2 (Foundational: T005–T014)**: Depends on Phase 1 — **BLOCKS all user stories** (`US1`–`US4`).
- **Phase 3 (`US1` MVP: T015–T022)**: Depends on Phase 2. Independently testable core forward engine.
- **Phase 4 (`US2`: T023–T030)**: Depends on Phase 3 (`US1` core Stage 3–4 boundary rules feed Stage 1–2 closed-class & *Chariyai* folding).
- **Phase 5 (`US3`: T031–T035)**: Depends on Phase 4 (context disambiguation & poetic gating operate over all Stage 1–4 rules).
- **Phase 6 (`US4`: T036–T041)**: Depends on Phase 5 (`split.rs` forward-verification pruning calls the complete forward engine from `US1`–`US3`).
- **Phase 7 (Polish & Multi-Runtime Integration: T042–T052)**: Depends on Phases 3–6, gated by T049 Owner Review before T050–T052.

### Parallel Opportunities

- **Phase 1**: `T002`, `T003`, `T004` run in parallel after `T001`.
- **Phase 2**: `T005` + `T006` in parallel; `T008` + `T009` + `T010` in parallel; `T012` + `T013` in parallel.
- **Phase 3 (`US1`)**: `T015` + `T016` + `T017` (vectors & test harnesses) in parallel; `T018` in parallel with test setup; `T019` (`uyireeru.rs`) and `T020` (`meyyeeru.rs`) can be drafted in parallel before `T021` integration.
- **Phase 4 (`US2`)**: `T023` + `T024` + `T025` in parallel; `T026` (TOML) before `T027` (`closed_class.rs`) + `T028` (`urupu.rs`).
- **Phase 5 (`US3`)**: `T031` + `T032` + `T033` in parallel before `T034`.
- **Phase 6 (`US4`)**: `T036` + `T037` + `T038` in parallel before `T039`.
- **Phase 7**: `T045` (Python), `T046` (JS/WASM), and `T047` (Dart) run in parallel immediately after `T044` (`tamil-toolkit` dispatcher wiring).

### Parallel Example: Phase 4 (User Story 2)

```text
# Parallel batch 1 (Hydrogen Medium — golden vectors & test runners first):
T023: Author Panpuppeyar/direction/numeral/Uyireeru closed-class vectors in tests/golden/punarchi_nannool.jsonl
T024: Author Meyyeeru named-stem & Urupu Chariyai vectors in tests/golden/punarchi_nannool.jsonl
T025: Create crates/tamil-punarchi/tests/urupu_golden.rs and expand chapter suites

# Parallel batch 2 (Neon — Stage 1 & Stage 2 engines once T026 TOML compiles):
T027: Implement Stage 1A/1B/1C closed-class transforms in crates/tamil-punarchi/src/closed_class.rs
T028: Implement Stage 2 Chariyai & case staging in crates/tamil-punarchi/src/urupu.rs
```

### Implementation Strategy

1. **MVP First (`Phase 1 → Phase 2 → Phase 3 / US1`)**: Delivers a build-verified 117-sūtra inventory, exact Sūtra `94`/`102–108` phonology, and core phonological forward Sandhi covering all 12 `237` surface outputs.
2. **Incremental Chapter Delivery (`US2 → US3 → US4`)**: Adds closed-class + *Panpuppeyar* `136` + *Urupu* multi-segment *Chariyai* folding (`US2`), full context/ambiguity/poetic control (`US3`), and the 28-pattern dual-pruned reverse split engine + 10,000-case properties (`US4`).
3. **Model Split Discipline**: Delegate repeatable/token-heavy TOML table authoring, witness-backed golden vector drafting, thin FFI binding wrappers, and adversarial verification passes to **Gemini 4 Hydrogen (`medium`)**; keep `build.rs`, `phonology.rs`, `pipeline.rs`, `uyireeru.rs`, `meyyeeru.rs`, `closed_class.rs`, `urupu.rs`, `split.rs`, and `roundtrip_properties.rs` on **Gemini 4 Neon**.
4. **Policy-Gated Promotion**: Keep `tests/golden/punarchi_nannool.jsonl` `planned` and `crates/tamil-punarchi` private until T048 multi-runtime parity and T049 explicit owner review complete.

---

## Phase 8: Convergence

- [ ] T053 Restore passing `just check-release-policy` and `just check-unicode` gates by either keeping provisional `tamil-toolkit` dependency wiring isolated from `crates/tamil-toolkit/Cargo.toml` until T049 approval or completing owner-approved release-policy promotion (T049–T052) per Constitution VI & VII (contradicts)
- [X] T054 Implement runtime execution and exact sūtra trace emission for Sūtras 177 (`ஆ+பீ→ஆப்பி` and `ஆப்பி` Alvazhi/Vetrumai), 255 (Case-2 `ஐ` elision compounds), and 256 (Case-3 `ஆல்` passive-action agentive compounds) in `crates/tamil-punarchi/src/{closed_class.rs,meyyeeru.rs,urupu.rs}` per FR-001, FR-005, FR-006, SC-002 (missing)
- [X] T055 Reconcile the 8 runtime-emitted `rule_id`s (`nannool_093_kurriyaligaram_y`, `nannool_163_4_non_udambadumei_v`, `nannool_163_demonstrative_consonant_double`, `nannool_163_demonstrative_nasal_double`, `nannool_163_demonstrative_v`, `nannool_221_num_nasal`, `nannool_235_av_iv_uv_aytham`, `nannool_235_av_iv_uv_nasal`) with canonical `lexicon/punarchi-nannool.toml` `[[rule]].id` entries and enforce golden-to-TOML `rule_id` referential integrity in `crates/tamil-punarchi/tests/inventory_completeness.rs` per FR-002, FR-003, Constitution IV (contradicts)
- [X] T056 Author witness-backed escaped golden vectors in `tools/punarchi_golden_cases.py` and `tests/golden/punarchi_nannool.jsonl` covering all 25 currently untested executable transformation sūtras (`168–169, 177–178, 188–193, 200, 202, 208, 213–218, 223, 231, 233–234, 255–256`) and all 6 Sūtra 167 `அ`-final Alvazhi classes, and verify across all chapter test suites per FR-005, FR-006, SC-002, Constitution III (partial)
- [X] T057 Measure native `--release` Rust latencies for `punarchi_join` and `punarchi_split_candidates` for recording in `docs/specs/punarchi-nannool-v1.md` per plan: Performance Goals, Constitution VII (partial)
- [X] T058 Update the superseded banner in `docs/specs/punarchi-v0.1.md` from `107-sūtra` to `117-sūtra` (`93–94, 102–108, 136, 151–257`) to match `spec.md` FR-001 per FR-001, SC-001 (partial)

