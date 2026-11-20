# Full historical lexicon release readiness

The historical record explorer is implemented and verified locally as of
2026-11-20. The separate ZIP covers all 307,243 original CSV rows under 177,606
lookup keys. Original cell comparisons and all 256 bucket hashes pass. The
data status is `owner_supplied_unverified` and third-party rights remain
unresolved. The owner authorized implementation and accepted responsibility
for addressing reuse questions.

The owner requested recovery of the entire 307,243-record historical bundle on
2026-11-16, and confirmed that no additional permission/open-license records are
available for TVA/Sorkuvai, Oxford/Apple, Tamilcube or Cre-A.

## Version and scope

The workspace is prepared for `0.1.0-alpha.8` (`0.1.0a8` for Python). The
latest immutable release tag is `v0.1.0-alpha.7`. The [alpha.8 release record](alpha-8.md)
tracks local checks and preparation for registry publication.
Cargo default data features and the approved crate/registry scope remain intact.

## Included work prepared so far

- Seven fresh Wiktionary entries / nine senses have been merged into the core
  data while preserving all 10,336 previous entry revisions and every existing
  golden entry payload. New canonical coverage is 9,410 distinct written forms,
  11,377 entries and 25,742 senses across the existing three packs.
- The source-backed seven-case suite is **planned**, explicitly exercised for
  review, and excluded from active-parity totals until owner activation.
- The original 12 historical files remain byte-identical and their claims remain
  quarantined. Matching a headword in a fresh source does not approve historical
  definitions, examples or derived fields attached to that spelling.
- A bounded rendered-source capture is investigating the remaining Wiktionary
  parser gaps. Those outputs are proposals, not approved historical claims or
  human-reviewed entries. The captured HTML, render time and current dependency
  limits must remain distinct from original revision wikitext.

## Verified promotion gaps (distinct from supplied-record access)

| Source slice | Evidence needed for verified dictionary promotion |
|---|---|
| TVA 117,121 technical rows; Sorkuvai 3,361 | Exact original records/endpoints or an authorized fresh export, applicable reuse basis, source attribution, and review of encoding/phrase/domain issues. Neither the supplied package nor current probes recovered a suitable project grant. |
| Oxford/Apple, Tamilcube and Cre-A slices | An applicable redistribution grant or independently sourced replacement claims. Source labels and local/public accessibility do not satisfy the project's reuse gate. |
| DSAL/Madras, Wikisource editions and other named sources | Exact editions, record locators, acquisition trace and applicable license/permission evidence. Current site terms cannot prove the terms of an unknown historical snapshot. |
| Unattributed or processing-labelled rows | Original source trace and actual lexical attestation; distinguish definitions from placeholders and observed forms from generated candidates. Preserve originals while claims remain withheld. |
| Rendered template expansions | Complete capture evidence and explicit review of the new extraction profile/claims under the existing acceptance rules; no fabricated human decisions or silent weakening of source-fidelity rules. |

The curation contract states: "No command infers source URLs or permissions from
labels." Passing structural checks is not an alternative to this source gate.
See the [full technical/source audit](../audits/historical-technical-recovery-2026-11-16.md),
[original readiness inventory](../audits/lexicon-source-readiness-2026-11-16.md)
and [local permission-request drafts](../../target/lexicon/full-recovery/technical/permission-request-packet.md).
No requests have been sent on the owner's behalf.

## Release preparation

Core integration and Dart checks passed. The two new lexicon golden suites were
exercised for review with 12 vectors and await activation review. The separate
data archive passed integrity checks and the local production playground can
serve the complete export. Evidence is recorded in
[the project handoff](../status.md#historical-source-record-explorer-2026-11-20).

The local SDK archive matrix passed on Windows for default, core and full. Follow
[the publishing policy](policy.md) for the version, source commit and reviewed
artifact run. See [the source-record contract](../specs/lexicon-source-records.md)
for the local export and lookup behavior.
