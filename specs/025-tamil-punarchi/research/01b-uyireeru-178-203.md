# Nannūl Uyirīṟṟup Puṇariyal (Part B: Sutras 178–203) — Formal Rule Specification

**Source Edition**: TVA 1999 Critical Edition (Thamodaran / Viruttiyurai) cross-checked against Project Madurai 1926 Vavilla (`pmuni0147.html`) and Arumuka Navalar Kandigaiyurai.
**Scope**: Sutras 178–203 (26 sutras; concluding *Uyirīṟṟup Puṇariyal*).
**Conventions**:
- `S1` = *Nilaimozhi* (first word); `S2` = *Varumozhi* (second word).
- `V` = Vowel; `C` = Consonant; `K` = *Vallinam* (`க், ச், த், ப்` or all 6); `M` = *Mellinam*; `I` = *Idaiyinam*.
- Contexts: `Alvazhi` (non-case relation), `Vetrumai` (case relation: *Thogai* or *Viri*), `Both` (unrestricted).
- Witness tags: `viruttiyurai_pno=<N>` and/or `kandigai=<S>`.

---

## Sutra 178 — `ஈ`-Final Special Rules (`பீ, நீ, மீ`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Special | Executable: Yes (Lexical) | Viruttiyurai pno: 244, 245 | Kandigai: 178 | Poetic: No`
- **Root Text (TVA 1999)**:
  > பவ்வீ நீமீ முன்ன ரல்வழி
  > இயல்பாம் வலிமெலி மிகலுமா மீக்கே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ப ஈ` vs `பவ்வீ`; `மீ கு ஏ` vs `மீக்கே`); identical lexical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 ∈ {"பீ", "நீ", "மீ"} AND context == Alvazhi AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN allow Natural (இயல்பு) join (blocking default vallinam doubling of Sutra 165).`
  2. `IF S1 == "மீ" AND context == Alvazhi AND S2.initial ∈ {க், ச், த், ப்}` (lexicalized compounds)
     `THEN ALSO allow gemination of S2.initial (வலி மிகல்) OR insertion of homorganic nasal (மெலி மிகல்), i.e., 3-way lexicalized behavior depending on compound.`
     - Note: Viruttiyurai & Kandigai explain `மீகண்` as *ilakkanappoli* (`கண்ணினது மேலிடம்`, treated as *Alvazhi* with no doubling), `மீக்கூற்று` & `மீக்கோள்` as *panputhogai/vetrumaithogai-purattu-pirantha anmolithogai* (with *valli* doubling), and `மீந்தோல்` as *panputhogai* (with *meli* nasal insertion; noted as colloquial `பீந்தோல்`).
  3. `IF S1 == "நீ" AND context == Vetrumai`
     `THEN this sutra does NOT apply; S1 shortens to "நின்" (covered by Sutras 218, 247).`
- **Interactions & Precedence**:
  - Overrides Sutra 165 (*iyalpum vitiyum...*) for *Alvazhi* stops after `பீ, நீ, மீ`.
  - Explains why `நீ` is not covered by Sutra 159 (*pothuppeyar...*): Sutra 159 requires invariant vowel/`ய்`/`ர்` ending across both *Alvazhi* and *Vetrumai*, whereas `நீ` alternates with `நின்` in *Vetrumai*.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பீ | குறிது | பீ குறிது | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | பீ | சிறிது | பீ சிறிது | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | பீ | தீது | பீ தீது | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | பீ | பெரிது | பீ பெரிது | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | நீ | குறியை | நீ குறியை | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | நீ | சிறியை | நீ சிறியை | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | நீ | தீயை | நீ தீயை | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | நீ | பெரியை | நீ பெரியை | Alvazhi; Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | மீ | கண் | மீகண் | Alvazhi (Ilakkanappoli); Natural | Natural | `viruttiyurai_pno=244`, `kandigai=178` |
  | மீ | கூற்று | மீக்கூற்று | Alvazhi/Compound; Valli doubling | Insert `க்` | `viruttiyurai_pno=244`, `kandigai=178` |
  | மீ | கோள் | மீக்கோள் | Compound; Valli doubling | Insert `க்` | `viruttiyurai_pno=244`, `kandigai=178` |
  | மீ | தோல் | மீந்தோல் | Alvazhi (Panputhogai); Meli insertion | Insert `ந்` | `viruttiyurai_pno=244`, `kandigai=178` |
- **Surface Signature & Reversibility**:
  - `மீ[க்ச்த்ப்]C...` -> ambiguous between `மீ + C...` (Sutra 178) and general vowel-final doubling; `மீ[ங்ஞ்ந்ம்]C...` -> `மீ + C...` (homorganic nasal + stop).

---

## Sutra 179 — *Mutriyalugaram* (Full `உ`) Special Rules

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Syntactic | Executable: Yes (with POS/Class tags) | Viruttiyurai pno: 245 | Kandigai: 179 | Poetic: No`
- **Root Text (TVA 1999)**:
  > மூன்றா றுருபெண் வினைத்தொகை சுட்டீ
  > றாகு முகர முன்ன ரியல்பாம்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`மூன்று ஆறு உருபு எண் வினைத்தொகை சுட்டு ஈறு / ஆகும் உகரம் முன்னர் இயல்பு ஆம்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1.final == "உ" (Mutriyalugaram) AND S2.initial ∈ {க், ச், த், ப்} AND S1.class ∈ {Case3_Urubu (-ஒடு), Case6_Urubu (-அது), Numeral_Full_U (natural: ஏழு; modified: ஒரு, இரு, அறு, எழு), Vinaiththogai_VerbStem (அடு, தரு, புகு, தெறு, எழு, விரவு, ...), Demonstrative_Pronoun (அது, இது, உது)}`
     `THEN S2.initial stays Natural (இயல்பு) — no vallinam doubling (blocks Sutra 165).`
  2. `IF S1 == "உது" AND S2 == "காண்"` (exception noted in Viruttiyurai/Kandigai via Sutra 255)
     `THEN optional doubling: "உது காண்" OR "உதுக் காண்".`
- **Interactions & Precedence**:
  - Blocks Sutra 165 (*vallinam* doubling) for these 5 *Mutriyalugaram* classes in both *Alvazhi* and *Vetrumai* where applicable.
  - Interacts with Sutra 188–189 (`ஒரு, இரு, அறு, எழு` are *mutriyalugaram* modified forms of numerals).
  - Note: Viruttiyurai footnote 180 records that Koolangai Thambiran / Mayilainathar merge Sutras 179 and 180 into one sutra, whereas TVA 1999 & Kandigai keep them separate.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | சாத்தனொடு | கொண்டான் | சாத்தனொடு கொண்டான் | Case 3 (`-ஒடு`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனொடு | சென்றான் | சாத்தனொடு சென்றான் | Case 3 (`-ஒடு`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனொடு | தந்தான் | சாத்தனொடு தந்தான் | Case 3 (`-ஒடு`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனொடு | போயினான் | சாத்தனொடு போயினான் | Case 3 (`-ஒடு`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனது | கை | சாத்தனது கை | Case 6 (`-அது`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனது | செவி | சாத்தனது செவி | Case 6 (`-அது`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனது | தலை | சாத்தனது தலை | Case 6 (`-அது`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | சாத்தனது | புறம் | சாத்தனது புறம் | Case 6 (`-அது`); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | ஏழு | கை | ஏழு கை | Numeral (natural); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | ஒரு | கை | ஒரு கை | Numeral (modified); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | இரு | கை | இரு கை | Numeral (modified); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அறு | கை | அறு கை | Numeral (modified); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அடு | களிறு | அடுகளிறு | Vinaiththogai; Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அடு | சேனை | அடுசேனை | Vinaiththogai; Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அடு | தானை | அடுதானை | Vinaiththogai; Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அடு | படை | அடுபடை | Vinaiththogai; Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அது | குறிது | அது குறிது | Demonstrative (Alvazhi); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அது | கண்டான் | அது கண்டான் | Demonstrative (Vetrumai); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அது | செகுத்தான் | அது செகுத்தான் | Demonstrative (Vetrumai); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அது | தந்தான் | அது தந்தான் | Demonstrative (Vetrumai); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | அது | படைத்தான் | அது படைத்தான் | Demonstrative (Vetrumai); Natural | Natural | `viruttiyurai_pno=245`, `kandigai=179` |
  | உது | காண் | உது காண் / உதுக் காண் | Exception (Sutra 255); Optional | Natural / Insert `க்` | `viruttiyurai_pno=245`, `kandigai=179` |
- **Surface Signature & Reversibility**:
  - `...-ஒடு C...`, `...-அது C...`, `(ஒரு|இரு|அறு|எழு|ஏழு) C...`, `(அது|இது|உது) C...` -> unambiguous natural boundary.

---

## Sutra 180 — Poetic Lengthening of `அன்று` after `அது`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Poetic/Lexical | Executable: Yes (Poetic flag) | Viruttiyurai pno: 246 | Kandigai: 180 | Poetic: Yes (தூக்கின்)`
- **Root Text (TVA 1999)**:
  > அதுமுன் வருமன் றான்றாந் தூக்கின்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`அது முன் வரும் அன்று ஆன்று ஆம் தூக்கின்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == "அது" AND S2 == "அன்று" AND poetic == True`
     `THEN S1 drops final உ (or S1 + S2 elides) and S2.initial "அ" lengthens to "ஆ" -> "அதான்று" (Optional; does NOT block natural "அதுவன்று" or elided "அதன்று").`
  2. `IF S1 ∈ {"இது", "உது"} AND S2 == "அன்று"`
     `THEN lengthening to *ஆன்று does NOT apply (strictly restricted to "அது").`
- **Interactions & Precedence**:
  - Optional poetic rule alongside standard `உயிர்வரினுக்குறள்` / `முற்றுமற்றொரோவழி` (Sutra 164: `அதன்று`) and `இயல்பு` + glide `வ்` (Sutra 162: `அதுவன்று`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | அது | அன்று | அதான்று | Poetic (`தூக்கின்`); Optional | `உ` elision + `அ -> ஆ` | `viruttiyurai_pno=246`, `kandigai=180` |
  | அது | அன்று | அதுவன்று | Standard/Poetic; Optional | Glide `வ்` (Sutra 162) | `viruttiyurai_pno=246`, `kandigai=180` |
  | அது | அன்று | அதன்று | Standard/Poetic; Optional | `உ` elision (Sutra 164) | `viruttiyurai_pno=246`, `kandigai=180` |
- **Surface Signature & Reversibility**:
  - `அதான்று` -> uniquely decomposes to `அது + அன்று` (poetic).

---

## Sutra 181 — *Kurriyalugaram* in *Alvazhi* (Non-*Vanthodar* Classes)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Phonological/Morphosyntactic | Executable: Yes | Viruttiyurai pno: 246 | Kandigai: 181 | Poetic: No`
- **Root Text (TVA 1999)**:
  > வன்றொட ரல்லன முன்மிகா வல்வழி.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`வன் தொடர் அல்லன முன் மிகா அல்வழி`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1.ending_type == Kurriyalugaram AND S1.kurriyalugaram_class ∈ {Nedilthodar, Aaydathodar, Uyirthodar, Menthodar, Idaithodar} (i.e., ≠ Vanthodar) AND context == Alvazhi AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial does NOT double (Natural / இயல்பு).`
  2. **Kandigai Exception (Place *Idaichol* in *Menthodar*)**:
     `IF S1 ∈ {"அங்கு", "இங்கு", "உங்கு", "எங்கு", "ஆங்கு", "ஈங்கு", "ஊங்கு", "யாங்கு", "யாண்டு"} (7th-case locative particles) AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial DOUBLES (வல்லினம் மிகும்).`
  3. **Kandigai Clarification (Time *Idaichol* in *Menthodar*)**:
     `IF S1 ∈ {"அன்று", "இன்று", "என்று", "பண்டு", "முந்து"} (7th-case temporal particles) AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial remains Natural (இயல்பு).`
- **Interactions & Precedence**:
  - Restricts Sutra 165 (*vallinam* doubling) in *Alvazhi* for 5 of the 6 *Kurriyalugaram* classes (leaving *Vanthodar* to double in *Alvazhi*).
  - Exception 2 (locative particles) overrides the *Menthodar* naturalness rule.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | நாகு | கடிது | நாகு கடிது | Alvazhi (Nedilthodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | எஃகு | சிறிது | எஃகு சிறிது | Alvazhi (Aaydathodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` *(Kandigai prints `எஃது சிறிது`)* |
  | வரகு | தீது | வரகு தீது | Alvazhi (Uyirthodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | குரங்கு | பெரிது | குரங்கு பெரிது | Alvazhi (Menthodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | தெள்கு | கொடிது | தெள்கு கொடிது | Alvazhi (Idaithodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | ஏகு | கால் | ஏகுகால் | Alvazhi (Vinaiththogai, Nedil); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | அஃகு | பிணி | அஃகுபிணி | Alvazhi (Vinaiththogai, Aaydam); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | பொருது | சென்றான் | பொருது சென்றான் | Alvazhi (Vinaiecham, Uyir); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | அறிந்து | தந்தான் | அறிந்து தந்தான் | Alvazhi (Vinaiecham, Menthodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | எய்து | கொன்றான் | எய்து கொன்றான் | Alvazhi (Vinaiecham, Idaithodar); Natural | Natural | `viruttiyurai_pno=246`, `kandigai=181` |
  | அங்கு | கொண்டான் | அங்குக் கொண்டான் | Locative Menthodar particle; Doubling | Insert `க்` | `kandigai=181` |
  | இங்கு | கொண்டான் | இங்குக் கொண்டான் | Locative Menthodar particle; Doubling | Insert `க்` | `kandigai=181` |
  | யாண்டு | கொண்டான் | யாண்டுக் கொண்டான் | Locative Menthodar particle; Doubling | Insert `க்` | `kandigai=181` |
  | அன்று | கண்டான் | அன்று கண்டான் | Temporal Menthodar particle; Natural | Natural | `kandigai=181` |
  | இன்று | சென்றான் | இன்று சென்றான் | Temporal Menthodar particle; Natural | Natural | `kandigai=181` |
  | பண்டு | பெற்றான் | பண்டு பெற்றான் | Temporal Menthodar particle; Natural | Natural | `kandigai=181` |
- **Surface Signature & Reversibility**:
  - Clean natural boundary for non-*Vanthodar* *Kurriyalugaram* in *Alvazhi* (except locative particles `அங்கு..யாண்டு`).

---

## Sutra 182 — *Kurriyalugaram* in *Vetrumai* (No Doubling Classes)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Phonological/Morphosyntactic | Executable: Yes | Viruttiyurai pno: 246, 247 | Kandigai: 182 | Poetic: No`
- **Root Text (TVA 1999)**:
  > இடைத்தொட ராய்தத் தொடரொற் றிடையின்
  > மிகாநெடி லுயிர்த்தொடர் முன்மிகா வேற்றுமை.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`இடை தொடர் ஆய்த தொடர் ஒற்று இடையின் / மிகா நெடில் உயிர் தொடர் முன் மிகா வேற்றுமை`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1.kurriyalugaram_class ∈ {Idaithodar, Aaydathodar} AND context == Vetrumai AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial does NOT double (Natural).`
  2. `IF S1.kurriyalugaram_class ∈ {Nedilthodar, Uyirthodar} AND S1 does NOT undergo internal consonant doubling (ஒற்று இடையின் மிகா — i.e., not டு/று doubling of Sutra 183) AND context == Vetrumai AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial does NOT double (Natural).`
- **Interactions & Precedence**:
  - Paired directly with Sutra 183: if a *Nedilthodar* or *Uyirthodar* *Kurriyalugaram* DOES undergo `டு/று` doubling (Sutra 183), then *vallinam* DOES double after it in *Vetrumai* (e.g., `ஆட்டுக்கால்`, `வரகுகதிர்` vs `முருட்டுக்கால்`).
  - Note: *Vanthodar* and *Menthodar* in *Vetrumai* are outside this exemption (they double stops by Sutra 165, unless *Menthodar* converts per Sutra 184).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | தெள்கு | கால் | தெள்குகால் | Vetrumai (Idaithodar); Natural | Natural | `viruttiyurai_pno=247`, `kandigai=182` |
  | எஃகு | கடுமை | எஃகுகடுமை | Vetrumai (Aaydathodar); Natural | Natural | `viruttiyurai_pno=247`, `kandigai=182` |
  | நாகு | கால் | நாகுகால் | Vetrumai (Nedilthodar, no `ஒற்று` doubling); Natural | Natural | `viruttiyurai_pno=247`, `kandigai=182` |
  | வரகு | கதிர் | வரகுகதிர் | Vetrumai (Uyirthodar, no `ஒற்று` doubling); Natural | Natural | `viruttiyurai_pno=247`, `kandigai=182` |
- **Surface Signature & Reversibility**:
  - Non-doubled `S1 + S2` in *Vetrumai* when `S1` ends in `கு, சு, து, பு` (not `டு, று`) or is *Idai/Aayda* *Kurriyalugaram*.

---

## Sutra 183 — `டு / று` Doubling in *Nedil-thodar* & *Uyir-thodar* *Kurriyalugaram*

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Phonological/Morphosyntactic | Executable: Yes (with exceptions) | Viruttiyurai pno: 247, 248 | Kandigai: 183 | Poetic: No`
- **Root Text (TVA 1999)**:
  > நெடிலோ டுயிர்த்தொடர்க் குற்றுக ரங்களுட்
  > டறவொற் றிரட்டும் வேற்றுமை மிகவே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`நெடில் ஓடு உயிர் தொடர் குற்றுகரங்கள் உள் / ட ற ஒற்று இரட்டும் வேற்றுமை மிக ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Primary Rule (*Vetrumai*, all 4 *ganam*s — `க்/ச்/த்/ப்`, nasals, glides, vowels)**:
     `IF S1.kurriyalugaram_class ∈ {Nedilthodar, Uyirthodar} AND S1.final ∈ {"டு", "று"} AND context == Vetrumai`
     `THEN S1's penultimate-support consonant (ட் or ற்) DOUBLES (டு -> ட்டு, று -> ற்று) [mostly / பெரும்பாலும்].`
     - `IF S2.initial ∈ {க், ச், த், ப்}` -> `S2.initial` ALSO doubles (per Sutra 165 & Viruttiyurai pno=247, e.g., `ஆடு + கால் -> ஆட்டுக்கால்`, `ஆறு + கால் -> ஆற்றுக்கால்` / `பாறு + கால் -> பாற்றுக்கால்`).
     - `IF S2.initial ∈ Vowel` -> `உ` drops by Sutra 164 (`உயிர்வரினுக்குறள்`) and doubled `ட்ட்/ற்ற்` fuses with `S2.initial` (e.g., `ஆடு + அடி -> ஆட்டடி`, `களிறு + யானை -> களிற்றுயானை` [glide]).
  2. **Minority Non-Doubling in *Vetrumai*** (implied by `மிகவே` = "mostly"):
     `IF S1 ∈ lexical/poetic exceptions (e.g., "நாடு கிழவோன்", "காடு + அகம் -> காடகம்", "மிடறு + அணியல் -> மிடறணியல்")`
     `THEN ட்/ற் does NOT double even in Vetrumai.`
  3. **Minority Doubling in *Alvazhi*** (implied by `மிகவே`):
     `IF S1 + S2 ∈ attested Alvazhi compounds (e.g., "காடு + அரண் -> காட்டரண்", "களிறு + யானை -> களிற்றுயானை", "ஏறு + ஏனம் -> ஏற்றேனம்", "வரடு + ஆடு -> வரட்டாடு", "குருடு + கோழி -> குருட்டுக்கோழி", "வெளிறு + பனை -> வெளிற்றுப்பனை")`
     `THEN ட்/ற் DOUBLES in Alvazhi.`
  4. **Minority Doubling of Other Stops (`கு, து`)** (implied by `மிகவே`):
     `IF S1 ∈ {"வெருகு", "எருது"} AND S2 ∈ attested compounds`
     `THEN க்/த் doubles in Both Vetrumai and Alvazhi ("வெருக்குக்கண்", "எருத்துக்கால்", "எருத்துமாடு").`
- **Interactions & Precedence**:
  - Feeds Sutra 182: once `டு/று` doubles, `S1` becomes an *ஒற்றிடையின் மிகும்* *Nedil/Uyir-thodar*, so Sutra 165 doubles following `க், ச், த், ப்`.
  - Before vowels, combines with Sutra 164 (`உயிர்வரினுக்குறள்`): `ஆடு + அடி -> ஆட்ட் + அடி -> ஆட்டடி`.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஆடு | கால் | ஆட்டுக்கால் | Vetrumai; Primary | `ட்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | பாறு | கால் | பாற்றுக்கால் | Vetrumai; Primary | `ற்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | முருடு | கால் | முருட்டுக்கால் | Vetrumai; Primary | `ட்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | முயிறு | கால் | முயிற்றுக்கால் | Vetrumai; Primary | `ற்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | ஆடு | அடி | ஆட்டடி | Vetrumai (before V); Primary | `ட்` doubles + `உ` elides | `viruttiyurai_pno=248`, `kandigai=183` |
  | நாடு | கிழவோன் | நாடுகிழவோன் | Vetrumai; Minority non-doubling | Natural | `viruttiyurai_pno=248`, `kandigai=183` |
  | காடு | அகம் | காடகம் | Vetrumai; Minority non-doubling | `உ` elides, no `ட்` doubling | `viruttiyurai_pno=248`, `kandigai=183` |
  | மிடறு | அணியல் | மிடறணியல் | Vetrumai; Minority non-doubling | `உ` elides, no `ற்` doubling | `viruttiyurai_pno=248`, `kandigai=183` |
  | காடு | அரண் | காட்டரண் | Alvazhi; Minority doubling | `ட்` doubles + `உ` elides | `viruttiyurai_pno=248`, `kandigai=183` |
  | களிறு | யானை | களிற்றுயானை | Alvazhi; Minority doubling | `ற்` doubles | `viruttiyurai_pno=248` |
  | ஏறு | ஏனம் | ஏற்றேனம் | Alvazhi; Minority doubling | `ற்` doubles + `உ` elides | `kandigai=183` |
  | வரடு | ஆடு | வரட்டாடு | Alvazhi; Minority doubling | `ட்` doubles + `உ` elides | `kandigai=183` |
  | குருடு | கோழி | குருட்டுக்கோழி | Alvazhi; Minority doubling | `ட்` doubles + `க்` doubles | `kandigai=183` |
  | வெளிறு | பனை | வெளிற்றுப்பனை | Alvazhi; Minority doubling | `ற்` doubles + `ப்` doubles | `kandigai=183` |
  | வெருகு | கண் | வெருக்குக்கண் | Vetrumai; Other stop doubling | `க்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | எருது | கால் | எருத்துக்கால் | Vetrumai; Other stop doubling | `த்` doubles + `க்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
  | எருது | மாடு | எருத்து மாடு | Alvazhi; Other stop doubling | `த்` doubles | `viruttiyurai_pno=248`, `kandigai=183` |
- **Surface Signature & Reversibility**:
  - `...ட்டு...` / `...ற்று...` in compound stems -> candidate `S1` is `...டு` / `...று` (Nedil/Uyir-thodar).

---

## Sutra 184 — *Menthodar* *Kurriyalugaram* Nasal-to-Stop Conversion

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Morphosyntactic | Executable: Yes (Lexicon-gated) | Viruttiyurai pno: 248, 249 | Kandigai: 184 | Poetic: No`
- **Root Text (TVA 1999)**:
  > மென்றொடர் மொழியுட் சிலவேற் றுமையிற்
  > றம்மின வன்றொட ராகா மன்னே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`மென் தொடர் மொழி உள் சில வேற்றுமை இல் / தம் இன வன் தொடர் ஆகா மன் ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Lexicalized Conversion in *Vetrumai*** (stated negatively: "some do not fail to become their homorganic *Vanthodar*"):
     `IF S1 ∈ Menthodar_Vanthodar_Lexicon (e.g., "மருந்து", "சுரும்பு", "கரும்பு", "கன்று") AND context == Vetrumai` (before all 4 *ganam*s)
     `THEN S1's penultimate nasal converts to its homorganic voiceless stop (ந் -> த், ம் -> ப், ன் -> ற், etc.), making S1 Vanthodar.`
     - `IF S2.initial ∈ {க், ச், த், ப்}` -> `S2.initial` DOUBLES (per Vanthodar rule).
     - `IF S2.initial ∈ Vowel` -> `உ` drops (Sutra 164) on the converted *Vanthodar* stem.
  2. **Majority Non-Conversion in *Vetrumai***:
     `IF S1 ∈ Menthodar (general, e.g., "வண்டு", "பந்து") AND S1 ∉ Menthodar_Vanthodar_Lexicon AND context == Vetrumai`
     `THEN S1 remains Menthodar (e.g., "வண்டுக்கால்", "பந்துத்திரட்சி" — with vallinam doubling per Sutra 165).`
  3. **Rare Conversion in *Alvazhi*** (from `மன்னே`):
     `IF S1 ∈ {"என்பு", "அன்பு", "குரங்கு"} AND context == Alvazhi AND S2 ∈ attested compounds`
     `THEN S1 converts to Vanthodar ("எற்புடம்பு", "அற்புத்தளை", "குரக்குமனம்").`
     - Note: The penultimate nasal converts to its homorganic voiceless stop (`ன் -> ற்` in `என்பு -> எற்பு`, `அன்பு -> அற்பு`; `ங் -> க்` in `குரங்கு -> குரக்கு`).
- **Interactions & Precedence**:
  - Lexicon-gated conversion feeds Sutra 164 (vowel elision) and Sutra 165 (stop doubling).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | மருந்து | பை | மருத்துப்பை | Vetrumai; Conversion | `ந் -> த்` + `ப்` doubles | `viruttiyurai_pno=248`, `kandigai=184` |
  | சுரும்பு | நாண் | சுருப்புநாண் | Vetrumai; Conversion | `ம் -> ப்` | `viruttiyurai_pno=248`, `kandigai=184` |
  | கரும்பு | வில் | கருப்புவில் | Vetrumai; Conversion | `ம் -> ப்` | `viruttiyurai_pno=248`, `kandigai=184` |
  | கன்று | ஆ | கற்றா | Vetrumai (before V); Conversion | `ன் -> ற்` + `உ` elides | `viruttiyurai_pno=248`, `kandigai=184` |
  | வண்டு | கால் | வண்டுக்கால் | Vetrumai; Majority non-conversion | `க்` doubles (stays Menthodar) | `viruttiyurai_pno=248`, `kandigai=184` |
  | பந்து | திரட்சி | பந்துத்திரட்சி | Vetrumai; Majority non-conversion | `த்` doubles (stays Menthodar) | `viruttiyurai_pno=248`, `kandigai=184` |
  | என்பு | உடம்பு | எற்புடம்பு | Alvazhi; Rare conversion (`மன்னே`) | `ன் -> ற்` + `உ` elides | `viruttiyurai_pno=249`, `kandigai=184` |
  | அன்பு | தளை | அற்புத்தளை | Alvazhi; Rare conversion (`மன்னே`) | `ன் -> ற்` + `த்` doubles | `viruttiyurai_pno=249`, `kandigai=184` |
  | குரங்கு | மனம் | குரக்குமனம் | Alvazhi; Rare conversion (`மன்னே`) | `ங் -> க்` | `viruttiyurai_pno=249`, `kandigai=184` |
- **Surface Signature & Reversibility**:
  - `மருத்து-`, `சுருப்பு-`, `கருப்பு-`, `கற்றா` -> reverse-map via *Menthodar-to-Vanthodar* lexicon.

---

## Sutra 185 — `ஐ` *Chariyai* Increment on *Kurriyalugaram* Stems

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Morphological | Executable: Yes (Lexicon-gated) | Viruttiyurai pno: 249 | Kandigai: 185 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஐயீற் றுடைக்குற் றுகரமு முளவே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஐ ஈற்று உடை குற்றுகரம் உம் உள ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Menthodar + `ஐ` (with optional Sutra 184 *Vanthodar* conversion)**:
     `IF S1 ∈ {"பண்டு", "இன்று", "அன்று"} AND context ∈ {Alvazhi, Vetrumai}`
     `THEN S1 drops final உ (and optionally converts nasal per Sutra 184: "இன்று -> இற்ற-", "அன்று -> அற்ற-", while "பண்டு -> பண்ட-") and takes -ஐ (பண்டை, இற்றை, அற்றை); following க்/ச்/த்/ப் doubles where applicable.`
  2. **Vanthodar + `ஐ` (extension)**:
     `IF S1 ∈ {"நேற்று"} AND context ∈ {Alvazhi, Vetrumai}`
     `THEN S1 drops final உ and takes -ஐ -> "நேற்றை" (e.g., "நேற்றைப்பொழுது", "நேற்றைக் கூலி").`
  3. **Standalone / Compound Stem + `ஐ` (without following word)**:
     `IF S1 ∈ {"ஒன்று", "இரண்டு", "வேட்டு", "ஓராண்டு", "ஈராண்டு", "மூவாண்டு"}`
     `THEN S1 takes -ஐ as a derived stem ("ஒற்றை", "இரட்டை", "வேட்டை", "ஓராட்டை", "ஈராட்டை", "மூவாட்டை").`
- **Interactions & Precedence**:
  - Builds on Sutra 184: `இன்று -> இற்று -> இற்றை`, `அன்று -> அற்று -> அற்றை`.
  - Once `-ஐ` is attached, *vallinam* doubling follows `ஐ`-final rules (Sutra 165).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பண்டு | காலம் | பண்டைக் காலம் | Both; `-ஐ` increment | `உ -> ஐ` + `க்` doubles | `viruttiyurai_pno=249`, `kandigai=185` |
  | இன்று | நாள் | இற்றை நாள் | Both; `ன் -> ற்` + `-ஐ` | `ன் -> ற்`, `உ -> ஐ` | `viruttiyurai_pno=249`, `kandigai=185` |
  | அன்று | கூலி | அற்றைக் கூலி | Both; `ன் -> ற்` + `-ஐ` | `ன் -> ற்`, `உ -> ஐ` + `க்` doubles | `viruttiyurai_pno=249`, `kandigai=185` |
  | இன்று | நலம் | இற்றை நலம் | Both; `ன் -> ற்` + `-ஐ` | `ன் -> ற்`, `உ -> ஐ` | `viruttiyurai_pno=249`, `kandigai=185` |
  | நேற்று | பொழுது | நேற்றைப் பொழுது | Alvazhi (Vanthodar); `-ஐ` | `உ -> ஐ` + `ப்` doubles | `viruttiyurai_pno=249`, `kandigai=185` |
  | நேற்று | கூலி | நேற்றைக் கூலி | Vetrumai (Vanthodar); `-ஐ` | `உ -> ஐ` + `க்` doubles | `kandigai=185` |
  | ஒன்று | ∅ | ஒற்றை | Standalone derived | `ன் -> ற்`, `உ -> ஐ` | `viruttiyurai_pno=249`, `kandigai=185` |
  | இரண்டு | ∅ | இரட்டை | Standalone derived | `ண்டு -> ட்டை` (`ண்` drops, `ட்` doubles, `உ -> ஐ`) | `viruttiyurai_pno=249`, `kandigai=185` |
  | வேட்டு | ∅ | வேட்டை | Standalone derived | `உ -> ஐ` | `viruttiyurai_pno=249` |
  | ஓராண்டு | ∅ | ஓராட்டை | Compound derived | `ண்டு -> ட்டை` (`ண்` drops, `ட்` doubles, `உ -> ஐ`) | `kandigai=185` |
  | ஈராண்டு | ∅ | ஈராட்டை | Compound derived | `ண்டு -> ட்டை` (`ண்` drops, `ட்` doubles, `உ -> ஐ`) | `viruttiyurai_pno=249`, `kandigai=185` |
  | மூவாண்டு | ∅ | மூவாட்டை | Compound derived | `ண்டு -> ட்டை` (`ண்` drops, `ட்` doubles, `உ -> ஐ`) | `viruttiyurai_pno=249` |
- **Surface Signature & Reversibility**:
  - `பண்டை`, `இற்றை`, `அற்றை`, `நேற்றை`, `-ஆட்டை` -> reversible via lexical table.

---

## Sutra 186 — *Kurriyalugaram* Direction Words (`திசைப்பெயர்கள்`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Morphological | Executable: Yes (Lexical matrix) | Viruttiyurai pno: 249, 250 | Kandigai: 186 | Poetic: No`
- **Root Text (TVA 1999)**:
  > திசையொடு திசையும் பிறவுஞ் சேரின்
  > நிலையீற் றுயிர்மெய் கவ்வொற்று நீங்கலும்
  > றகரம் னலவாத் திரிதலு மாம்பிற.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`திசை ஒடு திசை உம் பிற உம் சேரின் / நிலை ஈற்று உயிர்மெய் க ஒற்று நீங்கல் உம் / றகரம் ன ல ஆ திரிதல் உம் ஆம் பிற`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Base Deletion (`நிலையீற்று உயிர்மெய் கவ்வொற்று நீங்கல்`)**:
     `IF S1 ∈ {"வடக்கு", "தெற்கு", "மேற்கு", "குடக்கு", "குணக்கு"} AND S2 ∈ {Direction, Other}`
     `THEN drop final உயிர்மெய் ("கு") AND preceding க்-ஒற்று:`
     - `வடக்கு` -> `வட` (`வடகிழக்கு, வடமேற்கு, வடதிசை, வடபால், வடமலை, வடவேங்கடம்`).
     - `குடக்கு` -> `குட` (`குடதிசை, குடகடல், குடநாடு`).
     - `குணக்கு` -> `குண` (`குணதிசை, குணகடல், குணபால்`).
  2. **`றகரம் னலவாத் திரிதல்` (after dropping `கு` + `க்`)**:
     - `S1 == "தெற்கு"`: `தெற்கு` -> `தெற்` -> `தென்` (`ற் -> ன்`) before both directions (`தென்கிழக்கு, தென்மேற்கு`) and other words (`தென்குமரி, தென்வீதி, தென்மலை`).
     - `S1 == "மேற்கு"`: `மேற்கு` -> `மேற்` -> `மேல்` (`ற் -> ல்`) before non-`த` (`மேல்பால், மேல்கடல், மேல்வீதி`), and `மேல் + நாடு -> மேனாடு` (nasal assimilation), EXCEPT before `திசை` (`தகரம்` initial): `ற்` stays `ற்` -> `மேற்றிசை` (Kandigai 186).
  3. **`கிழக்கு` Special Rule (from `பிற`)**:
     `IF S1 == "கிழக்கு"`
     `THEN drop final "கு" + "க்", drop "அ" in "ழ", lengthen "கி" -> "கீ" => "கீழ்"` (`கீழ்கரை, கீழ்சார், கீழ்த்திசை`).
  4. **Additional Variants (from `பிற`)**:
     - `-ஐ` increment: `மேலைத்திசை, மேலைக்குளம், மேலைச்சேரி, கீழைத்திசை, கீழைக்குளம், கீழைச்சேரி`.
     - *Ummaiththogai* compound of all 4: `கீழ்மேற்றென்வடல்` (`கிழக்கு + மேற்கு + தெற்கு + வடக்கு`).
     - Unmodified / natural forms when `S2` is a general noun or cardinal-to-cardinal *Ummaiththogai*: `வடக்கூர், தெற்கூர், வடக்குமலை, தெற்குமலை`; and cardinal-to-cardinal `தெற்குவடக்கு, வடக்குத்தெற்கு, கிழக்குமேற்கு, மேற்குக்கிழக்கு`.
  5. **Cardinal + Cardinal Direction Scope (Kandigai 186)**:
     - When forming intercardinal (கோணத்திசை) compounds, only `வடக்கு` and `தெற்கு` stand as `S1`, with `கிழக்கு` or `மேற்கு` as `S2` (`வடகிழக்கு, வடமேற்கு, தென்கிழக்கு, தென்மேற்கு`).
- **Interactions & Precedence**:
  - `மேல் + நாடு -> மேனாடு` involves `ல் + ந் -> ன்` (consonant sandhi, cf. *Meyyīṟṟup Puṇariyal*).
  - `மேல் + திசை -> மேற்றிசை` retains `ற்` (or `ல் + த் -> ற்ற்`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | வடக்கு | கிழக்கு | வடகிழக்கு | Intercardinal (Anmolithogai) | Drop `க்கு` | `viruttiyurai_pno=250` |
  | வடக்கு | மேற்கு | வடமேற்கு | Intercardinal | Drop `க்கு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | வடக்கு | திசை | வடதிசை | Panputhogai | Drop `க்கு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | வடக்கு | மலை | வடமலை | Vetrumai-7; Modified / Unmodified | `வடமலை` / `வடக்குமலை` | `viruttiyurai_pno=250`, `kandigai=186` |
  | வடக்கு | ஊர் | வடக்கூர் | Unmodified (`பிற`) | `உ` elides | `viruttiyurai_pno=250`, `kandigai=186` |
  | தெற்கு | கிழக்கு | தென்கிழக்கு | Intercardinal | Drop `க்கு`, `ற் -> ன்` | `viruttiyurai_pno=250`, `kandigai=186` |
  | தெற்கு | மேற்கு | தென்மேற்கு | Intercardinal | Drop `க்கு`, `ற் -> ன்` | `viruttiyurai_pno=250`, `kandigai=186` |
  | தெற்கு | குமரி | தென்குமரி | Compound | Drop `க்கு`, `ற் -> ன்` | `viruttiyurai_pno=250`, `kandigai=186` |
  | தெற்கு | ஊர் | தெற்கூர் | Unmodified (`பிற`) | `உ` elides | `viruttiyurai_pno=250`, `kandigai=186` |
  | மேற்கு | பால் | மேல்பால் | Compound | Drop `க்கு`, `ற் -> ல்` | `viruttiyurai_pno=250` |
  | மேற்கு | கடல் | மேல்கடல் | Compound | Drop `க்கு`, `ற் -> ல்` | `kandigai=186` |
  | மேற்கு | நாடு | மேனாடு | Compound | `மேல் + நாடு -> மேனாடு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | மேற்கு | திசை | மேற்றிசை | Compound (before `த்`) | `ற்` retained / `மேல்+திசை` | `viruttiyurai_pno=250`, `kandigai=186` |
  | மேற்கு | திசை | மேலைத்திசை | `-ஐ` variant (`பிற`) | `மேலை` + `த்` doubles | `viruttiyurai_pno=250` |
  | கிழக்கு | கரை | கீழ்கரை | Compound (`பிற`) | `கிழக்கு -> கீழ்` | `kandigai=186` |
  | கிழக்கு | திசை | கீழ்த்திசை | Compound (`பிற`) | `கிழக்கு -> கீழ்` + `த்` doubles | `viruttiyurai_pno=250`, `kandigai=186` |
  | கிழக்கு | திசை | கீழைத்திசை | `-ஐ` variant (`பிற`) | `கீழை` + `த்` doubles | `viruttiyurai_pno=250` |
  | குடக்கு | திசை | குடதிசை | Compound | Drop `க்கு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | குடக்கு | நாடு | குடநாடு | Compound | Drop `க்கு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | குணக்கு | கடல் | குணகடல் | Compound | Drop `க்கு` | `viruttiyurai_pno=250`, `kandigai=186` |
  | தெற்கு | வடக்கு | தெற்குவடக்கு | Cardinal-cardinal Ummaiththogai | General rule | `kandigai=186` |
  | கிழக்கு+மேற்கு+தெற்கு+வடக்கு | (multi) | கீழ்மேற்றென்வடல் | 4-way Ummaiththogai | Combined | `viruttiyurai_pno=250` |
- **Surface Signature & Reversibility**:
  - Prefixes `வட-, தென்-, மேல்-, மேற்-, மேலை-, கீழ்-, கீழை-, குட-, குண-` -> map to `{வடக்கு, தெற்கு, மேற்கு, கிழக்கு, குடக்கு, குணக்கு}`.

---

## Sutra 187 — `தெங்கு + காய் -> தேங்காய்`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical | Executable: Yes (Lexical) | Viruttiyurai pno: 250 | Kandigai: 187 | Poetic: No`
- **Root Text (TVA 1999)**:
  > தெங்குநீண் டீற்றுயிர் மெய்கெடுங் காய்வரின்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`தெங்கு நீண்டு ஈற்று உயிர்மெய் கெடும் காய் வரின்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == "தெங்கு" AND S2 == "காய்"`
     `THEN S1.initial "தெ" lengthens to "தே" AND S1.final "கு" drops, yielding "தேங் + காய் -> தேங்காய்".`
  2. `IF S1 == "தெங்கு" AND S2 == "காய்"` (optionality: rule does not forbid natural/chariyai form)
     `THEN ALSO allow "தெங்கங்காய்" (via அம் chariyai).`
- **Interactions & Precedence**:
  - Lexical rule specific to `தெங்கு + காய்`.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | தெங்கு | காய் | தேங்காய் | Primary | `தெ -> தே`, drop `கு` | `viruttiyurai_pno=250`, `kandigai=187` |
  | தெங்கு | காய் | தெங்கங்காய் | Alternate (`யா. வி. 95`) | `உ` elides + `-அம்-` | `viruttiyurai_pno=250`, `kandigai=187` |
- **Surface Signature & Reversibility**:
  - `தேங்காய்` / `தெங்கங்காய்` -> `தெங்கு + காய்`.

---

## Sutra 188 — General Rules for Numerals `1..8` (`எண், நிறை, அளவு, பிற`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes (with Sutras 189–193) | Viruttiyurai pno: 250, 251, 252 | Kandigai: 188 | Poetic: No`
- **Root Text (TVA 1999)**:
  > எண்ணிறை யளவும் பிறவு மெய்தின்
  > ஒன்று முதலெட் டீறா மெண்ணுண்
  > முதலீ ரெண்முத னீளு மூன்றா
  > றேழ்குறு கும்மா றேழல் லவற்றின்
  > ஈற்றுயிர் மெய்யு மேழ னுயிரும்
  > ஏகு மேற்புழி யென்மனார் புலவர்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`குறுகும் ஆறு` vs `குறு கும்மா று`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Scope (`எண், நிறை, அளவு, பிற` + `ஏற்புழி`)**:
     `IF S1 ∈ {"ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "ஆறு", "ஏழு", "எட்டு"} AND S2.class ∈ {Number, Weight (நிறை), Measure (அளவு), Other (பிற)} AND compound_type == Panputhogai (where applicable, `ஏற்புழி`)`
     `THEN apply the following base transformations (which do NOT block natural/unmodified forms like "இரண்டு கழஞ்சு", "மூன்று படி", "நான்கு பொருள்", "ஐந்து பூதம்", "ஆறு குணம்", "ஏழு கடல்", "எட்டுக் கோடி"):`
  2. **First Two (`ஒன்று, இரண்டு`) — Lengthening (`முதல் நீளும்`)**:
     `IF S1 ∈ {"ஒன்று", "இரண்டு"} AND S2.initial ∈ Vowel` (per Kandigai 188 `ஏற்புழி`: before V, lengthens; before C, does not lengthen)
     `THEN S1.initial lengthens: ஒ -> ஓ, இ -> ஈ` (combined with Sutra 189: `ஓர்`, `ஈர்`; before C: `ஒரு`, `இரு`).
  3. **Three, Six, Seven (`மூன்று, ஆறு, ஏழு`) — Shortening (`குறுகும்`)**:
     `IF S1 ∈ {"மூன்று", "ஆறு", "ஏழு"} AND S2.initial ∈ Consonant` (per Kandigai 188 `ஏற்புழி`: before C, shortens; before V, does not shorten)
     `THEN S1.initial shortens: மூ -> மு, ஆ -> அ, ஏ -> எ` (`முப்ப-, அறு-, எழு-`).
     - Note: `ஆறு + C -> அறு + C` (`அறுபது, அறுகழஞ்சு, அறுநாழி, அறுவட்டி`); `ஏழு + C -> எழு + C` (`எழுபது, எழுகழஞ்சு, எழுநாழி, எழுவகை`).
  4. **Final Deletion (`ஆறு, ஏழு` vs others)**:
     - `IF S1 ∈ {"ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "எட்டு"}` (the 6 other than `ஆறு, ஏழு`)
       `THEN S1.final_uyirmey (து/று/கு) drops before all 4 ganams (ன/ண/ன்/ந்/ட் remain for Sutras 189–193).`
     - `IF S1 == "ஏழு"` (when NOT shortened before C, or treated as `ஏழ்` + `உ` *mutriyalugaram*)
       `THEN S1.final_vowel "உ" drops -> "ஏழ்" (e.g., "ஏழ்கடல்"), or before V drops "உ" via Sutra 164 ("ஏழாயிரம்").`
     - `IF S1 == "ஆறு"`
       `THEN final "று" is retained ("அறு-"); before V drops "உ" via Sutra 164.`
- **Interactions & Precedence**:
  - Governs Sutras 189–193 (`ஏற்புழி` carries through 189–193).
  - Natural/unmodified forms remain valid alongside modified forms (e.g., `ஏழு கடல்` alongside `ஏழ்கடல்`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஆறு | பத்து | அறுபது | Number (shortened) | `ஆ -> அ` | `viruttiyurai_pno=251`, `kandigai=188` |
  | ஆறு | கழஞ்சு | அறுகழஞ்சு | Weight (shortened) | `ஆ -> அ` | `viruttiyurai_pno=251`, `kandigai=188` |
  | ஆறு | நாழி | அறுநாழி | Measure (shortened) | `ஆ -> அ` | `viruttiyurai_pno=251`, `kandigai=188` |
  | ஆறு | வட்டி | அறுவட்டி | Measure (shortened) | `ஆ -> அ` | `kandigai=188` |
  | ஏழு | பத்து | எழுபது | Number (shortened) | `ஏ -> எ` | `viruttiyurai_pno=251`, `kandigai=188` |
  | ஏழு | கடல் | ஏழ்கடல் | Other; `உ` dropped | Drop `உ` | `viruttiyurai_pno=251`, `kandigai=188` |
  | ஏழு | ஆயிரம் | ஏழாயிரம் | Before V; `உ` elides | Drop `உ` (Sutra 164) | `viruttiyurai_pno=251`, `kandigai=188` |
  | இரண்டு | ஆயிரம் | இரண்டாயிரம் | Unmodified before V | Drop `உ` (Sutra 164) | `viruttiyurai_pno=251` |
  | இரண்டு | கழஞ்சு | இரண்டு கழஞ்சு | Unmodified | Natural | `viruttiyurai_pno=252`, `kandigai=188` |
  | மூன்று | படி | மூன்று படி | Unmodified | Natural | `viruttiyurai_pno=252`, `kandigai=188` |
  | நான்கு | பொருள் | நான்கு பொருள் | Unmodified | Natural | `viruttiyurai_pno=252`, `kandigai=188` |
- **Surface Signature & Reversibility**:
  - `அறு-`, `எழு-`, `ஏழ்-` -> `ஆறு`, `ஏழு`.

---

## Sutra 189 — Numerals `1` (`ஒன்று`) and `2` (`இரண்டு`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 252 | Kandigai: 189 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஒன்றன் புள்ளி ரகர மாக
  > இரண்ட னொற்றுயி ரேகவுவ் வருமே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`உவ் வரும்` vs `உ வரும்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Base Stem Derivation (after Sutra 188 drops final `று`/`டு`)**:
     - `ஒன்று` -> `ஒன்` -> `ன்` becomes `ர்` => `ஒர்` (or `ஓர்` if lengthened).
     - `இரண்டு` -> `இரண்` -> `ண்` and `அ` (in `ர`) drop => `இர்` (or `ஈர்` if lengthened).
  2. **Before Consonant (`S2.initial ∈ Consonant`)**:
     `THEN add "உ" to ர் -> "ஒரு" / "இரு"` (e.g., `ஒருபது, இருபது, ஒருகழஞ்சு, இருகழஞ்சு, ஒருநாழி, இருநாழி, ஒருவகை, இருவகை`).
     - Exception (Kandigai 189): Before `ய்` (`யானை`), BOTH `ஒரு யானை` / `இரு யானை` AND `ஓர் யானை` / `ஈர் யானை` (without `உ`, with lengthening) are attested.
  3. **Before Vowel (`S2.initial ∈ Vowel`)**:
     `THEN do NOT add "உ" (or elide "உ" per Sutra 164) and lengthen initial (Sutra 188):`
     - `ஓர் + V` (`ஓரொன்று, ஓரெடை, ஓருழக்கு, ஓரிலை`), `ஈர் + V` (`ஈரொன்று, ஈரெடை, ஈருழக்கு, ஈரிலை`).
     - Special case `ஆயிரம்`: BOTH unlengthened `ஒராயிரம் / இராயிரம்` (Viruttiyurai pno=252, Kandigai 189) AND lengthened `ஓராயிரம் / ஈராயிரம்` (Kandigai 189) are attested.
- **Interactions & Precedence**:
  - Depends on Sutra 188 for initial lengthening and final `று/டு` deletion.
  - Feeds Sutra 195 (`ஒருபது/ஒருபஃது`, `இருபது/இருபஃது`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஒன்று | ஆயிரம் | ஒராயிரம் / ஓராயிரம் | Number before V; Both attested | `ஒன்->ஒர்/ஓர்` + `ஆயிரம்` | `viruttiyurai_pno=252` (`ஒராயிரம்`), `kandigai=189` (both) |
  | இரண்டு | ஆயிரம் | இராயிரம் / ஈராயிரம் | Number before V; Both attested | `இரண்->இர்/ஈர்` + `ஆயிரம்` | `viruttiyurai_pno=252` (`இராயிரம்`), `kandigai=189` (both) |
  | ஒன்று | பத்து | ஒருபது | Number before C | `ஒன்று -> ஒரு` (+ Sutra 195) | `viruttiyurai_pno=252`, `kandigai=189` |
  | இரண்டு | பத்து | இருபது | Number before C | `இரண்டு -> இரு` (+ Sutra 195) | `viruttiyurai_pno=252`, `kandigai=189` |
  | ஒன்று | கழஞ்சு | ஒருகழஞ்சு | Weight before C | `ஒன்று -> ஒரு` | `viruttiyurai_pno=252`, `kandigai=189` |
  | இரண்டு | கழஞ்சு | இருகழஞ்சு | Weight before C | `இரண்டு -> இரு` | `viruttiyurai_pno=252`, `kandigai=189` |
  | ஒன்று | ஒன்று | ஓரொன்று | Number before V | `ஒன்று -> ஓர்` | `kandigai=189` |
  | இரண்டு | ஒன்று | ஈரொன்று | Number before V | `இரண்டு -> ஈர்` | `kandigai=189` |
  | ஒன்று | யானை | ஒரு யானை / ஓர் யானை | Before `ய்`; Optional | `ஒரு` / `ஓர்` | `kandigai=189` |
  | இரண்டு | யானை | இரு யானை / ஈர் யானை | Before `ய்`; Optional | `இரு` / `ஈர்` | `kandigai=189` |
- **Surface Signature & Reversibility**:
  - `ஒரு/ஓர்/ஒர்-`, `இரு/ஈர்/இர்-` -> `ஒன்று`, `இரண்டு`.

---

## Sutra 190 — Numeral `3` (`மூன்று`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 252 | Kandigai: 190 | Poetic: No`
- **Root Text (TVA 1999)**:
  > மூன்றனுறுப் பழிவும் வந்தது மாகும்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`மூன்றன் உறுப்பு அழிவு உம் வந்தது உம் ஆகும்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Before Vowel (`S2.initial ∈ Vowel`)**:
     `IF S1 == "மூன்று" AND S2.initial ∈ Vowel`
     `THEN drop final "று" (Sutra 188) AND drop "ன்" -> "மூ" + glide "வ்" (Sutra 162) -> "மூவ்" + S2` (`மூவொன்று, மூவெடை, மூவுழக்கு, மூவுலகு`).
  2. **Before Consonant (`S2.initial ∈ Consonant`)**:
     `IF S1 == "மூன்று" AND S2.initial ∈ Consonant`
     `THEN shorten "மூ -> மு" (Sutra 188), drop final "று", AND assimilate "ன்" to S2.initial (வந்த ஒற்று)` (`முப்பது, முக்கழஞ்சு, முந்நாழி, முந்நூல், மும்மொழி, முவ்வட்டி`).
  3. **Kandigai Exceptions (`ஏற்புழி`)**:
     - Before `வட்டி` (`வ்`): BOTH `முவ்வட்டி` AND `மூவட்டி` (unshortened, `ன்` dropped) are attested.
     - Before `யானை` (`ய்`): `ன்` becomes `வ்` -> `முவ்யானை`.
- **Interactions & Precedence**:
  - Uses Sutra 188 for `மூ -> மு` (before C) and `று` deletion; uses Sutra 162 (`வ்` glide) when `மூ` precedes a vowel.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | மூன்று | ஒன்று | மூவொன்று | Number before V | Drop `ன்று` + `வ்` glide | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | எடை | மூவெடை | Weight before V | Drop `ன்று` + `வ்` glide | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | உழக்கு | மூவுழக்கு | Measure before V | Drop `ன்று` + `வ்` glide | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | உலகு | மூவுலகு | Other before V | Drop `ன்று` + `வ்` glide | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | பத்து | முப்பது | Number before `ப்` | `மூ->மு`, `ன்->ப்` (+ Sutra 195) | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | கழஞ்சு | முக்கழஞ்சு | Weight before `க்` | `மூ->மு`, `ன்->க்` | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | நாழி | முந்நாழி | Measure before `ந்` | `மூ->மு`, `ன்->ந்` | `viruttiyurai_pno=252`, `kandigai=190` |
  | மூன்று | மொழி | மும்மொழி | Other before `ம்` | `மூ->மு`, `ன்->ம்` | `viruttiyurai_pno=252` |
  | மூன்று | வட்டி | முவ்வட்டி / மூவட்டி | Before `வ்`; Optional | `முவ்-` / `மூ-` | `kandigai=190` |
  | மூன்று | யானை | முவ்யானை | Before `ய்` | `ன் -> வ்` | `kandigai=190` |
- **Surface Signature & Reversibility**:
  - `மூவ-`, `மு[க்ச்த்ப்ந்ம்வ்]C...` -> `மூன்று + S2`.

---

## Sutra 191 — Numeral `4` (`நான்கு`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 252, 253 | Kandigai: 191 | Poetic: No`
- **Root Text (TVA 1999)**:
  > நான்கன் மெய்யே லறவா கும்மே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`நான்கன் மெய் ஏ ல ற ஆகும் ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Before Vowel or *Idaiyinam* (`S2.initial ∈ Vowel ∪ Idaiyinam`)**:
     `IF S1 == "நான்கு" AND S2.initial ∈ Vowel ∪ Idaiyinam`
     `THEN drop final "கு" (Sutra 188) and convert "ன்" -> "ல்" => "நால்" + S2` (`நாலொன்று, நாலெடை, நாலுழக்கு, நாலடி, நால்வட்டி`).
  2. **Before *Vallinam* (`S2.initial ∈ {க், ச், த், ப்}`)**:
     `IF S1 == "நான்கு" AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN drop final "கு" and convert "ன்" -> "ற்" => "நாற்" + S2` (`நாற்பது, நாற்கழஞ்சு, நாற்கலம், நாற்கவி`).
  3. **Before *Mellinam* (`S2.initial ∈ {ந், ம}`)**:
     `IF S1 == "நான்கு" AND S2.initial ∈ Mellinam`
     `THEN drop final "கு" and retain "ன்" (following னகர ஈற்றுப் புணர்ச்சி: `நான் + நாழி -> நானாழி` with `ன்+ந் -> ந்/ன்`, `நான் + மணி -> நான்மணி`)`.
- **Interactions & Precedence**:
  - `நான் + நாழி -> நானாழி` applies consonant-final `ன் + ந்` sandhi (cf. *Meyyīṟṟup Puṇariyal*).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | நான்கு | ஒன்று | நாலொன்று | Number before V | `ன் -> ல்` | `viruttiyurai_pno=253`, `kandigai=191` |
  | நான்கு | எடை | நாலெடை | Weight before V | `ன் -> ல்` | `viruttiyurai_pno=253`, `kandigai=191` |
  | நான்கு | உழக்கு | நாலுழக்கு | Measure before V | `ன் -> ல்` | `kandigai=191` |
  | நான்கு | வட்டி | நால்வட்டி | Measure before `வ்` | `ன் -> ல்` | `kandigai=191` |
  | நான்கு | பத்து | நாற்பது | Number before `ப்` | `ன் -> ற்` (+ Sutra 195) | `viruttiyurai_pno=253`, `kandigai=191` |
  | நான்கு | கழஞ்சு | நாற்கழஞ்சு | Weight before `க்` | `ன் -> ற்` | `viruttiyurai_pno=253`, `kandigai=191` |
  | நான்கு | கலம் | நாற்கலம் | Measure before `க்` | `ன் -> ற்` | `viruttiyurai_pno=253` |
  | நான்கு | கவி | நாற்கவி | Other before `க்` | `ன் -> ற்` | `viruttiyurai_pno=253` |
  | நான்கு | நாழி | நானாழி | Measure before `ந்` | `ன்` retained (`ன்+ந்->ன`) | `viruttiyurai_pno=253`, `kandigai=191` |
  | நான்கு | மணி | நான்மணி | Other before `ம்` | `ன்` retained | `viruttiyurai_pno=253`, `kandigai=191` |
- **Surface Signature & Reversibility**:
  - `நால்-`, `நாற்-`, `நான்-`, `நானாழி` -> `நான்கு + S2`.

---

## Sutra 192 — Numeral `5` (`ஐந்து`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 253 | Kandigai: 192 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஐந்தனொற் றடைவது மினமுங் கேடும்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஐந்தன் ஒற்று அடைவது உம் இனம் உம் கேடு உம்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Before *Mellinam* (`S2.initial ∈ Mellinam \ {ந்}`)**:
     `IF S1 == "ஐந்து" AND S2.initial ∈ {ஞ், ம்}` (specifically `ம், ஞ்` attested; before `ந்`, `ந்` stays natural per `ஐந்நூறு`)
     `THEN drop final "து" (Sutra 188) AND assimilate "ந்" to S2.initial (அடைவது)` (`ஐம்மூன்று, ஐம்மஞ்சாடி, ஐஞ்ஞாண்`).
  2. **Before *Vallinam* (`S2.initial ∈ {க், ச், த், ப்}`)**:
     `IF S1 == "ஐந்து" AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN drop final "து" AND convert "ந்" to the homorganic nasal of S2.initial (இனம்)`:
     - `க் -> ங்` (`ஐங்கழஞ்சு, ஐங்கலம்`), `ச் -> ஞ்`, `த் -> ந்` (stays `ந்`: `ஐந்தூணி`), `ப் -> ம்` (`ஐம்பது, ஐம்பொறி`).
     - Note: Viruttiyurai/Kandigai also note `ஐந்நூறு` (`ந்` stays natural before `ந்`) and `ஐந்தூணி` (`ந்` stays natural before `த்`) as *aruththapaththi* (`தன் இயல்பின் நிற்றல்`).
  3. **Before Vowel (`S2.initial ∈ Vowel`)**:
     `IF S1 == "ஐந்து" AND S2.initial ∈ Vowel`
     `THEN drop final "து" AND drop "ந்" (கேடு) -> "ஐ" + glide "ய்" (Sutra 162) -> "ஐய்" + S2` (`ஐயொன்று, ஐயெடை, ஐயாழாக்கு, ஐயம்பு`).
  4. **Before *Idaiyinam* (`S2.initial ∈ Idaiyinam`, e.g. `வ்`)**:
     `IF S1 == "ஐந்து" AND S2.initial == "வ்"`
     `THEN BOTH dropping "ந்" ("ஐவட்டி") AND assimilating "ந் -> வ்" ("ஐவ்வட்டி, ஐவ்வண்ணம்") are attested.`
- **Interactions & Precedence**:
  - Uses Sutra 188 for `து` deletion and Sutra 162 (`ய்` glide) when `ஐ` precedes a vowel.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஐந்து | மூன்று | ஐம்மூன்று | Before `ம்` | `ந் -> ம்` | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | மஞ்சாடி | ஐம்மஞ்சாடி | Before `ம்` | `ந் -> ம்` | `viruttiyurai_pno=253` |
  | ஐந்து | ஞாண் | ஐஞ்ஞாண் | Before `ஞ்` | `ந் -> ஞ்` | `kandigai=192` |
  | ஐந்து | வட்டி | ஐவ்வட்டி / ஐவட்டி | Before `வ்`; Optional | `ந் -> வ்` / drop `ந்` | `viruttiyurai_pno=253` (`ஐவ்வட்டி`), `kandigai=192` (`ஐவட்டி`) |
  | ஐந்து | வண்ணம் | ஐவ்வண்ணம் | Before `வ்` | `ந் -> வ்` | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | பத்து | ஐம்பது | Before `ப்` | `ந் -> ம்` (+ Sutra 195) | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | கழஞ்சு | ஐங்கழஞ்சு | Before `க்` | `ந் -> ங்` | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | கலம் | ஐங்கலம் | Before `க்` | `ந் -> ங்` | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | பொறி | ஐம்பொறி | Before `ப்` | `ந் -> ம்` | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | நூறு | ஐந்நூறு | Before `ந்`; Natural `ந்` | `ந்` retained | `viruttiyurai_pno=253` |
  | ஐந்து | தூணி | ஐந்தூணி | Before `த்`; Natural `ந்` | `ந்` retained | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | ஒன்று | ஐயொன்று | Before V | Drop `ந்து` + `ய்` glide | `viruttiyurai_pno=253`, `kandigai=192` |
  | ஐந்து | எடை | ஐயெடை | Before V | Drop `ந்து` + `ய்` glide | `viruttiyurai_pno=253` |
  | ஐந்து | ஆழாக்கு | ஐயாழாக்கு | Before V | Drop `ந்து` + `ய்` glide | `viruttiyurai_pno=253` |
  | ஐந்து | அம்பு | ஐயம்பு | Before V | Drop `ந்து` + `ய்` glide | `viruttiyurai_pno=253` |
- **Surface Signature & Reversibility**:
  - `ஐம்-`, `ஐங்-`, `ஐஞ்-`, `ஐந்-`, `ஐவ்-`, `ஐய-` -> `ஐந்து + S2`.

---

## Sutra 193 — Numeral `8` (`எட்டு`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 253, 254 | Kandigai: 193 | Poetic: No`
- **Root Text (TVA 1999)**:
  > எட்ட னுடம்பு ணவ்வாகு மென்ப.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`எட்டன் உடம்பு ண ஆகும் என்ப` vs `ணவ்வாகு மென்ப`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == "எட்டு" AND S2.class ∈ {Number, Weight, Measure, Other}` (all 4 *ganam*s)
     `THEN drop final "டு" (Sutra 188) AND convert remaining "ட்" to "ண்" => "எண்" + S2.`
     - Note: If `S2.initial ∈ Vowel` (e.g., `ஐந்து`), `எண்` being a single-short-vowel + consonant stem doubles `ண்` by Sutra 205 (`தனிக்குறின் முன்னொற்றுயிர்வரின் இரட்டும்`) -> `எண்ணைந்து`.
     - Note: If `S2.initial == "நூறு"` (`ந்`), `ண் + ந்` undergoes consonant sandhi (`எண்ணூறு`, cf. *Meyyīṟṟup Puṇariyal*).
- **Interactions & Precedence**:
  - Feeds Sutra 195 (`எண் + பத்து -> எண்பது / எண்பஃது`) and Sutra 205 (`எண் + ஐந்து -> எண்ணைந்து`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | எட்டு | பத்து | எண்பது | Number | `ட்டு -> ண்` (+ Sutra 195) | `viruttiyurai_pno=253`, `kandigai=193` |
  | எட்டு | கழஞ்சு | எண்கழஞ்சு | Weight | `ட்டு -> ண்` | `viruttiyurai_pno=253`, `kandigai=193` |
  | எட்டு | கலம் | எண்கலம் | Measure | `ட்டு -> ண்` | `viruttiyurai_pno=253`, `kandigai=193` |
  | எட்டு | குணம் | எண்குணம் | Other | `ட்டு -> ண்` | `viruttiyurai_pno=253`, `kandigai=193` |
  | எட்டு | நாழி | எண்ணாழி | Measure before `ந்` | `ட்டு -> ண்` (`ண்+ந்->ண்ண`) | `kandigai=193` |
  | எட்டு | வகை | எண்வகை | Other before `வ்` | `ட்டு -> ண்` | `kandigai=193` |
  | எட்டு | ஐந்து | எண்ணைந்து | Number before V | `ட்டு -> ண்` + `ண்` doubles (Sutra 205) | `kandigai=193` |
- **Surface Signature & Reversibility**:
  - `எண்-`, `எண்ண-` -> `எட்டு + S2`.

---

## Sutra 194 — `ஒன்பது + பத்து -> தொண்ணூறு` & `ஒன்பது + நூறு -> தொள்ளாயிரம்`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 254, 255 | Kandigai: 194 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஒன்பா னொடுபத்து நூறு மொன்றின்
  > முன்னதி னேனைய முரணி யொவ்வொடு
  > தகர நிறீஇப்பஃ தகற்றி னவ்வை
  > நிரலே ணளவாத் திரிப்பது நெறியே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஒன்பான் ஒடு பத்து உம் நூறு உம் ஒன்றின் / முன்னது இன் ஏனைய முரணி ஒ ஒடு / தகரம் நிறீஇ பஃது அகற்றி ன ஐ / நிரல் ஏ ண ள ஆ திரிப்பது நெறி ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)** — Step-by-step derivation as specified in Kandigaiyurai & Viruttiyurai:
  1. **`ஒன்பது` (or `ஒன்பஃது`) + `பத்து` -> `தொண்ணூறு`**:
     - Step 1 (`முன்னதின் ஏனைய முரணி`): Transform `S2 = "பத்து"` -> `"நூறு"`: `ஒன்பது + நூறு`.
     - Step 2 (`ஒவ்வொடு தகரம் நிறீஇ`): Prefix `த்` onto initial `ஒ` (`ஒ -> தொ`): `தொன்பது + நூறு`.
     - Step 3 (`பஃது அகற்றி`): Delete final `பது` (or `பஃது`): `தொன் + நூறு`.
     - Step 4 (`னவ்வை நிரலே ண ... ஆ திரிப்பது`): Convert `ன் -> ண்`: `தொண் + நூறு`.
     - Step 5 (`நெறியே` + `தனிக்குறில் முன்னொற்று இரட்டித்தல்` / `ண் + ந் -> ண்ண`): Double `ண்` and assimilate `ந்`: **`தொண்ணூறு`**.
  2. **`ஒன்பது` (or `ஒன்பஃது`) + `நூறு` -> `தொள்ளாயிரம்`**:
     - Step 1 (`முன்னதின் ஏனைய முரணி`): Transform `S2 = "நூறு"` -> `"ஆயிரம்"`: `ஒன்பது + ஆயிரம்`.
     - Step 2 (`ஒவ்வொடு தகரம் நிறீஇ`): Prefix `த்` onto initial `ஒ`: `தொன்பது + ஆயிரம்`.
     - Step 3 (`பஃது அகற்றி`): Delete final `பது` (or `பஃது`): `தொன் + ஆயிரம்`.
     - Step 4 (`னவ்வை நிரலே ... ள ஆ திரிப்பது`): Convert `ன் -> ள்`: `தொள் + ஆயிரம்`.
     - Step 5 (`நெறியே` + `தனிக்குறில் முன்னொற்று இரட்டித்தல்`, Sutra 205): Double `ள்` before vowel `ஆ`: **`தொள்ளாயிரம்`** (modern colloquial `தொளாயிரம்` noted in both commentaries).
- **Interactions & Precedence**:
  - Applies to both `ஒன்பது` and `ஒன்பஃது` as `S1`.
  - Step 5 invokes Sutra 205 (*thanikkuril munnorru uyirvarin irattum*).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஒன்பது / ஒன்பஃது | பத்து | தொண்ணூறு | Number (`9 × 10 = 90`) | 5-step rule (see above) | `viruttiyurai_pno=255`, `kandigai=194` |
  | ஒன்பது / ஒன்பஃது | நூறு | தொள்ளாயிரம் | Number (`9 × 100 = 900`) | 5-step rule (see above) | `viruttiyurai_pno=255`, `kandigai=194` |
- **Surface Signature & Reversibility**:
  - `தொண்ணூறு` -> `ஒன்பது + பத்து`; `தொள்ளாயிரம்` -> `ஒன்பது + நூறு`.

---

## Sutra 195 — Numerals `1..8 + பத்து` (`ஒருபது` / `ஒருபஃது` .. `எண்பது` / `எண்பஃது`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 256 | Kandigai: 195 | Poetic: No`
- **Root Text (TVA 1999)**:
  > முதலிறு நான்கா மெண்முனர்ப் பத்தின்
  > இடையொற் றேக லாய்த மாகல்
  > எனவிரு விதியு மேற்கு மென்ப.
- **Edition Diff vs `pmuni0147`**: **Textual Diff**: TVA 1999 reads `முதலிறு` (*mutaliṟu*), whereas `pmuni0147` (and Kandigaiyurai) reads `முதல் இரு` (*mutal iru*, i.e., `2 × 4 = 8`). Also sandhi-split (`முனர்` vs `முனர்ப்`).
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 ∈ {"ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "ஆறு", "ஏழு", "எட்டு"} (transformed per Sutras 188–193: ஒரு, இரு, முப், நாற், ஐம், அறு, எழு, எண்) AND S2 == "பத்து"`
     `THEN S2 ("பத்து") undergoes ONE of two optional rules:`
     - **Option A (`இடையொற்று ஏகல்`)**: Drop medial `த்` -> `"பது"` (`ஒருபது, இருபது, முப்பது, நாற்பது, ஐம்பது, அறுபது, எழுபது, எண்பது`).
     - **Option B (`ஆய்தம் ஆகல்`)**: Replace medial `த்` with `ஃ` -> `"பஃது"` (`ஒருபஃது, இருபஃது, முப்பஃது, நாற்பஃது, ஐம்பஃது, அறுபஃது, எழுபஃது, எண்பஃது`).
- **Interactions & Precedence**:
  - Applies after Sutras 188–193 transform `S1`.
  - Output feeds Sutra 196 when followed by `1..9`.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஒன்று | பத்து | ஒருபது / ஒருபஃது | Option A (`த்` drop) / Option B (`த்->ஃ`) | `ஒரு` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | இரண்டு | பத்து | இருபது / இருபஃது | Option A / Option B | `இரு` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | மூன்று | பத்து | முப்பது / முப்பஃது | Option A / Option B | `முப்` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | நான்கு | பத்து | நாற்பது / நாற்பஃது | Option A / Option B | `நாற்` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | ஐந்து | பத்து | ஐம்பது / ஐம்பஃது | Option A / Option B | `ஐம்` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | ஆறு | பத்து | அறுபது / அறுபஃது | Option A / Option B | `அறு` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | ஏழு | பத்து | எழுபது / எழுபஃது | Option A / Option B | `எழு` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
  | எட்டு | பத்து | எண்பது / எண்பஃது | Option A / Option B | `எண்` + `பது/பஃது` | `viruttiyurai_pno=256`, `kandigai=195` |
- **Surface Signature & Reversibility**:
  - `(ஒரு|இரு|முப்|நாற்|ஐம்|அறு|எழு|எண்)(பது|பஃது)` -> `S1 + பத்து`.

---

## Sutra 196 — Tens `10..80` (`ஒருபது/ஒருபஃது..எண்பது/எண்பஃது`) + `1..9`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 256, 257 | Kandigai: 196 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஒருபஃ தாதிமுன் னொன்றுமுத லொன்பான்
  > எண்ணு மவையூர் பிறவு மெய்தின்
  > ஆய்த மழியவாண் டாகுந் தவ்வே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஒருபஃது ஆதி முன் ஒன்று முதல் ஒன்பான் / எண் உம் அவை ஊர் பிற உம் எய்தின் / ஆய்தம் அழிய ஆண்டு ஆகும் த ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 ∈ {ஒருபஃது..எண்பஃது, ஒருபது..எண்பது} (both ஆய்தம் and non-ஆய்தம் forms per Viruttiyurai/Kandigai aruththapaththi) AND S2 ∈ {1..9, or compounds headed by 1..9 (அவையூர் பிறவும்)}`
     `THEN drop ஆய்தம் ("ஃ") if present, insert natural "த்" in its place (பது -> பத்த் + உ -> பத்து), and join S2 (eliding final உ before V per Sutra 164):`
     - `ஒருபஃது/ஒருபது + ஒன்று -> ஒருபத்தொன்று`
     - `இருபஃது + ஒன்றே காலேயரைக்கால் -> இருபத்தொன்றே காலேயரைக்கால்`
     - `முப்பஃது + ஒரு கழஞ்சு -> முப்பத்தொரு கழஞ்சு`
     - `எழுபஃது + ஒன்பதின் கலனே தூணி -> எழுபத்தொன்பதின் கலனேதூணி`
     - `எண்பஃது + எண் கலனே தூணி -> எண்பத்தெண் கலனே தூணி`
     - `எண்பஃது + ஒன்பது யாண்டு -> எண்பத்தொன்பதி யாண்டு`
- **Interactions & Precedence**:
  - Consumes output of Sutra 195 (`ஒருபது/ஒருபஃது..எண்பது/எண்பஃது`).
  - Before vowel-initial `S2` (`ஒன்று..ஒன்பது` except `மூன்று, நான்கு`), final `உ` of `-பத்து` elides via Sutra 164 (`பத்தொன்று`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஒருபஃது / ஒருபது | ஒன்று | ஒருபத்தொன்று | Number (`10 + 1`) | `ஃ -> த்` + `உ` elides | `viruttiyurai_pno=257`, `kandigai=196` |
  | இருபஃது / இருபது | ஒன்றே காலேயரைக்கால் | இருபத்தொன்றே காலேயரைக்கால் | Compound fraction | `ஃ -> த்` + `உ` elides | `viruttiyurai_pno=257`, `kandigai=196` |
  | முப்பஃது / முப்பது | ஒரு கழஞ்சு | முப்பத்தொரு கழஞ்சு | Number+Weight | `ஃ -> த்` + `உ` elides | `viruttiyurai_pno=257`, `kandigai=196` |
  | எழுபஃது / எழுபது | ஒன்பதின் கலனேதூணி | எழுபத்தொன்பதின் கலனேதூணி | Number+Measure | `ஃ -> த்` + `உ` elides | `viruttiyurai_pno=257` |
  | எண்பஃது / எண்பது | எண் கலனே தூணி | எண்பத்தெண் கலனே தூணி | Number+Measure | `ஃ -> த்` + `உ` elides | `kandigai=196` |
  | எண்பஃது / எண்பது | ஒன்பதி யாண்டு | எண்பத்தொன்பதி யாண்டு | Number+Other | `ஃ -> த்` + `உ` elides | `viruttiyurai_pno=257`, `kandigai=196` |
- **Surface Signature & Reversibility**:
  - `(ஒரு|இரு|முப்|நாற்|ஐம்|அறு|எழு|எண்)பத்த்...` -> `(S1_ten) + S2`.

---

## Sutra 197 — `பத்து` and `ஒன்பது` with `1..10, 1000, கோடி, நிறை, அளவு, பிற`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological/Lexical | Executable: Yes | Viruttiyurai pno: 257, 258 | Kandigai: 197 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஒன்றுமுத லீரைந் தாயிரங் கோடி
  > எண்ணிறை யளவும் பிறவரின் பத்தின்
  > ஈற்றுயிர் மெய்கெடுத் தின்னு மிற்றும்
  > ஏற்ப தேற்கு மொன்பது மினைத்தே
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஒன்று முதல் ஈர் ஐந்து ஆயிரம் கோடி / எண் நிறை அளவு உம் பிற வரின் பத்தின் / ஈற்று உயிர்மெய் கெடுத்து இன் உம் இற்று உம் / ஏற்பது ஏற்கும் ஒன்பது உம் இனைத்து ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **`S1 == "பத்து"`**:
     `IF S1 == "பத்து" AND S2 ∈ {1..10 (ஒன்று..பத்து), ஆயிரம், கோடி, Weight, Measure, Other}`
     `THEN drop S1.final_uyirmey ("து") -> "பத்" AND attach EITHER "-இன்" ("பதின்") OR "-இற்று" ("பதிற்று") as appropriate (ஏற்புழி):`
     - `-இன்` (typically *Ummaiththogai* / additive or before C/V): `பதினொன்று, பதின்மூன்று, பதினாயிரம், பதின் கழஞ்சு, பதின் கலம் / பதின்கலன், பதின் மடங்கு`.
     - `-இற்று` (typically *Panputhogai* / multiplicative): `பதிற்றொன்று, பதிற்றிரண்டு, பதிற்றுமூன்று, பதிற்றுக்கோடி, பதிற்றுத் தூணி`.
     - Natural form (`ஏற்பதேற்கும்`): `பத்துக்கோடி` (without `-இன்`/`-இற்று`).
  2. **`S1 == "ஒன்பது"`**:
     `IF S1 == "ஒன்பது" AND S2 ∈ {1..10, ஆயிரம், கோடி, Weight, Measure, Other}`
     `THEN drop ONLY S1.final_vowel "உ" (per Sutra 164, keeping "த்") -> "ஒன்பத்" AND attach EITHER "-இன்" ("ஒன்பதின்") OR "-இற்று" ("ஒன்பதிற்று") as appropriate:`
     - `-இன்`: `ஒன்பதினாயிரம், ஒன்பதின் கழஞ்சு, ஒன்பதின் கலம், ஒன்பதின் மடங்கு`.
     - `-இற்று`: `ஒன்பதிற்றொன்று, ஒன்பதிற்றிரண்டு, ஒன்பதிற்றுக் குறுணி`.
     - Natural form: `ஒன்பதுகோடி` / `ஒன்பது கோடி`.
- **Interactions & Precedence**:
  - Before `இரண்டு` in additive *Ummaiththogai*, Sutra 198 (`பன்னிரண்டு`) overrides `-இன்` (note Viruttiyurai fn. 191 citing Mayilainathar: `பத்தின் முன் இரண்டும் ஒன்பதும் பத்தும் வருவழி இன்னும், ஆயிரம் வருவழி இற்றும், ஒன்பதன் முன் ஒன்று முதல் பத்து எண்ணும் வருவழி இன்னும் வாரா`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பத்து | ஒன்று | பதினொன்று | Ummaiththogai (`10+1`) | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | மூன்று | பதின்மூன்று | Ummaiththogai (`10+3`) | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | ஆயிரம் | பதினாயிரம் | Multiplicative (`10×1000`) | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | கழஞ்சு | பதின் கழஞ்சு | Weight | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | கலம் / கலன் | பதின் கலம் / பதின்கலன் | Measure | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | மடங்கு | பதின் மடங்கு | Other | `து` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | ஒன்று | பதிற்றொன்று | Panputhogai (`10×1`) | `து` drop + `-இற்று` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | இரண்டு | பதிற்றிரண்டு | Panputhogai (`10×2`) | `து` drop + `-இற்று` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | மூன்று | பதிற்றுமூன்று | Panputhogai (`10×3`) | `து` drop + `-இற்று` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | கோடி | பதிற்றுக்கோடி | Panputhogai; vs `பத்துக்கோடி` | `து` drop + `-இற்று` | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | தூணி | பதிற்றுத் தூணி | Measure | `து` drop + `-இற்று` + `த்` doubles | `viruttiyurai_pno=257`, `kandigai=197` |
  | பத்து | கோடி | பத்துக்கோடி | Natural (`ஏற்பதேற்கும்`) | `க்` doubles | `viruttiyurai_pno=258`, `kandigai=197` |
  | ஒன்பது | ஆயிரம் | ஒன்பதினாயிரம் | Number (`9×1000`) | `உ` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | ஒன்பது | கழஞ்சு | ஒன்பதின் கழஞ்சு | Weight | `உ` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | ஒன்பது | கலம் | ஒன்பதின் கலம் | Measure | `உ` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | ஒன்பது | மடங்கு | ஒன்பதின் மடங்கு | Other | `உ` drop + `-இன்` | `viruttiyurai_pno=257`, `kandigai=197` |
  | ஒன்பது | ஒன்று | ஒன்பதிற்றொன்று | Panputhogai | `உ` drop + `-இற்று` | `viruttiyurai_pno=258`, `kandigai=197` |
  | ஒன்பது | இரண்டு | ஒன்பதிற்றிரண்டு | Panputhogai | `உ` drop + `-இற்று` | `viruttiyurai_pno=258`, `kandigai=197` |
  | ஒன்பது | குறுணி | ஒன்பதிற்றுக் குறுணி | Measure | `உ` drop + `-இற்று` + `க்` doubles | `viruttiyurai_pno=258`, `kandigai=197` |
  | ஒன்பது | கோடி | ஒன்பதுகோடி / ஒன்பது கோடி | Natural (`ஏற்பதேற்கும்`) | Natural | `viruttiyurai_pno=258`, `kandigai=197` |
- **Surface Signature & Reversibility**:
  - `பதின்-`, `பதிற்று-`, `பதிற்ற்-` -> `பத்து + S2`; `ஒன்பதின்-`, `ஒன்பதிற்று-`, `ஒன்பதிற்ற்-` -> `ஒன்பது + S2`.

---

## Sutra 198 — `பத்து + இரண்டு -> பன்னிரண்டு`

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Morphological | Executable: Yes | Viruttiyurai pno: 258, 259 | Kandigai: 198 | Poetic: No`
- **Root Text (TVA 1999)**:
  > இரண்டு முன்வரிற் பத்தினீற் றுயிர்மெய்
  > கரந்திட வொற்றனவ் வாகு மென்ப.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`இரண்டு முன் வரின் பத்தின் ஈற்று உயிர்மெய் / கரந்திட ஒற்று ன ஆகும் என்ப`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == "பத்து" AND S2 == "இரண்டு" AND compound_type == Ummaiththogai (additive 10 + 2 = 12)`
     `THEN drop S1.final_uyirmey ("து") AND convert remaining "த்" to "ன்" => "பன்" + "இரண்டு" -> (doubling ன் after short vowel per Sutra 205) "பன்னிரண்டு".`
  2. `IF compound_type == Panputhogai (multiplicative 10 × 2)`
     `THEN Sutra 197 applies -> "பதிற்றிரண்டு".`
- **Interactions & Precedence**:
  - Specific override for `பத்து + இரண்டு` in *Ummaiththogai* over Sutra 197 (`-இன்`).
  - Feeds Sutra 205 (`தனிக்குறின் முன்னொற்றுயிர்வரின் இரட்டும்`: `பன் + இரண்டு -> பன்னிரண்டு`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பத்து | இரண்டு | பன்னிரண்டு | Ummaiththogai (`10 + 2 = 12`) | `து` drop, `த் -> ன்`, `ன்` doubles | `viruttiyurai_pno=259`, `kandigai=198` |
- **Surface Signature & Reversibility**:
  - `பன்னிரண்டு` -> `பத்து + இரண்டு` (Ummaiththogai).

---

## Sutra 199 — Distributive Reduplication of Numerals `1..8, 10` (Excluding `9`)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphological | Executable: Yes | Viruttiyurai pno: 259, 260 | Kandigai: 199 | Poetic: No`
- **Root Text (TVA 1999)**:
  > ஒன்ப தொழித்தவெண் ணொன்பது மிரட்டின்
  > முன்னதின் முன்னல வோட வுயிர் வரின்
  > வவ்வு மெய்வரின் வந்தது மிகனெறி.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`ஒன்பது ஒழித்த எண் ஒன்பது உம் இரட்டின் / முன்னதின் முன் அல ஓட உயிர் வரின் / வ உம் மெய் வரின் வந்தது உம் மிகல் நெறி`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == S2 AND S1 ∈ {"ஒன்று", "இரண்டு", "மூன்று", "நான்கு", "ஐந்து", "ஆறு", "ஏழு", "எட்டு", "பத்து"} (i.e., excluding "ஒன்பது") AND distributive_reduplication == True`
     `THEN retain ONLY S1.first_letter (முன்னதின் முன், dropping all remaining letters of S1; with "நான்" shortened to "ந" and "ஐ" shortened as ஐகாரக்குறுக்கம் without doubling), AND:`
     - `IF S2.initial ∈ Vowel` -> insert `வ்` (doubled after short vowel `ஒ/இ/அ/எ`: `ஒவ்வொன்று, இவ்விரண்டு, அவ்வாறு, எவ்வேழு, எவ்வெட்டு`; single `வ்` after `ஐ`: `ஐவைந்து`).
     - `IF S2.initial ∈ Consonant` -> double `S2.initial` (`மும்மூன்று, நந்நான்கு, பப்பத்து`).
  2. **Additional / Optional Forms (`நெறி` extension)**:
     - Viruttiyurai & Kandigai also note: `ஒரோவொன்று` / `ஒரோவென்று`, `ஒன்றொன்று`, `கழக்கழஞ்சு`, `கலக்கலம்` (and fn. 194 notes `பத்துப்பத்து`, `பதிற்றுப்பத்து`).
- **Interactions & Precedence**:
  - Viruttiyurai notes this is *Alvazhi* (*thazhaaththodar*), NOT *adukkuththodar*.
  - Footnote 195 clarifies that `வ்` in `ஒவ்வொன்று, அவ்வாறு` is NOT an *udambadumey* (glide) but an explicit rule-inserted consonant.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | ஒன்று | ஒன்று | ஒவ்வொன்று | Distributive (V-initial) | `ஒ` + `வ்` (doubled) + `ஒன்று` | `viruttiyurai_pno=259`, `kandigai=199` |
  | இரண்டு | இரண்டு | இவ்விரண்டு | Distributive (V-initial) | `இ` + `வ்` (doubled) + `இரண்டு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | மூன்று | மூன்று | மும்மூன்று | Distributive (C-initial) | `மு` + `ம்` + `மூன்று` | `viruttiyurai_pno=259`, `kandigai=199` |
  | நான்கு | நான்கு | நந்நான்கு | Distributive (C-initial) | `ந` (short) + `ந்` + `நான்கு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | ஐந்து | ஐந்து | ஐவைந்து | Distributive (V-initial, short `ஐ`) | `ஐ` + `வ்` (single) + `ஐந்து` | `viruttiyurai_pno=259`, `kandigai=199` |
  | ஆறு | ஆறு | அவ்வாறு | Distributive (V-initial) | `அ` + `வ்` (doubled) + `ஆறு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | ஏழு | ஏழு | எவ்வேழு | Distributive (V-initial) | `எ` + `வ்` (doubled) + `ஏழு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | எட்டு | எட்டு | எவ்வெட்டு | Distributive (V-initial) | `எ` + `வ்` (doubled) + `எட்டு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | பத்து | பத்து | பப்பத்து | Distributive (C-initial) | `ப` + `ப்` + `பத்து` | `viruttiyurai_pno=259`, `kandigai=199` |
  | ஒன்று | ஒன்று | ஒரோவென்று / ஒரோவொன்று / ஒன்றொன்று | Alternate (`நெறி`) | Lexical/Natural | `viruttiyurai_pno=259`, `kandigai=199` |
  | கழஞ்சு | கழஞ்சு | கழக்கழஞ்சு | Measure reduplication (`நெறி`) | `கழ` + `க்` + `கழஞ்சு` | `viruttiyurai_pno=259`, `kandigai=199` |
  | கலம் | கலம் | கலக்கலம் | Measure reduplication (`நெறி`) | `கல` + `க்` + `கலம்` | `viruttiyurai_pno=259` |
- **Surface Signature & Reversibility**:
  - `ஒவ்வொன்று, இவ்விரண்டு, மும்மூன்று, நந்நான்கு, ஐவைந்து, அவ்வாறு, எவ்வேழு, எவ்வெட்டு, பப்பத்து` -> `N + N`.

---

## Sutra 200 — `பூ`-Final Special Rule (Nasal or Stop Insertion)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical | Executable: Yes | Viruttiyurai pno: 260 | Kandigai: 200 | Poetic: No`
- **Root Text (TVA 1999)**:
  > பூப்பெயர் முன்னின மென்மையுந் தோன்றும்.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`பூ பெயர் முன் இன மென்மை உம் தோன்றும்`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. `IF S1 == "பூ" (polysemous noun: flower / beauty) AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN in addition to default vallinam doubling (Sutra 165: பூ + கொடி -> பூக்கொடி), homorganic nasal insertion (இன மென்மை) ALSO occurs -> ங், ஞ், ந், ம்:`
     - `க் -> ங்` (`பூங்கொடி, பூங்கணை, பூங்கரும்பு`)
     - `ச் -> ஞ்` (`பூஞ்சோலை`)
     - `த் -> ந்` (`பூந்தடம்`)
     - `ப் -> ம்` (`பூம்பணை`)
     - Note: Viruttiyurai notes these are NOT free *urazhvu* in every compound, but distributed by usage/meaning (`ஏற்றபெற்றி`).
- **Interactions & Precedence**:
  - Extends Sutra 165 (*vallinam* doubling) by adding homorganic nasal insertion as a co-occurring pattern for `பூ`.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பூ | கொடி | பூங்கொடி | Nasal insertion (2nd-case/Panpu) | Insert `ங்` | `viruttiyurai_pno=260`, `kandigai=200` |
  | பூ | கொடி | பூக்கொடி | Stop doubling (Sutra 165) | Insert `க்` | `viruttiyurai_pno=260` |
  | பூ | சோலை | பூஞ்சோலை | Nasal insertion | Insert `ஞ்` | `viruttiyurai_pno=260`, `kandigai=200` |
  | பூ | தடம் | பூந்தடம் | Nasal insertion | Insert `ந்` | `viruttiyurai_pno=260`, `kandigai=200` |
  | பூ | பணை | பூம்பணை | Nasal insertion | Insert `ம்` | `viruttiyurai_pno=260`, `kandigai=200` |
  | பூ | கணை | பூங்கணை | Nasal insertion (3rd-case/Panpu) | Insert `ங்` | `viruttiyurai_pno=260` |
  | பூ | கரும்பு | பூங்கரும்பு | Nasal insertion (Panpu) | Insert `ங்` | `viruttiyurai_pno=260` |
- **Surface Signature & Reversibility**:
  - `பூ[ங்ஞ்ந்ம்][க்ச்த்ப்]...` or `பூ[க்ச்த்ப்]{2}...` -> `பூ + S2`.

---

## Sutra 201 — `ஏ` and `ஓ` Clitic Particles (*Idaichol*)

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Morphosyntactic | Executable: Yes (with particle/POS tag) | Viruttiyurai pno: 260, 261 | Kandigai: 201 | Poetic: No`
- **Root Text (TVA 1999)**:
  > இடைச்சொல் லேயோ முன்வரி னியல்பே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`இடைச்சொல் ஏ ஓ முன் வரின் இயல்பு ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Adjacency Direction**: `S1` ends in clitic particle `ஏ` or `ஓ` (i.e., `ஏ`/`ஓ` is the *nilaimozhi* final, BEFORE `S2`), and `S2.initial ∈ {க், ச், த், ப்}` (`முன் வரின்` = "when [vallinam] comes before/after `ஏ`/`ஓ`").
  2. **Scope of `ஏ` and `ஓ` Particles**:
     `IF S1.final_clitic ∈ {ஏ (6 senses: பிரிநிலை, வினா, எண், ஈற்றசை, தேற்றம், இசைநிறை), ஓ (8 senses: ஒழியிசை, வினா, சிறப்பு, எதிர்மறை, தெரிநிலை, கழிவு, பிரிநிலை, அசைநிலை)} AND S2.initial ∈ {க், ச், த், ப்}`
     `THEN S2.initial remains Natural (இயல்பு) — NO vallinam doubling (blocks Sutra 165).`
     - Note (Viruttiyurai fn. 196): Vaithiyanatha Desikar (following Tolkappiyam) excludes *thetram* (`தேற்றம்`) and *sirappu* (`சிறப்பு`), whereas Viruttiyurai & Kandigai explicitly include all 6 senses of `ஏ` (cross-ref Sutra 422) and all 8 senses of `ஓ` (cross-ref Sutra 423).
- **Interactions & Precedence**:
  - Blocks Sutra 165 (*vallinam* doubling) after `ஏ`/`ஓ` clitics.
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | அவனே | கொண்டான் | அவனே கொண்டான் | `ஏ` (பிரிநிலை/வினா/ஈற்றசை/தேற்றம்); Natural | Natural | `viruttiyurai_pno=261`, `kandigai=201` |
  | அறமே | பொருளே (காமமே துறவே) | அறமே பொருளே காமமே துறவே | `ஏ` (எண்); Natural | Natural | `viruttiyurai_pno=261` |
  | ஏஎ | தனை | ஏஎதனை | `ஏ` (இசைநிறை); Natural | Natural | `viruttiyurai_pno=261`, `kandigai=201` *(Kandigai prints `ஏயே தனை`)* |
  | அவனோ | கொண்டான் | அவனோ கொண்டான் | `ஓ` (ஒழியிசை முதலிய 8); Natural | Natural | `viruttiyurai_pno=261`, `kandigai=201` |
- **Surface Signature & Reversibility**:
  - `...[ஏஓ] [க்ச்த்ப்]...` -> no gemination at boundary.

---

## Sutra 202 — `ஐ`-Final Stems Taking `அம்` *Chariyai* in *Vetrumai*

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical/Morphological | Executable: Yes (Lexicon-gated) | Viruttiyurai pno: 261, 262 | Kandigai: 202 | Poetic: No`
- **Root Text (TVA 1999)**:
  > வேற்றுமை யாயி னைகா னிறுமொழி
  > ஈற்றழி வோடுமம் மேற்பவு முளவே.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`வேற்றுமை ஆயின் ஐகான் இறு மொழி / ஈற்று அழிவு ஓடு உம் அம் ஏற்ப உம் உள ஏ`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  1. **Pattern A (Retain `ஐ` + `-அம்`)**:
     `IF S1 ∈ AI_Retain_Am_Lexicon (e.g., "புன்னை", "கொல்லை", "கொன்றை", "முல்லை") AND context == Vetrumai`
     `THEN S1 retains final "ஐ", inserts "ய்" glide (Sutra 162) + "-அம்" -> "S1 + யம்" + S2` (and `ம்` assimilates before `க்/ச்/த்/ப்` or stays `ம்` before `வ்`/etc.).
     - Optionality: `முல்லை + புறவம்` also allows standard `முல்லைப்புறவம்` (without `-அம்`).
  2. **Pattern B (Drop `ஐ` + `-அம்`)**:
     `IF S1 ∈ AI_Drop_Am_Lexicon (e.g., "வழுதுணை", "ஆவிரை", "தாழை") AND context == Vetrumai`
     `THEN S1 drops final "ஐ" and takes "-அம்" -> "S1_stem + அம்" + S2` (with `ம்` assimilating before stops: `வழுதுணங்காய்`, or remaining `ம்`: `தாழம்பூ`, `ஆவிரம்பூ`, `ஆவிரம்வேர்`).
- **Interactions & Precedence**:
  - `S1 + யம்` uses Sutra 162 (`ய்` glide after `ஐ`).
  - Final `ம்` of `-அம்` undergoes nasal assimilation (`ம் -> ங்/ஞ்/ந்/ம்`) before stops (cf. *Meyyīṟṟup Puṇariyal*).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | புன்னை | கானல் | புன்னையங் கானல் | Vetrumai; Pattern A (`ஐ` retained + `அம்`) | `+யம்`, `ம் -> ங்` | `viruttiyurai_pno=261`, `kandigai=202` |
  | கொல்லை | சாரல் | கொல்லையஞ் சாரல் | Vetrumai; Pattern A | `+யம்`, `ம் -> ஞ்` | `viruttiyurai_pno=261` |
  | கொன்றை | தீங்குழல் | கொன்றையந் தீங்குழல் | Vetrumai; Pattern A | `+யம்`, `ம் -> ந்` | `viruttiyurai_pno=261` |
  | முல்லை | புறவம் | முல்லையம் புறவம் / முல்லைப்புறவம் | Vetrumai; Pattern A / Standard | `+யம்` / `ப்` doubles | `viruttiyurai_pno=261`, `kandigai=202` |
  | வழுதுணை | காய் | வழுதுணங்காய் | Vetrumai; Pattern B (`ஐ` dropped + `அம்`) | `ஐ -> அம்`, `ம் -> ங்` | `viruttiyurai_pno=261`, `kandigai=202` |
  | தாழை | பூ | தாழம்பூ | Vetrumai; Pattern B | `ஐ -> அம்` | `kandigai=202` |
  | ஆவிரை | பூ | ஆவிரம்பூ | Vetrumai; Pattern B | `ஐ -> அம்` | `viruttiyurai_pno=261` |
  | ஆவிரை | வேர் | ஆவிரம்வேர் | Vetrumai; Pattern B | `ஐ -> அம்` | `viruttiyurai_pno=261`, `kandigai=202` |
- **Surface Signature & Reversibility**:
  - `...ைய[ங்ஞ்ந்ம்]...` or `...[ங்ஞ்ந்ம்][க்ச்த்ப்]...` on `ஐ`-final botanical/landscape nouns.

---

## Sutra 203 — `பனை` Special Rules in *Vetrumai*

- **Metadata**: `Chapter: Uyirīṟṟup Puṇariyal | Tier: Lexical | Executable: Yes | Viruttiyurai pno: 262 | Kandigai: 203 | Poetic: No`
- **Root Text (TVA 1999)**:
  > பனைமுன் கொடிவரின் மிகலும் வலிவரின்
  > ஐபோ யம்முந் திரள்வரி னுறழ்வும்
  > அட்டுறி னைகெட்டந் நீள்வுமாம் வேற்றுமை.
- **Edition Diff vs `pmuni0147`**: Sandhi-split vs joined only (`பனை முன் கொடி வரின் மிகல் உம் வலி வரின் / ஐ போய் அம் உம் திரள் வரின் உறழ்வு உம் / அட்டு உறின் ஐ கெட்டு அ நீள்வு உம் ஆம் வேற்றுமை`); identical words.
- **Atomic Sub-Rules (`IF -> THEN`)**:
  All sub-rules require `S1 == "பனை"` AND `context == Vetrumai`:
  1. `IF S2 == "கொடி"`
     `THEN S2.initial doubles -> "பனைக்கொடி" (preserving Sutra 165).`
  2. `IF S2 == "திரள்"`
     `THEN OPTIONAL (உறழ்வு): EITHER stop doubling -> "பனைத்திரள்" OR drop "ஐ" + "-அம்" -> "பனந்திரள்".`
  3. `IF S2.initial ∈ {க், ச், த், ப்} AND S2 ∉ {"கொடி", "திரள்"}`
     `THEN drop "ஐ" and attach "-அம்" ("பனம்" + S2, with ம் assimilating to ங்/ஞ்/ந்/ம் -> "பனங்காய், பனஞ்செறும்பு, பனந்தூண், பனம்பழம்").`
  4. `IF S2 == "அட்டு"`
     `THEN drop "ஐ" ("பன்") AND lengthen S2.initial "அ -> ஆ" ("ஆட்டு") -> "பனாட்டு".`
- **Interactions & Precedence**:
  - Sub-rules 1 (`கொடி`) and 2 (`திரள்`) take precedence over Sub-rule 3 (general `வலி வரின்`).
  - Sub-rule 4 (`அட்டு`) overrides Sutra 162 (`ய்` glide) and Sutra 205 (no doubling of `ன்` since `ஆ` is long after `பன்` -> `பனாட்டு`).
- **Attested Examples**:
  | First (`S1`) | Second (`S2`) | Surface | Context / Optionality | Transform | Witness |
  | :--- | :--- | :--- | :--- | :--- | :--- |
  | பனை | கொடி | பனைக்கொடி | Vetrumai; Stop doubling | Insert `க்` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | காய் | பனங்காய் | Vetrumai; `ஐ` drop + `அம்` | `பனம் + காய் -> பனங்காய்` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | செறும்பு | பனஞ்செறும்பு | Vetrumai; `ஐ` drop + `அம்` | `பனம் + செறும்பு -> பனஞ்செறும்பு` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | தூண் | பனந்தூண் | Vetrumai; `ஐ` drop + `அம்` | `பனம் + தூண் -> பனந்தூண்` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | பழம் | பனம்பழம் | Vetrumai; `ஐ` drop + `அம்` | `பனம் + பழம் -> பனம்பழம்` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | திரள் | பனைத்திரள் / பனந்திரள் | Vetrumai; Optional (`உறழ்வு`) | Insert `த்` / `பனம் + திரள்` | `viruttiyurai_pno=262`, `kandigai=203` |
  | பனை | அட்டு | பனாட்டு | Vetrumai; `ஐ` drop + `அ -> ஆ` | `பன் + ஆட்டு -> பனாட்டு` | `viruttiyurai_pno=262`, `kandigai=203` |
- **Surface Signature & Reversibility**:
  - `பனைக்கொடி`, `பன[ங்ஞ்ந்ம்]...`, `பனைத்திரள்`, `பனாட்டு` -> `பனை + S2`.

---

## Batch Summary: Missing Rules, Edge Cases & Context Enums Needed (178–203)

1. **Edition Variants (`TVA 1999` vs `pmuni0147` / `Kandigai`)**:
   - **Sutra 195**: TVA 1999 has `முதலிறு நான்காம்` vs `pmuni0147` / Kandigai `முதல் இரு நான்காம்`. Both denote `1..8`, so the engine should normalize the sutra reference to the `1..8` numeral set.
2. **Required Context & Semantic Enums**:
   - `CompoundRelation`: `Alvazhi`, `Vetrumai`, `Panputhogai`, `Ummaiththogai`, `Vinaiththogai`, `Anmolithogai`, `Ilakkanappoli`. (Crucial for distinguishing `பதின்/பன்னிரண்டு` vs `பதிற்று`, `வன்றொடர்` vs `மென்றொடர்` behavior in Sutras 181–184, 197–198.)
   - `RegisterFlag`: `Poetic` (`தூக்கின்`, Sutra 180 `அதான்று`), `Colloquial` (`பீந்தோல்` in 178, `தொளாயிரம்` in 194).
   - `KurriyalugaramClass`: `{Vanthodar, Menthodar, Idaithodar, Nedilthodar, Uyirthodar, Aaydathodar}` (Sutras 181–185).
   - `SemanticClass` for numerals (188–199): `{Number, Weight (நிறை), Measure (அளவு), Other (பிற)}`.
   - `DistributiveReduplication` flag (Sutra 199).
3. **Lexicon Tables Needed**:
   - `Mutriyalugaram_Natural_Words`: Case 3 (`-ஒடு`), Case 6 (`-அது`), `Vinaiththogai` verb stems, demonstratives (`அது, இது, உது`) + exception `உது காண் / உதுக் காண்` (179).
   - `Menthodar_Locative_Particles` (`அங்கு..யாண்டு`, double stops) vs `Temporal_Particles` (`அன்று..முந்து`, natural) (181).
   - `Nedil_Uyir_Doubling_Exceptions` (`நாடு கிழவோன்`, `காடகம்`, `மிடறணியல்`; *Alvazhi* doublers `காட்டரண்`, `களிற்றுயானை`, `ஏற்றேனம்`, `வரட்டாடு`, `குருட்டுக்கோழி`, `வெளிற்றுப்பனை`; other-stop doublers `வெருக்குக்கண்`, `எருத்துக்கால்`, `எருத்து மாடு`) (183).
   - `Menthodar_Vanthodar_Lexicon` (`மருந்து, சுரும்பு, கரும்பு, கன்று` in *Vetrumai*; `என்பு, அன்பு, குரங்கு` in *Alvazhi*) (184).
   - `Kurriyalugaram_AI_Lexicon` (`பண்டு, இன்று, அன்று, நேற்று, ஒன்று, இரண்டு, வேட்டு, ஓராண்டு, ஈராண்டு, மூவாண்டு`) (185).
   - `Direction_Stems` (`வடக்கு, தெற்கு, மேற்கு, கிழக்கு, குடக்கு, குணக்கு`) and `-ஐ` variants (`மேலை, கீழை`) (186).
   - `AI_Am_Chariyai_Lexicon`: Retain-`ஐ` (`புன்னை, கொல்லை, கொன்றை, முல்லை`) vs Drop-`ஐ` (`வழுதுணை, ஆவிரை, தாழை`) (202).
4. **Cross-Chapter Dependencies**:
   - Sutras 186 (`மேனாடு`), 191 (`நானாழி`), 193 (`எண்ணாழி`), 194 (`தொண்ணூறு`), 202 (`புன்னையங் கானல்`, etc.), 203 (`பனங்காய்`, etc.) depend on **Meyyīṟṟup Puṇariyal** nasal/lateral sandhi (`ல்+ந்->ன்`, `ன்+ந்->ன்/ன`, `ண்+ந்->ண்ண`, `ம் -> ங்/ஞ்/ந்`).
   - Sutras 193 (`எண்ணைந்து`), 194 (`தொள்ளாயிரம்`), 198 (`பன்னிரண்டு`), 199 (`ஒவ்வொன்று..`) depend on Sutra 205 (*thanikkuril munnorru uyirvarin irattum*).
