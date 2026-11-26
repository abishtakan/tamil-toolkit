# Phase R2: Cross-Book Witness Comparison & Computational Edge-Case Audit (`025-tamil-punarchi`)

**Scope**: Comparative witness audit for *Nannūl Eḻuttatikāram* (**117 sūtras**: *Eḻuttiyal* `93–94`, `102–108`, *Padaviyal* `136`, and Puṇariyal `151–257`), *Tolkāppiyam* divergence boundaries, Modern Standard Tamil (TN SCERT / SL NIE / TVA) pedagogical alignment, and known computational Tamil Sandhi traps for `crates/tamil-punarchi`.

---

## 1. Nannūl Witness Comparison: Viruttiyurai (1999 Thamodaran) vs Arumuka Navalar Kandigaiyurai vs Project Madurai (1926 Vavilla)

Across *Uyirīṟṟup Puṇariyal* (151–203), *Meyyīṟṟup Puṇariyal* (204–239), and *Urupu Puṇariyal* (240–257), the three pinned digital witnesses—**TVA 1999 Critical Edition** (A. Thamodaran / Sankara Namasivayar *Viruttiyurai*), **TVA Arumuka Navalar *Kandigaiyurai*** (Jaffna/SL & TN pedagogical standard), and **Project Madurai** (`pmuni0147.html`, 1926 Vavilla e-text)—agree on the structural grammar. Specific reading, numbering, and interpretive nuances to track in `edition_note`:

| Sūtra | Topic | Viruttiyurai (1999 Thamodaran) | Arumuka Navalar *Kandigaiyurai* | Project Madurai (`pmuni0147.html`, 1926) | Engine / Inventory Implication |
| --- | --- | --- | --- | --- | --- |
| **136** | *Panpuppeyar* (`-மை`) | In *Padaviyal* (p. 198–199), explicitly extended to word compounding (*padappuṇarcci*) via *oppin muṭittal* (`நல்லன்`, `கரியன்`, `பாசி`, `பைந்தார்`, `வெற்றிலை`, `சேதாம்பல்`). | Identical extension: `இவ் விகாரங்கள் பதப் புணர்ச்சிக்கும் கொள்க` (sutra=136). | Identical root text (`ஈறு போதல் இடை உகரம் இ ஆதல்...`). | Must be modeled in Stage 1 (`QualityNoun` / `Panputhogai`) even though 136 sits outside 151–257. |
| **201** | `ஏ`/`ஓ` particles | `இடைச்சொல் லேயோ முன்வரி னியல்பே` — `முன்` means *after* `ஏ`/`ஓ` (`அவனே கொண்டான்`, `அவனோ கொண்டான்`) when followed by *Vallinam*, blocking 165 doubling. | Identical: `ஆறு ஏகாரத்தின் முன்னும் எட்டு ஓகாரத்தின் முன்னும் வல்லினம் வரின்... இயல்பாகும்`. | Identical root text (`இடைச்சொல் ஏ ஓ முன் வரின் இயல்பு ஏ`). | Directionality guard: `ஏ`/`ஓ` is **`first`** (*Nilaimozhi*), *Vallinam*-initial word is **`second`** (*Varumozhi*). |
| **206** | `இ` before `ய` | `துன்னு மென்று துணிநரு முளரே` — notes *iḻivu-siṟappummai* (`-உம்`): minority accepts `இ` insertion (`வேளியாவன்`, `மண்ணியாது`); majority keeps 158 natural join (`வேள்யாவன்`, `மண்யாது`). | Identical minority/majority split (`அரிதிற் கொள்வாரும் சிலருளர்`; majority follows 158). | Identical root text (`...துன்னும் என்று துணிநர் உம் உளர் ஏ`). | Mark `optional = true` (default primary: 158 *Iyalbu*; alternative: 206 `இ` insertion). |
| **227** | `ல்`/`ள்` + *Vallinam* | In *Alvazhi*, `ல்`/`ள்` optionally alternate (`உறழ்வு`: `கல்குறிது` / `கற்குறிது`), **except** before `த` (forbidden cluster per 117), where `ஏற்புழிக்கோடல்` forces assimilation (`கற்றீது`, `முட்டீது`). | Identical exception: `தகரம் வரின்... கற்றீது முட்டீது எனத் திரிபு ஒன்றுமே கொள்க`. | Identical root text (`ல ள வேற்றுமை இல் ற ட உம்...`). | Do **not** emit unassimilated `*கல்தீது` or `*முள்தீது` as alternatives in *Alvazhi*. |
| **241** | Case endings follow nouns | `241. பெயர்வழித் தம்பொரு டரவரு முருபே` (p. 286). | `241` identical. | Raw `pmuni0147.html` exhibits a numbering typo/shift around the *Urupu* header; normalize to critical 241 in `punarchi-nannool-inventory.toml`. | Record raw `pmuni0147` numbering discrepancy in `edition_note` for 241. |
| **244** | 17 *Chariyais* (`ன` vs `ன்`) | Root text ends in `ன` (`...ஐகுன`); glosses `னவ்வும்` with example `ஆன்`. | Root text ends in `ன`, but glosses `னகர மெய் ஈறாக` and gives example `ன் = ஆன்`. | Root text ends in `ன` (`...ஏ அ உ ஐ கு ன`). | Store canonical `ன்` consonant-stem behavior with `edition_note` documenting `ன`/`ன்` orthography in root vs gloss. |
| **247** | Pronouns (`நான்` vs `யான்`) | Root lists `தான், தாம், நாம்` and `யான், யாம், நீ, நீர்` (`என், எம், நின், நும்`). Does **not** list `நான்` in root 247; commentary brings `நீ→உன்`, `நீர்→உம்` via `பிற`. | Identical: `பிற என்ற மிகையால் நீ, நீர் என்பன முறையே உன், உம் எனவும் திரிந்து வருதல் கொள்க`. | Identical root text (`...யான் யாம் நீ நீர் என் எம் நின் நும் ஆம் பிற`). | Support `நான் → என்` explicitly as an extended/modern-aligned closed-class mapping (`பிற` / usage) while keeping `யான் → என்` as the primary 247 root rule. |

### Pluricentric Alignment (Tamil Nadu & Sri Lanka)
- **Literary Standard (`COMMON`)**: Arumuka Navalar's *Kandigaiyurai* (19th-century Jaffna/Sri Lankan Tamil revivalist standard, also widely adopted in Tamil Nadu) and the Madras/Thamodaran *Viruttiyurai* (Sankara Namasivayar / Sivagnana Munivar) **agree on all 107 Puṇariyal rules**.
- **Pedagogical Nuance Only**: Differences between TN and SL editions are confined to commentary verbosity (*Kandigaiyurai*'s 5-part concise format vs *Viruttiyurai*'s scholastic *utti* debates), not morphophonemic outcomes. Therefore, `nannool-v1` is genuinely pluricentric (`COMMON`) across TN and SL literary Tamil.

---

## 2. Tolkāppiyam vs Nannūl Divergences (Strictly Comparative — DO NOT Merge into `nannool-v1`)

*Tolkāppiyam Eḻuttatikāram* and *Nannūl Eḻuttatikāram* belong to different historical strata (~1,000+ years apart) and use incompatible rule architectures:

| Dimension | *Tolkāppiyam Eḻuttatikāram* | *Nannūl Eḻuttatikāram* (`nannool-v1`) |
| --- | --- | --- |
| **Chapter Architecture** | Six Puṇarchi-related chapters: *Puṇariyal*, *Tokaimarapu*, *Urupiyal*, *Uyirmayaṅkiyal*, *Puḷḷimayaṅkiyal*, *Kuṟṟiyalukarappuṇariyal*. | Condensed into three chapters: *Uyirīṟṟup Puṇariyal* (151–203), *Meyyīṟṟup Puṇariyal* (204–239), *Urupu Puṇariyal* (240–257). |
| ***Udambadumei* (Glides)** | Contextual/dispersed across vowel-meeting rules; underspecified compared to *Nannūl*'s unified formula. | Explicit unified rule (Sūtra 162): `இ/ஈ/ஐ` → `ய்`; other vowels → `வ்` (`ஏ` takes `ய்` or `வ்`). |
| **Pronouns (`யான்` vs `நான்`)** | Only `யான்`/`யாம்` are recognized as standard first-person pronouns; **`நான்` is absent**. | Accommodates post-Sangam evolution (`நான்` in broader usage; `யான்`/`யாம்`/`நாம்` in 247). |
| **1st/2nd Person & *Chariyai*** | Broader archaic *chariyai* inventory (`அன்`, `ஆன்`, `இன்`, `அல்`, `அற்று`, `இற்று`, `அத்து`, `அம்`, `ஒன்`, etc.) with granular lexical/semantic conditioning. | Streamlined to 17 *general chariyais* (Sūtra 244) with tighter structural triggers (`அத்து` for `ம்`-final neuter nouns, `அற்று` for `பல`/`சில`/`எல்லாம்`). |
| **`ஆய்தம்` (*Aytham*)** | Extensive *Aytham* conditioning across *Kuṟṟiyalukarappuṇariyal* and *Puḷḷimayaṅkiyal* (including `ஃ` retention/conversion in archaic forms). | Scoped primarily to `ல்`/`ள்` + `த` in *Alvazhi* after short vowel (228: `கஃறீது`, `முஃடீது`), `அஃது`/`இஃது`/`உஃது` (251), and `வஃகு`/`தெவ்` edge cases. |
| **Special Stems & Numerals** | Preserves archaic Sangam verb/measure/numeral alternations (e.g., older *Uyirmayaṅkiyal* forms of `சாவ`, `வாழிய`, and archaic compound numerals). | Codified into closed-class sūtras 168–170 (`வாழிய`, `சாவ`) and 188–199 (standardized medieval numeral compounds like `தொண்ணூறு`, `தொள்ளாயிரம்`). |

**Why `nannool-v1` must remain strictly segregated**: Mixing *Tolkāppiyam* rules (e.g., archaic *chariyai* distributions or *Kuṟṟiyalukarappuṇariyal* exceptions) into `nannool-v1` would violate sūtra traceability (`FR-002`) and produce spurious alternatives not attested in *Nannūl*. *Tolkāppiyam* rules MUST be deferred to a separate `tolkappiyam-v1` profile.

---

## 3. Modern Standard Tamil Pedagogical Nuances (TN SCERT, SL NIE, TVA *Thamizhai Pizhaiyinri Ezhuthuvom*)

Modern Tamil style guides—TN SCERT textbooks, Sri Lanka National Institute of Education (SL NIE) syllabi (Grades 6–11), and Tamil Virtual Academy's *Thamizhai Pizhaiyinri Ezhuthuvom*—teach a subset of *Nannūl* adapted for contemporary prose:

1. **Syntactic *Valimigum* / *Valimigaa* (Vallinam Doubling)**:
   - **Doubles (*Valimigum*)**: 2nd/4th case *viri* (`மரத்தைப் பார்த்தான்`, `வீட்டுக்குப் போனான்`), demonstratives/interrogatives (`அ/இ/உ/எ`, `அந்த/இந்த/எந்த` + noun), `அங்கு/இங்கு/எங்கு`, vowel-ending *vinaiyecham* (`ஓடிப் பார்த்தான்`, `செய்து பார்த்தான்`), `ஈறுகெட்ட எதிர்மறைப் பெயரெச்சம்` (`ஓடா + குதிரை → ஓடாக் குதிரை`), *panputhogai* / *uvamaithogai* (`செந்தாமரை`, `மலர்ப்பாதம்`).
   - **Does NOT Double (*Valimigaa*)**: Subject (*ezhuvai*, `தமிழ் கற்றார்`), *peyarecham* (`எழுதிய பாடல்`, `வந்த பையன்`), *ummaithogai* (`தாய் தந்தை`), *vinaithogai* (`வளர் தமிழ்`, `ஊது குழல்`), vocative (*vili*, `நண்பா கேள்`), *adukkuthodar* / *irattaikkilavi* (`பாம்பு பாம்பு`, `சலசல`), and multi-word cardinal numbers (`மூன்று புத்தகம்`).
2. **Modern Case Endings & Pronouns**:
   - Modern prose heavily uses `-இல்` (locative), `-இடம்` (locative/dative-locative), `-உடன்` / `-ஓடு` (sociative), alongside classical `ஐ`, `ஆல்`, `கு`, `இன்`, `அது`, `கண்`.
   - Modern prose standardizes `நான் → என்` and `நீ → உன்` (replacing `யான் → என்` and `நீ → நின்` in everyday writing).
3. **Obsolescence of Archaic Forms**:
   - Proximate demonstrative `உ` (`உவன்`, `உது`, `உஃது`) and `ஃ` *Aytham* sandhi (`கஃறீது`, `முஃடீது`) are absent from everyday modern prose, appearing only in classical/academic contexts.

### Architectural Boundary
- **Phase 10 (`nannool-v1`)**: Single-boundary word-level morphophonemics for all **117 *Nannūl* sūtras** (`93–94`, `102–108`, `136`, `151–257`, including closed-class *Valimigum* triggers like `அ/இ/உ/எ` 163, `165`, `201`, and classical `யான்`/`நான்`).
- **Phase 16 (*Valimigum* / *Valimigaa* Syntactic Linter)**: Sentence- and phrase-level syntactic disambiguation (identifying *ezhuvai*, *vinaiyecham*, *peyarecham*, *thogai* across multi-word clauses) belongs to Phase 16, NOT Phase 10.
- **Future `modern-prose-v1` profile**: Optional modern-only profile omitting `உ`-demonstrative/`ஃ` alternatives and defaulting to `-இல்`/`-இடம்`/`-உடன்`/`நான்`/`உன்`.

---

## 4. Known Computational Tamil Sandhi Bugs & Edge-Case Traps

From Tamil computational morphology literature (e.g., *ThamizhiMorph* / *ThamizhiFST*, *Open-Tamil*, ACL South Asian NLP workshops), naive Sandhi joiners and splitters fail on the following ten traps:

### a. *Kurriyalugaram* vs *Mutriyalugaram* Trap
- **Rule**: Only `கு/சு/டு/து/பு/று` at the end of a **2-letter `CVVCu` (*Nedil-thodar*)** word (`நாகு`, `ஆடு`, `காடு`, `வீடு`), **3+ letter** word (`வரகு`, `தெங்கு`, `கன்று`, `வண்டு`, `மார்பு`), or **monosyllabic/polysyllabic `Vanthodar`** (`பாட்டு`, `பத்து`) is *Kurriyalugaram* (elides `உ` before vowels per 164; doubles `ட்/ற்` in *Vetrumai* per 183).
- **The Trap**: **2-letter `CVCu` (*Thanikkuril* + `கு/சு/டு/து/பு/று`)** words (`பசு`, `புது`, `அது`, `தெரு`, `கடு`, `கொடு`, `நடு`, `பொது`) are ***Mutriyalugaram*** (full `உ`)!
- **Failure Mode**: If `phonology.rs` treats every final `கு/சு/டு/து/பு/று` as *Kurriyalugaram*, `பசு + அழகு` or `புது + இடம்` will mis-classify as *Kurriyalugaram* (164) instead of *Mutriyalugaram* (primary *Udambadumei* `வ்`: `பசுவழகு`, while attested `164.3` `ஒரோவழி` elision applies only to specific *Mutriyalugaram* stems like `கதவு + அழகிது → கதவழகிது`, `அது + ஐ → அதை`). Conversely, failing to distinguish *Nedil-thodar* (`நாகு`) from *Vanthodar* (`பாட்டு`) breaks 183 doubling.

### b. Non-*Thanikkuril* Deletion Trap (Sūtras 210 & 229)
- **Rule**: After a **non-monosyllabic** (*kuril-anaiyā*) stem ending in `ண்/ன்` (210) or `ல்/ள்` (229), `த்`→`ற்/ட்` or `ந்`→`ன/ண` triggers **deletion** of the stem-final consonant.
- **Examples**: `வேல் + தீது → வேறீது` (single `ற`, NOT `*வேற்றீது`), `வாள் + தீது → வாடீது` (single `ட`, NOT `*வாட்டீது`), `தூண் + நன்று → தூணன்று` (single `ண`, NOT `*தூண்ணன்று`), `அரசன் + நல்லன் → அரசனல்லன்` (single `ன`, NOT `*அரசன்னல்லன்`).
- **Failure Mode**: Naive engines apply 209/227 assimilation without checking the *Thanikkuril* condition, producing doubled consonants (`*வேற்றீது`, `*தூண்ணன்று`).

### c. Sūtra 237 Ordering Trap (`த→ற/ட`, `ந→ன/ண`)
- **Rule**: Sūtra 237 mutates *Varumozhi*-initial `த்`→`ற்/ட்` and `ந்`→`ன/ண` **conditioned on the pre-mutation stem-final `ன்/ல்/ண்/ள்`**.
- **Failure Mode**: If Stage 3 executes 209/227/210/229 (mutating or deleting `ன்/ல்/ண்/ள்`) **before** 237 inspects the boundary, 237 loses its trigger! E.g., `வேல் + தீது`: 237 must convert `தீது → றீது` while `ல்` is still visible, and 229 deletes `ல்` to yield `வேறீது`.

### d. Sūtra 183 vs 164/165 Ordering Trap (*Kurriyalugaram* Doubling vs Elision)
- **Rule**: In *Vetrumai* (or compound *thogai*), *Nedil-thodar* and *Uyir-thodar* `டு/று` stems double `ட்/ற்` (183) **before** elision (164) or *Vallinam* doubling (165).
- **Examples**: `ஆடு + கால் → ஆட்டுக்கால்` (183 + 165), `ஆறு + நீர் → ஆற்றுநீர்` (183), `காடு + எருமை → காட்டு + எருமை → காட்டெருமை` (183 then 164), whereas *Alvazhi* `காடு + எங்கும் → காடெங்கும்` (164 only, no 183 doubling).
- **Failure Mode**: Running 164 before 183 on `காடு + எருமை` produces `*காடெருமை`; running 165 without 183 produces `*ஆடுக்கால்`.

### e. Sūtra 252 (`அத்தின் அகரம்`) vs 162 (*Udambadumei*) Trap
- **Rule**: After `ம்`-deletion (219: `மரம் → மர`), attaching `அத்து` *chariyai* + case suffix `ஐ` triggers **Sūtra 252** (`அத்தின் அகரம் அகரமுனை இல்லை`), which **elides the initial `அ` of `அத்து`** (`மர + அத்து + ஐ → மர + த்து + ஐ → மரத்தை`), followed by 164 (`மரத்த் + ஐ`) + 204 (`மரத்தை`).
- **Failure Mode**: If Stage 3 applies general *Udambadumei* (162) to `மர + அத்து`, it inserts `வ்`, yielding `*மரவத்தை`. Likewise, citing 164 for `மர + அத்து` is wrong—252 owns the `அ` elision of `அத்து`, while 164 owns the trailing `உ` elision of `த்து` before `ஐ`.

### f. Multi-Segment *Chariyai* + `உம்` Post-Positioning Trap (Sūtras 245–246)
- **Rule**: `எல்லாம்`, `எல்லாரும்`, `எல்லீரும்` strip their trailing `உம்` (or `ம்`), insert `அற்று`/`நம்`/`தம்`/`நும்`, attach the case suffix, and **re-attach `உம்` after the case suffix**.
- **Examples**: `எல்லாம் + ஐ → எல்லாவற்றையும்` (non-rational, 245), `எல்லாரும் + கு → எல்லார்தமக்கும்` / `எல்லாருக்கும்` (246).
- **Failure Mode**: Naive 2-part joiners treat `எல்லாம்` as a normal `ம்`-final noun (`*எல்லாத்தை`) or fail to reposition `உம்` after the case ending (`*எல்லாமுக்கு`).

### g. Compound Numerals Trap (Sūtras 188–199)
- **Rule**: Closed-class numeral compounding applies non-concatenative stem reductions and irregular assimilations:
  - `ஒன்பது + பத்து → தொண்ணூறு` (194)
  - `ஒன்பது + நூறு → தொள்ளாயிரம்` (194)
  - `பத்து + இரண்டு → பன்னிரண்டு` (198)
  - `இரண்டு + நூறு → இருநூறு` (188)
  - `மூன்று + ஆயிரம் → மூவாயிரம்` (188 + 162)
- **Failure Mode**: Treating numerals as regular *Kurriyalugaram* words produces `*ஒன்பதுபத்து`, `*பத்திரண்டு`, `*இரண்டுநூறு`.

### h. *Panpuppeyar* `-மை` Cascade Trap (Sūtra 136)
- **Rule**: `-மை` stems undergo ordered multi-step cascades in Stage 1:
  - `செம்மை + தாமரை → செம் + தாமரை → செந்தாமரை` (`ஈறு போதல்` + `முன்னின்ற மெய் திரிதல்` / nasal assimilation)
  - `பசுமை + தமிழ் → பசு + தமிழ் → பைந்தமிழ்` (`ஈறு போதல்` + `இடை உகரம் கெடல்` + `அடி அகரம் ஐ ஆதல்` + `இனம் மிகல்`)
  - `சிறுமை + ஊர் → சிறு + ஊர் → சிற்றூர்` (`ஈறு போதல்` + `தன் ஒற்று இரட்டல்` + 164/204)
  - `பெருமை + ஊர் → பெரு + ஊர் → பேரூர்` (`ஈறு போதல்` + `ஆதி நீடல்` + `இடை உகரம் கெடல்` + 204)
- **Failure Mode**: Applying only `-மை` deletion yields `*செம்மைதாமரை` or `*சிறுஊர்` (`*சிறுவூர்`).

### i. Reverse-Split Combinatorial Explosion & False Positives
- **The Trap**: Inverting lossy rules (e.g., `ற்` → `ல்`/`ன்`/`ற்`, `உ`-restoration, `ம்`-restoration, *chariyai* stripping) at every `Uyirmei` boundary in a long word can explode into dozens of impossible splits (e.g., splitting inside a root like `மண்டலம்` into `*மண் + டலம்`, or proposing word-initial `ற்`/`ண்`/`ள்` or word-final stops `க்/ச்/ட்/த்/ப்/ற்`).
- **Required Guard**: `split.rs` MUST apply **both**:
  1. ***Mozhi-muthal* / *Mozhi-eetru* phonotactic filtering (Nannūl 102–108)**: Reject any candidate where `first` violates word-final constraints or `second` violates word-initial constraints (e.g., no word-initial `ட்/ண்/ற்/ள்`, no word-final pure stops `க்/ச்/ட்/த்/ப்/ற்` in standard Tamil).
  2. **Forward-verification pruning**: Re-run the forward joiner on `(cand.first, cand.second)` and keep only candidates whose forward output matches `surface`!

### j. Unicode / NFC / ZWJ / ZWNJ / Ligature Traps
- **Decomposed Two-Part Vowel Signs**: `கொ` (`\u{0BC6}\u{0BBE}` vs `\u{0BCA}`), `கோ` (`\u{0BC7}\u{0BBE}` vs `\u{0BCB}`), `கௌ` (`\u{0BC6}\u{0BD7}` vs `\u{0BCC}`). Matching before NFC normalization misreads the trailing scalar as `ா` (`\u{0BBE}`) instead of `ஒ/ஓ/ஔ`.
- **Atomic Ligatures (`க்ஷ`, `ஸ்ரீ`)**: Splitting `க்ஷ` (`\u{0B95}\u{0BCD}\u{0BB7}`) or `ஸ்ரீ` (`\u{0BB8}\u{0BCD}\u{0BB0}\u{0BC0}` / `\u{0BB6}\u{0BCD}\u{0BB0}\u{0BC0}`) mid-unit corrupts `split_byte` / `split_unit` invariants.
- **Invisible Joiners (`ZWJ`/`ZWNJ`)**: Silently stripping `ZWJ`/`ZWNJ` violates Constitution Principle 2 and corrupts user-intended boundary barriers.

---

## 5. Actionable Engineering Recommendations for Phase R3 & Phase R4

### For Phase R3 (Precedence & Inverse Matrix)
- **Enforce explicit sub-stage ordering inside Stage 3**:
  1. Closed-class & *Kurriyalugaram* pre-elision doubling (**183** `டு/று` doubling in *Vetrumai*) **before** **164** (*Kurriyalugaram* elision) and **165** (*Vallinam* doubling).
  2. **237** (`த்`/`ந்` → `ற்/ட்`/`ன/ண`) **before** **209/210/227/229** (`ண்/ன்/ல்/ள்` mutation or deletion) so 237 sees the pre-mutation consonant.
  3. **252** (`அத்தின் அகரம்`) **before** **162** (*Udambadumei*) so `மர + அத்து` elides `அ` instead of inserting `வ்`.
  4. **228** (`ல்/ள் + த → ஃற/ஃட` in *Alvazhi*) and **227** (`ஏற்புழிக்கோடல்` before `த`) with explicit suppression of ungrammatical `*ல்த`/`*ள்த` outputs.
- **Model *Kurriyalugaram* vs *Mutriyalugaram* in `phonology.rs`** using `tamil_core::classify_quantity` + syllable count (`2-letter CVCu` → *Mutriyalugaram*; `2-letter CVVCu` / `3+ letter` / `Vanthodar` → *Kurriyalugaram* with all 6 subclasses).
- **Build `split.rs` with dual pruning**: *Mozhi-muthal*/*Mozhi-eetru* (102–108) phonotactic filter + forward-join verification, bounding output cleanly.

### For Phase R4 (Spec / Data-Model / Contract Updates)
- **`contracts/punarchi.md`**: Fix the `மரம் + ஐ → மரத்தை` example trace (currently lines 45–60): insert Sūtra **252** (`nannool_252_attin_akaram`, `மர + அத்து + ஐ → மர + த்து + ஐ`) before Sūtra **164** (`மரத்து + ஐ → மரத்த் + ஐ`), or document `மர + அத்து → மரத்து` (252) followed by `மரத்து + ஐ → மரத்த் + ஐ` (164) → `மரத்தை` (204).
- **`spec.md` & `research.md`**:
  - Explicitly document all **10 prerequisite sūtras** (*Eḻuttiyal* `93–94`, `102–108` and *Padaviyal* `136`) as in-scope alongside Puṇariyal `151–257` (117 sūtras total).
  - Clarify **Sūtra 201** (`ஏ`/`ஓ` particle as `first` before *Vallinam* `second`), **Sūtra 206** (optional `இ` before `ய`, `optional: true`), **Sūtra 244** (`ன` vs `ன்` witness note), and **Sūtra 247** (`நான் → என்` as extended/usage mapping alongside root `யான் → என்`).
  - Explicitly note that **Phase 16** owns sentence-level *Valimigum*/*Valimigaa* syntactic linting, while **Phase 10 `nannool-v1`** owns single-boundary morphophonemics and closed-class triggers.
- **`data-model.md`**: Add a note under `[[rule]]` that `priority` + `stage` must encode intra-stage sub-ordering (e.g., `237` before `210`/`229`; `183` before `164`; `252` before `162`), and add `edition_note` coverage for `pmuni0147` raw numbering around 241.
