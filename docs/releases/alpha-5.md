# Alpha 5 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.5`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.5)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.5`; Python `0.1.0a5`.
- Reviewed source commit: `147ade2f1b0579200c2d222c9546c85a5e56b258`.
- Artifact workflow: [run 41409101149](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409101149), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local verification: check-release-policy, check-unicode, sync-release-files, check-release-files, agent-post-edit, test-dart, and release-check passed. The initial full agent gate retained a stale convenience assertion for the deferred Krishna Jayanthi event; the assertion was corrected and its focused rerun passed. See the candidate record for the full gate history.

## Published registries

### crates.io

All six approved crates were uploaded in dependency order by
[publisher run 41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856).
Registry checksums are the SHA-256 values returned by the crates.io API.
Each downloaded registry archive has the same file inventory and contents as
its reviewed CI crate except Cargo.lock, the only difference permitted by the
publisher's repackage comparison.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `ed3ec4ded15e6a2a02b4304577da513f1ea79deec9e6f151ad753d395629c4f3` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `274baad51f72a2604c42c2ece24add77fae5f2bb40770da2ac8492573d10035d` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `23ec11ea0de1a2286879d6165315a3a94ca46b37e6a4ca40f8cd5d605ec2c8cd` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `dd057d94a92b46339afd6078f68685caf27b89a38e4e4825a53ff2b19d030a5f` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `9b105db339cd15d8cafe863597320028f4407e02f17b3def89b86d076fd9d0af` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.5) | `0.1.0-alpha.5` | [41409938856](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409938856) | `f3903a7b0f97b516ae9f46eacdbe2c4c23bf8e5f28c3713cf68a23e638ee0709` |

### npm

[`tamil-toolkit@0.1.0-alpha.5`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.5)
was published by [run 41409955005](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409955005)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`32eac3d5c10328024a046d132d4d252f112649cfe06650827190156abb23e55e`.
The `alpha` tag points to `0.1.0-alpha.5`; `latest` remains on alpha 1.

### PyPI

[`tamil-toolkit 0.1.0a5`](https://pypi.org/project/tamil-toolkit/0.1.0a5/)
was published by [run 41409963577](https://github.com/abishtakan/tamil-toolkit/actions/runs/41409963577)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a5-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `c102d2038870aef527e1075c18f8856d3be21465554abfef6eea76e67bdc2b0b` |
| Windows wheel `tamil_toolkit-0.1.0a5-cp311-abi3-win_amd64.whl` | `55eb1226d58d9b9d1e6ff475df90d9398eece1118209e3b4c19a9173cfea9768` |
| macOS wheel `tamil_toolkit-0.1.0a5-cp311-abi3-macosx_11_0_arm64.whl` | `a267aaa3840b0f155ef5291c23bff7c035c8436060efbf4c6dd5ac3bd6e0751b` |
| Source archive `tamil_toolkit-0.1.0a5.tar.gz` | `0b10494b5d51f7451927d19c97230e386256cddfc929b5b4ad3413ebe3dbfc17` |

## Fresh public consumers

New isolated consumers installed the published packages from the public
registries and passed the unchanged 35,646 active golden rows:

- Rust consumer: Cargo resolved the six published 0.1.0-alpha.5 crates from
  crates.io; all 35,646 rows passed.
- Python consumer: Python 3.14.6 installed tamil-toolkit 0.1.0a5 from PyPI;
  all 35,646 rows passed.
- npm consumer: Node v23.11.0 installed tamil-toolkit 0.1.0-alpha.5 from npm;
  all 35,646 rows passed through both Node and browser-target WASM exports.

## Compatibility and scope

Numeric v0.3 remains approved with 35,646 active vectors. The release also
contains bounded, source-limited experimental calendar APIs; all 225 calendar
review vectors remain planned and no calendar suite was activated. Krishna
Jayanthi remains deferred because its annual festival-month selector lacks a
sourced contract. Broader calendar completeness and independent selector
review remain open; see the
[numerals/calendar candidate scope](numerals-calendar-candidate.md).
