# Wiktionary & Kaikki Snapshot Recovery Audit (2026-11-14)

- **Scope:** Feature `021-lexicon-curation` (`T038` PRIMARY dictionary provenance recovery for `SRC-WIKT-TAMIL`, `source_id = 5`)
- **Status:** **`T038` remains `pending` (`[ ]`)** — exact original snapshot artifacts and record-level permalinks were **not recovered within the searched local artifacts and public sources**; no curation approval, license inference, or `T039` human-review claim is recorded here.
- **Evidence bundle (gitignored):** [report.md](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/report.md) and [evidence-index.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/evidence-index.json)

## 1. Executive Findings

1. **Original Wiktionary/Kaikki extraction artifacts are missing locally.** Read-only inspection of [utlkd_reusable_package](C:/Users/abish/Downloads/utlkd_reusable_package) and the `tamil-toolkit` repository found zero copies of `kaikki_tamil.jsonl`, `raw_sources_archive/`, `new_sources/`, harvest logs, ingestion/merge scripts, `pageid`s, or `oldid` permalinks.
2. **The owner's `publication_year = 2024` is inconsistent with treating the entire merged slice as an unchanged 2024 extraction.** Sampled entries and module behavior match later revisions, suggesting a candidate extraction interval of **`>= 2026-08-08T17:06:29Z`** and **`< 2026-11-09T14:12:33Z`**, with revision pins reaching **`2026-08-27T16:28:58Z`** and IPA behavior matching Kaikki's **`2026-10-30`** build of **`enwiktionary-20261001`** (`access_date = 2026-11-01`).
3. **Upstream JSONL schema cannot retroactively supply revision IDs.** Even if the owner's `kaikki_tamil.jsonl` existed, `wiktextract` (`src/wiktextract/wiktionary.py`, `src/wiktextract/extractor/en/page.py`, and `README.md`) emits word-entry objects without `pageid`, `revid`, `oldid`, or per-entry revision timestamps, and `kaikki.org` overwrites its single Tamil download in place without a permanent snapshot archive.
4. **Source system is English Wiktionary (`en.wiktionary.org`), not Tamil Wiktionary (`ta.wiktionary.org`).** Glosses, etymology prose, and template phrasing match English Wiktionary (`ta.wiktionary.org` entries for `அடடா`, `நன்றி`, and `வணக்கம்` differ materially in structure and definitions).
5. **Serious schema/field-level transformations prevent bulk reuse as-is.** Inside the `8,575` Wiktionary-linked lemmas in `utlkd_primary.sqlite`, `371` lemmas mix Wiktionary senses with Madras Tamil Lexicon (`DSAL`) senses on the same `word_id`, some entries fold senses from *other* Wiktionary pages (`ஒன்றன்பால்`, `பலவின்பால்`, `அக்கரை`, `இயல்`) or inflections onto one lemma, multi-POS entries collapse under a single POS tag, etymologies insert synthetic `*PDr-*` / `DEDR` metadata absent from Wiktionary, and `verb_conjugations` contains algorithmically corrupted derived strings (`அருள்வஆன்`, `அறிப்பஆன்`, `அருள்ம்`).
6. **Actionable path forward:** Because historical snapshot identity cannot be closed without the owner's original archive or ingestion logs, `T038` stays pending. An independent, reproducible fresh small PRIMARY candidate subset can be anchored directly to pinned `en.wiktionary.org` `oldid` permalinks and a pinned Wikimedia dump (`20261001` or `20261101`), isolating verified literal senses/IPA/etymology prose from derived morphology and mixed DSAL material.

---

## 2. Local SQLite & Package Recovery Findings (Read-Only)

All database checks were opened strictly read-only (`mode=ro&immutable=1`) on [utlkd_primary.sqlite](C:/Users/abish/Downloads/utlkd_reusable_package/databases/utlkd_primary.sqlite) and [utlkd_secondary.sqlite](C:/Users/abish/Downloads/utlkd_reusable_package/databases/utlkd_secondary.sqlite), cross-checked against [primary_lemmas.csv](C:/Users/abish/Documents/dev/tamil-toolkit/data/sources/tamil-lexicon/primary_lemmas.csv), [primary_meanings.csv](C:/Users/abish/Documents/dev/tamil-toolkit/data/sources/tamil-lexicon/primary_meanings.csv), and [pilot-selection.toml](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/tamil-lexicon/pilot-selection.toml).

### 2.1 `sources` Row `source_id = 5` (`SRC-WIKT-TAMIL`) & Distribution Counts

| Field / Metric | Observed Value (`utlkd_primary.sqlite`) | Notes / Verification Gap |
| --- | --- | --- |
| `source_id` / `source_code` | `5` / `SRC-WIKT-TAMIL` | Single row representing all Wiktionary/Kaikki intake |
| `title` / `creator` / `publisher` | `Wiktionary Tamil Lexical Extraction` / `Wiktionary Contributors and Wiktextract` / `Wikimedia Foundation / Kaikki.org` | Owner-entered metadata; no `wiktextract` git SHA or dump tag |
| `publication_year` / `edition` | `2024` / `NULL` | **Unverified as snapshot year**; sampled content matches later revisions, but merged-field lineage is incomplete |
| `url` / `access_date` | `https://kaikki.org/dictionary/Tamil/` / `2026-11-01` | Index landing URL only; `dataset_releases.release_date` = `2026-11-07 06:06:11` |
| `reuse_status` / `licence_id` / `notes` | `open_license` / `NULL` / `Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)` | Omits dual GFDL option and per-entry attribution URLs |
| Union of Wiktionary-linked `word_id`s | **`8,575`** distinct `word_id`s | Across `tamil_words`, `word_source_links`, `word_meanings`, and `etymologies` |
| `tamil_words.notes` LIKE `%wikt%` | **`8,451`** (`8,412` `"Ingested and verified from Wiktionary Tamil Lexicon."`; `39` `"... extraction."`) | IPA distribution inside the `8,451` lemmas is heterogeneous (`1,545` `U+032F`, `5` `ə`, `158` `ʌ`, `6,052` `ɐ`, `6,030` `ː`; `0` `(கலைச்சொல்)`) |
| `word_source_links` (`source_id = 5`) | **`8,549`** (`8,489` + `39` generic notes; `21` `NULL`) | Generic boilerplate only; zero `pageid`, `revid`, `oldid`, or URL |
| `word_meanings.notes` LIKE `%wikt%` | **`26,138`** rows across **`8,544`** `word_id`s (`23,099` `"Sense verified..."`; `3,039` `"Additional sense verified and deduplicated..."`) | **`371`** of those `8,544` words mix Wiktionary and non-Wiktionary (mostly DSAL) senses; **`2,917`** Wiktionary-tagged meanings have non-empty `definition_ta`/`meaning_ta` from folding |
| `etymologies` (`source_id = 5`) | **`7,686`** rows | Mixes Wiktionary prose with synthetic `*PDr-*` / `DEDR` fields |
| `source_evidence` (`source_id = 5`) | **`0`** rows | Zero stored evidence quotes/URLs/permalinks for Wiktionary |
| `pilot-selection.toml` overlap | **`27`** of **`101`** primary pilot `word_id`s | Includes `1921`, `3906`, `4525`, `6306`, `8217`, `8218`, `28857` |

### 2.2 Secondary Package Contradiction (`kaikki_tamil.jsonl` Claim)

- [deepseek_tamil_slang_catalog.md:20-58](C:/Users/abish/Downloads/utlkd_reusable_package/documentation/deepseek_tamil_slang_catalog.md:20-58) claims that `583` dialect-tagged records were parsed from `kaikki_tamil.jsonl` and `400` `kaikki_wiktionary` rows were staged into `utlkd_secondary.sqlite`.
- Direct read-only query of `utlkd_secondary.sqlite` `staged_dialect_colloquialisms` shows **`0`** rows mentioning `kaikki` or `wikt` in `notes`. Neither `kaikki_tamil.jsonl` nor that extraction script exists in [utlkd_reusable_package](C:/Users/abish/Downloads/utlkd_reusable_package).

---

## 3. Revision and Template Consistency Clues (Original Snapshot Unverified)

Systematic comparison between `utlkd_primary.sqlite` records and live `en.wiktionary.org` MediaWiki revision histories (`target/lexicon/wiktionary-recovery/candidate_api_checks/`) provides conditional timing clues for sampled fields. It does not establish one extraction date for a merged dataset:

1. **Lower bound `>= 2025-06-22` & `>= 2025-08-09` (pages did not exist in 2024):**
   - `அக்கறை` (`word_id = 88`, `pageid = 11011658`): page created `2025-06-22T16:57:10Z` (`revid = 85271194`).
   - `அடடா` (`word_id = 1921`, `pageid = 11100687`, pilot): page created `2025-08-09T18:54:09Z` (`revid = 85842017`).
2. **Lower bound `>= 2025-12-05` .. `2026-03-20` (content added in late 2025 – early 2026):**
   - `அறிக்கை` (`word_id = 8218`, `pageid = 9685129`, pilot): `"From அறி (aṟi, “to know”) + -க்- (-k-) + -கை (-kai)"` reflects `{{suf|ta|அறி|-க்-|-கை|t1=to know}}` fixed on `2025-12-05T06:44:33Z` (`revid = 88382210`).
   - `குருகுலம்` (`word_id = 25166`, `pageid = 477967`): `{{lbor|ta|sa|गुरुकुल}}` & `/ɡʊɾ̪ʊkʊl̪əm/` edited on `2026-01-23T08:02:47Z` (`revid = 89321837`) and `2026-02-03T01:32:34Z` (`revid = 89438349`).
   - `அந்நிலை` (`word_id = 3906`, `pageid = 7769127`, pilot): embedded `"Etymology tree\nProto-Dravidian *a-\n..."` comes from `{{ety|...|tree=1}}` added `2026-03-20T08:41:52Z` (`revid = 89903937`).
3. **Lower bound `>= 2026-06-05` -> `>= 2026-08-08` -> `>= 2026-08-27`:**
   - `நன்றி` (`word_id = 32793`, `pageid = 4593930`): SQLite has sense 1 `"thanks, thank you"` and etymology `"from Proto-South Dravidian *nal (“good”)"`. Prior revision `85054486` (`2025-06-07T13:37:18Z`) had only `"thank you"` and `"Proto-Dravidian *nal"`; both edits entered in `revid = 91084863` on **`2026-06-05T13:35:31Z`**.
   - `நன்றி` IPA in SQLite is `/nɐnriː/` (long word-final `/iː/`): `Module:ta-IPA` (`pageid = 7196229`) introduced `"Show word final short <i> as long/tense"` on **`2026-08-08T17:06:29Z`** (`revid = 91919996`).
   - `வணக்கம்` (`word_id = 41705`, `pageid = 546263`): matches `revid = 92361350` (**`2026-08-27T16:28:58Z`**).
4. **Upper bound `< 2026-11-09T14:12:33Z`:**
   - `செப்பம்` (`word_id = 28857`, `pageid = 7902117`, pilot) stores `/tʃɛpːɐm/` (with epsilon `/ɛ/`) in `utlkd_primary.sqlite`, `primary_lemmas.csv`, **and** Kaikki's `2026-10-30` HTML page ([kaikki_sample_ceppam.html](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/candidate_api_checks/kaikki_sample_ceppam.html)). Live `en.wiktionary.org` `{{ta-IPA}}` now expands `செப்பம்` to `/tʃepːɐm/` because `Module:ta-IPA` removed `/ɛ/` in `revid = 95464085` on **`2026-11-09T14:12:33Z`** (comment: `"Avoid use of epsilon /ɛ/"`).

**Conditional timing summary:** Sampled fields are consistent with extraction between **`2026-08-27`** (or at minimum `2026-08-08`) and **`2026-11-09`**. Together with `sources.access_date = 2026-11-01`, `dataset_releases.release_date = 2026-11-07`, and `enwiktionary-20261101` not finishing `articlesdump` until `2026-11-01 19:48:03Z`, this strongly aligns with Kaikki's **`2026-10-30`** extraction of **`enwiktionary-20261001`** (`Last-Modified: Fri, 30 Oct 2026 23:05:56 GMT`). Because neither the downloaded JSONL file nor its SHA-256 nor ingestion script exists locally, this remains a **forensic consistency window**, not proof of byte-exact original snapshot closure.

---

### Orchestrator confidence correction

A single extraction interval is not proven. The package is a merged dataset; fields may have been added at different times, copied from cached extracts or generated by another pipeline. A page-creation date bounds direct copying from that page only if that copying is established; matching text alone cannot exclude an earlier shared source. IPA module changes similarly constrain an expansion only if the module revision used is known. Rendering an old page revision today can use newer transcluded templates/modules, so a page `oldid` alone does not pin generated IPA. Preserve raw page content plus the dependency revisions or a hashed historical expansion when claiming reproducibility. Matching the October Kaikki build supports a candidate lead, not a recovered original dump identity. The Wayback capture dated after owner-reported access is not disqualified solely by capture date; it could preserve the same previously served file, but its bytes have not been proven identical to the owner's missing file. Absence of tags in the inspected extractor files also does not prove that every extractor version or auxiliary metadata format omits revision identifiers.

## 4. Official Upstream Metadata & Historical Snapshot Availability

All fetched files and SHA-256 digests are recorded in [official_metadata/fetch_manifest.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/official_metadata/fetch_manifest.json):

- **Kaikki.org Tamil Index** ([https://kaikki.org/dictionary/Tamil/](https://kaikki.org/dictionary/Tamil/)):
  - Reports `11,203` distinct Tamil words across `18,748` Noun, `6,235` Verb, `1,568` Proper name, `641` Adjective, `513` Adverb, etc. senses.
  - States on page: *"structured data extracted on 2026-10-30 from the enwiktionary dump dated 2026-10-01 using wiktextract (19f9a30 and 6f96ddf)."*
  - Serves `kaikki.org-dictionary-Tamil.jsonl` (`Content-Length: 89,383,804`, `ETag: "6ae522d4-553e37c"`) and `.jsonl.gz` (`9,824,360` bytes), both `Last-Modified: Fri, 30 Oct 2026 23:05:56 GMT`, explicitly labeled **postprocessed** and **`DEPRECATED`** per [tatuylonen/wiktextract#1178](https://github.com/tatuylonen/wiktextract/issues/1178) because website post-processing alters raw entries.
- **Kaikki.org Raw Data Page** ([https://kaikki.org/dictionary/rawdata.html](https://kaikki.org/dictionary/rawdata.html)):
  - Offers full unprocessed English Wiktionary raw extracts (`raw-wiktextract-data.jsonl` / `.jsonl.gz`) from the same `2026-10-30` / `enwiktionary-20261001` run rather than per-language historical snapshots.
- **Wikimedia Dumps Retention** ([https://dumps.wikimedia.org/enwiktionary/](https://dumps.wikimedia.org/enwiktionary/), [https://dumps.wikimedia.org/tawiktionary/](https://dumps.wikimedia.org/tawiktionary/)):
  - Retain only 10 monthly snapshots (`20260201/` through `20261101/`); all 2024–2025 dumps are pruned.
  - `enwiktionary/20261001/dumpstatus.json` confirms `articlesdump` `status: "done"`, `updated: "2026-10-01 15:25:24"`.
  - `enwiktionary/20261101/dumpstatus.json` confirms `articlesdump` `status: "done"`, `updated: "2026-11-01 19:48:03"`.
- **Wayback Machine CDX Check** (`wayback_kaikki_tamil_cdx.json`, `wayback_kaikki_jsonl_cdx.json`):
  - Archived HTML captures of `/dictionary/Tamil/` exist (e.g., `20241129`, `20251027`, `20260906`, `20261103`).
  - Only 4 JSON/JSONL captures exist (`20231209` `113 KB`; `20241009` `110 KB`; `20251118` `515 KB`; `20261103` `9.8 MB`), none providing an independently verified pre-`2026-11-01` complete match (`20261103` postdates `access_date = 2026-11-01`; earlier captures are truncated/pre-2026).
- **`wiktextract` Upstream Schema** ([tatuylonen/wiktextract README](https://github.com/tatuylonen/wiktextract/blob/master/README.md)):
  - Inspection of local fetched copies ([wiktextract_wiktionary.py](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/candidate_api_checks/wiktextract_wiktionary.py), [wiktextract_en_page.py](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/candidate_api_checks/wiktextract_en_page.py), [wiktextract_readme.md](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/official_metadata/wiktextract_readme.md)) confirms **0** references to `revid`, `oldid`, `pageid`, or `dump_date` in output objects.
  - Upstream [LICENSE](https://github.com/tatuylonen/wiktextract/blob/master/LICENSE) is MIT for the extractor software only and confers no license over Wiktionary data.

---

## 5. License & Machine-Readable Attribution Requirements

Official policy sources retrieved into [official_metadata/](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-recovery/official_metadata/):

- **Wiktionary Copyrights** ([https://en.wiktionary.org/wiki/Wiktionary:Copyrights](https://en.wiktionary.org/wiki/Wiktionary:Copyrights), `revid = 87545419`, `2025-10-22T20:09:50Z`): text is available under both **CC BY-SA 4.0** and the **GNU Free Documentation License (GFDL)**.
- **Wikimedia Terms of Use §7** ([https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use), `revid = 598588`, `2026-10-25T01:07:30Z`): specifies dual licensing under CC BY-SA 4.0 and GFDL (`unversioned, with no invariant sections, front-cover texts, or back-cover texts`), adding: *"Reusers may comply with either license or both."* For contributor attribution, §7(b)(i) allows credit *"Through hyperlink (where possible) or URL to the article to which you contributed"*.
- **CC BY-SA 4.0 Legal Code §3(a)** ([https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt](https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt)): when sharing material (including modified form), reusers must retain creator identification, a copyright notice, license notice with URI, warranty disclaimer notice, *"a URI or hyperlink to the Licensed Material to the extent reasonably practicable"* (§3(a)(1)(A)(v)), and *"indicate if You modified the Licensed Material"* (§3(a)(1)(B)). Under §3(b), Adapted Material shared downstream must use CC BY-SA 4.0 (or compatible ShareAlike license).

**Proposed provenance fields for this project (engineering requirements, not a claim that every field is legally mandatory):**
1. `source_wiki` (`en.wiktionary.org`), `dump_date` (`YYYYMMDD`), `dump_url`, and extractor tool/commits (if Kaikki/wiktextract is used, plus academic citation to Ylonen LREC 2022 if citing Kaikki).
2. Entry-level `page_title`, `page_id`, `revision_id`, `revision_timestamp`, `permalink_url` (`https://en.wiktionary.org/w/index.php?title=...&oldid=...`), and `content_sha256` (since Kaikki omits `revid`, downstream ingestion must resolve exact `page_id`/`revid` from the pinned XML dump or MediaWiki API).
3. `license_spdx` (`CC-BY-SA-4.0` for the proposed CC route; preserve the upstream GFDL notice separately and verify any alternative identifier before use), `license_uri` (`https://creativecommons.org/licenses/by-sa/4.0/`), `author_attribution_url` (history/article URL), and `modification_note` (explicitly noting template expansion, POS splitting, gloss cleanup, and omitted/separated non-Wiktionary fields).

---

## 6. Compact Candidate Validation (Definitions vs. IPA vs. Derived Grammar)

Sixteen audited `utlkd_primary.sqlite` records (`word_id`s verified identically in `primary_lemmas.csv` and `primary_meanings.csv`) were checked against live MediaWiki revisions (`enwikt_rev_*.json`), `{{ta-IPA}}` expansions (`enwikt_ta_ipa_expand.json`), `enwikt_folded_check.json`, and `verb_conjugations`. Every homograph sibling in `utlkd_primary.sqlite` is explicitly preserved.

| `word_id` (Headword) | Pilot? | Homographs (`word_id` / POS / Source) | `en.wiktionary` Pin (`pageid` / `oldid`) | Definitions (Literal Status) | IPA (Literal vs. Template-Expanded) | Derived Grammar / Mixed / Corrupted Fields | Candidate Eligibility Assessment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1921` **அடடா** | Yes | Single lemma (`INTJ`) | `11100687` / [85842017](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%9F%E0%AE%9F%E0%AE%BE&oldid=85842017) (`2025-08-09`) | **Clean**: s1–s2 match `{{ng}}` glosses verbatim (minus trailing `.`) | `/ɐɖɐɖɑː/` matches `{{ta-IPA}}` | `0` `verb_conjugations`; etymology `"From அடா + அடா"` literal | **Candidate for source verification; not approved** (literal Wiktionary record) |
| `3906` **அந்நிலை** | Yes | Single lemma (`NOUN`) | `7769127` / [89903937](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%A8%E0%AF%8D%E0%AE%A8%E0%AE%BF%E0%AE%B2%E0%AF%88&oldid=89903937) (`2026-03-20`) | **Clean**: s1 `"that moment"` verbatim | `/ɐnːɪlɐɪ̯/` matches `{{ta-IPA}}` | `0` `verb_conjugations`; embeds rendered `{{ety\|tree=1}}` text | **Candidate for source verification; not approved** (also timeline pin `>= 2026-03-20`) |
| `8218` **அறிக்கை** | Yes | Single lemma (`NOUN`) | `9685129` / [88382210](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%88&oldid=88382210) (`2025-12-05`) | **Clean**: s1–s4 match Wiktionary glosses | `/ɐrɪkːɐɪ̯/` matches `{{ta-IPA}}` | Etymology adds synthetic `origin_form = *aṯ-V-` / `DEDR 314` absent in Wiktionary | **Clean candidate** for headword + IPA + s1–s4 if synthetic `*aṯ-V-` excluded |
| `28857` **செப்பம்** | Yes | Single lemma (`NOUN`) | `7902117` / [61485513](https://en.wiktionary.org/w/index.php?title=%E0%AE%9A%E0%AF%86%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AE%AE%E0%AF%8D&oldid=61485513) (`2021-01-04`) | **Clean**: s1–s9 match Wiktionary glosses | `/tʃɛpːɐm/` matches Kaikki `2026-10-30`; live `{{ta-IPA}}` now expands `/tʃepːɐm/` | Template-expanded IPA drifted `2026-11-09` (`Module:ta-IPA` `95464085`); etymology adds `*PDr-2747` / `DEDR 2747` | **Clean definitions**; **conditional pre-module-change clue**; use pinned dump/expansion for IPA |
| `5` **அஃகம்** | No | Single lemma (`NOUN`, **mixed**) | `4527631` / [83934478](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%83%E0%AE%95%E0%AE%AE%E0%AF%8D&oldid=83934478) (`2025-02-14`) | **Mixed**: s1–s4 literal Wiktionary; **s5–s6 are DSAL** | `/əʰɦam/` literal in `{{IPA\|ta\|/əʰɦam/}}` | s5–s6 (`meaning_id` `14`–`15`) must be excluded (`Madras Tamil Lexicon`) | Consider for verification **only** if sliced to s1–s4 + `/əʰɦam/` |
| `10` **அஃகு** | No | `10` (`NOUN`, Wikt+DSAL); **`11`** (`VERB`, DSAL) | `10102156` / [78542632](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%83%E0%AE%95%E0%AF%81&oldid=78542632) (`2024-03-21`) | **Mixed**: s1 literal (`oozing water`); **s2 is DSAL** | `/ɐxɯ/` reflects older `{{ta-IPA}}` before `2026-08-24` `ɨ`/`ɯ` edits | Etymology invents `*PDr-252` / `DEDR 252` (`en.wiktionary` has `{{rfe\|ta}}`) | Keep homograph `11` separate; strip s2 & `*PDr-252`, verify `{{ta-IPA}}` |
| `595` **அகல்** | No | **`594`** (`NOUN`, DSAL); `595` (`VERB`, Wikt+DSAL) | `8428612` / [80094195](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%95%E0%AE%B2%E0%AF%8D&oldid=80094195) (`2024-06-03`) | **Mixed**: s1–s5 literal Wiktionary; **s6 is DSAL** | `/ɐɡɐl/` matches `{{ta-IPA}}` | **23 derived `verb_conjugations`** (non-verbatim vs `{{ta-conj}}`); s6 DSAL; synthetic `*akam` | Consider for verification **only** for s1–s5 + `/ɐɡɐl/`, excluding s6 & `verb_conjugations`; keep `594` distinct |
| `32793` **நன்றி** | No | Single collapsed lemma (`NOUN`) | `4593930` / [93647113](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%A9%E0%AF%8D%E0%AE%B1%E0%AE%BF&oldid=93647113) (`2026-10-17`) | **POS-collapsed**: s1 is `INTJ`, s2–s3 are `NOUN` | `/nɐnriː/` matches `{{ta-IPA}}` (`>= 2026-08-08`) | `INTJ` + `NOUN` collapsed onto `NOUN`; etymology adds `*nan-key` / `DEDR 3610` | **Critical `>= 2026-06-05`/`08-08` pin**; clean if split into `INTJ` + `NOUN` |
| `41705` **வணக்கம்** | No | Single collapsed lemma (`NOUN`) | `546263` / [92361350](https://en.wiktionary.org/w/index.php?title=%E0%AE%B5%E0%AE%A3%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AE%AE%E0%AF%8D&oldid=92361350) (`2026-08-27`) | **POS-collapsed**: s1–s3 are `INTJ`, s4–s8 are `NOUN` | `/ʋɐɳɐkːɐm/` matches `{{ta-IPA}}` | `INTJ` + `NOUN` collapsed onto `NOUN`; synthetic `*PDr-5236` | Clean if split into `INTJ` + `NOUN` pinned to `92361350` |
| `25166` **குருகுலம்** | No | Single collapsed lemma (`NOUN`) | `477967` / [89438349](https://en.wiktionary.org/w/index.php?title=%E0%AE%95%E0%AF%81%E0%AE%B0%E0%AF%81%E0%AE%95%E0%AF%81%E0%AE%B2%E0%AE%AE%E0%AF%8D&oldid=89438349) (`2026-02-03`) | **Multi-etymology collapsed**: s1 (`Noun`) + s2–s3 (`Proper noun`) | `/ɡʊɾ̪ʊkʊl̪əm/` (Ety 1 only; drops Ety 2 `/kʊɾʊkʊlɐm/`) | Two Wiktionary `Etymology` sections & IPA values merged onto one `NOUN` row | Split Ety 1 (`NOUN`) and Ety 2 (`PROPN`) in fresh extraction |
| `21` **அஃறிணை** | No | Single lemma (`NOUN`, **folded**) | `8826225` / [87897173](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%83%E0%AE%B1%E0%AE%BF%E0%AE%A3%E0%AF%88&oldid=87897173) (`2025-11-01`) | **Folded**: s1 from page; **s2–s3 folded** from `ஒன்றன்பால்` & `பலவின்பால்` | `/əɦrɪɳəɪ̯/` literal in `{{IPA\|ta\|/əɦrɪɳəɪ̯/}}` | Cross-page folding from `pageid = 10049160` (`88248818`) & `10049175` (`88248827`) | **Reject folded s2–s3** under `word_id = 21`; keep s1 only or split |
| `88` **அக்கறை** | No | Single lemma (`NOUN`, **folded**) | `11011658` / [88620855](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AE%B1%E0%AF%88&oldid=88620855) (`2025-12-16`) | **Folded**: s1–s3 from page; **s4–s6 folded** from `அக்கரை` | `/ɐkːɐrɐɪ̯/` matches `{{ta-IPA}}` | Cross-page folding from `அக்கரை` (`9905086` / `86586931`); divergent `*PDr-21` etymology | Reject folded s4–s6 under `word_id = 88`; keep s1–s3 + IPA only |
| `4525` **அம்மை** | Yes | Single lemma (`NOUN`, **mixed+collapsed**) | `8825955` / [89027817](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%AE%E0%AF%8D%E0%AE%AE%E0%AF%88&oldid=89027817) (`2026-01-02`) | **Mixed+collapsed**: s1–s4 (`Noun`), s5 (`Proper noun`), **s6–s8 DSAL** | `/ɐmːɐɪ̯/` (`{{ta-IPA}}` not separately expanded in probe) | DSAL s6–s8 mixed; `PROPN` s5 collapsed; synthetic `*aṯṯ-` vs `*amma` | Do **not** accept raw row; must strip DSAL & split `PROPN` |
| `6306` **அருள்** | Yes | **`6305`** (`NOUN`, DSAL); `6306` (`VERB`, collapsed) | `8355802` / [88270113](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B0%E0%AF%81%E0%AE%B3%E0%AF%8D&oldid=88270113) (`2025-11-24`) | **POS-collapsed**: s1–s2 (`Verb`) + s3–s6 (`Noun`) | `/ɐɾʊɭ/` | **23 corrupted derived `verb_conjugations`** (e.g., `அருள்வில்லை`, `அருள்ம்`, `அருள்வஆன்`); `NOUN` folded into `VERB` | Strip `verb_conjugations`; split `VERB` vs `NOUN`; keep `6305` distinct |
| `8217` **அறி** | Yes | **`8216`** (`NOUN`, DSAL); `8217` (`VERB`, mixed+collapsed+folded) | `7904251` / [90949987](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF&oldid=90949987) (`2026-05-26`) | **Mixed+collapsed+folded**: s1/s13 DSAL; s2–s7 `Verb`; s8 `Noun`; **s9–s12 inflections** | `/ʌri/` (non-Wiktionary `/ʌ/`) | **26 corrupted derived `verb_conjugations`** (e.g., `அறிக்கவில்லை`, `அறிப்பஆன்`); inflections & DSAL mixed | **Unusable as clean candidate** without full decomposition |
| `30010` **தமிழ்** | No | Single collapsed lemma (`ADJ`) | Separate `இயல்` verified (`7317690` / `89603267`) | **POS-collapsed+folded+inflected**: s1–s3 (`ADJ`), s4–s9 (`NOUN`), **s10–s21 `இயல்`**, **s22–s33 case forms** | `/t̪ɐmɪɻ/` | Collapses `ADJ` + `NOUN` + 12 senses of `இயல்` + 12 declined case forms | **Reject composite row**; re-extract per lemma/POS from pinned dump |

---

## 7. Closure Decision & Actionable Next Options

### 7.1 Why `T038` Remains `pending` (`[ ]`)

Historical provenance closure for the existing `SRC-WIKT-TAMIL` slice (`8,575` lemmas) is **blocked** without genuine upstream artifacts:
- Matching word definitions or IPA inside a `[2026-08-27, 2026-11-09)` window suggests possible derivation from English Wiktionary / Kaikki around `2026-10-30`, **not** byte-level file identity, clean separation from synthetic fields, or license-compliant per-entry revision attribution.
- Per `specs/021-lexicon-curation/contracts/curation.md`, owner SQLite labels (`open_license`, generic `evidence_note`) do **not** satisfy `T038` or authorize `T039`.

### 7.2 Minimal Owner Input That Would Close Historical Lineage (If Obtainable)

1. Original `kaikki_tamil.jsonl` archive (or SHA-256 + `Last-Modified` / extraction commit metadata) and the Python/Rust ingestion & deduplication scripts that merged Wiktionary, DSAL, DEDR `*PDr-*`, cross-page foldings (`அக்கரை`, `இயல்`, `ஒன்றன்பால்`), and `verb_conjugations` into `utlkd_primary.sqlite`.
2. Any harvest log linking `word_id`s to exact Kaikki/Wiktionary entry URLs or revision IDs.

### 7.3 Actionable Option: Fresh Independently Sourced Small PRIMARY Candidate (Pinned Official Dump/Revisions)

If the original `kaikki_tamil.jsonl` and ingestion scripts remain unrecoverable, Feature `021` can pursue a **clean, strictly scoped fresh candidate track** (separate from the quarantined original `SRC-WIKT-TAMIL` bulk slice, leaving all 12 frozen original files untouched):
1. **Pin an official, immutable upstream snapshot:** Select Wikimedia's official `enwiktionary` XML dump (`20261001` or `20261101` — both currently downloadable from `dumps.wikimedia.org/enwiktionary/`) together with per-page `pageid` + `oldid` + timestamp + content SHA-256 extracted directly from the dump XML (never relying solely on undated `kaikki.org` postprocessed JSONL without revision IDs).
2. **Start with a clean, verified small candidate subset:** E.g., clean single-POS, non-DSAL-mixed pilot entries (`1921 அடடா`, `3906 அந்நிலை`, `8218 அறிக்கை`, `28857 செப்பம்`) plus cleanly split non-folded senses from `5 அஃகம்` (s1–s4), `595 அகல்` (s1–s5 + homograph `594` separation), `32793 நன்றி` (`INTJ`/`NOUN` split), and `41705 வணக்கம்` (`INTJ`/`NOUN` split).
3. **Strictly exclude derived/corrupted fields from upstream attribution:** Never tag algorithmic `verb_conjugations` (`அருள்வஆன்`, `அறிப்பஆன்`), synthetic `*PDr-*` / `DEDR` codes, or cross-page folded glosses as literal Wiktionary fields; if morphology or IPA normalization is generated later in `tamil-toolkit`, keep it strictly inside native Rust (`crates/tamil-*`) or clearly labeled downstream layers rather than attributing it to Wiktionary.
4. **Editorial writes remain outside this recovery audit.** Verification can proceed with fresh source assertions and pending proposals under the existing review machinery; only acceptance decisions need the applicable genuine reviewer or specified source-verification path. Do not treat this audit as approval of either historical artifacts or fresh source policy (including **CC BY-SA 4.0** ShareAlike implications for any pack bundling Wiktionary data).
