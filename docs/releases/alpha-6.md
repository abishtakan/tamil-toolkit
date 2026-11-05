# Alpha 6 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.6`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.6)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.6`; Python `0.1.0a6`.
- Reviewed source commit: `f8ab0a600b37b7ec10120ada5026db5762c9efc5`.
- Artifact workflow: [run 41998968411](https://github.com/abishtakan/tamil-toolkit/actions/runs/41998968411), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `fe63f87af7e11c86445e47b40edc97f0b554669c7040ab50cb5972fd04b291a6` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `9d9259f20eddbda78c3ad33af5f666f2027db0b8facc44620fc94c79dba32577` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `05daa8823c43b5d89704f6dfbae748b53a15b3cc398581335087b13e0fd50fed` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `2b2ff2fe244689c900f8be4e80d4e727b8ccbbfd6bf99fe8c75a0018876b3f5e` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `85b3e84b6dff4412a0757c9be35397f308bcde9794f5f69405d1201c9383717d` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `2147c47dab09efd6cba0025e8214bded94ce1bfc0c24e18d5c40c3b77e92dee8` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.6) | `0.1.0-alpha.6` | [41999652375](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999652375) | `8427d9e8cc61fef3b97d6e045cd3eab69f08dc97150da57c4d5f9d0a7d8653a7` |

### npm

[`tamil-toolkit@0.1.0-alpha.6`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.6)
was published by [run 41999812379](https://github.com/abishtakan/tamil-toolkit/actions/runs/41999812379)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`1d50e886fcbb0dbb61b6d90db730a04dda471151f81f61f30070372b95bdc09f`.
The `alpha` and `latest` tags point to `0.1.0-alpha.6`.

### PyPI

[`tamil-toolkit 0.1.0a6`](https://pypi.org/project/tamil-toolkit/0.1.0a6/)
was published by [run 42000175759](https://github.com/abishtakan/tamil-toolkit/actions/runs/42000175759)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a6-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `d0880314611f8260d200ab6ab3982ce1cb0890b25523cc85ff9efbc7bb79a2bd` |
| Windows wheel `tamil_toolkit-0.1.0a6-cp311-abi3-win_amd64.whl` | `9ae5cfba9c4cbc7d2975910c21cad1230e9a4e4bd00e67ee42ee14b16b119cd3` |
| macOS wheel `tamil_toolkit-0.1.0a6-cp311-abi3-macosx_11_0_arm64.whl` | `3564fc6d109260640dc625152a4857d28f28c04be09d4737b012a277a8add6b6` |
| Source archive `tamil_toolkit-0.1.0a6.tar.gz` | `21fcd08dc53ac262038575f170850fa687b9c615a48458fb7a81af25d76bf888` |

## Compatibility and scope

Release 0.1.0-alpha.6 stabilizes the autonomous release workflow, aligns all seven workspace crates on crates.io (including `tamil-calendar` with activated year cycle golden vectors), publishes TypeScript/WASM bindings (`tamil-toolkit@0.1.0-alpha.6`) to npm, and publishes multi-platform Python 3.11+ abi3 wheels and sdist (`tamil_toolkit-0.1.0a6`) to PyPI. All golden test suites and consumer verification jobs passed across Rust, Node, and Python.
