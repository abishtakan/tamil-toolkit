# Data Model — Tamil Sandhi (`tamil-punarchi`)

The [feature specification](spec.md) defines user outcomes and clarifications. The [interface contract](contracts/punarchi.md) defines request/response serialization and error handling. The [precedence & inverse matrix](research/05-precedence-and-inverse-matrix.md) defines the exact stage ordering and enum audit across all 117 sūtras.

## 1. Declarative Canonical Data (`lexicon/`)

All linguistic rules, closed word sets, and sūtra provenance live in canonical UTF-8 NFC TOML under `lexicon/` (no executable code in `lexicon/`), validated and compiled into static immutable Rust tables by `crates/tamil-punarchi/build.rs`.

### 1.1 Sūtra Inventory (`lexicon/punarchi-nannool-inventory.toml`)

Covers all **117 sūtras** (**10 mandatory prerequisites**: `93, 94, 102..=108, 136` + **107 Puṇariyal sūtras**: `151..=257`) with build-time assertion that every expected sūtra appears exactly once.

| Field | Type / Values | Validation |
| --- | --- | --- |
| `sutra` | Integer in `{93, 94, 102..=108, 136, 151..=257}` | Unique, complete 117/117 coverage. |
| `chapter` | `"ezhuttiyal" \| "padaviyal" \| "uyireeru" \| "meyyeeru" \| "urupu"` | Must match sūtra range: `93–94, 102–108` → `ezhuttiyal`, `136` → `padaviyal`, `151..=203` → `uyireeru`, `204..=239` → `meyyeeru`, `240..=257` → `urupu`. |
| `tier` | `"phonological" \| "closed_class" \| "context_dependent" \| "poetic_closed" \| "definition_or_scope"` | Explicit classification per `FR-001`. |
| `executable` | Boolean | `true` for the first 4 tiers (and attested extensions of `238`/`257`); `false` for non-generative meta/scope definitions (`151–157, 239, 240, 241, 253`). |
| `tva_page` | Integer (`166..=303`) | Direct locator into A. Thamodaran 1999 Critical Edition *Viruttiyurai* HTML viewer on TVA. |
| `kandigai_sutra` | Integer | Direct locator into TVA Āṟumuka Nāvalar *Kāṇṭikaiyurai* (`auth_pub_id=15&bookid=6&pno=<sutra>`). |
| `pm_ref` | String | Cross-check anchor in Project Madurai 1926 e-text (`pmuni0147.html`). |
| `summary` | Non-empty String | Concise factual subject statement (no copied commentary prose). |
| `edition_note` | Optional String | Records any reading/numbering discrepancy across TVA 1999, *Kāṇṭikaiyurai*, and `pmuni0147` (all 12 verified discrepancies). |

### 1.2 Executable Rule & Closed-Class Tables (`lexicon/punarchi-nannool.toml`)

| Table / Section | Fields | Validation |
| --- | --- | --- |
| `[metadata]` | `profile = "nannool-v1"`, `version = "0.1"`, `primary_edition`, `kandigai_edition`, `cross_check_edition`, `cross_check_sha256` | Exact 64-hex SHA-256 matching [tests/reference/punarchi-nannool/sources.json](../../tests/reference/punarchi-nannool/sources.json). |
| `[[closed_class]]` | `class_id`, `sutra`, `stems: Vec<String>`, `oblique_map?: Map<String, Vec<String>>`, `notes` | All stems valid NFC Tamil; unique `class_id`; valid sūtra reference. Covers *Panpuppeyar* `-மை` (`136`), bound `ஙனம்`/`மியா` (`93, 106`), directions (`186–187`), numerals (`188–199, 249`), pronouns (`218, 221, 245–247`), demonstratives/interrogatives (`163, 235, 250–251, 257`), and named stems (`வாழிய`, `சாவ`, `பல/சில`, `நாழி/உரி`, `புளி`, `பீ/நீ/மீ`, `பூ`, `பனை`, `மீன்`, `தேன்`, `எகின்`, `குயின்/ஊன்`, `மின்/பின்/பன்/கன்`, `அகம்`, `ஈம்/கம்/உரும்`, `தமிழ்/தாழ்`, `கீழ்`, `வல்`, `நெல்/செல்/கொல்/சொல்`, `இல்`, `புள்/வள்`, `தெவ்`, `ஆ/மா/கோ`). |
| `[[chariyai]]` | `id`, `form`, `sutra`, `attach_classes`, `case_filter?`, `stack_after?`, `post_um?: bool`, `suppress_205?: bool` | Encodes all 17 *Chariyais* (`244`), stacked chains (`அற்று+இன்`, `அத்து+இன்+உ`, `வ்+இன்+உ`, `அன்+உ`, `ன்+அ`), `254` `இன்`-before-`இன்` blocking, and `உம்` post-positioning (`245–246`). |
| `[[case_suffix]]` | `case_number: 2..=7`, `form`, `sutra`, `force_165?: bool` | Encodes inflected case endings (`ஐ`, `ஆல்`, `கு`, `இன்`, `அது`, `கண்`, plus `ஒடு`, `ஆது`, `அ`); `கு` sets `force_165 = true` per `242.2`. |
| `[[rule]]` | `id`, `sutra`, `chapter`, `stage: 1..=4`, `substage: "1a" \| "1b" \| "1c" \| "2" \| "3a" \| "3b" \| "3c" \| "3d" \| "4"`, `priority`, `transform`, `relation`, `subtype?`, `lexical_class?`, `poetic: bool`, `optional: bool`, `reversible: bool`, `left_match`, `right_match`, `action`, `flags?`, `evidence_layer` | Every `id` unique; `sutra` exists in 117-sūtra inventory; `substage` + `priority` enforce intra-stage ordering (`183` in `1c` before `164/165` in `3c`; `252`/`163` in `3a` before `162` in `3c`; `237` in `3b` before `209/210/227/228/229` in `3c`; `205` in `3d` respecting `suppress_205`); `evidence_layer` in `root_sutra \| commentary_gloss \| attested_example \| extended_usage`. |

## 2. Runtime Domain Entities (`crates/tamil-punarchi`)

### 2.1 Profile & Two-Level Grammatical Context

| Entity | Fields / Values | Constraints |
| --- | --- | --- |
| `PunarchiProfile` | `NannoolV1` (`"nannool-v1"`) | Default when omitted in dispatcher; any unknown profile string fails with `"unsupported punarchi profile"`. |
| `PunarchiChapter` | `Ezhuttiyal`, `Padaviyal`, `Uyireeru`, `Meyyeeru`, `Urupu` | Filter for `punarchi_rules`. |
| `GrammaticalRelation` | `Unspecified`, `Vetrumai`, `Alvazhi` | Default `Unspecified`. |
| `ContextSubtype` | *Vetrumai (6):* `Case2`..`Case7`. *Alvazhi (14 Nannūl 152 + 5 specific):* `Vinaithogai`, `Panputhogai`, `Uvamaithogai`, `Ummaithogai`, `Anmozhi`, `Ezhuvai`, `Vili`, `Peyarecham`, `Vinaiyecham`, `VinaiMutru`, `KurippuVinaiMutru`, `Idaiccol`, `Uriccol`, `Adukkuthodar`, `Imperative`, `SecondPersonVerb`, `Viyankol`, `Distributive`, `Ilakkanappoli` | Must be compatible with `relation` if both are supplied (e.g., `Case2` with `Alvazhi` returns `"unsupported or incompatible punarchi subtype"`). Overt *Viri* vs elided *Thogai* is inferred from whether `second` is an overt case suffix. |
| `LexicalClass` | `RationalNoun`, `NonRationalNoun`, `CommonNoun`, `TreeName`, `TastePuli`, `MeasureWord`, `QuantityWord`, `NumberWord`, `DirectionWord`, `Pronoun`, `Demonstrative`, `Interrogative`, `BranchName`, `QualityNoun`, `VerbalNounRoot`, `VerbalNounDerived`, `NegationStem`, `CliticParticle`, `LocativeParticle`, `TemporalParticle`, `NegativePluralVerb`, `PassiveActionCompound`, `FoodSesame`, `SwanEkin`, `DiceVal`, `CloudSel`, `SmithKol` | Optional caller-supplied semantic/morphological class tag gated by audited Tier C sūtras. |
| `PunarchiContext` | `relation: GrammaticalRelation`, `subtype: Option<ContextSubtype>`, `lexical_class: Option<LexicalClass>`, `poetic: bool` | `poetic` defaults to `false` (opt-in closed-form verse rules). |

### 2.2 Forward Join Outputs

| Entity | Fields | Invariants |
| --- | --- | --- |
| `AlterationKind` | `Iyalbu`, `Thonral`, `Thirithal`, `Keduthal` | Maps directly to *Nannūl* 153–154. |
| `DerivationStep` | `sutra: u16`, `rule_id: String`, `stage: u8`, `transform: AlterationKind`, `before: String`, `after: String` | Ordered strictly by pipeline execution (`stage` non-decreasing per fold; multi-segment folds record each segment step in execution order). Non-Tamil/joiner barrier emits `sutra: 153`, `rule_id: "nannool_153_iyalbu_passthrough"`. |
| `JoinAlternative` | `surface: String`, `transform: AlterationKind`, `steps: Vec<DerivationStep>`, `required_context: Option<String>`, `optional_variant: bool`, `poetic: bool` | Deduplicated by `(surface, rule_ids)`; ordered by canonical priority (unmarked/*Alvazhi* general rules first, then ascending sūtra number). |
| `PunarchiJoinResult` | `profile: PunarchiProfile`, `surface: String`, `transform: AlterationKind`, `steps: Vec<DerivationStep>`, `alternatives: Vec<JoinAlternative>` | Always has a non-empty deterministic primary `surface`; `alternatives` never duplicates the primary `(surface, rule_ids)`. |

### 2.3 Reverse Split Candidates

| Entity | Fields | Invariants |
| --- | --- | --- |
| `SplitCandidate` | `first: String`, `second: String`, `sutra: u16`, `rule_id: String`, `transform: AlterationKind`, `steps: Vec<DerivationStep>`, `split_byte: usize`, `split_unit: usize` | `0 < split_byte < surface.len()` and `0 < split_unit < total_units`; `split_byte` and `split_unit` land on an exact `tamil_core::Letters` written-unit boundary (never inside `க்ஷ`, `ஸ்ரீ`, or a vowel sign). Dual-pruned via *Nannūl* `102–108` phonotactics + forward-join verification. Deterministically ordered by `(split_byte, sutra, first, second)`. |

## 3. State & Pipeline Transitions

```text
Input (first, second, context)
  ├─ Empty/whitespace check ──► Error("punarchi: input components must not be empty")
  ├─ Boundary non-Tamil or ZWJ/ZWNJ barrier ──► Verbatim Iyalbu passthrough (sutra 153)
  └─ Canonical NFC view + Sutra 94 Kurriyalugaram/Mutriyalugaram classification:
       Stage 1: 1A Panpuppeyar -மை (136) ─► 1B Closed stems (186–199, 247, ...) ─► 1C Pre-elision 183–185
       Stage 2: Multi-segment Chariyai staging & உம் post-positioning (240–257) ─► left-to-right fold:
         Stage 3: 3A (252, 163) ─► 3B (pre-mutation 237) ─► 3C (core V/C rules) ─► 3D (205 unless suppress_205)
         Stage 4: Orthographic fusion (204) + NFC normalization
       ──► Deduplicate branches ──► Canonical priority sort ──► Primary + Alternatives
```

## 4. Verification Records

- **Planned Golden Suite (`tests/golden/punarchi_nannool.jsonl`):** Registered as `planned` in `tests/golden/manifest.json` until owner activation review. Escaped non-ASCII JSONL with globally unique IDs (`punarchi_*`), explicit source sūtra citations + witness tags (`viruttiyurai_pno` / `kandigai`), dialect/region labels (`COMMON`, `TN`, `SL`), and exact error-contract rows.
- **Standalone Rust Tests:**
  - `inventory_completeness.rs`: verifies all **117 sūtras** (`93–94, 102–108, 136, 151–257`) are present, validly classified, and matched to executable rules where `executable == true`.
  - `prereq_golden.rs`, `uyireeru_golden.rs`, `meyyeeru_golden.rs`, `urupu_golden.rs`, `context_ambiguity_golden.rs`, `split_golden.rs`: chapter-grouped and context/ambiguity/poetic verification against `punarchi_nannool.jsonl`.
  - `roundtrip_properties.rs`: 10,000-case `proptest` checking join↔split round-trip recall across all 28 reversible pattern families, `102–108` phonotactic pruning, joiner/non-Tamil preservation, written-unit boundary integrity, and bounded deterministic output.
