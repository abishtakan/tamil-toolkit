# Alpha 4 release

Status: published to crates.io, PyPI, and npm. Immutable tag
[`v0.1.0-alpha.4`](https://github.com/abishtakan/tamil-toolkit/tree/v0.1.0-alpha.4)
points to the reviewed release source.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.4`; Python `0.1.0a4`.
- Reviewed source commit: `252aaed369e0122e7b123bb7aa3c76a2ce64208d`.
- Artifact workflow: [run 41319153698](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319153698), successful for Rust, the Rust 1.85 minimum, Node 22 and 24, Linux/Windows/macOS wheels, and six CPython 3.11/3.14 consumer jobs.
- The artifact run's `release-source.json` and SHA-256 manifests bind the Rust, npm, and Python artifacts to the same source SHA, version, channel, and crate allowlist.
- Local release checks passed: `just check-release-policy`, `just check-unicode`, `just sync-release-files`, `just check-release-files`, `just agent-post-edit`, `just agent-pre-stop-gate`, `just test-dart`, and `just release-check`.

## Published registries

### crates.io

Each approved crate was uploaded from its own successful publisher workflow,
in dependency order. Registry checksums are the SHA-256 values returned by the
crates.io API.

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `08515b409b5c30d639782d48153cc238ba0b269a67e050fcb96edde2ff326973` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `7b10c9ce2ea7c28ffded20ed3e32795ab7e66a28b48958cb3c4e5b8225c899a4` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `a6edd7145889528d58a7025b7636ed2ecea7e6ed69597e9e8b2f076e2ef4adbd` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `fcb8f219e2740eb6c805811594743d66d95298c70c94e21d7671ee5251ba0f36` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `9e14e28ce76ca24e40e1ef8850b999a28fc4dae490201d0fbafee79af2c1bcdf` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.4) | `0.1.0-alpha.4` | [41319360003](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319360003) | `7fb0c86ac77481d5e0a9e77ccacfcc032dcfebed467a8d37d9305bcba150eb98` |

### npm

[`tamil-toolkit@0.1.0-alpha.4`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.4)
was published by [run 41319499023](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319499023)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`01bf7f06fd97380f99541cd6b403e9dccaf8d37b3f59da7c84581abe9094dd6f`.
The `alpha` tag points to `0.1.0-alpha.4`; `latest` remains on alpha 1.

### PyPI

[`tamil-toolkit 0.1.0a4`](https://pypi.org/project/tamil-toolkit/0.1.0a4/)
was published by [run 41319502255](https://github.com/abishtakan/tamil-toolkit/actions/runs/41319502255)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a4-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `c386e879c6d93429212327f632fb5824b03fe45239216d63e73556c82dc9d28e` |
| Windows wheel `tamil_toolkit-0.1.0a4-cp311-abi3-win_amd64.whl` | `a0831bc03624937623cdc7f26d5ffe4b78555da84e747952c216c7d5107dc2cd` |
| macOS wheel `tamil_toolkit-0.1.0a4-cp311-abi3-macosx_11_0_arm64.whl` | `da6eda9966a64dda765774fa2e1751620e8ffb9c83a91f4d91e151dcde28bc7d` |
| Source archive `tamil_toolkit-0.1.0a4.tar.gz` | `26e356ee13b0d0cc720df5c3283ba289b8c97c5b50479a6e59dc905428760025` |

## Compatibility and scope

Alpha 4 adds the bounded `Vanavil Avvaiyar` (`vanavil-avvaiyar-cid-v1`) 16-bit
code/CID profile (`vanavil_codes_to_unicode`, `vanavil_text_to_unicode`,
`unicode_to_vanavil_codes`, `unicode_to_vanavil_text`), its canonical
319-entry mapping table, and 661 active sourced golden vectors across Rust,
Python, WASM, and Dart, bringing the active golden corpus to 28,305 rows. See
the [Vanavil contract](../specs/codec-vanavil.md) for mapping provenance,
divergences from LT-TM (`0x00C0..0x00CF` / `0x00E0..0x00EF` transposition,
`0x00B7 -> U+0BFA`, and absence of `ஶ`), operation inputs, fallback, errors,
and acceptance limits.

Like LT-TM, `vanavil-avvaiyar-cid-v1` is a 16-bit code/CID profile rather than
an 8-bit byte decoder. It does not parse PDFs, select PDF font runs, detect
encodings automatically, or claim that every `Vanavil` font family shares the
same layout. Other planned linguistic modules and Dart/Pub distribution remain
outside the alpha release scope.

Tag `v0.1.0-alpha.4` points at the reviewed source commit above.
