# Wiktionary Link-Template Boundary & Gap Snapshot Staging Audit

Date: 2026-11-16. Scope: characterization of rejected `m` / `l` link templates among the 333 pinned-snapshot absent spellings, boundary preservation in `tools/lexicon_wiktionary_bulk.py`, and `snapshot_date` workspace parameterization for staging the supplemental `2026-11-16` gap fetch.

## Summary

- **No `m`/`l` parser broadening performed**: All 34 `m`/`l` rejections among the 333 pinned-snapshot absent spellings (`19` `m`, `15` `l`) are Tamil-language invocations (`{{m|ta|...}}` and `{{l|ta|...}}`) containing Tamil script in English glosses. All 34 fail current policy (`en`-only `m`/`l` links + `TAMIL_IN_ENGLISH_GLOSS_REJECTED`) correctly.
- **Boundary locked by regression tests**: Added `test_ml_template_policy_boundary_with_pinned_gap_blockers` in `tests/harness/test_lexicon_wiktionary_bulk.py` covering pinned `ta` `m`/`l` blockers (`ரூபாய்`, `அஃகேனம்`, `தெப்பக்குளம்`), non-`en` / alias rejections (`mention`, `link`, `mul`, Tamil scalars), and existing safe `en` literal links.
- **Supplemental `2026-11-16` staging support**: Added validated optional `snapshot_date: str = BULK_SNAPSHOT_DATE` to `_build_pack_attribution_notice`, `_build_bulk_pack_workspace`, and `promote_bulk_packs` in `tools/lexicon_wiktionary_bulk.py`, propagating the local date to source identity (`enwiktionary_ta_bulk_YYYYMMDD_<pack_id>`), source metadata, `decision_date`, bulk `labels.csv` descriptions, and attribution notices while preserving byte-identical `2026-11-15` default output.
- **Isolation preserved**: No changes to `data/sources/`, `data/curation/`, `lexicon/`, Rust crates, bindings, or golden vectors.

## Characterization of the 410 Absent Wiktionary Spellings

Against the three usable canonical packs (`core`, `names_taxa`, `regional`), historical reconciliation identified **410** exact absent spellings in the Wiktionary-labelled slice:

| Baseline bucket (2026-11-15 snapshot) | Pages | Outcome |
|---|---:|---|
| Present in `data/sources/enwiktionary-tamil/pages.jsonl.gz` | 333 | All 333 rejected (0 clean entries) |
| Absent from `data/sources/enwiktionary-tamil/pages.jsonl.gz` | 77 | Queried via API on `2026-11-16` |
| **Total** | **410** | |

### Exact `m` / `l` Template Profile in the 333 Pinned Pages

Inspecting every `# ` sense line inside `==Tamil==` across all 333 blocked pages:

- `UNEXPANDED_TEMPLATE_REJECTED:m`: **19** sense-line rejections across **19** distinct pages (**27** `{{m|ta|...}}` template calls).
- `UNEXPANDED_TEMPLATE_REJECTED:l`: **15** sense-line rejections across **15** distinct pages (**44** `{{l|ta|...}}` template calls).
- Total `m`/`l` blocker pages: **34** distinct pages (no page hits both; all other sense lines on those 34 pages had no additional blockers).
- Language breakdown across all 71 `m`/`l` calls on sense lines of the 333 pages:
  - `('m', 'ta')`: **27**
  - `('l', 'ta')`: **44**
  - `en`, `mul`, `mention`, `link`, or other languages: **0**

Representative pinned cases from `data/sources/enwiktionary-tamil/pages.jsonl.gz`:
- `ரூபாய்` (`pageid=65857`, `revid=93508862`): `# The [[rupee]] (symbol: {{m|ta|௹}})` -> `UNEXPANDED_TEMPLATE_REJECTED:m`
- `அஃகேனம்` (`pageid=10046631`, `revid=92521670`): `# {{lb|ta|orthography}} {{ng|[[name]] of the [[letter]] {{l|ta|ஃ}}}}` -> `UNEXPANDED_TEMPLATE_REJECTED:l`
- `தெப்பக்குளம்` (`pageid=11419946`, `revid=89249734`): `# {{w|temple tank}} {{gl|tank attached to a temple in which the deity is floated on rafts during {{m|ta|தெப்பத்திருவிழா||float festival or {{w|theppotsavam}}}}}}` -> `UNEXPANDED_TEMPLATE_REJECTED:m`

Across the full 10,799-page `2026-11-15` snapshot, `# ` sense lines in `==Tamil==` contain:
- `('l', 'en')`: **14** calls, `('m', 'en')`: **4** calls (**16** already accepted by the existing `en` branch in `_expand_safe_templates`; **2** on lines rejected by other templates: `பஞ்சு` `pageid=8889217` due to `{{m|ta|...}}` and `நூறாயிசு` `pageid=9065307` due to `{{m+|en|...}}`).
- `('link', 'ta')`: **2** calls (`௳`, `௵`, outside mapped POS sections).
- `('l', 'mul')`: **2** calls.
- `('mention', *)`: **0** calls.

### Other Observed Blockers in the 333 Pinned Pages (Left Unchanged)

Top page-level sense blockers among the 333 pages: `place` (134 pages / 168 lines), `number to word` (29 / 29), `HTML_TAG_OR_COMMENT_REJECTED` (29 / 32), `altform` (22 / 23), `m` (19 / 19), `given name` (17 / 17), `l` (15 / 15).

Nested allowlisted links inside qualifiers/labels remain rejected in this slice:
- `NESTED_TEMPLATE_IN_QUALIFIER` (2 of the 333 pages: `காந்தள்` `pageid=11014377` with `{{w|Sangam literature}}`, `காட்டுப்பன்றி` `pageid=11381452` with `{{vern|Indian boar}}`; 8 total across the snapshot, 5 of which contain `{{m|ta|...}}`/`{{l|ta|...}}`).
- `NESTED_TEMPLATE_IN_LABEL` (3 of the 333 pages: `ஐயனார்` `9973117`, `பாவாடைராயன்` `10258733`, `காத்தவராயன்` `10258892` with `{{w|Religion in ancient Tamilakam|Tamil religion}}`; 15 total across the snapshot, including `மேல்` `pageid=7153529` where `{{w|Madurai Tamil|Madurai}}` inside `{{lb|ta|...}}` would alter regional pack routing).

## Supplemental `2026-11-16` Gap Snapshot Staging Support

The supplemental API fetch (`data/sources/enwiktionary-tamil-gap-2026-11-16/manifest.json`) queried the 77 absent spellings:
- `api_revision_pinned`: **51**
- `api_page_missing`: **26**

Under the unchanged strict parser (`target/lexicon/wiktionary-gaps/reconciliation.json`), **7** candidate entries / **9** senses parse cleanly (`ஆயிற்று` VERB [2], `உன்` PRON [1], `எனது` PRON [2], `தன்` PRON [1], `நம்` PRON [1], `நின்` PRON [1], `வேண்டாம்` VERB [1]; all `core`), while **377** remain `source_present_parser_blocked` and **26** remain `missing_from_snapshot`.

To allow isolated candidate-pack staging with accurate provenance for `2026-11-16` without affecting `2026-11-15` outputs:
- Added `_validate_snapshot_date(snapshot_date)` in `tools/lexicon_wiktionary_bulk.py` requiring strict ASCII `YYYY-MM-DD` format and a valid calendar date, failing closed with `ValueError` before touching `workspace_dir`.
- Added optional `snapshot_date: str = BULK_SNAPSHOT_DATE` to `_build_pack_attribution_notice`, `_build_bulk_pack_workspace`, and `promote_bulk_packs`.
- Replaced hardcoded `2026-11-15` / `20261115` references inside those functions with the validated local date across `source_id` (`allocate_id("src", pack_ns, f"enwiktionary_ta_bulk_{compact_date}_{pack_id}")`), `sources.csv` (`label_json`, `edition_json`, `locator_json.snapshot_date`, `retrieval_date_json`, `reuse_basis_json`, `attribution_text_json`), `decisions.csv` (`decision_date`), `labels.csv` (`definition_json` for scope labels and region hierarchy nodes), and `notices/ATTRIBUTION_AND_LICENSE.md`.

## Verification

- `uv run --locked pytest tests/harness/test_lexicon_wiktionary_bulk.py` (tests-first check failed with `TypeError` on the new `snapshot_date` test prior to implementation; after implementation, all focused tests pass).
- `just agent-post-edit` (formatting, Unicode/schema gate, release-copy check, workspace check).
