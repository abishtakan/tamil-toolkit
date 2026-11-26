# Data Model — Tamil Word and Sentence Tokenization

The [module contract](../../docs/specs/tokenize-v0.1.md) defines the boundary profile. The [interface contract](contracts/tokenizer.md) defines request and result serialization.

## Source text and coordinates

| Entity | Fields | Validation |
| --- | --- | --- |
| Source text | Original Unicode string | Retain every scalar, including detached marks, non-NFC signs, and joiners. |
| Written unit | Original byte range and its ordinal in the document | Enumerate tailored `tamil-core::Letters` units on original text. Include whitespace, punctuation, other scripts, and malformed units. |
| Source span | `text`, `start_byte`, `end_byte`, `start_unit`, `end_unit` | Both ranges are nonempty, zero-based and half-open. Both select `text` from the same source. Endpoints are written-unit boundaries. |
| Word token | Source span and `kind` | `abbreviation`, `word`, `number`, or `other`. Order and coverage follow the module rules. |
| Sentence | Source span | Trim outer whole whitespace units. Preserve interior whitespace and closing punctuation assigned to the sentence. |

Entries in each result list are ordered by ascending start and do not overlap. Each unfiltered list covers every non-whitespace unit once. A filtered word list is a stable subsequence of the unfiltered list. Case, joiners, and original composition remain in all returned strings. Unit indices count positions across the whole source, including omitted whitespace and tokens.

## Abbreviation inventory

| Field | Meaning and constraints |
| --- | --- |
| Surface | Complete NFC form with the recorded periods. Keys are unique after canonical normalization. |
| Use class | Reviewed honorific, dotted initial, time marker, currency marker, or example marker. |
| Context | Canonical eligibility and permitted final-period continuation. Capture following letter or decimal classes, spacing, and permitted continuation punctuation for the entry. Keep lexical matching and final-period decisions distinct. |
| Attestation | Region, named source, and page or section locator for each admitted form or variant. Record the supporting examples and rights for redistributed material. |

Matches start and end at original written-unit boundaries. Prefer the longest eligible form at a given start. Token order uses left-to-right non-overlapping matches. The word pass inserts both endpoints and suppresses boundaries inside the match. The sentence pass preserves hard boundaries and distinguishes abbreviation periods from independent terminators.

## Stopword profiles

| ID | Membership |
| --- | --- |
| `none` | Empty set. Default when omitted. |
| `conservative` | Reviewed subset of common function words. |
| `broad` | Strict superset of `conservative`, with rationale for the additional entries. |

Each admitted entry is one NFC word with evidence, profile membership, an inclusion rationale, and recorded source rights. Compile unique entries and reject source records that violate containment or NFC rules. Compare complete word tokens by NFC equality. Non-word kinds, unlisted inflections, and joiner-bearing variants outside the admitted set remain eligible for output.

## Verification records

- The planned golden suite uses the repository schema and the two dispatcher operation names. Each row has a globally unique ID, expected result or error, dialect, source, and tags. Use explicit Tamil escapes and exact exception pointers for intentional NFD and joiners in both input and expected text.
- Corpus cases label region and case group. Independently annotated expected boundaries are stored with the passage and evidence. Compare word and sentence endpoints using original UTF-8 byte positions and consistent whitespace treatment. Record missed and spurious boundary counts by group and check source integrity separately.
- Raw Unicode tests keep the official input, expected boundary markers, version, hashes, and license. They exercise the default boundary iterators before Phase 9 tailoring.
- Suite status moves from `planned` to `active` only after owner review. Preactivation execution uses the same fixtures and reports its counts separately from active results.
