# Wiktionary Pending 4-Entry Candidate Dataset (`wiktionary-en-tamil-candidate`)

This directory is an **isolated, pending curation candidate** workspace (`id_namespace = 7a5a7f6c-7f1e-5b2e-94c8-2f4b8e6b4f01`, `text_codec = json-string-utf8-v1`). It is **not** part of the canonical runtime dictionary (`lexicon/dictionary/`), does **not** touch the 12 immutable intake files in [tamil-lexicon](C:/Users/abish/Documents/dev/tamil-toolkit/data/sources/tamil-lexicon), and does **not** alter the existing 739-record [tamil-lexicon curation workspace](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/tamil-lexicon).

All **4 entries** and **16 senses** (`wiktionary-candidate-v2`: `28` total assertions, `30` decisions — `4 pending`, `24 needs_review`, `2 rejected` superseded v1 qualifier-stripped assertions with `2` `changes.csv` transitions, `2` pending `labels.csv` rows, `26` `unknown` scope markers, `51` open review findings; `0 accepted_human`, `0 accepted_auto_source`) await genuine human curation review and license clearance (`l3_pack_eligible = false`, `eligible_assertions = 0`, `runtime_verified = null`). Note on `8218` (அறிக்கை): senses 3 & 4 now preserve `(written)` and `(catholicism)` literally alongside pending scope proposals and exact v1→v2 revision history in `changes.csv`.

## Pinned Official Revisions

Fetched directly from `https://en.wiktionary.org/w/api.php` on `2026-11-14` (`08:01:15Z`–`08:01:20Z` UTC) and cross-verified byte-for-byte against `target/lexicon/wiktionary-recovery/candidate_api_checks/enwikt_rev_05..08.json`.

| Legacy `word_id` | Headword (`tam`) | POS Source Heading | Senses | `pageid` | Pinned `oldid` | Revision Timestamp | Wikitext Bytes / SHA-256 |
|---|---|---|---|---:|---:|---|---|
| `1921` | அடடா | `===Interjection===` (`INTJ`) | `2` | `11100687` | `85842017` | `2025-08-09T18:54:09Z` | `526` / `ffa17f0eaa27f7ccf3b6bb55f9e7da0532e7e7f634fa4b9afb993847c609d063` |
| `3906` | அந்நிலை | `===Noun===` (`NOUN`) | `1` | `7769127` | `89903937` | `2026-03-20T08:41:52Z` | `431` / `527c5be08b52b9db426a1da8fb5b143e4faebb310be12375995a4d4392ecefa3` |
| `8218` | அறிக்கை | `===Noun===` (`NOUN`) | `4` | `9685129` | `88382210` | `2025-12-05T06:44:33Z` | `773` / `8bf77bf23d7c241f236575fcff535bc24d71d00287e288ab4d2238f857ccbed8` |
| `28857` | செப்பம் | `===Noun===` (`NOUN`) | `9` | `7902117` | `61485513` | `2021-01-04T16:15:52Z` | `524` / `844ff53b3d33176f07d8a92189b3b08f23ce5cb259fbea9f27581d0e66f1846e` |

Full snapshot metadata and checked-in API/wikitext payloads live under [snapshots_manifest.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/snapshots/snapshots_manifest.json).

## Exclusions and Pending Review Items

Because pinning a MediaWiki page `oldid` pins only raw wikitext (not transcluded templates or Lua modules such as `Module:ta-IPA`), the allowlist builder excludes:
- All `{{ta-IPA}}` and `{{audio}}` pronunciation lines (`0` IPA forms generated)
- All etymology sections and templates (`{{ety}}`, `{{com}}`, `{{af}}`, `{{suf}}`, `{{m}}`) and unverified legacy/synthetic strings (`*aṯ-V-`, `*PDr-2747`, `DEDR 314`, `DEDR 2747`)
- All usage examples (`{{ux}}`), synonyms (`{{syn}}`), declension tables (`{{ta-decl}}`), derived terms (`{{col3}}`), see-also links (`{{l}}`), references (`{{reflist}}`, `{{R:...}}`), and category templates (`{{C}}`)

Itemized raw source spans, unwrapped templates (`{{ng}}`, `{{q|written}}`, `{{lb|ta|catholicism}}`, wikilinks `[[...]]`), and excluded lines are recorded in [extraction_provenance.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/extraction_provenance.json) and [exclusions.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/exclusions.json). Recorded schema representation gaps (recorded without altering global contracts) are in [schema_gaps.json](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/provenance/schema_gaps.json).

## License Route and Notices

See [ATTRIBUTION_AND_LICENSE.md](C:/Users/abish/Documents/dev/tamil-toolkit/data/curation/wiktionary-candidate/notices/ATTRIBUTION_AND_LICENSE.md). Proposed route is `CC-BY-SA-4.0` (data only, preserving Wikimedia disclaimers and per-revision contributor/history links; dual-licensed upstream with `GFDL` where applicable; `MIT` tooling license does not apply to Wiktionary text, and `CC-BY-SA-4.0` does not relicense Rust engine crates). All rows in `sources.csv` keep `reuse_state = "restricted"` pending L3 human/policy review. This is provenance documentation, not legal advice or a compliance guarantee.

## Reproducible Offline Commands

All build, verify, and replay checks read strictly from checked-in files under `snapshots/` without network access:

```powershell
uv run --locked python -m tools.lexicon_wiktionary_candidate build
uv run --locked python -m tools.lexicon_wiktionary_candidate verify
uv run --locked python -m tools.lexicon_wiktionary_candidate replay-check
uv run --locked python -m pytest tests/harness/test_wiktionary_candidate.py -v
```

## Rebuild protection and coordinator verification

The builder rejects output paths overlapping the frozen intake or main editorial workspace. Before writing any table, it compares all existing tables with the generated proposals and refuses conflicting editorial changes, preserving review decisions and corrections. Use a fresh workspace for a deliberately different projection.

Coordinator checks passed: 11 focused tests; schema/Unicode/source-pin verification; all 12 frozen source hashes; byte-identical offline replay across 25 generated files. Full repository gate results are recorded separately in the handoff once complete.

Final coordinator verification: post-edit passed; Clippy, Rust and all 288 harness tests passed. The combined pre-stop command stopped at binding setup because direct Python lacked `maturin` on PATH; its exit remains 1. The documented `uv run --locked python tools/tasks.py test-parity` completed the remaining checks with exit 0, rebuilding real Python/both WASM bindings and passing 36,161 Rust active vectors, 30 Python golden groups and 36,185 WASM tests. All pre-stop components passed across the saved runs; no clean single-run pre-stop exit is claimed. [checkpoint-root.json](C:/Users/abish/Documents/dev/tamil-toolkit/target/lexicon/wiktionary-candidate/checkpoint-root.json) records exact outcomes and log hashes. Candidate verification and 25-file replay passed again; all 12 original files and the main intake assertions hash remain unchanged. No dictionary runtime or release approval is implied.
