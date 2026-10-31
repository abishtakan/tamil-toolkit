# Alpha 2 release

Status: published to crates.io, PyPI and npm. Immutable tag
[`v0.1.0-alpha.2`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.2)
points to the reviewed source commit below.

## Reviewed source and artifacts

- Release version: Rust/npm `0.1.0-alpha.2`; Python `0.1.0a2`.
- Reviewed source commit: `af11c96ddacd0fedda0cc8c346130a71f924c0b6`.
- Artifact workflow: [run 41237000066](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237000066), successful across Rust, Rust 1.85, Node 22/24, Linux/Windows/macOS wheels, and six Python consumer jobs.
- The later publisher and CI maintenance commits do not change the reviewed release source or its archives.
- Local gates on the reviewed release source passed: full agent gate, Dart, workbench checks/build, release policy and Unicode checks, and `just release-check`. Extracted Rust crates plus isolated Python, Node and browser-target WASM consumers passed all 26,957 active vectors. The lockfile update changed no third-party dependency entries.

The artifact SHA-256 inventory is the workflow's exact `SHA256SUMS.json`:

| Artifact | SHA-256 |
| --- | --- |
| `tamil-core-0.1.0-alpha.2.crate` | `d8811f10b0ce13d3e588f1b39aac94d2eaa506ceb741d3e5ac9c9c5390212a87` |
| `tamil-norm-0.1.0-alpha.2.crate` | `c8e67cf82faaba135bb4d37962a9f07ce643a38a4f5fd0a6e2addcc39e6dba2d` |
| `tamil-collate-0.1.0-alpha.2.crate` | `e4c3bfd60c8776d04b4cbbadc875d17579c3d57df463020f07a2263ad3104923` |
| `tamil-numerals-0.1.0-alpha.2.crate` | `9cd54cc02c17c5d4ef5bd1bb31c465db8a6c6b717bb31b8cace9c03fb6212cf6` |
| `tamil-codec-0.1.0-alpha.2.crate` | `6a4ac8455e3516f016de52b0620f1b73211f985a9cd76ff6110da9e726b2a202` |
| `tamil-toolkit-0.1.0-alpha.2.crate` | `897bcb25ef543b0e9a7676e69e2159b4b2e761a290157f5505e023ce64821b61` |
| `tamil-toolkit-0.1.0-alpha.2.tgz` (Node 22 and 24) | `f88a9425a2b1c9467795681895a3098bec49bf389cf81e12e4252816a45aaae5` |
| Linux wheel `tamil_toolkit-0.1.0a2-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `71438ea9893d24ea28b9e16e201c0c4ce5f372f440e7a5a12ac2f37b1e146e91` |
| Windows wheel `tamil_toolkit-0.1.0a2-cp311-abi3-win_amd64.whl` | `55c05a6c827dbfb2225c0c2b1b86bf0ee3f73afd676fea8ee4c75034c13198a7` |
| macOS wheel `tamil_toolkit-0.1.0a2-cp311-abi3-macosx_11_0_arm64.whl` | `c7ae1eb2491548b3cbd567fb73c1082945c2125b0df83fcae5856b54ddfbfd78` |
| Linux source archive `tamil_toolkit-0.1.0a2.tar.gz` | `1fddee0519ff65a89790b4de08332f7719d3500d5468e1cb5c90a0cf5bb53292` |
| Windows source archive `tamil_toolkit-0.1.0a2.tar.gz` | `037c8e9b9ec2d60f26c6b61ece0b8ddc56b58f8efa2c93f9b3b49f57d7621699` |
| macOS source archive `tamil_toolkit-0.1.0a2.tar.gz` | `1fddee0519ff65a89790b4de08332f7719d3500d5468e1cb5c90a0cf5bb53292` |

## Published registries

### crates.io

All six allowlisted crates are published. Each publisher run passed the reviewed
artifact gate, Cargo dry run, and archive comparison. The downloaded registry
archive for each crate matches the reviewed crate contents; only the root
`Cargo.lock` difference allowed by the publishing policy is ignored.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41237593561](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237593561) | `4151cee7daadceec5c37920a810a471be393ad417a3fdd3fa5acca9e1464afa1` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41237655947](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237655947) | `e6bfcd3d8f3d75abf5b695c48cee0f79eca961c5b398396b69978937038657ab` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41237817058](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237817058) | `9c261c390617db15adf2917ae95c58a5a8d8b10a0f3293f761cbc2a016f2f4e5` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41237927461](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237927461) | `4060e363f762a87522cae2f67575b3d81f98c33e6795ffd42003c496fe3c8e3e` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41237987426](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237987426) | `0d791b3aea65fac5ea3d256366d56ff221b469876bd507146b29a3d09ee13461` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.2) | `0.1.0-alpha.2` | [41238042432](https://github.com/abishtakan/tamil-toolkit/actions/runs/41238042432) | `e464feb86b4d387afce5b34ef7f8b6b4f327ab5fd9735850b10dcce32cf9c927` |

### npm

[`tamil-toolkit@0.1.0-alpha.2`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.2)
was published by [run 41237457340](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237457340)
using the configured OIDC trusted publisher. The public tarball is byte-identical
to the reviewed Node 22 and Node 24 tarballs and has SHA-256
`f88a9425a2b1c9467795681895a3098bec49bf389cf81e12e4252816a45aaae5`. A fresh
public installation on Node 23.11 passed all 26,957 active vectors through
both Node and browser-target WASM entry points. The `alpha` tag points to
`0.1.0-alpha.2`; `latest` remains on alpha 1.

### PyPI

[`tamil-toolkit 0.1.0a2`](https://pypi.org/project/tamil-toolkit/0.1.0a2/)
was published by [run 41237423572](https://github.com/abishtakan/tamil-toolkit/actions/runs/41237423572)
through the configured OIDC publisher and required `pypi` reviewer. All four
published files match the reviewed artifacts:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a2-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `71438ea9893d24ea28b9e16e201c0c4ce5f372f440e7a5a12ac2f37b1e146e91` |
| Windows wheel `tamil_toolkit-0.1.0a2-cp311-abi3-win_amd64.whl` | `55c05a6c827dbfb2225c0c2b1b86bf0ee3f73afd676fea8ee4c75034c13198a7` |
| macOS wheel `tamil_toolkit-0.1.0a2-cp311-abi3-macosx_11_0_arm64.whl` | `c7ae1eb2491548b3cbd567fb73c1082945c2125b0df83fcae5856b54ddfbfd78` |
| Source archive `tamil_toolkit-0.1.0a2.tar.gz` | `1fddee0519ff65a89790b4de08332f7719d3500d5468e1cb5c90a0cf5bb53292` |

A fresh Windows CPython 3.13.7 environment installed the package from PyPI and
passed all 26,957 active golden rows with
[`python_consumer.py`](../../tools/release_smoke/python_consumer.py).

## Compatibility and scope

The alpha adds bounded TSCII, TAB, TAM, and Anjal byte conversion. TAM is
monolingual: Latin letter byte positions represent Tamil glyphs. Anjal reports
four ambiguous byte values and rejects a source glyph without an agreed byte
mapping. Inputs outside the declared profiles return errors; these APIs do not
claim complete support for historical font variants or automatic detection.
No prior public Bamini behavior was intentionally changed.

Dart/Pub.dev, PostgreSQL, and unfinished crates remain outside this release.
Tag `v0.1.0-alpha.2` is pushed and points at the reviewed source commit above.
