# Alpha 4 release

Status: pending publication.

## Reviewed source and artifact matrix

- Release version: Rust/npm `0.1.0-alpha.4`; Python `0.1.0a4`.
- Reviewed source commit: pending.
- Artifact workflow: pending.
- Local release checks passed: pending.

## Published registries

### crates.io

| Crate | Version | Publisher run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| [`tamil-core`](https://crates.io/crates/tamil-core/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |
| [`tamil-norm`](https://crates.io/crates/tamil-norm/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |
| [`tamil-collate`](https://crates.io/crates/tamil-collate/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |
| [`tamil-numerals`](https://crates.io/crates/tamil-numerals/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |
| [`tamil-codec`](https://crates.io/crates/tamil-codec/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |
| [`tamil-toolkit`](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.4) | `0.1.0-alpha.4` | pending | pending |

### npm

[`tamil-toolkit@0.1.0-alpha.4`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.4)

### PyPI

[`tamil-toolkit 0.1.0a4`](https://pypi.org/project/tamil-toolkit/0.1.0a4/)

| File | SHA-256 |
| --- | --- |
| Linux wheel `tamil_toolkit-0.1.0a4-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | pending |
| Windows wheel `tamil_toolkit-0.1.0a4-cp311-abi3-win_amd64.whl` | pending |
| macOS wheel `tamil_toolkit-0.1.0a4-cp311-abi3-macosx_11_0_arm64.whl` | pending |
| Source archive `tamil_toolkit-0.1.0a4.tar.gz` | pending |

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
