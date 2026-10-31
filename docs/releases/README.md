# Alpha release runbook

The first alpha is prepared for https://github.com/abishtakan/tamil-toolkit.
See [scope and acceptance](alpha-1.md). Nothing in `just release-check` uploads,
tags, pushes, or creates accounts. Registry publication is partial: Python is
on PyPI; Rust and npm packages remain unpublished.

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

The six public Rust crate manifests now allow crates.io publishing. The guarded
`publish-crate.yml` workflow publishes one selected crate per manual run after
validating its successful `master` artifact run and archive digest. The
`CARGO_REGISTRY_TOKEN` Actions secret is configured. No Rust crate has been
uploaded yet. The npm package remains private pending its registry setup.

## Build and review

1. Run `just sync-release-files` after canonical lexicon/license changes, then
   `just agent-pre-stop-gate`, `just test-dart`, and the workbench checks.
2. Run `just release-check`. It produces six `.crate` archives, one host abi3
   wheel, a source archive, an npm `.tgz`, and `target/alpha/SHA256SUMS.json`.
   Real consumers outside the checkout run every active golden row. Node and
   browser-target WASM are both executed in Node; interactive browser testing
   is not implied. These local candidate artifacts may describe a dirty tree.
3. Review metadata, licensing, archive contents, supported platforms and changes.
   Commit the reviewed source. Push only when explicitly authorized, then run
   the **Alpha distribution artifacts** workflow with `workflow_dispatch` from
   `master`, setting `source_ref` to `v0.1.0-alpha.1`. It checks out that exact
   tag and records its commit in the Rust artifact. This lets the current
   workflow use supported runners without moving the public release tag. Its
   jobs need no registry credentials. It also runs for matching release tags
   and relevant pull requests.
4. Require the normal CI gate, Rust archive consumer, Rust 1.85 minimum check,
   Node 22/24 archive consumers, and Linux x64/Windows x64/macOS arm64 Python
   artifact jobs and CPython 3.11/3.14 wheel consumers to pass. Linux wheels use
   manylinux2014. Each wheel is built from its own complete source archive.
   Select one identical-version source archive for PyPI; do not upload three
   files with the same distribution filename.

Generated source snapshots are a packaging convenience, not a second Tamil
engine. `just check-unicode` fails on stale copies. Source staging removes unused
workspace members from Python's archive and checks that all retained dependency
versions/checksums still match Cargo.lock. Binary dependency notices come from
that locked Cargo graph. Development/build dependencies can appear in the
notice file conservatively; no test tooling is a Python/npm runtime dependency.

## Registry setup and first upload

After concrete artifact review and explicit authorization to publish:

1. Confirm the intended registry accounts can publish the requested names.
   PyPI's pending trusted publisher is configured for project `tamil-toolkit`,
   owner `abishtakan`, repository `tamil-toolkit`, workflow `publish-pypi.yml`,
   and environment `pypi`. The matching workflow is
   `.github/workflows/publish-pypi.yml`; dispatch it from `master`. It is
   manual-only, defaults to no publication, and accepts only artifacts from a
   successful `Alpha distribution artifacts` run whose source manifest matches
   the `v0.1.0-alpha.1` tag. The GitHub `pypi` environment has a required
   reviewer.
   npm trusted publishing is configured in an existing package's settings, so
   bootstrap its first upload using the maintainer's authenticated npm CLI,
   then configure the workflow. The repository Actions secret
   `CARGO_REGISTRY_TOKEN` is configured for crates.io. Never put credentials in
   this repository or ask for them in plaintext chat.
2. Remove `private: true` only from `bindings/js-wasm/package.json` when npm is
   ready. All placeholder crates, FFI support crates, the workspace root npm
   package, and the workbench remain private. The npm package stays private
   until its upload is reviewed.
3. The `v0.1.0-alpha.1` tag is already used by the PyPI release and must not be
   moved. Rebuild Rust artifacts by dispatching **Alpha distribution artifacts**
   from `master` with `source_ref=master`; the workflow records the exact commit
   used by the crate publisher.
4. Dispatch **Publish Rust crate to crates.io** once per crate from `master`,
   using a successful artifact run from step 3. Review its digest and choose
   `publish`. Publish in order: `tamil-core`, `tamil-norm`, `tamil-collate`,
   `tamil-numerals`, `tamil-codec`, `tamil-toolkit`; allow each crate to appear
   in the registry before publishing dependents. The workflow validates the
   source identity and archive digest and publishes only one allowlisted crate
   per run.
5. PyPI upload is complete (see the status record above). Upload the reviewed
   npm tarball using `npm publish PATH.tgz --tag alpha --access public`. Keep
   stable/default install channels free of this experimental npm alpha.
6. From a fresh consumer, install the exact public versions and run the same
   golden consumer suite. Update the changelog/status only after those installs
   succeed. Record registry links, tag, artifact digests, and CI evidence here.

Public publication cannot be validated solely with local dry runs. Registry
ownership, publisher configuration, and successful remote CI remain separate
requirements. This preparation does not request credentials or perform uploads.

## References

- [Cargo publishing](https://doc.rust-lang.org/cargo/reference/publishing.html)
- [Maturin source builds and wheel portability](https://www.maturin.rs/distribution.html)
- [PyPI pending trusted publishers](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- [npm trusted publisher setup](https://docs.npmjs.com/trusted-publishers/)
