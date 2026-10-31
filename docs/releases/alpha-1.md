# First public alpha: 0.1.0-alpha.1

Status: local preparation verified; remote CI, release review, and registry
publication remain pending. No registry upload has been performed.

Repository: https://github.com/abishtakan/tamil-toolkit

## Scope and versions

Publish these Rust packages, in dependency order: `tamil-core`, `tamil-norm`,
`tamil-collate`, `tamil-numerals`, `tamil-codec`, and `tamil-toolkit`.
Rust and npm use `0.1.0-alpha.1`; Python uses its equivalent PEP 440 version
`0.1.0a1`. npm uses the `alpha` dist-tag. These are experimental APIs.

The umbrella exposes Unicode/Ezhuthu primitives, normalization, Agara collation,
bounded TN/SL integer and currency words, exact fractions, Gregorian date
formatting, and explicit Bamini conversion. The existing module specifications
define the actual guarantees. There is no new linguistic behavior in this
release preparation, so existing golden vectors remain unchanged.

Do not publish placeholder crates, Rust FFI support crates, Dart, or PostgreSQL.
The Dart adapter remains available for host development. Other encodings,
Punarchi, morphology, dialect normalization, hyphenation, and prosody remain
planned. Removing placeholder re-exports is acceptable before the first public
version; implemented APIs must remain unchanged.

## Licensing and source packaging

Original project code is MIT licensed, copyright 2026 tamil-toolkit contributors.
Contributions use the same license. Upstream Unicode/CLDR and Bamini notices
retain their original licenses and attribution; MIT does not replace them.
Each distributed artifact must contain the project license and applicable
third-party notices.

`lexicon/*.toml` remains the canonical declarative source. Published crates need
their build inputs inside their own archives. Generated per-crate copies are
permitted only when byte-for-byte checked against the canonical files by the
normal verification gate. This small duplication avoids a new public data crate
or a network dependency in build scripts. Never edit the generated copies.

## Acceptance criteria

1. All six public Rust crates have consistent prerelease versions, MIT metadata,
   repository/documentation links, README files, and bundled declarative inputs.
   Unimplemented crates remain unpublished and are not umbrella dependencies.
2. Cargo produces actual `.crate` archives. A consumer outside the checkout
   builds the extracted archives with local patches only for these unpublished
   sibling crates. No checkout-relative lexicon or source path is available.
   All active golden rows run through that consumer's real dispatcher.
3. Maturin produces a Python wheel and complete source distribution. A fresh
   environment outside the checkout installs a wheel rebuilt from that source
   archive, imports the native extension and typing files, and executes every
   active golden row. PyPI builds target GIL-enabled CPython 3.11+ on Windows x64, Linux x64
   with a compliant manylinux baseline, and macOS arm64. CI must verify the
   artifacts on each advertised platform before upload.
4. npm packs production Node and browser WASM, JavaScript entry points, and
   TypeScript declarations into one tarball. An isolated consumer installs it,
   type-checks public imports, and executes every active golden row through
   both entry points. Browser-target WASM execution in Node is distinguished
   from interactive browser testing.
5. Version, archive-content, canonical-data, license, and release-scope checks
   fail on drift. Existing formatting, clippy, Unicode/schema, Rust properties,
   harness, binding parity, Dart, and workbench checks remain passing.
6. CI builds and uploads reviewable artifacts without registry credentials.
   Publishing is a separate explicit action using a reviewed release tag and
   registry credentials or trusted publisher configuration. No secret is stored
   in source, artifacts, or logs. Initial uploads are ordered Rust dependencies
   first, then Python/npm. All archives are tested before any upload.

## Release review and handoff

Record commands, artifact digests, local/CI evidence, supported platforms, and
any incomplete registry/account configuration here before the first upload.
Local Windows proof does not imply that Linux/macOS CI has passed. Public names
were not found by the initial registry checks; final registry acceptance and
ownership are only established by successful publication.

Release preparation does not create a release tag, push commits, or upload a
package. The first upload must follow the concrete artifact review.

## Primary references

- [Cargo package verification](https://doc.rust-lang.org/cargo/commands/cargo-package.html)
- [Maturin wheel and source distribution](https://www.maturin.rs/distribution.html)
- [PyPI trusted publishers](https://docs.pypi.org/trusted-publishers/)
- [npm trusted publishing](https://docs.npmjs.com/trusted-publishers/)
- [MIT license](https://opensource.org/license/mit)

## Local acceptance results (2026-10-31)

The full `just agent-pre-stop-gate` passed on Windows/MSVC with Rust 1.95.0:
formatting, Unicode/schema/source-copy validation, locked workspace checking,
clippy with denied warnings, 21 Rust tests, doctests, and 67 harness tests.
The existing seventeen 10,000-case properties remain active (170,000 cases).
Python reported 21,285 passing tests; Vitest reported 21,283, exercising both
WASM entry points. `just test-dart` passed analysis and 21,283 tests.

The final `just release-check` produced nine candidate archives under
`target/alpha/`: six `.crate` files, the Windows x64 cp311-abi3 wheel, its
complete source archive, and the npm tarball. The exact outgoing wheel is
rebuilt from an extracted source archive before installation. Each external
Rust, Python, Node WASM, and browser-target WASM consumer passed all **21,277**
active golden rows, including exact errors. TypeScript checked the installed
declarations with strict checking and without skipping library checks.
The same final wheel also passed all rows in a fresh CPython **3.11.15**
environment; the main consumer used CPython **3.14**. The Node consumers used
the locally available Node **23.11.0**; CI covers the advertised Node 22/24.

`cargo +1.85.0 check --locked -p tamil-toolkit --lib` passed against the declared
minimum Rust version. Workbench type checking and its production bundle passed.
The workbench now refreshes canonical data copies before browser WASM rebuilds;
Python development builds generate dependency notices before packaging.
Actionlint **1.7.12** validated both workflows. Distribution copy attributes
force LF where byte comparisons need to survive Windows checkouts.

Archive-content checks caught and fixed wasm-pack's generated `.gitignore`
excluding the WASM binaries from npm. The final npm package includes both
production binaries, entry points, declarations, and all license notices.
Python source staging prunes unused workspace members while proving that each
retained locked dependency version and checksum is unchanged. Binary notices
include the complete license texts from the resolved non-dev Cargo graph.

The generated `target/alpha/SHA256SUMS.json` records all nine candidate digests.
Detailed local logs are `target/alpha-full-gate.log`, `alpha-dart-gate.log`,
`alpha-final-release-check.log`, `alpha-python311-consumer.log`, and
`alpha-msrv-check.log`. Candidate archives were built from the current dirty
working tree; public release artifacts must be rebuilt from the reviewed commit.

The build-only alpha workflow is configured for Linux/Windows/macOS wheels,
CPython 3.11/3.14 consumers, Node 22/24, a Rust archive consumer, and Rust 1.85.
Those remote jobs have **not run**. Registry account ownership, initial npm
bootstrap authentication, PyPI publisher configuration, and actual uploads are
still pending. Publishing remains disabled in the manifests. Dart distribution
packaging and PostgreSQL remain excluded from this alpha.
