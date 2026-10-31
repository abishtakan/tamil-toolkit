# Alpha release runbook

The first alpha is prepared for https://github.com/abishtakan/tamil-toolkit.
See [scope and acceptance](alpha-1.md). Nothing in `just release-check` uploads,
tags, pushes, or creates accounts. Package publication is still disabled.

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
   the **Alpha distribution artifacts** workflow using `workflow_dispatch`.
   Its jobs need no registry credentials. It also runs for matching release
   tags and relevant pull requests.
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
   Configure PyPI's pending trusted publisher with project name
   `tamil-toolkit`, owner `abishtakan`, repository `tamil-toolkit`, workflow
   `publish-pypi.yml`, and environment `pypi`. The matching workflow is
   `.github/workflows/publish-pypi.yml`; dispatch it from `master`. It is
   manual-only, defaults to no publication, and accepts only artifacts from a
   successful `Alpha distribution artifacts` run for `v0.1.0-alpha.1`.
   Configure the GitHub `pypi` environment with required reviewers before
   publishing.
   npm trusted publishing is configured in an existing package's settings, so
   bootstrap its first upload using the maintainer's authenticated npm CLI,
   then configure the workflow. Configure crates.io authentication for the
   maintainer as well. Never put credentials in this repository or ask for
   them in plaintext chat.
2. Enable publishing only in the six public Rust manifests from `alpha-1.md`
   (`publish = ["crates-io"]`, overriding the workspace default). Remove
   `private: true` only from `bindings/js-wasm/package.json`. All placeholder
   crates, FFI support crates, the workspace root npm package, and the workbench
   remain private. These switches are deliberately still off in preparation.
3. Rebuild and review artifacts from that exact committed source. Create the
   `v0.1.0-alpha.1` tag only for the reviewed commit and require its CI checks.
4. Publish Rust packages in order: `tamil-core`, `tamil-norm`, `tamil-collate`,
   `tamil-numerals`, `tamil-codec`, `tamil-toolkit`. Run `cargo publish --locked
   -p NAME` for each without local patches; wait for registry availability
   before publishing dependents. The local alpha archive patches only bootstrap
   pre-publication checks and must not be used for the actual registry upload.
5. Upload the reviewed Python wheels and one source archive to PyPI. Upload the
   reviewed npm tarball using `npm publish PATH.tgz --tag alpha --access public`.
   Keep stable/default install channels free of this experimental npm alpha.
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
