# Phase 0 Research — Tamil Sandhi (`tamil-punarchi` / *Nannūl Eḻuttatikāram* 117 Sūtras)

This summary synthesizes the exhaustive line-by-line primary-source extraction across all **117 *Nannūl* sūtras** (`93–94`, `102–108`, `136`, `151–257`), archived under `specs/025-tamil-punarchi/research/`:

- [00-prerequisites-eluttiyal-padaviyal.md](research/00-prerequisites-eluttiyal-padaviyal.md) — *Eḻuttiyal* `93–94`, `102–108` & *Padaviyal* `136`
- [01a-uyireeru-151-177.md](research/01a-uyireeru-151-177.md) — *Uyirīṟṟup Puṇariyal* Part A (`151–177`)
- [01b-uyireeru-178-203.md](research/01b-uyireeru-178-203.md) — *Uyirīṟṟup Puṇariyal* Part B (`178–203`)
- [02-meyyeeru-204-239.md](research/02-meyyeeru-204-239.md) — *Meyyīṟṟup Puṇariyal* (`204–239`)
- [03-urupu-240-257.md](research/03-urupu-240-257.md) — *Urupu Puṇariyal* (`240–257`)
- [04-cross-book-and-edge-cases.md](research/04-cross-book-and-edge-cases.md) — Witness comparison, *Tolkāppiyam* boundary, modern TN/SL nuances & computational traps
- [05-precedence-and-inverse-matrix.md](research/05-precedence-and-inverse-matrix.md) — Formal precedence DAG, pipeline ordering proof, complete 28-pattern inverse matrix & enum audit

---

## 1. Source Pinning & 117-Sūtra Coverage Strategy

**Decision** — Pin verified source URLs, SHA-256 digests, and license constraints in [tests/reference/punarchi-nannool/sources.json](../../tests/reference/punarchi-nannool/sources.json) linking all three primary digital witnesses (without copying copyrighted TVA commentary prose or duplicating `pmuni0147.html` into git):
1. **Primary Critical Edition:** TVA A. Thamodaran 1999 Critical Edition / Sankara Namasivayar *Viruttiyurai* (`auth_pub_id=17&bookid=6`, viewer pages `166–180`, `198–200`, `218–303`).
2. **Pluricentric TN/SL Cross-Check Commentary:** TVA Āṟumuka Nāvalar *Kāṇṭikaiyurai* (`auth_pub_id=15&bookid=6`, Jaffna/SL & TN standard) — confirming 100% rule agreement across Tamil Nadu and Sri Lankan literary traditions (`COMMON`).
3. **Root-Text Cross-Check:** Project Madurai `pmuni0147.html` (1926 Vavilla edition, `137,243` bytes, SHA-256 `b970b4ee13b4b4e96dfd641b1e37d1c87bdfdc0b83fce1fcb24c664841671955`).

Record all **117 sūtras** (**10 mandatory prerequisites** `93–94`, `102–108`, `136` + **107 Puṇariyal sūtras** `151–257`) in `lexicon/punarchi-nannool-inventory.toml`, capturing all **12 verified witness discrepancies** in `edition_note` (including `pmuni0147`'s duplicate `242` numbering typo on sūtra `241`, sūtra `195` `முதலிறு` vs `முதல் இரு`, sūtra `206` contested `இ` before `ய`, sūtra `244` `ன` vs `ன்`, and sūtra `247` absence of `நான்`).

**Rationale** — *Nannūl*'s Puṇariyal (`151–257`) cannot execute accurately without *Eḻuttiyal* `93` (*Kurriyaligaram*), `94` (6-class *Kurriyalugaram* vs 2-letter CVCu *Mutriyalugaram*), `102–108` (*Mozhi-muthal*/*Mozhi-eetru* phonotactics for reverse split pruning), and *Padaviyal* `136` (*Panpuppeyar* `-மை` cascade explicitly extended to *padappuṇarcci* in both commentaries). *Tolkāppiyam* divergences remain strictly segregated for a future `tolkappiyam-v1` profile, and sentence-level *Valimigum*/*Valimigaa* syntactic linting remains in Phase 16.

---

## 2. Five-Tier Classification of All 117 Sūtras

Every sūtra in `lexicon/punarchi-nannool-inventory.toml` carries one explicit computational tier:

1. **`phonological`**: Pure orthographic/phonological structure (`93–94`, `102–108`, `162`, `164`, `204–205`, `209–210`, `219`, `227–228`, `237`, `252`, etc.).
2. **`closed_class`**: Finite closed word/morpheme sets explicitly enumerated in *Nannūl* with zero external dictionary dependency:
   - *Panpuppeyar* `-மை` stems (`136`), bound `ஙனம்`/`மியா` (`93, 106`),
   - Demonstratives & interrogatives (`163, 235, 250–251, 257` including `எவ் → எவற்றை`),
   - Cardinal directions & `தெங்கு` (`186–187`),
   - All numeral compounds (`188–199, 249`),
   - Pronouns & quantifiers (`218, 221, 238, 245–247` — noting `எல்லாம்` *uyartiṇai* takes `நம்` → `எல்லாநம்மையும்`, while `எல்லாரும்` takes `தம்` → `எல்லார்தம்மையும்`; `நான் → என்` labeled as `extended_usage`),
   - Named special stems (`168–170, 174–175, 177–178, 200, 203, 213–217, 222–223, 225–226, 231–234, 236, 248`),
   - All **17 *Chariyais*** (`244`) & **6 inflected case endings** (`240–242`).
3. **`context_dependent`**: Disambiguated by two-level `PunarchiContext` (`158–161, 165–167, 171, 176, 179, 181–185, 201–202, 206–208, 211–212, 220, 224, 229–230, 242–243, 254–256`).
4. **`poetic_closed`**: Closed-form verse-only rules active only when `context.poetic = true` (`163.3, 172.1, 173, 180, 222` `அஞ்சிறை`, `243.3`). *(Note: `177`, `228`, `235`, `255` are active in default `nannool-v1`; contested minority `206` is flagged `optional = true` under `context_dependent`.)*
5. **`definition_or_scope`**: Structural definitions & non-generative meta/usage principles (`151–157, 239, 240, 241, 253` with `executable = false`; `238` and `257` are `definition_or_scope` whose specific attested extensions—`Vetrumai` content-word delegation `245–251` and `எவ் → எவற்றை`—are linked as executable rules).

---

## 3. Compositional 4-Stage Pipeline with Strict Intra-Stage Precedence

Forward synthesis runs a bounded, acyclic pipeline inside `crates/tamil-punarchi` (Rank 2, depending strictly on `tamil-core` and `tamil-norm`, `#![forbid(unsafe_code)]`) carrying transient `BoundaryFlags` (`is_derived_final`, `block_165`, `force_165`, `suppress_205`, `is_chariyai_attu`, `triggered_237`):

1. **Stage 0 — Validation, Joiner/Non-Tamil Barrier & Phonology (`94`, `205`)**: Reject empty/whitespace inputs and invalid/incompatible context tags; preserve non-Tamil or `ZWJ`/`ZWNJ` boundary barriers verbatim as *Iyalbu* (`153`); normalize working view to NFC; compute 6-class *Kurriyalugaram* vs *Mutriyalugaram* (`94`, ensuring 2-letter short-vowel CVCu words `பசு/புது/அது/தெரு/கடு` are classified *Mutriyalugaram*) and *Thanikkuril* status.
2. **Stage 1 — Stem & Closed-Class Pre-Transform (`1A → 1B → 1C`)**:
   - **1A (`136`)**: *Panpuppeyar* `-மை` 8-operation ordered cascade (`ஈறு போதல் → இனையவும்/இடையுகரம் → ஆதிநீடல்/அடியகரம் ஐ → தன்னொற்று இரட்டல்/மெய்திரிதல்/இனமிகல்`).
   - **1B**: Numerals (`199 > 194 > 198 > 196 > 197 > 195 > 188–193`), directions (`186–187`), pronoun oblique stems (`247`/`238`, setting `suppress_205 = true` for 4th-case `+அ` and 6th-case `அது/ஆது/அ` per `247.5`), and named stems (`168–170, 172–174, 177, 180, 203, 222, 233`).
   - **1C (`183–185`)**: Pre-elision *Kurriyalugaram* stem strengthening — **`183` (`டு→ட்டு`, `று→ற்று`) MUST run here BEFORE Stage 3 (`164`/`165`)** so `காடு + எருமை → காட்டெருமை` and `ஆடு + கால் → ஆட்டுக்கால்` compose cleanly without losing doubling!
3. **Stage 2 — Multi-Segment *Chariyai* Staging & Left-to-Right Folding (`240–257`)**:
   - Expands `(stem', second)` into bounded segments `[s_0, ..., s_k]` (`k <= 5`), including stacked *Chariyais* (`அற்று+இன்`, `அத்து+இன்+உ`, `வ்+இன்+உ`, `அன்+உ`, `ன்+அ`) and post-positioned `உம்` (`245` `எல்லாவற்றையும்`/`எல்லாநம்மையும்`, `246` `எல்லார்தம்மையும்`/`எல்லீர்நும்மையும்`).
   - Enforces **`250.3`** (`suppress_205 = true` on `அவ்/இவ்/உவ்/எவ் + அற்று` → `அவற்றை`, never `*அவ்வற்றை`), **`254`** (blocks `இன்` *Chariyai* before 5th-case `இன்` *urupu*), and **`242.2`** (`கு` doubles after *Uyartinai* while `கண்` respects `159`).
   - Folds multi-segment chains strictly left-to-right through Stages 3–4.
4. **Stage 3 — Ordered Boundary Morphophonemics (`3A → 3B → 3C → 3D`)**:
   - **3A (`252`, `163`)**: `252` (`அத்தின் அகரம்`: `மர + அத்து → மர + த்து`) executes **BEFORE `162`** so `*மரவத்து` is never emitted; `163` (`அ/இ/உ/எ`) executes before `162`/`158`.
   - **3B (`237`)**: Mutates *Varumozhi*-initial `த → ற/ட` and `ந → ன/ண` **BEFORE `209/210/227/228/229`** mutate or delete *Nilaimozhi*-final `ன்/ல்/ண்/ள்`, recording `triggered_237`.
   - **3C**: Disjoint boundary rules (`93+164 > 162`; `158` & *Valimigal* blockers `159–182, 200–201 > 165`; `ண்/ன்` `211–218 > 159 > 210 > 209`; `ம்` `221–223 > 220 > 219`; `ய்/ர்/ழ்` `225–226 > 159 > 224`; `ல்/ள்` `230–234 > 228 > 229 > 159 > 227` with `117` cluster ban blocking `*ல்த/*ள்த`; `வ்` `235–236`; `C+ய` `158 > opt 206`).
   - **3D (`205`)**: *Thanikkuril Otru* doubling before vowels unless `suppress_205` is set.
5. **Stage 4 — Orthographic Fusion (`204`) & Canonical NFC (`tamil-norm`)**: Fuse trailing `Mei` + leading `Uyir` via `tamil_core::compose_uyirmei`, normalize to NFC, deduplicate `(surface, rule_ids)`, and sort deterministically (unmarked/*Alvazhi* general rules first, then ascending sūtra number).

---

## 4. Dictionary-Free Reverse Split Candidate Generation (`split.rs`)

**Decision** — Implement `punarchi_split_candidates(surface, profile, poetic)` over written-unit boundaries (`tamil_core::Letters`, capped at 256 UTF-8 bytes) covering the **complete 28-pattern inverse matrix** in [05-precedence-and-inverse-matrix.md](research/05-precedence-and-inverse-matrix.md) §3, including:
- Direct *Iyalbu* (`153`), *Udalmel Uyir* (`204`), *Thanikkuril Otru* (`205`),
- *Udambadumei* (`162`), *Kurriyalugaram* (`164`, validated via `94`), *Kurriyaligaram* (`93+164` `கி/சி/டி/தி/பி/றி + ய`),
- Doubled stops (`க்க/ச்ச/த்த/ப்ப`), nasal insertions (`ங்க/ஞ்ச/ந்த/ம்ப`), nasal/glide geminates (`ஞ்ஞ/ந்ந/ம்ம/ய்ய/வ்வ/ங்ங`),
- **All 12 `237`-interaction outputs**: **`ற்ற`**, **`ட்ட`**, **`ன்ற`**, **`ண்ட`**, **`ன்ன`**, **`ண்ண`**, **`ஃற`**, **`ஃட`**, and **non-*Thanikkuril* deletion singletons `ற`, `ட`, `ன`, `ண`** (`210`/`229`: `வேறீது`, `வாடீது`, `தூணன்று`, `அரசனல்லன்`), plus `ற்/ட் + க/ச/ப`, `ன்/ண் + ஞ/ம`, `ஃ + க/ச/த/ப` (`235`),
- Compositional *Chariyai* + case + `உம்` inversions (`243–253, 257`), oblique pronouns (`247`), and closed-class tables (*Panpuppeyar* `136`, directions `186`, numerals `188–199`, `பல/சில` `170`, named stems).

**Dual Pruning Guarantee**: Every candidate MUST pass BOTH:
1. ***Nannūl* `102–108` *Mozhi-muthal* / *Mozhi-eetru* phonotactic filter** (`is_valid_mozhi_eetru(first)` and `is_valid_mozhi_muthal(second)`), AND
2. **Forward-verification pruning** (re-running `punarchi_join` on `(cand.first, cand.second)` under its inferred context and confirming it reproduces `surface`).

---

## 5. Staged Integration & Release-Policy Alignment

1. Keep `crates/tamil-punarchi` private (`publish.workspace = true`) and `tests/golden/punarchi_nannool.jsonl` as `planned` in `tests/golden/manifest.json` during Phases 10A–10D while completing unit, chapter golden, and 10,000-case property verification.
2. Validate multi-runtime parity (Rust, Python, Node/browser WASM, Dart) in an isolated preactivation candidate worktree using `TAMIL_GOLDEN_INCLUDE_PLANNED=punarchi_nannool.jsonl`.
3. Only after owner approval of both fixture activation (`manifest.json`) and public crate scope (`release-policy.toml`, `tools/release_files.py`, `.github/workflows/publish-crate.yml`), integrate into `tamil-toolkit`, sync release files, and run `just agent-pre-stop-gate`, `just test-dart`, and isolated archive checks.
