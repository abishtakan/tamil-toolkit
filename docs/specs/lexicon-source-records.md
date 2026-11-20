# Owner-supplied historical record lookup (draft, 2026-11-16)

The owner explicitly requested inclusion of the entire supplied 307,243-record
historical CSV bundle and reported no additional third-party permissions.
This path makes supplied records searchable without representing them as
accepted dictionary claims or granting a new license to their contents.
Verified lexicon_lookup and its packs/acceptance rules remain unchanged.

Rust owns query NFC normalization, bucket selection and exact matching. Never
trim whitespace, case-fold, repair spelling, or remove joiners. Preserve every
original CSV cell as a string, including empty cells and inherited status text.
A source row is one-based after the header, not a physical text line. Duplicate
rows remain independently addressable by source_file and source_row.

## Shared dispatcher

lexicon_source_bucket takes a string (1..65536 UTF-8 bytes), returns
{query, normalized_query, bucket}, where bucket is the first SHA-256 byte of
normalized_query as two lowercase hexadecimal digits.
Errors: lexicon source: invalid query (wrong type, empty, or too long).

lexicon_source_lookup takes exactly {query,bucket,offset,limit}. offset is a
nonnegative integer <=1000000 and limit an integer 1..100. bucket is the data
object {schema_version:1,bucket:<two hex>,records:[...]} exported below. Each
record is exactly {source_file,source_row,lookup_key,fields}; source_file is a
plain CSV filename, source_row a positive integer, lookup_key a nonempty NFC
string, fields an object with string values. Validate every supplied record,
its NFC key and bucket assignment before returning any result. Reject duplicate
(source_file,source_row) locators. Invalid query uses the query error; all other
invalid shape/options/content: lexicon source: invalid bucket or options.

Response: {query,normalized_query,status,data_status,rights_status,total,offset,
limit,records}. status is matched iff total>0, else not_found, even if a requested
page is empty. data_status is owner_supplied_unverified and rights_status is
unresolved. total counts all exact matching rows, records is the selected page
in source-file then source-row order. Do not infer regional scope or linguistic
acceptance from inherited source cells.

## Deterministic exporter

The Rust source-records binary takes <source-dir> <frozen-manifest> <new-output-dir>.
Verify ALL twelve frozen file lengths and SHA-256 hashes before writing output,
including the old FST (which is not used for queries). Reject extra CSV files,
unsafe paths, wrong row widths, duplicate headers and existing output paths.
Index all eleven CSVs; preserve the originals untouched. Select the primary
lookup column: headword_ta for primary_lemmas/primary_meanings/unified_master;
source_headword_ta for primary_relationships (outgoing relations); term_ta for
archaic/dialect/technical; phrase_ta for phrases; name_ta for proper names;
tamil_name for taxa; transliterated_ta for loans. Empty keys fall back to
scientific_name if present, then '<filename>:<source_row>', so every record is
addressable. Normalize only the lookup key; retain original cells verbatim.
Write 256 bucket JSON files, a manifest with input hashes/per-file and total
counts, distinct key count, bucket hashes/bytes and exact data/rights status,
and a NOTICE.md recording owner direction and no newly asserted content license.
Output must account for all 307243 rows exactly once. No accepted decisions or
verified pack metadata may be synthesized. An exporter failure leaves no usable
manifest; completion manifest is written last.

## Browser and release behavior

The playground offers a separate Historical source records view with exact
search, original field display, per-row provenance and pagination. Fetch only
the required bucket, validate its byte hash against the manifest, then call the
shared Rust dispatcher. Surface missing/stale data or unsupported engine errors.
Do not count historical records as verified words. Exported data is a separate
owner-directed artifact; current MIT/CC verified package metadata does not
relicense it. This implementation does not itself upload any package.

Tests cover actual frozen source samples, absent queries, whitespace/joiner
preservation, pagination, malformed buckets, duplicate locators, deterministic
export and full-corpus row/cell identity. Fixtures remain planned until real
runtime review; planned tests are not counted as active parity.
