# Wiktionary Core Candidate Review & Source-Closure Packet

- **Generated:** `2026-11-14`
- **Status:** **Pending Genuine Human Linguistic Review & CC-BY-SA-4.0 Data Policy Approval**
- **Editorial Safety State:** `accepted_human = 0`, `accepted_auto_source = 0`, `reuse_state = "restricted"`, `eligible_assertions = 0`, `l3_pack_eligible = false`, `runtime_verified = null`.
- **Machine-Readable Companion Packet:** [core_review_packet.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/core_review_packet.json)
- **Attribution & Disclaimers (Not Legal Advice):**
  - 4-entry candidate notices: [ATTRIBUTION_AND_LICENSE.md](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/ATTRIBUTION_AND_LICENSE.md)
  - Homograph companion notices: [ATTRIBUTION_AND_LICENSE.md](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-homograph-candidate/notices/ATTRIBUTION_AND_LICENSE.md)

---

## 1. Source Closure Route & Policy Decisions Required

Historical archived `kaikki_tamil.jsonl` checksum/URL provenance recovery (`T038` historical route) remains **blocked** (historical archive absent/unverified). Fresh independent source closure uses **strictly pinned official English Wiktionary MediaWiki API revisions** (`pageid` + `oldid` + UTF-8 `.wikitext` SHA-256/SHA-1) across two isolated pending workspaces:

1. `data/curation/wiktionary-candidate` (`wiktionary-en-tamil-candidate`, `v2`): **4 single-POS pages / 4 entries / 16 senses**.
2. `data/curation/wiktionary-homograph-candidate` (`wiktionary-en-tamil-homograph-candidate`, `v1`): **1 single-page multi-POS homograph (`நன்றி`) / 2 entries (`INTJ` + `NOUN`) / 3 senses**.

### Official Policy & License Reference Pins

| Document | Canonical URL | Pinned Revision | Local Snapshot SHA-256 |
|---|---|---|---|
| Wikimedia Foundation Terms of Use (§7, §15) | `https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use` | `revid=598588` (`2026-10-25T01:07:30Z`) | `c3e0bff8b859941468d6895dff392d893bd13cfae2ea0ae8565db74aaaab1123` |
| English Wiktionary Copyrights Policy | `https://en.wiktionary.org/wiki/Wiktionary:Copyrights` | `revid=87545419` (`2025-10-22T20:09:50Z`) | `049a09491de163dc85b77e6f260705bb5e59052c27b4e0f75ea49dd5d3e4fe4c` |
| CC BY-SA 4.0 International Legal Code | `https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt` | CC BY-SA 4.0 | `28a9529c7d0bb4dc51f4bf5c116a3d16ef247a052f7591466768ddf563fd1cf5` |

### Proposed CC-BY-SA-4.0 Data Packaging vs. MIT Engine Separation (Needs Approval)

- **Proposed Data License:** `CC-BY-SA-4.0` (with upstream `GFDL` notice where applicable and Wikimedia ToU §7 per-revision contributor/history attribution) applies **only** to Wiktionary-derived lexical data and CC-licensed core packs.
- **Code / Engine Separation:** Rust core crates (`crates/*`), CLI/tooling, and non-Wiktionary repository code remain `MIT`; `CC-BY-SA-4.0` does **not** relicense the Rust runtime engine, and `MIT` does **not** overwrite Wiktionary text.
- **Policy Approval Needed:** Approve promoting `sources.csv` `reuse_state` from `"restricted"` to `"permitted"` under separate CC-BY-SA-4.0 data-pack packaging and preserved per-entry attribution notices (or reject Wiktionary candidate inclusion).

---

## 2. Candidate Summary (5 Pinned Pages -> 6 Distinct Entries, 19 Senses)

All written Tamil headwords pass Rust `native_inspect` (`is_nfc = true`).

| Dataset / Legacy ID | Headword & Codepoints (NFC) | POS (`raw heading` -> `mapped`) | `pageid` / `oldid` (User, Timestamp UTC) | Entry ID & Revision SHA-256 | Links |
|---|---|---|---|---|---|
| `candidate` / `1921` | **அடடா** `U+0B85 U+0B9F U+0B9F U+0BBE` | `INTJ` (`===Interjection===`) | `11100687` / `85842017` (`Pixelpito`, `2025-08-09T18:54:09Z`) | `ent_9469d6ba-b9ac-563d-9a16-c5d77397f148` · `ast_caa07ff5-ba46-5d6a-aff9-8fc611d64212` (`a8099b8f542c833eb975255b1bf31f02f0e79d465acd403c962a28d3ae31fdf6`) | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%9F%E0%AE%9F%E0%AE%BE&oldid=85842017) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%9F%E0%AE%9F%E0%AE%BE&action=history) |
| `candidate` / `3906` | **அந்நிலை** `U+0B85 U+0BA8 U+0BCD U+0BA8 U+0BBF U+0BB2 U+0BC8` | `NOUN` (`===Noun===`) | `7769127` / `89903937` (`Pixelpito`, `2026-03-20T08:41:52Z`) | `ent_9cbc0af9-5299-543f-8e6f-288b9e4d6424` · `ast_1c2d7143-f154-5703-8291-76b4727f5948` (`27393d8a7f2fee6e33bf5a7e351bf3e68269d7f47563a910aed15b96e1f992af`) | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%A8%E0%AF%8D%E0%AE%A8%E0%AE%BF%E0%AE%B2%E0%AF%88&oldid=89903937) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%A8%E0%AF%8D%E0%AE%A8%E0%AE%BF%E0%AE%B2%E0%AF%88&action=history) |
| `candidate` / `8218` | **அறிக்கை** `U+0B85 U+0BB1 U+0BBF U+0B95 U+0BCD U+0B95 U+0BC8` | `NOUN` (`===Noun===`) | `9685129` / `88382210` (`~2025-38205-63`, `2025-12-05T06:44:33Z`) | `ent_5e50b59e-3d35-52af-a248-fd4a0de475de` · `ast_a4597b3d-2c6c-54b6-86bb-c19e33f5b21c` (`ad8bee45176ac95aef6b139001f3a5a081572179173f7c960dc2866173dce3ea`) | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%88&oldid=88382210) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%85%E0%AE%B1%E0%AE%BF%E0%AE%95%E0%AF%8D%E0%AE%95%E0%AF%88&action=history) |
| `candidate` / `28857` | **செப்பம்** `U+0B9A U+0BC6 U+0BAA U+0BCD U+0BAA U+0BAE U+0BCD` | `NOUN` (`===Noun===`) | `7902117` / `61485513` (`Hk5183`, `2021-01-04T16:15:52Z`) | `ent_b52ae202-3f3a-5538-9db1-51b82d92d78f` · `ast_3f1023c6-13dc-51c6-a097-0f006af44d92` (`53506f718ab0574268f2316e1720f43314f3776105a1b1d901689d1b18f1209a`) | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%9A%E0%AF%86%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AE%AE%E0%AF%8D&oldid=61485513) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%9A%E0%AF%86%E0%AE%AA%E0%AF%8D%E0%AE%AA%E0%AE%AE%E0%AF%8D&action=history) |
| `homograph` / `32793` (#1) | **நன்றி** `U+0BA8 U+0BA9 U+0BCD U+0BB1 U+0BBF` | `INTJ` (`===Interjection===`) | `4593930` / `93647113` (`FenaBot`, `2026-10-17T21:53:52Z`) | `ent_f063763c-36ac-55c6-b288-8da7f9ab6fff` · `ast_dfcda0e1-9e2f-5f9a-8995-503bda38f738` (`963ab871a1dc5796910c6501d7474b755362330c4edd7e3754f20f3fa8f0575e`) | [Permalink](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%A9%E0%AF%8D%E0%AE%B1%E0%AE%BF&oldid=93647113) · [History](https://en.wiktionary.org/w/index.php?title=%E0%AE%A8%E0%AE%A9%E0%AF%8D%E0%AE%B1%E0%AE%BF&action=history) |
| `homograph` / `32793` (#2) | **நன்றி** `U+0BA8 U+0BA9 U+0BCD U+0BB1 U+0BBF` | `NOUN` (`===Noun===`) | `4593930` / `93647113` (`FenaBot`, `2026-10-17T21:53:52Z`) | `ent_a08297c3-424d-5a37-aaf0-4135d7476669` · `ast_1b690444-c35d-5759-b14e-60e8ac20f536` (`275c821c854855bab9272dca85ec2f30eee8c39322777b7809189c4db5f1b630`) | Same official page (`INTJ` + `NOUN` sections) |

### POS Assertion & Evidence Hashes (Pending Review)

- `1921` (`INTJ`): `ast_dee6f3c3-1cac-57ca-bea3-864de1b45bdf` · `claim_revision_sha256 = 3db5107085113f9d4ac9efaff95e80850ec72ce6a024dcf8f86cd336cb966de6` · `evidence_bundle_sha256 = fa115ca56f8c8c317f29b494de70342e7948fd1d9f40ce9e23e3198f5d2ea699`
- `3906` (`NOUN`): `ast_429209cd-e65f-5689-b396-92150a3781cd` · `claim_revision_sha256 = e8927e292f1abbe9eaf46d01f855485bd9b4bef6b8bed04989c686f04efb7724` · `evidence_bundle_sha256 = 52503d419f94f7dd79bf484070ceb24e5c414de38cc9ca78632d66b59263c7b5`
- `8218` (`NOUN`): `ast_ab7bb9c7-d672-5347-a7b9-e578cf07e411` · `claim_revision_sha256 = 54368e9db8b695ae238ce491e94074b2bc8d5dba3b6851c64cd6b65c127a5908` · `evidence_bundle_sha256 = 342f9e36c41b61f0f4bf058ccc46d99e508eac86909dc59a0c9f63420ea765bf`
- `28857` (`NOUN`): `ast_a3813180-4ffb-5826-860f-076b0897c4cb` · `claim_revision_sha256 = ad736a027d0a2883ab29a95d0e9c5dba53ac4386874b7f9eb29c55dc939f89ff` · `evidence_bundle_sha256 = b43ca89ca9aee02ec2d8d6e9e1a3bf5f79a456d887a405084ecd9dc369b57ac5`
- `32793` (#1 `INTJ`): `ast_98d03e35-bb49-5699-8cea-7a915788fff4` · `claim_revision_sha256 = 9e154b947d670f2dff68cbbaead2f5204853875dda914dec44ec6379f4c0f835` · `evidence_bundle_sha256 = be448647968f7b99668c2818b0f25bdd53a9585e94b4b692eae10e12f676eaf4`
- `32793` (#2 `NOUN`): `ast_873332a2-3011-58bd-a2d8-a89708190dbd` · `claim_revision_sha256 = 8dca4bc7f8d9f6675dca30f90e25676f4a0d650ba4a3b701573eb7a98e5ea32c` · `evidence_bundle_sha256 = 1eb82eaca26d2e734f1be86e5bea32376378f5fee34ecdf85dac29a3c80e2651`

---

## 3. Ordered Senses, Preserved Qualifiers, and Assertion Hashes

### A. `wiktionary-candidate` (4 entries, 16 senses)

#### 1) அடடா (`1921`, `INTJ`, `oldid=85842017`)
1. `[gloss]` **`an exclamation of surprise.`** (`raw: # {{ng|an exclamation of [[surprise]].}}`)
   - `sen_ea2a4fec-432f-5169-b87b-6da425f40134` · `ast_4ffcad28-9a6c-56eb-9a84-29dec5a2d12d` · `rev: bf803fcce449ca925c8f3632be4089f6d7ed2e192429d7e7c93430edd57856a7` · `ev: 059dc16a55cc55654840cea67cb929a7f23df93dd12e97275c0e6d1be1fe9576`
2. `[gloss]` **`an exclamation of vexation, grief, pity, regret.`** (`raw: # {{ng|an exclamation of [[vexation]], [[grief]], [[pity]], [[regret]].}}`)
   - `sen_75717b2b-97de-58b6-aace-0d92381376ca` · `ast_c8563f42-c884-54b5-b4ee-630373da5e53` · `rev: 8d457238f7e12a8aa9d014cb715bae401f3fd2952a23c95c6250f042aa2a9b54` · `ev: 45c22f6103d09633e84fa37f7237b0740320cb6625180e00bddc20f492b7e34b`

#### 2) அந்நிலை (`3906`, `NOUN`, `oldid=89903937`)
1. `[definition]` **`that moment`** (`raw: # [[that]] [[moment]]`)
   - `sen_b074cf21-c6a1-5fff-8bdd-539375007d04` · `ast_fa1a7419-7fd2-5166-80f4-d0c6225e3a1f` · `rev: 36afa48898b7b6e9d33e279e325f2e1fc78fc41d8327afd75716e20421f0f0b3` · `ev: 66f96189e1261873965924567cf740cfc7cd00a8907270755c6c3a0fb172a635`

#### 3) அறிக்கை (`8218`, `NOUN`, `oldid=88382210`) — Includes `v1 -> v2` Qualifier Correction
1. `[definition]` **`notice`** (`raw: # [[notice]]`)
   - `sen_d2b06f5a-95d4-5c51-b375-44a18136c2ec` · `ast_8303bcab-041b-5645-9bb9-b5f56efc01ff` · `rev: 519fb28b5ea463f30c1c261ab92848af83ca0300c0ab63a6e102c1c4009a0a8e` · `ev: 3767979199e82b53d3baac4302b12ad966de609036024d338d4c7ac7bc721429`
2. `[definition]` **`report; an account of events`** (`raw: # [[report]]; an [[account]] of [[event]]s`)
   - `sen_13f405ce-a43b-56ac-9b2f-7e0d476cce5b` · `ast_e60b0ffd-22d4-5e10-9cc8-93a04537c986` · `rev: 46905ab888ab1e555e0e80a86a64c37a163459b502049ab5074000a71d2bc35b` · `ev: ae3ac8c7649c90a6239c7b5010a6b82385a4c22b3769609eb68194a3ca267429`
3. `[definition]` **`(written) appeal; announcement`** (`raw: # {{q|written}} [[appeal]]; [[announcement]]`)
   - `sen_64d6c824-9c3d-52bf-abae-78e9c5d9ff3c` · `txt_61630435-ebc8-5d61-b2e6-c3dcb745bab2` · `ast_560c194e-bc99-56ff-915e-e9f9f7c6cf8e` · `rev: 8dbbc0ce3ff37072fb93d0bb9a60eaf46b0f69979adeafd4959af1b72fa2c477` · `ev: d2a6bdc350157b5ba51ffc28f89382a3c1d98f8eb416cd21efe73565c77ec915`
   - **v1 -> v2 Change:** `chg_f99d3bf6-f207-5d0b-b6fb-a9d0700b1c77` supersedes `ast_fe25618c-674e-58cf-9cda-ac8e65aa0ef7` (`"appeal; announcement"`, `rev: 612350ab4d318468fe1975a18115ce251a5ec690c07520e291d2d66c8aaccad5`).
   - **Pending Label/Scope Proposal:** `labels.csv` code `written` (`category="register"`), `scope_proposal_register` assertion `ast_a10c862d-d53d-5613-87cd-1d6bef2e4176`, `scopes.csv` `state="unknown"` until human approval.
4. `[definition]` **`(catholicism) confession`** (`raw: # {{lb|ta|catholicism}} [[confession]]`)
   - `sen_28f47fad-a25a-5f7b-8a52-d80aecf26084` · `txt_42a3e955-b4e7-51bc-a533-d34db434abc3` · `ast_1227cd3b-3c12-5a85-baeb-d5bd14bf9d99` · `rev: d9afdd576d555a8b773b663ceb61947d38b243701b9750944d540bd50e1ef41a` · `ev: dc29472dde69f8c4a3298f90331921ca2938d6209d41bcc1d1e9e47ff8814cea`
   - **v1 -> v2 Change:** `chg_29b06b08-8151-562a-938e-cd4b1cbd721a` supersedes `ast_90a3b38c-927b-5ec0-a9d7-1eb9963062b4` (`"confession"`, `rev: 471b5bd7ac6f8e18112f3810ba0558a1749624b5183ccc1dfb9e2ebb131d33f3`).
   - **Pending Label/Scope Proposal:** `labels.csv` code `catholicism` (`category="domain"`), `scope_proposal_domain` assertion `ast_7bc6ae93-e652-5508-a6cb-451ae6fd370c`, `scopes.csv` `state="unknown"` until human approval.

#### 4) செப்பம் (`28857`, `NOUN`, `oldid=61485513`)
1. `straightness, correctness, exactness, smoothness, uprightness` (`ast_71b11ddc-01b3-5061-acc4-010229d79957`, `rev: 48437ecb8d581bcd8d1512983155f1062415a8923b3f0737027c4c4a9f88102e`)
2. `impartiality, evenness, equity` (`ast_37c5bf98-9ff2-5625-9cf7-9874c28e6bf7`, `rev: 89328b4c2fe2235a86b7abf17bb1c1fee121c94c5ad2957517c2ccf62f5c0827`)
3. `repair, renewal` (`ast_f237dcfb-321b-5b66-b14b-d0b724b181af`, `rev: 7ef2ac58b65fd263a651850b734175f368cd49227585470cb12a313104cd0af4`)
4. `preparedness, fitness` (`ast_ebd55d0f-87c3-52d4-b600-051338074731`, `rev: 611a637194b618e1222e8663b435e8c08fd0303113ac420b05111c678e52afbd`)
5. `protection` (`ast_af54d74b-feb7-513e-9837-81c463971633`, `rev: c1e7628fdbb72c08e6f398b3298651fafa0967f68a1b2a063f6f97c1c8c3bf49`)
6. `straight path` (`ast_59b994c7-7085-5d90-9c71-42d97ced2027`, `rev: 53f0fa2109db6772f7ac25db69f00cc4ba35e4601e852a65db21e40d51513e3c`)
7. `street` (`ast_67afd4dc-4bb0-517c-b07b-4514e0c5d86b`, `rev: e54660a865acc8b173e506f6b0afe5e7592e2e025cd0fcaae5357c560472d15f`)
8. `heart` (`ast_ac725863-bb6c-50d9-8a9f-2967112affa2`, `rev: c17de83cf1331bae32908f5ba74b9e0db7d74a3d903b8cd3953f4c52c2bbfb4b`)
9. `satisfaction, agreeableness` (`ast_b8ea41ef-e9ba-5127-ad92-e6a0d8f69e50`, `rev: 87f7888d687dbc56cc98c54306f45f14721862fd010d907c3bfdd281427fe39c`)

*(All evidence bundle SHA-256s for `செப்பம்` senses 1–9 are recorded in `core_review_packet.json`.)*

### B. `wiktionary-homograph-candidate` (1 page: `நன்றி`, `pageid=4593930`, `oldid=93647113` -> 2 entries, 3 senses)

Source `==Tamil==` splits into `===Interjection===` (line 15) and `===Noun===` (line 20) — unlike the unverified legacy CSV (`word_id=32793`) which collapsed all three senses under a single `NOUN` entry.

1. **Entry #1 (`INTJ`):** `ent_f063763c-36ac-55c6-b288-8da7f9ab6fff`
   - Sense 1 `[definition]`: **`thanks, thank you`** (`raw: # [[thanks]], [[thank you]]`)
     - `sen_4ccafa9b-eb17-53a8-a571-69e0a63dc992` · `ast_b6b9fee7-db6e-5b54-aa33-b7270003280c` · `rev: 394ff9886619b557fa68662a50129db76b0e83c6e69ef82d46ae18b58367a356` · `ev: 1ebfa592527215c294cbb338e36045370d56aac26f4219148ed8e21487a22975`
2. **Entry #2 (`NOUN`):** `ent_a08297c3-424d-5a37-aaf0-4135d7476669`
   - Sense 1 `[definition]`: **`help, kindness, benefit, favour`** (`raw: # [[help]], [[kindness]], [[benefit]], [[favour]]`)
     - `sen_0b8e7d9e-d369-5dd8-a905-47ed39c673c6` · `ast_8ae52e6f-c478-5c99-8d9d-8eaa27408fc4` · `rev: 0e2eb18f2315f593910a848deb0d02f78f845f748546111253ef54d063d12f96` · `ev: c1da772548c7218beb35bcdb0c30350fda48063f2b5b14822dd3ced99e5813d7`
   - Sense 2 `[definition]`: **`gratitude, gratefulness`** (`raw: # [[gratitude]], [[gratefulness]]`)
     - `sen_bf8afb40-f31a-5e1e-bd37-7c515bbfbfb7` · `ast_ab0270e5-52a1-5d4f-8c57-907b80324f6f` · `rev: c4306dc396a94f94f481fddb33fd68f008e5ec97f9724988d1c3eef453a0f946` · `ev: b25b1befdf95e7c779c8bce2f712a77f007c588bdfa676ba85812fae56af4579`

---

## 4. Explicit Exclusions, Remaining Gaps, and Sensible First-Pass Subset

- **Excluded Across All Pinned Pages:** `{{ta-IPA}}` / `Module:ta-IPA`, `{{audio}}`, etymology sections and unverified/synthetic legacy strings (`*aṯ-V-`, `*PDr-2747`, `*nal`, `DEDR 314`, `DEDR 2747`), `{{ux}}`, `{{syn}}`, `{{quote-book}}`, `{{ta-decl}}`, `{{col}}`/`{{col3}}`, `{{C}}`/`{{cln}}`, `{{phrasebook}}`, `{{reflist}}`, and `{{R:...}}`.
- **Sensible Minimal Subset Option:** If reviewing all 9 senses of `செப்பம்` (`28857`) at once is too broad for initial `core` L2/L3 pipeline closure, approve `1921` (2 senses), `3906` (1 sense), `8218` (4 senses with `written` / `catholicism` scope choices), `28857` (sense 1 or full 9), and `32793` (`நன்றி` `INTJ` + `NOUN`, 3 senses) cleanly via explicit per-claim decisions.
- **Required User Inputs Before Any L2/L3 State Mutation:**
  1. Reviewer `actor_id` (matching `^[A-Za-z][A-Za-z0-9_.:-]*$`) + `decision_date` (`YYYY-MM-DD`).
  2. Explicit CC-BY-SA-4.0 separate data-pack policy decision (`reuse_state`: `"permitted"` vs remain `"restricted"`).
  3. Per-entry/per-claim approval/rejection/revision for headwords, POS mappings, English sense texts, `அறிக்கை` senses 3–4 literal prefix vs structured `attested` scope (`written`, `catholicism`), and `நன்றி` `INTJ` + `NOUN` homograph split.
