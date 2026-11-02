# Numerals and experimental calendar release candidate

This candidate includes approved numerals v0.3 and existing approved modules.
It also includes experimental, bounded calendar APIs inside the already public
`tamil-numerals` and umbrella packages. Their suites remain planned; selected
review checks do not activate them or establish complete calendar support.
This is the explicit candidate scope exception to the normal active-suite
requirement in policy.md, authorized by the request to finish a releasable
version while documenting pending work. No new public crate is introduced.

Thirukanitham covers the contracted 2024–2027 TN/SL contexts. Vakiya is the
source-named historical Ujjain mean-sunrise model, with per-operation limits.
Named observances use explicit TN community/publisher rules and retain known
publisher disagreements. Official holiday snapshots are bounded by jurisdiction
and year; provenance and reuse limitations remain visible in API metadata.

## Deferred work

- Arbitrary-location Vakiya corrections, true local sunrise/sunset and daylight
  periods; historical Bhujaantara interpolation remains experimental.
- Authoritative Thiruvalluvar-era boundary and the 2026 Gazette conflict.
- Krishna Jayanthi: annual festival-month selection needs a sourced contract.
  It is excluded from the candidate event inventory; exploratory helper code
  and source research are not a supported event selector.
- Broader regional/community evidence, calendar owner activation, holiday
  provenance/terms review and wider years.
- Independent review of the latest named festival selectors beyond the earlier
  reviewed subset; all calendar APIs remain experimental pending that review.

The last festival batch was interrupted and repaired during the candidate audit.
The following fresh verification supersedes its earlier incomplete counts.

## Final local candidate verification

Prepared version: Rust/npm `0.1.0-alpha.5`, Python `0.1.0a5`.
The candidate contains 35,646 approved active vectors and 225 planned calendar
review vectors. Calendar activation was not performed.

- Rust: 91 tests passed plus one intentional derived-exporter skip; doctests,
  Clippy and 121 harness checks passed. Python parity: 26 tests passed.
- WASM: 35,893 checks passed in the broad run. Its one stale convenience
  assertion expected the deferred event; after correction, that test passed
  separately against both targets. The focused convenience query uses October
  so annual serialization is not repeated unnecessarily. Annual exact-output
  vectors remain in the broad run; their test budget is 120 seconds, not a
  latency guarantee. The original full-gate invocation retains that recorded
  assertion failure; the targeted rerun resolves it without rerunning unchanged
  numerical tests.
- Dart analysis and all 35,890 checks passed.
- Workbench coverage (84 forms), TypeScript check and production build passed.
- Formatting, Unicode/schema, release policy and all 50 release-copy checks
  passed. Release-check passed isolated Rust/Python/Node/browser-WASM consumers;
  each installed WASM package passed all 35,871 selected vectors.
- Nine alpha.5 archives have verified SHA-256 digests in
  `target/alpha/alpha-5-SHA256SUMS.json`; the cumulative digest file has 45
  historical/current archive entries. No upload occurred.

The three monthly fixture names mentioning Krishna Jayanthi are historical
query names; their candidate expectations omit that event. They verify the
remaining monthly inventory, not the deferred selector or its publisher date.
The broader calendar completeness milestone remains deferred as listed above.
The user authorized committing and pushing this candidate after verification.
No release tag or registry publication is part of that action.
