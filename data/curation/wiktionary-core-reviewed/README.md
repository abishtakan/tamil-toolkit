# Reviewed Wiktionary Core Workspace (`wiktionary-core-reviewed`)

Deterministic human-reviewed editorial closure built strictly from:
- `data/curation/wiktionary-candidate/` (4 pages / 4 entries / 16 senses, untouched pending workspace)
- `data/curation/wiktionary-homograph-candidate/` (1 page / 2 entries / 3 senses, untouched pending workspace)
- `docs/reviews/wiktionary-core-approval-2026-11-14.json` (immutable human approval receipt by `abish` on `2026-11-14`)

## Verified Closure Summary

- **Dataset ID:** `wiktionary-core-reviewed`
- **Pack ID / Policy:** `core` (separate `CC-BY-SA-4.0` data pack; MIT code/engine unchanged; `registry_publication_authorized = false`)
- **Entries / Senses:** `6` entries (`6` `pack_members.csv` rows with `relation_inclusion_policy = "omit_cross_pack"`), `19` senses, `0` IPA forms
- **Assertions & Decisions:** `35` total assertions:
  - `31` receipt-approved core claims (`6` headword + `6` POS + `19` definition/gloss): `accepted_human` (`actor_type = "human"`, `actor_id = "abish"`, `decision_date = "2026-11-14"`, linear `predecessor_decision_id`), `eligible = True`
  - `2` superseded `v1` qualifier-stripped assertions (`ast_fe25618c-674e-58cf-9cda-ac8e65aa0ef7`, `ast_90a3b38c-927b-5ec0-a9d7-1eb9963062b4`): remain `rejected`, `eligible = False`
  - `2` structured scope proposals (`ast_a10c862d-d53d-5613-87cd-1d6bef2e4176` register `written`, `ast_7bc6ae93-e652-5508-a6cb-451ae6fd370c` domain `catholicism`): remain `needs_review` with open `SCOPE_QUALIFIER_REQUIRES_REVIEW` findings and `scopes.csv` `state = "unknown"`, `eligible = False`
- **Source & Notice Closure:** `sources.csv` `reuse_state = "permitted"` verified against pinned Wikimedia ToU (`revid=598588`), English Wiktionary `Wiktionary:Copyrights` (`revid=87545419`), and `cc_by_sa_4_0_legalcode.txt` (historical Kaikki remains unverified and excluded)
- **Canonical Pack Release Guard:** `eligible_assertions = 31`, `included_entries = 6`, `l3_pack_eligible = true`, `findings = []`

## Reproduction & Verification Commands

```powershell
uv run --locked python -m tools.lexicon_wiktionary_candidate verify --dataset reviewed
uv run --locked python -m tools.lexicon_wiktionary_candidate replay-check --dataset reviewed
uv run --locked python -m pytest tests/harness/test_wiktionary_candidate.py -v
```
