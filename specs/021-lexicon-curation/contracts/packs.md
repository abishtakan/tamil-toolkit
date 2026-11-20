# Pack Compilation and Distribution Contract v1

Large dictionary CSV uses readable UTF-8 with the versioned
`json-string-utf8-v1` reversible cell codec. Golden tests and scalar diagnostics
retain escapes. Runtime FST/posting/text bytes use the deterministic compact
format selected by Rust build tooling; do not serialize ASCII escapes into a
runtime pack merely to copy the editorial representation. Measure actual source,
archive and runtime bytes separately. The
[storage decision](../../../docs/decisions/lexicon-text-storage.md) requires an
explicit verified clean UTF-8 rebuild and grants no pack/source approval.

**Status**: Proposed L3/L4 design. None of the supplied source text is approved
for bundling by this plan. [Research](../research.md) records alternatives.

## Pack profiles

| Pack ID | Future Cargo feature | Content scope |
|---|---|---|
| `core` | `lexicon-core` | Approved dictionary entries, reviewed literary/loanword content where selected, and required evidence |
| `terminology` | `lexicon-terminology` | Approved technical equivalents/senses and MWEs; no invented definitions |
| `names_taxa` | `lexicon-names-taxa` | Approved names/taxa with typed supporting assertions |
| `regional` | `lexicon-regional` | Attested regional lexical material and scope evidence |

All dataset features are off by default and are additive. Forward them explicitly
through the Python, WASM, and Dart Rust binding manifests/build tools. Every
consumer build records its profile; default Rust and default FFI builds contain
zero embedded dictionary payload bytes and do not claim dictionary availability.
No variant of the existing npm/PyPI package is published in this feature. Future
release review chooses the bundled profile and corresponding golden manifest;
the package inventory/version/channel remain governed by current policy.

Pack selection does not determine claim eligibility. One entry can belong to
several packs without allocating a new identity. A pack must include the required
forms, senses, scope metadata, sources and evidence/decision summaries for every
selected entry. Structural dependencies cannot be silently omitted. Optional
cross-pack relations may be omitted only under an explicit per-relation policy,
with omitted IDs/counts and reasons in the pack's audit manifest. No dangling
returned link is permitted. Unknown/ineligible source text is never included to
close a reference. A source/entry revision conflict between packs fails validation.

## Input and output manifests

Canonical inputs are declared in `lexicon/dictionary/packs.toml` plus table
manifests: dataset/schema/codec/Unicode versions, selected entry revisions,
source/reuse/terms digests, vocabulary versions, index-format version, and required
attributions. The digest covers the exact sorted file list and bytes. Cache
identities do not rely on filesystem mtimes or directory enumeration order.

Compilation sorts NFC keys by UTF-8 bytes, groups all eligible entry IDs per
key, and sorts postings by stable ID. `fst` 0.4.7 maps each unique key to a posting
ordinal; a checked range table resolves its offset/count. Integer tables use
explicit little-endian widths with checked conversions, never architecture-sized
`usize` or host endianness on disk. Lookup uses safe reads/borrows; no unsafe mmap.
Entry/sense payloads and evidence projections have deterministic field ordering,
newline/escape rules and checksums. No timestamps, absolute paths, randomness,
or network data enter reproducible artifacts. Event review dates are source
input metadata, not a newly generated build time.

`build.rs` compiles into `OUT_DIR` only. Supplied `.fst` bytes are not a trusted
input. Required validation is repeated on packaged canonical data; host Python
is not required for standalone Cargo users. Builds from identical declared inputs
must produce identical generated data/index bytes on Windows and Linux. Toolchain
and target differences in executable binaries do not invalidate data-byte tests;
compare data artifacts separately from full compiler output.

The future build helper must be driven by the same table/schema contract as
host promotion and tested with malformed/eligible packs. Build dependencies
remain lower-ranked existing crates and external parsing/index libraries. It
must never depend back on `tamil-toolkit` or on a rank peer through a new cycle.

## Release-file ownership

Extend `tools/release_files.py` with an explicit selected-file mapping for the
approved dictionary projection and applicable source terms/notices; do not
recursively copy `data/` or all `lexicon/` subdirectories. Generate crate-local
copies under `crates/tamil-toolkit/lexicon/dictionary/` and include them via
reviewed Cargo `include` patterns. Update generated notices through canonical
inputs and sync tooling, not by editing distribution copies.

Cargo feature selection controls embedded runtime bytes, not source archive
contents. An approved optional pack may still be present in a `.crate` source
archive: every included file must independently have approved redistribution
terms. No unresolved or private editorial data may enter an archive even when
its feature is disabled. Feature-disabled build checks must verify both zero
payload embedding and package inventory. Python/npm/Dart artifacts and source
archives receive the required attribution/terms for their actual content.

`just sync-release-files` and `just check-release-files` must cover all new copies;
`just check-release-policy` preserves approved crate closure, versions, and ranks.
At L4, `just release-check` builds actual archives in isolated offline consumers
and runs nonempty approved acceptance cases, without registry upload.

## Validation and budgets

Two clean data-generation runs compare every output byte and manifest checksum.
Verify that each selected eligible entry ID appears in its posting list, every
key maps to every approved homograph, all ranges are bounded/non-overlapping,
and no ineligible assertion/terms file is bundled. Check no-data and all supported
feature combinations, including pack removal/reference policies and duplicate
identities. Data-only profile checks are separate from public-operation parity.

Record per-pack canonical bytes, generated index bytes, total embedded bytes,
startup cost, warm/cold query latency, response sizes, and peak memory on a named
reference machine. Initial engineering targets are under 60 seconds/512 MiB for
full structural processing and warmed exact lookup p95 under 10 ms for 10,000
queries with inputs up to 64 KiB, excluding result serialization. These targets
are unmeasured. Benchmark output must also report serialized end-to-end latency
and large-result cases; never drop senses or homographs to meet a target. L3
approval records a measured pack-specific size budget before any distribution;
no default embedding or unknown full-corpus guarantee is permitted.

The structural workload measures inventory, staging and structural validation
of all 307,243 CSV records and the 12 source file hashes into fresh outputs.
Report each stage and end-to-end wall time, peak process-tree RSS and its
sampling method, reference machine/OS/toolchain, input hashes and target misses.
Exclude environment installation/compilation, not executed data-processing
stages. Lookup is a separate workload; a pilot run or lookup timing cannot stand
in for the full structural 60-second/512-MiB measurement.

## Milestone boundary

A structurally valid L2 pilot with zero eligible content is a successful pilot
and an unavailable dictionary. It cannot produce a release-approved pack, pass
nonempty CLDF exchange acceptance, activate a runtime suite, or establish L4.
L3 needs actual approved assertions; L4 needs unchanged real-runtime fixtures,
Dart host ABI checks, standalone archives and separate activation/release review.

## Dataset compatibility and content identity

`dataset_version` retains the complete published value, including the per-pack
content hash in its `+` build metadata suffix. When combining packs, compare the
release portion before `+`; build metadata identifies content and does not select
a different release compatibility epoch. Schema, index-format and vocabulary
versions must still agree, as must overlapping entry revisions and region-parent
definitions. Different release portions or conflicting shared records fail with
`lexicon: incompatible pack versions`. Full per-pack manifest hashes and version
strings remain visible in `PackInfo`; this rule grants no approval to new data.
