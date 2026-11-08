# Canonical architecture and dependency roadmap

Normative companion to [Spec 016](../../specs/016-crate-dependency-roadmap/spec.md) and [ROADMAP](../../ROADMAP.md). Phase numbers describe future work, not completion claims.

## Lifecycle and acceptance

The seven states are `unscaffolded`, `planned`, `specified`, `implemented`, `active`, `release-approved`, and `published`. Roadmap outlines alone do not prove sourced fixtures or complete linguistic support. Release records own publication evidence.

| State | Required evidence before transition |
| --- | --- |
| `unscaffolded` | Roadmap owner, rank and phase recorded; no crate directory. |
| `planned` | Registered scaffold or planned suite; behavior or source review remains unfinished. |
| `specified` | Bounded normative contract and sourced, escaped golden vectors exist. A roadmap outline alone is insufficient. |
| `implemented` | Rust implementation passes local unit and golden checks for the specified scope. |
| `active` | Owner approved manifest activation and unchanged fixtures pass in real Rust, Python, WASM and Dart runtimes. |
| `release-approved` | Public allowlist review includes dependency closure and successful isolated archive consumer verification. |
| `published` | Immutable version tag, reviewed source SHA and registry artifact evidence are recorded in a release record for the applicable distributions. |

Beginning Phase 8/14/9/16 respectively permits implementation work on transliteration, phonetics, tokenization and spelling after its source-backed specification and golden vectors exist. The Python guard rejects manifest-free directories and sources containing only comments, attributes or STATUS declarations. It accepts substantive source alongside a manifest, including implementations retaining a planned status during development. This bounded placeholder check does not establish specification approval, Rust validity or linguistic completeness; review and the remaining gates establish those claims. Existing four scaffolds are exempt from this future-crate guard.

Every phase requires (1) source-backed specification, (2) escaped sourced golden JSONL, (3) Rust implementation with `#![forbid(unsafe_code)]`, (4) shared dispatcher, CLI and thin Python/WASM/Dart exposure, (5) real runtime parity, and (6) explicit owner suite activation and release-policy review. Publication remains a separate action.

`just check-release-policy` checks runtime, build, dev and target-specific dependencies, including package aliases inherited from the workspace. Strict lower ranks enforce acyclicity; domain edge restrictions below also require review.

## 3. Target Crate Dependency DAG (`Rank 0` – `Rank 6`)

Every dependency edge MUST point strictly from a higher rank number to a lower rank number (`Rank(dependency) < Rank(dependent)`). This rule applies to `[dependencies]`, `[dev-dependencies]`, and `[build-dependencies]`. Cross-crate integration tests that require multiple sibling crates belong in `crates/tamil-toolkit/tests/` or the root test harness.

```mermaid
flowchart TD
    subgraph R6["Rank 6: Multi-Runtime Bindings & Integrations"]
        PY["bindings/python (PyO3)"]
        WASM["bindings/js-wasm (WASM)"]
        DART["bindings/dart-flutter (FRB)"]
        CLI["tamil-toolkit CLI / tamil-oracle"]
        ADDIN["integrations/office-word-addin & playground"]
    end

    subgraph R5["Rank 5: Unified Facade & Orchestrator"]
        TK["tamil-toolkit"]
    end

    subgraph R4["Rank 4: High-Level Linguistic Applications & DB Extension"]
        SPELL["tamil-spell (New Planned)"]
        DIALECT["tamil-dialect (Planned)"]
        PG["extensions/pg_tamil (Isolated PG Adapter)"]
    end

    subgraph R3["Rank 3: Morphological Analyzer & Lexicon"]
        MORPH["tamil-morph (Planned)"]
    end

    subgraph R2["Rank 2: Contextual Engines, Sandhi, Typography & Conversion"]
        PUNARCHI["tamil-punarchi (Planned)"]
        HYPHEN["tamil-hyphen (Implemented)"]
        COLLATE["tamil-collate (Implemented)"]
        CALENDAR["tamil-calendar (Bounded/Review)"]
        TRANSLIT["tamil-translit (New Planned)"]
        PHONETICS["tamil-phonetics (New Planned)"]
        TOKENIZE["tamil-tokenize (New Planned)"]
    end

    subgraph R1["Rank 1: Normalization, Codecs, Numerals & Classical Prosody"]
        NORM["tamil-norm (Facade -> Full Norm)"]
        CODEC["tamil-codec + codec::braille (Implemented)"]
        NUMERALS["tamil-numerals + ITN parse (Implemented)"]
        YAAPPU["tamil-yaappu (Planned)"]
    end

    subgraph R0["Rank 0: Foundational Orthography & Phonological Primitives"]
        CORE["tamil-core (Implemented + Phase 1 Primitives)"]
    end

    R6 --> TK
    TK --> SPELL & DIALECT & MORPH & PUNARCHI & HYPHEN & COLLATE & CALENDAR & TRANSLIT & PHONETICS & TOKENIZE & NORM & CODEC & NUMERALS & YAAPPU & CORE
    SPELL --> MORPH & PUNARCHI & TOKENIZE & NORM & CORE
    DIALECT --> MORPH & TOKENIZE & NORM & CORE
    PG --> MORPH & TOKENIZE & COLLATE & NORM
    MORPH --> PUNARCHI & NORM & CORE
    PUNARCHI --> NORM & CORE
    HYPHEN --> NORM & CORE
    COLLATE --> NORM & CORE
    TRANSLIT --> NORM & CORE
    PHONETICS --> NORM & CORE
    TOKENIZE --> NORM & CORE
    CALENDAR --> NUMERALS & CORE
    NORM --> CORE
    CODEC --> CORE
    NUMERALS --> CORE
    YAAPPU --> CORE
```

### Canonical Dependency Matrix

| Rank | Crate / Target | Status Vocabulary | Direct `tamil-*` Dependencies | Owned Domain & Boundary Contract |
|---:|---|---|---|---|
| **0** | [`tamil-core`](../../crates/tamil-core/Cargo.toml) | `published` (v0.1.0-alpha.6); Phase 1 primitives `implemented` | *None* (Zero `tamil-*` deps) | NFC/NFD, UAX #29 tailored `Letters` (`க்ஷ`, `ஸ்ரீ`), `split_uyirmei`/`compose_uyirmei`, scalar inspection, **plus Phase 1 implemented**: `is_kuril`, `is_nedil`, `is_mei`/`is_otru`, `is_aytham`, nominal `baseline_maathirai`, sourced `ina_ezhuthu` (`get_cognate`, `are_cognates`), and narrow zero-allocation orthographic syllable nucleus (`Olippasai`) with spans. |
| **1** | [`tamil-norm`](../../crates/tamil-norm/Cargo.toml) | `published` (minimal facade); Phase 2 contracts `specified` | `tamil-core` | Three explicit contracts: (1) Canonical NFC/NFD, (2) Opt-in orthographic repair (duplicate pulli, visual left-kombu, control/SHY stripping with diagnostics), (3) Versioned lossy search folding (*Mayangoli* & Grantha folding). |
| **1** | [`tamil-codec`](../../crates/tamil-codec/Cargo.toml) | `published` (7 codecs + auto-detect); Phase 7 extensions `specified` | `tamil-core` | Bidirectional legacy font transcoding (Bamini, TSCII, TAB, TAM, Anjal, LT-TM, Vanavil), heuristic auto-detection, **plus Phase 7**: remaining legacy fonts (Senthamil, Shree-Tam, Softview, TBO) and `tamil-codec::braille` (Bharathi / Unicode Braille `U+2800..U+28FF`). |
| **1** | [`tamil-numerals`](../../crates/tamil-numerals/Cargo.toml) | `published` (v0.3 active); Phase 6 extensions `specified` | `tamil-core` | CLDR 49 integer/decimal spellout (`ta-IN`, `ta-LK`), INR/LKR currency, 20 traditional fractions, `U+0BF0..U+0BF2` numerals, ordinals, Gregorian date formatting, **plus Phase 6**: reverse word-to-number parsing (ITN), colloquial mixed fraction words (`ஒன்றேகால்`, `இரண்டரை`), diaspora currencies (`SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`). |
| **1** | [`tamil-yaappu`](../../crates/tamil-yaappu/Cargo.toml) | `planned` (scaffold in workspace) | `tamil-core` | Classical Tamil prosody (*Yaapparungalakkaarigai* / *Tolkappiyam*): contextual *Maathirai* (*Kurriyalugaram*, *Kurriyaligaram*, *Alapedai*, *Aytham*), *Asai* (*Ner* / *Nirai*), *Seer*, *Thalai*, *Adi*, *Thodai* (*Monai*, *Ethugai*, *Iyaibu*, *Muran*), and *Paa* meter validation (*Venpa*, *Asiriyappa*, *Kalippa*, *Vanjippa*). Optional pre-split Sandhi hints passed via API/facade. |
| **2** | [`tamil-calendar`](../../crates/tamil-calendar/Cargo.toml) | `published` (4 civil suites `active`, 13 ephemeris/observance suites `planned`) | `tamil-core`, `tamil-numerals` | 60-year cycle, Thiruvalluvar year, TN/SL official holidays, bounded Thirukanitham (`astro` 2.0.0) & 1962 Vakya solar/lunar/civil engines, daylight periods, lunar phases, and sourced observance rules. |
| **2** | [`tamil-collate`](../../crates/tamil-collate/Cargo.toml) | `published` (`agara-v1` active); Phase 5 extensions `specified` | `tamil-core`, `tamil-norm` | Deterministic Mei-first *Agara Varisai* (`agara-v1`) `sort_key`/`search_key`/`compare`, **plus Phase 5**: versioned `folded_search_key` (consuming `tamil-norm` search folding) and modern Uyirmei-first school dictionary profile. |
| **2** | [`tamil-hyphen`](../../crates/tamil-hyphen/Cargo.toml) | `implemented` (Spec 015 parity complete; pending `release-policy.toml` & manifest promotion) | `tamil-core`, `tamil-norm` | Canonical 5-step Tamil *Asai* + `left_min = 3, right_min = 3` (`MIN_WORD_LETTERS = 6`) typographic hyphenation, soft-hyphen (`\u{00AD}`) injection, Frank Liang `.dic` synthesis, LibreOffice `.oxt` packager, OpenXML `.docx` processor, and optional morphological boundary hints API. |
| **2** | [`tamil-punarchi`](../../crates/tamil-punarchi/Cargo.toml) | `planned` (scaffold in workspace; source notes in `docs/specs/punarchi-v0.1.md`) | `tamil-core`, `tamil-norm` | Sourced *Nannool Ezhuthathikaram* (Sutras 151–257) Sandhi engine: (1) Forward synthesis (`Thonral`, `Thirithal`, `Keduthal`, `Iyalbu`) with explicit grammatical context (*Vetrumai* vs *Alvazhi*), and (2) Bounded inverse-rule candidate generation returning rule IDs, reconstructed forms, and surface spans. Never depends on `tamil-morph`. |
| **2** | `tamil-translit` | `unscaffolded` (New Planned Crate — create in Phase 8) | `tamil-core`, `tamil-norm` | Bidirectional orthographic transliteration: Phase 8 reversible scholarly schemes (ISO 15919, Madras University Tamil Lexicon, ITRANS, Harvard-Kyoto); Phase 17 historical/epigraphic scripts (Tamil-Brahmi `U+11000`, Grantha `U+11300`, Vatteluttu), cross-script (Sinhala-Tamil, Malayalam-Tamil), and noisy phonetic Roman/Tanglish input. |
| **2** | `tamil-phonetics` | `unscaffolded` (New Planned Crate — create in Phase 14) | `tamil-core`, `tamil-norm` | Profile-specific Grapheme-to-Phoneme (G2P) and IPA transcription: contextual allophonic voicing and intervocalic lenition of `க, ச, ட, த, ப`, post-nasal homorganic voicing, geminate invariance, and vowel reduction rules. |
| **2** | `tamil-tokenize` | `unscaffolded` (New Planned Crate — create in Phase 9) | `tamil-core`, `tamil-norm` | Surface sentence and word tokenization with byte/letter span preservation, sourced Tamil abbreviation disambiguation (`திரு.`, `பி.ப.`, `மு.க.`, `எ.கா.`, `ரூ.`), and stratified stopword lexicons. |
| **3** | [`tamil-morph`](../../crates/tamil-morph/Cargo.toml) | `planned` (scaffold in workspace) | `tamil-core`, `tamil-norm`, `tamil-punarchi` | Finite-State Transducer (FST) / chart morphological analyzer, lemmatizer, and stemmer: noun declension across 8 *Vetrumai* cases + *Cariyai* increments + plural `-கள்`, verb 6-part *Pagu-padham* conjugation (`பகுதி, விகுதி, இடைநிலை, சந்தி, சாரியை, விகாரம்`), clitic detachment (`-உம், -ஏ, -ஓ, -தான்`), and lexical validation/ranking of `tamil-punarchi` compound split candidates. |
| **4** | [`tamil-dialect`](../../crates/tamil-dialect/Cargo.toml) | `planned` (scaffold in workspace) | `tamil-core`, `tamil-norm`, `tamil-tokenize`, `tamil-morph` | Sourced pluricentric regional lexical & spoken-to-literary (*Senthamizh*) mapping across `ta-IN` (Central, Madurai, Kongu, Nellai, Madras) and `ta-LK` (Jaffna, Batticaloa, Vanni, Up-Country), plus `ta-SG`/`ta-MY`. |
| **4** | `tamil-spell` | `unscaffolded` (New Planned Crate — create in Phase 16) | `tamil-core`, `tamil-norm`, `tamil-tokenize`, `tamil-punarchi`, `tamil-morph` | Orthographic & morpho-syntactic linter: (1) *Mayangoli* (`ல/ள/ழ`, `ன/ண`, `ர/ற`) confusion-set detection & grapheme-weighted edit distance, and (2) *Valimigum / Valimigaa Idangal* (வல்லினம் மிகும்/மிகா இடங்கள்) fortis stop doubling diagnostics using `tamil-morph` POS/case tags and `tamil-punarchi` rules. |
| **4** | [`extensions/pg_tamil`](../../extensions/pg_tamil/Cargo.toml) | `scaffold` (isolated outside workspace) | `tamil-norm`, `tamil-collate`, `tamil-tokenize`, `tamil-morph` (staged) | PostgreSQL `pgrx` extension: Stage 1 SQL normalization, orthographic repair, and `agara-v1` / folded collation keys (`tamil-norm` + `tamil-collate`); Stage 2 Tamil Full-Text Search (FTS) parser, stopword filter, and morphological stemmer dictionary (`tamil-tokenize` + `tamil-morph`). |
| **5** | [`tamil-toolkit`](../../crates/tamil-toolkit/Cargo.toml) | `published` (v0.1.0-alpha.6) | All active `Rank 0`–`Rank 4` library crates (never `pg_tamil`) | Unified Rust facade, JSON dispatcher (`execute` / `execute_json`), cross-crate pipeline orchestrator (e.g., passing `tamil-morph` compound boundaries into `tamil-hyphen`), `tamil-oracle`, and `tamil-toolkit` CLI. |
| **6** | `bindings/*`, `playground/`, `integrations/*` | `published` / `live` | `tamil-toolkit` | Thin runtime adapters (`bindings/python`, `bindings/js-wasm`, `bindings/dart-flutter/rust`), PWA Playground, and Microsoft Word Office.js Add-in consuming the single shared Rust/WASM implementation. |

---

## 4. Capability Difficulty Tiers (`Tier 1` – `Tier 5`)

Difficulty is rated at the **capability and profile level** rather than assigning one flat score to an entire crate. Each tier reflects both **algorithmic/engineering complexity** and **primary-source verification/evidence complexity**.

| Difficulty Tier | Classification Name | Defining Characteristics | Assigned Capabilities & Crate Modules |
|---|---|---|---|
| **Tier 1** | **Foundation & Mechanical Wiring** | Finite, unambiguous Unicode/phonological facts, deterministic table projections, CLI subcommand wiring, and release-policy alignment. | • `tamil-core`: Existing scalar/grapheme segmentation + Phase 1 `is_kuril`, `is_nedil`, `is_mei`, `is_aytham`, nominal `baseline_maathirai`, `ina_ezhuthu`, and narrow `Olippasai` nucleus spans.<br>• `tamil-hyphen`: Promotion to `release-policy.toml` `public_crates`, removal of `release_policy.py` exemption, activation of `hyphen_syllable.jsonl` in `manifest.json`, and WASM consolidation in Playground/Word Add-in.<br>• `tamil-toolkit`: CLI subcommand exposure for `codec`, `collate`, `numerals`, `norm`, and `calendar`. |
| **Tier 2** | **Bounded Table & Rule Conversions** | Deterministic 1-to-1 or finite-state trie conversions backed by published standards, lexicon tables, or statutory schedules. | • `tamil-collate`: Existing `agara-v1` sorting + Phase 5 `folded_search_key` and Uyirmei-first school dictionary profile.<br>• `tamil-codec`: Existing 7 codecs + Phase 7 additional legacy font tables (Senthamil, Shree-Tam, Softview, TBO) and `tamil-codec::braille` (Bharathi / Unicode Braille Grade 1).<br>• `tamil-numerals`: Existing v0.3 spellout/fractions + Phase 6 diaspora currency labels (`SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`) and colloquial mixed-fraction words (`ஒன்றேகால்`, `இரண்டரை`).<br>• `tamil-calendar`: Active Phase 1 civil/tabular suites (`calendar_year_cycle`, `calendar_official_holidays`, `calendar_tamil_display`, `calendar_thiruvalluvar_year`).<br>• `tamil-translit` (Profile 1): Reversible orthographic romanization (ISO 15919, Madras University Tamil Lexicon, ITRANS, Harvard-Kyoto).<br>• `extensions/pg_tamil` (Stage 1): SQL scalar normalization and collation functions. |
| **Tier 3** | **Contextual Processing & Bounded Grammars** | Local context windows, finite state machines, AST parsing of structured phrases, or typographic constraint satisfaction. | • `tamil-norm`: Opt-in orthographic repair engine (duplicate pullis, visual left-kombu reordering, control/SHY stripping with edit provenance) and versioned lossy search-folding profiles.<br>• `tamil-hyphen`: Existing 5-step *Asai* + `left_min=3, right_min=3` hyphenator, Frank Liang `.dic` synthesizer, `.oxt`, and streaming `.docx` XML processor.<br>• `tamil-numerals` (ITN): Reverse formal word-to-number parser (`"நூற்று இருபத்து மூன்று"` $\rightarrow$ `123`).<br>• `tamil-tokenize`: Abbreviation-aware Tamil sentence splitter, surface word tokenizer with byte/letter spans, and stopword filtering.<br>• `tamil-yaappu` (Phase 13a): Contextual *Maathirai* and *Ner*/*Nirai* *Asai* + *Seer*/*Thalai*/*Adi*/*Thodai* scansion on pre-tokenized verse. |
| **Tier 4** | **Classical Rule Engines & FST Morphology** | Multi-rule interaction across classical grammatical treatises, finite-state morphological transducers, allophonic phonology, and lexicon-backed disambiguation. | • `tamil-punarchi`: Forward Nannool Sandhi synthesizer (Sutras 151–257 with explicit *Vetrumai* / *Alvazhi* context) and bounded inverse-rule split candidate generator.<br>• `tamil-morph`: FST morphological analyzer, lemmatizer, 8-case noun declension, 6-part *Pagu-padham* verb conjugation, clitic detachment, and lexical ranking of `tamil-punarchi` compound candidates.<br>• `tamil-phonetics`: Rule-based G2P and IPA transcription (allophonic voicing/lenition, post-nasal voicing, geminate invariance, vowel reductions).<br>• `tamil-yaappu` (Phase 13b): Full *Venpa*, *Asiriyappa*, *Kalippa*, and *Vanjippa* meter validators.<br>• `tamil-spell` (Phase 16a): *Mayangoli* confusion-set spellchecker and unambiguous *Valimigum/Valimigaa* boundary diagnostics.<br>• `extensions/pg_tamil` (Stage 2): PostgreSQL Tamil Full-Text Search (FTS) dictionary and morphological stemmer. |
| **Tier 5** | **Ambiguous Synthesis, Diglossia & Contested Witnesses** | High structural ambiguity, unstandardized spoken orthography, or historical/sectarian primary sources requiring independent witness adjudication. | • `tamil-calendar` (Phase 4): Independent witness review and activation of the 13 planned Thirukanitham/Vakya ephemeris and religious observance suites, arbitrary-location Vakya station geometry, and contested festival selectors (e.g., Krishna Jayanthi, Smartha vs. Vaishnava Ekadashi, Dharmasindhu Pradosham).<br>• `tamil-dialect`: Pluricentric spoken-to-literary (*Senthamizh*) normalization and regional dialect transformation packs (`ta-IN` TN dialects, `ta-LK` Jaffna/Batticaloa/Vanni/Up-Country).<br>• `tamil-spell` (Phase 16b): Full syntactic *Valimigum/Valimigaa* disambiguation across ambiguous compounds (*Vinait-thogai* vs. *Vetrumait-thogai*).<br>• `tamil-translit` (Phase 17): Ambiguous phonetic Roman/Tanglish IME conversion, Tamil-Brahmi (`U+11000` Systems I–III), Grantha (`U+11300`), Vatteluttu, and cross-script Sinhala/Malayalam conversion. |

---

## 5. Comprehensive Gap Inventory (Existing Crates + Missing Capabilities)

### 5.1 Gaps & Missing Primitives Inside Existing Crates

1. **[`crates/tamil-core`](../../crates/tamil-core/src/lib.rs)**:
   - Missing letter-quantity predicates: `is_kuril(letter)`, `is_nedil(letter)`, `is_mei(letter)` / `is_otru(letter)`, `is_aytham(letter)`, and nominal `baseline_maathirai(letter)` (returning exact rational/half-unit measures: Kuril = `1`, Nedil = `2`, Mei/Aytham = `1/2`).
   - Missing homorganic cognate mapping (`ina_ezhuthu`): Vallinam-Mellinam cognate pairs (`க்↔ங்`, `ச்↔ஞ்`, `ட்↔ண்`, `த்↔ந்`, `ப்↔ம்`, `ற்↔ன்`) and Uyir cognate pairs (`அ↔ஆ`, `இ↔ஈ`, `உ↔ஊ`, `எ↔ஏ`, `ஐ↔இ`, `ஒ↔ஓ`, `ஔ↔உ`).
   - Missing shared orthographic nucleus kernel (`Olippasai`): Currently embedded privately inside [`crates/tamil-hyphen/src/syllable.rs`](../../crates/tamil-hyphen/src/syllable.rs); extracting the pure nucleus + coda grouping (without typographic margin merging) into `tamil-core` allows `tamil-hyphen` and `tamil-yaappu` to share it without code duplication.
2. **[`crates/tamil-norm`](../../crates/tamil-norm/src/lib.rs)**:
   - Currently a 2-line facade (`pub use tamil_core::{normalize_nfc, normalize_nfd};`).
   - Missing opt-in **Orthographic Repair** (`repair_tamil_text`): healing duplicate pullis (`\u{0BCD}\u{0BCD}` $\rightarrow$ `\u{0BCD}`), reordering visually typed left-side vowel signs (`\u{0BC6}`, `\u{0BC7}`, `\u{0BC8}`) placed before consonants, stripping stray zero-width/discretionary characters (`\u{00AD}`, `\u{200B}`, `\u{200C}`, `\u{200D}`) when explicitly requested, and returning structured diagnostic edit counts (needed by Spec 014 Word Utility Suite).
   - Missing opt-in **Search Folding** (`fold_for_search`): versioned lossy folding for *Mayangoli* equivalents (`ல/ள/ழ`, `ன/ண`, `ர/ற`) and Grantha-to-Tamil phonetic equivalents for fuzzy search and indexing.
3. **[`crates/tamil-hyphen`](../../crates/tamil-hyphen/src/lib.rs)**:
   - Missing from `public_crates` in [`release-policy.toml`](../../release-policy.toml) and carries a temporary exemption in [`tools/release_policy.py`](../../tools/release_policy.py#L109).
   - [`tests/golden/manifest.json`](../../tests/golden/manifest.json) still marks `hyphen_syllable.jsonl` as `"planned"` despite all 122 canonical Spec 015 vectors passing in Rust tests.
   - [`playground/src/lib/engine.ts`](../../playground/src/lib/engine.ts) and [`integrations/office-word-addin/engine.js`](../../integrations/office-word-addin/engine.js) maintain mirrored JS/TS implementations of the 5-step hyphenator that should be consolidated onto the shared Rust/WASM bundle.
   - Missing optional compound-word boundary preference hook (to be orchestrated via `tamil-toolkit` once `tamil-morph` is built, while strictly enforcing `left_min` and `right_min`).
4. **[`crates/tamil-calendar`](../../crates/tamil-calendar/src/lib.rs)**:
   - 13 of 17 golden suites in [`tests/golden/manifest.json`](../../tests/golden/manifest.json) remain `"planned"` awaiting independent witness verification per suite.
   - Open source-evidence items documented in [`docs/status.md`](../../docs/status.md): arbitrary-location Vakya station geometry (Bhujaantara interpolation & Udayantara omission in the 1962 edition), 2026 Thiruvalluvar Gazette boundary conflict, and contested annual festival month selectors (Krishna Jayanthi, Dharmasindhu Pradosham, Smartha Ekadashi).
5. **[`crates/tamil-collate`](../../crates/tamil-collate/src/lib.rs)**:
   - `search_key` is currently identical to `sort_key`; needs a distinct versioned `folded_search_key` consuming `tamil-norm` search folding while preserving exact `search_key` backward compatibility.
   - Only implements Mei-first `agara-v1`; missing modern Uyirmei-first school dictionary profile.
6. **[`crates/tamil-numerals`](../../crates/tamil-numerals/src/lib.rs)**:
   - Missing reverse word-to-number parsing (Inverse Text Normalization: `"நூற்று இருபத்து மூன்று"` $\rightarrow$ `123`).
   - Missing colloquial inflected mixed-fraction word synthesis/parsing (`ஒன்றேகால்`, `இரண்டரை`, `மூன்றேமுக்கால்`, `அரைக்கால்`).
   - Missing diaspora currency profiles (`SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`).
7. **[`crates/tamil-codec`](../../crates/tamil-codec/src/lib.rs)**:
   - Missing remaining legacy font tables tracked in [`docs/specs/codec-roadmap.md`](../../docs/specs/codec-roadmap.md) (Senthamil, Shree Lipi / Shree-Tam, Softview, TBO, Anu/Pallavar).
   - Missing Bharathi Braille / Unicode Braille (`U+2800..U+28FF`) conversion module (`tamil-codec::braille`).
8. **[`crates/tamil-toolkit`](../../crates/tamil-toolkit/src/bin/tamil-toolkit.rs)**:
   - Production CLI binary currently exposes only `hyphen` subcommands (`export-dic`, `package-oxt`, `process-docx`); needs subcommands for `core`, `norm`, `codec`, `collate`, `numerals`, and `calendar`.

### 5.2 Planned & Newly Identified Workspace Crates

| Crate | Current State | Target Rank | Target Difficulty | Why It Exists & What Prerequisite It Requires |
|---|---|---:|---|---|
| [`tamil-punarchi`](../../crates/tamil-punarchi/src/lib.rs) | Scaffold (`STATUS = "planned"`) | **Rank 2** | **Tier 4** | Implements Nannool Sandhi Sutras 151–257 (forward synthesis + bounded inverse split candidates). **Requires**: `tamil-core` Phase 1 primitives (`is_kuril`, `is_nedil`, `ina_ezhuthu`) and `tamil-norm`. **Prerequisite for**: `tamil-morph` and `tamil-spell`. |
| [`tamil-morph`](../../crates/tamil-morph/src/lib.rs) | Scaffold (`STATUS = "planned"`) | **Rank 3** | **Tier 4** | FST morphological analyzer, lemmatizer, noun cases, verb *Pagu-padham* conjugation, clitic detachment, and compound split validator/ranker. **Requires**: `tamil-punarchi` (to apply/invert morphophonemic boundary transitions) + `tamil-core` + `tamil-norm`. **Prerequisite for**: `tamil-spell`, `tamil-dialect`, `extensions/pg_tamil` FTS, and compound-aware hyphenation in `tamil-toolkit`. |
| [`tamil-yaappu`](../../crates/tamil-yaappu/src/lib.rs) | Scaffold (`STATUS = "planned"`) | **Rank 1** | **Tier 3–4** | Classical prosody (*Asai, Seer, Thalai, Adi, Thodai*) and meter validation (*Venpa, Asiriyappa, Kalippa, Vanjippa*). **Requires**: `tamil-core` Phase 1 letter-quantity and `Olippasai` nucleus primitives. |
| [`tamil-dialect`](../../crates/tamil-dialect/src/lib.rs) | Scaffold (`STATUS = "planned"`) | **Rank 4** | **Tier 5** | Pluricentric spoken-to-literary (*Senthamizh*) and regional dialect mapping (`ta-IN`, `ta-LK`, `ta-SG`, `ta-MY`). **Requires**: `tamil-tokenize` and `tamil-morph` (to normalize contracted spoken verb/noun inflections like `வந்துட்டான்` $\rightarrow$ `வந்துவிட்டான்` accurately). |
| `tamil-translit` | New Planned (Unscaffolded) | **Rank 2** | **Tier 2 / Tier 5** | Bidirectional orthographic transliteration (ISO 15919, Madras University Lexicon, ITRANS/HK; later profiles for Tamil-Brahmi, Grantha, Vatteluttu, Sinhala-Tamil, and Tanglish IME). **Requires**: `tamil-core` and `tamil-norm`. |
| `tamil-phonetics` | New Planned (Unscaffolded) | **Rank 2** | **Tier 4** | Context-sensitive G2P and IPA pronunciation (intervocalic lenition, post-nasal voicing, geminate invariance). Kept separate from `tamil-translit` because Tamil orthography is archiphonemic. **Requires**: `tamil-core` Phase 1 (`ina_ezhuthu`, `is_kuril`/`is_nedil`) and `tamil-norm`. |
| `tamil-tokenize` | New Planned (Unscaffolded) | **Rank 2** | **Tier 3** | Surface word/sentence segmentation with byte/letter spans, Tamil abbreviation handling (`திரு.`, `பி.ப.`, `மு.க.`), and stopword sets. **Requires**: `tamil-core` and `tamil-norm`. **Prerequisite for**: `tamil-spell`, `tamil-dialect`, and `extensions/pg_tamil`. |
| `tamil-spell` | New Planned (Unscaffolded) | **Rank 4** | **Tier 4–5** | *Mayangoli* (`ல/ள/ழ`, `ன/ண`, `ர/ற`) spellchecker and *Valimigum / Valimigaa Idangal* (வல்லினம் மிகும்/மிகா இடங்கள்) grammatical linter. **Requires**: `tamil-tokenize`, `tamil-punarchi`, and `tamil-morph` (because distinguishing *Valimigum* from *Valimigaa* requires knowing whether a word is an accusative/dative noun, demonstrative, relative participle *Peyarechcham*, or verbal compound *Vinait-thogai*). |

---

## 6. Sequenced Execution Roadmap (`Phase 0` – `Phase 17`)

Each phase has explicit **Hard Prerequisites** (phases that MUST be completed before it can start) and an **Exit Gate**. Phases whose hard prerequisites are satisfied may run in parallel tracks.

| Phase | Milestone / Deliverable | Difficulty | Hard Prerequisites | Exit Gate & Verification Contract |
|---:|---|---:|---|---|
| **0** | **Architectural Roadmap & Status Governance (Spec 016)** | Tier 1 | *None* | `specs/016-crate-dependency-roadmap/spec.md` and `ROADMAP.md` synchronized; status vocabulary (`unscaffolded`, `planned`, `specified`, `implemented`, `active`, `release-approved`, `published`) frozen. |
| **1** | **`tamil-core` Phonological & Nucleus Primitives Closeout** | Tier 1 | Phase 0 | `is_kuril`, `is_nedil`, `is_mei`/`is_otru`, `is_aytham`, `baseline_maathirai`, sourced `ina_ezhuthu`, and narrow `Olippasai` nucleus spans added to `tamil-core` with active golden vectors; zero regressions in existing `Letters` segmentation. |
| **2** | **`tamil-norm` Repair & Search-Folding Contracts** | Tier 3 | Phase 1 | `tamil-norm` expanded from 2-line facade to 3 explicit contracts: (1) NFC/NFD, (2) opt-in `repair_tamil_text` with diagnostic counts, (3) versioned `fold_for_search` profiles (*Mayangoli* & Grantha) with golden vectors. |
| **3** | **`tamil-hyphen` Release Policy, Manifest & WASM Consolidation** | Tier 1 | Phase 1, Phase 2 | `tamil-hyphen` refactored to use `tamil-core` Phase 1 primitives; `hyphen_syllable.jsonl` activated in `manifest.json`; `tamil-hyphen` added to `release-policy.toml` `public_crates`; `release_policy.py` exemption removed; Playground & Word Add-in consolidated onto shared Rust/WASM engine; CLI subcommands added for existing crates. |
| **4** | **`tamil-calendar` Planned Suite Review & Activation Track** | Tier 5 | Phase 0 *(Independent Track)* | Each of the 13 planned calendar/observance JSONL suites reviewed individually against primary witnesses; verified suites promoted to `active` upon owner approval; unresolved historical witnesses remain `planned` without blocking language phases. |
| **5** | **`tamil-collate` Folded Search & Uyirmei-First Profile** | Tier 2 | Phase 2 | Versioned `folded_search_key` added (preserving existing `agara-v1` `search_key` exact contract) alongside a sourced modern Uyirmei-first school dictionary collation profile. |
| **6** | **`tamil-numerals` Reverse Word Parsing (ITN), Mixed Fractions & Currencies** | Tier 2–3 | Phase 1 | Reverse formal word-to-number parser (`parse_number_words`), colloquial mixed-fraction words (`ஒன்றேகால்`, `இரண்டரை`), and diaspora currency profiles (`SGD`, `MYR`, `USD`, `EUR`, `GBP`, `CAD`) added with active golden vectors. |
| **7** | **`tamil-codec` Legacy Font Expansion & `codec::braille`** | Tier 2 | Phase 1 | Remaining sourced legacy font tables (Senthamil, Shree-Tam, Softview, TBO) and `tamil-codec::braille` (Bharathi / Unicode Braille `U+2800..U+28FF` Grade 1) implemented and verified. |
| **8** | **`tamil-translit` (Profile 1: Reversible Orthographic Romanization)** | Tier 2 | Phase 1, Phase 2 | Create `crates/tamil-translit`; implement reversible ISO 15919, Madras University Tamil Lexicon, ITRANS, and Harvard-Kyoto schemes with round-trip golden vectors. |
| **9** | **`tamil-tokenize` (Surface Sentence/Word Spans & Abbreviations)** | Tier 3 | Phase 1, Phase 2 | Create `crates/tamil-tokenize`; implement span-preserving word/sentence segmentation, sourced Tamil abbreviation lexicon (`திரு.`, `பி.ப.`, `மு.க.`), and stopword profiles. |
| **10** | **`tamil-punarchi` (Nannool Forward Synthesis & Inverse Candidates)** | Tier 4 | Phase 1, Phase 2 | Implement sourced Nannool Sutras 151–257 in `crates/tamil-punarchi`: forward synthesis with explicit *Vetrumai*/*Alvazhi* context and bounded inverse-rule candidate generation returning rule IDs, reconstructed stems, and surface spans. |
| **11** | **`tamil-morph` (FST Analyzer, Noun/Verb Inflection & Compound Ranker)** | Tier 4 | Phase 10 | Implement FST/chart analyzer in `crates/tamil-morph`: 8-case noun declension, 6-part *Pagu-padham* verb conjugation, clitic detachment, lemmatization, and lexical validation/ranking of `tamil-punarchi` compound split candidates. |
| **12** | **Cross-Crate Integrations: Compound Hyphenation & `pg_tamil` FTS** | Tier 3–4 | Phase 3, Phase 5, Phase 9, Phase 11 | Wire `tamil-morph` surface-aligned compound boundaries into `tamil-hyphen` via `tamil-toolkit` (respecting `left_min`/`right_min` margins), and implement `extensions/pg_tamil` Stage 1 (SQL norm/collation) & Stage 2 (PostgreSQL FTS dictionary/stemmer). |
| **13** | **`tamil-yaappu` (Classical Prosody & Meter Validation)** | Tier 3–4 | Phase 1 *(Optional Sandhi hints from Phase 10)* | Implement contextual *Maathirai*, *Asai* (*Ner*/*Nirai*), *Seer*, *Thalai*, *Adi*, *Thodai*, and meter validators (*Venpa*, *Asiriyappa*, *Kalippa*, *Vanjippa*) in `crates/tamil-yaappu`. |
| **14** | **`tamil-phonetics` (Contextual G2P & Allophonic IPA)** | Tier 4 | Phase 1, Phase 2 | Create `crates/tamil-phonetics`; implement Tolkappiyam/modern allophonic voicing, intervocalic lenition, post-nasal voicing, geminate invariance, and IPA transcription. |
| **15** | **`tamil-dialect` (Pluricentric Regional & Spoken-to-Literary Mapping)** | Tier 5 | Phase 9, Phase 11 | Implement sourced regional lexical and spoken-to-literary (*Senthamizh*) transformations across `ta-IN` and `ta-LK` (Jaffna, Batticaloa, Vanni, Up-Country) in `crates/tamil-dialect`. |
| **16** | **`tamil-spell` (*Mayangoli* Spellcheck & *Valimigum/Valimigaa* Linter)** | Tier 4–5 | Phase 9, Phase 10, Phase 11 | Create `crates/tamil-spell`; implement *Mayangoli* (`ல/ள/ழ`, `ன/ண`, `ர/ற`) confusion-set spellchecking and morphology-backed *Valimigum / Valimigaa Idangal* boundary diagnostics and suggestions. |
| **17** | **Advanced Profiles (Tanglish IME, Epigraphic Scripts & Broad Grammar)** | Tier 5 | Phase 8, Phase 11, Phase 14, Phase 16 | Add ambiguous phonetic Roman/Tanglish input conversion, Tamil-Brahmi (`U+11000` Systems I–III), Grantha (`U+11300`), Vatteluttu, Sinhala/Malayalam cross-script profiles, and full syntactic compound disambiguation. |

---

## 7. Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Acyclic Rank Invariant & Automated Enforcement)**: Every workspace crate and extension MUST be assigned an integer dependency rank (`Rank 0` through `Rank 6`), and every Cargo dependency edge (`[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, including optional features) MUST point strictly to a lower rank (`Rank(dependency) < Rank(dependent)`). This invariant MUST be enforced automatically in [`tools/release_policy.py`](../../tools/release_policy.py) (`just check-release-policy`).
- **FR-002 (Core vs. Yaappu vs. Hyphen Boundary)**: Pure letter-quantity classifications (`is_kuril`, `is_nedil`, `is_mei`/`is_otru`, `is_aytham`), nominal baseline duration (`baseline_maathirai`), homorganic pairs (`ina_ezhuthu`), and narrow orthographic syllable nuclei (`Olippasai` with spans) MUST reside in `tamil-core` (`Rank 0`). Typographic minimum-margin segment merging (`left_min`/`right_min`) MUST remain in `tamil-hyphen` (`Rank 2`), and contextual metrical duration (*Kurriyalugaram*, *Alapedai*) and *Ner*/*Nirai* scansion MUST reside in `tamil-yaappu` (`Rank 1`).
- **FR-003 (Punarchi vs. Morph Unidirectional Boundary)**: `tamil-punarchi` (`Rank 2`) MUST depend only on `tamil-core` and `tamil-norm`, owning forward Sandhi synthesis (with explicit grammatical context) and bounded inverse-rule candidate generation (returning rule IDs, reconstructed forms, and surface spans). `tamil-morph` (`Rank 3`) MUST depend on `tamil-punarchi` to validate stems and rank compound split candidates. `tamil-punarchi` MUST NEVER depend on `tamil-morph`.
- **FR-004 (Three Distinct Normalization Contracts)**: `tamil-norm` (`Rank 1`) MUST separate (a) lossless canonical normalization (`normalize_nfc`, `normalize_nfd`), (b) explicit opt-in orthographic repair (`repair_tamil_text` with diagnostic provenance and preservation of `ZWJ`/`ZWNJ` unless stripping is explicitly requested), and (c) explicit versioned lossy search-folding profiles (`fold_for_search` for *Mayangoli* and Grantha).
- **FR-005 (Collation Key Stability)**: `tamil-collate` (`Rank 2`) MUST preserve the exact byte/integer output of `sort_key` and `search_key` under `agara-v1` (`docs/specs/collate-v0.1.md`) and introduce folded search keys or Uyirmei-first ordering only via distinct versioned profiles/functions.
- **FR-006 (No Premature Empty Crate Scaffolding)**: The four existing planned crate directories (`tamil-punarchi`, `tamil-morph`, `tamil-yaappu`, `tamil-dialect`) are retained as workspace scaffolds, but the four newly identified standalone crates (`tamil-translit`, `tamil-phonetics`, `tamil-tokenize`, `tamil-spell`) MUST NOT be created as empty placeholder directories in `crates/` until their respective specification phase (`Phase 8`, `Phase 14`, `Phase 9`, `Phase 16`) begins.
- **FR-007 (Module vs. Crate Assignment for Braille & ITN)**: Bharathi / Unicode Braille (`U+2800..U+28FF`) MUST be scheduled initially as `tamil-codec::braille` (`Rank 1`), and reverse word-to-number parsing (ITN) MUST be scheduled inside `tamil-numerals` (`Rank 1`), preventing unnecessary micro-crate proliferation.
- **FR-008 (Facade Orchestration & Margin Precedence for Cross-Branch Integrations)**: Integrations that combine sibling branches—such as morphology-aware compound hyphenation (`tamil-morph` + `tamil-hyphen`) or morphology-assisted pronunciation (`tamil-morph` + `tamil-phonetics`)—MUST be orchestrated in `tamil-toolkit` (`Rank 5`) or via lightweight boundary hints passed by the caller, without adding direct Cargo dependencies between `tamil-hyphen`/`tamil-phonetics` and `tamil-morph`. In compound-aware hyphenation, typographic margin constraints (`left_min` and `right_min`, default `3/3`) MUST strictly govern first; morphological compound boundaries are preferred only when both resulting segments satisfy the active margin settings.
- **FR-009 (Publication Dependency Closure & Hyphen Closeout)**: No crate may be added to `public_crates` in [`release-policy.toml`](../../release-policy.toml) unless its entire Cargo dependency closure is also in `public_crates`. Phase 3 MUST promote `tamil-hyphen` to `public_crates`, activate `hyphen_syllable.jsonl` in [`tests/golden/manifest.json`](../../tests/golden/manifest.json), and remove the temporary `tamil-hyphen` exemption from [`tools/release_policy.py`](../../tools/release_policy.py#L109).
- **FR-010 (Standardized Milestone Acceptance Gate)**: Every roadmap phase (`Phase 1` through `Phase 17`) MUST follow the 6-step repository gate before mark-complete: (1) source-backed specification in `docs/specs/` and `specs/`, (2) escaped golden vectors in `tests/golden/`, (3) `#![forbid(unsafe_code)]` Rust implementation, (4) shared-dispatcher exposure in `tamil-toolkit` + CLI + Python/WASM/Dart adapters, (5) multi-runtime parity verification, and (6) explicit suite activation & release-policy review.

### Key Entities

- **Dependency Rank (`Rank 0` – `Rank 6`)**: Topological layer index in the workspace Directed Acyclic Graph (DAG) guaranteeing zero circular dependencies across code, build scripts, and tests.
- **Difficulty Tier (`Tier 1` – `Tier 5`)**: Capability-level classification measuring algorithmic complexity, state space, and primary-source verification difficulty.
- **Capability Status Vocabulary**: Standardized lifecycle states across all crates and golden suites:
  - `unscaffolded`: Planned in roadmap (`Spec 016`), no `crates/<name>` directory yet.
  - `planned`: Scaffold or golden suite registered in workspace/manifest, implementation or witness review pending.
  - `specified`: Normative specification and sourced test vectors authored.
  - `implemented`: Rust implementation and unit/golden tests passing locally.
  - `active`: Golden suite marked `"status": "active"` in `tests/golden/manifest.json` and enforced across Rust, Python, WASM, and Dart gates.
  - `release-approved`: Listed in `release-policy.toml` `public_crates` with full archive consumer verification.
  - `published`: Immutable version tag published to `crates.io`, `PyPI`, and `npm`.

---


## Boundary payloads and phase closeout

`LetterQuantity`, `InaEzhuthuPair` and `OrthographicNucleus` are proposed core contracts. Contextual metrical duration belongs in yaappu; typography belongs in hyphen.

`SandhiSplitCandidate` carries rule IDs, reconstructed stems and separate surface spans. Stem lengths never establish surface offsets. Morph ranks candidates; punarchi never calls morph.

`HyphenationBoundaryHint` carries surface boundaries through the toolkit facade. Both sides must satisfy active `left_min`/`right_min` (default 3/3) before compound preference applies. Hints cannot override margins. Morphology-assisted phonetics also uses facade orchestration.

Phases 1 through 7 close existing gaps: core primitives; three normalization contracts preserving joiners; hyphen publication closure, suite review and shared WASM consolidation; calendar's 13 planned witness suites; collation extensions preserving exact agara-v1 keys; numeral ITN, mixed fractions and currencies; codec provenance and Braille. CLI exposure accompanies relevant phases. Each phase exits only after the six gates above. Calendar witness review can proceed independently of unrelated NLP work. Punarchi remains deferred under its recorded source-review criteria.

Braille remains inside codec and ITN inside numerals. Four future standalone crates remain unscaffolded until their named specification phases. Regional scope includes TN and SL, including Jaffna, Batticaloa, Vanni and Up-Country when relevant; Unicode-only operations remain region invariant.
