# Feature Specification: Tamil Sandhi (Punarchi) — Complete Nannūl Eḻuttatikāram Rule Engine

**Feature Branch**: `master` (current branch)

**Created**: 2026-11-26

**Status**: Draft

**Input**: Phase 10 (`tamil-punarchi`) from the [project roadmap](../../ROADMAP.md), superseding the deferred Nov 2026 draft in [docs/specs/punarchi-v0.1.md](../../docs/specs/punarchi-v0.1.md): systematic coverage of all **117 *Nannūl Eḻuttatikāram* sūtras** required for complete Sandhi — all **107 Puṇariyal sūtras (`151–257`)** plus **10 mandatory *Eḻuttiyal*/*Padaviyal* prerequisite sūtras (`93–94`, `102–108`, `136`)** — with compositional forward word joining, explicit grammatical context and ambiguity reporting, and dictionary-free reverse split candidate generation.

## Clarifications

### Session 2026-11-26

- Q: How detailed should the optional grammatical context input be for selecting context-dependent *Nannūl* rules? → A: Two-level context: coarse relation (`unspecified`, `vetrumai`, `alvazhi`) plus optional fine-grained subtypes (cases 2–7 and *Nannūl* 152 *Alvazhi* subtypes such as *vinaiyecham*, *peyarecham*, *panputhogai*), lexical class tags (tree name, measure word, verbal noun, etc.), and a poetic flag.
- Q: When a caller omits grammatical context (or *Nannūl* itself permits optional forms) and multiple valid joined forms exist, how should the primary result be selected? → A: Always return a deterministic primary result (preferring unmarked / *Alvazhi* general rules first, then sūtra order) and list every other valid outcome with its required context or optionality label in `alternatives`.
- Q: How should open-ended poetic metrical sūtras (155–156) and usage-governed loan/colloquial sūtra 239 be handled within the 117-sūtra `nannool-v1` profile? → A: Execute all deterministic prose rules and all closed-form poetic rules (`163.3`, `172.1`, `173`, `180`, `222` `அஞ்சிறை`, `243.3`) under opt-in poetic mode; record open-ended meta/metrical/usage sūtras (`151–156`, `239`, `240`, `241`, `253`) as non-generative definition/scope entries in the 117-sūtra inventory.
- Q: What scope should reverse split candidate generation cover for a joined surface word? → A: Single-boundary two-part splits `(first, second)` inverting both single-step phonological rules and multi-step compositional rules (including *Chariyai* + case suffixes and closed-class stem reductions); multi-word recursive chaining remains in Phase 11 morphology.
- Q: How should forward joining behave when a non-empty input contains non-Tamil characters (Latin, digits, punctuation) or an explicit `ZWJ`/`ZWNJ` joiner at the boundary? → A: Reject empty or whitespace-only inputs with an error; when a non-empty join boundary involves a non-Tamil scalar or an explicit `ZWJ`/`ZWNJ` barrier, preserve all scalars verbatim and return an unaltered *Iyalbu* concatenation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Join two Tamil words with a complete Nannūl rule trace (Priority: P1)

A Tamil educator, writer, or language-tool user provides a preceding word (*Nilaimozhi*) and a following word (*Varumozhi*) under the named *Nannūl* literary profile to obtain the properly joined Tamil form along with a step-by-step explanation of every grammar rule and sound change that occurred.

**Why this priority**: Accurate forward word joining across vowel-final (*Uyirīṟṟu*) and consonant-final (*Meyyīṟṟu*) boundaries — including multi-step sound changes — is the core linguistic capability required by learners, editors, and downstream spellchecking and morphology workflows.

**Independent Test**: Submit pairs of Tamil words spanning natural joining (*Iyalbu*), glide insertion (*Udambadumei*), short-u elision (*Kurriyalugaram*), consonant-vowel fusion (*Udalmel Uyir*), monosyllabic consonant doubling, nasal/lateral assimilations, and *Aytham* mutations, and verify both the joined surface form and the exact sūtra trace returned.

**Acceptance Scenarios**:

1. **Given** a vowel-final preceding word and a vowel-initial following word (such as `மணி` + `அடி` or `பூ` + `இதழ்`), **When** a user requests a *Nannūl* join, **Then** the system inserts the required glide (`ய்` or `வ்`), fuses it with the following vowel (`மணியடி`, `பூவிதழ்`), and reports each applied sūtra and alteration type.
2. **Given** a short-u (*Kurriyalugaram*) word before a vowel-initial word (such as `நாகு` + `அரிது` or `காடு` + `எங்கும்`), **When** a user requests a join, **Then** the short-u elides and the exposed consonant fuses with the following vowel (`நாகரிது`, `காடெங்கும்`), recording both deletion and fusion in the derivation trace.
3. **Given** a consonant-final word before a vowel-initial word (such as `தமிழ்` + `அம்மா` or a short-vowel monosyllable such as `கல்` + `அடி`), **When** a user requests a join, **Then** the consonant either fuses directly (`தமிழம்மா`) or doubles before fusing (`கல்லடி`), citing the applicable *Meyyīṟṟup Puṇariyal* sūtras.
4. **Given** a consonant-final word undergoing assimilation before a consonant (such as `மரம்` + `வேர்`, `கல்` + `சிலை`, `முள்` + `செடி`, or `அல்` + `திணை`), **When** a user requests a join, **Then** the system produces the expected altered form (`மரவேர்`, `கற்சிலை`, `முட்செடி`, `அஃறிணை`) with the ordered list of alteration classes (*Iyalbu*, *Thonral*, *Thirithal*, *Keduthal*) and sūtra citations.
5. **Given** a pair requiring no boundary alteration (such as `பொன்` + `மணி` in natural joining), **When** a user requests a join, **Then** the system returns the unaltered joined form (`பொன்மணி`) marked as natural joining (*Iyalbu*).

---

### User Story 2 - Join closed-class stems, numbers, directions, pronouns, and case suffixes (Priority: P2)

A developer, student, or computational linguist combines *Nannūl*'s finite special stem classes — cardinal directions, number words, demonstratives/interrogatives, pronouns, named stems, and case suffixes with connecting increments (*Chariyai*) — and receives the exact multi-step joined output without supplying an external dictionary.

**Why this priority**: Many of Tamil's most distinctive and error-prone Sandhi transformations belong to closed grammatical classes explicitly enumerated in *Nannūl* (sūtras 163, 186–203, 214–222, 232–236, and 240–257). Supporting these closed classes is essential for faithful *Nannūl* coverage and for inflecting nouns with case endings in downstream tools.

**Independent Test**: Submit pairs from each closed class (directions, numbers, pronouns, named stems, and case suffixes with *Chariyai*) and confirm that multi-step compositional derivations produce the exact documented forms and cite every sūtra in order.

**Acceptance Scenarios**:

1. **Given** a noun and a case suffix requiring a connecting increment (*Chariyai*, such as `மரம்` + `ஐ` or `பல` + `ஐ`), **When** a user joins them in a case-suffix context, **Then** the system chains stem adjustment, *Chariyai* insertion (`அத்து`, `அற்று`), vowel elision, and fusion to yield the exact inflected form (`மரத்தை`, `பலவற்றை`) with the full multi-step rule trace.
2. **Given** closed-class number words or cardinal directions (such as `பத்து` + `இரண்டு`, `ஒன்று` + `பத்து`, or `வடக்கு` + `கிழக்கு`), **When** a user requests a join, **Then** the system applies the documented *Nannūl* reductions and assimilations (`பன்னிரண்டு`, `ஒருபது`, `வடகிழக்கு`) with each intermediate sūtra recorded.
3. **Given** personal or reflexive pronouns with case endings (such as `யான்`/`நான்` + `கு`, `நீ` + `ஐ`, `தான்` + `ஆல்`, `எல்லாம்` + `ஐ`, or `எல்லாரும்` + `ஐ`), **When** a user requests a join, **Then** the system applies the *Urupu Puṇariyal* oblique stem transformations, anti-gemination overrides (sūtras 247.5, 250.3), and connecting increments to produce the attested forms (`எனக்கு`, `நின்னை`/`உன்னை`, `தன்னால்`, `எல்லாவற்றையும்`/`எல்லாநம்மையும்` for `எல்லாம்` per sūtra 245, `எல்லார்தம்மையும்`/`எல்லாரையும்` for `எல்லாரும்` per sūtra 246).
4. **Given** short demonstrative or interrogative forms (`அ`, `இ`, `உ`, `எ`) followed by a vowel or consonant, **When** a user requests a join, **Then** the system applies *Nannūl*'s demonstrative doubling/glide rules rather than the generic vowel rule.

---

### User Story 3 - Control grammatical context and inspect genuine ambiguity (Priority: P3)

A linguist or downstream language tool supplies explicit grammatical context — such as case relation (*Vetrumai*) versus non-case relation (*Alvazhi* subtypes), named lexical class tags (tree names, measure words, verbal nouns), or opt-in poetic license — to select exact outcomes, and sees all valid alternatives whenever context is omitted and multiple *Nannūl* rules legitimately apply.

**Why this priority**: In Tamil grammar, identical surface pairs can yield different valid joined forms depending on whether the relation is *Vetrumai* or *Alvazhi* (for example, `மரம்` + `கால்` vs case-marked compounds, or natural vs doubled *Vallinam*). Guessing silently causes subtle semantic errors; explicit context plus transparent ambiguity reporting makes the engine trustworthy for both human learners and automated pipelines.

**Independent Test**: Submit an ambiguous pair first without grammatical context (confirming all valid outcomes and their distinguishing contexts are returned) and then with explicit *Vetrumai* and *Alvazhi* contexts (confirming each selects the exact matching outcome), and verify poetic-only rules stay inactive unless explicitly enabled.

**Acceptance Scenarios**:

1. **Given** a word pair whose *Nannūl* outcome differs between case (*Vetrumai*) and non-case (*Alvazhi*) relations, **When** a user supplies an explicit relation context, **Then** the system returns the outcome governed by that relation and cites the controlling sūtra.
2. **Given** a word pair where multiple *Nannūl* outcomes are valid when no context is supplied (or where *Nannūl* itself permits optional forms, such as `ஏ` taking either `ய்` or `வ்`, or `அல்`/`முள்` permitting *Aytham* or stop assimilation), **When** a user requests a join without disambiguating context, **Then** the system returns the primary outcome alongside labeled alternatives stating the required context or optionality for each.
3. **Given** a word pair eligible for a verse-only poetic alteration (*Seyyul Vikaaram*, e.g., sūtras `163.3`, `172.1`, `173`, `180`, `222` `அஞ்சிறை`, `243.3`), **When** a user runs in default standard-literary mode, **Then** the verse-only alteration is not applied; **When** the user explicitly enables poetic mode, **Then** the verse-only variant is included and explicitly labeled as poetic.

---

### User Story 4 - Generate reverse Sandhi split candidates for a joined surface word (Priority: P4)

A morphological analyzer, dictionary search engine, or student submits a joined Tamil surface word and receives a deterministic, bounded list of candidate two-part splits showing the reconstructed preceding and following words, the *Nannūl* rule(s) inverted, and the exact boundary location in the original surface word — without needing an external dictionary.

**Why this priority**: Cleanly separating pure morphophonemic split candidate generation from dictionary-based lexical ranking prevents architectural coupling while immediately supplying the exact candidate generator needed by future morphological analysis and spellchecking.

**Independent Test**: Take joined outputs produced by reversible *Nannūl* rules across all three chapters, pass each surface string to the reverse candidate generator, and verify that the original `(Nilaimozhi, Varumozhi)` pair appears in the deterministic candidate list with accurate original boundary positions and inverted rule identifiers.

**Acceptance Scenarios**:

1. **Given** a joined Tamil surface word formed by a reversible *Nannūl* rule (such as `மணியடி`, `கல்லடி`, `கற்சிலை`, `தமிழம்மா`, or `மரவேர்`), **When** a user requests split candidates, **Then** the system returns a deterministic, deduplicated list of candidate `(first, second)` pairs that includes the original pair, the inverted rule identifier(s), the alteration type, and exact zero-based boundary coordinates in the input string.
2. **Given** a surface boundary that can result from more than one *Nannūl* rule (for example, a medial `ற்` that could reflect original `ற்`, `ல்`, or `ன்` before a stop), **When** a user requests split candidates, **Then** the system returns every applicable rule-backed candidate without fabricating arbitrary splits or claiming one unique lexical answer.
3. **Given** a surface string with no valid internal *Nannūl* split point (such as a single written unit or non-Tamil text), **When** a user requests split candidates, **Then** the system returns an empty candidate list without error.

---

### Edge Cases

- **Canonically equivalent input, non-Tamil text, and invisible joiners**: Input containing canonically decomposed Tamil vowel signs (`\u{0BC6}\u{0BBE}` vs `\u{0BCA}`) matches the same rules as NFC input. When a non-empty forward join has a non-Tamil scalar (Latin, digits, punctuation) or an explicit `ZWJ`/`ZWNJ` barrier right at the boundary, all scalars are preserved verbatim and the system returns an unaltered natural (*Iyalbu*) concatenation without silently dropping format controls.
- **Atomic written units**: Ligatures such as `க்ஷ` and both `ஸ்ரீ` spellings remain atomic written units and are never split mid-unit when computing boundaries or candidate split positions.
- **Invalid inputs and unknown selections**: Empty or whitespace-only components in forward joining, unknown grammar profiles (e.g., requesting an unimplemented *Tolkāppiyam* profile or bogus name), or unsupported context values return explicit, deterministic errors rather than silent fallbacks.
- **Multi-alteration interactions**: Boundaries undergoing two or three chained transformations (per sūtra 157, such as deletion + increment + elision + fusion) execute in a well-defined, non-looping order and never enter infinite rule cycles.
- **Usage-governed and open-ended poetic sūtras (`155–156`, `239`)**: Arbitrary metrical lengthening/contraction (sūtras `155–156`) and lexicalized loans, particles, or colloquial compounds (sūtra `239`) are recorded as non-generative scope entries in the 117-sūtra inventory and are not synthesized heuristically, while closed-form poetic rules (`163.3`, `172.1`, `173`, `180`, `222` `அஞ்சிறை`, `243.3`) execute deterministically when poetic mode is enabled.
- **Edition and reading variants**: Where the 1999 critical edition (Thamodaran / Viruttiyurai) and the 1926 Project Madurai cross-check differ in reading or numbering, the discrepancy is recorded explicitly in the rule inventory rather than silently merged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (Complete 117-Sūtra Inventory Coverage)**: The feature MUST establish a complete, auditable rule inventory accounting for all **117 *Nannūl Eḻuttatikāram* sūtras**: **10 mandatory prerequisites** (*Eḻuttiyal* `93–94` *Kurriyaligaram*/*Kurriyalugaram* 6-class classifier, `102–108` *Mozhi-muthal*/*Mozhi-eetru* phonotactics; *Padaviyal* `136` *Panpuppeyar* `-மை` cascade) plus all **107 Puṇariyal sūtras** (*Uyirīṟṟup Puṇariyal* `151–203`, *Meyyīṟṟup Puṇariyal* `204–239`, *Urupu Puṇariyal* `240–257`). Every sūtra MUST be explicitly classified as one of: pure phonological rule, closed-class lexical rule, context-dependent rule, closed-form poetic/verse rule (executable under opt-in poetic mode), or non-generative definition/usage-scope record (such as meta/metrical sūtras `151–156`, `239`, `240`, `253`, `257`) — with zero sūtras omitted silently.
- **FR-002 (Edition Provenance & Evidence Layer Separation)**: Every executable rule MUST cite its exact *Nannūl* sūtra number, chapter, primary edition reference (A. Thamodaran 1999 critical edition / Sankara Namasivayar *Viruttiyurai* on TVA, cross-checked against Āṟumuka Nāvalar's *Kāṇṭikaiyurai* on TVA and the 1926 Project Madurai e-text `pmuni0147.html`), and distinct evidence layer (`root_sutra`, `commentary_gloss`, `attested_example`, or `extended_usage`, e.g., `நான் → என்` alongside root 247 `யான் → என்`). Rules MUST NEVER be hallucinated without citation, and *Nannūl* MUST NEVER be blended with *Tolkāppiyam* under an unqualified mode.
- **FR-003 (Forward Word Joining with Derivation Trace)**: The system MUST accept an explicit preceding component (*Nilaimozhi*), a following component (*Varumozhi*), a named grammar profile (`nannool-v1`), and an optional grammatical context, and MUST return the joined surface form together with an ordered derivation trace identifying every applied rule, sūtra number, alteration class (*Iyalbu*, *Thonral*, *Thirithal*, *Keduthal*), and intermediate boundary transition.
- **FR-004 (Compositional Multi-Step Rule Execution)**: Forward joining MUST support ordered multi-step derivations at a single boundary — Stage 1 stem/closed-class pre-transforms (`136` `-மை`, `183–185` pre-elision *Kurriyalugaram*, numerals, directions, pronouns) → Stage 2 multi-segment *Chariyai* staging & `உம்` post-positioning (`240–257`, folded left-to-right) → Stage 3 ordered boundary morphophonemics (`3A`: `252`/`163` → `3B`: pre-mutation `237` → `3C`: core vowel/consonant rules → `3D`: `205` with `247.5`/`250.3` anti-gemination) → Stage 4 orthographic fusion (`204`) & NFC — so complex *Nannūl* combinations (including sūtra 157 multi-alteration joins and case-suffix inflections) compose accurately without hardcoding each word pair.
- **FR-005 (Closed-Class Lexical Coverage Without External Dictionary)**: The system MUST handle all finite closed word classes explicitly enumerated in *Nannūl* — *Panpuppeyar* `-மை` stems (136), cardinal directions (186–187), number compounds (188–199, 249), demonstratives and interrogatives (163, 235, 250–251, 257), pronouns and oblique stems (218, 221, 238, 245–247), named special stems (`வாழிய`, `சாவ`, `பல`, `சில`, `நாழி`/`உரி`, `புளி`, `பீ`/`நீ`/`மீ`, `பூ`, `பனை`, `மீன்`, `தேன்`, `எகின்`, `குயின்`/`ஊன்`, `மின்`/`பின்`/`பன்`/`கன்`, `அகம்`, `ஈம்`/`கம்`/`உரும்`, `தமிழ்`/`தாழ்`, `கீழ்`, `வல்`, `நெல்`/`செல்`/`கொல்`/`சொல்`, `இல்`, `புள்`/`வள்`, `தெவ்`, `ஆ`/`மா`/`கோ`), and all 17 connecting increments (*Chariyai*) with case endings (240–257) — using self-contained declarative lexical data with zero dependency on an external dictionary.
- **FR-006 (Explicit Grammatical Context & Ambiguity Transparency)**: Context-dependent rules MUST be controllable through a two-level optional grammatical context: a coarse relation (`unspecified`, `vetrumai`, `alvazhi`) plus optional fine-grained subtypes (cases 2–7 and *Nannūl* 152 *Alvazhi* subtypes plus verb/distributive triggers), optional lexical/semantic class tags, and an opt-in poetic flag. When context is omitted or left coarse and multiple *Nannūl* outcomes are valid, the system MUST return a deterministic primary result (preferring unmarked / *Alvazhi* general rules first, then ascending sūtra order) and surface every other valid outcome in `alternatives` with its required context or optionality label. Poetic/verse-only alterations and minority contested readings (such as sūtra `206`) MUST be disabled or demoted to labeled alternatives by default.
- **FR-007 (Dictionary-Free Reverse Split Candidate Generation)**: The system MUST accept a joined Tamil surface form and named profile and return a deterministic, bounded, deduplicated list of single-boundary two-part split candidates `(first, second)`, inverting both single-step phonological rules (including all 12 `237`-interaction clusters/singletons `ற்ற/ட்ட/ன்ற/ண்ட/ன்ன/ண்ண/ஃற/ஃட` and post-210/229 single `ற/ட/ன/ண`, *Kurriyaligaram* `93`, and 6-class *Kurriyalugaram* `94`) and multi-step compositional rules (including *Panpuppeyar* `136`, *Chariyai* + case suffixes + `உம்`, and closed-class stem reductions). Candidate generation MUST apply dual pruning — *Nannūl* `102–108` *Mozhi-muthal*/*Mozhi-eetru* phonotactic filtering plus forward-join verification — and report reconstructed `(first, second)` forms, applied inverse rule ID(s) and sūtra number(s), alteration class, and zero-based byte and written-unit boundary offsets in the original input without requiring an external dictionary. Recursive multi-word chain splitting remains outside Phase 10.
- **FR-008 (Orthographic Integrity, Normalization & Error Handling)**: All operations MUST keep Tamil written units intact (including atomic ligatures `க்ஷ` and `ஸ்ரீ`), handle canonically equivalent Unicode forms consistently during rule matching, and reject empty or whitespace-only forward-join inputs, unknown profiles, or unsupported context parameters with clear, deterministic errors. When a non-empty forward join encounters a non-Tamil scalar or an explicit `ZWJ`/`ZWNJ` barrier at the join boundary, it MUST preserve all scalars verbatim and return an unaltered *Iyalbu* concatenation without silently dropping format controls.
- **FR-009 (Pluricentric Clarity & Offline Determinism)**: All operations MUST execute completely offline and produce identical, deterministic results across all supported consumer environments and regional locales. The `nannool-v1` profile MUST be explicitly documented as classical literary *Nannūl* grammar (shared across Tamil Nadu and Sri Lankan literary standards) and MUST NOT claim to represent modern colloquial dialect conventions without separate regional evidence.
- **FR-010 (Clean Provenance & Licensing Compliance)**: All pinned reference texts, rule inventories, and example datasets MUST record source URLs, checksums, and redistribution/attribution terms; copyrighted modern commentary prose MUST NOT be copied into distributed data or fixtures.

### Key Entities *(include if feature involves data)*

- **Grammar Profile**: A named, versioned grammatical tradition governing rule selection (initial profile: `nannool-v1`, scoped to *Nannūl Eḻuttatikāram* sūtras `93–94`, `102–108`, `136`, and `151–257`; future profiles such as *Tolkāppiyam* or modern prose remain strictly separate).
- **Sūtra Inventory Record**: A traceable entry for each of the **117 sūtras** (`93–94`, `102–108`, `136`, `151–257`), capturing sūtra number, chapter (`ezhuttiyal`, `padaviyal`, `uyireeru`, `meyyeeru`, `urupu`), edition locators (TVA 1999 *Viruttiyurai*, TVA *Kāṇṭikaiyurai*, `pmuni0147`), computational tier, audit status, and edition notes.
- **Punarchi Rule**: A declarative, versioned transformation unit linked to one or more sūtras, defining its pipeline stage, boundary trigger pattern, required context, alteration class (*Iyalbu*, *Thonral*, *Thirithal*, *Keduthal*), output operation, optionality, and reversibility.
- **Grammatical Context**: Two-level optional caller-supplied disambiguation metadata comprising a coarse relation (`unspecified`, `vetrumai`, `alvazhi`), optional fine-grained subtype (cases 2–7 or *Nannūl* 152 *Alvazhi* subtypes such as *vinaiyecham*, *peyarecham*, *panputhogai*), optional lexical/semantic class tags (tree name, measure word, verbal noun, rational/common noun), and an opt-in poetic/verse flag (default false).
- **Join Result & Derivation Step**: The deterministic primary joined surface form (selected by unmarked / *Alvazhi* general-rule priority, then ascending sūtra order when multiple outcomes apply), its ordered list of derivation steps (`sutra`, `rule_id`, `transform`, `before`, `after`), and any valid alternative joins in `alternatives` with their distinguishing context or optionality notes.
- **Split Candidate**: A dictionary-free single-boundary reverse analysis record pairing reconstructed `(first, second)` components (inverting single-step phonological or multi-step compositional/*Chariyai* rules) with the inverted rule trace, alteration class, and zero-based byte and written-unit boundary offsets into the submitted surface string.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (100% Sūtra Accounting)**: 100% of the **117 sūtras** (**10 mandatory prerequisites** `93–94`, `102–108`, `136` plus all **107 Puṇariyal sūtras** `151–257`) across *Nannūl Eḻuttatikāram* are explicitly accounted for and classified in the canonical rule inventory, with zero unmapped or silently omitted sūtras.
- **SC-002 (Verified Forward Accuracy Across All Three Chapters)**: 100% of reviewed positive, negative, multi-step compositional, closed-class, and context-disambiguated forward joining test cases across *Uyirīṟṟup Puṇariyal*, *Meyyīṟṟup Puṇariyal*, and *Urupu Puṇariyal* produce the exact expected joined surface form, alteration class, and sūtra trace.
- **SC-003 (Transparent Ambiguity & Context Control)**: 100% of context-sensitive test pairs select the exact target outcome when explicit context is supplied, surface all documented valid alternatives when context is omitted, and suppress verse-only alterations unless poetic mode is explicitly enabled.
- **SC-004 (Reversible Round-Trip Coverage)**: For 100% of reversible rules tested across both curated examples and 10,000+ generated inputs, the original `(first, second)` pair appears in the reverse candidate generator's bounded, deduplicated output with exact boundary coordinates and zero mid-written-unit splits.
- **SC-005 (Cross-Consumer Parity & Regional Invariance)**: 100% of active shared test cases execute identically across all supported consumer environments offline, producing identical results across Tamil Nadu and Sri Lanka literary contexts and explicit errors for every invalid input case.
- **SC-006 (Auditability & Clean Scope)**: Every executable rule and golden test case traces directly to a documented *Nannūl* sūtra and pinned reference without copying restricted commentary text, and zero external dictionary data is required for either forward joining or reverse candidate generation.

## Assumptions

- **Superseding the Nov 2026 Draft**: This specification supersedes [docs/specs/punarchi-v0.1.md](../../docs/specs/punarchi-v0.1.md). The existing source register and page-indexed locator digest in [docs/specs/punarchi-source-notes.md](../../docs/specs/punarchi-source-notes.md) are retained as foundational research inputs rather than discarded.
- **Primary Authority & Verification Model**: *Nannūl Eḻuttatikāram* (Thamodaran 1999 critical edition via TVA HTML viewer, cross-checked against Āṟumuka Nāvalar's *Kāṇṭikaiyurai* on TVA and the 1926 Project Madurai e-text) is sufficient to inventory, specify, and review all **117 sūtras** (`93–94`, `102–108`, `136`, `151–257`) for `nannool-v1` without blocking on physical print scans of separate *Tolkāppiyam* editions. Any edition discrepancy is recorded explicitly as a review note.
- **Separation from Lexical Splitting**: Selecting the single most likely lexical split from multiple grammatically valid split candidates requires a reviewed stem lexicon and morphological analyzer; that lexical ranking belongs to Phase 11 (`tamil-morph` + `tamil-lexicon`), while Phase 10 (`tamil-punarchi`) delivers the complete, dictionary-free forward joiner and bounded reverse candidate generator.
- **Phased Execution**: Implementation may proceed chapter by chapter (10A: 117-sūtra inventory & prerequisites `93–94`, `102–108`, `136` → 10B: *Uyirīṟṟup Puṇariyal* `151–203` → 10C: *Meyyīṟṟup Puṇariyal* `204–239` → 10D: *Urupu Puṇariyal* `240–257` & reverse candidates), while keeping fixtures `planned` until owner review approves activation.
- **Out of Scope for Phase 10**: *Tolkāppiyam* as an executable profile, statistical/neural Sandhi correction, full sentence-level *Valimigum*/*Valimigaa* syntactic linting (Phase 16), modern spoken-to-literary dialect normalization (Phase 15), and `apps/playground` web UI panels remain separate tracks.
