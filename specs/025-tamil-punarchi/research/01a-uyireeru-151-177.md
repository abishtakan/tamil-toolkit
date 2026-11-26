# Nannūl Uyirīṟṟup Puṇariyal — Part A (Sutras 151–177) Research Specification

- **Source Bundle**: `bundle_01a_uyireeru_151_177.md` (27 sutras: `151..=177`)
- **Primary Text**: TVA 1999 Critical Edition (Thamodaran / Viruttiyurai, `pno=218..244`)
- **Cross-Witnesses**: Project Madurai `pmuni0147` (1926 Vavilla), TVA Arumuka Navalar Kandigaiyurai (`sutra=151..177`)
- **Scope**: Foundational Puṇarcci definitions & taxonomy (151–157), General Puṇarcci across all 24 finals (158–161), and Vowel-final Special Puṇarcci: *Udambadumei*, Demonstrative/Interrogative overrides, *Kuṟṟiyalugaram*/*Muṟṟiyalugaram*, general *Valimigal*, tree names, *Agara*, *Āgāra*, *Igara*, *Igara/Aikāra*, and *Īgāra* special rules (162–177).

---

## Sutra 151

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Foundational / Definitional | **Executable:** Metadata / Framework | **Viruttiyurai pno:** 218, 219 | **Kandigai:** 151 | **Poetic:** No

### Root Text (TVA 1999)
> மெய்யுயிர் முதலீ றாமிரு பதங்களுந்  
> தன்னொடும் பிறிதொடு மல்வழி வேற்றுமைப்  
> பொருளிற் பொருந்துழி நிலைவரு மொழிகள்  
> இயல்பொடு விகாரத் தியைவது புணர்ப்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`மெய் உயிர் முதல் ஈறு ஆம் இரு பதங்கள் உம் / தன் ஒடு உம் பிறிது ஒடு உம் அல்வழி வேற்றுமை / பொருளின் பொருந்துழி நிலை வரு மொழிகள் / இயல்பு ஒடு விகாரத்து இயைவது புணர்ப்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R151.1 (Domain of Puṇarcci)**: `IF` two words (`நிலைமொழி` standing word + `வருமொழி` coming word) belong to either `பகாப்பதம்` (simple/unanalysable word) or `பகுபதம்` (analysable/inflected word) — including loan/regional words (`திசைச்சொல்`, `வடசொல்`) subsumed under `பெயர், வினை, இடை, உரி` — and have one of the 4 onset/coda combinations (`மெய் முதல் மெய்யீறு`, `உயிர் முதல் உயிரீறு`, `மெய் முதல் உயிரீறு`, `உயிர் முதல் மெய்யீறு`) `THEN` they are eligible inputs to Puṇarcci.
2. **R151.2 (Self vs Other Pairing)**: `IF` `நிலைமொழி` combines with an identical word (`தன்னொடும்`, e.g., reduplication `அடுக்கு` or `பல+பல`) OR a different word (`பிறிதொடும்`) `THEN` Puṇarcci applies.
3. **R151.3 (Semantic Context Dichotomy)**: `IF` two words combine `THEN` the syntactic/semantic relation is partitioned into `அல்வழி` (non-case relation) or `வேற்றுமை` (case relation).
4. **R151.4 (Output Mode)**: `IF` Puṇarcci applies `THEN` the surface join is realized via either `இயல்பு` (natural/unmodified concatenation, defined in 153) or `விகாரம்` (phonological/morphological modification, defined in 154).

### Interactions & Precedence
- Entry point of the entire Puṇarcci engine (links to Sutra 57 `பதம்`).
- Establishes the core signature: `join(first: Word, second: Word, context: Alvazhi | Vetrumai) -> Natural | Modified`.
- `அல்வழி` precedes `வேற்றுமை` in wording so `அல்வழி` is not misread as modifying `வேற்றுமை`.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| *(Framework rule; no standalone lexical examples in 151)* | — | — | — | — | `viruttiyurai_pno=218..219`, `kandigai=151` |

### Surface Signature & Reversibility
- **Signature**: Architectural axiom; no direct surface mutation.
- **Reversibility**: Defines forward join and inverse split over `(நிலைமொழி, வருமொழி, புணர்ச்சி_வழி)`.

---

## Sutra 152

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Foundational / Taxonomy | **Executable:** Metadata / Context Enum | **Viruttiyurai pno:** 219, 220, 221 | **Kandigai:** 152 | **Poetic:** No

### Root Text (TVA 1999)
> வேற்றுமை யைம்முத லாறா மல்வழி  
> தொழில்பண் புவமை யும்மை யன்மொழி  
> எழுவாய் விளியீ ரெச்சமுற் றிடையுரி  
> தழுவு தொடரடுக் கெனவீ ரேழே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`வேற்றுமை ஐ முதல் ஆறு ஆம் அல்வழி / தொழில் பண்பு உவமை உம்மை அன்மொழி / எழுவாய் விளி ஈர் எச்சம் முற்று இடை உரி / தழுவுதொடர் அடுக்கு என ஈர் ஏழ் ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R152.1 (6 *Vēṟṟumai* Case Subtypes — தொகை & விரி)**: `IF` `context == Vetrumai` `THEN` it is one of the 6 case relations with overt (`விரி`) or elided (`தொகை`) case markers (`உருபு`), excluding nominative (`எழுவாய்`) and vocative (`விளி`) which lack separate case suffixes:
   1. `இரண்டாம் வேற்றுமை` (`ஐ`) — Accusative (`தொகை` / `விரி`)
   2. `மூன்றாம் வேற்றுமை` (`ஆல்` / `ஆன்` / `ஒடு` / `ஓடு`) — Instrumental/Sociative (`தொகை` / `விரி`)
   3. `நான்காம் வேற்றுமை` (`கு`) — Dative (`தொகை` / `விரி`)
   4. `ஐந்தாம் வேற்றுமை` (`இன்` / `இல்`) — Ablative/Comparative (`தொகை` / `விரி`)
   5. `ஆறாம் வேற்றுமை` (`அது` / `ஆது` / `அ`) — Genitive (`தொகை` / `விரி`)
   6. `ஏழாம் வேற்றுமை` (`கண்` etc.) — Locative (`தொகை` / `விரி`)
   - *Note*: `உருபும் பயனும் உடன் தொக்க தொகை` (e.g., `பொற்குடம்`, `கைக்களிறு`, `ஆடகப்பூண்`) is a `தழாத்தொடர்` (non-adjacent semantic head) subtype of `வேற்றுமை`.
2. **R152.2 (14 *Alvaḻi* Non-Case Subtypes — 5 *Thogainilai* + 9 *Thogaanilai*)**: `IF` `context == Alvazhi` `THEN` it is one of `ஈரேழ்` (14) subtypes:
   - **5 *Thogainilai* (தொகைநிலைத்தொடர் — Compounds)**:
     1. `வினைத்தொகை` (`தொழில்`) — Verbal compound
     2. `பண்புத்தொகை` (`பண்பு`, including `இருபெயரொட்டுப் பண்புத்தொகை`) — Adjectival/appositional compound
     3. `உவமைத்தொகை` (`உவமை`) — Simile/metaphor compound
     4. `உம்மைத்தொகை` (`உம்மை`) — Copulative/dvandva compound
     5. `அன்மொழித்தொகை` (`அன்மொழி`) — Exocentric/bahuvrihi compound
   - **9 *Thogaanilai* (தொகாநிலைத்தொடர் — Phrases)**:
     6. `எழுவாய்த்தொடர்` (`எழுவாய்`) — Subject + predicate
     7. `விளித்தொடர்` (`விளி`) — Vocative + verb/noun
     8. `பெயரெச்சத்தொடர்` (first of `ஈரெச்சம்`) — Adjectival participle + noun
     9. `வினையெச்சத்தொடர்` (second of `ஈரெச்சம்`) — Adverbial participle + verb
     10. `தெரிநிலை வினைமுற்றுத்தொடர்` (first of `ஈர் முற்று`) — Finite indicative verb + subject
     11. `குறிப்பு வினைமுற்றுத்தொடர்` (second of `ஈர் முற்று`) — Finite appellative verb + subject
     12. `இடைச்சொற்றொடர்` (`இடை`) — Particle + word
     13. `உரிச்சொற்றொடர்` (`உரி`) — Poetic/lexical intensifier + word
     14. `அடுக்குத்தொடர்` (`அடுக்கு`) — Iterative/reduplicated word (syntactically non-modifying `தழாத்தொடர்`-like repetition, hence listed last).
3. **R152.3 (*Taḻuvu-toṭar* vs *Taḻā-toṭar*)**: `IF` `நிலைமொழி` semantically modifies `வருமொழி` directly `THEN` it is `தழுவுதொடர்`; `IF` `நிலைமொழி` linearly precedes `வருமொழி` without direct semantic modification (e.g., poetic word-order transposition `மொழிமாற்று` or `உருபும் பயனும் உடன் தொக்க தொகை` where an intermediate word is elided) `THEN` it is `தழாத்தொடர்`, which still undergoes Puṇarcci (`சுரையாழ`, `மருப்பிற் பரல்`).

### Interactions & Precedence
- Defines the complete `Context` enum required by all downstream Puṇarcci rules (e.g., `159`, `166`, `167`, `171`, `176`, `177`).
- When a rule does not specify `அல்வழி` or `வேற்றுமை`, it applies to **both** (stated explicitly in Sutra 158 commentary).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| பொன் | உடையான் | பொன்னுடையான் | `வேற்றுமை.இரண்டாம்.தொகை` | `ன்` doubling + vowel attach | `viruttiyurai_pno=220` |
| பொன்னை | உடையான் | பொன்னை உடையான் | `வேற்றுமை.இரண்டாம்.விரி` | natural | `viruttiyurai_pno=220` |
| நிலம் | கடந்தான் | நிலங்கடந்தான் | `வேற்றுமை.இரண்டாம்.தொகை` | `ம் -> ங்` | `kandigai=152` |
| நிலத்தை | கடந்தான் | நிலத்தைக் கடந்தான் | `வேற்றுமை.இரண்டாம்.விரி` | `க்` insertion | `kandigai=152` |
| கல் | எறிந்தான் | கல் எறிந்தான் / கல்லாலெறிந்தான் | `வேற்றுமை.மூன்றாம்` (தொகை / விரி) | natural / `ல்` doubling | `viruttiyurai_pno=220`, `kandigai=152` |
| கொற்றன் | மகன் | கொற்றன்மகன் | `வேற்றுமை.நான்காம்.தொகை` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| கொற்றனுக்கு | மகன் | கொற்றனுக்கு மகன் | `வேற்றுமை.நான்காம்.விரி` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| மலை | வீழருவி | மலைவீழருவி | `வேற்றுமை.ஐந்தாம்.தொகை` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| மலையின் | வீழருவி | மலையின் வீழருவி | `வேற்றுமை.ஐந்தாம்.விரி` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| மலை | உச்சி | மலையுச்சி | `வேற்றுமை.ஆறாம்.தொகை` | `ய்` udambadumei | `viruttiyurai_pno=220` |
| மலையினது | உச்சி | மலையினது உச்சி | `வேற்றுமை.ஆறாம்.விரி` | natural | `viruttiyurai_pno=220` |
| சாத்தன் | கை | சாத்தன் கை / சாத்தனது கை | `வேற்றுமை.ஆறாம்` (தொகை / விரி) | natural | `kandigai=152` |
| மலை | முழை | மலைமுழை | `வேற்றுமை.ஏழாம்.தொகை` | natural | `viruttiyurai_pno=220` |
| மலைக்கண் | முழை | மலைக்கண் முழை | `வேற்றுமை.ஏழாம்.விரி` | natural | `viruttiyurai_pno=220` |
| குன்றம் | கூகை | குன்றக் கூகை | `வேற்றுமை.ஏழாம்.தொகை` | `ம்` elision + `க்` insertion | `kandigai=152` |
| குன்றத்தின்கண் | கூகை | குன்றத்தின்கட் கூகை | `வேற்றுமை.ஏழாம்.விரி` | `ண் -> ட்` | `kandigai=152` |
| கொல் | யானை | கொல்யானை | `அல்வழி.வினைத்தொகை` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| கருமை | குதிரை | கருங்குதிரை | `அல்வழி.பண்புத்தொகை` | `மை` elision + `ங்` insertion | `viruttiyurai_pno=220`, `kandigai=152` |
| சாரை | பாம்பு | சாரைப்பாம்பு | `அல்வழி.இருபெயரொட்டுப் பண்புத்தொகை` | `ப்` insertion | `kandigai=152` |
| ஆயன் | சாத்தன் | ஆயன்சாத்தன் | `அல்வழி.இருபெயரொட்டுப் பண்புத்தொகை` | natural | `viruttiyurai_pno=220` |
| பொன் | சுணங்கு | பொற்சுணங்கு | `அல்வழி.உவமைத்தொகை` | `ன் -> ற்` | `viruttiyurai_pno=220` |
| மதி | முகம் | மதிமுகம் | `அல்வழி.உவமைத்தொகை` | natural | `kandigai=152` |
| இரா | பகல் | இராப்பகல் | `அல்வழி.உம்மைத்தொகை` | `ப்` insertion | `viruttiyurai_pno=220`, `kandigai=152` |
| பொன் | தொடி | பொற்றொடி | `அல்வழி.அன்மொழித்தொகை` | `ன் -> ற்` | `viruttiyurai_pno=220`, `kandigai=152` |
| கொற்றன் | கொடுத்தான் | கொற்றன் கொடுத்தான் | `அல்வழி.எழுவாய்த்தொடர்` | natural | `viruttiyurai_pno=220` |
| சாத்தன் | வந்தான் | சாத்தன் வந்தான் | `அல்வழி.எழுவாய்த்தொடர்` | natural | `kandigai=152` |
| கொற்றா | கொள் | கொற்றா கொள் | `அல்வழி.விளித்தொடர்` | natural | `viruttiyurai_pno=220` |
| சாத்தா | வா | சாத்தா வா | `அல்வழி.விளித்தொடர்` | natural | `kandigai=152` |
| உண்ட | சாத்தன் | உண்ட சாத்தன் | `அல்வழி.பெயரெச்சத்தொடர்` | natural | `viruttiyurai_pno=220` |
| உண்டு | வந்தான் | உண்டு வந்தான் | `அல்வழி.வினையெச்சத்தொடர்` | natural | `viruttiyurai_pno=220` |
| உண்டான் | சாத்தன் | உண்டான் சாத்தன் | `அல்வழி.தெரிநிலை_வினைமுற்றுத்தொடர்` | natural | `viruttiyurai_pno=220` |
| குண்டுகட்டு | எருமை | குண்டுகட்டெருமை | `அல்வழி.குறிப்பு_வினைமுற்றுத்தொடர்` | `உ` elision + `ட்` vowel attach | `viruttiyurai_pno=220` |
| பெரியன் | சாத்தன் | பெரியன் சாத்தன் | `அல்வழி.குறிப்பு_வினைமுற்றுத்தொடர்` | natural | `kandigai=152` |
| மற்று | ஒன்று | மற்றொன்று | `அல்வழி.இடைச்சொற்றொடர்` | `உ` elision | `kandigai=152` |
| நனி | பேதை | நனிபேதை | `அல்வழி.உரிச்சொற்றொடர்` | natural | `viruttiyurai_pno=220`, `kandigai=152` |
| படை | படை | படைபடை | `அல்வழி.அடுக்குத்தொடர்` | natural | `viruttiyurai_pno=220` |
| பாம்பு | பாம்பு | பாம்புபாம்பு | `அல்வழி.அடுக்குத்தொடர்` | natural | `kandigai=152` |
| சுரை | ஆழ | சுரையாழ | `அல்வழி.தழாத்தொடர்` | `ய்` udambadumei | `viruttiyurai_pno=221`, `kandigai=152` |
| மருப்பு | பரல் | மருப்பிற் பரல் | `வேற்றுமை.தழாத்தொடர்` | `இன்` cāriyai + `ன் -> ற்` | `viruttiyurai_pno=220` |

### Surface Signature & Reversibility
- **Signature**: Context classification taxonomy; governs disambiguation when identical words yield different surfaces under `வேற்றுமை` vs `அல்வழி`.
- **Reversibility**: Context enum is a required input/output tag in disambiguated morphological analysis.

---

## Sutra 153

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Foundational / Definitional | **Executable:** Rule (Default / Fallback) | **Viruttiyurai pno:** 221, 222 | **Kandigai:** 153 | **Poetic:** No

### Root Text (TVA 1999)
> விகார மனைத்து மேவல தியல்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`விகாரம் அனைத்து உம் மேவலது இயல்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R153.1 (Natural Join Definition)**: `IF` no modification rule (`தோன்றல்`, `திரிதல்`, `கெடுதல்`) applies to `(first, second, context)` `THEN` the join is `இயல்பு` (direct concatenation without phonological alteration).

### Interactions & Precedence
- Lowest-precedence default when no `விகாரம்` rule fires, and explicit target of all `இயல்பு` / `மிகா` rules (`158`, `159`, `160`, `161`, `167`, `168`, `171`, `173`, `176`, `177`).
- Note semantic contrast in Viruttiyurai pno=222: `மலர்க்கணை` (modification -> `பண்புத்தொகை` / metaphor) vs `மலர்கணை` (natural -> `உம்மைத்தொகை` "flowers and arrows").

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| பொன் | மலை | பொன்மலை | general | natural | `viruttiyurai_pno=222`, `kandigai=153` *(Kandigai has typo `பொன்யலை`)* |
| புகழ் | அழகிது | புகழழகிது | general | `ழ்` + `அ` -> `ழ` (syllabic join, no consonant/vowel mutation) | `viruttiyurai_pno=222`, `kandigai=153` |
| ஒளி | மணி | ஒளிமணி | general | natural | `viruttiyurai_pno=222`, `kandigai=153` |
| மலர் | கணை | மலர்கணை | `உம்மைத்தொகை` (contrastive) | natural (vs `மலர்க்கணை`) | `viruttiyurai_pno=222` |

### Surface Signature & Reversibility
- **Signature**: `first + second` (with `உடன்மேல் உயிர்` syllabic ligature if `first` ends in consonant and `second` starts with vowel, per Sutra 204).
- **Reversibility**: Trivial boundary split at `len(first)`.

---

## Sutra 154

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Foundational / Definitional | **Executable:** Metadata / Transform Enum | **Viruttiyurai pno:** 222, 223 | **Kandigai:** 154 | **Poetic:** No

### Root Text (TVA 1999)
> தோன்ற றிரிதல் கெடுதல் விகாரம்  
> மூன்று மொழிமூ விடத்து மாகும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`தோன்றல் திரிதல் கெடுதல் விகாரம் / மூன்று உம் மொழி மூ இடத்து உம் ஆகும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R154.1 (Three Mutation Operations)**: `IF` Puṇarcci is `விகாரம்` `THEN` each atomic edit is one of:
   - `தோன்றல்` (Insertion/Augmentation of consonant, vowel, CV, or `சாரியை`)
   - `திரிதல்` (Substitution/Alternation)
   - `கெடுதல்` (Deletion/Elision)
2. **R154.2 (Three Positions + Inter-Word)**: `IF` any of the 3 mutations occurs `THEN` it may target `முதல்` (initial of `வருமொழி` or `நிலைமொழி`), `இடை` (medial), or `கடை` (final of `நிலைமொழி`), OR span the inter-word boundary (`இருமொழியையும் சார்ந்து`, e.g., `உடம்படுமெய்`, `அம்முச்சாரியை`).

### Interactions & Precedence
- Defines the `TransformOp` primitive set (`Insert`, `Replace`, `Delete`) used by all Puṇarcci rules and by Sutra 157 (multi-operation chains).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| பூ | கொடி | பூக்கொடி | general | `தோன்றல்`: `க்` at `வருமொழி முதல்` | `viruttiyurai_pno=222` |
| பூ | கொடி | பூங்கொடி | general | `தோன்றல்`: `ங்` at `வருமொழி முதல்` | `viruttiyurai_pno=222`, `kandigai=154` |
| பல் | தலை | பஃறலை | general | `திரிதல்`: `ல் -> ஃ` (final) & `த் -> ற்` (initial) | `viruttiyurai_pno=222`, `kandigai=154` |
| நிலம் | வலயம் | நிலவலயம் | general | `கெடுதல்`: `ம்` at `நிலைமொழி ஈறு` | `viruttiyurai_pno=222`, `kandigai=154` |
| ஆறு | பத்து | அறுபது | numeral | `திரிதல்` (`ஆ -> அ` initial) + `கெடுதல்` (`த்` medial) | `viruttiyurai_pno=222`, `kandigai=154` |
| பல | பொருள் | பல்பொருள் | `அல்வழி` | `கெடுதல்`: `அ` at `நிலைமொழி ஈறு` | `viruttiyurai_pno=222`, `kandigai=154` |
| நாழி | உரி | நாடுரி | measure | `கெடுதல்` (`ழி`) + `தோன்றல்` (`ட்`) | `viruttiyurai_pno=222`, `kandigai=154` |
| தமிழ் | பிள்ளை | தமிழப்பிள்ளை / தமிழ்ப்பிள்ளை | general | `தோன்றல்`: `அ` / `ப்` cāriyai | `viruttiyurai_pno=222`, `kandigai=154` |
| பனை | காய் | பனங்காய் | tree | `கெடுதல்` (`ஐ`) + `தோன்றல்` (`அம்` cāriyai, `ம் -> ங்`) | `viruttiyurai_pno=222`, `kandigai=154` |
| ஆ | அழகிது | ஆவழகிது | vowel+vowel | `தோன்றல்`: `வ்` inter-word (`உடம்படுமெய்`) | `viruttiyurai_pno=222` |
| உரி | நெய் | உரியநெய் | measure | `தோன்றல்`: `ய` CV inter-word | `viruttiyurai_pno=222` |
| புளி | காய் | புளியங்காய் | tree | `தோன்றல்`: `அம்` cāriyai inter-word | `viruttiyurai_pno=222` |

### Surface Signature & Reversibility
- **Signature**: Structural classification of edit operations.
- **Reversibility**: Each transform must record `(op_kind, locus, before, after)` for inverse parsing.

---

## Sutra 155

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Poetic (`செய்யுள் விகாரம்`) | **Executable:** Poetic-only (6 poetic licenses) | **Viruttiyurai pno:** 223, 224 | **Kandigai:** 155 | **Poetic:** Yes

### Root Text (TVA 1999)
> வலித்தன் மெலித்த னீட்டல் குறுக்கல்  
> விரித்த றொகுத்தலும் வருஞ்செய்யுள் வேண்டுழி.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`வலித்தல் மெலித்தல் நீட்டல் குறுக்கல் / விரித்தல் தொகுத்தல் உம் வரும் செய்யுள் வேண்டுழி`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R155.1 (Poetic License Gate)**: `IF` `poetic == true` AND prosodic meter/ornamentation (`அடி, தொடை`) requires it `THEN` any of the 6 poetic mutations may apply:
   - `வலித்தல்`: Soft nasal consonant (`மெல்லொற்று`) -> hard stop (`வல்லொற்று`)
   - `மெலித்தல்`: Hard stop (`வல்லொற்று`) -> soft nasal (`மெல்லொற்று`)
   - `நீட்டல்`: Short vowel (`குறில்`) -> long vowel (`நெடில்`)
   - `குறுக்கல்`: Long vowel (`நெடில்`) -> short vowel (`குறில்`)
   - `விரித்தல்`: Insertion of an otherwise absent consonant/vowel (`இல்லாத எழுத்தை வருவித்தல்`)
   - `தொகுத்தல்`: Deletion of an existing consonant/vowel (`உள்ள எழுத்தை நீக்கல்`)

### Interactions & Precedence
- Strictly gated behind `poetic == true` (`செய்யுள் வேண்டுழி`). Must NEVER fire in default prose Puṇarcci.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| குறுந்தாள் | *(poetic)* | குறுத்தாள் | `poetic` (`வலித்தல்`) | `ந் -> த்` | `viruttiyurai_pno=223`, `kandigai=155` |
| தட்டை | *(poetic)* | தண்டை | `poetic` (`மெலித்தல்`) | `ட் -> ண்` | `viruttiyurai_pno=223`, `kandigai=155` |
| பொத்தறார் | *(poetic)* | போத்தறார் | `poetic` (`நீட்டல்`) | `ஒ -> ஓ` | `viruttiyurai_pno=223`, `kandigai=155` |
| தீயேன் | *(poetic)* | தியேன் | `poetic` (`குறுக்கல்`) | `ஈ -> இ` | `viruttiyurai_pno=223`, `kandigai=155` |
| விளையுமே | *(poetic)* | விளையும்மே | `poetic` (`விரித்தல்`) | `ம்` gemination | `viruttiyurai_pno=224`, `kandigai=155` |
| சிறிய | இலை | சிறியிலை | `poetic` (`தொகுத்தல்`) | `வ்`/`அ` elision (`சிறியவிலை -> சிறியிலை`) | `viruttiyurai_pno=224`, `kandigai=155` |
| தொட்டது | *(poetic)* | தொட்டு | `poetic` (`தொகுத்தல்`) | `அது` -> `உ` reduction | `viruttiyurai_pno=224` |
| கற்றது | *(poetic)* | கற்று | `poetic` (`தொகுத்தல்`) | `அது` -> `உ` reduction | `viruttiyurai_pno=224` |

### Surface Signature & Reversibility
- **Signature**: Non-deterministic metrical transforms (`poetic == true`).
- **Reversibility**: Requires poetic-mode relaxation during inverse lookup.

---

## Sutra 156

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Poetic (`செய்யுள் விகாரம்`) | **Executable:** Poetic-only (3 positional truncations) | **Viruttiyurai pno:** 224 | **Kandigai:** 156 | **Poetic:** Yes

### Root Text (TVA 1999)
> ஒருமொழி மூவழிக் குறைதலு மனைத்தே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`ஒரு மொழி மூ வழி குறைதல் உம் அனைத்து ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R156.1 (Poetic Word-Clipping)**: `IF` `poetic == true` AND meter/prosody requires it `THEN` a single word may be clipped at one of 3 positions (`செய்யுள் மரூஉ`):
   - `முதற்கூறை` (Initial clipping, e.g., `தாமரை -> மரை`)
   - `இடைக்குறை` (Medial clipping, e.g., `ஓந்தி -> ஓதி`)
   - `கடைக்குறை` (Final clipping, e.g., `நீலம் -> நீல்`)

### Interactions & Precedence
- Completes the 9 poetic `விகாரம்` types (6 in Sutra 155 + 3 in Sutra 156) alongside the 3 general `விகாரம்` types (Sutra 154).
- Strictly gated behind `poetic == true`.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| தாமரை | *(poetic)* | மரை | `poetic` (`முதற்குறை`) | drop `தா` | `viruttiyurai_pno=224`, `kandigai=156` |
| ஓந்தி | *(poetic)* | ஓதி | `poetic` (`இடைக்குறை`) | drop `ந்` | `viruttiyurai_pno=224`, `kandigai=156` |
| நீலம் | *(poetic)* | நீல் | `poetic` (`கடைக்குறை`) | drop `அம்` | `viruttiyurai_pno=224`, `kandigai=156` |

### Surface Signature & Reversibility
- **Signature**: Clipped stem forms in verse (`மரையிதழ்`, `வேதின வெரிநின் ஓதி`, `நீலுண் துகிலிகை`).
- **Reversibility**: Requires poetic lexicon/alias mapping (`மரை <-> தாமரை`, `ஓதி <-> ஓந்தி`, `நீல் <-> நீலம்`).

---

## Sutra 157

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Foundational / Composition | **Executable:** Metadata / Pipeline | **Viruttiyurai pno:** 225 | **Kandigai:** 157 | **Poetic:** No

### Root Text (TVA 1999)
> ஒருபுணர்க் கிரண்டு மூன்று முறப்பெறும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`ஒரு புணர் கு இரண்டு மூன்று உம் உற பெறும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R157.1 (Multi-Mutation Allowance)**: `IF` a single Puṇarcci join undergoes `விகாரம்` `THEN` 1, 2, or 3 distinct `விகாரம்` operations (`தோன்றல்`, `திரிதல்`, `கெடுதல்`) may co-occur in the same join.

### Interactions & Precedence
- Authorizes multi-step rule pipelines in the Puṇarcci engine (e.g., elision + cāriyai insertion + consonant assimilation).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| யானை | கோடு | யானைக்கோடு | general (1 mutation) | `தோன்றல்` (`க்`) | `viruttiyurai_pno=225`, `kandigai=157` |
| நிலம் | பனை | நிலப்பனை | general (2 mutations) | `கெடுதல்` (`ம்`) + `தோன்றல்` (`ப்`) | `viruttiyurai_pno=225`, `kandigai=157` |
| பனை | காய் | பனங்காய் | general (3 mutations) | `கெடுதல்` (`ஐ`) + `தோன்றல்` (`அம்`) + `திரிதல்` (`ம் -> ங்`) | `viruttiyurai_pno=225`, `kandigai=157` |

### Surface Signature & Reversibility
- **Signature**: Multi-op transform trace (`len(ops) in 1..=3`).
- **Reversibility**: Inverse pipeline must unwind up to 3 sequential edits.

---

## Sutra 158

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** General (`பொதுப் புணர்ச்சி`) | **Executable:** Rule (Deterministic + Optional) | **Viruttiyurai pno:** 225, 226 | **Kandigai:** 158 | **Poetic:** No

### Root Text (TVA 1999)
> எண்மூ வெழுத்தீற் றெவ்வகை மொழிக்கும்  
> முன்வரு ஞநமய வக்க ளியல்புங்  
> குறில்வழி யத்தனி யைந்நொது முன்மெலி  
> மிகலுமாம் ணளனல வழிநத் திரியும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`எண் மூ எழுத்து ஈற்று எ வகை மொழி கு உம் / முன் வரும் ஞ ந ம ய வக்கள் இயல்பு உம் / குறில் வழி ய தனி ஐ நொ து முன் மெலி / மிகல் உம் ஆம் ண ள ன ல வழி ந திரியும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R158.1 (Default Nasal & Approximant Naturalness across all 24 Finals)**: `IF` `first` ends in any of the 24 Puṇarcci-eligible finals (12 vowels or 11 consonants `ஞ்,ண்,ந்,ம்,ன்,ய்,ர்,ல்,வ்,ழ்,ள்` or `குற்றியலுகரம்` — excluding `எ` interrogative particle overridden in Sutra 163) AND `second` begins with `ஞ, ந, ம, ய, வ` `THEN` in both `அல்வழி` and `வேற்றுமை`, `second`'s initial consonant remains **natural** (`இயல்பு`). *(Note: `first`'s own final may still undergo its coda-specific rule, e.g., `வேல் + ஞான்றது -> வேன்ஞான்றது`, `மரம் + ஞான்றது -> மரஞான்றது`.)*
2. **R158.2 (Nasal Doubling after `குறில்+ய்`, Monosyllabic `ஐ`, `நொ`, `து`)**: `IF` `first` is:
   - `(a)` short vowel + `ய்` (`குறில் வழி ய்`, e.g., `மெய்`), OR
   - `(b)` monosyllabic word ending in `ஐ` (`தனி ஐ` — vowel or CV, e.g., `கை`, `ஐ`), OR
   - `(c)` `நொ` or `து` (imperative/monosyllable)
   AND `second` begins with `ஞ, ந, ம` (`மெல்லினம்` onset)
   `THEN` the initial nasal (`ஞ், ந், ம்`) **doubles** (`மிகும்`) in both `அல்வழி` and `வேற்றுமை` (for `நொ`/`து`, `அல்வழி` as verbs).
3. **R158.3 (Approximant `ய, வ` Doubling after `நொ, து` via `எச்சவும்மை`)**: `IF` `first` is `நொ` or `து` AND `second` begins with `ய` or `வ` (`இடையினம்`) `THEN` `ய்` or `வ்` also **doubles** (`நொய்யவனா`, `நொவ்வளவா`, `துய்யவனா`, `துவ்வளவா`) in `அல்வழி` (otherwise hiatus/break `விட்டிசை` would occur). *(Does NOT apply to `குறில் வழி ய்` or `தனி ஐ`.)*
4. **R158.4 (`ந` Mutation after `ண, ள, ன, ல`)**: `IF` `first` ends in `ண், ள், ன், ல்` AND `second` begins with `ந` `THEN` `ந` does NOT remain natural; it **mutates** (`திரியும்`) per later consonant-final rules (`னல முன் றனவும்` etc., Sutra 208/227/237).

### Interactions & Precedence
- **Overridden by Sutra 163**: `எ` interrogative clitic (`எ + ஞாலம் -> எஞ்ஞாலம்`) overrides R158.1.
- **Linked to Sutra 165**: For `நொ, து`, Sutra 165 adds `க,ச,த,ப` doubling (`நொக்கொற்றா`, `துக்கொற்றா`), so `நொ, து` double all 3 consonant classes (`வல்லினம்`, `மெல்லினம்`, `இடையினம்`).
- **Linked to Sutra 207–208, 227, 237**: `ண, ள, ன, ல` + `ந` mutation details deferred to `மெய்யீற்றுப் புணரியல்`.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| விள | ஞான்றது / ஞாற்சி | விள ஞான்றது / விள ஞாற்சி | `அல்வழி` / `வேற்றுமை` | natural | `viruttiyurai_pno=225`, `kandigai=158` |
| விள | நீண்டது / நீட்சி | விள நீண்டது / விள நீட்சி | `அல்வழி` / `வேற்றுமை` | natural | `viruttiyurai_pno=225`, `kandigai=158` |
| விள | மாண்டது / மாட்சி | விள மாண்டது / விள மாட்சி | `அல்வழி` / `வேற்றுமை` | natural | `viruttiyurai_pno=225`, `kandigai=158` |
| விள | யாது / யாப்பு | விள யாது / விள யாப்பு | `அல்வழி` / `வேற்றுமை` | natural | `viruttiyurai_pno=225`, `kandigai=158` |
| விள | வலிது / வன்மை | விள வலிது / விள வன்மை | `அல்வழி` / `வேற்றுமை` | natural | `viruttiyurai_pno=225`, `kandigai=158` |
| உரிஞ் | ஞான்றது | உரிஞுஞான்றது | `அல்வழி` | `உ` insertion on `உரிஞ்`; `ஞ` natural | `kandigai=158` |
| பொருந் | ஞான்றது | பொருஞுஞான்றது | `அல்வழி` | `உ` insertion + assimilation; `ஞ` natural | `kandigai=158` |
| வேல் | ஞான்றது | வேன்ஞான்றது | `அல்வழி` | `ல் -> ன்`; `ஞ` natural | `kandigai=158` |
| வாள் | ஞான்றது | வாண்ஞான்றது | `அல்வழி` | `ள் -> ண்`; `ஞ` natural | `kandigai=158` |
| மரம் | ஞான்றது | மரஞான்றது | `அல்வழி` | `ம்` elision; `ஞ` natural | `kandigai=158` |
| மெய் | ஞான்றது / ஞாற்சி | மெய்ஞ்ஞான்றது / மெய்ஞ்ஞாற்சி | `அல்வழி` / `வேற்றுமை` (`குறில்+ய்`) | `ஞ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| மெய் | நீண்டது / நீட்சி | மெய்ந்நீண்டது / மெய்ந்நீட்சி | `அல்வழி` / `வேற்றுமை` (`குறில்+ய்`) | `ந்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| மெய் | மாண்டது / மாட்சி | மெய்ம்மாண்டது / மெய்ம்மாட்சி | `அல்வழி` / `வேற்றுமை` (`குறில்+ய்`) | `ம்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| கை | ஞான்றது / ஞாற்சி | கைஞ்ஞான்றது / கைஞ்ஞாற்சி | `அல்வழி` / `வேற்றுமை` (`தனி ஐ`) | `ஞ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| கை | நீண்டது / நீட்சி | கைந்நீண்டது / கைந்நீட்சி | `அல்வழி` / `வேற்றுமை` (`தனி ஐ`) | `ந்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| கை | மாண்டது / மாட்சி | கைம்மாண்டது / கைம்மாட்சி | `அல்வழி` / `வேற்றுமை` (`தனி ஐ`) | `ம்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| நொ | ஞெள்ளா | நொஞ்ஞெள்ளா | `அல்வழி` (verb) | `ஞ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| நொ | நாகா | நொந்நாகா | `அல்வழி` (verb) | `ந்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| நொ | மாடா | நொம்மாடா | `அல்வழி` (verb) | `ம்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| நொ | யவனா | நொய்யவனா | `அல்வழி` (verb, `எச்சவும்மை`) | `ய்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| நொ | வளவா | நொவ்வளவா | `அல்வழி` (verb, `எச்சவும்மை`) | `வ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| து | ஞெள்ளா | துஞ்ஞெள்ளா | `அல்வழி` (verb) | `ஞ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| து | நாகா | துந்நாகா | `அல்வழி` (verb) | `ந்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| து | மாடா | தும்மாடா | `அல்வழி` (verb) | `ம்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| து | யவனா | துய்யவனா | `அல்வழி` (verb, `எச்சவும்மை`) | `ய்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |
| து | வளவா | துவ்வளவா | `அல்வழி` (verb, `எச்சவும்மை`) | `வ்` insertion | `viruttiyurai_pno=226`, `kandigai=158` |

### Surface Signature & Reversibility
- **Signature**: Nasal/approximant gemination at `மெய்`, `கை`, `நொ`, `து` + `{ஞ,ந,ம,(ய,வ)}`; natural elsewhere.
- **Reversibility**: Strip doubled `{ஞ்,ந்,ம்,ய்,வ்}` when `first` matches `{குறில்+ய், தனி ஐ, நொ, து}`.

---

## Sutra 159

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** General (`பொதுப் புணர்ச்சி`) | **Executable:** Rule (Deterministic + Lexical Exception) | **Viruttiyurai pno:** 226, 227, 228 | **Kandigai:** 159 | **Poetic:** No

### Root Text (TVA 1999)
> பொதுப்பெய ருயர்திணைப் பெயர்க ளீற்றுமெய்  
> வலிவரி னியல்பா மாவி யரமுன்  
> வன்மை மிகாசில விகாரமா முயர்திணை.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`பொது பெயர் உயர்திணை பெயர்கள் ஈற்று மெய் / வலி வரின் இயல்பு ஆம் ஆவி ய ர முன் / வன்மை மிகா சில விகாரம் ஆம் உயர்திணை`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R159.1 (Consonant-Final Common & Rational Nouns before Hard Consonants)**: `IF` `first.pos_class in {Poduppeyar (பொதுப்பெயர் / விரவுப்பெயர்), Uyartinaipeyar (உயர்திணைப்பெயர்)}` AND `first` ends in a consonant (`ஈற்று மெய்`) AND `second` starts with `வல்லினம்` (`க, ச, த, ப`) `THEN` `first`'s final consonant remains **natural** (`இயல்பு`) in both `அல்வழி` and `வேற்றுமை` — EXCEPT where phonotactic consonant cluster constraints (`மயக்க விதி இன்மை`) force mutation (e.g., `ல் + த -> றீ/ற` as in `தோன்றல் + தீயன் -> தோன்றறீயன்`, `ள் + த -> டீ/ட` as in `வேள் + தீயன் -> வேடீயன்`).
2. **R159.2 (Vowel / `ய்` / `ர்`-Final Common & Rational Nouns before `க, ச, த, ப`)**: `IF` `first.pos_class in {Poduppeyar, Uyartinaipeyar}` AND `first` ends in `உயிர்` (vowel), `ய்`, or `ர்` (`ழ்` does not end rational/common nouns) AND `second` starts with `க, ச, த, ப` `THEN` `க, ச, த, ப` do **NOT** double (`வன்மை மிகா`) in both `அல்வழி` and `வேற்றுமை`.
3. **R159.3 (Lexicalized Mutations in Some `உயர்திணை` Nouns)**: `IF` `first.pos_class == Uyartinaipeyar` AND `first` is in the special rational-noun subclass (both vowel-final and consonant-final, before any of the 4 consonant/vowel classes `நாற்கணம்`) `THEN` `first` and/or `second` undergo lexicalized `விகாரம்` (e.g., `அன்`/`அர்` elision, optional or obligatory `வல்லெழுத்து மிகல்`, `ஆன் -> அன்`, `ளன் -> ண்`, `ல் -> ட்`).

### Interactions & Precedence
- **Partially overridden by Sutra 165**: Sutra 165 (`இயல்பினும் விதியினும் நின்ற உயிர்முன் கசதப மிகும்`) overrides R159.2 for specific vowel-final rational/common nouns where `வல்லினம்` doubles (e.g., `ஆடூஉக் குறியன்`, `நம்பிக் கொற்றன்`, `சாத்திப்பெண்`, `செட்டித்தெரு`).
- **Distinction**: `உயர்திணை` vs `அஃறிணை` lexical tagging is mandatory on nouns to select R159.2 vs Sutra 165.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| சாத்தன் | குறிது / கை | சாத்தன்குறிது / சாத்தன்கை | `அல்வழி` / `வேற்றுமை` (`பொதுப்பெயர்`) | natural | `viruttiyurai_pno=227`, `kandigai=159` |
| ஊரன் | குறியன் / கை | ஊரன்குறியன் / ஊரன்கை | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`) | natural | `viruttiyurai_pno=227`, `kandigai=159` |
| தோன்றல் | குறியன் / கை | தோன்றல்குறியன் / தோன்றல்கை | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`) | natural | `kandigai=159` |
| தோன்றல் | தீயன் / தலை | தோன்றறீயன் / தோன்றறலை | `அல்வழி` / `வேற்றுமை` (cluster constraint) | `ல் + த் -> ற்` | `kandigai=159` |
| வேள் | தீயன் / தலை | வேடீயன் / வேடலை | `அல்வழி` / `வேற்றுமை` (cluster constraint) | `ள் + த் -> ட்` | `kandigai=159` |
| சாத்தி | குறிது / குறியள் / கை | சாத்திகுறிது / சாத்திகுறியள் / சாத்திகை | `அல்வழி` / `வேற்றுமை` (`பொதுப்பெயர்`) | no doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| தாய் | கை | தாய்கை | `வேற்றுமை` (`பொதுப்பெயர்`, `ய்`) | no doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| நம்பி | குறியன் / கை | நம்பிகுறியன் / நம்பிகை | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`) | no doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| சேய் | குறியன் | சேய்குறியன் | `அல்வழி` (`உயர்திணை`, `ய்`) | no doubling | `viruttiyurai_pno=227` |
| அவர் | குறியர் / கை | அவர்குறியர் / அவர்கை | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`, `ர்`) | no doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| கபிலன் | பரணன் | கபிலபரணர் | `உயர்திணை` (`உம்மைத்தொகை`) | `ன்` elision + `ர்` plural | `viruttiyurai_pno=227`, `kandigai=159` |
| வடுகன் | நாகன் / நாதன் | வடுகநாகன் / வடுகநாதன் | `உயர்திணை` (`இருபெயரொட்டு`) | `ன்` elision, no doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| அரசன் | வள்ளல் | அரசவள்ளல் | `உயர்திணை` | `ன்` elision | `viruttiyurai_pno=227`, `kandigai=159` |
| ஆசீவகர் | பள்ளி | ஆசீவகப்பள்ளி | `உயர்திணை` | `ர்` elision + `ப்` doubling | `viruttiyurai_pno=227`, `kandigai=159` |
| வாணிகர் | தெரு | வாணிகத்தெரு | `உயர்திணை` | `ர்` elision + `த்` doubling | `kandigai=159` |
| குமரன் | கோட்டம் | குமரகோட்டம் / குமரக்கோட்டம் | `உயர்திணை` (optional) | `ன்` elision + optional `க்` doubling | `viruttiyurai_pno=227..228`, `kandigai=159` |
| வாசுதேவன் | கோட்டம் | வாசுதேவகோட்டம் / வாசுதேவக்கோட்டம் | `உயர்திணை` (optional) | `ன்` elision + optional `க்` doubling | `kandigai=159` |
| பார்ப்பான் | கன்னி | பார்ப்பனக்கன்னி | `உயர்திணை` | `ஆ -> அ` + `அ` cāriyai + `க்` doubling | `kandigai=159` |
| வேளாளன் | பிள்ளை | வேளாண்பிள்ளை | `உயர்திணை` | `அன்` elision + `ள் -> ண்` | `kandigai=159` |
| மக்கள் | பண்பு / சுட்டு | மக்கட்பண்பு / மக்கட்சுட்டு | `உயர்திணை` | `ள் -> ட்` | `kandigai=159` |

### Surface Signature & Reversibility
- **Signature**: Absence of `வல்லொற்று` doubling after `பொதுப்பெயர்`/`உயர்திணை` finals; `அன்`/`அர்` truncation in compound rational names.
- **Reversibility**: Requires `பொதுப்பெயர்`/`உயர்திணை` dictionary lookup to distinguish non-doubling from `அஃறிணை` doubling.

---

## Sutra 160

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** General (`பொதுப் புணர்ச்சி`) | **Executable:** Rule (Deterministic) | **Viruttiyurai pno:** 228 | **Kandigai:** 160 | **Poetic:** No

### Root Text (TVA 1999)
> ஈற்றியா வினாவிளிப் பெயர்முன்வலி யியல்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`ஈற்று யா வினா விளி பெயர் முன் வலி இயல்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R160.1 (Final Interrogative Clitics `ஆ, ஏ, ஓ`)**: `IF` `first` ends in an interrogative clitic (`ஈற்று வினா` = `ஆ, ஏ, ஓ`, per Sutra 67) AND `second` starts with `வல்லினம்` (`க, ச, த, ப`) `THEN` `second`'s initial `வல்லினம்` remains **natural** (`இயல்பு`). *(Note: `ஏ, ஓ` are further handled in Sutra 201 `இடைச்சொல்லேயோ`.)*
2. **R160.2 (Interrogative Pronoun `யா`)**: `IF` `first == யா` (interrogative pronoun) AND `second` starts with `வல்லினம்` `THEN` `வல்லினம்` remains **natural** (`இயல்பு`).
3. **R160.3 (Vocative Nouns `விளிப்பெயர்`)**: `IF` `first` is a vocative noun (`விளிப்பெயர்`, vowel-final or consonant-final, proximate `அண்மை விளி` or distant `சேய்மை விளி`) AND `second` starts with `வல்லினம்` `THEN` `வல்லினம்` remains **natural** (`இயல்பு`).

### Interactions & Precedence
- Overrides Sutra 165 (`உயிர்முன் கசதப மிகும்`) for `ஆ, ஏ, ஓ` interrogatives, `யா`, and vowel-final vocatives.
- Links to Sutra 201 (`இடைச்சொல்லேயோ`) for `ஏ, ஓ` particle rules.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| நம்பியா | கொண்டான் | நம்பியா கொண்டான் | `வினா` (`ஆ` clitic) | natural | `viruttiyurai_pno=228`, `kandigai=160` |
| உண்கா | கொற்றா | உண்கா கொற்றா | `வினா` (`ஆ` clitic on `உண்கு+ஆ`) | natural | `viruttiyurai_pno=228`, `kandigai=160` |
| யா | குறிய / குறியன | யா குறிய / யா குறியன | `யா` interrogative | natural | `viruttiyurai_pno=228`, `kandigai=160` |
| நம்பி / நம்பீ | கொள் | நம்பி கொள் / நம்பீ கொள் | `விளி` (proximate / distant) | natural | `viruttiyurai_pno=228`, `kandigai=160` |
| விடலை / விடலாய் | கொள் | விடலை கொள் / விடலாய் கொள் | `விளி` | natural | `viruttiyurai_pno=228`, `kandigai=160` |
| தாய் / தாயே | கொள் / செல் / தா / போ | தாய் கொள் / தாயே கொள் | `விளி` | natural | `viruttiyurai_pno=228`, `kandigai=160` |

### Surface Signature & Reversibility
- **Signature**: No `க், ச், த், ப்` insertion after `{ஆ, ஏ, ஓ}` interrogative, `யா`, or vocatives.
- **Reversibility**: Requires morphosyntactic tag (`Interrogative` / `Vocative`) to block doubling.

---

## Sutra 161

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** General (`பொதுப் புணர்ச்சி`) | **Executable:** Rule (Optional / Vikalpam) | **Viruttiyurai pno:** 228, 229 | **Kandigai:** 161 | **Poetic:** No

### Root Text (TVA 1999)
> ஆவி யரழ விறுதிமுன் னிலைவினை  
> ஏவன்முன் வல்லின மியல்பொடு விகற்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`ஆவி ய ர ழ இறுதி முன்னிலை வினை / ஏவல் முன் வல்லினம் இயல்பு ஒடு விகற்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R161.1 (2nd-Person Finite Verb `முன்னிலைவினை`)**: `IF` `first` is a 2nd-person finite verb (`முன்னிலைவினை`, distinct from imperative `ஏவல்`, having 1st/3rd-person counterparts) ending in a vowel (`ஆவி`), `ய்`, or `ர்` (`ழ்` does not end `முன்னிலைவினை`) AND `second` begins with `வல்லினம்` (`க, ச, த, ப`) `THEN` `வல்லினம்` is primarily **natural** (`இயல்பு`), with rare **optionality** (`விகற்பம்`, i.e., occasional doubling).
2. **R161.2 (2nd-Person Imperative `ஏவல்`)**: `IF` `first` is a 2nd-person imperative verb (`ஏவல்`) ending in a vowel (`ஆவி`), `ய்`, `ர்`, or `ழ்` AND `second` begins with `வல்லினம்` `THEN` `வல்லினம்` is primarily **natural** (`இயல்பு`), with **optional doubling** (`விகற்பம்` — e.g., `நட கொற்றா` / `நடக் கொற்றா`).

### Interactions & Precedence
- **Overridden by Sutra 165 for `நொ, து`**: Imperatives `நொ` and `து` are explicitly excluded from R161.2 optionality and undergo obligatory doubling (`நொக்கொற்றா`, `துக்கொற்றா`) per Sutra 165 commentary (Viruttiyurai pno=233).
- Contrast with `இயல்பொடு விகற்பே`: `இயல்பு` is the unmarked default; `விகற்பம்` (natural OR doubled) is marked/rarer.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| உண்டி | கொற்றா / சாத்தா | உண்டி கொற்றா / உண்டி சாத்தா | `முன்னிலைவினை` (default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| உண்டனை | கொற்றா | உண்டனை கொற்றா | `முன்னிலைவினை` (default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| உண்டாய் | கொற்றா | உண்டாய் கொற்றா | `முன்னிலைவினை` (`ய்`, default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| உண்டனிர் | கொற்றரே | உண்டனிர் கொற்றரே | `முன்னிலைவினை` (`ர்`, default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| கொணா / எறி / விடு | கொற்றா | கொணா கொற்றா / எறி கொற்றா / விடு கொற்றா | `ஏவல்` (vowel, default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| ஆய் / சேர் / தாழ் | கொற்றா | ஆய் கொற்றா / சேர் கொற்றா / தாழ் கொற்றா | `ஏவல்` (`ய், ர், ழ்`, default) | natural | `viruttiyurai_pno=228`, `kandigai=161` |
| நட | கொற்றா | நட கொற்றா / நடக் கொற்றா | `ஏவல்` (`விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=228`, `kandigai=161` |
| எய் | கொற்றா | எய் கொற்றா / எய்க் கொற்றா | `ஏவல்` (`ய்`, `விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=228`, `kandigai=161` |
| ஈர் | கொற்றா | ஈர் கொற்றா / ஈர்க் கொற்றா | `ஏவல்` (`ர்`, `விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=228` |
| தாழ் | கொற்றா | தாழ் கொற்றா / தாழ்க் கொற்றா | `ஏவல்` (`ழ்`, `விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=228` |

### Surface Signature & Reversibility
- **Signature**: Optional `க், ச், த், ப்` gemination after `{V, ய், ர், ழ்}`-final imperatives/2nd-person verbs.
- **Reversibility**: Both natural and doubled surfaces map to `(first, second)` when `first` is `முன்னிலைவினை` or `ஏவல்`.

---

## Sutra 162

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`உயிரீற்றுச் சிறப்புப் புணர்ச்சி`) | **Executable:** Rule (Deterministic + Lexical/Contextual `ஏ`) | **Viruttiyurai pno:** 229, 230 | **Kandigai:** 162 | **Poetic:** No

### Root Text (TVA 1999)
> இஈ ஐவழி யவ்வு மேனை  
> உயிர்வழி வவ்வு மேமுனிவ் விருமையும்  
> உயிர்வரி னுடம்படு மெய்யென் றாகும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`இ ஈ ஐ வழி ய உம் ஏனை / உயிர் வழி வ உம் ஏ முன் இவ் இருமை உம் / உயிர் வரின் உடம்படுமெய் என்று ஆகும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R162.1 (`இ, ஈ, ஐ` + Vowel -> `ய்` Glide)**: `IF` `first` ends in `இ`, `ஈ`, or `ஐ` (excluding `குற்றியலுகரம்` / `எ` / special overrides) AND `second` begins with any vowel `THEN` insert `உடம்படுமெய்` **`ய்`** at the boundary (then attach `second`'s initial vowel onto `ய்` via Sutra 204 `உடன்மேல் உயிர்`).
2. **R162.2 (`அ, ஆ, உ, ஊ, ஒ, ஓ, ஔ` + Vowel -> `வ்` Glide)**: `IF` `first` ends in `அ, ஆ, உ, ஊ, ஒ, ஓ, ஔ` (`ஏனை உயிர்`, excluding `எ` per Sutra 163 and `குற்றியலுகரம்` per Sutra 164) AND `second` begins with any vowel `THEN` insert `உடம்படுமெய்` **`வ்`** at the boundary (and for short-vowel monosyllables like `நொ`, `வ்` doubles via Sutra 205 `தனிக்குறில் முன்னொற்று` -> `நொவ்வழகிது`).
3. **R162.3 (`ஏ` + Vowel -> `ய்` or `வ்` Glide)**: `IF` `first` ends in `ஏ` AND `second` begins with any vowel `THEN` insert either **`ய்`** or **`வ்`** (specifically: `ஏ` particle takes `ய்`, e.g., `அவனே + அழகன் -> அவனேயழகன்`, `ஏயே + இவள் -> ஏயேயிவள்`; monosyllabic `ஏ`/`சே` verb/noun takes `வ்`, e.g., `ஏ + எலாம் -> ஏவெலாம்`, `சே + அழகிது -> சேவழகிது`; `சே` from `செம்மை` takes both `சே + அடி -> சேயடி / சேவடி`).

### Interactions & Precedence
- **Overridden by Sutra 163**: `எ` interrogative and `அ, இ, உ` demonstratives take `வ்` (or `ய்` when lengthened in poetry), NOT R162.1/R162.2.
- **Overridden by Sutra 164**: `குற்றியலுகரம்` elides its `உ` before vowels instead of taking `வ்` (except rare poetic/special forms like `அழைப்பதுவே`).
- **Overridden by Sutra 174**: `நாழி + உரி -> நாடுரி` blocks `ய்` insertion (`*நாழியுரி` rejected by Viruttiyurai).
- **Chains with Sutra 204 (`உடன்மேல் உயிர்`) & Sutra 205 (`தனிக்குறில் முன்னொற்று`)**: `நொ + அழகிது -> நொ + வ் + அழகிது -> நொவ் + வ் + அழகிது -> நொவ்வழகிது`.
- **Exception noted**: Poetic/lexical `மா + இரு -> மாயிரு` (`உரிச்சொல்` `மா` takes `ய்` instead of `வ்`, deferred to Sutra 239).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| மணி | அழகிது / ஒளி | மணியழகிது / மணியொளி | `அல்வழி` / `வேற்றுமை` (`இ`) | insert `ய்` | `viruttiyurai_pno=229`, `kandigai=162` |
| தீ | எழுந்தது | தீயெழுந்தது | `அல்வழி` (`ஈ`) | insert `ய்` | `viruttiyurai_pno=229` |
| அவை | ஒளவியம் | அவையௌவியம் | `அல்வழி` (`ஐ`) | insert `ய்` | `viruttiyurai_pno=229` |
| பனை | அழகிது | பனையழகிது | `அல்வழி` (`ஐ`) | insert `ய்` | `kandigai=162` |
| விள | அழகிது / அடி | விளவழகிது / விளவடி | `அல்வழி` / `வேற்றுமை` (`அ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| பலா | அழகிது | பலாவழகிது | `அல்வழி` (`ஆ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| கடு | அழகிது | கடுவழகிது | `அல்வழி` (`உ`, முற்றியலுகரம்) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| பூ | அழகிது | பூவழகிது | `அல்வழி` (`ஊ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| நொ | அழகிது | நொவ்வழகிது | `அல்வழி` (`ஒ`, `தனிக்குறில்`) | insert `வ்` + geminate `வ்` (Sutra 205) | `viruttiyurai_pno=229`, `kandigai=162` |
| சோ / கோ | அழகிது | சோவழகிது / கோவழகிது | `அல்வழி` (`ஓ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| கௌ | அழகிது | கௌவழகிது | `அல்வழி` (`ஔ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| ஏயே | இவள் | ஏயேயிவள் | `அல்வழி` (`ஏ`) | insert `ய்` | `viruttiyurai_pno=229` |
| அவனே | அழகன் | அவனேயழகன் | `அல்வழி` (`ஏ` particle) | insert `ய்` | `kandigai=162` |
| ஏ | எலாம் | ஏவெலாம் | `அல்வழி` (`ஏ` monosyllable) | insert `வ்` | `kandigai=162` |
| சே | அழகிது / உழுதது | சேவழகிது / சேவுழுதது | `அல்வழி` (`ஏ`) | insert `வ்` | `viruttiyurai_pno=229`, `kandigai=162` |
| சே | அடி | சேயடி / சேவடி | `பண்புத்தொகை` (`ஏ`, both) | insert `ய்` or `வ்` | `kandigai=162` |

### Surface Signature & Reversibility
- **Signature**: Intervocalic `ய்` or `வ்` (or `வ்வ்` after short monosyllable) bridging `V1 + V2`.
- **Reversibility**: Deterministic glide stripping when `V1` matches `{இ,ஈ,ஐ}` (`ய்`), `{அ,ஆ,உ,ஊ,ஒ,ஓ,ஔ}` (`வ்`), or `{ஏ}` (`ய்|வ்`), provided `first` is not a `குற்றியலுகரம்` or demonstrative/interrogative clitic.

---

## Sutra 163

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`உயிரீற்றுச் சிறப்புப் புணர்ச்சி`) | **Executable:** Rule (Deterministic + Poetic Clause) | **Viruttiyurai pno:** 230, 231 | **Kandigai:** 163 | **Poetic:** Partial (includes poetic lengthening)

### Root Text (TVA 1999)
> எகர வினாமுச் சுட்டின் முன்னர்  
> உயிரும் யகரமு மெய்தின் வவ்வும்  
> பிறவரி னவையுந் தூக்கிற் சுட்டு  
> நீளின் யகரமுந் தோன்றுத னெறியே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`எகர வினா மு சுட்டின் முன்னர் / உயிர் உம் யகரம் உம் எய்தின் வ உம் / பிற வரின் அவை உம் தூக்கு இல் சுட்டு / நீளின் யகரம் உம் தோன்றுதல் நெறி ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R163.1 (`எ, அ, இ, உ` + Vowel or `ய` -> `வ்` + Gemination)**: `IF` `first in {எ (வினா இடைச்சொல்), அ, இ, உ (சுட்டு இடைச்சொல்)}` AND `second` begins with a **vowel** OR **`ய`** `THEN` insert **`வ்`** (not an `உடம்படுமெய்`; when `second` begins with a vowel, `வ்` doubles via Sutra 205 `தனிக்குறில் முன்னொற்று`, e.g., `அ + அணி -> அவ்வணி`, and `second`'s vowel attaches via Sutra 204).
2. **R163.2 (`எ, அ, இ, உ` + Other Consonant -> Consonant Gemination)**: `IF` `first in {எ, அ, இ, உ}` AND `second` begins with any consonant **other than `ய`** (`க, ச, த, ப, ங, ஞ, ந, ம, வ`) `THEN` **double that initial consonant** (`அவை தோன்றும்`, e.g., `எ + குதிரை -> எக்குதிரை`, `எ + ஙனம் -> எங்ஙனம்`, `அ + ஞாலம் -> அஞ்ஞாலம்`).
3. **R163.3 (Poetic Lengthened Demonstrative + Vowel -> `ய்`)**: `IF` `poetic == true` (`தூக்கில்`) AND demonstrative `அ, இ, உ` is lengthened (`ஆ, ஈ, ஊ`, e.g., `ஆ`) AND `second` begins with a **vowel** `THEN` insert **`ய்`** (`ஆ + இடை -> ஆயிடை`). *(Does NOT apply before consonants, e.g., `ஆவயின்` / `ஆங்ஙனம்`.)*
4. **R163.4 (`நெறி` Analogical Extensions)**: By `நெறி` ("established pattern"), both *Viruttiyurai* (`pno=231`) and *Kandigai* (`163`) add three extensions:
   - `(a)` `யா + ஙனம் -> யாங்ஙனம்` and lengthened demonstratives `ஆ/ஈ/ஊ + ஙனம் -> ஆங்ஙனம், ஈங்ஙனம், ஊங்ஙனம்` geminate `ங`.
   - `(b)` Demonstrative pronoun/adverb lengthening (`ஈது`, `ஆங்கு, ஈங்கு, ஊங்கு`, `ஆண்டு, ஈண்டு`).
   - `(c)` Non-*udambadumei* `வ்` insertion after consonant-final stems before vowel-initial suffixes/words (`விண் + அத்து -> விண்வத்து`, `செல் + உழி -> செல்வுழி`, `சார் + உழி -> சார்வுழி`).

### Interactions & Precedence
- **Overrides Sutra 162** (`உடம்படுமெய்`) for `இ` before vowels (`இ + அணி -> இவ்வணி`, not `*இயணி`).
- **Overrides Sutra 158** (`ஞ, ந, ம, ய, வ` natural) for `எ, அ, இ, உ` before `ஞ, ந, ம, ய, வ` (`எவ்யானை`, `எஞ்ஞாலம்`, `எந்நாடு`, `எம்மனை`, `எவ்வளை`).
- **Chains with Sutra 204 & 205** for `V + V` gemination (`அவ்வணி`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| எ | அணி | எவ்வணி | `எகர வினா` + vowel | insert `வ்` + geminate `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |
| எ | யானை | எவ்யானை | `எகர வினா` + `ய` | insert `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |
| அ / இ / உ | அணி | அவ்வணி / இவ்வணி / உவ்வணி | `சுட்டு` + vowel | insert `வ்` + geminate `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |
| அ / இ / உ | யானை | அவ்யானை / இவ்யானை / உவ்யானை | `சுட்டு` + `ய` | insert `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |
| எ | குதிரை / சேனை / தண்டு / படை | எக்குதிரை / எச்சேனை / எத்தண்டு / எப்படை | `எகர வினா` + stop | geminate initial stop | `kandigai=163` *(Viruttiyurai lists for `அ,இ,உ`)* |
| எ | ஞாலம் / நாடு / மனை / வளை | எஞ்ஞாலம் / எந்நாடு / எம்மனை / எவ்வளை | `எகர வினா` + nasal/`வ` | geminate initial `ஞ,ந,ம,வ` | `kandigai=163` |
| எ / அ / இ / உ | ஙனம் | எங்ஙனம் / அங்ஙனம் / இங்ஙனம் / உங்ஙனம் | `வினா`/`சுட்டு` + `ங` | geminate `ங்` | `viruttiyurai_pno=231`, `kandigai=163` |
| ஆ | இடை | ஆயிடை | `poetic` (`சுட்டு நீடல்` + vowel) | `அ -> ஆ` + insert `ய்` | `viruttiyurai_pno=231`, `kandigai=163` |
| யா | ஙனம் | யாங்ஙனம் | `நெறி` (`யா` + `ங`) | geminate `ங்` | `viruttiyurai_pno=231`, `kandigai=163` |
| ஆ / ஈ / ஊ | ஙனம் | ஆங்ஙனம் / ஈங்ஙனம் / ஊங்ஙனம் | `நெறி` (lengthened `சுட்டு` + `ங`) | geminate `ங்` | `viruttiyurai_pno=231`, `kandigai=163` |
| விண் | அத்து | விண்வத்து | `நெறி` (non-*udambadumei* `வ்` after `மெய்`) | insert `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |
| செல் / சார் | உழி | செல்வுழி / சார்வுழி | `நெறி` (non-*udambadumei* `வ்` after `மெய்`) | insert `வ்` | `viruttiyurai_pno=231`, `kandigai=163` |

### Surface Signature & Reversibility
- **Signature**: Prefix `[அஇஉஎ]வ்வ்?[உயிர்]` or `[அஇஉஎ]வ்[ய]` or `[அஇஉஎ]C_i C_i`.
- **Reversibility**: Strip proclitic `[அஇஉஎ]` + doubled consonant (or `வ்வ்` before vowel, `வ்` before `ய`).

---

## Sutra 164

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`உயிரீற்றுச் சிறப்புப் புணர்ச்சி`) | **Executable:** Rule (Deterministic + Rare Exception) | **Viruttiyurai pno:** 231, 232 | **Kandigai:** 164 | **Poetic:** No

### Root Text (TVA 1999)
> உயிர்வரி னுக்குறண் மெய்விட் டோடும்  
> யவ்வரி னிய்யா முற்றுமற் றொரோவழி.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`உயிர் வரின் உ குறள் மெய் விட்டு ஓடும் / ய வரின் இ ஆம் முற்று உம் அற்று ஒரோ வழி`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R164.1 (*Kuṟṟiyalugaram* + Vowel -> `உ` Elision)**: `IF` `first` ends in `குற்றியலுகரம்` (shortened `உ`, per Sutra 94) AND `second` begins with a **vowel** `THEN` the final `உ` **elides** (`மெய் விட்டு ஓடும்`), leaving its supporting stop consonant (`க், ச், ட், த், ப், ற்`), onto which `second`'s initial vowel attaches (per Sutra 204 `உடன்மேல் உயிர்`).
2. **R164.2 (*Kuṟṟiyalugaram* + `ய` -> `இ` (*Kuṟṟiyaligaram*))**: `IF` `first` ends in `குற்றியலுகரம்` AND `second` begins with **`ய`** `THEN` the final `உ` mutates to **`இ`** (*Kuṟṟiyaligaram*, linking to Sutra 93).
3. **R164.3 (*Muṟṟiyalugaram* Occasional Elision / `இ` Mutation)**: `IF` `first` ends in `முற்றியலுகரம்` (full `உ`, e.g., `கதவு`, `செலவு`, `அது`, `இது`) in specific lexical/contextual items (`ஒரோவழி`) AND `second` begins with a vowel or `ய` `THEN` `உ` may similarly elide before a vowel (`கதவழகிது`, `அதனை`, `அதை`) or become `இ` before `ய` (`கதவியாது`).
4. **R164.4 (Rare *Kuṟṟiyalugaram* Retention with `வ்` *Udambadumei*)**: Because the sutra says `ஓடும்` ("runs away") rather than `கெடும்`, in rare instances (`ஒரோவழி`, e.g., `அழைப்பது + ஏ -> அழைப்பதுவே`, `அடித்து + அக்காரம் -> அடித்து வக்காரம்`), `குற்றியலுகரம்` does NOT elide and instead takes `வ்` glide via Sutra 162.

### Interactions & Precedence
- **Overrides Sutra 162** (`உடம்படுமெய்` `வ்`) for all `குற்றியலுகரம்` stems.
- **Links to Sutra 93 & 94**: Requires accurate `குற்றியலுகரம்` vs `முற்றியலுகரம்` classification on `உ`-final words (e.g., `நாகு` is `நெடிற்றொடர்க் குற்றியலுகரம்`; `கதவு`, `அது` are `முற்றியலுகரம்`).
- **Chains with Sutra 204** (`உடன்மேல் உயிர்`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| நாகு | அரிது / அருமை | நாகரிது / நாகருமை | `அல்வழி` / `வேற்றுமை` (`குற்றியலுகரம்`) | elide `உ`; `க்+அ -> க` | `viruttiyurai_pno=232`, `kandigai=164` |
| நாகு | யாது / யாப்பு / யமன் | நாகியாது / நாகியாப்பு / நாகியமன் | `அல்வழி` / `வேற்றுமை` (`குற்றியலுகரம்`) | `உ -> இ` (`குற்றியலிகரம்`) | `viruttiyurai_pno=232`, `kandigai=164` |
| நாகு | இன் + வளர்ச்சி | நாகின் வளர்ச்சி | `வேற்றுமை` (`இன்` cāriyai) | elide `உ` before `இன்` | `viruttiyurai_pno=232` |
| தனாது | அடி | தனாதடி | `வேற்றுமை` (`குற்றியலுகரம்`) | elide `உ` | `viruttiyurai_pno=232` |
| கதவு | அழகிது | கதவழகிது | `அல்வழி` (`முற்றியலுகரம்`, `ஒரோவழி`) | elide `உ` | `viruttiyurai_pno=232`, `kandigai=164` |
| கதவு | யாது | கதவியாது | `அல்வழி` (`முற்றியலுகரம்`, `ஒரோவழி`) | `உ -> இ` | `viruttiyurai_pno=232`, `kandigai=164` |
| அது / இது | அன் + ஐ | அதனை / இதனை | `வேற்றுமை` (`முற்றியலுகரம்`) | elide `உ` before `அன்` | `viruttiyurai_pno=232` |
| அது | ஐ | அதை | `வேற்றுமை` (`முற்றியலுகரம்`) | elide `உ` | `kandigai=164` |
| அழைப்பது | ஏ | அழைப்பதுவே | `ஒரோவழி` (`குற்றியலுகரம்` retention) | `வ்` udambadumei (Sutra 162) | `viruttiyurai_pno=232`, `kandigai=164` |
| அடித்து | அக்காரம் | அடித்து வக்காரம் | `ஒரோவழி` (`குற்றியலுகரம்` retention) | `வ்` udambadumei (Sutra 162) | `kandigai=164` |

### Surface Signature & Reversibility
- **Signature**: `[க்ச்ட்த்ப்ற்][vowel]` for elided `குற்றியலுகரம்`; `[க்ச்ட்த்ப்ற்]இ + ய...` for `குற்றியலிகரம்`.
- **Reversibility**: Reconstruct `உ` on the consonant preceding `V` or restore `இ -> உ` before `ய` when `first` is a valid `குற்றியலுகரம்` stem.

---

## Sutra 165

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`உயிரீற்றின் முன் வல்லினம்` — General Default) | **Executable:** Rule (Default Vowel-Final *Valimigal*) | **Viruttiyurai pno:** 233, 234 | **Kandigai:** 165 | **Poetic:** No

### Root Text (TVA 1999)
> இயல்பினும் விதியினு நின்ற வுயிர்முன்  
> கசதப மிகும்வித வாதன மன்னே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`இயல்பின் உம் விதியின் உம் நின்ற உயிர் முன் / க ச த ப மிகும் விதவாதன மன் ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R165.1 (Default Hard-Consonant Doubling after Vowel Finals)**: `IF` `first` ends in a vowel — either naturally (`இயல்பீறு`) or as the result of an earlier sandhi derivation (`விதியீறு`, e.g., `ஒற்றை`, `வட்ட`, `தாழ` from `மெய்யீறு` elision) — AND `first` is NOT excluded by any specific blocking rule (`விதவாதன`, i.e., Sutras `159, 160, 161, 166, 167, 168, 171, 173, 174, 176, 177`, etc.) AND `second` begins with `க, ச, த, ப` `THEN` the initial `வல்லினம்` (`க், ச், த், ப்`) **usually doubles** (`பெரும்பாலும் மிகும்`) in both `அல்வழி` and `வேற்றுமை` across all POS (`உயர்திணை/பொது/அஃறிணை பெயர்`, `வினையெச்சம்`, `வினைமுற்று`, `இடை`, `உரி`, `திசை`, `வடசொல்`).
2. **R165.2 (`நொ, து` Imperative Override)**: Because `மன்` ("usually") implies exceptions both ways, `நொ` and `து` (not covered by Sutra 161's optionality) **obligatorily double** `க, ச, த, ப` (`நொக்கொற்றா`, `துக்கொற்றா`), completing 3-class doubling with Sutra 158.
3. **R165.3 (Lexical Non-Doubling Residual)**: Some unblocked vowel-final nouns (`சிறுபான்மை மிகா`) do not double in specific compounds/phrases (e.g., `ஏரிகரை`, `குழந்தைகை`, `குழவிகை`, `மலைகிழவோன்`, `கூப்புகரம்`, `ஈட்டுதனம்`, `நாட்டுபுகழ்`).

### Interactions & Precedence
- **Default rule** for `V + {க, ச, த, ப}`; **overridden** by all specific blocking/nasal rules (`159, 160, 161, 166, 167, 168, 171, 173, 176, 177`).
- Crucially applies to **derived vowel finals (`விதியீறு`)** such as `வட்ட + கல் -> வட்டக்கல்` (`வட்டம் -> வட்ட`), `தாழ + கோல் -> தாழக்கோல்` (`தாழ் -> தாழ`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| ஆடூஉ | குறியன் / கை | ஆடூஉக் குறியன் / ஆடூஉக் கை | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| நம்பி | கொற்றன் / பூ | நம்பிக் கொற்றன் / நம்பிப்பூ | `அல்வழி` / `வேற்றுமை` (`உயர்திணை`) | `க்` / `ப்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| சாத்தி | பெண் | சாத்திப்பெண் | `அல்வழி` (`பொதுப்பெயர்`) | `ப்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| தாரா | கடிது | தாராக் கடிது | `அல்வழி` (`அஃறிணை`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| ஒற்றை / வட்ட / தாழ | கை / கல் / கோல் | ஒற்றைக்கை / வட்டக்கல் / தாழக்கோல் | `அல்வழி` (`விதியீறு`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| விள | கோடு | விளக்கோடு | `வேற்றுமை` (`அஃறிணை`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| கடு | காய் | கடுக்காய் | `வேற்றுமை` (`அஃறிணை`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| ஆடு | கால் | ஆட்டுக்கால் | `வேற்றுமை` (`விதியீறு` `ஆட்டு`) | `க்` insertion | `viruttiyurai_pno=233` |
| ஆடி / ஆடா / ஆடூஉ / ஆடென / ஆட | கொண்டான் | ஆடிக் கொண்டான் / ஆடாக் கொண்டான் / ஆடூஉக் கொண்டான் / ஆடெனக் கொண்டான் / ஆடக் கொண்டான் | `அல்வழி` (`வினையெச்சம்`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| உண்பாக்கு | சென்றான் | உண்பாக்குச் சென்றான் | `அல்வழி` (`வினையெச்சம்`) | `ச்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| பூத்து | காய்த்தது | பூத்துக் காய்த்தது | `அல்வழி` (`வினையெச்சம்`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| பொள்ளென | பரந்தது | பொள்ளெனப் பரந்தது | `அல்வழி` (`வினையெச்சம்`) | `ப்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| சால | பகைத்தது | சாலப் பகைத்தது | `அல்வழி` (`வினையெச்சம்`) | `ப்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| இருளின்றி / பொருளன்றி | கண்டார் / காணார் | இருளின்றிக் கண்டார் / பொருளன்றிக் காணார் | `அல்வழி` (`குறிப்பு வினையெச்சம்`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| மற்றை | சாதி / தெரு | மற்றைச்சாதி / மற்றைத்தெரு | `அல்வழி` (`இடைச்சொல்`) | `ச்` / `த்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| கடி | கமலம் | கடிக்கமலம் | `அல்வழி` (`உரிச்சொல்`) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| சொன்றி | குழிசி | சொன்றிக்குழிசி | `திசைச்சொல்` | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| கங்கை | சடை | கங்கைச்சடை | `வடசொல்` | `ச்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| நொ / து | கொற்றா | நொக்கொற்றா / துக்கொற்றா | `அல்வழி` (`ஏவல்` exception to 161) | `க்` insertion | `viruttiyurai_pno=233`, `kandigai=165` |
| ஏரி / குழந்தை / குழவி | கரை / கை | ஏரிகரை / குழந்தைகை / குழவிகை | residual non-doubling (`சிறுபான்மை மிகா`) | natural | `viruttiyurai_pno=233`, `kandigai=165` |
| மலை | கிழவோனே | மலைகிழவோனே | residual non-doubling | natural | `viruttiyurai_pno=233`, `kandigai=165` |
| கூப்பு / ஈட்டு / நாட்டு | கரம் / தனம் / புகழ் | கூப்புகரம் / ஈட்டுதனம் / நாட்டுபுகழ் | `வினைத்தொகை` / residual non-doubling | natural | `viruttiyurai_pno=233..234`, `kandigai=165` |

### Surface Signature & Reversibility
- **Signature**: `V + [க்ச்த்ப்] + [கசதப]...`
- **Reversibility**: Strip geminated `[க்ச்த்ப்]` before matching `[கசதப]`-initial `second`.

---

## Sutra 166

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`மரப்பெயர்` Nasal Insertion) | **Executable:** Rule (Lexical-conditioned) | **Viruttiyurai pno:** 234 | **Kandigai:** 166 | **Poetic:** No

### Root Text (TVA 1999)
> மரப்பெயர் முன்ன ரினமெல் லெழுத்து  
> வரப்பெறு னவுமுள வேற்றுமை வழியே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`மர பெயர் முன்னர் இன மெல்லெழுத்து / வர பெறுன உம் உள வேற்றுமை வழி ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R166.1 (Vowel-Final Tree Names in *Vēṟṟumai* -> Homorganic Nasal Insertion)**: `IF` `first` belongs to the vowel-final tree-name subclass (`மரப்பெயர்`, e.g., `விள` [`விளா`], `கள` [`களா`], `மா`, `காயா`) AND `context == Vetrumai` AND `second` begins with `க, ச, த, ப` `THEN` instead of hard-consonant doubling (Sutra 165), insert the **homorganic nasal** (`இன மெல்லெழுத்து`: `க் -> ங்`, `ச் -> ஞ்`, `த் -> ந்`, `ப் -> ம்`). *(Note: Does not take `வல்லினம்` doubling alongside it.)*

### Interactions & Precedence
- **Overrides Sutra 165** (`கசதப மிகும்`) for the `மரப்பெயர்` lexical class in `வேற்றுமை`.
- Needs a `tree_nasal_inserting` lexical flag on `விள, கள, மா, காயா` (distinguishing them from trees that take `வல்லினம்` or `அம்` cāriyai).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| விள | காய் | விளங்காய் | `வேற்றுமை` (`மரப்பெயர்`) | `ங்` insertion | `viruttiyurai_pno=234`, `kandigai=166` |
| கள | கனி | களங்கனி | `வேற்றுமை` (`மரப்பெயர்`) | `ங்` insertion | `viruttiyurai_pno=234`, `kandigai=166` |
| மா | கொம்பு / செதிள் / தோல் / பழம் / துளிர் | மாங்கொம்பு / மாஞ்செதிள் / மாந்தோல் / மாம்பழம் / மாந்துளிர் | `வேற்றுமை` (`மரப்பெயர்`) | `ங்` / `ஞ்` / `ந்` / `ம்` insertion | `viruttiyurai_pno=234`, `kandigai=166` |
| காயா | பூ | காயாம்பூ | `வேற்றுமை` (`மரப்பெயர்`) | `ம்` insertion | `kandigai=166` |

### Surface Signature & Reversibility
- **Signature**: `V + [ங்ஞ்ந்ம்] + [கசதப]` (homorganic nasal-stop cluster).
- **Reversibility**: Strip homorganic nasal `{ங்->க, ஞ்->ச, ந்->த, ம்->ப}` when `first` is in `மரப்பெயர்`.

---

## Sutra 167

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`அகரவீற்றுச் சிறப்புவிதி` — Blocking Environments) | **Executable:** Rule (Deterministic) | **Viruttiyurai pno:** 234, 235, 236 | **Kandigai:** 167 | **Poetic:** No

### Root Text (TVA 1999)
> செய்யிய வென்னும் வினையெச்சம் பல்வகைப்  
> பெயரி னெச்சமுற் றாற னுருபே  
> அஃறிணைப் பன்மை யம்மமுன்* னியல்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`செய்யிய என்னும் வினையெச்சம் பல் வகை / பெயரின் எச்சம் முற்று ஆறன் உருபு ஏ / அஃறிணை பன்மை அம்ம முன் இயல்பு ஏ`); footnote 165 notes Sankara Namaccivayar's reading `யம்மமுன் னியல்பே`.

### Atomic Sub-Rules (IF -> THEN)
`IF` `first` ends in **`அ`** AND belongs to any of the following **6 blocking categories** AND `second` begins with `க, ச, த, ப` `THEN` `வல்லினம்` does **NOT** double; it remains **natural** (`இயல்பு`):
1. **R167.1 (`செய்யிய` Adverbial Participle)**: `first` is a `செய்யிய`-pattern `வினையெச்சம்` (e.g., `உண்ணிய`).
2. **R167.2 (All Types of Adjectival Participles `பல்வகைப் பெயரெச்சம்`)**: `first` is any `அ`-final `பெயரெச்சம்` formed from the 4 verb bases (`இயல்பு, பெயர், இடை, உரி`):
   - `தெரிநிலை பெயரெச்சம்` (4 base types: e.g., `உண்ட, உண்ணாநின்ற, உண்ணாத`; `கடைக்கணித்த, சித்திரித்த, வெளுத்த, சினவிய, கறுவிய, அமரிய`; `திண்ணென்ற, பொன் போன்ற`; `சான்ற, உற்ற`)
   - `குறிப்புப் பெயரெச்சம்` (3 base types: e.g., `அமர்முகத்த, கடுங்கண்ண, சிறிய, பெரிய, உள, இல, பல, சில`; `பொன் அன்ன`; `கடிய`).
3. **R167.3 (All Types of `அ`-final Finite Verbs `பல்வகை முற்று`)**: `first` is any `அ`-final `வினைமுற்று` (`தெரிநிலை` like `உண்டன, உண்ணாநின்றன, உண்பன, உண்ணாதன`, `குறிப்பு` like `அமர்முகத்தன, கரியன`, `வியங்கோள்` like `வாழ்க, வாழிய`, and `அன்`-dropped `அ`-final finite verbs), PLUS (by `அருத்தாபத்தி`) finite verbs functioning as `வினையெச்சம்` or `குறிப்புமுற்று` functioning as `ஈரெச்சம்` (`உண்ட கண்டன`, `அமர்முகத்த குதிரை`, `அமர்முகத்த கலக்கின`).
4. **R167.4 (6th-Case Genitive Suffix `ஆறன் உருபு` `அ`)**: `first` ends in the plural/genitive 6th-case marker `அ` (e.g., `தன`).
5. **R167.5 (Non-Rational Plural Nouns `அஃறிணைப் பன்மைப் பெயர்`)**: `first` is an `அ`-final non-rational plural noun (including `குறிப்பு வினையாலணையும் பெயர்` / `பண்பு` plural nouns like `பல, சில`), in both `அல்வழி` and `வேற்றுமை` (`பல கொடுத்தான்`, `பல குதிரை`).
6. **R167.6 (`அம்ம` Particle)**: `first == அம்ம` (`உரையசை இடைச்சொல்`, e.g., `அம்ம கொற்றா`).

### Interactions & Precedence
- **Overrides Sutra 165** (`கசதப மிகும்`) for all 6 `அ`-final categories.
- **Linked to Sutra 168**: `வாழிய` retains naturalness even after losing `ய` (`வாழி`).
- **Linked to Sutra 170**: `பல, சில` are blocked from doubling here, EXCEPT in `பலப்பல, சிலச்சில` (Sutra 170).
- Note Viruttiyurai pno=236: `பல` has 6 distinct grammatical roles (`பெயரெச்சக் குறிப்பு`, `குறிப்பு வினைமுற்று`, `குறிப்புமுற்று பெயரெச்சம்`, `குறிப்புமுற்று வினையெச்சம்`, `குறிப்பு வினையாலணையும் அஃறிணைப் பன்மைப்பெயர்`, `பண்பு அஃறிணைப் பன்மைப்பெயர்`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| உண்ணிய | கொண்டான் / சென்றான் / தந்தான் / போயினான் | உண்ணிய கொண்டான் | `செய்யிய` வினையெச்சம் | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| உண்ட / உண்ணாநின்ற / உண்ணாத | குதிரை / செந்நாய் / தகர் / பன்றி | உண்ட குதிரை | `தெரிநிலைப் பெயரெச்சம்` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| கடுங்கண்ண / சிறிய / பெரிய / உள / இல / பல / சில | குதிரை | கடுங்கண்ண குதிரை / சிறிய குதிரை | `குறிப்புப் பெயரெச்சம்` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| பொன்னன்ன / கடிய | குதிரை | பொன்னன்ன குதிரை / கடிய குதிரை | `குறிப்புப் பெயரெச்சம்` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| உண்டன | குதிரை / செந்நாய் | உண்டன குதிரை / உண்டன செந்நாய் | `தெரிநிலை வினைமுற்று` | natural | `kandigai=167` |
| வாழ்க / வாழிய | கொற்றா / சாத்தா / தேவா / பூதா | வாழ்க கொற்றா / வாழிய கொற்றா | `வியங்கோள் முற்று` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| உண்ட | கண்டன | உண்ட கண்டன | `வினைமுற்று` as `வினையெச்சம்` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| அமர்முகத்த | குதிரை / கலக்கின | அமர்முகத்த குதிரை / அமர்முகத்த கலக்கின | `குறிப்புமுற்று` as `ஈரெச்சம்` | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| தன | கைகள் / செவிகள் / தாள்கள் / பதங்கள் | தன கைகள் | `ஆறன் உருபு` (`அ`) | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| பல | குதிரை / செந்நாய் / தகர் / பன்றி | பல குதிரை | `அஃறிணைப் பன்மை` (`அல்வழி`) | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| பல | கொடுத்தான் / செய்தான் / தந்தான் / படைத்தான் | பல கொடுத்தான் | `அஃறிணைப் பன்மை` (`வேற்றுமை` obj) | natural | `viruttiyurai_pno=235`, `kandigai=167` |
| அம்ம | கொற்றா / சாத்தா / தேவா / பூதா | அம்ம கொற்றா | `அம்ம` இடைச்சொல் | natural | `viruttiyurai_pno=235..236`, `kandigai=167` |

### Surface Signature & Reversibility
- **Signature**: No `க், ச், த், ப்` insertion after `அ`-final words in these 6 classes.
- **Reversibility**: Requires POS/morphological tags (`Viyankol`, `Peyareccam`, `Seyyiya`, `AfranUrubu`, `AhrinaiPanmai`, `Amma`) to block doubling.

---

## Sutra 168

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception | **Executable:** Rule (Optional Truncation + Deterministic Non-Doubling) | **Viruttiyurai pno:** 236 | **Kandigai:** 168 | **Poetic:** No

### Root Text (TVA 1999)
> வாழிய வென்பத னீற்றி னுயிர்மெய்  
> ஏகலு முரித்தஃ தேகினு மியல்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`வாழிய என்பதன் ஈற்றின் உயிர்மெய் / ஏகல் உம் உரித்து அஃது ஏகின் உம் இயல்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R168.1 (`வாழிய` Final `ய` Truncation)**: `IF` `first == வாழிய` (specifically the `வியங்கோள் முற்று`, NOT the `செய்யிய` `வினையெச்சம்`) `THEN` its final CV `ய` may optionally elide (`கடைக்குறை`), yielding **`வாழி`** (even at utterance/verse end, e.g., `ஆ வாழி`).
2. **R168.2 (Preserved Naturalness of `வாழி`)**: `IF` `வாழிய` has truncated to `வாழி` (`இ`-final) AND `second` begins with `க, ச, த, ப` `THEN` `வல்லினம்` does **NOT** double via Sutra 165; it remains **natural** (`இயல்பு`, preserving Sutra 167's rule).

### Interactions & Precedence
- **Overrides Sutra 165** (`விதியீறு` `இ`-final doubling) for derived `வாழி`.
- **Preserves Sutra 167** (`வாழிய` non-doubling).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| ஆ | வாழிய | ஆ வாழி | `வியங்கோள்` (utterance final) | `வாழிய -> வாழி` (drop `ய`) | `viruttiyurai_pno=236`, `kandigai=168` |
| அந்தணர் | வாழிய | அந்தணர் வாழி | `வியங்கோள்` | `வாழிய -> வாழி` | `viruttiyurai_pno=236`, `kandigai=168` |
| படாதி | வாழிய | படாதி வாழி | `வியங்கோள்` (verse) | `வாழிய -> வாழி` | `viruttiyurai_pno=236` |
| வாழி (< வாழிய) | கொற்றா / சாத்தா / தேவா / பூதா | வாழி கொற்றா / வாழி சாத்தா | `வியங்கோள்` + `வல்லினம்` | `வாழிய -> வாழி`, natural | `viruttiyurai_pno=236`, `kandigai=168` |

### Surface Signature & Reversibility
- **Signature**: `வாழி + [கசதப]` without doubling.
- **Reversibility**: Map `வாழி` <-> `வாழிய` (`Viyankol`).

---

## Sutra 169

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception | **Executable:** Rule (Optional / Rare) | **Viruttiyurai pno:** 237 | **Kandigai:** 169 | **Poetic:** No

### Root Text (TVA 1999)
> சாவவென் மொழியீற் றுயிர்மெய் சாதலும்விதி.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`சாவ என் மொழி ஈற்று உயிர்மெய் சாதல் உம் விதி`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R169.1 (`சாவ` Optional Final `வ` Elision)**: `IF` `first == சாவ` (`செயவென் எச்சம்` adverbial participle of `சா`) `THEN` in addition to the standard form (`சாவக் குத்தினான்` via Sutra 165), its final CV **`வ`** may optionally/rarely elide (`சாதல்`), leaving `சா`, before `second` (with `வல்லினம்` doubling via Sutra 165: `சாக் குத்தினான்`).

### Interactions & Precedence
- **Feeds Sutra 165**: After `சாவ -> சா`, `சா` is an `ஆ`-final `விதியீறு` that takes `க்` doubling (`சாக் குத்தினான்`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| சாவ | குத்தினான் | சாக் குத்தினான் | `செயவென் எச்சம்` (rare/optional vs `சாவக் குத்தினான்`) | drop `வ` + `க்` insertion (165) | `viruttiyurai_pno=237`, `kandigai=169` |
| சாவ | குத்தினான் | சாவக் குத்தினான் | `செயவென் எச்சம்` (standard) | `க்` insertion (165) | `viruttiyurai_pno=237`, `kandigai=169` |

### Surface Signature & Reversibility
- **Signature**: `சாக் குத்தினான்` alongside `சாவக் குத்தினான்`.
- **Reversibility**: `சா` (before `க்+V`) <-> `சாவ`.

---

## Sutra 170

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception | **Executable:** Rule (Multi-variant / Vikalpam) | **Viruttiyurai pno:** 237, 238 | **Kandigai:** 170 | **Poetic:** No

### Root Text (TVA 1999)
> பலசில வெனுமிவை தம்முன் றாம்வரின்  
> இயல்பு மிகலு மகர மேக  
> லகரம் றகர மாகலும் பிறவரின்  
> அகரம் விகற்ப மாகலு முளபிற.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`பல சில எனும் இவை தம் முன் தாம் வரின் / இயல்பு உம் மிகல் உம் அகரம் ஏக / லகரம் றகரம் ஆகல் உம் பிற வரின் / அகரம் விகற்பம் ஆகல் உம் உள பிற`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
All sub-rules apply in `அல்வழி` (per Viruttiyurai pno=238):
1. **R170.1 (Self-Compounding `பல+பல`, `சில+சில` — 3+ Variants)**: `IF` `first in {பல, சில}` AND `second == first` (`தம்முன் தாம் வரின்`) `THEN` 3 primary outcomes (plus 1 rare outcome via `பிற`):
   - `(a)` **Natural** (`இயல்பு`, preserving Sutra 167): `பலபல`, `சிலசில`
   - `(b)` **Hard Consonant Doubling** (`மிகல்`, overriding Sutra 167): `பலப்பல`, `சிலச்சில`
   - `(c)` **Final `அ` Elision + `ல் -> ற்`** (`அகரம் ஏக லகரம் றகரம் ஆகல்`): `பற்பல`, `சிற்சில`
   - `(d)` **Rare `அ` Elision without `ல் -> ற்`** (via `பிற`): `பல்பல`, `சில்சில`.
2. **R170.2 (Before Other Words `பிறவரின்` — Optional `அ` Elision)**: `IF` `first in {பல, சில}` AND `second != first` `THEN` final `அ` optionally stays or elides (`அகரம் விகற்பம்`):
   - If `அ` **stays**: `இயல்பு` per Sutra 167 before consonants (`பல கலை`, `பல படை`), or `வ்` *udambadumei* per Sutra 162 before vowels (`பல + அணி -> பலவணி`, `பல + ஆயம் -> பலவாயம்`).
   - If `அ` **elides** (`பல்`, `சில்`): subsequent sandhi follows `லகர மெய்யீற்றுப் புணர்ச்சி` (`ல்` rules):
     - Before `க, ச, ப`: `ல்` stays (`பல்கலை`, `பல்சாலை`, `பல்படை`), or optionally mutates to `ற்` where applicable (though `பிற` also notes occasional non-mutation).
     - Before `த`: `ல் + த -> ஃற` (`பல + தாழிசை -> பஃறாழிசை`).
     - Before `ஞ, ந, ம`: `ல் -> ன்` (`பல + ஞானம் -> பன்ஞானம்`, `பல + நாள் -> பன்னாள்`, `பல + மணி -> பன்மணி`).
     - Before `வ, ய`: `ல்` stays (`பல்வளை`, `பல்யானை` / `பல்யாழ்`).
     - Before vowels: `ல்` doubles (`தனிக்குறில்` Sutra 205) + vowel attaches (`பல + அணி -> பல்லணி`, `பல + ஆயம் -> பல்லாயம்`).

### Interactions & Precedence
- **Overrides Sutra 167** for `பலப்பல`, `சிலச்சில`, and `அ`-elided `பல்`/`சில்` forms.
- **Chains with `லகர ஈற்றுப் புணர்ச்சி`** (Sutras 227–230) and **Sutra 205** (`பல் + அணி -> பல்லணி`) when `அ` elides.

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| பல / சில | பல / சில | பலபல / சிலசில | `அல்வழி` (natural) | natural | `viruttiyurai_pno=237`, `kandigai=170` |
| பல / சில | பல / சில | பலப்பல / சிலச்சில | `அல்வழி` (doubled) | `ப்` / `ச்` insertion | `viruttiyurai_pno=237`, `kandigai=170` |
| பல / சில | பல / சில | பற்பல / சிற்சில | `அல்வழி` (`அ` drop + `ல்->ற்`) | `அ` elision + `ல் -> ற்` | `viruttiyurai_pno=237`, `kandigai=170` |
| பல / சில | பல / சில | பல்பல / சில்சில | `அல்வழி` (rare, via `பிற`) | `அ` elision only | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | கலை | பலகலை / பல்கலை | `அல்வழி` (`அ` retention / elision) | natural / `அ` elision | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | சாலை | பலசாலை / பல்சாலை | `அல்வழி` | natural / `அ` elision | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | தாழிசை | பலதாழிசை / பஃறாழிசை | `அல்வழி` | natural / `அ` elision + `ல்+த் -> ஃற` | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | படை | பலபடை / பல்படை | `அல்வழி` | natural / `அ` elision | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | ஞானம் | பலஞானம் / பன்ஞானம் | `அல்வழி` | natural / `அ` elision + `ல் -> ன்` | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | நாள் | பலநாள் / பன்னாள் | `அல்வழி` | natural / `அ` elision + `ல் -> ன்` | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | மணி | பலமணி / பன்மணி | `அல்வழி` | natural / `அ` elision + `ல் -> ன்` | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | வளை | பலவளை / பல்வளை | `அல்வழி` | natural / `அ` elision | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | யானை / யாழ் | பலயானை / பல்யானை / பலயாழ் / பல்யாழ் | `அல்வழி` | natural / `அ` elision | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | அணி | பலவணி / பல்லணி | `அல்வழி` | `வ்` glide / `அ` elision + `ல்` gemination | `viruttiyurai_pno=238`, `kandigai=170` |
| பல | ஆயம் | பலவாயம் / பல்லாயம் | `அல்வழி` | `வ்` glide / `அ` elision + `ல்` gemination | `viruttiyurai_pno=238`, `kandigai=170` |

### Surface Signature & Reversibility
- **Signature**: `{பல, பலப், பற், பல், பன், பஃ}` / `{சில, சிலச், சிற், சில், சின், சிஃ}` prefixes.
- **Reversibility**: Multi-variant stem normalization mapping `{பல், பற், பன், பஃ}` -> `பல` and `{சில், சிற், சின், சிஃ}` -> `சில`.

---

## Sutra 171

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`ஆகாரவீற்றுச் சிறப்புவிதி`) | **Executable:** Rule (Deterministic) | **Viruttiyurai pno:** 238, 239 | **Kandigai:** 171 | **Poetic:** No

### Root Text (TVA 1999)
> அல்வழி யாமா மியாமுற்று முன்மிகா.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`அல்வழி ஆ மா மியா முற்று முன் மிகா`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
`IF` `context == Alvazhi` AND `second` begins with `க, ச, த, ப` AND `first` is any of the following `ஆ`-final items `THEN` `வல்லினம்` does **NOT** double (`மிகா`, natural):
1. **R171.1 (`ஆ` and `மா` Nouns + `ஆமா`)**: `first in {ஆ (cow), மா (animal/horse/etc.), ஆமா (wild cow, via இரட்டுற மொழிதல்)}`. *(In `வேற்றுமை`, they double per Sutra 165, or `மா` tree takes nasal per Sutra 166.)*
2. **R171.2 (`மியா` Expletive Particle)**: `first` ends in `மியா` (`முன்னிலையசை இடைச்சொல்`, e.g., `கேண்மியா`).
3. **R171.3 (`ஆ`-Final Non-Rational Plural Negative Finite Verbs + Derived Forms)**: `first` is an `ஆ`-final `அஃறிணைப் பன்மை எதிர்மறை முற்றுவினை` (e.g., `உண்ணா`, `தின்னா`), OR (by `அருத்தாபத்தி`) its derived `வினையாலணையும் பெயர்` / `வினையெச்சமாகிய வினைமுற்று` (`உண்ணா கிடந்தன`).
   - *Contrast*: If `உண்ணா` is a `தகர ஈறு குறைந்த எதிர்மறைப் பெயரெச்சம்` (`உண்ணாத -> உண்ணா`) or `செய்யா` positive/negative `வினையெச்சம்`, it **DOES** double via Sutra 165 (`உண்ணாக் குதிரைகள்`, `உண்ணாக் கிடந்தன`).

### Interactions & Precedence
- **Overrides Sutra 165** (`கசதப மிகும்`) in `அல்வழி` for `{ஆ, மா, ஆமா, *மியா, ஆ-negative-plural-finite-verb}`.
- Requires morphological disambiguation on `உண்ணா` (finite negative plural vs truncated negative participle vs `செய்யா` adverbial participle) and semantic/POS disambiguation on `மா` (animal vs tree).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| ஆ | குறிது / சிறிது / தீது / பெரிது | ஆ குறிது | `அல்வழி` (`ஆ`) | natural | `viruttiyurai_pno=238`, `kandigai=171` |
| மா | குறிது / சிறிது / தீது / பெரிது | மா குறிது | `அல்வழி` (`மா` = animal) | natural | `viruttiyurai_pno=238`, `kandigai=171` |
| ஆமா | குறிது / சிறிது / தீது / பெரிது | ஆமா குறிது | `அல்வழி` (`ஆமா` = wild cow) | natural | `viruttiyurai_pno=239`, `kandigai=171` |
| கேண்மியா | கொற்றா / சாத்தா / தேவா / பூதா | கேண்மியா கொற்றா | `அல்வழி` (`மியா` particle) | natural | `viruttiyurai_pno=238`, `kandigai=171` |
| உண்ணா / தின்னா | குதிரைகள் / செந்நாய்கள் / தகர்கள் / பன்றிகள் | உண்ணா குதிரைகள் | `அல்வழி` (`எதிர்மறை முற்று`) | natural | `viruttiyurai_pno=238`, `kandigai=171` |
| உண்ணா / தின்னா | கிடந்தன / சென்றன / தந்தன / போயின | உண்ணா கிடந்தன | `அல்வழி` (`வினையாலணையும் பெயர்` / `வினைமுற்று வினையெச்சம்`) | natural | `viruttiyurai_pno=239`, `kandigai=171` |
| உண்ணா *(contrast)* | குதிரைகள் / கிடந்தன | உண்ணாக் குதிரைகள் / உண்ணாக் கிடந்தன | `அல்வழி` (`பெயரெச்சம்` / `செய்யா வினையெச்சம்`) | `க்` insertion (Sutra 165) | `viruttiyurai_pno=239`, `kandigai=171` |

### Surface Signature & Reversibility
- **Signature**: Absence of `க், ச், த், ப்` after `ஆ, மா, ஆமா, *மியா, *ஆ (neg.pl)` in `அல்வழி`.
- **Reversibility**: Disambiguates `உண்ணா + குதிரைகள்` (finite verb) vs `உண்ணாக் குதிரைகள்` (participle).

---

## Sutra 172

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Poetic (`ஆகாரவீற்றுச் சிறப்புவிதி`) | **Executable:** Poetic-only (with prose subset) | **Viruttiyurai pno:** 239 | **Kandigai:** 172 | **Poetic:** Yes (prose subset noted)

### Root Text (TVA 1999)
> குறியதன் கீழாக் குறுகலு மதனோ  
> டுகர மேற்றலு மியல்புமாந் தூக்கின்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`குறியதன் கீழ் ஆ குறுகல் உம் அதன் ஓடு / உகரம் ஏற்றல் உம் இயல்பு உம் ஆம் தூக்கின்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
`IF` `first` is a noun ending in **`ஆ`** preceded by a **short syllable (`குறியதன் கீழ்`, CVCV-type `நிலா, சுறா, இறா, கனா, இரா`)** `THEN`:
1. **R172.1 (Poetic 3-Way Realization `தூக்கின்`)**: `IF` `poetic == true` `THEN` 3 forms are valid (independent of sandhi context):
   - `(a)` **Shortening (`ஆ -> அ`)**: `நிலா -> நில`, `சுறா -> சுற` (`நிலவிரி`, `சுறமறிவன`).
   - `(b)` **Shortening + `உ` Augmentation (`ஆ -> அ + வ் + உ = அவு`)**: `நிலா -> நிலவு`, `சுறா -> சுறவு`, `இறா -> இறவு` (`மருவினென் செய்யுமோ நிலவு`, `சுறவுக்கோட்டன்ன`, `இறவுப்புறத்தன்ன`).
   - `(c)` **Retention (`இயல்பு`)**: `நிலா`, `இரா` (`நிலாவணங்கு`, `நெடிய கழியும் இரா`).
2. **R172.2 (Prose Usage `வழக்கில்`)**: `IF` `poetic == false` `THEN` either 2 forms (`அவு`-form + `ஆ`-form, e.g., `நிலவு / நிலா`, `கனவு / கனா`) or 1 form (`ஆ`-form only, e.g., `தரா`, `மிடா`) are valid; bare shortened `அ`-form (`நில`, `சுற`) is poetic-only.

### Interactions & Precedence
- Stem-level alternation (not caused by `அல்வழி`/`வேற்றுமை` sandhi, explicitly clarified in commentary).
- Feeds downstream sandhi according to the realized ending (`அ`, `உ` mutriyalugaram, or `ஆ`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| சுறா | மறிவன | சுறமறிவன | `poetic` (`ஆ -> அ`) | `ஆ -> அ` | `viruttiyurai_pno=239` |
| நிலா | விரி | நிலவிரி | `poetic` (`ஆ -> அ`) | `ஆ -> அ` | `viruttiyurai_pno=239`, `kandigai=172` |
| இறா | புறத்தன்ன | இறவுப்புறத்தன்ன | `poetic` (`ஆ -> அவு`) | `ஆ -> அ + வ் + உ` | `viruttiyurai_pno=239` |
| சுறா | கோட்டன்ன | சுறவுக்கோட்டன்ன | `poetic` (`ஆ -> அவு`) | `ஆ -> அ + வ் + உ` | `viruttiyurai_pno=239` |
| நிலா | *(verse)* | நிலவு | `poetic` & prose (`ஆ -> அவு`) | `ஆ -> அ + வ் + உ` | `viruttiyurai_pno=239`, `kandigai=172` |
| நிலா | வணங்கு | நிலாவணங்கு | `poetic` (`இயல்பு`) | natural + `வ்` glide | `viruttiyurai_pno=239`, `kandigai=172` |
| இரா | *(verse)* | இரா | `poetic` (`இயல்பு`) | natural | `viruttiyurai_pno=239` |
| கனா | *(prose)* | கனவு / கனா | prose (2 forms) | `ஆ -> அ + வ் + உ` / natural | `viruttiyurai_pno=239`, `kandigai=172` |
| தரா / மிடா | *(prose)* | தரா / மிடா | prose (1 form) | natural | `viruttiyurai_pno=239`, `kandigai=172` |

### Surface Signature & Reversibility
- **Signature**: Stem alternation `(C)V C ஆ` <-> `(C)V C அவு` <-> `(C)V C அ` (poetic).
- **Reversibility**: Lexicon alias mapping (`நிலா <-> நிலவு <-> நில`, `சுறா <-> சுறவு <-> சுற`, `இறா <-> இறவு`, `கனா <-> கனவு`).

---

## Sutra 173

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Poetic (`இகரவீற்றுச் சிறப்புவிதி`) | **Executable:** Poetic-only (Conditional) | **Viruttiyurai pno:** 240, 241 | **Kandigai:** 173 | **Poetic:** Yes

### Root Text (TVA 1999)
> அன்றி யின்றியென் வினையெஞ் சிகரந்  
> தொடர்பினு ளுகர மாய்வரி னியல்பே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`அன்றி இன்றி என் வினையெஞ்சு இகரம் / தொடர்பின் உள் உகரம் ஆய் வரின் இயல்பு ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R173.1 (`அன்றி/இன்றி` -> `அன்று/இன்று` in Verse + Non-Doubling)**: `IF` `poetic == true` (`தொடர்பினுள்` = செய்யுளில்) AND `first in {அன்றி, இன்றி}` (`குறிப்பு வினையெச்சம்`) AND its final **`இ`** optionally mutates to **`உ`** (`அன்று`, `இன்று`) AND `second` begins with `க, ச, த, ப` `THEN` `வல்லினம்` does **NOT** double via Sutra 165; it remains **natural** (`இயல்பு`).
2. **R173.2 (Unmutated `அன்றி/இன்றி` Retention)**: `IF` `இ` does NOT mutate to `உ` `THEN` Sutra 165 applies normally (`வாளன்றிப் பிடியா`, `விண்ணின்றிப் பொய்ப்பின்`, `பொருளன்றிக் காணார்`).

### Interactions & Precedence
- **Overrides Sutra 165** (`கசதப மிகும்`) when `அன்றி/இன்றி` surfaces as `அன்று/இன்று` in verse.
- **Note**: `அன்று/இன்று` here is a `குற்றியலுகரம்`-like poetic form of `அன்றி/இன்றி` (distinct from `அன்று` finite verb).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| அன்றி | போகி | (நாள)ன்று போகி | `poetic` (`அன்றி -> அன்று`) | `இ -> உ`, natural | `viruttiyurai_pno=240` |
| அன்றி | புக்கு | (பதன)ன்று புக்கு | `poetic` (`அன்றி -> அன்று`) | `இ -> உ`, natural | `viruttiyurai_pno=240` |
| அன்றி | பிடியா | வாளன்று பிடியா | `poetic` (`அன்றி -> அன்று`) | `இ -> உ`, natural | `kandigai=173` |
| இன்றி | பொய்ப்பின் | விண்ணின்று பொய்ப்பின் | `poetic` (`இன்றி -> இன்று`) | `இ -> உ`, natural | `kandigai=173` |
| இன்றி | புற்கை | உப்பின்று புற்கை | `poetic` (`இன்றி -> இன்று`) | `இ -> உ`, natural | `viruttiyurai_pno=241` |
| அன்றி / இன்றி *(contrast)* | பிடியா / பொய்ப்பின் | வாளன்றிப் பிடியா / விண்ணின்றிப் பொய்ப்பின் | unmutated (`இ`-final) | `ப்` insertion (Sutra 165) | `kandigai=173` |

### Surface Signature & Reversibility
- **Signature**: `அன்று / இன்று` + `[கசதப]` without doubling in verse.
- **Reversibility**: Map poetic `அன்று / இன்று` (adverbial negative context) <-> `அன்றி / இன்றி`.

---

## Sutra 174

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception (`இகரவீற்றுச் சிறப்புவிதி`) | **Executable:** Rule (Deterministic + Lexical-conditioned) | **Viruttiyurai pno:** 241 | **Kandigai:** 174 | **Poetic:** No

### Root Text (TVA 1999)
> உரிவரி னாழியி னீற்றுயிர் மெய்கெட  
> மருவும் டகர முரியின் வழியே  
> யகரவுயிர் மெய்யா மேற்பன வரினே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`உரி வரின் நாழியின் ஈற்று உயிர்மெய் கெட / மருவும் டகரம் உரியின் வழி ஏ / யகர உயிர்மெய் ஆம் ஏற்பன வரின் ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R174.1 (`நாழி + உரி -> நாடுரி`)**: `IF` `first == நாழி` (measure) AND `second == உரி` (measure) `THEN` delete `நாழி`'s final CV `ழி` (`ஈற்று உயிர்மெய் கெட`), insert **`ட்`** (`மருவும் டகரம்`), and attach `உ` of `உரி` onto `ட்` -> **`நாடுரி`**. *(Strictly blocks `*நாழியுரி` via Sutra 162; Viruttiyurai notes colloquial `நாவுரி` as later `மரூஉ`.)*
2. **R174.2 (`உரி` + Eligible Commodity -> `உரிய` + Commodity)**: `IF` `first == உரி` (measure) AND `second` is an **eligible commodity/measured noun (`ஏற்பன வரின்`)** (whether vowel-initial like `உப்பு`, or consonant-initial like `பயிறு`/`பயறு`, `மிளகு`, `வரகு`, `நெய்`) `THEN` insert **`ய`** (`யகர உயிர்மெய்`) after `உரி` -> **`உரிய`**, and join `second` naturally (no `வல்லினம்` doubling, e.g., `உரியபயிறு`, not `*உரியப்பயிறு`, and before vowel `உப்பு`, `உரியவுப்பு` via `வ்` *udambadumei* from `ய` -> `உரிய + உப்பு` or direct `ய`+`வ்`).
3. **R174.3 (`உரி` + Ineligible Word -> Default Sutra 162)**: `IF` `first == உரி` AND `second` is **ineligible (`ஏலாதன`)** (e.g., `அரிசி`, `ஆழாக்கு`, `எண்ணெய்`) `THEN` R174.2 does NOT apply; fall back to Sutra 162 (`ய்` *udambadumei* -> `உரியரிசி`, `உரியாழாக்கு`, `உரியெண்ணெய்`).

### Interactions & Precedence
- **Overrides Sutra 162** (`உடம்படுமெய்` `ய்`) for `நாழி + உரி -> நாடுரி`.
- **Overrides Sutra 165** (`கசதப மிகும்`) for `உரிய + பயிறு -> உரியபயிறு`.
- Requires a lexical eligibility list (`ஏற்பன`) on `உரி` (measured items like `உப்பு, பயிறு/பயறு, மிளகு, வரகு, நெய்` vs `அரிசி, ஆழாக்கு, எண்ணெய்`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| நாழி | உரி | நாடுரி | measure (`நாழி + உரி`) | drop `ழி` + insert `ட்` | `viruttiyurai_pno=241`, `kandigai=174` |
| உரி | உப்பு | உரியவுப்பு | measure (`ஏற்பன`) | insert `ய` + `வ்` glide | `viruttiyurai_pno=241`, `kandigai=174` |
| உரி | பயிறு / பயறு | உரியபயிறு / உரியபயறு | measure (`ஏற்பன`) | insert `ய`, natural | `viruttiyurai_pno=241`, `kandigai=174` |
| உரி | மிளகு / வரகு | உரியமிளகு / உரியவரகு | measure (`ஏற்பன`) | insert `ய`, natural | `viruttiyurai_pno=241`, `kandigai=174` |
| உரி | நெய் | உரியநெய் | measure (`ஏற்பன`) | insert `ய`, natural | `viruttiyurai_pno=222` (Sutra 154) |
| உரி | அரிசி / ஆழாக்கு / எண்ணெய் | உரியரிசி / உரியாழாக்கு / உரியெண்ணெய் | measure (`ஏலாதன`, fallback 162) | `ய்` udambadumei (162) | `viruttiyurai_pno=241`, `kandigai=174` |

### Surface Signature & Reversibility
- **Signature**: `நாடுரி`; `உரிய` + `[உப்பு|பயிறு|மிளகு|வரகு|நெய்]`.
- **Reversibility**: `நாடுரி` <-> `(நாழி, உரி)`; `உரிய` (in measure context) <-> `உரி`.

---

## Sutra 175

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception (`இகரவீற்றுச் சிறப்புவிதி`) | **Executable:** Rule (Optional / Semantic-conditioned) | **Viruttiyurai pno:** 241, 242 | **Kandigai:** 175 | **Poetic:** No

### Root Text (TVA 1999)
> சுவைப்புளி முன்னின மென்மையுந் தோன்றும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`சுவை புளி முன் இன மென்மை உம் தோன்றும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R175.1 (Taste-Sense `புளி` + `க, ச, த, ப` -> Optional Homorganic Nasal)**: `IF` `first == புளி` with semantic sense **`சுவை` (sour taste)** (NOT `மரம்` tree or `பழம்` fruit) AND `second` begins with `க, ச, த, ப` `THEN`:
   - `(a)` **Primary (`சிறப்புடைத்து`, via Sutra 165)**: Double `க, ச, த, ப` (`புளிக்கறி`, etc.).
   - `(b)` **Occasional (`ஒரோவழி`, via `மென்மையும்`)**: Insert the **homorganic nasal** (`ங், ஞ், ந், ம்`) in both `அல்வழி` (`புளிப்பாகிய கறி`) and `வேற்றுமை` (`புளிப்பை உடைய கறி`).

### Interactions & Precedence
- **Extends Sutra 165** with an optional homorganic-nasal variant for `சுவைப்புளி`.
- Requires word-sense disambiguation on `புளி` (`taste` vs `tree/fruit`).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| புளி (`சுவை`) | கறி | புளிக்கறி / புளிங்கறி | `அல்வழி` / `வேற்றுமை` (primary / rare) | `க்` insertion (165) / `ங்` insertion | `viruttiyurai_pno=242`, `kandigai=175` |
| புளி (`சுவை`) | சோறு | புளிஞ்சோறு | `அல்வழி` / `வேற்றுமை` (rare) | `ஞ்` insertion | `viruttiyurai_pno=242`, `kandigai=175` |
| புளி (`சுவை`) | தயிர் | புளிந்தயிர் | `அல்வழி` / `வேற்றுமை` (rare) | `ந்` insertion | `viruttiyurai_pno=242`, `kandigai=175` |
| புளி (`சுவை`) | பாளிதம் | புளிம்பாளிதம் | `அல்வழி` / `வேற்றுமை` (rare) | `ம்` insertion | `viruttiyurai_pno=242`, `kandigai=175` |

### Surface Signature & Reversibility
- **Signature**: `புளி[ங்ஞ்ந்ம்][கசதப]` alongside `புளி[க்ச்த்ப்][கசதப]`.
- **Reversibility**: Strip `{ங்,ஞ்,ந்,ம்}` or `{க்,ச்,த்,ப்}` after `புளி`.

---

## Sutra 176

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Special (`இகர ஐகார ஈற்றுச் சிறப்புவிதி`) | **Executable:** Rule (Context-conditioned + Vikalpam) | **Viruttiyurai pno:** 242, 243 | **Kandigai:** 176 | **Poetic:** No

### Root Text (TVA 1999)
> அல்வழி இஐம் முன்ன ராயின்  
> இயல்பு மிகலும் விகற்பமு மாகும்.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`அல்வழி இ ஐ முன்னர் ஆயின் / இயல்பு உம் மிகல் உம் விகற்பம் உம் ஆகும்`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
`IF` `first` is an **non-rational noun (`அஃறிணைப்பெயர்`)** ending in **`இ`** or **`ஐ`** AND `context == Alvazhi` AND `second` begins with `க, ச, த, ப` `THEN` 3 sub-behaviors partition `அல்வழி` subtypes (clarified in Viruttiyurai fn 177 / Sutra 254 & Kandigai 176):
1. **R176.1 (Natural `இயல்பு`)**: In `எழுவாய்த்தொடர்` (subject + predicate, e.g., `பருத்தி குறிது`, `யானை கரிது`) and `உம்மைத்தொகை` (`பரணிகார்த்திகை`, `யானைகுதிரை`), `வல்லினம்` remains **natural**.
2. **R176.2 (Doubling `மிகல்`)**: In `பண்புத்தொகை` (`மாசித்திங்கள்`, `ஆடித்திங்கள்`, `சாரைப்பாம்பு`) and `உவமைத்தொகை` (`காவிக்கண்`, `பனைக்கை`), `வல்லினம்` **doubles** (via Sutra 165).
3. **R176.3 (Optionality `விகற்பம்`)**: For specific `இ`/`ஐ`-final nouns in `எழுவாய்த்தொடர்` (e.g., `கிளி`, `தினை`), `வல்லினம்` optionally stays natural or doubles (`கிளி குறிது` / `கிளிக் குறிது`; `தினை குறிது` / `தினைக் குறிது`).

### Interactions & Precedence
- **Refines Sutra 165** (`கசதப மிகும்`) for `இ`/`ஐ`-final `அஃறிணை` nouns in `அல்வழி`.
- Demonstrates that `Alvazhi` cannot be a single boolean; subtype (`எழுவாய்`, `உம்மைத்தொகை`, `பண்புத்தொகை`, `உவமைத்தொகை`) determines whether `வல்லினம்` doubles or stays natural!

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| பருத்தி / ஒதி | குறிது / சிறிது / தீது / பெரிது | பருத்தி குறிது / ஒதி குறிது | `அல்வழி.எழுவாய்` | natural | `viruttiyurai_pno=243`, `kandigai=176` |
| யானை / குதிரை | கரிது / குறிது | யானை கரிது / குதிரை குறிது | `அல்வழி.எழுவாய்` | natural | `viruttiyurai_pno=243`, `kandigai=176` |
| பரணி | கார்த்திகை | பரணிகார்த்திகை | `அல்வழி.உம்மைத்தொகை` | natural | `kandigai=176` |
| யானை | குதிரை | யானைகுதிரை | `அல்வழி.உம்மைத்தொகை` | natural | `kandigai=176` |
| ஆடி / மாசி | திங்கள் | ஆடித்திங்கள் / மாசித்திங்கள் | `அல்வழி.பண்புத்தொகை` | `த்` insertion (165) | `viruttiyurai_pno=242 (fn.177)`, `kandigai=176` |
| சாரை | பாம்பு | சாரைப்பாம்பு | `அல்வழி.பண்புத்தொகை` | `ப்` insertion (165) | `kandigai=176` |
| காவி / பனை | கண் / கை | காவிக்கண் / பனைக்கை | `அல்வழி.உவமைத்தொகை` | `க்` insertion (165) | `kandigai=176` |
| கிளி | குறிது | கிளி குறிது / கிளிக் குறிது | `அல்வழி.எழுவாய்` (`விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=243`, `kandigai=176` |
| தினை | குறிது | தினை குறிது / தினைக் குறிது | `அல்வழி.எழுவாய்` (`விகற்பம்`) | optional `க்` insertion | `viruttiyurai_pno=243`, `kandigai=176` |

### Surface Signature & Reversibility
- **Signature**: Subtype-dependent presence/absence of `[க்ச்த்ப்]` after `{இ, ஐ}`-final `அஃறிணை` nouns in `அல்வழி`.
- **Reversibility**: Requires `Alvazhi` subtype tag to predict forward; inverse split handles both natural and doubled forms.

---

## Sutra 177

**Chapter:** உயிரீற்றுப் புணரியல் | **Tier:** Lexical / Exception (`ஈகாரவீற்றுச் சிறப்புவிதி`) | **Executable:** Rule (Deterministic) | **Viruttiyurai pno:** 243 | **Kandigai:** 177 | **Poetic:** No

### Root Text (TVA 1999)
> ஆமுன் பகரவீ யனைத்தும்வரக் குறுகும்  
> மேலன வல்வழி யியல்பா கும்மே.

**Edition Diff vs pmuni0147:** Sandhi-split formatting only (`ஆ முன் பகர ஈ அனைத்து உம் வர குறுகும் / மேலன அல்வழி இயல்பு ஆகும் ஏ`); no lexical variants.

### Atomic Sub-Rules (IF -> THEN)
1. **R177.1 (`ஆ + பீ -> ஆப்பி` Shortening before Any Following Word)**: `IF` `first` is the compound `ஆ + பீ` (euphemism `பகரவீ`, cow dung) followed by `second` starting with **any of the 4 classes** (`அனைத்தும் வர` = `வல்லினம்`, `மெல்லினம்`, `இடையினம்`, `உயிர்`) in either `அல்வழி` or `வேற்றுமை` `THEN` `பீ`'s final `ஈ` shortens to `இ` (`குறுகும்`), yielding **`ஆப்பி`** (with `ப்` doubling from `ஆ + பீ` per Sutra 165). *(If uncompounded or utterance-final without `second`, `ஈ` does not shorten via this rule.)*
2. **R177.2 (`ஆப்பி` in *Alvaḻi* -> Natural; in *Vēṟṟumai* -> Doubling)**: `IF` `ஆப்பி` (derived `விதியிகர ஈறு`) is followed by `second` starting with `க, ச, த, ப`:
   - `(a)` `IF` `context == Alvazhi` `THEN` `வல்லினம்` remains **natural** (`இயல்பு`, selecting the natural branch of Sutra 176 — e.g., `ஆப்பி குளிரும்`).
   - `(b)` `IF` `context == Vetrumai` `THEN` `வல்லினம்` **doubles** via Sutra 165 (`ஆப்பிக் குளிர்ச்சி`).
   - `(c)` `IF` `second` starts with a vowel `THEN` `ய்` *udambadumei* applies via Sutra 162 (`ஆப்பி + அரிது -> ஆப்பியரிது`, `ஆப்பி + அருமை -> ஆப்பியருமை`).

### Interactions & Precedence
- **Feeds Sutra 176 & 165**: Produces derived `இ`-final `ஆப்பி`, then selects `இயல்பு` from Sutra 176 in `அல்வழி` and `மிகல்` from Sutra 165 in `வேற்றுமை`.
- **Links to Sutra 178** (`பவ்வீ நீமீ முன்னர் அல்வழி`, Part B).

### Attested Examples
| First | Second | Surface | Context/Optionality | Transform | Witness |
|---|---|---|---|---|---|
| ஆப்பி (< ஆ+பீ) | அரிது / அருமை | ஆப்பியரிது / ஆப்பியருமை | `அல்வழி` / `வேற்றுமை` (+ vowel) | `பீ -> பி` + `ய்` glide (162) | `viruttiyurai_pno=243`, `kandigai=177` |
| ஆப்பி (< ஆ+பீ) | குளிரும் / நன்று / வலிது | ஆப்பி குளிரும் / ஆப்பி நன்று / ஆப்பி வலிது | `அல்வழி` (+ `வல்லினம்`/`மெல்லினம்`/`இடையினம்`) | `பீ -> பி`, natural | `viruttiyurai_pno=243`, `kandigai=177` |
| ஆப்பி (< ஆ+பீ) | குளிர்ச்சி | ஆப்பிக் குளிர்ச்சி | `வேற்றுமை` (+ `வல்லினம்`) | `பீ -> பி` + `க்` insertion (165) | `viruttiyurai_pno=243`, `kandigai=177` *(Kandigai prints `ஆப்பி குளிர்ச்சி`)* |
| ஆப்பி (< ஆ+பீ) | நன்மை / வன்மை | ஆப்பி நன்மை / ஆப்பி வன்மை | `வேற்றுமை` (+ `மெல்லினம்`/`இடையினம்`) | `பீ -> பி`, natural | `viruttiyurai_pno=243`, `kandigai=177` |

### Surface Signature & Reversibility
- **Signature**: `ஆப்பி` (with `க்,ச்,த்,ப்` in `வேற்றுமை`, natural in `அல்வழி`, `ய்` before vowels).
- **Reversibility**: `ஆப்பி` <-> `ஆ + பீ`.

---

## Batch Summary: Missing Rules, Edge Cases & Context Enums Needed (151–177)

### 1. Required Context Enums (from Sutra 152)
To implement Sutras 151–177 without conflating distinct sandhi behaviors, the `PunarchiContext` enum cannot be a flat `Alvazhi | Vetrumai` boolean:
- **`Vetrumai(CaseType, Realization)`**:
  - `CaseType`: `Second (ஐ)`, `Third (ஆல்)`, `Fourth (கு)`, `Fifth (இன்)`, `Sixth (அது)`, `Seventh (கண்)`
  - `Realization`: `Thogai (elided)`, `Viri (overt)`, `UrubumPayanumThokka (தழாத்தொடர்)`
- **`Alvazhi(AlvazhiSubtype)`**:
  - *Thogainilai (5)*: `Vinaitthogai`, `Panbuthogai` (incl. `Irupeyarottu`), `Uvamaitthogai`, `Ummaitthogai`, `Anmozhitthogai`
  - *Thogaanilai (9)*: `Ezhuvai`, `Vili`, `Peyareccam`, `Vinaiyeccam`, `TherilaiVinaiMutru`, `KurippuVinaiMutru`, `Idaichol`, `Urichol`, `Adukku`
  - *Cross-cutting flag*: `Thazhatthodar` (non-adjacent semantic head, e.g., `சுரையாழ`)

### 2. Required Lexical / Morphosyntactic Feature Flags
- **Animacy / Rationality (`திணை`)**: `Uyartinai`, `Ahrinai`, `Poduppeyar` (needed for 159 vs 165, 176).
- **POS & Subtype**: `Viyankol` (167, 168), `Munnaippinai` vs `Eval` (161), `SeyyiyaVinaiyeccam` (167), `AfranUrubu` (167), `AhrinaiPanmai` (167), `Kurriyalugaram` vs `Mutriyalugaram` (164), `InterrogativeClitic (ஆ, ஏ, ஓ)` & `Ya` (160), `DeicticClitic (அ, இ, உ)` & `InterrogativeClitic (எ)` (163).
- **Lexical Subclasses**:
  - `tree_nasal_inserting` (`விள/விளா, கள/களா, மா, காயா` — 166)
  - `taste_puli` vs `tree_puli` (`புளி` — 175)
  - `uri_eligible_commodity` (`உப்பு, பயிறு/பயறு, மிளகு, வரகு, நெய்` vs `அரிசி, ஆழாக்கு, எண்ணெய்` — 174)
  - `non_doubling_residual` (`ஏரி, குழந்தை, குழவி, மலை, கூப்பு, ஈட்டு, நாட்டு` — 165)
  - `alvazhi_i_ai_vikalpam` (`கிளி, தினை` — 176)
- **Mode Flags**: `poetic: bool` (gates 155, 156, 163.3, 172.1, 173), `include_rare_variants: bool` (gates 161 `விகற்பம்`, 164 `ஒரோவழி` `முற்றியலுகரம்`/`உடம்படுமெய்`, 169 `சாக் குத்தினான்`, 170 `பல்பல`, 175 `புளிங்கறி`).

### 3. Cross-Sutra Dependencies & Deferred Rules (Outside 151–177)
- **Sutra 93 & 94**: `குற்றியலிகரம்` and `குற்றியலுகரம்` classification (required by 164).
- **Sutra 201 (`இடைச்சொல் லேயோ`)**: `ஏ, ஓ` interrogative/particle handling (deferred from 160).
- **Sutra 204 (`உடன்மேல் உயிர்`)**: Vowel attachment onto `ய், வ்` glides and residual consonants (required by 153, 162, 163, 164, 174).
- **Sutra 205 (`தனிக்குறில் முன்னொற்று`)**: Gemination of `வ், ல்` after short-vowel monosyllables (`நொவ்வழகிது`, `அவ்வணி`, `பல்லணி` — required by 162, 163, 170).
- **Sutras 207–208, 227, 237**: `ண, ள, ன, ல` + `ந` mutation and `ல்`-final sandhi after `பல/சில -> பல்/சில்` (deferred from 158, 170).
- **Sutra 239 (`இடையுரி வடசொலின் இயம்பிய கொளாதவும்`)**: Explains `மாயிரு` exception to 162.

### 4. Subtle Edge Cases & Potential Engine Bugs Identified
1. **`விதியீறு` (Derived Vowel Finals) Pipeline**: Sutra 165 applies to derived vowel finals (`வட்ட, தாழ, ஒற்றை, ஆட்டு, சா`), EXCEPT where explicitly blocked (`வாழி` in 168, `ஆப்பி` in 177 `அல்வழி`). Engine must track `is_derived_final` + `origin_sutra` so 168/177 aren't clobbered by 165.
2. **`நொ` and `து` 3-Way Doubling**: Sutra 158 doubles `ஞ, ந, ம` (and `ய, வ` via `எச்சவும்மை`) after `நொ, து`, while Sutra 165 doubles `க, ச, த, ப` (overriding Sutra 161's optionality).
3. **`உண்ணா` 3-Way Ambiguity (171 vs 165)**: `உண்ணா குதிரைகள்` (negative plural finite verb, no doubling) vs `உண்ணாக் குதிரைகள்` (elided `உண்ணாத` negative adjectival participle, doubles).
4. **`பல / சில` Self vs Other & `பிற` Clause (170)**: Must emit all 4 self-forms (`பலபல`, `பலப்பல`, `பற்பல`, `பல்பல`) and both `அ`-retained and `அ`-elided forms before other words (`பலகலை` / `பல்கலை`, `பலவணி` / `பல்லணி`).
5. **`நாழி + உரி -> நாடுரி` (174)**: Must block Sutra 162 `*நாழியுரி` (`இலக்கணம் அன்று` per Viruttiyurai).
6. **`அன்றி / இன்றி` -> `அன்று / இன்று` (173)**: Only blocks doubling when `இ -> உ` has occurred in verse; unmutated `அன்றி / இன்றி` doubles via Sutra 165.
