# Alpha 9 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.9`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.9)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.9`; Python `0.1.0a9`.
- Reviewed source commit: `bbc6a3e35369034d3286eadc8653c1921749f37c`.
- Artifact workflow: [run 45013314365](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013314365), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `4346ab7340f32e7051e2be895f0e0b30c97a0bf8aef66d02343e2ff8184190f8` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `47f0cb21e4661a0522f65c186b51545eb7e492f68c7502c370856a2adb9b49a5` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `1b37e60f2bd2fdab1fe79f7c400e9e110ba54ffc472dea9fa2a7a283d98068cc` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `568461413787283f33edc67f1c72a6cd59b533a9b420a8039472bb0f506d14ce` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `ba915a1e96e1b5672c4c18f7f6e6a298153b848470c2d3a3f3aa48cedc5728c4` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `624671a8ad037e75351b9b1054b53d7e39e55d12e65e81693dcb76490ec0396b` |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `99d9180e37b62d3b22a9dd256b1fedaab97a174f1fda809a4ec7bb84c1ff24c5` |
| [`tamil-translit`](https://crates.io/crates/tamil-translit/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `6b4d72a2c93bbb06a46e6d5d134c3d76d1ab3713d55ffc0fc7ebd3732aabf9c3` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.9) | `0.1.0-alpha.9` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `09b9d77d69fec6db372964efff2dadcf1a68417e2e0e532d662aee123bb31ccb` |

### npm

[`tamil-toolkit@0.1.0-alpha.9`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.9)
was published by [run 45013766149](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013766149)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`pending`.
The `alpha` and `latest` tags point to `0.1.0-alpha.9`.

### PyPI

[`tamil-toolkit 0.1.0a9`](https://pypi.org/project/tamil-toolkit/0.1.0a9/)
was published by [run 44756745737](https://github.com/abishtakan/tamil-toolkit/actions/runs/44756745737)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a9-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `pending` |
| Windows wheel `tamil_toolkit-0.1.0a9-cp311-abi3-win_amd64.whl` | `pending` |
| macOS wheel `tamil_toolkit-0.1.0a9-cp311-abi3-macosx_11_0_arm64.whl` | `pending` |
| Source archive `tamil_toolkit-0.1.0a9.tar.gz` | `pending` |

## Compatibility and scope

Pending publication.
