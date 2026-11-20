# Lexicon text storage decision

**Date**: 2026-11-14  
**Decision**: User-directed revision during Feature 021 implementation.  
**Implementation status**: Clean `json-string-utf8-v1` intake, exact source-content
equality proof, pre-projection clean inventory/stage replay, 739-record
structural pilot acceptance (L2), fail-closed release-rejection guard, and full
`just agent-pre-stop-gate` are complete. Uncommitted legacy staging and temporary
copies were deleted with no legacy archive retained. L3 source/reuse/human
review and L4 compact runtime artifacts remain pending.

## Policy

- Large editorial and approved lexicon CSV tables store ordinary Tamil and other
  visible text as UTF-8, without a BOM and with LF record endings. They do not
  expand every non-ASCII scalar into a hexadecimal escape.
- Golden JSONL, exact scalar diagnostics, and small declarative rule tables keep
  explicit escapes where required for codepoint review. Human-facing review
  views may show Tamil alongside those diagnostics.
- Released lookup artifacts use the compact deterministic representation chosen
  and measured by the Rust compiler. CSV source encoding does not prescribe the
  runtime format, and no runtime pack is approved by this decision.
- No serialization step normalizes, repairs, folds, strips controls, or changes
  Unicode scalar sequences. Authoritative linguistic checks remain in Rust.

## CSV cell contract

The new codec identifier is `json-string-utf8-v1`. Free-text CSV cells contain
one JSON string literal; typed `*_json` fields retain their declared JSON types.
CSV quoting surrounds JSON encoding. Decode CSV and then JSON exactly once.
Visible Tamil stays literal UTF-8. JSON-required escapes preserve quotes,
backslashes, C0 controls and line breaks. Audit-sensitive format scalars,
including ZWJ/ZWNJ, FEFF, soft hyphen, C1 controls and Unicode line separators,
use explicit escapes in generated cells. These escapes preserve their characters;
they never authorize removal. Scalar diagnostics enumerate exact positions.

Known empty strings, unknown JSON null, and not-applicable values remain distinct.
Lone surrogates and invalid JSON remain errors. A source spelling that resembles
an escape is literal source text and must never be decoded a second time.

`json-string-utf8-v1` is the only supported dataset codec for this unreleased
feature. At the user's explicit direction, the earlier uncommitted ASCII-escaped
staging, its temporary copies and incomplete migration archive were deleted.
There is no released dataset to migrate and no legacy archive to retain. Dataset
metadata now declares the new codec. Canonical claim hashing remains separate
from storage and may use deterministic ASCII JSON.

## Rationale and measured baseline

Tamil is already Unicode. U+0BA4 occupies three UTF-8 bytes; its six-character
JSON escape occupies six bytes. Expanding ordinary text adds size and obscures
reading without providing additional identity or source evidence. Exact scalar
inspection and visible control diagnostics provide the needed auditing separately.

The initial staged CSV tables occupy **581,570,653 bytes**, before completing
the representative projection. This includes duplicated unparsed row payloads;
escaping is only one contributor. Do not attribute the entire difference from
the frozen source bundle to escapes. Before/after measurements must compare
equivalent rows and report table sizes, record counts, and duplicated payload
cost separately. The raw bundle and original checksum manifest stay unchanged.

## Clean rebuild and acceptance

1. Rebuilt directly from the unchanged 12 frozen source files using the retained
   namespace, immutable source-lineage/legacy allocation keys and selected IDs,
   without recreating the discarded legacy format or keeping a second dictionary copy.
2. Exact Unicode scalar and decoded source-row equality passed in
   [source-content-proof-final.json](../../target/lexicon/source-content-proof-final.json)
   (`307,243` matching raw assertions, `44,229` master records, `0` missing or
   duplicate assertions, `12` source hashes verified,
   `exact_decoded_source_fields_and_scalars: true`,
   `subject_ids_match_immutable_allocations: true`; reproducible via
   `tools/lexicon_proof.py --payloads-only`).
3. New claim revisions bind the actual reconstructed values (`0` accepted
   decisions existed in intake or remain in the workspace; no acceptance was
   fabricated or transferred).
4. Equivalent-row pre-projection intake bytes and independent clean replay passed
   in [us1-proof.json](../../target/lexicon/us1-proof.json) (`504,384,984` UTF-8
   CSV bytes vs `581,570,653` legacy escaped baseline across `307,243` intake
   records and `263,014` initial identities, with payload duplication remaining in
   both representations and `clean_inventory_and_stage_replay_identical: true`).
   Clean full inventory/stage replay belongs **before** representative pilot
   projection (`263,014` initial identities vs `264,402` post-projection identities).
5. Focused lexicon tests (`120 passed`), decoded curated CSV gate (`check_curated_csv`),
   structural pilot acceptance ([l2-acceptance.json](../../target/lexicon/l2-acceptance.json),
   [structural-final.json](../../target/lexicon/structural-final.json), exit `0`),
   fail-closed release rejection ([release-rejection-final.json](../../target/lexicon/release-rejection-final.json),
   exit `1`), [us2-proof.json](../../target/lexicon/us2-proof.json),
   `just agent-post-edit`, and `just agent-pre-stop-gate`
   ([pre-stop-utf8-final-retry.log](../../target/lexicon/pre-stop-utf8-final-retry.log))
   all passed. L2 unblocks Phase 6 numerals scheduling; source/reuse eligibility,
   L3 packs, and L4 runtime proof remain independent and pending.

This narrows Constitution II for large lexicon CSV data. Its scalar-inspection,
escaped-golden and control-preservation requirements remain in force. The
constitution's governance requires a major version increment for modifying an
established principle; the documented amendment is version 2.0.0.
