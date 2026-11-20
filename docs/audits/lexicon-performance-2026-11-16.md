# Lexicon verification performance — 2026-11-16

Scope: the checked-in 11,370-entry / 25,733-sense three-pack dictionary,
307,243 historical intake records / 12 frozen source files, and existing
Rust/Python/Node/browser-WASM/Dart acceptance. No publication or release-scope
change is part of this work.

## Preserved baseline

`target/lexicon/speed-baseline/` preserves the completed acceptance, isolated
three-profile archives, harness log, and enforced benchmark report. The owner
stopped the extra whole-pre-stop baseline. An earlier attempt failed on disk
space after 1718.285468 seconds; the subsequent owner-stopped attempt is also
incomplete. Neither is a passing before-time or a valid speedup denominator.
No extra unmodified baseline was restarted.

## Measured results

| Workload | Before | Candidate | Conditions |
| --- | ---: | ---: | --- |
| Full harness | 447 passed, 1130.88s | 484 passed, 64.25s | All original test IDs retained; 37 additional regression cases |
| Binding synchronization | No isolated comparable timing | 200.681069s cold; 1.344987s warm | Core, Python + Node WASM + browser WASM + Dart; independent Cargo targets |
| Structural pipeline | 40.918690s; 388.26 MiB | 47.121055s; 391.40 MiB | Debug binding; full 307,243 rows and 12 hashes |
| Structural pipeline, optimized binding | Same baseline used debug | 45.351766s; 390.30 MiB | Explicit optimized-build diagnostic; not a like-for-like speedup |
| Warm native lookup p95 | 6.5444ms | 7.4617ms | Same seeded 10,000-query core corpus; debug binding |
| Warm serialized lookup p95 | 7.3160ms | 8.3358ms | Full response verification; debug binding |
| Exact pre-stop gate | No completed passing timing | 835.532051s passed | Do not derive a ratio from failed/stopped attempts |

The harness improvement is about 17.6x. The structural pipeline and lookup do
**not** demonstrate a net speedup in these measurements; all measured final
budgets still pass (under 60s, at most 512 MiB; lookup p95 under 10ms).
A first native-debug candidate regressed to 92.621592s and correctly failed;
that report remains in `speed-candidate/lexicon-benchmarks.json`.

## Changes and preservation checks

- Session fixtures validate real checked-in packs once across xdist workers,
  bind cached results to file-content fingerprints, and assert immutability at
  teardown. Negative/tamper tests use isolated small canonical packs.
- Cross-process locks protect shared Cargo work independent of scheduler groups.
  Explicit `--dist=load` lock regressions passed (3 tests, 19.44s); serial fixture
  and real native checks passed (76 tests, 128.68s).
- Actual profiles covered inventory, stage, CSV validation, proof and CLDF export
  across all three packs. Bounded Rust/PyO3 helpers preserve exact scalar audits,
  JSON encodings and hashes with reference fallbacks for unsupported Python
  values. Cycles fail promptly; shared DAGs and iterable dictionary pairs retain
  their intended behavior. Nine direct native parity tests pass.
- CPython's C encoder beats unoptimized generic Rust batches. The adapters use
  optimized native generic batches only when `HOST_BATCH_OPTIMIZED` is true;
  debug builds retain the reference checks/encoder/hash path. Both choices are
  exercised by a regression test. Rust text auditing remains active in both.
- Genuine offline pycldf/csvw validation still executes. Parsed rows are cached
  only within a validation call; the redundant second FK pass is omitted only
  after successful Dataset.validate(), which already executes that check.
- Binding cache hits require source, toolchain, profile and output hashes.
  Cross-process leases cover canonical builds and consumers. Force builds remain
  available. Warm reuse still runs the parity consumers.
- Daily gates select one profile. The explicit final runtime and isolated
  archive recipes retain default/core/full coverage. Only the proven duplicate
  Rust package invocation was removed; workspace tests, doctests and 10,000-case
  properties remain. The existing ignored calendar evidence exporter stays
  ignored, exactly as before; no new tests were skipped.
- The first optimized pre-stop attempt passed all 220 Rust tests, then exposed
  fake build unit tests depending on actual free disk space. Their fake-runner
  fixtures now control that input; dedicated low-disk rejection assertions and
  the production guard remain intact. Focused 28 tests pass. The failed 756.656629s
  run is preserved rather than reported as successful.
- Independent Hydrogen high reviews, including cycle/fallback, disk-guard and
  scalar-fixture follow-ups, found no actionable issues after remediation.

Evidence and logs: `target/lexicon/speed-candidate/`. Final gate, all three runtime profiles, and all three isolated archive profiles
passed. Private Dart archives also passed for every profile. The original 12
source hashes were reverified after acceptance. Per-step timings and exit codes
are recorded in `speed-candidate/acceptance-summary.json`. Core development
bindings were restored and all core runtimes, including Dart, rechecked successfully
in 121.690161s after archive verification. No publishing occurred.
