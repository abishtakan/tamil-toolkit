# Wiktionary Pending Homograph Candidate Dataset (`wiktionary-en-tamil-homograph-candidate`)

This directory is an **isolated, pending homograph companion candidate** workspace (`id_namespace = 4f8c3162-a2c9-5a18-9d25-6d8d2d37b110`, `text_codec = json-string-utf8-v1`). It is **not** part of the canonical runtime dictionary (`lexicon/dictionary/`), does **not** touch the 12 immutable intake files in [tamil-lexicon](C:/Users/abish/Documents/dev/tamil-toolkit/data/sources/tamil-lexicon), and does **not** modify `data/curation/tamil-lexicon/` or `data/curation/wiktionary-candidate/`.

All **2 entries** sharing the same written Tamil form `நன்றி` (`INTJ` + `NOUN`) and **3 senses** (`7` total assertions, `7` decisions: `2 pending`, `5 needs_review`, `0 accepted_human`, `0 accepted_auto_source`, `11` open review findings, `0` pack members) await genuine human curation review and license clearance (`l3_pack_eligible = false`, `eligible_assertions = 0`, `runtime_verified = null`).

## Pinned Official Revision

Copied byte-for-byte from the cached official `en.wiktionary.org` API check `target/lexicon/wiktionary-recovery/candidate_api_checks/enwikt_rev_10.json` (`12,430` bytes, retrieved `2026-11-14T07:44:20Z`).

| Legacy `word_id` | Headword (`tam`) | POS Source Headings | Senses | `pageid` | Pinned `oldid` | Revision Timestamp | Wikitext Bytes / SHA-256 |
|---|---|---|---:|---:|---:|---|---|
| `32793` (legacy collapsed as single `NOUN`) | நன்றி | `===Interjection===` (`INTJ`, 1 sense); `===Noun===` (`NOUN`, 2 senses) | `3` | `4593930` | `93647113` | `2026-10-17T21:53:52Z` | `2023` / `d0c85376de17daab66cdce055a36ca1d208dcd0135edfa44856ae31ea6dabbad` |

## Reproducible Offline Commands

```powershell
uv run --locked python -m tools.lexicon_wiktionary_candidate verify --dataset homograph
uv run --locked python -m tools.lexicon_wiktionary_candidate replay-check --dataset homograph
```
