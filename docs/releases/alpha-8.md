# Alpha 8 release

Status: local release checks passed. Source review and publication are pending.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.8`; Python `0.1.0a8`.
- Reviewed source commit: pending.
- Artifact workflow: pending.
- Local release checks passed on Windows for integration, host Dart, and the
  complete default, core and full archive matrix.
- Local check results: `target/lexicon/alpha-8/progress.json`.
- Local checksums: `target/lexicon/alpha-8/archive-digests.json`. The audit
  verified 36 archives and confirmed that the historical bundle is stored separately.

## Local verification

The integration gate passed formatting, release policy, Unicode and schema
checks, source synchronization, Clippy, Rust (227 passed, one skipped),
doctests, the harness (522 passed), and golden parity (36,205 active vectors).
Dart passed 36,225 tests. The production playground built successfully and
all 111 playground tests passed.

The Rust, Python, Node and browser-target WASM, and private Dart consumers
passed after installation or extraction from the local archives. Each ran the
golden cases selected for its profile.

| Profile | Golden cases per isolated consumer |
| --- | ---: |
| Default | 36,161 |
| Core | 36,205 |
| Full | 36,161 |

The core-only suite contributes 44 cases to the core profile. The new
historical and Wiktionary suites retain their planned status.

## Published registries

### crates.io

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.8) | `0.1.0-alpha.8` | pending | pending |

### npm

[`tamil-toolkit@0.1.0-alpha.8`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.8)

### PyPI

[`tamil-toolkit 0.1.0a8`](https://pypi.org/project/tamil-toolkit/0.1.0a8/)

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a8-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | pending |
| Windows wheel `tamil_toolkit-0.1.0a8-cp311-abi3-win_amd64.whl` | pending |
| macOS wheel `tamil_toolkit-0.1.0a8-cp311-abi3-macosx_11_0_arm64.whl` | pending |
| Source archive `tamil_toolkit-0.1.0a8.tar.gz` | pending |

## Compatibility and scope

The optional dictionary profiles provide 9,410 distinct written forms, 11,377
entries and 25,742 senses across the verified core, names/taxa and regional
packs. Default builds omit the embedded dictionary. The seven Wiktionary
recovery cases and five historical lookup cases retain planned fixture status.

The historical record explorer indexes 307,243 owner-supplied records using
177,606 distinct search keys. The data is available as a separate local ZIP and
playground export. Source rights remain unresolved and linguistic claims remain
unverified. The archive retains the source locator and each original CSV cell.
See [historical release readiness](lexicon-full-bundle-readiness.md) for evidence
and [the source-record contract](../specs/lexicon-source-records.md) for the
dispatcher operations and their input and response formats.
