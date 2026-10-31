# Alpha release runbook

The first alpha release record for https://github.com/abishtakan/tamil-toolkit.
See [scope and acceptance](alpha-1.md). Nothing in `just release-check` uploads,
tags, pushes, or creates accounts. The Python, Rust, and npm alpha packages are
published.

## Alpha 1 publication status

- PyPI: [`tamil-toolkit 0.1.0a1`](https://pypi.org/project/tamil-toolkit/0.1.0a1/)
  published on 2026-10-31 with three platform wheels and one source archive.
- Source: tag `v0.1.0-alpha.1`, commit
  `9cd7ae3494090273bca07ab089d8cca786df5a4a`.
- Artifact workflow: [run 41210386284](https://github.com/abishtakan/tamil-toolkit/actions/runs/41210386284)
  passed all Rust, npm, Python wheel, and consumer jobs.
- PyPI upload: [run 41210795966](https://github.com/abishtakan/tamil-toolkit/actions/runs/41210795966)
  succeeded through the `pypi` trusted publisher and required-reviewer gate.
- Public consumer check: CPython 3.13.7 on Windows installed the wheel from
  PyPI and passed all 21,277 active golden rows.
- SHA-256 digests from PyPI's simple index:

  | File | SHA-256 |
  | --- | --- |
  | `tamil_toolkit-0.1.0a1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl` | `f742413074dd2e2b533f934d65c1b95142e47899f88271d95ff064289b75de27` |
  | `tamil_toolkit-0.1.0a1-cp311-abi3-win_amd64.whl` | `9835cae3e702711e543cc0065958ae70a7f8d89d4987226706e75fd51ac9c477` |
  | `tamil_toolkit-0.1.0a1-cp311-abi3-macosx_11_0_arm64.whl` | `aa96211e50dd460eba50b626dd3591a34ebeb380957e6efa0363029c6ea173ce` |
  | `tamil_toolkit-0.1.0a1.tar.gz` | `601974e24b3c3c45fe1160d8187a473ec30c0696b7c8cb621f2edc14611a7d5d` |

The six finished Rust crates were published on crates.io from reviewed source
commit `60765b24e5d7826460dc3be3836ebdcc71816461`. Their successful publishing
workflow runs and registry checksums are recorded below. The local artifact
archives were built with temporary `[patch.crates-io]` entries for package
verification; Cargo regenerated the upload archives without those local
patches. Comparison with crates.io downloads showed that only the embedded
`Cargo.lock` differs.

| Crate | crates.io | Publish run | Registry archive SHA-256 |
| --- | --- | --- | --- |
| `tamil-core` | [0.1.0-alpha.1](https://crates.io/crates/tamil-core/0.1.0-alpha.1) | [41211949196](https://github.com/abishtakan/tamil-toolkit/actions/runs/41211949196) | `3fe1cbc7434b413e0fa30251970e535676dd2bbee487c43295997fd9c672d993` |
| `tamil-norm` | [0.1.0-alpha.1](https://crates.io/crates/tamil-norm/0.1.0-alpha.1) | [41212014986](https://github.com/abishtakan/tamil-toolkit/actions/runs/41212014986) | `dc96dbe271c7d9506e019db7aa24e977edf84b25162605ba36130bd3315ced69` |
| `tamil-collate` | [0.1.0-alpha.1](https://crates.io/crates/tamil-collate/0.1.0-alpha.1) | [41212070399](https://github.com/abishtakan/tamil-toolkit/actions/runs/41212070399) | `ac49c38ca09f31972934d9099e9e3efc96990326eae800c563274a586987df3e` |
| `tamil-numerals` | [0.1.0-alpha.1](https://crates.io/crates/tamil-numerals/0.1.0-alpha.1) | [41212121785](https://github.com/abishtakan/tamil-toolkit/actions/runs/41212121785) | `1d1c1d47ea28928d8f6dd6da5a9fb334176f088182628bc8aa016592b89e0107` |
| `tamil-codec` | [0.1.0-alpha.1](https://crates.io/crates/tamil-codec/0.1.0-alpha.1) | [41212174436](https://github.com/abishtakan/tamil-toolkit/actions/runs/41212174436) | `0b851e13bcd786280c6f7b1e70187d5cc4baa192fdf787aee6bf963217bb7812` |
| `tamil-toolkit` | [0.1.0-alpha.1](https://crates.io/crates/tamil-toolkit/0.1.0-alpha.1) | [41212755732](https://github.com/abishtakan/tamil-toolkit/actions/runs/41212755732) | `a63cb34afa8dbb411c313eb498897adf61b7bd739170ea685dfb31490e8cfdbf` |

The npm package [`tamil-toolkit 0.1.0-alpha.1`](https://www.npmjs.com/package/tamil-toolkit/v/0.1.0-alpha.1)
was published on 2026-10-31. Its tarball was built from source commit
`403bcfca0b312d1c9a2188e271c1dc760d9725f6` in [artifact run
41213495093](https://github.com/abishtakan/tamil-toolkit/actions/runs/41213495093).
Node 22 and Node 24 produced byte-identical tarballs; the reviewed and registry
tarball SHA-256 is
`0018c5451da8330e5fa2f45b54112e2dc832138c963523b34c7229c31b51d1d9`. A fresh
consumer installed the public version and passed all 21,277 active golden rows
through both Node and browser-target WASM entry points. The current `alpha` and
`latest` dist-tags both resolve to `0.1.0-alpha.1`. The initial publication used
an authenticated maintainer CLI and interactive OTP; npm trusted publishing is
not yet configured for future releases.


## Future releases

The reusable [publishing policy](policy.md) owns versioning, local and remote
gates, source review, package allowlists, account configuration, upload order,
and partial-release recovery. The first-alpha evidence above is historical;
do not reuse its already published versions or move its existing tag.

Start with `just release-status` and `just check-release-policy`. Development
continues at the current version until a release batch is chosen. The expensive
**Alpha distribution artifacts** workflow is manual-only: dispatch it from
master with the full reviewed commit as `source_ref`. All jobs resolve that
same immutable SHA and attach release identity plus SHA-256 inventory.

Future publishers require `artifact_run_id`, the full reviewed `source_sha`,
and `confirm_publish=publish`; Rust also requires the approved `package`.
They reject artifacts from failed, PR, fork, or non-master dispatch runs, and
check source identity, versions, scope, and archive hashes. Artifacts from the
first-alpha harness lack the new source metadata and cannot be reused by
these gates. Publishing is an explicit release action under existing session
authorization; ordinary commits, pushes, and tags do not upload.

The publishing workflow filenames are durable account configuration:

| Registry | Workflow | Authentication |
| --- | --- | --- |
| crates.io | `publish-crate.yml` | Existing Actions secret `CARGO_REGISTRY_TOKEN` |
| PyPI | `publish-pypi.yml` | Trusted publisher; project `tamil-toolkit`, GitHub owner/repo `abishtakan/tamil-toolkit`, environment `pypi` with required reviewer |
| npm | `publish-npm.yml` | OIDC workflow prepared; package trusted publisher configuration remains deferred until the next version is ready |

For npm, select GitHub Actions, owner `abishtakan`, repository `tamil-toolkit`,
workflow `publish-npm.yml`, blank environment, and permit direct `npm publish`.
Complete its first successful OIDC publication within two days of setup.
No npm/PyPI token is required in GitHub. Never place credential values in this
record, source, logs, or chat.

Pub.dev/Dart distribution and PostgreSQL remain deferred. See
[current handoff](../status.md) and [development workflow](../development.md)
before starting the next feature.
