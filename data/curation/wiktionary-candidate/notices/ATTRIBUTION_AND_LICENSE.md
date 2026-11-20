# Attribution, License Notices, and Disclaimers (Pending Wiktionary Candidate)

> **Important Scope Notice (No Legal Advice / No Compliance Certification):**  
> This document records source-specific attribution metadata, license texts, and disclaimers gathered from official Wikimedia Foundation and Creative Commons sources for review in `tamil-toolkit`. It is engineering provenance documentation only — **not legal advice** and **not a claim of complete legal compliance**.

## 1. Proposed Data License Route (`CC-BY-SA-4.0`) and Engine Separation

- **Data Route Proposed:** Creative Commons Attribution-ShareAlike 4.0 International (`CC-BY-SA-4.0`), as set out in English Wiktionary's copyright policy (`Wiktionary:Copyrights`, `pageid=1503`, `revid=87545419`, `2025-10-22T20:09:50Z`) and the Wikimedia Foundation Terms of Use (`Policy:Terms_of_Use`, `pageid=21261`, `revid=598588`, `2026-10-25T01:07:30Z`). Upstream Wiktionary text may also be available under the GNU Free Documentation License (`GFDL`) for unmigrated/applicable portions per Wikimedia ToU §7.
- **Data vs. Tooling / Engine Separation:**
  - `CC-BY-SA-4.0` applies **only to the Wiktionary source snapshots and candidate lexical data** under `data/curation/wiktionary-candidate/`.
  - It does **not** apply MIT (the toolkit/extractor code license) to Wiktionary data, and it does **not** relicense the Rust core crates (`crates/*`) or runtime engine under `CC-BY-SA-4.0`.
  - Downstream ShareAlike implications for bundling CC-BY-SA-4.0 material into any distributable lexicon pack remain **pending explicit L3 human/policy review** (`reuse_state = "restricted"` in `sources.csv`; `0` accepted or runtime claims).

## 2. Official Pinned Sources & Contributor Attribution Links

Per Wikimedia Terms of Use §7(b) and `CC-BY-SA-4.0` §3(a)(1), attribution for each extracted entry preserves page title, pinned revision `oldid`, timestamp, contributor/editor handle from the API revision record, permalink URL, and revision history URL:

| Legacy `word_id` | Headword (`tam`) | `pageid` | Pinned `oldid` | Revision Timestamp (UTC) | Revision User (API) | Permalink & Revision History |
|---|---|---|---|---|---|---|
| `1921` | அடடா | `11100687` | `85842017` | `2025-08-09T18:54:09Z` | `Pixelpito` | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%9F%E0%AE%9F%E0%AE%BE&oldid=85842017) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%9F%E0%AE%9F%E0%AE%BE&action=history) |
| `3906` | அந்நிலை | `7769127` | `89903937` | `2026-03-20T08:41:52Z` | `Pixelpito` | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%A8%E0%AF%8D%E0%AE%A8%E0%AE%BF%E0%AE%B2%E0%AF%88&oldid=89903937) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%A8%E0%AF%8D%E0%AE%A8%E0%AE%BF%E0%AE%B2%E0%AF%88&action=history) |
| `8218` | அறிக்கை | `9685129` | `88382210` | `2025-12-05T06:44:33Z` | `~2025-38205-63` | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%88&oldid=88382210) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%88&action=history) |
| `28857` | செப்பம் | `7902117` | `61485513` | `2021-01-04T16:15:52Z` | `Hk5183` | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%9A%E0%AF%86%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AE%AE%E0%AF%8D&oldid=61485513) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%9A%E0%AF%86%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AE%AE%E0%AF%8D&action=history) |

## 3. Summary of Modifications Made to Pinned Wikitext

Per `CC-BY-SA-4.0` §3(a)(1)(B), any modification from the upstream revision is explicitly tracked:

1. **Structural projection:** Only `page.title`, declared `==Tamil==` heading, mapped POS section heading (`===Interjection===` → `INTJ`, `===Noun===` → `NOUN`), and literal `# ...` sense lines were projected into CSV candidate tables; all unpinned template expansions (`{{ta-IPA}}`, `{{ety}}`, `{{com}}`, `{{af}}`, `{{suf}}`, `{{m}}`, `{{ux}}`, `{{syn}}`, `{{ta-decl}}`, `{{col3}}`, `{{audio}}`, `{{reflist}}`, `{{R:...}}`, `{{l}}`, `{{C}}`) were excluded and itemized in `provenance/exclusions.json`.
2. **Inline markup/template unwrapping (all held `needs_review`):**
   - `[[target]]` wikilink brackets stripped to visible link text.
   - `{{ng|...}}` wrapper unwrapped to its inner argument (preserving trailing `.` verbatim).
   - `{{q|written}}` (`8218` sense 3) and `{{lb|ta|catholicism}}` (`8218` sense 4): in `wiktionary-candidate-v1`, these prefixes were stripped and logged in `findings.csv`; in controlled `wiktionary-candidate-v2`, both prefixes are preserved literally in the candidate definitions (`(written) appeal; announcement`, `(catholicism) confession`), v1 → v2 assertion transitions are recorded in `changes.csv`, pending scope labels (`written`, `catholicism`) are recorded in `labels.csv` alongside `scope_proposal_*` assertions, and `scopes.csv` keeps both sense scopes `unknown` pending human review.

## 4. Preserved Disclaimers & Official Notice Snapshots

Checked-in official source documents alongside this notice:
- [cc_by_sa_4_0_legalcode.txt](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/cc_by_sa_4_0_legalcode.txt) — Full Creative Commons Attribution-ShareAlike 4.0 International Legal Code, including Section 5 (Disclaimer of Warranties and Limitation of Liability: material offered *as-is* and *as-available*, no warranties, no endorsement).
- [wikimedia_tou_api.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/wikimedia_tou_api.json) — Official Wikimedia Terms of Use revision (`revid=598588`, `2026-10-25T01:07:30Z`), including Section 7 (Licensing of Content) and Section 15 (Disclaimers).
- [wiktionary_copyrights_api.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/wiktionary_copyrights_api.json) — Official English Wiktionary `Wiktionary:Copyrights` revision (`revid=87545419`, `2025-10-22T20:09:50Z`).
- [fetch_manifest.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/fetch_manifest.json) — Retrieval metadata and SHA-256 digests for the copied official notice files.
