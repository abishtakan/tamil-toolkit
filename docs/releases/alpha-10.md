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
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `427d89860b89e3351b35ef6f187a0dd4a4e67825040fa137a3b32846d1d3e1f4` |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `668e8c14eea59877963650cc8abefc6a06a02259d14d7a53cda7dc37dac713a5` |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `a0d62acbab85399870a88b4f9c775c7780c8e8926fa8cd6a18e7289b52feea93` |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `147a7b89a9e5ae89596a7a024021714616b87d93dfae551958908d36c7e17217` |
| [`tamil-calendar`](https://crates.io/crates/tamil-calendar/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `f9b7fee797963624b634afb52a390e86cd4285ff9628d0ce08c31d3c83e83014` |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `44f3e99be2af81a2c6b256ad715c91192ec911233277de0105228481740b6eb9` |
| [`tamil-hyphen`](https://crates.io/crates/tamil-hyphen/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `2e35d8b71ed4ea36eacb51d343e0717c9790efe93fb37b35ebe23132970f2a8c` |
| [`tamil-translit`](https://crates.io/crates/tamil-translit/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `5b6a7304656cf5f7f574f50e3faf9f9f5903d2e8dcc400b3ffb51e6bbc9e22bd` |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.10) | `0.1.0-alpha.10` | [45058020552](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058020552) | `7120cd84bcd7d8c9f744f9f8ec2ae2c170b95e63a80e9b2965b1f6e6f379b636` |

### npm

[`tamil-toolkit@0.1.0-alpha.10`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.10)
was published by [run 45058040282](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058040282)
using the configured OIDC trusted publisher. The published tarball matches the
reviewed Node 22 and Node 24 tarballs byte for byte; SHA-256:
`113b88d7b42db841b1b712cac5b26c4744f4e6ba0787c41932ec2bdb9b8a77f4`.
The `alpha` and `latest` tags point to `0.1.0-alpha.10`.

### PyPI

[`tamil-toolkit 0.1.0a10`](https://pypi.org/project/tamil-toolkit/0.1.0a10/)
was published by [run 45058060092](https://github.com/abishtakan/tamil-toolkit/actions/runs/45058060092)
through the configured OIDC publisher and required `pypi` reviewer. PyPI's
four public file digests match the reviewed build:

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a10-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `38364f17f902cbdba0f0115b8e7b7b21cbce0051de44e1f6ce6e659d29959e54` |
| Windows wheel `tamil_toolkit-0.1.0a10-cp311-abi3-win_amd64.whl` | `fa2e08c9d8071ecb17d49f63fd459abf48911f8c4d48dc3893751e633b742cc9` |
| macOS wheel `tamil_toolkit-0.1.0a10-cp311-abi3-macosx_11_0_arm64.whl` | `911ca8d63f9bc53165f1ddcd472d6b53688577c8f79d1f8369f3618035a9d972` |
| Source archive `tamil_toolkit-0.1.0a10.tar.gz` | `13f0c24daae9fbf4d73ceb21a5517a4ea70d50db3748ba82ba225ab636982137` |

## Compatibility and scope

- Synchronized workspace release `0.1.0-alpha.10` (PyPI `0.1.0a10`) from commit `ba4fa913bf327157323eeb7f8975e4f39b29224a`.
- Adds `transliterate_suggest` (`crates/tamil-translit`, `crates/tamil-toolkit`, `bindings/js-wasm`, `bindings/python`, `bindings/dart-flutter`) with phonotactically valid Mayangoli (`ன/ண`, `ல/ள/ழ`, `ர/ற`) candidate generation and Google Input Tools / Microsoft Indic Phonetic keyboard cycling across the Browser Extension (`integrations/browser-extension/`) and Microsoft Word Add-in (`integrations/office-word-addin/`).
- Includes declarative Anjal (`anjal-phonetic`) vs. Tanglish (`phonetic-v1`) input table separation (`lexicon/translit.toml`), visual-kombu repair false-positive fix (`tamil-norm`), and Chrome/Edge & Firefox MV3 Browser Extension packages.
- All 9 approved `crates.io` crates remain slim Apache-2.0 engine packages (< 10 MiB) backed by 40,211 active golden vectors (`tests/golden/translit_v01.jsonl` has 570 vectors).
