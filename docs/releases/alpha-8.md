# Alpha 8 release

Status: published to crates.io, npm, and PyPI. Immutable tag
[`v0.1.0-alpha.8`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.8)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.8`; Python `0.1.0a8`.
- Reviewed source commit: `9fc40f6ae081d8cc0a0307fa7325de4f2f66db6d`.
- Artifact workflow: [run 44755276268](https://github.com/abishtakan/tamil-toolkit/actions/runs/44755276268), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs (14/14 jobs).
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist under the default slim MIT profile (`tamil-toolkit-0.1.0-alpha.8.crate` is `92.21 KB`, well below crates.io's `10 MiB` limit).
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

Each approved crate was uploaded in dependency order via the `crates` job of
[run 44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322).
Registry checksums are the SHA-256 values returned by the crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `6eb4b11c0d50ac1fcb8d98ad04c295d279844b08c297961d9d9841cac8892e9b` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `03be93584ff841f324d9d3616385202e543d1d4bc7e78a9ec5a2d7fe76c21f7c` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `0cae8b37d7d90db2e4fe77e16450d067eb270c1cf88d2df081013acfa9b96524` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `ebb1de78a34f840c7a8cff69e1363f96cf0c9884fc54da5a58051f55617b6888` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `ecf2373a75ac2ddcf26f1f4466d09f00a81667e02677a569388cd31eda7e2997` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `b495549c77859c591aeb58cef32b6e91ae33172ebb054f204c6b5204acee87fd` |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `178a2d120bb88541a4b39c036eea7abe7293dbe55b50c6121c0aa45069264c1f` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.8) | `0.1.0-alpha.8` | [44756065322](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756065322) | `b586e9462d1262fba9cb3b7f1ef8588594ef11189fbac94dc082830908b719c2` |

### npm

[`tamil-toolkit@0.1.0-alpha.8`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.8)
was published by [run 44756738415](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756738415)
(`publish-npm.yml`) using the configured OIDC trusted publisher. The published
tarball SHA-256 is
`f08b31b98e2452cb2770fd6623d8dbdb63c13cbe038f91393b904078847d66c7`.
The `alpha` and `latest` tags point to `0.1.0-alpha.8`.

### PyPI

[`tamil-toolkit 0.1.0a8`](https://pypi.org/project/tamil-toolkit/0.1.0a8/)
was published by [run 44756745737](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756745737)
(`publish-pypi.yml`) through the configured OIDC trusted publisher and required
`pypi` reviewer approval. PyPI's four public file digests match the reviewed
build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a8-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `9c732d6c175544a51fe76771b76f86dff6715efc00ecbe210e73332aeca337f1` |
| Windows wheel `tamil_toolkit-0.1.0a8-cp311-abi3-win_amd64.whl` | `fa68490e51fd108eaafb8351ec9a2bc4953bd07eb585638ab22b0e0774afb26a` |
| macOS wheel `tamil_toolkit-0.1.0a8-cp311-abi3-macosx_11_0_arm64.whl` | `4c17489f280d32bfcd7b9cfbf930929e59900e0205394fe23f788811f521222c` |
| Source archive `tamil_toolkit-0.1.0a8.tar.gz` | `d26a593f3498473c05b0a3b60ef1aceb61936d8aa1f01f9c1f033962e15d54d7` |

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
