# Alpha 3 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.3`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.3)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.3`; Python `0.1.0a3`.
- Reviewed source commit: `9917a761365dafbaa21a8f0bda2923ad71e712c1`.
- Artifact workflow: [run 41304156907](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304156907), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`. The full gate passed 25 Rust tests, 115 harness tests, 27,644 Rust golden vectors, 27,656 Python cases, 27,654 Vitest cases, and 13 PDF extractor tests. `just release-check` passed isolated Rust, Python, Node, and browser-target WASM package consumers.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API. Each workflow also dry-ran and compared the repackaged crate
against its reviewed archive; only the root `Cargo.lock` difference permitted
by the publishing policy is ignored.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304455588](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304455588) | `ae408710ce430b3e6bdf1a235b618dd2234c2480ca7a1c75b2620a3248e262b2` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304526264](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304526264) | `bb8495cb6c634f4e7c5bde7f0774c410d5b7b06643a91c1f5a7d934a0b0a76fa` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304581785](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304581785) | `1bb7ebf1b86b25e23916e898c8b6f9cf6033c1ecff0ce9151baaf7ad90500f26` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304649088](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304649088) | `6e59b9a0a3f6fcce1503dc338c77a45f252b494f18616deef5f1356426b11421` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304717618](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304717618) | `fa854b10a9b8978df7bc9b37bb7f5ce72017368fb89313136d7f64603e62a28b` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.3) | `0.1.0-alpha.3` | [41304782723](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304782723) | `dadfef0222ef96e36476b7f9cae75a659383009a7697d908ee233b2e9c0bc6b2` |

A fresh Rust consumer downloaded the public crates.io packages and passed all
27,644 active golden rows.

### npm

[`tamil-toolkit@0.1.0-alpha.3`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.3)
was published by [run 41304883796](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304883796)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`681ecc35be5b0c3aae36f44208d63303c07a98dc8feda150511279976b03a018`.
The `alpha` tag points to `0.1.0-alpha.3`; `latest` remains on alpha 1.

A fresh public install on Node 23.11 passed all 27,644 active golden rows
through both the Node and browser-target WASM entry points.

### PyPI

[`tamil-toolkit 0.1.0a3`](https://pypi.org/project/tamil-toolkit/0.1.0a3/)
was published by [run 41304851700](https://github.com/abishtakan/tamil-toolkit/actions/runs/41304851700)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a3-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `b4079bbf2e9aec9e8ef1c0afaa11e0361cac5f02aa30ac9b0f7c7d250ee70ec7` |
| Windows wheel `tamil_toolkit-0.1.0a3-cp311-abi3-win_amd64.whl` | `bf5ab3b73a7ee4f20c76e9a85a89d456eb13cf361055b21ef9e67898b226632a` |
| macOS wheel `tamil_toolkit-0.1.0a3-cp311-abi3-macosx_11_0_arm64.whl` | `56b99350253d99fcef2ab0055f4858efebb71303208ab90f009cf9bdd4619ea5` |
| Source archive `tamil_toolkit-0.1.0a3.tar.gz` | `a2031796d1f66472654fcb4e5fe1e9c68e71a0da0d1061c49675a598dd8e02c0` |

A fresh Windows CPython 3.13.7 environment installed the public PyPI wheel and
passed all 27,644 active golden rows with
[`python_consumer.py`](../../tools/release_smoke/python_consumer.py).

## Compatibility and scope

Alpha 3 adds the bounded LT-TM / IndoWord 16-bit code profile, its reverse
encoder, and shared dispatcher operations. The profile uses a canonical
332-entry mapping with 687 active sourced vectors. See the
[LT-TM contract](../specs/codec-lt-tm.md) for mapping provenance, operation
inputs, fallback, errors, and acceptance limits.

The profile is not an 8-bit decoder. It does not parse PDFs, select PDF font
runs, detect encodings, or claim that every LT-TM or IndoWord font has the same
mapping. Vanavil, AnuGraphics, and Pallavar are not aliases. The private PDF
extraction utility in `tools/tamil-pdf-extract/` is not included in these
packages. Other planned linguistic modules and Dart/Pub distribution remain
outside the alpha release scope.

Tag `v0.1.0-alpha.3` points at the reviewed source commit above.
