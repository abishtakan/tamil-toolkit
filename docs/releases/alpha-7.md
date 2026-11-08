# Alpha 7 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.7`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.7)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.7`; Python `0.1.0a7`.
- Reviewed source commit: `1cfa1c8cd76301651ffc218fa10a041524e3ef45`.
- Artifact workflow: [run 42478611671](https://github.com/abishtakan/tamil-toolkit/actions/runs/42478611671), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `6e75c219738afac7e00a0f5b2790f58b203650acec930e739776f714269686ef` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `8c188a48335f22555c7fb13c860490d25a76ebf14e37f6f5e9204e344cbaf95a` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `58bacc23b58e33337c68adf2f04fd06ffb555df1f7826f16a6a0a71db5f404da` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `933a4d86605a4c6f8252b1bd8de9b8c5cc0aaf2c42042aa7291a8828f483106d` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `75ce5047c41b11721c57c7fc70bd807cb98e380b337db54d6ebdfa25bd3cccd8` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `cd37730f6e62783422aebc12125d6962a07e64f18e91c0843ed7dc0a3c538ea6` |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `c57b80e0bd07ad8fbf17014f7a4c9c891cf0222b97d45f2aec1f9de237a02799` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.7) | `0.1.0-alpha.7` | [42479221917](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479221917) | `f08397983fda3bea88aeec545d7aadfeb7f6c760b134febc1178a448f5d641cb` |

### npm

[`tamil-toolkit@0.1.0-alpha.7`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.7)
was published by [run 42479314447](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479314447)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`babd09774ad4c9e8285219a3c137ebfeb9f70ce2f3d7e330f2305bfc635e6340`.
The `alpha` and `latest` tags point to `0.1.0-alpha.7`.

### PyPI

[`tamil-toolkit 0.1.0a7`](https://pypi.org/project/tamil-toolkit/0.1.0a7/)
was published by [run 42479359576](https://github.com/abishtakan/tamil-toolkit/actions/runs/42479359576)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a7-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `bc23f81670b3779f77d20eba21472564fba66d4993090d8702083293a537d37a` |
| Windows wheel `tamil_toolkit-0.1.0a7-cp311-abi3-win_amd64.whl` | `0adeb6ddac341145a23c48b12942fb4e8bbabf028939e6a2ca02e08f8ead070a` |
| macOS wheel `tamil_toolkit-0.1.0a7-cp311-abi3-macosx_11_0_arm64.whl` | `fdc1410f30206edbaaeb2fe43bb7d03a58eff64d9d69d34f5173359283ed2828` |
| Source archive `tamil_toolkit-0.1.0a7.tar.gz` | `a0ff24e50674b43e340a251be9e2b4fb08619eb1c8f18ad87485dcbf4ff356ff` |

## Compatibility and scope

Pending publication.
