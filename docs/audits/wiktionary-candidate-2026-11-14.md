# Wiktionary Pending 4-Entry Candidate Audit (2026-11-14)

- **Scope & state**: Created a separate, fail-closed, **pending** 4-entry PRIMARY candidate dataset in [README.md](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/README.md) using checked-in pinned English Wiktionary API/wikitext snapshots. Historical `T038` remains **unverified** (`[ ]`), genuine human review (`T039`) and L3/L4 pack/runtime milestones (`T040`–`T070`) remain **pending** (`[ ]`), all 12 immutable intake files in [tamil-lexicon](C:/Users/abish/Documents/dev/tamil-toolkit/data/sources/tamil-lexicon) and the 739-record [tamil-lexicon curation workspace](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/tamil-lexicon) remain untouched, and `lexicon/dictionary/` remains empty/unchanged.

## 1. Pinned Revision Verification (Saved Checks + Fresh Official API)

Each entry was verified via `https://en.wiktionary.org/w/api.php?action=query&prop=revisions&revids=...&rvprop=ids|timestamp|user|comment|sha1|size|content&rvslots=main&format=json&formatversion=2` on `2026-11-14T08:01:15Z`–`20Z` UTC and confirmed identical (`pageid`, `title`, `revid`, `timestamp`, `sha1`, and raw UTF-8 wikitext) to `target/lexicon/wiktionary-recovery/candidate_api_checks/enwikt_rev_05..08.json`.

| Legacy `word_id` | Title | `pageid` | `revid` | `revision_timestamp` | API JSON Bytes / SHA-256 | Wikitext Bytes / SHA-256 |
|---|---|---:|---:|---|---|---|
| `1921` | அடடா | `11100687` | `85842017` | `2025-08-09T18:54:09Z` | `1400` / `cbb0090456c4bd19375cd8096e06ea5029ad397920dfb8fee07c62ffda923c2c` | `526` / `ffa17f0eaa27f7ccf3b6bb55f9e7da0532e7e7f634fa4b9afb993847c609d063` |
| `3906` | அந்நிலை | `7769127` | `89903937` | `2026-03-20T08:41:52Z` | `882` / `1ea97c546b67963a757179143807f25338318f54fb4c6a07202af2c03568f0af` | `431` / `527c5be08b52b9db426a1da8fb5b143e4faebb310be12375995a4d4392ecefa3` |
| `8218` | அறிக்கை | `9685129` | `88382210` | `2025-12-05T06:44:33Z` | `1241` / `4c0e2de40110d99d6bc40c36c45c4cec8db09ddc9bf44a016b35a41ca795249e` | `773` / `8bf77bf23d7c241f236575fcff535bc24d71d00287e288ab4d2238f857ccbed8` |
| `28857` | செப்பம் | `7902117` | `61485513` | `2021-01-04T16:15:52Z` | `1107` / `6934755c5194cd9fff0e1335bbecdedc9ef0873941e056b601d83fd19dd9c895` | `524` / `844ff53b3d33176f07d8a92189b3b08f23ce5cb259fbea9f27581d0e66f1846e` |

## 2. Projected Counts & Strict Pending Posture

- **Workspace counts ([verify_proof.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-candidate/verify_proof.json)):**
  - `entries.csv`: `4` (`language_id = tam`, `structural_kind = proposed_wiktionary_candidate`)
  - `forms.csv`: `4` (`written` `canonical`; `0` `ipa` forms)
  - `senses.csv`: `16` (`2` + `1` + `4` + `9`)
  - `texts.csv`: `16` (`2` `gloss` from `{{ng|...}}` + `14` `definition`, `language_id = eng`)
  - `assertions.csv`: `24` (`4` `headword` + `4` `part_of_speech` + `2` `gloss` + `14` `definition`)
  - `decisions.csv`: `24` (`4` `pending` for literal verified `headword`s, `20` `needs_review` for POS heading mapping and sense markup/template unwrapping, `0` `accepted_human`, `0` `accepted_auto_source`)
  - `findings.csv`: `49` open review items
  - `scopes.csv`: `24` (`unknown`, `label_code = null`)
  - `pack_members.csv`: `0`
- **Release guard (`tools.lexicon_pilot.release_guard`):** `eligible_assertions: 0`, `l2_structural_accepted: false`, `l3_pack_eligible: false`, `runtime_verified: null`, finding `NONEMPTY_ELIGIBLE_PACK_REQUIRED`.

## 3. Exclusions Summary

Because a page `oldid` pins raw wikitext only (not live transclusions or Lua modules), all template-generated/unpinned structures are excluded from lexical tables and itemized in [exclusions.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/exclusions.json):
- `{{ta-IPA}}` and `{{audio}}` across all 4 entries (preventing unpinned `Module:ta-IPA` drift such as `/ɛ/` vs `/e/` on `செப்பம்`)
- Etymologies (`{{ety}}`, `{{com}}`, `{{af}}`, `{{suf}}`, `{{m}}`) and unverified legacy/synthetic strings (`*aṯ-V-`, `*PDr-2747`, `DEDR 314`, `DEDR 2747`)
- Usage examples (`{{ux}}` on `1921`), synonyms (`{{syn}}` on `3906` and `8218`), declensions (`{{ta-decl}}` on `3906` and `8218`), derived terms (`{{col3}}` on `8218`), see-also (`{{l}}` on `28857`), references (`{{reflist}}`, `{{R:...}}`), and categories (`{{C}}`)
- Notice: `{{ng|...}}` (`1921` senses 1–2), `{{q|written}}` (`8218` sense 3), `{{lb|ta|catholicism}}` (`8218` sense 4), and `[[...]]` wikilinks (`[[event]]s` postfix inflection) were unwrapped only with explicit raw-line/arg provenance in [extraction_provenance.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/extraction_provenance.json), `source_fidelity_state = "changed"`, and `needs_review` decisions + open findings.

## 4. License Attribution Rationale & Preserved Disclaimers

Proposed route is `CC-BY-SA-4.0` backed by checked-in snapshots under [ATTRIBUTION_AND_LICENSE.md](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/ATTRIBUTION_AND_LICENSE.md): `Wiktionary:Copyrights` (`revid=87545419`), `Policy:Terms_of_Use` (`revid=598588`, §7 and §15 disclaimers), and `CC-BY-SA-4.0` legal code (§5 disclaimers). Data licensing is kept strictly separate from MIT extractor/tool code and Rust runtime crates (`crates/*`), and `sources.csv` retains `reuse_state = "restricted"` pending L3 ShareAlike pack clearance. **This record is engineering documentation only, not legal advice or a claim of total legal compliance.**

## 5. Concrete Review Gaps (Recorded Without Weakening Schemas)

Documented in [schema_gaps.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/schema_gaps.json):
1. `source_records` schema enforces `ordinal >= 2` (designed for 1-based CSV rows after line 1 header), so single-page `.wikitext` revisions use `ordinal = 2` while recording exact `1..N` physical line bounds.
2. `sources` lacks dedicated `pageid`, `revid`, `revision_timestamp`, `wikitext_sha256`, `permalink_url`, `history_url`, and dual-license (`GFDL`) columns; tracked via `edition_json`, `locator_json`, and `snapshots_manifest.json`.
3. `texts` / `assertions` lack dedicated byte/char range, template-name, and template-arg columns; tracked via `cited_source_locator_json`, `evidence.locator_json`, and `provenance/extraction_provenance.json`.
4. Qualifier/label templates (`{{q|written}}`, `{{lb|ta|catholicism}}`), multi-gloss lists, `{{ng|...}}` trailing periods, and `INTJ`/`NOUN` heading mappings remain unresolved human-review items (`T039`+).

## Rebuild protection and coordinator verification

The builder rejects output paths overlapping the frozen intake or main editorial workspace. Before writing any table, it compares all existing tables with the generated proposals and refuses conflicting editorial changes, preserving review decisions and corrections. Use a fresh workspace for a deliberately different projection.

Coordinator checks passed: 11 focused tests; schema/Unicode/source-pin verification; all 12 frozen source hashes; byte-identical offline replay across 25 generated files. Full repository gate results are recorded separately in the handoff once complete.

Final coordinator verification: post-edit passed; Clippy, Rust and all 288 harness tests passed. The combined pre-stop command stopped at binding setup because direct Python lacked `maturin` on PATH; its exit remains 1. The documented `uv run --locked python tools/tasks.py test-parity` completed the remaining checks with exit 0, rebuilding real Python/both WASM bindings and passing 36,161 Rust active vectors, 30 Python golden groups and 36,185 WASM tests. All pre-stop components passed across the saved runs; no clean single-run pre-stop exit is claimed. [checkpoint-root.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-candidate/checkpoint-root.json) records exact outcomes and log hashes. Candidate verification and 25-file replay passed again; all 12 original files and the main intake assertions hash remain unchanged. No dictionary runtime or release approval is implied.
