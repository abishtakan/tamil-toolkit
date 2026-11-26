# Nannool Prerequisites Research: Ezhuttiyal (93–94, 102–108) & Padaviyal (136)

- **Feature**: `025-tamil-punarchi` (Phase R1.0 — Prerequisites Extraction)
- **Source Bundle**: `bundle_00_prerequisites.md` (10 sutras: `93, 94, 102, 103, 104, 105, 106, 107, 108, 136`)
- **Primary Witnesses**:
  - **TVA 1999 Critical Edition**: Nannool Viruttiyurai (Thamodaran, bookid=6, auth_pub_id=17)
  - **TVA Kandigaiyurai**: Arumuka Navalar Kandigaiyurai (bookid=6, auth_pub_id=15)
  - **Project Madurai 1926**: Vavilla Edition (`pmuni0147.html`)

---

## Sutra 93

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — பிறப்பு / குற்றியலிகரம்)
- **Tier**: Core Phonology / Sandhi Prerequisite
- **TVA Viruttiyurai**: [pno=166](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=166)
- **TVA Kandigaiyurai**: [sutra=93](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=93&y=93)

### Root Text (TVA 1999 Critical Edition)

```text
யகரம் வரக்குற ளுத்திரி யிகரமும்
அசைச்சொன் மியாவி னிகரமுங் குறிய.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  யகரம் வர குறள் உ திரி இகரம் உம்
  அசைச்சொல் மியாவின் இகரம் உம் குறிய
  ```
- **Diff**: `pmuni0147` uses un-sandhied word-separated orthography (`வர குறள் உ திரி இகரம் உம் / அசைச்சொல் மியாவின் இகரம் உம் குறிய`) vs TVA 1999 metrical sandhi (`வரக்குற ளுத்திரி யிகரமும் / அசைச்சொன் மியாவி னிகரமுங் குறிய`). No lexical divergence.

### Atomic Sub-Rules (`IF -> THEN`)

1. **R93.1 — Sandhi-derived *Kurriyaligaram* (`குற்றியலிகரம்`)**:
   - **IF**: `first` ends in a *Kurriyalugaram* (`கு, சு, டு, து, பு, று` classified under Sutra 94; 36 subtypes) AND `second` begins with `ய` (`ய் + vowel`, e.g., `யாது`).
   - **THEN**: The final `உ` of `first` mutates (`திரிதல்` / `thirithal`) to *Kurriyaligaram* `இ` (`Cu + y... -> Ci + y...`).
   - **Alteration Class**: `thirithal` (திரிதல்).
   - **Optionality**: Obligatory in classical *punarchi* (cross-referenced by Viruttiyurai pno=166 to Sutra 164).
2. **R93.2 — Lexical/Particle *Kurriyaligaram* (`மியா`)**:
   - **IF**: The form contains the expletive/hortative particle (`அசைச்சொல்`) `மியா` (e.g., suffixed to imperatives `கேள் + மியா -> கேண்மியா`, `செல் + மியா -> சென்மியா`).
   - **THEN**: The `இ` in `மி` (`ம் + இ`) is classified prosodically as *Kurriyaligaram* (shortened from 1 *matra* to 1/2 *matra*).
   - **Alteration Class**: `iyalbu` (for the vowel `இ` itself; note that stem-final `ள் -> ண்` and `ல் -> ன்` in `கேண்மியா`/`சென்மியா` follow nasal assimilation before `ம்`).
   - **Count**: `36` (*kurriyalugaram* subtypes before `ய`) + `1` (`மியா`) = `37` *kurriyaligaram* instances (`முப்பத்தேழு`).

### Deep-Dive: Interaction with Sutra 164

- Sutra 93 in *Ezhuttiyal* defines the phonological class *Kurriyaligaram* and enumerates its 37 instances.
- Viruttiyurai pno=166 explicitly links the `உ -> இ` mutation to **Sutra 164** (*Uyireetru Punariyal*): Sutra 164 states the operational sandhi rule that *kurriyalugaram* before `ய` mutates to `இ` (and does not elide as it would before vowels by `உயிர்வரின் உக்குறள் மெய்விட்டோடும்`).
- Thus, Sutra 93 provides the **classification & inventory**, while Sutra 164 provides the **junction trigger**.

### Attested Examples

| First | Second | Surface | Transform | Witness | Notes |
| --- | --- | --- | --- | --- | --- |
| `நாகு` | `யாது` | `நாகியாது` / `நாகி யாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166`, `kandigai=93` | Nedil-thodar |
| `எஃகு` | `யாது` | `எஃகியாது` / `எஃகி யாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166`, `kandigai=93` | Aythath-thodar |
| `வரகு` | `யாது` | `வரகியாது` / `வரகி யாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166`, `kandigai=93` | Uyir-thodar |
| `கொக்கு` | `யாது` | `கொக்கியாது` / `கொக்கி யாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166`, `kandigai=93` | Vanthodar |
| `குரங்கு` | `யாது` | `குரங்கியாது` / `குரங்கி யாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166`, `kandigai=93` | Menthodar |
| `அல்கு` | `யாது` | `அல்கியாது` | `thirithal` (`கு -> கி`) | `viruttiyurai_pno=166` | Idaithodar |
| `தெள்கு` | `யாது` | `தெள்கியாது` | `thirithal` (`கு -> கி`) | `kandigai=93` | Idaithodar |
| `கேள்` | `மியா` | `கேண்மியா` | `iyalbu` (`மி` is kurriyaligaram) + `ள் -> ண்` | `viruttiyurai_pno=166`, `kandigai=93` | Particle `மியா` |
| `செல்` | `மியா` | `சென்மியா` | `iyalbu` (`மி` is kurriyaligaram) + `ல் -> ன்` | `viruttiyurai_pno=166` | Particle `மியா` |

### Surface Signature & Reversibility (`split.rs`)

- **Surface signature**: `<prefix><C_v>இ<y_vowel><rest>` (or space-separated `<prefix><C_v>இ ய<rest>`) where `C_v ∈ {க, ச, ட, த, ப, ற}` (i.e., `கி, சி, டி, தி, பி, றி` followed by `ய-`).
- **Reversibility**: When `split.rs` encounters `...<C_v>இ` immediately before `ய...`, it should generate a candidate split restoring `<prefix><C_v>உ` + `ய<rest>`, **only if** `<prefix><C_v>உ` is classified as *Kurriyalugaram* under Sutra 94 (never for *Mutriyalugaram* like `பசு`, `அது`, which do not undergo `u -> i` before `ய`).

---

## Sutra 94

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — பிறப்பு / குற்றியலுகரம்)
- **Tier**: Core Phonology / Sandhi Prerequisite
- **TVA Viruttiyurai**: [pno=166](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=166), [pno=167](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=167), [pno=168](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=168)
- **TVA Kandigaiyurai**: [sutra=94](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=94&y=94)

### Root Text (TVA 1999 Critical Edition)

```text
நெடிலோ டாய்த முயிர்வலி மெலியிடைத்
தொடர்மொழி யிறுதி வன்மையூ ருகரம்
அஃகும் பிறமேற் றொடரவும் பெறுமே.
```

*(Note: Viruttiyurai footnote 86 records Sankara Namachivayar's variant `நெடிலொ டாய்த...` with short `ஒ`.)*

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  நெடில் ஓடு ஆய்தம் உயிர் வலி மெலி இடை
  தொடர் மொழி இறுதி வன்மை ஊர் உகரம்
  அஃகும் பிற மேல் தொடர உம் பெறும் ஏ
  ```
- **Diff**: `pmuni0147` separates sandhied words (`நெடில் ஓடு ஆய்தம்...`, `தொடர உம் பெறும் ஏ`) vs TVA 1999 (`நெடிலோ டாய்த...`, `தொடரவும் பெறுமே`). No lexical divergence.

### Atomic Sub-Rules (`IF -> THEN`)

1. **R94.1 — *Kurriyalugaram* 6-class Condition**:
   - **IF**: A word ends in `உ` mounted on a vallinam consonant (`C_v ∈ {க், ச், ட், த், ப், ற்}`, i.e., final *uyirmei* in `{கு, சு, டு, து, பு, று}`), AND its penultimate phonological unit (*eetru-ayal*) is one of 36 valid predecessors:
     - `7` single long vowels (`தனிநெடில்`: `ஆ, ஈ, ஊ, ஏ, ஐ, ஓ, ஔ`), OR
     - `1` aytham (`ஃ`), OR
     - `11` vowels (`உயிர்`: all 12 vowels except `ஔ`, which never occurs medially/finally) in a polysyllabic word (`பிறமேல் தொடரவும் பெறும்`), OR
     - `6` vallinam pure consonants (`வலி`: `க், ச், ட், த், ப், ற்`), OR
     - `6` mellinam pure consonants (`மெலி`: `ங், ஞ், ண், ந், ம், ன்`), OR
     - `5` idaiyinam pure consonants (`இடை`: `ய், ர், ல், ழ், ள்`; `வ்` is excluded because it never clusters before vallinam).
   - **THEN**: The final `உ` shortens (`அஃகும்` — 1/2 *matra*) and belongs to the corresponding *Kurriyalugaram* class (`நெடில்தொடர்`, `ஆய்தத்தொடர்`, `உயிர்த்தொடர்`, `வன்தொடர்`, `மென்தொடர்`, `இடைத்தொடர்`).
   - **Alteration Class**: `iyalbu` (prosodic/phonological classification).
2. **R94.2 — *Mutriyalugaram* Exclusion (`பிறமேற் றொடரவும் பெறுமே`)**:
   - **IF**: The final `உ` is mounted on a non-vallinam consonant (`மெய் ∉ {க், ச், ட், த், ப், ற்}`), OR the word is a 2-unit short-vowel `C?V_short + C_v u` (e.g., `அது, இது, பசு, புது, கடு, நடு, வடு`),
   - **THEN**: It is **Mutriyalugaram** (full 1-*matra* `u`), NOT *Kurriyalugaram*.
3. **R94.3 — Extended / Compound Scope**:
   - Viruttiyurai pno=168 & Kandigai sutra=94 note two extensions via grammatical implication:
     - Word-initial `நு` in the kinship noun `நுந்தை` (citing Tolkappiyam Mozhi. 34).
     - Compound-medial *kurriyalugaram* (e.g., `செக்குக்கணை`, `சுக்குக் கொடு` — Viruttiyurai pno=168) retains its 1/2 *matra* quantity.

### Deep-Dive: Formal Decision Algorithm (*Kurriyalugaram* 6 Classes vs *Mutriyalugaram*)

Given a Tamil word `W` decomposed into orthographic/phonological units `[U_1, U_2, ..., U_n]` where each `U_i` is either a standalone vowel `V`, `ஃ` (aytham), pure consonant `C`, or *uyirmei* `(C, V)`:

1. **Check final unit `U_n`**:
   - If `U_n` is NOT `(C_v, உ)` with `C_v ∈ {க், ச், ட், த், ப், ற்}` (for example, `U_n` is `பூ`, `உ`, or `மு, னு, ரு, லு, வு, ழு, ளு` as in `தெரு`):
     -> Return **`Mutriyalugaram`** (if ending in `உ`) or **`NonU`**.
2. **Check word length `n == 2` with short vowel**:
   - If `n == 2` and `U_1` has a **short vowel** `V ∈ {அ, இ, உ, எ, ஒ}` (either standalone `V` as in `அது, இது, உது, எது`, or `(C, V_short)` as in `பசு, புது, கடு, நடு, வடு`):
     -> Return **`Mutriyalugaram`** (Kandigai sutra=94: *short-vowel-only + vallinam-u is Mutriyalugaram*).
3. **Inspect penultimate unit `U_{n-1}`**:
   - **If `U_{n-1}` is `ஃ` (Aytham)**:
     -> Return **`AythathThodar`** (`ஆய்தத்தொடர்`).
   - **If `U_{n-1}` is a pure consonant `C`**:
     - If `C ∈ {க், ச், ட், த், ப், ற்}` -> Return **`Vanthodar`** (`வன்தொடர்`).
     - If `C ∈ {ங், ஞ், ண், ந், ம், ன்}` -> Return **`Menthodar`** (`மென்தொடர்`).
     - If `C ∈ {ய், ர், ல், ழ், ள்}` -> Return **`Idaithodar`** (`இடைத்தொடர்`).
     - (Note: `வ்` cannot precede `C_v` in native Tamil; if encountered in a loanword, it is not classical *Idaithodar*.)
   - **If `U_{n-1}` is a vowel `V` or *uyirmei* `(C, V)`**:
     - If `n == 2` AND `V ∈ {ஆ, ஈ, ஊ, ஏ, ஐ, ஓ, ஔ}` (single long vowel syllable `தனிநெடில்`):
       -> Return **`NedilThodar`** (`நெடில்தொடர்`).
     - Else (`n >= 3`, i.e., `பிறமேற் றொடரவும் பெறும்`, whether `U_{n-1}` has a short or long vowel, e.g. `வரகு`, `பலாசு`, `போவது`, `இறும்பூது`):
       -> Return **`UyirThodar`** (`உயிர்த்தொடர்`). (Kandigai sutra=94 explicitly notes: `பிறமேல் தொடரின் உயிர்த்தொடர் எனப்படும்`.)

### Attested Examples

| First / Word | Second | Surface | Class / Transform | Witness | Notes |
| --- | --- | --- | --- | --- | --- |
| `நாகு` | — | `நாகு` | `NedilThodar` | `viruttiyurai_pno=167`, `kandigai=94` | Single long vowel + `கு` |
| `காசு`, `நீறு` | — | `காசு`, `நீறு` | `NedilThodar` | `kandigai=94` | Single long vowel + `சு`/`று` |
| `எஃகு` | — | `எஃகு` | `AythathThodar` | `viruttiyurai_pno=167`, `kandigai=94` | Preceded by `ஃ` |
| `கஃசு`, `இருபஃது` | — | `கஃசு`, `இருபஃது` | `AythathThodar` | `kandigai=94` | `இருபஃது` has `பிறமேல் தொடர்தல்` |
| `வரகு`, `பலாசு` | — | `வரகு`, `பலாசு` | `UyirThodar` | `viruttiyurai_pno=167`, `kandigai=94` | `பலாசு` has long `லா` but `n=3` |
| `போவது`, `ஒன்பது`, `இறும்பூது` | — | `போவது`, `ஒன்பது`, `இறும்பூது` | `UyirThodar` | `viruttiyurai_pno=168`, `kandigai=94` | Polysyllabic vowel-medial |
| `கயிறு` | — | `கயிறு` | `UyirThodar` | `kandigai=94` | Polysyllabic vowel-medial |
| `கொக்கு` | — | `கொக்கு` | `Vanthodar` | `viruttiyurai_pno=167`, `kandigai=94` | Preceded by `க்` |
| `பிண்ணாக்கு`, `விளையாட்டு` | — | (same) | `Vanthodar` | `viruttiyurai_pno=168`, `kandigai=94` | Preceded by vallinam |
| `கச்சு`, `பற்று`, `குருத்து` | — | (same) | `Vanthodar` | `kandigai=94` | Preceded by vallinam |
| `குரங்கு` | — | `குரங்கு` | `Menthodar` | `viruttiyurai_pno=167` | Preceded by `ங்` |
| `பட்டாங்கு`, `சுண்ணாம்பு` | — | (same) | `Menthodar` | `viruttiyurai_pno=168`, `kandigai=94` | Preceded by mellinam |
| `சங்கு`, `பஞ்சு`, `அம்பு`, `கன்று` | — | (same) | `Menthodar` | `kandigai=94` | Preceded by mellinam |
| `அல்கு` | — | `அல்கு` | `Idaithodar` | `viruttiyurai_pno=167` | Preceded by `ல்` |
| `வெய்து`, `சால்பு`, `தெள்கு` | — | (same) | `Idaithodar` | `kandigai=94` | Preceded by `ய், ல், ள்` |
| `அது`, `இது` | — | `அது`, `இது` | `Mutriyalugaram` | `viruttiyurai_pno=167, 168` | Excluded by `பிறமேற் றொடரவும் பெறுமே` |
| `நுந்தை` | — | `நுந்தை` | Special initial `நு` | `viruttiyurai_pno=168`, `kandigai=94` | Kinship term |
| `செக்கு` + `கணை` | — | `செக்குக்கணை` | Compound-medial | `viruttiyurai_pno=168` | Retains 1/2 matra |
| `சுக்கு` + `கொடு` | — | `சுக்குக் கொடு` | Compound-medial | `viruttiyurai_pno=168` | Retains 1/2 matra |

### Interactions & Precedence

- **Prerequisite for Sutras 163–164, 183–185**:
  - *NedilThodar* and *UyirThodar* with `டு/று` undergo `ottu irattal` (gemination: `நாடு + அகம் -> நாட்டகம்` / `ஆறு + நீர் -> ஆற்றுநீர்`).
  - *Vanthodar* triggers vallinam doubling (`கொக்கு + கால் -> கொக்குக்கால்`).
  - *Menthodar* (`குரங்கு`) and *Idaithodar* (`அல்கு`) follow distinct *kurriyalugaram* sandhi rules.
  - *Mutriyalugaram* (`பசு, அது`) does **not** elide before vowels via Sutra 164's *kurriyalugaram* rule (`உயிர்வரின் உக்குறள் மெய்விட்டோடும்`) — instead it takes `வ்` glide or remains *iyalbu* depending on the *mutriyalugaram* rule.

### Surface Signature & Reversibility (`split.rs`)

- Every candidate `first` ending in `கு, சு, டு, து, பு, று` reconstructed after vowel elision (`C_v + V_2 -> C_v உ + V_2`) or `ட்ட/ற்ற` gemination (`C_v C_v -> C_v உ`) MUST be routed through this exact 6-class classifier to determine which *punariyal* rules apply and whether *kurriyalugaram* elision was legal.

---

## Sutra 102

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — முதனிலைப் பொதுவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=175](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=175)
- **TVA Kandigaiyurai**: [sutra=102](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=102&y=102)

### Root Text (TVA 1999 Critical Edition)

```text
பன்னீ ருயிருங் கசதந பமவய
ஞஙவீ ரைந்துயிர் மெய்யு மொழிமுதல்.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  பன்னீர் உயிர் உம் க ச த ந ப ம வ ய
  ஞ ங ஈர் ஐந்து உயிர்மெய் உம் மொழி முதல்
  ```
- **Diff**: Un-sandhied word separation in `pmuni0147` vs sandhied metrical text in TVA 1999.

### Atomic Sub-Rules (`IF -> THEN`)

1. **R102.1 — Word-Initial Vowels (`உயிர்`)**:
   - **IF**: A word starts with any of the 12 vowels `{அ, ஆ, இ, ஈ, உ, ஊ, எ, ஏ, ஐ, ஒ, ஓ, ஔ}`.
   - **THEN**: Phonotactically legal word-initial (`மொழிமுதல்`).
2. **R102.2 — Word-Initial *Uyirmei* (`உயிர்மெய்`)**:
   - **IF**: A word starts with an *uyirmei* whose base consonant is one of the 10 (`ஈரைந்து`) consonants `{க, ச, த, ந, ப, ம, வ, ய, ஞ, ங}`, subject to the restrictions in Sutras 103–106.
   - **THEN**: Phonotactically legal word-initial.
3. **R102.3 — Disallowed Word-Initials**:
   - **IF**: A word starts with a pure consonant (`மெய்`), aytham (`ஃ`), or an *uyirmei* of the 8 consonants `{ட, ண, ர, ல, ழ, ள, ற, ன}`.
   - **THEN**: Illegal as a native Tamil word-initial.

### Attested Examples

| Word | Initial | Class | Witness | Notes |
| --- | --- | --- | --- | --- |
| `அடை, ஆடை, இடை, ஈடு, உடை, ஊடல், எடு, ஏடு, ஐயம், ஒதி, ஓதி, ஒளவியம்` | 12 vowels | Legal vowel-initial | `viruttiyurai_pno=175`, `kandigai=102` | All 12 vowels |
| `களி, சவடி, தளிர், நலம், படை, மலை, வளம், யவனர், ஞமலி, அங்ஙனம்` | 10 consonants | Legal *uyirmei*-initial | `viruttiyurai_pno=175`, `kandigai=102` | `அங்ஙனம்` illustrates `ஙனம்` |

---

## Sutra 103

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — முதனிலைச் சிறப்புவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=175](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=175)
- **TVA Kandigaiyurai**: [sutra=103](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=103&y=103)

### Root Text (TVA 1999 Critical Edition)

```text
உஊ ஒஓ வலவொடு வம்முதல்.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading: `உ ஊ ஒ ஓ அல ஒடு வ முதல்`
- **Diff**: Un-sandhied word separation in `pmuni0147` vs `வலவொடு வம்முதல்` in TVA 1999.

### Atomic Sub-Rules (`IF -> THEN`)

- **R103.1 — `வ`-initial restriction**:
  - **IF**: A word begins with `வ`-series *uyirmei*.
  - **THEN**: Legal ONLY with the 8 vowels `{அ, ஆ, இ, ஈ, எ, ஏ, ஐ, ஔ}` (`வ, வா, வி, வீ, வெ, வே, வை, வௌ`).
  - **DISALLOWED**: `வு, வூ, வொ, வோ`.

### Attested Examples

| Word | Initial | Witness | Notes |
| --- | --- | --- | --- |
| `வளி, வாளி, விளி, வீளி, வெளி, வேளை, வைகல், வௌவு` | `வ..வௌ` | `viruttiyurai_pno=175` | 8 legal `வ`-initials |
| `வளி, வாளி, விளி, வீறு, வெளி, வேளை, வைகல், வௌவு` | `வ..வௌ` | `kandigai=103` | `வீறு` instead of `வீளி` |

---

## Sutra 104

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — முதனிலைச் சிறப்புவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=175](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=175), [pno=176](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=176)
- **TVA Kandigaiyurai**: [sutra=104](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=104&y=104) *(Note: TVA Kandigai page `pno=104` in the source bundle displays Sutra 103's text due to TVA page indexing; Viruttiyurai pno=175–176 carries Sutra 104.)*

### Root Text (TVA 1999 Critical Edition)

```text
அஆ உஊ ஓஒள யம்முதல்.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading: `அ ஆ உ ஊ ஓ ஔ ய முதல்`
- **Diff**: `pmuni0147` spaces the vowels and reads `ய முதல்` vs TVA 1999 `யம்முதல்`.

### Atomic Sub-Rules (`IF -> THEN`)

- **R104.1 — `ய`-initial restriction**:
  - **IF**: A word begins with `ய`-series *uyirmei*.
  - **THEN**: Legal ONLY with the 6 vowels `{அ, ஆ, உ, ஊ, ஓ, ஔ}` (`ய, யா, யு, யூ, யோ, யௌ`).
  - **DISALLOWED**: `யி, யீ, யெ, யே, யை, யொ`.

### Attested Examples

| Word | Initial | Witness | Notes |
| --- | --- | --- | --- |
| `யவனர், யானை, யுகம், யூகி, யோகம், யௌவனம்` | `ய, யா, யு, யூ, யோ, யௌ` | `viruttiyurai_pno=176` | 6 legal `ய`-initials |

---

## Sutra 105

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — முதனிலைச் சிறப்புவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=176](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=176)
- **TVA Kandigaiyurai**: [sutra=105](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=105&y=105) *(Note: TVA Kandigai `pno=105` in the source bundle displays Sutra 103's text due to TVA page indexing.)*

### Root Text (TVA 1999 Critical Edition)

```text
அஆஎ ஒவ்வொ டாகு ஞம்முதல்.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading: `அ ஆ எ ஒ ஓடு ஆகும் ஞ முதல்`
- **Diff**: Un-sandhied spacing in `pmuni0147` vs sandhied `ஒவ்வொ டாகு ஞம்முதல்` in TVA 1999.

### Atomic Sub-Rules (`IF -> THEN`)

- **R105.1 — `ஞ`-initial restriction**:
  - **IF**: A word begins with `ஞ`-series *uyirmei*.
  - **THEN**: Legal ONLY with the 4 vowels `{அ, ஆ, எ, ஒ}` (`ஞ, ஞா, ஞெ, ஞொ`).
  - **DISALLOWED**: `ஞி, ஞீ, ஞு, ஞூ, ஞே, ஞை, ஞோ, ஞௌ`.

### Attested Examples

| Word | Initial | Witness | Notes |
| --- | --- | --- | --- |
| `ஞமலி, ஞாலம், ஞெகிழி, ஞொள்கிற்று` | `ஞ, ஞா, ஞெ, ஞொ` | `viruttiyurai_pno=176` | 4 legal `ஞ`-initials |

---

## Sutra 106

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — முதனிலைச் சிறப்புவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=176](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=176), [pno=177](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=177)
- **TVA Kandigaiyurai**: [sutra=106](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=106&y=106) *(Note: TVA Kandigai `pno=106` in the source bundle displays Sutra 93's text due to TVA page indexing.)*

### Root Text (TVA 1999 Critical Edition)

```text
சுட்டியா வெகர வினாவழி யவ்வை
ஒட்டி ஙவ்வு முதலா கும்மே.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  சுட்டு யா எகர வினா வழி அ ஐ
  ஒட்டி ங உம் முதல் ஆகும் ஏ
  ```
- **Diff**: `pmuni0147` splits `அவ்வை` (`அ`-வை, accusative of `அ`) into `அ ஐ`; TVA 1999 reads `யவ்வை` (`அவ்வை` = vowel `அ` + accusative `-ஐ` after glide `ய்`), which matches Viruttiyurai's gloss (`அகரத்தை ஒட்டி`).

### Atomic Sub-Rules (`IF -> THEN`)

- **R106.1 — Bound `ங`-initial (`ஙனம்`)**:
  - **IF**: `first` is a demonstrative (`அ, இ, உ`) or interrogative (`யா, எ`) clitic, AND `second` is `ஙனம்` (`ங` + `அ` = `ங` initial).
  - **THEN**: `ங` (`ங் + அ`) is allowed as the initial of the bound second constituent `ஙனம்` (producing `அங்ஙனம், இங்ஙனம், உங்ஙனம், யாங்ஙனம், எங்ஙனம்` with `ங்` gemination). `ங` NEVER starts an independent standalone word.
- **R106.2 — Unmarked 6 Consonants (`அருத்தாபத்தி` — Viruttiyurai pno=177)**:
  - By elimination from Sutras 102–106, the remaining 6 initial consonants `{க, ச, த, ந, ப, ம}` combine with **all 12 vowels** (`6 × 12 = 72` initials). Viruttiyurai pno=177 explicitly notes that unlike Tolkappiyam (which barred `ச` with `அ, ஐ, ஔ`), Nannool permits `ச` with all 12 vowels due to Sanskrit/regional loanwords.

### Attested Examples

| First | Second | Surface | Witness | Notes |
| --- | --- | --- | --- | --- |
| `அ` | `ஙனம்` | `அங்ஙனம்` | `viruttiyurai_pno=176` | Demonstrative + `ஙனம்` |
| `இ` | `ஙனம்` | `இங்ஙனம்` | `viruttiyurai_pno=176` | Demonstrative + `ஙனம்` |
| `உ` | `ஙனம்` | `உங்ஙனம்` | `viruttiyurai_pno=176` | Demonstrative + `ஙனம்` |
| `யா` | `ஙனம்` | `யாங்ஙனம்` | `viruttiyurai_pno=176` | Interrogative + `ஙனம்` |
| `எ` | `ஙனம்` | `எங்ஙனம்` | `viruttiyurai_pno=176` | Interrogative + `ஙனம்` |

---

## Sutra 107

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — இறுதிநிலை)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=177](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=177)
- **TVA Kandigaiyurai**: [sutra=107](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=107&y=107)

### Root Text (TVA 1999 Critical Edition)

```text
ஆவி ஞணநம னயரல வழளமெய்
சாயு முகர நாலாறு மீறே.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  ஆவி ஞ ண ந ம ன ய ர ல வ ழ ள மெய்
  சாயும் உகரம் நால் ஆறு உம் ஈறு ஏ
  ```
- **Diff**: Un-sandhied spacing in `pmuni0147` vs sandhied metrical text in TVA 1999.

### Atomic Sub-Rules (`IF -> THEN`)

- **R107.1 — 24 Legal Word-Finals (`நாலாறு ஈறு`)**:
  - **12 Vowels (`ஆவி`)**: `{அ, ஆ, இ, ஈ, உ, ஊ, எ, ஏ, ஐ, ஒ, ஓ, ஔ}` (standalone or in *uyirmei*, subject to Sutra 108).
  - **11 Pure Consonants (`மெய்`)**: `{ஞ், ண், ந், ம், ன், ய், ர், ல், வ், ழ், ள்}` (all 6 mellinam except `ங்`; all 6 idaiyinam; zero vallinam).
  - **1 *Kurriyalugaram* (`சாயும் உகரம்`)**: Counted separately for sandhi behavior (24 total = `12 + 11 + 1`).
- **R107.2 — Disallowed Word-Finals**:
  - Pure `ங்`, all 6 pure vallinam consonants `{க், ச், ட், த், ப், ற்}`, and `ஃ` (aytham) NEVER end a native Tamil word.

### Attested Examples

| Word | Final | Class | Witness | Notes |
| --- | --- | --- | --- | --- |
| `ஆ, ஈ, ஊ, ஏ, ஐ, ஓ, ஔ` | Standalone long vowels | Vowel-final | `viruttiyurai_pno=177` (prints two-scalar `ஒள`), `kandigai=107` (lists `ஆ..ஓ`, omits standalone `ஔ`) | Single-letter words |
| `அ, இ, உ, எ, ஒ` | Standalone short vowels | Vowel-final | `viruttiyurai_pno=177` | Deictic/interrogative/similitude particles |
| `விள, பலா, கரி, கடு, சே, தை` | *Uyirmei* vowels | Vowel-final | `viruttiyurai_pno=177`, `kandigai=107` | `kandigai=107` also lists `தீ, பூ, சேஎ, தே, நொ, போ, கௌ`; `viruttiyurai_pno=177` also lists `குரீஇ, மரூஉ, கோ` |
| `உரிஞ், மண், பொருந், மரம், பொன், வேய், வேர், வேல், தெவ், வீழ், வாள்` | 11 pure consonants | Consonant-final | `viruttiyurai_pno=177`, `kandigai=107` | All 11 legal consonants |
| `அஃகு` | *Kurriyalugaram* | `சாயும் உகரம்` | `viruttiyurai_pno=177`, `kandigai=107` | Counted as 24th final |

---

## Sutra 108

- **Chapter**: `ezhuttiyal` (எழுத்தியல் — சில எழுத்துக்களுக்குச் சிறப்புவிதி)
- **Tier**: Phonotactic Filter (`split.rs`)
- **TVA Viruttiyurai**: [pno=178](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=178), [pno=179](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=179)
- **TVA Kandigaiyurai**: [sutra=108](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=108&y=108)

### Root Text (TVA 1999 Critical Edition)

```text
குற்றுயி ரளபி னீறா மெகர
மெய்யொ டேலா தொந்நவ்வொ டாமௌக்
ககர வகரமோ டாகு மென்ப.
```

*(Note: Viruttiyurai footnote 105 records Sankara Namachivayar's variant `வகரமொ டாகு`.)*

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  குற்று உயிர் அளபின் ஈறு ஆம் எகரம்
  மெய் ஒடு ஏலாது ஒ ந ஒடு ஆம் ஔ
  ககர வகரம் ஓடு ஆகும் என்ப
  ```
- **Diff**: Un-sandhied spacing in `pmuni0147` vs sandhied text in TVA 1999.

### Atomic Sub-Rules (`IF -> THEN`)

1. **R108.1 — Short-vowel orthographic *alapedai* finals (`குற்றுயிர் அளபின் ஈறாம்`)**:
   - Standalone short vowels `{அ, இ, உ, எ, ஒ}` appear at word-end as orthographic *alapedai* markers after their matching long vowel (`ஆஅ, ஈஇ, ஊஉ, ஏஎ, ஐஇ, ஓஒ, ஔஉ`).
2. **R108.2 — `எ` restriction (`எகரம் மெய்யோடு ஏலாது`)**:
   - Short `எ` NEVER ends a word in an *uyirmei* (`C + எ`, e.g., `கெ, செ, தெ` are illegal word-finals).
3. **R108.3 — `ஒ` restriction (`ஒ நவ்வொடு ஆம்`)**:
   - Short `ஒ` ends a word in an *uyirmei* ONLY with `ந` (`நொ`).
4. **R108.4 — `ஔ` restriction (`ஔ ககர வகரமொடு ஆகும்`)**:
   - `ஔ` ends a word in an *uyirmei* ONLY with `க` or `வ` (`கௌ, வௌ`).

### Attested Examples

| Word | Final | Rule | Witness | Notes |
| --- | --- | --- | --- | --- |
| `ஆஅ` (`ஆஅ வளிய வலவன்`) | Standalone `அ` (*alapedai*) | R108.1 | `viruttiyurai_pno=178` | Orthographic marker |
| `பலாஅ, தீஇ, பூஉ, சேஎ, கைஇ, கோஒ, கௌஉ` | Standalone short vowels (*alapedai*) | R108.1 | `kandigai=108` | Also `காணூஉ` in `viruttiyurai_pno=178` |
| `நொ` | `ந் + ஒ` | R108.3 | `viruttiyurai_pno=178`, `kandigai=108` | Only `C+ஒ` word-final |
| `கௌ, வௌ` | `க் + ஔ`, `வ் + ஔ` | R108.4 | `viruttiyurai_pno=178`, `kandigai=108` | Only `C+ஔ` word-finals |

---

## Deep-Dive: Machine-Implementable *Mozhi-muthal* & *Mozhi-eetru* Tables (Sutras 102–108)

### 1. Legal Word-Initials (`is_valid_mozhi_muthal`)

| Category | Allowed Vowels (`V`) | Count | Disallowed Vowels |
| --- | --- | --- | --- |
| Standalone Vowel | All 12 (`அ, ஆ, இ, ஈ, உ, ஊ, எ, ஏ, ஐ, ஒ, ஓ, ஔ`) | 12 | None |
| `க, ச, த, ந, ப, ம` + `V` | All 12 (`அ..ஔ`) | 72 | None |
| `வ` + `V` (Sutra 103) | `அ, ஆ, இ, ஈ, எ, ஏ, ஐ, ஔ` | 8 | `உ, ஊ, ஒ, ஓ` (`வு, வூ, வொ, வோ`) |
| `ய` + `V` (Sutra 104) | `அ, ஆ, உ, ஊ, ஓ, ஔ` | 6 | `இ, ஈ, எ, ஏ, ஐ, ஒ` (`யி, யீ, யெ, யே, யை, யொ`) |
| `ஞ` + `V` (Sutra 105) | `அ, ஆ, எ, ஒ` | 4 | `இ, ஈ, உ, ஊ, ஏ, ஐ, ஓ, ஔ` |
| `ங` + `V` (Sutra 106) | `அ` (`ங`) ONLY in bound `ஙனம்` after `அ, இ, உ, யா, எ` | 1 (bound) | All other vowels; never standalone |
| `ட, ண, ர, ல, ழ, ள, ற, ன` | None (native Tamil) | 0 | All 12 |
| Pure consonants & `ஃ` | None | 0 | All |

### 2. Legal Word-Finals (`is_valid_mozhi_eetru`)

| Category | Allowed Forms | Disallowed Forms |
| --- | --- | --- |
| Standalone Vowel | All 12 (`அ..ஔ`, including *alapedai* short vowels) | None |
| *Uyirmei* (`C + V`) | `V ∈ {அ, ஆ, இ, ஈ, உ, ஊ, ஏ, ஐ, ஓ}` (any `C`); `நொ` (`ந+ஒ`); `கௌ, வௌ` (`க/வ+ஔ`) | `C + எ` (all 18); `C + ஒ` (`C ≠ ந`); `C + ஔ` (`C ∉ {க, வ}`) |
| Pure Consonant (`மெய்`) | `ஞ், ண், ந், ம், ன், ய், ர், ல், வ், ழ், ள்` (11) | `ங்`, `க், ச், ட், த், ப், ற்` (7) |
| Aytham (`ஃ`) | None | Always disallowed |
| *Kurriyalugaram* | `கு, சு, டு, து, பு, று` (when Sutra 94 holds) | — |

### 3. Usage in `split.rs` & Loanword Caveats

- **Phonotactic Filter**: `split.rs` can reject impossible native splits immediately if `first` ends in an illegal *mozhi-eetru* (e.g., `க், ச், ட், த், ப், ற், ங், ஃ`, or `C+எ`) or `second` begins with an illegal *mozhi-muthal* (e.g., pure consonant, `ஃ`, `வு`, `யி`, `ஞி`, or `ட/ர/ல` in native mode).
- **Loanword Caveat**: As Viruttiyurai pno=177 already observes for `ச`, loanwords (*vadamozhi* / *thisaichol* / modern English/Sanskrit loans) violate classical *mozhi-muthal* (e.g., `ராமன்`, `லட்சுமி`, `டப்பா`, `யுத்த` vs `யேசு`). Therefore, `is_valid_mozhi_muthal` / `is_valid_mozhi_eetru` should be applied as a **hard filter for native-sandhi hypothesis scoring/pruning**, or gated by a strictness flag when dictionary lookup already confirms a loanword stem.

---

## Sutra 136

- **Chapter**: `padaviyal` (பதவியல் — பண்புப் பகுதிக்கு எய்தியதன்மேல் சிறப்புவிதி)
- **Tier**: Core Morphology / Compound Sandhi
- **TVA Viruttiyurai**: [pno=198](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=198), [pno=199](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=199), [pno=200](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?auth_pub_id=17&bookid=6&pno=200)
- **TVA Kandigaiyurai**: [sutra=136](https://www.tamilvu.org/slet/l0100/l0100pd1.jsp?bookid=6&auth_pub_id=15&pno=136&y=136)

### Root Text (TVA 1999 Critical Edition)

```text
ஈறு போத லிடையுகர மிய்யாதல்
ஆதி நீட லடியகர மையாதல்
தன்னொற் றிரட்டன் முன்னின்ற மெய்திரிதல்
இனமிக லினையவும் பண்பிற் கியல்பே.
```

### Edition Diff vs `pmuni0147`

- `pmuni0147` reading:
  ```text
  ஈறு போதல் இடை உகரம் இ ஆதல்
  ஆதி நீடல் அடி அகரம் ஐ ஆதல்
  தன் ஒற்று இரட்டல் முன் நின்ற மெய் திரிதல்
  இனம் மிகல் இனைய உம் பண்பின் கு இயல்பு ஏ
  ```
- **Diff**: Un-sandhied word separation in `pmuni0147` vs sandhied metrical text in TVA 1999.

### Deep-Dive: The 8 Named Operations (*Panpuppeyar* Sandhi)

Sutra 136 governs `-மை`-ending qualitative stems (*panpu-ppaguthi* enumerated in Sutra 135: `செம்மை, சிறுமை, சேய்மை, தீமை, வெம்மை, புதுமை, மென்மை, மேன்மை, திண்மை, உண்மை, நுண்மை`, and their opposites `வெண்மை, கருமை, பொன்மை, பசுமை, பெருமை, அணிமை, நன்மை, தண்மை, பழமை, வன்மை, கீழ்மை, நொய்மை, இன்மை, பருமை`, etc.) when combining with suffixes or following words (`பதப் புணர்ச்சி`). Note Viruttiyurai pno=199 explicitly states these operations are **optional/lexicalized** (`ஒருதலை அன்று` — e.g., `செம்மையன், கருமையன்` also occur without `-மை` elision).

1. **Op 1 — `ஈறு போதல்` (Elision of final `-மை`)** [`keduthal`]:
   - `Xமை -> X` (e.g., `நன்மை -> நன் -> நல் + அன் -> நல்லன்`; `வன்மை -> வல் + அன் -> வல்லன்`).
2. **Op 2 — `இடையுகரம் இய்யாதல்` (Medial `உ` becomes `இ`)** [`thirithal`]:
   - After `-மை` elides, `Cஉ -> Cஇ` (e.g., `கருமை + அன் -> கரு + அன் -> கரி + அன் -> கரியன்` via `ய்`-glide; `பெருமை + அன் -> பெரு + அன் -> பெரி + அன் -> பெரியன்`).
3. **Op 3 — `ஆதி நீடல்` (Initial short vowel lengthens)** [`thirithal`]:
   - Initial short vowel lengthens (`அ -> ஆ`, `எ -> ஏ`, `இ -> ஈ`, `உ -> ஊ`, `ஒ -> ஓ`): e.g., `பசுமை + இ -> பாசி` (`பசு -> பாசு -> பாசு + இ -> பாசி` via `u`-elision), `பசுமை + அடை -> பாசடை` (`பாசு + அடை -> பாசடை`), `செம்மை + ஆ -> சேதா`, `செம்மை + ஆம்பல் -> சேதாம்பல்`.
4. **Op 4 — `அடியகரம் ஐயாதல்` (Initial `அ` becomes `ஐ`)** [`thirithal`]:
   - Initial `அ` (in `Cஅ...`) becomes `ஐ`: e.g., `பசுமை + கண் -> பைங்கண்`, `பசுமை + தார் -> பைந்தார்`.
5. **Op 5 — `தன்னொற்று இரட்டல்` (Stem consonant geminates)** [`thonral`]:
   - Stem consonant doubles (`C -> CC`), especially before vowel-initial `second`: e.g., `வெறுமை + இலை -> வெறு + இலை -> வெற்றிலை`; `நெடுமை + அணை -> நெடு + அணை -> நெட்டணை`.
6. **Op 6 — `முன்னின்ற மெய்திரிதல்` (Preceding consonant mutates)** [`thirithal`]:
   - Stem-final consonant mutates to another consonant: e.g., `செம்மை + ஆ -> சேதா` (`ம் -> த்`), `செம்மை + ஆம்பல் -> சேதாம்பல்` (`ம் -> த்`).
7. **Op 7 — `இனமிகல்` (Homorganic nasal/consonant insertion)** [`thonral`]:
   - Homorganic nasal corresponding to the initial consonant of `second` is inserted (`க் -> ங்`, `ச் -> ஞ்`, `ட் -> ண்`, `த் -> ந்`, `ப் -> ம்`, `ற் -> ன்`): e.g., `பசுமை + கண் -> பைங்கண்` (`ங்` before `க`), `பசுமை + தார் -> பைந்தார்` (`ந்` before `த`).
8. **Op 8 — `இனையவும்` (Other analogous/residual transformations)**:
   - Covers non-enumerated stem reductions such as **medial syllable elision** (`இடையுகரம் சகரத்தோடு கெட்டு` — Viruttiyurai pno=199 in `பசுமை + கண் -> பைங்கண்` and `பசுமை + தார் -> பைந்தார்`, where `சு` drops completely alongside `-மை`), and `ன் -> ல்` in `நன்மை -> நல்லன்`.

### Rule Ordering When Multiple Operations Apply

1. **Stage 1 — Suffix Drop**: `ஈறு போதல்` (`-மை` drops, leaving the root stem).
2. **Stage 2 — Root Vowel / Syllable Adjustment**:
   - `இனையவும்` medial syllable drop (`பசு -> ப`) OR `இடையுகரம் இய்யாதல்` (`கரு -> கரி`)
   - `ஆதி நீடல்` (`பசு -> பாசு`, `செம் -> சேம்`) OR `அடியகரம் ஐயாதல்` (`ப -> பை`)
3. **Stage 3 — Junction Consonant Adjustment**:
   - `தன்னொற்று இரட்டல்` (`வெறு -> வெற்று`, `நெடு -> நெட்டு`)
   - `முன்னின்ற மெய்திரிதல்` (`சேம் -> சேத்`, or nasal assimilation)
   - `இனமிகல்` (`பை + கண் -> பைங்கண்`, `பை + தார் -> பைந்தார்`)
4. **Stage 4 — General Boundary Sandhi** (Sutras 158, 162, 165 cited in Viruttiyurai pno=199):
   - *Uyir-varin ukkural mei vittodum* (`பாசு + அடை -> பாசடை`, `வெற்று + இலை -> வெற்றிலை`)
   - *Udalmel uyirvanthu onruvathu iyalbe* (`சேத் + ஆம்பல் -> சேதாம்பல்`)
   - *Udambadumei* (`கரி + அன் -> கரியன்`)

*(Structural walkthrough for standard test stems — not in `bundle_00` witness list: `செம்மை+தாமரை -> செந்தாமரை` [Op 1 + Op 6/7]; `பசுமை+தமிழ் -> பைந்தமிழ்` [Op 1 + Op 8 (`சு` drop) + Op 4 + Op 7]; `சிறுமை+ஊர் -> சிற்றூர்` [Op 1 + Op 5 + `u`-elision]; `வெண்மை+தாமரை -> வெண்டாமரை` [Op 1 + `ண்+த்->ண்ட`]; `கருமை+கடல் -> கருங்கடல்` [Op 1 + Op 7]; `பெருமை+வழி -> பெருவழி` [Op 1]; `கருமை+குதிரை -> கரியகுதிரை` [Op 1 + Op 2 + `-அ`]; `முதுமை+ஊர் -> மூதூர்` [Op 1 + Op 3 + `u`-elision].)*

### Attested Examples

| First | Second | Surface | Operations Applied | Witness | Notes |
| --- | --- | --- | --- | --- | --- |
| `நன்மை` | `அன்` | `நல்லன்` | Op 1 (`ஈறு போதல்`) + `ன் -> ல்` | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `வன்மை` | `அன்` | `வல்லன்` | Op 1 (`ஈறு போதல்`) + `ன் -> ல்` | `viruttiyurai_pno=199` | — |
| `கருமை` | `அன்` | `கரியன்` | Op 1 + Op 2 (`உ -> இ`) + `ய்` glide | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `பெருமை` | `அன்` | `பெரியன்` | Op 1 + Op 2 (`உ -> இ`) + `ய்` glide | `viruttiyurai_pno=199` | — |
| `பசுமை` | `இ` | `பாசி` | Op 1 + Op 3 (`ஆதி நீடல்`) | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `பசுமை` | `அடை` | `பாசடை` | Op 1 + Op 3 + `u`-elision | `viruttiyurai_pno=199` | — |
| `பசுமை` | `கண்` | `பைங்கண்` | Op 1 + Op 8 (`சு` drop) + Op 4 (`அ -> ஐ`) + Op 7 (`ங்`) | `viruttiyurai_pno=199` | — |
| `பசுமை` | `தார்` | `பைந்தார்` | Op 1 + Op 8 (`சு` drop) + Op 4 (`அ -> ஐ`) + Op 7 (`ந்`) | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `வெறுமை` | `இலை` | `வெற்றிலை` | Op 1 + Op 5 (`ற் -> ற்ற`) + `u`-elision | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `நெடுமை` | `அணை` | `நெட்டணை` | Op 1 + Op 5 (`ட் -> ட்ட`) + `u`-elision | `viruttiyurai_pno=199` | — |
| `செம்மை` | `ஆ` | `சேதா` | Op 1 + Op 3 (`எ -> ஏ`) + Op 6 (`ம் -> த்`) | `viruttiyurai_pno=199` | — |
| `செம்மை` | `ஆம்பல்` | `சேதாம்பல்` | Op 1 + Op 3 (`எ -> ஏ`) + Op 6 (`ம் -> த்`) | `viruttiyurai_pno=199`, `kandigai=136` | — |
| `செம்மை` | `அன்` | `செம்மையன்` | `iyalbu` (`ய்` glide, no `-மை` drop) | `viruttiyurai_pno=199` | Shows optionality |
| `கருமை` | `அன்` | `கருமையன்` | `iyalbu` (`ய்` glide, no `-மை` drop) | `viruttiyurai_pno=199` | Shows optionality |

### Surface Signature & Reversibility (`split.rs`)

Because Sutra 136 transforms are non-local (modifying the stem's initial vowel, medial syllable, or consonant), pure local boundary splitting cannot recover `<stem>மை` without a closed-class stem table:
- **Geminated `-ற்ற-` / `-ட்ட-` + vowel**: `வெற்றிலை`, `நெட்டணை` -> check closed-class stems `வெறுமை`, `நெடுமை`, `சிறுமை`, `குறுமை`, `நெடுமை`, `பசுமை`, etc.
- **`Cஐ` + homorganic nasal `[ங், ஞ், ண், ந், ம், ன்]`**: `பைங்கண்`, `பைந்தார்` -> reverse-map `பை[ங்/ந்]` to `பசுமை` (and similarly `மை...` / `செய்...`).
- **`சேத்-` + vowel**: `சேதா`, `சேதாம்பல்` -> reverse-map to `செம்மை`.
- **`Cஇய்` + vowel**: `கரியன்`, `பெரியன்` -> reverse-map `கரி/பெரி` to `கருமை/பெருமை`.

---

## Chapter Summary & Implementation Implications

### 1. `phonology.rs`
- **`KurriyalugaramClass` enum**: `NedilThodar`, `AythathThodar`, `UyirThodar`, `Vanthodar`, `Menthodar`, `Idaithodar`, `Mutriyalugaram`, `NonU`.
- **`classify_ugaram(word: &str) -> KurriyalugaramClass`**: Implements the exact Sutra 94 decision tree (checking final `{கு, சு, டு, து, பு, று}`, excluding 2-unit short-vowel `C?V_short + C_v u` as `Mutriyalugaram`, separating `NedilThodar` (`n == 2` long vowel) from `UyirThodar` (`n >= 3` vowel-preceded), and classifying `ஃ` and pure consonants `வலி/மெலி/இடை` excluding `வ்`).
- **`is_kurriyaligaram_context(first: &str, second: &str) -> bool`**: Checks Sutra 93/164 (`classify_ugaram(first)` is one of the 6 *Kurriyalugaram* classes AND `second` starts with `ய`).
- **`is_valid_mozhi_muthal(word: &str, strict_native: bool) -> bool`**: Implements Sutras 102–106 (12 vowels; 6 unrestricted consonants `{க, ச, த, ந, ப, ம}`; `வ` 8-vowel set; `ய` 6-vowel set; `ஞ` 4-vowel set; `ங` only in `ஙனம்` bound context).
- **`is_valid_mozhi_eetru(word: &str) -> bool`**: Implements Sutras 107–108 (12 vowels, 11 pure consonants `{ஞ், ண், ந், ம், ன், ய், ர், ல், வ், ழ், ள்}`, excluding `C+எ`, `C+ஒ` except `நொ`, and `C+ஔ` except `{கௌ, வௌ}`).

### 2. `closed_class.rs` (or `lexicon/punarchi_*.toml` compiled tables)
- **Panpu stems (Sutra 135–136)**: Closed-class table of `-மை` qualitative stems (`செம்மை, சிறுமை, வெம்மை, புதுமை, மென்மை, மேன்மை, திண்மை, உண்மை, நுண்மை, வெண்மை, கருமை, பொன்மை, பசுமை, பெருமை, அணிமை, நன்மை, தண்மை, பழமை, வன்மை, கீழ்மை, நொய்மை, இன்மை, பருமை, நெடுமை, வெறுமை, முதுமை, ...`) with their pre-computed allomorphs (`ஆதி நீடல்`, `அடியகரம் ஐயாதல்`, `இடையுகரம் இய்யாதல்`, `தன்னொற்று இரட்டல்`, `முன்னின்ற மெய்திரிதல்`, `இனமிகல்`) so both `join` and `split` are deterministic and fast.
- **Bound `ஙனம்` & `மியா` clitics**: Register `ஙனம்` (with `அ, இ, உ, யா, எ` triggers per Sutra 106) and `மியா` (per Sutra 93).

### 3. `split.rs`
- **Phonotactic pruning**: Filter every candidate `(first, second)` split through `is_valid_mozhi_eetru(first)` and `is_valid_mozhi_muthal(second)` before expensive dictionary/lexicon scoring (with loanword fallback if `strict_native` is off).
- **Kurriyaligaram reversal (Sutra 93)**: On `...<C_v>இ ய...` (`கி, சி, டி, தி, பி, றி` + `ய`), emit candidate `...<C_v>உ` + `ய...` if `classify_ugaram(first) != Mutriyalugaram`.
- **Kurriyalugaram reversal (Sutra 94)**: On `...<C_v><V_2>` or `...ட்ட<V_2>` / `...ற்ற<V_2>`, verify `classify_ugaram` on the reconstructed `...<C_v>உ` stem.
- **Panpu stem reversal (Sutra 136)**: Match stem-initial/medial signatures (`பை[ங்/ந்]-`, `வெற்ற-`, `நெட்ட-`, `சேத்-`, `பாச்-`, `கரி-`, `பெரி-`) against the closed-class `-மை` allomorph table to recover `<stem>மை`.
