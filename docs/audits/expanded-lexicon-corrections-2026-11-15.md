# Expanded lexicon correction checkpoint

The corrected revision-pinned Wiktionary extraction contains 11,370 entries and
25,733 senses. This checkpoint records implementation and regeneration evidence;
expanded runtime and archive acceptance remains pending.

| Pack | Entries | Senses | Assertions | Dataset version |
| --- | ---: | ---: | ---: | --- |
| core | 10,336 | 23,818 | 50,693 | 0.1.0+1f2bc70dc132 |
| names_taxa | 762 | 906 | 2,833 | 0.1.0+279048283410 |
| regional | 272 | 1,009 | 2,098 | 0.1.0+b97b5f21230d |

Repeated POS headings now retain separate source identities across etymologies.
Regional routing uses the entry's own qualifiers. Unknown qualifier prose remains
literal evidence with review diagnostics rather than generating domain codes.
Four pinned regressions failed before these fixes; all 12 extraction tests passed
afterward. Native-checked regeneration and promotion then completed successfully.

The six human-reviewed entry/sense payloads remain exactly equal to their previous
projections. The 44 core golden expectations received pack metadata updates only.
Evidence is recorded in
`target/lexicon/corrected-pack-refresh-proof.json`,
`target/lexicon/corrected-bulk-dryrun.log`, and
`target/lexicon/corrected-bulk-promotion.log`.

Default Cargo data features remain empty. The `full` verification profile builds
core, names_taxa and regional. It reports exclusions of the 44 core-only golden
vectors, whose unavailable-pack expectations cannot apply to a full build.
Dedicated full-profile checks verify the three manifests and actual lookups.

Independent re-review found no further extraction, routing, provenance or compact
runtime defects. It identified stale Rust and CLDF metadata assertions, which have
been refreshed. Focused profile tests also exposed invalid archive fixtures that
combined signed manifests with stub CSVs; those fixtures now copy the signed
files. Profile inference unit tests explicitly control their input profile.
Rust's absent-word check reads the existing golden case, avoiding a second literal
pin. The private Dart archive helper supports direct-script imports.

The final narrow independent Hydrogen high follow-up reported no findings. It
confirmed golden-helper and row-ID checks across all four runners, escaped
absent literals in isolated smoke consumers, preserved parameterized error
assertions, and current citation metadata. The final golden file has SHA-256
`023bc22e8ac6655db97724a7125408f612a18110a6daec48c170e521d7d05232`.
This was a read-only inspection; runtime and archive acceptance still requires
the serialized checks below.

Current CLDF verification passed 14 tests in 297.03 seconds. The initial full Rust
run passed five golden tests, ten lookup tests and 24 compiler tests; the remaining
compiler fixture panicked on TOML index assignment to an absent optional key.
The fixture now inserts that key explicitly. The serial queue resumed at the Rust
step, retaining the passing CLDF evidence and gating archives on runtime success.

The Rust rerun passed all five golden, ten lookup and 25 compiler tests. Full
binding parity then found a convenience-test expectation that confused compiled
pack availability with default query selection. Default queries search core;
the Python and TypeScript tests now assert core metadata, while explicit
three-pack queries are checked separately in Python, TypeScript and Dart. These
are test-only changes; the rebuilt full runtime artifacts remain current.

Real parity and Dart subsequently passed under full, core and default profiles.
The final gate passed formatting, Unicode/schema, release policy, 129 release
copies and workspace checks. Clippy then exposed a default-profile typed test
using an import gated to core. Qualifying that call fixed it: nine default lookup
tests and workspace Clippy passed. Remaining pre-stop steps and archives are still
pending; passing profile checks alone do not close expanded acceptance.

## Long harness diagnosis and fixes (2026-11-16)

The owner requested investigation of the long-running harness. A live `py-spy`
stack identified `unicode_findings` rebuilding the entire decision index per
assertion, even with no exceptions. On the expanded core this combined roughly
50,000 claims and decisions, and candidate verification repeated the work. The
run was stopped. Decision indexing and terminal-history lookup are now lazy and
run on the first actual exception; ordinary Unicode inspection still always runs.
Three ordinary/NFD/joiner regression cases failed before the fix.

A subsequent five-second profile attributed 406 of 499 samples to the review
helper's Python schema validation. That helper now uses the existing shared
compiled row validator, including scalar checks and the reference-validator
fallback for nonstandard Python values. Differential type/missing/extra-field
tests preserve schema outcomes. Combined focused tests passed 106 cases in
9.00 seconds. A fresh independent Hydrogen high read-only review found no
actionable issues in the lazy index, schema reuse, authorization or import safety.

The full harness is rerunning with individual test names, duration reporting and
diagnostic stacks for tests exceeding 120 seconds. Evidence is under
`target/lexicon/`: `slow-harness-stack.txt`, `lazy-unicode-before.log`,
`lazy-followup-profile.json`, `shared-validator-followup-profile.json`,
`lazy-unicode-focused.log`, and `lazy-unicode-full-harness.log`.
Final harness and downstream archive completion are still pending.

Release source synchronization verified 129 files. Full-profile PyO3, Node WASM,
browser WASM and TypeScript library builds passed. The initial focused profile run
reported 30 passed and six failed; repair validation and subsequent serialized
acceptance steps are tracked in
`target/lexicon/corrected-acceptance-progress.json` and corresponding
`corrected-*.log` files. These pending checks must finish before T082/T083 close.

The 12 historical source files remain quarantined and unchanged. Bulk claims retain
automated source acceptance, distinct from the 31 human-reviewed claims. No
publication, version change, registry scope change, commit or push is included.
