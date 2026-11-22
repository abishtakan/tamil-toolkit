# Alpha 10 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.10`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.10)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.10`; Python `0.1.0a10`.
- Reviewed source commit: `ba4fa913bf327157323eeb7f8975e4f39b29224a`.
- Artifact workflow: [run 45057597093](https://github.com/abishtakan/tamil-toolkit/actions/runs/45057597093), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `427d89860b89e3351b35ef6f187a0dd4a4e67825040fa137a3b32846d1d3e1f4` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `668e8c14eea59877963650cc8abefc6a06a02259d14d7a53cda7dc37dac713a5` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `a0d62acbab85399870a88b4f9c775c7780c8e8926fa8cd6a18e7289b52feea93` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `147a7b89a9e5ae89596a7a024021714616b87d93dfae551958908d36c7e17217` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `pending` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `pending` |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `pending` |
| [`tamil-translit`](https://crates.io/crates/tamil-translit/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `pending` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45013643980](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013643980) | `pending` |

### npm

[`tamil-toolkit@0.1.0-alpha.10`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.10)
was published by [run 45058040282](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058040282)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`pending`.
The `alpha` and `latest` tags point to `0.1.0-alpha.10`.

### PyPI

[`tamil-toolkit 0.1.0a10`](https://pypi.org/project/tamil-toolkit/0.1.0a10/)
was published by [run 45013839586](https://github.com/abishtakan/tamil-toolkit/actions/runs/45013839586)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a10-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `pending` |
| Windows wheel `tamil_toolkit-0.1.0a10-cp311-abi3-win_amd64.whl` | `pending` |
| macOS wheel `tamil_toolkit-0.1.0a10-cp311-abi3-macosx_11_0_arm64.whl` | `pending` |
| Source archive `tamil_toolkit-0.1.0a10.tar.gz` | `pending` |

## Compatibility and scope

Pending publication.
