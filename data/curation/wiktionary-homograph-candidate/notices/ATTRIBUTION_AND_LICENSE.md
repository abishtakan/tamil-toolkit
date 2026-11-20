# Attribution, License Notices, and Disclaimers (Pending Wiktionary Homograph Candidate)

> **Important Scope Notice (No Legal Advice / No Compliance Certification):**  
> This document records source-specific attribution metadata, license texts, and disclaimers gathered from official Wikimedia Foundation and Creative Commons sources for review in `tamil-toolkit`. It is engineering provenance documentation only — **not legal advice** and **not a claim of complete legal compliance**.

## 1. Proposed Data License Route (`CC-BY-SA-4.0`) and Engine Separation

- **Data Route Proposed:** Creative Commons Attribution-ShareAlike 4.0 International (`CC-BY-SA-4.0`), as set out in English Wiktionary's copyright policy (`Wiktionary:Copyrights`, `pageid=1503`, `revid=87545419`, `2025-10-22T20:09:50Z`) and the Wikimedia Foundation Terms of Use (`Policy:Terms_of_Use`, `pageid=21261`, `revid=598588`, `2026-10-25T01:07:30Z`). Upstream Wiktionary text may also be available under the GNU Free Documentation License (`GFDL`) for unmigrated/applicable portions per Wikimedia ToU §7.
- **Data vs. Tooling / Engine Separation:**
  - `CC-BY-SA-4.0` applies **only to the Wiktionary source snapshot and candidate lexical data** under `data/curation/wiktionary-homograph-candidate/`.
  - It does **not** apply MIT (the toolkit/extractor license) to Wiktionary data, and it does **not** relicense the Rust core crates (`crates/*`) or runtime engine under `CC-BY-SA-4.0`.
  - Downstream ShareAlike implications for bundling CC-BY-SA-4.0 material into any distributable lexicon pack remain **pending explicit L3 human/policy review** (`reuse_state = "restricted"` in `sources.csv`; `0` accepted or runtime claims).

## 2. Official Pinned Source & Contributor Attribution Link

| Legacy `word_id` | Headword (`tam`) | Source POS Sections | `pageid` | Pinned `oldid` | Revision Timestamp (UTC) | Revision User (API) | Permalink & Revision History |
|---|---|---|---:|---:|---|---|---|
| `32793` | நன்றி | `===Interjection===` (`INTJ`), `===Noun===` (`NOUN`) | `4593930` | `93647113` | `2026-10-17T21:53:52Z` | `FenaBot` | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%A9%E0%AF%8D%E0%AE%B1%E0%AE%BF&oldid=93647113) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%A9%E0%AF%8D%E0%AE%B1%E0%AE%BF&action=history) |

## 3. Summary of Modifications Made to Pinned Wikitext

Per `CC-BY-SA-4.0` §3(a)(1)(B), any modification from the upstream revision is explicitly tracked:

1. **POS homograph split from source sections (no invented split):** The single page `நன்றி` contains distinct `===Interjection===` (line 15, sense line 18) and `===Noun===` (line 20, sense lines 23 and 26) headings under `==Tamil==`. These project into two separate candidate `entries.csv` rows sharing canonical written headword `நன்றி`.
2. **Excluded lines (`provenance/exclusions.json`):** `{{phrasebook|ta}}`, `===Alternative forms===` (`{{alt}}`), `===Etymology===` (`{{m}}`, `{{der}}`, `*nal`, `{{cog}}`), `===Pronunciation===` (`{{ta-IPA}}`), `{{ta-interj}}`, `{{ta-noun}}`, synonyms (`#: {{syn}}`), quotation block (`#* {{quote-book}}`), declension (`{{ta-decl}}`), derived terms/see-also (`{{col}}`), `{{reflist}}`, and category templates (`{{cln}}`, `{{C}}`).
3. **Inline wikilink markup unwrapping (held `needs_review`):** `[[target]]` brackets stripped to visible text on the three English definition lines.

## 4. Preserved Official Notice Snapshots

- [cc_by_sa_4_0_legalcode.txt](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-homograph-candidate/notices/cc_by_sa_4_0_legalcode.txt)
- [wikimedia_tou_api.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-homograph-candidate/notices/wikimedia_tou_api.json)
- [wiktionary_copyrights_api.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-homograph-candidate/notices/wiktionary_copyrights_api.json)
- [fetch_manifest.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-homograph-candidate/notices/fetch_manifest.json)
